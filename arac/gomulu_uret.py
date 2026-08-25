"""Sozluk/konu/arsiv verisini ve motor.js'i yapay-zeka-editor.html icine gomer.

Neden var: kural motoru iki yerde calisiyor — Python (CLI) ve tarayici (demo
sayfasi). Sozluk, konu arsivi ve haber dizini tek kaynaktan gelsin, iki taraf
zamanla ayrismasin diye.

HTML sayfasi bu betige BAGLI DEGILDIR: uretilen blok dosyanin icine yazilir,
sayfa yine cift tikla, agsiz, paketsiz acilir. Betik yalnizca veri ya da motor
degistiginde elle calistirilir:

    python arac/gomulu_uret.py
    python arac/gomulu_uret.py --kontrol    # yazmaz, guncel mi diye bakar
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

KLASOR = Path(__file__).resolve().parent
KOK = KLASOR.parent
HEDEF = KOK / "yapay-zeka-editor.html"

BAS = "/* === ÜRETİLMİŞ BLOK — arac/gomulu_uret.py üretir, elle düzenlemeyin === */"
SON = "/* === ÜRETİLMİŞ BLOK SONU === */"


def blok_uret() -> str:
    sozluk = json.loads((KLASOR / "sozluk.json").read_text(encoding="utf-8"))
    konular = json.loads((KLASOR / "konular.json").read_text(encoding="utf-8"))["konular"]
    arsiv = json.loads((KLASOR / "arsiv.json").read_text(encoding="utf-8"))["haberler"]
    motor = (KLASOR / "motor.js").read_text(encoding="utf-8")

    veri = {"sozluk": sozluk, "konular": konular, "arsiv": arsiv}
    # </script> dizisi JSON icinde kalirsa sayfa erken kapanir
    veri_metni = json.dumps(veri, ensure_ascii=False, indent=1).replace("</", "<\\/")

    return "\n".join([
        BAS,
        "/* Kaynak: arac/sozluk.json · arac/konular.json · arac/arsiv.json · arac/motor.js */",
        f"window.BHVeri = {veri_metni};",
        "",
        motor.rstrip(),
        SON,
    ])


def main() -> int:
    ayrist = argparse.ArgumentParser(description=__doc__)
    ayrist.add_argument("--kontrol", action="store_true",
                        help="Yazmaz; gomulu blok guncel mi diye bakar")
    ayrist.add_argument("--hedef", default=str(HEDEF), help="Hedef HTML dosyasi")
    a = ayrist.parse_args()

    yol = Path(a.hedef)
    metin = yol.read_text(encoding="utf-8")
    bas, son = metin.find(BAS), metin.find(SON)
    if bas < 0 or son < 0:
        print(f"HATA: {yol.name} icinde blok isaretleri yok.\n"
              f"      Beklenen: {BAS}\n                {SON}", file=sys.stderr)
        return 1

    yeni_blok = blok_uret()
    eski_blok = metin[bas:son + len(SON)]

    if eski_blok == yeni_blok:
        print("Guncel — degisiklik yok.")
        return 0
    if a.kontrol:
        print("ESKI: gomulu blok kaynak dosyalarla ayrismis. "
              "`python arac/gomulu_uret.py` calistirin.", file=sys.stderr)
        return 2

    yol.write_text(metin[:bas] + yeni_blok + metin[son + len(SON):], encoding="utf-8")
    print(f"Yazildi: {yol.name} ({len(yeni_blok):,} karakter gomulu blok)".replace(",", "."))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
