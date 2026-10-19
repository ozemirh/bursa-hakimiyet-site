"""Sağlık ucu: `/_durum` (19 Ekim 2026).

Dış yoklama (uptime denetçisi) ve kesim günü için tek adres. `/saglik`
kullanılmadı: o bir kategori slug'ı.

Yanıt JSON'dur, önbelleğe alınmaz (`never_cache`; nginx mikro önbelleği de
`Cache-Control: no-store`'u görüp atlar).

**Kime ne gösterilir.** Yetkisiz istek yalnız özet alır:
`{"genel": "tamam" | "uyari" | "bozuk"}` ve durum kodu. Ayrıntı (disk yolu,
sürüm, hangi bileşenin bayat olduğu) saldırgana altyapı haritası olurdu.
Ayrıntıyı görenler: panele girmiş personel (`is_staff`) ya da
`X-Durum-Anahtari` başlığında `BH_DURUM_ANAHTARI` değerini gönderen
denetçi.

**Durum kodu.** Veritabanı yanıt vermiyorsa ya da disk kritik doluysa 503
— bu, yük dengeleyicinin ve denetçinin "site düştü" demesi gereken durum.
Canlı veri bayatsa ya da disk azalıyorsa 200 + `"genel": "uyari"`: site
çalışıyor, ama birinin bakması gerekiyor. Zamanlayıcı kapalıyken (19 Ekim
2026'daki durum) bu uç bilerek "uyari" döner; doğru davranış budur.
"""

from __future__ import annotations

import hmac
import json
import os
import shutil
import time
from datetime import datetime
from functools import lru_cache
from pathlib import Path

from django.conf import settings
from django.db import connection
from django.http import JsonResponse
from django.views.decorators.cache import never_cache

# Disk: bu eşiklerin altında uyarı / bozuk. Görsel türevleri ve PostgreSQL
# aynı diske yazıyorsa dolu disk sitenin sessizce yazamaması demektir.
DISK_UYARI_ORAN = 0.10
DISK_UYARI_GB = 10
DISK_BOZUK_ORAN = 0.02


def _yas_dakika(damga: str | None):
    if not damga:
        return None
    try:
        an = datetime.fromisoformat(damga)
    except (TypeError, ValueError):
        return None
    simdi = datetime.now(an.tzinfo) if an.tzinfo else datetime.now()
    return round((simdi - an).total_seconds() / 60, 1)


def _veritabani() -> dict:
    bas = time.perf_counter()
    try:
        with connection.cursor() as imlec:
            imlec.execute("SELECT 1")
            imlec.fetchone()
    except Exception as hata:  # noqa: BLE001 - her hata "bozuk" demek
        return {"durum": "bozuk", "hata": type(hata).__name__}
    return {"durum": "tamam", "motor": connection.vendor,
            "sure_ms": round((time.perf_counter() - bas) * 1000, 1)}


def _canli_veri() -> dict:
    """Her bileşen için iki yaş: verinin kendisi ve son çekme denemesi.

    Veri yaşı `<bilesen>.json` içindeki `guncelleme` damgasından, eşik aynı
    dosyanın `bayat_esik_dakika` alanından gelir (`icerik/canli.py` ile aynı
    kural). Deneme yaşı `durum-<bilesen>.json`dan: zamanlayıcı çalışıyor mu?
    """
    kok = Path(settings.CANLI_VERI_KOK)
    if not kok.is_dir():
        return {"durum": "yok", "kok_var": False, "bilesenler": {}}
    bilesenler = {}
    for durum_yolu in sorted(kok.glob("durum-*.json")):
        ad = durum_yolu.stem[len("durum-"):]
        kayit = _json(durum_yolu) or {}
        veri = _json(kok / f"{ad}.json") or {}
        veri_yas = _yas_dakika(veri.get("guncelleme"))
        esik = veri.get("bayat_esik_dakika") or 0
        bayat = veri_yas is None or bool(esik and veri_yas > esik)
        bilesenler[ad] = {
            "son_kosu": kayit.get("durum"),
            "denendi": kayit.get("denendi"),
            "deneme_yas_dakika": _yas_dakika(kayit.get("denendi")),
            "veri_yas_dakika": veri_yas,
            "esik_dakika": esik or None,
            "bayat": bayat,
        }
    bayatlar = sorted(a for a, b in bilesenler.items() if b["bayat"])
    return {"durum": "bayat" if bayatlar or not bilesenler else "taze",
            "bayat": bayatlar, "bilesenler": bilesenler}


def _json(yol: Path):
    try:
        with open(yol, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def _disk() -> dict:
    yollar = {"uygulama": Path(settings.BASE_DIR)}
    arsiv = getattr(settings, "ARSIV_KOK", None)
    if arsiv and Path(arsiv).is_dir():
        yollar["arsiv"] = Path(arsiv)
    sonuc, genel = {}, "tamam"
    for ad, yol in yollar.items():
        try:
            kullanim = shutil.disk_usage(yol)
        except OSError:
            continue
        oran = kullanim.free / kullanim.total if kullanim.total else 0
        bos_gb = kullanim.free / 1024 ** 3
        durum = "tamam"
        if oran < DISK_BOZUK_ORAN:
            durum = "bozuk"
        elif oran < DISK_UYARI_ORAN or bos_gb < DISK_UYARI_GB:
            durum = "uyari"
        sonuc[ad] = {"durum": durum, "bos_gb": round(bos_gb, 1),
                     "bos_oran": round(oran, 3)}
        if durum == "bozuk" or (durum == "uyari" and genel == "tamam"):
            genel = durum
    return {"durum": genel, "bolumler": sonuc}


@lru_cache(maxsize=1)
def surum() -> dict:
    """Çalışan kodun sürümü: `BH_SURUM` ya da git HEAD (alt süreç açmadan).

    Dağıtım betiği `BH_SURUM`ü yazarsa o esastır; yoksa depo kökündeki
    `.git` okunur. Worktree'de `.git` bir dosyadır ve gerçek dizini gösterir.
    Süreç ömrü boyunca önbellekte: kod değişince süreç zaten yeniden başlar.
    """
    acik = os.environ.get("BH_SURUM", "").strip()
    if acik:
        return {"commit": acik, "kaynak": "BH_SURUM"}
    try:
        git = Path(settings.BASE_DIR).parent / ".git"
        if git.is_file():
            hedef = git.read_text(encoding="utf-8").strip()
            if hedef.startswith("gitdir:"):
                git = (git.parent / hedef[len("gitdir:"):].strip()).resolve()
        bas = (git / "HEAD").read_text(encoding="utf-8").strip()
        if not bas.startswith("ref:"):
            return {"commit": bas[:40], "kaynak": "git"}
        ref = bas[len("ref:"):].strip()
        ortak = git
        ortak_dosya = git / "commondir"
        if ortak_dosya.is_file():
            ortak = (git / ortak_dosya.read_text(encoding="utf-8").strip()).resolve()
        for yer in (git, ortak):
            dosya = yer / ref
            if dosya.is_file():
                return {"commit": dosya.read_text(encoding="utf-8").strip()[:40],
                        "dal": ref.rsplit("/", 1)[-1] if ref.startswith("refs/heads/")
                        else ref, "kaynak": "git"}
        paketli = ortak / "packed-refs"
        if paketli.is_file():
            for satir in paketli.read_text(encoding="utf-8").splitlines():
                if satir.endswith(" " + ref):
                    return {"commit": satir.split(" ", 1)[0][:40],
                            "dal": ref.rsplit("/", 1)[-1], "kaynak": "git"}
    except OSError:
        pass
    return {"commit": None, "kaynak": "bilinmiyor"}


def _ayrinti_yetkisi(request) -> bool:
    kullanici = getattr(request, "user", None)
    if kullanici is not None and kullanici.is_authenticated and kullanici.is_staff:
        return True
    beklenen = os.environ.get("BH_DURUM_ANAHTARI", "")
    gelen = request.headers.get("X-Durum-Anahtari", "")
    return bool(beklenen) and hmac.compare_digest(gelen.encode(), beklenen.encode())


@never_cache
def durum(request):
    vt = _veritabani()
    canli = _canli_veri()
    disk = _disk()
    if vt["durum"] == "bozuk" or disk["durum"] == "bozuk":
        genel = "bozuk"
    elif canli["durum"] != "taze" or disk["durum"] == "uyari":
        genel = "uyari"
    else:
        genel = "tamam"
    kod = 503 if genel == "bozuk" else 200
    govde = {"genel": genel, "zaman": datetime.now().astimezone().isoformat(
        timespec="seconds")}
    if _ayrinti_yetkisi(request):
        govde.update({
            "ortam": getattr(settings, "ORTAM", None),
            "surum": surum(),
            "veritabani": vt,
            "canli_veri": canli,
            "disk": disk,
        })
    yanit = JsonResponse(govde, status=kod,
                         json_dumps_params={"ensure_ascii": False})
    yanit["X-Robots-Tag"] = "noindex"
    return yanit
