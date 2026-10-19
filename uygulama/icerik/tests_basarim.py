"""Başarım paketi (19 Ekim 2026) — gerileme kilitleri.

Her madde bir ölçümden geliyor (ölçümler ilgili modüllerin başında):

1. Yayın süzgeci: ileri tarihli haber hiçbir yüzde görünmez.
2. Paylaşılan önbellek: taze/bayat düzeni, kilit, hata yolunda damga.
3. Menü sayımı: tek `GROUP BY` + `COUNT(*)`, ikinci istekte sorgu yok.
4. Okunma sayacı: tek işlem/tek deyim, okuma yolu yazmaz, kuyruk + komut.
5. Kategori slug eşlemesi: adres kurmak KategoriTur sorgusu açmaz.
6. Sayfa mikro önbelleği: anonim isabet, oturumda atlama, kayıtta düşme,
   önbellekten servis edilen okumanın sayılması.
7. Site haritası: indeks ay sayısından bağımsız sorgu sayısıyla, aylık
   dosya önbellekte ve kayıt değişince tazeleniyor.
8. Masa kuyruğu ve konu üyeleri: indeksin istediği terimler sorguda.
9. Yavaş sorgu günlüğü ve kalıcı bağlantı ayarı.
"""

from __future__ import annotations

import tempfile
from datetime import datetime, timedelta
from datetime import timezone as dt_timezone
from pathlib import Path
from unittest import mock

from django.conf import settings
from django.core.cache import caches
from django.core.management import call_command
from django.db import DatabaseError, IntegrityError, connection
from django.test import RequestFactory, TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from taksonomi import slug_eslemesi
from taksonomi.models import Kategori, KategoriTur

from . import baglam, okunma, onbellek
from .models import Haber, Konu, KonuHaber, Okunma

TARAYICI = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/128.0 Safari/537.36")
LOCMEM = "django.core.cache.backends.locmem.LocMemCache"
SAYFA_ACIK = override_settings(
    CACHES={"default": {"BACKEND": LOCMEM, "LOCATION": "bh-t-veri"},
            "sayfa": {"BACKEND": LOCMEM, "LOCATION": "bh-t-sayfa"}},
    SAYFA_ONBELLEK_SANIYE=30)


class Temel(TestCase):

    @classmethod
    def setUpTestData(cls):
        call_command("taksonomi_kur", verbosity=0)
        cls.tur = KategoriTur.objects.filter(tur=Kategori.TUR_HABER, slug="bursaspor").first()
        cls.kategori = cls.tur.kategori

    def setUp(self):
        okunma.sifirla()

    def tearDown(self):
        okunma.sifirla()

    def haber(self, n, an=None, **ek):
        alanlar = dict(id=980000 + n, slug=f"basarim-{n}", baslik=f"Başarım başlığı {n}",
                       spot="spot", govde="<p>gövde</p><p>ikinci</p>", kategori=self.kategori,
                       yayin_zamani=an or timezone.now() - timedelta(minutes=n))
        alanlar.update(ek)
        return Haber.objects.create(**alanlar)


# --------------------------------------------------------------------------
# 1. Yayın süzgeci

class IleriTarihliHaber(Temel):
    """DEGERLENDIRME-2026-10 bulgu 4: ileri tarihli haber hemen yayına çıkıyordu."""

    def test_yayindakiler_ileri_tarihi_almiyor(self):
        gecmis = self.haber(1)
        ileri = self.haber(2, an=timezone.now() + timedelta(hours=3))
        kimlikler = set(Haber.yayindakiler().values_list("pk", flat=True))
        self.assertIn(gecmis.pk, kimlikler)
        self.assertNotIn(ileri.pk, kimlikler)
        self.assertFalse(ileri.yayinda_mi())
        self.assertTrue(gecmis.yayinda_mi())

    def test_ileri_tarihli_haber_hicbir_yuzde_gorunmuyor(self):
        ileri = self.haber(3, an=timezone.now() + timedelta(hours=3),
                           baslik="İleri tarihli gizli başlık")
        self.assertEqual(self.client.get(ileri.get_absolute_url()).status_code, 404)
        for adres in ("/", "/bursaspor", "/rss", "/rss/bursaspor"):
            with self.subTest(adres=adres):
                self.assertNotContains(self.client.get(adres), "İleri tarihli gizli başlık")
        ay = ileri.yayin_zamani.astimezone().strftime("%Y-%m")
        govde = b"".join(self.client.get(f"/static/sitemap/news_{ay}.xml").streaming_content)
        self.assertNotIn(f"-{ileri.pk}".encode(), govde)

    def test_saati_gelince_gorunuyor(self):
        ileri = self.haber(4, an=timezone.now() + timedelta(hours=3))
        self.assertEqual(self.client.get(ileri.get_absolute_url()).status_code, 404)
        ileri.yayin_zamani = timezone.now() - timedelta(minutes=1)
        ileri.save()
        self.assertEqual(self.client.get(ileri.get_absolute_url()).status_code, 200)

    def test_konu_sayfasi_ileri_tarihi_almiyor(self):
        from . import konu as konu_yardimci
        gecmis, ileri = self.haber(5), self.haber(6, an=timezone.now() + timedelta(days=1))
        k = Konu.objects.create(ad="Dosya", slug="dosya", onay=Konu.ONAY_ONAYLI,
                                baslangic=timezone.localdate(), bitis=timezone.localdate())
        for h in (gecmis, ileri):
            KonuHaber.objects.create(konu=k, haber=h, tarih=timezone.localdate())
        self.assertEqual([h.pk for h in konu_yardimci.uyeler(k)], [gecmis.pk])


# --------------------------------------------------------------------------
# 2. Paylaşılan önbellek

class TazeBayatKilit(TestCase):

    def test_taze_deger_yeniden_hesaplanmiyor(self):
        uret = mock.Mock(return_value=1)
        for _ in range(3):
            self.assertEqual(onbellek.hesapla("t:taze", uret, taze=60), 1)
        self.assertEqual(uret.call_count, 1)

    def test_bayat_deger_kilit_tutulurken_beklemeden_doniyor(self):
        ob = caches[onbellek.VERI]
        ob.set("t:bayat", (0.0, "eski"), 300)      # damga 0: bayat
        ob.add("t:bayat:kilit", 1, 30)               # başka süreç hesaplıyor
        uret = mock.Mock(return_value="yeni")
        self.assertEqual(onbellek.hesapla("t:bayat", uret, taze=60), "eski")
        uret.assert_not_called()

    def test_kilit_bosken_bayat_deger_tazeleniyor(self):
        caches[onbellek.VERI].set("t:tazele", (0.0, "eski"), 300)
        self.assertEqual(onbellek.hesapla("t:tazele", lambda: "yeni", taze=60), "yeni")
        self.assertIsNone(caches[onbellek.VERI].get("t:tazele:kilit"))

    def test_hata_yolunda_son_bilinen_deger_ve_damga_yaziliyor(self):
        caches[onbellek.VERI].set("t:hata", (0.0, "son"), 300)
        uret = mock.Mock(side_effect=DatabaseError("database is locked"))
        for _ in range(3):
            self.assertEqual(onbellek.hesapla("t:hata", uret, taze=60, hata=20), "son")
        self.assertEqual(uret.call_count, 1)      # damga güncellendi: kilide yeniden girmiyor

    def test_hata_yolunda_deger_yoksa_yedek(self):
        uret = mock.Mock(side_effect=DatabaseError("kilit"))
        self.assertEqual(onbellek.hesapla("t:yedek", uret, taze=60, yedek=list), [])
        self.assertEqual(onbellek.hesapla("t:yedek", uret, taze=60, yedek=list), [])
        self.assertEqual(uret.call_count, 1)

    def test_bayatlat_silmeden_yeniden_hesaplatiyor(self):
        self.assertEqual(onbellek.hesapla("t:b", lambda: 1, taze=60), 1)
        onbellek.bayatlat("t:b")
        self.assertEqual(caches[onbellek.VERI].get("t:b")[1], 1)   # değer duruyor
        self.assertEqual(onbellek.hesapla("t:b", lambda: 2, taze=60), 2)

    def test_ayarlar_paylasilan_onbellek_tanimliyor(self):
        """Test dışında `default` ve `sayfa` paylaşılan arka uçta; testte
        süreç içi ve kapalı. Ayar dosyası iki yolu da taşıyor."""
        metin = (Path(settings.BASE_DIR) / "cekirdek" / "settings.py").read_text(encoding="utf-8")
        self.assertIn("django.core.cache.backends.redis.RedisCache", metin)
        self.assertIn("django.core.cache.backends.filebased.FileBasedCache", metin)
        self.assertIn("BH_REDIS", metin)
        self.assertIn("BH_ONBELLEK_KOK", metin)
        self.assertEqual(settings.CACHES["sayfa"]["BACKEND"],
                         "django.core.cache.backends.dummy.DummyCache")


# --------------------------------------------------------------------------
# 3. Menü sayımı

class MenuSayimi(Temel):

    def test_tek_gruplu_sayim_ve_ikinci_cagrida_sorgu_yok(self):
        self.haber(1)
        with CaptureQueriesContext(connection) as ilk:
            liste = baglam._tum_kategoriler()
        sayimlar = [q["sql"] for q in ilk.captured_queries if "COUNT" in q["sql"].upper()]
        self.assertEqual(len(sayimlar), 1, sayimlar)
        self.assertIn("COUNT(*)", sayimlar[0])
        self.assertIn("GROUP BY", sayimlar[0].upper())
        # Eski biçim birleşmeli `COUNT("icerik_haber"."id")` idi ve `id` rowid
        # olmadığı için her satırda tabloya gidiyordu.
        self.assertNotIn('COUNT("icerik_haber"."id")', sayimlar[0])
        self.assertNotIn("JOIN", sayimlar[0].upper())
        self.assertEqual(liste[0]["slug"], "bursaspor")       # tek haberli kategori önde
        with CaptureQueriesContext(connection) as ikinci:
            self.assertEqual(baglam._tum_kategoriler(), liste)
        self.assertEqual(len(ikinci.captured_queries), 0)

    def test_bant_da_ozetten_geliyor(self):
        self.client.get("/ilceler")
        with CaptureQueriesContext(connection) as y:
            self.client.get("/ilceler")
        kategori = [q["sql"] for q in y.captured_queries
                    if "taksonomi_kategori" in q["sql"] or "taksonomi_ilce" in q["sql"]]
        self.assertEqual(kategori, [], "bant/ilçe her istekte sorgu açıyor")


# --------------------------------------------------------------------------
# 4. Okunma sayacı

class OkunmaYazimi(Temel):

    def _say(self, haber, adres):
        okunma.say(RequestFactory().get("/", HTTP_USER_AGENT=TARAYICI, REMOTE_ADDR=adres),
                   haber.pk)

    def test_bosaltma_tek_deyim(self):
        haberler = [self.haber(n) for n in range(1, 4)]
        for h in haberler:
            self._say(h, "10.1.0.1")
        Okunma.objects.create(haber=haberler[0], gun=timezone.localdate(), adet=5)
        with CaptureQueriesContext(connection) as y:
            self.assertEqual(okunma.bosalt(), 3)
        yazan = [q["sql"] for q in y.captured_queries
                 if q["sql"].upper().startswith(("INSERT", "UPDATE"))]
        self.assertEqual(len(yazan), 1, yazan)
        self.assertIn("ON CONFLICT", yazan[0])
        self.assertEqual(Okunma.objects.get(haber=haberler[0]).adet, 6)
        self.assertEqual(Okunma.objects.get(haber=haberler[2]).adet, 1)

    def test_okuma_yolu_bosaltmiyor(self):
        h = self.haber(1)
        self._say(h, "10.1.0.2")
        okunma._son_bosaltma -= 3600          # süre çoktan doldu
        with CaptureQueriesContext(connection) as y:
            okunma.en_cok(Haber.yayindakiler(), 5)
        self.assertFalse(any(q["sql"].upper().startswith("INSERT")
                             for q in y.captured_queries))
        self.assertEqual(Okunma.objects.count(), 0)

    def test_yazilamazsa_tampona_geri_donuyor(self):
        h = self.haber(1)
        self._say(h, "10.1.0.3")
        with mock.patch.object(okunma, "_upsert", side_effect=DatabaseError("kilit")):
            self.assertEqual(okunma.bosalt(), 0)
        self.assertEqual(okunma.bosalt(), 1)
        self.assertEqual(Okunma.objects.get(haber=h).adet, 1)

    def test_silinmis_haberin_kovasi_partiyi_dusurmuyor(self):
        h = self.haber(1)
        kovalar = {(h.pk, timezone.localdate()): 2, (999999999, timezone.localdate()): 1}
        gercek = okunma._upsert
        cagrilar = []

        def sahte(k):
            cagrilar.append(dict(k))
            if len(cagrilar) == 1:
                raise IntegrityError("FOREIGN KEY constraint failed")
            return gercek(k)

        with mock.patch.object(okunma, "_upsert", side_effect=sahte):
            self.assertEqual(okunma.kovalari_yaz(kovalar), 1)
        self.assertEqual(list(cagrilar[1]), [(h.pk, timezone.localdate())])
        self.assertEqual(Okunma.objects.get(haber=h).adet, 2)

    def test_komut_duzeni_kuyruga_yazar_komut_veritabanina_tasir(self):
        h = self.haber(1)
        kuyruk = Path(tempfile.mkdtemp())
        with override_settings(OKUNMA_YAZIM="komut", OKUNMA_KUYRUK_KOK=kuyruk):
            self._say(h, "10.1.0.4")
            self._say(h, "10.1.0.5")
            self.assertEqual(okunma.bosalt(), 1)
            self.assertEqual(Okunma.objects.count(), 0)          # veritabanı yok
            self.assertEqual(len(list(kuyruk.glob("okunma-*.json"))), 1)
            call_command("okunma_bosalt", stdout=open(Path(kuyruk) / "cikti.txt", "w"))
            self.assertEqual(Okunma.objects.get(haber=h).adet, 2)
            self.assertEqual(list(kuyruk.glob("okunma-*")), [])
            # Komut ikinci kez çalışınca hiçbir şeyi iki kez yazmaz.
            call_command("okunma_bosalt", stdout=open(Path(kuyruk) / "cikti.txt", "w"))
            self.assertEqual(Okunma.objects.get(haber=h).adet, 2)

    def test_kapanista_tampon_kuyruga_birakiliyor(self):
        h = self.haber(1)
        kuyruk = Path(tempfile.mkdtemp())
        with override_settings(OKUNMA_KUYRUK_KOK=kuyruk):
            self._say(h, "10.1.0.6")
            okunma._kapanista_birak()
            self.assertEqual(len(list(kuyruk.glob("okunma-*.json"))), 1)
            okunma.bosalt()       # istek düzeni kuyruğu da toplar
        self.assertEqual(Okunma.objects.get(haber=h).adet, 1)


# --------------------------------------------------------------------------
# 5. Kategori slug eşlemesi

class SlugEslemesi(Temel):

    def test_on_cekimsiz_adres_sorgu_acmiyor(self):
        h = self.haber(1)
        slug_eslemesi.eslem()                        # ısıt
        kayit = Haber.objects.get(pk=h.pk)           # kategori yüklenmemiş
        with CaptureQueriesContext(connection) as y:
            adres = kayit.get_absolute_url()
            kayit_kategori_slug = Kategori.objects.get(pk=self.kategori.pk)
        self.assertEqual(adres, f"/bursaspor/{h.slug}-{h.pk}")
        self.assertEqual(len(y.captured_queries), 1)   # yalnız kategori get'i
        with CaptureQueriesContext(connection) as y:
            self.assertEqual(kayit_kategori_slug.slug_al(), "bursaspor")
        self.assertEqual(len(y.captured_queries), 0)

    def test_tur_satiri_degisince_eslem_duser(self):
        slug_eslemesi.eslem()
        self.tur.slug = "bursaspor-yeni"
        self.tur.save()
        self.assertEqual(slug_eslemesi.slug(self.kategori.pk), "bursaspor-yeni")

    def test_anasayfa_ve_haber_detay_kategori_turu_sorgusu_acmiyor(self):
        h = self.haber(1)
        for n in range(2, 12):
            self.haber(n)
        for adres in ("/", h.get_absolute_url()):
            self.client.get(adres)                   # menü/eşleme ısınsın
            with CaptureQueriesContext(connection) as y:
                self.assertEqual(self.client.get(adres).status_code, 200)
            tur = [q["sql"] for q in y.captured_queries if "taksonomi_kategoritur" in q["sql"]]
            with self.subTest(adres=adres):
                self.assertEqual(tur, [], f"{adres}: {len(tur)} KategoriTur sorgusu")


# --------------------------------------------------------------------------
# 6. Sayfa mikro önbelleği

@SAYFA_ACIK
class SayfaOnbellegi(Temel):

    def test_anonim_ikinci_istek_onbellekten_ve_sorgusuz(self):
        self.haber(1)
        ilk = self.client.get("/")
        self.assertEqual(ilk["X-Onbellek"], "kayit")
        with CaptureQueriesContext(connection) as y:
            ikinci = self.client.get("/")
        self.assertEqual(ikinci["X-Onbellek"], "isabet")
        self.assertEqual(ikinci.content, ilk.content)
        self.assertEqual(len(y.captured_queries), 0)

    def test_haber_kaydedilince_sayfa_aninda_tazeleniyor(self):
        h = self.haber(1, baslik="Eski başlık burada")
        self.client.get("/")
        h.baslik = "Yepyeni başlık burada"
        h.save()
        yanit = self.client.get("/")
        self.assertEqual(yanit["X-Onbellek"], "kayit")
        self.assertContains(yanit, "Yepyeni başlık burada")

    def test_oturumlu_kullanici_onbellege_girmiyor(self):
        from django.contrib.auth.models import User
        User.objects.create_user("editor", password="deneme-parola-123", is_staff=True)
        self.client.login(username="editor", password="deneme-parola-123")
        self.assertNotIn("X-Onbellek", self.client.get("/"))
        self.assertNotIn("X-Onbellek", self.client.get("/"))

    def test_paylasim_parametresi_ayri_kayit_acmiyor(self):
        self.client.get("/bursaspor")
        self.assertEqual(self.client.get("/bursaspor?utm_source=x")["X-Onbellek"], "isabet")
        self.assertEqual(self.client.get("/bursaspor?sayfa=2")["X-Onbellek"], "kayit")

    def test_onbellekten_servis_edilen_okuma_da_sayiliyor(self):
        h = self.haber(1)
        adres = h.get_absolute_url()
        ilk = self.client.get(adres, HTTP_USER_AGENT=TARAYICI, REMOTE_ADDR="10.2.0.1")
        ikinci = self.client.get(adres, HTTP_USER_AGENT=TARAYICI, REMOTE_ADDR="10.2.0.2")
        self.assertEqual(ilk["X-Onbellek"], "kayit")
        self.assertEqual(ikinci["X-Onbellek"], "isabet")
        # Aynı okur yarım saat içinde tekrar: önbellekte de sayılmaz.
        self.client.get(adres, HTTP_USER_AGENT=TARAYICI, REMOTE_ADDR="10.2.0.2")
        okunma.bosalt()
        self.assertEqual(Okunma.objects.get(haber=h).adet, 2)

    def test_yonlendirme_ve_404_onbelleklenmiyor(self):
        h = self.haber(1)
        yanlis = f"/bursaspor/yanlis-slug-{h.pk}"
        self.assertEqual(self.client.get(yanlis).status_code, 301)
        self.assertNotIn("X-Onbellek", self.client.get(yanlis))
        self.assertNotIn("X-Onbellek", self.client.get("/bursaspor/yok-1"))


# --------------------------------------------------------------------------
# 7. Site haritası

def _utc(yil, ay, gun, saat=12, dakika=0):
    return datetime(yil, ay, gun, saat, dakika, tzinfo=dt_timezone.utc)


class SiteHaritasi(Temel):

    def _indeks(self):
        return b"".join(self.client.get("/static/sitemap/sitemap.xml").streaming_content).decode()

    def test_indeks_sorgu_sayisi_ay_sayisindan_bagimsiz(self):
        self.haber(1, an=_utc(2025, 1, 10))
        with CaptureQueriesContext(connection) as tek:
            self._indeks()
        caches[onbellek.VERI].clear()
        for n, ay in enumerate(range(2, 13), start=2):
            self.haber(n, an=_utc(2025, ay, 10))
        with CaptureQueriesContext(connection) as on_iki:
            metin = self._indeks()
        self.assertEqual(metin.count("news_2025-"), 12)
        self.assertEqual(len(on_iki.captured_queries), len(tek.captured_queries))

    def test_ikinci_indeks_isteginde_ozet_sorgusu_yok(self):
        self.haber(1, an=_utc(2025, 1, 10))
        self._indeks()
        with CaptureQueriesContext(connection) as y:
            self._indeks()
        haber = [q["sql"] for q in y.captured_queries if '"icerik_haber"' in q["sql"]]
        self.assertEqual(haber, [])

    def test_toplu_ozet_ay_ay_hesapla_ayni(self):
        """UTC ay sınırı (yerelde ertesi ay) toplu gruplamada da doğru aya."""
        from besleme.aileler import aile
        self.haber(1, an=_utc(2021, 3, 31, 21, 2))     # yerelde 1 Nisan
        self.haber(2, an=_utc(2021, 3, 31, 20, 59))    # yerelde 31 Mart
        self.haber(3, an=_utc(2021, 4, 15), guncelleme_zamani=_utc(2021, 5, 2))
        haber_ailesi = aile("haber")
        ozetler = {o.ay: (o.adet, o.son_degisiklik) for o in haber_ailesi.aylar()}
        self.assertEqual(set(ozetler), {"2021-03", "2021-04"})
        for ay, deger in ozetler.items():
            tek = haber_ailesi.ay_ozeti(ay)
            self.assertEqual(deger, (tek.adet, tek.son_degisiklik), ay)
        self.assertEqual(ozetler["2021-04"][0], 2)
        self.assertEqual(ozetler["2021-04"][1], _utc(2021, 5, 2))

    def test_kayit_eklenince_ay_aninda_indekste(self):
        self.haber(1, an=_utc(2025, 1, 10))
        self.assertNotIn("news_2025-03", self._indeks())
        self.haber(2, an=_utc(2025, 3, 10))
        self.assertIn("news_2025-03", self._indeks())

    def test_haber_baska_aya_tasininca_eski_ay_da_tazeleniyor(self):
        h = self.haber(1, an=_utc(2025, 1, 10))
        self.assertIn("news_2025-01", self._indeks())
        h = Haber.objects.get(pk=h.pk)
        h.yayin_zamani = _utc(2025, 2, 10)
        h.save()
        metin = self._indeks()
        self.assertNotIn("news_2025-01", metin)
        self.assertIn("news_2025-02", metin)

    @SAYFA_ACIK
    def test_aylik_dosya_onbellekte_ve_kayitla_tazeleniyor(self):
        self.haber(1, an=_utc(2025, 1, 10))
        adres = "/static/sitemap/news_2025-01.xml"
        ilk = b"".join(self.client.get(adres).streaming_content)
        with CaptureQueriesContext(connection) as y:
            ikinci = b"".join(self.client.get(adres).streaming_content)
        self.assertEqual(ilk, ikinci)
        self.assertEqual([q for q in y.captured_queries if "icerik_haber" in q["sql"]], [])
        self.haber(2, an=_utc(2025, 1, 11))
        ucuncu = b"".join(self.client.get(adres).streaming_content).decode()
        self.assertEqual(ucuncu.count("<url>"), 2)


# --------------------------------------------------------------------------
# 8. Masa kuyruğu ve konu üyeleri

class IndeksTerimleri(Temel):

    def test_masa_kuyrugu_kismi_indeks_terimini_tasiyor(self):
        """SQLite kısmi indeksi ancak koşulu sorguda AYNEN görünce kullanır;
        terim eksikken kopya veritabanında sorgu 68.300 ms sürdü."""
        sql = str(Haber.masadakiler().query)
        self.assertIn("NOT (\"icerik_haber\".\"hazirlik\" = )", sql.replace("''", ""))

    def test_indeksler_test_veritabaninda_kurulu(self):
        with connection.cursor() as c:
            kisitlar = connection.introspection.get_constraints(c, "icerik_haber")
        for ad in ("haber_okur_kismi", "haber_kategori_sira", "haber_ilce_sira",
                   "haber_olusturan_sira", "haber_masa_kismi", "haber_siralama"):
            self.assertIn(ad, kisitlar)
        # Bileşiğin öneki olan tek sütunlu indeksler kalktı.
        tekler = {tuple(v["columns"]) for v in kisitlar.values()
                  if v["index"] and not v["unique"] and len(v["columns"]) == 1}
        for sutun in ("kategori_id", "ilce_id", "olusturan_id", "yayin_zamani"):
            self.assertNotIn((sutun,), tekler)

    # Kopya veritabanında 0015 sonrası `ANALYZE`in yazdığı değerler. Küçük
    # test tablosunda her plan ucuz görünür; planlayıcıyı ÜRETİMDEKİ
    # dağılımla karar vermeye zorlamak için istatistik elle yazılır.
    URETIM_ISTATISTIGI = {
        "haber_siralama": "1038477 1 1",
        "haber_okur_kismi": "1038457 1 1 1 1",
        "haber_kategori_sira": "1038477 79883 1 1",
        "haber_ilce_sira": "1038477 57694 1 1",
        "haber_olusturan_sira": "1038477 346159 1 1",
        "haber_masa_kismi": "4 2 2 1",
        "icerik_habe_durum_8a0e62_idx": "1038477 519239 259620",
        "icerik_habe_kategor_d7bb73_idx": "1038477 79883 69232",
        "icerik_habe_olustur_eca571_idx": "1038477 346159 259620",
        "icerik_haber_slug_52e5d57c": "1038477 1",
        "sqlite_autoindex_icerik_haber_1": "1038477 1",
    }

    def _plan(self, sorgu):
        with connection.cursor() as c:
            sql, params = sorgu.query.sql_with_params()
            c.execute("EXPLAIN QUERY PLAN " + sql, params)
            return " ".join(r[3] for r in c.fetchall())

    def test_masa_kuyrugu_plani_taramaya_dusmuyor(self):
        if connection.vendor != "sqlite":
            self.skipTest("istatistik tablosu SQLite'a özgü")
        for n in range(1, 4):
            self.haber(n, durum=Haber.DURUM_PASIF, hazirlik="taslak")
        with connection.cursor() as c:
            c.execute("ANALYZE icerik_haber")
            c.execute("DELETE FROM sqlite_stat1 WHERE tbl = 'icerik_haber'")
            for idx, stat in self.URETIM_ISTATISTIGI.items():
                c.execute("INSERT INTO sqlite_stat1 (tbl, idx, stat) VALUES (%s, %s, %s)",
                          ["icerik_haber", idx, stat])
            c.execute("ANALYZE sqlite_master")      # istatistiği yeniden yükle
        tarama = "SCAN icerik_haber USING INDEX haber_siralama"
        plan = self._plan(Haber.masadakiler().filter(hazirlik="taslak")[:20])
        self.assertNotIn(tarama, plan)
        # Kontrol: terimsiz eski sorgu aynı istatistikle TARAMAYA düşüyor —
        # test gerçekten planlayıcının kararını ölçüyor.
        eski = Haber.objects.filter(durum=Haber.DURUM_PASIF,
                                    hazirlik__in=("taslak", "incelemede"),
                                    hazirlik="taslak")[:20]
        self.assertIn(tarama, self._plan(eski))


# --------------------------------------------------------------------------
# 9. Yavaş sorgu günlüğü, kalıcı bağlantı

class GunlukVeBaglanti(TestCase):

    @override_settings(YAVAS_SORGU_MS=0)
    def test_esik_ustu_sorgu_gunluge_yaziliyor(self):
        with self.assertLogs("bh.yavas_sorgu", "WARNING") as kayit:
            Haber.objects.count()
        self.assertIn("icerik_haber", kayit.output[0])

    def test_esik_alti_sorgu_yazilmiyor(self):
        from . import yavas_sorgu
        self.assertIn(yavas_sorgu.sarmalayici, connection.execute_wrappers)
        with mock.patch.object(yavas_sorgu.gunluk, "warning") as uyari:
            Haber.objects.count()
        uyari.assert_not_called()

    def test_kalici_baglanti_ayari(self):
        db = settings.DATABASES["default"]
        self.assertTrue(db.get("CONN_HEALTH_CHECKS"))
        self.assertGreater(db.get("CONN_MAX_AGE", 0), 0)
