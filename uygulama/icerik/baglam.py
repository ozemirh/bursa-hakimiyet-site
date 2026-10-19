"""Her sayfada duran ortak bağlam: kategori bandı, son dakika, ilçeler.

Bunlar `taban.html` içindeki parçalarda kullanıldığı için her görünümde
tek tek verilmez; bağlam işlemcisiyle bir kez hazırlanır.

**Kategori bandı 10 kalemdir ve sırası bağlayıcıdır** (URUN-PLANI.md §1,
bileşen 3). Liste veritabanındaki 13 kategoriden türetilmez — banda girmeyen
kategoriler (Sağlık, Teknoloji, Yaşam…) tam menüde durur. Bandın iki kalemi
kategori değildir: "Yazarlar" ve "İlçeler" kendi bölümlerine, "Resmî İlan"
ise BİK yükümlülüğü olan editoryal bölüme gider.
"""

from django.conf import settings
from django.db import DatabaseError
from django.db.models import Count

from taksonomi.models import Ilce, Kategori

from . import onbellek
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


class BantKalemi:
    """Bandın tek satırı — kaynağı `SonDakika` kaydı ya da haber olabilir.

    Şablon yalnız bu üç alanı okur; iki kaynağın alan adları farklı
    (`baslangic` / `yayin_zamani`, `yol` / `get_absolute_url`).
    """

    def __init__(self, baslik, yol, zaman):
        self.baslik, self.yol, self.zaman = baslik, yol, zaman


def guvenli_bant_adresi(adres: str) -> bool:
    """Serbest adres yalnız site içi yol (`/…`, `//` değil) ya da http(s).

    `SonDakika.adres` serbest metin; `javascript:` gibi bir şema bağlantıya
    basılırsa okurun tarayıcısında çalışırdı. Form da aynı kuralla reddeder
    (`formlar.SonDakikaForm.clean_adres`); burası eski kayda karşı ikinci kat.
    """
    adres = (adres or "").strip()
    if adres.startswith("/"):
        return not adres.startswith("//")
    return adres.lower().startswith(("https://", "http://"))


class SonDakikaBandi:
    """Bandın kalemleri — TEMBEL: sorgu ancak şablon bandı çizerken açılır.

    Bağlam işlemcisi HER sayfada çalışır ama bant yalnız ray taşıyan
    sayfalarda (anasayfa, haber detay, köşe yazısı) çizilir; eskiden de
    tembel bir QuerySet'ti. Liste gibi davranır (`son_dakika.0`, döngü,
    `|slice`), ayrıca `etiket` ve `canli` taşır.
    """

    def __init__(self):
        self._deger = None

    def _kur(self):
        if self._deger is None:
            self._deger = _son_dakika_kur()
        return self._deger

    @property
    def kalemler(self) -> list:
        return self._kur()[0]

    @property
    def etiket(self) -> str:
        return self._kur()[1]

    @property
    def canli(self) -> bool:
        return self._kur()[2]

    def __iter__(self):
        return iter(self.kalemler)

    def __len__(self):
        return len(self.kalemler)

    def __bool__(self):
        return bool(self.kalemler)

    def __getitem__(self, i):
        return self.kalemler[i]


def son_dakika_bandi() -> SonDakikaBandi:
    return SonDakikaBandi()


#: Masanın son dakika kayıtları kısa süre önbellekte durur (Paket H).
#: Kayıt (ya da bağlı haber) kaydedilince anahtar ANINDA silinir
#: (`sinyaller.py`); süre yalnız ZAMANLA değişen şeyler için — başlangıcı
#: gelen / bitişi geçen kayıt en geç bu kadar sonra görünür. Sayfa mikro
#: önbelleğiyle aynı süre (§21: "beş dakika eski manşet kabul edilemez").
#: Gerekçe ölçüm: tablo okunmaya başlayınca ray taşıyan her sayfa (haber
#: detay, köşe yazısı) bir sorgu daha açıyordu; tablo çoğu zaman BOŞ.
SON_DAKIKA_ANAHTARI = "bh:son-dakika-kayitlari:v1"
SON_DAKIKA_TAZE_SANIYE = 30


def _masa_kalemleri() -> list:
    return onbellek.hesapla(SON_DAKIKA_ANAHTARI, _masa_kalemleri_kur,
                            taze=SON_DAKIKA_TAZE_SANIYE, bayat=SON_DAKIKA_TAZE_SANIYE,
                            hata=5, yedek=list)


def _masa_kalemleri_kur() -> list:
    from .models import SonDakika
    kalemler = []
    for kayit in (SonDakika.bandakiler()
                  .select_related("haber")[:SON_DAKIKA_ADET * 2]):
        if not kayit.adres and kayit.haber_id and not kayit.haber.yayinda_mi():
            continue
        yol = kayit.yol
        if not guvenli_bant_adresi(yol):
            continue
        kalemler.append(BantKalemi(kayit.baslik, yol, kayit.baslangic))
        if len(kalemler) == SON_DAKIKA_ADET:
            break
    return kalemler


def _son_dakika_kur() -> tuple:
    """Bandın kalemleri ve etiketi (19 Ekim 2026, Paket H).

    Önceden bant `SonDakika` tablosunu HİÇ okumuyordu, en yeni yedi haberi
    "SON DAKİKA" diye basıyordu (DEGERLENDIRME-2026-10 §3 bulgu 5). Şimdi:

    1. Masanın kayıtları (`SonDakika.bandakiler`: etkin, başlamış, süresi
       dolmamış), sıra alanı ve başlangıçla. Bağlı haber yayından
       çekildiyse ve serbest adres yoksa satır düşer — okur 404'e
       gönderilmez. Etiket **SON DAKİKA**, "CANLI" pili yanar.
    2. Tablo boşsa son haberler — ama etiket **SON HABERLER** ve pil
       yok: masanın vermediği "son dakika" kararını site vermez.
       Nöbetçi eczane servis haberi (§41) bu listeye GİRMEZ; günlük
       otomatik kayıt bant için gürültü. Python'da elenir: `slug LIKE`
       koşulu SQLite'ta indeks sırasını bozabiliyor (sayımı 2,7 sn
       ölçüldü); servis haberi günde bir tane, iki fazla satır yeter.
    """
    from .anasayfa_dizilimi import servis_haberi_mi

    kalemler = _masa_kalemleri()
    if kalemler:
        return kalemler, "SON DAKİKA", True

    # Adres slug'ı süreç içi eşlemeden (`slug_eslemesi`): kategori
    # birleştirmesine gerek yok.
    haberler = [h for h in Haber.yayindakiler()[:SON_DAKIKA_ADET + 2]
                if not servis_haberi_mi(h)]
    return ([BantKalemi(h.baslik, h.get_absolute_url(), h.yayin_zamani)
             for h in haberler[:SON_DAKIKA_ADET]], "SON HABERLER", False)


def site(request):
    yol = request.path

    # Bant da menüyle AYNI önbellekli özetten kuruluyor: eskiden her sayfa
    # bunun için iki sorgu (kategori + tür satırları) açıyordu.
    kategoriler = {k["ad"]: k["slug"] for k in _kategori_ozeti()}

    bant = []
    for ad, kategori_adi, sabit_yol in BANT:
        if sabit_yol:
            hedef = sabit_yol
        else:
            if kategori_adi not in kategoriler:
                continue  # taksonomi kurulmadıysa bandı kırma
            hedef = "/" + kategoriler[kategori_adi]
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
        # Son dakika: önce masanın `SonDakika` kayıtları, yoksa son
        # haberler. Tembel: yalnız bandı çizen sayfa sorgu açar. Masanın
        # kayıtları 30 sn önbellekte, kayıt değişince anında düşer (§21).
        "son_dakika": son_dakika_bandi(),
        "ilceler": _ilceler(),
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


# Menü sıralaması ÖNBELLEKLENİR — paylaşılan önbellekte, kilitli.
#
# Ölçüm (27 Ağustos 2026, 308.602 haber): `annotate(Count("haberler"))`
# tek başına **1.113 ms** sürüyordu ve bu bağlam işlemcisi **her sayfada**
# çalıştığı için sitenin tamamı bu bedeli ödüyordu.
#
# 19 Ekim 2026, 1.038.477 haber: aynı sorgu SOĞUK süreçte 3,4–45 sn
# (sayfaya göre; disk önbelleğine bağlı) ve kopya veritabanında 112 sn.
# Kök neden süreden fazlası: `COUNT("icerik_haber"."id")` birleşmeli
# biçimde her haber satırına TABLODAN gidiyordu, çünkü `id` sütunu
# `bigint PRIMARY KEY` ve SQLite'ta rowid takma adı değil — indeks onu
# taşımıyor. Aynı sayım `GROUP BY kategori_id` + `COUNT(*)` ile kapsayan
# indeksten çıkıyor: **313 ms**, tabloya hiç gitmeden.
#
# `adet` **ekranda hiç gösterilmiyor**; yalnız menüyü çok haberliden aza
# sıralamak için var (künye ilk altıyı basıyor). Sıralama günler içinde
# değişmez: 6 saat taze, bir hafta bayat servis edilir; yeniden hesabı
# kilidi alan tek istek yapar, ötekiler beklemez.
MENU_ANAHTARI = "bh:kategori-ozeti:v1"
MENU_TAZE_SANIYE = 6 * 3600
MENU_BAYAT_SANIYE = 7 * 86400


def _kategori_ozeti_hesapla(sayimli: bool = True) -> list[dict]:
    kategoriler = list(Kategori.objects.filter(aktif=True)
                       .prefetch_related("turler").order_by("sira", "ad"))
    adetler = {}
    if sayimli:
        adetler = dict(Haber.objects.order_by().values_list("kategori_id")
                       .annotate(n=Count("*")).values_list("kategori_id", "n"))
    ozet = [{"ad": k.ad, "slug": k.slug_al(), "adet": adetler.get(k.pk, 0)}
            for k in kategoriler]
    # `sorted` kararlı: eşit sayıda `sira` düzeni korunur.
    return sorted(ozet, key=lambda o: -o["adet"])


def _sayimsiz_ozet() -> list[dict]:
    """Önbellek boş ve hesap başka süreçteyken: sayımsız, `sira` düzeni.
    Kilitli veritabanında bu da düşerse boş liste — sayfa ayakta kalır."""
    try:
        return _kategori_ozeti_hesapla(sayimli=False)
    except DatabaseError:
        return []


def _kategori_ozeti() -> list[dict]:
    """Etkin kategoriler: ad, haber slug'ı, haber sayısı; çoktan aza."""
    return onbellek.hesapla(MENU_ANAHTARI, _kategori_ozeti_hesapla,
                            taze=MENU_TAZE_SANIYE, bayat=MENU_BAYAT_SANIYE,
                            hata=20, yedek=_sayimsiz_ozet)


def _tum_kategoriler():
    """Tam menüdeki liste: haber taşıyan kategoriler, çok haberliden aza.

    Sayım kilide takılırsa son bilinen liste döner, o da yoksa
    **sayımsız** sıralamaya düşülür — menü her hâlükârda çizilmeli, sayfa
    bir sıralama yüzünden düşmemeli.
    """
    return [{"ad": o["ad"], "slug": o["slug"], "adet": o["adet"]}
            for o in _kategori_ozeti() if o["slug"]]


ILCE_ANAHTARI = "bh:ilceler:v1"


def _ilceler() -> list:
    """17 ilçe; her sayfanın menüsünde ve künyesinde. Kayıt değişince
    `icerik/sinyaller.py` anahtarı siler."""
    return onbellek.hesapla(ILCE_ANAHTARI, lambda: list(Ilce.objects.all()),
                            taze=3600, hata=20, yedek=list)


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
KUNYE_ANAHTARI = "bh:kunye-arsiv:v1"


def _kunye_arsiv() -> dict | None:
    """Künyedeki arşiv kapsamı. Sayılamazsa `None` — şablon cümleyi basmaz.

    Hata da tam süreyle önbelleğe yazılır (`hata=KUNYE_BELLEK_SANIYE`):
    künye satırı sayfayı kilit beklemesine sokmaya değmez.
    """
    return onbellek.hesapla(KUNYE_ANAHTARI, _kunye_hesapla,
                            taze=KUNYE_BELLEK_SANIYE, hata=KUNYE_BELLEK_SANIYE,
                            yedek=None)


def _kunye_hesapla() -> dict | None:
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
    #
    # 19 Ekim 2026: 0015'teki `haber_okur_kismi` kısmi indeksi o sayımı
    # da kapsayan indeksten veriyor (kopyada 117 ms). Cümle "arşivde"
    # dediği için süzgeçsiz sayım KORUNDU; değiştirmek editoryal karardır.
    adet = Haber.objects.count()
    ilk = (Haber.yayindakiler().order_by("yayin_zamani")
           .values_list("yayin_zamani", flat=True).first())
    # Binlik ayraci burada kuruluyor: `intcomma` virgul koyar, Turkce
    # ayrac noktadir ve panelde de ayni donusum yapiliyor.
    deger = ({"adet": f"{adet:,}".replace(",", "."),
              "ilk_yil": ilk.year if ilk else None} if adet else None)
    return deger
