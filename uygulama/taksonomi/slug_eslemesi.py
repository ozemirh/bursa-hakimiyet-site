"""(kategori, tür) → slug eşlemesi — süreç içi, kısa ömürlü.

19 Ekim 2026 (başarım paketi). Haber adresi `get_absolute_url` →
`Kategori.slug_al` yolundan kuruluyordu ve slug `KategoriTur` satırında
duruyor. Her liste sorgusu bunun için `prefetch_related("kategori__turler")`
taşıyordu: ölçüm anasayfada 7, haber detayında 7 ayrı KategoriTur sorgusu.
Ön çekimi unutan her yeni sorgu da haber başına bir sorgu açıyordu.

Tablo 39 satır ve slug'lar DONDURULMUŞ (adresin parçası, `KategoriTur`
belgesine bakın). Bu yüzden eşleme süreç belleğinde tutulur:

* Tek sorguyla kurulur, `OMUR` saniye geçerlidir.
* `KategoriTur` kaydedilince ya da silinince bu süreçte hemen düşer
  (`icerik/sinyaller.py`); öbür süreçler en geç `OMUR` sonra tazelenir.
* Paylaşılan önbelleğe KONMAZ: sayfa başına onlarca adres kuruluyor ve
  her biri için dosya önbelleğine gitmek eşlemenin kendisinden pahalıdır.
"""

from __future__ import annotations

import threading
import time

from django.db import DatabaseError

OMUR = 60

_kilit = threading.Lock()
_eslem: dict[tuple[int, str], str] | None = None
_kuruldu = 0.0


def _kur() -> dict[tuple[int, str], str]:
    from .models import KategoriTur
    return {(k, t): s for k, t, s in
            KategoriTur.objects.values_list("kategori_id", "tur", "slug")}


#: Eşlemede OLMAYAN bir anahtar sorulursa (başka süreçte az önce açılmış
#: kategori) eşleme en çok bu sıklıkla yeniden kurulur. Bilinmeyen slug'la
#: gelen tarama istekleri tabloyu her istekte sorgulatmasın diye sınırlı.
ISKA_ARALIGI = 5


def eslem(zorla: bool = False) -> dict[tuple[int, str], str]:
    global _eslem, _kuruldu
    mevcut = _eslem
    if not zorla and mevcut is not None and time.monotonic() - _kuruldu < OMUR:
        return mevcut
    try:
        yeni = _kur()
    except DatabaseError:
        # Kilitli veritabanı adresleri DÜŞÜRMEZ: son bilinen eşleme sürer.
        if mevcut is not None:
            return mevcut
        raise
    with _kilit:
        _eslem, _kuruldu = yeni, time.monotonic()
    return yeni


def slug(kategori_id: int | None, tur: str = "haber") -> str:
    if kategori_id is None:
        return ""
    deger = eslem().get((kategori_id, tur))
    if deger is None and time.monotonic() - _kuruldu >= ISKA_ARALIGI:
        deger = eslem(zorla=True).get((kategori_id, tur))
    return deger or ""


def slug_var_mi(slug: str, tur: str = "haber") -> bool:
    """Adresteki kategori diliminin bu türde tanınıp tanınmadığı (yalnız
    eşlemeye bakar; `False` kesin değildir, çağıran veritabanına sorar)."""
    return any(t == tur and s == slug for (_, t), s in eslem().items())


def sifirla() -> None:
    global _eslem
    with _kilit:
        _eslem = None
