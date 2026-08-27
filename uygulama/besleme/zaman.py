"""Ay hesabı ve zaman biçimi.

**Aylık bölme yerel saate göre yapılmak zorunda.** Veritabanı zamanları
UTC saklıyor (`USE_TZ = True`), site ise `Europe/Istanbul` (+03:00).
Ölçülmüş örnek: arşivdeki en eski haberin `yayin_zamani` değeri
`2021-03-31 21:02:40` (UTC), yani yerelde **1 Nisan 2021 00:02**. UTC ayına
göre bölersek bu kayıt `news_2021-03.xml` diye olmayan bir dosyaya düşer —
canlı sitenin haber ailesi **2021-04**'te başlıyor (274 dosyalık indeks,
27 Ağustos 2026 ölçümü). Bu yüzden ay sınırları yerel saatte kurulup UTC'ye
çevrilerek sorguya verilir.

Zaman biçimi de canlı dosyalardan alındı: `2026-08-27T09:15:00+03:00`.
Saniye var, mikrosaniye yok, ofset yazılı.
"""

from __future__ import annotations

from datetime import datetime

from django.utils import timezone

AY_DESENI = r"\d{4}-\d{2}"


def ay_adi(an: datetime) -> str:
    """Bir zamanın ait olduğu aylık dosya: `2026-08`. Yerel saate göre."""
    return timezone.localtime(an).strftime("%Y-%m")


def ay_sinirlari(ay: str) -> tuple[datetime, datetime]:
    """`2026-08` → (yerel ayın başı, sonraki ayın başı), zaman dilimi bilgili.

    Üst sınır **dışlayıcıdır**; ayın son saniyesini elle hesaplamak
    (23:59:59) mikrosaniyeli kayıtları düşürür.
    """
    yil, no = int(ay[:4]), int(ay[5:7])
    dilim = timezone.get_current_timezone()
    bas = datetime(yil, no, 1, tzinfo=dilim)
    son = datetime(yil + (1 if no == 12 else 0), 1 if no == 12 else no + 1, 1,
                   tzinfo=dilim)
    return bas, son


def zaman_yaz(an: datetime) -> str:
    """`2026-08-27T09:15:00+03:00` — canlı sitemap'lerdeki biçim."""
    return timezone.localtime(an).isoformat(timespec="seconds")


def ay_dizisi(ilk: str, son: str) -> list[str]:
    """`("2021-04", "2026-08")` → aradaki bütün aylar, eskiden yeniye.

    Boş aylar da listeye girer; çağıran kayıt sayısına bakıp eleyecek.
    Aralığı **kayıttan** kurmak, ay listesini veritabanına saydırmaktan
    ucuz: bkz. `kaynaklar.zamanli_aile`.
    """
    yil, no = int(ilk[:4]), int(ilk[5:7])
    son_yil, son_no = int(son[:4]), int(son[5:7])
    aylar = []
    while (yil, no) <= (son_yil, son_no):
        aylar.append(f"{yil:04d}-{no:02d}")
        yil, no = (yil + 1, 1) if no == 12 else (yil, no + 1)
    return aylar
