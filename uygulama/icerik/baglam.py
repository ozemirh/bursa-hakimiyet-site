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

from django.conf import settings
from django.db import DatabaseError
from django.db.models import Count

from taksonomi.models import Ilce, Kategori

from .models import Haber

# "İLÇELER" bandı DİZİNE değil doğrudan bir ilçeye gider (2 Eylül 2026,
# kullanıcı isteği: "ilçelere tıklanınca default olarak osmangaziye yolla").
# Gerekçe: dizin sayfası okuru bir tıklama daha uzağa koyuyordu; ilçe sayfası
# §46'dan beri 17 ilçenin hepsini taşıyan hızlı geçiş şeridini çiziyor, yani
# dizinin işini de görüyor. Osmangazi Bursa'nın merkez ilçesi.
#
# Dizin sayfası KALDIRILMADI: tam menüdeki "Tüm ilçeler" ve anasayfadaki
# "BURSA İLÇELERİ" kutusu oraya gitmeye devam ediyor, adres arama motorunda
# kayıtlı.
VARSAYILAN_ILCE = "osmangazi"

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
    ("İLÇELER", None, f"/ilce/{VARSAYILAN_ILCE}"),
    ("RESMÎ İLAN", None, "/resmi-ilan"),
]

# Dar ekranda banda SIĞAN dört kalem (29 Ağustos 2026 kararı). Onlu bant
# 1000 px altında satıra sığmıyordu ve eskiden tamamen gizleniyordu —
# ölçüldü: 360 px'te görünen kategori sayısı SIFIR. Yerel gazete okuru
# "Bursa"ya tek dokunuşla gidemiyordu.
#
# Bant sözleşmesi (10 kalem) BOZULMADI: onu da DOM'da duruyor, dördü
# dışındakileri CSS gizliyor ve hepsi tam menüde zaten var. Seçim DOM
# sırasının ilk dördü değil, okurun ilk aradığı dört bölüm.
MOBIL_BANT = {"BURSA", "BURSASPOR", "GÜNDEM", "SPOR"}

# 4 -> 6 (30 Ağustos 2026, §36): kayan şerit dört başlığı sırayla
# gösteriyordu, rayda sabit liste altısını da AYNI ANDA gösteriyor —
# yerine sığıyor ve okur birini kaçırmıyor.
#
# 6 -> 7 (2 Eylül 2026, §44): en yeni kalem listeden çıkıp panelin
# ŞERİDİNE taşındı. Listede altı kalem kalsın diye bir artırıldı —
# anasayfanın iki sütunlu yerleşiminde altı kalem üç TAM satır yapıyor,
# beş kalem son satırı yarım bırakıyordu.
SON_DAKIKA_ADET = 7


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
        # Bandın "İLÇELER" kalemi Osmangazi'ye gidiyor ama HER ilçe
        # sayfasında etkin görünmeli — okur Nilüfer'deyken bandın hangi
        # kalemi altında olduğunu göremezdi.
        etkin = yol == hedef or (hedef.startswith("/ilce/")
                                 and yol.startswith("/ilce/"))
        bant.append({"ad": ad, "yol": hedef, "etkin": etkin,
                     "mobil": ad in MOBIL_BANT, "mobil_son": False})

    # Dar ekrandaki DÖRTLÜNÜN sonuncusu işaretlenir: ayraç çizgisi onda
    # kalkacak. CSS `:last-of-type` burada yanlış kalemi seçerdi — DOM'un
    # son bağlantısı "Resmî İlan" ve o dar ekranda gizli.
    for oge in reversed(bant):
        if oge["mobil"]:
            oge["mobil_son"] = True
            break

    return {
        "band_kategorileri": bant,
        "tum_kategoriler": _tum_kategoriler(),
        "kunye_arsiv": _kunye_arsiv(),
        "son_dakika": Haber.yayindakiler().select_related("kategori")[:SON_DAKIKA_ADET],
        "ilceler": Ilce.objects.all(),
        "reklam_dugmesi": sunum_araci_mi(request),
        # Reklam demo agi. Bayrak kapaliyken taban.html hicbir dis betik
        # basmaz; yuvalar gri yer tutucu olarak kalir.
        "reklam_demo": settings.REKLAM_DEMO,
        "reklam_yolu": settings.REKLAM_DEMO_YOLU,
        # Yerel test reklam hizmeti (7 Eylul 2026). Dis ag DEGIL: yaratici
        # sunucuda uretilir, istenen olcude ve internetsiz. Yalniz sunum
        # oturumunda cizilir; siradan ziyaretci ne dugmeyi ne betigi gorur.
        "reklam_test": settings.REKLAM_TEST and sunum_araci_mi(request),
        # AdSense — gazetenin kendi yayinci kimligi. TEST MODUNDA yalniz
        # sunum oturumuna cizilir: test yaraticisi okura gosterilecek sey
        # degil. Test kapatildiginda (gercek yayin) herkese cizilir.
        "adsense_ayar": _adsense_ayar(request),
    }


def _adsense_ayar(request):
    """`<ins>` kurmak icin gereken her sey ya da None.

    Kimlik verilmediyse None doner ve taban.html hicbir dis betik basmaz;
    site disaridan yalniz Google Fonts ceker.
    """
    if not settings.ADSENSE_ID:
        return None
    if settings.ADSENSE_TEST and not sunum_araci_mi(request):
        return None
    return {
        "kimlik": settings.ADSENSE_ID,
        "test": settings.ADSENSE_TEST,
        "varsayilan": settings.ADSENSE_SLOT,
        "yuvalar": settings.ADSENSE_YUVALAR,
    }


# Reklam panolarını gizleyen düğme SUNUM ARACIDIR, okur özelliği değil
# (29 Ağustos 2026 kararı). Yayın ekibine sayfayı reklamsız gösterebilmek
# için var; sıradan ziyaretçiye çizilmez, çünkü reklam gizleme düğmesi
# gelir modeline dokunur.
#
# İki kapı: geliştirme makinesi ya da panele girmiş kullanıcı. `is_staff`
# değil `is_authenticated` de yeterli olurdu ama panelin kendi eşiği
# `is_staff`; ikisini ayrı tutmanın bir karşılığı yok.
YEREL_SUNUCULAR = {"127.0.0.1", "localhost", "[::1]"}


def sunum_araci_mi(request):
    kullanici = getattr(request, "user", None)
    if kullanici is not None and kullanici.is_authenticated and kullanici.is_staff:
        return True
    return request.get_host().split(":")[0] in YEREL_SUNUCULAR


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


# Künyedeki arşiv kapsamı cümlesi — "2012'den bugüne N haber".
#
# Şablona ÇAKILI YAZILMAZ. Aynı hata bir kez yapıldı: anasayfanın not
# satırlarında "1484 video" yazarken veritabanında 31.084 vardı (27 Ağustos
# ölçümü, `views.arsiv_sayilari`). Künye sitenin okura verdiği beyandır;
# sayı veriden gelmeli.
#
# Bu bağlam işlemcisi HER sayfada çalışıyor, o yüzden sayım kısa süre
# önbellekleniyor. `views.arsiv_sayilari`den bir farkı var: hata durumu da
# önbelleğe yazılıyor. Orada yazılmıyor ve göç sürerken her istek kilide
# yeniden girip beş saniye bekliyordu; künye satırı sayfayı bekletmeye
# değmez, sayılamadığında cümle hiç basılmaz.
KUNYE_BELLEK_SANIYE = 300
_kunye_bellek: tuple[float, dict | None] | None = None


def _kunye_arsiv() -> dict | None:
    """Künyedeki arşiv kapsamı. Sayılamazsa `None` — şablon cümleyi basmaz."""
    global _kunye_bellek
    simdi = time.monotonic()
    if _kunye_bellek and simdi - _kunye_bellek[0] < KUNYE_BELLEK_SANIYE:
        return _kunye_bellek[1]
    try:
        # SÜZGEÇSİZ sayılıyor ve cümle de "arşivde" diyor — ölçüm gerekçesi
        # (3 Eylül 2026, 1.038.474 satır):
        #
        #     durum=1 AND yayin_zamani IS NOT NULL   2.202 ms  (TAM TARAMA)
        #     süzgeçsiz COUNT(*)                        11 ms  (kapsayan indeks)
        #
        # `IS NOT NULL` hiçbir B-ağacı indeksiyle karşılanamıyor, o yüzden
        # `yayindakiler()` sayımı tabloyu baştan sona tarıyor. Bu bağlam
        # işlemcisi HER sayfada çalışıyor; künyedeki bir cümle için soğuk
        # isteğe 2,2 saniye eklemek `_tum_kategoriler`in düştüğü tuzağın
        # aynısı olurdu. Sayı arşivin büyüklüğünü söylüyor, "hepsi
        # listelenebilir" demiyor — cümle de öyle kuruldu.
        adet = Haber.objects.count()
        ilk = (Haber.yayindakiler().order_by("yayin_zamani")
               .values_list("yayin_zamani", flat=True).first())
    except DatabaseError:
        _kunye_bellek = (simdi, _kunye_bellek[1] if _kunye_bellek else None)
        return _kunye_bellek[1]
    # Binlik ayraci burada kuruluyor: `intcomma` virgul koyar, Turkce
    # ayrac noktadir ve panelde de ayni donusum yapiliyor.
    deger = ({"adet": f"{adet:,}".replace(",", "."),
              "ilk_yil": ilk.year if ilk else None} if adet else None)
    _kunye_bellek = (simdi, deger)
    return deger
