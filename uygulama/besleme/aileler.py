"""Aile kayıt defteri — sitemap üreticisinin içerik kaynağından ayrıldığı yer.

Canlı sitenin sitemap indeksinde **beş aile** var ve her biri aylık
dosyalara bölünmüş (`disa-aktarim/site_arsivleyici.py` içindeki `AILELER`
sözlüğüyle aynı önekler):

    news_YYYY-MM.xml            haber
    articles_YYYY-MM.xml        köşe yazısı
    videoGalleries_YYYY-MM.xml  video
    photoGalleries_YYYY-MM.xml  foto galeri
    authors_YYYY-MM.xml         yazar

Bugün veritabanında yalnız **haber** ailesi var; diğer dördünün modeli
`uygulama/medya/` altında ayrı yazılıyor. Bu yüzden üretici modelleri
doğrudan tanımaz: her aile kendini `aile_kaydet()` ile deftere yazdırır,
üretici de yalnızca deftere bakar. Yeni aile geldiğinde bu dosyada tek
satır bile değişmez.

**Sıra bağlayıcıdır.** İndeksteki blok sırası canlı sitede
news → articles → videoGalleries → photoGalleries → authors biçiminde
ölçüldü (27 Ağustos 2026, 274 dosya). Karşılaştırma yapılırken satır satır
diff alınabilsin diye aynı sırayı koruyoruz.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Iterable, Iterator, NamedTuple


class Kayit(NamedTuple):
    """Sitemap'e girecek tek adres.

    `yol` **kökten göreli**dir (`/spor/…-526347`); alan adı üretim anında
    başa eklenir, çünkü aynı kayıt hem canlı adresle hem geliştirme
    adresiyle basılabilmeli.

    `baslik` yalnız Google News sitemap'inde kullanılır; diğer dosyalarda
    boş kalması sorun değildir.
    """

    yol: str
    son_degisiklik: datetime
    yayin: datetime | None = None
    baslik: str = ""


class AyOzeti(NamedTuple):
    """Bir aylık dosyanın özeti: adı, kaç adres içerdiği, en son ne zaman
    değiştiği.

    Üçü tek sorguda çıkar (`Count` + `Max`). `son_degisiklik` indeksteki
    `<lastmod>` alanına yazılır; ayrı sorguyla toplansaydı 274 dosyalık
    indeks için 274 sorgu daha açılırdı.
    """

    ay: str
    adet: int
    son_degisiklik: datetime


@dataclass(frozen=True)
class Aile:
    """Bir sitemap ailesinin sözleşmesi.

    `aylar()`   → [AyOzeti("2026-08", 5436, …), …] — dolu aylar,
                  **yeniden eskiye**. Sayı ve son değişiklik de gelir;
                  indeks yazılırken ve F8 karşılaştırma komutunda aynı
                  değer iki kez hesaplanmasın diye.
    `kayitlar(ay)` → o ayın kayıtları, **akış hâlinde**. 556.824 kayıtlık
                  aile bellekte tutulamaz; bu yüzden liste değil üreteç.
    """

    anahtar: str
    dosya_oneki: str
    ad: str
    aylar: Callable[[], list[AyOzeti]]
    kayitlar: Callable[[str], Iterator[Kayit]]
    # Google News sitemap'i yalnız son 48 saati alır ve tüm ailelerde
    # anlamlı değildir (yazar sayfasının yayın anı yoktur). Veren aile verir.
    son_kayitlar: Callable[[int], Iterable[Kayit]] | None = None


# İndeksteki blok sırası. Deftere kaydolmamış aile atlanır.
SIRA = ["haber", "kose", "video", "galeri", "yazar"]

_DEFTER: dict[str, Aile] = {}


def aile_kaydet(aile: Aile) -> None:
    """Aileyi deftere yazar. Aynı anahtar iki kez gelirse sonuncusu kalır."""
    if aile.anahtar not in SIRA:
        raise ValueError(
            f"Bilinmeyen aile anahtarı: {aile.anahtar!r}. "
            f"Canlı sitede beş aile var: {', '.join(SIRA)}."
        )
    _DEFTER[aile.anahtar] = aile


def aile_sil(anahtar: str) -> None:
    """Testler ve yönetim komutu için: defteri eski hâline döndürmek."""
    _DEFTER.pop(anahtar, None)


def aile(anahtar: str) -> Aile | None:
    return _DEFTER.get(anahtar)


def kayitli_aileler() -> list[Aile]:
    """Deftere yazılmış aileler — canlı indeksle aynı sırada."""
    return [_DEFTER[a] for a in SIRA if a in _DEFTER]


def onekten_aile(onek: str) -> Aile | None:
    """`news` → haber ailesi. Adres kalıbı dosya adından aileyi bulur."""
    for a in kayitli_aileler():
        if a.dosya_oneki == onek:
            return a
    return None


def dosya_adi(a: Aile, ay: str) -> str:
    """`news_2026-08.xml`. Desen canlı siteyle birebir; değiştirilemez."""
    return f"{a.dosya_oneki}_{ay}.xml"
