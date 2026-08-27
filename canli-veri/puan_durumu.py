"""Dort ligin puan durumunu ve takip edilen takimin haftalik skorunu ceker.

Kaynak: Turkiye Futbol Federasyonu (www.tff.org) - resmi kaynak, ucretsiz.
Ucretli spor veri servisi kullanilmaz (26 Agustos 2026 karari, URUN-PLANI.md
bolum 8).

Anasayfadaki "Bursaspor alani" bilesenini besler: solda dar sutunda dort lig
puan durumu, ustunde o haftaki Bursaspor maci.

Kullanim:
    python puan_durumu.py                    # dort ligin hepsi
    python puan_durumu.py --lig super 1lig   # yalnizca secilenler
    python puan_durumu.py --takim BURSASPOR  # takip edilen takim (varsayilan)
    python puan_durumu.py --kok D:/canli     # ciktiyi baska yere al

Cikti: <kok>/puan-durumu.json ve <kok>/durum-puan-durumu.json

Cikis kodu: 0 taze veri yazildi - 2 cekilemedi, onceki dosya korundu -
1 cekilemedi ve elde onceki veri de yok.

TFF sayfalarina dair iki olculmus tuhaflik (26 Agustos 2026):

1. Sayfalar windows-1254 dondurur ama pageID=198 (Super Lig puan cetveli)
   sayfasinda sunucu Turkce harflerin yerine U+FFFD basiyor: "GENCLERBIRLIGI"
   yerine "GEN?LERB?RL???". Kulup kimligi (kulupID) saglam geldigi icin
   adlar pageID=80'deki temiz mini tablodan kimlikle onarilir. Onarilamayan
   ad "ad_dogrulanmadi": true ile isaretlenir, uydurulmaz.

2. Super Lig'in tam tablosu yalnizca pageID=198'de; pageID=80'deki tablo
   uc sutunlu (takim, O, P) ozet tablodur. Diger uc lig kendi sayfasinda
   tam tabloyu verir.
"""

from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ortak  # noqa: E402

BILESEN = "puan-durumu"
TFF = "https://www.tff.org/default.aspx?pageID=%d"

# Kaynak dustugunde sayfanin ne yapacagini belirleyen esik. Puan durumu
# haftada bir degisir; yarim gunluk gecikme sorun degil, iki gunluk gecikme
# "guncel degil" uyarisi ister.
BAYAT_ESIK_DAKIKA = 2880  # 48 saat

# TFF sayfa kimlikleri. Sponsor adlari degistiginde sayfa basligindan
# okundugu icin burasi degismek zorunda kalmaz.
LIGLER = [
    {
        "anahtar": "super",
        "ad": "Süper Lig",
        # Tam tablo burada, ama adlar bozuk (bkz. modul aciklamasi).
        "cetvel": 198,
        # Temiz adlarin kimlikle alindigi sayfa.
        "ad_sayfasi": 80,
    },
    {"anahtar": "1lig", "ad": "1. Lig", "cetvel": 142, "ad_sayfasi": None},
    {"anahtar": "2lig", "ad": "2. Lig", "cetvel": 976, "ad_sayfasi": None},
    {"anahtar": "3lig", "ad": "3. Lig", "cetvel": 971, "ad_sayfasi": None},
]

SUTUNLAR = ["oynadi", "galibiyet", "beraberlik", "maglubiyet",
            "attigi", "yedigi", "averaj", "puan"]

_SATIR = re.compile(r"<tr[^>]*>(.*?)</tr>", re.S)
_HUCRE = re.compile(r"<td[^>]*>(.*?)</td>", re.S)
_KULUP = re.compile(r"kulupID=(\d+)", re.I)
_SIRA = re.compile(r"^(\d+)\.(.+)$", re.S)
_GRUP = re.compile(r'grupID=(\d+)[^>]*>\s*([^<]{1,40}?)\s*</a>', re.I)
_HAFTA_ETKIN = re.compile(r'haftaNoActive[^>]*>\s*<a[^>]*hafta=(\d+)', re.I)
_MODUL_BASLIK = re.compile(r'class="moduleTitle">([^<]{5,140})</div>')
_SEZON = re.compile(r"(\d{4}-\d{4})")
_MAC_SATIRI = re.compile(r'class="haftaninMaclariTr".*?</tr>', re.S)


# -- kucuk yardimcilar ----------------------------------------------------

def _metin(ham: str) -> str:
    ham = re.sub(r"<[^>]+>", " ", ham)
    ham = ham.replace("&nbsp;", " ").replace("&amp;", "&")
    return re.sub(r"\s+", " ", ham).strip()


def _sayi(deger: str):
    d = deger.strip().replace("+", "")
    try:
        return int(d)
    except ValueError:
        return None


def _sadelestir(ad: str) -> str:
    """Takim adini karsilastirma icin sadelestirir: BUYUK HARF, aksansiz."""
    ad = ad.replace("ı", "i").replace("I", "I").replace("İ", "I")
    ad = unicodedata.normalize("NFKD", ad)
    ad = "".join(c for c in ad if not unicodedata.combining(c))
    return re.sub(r"[^A-Za-z0-9 ]", " ", ad.upper())


def _bozuk_mu(ad: str) -> bool:
    return "\ufffd" in ad


# -- ayristirma -----------------------------------------------------------

def cetvel_ayikla(html: str) -> list[dict]:
    """standings blogundaki puan cetvelini satir satir cikarir.

    Tam tablo dokuz hucreli (takim + O G B M A Y AV P), Super Lig'in
    pageID=80'deki ozet tablosu uc hucreli (takim + O + P). Ikisi de
    kabul edilir; ozet tablodan yalnizca ad/kimlik alinir.
    """
    i = html.find('class="standings"')
    if i < 0:
        return []
    j = html.find("</table>", i)
    tablo = html[i:j + 8] if j > 0 else html[i:]

    cikti = []
    for m in _SATIR.finditer(tablo):
        hucreler = _HUCRE.findall(m.group(1))
        if len(hucreler) not in (3, 9):
            continue
        kimlik = _KULUP.search(hucreler[0])
        if not kimlik:
            continue  # baslik satiri
        ham_ad = _metin(hucreler[0])
        sira = None
        esle = _SIRA.match(ham_ad)
        if esle:
            sira = int(esle.group(1))
            ham_ad = esle.group(2).strip()

        kayit = {"sira": sira, "kulup_id": int(kimlik.group(1)), "ad": ham_ad}
        if len(hucreler) == 9:
            for alan, hucre in zip(SUTUNLAR, hucreler[1:9]):
                kayit[alan] = _sayi(_metin(hucre))
        cikti.append(kayit)

    if cikti and all(s["sira"] is None for s in cikti):
        for n, s in enumerate(cikti, 1):
            s["sira"] = n
    return cikti


def gruplari_ayikla(html: str) -> list[dict]:
    """Grup usulu liglerde "Gruplar: Beyaz | Kirmizi" baglantilarini okur.

    Grup adlari sayfadan gelir; kodda grup adi tutulmaz. Boylece sezon
    basinda grup sayisi ya da adi degistiginde betik kendini duzeltir.
    """
    gorulen: dict[int, str] = {}
    for kimlik, ad in _GRUP.findall(html):
        n = int(kimlik)
        if n not in gorulen and ad:
            gorulen[n] = ad
    cikti = []
    for kimlik, ad in sorted(gorulen.items()):
        # 3. Lig gruplarini TFF "01" "02" "03" diye yaziyor; sayfada
        # "1. Grup" okunacak. Kaynaktaki hali ad_kaynak'ta durur.
        gosterim = f"{int(ad)}. Grup" if ad.isdigit() else ad
        cikti.append({"grup_id": kimlik, "ad": gosterim, "ad_kaynak": ad})
    return cikti


def hafta_ayikla(html: str) -> int | None:
    esle = _HAFTA_ETKIN.search(html)
    return int(esle.group(1)) if esle else None


def baslik_ayikla(html: str) -> tuple[str, str]:
    """standings blogundan once gelen son modul basligini dondurur.

    "Nesine 2. Lig 2026-2027 Sezonu Puan Cetveli" -> ("Nesine 2. Lig",
    "2026-2027"). Sponsor adi buradan geldigi icin kod sabit tutmaz.
    """
    i = html.find('class="standings"')
    basliklar = _MODUL_BASLIK.findall(html[:i] if i > 0 else html)
    if not basliklar:
        return "", ""
    ham = basliklar[-1].strip()
    sezon_esle = _SEZON.search(ham)
    sezon = sezon_esle.group(1) if sezon_esle else ""
    ad = re.sub(r"\s*\d{4}-\d{4}\s*Sezonu.*$", "", ham)
    ad = re.sub(r"\s*Puan (Cetveli|Durumu)\s*$", "", ad).strip()
    return ad, sezon


def maclari_ayikla(html: str) -> list[dict]:
    """"Haftanin Maclari" blogundaki maclari cikarir.

    Oynanmamis macta skor hucresi bostur; o zaman skor None kalir ve
    "oynandi": false yazilir - sifir-sifir gibi gosterilmesin.
    """
    cikti = []
    for blok in _MAC_SATIRI.findall(html):
        hucreler = _HUCRE.findall(blok)
        if len(hucreler) < 4:
            continue
        tarih_ham = _metin(hucreler[0])
        tarih = saat = ""
        esle = re.match(r"(\d{2}\.\d{2}\.\d{4})\s*(\d{2}:\d{2})?", tarih_ham)
        if esle:
            tarih = esle.group(1)
            saat = esle.group(2) or ""

        ev_kimlik = _KULUP.search(hucreler[1])
        dep_kimlik = _KULUP.search(hucreler[3])
        skorlar = re.findall(r"<span[^>]*>([^<]*)</span>", hucreler[2])
        ev_gol = _sayi(skorlar[0]) if len(skorlar) > 0 else None
        dep_gol = _sayi(skorlar[1]) if len(skorlar) > 1 else None
        mac_kimlik = re.search(r"macId=(\d+)", hucreler[2])

        cikti.append({
            "tarih": tarih,
            "saat": saat,
            "ev": _metin(hucreler[1]),
            "ev_kulup_id": int(ev_kimlik.group(1)) if ev_kimlik else None,
            "deplasman": _metin(hucreler[3]),
            "deplasman_kulup_id": int(dep_kimlik.group(1)) if dep_kimlik else None,
            "ev_gol": ev_gol,
            "deplasman_gol": dep_gol,
            "oynandi": ev_gol is not None and dep_gol is not None,
            "mac_id": int(mac_kimlik.group(1)) if mac_kimlik else None,
        })
    return cikti


# -- ad onarimi -----------------------------------------------------------

def adlari_onar(kayitlar: list[dict], sozluk: dict[int, str]) -> int:
    """U+FFFD tasiyan adlari kulup kimliginden onarir; onarilamayani isaretler."""
    onarilan = 0
    for k in kayitlar:
        if not _bozuk_mu(k.get("ad", "")):
            continue
        temiz = sozluk.get(k.get("kulup_id"))
        if temiz and not _bozuk_mu(temiz):
            k["ad"] = temiz
            onarilan += 1
        else:
            k["ad_dogrulanmadi"] = True
    return onarilan


def maclarin_adlarini_onar(maclar: list[dict], sozluk: dict[int, str]) -> None:
    for m in maclar:
        for alan, kimlik_alani in (("ev", "ev_kulup_id"),
                                   ("deplasman", "deplasman_kulup_id")):
            if not _bozuk_mu(m.get(alan, "")):
                continue
            temiz = sozluk.get(m.get(kimlik_alani))
            if temiz and not _bozuk_mu(temiz):
                m[alan] = temiz
            else:
                m[alan + "_dogrulanmadi"] = True


# -- lig cekme ------------------------------------------------------------

def lig_cek(tanim: dict, sozluk: dict[int, str]) -> dict:
    """Bir ligi ceker. Gruplu ligde her grup icin ayri istek atilir."""
    adres = TFF % tanim["cetvel"]
    ortak.log(f"  {tanim['ad']}: {adres}")
    html = ortak.getir(adres, kodlama="cp1254")

    ad, sezon = baslik_ayikla(html)
    hafta = hafta_ayikla(html)
    gruplar_tanimi = gruplari_ayikla(html)

    lig = {
        "anahtar": tanim["anahtar"],
        "ad": ad or tanim["ad"],
        "sezon": sezon,
        "hafta": hafta,
        "sayfa": adres,
        "gruplar": [],
    }

    if not gruplar_tanimi:
        lig["gruplar"].append({
            "grup_id": None,
            "ad": None,
            "takimlar": cetvel_ayikla(html),
        })
        lig["maclar"] = maclari_ayikla(html)
        return lig

    # Gruplu lig: varsayilan sayfa gruplardan birini gosterir, hangisi
    # oldugu belli olmadigi icin her grup ayrica ve acikca istenir.
    lig["maclar"] = []
    for g in gruplar_tanimi:
        ortak.bekle()
        grup_adres = f"{adres}&grupID={g['grup_id']}"
        gh = ortak.getir(grup_adres, kodlama="cp1254")
        lig["gruplar"].append({
            "grup_id": g["grup_id"],
            "ad": g["ad"],
            "ad_kaynak": g.get("ad_kaynak"),
            "sayfa": grup_adres,
            "takimlar": cetvel_ayikla(gh),
        })
        lig["maclar"].extend(maclari_ayikla(gh))
        if lig["hafta"] is None:
            lig["hafta"] = hafta_ayikla(gh)

    for grup in lig["gruplar"]:
        adlari_onar(grup["takimlar"], sozluk)
    maclarin_adlarini_onar(lig["maclar"], sozluk)
    return lig


def sozluk_besle(sozluk: dict[int, str], kayitlar: list[dict]) -> None:
    for k in kayitlar:
        ad = k.get("ad", "")
        kimlik = k.get("kulup_id")
        if kimlik and ad and not _bozuk_mu(ad):
            sozluk.setdefault(kimlik, ad)


# -- takip edilen takim ---------------------------------------------------

def takimi_bul(ligler: list[dict], aranan: str) -> dict | None:
    """Takip edilen takimi ligler icinde arar; hangi ligde oldugu kodda yazili
    degil, her kosuda bulunur - kume dustugunde/ciktiginda betik degismesin."""
    hedef = _sadelestir(aranan)
    for lig in ligler:
        for grup in lig["gruplar"]:
            for t in grup["takimlar"]:
                if hedef in _sadelestir(t["ad"]):
                    kayit = dict(t)
                    kayit["lig"] = lig["anahtar"]
                    kayit["lig_adi"] = lig["ad"]
                    kayit["grup_id"] = grup["grup_id"]
                    kayit["grup_adi"] = grup["ad"]
                    kayit["hafta"] = lig["hafta"]
                    kayit["mac"] = _macini_bul(lig.get("maclar", []),
                                               t["kulup_id"])
                    return kayit
    return None


def _macini_bul(maclar: list[dict], kulup_id: int) -> dict | None:
    for m in maclar:
        if kulup_id in (m.get("ev_kulup_id"), m.get("deplasman_kulup_id")):
            return m
    return None


# -- tutarlilik -----------------------------------------------------------

def tutarlilik_denetle(ligler: list[dict]) -> dict:
    """Cekilen tablonun kendi icinde tutarli olup olmadigini olcer.

    Iki esitlik her zaman gecerlidir: oynanan = galibiyet + beraberlik +
    maglubiyet, ve averaj = attigi - yedigi. Puan denetlenmez: TFF ceza
    silmesi uygular (olculdu - Adana Demirspor 2026-2027 sezonuna -24 ile
    basladi), yani puan = 3G + B esitligi dogru degildir.

    Ayristirma kaymasi en once bu iki esitlikte kendini gosterir; sonuc
    ciktiya yazilir ki bozuk tablo sessizce yayina gitmesin.
    """
    takim = tutarsiz = adsiz = 0
    ornekler = []
    for lig in ligler:
        for grup in lig["gruplar"]:
            for t in grup["takimlar"]:
                takim += 1
                if t.get("ad_dogrulanmadi"):
                    adsiz += 1
                if t.get("oynadi") is None:
                    continue
                mac = (t["galibiyet"] or 0) + (t["beraberlik"] or 0) \
                    + (t["maglubiyet"] or 0)
                if t["oynadi"] != mac or \
                        t["averaj"] != (t["attigi"] or 0) - (t["yedigi"] or 0):
                    tutarsiz += 1
                    if len(ornekler) < 5:
                        ornekler.append(f"{lig['anahtar']}/{t['ad']}")
    return {
        "takim": takim,
        "tutarsiz_satir": tutarsiz,
        "adi_dogrulanmayan": adsiz,
        "ornekler": ornekler,
    }


# -- akis -----------------------------------------------------------------

def calistir(kok: Path, secilen: list[str], takim: str) -> int:
    cikti = kok / f"{BILESEN}.json"
    tanimlar = [l for l in LIGLER if not secilen or l["anahtar"] in secilen]

    sozluk: dict[int, str] = {}
    ligler = []
    try:
        # Once ad sayfalari: Super Lig'in temiz adlari buradan gelir ve
        # bozuk gelen tam tabloyu kimlikle onarir.
        for tanim in tanimlar:
            if not tanim["ad_sayfasi"]:
                continue
            adres = TFF % tanim["ad_sayfasi"]
            ortak.log(f"  {tanim['ad']} ad sayfasi: {adres}")
            sozluk_besle(sozluk, cetvel_ayikla(
                ortak.getir(adres, kodlama="cp1254")))
            ortak.bekle()

        for tanim in tanimlar:
            lig = lig_cek(tanim, sozluk)
            for grup in lig["gruplar"]:
                sozluk_besle(sozluk, grup["takimlar"])
                onarilan = adlari_onar(grup["takimlar"], sozluk)
                if onarilan:
                    ortak.log(f"    {onarilan} takim adi kimlikten onarildi")
            maclarin_adlarini_onar(lig.get("maclar", []), sozluk)
            ligler.append(lig)
            ortak.bekle()
    except ortak.CekmeHatasi as e:
        return ortak.dusme_ile_bitir(kok, BILESEN, cikti, str(e))

    bos = [l["anahtar"] for l in ligler
           if not any(g["takimlar"] for g in l["gruplar"])]
    if bos:
        return ortak.dusme_ile_bitir(
            kok, BILESEN, cikti,
            "su liglerin tablosu bos dondu: " + ", ".join(bos))

    veri = {
        "_not": ("TFF'nin acik sayfalarindan cekildi. Yayinlanirken kaynak "
                 "belirtilir. Takim adlari kaynaktan alinir, duzeltilmez; "
                 "yalnizca sunucunun bozuk dondurdugu harfler kulup "
                 "kimliginden onarilir."),
        "guncelleme": ortak.simdi(),
        "bayat_esik_dakika": BAYAT_ESIK_DAKIKA,
        "kaynak": {
            "ad": "Türkiye Futbol Federasyonu",
            "kisa": "TFF",
            "adres": "https://www.tff.org/",
            "kosullar": "https://www.tff.org/Default.aspx?pageID=179",
        },
        "ligler": ligler,
        "denetim": tutarlilik_denetle(ligler),
    }

    d = veri["denetim"]
    ortak.log(f"Denetim: {d['takim']} takim, tutarsiz satir "
              f"{d['tutarsiz_satir']}, adi dogrulanmayan "
              f"{d['adi_dogrulanmayan']}")
    if d["tutarsiz_satir"]:
        ortak.log("UYARI: tutarsiz satirlar var -> " + ", ".join(d["ornekler"]))

    takip = takimi_bul(ligler, takim)
    if takip:
        veri["takip"] = takip
        skor = takip.get("mac")
        nerede = f"{takip['lig_adi']} {takip['sira']}. sira, {takip['puan']} puan"
        if skor and skor["oynandi"]:
            nerede += (f" | {skor['ev']} {skor['ev_gol']}-"
                       f"{skor['deplasman_gol']} {skor['deplasman']}")
        elif skor:
            nerede += f" | {skor['tarih']} {skor['saat']} {skor['ev']} - {skor['deplasman']}"
        ortak.log(f"{takim}: {nerede}")
    else:
        veri["takip"] = None
        ortak.log(f"UYARI: {takim} hicbir ligin tablosunda bulunamadi.")

    ortak.json_yaz(cikti, veri)
    ortak.durum_yaz(kok, BILESEN, "taze")

    toplam = sum(len(g["takimlar"]) for l in ligler for g in l["gruplar"])
    ortak.log(f"Bitti: {len(ligler)} lig, "
              f"{sum(len(l['gruplar']) for l in ligler)} grup, "
              f"{toplam} takim -> {cikti}")
    return 0


def main() -> int:
    ayristi = argparse.ArgumentParser(
        description="Dort ligin puan durumunu TFF'den ceker.")
    ayristi.add_argument("--lig", nargs="*", default=[],
                         choices=[l["anahtar"] for l in LIGLER],
                         help="yalnizca bu ligler (varsayilan: hepsi)")
    ayristi.add_argument("--takim", default="BURSASPOR",
                         help="haftalik skoru ayrica cikarilacak takim")
    ayristi.add_argument("--kok", default=None,
                         help="cikti koku (ortam degiskeni: BH_CANLI_KOK)")
    arg = ayristi.parse_args()

    kok = ortak.kok_coz(arg.kok)
    ortak.log_kur(kok, BILESEN)
    ortak.log(f"Puan durumu cekiliyor -> {kok}")
    return calistir(kok, arg.lig, arg.takim)


if __name__ == "__main__":
    raise SystemExit(main())
