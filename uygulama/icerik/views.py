"""İçerik görünümleri — anasayfa, kategori, ilçe, arama, haber detay.

Hepsi veritabanından render eder; şablonlarda gömülü haber başlığı ya da
gövdesi yoktur (F4 bitti ölçütü, madde a).

Anasayfa düzeni URUN-PLANI.md §1'deki bileşen sözleşmesine bağlıdır:
manşet **5 slayt + 10 başlıklık liste**, ikinci alan **5**, dörtlü kutucuk
**4**, haber kutuları **11** (biri geniş). Sayılar burada sabit durur ki
şablon hâli aynı ölçümü versin.

30 Ağustos 2026 (§35): manşet 15'ten 5'e indi. Plan §4 madde 1 ölçümü
"5'ten sonrası neredeyse görülmüyor" diyordu; kalan 10 kayıt slaytın
altında tarihli başlık listesi olarak duruyor — Bursaspor bölümünde
işe yaradığı ölçülen çözümün anasayfa uyarlaması.
"""

import json
import time
from urllib.parse import urlsplit

from django.core.paginator import Paginator
from django.utils.functional import cached_property
from django.db import DatabaseError
from django.db.models import F, Max, Min, Q
from django.http import Http404
from django.shortcuts import get_object_or_404, render

from taksonomi.models import Ilce, Kategori

from .templatetags.site_etiket import baslikla

from medya.models import FotoGaleri, KoseYazisi, Video, Yazar

from .arama_metni import sorgu_coz
from .canli import anasayfa_verisi, oku
from . import eczane as eczane_sayfa
from .models import Haber, ResmiIlan

# Manşet slaydındaki sayfa sayısı. §35'te 15'ten 5'e inmişti; 30 Ağustos
# 2026'da kullanıcı kararıyla yeniden 15 oldu.
MANSET = 15
# Slaytın altındaki "GÜNÜN MANŞETLERİ" listesi. Slayta girmeyen 10 kayıt,
# taranabilir bir başlık dizisine dönüyor — dilim slayttan SONRA alındığı
# için liste hiçbir manşeti tekrarlamaz.
MANSET_LISTE = 10
IKINCIL = 5
DORTLU = 4
# 11 = 1 geniş + 10 kart. 10 kalsaydı ilk kart iki sütuna yayılınca son
# hücre öksüz kalıyordu (iki sütunlu ızgarada 1 + 9 tek satırı yarım bırakır).
KUTU = 11
# "En çok okunanlar" rayı. 29 Ağustos görsel denetimi: `havuz[:5]` manşetin
# ilk beşinin birebir kopyasıydı — aynı başlık sayfada üç kez görünüyordu
# (slayt, son dakika şeridi, ray). Kutu artık havuzun manşet/ikincil/dörtlü/
# kutu dilimlerinden SONRAKİ beş kaydını alır.
EN_COK = 5
# Anasayfada gösterilen resmî ilan adedi. İki sütunda dört satır: bölüm
# haber akışının önüne geçmeden süzgeci anlamlı kılacak kadar kayıt.
ILAN = 8
BURSASPOR = 6
# Fotoğraflı kartların ALTINDAKİ başlık listesi (29 Ağustos 2026).
# Neden: tablo tam kadro olunca sol sütun 958 px'e çıkıyor, altı kart ise
# 546 px'te bitiyordu — 1280 ve 1600 px'te sağ altta 412 px'lik boşluk
# kalıyordu (ölçüldü). Boşluk kart sayısını artırarak değil, başlık
# listesiyle kapatılıyor: on iki kart bölümü düz bir kart duvarına
# çevirirdi (URUN-PLANI.md §32). Toplam 6 + 7 = 13 kayıt.
#
# 9'dan 7'ye indi: puan tablosunun sütunu 300 -> 380 px'e genişleyince
# (takım adları artık sarmıyor) tablo 865 px'e KISALDI ve bu kez sağ sütun
# 100 px uzun kaldı. Denge satır sayısıyla kuruluyor; satır 41 px, iki satır
# eksilince fark -18 px'e iniyor (ölçüldü).
#
# 31 Ağustos 2026, kullanıcı isteği: liste DÖRT satıra indi. Sayı artık
# sütun dengesinden değil karardan geliyor; denge yine de ölçüldü ve
# işareti değişti — 7 satırda sağ sütun 56 px UZUNDU (794 / 850), 4 satırda
# ~67 px KISA kalıyor. Büyüklük aynı sınıfta, o yüzden yerleşim düzeltmesi
# yapılmadı; sayı bir daha oynatılırsa fark yeniden ölçülmeli.
BURSASPOR_LISTE = 4
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
    # NOT — `.defer("govde")` DENENDİ VE GERİ ALINDI (28 Ağustos 2026).
    # Gerekçe kâğıt üzerinde sağlamdı: gövde ortalama 1.481 karakter ve liste
    # şablonlarının hiçbiri onu basmıyor. Ölçüm gerekçeyi doğrulamadı —
    # 20 satırlık kategori listesinde medyan 4,14 → 3,77 ms (0,38 ms), en iyi
    # değer ise 2,86 → 3,33 ms ile KÖTÜLEŞTİ; kazanç gürültü içinde kaldı.
    # Buna karşılık ertelenmiş alan sessiz bir tuzak taşıyor: gövdeye
    # yanlışlıkla erişen bir kod satır başına ek sorgu açar ve bu fark
    # edilmez. Ölçülemeyen kazanç için tuzak taşınmaz.
    return (Haber.yayindakiler()
            .select_related("kategori", "ilce")
            .prefetch_related("kategori__turler"))


def anasayfa(request):
    """§1'deki sırayı besler. Tek sorgudan dilimlenir; sayılar sözleşmedendir.

    Manşet ile aşağıdaki bloklar aynı havuzdan gelir ve **tekrar etmemeleri**
    gerekir; bu yüzden tek listeden ardışık dilimler alınır.
    """
    gerekli = MANSET + MANSET_LISTE + IKINCIL + DORTLU + KUTU + EN_COK
    havuz = list(_liste()[:gerekli])

    kes = 0
    def al(adet):
        nonlocal kes
        parca = havuz[kes:kes + adet]
        kes += adet
        return parca

    manset = al(MANSET)
    manset_liste = al(MANSET_LISTE)
    ikincil = al(IKINCIL)
    dortlu = al(DORTLU)
    kutular = al(KUTU)

    # "En çok okunanlar" için okunma verisi yok — göçte kurtarılamadı
    # (URUN-PLANI.md §4, madde 8). Başlangıçta editör seçkisi gibi davranıp
    # en yenileri gösteriyoruz; sayaç gerçek veriyle dolunca burası değişir.
    # 29 Ağustos: dilim havuzun SONUNDAN alınıyor — `havuz[:5]` manşetin ilk
    # beşinin kopyasıydı ve aynı başlık sayfada üç kez görünüyordu.
    en_cok = al(EN_COK)

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
    bursaspor_liste = []
    if bursaspor:
        havuz = list(_liste().filter(kategori=bursaspor)
                     [:BURSASPOR + BURSASPOR_LISTE])
        bursaspor_haberleri = havuz[:BURSASPOR]
        bursaspor_liste = havuz[BURSASPOR:]

    return render(request, "anasayfa.html", {
        "anasayfa_mi": True,
        "manset": manset,
        "manset_liste": manset_liste,
        "ikincil": ikincil,
        "dortlu": dortlu,
        "kutular": kutular,
        "bursaspor_haberleri": bursaspor_haberleri,
        "bursaspor_liste": bursaspor_liste,
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


def kategori(request, slug):
    """Kategori listesi. Slug **tür satırından** gelir, kategori adından değil."""
    kategori = get_object_or_404(Kategori, turler__tur=Kategori.TUR_HABER,
                                 turler__slug=slug, aktif=True)
    sayfa = _sayfala(request, _liste().filter(kategori=kategori), sinirli=True)
    return render(request, "kategori.html", {
        "kategori": kategori,
        "baslik": baslikla(kategori.ad),
        "sayfa": sayfa,
    })


def ilce(request, slug):
    ilce = get_object_or_404(Ilce, slug=slug)
    sayfa = _sayfala(request, _liste().filter(ilce=ilce), sinirli=True)
    return render(request, "kategori.html", {
        "baslik": f"{ilce.ad} haberleri",
        "ilce": ilce,
        "sayfa": sayfa,
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
    baglam["yapisal_veri"] = json.dumps(
        eczane_sayfa.yapisal_veri(baglam), ensure_ascii=False)
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
        veri = oku(bilesen) or {}
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
    return render(request, "veri_kaynaklari.html", {
        "baslik": "Veri kaynakları ve kapsam",
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
    """Başlık ve spot üzerinde arama.

    **Hâlâ `icontains`, yani tam tarama.** Türkçe büyük/küçük harf kusuru
    da duruyor (`IŞIK` → 0 sonuç): ikisini de indeks çözecek ve indeks göç
    bittikten sonra kurulacak (URUN-PLANI.md F7 ölçüm turu). Bu görünümde
    yapılanlar migration gerektirmeyen iki kazanımdır:

    1. `_liste()` artık `govde` çekmiyor,
    2. sayım üst sınırla kesiliyor (`SinirliSayfalayici`).

    `arama_metni.sorgu_coz` burada **yalnız kapıda** kullanılıyor: sorgunun
    aranmaya değip değmediğine karar veriyor. Sorgunun kendisi hâlâ ham
    metinle çalışıyor — normalizasyonun sorguya girmesi için normalize
    edilmiş bir alan, yani migration gerekiyor.
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
    sonuc = _liste().filter(
        Q(baslik__icontains=sorgu) | Q(spot__icontains=sorgu)
    ) if aranacak else Haber.objects.none()
    sayfa = _sayfala(request, sonuc, sinirli=aranacak)
    return render(request, "arama.html", {
        "baslik": f"“{sorgu}” için arama sonuçları" if sorgu else "Arama",
        "sorgu": sorgu,
        "uyari": uyari,
        "sayfa": sayfa,
        "toplam": sayfa.paginator.count if aranacak else 0,
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
    numara = request.GET.get("sayfa") or 1
    sinif = SinirliSayfalayici if sinirli else Paginator
    sayfa = sinif(sorgu, boy).get_page(numara)
    # Numaralı sayfalama (29 Ağustos): "1 … 4 [5] 6 … 50". Elided aralık
    # şablondan çağrılamıyor (metot bağımsız değişken istiyor), burada
    # kurulur; parca/sayfalama.html bu listeyi çizer.
    sayfa.numaralar = (list(sayfa.paginator.get_elided_page_range(
        sayfa.number, on_each_side=2, on_ends=1))
        if sayfa.paginator.num_pages > 1 else [])
    return sayfa
