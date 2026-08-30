"""Görünümler — çözümleme ve kanonik yönlendirme.

Canlı sitenin davranışı ölçüldü: adres **kimlikle** çözülüyor, slug yok
sayılıyor, ve kanonik adrese yönlendiriliyor. `/spor/yanlis-slug-526347`
→ 200, kanonike gidiyor. Yeni sistem aynısını yapar.

F2'de içerik modelleri henüz yok, o yüzden:

- **Galeri ve video** için kategori dilimi (`{slug}-{katid}`) taksonomiden
  doğrulanabiliyor → kanonik yönlendirme burada **tam çalışıyor**.
- **Haber** için kanonik adres, haberin kendi slug'ına ve kategorisine bağlı;
  ikisi de içerik modelinde (F3). Şimdilik yalnız **kategori slug sapması**
  yakalanıyor (`bursada-spor` → `bursa-da-spor`). Tam kanonik yönlendirme
  F3'te kapanır.
"""

from django.http import Http404, JsonResponse
from django.shortcuts import redirect, render

from icerik.models import Haber

from .models import Kategori, KategoriTur, Yonlendirme


def _yanit(tur: str, kimlik, **ek) -> JsonResponse:
    return JsonResponse({"tur": tur, "kimlik": int(kimlik), **ek})


def _kanonik_dilim(tur: str, dilim_slug: str, dilim_id: str):
    """Kategori dilimini kimlikten doğrular.

    (kanonik_slug, uyusuyor_mu) döndürür. Kimlik bilinmiyorsa (None, False).
    """
    satir = KategoriTur.objects.filter(tur=tur, eski_id=int(dilim_id)).first()
    if satir is None:
        return None, False
    return satir.slug, satir.slug == dilim_slug


def haber(request, kategori, slug, kimlik):
    """Haber detayı. **Çözüm kimlikle yapılır**, slug yok sayılır.

    Canlı sitenin ölçülmüş davranışı: `/spor/yanlis-slug-526347` çalışıyor
    ve kanonik adrese yönlendiriyor. F3'te içerik modeli geldiği için artık
    kanonik adres haberin kendi kategori ve slug'ından kuruluyor; F2'deki
    "yalnız kategori sapması" sınırı kalktı.
    """
    # Bilinen bir slug sapmasi mi? (orn. bursada-spor -> bursa-da-spor)
    kayit = Yonlendirme.objects.filter(eski_yol=f"/{kategori}/").first()
    if kayit is not None:
        hedef = f"{kayit.yeni_yol.rstrip('/')}/{slug}-{kimlik}"
        return redirect(hedef, permanent=kayit.kod == 301)

    # Kategori slug'i hic taninmiyorsa adres gecerli degil.
    if not KategoriTur.objects.filter(tur=Kategori.TUR_HABER, slug=kategori).exists():
        raise Http404("Bilinmeyen kategori slug'ı")

    kayit = (Haber.yayindakiler()
             .select_related("kategori", "ilce")
             .prefetch_related("kategori__turler", "kaynaklar")
             .filter(pk=kimlik).first())
    if kayit is None:
        raise Http404("Haber yok")

    kanonik = kayit.get_absolute_url()
    if request.path.rstrip("/") != kanonik:
        return redirect(kanonik, permanent=True)

    return render(request, "haber_detay.html", {
        "haber": kayit,
        "baslik": kayit.baslik,
        "ilgili": _ilgili(kayit),
        # Sağ ray (29 Ağustos görsel denetimi): `.izgara` iki sütun ayırıyor
        # ama şablon tekini dolduruyordu — her makale sayfasında 342 px ölü
        # sütun (ölçüldü). Ray anasayfanın bileşenlerini yeniden kullanır.
        "en_cok": _en_cok(kayit),
        "ilcedekiler": _ilcedekiler(kayit),
    })


def _ilgili(kayit):
    """Aynı kategoriden, kendisi hariç en yeni haberler."""
    return (Haber.yayindakiler()
            .select_related("kategori")
            .prefetch_related("kategori__turler")
            .filter(kategori=kayit.kategori)
            .exclude(pk=kayit.pk)[:5])


def _en_cok(kayit):
    """Raydaki liste. Okunma sayacı dolana kadar anasayfayla aynı kural:
    editör seçkisi gibi davranan en yeniler (URUN-PLANI.md §4, madde 8)."""
    return (Haber.yayindakiler()
            .select_related("kategori")
            .prefetch_related("kategori__turler")
            .exclude(pk=kayit.pk)[:5])


def _ilcedekiler(kayit):
    """Aynı ilçeden son haberler; ilçesiz kayıtta bölüm hiç çizilmez."""
    if not kayit.ilce_id:
        return []
    return (Haber.yayindakiler()
            .select_related("kategori")
            .prefetch_related("kategori__turler")
            .filter(ilce=kayit.ilce)
            .exclude(pk=kayit.pk)[:4])


def _dilimli(request, tur, ad, dilim_slug, dilim_id, slug, kimlik):
    kanonik, uyuyor = _kanonik_dilim(tur, dilim_slug, dilim_id)
    if kanonik is None:
        raise Http404("Bilinmeyen kategori kimliği")
    if not uyuyor:
        kok = "galeriler" if tur == Kategori.TUR_FOTO else "videolar"
        return redirect(f"/{kok}/{kanonik}-{dilim_id}/{slug}-{kimlik}", permanent=True)
    return _yanit(ad, kimlik, kategori_slug=dilim_slug,
                  kategori_id=int(dilim_id), slug=slug)


def foto_galeri(request, dilim_slug, dilim_id, slug, kimlik):
    return _dilimli(request, Kategori.TUR_FOTO, "galeri",
                    dilim_slug, dilim_id, slug, kimlik)


def video(request, dilim_slug, dilim_id, slug, kimlik):
    return _dilimli(request, Kategori.TUR_VIDEO, "video",
                    dilim_slug, dilim_id, slug, kimlik)


def kose_yazisi(request, dilim_slug, dilim_id, slug, kimlik):
    # Yazar dilimi icerik tarafinda (F3); burada yalnizca cozumleme.
    return _yanit("kose", kimlik, yazar_slug=dilim_slug,
                  yazar_id=int(dilim_id), slug=slug)


def yazar(request, dilim_slug, dilim_id):
    return _yanit("yazar", dilim_id, yazar_slug=dilim_slug)
