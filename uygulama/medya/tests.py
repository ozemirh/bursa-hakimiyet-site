"""Medya tarafı gerileme testleri.

Üç şey korunuyor:

1. **Adres sözleşmesi.** Dört ailenin deseni ölçülmüş ve dondurulmuştur;
   kimlik adresin parçası. Kalıp sırası bozulursa yazar sayfaları haber
   sanılır ve sessizce kaybolur — `taksonomi/tests.py`deki tuzağın aynısı,
   bu kez gerçek görünümlerle.
2. **Kanonik davranış.** Çözüm kimlikle yapılır, slug yok sayılır, kanonik
   adrese 301 verilir. Kayıt yoksa 404 — sessiz boş sayfa değil.
3. **Göçün tekrar çalıştırılabilirliği.** Arşiv taraması sürerken komut
   defalarca koşacak; ikinci koşu kopya üretmemeli.

Uygulama kök adres tablosuna bağlandı; testler gerçek `cekirdek.urls`
üzerinden koşuyor. Böylece kalıp SIRASI da sınanmış oluyor — medya
kalıpları taksonomi'nin genel haber kalıbından önce gelmezse yazar ve
galeri sayfaları sessizce kaybolur.
"""

import json
import tempfile
from datetime import datetime, timezone as std_zaman
from io import StringIO
from pathlib import Path

from django.core.management import call_command
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import Resolver404, resolve
from django.utils import timezone

from taksonomi.models import Kategori, KategoriTur

from .ayikla import adresten_slug_kimlik, dilim_ayir, sure_saniyeye, zaman
from .models import FotoGaleri, KoseYazisi, Video, Yazar

TEST_ADRESLER = "cekirdek.urls"


def _zaman(gun=1):
    return timezone.make_aware(datetime(2026, 8, gun, 10, 0, 0))


# ---------------------------------------------------------------- adresler

@override_settings(ROOT_URLCONF=TEST_ADRESLER)
class AdresKaliplari(SimpleTestCase):
    """Ölçülmüş gerçek adresler. Değerler canlı siteden alındı."""

    ORNEKLER = [
        ("/yazarlar/namik-goz-76/gokyuzune-bakarken-hafizamizi-da-koruyalim-32099",
         "kose", 32099),
        ("/yazarlar/namik-goz-76", "yazar", 76),
        ("/galeriler/bursa-208/bursa-da-kizil-sirtli-orumcekkusu-12431", "galeri", 12431),
        ("/videolar/bursa-308/bursa-da-firar-eden-50-koyun-91994", "video", 91994),
    ]

    def test_dort_aile_dogru_cozuluyor(self):
        for yol, ad, kimlik in self.ORNEKLER:
            with self.subTest(yol=yol):
                eslesme = resolve(yol)
                self.assertEqual(eslesme.url_name, ad)
                yakalanan = eslesme.kwargs.get("kimlik") or eslesme.kwargs.get("dilim_id")
                self.assertEqual(int(yakalanan), kimlik)

    def test_yazar_sayfasi_haber_sanilmiyor(self):
        """SIRA TUZAĞI. Genel haber kalıbı öne alınırsa bu test kırılır."""
        self.assertEqual(resolve("/yazarlar/namik-goz-76").url_name, "yazar")

    def test_kose_yazisi_yazar_sayfasi_sanilmiyor(self):
        """İkinci tuzak: köşe kalıbı yazar kalıbından ÖNCE gelmeli."""
        eslesme = resolve("/yazarlar/namik-goz-76/bir-yazi-1")
        self.assertEqual(eslesme.url_name, "kose")

    def test_gorunumler_medya_uygulamasindan_geliyor(self):
        """Kalıplar taksonominin taslak görünümlerine değil buraya bağlanmalı."""
        for yol, _, _ in self.ORNEKLER:
            with self.subTest(yol=yol):
                self.assertEqual(resolve(yol).func.__module__, "medya.views")

    def test_bolum_listeleri_cozuluyor(self):
        for yol, ad in (("/yazarlar", "yazarlar"), ("/galeriler", "galeriler"),
                        ("/videolar", "videolar")):
            with self.subTest(yol=yol):
                self.assertEqual(resolve(yol).url_name, ad)

    def test_kimliksiz_adres_cozulmuyor(self):
        for yol in ("/galeriler/bursa-208/kimliksiz-baslik",
                    "/yazarlar/namik-goz/bir/derin/yol"):
            with self.subTest(yol=yol):
                with self.assertRaises(Resolver404):
                    resolve(yol)


# ------------------------------------------------------------- ayıklayıcı

class AyiklamaKurallari(SimpleTestCase):
    """Göç, adresi kaynaktan okur; başlıktan slug üretmez."""

    def test_dilim_ayirma(self):
        self.assertEqual(dilim_ayir("namik-goz-76"), ("namik-goz", 76))
        self.assertEqual(dilim_ayir("bursa-208"), ("bursa", 208))
        self.assertEqual(dilim_ayir("bursada-spor-250"), ("bursada-spor", 250))

    def test_dilim_kimliksizse_kayit_dusmez(self):
        """Kimlik çözülemese de ham dilim korunur; adres yaşamaya devam eder."""
        self.assertEqual(dilim_ayir("kimliksiz"), ("kimliksiz", None))

    def test_adresten_slug_ve_kimlik(self):
        self.assertEqual(
            adresten_slug_kimlik("https://x/galeriler/dunya-204/bir-galeri-5396"),
            ("bir-galeri", 5396))
        self.assertEqual(
            adresten_slug_kimlik("https://x/yazarlar/erdal-abi-26"),
            ("erdal-abi", 26))

    def test_slug_kimligi_kendi_icine_katmiyor(self):
        """Açgözlü kalıp `bir-galeri-5396`yı bütün olarak slug sayardı."""
        slug, kimlik = adresten_slug_kimlik("https://x/a/2026-yilinda-bursa-12345")
        self.assertEqual(slug, "2026-yilinda-bursa")
        self.assertEqual(kimlik, 12345)

    def test_sure_cozumu(self):
        # `0:1:2` gerilemesi: arşivdeki 9.306 video süresini sıfır dolgusuz
        # yazıyor. İki basamak şart koşulunca hepsi süresiz kalıyordu.
        for ham, saniye in (("PT2M30S", 150), ("PT45S", 45),
                            ("P0DT1H2M3S", 3723), ("01:02:03", 3723),
                            ("2:30", 150), ("0:1:2", 62), ("0:0:9", 9),
                            ("1:2:3", 3723),
                            # Oynatıcının ondalıklı ham değeri — 7.783 kayıt.
                            ("00:22.0586", 22), ("01:8.92799", 68),
                            ("0:0:38.698", 38)):
            with self.subTest(ham=ham):
                self.assertEqual(sure_saniyeye(ham), saniye)

    def test_cozulemeyen_sure_sifir(self):
        """Sıfır 'bilinmiyor' demektir; şablon o zaman süre basmaz."""
        for ham in ("", "bilinmiyor", None):
            self.assertEqual(sure_saniyeye(ham), 0)

    def test_zaman_cozumu(self):
        cozum = zaman("2021-02-01T10:18:46")
        self.assertIsNotNone(cozum)
        self.assertEqual(cozum.astimezone(std_zaman.utc).year, 2021)

    def test_turkce_tarih_bicimi(self):
        """ÖLÇÜM: köşe ailesinin 1.500 örneğinin TAMAMI `gg.aa.yyyy SS:DD`
        biçiminde. Yalnız ISO kabul edilseydi 6.903 köşe yazısı yayın zamansız
        kalır, `yayindakiler()` hiçbirini listelemez ve sayfaları 404 olurdu."""
        cozum = zaman("01.03.2021 08:04")
        self.assertIsNotNone(cozum)
        self.assertEqual((cozum.year, cozum.month, cozum.day), (2021, 3, 1))
        self.assertEqual((cozum.hour, cozum.minute), (8, 4))

    def test_saniyesiz_iso_da_cozuluyor(self):
        self.assertIsNotNone(zaman("2021-02-01T10:18"))

    def test_cozulemeyen_zaman_none(self):
        """Sessizce 'şimdi' yazmak arşivin kronolojisini bozardı."""
        for ham in ("", "dün", "2021"):
            self.assertIsNone(zaman(ham))


# ---------------------------------------------------------------- modeller

class ModelDavranisi(TestCase):

    @classmethod
    def setUpTestData(cls):
        call_command("taksonomi_kur", verbosity=0)
        cls.yazar = Yazar.objects.create(
            id=76, slug="namik-goz", ad="Namık GÖZ", sayfasi_tarandi=True)
        cls.bursa = KategoriTur.objects.get(tur=Kategori.TUR_FOTO, eski_id=208).kategori

    def test_yazar_adresi(self):
        self.assertEqual(self.yazar.get_absolute_url(), "/yazarlar/namik-goz-76")

    def test_kose_adresi_yazarin_diliminden_kurulur(self):
        yazi = KoseYazisi.objects.create(
            id=32099, slug="bir-yazi", baslik="Bir yazı",
            yazar=self.yazar, yayin_zamani=_zaman())
        self.assertEqual(yazi.get_absolute_url(),
                         "/yazarlar/namik-goz-76/bir-yazi-32099")

    def test_galeri_adresi_kanonik_dilimi_kullanir(self):
        """Ölçülmüş sapma: foto ailesinde `bursada-spor-250` geçiyor, kanoniği
        `bursa-da-spor-250`. Kimlikten çözülüp kanoniğe çekilmeli."""
        sapan = KategoriTur.objects.get(tur=Kategori.TUR_FOTO, eski_id=250)
        galeri = FotoGaleri.objects.create(
            id=1, slug="bir-galeri", baslik="Bir galeri",
            kategori=sapan.kategori, kategori_dilimi="bursada-spor-250",
            yayin_zamani=_zaman())
        self.assertEqual(galeri.get_absolute_url(),
                         "/galeriler/bursa-da-spor-250/bir-galeri-1")

    def test_taksonomide_olmayan_dilim_kaydi_dusurmez(self):
        """ÖLÇÜM (27 Ağustos 2026): taranan 3.660 galerinin 998'i `haber-213`
        dilimindeydi ve taksonomide 213 diye bir foto kimliği yok. Kategorisiz
        kayıt da adresini korumalı."""
        galeri = FotoGaleri.objects.create(
            id=2, slug="bir-galeri", baslik="Bir galeri",
            kategori=None, kategori_dilimi="haber-213", yayin_zamani=_zaman())
        self.assertEqual(galeri.get_absolute_url(),
                         "/galeriler/haber-213/bir-galeri-2")

    def test_video_adresi(self):
        kategori = KategoriTur.objects.get(tur=Kategori.TUR_VIDEO, eski_id=308).kategori
        video = Video.objects.create(
            id=91994, slug="bir-video", baslik="Bir video", kategori=kategori,
            kategori_dilimi="bursa-308", yayin_zamani=_zaman())
        self.assertEqual(video.get_absolute_url(),
                         "/videolar/bursa-308/bir-video-91994")

    def test_sure_yazisi(self):
        video = Video(sure_saniye=150)
        self.assertEqual(video.sure_yazi, "2:30")
        self.assertEqual(Video(sure_saniye=3723).sure_yazi, "1:02:03")

    def test_suresi_bilinmeyen_video_deger_uydurmaz(self):
        """ÖLÇÜM: 312 video kaydının hiçbirinde `sure` alanı dolu değil."""
        self.assertEqual(Video(sure_saniye=0).sure_yazi, "")

    def test_oynatma_adresi_gomulu_adresi_tercih_ediyor(self):
        """ÖLÇÜM: JSON-LD `contentUrl` 312 kaydın hepsinde sayfanın KENDİ
        adresi; gerçek oynatıcı `embedUrl`de. Kendi adresine dönen bağlantı
        basılmamalı."""
        kategori = KategoriTur.objects.get(tur=Kategori.TUR_VIDEO,
                                           eski_id=308).kategori
        video = Video(id=16522, slug="bir-video", baslik="Bir video",
                      kategori=kategori, kategori_dilimi="bursa-308",
                      video_url="https://x/videolar/bursa-308/bir-video-16522",
                      gomulu_url="https://y.web.tv/embed/abc")
        self.assertEqual(video.oynatma_adresi, "https://y.web.tv/embed/abc")

    def test_kendi_adresine_donen_baglanti_basilmaz(self):
        kategori = KategoriTur.objects.get(tur=Kategori.TUR_VIDEO,
                                           eski_id=308).kategori
        video = Video(id=16522, slug="bir-video", baslik="Bir video",
                      kategori=kategori, kategori_dilimi="bursa-308",
                      video_url="https://x/videolar/bursa-308/bir-video-16522",
                      gomulu_url="")
        self.assertEqual(video.oynatma_adresi, "")

    def test_gorsel_yolu_yerel_onek_kullanir(self):
        """Medya aileleri arşiv kökünün altında KARDEŞ klasörlere yazıyor;
        `/arsiv-gorsel/` oraya bakmıyor, bu yüzden ayrı önek var."""
        galeri = FotoGaleri(gorsel_var=True,
                            gorsel_dosya="gorseller-galeri/2021-02/x.webp")
        self.assertEqual(galeri.gorsel_yolu(),
                         "/arsiv-medya/gorseller-galeri/2021-02/x.webp")

    def test_yerel_dosyasi_olmayan_kayit_uzaga_baglanmaz(self):
        galeri = FotoGaleri(gorsel_var=False, gorsel_url="https://uzak/x.webp",
                            gorsel_dosya="")
        self.assertEqual(galeri.gorsel_yolu(), "")

    def test_basharfler_turkce(self):
        """`"ismail".upper()` Python'da "ISMAIL" verir; doğrusu "İSMAİL"."""
        self.assertEqual(Yazar(ad="İsmail KARADUMAN").basharfler, "İK")
        self.assertEqual(Yazar(ad="Namık GÖZ").basharfler, "NG")

    def test_yayin_zamani_olmayan_kayit_listelenmez(self):
        FotoGaleri.objects.create(id=3, slug="zamansiz", baslik="Zamansız",
                                  kategori_dilimi="bursa-208", yayin_zamani=None)
        self.assertFalse(FotoGaleri.yayindakiler().filter(pk=3).exists())


# --------------------------------------------------------------- görünümler

@override_settings(ROOT_URLCONF=TEST_ADRESLER)
class GorunumDavranisi(TestCase):
    """Çözüm kimlikle; slug uyuşmuyorsa kanoniğe 301, kayıt yoksa 404."""

    @classmethod
    def setUpTestData(cls):
        call_command("taksonomi_kur", verbosity=0)
        cls.yazar = Yazar.objects.create(
            id=76, slug="namik-goz", ad="Namık GÖZ", sayfasi_tarandi=True)
        cls.yazi = KoseYazisi.objects.create(
            id=32099, slug="dogru-slug", baslik="Doğru slug",
            govde="<p>Gövde</p>", yazar=cls.yazar, yayin_zamani=_zaman())
        foto = KategoriTur.objects.get(tur=Kategori.TUR_FOTO, eski_id=208)
        cls.galeri = FotoGaleri.objects.create(
            id=12431, slug="dogru-slug", baslik="Doğru slug",
            kategori=foto.kategori, kategori_dilimi="bursa-208",
            yayin_zamani=_zaman())
        vid = KategoriTur.objects.get(tur=Kategori.TUR_VIDEO, eski_id=308)
        cls.video = Video.objects.create(
            id=91994, slug="dogru-slug", baslik="Doğru slug",
            kategori=vid.kategori, kategori_dilimi="bursa-308",
            yayin_zamani=_zaman())

    # -- kanonik 200 --
    def test_kanonik_adresler_200(self):
        for yol in ("/yazarlar/namik-goz-76",
                    "/yazarlar/namik-goz-76/dogru-slug-32099",
                    "/galeriler/bursa-208/dogru-slug-12431",
                    "/videolar/bursa-308/dogru-slug-91994",
                    "/yazarlar", "/galeriler", "/videolar"):
            with self.subTest(yol=yol):
                self.assertEqual(self.client.get(yol).status_code, 200)

    # -- yanlış slug 301 --
    def test_yanlis_slug_kanonige_301(self):
        ornekler = [
            ("/yazarlar/yanlis-76", "/yazarlar/namik-goz-76"),
            ("/yazarlar/namik-goz-76/tamamen-yanlis-32099",
             "/yazarlar/namik-goz-76/dogru-slug-32099"),
            ("/galeriler/yanlis-208/tamamen-yanlis-12431",
             "/galeriler/bursa-208/dogru-slug-12431"),
            ("/videolar/yanlis-308/tamamen-yanlis-91994",
             "/videolar/bursa-308/dogru-slug-91994"),
        ]
        for yol, hedef in ornekler:
            with self.subTest(yol=yol):
                yanit = self.client.get(yol)
                self.assertEqual(yanit.status_code, 301)
                self.assertEqual(yanit["Location"], hedef)

    def test_yanlis_yazar_dilimi_dogru_yazara_301(self):
        """Köşe yazısının kanonik adresi yazarın diliminden kurulur; yazının
        kimliği doğruysa yanlış yazar dilimi de kanoniğe çekilir."""
        yanit = self.client.get("/yazarlar/baska-yazar-999/dogru-slug-32099")
        self.assertEqual(yanit.status_code, 301)
        self.assertEqual(yanit["Location"],
                         "/yazarlar/namik-goz-76/dogru-slug-32099")

    # -- kayıt yok --
    def test_olmayan_kimlik_404(self):
        for yol in ("/yazarlar/namik-goz-999999",
                    "/yazarlar/namik-goz-76/bir-yazi-999999",
                    "/galeriler/bursa-208/bir-galeri-999999",
                    "/videolar/bursa-308/bir-video-999999"):
            with self.subTest(yol=yol):
                self.assertEqual(self.client.get(yol).status_code, 404)

    def test_bilinmeyen_kategori_kimligi_404(self):
        """F2'de ölçülen davranış korunuyor: tanınmayan kategori kimliği
        geçerli bir adres değil."""
        for yol in ("/galeriler/bursa-9999/bir-galeri-1",
                    "/videolar/bursa-9999/bir-video-1"):
            with self.subTest(yol=yol):
                self.assertEqual(self.client.get(yol).status_code, 404)

    def test_kaydi_yokken_yanlis_slug_yine_kanonige_301(self):
        """Tarama sürerken gelen adres henüz kayıtsız olabilir; kanonik biçime
        çekmek yine de doğru — kayıt geldiğinde okur doğru adreste olur."""
        yanit = self.client.get("/galeriler/tamamen-yanlis-208/bir-galeri-777")
        self.assertEqual(yanit.status_code, 301)
        self.assertEqual(yanit["Location"], "/galeriler/bursa-208/bir-galeri-777")

    # -- yayında olmayan kayıt --
    def test_pasif_kayit_404(self):
        FotoGaleri.objects.filter(pk=12431).update(durum=FotoGaleri.DURUM_PASIF)
        self.assertEqual(
            self.client.get("/galeriler/bursa-208/dogru-slug-12431").status_code, 404)

    def test_pasif_yazarin_sayfasi_acik_kalir(self):
        """`aktif` yalnız listeleri süzer; eski bağlantı 404 olmamalı."""
        Yazar.objects.filter(pk=76).update(aktif=False)
        self.assertEqual(self.client.get("/yazarlar/namik-goz-76").status_code, 200)
        self.assertNotContains(self.client.get("/yazarlar"), "namik-goz-76")

    # -- içerik gerçekten veritabanından geliyor mu --
    def test_sayfalar_veritabanindan_render_ediliyor(self):
        for yol, beklenen in (
                ("/yazarlar/namik-goz-76", "Namık GÖZ"),
                ("/yazarlar/namik-goz-76/dogru-slug-32099", "Doğru slug"),
                ("/galeriler/bursa-208/dogru-slug-12431", "Doğru slug"),
                ("/videolar/bursa-308/dogru-slug-91994", "Doğru slug")):
            with self.subTest(yol=yol):
                self.assertContains(self.client.get(yol), beklenen)

    def test_galeri_kareleri_eksikse_okura_soyleniyor(self):
        yanit = self.client.get("/galeriler/bursa-208/dogru-slug-12431")
        self.assertContains(yanit, "kaynaktan alınamadı")

    def test_gorselsiz_kayit_uzak_adrese_baglanmiyor(self):
        """Sayfa internetsiz de açılmalı: yerel dosyası olmayan kayıt kategori
        temsilî çizimine düşer, `gorsel_url`e değil."""
        FotoGaleri.objects.filter(pk=12431).update(
            gorsel_var=False, gorsel_url="https://uzak.example/x.webp")
        yanit = self.client.get("/galeriler/bursa-208/dogru-slug-12431")
        self.assertNotContains(yanit, "uzak.example")
        self.assertContains(yanit, "temsilî")


# ------------------------------------------------------------------- göç

class GocKomutu(TestCase):
    """Tarama sürerken komut defalarca koşacak; ikinci koşu kopya üretmemeli."""

    @classmethod
    def setUpTestData(cls):
        call_command("taksonomi_kur", verbosity=0)

    def setUp(self):
        self.gecici = tempfile.TemporaryDirectory()
        self.kok = Path(self.gecici.name)
        self.addCleanup(self.gecici.cleanup)

    def _yaz(self, aile, ay, kimlik, veri):
        klasor = self.kok / f"veri-{aile}" / ay
        klasor.mkdir(parents=True, exist_ok=True)
        (klasor / f"{kimlik}.json").write_text(
            json.dumps(veri, ensure_ascii=False), encoding="utf-8")

    def _kos(self, **ek):
        cikti = StringIO()
        call_command("medya_goc_al", kok=str(self.kok), stdout=cikti,
                     verbosity=0, **ek)
        return cikti.getvalue()

    def _ornek_arsiv(self):
        self._yaz("yazar", "2021-01", 26, {
            "tur": "yazar",
            "url": "https://x/yazarlar/erdal-abi-26",
            "ad": "Erdal ABİ",
            "yazar_dilimi": "erdal-abi-26",
            "yayin_tarihi": "2021-01-01T00:00:00",
            "gorsel_url": "https://x/cdn/erdal.webp",
            "yerel_gorseller": ["gorseller-yazar/2021-01/erdal.webp"],
        })
        self._yaz("kose", "2021-03", 32099, {
            "tur": "kose",
            "url": "https://x/yazarlar/namik-goz-76/bir-yazi-32099",
            "yazar_dilimi": "namik-goz-76",
            "yazar": "Namık GÖZ",
            "baslik": "Bir yazı",
            "spot": "Spot",
            "govde_html": "<p>Gövde</p>",
            "kategori_etiketi": "GÜNDEM",
            # Ölçülen biçim: köşe ailesinde tarih Türkçe yazılıyor.
            "yayin_tarihi": "05.03.2021 08:30",
            "kelime_sayisi": 400,
            "yerel_gorseller": [],
        })
        self._yaz("galeri", "2021-02", 5396, {
            "tur": "galeri",
            "url": "https://x/galeriler/dunya-204/bir-galeri-5396",
            "baslik": "Bir galeri",
            "kategori_dilimi": "dunya-204",
            "yayin_tarihi": "2021-02-01T10:18:46",
            "kareler_eksik": True,
            "kareler_notu": "Kareler statik HTML'de yok.",
            "gorsel_url": "https://x/cdn/kapak.webp",
            "yerel_gorseller": ["gorseller-galeri/2021-02/kapak.webp"],
        })
        # Taksonomide karşılığı olmayan dilim — ölçüldü, düşürülmemeli.
        self._yaz("galeri", "2021-02", 9770, {
            "tur": "galeri",
            "url": "https://x/galeriler/haber-213/bir-galeri-9770",
            "baslik": "Kategorisiz galeri",
            "kategori_dilimi": "haber-213",
            "yayin_tarihi": "2021-02-02T10:00:00",
            "yerel_gorseller": [],
        })
        self._yaz("video", "2021-04", 91994, {
            "tur": "video",
            "url": "https://x/videolar/bursa-308/bir-video-91994",
            "baslik": "Bir video",
            "kategori_dilimi": "bursa-308",
            "yayin_tarihi": "2021-04-01T12:00:00",
            "video_url": "https://x/video.mp4",
            "gomulu_url": "https://x/gomulu",
            "sure": "PT2M30S",
            "yerel_gorseller": [],
        })

    def test_bos_klasor_cokertmiyor(self):
        """Aileler ayrı ayrı taranıyor; başlamamış aile hata değil."""
        self._kos()
        self.assertEqual(Yazar.objects.count(), 0)

    def test_dort_aile_iceri_aliniyor(self):
        self._ornek_arsiv()
        self._kos()
        self.assertEqual(KoseYazisi.objects.count(), 1)
        self.assertEqual(FotoGaleri.objects.count(), 2)
        self.assertEqual(Video.objects.count(), 1)
        # 26 arşivden, 76 köşe yazısından türetildi.
        self.assertEqual(Yazar.objects.count(), 2)

    def test_kimlik_korunuyor(self):
        """Kimlik adresin parçası; değişirse eski bağlantılar kırılır."""
        self._ornek_arsiv()
        self._kos()
        self.assertTrue(FotoGaleri.objects.filter(pk=5396).exists())
        self.assertTrue(Video.objects.filter(pk=91994).exists())
        self.assertTrue(KoseYazisi.objects.filter(pk=32099).exists())
        self.assertTrue(Yazar.objects.filter(pk=26).exists())

    def test_slug_adresten_geliyor_basliktan_degil(self):
        self._ornek_arsiv()
        self._kos()
        self.assertEqual(FotoGaleri.objects.get(pk=5396).slug, "bir-galeri")

    def test_taranmamis_yazar_icin_gecici_kayit(self):
        self._ornek_arsiv()
        self._kos()
        yazar = Yazar.objects.get(pk=76)
        self.assertFalse(yazar.sayfasi_tarandi)
        self.assertEqual(yazar.slug, "namik-goz")
        self.assertEqual(yazar.ad, "Namık GÖZ")
        self.assertTrue(Yazar.objects.get(pk=26).sayfasi_tarandi)

    def test_gecici_yazar_sonradan_taraninca_ezilmiyor(self):
        """Yazar ailesi köşeden sonra gelirse künye tamamlanmalı; tersi
        durumda köşe koşusu taranmış künyeyi ezmemeli."""
        self._ornek_arsiv()
        self._kos()
        self._yaz("yazar", "2021-01", 76, {
            "tur": "yazar", "url": "https://x/yazarlar/namik-goz-76",
            "ad": "Namık GÖZ", "yazar_dilimi": "namik-goz-76",
            "yayin_tarihi": "2021-01-01T00:00:00",
            "yerel_gorseller": ["gorseller-yazar/2021-01/namik.webp"],
        })
        self._kos()
        yazar = Yazar.objects.get(pk=76)
        self.assertTrue(yazar.sayfasi_tarandi)
        self.assertTrue(yazar.gorsel_var)
        # Köşe koşusu ikinci kez döndü ama taranmış kaydı bozmadı.
        self._kos(aile="kose")
        self.assertTrue(Yazar.objects.get(pk=76).sayfasi_tarandi)

    def test_taksonomide_olmayan_dilim_kaydi_dusurmuyor(self):
        self._ornek_arsiv()
        self._kos()
        galeri = FotoGaleri.objects.get(pk=9770)
        self.assertIsNone(galeri.kategori)
        self.assertEqual(galeri.kategori_dilimi, "haber-213")
        self.assertEqual(galeri.get_absolute_url(),
                         "/galeriler/haber-213/bir-galeri-9770")

    def test_tekrar_calistirilabilir(self):
        self._ornek_arsiv()
        self._kos()
        self._kos()
        self.assertEqual(FotoGaleri.objects.count(), 2)
        self.assertEqual(Video.objects.count(), 1)
        self.assertEqual(KoseYazisi.objects.count(), 1)
        self.assertEqual(Yazar.objects.count(), 2)

    def test_guncellenen_kaynak_uzerine_yaziliyor(self):
        self._ornek_arsiv()
        self._kos()
        self._yaz("galeri", "2021-02", 5396, {
            "tur": "galeri",
            "url": "https://x/galeriler/dunya-204/bir-galeri-5396",
            "baslik": "Düzeltilmiş başlık",
            "kategori_dilimi": "dunya-204",
            "yayin_tarihi": "2021-02-01T10:18:46",
            "yerel_gorseller": [],
        })
        self._kos()
        self.assertEqual(FotoGaleri.objects.get(pk=5396).baslik,
                         "Düzeltilmiş başlık")
        self.assertEqual(FotoGaleri.objects.count(), 2)

    def test_kuru_calisma_yazmiyor(self):
        self._ornek_arsiv()
        self._kos(kuru=True)
        self.assertEqual(FotoGaleri.objects.count(), 0)
        self.assertEqual(Yazar.objects.count(), 0)

    def test_video_suresi_cozuluyor(self):
        self._ornek_arsiv()
        self._kos()
        video = Video.objects.get(pk=91994)
        self.assertEqual(video.sure_saniye, 150)
        self.assertEqual(video.sure, "PT2M30S")

    def test_kose_kategorisi_articlesection_alanindan(self):
        self._ornek_arsiv()
        self._kos()
        self.assertEqual(KoseYazisi.objects.get(pk=32099).kategori.ad, "GÜNDEM")

    def test_kose_yayin_zamani_turkce_tarihten_cozuluyor(self):
        """Bu test kırılırsa 6.903 köşe yazısı yayından düşer."""
        self._ornek_arsiv()
        self._kos()
        yazi = KoseYazisi.objects.get(pk=32099)
        self.assertIsNotNone(yazi.yayin_zamani)
        self.assertTrue(KoseYazisi.yayindakiler().filter(pk=32099).exists())

    def test_gecici_yazarin_portresi_yazidan_geliyor(self):
        """Köşe sayfasının og:image'ı yazının değil YAZARIN fotoğrafı; sayfası
        taranamamış yazarların vesikası ancak buradan doluyor."""
        self._yaz("kose", "2021-05", 40000, {
            "tur": "kose",
            "url": "https://x/yazarlar/murat-kuter-28/bir-yazi-40000",
            "yazar_dilimi": "murat-kuter-28",
            "yazar": "Murat KUTER",
            "baslik": "Bir yazı",
            "govde_html": "<p>Gövde</p>",
            "yayin_tarihi": "01.05.2021 07:30",
            "gorsel_url": "https://x/cdn/murat.jpg",
            "gorsel_alt": "Murat KUTER",
            "yerel_gorseller": ["gorseller-kose/2021-05/murat.jpg"],
        })
        self._kos()
        yazar = Yazar.objects.get(pk=28)
        self.assertFalse(yazar.sayfasi_tarandi)
        self.assertTrue(yazar.gorsel_var)
        self.assertEqual(yazar.gorsel_yolu(),
                         "/arsiv-medya/gorseller-kose/2021-05/murat.jpg")

    def test_yerel_gorsel_isaretleniyor(self):
        self._ornek_arsiv()
        self._kos()
        galeri = FotoGaleri.objects.get(pk=5396)
        self.assertTrue(galeri.gorsel_var)
        self.assertEqual(galeri.gorsel_dosya,
                         "gorseller-galeri/2021-02/kapak.webp")
        self.assertFalse(FotoGaleri.objects.get(pk=9770).gorsel_var)
