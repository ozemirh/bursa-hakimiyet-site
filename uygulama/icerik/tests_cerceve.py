"""Fotoğraf çerçevesi kırpmaz + bölüm/ilçe H1'i biçimli — 20 Ekim 2026.

Tasarım direktörünün önerisi R1 ve R2 (`referans-kutuphanesi/tasarim/
bursa-hakimiyet-oneri.md`), kullanıcının 19 Ekim kararı: "görsel
kırpılmasın" (arama sonuçları için verildi; bölüm/ilçe listelerinde §45/§64
ile zaten uygulanıyordu).

Ölçüm (başsız Chrome, `object-fit:cover` ile görünmeyen alan yüzdesi):

    yüzey                         önce 390 / 768 / 1440     sonra
    anasayfa dörtlüsü (132 px)    %44 / %45 / %24           ~%0
    anasayfa son haberler (185)   %15 / %19 / %23           ~%0
    anasayfa Bursaspor (140)      %34 / %38 / %4  (ort.)    ~%0 (3:2 kaynak)
    detay ilgili haberler (150)   %31 / %35 / %37           ~%0
    detay ana görsel (210/300/420) %3 / %34 / %11           ~%0
    galeri/video kartı (150)      %13 / %17 / %10           ~%0
    bölüm 390'da galeri/video     %46                       ~%0

Korunan şeyler:

1. **Oran tek kaynaktan.** `:root`ta `--cerceve-orani:3/2` (arşivin oranı,
   §64) ve `--kapak-orani:40/21` (galeri/video kapağı 1200x630).
2. **Kart fotoğrafı sabit px yükseklik almaz.** Sabit yükseklik + `cover`
   farkı kırparak kapatır. Demo döneminin üç ölü seçicisi (tur B'de
   silindi) geri gelmesin diye ayrıca sınanıyor (`OluSecici`).
3. **Dar ekranda yatay kart.** Dörtlü, ilgili haberler ve Bursaspor şeridi
   ≤600'de fotoğrafı solda 112 px 3:2 tutar; `align-items:start` olmadan
   fotoğraf metnin boyuna gerilir ve yeniden kırpılır.
4. **Bölüm/ilçe H1'i** temanın başlık ailesinde, 32/900 (≤600'de 26) ve
   seçicinin bağlandığı şablon yapısı yerinde.
"""

import re
from pathlib import Path

from django.core.management import call_command
from django.test import SimpleTestCase, TestCase
from django.utils import timezone

from taksonomi.models import Ilce, Kategori, KategoriTur

from .models import Haber
from .templatetags import gorsel_etiket as ge

KOK = Path(__file__).resolve().parent.parent
STIL = (KOK / "statik" / "stil" / "site.css").read_text(encoding="utf-8")
KURAL = re.sub(r"/\*.*?\*/", "", STIL, flags=re.S)
BLOK = re.compile(r"([^{}]+)\{([^{}]*)\}")
SABIT_BOY = re.compile(r"(?<![-\w])(min-)?height:\s*[1-9][0-9.]*px")

#: İzinli liste BOŞ (20 Ekim 2026, tur B): sabit boylu üç ölü seçici
#: (`.manset .foto`, `.yatay .foto`, `.serit-oge .foto` — demo dönemi,
#: hiçbir şablon/betik basmıyordu) aileleriyle birlikte silindi. Geri
#: gelmemeleri `OluSecici` ile sınanır.
IZINLI = {}
OLU_SINIFLAR = ("manset", "yatay", "serit-oge")


def _kurallar():
    """(seçici, bildirimler) — iç içe olmayan her kural bloğu."""
    for m in BLOK.finditer(KURAL):
        yield m.group(1).strip(), m.group(2)


def _blok(secici: str) -> str:
    for sec, bildirim in _kurallar():
        if secici in [s.strip() for s in sec.split(",")]:
            return bildirim
    raise AssertionError(f"kural yok: {secici}")


class CerceveOrani(SimpleTestCase):

    def test_oranlar_kokte_tanimli(self):
        kok = re.search(r":root\s*\{([^}]*)\}", KURAL).group(1)
        self.assertIn("--cerceve-orani:3/2;", kok)
        self.assertIn("--kapak-orani:40/21;", kok)

    def test_kart_ve_ana_gorsel_oranla_cizilir(self):
        for secici, oran in ((".kart .foto", "--cerceve-orani"),
                             (".ana-gorsel", "--cerceve-orani"),
                             (".ana-gorsel.kapak", "--kapak-orani"),
                             (".galeri-kart .foto", "--kapak-orani"),
                             (".video-kart .foto", "--kapak-orani")):
            self.assertIn(f"aspect-ratio:var({oran})", _blok(secici), secici)

    def test_kart_fotografi_sabit_yukseklik_almaz(self):
        """`.foto` ve `.ana-gorsel` çerçevelerinde px yükseklik yok."""
        bulgu = []
        for sec, bildirim in _kurallar():
            for s in (x.strip() for x in sec.split(",")):
                if not re.search(r"(\.foto|\.ana-gorsel)$", s) or s in IZINLI:
                    continue
                if SABIT_BOY.search(bildirim):
                    bulgu.append(f"{s} {{{bildirim.strip()}}}")
        self.assertEqual(bulgu, [], "sabit boy + cover fotoğrafı kırpar")

    def test_izinli_liste_bos(self):
        self.assertEqual(IZINLI, {})

    def test_genis_kart_fotografi_esnemez(self):
        """Esneyen hücrede `aspect-ratio` yok sayılır (§45): satır düzeninde
        fotoğraf başa yaslanır, sütun düzeninde boy oranından gelir."""
        bloklar = [b for s, b in _kurallar()
                   if ".kart.genis .foto" in [x.strip() for x in s.split(",")]]
        self.assertEqual(len(bloklar), 2)
        self.assertIn("align-self:start", bloklar[0])
        self.assertIn("min-height:0", bloklar[0])
        self.assertIn("height:auto", bloklar[1])

    def test_dar_ekranda_yatay_kart(self):
        m = re.search(r"@media\(max-width:600px\)\{\s*([^{}]+)\{([^{}]*)\}", KURAL[
            KURAL.index(".dortlu .kart,.ilgili-izgara .kart") - 40:])
        self.assertIsNotNone(m)
        secici, bildirim = m.group(1), m.group(2)
        for s in (".dortlu .kart", ".ilgili-izgara .kart", ".bursaspor-haber .kart"):
            self.assertIn(s, secici)
        self.assertIn("grid-template-columns:112px minmax(0,1fr)", bildirim)
        self.assertIn("align-items:start", bildirim)

    def test_yatay_kartin_sizes_degeri_112px(self):
        """Yerleşim değişti, `sizes` da: dar ekranda 112 px'lik kutuya tam
        genişlik görsel indirilmesin."""
        for yuva in ("dortlu", "kart-yatay"):
            self.assertTrue(ge.YUVALAR[yuva][0].startswith("(max-width: 600px) 112px"),
                            yuva)

    def test_galeri_kareleri_kesilmez(self):
        """Galeri sayfasının kareleri kapak değil, oranı bilinmiyor: çerçeve
        3:2, görsel `contain`."""
        self.assertIn("aspect-ratio:var(--cerceve-orani)", _blok("figure.galeri-kart .foto"))
        self.assertIn("object-fit:contain", _blok("figure.galeri-kart .foto img"))

    def test_sablon_kancalari(self):
        detay = (KOK / "sablonlar" / "haber_detay.html").read_text(encoding="utf-8")
        self.assertIn('class="kutu-izgara ilgili-izgara"', detay)
        self.assertIn('gorsel_yuva="kart-yatay"', detay)
        ana = (KOK / "sablonlar" / "anasayfa.html").read_text(encoding="utf-8")
        self.assertRegex(ana, r'bursaspor_haberleri %\}[^\n]*gorsel_yuva="kart-yatay"')
        for ad in ("galeri.html", "video.html"):
            metin = (KOK / "medya" / "sablonlar" / "medya" / ad).read_text(encoding="utf-8")
            self.assertNotRegex(metin, r'class="foto ana-gorsel(?! kapak)', ad)


class OluSecici(SimpleTestCase):
    """20 Ekim 2026 (tur B): demo döneminin `.manset`, `.yatay`,
    `.serit-oge` aileleri silindi. Kural da, kullanan şablon da yok."""

    def test_css_de_kural_yok(self):
        for sinif in OLU_SINIFLAR:
            desen = re.compile(r"(?:^|[\s,>+~}])\.%s(?![-\w])" % re.escape(sinif))
            for sec, _ in _kurallar():
                for s in sec.split(","):
                    self.assertIsNone(desen.search(" " + s.strip()), f"{sinif}: {s.strip()}")

    def test_sablon_ve_betikte_yok(self):
        sablonlar = "".join(p.read_text(encoding="utf-8") for p in KOK.rglob("*.html"))
        betikler = "".join(p.read_text(encoding="utf-8")
                           for p in (KOK / "statik").rglob("*.js"))
        for sinif in OLU_SINIFLAR:
            desen = re.compile(r'class="(?:[^"]*\s)?%s(?:\s[^"]*)?"' % re.escape(sinif))
            self.assertIsNone(desen.search(sablonlar), sinif)
            self.assertNotRegex(betikler, r"""['".]%s['"\s.]""" % re.escape(sinif))


class KirpilmayanCerceve(SimpleTestCase):
    """Kullanıcı kararı "görsel kırpılmasın" — 16:9 gelen fotoğraf 3:2
    çerçevede `contain` (bölüm ilk kademesi, anasayfa Bursaspor şeridi) ve
    manşet penceresi ray alta inince oranla çizilir."""

    def test_ilk_kademe_ve_bursaspor_contain(self):
        for kap in (".liste-izgara", ".bursaspor-haber"):
            self.assertIn("object-fit:contain", _blok(f"{kap} .kart .foto img"), kap)
            self.assertIn("background:var(--tema-zemin)", _blok(f"{kap} .kart .foto:has(img)"), kap)

    def test_manset_penceresi_rayi_alta_inince_oranli(self):
        govde = medya_blogu(KURAL, "max-width:1000px", ".manset-slayt .slayt-pencere")
        self.assertIn(".manset-slayt .slayt-pencere{height:auto;aspect-ratio:var(--cerceve-orani)}",
                      govde)
        # Ray yanındayken (≥1001) 485 px hizası sürer; dar ekranlarda sabit
        # boylu genel pencere kuralı kalmadı.
        self.assertRegex(KURAL, r"\n\.slayt-pencere\{[^}]*height:485px")
        for sorgu in ("max-width:768px", "max-width:600px"):
            for govde in medya_govdeleri(KURAL, sorgu):
                self.assertNotRegex(govde, r"(?:^|[\n{};,])[ \t]*\.slayt-pencere\{height", sorgu)


def medya_govdeleri(metin: str, sorgu: str):
    """`@media(<sorgu>)` bloklarının gövdeleri (iç içe parantez sayılarak)."""
    for m in re.finditer(r"@media\(%s\)[^{]*\{" % re.escape(sorgu), metin):
        derinlik, i = 1, m.end()
        while derinlik:
            derinlik += {"{": 1, "}": -1}.get(metin[i], 0)
            i += 1
        yield metin[m.end():i - 1]


def medya_blogu(metin: str, sorgu: str, icerik: str) -> str:
    for govde in medya_govdeleri(metin, sorgu):
        if icerik in govde:
            return govde
    raise AssertionError(f"@media({sorgu}) içinde {icerik} yok")


class BolumBasligi(SimpleTestCase):
    """20 Ekim 2026: seçici sayfa başlığı taşıyan her vurgu çubuğunu
    kapsar (404, arama, nöbetçi eczane, veri kaynakları, dizinler…)."""

    def test_h1_bicimi(self):
        b = _blok(".kutu>.kutu-bas.vurgu h1")
        self.assertIn("font-family:var(--tema-baslik-aile)", b)
        self.assertIn("font-weight:900", b)
        self.assertIn("font-size:32px", b)
        self.assertRegex(KURAL, r"@media\(max-width:600px\)\{\.kutu>\.kutu-bas\.vurgu h1\{font-size:26px\}\}")

    def test_bicimsiz_h1_kalmadi(self):
        """Vurgu çubuğunda h1 taşıyan her şablon `.kutu` içinde — seçicinin
        kancası. Liste elle değil, şablonların kendisinden."""
        desen = re.compile(r'<(?:section|header|div) class="kutu[ "][^>]*>\s*<div class="kutu-bas vurgu">\s*<h1')
        bulunan = {p.name for p in KOK.rglob("*.html")
                   if "panel" not in p.parts and desen.search(p.read_text(encoding="utf-8"))}
        for ad in ("404.html", "arama.html", "bekleyen.html", "nobetci_eczane.html",
                   "veri_kaynaklari.html", "galeri_listesi.html", "video_listesi.html",
                   "yazar_listesi.html", "kategori.html", "piyasa.html"):
            self.assertIn(ad, bulunan)


class BolumBasligiSablonda(TestCase):
    """Seçici şablonun yapısına bağlı: sayfa başı kutusunun (`.bolum-bas`,
    20 Ekim 2026 K3) DOĞRUDAN çocuğu olan vurgu çubuğundaki h1. Şablon
    değişirse kural sessizce ölür."""

    @classmethod
    def setUpTestData(cls):
        call_command("taksonomi_kur", verbosity=0)
        cls.ilce = Ilce.objects.first()
        kategori = KategoriTur.objects.filter(
            tur=Kategori.TUR_HABER, slug="gundem").first().kategori
        Haber.objects.create(id=951000, slug="cerceve-1", baslik="Çerçeve haberi",
                             spot="Spot", govde="<p>Gövde</p>", kategori=kategori,
                             ilce=cls.ilce, yayin_zamani=timezone.now())

    def test_bolum_ve_ilce_h1_kancasi(self):
        desen = r'<header class="kutu bolum-bas">\s*<div class="kutu-bas vurgu">\s*<h1>'
        for yol in ("/gundem", f"/ilce/{self.ilce.slug}"):
            self.assertRegex(self.client.get(yol).content.decode(), desen, yol)
