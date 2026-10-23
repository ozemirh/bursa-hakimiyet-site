"""Panel giriş güvenliği — 19 Ekim 2026, Paket F madde 8.

DEGERLENDIRME-2026-10 §3 6f: giriş denemesi sınırı yoktu, oturum hiç
düşmüyordu (Django varsayılanı iki hafta). Paket kurulmadı; Django'nun
önbelleği ve oturumu yeter.

## Başarısız giriş sınırı

İki sayaç, ikisi de `django.core.cache` üzerinde:

    kullanıcı adı + IP   5 başarısız deneme / 15 dk  → 15 dk kilit
    yalnız IP           20 başarısız deneme / 15 dk  → 15 dk kilit

Birincisi tek hesaba parola denemeyi, ikincisi aynı adresten çok hesaba
"parola püskürtmeyi" keser. Kilitliyken parola HİÇ denenmez (karma hesabı
da yapılmaz); mesaj hesabın var olup olmadığını söylemez. Kilidin başladığı
an denetim kaydına `giris_kilidi` olarak düşer. Başarılı giriş kullanıcı
sayacını sıfırlar.

Sayaçlar `default` önbellek takma adında (başarım paketinin kurduğu
paylaşılan önbellek: Redis ya da dosya). Dosya önbelleğinde `incr` atomik
değildir; eşzamanlı denemede bir-iki deneme kaçabilir, sınırın amacı bozulmaz.
IP adresi okunma sayacının güvenilir vekil kuralıyla bulunur.

Ayarlar (settings, hepsi isteğe bağlı): `BH_GIRIS_KULLANICI_SINIRI` (5),
`BH_GIRIS_IP_SINIRI` (20), `BH_GIRIS_PENCERE_SANIYE` (900),
`BH_GIRIS_KILIT_SANIYE` (900).

## Oturum süresi

`OturumSuresi` ara katmanı iki sınır uygular:

    mutlak  BH_OTURUM_MUTLAK_SANIYE   girişten en çok 8 saat
    boşta   BH_OTURUM_BOSTA_SANIYE    60 dk hiçbir istek yoksa

Süre dolunca oturum kapatılır (denetim kaydına gerekçesiyle `cikis`) ve
istek anonim devam eder; panel adresleri `login_required` ile giriş
ekranına döner. Son etkinlik damgası en çok dakikada bir yazılır — her
istekte oturum tablosuna yazmamak için.
"""

from __future__ import annotations

import hashlib
import time

from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.signals import user_logged_in
from django.contrib.auth.views import LoginView
# `cache` = `caches["default"]` vekili (her erişimde çözülür; ayar ezmeleri
# ve iş parçacıkları doğru arka ucu görür). Başarım paketinin paylaşılan
# önbelleği: Redis ya da dosya — süreçler arasında ortak.
from django.core.cache import cache


def _ayar(ad: str, varsayilan: int) -> int:
    try:
        return int(getattr(settings, ad, varsayilan))
    except (TypeError, ValueError):
        return varsayilan


def kullanici_siniri() -> int:
    return _ayar("BH_GIRIS_KULLANICI_SINIRI", 5)


def ip_siniri() -> int:
    return _ayar("BH_GIRIS_IP_SINIRI", 20)


def pencere() -> int:
    return _ayar("BH_GIRIS_PENCERE_SANIYE", 900)


def kilit_suresi() -> int:
    return _ayar("BH_GIRIS_KILIT_SANIYE", 900)


def _ip(request) -> str:
    """Okunma sayacıyla AYNI güvenilir vekil kuralı (`BH_GUVENILIR_VEKIL`).

    Koşulsuz `X-Forwarded-For` okunsaydı saldırgan her denemede başlığa
    başka adres yazıp IP sayacını atlatırdı."""
    if request is None:
        return "-"
    from .okunma import ziyaretci_adresi
    return ziyaretci_adresi(request) or "-"


def _anahtar(tur: str, *parcalar: str) -> str:
    # Önbellek anahtarına kullanıcı adı / IP AÇIK yazılmaz.
    ozet = hashlib.sha256("|".join(parcalar).encode("utf-8")).hexdigest()[:32]
    return f"bh:giris:{tur}:{ozet}"


def _anahtarlar(request, ad: str) -> dict:
    ad = (ad or "").strip().lower()
    ip = _ip(request)
    return {"kullanici": _anahtar("k", ad, ip), "ip": _anahtar("i", ip)}


def kilit_kalan(request, ad: str) -> int:
    """Kilit varsa kalan saniye, yoksa 0."""
    simdi = time.time()
    kalan = 0
    for anahtar in _anahtarlar(request, ad).values():
        bitis = cache.get(anahtar + ":kilit")
        if bitis and bitis > simdi:
            kalan = max(kalan, int(bitis - simdi) + 1)
    return kalan


def _say(anahtar: str) -> int:
    cache.add(anahtar, 0, timeout=pencere())
    try:
        return cache.incr(anahtar)
    except ValueError:              # süresi tam o anda doldu
        cache.set(anahtar, 1, timeout=pencere())
        return 1


def basarisiz_say(request, ad: str) -> bool:
    """Başarısız denemeyi sayar. Döner: bu denemeyle kilit başladı mı."""
    anahtarlar = _anahtarlar(request, ad)
    basladi = False
    for tur, sinir in (("kullanici", kullanici_siniri()), ("ip", ip_siniri())):
        if _say(anahtarlar[tur]) >= sinir:
            cache.set(anahtarlar[tur] + ":kilit", time.time() + kilit_suresi(),
                      timeout=kilit_suresi())
            cache.delete(anahtarlar[tur])
            basladi = True
    return basladi


def basarili(request, ad: str) -> None:
    cache.delete(_anahtarlar(request, ad)["kullanici"])


class SinirliGirisFormu(AuthenticationForm):
    """Kilitliyken parolayı denemeyen giriş formu."""

    kilitli = False

    def clean(self):
        ad = self.cleaned_data.get("username") or ""
        kalan = kilit_kalan(self.request, ad)
        if kalan:
            self.kilitli = True
            dakika = max(1, (kalan + 59) // 60)
            raise forms.ValidationError(
                f"Çok sayıda başarısız giriş denemesi. {dakika} dakika sonra "
                "yeniden deneyin.", code="kilitli")
        try:
            veri = super().clean()
        except forms.ValidationError:
            if basarisiz_say(self.request, ad):
                from .denetim_kaydi import yaz
                yaz(self.request, "giris_kilidi", hedef_tur="kullanici",
                    gerekce=("Kilitlenen kullanıcı adı: %s" % ad)[:200])
            raise
        basarili(self.request, ad)
        return veri


class GirisGorunumu(LoginView):
    template_name = "panel/giris.html"
    redirect_authenticated_user = True
    form_class = SinirliGirisFormu


# ---------------------------------------------------------------------------
# Oturum süresi
# ---------------------------------------------------------------------------

GIRIS_ANAHTARI = "bh_giris_zamani"
ETKINLIK_ANAHTARI = "bh_son_etkinlik"
DAMGA_ARALIGI = 60


def mutlak_sure() -> int:
    return _ayar("BH_OTURUM_MUTLAK_SANIYE", 8 * 3600)


def bosta_sure() -> int:
    return _ayar("BH_OTURUM_BOSTA_SANIYE", 60 * 60)


def _giris_damgasi(sender, request, user, **kw):
    if request is not None and hasattr(request, "session"):
        simdi = int(time.time())
        request.session[GIRIS_ANAHTARI] = simdi
        request.session[ETKINLIK_ANAHTARI] = simdi


def sinyali_bagla() -> None:
    """`IcerikConfig.ready` çağırır: test istemcisinin `force_login`i de
    URL tablosu yüklenmeden önce giriş yapabilir."""
    user_logged_in.connect(_giris_damgasi, dispatch_uid="bh_oturum_giris_damgasi")


class OturumSuresi:
    """Mutlak ve boşta oturum süresi ara katmanı."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        kullanici = getattr(request, "user", None)
        if kullanici is not None and kullanici.is_authenticated:
            self._denetle(request)
        return self.get_response(request)

    def _denetle(self, request):
        oturum = request.session
        simdi = int(time.time())
        giris = oturum.get(GIRIS_ANAHTARI)
        son = oturum.get(ETKINLIK_ANAHTARI)
        if giris is None:
            # Bu düzenden önce açılmış oturum: şimdiden say.
            oturum[GIRIS_ANAHTARI] = oturum[ETKINLIK_ANAHTARI] = simdi
            return
        neden = ""
        if simdi - giris > mutlak_sure():
            neden = "Oturum süresi doldu (mutlak sınır)."
        elif son is not None and simdi - son > bosta_sure():
            neden = "Oturum boşta kaldığı için kapandı."
        if neden:
            request._bh_cikis_nedeni = neden
            logout(request)
            messages.info(request, neden + " Yeniden giriş yapın.")
            return
        if son is None or simdi - son >= DAMGA_ARALIGI:
            oturum[ETKINLIK_ANAHTARI] = simdi
