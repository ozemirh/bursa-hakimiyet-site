"""Test paketi hermetik mi — makinedeki gerçek dosyalara bağlılık kilidi.

Paket K (19 Ekim 2026). Önce: bazı testler `canli-veri/veri/*.json`
dosyalarını okuyordu; klasör git'te yok, temiz klonda ve CI'da sonuç
değişiyordu (ölçüldü: veri yokken `test_servis_panelleri_kaldi` düştü).
Arşiv kökü D: sürücüsündeydi. Artık test ayarı (settings.py sonundaki
"test ortamı" bloğu) üçünü de depodaki fixture'a ya da var olmayan geçici
yola yönlendirir; bu dosya o yönlendirmenin bozulmadığını sınar.
"""

import json
import os
from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase

DEPO = Path(settings.BASE_DIR).resolve()
BILESENLER = ["doviz", "hava-durumu", "namaz-vakitleri", "nobetci-eczane",
              "piyasa", "puan-durumu", "vizyon-takvimi"]


class TestKokleri(SimpleTestCase):

    def test_canli_veri_depodaki_fixture(self):
        kok = Path(settings.CANLI_VERI_KOK).resolve()
        self.assertEqual(kok, DEPO / "icerik" / "test_verisi" / "canli")
        for ad in BILESENLER:
            with open(kok / f"{ad}.json", encoding="utf-8") as f:
                veri = json.load(f)
            self.assertIn("guncelleme", veri, ad)

    def test_ortam_degiskeni_testte_yok_sayilir(self):
        """BH_CANLI_VERI_KOK verilse bile test fixture'ı okur."""
        if os.environ.get("BH_CANLI_VERI_KOK"):
            self.assertNotEqual(Path(os.environ["BH_CANLI_VERI_KOK"]).resolve(),
                                Path(settings.CANLI_VERI_KOK).resolve())
        self.assertNotIn("D:", str(settings.ARSIV_KOK).upper().replace("\\", "/")[:2])

    def test_arsiv_ve_turev_koku_var_olmayan_gecici_yol(self):
        self.assertFalse(Path(settings.ARSIV_KOK).exists(),
                         "bir test kendi klasörünü kurmadan arşive yazdı")
        self.assertEqual(Path(settings.ARSIV_GORSEL_KOK).parent, Path(settings.ARSIV_KOK))
        self.assertEqual(Path(settings.TUREV_KOK).parent, Path(settings.ARSIV_KOK).parent)

    def test_turev_koku_gorsel_turev_modulunde_de_test_yolu(self):
        from icerik import gorsel_turev
        self.assertEqual(Path(gorsel_turev.turev_koku()), Path(settings.TUREV_KOK))

    def test_onbellek_paylasilan_diske_yazmiyor(self):
        for ad, ayar in settings.CACHES.items():
            self.assertNotIn("FileBasedCache", ayar["BACKEND"], ad)

    def test_parola_karistirici_hizli(self):
        self.assertEqual(settings.PASSWORD_HASHERS,
                         ["django.contrib.auth.hashers.MD5PasswordHasher"])

    def test_fixture_kisisel_veri_tasimiyor(self):
        """Eczane adları/telefonları yer tutucu (gerçek işletme bilgisi yok)."""
        with open(Path(settings.CANLI_VERI_KOK) / "nobetci-eczane.json",
                  encoding="utf-8") as f:
            eczaneler = json.load(f)["eczaneler"]
        self.assertTrue(eczaneler)
        for e in eczaneler:
            self.assertTrue(e["ad"].startswith("ÖRNEK "), e["ad"])
            self.assertTrue(e["telefon"].startswith("0224 000 00 "), e["telefon"])
