"""Denetim kaydı (eylem günlüğü) — 19 Ekim 2026, Paket F madde 9.

`LogKaydi` modeli 28 Ağustos'tan beri vardı ama ona yazan TEK satır kod yoktu
(DEGERLENDIRME-2026-10 §3 6g): panel "Log" ekranı her zaman boştu. Bu modül
yazan taraftır; panel görünümleri ve oturum sinyalleri buradan yazar.

Yazılan olaylar: oturum açma / başarısız deneme / kilit / kapatma · haber
oluşturma · yayına alma / yayından çekme / arşivleme · manşet ve kategori
değişikliği · toplu işlemler (kayıt başına satır, aynı toplu iş kimliğiyle) ·
son dakika değişikliği · konu onay/ret ve dosyadan haber çıkarma · kullanıcı
ve rol değişikliği · parola değişikliği.

## IP adresi ve KVKK (karar)

IP adresi kişisel veridir. Varsayılan **maskeli** yazılır: IPv4'te son
sekizli (`/24`), IPv6'da `/48` sonrası sıfırlanır. Bu, "aynı ağdan mı geldi"
sorusunu yanıtlar ama kişiyi tek başına belirlemez. Ayar:

    BH_LOG_IP = maskeli (varsayılan) | tam | yok

`tam` ancak hukuki teyitten sonra açılmalı (→ hukuk-guvenlik-uyum-uzmani);
`yok` IP ve tarayıcı bilgisini hiç yazmaz. Tarayıcı satırı 200 karakterle
kesilir. Saklama önerisi modelde: oturum kayıtları 12 ay, eylemler süresiz.

IP `REMOTE_ADDR`dan okunur; `X-Forwarded-For` bilerek okunmaz — vekil
sunucu arkasında güvenilir vekil yapılandırması gelmeden o başlık okurun
yazdığı bir metindir (→ devops-altyapi-muhendisi).

## Hata davranışı

Günlük yazılamazsa eylem GERİ ALINMAZ (işlem çoğu ekranda zaten yapılmıştır)
ama hata sunucu günlüğüne `ERROR` düzeyinde düşer. Sessiz yutma yok.
"""

from __future__ import annotations

import ipaddress
import logging
import os
import uuid

from django.conf import settings

gunluk = logging.getLogger("bh.denetim")

TOPLU_PARTI = 500


def ip_kipi() -> str:
    kip = (getattr(settings, "BH_LOG_IP", None)
           or os.environ.get("BH_LOG_IP", "") or "maskeli").strip().lower()
    return kip if kip in ("maskeli", "tam", "yok") else "maskeli"


def ip_maskele(metin: str) -> str | None:
    """`203.0.113.57` → `203.0.113.0`; IPv6 `/48` ağına indirilir."""
    try:
        ip = ipaddress.ip_address((metin or "").split("%", 1)[0])
    except ValueError:
        return None
    onek = 24 if ip.version == 4 else 48
    return str(ipaddress.ip_network(f"{ip}/{onek}", strict=False).network_address)


def _istek_izi(request) -> tuple[str | None, str]:
    if request is None or ip_kipi() == "yok":
        return None, ""
    ham = (request.META.get("REMOTE_ADDR") or "").strip()
    ip = ham if ip_kipi() == "tam" else ip_maskele(ham)
    try:
        ip = str(ipaddress.ip_address(ip)) if ip else None
    except ValueError:
        ip = None
    tarayici = (request.META.get("HTTP_USER_AGENT") or "")[:200]
    return ip, tarayici


def _kullanici(request, kullanici):
    if kullanici is not None:
        return kullanici if getattr(kullanici, "pk", None) else None
    k = getattr(request, "user", None)
    return k if (k is not None and getattr(k, "is_authenticated", False)) else None


def yaz(request, fiil: str, *, kullanici=None, hedef_tur: str = "",
        hedef_id=None, oncesi=None, sonrasi=None, gerekce: str = "",
        etkilenen: int = 1, toplu_kimlik: str = ""):
    """Tek bir denetim satırı yazar. Döner: kayıt ya da (hata olursa) None."""
    from .models import LogKaydi
    ip, tarayici = _istek_izi(request)
    try:
        return LogKaydi.objects.create(
            kullanici=_kullanici(request, kullanici), fiil=fiil,
            hedef_tur=hedef_tur[:24], hedef_id=hedef_id,
            oncesi=oncesi, sonrasi=sonrasi, gerekce=(gerekce or "")[:200],
            etkilenen_sayisi=max(int(etkilenen or 0), 0),
            toplu_islem_kimligi=toplu_kimlik, ip=ip, tarayici=tarayici)
    except Exception:                                   # noqa: BLE001
        gunluk.exception("denetim kaydı yazılamadı: %s %s#%s", fiil, hedef_tur, hedef_id)
        return None


def toplu_yaz(request, fiil: str, hedef_tur: str, kimlikler, *, oncesi=None,
              sonrasi=None, gerekce: str = "") -> str:
    """Toplu işlemde etkilenen HER kayıt için bir satır; hepsi aynı toplu iş
    kimliğini taşır. Döner: toplu iş kimliği."""
    from .models import LogKaydi
    kimlikler = list(kimlikler)
    toplu = str(uuid.uuid4())
    if not kimlikler:
        return toplu
    ip, tarayici = _istek_izi(request)
    kullanici = _kullanici(request, None)
    satirlar = [LogKaydi(kullanici=kullanici, fiil=fiil, hedef_tur=hedef_tur[:24],
                         hedef_id=k, oncesi=oncesi, sonrasi=sonrasi,
                         gerekce=(gerekce or "")[:200],
                         etkilenen_sayisi=len(kimlikler),
                         toplu_islem_kimligi=toplu, ip=ip, tarayici=tarayici)
                for k in kimlikler]
    try:
        for bas in range(0, len(satirlar), TOPLU_PARTI):
            LogKaydi.objects.bulk_create(satirlar[bas:bas + TOPLU_PARTI])
    except Exception:                                   # noqa: BLE001
        gunluk.exception("toplu denetim kaydı yazılamadı: %s %s (%d)",
                         fiil, hedef_tur, len(kimlikler))
    return toplu


# ---------------------------------------------------------------------------
# Haber kaydının değişimi — form yolu
# ---------------------------------------------------------------------------

#: Haber formunda izlenen alanlar ve hangi fiille yazılacakları.
DURUM_FIILI = {1: "yayina_alma", 2: "yayindan_cekme", 4: "arsivleme"}
MANSET_ALANLARI = ("manset_ana", "manset_tepe", "manset_kare")


def haber_ozeti(haber) -> dict:
    """Değişim karşılaştırması için haberin izlenen alanları."""
    return {"durum": haber.durum, "kategori_id": haber.kategori_id,
            **{a: getattr(haber, a) for a in MANSET_ALANLARI}}


def haber_degisimi(request, haber, onceki: dict | None) -> None:
    """Formla kaydedilen haberin değişimlerini fiil fiil yazar."""
    simdiki = haber_ozeti(haber)
    if onceki is None:
        yaz(request, "haber_olusturma", hedef_tur="haber", hedef_id=haber.pk,
            sonrasi={"baslik": haber.baslik[:120], **simdiki})
        onceki = {"durum": None, "kategori_id": haber.kategori_id,
                  **{a: False for a in MANSET_ALANLARI}}
    if simdiki["durum"] != onceki["durum"] and simdiki["durum"] in DURUM_FIILI \
            and not (onceki["durum"] is None and simdiki["durum"] != 1):
        yaz(request, DURUM_FIILI[simdiki["durum"]], hedef_tur="haber",
            hedef_id=haber.pk, oncesi={"durum": onceki["durum"]},
            sonrasi={"durum": simdiki["durum"]})
    if simdiki["kategori_id"] != onceki["kategori_id"]:
        yaz(request, "kategori_degistirme", hedef_tur="haber", hedef_id=haber.pk,
            oncesi={"kategori_id": onceki["kategori_id"]},
            sonrasi={"kategori_id": simdiki["kategori_id"]})
    alinan = [a for a in MANSET_ALANLARI if simdiki[a] and not onceki[a]]
    cikan = [a for a in MANSET_ALANLARI if onceki[a] and not simdiki[a]]
    if alinan:
        yaz(request, "mansete_alma", hedef_tur="haber", hedef_id=haber.pk,
            oncesi={a: onceki[a] for a in alinan}, sonrasi={a: True for a in alinan})
    if cikan:
        yaz(request, "mansetten_cikarma", hedef_tur="haber", hedef_id=haber.pk,
            oncesi={a: True for a in cikan}, sonrasi={a: False for a in cikan})


# ---------------------------------------------------------------------------
# Oturum sinyalleri — `IcerikConfig.ready` bağlar
# ---------------------------------------------------------------------------

def _giris(sender, request, user, **kw):
    yaz(request, "giris", kullanici=user, hedef_tur="kullanici", hedef_id=user.pk)


def _cikis(sender, request, user, **kw):
    if user is not None and getattr(user, "pk", None):
        # Oturum süresi dolduysa nedeni `giris_guvenligi.OturumSuresi` bırakır.
        yaz(request, "cikis", kullanici=user, hedef_tur="kullanici", hedef_id=user.pk,
            gerekce=getattr(request, "_bh_cikis_nedeni", "") if request else "")


def _basarisiz(sender, credentials, request=None, **kw):
    from django.contrib.auth import get_user_model
    ad = str((credentials or {}).get("username") or "")[:150]
    kullanici = get_user_model().objects.filter(username=ad).first() if ad else None
    yaz(request, "giris_basarisiz", kullanici=kullanici, hedef_tur="kullanici",
        hedef_id=getattr(kullanici, "pk", None),
        gerekce=("Denenen kullanıcı adı: %s" % ad)[:200])


def sinyalleri_bagla() -> None:
    from django.contrib.auth.signals import (user_logged_in, user_logged_out,
                                             user_login_failed)
    user_logged_in.connect(_giris, dispatch_uid="bh_denetim_giris")
    user_logged_out.connect(_cikis, dispatch_uid="bh_denetim_cikis")
    user_login_failed.connect(_basarisiz, dispatch_uid="bh_denetim_basarisiz")
