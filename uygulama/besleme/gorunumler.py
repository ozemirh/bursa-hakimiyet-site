"""Sitemap ve robots.txt görünümleri.

**Bunlar üretimin aslı değil, doğrulama yoludur.** Canlı sitede sitemap
dosyaları statiktir (`/static/sitemap/…`) ve web sunucusu servis eder;
556.824 adresi her tarayıcı isteğinde yeniden üretmek anlamsız.
`manage.py site_haritasi_uret` dosyaları diske yazar, bu görünümler ise
geliştirmede ve F8 karşılaştırmasında aynı çıktıyı **canlı veriden**
üretip göstermek için var. İkisi de `siteharitasi.py`deki tek üreteci
çağırır; ayrışma ihtimali yok.

Aylık dosya `StreamingHttpResponse` ile dönüyor: en yoğun ay ~15.000
adres / ~4 MB ve bunu belleğe alıp tek parça göndermek gereksiz.
"""

from __future__ import annotations

from django.http import Http404, HttpResponse, StreamingHttpResponse

from . import ayarlar, siteharitasi
from .aileler import onekten_aile

XML_TURU = "application/xml; charset=utf-8"


def indeks(istek):
    """`/static/sitemap/sitemap.xml` — beş ailenin bütün aylık dosyaları."""
    kok = ayarlar.site_koku(istek)
    return StreamingHttpResponse(
        siteharitasi.indeks_parcalari(kok), content_type=XML_TURU)


def aylik(istek, onek, ay):
    """`/static/sitemap/news_2026-08.xml`.

    Aile deftere kayıtlı değilse 404. Sessizce boş dosya döndürmek daha
    kötü olurdu: arama motoru "bu ay boşalmış" diye kayıtlı adresleri
    düşürür.
    """
    aile = onekten_aile(onek)
    if aile is None or not siteharitasi.ay_gecerli(ay):
        raise Http404("Böyle bir sitemap dosyası yok.")
    kok = ayarlar.site_koku(istek)
    return StreamingHttpResponse(
        siteharitasi.aylik_parcalar(kok, aile, ay), content_type=XML_TURU)


def google_news(istek):
    """`/static/sitemap/googleNews.xml` — son 48 saatin haberleri."""
    aile = onekten_aile("news")
    if aile is None or aile.son_kayitlar is None:
        raise Http404("Haber ailesi kayıtlı değil.")
    kok = ayarlar.site_koku(istek)
    return StreamingHttpResponse(
        siteharitasi.google_news_parcalari(kok, aile), content_type=XML_TURU)


def robots(istek):
    """Arama motoruna sitemap'lerin yerini söyler.

    Canlı `robots.txt`ten birebir alındı (27 Ağustos 2026 ölçümü): iki
    `Sitemap:` satırı, arama sayfası ve kategori sayfalama adresleri
    kapalı. Arama sonucu sayfaları taranırsa aynı içerik onlarca adreste
    tekrarlanmış görünür.
    """
    kok = ayarlar.site_koku(istek)
    satirlar = [
        "User-agent: facebookexternalhit",
        "Allow: /",
        "",
        "User-agent: *",
        "Allow: /",
        "Disallow: /ara",
        "Disallow: /panel/",
        "Disallow: /yonetim/",
        "",
        f"Sitemap: {siteharitasi.dosya_adresi(kok, siteharitasi.INDEKS_ADI)}",
        f"Sitemap: {siteharitasi.dosya_adresi(kok, siteharitasi.GOOGLE_NEWS_ADI)}",
        "",
    ]
    return HttpResponse("\n".join(satirlar), content_type="text/plain; charset=utf-8")
