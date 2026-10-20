"""Küçük metin renkleri AA'yı geçen değişkenden (20 Ekim 2026).

Biçim dosyası okunur, kuralın `color` değişkeni `:root`taki değerine
çözülür, metnin gerçekten oturduğu zeminlere karşı WCAG oranı hesaplanır.
Zeminler başsız Chrome'da ölçüldü (elle, `getComputedStyle` ata zinciri).

1. Panel ipucu `.sag-not`: `--gri-acik` beyazda 2,98, `--zemin`de 2,75
   idi. Artık `--gri` (5,85 · 5,40 · girdi zemininde 4,86).
2. Site, nöbetçi eczane ızgarasında ilçe adı `.eczane-izgara .yer`
   (11 px): `--kirmizi` `--yumusak` gözde 4,32 idi → `--kirmizi-koyu` 6,22.
"""

import re
from pathlib import Path

from django.test import SimpleTestCase

STIL = Path(__file__).resolve().parent.parent / "statik" / "stil"
AA = 4.5


def degiskenler(metin):
    kok = re.search(r":root\s*\{(.*?)\n\}", metin, re.S).group(1)
    return {ad: deger for ad, deger in re.findall(r"--([a-z0-9-]+):\s*(#[0-9A-Fa-f]{6})", kok)}


def kural_renkleri(metin, secici):
    """Seçicinin geçtiği her kuraldaki `color:var(--x)` adları."""
    adlar = []
    metin = re.sub(r"/\*.*?\*/", "", metin, flags=re.S)
    for seciciler, govde in re.findall(r"([^{}]+)\{([^{}]*)\}", metin):
        if any(s.strip() == secici for s in seciciler.split(",")):
            adlar += re.findall(r"(?:^|[;\s])color:\s*var\(--([a-z0-9-]+)\)", govde)
    return adlar


def oran(a, b):
    def isik(h):
        r, g, b_ = (int(h[i:i + 2], 16) / 255 for i in (1, 3, 5))
        f = lambda c: c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4  # noqa: E731
        return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b_)
    x, y = sorted((isik(a), isik(b)), reverse=True)
    return (x + 0.05) / (y + 0.05)


class Kontrast(SimpleTestCase):

    def test_olcer_bilinen_degerleri_veriyor(self):
        self.assertAlmostEqual(oran("#000000", "#FFFFFF"), 21.0, places=2)
        self.assertAlmostEqual(oran("#8B97A3", "#F4F6F8"), 2.75, places=2)

    def test_panel_ipucu_aa(self):
        metin = (STIL / "panel.css").read_text("utf-8")
        renk = degiskenler(metin)
        for secici in (".sag-not", ".kutu-kart>h2 .sag-not"):
            adlar = kural_renkleri(metin, secici)
            self.assertTrue(adlar, f"{secici} kuralı/rengi bulunamadı")
            for ad in adlar:
                for zemin in ("yuzey", "zemin", "girdi-zemin", "uyari-zemin", "bilgi-zemin"):
                    with self.subTest(secici=secici, renk=ad, zemin=zemin):
                        self.assertGreaterEqual(oran(renk[ad], renk[zemin]), AA)
        # Eski yerel yama gereksiz: genel kural zaten AA.
        self.assertEqual(kural_renkleri(metin, ".duzeltme-bolumu .sag-not"), [])

    def test_eczane_ilce_adi_aa(self):
        metin = (STIL / "site.css").read_text("utf-8")
        renk = degiskenler(metin)
        adlar = kural_renkleri(metin, ".eczane-izgara .yer")
        self.assertTrue(adlar)
        # Göz zemini (`.eczane-izgara li`) ölçülüyor, yazılı varsayılmıyor.
        zemin = re.search(r"\.eczane-izgara li\{[^}]*background:var\(--([a-z-]+)\)", metin).group(1)
        for ad in adlar:
            with self.subTest(renk=ad, zemin=zemin):
                self.assertGreaterEqual(oran(renk[ad], renk[zemin]), AA)
