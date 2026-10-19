# -*- coding: utf-8 -*-
"""Arşivin düz metin alanlarındaki kodlama artıklarını onarır.

Arşiv eski siteden olduğu gibi alındı; başlık ve spotlarda dört tür artık
kaldı — çözülmemiş varlık kaçışı (`Ug&#774;ur`), ayrışmış harf
("Atatu" + U+0308), görünmez karakter (sıfır genişlikli boşluk, BOM) ve
boşluk çeşitleri. Onarım kuralı tek yerde: `icerik/temizle.metin_duzelt`.

    python manage.py metin_temizle --dene     # yalnız sayar, yazmaz
    python manage.py metin_temizle            # yazar

**Gövdeye dokunmaz.** Gövde HTML'dir ve orada `&amp;` kaçışı doğrudur.
**Slug'a dokunmaz.** Adres donmuştur; başlığın düzelmesi adresi değiştirmez.
U+FFFD (`&#65533;`) taşıyan kayıtlar onarılamaz — özgün karakter kodlama
hatasında kaybolmuş; sayılır ve raporlanır, uydurulmaz.
"""

import time

from django.core.management.base import BaseCommand
from django.db import transaction

from medya.models import FotoGaleri, KoseYazisi, Video, Yazar

from ... import arama
from ...models import Haber
from ...temizle import KURTARILAMAZ, metin_duzelt

# (model, alanlar). Yalnız DÜZ METİN alanları; gövde ve slug listede yok.
HEDEFLER = [
    (Haber, ["baslik", "spot"]),
    (Video, ["baslik", "spot"]),
    (KoseYazisi, ["baslik", "spot"]),
    (FotoGaleri, ["baslik"]),
    (Yazar, ["ad"]),
]

YIGIN = 500


class Command(BaseCommand):
    help = "Başlık ve spotlardaki kodlama artıklarını onarır."

    def add_arguments(self, ayrist):
        ayrist.add_argument("--dene", action="store_true",
                            help="Yazmadan sayar.")
        ayrist.add_argument("--bosluk", action="store_true",
                            help="Kırılmaz/dar boşlukları da sıradan "
                                 "boşluğa indirir (ayrı karar).")

    def handle(self, *args, **secim):
        dene, bosluk = secim["dene"], secim["bosluk"]
        basladi = time.time()
        toplam_tarandi = toplam_degisen = toplam_kurtarilamaz = 0

        for model, alanlar in HEDEFLER:
            tarandi, degisen, kurtarilamaz, ornek = self._model_gec(
                model, alanlar, dene, bosluk)
            toplam_tarandi += tarandi
            toplam_degisen += degisen
            toplam_kurtarilamaz += kurtarilamaz
            self.stdout.write("%-14s tarandı %7d · düzelen %5d%s" % (
                model.__name__, tarandi, degisen,
                " · kurtarılamaz %d" % kurtarilamaz if kurtarilamaz else ""))
            for eski, yeni in ornek:
                self.stdout.write("    %s" % eski[:96])
                self.stdout.write("  → %s" % yeni[:96])

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(
            "tarandı %d · düzelen %d · kurtarılamaz %d · %.1f sn%s" % (
                toplam_tarandi, toplam_degisen, toplam_kurtarilamaz,
                time.time() - basladi, " (deneme turu)" if dene else "")))

    def _model_gec(self, model, alanlar, dene, bosluk):
        tarandi = degisen = kurtarilamaz = 0
        ornek = []
        yigin = []
        for kayit in model.objects.only("pk", *alanlar).iterator(
                chunk_size=2000):
            tarandi += 1
            bu_kayit_degisti = False
            for alan in alanlar:
                eski = getattr(kayit, alan) or ""
                yeni = metin_duzelt(eski, bosluk)
                if yeni == eski:
                    continue
                setattr(kayit, alan, yeni)
                bu_kayit_degisti = True
                if KURTARILAMAZ in yeni:
                    kurtarilamaz += 1
                if len(ornek) < 3 and alan == alanlar[0]:
                    ornek.append((eski, yeni))
            if not bu_kayit_degisti:
                continue
            degisen += 1
            yigin.append(kayit)
        # YAZMA TARAMADAN SONRA. İlk denemede yığın dolunca yazılıyordu ve
        # SQLite açık imleçle aynı tabloya yazınca **satır atlıyordu**:
        # ikinci deneme turu 3 kayıt daha buldu. Değişen kayıt sayısı
        # ölçüldü (4.887), bellekte tutmak sorun değil.
        if not dene:
            for bas in range(0, len(yigin), YIGIN):
                self._yaz(model, yigin[bas:bas + YIGIN], alanlar)
        return tarandi, degisen, kurtarilamaz, ornek

    @staticmethod
    def _yaz(model, yigin, alanlar):
        with transaction.atomic():
            model.objects.bulk_update(yigin, alanlar, batch_size=YIGIN)
            if model is Haber:
                # `bulk_update` kayıt kancasını çağırmaz; düzelen başlık/spot
                # aramaya AYNI işlemde yansır (Paket L2). Kayıtlar
                # `only("pk", "baslik", "spot")` ile yüklendi, ek sorgu yok.
                arama.yaz(arama.satir_kur(h.pk, h.baslik, h.spot) for h in yigin)
