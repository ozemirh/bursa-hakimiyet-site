"""Haber detayı: üst şeridin yeri (K1 b), spot ölçüsü (R3), araç çubuğu
işleyicileri, "başa dön" ve medya sayfalarında paylaşım (20 Ekim 2026).

Sözleşme:
- Detayda üst şerit içerik sütununun tepesinde DEĞİL; aynı yuva tanımı
  (`parca/ust_serit.html`) ana görselin altında, seslendirmenin üstünde.
  Anasayfada şerit yerinde.
- Spot gövdeden belirgin: aynı serif aile, 500 ağırlık, 20 px (> gövde 18).
- Kopyala · A− · A+ · yazdır `site.js`te bağlı; betik yokken düğmeler
  çizilmez (`html.js-var`, `taban.html` başındaki satır içi betik).
- Köşe yazısı, galeri ve video araç çubuğunda `parca/paylas.html`.

Yerleşimin kendisi (H1 y, taşma) başsız Chrome ile ölçülür —
`tests_sayfa_butcesi`; buradaki testler sunucu çıktısını ve kaynakları sınar.
"""

import re
from datetime import timedelta
from pathlib import Path

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from medya.models import FotoGaleri, KoseYazisi, Video, Yazar
from taksonomi.models import Kategori, KategoriTur

from .models import Haber

KOK = Path(__file__).resolve().parent.parent
CSS = (KOK / "statik" / "stil" / "site.css").read_text(encoding="utf-8")
JS = (KOK / "statik" / "betik" / "site.js").read_text(encoding="utf-8")
SERIT = 'class="reklam tam"'


YORUMSUZ = re.sub(r"/\*.*?\*/", "", CSS, flags=re.S)


def _kural(secici):
    """Seçicinin @media DIŞINDAKİ son kuralının gövdesi (en son yazılan kazanır)."""
    bulunan, derinlik, onceki = None, 0, 0
    for i, c in enumerate(YORUMSUZ):
        if c == "{":
            if derinlik == 0 and YORUMSUZ[onceki:i].strip() == secici:
                bulunan = YORUMSUZ[i + 1:YORUMSUZ.index("}", i)]
            derinlik += 1
            onceki = i + 1
        elif c == "}":
            derinlik -= 1
            onceki = i + 1
    return bulunan


def _zaman():
    return timezone.now() - timedelta(hours=1)


class DetayUstSerit(TestCase):

    @classmethod
    def setUpTestData(cls):
        call_command("taksonomi_kur", verbosity=0)
        kategori = KategoriTur.objects.get(tur=Kategori.TUR_HABER, slug="gundem").kategori
        cls.haber = Haber.objects.create(
            id=5_950_101, slug="serit-olcusu", baslik="Şerit ölçüsü", kategori=kategori,
            spot="Spot cümlesi", govde="<p>Bir.</p><p>İki.</p>", durum=Haber.DURUM_AKTIF,
            kaynak_turu=Haber.KAYNAK_MUHABIR, muhabir="", yayin_zamani=_zaman())

    def setUp(self):
        yanit = self.client.get(self.haber.get_absolute_url())
        self.assertEqual(yanit.status_code, 200)
        self.metin = yanit.content.decode()

    def test_detayda_serit_icerigin_ustunde_degil(self):
        self.assertEqual(self.metin.count(SERIT), 1)
        self.assertGreater(self.metin.index(SERIT), self.metin.index("<main"),
                           "üst şerit hâlâ içerik sütununun tepesinde")

    def test_serit_ana_gorselin_altinda_seslendirmenin_ustunde(self):
        makale = self.metin[self.metin.index('<article class="detay">'):]
        serit = makale.index(SERIT)
        self.assertLess(makale.index("<h1>"), serit)
        self.assertLess(makale.index('class="spot"'), serit)
        self.assertLess(makale.index('class="detay-kunye"'), serit)
        self.assertLess(makale.index("ana-gorsel"), serit)
        self.assertLess(serit, makale.index('id="seslendirme"'))
        self.assertLess(serit, makale.index('class="metin"'))

    def test_yuva_tanimi_tabandakiyle_ayni(self):
        """Ad, ölçüler, harita, demo işareti: anasayfadaki şeritle birebir."""
        def yuva(metin):
            bas = metin.index(SERIT)
            return metin[bas:metin.index("</span></span>", bas)]
        ana = self.client.get("/").content.decode()
        self.assertEqual(yuva(self.metin), yuva(ana))
        self.assertIn('data-gpt="1100x150,970x250,728x90"', yuva(self.metin))
        self.assertIn('data-gpt-demo="kapali"', yuva(self.metin))

    def test_anasayfada_serit_yerinde(self):
        ana = self.client.get("/").content.decode()
        self.assertEqual(ana.count(SERIT), 1)
        self.assertLess(ana.index(SERIT), ana.index("<main"))

    def test_kutu_boyu_ve_tasma_kurali(self):
        """Kutu boyu `.reklam.tam` sınıfından (250 · 120 · 44); detay kopyası
        yalnız kenar boşluğunu değiştirir, boyu değil."""
        self.assertIn("height:250px", _kural(".reklam.tam"))
        detay = _kural(".detay>.reklam.tam")
        self.assertIsNotNone(detay)
        self.assertNotIn("height", detay)


class SpotOlcusu(TestCase):

    def test_spot_govdeden_belirgin(self):
        spot = _kural(".detay .spot")
        self.assertIn("font-family:var(--serif)", spot)   # §35: aile aynı
        self.assertIn("font-weight:500", spot)
        boy = float(re.search(r"font-size:([\d.]+)px", spot).group(1))
        govde = float(re.search(r"\.metin\{font-size:([\d.]+)px", CSS).group(1))
        self.assertGreater(boy / govde, 1.05, (boy, govde))
        self.assertNotRegex(spot, r"#[0-9a-fA-F]{3,6}\b")

    def test_h1_38(self):
        self.assertIn("font-size:38px", _kural(".detay h1"))


class AracCubuguBetigi(TestCase):

    def test_isleyiciler_var(self):
        for secici in (".kopyala", ".yazi-kucult", ".yazi-buyut", ".yazdir"):
            self.assertIn(f"querySelector('{secici}')", JS, secici)
        self.assertIn("navigator.clipboard", JS)
        self.assertIn("execCommand('copy')", JS)          # geri dönüş
        self.assertIn("Bağlantı kopyalandı", JS)
        self.assertIn("'aria-live', 'polite'", JS)
        self.assertIn("window.print()", JS)
        self.assertIn(".disabled = sira", JS)
        # localStorage gizli sekmede atar: her yazma try içinde.
        for m in re.finditer(r"localStorage\.(setItem|removeItem)\('bh-yazi-boyu'", JS):
            onu = JS[max(0, m.start() - 160):m.start()]
            self.assertIn("try{", onu)

    def test_kademeler_css_ile_ayni(self):
        kademeler = re.search(r"YAZI_BOYLARI = \[([^\]]*)\]", JS).group(1)
        for ad in re.findall(r"'([a-z-]+)'", kademeler):
            self.assertIn(f'html[data-yazi-boyu="{ad}"] .metin', CSS, ad)
        self.assertIn("'bh-yazi-boyu'", JS)

    def test_betiksiz_gizli(self):
        taban = (KOK / "sablonlar" / "taban.html").read_text(encoding="utf-8")
        self.assertIn("className+=' js-var'", taban)
        self.assertIn("localStorage.getItem('bh-yazi-boyu')", taban)
        self.assertEqual(_kural("html:not(.js-var) .arac button"), "display:none")
        self.assertEqual(_kural("html:not(.js-var) .yukari"), "display:none")


class BasaDon(TestCase):

    @classmethod
    def setUpTestData(cls):
        call_command("taksonomi_kur", verbosity=0)
        kategori = KategoriTur.objects.get(tur=Kategori.TUR_HABER, slug="gundem").kategori
        cls.haber = Haber.objects.create(
            id=5_950_102, slug="basa-don", baslik="Başa dön", kategori=kategori,
            spot="Spot", govde="<p>Bir.</p>", durum=Haber.DURUM_AKTIF,
            kaynak_turu=Haber.KAYNAK_MUHABIR, muhabir="", yayin_zamani=_zaman())

    def test_detayda_basili_anasayfada_yok(self):
        metin = self.client.get(self.haber.get_absolute_url()).content.decode()
        self.assertEqual(metin.count('class="yukari"'), 1)
        self.assertIn('<button type="button" class="yukari"', metin)
        self.assertNotIn('class="yukari"', self.client.get("/").content.decode())

    def test_hareket_azaltmaya_uyuyor(self):
        self.assertIn("azalt.matches ? 'auto' : 'smooth'", JS[JS.index("yukarı çık"):])
        self.assertIn("@media(prefers-reduced-motion:reduce){.yukari{transition:none}}", CSS)


class MedyaPaylasim(TestCase):
    """Köşe yazısı, galeri, video: araç çubuğunda üç paylaşım bağlantısı."""

    @classmethod
    def setUpTestData(cls):
        call_command("taksonomi_kur", verbosity=0)
        yazar = Yazar.objects.create(id=990176, slug="deneme-yazar", ad="Deneme YAZAR",
                                     sayfasi_tarandi=True)
        cls.yazi = KoseYazisi.objects.create(
            id=932099, slug="paylasim-yazisi", baslik="Paylaşım yazısı",
            govde="<p>Gövde</p>", yazar=yazar, yayin_zamani=_zaman())
        foto = KategoriTur.objects.get(tur=Kategori.TUR_FOTO, eski_id=208)
        cls.galeri = FotoGaleri.objects.create(
            id=912431, slug="paylasim-galerisi", baslik="Paylaşım galerisi",
            kategori=foto.kategori, kategori_dilimi="bursa-208", yayin_zamani=_zaman())
        vid = KategoriTur.objects.get(tur=Kategori.TUR_VIDEO, eski_id=308)
        cls.video = Video.objects.create(
            id=991994, slug="paylasim-videosu", baslik="Paylaşım videosu",
            kategori=vid.kategori, kategori_dilimi="bursa-308", yayin_zamani=_zaman())

    def test_uc_sayfada_paylas_parcasi(self):
        for nesne in (self.yazi, self.galeri, self.video):
            with self.subTest(adres=nesne.get_absolute_url()):
                yanit = self.client.get(nesne.get_absolute_url())
                self.assertEqual(yanit.status_code, 200)
                metin = yanit.content.decode()
                arac = metin.index('<div class="arac">')
                grup = metin[arac:metin.index("</div>", metin.index('class="paylas"', arac))]
                self.assertEqual(grup.count('class="paylas-bag"'), 3)
                self.assertIn('role="group"', grup)
                self.assertIn('class="kopyala"', grup)
                self.assertIn("Payla%C5%9F%C4%B1m", grup)       # başlık kodlu
