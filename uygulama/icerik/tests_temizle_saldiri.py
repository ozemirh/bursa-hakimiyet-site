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
    r"""`//kotu.example` ve `/\kotu.example` — "/" ile başlıyor ama tarayıcı
    ikisini de DIŞ adrese çözer (`/\` WHATWG URL ayrıştırıcısında `//`
    sayılır; sekme ve satır sonu adresin her yerinden silinir).

    Eski davranış (Paket K'da ölçülüp kilitlenmişti): iç bağlantı dalına
    düşüp olduğu gibi basılıyordu — iç bağlantı gibi GÖRÜNEN dış bağlantı.
    Yeni davranış (Paket L2, 19 Ekim 2026): açık `https://` adresine
    çevrilir, yani dış bağlantıyla birebir aynı muameleyi görür; ana
    makinesi olmayan biçim düz metne iner. Asla "/" ile başlayan bir dış
    adres basılmaz.
    """

    CEVRILEN = [
        ('<a href="//kotu.example/yol">x</a>', "https://kotu.example/yol"),
        ('<a href="/\\kotu.example/yol">x</a>', "https://kotu.example/yol"),
        ('<a href="/\\/kotu.example">x</a>', "https://kotu.example"),
        ('<a href=" //kotu.example">x</a>', "https://kotu.example"),
        ('<a href="\\\\kotu.example">x</a>', "https://kotu.example"),
        ('<a href="/\t/kotu.example">x</a>', "https://kotu.example"),
        ('<a href="/\n/kotu.example/a?b=1#c">x</a>', "https://kotu.example/a?b=1#c"),
    ]

    def test_https_adresine_cevrilir(self):
        for yuk, beklenen in self.CEVRILEN:
            with self.subTest(yuk):
                self.assertEqual(
                    str(govde_temizle(yuk)),
                    f'<a href="{beklenen}" rel="noopener nofollow">x</a>')

    def test_ana_makinesiz_bicim_duz_metne_iner(self):
        for yuk in ('<a href="///">x</a>', '<a href="/\\/">x</a>', '<a href="//">x</a>'):
            with self.subTest(yuk):
                self.assertEqual(str(govde_temizle(yuk)), "x")

    def test_hicbir_baglanti_egik_cizgiyle_dis_adrese_gitmez(self):
        """Değişmez: "/" ya da ters bölüyle başlayan basılmış href, tarayıcının
        gözünde de iç adres olmalı (ikinci karakteri "/" ya da ters bölü değil)."""
        for yuk, _ in self.CEVRILEN:
            cikti = str(govde_temizle(yuk))
            for href in re.findall(r'href="([^"]*)"', cikti):
                if href[:1] in ("/", "\\"):
                    self.assertNotIn(href[1:2], ("/", "\\"), cikti)

    def test_tarayicinin_sildigi_karakter_semayi_gizleyemez(self):
        for yuk in ('<a href="java\tscript:alert(1)">x</a>',
                    '<a href="java\nscript:alert(1)">x</a>'):
            with self.subTest(yuk):
                self.assertEqual(str(govde_temizle(yuk)), "x")

    def test_ic_baglantidaki_ters_bolu_tarayici_bicimine_iner(self):
        """Tek eğik çizgili iç adresteki ters bölü tarayıcıda "/" olur;
        basılan biçim de odur (adres iç kalır)."""
        self.assertEqual(
            str(govde_temizle('<a href="/bursa\\haber-12">x</a>')),
            '<a href="/bursa/haber-12" rel="noopener nofollow">x</a>')

    def test_gercek_ic_baglanti_korunur(self):
        self.assertEqual(
            str(govde_temizle('<a href="/bursa/haber-12">x</a>')),
            '<a href="/bursa/haber-12" rel="noopener nofollow">x</a>')
