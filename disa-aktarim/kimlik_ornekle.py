"""Sitemap disi eski haberlerden yillara dagitilmis ornek ceker.

Sitemap yalnizca 2021-02'den bugune ilan ediyor; site ise ~24.375 kimliginden
(2012) itibaren haber sunmaya devam ediyor. Bu betik o araliktan **yil yil
ornek** cekerek tam taramanin ne getirecegini olcer.

Nasil calisir:
  1. Aralik boyunca seyrek yoklama yapip kimlik -> tarih egrisini cikarir.
  2. Egriyi araya deger koyarak her yilin kimlik bandini bulur.
  3. Her bandan rastgele `--adet` kimlik secip ceker.

Cekilen kayitlar **asil arsive** yazilir (`veri/<YIL-AY>/<id>.json`); veri
gercek, atilacak bir sey degil. Adres olarak sayfanin kanonik adresi kullanilir
-- kimlikle istenen `/gundem/x-<id>` adresi 301 ile ona gidiyor.

Gorseller bu donemde sunucudan silinmis (tarihsiz /static/ duzeni), o yuzden
`gorsel_denenmeli_mi` hepsini eliyor ve bos istek atilmiyor.
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import random
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import site_arsivleyici as sa  # noqa: E402

EN_KUCUK_KIMLIK = 24375     # olculdu: altinda kalan kimlikler 404
EN_BUYUK_KIMLIK = 512167    # bunun ustu zaten sitemap'ten alindi
_KANONIK = re.compile(r'<link[^>]+rel="canonical"[^>]+href="([^"]+)"')


def sonda_url(id_: int) -> str:
    """Kimlikle cozulen gecici adres; site 301 ile kanonige goturur."""
    return f"https://www.bursahakimiyet.com.tr/gundem/x-{id_}"


def _tarih_oku(id_: int) -> tuple[int, str] | None:
    html = sa.sayfa_indir(sonda_url(id_))
    if not html:
        return None
    veri = sa.haberi_ayikla(html, sonda_url(id_))
    tarih = (veri.get("yayin_tarihi") or "")[:7]
    return (id_, tarih) if re.match(r"^\d{4}-\d{2}$", tarih) else None


def egri_cikar(nokta: int, esz: int) -> list[tuple[int, str]]:
    """Aralik boyunca esit araliklarla yoklayip (kimlik, YYYY-AA) listesi kurar."""
    adim = (EN_BUYUK_KIMLIK - EN_KUCUK_KIMLIK) // (nokta - 1)
    adaylar = [EN_KUCUK_KIMLIK + i * adim for i in range(nokta)]
    egri = []
    with ThreadPoolExecutor(max_workers=esz) as havuz:
        for sonuc in havuz.map(_tarih_oku, adaylar):
            if sonuc:
                egri.append(sonuc)
    egri.sort()
    return egri


def yil_bandlari(egri: list[tuple[int, str]], yillar: list[int]) -> dict[int, tuple[int, int]]:
    """Her yil icin (alt kimlik, ust kimlik) tahmini -- egriden dogrusal ara deger."""
    def kimlik_tahmin(hedef: str) -> int:
        onceki = None
        for id_, ay in egri:
            if ay >= hedef:
                if onceki is None:
                    return id_
                # iki yoklama arasinda dogrusal say: ay farkina gore bol
                onceki_id, onceki_ay = onceki
                a1 = int(onceki_ay[:4]) * 12 + int(onceki_ay[5:7])
                a2 = int(ay[:4]) * 12 + int(ay[5:7])
                ah = int(hedef[:4]) * 12 + int(hedef[5:7])
                if a2 == a1:
                    return id_
                oran = (ah - a1) / (a2 - a1)
                return int(onceki_id + oran * (id_ - onceki_id))
            onceki = (id_, ay)
        return EN_BUYUK_KIMLIK

    bandlar = {}
    for yil in yillar:
        alt = max(EN_KUCUK_KIMLIK, kimlik_tahmin(f"{yil}-01"))
        ust = min(EN_BUYUK_KIMLIK, kimlik_tahmin(f"{yil + 1}-01"))
        if ust - alt > 20:
            bandlar[yil] = (alt, ust)
    return bandlar


def kaydet(id_: int) -> tuple[str, str]:
    """Tek kimligi ceker, kanonik adresle asil arsive yazar. (sonuc, ay) doner."""
    html = sa.sayfa_indir(sonda_url(id_))
    if not html:
        return "sayfa alinamadi", ""
    esle = _KANONIK.search(html)
    url = esle.group(1) if esle else sonda_url(id_)
    veri = sa.haberi_ayikla(html, url)
    ay = (veri.get("yayin_tarihi") or "")[:7]
    if not re.match(r"^\d{4}-\d{2}$", ay):
        return "tarih okunamadi", ""

    gercek_id, _ = sa.id_kategori_cikar(url)
    if gercek_id is None:
        gercek_id = id_
    if sa.zaten_islendi_mi(ay, gercek_id):
        return "zaten vardi", ay

    klasor = sa.GORSEL_KOK / ay
    yerel = []
    for g_url in filter(None, [veri["gorsel_url"], *veri["ek_gorseller"]]):
        if sa.gorsel_denenmeli_mi(g_url):
            inen = sa.gorsel_indir(g_url, klasor)
            if inen:
                yerel.append(inen)
    veri["yerel_gorseller"] = yerel

    veri_klasor = sa.VERI_KOK / ay
    veri_klasor.mkdir(parents=True, exist_ok=True)
    hedef = veri_klasor / f"{gercek_id}.json"
    gecici = hedef.with_suffix(".tmp")
    gecici.write_text(json.dumps(veri, ensure_ascii=False, indent=2), encoding="utf-8")
    gecici.replace(hedef)
    return "alindi", ay


def calistir(adet: int, yillar: list[int], esz: int, nokta: int, tohum: int) -> None:
    print(f"Kimlik -> tarih egrisi cikariliyor ({nokta} yoklama)...")
    egri = egri_cikar(nokta, esz)
    print(f"  {len(egri)} gecerli yoklama: {egri[0][1]} ({egri[0][0]}) .. {egri[-1][1]} ({egri[-1][0]})")

    bandlar = yil_bandlari(egri, yillar)
    print("\nYil bandlari (tahmin):")
    for yil, (alt, ust) in bandlar.items():
        print(f"  {yil}: {alt:>7} - {ust:>7}  ({ust - alt:,} kimlik)")

    random.seed(tohum)
    secilen: list[tuple[int, int]] = []
    for yil, (alt, ust) in bandlar.items():
        havuz = range(alt, ust)
        secilen += [(yil, i) for i in random.sample(list(havuz), min(adet, len(havuz)))]
    print(f"\nToplam {len(secilen)} kimlik cekilecek (esz={esz}).\n")

    baslangic = time.time()
    yil_sayaci: dict[int, collections.Counter] = collections.defaultdict(collections.Counter)
    gercek_ay = collections.Counter()
    bitti = 0
    with ThreadPoolExecutor(max_workers=esz) as havuz:
        isler = {havuz.submit(kaydet, id_): (yil, id_) for yil, id_ in secilen}
        for is_ in as_completed(isler):
            yil, id_ = isler[is_]
            try:
                sonuc, ay = is_.result()
            except Exception as e:
                sonuc, ay = f"hata ({type(e).__name__})", ""
            yil_sayaci[yil][sonuc] += 1
            if ay:
                gercek_ay[ay[:4]] += 1
            bitti += 1
            if bitti % 100 == 0:
                hiz = bitti / (time.time() - baslangic)
                print(f"  [{bitti}/{len(secilen)}] {hiz:.1f} kayit/sn")

    print("\nHedeflenen yila gore sonuc:")
    for yil in sorted(yil_sayaci):
        print(f"  {yil}: {dict(yil_sayaci[yil])}")
    print("\nGercek yayin yilina gore alinanlar:")
    for yil in sorted(gercek_ay):
        print(f"  {yil}: {gercek_ay[yil]}")
    print(f"\nSure: {time.time() - baslangic:.0f} sn "
          f"({len(secilen) / max(1, time.time() - baslangic):.1f} kayit/sn)")


if __name__ == "__main__":
    ayristi = argparse.ArgumentParser(description=__doc__,
                                      formatter_class=argparse.RawDescriptionHelpFormatter)
    ayristi.add_argument("--adet", type=int, default=100, help="yil basina kac haber (varsayilan 100)")
    ayristi.add_argument("--yillar", default="2012-2021", help="ornegin 2015-2021")
    ayristi.add_argument("--esz", type=int, default=4)
    ayristi.add_argument("--nokta", type=int, default=24, help="egri icin yoklama sayisi")
    ayristi.add_argument("--tohum", type=int, default=2026)
    ayristi.add_argument("--kok", default=None)
    arg = ayristi.parse_args()

    bas, _, son = arg.yillar.partition("-")
    yillar = list(range(int(bas), int(son) + 1))

    sa.AILE = "haber"
    sa.kok_ayarla(arg.kok or os.environ.get("BH_ARSIV_KOK", sa.VARSAYILAN_KOK))
    print(f"Kok: {sa.KOK}  yillar: {yillar[0]}-{yillar[-1]}  yil basina: {arg.adet}")
    try:
        calistir(arg.adet, yillar, arg.esz, arg.nokta, arg.tohum)
    except KeyboardInterrupt:
        print("Kullanici durdurdu.")
