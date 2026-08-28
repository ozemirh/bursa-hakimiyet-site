"""Var olan haberlerin ilçe alanını başlık+spottan doldurur.

Neden ayrı komut: `ilce` bilgisi arşivde yok, **türetiliyor** (bkz.
`icerik/goc_ilce.py`). Türetim başlık ve spota bakar; ikisi de zaten
veritabanında. Yani 320 bin JSON dosyasını yeniden okumaya gerek YOK —
komut tamamen veritabanı içinde çalışır ve saniyeler sürer.

Var olan ilçe değerini EZMEZ: elle düzeltilmiş bir kaydı türetim bozmasın.
`--uzerine-yaz` ile bu davranış kapatılabilir.

Kullanım:
    python manage.py ilce_doldur --kuru
    python manage.py ilce_doldur
"""

from __future__ import annotations

from collections import Counter

from django.core.management.base import BaseCommand
from django.db import transaction

from icerik.goc_ilce import ilce_bul, kaliplar
from icerik.models import Haber
from taksonomi.models import Ilce

PARCA = 5_000


class Command(BaseCommand):
    help = "Haberlerin ilçe alanını başlık ve spottan türetir."

    def add_arguments(self, parser):
        parser.add_argument("--kuru", action="store_true",
                            help="yazmaz, yalnız ne olacağını sayar")
        parser.add_argument("--uzerine-yaz", action="store_true",
                            help="dolu ilçe alanlarını da yeniden türetir")

    def handle(self, *args, **s):
        y = self.stdout.write
        ilceler = {i.ad: i for i in Ilce.objects.all()}
        kalip = kaliplar(ilceler)

        qs = Haber.objects.all()
        if not s["uzerine_yaz"]:
            qs = qs.filter(ilce__isnull=True)

        sayac = Counter()
        dagilim = Counter()
        yigin: list[Haber] = []
        toplam = qs.count()

        y("")
        y(f"İlçe        : {len(ilceler)}")
        y(f"Taranan kayıt: {toplam:,}".replace(",", "."))

        for h in qs.only("id", "baslik", "spot", "ilce").iterator(chunk_size=5000):
            ad = ilce_bul(h.baslik, h.spot, kalip)
            if ad is None:
                sayac["ilçesi bulunamadı"] += 1
                continue
            sayac["ilçe atandı"] += 1
            dagilim[ad] += 1
            h.ilce = ilceler[ad]
            yigin.append(h)
            if len(yigin) >= PARCA and not s["kuru"]:
                with transaction.atomic():
                    Haber.objects.bulk_update(yigin, ["ilce"], batch_size=1000)
                yigin.clear()

        if yigin and not s["kuru"]:
            with transaction.atomic():
                Haber.objects.bulk_update(yigin, ["ilce"], batch_size=1000)

        y("")
        for k, n in sayac.most_common():
            oran = 100 * n / toplam if toplam else 0
            y(f"  {k:22} {n:>9,}  %{oran:5.1f}".replace(",", "."))
        y("")
        y("  ilçeye göre dağılım")
        for ad, n in dagilim.most_common():
            y(f"    {ad:20} {n:>8,}".replace(",", "."))

        if s["kuru"]:
            y(self.style.WARNING("\nKURU ÇALIŞMA — hiçbir şey yazılmadı."))
        else:
            dolu = Haber.objects.filter(ilce__isnull=False).count()
            y(self.style.SUCCESS(
                f"\nİlçesi olan haber: {dolu:,}".replace(",", ".")))
