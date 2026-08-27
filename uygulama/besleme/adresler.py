"""Besleme adresleri — **köke bağlanmamış**, bağlamayı çağıran yapar.

Bağlama (`cekirdek/urls.py` içine, tek satır):

    path("", include("besleme.adresler")),

**Nereye konacağı bağlayıcıdır.** İki kural var:

1. `/rss` tek dilimlidir ve `cekirdek/urls.py`nin en sonundaki kategori
   kalıbı (`^(?P<slug>[-\\w]+)/?$`) her tek dilimli yolu yakalar. Bu
   satır **o kalıptan önce** gelmek zorunda; sonra gelirse `/rss`
   "rss adlı kategori" diye çözülür ve 404 verir.
2. `/rss/<kategori>` iki dilimlidir ama sonu `-{sayı}` ile bitmediği
   için haber kalıbına uymaz; yine de karışıklığa yer bırakmamak için
   `include("taksonomi.adresler")` satırından **önce** konması önerilir.

Pratik yer: `path("resmi-ilan", …)` satırının hemen ardı. Orada hem
kategori kalıbından hem de iki dilimli kalıplardan önce gelir.

Sitemap adresleri üç dilimli (`/static/sitemap/…`) ve hiçbir mevcut
kalıpla çakışmaz; sıraları serbesttir.

**Adresler canlı siteyle birebir.** `/static/sitemap/sitemap.xml`,
`/static/sitemap/news_2026-08.xml`, `/static/sitemap/googleNews.xml`,
`/robots.txt`, `/rss`. Arama motorlarının kayıtlı olduğu adresler bunlar;
yeni bir adres uydurmak F8'in bütün gerekçesini boşa çıkarır.

Not: `STATIC_URL` bu projede `statik/`, yani `/static/` yolu boştur ve
sitemap adresleriyle çakışmaz.
"""

from django.urls import path, re_path

from . import gorunumler
from .rss import GenelBesleme, KategoriBeslemesi

app_name = "besleme"

# Aile öneki: canlı indekste geçen beş ad. Kalıba açık liste yazılıyor ki
# `/static/sitemap/rastgele_2026-08.xml` isteği görünüme hiç girmesin.
ONEK = r"(?P<onek>news|articles|videoGalleries|photoGalleries|authors)"
AY = r"(?P<ay>\d{4}-\d{2})"

urlpatterns = [
    # --- sitemap (üç dilimli, çakışma yok) ---
    path("static/sitemap/sitemap.xml", gorunumler.indeks, name="sitemap-indeks"),
    path("static/sitemap/googleNews.xml", gorunumler.google_news,
         name="sitemap-google-news"),
    re_path(rf"^static/sitemap/{ONEK}_{AY}\.xml$", gorunumler.aylik,
            name="sitemap-aylik"),

    path("robots.txt", gorunumler.robots, name="robots"),

    # --- RSS ---
    # Sıra: kategori beslemesi genel beslemeden sonra; ikisi çakışmıyor
    # ama okurken "önce genel, sonra dallar" daha anlaşılır.
    path("rss", GenelBesleme(), name="rss"),
    re_path(r"^rss/(?P<slug>[-\w]+)/?$", KategoriBeslemesi(), name="rss-kategori"),
]
