"""Skill zinciri: uret -> denetle -> duzelt. Anahtarsiz.

    python arac/haber_taslak.py "https://..." --saglayici skill

`cli` yolu tek atista taslak uretir ve orada birakir; ilk denemede kaynakla uc
ayri 8 kelimelik birebir ortusme (K1) cikti. Bu yol o boslugu kapatir:
`taslak-denetimi` skill'inin Mod 1 adimini makinelestirip modelin kendi
ciktisina uygular, bulgu varsa bulgulari modele geri verip duzelttirir ve
yeniden denetler.

Denetim `denetim.py` ile YAPILIR, kopyasi cikarilmaz: kural metni tek yerde
kalsin. Duzeltme turu sayisi sinirlidir; bitmeyen bulgu paketle birlikte
raporlanir, sessizce yutulmaz.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import denetim  # noqa: E402
import yz_cli  # noqa: E402
from haber_taslak import SEMA, SISTEM  # noqa: E402
from kural_motoru import sozluk_yukle, tezgah_kur  # noqa: E402

EN_FAZLA_TUR = 2


def bulgu_bul(paket: dict) -> list[str]:
    """Paketi `denetim.py` ile denetler. K2 (uydurma olgu) elle kalir."""
    hal = denetim.hal_bul(paket)
    return denetim.mekanik(paket["taslak"], hal) + denetim.kural_denetimi(paket, hal)


def _duzeltme_istemi(kaynak: dict, taslak: dict, bulgular: list[str]) -> str:
    return "\n\n".join([
        SISTEM,
        "Asagidaki taslagi SEN urettin ve denetimden gecmedi. Bulgular:",
        "\n".join("- " + b for b in bulgular),
        "Bulgularin anlami:\n"
        "- K1: kaynakla 8 kelime birebir ortusuyor. O cumleyi KENDI sozcuklerinle "
        "bastan yaz; olguyu koru, kalibi degistir. Alintiyi korumak istiyorsan "
        "blogun turunu `alinti` yap ve tirnak icine al.\n"
        "- K3/K4/K5/K6/K7 ve ALAN bulgulari: ilgili alani duzelt.\n"
        "Bulgusu olmayan alanlari OLDUGU GIBI birak.",
        "SEMA:",
        json.dumps(SEMA, ensure_ascii=False, indent=1),
        "KAYNAK:",
        json.dumps({k: kaynak.get(k, "") for k in
                    ("kaynak_adi", "orijinal_baslik", "orijinal_govde")},
                   ensure_ascii=False, indent=1),
        "SENIN TASLAGIN:",
        json.dumps(taslak, ensure_ascii=False, indent=1),
        "Duzeltilmis taslagin TAMAMINI yalnizca JSON olarak don. Aciklama yazma, "
        "kod citi kullanma. Ilk karakter { olsun.",
    ])


def taslak_uret_skill(kaynak: dict, en_fazla_tur: int = EN_FAZLA_TUR) -> dict:
    """Uretir, denetler, gerekiyorsa duzelttirir. Paket govdesini doner."""
    sonuc = yz_cli.taslak_uret_cli(kaynak)
    taslak = sonuc["taslak"]
    gunluk: list[dict] = []

    for tur in range(en_fazla_tur + 1):
        paket = {"kaynak": kaynak, "taslak": taslak,
                 "uretim": {"saglayici": "skill"}}
        bulgular = bulgu_bul(paket)
        gunluk.append({"tur": tur, "bulgu_sayisi": len(bulgular), "bulgular": bulgular})
        if not bulgular or tur == en_fazla_tur:
            break
        ham = yz_cli._json_ayikla(yz_cli.cagir(_duzeltme_istemi(kaynak, taslak, bulgular)))
        taslak = ham.get("taslak") if isinstance(ham.get("taslak"), dict) else ham

    return {
        "taslak": taslak,
        "tezgah": tezgah_kur(kaynak, sozluk_yukle()),
        "uretim": {
            "saglayici": "skill",
            "model": "claude-code-cli",
            "surum": "1.0",
            "turlar": gunluk,
            "kalan_bulgular": gunluk[-1]["bulgular"],
            "not": "taslak-denetimi Mod 1 zinciri uygulandi; K2 (uydurma olgu) elle kalir.",
        },
    }


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    paket = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    try:
        sonuc = taslak_uret_skill(paket["kaynak"])
    except yz_cli.YzHatasi as e:
        print("Uretilemedi: %s" % e)
        return 2
    for t in sonuc["uretim"]["turlar"]:
        print("  tur %d: %d bulgu%s" % (t["tur"], t["bulgu_sayisi"],
                                        "" if not t["bulgular"] else " -> " +
                                        "; ".join(x[:70] for x in t["bulgular"][:3])))
    kalan = sonuc["uretim"]["kalan_bulgular"]
    print("Sonuc: %s" % ("temiz" if not kalan else "%d bulgu kaldi" % len(kalan)))
    return 0 if not kalan else 2


if __name__ == "__main__":
    raise SystemExit(main())
