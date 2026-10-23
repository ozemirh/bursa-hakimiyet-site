"""İlçe sayfalarının kaldırılması ve menü izin listesi (20 Ekim 2026).

Kullanıcı kararları:

1. Tam menünün KATEGORİLER bölümü açık bir izin listesinden gelir
   (`baglam.MENU_KATEGORILERI`); Aktüalite menüden çıktı ama sayfası ve
   haberleri yerinde.
2. Bantta İLÇELER kalemi yerine SAĞLIK; bant 10 kalem.
3. `/ilce/<slug>` ve `/ilceler` yok: 301 ile `/bursa` (sorgu dizesi
   korunur, eğik çizgili biçim de tek halkada). `/daha-fazla?kaynak=ilce`
   404. Hiçbir okur sayfasında `/ilce/` bağlantısı kalmaz.

KORUNANLAR da burada kilitli: haberin ilçe alanı, haber detayındaki aynı
ilçeden haberler kutusu ve nöbetçi eczanenin ilçe kırılımı.
"""

import re

from django.core.management import call_command
from django.template import TemplateDoesNotExist
from django.template.loader import get_template
from django.test import TestCase
from django.urls import NoReverseMatch, reverse
from django.utils import timezone

from taksonomi.models import Ilce, Kategori, KategoriTur

from . import baglam, views
from .models import Haber
from .tests_eczane import EczaneTabani, paket
from .tests_menu import menu_blogu

#: Kullanıcının 20 Ekim 2026'da verdiği liste (görünen adlar, menüdeki
#: `baslikla` biçimiyle).
MENU_ADLARI = {"Magazin", "Dünya", "Ekonomi", "Spor", "Bursa", "Bursaspor",
               "Sağlık", "Gündem", "Teknoloji", "Yaşam", "Bursa'da Spor",
               "Savunma Sanayi"}


def _tur(slug):
    return KategoriTur.objects.get(tur=Kategori.TUR_HABER, slug=slug).kategori


class _Taban(TestCase):

    @classmethod
    def setUpTestData(cls):
        call_command("taksonomi_kur", verbosity=0)
        cls.osmangazi = Ilce.objects.get(slug="osmangazi")
        simdi = timezone.now()
        cls.haber = Haber.objects.create(
            id=975001, slug="ilceli-haber", baslik="Osmangazi'de yol çalışması",
            spot="Spot", govde="<p>Bir.</p><p>İki.</p>", kategori=_tur("bursa"),
            ilce=cls.osmangazi, yayin_zamani=simdi)
        cls.komsu = Haber.objects.create(
            id=975002, slug="ilceli-komsu", baslik="Osmangazi'de park açıldı",
            spot="Spot", govde="<p>Bir.</p><p>İki.</p>", kategori=_tur("gundem"),
            ilce=cls.osmangazi, yayin_zamani=simdi - timezone.timedelta(minutes=5))
        cls.aktualite = Haber.objects.create(
            id=975003, slug="aktualite-haberi", baslik="Aktüalite haberi duruyor",
            spot="Spot", govde="<p>Bir.</p><p>İki.</p>", kategori=_tur("aktualite"),
            yayin_zamani=simdi - timezone.timedelta(minutes=10))

    def setUp(self):
        baglam.onbellek.sil(baglam.MENU_ANAHTARI)

    def tearDown(self):
        baglam.onbellek.sil(baglam.MENU_ANAHTARI)


# -- 1. adresler -------------------------------------------------------------

class IlceAdresleriBursayaYonlenir(_Taban):

    def _301(self, yol, hedef):
        yanit = self.client.get(yol)
        self.assertEqual(yanit.status_code, 301, yol)
        self.assertEqual(yanit["Location"], hedef, yol)

    def test_ilce_sayfasi(self):
        self._301("/ilce/osmangazi", "/bursa")
        self._301("/ilce/nilufer", "/bursa")

    def test_ilce_dizini(self):
        self._301("/ilceler", "/bursa")

    def test_egik_cizgili_bicim_tek_halkada(self):
        """Paket G'nin eğik çizgi kuralı önce `/ilce/x`e, sonra `/bursa`ya
        götürseydi zincir iki halka olurdu; doğrudan `/bursa`."""
        self._301("/ilce/osmangazi/", "/bursa")
        self._301("/ilceler/", "/bursa")
        yanit = self.client.get("/ilce/osmangazi/", follow=True)
        self.assertEqual(yanit.status_code, 200)
        self.assertEqual(yanit.redirect_chain, [("/bursa", 301)])

    def test_sorgu_dizesi_korunur(self):
        self._301("/ilce/osmangazi?utm_source=facebook&utm_medium=social",
                  "/bursa?utm_source=facebook&utm_medium=social")
        self._301("/ilce/osmangazi/?utm_source=x", "/bursa?utm_source=x")
        self._301("/ilceler?utm_campaign=ekim", "/bursa?utm_campaign=ekim")
        self._301("/ilceler/?sayfa=2", "/bursa?sayfa=2")

    def test_bilinmeyen_ilce_de_yonlenir(self):
        """Sayfa türü kalktı; hangi ilçe olduğunun önemi kalmadı."""
        self._301("/ilce/ankara", "/bursa")

    def test_hedef_ayakta(self):
        self.assertEqual(self.client.get("/bursa").status_code, 200)

    def test_benzer_adresler_yakalanmaz(self):
        """Kalıp dar: eczanenin ilçe kırılımı ve haber adresleri dokunulmaz."""
        self.assertEqual(self.client.get("/nobetci-eczane/osmangazi").status_code, 200)
        self.assertEqual(self.client.get(self.haber.get_absolute_url()).status_code, 200)
        self.assertNotEqual(self.client.get("/ilce/osmangazi/fazla").status_code, 301)

    def test_daha_fazla_ilce_kaynagi_404(self):
        self.assertEqual(self.client.get(
            "/daha-fazla?kaynak=ilce&slug=osmangazi").status_code, 404)
        self.assertEqual(self.client.get(
            "/daha-fazla?kaynak=ilce&slug=osmangazi&sayfa=2").status_code, 404)

    def test_gorunum_sablon_ve_adres_adi_kalkti(self):
        for ad in ("ilce", "ilceler"):
            with self.assertRaises(NoReverseMatch):
                reverse(ad, **({"kwargs": {"slug": "osmangazi"}} if ad == "ilce" else {}))
            self.assertFalse(hasattr(views, ad), ad)
        with self.assertRaises(TemplateDoesNotExist):
            get_template("ilceler.html")
        self.assertFalse(hasattr(baglam, "VARSAYILAN_ILCE"))


# -- 2. menü izin listesi ------------------------------------------------------

class MenuIzinListesi(_Taban):

    def _kategoriler(self, yol="/"):
        menu = menu_blogu(self.client.get(yol).content.decode())
        bolum = menu[menu.index("<summary><h2>KATEGORİLER"):]
        bolum = bolum[:bolum.index("</details>")]
        return re.findall(r'<a href="/([^"]+)">([^<]+)</a>', bolum), menu

    def test_menude_tam_olarak_izin_listesi(self):
        kalemler, _ = self._kategoriler()
        self.assertEqual({s for s, _ in kalemler}, baglam.MENU_KATEGORILERI)
        self.assertEqual({a.replace("&#x27;", "'") for _, a in kalemler}, MENU_ADLARI)
        self.assertEqual(len(kalemler), 12)

    def test_resmi_ilan_menude_ayri(self):
        _, menu = self._kategoriler()
        self.assertIn('<a href="/resmi-ilan">Resmî ilanlar</a>', menu)

    def test_aktualite_menude_yok_ama_sayfasi_acik(self):
        kalemler, menu = self._kategoriler()
        self.assertNotIn("aktualite", {s for s, _ in kalemler})
        self.assertNotIn("/aktualite", menu)
        self.assertNotIn("Aktüalite", menu)
        yanit = self.client.get("/aktualite")
        self.assertEqual(yanit.status_code, 200)
        self.assertContains(yanit, "Aktüalite haberi duruyor")
        self.assertEqual(self.client.get(self.aktualite.get_absolute_url()).status_code, 200)

    def test_veritabaninda_olmayan_slug_sessizce_atlanir(self):
        """Listede olup etkin olmayan (ya da hiç olmayan) kategori menüyü
        kırmaz; yalnız eksilir."""
        Kategori.objects.filter(pk=_tur("savunma-sanayi").pk).update(aktif=False)
        kalemler, _ = self._kategoriler()
        self.assertEqual(len(kalemler), 11)
        self.assertNotIn("savunma-sanayi", {s for s, _ in kalemler})

    def test_listede_olmayan_yeni_kategori_menuye_girmez(self):
        yeni = Kategori.objects.create(ad="DENEME BÖLÜMÜ", sira=99, aktif=True)
        KategoriTur.objects.create(kategori=yeni, tur=Kategori.TUR_HABER,
                                   eski_id=99001, slug="deneme-bolumu")
        kalemler, _ = self._kategoriler()
        self.assertNotIn("deneme-bolumu", {s for s, _ in kalemler})
        self.assertEqual(len(kalemler), 12)


# -- 3. bant -------------------------------------------------------------------

class BantSaglik(_Taban):

    def _bant(self, yol="/"):
        govde = self.client.get(yol).content.decode()
        return re.search(r'<div class="kategori-liste"[^>]*>(.*?)</div>', govde, re.S).group(1)

    def test_on_kalem_saglik_var_ilceler_yok(self):
        bant = self._bant()
        adlar = re.findall(r"<a[^>]*>([^<]+)</a>", bant)
        self.assertEqual(len(adlar), 10)
        self.assertIn("SAĞLIK", adlar)
        self.assertNotIn("İLÇELER", adlar)
        self.assertIn('href="/saglik"', bant)
        self.assertNotIn("/ilce", bant)
        # YAZARLAR bantta kalıyor; dar ekran dörtlüsü değişmedi.
        self.assertIn("YAZARLAR", adlar)
        self.assertEqual(baglam.MOBIL_BANT, {"BURSA", "BURSASPOR", "GÜNDEM", "SPOR"})

    def test_saglik_sayfasinda_kalem_etkin(self):
        bant = self._bant("/saglik")
        self.assertIn('href="/saglik" aria-current="page">SAĞLIK</a>', bant)


# -- 4. hiçbir sayfada ilçe sayfası bağlantısı yok -----------------------------

class IlceBaglantisiKalmadi(EczaneTabani):
    """Eczane tabanı: geçici canlı veri kökü (eczane sayfaları veriyle)."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        _Taban.setUpTestData.__func__(cls)

    def test_okur_sayfalarinda_ilce_baglantisi_yok(self):
        self._yaz(paket())
        for yol in ("/", self.haber.get_absolute_url(), "/gundem", "/bursa",
                    "/saglik", "/aktualite", "/son-haberler", "/nobetci-eczane",
                    "/nobetci-eczane/osmangazi"):
            with self.subTest(yol=yol):
                yanit = self._al(yol)
                self.assertEqual(yanit.status_code, 200, yol)
                metin = yanit.content.decode()
                self.assertNotIn('href="/ilce', metin, yol)
                self.assertNotIn("menu-ilce", metin, yol)

    def test_haber_kirintisinda_ilce_yok_kutusu_duruyor(self):
        """Kırıntı kararı: ilçe kırıntıdan TAMAMEN çıktı (sayfası olmayan bir
        hiyerarşi basamağı olmasın). İlçe bilgisi okurdan kaybolmadı: raydaki
        aynı ilçeden haberler kutusu ilçe adıyla duruyor."""
        metin = self._al(self.haber.get_absolute_url()).content.decode()
        kirinti = metin[metin.index('<nav class="kirinti"'):]
        kirinti = kirinti[:kirinti.index("</nav>")]
        # Anasayfa › Bursa › başlık (başlığın kendisi "Osmangazi'de…" der;
        # ölçülen şey ilçenin AYRI bir basamak olmaması).
        self.assertEqual(re.findall(r'<li><a href="([^"]+)">', kirinti), ["/", "/bursa"])
        self.assertEqual(kirinti.count("<li>"), 3)
        self.assertIn("OSMANGAZİ HABERLERİ", metin)
        self.assertIn(self.komsu.get_absolute_url(), metin)

    def test_eczane_ilce_kirilimi_calisiyor(self):
        """KORUNAN: nöbetçi eczanenin ilçe ilçe listesi ve ilçe sayfaları."""
        self._yaz(paket())
        genel = self._al("/nobetci-eczane").content.decode()
        for slug in ("osmangazi", "nilufer"):
            self.assertIn(f'href="/nobetci-eczane/{slug}"', genel)
        self.assertIn('id="ilce-osmangazi"', genel)
        ilce = self._al("/nobetci-eczane/osmangazi")
        self.assertEqual(ilce.status_code, 200)
        self.assertContains(ilce, "Uludağ Eczanesi")
        self.assertNotContains(ilce, "Metropol Eczanesi")

    def test_haberin_ilce_alani_korunuyor(self):
        self.haber.refresh_from_db()
        self.assertEqual(self.haber.ilce, self.osmangazi)
        self.assertEqual(Ilce.objects.count(), 17)
