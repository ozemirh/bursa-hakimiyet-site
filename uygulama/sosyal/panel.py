"""Sosyal medya ekranları — kuyruk, gönderi ve hesaplar.

Liste kabuğu `icerik.panel`den geliyor: aynı süzgeç şeridi, aynı tablo,
aynı sayfalama. İkinci bir liste altyapısı yazmak, ölçülmüş tek şablonu
ikiye bölmek olurdu.

## Yetkilik açılmadı

§24'ün kuralı korundu: yeni bir yetkilik tanımlanmadı, iki ekran mevcut
on dörtten birine bağlandı.

    Kuyruk ve gönderim  →  icerik.kendi_haberini_yayinlama
    Hesaplar (jetonlar) →  icerik.kullanici_yonetimi

Gerekçe: sosyal paylaşım **yayımlamanın devamıdır**, dolayısıyla yayına
alabilen paylaşabilir. Jeton ise hesabın anahtarıdır; onu görmek kullanıcı
yönetimiyle aynı ağırlıkta bir iştir.

## Gönderim isteğin içinde

"Şimdi gönder" düğmesi ağ isteğini kullanıcıyı bekleterek yapar ve bu
bilinçli: editör düğmeye bastığında sonucu görmek ister. Kendiliğinden
gönderim ise istek dışında, `manage.py sosyal_gonder` ile.
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from icerik.models import Haber
from icerik.panel import (_bag, _liste_ciz, _metin, _rozet, _tarih, _yetkiler,
                          _yok, _arama_suzgeci)

from . import kuyruk
from .formlar import SosyalGonderiForm, SosyalHesapForm, YeniGonderiForm
from .metin import SINIRLAR, olculen_uzunluk, paylas_adresi
from .models import SosyalGonderi, SosyalHesap

# "Şimdi gönder" tek istekte en çok kaç satır işler. Sınır ağ süresinden
# geliyor: 15 sn zaman aşımı × 10 satır en kötü hâlde 2,5 dakika eder ve
# tarayıcı bunu bekleyemez.
ELDEN_SINIR = 10

YETKI_KUYRUK = "icerik.kendi_haberini_yayinlama"
YETKI_HESAP = "icerik.kullanici_yonetimi"


def _durum_suzgeci(deger):
    return {"tur": "secim", "ad": "durum", "etiket": "Durum",
            "bos": "Durum seç", "secenekler": SosyalGonderi.DURUMLAR,
            "deger": deger}


def _platform_suzgeci(deger):
    return {"tur": "secim", "ad": "platform", "etiket": "Platform",
            "bos": "Platform seç", "secenekler": SosyalHesap.PLATFORMLAR,
            "deger": deger}


@login_required
@permission_required(YETKI_KUYRUK, raise_exception=True)
def gonderi_listesi(request):
    sorgu = (SosyalGonderi.objects
             .select_related("haber", "haber__kategori", "hesap"))
    durum = request.GET.get("durum") or ""
    platform = request.GET.get("platform") or ""
    aranan = (request.GET.get("q") or "").strip()
    if durum:
        sorgu = sorgu.filter(durum=durum)
    if platform:
        sorgu = sorgu.filter(hesap__platform=platform)
    if aranan:
        sorgu = sorgu.filter(haber__baslik__icontains=aranan)

    def satir(g):
        return {
            "kimlik": g.pk,
            "duzenle": f"/panel/sosyal/{g.pk}",
            "adres": g.dis_adres,
            "hucreler": [
                _bag(f"/panel/haber/{g.haber_id}", f"[{g.haber_id}] "
                     f"{g.haber.baslik[:60]}"),
                _metin(g.hesap.ad),
                _metin(g.hesap.get_platform_display()),
                _rozet(g.get_durum_display(), g.durum_sinifi()),
                _tarih(g.olusma_zamani),
                _tarih(g.gonderim_zamani) if g.gonderim_zamani
                else _yok("Henüz gönderilmedi."),
            ],
        }

    bekleyen = SosyalGonderi.bekleyenler().count()
    elle = SosyalGonderi.objects.filter(durum=SosyalGonderi.ELLE).count()
    hatali = SosyalGonderi.objects.filter(durum=SosyalGonderi.HATA).count()
    return _liste_ciz(
        request, baslik="Sosyal paylaşım", bolum="sosyal",
        ust_bolum="etkilesim", tablo_adi="Sosyal gönderi kuyruğu",
        basliklar=["Haber", "Hesap", "Platform", "Durum", "Açılış",
                   "Gönderim", "İşlemler"],
        sorgu=sorgu, satir_kur=satir, temiz_adi="panel-sosyal",
        suzgecler=[_arama_suzgeci(aranan, "Haber başlığında ara"),
                   _durum_suzgeci(durum), _platform_suzgeci(platform)],
        ust_bilgi=(f"Sırada {bekleyen} · elle paylaşılacak {elle} · "
                   f"hatalı {hatali}."),
        ek_baglantilar=[("/panel/sosyal/gonder", "Bekleyenleri gönder"),
                        ("/panel/sosyal/ekle", "Elle gönderi aç"),
                        ("/panel/sosyal/hesaplar", "Hesaplar")],
        notlar=[
            "Satır haber taslakken de açılabilir; gönderici haberin yayına "
            "çıkmasını bekler ve o zamana kadar satırı kuyrukta tutar.",
            "Hesabın anahtarı yoksa satır ELLE durumunda açılır: metin ve "
            "paylaş bağlantısı hazır, gönderimi editör yapar.",
            "YouTube otomatik akışa girmez — orada haber değil, ayrıca "
            "çekilmiş özel video paylaşılıyor.",
        ])


@login_required
@permission_required(YETKI_KUYRUK, raise_exception=True)
def gonderi_detay(request, kimlik):
    gonderi = get_object_or_404(
        SosyalGonderi.objects.select_related("haber", "haber__kategori",
                                             "hesap"), pk=kimlik)
    form = SosyalGonderiForm(request.POST or None, instance=gonderi)

    if request.method == "POST":
        eylem = request.POST.get("eylem") or "kaydet"
        if eylem == "tazele":
            kuyruk.metni_tazele(gonderi)
            messages.success(request, "Metin haberin bugünkü hâlinden "
                                      "yeniden kuruldu.")
            return redirect("panel-sosyal-gonderi", kimlik=gonderi.pk)
        if eylem == "iptal":
            gonderi.durum = SosyalGonderi.IPTAL
            gonderi.save(update_fields=["durum"])
            messages.success(request, "Gönderi iptal edildi; kuyruktan çıktı.")
            return redirect("panel-sosyal-gonderi", kimlik=gonderi.pk)
        if form.is_valid():
            form.save()
            if eylem == "gonder":
                return _elden_gonder(request, gonderi)
            if eylem == "paylasildi":
                return _elle_isaretle(request, gonderi)
            messages.success(request, "Gönderi kaydedildi.")
            return redirect("panel-sosyal-gonderi", kimlik=gonderi.pk)

    saglayici = gonderi.hesap.saglayici()
    sinir = SINIRLAR.get(gonderi.hesap.platform)
    return render(request, "panel/sosyal_gonderi.html", {
        "baslik": f"{gonderi.hesap.ad} — [{gonderi.haber_id}]",
        "bolum": "sosyal", "ust_bolum": "etkilesim",
        "form": form,
        "gonderi": gonderi,
        "haber_adresi": gonderi.haber_adresi(),
        "paylas_adresi": paylas_adresi(gonderi.hesap, gonderi.metin,
                                       gonderi.haber_adresi()),
        "sinir": sinir,
        "uzunluk": olculen_uzunluk(gonderi.metin, gonderi.hesap.platform),
        "eksik_alanlar": gonderi.hesap.eksik_alanlar(),
        "otomatik_olur": gonderi.hesap.otomatik_olur,
        "yardim": saglayici.yardim,
        "yayinda": gonderi.haber_yayinda_mi(),
        "gonderilebilir": gonderi.gonderilebilir_mi(),
        **_yetkiler(request.user),
    })


def _elden_gonder(request, gonderi):
    if not gonderi.gonderilebilir_mi():
        messages.error(request, _neden_gonderilemez(gonderi))
        return redirect("panel-sosyal-gonderi", kimlik=gonderi.pk)
    if kuyruk.gonder(gonderi):
        messages.success(request, "Gönderi paylaşıldı.")
    else:
        messages.error(request, f"Gönderilemedi: {gonderi.hata_metni}")
    return redirect("panel-sosyal-gonderi", kimlik=gonderi.pk)


def _elle_isaretle(request, gonderi):
    """Editörün kendi paylaştığı gönderiyi kayda geçirir.

    Dış adres istenmiyor ama isteniyormuş gibi de davranılmıyor: adres
    boşsa kayıt yine tamamlanır, yalnız panelde bağlantı olmaz.
    """
    gonderi.durum = SosyalGonderi.GONDERILDI
    gonderi.gonderim_zamani = timezone.now()
    gonderi.hata_metni = ""
    gonderi.save(update_fields=["durum", "gonderim_zamani", "hata_metni"])
    messages.success(request, "Elle paylaşıldı olarak işaretlendi.")
    return redirect("panel-sosyal-gonderi", kimlik=gonderi.pk)


def _neden_gonderilemez(gonderi) -> str:
    hesap = gonderi.hesap
    if gonderi.durum in SosyalGonderi.KAPALI_DURUMLAR:
        return "Bu satır kapalı: gönderilmiş ya da iptal edilmiş."
    if not hesap.aktif:
        return "Hesap kapalı."
    if not hesap.otomatik_olur:
        return ("Bu platforma panelden gönderilmiyor; paylaştıktan sonra "
                "“Paylaşıldı” işaretleyin.")
    if not hesap.kimligi_tam_mi():
        return ("Hesabın kimlik bilgisi eksik: "
                + ", ".join(hesap.eksik_alanlar()) + ".")
    if not gonderi.haber_yayinda_mi():
        return ("Haber yayında değil. Satır kuyrukta kalır; haber yayına "
                "alınınca gönderilir.")
    return "Gönderilemedi."


@login_required
@permission_required(YETKI_KUYRUK, raise_exception=True)
def bekleyenleri_gonder(request):
    """Onay ekranı (GET) ve gönderim (POST)."""
    hazir = [g for g in SosyalGonderi.bekleyenler()
             .select_related("haber", "haber__kategori", "hesap")
             if g.gonderilebilir_mi()]
    if request.method == "POST":
        ozet = kuyruk.bekleyenleri_gonder(sinir=ELDEN_SINIR)
        messages.success(request, kuyruk.ozet_cumlesi(ozet))
        return redirect("panel-sosyal")
    return render(request, "panel/sosyal_gonder.html", {
        "baslik": "Bekleyenleri gönder",
        "bolum": "sosyal", "ust_bolum": "etkilesim",
        "hazir": hazir[:ELDEN_SINIR],
        "sayi": len(hazir),
        "sinir": ELDEN_SINIR,
        **_yetkiler(request.user),
    })


@login_required
@permission_required(YETKI_KUYRUK, raise_exception=True)
def gonderi_ekle(request):
    form = YeniGonderiForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        haber = Haber.objects.get(pk=form.cleaned_data["haber_kimligi"])
        hesap = form.cleaned_data["hesap"]
        acilan = kuyruk.kuyruga_al(haber, [hesap], request.user,
                                   kaynak=SosyalGonderi.ELLE_ACILDI)
        if not acilan:
            messages.error(request, "Bu haberin bu hesapta zaten açık bir "
                                    "gönderisi var.")
            return redirect("panel-sosyal")
        return redirect("panel-sosyal-gonderi", kimlik=acilan[0].pk)
    return render(request, "panel/kayit_form.html", {
        "baslik": "Elle gönderi aç",
        "bolum": "sosyal", "ust_bolum": "etkilesim",
        "form": form, "geri_adi": "panel-sosyal", "adres": "",
        "kilitli": [("Kuyruk", "Sosyal paylaşım")],
        "kilit_notu": ("YouTube videoları bu yoldan girer: satır açılır, "
                       "metin hazırlanır, video elle yüklenir."),
        **_yetkiler(request.user),
    })


# ---------------------------------------------------------------------------
# Hesaplar
# ---------------------------------------------------------------------------


@login_required
@permission_required(YETKI_HESAP, raise_exception=True)
def hesap_listesi(request):
    sorgu = SosyalHesap.objects.all()
    platform = request.GET.get("platform") or ""
    if platform:
        sorgu = sorgu.filter(platform=platform)

    def satir(h):
        eksik = h.eksik_alanlar()
        return {
            "kimlik": h.pk,
            "duzenle": f"/panel/sosyal/hesap/{h.pk}",
            "adres": "",
            "hucreler": [
                _bag(f"/panel/sosyal/hesap/{h.pk}", h.ad),
                _metin(h.get_platform_display()),
                _metin("@" + h.kullanici_adi) if h.kullanici_adi
                else _yok("Kullanıcı adı girilmedi; gönderi adresi kurulamaz."),
                _rozet("Aktif", "aktif") if h.aktif else _rozet("Pasif", "pasif"),
                _rozet("Otomatik", "hazir") if h.otomatik_olur
                else _rozet("Elle", "taslak"),
                _rozet("Anahtar tam", "hazir") if not eksik
                else _rozet("Eksik: " + ", ".join(eksik), "incelemede"),
                _tarih(h.son_gonderim) if h.son_gonderim
                else _yok("Bu hesapla henüz gönderi yapılmadı."),
            ],
        }

    return _liste_ciz(
        request, baslik="Sosyal hesaplar", bolum="sosyal-hesap",
        ust_bolum="ayarlar", tablo_adi="Sosyal medya hesapları",
        basliklar=["Hesap", "Platform", "Kullanıcı adı", "Durum", "Yol",
                   "Anahtar", "Son gönderim", "İşlemler"],
        sorgu=sorgu, satir_kur=satir, temiz_adi="panel-sosyal-hesaplar",
        suzgecler=[_platform_suzgeci(platform)],
        ek_baglantilar=[("/panel/sosyal/hesap/ekle", "Hesap ekle"),
                        ("/panel/sosyal", "Kuyruk")],
        notlar=[
            "Anahtarlar önce ortam değişkeninden okunur "
            "(BH_SOSYAL_X_ERISIM_JETONU gibi), yoksa kayıttan. Ortamda "
            "duran anahtar veritabanı yedeğine düşmez.",
            "Anahtarı eksik hesap gönderi yapmaz ama işe yaramaz da olmaz: "
            "gönderileri ELLE paylaşım olarak kuyruğa düşer.",
        ])


@login_required
@permission_required(YETKI_HESAP, raise_exception=True)
def hesap_ekle(request):
    form = SosyalHesapForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        hesap = form.save()
        messages.success(request, "Hesap tanımlandı. Anahtarları şimdi "
                                  "girebilirsiniz.")
        return redirect("panel-sosyal-hesap", kimlik=hesap.pk)
    return render(request, "panel/kayit_form.html", {
        "baslik": "Sosyal hesap ekle",
        "bolum": "sosyal-hesap", "ust_bolum": "ayarlar",
        "form": form, "geri_adi": "panel-sosyal-hesaplar", "adres": "",
        "kilitli": [("Anahtarlar", "kayıttan sonra")],
        "kilit_notu": ("Hangi anahtarların isteneceği platforma bağlı; "
                       "bu yüzden anahtar alanları hesap kaydedildikten "
                       "sonra açılır."),
        **_yetkiler(request.user),
    })


@login_required
@permission_required(YETKI_HESAP, raise_exception=True)
def hesap_duzenle(request, kimlik):
    hesap = get_object_or_404(SosyalHesap, pk=kimlik)
    form = SosyalHesapForm(request.POST or None, instance=hesap)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Hesap kaydedildi.")
        return redirect("panel-sosyal-hesap", kimlik=hesap.pk)

    saglayici = hesap.saglayici()
    eksik = hesap.eksik_alanlar()
    return render(request, "panel/kayit_form.html", {
        "baslik": hesap.ad,
        "bolum": "sosyal-hesap", "ust_bolum": "ayarlar",
        "form": form, "geri_adi": "panel-sosyal-hesaplar", "adres": "",
        "kilitli": [
            ("Kimlik", hesap.pk),
            ("Platform", hesap.get_platform_display()),
            ("Yol", "otomatik" if hesap.otomatik_olur else "elle"),
            ("Anahtar", "tam" if not eksik else "eksik: " + ", ".join(eksik)),
            ("Bekleyen gönderi",
             hesap.gonderiler.filter(durum=SosyalGonderi.BEKLIYOR).count()),
            ("Son hata", hesap.son_hata or "—"),
        ],
        "kilit_notu": saglayici.yardim,
        **_yetkiler(request.user),
    })
