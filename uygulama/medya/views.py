"""Medya görünümleri — yazar · köşe yazısı · foto galeri · video.

**Çözüm kimlikle yapılır, slug yok sayılır.** Canlı sitenin ölçülmüş davranışı
budur (`/spor/yanlis-slug-526347` → 200 + kanoniğe 301) ve dört aile için de
aynen geçerlidir. Kanonik adres kaydın kendisinden kurulur, adresten değil.

Kayıt yoksa ne olacağı `icerik`/`taksonomi` tarafındaki F4 kararıyla aynı:
**404**, sessiz boş sayfa değil. F2'de bu görünümler kayıt olsun olmasın 200
dönüyordu; içerik modeli geldiği için o taslak davranış kalkıyor.

Kaydı olmayan ama dilimi tanınan adreste eski davranış korunuyor: yanlış slug
→ kanoniğe **301**, tanınmayan kategori kimliği → **404**. Tarama sürerken
gelen adreslerin kanonik biçime düşmesi bu sayede sürüyor.
"""

from django.core.paginator import Paginator
from django.http import Http404
from django.shortcuts import redirect, render

from taksonomi.models import Kategori, KategoriTur

from .models import FotoGaleri, KoseYazisi, Video, Yazar

SAYFA_BOYU = 20
YAZAR_SAYFA_BOYU = 15


def _sayfala(request, sorgu, boyut=SAYFA_BOYU):
    return Paginator(sorgu, boyut).get_page(request.GET.get("sayfa") or 1)


def _kanoniklestir(request, kayit):
    """Adres kaydın kanonik adresi değilse 301 döndürür, değilse None."""
    kanonik = kayit.get_absolute_url()
    if request.path.rstrip("/") != kanonik:
        return redirect(kanonik, permanent=True)
    return None


def _dilim_bekleyen(kok: str, tur: str, dilim_slug: str, dilim_id: str, slug: str, kimlik):
    """Kaydı henüz göç etmemiş adresin yanıtı.

    Kategori kimliği taksonomide yoksa adres hiç geçerli değildir → 404.
    Geçerli ama slug sapmışsa kanoniğe 301 verilir; kayıt geldiğinde okur
    doğru adreste olur. İkisi de değilse kayıt yok demektir → 404.
    """
    satir = KategoriTur.objects.filter(tur=tur, eski_id=int(dilim_id)).first()
    if satir is None:
        raise Http404("Bilinmeyen kategori kimliği")
    if satir.slug != dilim_slug:
        return redirect(f"/{kok}/{satir.slug}-{dilim_id}/{slug}-{kimlik}", permanent=True)
    raise Http404("Kayıt yok")


# -- yazar ------------------------------------------------------------------

def yazar(request, dilim_slug, dilim_id):
    """Yazar sayfası ve köşe yazıları listesi.

    Pasif yazarın sayfası da açılır: `aktif` yalnız listeleri süzer, eski
    bağlantıların 404 olmaması gerekir.
    """
    kayit = Yazar.objects.filter(pk=int(dilim_id)).first()
    if kayit is None:
        raise Http404("Yazar yok")

    yonlendirme = _kanoniklestir(request, kayit)
    if yonlendirme is not None:
        return yonlendirme

    sayfa = _sayfala(request, kayit.yazilari().select_related("yazar"),
                     YAZAR_SAYFA_BOYU)
    return render(request, "medya/yazar.html", {
        "yazar": kayit,
        "baslik": kayit.ad,
        "sayfa": sayfa,
    })


def kose_yazisi(request, dilim_slug, dilim_id, slug, kimlik):
    kayit = (KoseYazisi.yayindakiler()
             .select_related("yazar", "kategori")
             .prefetch_related("kategori__turler")
             .filter(pk=kimlik).first())
    if kayit is None:
        raise Http404("Köşe yazısı yok")

    yonlendirme = _kanoniklestir(request, kayit)
    if yonlendirme is not None:
        return yonlendirme

    return render(request, "medya/kose_yazisi.html", {
        "yazi": kayit,
        "yazar": kayit.yazar,
        "baslik": kayit.baslik,
        # Aynı yazarın diğer yazıları; kendisi hariç.
        "digerleri": kayit.yazar.yazilari().exclude(pk=kayit.pk)[:5],
    })


def yazar_listesi(request):
    """`/yazarlar` — yazar dizini.

    Veri gelmeden de çalışır: boş liste şablonda "henüz göç etmedi" olarak
    karşılanıyor, böylece kök adres tablosunda bekleme sayfasıyla yer
    değiştirmek tek satırlık bir iş.
    """
    yazarlar = list(Yazar.listedekiler())
    return render(request, "medya/yazar_listesi.html", {
        "baslik": "Yazarlar",
        "yazarlar": yazarlar,
    })


# -- foto galeri ------------------------------------------------------------

def foto_galeri(request, dilim_slug, dilim_id, slug, kimlik):
    kayit = (FotoGaleri.yayindakiler()
             .select_related("kategori")
             .prefetch_related("kategori__turler", "kareler")
             .filter(pk=kimlik).first())
    if kayit is None:
        return _dilim_bekleyen("galeriler", Kategori.TUR_FOTO,
                               dilim_slug, dilim_id, slug, kimlik)

    yonlendirme = _kanoniklestir(request, kayit)
    if yonlendirme is not None:
        return yonlendirme

    return render(request, "medya/galeri.html", {
        "galeri": kayit,
        "baslik": kayit.baslik,
        "kareler": kayit.kareler.all(),
        "digerleri": _yakin(FotoGaleri, kayit),
    })


def galeri_listesi(request):
    sayfa = _sayfala(request, FotoGaleri.yayindakiler()
                     .select_related("kategori")
                     .prefetch_related("kategori__turler"))
    return render(request, "medya/galeri_listesi.html", {
        "baslik": "Foto galeri",
        "sayfa": sayfa,
    })


# -- video ------------------------------------------------------------------

def video(request, dilim_slug, dilim_id, slug, kimlik):
    kayit = (Video.yayindakiler()
             .select_related("kategori")
             .prefetch_related("kategori__turler")
             .filter(pk=kimlik).first())
    if kayit is None:
        return _dilim_bekleyen("videolar", Kategori.TUR_VIDEO,
                               dilim_slug, dilim_id, slug, kimlik)

    yonlendirme = _kanoniklestir(request, kayit)
    if yonlendirme is not None:
        return yonlendirme

    return render(request, "medya/video.html", {
        "video": kayit,
        "baslik": kayit.baslik,
        "digerleri": _yakin(Video, kayit),
    })


def video_listesi(request):
    sayfa = _sayfala(request, Video.yayindakiler()
                     .select_related("kategori")
                     .prefetch_related("kategori__turler"))
    return render(request, "medya/video_listesi.html", {
        "baslik": "Videolar",
        "sayfa": sayfa,
    })


def _yakin(model, kayit, adet=4):
    """Aynı kategoriden, kendisi hariç en yeniler.

    Kategorisi olmayan kayıtlarda (ölçüldü: `haber-213` dilimi) kategori
    süzgeci tüm kategorisizleri toplardı; o yüzden süzgeç ham adres dilimine
    düşüyor — kaydın gerçekten ait olduğu şey odur.
    """
    sorgu = (model.yayindakiler()
             .select_related("kategori")
             .prefetch_related("kategori__turler")
             .exclude(pk=kayit.pk))
    if kayit.kategori_id:
        sorgu = sorgu.filter(kategori_id=kayit.kategori_id)
    else:
        sorgu = sorgu.filter(kategori_dilimi=kayit.kategori_dilimi)
    return sorgu[:adet]
