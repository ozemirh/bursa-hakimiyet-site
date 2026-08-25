"""Konu takibi: yeni bir haberi mevcut dosyalarla ve arsivle eslestirir.

Model kullanmaz. Ortak ozel isim, konu anahtari, ortak etiket, kategori, ilce
ve tarih yakinligini puanlar; her puan icin editorun okuyabilecegi bir GEREKCE
uretir.

Onemli: bu modul hicbir kosulda kendiliginden baglamaz. `ilgili_bul()` yalnizca
aday listeler; baglama `konuya_bagla()` ile ve ancak acik onay uzerine yapilir.
"""

from __future__ import annotations

import html
import json
import re
from datetime import date, datetime
from pathlib import Path

from kural_motoru import (etiket_kucuk, gecer, kokle, kucuk, ozel_isimler, sadelestir,
                          slugla, sozluk_yukle)

KLASOR = Path(__file__).resolve().parent
KONULAR_YOLU = KLASOR / "konular.json"
ARSIV_YOLU = KLASOR / "arsiv.json"

GUCLU_ESIK = 60
OLASI_ESIK = 35

AYLAR = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
         "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]


def veri_yukle(konular_yolu: Path = KONULAR_YOLU,
               arsiv_yolu: Path = ARSIV_YOLU) -> tuple[list[dict], list[dict]]:
    konular = json.loads(konular_yolu.read_text(encoding="utf-8"))["konular"]
    arsiv = json.loads(arsiv_yolu.read_text(encoding="utf-8"))["haberler"]
    return konular, arsiv


# ---------------------------------------------------------------- parmak izi

def _koklu_kume(degerler, ekler) -> set[str]:
    kume = set()
    for d in degerler:
        for parca in sadelestir(str(d)).split():
            if len(parca) >= 3:
                kume.add(kokle(parca, ekler))
    return kume


_KESME_EKI = re.compile(r"['’][\wçğıöşü]{1,6}")

GENEL_ISIMLER = ["mahalle", "mahallesi", "cadde", "caddesi", "sokak", "bulvar",
                 "belediye", "belediyesi", "müdürlüğü", "valiliği", "ilçe", "köyü",
                 "semti", "bölgesi", "merkezi", "projesi", "alanı"]


def _isim_haritasi(isimler, ekler) -> dict[str, str]:
    """Ozel isim obeklerini kelime koklerine acar: "Mustafa Bozbey" hem
    "mustafa" hem "bozbey" ile eslesebilsin. Deger, gosterilecek tam obek.

    Kesme isaretli ekler once atilir; yoksa "Mahallesi'nden" icindeki "nden"
    parcasi bagimsiz bir isim gibi eslesir.
    """
    harita: dict[str, str] = {}
    for isim in isimler:
        gosterim = str(isim).strip()
        if not gosterim:
            continue
        for parca in sadelestir(_KESME_EKI.sub("", gosterim)).split():
            if len(parca) >= 4:
                harita.setdefault(kokle(parca, ekler), gosterim)
    return harita


def _zayif_kokler(s: dict, ekler: list[str]) -> set[str]:
    """Ozel isim sinyali sayilmayacak kokler.

    Ilce/Bursa adlari zaten `ilce` alanindan puanlaniyor; unvanlar, durak
    kelimeler ve "mahallesi/belediyesi" gibi genel adlar tek baslarina hicbir
    dosyayi digerinden ayirmaz. Disarida birakilmazlarsa her Osmangazi haberi
    her Osmangazi haberine benzer cikar.
    """
    zayif = list(s["ilce_ipuclari"].keys()) + ["Bursa", "Bursa geneli", "Bursa dışı"]
    for ipuclari in s["ilce_ipuclari"].values():
        zayif.extend(ipuclari)
    zayif.extend(s["unvanlar"])
    zayif.extend(s["durak_kelimeler"])
    zayif.extend(GENEL_ISIMLER)
    return _koklu_kume(zayif, ekler)


def _gosterim_temizle(obek: str, s: dict) -> str:
    """Gosterilecek ozel ismi sadelestirir.

    "Başkanı Mustafa Bozbey"          -> "Mustafa Bozbey"
    "Mahallesi'nden Ovaakça Mahallesi" -> "Ovaakça Mahallesi"
    """
    atilacak = {kucuk(u) for u in s["unvanlar"]} | {kucuk(g) for g in GENEL_ISIMLER}
    parcalar = _KESME_EKI.sub("", obek).split()
    while len(parcalar) > 1 and kucuk(parcalar[0]) in atilacak:
        parcalar.pop(0)
    return " ".join(parcalar)


def parmak_izi(taslak: dict, kaynak: dict, sozluk: dict | None = None) -> dict:
    """Haberin eslestirilebilir imzasi."""
    s = sozluk or sozluk_yukle()
    ekler = s["ek_listesi"]

    baslik = kaynak.get("orijinal_baslik") or ""
    spot = kaynak.get("orijinal_spot") or ""
    govde = kaynak.get("orijinal_govde") or ""

    # Editor baslik yazdiysa onu da hesaba kat
    secili = ""
    secenekler = taslak.get("baslik_secenekleri") or []
    if secenekler:
        i = taslak.get("onerilen_baslik_indeksi", 0)
        secili = (secenekler[i] if i < len(secenekler) else secenekler[0]).get("metin", "")

    tam = f"{secili}. {baslik}. {spot} {govde}"
    isimler = ozel_isimler(f"{secili}. {baslik}. {spot}", en_uzun_obek=3)

    return {
        "isimler": _isim_haritasi([_gosterim_temizle(i, s) for i in isimler], ekler),
        "zayif_kokler": _zayif_kokler(s, ekler),
        "etiketler": _koklu_kume(taslak.get("etiketler") or [], ekler),
        "kategori": taslak.get("kategori") or "",
        "ilce": taslak.get("ilce") or "",
        "tarih": (kaynak.get("yayin_tarihi") or "")[:10] or date.today().isoformat(),
        "duz": sadelestir(tam),
        "_ekler": ekler,
    }


def _tarih_coz(metin: str) -> date | None:
    if not metin:
        return None
    m = re.match(r"(\d{4})-(\d{2})(?:-(\d{2}))?", metin)
    if not m:
        return None
    try:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3) or 1))
    except ValueError:
        return None


def _gun_farki(a: str, b: str) -> int | None:
    ta, tb = _tarih_coz(a), _tarih_coz(b)
    if not ta or not tb:
        return None
    return abs((ta - tb).days)


# ---------------------------------------------------------------- puanlama

def puanla(parmak: dict, aday: dict, tur: str) -> tuple[int, list[str]]:
    """Adayin haberle ne kadar ilgili oldugunu puanlar ve gerekce uretir."""
    ekler = parmak["_ekler"]
    ham = 0.0
    gerekceler: list[str] = []

    # 1. Ortak ozel isim (yer adlari haric — onlar `ilce` alanindan puanlaniyor)
    aday_isim_kaynagi = list(aday.get("kisiler", [])) + list(aday.get("kurumlar", []))
    if tur == "haber":
        aday_isim_kaynagi = ozel_isimler(aday.get("baslik", ""), en_uzun_obek=3)
    aday_isim_kaynagi.append(aday.get("ad", "") or aday.get("baslik", ""))
    aday_kokler = set(_isim_haritasi(aday_isim_kaynagi, ekler))

    ortak_isim: list[str] = []
    for kok, gosterim in parmak["isimler"].items():
        if kok in parmak["zayif_kokler"] or kok not in aday_kokler:
            continue
        if gosterim not in ortak_isim:
            ortak_isim.append(gosterim)
    if ortak_isim:
        ham += 5 * len(ortak_isim)
        gerekceler.append(f"{len(ortak_isim)} ortak özel isim: " + ", ".join(ortak_isim[:4]))

    # 2. Konunun anahtar kelimeleri
    if tur == "konu":
        eslesen = [a for a in aday.get("anahtarlar", []) if gecer(a, parmak["duz"])]
        if eslesen:
            ham += 4 * len(eslesen)
            gerekceler.append(f"{len(eslesen)} konu anahtarı: " + ", ".join(eslesen[:4]))

    # 3. Ortak etiket
    aday_etiket = _koklu_kume(aday.get("etiketler", []), ekler)
    ortak_etiket = parmak["etiketler"] & aday_etiket
    if ortak_etiket:
        ham += 3 * len(ortak_etiket)
        gerekceler.append(f"{len(ortak_etiket)} ortak etiket")

    # 4-5. Kategori ve ilce
    if parmak["kategori"] and parmak["kategori"] == aday.get("kategori"):
        ham += 2
        gerekceler.append(f"Aynı kategori: {parmak['kategori']}")
    if parmak["ilce"] and parmak["ilce"] == aday.get("ilce"):
        ham += 2
        gerekceler.append(f"Aynı ilçe: {parmak['ilce']}")

    # 6. Tarih yakinligi
    son_tarih = aday.get("tarih") or ""
    if tur == "konu" and aday.get("maddeler"):
        son_tarih = max(m.get("tarih", "") for m in aday["maddeler"])
    fark = _gun_farki(parmak["tarih"], son_tarih)
    if fark is not None:
        if fark <= 30:
            ham += 2
            gerekceler.append(f"Son gelişme {fark} gün önce")
        elif fark <= 90:
            ham += 1
            gerekceler.append(f"Son gelişme {fark} gün önce")

    if aday.get("durum") == "kapali":
        ham *= 0.5
        gerekceler.append("Dosya kapalı — puan yarıya indirildi")

    return min(100, round(ham * 100 / 25)), gerekceler


def ilgili_bul(parmak: dict, konular: list[dict], arsiv: list[dict],
               en_fazla: int = 5) -> list[dict]:
    """Esigi gecen adaylari skora gore siralar. Baglama YAPMAZ."""
    adaylar: list[dict] = []

    for konu in konular:
        skor, gerekceler = puanla(parmak, konu, "konu")
        if skor >= OLASI_ESIK:
            adaylar.append({
                "tur": "konu", "id": konu["id"], "ad": konu["ad"], "skor": skor,
                "guclu": skor >= GUCLU_ESIK, "gerekceler": gerekceler,
                "madde_sayisi": len(konu.get("maddeler", [])),
                "son_maddeler": konu.get("maddeler", [])[-2:],
                "hassas": konu.get("hassas", {"var_mi": False}),
            })

    for haber in arsiv:
        skor, gerekceler = puanla(parmak, haber, "haber")
        if skor >= OLASI_ESIK:
            adaylar.append({
                "tur": "haber", "id": haber["slug"], "ad": haber["baslik"], "skor": skor,
                "guclu": skor >= GUCLU_ESIK, "gerekceler": gerekceler,
                "tarih": haber.get("tarih", ""), "konu_id": haber.get("konu_id"),
            })

    adaylar.sort(key=lambda a: (-a["skor"], a["tur"] != "konu"))
    return adaylar[:en_fazla]


YER_SONU = ("mahallesi", "caddesi", "sokağı", "sokak", "bulvarı", "meydanı", "parkı",
            "çayı", "deresi", "barajı", "köyü", "ovası", "tepesi", "yolu", "kavşağı")

KURUM_SONU = ("belediyesi", "başkanlığı", "müdürlüğü", "bakanlığı", "üniversitesi",
              "hastanesi", "müdürlüğü", "genel müdürlüğü", "odası", "birliği",
              "derneği", "vakfı", "kulübü", "a.ş.", "valiliği", "kaymakamlığı")

# "Kazandırılıyor", "Tamamlandı" gibi baslik kelimeleri buyuk harfle basladigi
# icin ozel isim gibi gorunur; fiil ekiyle biten obekleri ele.
FIIL_SONU = ("ıyor", "iyor", "uyor", "üyor", "acak", "ecek", "mış", "miş", "muş", "müş",
             "ldı", "ldi", "ldu", "ldü", "tı", "ti", "du", "dü", "yor")


def _ad_turu(ad: str) -> str:
    """Ozel ismi kabaca siniflandirir.

    kisi / kurum / yer  — siniflandirilabilenler
    tekil               — tek sozcuk; kurum da takim da olabilir, kisi sayilmaz
                          ama dosya adi olabilir ("Fiorentina")
    artik               — fiil cekimi; baslik buyuk harfi yuzunden ozel isim
                          gibi gorunen sozcuk ("Kazandırılıyor"). Hicbir ise yaramaz.
    """
    k = kucuk(ad).strip()
    if k.endswith(FIIL_SONU):
        return "artik"
    if k.endswith(KURUM_SONU):
        return "kurum"
    if k.endswith(YER_SONU):
        return "yer"
    return "kisi" if len(ad.split()) >= 2 else "tekil"


def konu_onerisi(parmak: dict, taslak: dict) -> dict:
    """Hicbir aday yoksa yeni dosya icin baslangic onerisi. Editor duzenler."""
    # En belirgin ozel ismi dosya adi olarak oner: zayif kokler (ilce, unvan,
    # genel adlar) elenir, kalanin en uzunu secilir. Editor zaten duzenler.
    # Gosterim bicimi ayni olan kokler tekrar uretiyordu; benzersizlestir.
    gorunen = {g: None for k, g in parmak["isimler"].items()
               if k not in parmak["zayif_kokler"]}
    isimler = sorted(gorunen, key=lambda i: -len(i))
    turler = {i: _ad_turu(i) for i in isimler}

    # Dosya adi yer, kurum ya da kisi olabilir — hepsi iyi dosya adidir. Fiil
    # kalintisi ("Yeni Park Kazandırılıyor") ve tek basina ay adi ("Ağustos")
    # olamaz; hicbiri kalmazsa kategoriye dus.
    adaylar = [i for i in isimler if turler[i] != "artik" and i not in AYLAR]
    ad = adaylar[0] if adaylar else (taslak.get("kategori") or "Yeni dosya")

    # `kisiler` yalnizca kisi, `kurumlar` yalnizca kurum tasimali.
    kisiler = [i for i in isimler if turler[i] == "kisi"]
    kurumlar = [i for i in isimler if turler[i] == "kurum"]
    slug = re.sub(r"[^a-z0-9]+", "-",
                  kucuk(ad).translate(str.maketrans("çğıöşü", "cgiosu"))).strip("-")
    return {
        "id": slug or "yeni-dosya",
        "ad": ad,
        "slug": slug or "yeni-dosya",
        "durum": "acik",
        "kategori": taslak.get("kategori", ""),
        "ilce": taslak.get("ilce", ""),
        "anahtarlar": (taslak.get("etiketler") or [])[:5],
        "kisiler": kisiler[:3],
        "kurumlar": kurumlar[:3],
        "hassas": taslak.get("hassas_konu", {"var_mi": False, "turu": "", "uyari": ""}),
        "not": "",
        "maddeler": [],
    }


# ---------------------------------------------------------------- baglama

def konuya_bagla(konu: dict, taslak: dict, kaynak: dict, arsiv: list[dict]) -> dict:
    """Haberi konuya ekler. YALNIZCA acik onay uzerine cagrilir."""
    secenekler = taslak.get("baslik_secenekleri") or [{}]
    i = taslak.get("onerilen_baslik_indeksi", 0)
    baslik = (secenekler[i] if i < len(secenekler) else secenekler[0]).get("metin", "")
    baslik = baslik or kaynak.get("orijinal_baslik") or "(başlık yazılmadı)"

    madde = {
        "tarih": (kaynak.get("yayin_tarihi") or date.today().isoformat())[:10],
        "baslik": baslik,
        "ozet": taslak.get("spot") or "",
        # Editor slug yazmadiysa basliktan turet; yoksa haber arsive dusmez
        "haber_slug": taslak.get("url_slug") or slugla(baslik),
    }
    konu.setdefault("maddeler", []).append(madde)
    konu["maddeler"].sort(key=lambda m: m.get("tarih", ""))

    taslak["konu"] = {"id": konu["id"], "ad": konu["ad"], "slug": konu["slug"]}

    kayit = next((h for h in arsiv if h.get("slug") == madde["haber_slug"]), None)
    if kayit:
        kayit["konu_id"] = konu["id"]
    elif madde["haber_slug"]:
        arsiv.append({
            "slug": madde["haber_slug"], "baslik": baslik, "spot": madde["ozet"],
            "tarih": madde["tarih"], "kategori": taslak.get("kategori", ""),
            "ilce": taslak.get("ilce", ""), "etiketler": taslak.get("etiketler", []),
            "konu_id": konu["id"],
        })
    return madde


def veri_yaz(konular: list[dict], arsiv: list[dict],
             konular_yolu: Path = KONULAR_YOLU, arsiv_yolu: Path = ARSIV_YOLU) -> None:
    for yol, anahtar, veri in ((konular_yolu, "konular", konular), (arsiv_yolu, "haberler", arsiv)):
        mevcut = json.loads(yol.read_text(encoding="utf-8"))
        mevcut[anahtar] = veri
        yol.write_text(json.dumps(mevcut, ensure_ascii=False, indent=2), encoding="utf-8")


# ---------------------------------------------------------------- html uretimi

def tarih_yaz(tarih: str, gorunen: str = "") -> str:
    """2026-08-20 -> "20 Ağustos 2026", 2026-04 -> "Nisan 2026"."""
    if gorunen:
        return gorunen
    m = re.match(r"(\d{4})-(\d{2})(?:-(\d{2}))?$", tarih or "")
    if not m:
        return tarih
    yil, ay, gun = m.group(1), int(m.group(2)), m.group(3)
    return f"{int(gun)} {AYLAR[ay - 1]} {yil}" if gun else f"{AYLAR[ay - 1]} {yil}"


def kronoloji_html(konu: dict) -> str:
    """tasarim-3'e yapistirilmaya hazir <ol class="zaman"> blogu."""
    k = html.escape
    satirlar = ['<ol class="zaman">']
    for m in konu.get("maddeler", []):
        satirlar.append("  <li>")
        satirlar.append(f'    <time datetime="{k(m.get("tarih", ""))}">'
                        f'{k(tarih_yaz(m.get("tarih", ""), m.get("gorunen", "")))}</time>')
        satirlar.append(f'    <h3>{k(m.get("baslik", ""))}</h3>')
        if m.get("ozet"):
            satirlar.append(f'    <p>{k(m["ozet"])}</p>')
        satirlar.append("  </li>")
    satirlar.append("</ol>")
    if konu.get("not"):
        satirlar.append(f'<p class="zaman-not">{k(konu["not"])}</p>')
    return "\n".join(satirlar)
