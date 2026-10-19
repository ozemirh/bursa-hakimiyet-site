"""Paylaşılan önbellek: taze/bayat düzeni, yığılma kilidi, sayfa sürümü.

19 Ekim 2026 (başarım paketi). Bu dosyadan önce site üç yerde **modül
düzeyindeki global değişkende** önbellek tutuyordu (`baglam._menu_bellek`,
`baglam._kunye_bellek`, `views._sayim_bellek`). Üç kusuru vardı:

1. **Süreçler arasında paylaşılmıyordu.** Üretimde dört işçi süreç varsa
   pahalı sayım dört kez yapılır; her yeniden başlatmada sıfırdan.
2. **Kilitsizdi.** Süre dolduğu anda o süreçteki bütün eşzamanlı istekler
   aynı pahalı sorguyu birlikte açıyordu (yığılma, "cache stampede").
3. **İlk istek bedeli tek başına ödüyordu.** Menü sayımı soğuk diskte
   3,4–45 sn ölçüldü (19 Ekim 2026, 1.038.477 haber).

Burada üçü de kapanır: değerler `django.core.cache` üzerinden (Redis ya da
dosya önbelleği, bkz. `settings.py` başarım bloğu) bütün süreçlerce
paylaşılır ve `hesapla()` şu sözleşmeyle çalışır:

* **Taze** değer doğrudan döner.
* Süresi geçmiş ama hâlâ saklanan **bayat** değer varsa: kilidi alan TEK
  istek yeniden hesaplar, kilidi alamayanlar beklemeden bayat değeri alır.
* Hiç değer yoksa kilidi alamayan istek kısa süre (`bekle`) bekler;
  değer gelmezse `yedek`e düşer, yedek yoksa kendisi hesaplar — sayfa
  bir önbellek yüzünden düşmez.
* Hesap veritabanı hatasıyla düşerse son bilinen değer (yoksa `yedek`)
  `hata` saniyeliğine taze sayılarak yazılır. **Zaman damgası hata
  yolunda da güncellenir**: aksi hâlde kilitli bir veritabanında her istek
  aynı sorguya yeniden girip SQLite'ın bekleme süresi kadar dururdu
  (3 Eylül 2026'da künye satırında ölçülen tuzak).

Zaman damgası `time.time()` — duvar saati. `time.monotonic()` süreçten
sürece farklı bir sıfırdan sayar ve paylaşılan önbellekte anlamsızdır.
"""

from __future__ import annotations

import itertools
import logging
import os
import time
from typing import Any, Callable

from django.core.cache import caches
from django.db import DatabaseError

gunluk = logging.getLogger("bh.onbellek")

#: Hesaplanmış veri (menü, sayımlar, site haritası özetleri).
VERI = "default"
#: Basılmış çıktı (sayfa HTML'i, site haritası dosyaları). Ayrı takma ad,
#: çünkü çok sayıda ve büyük kayıt taşır; dolup budandığında menü gibi
#: pahalı verileri sürüklememeli.
SAYFA = "sayfa"

_YOK = object()


def _yedek_degeri(yedek):
    return yedek() if callable(yedek) else yedek


def hesapla(anahtar: str, uret: Callable[[], Any], *, taze: float,
            bayat: float | None = None, hata: float = 20, bekle: float = 2.0,
            yedek: Any = None, takma_ad: str = VERI,
            hatalar: tuple = (DatabaseError,)) -> Any:
    """`anahtar`ın değeri; gerekiyorsa `uret()` ile yeniden hesaplanır.

    `taze`   saniye: bu süre içinde değer olduğu gibi döner.
    `bayat`  saniye: tazeliğini yitirmiş değerin saklandığı ek süre
             (varsayılan `taze`nin 12 katı). Bu sürede değer kilitsiz
             isteklere servis edilir.
    `hata`   saniye: hesap düştüğünde yedek değerin taze sayılacağı süre.
    `yedek`  değer ya da çağrılabilir: hiç değer yokken ve hesap
             yapılamıyorken dönecek olan.
    """
    ob = caches[takma_ad]
    omur = int(taze + (bayat if bayat is not None else taze * 12))
    kayit = ob.get(anahtar)
    simdi = time.time()
    if kayit is not None and simdi - kayit[0] < taze:
        return kayit[1]

    kilit = f"{anahtar}:kilit"
    # Kilit, hesabın sürebileceği en uzun süreden uzun olmalı ama sonsuz
    # olmamalı: hesaplayan süreç ölürse kilit kendiliğinden düşer.
    aldim = ob.add(kilit, simdi, int(max(30, min(taze, 300))))
    if not aldim:
        if kayit is not None:
            return kayit[1]
        son = time.monotonic() + bekle
        while time.monotonic() < son:
            time.sleep(0.05)
            kayit = ob.get(anahtar)
            if kayit is not None:
                return kayit[1]
        if yedek is not None:
            return _yedek_degeri(yedek)
        # Yedek yok ve bekleme bitti: doğruluk yükten önce gelir, kendimiz
        # hesaplarız (kilidi almadığımız için silmeyiz).

    try:
        try:
            deger = uret()
        except hatalar as hata_nesnesi:
            gunluk.warning("önbellek hesabı düştü: %s (%s)", anahtar, hata_nesnesi)
            deger = kayit[1] if kayit is not None else _yedek_degeri(yedek)
            ob.set(anahtar, (time.time() - taze + hata, deger), omur)
            return deger
        ob.set(anahtar, (time.time(), deger), omur)
        return deger
    finally:
        if aldim:
            ob.delete(kilit)


def bayatlat(anahtar: str, takma_ad: str = VERI) -> None:
    """Değeri SİLMEDEN bayatlatır: bir sonraki istek yeniden hesaplar,
    o hesap sürerken gelenler son bilinen değeri alır."""
    ob = caches[takma_ad]
    kayit = ob.get(anahtar)
    if kayit is not None:
        ob.set(anahtar, (0.0, kayit[1]), ob.default_timeout)


def sil(*anahtarlar: str, takma_ad: str = VERI) -> None:
    ob = caches[takma_ad]
    for a in anahtarlar:
        ob.delete(a)


# --------------------------------------------------------------------------
# Yayın sürümü — sayfa mikro önbelleğinin toptan geçersizleştirilmesi.
#
# Sayfa anahtarları özetlenmiş adres taşıdığı için "bu kategorinin bütün
# sayfaları" diye joker silme yapılamaz. Onun yerine her sayfa anahtarına
# bir SÜRÜM katılır; haber kaydedilince sürüm değişir ve o andan sonra
# bütün eski anahtarlar ölü kalır (30 sn içinde kendiliğinden düşerler).
# Okur için sonuç: kaydedilen haber bir sonraki istekte görünür.

SURUM_ANAHTARI = "bh:yayin-surumu"


def yayin_surumu() -> str:
    deger = caches[SAYFA].get(SURUM_ANAHTARI)
    if deger is None:
        deger = surumu_artir()
    return deger


_surum_sayaci = itertools.count()


def yeni_surum() -> str:
    """Her çağrıda FARKLI bir sürüm değeri.

    Yalnız zaman damgası yetmiyordu: Windows'ta `time.time()` çözünürlüğü
    15,625 ms ve aynı dilimdeki iki kayıt aynı sürümü yazıyor, ikincisi
    önbellekte görünmüyordu (`tests_kararlilik` başındaki kök neden).
    Süreç kimliği + süreç içi sayaç çakışmayı kapatır.
    """
    return f"{time.time():.6f}-{os.getpid()}-{next(_surum_sayaci)}"


def surumu_artir() -> str:
    # Sayı değil zaman damgası: iki süreç aynı anda artırırsa ikisi de
    # FARKLI ve yeni bir değer yazar; `incr` dosya önbelleğinde atomik değil.
    deger = yeni_surum()
    caches[SAYFA].set(SURUM_ANAHTARI, deger, None)
    return deger
