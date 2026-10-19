"""Paket G — SEO eşitliği: meta, kanonik, JSON-LD, adres düzeni (19 Ekim 2026).

Her madde için en az bir ölçüm: meta bloğu her sayfa türünde var; kanonik
`SITE_KOKU`dan (istek konağından değil); JSON-LD ayrıştırılabilir, Google'ın
zorunlu alanlarını taşıyor ve betik kapatılamıyor; /amp, sondaki eğik çizgi ve
/arama 301 (utm korunur); geçersiz ?sayfa= 404; ince konu noindex; sosyal
bağlantıda UTM; sitemap indeksinde standart dışı nitelik yok; /favicon.ico 200.
"""

import json
import re
from datetime import timedelta
from types import SimpleNamespace

from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone

from medya.models import FotoGaleri, KoseYazisi, Video, Yazar
from taksonomi.models import Ilce, Kategori, KategoriTur

from . import seo
from .models import Haber, Konu, KonuHaber

KOK = "https://www.ornek-hakimiyet.test"

_LD = re.compile(r'<script type="application/ld\+json">(.*?)</script>', re.S)


def _meta(html, nitelik, ad):
    m = re.search(rf'<meta {nitelik}="{re.escape(ad)}" content="([^"]*)"', html)
    return m.group(1) if m else None


def _kanonik(html):
    bulunan = re.findall(r'<link rel="canonical" href="([^"]+)"', html)
    return bulunan


def _ld(html):
    return [json.loads(ham) for ham in _LD.findall(html)]


def _tur(ld, tur):
    return next(x for x in ld if x.get("@type") == tur)


@override_settings(SITE_KOKU=KOK, SAYFA_ONBELLEK_SANIYE=0)
class SeoTabani(TestCase):

    @classmethod
    def setUpTestData(cls):
        call_command("taksonomi_kur", verbosity=0)
        cls.gundem = KategoriTur.objects.get(tur=Kategori.TUR_HABER, slug="gundem").kategori
        cls.ilce = Ilce.objects.first()
        simdi = timezone.now() - timedelta(hours=2)
        cls.haber = Haber.objects.create(
            id=990001, slug="nilufer-de-kopru", baslik="Nilüfer'de köprü açıldı",
            spot="Köprü <b>bugün</b> açıldı.", govde="<p>Gövde bir.</p><p>İki.</p>",
            kategori=cls.gundem, ilce=cls.ilce, yayin_zamani=simdi,
            guncelleme_zamani=simdi + timedelta(minutes=45))
        cls.esit = Haber.objects.create(
            id=990002, slug="esit-zaman", baslik="Eşit zamanlı haber",
            spot="Spot", kategori=cls.gundem, yayin_zamani=simdi, guncelleme_zamani=simdi)
        cls.yazar = Yazar.objects.create(id=76, slug="namik-goz", ad="Namık GÖZ",
                                         sayfasi_tarandi=True)
        cls.yazi = KoseYazisi.objects.create(id=32099, slug="bir-yazi", baslik="Bir yazı",
                                             govde="<p>Gövde</p>", yazar=cls.yazar,
                                             yayin_zamani=simdi)
        foto = KategoriTur.objects.get(tur=Kategori.TUR_FOTO, eski_id=208)
        cls.galeri = FotoGaleri.objects.create(id=12431, slug="galeri", baslik="Galeri",
                                               kategori=foto.kategori, kategori_dilimi="bursa-208",
                                               yayin_zamani=simdi)
        vid = KategoriTur.objects.get(tur=Kategori.TUR_VIDEO, eski_id=308)
        cls.video = Video.objects.create(id=91994, slug="video", baslik="Video",
                                         kategori=vid.kategori, kategori_dilimi="bursa-308",
                                         yayin_zamani=simdi)
        bugun = timezone.localdate()
        cls.ince = Konu.objects.create(ad="İnce dosya", slug="ince", onay=Konu.ONAY_ONAYLI,
                                       baslangic=bugun, bitis=bugun, haber_sayisi=2)
        cls.kalin = Konu.objects.create(ad="Kalın dosya", slug="kalin", onay=Konu.ONAY_ONAYLI,
                                        baslangic=bugun, bitis=bugun, haber_sayisi=7)
        KonuHaber.objects.create(konu=cls.ince, haber=cls.haber, tarih=bugun)

    def _al(self, yol, **ek):
        yanit = self.client.get(yol, HTTP_HOST="127.0.0.1:8751", **ek)
        self.assertEqual(yanit.status_code, 200, yol)
        return yanit.content.decode()


class MetaBlogu(SeoTabani):
    """Yirmi sayfa türünde meta bloğu: robots, kanonik, OG, Twitter, RSS, simge."""

    def _yollar(self):
        return [
            "/", self.haber.get_absolute_url(), "/gundem", f"/ilce/{self.ilce.slug}",
            "/ilceler", "/konular", "/konu/ince", "/konu/kalin", "/son-haberler",
            "/bursaspor", "/yazarlar", self.yazar.get_absolute_url(),
            self.yazi.get_absolute_url(), "/galeriler", self.galeri.get_absolute_url(),
            "/videolar", self.video.get_absolute_url(), "/resmi-ilan",
            "/nobetci-eczane", "/veri-kaynaklari", "/ara?q=köprü",
        ]

    def test_her_sayfa_turunde_meta_var_ve_json_ayristirilir(self):
        for yol in self._yollar():
            with self.subTest(yol=yol):
                html = self._al(yol)
                self.assertIsNotNone(_meta(html, "name", "robots"))
                for ad in ("og:site_name", "og:locale", "og:type", "og:title",
                           "og:description", "og:url", "og:image",
                           "og:image:width", "og:image:height", "og:image:alt"):
                    self.assertTrue(_meta(html, "property", ad), ad)
                self.assertEqual(_meta(html, "property", "og:locale"), "tr_TR")
                self.assertEqual(_meta(html, "name", "twitter:card"), "summary_large_image")
                self.assertTrue(_meta(html, "name", "twitter:image"))
                self.assertTrue(_meta(html, "property", "og:image").startswith(KOK))
                self.assertIn(f'href="{KOK}/rss"', html)
                self.assertIn('rel="apple-touch-icon"', html)
                self.assertTrue(_meta(html, "name", "theme-color").startswith("#"))
                self.assertNotIn("127.0.0.1", html.split("</head>")[0])
                _ld(html)        # ayrıştırılamazsa json hatası

    def test_dizine_acik_sayfada_buyuk_onizleme(self):
        robots = _meta(self._al("/"), "name", "robots")
        self.assertIn("max-image-preview:large", robots)
        self.assertIn("max-snippet:-1", robots)

    def test_arama_ve_404_noindex_ve_kanoniksiz(self):
        html = self._al("/ara?q=köprü")
        self.assertEqual(_meta(html, "name", "robots"), "noindex, follow")
        self.assertEqual(_kanonik(html), [])
        yanit = self.client.get("/gundem/olmayan-123456789")
        self.assertEqual(yanit.status_code, 404)

    def test_og_aciklama_meta_aciklamayla_ayni(self):
        html = self._al(self.haber.get_absolute_url())
        self.assertEqual(_meta(html, "name", "description"),
                         _meta(html, "property", "og:description"))
        self.assertEqual(_meta(html, "property", "og:description"), "Köprü bugün açıldı.")
        self.assertEqual(_meta(html, "property", "og:type"), "article")
        self.assertTrue(_meta(html, "property", "article:published_time"))

    def test_seo_basligi_title_ve_og_title(self):
        Haber.objects.filter(pk=self.haber.pk).update(seo_baslik="Nilüfer köprüsü açıldı")
        html = self._al(self.haber.get_absolute_url())
        self.assertIn("<title>Nilüfer köprüsü açıldı — Bursa Hakimiyet</title>", html)
        self.assertEqual(_meta(html, "property", "og:title"), "Nilüfer köprüsü açıldı")
        # Görünen h1 haberin kendi başlığı kalır.
        self.assertIn("<h1>Nilüfer&#x27;de köprü açıldı</h1>", html)

    def test_bolum_rss_alternate(self):
        self.assertIn(f'href="{KOK}/rss/gundem"', self._al("/gundem"))
        self.assertIn(f'href="{KOK}/rss/gundem"', self._al(self.haber.get_absolute_url()))

    def test_favicon(self):
        yanit = self.client.get("/favicon.ico")
        self.assertEqual(yanit.status_code, 200)
        self.assertEqual(yanit["Content-Type"], "image/x-icon")


class Kanonik(SeoTabani):

    def test_kanonik_site_kokunden_tek_ve_utm_siz(self):
        for yol, beklenen in (("/", f"{KOK}/"),
                              (self.haber.get_absolute_url() + "?utm_source=x",
                               KOK + self.haber.get_absolute_url()),
                              ("/gundem?fbclid=1", f"{KOK}/gundem"),
                              (f"/ilce/{self.ilce.slug}", f"{KOK}/ilce/{self.ilce.slug}"),
                              ("/konular", f"{KOK}/konular"),
                              ("/yazarlar", f"{KOK}/yazarlar"),
                              ("/resmi-ilan?tur=ihale", f"{KOK}/resmi-ilan")):
            with self.subTest(yol=yol):
                self.assertEqual(_kanonik(self._al(yol)), [beklenen])

    def test_sayfali_liste_kendi_kanonigi(self):
        for i in range(45):
            Haber.objects.create(id=991000 + i, slug=f"h-{i}", baslik=f"Haber {i}",
                                 kategori=self.gundem,
                                 yayin_zamani=timezone.now() - timedelta(minutes=i + 1))
        html = self._al("/gundem?sayfa=2")
        self.assertEqual(_kanonik(html), [f"{KOK}/gundem?sayfa=2"])
        self.assertIn("— Sayfa 2 —", html.split("</title>")[0])
        self.assertEqual(_kanonik(self._al("/gundem?sayfa=1")), [f"{KOK}/gundem"])


class SayfaNumarasi(SeoTabani):

    def test_gecersiz_ve_aralik_disi_sayfa_404(self):
        for yol in ("/gundem?sayfa=abc", "/gundem?sayfa=0", "/gundem?sayfa=-2",
                    "/gundem?sayfa=999", "/son-haberler?sayfa=50", "/konular?sayfa=9",
                    "/galeriler?sayfa=5", f"/ilce/{self.ilce.slug}?sayfa=x"):
            with self.subTest(yol=yol):
                self.assertEqual(self.client.get(yol).status_code, 404)

    def test_bos_ve_birinci_sayfa_200(self):
        for yol in ("/gundem?sayfa=", "/gundem?sayfa=1", "/videolar?sayfa=1"):
            with self.subTest(yol=yol):
                self.assertEqual(self.client.get(yol).status_code, 200)


class AdresDuzeni(SeoTabani):

    def _301(self, yol, hedef):
        yanit = self.client.get(yol)
        self.assertEqual(yanit.status_code, 301, yol)
        self.assertEqual(yanit["Location"], hedef)

    def test_amp_ikizi_kanonige(self):
        adres = self.haber.get_absolute_url()
        self._301("/amp" + adres, adres)
        self._301("/amp" + adres + "?utm_source=x&utm_medium=social",
                  adres + "?utm_source=x&utm_medium=social")
        self._301("/amp/gundem/yanlis-slug-990001", "/gundem/yanlis-slug-990001")
        self._301("/amp", "/")

    def test_amp_yanlis_slug_iki_halkada_kanonige(self):
        yanit = self.client.get("/amp/gundem/yanlis-990001", follow=True)
        self.assertEqual(yanit.redirect_chain[-1][0], self.haber.get_absolute_url())
        self.assertLessEqual(len(yanit.redirect_chain), 2)

    def test_sondaki_egik_cizgi(self):
        self._301("/gundem/", "/gundem")
        self._301(f"/ilce/{self.ilce.slug}/?utm_source=facebook",
                  f"/ilce/{self.ilce.slug}?utm_source=facebook")
        self._301(self.haber.get_absolute_url() + "/", self.haber.get_absolute_url())

    def test_panel_ve_yonetim_egik_cizgisi_korunur(self):
        self.assertNotEqual(self.client.get("/panel/").status_code, 301)
        self.assertNotEqual(self.client.get("/yonetim/").status_code, 301)

    def test_eski_arama_adresi(self):
        self._301("/arama?ara=k%C3%B6pr%C3%BC", "/ara?q=k%C3%B6pr%C3%BC")
        self._301("/arama?ara=x&utm_source=x", "/ara?q=x&utm_source=x")
        self._301("/arama", "/ara")

    def test_kanonik_301_utm_korur(self):
        self._301("/gundem/yanlis-slug-990001?utm_source=x",
                  self.haber.get_absolute_url() + "?utm_source=x")
        self._301("/yazarlar/namik-goz-76/yanlis-32099?utm_medium=social",
                  self.yazi.get_absolute_url() + "?utm_medium=social")


class YapilandirilmisVeri(SeoTabani):

    def test_haber_newsarticle_zorunlu_ve_onerilen_alanlar(self):
        ld = _ld(self._al(self.haber.get_absolute_url()))
        m = _tur(ld, "NewsArticle")
        for alan in ("headline", "description", "datePublished", "dateModified",
                     "author", "publisher", "mainEntityOfPage", "articleSection",
                     "inLanguage", "url"):
            self.assertIn(alan, m)
        self.assertEqual(m["url"], KOK + self.haber.get_absolute_url())
        self.assertEqual(m["mainEntityOfPage"]["@id"], m["url"])
        self.assertEqual(m["inLanguage"], "tr-TR")
        self.assertEqual(m["publisher"]["@type"], "NewsMediaOrganization")
        self.assertTrue(m["publisher"]["logo"]["url"].startswith(KOK))
        self.assertEqual(m["author"][0], {"@type": "Organization", "name": "Bursa Hakimiyet",
                                          "url": KOK + "/"})
        self.assertEqual(m["articleSection"], "Gündem")
        self.assertNotEqual(m["datePublished"], m["dateModified"])
        self.assertLessEqual(len(m["headline"]), 110)

    def test_muhabir_varsa_person(self):
        Haber.objects.filter(pk=self.haber.pk).update(muhabir="Ayşe Yılmaz")
        m = _tur(_ld(self._al(self.haber.get_absolute_url())), "NewsArticle")
        self.assertEqual(m["author"], [{"@type": "Person", "name": "Ayşe Yılmaz"}])

    def test_esit_guncelleme_degisiklik_sayilmaz(self):
        html = self._al(self.esit.get_absolute_url())
        m = _tur(_ld(html), "NewsArticle")
        self.assertEqual(m["datePublished"], m["dateModified"])
        self.assertNotIn("Güncelleme:", html)

    def test_gorunur_guncelleme_tarih_ve_saat(self):
        html = self._al(self.haber.get_absolute_url())
        g = timezone.localtime(self.haber.guncelleme_zamani)
        self.assertRegex(html, r'Güncelleme: <time datetime="[^"]+">\d{1,2} \w+ \d{4}, \d\d:\d\d</time>')
        self.assertIn(f'datetime="{g.isoformat()}"', html)

    def test_haber_kirintisi(self):
        k = _tur(_ld(self._al(self.haber.get_absolute_url())), "BreadcrumbList")
        adlar = [o["name"] for o in k["itemListElement"]]
        self.assertEqual(adlar, ["Anasayfa", "Gündem", "Nilüfer'de köprü açıldı"])
        self.assertEqual(k["itemListElement"][1]["item"], f"{KOK}/gundem")

    def test_anasayfa_website_ve_kurulus(self):
        ld = _ld(self._al("/"))
        site = _tur(ld, "WebSite")
        self.assertEqual(site["potentialAction"]["target"]["urlTemplate"],
                         KOK + "/ara?q={search_term_string}")
        kurulus = _tur(ld, "NewsMediaOrganization")
        self.assertIn("https://x.com/b_hakimiyet", kurulus["sameAs"])
        self.assertEqual(len(kurulus["sameAs"]), 4)

    def test_kategori_ve_ilce_kirintisi(self):
        k = _tur(_ld(self._al("/gundem")), "BreadcrumbList")
        self.assertEqual([o["name"] for o in k["itemListElement"]], ["Anasayfa", "Gündem"])
        k = _tur(_ld(self._al(f"/ilce/{self.ilce.slug}")), "BreadcrumbList")
        self.assertEqual([o["name"] for o in k["itemListElement"]],
                         ["Anasayfa", "İlçeler", self.ilce.ad])

    def test_kose_galeri_video_yazar(self):
        m = _tur(_ld(self._al(self.yazi.get_absolute_url())), "OpinionNewsArticle")
        self.assertEqual(m["author"][0]["@type"], "Person")
        self.assertEqual(m["author"][0]["name"], "Namık GÖZ")
        self.assertIn("ImageGallery", [x["@type"] for x in _ld(self._al(self.galeri.get_absolute_url()))])
        tipler = [x["@type"] for x in _ld(self._al(self.video.get_absolute_url()))]
        self.assertIn("WebPage", tipler)
        self.assertNotIn("VideoObject", tipler)     # oynatıcı gömülü değil
        p = _tur(_ld(self._al(self.yazar.get_absolute_url())), "ProfilePage")
        self.assertEqual(p["mainEntity"]["name"], "Namık GÖZ")

    def test_baslikta_betik_kapanisi_etkisiz(self):
        Haber.objects.filter(pk=self.haber.pk).update(
            baslik="KÖTÜ</script><script>alert(1)</script> & <!--")
        html = self._al(self.haber.get_absolute_url())
        self.assertNotIn("<script>alert(1)", html)
        # Başlık düz metne indirgenir; kalan `<` ve `&` JSON içinde kaçışlı.
        m = _tur(_ld(html), "NewsArticle")
        self.assertEqual(m["headline"], "KÖTÜalert(1) & <!--")
        for ham in _LD.findall(html):
            self.assertNotIn("<", ham)
            self.assertNotIn("&", ham)

    def test_gorsel_dizisi_dort_oran(self):
        h = SimpleNamespace(gorsel_yolu="/arsiv-gorsel/2026-08/a_large.jpg")
        dizi = seo.gorsel_dizisi(h)
        self.assertEqual([(g["width"], g["height"]) for g in dizi],
                         [(1200, 675), (1200, 900), (1200, 1200), (1200, 630)])
        self.assertTrue(dizi[0]["url"].startswith(KOK + "/gorsel/16x9/gorseller/2026-08/"))


class InceKonu(SeoTabani):

    def test_bes_haberin_alti_noindex(self):
        self.assertEqual(_meta(self._al("/konu/ince"), "name", "robots"), "noindex, follow")
        self.assertIn("max-image-preview:large", _meta(self._al("/konu/kalin"), "name", "robots"))


class SosyalUtm(SeoTabani):

    def test_platform_utm(self):
        from sosyal import metin
        for platform, kaynak in (("x", "x"), ("facebook", "facebook"),
                                 ("instagram", "instagram")):
            with self.subTest(platform=platform):
                adres = metin.haber_adresi(self.haber, platform)
                self.assertTrue(adres.startswith(KOK + self.haber.get_absolute_url() + "?"))
                self.assertIn(f"utm_source={kaynak}&utm_medium=social", adres)
        self.assertNotIn("utm_", metin.haber_adresi(self.haber))

    def test_gonderi_metninde_utm(self):
        from sosyal import metin
        hesap = SimpleNamespace(platform="facebook", metin_kalibi="")
        self.assertIn("utm_source=facebook&utm_medium=social",
                      metin.gonderi_metni(self.haber, hesap))


class SiteHaritasiIndeksi(SeoTabani):

    def test_kok_ogede_standart_disi_nitelik_yok(self):
        metin = b"".join(self.client.get("/static/sitemap/sitemap.xml").streaming_content).decode()
        self.assertIn('<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">', metin)
        self.assertNotIn("lastModified", metin)
