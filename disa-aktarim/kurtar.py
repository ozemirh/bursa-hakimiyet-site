"""Taramada alinamayan sayfalari ve gorselleri sonradan kurtarir.

`site_arsivleyici.py` bir aileyi bastan sona tarar; bu betik ise **yalnizca
eksigi** hedefler. Iki kip var:

  --kip sayfa    url listesinde olup diskte JSON'u olmayan adresleri yeniden ceker
  --kip gorsel   JSON'u olan ama gorseli inmemis kayitlarda gorseli yeniden dener

NEDEN AYRI BIR BETIK (31 Agustos 2026'da olculdu). Kucuk aileler 27 Agustos'ta
tarandi, 502 geri cekilmesi ise 29 Agustos'ta eklendi; o yuzden video (930) ve
kose (193) kayitlari "HTTP 502" ile dustu. 31 Agustos'ta ayni adresler tek tek
denendiginde **hepsi 200 donuyor** -- yani kayip kalici degil, o gunku origin
dalgalanmasindan. Tum aileyi bastan taramak yerine eksik listesi cikarilip
yalnizca o adresler cekiliyor.

KURTARILAMAYAN: eski (tarihsiz) /static/ gorselleri sunucudan silinmis. Ne
imzali /cdn/ adresi, ne tarihli yola cevirme, ne de Wayback ile geliyor; canli
sitede de kirik gorunuyorlar. Onlari ancak gazetenin kendi sunucu yedegi
kurtarir.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import site_arsivleyici as sa  # noqa: E402


def diskteki_kimlikler() -> set[str]:
    """Hangi kayitlar zaten inmis: ay klasoru fark etmeksizin kimlik kumesi."""
    kimlikler: set[str] = set()
    if not sa.VERI_KOK.exists():
        return kimlikler
    for ay in sa.VERI_KOK.iterdir():
        if ay.is_dir():
            kimlikler |= {g.name[:-5] for g in os.scandir(ay) if g.name.endswith(".json")}
    return kimlikler


def eksik_kayitlar(atlanacak: set[str]) -> list[dict]:
    kimlikler = diskteki_kimlikler()
    eksik = []
    with open(sa.URL_LISTESI, "r", encoding="utf-8-sig") as f:
        for satir in f:
            kayit = json.loads(satir)
            if kayit["url"] in atlanacak:
                continue
            id_, _ = sa.id_kategori_cikar(kayit["url"])
            if id_ is None or str(id_) not in kimlikler:
                eksik.append(kayit)
    return eksik


def kalici_kayiplar_dosyasi() -> Path:
    ek = "" if sa.AILE == "haber" else f"-{sa.AILE}"
    return sa.KOK / f"kurtarilamayan{ek}.txt"


def kalici_kayiplari_oku() -> set[str]:
    yol = kalici_kayiplar_dosyasi()
    if not yol.exists():
        return set()
    return {s.split("\t")[0] for s in yol.read_text(encoding="utf-8").splitlines() if s.strip()}


def sayfalari_kurtar(esz: int, sinirla: int | None, kalicilari_atla: bool) -> None:
    atlanacak = kalici_kayiplari_oku() if kalicilari_atla else set()
    eksik = eksik_kayitlar(atlanacak)
    if sinirla:
        eksik = eksik[:sinirla]
    print(f"[{sa.AILE}] eksik adres: {len(eksik)}"
          + (f" (kalici kayip olarak isaretli {len(atlanacak)} adres atlandi)" if atlanacak else ""))
    if not eksik:
        ilerlemeyi_tazele()
        return

    alinan = kalan = 0
    kaliciya_yaz = []
    with ThreadPoolExecutor(max_workers=esz) as havuz:
        isler = {havuz.submit(sa.haberi_isle_ve_kaydet, k): k for k in eksik}
        for i, is_ in enumerate(as_completed(isler), 1):
            kayit = isler[is_]
            try:
                sonuc = is_.result()
            except Exception as e:
                sonuc = f"basarisiz ({type(e).__name__})"
            if sonuc in ("tamamlandi", "atlandi"):
                alinan += 1
            else:
                kalan += 1
                kaliciya_yaz.append(f"{kayit['url']}\t{sonuc}")
            if i % 50 == 0 or i == len(eksik):
                print(f"  [{i}/{len(eksik)}] alinan={alinan} kalan={kalan}")

    if kaliciya_yaz:
        with open(kalici_kayiplar_dosyasi(), "a", encoding="utf-8") as f:
            f.write("\n".join(kaliciya_yaz) + "\n")
    print(f"[{sa.AILE}] kurtarilan={alinan} hala alinamayan={kalan}"
          + (f" -> {kalici_kayiplar_dosyasi().name}" if kaliciya_yaz else ""))
    ilerlemeyi_tazele()


def kalici_listeyi_buda() -> None:
    """Sonradan inen adresleri kurtarilamayan listesinden cikarir."""
    yol = kalici_kayiplar_dosyasi()
    if not yol.exists():
        return
    kimlikler = diskteki_kimlikler()
    kalan = []
    for satir in yol.read_text(encoding="utf-8").splitlines():
        if not satir.strip():
            continue
        id_, _ = sa.id_kategori_cikar(satir.split("\t")[0])
        if id_ is None or str(id_) not in kimlikler:
            kalan.append(satir)
    metin = ("\n".join(sorted(set(kalan))) + "\n") if kalan else ""
    yol.write_text(metin, encoding="utf-8")


def ilerlemeyi_tazele() -> None:
    """durum.py'nin okudugu sayaci diskin gercegine gore yeniden yazar.

    Kurtarma kosusundan sonra ilerleme dosyasi eski taramanin sayilarini
    tasiyor ve tablo oldugundan kotu gorunuyor; sayim burada diskten yapilir.
    """
    if not sa.ILERLEME_DOSYA.exists():
        return
    try:
        d = json.loads(sa.ILERLEME_DOSYA.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return
    diskte = len(diskteki_kimlikler())
    kalici_listeyi_buda()
    d.update({
        "tamamlanan": 0,
        "onceden_vardi": diskte,
        "basarisiz": max(0, d.get("toplam_url", diskte) - diskte),
        "son_guncelleme": datetime.now().isoformat(timespec="seconds"),
        "kaynak": "kurtar.py",
    })
    gecici = sa.ILERLEME_DOSYA.with_suffix(".tmp")
    gecici.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    gecici.replace(sa.ILERLEME_DOSYA)
    print(f"[{sa.AILE}] ilerleme dosyasi tazelendi: diskte {diskte:,} kayit")


def _gorseli_olmayanlar() -> list[Path]:
    """yerel_gorseller'i bos olan JSON'lar. Kuyruk okumasi tam yuklemeden hizli."""
    adaylar = []
    for ay in sorted(sa.VERI_KOK.iterdir()):
        if not ay.is_dir():
            continue
        for g in os.scandir(ay):
            if not g.name.endswith(".json"):
                continue
            try:
                with open(g.path, "rb") as f:
                    f.seek(max(0, g.stat().st_size - 400))
                    if b'"yerel_gorseller": []' in f.read():
                        adaylar.append(Path(g.path))
            except OSError:
                continue
    return adaylar


def _kaydi_tamir_et(yol: Path) -> str:
    try:
        veri = json.loads(yol.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return "okunamadi"
    if veri.get("yerel_gorseller"):
        return "zaten var"
    adresler = [u for u in [veri.get("gorsel_url", ""), *veri.get("ek_gorseller", [])] if u]
    denenebilir = [u for u in adresler if sa.gorsel_denenmeli_mi(u)]
    if not denenebilir:
        return "silinmis"  # tarihsiz /static/: sunucuda yok, denemeye degmez
    klasor = sa.GORSEL_KOK / yol.parent.name
    yerel = [y for y in (sa.gorsel_indir(u, klasor) for u in denenebilir) if y]
    if not yerel:
        return "yine alinamadi"
    veri["yerel_gorseller"] = yerel
    gecici = yol.with_suffix(".tmp")
    gecici.write_text(json.dumps(veri, ensure_ascii=False, indent=2), encoding="utf-8")
    gecici.replace(yol)
    return "tamir edildi"


def gorselleri_kurtar(esz: int, sinirla: int | None) -> None:
    adaylar = _gorseli_olmayanlar()
    if sinirla:
        adaylar = adaylar[:sinirla]
    print(f"[{sa.AILE}] gorseli olmayan kayit: {len(adaylar)}")
    if not adaylar:
        return
    sayac: dict[str, int] = {}
    with ThreadPoolExecutor(max_workers=esz) as havuz:
        isler = {havuz.submit(_kaydi_tamir_et, y): y for y in adaylar}
        for i, is_ in enumerate(as_completed(isler), 1):
            try:
                sonuc = is_.result()
            except Exception as e:
                sonuc = f"hata ({type(e).__name__})"
            sayac[sonuc] = sayac.get(sonuc, 0) + 1
            if i % 2000 == 0 or i == len(adaylar):
                print(f"  [{i}/{len(adaylar)}] {sayac}")
    print(f"[{sa.AILE}] sonuc: {sayac}")


if __name__ == "__main__":
    ayristi = argparse.ArgumentParser(description=__doc__,
                                      formatter_class=argparse.RawDescriptionHelpFormatter)
    ayristi.add_argument("--aile", default="haber", choices=sorted(sa.AILELER))
    ayristi.add_argument("--kip", default="sayfa", choices=("sayfa", "gorsel"))
    ayristi.add_argument("--esz", type=int, default=6, help="es zamanli istek (varsayilan 6)")
    ayristi.add_argument("--sinirla", type=int, default=None, help="yalnizca ilk N kayit (deneme)")
    ayristi.add_argument("--kalicilari-atla", action="store_true",
                         help="onceki kurtarma kosusunda alinamayanlari tekrar denemez")
    ayristi.add_argument("--kok", default=None)
    arg = ayristi.parse_args()

    sa.AILE = arg.aile
    sa.kok_ayarla(arg.kok or os.environ.get("BH_ARSIV_KOK", sa.VARSAYILAN_KOK))
    print(f"Kok: {sa.KOK}  aile: {arg.aile}  kip: {arg.kip}")

    baslangic = time.time()
    try:
        if arg.kip == "sayfa":
            sayfalari_kurtar(arg.esz, arg.sinirla, arg.kalicilari_atla)
        else:
            gorselleri_kurtar(arg.esz, arg.sinirla)
    except KeyboardInterrupt:
        print("Kullanici durdurdu; tekrar calistirinca kalanla devam eder.")
    print(f"Sure: {time.time() - baslangic:.0f} sn")
