# -*- coding: utf-8 -*-
"""Arşivi tarayıp konu dosyası önerileri yazar.

    python manage.py konu_tara                      # tüm arşiv, öneri olarak
    python manage.py konu_tara --bas 2025-01-01     # tarih aralığı
    python manage.py konu_tara --onay-esigi 80      # güveni ≥80 olanı onayla
    python manage.py konu_tara --kuru               # yazma, yalnız say

Motor `icerik/konu_motoru.py`; burada yalnız okuma, yazma ve rapor var.
Yeniden çalıştırınca **onay bekleyen motor önerileri silinir** ve baştan
yazılır; onaylı ve reddedilmiş dosyalara dokunulmaz. Onaylı bir dosyayla
üyelerinin yarısından çoğu örtüşen öneri yazılmaz (aynı dosya iki kez
önerilmesin).

Başlıklar 1.038.474 satırdan `values_list` ile ham okunur; model nesnesi
kurulmaz. Ölçüm 5 Eylül 2026: okuma ~40 s, zincirleme ~6 dk.
"""

from __future__ import annotations

import time
from collections import Counter
from datetime import date, timedelta

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from icerik import konu_motoru
from icerik.arama_metni import slugla
from icerik.models import Haber, Konu, KonuHaber

# Yargı dili geçen dosyalara editörün göreceği uyarı; arac/konular.json'daki
# "hassas" alanının karşılığı. Metin demo dosyasından alındı.
HASSAS_KOKLER = ("tutukla", "gözaltı", "soruştur", "dava", "iddianame",
                 "rüşvet", "cinayet", "taciz", "istismar", "dolandır")
HASSAS_UYARI = ("Yargı süreci sürüyor olabilir. Masumiyet karinesi korunur: "
                "kesin hüküm dili kullanılmaz, şüphelinin suçlamaları reddettiği "
                "belirtilir.")
ACIK_GUN = 30   # son haber bu kadar yakınsa dosya "sürüyor"


class Command(BaseCommand):
    help = "Arşivi tarar, konu dosyası önerileri yazar."

    def add_arguments(self, parser):
        parser.add_argument("--bas", help="Başlangıç tarihi (YYYY-AA-GG)")
        parser.add_argument("--son", help="Bitiş tarihi, hariç (YYYY-AA-GG)")
        parser.add_argument("--onay-esigi", type=int, default=None,
                            help="Güveni bu değerin üstündeki öneriler onaylı yazılır.")
        parser.add_argument("--kuru", action="store_true",
                            help="Yazma; yalnız sonucu raporla.")
        parser.add_argument("--ornek", type=int, default=0,
                            help="Rapora bu kadar örnek dosya bas.")
        parser.add_argument("--sifirla", action="store_true",
                            help="Motor kaynaklı ve editör eli değmemiş (onaylayan boş) "
                                 "BÜTÜN dosyaları sil, baştan yaz. Motor kuralı "
                                 "değişince kullanılır; editör onayı ve reddi korunur.")

    def handle(self, *args, **secenek):
        if not secenek.get("verbosity", 1):
            self.stdout = _Sessiz()
        bas = _tarih(secenek.get("bas"))
        son = _tarih(secenek.get("son"))
        t0 = time.time()

        sorgu = Haber.yayindakiler().order_by("yayin_zamani", "id")
        if bas:
            sorgu = sorgu.filter(yayin_zamani__date__gte=bas)
        if son:
            sorgu = sorgu.filter(yayin_zamani__date__lt=son)
        kayitlar = [(k, b, z.date()) for k, b, z in
                    sorgu.values_list("id", "baslik", "yayin_zamani").iterator(chunk_size=20000)]
        self.stdout.write(f"{len(kayitlar)} başlık okundu ({time.time() - t0:.0f} s)")
        if not kayitlar:
            raise CommandError("Aralıkta haber yok.")

        motor = konu_motoru.Motor()
        for _, baslik, _ in kayitlar:
            motor.say(baslik)
        zincirler = motor.zincirle(kayitlar)
        konular = motor.konular(zincirler)
        del zincirler
        self.stdout.write(f"{len(konular)} konu bulundu ({time.time() - t0:.0f} s)")
        self._rapor(konular, secenek["ornek"])
        if secenek["kuru"]:
            return

        son_gun = max(t for _, _, t in kayitlar)
        yazilan, atlanan, onaylanan = self._yaz(
            konular, son_gun, secenek.get("onay_esigi"), secenek["sifirla"])
        self.stdout.write(self.style.SUCCESS(
            f"{yazilan} konu yazıldı, {onaylanan} onaylı, {atlanan} onaylı dosyayla "
            f"örtüştüğü için atlandı ({time.time() - t0:.0f} s)"))

    # ------------------------------------------------------------ rapor
    def _rapor(self, konular, ornek):
        guven = Counter(k.guven // 10 * 10 for k in konular)
        uye = sum(len(k.uyeler) for k in konular)
        self.stdout.write(f"  bağlanan haber: {uye}")
        self.stdout.write("  güven dağılımı: " + ", ".join(
            f"{g}-{g + 9}: {n}" for g, n in sorted(guven.items())))
        for k in sorted(konular, key=lambda k: -k.guven)[:ornek]:
            self.stdout.write(f"  [{k.guven}] {k.ad} · {len(k.uyeler)} haber · "
                              f"{k.baslangic}..{k.bitis}")
            for h in k.uyeler[:3]:
                self.stdout.write(f"      {h.tarih} {h.baslik[:80]}")

    # ------------------------------------------------------------ yazma
    @transaction.atomic
    def _yaz(self, konular, son_gun: date, onay_esigi, sifirla=False):
        silinecek = Konu.objects.filter(kaynak=Konu.KAYNAK_MOTOR)
        if sifirla:
            # Komut/eşik onayı editör kararı değildir; yalnız `onaylayan`
            # dolu olan (panelden onaylanan) ve reddedilen dosyalar kalır.
            silinecek = silinecek.filter(onaylayan__isnull=True).exclude(onay=Konu.ONAY_RET)
        else:
            silinecek = silinecek.filter(onay=Konu.ONAY_BEKLIYOR)
        silinecek.delete()

        # Onaylı dosyaların üyeleri: örtüşen öneri yazılmaz.
        onayli_uyeler: dict[int, set[int]] = {}
        for konu_id, haber_id in (KonuHaber.objects
                                  .filter(konu__onay=Konu.ONAY_ONAYLI)
                                  .values_list("konu_id", "haber_id")):
            onayli_uyeler.setdefault(konu_id, set()).add(haber_id)

        mevcut_sluglar = set(Konu.objects.values_list("slug", flat=True))
        simdi = timezone.now()
        yazilan = atlanan = onaylanan = 0
        for k in konular:
            uyeler = {h.kimlik for h in k.uyeler}
            if any(len(uyeler & u) * 2 > len(uyeler) for u in onayli_uyeler.values()):
                atlanan += 1
                continue
            onayli = onay_esigi is not None and k.guven >= onay_esigi
            hassas = any(kok.startswith(HASSAS_KOKLER)
                         for h in k.uyeler for kok in h.kokler)
            konu = Konu(
                ad=k.ad[:200], slug=_slug(k, mevcut_sluglar),
                anahtarlar=k.anahtarlar,
                hassas_uyari=HASSAS_UYARI if hassas else "",
                kaynak=Konu.KAYNAK_MOTOR,
                onay=Konu.ONAY_ONAYLI if onayli else Konu.ONAY_BEKLIYOR,
                guven=k.guven, gerekce=k.gerekce,
                acik=(son_gun - k.bitis).days <= ACIK_GUN,
                baslangic=k.baslangic, bitis=k.bitis,
                haber_sayisi=len(k.uyeler),
                onay_zamani=simdi if onayli else None,
            )
            konu.save()
            KonuHaber.objects.bulk_create([
                KonuHaber(konu=konu, haber_id=h.kimlik, tarih=h.tarih, puan=k.guven)
                for h in k.uyeler])
            yazilan += 1
            onaylanan += onayli
        return yazilan, atlanan, onaylanan


class _Sessiz:
    """verbosity=0: test çıktısını kirletme."""

    def write(self, *_args, **_kwargs):
        pass


def _tarih(metin):
    if not metin:
        return None
    try:
        return date.fromisoformat(metin)
    except ValueError as h:
        raise CommandError(f"Tarih anlaşılmadı: {metin}") from h


def _slug(k, mevcut: set[str]) -> str:
    """`ece-gurel-2025-03` gibi; çakışırsa sayaç eklenir.

    Katlama `arama_metni.slugla` ile: Django'nun `slugify`'ı noktasız `ı`yı
    atıyor ve kesme işaretini siliyor — "Aziz Yıldırım" → `aziz-yldrm`,
    "Bursa'da" → `bursada`. `/konu/<slug>` bir adres olduğu için bu kusur
    arşivin deseninden ayrılıyordu (URUN-PLANI.md §51).
    """
    kok = slugla(k.ad, 180) or "konu"
    taban = f"{kok}-{k.baslangic:%Y-%m}"
    aday, n = taban, 1
    while aday in mevcut:
        n += 1
        aday = f"{taban}-{n}"
    mevcut.add(aday)
    return aday
