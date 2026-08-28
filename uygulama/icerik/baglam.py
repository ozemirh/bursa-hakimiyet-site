"""Her sayfada duran ortak bağlam: kategori bandı, son dakika, ilçeler.

Bunlar `taban.html` içindeki parçalarda kullanıldığı için her görünümde
tek tek verilmez; bağlam işlemcisiyle bir kez hazırlanır.

**Kategori bandı 10 kalemdir ve sırası bağlayıcıdır** (URUN-PLANI.md §1,
bileşen 3). Liste veritabanındaki 13 kategoriden türetilmez — banda girmeyen
kategoriler (Sağlık, Teknoloji, Yaşam…) tam menüde durur. Bandın iki kalemi
kategori değildir: "Yazarlar" ve "İlçeler" kendi bölümlerine, "Resmî İlan"
ise BİK yükümlülüğü olan editoryal bölüme gider.
"""

import time

from django.db import DatabaseError
from django.db.models import Count

from taksonomi.models import Ilce, Kategori

from .models import Haber

# (görünen ad, kategori adı ya da None, sabit yol) — sıra plandaki sıradır.
BANT = [
    ("YAZARLAR", None, "/yazarlar"),
    ("BURSA", "BURSA", None),
    ("BURSASPOR", "BURSASPOR", None),
    ("GÜNDEM", "GÜNDEM", None),
    ("EKONOMİ", "EKONOMİ", None),
    ("DÜNYA", "DÜNYA", None),
    ("SPOR", "SPOR", None),
    ("MAGAZİN", "MAGAZİN", None),
    ("İLÇELER", None, "/ilceler"),
    ("RESMÎ İLAN", None, "/resmi-ilan"),
]

SON_DAKIKA_ADET = 4


def site(request):
    yol = request.path

    kategoriler = {k.ad: k for k in Kategori.objects.filter(aktif=True)
                   .prefetch_related("turler")}

    bant = []
    for ad, kategori_adi, sabit_yol in BANT:
        if sabit_yol:
            hedef = sabit_yol
        else:
            kategori = kategoriler.get(kategori_adi)
            if kategori is None:
                continue  # taksonomi kurulmadıysa bandı kırma
            hedef = "/" + kategori.slug_al()
        bant.append({"ad": ad, "yol": hedef, "etkin": yol == hedef})

    return {
        "band_kategorileri": bant,
        "tum_kategoriler": _tum_kategoriler(),
        "son_dakika": Haber.yayindakiler().select_related("kategori")[:SON_DAKIKA_ADET],
        "ilceler": Ilce.objects.all(),
    }


# Menü sıralaması ÖNBELLEKLENİR.
#
# Ölçüm (27 Ağustos 2026, 308.602 haber): `annotate(Count("haberler"))`
# tek başına **1.113 ms** sürüyordu ve bu bağlam işlemcisi **her sayfada**
# çalıştığı için sitenin tamamı — anasayfa, kategori, ilçe, haber detay,
# 404 — bu bedeli ödüyordu. Sayfa kabuğunun ölçülen 1.138 ms'sinin
# neredeyse tamamı buydu.
#
# Sorgu planı: `SCAN taksonomi_kategori` + her kategori için haber
# tablosunda indeks araması + sıralama için geçici B-ağacı.
#
# `adet` **ekranda hiç gösterilmiyor**; yalnız menüyü çok haberliden aza
# sıralamak için var. Bu sıralama saatler içinde değişmez, o yüzden
# önbellek doğru araç — `views.arsiv_sayilari` ile aynı düzen.
MENU_BELLEK_SANIYE = 300
_menu_bellek: tuple[float, list] | None = None


def _tum_kategoriler():
    """Tam menüdeki liste: haber taşıyan kategoriler, çok haberliden aza.

    Kısa süre önbelleklenir; sayım kilide takılırsa son bilinen liste
    döner, o da yoksa **sayımsız** sıralamaya düşülür — menü her hâlükârda
    çizilmeli, sayfa bir sıralama yüzünden düşmemeli.
    """
    global _menu_bellek
    simdi = time.monotonic()
    if _menu_bellek and simdi - _menu_bellek[0] < MENU_BELLEK_SANIYE:
        return _menu_bellek[1]

    try:
        kategoriler = list(Kategori.objects.filter(aktif=True)
                           .prefetch_related("turler")
                           .annotate(adet=Count("haberler")).order_by("-adet"))
    except DatabaseError:
        # Kilit ya da başka bir veritabanı hatası MENÜYÜ DÜŞÜRMEZ. Yedek yolda
        # ikinci bir sorgu denenmiyor: kilitliyken o da düşerdi. Son bilinen
        # liste yoksa menünün kategori sütunu boş çizilir, sayfa ayakta kalır.
        return _menu_bellek[1] if _menu_bellek else []

    cikti = []
    for k in kategoriler:
        slug = k.slug_al()
        if slug:
            cikti.append({"ad": k.ad, "slug": slug, "adet": k.adet})
    _menu_bellek = (simdi, cikti)
    return cikti
