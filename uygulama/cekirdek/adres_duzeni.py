"""Adres düzeni — kesim günü (F8) için kalıcı yönlendirmeler (Paket G, 19 Ekim 2026).

Canlı sitede arama motorlarının bildiği ama bizde karşılığı olmayan adres
biçimleri tek katmanda kanonik biçime **301** ile bağlanır. Sorgu dizesi
(`utm_*` dahil) korunur: kampanya ölçümü yönlendirmede kaybolmasın.

| Gelen | Giden | Neden |
|---|---|---|
| `/amp/<yol>` | `/<yol>` | Canlıda her haberin AMP ikizi var (`<link rel="amphtml">`); bizde AMP yok |
| `/spor/`, `/ilce/osmangazi/`, haber adresi `/` ile | eğik çizgisiz | Adres sözleşmesi eğik çizgisiz (`APPEND_SLASH = False`); iki biçim iki kopya demekti |
| `/arama?ara=x` | `/ara?q=x` | Eski sitenin arama adresi |

Hedef bir haber adresiyse ve slug yanlışsa görünüm ikinci bir 301 verir
(kimlikle çözüm, `taksonomi/views.py`). Zincir en çok iki halkadır.

Panel, yönetim, statik ve görsel önekleri bu katmana girmez: Django'nun
yönetim adresleri eğik çizgiyle biter (`/panel/`, `/yonetim/`).
"""

from __future__ import annotations

from pathlib import Path
from urllib.parse import urlencode

from django.conf import settings
from django.http import FileResponse, Http404, HttpResponsePermanentRedirect
from django.utils.encoding import iri_to_uri

#: Bu öneklerle başlayan adresler olduğu gibi geçer.
DOKUNULMAZ = ("/panel/", "/yonetim/", "/statik/", "/static/", "/gorsel/",
              "/arsiv-gorsel/", "/arsiv-medya/", "/reklam/", "/_")


def _sorgu(request) -> str:
    ham = request.META.get("QUERY_STRING", "")
    return f"?{ham}" if ham else ""


def _yonlendir(hedef: str, sorgu: str = "") -> HttpResponsePermanentRedirect:
    return HttpResponsePermanentRedirect(iri_to_uri(hedef) + sorgu)


def hedef_bul(request) -> HttpResponsePermanentRedirect | None:
    """İstek bir düzeltme gerektiriyorsa 301 yanıtı, değilse None."""
    if request.method not in ("GET", "HEAD"):
        return None
    yol = request.path

    if yol == "/amp" or yol.startswith("/amp/"):
        kalan = yol[len("/amp"):].rstrip("/") or "/"
        return _yonlendir(kalan, _sorgu(request))

    if yol.rstrip("/") == "/arama":
        parametreler = [(ad, d) for ad, degerler in request.GET.lists()
                        if ad not in ("ara", "q") for d in degerler]
        aranan = request.GET.get("ara") or request.GET.get("q")
        if aranan:
            parametreler.insert(0, ("q", aranan))
        sorgu = urlencode(parametreler)
        return _yonlendir("/ara", f"?{sorgu}" if sorgu else "")

    if (len(yol) > 1 and yol.endswith("/")
            and not yol.startswith(DOKUNULMAZ)):
        return _yonlendir(yol.rstrip("/") or "/", _sorgu(request))
    return None


def kalici(request, hedef: str) -> HttpResponsePermanentRedirect:
    """Görünümlerin kanonik 301'i — sorgu dizesi (utm) korunur."""
    return _yonlendir(hedef, _sorgu(request))


class AdresDuzeni:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        yanit = hedef_bul(request)
        if yanit is not None:
            return yanit
        return self.get_response(request)


def favicon(request):
    """`/favicon.ico` — tarayıcılar ve Google bunu kökten ister (statik/simge/)."""
    yol = Path(settings.BASE_DIR) / "statik" / "simge" / "favicon.ico"
    if not yol.is_file():
        raise Http404("favicon yok")
    yanit = FileResponse(open(yol, "rb"), content_type="image/x-icon")
    yanit["Cache-Control"] = "public, max-age=604800"
    return yanit
