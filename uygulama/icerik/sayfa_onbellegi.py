"""Sayfa mikro önbelleği — anonim okur için 30 saniyelik HTML.

19 Ekim 2026 (başarım paketi). Bir haber sitesinde trafiğin büyük kısmı
okumadır ve son dakika anında anasayfa sıradan günün katlarca yükünü alır.
Aynı 30 saniye içinde aynı sayfayı isteyen bin okur için sayfa bir kez
kurulur.

**Ne önbelleklenir:** anasayfa, kategori, ilçe, haber detay, konu dizini
ve konu dosyası görünümleri; yalnız `GET`/`HEAD`, yalnız 200, yalnız çerez
bırakmayan yanıt.

**Ne önbelleklenmez:**

* Oturum çerezi taşıyan istek (panel kullanıcısı, mesaj taşıyan oturum):
  sayfa ona özel olabilir (sunum düğmesi, reklam test hizmeti).
* CSRF belirteci basılmış sayfa: belirteç okura özeldir, başkasına
  verilirse formu kırılır.
* Yönlendirme, 404, akış yanıtı.

**Tazelik.** §21'in kuralı "gazetede beş dakika eski manşet kabul
edilemez". Süre 30 sn ve haber, kategori, ilçe, konu, son dakika ya da
resmî ilan kaydedildiğinde bütün sayfa anahtarları ANINDA ölür: anahtara
yayın sürümü katılıyor (`onbellek.yayin_surumu`, `icerik/sinyaller.py`).

**Okunma sayacı önbelleğin ÖNÜNDE.** Sayım eskiden haber görünümünün
içindeydi; önbellekten servis edilen istek görünüme hiç girmediği için
sayılmazdı. Görünüm artık yanıta `okunma_haber` iliştiriyor, değer kayıtla
birlikte saklanıyor ve sayım hem ilk istekte hem önbellek isabetinde bu
katmanda yapılıyor.

**Anahtar.** Konak + yol + yalnız `sayfa` parametresi. Görünümlerin
okuduğu tek parametre o; `utm_source`, `fbclid` gibi paylaşım ekleri
çıktıyı değiştirmez ve her biri ayrı kayıt açsaydı önbellek çöp dolardı.
Konak anahtarda, çünkü yerel makinede sunum araçları çiziliyor.
"""

from __future__ import annotations

import hashlib
from functools import wraps

from django.conf import settings
from django.core.cache import caches
from django.http import HttpResponse

from . import okunma, onbellek

#: Anahtara giren sorgu parametreleri; görünümlerin okuduğu tek parametre.
ANAHTAR_PARAMETRELERI = ("sayfa",)

#: Oturum durumunu taşıyan çerezler. Biri varsa sayfa okura özel olabilir.
_OTURUM_CEREZLERI = None


def _oturum_cerezleri():
    global _OTURUM_CEREZLERI
    if _OTURUM_CEREZLERI is None:
        _OTURUM_CEREZLERI = (settings.SESSION_COOKIE_NAME, "messages")
    return _OTURUM_CEREZLERI


def _uygun_istek(request) -> bool:
    if request.method not in ("GET", "HEAD"):
        return False
    return not any(ad in request.COOKIES for ad in _oturum_cerezleri())


def _anahtar(request) -> str:
    parametreler = "&".join(f"{ad}={request.GET.get(ad)}"
                            for ad in ANAHTAR_PARAMETRELERI if ad in request.GET)
    ham = f"{onbellek.yayin_surumu()}|{request.get_host()}|{request.path}?{parametreler}"
    return "bh:sayfa:" + hashlib.md5(ham.encode("utf-8"), usedforsecurity=False).hexdigest()


def _saklanabilir(request, yanit) -> bool:
    if yanit.status_code != 200 or getattr(yanit, "streaming", False):
        return False
    if yanit.cookies or request.META.get("CSRF_COOKIE_NEEDS_UPDATE"):
        return False
    kullanici = getattr(request, "user", None)
    if kullanici is not None and kullanici.is_authenticated:
        return False
    denetim = yanit.get("Cache-Control", "")
    return "private" not in denetim and "no-store" not in denetim


def _say(request, haber_id) -> None:
    if haber_id:
        okunma.say(request, haber_id)


def sayfa_onbellegi(gorunum):
    """Görünümü 30 sn'lik anonim sayfa önbelleğiyle sarar (bkz. modül)."""

    @wraps(gorunum)
    def sarmal(request, *args, **kwargs):
        sure = getattr(settings, "SAYFA_ONBELLEK_SANIYE", 0)
        if sure <= 0 or not _uygun_istek(request):
            yanit = gorunum(request, *args, **kwargs)
            _say(request, getattr(yanit, "okunma_haber", None))
            return yanit

        ob = caches[onbellek.SAYFA]
        anahtar = _anahtar(request)
        kayit = ob.get(anahtar)
        if kayit is not None:
            yanit = HttpResponse(kayit["govde"], content_type=kayit["tur"])
            yanit["X-Onbellek"] = "isabet"
            _say(request, kayit.get("okunma"))
            return yanit

        yanit = gorunum(request, *args, **kwargs)
        haber_id = getattr(yanit, "okunma_haber", None)
        if _saklanabilir(request, yanit):
            ob.set(anahtar, {"govde": yanit.content, "tur": yanit["Content-Type"],
                             "okunma": haber_id}, sure)
            yanit["X-Onbellek"] = "kayit"
        _say(request, haber_id)
        return yanit

    return sarmal
