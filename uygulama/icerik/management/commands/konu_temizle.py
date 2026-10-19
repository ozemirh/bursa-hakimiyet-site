# -*- coding: utf-8 -*-
"""Kuralı çiğneyen onaylı konu dosyalarını onay beklemeye geri alır — ve geri yükler.

    python manage.py konu_temizle --kuru --ornek 20
    python manage.py konu_temizle --yaz D:\\bursa-hakimiyet-pg\\konu_geri_alma_2026-10-19.json
    python manage.py konu_temizle --geri-yukle D:\\bursa-hakimiyet-pg\\konu_geri_alma_2026-10-19.json

**Neden (19 Ekim 2026, Paket M).** 5 Eylül'de 19.966 dosya `konu_tara
--onay-esigi` ve `konu_onayla` ile toplu onaylandı; hiçbirini bir editör
tek tek onaylamadı. Kullanıcının "konu değil" dediği periyodik türler (borsa
açılışı 300 haber, "tarihte bugün" 160, Brent, Loto, BUSKİ kesintisi, fiyat
endeksleri) bu yolla sitede onaylı dosya olarak durdu.

**Ne yapar.** Motor kaynaklı, onaylı ve editör eli değmemiş (`onaylayan`
boş) her dosyanın üyelerine iki ölçüt uygulanır; biri tutarsa dosya **onay
beklemeye** alınır:

1. `konu_motoru.periyodik_gerekce` — motorun bugünkü kuralı: üyelerin
   yarısından fazlası periyodik başlık kalıbında ya da dosya yapısal olarak bir dizi
   (≥15 haber, her gün bir tane, gelişme dili <%5).
2. Değerlendirme sezgisi (DEGERLENDIRME-2026-10 §4, "210 şüpheli dosya"):
   aynı yapısal ölçüt, gelişme dili yalnız KÖKTEN sayılarak. Motor artık
   yüzeye de bakıyor (`gelisme_var`), bu yüzden o listenin birkaç dosyası
   1. ölçütten geçer; değerlendirmede adı geçen liste eksiksiz editöre
   gitsin diye ikinci ölçüt ayrıca uygulanır. Silinmez, reddedilmez: karar editörün, panelde tek tek.
Toplu ret bu komutta yok — bilerek.

**Geri alınabilir.** `--yaz <dosya>` önce JSON'u yazar (dosya kimliği,
önceki onay, onay zamanı, neden), sonra veritabanını değiştirir.
`--geri-yukle <dosya>` aynı dosyaları önceki onayına döndürür; editörün bu
arada karar verdiği (onayladığı, reddettiği) ya da silinen dosyaya
dokunmaz, sayısını raporlar. Dosya depo dışına yazılmalı: veri, kod değil.

Geri alınan dosya `geri_alma` alanında nedenini taşır; `konu_tara` onu
yeniden taramada silmez (bkz. o komutun notu). Sitede onaysız dosya 404'tür.
"""

from __future__ import annotations

import json
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from icerik import konu_motoru, onbellek
from icerik.management.commands.konu_tara import _Sessiz
from icerik.models import Konu, KonuHaber

NEDEN_ONEKI = "19 Ekim 2026 temizliği — "


class Command(BaseCommand):
    help = "Periyodik görünen onaylı konu dosyalarını onay beklemeye alır; geri yükler."

    def add_arguments(self, parser):
        grup = parser.add_mutually_exclusive_group(required=True)
        grup.add_argument("--kuru", action="store_true", help="Yazma; yalnız say.")
        grup.add_argument("--yaz", metavar="DOSYA",
                          help="Geri alma listesini bu JSON dosyasına yaz ve uygula.")
        grup.add_argument("--geri-yukle", metavar="DOSYA",
                          help="Bu JSON dosyasındaki dosyaları önceki onayına döndür.")
        parser.add_argument("--ornek", type=int, default=0,
                            help="Rapora bu kadar örnek dosya bas.")

    def handle(self, *args, **secenek):
        if not secenek.get("verbosity", 1):
            self.stdout = _Sessiz()
        if secenek.get("geri_yukle"):
            return self._geri_yukle(Path(secenek["geri_yukle"]))
        if secenek.get("yaz") and Path(secenek["yaz"]).exists():
            raise CommandError(f"{secenek['yaz']} zaten var; üzerine yazılmaz "
                               "(geri yükleme kaynağı).")
        t0 = time.time()
        adaylar = self._adaylar()
        bag = sum(a["haber_sayisi"] for a in adaylar)
        self.stdout.write(f"{len(adaylar)} dosya onay beklemeye alınacak "
                          f"({bag} haber bağı; {time.time() - t0:.0f} s)")
        for a in sorted(adaylar, key=lambda a: -a["haber_sayisi"])[:secenek["ornek"]]:
            self.stdout.write(f"  #{a['id']} {a['ad']} · {a['haber_sayisi']} haber · {a['neden']}")
        if secenek["kuru"] or not adaylar:
            return
        yol = Path(secenek["yaz"])
        yol.parent.mkdir(parents=True, exist_ok=True)
        yol.write_text(json.dumps({
            "olusturma": timezone.now().isoformat(),
            "komut": "konu_temizle",
            "aciklama": "Onay beklemeye alınan dosyalar ve önceki durumları. "
                        "Geri yükleme: manage.py konu_temizle --geri-yukle <bu dosya>",
            "toplam": {"dosya": len(adaylar), "bag": bag},
            "dosyalar": adaylar,
        }, ensure_ascii=False, indent=1), encoding="utf-8")
        with transaction.atomic():
            for a in adaylar:
                Konu.objects.filter(pk=a["id"], onay=Konu.ONAY_ONAYLI,
                                    onaylayan__isnull=True).update(
                    onay=Konu.ONAY_BEKLIYOR, onay_zamani=None,
                    geri_alma=(NEDEN_ONEKI + a["neden"])[:300])
        # update() kayıt sinyali göndermez; sayfa önbelleğinin yayın sürümü elle.
        onbellek.surumu_artir()
        self.stdout.write(self.style.SUCCESS(
            f"{len(adaylar)} dosya onay beklemeye alındı; liste: {yol}. Sitede onaylı: "
            f"{Konu.objects.filter(onay=Konu.ONAY_ONAYLI).count()}"))

    # ------------------------------------------------------------ seçim
    def _adaylar(self) -> list[dict]:
        hedef = {k.pk: k for k in Konu.objects.filter(
            kaynak=Konu.KAYNAK_MOTOR, onay=Konu.ONAY_ONAYLI, onaylayan__isnull=True)}
        uyeler: dict[int, list] = defaultdict(list)
        for kid, baslik, tarih in (KonuHaber.objects.filter(konu_id__in=list(hedef))
                                   .values_list("konu_id", "haber__baslik", "tarih")
                                   .iterator(chunk_size=20000)):
            uyeler[kid].append((tarih, baslik))
        cikti = []
        for kid, konu in sorted(hedef.items()):
            liste = sorted(uyeler.get(kid, ()))
            neden = konu_motoru.periyodik_gerekce(liste) or _degerlendirme_sezgisi(liste)
            if not neden:
                continue
            cikti.append({
                "id": kid, "slug": konu.slug, "ad": konu.ad,
                "haber_sayisi": len(uyeler.get(kid, ())),
                "neden": neden,
                "onceki": {
                    "onay": konu.onay,
                    "onay_zamani": konu.onay_zamani.isoformat() if konu.onay_zamani else None,
                    "onaylayan_id": konu.onaylayan_id,
                    "geri_alma": konu.geri_alma,
                },
            })
        return cikti

    # ------------------------------------------------------------ geri yükleme
    def _geri_yukle(self, yol: Path):
        if not yol.exists():
            raise CommandError(f"{yol} yok.")
        veri = json.loads(yol.read_text(encoding="utf-8"))
        dosyalar = veri.get("dosyalar") or []
        mevcut = {k.pk: k for k in Konu.objects.filter(pk__in=[d["id"] for d in dosyalar])}
        yuklenen = silinmis = karar = 0
        with transaction.atomic():
            for d in dosyalar:
                konu = mevcut.get(d["id"])
                if konu is None:
                    silinmis += 1
                    continue
                # Yalnız bu komutun bıraktığı hâl geri döner: editör bu arada
                # onayladıysa, reddettiyse ya da nedeni sildiyse karar onundur.
                if konu.onay != Konu.ONAY_BEKLIYOR or konu.onaylayan_id \
                        or not konu.geri_alma.startswith(NEDEN_ONEKI):
                    karar += 1
                    continue
                onceki = d.get("onceki") or {}
                zaman = onceki.get("onay_zamani")
                konu.onay = onceki.get("onay") or Konu.ONAY_ONAYLI
                konu.onay_zamani = datetime.fromisoformat(zaman) if zaman else None
                konu.geri_alma = onceki.get("geri_alma") or ""
                konu.save(update_fields=["onay", "onay_zamani", "geri_alma"])
                yuklenen += 1
        self.stdout.write(self.style.SUCCESS(
            f"{yuklenen} dosya önceki onayına döndü; {karar} dosyaya editör karar "
            f"verdiği için dokunulmadı; {silinmis} dosya artık yok."))


def _degerlendirme_sezgisi(uyeler) -> str:
    """DEGERLENDIRME-2026-10 §4'teki ölçüm, aynen: ≥15 haber, gün/haber >0,8,
    gelişme dili (yalnız kökten) <%5."""
    n = len(uyeler)
    if n < konu_motoru.PERIYODIK_EN_AZ_UYE:
        return ""
    gun = len({t for t, _ in uyeler})
    gelisme = sum(1 for _, b in uyeler if any(
        p.kok.startswith(konu_motoru.GELISME) for p in konu_motoru.parcala(b)))
    if konu_motoru.Motor._periyodik_mi(n, gun, gelisme):
        return (f"değerlendirme sezgisi: {n} haber, gün/haber {gun / n:.2f}, "
                f"kökte gelişme dili {gelisme}/{n}")
    return ""
