"""F8 kesim ölçütü (b) ölçer: "adres sayıları kaynağıyla eşleşiyor".

    python manage.py site_haritasi_karsilastir --arsiv-kok D:/bursa-hakimiyet-arsiv
    python manage.py site_haritasi_karsilastir --canli --aile haber
    python manage.py site_haritasi_karsilastir --canli --sadece-indeks

İki kaynak var:

**--arsiv-kok (çevrimdışı, varsayılan yol).** Arşiv taraması sitemap'ten
çıkardığı her adresi `tum-urller{ek}.jsonl` dosyasına `{"url":…,
"ay":"2026-08"}` biçiminde yazıyor (`disa-aktarim/site_arsivleyici.py`).
Ay bilgisi doğrudan kaynak dosyanın adından geldiği için karşılaştırma
tam da F8'in istediği şey: **kaynak sitemap'teki sayı** ile **bizim
ürettiğimiz sayı**. Dosya adı eki ailenin kendi eki: haber ailesi
`tum-urller.jsonl`, diğerleri `tum-urller-<anahtar>.jsonl`.

**--canli (ağ üzerinden).** Canlı sitemap indeksi indirilir, her aylık
dosyadaki `<url>` sayılır. Kesin ama pahalı: 274 dosya, haber ailesi tek
başına yüz MB'ın üzerinde. `--sadece-indeks` yalnız dosya listesini ve
aile başına dosya sayısını karşılaştırır, içerik indirmez.

Çıkış kodu: fark varsa **1**. Böylece kesim listesinde bir kapı olarak
kullanılabilir.
"""

from __future__ import annotations

import json
import re
import sys
import urllib.request
from collections import Counter
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from besleme.aileler import SIRA, aile as aile_bul, kayitli_aileler

SITEMAP_INDEKS = "https://www.bursahakimiyet.com.tr/static/sitemap/sitemap.xml"

# Canlı siteyi çeken taraf `disa-aktarim/site_arsivleyici.py` ile aynı
# tarayıcı kimliğini kullanıyor; site tanımadığı istemciye kapanıyor.
BASLIKLAR = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/126.0.0.0 Safari/537.36"),
    "Accept-Language": "tr,en;q=0.8",
}

_LOC = re.compile(r"<loc>([^<]+)</loc>")
_DOSYA = re.compile(r"/([A-Za-z]+)_(\d{4}-\d{2})\.xml$")


class Command(BaseCommand):
    help = "Üretilen sitemap adres sayılarını kaynağıyla karşılaştırır (F8/b)."

    def add_arguments(self, ayristirici):
        ayristirici.add_argument("--arsiv-kok", default=None,
                                 help="Arşiv taramasının çıktı kökü.")
        ayristirici.add_argument("--canli", action="store_true",
                                 help="Kaynak olarak canlı sitemap'i indir.")
        ayristirici.add_argument("--sadece-indeks", action="store_true",
                                 help="--canli ile: aylık dosyaları indirme, "
                                      "yalnız dosya listesini karşılaştır.")
        ayristirici.add_argument("--aile", action="append", default=None,
                                 help="Yalnız bu aile(ler).")

    def handle(self, *args, **secenekler):
        if not secenekler["arsiv_kok"] and not secenekler["canli"]:
            raise CommandError("--arsiv-kok ya da --canli vermelisin.")

        aileler = self._aileleri_sec(secenekler["aile"])
        bizim = {a.anahtar: {o.ay: o.adet for o in a.aylar()} for a in aileler}

        if secenekler["canli"]:
            kaynak = self._canli_sayilar(secenekler["sadece_indeks"])
        else:
            kaynak = self._arsiv_sayilar(Path(secenekler["arsiv_kok"]))

        return self._rapor(aileler, bizim, kaynak,
                           sadece_dosya=secenekler["canli"] and secenekler["sadece_indeks"])

    # -- kaynaklar --

    def _arsiv_sayilar(self, kok: Path) -> dict[str, Counter]:
        """`tum-urller*.jsonl` dosyalarından ay başına adres sayısı."""
        if not kok.exists():
            raise CommandError(f"Arşiv kökü yok: {kok}")
        sonuc: dict[str, Counter] = {}
        for anahtar in SIRA:
            ek = "" if anahtar == "haber" else f"-{anahtar}"
            dosya = kok / f"tum-urller{ek}.jsonl"
            if not dosya.exists():
                # Aile hiç taranmadıysa uydurma sayı üretmiyoruz; raporda
                # "kaynak yok" satırı çıkacak.
                continue
            sayac: Counter = Counter()
            with open(dosya, encoding="utf-8-sig") as akis:
                for satir in akis:
                    satir = satir.strip()
                    if not satir:
                        continue
                    sayac[json.loads(satir)["ay"]] += 1
            sonuc[anahtar] = sayac
        if not sonuc:
            raise CommandError(
                f"{kok} altında hiç `tum-urller*.jsonl` bulunamadı.")
        return sonuc

    def _canli_sayilar(self, sadece_indeks: bool) -> dict[str, Counter]:
        onek_anahtar = {a.dosya_oneki: a.anahtar for a in
                        [aile_bul(k) for k in SIRA] if a is not None}
        ham = self._indir(SITEMAP_INDEKS)
        sonuc: dict[str, Counter] = {}
        for adres in _LOC.findall(ham):
            eslesme = _DOSYA.search(adres)
            if not eslesme:
                continue
            onek, ay = eslesme.groups()
            anahtar = onek_anahtar.get(onek)
            if anahtar is None:
                continue
            sayac = sonuc.setdefault(anahtar, Counter())
            if sadece_indeks:
                sayac[ay] = -1  # "dosya var, sayısı bilinmiyor"
                continue
            self.stderr.write(f"  indiriliyor: {onek}_{ay}.xml")
            sayac[ay] = self._indir(adres).count("<url>")
        return sonuc

    def _indir(self, adres: str) -> str:
        istek = urllib.request.Request(adres, headers=BASLIKLAR)
        with urllib.request.urlopen(istek, timeout=60) as yanit:
            return yanit.read().decode("utf-8", errors="replace")

    # -- rapor --

    def _rapor(self, aileler, bizim, kaynak, sadece_dosya=False):
        toplam_fark = 0
        for aile in aileler:
            k = kaynak.get(aile.anahtar)
            b = bizim.get(aile.anahtar, {})
            self.stdout.write("")
            self.stdout.write(self.style.MIGRATE_HEADING(
                f"{aile.ad} ({aile.dosya_oneki})"))
            if k is None:
                self.stdout.write(self.style.WARNING(
                    f"  kaynak yok — bu aile hiç taranmamış. "
                    f"Bizde {sum(b.values()):,} adres var.".replace(",", ".")))
                toplam_fark += 1
                continue
            aylar = sorted(set(k) | set(b), reverse=True)
            aile_fark = 0
            for ay in aylar:
                kaynak_adet = k.get(ay, 0)
                bizim_adet = b.get(ay, 0)
                if sadece_dosya:
                    # Yalnız dosyanın varlığı karşılaştırılıyor.
                    uyusuyor = (ay in k) == (ay in b)
                    if not uyusuyor:
                        aile_fark += 1
                        nerede = "yalnız kaynakta" if ay in k else "yalnız bizde"
                        self.stdout.write(self.style.ERROR(
                            f"  {ay}  {nerede}"))
                    continue
                fark = bizim_adet - kaynak_adet
                if fark:
                    aile_fark += abs(fark)
                    self.stdout.write(self.style.ERROR(
                        f"  {ay}  kaynak {kaynak_adet:>7,}  bizde {bizim_adet:>7,}"
                        f"  fark {fark:+,}".replace(",", ".")))
            toplam_fark += aile_fark
            if sadece_dosya:
                # Bu kipte adres sayısı indirilmiyor; ay sayısı konuşur.
                self.stdout.write(
                    f"  kaynakta {len(k)} ay · bizde {len(b)} ay"
                    + ("" if aile_fark else " — dosya listesi birebir"))
            elif aile_fark == 0:
                self.stdout.write(self.style.SUCCESS(
                    f"  {len(aylar)} ay, tamamı eşleşiyor "
                    f"({sum(b.values()):,} adres)".replace(",", ".")))
            else:
                self.stdout.write(
                    f"  {len(aylar)} ay · kaynak {sum(k.values()):,} · "
                    f"bizde {sum(b.values()):,}".replace(",", "."))

        # Kaynakta olup deftere hiç kaydolmamış aile: F8 "beş sitemap
        # ailesi" diyor, dördü eksikken ölçüt karşılanmış sayılamaz.
        kayitli = {a.anahtar for a in aileler}
        for anahtar in SIRA:
            if anahtar in kayitli or anahtar not in kaynak:
                continue
            adet = sum(v for v in kaynak[anahtar].values() if v > 0)
            self.stdout.write("")
            self.stdout.write(self.style.ERROR(
                f"{anahtar}: kaynakta {len(kaynak[anahtar])} ay / "
                f"{adet:,} adres var, bizde aile **kayıtlı değil**. "
                f"Modeli yazılıp `besleme_kaynaklari` ile deftere "
                f"eklenmesi gerekiyor.".replace(",", ".")))
            toplam_fark += adet or 1

        self.stdout.write("")
        if toplam_fark == 0:
            self.stdout.write(self.style.SUCCESS(
                "F8 (b): beş aile de kaynağıyla eşleşiyor."))
            return
        self.stdout.write(self.style.ERROR(
            f"F8 (b) KARŞILANMADI: toplam fark {toplam_fark:,}".replace(",", ".")))
        sys.exit(1)

    def _aileleri_sec(self, istenen):
        kayitli = kayitli_aileler()
        if not istenen:
            return kayitli
        secili = []
        for anahtar in istenen:
            bulunan = aile_bul(anahtar)
            if bulunan is None:
                raise CommandError(f"{anahtar!r} ailesi deftere kayıtlı değil.")
            secili.append(bulunan)
        return secili
