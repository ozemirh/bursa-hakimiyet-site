"""`?sayfa=N` çözümü — geçersiz ya da aralık dışı sayfa 404 (Paket G, 19 Ekim 2026).

Django'nun `Paginator.get_page` bozuk değeri 1. sayfaya, aralık dışını son
sayfaya çeviriyordu: `/spor?sayfa=99999` 200 dönüp son sayfayı basıyordu.
Arama motoru için bu **yumuşak 404**'tür — sonsuz sayıda adres aynı içeriği
gösterir ve tarama bütçesi boşa gider. Artık:

- parametre yok ya da boş → 1. sayfa,
- tamsayı değil, 1'den küçük ya da son sayfadan büyük → **404**.

Boş liste 1. sayfada 200'dür (`allow_empty_first_page`): bölümün hiç haberi
olmaması adres hatası değildir.
"""

from django.core.paginator import EmptyPage, PageNotAnInteger
from django.http import Http404


def sayfa_getir(sayfalayici, ham):
    if ham is None or str(ham).strip() == "":
        return sayfalayici.page(1)
    try:
        numara = int(str(ham).strip())
    except ValueError:
        raise Http404("Geçersiz sayfa numarası") from None
    if numara < 1:
        raise Http404("Geçersiz sayfa numarası")
    try:
        return sayfalayici.page(numara)
    except (EmptyPage, PageNotAnInteger):
        raise Http404("Sayfa aralık dışında") from None
