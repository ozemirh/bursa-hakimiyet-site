"""Sitemap XML üreticisi — akış hâlinde, belleğe almadan.

**Neden Django'nun `contrib.sitemaps`'i kullanılmadı.** Üç ölçülmüş sebep:

1. *Dosya adı deseni tutmuyor.* `contrib.sitemaps` indeksi bölüm adı +
   sayfa numarasıyla adres kurar (`sitemap-news.xml?p=2`). Bize gereken
   `news_2026-08.xml`; aylık bölme onun kavram kümesinde yok. İndeksi ve
   adres kalıplarını baştan yazmak, kütüphaneyi kullanmakla aynı iş.
2. *Belleğe alıyor.* `views.sitemap` sayfalayıcıdan `page.object_list`
   alır; `Sitemap.get_urls()` her adres için sözlük kurup **liste**
   döndürür. 556.824 kayıtta bu tek başına yüzlerce MB, üstelik OFFSET'li
   sayfalama sayfa numarası büyüdükçe kareli yavaşlar.
3. *Adres başına sorgu.* `Sitemap.location()` varsayılan olarak
   `get_absolute_url()` çağırır; `Haber.get_absolute_url` kategorinin
   slug'ını ilişkiden okuyor. Ön çekim kurmanın yolu yok.

Aylık bölme zaten sayfalamanın kendisi: her dosya bir ay, her ay
ortalama ~8.500 kayıt. Bu yüzden burada sayfalayıcı yok; her ay için tek
sıralı sorgu ve `iterator()` var.

**RSS tarafı bunun tersi.** `besleme/rss.py` Django'nun
`contrib.syndication`'ını kullanıyor: beslemeler 60 kalemlik, ölçek
sorunu yok ve RSS 2.0'ın ayrıntısını (pubDate biçimi, guid, kaçış)
kütüphane doğru yapıyor.

Biçim canlı siteden ölçüldü (27 Ağustos 2026): girinti **sekme**,
`changefreq daily`, `priority 0.5`, zaman `2026-08-27T09:15:00+03:00`.
Google News dosyası ayrı biçimde — iki boşluk girintili, ayrı ad alanı.

Bilerek atlanan tek satır, canlı dosyaların ikinci satırındaki
`<?xml-stylesheet … indexStyle.xslt?>` yönergesi. Yalnızca dosya
tarayıcıda **elle** açıldığında görünümü süslüyor; arama motoru onu
okumuyor. Karşılığında eski alan adındaki bir XSLT dosyasına bağımlılık
getiriyordu ve o dosya yeni sistemde yok. Diff alan biri farkı burada
görsün diye yazıldı.
"""

from __future__ import annotations

import re
from typing import Iterable, Iterator
from xml.sax.saxutils import escape

from django.utils import timezone

from . import ayarlar
from .aileler import Aile, AyOzeti, dosya_adi, kayitli_aileler
from .zaman import zaman_yaz

# Canlı sitede sitemap dosyaları `/static/sitemap/` altında duruyor ve
# arama motorlarının kayıtlı olduğu adres bu. Değiştirmek, F8'in bütün
# gerekçesini (mevcut kayıtlar bu adreslere bakıyor) çöpe atar.
DIZIN_YOLU = "/static/sitemap"
INDEKS_ADI = "sitemap.xml"
GOOGLE_NEWS_ADI = "googleNews.xml"

# Dosya adından ay çekerken kullanılıyor. Görünümlerde **doğrulama**
# görevi de var: `../` içeren bir ay değeri dosya yoluna dönüşmemeli.
AY_DESENI = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")

# sitemaps.org sınırı: dosya başına 50.000 adres, 50 MB. Ölçüm:
# news_2026-08.xml 5.436 adres / 1,34 MB, yani adres başına ~246 bayt ve
# 50.000 adres ~ 12 MB. En yoğun ay ~15.000 olduğu için sınır bugün
# aşılmıyor; aşılırsa komut uyarır, sessizce bölmez (bölme dosya adını
# değiştirir ve kayıtlı adresleri kırar).
ADRES_SINIRI = 50_000

_INDEKS_BAS = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"'
    ' lastModified="{yerel}" lastmod="{iso}">\n'
)
_INDEKS_SON = "</sitemapindex>\n"

_URLSET_BAS = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"'
    ' xmlns:xhtml="http://www.w3.org/1999/xhtml"'
    ' xmlns:news="http://www.google.com/schemas/sitemap-news/0.9"'
    ' xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">\n'
)
_URLSET_SON = "</urlset>\n"

_HABER_URLSET_BAS = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"'
    ' xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">\n'
)


def ay_gecerli(ay: str) -> bool:
    return bool(AY_DESENI.match(ay or ""))


def dosya_adresi(kok: str, ad: str) -> str:
    """`https://alan.adi/static/sitemap/news_2026-08.xml`."""
    return f"{kok}{DIZIN_YOLU}/{ad}"


def _loc(kok: str, yol: str) -> str:
    """Mutlak adres, XML'e güvenli.

    Kaçış şart: slug'lar temiz olsa da bir gün gövdeden gelen bir `&` ya
    da sorgu parametresi dosyayı bozar ve arama motoru **tüm dosyayı**
    atar — tek adresi değil.
    """
    return escape(f"{kok}{yol}")


# -- indeks ---------------------------------------------------------------

def indeks_parcalari(kok: str, ozetler: dict[str, list[AyOzeti]] | None = None,
                     aileler: Iterable[Aile] | None = None) -> Iterator[str]:
    """Sitemap indeksi.

    `ozetler` verilmezse her aileye `aylar()` sorulur. Yönetim komutu
    dosyaları yazarken bu bilgiyi zaten topladığı için ona veriyor;
    aynı 274 satırlık özet iki kez hesaplanmıyor.
    """
    aileler = list(aileler if aileler is not None else kayitli_aileler())
    simdi = timezone.localtime()
    yield _INDEKS_BAS.format(yerel=simdi.strftime("%Y-%m-%d %H:%M:%S"),
                             iso=zaman_yaz(simdi))
    for aile in aileler:
        aylar = (ozetler or {}).get(aile.anahtar)
        if aylar is None:
            aylar = aile.aylar()
        for ozet in aylar:
            adres = dosya_adresi(kok, dosya_adi(aile, ozet.ay))
            yield ("\t<sitemap>\n"
                   f"\t\t<loc>{escape(adres)}</loc>\n"
                   f"\t\t<lastmod>{zaman_yaz(ozet.son_degisiklik)}</lastmod>\n"
                   "\t</sitemap>\n")
    yield _INDEKS_SON


# -- aylık dosya ----------------------------------------------------------

def aylik_parcalar(kok: str, aile: Aile, ay: str,
                   sayac: dict | None = None) -> Iterator[str]:
    """Bir ailenin bir aylık dosyası.

    `sayac` verilirse iş bitince `sayac["adet"]` yazılır. F8 ölçütü
    "adres sayıları kaynağıyla eşleşiyor" diyor; sayının **yazılan
    dosyadan** gelmesi, sorgudan tahmin edilmesinden daha güvenilir.
    """
    if not ay_gecerli(ay):
        raise ValueError(f"Geçersiz ay: {ay!r}. Beklenen biçim YYYY-AA.")
    yield _URLSET_BAS
    adet = 0
    for kayit in aile.kayitlar(ay):
        adet += 1
        yield ("\t<url>\n"
               f"\t\t<loc>{_loc(kok, kayit.yol)}</loc>\n"
               f"\t\t<lastmod>{zaman_yaz(kayit.son_degisiklik)}</lastmod>\n"
               "\t\t<changefreq>daily</changefreq>\n"
               "\t\t<priority>0.5</priority>\n"
               "\t</url>\n")
    yield _URLSET_SON
    if sayac is not None:
        sayac["adet"] = adet


# -- Google News ----------------------------------------------------------

def google_news_parcalari(kok: str, aile: Aile, saat: int = 48,
                          sayac: dict | None = None) -> Iterator[str]:
    """Google News sitemap'i — **yalnız son 48 saat**.

    Kuralı Google koyuyor: iki günden eski adres bu dosyada işe yaramaz,
    yalnızca dosyayı şişirir. Bu yüzden `news:news` etiketleri beş ailenin
    aylık dosyalarına **konmadı**; oraya konsa 2021 tarihli 8.500 adres
    Google News'e geçersiz veri olarak giderdi. Canlı site de aynı ayrımı
    yapıyor: aylık dosyalarda `news:` ad alanı tanımlı ama hiç
    kullanılmıyor, haber akışı ayrı `googleNews.xml` dosyasında duruyor
    (ölçüm: 473 adres, 27 Ağustos 2026).
    """
    if aile.son_kayitlar is None:
        raise ValueError(f"{aile.ad} ailesi son kayıt akışı vermiyor.")
    ad = escape(ayarlar.yayin_adi())
    dil = escape(ayarlar.dil())
    yield _HABER_URLSET_BAS
    adet = 0
    for kayit in aile.son_kayitlar(saat):
        adet += 1
        an = kayit.yayin or kayit.son_degisiklik
        yield ("<url>\n"
               f"  <loc>{_loc(kok, kayit.yol)}</loc>\n"
               "  <news:news>\n"
               "    <news:publication>\n"
               f"      <news:name>{ad}</news:name>\n"
               f"      <news:language>{dil}</news:language>\n"
               "    </news:publication>\n"
               f"    <news:publication_date>{zaman_yaz(an)}</news:publication_date>\n"
               f"    <news:title>{escape(kayit.baslik)}</news:title>\n"
               "  </news:news>\n"
               "</url>\n")
    yield _URLSET_SON
    if sayac is not None:
        sayac["adet"] = adet


# -- diske yazma ----------------------------------------------------------

def dosyaya_yaz(yol, parcalar: Iterator[str]) -> int:
    """Parçaları diske akıtır, yazılan bayt sayısını döndürür.

    Doğrudan hedefe değil, önce `.tmp` uzantısına yazıp sonunda taşıyor:
    üretim yarıda kesilirse arama motoru yarım bir sitemap okumasın.
    """
    gecici = yol.with_name(yol.name + ".tmp")
    bayt = 0
    with open(gecici, "w", encoding="utf-8", newline="\n") as dosya:
        for parca in parcalar:
            dosya.write(parca)
            bayt += len(parca.encode("utf-8"))
    gecici.replace(yol)
    return bayt
