"""Django sistem denetimleri — fail-closed düzeninin ayara bağlı parçası.

`cekirdek/ortam.py` üretimin olmazsa olmazlarını (anahtar, sunucu adları,
DEBUG) ayar yüklenirken denetler ve uygulamayı hiç açmaz. Buradakiler
ayarların TAMAMI yüklendikten sonra anlam kazanan kurallardır; `manage.py
check` (ve `migrate`, `runserver`) her koşuda çalıştırır, yayın betiği
`check --deploy --fail-level ERROR` ile koşar (`dagitim/bin/yayinla.sh`).

Kayıt: `icerik/apps.py` → `ready()`.
"""

from __future__ import annotations

import ipaddress

from django.conf import settings
from django.core.checks import Error, Tags, register


def _gecersiz_vekiller(vekiller) -> list[str]:
    hatali = []
    for v in vekiller:
        try:
            ipaddress.ip_network(v, strict=False)
        except ValueError:
            hatali.append(v)
    return hatali


@register(Tags.security)
def guvenilir_vekil(app_configs=None, **kwargs):
    """bh.E001 / bh.E002 — üretimde `BH_GUVENILIR_VEKIL` (Paket L2, 19 Ekim 2026).

    Boş liste üretimde sessiz bir arıza: `X-Forwarded-For` hiç okunmaz ve
    nginx arkasındaki BÜTÜN okurlar tek IP (127.0.0.1) sayılır — okunma
    sayacının tekrar süzgeci, giriş denemesi sınırı ve denetim kaydının IP
    alanı bozulur. Vekilsiz kurulum (`BH_VEKIL_ARKASI=0`) bu kuraldan muaftır.
    """
    if not getattr(settings, "URETIM", False):
        return []
    vekiller = list(getattr(settings, "GUVENILIR_VEKILLER", []) or [])
    hatalar = []
    if getattr(settings, "VEKIL_ARKASI", True) and not vekiller:
        hatalar.append(Error(
            "Üretimde BH_GUVENILIR_VEKIL zorunlu (vekil arkasında).",
            hint="nginx aynı makinedeyse BH_GUVENILIR_VEKIL=127.0.0.1,::1 verin; "
                 "vekilsiz kurulumda BH_VEKIL_ARKASI=0 (dagitim/.env.ornek).",
            id="bh.E001"))
    hatali = _gecersiz_vekiller(vekiller)
    if hatali:
        hatalar.append(Error(
            f"BH_GUVENILIR_VEKIL geçersiz adres/ağ içeriyor: {hatali}",
            hint="Adres (127.0.0.1) ya da CIDR (10.0.0.0/8) yazılır, virgülle ayrılır.",
            id="bh.E002"))
    return hatalar
