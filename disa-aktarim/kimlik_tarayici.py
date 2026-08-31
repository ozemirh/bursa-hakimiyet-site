"""Sitemap disi eski haberleri kimlik sayarak tarar (2012 - 2021 Mart).

Sitemap indeksi yalnizca 2021-02'den bugune ilan ediyor; oysa site
**24.375** kimliginden itibaren haber sunuyor. Panelin 1.044.757 haber
sayisi ile sitemap'in 556.824'u arasindaki fark tam olarak bu araliktir
(31 Agustos 2026'da olculdu: 100 rastgele kimligin 100'u 200 donuyor).

Adres kimlikle cozuluyor: `/gundem/x-<id>` -> 200 ve 301 ile kanonik adrese.
Kayit **kanonik adresle** yazilir, yani `veri/<YIL-AY>/<id>.json` duzeni ve
adres deseni sitemap taramasiyla birebir ayni kalir.

Kesintiye dayanikli: diskte JSON'u olan kimlik atlanir, kalici 404'ler
`kurtarilamayan-eski.txt` dosyasina yazilip bir daha denenmez.

  python disa-aktarim/kimlik_tarayici.py                # tam tarama
  python disa-aktarim/kimlik_tarayici.py --sinirla 200  # deneme
  python disa-aktarim/kimlik_tarayici.py --yeniden-dene # 404 listesini de dene

NOT: bu donemin gorselleri sunucudan silinmis (2023 Temmuz gocu), o yuzden
gorsel indirilmez -- `gorsel_denenmeli_mi` tarihsiz /static/ adreslerini
zaten eliyor. Disk maliyeti yalnizca JSON.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import site_arsivleyici as sa  # noqa: E402
from kimlik_ornekle import EN_BUYUK_KIMLIK, EN_KUCUK_KIMLIK, kaydet  # noqa: E402

OBEK = 4000  # kac kimlik birden havuza verilecek


def _dosya(ad: str) -> Path:
    return sa.KOK / ad


def log(mesaj: str) -> None:
    satir = f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {mesaj}"
    print(satir, flush=True)
    with open(_dosya("log-eski.txt"), "a", encoding="utf-8") as f:
        f.write(satir + "\n")


def olu_kimlikler() -> set[int]:
    yol = _dosya("kurtarilamayan-eski.txt")
    if not yol.exists():
        return set()
    olu = set()
    for satir in yol.read_text(encoding="utf-8").splitlines():
        parca = satir.split("\t")[0].strip()
        if parca.isdigit():
            olu.add(int(parca))
    return olu


def diskteki_kimlikler() -> set[int]:
    kimlikler: set[int] = set()
    for ay in sa.VERI_KOK.iterdir():
        if ay.is_dir():
            for g in os.scandir(ay):
                if g.name.endswith(".json") and g.name[:-5].isdigit():
                    kimlikler.add(int(g.name[:-5]))
    return kimlikler


def ilerleme_yaz(toplam: int, tamamlanan: int, atlanan: int, basarisiz: int, baslangic: float) -> None:
    _dosya("ilerleme-eski.json").write_text(json.dumps({
        "toplam_url": toplam,
        "tamamlanan": tamamlanan,
        "onceden_vardi": atlanan,
        "basarisiz": basarisiz,
        "gecen_saniye": round(time.time() - baslangic),
        "son_guncelleme": datetime.now().isoformat(timespec="seconds"),
        "kaynak": "kimlik_tarayici.py",
    }, ensure_ascii=False, indent=2), encoding="utf-8")


def calistir(alt: int, ust: int, esz: int, sinirla: int | None, yeniden_dene: bool) -> None:
    log(f"Kimlik araligi {alt:,} - {ust:,} taranacak (esz={esz}).")
    diskte = diskteki_kimlikler()
    olu = set() if yeniden_dene else olu_kimlikler()
    log(f"Diskte {len(diskte):,} kayit var; olu olarak isaretli {len(olu):,} kimlik atlanacak.")

    kalanlar = [i for i in range(alt, ust + 1) if i not in diskte and i not in olu]
    toplam = ust - alt + 1
    # "atlanan" gercekten diskte olan / olu bilinen kimliklerdir; --sinirla ile
    # kirpilan kuyrugu buraya katarsak ilerleme oldugundan buyuk gorunur.
    onceden = toplam - len(kalanlar)
    if sinirla:
        kalanlar = kalanlar[:sinirla]
    log(f"Cekilecek kimlik: {len(kalanlar):,} (atlanan {onceden:,}).")
    if not kalanlar:
        return

    baslangic = time.time()
    tamamlanan = basarisiz = 0
    bitti = 0
    olu_tampon: list[str] = []

    for bas in range(0, len(kalanlar), OBEK):
        obek = kalanlar[bas:bas + OBEK]
        with ThreadPoolExecutor(max_workers=esz) as havuz:
            isler = {havuz.submit(kaydet, i): i for i in obek}
            for is_ in as_completed(isler):
                id_ = isler[is_]
                try:
                    sonuc, _ = is_.result()
                except Exception as e:
                    sonuc = f"hata ({type(e).__name__})"
                if sonuc in ("alindi", "zaten vardi"):
                    tamamlanan += 1
                else:
                    basarisiz += 1
                    olu_tampon.append(f"{id_}\t{sonuc}")
                bitti += 1
                if bitti % 500 == 0:
                    hiz = bitti / (time.time() - baslangic)
                    kalan_sn = (len(kalanlar) - bitti) / max(hiz, 0.01)
                    log(f"[{bitti:,}/{len(kalanlar):,}] alinan={tamamlanan:,} "
                        f"olu={basarisiz:,} {hiz:.1f} kayit/sn "
                        f"kalan ~{kalan_sn / 3600:.1f} saat")
                    ilerleme_yaz(toplam, tamamlanan, onceden, basarisiz, baslangic)
                    if not sa.disk_yeterli_mi():
                        log("Disk alani yetersiz, duruluyor.")
                        return

        if olu_tampon:
            with open(_dosya("kurtarilamayan-eski.txt"), "a", encoding="utf-8") as f:
                f.write("\n".join(olu_tampon) + "\n")
            olu_tampon.clear()
        sa.baglantilari_kapat()

    ilerleme_yaz(toplam, tamamlanan, onceden, basarisiz, baslangic)
    log(f"Bitti. alinan={tamamlanan:,} olu={basarisiz:,} "
        f"sure={(time.time() - baslangic) / 3600:.1f} saat")


if __name__ == "__main__":
    ayristi = argparse.ArgumentParser(description=__doc__,
                                      formatter_class=argparse.RawDescriptionHelpFormatter)
    ayristi.add_argument("--alt", type=int, default=EN_KUCUK_KIMLIK)
    ayristi.add_argument("--ust", type=int, default=EN_BUYUK_KIMLIK)
    ayristi.add_argument("--esz", type=int, default=8)
    ayristi.add_argument("--sinirla", type=int, default=None)
    ayristi.add_argument("--yeniden-dene", action="store_true",
                         help="olu olarak isaretli kimlikleri de tekrar dener")
    ayristi.add_argument("--kok", default=None)
    arg = ayristi.parse_args()

    sa.AILE = "haber"
    sa.kok_ayarla(arg.kok or os.environ.get("BH_ARSIV_KOK", sa.VARSAYILAN_KOK))
    print(f"Kok: {sa.KOK}")
    try:
        calistir(arg.alt, arg.ust, arg.esz, arg.sinirla, arg.yeniden_dene)
    except KeyboardInterrupt:
        log("Kullanici durdurdu; tekrar calistirinca kaldigi yerden devam eder.")
