"""Besleme gerileme testleri.

Beş şey korunuyor:

1. **Aylık bölme yerel saate göre.** Veritabanı UTC saklıyor, site +03:00.
   Ölçülmüş tuzak: arşivin en eski haberi `2021-03-31 21:02:40` (UTC) =
   yerelde 1 Nisan 2021. UTC ayına bölersek `news_2021-03.xml` diye
   olmayan bir dosya doğar; canlı indekste haber ailesi **2021-04**'te
   başlıyor.
2. **Dosya adı deseni.** `news_2026-08.xml`. Arama motorlarının kayıtlı
   olduğu adres bu; desen kayarsa 556.824 kaydın tamamı yeniden
   taranmaya muhtaç kalır.
3. **Sitemap yalnız yayındaki kaydı gösterir.** Arama motoruna 404 vaat
   etmek en pahalı hatadır.
4. **Aile defteri modelden bağımsız.** Sahte bir aile deftere yazıldığında
   indekste görünüyor — `medya` uygulaması geldiğinde `besleme`de tek
   satır değişmeyeceğinin kanıtı.
5. **RSS guid biçimi.** `{kimlik}-{md5(kimlik)}`; canlı beslemeyle birebir.
   Değişirse okuyucular bütün arşivi "yeni" sanıp yeniden gösterir.

Testler kendi adres tablosunu kullanıyor (`ROOT_URLCONF = "besleme.tests"`),
çünkü `besleme/adresler.py` bilinçli olarak köke bağlanmamış.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone as utc_dilimi
from xml.etree import ElementTree

from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import include, path
from django.utils import timezone

from icerik.models import Haber
from taksonomi.models import Kategori, KategoriTur

from . import siteharitasi
from .aileler import Aile, AyOzeti, Kayit, aile_kaydet, aile_sil, kayitli_aileler
from .rss import guid_uret
from .zaman import ay_adi, ay_sinirlari

urlpatterns = [path("", include("besleme.adresler"))]

AD_ALANI = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9",
            "news": "http://www.google.com/schemas/sitemap-news/0.9"}

KOK = "https://ornek.test"


def utc(yil, ay, gun, saat=12, dakika=0):
    """Zaman dilimi bilgili UTC anı — testin niyeti okunur kalsın diye."""
    return datetime(yil, ay, gun, saat, dakika, tzinfo=utc_dilimi.utc)


class TemelVeri(TestCase):
    """Üç kategori, birkaç haber. Uydurma metin yok; alanlar en azıyla dolu."""

    @classmethod
    def setUpTestData(cls):
        cls.gundem = Kategori.objects.create(ad="GÜNDEM", sira=1)
        KategoriTur.objects.create(kategori=cls.gundem, tur=Kategori.TUR_HABER,
                                   eski_id=1, slug="gundem")
        cls.spor = Kategori.objects.create(ad="SPOR", sira=2)
        KategoriTur.objects.create(kategori=cls.spor, tur=Kategori.TUR_HABER,
                                   eski_id=2, slug="spor")

    def haber_kur(self, kimlik, an, kategori=None, **ek):
        alanlar = {
            "id": kimlik,
            "slug": f"deneme-haber-{kimlik}",
            "baslik": f"Deneme haber {kimlik}",
            "kategori": kategori or self.gundem,
            "durum": Haber.DURUM_AKTIF,
            "yayin_zamani": an,
        }
        alanlar.update(ek)
        return Haber.objects.create(**alanlar)


# -- ay hesabı ------------------------------------------------------------

@override_settings(TIME_ZONE="Europe/Istanbul", USE_TZ=True)
class AyHesabi(SimpleTestCase):

    def test_utc_gece_yarisi_yerel_aya_dusuyor(self):
        """Arşivin en eski kaydıyla aynı durum: UTC mart, yerel nisan."""
        an = utc(2021, 3, 31, 21, 2)  # yerelde 2021-04-01 00:02
        self.assertEqual(ay_adi(an), "2021-04")

    def test_ay_sinirlari_yerel_baslangictan_kuruluyor(self):
        bas, son = ay_sinirlari("2021-04")
        # 1 Nisan 00:00 +03:00 = 31 Mart 21:00 UTC
        self.assertEqual(bas.astimezone(utc_dilimi.utc), utc(2021, 3, 31, 21, 0))
        self.assertEqual(son.astimezone(utc_dilimi.utc), utc(2021, 4, 30, 21, 0))

    def test_aralik_ayi_yila_tasiyor(self):
        bas, son = ay_sinirlari("2025-12")
        self.assertEqual(son.year, 2026)
        self.assertEqual(son.month, 1)

    def test_gecersiz_ay_reddediliyor(self):
        for kotu in ("2026-13", "2026-00", "202608", "../gizli", ""):
            self.assertFalse(siteharitasi.ay_gecerli(kotu), kotu)
        self.assertTrue(siteharitasi.ay_gecerli("2026-08"))


# -- aylık dosya ----------------------------------------------------------

@override_settings(TIME_ZONE="Europe/Istanbul", SITE_KOKU=KOK,
                   ROOT_URLCONF="besleme.tests")
class AylikDosya(TemelVeri):

    def test_utc_ay_siniri_haberi_dogru_dosyaya_giriyor(self):
        """Bu test 1 numaralı tuzağı ölçüyor; kırılırsa dosya adı kayar."""
        self.haber_kur(1, utc(2021, 3, 31, 21, 2))
        aile = self._aile()
        aylar = {o.ay: o.adet for o in aile.aylar()}
        self.assertEqual(aylar, {"2021-04": 1})

    def test_dosya_adi_deseni(self):
        from .aileler import dosya_adi
        self.assertEqual(dosya_adi(self._aile(), "2026-08"), "news_2026-08.xml")

    def test_adresler_kanonik_ve_iyi_bicimli(self):
        haber = self.haber_kur(526347, utc(2026, 8, 20), kategori=self.spor)
        kok_dugum = self._xml("2026-08")
        adresler = [d.text for d in kok_dugum.findall("sm:url/sm:loc", AD_ALANI)]
        self.assertEqual(adresler, [KOK + haber.get_absolute_url()])
        self.assertTrue(adresler[0].startswith(f"{KOK}/spor/"))

    def test_changefreq_ve_priority_canliyla_ayni(self):
        self.haber_kur(2, utc(2026, 8, 20))
        kok_dugum = self._xml("2026-08")
        self.assertEqual(kok_dugum.find("sm:url/sm:changefreq", AD_ALANI).text, "daily")
        self.assertEqual(kok_dugum.find("sm:url/sm:priority", AD_ALANI).text, "0.5")

    def test_lastmod_guncelleme_varsa_onu_soyluyor(self):
        self.haber_kur(3, utc(2026, 8, 20),
                       guncelleme_zamani=utc(2026, 8, 25, 9))
        metin = self._metin("2026-08")
        self.assertIn("<lastmod>2026-08-25T12:00:00+03:00</lastmod>", metin)

    def test_yayinda_olmayan_kayit_girmiyor(self):
        """Pasif · Silinmiş · Arşiv ve yayın zamanı boş olan listelenmez."""
        self.haber_kur(10, utc(2026, 8, 20))                    # girer
        self.haber_kur(11, utc(2026, 8, 21), durum=Haber.DURUM_PASIF)
        self.haber_kur(12, utc(2026, 8, 22), durum=Haber.DURUM_SILINMIS)
        self.haber_kur(13, utc(2026, 8, 23), durum=Haber.DURUM_ARSIV)
        self.haber_kur(14, None)
        kok_dugum = self._xml("2026-08")
        self.assertEqual(len(kok_dugum.findall("sm:url", AD_ALANI)), 1)

    def test_sayac_yazilan_adresi_bildiriyor(self):
        for kimlik in range(20, 25):
            self.haber_kur(kimlik, utc(2026, 8, kimlik))
        sayac: dict = {}
        list(siteharitasi.aylik_parcalar(KOK, self._aile(), "2026-08", sayac))
        self.assertEqual(sayac["adet"], 5)

    def test_adreste_ozel_karakter_kaciriliyor(self):
        """Kaçış kaçarsa arama motoru tek adresi değil **tüm dosyayı** atar.

        Slug'lar bugün temiz; ama `SlugField` yalnız form doğrulamasında
        denetleniyor, göç ve panel doğrudan `create()` çağırabiliyor. Tek
        bir `&` bütün ayı çöpe atar, o yüzden kaçış burada ölçülüyor.
        """
        self.haber_kur(30, utc(2026, 8, 20), slug="ekonomi-a&b-ticaret")
        metin = self._metin("2026-08")
        self.assertIn("/gundem/ekonomi-a&amp;b-ticaret-30", metin)
        kok_dugum = ElementTree.fromstring(metin)  # kaçışsız olsa patlardı
        self.assertEqual(kok_dugum.find("sm:url/sm:loc", AD_ALANI).text,
                         KOK + "/gundem/ekonomi-a&b-ticaret-30")

    def test_gecersiz_ay_hata_veriyor(self):
        with self.assertRaises(ValueError):
            list(siteharitasi.aylik_parcalar(KOK, self._aile(), "2026-13"))

    # -- yardımcılar --

    def _aile(self):
        from .aileler import aile
        return aile("haber")

    def _metin(self, ay):
        return "".join(siteharitasi.aylik_parcalar(KOK, self._aile(), ay))

    def _xml(self, ay):
        return ElementTree.fromstring(self._metin(ay))


# -- indeks ---------------------------------------------------------------

@override_settings(TIME_ZONE="Europe/Istanbul", SITE_KOKU=KOK,
                   ROOT_URLCONF="besleme.tests")
class Indeks(TemelVeri):

    def test_yalniz_dolu_aylar_listeleniyor(self):
        self.haber_kur(1, utc(2026, 8, 20))
        self.haber_kur(2, utc(2026, 5, 20))  # aradaki 6 · 7 boş
        kok_dugum = ElementTree.fromstring("".join(siteharitasi.indeks_parcalari(KOK)))
        adresler = [d.text for d in kok_dugum.findall("sm:sitemap/sm:loc", AD_ALANI)]
        self.assertEqual(adresler, [
            f"{KOK}/static/sitemap/news_2026-08.xml",
            f"{KOK}/static/sitemap/news_2026-05.xml",
        ])

    def test_aile_sirasi_canli_indeksle_ayni(self):
        """news → articles → videoGalleries → photoGalleries → authors."""
        self.haber_kur(1, utc(2026, 8, 20))
        ozet = AyOzeti("2026-08", 3, utc(2026, 8, 21))
        for anahtar, onek in (("kose", "articles"), ("video", "videoGalleries"),
                              ("galeri", "photoGalleries"), ("yazar", "authors")):
            aile_kaydet(Aile(anahtar=anahtar, dosya_oneki=onek, ad=anahtar,
                             aylar=lambda o=ozet: [o],
                             kayitlar=lambda ay: iter(())))
        self.addCleanup(lambda: [aile_sil(a) for a in
                                 ("kose", "video", "galeri", "yazar")])

        metin = "".join(siteharitasi.indeks_parcalari(KOK))
        sira = [metin.index(f"/{o}_") for o in
                ("news", "articles", "videoGalleries", "photoGalleries", "authors")]
        self.assertEqual(sira, sorted(sira))
        self.assertEqual(len(kayitli_aileler()), 5)

    def test_sahte_aile_defterden_gelince_indekse_giriyor(self):
        """`medya` uygulaması geldiğinde `besleme`de satır değişmeyecek."""
        ozet = AyOzeti("2024-02", 7, utc(2024, 2, 20))
        aile_kaydet(Aile(anahtar="galeri", dosya_oneki="photoGalleries",
                         ad="foto galeri", aylar=lambda: [ozet],
                         kayitlar=lambda ay: iter([
                             Kayit("/galeriler/bursa-208/deneme-12431",
                                   utc(2024, 2, 20))])))
        self.addCleanup(aile_sil, "galeri")

        metin = "".join(siteharitasi.indeks_parcalari(KOK))
        self.assertIn(f"{KOK}/static/sitemap/photoGalleries_2024-02.xml", metin)

        from .aileler import aile
        dosya = "".join(siteharitasi.aylik_parcalar(KOK, aile("galeri"), "2024-02"))
        self.assertIn(f"{KOK}/galeriler/bursa-208/deneme-12431", dosya)

    def test_bilinmeyen_aile_anahtari_reddediliyor(self):
        with self.assertRaises(ValueError):
            aile_kaydet(Aile(anahtar="ilan", dosya_oneki="ads", ad="ilan",
                             aylar=list, kayitlar=lambda ay: iter(())))


# -- Google News ----------------------------------------------------------

@override_settings(TIME_ZONE="Europe/Istanbul", SITE_KOKU=KOK,
                   ROOT_URLCONF="besleme.tests")
class GoogleNews(TemelVeri):

    def test_yalniz_son_48_saat(self):
        simdi = timezone.now()
        self.haber_kur(1, simdi - timedelta(hours=5))
        self.haber_kur(2, simdi - timedelta(days=9))
        from .aileler import aile
        kok_dugum = ElementTree.fromstring(
            "".join(siteharitasi.google_news_parcalari(KOK, aile("haber"))))
        adresler = [d.text for d in kok_dugum.findall("sm:url/sm:loc", AD_ALANI)]
        self.assertEqual(len(adresler), 1)
        self.assertIn("-1", adresler[0])

    def test_yayin_adi_dili_ve_baslik_var(self):
        self.haber_kur(1, timezone.now() - timedelta(hours=1))
        from .aileler import aile
        kok_dugum = ElementTree.fromstring(
            "".join(siteharitasi.google_news_parcalari(KOK, aile("haber"))))
        haber_dugum = kok_dugum.find("sm:url/news:news", AD_ALANI)
        self.assertEqual(
            haber_dugum.find("news:publication/news:name", AD_ALANI).text,
            "Bursa Hakimiyet")
        self.assertEqual(
            haber_dugum.find("news:publication/news:language", AD_ALANI).text, "tr")
        self.assertEqual(haber_dugum.find("news:title", AD_ALANI).text,
                         "Deneme haber 1")

    def test_baslikta_ozel_karakter_kaciriliyor(self):
        self.haber_kur(1, timezone.now() - timedelta(hours=1),
                       baslik="Ali & Veli <dava>")
        from .aileler import aile
        kok_dugum = ElementTree.fromstring(
            "".join(siteharitasi.google_news_parcalari(KOK, aile("haber"))))
        self.assertEqual(kok_dugum.find("sm:url/news:news/news:title", AD_ALANI).text,
                         "Ali & Veli <dava>")

    def test_aylik_dosyalarda_news_etiketi_yok(self):
        """Google News yalnız iki günü kabul ediyor; aylık dosyaya konmaz."""
        self.haber_kur(1, utc(2026, 8, 20))
        from .aileler import aile
        metin = "".join(siteharitasi.aylik_parcalar(KOK, aile("haber"), "2026-08"))
        self.assertNotIn("<news:news>", metin)


# -- görünümler -----------------------------------------------------------

@override_settings(TIME_ZONE="Europe/Istanbul", SITE_KOKU=KOK,
                   ROOT_URLCONF="besleme.tests")
class Gorunumler(TemelVeri):

    def test_indeks_adresi_canliyla_ayni(self):
        self.haber_kur(1, utc(2026, 8, 20))
        yanit = self.client.get("/static/sitemap/sitemap.xml")
        self.assertEqual(yanit.status_code, 200)
        self.assertIn("application/xml", yanit["Content-Type"])
        self.assertIn(b"news_2026-08.xml", b"".join(yanit.streaming_content))

    def test_aylik_dosya_adresi(self):
        self.haber_kur(1, utc(2026, 8, 20))
        yanit = self.client.get("/static/sitemap/news_2026-08.xml")
        self.assertEqual(yanit.status_code, 200)
        govde = b"".join(yanit.streaming_content).decode("utf-8")
        self.assertEqual(govde.count("<url>"), 1)

    def test_kayitsiz_aile_ve_bozuk_ay_404(self):
        """Tanınmayan önek, geçersiz ay ve boş ay 404 vermeli.

        `articles` (köşe yazısı) buradan çıkarıldı: `medya` uygulaması
        deftere kaydolduğundan beri **kayıtlı bir aile**. Kayıtsız aile
        örneği olarak defterde hiç bulunmayan bir önek kullanılıyor;
        aksi hâlde test, aile eklendiği anda kırılır ve eklenen ailenin
        çalıştığını yanlışlıkla hata sayar.
        """
        for adres in ("/static/sitemap/news_2026-13.xml",
                      "/static/sitemap/rastgele_2026-08.xml",
                      "/static/sitemap/olmayanAile_2026-08.xml"):
            self.assertEqual(self.client.get(adres).status_code, 404, adres)

    def test_robots_iki_sitemap_satiri_veriyor(self):
        govde = self.client.get("/robots.txt").content.decode("utf-8")
        self.assertIn(f"Sitemap: {KOK}/static/sitemap/sitemap.xml", govde)
        self.assertIn(f"Sitemap: {KOK}/static/sitemap/googleNews.xml", govde)
        self.assertIn("Disallow: /panel/", govde)


# -- RSS ------------------------------------------------------------------

@override_settings(TIME_ZONE="Europe/Istanbul", SITE_KOKU=KOK,
                   ROOT_URLCONF="besleme.tests")
class Rss(TemelVeri):

    def test_guid_canli_beslemeyle_ayni_bicimde(self):
        """Canlı örnek: 1697447 → 1697447-a91091f5b65ed9c76d27c2eac39b8a76."""
        self.assertEqual(
            guid_uret(1697447),
            "1697447-" + hashlib.md5(b"1697447").hexdigest())

    def test_genel_besleme_yeniden_eskiye_diziliyor(self):
        self.haber_kur(1, utc(2026, 8, 20))
        self.haber_kur(2, utc(2026, 8, 25))
        kok_dugum = self._xml("/rss")
        basliklar = [d.text for d in kok_dugum.findall("channel/item/title")]
        self.assertEqual(basliklar, ["Deneme haber 2", "Deneme haber 1"])

    def test_baglanti_mutlak_ve_kanonik(self):
        haber = self.haber_kur(1, utc(2026, 8, 20), kategori=self.spor)
        kok_dugum = self._xml("/rss")
        self.assertEqual(kok_dugum.find("channel/item/link").text,
                         KOK + haber.get_absolute_url())
        self.assertEqual(kok_dugum.find("channel/item/guid").text, guid_uret(1))
        self.assertEqual(kok_dugum.find("channel/item/category").text, "SPOR")

    def test_rss_kapali_haber_beslemede_yok(self):
        """§4 alan sözleşmesi: editör haberi beslemeden çıkarabiliyor."""
        self.haber_kur(1, utc(2026, 8, 20), rss=False)
        self.haber_kur(2, utc(2026, 8, 21), rss=True)
        kok_dugum = self._xml("/rss")
        self.assertEqual(len(kok_dugum.findall("channel/item")), 1)

    def test_sy_etiketleri_kanalda(self):
        self.haber_kur(1, utc(2026, 8, 20))
        govde = self.client.get("/rss").content.decode("utf-8")
        self.assertIn("<sy:updatePeriod>hourly</sy:updatePeriod>", govde)
        self.assertIn("<sy:updateFrequency>2</sy:updateFrequency>", govde)

    def test_kategori_beslemesi_suzuyor(self):
        self.haber_kur(1, utc(2026, 8, 20), kategori=self.spor)
        self.haber_kur(2, utc(2026, 8, 21), kategori=self.gundem)
        kok_dugum = self._xml("/rss/spor")
        basliklar = [d.text for d in kok_dugum.findall("channel/item/title")]
        self.assertEqual(basliklar, ["Deneme haber 1"])

    def test_bilinmeyen_kategori_404(self):
        self.assertEqual(self.client.get("/rss/olmayan").status_code, 404)

    def test_gorseli_olmayan_haberde_media_content_yok(self):
        """Arşivin %99,98'inde yerel görsel yok; ölü adres yayılmamalı."""
        self.haber_kur(1, utc(2026, 8, 20),
                       gorsel_url="https://eski.example/silinmis.jpg")
        self.assertNotIn("media:content", self.client.get("/rss").content.decode())

    def _xml(self, adres):
        yanit = self.client.get(adres)
        self.assertEqual(yanit.status_code, 200)
        return ElementTree.fromstring(yanit.content)
