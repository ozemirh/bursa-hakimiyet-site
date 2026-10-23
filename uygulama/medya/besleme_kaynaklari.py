"""Medya ailelerini sitemap defterine kaydeder.

`besleme` uygulaması bu modülü Django'nun autodiscover düzeniyle kendisi
bulur; `besleme` tarafında tek satır değişmez ve iki uygulama birbirine
bağımlı olmaz (sözleşme `besleme/kaynaklar.py` başında yazılı).

Dört ailenin üçü — köşe · video · galeri — `yayin_zamani` üzerinden
aylara bölündüğü için ortak `zamanli_aile` üreticisini kullanıyor.
**Yazar ailesi ayrık:** yazar sayfasının bir "yayın anı" yok, o yüzden
`aylar()` ve `kayitlar()` işlevlerini kendi yazıyor — ayı, yazarın en
yeni yazısının tarihinden türetiyor. Canlı indekste `authors_*.xml`
dosyalarının varlığı bu ailenin de aylara bölündüğünü gösteriyor.
"""

from __future__ import annotations

from typing import Iterator

from django.db.models import Max

from besleme.aileler import AyOzeti, Aile, Kayit, aile_kaydet
from besleme.kaynaklar import zamanli_aile
from besleme.zaman import ay_sinirlari

from .models import FotoGaleri, KoseYazisi, Video, Yazar


def _kose():
    return KoseYazisi.yayindakiler().select_related("yazar")


def _video():
    return Video.yayindakiler().select_related("kategori").prefetch_related(
        "kategori__turler")


def _galeri():
    return FotoGaleri.yayindakiler().select_related("kategori").prefetch_related(
        "kategori__turler")


# -- yazar ailesi ---------------------------------------------------------

def _yazar_sorgu():
    """Listelenebilir yazarlar, en yeni yazı tarihiyle birlikte.

    Yazarın kendi zaman damgası yok; sitemap'in `lastmod` alanı için
    en yeni yazısının tarihi kullanılıyor. Hiç yazısı olmayan yazar da
    listeye girer — sayfası var ve adresi yaşıyor.
    """
    return Yazar.listedekiler().annotate(son_yazi_zamani=Max("tum_yazilari__yayin_zamani"))


def _yazar_aylar() -> list[AyOzeti]:
    kutu: dict[str, list] = {}
    for yazar in _yazar_sorgu():
        an = yazar.son_yazi_zamani
        if an is None:
            continue  # ayı belirlenemeyen yazar aylık dosyaya giremez
        ay = an.astimezone().strftime("%Y-%m")
        kutu.setdefault(ay, []).append(an)
    return [AyOzeti(ay, len(anlar), max(anlar))
            for ay, anlar in sorted(kutu.items(), reverse=True)]


def _yazar_kayitlar(ay: str) -> Iterator[Kayit]:
    bas, son = ay_sinirlari(ay)
    for yazar in _yazar_sorgu():
        an = yazar.son_yazi_zamani
        if an is None or not (bas <= an < son):
            continue
        yield Kayit(yol=yazar.get_absolute_url(), son_degisiklik=an,
                    baslik=yazar.ad)


aile_kaydet(zamanli_aile("kose", "articles", "köşe yazısı", _kose))
aile_kaydet(zamanli_aile("video", "videoGalleries", "video", _video))
aile_kaydet(zamanli_aile("galeri", "photoGalleries", "foto galeri", _galeri))
aile_kaydet(Aile(anahtar="yazar", dosya_oneki="authors", ad="yazar",
                 aylar=_yazar_aylar, kayitlar=_yazar_kayitlar))
