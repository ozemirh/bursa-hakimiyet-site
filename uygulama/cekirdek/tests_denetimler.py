"""`cekirdek/denetimler.py` — üretimde güvenilir vekil zorunluluğu (Paket L2)."""

from __future__ import annotations

from django.core.checks import run_checks
from django.test import SimpleTestCase, override_settings

from .denetimler import guvenilir_vekil
from .tests import URETIM_ORTAMI, manage


def _kimlikler(hatalar):
    return sorted(h.id for h in hatalar)


class GuvenilirVekil(SimpleTestCase):

    @override_settings(URETIM=True, VEKIL_ARKASI=True, GUVENILIR_VEKILLER=[])
    def test_uretimde_vekil_arkasinda_bos_liste_hata(self):
        self.assertEqual(_kimlikler(guvenilir_vekil()), ["bh.E001"])
        # Kayıtlı mı: Django'nun denetim koşusu da görüyor.
        self.assertIn("bh.E001", _kimlikler(run_checks()))

    @override_settings(URETIM=True, VEKIL_ARKASI=True, GUVENILIR_VEKILLER=["127.0.0.1", "::1"])
    def test_uretimde_dolu_liste_temiz(self):
        self.assertEqual(guvenilir_vekil(), [])

    @override_settings(URETIM=True, VEKIL_ARKASI=False, GUVENILIR_VEKILLER=[])
    def test_vekilsiz_kurulum_muaf(self):
        self.assertEqual(guvenilir_vekil(), [])

    @override_settings(URETIM=True, VEKIL_ARKASI=True,
                       GUVENILIR_VEKILLER=["127.0.0.1", "nginx-sunucusu", "10.0.0.0/8"])
    def test_gecersiz_adres_hata(self):
        hatalar = guvenilir_vekil()
        self.assertEqual(_kimlikler(hatalar), ["bh.E002"])
        self.assertIn("nginx-sunucusu", hatalar[0].msg)

    @override_settings(URETIM=False, GUVENILIR_VEKILLER=[])
    def test_gelistirmede_denetim_yok(self):
        self.assertEqual(guvenilir_vekil(), [])


class GuvenilirVekilUcdanUca(SimpleTestCase):
    """Gerçek ayar dosyasıyla: üretim ortamında değişken yoksa `check` düşer."""

    def test_check_vekilsiz_uretimde_duser(self):
        ortam = {k: v for k, v in URETIM_ORTAMI.items() if k != "BH_GUVENILIR_VEKIL"}
        sonuc = manage("check", degiskenler=ortam)
        self.assertNotEqual(sonuc.returncode, 0)
        self.assertIn("bh.E001", sonuc.stdout + sonuc.stderr)
        muaf = manage("check", degiskenler={**ortam, "BH_VEKIL_ARKASI": "0"})
        self.assertEqual(muaf.returncode, 0, muaf.stdout + muaf.stderr)
