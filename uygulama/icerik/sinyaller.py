"""Önbellek geçersizleştirme sinyalleri (19 Ekim 2026, başarım paketi).

Kayıt değişince ona dayanan önbellek anında düşer:

* **Sayfa mikro önbelleği** — haber, kategori, ilçe, konu, son dakika ya
  da resmî ilan kaydedilince yayın sürümü değişir; bütün sayfa anahtarları
  bir sonraki istekte yeniden kurulur (`onbellek.surumu_artir`).
* **Kategori özeti / ilçe listesi** — menü, bant ve künye.
* **Slug eşlemesi** — bu süreçte hemen; öbür süreçlerde en geç
  `slug_eslemesi.OMUR` sonra.
* **Site haritası** — `besleme/bellek.py` kendi sinyallerini bağlar
  (aile modelleri oradan biliniyor).

**Bilinen sınır:** `QuerySet.update()` ve `bulk_create` sinyal göndermez.
Panelin toplu işlemleri bu yolu kullanıyorsa sayfa önbelleği en geç
`SAYFA_ONBELLEK_SANIYE` (30 sn) sonra kendiliğinden tazelenir; site
haritası özetleri kendi tazelik süresiyle. Toplu işlem anında tazelik
isterse `onbellek.surumu_artir()` çağırmalı.
"""

from __future__ import annotations

from django.db.models.signals import post_delete, post_save


def _surum(**_):
    from . import onbellek
    onbellek.surumu_artir()


def _kategori_degisti(**_):
    from taksonomi import slug_eslemesi

    from . import anasayfa_dizilimi, baglam, onbellek
    slug_eslemesi.sifirla()
    onbellek.sil(baglam.MENU_ANAHTARI)
    onbellek.sil(anasayfa_dizilimi.BURSA_KATEGORI_ANAHTARI)
    onbellek.surumu_artir()


def _ilce_degisti(**_):
    from . import baglam, onbellek
    onbellek.sil(baglam.ILCE_ANAHTARI)
    onbellek.surumu_artir()


def bagla() -> None:
    from taksonomi.models import Ilce, Kategori, KategoriTur

    from .models import Haber, Konu, KonuHaber, ResmiIlan, SonDakika

    for model in (Haber, Konu, KonuHaber, ResmiIlan, SonDakika):
        for sinyal in (post_save, post_delete):
            sinyal.connect(_surum, sender=model,
                           dispatch_uid=f"bh-surum-{model.__name__}-{sinyal is post_save}")
    for model in (Kategori, KategoriTur):
        for sinyal in (post_save, post_delete):
            sinyal.connect(_kategori_degisti, sender=model,
                           dispatch_uid=f"bh-kategori-{model.__name__}-{sinyal is post_save}")
    for sinyal in (post_save, post_delete):
        sinyal.connect(_ilce_degisti, sender=Ilce,
                       dispatch_uid=f"bh-ilce-{sinyal is post_save}")
