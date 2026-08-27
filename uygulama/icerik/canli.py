"""`canli-veri/` çıktılarını sayfaya taşır.

Çekme betikleri (`canli-veri/*.py`) siteden **bağımsız** çalışır: zamanlanmış
görev olarak koşar, `canli-veri/veri/<bileşen>.json` yazar. Site o dosyaları
yalnızca **okur**. Bu ayrım bilinçli — bir kaynak düştüğünde ya da yavaşladığında
sayfa isteği ona takılmasın; sayfa hep diskten okur, en kötü ihtimalle biraz
eski veriyi gösterir.

## Bayatlık

Her dosya kendi `bayat_esik_dakika` değerini taşır: döviz 1.440, hava 180,
namaz 2.880, puan durumu 2.880. Eşiği aşan veri **atılmaz**, "bayat" diye
işaretlenir ve şablon güncelleme zamanını okura gösterir. Gerekçe: haftada bir
değişen puan tablosunun bir gün gecikmesi sorun değil, ama okur neye baktığını
bilmeli. Dosya hiç yoksa bileşen sessizce gizlenir — uydurma değer basmaktansa
hiç göstermemek doğru.

## Önbellek

Dosyalar her istekte diskten okunmaz; `KISA_BELLEK_SANIYE` boyunca süreç
belleğinde tutulur. Anasayfa altı bileşeni birden istiyor ve saniyede onlarca
istek gelebilir.
"""

from __future__ import annotations

import json
import time
from datetime import date, datetime
from pathlib import Path

from django.conf import settings

KISA_BELLEK_SANIYE = 30

_bellek: dict[str, tuple[float, dict | None]] = {}


def _kok() -> Path:
    return Path(getattr(settings, "CANLI_VERI_KOK",
                        settings.BASE_DIR.parent / "canli-veri" / "veri"))


def oku(bilesen: str) -> dict | None:
    """Bileşenin JSON'unu döndürür; yoksa ya da bozuksa None.

    Dönen sözlüğe iki alan eklenir:
      `bayat`      — güncelleme eşiği aştı mı
      `yas_dakika` — verinin yaşı
    """
    simdi = time.time()
    onbellek = _bellek.get(bilesen)
    if onbellek and simdi - onbellek[0] < KISA_BELLEK_SANIYE:
        return onbellek[1]

    yol = _kok() / f"{bilesen}.json"
    veri: dict | None = None
    try:
        with open(yol, "r", encoding="utf-8") as f:
            veri = json.load(f)
    except (OSError, json.JSONDecodeError):
        veri = None

    if veri is not None:
        yas = _yas_dakika(veri.get("guncelleme", ""))
        esik = veri.get("bayat_esik_dakika") or 0
        veri["yas_dakika"] = yas
        veri["bayat"] = bool(yas is not None and esik and yas > esik)

    _bellek[bilesen] = (simdi, veri)
    return veri


def _yas_dakika(damga: str):
    try:
        an = datetime.fromisoformat(damga)
    except (TypeError, ValueError):
        return None
    simdi = datetime.now(an.tzinfo) if an.tzinfo else datetime.now()
    return round((simdi - an).total_seconds() / 60, 1)


def simdiki_vakit(namaz: dict | None) -> str:
    """İçinde bulunulan namaz vaktinin anahtarı; şablon onu vurguluyor.

    Yatsıdan sonra ve imsaktan önce "yatsı" sayılır — gün dönmeden vakit
    değişmiyor.
    """
    if not namaz or not namaz.get("gunler"):
        return ""
    vakitler = namaz["gunler"][0].get("vakitler") or {}
    simdi = datetime.now().strftime("%H:%M")
    gecerli = ""
    for anahtar, saat in vakitler.items():
        if saat <= simdi:
            gecerli = anahtar
    return gecerli or "yatsi"


def _tarihe_cevir(damga: str | None):
    """`YYYY-AA-GG` → `date`; çözülemezse None (şablon o zaman hiç basmaz)."""
    try:
        return date.fromisoformat(damga)
    except (TypeError, ValueError):
        return None


def vizyon_filmleri(vizyon: dict | None, adet: int = 4) -> list[dict]:
    """Vizyon takvimini şablonun beklediği **düz** film listesine çevirir.

    Dosya haftalara bölünmüş (`haftalar[].filmler[]`); sayfadaki kart şeridi
    düz bir liste istiyor. Boş dönerse şablon sahte kart basmaz, boş durumu
    gösterir — dört tane "Vizyon filmi N — yer tutucu" kartı 27 Ağustos'ta
    bu yüzden kaldırıldı.

    **Afiş basılmaz.** Dosyanın kendi notu afişlerin telifli olduğunu ve
    dosyanın afiş taşımadığını söylüyor; ayrıca dış adrese bağlanmak sayfanın
    internetsiz açılması kuralına aykırı. Kartta yerel yer tutucu durur.
    """
    if not vizyon:
        return []
    filmler: list[dict] = []
    for hafta in vizyon.get("haftalar") or []:
        for film in hafta.get("filmler") or []:
            ad = (film.get("ad") or "").strip()
            if not ad:
                continue
            # Kaynakta olmayan alan doldurulmaz; şablon boş olanı hiç basmaz.
            turler = [t for t in (film.get("tur") or []) if t]
            filmler.append({
                "ad": ad,
                # `date` süzgeci düz metinle çalışmaz; tarih burada çözülür ki
                # sayfada "4 Aralık 2026" yazsın, "2026-12-04" değil.
                "tarih": _tarihe_cevir(film.get("tarih") or hafta.get("tarih")),
                "tur": " · ".join(turler),
                "yas_siniri": film.get("yas_siniri") or "",
                "dagitimci": film.get("dagitimci") or "",
            })
            if len(filmler) >= adet:
                return filmler
    return filmler


def anasayfa_verisi() -> dict:
    """Anasayfanın canlı veri bileşenleri.

    Adlar `canli-veri/veri/` altındaki dosya adlarıyla birebir; yeni bir
    kalem eklendiğinde burada tek satır yeter.
    """
    vizyon = oku("vizyon-takvimi")
    return {
        # Doviz bandi CANLI kur gosteriyor (27 Agustos karari): serbest
        # piyasa kuru surekli hareket eder, TCMB bulteni gunde bir cikar.
        # Bayat esigi bu yuzden dosyanin kendi degerinden gelir (45 dk).
        "doviz": oku("doviz"),
        "hava": oku("hava-durumu"),
        "namaz": oku("namaz-vakitleri"),
        "eczane": oku("nobetci-eczane"),
        "puan": oku("puan-durumu"),
        "vizyon": vizyon,
        "vizyon_filmler": vizyon_filmleri(vizyon),
        "namaz_simdiki": simdiki_vakit(oku("namaz-vakitleri")),
    }
