# -*- coding: utf-8 -*-
"""Görsel türevlerini önceden üretir — tüm arşivi DEĞİL, görünen kesimi.

    python manage.py gorsel_turev_uret                    # son 30 gün + vitrin
    python manage.py gorsel_turev_uret --son-gun 7
    python manage.py gorsel_turev_uret --referans 2026-10-19
    python manage.py gorsel_turev_uret --vitrin-yok       # yalnız tarih penceresi
    python manage.py gorsel_turev_uret --kuru             # üretme, yalnız say

Türevler zaten isteğe bağlı üretiliyor (`icerik/gorsel_turev.py`); bu komut
ilk okurun beklemesini ortadan kaldırır. Kaynak BİR kez çözülür, beş genişlik
ve og:image kırpımı ondan iner. Taze türev atlanır; komut yeniden
çalıştırılabilir.

**Tarih penceresi** `--referans`tan geriye sayılır. Verilmezse referans
yayındaki EN YENİ haberin tarihidir, bugün değil: taze akış durduğunda
(19 Ekim 2026'da son haber 6 Eylül'de) "son 30 gün" boş küme olurdu.

**Vitrin**: anasayfa havuzu ve "daha fazla göster"in ilk dilimleri, her
bölümün ilk sayfası, Bursaspor, galeri ve video kapakları, yazar portreleri,
sitenin panel fotoğrafları. Tarihten bağımsız olarak her gün görünenler.

Tüm arşivi (264 bin görsel) üretmek bilinçli olarak YOK: hepsi okunmuyor ve
gereken, istek anında zaten üretiliyor.
"""

from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from icerik import gorsel_turev as gt
from icerik.models import Haber
from icerik.templatetags.gorsel_etiket import kaynak_yolu

VITRIN_ANASAYFA = 200      # anasayfa havuzu + birkaç "daha fazla" dilimi
VITRIN_BOLUM = 20          # bölüm sayfasının ilk sayfası
VITRIN_MEDYA = 60


class Command(BaseCommand):
    help = "Görsel türevlerini (WebP genişlikleri + og:image) önceden üretir."

    def add_arguments(self, parser):
        parser.add_argument("--son-gun", type=int, default=30)
        parser.add_argument("--referans", help="YYYY-AA-GG; varsayılan: en yeni haber")
        parser.add_argument("--vitrin-yok", action="store_true")
        parser.add_argument("--og-yok", action="store_true")
        parser.add_argument("--genislikler", default=",".join(map(str, gt.GENISLIKLER)))
        parser.add_argument("--isci", type=int, default=4)
        parser.add_argument("--kuru", action="store_true")

    # --- seçim ---------------------------------------------------------------

    def _pencere(self, gun, referans):
        if referans:
            try:
                ref = timezone.make_aware(datetime.strptime(referans, "%Y-%m-%d")
                                          + timedelta(days=1))
            except ValueError:
                raise CommandError("--referans YYYY-AA-GG olmalı")
        else:
            ref = (Haber.yayindakiler().order_by("-yayin_zamani")
                   .values_list("yayin_zamani", flat=True).first())
            if ref is None:
                return [], None
        alt = ref - timedelta(days=gun)
        nesneler = (Haber.yayindakiler()
                    .filter(gorsel_var=True, yayin_zamani__gte=alt, yayin_zamani__lte=ref)
                    .only("id", "gorsel_var", "gorsel_dosya"))
        return list(nesneler), (alt, ref)

    def _vitrin(self):
        from medya.models import FotoGaleri, Video, Yazar
        from taksonomi.models import Kategori

        ortak = ("id", "gorsel_var", "gorsel_dosya")
        nesneler = list(Haber.yayindakiler().filter(gorsel_var=True)
                        .order_by("-yayin_zamani").only(*ortak)[:VITRIN_ANASAYFA])
        for kat in Kategori.objects.filter(haberler__isnull=False).distinct().only("id"):
            nesneler += list(Haber.yayindakiler().filter(kategori=kat)
                             .order_by("-yayin_zamani").only(*ortak)[:VITRIN_BOLUM])
        for model in (FotoGaleri, Video):
            nesneler += list(model.yayindakiler().filter(gorsel_var=True)
                             .order_by("-yayin_zamani").only(*ortak)[:VITRIN_MEDYA])
        nesneler += list(Yazar.listedekiler().filter(gorsel_var=True).only(*ortak))
        return nesneler + ["site/uludag.jpg", "site/yesil-cami.jpg"]

    # --- iş ------------------------------------------------------------------

    def handle(self, *args, **o):
        genislikler = [int(g) for g in o["genislikler"].split(",") if g.strip()]
        yanlis = [g for g in genislikler if g not in gt.GENISLIKLER]
        if yanlis:
            raise CommandError(f"beyaz liste dışı genişlik: {yanlis}")

        bas = time.perf_counter()
        nesneler, aralik = self._pencere(o["son_gun"], o["referans"])
        if aralik:
            self.stdout.write(f"pencere: {aralik[0]:%Y-%m-%d} → {aralik[1]:%Y-%m-%d} "
                              f"({o['son_gun']} gün) · {len(nesneler)} haber")
        if not o["vitrin_yok"]:
            vitrin = self._vitrin()
            self.stdout.write(f"vitrin: {len(vitrin)} kayıt")
            nesneler += vitrin

        kaynaklar = sorted({k for k in (kaynak_yolu(n) for n in nesneler) if k})
        self.stdout.write(f"tekil kaynak: {len(kaynaklar)} · seçim "
                          f"{time.perf_counter() - bas:.1f} sn · kök {gt.turev_koku()}")
        if o["kuru"]:
            return

        toplam = {"uretilen": 0, "atlanan": 0, "bayt": 0, "hata": 0}
        hatalar = []
        bas = time.perf_counter()

        def is_(k):
            return gt.tum_turevler(k, genislikler, og=not o["og_yok"])

        with ThreadPoolExecutor(max_workers=max(1, o["isci"])) as havuz:
            isler = {havuz.submit(is_, k): k for k in kaynaklar}
            for sira, gelecek in enumerate(as_completed(isler), 1):
                try:
                    sonuc = gelecek.result()
                    for anahtar in ("uretilen", "atlanan", "bayt"):
                        toplam[anahtar] += sonuc[anahtar]
                except (gt.GecersizIstek, gt.GorselHatasi, gt.Mesgul, OSError) as hata:
                    toplam["hata"] += 1
                    if len(hatalar) < 10:
                        hatalar.append(f"{isler[gelecek]}: {hata}")
                if sira % 500 == 0:
                    self.stdout.write(f"  {sira}/{len(kaynaklar)} · "
                                      f"{toplam['bayt'] / 1e6:.0f} MB · "
                                      f"{time.perf_counter() - bas:.0f} sn")

        sure = time.perf_counter() - bas
        self.stdout.write(self.style.SUCCESS(
            f"bitti: {len(kaynaklar)} kaynak · {toplam['uretilen']} türev üretildi · "
            f"{toplam['atlanan']} taze atlandı · {toplam['hata']} hata · "
            f"{toplam['bayt'] / 1e6:.1f} MB yazıldı · {sure:.0f} sn"))
        for h in hatalar:
            self.stdout.write(f"  hata: {h}")
