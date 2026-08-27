"""Var olan haber–kaynak bağlarını kaynak kapısından geçirir.

Neden ayrı bir komut: `goc_al` yalnız **bağ ekler** (`ignore_conflicts`), hiç
silmez. Kapı (`icerik/goc_kaynak.py`) devreye girdiğinde bundan sonraki
kayıtlar temiz gelir ama **daha önce kurulmuş yanlış bağlar yerinde kalır**.
271.205 haberi yeniden okumak ~55 dakika sürer; oysa yapılacak iş yalnızca ara
tabloda bir silme. Bu komut o silmeyi yapar ve saniyeler sürer.

`Kaynak` kayıtlarının kendisi **silinmez**. Gerekçe: kaydı silmek/pasifleştirmek
bir çözüm değil, izin kaybıdır — hangi haberin hangi yanlış değere bağlandığı
bilgisi de gider. Bağ kopar, kayıt kalır; sayısı raporlanır.

Kullanım:
    python manage.py kaynak_denetle --kuru     # yalnız sayar
    python manage.py kaynak_denetle
"""

from __future__ import annotations

from collections import Counter

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Count

from icerik.goc_kaynak import kaynak_kabul
from icerik.models import Haber
from taksonomi.models import Kaynak

PARCA = 20_000


class Command(BaseCommand):
    help = "Yanlış kurulmuş haber–kaynak bağlarını kopartır (kayıtları silmez)."

    def add_arguments(self, parser):
        parser.add_argument("--kuru", action="store_true",
                            help="yazmaz, yalnız ne olacağını sayar")

    def handle(self, *args, **s):
        y = self.stdout.write
        ara = Haber.kaynaklar.through

        kabul_id, ret_id = [], []
        ret_sayisi: Counter = Counter()
        ret_bag: Counter = Counter()

        for k in Kaynak.objects.annotate(n=Count("haberler")):
            kabul, neden = kaynak_kabul(k.ad)
            if kabul:
                kabul_id.append(k.id)
            else:
                ret_id.append(k.id)
                ret_sayisi[neden] += 1
                ret_bag[neden] += k.n

        onceki = ara.objects.count()
        kopacak = ara.objects.filter(kaynak_id__in=ret_id).count()

        y("")
        y(f"Kaynak kaydı      : {len(kabul_id) + len(ret_id):,}".replace(",", "."))
        y(f"  kapıdan geçen   : {len(kabul_id):,}".replace(",", "."))
        y(f"  reddedilen      : {len(ret_id):,}".replace(",", "."))
        y("")
        y(f"  {'ret nedeni':30} {'kayıt':>7} {'bağ':>10}")
        for neden, adet in ret_bag.most_common():
            y(f"  {neden:30} {ret_sayisi[neden]:>7,} {adet:>10,}".replace(",", "."))
        y("")
        y(f"Bağ öncesi        : {onceki:,}".replace(",", "."))
        y(f"Kopacak bağ       : {kopacak:,}".replace(",", "."))

        if s["kuru"]:
            y(self.style.WARNING("KURU ÇALIŞMA — hiçbir şey silinmedi."))
            return

        # Parça parça ve her parça ayrı işlemde: SQLite `delete` günlüğünde
        # uzun bir yazma işlemi aynı dosyayı okuyan süreçleri bloklar.
        silinen = 0
        while True:
            kimlikler = list(
                ara.objects.filter(kaynak_id__in=ret_id)
                .values_list("id", flat=True)[:PARCA])
            if not kimlikler:
                break
            with transaction.atomic():
                silinen += ara.objects.filter(id__in=kimlikler).delete()[0]

        kalan = ara.objects.count()
        kaynaksiz = Haber.objects.filter(kaynaklar__isnull=True).count()
        y("")
        y(self.style.SUCCESS(
            f"Kopartılan bağ {silinen:,} · kalan bağ {kalan:,} · "
            f"kaynağı olmayan haber {kaynaksiz:,}".replace(",", ".")))
        y("Kaynak kayıtlarının kendisi silinmedi; boşta kalanlar duruyor.")
