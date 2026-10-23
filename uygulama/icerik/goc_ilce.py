"""Haber metninden ilçe çıkarımı — ÖLÇÜLMÜŞ SINIRLARIYLA.

Arşivde ilçe alanı **yoktur**. Ölçüm (28 Ağustos 2026, 8.513 kayıtlık ay-bazlı
örneklem, 42 ay klasörü):

- Arşiv JSON'unda ilçe adına ayrılmış alan yok. Bulunan 22 alanın hiçbiri yer
  bilgisi taşımıyor; `kategori_etiketi` yalnız 12 kategori adı veriyor
  (GÜNDEM · SPOR · DÜNYA · BURSA …), ilçe yok.
- Türk haber metninin klasik "İNEGÖL (İHA) -" tarih satırı **yok**: 8.512
  kaydın yalnız 5'inde (%0,1) böyle bir kalıp var, hiçbiri ilçe adı değil.
- Geriye tek yol kalıyor: **başlık ve spot içinde ilçe adını aramak.**

Bu bir ÇIKARIM'dır, kaynaktan gelen olgu değildir. O yüzden iki kural:

1. **Yalnız ilçenin KENDİ ADI aranır.** `sozluk.json`daki mahalle/köy ipuçları
   (`heykel`, `cerrah`, `fethiye`, `çekirge` …) KULLANILMAZ. Ölçüldü: mahalle
   ipucu %0,7 ek kayıt getiriyor ama neredeyse tamamı yanlış — "Şeyh
   Cerrah'ta Filistinlilere müdahale" → İnegöl, "Denizli'de tarihi eser" →
   Osmangazi (heykel = yontu), "Alerjik Rinit" → İnegöl (cerrah = hekim).
   Yanlış ilçe etiketi, boş ilçe sayfasından daha kötüdür.
2. **Birden çok ilçe geçiyorsa hiçbiri yazılmaz.** (%0,2)

ÖLÇÜLEN KAPSAMA (başlık + spot, yalnız ilçe adı):
    tek ilçe        %5,5
    birden çok      %0,2   -> yazılmaz
    hiç             %93,6  -> boş kalır

Yani 320 bin kaydın ~17.600'ü ilçe alabilir. Kalanın ilçesi **bilinmiyor**;
uydurulmaz. Gövde metnine bakmak kapsamayı ~%10'a çıkarıyor ama geçerken
anılan ilçeyi haberin ilçesi saymak demek — bilerek yapılmadı.
"""

from __future__ import annotations

import re

_KUCULT = {"İ": "i", "I": "ı"}


def kucult(metin: str) -> str:
    return "".join(_KUCULT.get(c, c) for c in metin).lower()


# Soldan kelime sınırı: "nilüfer'de" ve "inegöllü" eşleşsin, "xnilüfer" eşleşmesin.
_SINIR = r"(?<![a-zçğıöşü])"


def kaliplar(ilce_adlari) -> dict:
    """{ilçe adı: derlenmiş kalıp}. Çağıran bir kez kurar, döngüde kullanır."""
    return {ad: re.compile(_SINIR + re.escape(kucult(ad))) for ad in ilce_adlari}


def ilce_bul(baslik: str, spot: str, kaliplar_: dict) -> str | None:
    """Tek ve kesin eşleşme varsa ilçe adı, yoksa None.

    Gövdeye BAKMAZ (bkz. modül açıklaması).
    """
    metin = kucult(f"{baslik or ''} {spot or ''}")
    bulunan = [ad for ad, kalip in kaliplar_.items() if kalip.search(metin)]
    return bulunan[0] if len(bulunan) == 1 else None
