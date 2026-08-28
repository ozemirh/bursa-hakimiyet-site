# -*- coding: utf-8 -*-
"""Tam menü (sidebar) — yapı ve sözleşme testleri.

28 Ağustos 2026: tam genişlikte beş sütunlu levha, sağdan kayan dikey
panele çevrildi ve bölümler `<details>` ile katlanır oldu. Bu dosya
değişmemesi gerekenleri kilitler.
"""

import re
from pathlib import Path

from django.test import TestCase

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

    def test_kategori_bandi_10_kalem_dokunulmadi(self):
        """URUN-PLANI.md §1 madde 3 · F1 ölçütü 2 — bant sözleşmesi."""
        bant = re.search(r'<div class="kategori-liste"[^>]*>(.*?)</div>',
                         self.govde, re.S).group(1)
        self.assertEqual(len(re.findall(r"<a href=", bant)), 10)

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

    def test_sidebar_sabit_konumlu(self):
        kural = re.search(r"\.tam-menu\{([^}]*)\}", self.CSS).group(1)
        self.assertIn("position:fixed", kural)
        self.assertIn("var(--perde)", kural)   # perde ayrı öğe değil, gölge

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
