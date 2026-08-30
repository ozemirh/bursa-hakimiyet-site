# -*- coding: utf-8 -*-
"""Tam menü (sidebar) — yapı ve sözleşme testleri.

28 Ağustos 2026: tam genişlikte beş sütunlu levha, sağdan kayan dikey
panele çevrildi ve bölümler `<details>` ile katlanır oldu. Bu dosya
değişmemesi gerekenleri kilitler.
"""

import re
from pathlib import Path

from django.test import TestCase, override_settings

KOK = Path(__file__).resolve().parent.parent


def menu_blogu(govde):
    """Sayfadaki `.tam-menu` bölümü."""
    i = govde.index('<div class="tam-menu"')
    return govde[i:govde.index("</nav>", i)]


class MenuYapisi(TestCase):

    @classmethod
    def setUpTestData(cls):
        from django.core.management import call_command
        call_command("taksonomi_kur", verbosity=0)

    def setUp(self):
        from icerik import baglam
        baglam._menu_bellek = None
        self.govde = self.client.get("/").content.decode()
        self.menu = menu_blogu(self.govde)

    def tearDown(self):
        from icerik import baglam
        baglam._menu_bellek = None

    def test_bolumler_details_ile_katlaniyor(self):
        self.assertEqual(len(re.findall(r"<details", self.menu)), 5)
        self.assertEqual(len(re.findall(r"<summary", self.menu)), 5)

    def test_yalniz_kategoriler_acik(self):
        """En çok kullanılan bölüm açık, kalan dördü katlı."""
        acik = re.findall(r"<details[^>]*\sopen[^>]*>\s*<summary><h2>([^<]+)", self.menu)
        self.assertEqual(acik, ["KATEGORİLER"])

    def test_basliklar_summary_icinde_h2(self):
        """Belge başlık düzeni bozulmasın: `summary` başlık öğesi taşıyabilir."""
        self.assertEqual(len(re.findall(r"<summary><h2>", self.menu)), 5)

    def test_17_ilce_DOM_da_katlanmis_olsa_bile(self):
        """URUN-PLANI.md §14: menüde 18 bağlantı (17 ilçe + tüm ilçeler).

        Katlanmış olmak gizlenmiş olmak değildir; `hidden` ya da sonradan
        yükleme yok — arama motoru ve ekran okuyucu bağlantıları görmeli.
        """
        self.assertEqual(len(re.findall(r'href="/ilce/', self.menu)), 17)
        self.assertEqual(len(re.findall(r'href="/ilceler"', self.menu)), 1)

    def test_ilce_bolumu_hidden_kullanmiyor(self):
        ilce = self.menu[self.menu.index("menu-ilce"):]
        ilce = ilce[:ilce.index("</details>")]
        self.assertNotIn("hidden", ilce)
        self.assertNotIn("display:none", ilce)

    def test_menudeki_baglanti_sayisi_korundu(self):
        """Sidebar'a geçerken hiçbir bağlantı düşmedi (ölçüm: 50)."""
        self.assertEqual(len(re.findall(r"<a href=", self.menu)), 50)

    def bant_blogu(self):
        return re.search(r'<div class="kategori-liste"[^>]*>(.*?)</div>',
                         self.govde, re.S).group(1)

    def test_kategori_bandi_10_kalem_dokunulmadi(self):
        """URUN-PLANI.md §1 madde 3 · F1 ölçütü 2 — bant sözleşmesi.

        Sayım `<a` üzerinden: 29 Ağustos 2026'da dört kaleme dar ekran için
        `class` eklendi ve `<a href=` kalıbı onları kaçırıyordu. Sayılan şey
        kalem sayısı, niteliklerin sırası değil.
        """
        self.assertEqual(len(re.findall(r"<a[\s]", self.bant_blogu())), 10)

    def test_dar_ekran_dortlusu_isaretli(self):
        """Dar ekranda banda kalan dört kalem (29 Ağustos 2026 kararı).

        Onu da DOM'da duruyor — gizleme CSS'te. Sayfadan düşürülselerdi
        arama motoru ve ekran okuyucu bağlantıları göremezdi.
        """
        mobil = re.findall(r'<a class="mobil[^"]*"[^>]*>([^<]+)</a>',
                           self.bant_blogu())
        self.assertEqual(mobil, ["BURSA", "BURSASPOR", "GÜNDEM", "SPOR"])

    def test_dortlunun_sonuncusu_isaretli(self):
        """Ayraç çizgisi son görünen kalemde kalkar.

        CSS `:last-of-type` burada YANLIŞ kalemi seçerdi: DOM'un son
        bağlantısı "Resmî İlan" ve o dar ekranda gizli.
        """
        son = re.findall(r'<a class="mobil mobil-son"[^>]*>([^<]+)</a>',
                         self.bant_blogu())
        self.assertEqual(son, ["SPOR"])

    def test_logo_bandin_icinde_ve_listenin_disinda(self):
        """Logo kendi 93 px'lik şeridinde değil, yapışkan bandın içinde.

        `.kategori-liste`nin DIŞINDA durmalı: bant sözleşmesi o listedeki
        kalemleri sayıyor, logo kategori değil.
        """
        self.assertNotIn('<header class="bant">', self.govde)
        bant_ici = self.govde[self.govde.index('<div class="kategori-ic">'):]
        self.assertIn('class="bant-logo"',
                      bant_ici[:bant_ici.index('class="kategori-liste"')])
        self.assertNotIn("bant-logo", self.bant_blogu())

    def test_tek_h1_kaldi(self):
        """Logo taşınırken anasayfanın gizli h1'i düşmemeli."""
        self.assertEqual(len(re.findall(r"<h1[\s>]", self.govde)), 1)

    def test_menu_dugmesi_aria_kurulu(self):
        self.assertIn('aria-expanded="false"', self.govde)
        self.assertIn('aria-controls="tam-menu"', self.govde)


class MenuStiliVeBetigi(TestCase):
    """Erişilebilirlik kararları CSS ve JS tarafında da kilitli."""

    CSS = (KOK / "statik" / "stil" / "site.css").read_text(encoding="utf-8")
    JS = (KOK / "statik" / "betik" / "site.js").read_text(encoding="utf-8")

    def test_summary_odak_halkasi_var(self):
        """Listede olmasa tarayıcının soluk halkasına düşerdi."""
        kural = re.search(r"([^\n}]*summary:focus-visible[^{]*)\{([^}]*)\}", self.CSS)
        self.assertIsNotNone(kural, "summary:focus-visible kuralı yok")
        self.assertIn("outline", kural.group(2))
        self.assertIn("var(--kirmizi)", kural.group(2))

    def test_mega_levha_banda_asili(self):
        """30 Ağustos 2026 (§35): sağdan kayan sidebar, banda asılı beyaz
        mega levhaya dönüştü. `position:absolute` + `top:100%` levhayı
        yapışkan bandın altına kilitler; perde hâlâ ayrı bir öğe değil,
        ikinci gölge (dışarı tıklayınca kapanma davranışı bu yüzden
        çalışmaya devam ediyor)."""
        kural = re.search(r"\.tam-menu\{([^}]*)\}", self.CSS).group(1)
        self.assertIn("position:absolute", kural)
        self.assertIn("top:100%", kural)
        self.assertIn("var(--perde)", kural)

    def test_masaustunde_bes_sutunlu_levha(self):
        """Levha ≥1001 px'te beş sütuna açılır; bölümleri JS açar, şablonda
        `open` YAZILMAZ (DOM sözleşmeleri oynamasın)."""
        blok = re.search(r"@media\(min-width:1001px\)\{\s*\.tam-menu-ic\{([^}]*)\}",
                         self.CSS)
        self.assertIsNotNone(blok, "masaüstü levha kuralı yok")
        self.assertIn("display:grid", blok.group(1))
        self.assertEqual(len(blok.group(1).split("grid-template-columns:")[1]
                             .split("}")[0].split()), 5)
        betik = (KOK / "statik" / "betik" / "site.js").read_text(encoding="utf-8")
        self.assertIn("min-width:1001px", betik)
        self.assertIn("b.open = true", betik)

    def test_hareket_azaltma_korunuyor(self):
        blok = re.findall(r"@media\(prefers-reduced-motion:reduce\)\{([^}]*\}?[^}]*)\}",
                          self.CSS)
        self.assertTrue(any("tam-menu" in b and "animation:none" in b for b in blok),
                        "sidebar animasyonu reduced-motion altında durmuyor")

    def test_renk_literali_yok(self):
        govde = re.sub(r":root\s*\{[^}]*\}", "", self.CSS, flags=re.S)
        govde = re.sub(r"--[a-z0-9-]+\s*:[^;}]*", "", govde)
        suclu = [p for p in re.findall(
            r"(?:^|[;{\s])(?:color|background|border[a-z-]*|box-shadow|outline)\s*:[^;}]*",
            govde, re.I) if re.search(r"#[0-9a-fA-F]{3,8}\b|rgba?\(", p)]
        self.assertEqual(suclu, [], f"renk literali: {suclu[:3]}")

    def test_odak_tuzagi_kapali_detayi_disliyor(self):
        """Kapalı `<details>` içi odak ALAMAZ ama Chrome kutu veriyor.

        Süzgeç olmadan tuzağın "son öğe"si asla odaklanamayan bir bağlantı
        oluyor ve odak menüden kaçıyordu (ölçüldü: 70 Tab'ın 53'ü).
        """
        self.assertIn("details:not([open])", self.JS)
        self.assertIn("SUMMARY", self.JS)

    def test_odak_tuzagi_summary_topluyor(self):
        self.assertIn("'summary, a[href]'", self.JS)

    def test_esc_ve_odak_donusu_duruyor(self):
        self.assertIn("Escape", self.JS)
        self.assertIn("menuDugme.focus()", self.JS)


class ReklamAnahtari(TestCase):
    """Reklam panolarını gizleyen düğme — SUNUM ARACI, okur özelliği değil.

    29 Ağustos 2026 kararı: yayın ekibine sayfayı reklamsız gösterebilmek
    için var. Sıradan ziyaretçiye çizilmez, çünkü reklam gizleme düğmesi
    gelir modeline dokunur.
    """

    CSS = (KOK / "statik" / "stil" / "site.css").read_text(encoding="utf-8")

    @classmethod
    def setUpTestData(cls):
        from django.core.management import call_command
        call_command("taksonomi_kur", verbosity=0)

    def setUp(self):
        from icerik import baglam
        baglam._menu_bellek = None

    def tearDown(self):
        from icerik import baglam
        baglam._menu_bellek = None

    # ALLOWED_HOSTS yalnız yerel adları taşıyor; ayar geçilmeden uzak konak
    # 400 dönüyor ve "düğme yok" ölçümü YANLIŞ NEDENLE geçiyordu — hata
    # sayfasında da düğme yok. Konak gerçekten kabul edilmeli.
    UZAK = override_settings(
        ALLOWED_HOSTS=["bursahakimiyet.com.tr", "127.0.0.1", "localhost"])

    def test_yabanci_konakta_cizilmiyor(self):
        """Gerçek ziyaretçi düğmeyi GÖRMEZ."""
        with self.UZAK:
            yanit = self.client.get("/", HTTP_HOST="bursahakimiyet.com.tr")
        self.assertEqual(yanit.status_code, 200)   # 400 sayfası ölçüm sayılmaz
        govde = yanit.content.decode()
        self.assertNotIn("reklam-anahtar", govde)
        self.assertNotIn("bh-reklam", govde)   # erken betik de gitmedi

    def test_yerel_makinede_ciziliyor(self):
        govde = self.client.get("/", HTTP_HOST="127.0.0.1:8000").content.decode()
        self.assertIn("reklam-anahtar", govde)
        self.assertIn('aria-pressed="false"', govde)

    def test_panel_kullanicisi_uzak_konakta_da_goruyor(self):
        from django.contrib.auth.models import User
        User.objects.create_user("editor", password="olcum-parola-123",
                                 is_staff=True)
        self.client.login(username="editor", password="olcum-parola-123")
        with self.UZAK:
            yanit = self.client.get("/", HTTP_HOST="bursahakimiyet.com.tr")
        self.assertEqual(yanit.status_code, 200)
        self.assertIn("reklam-anahtar", yanit.content.decode())

    def test_tercih_sayfa_cizilmeden_okunuyor(self):
        """Erken betik `</head>`ten ÖNCE; sonra olsaydı panolar bir an
        görünüp kaybolurdu."""
        govde = self.client.get("/", HTTP_HOST="127.0.0.1").content.decode()
        self.assertLess(govde.index("bh-reklam"), govde.index("</head>"))

    def test_bes_yuvayi_da_kapatan_kural_var(self):
        self.assertIn('html[data-reklam="kapali"] .reklam,', self.CSS)
        self.assertIn('html[data-reklam="kapali"] .yan-reklam{display:none}',
                      self.CSS)

    def test_yuvalar_gizlenince_izgara_da_tek_sutuna_iniyor(self):
        """Gerçek kusurdu: sayfa 160 px'e sıkışıyordu.

        1480 px üstünde `.sayfa` üç sütun (160 · 1100 · 160). Yan raylar
        `display:none` olunca ızgara yerleşiminden düşüyor ve orta sütun
        BİRİNCİ sütuna — 160 px'lik raya — geçiyordu. Sütun sayısı içerikle
        birlikte azalmak zorunda; ölçüldü: düzeltmeden sonra orta sütun
        reklamlar açıkken de kapalıyken de 1100 px.
        """
        self.assertIn(
            'html[data-reklam="kapali"] .sayfa{grid-template-columns:minmax(0,1100px)}',
            self.CSS)
