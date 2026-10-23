"""Yeni içerik kimliği — TEK kaynak (19 Ekim 2026, Paket F madde 1).

## Neden ayrı bir aralık

Kimlik adresin parçasıdır (`/{kategori-slug}/{slug}-{id}`) ve göçte eski
sitenin kimlikleri birebir korundu. Bugüne kadar yeni haber "en büyük + 1"
alıyordu ve bu kural üç ayrı yerde kopyalıydı (`panel._kaydet`,
`yz_kopru._yeni_kimlik`, `eczane_haberi`). Sonuç ölçüldü: panelin verdiği
1696272–74 kimlikleri canlı sitede zaten BAŞKA haberlere ait (`-1696274`
canlıda "Cem Küçük soruşturması"). Eski site haber basmaya devam ettikçe
"en büyük + 1" kuralı her gün yeni bir çakışma doğurur.

Çözüm: panelin kimlikleri eski sitenin hiç ulaşamayacağı bir tabandan
başlar. Varsayılan **5.000.000** — eski site 19 Ekim 2026'da ~1.732.500'de
ve ayda ~6 bin kimlik ilerliyor; tabana yetişmesi on yıllar sürer.

    BH_YENI_KIMLIK_TABANI=5000000     (ortam değişkeni ya da settings)

Kural: `kimlik = max(taban, tabandaki en büyük kimlik + 1)`. Tabanın
altındaki kimlikler (göç, eski site) hesaba HİÇ girmez; yani eski siteden
yeni bir kayıt alınsa bile panelin sırası kaymaz.

## Eşzamanlılık

İki editör aynı anda "Kaydet"e basarsa ikisi de aynı adayı hesaplar.
Kayıt `force_insert=True` ile yazılır — var olan bir satırın ÜSTÜNE
YAZILMAZ, bütünlük hatası verir — ve hata gelirse aday yeniden hesaplanıp
denenir. Deneme bir savepoint içinde olduğu için dıştaki işlem bozulmaz.
Bu düzen hem SQLite'ta hem PostgreSQL'de aynı çalışır; veritabanı dizisi
(sequence) istemez.
"""

from __future__ import annotations

import os

from django.conf import settings
from django.db import IntegrityError, transaction

VARSAYILAN_TABAN = 5_000_000
EN_COK_DENEME = 25


def taban() -> int:
    """Yeni kimlik tabanı: settings > ortam > varsayılan."""
    deger = getattr(settings, "BH_YENI_KIMLIK_TABANI", None)
    if deger in (None, ""):
        deger = os.environ.get("BH_YENI_KIMLIK_TABANI", "")
    metin = str(deger if deger is not None else "").strip()
    try:
        sayi = int(metin.replace("_", "").replace(".", "")) if metin else VARSAYILAN_TABAN
    except ValueError:
        sayi = VARSAYILAN_TABAN
    # Taban eski aralığa düşürülemez: 2 milyonun altı canlı sitenin
    # kimlikleriyle çakışır. Yanlış bir ayar sessizce çakışma doğurmasın.
    return max(sayi, 2_000_000)


def aday_kimlik(model) -> int:
    """Bir sonraki aday: max(taban, tabandaki en büyük + 1).

    Sorgu birincil anahtar indeksinin yalnız taban üstü dilimine bakar;
    1 milyon satırlık tabloda da tek indeks adımıdır.
    """
    t = taban()
    en_buyuk = (model.objects.filter(pk__gte=t).order_by("-pk")
                .values_list("pk", flat=True).first())
    return max(t, (en_buyuk or 0) + 1)


def yeni_kayit_kaydet(nesne, **kaydet_secenekleri):
    """`nesne`ye yeni kimlik verip ilk kez yazar; çakışmada yeniden dener.

    Dönen değer aynı nesnedir (kimliği atanmış ve kaydedilmiş). Var olan
    bir kaydın üzerine yazmak İMKÂNSIZDIR: `force_insert` UPDATE'e düşmez.
    """
    model = type(nesne)
    son_hata = None
    for _ in range(EN_COK_DENEME):
        nesne.pk = aday_kimlik(model)
        try:
            with transaction.atomic():
                nesne.save(force_insert=True, **kaydet_secenekleri)
            return nesne
        except IntegrityError as hata:
            # Yalnız KİMLİK çakışmasında yeniden dene. Başka bir bütünlük
            # hatası (boş zorunlu alan, yabancı anahtar) tekrar denemekle
            # düzelmez; olduğu gibi yükselsin.
            if not model.objects.filter(pk=nesne.pk).exists():
                raise
            son_hata = hata
    raise IntegrityError(
        f"{model.__name__}: {EN_COK_DENEME} denemede boş kimlik bulunamadı "
        f"(son aday {nesne.pk}).") from son_hata
