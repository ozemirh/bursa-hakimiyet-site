"""Panel form girdileri — 29 Ağustos 2026'da ölçülen iki kusur.

1. **Etiket alanı ekranda yoktu.** Alan `Etiket.objects.all()` üzerinden
   çoklu seçim sunuyordu ama etiket tablosu **boş** (0 satır) ve arşivde de
   etiket verisi yok: 400 kayıtlık örneklemde `anahtar_kelimeler` hepsinde
   boştu. Boş bir `<select multiple>` çökmüş bir kutu olarak çiziliyordu.
   Sonuç görsel değildi — `clean()` yayına almak için en az bir etiket şart
   koştuğu için **panelden hiçbir haber yayınlanamıyordu**.

2. **Girdiler arka planlarıyla aynı renkti.** Başsız Chrome'da ölçüldü:
   `/panel/haber/ekle` sayfasındaki **23 girdinin 23'ü** kabıyla birebir
   aynı renk (`#F4F6F8`, kontrast 1,000:1); beyaz kartların üstünde bile
   fark 1,083:1'di. Çerçeve de WCAG 1.4.11'in etkileşimli öğe sınırı için
   istediği 3:1'i karşılamıyordu (1,23:1).

Buradaki testler tarayıcı açmaz — açsalardı gerileme testi olmaz, CI'da
Chrome gerektirirdi. **Renk sözleşmesini ve kontrast oranını sayıyla**
kilitliyorlar; tarayıcı ölçümü kararı verirken bir kez yapıldı.
"""

import re
from pathlib import Path

from django.test import SimpleTestCase

STIL = (Path(__file__).resolve().parent.parent / "statik" / "stil" / "panel.css")


def _bagil_isik(renk: str) -> float:
    r, g, b = (int(renk[i:i + 2], 16) / 255 for i in (1, 3, 5))

    def d(k):
        return k / 12.92 if k <= 0.04045 else ((k + 0.055) / 1.055) ** 2.4

    return 0.2126 * d(r) + 0.7152 * d(g) + 0.0722 * d(b)


def kontrast(a: str, b: str) -> float:
    ia, ib = _bagil_isik(a), _bagil_isik(b)
    return (max(ia, ib) + 0.05) / (min(ia, ib) + 0.05)


class GirdiRengiArkaPlandanAyrisiyor(SimpleTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.css = STIL.read_text(encoding="utf-8")
        cls.degiskenler = dict(re.findall(
            r"--([a-z0-9-]+)\s*:\s*(#[0-9A-Fa-f]{6})", cls.css))

    def _renk(self, ad):
        deger = self.degiskenler.get(ad)
        self.assertIsNotNone(deger, f"--{ad} tanımlı değil")
        return deger

    def test_girdi_zemini_sayfa_zemininden_farkli(self):
        """Aynı olurlarsa haber formunda girdiler görünmez olur."""
        self.assertNotEqual(self._renk("girdi-zemin"), self._renk("zemin"))

    def test_girdi_zemini_kart_yuzeyinden_de_farkli(self):
        """Liste süzgeçleri beyaz kartın üstünde duruyor."""
        self.assertNotEqual(self._renk("girdi-zemin"), self._renk("yuzey"))

    def test_girdi_cercevesi_wcag_esigini_geciyor(self):
        """WCAG 1.4.11: etkileşimli öğe sınırı en az 3:1."""
        cerceve = self._renk("girdi-cizgi")
        for yuzey_adi in ("yuzey", "zemin", "girdi-zemin"):
            with self.subTest(yuzey=yuzey_adi):
                self.assertGreaterEqual(
                    kontrast(cerceve, self._renk(yuzey_adi)), 3.0)

    def test_girdi_kurali_sayfa_zeminini_kullanmiyor(self):
        """Kusurun kaynağı buydu: girdi de `body` de `--zemin` diyordu."""
        kural = re.search(
            r"input\[type=text\][^{]*\{([^}]*)\}", self.css, re.S)
        self.assertIsNotNone(kural, "girdi kuralı bulunamadı")
        govde = kural.group(1)
        self.assertIn("var(--girdi-zemin)", govde)
        self.assertIn("var(--girdi-cizgi)", govde)
        self.assertNotIn("background:var(--zemin)", govde.replace(" ", ""))
