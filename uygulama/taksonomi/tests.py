"""Adres sözleşmesi gerileme testleri.

Bu testlerin varlık sebebi: kalıp SIRASI bozulursa yazar sayfaları haber
sanılır ve sessizce kaybolur. `adres_dogrula` komutu 556.824 haber adresini
tarar ama diğer dört aileyi göremez — bu dosya onu kapatır.
"""

from django.test import SimpleTestCase, TestCase
from django.urls import Resolver404, resolve
from django.utils import timezone


class AdresSozlesmesi(SimpleTestCase):
    """Ölçülmüş gerçek adresler. Değerler canlı siteden alındı."""

    ORNEKLER = [
        ("/spor/lucescu-allahyar-sayyadmanesh-i-istiyor-526347", "haber", 526347),
        ("/yazarlar/namik-goz-76/gokyuzune-bakarken-hafizamizi-da-koruyalim-32099", "kose", 32099),
        ("/galeriler/bursa-208/bursa-da-kizil-sirtli-orumcekkusu-12431", "galeri", 12431),
        ("/videolar/bursa-308/bursa-da-firar-eden-50-koyun-91994", "video", 91994),
        ("/yazarlar/namik-goz-76", "yazar", 76),
    ]

    def test_bes_aile_dogru_cozuluyor(self):
        for yol, tur, kimlik in self.ORNEKLER:
            with self.subTest(yol=yol):
                eslesme = resolve(yol)
                self.assertEqual(eslesme.url_name, tur)
                yakalanan = eslesme.kwargs.get("kimlik") or eslesme.kwargs.get("dilim_id")
                self.assertEqual(int(yakalanan), kimlik)

    def test_yazar_sayfasi_haber_sanilmiyor(self):
        """SIRA TUZAĞI. /yazarlar/{slug}-{id} iki dilimli olduğu için genel
        haber kalıbına da uyar. Genel kalıp öne alınırsa bu test kırılır."""
        eslesme = resolve("/yazarlar/namik-goz-76")
        self.assertEqual(eslesme.url_name, "yazar")
        self.assertNotEqual(eslesme.url_name, "haber")

    def test_slug_uyusmasa_da_kimlikten_cozuluyor(self):
        """Canlı site slug'ı yok sayıp kimlikten çözüyor; biz de öyle yapmalıyız."""
        eslesme = resolve("/spor/tamamen-yanlis-slug-526347")
        self.assertEqual(eslesme.url_name, "haber")
        self.assertEqual(int(eslesme.kwargs["kimlik"]), 526347)

    def test_tireli_ve_sapan_kategori_sluglari(self):
        """`bursa-da-spor` ve tek aylık sapma `bursada-spor` ikisi de çözülmeli."""
        for slug in ("bursa-da-spor", "bursada-spor"):
            with self.subTest(slug=slug):
                eslesme = resolve(f"/{slug}/bir-haber-123456")
                self.assertEqual(eslesme.url_name, "haber")

    def test_kimliksiz_iki_dilimli_adres_cozulmuyor(self):
        """Kimliksiz iki dilimli yol hiçbir kalıba uymamalı."""
        for yol in ("/spor/kimliksiz-baslik", "/yazarlar/kimliksiz/yol/derin"):
            with self.subTest(yol=yol):
                with self.assertRaises(Resolver404):
                    resolve(yol)

    def test_tek_dilimli_yollar_bolum_sayfasi(self):
        """F4'te açılan bölüm sayfaları. F2'de bu yollar çözülmüyordu;
        kategori listesi ve anasayfa geldiği için artık çözülüyorlar ve
        haber kalıbını GÖLGELEMEMELERİ gerekiyor."""
        for yol, ad in (("/", "anasayfa"), ("/spor", "kategori"),
                        ("/spor/", "kategori"), ("/ara", "arama"),
                        ("/ilceler", "ilceler"), ("/yazarlar", "yazarlar")):
            with self.subTest(yol=yol):
                self.assertEqual(resolve(yol).url_name, ad)


class KanonikYonlendirme(TestCase):
    """Kimlikten çöz, slug uyuşmuyorsa kanonik adrese 301 ver.

    Canlı sitenin ölçülmüş davranışı budur; yeni sistem aynısını yapmalı.
    """

    @classmethod
    def setUpTestData(cls):
        from django.core.management import call_command
        call_command("taksonomi_kur", verbosity=0)

    def test_galeri_yanlis_slug_kanonige_301(self):
        # bursa foto kimligi 208 (haber 8 + 200)
        yanit = self.client.get("/galeriler/tamamen-yanlis-208/bir-galeri-12431")
        self.assertEqual(yanit.status_code, 301)
        self.assertEqual(yanit["Location"], "/galeriler/bursa-208/bir-galeri-12431")

    def test_video_yanlis_slug_kanonige_301(self):
        # bursa video kimligi 308 (haber 8 + 300)
        yanit = self.client.get("/videolar/yanlis-308/bir-video-91994")
        self.assertEqual(yanit.status_code, 301)
        self.assertEqual(yanit["Location"], "/videolar/bursa-308/bir-video-91994")

    def test_galeri_dogru_slug_yonlendirmiyor(self):
        """Kanonik adres yönlendirmeden 200 dönmeli.

        F2'de galeri görünümü bir taslaktı ve kayıt olsun olmasın 200
        dönüyordu. `medya` uygulaması geldiğinden beri veritabanına
        bakıyor, o yüzden testin kendi kaydını yaratması gerekiyor —
        haber tarafında `test_on_uc_slugun_hepsi_taniniyor` ile aynı geçiş.
        """
        from medya.models import FotoGaleri
        from .models import Kategori, KategoriTur

        kategori = KategoriTur.objects.get(
            tur=Kategori.TUR_FOTO, eski_id=208).kategori
        FotoGaleri.objects.create(
            id=12431, slug="bir-galeri", baslik="Bir galeri",
            kategori=kategori, kategori_dilimi="bursa-208",
            yayin_zamani=timezone.now())
        yanit = self.client.get("/galeriler/bursa-208/bir-galeri-12431")
        self.assertEqual(yanit.status_code, 200)

    def test_sapan_kategori_slugu_kanonige_301(self):
        """2022-01'deki tek aylık `bursada-spor` sapması."""
        yanit = self.client.get("/bursada-spor/bir-haber-654321")
        self.assertEqual(yanit.status_code, 301)
        self.assertEqual(yanit["Location"], "/bursa-da-spor/bir-haber-654321")

    def test_bilinmeyen_kategori_404(self):
        yanit = self.client.get("/olmayan-kategori/bir-haber-123456")
        self.assertEqual(yanit.status_code, 404)

    def test_bilinmeyen_kategori_kimligi_404(self):
        yanit = self.client.get("/galeriler/bursa-9999/bir-galeri-1")
        self.assertEqual(yanit.status_code, 404)

    KANONIK_SLUGLAR = [
        "gundem", "spor", "bursa", "dunya", "ekonomi", "magazin",
        "bursaspor", "saglik", "teknoloji", "yasam",
        "bursa-da-spor", "aktualite", "savunma-sanayi",
    ]

    def test_on_uc_slugun_hepsi_taniniyor(self):
        """556.824 adresten ölçülen 13 kanonik slug + 1 sapma.

        F3'te içerik modeli geldiği için görünüm artık veritabanına bakıyor:
        kaydı olmayan kimlik 404 verir. Bu yüzden her kategoriye bir haber
        yazılıp adresin **200 döndüğü** ölçülüyor. F2'deki hâli, kayıt olsun
        olmasın 200 döndüğü için bu ayrımı göremiyordu.
        """
        from icerik.models import Haber
        from .models import Kategori, KategoriTur

        for sira, slug in enumerate(self.KANONIK_SLUGLAR, start=1):
            with self.subTest(slug=slug):
                tur = KategoriTur.objects.filter(
                    tur=Kategori.TUR_HABER, slug=slug).first()
                self.assertIsNotNone(tur, f"{slug} taksonomide yok")
                kimlik = 900000 + sira
                Haber.objects.create(
                    id=kimlik, slug="bir-haber", baslik="Bir haber",
                    kategori=tur.kategori, yayin_zamani=timezone.now())
                yanit = self.client.get(f"/{slug}/bir-haber-{kimlik}")
                self.assertEqual(yanit.status_code, 200)

    def test_sapma_slugu_301(self):
        self.assertEqual(self.client.get("/bursada-spor/x-1").status_code, 301)

    def test_olmayan_kimlik_404(self):
        """Tanınan kategori + olmayan kimlik = 404. Sessiz boş sayfa değil."""
        self.assertEqual(
            self.client.get("/spor/bir-haber-999999999").status_code, 404)

    def test_yanlis_slug_kanonige_301(self):
        """Kimlikten çözülür, slug uyuşmuyorsa kanonik adrese 301."""
        from icerik.models import Haber
        from .models import Kategori, KategoriTur

        tur = KategoriTur.objects.get(tur=Kategori.TUR_HABER, slug="spor")
        Haber.objects.create(id=888001, slug="dogru-slug", baslik="Doğru slug",
                             kategori=tur.kategori, yayin_zamani=timezone.now())
        yanit = self.client.get("/spor/tamamen-yanlis-888001")
        self.assertEqual(yanit.status_code, 301)
        self.assertEqual(yanit["Location"], "/spor/dogru-slug-888001")
