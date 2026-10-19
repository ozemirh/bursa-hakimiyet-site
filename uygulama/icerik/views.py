"""İçerik görünümleri — anasayfa, kategori, ilçe, arama, haber detay.

Hepsi veritabanından render eder; şablonlarda gömülü haber başlığı ya da
gövdesi yoktur (F4 bitti ölçütü, madde a).

Anasayfa düzeni URUN-PLANI.md §1'deki bileşen sözleşmesine bağlıdır:
manşet **15 slayt + 10 başlıklık liste**, ikinci alan **5**, dörtlü kutucuk
**4**, haber kutuları **11** (biri geniş). Sayılar `anasayfa_dizilimi`nde
sabit durur ki şablon hâli ve panelin manşet ekranı aynı ölçümü versin.

30 Ağustos 2026 (§35): manşet 15'ten 5'e indi. Plan §4 madde 1 ölçümü
"5'ten sonrası neredeyse görülmüyor" diyordu; kalan 10 kayıt slaytın
altında tarihli başlık listesi olarak duruyor — Bursaspor bölümünde
işe yaradığı ölçülen çözümün anasayfa uyarlaması.
"""

import json
from urllib.parse import urlsplit

from django.core.paginator import Paginator
from django.utils.functional import cached_property
from django.db.models import F, Max, Min, Q
from django.http import Http404
from django.shortcuts import get_object_or_404, render

from taksonomi.models import Ilce, Kategori

from .templatetags.site_etiket import baslikla

from medya.models import FotoGaleri, KoseYazisi, Video, Yazar

from . import arama as arama_motoru
from .arama_metni import sorgu_coz
from .canli import (anasayfa_verisi, namaz_verisi, oku, puan_ligleri,
                    puan_takibi)
from . import bursaspor as bursaspor_bolumu
from . import temalar
from . import eczane as eczane_sayfa
from . import okunma, onbellek
from .models import Haber, ResmiIlan
from .sayfa_onbellegi import sayfa_onbellegi
from .sayfa_no import sayfa_getir

# Yuva sayıları (§1 bileşen sözleşmesi) 19 Ekim 2026'dan beri dizilim
# modülünde duruyor; anasayfa ve panelin manşet ekranı aynı sayıyı okusun:
#
#   MANSET 15        manşet slaytı (§35'te 5'e inmiş, 30 Ağustos'ta 15)
#   MANSET_LISTE 10  slaytın altındaki "GÜNÜN MANŞETLERİ"
#   IKINCIL 5        yan slayt (kare manşet) · DORTLU 4 (tepe manşet)
#   KUTU 11          1 geniş + 10 kart (10'da son hücre öksüz kalıyordu)
#   EN_COK 5         "en çok okunanlar"; sayfadaki hiçbir kaydı tekrarlamaz
from .anasayfa_dizilimi import DORTLU, EN_COK, IKINCIL, KUTU, MANSET, MANSET_LISTE  # noqa: E402,F401
from . import anasayfa_dizilimi  # noqa: E402
# Anasayfada gösterilen resmî ilan adedi. İki sütunda dört satır: bölüm
# haber akışının önüne geçmeden süzgeci anlamlı kılacak kadar kayıt.
ILAN = 8
# Bursaspor bölümündeki fotoğraflı kart sayısı: 3x3 ızgara.
#
# 6 Eylül 2026, kullanıcı isteği: 6 -> 9. Aynı kararla kartların altındaki
# "SON GELİŞMELER" başlık listesi (`BURSASPOR_LISTE`, 29 Ağustos'ta konmuş,
# 31 Ağustos'ta dört satıra inmişti) tümüyle KALKTI. Listenin gerekçesi sağ
# alttaki boşluğu kart eklemeden kapatmaktı; üçüncü kart sırası o boşluğu
# zaten dolduruyor ve sağ sütun artık puan tablosundan UZUN (ölçüldü:
# kart sütunu 808 px, tablo 790 px). Denge bu kez tablo tarafında kuruluyor —
# `.bursaspor-izgara` gerilip puan kutusunu kartların bittiği yerde
# bitiriyor (site.css). Sayı değişirse iki sütunun farkı yeniden ölçülmeli.
BURSASPOR = 9
SAYFA_BOYU = 20
# Resmî ilan DİZİNİNİN sayfa boyu — haber listelerinden ayrı.
#
# 23 kayıtta sayfalama ETKİN DEĞİL ve bu bilerek böyle: 23 satırlık bir
# dizini ikiye bölmek okurdan üçte birini saklardı, üstelik sayfanın asıl
# iddiası ("gazetenin bu dönemde yayımladığı ilanların tamamı bu") tek
# ekranda okunabilsin diye var. Mekanizma yine de kurulu — ilan modülü
# canlıya çıkınca kayıt sayısı hızla büyür ve sınırsız liste bir gün
# sayfayı düşürür. 40, okunmayıp TARANAN bir dizin satırı için makul
# dilim; haber kartından çok daha kısa satırlar.
ILAN_SAYFA_BOYU = 40


# Anasayfadaki not satırları arşivin büyüklüğünü söylüyor. Bu sayılar
# şablona ELLE yazılmıştı ve göç sürdükçe yanlışlaşıyordu (ölçüm, 27 Ağustos:
# şablonda "1484 video" yazarken veritabanında 31.084 vardı). Artık
# veritabanından sayılıyor. Sayım ucuz değil (ölçüldü: dört tablo toplam
# ~67 ms), o yüzden `canli.py`deki kısa bellek düzeniyle aynı biçimde
# önbelleğe alınıyor — anasayfa her istekte dört COUNT açmasın.
SAYIM_BELLEK_SANIYE = 300
# Sayım kilide takılırsa sonuç bu kadar süre beklet: her istek kilide
# yeniden girmesin, ama kilit kalkınca sayfa dakikalarca eksik kalmasın.
HATA_BELLEK_SANIYE = 20
# 19 Ekim 2026: modül değişkeninden paylaşılan önbelleğe (icerik/onbellek.py).
SAYIM_ANAHTARI = "bh:arsiv-sayilari:v1"
_SAYILAMADI = {"yazar_adedi": None, "kose_adedi": None,
               "galeri_adedi": None, "video_adedi": None}


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

    Hata da ÖNBELLEĞE yazılır (`HATA_BELLEK_SANIYE`). Yazılmadığı sürece,
    göç gibi uzun bir yazma işi sürerken her istek kilide yeniden giriyor
    ve SQLite'ın bekleme süresi kadar duruyordu. Kısa bir pencere seçildi:
    kilit geçici, sayfa da uzun süre eksik kalmasın.
    """
    return onbellek.hesapla(SAYIM_ANAHTARI, _arsiv_say,
                            taze=SAYIM_BELLEK_SANIYE, hata=HATA_BELLEK_SANIYE,
                            yedek=lambda: dict(_SAYILAMADI))


def _arsiv_say() -> dict:
    return {
        "yazar_adedi": Yazar.listedekiler().count(),
        "kose_adedi": KoseYazisi.yayindakiler().count(),
        "galeri_adedi": FotoGaleri.yayindakiler().count(),
        "video_adedi": Video.yayindakiler().count(),
    }


def _liste(sinirsiz=False):
    """Ortak sorgu: yayındaki haberler, adres kurmak için gereken ilişkilerle.

    `kategori__turler` ön çekimi 19 Ekim 2026'da KALKTI: adres slug'ı
    süreç içi eşlemeden geliyor (`taksonomi/slug_eslemesi.py`). Her liste
    için açılan KategoriTur sorgusu gitti (anasayfada 7 sorgu).
    """
    # NOT — `.defer("govde")` DENENDİ VE GERİ ALINDI (28 Ağustos 2026).
    # Gerekçe kâğıt üzerinde sağlamdı: gövde ortalama 1.481 karakter ve liste
    # şablonlarının hiçbiri onu basmıyor. Ölçüm gerekçeyi doğrulamadı —
    # 20 satırlık kategori listesinde medyan 4,14 → 3,77 ms (0,38 ms), en iyi
    # değer ise 2,86 → 3,33 ms ile KÖTÜLEŞTİ; kazanç gürültü içinde kaldı.
    # Buna karşılık ertelenmiş alan sessiz bir tuzak taşıyor: gövdeye
    # yanlışlıkla erişen bir kod satır başına ek sorgu açar ve bu fark
    # edilmez. Ölçülemeyen kazanç için tuzak taşınmaz.
    return Haber.yayindakiler().select_related("kategori", "ilce")


@sayfa_onbellegi
def anasayfa(request):
    """§1'deki sırayı besler; sayılar sözleşmedendir.

    19 Ekim 2026 (Paket H): yuvalar masanın manşet bayraklarından ve "önce
    Bursa" düşüş kuralından dolar (`icerik/anasayfa_dizilimi.py`). Panelin
    manşet ekranı AYNI işlevi çağırır. Bloklar birbirini **tekrar etmez**:
    dizilim her haberi tek yuvaya yerleştirir.
    """
    dizilim = anasayfa_dizilimi.kur()
    manset = dizilim.manset
    manset_liste = dizilim.manset_liste
    ikincil = dizilim.ikincil
    dortlu = dizilim.dortlu
    kutular = dizilim.kutular

    # "En çok okunanlar" — artık gerçek sayaçtan (icerik/okunma.py).
    # Sayaç yeterli veriyi toplayana kadar liste eski kuralına düşer:
    # editör seçkisi gibi davranan en yeniler (URUN-PLANI.md §4, madde 8).
    #
    # Sayfada ZATEN geçen kayıtlar dışarıda bırakılıyor. Bu kural gerçek
    # veriyle daha da gerekli: en çok okunan haber çoğu zaman manşetin
    # kendisidir ve liste onu tekrarlarsa 29 Ağustos'ta ölçülen kusur
    # (aynı başlık sayfada üç kez) geri gelirdi.
    kullanilan = dizilim.kullanilan
    en_cok = okunma.en_cok(_liste(), EN_COK, haric=kullanilan) or dizilim.kalan[:EN_COK]

    # Yazar kuşağı (§35): sağ raydaki beş satırlık silik liste, tam
    # genişlikte portreli bir şeride dönüştü — 10 yazar sığıyor.
    yazarlar = list(Yazar.listedekiler()[:10])

    # Resmî ilan bölümü ELLE YAZILMIŞTI (altı sabit <li>). Kayıtlar
    # veritabanında duruyordu; artık oradan çiziliyor. Süzgeç şeridindeki
    # sayılar **sayfada listelenen** ilanları sayar, tüm arşivi değil —
    # şeridin altındaki not toplamı ayrıca söylüyor.
    ilanlar = list(ResmiIlan.yayimlananlar()[:ILAN])
    ilan_toplami = ResmiIlan.yayimlananlar().count()
    ilan_dagilimi = ResmiIlan.tur_dagilimi(ResmiIlan.yayimlananlar())

    # Bölümün notu "İCRA ve PERSONEL ALIMI türünde ilan yok" cümlesini
    # ŞABLONA ÇAKILI taşıyordu: veri değişse not yalan söyleyecekti.
    # Boş türler artık dağılımdan okunuyor.
    ilan_bos_turler = [t["ad"] for t in ilan_dagilimi if not t["adet"]]

    # Dönem etiketi. Kayıtların tamamı arşiv durumunda ve `bitis_tarihi`
    # boş; okur "bunlar bugünün açık ihaleleri mi?" sorusunu ancak satır
    # satır tarihlere bakarak yanıtlıyordu. Başlıktaki tarih aralığı bunu
    # ilk bakışta söylüyor (URUN-PLANI.md §32).
    ilan_tarihleri = [i.yayin_tarihi for i in ilanlar if i.yayin_tarihi]
    ilan_son = max(ilan_tarihleri) if ilan_tarihleri else None
    ilan_ilk = min(ilan_tarihleri) if ilan_tarihleri else None
    if ilan_ilk == ilan_son:
        ilan_ilk = None

    bursaspor = Kategori.objects.filter(ad="BURSASPOR").first()
    bursaspor_haberleri = []
    if bursaspor:
        bursaspor_haberleri = list(_liste().filter(kategori=bursaspor)[:BURSASPOR])

    return render(request, "anasayfa.html", {
        "anasayfa_mi": True,
        "manset": manset,
        "manset_liste": manset_liste,
        "ikincil": ikincil,
        "dortlu": dortlu,
        "kutular": kutular,
        "bursaspor_haberleri": bursaspor_haberleri,
        "en_cok": en_cok,
        "ilanlar": ilanlar,
        "ilan_turleri": ResmiIlan.tur_dagilimi(ilanlar),
        "ilan_toplami": ilan_toplami,
        "ilan_tur_toplami": ilan_dagilimi,
        "ilan_bos_turler": ilan_bos_turler,
        "ilan_ilk": ilan_ilk,
        "ilan_son": ilan_son,
        # Medya aileleri göç etti; sağ ray ve alt bloklar artık gerçek
        # veriden besleniyor. Şablonlar boş listeyi yine de karşılıyor —
        # tarama sürerken bir aile boş kalabilir.
        "yazarlar": yazarlar,
        **arsiv_sayilari(),
        **anasayfa_verisi(),
        "galeriler": FotoGaleri.yayindakiler()
                     .select_related("kategori")
                     .prefetch_related("kategori__turler")[:4],
        "videolar": Video.yayindakiler()
                    .select_related("kategori")
                    .prefetch_related("kategori__turler")[:4],
    })


# Bölüm sayfasının "EN ÇOK OKUNANLAR" şeridi (2 Eylül 2026, §47, kullanıcı
# isteği: "kategori sayfalarına en çok okunanlar paneli ekle, o kategoriye
# özel").
KATEGORI_EN_COK = 5

# ---------------------------------------------------------------------------
# AKIŞ RİTMİ — 7 Eylül 2026 (§60, kullanıcı isteği: "kategori sayfalarında
# haberlerin tarihlere bölünmesini kaldır, onun yerine 2'li ve 3'lü
# haberlerin sunulacağı bir akış hazırla").
#
# Tarih ayracı (2 Eylül, §46) KALKTI. Bilgi kaybolmuyor: her kartın kendi
# zaman damgası zaten var ve `kisa_zaman` süzgeci aynı günün haberinde saat,
# eskisinde tarih basıyor ("31 Eki 2025") — ayracın söylediğini kart tek
# başına söylüyor.
#
# Yerine gelen ritim: iki geniş kart, üç dar kart, iki, üç… Blok boyu
# sayfada ölçülebilir bir kesme yapıyor; eskiden yirmi eşit satır art arda
# geliyordu ve sayfanın hiçbir yerinde durak yoktu.
#
# SAYI SEÇİMİ TESADÜF DEĞİL. Ritmin bir turu 5 kayıt ve sayfa boyları buna
# tam oturuyor:
#
#     1. sayfa akışı  = 20 − 3 (üstteki kart kademesi) = 17 = 2+3+2+3+2+3+2
#     2+. sayfa akışı = 20                             = 3+2+3+2+3+2+3+2
#
# İkisi de TAM bölünüyor, yani hiçbir blok yarım kalmıyor. Üstelik 1. sayfa
# ikiliyle bitiyor ve sonraki sayfa ÜÇLÜYLE başlıyor (`ilk_uclu`): "daha
# fazla göster" ile eklenen dilim, ritmi bozmadan kaldığı yerden sürüyor.
# Sayfa boyu ya da kart kademesi değişirse bu iki toplam yeniden kontrol
# edilmeli — test (`tests_akis_ritmi`) bunu bekliyor.
AKIS_RITMI = (2, 3)
# 1. sayfanın başındaki kart kademesi: 1 geniş + 2 normal (§46).
KATEGORI_KART = 3


def _akis_bloklari(kalemler, ilk_uclu=False):
    """Kalemleri ikili ve üçlü bloklara böler.

    `ilk_uclu`, ritmin nerede kaldığını taşır: 1. sayfa ikiliyle bittiği
    için sonraki dilim üçlüyle başlar. Bu tek bayrak olmasa "daha fazla
    göster"in eklediği ilk blok, sayfadaki son blokla aynı boyda çıkar ve
    ritim seamde tekler.

    Son blok EKSİK kalabilir — bölümün son sayfasında kalem sayısı 5'in
    katı olmayabilir. Izgara o durumda hücreyi boş bırakır; kartı gerip
    satırı doldurmak, o haberi olmadığı kadar önemli gösterirdi.
    """
    bloklar = []
    sira = 1 if ilk_uclu else 0
    i = 0
    while i < len(kalemler):
        boy = AKIS_RITMI[sira % len(AKIS_RITMI)]
        bloklar.append({
            "tur": "uclu" if boy == 3 else "ikili",
            "boy": boy,
            # Spot YALNIZ ikilide: üçlü blokta sütun 357 px'e iniyor ve
            # üç satırlık spot başlığı bastırıyor. Ağırlık farkı ritmin
            # kendisi — iki blok aynı görünseydi bölmenin anlamı kalmazdı.
            "spot": boy == 2,
            "kalemler": kalemler[i:i + boy],
        })
        i += boy
        sira += 1
    return bloklar


def _bolum_akisi(sayfa):
    """Bölüm sayfasının akış blokları.

    1. sayfada ilk üç kayıt yukarıdaki kart kademesindedir ve akışa
    girmez; sonraki sayfalar kronolojik devamdır, kademe yoktur.
    """
    kalemler = list(sayfa)
    ilk = sayfa.number == 1
    if ilk:
        kalemler = kalemler[KATEGORI_KART:]
    return _akis_bloklari(kalemler, ilk_uclu=not ilk)


def _bolum_en_cok(sorgu, sayfa):
    """Şeridin kalemleri — bu bölümün pencerede en çok okunanları.

    Kapsamı `sorgu` taşır: sıralama küçük okunma tablosundan çıkar, sonra
    o bölümün listesiyle süzülür (gerekçe ve ölçüm: `icerik/okunma.py`,
    `en_cok`).

    Sıralama `icerik/okunma.py` üzerinden çıkar ve **yalnız bu bölümün**
    kayıtlarını taşır: kapsamı `sorgu`nun kendisi veriyor. Sayfada görünen
    haberler dışarıda bırakılır, yoksa aynı başlık ekranda iki kez durur.

    Sayaç yeterli veriyi toplayana kadar (URUN-PLANI.md §4, madde 8) eski
    kural sürüyor: sayfanın son kaydından SONRAKİ beş haber. İki durumda da
    kalemler o bölüme ait ve sayfada ikinci kez görünmüyorlar; şablon ve
    biçim değişmiyor.
    """
    sayfadakiler = [h.pk for h in sayfa]
    okunanlar = okunma.en_cok(sorgu, KATEGORI_EN_COK, haric=sayfadakiler)
    if okunanlar:
        return okunanlar
    bas = sayfa.end_index() or 0
    return list(sorgu[bas:bas + KATEGORI_EN_COK])


# ---------------------------------------------------------------------------
# BÖLÜM SAYFASININ İKİ YENİ BLOĞU (6 Eylül 2026, §59, kullanıcı isteği:
# "kategori sayfalarının içeriğini çeşitlendirmeni de istiyorum").
#
# Sayfa tek bir şey yapıyordu: kronolojik liste. Eklenen iki şey, Guardian ·
# BBC · NYT · Hürriyet bölüm sayfalarında ortak olup bizde bulunmayanlardan
# ÖLÇÜLEREK seçildi — yani verisi bugün var olanlar:
#
#   1. GÖRÜNTÜ KUŞAĞI — o bölümün videoları ve foto galerileri. 31.075
#      videonun ve 2.872 galerinin kategorisi dolu; sorgu 1 ms.
#   2. SERVİS ŞERİDİ — bölümü okuyanın işine yarayan canlı veri. Ekonomi'de
#      döviz bandı, spor bölümlerinde Bursaspor'un lig satırı ve haftanın
#      maçı, sağlıkta ve İLÇE sayfalarında nöbetçi eczane.
#
# Denenip ELENENLER (veri yok, uydurulmaz): bölümün yazarları — 6.713 köşe
# yazısının TAMAMININ kategorisi boş; etiket bulutu — 23 etiket, 23 bağ.
# İkisi de veri işi; kurulursa bu blokların yanına eklenir.
# ---------------------------------------------------------------------------

# Kuşaktaki kalem sayısı. Dörder: ızgaralar (`.galeri-izgara`,
# `.video-izgara`) anasayfada da dörtlü ve aynı CSS kullanılıyor.
BOLUM_GALERI = 4
BOLUM_VIDEO = 4
# Servis panelinde listelenen nöbetçi eczane adedi. Panel bir ÖZETTİR;
# tam liste kendi sayfasında (`/nobetci-eczane`) duruyor. 4 = ızgaranın bir
# tam satırı; 3 bırakıldığında son gözde delik kalıyordu.
SERVIS_ECZANE = 4

# Puan tablosundan gösterilen pencere: Bursaspor'un ÜSTÜNDE ve ALTINDA kaç
# takım. 2 + 2 + kendisi = 5 satır — okurun "kiminle yarışıyoruz" sorusunu
# yanıtlayacak kadar, tabloyu bölüm sayfasına taşımayacak kadar.
PUAN_PENCERE = 2

# Hangi bölüm hangi servisi görür. Slug **tür satırının** slug'ıdır.
SERVIS_DOVIZ = {"ekonomi"}
SERVIS_PUAN = {"bursaspor", "spor", "bursa-da-spor"}
SERVIS_NOBET = {"saglik"}
# Kulüp sayfası: sezon fikstürü ve yeşil-beyaz kabuk yalnız burada.
BURSASPOR_SLUG = "bursaspor"

# NOT — BÖLÜME ÖZEL RENK 7 Eylül 2026'da geri alınmıştı (§62 → §63); 19
# Ekim 2026 kullanıcı kararıyla sayfaya özel tasarım geri geldi, ama bu
# sefer TEK KAYITTAN: `icerik/temalar.py`. Burada bölüm→renk sözlüğü
# tutulmaz (eski `BOLUM_TEMA` / `ILCE_TEMA` dönmesin); görünüm yalnız
# kaydın verdiği `tema`yı bağlama koyar.


def _bolum_gorselleri(kategori):
    """Bölümün video ve galerileri. İkisi de boşsa kuşak hiç çizilmez.

    Gündemde galeri YOK, aktüalite ve savunma sanayinde ikisi de yok
    (ölçüldü). Şablon boş listeyi karşılıyor; "arşiv göç etmedi" gibi bir
    yer tutucu basmıyor — bölüm sayfasında o cümle okura hiçbir şey
    anlatmaz, yalnızca yer kaplar.
    """
    ortak = ["kategori"]
    return {
        "bolum_galerileri": list(
            FotoGaleri.yayindakiler().filter(kategori=kategori)
            .select_related(*ortak).prefetch_related("kategori__turler")[:BOLUM_GALERI]),
        "bolum_videolari": list(
            Video.yayindakiler().filter(kategori=kategori)
            .select_related(*ortak).prefetch_related("kategori__turler")[:BOLUM_VIDEO]),
    }


def _nobet_ozeti(slug="", ad=""):
    """Nöbetçi eczane panelinin içeriği. Kayıt yoksa None — sahte satır yok.

    Liste dünden eskiyse (`canli.GECERLIK_GUN`, 19 Ekim 2026) eczane
    basılmaz; panel "liste güncel değil" der ve kaynağa yönlendirir.
    """
    panel = eczane_sayfa.gunun_paketi(gecersizi_de=True)
    if panel and panel.get("gecersiz"):
        return {"tur": "nobet", "gecersiz": True, "panel": panel, "yer": ad,
                "yol": eczane_sayfa.ilce_yolu(slug), "eczaneler": [], "adet": 0}
    tumu = panel["eczaneler"] if panel else []
    kayitlar = [e for e in tumu if e["ilce_anahtar"] == slug] if slug else tumu
    if not kayitlar:
        return None
    return {
        "tur": "nobet",
        "eczaneler": kayitlar[:SERVIS_ECZANE],
        "adet": len(kayitlar),
        "yer": ad,
        "yol": eczane_sayfa.ilce_yolu(slug),
        "gun": panel["gun"] if panel else None,
        # Nöbet aralığı ("08:30 – 08:30 ertesi gün") ve şu an nöbette olan
        # sayısı panelin künyesinde duruyor: okur "bu liste ne zamana ait"
        # sorusunu paneli terk etmeden yanıtlıyor.
        "pencere": panel.get("pencere") if panel else "",
        "kaynak": panel.get("kaynak") if panel else None,
        # Bayatlık sözleşmesi (`canli.tazelik`): eski liste künyede
        # anasayfadaki panelle aynı uyarıyı taşır (19 Ekim 2026).
        "tazelik": panel.get("tazelik") if panel else None,
        "bayat": bool(panel and panel.get("bayat")),
    }


def _puan_penceresi(puan, takip):
    """Bursaspor'un bulunduğu grubun tablosundan onun ETRAFINDAKİ satırlar.

    Tablonun tamamı anasayfada duruyor ve bölüm sayfasına taşınsa haber
    akışını yirmi satır aşağı iterdi. Okurun burada sorduğu şey "kiminle
    yarışıyoruz": beş satır onu yanıtlıyor.

    Pencere tablonun ucuna dayanırsa kaydırılır — Bursaspor birinciyken de
    sonuncuyken de beş satır gösterilir, üstü boş bırakılmaz.
    """
    if not takip:
        return []
    boy = 2 * PUAN_PENCERE + 1
    for lig in puan_ligleri(puan):
        for grup in lig.get("gruplar") or []:
            takimlar = grup.get("takimlar") or []
            for i, t in enumerate(takimlar):
                if t.get("bizim"):
                    bas = max(0, min(i - PUAN_PENCERE, len(takimlar) - boy))
                    return takimlar[bas:bas + boy]
    return []


def _bolum_servisi(slug="", ilce=None):
    """Bölüme özel canlı veri şeridi — yoksa None, şablon hiç çizmez.

    Veri ZATEN toplanıyor (`canli.py`, `icerik/eczane.py`) ve anasayfada
    duruyor; buraya taşınan tek şey sunum. Şerit anasayfadaki panellerin
    kopyası DEĞİL, özeti: ekonomi bandı aynı bant, spor şeridi tablonun
    tamamı değil Bursaspor'un satırı, eczane şeridi listenin ilk üçü.
    """
    if ilce is not None:
        # İlçe sayfası: o ilçenin bugünkü nöbetçileri. Hava durumu BURSA
        # merkezi için tek pakettir (`hava_paneli`), ilçeye inmiyor — ilçe
        # sayfasında merkezin havasını basmak yanlış bilgi olurdu.
        return _nobet_ozeti(ilce.slug, ilce.ad)
    if slug in SERVIS_DOVIZ:
        doviz = oku("doviz")
        return {"tur": "doviz", "doviz": doviz} if doviz else None
    if slug in SERVIS_PUAN:
        puan = oku("puan-durumu")
        takip = puan_takibi(puan)
        if not takip:
            return None
        return {"tur": "puan", "takip": takip,
                "pencere": _puan_penceresi(puan, takip)}
    if slug in SERVIS_NOBET:
        return _nobet_ozeti()
    return None


@sayfa_onbellegi
def kategori(request, slug):
    """Kategori listesi. Slug **tür satırından** gelir, kategori adından değil."""
    kategori = get_object_or_404(Kategori, turler__tur=Kategori.TUR_HABER,
                                 turler__slug=slug, aktif=True)
    sorgu = _liste().filter(kategori=kategori)
    sayfa = _sayfala(request, sorgu, sinirli=True)
    baglam = {
        "kategori": kategori,
        "baslik": baslikla(kategori.ad),
        "sayfa": sayfa,
        "en_cok": _bolum_en_cok(sorgu, sayfa),
        # "Daha fazla göster" düğmesinin çektiği uç. Slug **tür satırından**
        # gelen slug'dır, kategori adından türetilmiş olan değil.
        "daha_uc": f"/daha-fazla?kaynak=kategori&slug={slug}",
        "servis": _bolum_servisi(slug=slug),
        "akis": _bolum_akisi(sayfa),
        # Bursaspor'a özel blok (12 Eylül 2026, `icerik/bursaspor.py`):
        # sezon fikstürü + yeşil-beyaz kabuk. Yalnız o bölümde; `/spor`
        # genel spor sayfasıdır ve kulüp sayfasına dönmez.
        "bursaspor": (bursaspor_bolumu.bolum_verisi(oku("puan-durumu"))
                      if slug == BURSASPOR_SLUG else None),
        **_bolum_gorselleri(kategori),
    }
    # Sayfaya özel tasarım (19 Ekim 2026): `tema` ve temanın düzen verisi.
    # Hangi bölümün tema aldığı tek kayıtta (`icerik/temalar.py`).
    baglam.update(temalar.kategori_baglami(slug, kategori, sayfa, baglam))
    return render(request, "kategori.html", baglam)


@sayfa_onbellegi
def ilce(request, slug):
    ilce = get_object_or_404(Ilce, slug=slug)
    sorgu = _liste().filter(ilce=ilce)
    sayfa = _sayfala(request, sorgu, sinirli=True)
    return render(request, "kategori.html", {
        "baslik": f"{ilce.ad} haberleri",
        "ilce": ilce,
        "sayfa": sayfa,
        "en_cok": _bolum_en_cok(sorgu, sayfa),
        "daha_uc": f"/daha-fazla?kaynak=ilce&slug={slug}",
        # İlçenin görüntü kuşağı YOK: galeri ve videonun kategorisi var,
        # ilçesi yok (`medya.models.KategoriliIcerik`). Uydurma bir eşleme
        # yapmaktansa blok hiç çizilmiyor.
        "servis": _bolum_servisi(ilce=ilce),
        "akis": _bolum_akisi(sayfa),
    })


# ---------------------------------------------------------------------------
# "DAHA FAZLA GÖSTER" (6 Eylül 2026, kullanıcı isteği: "hem anasayfada hem de
# kategori sayfalarında daha fazla göster seçeneği ekle haberler için,
# numaralara bölme sayfaları").
#
# Numaralı sayfalama kategori/ilçe sayfasından KALKTI; yerine akışın altında
# tek bir düğme duruyor. Düğme GERÇEK BİR BAĞLANTIDIR (`?sayfa=2`) ve bu
# bilinçli: JavaScript yoksa okur sonraki sayfaya gider, arama motoru da aynı
# zinciri yürüyerek arşivin tamamına iner. Numaralar gitti, tarama yolu değil.
#
# Anasayfanın SON HABERLER ızgarasında sayfalama YOKTU: kartlar tek havuzun
# sabit diliminden geliyor. Düğmenin çektiği dilim o havuzun BİTTİĞİ yerden
# başlar (`ANASAYFA_ATLA`), yoksa ilk tıklamada sayfada zaten duran haberler
# ikinci kez görünürdü. JavaScript'siz karşılığı `/son-haberler` sayfasıdır —
# orada liste baştan başlar, çünkü kendi başına açılan bir sayfanın 46.
# haberden başlaması okura hiçbir şey anlatmaz.
# ---------------------------------------------------------------------------

# Anasayfada ızgaraya kadar basılan her dilim. EN_COK burada YOK: o kutu
# okunma sayacından besleniyor ve havuzun sırasını takip etmiyor.
ANASAYFA_ATLA = MANSET + MANSET_LISTE + IKINCIL + DORTLU + KUTU
# Anasayfada bir tıklamanın getirdiği kart sayısı. Kategori akışının 20'si
# değil: ızgara iki sütunlu ve fotoğraflı, 20 kart tek tıklamada 10 satır
# açardı. 10 = beş satır.
ANASAYFA_DAHA = 10


def _akis_sorgusu(kaynak, slug):
    """Düğmenin çektiği dilimlerin kaynağı — sayfadakiyle AYNI sıralama.

    Dönen ikinci değer kategori nesnesidir; akış satırı kendi bölüm adını
    tekrar basmasın diye şablona geçiyor (`kategori_gizle`).
    """
    if kaynak == "kategori":
        kategori = get_object_or_404(Kategori, turler__tur=Kategori.TUR_HABER,
                                     turler__slug=slug, aktif=True)
        return _liste().filter(kategori=kategori), kategori
    if kaynak == "ilce":
        get_object_or_404(Ilce, slug=slug)
        return _liste().filter(ilce__slug=slug), None
    return _liste(), None


def _dilim(sorgu, numara, boy, atla=0):
    """`numara`ıncı dilim ve "devamı var mı" — SAYIM YAPMADAN.

    Parça ucunun `Paginator`a ihtiyacı yok: numara listesi, toplam sayı,
    "kaçıncı sayfadasınız" bilgisi yanıtta zaten görünmüyor. Sayımın bedeli
    ise gerçek — `SinirliSayfalayici` bunun için yazılmıştı ve o bile
    1.000'de kesiyor, yani düğme 50. tıklamadan sonra "daha var" diyemezdi.

    Yerine BİR FAZLA kayıt çekiliyor: yirmi bir satır geldiyse devamı vardır.
    Bedeli tek satır, sonucu kesin ve arşivin derinliğiyle sınırlı değil.

    `atla` anasayfa içindir: ızgarada zaten basılmış kayıtların üstünden
    atlar, yoksa ilk tıklamada manşet ikinci kez görünürdü.
    """
    bas = atla + max(numara - 1, 0) * boy
    kayitlar = list(sorgu[bas:bas + boy + 1])
    return kayitlar[:boy], len(kayitlar) > boy


def daha_fazla(request):
    """Akışın sonraki dilimi — düğmenin çektiği HTML parçası.

    Yanıt bir PARÇADIR, sayfa değil: kalemler ve onları saran, "daha var mı"
    bilgisini taşıyan tek bir kap. JSON değil — kart ve akış satırı şablonları
    sunucuda duruyor ve ikinci bir kopyayı JavaScript'te tutmak ikisinin
    sessizce ayrışması demekti.
    """
    kaynak = request.GET.get("kaynak") or "anasayfa"
    if kaynak not in {"anasayfa", "son", "kategori", "ilce"}:
        raise Http404("Bilinmeyen akış")
    slug = request.GET.get("slug") or ""
    if kaynak in {"kategori", "ilce"} and not slug:
        raise Http404("Bölüm belirtilmedi")
    try:
        numara = max(int(request.GET.get("sayfa") or 1), 1)
    except (TypeError, ValueError):
        numara = 1
    sorgu, kategori = _akis_sorgusu(kaynak, slug)
    if kaynak == "anasayfa":
        kalemler, devam = _dilim(sorgu, numara, ANASAYFA_DAHA, atla=ANASAYFA_ATLA)
    else:
        kalemler, devam = _dilim(sorgu, numara, SAYFA_BOYU)
    return render(request, "parca/akis_parcasi.html", {
        "kalemler": kalemler,
        # Anasayfa ızgarası ritim tanımıyor (kart ızgarası, akış değil);
        # kalan üç kaynak bölüm akışının bloklarını basar. `ilk_uclu`
        # bilerek koşulsuz: düğme bu uçları hep 2. sayfadan itibaren
        # çağırıyor ve 1. sayfa ikiliyle bitiyor.
        "akis": ([] if kaynak == "anasayfa"
                 else _akis_bloklari(kalemler, ilk_uclu=numara > 1)),
        "devam": devam,
        "kaynak": kaynak,
        "kategori": kategori,
    })


def son_haberler(request):
    """Bütün bölümlerin ortak akışı — anasayfa düğmesinin JS'siz karşılığı.

    Kategori sayfasının şablonunu kullanır; tek farkı kapsamının bölümle
    sınırlı olmaması. "EN ÇOK OKUNANLAR" şeridi BİLEREK yollanmıyor: burada
    kapsam site geneli olurdu ve anasayfadaki aynı adlı kutunun kopyası
    olarak dururdu.
    """
    sorgu = _liste()
    sayfa = _sayfala(request, sorgu, sinirli=True)
    return render(request, "kategori.html", {
        "baslik": "Son haberler",
        "sayfa": sayfa,
        "daha_uc": "/daha-fazla?kaynak=son",
        "akis": _bolum_akisi(sayfa),
    })


def nobetci_eczane(request, slug=""):
    """Kalıcı nöbetçi eczane sayfası — Bursa geneli ve 17 ilçe.

    31 Ağustos 2026, kullanıcı isteği. Nöbet listesi anasayfa panelinde
    zaten duruyordu ama **kendi adresi yoktu**; "bursa nöbetçi eczane" ya
    da "osmangazi nöbetçi eczane" arayan okurun ineceği bir sayfa
    bulunmuyordu.

    Adres kalıcıdır ve her gün kendini tazeler. Günlük haber kaydı ayrı
    iştir (`eczane_haberi` komutu) ve tarihli sorguları karşılar; gerekçe
    ayrımı `icerik/eczane.py` başında yazılı.

    **Veri yoksa da 200 döner.** Adres arama motoruna kayıtlı; çekme
    betiği bir tur kaçırdı diye 404 vermek sayfayı dizinden düşürür.
    Bilinmeyen ilçe slug'ı ise gerçekten yoktur, 404'tür.
    """
    if slug and not Ilce.objects.filter(slug=slug).exists():
        raise Http404("İlçe yok")
    baglam = eczane_sayfa.sayfa_baglami(slug)
    # `<`, `>`, `&` kaçışlı (icerik/jsonld.py); şablonda `|safe` yok.
    # Eczane adı/adresi dış kaynaktan geliyor: `</script>` enjeksiyonu.
    from .jsonld import betik_json
    baglam["yapisal_veri"] = betik_json(eczane_sayfa.yapisal_veri(baglam))
    return render(request, "nobetci_eczane.html", baglam)


def ilceler(request):
    return render(request, "ilceler.html", {"baslik": "İlçeler"})


# Anasayfa panellerinin altındaki dokuz "Veri kaynağı ve kapsam" notu
# 31 Ağustos 2026'da bu sayfaya taşındı — §34 K7'de "yeniden açılacaksa
# kullanıcı kararı" diye bırakılan maddenin kararı geldi. Notlar bağlam
# değişkenlerine bağlıydı (arşiv adetleri, ilan dağılımı, puan tazeliği);
# o yüzden sayfa statik bir metin değil, aynı sayıları kendi görünümünden
# okuyan bir görünümdür. Beyan yerinden kalktı ama veriden kopmadı.

# Canlı veri kalemleri ve `canli-veri/veri/` altındaki dosya adları.
# Sıra sayfadaki sıradır; künye bilgisi dosyanın kendi `kaynak` bloğundan
# gelir, buraya İKİNCİ bir kopya yazılmaz — kaynak değişince sayfa da
# değişsin diye.
CANLI_KALEMLER = [
    ("Döviz kurları", "doviz"),
    ("Gram altın ve BIST 100", "piyasa"),
    ("Hava durumu", "hava-durumu"),
    ("Namaz vakitleri", "namaz-vakitleri"),
    ("Nöbetçi eczane", "nobetci-eczane"),
    ("Puan durumu", "puan-durumu"),
    ("Vizyon takvimi", "vizyon-takvimi"),
]


def _baglar(metin):
    """Kaynak alanındaki GEÇERLİ adresleri ayıklar.

    Alan çoğu kalemde tek adres taşıyor ama hepsinde değil: vizyon takvimi
    iki dağıtımcıdan besleniyor ve `adres` iki adresi ayraçla tutuyor,
    `kosullar` ise kimi kalemde adres değil düz cümle. Alanı olduğu gibi
    `href`e koymak ikisinde de kırık bağlantı üretir — bu yüzden alan
    boşluklara bölünüp yalnız `http` ile başlayan parçalar alınıyor.
    """
    return [p for p in (metin or "").split() if p.startswith("http")]


def _alan_adi(adres):
    """Bağlantı metni: "https://www.tff.org/" -> "tff.org"."""
    return urlsplit(adres).netloc.removeprefix("www.") or adres


def _canli_kunyeler():
    """Canlı veri kalemlerinin kaynak künyesi, tazelik damgasıyla.

    `piyasa` kaynağını **liste** olarak taşır (sırayla denenen uçlar);
    diğerleri tek sözlük. İkisi de aynı biçime indiriliyor ki şablon tek
    döngüyle bassın. Dosya okunamazsa kalem listeden düşmez, "bağlı değil"
    olarak durur — sessizce kaybolması beyanı eksiltirdi.
    """
    kalemler = []
    for ad, bilesen in CANLI_KALEMLER:
        # Namaz dosyadan değil istek anında hesaptan gelir (19 Ekim 2026);
        # beyan da sitenin gerçekte gösterdiğini söylemeli.
        veri = (namaz_verisi() if bilesen == "namaz-vakitleri"
                else oku(bilesen)) or {}
        kaynak = veri.get("kaynak")
        if isinstance(kaynak, dict):
            ham = [kaynak]
        elif isinstance(kaynak, list):
            ham = [k for k in kaynak if isinstance(k, dict)]
        else:
            ham = []
        kaynaklar = []
        for k in ham:
            adresler = _baglar(k.get("adres"))
            kaynaklar.append({
                "ad": k.get("ad") or k.get("kisa") or "",
                # Tek adres varsa ad'ın kendisi bağlantı olur; birden çok
                # adres varsa ad düz metin kalır ve adresler alan adlarıyla
                # ayrı ayrı basılır.
                "tek_bag": adresler[0] if len(adresler) == 1 else "",
                "baglar": [{"adres": a, "alan": _alan_adi(a)}
                           for a in adresler] if len(adresler) > 1 else [],
                "kosullar": next(iter(_baglar(k.get("kosullar"))), ""),
            })
        kalemler.append({
            "ad": ad,
            "kaynaklar": kaynaklar,
            "guncelleme": veri.get("guncelleme"),
            "bayat": veri.get("bayat"),
        })
    return kalemler


def veri_kaynaklari(request):
    ilanlar = ResmiIlan.yayimlananlar()
    # Beyan sayfası "en çok okunanlar"ın hangi veriye dayandığını söylüyor.
    # Cümle ŞABLONA ÇAKILI olamaz: liste sayaç eşiği aşılınca kendiliğinden
    # gerçek veriye geçiyor ve beyan o anda yanlışlaşırdı — resmî ilan
    # notunda ölçülen kusurun (§30) aynısı.
    return render(request, "veri_kaynaklari.html", {
        "baslik": "Veri kaynakları ve kapsam",
        "okunma_gercek": bool(okunma.en_cok(_liste(), EN_COK)),
        "okunma_pencere": okunma.PENCERE_GUN,
        "canli_kalemler": _canli_kunyeler(),
        "ilan_toplami": ilanlar.count(),
        "ilan_tur_toplami": ResmiIlan.tur_dagilimi(ilanlar),
        "puan": oku("puan-durumu"),
        "vizyon": oku("vizyon-takvimi"),
        **arsiv_sayilari(),
    })


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


def _ilan_aylara_bol(kayitlar):
    """Sıralı ilan listesini AY başlıklarına böler.

    Neden ay: dizin 23 satır ve 15 ayrı güne dağılıyor — güne göre
    gruplamak 15 başlık, 1-3 satırlık kümeler demekti; gün bilgisini
    zaten satırın solundaki tarih omurgası taşıyor. Ay, "bu dizin hangi
    dönemi kapsıyor" sorusunu kaydırırken de yanıtlıyor ve liste
    büyüdükçe tek işe yarayan kırılım o.

    Kayıtlar zaten tarihe göre sıralı geldiği için tek geçiş yeter;
    tarihi olmayan kayıtlar (şu an yok, alan boş olabiliyor) kendi
    grubunda ve en sonda toplanır — sorgu `nulls_last` ile sıralı.
    """
    gruplar = []
    for kayit in kayitlar:
        tarih = kayit.yayin_tarihi
        anahtar = f"{tarih:%Y-%m}" if tarih else ""
        if not gruplar or gruplar[-1]["anahtar"] != anahtar:
            gruplar.append({"anahtar": anahtar, "tarih": tarih, "ilanlar": []})
        gruplar[-1]["ilanlar"].append(kayit)
    return gruplar


def resmi_ilan(request):
    """Resmî ilan DİZİNİ — anasayfadaki bölümün tam listesi.

    Anasayfadaki bölüm bir seçkidir (8 kayıt) ve süzgeci JavaScript ile
    **sayfadaki** satırlar üzerinde çalışır. Dizinde üç şey ondan ayrılır:

    1. **Süzgeç adreste.** `?tur=ihale` paylaşılabilir, geri tuşu
       çalışır, JavaScript'siz çalışır ve sayfalamayla çelişmez —
       sayfalanmış bir listede tarayıcı içi süzgeç yalnız o sayfayı
       süzer, düğmedeki sayı da yalan söylerdi.
    2. **Sayılar arşivin tamamını sayar.** İlke anasayfayla aynı:
       *düğmedeki sayı, basınca geleni sayar.* Orada tıklama sayfayı
       süzdüğü için sayı sayfayı sayıyordu; burada tıklama arşivi
       süzüyor.
    3. **Ay başlıkları.** Dizin tarayarak okunur; ay, listeye omurga
       verir (`_ilan_aylara_bol`).

    Sıralama seçeneği bilerek YOK: ilan dizininin tek anlamlı sırası
    yeniden eskiye. Başlığa göre sıralamak işe yaramaz — başlıklar
    tekrar ediyor ("TAŞINMAZ SATIŞI YAPILACAK" üç kayıtta aynı); türe
    göre sıralamanın işini zaten süzgeç görüyor. Karşılığı olmayan bir
    denetim eklemek, sayfayı zenginleştirmez, kalabalıklaştırır.
    """
    tum = ResmiIlan.yayimlananlar()
    dagilim = ResmiIlan.tur_dagilimi(tum)
    arsiv_toplami = sum(t["adet"] for t in dagilim)

    turler = dict(ResmiIlan.TURLER)
    secili = request.GET.get("tur") or ""
    # Tanınmayan tür 404 DEĞİL: adres satırından gelen bozuk bir süzgeç
    # okurun karşısına hata çıkarmamalı, dizinin tamamına düşmeli.
    if secili not in turler:
        secili = ""

    kayitlar = tum.filter(tur=secili) if secili else tum
    # `nulls_last`: Meta sıralaması `-yayin_tarihi` ve tarihi olmayan kayıt
    # veritabanına göre başa ya da sona düşüyor. Dizinde tarihsiz kayıt
    # en sonda toplanmalı ki ay omurgası kırılmasın.
    kayitlar = kayitlar.order_by(F("yayin_tarihi").desc(nulls_last=True), "-id")
    sayfa = _sayfala(request, kayitlar, boy=ILAN_SAYFA_BOYU)

    # Dönem etiketi SÜZÜLMÜŞ kümeden okunur: ekranda ne varsa dönem odur.
    # Meta açıklaması ise arşivin tamamını anlatır — süzgeç adresleri zaten
    # dizinin kendisine kanonikleniyor, açıklamaları da dizini anlatmalı.
    arsiv_sinir = tum.aggregate(ilk=Min("yayin_tarihi"), son=Max("yayin_tarihi"))
    sinir = (kayitlar.aggregate(ilk=Min("yayin_tarihi"), son=Max("yayin_tarihi"))
             if secili else arsiv_sinir)
    ilk, son = sinir["ilk"], sinir["son"]
    if ilk == son:
        ilk = None      # tek güne düşen dizinde "24 Ağustos – 24 Ağustos" yazmaz

    # Sayfanın notundaki iki olgu da VERİDEN okunur, şablona çakılı değil
    # (URUN-PLANI.md §32.5'in dersi: "İCRA türünde ilan yok" cümlesi elle
    # yazılmıştı ve kayıt gelseydi yalan söyleyecekti).
    return render(request, "resmi_ilan.html", {
        "baslik": "Resmî ilanlar",
        "sayfa": sayfa,
        "gruplar": _ilan_aylara_bol(sayfa.object_list),
        "turler": dagilim,
        "bos_turler": [t["ad"] for t in dagilim if not t["adet"]],
        "arsiv_toplami": arsiv_toplami,
        "secili_ad": turler.get(secili, ""),
        # `tur` adı sayfalama parçasının beklediği addır: süzgeç sayfa
        # değişince kaybolmamalı.
        "tur": secili,
        "ilk": ilk,
        "son": son,
        "arsiv_ilk": arsiv_sinir["ilk"],
        "arsiv_son": arsiv_sinir["son"],
        "metni_olan_var": tum.exclude(metin="").exists(),
        "bitisi_olan_var": tum.exclude(bitis_tarihi=None).exists(),
    })


# Aranacak en kısa terim. Ölçüm (27 Ağustos 2026): 1-2 harflik sorgular
# ("a" 308.596 sonuç · "e" · "i" · "in" · "ve") hem en yavaşlarıydı hem de
# okura işe yaramaz bir liste veriyordu. Kısa terim aramak bilgi taşımıyor.
ARAMA_EN_AZ = 3


def arama(request):
    """Başlık ve spot üzerinde arama (19 Ekim 2026: indeksli).

    Sorgu `arama_metni.sorgu_coz` ile terimlere çözülür ve normalize edilmiş
    `HaberArama` sütununda aranır (`icerik/arama.py`): PostgreSQL'de
    `tsvector` + GIN + `kelime:*` önek, SQLite'ta aynı anlamda `LIKE`.
    Türkçe harf kusuru (`IŞIK` → 0 sonuç, §21) böylece iki motorda da kapandı.

    Korunan iki eski kazanım: `_liste()` `govde` taşımıyor ve sayım üst
    sınırla kesiliyor (`SinirliSayfalayici`).

    **Zaman sınırı.** Sayım ve sayfa dilimi `arama.sure_siniri` içinde
    değerlendirilir; aşılırsa okur uyarı görür, işçi kilitlenmez. SQLite
    yolunda bu sınır gerçekten işler (tam tarama), PostgreSQL'de emniyettir.
    """
    sorgu = (request.GET.get("q") or "").strip()
    cozum = sorgu_coz(sorgu)
    uyari = ""

    if sorgu and not cozum:
        if cozum.sebep == "hepsi_durak":
            gecen = ", ".join(f"“{k}”" for k in cozum.dusen_durak)
            uyari = (f"{gecen} gibi çok genel kelimelerle arama yapılamıyor. "
                     "Daha belirgin bir kelime deneyin.")
        else:
            uyari = "Aramak istediğiniz kelimeyi yazın."
    elif sorgu and max(len(t.kelime) for t in cozum.terimler) < ARAMA_EN_AZ:
        uyari = f"Aramak için en az {ARAMA_EN_AZ} harflik bir kelime yazın."

    aranacak = bool(sorgu) and not uyari
    toplam = 0
    if aranacak:
        try:
            with arama_motoru.sure_siniri():
                sayfa = arama_motoru.AramaSayfalayici(_liste(), cozum, SAYFA_BOYU) \
                    .get_page(request.GET.get("sayfa") or 1)
                toplam = sayfa.paginator.count
                # Tembel sorgu şablonda, yani sınırın DIŞINDA çalışırdı.
                sayfa.object_list = list(sayfa.object_list)
                sayfa.numaralar = (list(sayfa.paginator.get_elided_page_range(
                    sayfa.number, on_each_side=2, on_ends=1))
                    if sayfa.paginator.num_pages > 1 else [])
        except arama_motoru.ZamanAsimi:
            uyari = ("Arama zaman sınırını aştı. Daha belirgin ya da daha çok "
                     "kelimeyle yeniden deneyin.")
            aranacak = False
            toplam = 0
    if not aranacak:
        sayfa = _sayfala(request, Haber.objects.none())
    return render(request, "arama.html", {
        "baslik": f"“{sorgu}” için arama sonuçları" if sorgu else "Arama",
        "sorgu": sorgu,
        "uyari": uyari,
        "sayfa": sayfa,
        "toplam": toplam,
    })


class SinirliSayfalayici(Paginator):
    """Sayımı ÜST SINIRA bağlayan sayfalayıcı.

    Ölçüm (27 Ağustos 2026, 308.602 kayıt): arama sorgu başına **iki tam
    tarama** yapıyordu — biri `Paginator.count` için, biri sayfa dilimi
    için. Tam sayım okura pek bir şey katmıyor ("41.074 sonuç" ile
    "1.000+ sonuç" arasındaki fark okurun kararını değiştirmiyor) ama
    yaygın terimlerde taramanın yarısı ona gidiyordu.

    Karar: sayım en çok `UST_SINIR + 1` kayda kadar yapılır ve orada
    kesilir. Yaygın terimde tarama erken biter; nadir terimde zaten sınıra
    ulaşılmaz, o yüzden **nadir terimi hızlandırmaz** (ölçüldü — asıl
    çözüm indeks).

    `order_by()` bilerek boşaltılıyor: sayım için sıralama gereksiz ve
    sıralı sayım `yayin_zamani` indeksini baştan sona yürütüyordu.
    """

    UST_SINIR = 1000

    @cached_property
    def _ham_sayim(self) -> int:
        return len(self.object_list.order_by()
                   .values_list("pk", flat=True)[:self.UST_SINIR + 1])

    @property
    def count(self) -> int:
        return min(self._ham_sayim, self.UST_SINIR)

    @property
    def kesildi_mi(self) -> bool:
        """Sonuç sınırdan çok mu — şablon "1.000+" yazsın diye."""
        return self._ham_sayim > self.UST_SINIR


def _sayfala(request, sorgu, sinirli=False, boy=SAYFA_BOYU):
    sinif = SinirliSayfalayici if sinirli else Paginator
    # Geçersiz/aralık dışı ?sayfa= → 404, yumuşak 404 yok (Paket G).
    sayfa = sayfa_getir(sinif(sorgu, boy), request.GET.get("sayfa"))
    # Numaralı sayfalama (29 Ağustos): "1 … 4 [5] 6 … 50". Elided aralık
    # şablondan çağrılamıyor (metot bağımsız değişken istiyor), burada
    # kurulur; parca/sayfalama.html bu listeyi çizer.
    sayfa.numaralar = (list(sayfa.paginator.get_elided_page_range(
        sayfa.number, on_each_side=2, on_ends=1))
        if sayfa.paginator.num_pages > 1 else [])
    return sayfa


# ---------------------------------------------------------------------------
# Konu dosyaları (5 Eylül 2026). Yalnız onaylı dosya görünür; motorun
# önerileri panelde bekler. Okuma yardımcıları `icerik/konu.py` içinde.
# ---------------------------------------------------------------------------

from . import konu as konu_yardimci  # noqa: E402
from .models import Konu  # noqa: E402

KONU_SAYFA_BOYU = 30


# Konu dizini ve dosya sayfası da sayfa önbelleğinde (19 Ekim 2026): 300
# üyelik bir dosyanın sayfası 265 KB ve çizimi sıcak süreçte 128–159 ms
# (sorgusu artık `konuhaber_sira` indeksinden). Konu ya da bağ
# kaydedilince yayın sürümü değişir, sayfa anında tazelenir.
@sayfa_onbellegi
def konular(request):
    """Onaylı dosyaların dizini; en son gelişme önde."""
    sorgu = Konu.yayindakiler().order_by("-bitis", "-id")
    sayfa = sayfa_getir(Paginator(sorgu, KONU_SAYFA_BOYU), request.GET.get("sayfa"))
    return render(request, "konular.html", {
        "baslik": "Konu Dosyaları",
        "sayfa": sayfa,
        "surenler": Konu.surenler().count(),
    })


@sayfa_onbellegi
def konu(request, slug):
    kayit = Konu.yayindakiler().filter(slug=slug).first()
    if kayit is None:
        raise Http404("Konu yok")
    haberler = konu_yardimci.uyeler(kayit)
    return render(request, "konu.html", {
        "konu": kayit,
        "baslik": kayit.ad,
        "haberler": haberler,
        "son": haberler[-1] if haberler else None,
    })
