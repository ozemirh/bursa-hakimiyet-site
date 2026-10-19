"""Site haritası önbelleği (19 Ekim 2026, başarım paketi).

Ölçüm (1.038.477 haber): indeks **385 sorgu / 3,6 sn**, soğuk süreçte
**19,6 sn**; aylık dosya ~0,5 sn. Arama motoru bu adresleri sık ve
paralel yokluyor.

Üç katman:

1. **Ay özetleri** (indeksin içeriği) aile başına tek kayıt olarak `VERI`
   önbelleğinde. `OZET_TAZE` boyunca taze, sonra bayat-ama-servis (bkz.
   `icerik/onbellek.py`). Kayıt değişince TÜM özet yeniden hesaplanmaz:
   yalnız etkilenen ay(lar) tek ay sorgusuyla (`Aile.ay_ozeti`, ~10 ms)
   yeniden sayılıp kayda işlenir.
2. **Aylık dosya gövdeleri** `SAYFA` önbelleğinde. Anahtar ayın SÜRÜMÜNÜ
   taşır; kayıt değişince o ayın sürümü değişir ve eski gövde bir daha
   okunmaz. İçinde bulunulan ay kısa (`AKTIF_AY_TAZE`), geçmiş aylar uzun
   (`GECMIS_AY_TAZE`) taze kalır.
3. **İndeks metni önbelleklenmez**: başlığında üretim anı var ve özetler
   elde olunca 274 satırı yazmak milisaniyelik iş.

Sinyalle yakalanmayan değişiklik (`QuerySet.update`, ileri tarihli haberin
saati gelmesi) tazelik süresi dolunca görünür; o yüzden süreler kısa.
Dosya adları ve içerik biçimi DEĞİŞMEDİ: önbellek aynı üretecin çıktısını
saklar.
"""

from __future__ import annotations

import hashlib

from django.core.cache import caches
from django.db.models.signals import post_delete, post_save, pre_save
from django.utils import timezone

from icerik import onbellek

from .aileler import kayitli_aileler
from .zaman import ay_adi

OZET_TAZE = 15 * 60
OZET_BAYAT = 7 * 86400
AKTIF_AY_TAZE = 10 * 60
GECMIS_AY_TAZE = 6 * 3600


def ozet_anahtari(aile_anahtari: str) -> str:
    return f"bh:sitemap:aylar:{aile_anahtari}:v1"


def _surum_anahtari(aile_anahtari: str, ay: str) -> str:
    return f"bh:sitemap:surum:{aile_anahtari}:{ay}"


def aylar(aile_anahtari: str, hesapla) -> list:
    # Hata yolu YOK (`hatalar=()`): boş indeks döndürmek arama motoruna
    # "bütün dosyalar kalktı" demektir; 500 ise yeniden denenir.
    return onbellek.hesapla(ozet_anahtari(aile_anahtari), hesapla,
                            taze=OZET_TAZE, bayat=OZET_BAYAT, hatalar=())


def aylik_metin(kok: str, aile, ay: str, uret) -> str:
    """Aylık dosyanın tam metni; `uret()` önbellek boşsa çağrılır."""
    surum = caches[onbellek.VERI].get(_surum_anahtari(aile.anahtar, ay)) or "0"
    kok_ozeti = hashlib.md5(kok.encode("utf-8"), usedforsecurity=False).hexdigest()[:12]
    anahtar = f"bh:sitemap:dosya:{aile.anahtar}:{ay}:{surum}:{kok_ozeti}"
    taze = AKTIF_AY_TAZE if ay == ay_adi(timezone.now()) else GECMIS_AY_TAZE
    return onbellek.hesapla(anahtar, uret, taze=taze, bayat=taze,
                            takma_ad=onbellek.SAYFA, hatalar=())


def ay_degisti(aile, aylar_: set[str]) -> None:
    """Kayıt değişti: o ayların dosyası düşer, özeti tek tek yeniden sayılır."""
    aylar_ = {a for a in aylar_ if a}
    if not aylar_:
        return
    veri = caches[onbellek.VERI]
    for ay in aylar_:
        # Benzersiz sürüm: düz `time.time()` Windows'ta 15,6 ms aynı kalıyor,
        # aynı dilimdeki ikinci kayıt eski dosyayı servis ettiriyordu.
        veri.set(_surum_anahtari(aile.anahtar, ay), onbellek.yeni_surum(), None)
    if aile.ay_ozeti is None:
        onbellek.sil(ozet_anahtari(aile.anahtar))
        return
    anahtar = ozet_anahtari(aile.anahtar)
    kayit = veri.get(anahtar)
    if kayit is None:
        return  # özet hiç kurulmamış; ilk istek baştan hesaplar
    zaman, ozetler = kayit
    sozluk = {o.ay: o for o in ozetler}
    for ay in aylar_:
        yeni = aile.ay_ozeti(ay)
        if yeni is None:
            sozluk.pop(ay, None)
        else:
            sozluk[ay] = yeni
    # Damga KORUNUR: tam yeniden hesap yine `OZET_TAZE` dolunca yapılır ve
    # iki sürecin aynı anda yaptığı yamalardan biri kaybolsa bile düzelir.
    veri.set(anahtar, (zaman, sorted(sozluk.values(), key=lambda o: o.ay, reverse=True)),
             int(OZET_TAZE + OZET_BAYAT))


# --------------------------------------------------------------------------
# Sinyaller — ailenin modeli kaydedilince/silinince

def _ay(an):
    return ay_adi(an) if an else None


def _once(sender, instance, raw=False, **_):
    """Kayıt BAŞKA aya taşınıyorsa eski ay da tazelenmeli; eski değer
    burada yakalanır. Model yüklenirken değeri saklıyorsa
    (`Haber.from_db` → `_yuklenen_yayin_zamani`) sorgu açılmaz."""
    if raw or instance.pk is None:
        instance._bh_eski_yayin = None
        return
    if hasattr(instance, "_yuklenen_yayin_zamani"):
        instance._bh_eski_yayin = instance._yuklenen_yayin_zamani
        return
    instance._bh_eski_yayin = (sender.objects.filter(pk=instance.pk)
                               .values_list("yayin_zamani", flat=True).first())


def _sonra(sender, instance, **_):
    aylar_ = {_ay(getattr(instance, "yayin_zamani", None)),
              _ay(getattr(instance, "_bh_eski_yayin", None))}
    for aile in kayitli_aileler():
        if aile.model is sender:
            ay_degisti(aile, aylar_)


def bagla() -> None:
    modeller = {a.model for a in kayitli_aileler() if a.model is not None}
    for model in modeller:
        etiket = model._meta.label_lower
        pre_save.connect(_once, sender=model, dispatch_uid=f"bh-sitemap-once-{etiket}")
        post_save.connect(_sonra, sender=model, dispatch_uid=f"bh-sitemap-sonra-{etiket}")
        post_delete.connect(_sonra, sender=model, dispatch_uid=f"bh-sitemap-sil-{etiket}")
