"""Uretilen taslak paketini editoryal kurallara karsi denetler.

    python arac/denetim.py arac/cikti/<slug>.json
    python arac/denetim.py arac/cikti/*.json --kisa

Model kullanmaz, aga cikmaz; yalnizca standart kutuphane. Denetim RAPOR uretir,
dosyayi degistirmez. Kural metinleri `haber_taslak.py` icindeki SISTEM ile ayni.

Paket uc halde olabilir; betik `uretim.saglayici` ve dil alanlarina bakip ayirir:

  model      `haber_taslak.py` uretmis, tum alanlar dolu       -> tam denetim
  kural-bos  `kural_motoru.py` uretmis, dil alanlari bos       -> iskelet denetimi
  kural-dolu kural iskeleti editor tarafindan doldurulmus      -> tam denetim

Boslugu ihlal saymamak icin bu ayrim sart: kural motoru basligi, spotu ve govdeyi
KASITLI bos birakir.
"""

from __future__ import annotations

import argparse
import glob
import json
import re
import sys
import unicodedata
from pathlib import Path

DIL_ALANLARI = ("spot", "seo_baslik", "seo_aciklama", "url_slug", "gorsel_alt")

# K1 icin: bu uzunlukta birebir ortusme kopyalama sayilir
ORTUSME_KELIME = 8

HUKUM_DILI = (
    "öldürdü", "öldürmüş", "zimmetine geçirdi", "dolandırdı", "çaldı",
    "rüşvet aldı", "istismar etti", "katletti", "suçu işledi",
)
TUZAK = (
    "inanamayacaksınız", "işte o an", "bakın ne oldu", "şok etkisi",
    "olay yerinde", "herkes bunu konuşuyor", "bir tık uzağınızda",
)
YARGI_IZI = ("dava", "gözaltı", "iddianame", "tutukla", "savcı", "mahkeme", "soruşturma")


def sadelestir(metin: str) -> list[str]:
    """Karsilastirma icin kelime listesi: kucuk harf, noktalama yok.

    Iki Turkce tuzagi elenir. "İ".lower() birlesik nokta (U+0307) uretir ve `\\w`
    bunu kelime karakteri saymaz — "İtalya" iki parcaya bolunurdu. Kesme isareti
    de "Inter'den" gibi ekleri ayirir. Ikisi de kelime sayisini sisirip 8 kelimelik
    ortusme esigini yaniltiyordu.
    """
    d = unicodedata.normalize("NFKC", metin or "").lower()
    d = d.replace("'", "").replace("’", "")
    d = "".join(c for c in d if unicodedata.category(c) != "Mn")
    return re.findall(r"\w+", d, flags=re.UNICODE)


def ngram(kelimeler: list[str], n: int) -> set[tuple]:
    return {tuple(kelimeler[i:i + n]) for i in range(len(kelimeler) - n + 1)}


# Tirnakli aralik: acilis isaretinden kapanisa, kapanmadiysa metnin sonuna kadar.
TIRNAK_ARALIK = re.compile("[\u201c\"\u00ab][^\u201d\"\u00bb]*(?:[\u201d\"\u00bb]|$)", re.S)


def tirnaksiz(metin: str) -> str:
    """Tirnakli aralıklari cikarir; geriye yazarin kendi cumleleri kalir.

    Alinti muafiyeti K1'de ARALIK duzeyinde olmali, blok duzeyinde degil. Turkce
    haber paragrafi tipik olarak "...diyen Biba, “...”" bicimindedir: tek bir
    tirnak isareti paragrafin ortasinda acilir. Blogun tamamini muaf tutmak,
    tirnak tasiyan her kopyalanmis paragrafi denetim disi birakiyordu — tezgahin
    en yuksek puanli cumleleri de tam olarak alinti tasiyanlardir.
    """
    return TIRNAK_ARALIK.sub(" ", metin or "")


def hal_bul(paket: dict) -> str:
    saglayici = (paket.get("uretim") or {}).get("saglayici", "")
    if saglayici != "kural":
        return "model"
    t = paket["taslak"]
    dolu = any(t.get(a) for a in DIL_ALANLARI) or t["baslik_secenekleri"][0]["metin"]
    return "kural-dolu" if dolu else "kural-bos"


def govde_metni(t: dict) -> str:
    return " ".join(g["metin"] for g in t["govde"])


def mekanik(t: dict, hal: str) -> list[str]:
    """Sayilabilir alan kurallari. Kural-bos halinde dil alanlari atlanir."""
    b: list[str] = []

    if not 3 <= len(t["etiketler"]) <= 8:
        b.append("ALAN etiketler %d adet (3-8)" % len(t["etiketler"]))
    for e in t["etiketler"]:
        if e != e.lower():
            b.append("ALAN etiket buyuk harfli: %s" % e)
    if len(t["govde"]) < 5:
        b.append("ALAN govde %d blok (en az 5)" % len(t["govde"]))
    if t["govde"] and t["govde"][0]["tur"] != "paragraf":
        b.append("ALAN ilk govde blogu paragraf degil")
    if not t.get("kaynak_atfi"):
        b.append("ALAN kaynak_atfi bos")
    if not t.get("dogrulanmasi_gerekenler"):
        b.append("ALAN dogrulanmasi_gerekenler bos")
    if t["okuma_suresi_dk"] < 1:
        b.append("ALAN okuma_suresi_dk %d" % t["okuma_suresi_dk"])

    if hal == "kural-bos":
        # Iskelet dogru mu: bos birakilmasi gerekenler bos, dolmasi gerekenler dolu
        if any(s["metin"] for s in t["baslik_secenekleri"]):
            b.append("ISKELET baslik dolu ama paket kural-bos gorunuyor")
        if not all(s["gerekce"] for s in t["baslik_secenekleri"]):
            b.append("ISKELET baslik gerekceleri eksik")
        return b

    for i, s in enumerate(t["baslik_secenekleri"]):
        if not s["metin"]:
            b.append("ALAN baslik[%d] bos" % i)
        elif len(s["metin"]) > 70:
            b.append("ALAN baslik[%d] %d karakter (sinir 70)" % (i, len(s["metin"])))
    if not 160 <= len(t["spot"]) <= 260:
        b.append("ALAN spot %d karakter (160-260)" % len(t["spot"]))
    if any(not m.strip() for m in t["uc_madde"]):
        b.append("ALAN uc_madde icinde bos madde var")
    if any(not g["metin"].strip() for g in t["govde"]):
        b.append("ALAN govde icinde bos blok var")
    if len(t["seo_baslik"]) > 60:
        b.append("ALAN seo_baslik %d (sinir 60)" % len(t["seo_baslik"]))
    if len(t["seo_aciklama"]) > 155:
        b.append("ALAN seo_aciklama %d (sinir 155)" % len(t["seo_aciklama"]))
    if not re.fullmatch(r"[a-z0-9-]+", t["url_slug"] or ""):
        b.append("ALAN url_slug bicimsiz: %s" % (t["url_slug"] or "(bos)"))
    kelime = len(sadelestir(govde_metni(t)))
    if abs(t["okuma_suresi_dk"] - max(1, round(kelime / 200))) > 1:
        b.append("ALAN okuma_suresi_dk %d, govde %d kelime" % (t["okuma_suresi_dk"], kelime))
    return b


def kural_denetimi(paket: dict, hal: str) -> list[str]:
    """SISTEM'deki mutlak kurallardan mekaniklestirilebilir olanlar."""
    t, k = paket["taslak"], paket["kaynak"]
    b: list[str] = []

    if hal != "kural-bos":
        # K1 — kopyalama. Alinti bloklari muaf; paragraf icindeki tirnakli
        # aralik metinden dusulur, kalani denetlenir.
        kaynak_ng = ngram(sadelestir(k.get("orijinal_govde", "")), ORTUSME_KELIME)
        for i, g in enumerate(t["govde"]):
            if g["tur"] == "alinti":
                continue
            ortak = ngram(sadelestir(tirnaksiz(g["metin"])), ORTUSME_KELIME) & kaynak_ng
            if ortak:
                ornek = " ".join(sorted(ortak)[0])
                b.append("K1 govde[%d] kaynakla %d kelimelik birebir ortusme: \"%s...\""
                         % (i, ORTUSME_KELIME, ornek))

        # K3 — atif VAR mi. 23 Agustos 2026'da alinan kararla atif govdenin ilk
        # iki paragrafinda gecmek zorunda degil; yayinlanan sayfada ayri bir
        # kaynak bolmesinde gosteriliyor. Kural kalkmadi, yeri degisti.
        if not (t.get("kaynak_atfi") or "").strip():
            b.append("K3 kaynak_atfi bos — kaynak bolmesi kurulamaz")

        # K4 — kesin hukum dili
        govde_kucuk = govde_metni(t).lower()
        for kalip in HUKUM_DILI:
            if kalip in govde_kucuk:
                b.append("K4 kesin hukum dili: \"%s\"" % kalip)

        # K6 — tiklama tuzagi
        for i, s in enumerate(t["baslik_secenekleri"]):
            for kalip in TUZAK:
                if kalip in s["metin"].lower():
                    b.append("K6 baslik[%d] tiklama tuzagi: \"%s\"" % (i, kalip))

    # K4/K5 — hassas konu isaretlenmis mi (her halde gecerli)
    kaynak_kucuk = (k.get("orijinal_govde", "") + k.get("orijinal_baslik", "")).lower()
    yargi_var = any(iz in kaynak_kucuk for iz in YARGI_IZI)
    if (yargi_var or t["kategori"] in ("Yargı", "Asayiş")) and not t["hassas_konu"]["var_mi"]:
        b.append("K4 kaynakta yargi izi var ama hassas_konu.var_mi false")
    if t["hassas_konu"]["var_mi"] and not t["hassas_konu"]["uyari"].strip():
        b.append("K5 hassas_konu isaretli ama uyari bos")

    # K7 — zorla yerellestirme
    if not t["bursa_ilgisi"]["var_mi"] and "bursa" in govde_metni(t).lower():
        b.append("K7 bursa_ilgisi false ama govdede Bursa gecmis")

    b += konu_denetimi(paket)
    return b


def konu_denetimi(paket: dict) -> list[str]:
    """Konu onerisi tasiyan paketler. Baglama ancak acik onayla yapilir; bu
    yuzden oneri her zaman ONERI olarak kalmali, kurulmus bag gibi durmamali."""
    oneri = paket.get("konu_onerisi")
    if not oneri:
        return []

    b: list[str] = []
    # Oneri YALNIZCA aday cikmadiginda kurulur (haber_taslak.py ve yayinci.py ayni
    # yolu izler). Ikisi birden doluysa eslestirici tutarsiz demektir.
    if paket.get("konu_adaylari"):
        b.append("KONU hem aday hem yeni dosya onerisi var — eslestirici tutarsiz")
    if oneri.get("hassas", {}).get("var_mi") and not paket["taslak"]["hassas_konu"]["var_mi"]:
        b.append("KONU dosya hassas isaretli ama taslakta hassas_konu false")
    # Mahalle/kurum adlarinin kisi listesine dusmesi sik gorulen eslestirme hatasi
    kisiler = oneri.get("kisiler") or []
    yanlis = [x for x in kisiler if x.lower().endswith(("mahallesi", "belediyesi", "müdürlüğü"))]
    if yanlis:
        b.append("KONU kisiler listesinde yer/kurum adi var: %s" % ", ".join(yanlis))
    return b


def denetle(yol: Path, kisa: bool = False) -> int:
    paket = json.loads(yol.read_text(encoding="utf-8"))
    hal = hal_bul(paket)
    guven = paket["kaynak"].get("ayiklama_guveni", "?")

    bulgular = mekanik(paket["taslak"], hal) + kural_denetimi(paket, hal)

    print("== %s  [%s, ayiklama %s]" % (yol.name, hal, guven))
    if guven == "dusuk":
        print("   ! kaynak eksik ayiklanmis olabilir; K1/K2 bulgulari elle dogrulanmali")
    if hal == "kural-bos" and not paket.get("tezgah"):
        print("   ! kural paketi tezgahsiz geldi; editorun bakacagi ham malzeme yok")

    if not bulgular:
        print("   temiz")
    elif kisa:
        print("   %d bulgu" % len(bulgular))
    else:
        for x in bulgular:
            print("   - " + x)

    if hal != "kural-bos":
        print("   > K2 (uydurma olgu) elle: taslaktaki isim/rakam/tarihleri "
              "kaynak.orijinal_govde ile karsilastir")
    return len(bulgular)


def main() -> int:
    # Windows konsolu varsayilan kod sayfasinda Turkce karakterleri bozuyor
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    ayrist = argparse.ArgumentParser(description=__doc__)
    ayrist.add_argument("paketler", nargs="+", help="arac/cikti/*.json")
    ayrist.add_argument("--kisa", action="store_true", help="Bulgulari sayar, listelemez")
    a = ayrist.parse_args()

    yollar = [Path(y) for kalip in a.paketler for y in sorted(glob.glob(kalip))]
    if not yollar:
        print("Paket bulunamadi.", file=sys.stderr)
        return 1

    toplam = sum(denetle(y, a.kisa) for y in yollar)
    print("\nToplam %d bulgu / %d paket" % (toplam, len(yollar)))
    return 2 if toplam else 0


if __name__ == "__main__":
    raise SystemExit(main())
