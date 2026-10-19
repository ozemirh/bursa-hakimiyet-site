"""Gövde temizleyicisinin saldırı tablosu (Paket K, 19 Ekim 2026).

DEGERLENDIRME-2026-10 §1: "Gövde temizleyici 16 saldırı yükünün hepsini
durdurdu." O ölçüm elle yapılmıştı; burada TABLO olarak kilitlenir. Her
satır: yük, ve çıktıda BULUNMAMASI gereken parçalar. Çıktının tamamı
sabitlenmiyor — temizleyici değişince metin biçimi değişebilir, güvenlik
değişmezi değişmemeli.

Ortak değişmezler (her yük için ayrıca denetlenir):
* `<script`, `<iframe`, `<svg`, `<img`, `<object`, `<embed`, `<style`,
  `<form`, `<base`, `<meta` etiketi çıktıda yok;
* hiçbir `on…=` olay niteliği yok;
* hiçbir `href` `javascript:` / `data:` / `vbscript:` ile başlamıyor;
* çıktıdaki her `<a` `rel="noopener nofollow"` taşıyor.
"""

import re

from django.test import SimpleTestCase

from .temizle import govde_temizle

# (ad, yük, ek yasak parçalar)
SALDIRILAR = [
    ("script", "<script>alert(1)</script>", ["alert"]),
    ("img onerror", "<img src=x onerror=alert(1)>", ["onerror"]),
    ("svg onload", "<svg onload=alert(1)>", ["onload"]),
    ("svg içinde script", "<svg><script>alert(1)</script></svg>", ["alert"]),
    ("javascript href", '<a href="javascript:alert(1)">x</a>', ["javascript"]),
    ("büyük-küçük harf", '<a href="JaVaScRiPt:alert(1)">x</a>', ["script:"]),
    ("baştaki boşluk", '<a href=" javascript:alert(1)">x</a>', ["javascript"]),
    ("sekme kaçışı", '<a href="java&#x09;script:alert(1)">x</a>', ["script:"]),
    ("ondalık varlık", '<a href="&#106;avascript:alert(1)">x</a>', ["avascript"]),
    ("dolgulu varlık", '<a href="&#0000106&#0000097vascript:alert(1)">x</a>', ["vascript"]),
    ("data: URI", '<a href="data:text/html;base64,PHNjcmlwdD4=">x</a>', ["data:"]),
    ("vbscript", '<a href="vbscript:msgbox(1)">x</a>', ["vbscript"]),
    ("iframe", '<iframe src="javascript:alert(1)"></iframe>', ["javascript"]),
    ("style niteliği", '<p style="background:url(javascript:alert(1))">x</p>',
     ["style", "javascript"]),
    ("olay niteliği", '<p onmouseover="alert(1)">x</p>', ["alert"]),
    ("mXSS math/style", "<math><mtext><table><mglyph><style><img src=x onerror=alert(1)>",
     ["onerror"]),
    ("iç içe script", "<scr<script>ipt>alert(1)</script>", ["<script", "<scr"]),
    ("nitelikten kaçış", '"><script>alert(1)</script>', ["<script"]),
    ("noscript kaçışı",
     '<noscript><p title="</noscript><img src=x onerror=alert(1)>"></noscript>',
     ["onerror"]),
    ("geçerli bağlantıda olay", '<a href="https://ornek.tr" onclick="alert(1)">x</a>',
     ["onclick"]),
    ("object/embed", '<object data="x.swf"></object><embed src=x>', ["x.swf"]),
    ("form", '<form action="https://kotu.example"><input></form>', ["kotu"]),
    ("base", '<base href="https://kotu.example"><p>a</p>', ["kotu"]),
    ("meta yenileme", "<meta http-equiv=refresh content=0;url=https://kotu.example>",
     ["kotu"]),
    ("yorum içinde script", "<!--<script>alert(1)--><p>a</p>", ["alert"]),
    ("textarea", "<textarea><script>alert(1)</script></textarea>", ["<script"]),
]

YASAK_ETIKET = re.compile(
    r"<\s*(script|iframe|svg|img|object|embed|style|form|base|meta|math|textarea)\b", re.I)
OLAY = re.compile(r"\son\w+\s*=", re.I)
TEHLIKELI_HREF = re.compile(r'href="\s*(javascript|data|vbscript):', re.I)


class SaldiriTablosu(SimpleTestCase):

    def _degismezler(self, ad, cikti):
        self.assertIsNone(YASAK_ETIKET.search(cikti), f"{ad}: {cikti!r}")
        self.assertIsNone(OLAY.search(cikti), f"{ad}: {cikti!r}")
        self.assertIsNone(TEHLIKELI_HREF.search(cikti), f"{ad}: {cikti!r}")
        for a in re.findall(r"<a\b[^>]*>", cikti):
            self.assertIn('rel="noopener nofollow"', a, f"{ad}: {cikti!r}")

    def test_tablo(self):
        self.assertGreaterEqual(len(SALDIRILAR), 16)
        for ad, yuk, yasaklar in SALDIRILAR:
            with self.subTest(ad):
                cikti = str(govde_temizle(yuk))
                self._degismezler(ad, cikti)
                for parca in yasaklar:
                    self.assertNotIn(parca.lower(), cikti.lower(), f"{ad}: {cikti!r}")

    def test_metin_kaybolmuyor(self):
        """Güvenli içerik saldırıyla birlikte gelse de korunur."""
        cikti = str(govde_temizle('<p>Önce</p><script>x()</script><p>Sonra</p>'))
        self.assertEqual(cikti, "<p>Önce</p><p>Sonra</p>")


class IkiEgikCizgi(SimpleTestCase):
    """`//kotu.example` ve `/\\kotu.example` — "/" ile başlıyor, yani
    temizleyicinin iç bağlantı dalına (`hedef.startswith("/")`) düşüyor; ama
    tarayıcı ikisini de DIŞ adrese çözer (`/\\` WHATWG URL ayrıştırıcısında
    `//` sayılır). Bugünkü davranış ölçüldü: bağlantı korunur, `rel="noopener
    nofollow"` alır — yani `https://` dış bağlantıyla aynı muamele. Bu bir
    yetki açığı değil (editör zaten dış bağlantı ekleyebiliyor), ama iç
    bağlantı gibi GÖRÜNEN bir dış bağlantı. Kilitlenen değişmez: ya düz
    metne iner ya da dış bağlantı muamelesi görür; asla nofollow'suz,
    "iç" bir bağlantı olarak basılmaz. (Biçim düzeltmesi — `https://`ye
    çevirmek ya da reddetmek — sahibinde; bu test ikisine de izin verir.)
    """

    YUKLER = ['<a href="//kotu.example/yol">x</a>',
              '<a href="/\\kotu.example/yol">x</a>',
              '<a href="/\\/kotu.example">x</a>',
              '<a href=" //kotu.example">x</a>']

    def test_dis_baglanti_muamelesi(self):
        for yuk in self.YUKLER:
            with self.subTest(yuk):
                cikti = str(govde_temizle(yuk))
                self.assertIn("x", cikti)
                baglantilar = re.findall(r"<a\b[^>]*>", cikti)
                for a in baglantilar:
                    self.assertIn('rel="noopener nofollow"', a, cikti)
                    self.assertNotIn("javascript", a)

    def test_gercek_ic_baglanti_korunur(self):
        self.assertEqual(
            str(govde_temizle('<a href="/bursa/haber-12">x</a>')),
            '<a href="/bursa/haber-12" rel="noopener nofollow">x</a>')
