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

# Uzunluk sinirlari PANELIN sozlesmesinden gelir (`uygulama/icerik/formlar.py`
# BASLIK_SINIR / SPOT_SINIR). Sabit olarak duruyorlar ki urun tarafi degisince
# hizanin bozuldugu testle yakalansin (`icerik/tests_yz.py`). Spot ustu 300:
# panelin siniri 320, arada pay birakiliyor.
BASLIK_SINIR = 60
SPOT_ALT = 160
SPOT_UST = 300

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
        elif len(s["metin"]) > BASLIK_SINIR:
            b.append("ALAN baslik[%d] %d karakter (sinir %d)"
                     % (i, len(s["metin"]), BASLIK_SINIR))
    if not SPOT_ALT <= len(t["spot"]) <= SPOT_UST:
        b.append("ALAN spot %d karakter (%d-%d)"
                 % (len(t["spot"]), SPOT_ALT, SPOT_UST))
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

        # K2 — uydurma olgu: kaynakta olmayan sayi, tarih, yuzde, ozel ad
        b += [olgu_bulgu_metni(x) for x in olgu_bulgulari(paket)]

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


# ---------------------------------------------------------------------------
# K2 -- uydurma olgu (19 Ekim 2026, Paket M)
# ---------------------------------------------------------------------------
#
# Taslaktaki her SAYI, TARIH (saat dahil), YUZDE ve OZEL AD (buyuk harfle baslayan cok
# sozcuklu obek) kaynak metinde aranir; yoksa bulgu olur. Bu bir dogrulama
# DEGIL, bir isarettir: "kaynakta gecmiyor" der, "yanlis" demez. Model "dun"u
# "18 Ekim" diye yazmissa da isaret dogrudur -- olgu artik modelin hesabidir
# ve editor kaynaga bakip kapatir. Anlamsal uydurma (dogru sayilarla yanlis
# iliski, yanlis kisiye atfedilen alinti) burada yakalanmaz; o elle kalir.
#
# Yanlis pozitifi azaltan uc tolerans:
#   - sayi esdegerligi: "10 bin" = "10.000", "2,5" = "2.5", "%15" = "yuzde 15",
#     "uc" = "3" (kaynakta yaziyla yazilmis kucuk sayilar)
#   - ozel adda ek toleransi: kelime kokunun on eki kaynakta geciyorsa var
#     sayilir ("Belediyesi'nin" ~ "Belediyesi")
#   - cumle basi: cumlenin ilk kelimesi buyuk harflidir; eki kesmesiz ise
#     ("Toplantida", "Yetkililer") ya da metinde kucuk harfle de geciyorsa
#     obekten dusulur.

AYLAR = ("ocak", "şubat", "mart", "nisan", "mayıs", "haziran", "temmuz",
         "ağustos", "eylül", "ekim", "kasım", "aralık")
GUNLER = ("pazartesi", "salı", "çarşamba", "perşembe", "cuma", "cumartesi", "pazar")
SAYI_SOZ = {"bir": "1", "iki": "2", "üç": "3", "dört": "4", "beş": "5",
            "altı": "6", "yedi": "7", "sekiz": "8", "dokuz": "9", "on": "10",
            "yirmi": "20", "otuz": "30", "kırk": "40", "elli": "50", "yüz": "100"}
CARPAN = {"bin": 1000, "milyon": 10 ** 6, "milyar": 10 ** 9}
# K2'de taranan taslak alanlari. Editor notu, dogrulanacaklar listesi ve
# kaynak atfi taranmaz: onlar olgu degil, editore not.
K2_ALANLARI = ("baslik_secenekleri", "spot", "uc_madde", "govde", "gorsel_altyazi",
               "seo_baslik", "seo_aciklama")
K2_KAYNAK_ALANLARI = ("orijinal_baslik", "orijinal_spot", "orijinal_govde",
                      "kaynak_adi", "asil_kaynak", "yazar", "gorsel_alt")

_TR_KUCUK = str.maketrans("IİÇĞÖŞÜÂÎÛ", "ıiçğöşüâîû")
_HARF = "A-Za-zÇĞİÖŞÜçğıöşüÂÎÛâîû"
_SAYI = re.compile(r"(?<![\w.,])(\d{1,3}(?:\.\d{3})+|\d+(?:[.,]\d+)?)(?![\d])")
_YUZDE = re.compile(r"(?:%\s?|yüzde\s+)(\d+(?:[.,]\d+)?)", re.I)
_TARIH = re.compile(r"\b(\d{1,2})\s+(" + "|".join(AYLAR) + r")\w*(?:\s+(\d{4}))?", re.I)
_SAYISAL_TARIH = re.compile(r"\b(\d{1,2})[./](\d{1,2})[./](\d{2,4})\b")
_ISO_TARIH = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})")
_SAAT = re.compile(r"(?<![\d.,])([01]?\d|2[0-3])[.:]([0-5]\d)(?![\d])")
_KELIME_TR = re.compile(r"[" + _HARF + r"]+(?:['’][" + _HARF + r"]+)?")
_CUMLE_SONU = re.compile(r"[.!?:;\"“”«»(]\s*$")
_EKLI_SOZ = re.compile(r"(da|de|ta|te|dan|den|tan|ten|nda|nde|ndan|nden|la|le|yla|"
                       r"yle|lar|ler|ları|leri|ki|ken|ince|ınca|unca|ünce)$")


def tr_kucuk(metin: str) -> str:
    """Turkce kucuk harf: I->ı, İ->i (str.lower() 'İ'yi i + birlesen nokta yapar)."""
    return (metin or "").translate(_TR_KUCUK).lower()


def _sayi_bicim(ham: str) -> str:
    """'10.000' -> '10000', '2,5' -> '2.5', '07' -> '7', '3.0' -> '3'."""
    if re.fullmatch(r"\d{1,3}(?:\.\d{3})+", ham):
        ham = ham.replace(".", "")
    ham = ham.replace(",", ".")
    if "." in ham:
        tam, kesir = ham.split(".", 1)
        kesir = kesir.rstrip("0")
        tam = tam.lstrip("0") or "0"
        return tam + ("." + kesir if kesir else "")
    return ham.lstrip("0") or "0"


def _sayilar(metin: str) -> set[str]:
    """Metindeki sayilarin bicimlenmis degerleri; 'N bin' carpimi da eklenir."""
    kucuk = tr_kucuk(metin)
    bulunan: set[str] = set()
    for es in _SAYI.finditer(kucuk):
        deger = _sayi_bicim(es.group(1))
        bulunan.add(deger)
        sonrasi = kucuk[es.end():es.end() + 9].split()
        if sonrasi and sonrasi[0] in CARPAN:
            try:
                bulunan.add(_sayi_bicim(str(round(float(deger) * CARPAN[sonrasi[0]]))))
            except ValueError:
                pass
    for kelime in re.findall(r"\w+", kucuk):
        if kelime in SAYI_SOZ:
            bulunan.add(SAYI_SOZ[kelime])
    return bulunan


def _tarihler(metin: str) -> set[tuple[str, str]]:
    kucuk = tr_kucuk(metin)
    bulunan = {(str(int(g)), a.lower()) for g, a, _ in _TARIH.findall(kucuk)}
    for g, a, _ in _SAYISAL_TARIH.findall(kucuk):
        if 1 <= int(a) <= 12:
            bulunan.add((str(int(g)), AYLAR[int(a) - 1]))
    for _, a, g in _ISO_TARIH.findall(kucuk):
        if 1 <= int(a) <= 12:
            bulunan.add((str(int(g)), AYLAR[int(a) - 1]))
    return bulunan


def _ad_kokleri(metin: str) -> set[str]:
    """Kaynaktaki kelimelerin (kesme oncesi) tum 3+ harfli on ekleri."""
    on_ekler: set[str] = set()
    for kelime in _KELIME_TR.findall(metin or ""):
        k = tr_kucuk(re.split(r"['’]", kelime)[0])
        on_ekler.add(k)                      # "A", "CT" gibi kisa kelimeler
        for n in range(3, len(k) + 1):
            on_ekler.add(k[:n])
    return on_ekler


def _kaynakta_mi(kelime: str, on_ekler: set[str]) -> bool:
    k = tr_kucuk(re.split(r"['’]", kelime)[0])
    if len(k) <= 4:
        return k in on_ekler
    return k[:max(4, len(k) - 3)] in on_ekler


def _taslak_metinleri(t: dict) -> list[tuple[str, str]]:
    """(alan, metin) ciftleri, K2_ALANLARI sirasinda."""
    cikti: list[tuple[str, str]] = []
    for alan in K2_ALANLARI:
        deger = t.get(alan)
        if isinstance(deger, str):
            cikti.append((alan, deger))
        elif isinstance(deger, list):
            for i, oge in enumerate(deger):
                if isinstance(oge, dict):
                    oge = oge.get("metin", "")
                if isinstance(oge, str):
                    cikti.append(("%s[%d]" % (alan, i), oge))
    return [(a, m) for a, m in cikti if (m or "").strip()]


def _baglam(metin: str, bas: int, son: int) -> str:
    return ("…" if bas > 30 else "") + metin[max(0, bas - 30):son + 30].strip() + \
        ("…" if son + 30 < len(metin) else "")


def _ozel_adlar(metin: str, kucuk_kelimeler: set[str]):
    """(obek, bas, son) uclusu: iki ve daha cok buyuk harfli ardisik kelime.

    Cumlenin ilk kelimesi ad degilse obekten dusulur (bkz. ust not)."""
    kelimeler = list(_KELIME_TR.finditer(metin))
    i = 0
    while i < len(kelimeler):
        if not kelimeler[i].group()[:1].isupper():
            i += 1
            continue
        j = i
        while j + 1 < len(kelimeler) and kelimeler[j + 1].group()[:1].isupper() \
                and metin[kelimeler[j].end():kelimeler[j + 1].start()].strip() in ("", "-"):
            j += 1
        obek = kelimeler[i:j + 1]
        cumle_basi = i == 0 or _CUMLE_SONU.search(metin[:kelimeler[i].start()]) is not None
        if cumle_basi and obek:
            ilk = obek[0].group()
            ilk_k = tr_kucuk(ilk)
            if ("'" not in ilk and "’" not in ilk and _EKLI_SOZ.search(ilk_k)) \
                    or ilk_k in kucuk_kelimeler:
                obek = obek[1:]
        obek = [k for k in obek if tr_kucuk(k.group()) not in AYLAR + GUNLER]
        if len(obek) >= 2:
            yield obek, obek[0].start(), obek[-1].end()
        i = j + 1


def olgu_bulgulari(paket: dict) -> list[dict]:
    """K2: taslakta olup kaynakta olmayan sayi, tarih, yuzde ve ozel adlar.

    Her bulgu bir sozluk: {kural, tur, deger, alan, baglam}. Ayni deger bir
    kez raporlanir (ilk gectigi alanla). Kural motorunun bos iskeletinde
    taranacak metin olmadigi icin bos liste doner.
    """
    t, k = paket.get("taslak") or {}, paket.get("kaynak") or {}
    kaynak = " ".join(str(k.get(a) or "") for a in K2_KAYNAK_ALANLARI)
    kaynak_tarih = _tarihler(kaynak + " " + str(k.get("yayin_tarihi") or ""))
    # Metindeki sayilar + yayin tarihinin YILI. Yayin tarihinin gunu sayi
    # sayilmaz: taslaktaki "20" kaynagin 20 Temmuz'da yayimlanmasiyla dogrulanmaz.
    kaynak_sayi = _sayilar(kaynak)
    for yil in re.findall(r"\b(\d{4})-\d{2}-\d{2}", str(k.get("yayin_tarihi") or "")):
        kaynak_sayi.add(yil)
    on_ekler = _ad_kokleri(kaynak)
    kaynak_saat = {(str(int(h)), m) for h, m in _SAAT.findall(tr_kucuk(kaynak))}
    metinler = _taslak_metinleri(t)
    kucuk_kelimeler = {tr_kucuk(w) for _, m in metinler for w in _KELIME_TR.findall(m)
                       if w[:1].islower()}
    kucuk_kelimeler |= {tr_kucuk(w) for w in _KELIME_TR.findall(kaynak) if w[:1].islower()}

    bulgular: list[dict] = []
    gorulen: set[tuple[str, str]] = set()

    def ekle(tur, deger, alan, metin, bas, son):
        anahtar = (tur, tr_kucuk(deger))
        if anahtar in gorulen:
            return
        gorulen.add(anahtar)
        bulgular.append({"kural": "K2", "tur": tur, "deger": deger, "alan": alan,
                         "baglam": _baglam(metin, bas, son)})

    for alan, metin in metinler:
        kucuk = tr_kucuk(metin)
        kapsanan: list[tuple[int, int]] = []
        for es in _SAAT.finditer(kucuk):
            kapsanan.append(es.span())
            if (str(int(es.group(1))), es.group(2)) not in kaynak_saat:
                ekle("saat", metin[es.start():es.end()], alan, metin, *es.span())
        for es in _TARIH.finditer(kucuk):
            kapsanan.append(es.span())
            gun, ay, yil = str(int(es.group(1))), es.group(2).lower(), es.group(3)
            if (gun, ay) not in kaynak_tarih or (yil and yil not in kaynak_sayi):
                ekle("tarih", metin[es.start():es.end()], alan, metin, *es.span())
        for es in _YUZDE.finditer(kucuk):
            kapsanan.append(es.span())
            if _sayi_bicim(es.group(1)) not in kaynak_sayi:
                ekle("yuzde", metin[es.start():es.end()], alan, metin, *es.span())
        for es in _SAYI.finditer(kucuk):
            if any(b <= es.start() < s for b, s in kapsanan):
                continue
            deger = _sayi_bicim(es.group(1))
            if deger in kaynak_sayi:
                continue
            sonrasi = kucuk[es.end():es.end() + 9].split()
            if sonrasi and sonrasi[0] in CARPAN:
                try:
                    carpik = _sayi_bicim(str(round(float(deger) * CARPAN[sonrasi[0]])))
                except ValueError:
                    carpik = ""
                if carpik in kaynak_sayi:
                    continue
            ekle("sayi", es.group(1), alan, metin, *es.span())
        for obek, bas, son in _ozel_adlar(metin, kucuk_kelimeler):
            eksik = [w.group() for w in obek if not _kaynakta_mi(w.group(), on_ekler)]
            if eksik:
                ekle("ozel_ad", " ".join(w.group() for w in obek), alan, metin, bas, son)
    return bulgular


def olgu_bulgu_metni(b: dict) -> str:
    adlar = {"sayi": "sayi", "tarih": "tarih", "saat": "saat", "yuzde": "yuzde",
             "ozel_ad": "ozel ad"}
    return "K2 %s kaynakta yok: %s \"%s\"" % (b["alan"], adlar.get(b["tur"], b["tur"]), b["deger"])


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
        print("   ! kaynak eksik ayiklanmis olabilir; K1/K2 bulgulari elle dogrulanmali "
              "(eksik kaynak K2'de yanlis pozitif uretir)")
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
        print("   > K2 otomatik: sayi/tarih/yuzde/ozel ad kaynakta arandi. Anlam "
              "(kim ne dedi, hangi sayi neye ait) yine elle dogrulanir.")
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
