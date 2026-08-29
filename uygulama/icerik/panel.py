"""Panel görünümleri — masanın günlük iş ekranları.

`PANEL-NOTLARI.md` §12 (akış) ve §9 (durum/hazırlık) kararlarını uygular.
Ekran yerleşimi `panel-bugun.html` ve `panel-akis.html` referans
tasarımlarından gelir; kod bizimdir (URUN-PLANI.md §2, yol 1).

**Yetki her görünümde ayrıca denetlenir.** Menüde bir bağlantının
görünmemesi yetki denetimi değildir; adres elle yazılabilir.
"""

import re

from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import Group, User
from django.contrib.auth.views import PasswordChangeView
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from medya.models import FotoGaleri, KoseYazisi, Video, Yazar
from taksonomi.models import Etiket, Ilce, Kategori, KategoriTur, Kaynak, Yonlendirme

from .formlar import (BildirimForm, FotoGaleriForm, GazeteForm, HaberForm,
                      KategoriForm, KaynakForm, KoseYazisiForm, KullaniciForm,
                      ReklamKampanyasiForm, ReklamYuvasiForm, ResmiIlanForm,
                      SonDakikaForm, VideoForm, YazarForm, YorumForm)
from .models import (Bildirim, Gazete, Haber, IkiAdimli, LogKaydi,
                     ReklamKampanyasi, ReklamYuvasi, ResmiIlan, SonDakika,
                     Yorum)

SAYFA_BOYU = 25

# Mevcut panelin liste ekranlarındaki DataTables sayfa boyu seçenekleri
# (ölçüldü: `dt-length-0` seçeneği haber/galeri/videoda 10·25·50, köşe ve
# yazar listelerinde 10·25·50·100). Birleşik küme alındı.
SAYFA_BOYLARI = [10, 25, 50, 100]

# İçerik ekranları "Silinmiş"i gizler (PANEL-NOTLARI.md §9, yumuşak silme).
# Mevcut panelin süzgeçleri de yalnız Aktif/Pasif/Arşiv gösteriyordu.
GORUNUR_DURUMLAR = [
    (Haber.DURUM_AKTIF, "Aktif"),
    (Haber.DURUM_PASIF, "Pasif"),
    (Haber.DURUM_ARSIV, "Arşiv"),
]

# Göçte kurtarılamayan iki sütunun tek yerde tutulan açıklaması. Sütunlar
# silinmedi: eksikliği görünür tutmak, sessizce kaldırmaktan iyidir.
OKUNMA_NOTU = ("Okunma sayıları göçte kurtarılamadı; sayaç yeni sistemde "
               "sıfırdan başlayacak.")
EDITOR_NOTU = ("Kaynak sayfada editör adı yayımlanmıyor, bu yüzden göçte "
               "taşınamadı. Panelden girilen kayıtlarda dolar.")


def _yetkiler(kullanici) -> dict:
    """Şablonun menüyü ve düğmeleri kısması için tek yerde toplanan yetkiler."""
    return {
        "haber_girebilir": kullanici.has_perm("icerik.haber_girme"),
        "yayinlayabilir": kullanici.has_perm("icerik.kendi_haberini_yayinlama"),
        "baskasini_yayinlayabilir": kullanici.has_perm(
            "icerik.baskasinin_haberini_yayinlama"),
        "arsivleyebilir": kullanici.has_perm("icerik.haberi_arsivleme"),
        "mansete_alabilir": kullanici.has_perm("icerik.mansete_alma"),
        "ilan_girebilir": kullanici.has_perm("icerik.resmi_ilan_girme"),
        "taksonomi_duzenler": kullanici.has_perm("icerik.taksonomi_duzenleme"),
        "kullanici_yonetir": kullanici.has_perm("icerik.kullanici_yonetimi"),
        "log_gorur": kullanici.has_perm("icerik.log_goruntuleme"),
        "kose_yonetir": kullanici.has_perm("icerik.kose_yonetimi"),
        "yorum_onaylar": kullanici.has_perm("icerik.yorum_onaylama"),
        "sayfa_duzeni_yapar": kullanici.has_perm("icerik.sayfa_duzeni"),
        "reklam_yonetir": kullanici.has_perm("icerik.reklam_kampanyasi"),
    }


# ---------------------------------------------------------------------------
# Ortak liste altyapısı
#
# Mevcut panelin on liste ekranı tek bir DataTables kabuğunu paylaşıyor:
# üstte süzgeç açılırları + arama, altta aynı biçimli tablo, sonda sayfa boyu.
# Aynı kabuğu burada da tek yerde kuruyoruz — hem yerleşim birebir aynı kalıyor
# hem de ölçüm tek bir şablonu doğruluyor.
#
# Hücreler görünüm katmanında **tip**leriyle üretilir (metin · bağ · görsel ·
# rozet · yok). Şablonda `{{ nesne.alan.alan }}` zinciri kurmak yerine böyle
# yapıldı: liste şablonu modelden bağımsız kalıyor.
# ---------------------------------------------------------------------------


def _metin(deger, sinif=""):
    return {"tur": "metin", "metin": deger if deger not in (None, "") else "—",
            "sinif": sinif}


def _bag(url, metin):
    return {"tur": "bag", "url": url, "metin": metin or "(başlıksız)"}


def _gorsel(yol, alt):
    return {"tur": "gorsel", "yol": yol, "alt": alt} if yol else _yok(
        "Yerelde görsel dosyası yok.")


def _rozet(metin, sinif):
    return {"tur": "rozet", "metin": metin, "sinif": sinif}


def _yok(baslik):
    """Veri yok, ve **neden** yok olduğu hücrenin üstünde duruyor."""
    return {"tur": "yok", "baslik": baslik}


def _tarih(deger):
    return _metin(deger.strftime("%d.%m.%Y %H:%M") if deger else "", "mono")


def _durum_rozeti(nesne):
    sinif = {1: "aktif", 2: "pasif", 3: "silinmis", 4: "arsiv"}.get(nesne.durum, "")
    return _rozet(nesne.get_durum_display(), sinif)


def _sayfa_boyu(request) -> int:
    try:
        boyut = int(request.GET.get("boyut") or SAYFA_BOYU)
    except (TypeError, ValueError):
        boyut = SAYFA_BOYU
    return boyut if boyut in SAYFA_BOYLARI else SAYFA_BOYU


def _boyut_suzgeci(secili) -> dict:
    return {"tur": "secim", "ad": "boyut", "etiket": "Sayfa boyu", "bos": "",
            "secenekler": [(b, f"{b} satır") for b in SAYFA_BOYLARI],
            "deger": str(secili)}


def _liste_ciz(request, *, baslik, bolum, ust_bolum, tablo_adi, basliklar,
               sorgu, satir_kur, suzgecler, temiz_adi, notlar=(), uyari="",
               ust_bilgi="", ek_baglantilar=(), toplu=None):
    """Süzülmüş sorguyu sayfalayıp ortak liste şablonuna verir."""
    basliklar = list(basliklar)
    boyut = _sayfa_boyu(request)
    sayfa = Paginator(sorgu, boyut).get_page(request.GET.get("sayfa") or 1)

    # Sayfalama bağlantısı süzgeçleri korumalı; `sayfa` iki kez yazılmamalı.
    korunan = request.GET.copy()
    korunan.pop("sayfa", None)

    return render(request, "panel/liste.html", {
        "baslik": baslik,
        "bolum": bolum,
        "ust_bolum": ust_bolum,
        "tablo_adi": tablo_adi,
        "basliklar": basliklar,
        "sutun_sayisi": len(basliklar),
        "satirlar": [satir_kur(n) for n in sayfa],
        "sayfa": sayfa,
        "suzgecler": list(suzgecler) + [_boyut_suzgeci(boyut)],
        "temiz_adi": temiz_adi,
        "korunan": korunan.urlencode(),
        "notlar": list(notlar),
        "uyari": uyari,
        "ust_bilgi": ust_bilgi,
        "ek_baglantilar": list(ek_baglantilar),
        "toplu": toplu,
        **_yetkiler(request.user),
    })


def _arama_suzgeci(deger, yer_tutucu="Başlıkta ara"):
    return {"tur": "arama", "ad": "q", "etiket": "Ara", "deger": deger,
            "yer_tutucu": yer_tutucu}


def _durum_suzgeci(deger):
    return {"tur": "secim", "ad": "durum", "etiket": "Durum",
            "bos": "Durum seç", "secenekler": GORUNUR_DURUMLAR, "deger": deger}


def _kategori_suzgeci(deger, tur=Kategori.TUR_HABER):
    """Kategori açılırı — yalnız o türde satırı olan kategoriler.

    Mevcut panelde her tür kendi kategori listesini gösteriyordu (haberde 13,
    fotoda ve videoda başka kümeler); adlar birleşti ama tür ayrımı duruyor.
    """
    kimlikler = KategoriTur.objects.filter(tur=tur).values_list("kategori_id", flat=True)
    secenekler = [(k.pk, k.ad) for k in
                  Kategori.objects.filter(pk__in=kimlikler, aktif=True)]
    return {"tur": "secim", "ad": "kategori", "etiket": "Kategori",
            "bos": "Kategori seç", "secenekler": secenekler, "deger": deger}


def _durumla_suz(sorgu, deger):
    if deger:
        return sorgu.filter(durum=deger)
    return sorgu


@login_required
def bugun(request):
    """Bugün ekranı — masadaki iş kuyruğu.

    Kuyruk §9'daki tanımdır: `durum = Pasif` **ve**
    `hazirlik ∈ (Taslak, İncelemede)`. Mevcut panelde bu ayrım yoktu,
    çünkü Pasif hem "bitmedi" hem "yayından çekildi" demekti.
    """
    kuyruk = (Haber.masadakiler()
              .select_related("kategori", "olusturan")
              .prefetch_related("kategori__turler"))

    bugun_baslangic = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)

    # UCUZ KAPI — 28 Ağustos 2026 ölçümü.
    #
    # Ekran 2.287 ms sürüyordu ve sebebi render değil sorgu planıydı:
    # `durum + hazirlik` indeksi bugünkü veride SEÇİCİ DEĞİL, çünkü göçten
    # gelen 356.839 kaydın **tamamı** `durum=1, hazirlik=''`. SQLite'ın
    # istatistiği (`356839 356839 356839`) "bu alanlar hiçbir şeyi
    # daraltmıyor" diyor, bu yüzden `LIMIT 20` sorgularında indeksi bırakıp
    # tam tarama seçiyor — ve eşleşen kayıt olmadığı için tarama sonuna
    # kadar gidiyor (~840 ms × 3 sorgu).
    #
    # `COUNT` aynı indeksi ÖRTÜCÜ olarak kullanabildiği için 0,1 ms.
    # Kuyruk boşken liste sorgularını hiç çalıştırmıyoruz. Kuyruk doluyken
    # tarama zaten erken biter, yani bu kapı yavaşlatmıyor.
    kuyruk_sayisi = kuyruk.count()
    if kuyruk_sayisi:
        taslaklar = list(kuyruk.filter(hazirlik="taslak")[:20])
        incelemedekiler = list(kuyruk.filter(hazirlik="incelemede")[:20])
        benim = kuyruk.filter(olusturan=request.user).count()
    else:
        taslaklar, incelemedekiler, benim = [], [], 0

    return render(request, "panel/bugun.html", {
        "baslik": "Bugün",
        "bolum": "bugun",
        "ust_bolum": "bugun",
        "taslaklar": taslaklar,
        "incelemedekiler": incelemedekiler,
        "kuyruk_sayisi": kuyruk_sayisi,
        "bugun_yayinlanan": Haber.yayindakiler().filter(
            yayin_zamani__gte=bugun_baslangic).count(),
        "benim_taslaklarim": benim,
        **_yetkiler(request.user),
    })


@login_required
def akis(request):
    """Tüm haberler — daralt-ve-bul (§12), `news_list.php`'nin karşılığı.

    Süzgeçler birleşiktir: editör · kategori · durum · hazırlık · arama tek
    sorguda daraltır. Mevcut panelde süzgeçler ayrı sayfalara dağılmıştı.

    Ölçülen sütun sözleşmesi (`news_list.php`): Başlık · Kategori · Resim ·
    Tarih · Hit · Editör · İşlemler. Süzgeç: Editör Seç · Kategori Seç ·
    Durum Seç. "Hazırlık" bizim eklediğimiz eksendir (§9).
    """
    sorgu, secili = akis_sorgusu(request.GET)

    def satir(haber):
        return {
            "kimlik": haber.pk,
            "duzenle": f"/panel/haber/{haber.pk}",
            "adres": haber.get_absolute_url(),
            "hucreler": [
                _bag(f"/panel/haber/{haber.pk}", haber.baslik),
                _metin(haber.kategori.ad),
                _gorsel(haber.gorsel_yolu(),
                        haber.gorsel_alt or f"{haber.baslik} fotoğrafı"),
                _tarih(haber.yayin_zamani),
                _yok(OKUNMA_NOTU),
                _metin(haber.olusturan.get_username()) if haber.olusturan_id
                else _yok(EDITOR_NOTU),
                _durum_rozeti(haber),
                _rozet(haber.get_hazirlik_display(), haber.hazirlik)
                if haber.durum == Haber.DURUM_PASIF else _metin(""),
            ],
        }

    # Açılır liste **bütün açık hesapları** gösterir, yalnız haber girmiş
    # olanları değil — mevcut panelin "Editör Seç" listesi de öyleydi
    # (17 hesabın tamamı, haberi olmayanlar dâhil).
    #
    # Ölçüm gerekçesi: `User.objects.filter(haberleri__isnull=False)`
    # 96.473 satırlık haber tablosunu tarıyordu, **668 ms**, ve göçle gelen
    # hiçbir kayıtta `olusturan` olmadığı için sonuç **boş** dönüyordu. Aynı
    # liste açık hesaplardan **1,4 ms**'de geliyor.
    editorler = [(k.pk, k.get_username())
                 for k in User.objects.filter(is_active=True).order_by("username")]
    return _liste_ciz(
        request, baslik="Tüm haberler", bolum="akis", ust_bolum="icerik",
        tablo_adi="Haber listesi",
        basliklar=["Başlık", "Kategori", "Resim", "Tarih", "Okunma", "Editör",
                   "Durum", "Hazırlık", "İşlemler"],
        sorgu=sorgu, satir_kur=satir, temiz_adi="panel-akis",
        suzgecler=[
            _arama_suzgeci(secili["q"], "Başlık ya da spotta ara"),
            _kategori_suzgeci(secili["kategori"]),
            _durum_suzgeci(secili["durum"]),
            {"tur": "secim", "ad": "hazirlik", "etiket": "Hazırlık",
             "bos": "Hazırlık seç", "secenekler": Haber.HAZIRLIK,
             "deger": secili["hazirlik"]},
            {"tur": "secim", "ad": "editor", "etiket": "Editör",
             "bos": "Editör seç", "secenekler": editorler,
             "deger": secili["editor"]},
        ],
        toplu=toplu_baglam(request, sorgu, secili),
        notlar=[
            "Okunma: " + OKUNMA_NOTU,
            "Editör sütunu göçle gelen kayıtlarda boştur: " + EDITOR_NOTU,
            "Hazırlık yalnız durum Pasif iken anlamlıdır (§9).",
        ])


@login_required
@permission_required("icerik.haber_girme", raise_exception=True)
def haber_ekle(request):
    form = HaberForm(request.POST or None, kullanici=request.user)
    if request.method == "POST" and form.is_valid():
        haber = _kaydet(form, request)
        return redirect("panel-haber-duzenle", kimlik=haber.pk)
    return render(request, "panel/haber_form.html", {
        "baslik": "Haber ekle",
        "bolum": "haber",
        "ust_bolum": "icerik",
        "form": form,
        "haber": None,
        **_yetkiler(request.user),
    })


@login_required
@permission_required("icerik.haber_girme", raise_exception=True)
def haber_duzenle(request, kimlik):
    haber = get_object_or_404(Haber, pk=kimlik)

    # §11: kendi haberi ile başkasının haberi ayrı kararlardır.
    kendisinin = haber.olusturan_id == request.user.pk
    yayinlayabilir = request.user.has_perm(
        "icerik.kendi_haberini_yayinlama" if kendisinin
        else "icerik.baskasinin_haberini_yayinlama")

    form = HaberForm(request.POST or None, instance=haber, kullanici=request.user)
    if request.method == "POST" and form.is_valid():
        if form.cleaned_data.get("durum") == Haber.DURUM_AKTIF and not yayinlayabilir:
            form.add_error(
                "durum",
                "Bu haberi yayına alma yetkiniz yok. Taslak olarak kaydedebilir "
                "ya da 'Yayına hazır' işaretleyip masaya bırakabilirsiniz.")
        else:
            _kaydet(form, request)
            return redirect("panel-haber-duzenle", kimlik=haber.pk)

    return render(request, "panel/haber_form.html", {
        "baslik": haber.baslik,
        "bolum": "haber",
        "ust_bolum": "icerik",
        "form": form,
        "haber": haber,
        "yayinlayabilir": yayinlayabilir,
        "kendisinin": kendisinin,
        **_yetkiler(request.user),
    })


def _kaydet(form, request):
    """Yeni kayda kimlik ve slug verir.

    **Kimlik adresin parçasıdır** ve göçte eski kimlikler korunmuştur; yeni
    haberler mevcut en büyük kimliğin üstünden devam eder ki eski adreslerle
    hiç çakışmasın.
    """
    from django.utils.text import slugify

    haber = form.save(commit=False)
    if haber.pk is None:
        en_buyuk = Haber.objects.order_by("-id").values_list("id", flat=True).first()
        haber.id = (en_buyuk or 0) + 1
    if not haber.slug:
        haber.slug = slugify(haber.baslik, allow_unicode=False)[:220] or f"haber-{haber.id}"
    if haber.olusturan_id is None:
        haber.olusturan = request.user
    haber.save()
    form.save_m2m()
    form._kategori_degisimini_yonlendir(haber)
    return haber


@login_required
@permission_required("icerik.kullanici_yonetimi", raise_exception=True)
def roller(request):
    """Rol matrisi ekranı — salt okunur döküm.

    Matris kodda tek kaynaktan tutulur (`icerik/yetkiler.py`); ekran onu
    gösterir, düzenlemez. Yetki dağılımını değiştirmek bir **karar**dır ve
    PANEL-NOTLARI.md §11 güncellenmeden yapılmaz.
    """
    from .yetkiler import IKI_ADIMLI_ZORUNLU, MATRIS, OZEL_IZINLER, ROLLER

    adlar = dict(OZEL_IZINLER)
    matris = [
        {"ad": adlar.get(kod, kod), "roller": [rol in roller_ for rol in ROLLER]}
        for kod, roller_ in MATRIS.items()
    ]
    return render(request, "panel/roller.html", {
        "baslik": "Roller",
        "bolum": "roller",
        "ust_bolum": "ayarlar",
        "roller": ROLLER,
        "matris": matris,
        "iki_adimli": sorted(IKI_ADIMLI_ZORUNLU),
        **_yetkiler(request.user),
    })


# ===========================================================================
# Kaynaklar  (Ayarlar › Taksonomi — PANEL-NOTLARI.md §17)
#
# §2'nin açık düzeltme kalemi: "Kaynak listesi 348 kayıt, 6 tekrar, 7 birleşik".
# O sayılar **sağlayıcı panelinin** dökümünden geliyordu. Bizim veritabanımızdaki
# tablo başka bir kaynaktan doldu: `goc_al` kazınan sayfaların künyesinden
# çıkardı. Ekran bu yüzden dökümün sayılarını tekrarlamıyor, **eldeki tabloyu
# ölçüyor**.
#
# Tespitler ölçülmüş bozukluk biçimleridir; hiçbiri kendiliğinden kayıt silmez
# ya da birleştirmez. §17'nin kararı burada da geçerli: **bölme tam otomatik
# yapılamıyor**, son ayrımı editör onaylar.
# ===========================================================================

# PANEL-NOTLARI.md §8'de ölçülerek doğrulanan sadeleştirme kuralı.
_SADELESTIR = str.maketrans({
    "ç": "c", "ğ": "g", "ı": "i", "ö": "o", "ş": "s", "ü": "u",
    "Ç": "c", "Ğ": "g", "İ": "i", "I": "i", "Ö": "o", "Ş": "s", "Ü": "u",
})

# Birleşik kayıt imzası: virgül, eğik çizgi ya da iki kelime arasındaki tire.
# Dökümdeki yedi örneğin tamamı bu üç ayraçtan biriyle kurulmuştu
# (`İHA, DHA` · `İHA - DHA - AA` · `Haber Merkezi / İHA` …).
_BIRLESIK_IMZA = re.compile(r"[,/]|(?<=\w)\s*-\s*(?=\w)")
_ALAN_ADI = re.compile(r"^(https?://)?(www\.)?[\w-]+(\.[\w-]{2,})+/?$", re.I)

# Göç ayıklayıcısının ÖLÇÜLEN kesme uzunluğu: künyeden alınan metin tam 40
# karakterde kesilmiş. Bu, kaydın bir kaynak adı değil **cümle** olduğunun
# imzasıdır (ör. "MHP Genel Başkanı Bahçeli grup toplantıs").
KESME_UZUNLUGU = 40

TESPITLER = [
    ("tekrar", "Birebir tekrar"),
    ("birlesik", "Birleşik kayıt"),
    ("sayisal", "Sayı"),
    ("alan_adi", "Alan adı"),
    ("kesik", "Kesik cümle (40 karakter)"),
    ("cumle", "Cümle parçası"),
    ("kucuk_parca", "Cümleden düşmüş kelime"),
    ("kendi_yayinimiz", "Kendi yayınımız"),
    ("meta_yazar", "Meta Yazar değeri"),
]
TESPIT_ADLARI = dict(TESPITLER)


def kaynak_anahtari(ad: str) -> str:
    """Tekrar aramak için sadeleştirilmiş ad."""
    sade = (ad or "").strip().translate(_SADELESTIR).lower()
    return re.sub(r"[^a-z0-9]+", " ", sade).strip()


def kaynak_tespitleri(ad: str, tekrar_eden_anahtarlar=frozenset()) -> list:
    """Bir kaynak adındaki ölçülebilir bozuklukları döndürür.

    **Ne yapmadığı da önemli:** bu işlev "bu kayıt çöp" demez, yalnız neyin
    şüpheli olduğunu işaretler. Yakalayamadığı bir biçim var ve bilerek
    zorlanmadı: büyük harfle başlayan kısa cümleler (ölçülen örnek
    "Soğuk su içtiler"). Üç kelimelik her adı cümle saymak "Our World in
    Data" ve "Independent Türkçe" gibi gerçek yayınları da yakalardı.
    """
    ad = (ad or "").strip()
    bulgular = []
    anahtar = kaynak_anahtari(ad)

    if anahtar and anahtar in tekrar_eden_anahtarlar:
        bulgular.append("tekrar")
    if _BIRLESIK_IMZA.search(ad):
        bulgular.append("birlesik")
    if ad.isdigit():
        bulgular.append("sayisal")
    if _ALAN_ADI.match(ad) or ad.lower() in ("http", "https", "www"):
        bulgular.append("alan_adi")
    if len(ad) == KESME_UZUNLUGU:
        bulgular.append("kesik")
    if len(ad.split()) >= 5:
        bulgular.append("cumle")
    # Yalniz TEK kelimelik, hic buyuk harf tasimayan adlar. Olcumde bu kosul
    # yoktu ve tespit iki kez fazla atesliyordu: sayilar ("525218") ve
    # kucuk harfle baslayan cumleler ("etkin bir ekonomiye gecisini...")
    # da cumleden dusmus kelime sayiliyordu.
    if (len(ad.split()) == 1 and not any(h.isupper() for h in ad)
            and "sayisal" not in bulgular and "alan_adi" not in bulgular):
        bulgular.append("kucuk_parca")
    # Bosluklar atiliyor: olculen bir kayit "Bu rsahakimiyet" diye gecmis,
    # yani bosluk yanlis yere dusmus. Boslukla arayan kural onu kaciriyordu.
    if "bursahakimiyet" in anahtar.replace(" ", ""):
        bulgular.append("kendi_yayinimiz")
    if anahtar in {kaynak_anahtari(a) for _, a in Haber.META_YAZARLAR}:
        bulgular.append("meta_yazar")
    return bulgular


def _tekrar_eden_anahtarlar() -> set:
    sayac = {}
    for ad in Kaynak.objects.values_list("ad", flat=True):
        anahtar = kaynak_anahtari(ad)
        sayac[anahtar] = sayac.get(anahtar, 0) + 1
    return {a for a, adet in sayac.items() if a and adet > 1}


def kaynak_olcumu() -> dict:
    """Ekranın üstündeki sayılar. Testler de bu işlevi ölçüyor."""
    tekrarlar = _tekrar_eden_anahtarlar()
    kayitlar = list(Kaynak.objects.annotate(haber_sayisi=Count("haberler")))
    dagilim = {}
    sorunlu = 0
    for kaynak in kayitlar:
        bulgular = kaynak_tespitleri(kaynak.ad, tekrarlar)
        if bulgular:
            sorunlu += 1
        for bulgu in bulgular:
            dagilim[bulgu] = dagilim.get(bulgu, 0) + 1
    return {
        "toplam": len(kayitlar),
        "tekil": len({kaynak_anahtari(k.ad) for k in kayitlar}),
        "sorunlu": sorunlu,
        "temiz": len(kayitlar) - sorunlu,
        "tek_haber": len([k for k in kayitlar if k.haber_sayisi == 1]),
        "pasif": len([k for k in kayitlar if not k.aktif]),
        "birlestirilmis": len([k for k in kayitlar if k.birlesti_ile_id]),
        "dagilim": dagilim,
    }


@login_required
@permission_required("icerik.taksonomi_duzenleme", raise_exception=True)
def kaynak_listesi(request):
    tekrarlar = _tekrar_eden_anahtarlar()
    sorgu = (Kaynak.objects.select_related("birlesti_ile")
             .annotate(haber_sayisi=Count("haberler"))
             .order_by("ad", "id"))

    secili_tur = request.GET.get("tur") or ""
    secili_durum = request.GET.get("durum") or ""
    secili_tespit = request.GET.get("tespit") or ""
    aranan = (request.GET.get("q") or "").strip()

    if secili_tur:
        sorgu = sorgu.filter(tur=secili_tur)
    if secili_durum == "aktif":
        sorgu = sorgu.filter(aktif=True)
    elif secili_durum == "pasif":
        sorgu = sorgu.filter(aktif=False)
    if aranan:
        sorgu = sorgu.filter(ad__icontains=aranan)

    # Tespit süzgeci veritabanında yapılamaz — kural adın metnindedir.
    # Python tarafında süzülüyor; tablo yüzlerce satırlık bir ayar tablosu.
    if secili_tespit:
        kimlikler = [k.pk for k in sorgu
                     if secili_tespit in kaynak_tespitleri(k.ad, tekrarlar)]
        sorgu = sorgu.filter(pk__in=kimlikler)

    def satir(kaynak):
        bulgular = kaynak_tespitleri(kaynak.ad, tekrarlar)
        return {
            "duzenle": "/panel/kaynak/%d" % kaynak.pk,
            "adres": "",
            "hucreler": [
                _bag("/panel/kaynak/%d" % kaynak.pk, kaynak.ad),
                _metin(kaynak.get_tur_display()),
                _metin(kaynak.haber_sayisi, "mono"),
                _metin(", ".join(TESPIT_ADLARI[b] for b in bulgular))
                if bulgular else _rozet("Temiz", "aktif"),
                _rozet("Aktif", "aktif") if kaynak.aktif
                else _rozet("Pasif", "pasif"),
                _metin(kaynak.birlesti_ile.ad) if kaynak.birlesti_ile_id
                else _yok("Başka bir kayda birleştirilmedi."),
            ],
        }

    olcum = kaynak_olcumu()
    return _liste_ciz(
        request, baslik="Kaynaklar", bolum="kaynaklar", ust_bolum="ayarlar",
        tablo_adi="Kaynak listesi",
        basliklar=["Ad", "Tür", "Bağlı haber", "Tespit", "Durum",
                   "Birleşti", "İşlemler"],
        sorgu=sorgu, satir_kur=satir, temiz_adi="panel-kaynaklar",
        suzgecler=[
            _arama_suzgeci(aranan, "Kaynak adında ara"),
            {"tur": "secim", "ad": "tur", "etiket": "Tür", "bos": "Tür seç",
             "secenekler": Kaynak.TURLER, "deger": secili_tur},
            {"tur": "secim", "ad": "tespit", "etiket": "Tespit",
             "bos": "Tespit seç", "secenekler": TESPITLER,
             "deger": secili_tespit},
            {"tur": "secim", "ad": "durum", "etiket": "Durum",
             "bos": "Durum seç",
             "secenekler": [("aktif", "Aktif"), ("pasif", "Pasif")],
             "deger": secili_durum},
        ],
        ust_bilgi=("%(toplam)d kayıt · %(tekil)d sadeleşmiş ad · "
                   "%(sorunlu)d kayıtta tespit var · %(temiz)d temiz · "
                   "%(tek_haber)d kayıt yalnız 1 habere bağlı · "
                   "%(pasif)d pasif · %(birlestirilmis)d birleştirilmiş."
                   % olcum),
        uyari=("Bu tablo sağlayıcı panelindeki 348 kayıtlık liste DEĞİLDİR; "
               "göç, kazınan sayfaların künyesinden çıkardı. Tespitler "
               "yalnızca işarettir — birleştirme ve pasifleştirme kararını "
               "editör verir.") if olcum["sorunlu"] else "",
        notlar=[
            "“Kesik cümle” tespiti ölçülmüş bir imzadır: göç ayıklayıcısı "
            "künye metnini tam 40 karakterde kesmiş.",
            "Pasifleştirilen kaynak seçim listesinden düşer ama bağlı "
            "haberler ve bağlantılar durur — kayıt silinmez.",
            "Ajans listesi kapalıdır (§17): AA · DHA · İHA · ANKA. Türü "
            "düzeltmek kaydın kendi formundan yapılır.",
            "Birleştirme bağlantıları hedefe taşır, kaynağı pasife alır ve "
            "“Birleşti” sütununa iz bırakır.",
        ])


@login_required
@permission_required("icerik.taksonomi_duzenleme", raise_exception=True)
def kaynak_duzenle(request, kimlik):
    kaynak = get_object_or_404(Kaynak, pk=kimlik)
    form = KaynakForm(request.POST or None, instance=kaynak)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("panel-kaynak-duzenle", kimlik=kaynak.pk)

    tekrarlar = _tekrar_eden_anahtarlar()
    bulgular = [TESPIT_ADLARI[b] for b in kaynak_tespitleri(kaynak.ad, tekrarlar)]
    return render(request, "panel/kayit_form.html", {
        "baslik": kaynak.ad,
        "bolum": "kaynaklar", "ust_bolum": "ayarlar",
        "form": form,
        "adres": "",
        "geri_adi": "panel-kaynaklar",
        "kilitli": [
            ("Kimlik", kaynak.pk),
            ("Bağlı haber", kaynak.haberler.count()),
            ("Sadeleşmiş ad", kaynak_anahtari(kaynak.ad) or "—"),
            ("Tespit", ", ".join(bulgular) or "yok"),
        ],
        "kilit_notu": "Birleştirme bağlantıları taşır ve bu kaydı pasife "
                      "alır; kayıt silinmez, iz kalır.",
        **_yetkiler(request.user),
    })


# ===========================================================================
# Toplu işlem  (PANEL-NOTLARI.md §12)
#
# Mevcut panelin ölçülmüş hatası: her liste ekranında `dataTables.checkboxes`
# yüklü ve seçim kutuları var, ama "toplu" ve "seçilen" kelimeleri **21
# ekranda 0 kez** geçiyor. **Seçim var, fiil yok.**
#
# Burada ikisi birlikte geliyor. Üç kural:
#
# 1. **Fiil yetkiye bağlı.** Kullanıcının yetkisi olmayan fiil şeritte
#    çizilmez *ve* sunucu tarafında reddedilir. Menüde gizlemek yetki
#    denetimi sayılmaz — aynı kural burada da geçerli.
# 2. **Kategori değişimi adres değiştirir.** Desen `/{kategori}/{slug}-{id}`;
#    kategori değişince kanonik adres değişir. Toplu işlemde bu sessizce
#    olmaz: kaç adresin değişeceği **işlemden önce** söylenir ve her
#    değişen kayıt için 301 yönlendirme yazılır.
# 3. **Yayına alma eşiği toplu işlemde de işler.** §4'ün "gerçekten zorunlu"
#    sütunu (spot · etiket · en az iki paragraf gövde) tek tek kayıtta
#    uygulanıyorsa toplu işlemde de uygulanmalı; yoksa kural bir düğmeyle
#    delinir. Eşiği geçmeyen kayıt atlanır ve sayısı raporlanır.
#
# Fiil/rol eşlemesi §12'nin tablosundan geldi; **tek sapma kategori
# satırıdır** ve bilinçlidir (aşağıdaki nota bakınız).
# ===========================================================================

# Tek POST'ta işlenecek en çok kayıt. Sayfa boyu en fazla 100 olduğu için bu
# sınır arayüzden zor aşılır; asıl işi "süzgeçteki tüm kayıtları seç"
# seçeneğinde ve elle kurulmuş isteklerde yapar.
TOPLU_UST_SINIR = 5000

# Bu sayının üstündeki her işlem onay ekranından geçer. Kategori değişimi
# **sayıdan bağımsız** olarak her zaman onay ister (adres kırar).
TOPLU_ONAY_ESIGI = 100

# `grup`, şeritte fiilin hangi değer seçicisiyle birlikte çizileceğini söyler.
TOPLU_FIILLER = [
    {"kod": "yayina_al", "ad": "Yayına al", "grup": "durum",
     "yetki": "icerik.baskasinin_haberini_yayinlama"},
    {"kod": "yayindan_cek", "ad": "Yayından çek", "grup": "durum",
     "yetki": "icerik.baskasinin_haberini_yayinlama"},
    {"kod": "arsivle", "ad": "Arşive al", "grup": "durum",
     "yetki": "icerik.haberi_arsivleme"},
    {"kod": "hazirlik", "ad": "Hazırlık ata", "grup": "hazirlik",
     "yetki": "icerik.haber_girme"},
    {"kod": "ilce", "ad": "İlçe ata", "grup": "ilce",
     "yetki": "icerik.haber_girme"},
    {"kod": "etiket", "ad": "Etiket ekle", "grup": "etiket",
     "yetki": "icerik.haber_girme"},
    {"kod": "mansete_al", "ad": "Manşete al", "grup": "manset",
     "yetki": "icerik.mansete_alma"},
    {"kod": "mansetten_cikar", "ad": "Manşetten çıkar", "grup": "manset",
     "yetki": "icerik.mansete_alma"},
    # SAPMA — §12'nin tablosu bu satırı Editör ve Sayfa Sekreteri'ne de
    # açıyor; burada yalnız Yayın Yönetmeni'nde. Gerekçe §11'in kendi
    # gerekçesiyle aynı: kategori slug'ı 556.824 adresin parçası ve toplu
    # değişim yüzlerce adresi tek tıkla taşır. Daraltma bilinçlidir ve
    # raporda plan eki olarak yazılıdır; §12 güncellenmeden kalıcı
    # sayılmamalı.
    {"kod": "kategori", "ad": "Kategori değiştir", "grup": "kategori",
     "yetki": "icerik.taksonomi_duzenleme", "tehlikeli": True},
]
TOPLU_FIIL_SOZLUGU = {f["kod"]: f for f in TOPLU_FIILLER}

MANSET_SLOTLARI = [("manset_ana", "Ana manşet"), ("manset_tepe", "Tepe manşet"),
                   ("manset_kare", "Kare manşet")]


# ===========================================================================
# Medya ailelerinde toplu işlem  (köşe · galeri · video)
#
# Akış'taki desenin aynısı, **daraltılmış fiil kümesiyle**: yalnız durum
# fiilleri (yayına al · yayından çek · arşive al). Üç ailenin de modelinde
# `durum` alanı var ve dört değerli enum aynı (§9).
#
# **Kategori değiştirme bilerek YOK.** Galeri ve video adresi
# `/{galeriler|videolar}/{slug}-{katid}/{slug}-{id}` desenindedir; adres
# dilimini kategorinin *tür satırı* taşır (foto = haber kimliği + 200,
# video = + 300) ve taksonomide karşılığı olmayan dilimler var (ölçüldü:
# `haber-213`, galerilerin bir bölümü). Yani orada adres etkisi haberdekiyle
# aynı değil — ayrı bir iştir ve tek tık arkasına konmaz.
#
# **Yayın eşiği de yok.** §4'ün eşiği (spot · iki paragraf gövde · etiket)
# haber formunun sözleşmesidir; medya ailelerinin ölçülmüş bir alan
# sözleşmesi hiç yok (§11). Olmayan bir sözleşmeyi uydurup dayatmıyoruz.
# Yayına almanın tek koşulu yayın zamanının dolu olmasıdır — `yayindakiler()`
# sıralamayı ona dayandırıyor, boşsa kayıt zaten listelenmez.
# ===========================================================================

MEDYA_TOPLU_FIILLER = [
    {"kod": "yayina_al", "ad": "Yayına al", "grup": "durum",
     "yetki": "icerik.baskasinin_haberini_yayinlama"},
    {"kod": "yayindan_cek", "ad": "Yayından çek", "grup": "durum",
     "yetki": "icerik.baskasinin_haberini_yayinlama"},
    {"kod": "arsivle", "ad": "Arşive al", "grup": "durum",
     "yetki": "icerik.haberi_arsivleme"},
]
MEDYA_FIIL_SOZLUGU = {f["kod"]: f for f in MEDYA_TOPLU_FIILLER}

# Aile kodu -> (model, liste adresi, ekranı açan yetkilik).
# Ekran yetkisi ile fiil yetkisi AYRI: köşe listesini Editör görür ama
# arşivleme yetkisi de olmalı ki fiil şeritte çıksın.
MEDYA_AILELERI = {
    "kose":   ("KoseYazisi", "/panel/kose", "icerik.kose_yonetimi"),
    "galeri": ("FotoGaleri", "/panel/galeriler", "icerik.haber_girme"),
    "video":  ("Video", "/panel/videolar", "icerik.haber_girme"),
}


def _medya_modeli(aile):
    return {"kose": KoseYazisi, "galeri": FotoGaleri, "video": Video}[aile]


def medya_toplu_baglam(request, aile, sorgu):
    """Medya listelerinin şerit bağlamı. Fiili olmayan kullanıcıda `None`."""
    fiiller = [f for f in MEDYA_TOPLU_FIILLER
               if request.user.has_perm(f["yetki"])]
    if not fiiller:
        return None
    suzgec = request.GET.copy()
    suzgec.pop("sayfa", None)
    suzgec.pop("boyut", None)
    return {
        "fiiller": fiiller,
        "gruplar": {f["grup"] for f in fiiller},
        "aile": aile,
        "suzgec": suzgec.urlencode(),
        "suzgec_sayisi": sorgu.count(),
        "ust_sinir": TOPLU_UST_SINIR,
        # Medya ailelerinde değer seçici gerektiren fiil yok.
        "hazirliklar": [], "kategoriler": [], "ilceler": [], "etiketler": [],
        "manset_slotlari": [],
    }


@login_required
def medya_toplu_islem(request, aile):
    """Köşe · galeri · video listelerinin toplu durum fiilleri."""
    if aile not in MEDYA_AILELERI:
        from django.http import Http404
        raise Http404("Bilinmeyen aile")
    _, liste_adresi, ekran_yetkisi = MEDYA_AILELERI[aile]

    if request.method != "POST":
        return redirect(liste_adresi)

    from django.core.exceptions import PermissionDenied
    # İki kapı: ekranın kendi yetkisi, sonra fiilin yetkisi.
    if not request.user.has_perm(ekran_yetkisi):
        raise PermissionDenied(f"Bu ekrana erişim yetkiniz yok ({ekran_yetkisi}).")

    fiil = MEDYA_FIIL_SOZLUGU.get(request.POST.get("fiil") or "")
    if fiil is None:
        return _medya_don(request, liste_adresi, "Tanınmayan işlem.", hata=True)
    if not request.user.has_perm(fiil["yetki"]):
        raise PermissionDenied(
            f"“{fiil['ad']}” için yetkiniz yok ({fiil['yetki']}).")

    model = _medya_modeli(aile)
    if request.POST.get("tumu") == "1":
        from django.http import QueryDict
        sorgu = _medya_sorgusu(model, QueryDict(request.POST.get("suzgec") or ""))
    else:
        sorgu = model.objects.filter(
            pk__in=request.POST.getlist("kimlikler")
        ).exclude(durum=model.DURUM_SILINMIS)

    sayi = sorgu.count()
    if not sayi:
        return _medya_don(request, liste_adresi, "Hiç kayıt seçilmedi.", hata=True)
    if sayi > TOPLU_UST_SINIR:
        return _medya_don(
            request, liste_adresi,
            f"{sayi} kayıt seçildi; tek işlemde en çok {TOPLU_UST_SINIR} "
            "kayıt işlenebilir. Süzgeci daraltın.", hata=True)

    if sayi > TOPLU_ONAY_ESIGI and request.POST.get("onay") != "1":
        return render(request, "panel/toplu_onay.html", {
            "baslik": "Toplu işlem onayı",
            "bolum": aile, "ust_bolum": "icerik",
            "fiil": fiil, "sayi": sayi,
            "adres_degisecek": 0, "ornekler": [], "hedef": None,
            "veri": _onay_gizli_alanlari(request),
            "esik": TOPLU_ONAY_ESIGI,
            "geri_adresi": liste_adresi,
            **_yetkiler(request.user),
        })

    if fiil["kod"] == "yayina_al":
        simdi = timezone.now()
        sorgu.filter(yayin_zamani__isnull=True).update(yayin_zamani=simdi)
        sayi = sorgu.update(durum=model.DURUM_AKTIF)
        ozet = f"{sayi} kayıt yayına alındı."
    elif fiil["kod"] == "yayindan_cek":
        sayi = sorgu.update(durum=model.DURUM_PASIF)
        ozet = f"{sayi} kayıt yayından çekildi (Pasif)."
    else:
        sayi = sorgu.update(durum=model.DURUM_ARSIV)
        ozet = f"{sayi} kayıt arşive alındı."
    return _medya_don(request, liste_adresi, ozet)


def _medya_sorgusu(model, parametreler):
    """Medya listelerinin ortak süzgeci.

    Akış'taki gerekçenin aynısı: liste ile toplu işlem aynı süzgeçten
    geçmeli, yoksa "süzgeçteki tümü" ekranda görünenden başka bir küme
    üzerinde çalışır.
    """
    sorgu = model.objects.exclude(durum=model.DURUM_SILINMIS)
    if parametreler.get("durum"):
        sorgu = sorgu.filter(durum=parametreler["durum"])
    if parametreler.get("kategori"):
        sorgu = sorgu.filter(kategori_id=parametreler["kategori"])
    if parametreler.get("yazar"):
        sorgu = sorgu.filter(yazar_id=parametreler["yazar"])
    aranan = (parametreler.get("q") or "").strip()
    if aranan:
        sorgu = sorgu.filter(baslik__icontains=aranan)
    return sorgu


def _medya_don(request, adres, ozet, hata=False):
    if hata:
        messages.error(request, ozet)
    else:
        messages.success(request, ozet)
    nereye = request.POST.get("suzgec") or ""
    return redirect(f"{adres}{'?' + nereye if nereye else ''}")


def akis_sorgusu(parametreler):
    """Akış süzgeci — hem liste hem toplu işlem aynı kaynaktan süzer.

    İkisinin ayrı kopyası olsaydı "süzgeçteki tüm kayıtları seç" seçeneği
    ekranda görünenden **başka** bir küme üzerinde çalışabilirdi. Bu, en
    sessiz veri hatası biçimlerinden biridir.
    """
    sorgu = (Haber.objects
             .select_related("kategori", "ilce", "olusturan")
             .prefetch_related("kategori__turler")
             .exclude(durum=Haber.DURUM_SILINMIS))  # yumuşak silme gizlenir (§9)

    secili = {
        "kategori": parametreler.get("kategori") or "",
        "durum": parametreler.get("durum") or "",
        "hazirlik": parametreler.get("hazirlik") or "",
        "editor": parametreler.get("editor") or "",
        "q": (parametreler.get("q") or "").strip(),
    }
    if secili["kategori"]:
        sorgu = sorgu.filter(kategori_id=secili["kategori"])
    if secili["durum"]:
        sorgu = sorgu.filter(durum=secili["durum"])
    if secili["hazirlik"]:
        sorgu = sorgu.filter(hazirlik=secili["hazirlik"])
    if secili["editor"]:
        sorgu = sorgu.filter(olusturan_id=secili["editor"])
    if secili["q"]:
        sorgu = sorgu.filter(Q(baslik__icontains=secili["q"]) |
                             Q(spot__icontains=secili["q"]))
    return sorgu, secili


def kullanilabilir_fiiller(kullanici) -> list:
    """Kullanıcının gerçekten yapabildiği fiiller. Şerit bunu çizer."""
    return [f for f in TOPLU_FIILLER if kullanici.has_perm(f["yetki"])]


def toplu_baglam(request, sorgu, secili) -> dict:
    """Şeridin ihtiyaç duyduğu her şey. Yetkisi olmayan için `None` döner —
    o zaman seçim kutusu da çizilmez: fiili olmayan seçim, mevcut panelin
    tam da tekrarlanmaması gereken hatasıdır."""
    fiiller = kullanilabilir_fiiller(request.user)
    if not fiiller:
        return None
    suzgec = request.GET.copy()
    suzgec.pop("sayfa", None)
    suzgec.pop("boyut", None)
    return {
        "fiiller": fiiller,
        "gruplar": {f["grup"] for f in fiiller},
        "suzgec": suzgec.urlencode(),
        "suzgec_sayisi": sorgu.count(),
        "hazirliklar": Haber.HAZIRLIK,
        "kategoriler": Kategori.objects.filter(aktif=True),
        "ilceler": Ilce.objects.all(),
        "etiketler": Etiket.objects.all()[:200],
        "manset_slotlari": MANSET_SLOTLARI,
        "ust_sinir": TOPLU_UST_SINIR,
    }


def _secilen_sorgu(request):
    """POST'taki seçimi bir sorguya çevirir.

    İki kip var: işaretlenen kimlikler, ya da "süzgeçteki tüm kayıtlar".
    İkincisinde küme **yeniden süzülerek** kuruluyor; istemciden gelen
    sayıya güvenilmiyor.
    """
    if request.POST.get("tumu") == "1":
        from django.http import QueryDict
        sorgu, _ = akis_sorgusu(QueryDict(request.POST.get("suzgec") or ""))
        return sorgu
    kimlikler = request.POST.getlist("kimlikler")
    return Haber.objects.filter(pk__in=kimlikler).exclude(
        durum=Haber.DURUM_SILINMIS)


def _yayina_hazir_mi(haber) -> bool:
    """§4'ün yayın eşiği: spot · en az iki paragraf gövde · en az bir etiket."""
    from .formlar import EN_AZ_PARAGRAF, HaberForm
    if not (haber.spot or "").strip():
        return False
    if HaberForm._paragraf_sayisi(haber.govde or "") < EN_AZ_PARAGRAF:
        return False
    return haber.etiketler.exists()


@login_required
def toplu_islem(request):
    """Akış ekranının toplu fiilleri. Yalnız POST."""
    if request.method != "POST":
        return redirect("panel-akis")

    fiil_kodu = request.POST.get("fiil") or ""
    fiil = TOPLU_FIIL_SOZLUGU.get(fiil_kodu)
    if fiil is None:
        return _toplu_don(request, "Tanınmayan işlem.", hata=True)

    # Yetki denetimi SUNUCUDA. Şeritte çizilmemesi tek başına yeterli değil;
    # istek elle kurulabilir.
    if not request.user.has_perm(fiil["yetki"]):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied(
            f"“{fiil['ad']}” için yetkiniz yok ({fiil['yetki']}).")

    sorgu = _secilen_sorgu(request)
    sayi = sorgu.count()
    if not sayi:
        return _toplu_don(request, "Hiç kayıt seçilmedi.", hata=True)
    if sayi > TOPLU_UST_SINIR:
        return _toplu_don(
            request,
            f"{sayi} kayıt seçildi; tek işlemde en çok {TOPLU_UST_SINIR} "
            "kayıt işlenebilir. Süzgeci daraltın.", hata=True)

    # Onay adımı: kategori HER ZAMAN (adres kırar), diğerleri eşik üstünde.
    onaylandi = request.POST.get("onay") == "1"
    onay_gerek = fiil.get("tehlikeli") or sayi > TOPLU_ONAY_ESIGI
    if onay_gerek and not onaylandi:
        return _toplu_onay_ekrani(request, fiil, sorgu, sayi)

    islem = {
        "yayina_al": _fiil_yayina_al,
        "yayindan_cek": _fiil_yayindan_cek,
        "arsivle": _fiil_arsivle,
        "hazirlik": _fiil_hazirlik,
        "ilce": _fiil_ilce,
        "etiket": _fiil_etiket,
        "mansete_al": _fiil_mansete_al,
        "mansetten_cikar": _fiil_mansetten_cikar,
        "kategori": _fiil_kategori,
    }[fiil_kodu]
    ozet = islem(request, sorgu)
    return _toplu_don(request, ozet)


def _toplu_don(request, ozet, hata=False):
    if hata:
        messages.error(request, ozet)
    else:
        messages.success(request, ozet)
    nereye = request.POST.get("suzgec") or ""
    return redirect(f"/panel/akis{'?' + nereye if nereye else ''}")


def _toplu_onay_ekrani(request, fiil, sorgu, sayi):
    """Onay ekranı. Kategori değişiminde **adres uyarısı** burada çıkar."""
    adres_degisecek, ornekler, hedef = 0, [], None
    if fiil["kod"] == "kategori":
        hedef = Kategori.objects.filter(
            pk=request.POST.get("kategori_degeri") or 0).first()
        if hedef is None:
            return _toplu_don(request, "Hedef kategori seçilmedi.", hata=True)
        # Kanonik adres yalnız kategorisi GERÇEKTEN değişen kayıtlarda değişir.
        degisenler = sorgu.exclude(kategori_id=hedef.pk)
        adres_degisecek = degisenler.count()
        for haber in degisenler.select_related("kategori").prefetch_related(
                "kategori__turler")[:5]:
            ornekler.append((haber.get_absolute_url(),
                             f"/{hedef.slug_al()}/{haber.slug}-{haber.pk}"))

    return render(request, "panel/toplu_onay.html", {
        "baslik": "Toplu işlem onayı",
        "bolum": "akis", "ust_bolum": "icerik",
        "fiil": fiil,
        "sayi": sayi,
        "adres_degisecek": adres_degisecek,
        "ornekler": ornekler,
        "hedef": hedef,
        "veri": _onay_gizli_alanlari(request),
        "esik": TOPLU_ONAY_ESIGI,
        **_yetkiler(request.user),
    })


def _onay_gizli_alanlari(request) -> list:
    """Onay ekranının POST'u aynen tekrar göndermesi için."""
    alanlar = []
    for ad in ("fiil", "tumu", "suzgec", "hazirlik_degeri", "ilce_degeri",
               "etiket_degeri", "manset_slot", "kategori_degeri"):
        deger = request.POST.get(ad)
        if deger:
            alanlar.append((ad, deger))
    if request.POST.get("tumu") != "1":
        alanlar += [("kimlikler", k) for k in request.POST.getlist("kimlikler")]
    return alanlar


# --- fiiller ---------------------------------------------------------------
#
# Basit durum değişimleri `.update()` ile yapılıyor: toplu işlemde
# `save()`in yan etkilerini (hazırlık varsayılanı, meta yazar türetimi)
# tekrar çalıştırmak istemiyoruz — kayıtlar zaten kurulu.


def _fiil_yayina_al(request, sorgu) -> str:
    hazir, eksik = [], 0
    for haber in sorgu.prefetch_related("etiketler").iterator(chunk_size=500):
        if _yayina_hazir_mi(haber):
            hazir.append(haber.pk)
        else:
            eksik += 1
    simdi = timezone.now()
    for bas in range(0, len(hazir), 500):
        dilim = hazir[bas:bas + 500]
        Haber.objects.filter(pk__in=dilim).update(durum=Haber.DURUM_AKTIF,
                                                  hazirlik="hazir")
        Haber.objects.filter(pk__in=dilim, yayin_zamani__isnull=True).update(
            yayin_zamani=simdi)
    ozet = f"{len(hazir)} haber yayına alındı."
    if eksik:
        ozet += (f" {eksik} kayıt ATLANDI: yayın eşiğini geçmiyor "
                 "(spot · en az iki paragraf gövde · en az bir etiket).")
    return ozet


def _fiil_yayindan_cek(request, sorgu) -> str:
    sayi = sorgu.update(durum=Haber.DURUM_PASIF)
    return f"{sayi} haber yayından çekildi (Pasif)."


def _fiil_arsivle(request, sorgu) -> str:
    sayi = sorgu.update(durum=Haber.DURUM_ARSIV)
    return f"{sayi} haber arşive alındı."


def _fiil_hazirlik(request, sorgu) -> str:
    deger = request.POST.get("hazirlik_degeri") or ""
    if deger not in dict(Haber.HAZIRLIK):
        return "Geçersiz hazırlık değeri."
    sayi = sorgu.update(hazirlik=deger)
    return f"{sayi} haberin hazırlığı “{dict(Haber.HAZIRLIK)[deger]}” yapıldı."


def _fiil_ilce(request, sorgu) -> str:
    """§12: ilçe alanı yeni ve 556.824 haberin hiçbirinde yok; toplu atama
    geçmişe uygulanabilmesi için özellikle önemli."""
    ilce = Ilce.objects.filter(pk=request.POST.get("ilce_degeri") or 0).first()
    if ilce is None:
        return "İlçe seçilmedi."
    sayi = sorgu.update(ilce=ilce)
    return f"{sayi} habere “{ilce.ad}” ilçesi atandı."


def _fiil_etiket(request, sorgu) -> str:
    etiket = Etiket.objects.filter(
        pk=request.POST.get("etiket_degeri") or 0).first()
    if etiket is None:
        return "Etiket seçilmedi."
    kimlikler = list(sorgu.values_list("pk", flat=True))
    for bas in range(0, len(kimlikler), 500):
        etiket.haberler.add(*kimlikler[bas:bas + 500])
    return f"{len(kimlikler)} habere “{etiket.ad}” etiketi eklendi."


def _fiil_mansete_al(request, sorgu) -> str:
    slot = request.POST.get("manset_slot") or ""
    if slot not in dict(MANSET_SLOTLARI):
        return "Manşet türü seçilmedi."
    sayi = sorgu.update(**{slot: True})
    return f"{sayi} haber “{dict(MANSET_SLOTLARI)[slot]}” olarak işaretlendi."


def _fiil_mansetten_cikar(request, sorgu) -> str:
    sayi = sorgu.update(manset_ana=False, manset_tepe=False, manset_kare=False)
    return f"{sayi} haber manşetten çıkarıldı."


def _fiil_kategori(request, sorgu) -> str:
    """Kategori değişimi — **adres değiştirir**, yönlendirme yazar.

    Tek kayıtta `HaberForm._kategori_degisimini_yonlendir` ne yapıyorsa
    burada da o yapılıyor. Toplu işlemde yönlendirme atlanırsa yüzlerce
    eski bağlantı tek tıkla ölür.
    """
    hedef = Kategori.objects.filter(
        pk=request.POST.get("kategori_degeri") or 0).first()
    if hedef is None:
        return "Hedef kategori seçilmedi."
    yeni_slug = hedef.slug_al()

    degisenler = (sorgu.exclude(kategori_id=hedef.pk)
                  .select_related("kategori").prefetch_related("kategori__turler"))
    yonlendirme, kimlikler = [], []
    for haber in degisenler.iterator(chunk_size=500):
        eski_slug = haber.kategori.slug_al()
        kimlikler.append(haber.pk)
        if eski_slug and yeni_slug:
            yonlendirme.append(Yonlendirme(
                eski_yol=f"/{eski_slug}/{haber.slug}-{haber.pk}",
                yeni_yol=f"/{yeni_slug}/{haber.slug}-{haber.pk}",
                kod=301, sebep="Kategori toplu işlemle değiştirildi."))

    # `ignore_conflicts`: aynı eski yol için kayıt zaten varsa üzerine
    # yazılmaz — ilk yönlendirme kanoniktir.
    for bas in range(0, len(yonlendirme), 500):
        Yonlendirme.objects.bulk_create(yonlendirme[bas:bas + 500],
                                        ignore_conflicts=True)
    for bas in range(0, len(kimlikler), 500):
        Haber.objects.filter(pk__in=kimlikler[bas:bas + 500]).update(
            kategori=hedef)
    return (f"{len(kimlikler)} haberin kategorisi “{hedef.ad}” yapıldı; "
            f"{len(yonlendirme)} adres için 301 yönlendirme yazıldı.")


# ===========================================================================
# Manşetler  (`headline_list.php`)
#
# **Defterden slota** — PANEL-NOTLARI.md §14'ün kararı burada uygulanıyor.
# Mevcut ekran bir kayıt defteriydi: her işaretleme yeni satır açıyor,
# ~1.900 kayıt birikmiş ve hiçbiri "şu anda hangisi yayında" demiyordu.
#
# Burada durum haberin kendi üç alanında (`manset_ana` · `manset_tepe` ·
# `manset_kare`) duruyor, yani listenin kendisi zaten "şu an anasayfada ne
# var" sorusunun cevabı. Ayrı bir defter tablosu YOK — olsaydı aynı hatayı
# tekrarlardı.
#
# Ölçülen sütun sözleşmesi: Başlık · Resim · Manşet Türü · İçerik Türü ·
# Editör · Tarih · İşlemler.
# Yetki: `icerik.mansete_alma` — §11'de yalnız Sayfa Sekreteri ve Yayın
# Yönetmeni'nde; "anasayfanın sırasını değiştirmek yayımlamaktan farklı bir
# karardır".
# ===========================================================================

MANSET_ALANLARI = [("ana", "Ana manşet", "manset_ana"),
                   ("tepe", "Tepe manşet", "manset_tepe"),
                   ("kare", "Kare manşet", "manset_kare")]


@login_required
@permission_required("icerik.mansete_alma", raise_exception=True)
def mansetler(request):
    # ÜÇ AYRI İNDEKSLİ SORGU, OR DEĞİL — 28 Ağustos 2026 ölçümü.
    #
    # `Q(a) | Q(b) | Q(c)` biçimini SQLite'ın kısmi indeksleri KARŞILAMIYOR:
    # Django boolean'ı çıplak sütun olarak yazıyor (`WHERE "manset_ana"`) ve
    # çıplak koşullu kısmi indeks yalnız TEK sütunlu sorguda eşleşiyor
    # (ölçüm tablosu `migrations/0006`in başlığında). OR'da hiçbir biçim
    # eşleşmiyor ve sorgu 356.839 satırı tam tarıyordu (752 ms).
    #
    # Üç ayrı sorgu her biri örtücü indeks taramasıyla ~0,2 ms; kimlikler
    # Python'da birleşiyor. Manşetli kayıt sayısı doğası gereği küçük
    # (anasayfada üç slot), yani birleşen küme de küçük.
    kimlikler = set()
    for _kod, _ad, alan in MANSET_ALANLARI:
        # `.order_by()` ŞART: Meta sıralaması (`-yayin_zamani`) planlayıcıyı
        # o indekse çekiyor ve kısmi indeks devre dışı kalıyordu (ölçüldü).
        # Kimlik toplarken sıralamanın zaten anlamı yok.
        kimlikler.update(Haber.objects.filter(**{alan: True})
                         .order_by().values_list("pk", flat=True))
    sorgu = (Haber.objects
             .select_related("kategori", "olusturan")
             .prefetch_related("kategori__turler")
             .exclude(durum=Haber.DURUM_SILINMIS)
             .filter(pk__in=kimlikler))
    secili_slot = request.GET.get("slot") or ""
    secili_durum = request.GET.get("durum") or ""
    aranan = (request.GET.get("q") or "").strip()

    alan = {kod: ad for kod, _, ad in MANSET_ALANLARI}.get(secili_slot)
    if alan:
        sorgu = sorgu.filter(**{alan: True})
    sorgu = _durumla_suz(sorgu, secili_durum)
    if aranan:
        sorgu = sorgu.filter(baslik__icontains=aranan)

    def satir(haber):
        slotlar = ", ".join(ad for _, ad, alan_ in MANSET_ALANLARI
                            if getattr(haber, alan_))
        return {
            "duzenle": f"/panel/haber/{haber.pk}",
            "adres": haber.get_absolute_url(),
            "hucreler": [
                _bag(f"/panel/haber/{haber.pk}", haber.baslik),
                _gorsel(haber.gorsel_yolu(),
                        haber.gorsel_alt or f"{haber.baslik} fotoğrafı"),
                _metin(slotlar),
                _metin(haber.kategori.ad),
                _tarih(haber.yayin_zamani),
                _durum_rozeti(haber),
            ],
        }

    # ALTI SORGU -> BİR. 28 Ağustos ölçümü: manşet alanlarında indeks yok,
    # her sorgu 356.839 satırı tam tarıyordu (~800 ms) ve ekran altı tane
    # çalıştırıyordu. Manşetli kayıt sayısı doğası gereği küçük (anasayfada
    # üç slot var), o yüzden kümeyi bir kez çekip sayımları Python'da
    # yapmak doğru: tarama bir kez oluyor.
    isaretliler = list(sorgu.values_list(
        "manset_ana", "manset_tepe", "manset_kare", "durum"))
    doluluk = ", ".join(
        f"{ad}: {sum(1 for satir in isaretliler if satir[sira])}"
        for sira, (_, ad, _alan) in enumerate(MANSET_ALANLARI))
    yayindan_dusmus = sum(1 for satir in isaretliler
                          if satir[3] != Haber.DURUM_AKTIF)
    return _liste_ciz(
        request, baslik="Manşetler", bolum="mansetler", ust_bolum="icerik",
        tablo_adi="Manşet listesi",
        basliklar=["Başlık", "Resim", "Manşet türü", "Kategori", "Tarih",
                   "Durum", "İşlemler"],
        sorgu=sorgu, satir_kur=satir, temiz_adi="panel-mansetler",
        suzgecler=[
            _arama_suzgeci(aranan),
            {"tur": "secim", "ad": "slot", "etiket": "Manşet türü",
             "bos": "Manşet türü seç",
             "secenekler": [(kod, ad) for kod, ad, _ in MANSET_ALANLARI],
             "deger": secili_slot},
            _durum_suzgeci(secili_durum),
        ],
        ust_bilgi=f"Slot doluluğu — {doluluk}.",
        uyari=(f"{yayindan_dusmus} manşet kaydı yayında değil (Pasif ya da "
               "Arşiv). Anasayfada görünmezler ama işaret üstlerinde duruyor; "
               "manşetten çıkarılmalılar.") if yayindan_dusmus else "",
        notlar=[
            "Manşet, ayrı bir kayıt defteri değil haberin kendi alanıdır: "
            "liste doğrudan “şu an anasayfada ne var” sorusunu cevaplar.",
            "İşaret haber formundaki Manşet bölmesinden konulur ve o bölme "
            "yalnız bu yetkiye sahip rollerde görünür.",
        ])


# ===========================================================================
# Köşe Yazıları  (mevcut panelde `editorialist_list.php`)
#
# Ölçülen sütun sözleşmesi: Başlık · Yazar Adı Soyadı · Gösterim · Tarih ·
# Editör · İşlemler. Süzgeç: Yazar Seç · Durum Seç.
# Yetki: `icerik.kose_yonetimi` — §11'de "Köşe yazısı ve yazar yönetimi"
# satırı Editör ve Yayın Yönetmeni'nde.
# ===========================================================================


@login_required
@permission_required("icerik.kose_yonetimi", raise_exception=True)
def kose_listesi(request):
    sorgu = (KoseYazisi.objects.select_related("yazar", "kategori")
             .exclude(durum=KoseYazisi.DURUM_SILINMIS))
    secili_yazar = request.GET.get("yazar") or ""
    secili_durum = request.GET.get("durum") or ""
    aranan = (request.GET.get("q") or "").strip()

    if secili_yazar:
        sorgu = sorgu.filter(yazar_id=secili_yazar)
    sorgu = _durumla_suz(sorgu, secili_durum)
    if aranan:
        sorgu = sorgu.filter(Q(baslik__icontains=aranan) | Q(spot__icontains=aranan))

    def satir(yazi):
        return {
            "kimlik": yazi.pk,
            "duzenle": f"/panel/kose/{yazi.pk}",
            "adres": yazi.get_absolute_url(),
            "hucreler": [
                _bag(f"/panel/kose/{yazi.pk}", yazi.baslik),
                _metin(yazi.yazar.ad),
                _yok(OKUNMA_NOTU),
                _tarih(yazi.yayin_zamani),
                _yok(EDITOR_NOTU),
                _durum_rozeti(yazi),
            ],
        }

    yazarlar = [(y.pk, y.ad) for y in Yazar.objects.all()]
    return _liste_ciz(
        request, baslik="Köşe yazıları", bolum="kose", ust_bolum="icerik",
        tablo_adi="Köşe yazısı listesi",
        basliklar=["Başlık", "Yazar", "Gösterim", "Tarih", "Editör", "Durum",
                   "İşlemler"],
        sorgu=sorgu, satir_kur=satir, temiz_adi="panel-kose",
        toplu=medya_toplu_baglam(request, "kose", sorgu),
        suzgecler=[
            _arama_suzgeci(aranan),
            {"tur": "secim", "ad": "yazar", "etiket": "Yazar",
             "bos": "Yazar seç", "secenekler": yazarlar, "deger": secili_yazar},
            _durum_suzgeci(secili_durum),
        ],
        notlar=[
            "Gösterim: " + OKUNMA_NOTU,
            "Editör: " + EDITOR_NOTU,
            "Köşe yazısının adresi YAZARA bağlıdır "
            "(/yazarlar/{yazar-slug}-{yazar-id}/{slug}-{id}); yazarı "
            "değiştirmek adresi değiştirir.",
        ])


@login_required
@permission_required("icerik.kose_yonetimi", raise_exception=True)
def kose_duzenle(request, kimlik):
    yazi = get_object_or_404(KoseYazisi.objects.select_related("yazar"), pk=kimlik)
    form = KoseYazisiForm(request.POST or None, instance=yazi)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("panel-kose-duzenle", kimlik=yazi.pk)
    return render(request, "panel/kayit_form.html", {
        "baslik": yazi.baslik,
        "bolum": "kose", "ust_bolum": "icerik",
        "form": form,
        "adres": yazi.get_absolute_url(),
        "geri_adi": "panel-kose",
        "kilitli": [("Kimlik", yazi.pk), ("Slug", yazi.slug)],
        "kilit_notu": "Kimlik ve slug adresin parçasıdır; dondurulmuştur.",
        **_yetkiler(request.user),
    })


# ===========================================================================
# Köşe Yazarları  (`authors_list.php`)
#
# Ölçülen sütunlar: Ad Soyad · Fotoğraf · Tarih · Okunma Sayısı ·
# Toplam Köşe Yazısı · İşlemler. Süzgeç: Durum Seç.
# ===========================================================================


@login_required
@permission_required("icerik.kose_yonetimi", raise_exception=True)
def yazar_listesi(request):
    # `annotate()` GROUP BY kurdugu icin Meta.ordering'i Paginator "siralanmamis"
    # sayiyor; siralama sayfalar arasi tutarlilik icin acikca veriliyor.
    # Yazi sayaci yumusak silinmisleri saymaz: liste ekranlari durum 3'u
    # gizliyor (PANEL-NOTLARI.md 9), sayac da onunla ayni sayiyi vermeli.
    # `annotate()` GROUP BY kurdugu icin Meta.ordering'i Paginator
    # "siralanmamis" sayiyor; siralama acikca veriliyor.
    sorgu = (Yazar.objects
             .annotate(yazi_sayisi=Count(
                 "tum_yazilari",
                 filter=~Q(tum_yazilari__durum=KoseYazisi.DURUM_SILINMIS)))
             .order_by("sira", "ad", "id"))
    secili_durum = request.GET.get("durum") or ""
    secili_kayit = request.GET.get("kayit") or ""
    aranan = (request.GET.get("q") or "").strip()

    if secili_durum == "aktif":
        sorgu = sorgu.filter(aktif=True)
    elif secili_durum == "pasif":
        sorgu = sorgu.filter(aktif=False)
    if secili_kayit == "gecici":
        sorgu = sorgu.filter(sayfasi_tarandi=False)
    elif secili_kayit == "tam":
        sorgu = sorgu.filter(sayfasi_tarandi=True)
    if aranan:
        sorgu = sorgu.filter(ad__icontains=aranan)

    def satir(yazar):
        return {
            "duzenle": f"/panel/yazar/{yazar.pk}",
            "adres": yazar.get_absolute_url(),
            "hucreler": [
                _bag(f"/panel/yazar/{yazar.pk}", yazar.ad),
                _gorsel(yazar.gorsel_yolu(), f"{yazar.ad} portresi"),
                _metin(yazar.unvan),
                _yok(OKUNMA_NOTU),
                _metin(yazar.yazi_sayisi, "mono"),
                _rozet("Aktif", "aktif") if yazar.aktif else _rozet("Pasif", "pasif"),
                _rozet("Tam kayıt", "hazir") if yazar.sayfasi_tarandi
                else _rozet("Geçici", "taslak"),
            ],
        }

    gecici = Yazar.objects.filter(sayfasi_tarandi=False).count()
    return _liste_ciz(
        request, baslik="Köşe yazarları", bolum="yazarlar", ust_bolum="icerik",
        tablo_adi="Köşe yazarı listesi",
        basliklar=["Ad Soyad", "Fotoğraf", "Unvan", "Okunma", "Köşe yazısı",
                   "Durum", "Kayıt", "İşlemler"],
        sorgu=sorgu, satir_kur=satir, temiz_adi="panel-yazarlar",
        suzgecler=[
            _arama_suzgeci(aranan, "Yazar adında ara"),
            {"tur": "secim", "ad": "durum", "etiket": "Durum",
             "bos": "Durum seç",
             "secenekler": [("aktif", "Aktif"), ("pasif", "Pasif")],
             "deger": secili_durum},
            {"tur": "secim", "ad": "kayit", "etiket": "Kayıt",
             "bos": "Kayıt türü",
             "secenekler": [("tam", "Tam kayıt"), ("gecici", "Geçici kayıt")],
             "deger": secili_kayit},
        ],
        uyari=(f"{gecici} yazarın sayfası arşivde yok; kaydı köşe yazısının "
               "künyesinden türetildi. Adı ve unvanı burada tamamlanmalı."
               ) if gecici else "",
        notlar=[
            "Okunma: " + OKUNMA_NOTU,
            "Pasif yazarın sayfası yine açılır — yalnız listelerden düşer; "
            "eski bağlantılar 404 olmamalı.",
        ])


@login_required
@permission_required("icerik.kose_yonetimi", raise_exception=True)
def yazar_duzenle(request, kimlik):
    yazar = get_object_or_404(Yazar, pk=kimlik)
    form = YazarForm(request.POST or None, instance=yazar)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("panel-yazar-duzenle", kimlik=yazar.pk)
    return render(request, "panel/kayit_form.html", {
        "baslik": yazar.ad,
        "bolum": "yazarlar", "ust_bolum": "icerik",
        "form": form,
        "adres": yazar.get_absolute_url(),
        "geri_adi": "panel-yazarlar",
        "kilitli": [("Kimlik", yazar.pk), ("Slug", yazar.slug)],
        "kilit_notu": "Kimlik ve slug adresin parçasıdır; dondurulmuştur.",
        **_yetkiler(request.user),
    })


# ===========================================================================
# Foto Galeri  (`gallery_list.php`)
#
# Ölçülen sütunlar: Başlık · Resim · Kategori · Editör · Yayınlanma Tarihi ·
# Okunma · İşlemler. Süzgeç: Editör Seç · Kategori Seç · Durum Seç.
# Yetki: `icerik.haber_girme`. §11'in 14 yetkiliğinde galeriye ayrı satır
# YOK; içerik girme satırı en yakın karşılıktır ve İlan Sorumlusu'nu dışarıda
# bırakır. Ayrı bir yetkilik açmak matrisi değiştirmek olurdu — o bir karar,
# kod işi değil (raporda plan eki olarak öneriliyor).
# ===========================================================================


@login_required
@permission_required("icerik.haber_girme", raise_exception=True)
def galeri_listesi(request):
    sorgu = (FotoGaleri.objects.select_related("kategori")
             .prefetch_related("kategori__turler")
             .annotate(kare=Count("kareler"))
             .exclude(durum=FotoGaleri.DURUM_SILINMIS)
             .order_by("-yayin_zamani", "-id"))
    secili_kategori = request.GET.get("kategori") or ""
    secili_durum = request.GET.get("durum") or ""
    aranan = (request.GET.get("q") or "").strip()

    if secili_kategori:
        sorgu = sorgu.filter(kategori_id=secili_kategori)
    sorgu = _durumla_suz(sorgu, secili_durum)
    if aranan:
        sorgu = sorgu.filter(baslik__icontains=aranan)

    def satir(galeri):
        return {
            "kimlik": galeri.pk,
            "duzenle": f"/panel/galeri/{galeri.pk}",
            "adres": galeri.get_absolute_url(),
            "hucreler": [
                _bag(f"/panel/galeri/{galeri.pk}", galeri.baslik),
                _gorsel(galeri.gorsel_yolu(),
                        galeri.gorsel_alt or f"{galeri.baslik} kapak fotoğrafı"),
                _metin(galeri.kategori.ad if galeri.kategori_id
                       else galeri.kategori_dilimi),
                _metin(galeri.kare, "mono") if galeri.kare
                else _yok("Kareler kaynaktan alınamadı; kapak var."),
                _tarih(galeri.yayin_zamani),
                _yok(OKUNMA_NOTU),
                _durum_rozeti(galeri),
            ],
        }

    karesiz = FotoGaleri.objects.filter(kareler_eksik=True).count()
    return _liste_ciz(
        request, baslik="Foto galeri", bolum="galeriler", ust_bolum="icerik",
        tablo_adi="Foto galeri listesi",
        basliklar=["Başlık", "Kapak", "Kategori", "Kare", "Tarih", "Okunma",
                   "Durum", "İşlemler"],
        sorgu=sorgu, satir_kur=satir, temiz_adi="panel-galeriler",
        toplu=medya_toplu_baglam(request, "galeri", sorgu),
        suzgecler=[
            _arama_suzgeci(aranan),
            _kategori_suzgeci(secili_kategori, Kategori.TUR_FOTO),
            _durum_suzgeci(secili_durum),
        ],
        uyari=(f"{karesiz} galerinin kareleri eksik. Ölçüldü: kareler kaynak "
               "sayfanın statik HTML'inde yok, yalnız kapak alınabiliyor. "
               "Kareler panelden ya da sağlayıcı dökümünden gelecek."
               ) if karesiz else "",
        notlar=[
            "Okunma: " + OKUNMA_NOTU,
            "Taksonomide karşılığı olmayan kategori dilimleri (ör. haber-213) "
            "ham hâliyle gösterilir; adres yine çalışır.",
        ])


@login_required
@permission_required("icerik.haber_girme", raise_exception=True)
def galeri_duzenle(request, kimlik):
    galeri = get_object_or_404(
        FotoGaleri.objects.select_related("kategori")
        .prefetch_related("kategori__turler"), pk=kimlik)
    form = FotoGaleriForm(request.POST or None, instance=galeri)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("panel-galeri-duzenle", kimlik=galeri.pk)
    return render(request, "panel/kayit_form.html", {
        "baslik": galeri.baslik,
        "bolum": "galeriler", "ust_bolum": "icerik",
        "form": form,
        "adres": galeri.get_absolute_url(),
        "geri_adi": "panel-galeriler",
        "kilitli": [("Kimlik", galeri.pk), ("Slug", galeri.slug),
                    ("Adres dilimi", galeri.adres_dilimi()),
                    ("Kare sayısı", galeri.kare_sayisi)],
        "kilit_notu": "Kimlik, slug ve kategori dilimi adresin parçasıdır.",
        **_yetkiler(request.user),
    })


# ===========================================================================
# Videolar  (`video_list.php`)
#
# Ölçülen sütunlar: Başlık · Kategori · Kapak Görseli · Hit · Tarih ·
# Editör · İşlemler.
# ===========================================================================


@login_required
@permission_required("icerik.haber_girme", raise_exception=True)
def video_listesi(request):
    sorgu = (Video.objects.select_related("kategori")
             .prefetch_related("kategori__turler")
             .exclude(durum=Video.DURUM_SILINMIS))
    secili_kategori = request.GET.get("kategori") or ""
    secili_durum = request.GET.get("durum") or ""
    aranan = (request.GET.get("q") or "").strip()

    if secili_kategori:
        sorgu = sorgu.filter(kategori_id=secili_kategori)
    sorgu = _durumla_suz(sorgu, secili_durum)
    if aranan:
        sorgu = sorgu.filter(baslik__icontains=aranan)

    def satir(video):
        return {
            "kimlik": video.pk,
            "duzenle": f"/panel/video/{video.pk}",
            "adres": video.get_absolute_url(),
            "hucreler": [
                _bag(f"/panel/video/{video.pk}", video.baslik),
                _metin(video.kategori.ad if video.kategori_id
                       else video.kategori_dilimi),
                _gorsel(video.gorsel_yolu(),
                        video.gorsel_alt or f"{video.baslik} kapak görseli"),
                _metin(video.sure_yazi, "mono") if video.sure_yazi
                else _yok("Kaynakta süre bilgisi yok."),
                _tarih(video.yayin_zamani),
                _yok(OKUNMA_NOTU),
                _durum_rozeti(video),
            ],
        }

    oynatmasiz = Video.objects.filter(gomulu_url="").count()
    return _liste_ciz(
        request, baslik="Videolar", bolum="videolar", ust_bolum="icerik",
        tablo_adi="Video listesi",
        basliklar=["Başlık", "Kategori", "Kapak", "Süre", "Tarih", "Okunma",
                   "Durum", "İşlemler"],
        sorgu=sorgu, satir_kur=satir, temiz_adi="panel-videolar",
        toplu=medya_toplu_baglam(request, "video", sorgu),
        suzgecler=[
            _arama_suzgeci(aranan),
            _kategori_suzgeci(secili_kategori, Kategori.TUR_VIDEO),
            _durum_suzgeci(secili_durum),
        ],
        uyari=(f"{oynatmasiz} videoda oynatma adresi yok. Ölçüldü: kaynağın "
               "`contentUrl` alanı videonun değil SAYFANIN adresini taşıyor; "
               "gerçek oynatıcı `embedUrl`de. Boş olan kayıtlarda okura "
               "bağlantı gösterilmiyor.") if oynatmasiz else "",
        notlar=["Okunma: " + OKUNMA_NOTU])


@login_required
@permission_required("icerik.haber_girme", raise_exception=True)
def video_duzenle(request, kimlik):
    video = get_object_or_404(
        Video.objects.select_related("kategori")
        .prefetch_related("kategori__turler"), pk=kimlik)
    form = VideoForm(request.POST or None, instance=video)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("panel-video-duzenle", kimlik=video.pk)
    return render(request, "panel/kayit_form.html", {
        "baslik": video.baslik,
        "bolum": "videolar", "ust_bolum": "icerik",
        "form": form,
        "adres": video.get_absolute_url(),
        "geri_adi": "panel-videolar",
        "kilitli": [("Kimlik", video.pk), ("Slug", video.slug),
                    ("Adres dilimi", video.adres_dilimi()),
                    ("Oynatma adresi", video.oynatma_adresi or "yok")],
        "kilit_notu": "Kimlik, slug ve kategori dilimi adresin parçasıdır.",
        **_yetkiler(request.user),
    })


# ===========================================================================
# Kategoriler  (`categories_list.php`)
#
# Mevcut ekran 37 satır (her tür ayrı kayıt) gösteriyordu. Karar (§18):
# adlar birleşti, **slug'lar donduruldu**. Ekran bu yüzden kategori başına
# tek satır ve üç türün slug'ını yan yana veriyor — §17'deki "birleşme
# haritası" budur.
# Yetki: `icerik.taksonomi_duzenleme` — yalnız Yayın Yönetmeni. Gerekçe §11:
# kategori slug'ı 556.824 adresin parçası.
# ===========================================================================


@login_required
@permission_required("icerik.taksonomi_duzenleme", raise_exception=True)
def kategori_listesi(request):
    # Haber sayımı İSTEĞE BAĞLI. Ölçüldü (96.473 haber): kategori başına
    # gruplu sayım **486 ms** sürüyor ve göç bittiğinde 556.824 satırda
    # birkaç saniyeye çıkar. Ekran 13 satırlık bir ayar ekranı; her açılışta
    # tam tablo taraması yaptırmak yanlış. Sayı gerektiğinde `?sayim=1` ile
    # hesaplanıyor, gerektirmediğinde sütun "hesaplanmadı" diyor.
    sayim = request.GET.get("sayim") == "1"
    sorgu = Kategori.objects.prefetch_related("turler").order_by(
        "sira", "ad", "id")
    if sayim:
        sorgu = sorgu.annotate(haber_sayisi=Count("haberler"))
    secili_tur = request.GET.get("tur") or ""
    aranan = (request.GET.get("q") or "").strip()

    if secili_tur:
        sorgu = sorgu.filter(turler__tur=secili_tur).distinct()
    if aranan:
        sorgu = sorgu.filter(ad__icontains=aranan)

    def dilim(kategori, tur):
        for satir_ in kategori.turler.all():
            if satir_.tur == tur:
                return satir_.adres_dilimi
        return ""

    def satir(kategori):
        haber_slug = kategori.slug_al()
        return {
            "duzenle": f"/panel/kategori/{kategori.pk}",
            "adres": f"/{haber_slug}" if haber_slug else "",
            "hucreler": [
                _metin(kategori.sira, "mono"),
                _bag(f"/panel/kategori/{kategori.pk}", kategori.ad),
                _metin(haber_slug, "mono kilitli") if haber_slug
                else _yok("Bu kategorinin haber türünde satırı yok."),
                _metin(dilim(kategori, Kategori.TUR_FOTO), "mono kilitli")
                if dilim(kategori, Kategori.TUR_FOTO)
                else _yok("Foto türünde kategori kaydı yok."),
                _metin(dilim(kategori, Kategori.TUR_VIDEO), "mono kilitli")
                if dilim(kategori, Kategori.TUR_VIDEO)
                else _yok("Video türünde kategori kaydı yok."),
                _metin(kategori.haber_sayisi, "mono") if sayim
                else _yok("Hesaplanmadı — “Haber sayılarını hesapla” "
                          "bağlantısı bu sütunu doldurur."),
                _rozet("Aktif", "aktif") if kategori.aktif
                else _rozet("Pasif", "pasif"),
            ],
        }

    return _liste_ciz(
        request, baslik="Kategoriler", bolum="kategoriler", ust_bolum="ayarlar",
        tablo_adi="Kategori listesi",
        basliklar=["Sıra", "Kategori", "Haber slug'ı", "Foto dilimi",
                   "Video dilimi", "Haber", "Durum", "İşlemler"],
        sorgu=sorgu, satir_kur=satir, temiz_adi="panel-kategoriler",
        suzgecler=[
            _arama_suzgeci(aranan, "Kategori adında ara"),
            {"tur": "secim", "ad": "tur", "etiket": "Tür", "bos": "Tür seç",
             "secenekler": KategoriTur.TURLER, "deger": secili_tur},
        ],
        uyari="Slug'lar DONDURULMUŞTUR ve panelden değiştirilemez. Kategori "
              "slug'ı /{kategori}/{slug}-{id} adresinin ilk parçası; "
              "değiştirmek 556.824 haber adresini kırar.",
        ust_bilgi="" if sayim else
                  "Haber sayıları hesaplanmadı (tam tablo taraması gerektiriyor).",
        ek_baglantilar=[] if sayim else
                       [("?sayim=1", "Haber sayılarını hesapla")],
        notlar=[
            "Foto ve video dilimi `{slug}-{katid}` biçimindedir; ölçülen "
            "kural foto = haber kimliği + 200, video = + 300 (19/19).",
            "Haber sütunu bu kategoriye bağlı haber kaydı sayısıdır; "
            "göç sürdükçe artar.",
        ])


@login_required
@permission_required("icerik.taksonomi_duzenleme", raise_exception=True)
def kategori_duzenle(request, kimlik):
    kategori = get_object_or_404(Kategori.objects.prefetch_related("turler"),
                                 pk=kimlik)
    form = KategoriForm(request.POST or None, instance=kategori)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("panel-kategori-duzenle", kimlik=kategori.pk)
    kilitli = [("Kimlik", kategori.pk)]
    for satir_ in kategori.turler.all():
        kilitli.append((satir_.get_tur_display(), satir_.adres_dilimi))
    return render(request, "panel/kayit_form.html", {
        "baslik": kategori.ad,
        "bolum": "kategoriler", "ust_bolum": "ayarlar",
        "form": form,
        "adres": f"/{kategori.slug_al()}" if kategori.slug_al() else "",
        "geri_adi": "panel-kategoriler",
        "kilitli": kilitli,
        "kilit_notu": "Slug ve kategori kimlikleri dondurulmuştur (§18). "
                      "Ad değiştirilebilir; adres değişmez.",
        **_yetkiler(request.user),
    })


# ===========================================================================
# Kullanıcılar  (`operator_list` — dökümü YOK, menü betiğinden biliniyor)
#
# §2'nin düzeltme kalemlerinden biri burada karşılanıyor: mevcut sistemde
# **dört hesap "Administrator" adını paylaşıyor** ve log kaydı kimin ne
# yaptığını söyleyemiyor. Ekran çakışan adları sayar ve form aynı görünen
# adın ikinci kez kaydedilmesini engeller.
# ===========================================================================


def _gorunen_ad(kullanici) -> str:
    return (kullanici.get_full_name() or kullanici.get_username()).strip()


@login_required
@permission_required("icerik.kullanici_yonetimi", raise_exception=True)
def kullanici_listesi(request):
    sorgu = User.objects.prefetch_related("groups").order_by("username")
    secili_rol = request.GET.get("rol") or ""
    secili_durum = request.GET.get("durum") or ""
    aranan = (request.GET.get("q") or "").strip()

    if secili_rol:
        sorgu = sorgu.filter(groups__id=secili_rol)
    if secili_durum == "aktif":
        sorgu = sorgu.filter(is_active=True)
    elif secili_durum == "pasif":
        sorgu = sorgu.filter(is_active=False)
    if aranan:
        sorgu = sorgu.filter(Q(username__icontains=aranan) |
                             Q(first_name__icontains=aranan) |
                             Q(last_name__icontains=aranan))

    # Çakışan görünen adlar — §2'deki "4 Administrator" sorununun ölçümü.
    sayac = {}
    for kullanici in User.objects.all():
        sayac[_gorunen_ad(kullanici)] = sayac.get(_gorunen_ad(kullanici), 0) + 1
    cakisanlar = {ad for ad, adet in sayac.items() if adet > 1}

    def satir(kullanici):
        ad = _gorunen_ad(kullanici)
        roller_ = ", ".join(g.name for g in kullanici.groups.all())
        return {
            "duzenle": f"/panel/kullanici/{kullanici.pk}",
            "adres": "",
            "hucreler": [
                _bag(f"/panel/kullanici/{kullanici.pk}", kullanici.get_username()),
                _rozet(ad, "silinmis") if ad in cakisanlar else _metin(ad),
                _metin(kullanici.email),
                _metin(roller_) if roller_ else _yok("Rolü atanmamış."),
                _rozet("Aktif", "aktif") if kullanici.is_active
                else _rozet("Pasif", "pasif"),
                _tarih(kullanici.last_login),
            ],
        }

    roller_secenek = [(g.pk, g.name) for g in Group.objects.all()]
    return _liste_ciz(
        request, baslik="Kullanıcılar", bolum="kullanicilar", ust_bolum="ayarlar",
        tablo_adi="Kullanıcı listesi",
        basliklar=["Kullanıcı adı", "Görünen ad", "E-posta", "Rol", "Durum",
                   "Son giriş", "İşlemler"],
        sorgu=sorgu, satir_kur=satir, temiz_adi="panel-kullanicilar",
        suzgecler=[
            _arama_suzgeci(aranan, "Ad ya da kullanıcı adında ara"),
            {"tur": "secim", "ad": "rol", "etiket": "Rol", "bos": "Rol seç",
             "secenekler": roller_secenek, "deger": secili_rol},
            {"tur": "secim", "ad": "durum", "etiket": "Durum",
             "bos": "Durum seç",
             "secenekler": [("aktif", "Aktif"), ("pasif", "Pasif")],
             "deger": secili_durum},
        ],
        uyari=(f"{len(cakisanlar)} görünen ad birden çok hesapta kullanılıyor: "
               + ", ".join(sorted(cakisanlar)) +
               ". Log kaydı kimin ne yaptığını söyleyemez; adlar "
               "ayrıştırılmalı.") if cakisanlar else "",
        notlar=[
            "Rol, kullanıcının Django grubudur; yetkiler rol matrisinden "
            "gelir (Ayarlar › Roller).",
            "Parola bu ekrandan değiştirilmez; hesap sahibi kendi değiştirir.",
        ])


@login_required
@permission_required("icerik.kullanici_yonetimi", raise_exception=True)
def kullanici_duzenle(request, kimlik):
    kullanici = get_object_or_404(User, pk=kimlik)
    form = KullaniciForm(request.POST or None, instance=kullanici)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("panel-kullanici-duzenle", kimlik=kullanici.pk)
    return render(request, "panel/kayit_form.html", {
        "baslik": _gorunen_ad(kullanici),
        "bolum": "kullanicilar", "ust_bolum": "ayarlar",
        "form": form,
        "adres": "",
        "geri_adi": "panel-kullanicilar",
        "kilitli": [("Kimlik", kullanici.pk),
                    ("Katılma", kullanici.date_joined.strftime("%d.%m.%Y"))],
        "kilit_notu": "Parola bu ekrandan değiştirilmez.",
        **_yetkiler(request.user),
    })


# ===========================================================================
# Şifre  (mevcut panelde ayrı menü maddesi; §17'de "Hesap" sekmesi)
#
# Django'nun kendi `PasswordChangeView`'ı panel kabuğuna giydirildi. Kendi
# parola akışımızı yazmadık: eski parola doğrulaması, parola politikası
# denetimi ve `update_session_auth_hash` (parola değişince oturumun
# düşmemesi) hazır ve sınanmış geliyor.
#
# **Yetki yok, bilerek.** Herkes kendi parolasını değiştirebilmeli; ekran
# yalnız `login_required`. Başkasının parolasını değiştirmek bu ekranın işi
# değil — Kullanıcılar formunda da parola alanı yok (izsiz kimliğe bürünme).
# ===========================================================================


class SifreDegistir(PasswordChangeView):
    template_name = "panel/sifre.html"
    success_url = "/panel/sifre?degisti=1"

    def get_context_data(self, **kwargs):
        baglam = super().get_context_data(**kwargs)
        baglam.update({
            "baslik": "Şifre",
            "bolum": "sifre",
            "ust_bolum": "ayarlar",
            "degisti": self.request.GET.get("degisti") == "1",
            **_yetkiler(self.request.user),
        })
        return baglam


# ===========================================================================
# Model turu ekranları — PANEL-NOTLARI.md §24
#
# Dokuz model, dokuz liste + dokuz düzenleme ekranı. Ortak liste kabuğunu
# (`_liste_ciz`) ve ortak kayıt formunu (`kayit_form.html`) kullanıyorlar;
# yeni bir kabuk yazılmadı.
#
# **Yeni yetkilik AÇILMADI.** §11'in 14 yetkiliği ve 5×14 matrisi olduğu gibi
# duruyor; her ekran en yakın mevcut yetkiliğe bağlandı. Yeni yetkilik açmak
# matrisi değiştirmek olurdu ve o bir karardır, kod işi değil:
#
#   Yorumlar          → yorum_onaylama      (Editör · Yayın Yönetmeni)
#   Log Kayıtları     → log_goruntuleme     (Yayın Yönetmeni)
#   Reklam yuvaları   → sayfa_duzeni        (Sayfa Sekreteri · Yayın Yön.)
#   Reklam kampanyası → reklam_kampanyasi   (İlan Sorumlusu · Yayın Yön.)
#   Gazeteler         → resmi_ilan_girme    (İlan Sorumlusu · Yayın Yön.)
#   Resmî ilanlar     → resmi_ilan_girme    (aynı)
#   Bildirimler       → mansete_alma        (Sayfa Sekreteri · Yayın Yön.)
#   Son dakika        → mansete_alma        (aynı)
#   2FA               → yetkilik YOK, login_required (kendi hesabı)
#
# Bildirim ve son dakika `mansete_alma`ya bağlandı çünkü ikisi de "okurun
# önüne ne çıkacak" kararıdır — manşetle aynı karar sınıfı. Adayı raporda
# plan eki olarak duruyor: ikisine ayrı yetkilik açılabilir.
# ===========================================================================


def _durum_rozeti_genel(nesne, sinif_haritasi):
    return _rozet(nesne.get_durum_display(),
                  sinif_haritasi.get(nesne.durum, ""))


@login_required
@permission_required("icerik.yorum_onaylama", raise_exception=True)
def yorum_listesi(request):
    """Yorumlar — §24.1. Dökümdeki sütun sözleşmesi."""
    sorgu = Yorum.objects.select_related("onaylayan", "duzenleyen")
    secili_durum = request.GET.get("durum") or ""
    secili_tur = request.GET.get("icerik_turu") or ""
    aranan = (request.GET.get("q") or "").strip()
    if secili_durum:
        sorgu = sorgu.filter(durum=secili_durum)
    if secili_tur:
        sorgu = sorgu.filter(icerik_turu=secili_tur)
    if aranan:
        sorgu = sorgu.filter(Q(metin__icontains=aranan) |
                             Q(okur_adi__icontains=aranan))

    sinif = {1: "aktif", 2: "pasif", 3: "silinmis"}

    def satir(y):
        return {
            "kimlik": y.pk,
            "duzenle": f"/panel/yorum/{y.pk}",
            "adres": "",
            "hucreler": [
                _bag(f"/panel/yorum/{y.pk}", y.metin[:60] or "(boş)"),
                _metin(y.okur_adi),
                _metin(y.get_icerik_turu_display()),
                _metin(y.icerik_id, "mono"),
                _metin(y.ip or "", "mono"),
                _tarih(y.tarih),
                _rozet("Düzenlendi", "silinmis") if y.duzenlendi_mi
                else _metin(""),
                _durum_rozeti_genel(y, sinif),
            ],
        }

    bekleyen = Yorum.bekleyenler().count()
    return _liste_ciz(
        request, baslik="Yorumlar", bolum="yorumlar", ust_bolum="etkilesim",
        tablo_adi="Yorum listesi",
        basliklar=["Yorum", "Yorumu yapan", "Sayfa tipi", "İçerik ID", "IP",
                   "Tarih", "İz", "Durum", "İşlemler"],
        sorgu=sorgu, satir_kur=satir, temiz_adi="panel-yorumlar",
        suzgecler=[
            _arama_suzgeci(aranan, "Yorumda ya da adda ara"),
            {"tur": "secim", "ad": "icerik_turu", "etiket": "Sayfa tipi",
             "bos": "Sayfa tipi seç", "secenekler": Yorum.TURLER,
             "deger": secili_tur},
            {"tur": "secim", "ad": "durum", "etiket": "Durum",
             "bos": "Durum seç", "secenekler": Yorum.DURUMLAR,
             "deger": secili_durum},
        ],
        ust_bilgi=f"{bekleyen} yorum karar bekliyor.",
        notlar=[
            "Durum enum'u burada ÜÇ değerli (Aktif · Pasif · Silinmiş); "
            "dökümde ölçüldü, içerik ekranlarındaki dördüncü değer Arşiv "
            "yorumlarda yok (§9).",
            "Yorum metnini değiştirmek gerekçe ister; özgün metin saklanır ve "
            "okur “düzenlendi” işaretini görür (§13).",
        ])


@login_required
@permission_required("icerik.yorum_onaylama", raise_exception=True)
def yorum_duzenle(request, kimlik):
    yorum = get_object_or_404(Yorum, pk=kimlik)
    form = YorumForm(request.POST or None, instance=yorum,
                     kullanici=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("panel-yorum-duzenle", kimlik=yorum.pk)
    kilitli = [("Kimlik", yorum.pk),
               ("Sayfa tipi", yorum.get_icerik_turu_display()),
               ("İçerik ID", yorum.icerik_id),
               ("IP", yorum.ip or "—"),
               ("Tarih", yorum.tarih.strftime("%d.%m.%Y %H:%M"))]
    if yorum.duzenlendi_mi:
        kilitli.append(("Özgün metin", yorum.ozgun_metin[:120] or "—"))
    return render(request, "panel/kayit_form.html", {
        "baslik": f"Yorum #{yorum.pk}",
        "bolum": "yorumlar", "ust_bolum": "etkilesim",
        "form": form, "adres": "", "geri_adi": "panel-yorumlar",
        "kilitli": kilitli,
        "kilit_notu": "Metin değişirse gerekçe zorunlu; özgün hâli saklanır.",
        **_yetkiler(request.user),
    })


@login_required
@permission_required("icerik.log_goruntuleme", raise_exception=True)
def log_listesi(request):
    """Log kayıtları — §24.8. **Eylem günlüğü**, oturum günlüğü değil.

    Mevcut panelin `login_logs` ekranı yalnız oturum açmayı kaydediyordu ve
    hangi kaydın değiştiğini söyleyen tek sütunu yoktu; bu ekran `hedef_tur`
    ve `hedef_id` sütunlarıyla o boşluğu kapatıyor.
    """
    sorgu = LogKaydi.objects.select_related("kullanici")
    secili_fiil = request.GET.get("fiil") or ""
    secili_kullanici = request.GET.get("kullanici") or ""
    aranan = (request.GET.get("q") or "").strip()
    if secili_fiil:
        sorgu = sorgu.filter(fiil=secili_fiil)
    if secili_kullanici:
        sorgu = sorgu.filter(kullanici_id=secili_kullanici)
    if aranan:
        sorgu = sorgu.filter(Q(hedef_tur__icontains=aranan) |
                             Q(gerekce__icontains=aranan))

    def satir(k):
        return {
            "kimlik": k.pk,
            "duzenle": f"/panel/log/{k.pk}",
            "adres": "",
            "hucreler": [
                _tarih(k.zaman),
                _metin(k.kullanici.get_username()),
                _metin(k.get_fiil_display()),
                _metin(k.hedef_tur, "mono") if k.hedef_tur
                else _yok("Hedefsiz kayıt — oturum olayı."),
                _metin(k.hedef_id, "mono") if k.hedef_id
                else _yok("Hedefsiz kayıt."),
                _metin(k.etkilenen_sayisi, "mono"),
                _metin(k.ip or "", "mono"),
            ],
        }

    oturum = LogKaydi.objects.filter(
        fiil__in=("giris", "giris_basarisiz", "cikis")).count()
    kullanicilar = [(u.pk, u.get_username())
                    for u in User.objects.filter(is_active=True).order_by("username")]
    return _liste_ciz(
        request, baslik="Log kayıtları", bolum="log", ust_bolum="ayarlar",
        tablo_adi="Log kaydı listesi",
        basliklar=["Zaman", "Kullanıcı", "Fiil", "Hedef türü", "Hedef",
                   "Etkilenen", "IP", "İşlemler"],
        sorgu=sorgu, satir_kur=satir, temiz_adi="panel-log",
        suzgecler=[
            _arama_suzgeci(aranan, "Hedef türünde ya da gerekçede ara"),
            {"tur": "secim", "ad": "fiil", "etiket": "Fiil", "bos": "Fiil seç",
             "secenekler": LogKaydi.FIILLER, "deger": secili_fiil},
            {"tur": "secim", "ad": "kullanici", "etiket": "Kullanıcı",
             "bos": "Kullanıcı seç", "secenekler": kullanicilar,
             "deger": secili_kullanici},
        ],
        ust_bilgi=f"{sorgu.count()} kayıt · bunun {oturum} tanesi oturum olayı.",
        notlar=[
            "Mevcut panelin log ekranı bir OTURUM AÇMA günlüğüydü; hangi "
            "kaydın değiştiğini söyleyen sütunu yoktu (§24.8).",
            "Saklama önerisi: oturum kayıtları 12 ay, eylem kayıtları süresiz.",
            "Kullanıcı bağı PROTECT: hesap silinirse log okunamaz hâle gelirdi.",
        ])


@login_required
@permission_required("icerik.log_goruntuleme", raise_exception=True)
def log_detay(request, kimlik):
    """Log kaydı **salt okunur**. Düzenlenebilen log, log değildir."""
    kayit = get_object_or_404(LogKaydi.objects.select_related("kullanici"),
                              pk=kimlik)
    return render(request, "panel/log_detay.html", {
        "baslik": f"Log #{kayit.pk}",
        "bolum": "log", "ust_bolum": "ayarlar",
        "kayit": kayit,
        **_yetkiler(request.user),
    })


@login_required
@permission_required("icerik.sayfa_duzeni", raise_exception=True)
def yuva_listesi(request):
    """Reklam yuvaları — §24.4, F7(b)'nin konum + ölçü + cihaz modeli."""
    # `annotate()` GROUP BY kurdugu icin Paginator Meta.ordering'i
    # "siralanmamis" sayiyor; siralama acikca veriliyor.
    sorgu = (ReklamYuvasi.objects.annotate(kampanya=Count("kampanyalar"))
             .order_by("konum", "ad", "id"))
    secili_cihaz = request.GET.get("cihaz") or ""
    aranan = (request.GET.get("q") or "").strip()
    if secili_cihaz:
        sorgu = sorgu.filter(cihaz=secili_cihaz)
    if aranan:
        sorgu = sorgu.filter(Q(ad__icontains=aranan) | Q(konum__icontains=aranan))

    def satir(y):
        return {
            "kimlik": y.pk,
            "duzenle": f"/panel/yuva/{y.pk}",
            "adres": "",
            "hucreler": [
                _bag(f"/panel/yuva/{y.pk}", y.ad),
                _metin(y.konum),
                _metin(y.olcu, "mono") if y.olcu
                else _yok("Ölçüsü kaynakta yoktu; 50 yuvanın 12'sinde eksik."),
                _metin(y.get_cihaz_display()),
                _metin(y.kampanya, "mono"),
                _rozet("Yer tutucu", "pasif") if y.yer_tutucu_mu
                else (_rozet("Aktif", "aktif") if y.aktif
                      else _rozet("Pasif", "pasif")),
            ],
        }

    olcusuz = ReklamYuvasi.objects.filter(genislik__isnull=True).count()
    return _liste_ciz(
        request, baslik="Reklam yuvaları", bolum="yuvalar", ust_bolum="reklam",
        tablo_adi="Reklam yuvası listesi",
        basliklar=["Yuva adı", "Konum", "Ölçü", "Cihaz", "Kampanya", "Durum",
                   "İşlemler"],
        sorgu=sorgu, satir_kur=satir, temiz_adi="panel-yuvalar",
        suzgecler=[
            _arama_suzgeci(aranan, "Yuva adında ya da konumda ara"),
            {"tur": "secim", "ad": "cihaz", "etiket": "Cihaz",
             "bos": "Cihaz seç", "secenekler": ReklamYuvasi.CIHAZLAR,
             "deger": secili_cihaz},
        ],
        uyari=(f"{olcusuz} yuvanın ölçüsü boş. Ölçüldü: sağlayıcıdaki 50 "
               "yuvanın yalnız 6'sı konum + ölçü + cihaz üçlüsüne ayrışıyor, "
               "cihaz bilgisi 43'ünde hiç yok. Taşıma elle yapılır."
               ) if olcusuz else "",
        notlar=[
            "Reklamverenin adı yuvaya değil KAMPANYAYA yazılır (§14); "
            "böylece reklamveren değişince yuva yerinde kalır.",
            "Yuva adı anasayfa şablonlarının çağırdığı addır (F1 ölçütü 3); "
            "değiştirmek bağı koparır.",
        ])


@login_required
@permission_required("icerik.sayfa_duzeni", raise_exception=True)
def yuva_duzenle(request, kimlik):
    yuva = get_object_or_404(ReklamYuvasi, pk=kimlik)
    form = ReklamYuvasiForm(request.POST or None, instance=yuva)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("panel-yuva-duzenle", kimlik=yuva.pk)
    return render(request, "panel/kayit_form.html", {
        "baslik": yuva.ad,
        "bolum": "yuvalar", "ust_bolum": "reklam",
        "form": form, "adres": "", "geri_adi": "panel-yuvalar",
        "kilitli": [("Kimlik", yuva.pk), ("Ölçü", yuva.olcu or "—"),
                    ("Kampanya", yuva.kampanyalar.count())],
        "kilit_notu": "Yuva adını şablonlar kullanıyor; değiştirmeden önce "
                      "anasayfadaki karşılığını kontrol edin.",
        **_yetkiler(request.user),
    })


@login_required
@permission_required("icerik.reklam_kampanyasi", raise_exception=True)
def kampanya_listesi(request):
    """Reklam kampanyaları — dökümdeki `advertisement_list.php` sözleşmesi."""
    sorgu = (ReklamKampanyasi.objects.select_related("olusturan")
             .prefetch_related("yuvalar"))
    secili_yuva = request.GET.get("yuva") or ""
    secili_durum = request.GET.get("durum") or ""
    aranan = (request.GET.get("q") or "").strip()
    if secili_yuva:
        sorgu = sorgu.filter(yuvalar__id=secili_yuva)
    if secili_durum:
        sorgu = sorgu.filter(durum=secili_durum)
    if aranan:
        sorgu = sorgu.filter(baslik__icontains=aranan)

    def satir(k):
        return {
            "kimlik": k.pk,
            "duzenle": f"/panel/kampanya/{k.pk}",
            "adres": k.hedef_adres or "",
            "hucreler": [
                _bag(f"/panel/kampanya/{k.pk}", k.baslik),
                _metin(" / ".join(y.ad for y in k.yuvalar.all()) or "—"),
                _metin(f"{k.baslangic or '—'} → {k.bitis or '—'}", "mono"),
                _metin(k.olusturan.get_username()) if k.olusturan_id
                else _yok(EDITOR_NOTU),
                _rozet("Süresi geçti", "pasif") if k.suresi_gecti_mi()
                else _rozet(k.get_durum_display(),
                            "aktif" if k.durum == 1 else "pasif"),
            ],
        }

    yuvalar = [(y.pk, y.ad) for y in ReklamYuvasi.objects.filter(aktif=True)]
    gecmis = len([k for k in ReklamKampanyasi.objects.all() if k.suresi_gecti_mi()])
    return _liste_ciz(
        request, baslik="Reklam kampanyaları", bolum="kampanyalar",
        ust_bolum="reklam", tablo_adi="Reklam kampanyası listesi",
        basliklar=["Başlık", "Reklam alanı", "Başlangıç / Bitiş", "Editör",
                   "Durum", "İşlemler"],
        sorgu=sorgu, satir_kur=satir, temiz_adi="panel-kampanyalar",
        suzgecler=[
            _arama_suzgeci(aranan, "Kampanya başlığında ara"),
            {"tur": "secim", "ad": "yuva", "etiket": "Reklam alanı",
             "bos": "Reklam alanı seç", "secenekler": yuvalar,
             "deger": secili_yuva},
            {"tur": "secim", "ad": "durum", "etiket": "Durum",
             "bos": "Durum seç", "secenekler": ReklamKampanyasi.DURUMLAR,
             "deger": secili_durum},
        ],
        uyari=(f"{gecmis} kampanyanın bitiş tarihi geçmiş ama kaydı duruyor."
               ) if gecmis else "",
        notlar=["Görsel yerel dosyadan gelir; sayfa internetsiz de açılmalı."])


@login_required
@permission_required("icerik.reklam_kampanyasi", raise_exception=True)
def kampanya_duzenle(request, kimlik):
    kampanya = get_object_or_404(
        ReklamKampanyasi.objects.prefetch_related("yuvalar"), pk=kimlik)
    form = ReklamKampanyasiForm(request.POST or None, instance=kampanya)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("panel-kampanya-duzenle", kimlik=kampanya.pk)
    return render(request, "panel/kayit_form.html", {
        "baslik": kampanya.baslik,
        "bolum": "kampanyalar", "ust_bolum": "reklam",
        "form": form, "adres": kampanya.hedef_adres or "",
        "geri_adi": "panel-kampanyalar",
        "kilitli": [
            ("Kimlik", kampanya.pk),
            ("Yuva", " / ".join(y.ad for y in kampanya.yuvalar.all()) or "—"),
            ("Yuva ölçüleri",
             " / ".join(y.olcu or "—" for y in kampanya.yuvalar.all()) or "—")],
        "kilit_notu": "Yuva tanımı Sayfa Düzeni'ndedir; buradan değiştirilmez. "
                      "Bir kampanya birden çok yuvada yayımlanabilir.",
        **_yetkiler(request.user),
    })


@login_required
@permission_required("icerik.resmi_ilan_girme", raise_exception=True)
def gazete_listesi(request):
    """Gazete listesi — BIK yayın kodu defteri (§24.5)."""
    sorgu = (Gazete.objects.annotate(ilan=Count("ilanlar"))
             .order_by("sira", "ad", "id"))
    aranan = (request.GET.get("q") or "").strip()
    if aranan:
        sorgu = sorgu.filter(Q(ad__icontains=aranan) |
                             Q(bik_kodu__icontains=aranan))

    def satir(g):
        return {
            "kimlik": g.pk,
            "duzenle": f"/panel/gazete/{g.pk}",
            "adres": "",
            "hucreler": [
                _metin(g.sira, "mono"),
                _bag(f"/panel/gazete/{g.pk}", g.ad),
                _metin(g.bik_kodu, "mono kilitli") if g.bik_kodu
                else _yok("BIK kodu girilmemiş."),
                _rozet("Bizim", "aktif") if g.bizim_mi else _metin(""),
                _metin(g.ilan, "mono"),
                _rozet("Aktif", "aktif") if g.aktif else _rozet("Pasif", "pasif"),
            ],
        }

    return _liste_ciz(
        request, baslik="Gazete listesi", bolum="gazeteler", ust_bolum="reklam",
        tablo_adi="Gazete listesi",
        basliklar=["Sıra", "Gazete", "BIK kodu", "", "İlan", "Durum",
                   "İşlemler"],
        sorgu=sorgu, satir_kur=satir, temiz_adi="panel-gazeteler",
        suzgecler=[_arama_suzgeci(aranan, "Gazete adında ya da kodda ara")],
        notlar=[
            "Bursa Hakimiyet'in kendi kodu YYN-000132'dir; resmî ilan "
            "yükümlülüklerinin dayanağı, değiştirilmemeli (§16).",
            "Dökümde 17 kayıt vardı, hepsi YYN kodlu.",
        ])


@login_required
@permission_required("icerik.resmi_ilan_girme", raise_exception=True)
def gazete_duzenle(request, kimlik):
    gazete = get_object_or_404(Gazete, pk=kimlik)
    form = GazeteForm(request.POST or None, instance=gazete)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("panel-gazete-duzenle", kimlik=gazete.pk)
    return render(request, "panel/kayit_form.html", {
        "baslik": gazete.ad,
        "bolum": "gazeteler", "ust_bolum": "reklam",
        "form": form, "adres": "", "geri_adi": "panel-gazeteler",
        "kilitli": [("Kimlik", gazete.pk), ("Bağlı ilan", gazete.ilanlar.count())],
        "kilit_notu": "BIK kodu yasal dayanaktır; değiştirmeden önce doğrulayın.",
        **_yetkiler(request.user),
    })


@login_required
@permission_required("icerik.resmi_ilan_girme", raise_exception=True)
def ilan_listesi(request):
    """Resmî ilanlar — §24.3. Dökümdeki `official_announcement_list.php`."""
    sorgu = ResmiIlan.objects.select_related("gazete", "olusturan")
    secili_tur = request.GET.get("tur") or ""
    secili_durum = request.GET.get("durum") or ""
    aranan = (request.GET.get("q") or "").strip()
    if secili_tur:
        sorgu = sorgu.filter(tur=secili_tur)
    if secili_durum:
        sorgu = sorgu.filter(durum=secili_durum)
    if aranan:
        sorgu = sorgu.filter(baslik__icontains=aranan)

    sinif = {1: "aktif", 2: "pasif", 4: "arsiv"}

    def satir(i):
        return {
            "kimlik": i.pk,
            "duzenle": f"/panel/ilan/{i.pk}",
            "adres": "",
            "hucreler": [
                _metin(i.pk, "mono"),
                _bag(f"/panel/ilan/{i.pk}", i.baslik),
                _metin(i.get_tur_display()),
                _metin(i.yayin_tarihi.strftime("%d.%m.%Y") if i.yayin_tarihi else "",
                       "mono"),
                _metin(i.olusturan.get_username()) if i.olusturan_id
                else _yok(EDITOR_NOTU),
                _durum_rozeti_genel(i, sinif),
            ],
        }

    return _liste_ciz(
        request, baslik="Resmî ilanlar", bolum="ilanlar", ust_bolum="reklam",
        tablo_adi="Resmî ilan listesi",
        basliklar=["ID", "Başlık", "İlan türü", "Tarih", "Editör", "Durum",
                   "İşlemler"],
        sorgu=sorgu, satir_kur=satir, temiz_adi="panel-ilanlar",
        suzgecler=[
            _arama_suzgeci(aranan, "İlan başlığında ara"),
            {"tur": "secim", "ad": "tur", "etiket": "İlan türü",
             "bos": "İlan türü", "secenekler": ResmiIlan.TURLER,
             "deger": secili_tur},
            {"tur": "secim", "ad": "durum", "etiket": "Durum",
             "bos": "Durum seç", "secenekler": ResmiIlan.DURUMLAR,
             "deger": secili_durum},
        ],
        notlar=[
            "Dört tür yasal karşılığı olduğu için korunuyor; ölçülen 24 "
            "kaydın hiçbiri İCRA ya da PERSONEL ALIMI değildi (§16).",
            "ALAN SÖZLEŞMESİ ÖLÇÜLEMEDİ: dökümde ilan ekleme formu yok; "
            "alanlar bizim modelimizden türetildi (§24.3).",
        ])


@login_required
@permission_required("icerik.resmi_ilan_girme", raise_exception=True)
def ilan_duzenle(request, kimlik):
    ilan = get_object_or_404(ResmiIlan.objects.select_related("gazete"), pk=kimlik)
    form = ResmiIlanForm(request.POST or None, instance=ilan)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("panel-ilan-duzenle", kimlik=ilan.pk)
    return render(request, "panel/kayit_form.html", {
        "baslik": ilan.baslik,
        "bolum": "ilanlar", "ust_bolum": "reklam",
        "form": form, "adres": "", "geri_adi": "panel-ilanlar",
        "kilitli": [("Kimlik", ilan.pk), ("Tür", ilan.get_tur_display()),
                    ("Gazete", ilan.gazete.ad if ilan.gazete_id else "—")],
        "kilit_notu": "Resmî ilan BIK yükümlülüğü taşır ve yasal sonuç doğurur.",
        **_yetkiler(request.user),
    })


@login_required
@permission_required("icerik.mansete_alma", raise_exception=True)
def bildirim_listesi(request):
    """Bildirimler — §24.9. Açılma oranı **türetiliyor**, saklanmıyor."""
    sorgu = Bildirim.objects.select_related("gonderen")
    secili_tur = request.GET.get("icerik_turu") or ""
    aranan = (request.GET.get("q") or "").strip()
    if secili_tur:
        sorgu = sorgu.filter(icerik_turu=secili_tur)
    if aranan:
        sorgu = sorgu.filter(baslik__icontains=aranan)

    def satir(b):
        return {
            "kimlik": b.pk,
            "duzenle": f"/panel/bildirim/{b.pk}",
            "adres": "",
            "hucreler": [
                _tarih(b.gonderim_zamani),
                _metin(b.get_icerik_turu_display()),
                _bag(f"/panel/bildirim/{b.pk}", b.baslik),
                _metin(b.hedef_sayisi, "mono"),
                _metin(b.acan_sayisi, "mono"),
                _metin("%%%.2f" % b.acilma_orani, "mono") if b.hedef_sayisi
                else _yok("Henüz gönderilmedi."),
            ],
        }

    gonderilen = [b for b in Bildirim.objects.all() if b.hedef_sayisi]
    ortalama = (sum(b.acilma_orani for b in gonderilen) / len(gonderilen)
                if gonderilen else 0.0)
    return _liste_ciz(
        request, baslik="Bildirimler", bolum="bildirimler",
        ust_bolum="etkilesim", tablo_adi="Bildirim listesi",
        basliklar=["Tarih", "Veri kaynağı", "Bildirim", "Hedef kişi",
                   "Açan kişi", "Açılma oranı", "İşlemler"],
        sorgu=sorgu, satir_kur=satir, temiz_adi="panel-bildirimler",
        suzgecler=[
            _arama_suzgeci(aranan, "Bildirim başlığında ara"),
            {"tur": "secim", "ad": "icerik_turu", "etiket": "Veri kaynağı",
             "bos": "Veri kaynağı seç", "secenekler": Yorum.TURLER,
             "deger": secili_tur},
        ],
        ust_bilgi=("Ortalama açılma oranı %%%.2f (%d gönderim)."
                   % (ortalama, len(gonderilen))) if gonderilen else
                  "Henüz gönderim yok.",
        notlar=[
            "Oran SAKLANMIYOR, hedef ve açan sayısından türetiliyor. Mevcut "
            "panelde iki sütun vardı ama oran hiçbir yerde hesaplanmıyordu (§13).",
            "Ölçülen geçmiş: 10 gönderimde ortalama %0,21; hedef kitle "
            "9.207 → 22.683'e çıkarken açan sayısı 21-47 bandında sabit kaldı.",
            "Bu ekran yalnız KAYDI tutar; gerçek gönderim altyapısı kapsam dışı.",
        ])


@login_required
@permission_required("icerik.mansete_alma", raise_exception=True)
def bildirim_duzenle(request, kimlik):
    bildirim = get_object_or_404(Bildirim, pk=kimlik)
    form = BildirimForm(request.POST or None, instance=bildirim)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("panel-bildirim-duzenle", kimlik=bildirim.pk)
    return render(request, "panel/kayit_form.html", {
        "baslik": bildirim.baslik,
        "bolum": "bildirimler", "ust_bolum": "etkilesim",
        "form": form, "adres": "", "geri_adi": "panel-bildirimler",
        "kilitli": [("Kimlik", bildirim.pk),
                    ("Açılma oranı", "%%%.2f" % bildirim.acilma_orani),
                    ("Gönderen", bildirim.gonderen.get_username()
                     if bildirim.gonderen_id else "—")],
        "kilit_notu": "Oran türetilir; hedef ve açan sayısından hesaplanır.",
        **_yetkiler(request.user),
    })


@login_required
@permission_required("icerik.mansete_alma", raise_exception=True)
def son_dakika_listesi(request):
    """Son dakika — §24.2. Ayrı model, haberde bayrak değil."""
    sorgu = SonDakika.objects.select_related("haber", "olusturan")
    secili_durum = request.GET.get("durum") or ""
    aranan = (request.GET.get("q") or "").strip()
    if secili_durum == "aktif":
        sorgu = sorgu.filter(aktif=True)
    elif secili_durum == "pasif":
        sorgu = sorgu.filter(aktif=False)
    if aranan:
        sorgu = sorgu.filter(baslik__icontains=aranan)

    def satir(s):
        return {
            "kimlik": s.pk,
            "duzenle": f"/panel/son-dakika/{s.pk}",
            "adres": s.yol,
            "hucreler": [
                _metin(s.sira, "mono"),
                _bag(f"/panel/son-dakika/{s.pk}", s.baslik),
                _metin(s.yol, "mono") if s.yol
                else _yok("Ne serbest adres ne bağlı haber var."),
                _metin(s.olusturan.get_username()) if s.olusturan_id
                else _yok(EDITOR_NOTU),
                _tarih(s.baslangic),
                _rozet("Aktif", "aktif") if s.aktif else _rozet("Pasif", "pasif"),
            ],
        }

    bantta = SonDakika.bandakiler().count()
    return _liste_ciz(
        request, baslik="Son dakika", bolum="son-dakika", ust_bolum="icerik",
        tablo_adi="Son dakika listesi",
        basliklar=["Sıra", "Başlık", "Adres", "Editör", "Başlangıç", "Durum",
                   "İşlemler"],
        sorgu=sorgu, satir_kur=satir, temiz_adi="panel-son-dakika",
        suzgecler=[
            _arama_suzgeci(aranan, "Bant başlığında ara"),
            {"tur": "secim", "ad": "durum", "etiket": "Durum",
             "bos": "Durum seç",
             "secenekler": [("aktif", "Aktif"), ("pasif", "Pasif")],
             "deger": secili_durum},
        ],
        ust_bilgi=f"Şu an bantta görünen kayıt: {bantta}.",
        notlar=[
            "Ayrı model, haberde bayrak DEĞİL: dökümdeki kayıt serbest URL "
            "taşıyor ve başlık habere ait değil (§24.2).",
            "Bant boşsa site bugünkü davranışına düşer — en yeni yayındaki "
            "haberler gösterilir; bugünkü davranış kaybolmadı.",
            "§18 m.4: sağlayıcıdaki en yeni kayıt 2025-12-20; göçte veri "
            "taşınmadı, davranış yeniden kuruldu.",
        ])


@login_required
@permission_required("icerik.mansete_alma", raise_exception=True)
def son_dakika_duzenle(request, kimlik):
    kayit = get_object_or_404(SonDakika.objects.select_related("haber"), pk=kimlik)
    form = SonDakikaForm(request.POST or None, instance=kayit)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("panel-son-dakika-duzenle", kimlik=kayit.pk)
    return render(request, "panel/kayit_form.html", {
        "baslik": kayit.baslik,
        "bolum": "son-dakika", "ust_bolum": "icerik",
        "form": form, "adres": kayit.yol, "geri_adi": "panel-son-dakika",
        "kilitli": [("Kimlik", kayit.pk),
                    ("Bantta mı", "evet" if kayit in SonDakika.bandakiler() else "hayır"),
                    ("Bağlı haber", kayit.haber_id or "—")],
        "kilit_notu": "Serbest adres varsa bağlı haberin adresi kullanılmaz.",
        **_yetkiler(request.user),
    })


@login_required
def iki_adimli(request):
    """2FA durumu — **salt okunur, kurulum akışı bilerek YOK** (§24.10).

    Gizli anahtarın nasıl saklanacağı bir güvenlik kararıdır ve kullanıcıya
    soruldu (28 Ağustos 2026); cevap gelmedi. Bu ekran durumu gösterir,
    kurulum yaptırmaz.

    **Yarım bir 2FA, olmayan 2FA'dan tehlikelidir**: kullanıcı korunduğunu
    sanır. Bu yüzden `gizli_anahtar` alanına yazan hiçbir yol açılmadı.

    Yetkilik yok, `login_required` yeter: herkes kendi hesabının durumunu
    görebilmeli — Şifre ekranıyla aynı gerekçe.
    """
    from .yetkiler import IKI_ADIMLI_ZORUNLU
    kayit = IkiAdimli.objects.filter(kullanici=request.user).first()
    roller = {g.name for g in request.user.groups.all()}
    return render(request, "panel/iki_adimli.html", {
        "baslik": "İki adımlı doğrulama",
        "bolum": "iki-adimli", "ust_bolum": "ayarlar",
        "kayit": kayit,
        "zorunlu_mu": bool(roller & IKI_ADIMLI_ZORUNLU),
        "zorunlu_roller": sorted(IKI_ADIMLI_ZORUNLU),
        "yontemler": IkiAdimli.YONTEMLER,
        **_yetkiler(request.user),
    })


# ===========================================================================
# Haber arama ucu — ilgili haber seçicisinin kaynağı (28 Ağustos 2026)
#
# `/panel/haber/ekle` sayfası 356.839 `<option>` basıyordu: 36,5 MB ve
# 32,7 sn. Alan artık yalnız seçilileri basıyor, yenisi buradan geliyor.
#
# İkinci bir arama mantığı YAZILMADI: `arama_metni.sorgu_coz` sitenin
# aramasında ne yapıyorsa burada da onu yapıyor — durak kelime elemesi ve
# en az uzunluk kapısı. Motor tarafı (normalize alan + indeks) F7'nin işi;
# burada da ham `icontains` kullanılıyor, tıpkı `icerik/views.py`de olduğu
# gibi. İki yerde iki farklı arama davranışı olmasın diye.
# ===========================================================================

HABER_ARA_EN_COK = 12


@login_required
@permission_required("icerik.haber_girme", raise_exception=True)
def haber_ara(request):
    """İlgili haber seçicisi için JSON arama. Yalnız okuma yapar."""
    from django.http import JsonResponse

    from .arama_metni import sorgu_coz

    sorgu = (request.GET.get("q") or "").strip()
    cozum = sorgu_coz(sorgu)
    if not cozum:
        sebep = ("Çok genel kelimelerle arama yapılamıyor."
                 if cozum.sebep == "hepsi_durak"
                 else "Aramak istediğiniz kelimeyi yazın.")
        return JsonResponse({"sonuclar": [], "uyari": sebep})
    if max(len(t.kelime) for t in cozum.terimler) < 3:
        return JsonResponse({"sonuclar": [],
                             "uyari": "En az 3 harflik bir kelime yazın."})

    haric = request.GET.get("haric") or 0
    bulunan = (Haber.objects.filter(baslik__icontains=sorgu)
               .exclude(pk=haric)
               .exclude(durum=Haber.DURUM_SILINMIS)
               .only("id", "baslik", "yayin_zamani")
               .order_by()[:HABER_ARA_EN_COK])
    return JsonResponse({"sonuclar": [
        {"id": h.pk,
         "etiket": f"[{h.pk}] {h.baslik[:70]}",
         "tarih": h.yayin_zamani.strftime("%d.%m.%Y") if h.yayin_zamani else ""}
        for h in bulunan], "uyari": ""})


@login_required
@permission_required("icerik.haber_girme", raise_exception=True)
def galeri_ara(request):
    """Bağlı galeri seçicisi için JSON arama.

    `haber_ara` ile aynı kapı, aynı gerekçe: ikinci bir arama mantığı
    yazılmadı, `arama_metni.sorgu_coz` kullanılıyor.
    """
    from django.http import JsonResponse

    from .arama_metni import sorgu_coz

    sorgu = (request.GET.get("q") or "").strip()
    cozum = sorgu_coz(sorgu)
    if not cozum:
        return JsonResponse({"sonuclar": [], "uyari":
                             "Aramak istediğiniz kelimeyi yazın."})
    if max(len(t.kelime) for t in cozum.terimler) < 3:
        return JsonResponse({"sonuclar": [],
                             "uyari": "En az 3 harflik bir kelime yazın."})

    bulunan = (FotoGaleri.objects.filter(baslik__icontains=sorgu)
               .exclude(durum=FotoGaleri.DURUM_SILINMIS)
               .only("id", "baslik", "yayin_zamani")
               .order_by()[:HABER_ARA_EN_COK])
    return JsonResponse({"sonuclar": [
        {"id": g.pk,
         "etiket": f"[{g.pk}] {g.baslik[:70]}",
         "tarih": g.yayin_zamani.strftime("%d.%m.%Y") if g.yayin_zamani else ""}
        for g in bulunan], "uyari": ""})
