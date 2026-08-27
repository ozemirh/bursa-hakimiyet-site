"""Bursa'nin nobetci eczanelerini Bursa Eczaci Odasi'ndan ceker.

Sag raydaki uc sekmeden ucuncusunu besler (URUN-PLANI.md bolum 1, madde 12).
Ucretli servis kullanilmaz (26 Agustos 2026 karari, URUN-PLANI.md bolum 8).

Kaynak: Bursa Eczaci Odasi (www.beo.org.tr) - Turk Eczacilari Birligi
7. Bolge odasi, nobet listesinin resmi sahibi. Plan "cogu ilde API yok,
elle giris gerekebilir" diyordu (URUN-PLANI.md bolum 4, madde 4); Bursa
icin OLCUM SONUCU FARKLI: oda nobet listesini kendi sayfasinda sunucu
tarafinda basiyor, yani API olmasa da duzenli veri var. Ad, ilce, adres,
telefon, harita konumu ve nobet saatleri sayfadan aliniyor. Elle giris
yolu yine de duruyor (--kaynak elle), kaynak kalici olarak dustugunde
panel devreye girer.

robots.txt (olculdu, 27 Agustos 2026): /yonetim, /eczaci ve butun
/dosyalar/... yollari kapali; /nobetci-eczaneler acik. Betik yalnizca
acik yolu ister. Kapali /dosyalar/image/... altindaki gorseller
indirilmez - zaten gerek de yok.

Sayfanin iki kipi var:
  GET  /nobetci-eczaneler              bugun, il genelinde butun nobetciler
  POST /nobetci-eczaneler  tarih1+ilce belirli gun ve/veya ilce

Kullanim:
    python nobetci_eczane.py                       # bugun, il geneli
    python nobetci_eczane.py --ilce İNEGÖL
    python nobetci_eczane.py --tarih 2026-08-28
    python nobetci_eczane.py --kaynak elle

Cikti: <kok>/nobetci-eczane.json ve <kok>/durum-nobetci-eczane.json

Cikis kodu: 0 taze veri - 2 cekilemedi, onceki dosya korundu -
1 cekilemedi ve elde onceki veri de yok.

KVKK notu: cekilen alanlar eczanenin nobet gorevine ait KAMUYA ACIK
isletme bilgileridir (isletme adi, acik adres, isletme telefonu). Kisisel
veri - eczacinin adi, uyelik bilgisi - cekilmez; robots.txt'nin kapattigi
/eczaci ve /yonetim yollarina hic gidilmez.
"""

from __future__ import annotations

import argparse
import html
import re
import sys
import urllib.parse
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ortak  # noqa: E402

BILESEN = "nobetci-eczane"

BEO = "https://www.beo.org.tr/nobetci-eczaneler"

# Nobet gunde bir devrediliyor (olculdu: 18:30 - ertesi gun 08:30).
# Bir gunden eski liste yanlis eczaneyi gosterir; sayfa uyarmali.
BAYAT_ESIK_DAKIKA = 1440  # 24 saat

ELLE_DOSYA = "eczane-elle.json"

_BLOK = re.compile(
    r'<div class="col-md-12 nobetci">(.*?)(?=<div class="col-md-12 nobetci">|\Z)',
    re.S)
_BASLIK = re.compile(r'<h4[^>]*>\s*<strong>(.*?)</strong>(.*?)</h4>', re.S)
_TELEFON = re.compile(r'href="tel:([^"]+)"', re.I)
_KONUM = re.compile(r'maps\?q=(-?\d+\.\d+),(-?\d+\.\d+)', re.I)
_NOBET = re.compile(r'<span class="red">(.*?)</span>', re.S)
_SAYFA_BASLIGI = re.compile(r'<h2 class="main-color[^>]*>\s*<strong>(.*?)'
                            r'</strong>', re.S)
_ILCE_SECENEK = re.compile(r'<option\s+value="(\d+)"[^>]*>\s*([^<]+?)\s*</option>')
_ARALIK = re.compile(r'(\d{2}\.\d{2}\.\d{4})\s+(\d{2}:\d{2})\s*/\s*'
                     r'(\d{2}\.\d{2}\.\d{4})\s+(\d{2}:\d{2})')


# -- kucuk yardimcilar ----------------------------------------------------

def _metin(ham: str) -> str:
    ham = re.sub(r"<br\s*/?>", " ", ham, flags=re.I)
    ham = re.sub(r"<[^>]+>", " ", ham)
    return re.sub(r"\s+", " ", html.unescape(ham)).strip()


def _iso(tarih: str) -> str:
    """'27.08.2026' -> '2026-08-27'. Cozemezse ham hali doner."""
    p = tarih.split(".")
    if len(p) != 3:
        return tarih
    try:
        return date(int(p[2]), int(p[1]), int(p[0])).isoformat()
    except ValueError:
        return tarih


def _sadelestir(ad: str) -> str:
    ad = (ad.replace("İ", "I").replace("ı", "i").replace("Ş", "S")
            .replace("Ğ", "G").replace("Ü", "U").replace("Ö", "O")
            .replace("Ç", "C"))
    return re.sub(r"[^A-Za-z0-9]", "", ad.upper())


# -- ayristirma -----------------------------------------------------------

def ilceleri_ayikla(sayfa: str) -> list[dict]:
    """Nobet formundaki ilce listesini okur (kodda ilce listesi tutulmaz)."""
    gorulen: dict[str, str] = {}
    for kimlik, ad in _ILCE_SECENEK.findall(sayfa):
        gorulen.setdefault(kimlik, ad.strip())
    return [{"kimlik": k, "ad": a} for k, a in gorulen.items()]


def eczaneleri_ayikla(sayfa: str) -> list[dict]:
    """Nobetci eczane bloklarini tek tek kayda cevirir.

    Adres kaynakta iki parca gelebiliyor (ana adres + parantezli tarif);
    araya <br> girdigi icin etiketler bosluga cevrilip birlestiriliyor.
    Telefonu ya da konumu olmayan eczane bos alanla gecer - uydurulmaz.
    """
    cikti = []
    for blok in _BLOK.findall(sayfa):
        baslik = _BASLIK.search(blok)
        if not baslik:
            continue
        ad = _metin(baslik.group(1))
        ilce = _metin(baslik.group(2)).lstrip("-").strip()
        if not ad:
            continue

        # Govde: baslikla nobet saati arasindaki her sey adres/telefon.
        # Adres, telefon simgesine kadar olan parca. Kesme noktasi bir
        # etiketin ortasina denk geldigi icin yarim kalan "<i class='fa"
        # parcasi ayrica atilir; yoksa adresin sonuna yapisiyor.
        govde = blok[baslik.end():]
        adres = re.split(r"fa-phone|href=[\"']tel:", govde)[0]
        adres = re.sub(r"<[^>]*$", "", adres)
        adres = _metin(adres)

        telefon = _TELEFON.search(govde)
        konum = _KONUM.search(govde)
        nobet = _NOBET.search(govde)

        kayit = {
            "ad": ad,
            "ilce": ilce,
            "adres": adres,
            "telefon": _metin(telefon.group(1)) if telefon else "",
            "enlem": float(konum.group(1)) if konum else None,
            "boylam": float(konum.group(2)) if konum else None,
            "nobet_metni": _metin(nobet.group(1)) if nobet else "",
            "nobet_baslangic": "",
            "nobet_bitis": "",
        }
        aralik = _ARALIK.search(kayit["nobet_metni"])
        if aralik:
            kayit["nobet_baslangic"] = (f"{_iso(aralik.group(1))}"
                                        f"T{aralik.group(2)}")
            kayit["nobet_bitis"] = (f"{_iso(aralik.group(3))}"
                                    f"T{aralik.group(4)}")
        cikti.append(kayit)
    return cikti


# -- cekme ----------------------------------------------------------------

def beo_cek(tarih: str, ilce: str) -> dict:
    ortak.log(f"  {BEO}")
    sayfa = ortak.getir(BEO)
    ilceler = ilceleri_ayikla(sayfa)

    secilen = None
    if ilce:
        hedef = _sadelestir(ilce)
        for i in ilceler:
            if hedef == _sadelestir(i["ad"]) or hedef in _sadelestir(i["ad"]):
                secilen = i
                break
        if not secilen:
            raise ortak.CekmeHatasi(
                f"'{ilce}' ilcesi listede yok. Gelenler: "
                + ", ".join(i["ad"] for i in ilceler))

    if tarih or secilen:
        # Tarih ve ilce secimi yalnizca form gonderimiyle kabul ediliyor.
        alan = {
            "tarih1": tarih or date.today().isoformat(),
            "ilce": secilen["kimlik"] if secilen else "",
            "gnr": "NÖBET GÖSTER",
        }
        ortak.bekle()
        ortak.log(f"  POST {BEO}  tarih={alan['tarih1']} "
                  f"ilce={secilen['ad'] if secilen else '(il geneli)'}")
        sayfa = ortak.getir(
            BEO, veri=urllib.parse.urlencode(alan, encoding="utf-8").encode())

    baslik = _SAYFA_BASLIGI.search(sayfa)
    return {
        "sayfa_basligi": _metin(baslik.group(1)) if baslik else "",
        "ilceler": ilceler,
        "eczaneler": eczaneleri_ayikla(sayfa),
        "kaynak": {
            "ad": "Bursa Eczacı Odası",
            "kisa": "BEO",
            "adres": BEO,
            "kosullar": "https://www.beo.org.tr/robots.txt",
            "kunye": "Kaynak: Bursa Eczacı Odası.",
        },
    }


def elle_cek(kok: Path) -> dict:
    """Panelden girilen nobet listesi. Kaynak dustugunde calisan yol.

    Bicim: {"eczaneler": [{"ad": "...", "ilce": "...", "adres": "...",
                           "telefon": "...", "nobet_baslangic": "...",
                           "nobet_bitis": "..."}]}
    """
    yol = kok / ELLE_DOSYA
    d = ortak.json_oku(yol)
    if not d:
        raise ortak.CekmeHatasi(f"{yol} yok ya da okunamadi.")
    eczaneler = []
    for e in d.get("eczaneler", []):
        if not e.get("ad"):
            continue
        eczaneler.append({
            "ad": e["ad"],
            "ilce": e.get("ilce", ""),
            "adres": e.get("adres", ""),
            "telefon": e.get("telefon", ""),
            "enlem": e.get("enlem"),
            "boylam": e.get("boylam"),
            "nobet_metni": e.get("nobet_metni", ""),
            "nobet_baslangic": e.get("nobet_baslangic", ""),
            "nobet_bitis": e.get("nobet_bitis", ""),
        })
    return {
        "sayfa_basligi": d.get("baslik", ""),
        "ilceler": d.get("ilceler", []),
        "eczaneler": eczaneler,
        "kaynak": {
            "ad": "Elle giriş",
            "kisa": "panel",
            "adres": str(yol),
            "kosullar": "",
            "kunye": "",
        },
    }


# -- akis -----------------------------------------------------------------

def calistir(kok: Path, kaynak_adi: str, tarih: str, ilce: str) -> int:
    cikti = kok / f"{BILESEN}.json"
    try:
        paket = elle_cek(kok) if kaynak_adi == "elle" else beo_cek(tarih, ilce)
    except ortak.CekmeHatasi as e:
        return ortak.dusme_ile_bitir(kok, BILESEN, cikti, str(e))
    except Exception as e:
        return ortak.dusme_ile_bitir(kok, BILESEN, cikti, repr(e))

    eczaneler = paket["eczaneler"]
    if not eczaneler:
        return ortak.dusme_ile_bitir(
            kok, BILESEN, cikti,
            f"{kaynak_adi} kaynagi hic nobetci eczane dondurmedi")

    ilce_sayisi: dict[str, int] = {}
    for e in eczaneler:
        ilce_sayisi[e["ilce"] or "(belirtilmemiş)"] = \
            ilce_sayisi.get(e["ilce"] or "(belirtilmemiş)", 0) + 1

    veri = {
        "_not": ("Bursa Eczacı Odası'nın açık nöbet sayfasından çekildi. "
                 "Yayınlanırken kaynak belirtilir. Telefonu ya da harita "
                 "konumu kaynakta olmayan eczane boş alanla geçer; "
                 "uydurulmaz."),
        "guncelleme": ortak.simdi(),
        "bayat_esik_dakika": BAYAT_ESIK_DAKIKA,
        "kaynak": paket["kaynak"],
        "gun": tarih or date.today().isoformat(),
        "sayfa_basligi": paket.get("sayfa_basligi", ""),
        "ilce_suzgeci": ilce,
        "ilceler": paket.get("ilceler", []),
        "eczane_sayisi": len(eczaneler),
        "eczaneler": eczaneler,
        "denetim": {
            "eczane": len(eczaneler),
            "ilce": len(ilce_sayisi),
            "ilce_dagilimi": dict(sorted(ilce_sayisi.items())),
            "telefonsuz": sum(1 for e in eczaneler if not e["telefon"]),
            "konumsuz": sum(1 for e in eczaneler if e["enlem"] is None),
            "nobet_saati_cozulemeyen": sum(
                1 for e in eczaneler if not e["nobet_baslangic"]),
        },
    }

    ortak.json_yaz(cikti, veri)
    ortak.durum_yaz(kok, BILESEN, "taze")

    d = veri["denetim"]
    ortak.log(f"  {veri['sayfa_basligi']}")
    for e in eczaneler[:5]:
        ortak.log(f"    {e['ad']} - {e['ilce']} | {e['telefon']} | "
                  f"{e['nobet_baslangic']} → {e['nobet_bitis']}")
    if len(eczaneler) > 5:
        ortak.log(f"    ... ve {len(eczaneler) - 5} eczane daha")
    ortak.log(f"  Denetim: {d['eczane']} eczane, {d['ilce']} ilçe, "
              f"telefonsuz {d['telefonsuz']}, konumsuz {d['konumsuz']}, "
              f"nöbet saati çözülemeyen {d['nobet_saati_cozulemeyen']}")
    ortak.log(f"Bitti: {len(eczaneler)} nöbetçi eczane -> {cikti}")
    return 0


def main() -> int:
    ayristi = argparse.ArgumentParser(
        description="Bursa nöbetçi eczanelerini Bursa Eczacı Odası'ndan çeker.")
    ayristi.add_argument("--kaynak", default="beo", choices=["beo", "elle"],
                         help="veri kaynagi (varsayilan: beo)")
    ayristi.add_argument("--tarih", default="",
                         help="YYYY-AA-GG (varsayilan: bugun)")
    ayristi.add_argument("--ilce", default="",
                         help="tek ilce (varsayilan: il geneli)")
    ayristi.add_argument("--kok", default=None,
                         help="cikti koku (ortam degiskeni: BH_CANLI_KOK)")
    arg = ayristi.parse_args()

    kok = ortak.kok_coz(arg.kok)
    ortak.log_kur(kok, BILESEN)
    ortak.log(f"Nöbetçi eczaneler çekiliyor (kaynak: {arg.kaynak}) -> {kok}")
    return calistir(kok, arg.kaynak, arg.tarih, arg.ilce)


if __name__ == "__main__":
    raise SystemExit(main())
