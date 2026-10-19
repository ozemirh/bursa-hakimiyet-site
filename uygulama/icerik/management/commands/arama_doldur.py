"""Arama metnini (`HaberArama`) toplu doldurur.

    python manage.py arama_doldur              # yalnız satırı olmayan haberler
    python manage.py arama_doldur --hepsi      # hepsini yeniden yazar
    python manage.py arama_doldur --parti 10000

Kayıt kancası (`icerik/apps.py`) tek tek kaydedilen haberi kendisi
tazeler; bu komut kancanın görmediği yollar içindir: ilk kurulum, göç
(`pg_goc`), `bulk_create` / `update()` kullanan toplu onarımlar
(`metin_temizle`, `goc_al`).

Arşiv tablosuna YAZMAZ; yalnız okur. Kimlik sırasıyla, partiler hâlinde
ilerler ve her parti tek `INSERT … ON CONFLICT` sorgusudur — yarıda
kesilirse yeniden çalıştırmak güvenlidir.
"""

from __future__ import annotations

import time

from django.core.management.base import BaseCommand

from icerik import arama
from icerik.models import Haber, HaberArama


class Command(BaseCommand):
    help = "Haberlerin normalize arama metnini (HaberArama) doldurur."

    def add_arguments(self, ayristirici):
        ayristirici.add_argument("--hepsi", action="store_true",
                                 help="Var olan satırları da yeniden yazar.")
        ayristirici.add_argument("--parti", type=int, default=5000)

    def handle(self, *args, hepsi=False, parti=5000, **kw):
        ayrinti = kw.get("verbosity", 1)
        t0 = time.perf_counter()
        sorgu = Haber.objects.order_by("id")
        if not hepsi:
            sorgu = sorgu.filter(arama__isnull=True)
        son, toplam = -1, 0
        while True:
            satirlar = list(sorgu.filter(id__gt=son)
                            .values_list("id", "baslik", "spot")[:parti])
            if not satirlar:
                break
            toplam += arama.yaz(arama.satir_kur(i, b, s) for i, b, s in satirlar)
            son = satirlar[-1][0]
            if ayrinti >= 2:
                self.stdout.write(f"  {toplam:>9,} satır · son kimlik {son}")
        sure = time.perf_counter() - t0
        self.stdout.write(
            f"arama_doldur: {toplam:,} satır yazıldı, {sure:.1f} sn; "
            f"tabloda {HaberArama.objects.count():,} satır, "
            f"haber {Haber.objects.count():,}.")
