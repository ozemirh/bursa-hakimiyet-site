"""canli-veri betiklerinin ortak yardimcilari.

Yalnizca standart kutuphane. disa-aktarim/site_arsivleyici.py ile ayni
yaklasim: dogrudan istek, saygili hiz, kesintiye dayanikli, cikti yerel
dosyaya.

Buradaki tek onemli davranis "kaynak dustugunde ne olur" sorusunun cevabi:
cekme basarisiz olursa eldeki dosyaya DOKUNULMAZ, yanina bir durum dosyasi
yazilir ve betik sifirdan farkli bir kodla doner. Sayfa boylece son bilinen
tabloyu "guncelleme" damgasiyla gostermeye devam eder.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

TARAYICI = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)

TR_SAAT = timezone(timedelta(hours=3))

VARSAYILAN_KOK = Path(__file__).resolve().parent / "veri"

DENEME_SAYISI = 3
BEKLEME = 1.5  # ardisik istekler arasi saniye; kaynaga saygili hiz


# -- gizli anahtar --------------------------------------------------------

GIZLI_DOSYA = Path(__file__).resolve().parent / "gizli.json"


def gizli_oku(ad: str) -> str:
    """Bir API anahtarini once ortam degiskeninden, sonra gizli.json'dan okur.

    Anahtarlar depoya GIRMEZ: `gizli.json` .gitignore'dadir, ornegi
    `gizli-ornek.json` dosyasindadir. Ortam degiskeni oncelikli, cunku
    tek seferlik denemede `set TMDB_ANAHTAR=...` yeterli olsun istiyoruz.
    Gorev Zamanlayici'dan kosarken ortam degiskeni her zaman gorunmez;
    kalici cozum dosyadir.

    Bulunamazsa bos dize doner - cagiran taraf kendi hata metnini yazar.
    """
    d = os.environ.get(ad, "").strip()
    if d:
        return d
    try:
        with open(GIZLI_DOSYA, encoding="utf-8") as y:
            return str(json.load(y).get(ad, "")).strip()
    except (OSError, ValueError):
        return ""


# -- zaman ----------------------------------------------------------------

def simdi() -> str:
    return datetime.now(TR_SAAT).replace(microsecond=0).isoformat()


def yas_dakika(damga: str) -> float | None:
    """ISO damgasindan bu yana gecen dakika. Cozulemezse None."""
    try:
        t = datetime.fromisoformat(damga)
    except (TypeError, ValueError):
        return None
    if t.tzinfo is None:
        t = t.replace(tzinfo=TR_SAAT)
    return (datetime.now(TR_SAAT) - t).total_seconds() / 60


# -- kok ------------------------------------------------------------------

def kok_coz(arg: str | None) -> Path:
    yol = arg or os.environ.get("BH_CANLI_KOK") or VARSAYILAN_KOK
    kok = Path(yol).expanduser()
    kok.mkdir(parents=True, exist_ok=True)
    return kok


# -- log ------------------------------------------------------------------

_LOG_DOSYA: Path | None = None


def log_kur(kok: Path, ad: str) -> None:
    global _LOG_DOSYA
    _LOG_DOSYA = kok / f"log-{ad}.txt"


def log(mesaj: str) -> None:
    satir = f"[{datetime.now(TR_SAAT).strftime('%Y-%m-%d %H:%M:%S')}] {mesaj}"
    print(satir)
    if _LOG_DOSYA is not None:
        with open(_LOG_DOSYA, "a", encoding="utf-8") as f:
            f.write(satir + "\n")


# -- ag -------------------------------------------------------------------

class CekmeHatasi(Exception):
    pass


def getir(url: str, kodlama: str = "utf-8", zaman_asimi: int = 30,
          basliklar: dict | None = None, veri: bytes | None = None) -> str:
    """Sayfayi indirir; 403/429/5xx durumunda artan bekleme ile yeniden dener.

    kodlama: TFF sayfalari windows-1254, digerleri utf-8. errors="replace"
    bilerek kullaniliyor - tek bir bozuk bayt yuzunden koca tablo dusmesin.

    veri verilirse istek POST olur. Bursa Eczaci Odasi'nin nobet listesi
    tarih/ilce secimini yalnizca form gonderimiyle kabul ediyor; ayni
    yeniden deneme davranisi POST'ta da gecerli olsun diye buraya kondu.
    """
    bas = {
        "User-Agent": TARAYICI,
        "Accept-Language": "tr,en;q=0.8",
    }
    if veri is not None:
        bas["Content-Type"] = "application/x-www-form-urlencoded"
    if basliklar:
        bas.update(basliklar)
    son_hata = None
    for deneme in range(1, DENEME_SAYISI + 1):
        try:
            istek = urllib.request.Request(url, headers=bas, data=veri)
            with urllib.request.urlopen(istek, timeout=zaman_asimi) as yanit:
                return yanit.read().decode(kodlama, errors="replace")
        except urllib.error.HTTPError as e:
            son_hata = f"HTTP {e.code}"
            if e.code in (403, 429) or e.code >= 500:
                if deneme < DENEME_SAYISI:
                    time.sleep(3 * deneme)
                    continue
            break
        except Exception as e:  # ag/DNS/zaman asimi
            son_hata = repr(e)
            if deneme < DENEME_SAYISI:
                time.sleep(3 * deneme)
                continue
    raise CekmeHatasi(f"{url} alinamadi: {son_hata}")


def bekle() -> None:
    time.sleep(BEKLEME)


# -- dosya ----------------------------------------------------------------

def json_yaz(yol: Path, veri) -> None:
    """Once gecici dosyaya yazip yer degistirir; yarim dosya birakmaz."""
    yol.parent.mkdir(parents=True, exist_ok=True)
    gecici = yol.with_suffix(yol.suffix + ".gecici")
    with open(gecici, "w", encoding="utf-8") as f:
        json.dump(veri, f, ensure_ascii=False, indent=2)
        f.write("\n")
    os.replace(gecici, yol)


def json_oku(yol: Path):
    if not yol.exists():
        return None
    try:
        with open(yol, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None


# -- kaynak dustugunde ----------------------------------------------------

def durum_yaz(kok: Path, bilesen: str, durum: str, hata: str = "",
              eski_damga: str = "") -> None:
    """durum: taze | eski | yok

    taze = bu kosuda yeni veri yazildi
    eski = cekme basarisiz, onceki dosya duruyor -> sayfa onu gostersin
    yok  = cekme basarisiz ve elde hicbir sey yok -> sayfa bilesen kutusunu gizlesin
    """
    kayit = {
        "bilesen": bilesen,
        "durum": durum,
        "denendi": simdi(),
    }
    if hata:
        kayit["hata"] = hata
    if eski_damga:
        kayit["veri_damgasi"] = eski_damga
        y = yas_dakika(eski_damga)
        if y is not None:
            kayit["yas_dakika"] = round(y, 1)
    json_yaz(kok / f"durum-{bilesen}.json", kayit)


def dusme_ile_bitir(kok: Path, bilesen: str, cikti: Path, hata: str) -> int:
    """Cekme basarisiz oldugunda cagrilir; surec cikis kodunu dondurur."""
    eski = json_oku(cikti)
    if eski:
        damga = eski.get("guncelleme", "")
        durum_yaz(kok, bilesen, "eski", hata, damga)
        y = yas_dakika(damga)
        log(f"HATA: {hata}. Onceki dosya korundu"
            + (f" (yas {y:.0f} dk)." if y is not None else "."))
        return 2
    durum_yaz(kok, bilesen, "yok", hata)
    log(f"HATA: {hata}. Elde onceki veri de yok.")
    return 1
