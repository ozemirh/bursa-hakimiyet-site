"""Alan sozlesmesi altı yerde hizada mi.

    python arac/hiza.py

Bir alan alti yerde tanimli: SEMA, SISTEM, kural_motoru.py, motor.js, sayfa
(render + ORNEKLER paketleri) ve README tablosu. Biri guncellenip digeri
unutulursa sayfa sessizce bos alan gosterir; sema `additionalProperties: False`
oldugu icin de required'a girmis ama uretilmeyen alan Claude yolunda dogrudan
hataya duser — ve o hata yalniz API anahtari olan makinede gorunur.

Iki motor icin metin araması degil, CIKTI karsilastirmasi yapilir: motorlar
calistirilip urettikleri anahtarlar semayla karsilastirilir. Grep, alanin adi
yorumda gecerse yaniliyordu.

Cikis kodu: 0 hizali, 2 bosluk var, 1 calistirilamadi.
"""

from __future__ import annotations

import io
import json
import re
import sys
from pathlib import Path

ARAC = Path(__file__).resolve().parent
KOK = ARAC.parent
sys.path.insert(0, str(ARAC))

from haber_taslak import SEMA, SISTEM  # noqa: E402
from kural_motoru import taslak_uret_kural  # noqa: E402
from parite import js_calistir  # noqa: E402

SAYFA = KOK / "yapay-zeka-editor.html"
README = ARAC / "README.md"


def oku(yol: Path) -> str:
    return io.open(yol, encoding="utf-8").read()


def ornekleri_ayikla(sayfa: str) -> dict:
    """`const ORNEKLER = { ... }` blogunu JSON olarak cozer.

    Sinir bulunurken tirnak ici suslu parantezler sayilmaz; kaynak metinlerinde
    süslü parantez gecebiliyor."""
    bas = sayfa.index("const ORNEKLER = {") + len("const ORNEKLER = ")
    derinlik, i, dizede, kacis = 0, bas, False, False
    while i < len(sayfa):
        c = sayfa[i]
        if kacis:
            kacis = False
        elif c == "\\":
            kacis = True
        elif c == '"':
            dizede = not dizede
        elif not dizede:
            if c == "{":
                derinlik += 1
            elif c == "}":
                derinlik -= 1
                if derinlik == 0:
                    return json.loads(sayfa[bas:i + 1])
        i += 1
    raise SystemExit("ORNEKLER blogunun sonu bulunamadi.")


def main() -> int:
    alanlar = set(SEMA["properties"])
    gerekli = set(SEMA.get("required", []))
    sayfa, readme = oku(SAYFA), oku(README)
    kaynak_paket = sorted((ARAC / "cikti").glob("*.json"))[0]
    ham = json.loads(kaynak_paket.read_text(encoding="utf-8"))["kaynak"]

    bulgular: list[str] = []

    def bildir(yer: str, eksik: set, fazla: set = frozenset()) -> None:
        if eksik:
            bulgular.append("%-18s eksik: %s" % (yer, ", ".join(sorted(eksik))))
        if fazla:
            bulgular.append("%-18s semada yok: %s" % (yer, ", ".join(sorted(fazla))))

    # 1 — SEMA kendi icinde tutarli mi
    bildir("SEMA.required", set(), gerekli - alanlar)
    if alanlar - gerekli:
        bulgular.append("%-18s required disinda: %s"
                        % ("SEMA", ", ".join(sorted(alanlar - gerekli))))

    # 2 — SISTEM alan kurallari
    bildir("SISTEM", {a for a in alanlar if a not in SISTEM})

    # 3 — kural motoru gercekten uretiyor mu
    py_taslak = set(taslak_uret_kural(ham)["taslak"])
    bildir("kural_motoru.py", alanlar - py_taslak, py_taslak - alanlar)

    # 4 — tarayici ikizi
    js_taslak = set(js_calistir(kaynak_paket)["taslak"])
    bildir("motor.js", alanlar - js_taslak, js_taslak - alanlar)

    # 5a — sayfadaki render kodu. Ters yon bakilmaz: `t.` oneki DOM cagrilarinda
    # da kullaniliyor (t.add, t.class) ve liste kullanilamayacak kadar gurultulu.
    render = set(re.findall(r"t\.([a-z_]+)", sayfa))
    bildir("sayfa render", alanlar - render)

    # 5b — gomulu ornek paketleri
    ornekler = ornekleri_ayikla(sayfa)
    for slug, paket in ornekler.items():
        bildir("ORNEK %s" % slug[:22], alanlar - set(paket.get("taslak", {})))

    # 5c — cip <-> paket simetrisi ve URL cakismasi. Adres kutusu ILK eslesen
    # ornegi yukler; iki ornek ayni kaynak_url'yi tasirsa ikincisi yalnizca
    # cipinden erisilebilir olur, sessizce.
    cipler = set(re.findall(r'data-ornek="([^"]+)"', sayfa))
    for eksik in sorted(cipler - set(ornekler)):
        bulgular.append("%-18s cipi var, paketi yok: %s" % ("ORNEKLER", eksik))
    for eksik in sorted(set(ornekler) - cipler):
        bulgular.append("%-18s paketi var, cipi yok: %s" % ("ORNEKLER", eksik))
    adresler: dict[str, list[str]] = {}
    for slug, paket in ornekler.items():
        adresler.setdefault(paket.get("kaynak", {}).get("kaynak_url", ""), []).append(slug)
    for adres, sluglar in adresler.items():
        if len(sluglar) > 1:
            bulgular.append("%-18s ayni kaynak_url: %s — adres kutusu yalniz \"%s\" yukler"
                            % ("ORNEKLER", ", ".join(sluglar), sluglar[0]))

    # 6 — README tablosu
    bildir("README", {a for a in alanlar if "`%s`" % a not in readme})

    print("Sema alan sayisi: %d" % len(alanlar))
    if not bulgular:
        print("Alti yer de hizali.")
        return 0
    for b in bulgular:
        print("  - " + b)
    print("\nToplam %d bosluk" % len(bulgular))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
