"""Anahtarsiz yapay zeka yolu: taslagi yerel `claude` CLI ile uretir.

    python arac/haber_taslak.py "https://..." --saglayici cli

`--saglayici claude` API anahtari ister; bu yol istemez. Makinede kurulu ve
oturum acilmis Claude Code CLI'sini (`claude -p`) cagirir, yani kullanicinin
kendi aboneligini kullanir. Ag istegi CLI tarafindan yapilir; bu dosya yalnizca
standart kutuphane kullanir.

Editoryal yonerge tek yerden gelir: `haber_taslak.py` icindeki SISTEM. Sema da
oradan (SEMA) alinir, boylece uc saglayici ayni alan sozlesmesine yazar.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from haber_taslak import SEMA, SISTEM, sema_dogrula  # noqa: E402
from kural_motoru import sozluk_yukle, tezgah_kur  # noqa: E402

# Uzun haberlerde model birkac dakika surebiliyor.
ZAMAN_ASIMI = 420


class YzHatasi(Exception):
    """CLI yolu calismadi. Mesaji dogrudan editore gosterilir."""


def cli_var_mi() -> str:
    """Kurulu `claude` CLI'sinin yolunu doner, yoksa bos."""
    return shutil.which("claude") or ""


def _istem(kaynak: dict) -> str:
    """Modele gidecek tek parca istem: yonerge + sema + kaynak."""
    ozet = {
        "kaynak_adi": kaynak.get("kaynak_adi", ""),
        "kaynak_url": kaynak.get("kaynak_url", ""),
        "yazar": kaynak.get("yazar", ""),
        "yayin_tarihi": kaynak.get("yayin_tarihi", ""),
        "orijinal_baslik": kaynak.get("orijinal_baslik", ""),
        "orijinal_spot": kaynak.get("orijinal_spot", ""),
        "orijinal_govde": kaynak.get("orijinal_govde", ""),
    }
    return "\n\n".join([
        SISTEM,
        "SEMA (donecegin JSON tam olarak bu alanlari tasimali):",
        json.dumps(SEMA, ensure_ascii=False, indent=1),
        "KAYNAK:",
        json.dumps(ozet, ensure_ascii=False, indent=1),
        "YALNIZCA gecerli JSON don. Aciklama, selamlama, kod citi (```) yazma. "
        "Ilk karakter { olsun, son karakter } olsun.",
    ])


def _json_ayikla(cikti: str) -> dict:
    """CLI ciktisindan JSON nesnesini cikarir; kod citi ve on soz tolere edilir."""
    metin = cikti.strip()
    cit = re.search(r"```(?:json)?\s*(.+?)```", metin, re.S)
    if cit:
        metin = cit.group(1).strip()
    if not metin.startswith("{"):
        bas = metin.find("{")
        son = metin.rfind("}")
        if bas == -1 or son <= bas:
            raise YzHatasi("Model JSON dondurmedi. Ilk 200 karakter: " + cikti[:200])
        metin = metin[bas:son + 1]
    try:
        return json.loads(metin)
    except ValueError as e:
        raise YzHatasi("Modelin JSON'u cozulemedi: %s" % e) from e


def cagir(istem: str, zaman_asimi: int = ZAMAN_ASIMI) -> str:
    """Yerel `claude` komutunu calistirir, ham metin ciktisini doner.

    Duzeltme turlari da (yz_skill.py) bu kapiyi kullanir; CLI cagrisi tek yerde."""
    yol = cli_var_mi()
    if not yol:
        raise YzHatasi("`claude` komutu bulunamadi. Claude Code kurulu ve oturumu "
                       "acik olmali; ya da --saglayici kural kullanin.")
    try:
        s = subprocess.run([yol, "-p", istem, "--output-format", "text"],
                           capture_output=True, timeout=zaman_asimi)
    except subprocess.TimeoutExpired as e:
        raise YzHatasi("Model %d saniyede yanit vermedi." % zaman_asimi) from e
    except OSError as e:
        raise YzHatasi("`claude` calistirilamadi: %s" % e) from e
    if s.returncode != 0:
        hata = s.stderr.decode("utf-8", "replace").strip() or "bilinmeyen hata"
        raise YzHatasi("`claude` hata verdi: %s" % hata[:300])
    return s.stdout.decode("utf-8", "replace")


def taslak_uret_cli(kaynak: dict, zaman_asimi: int = ZAMAN_ASIMI) -> dict:
    """Kaynaktan tam taslak uretir (baslik, spot, govde dahil).

    Paket govdesini `taslak_uret_kural` ile ayni bicimde doner: {"taslak", "uretim"}.
    """
    taslak = _json_ayikla(cagir(_istem(kaynak), zaman_asimi))
    if "taslak" in taslak and isinstance(taslak["taslak"], dict):
        taslak = taslak["taslak"]          # paket dondurduyse icini al

    return {
        "taslak": taslak,
        # Tezgah kaynagin ham cumleleridir; kimin yazdigindan bagimsiz olarak
        # editorun yaninda durmali. Model yolunda da veriliyor.
        "tezgah": tezgah_kur(kaynak, sozluk_yukle()),
        "uretim": {
            "saglayici": "cli",
            "model": "claude-code-cli",
            "surum": "1.0",
            "sema_uyarilari": sema_dogrula(taslak),
        },
    }


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    paket = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    try:
        sonuc = taslak_uret_cli(paket["kaynak"])
    except YzHatasi as e:
        print("Uretilemedi: %s" % e)
        return 2
    uyari = sonuc["uretim"]["sema_uyarilari"]
    t = sonuc["taslak"]
    print("Uretildi. Sema uyarisi: %s" % ("; ".join(uyari[:5]) if uyari else "yok"))
    print("  baslik : %s" % (t.get("baslik_secenekleri") or [{}])[0].get("metin", ""))
    print("  govde  : %d blok" % len(t.get("govde") or []))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
