# -*- coding: utf-8 -*-
"""Motor önerilerini döneme ve güvene göre toplu onaylar (5 Eylül 2026).

    python manage.py konu_onayla --son 2021-12-31          # 2021 sonuna kadar bitenler
    python manage.py konu_onayla --bas 2020-01-01 --guven 70
    python manage.py konu_onayla --son 2021-12-31 --geri   # onayı geri al (bekliyor)
    python manage.py konu_onayla --son 2021-12-31 --kuru   # yalnız say

Kullanıcı 5 Eylül 2026'da "2021'e kadar olan haberlere uygula" dedi:
arşivin eski bölümünde tek tek panel onayı beklemek anlamsız, dönem
toplu açılır. Yalnız **motor** kaynaklı ve **bekliyor** durumundaki
dosyalara dokunur; editörün reddettiği ya da elle açtığı dosya bu
komutla değişmez. `--geri` yalnız bu komutun (ya da eşiğin) onayladığı
dosyaları geri alır: editör onayı (`onaylayan` dolu) korunur.
"""

from __future__ import annotations

from datetime import date

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from icerik.models import Konu


class Command(BaseCommand):
    help = "Motor önerilerini döneme/güvene göre toplu onaylar ya da geri alır."

    def add_arguments(self, parser):
        parser.add_argument("--bas", help="Dosyanın bitişi bu tarihte ya da sonrasında (YYYY-AA-GG)")
        parser.add_argument("--son", help="Dosyanın bitişi bu tarihte ya da öncesinde (YYYY-AA-GG)")
        parser.add_argument("--guven", type=int, default=0, help="En az güven (0-100)")
        parser.add_argument("--geri", action="store_true",
                            help="Onayı geri al: komut/eşik onaylılarını 'bekliyor' yap")
        parser.add_argument("--kuru", action="store_true", help="Yazma, yalnız say")

    def handle(self, *args, **secenek):
        bas, son = _tarih(secenek.get("bas")), _tarih(secenek.get("son"))
        if not bas and not son and not secenek["guven"]:
            raise CommandError("En az bir süzgeç ver: --bas, --son ya da --guven.")
        sorgu = Konu.objects.filter(kaynak=Konu.KAYNAK_MOTOR, guven__gte=secenek["guven"])
        if bas:
            sorgu = sorgu.filter(bitis__gte=bas)
        if son:
            sorgu = sorgu.filter(bitis__lte=son)
        if secenek["geri"]:
            sorgu = sorgu.filter(onay=Konu.ONAY_ONAYLI, onaylayan__isnull=True)
            yeni = {"onay": Konu.ONAY_BEKLIYOR, "onay_zamani": None}
            fiil = "geri alınacak"
        else:
            sorgu = sorgu.filter(onay=Konu.ONAY_BEKLIYOR)
            yeni = {"onay": Konu.ONAY_ONAYLI, "onay_zamani": timezone.now()}
            fiil = "onaylanacak"
        sayi = sorgu.count()
        self.stdout.write(f"{sayi} dosya {fiil}")
        if secenek["kuru"] or not sayi:
            return
        sorgu.update(**yeni)
        self.stdout.write(self.style.SUCCESS(
            f"Bitti. Sitede onaylı dosya: {Konu.objects.filter(onay=Konu.ONAY_ONAYLI).count()}, "
            f"bekleyen: {Konu.objects.filter(onay=Konu.ONAY_BEKLIYOR).count()}"))


def _tarih(metin):
    if not metin:
        return None
    try:
        return date.fromisoformat(metin)
    except ValueError as h:
        raise CommandError(f"Tarih anlaşılmadı: {metin}") from h
