"""İçerik görünümleri — anasayfa, kategori, ilçe, arama, haber detay.

Hepsi veritabanından render eder; şablonlarda gömülü haber başlığı ya da
gövdesi yoktur (F4 bitti ölçütü, madde a).

Anasayfa düzeni URUN-PLANI.md §1'deki bileşen sözleşmesine bağlıdır:
manşet **15**, ikinci alan **5**, dörtlü kutucuk **4**, haber kutuları
**2 × 5 = 10**. Bu sayılar F1'de ölçüldü; burada da sabit olarak durur ki
şablon hâli aynı ölçümü versin.
"""

import time

from django.core.paginator import Paginator
from django.db import DatabaseError
from django.db.models import Q
from django.shortcuts import get_object_or_404, render

from taksonomi.models import Ilce, Kategori

from .templatetags.site_etiket import baslikla

from medya.models import FotoGaleri, KoseYazisi, Video, Yazar

from .canli import anasayfa_verisi
from .models import Haber

MANSET = 15
IKINCIL = 5
DORTLU = 4
KUTU = 10
BURSASPOR = 6
SAYFA_BOYU = 20


# Anasayfadaki not satırları arşivin büyüklüğünü söylüyor. Bu sayılar
# şablona ELLE yazılmıştı ve göç sürdükçe yanlışlaşıyordu (ölçüm, 27 Ağustos:
# şablonda "1484 video" yazarken veritabanında 31.084 vardı). Artık
# veritabanından sayılıyor. Sayım ucuz değil (ölçüldü: dört tablo toplam
# ~67 ms), o yüzden `canli.py`deki kısa bellek düzeniyle aynı biçimde
# önbelleğe alınıyor — anasayfa her istekte dört COUNT açmasın.
SAYIM_BELLEK_SANIYE = 300
_sayim_bellek: tuple[float, dict] | None = None


def arsiv_sayilari() -> dict:
    """Anasayfa notlarındaki arşiv büyüklükleri. Kısa süre önbelleklenir.

    Sayım **anasayfayı düşürmez.** Göç sürerken aynı SQLite dosyasına yazan
    bir süreç varken sayım kilide takılabiliyor (ölçüldü: boştayken 67 ms,
    göç sürerken 1.250 ms). Kilit ya da hata gelirse bir önceki bilinen değer
    döner; o da yoksa değerler **açıkça None** olur ve şablon o cümleyi hiç
    basmaz — `canli.py`deki "kaynak düşerse bileşen sessizce gizlenir"
    kararıyla aynı.

    None ile 0 **ayrı şeylerdir**: "sayılamadı" ile "arşivde hiç yok" aynı
    cümleyi doğurmamalı. Şablon bu yüzden `is not None` ile bakar; `{% if %}`
    ile baksaydı gerçek bir sıfır da gizlenirdi (test bunu yakaladı).
    """
    global _sayim_bellek
    simdi = time.monotonic()
    if _sayim_bellek and simdi - _sayim_bellek[0] < SAYIM_BELLEK_SANIYE:
        return _sayim_bellek[1]
    try:
        sayilar = {
            "yazar_adedi": Yazar.listedekiler().count(),
            "kose_adedi": KoseYazisi.yayindakiler().count(),
            "galeri_adedi": FotoGaleri.yayindakiler().count(),
            "video_adedi": Video.yayindakiler().count(),
        }
    except DatabaseError:
        if _sayim_bellek:
            return _sayim_bellek[1]
        return {"yazar_adedi": None, "kose_adedi": None,
                "galeri_adedi": None, "video_adedi": None}
    _sayim_bellek = (simdi, sayilar)
    return sayilar


def _liste(sinirsiz=False):
    """Ortak sorgu: yayındaki haberler, adres kurmak için gereken ilişkilerle.

    `kategori__turler` prefetch'i şart: `get_absolute_url` kategorinin
    slug'ını oradan okuyor, yoksa haber başına bir sorgu daha açılıyor.
    """
    return (Haber.yayindakiler()
            .select_related("kategori", "ilce")
            .prefetch_related("kategori__turler"))


def anasayfa(request):
    """§1'deki sırayı besler. Tek sorgudan dilimlenir; sayılar sözleşmedendir.

    Manşet ile aşağıdaki bloklar aynı havuzdan gelir ve **tekrar etmemeleri**
    gerekir; bu yüzden tek listeden ardışık dilimler alınır.
    """
    gerekli = MANSET + IKINCIL + DORTLU + KUTU
    havuz = list(_liste()[:gerekli])

    kes = 0
    def al(adet):
        nonlocal kes
        parca = havuz[kes:kes + adet]
        kes += adet
        return parca

    manset = al(MANSET)
    ikincil = al(IKINCIL)
    dortlu = al(DORTLU)
    kutular = al(KUTU)

    # "En çok okunanlar" için okunma verisi yok — göçte kurtarılamadı
    # (URUN-PLANI.md §4, madde 8). Karar: başlangıçta editör seçkisi gibi
    # davranıp en yenileri göster; sayaç gerçek veriyle dolunca burası
    # değişir. Şablondaki yer-not bunu okura da söylüyor.
    en_cok = havuz[:5]

    bursaspor = Kategori.objects.filter(ad="BURSASPOR").first()
    bursaspor_haberleri = []
    if bursaspor:
        bursaspor_haberleri = list(
            _liste().filter(kategori=bursaspor)[:BURSASPOR])

    return render(request, "anasayfa.html", {
        "anasayfa_mi": True,
        "manset": manset,
        "ikincil": ikincil,
        "dortlu": dortlu,
        "kutular": kutular,
        "bursaspor_haberleri": bursaspor_haberleri,
        "en_cok": en_cok,
        # Medya aileleri göç etti; sağ ray ve alt bloklar artık gerçek
        # veriden besleniyor. Şablonlar boş listeyi yine de karşılıyor —
        # tarama sürerken bir aile boş kalabilir.
        "yazarlar": Yazar.listedekiler()[:5],
        **arsiv_sayilari(),
        **anasayfa_verisi(),
        "galeriler": FotoGaleri.yayindakiler()
                     .select_related("kategori")
                     .prefetch_related("kategori__turler")[:4],
        "videolar": Video.yayindakiler()
                    .select_related("kategori")
                    .prefetch_related("kategori__turler")[:4],
    })


def kategori(request, slug):
    """Kategori listesi. Slug **tür satırından** gelir, kategori adından değil."""
    kategori = get_object_or_404(Kategori, turler__tur=Kategori.TUR_HABER,
                                 turler__slug=slug, aktif=True)
    sayfa = _sayfala(request, _liste().filter(kategori=kategori))
    return render(request, "kategori.html", {
        "kategori": kategori,
        "baslik": baslikla(kategori.ad),
        "sayfa": sayfa,
    })


def ilce(request, slug):
    ilce = get_object_or_404(Ilce, slug=slug)
    sayfa = _sayfala(request, _liste().filter(ilce=ilce))
    return render(request, "kategori.html", {
        "baslik": f"{ilce.ad} haberleri",
        "ilce": ilce,
        "sayfa": sayfa,
    })


def ilceler(request):
    return render(request, "ilceler.html", {"baslik": "İlçeler"})


# Arşiv taraması yalnız "haber" ailesini aldı; köşe yazısı, foto galeri,
# video ve yazar aileleri hiç başlamadı (URUN-PLANI.md F3 bitti ölçütü, a).
# Bu bölümler adres sözleşmesinde var ve menüden bağlanıyor, o yüzden
# sayfaları duruyor; verileri geldiğinde aynı şablon dolar.
BEKLEYEN_AILELER = {
    "yazarlar": ("Yazarlar", "Yazar ve köşe yazısı arşivi", 18 + 6903),
    "galeriler": ("Foto galeri", "Foto galeri arşivi", 4042),
    "videolar": ("Videolar", "Video arşivi", 32006),
}


def bekleyen_aile(request, anahtar):
    baslik, ad, adet = BEKLEYEN_AILELER[anahtar]
    return render(request, "bekleyen.html", {
        "baslik": baslik,
        "aile_adi": ad,
        "beklenen_adet": adet,
    })


def resmi_ilan(request):
    """Resmî ilanlar — BİK yükümlülüğü olan editoryal bölüm.

    İlan kayıtları panelin ilan modülünden gelecek (F5); şimdilik sayfa
    duruyor ama içerik uydurulmuyor.
    """
    return render(request, "bekleyen.html", {
        "baslik": "Resmî ilanlar",
        "aile_adi": "Resmî ilan kayıtları",
        "beklenen_adet": None,
        "not_metni": "İlanlar Basın İlan Kurumu aracılığıyla yayımlanır. "
                     "Kayıtlar panelin ilan modülüne bağlanacak.",
    })


def arama(request):
    """Başlık ve spot üzerinde arama.

    SQLite üzerinde `icontains` ile çalışıyor; tam metin araması ve p95
    ölçümü F7'nin işi (PostgreSQL'e geçince). Burada amaç sayfanın
    veritabanından render edilmesi.
    """
    sorgu = (request.GET.get("q") or "").strip()
    sonuc = _liste().filter(
        Q(baslik__icontains=sorgu) | Q(spot__icontains=sorgu)
    ) if sorgu else Haber.objects.none()
    sayfa = _sayfala(request, sonuc)
    return render(request, "arama.html", {
        "baslik": f"“{sorgu}” için arama sonuçları" if sorgu else "Arama",
        "sorgu": sorgu,
        "sayfa": sayfa,
        "toplam": sayfa.paginator.count if sorgu else 0,
    })


def _sayfala(request, sorgu):
    numara = request.GET.get("sayfa") or 1
    return Paginator(sorgu, SAYFA_BOYU).get_page(numara)
