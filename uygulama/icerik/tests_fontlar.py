"""Arayüz işaretleri sembol yazı tipi dilimini tetiklemesin (20 Ekim 2026).

Her sayfa `roboto-math.woff2` (41 KB) ve `roboto-symbols.woff2` (21 KB)
indiriyordu; tetikleyen yalnız arayüz işaretleriydi (menü ☰, "Tümü →",
döviz ▲▼, seslendirme ▶ ◀ ■ ❚, açılır ▾). Başsız Chrome'da
`CSS.getPlatformFontsForNode` ölçümü: bu glifler dosyalar inse de Roboto'dan
değil Segoe UI Symbol / Arial / Arial Narrow'dan çiziliyordu — indirme
boştu. Çare `fontlar.css`'te: Oklar, Geometrik Şekiller ve Çeşitli Semboller
blokları (ve ❚) iki dilimin `unicode-range`'inden çıkarıldı.

Tarayıcısız denetim: `fontlar.css` okunur, indirilen (`url()`) her yüzün
aralığı çözülür. Tarayıcıdaki karşılığı `tests_sayfa_butcesi.test_5`.
"""

import html
import re
from pathlib import Path

from django.test import SimpleTestCase

KOK = Path(__file__).resolve().parent.parent
FONTLAR = KOK / "statik" / "stil" / "fontlar.css"

#: Sayfada her ziyarette ya da tek tıkla görünen arayüz işaretleri.
ARAYUZ_ISARETLERI = {
    0x2630: "☰ menü düğmesi",
    0x2192: "→ Tümü / Veri kaynakları",
    0x25B2: "▲ döviz yükseliş",
    0x25BC: "▼ döviz düşüş",
    0x25B6: "▶ video / seslendirme",
    0x25C0: "◀ seslendirme geri",
    0x25A0: "■ seslendirme dur",
    0x25BE: "▾ açılır menü",
    0x275A: "❚ seslendirme duraklat",
}

#: Sembol dilimlerinden bütünüyle çıkarılan Unicode blokları.
CIKARILAN_BLOKLAR = {
    "Oklar": (0x2190, 0x21FF),
    "Geometrik Şekiller": (0x25A0, 0x25FF),
    "Çeşitli Semboller": (0x2600, 0x26FF),
}


def yuzler(metin):
    """`(dosya adı, [(baş, son), ...])` — yalnız indirilen (`url()`) yüzler."""
    sonuc = []
    for blok in re.findall(r"@font-face\s*\{([^}]*)\}", metin):
        dosya = re.search(r'url\("[^"]*/([^"/]+)"\)', blok)
        aralik = re.search(r"unicode-range:([^;]*);", blok)
        if not dosya or not aralik:
            continue
        parcalar = []
        for p in aralik.group(1).split(","):
            bas, _, son = p.strip().upper().removeprefix("U+").partition("-")
            parcalar.append((int(bas, 16), int(son or bas, 16)))
        sonuc.append((dosya.group(1), parcalar))
    return sonuc


class SembolDilimi(SimpleTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.yuzler = yuzler(FONTLAR.read_text("utf-8"))

    def test_cozumleyici_dilimleri_buluyor(self):
        adlar = {ad for ad, _ in self.yuzler}
        self.assertIn("roboto-math.woff2", adlar)
        self.assertIn("roboto-symbols.woff2", adlar)
        self.assertIn("roboto-latin.woff2", adlar)
        # Kontrol: çözümleyici gerçekten aralık görüyor (latin dilimi ç'yi kapsar).
        latin = dict(self.yuzler)["roboto-latin.woff2"]
        self.assertTrue(any(a <= ord("ç") <= b for a, b in latin))

    def test_arayuz_isaretleri_hicbir_web_fontunu_indirtmiyor(self):
        for kod, ne in ARAYUZ_ISARETLERI.items():
            for ad, araliklar in self.yuzler:
                with self.subTest(isaret=ne, dosya=ad):
                    self.assertFalse(any(a <= kod <= b for a, b in araliklar),
                                     f"U+{kod:04X} ({ne}) {ad} aralığında: her sayfada iner")

    def test_sembol_dilimleri_ui_bloklarina_dokunmuyor(self):
        for ad, araliklar in self.yuzler:
            if not ad.startswith(("roboto-math", "roboto-symbols")):
                continue
            for blok, (bb, bs) in CIKARILAN_BLOKLAR.items():
                with self.subTest(dosya=ad, blok=blok):
                    kesisen = [f"U+{a:04X}-{b:04X}" for a, b in araliklar if a <= bs and b >= bb]
                    self.assertEqual(kesisen, [])

    def test_liste_gercek_isaretleri_tutuyor(self):
        """Denetlenen işaretler gerçekten şablon/betik/stilde geçiyor —
        liste kendiliğinden eskimesin."""
        kaynaklar = [p for p in KOK.rglob("*.html") if "sablonlar" in p.parts]
        kaynaklar += list((KOK / "statik" / "betik").glob("*.js"))
        kaynaklar.append(KOK / "statik" / "stil" / "site.css")
        gecen = set()
        for p in kaynaklar:
            metin = p.read_text("utf-8")
            gecen.update(ord(c) for c in html.unescape(metin) if ord(c) > 0x2000)
            gecen.update(int(h, 16) for h in re.findall(r"\\([0-9A-Fa-f]{4,6})", metin))
        eksik = [ne for kod, ne in ARAYUZ_ISARETLERI.items() if kod not in gecen]
        self.assertEqual(eksik, [])
