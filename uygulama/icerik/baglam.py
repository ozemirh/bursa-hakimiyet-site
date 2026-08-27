"""Her sayfada duran ortak bağlam: kategori bandı, son dakika, ilçeler.

Bunlar `taban.html` içindeki parçalarda kullanıldığı için her görünümde
tek tek verilmez; bağlam işlemcisiyle bir kez hazırlanır.

**Kategori bandı 10 kalemdir ve sırası bağlayıcıdır** (URUN-PLANI.md §1,
bileşen 3). Liste veritabanındaki 13 kategoriden türetilmez — banda girmeyen
kategoriler (Sağlık, Teknoloji, Yaşam…) tam menüde durur. Bandın iki kalemi
kategori değildir: "Yazarlar" ve "İlçeler" kendi bölümlerine, "Resmî İlan"
ise BİK yükümlülüğü olan editoryal bölüme gider.
"""

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


def _tum_kategoriler():
    """Tam menüdeki liste: haber taşıyan kategoriler, çok haberliden aza."""
    cikti = []
    for k in (Kategori.objects.filter(aktif=True)
              .annotate(adet=Count("haberler")).order_by("-adet")
              .prefetch_related("turler")):
        slug = k.slug_al()
        if slug:
            cikti.append({"ad": k.ad, "slug": slug, "adet": k.adet})
    return cikti
