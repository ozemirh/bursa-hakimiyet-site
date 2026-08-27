"""Bursa icin namaz vakitlerini Diyanet yontemiyle hesaplar.

Sag raydaki uc sekmeden ikincisini besler (URUN-PLANI.md bolum 1, madde 12).
Ucretli servis kullanilmaz (26 Agustos 2026 karari, URUN-PLANI.md bolum 8).

NEDEN CEKME DEGIL HESAP (olculdu, 27 Agustos 2026)

Ilk secenek Diyanet'in kendi sayfasini okumakti. Olcum: diyanet.gov.tr
alan adindaki hicbir sunucu bu agdan cevap vermiyor - istek TLS
tokalasmasindan sonra sifirlaniyor (RemoteDisconnected / connection reset).
Denenen makineler: Python urllib, curl (Schannel) ve tarayici tabanli
getirici; ucu de ayni sonucu verdi.

    www.diyanet.gov.tr              88.255.37.202   baglanti sifirlandi
    namazvakitleri.diyanet.gov.tr   88.255.37.167   baglanti sifirlandi
    vakithesaplama.diyanet.gov.tr   88.255.37.145   baglanti sifirlandi

Bu yuzden varsayilan yol HESAPtir. Hesap ayrica daha saglamdir: ag
gerektirmez, kaynak dusmesi diye bir sorunu yoktur, kullanim sarti
sorunu dogurmaz. Vakit bir ASTRONOMI OLGUSUDUR; telif korumasina girmez.

YONTEM

Gunes konumu Meeus'un dusuk dogruluklu (birkac saniye hatali) algoritmasiyla
bulunur; deklinasyon ve denklem-i zaman her vakit icin O VAKTIN saatinde
yeniden hesaplanir (iki yineleme). Diyanet'in olcutleri:

    imsak    gunes ufkun 18 derece altinda
    gunes    ust kenar ufukta: -0.8333 derece + rakim alcalmasi
    ogle     gunesin gecisi (zeval)
    ikindi   golge = nesne boyu + ogle golgesi (Safii, carpan 1)
    aksam    gunes batisi, ayni ufuk acisi
    yatsi    gunes ufkun 17 derece altinda

TEMKIN - OLCULDU, UYDURULMADI

Diyanet yayimladigi vakitlere temkin (ihtiyat payi) ekler. Temkin degerleri
Diyanet'in acikladigi Bursa tablosuyla karsilastirilarak OLCULDU; kodda
sabit olarak durur ve --dogrula ile her zaman yeniden olculebilir. Olcum
sonuclari README.md'de.

Kullanim:
    python namaz_vakitleri.py                 # Bursa, 7 gun
    python namaz_vakitleri.py --gun 30
    python namaz_vakitleri.py --dogrula       # gomulu tabloya karsi olc
    python namaz_vakitleri.py --kaynak elle

Cikti: <kok>/namaz-vakitleri.json ve <kok>/durum-namaz-vakitleri.json

Cikis kodu: 0 taze veri - 2 uretilemedi, onceki dosya korundu -
1 uretilemedi ve elde onceki veri de yok.
"""

from __future__ import annotations

import argparse
import math
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ortak  # noqa: E402

BILESEN = "namaz-vakitleri"

# Hesap ag gerektirmedigi icin "bayat" olmaz; esik yalnizca dosyanin
# guncellenmedigini (zamanlayici durmus olabilir) fark etmek icindir.
BAYAT_ESIK_DAKIKA = 2880  # 48 saat

ELLE_DOSYA = "namaz-elle.json"

# Bursa il merkezi. Kodda sabit degil, --enlem/--boylam ile degistirilebilir.
BURSA = {"ad": "Bursa", "enlem": 40.1826, "boylam": 29.0665, "rakim": 155}

DILIM = 3.0        # Turkiye kalici UTC+3; yaz saati uygulamasi yok
IMSAK_ACI = 18.0   # Diyanet 1983'ten beri imsakta 18 derece kullaniyor
YATSI_ACI = 17.0
IKINDI_CARPAN = 1  # Safii: golge = nesne boyu + ogle golgesi

VAKITLER = ["imsak", "gunes", "ogle", "ikindi", "aksam", "yatsi"]

VAKIT_ADI = {
    "imsak": "İmsak", "gunes": "Güneş", "ogle": "Öğle",
    "ikindi": "İkindi", "aksam": "Akşam", "yatsi": "Yatsı",
}

# OLCULMUS temkin (dakika). Diyanet'in yayimladigi Bursa tablosuyla
# karsilastirilarak bulundu; --dogrula bunu her kosuda yeniden olcer.
# Isaret: eksi = hesaplanan vakitten once, arti = sonra.
#
# Degerler tam sayi taramasiyla secildi: her vakit icin -7..+7 arasindaki
# butun temkinler denendi ve yayimlanan tabloya karsi azami sapmayi en
# kucuk yapan alindi. Sonuc alti vakitte de azami 1 dakika (bkz. README).
TEMKIN = {
    "imsak": 0,
    "gunes": -5,
    "ogle": +5,
    "ikindi": +4,
    "aksam": +5,
    "yatsi": +1,
}

# Diyanet'in yayimladigi Bursa vakitleri, Agustos 2026.
# 27 Agustos 2026'da alindi. diyanet.gov.tr bu agdan erisilemedigi icin
# tablo Diyanet verisini yayimlayan iki ulusal yayinin sayfasindan
# alinip BIREBIR AYNI oldugu dogrulandi (Haberturk ve CNN Turk).
# Yalnizca dogrulama icin durur; uretilen ciktida kullanilmaz.
DOGRULAMA_REFERANSI = {
    "_kaynak": ("Diyanet İşleri Başkanlığı vakitleri, 2026 Ağustos, Bursa. "
                "27 Ağustos 2026'da iki bağımsız yayından alınıp "
                "birebir aynı olduğu doğrulandı."),
    "2026-08-01": ("04:12", "05:54", "13:15", "17:08", "20:26", "22:01"),
    "2026-08-02": ("04:14", "05:55", "13:15", "17:08", "20:25", "21:59"),
    "2026-08-03": ("04:15", "05:56", "13:15", "17:08", "20:24", "21:58"),
    "2026-08-04": ("04:17", "05:57", "13:15", "17:07", "20:23", "21:56"),
    "2026-08-05": ("04:18", "05:58", "13:15", "17:07", "20:22", "21:55"),
    "2026-08-06": ("04:19", "05:59", "13:15", "17:06", "20:20", "21:53"),
    "2026-08-07": ("04:21", "06:00", "13:15", "17:06", "20:19", "21:51"),
    "2026-08-08": ("04:22", "06:01", "13:15", "17:05", "20:18", "21:50"),
    "2026-08-09": ("04:24", "06:02", "13:14", "17:05", "20:17", "21:48"),
    "2026-08-10": ("04:25", "06:03", "13:14", "17:04", "20:16", "21:46"),
    "2026-08-11": ("04:27", "06:04", "13:14", "17:04", "20:14", "21:45"),
    "2026-08-12": ("04:28", "06:05", "13:14", "17:03", "20:13", "21:43"),
    "2026-08-13": ("04:30", "06:06", "13:14", "17:03", "20:12", "21:41"),
    "2026-08-14": ("04:31", "06:07", "13:14", "17:02", "20:10", "21:40"),
    "2026-08-15": ("04:32", "06:08", "13:13", "17:02", "20:09", "21:38"),
    "2026-08-16": ("04:34", "06:09", "13:13", "17:01", "20:08", "21:36"),
    "2026-08-17": ("04:35", "06:10", "13:13", "17:00", "20:06", "21:34"),
    "2026-08-18": ("04:37", "06:11", "13:13", "17:00", "20:05", "21:33"),
    "2026-08-19": ("04:38", "06:12", "13:13", "16:59", "20:03", "21:31"),
    "2026-08-20": ("04:39", "06:13", "13:12", "16:58", "20:02", "21:29"),
    "2026-08-21": ("04:41", "06:14", "13:12", "16:58", "20:01", "21:27"),
    "2026-08-22": ("04:42", "06:15", "13:12", "16:57", "19:59", "21:25"),
    "2026-08-23": ("04:43", "06:15", "13:12", "16:56", "19:58", "21:23"),
    "2026-08-24": ("04:45", "06:16", "13:11", "16:55", "19:56", "21:22"),
    "2026-08-25": ("04:46", "06:17", "13:11", "16:55", "19:55", "21:20"),
    "2026-08-26": ("04:47", "06:18", "13:11", "16:54", "19:53", "21:18"),
    "2026-08-27": ("04:49", "06:19", "13:10", "16:53", "19:52", "21:16"),
    "2026-08-28": ("04:50", "06:20", "13:10", "16:52", "19:50", "21:14"),
    "2026-08-29": ("04:51", "06:21", "13:10", "16:51", "19:49", "21:12"),
    "2026-08-30": ("04:53", "06:22", "13:10", "16:51", "19:47", "21:11"),
    "2026-08-31": ("04:54", "06:23", "13:09", "16:50", "19:45", "21:09"),
}

_DER = math.radians
_DRC = math.degrees


# -- gunes konumu ---------------------------------------------------------

def julian_gun(g: date) -> float:
    """Takvim gununun 00:00 UT anina karsilik gelen Julyen gun sayisi."""
    y, a, gun = g.year, g.month, g.day
    if a <= 2:
        y -= 1
        a += 12
    yuzyil = y // 100
    duzeltme = 2 - yuzyil + yuzyil // 4
    return (int(365.25 * (y + 4716)) + int(30.6001 * (a + 1))
            + gun + duzeltme - 1524.5)


def gunes_konumu(jd: float) -> tuple[float, float]:
    """(deklinasyon derece, denklem-i zaman dakika) dondurur.

    Meeus, Astronomical Algorithms, dusuk dogruluklu gunes konumu.
    """
    t = (jd - 2451545.0) / 36525.0
    ort_boylam = (280.46646 + t * (36000.76983 + t * 0.0003032)) % 360
    ort_anomali = 357.52911 + t * (35999.05029 - 0.0001537 * t)
    disyuvarlik = 0.016708634 - t * (0.000042037 + 0.0000001267 * t)
    merkez = (math.sin(_DER(ort_anomali))
              * (1.914602 - t * (0.004817 + 0.000014 * t))
              + math.sin(_DER(2 * ort_anomali)) * (0.019993 - 0.000101 * t)
              + math.sin(_DER(3 * ort_anomali)) * 0.000289)
    omega = 125.04 - 1934.136 * t
    gorunen = ort_boylam + merkez - 0.00569 - 0.00478 * math.sin(_DER(omega))
    egiklik = 23 + (26 + (21.448 - t * (46.8150 + t * (0.00059 - t * 0.001813)))
                    / 60) / 60
    egiklik += 0.00256 * math.cos(_DER(omega))

    deklinasyon = _DRC(math.asin(math.sin(_DER(egiklik))
                                 * math.sin(_DER(gorunen))))
    y = math.tan(_DER(egiklik / 2)) ** 2
    denklem = (y * math.sin(2 * _DER(ort_boylam))
               - 2 * disyuvarlik * math.sin(_DER(ort_anomali))
               + 4 * disyuvarlik * y * math.sin(_DER(ort_anomali))
               * math.cos(2 * _DER(ort_boylam))
               - 0.5 * y * y * math.sin(4 * _DER(ort_boylam))
               - 1.25 * disyuvarlik * disyuvarlik
               * math.sin(2 * _DER(ort_anomali)))
    return deklinasyon, 4 * _DRC(denklem)


def saat_acisi(enlem: float, deklinasyon: float, irtifa: float):
    """Gunesin verilen irtifaya geldigi saat acisi (derece). Olmuyorsa None.

    Kutba yakin enlemlerde imsak/yatsi hic olusmayabilir; o durumda None
    doner ve vakit ciktiya null yazilir - uydurulmaz.
    """
    pay = (math.sin(_DER(irtifa))
           - math.sin(_DER(enlem)) * math.sin(_DER(deklinasyon)))
    payda = math.cos(_DER(enlem)) * math.cos(_DER(deklinasyon))
    if payda == 0:
        return None
    oran = pay / payda
    if oran < -1 or oran > 1:
        return None
    return _DRC(math.acos(oran))


# -- vakit hesabi ---------------------------------------------------------

def ufuk_irtifasi(rakim: float) -> float:
    """Kirilma + gunes yariçapi (-0.8333) ve rakimdan gelen ufuk alcalmasi."""
    return -0.8333 - 0.0347 * math.sqrt(max(rakim, 0.0))


def vakitleri_hesapla(g: date, enlem: float, boylam: float, rakim: float,
                      dilim: float = DILIM, imsak_aci: float = IMSAK_ACI,
                      yatsi_aci: float = YATSI_ACI,
                      ikindi_carpan: int = IKINDI_CARPAN,
                      yineleme: int = 2) -> dict:
    """Bir gunun alti vaktini saat cinsinden (13.5 = 13:30) dondurur.

    Deklinasyon ve denklem-i zaman her vakit icin o vaktin tahmini
    saatinde yeniden hesaplanir; tek seferlik (ogle vakti) hesap
    imsak ve yatsida bir dakikaya varan sapma birakiyordu.
    """
    jd0 = julian_gun(g)

    def coz(baslangic: float, irtifa_fn, once: bool | None):
        saat = baslangic
        for _ in range(yineleme):
            deklinasyon, denklem = gunes_konumu(jd0 + (saat - dilim) / 24.0)
            ogle = 12.0 + dilim - boylam / 15.0 - denklem / 60.0
            if once is None:
                return ogle
            aci = saat_acisi(enlem, deklinasyon, irtifa_fn(deklinasyon))
            if aci is None:
                return None
            saat = ogle - aci / 15.0 if once else ogle + aci / 15.0
        return saat

    ufuk = lambda _dek: ufuk_irtifasi(rakim)  # noqa: E731

    def ikindi_irtifasi(deklinasyon: float) -> float:
        golge = ikindi_carpan + math.tan(abs(_DER(enlem - deklinasyon)))
        return _DRC(math.atan(1.0 / golge))

    return {
        "imsak": coz(5.0, lambda _d: -imsak_aci, True),
        "gunes": coz(6.0, ufuk, True),
        "ogle": coz(12.0, ufuk, None),
        "ikindi": coz(16.0, ikindi_irtifasi, False),
        "aksam": coz(19.0, ufuk, False),
        "yatsi": coz(21.0, lambda _d: -yatsi_aci, False),
    }


def saat_metni(saat: float | None, temkin: int = 0) -> str:
    """Ondalik saati temkinle birlikte SS:DD metnine cevirir."""
    if saat is None:
        return ""
    dakika = int(round(saat * 60)) + temkin
    dakika %= 24 * 60
    return f"{dakika // 60:02d}:{dakika % 60:02d}"


def gun_kaydi(g: date, yer: dict) -> dict:
    ham = vakitleri_hesapla(g, yer["enlem"], yer["boylam"], yer["rakim"])
    kayit = {"tarih": g.isoformat(), "vakitler": {}}
    for v in VAKITLER:
        kayit["vakitler"][v] = saat_metni(ham[v], TEMKIN[v])
    return kayit


# -- dogrulama ------------------------------------------------------------

def _dakika(metin: str) -> int:
    saat, dakika = metin.split(":")
    return int(saat) * 60 + int(dakika)


def dogrula(yer: dict, referans: dict) -> dict:
    """Hesabi Diyanet'in yayimladigi tabloyla karsilastirir.

    Her vakit icin sapmalarin en buyugu, ortalamasi ve birebir tutan gun
    sayisi olculur. Beyan degil olcumdur; --dogrula ile her zaman
    tekrarlanabilir.
    """
    gunler = sorted(k for k in referans if not k.startswith("_"))
    sonuc = {v: {"azami_sapma_dk": 0, "ortalama_sapma_dk": 0.0,
                 "birebir": 0, "gun": 0} for v in VAKITLER}
    toplam = {v: 0 for v in VAKITLER}
    for tarih in gunler:
        hesap = gun_kaydi(date.fromisoformat(tarih), yer)["vakitler"]
        for v, beklenen in zip(VAKITLER, referans[tarih]):
            if not hesap[v]:
                continue
            sapma = _dakika(hesap[v]) - _dakika(beklenen)
            s = sonuc[v]
            s["gun"] += 1
            s["azami_sapma_dk"] = max(s["azami_sapma_dk"], abs(sapma))
            s["birebir"] += 1 if sapma == 0 else 0
            toplam[v] += sapma
    for v in VAKITLER:
        if sonuc[v]["gun"]:
            sonuc[v]["ortalama_sapma_dk"] = round(
                toplam[v] / sonuc[v]["gun"], 2)
    return {
        "referans": referans.get("_kaynak", ""),
        "gun": len(gunler),
        "vakitler": sonuc,
        "azami_sapma_dk": max(s["azami_sapma_dk"] for s in sonuc.values()),
    }


# -- elle giris -----------------------------------------------------------

def elle_cek(kok: Path) -> list[dict]:
    """Panelden girilen vakit listesi. Hesap yolu reddedilirse kullanilir.

    Bicim: {"gunler": [{"tarih": "2026-08-27",
                        "vakitler": {"imsak": "04:49", ...}}]}
    """
    yol = kok / ELLE_DOSYA
    d = ortak.json_oku(yol)
    if not d:
        raise ortak.CekmeHatasi(f"{yol} yok ya da okunamadi.")
    gunler = []
    for g in d.get("gunler", []):
        if not g.get("tarih") or not g.get("vakitler"):
            continue
        gunler.append({
            "tarih": g["tarih"],
            "vakitler": {v: g["vakitler"].get(v, "") for v in VAKITLER},
        })
    return gunler


# -- akis -----------------------------------------------------------------

def calistir(kok: Path, kaynak_adi: str, yer: dict, gun_sayisi: int) -> int:
    cikti = kok / f"{BILESEN}.json"
    bugun = date.today()

    try:
        if kaynak_adi == "elle":
            gunler = elle_cek(kok)
            kaynak = {
                "ad": "Elle giriş",
                "kisa": "panel",
                "adres": str(kok / ELLE_DOSYA),
                "kosullar": "",
                "kunye": "",
            }
        else:
            gunler = [gun_kaydi(bugun + timedelta(days=n), yer)
                      for n in range(gun_sayisi)]
            kaynak = {
                "ad": "Diyanet İşleri Başkanlığı ölçütleriyle astronomik hesap",
                "kisa": "hesap",
                "adres": "",
                "kosullar": "",
                "kunye": ("Vakitler Diyanet İşleri Başkanlığı'nın ölçütlerine "
                          "göre hesaplanmıştır."),
            }
    except ortak.CekmeHatasi as e:
        return ortak.dusme_ile_bitir(kok, BILESEN, cikti, str(e))
    except Exception as e:
        return ortak.dusme_ile_bitir(kok, BILESEN, cikti, repr(e))

    if not gunler:
        return ortak.dusme_ile_bitir(
            kok, BILESEN, cikti, f"{kaynak_adi} kaynagi bos liste dondurdu")

    olcum = dogrula(yer, DOGRULAMA_REFERANSI) if kaynak_adi == "hesap" else None

    veri = {
        "_not": ("Vakitler Diyanet ölçütleriyle hesaplanır: imsak 18°, "
                 "yatsı 17°, ikindi Şafii (gölge çarpanı 1), güneş/akşam "
                 "rakım düzeltmeli ufuk. Temkin değerleri Diyanet'in "
                 "yayımladığı tabloyla karşılaştırılarak ölçülmüştür; "
                 "denetim bloğuna bakınız."),
        "guncelleme": ortak.simdi(),
        "bayat_esik_dakika": BAYAT_ESIK_DAKIKA,
        "kaynak": kaynak,
        "yer": dict(yer),
        "yontem": {
            "imsak_aci": IMSAK_ACI,
            "yatsi_aci": YATSI_ACI,
            "ikindi_carpan": IKINDI_CARPAN,
            "zaman_dilimi": DILIM,
            "temkin_dakika": dict(TEMKIN),
        },
        "vakit_adlari": dict(VAKIT_ADI),
        "gunler": gunler,
        "denetim": {
            "gun": len(gunler),
            "eksik_vakit": sum(1 for g in gunler
                               for v in VAKITLER if not g["vakitler"][v]),
            "dogrulama": olcum,
        },
    }

    ortak.json_yaz(cikti, veri)
    ortak.durum_yaz(kok, BILESEN, "taze")

    ilk = gunler[0]
    ortak.log("  " + ilk["tarih"] + "  " + "  ".join(
        f"{VAKIT_ADI[v]} {ilk['vakitler'][v]}" for v in VAKITLER))
    if olcum:
        ortak.log(f"  Doğrulama ({olcum['gun']} gün, Diyanet tablosu): "
                  f"azami sapma {olcum['azami_sapma_dk']} dk")
        for v in VAKITLER:
            s = olcum["vakitler"][v]
            ortak.log(f"    {VAKIT_ADI[v]:7s} azami {s['azami_sapma_dk']} dk, "
                      f"ortalama {s['ortalama_sapma_dk']:+.2f} dk, "
                      f"birebir {s['birebir']}/{s['gun']}")
    ortak.log(f"Bitti: {len(gunler)} gün -> {cikti}")
    return 0


def main() -> int:
    ayristi = argparse.ArgumentParser(
        description="Bursa namaz vakitlerini Diyanet ölçütleriyle hesaplar.")
    ayristi.add_argument("--kaynak", default="hesap",
                         choices=["hesap", "elle"],
                         help="veri kaynagi (varsayilan: hesap)")
    ayristi.add_argument("--gun", type=int, default=7,
                         help="kac gunluk vakit uretilecek (varsayilan: 7)")
    ayristi.add_argument("--enlem", type=float, default=BURSA["enlem"])
    ayristi.add_argument("--boylam", type=float, default=BURSA["boylam"])
    ayristi.add_argument("--rakim", type=float, default=BURSA["rakim"])
    ayristi.add_argument("--ad", default=BURSA["ad"], help="yer adi")
    ayristi.add_argument("--dogrula", action="store_true",
                         help="yalnizca gomulu Diyanet tablosuna karsi olc")
    ayristi.add_argument("--kok", default=None,
                         help="cikti koku (ortam degiskeni: BH_CANLI_KOK)")
    arg = ayristi.parse_args()

    yer = {"ad": arg.ad, "enlem": arg.enlem,
           "boylam": arg.boylam, "rakim": arg.rakim}

    kok = ortak.kok_coz(arg.kok)
    ortak.log_kur(kok, BILESEN)

    if arg.dogrula:
        olcum = dogrula(yer, DOGRULAMA_REFERANSI)
        ortak.log(f"Doğrulama: {yer['ad']} ({yer['enlem']}, {yer['boylam']}, "
                  f"rakım {yer['rakim']} m), {olcum['gun']} gün")
        ortak.log("  " + olcum["referans"])
        for v in VAKITLER:
            s = olcum["vakitler"][v]
            ortak.log(f"  {VAKIT_ADI[v]:7s} temkin {TEMKIN[v]:+d} dk -> "
                      f"azami sapma {s['azami_sapma_dk']} dk, "
                      f"ortalama {s['ortalama_sapma_dk']:+.2f} dk, "
                      f"birebir tutan {s['birebir']}/{s['gun']}")
        ortak.log(f"Azami sapma (altı vakit): {olcum['azami_sapma_dk']} dk")
        return 0

    ortak.log(f"Namaz vakitleri üretiliyor (kaynak: {arg.kaynak}) -> {kok}")
    return calistir(kok, arg.kaynak, yer, max(1, arg.gun))


if __name__ == "__main__":
    raise SystemExit(main())
