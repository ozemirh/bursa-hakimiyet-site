"""Arama başarım ölçümü — 56 sorguluk set (`icerik/veri/arama_olcum_sorgulari.json`).

    python manage.py arama_olc                 # yeni yol, sorgu düzeyi, 9 tur
    python manage.py arama_olc --yol eski      # 19 Ekim öncesi icontains yolu
    python manage.py arama_olc --http          # tam HTTP yanıtı (/ara)
    python manage.py arama_olc --tur 3 --sinif sonucsuz

Ölçülen iş görünümün yaptığının aynısıdır: sınırlı sayım (≤ 1.001) + ilk
sayfanın dilimi, liste olarak değerlendirilmiş. Turlar DÖNÜŞÜMLÜ koşar
(her turda 56 sorgunun hepsi), aynı sorgu art arda ölçülüp önbellek
şişirilmesin diye. Zaman sınırı ölçümde KAPALIDIR — ölçülen motorun
kendisi; `--sinirli` sınırı açar.

`--yol eski` yalnız karşılaştırma içindir: `HaberArama` tablosu olmayan
(salt okunur, migration'sız) gerçek SQLite veritabanında da çalışır.
"""

from __future__ import annotations

import json
import statistics
import time
from contextlib import nullcontext
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import connection
from django.db.models import Q

from icerik import arama
from icerik.arama_metni import sorgu_coz
from icerik.views import SAYFA_BOYU, SinirliSayfalayici, _liste

SET = Path(__file__).resolve().parents[2] / "veri" / "arama_olcum_sorgulari.json"


def _yuzdelik(degerler, oran):
    s = sorted(degerler)
    return s[min(len(s) - 1, max(0, int(round(oran * len(s))) - 1))]


class Command(BaseCommand):
    help = "56 sorguluk arama setini ölçer (p50/p95, sınıf bazında)."

    def add_arguments(self, a):
        a.add_argument("--yol", choices=("yeni", "eski"), default="yeni")
        a.add_argument("--tur", type=int, default=9)
        a.add_argument("--http", action="store_true")
        a.add_argument("--sinif", action="append")
        a.add_argument("--sinirli", action="store_true",
                       help="Zaman sınırını açık ölçer (varsayılan kapalı).")
        a.add_argument("--json", help="Ham ölçümleri bu dosyaya yazar.")

    def _sayfalayici(self, q, yol):
        if yol == "eski":
            return SinirliSayfalayici(
                _liste().filter(Q(baslik__icontains=q) | Q(spot__icontains=q)), SAYFA_BOYU)
        return arama.AramaSayfalayici(_liste(), sorgu_coz(q), SAYFA_BOYU)

    def _olc(self, q, o):
        t0 = time.perf_counter()
        if o["http"]:
            from django.test import Client
            from django.test.utils import override_settings
            with override_settings(ALLOWED_HOSTS=["*"]):
                yanit = Client().get("/ara", {"q": q})
            sure = (time.perf_counter() - t0) * 1000
            return sure, yanit.status_code, None
        sinir = arama.sure_siniri() if o["sinirli"] else nullcontext()
        try:
            with sinir:
                s = self._sayfalayici(q, o["yol"])
                adet = s._ham_sayim
                list(s.page(1).object_list)
        except arama.ZamanAsimi:
            adet = "SINIR"
        return (time.perf_counter() - t0) * 1000, 200, adet

    def handle(self, *args, **o):
        veri = json.loads(SET.read_text(encoding="utf-8"))
        siniflar = {k: v for k, v in veri["siniflar"].items()
                    if not o["sinif"] or k in o["sinif"]}
        sorgular = [(s, q) for s, liste in siniflar.items() for q in liste]
        self.stdout.write(f"motor {connection.vendor} · yol {o['yol']} · "
                          f"{'HTTP' if o['http'] else 'sorgu'} · {len(sorgular)} sorgu × "
                          f"{o['tur']} tur · set {veri['surum']}")
        olcum = {q: [] for _, q in sorgular}
        adetler = {}
        # Isınma turu: ilk bağlantı ve şablon yükleme ölçüme girmesin.
        self._olc(sorgular[0][1], o)
        for tur in range(o["tur"]):
            for _, q in sorgular:
                sure, _kod, adet = self._olc(q, o)
                olcum[q].append(sure)
                adetler[q] = adet
            self.stdout.write(f"  tur {tur + 1}/{o['tur']} bitti")
            self.stdout.flush()

        hepsi = [s for v in olcum.values() for s in v]
        self.stdout.write(f"\n{'sınıf':12} {'p50':>8} {'p95':>8} {'en kötü':>9}")
        for sinif in siniflar:
            d = [s for sn, q in sorgular if sn == sinif for s in olcum[q]]
            self.stdout.write(f"{sinif:12} {statistics.median(d):>8.1f} "
                              f"{_yuzdelik(d, .95):>8.1f} {max(d):>9.1f}")
        self.stdout.write(f"{'TOPLAM':12} {statistics.median(hepsi):>8.1f} "
                          f"{_yuzdelik(hepsi, .95):>8.1f} {max(hepsi):>9.1f}  (ms)")
        self.stdout.write("\nsorgu başına (medyan ms · sınırlı sayım):")
        for sinif, q in sorgular:
            self.stdout.write(f"  {sinif:11} {q[:44]:44} {statistics.median(olcum[q]):>8.1f} "
                              f"{adetler[q]!s:>6}")
        if o["json"]:
            Path(o["json"]).write_text(json.dumps(
                {"motor": connection.vendor, "yol": o["yol"], "http": o["http"],
                 "olcum": olcum, "adet": adetler}, ensure_ascii=False, indent=1),
                encoding="utf-8")
