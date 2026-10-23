"""Namaz vakti hesabi - SAF standart kutuphane, ag yok, dosya yok, durum yok.

19 Ekim 2026'da `namaz_vakitleri.py`den ayrildi. Neden: zamanlayici kapali
kaldiginda `namaz-vakitleri.json` 12 Eylul'de dondu ve site 37 gun boyunca
12 Eylul vakitlerini "SIMDI" diye gosterdi (DEGERLENDIRME-2026-10.md bulgu
10). Vakit bir astronomi olgusudur; hesap mikro saniyeler surer ve ag
gerektirmez. Site bu modulu ISTEK ANINDA yukler ve bugunun vakitlerini
kendisi hesaplar - bu bilesen icin "bayat veri" diye bir durum kalmaz.

Bu dosya BILEREK hicbir sey ice aktarmaz (ne `ortak` ne Django): site onu
`importlib` ile dosya yolundan yukler, `sys.path`e dokunmadan. Yeni bir
bagimlilik eklemek o yuklemeyi bozar.

Yontem ve temkin olcumu `namaz_vakitleri.py` basinda ve README.md'de;
`python namaz_vakitleri.py --dogrula` hesabi Diyanet tablosuna karsi
yeniden olcer.
"""

from __future__ import annotations

import math
from datetime import date

# Bursa il merkezi. Betikte --enlem/--boylam ile degistirilebilir.
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
# karsilastirilarak bulundu; `namaz_vakitleri.py --dogrula` bunu yeniden
# olcer. Isaret: eksi = hesaplanan vakitten once, arti = sonra.
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

KAYNAK = {
    "ad": "Diyanet İşleri Başkanlığı ölçütleriyle astronomik hesap",
    "kisa": "hesap",
    "adres": "",
    "kosullar": "",
    "kunye": ("Vakitler Diyanet İşleri Başkanlığı'nın ölçütlerine "
              "göre hesaplanmıştır."),
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
    doner ve vakit ciktiya bos yazilir - uydurulmaz.
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
    """Kirilma + gunes yaricapi (-0.8333) ve rakimdan gelen ufuk alcalmasi."""
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


def gun_kaydi(g: date, yer: dict | None = None) -> dict:
    """`{"tarih": "YYYY-AA-GG", "vakitler": {"imsak": "05:41", ...}}`."""
    yer = yer or BURSA
    ham = vakitleri_hesapla(g, yer["enlem"], yer["boylam"], yer["rakim"])
    kayit = {"tarih": g.isoformat(), "vakitler": {}}
    for v in VAKITLER:
        kayit["vakitler"][v] = saat_metni(ham[v], TEMKIN[v])
    return kayit
