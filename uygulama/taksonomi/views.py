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

from django.db.models import Exists, OuterRef
from django.http import Http404, JsonResponse
from django.shortcuts import redirect, render

from cekirdek.adres_duzeni import kalici

from icerik import ilgili as ilgili_yardimci
from icerik import konu as konu_yardimci
from icerik import okunma
from icerik.models import Duzeltme, Haber
from icerik.sayfa_onbellegi import sayfa_onbellegi

from . import slug_eslemesi
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


@sayfa_onbellegi
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
        if kayit.kod == 301:
            return kalici(request, hedef)
        return redirect(hedef, permanent=False)

    # Kategori slug'i hic taninmiyorsa adres gecerli degil. Surec ici
    # eslemeden bakiliyor (taksonomi/slug_eslemesi.py): istek basina bir
    # KategoriTur sorgusu daha az. Eslemede yoksa veritabanina sorulur —
    # baska bir surecte az once acilmis kategori eslemeye en gec
    # `slug_eslemesi.OMUR` sonra girer, o arada adres 404 vermemeli.
    if not (slug_eslemesi.slug_var_mi(kategori, Kategori.TUR_HABER)
            or KategoriTur.objects.filter(tur=Kategori.TUR_HABER, slug=kategori).exists()):
        raise Http404("Bilinmeyen kategori slug'ı")

    # `kategori__turler` ön çekimi kalktı: slug süreç içi eşlemeden geliyor
    # (taksonomi/slug_eslemesi.py), sayfa başına bir sorgu daha az.
    # `duzeltme_var` (20 Ekim 2026): düzeltme notu var mı — aynı
    # sorguda EXISTS. Arşivin hemen tamamında not yok; o haberlerde sayfa
    # tek sorgu bile fazla açmaz (`Duzeltme.haber_icin`).
    kayit = (Haber.yayindakiler()
             .select_related("kategori", "ilce")
             .prefetch_related("kaynaklar", "etiketler")
             .annotate(duzeltme_var=Exists(
                 Duzeltme.yayindakiler().filter(haber_id=OuterRef("pk"))))
             .filter(pk=kimlik).first())
    if kayit is None:
        raise Http404("Haber yok")

    kanonik = kayit.get_absolute_url()
    if request.path.rstrip("/") != kanonik:
        # Sorgu dizesi (utm) korunur — Paket G.
        return kalici(request, kanonik)

    # Konu akışı önce: ilgili haberler kutusu akışta zaten görünenleri
    # atlar, aynı başlık sayfada iki kez basılmaz (5 Eylül 2026).
    akis = konu_yardimci.akis(kayit)
    # Düzeltme notları: gövdenin sonundaki blok, başlık altındaki
    # işaret ve JSON-LD `correction` aynı listeden okur (`seo.haber_makalesi`).
    kayit.yayindaki_duzeltmeler = Duzeltme.haber_icin(kayit)
    yanit = render(request, "haber_detay.html", {
        "duzeltmeler": kayit.yayindaki_duzeltmeler,
        "duzeltme_isareti": Duzeltme.isaret_metni(kayit.yayindaki_duzeltmeler),
        "haber": kayit,
        "baslik": kayit.baslik,
        "ilgili": _ilgili(kayit, akis),
        # Sağ ray (29 Ağustos görsel denetimi): `.izgara` iki sütun ayırıyor
        # ama şablon tekini dolduruyordu — her makale sayfasında 342 px ölü
        # sütun (ölçüldü). Ray anasayfanın bileşenlerini yeniden kullanır.
        "en_cok": _en_cok(kayit),
        "ilcedekiler": _ilcedekiler(kayit),
        # Konu dosyası akışı; haber onaylı bir dosyada değilse None ve
        # şablon bloğu hiç çizmez (5 Eylül 2026).
        "konu_akisi": akis,
    })
    # Okunma sayacı. Kanonik denetimden SONRA: yönlendirilen istek sayılsaydı
    # aynı okuma iki kez sayılırdı (301 + hedef). Sayımı görünüm değil sayfa
    # önbelleği katmanı yapar (icerik/sayfa_onbellegi.py): önbellekten
    # servis edilen okuma da böylece sayılır. Yazma tamponludur ve hatası
    # sayfaya yansımaz (icerik/okunma.py).
    yanit.okunma_haber = kayit.pk
    return yanit


ILGILI_ADET = 6   # iki sütunlu ızgara; 5'te son satır tek kalıyordu


def _ilgili(kayit, akis=None):
    """İlgili haberler kutusu: önce EDİTÖRÜN SEÇTİKLERİ, sonra otomatik.

    Paket H (19 Ekim 2026): panelin "İlgili haberler" alanı (§4 alan 28)
    sitede okunmuyordu. Editörün seçtiği haberler yayındaysa seçim
    sırasıyla (ara tablonun satır sırası; ayrı sıra alanı yok) önde gelir;
    kutu `ILGILI_ADET`e kadar başlık benzerliğiyle (icerik/ilgili.py)
    tamamlanır. Konu akışında zaten görünenler iki listeden de çıkar.
    """
    haric = []
    if akis:
        haric = [h.pk for h in akis["oncekiler"]] + [h.pk for h in akis["sonrakiler"]]
    # Seçim sırası ara tablonun satır sırasıdır. Seçim yoksa (arşivin
    # tamamı) tek, ucuz bir sorgu: `from_haber_id` ara tabloda indeksli.
    sira = [k for k in Haber.ilgili_haberler.through.objects
            .filter(from_haber_id=kayit.pk).order_by("id")
            .values_list("to_haber_id", flat=True)
            if k not in haric and k != kayit.pk]
    secilen = []
    if sira:
        bulunan = {h.pk: h for h in Haber.yayindakiler()
                   .select_related("kategori", "ilce").filter(pk__in=sira)}
        secilen = [bulunan[k] for k in sira if k in bulunan][:ILGILI_ADET]
    if len(secilen) >= ILGILI_ADET:
        return secilen
    otomatik = ilgili_yardimci.bul(kayit, adet=ILGILI_ADET - len(secilen),
                                   haric=haric + [h.pk for h in secilen])
    return secilen + otomatik


EN_COK = 5


def _en_cok(kayit):
    """Raydaki liste — pencerede en çok okunan haberler.

    Sayaç yeterli veriyi toplayana kadar (bkz. `okunma.ESIK_OKUNMA`) liste
    eski kuralına döner: editör seçkisi gibi davranan en yeniler
    (URUN-PLANI.md §4, madde 8). Anasayfa ve bölüm şeridi de aynı kapıdan
    beslenir, üçü aynı anda gerçek veriye geçer.
    """
    sorgu = (Haber.yayindakiler()
             .select_related("kategori")
             .exclude(pk=kayit.pk))
    # Okunan haberin kendisi rayında durmaz: eleme `haric` ile SIRALAMA
    # tarafında yapılıyor, yoksa beşinci sıra kendisi olduğunda liste
    # dörde düşüp geri düşüşe geçerdi.
    okunanlar = okunma.en_cok(sorgu, EN_COK, haric=[kayit.pk])
    return okunanlar or sorgu[:EN_COK]


def _ilcedekiler(kayit):
    """Aynı ilçeden son haberler; ilçesiz kayıtta bölüm hiç çizilmez."""
    if not kayit.ilce_id:
        return []
    return (Haber.yayindakiler()
            .select_related("kategori")
            .filter(ilce_id=kayit.ilce_id)
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
