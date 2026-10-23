"""Arama metnini (`HaberArama`) toplu doldurur.

    python manage.py arama_doldur              # yalnız satırı olmayan haberler
    python manage.py arama_doldur --hepsi      # hepsini yeniden yazar
    python manage.py arama_doldur --parti 10000
    python manage.py arama_doldur --kimlikler 12,15,20   # yalnız bunlar

Kayıt kancası (`icerik/apps.py`) tek tek kaydedilen haberi kendisi
tazeler; bu komut kancanın görmediği yollar içindir: ilk kurulum, göç
(`pg_goc`), `bulk_create` / `update()` kullanan toplu onarımlar
(`metin_temizle`, `goc_al`). Bu iki komut 19 Ekim 2026'dan (Paket L2) beri
etkilediği kimlikleri kendisi tazeliyor; `--kimlikler` başka bir toplu
yazımdan sonra yalnız o kayıtları yeniden yazmak içindir.

Arşiv tablosuna YAZMAZ; yalnız okur. Kimlik sırasıyla, partiler hâlinde
ilerler ve her parti tek `INSERT … ON CONFLICT` sorgusudur — yarıda
kesilirse yeniden çalıştırmak güvenlidir.
"""

from __future__ import annotations

import time

from django.core.management.base import BaseCommand, CommandError

from icerik import arama
from icerik.models import Haber, HaberArama


class Command(BaseCommand):
    help = "Haberlerin normalize arama metnini (HaberArama) doldurur."

    def add_arguments(self, ayristirici):
        ayristirici.add_argument("--hepsi", action="store_true",
                                 help="Var olan satırları da yeniden yazar.")
        ayristirici.add_argument("--parti", type=int, default=5000)
        ayristirici.add_argument(
            "--kimlikler", default="",
            help="Virgülle ayrılmış haber kimlikleri; yalnız bunlar yeniden yazılır.")

    def handle(self, *args, hepsi=False, parti=5000, kimlikler="", **kw):
        ayrinti = kw.get("verbosity", 1)
        t0 = time.perf_counter()
        if kimlikler:
            try:
                liste = [int(k) for k in kimlikler.split(",") if k.strip()]
            except ValueError as hata:
                raise CommandError(f"--kimlikler tam sayı listesi olmalı: {hata}") from hata
            yazilan = arama.tazele(liste, parti=parti)
            self.stdout.write(f"arama_doldur: {yazilan:,} / {len(set(liste)):,} kimlik "
                              f"tazelendi, {time.perf_counter() - t0:.1f} sn.")
            return
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
