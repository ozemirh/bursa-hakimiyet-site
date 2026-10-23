"""İlgili haberler — arama indeksinden aday (Paket L2, 19 Ekim 2026).

Ortak testler iki motorda da koşar (SQLite yedek yolu, PostgreSQL asıl
yol); motora özgü olanlar `skipUnless(PG)`. Sözleşme `icerik/ilgili.py`
başında: aday = pencere içinde normalize başlıkta çapayla KELİME BAŞINDA
eşleşen yayındaki haber; puan ortak köklerden; dolgu aynı kategoriden.
"""

from __future__ import annotations

from datetime import timedelta
from unittest import mock, skipUnless

from django.core.management import call_command
from django.db import connection
from django.test import TestCase
from django.utils import timezone

from taksonomi.models import Kategori, KategoriTur

from . import ilgili
from .models import Haber

PG = connection.vendor == "postgresql"


class Temel(TestCase):

    @classmethod
    def setUpTestData(cls):
        call_command("taksonomi_kur", verbosity=0)
        cls.gundem = KategoriTur.objects.get(tur=Kategori.TUR_HABER, slug="gundem").kategori
        cls.spor = KategoriTur.objects.get(tur=Kategori.TUR_HABER, slug="spor").kategori
        cls.an = timezone.now() - timedelta(days=200)
        cls.sayac = 970000

    @classmethod
    def ekle(cls, baslik, gun=0, kategori=None, **ek):
        cls.sayac += 1
        alanlar = dict(id=cls.sayac, slug=f"ilgili-{cls.sayac}", baslik=baslik,
                       spot="", govde="<p>a</p><p>b</p>",
                       kategori=kategori or cls.gundem, durum=Haber.DURUM_AKTIF,
                       yayin_zamani=cls.an + timedelta(days=gun))
        alanlar.update(ek)
        return Haber.objects.create(**alanlar)


class AdayVePuan(Temel):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.ana = cls.ekle("Pfizer aşısı İnegöl'de dağıtılmaya başlandı")
        cls.yakin = [
            cls.ekle("Pfizer aşısında ikinci doz takvimi açıklandı", gun=-3),
            cls.ekle("İNEGÖL'DE AŞISI BİTEN MERKEZ", gun=2),     # tümü büyük harf
            cls.ekle("Pfizer ve BioNTech yeni veriyi paylaştı", gun=10),
        ]
        cls.uzak = cls.ekle("Pfizer yıllık raporunu yayımladı", gun=75)   # pencere dışı
        cls.alt_dizi = cls.ekle("Superpfizerco hisseleri yükseldi", gun=1)  # kelime ortası
        cls.yayinda_degil = cls.ekle("Pfizer taslak haberi", gun=1, durum=Haber.DURUM_PASIF)
        cls.ilgisiz = [cls.ekle(f"Spor kulübünde {n}. antrenman", gun=n, kategori=cls.spor)
                       for n in range(3)]
        # Dolgu adayları: aynı kategori, haberden ÖNCE, başlıkça ilgisiz.
        cls.dolgu = [cls.ekle(f"sıradan gündem notu {n}", gun=-n) for n in range(1, 6)]

    def test_baslikca_yakinlar_once_dolgu_sonra(self):
        sonuc = ilgili.bul(self.ana, adet=6)
        kimlikler = [h.pk for h in sonuc]
        self.assertEqual(len(sonuc), 6)
        self.assertEqual(kimlikler[:3], [h.pk for h in self.yakin])   # puan sırası
        # Pencere dışı, kelime ortası ve yayında olmayan aday DEĞİL; dolgu
        # aynı kategoriden ve haberin kendi döneminden (geriye doğru).
        for h in (self.uzak, self.alt_dizi, self.yayinda_degil, self.ana):
            self.assertNotIn(h.pk, kimlikler[:3])
        self.assertNotIn(self.ana.pk, kimlikler)
        self.assertNotIn(self.yayinda_degil.pk, kimlikler)
        for h in sonuc[3:]:
            self.assertEqual(h.kategori_id, self.gundem.pk)
            self.assertLessEqual(h.yayin_zamani, self.ana.yayin_zamani)

    def test_tumu_buyuk_harf_baslik_aday(self):
        """Eski PG yolu `UPPER(baslik) LIKE UPPER('%inegöl%')` idi ve derlemeye
        bağlıydı; normalize başlıkta "İNEGÖL" de "inegol" kelimesidir."""
        adaylar = self._adaylar(self.ana)
        self.assertIn(self.yakin[1].pk, adaylar)

    def test_aday_kelime_basinda_ve_pencerede(self):
        adaylar = self._adaylar(self.ana)
        self.assertEqual(adaylar, {h.pk for h in self.yakin})

    def test_haric_listesi_atlanir(self):
        sonuc = ilgili.bul(self.ana, adet=6, haric=[self.yakin[0].pk])
        self.assertNotIn(self.yakin[0].pk, [h.pk for h in sonuc])

    def test_onbellekten_ikinci_cagri_aday_sorgusu_acmaz(self):
        ilgili.bul(self.ana, adet=6)
        with self.assertNumQueries(1):      # yalnız _nesneler
            ilgili.bul(self.ana, adet=6)

    def _adaylar(self, haber):
        capalar = ilgili._capalar(haber.baslik)[:ilgili.EN_COK_CAPA]
        bas = haber.yayin_zamani - timedelta(days=ilgili.PENCERE_GUN)
        son = haber.yayin_zamani + timedelta(days=ilgili.PENCERE_GUN)
        return {k for k, _, _ in ilgili._adaylar(
            haber, ilgili._terimler(capalar), bas, son, {haber.pk})}


class KimlikAraligi(Temel):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.haberler = [cls.ekle(f"Sıradan haber {n}", gun=n) for n in range(10)]
        # Yeniden tarihlenmiş eski kayıt: kimliği küçük, zamanı pencerede.
        cls.aykiri = cls.ekle("Yeniden tarihlenen eski kayıt", gun=1, id=100)

    def test_aralik_pencereyi_kapsar_aykiriyi_disarida_birakir(self):
        bas = self.an
        son = self.an + timedelta(days=9)
        alt, ust = ilgili.kimlik_araligi(bas, son)
        self.assertEqual(alt, self.haberler[0].pk)
        self.assertEqual(ust, self.haberler[-1].pk)

    def test_bugune_degen_pencerede_ust_sinir_yok(self):
        alt, ust = ilgili.kimlik_araligi(self.an, timezone.now() + timedelta(days=1))
        self.assertIsNone(ust)

    def test_bos_pencere(self):
        uzak = self.an - timedelta(days=3000)
        self.assertIsNone(ilgili.kimlik_araligi(uzak, uzak + timedelta(days=1)))


class AgirCapa(TestCase):

    def test_agir_karari_istatistikten(self):
        sozluk = {"bursa": 0.13, "bursaspor": 0.016, "pfizer": 0.0006, "turkiye": 0.025}
        self.assertTrue(ilgili.agir_mi(["burs"], sozluk))
        self.assertFalse(ilgili.agir_mi(["pfizer"], sozluk))
        self.assertFalse(ilgili.agir_mi(["turki"], sozluk))       # %2,5 < %3
        self.assertFalse(ilgili.agir_mi(["mustafa", "kemal"], sozluk))
        self.assertFalse(ilgili.agir_mi(["burs"], {}))            # istatistik yok

    def test_sorgu_agir_capayi_gine_sokmaz(self):
        with mock.patch.object(ilgili, "siklik", return_value={"bursa": 0.13}):
            sql, parametre = ilgili._pg_aday_sorgusu(
                500, [["burs"], ["pfizer"]], (100, 900), 1)
        self.assertIn("('pfizer':*)", parametre)
        self.assertNotIn("burs", " ".join(str(p) for p in parametre if "':*" in str(p)))
        self.assertEqual(sql.count("strpos(baslik, %s)"), 2)   # iki yön
        self.assertIn(" burs", parametre)


@skipUnless(PG, "PostgreSQL'e özgü: ifade GIN indeksi ve iki yönlü tarama")
class PostgresYolu(Temel):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.ana = cls.ekle("Bursa'da Pfizer aşısı kuyruğu")
        cls.digerleri = [cls.ekle(f"Bursa'da aşı kuyruğu {n}. gün", gun=n - 5)
                         for n in range(10)]
        cls.digerleri.append(cls.ekle("Pfizer aşısında yeni dönem", gun=4))

    def test_indeks_var(self):
        with connection.cursor() as imlec:
            imlec.execute("SELECT 1 FROM pg_indexes WHERE indexname = %s",
                          ["haberarama_baslik_vektor_gin"])
            self.assertIsNotNone(imlec.fetchone())

    def test_agir_ve_hafif_yol_ayni_sonucu_verir(self):
        """"burs" çapası ağır sayılsa da (iki yönlü tarama) hafif sayılsa da
        (GIN) sonuç aynı — yol bir başarım kararıdır, anlam değil."""
        with mock.patch.object(ilgili, "siklik", return_value={}):
            hafif = [h.pk for h in ilgili.bul(self.ana, adet=6)]
        from django.core.cache import cache
        cache.clear()
        with mock.patch.object(ilgili, "siklik", return_value={"bursa": 0.5}):
            agir = [h.pk for h in ilgili.bul(self.ana, adet=6)]
        self.assertEqual(hafif, agir)
        self.assertEqual(len(hafif), 6)
        self.assertEqual(hafif[0], self.digerleri[-1].pk)   # Pfizer + aşı: puanı en yüksek
        self.assertTrue(set(hafif[1:]) <= {h.pk for h in self.digerleri[:-1]})

    def test_siklik_pg_istatistiginden_okunur(self):
        with connection.cursor() as imlec:
            imlec.execute("ANALYZE icerik_haberarama")
        from django.core.cache import cache
        cache.delete("ilgili:siklik")
        sozluk = ilgili.siklik()
        self.assertIsInstance(sozluk, dict)
        if sozluk:   # küçük test verisinde istatistik boş olabilir
            self.assertTrue(all(isinstance(f, float) for f in sozluk.values()))
