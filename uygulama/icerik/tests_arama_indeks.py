# -*- coding: utf-8 -*-
"""F7 arama indeksi — `HaberArama`, kayıt kancası, iki motorun yolu.

Paket iki motorda da koşar: `BH_VERITABANI` verilirse PostgreSQL, verilmezse
SQLite. Motora özgü testler `skipUnless` ile ayrılır; ortak testler iki
motorda AYNI sonucu ister — iki yolun anlamı aynı olmalı (`icerik/arama.py`).
"""

from unittest import mock, skipUnless

from django.contrib.auth.models import Group, User
from django.core.management import call_command
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from taksonomi.models import Kategori, KategoriTur

from . import arama
from .arama_metni import kayit_metni, sorgu_coz
from .models import Haber, HaberArama

PG = connection.vendor == "postgresql"


class KayitMetni(TestCase):
    """Saklama biçimi bir sözleşme: tek boşluk ayırıcı, iki uçta boşluk."""

    def test_bicim(self):
        self.assertEqual(kayit_metni("Bursa'da IŞIK", None, "Gölge"),
                         " bursa da isik golge ")

    def test_bos(self):
        self.assertEqual(kayit_metni(None, "", "  ...  "), "")

    def test_buyuk_i_ve_noktasiz_i(self):
        self.assertEqual(kayit_metni("İNEGÖL Işık"), " inegol isik ")
        self.assertNotIn("̇", kayit_metni("İNEGÖL"))  # birleşen nokta yok

    def test_tsquery_kurulusu(self):
        self.assertEqual(arama.tsquery(sorgu_coz("IŞIK ve gölge")), "'isik':* & 'golge':*")
        self.assertEqual(arama.tsquery(sorgu_coz("a takımı")), "'a' & 'takimi':*")


def _kategori():
    return KategoriTur.objects.get(tur=Kategori.TUR_HABER, slug="gundem").kategori


def _haber(i, baslik, spot="", durum=Haber.DURUM_AKTIF):
    return Haber.objects.create(
        id=i, slug=f"arama-{i}", baslik=baslik, spot=spot, kategori=_kategori(),
        durum=durum, yayin_zamani=timezone.now())


class AramaIndeksi(TestCase):
    """Okur araması — iki motorda aynı sonuç."""

    @classmethod
    def setUpTestData(cls):
        call_command("taksonomi_kur", verbosity=0)
        _haber(1, "Işıklar yandı, Osmangazi aydınlandı")
        _haber(2, "Trafik ışıkları arızalandı")
        _haber(10, "Kavşaktaki ışığı söktüler")              # ünsüz yumuşaması
        _haber(3, "IŞIK OYUNLARI FESTİVALİ")
        _haber(4, "Yönetmelik değişikliği yürürlükte")      # "isik" ALT DİZİSİ var
        _haber(5, "Bisiklet yolu açıldı")                    # "isik" ALT DİZİSİ var
        _haber(6, "Başlıkta yok", spot="Spotta ışık geçiyor")
        _haber(7, "Bursaspor a takımı kampta")
        _haber(8, "Taslak ışık haberi", durum=Haber.DURUM_PASIF)
        _haber(9, "Öğrenci servisleri ÇAĞRI merkezi")

    def _bulunan(self, q):
        return sorted(arama.haberleri_suz(Haber.yayindakiler(), sorgu_coz(q))
                      .values_list("id", flat=True))

    def test_kanca_satiri_kurar(self):
        self.assertEqual(HaberArama.objects.get(pk=1).baslik,
                         " isiklar yandi osmangazi aydinlandi ")
        self.assertEqual(HaberArama.objects.get(pk=6).metin,
                         " baslikta yok spotta isik geciyor ")

    def test_turkce_harf_kusuru_kapandi(self):
        """§21: `IŞIK` → 0 sonuç kusuru. Dört yazım da aynı sonucu vermeli."""
        beklenen = [1, 2, 3, 6]
        for q in ("ışık", "IŞIK", "Işık", "isik"):
            with self.subTest(q=q):
                self.assertEqual(self._bulunan(q), beklenen)

    def test_alt_dizi_rastlantisi_yok(self):
        """`değişikliği`, `bisiklet` "ışık" aramasında GELMEZ (§21: %83 rastlantı)."""
        self.assertNotIn(4, self._bulunan("ışık"))
        self.assertNotIn(5, self._bulunan("ışık"))

    def test_unsuz_yumusamasi_HENUZ_KACIYOR(self):
        """Bilinen sınır, bilerek kilitli: `ışık` → `ışığı` (k → ğ).

        Önek araması eki yakalar ama kökün son harfi değişince kaçırır
        (`isik` önek `isigi`yi kapsamaz). Çözüm kök bulucu (PostgreSQL
        `turkish` Snowball, §21) ya da sorgu genişletme; ikisi de ayrı karar.
        Bu sınır kalkınca test kırılır ve bilinçli güncellenir.
        """
        self.assertNotIn(10, self._bulunan("ışık"))
        self.assertIn(10, self._bulunan("ışığı"))

    def test_yayinda_olmayan_gelmez(self):
        self.assertNotIn(8, self._bulunan("ışık"))

    def test_terimler_ve_ile_baglanir(self):
        self.assertEqual(self._bulunan("trafik ışık"), [2])
        self.assertEqual(self._bulunan("öğrenci çağrı"), [9])
        self.assertEqual(self._bulunan("ÖĞRENCİ ÇAĞRI"), [9])

    def test_kisa_terim_tam_kelime(self):
        """`a` önek almaz: "a takımı" yalnız tam `a` kelimesini ister."""
        self.assertEqual(self._bulunan("a takımı"), [7])
        self.assertEqual(self._bulunan("a ışık"), [])

    def test_sayfalayici_kucuk_sonucta_sayfayi_kimlikten_kurar(self):
        """Sınır altı sonuçta sayfa sorgusu arama süzgecini TAŞIMAZ (pk IN).

        PG'de süzgeç + ORDER BY + LIMIT planlayıcıyı sıralama indeksini
        baştan yürümeye itiyordu: sonuçsuz `qxzvbn` 8.483 ms.
        """
        s = arama.AramaSayfalayici(Haber.yayindakiler(), sorgu_coz("ışık"), 20)
        with CaptureQueriesContext(connection) as yakala:
            sonuc = [h.pk for h in s.page(1).object_list]
        sorgular = [q["sql"] for q in yakala.captured_queries]
        self.assertEqual(len(sorgular), 2, sorgular)
        self.assertIn("haberarama", sorgular[0])
        self.assertNotIn("haberarama", sorgular[1])
        self.assertEqual(sorted(sonuc), [1, 2, 3, 6])
        self.assertFalse(s.kesildi_mi)

    def test_sayfalayicinin_iki_yolu_ayni_sirayi_verir(self):
        class Kucuk(arama.AramaSayfalayici):
            UST_SINIR = 2
        kisa = Kucuk(Haber.yayindakiler(), sorgu_coz("ışık"), 10)
        tam = arama.AramaSayfalayici(Haber.yayindakiler(), sorgu_coz("ışık"), 10)
        self.assertTrue(kisa.kesildi_mi)
        self.assertEqual(kisa.count, 2)
        self.assertEqual([h.pk for h in kisa.page(1).object_list][:2],
                         [h.pk for h in tam.page(1).object_list][:2])

    def test_sonucsuz_sorgu_tek_sorguda_biter(self):
        s = arama.AramaSayfalayici(Haber.yayindakiler(), sorgu_coz("qxzvbn"), 20)
        with CaptureQueriesContext(connection) as yakala:
            self.assertEqual(list(s.page(1).object_list), [])
        # Kimlik sorgusu + boş `pk IN ()` (Django boş IN'i sorguya hiç yollamaz).
        self.assertLessEqual(len(yakala), 2)

    def test_gorunum_buyuk_harfle_sonuc_verir(self):
        yanit = self.client.get("/ara", {"q": "IŞIK"})
        self.assertContains(yanit, "4 sonuç")
        self.assertContains(yanit, "IŞIK OYUNLARI")

    def test_basliktaki_degisiklik_aramaya_yansir(self):
        h = Haber.objects.get(pk=5)
        h.baslik = "Işık festivali ertelendi"
        h.save()
        self.assertIn(5, self._bulunan("ışık"))

    def test_ilgisiz_alan_kaydi_arama_satirina_yazmaz(self):
        h = Haber.objects.get(pk=1)
        h.durum = Haber.DURUM_PASIF
        with CaptureQueriesContext(connection) as yakala:
            h.save(update_fields=["durum"])
        self.assertFalse([s for s in yakala.captured_queries
                          if "icerik_haberarama" in s["sql"]])

    def test_haber_silinince_satir_gider(self):
        Haber.objects.filter(pk=2).delete()
        self.assertFalse(HaberArama.objects.filter(pk=2).exists())

    def test_toplu_yazim_doldur_komutuyla_kapanir(self):
        """`bulk_create` kancayı çağırmaz; `arama_doldur` eksiği kapatır."""
        Haber.objects.bulk_create([Haber(
            id=50, slug="toplu", baslik="Toplu ışık kaydı", kategori=_kategori(),
            durum=Haber.DURUM_AKTIF, yayin_zamani=timezone.now(), hazirlik="taslak")])
        self.assertNotIn(50, self._bulunan("ışık"))
        call_command("arama_doldur", stdout=mock.MagicMock())
        self.assertIn(50, self._bulunan("ışık"))

    def test_doldur_hepsi_bozuk_satiri_onarir(self):
        HaberArama.objects.filter(pk=1).update(metin=" bozuk ", baslik=" bozuk ")
        call_command("arama_doldur", stdout=mock.MagicMock())          # eksik yok
        self.assertNotIn(1, self._bulunan("ışık"))
        call_command("arama_doldur", hepsi=True, stdout=mock.MagicMock())
        self.assertIn(1, self._bulunan("ışık"))


class ZamanSiniri(TestCase):
    """Sonuçsuz sorgu işçiyi kilitlememeli (DEGERLENDIRME §3 bulgu 9)."""

    @classmethod
    def setUpTestData(cls):
        call_command("taksonomi_kur", verbosity=0)
        _haber(1, "Işıklar yandı")

    def _uzun_sorgu(self):
        with connection.cursor() as c:
            if PG:
                c.execute("SELECT pg_sleep(2)")
            else:
                c.execute("WITH RECURSIVE s(n) AS (SELECT 1 UNION ALL SELECT n + 1 "
                          "FROM s WHERE n < 50000000) SELECT COUNT(*) FROM s")
            c.fetchall()

    def test_sinir_asilinca_zaman_asimi(self):
        with self.assertRaises(arama.ZamanAsimi):
            with arama.sure_siniri(50):
                self._uzun_sorgu()

    def test_sinir_blok_disina_sizmaz(self):
        """Blok bittikten sonra aynı bağlantıdaki sorgu kesilmemeli."""
        with arama.sure_siniri(20):
            list(Haber.objects.all()[:1])
        with connection.cursor() as c:
            if PG:
                c.execute("SHOW statement_timeout")
                self.assertEqual(c.fetchone()[0], "0")
                c.execute("SELECT pg_sleep(0.1)")
            else:
                c.execute("WITH RECURSIVE s(n) AS (SELECT 1 UNION ALL SELECT n + 1 "
                          "FROM s WHERE n < 300000) SELECT COUNT(*) FROM s")
                self.assertEqual(c.fetchone()[0], 300000)

    def test_gorunum_zaman_asiminda_uyari_basar(self):
        def asim(ms=None):
            raise arama.ZamanAsimi("deneme")
        with mock.patch.object(arama, "sure_siniri", side_effect=asim):
            yanit = self.client.get("/ara", {"q": "ışık"})
        self.assertEqual(yanit.status_code, 200)
        self.assertContains(yanit, "zaman sınırını aştı")
        self.assertNotContains(yanit, "Işıklar yandı")


class PanelHaberAra(TestCase):
    """Panel seçicisi: normalize başlıkta ALT DİZİ, Türkçe harf doğru."""

    @classmethod
    def setUpTestData(cls):
        call_command("taksonomi_kur", verbosity=0)
        call_command("roller_kur", verbosity=0)
        cls.editor = User.objects.create_user("ed-arama", password="deneme-parola-123")
        cls.editor.groups.add(Group.objects.get(name="Editör"))
        _haber(11, "Bozbey basın toplantısı düzenledi")
        _haber(12, "İNEGÖL'DE KÖFTE FESTİVALİ")
        _haber(13, "Silinmiş Bozbey kaydı", durum=Haber.DURUM_SILINMIS)

    def _ara(self, q):
        self.client.force_login(self.editor)
        return [s["id"] for s in self.client.get("/panel/haber-ara", {"q": q}).json()["sonuclar"]]

    def test_alt_dizi_bulur(self):
        self.assertEqual(self._ara("bozbe"), [11])

    def test_buyuk_harf_ve_kucuk_harf_ayni(self):
        self.assertEqual(self._ara("inegöl"), [12])
        self.assertEqual(self._ara("İNEGÖL"), [12])
        self.assertEqual(self._ara("inegol"), [12])


@skipUnless(PG, "PostgreSQL'e özgü: üretilmiş sütun ve GIN indeksleri")
class PostgresIndeksleri(TestCase):

    @classmethod
    def setUpTestData(cls):
        call_command("taksonomi_kur", verbosity=0)
        _haber(21, "Işıklar yandı", spot="Osmangazi")

    def test_vektor_uretilmis_sutun(self):
        with connection.cursor() as c:
            c.execute("SELECT vektor::text FROM icerik_haberarama WHERE haber_id = 21")
            self.assertEqual(c.fetchone()[0], "'isiklar' 'osmangazi' 'yandi'")
            c.execute("SELECT attgenerated FROM pg_attribute WHERE attrelid = "
                      "'icerik_haberarama'::regclass AND attname = 'vektor'")
            self.assertEqual(c.fetchone()[0], "s")

    def test_indeksler_kurulu(self):
        with connection.cursor() as c:
            c.execute("SELECT indexname, indexdef FROM pg_indexes "
                      "WHERE tablename = 'icerik_haberarama'")
            tanim = dict(c.fetchall())
        self.assertIn("gin (vektor)", tanim["haberarama_vektor_gin"])
        self.assertIn("gin_trgm_ops", tanim["haberarama_baslik_trgm"])

    def _plan(self, sql, parametre):
        """Tarama kapalıyken plan: sorgu biçimi indeksle EŞLEŞİYOR mu?

        Küçük test tablosunda planlayıcı her zaman taramayı seçer; asıl
        ölçüm 1 milyon satırda yapıldı (rapor). Burada kilitlenen şey,
        `icerik/arama.py`nin ürettiği koşulun indeksin işleciyle aynı
        biçimde olması — biçim değişirse indeks sessizce boşa düşer.
        """
        with connection.cursor() as c:
            c.execute("SET LOCAL enable_seqscan = off")
            c.execute("EXPLAIN " + sql, parametre)
            return "\n".join(r[0] for r in c.fetchall())

    def test_okur_kosulu_gin_indeksiyle_eslesir(self):
        plan = self._plan("SELECT haber_id FROM icerik_haberarama "
                          "WHERE vektor @@ %s::tsquery",
                          [arama.tsquery(sorgu_coz("ışık"))])
        self.assertIn("haberarama_vektor_gin", plan)

    def test_panel_kosulu_trigram_indeksiyle_eslesir(self):
        sorgu = HaberArama.objects.filter(baslik__contains="bozbe").values("pk")
        plan = self._plan(*sorgu.query.sql_with_params())
        self.assertIn("haberarama_baslik_trgm", plan)

    def test_okur_sorgusu_kosulu_alt_sorguda_tasir(self):
        sorgu = arama.haberleri_suz(Haber.yayindakiler(), sorgu_coz("ışık"))
        sql, _ = sorgu.query.sql_with_params()
        self.assertIn("vektor @@", sql)


@skipUnless(PG, "ICU tr-TR derlemi yalnız PostgreSQL'de")
class TurkceDerlem(TestCase):
    """Veritabanı ICU `tr-TR` ile kuruldu (karar ve ölçüm: rapor, 19 Ekim 2026).

    Bu testler kararı kilitler: yeni bir kümede derlem unutulursa (üretimde
    aynı karar tekrar uygulanacak) kırılırlar.
    """

    def test_veritabani_derlemi_tr(self):
        with connection.cursor() as c:
            c.execute("SELECT datlocprovider, datlocale FROM pg_database "
                      "WHERE datname = current_database()")
            self.assertEqual(c.fetchone(), ("i", "tr-TR"))

    def test_siralama_turkce(self):
        with connection.cursor() as c:
            c.execute("SELECT x FROM unnest(ARRAY['Osmangazi','İnegöl','Iğdır','Çanakkale',"
                      "'Cami','Ödemiş','Şile','Sakarya','Zonguldak']) x ORDER BY x")
            self.assertEqual([r[0] for r in c.fetchall()],
                             ["Cami", "Çanakkale", "Iğdır", "İnegöl", "Osmangazi",
                              "Ödemiş", "Sakarya", "Şile", "Zonguldak"])

    def test_icontains_turkce_dogru(self):
        """ORM'in `icontains`'i (UPPER … LIKE UPPER) tr-TR'de i/İ, ı/I'yı doğru eşler."""
        call_command("taksonomi_kur", verbosity=0)
        _haber(31, "Işık festivali İnegöl'de")
        for q in ("ışık", "IŞIK", "inegöl", "İNEGÖL"):
            with self.subTest(q=q):
                self.assertTrue(Haber.objects.filter(baslik__icontains=q).exists())
