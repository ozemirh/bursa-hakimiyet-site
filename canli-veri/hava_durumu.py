"""Bursa icin hava durumunu Meteoroloji Genel Mudurlugu'nden ceker.

Sag raydaki uc sekmeden birincisini besler (URUN-PLANI.md bolum 1, madde 12).
Ucretli servis kullanilmaz (26 Agustos 2026 karari, URUN-PLANI.md bolum 8).

Kaynak: MGM'nin kendi sitesinin kullandigi acik uclar (servis.mgm.gov.tr).
Uc adet istek atilir:

    merkezler?il=Bursa              hangi istasyon numaralari kullanilacak
    sondurumlar?istno=...           su anki gozlem
    tahminler/gunluk?istno=...      bes gunluk tahmin
    tahminler/saatlik?istno=...     saatlik tahmin

Istasyon numaralari KODA YAZILMAZ; her kosuda il adindan cozulur. MGM
istasyon degistirdiginde betik kendini duzeltir.

Olculmus iki tuhaflik (27 Agustos 2026):

1. servis.mgm.gov.tr istek basliklarina bakiyor; Origin/Referer olarak
   www.mgm.gov.tr gonderilmezse uclar cevap vermiyor. Basliklar her
   istekte gonderilir.
2. Olcum yapilamayan alanlar 0 degil -9999 doner (deniz suyu sicakligi,
   kar yuksekligi, metar...). Bunlar None'a cevrilir; sifir gibi
   gosterilmesi hatali olurdu.

Hadise kodu -> Turkce ad esleme MGM'nin kendi betiginden alinmistir
(Scripts/ziko16_js/angularService/ililceler.js icindeki convertHadise).
Tanimadigimiz kod uydurulmaz; ham kod gosterilir.

Kullanim:
    python hava_durumu.py
    python hava_durumu.py --il Bursa --ilce Osmangazi
    python hava_durumu.py --kaynak elle

Cikti: <kok>/hava-durumu.json ve <kok>/durum-hava-durumu.json

Cikis kodu: 0 taze veri - 2 cekilemedi, onceki dosya korundu -
1 cekilemedi ve elde onceki veri de yok.

MGM Yasal Uyarisi (olculdu, 27 Agustos 2026):

    "Internet sitesinde bulunan hicbir bilgi; onceden izin alinmadan ve
     kaynak gosterilmeden ... yeniden yayimlanamaz ..."

Kaynak gosterme sarti betikte karsilanmistir (kaynak blogu + kunye).
"Onceden izin" sarti bir HUKUK TEYIDI kalemidir: TCMB ve TFF'nin ayni
bicimdeki maddeleriyle birlikte sorulmali (URUN-PLANI.md bolum 8).
MGM'den yayin izni almak tek seferlik bir yazisma isidir.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.parse
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ortak  # noqa: E402

BILESEN = "hava-durumu"

MGM = "https://servis.mgm.gov.tr/web"
# Uclar istegin nereden geldigine bakiyor; bu basliklar olmadan cevap gelmiyor.
MGM_BASLIK = {
    "Origin": "https://www.mgm.gov.tr",
    "Referer": "https://www.mgm.gov.tr/",
    "Accept": "application/json, text/plain, */*",
}

# Son durum saatlik guncellenir. Uc saatlik gecikme sonrasi "su anki hava"
# demek dogru olmaz; sayfa damgayi gostermeli.
BAYAT_ESIK_DAKIKA = 180

YOKSA = -9999  # MGM'nin "olcum yok" degeri

ELLE_DOSYA = "hava-elle.json"

# MGM'nin kendi convertHadise fonksiyonundan alindi.
HADISE = {
    "A": "Açık",
    "AB": "Az bulutlu",
    "PB": "Parçalı bulutlu",
    "CB": "Çok bulutlu",
    "HY": "Hafif yağmurlu",
    "Y": "Yağmurlu",
    "KY": "Kuvvetli yağmurlu",
    "KKY": "Karla karışık yağmurlu",
    "HKY": "Hafif kar yağışlı",
    "K": "Kar yağışlı",
    "KYK": "Yoğun kar yağışlı",
    "YKY": "Yoğun kar yağışlı",
    "HSY": "Hafif sağanak yağışlı",
    "SY": "Sağanak yağışlı",
    "KSY": "Kuvvetli sağanak yağışlı",
    "MSY": "Mevzi sağanak yağışlı",
    "DY": "Dolu",
    "GSY": "Gök gürültülü sağanak yağışlı",
    "KGY": "Kuvvetli gök gürültülü sağanak yağışlı",
    "KGSY": "Kuvvetli gök gürültülü sağanak yağışlı",
    "SIS": "Sisli",
    "PUS": "Puslu",
    "DNM": "Dumanlı",
    "KF": "Toz veya kum fırtınası",
    "R": "Rüzgârlı",
    "GKR": "Güneyli kuvvetli rüzgâr",
    "KKR": "Kuzeyli kuvvetli rüzgâr",
    "SCK": "Sıcak",
    "SGK": "Soğuk",
    "HHY": "Yağışlı",
}

YON = ["kuzey", "kuzey-kuzeydoğu", "kuzeydoğu", "doğu-kuzeydoğu",
       "doğu", "doğu-güneydoğu", "güneydoğu", "güney-güneydoğu",
       "güney", "güney-güneybatı", "güneybatı", "batı-güneybatı",
       "batı", "batı-kuzeybatı", "kuzeybatı", "kuzey-kuzeybatı"]


# -- kucuk yardimcilar ----------------------------------------------------

def _deger(kayit: dict, alan: str):
    """MGM'nin -9999 'olcum yok' degerini None'a cevirir.

    Ondalikli degerler bir haneye yuvarlanir: MGM ruzgar hizini
    0.7200000000000001 gibi kayan nokta artigiyla donduruyor, bu hem
    sayfada hem log'da anlamsiz duruyor.
    """
    d = kayit.get(alan)
    if d is None or d == YOKSA:
        return None
    if isinstance(d, float):
        return round(d, 1)
    return d


def _hadise(kod: str | None) -> dict:
    kod = (kod or "").strip()
    if not kod:
        return {"kod": "", "ad": ""}
    ad = HADISE.get(kod)
    kayit = {"kod": kod, "ad": ad or kod}
    if ad is None:
        # Sozlukte olmayan kodu uydurmayiz; sayfa ham kodu gosterir.
        kayit["ad_dogrulanmadi"] = True
    return kayit


def _yon(derece) -> str:
    if derece is None:
        return ""
    return YON[int((derece % 360) / 22.5 + 0.5) % 16]


def _yerel(damga: str | None) -> str:
    """MGM UTC damgasini (2026-08-27T06:23:00.000Z) TR saatine cevirir."""
    if not damga:
        return ""
    try:
        t = datetime.fromisoformat(damga.replace("Z", "+00:00"))
    except ValueError:
        return damga
    return t.astimezone(ortak.TR_SAAT).replace(microsecond=0).isoformat()


def _json(yol: str, **parametre):
    adres = f"{MGM}/{yol}"
    if parametre:
        adres += "?" + urllib.parse.urlencode(parametre)
    ortak.log(f"  {adres}")
    ham = ortak.getir(adres, basliklar=MGM_BASLIK)
    try:
        return json.loads(ham)
    except json.JSONDecodeError as e:
        raise ortak.CekmeHatasi(f"{adres} JSON degil: {e}")


# -- merkez cozumu --------------------------------------------------------

def merkez_coz(il: str, ilce: str) -> dict:
    """Il (ve istenirse ilce) adindan istasyon numaralarini cozer."""
    liste = _json("merkezler", il=il)
    if not liste:
        raise ortak.CekmeHatasi(f"MGM {il} icin merkez dondurmedi")
    if ilce:
        sec = [m for m in liste
               if (m.get("ilce") or "").casefold() == ilce.casefold()]
        if not sec:
            adlar = ", ".join(sorted({m.get("ilce", "") for m in liste}))
            raise ortak.CekmeHatasi(
                f"{il} icinde '{ilce}' ilcesi yok. Gelenler: {adlar}")
        liste = sec
    # oncelik alani MGM'nin il merkezi sirasi; en dusuk olan il merkezidir.
    return sorted(liste, key=lambda m: m.get("oncelik") or 99)[0]


# -- cekme parcalari ------------------------------------------------------

def son_durum_cek(istno: int) -> dict | None:
    liste = _json("sondurumlar", istno=istno)
    if not liste:
        return None
    d = liste[0]
    return {
        "olcum_zamani": _yerel(d.get("veriZamani")),
        "sicaklik": _deger(d, "sicaklik"),
        "hissedilen": _deger(d, "hissedilenSicaklik"),
        "nem": _deger(d, "nem"),
        "basinc": _deger(d, "aktuelBasinc"),
        "gorus_metre": _deger(d, "gorus"),
        "kapalilik": _deger(d, "kapalilik"),
        "ruzgar_hiz": _deger(d, "ruzgarHiz"),
        "ruzgar_yon_derece": _deger(d, "ruzgarYon"),
        "ruzgar_yon": _yon(_deger(d, "ruzgarYon")),
        "yagis_1saat": _deger(d, "yagis1Saat"),
        "yagis_24saat": _deger(d, "yagis24Saat"),
        "kar_yukseklik": _deger(d, "karYukseklik"),
        "hadise": _hadise(d.get("hadiseKodu")),
    }


def gunluk_cek(istno: int) -> list[dict]:
    """Bes gunluk tahmini gunlere ayirir.

    MGM alanlari Gun0..Gun5 diye numaralar ve Gun0 cogu zaman Gun1 ile
    ayni gundur (gunun kalani icin ayri deger). Tarihe gore tekillestirilir,
    once resmi bes gun (1..5) alinir; Gun0 ancak farkli bir gune isaret
    ediyorsa eklenir.
    """
    liste = _json("tahminler/gunluk", istno=istno)
    if not liste:
        return []
    d = liste[0]
    gunler: dict[str, dict] = {}
    for n in [1, 2, 3, 4, 5, 0]:
        tarih = _yerel(d.get(f"tarihGun{n}"))
        if not tarih or tarih[:10] in gunler:
            continue
        gunler[tarih[:10]] = {
            "tarih": tarih[:10],
            "en_dusuk": _deger(d, f"enDusukGun{n}"),
            "en_yuksek": _deger(d, f"enYuksekGun{n}"),
            "en_dusuk_nem": _deger(d, f"enDusukNemGun{n}"),
            "en_yuksek_nem": _deger(d, f"enYuksekNemGun{n}"),
            "ruzgar_hiz": _deger(d, f"ruzgarHizGun{n}"),
            "ruzgar_yon_derece": _deger(d, f"ruzgarYonGun{n}"),
            "ruzgar_yon": _yon(_deger(d, f"ruzgarYonGun{n}")),
            "hadise": _hadise(d.get(f"hadiseGun{n}")),
        }
    return [gunler[t] for t in sorted(gunler)]


def saatlik_cek(istno: int) -> list[dict]:
    liste = _json("tahminler/saatlik", istno=istno)
    if not liste:
        return []
    cikti = []
    for s in liste[0].get("tahmin", []):
        cikti.append({
            "zaman": _yerel(s.get("tarih")),
            "sicaklik": _deger(s, "sicaklik"),
            "hissedilen": _deger(s, "hissedilenSicaklik"),
            "nem": _deger(s, "nem"),
            "ruzgar_hiz": _deger(s, "ruzgarHizi"),
            "ruzgar_azami": _deger(s, "maksimumRuzgarHizi"),
            "ruzgar_yon_derece": _deger(s, "ruzgarYonu"),
            "ruzgar_yon": _yon(_deger(s, "ruzgarYonu")),
            "hadise": _hadise(s.get("hadise")),
        })
    return cikti


# -- elle giris -----------------------------------------------------------

SON_DURUM_ALANLARI = [
    "olcum_zamani", "sicaklik", "hissedilen", "nem", "basinc", "gorus_metre",
    "kapalilik", "ruzgar_hiz", "ruzgar_yon_derece", "ruzgar_yon",
    "yagis_1saat", "yagis_24saat", "kar_yukseklik", "hadise"]

GUN_ALANLARI = [
    "tarih", "en_dusuk", "en_yuksek", "en_dusuk_nem", "en_yuksek_nem",
    "ruzgar_hiz", "ruzgar_yon_derece", "ruzgar_yon", "hadise"]

SAAT_ALANLARI = [
    "zaman", "sicaklik", "hissedilen", "nem", "ruzgar_hiz", "ruzgar_azami",
    "ruzgar_yon_derece", "ruzgar_yon", "hadise"]


def _bicimle(alanlar: list[str], kayit: dict | None) -> dict | None:
    """Kaydi alan alan ayni bicime oturtur; eksik alan None kalir.

    Elle girilen dosya butun alanlari icermeyebilir; ciktinin bicimi
    kaynaga gore degismemeli, yoksa sayfa iki ayri sekil gormek zorunda
    kalir.
    """
    if not kayit:
        return None
    cikti = {a: kayit.get(a) for a in alanlar}
    ham_hadise = kayit.get("hadise")
    cikti["hadise"] = (ham_hadise if isinstance(ham_hadise, dict)
                       else _hadise(ham_hadise if isinstance(ham_hadise, str)
                                    else ""))
    if not cikti.get("ruzgar_yon"):
        cikti["ruzgar_yon"] = _yon(cikti.get("ruzgar_yon_derece"))
    return cikti


def elle_cek(kok: Path) -> dict:
    """Kaynak kalici olarak dustugunde panelden girilen dosya okunur."""
    yol = kok / ELLE_DOSYA
    d = ortak.json_oku(yol)
    if not d:
        raise ortak.CekmeHatasi(f"{yol} yok ya da okunamadi.")
    return {
        "merkez": d.get("merkez", {"il": "Bursa"}),
        "son_durum": _bicimle(SON_DURUM_ALANLARI, d.get("son_durum")),
        "gunler": [_bicimle(GUN_ALANLARI, g) for g in d.get("gunler", []) if g],
        "saatlik": [_bicimle(SAAT_ALANLARI, s)
                    for s in d.get("saatlik", []) if s],
        "kaynak": {
            "ad": "Elle giriş",
            "kisa": "panel",
            "adres": str(yol),
            "kosullar": "",
            "kunye": "",
        },
    }


# -- akis -----------------------------------------------------------------

def mgm_cek(il: str, ilce: str) -> dict:
    merkez = merkez_coz(il, ilce)
    ortak.log(f"  Merkez: {merkez.get('il')} / {merkez.get('ilce')} "
              f"(merkezId {merkez.get('merkezId')}, "
              f"yükseklik {merkez.get('yukseklik')} m)")
    ortak.bekle()
    son = son_durum_cek(merkez["sondurumIstNo"])
    ortak.bekle()
    gunler = gunluk_cek(merkez["gunlukTahminIstNo"])
    ortak.bekle()
    saatlik = saatlik_cek(merkez["saatlikTahminIstNo"])
    return {
        "merkez": {
            "il": merkez.get("il", ""),
            "ilce": merkez.get("ilce", ""),
            "merkez_id": merkez.get("merkezId"),
            "enlem": merkez.get("enlem"),
            "boylam": merkez.get("boylam"),
            "yukseklik": merkez.get("yukseklik"),
            "sondurum_istno": merkez.get("sondurumIstNo"),
            "gunluk_istno": merkez.get("gunlukTahminIstNo"),
            "saatlik_istno": merkez.get("saatlikTahminIstNo"),
        },
        "son_durum": son,
        "gunler": gunler,
        "saatlik": saatlik,
        "kaynak": {
            "ad": "Meteoroloji Genel Müdürlüğü",
            "kisa": "MGM",
            "adres": "https://www.mgm.gov.tr/",
            "kosullar": "https://www.mgm.gov.tr/site/yasal-uyari.aspx",
            "kunye": "Kaynak: Meteoroloji Genel Müdürlüğü.",
        },
    }


def calistir(kok: Path, kaynak_adi: str, il: str, ilce: str) -> int:
    cikti = kok / f"{BILESEN}.json"
    try:
        paket = elle_cek(kok) if kaynak_adi == "elle" else mgm_cek(il, ilce)
    except ortak.CekmeHatasi as e:
        return ortak.dusme_ile_bitir(kok, BILESEN, cikti, str(e))
    except Exception as e:
        return ortak.dusme_ile_bitir(kok, BILESEN, cikti, repr(e))

    if not paket.get("son_durum") and not paket.get("gunler"):
        return ortak.dusme_ile_bitir(
            kok, BILESEN, cikti,
            f"{kaynak_adi} kaynagi ne son durum ne tahmin dondurdu")

    tanimsiz = []
    for h in ([paket["son_durum"]["hadise"]] if paket.get("son_durum") else []) \
            + [g["hadise"] for g in paket.get("gunler", [])] \
            + [s["hadise"] for s in paket.get("saatlik", [])]:
        if h.get("ad_dogrulanmadi"):
            tanimsiz.append(h["kod"])

    veri = {
        "_not": ("MGM'nin açık uçlarından çekildi. Yayınlanırken kaynak "
                 "belirtilir. Ölçülemeyen alanlar null bırakılır; MGM'nin "
                 "-9999 değeri sıfır gibi gösterilmez. Tanınmayan hadise "
                 "kodu uydurulmaz, ham kod yazılır."),
        "guncelleme": ortak.simdi(),
        "bayat_esik_dakika": BAYAT_ESIK_DAKIKA,
        "kaynak": paket["kaynak"],
        "merkez": paket.get("merkez", {}),
        "son_durum": paket.get("son_durum"),
        "gunler": paket.get("gunler", []),
        "saatlik": paket.get("saatlik", []),
        "denetim": {
            "gun": len(paket.get("gunler", [])),
            "saatlik_adim": len(paket.get("saatlik", [])),
            "son_durum_var": bool(paket.get("son_durum")),
            "tanimsiz_hadise_kodu": sorted(set(tanimsiz)),
        },
    }

    ortak.json_yaz(cikti, veri)
    ortak.durum_yaz(kok, BILESEN, "taze")

    s = veri["son_durum"]
    if s:
        ortak.log(f"  Şu an: {s['sicaklik']}°C ({s['hadise']['ad']}), "
                  f"nem %{s['nem']}, rüzgâr {s['ruzgar_hiz']} km/sa "
                  f"{s['ruzgar_yon']} — ölçüm {s['olcum_zamani']}")
    for g in veri["gunler"]:
        ortak.log(f"    {g['tarih']}  {g['en_dusuk']}/{g['en_yuksek']}°C  "
                  f"{g['hadise']['ad']}")
    if tanimsiz:
        ortak.log("UYARI: sözlükte olmayan hadise kodu -> "
                  + ", ".join(sorted(set(tanimsiz))))
    ortak.log(f"Bitti: {len(veri['gunler'])} gün, "
              f"{len(veri['saatlik'])} saatlik adım -> {cikti}")
    return 0


def main() -> int:
    ayristi = argparse.ArgumentParser(
        description="Bursa hava durumunu MGM'den çeker.")
    ayristi.add_argument("--kaynak", default="mgm", choices=["mgm", "elle"],
                         help="veri kaynagi (varsayilan: mgm)")
    ayristi.add_argument("--il", default="Bursa", help="il adi")
    ayristi.add_argument("--ilce", default="",
                         help="ilce adi (bos: il merkezi)")
    ayristi.add_argument("--kok", default=None,
                         help="cikti koku (ortam degiskeni: BH_CANLI_KOK)")
    arg = ayristi.parse_args()

    kok = ortak.kok_coz(arg.kok)
    ortak.log_kur(kok, BILESEN)
    ortak.log(f"Hava durumu çekiliyor (kaynak: {arg.kaynak}) -> {kok}")
    return calistir(kok, arg.kaynak, arg.il, arg.ilce)


if __name__ == "__main__":
    raise SystemExit(main())
