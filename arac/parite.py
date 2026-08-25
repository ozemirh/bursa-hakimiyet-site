"""motor.js ile kural_motoru.py ayni sonucu veriyor mu.

    python arac/parite.py                          # cikti/ icindeki tum paketler
    python arac/parite.py arac/cikti/<slug>.json   # tek paket

Iki motor elle, ayri ayri guncelleniyor ve sessizce ayrisabiliyor. `gomulu_uret.py
--kontrol` bunu goremez: o yalnizca gomulu blogun taze olup olmadigina bakar, iki
motorun ciktisini karsilastirmaz. Bu betik kaynagi ikisine de verip sonucu diffler.

Node gerekir. Yoksa test sessizce ATLANMAZ, hata verir — atlanan parite testi
yok hukmundedir.

Cikis kodu: 0 ayni, 2 sapma var, 1 calistirilamadi.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from kural_motoru import taslak_uret_kural  # noqa: E402

ARAC = Path(__file__).resolve().parent

# Uretim aninda degisen alanlar; sapma sayilmaz.
YOK_SAY = {"/uretim/zaman", "/uretim/tarih"}

SHIM = r"""
const fs = require("fs"), path = require("path");
const arac = process.env.BH_ARAC, paket = process.env.BH_PAKET;
const oku = f => JSON.parse(fs.readFileSync(path.join(arac, f), "utf-8"));
global.window = { BHVeri: {
  sozluk: oku("sozluk.json"), konular: oku("konular.json"), arsiv: oku("arsiv.json")
} };
eval(fs.readFileSync(path.join(arac, "motor.js"), "utf-8"));
const k = JSON.parse(fs.readFileSync(paket, "utf-8")).kaynak;
process.stdout.write(JSON.stringify(window.BHMotor.taslakUretKural(k)));
"""


def js_calistir(paket: Path) -> dict:
    ortam = dict(os.environ, BH_ARAC=str(ARAC), BH_PAKET=str(paket))
    try:
        s = subprocess.run(["node", "-e", SHIM], capture_output=True, env=ortam)
    except FileNotFoundError:
        raise SystemExit("node bulunamadi — parite testi calistirilamiyor.")
    if s.returncode != 0:
        raise SystemExit("motor.js calismadi:\n" + s.stderr.decode("utf-8", "replace"))
    return json.loads(s.stdout.decode("utf-8"))


def farklar(a, b, yol: str = "") -> list[str]:
    if yol in YOK_SAY:
        return []
    if type(a) is not type(b):
        return ["%s tip: py=%s js=%s" % (yol, type(a).__name__, type(b).__name__)]
    if isinstance(a, dict):
        f = []
        for anahtar in sorted(set(a) | set(b)):
            alt = "%s/%s" % (yol, anahtar)
            if anahtar not in a:
                f.append("%s yalniz js'te" % alt)
            elif anahtar not in b:
                f.append("%s yalniz py'de" % alt)
            else:
                f += farklar(a[anahtar], b[anahtar], alt)
        return f
    if isinstance(a, list):
        if len(a) != len(b):
            return ["%s uzunluk: py=%d js=%d" % (yol, len(a), len(b))]
        f = []
        for i, (x, y) in enumerate(zip(a, b)):
            f += farklar(x, y, "%s[%d]" % (yol, i))
        return f
    if a != b:
        return ["%s\n     py: %s\n     js: %s" % (yol, kirp(a), kirp(b))]
    return []


def kirp(deger, n: int = 110) -> str:
    m = repr(deger)
    return m if len(m) <= n else m[:n] + "..."


def main() -> int:
    yollar = [Path(y) for y in sys.argv[1:]] or sorted((ARAC / "cikti").glob("*.json"))
    if not yollar:
        print("Karsilastirilacak paket yok.")
        return 1

    toplam = 0
    for yol in yollar:
        paket = json.loads(yol.read_text(encoding="utf-8"))
        if "kaynak" not in paket:
            print("== %s  atlandi (kaynak yok)" % yol.name)
            continue
        f = farklar(taslak_uret_kural(paket["kaynak"]), js_calistir(yol))
        toplam += len(f)
        print("== %s  %s" % (yol.name, "ayni" if not f else "%d sapma" % len(f)))
        for satir in f:
            print("   - " + satir)

    print("\nToplam %d sapma / %d paket" % (toplam, len(yollar)))
    return 2 if toplam else 0


if __name__ == "__main__":
    raise SystemExit(main())
