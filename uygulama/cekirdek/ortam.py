"""Çalışma ortamı ve güvenli varsayılan (19 Ekim 2026).

Değerlendirme bulgusu 6a: ayarlar ortam değişkeni yoksa `DEBUG=1`e ve
depodaki sabit anahtara düşüyordu. Depo herkese açık olduğu için o anahtar
herkesin elindeydi; üretimde unutulan tek bir değişken sitenin oturumlarını
ve imzalı verilerini açığa çıkarırdı.

Yeni düzen **fail-closed**: ortam açıkça söylenmedikçe üretim sayılır ve
üretimin şartları yerine gelmezse uygulama AÇILMAZ.

    BH_ORTAM=gelistirme   bu makine. DEBUG varsayılanı açık, yerel anahtar
                          `uygulama/.yerel-gizli-anahtar` dosyasında üretilir
                          (depoya girmez). `gelistir.ps1` bunu kurar.
    BH_ORTAM=test         `manage.py test` ve CI. BH_ORTAM verilmemişse ve
                          komut `test` ise kendiliğinden seçilir; başka hiçbir
                          komut için tahmin yapılmaz.
    BH_ORTAM=uretim       varsayılan. BH_GIZLI_ANAHTAR ve BH_SUNUCU_ADLARI
                          zorunlu, DEBUG açılamaz, yerel adlar reddedilir.

Bu modül `settings.py` tarafından okunur; Django ayarlarına bağımlı değildir,
yalnız ortam sözlüğüne bakar. Böylece testler ayarları farklı ortamlarla
yeniden yükleyip davranışı sınayabilir (`cekirdek/tests.py`).
"""

from __future__ import annotations

import os
import secrets
import sys
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

ORTAMLAR = ("gelistirme", "test", "uretim")

# Üretimde ALLOWED_HOSTS'a girmemesi gereken adlar. "*" her konağı kabul
# eder (Host başlığı zehirlenmesi); diğerleri yalnız bu makineyi gösterir ve
# üretimde bulunmaları yanlış dosyanın yüklendiğine işarettir.
YEREL_ADLAR = frozenset({"localhost", "127.0.0.1", "[::1]", "::1", "0.0.0.0",
                         "*", "testserver"})

# Django'nun `check --deploy` W009 ölçütüyle aynı: en az 50 karakter, en az
# 5 farklı karakter, `django-insecure` önekiyle başlamaz.
ANAHTAR_EN_KISA = 50
ANAHTAR_EN_AZ_FARKLI = 5


def _evet(deger: str | None) -> bool:
    return (deger or "").strip().lower() in ("1", "evet", "true", "acik", "açık")


def ortam_adi(ortam: dict | None = None, argv: list | None = None) -> str:
    """Hangi ortamdayız? Bilinmiyorsa `uretim` (güvenli varsayılan)."""
    ortam = os.environ if ortam is None else ortam
    argv = sys.argv if argv is None else argv
    deger = (ortam.get("BH_ORTAM") or "").strip().lower()
    if deger:
        if deger not in ORTAMLAR:
            raise ImproperlyConfigured(
                f"BH_ORTAM={deger!r} tanınmıyor; şunlardan biri olmalı: "
                + ", ".join(ORTAMLAR))
        return deger
    if len(argv) > 1 and argv[1] == "test":
        return "test"
    return "uretim"


def gizli_anahtar(ad: str, ortam: dict | None = None,
                  yerel_dosya: Path | None = None) -> str:
    ortam = os.environ if ortam is None else ortam
    anahtar = (ortam.get("BH_GIZLI_ANAHTAR") or "").strip()
    if ad == "uretim":
        if not anahtar:
            raise ImproperlyConfigured(
                "Üretimde BH_GIZLI_ANAHTAR zorunlu. Bu bir geliştirme "
                "makinesiyse BH_ORTAM=gelistirme verin (gelistir.ps1 verir). "
                "Anahtar üretmek için: python -c \"import secrets; "
                "print(secrets.token_urlsafe(64))\"")
        if (len(anahtar) < ANAHTAR_EN_KISA
                or len(set(anahtar)) < ANAHTAR_EN_AZ_FARKLI
                or anahtar.startswith("django-insecure")):
            raise ImproperlyConfigured(
                f"BH_GIZLI_ANAHTAR zayıf: en az {ANAHTAR_EN_KISA} karakter, "
                f"{ANAHTAR_EN_AZ_FARKLI} farklı karakter olmalı ve "
                "'django-insecure' ile başlamamalı.")
        return anahtar
    if anahtar:
        return anahtar
    if ad == "test":
        # Her koşuda yeni: testler anahtara bağlı bir değer saklamaz.
        return "test-" + secrets.token_urlsafe(48)
    return _yerel_anahtar(yerel_dosya)


def _yerel_anahtar(yol: Path | None) -> str:
    """Geliştirme anahtarı: bir kez üretilir, makinede kalır.

    Her açılışta yeni anahtar üretmek panel oturumunu her yeniden başlatmada
    düşürürdü. Dosya `.gitignore`'da; yazılamazsa süreç ömürlük anahtar.
    """
    if yol is None:
        return secrets.token_urlsafe(50)
    try:
        if yol.exists():
            mevcut = yol.read_text(encoding="utf-8").strip()
            if len(mevcut) >= ANAHTAR_EN_KISA:
                return mevcut
        yeni = secrets.token_urlsafe(50)
        yol.write_text(yeni + "\n", encoding="utf-8")
        return yeni
    except OSError:
        return secrets.token_urlsafe(50)


def hata_ayiklama(ad: str, ortam: dict | None = None) -> bool:
    ortam = os.environ if ortam is None else ortam
    istenen = ortam.get("BH_HATA_AYIKLA")
    if ad == "uretim":
        if _evet(istenen):
            raise ImproperlyConfigured(
                "Üretimde BH_HATA_AYIKLA açılamaz: DEBUG hata sayfası ayarları, "
                "SQL sorgularını ve ortam değişkenlerini okura gösterir.")
        return False
    if ad == "test":
        return False
    return istenen is None or _evet(istenen)


def sunucu_adlari(ad: str, ortam: dict | None = None) -> list[str]:
    ortam = os.environ if ortam is None else ortam
    adlar = [a.strip() for a in (ortam.get("BH_SUNUCU_ADLARI") or "").split(",")
             if a.strip()]
    if ad == "uretim":
        if not adlar:
            raise ImproperlyConfigured(
                "Üretimde BH_SUNUCU_ADLARI zorunlu, ör. "
                "'www.bursahakimiyet.com.tr,bursahakimiyet.com.tr'.")
        yerel = [a for a in adlar if a.lower() in YEREL_ADLAR]
        if yerel:
            raise ImproperlyConfigured(
                f"Üretimde BH_SUNUCU_ADLARI yerel/joker ad içeremez: {yerel}. "
                "Sağlık yoklaması makinenin kendisinden yapılacaksa Host "
                "başlığıyla gönderilir (dagitim/KURULUM.md).")
        return adlar
    varsayilan = ["127.0.0.1", "localhost", "[::1]"]
    if ad == "test":
        varsayilan.append("testserver")
    return adlar or varsayilan


def guvenilir_kokenler(adlar: list[str], ortam: dict | None = None) -> list[str]:
    """CSRF için güvenilir kökenler. Verilmezse sunucu adlarından türer.

    Django 4'ten beri HTTPS'te `Origin` başlığı bu listeyle karşılaştırılıyor;
    vekil arkasında liste boş kalırsa panelin her POST'u 403 alır.
    """
    ortam = os.environ if ortam is None else ortam
    acik = [k.strip() for k in (ortam.get("BH_GUVENILIR_KOKENLER") or "").split(",")
            if k.strip()]
    if acik:
        return acik
    kokenler = []
    for a in adlar:
        if a.lower() in YEREL_ADLAR:
            continue
        kokenler.append(f"https://*{a}" if a.startswith(".") else f"https://{a}")
    return kokenler


def sayi(ortam: dict, ad: str, varsayilan: int) -> int:
    deger = (ortam.get(ad) or "").strip()
    if not deger:
        return varsayilan
    try:
        return int(deger)
    except ValueError as hata:
        raise ImproperlyConfigured(f"{ad} bir tam sayı olmalı: {deger!r}") from hata


def bayrak(ortam: dict, ad: str, varsayilan: bool) -> bool:
    deger = ortam.get(ad)
    if deger is None or not deger.strip():
        return varsayilan
    return _evet(deger)
