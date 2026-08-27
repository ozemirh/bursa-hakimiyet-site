"""Piyasa bandinin bosta kalan iki kalemini ceker: GRAM ALTIN ve BIST 100.

Neden ayri bir betik: doviz.py TCMB gunluk bultenini okur ve dolar/euro/
sterlini oradan alir. TCMB gram altin ve BIST 100 yayimlamaz, bu yuzden o
iki kutu bugune kadar bos kaldi (README "Gram altin ve BIST 100 - neden
kaynak yok" bolumu). Bu betik o boslugu doldurur ve sonucu piyasa.json'a
yazar; doviz.py da oradan okur. TCMB mantigi degismedi.

Neden ayri bir siklik: TCMB bulteni gunde bir kez (is gunu 15:30) cikar,
gram altin ve BIST 100 ise gun icinde surekli hareket eder. Bu yuzden bu
betik 15 dakikada bir kosar (--surekli 15), doviz.py gunde iki kez.

  DORT KAYNAK, SIRAYLA DENENIR

  1. evds    TCMB EVDS. Resmi kaynak, ANAHTAR ISTEMEZ, saf urllib ile tek
             POST. Gram altin BIST Kiymetli Madenler Piyasasi altin
             kapanisindan (TP.ALTINPIYASA.KAP02, TL/kg -> /1000), BIST 100
             TP.MK.F.BILESIK'ten gelir. Ikisi de RESMI KAPANISTIR, gun ici
             fiyat degildir: gun icinde en taze gozlem bir onceki is
             gunune aittir, kapanis aksam duser. Bu yuzden kayitlar
             "resmi_kapanis" damgasi ve gozlem tarihiyle doner ve gun ici
             canli kotasyon geldiginde ona yerini birakir - kapanis bugune
             aitse tersi olur (bkz. sira_puani).
  2. google  Google Finance. Sayfa JS ile
             basiliyor - duz HTTP istegi 200 doner ama fiyat HTML'de YOKTUR
             (olculdu). Bu yuzden bassiz Chrome'un --dump-dom kipi kullanilir:
             sayfa gercekten calistirilir, olusan DOM okunur. Paket gerekmez,
             yalnizca makinede Chrome bulunmasi yeter.
  2. doviz   doviz.com ana sayfasi. Duz HTTP, sunucu tarafinda basiliyor,
             tek istekte XU100 + gram-altin + USD + EUR + GBP veriyor.
  3. mynet   finans.mynet.com serit. Duz HTTP, ayni sekilde sunucu tarafinda.

Google neden tek basina birakilmadi: Google otomatik erisimi engelleyebilir
(CAPTCHA, IP kisiti) ve sayfa yapisini haber vermeden degistirir; ustelik
Chrome'a bagimlidir. Yedeklerin hepsi saf standart kutuphaneyle calisir,
yani Google dustugunde bant durmaz. Hangi kaynaktan geldigi her kalemde
"kaynak" alaninda yazar - uydurulmaz, gizlenmez.

Google neden hala listede: EVDS gun ici fiyat vermiyor, yalnizca kapanis
veriyor. Gun ici canli rakami doviz.com ve Mynet de veriyor, yani Google
teknik olarak GEREKSIZ hale geldi. Hizmet Sartlari cekincesi (asagida)
duruyorken listeden cikarilmasi savunulabilir; bu bir urun karari oldugu
icin burada tek basina alinmadi. Cikarmak icin VARSAYILAN_SIRA'dan
"google" silmek yeter, baska degisiklik gerekmez.

  GRAM ALTIN - HESAP VE BIRIM (onemli, olculdu)

Gram altin TL/gram cinsindendir. Yedek kaynaklarin ikisi de gram altini
DOGRUDAN kote eder, cevrim gerekmez. Google'da ise TRY cinsinden altin
kotasyonu YOKTUR (olculdu: /finance/quote/XAU-TRY ve XAU-USD "Sayfa
Bulunamadi" doner). Google'da bulunan tek altin kalemi GCW00:COMEX, yani
COMEX vadeli altin sozlesmesi - USD/ons.

Google yolunda gram altin su cevrimle HESAPLANIR:

    gram_altin_TL = ons_USD * USD/TRY / 31,1034768     (1 troy ons = 31,1035 g)

Bu bir YAKLASIKTIR ve oyle isaretlenir (kaynak_durumu "hesaplanan"):
  - GCW00 vadeli fiyattir, spot degildir; vadeli fiyat spotun uzerinde durur.
  - Turkiye'de gram altin Kapalicarsi'da kendi arz/talebiyle fiyatlanir,
    uluslararasi pariteden sapabilir.
27 Agustos 2026 olcumu: hesaplanan 7.211 TL, dogrudan kote edilen 7.125 TL
-> %1,2 sapma. Bu yuzden betik DOGRUDAN KOTASYONU tercih eder; hesaplanan
deger yalnizca dogrudan kaynaklarin hepsi dustugunde yayina cikar ve o
zaman da "hesaplanan" damgasiyla cikar. Iki deger de eldeyse aralarindaki
sapma olculur ve capraz_kontrol blogunda yazilir.

  KULLANIM

    python piyasa.py                      # tek kosu (varsayilan)
    python piyasa.py --surekli 15         # 15 dakikada bir, surekli
    python piyasa.py --kaynak evds        # yalnizca resmi kapanis
    python piyasa.py --kaynak evds doviz mynet   # Chrome'suz sira
    python piyasa.py --kok D:/canli

Cikti: <kok>/piyasa.json ve <kok>/durum-piyasa.json

Cikis kodu: 0 taze veri - 2 cekilemedi, onceki dosya korundu -
1 cekilemedi ve elde onceki veri de yok. (ortak.dusme_ile_bitir)

  KULLANIM SARTLARI - olculdu 27 Agustos 2026

google.com/robots.txt: /finance yolunu KISITLAMIYOR. Dikkat: Python'un
kendi urllib.robotparser'i burada yanlis cevap verir - "Disallow: /?"
satirindaki soru isaretini dusurup kurali "Disallow: /" gibi okur ve her
yolu yasakli sanir. Ham satirlar elle esletildiginde /finance/quote/... ile
eslesen tek bir kural yoktur. (stooq ve Yahoo ise gercekten "Disallow: /"
diyordu; onlar bu yuzden elenmisti.) Ayri konu: Google Hizmet Sartlari
otomatik erisimi genel olarak hos karsilamaz - bu robots meselesi degil,
sozlesme meselesidir ve hukuk teyidine giden listeye eklenmelidir.

doviz.com/robots.txt: "Allow: /", yalnizca /api/, /user-api/, /tickerbar/,
/kucoin/, /virgul/ kapali. Betik ana sayfayi okur, o yollara hic gitmez.

finans.mynet.com/robots.txt: ilgili yollar acik (/api/ kapali, oraya
gidilmiyor).

EVDS: TCMB'nin kendi acik veri sistemidir, veriyi herkese acik yayimlar ve
erisim icin anahtar/kayit istemez. evds2/evds3 alan adlarinda robots.txt
YOKTUR (istege SPA kabugu doner); www.tcmb.gov.tr/robots.txt yalnizca
"*/search+results" yolunu kapatir, veri ucuna deginmez. Ucun kendisi
sitenin kendi arayuzunun kullandigi uctur, gizli/ozel bir uc degildir.
Yine de kunye zorunludur: BIST 100 ve altin kapanis serilerinin sahibi
Borsa Istanbul'dur, EVDS dagitir. Ticari yeniden yayimda EVDS kullanim
sartlarinin hukuk teyidi listesine eklenmesi gerekir.

Her dort kaynak da ciktiya kunyesiyle yazilir; sayfada atif gorunmelidir.
Elenen bir aday: bigpara.hurriyet.com.tr veriyi sunucu tarafinda basiyor ve
"User-agent: *" icin ilgili yollari aciyor, ama robots.txt'sinde ClaudeBot /
anthropic-ai / GPTBot gibi ajanlara acik "Disallow: /" var. Sinirdaki bir
durum oldugu icin yedek listesine ALINMADI; gerekirse ayrica degerlendirilir.
"""

from __future__ import annotations

import argparse
import html as _html
import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ortak  # noqa: E402

BILESEN = "piyasa"

# 15 dakikada bir kosuyoruz. Ust uste iki kosu kacarsa veri hala kabul
# edilebilir, ucuncude bant "guncel degil" demeli -> 45 dakika.
BAYAT_ESIK_DAKIKA = 45

# 1 troy ons = 31,1034768 gram. Gram altin cevriminin tek sabiti budur.
ONS_GRAM = 31.1034768

# Bandin sirasi URUN-PLANI.md bolum 1 madde 9'dan gelir. Dolar ve euro
# burada YAYIN icin degil DOGRULAMA icin cekilir: TCMB kuruyla
# karsilastirilip kaynagin sapip sapmadigi olculur.
KALEMLER = [
    {"anahtar": "gram_altin", "ad": "Gram altın", "birim": "TL", "asil": True},
    {"anahtar": "bist100", "ad": "BIST 100", "birim": "puan", "asil": True},
    {"anahtar": "dolar", "ad": "Dolar", "birim": "TL", "asil": False},
    {"anahtar": "euro", "ad": "Euro", "birim": "TL", "asil": False},
    {"anahtar": "sterlin", "ad": "Sterlin", "birim": "TL", "asil": False},
]

ASIL_KALEM = [k["anahtar"] for k in KALEMLER if k["asil"]]

KAYNAK_KUNYE = {
    "evds": {
        "ad": "TCMB Elektronik Veri Dağıtım Sistemi (EVDS)",
        "kisa": "TCMB EVDS",
        "adres": "https://evds2.tcmb.gov.tr/",
        "kunye": ("Kaynak: TCMB EVDS. BIST 100 ve altın kapanış serilerini "
                  "EVDS'ye Borsa İstanbul sağlar."),
    },
    "google": {
        "ad": "Google Finance",
        "kisa": "Google Finance",
        "adres": "https://www.google.com/finance/",
        "kunye": "Kaynak: Google Finance.",
    },
    "doviz": {
        "ad": "doviz.com",
        "kisa": "doviz.com",
        "adres": "https://www.doviz.com/",
        "kunye": "Kaynak: doviz.com.",
    },
    "mynet": {
        "ad": "Mynet Finans",
        "kisa": "Mynet Finans",
        "adres": "https://finans.mynet.com/",
        "kunye": "Kaynak: Mynet Finans.",
    },
}

# Google VARSAYILANDAN CIKARILDI (27 Agustos, kullanici karari:
# "tcmb evds ile ucretsiz olarak alabileceksek verileri o yolu kullanalim").
# Gerekcesi olculdu: EVDS resmi kapanisi, doviz/mynet gun ici kotasyonu
# veriyor; Google'in ekledigi tek sey 19 sn calisma suresi (zincirin
# tamami 0,3 sn), bir Chrome bagimliligi ve Hizmet Sartlari sorunu.
# Kodu duruyor: `--kaynak google ...` ile elle cagrilabilir.
VARSAYILAN_SIRA = ["evds", "doviz", "mynet"]


# -- sayi ayristirma ------------------------------------------------------

def sayi_coz(ham):
    """'14.686,70' ya da '14,686.70' -> 14686.70. Cozemezse None.

    Iki bicimi de kabul eder cunku sayfa dilini biz zorluyoruz ama kaynak
    bunu haber vermeden degistirebilir. Karar olcutu: SON gecen ayirac
    ondalik ayiracidir. Para simgesi, yuzde, bosluk temizlenir.
    """
    if ham is None:
        return None
    d = re.sub(r"[^\d,.\-]", "", str(ham).replace("\u00a0", ""))
    if not d or d in ("-", ".", ","):
        return None
    son_nokta, son_virgul = d.rfind("."), d.rfind(",")
    if son_nokta > son_virgul:
        d = d.replace(",", "")
    elif son_virgul > son_nokta:
        d = d.replace(".", "").replace(",", ".")
    try:
        return float(d)
    except ValueError:
        return None


# -- kaynak 1: TCMB EVDS (resmi, duz HTTP) --------------------------------

# EVDS'nin SPA'sinin arkasindaki veri ucu. Eski belgelerde gecen
# evds2.tcmb.gov.tr/service/evds/... yolu ARTIK CALISMIYOR: her istege
# 1355 baytlik SPA kabugu donuyor (olculdu 27 Agustos 2026). Anahtarli
# (&key=) surum de ayni kabugu donduruyor. Calisan uc budur ve ANAHTAR
# ISTEMEZ - kayit, token, oturum gerekmez.
EVDS_UC = "https://evds3.tcmb.gov.tr/igmevdsms-dis/fe"

# Hangi kalem hangi EVDS serisinden geliyor (27 Agustos 2026'da EVDS'nin
# kendi arama ucundan bulundu, /fe ile dogrulandi).
#
#   gram_altin  TP.ALTINPIYASA.KAP02 - "Altin - Kapanis Fiyati - TL/kg".
#               Veri grubu bie_altinbistbul = BIST Kiymetli Madenler
#               Piyasasi altin kapanisi. Kaynak: Borsa Istanbul. IS GUNU.
#               TL/kg kote edilir, gram icin 1000'e BOLUNUR.
#               Ayni grupta dogrudan TL/gr kote eden TP.ALTINPIYASA.KAP05
#               de var ama SEYREK dolu (17-26 Agustos araliginda 8 is
#               gununden yalnizca 1'i doluydu - olculdu), bu yuzden yayina
#               girmiyor; dolu oldugu gunlerde capraz kontrol icin okunur
#               (25-08-2026: KAP05 7150,0 - KAP02/1000 7150,5).
#   bist100     TP.MK.F.BILESIK - "(FIYAT) BIST 100 Endeks (XU100),
#               Kapanis Fiyatlarina Gore". Kaynak: Borsa Istanbul. IS GUNU.
#               DIKKAT: TP.MK.G.BILESIK "getiri" endeksidir (temettu
#               dahil) ve haberlerde anilan XU100 DEGILDIR; karistirma.
#
# Dolar ve euro BILEREK bu listede yok. Onlar bantta yayin icin degil,
# piyasa kaynagi sapmis mi diye TCMB bulteniyle karsilastirmak icin
# cekiliyor (tcmb_karsilastir). EVDS'den alinsalardi karsilastirma
# TCMB'yi TCMB ile olcerdi, yani hicbir sey olcmezdi.
EVDS_SERI = {
    "gram_altin": {"kod": "TP.ALTINPIYASA.KAP02", "carpan": 0.001,
                   "birim_notu": "EVDS TL/kg kote eder; 1000'e bölünür"},
    "bist100": {"kod": "TP.MK.F.BILESIK", "carpan": 1.0,
                "birim_notu": "endeks puanı, çarpan yok"},
}

# Capraz kontrol icin okunan ikinci altin serisi (bkz. yukarisi).
EVDS_ALTIN_GRAM_KOD = "TP.ALTINPIYASA.KAP05"

# frequency=2 "IS GUNU" demek; iki seri de is gunu serisi.
EVDS_FREKANS = "2"

# Kac gun geriye bakiliyor. Son iki gozlem gerekiyor (degisim yuzdesi
# icin) ama araya bayram girebiliyor - 9 gunluk resmi tatil gorulmustur.
# 21 gun her tatili asar ve istek yine tek POST olarak kalir.
EVDS_GUN = 21


def evds_cek():
    """TCMB EVDS'den gram altin ve BIST 100 kapanislarini ceker.

    Donen deger RESMI KAPANISTIR, gun ici fiyat degildir. Borsa Istanbul
    kapanisi ayni gun aksam EVDS'ye duser; gun icinde en taze gozlem BIR
    ONCEKI IS GUNUNE aittir. Bu yuzden kayitlar "taze" degil
    "resmi_kapanis" damgasi ve gozlem tarihi ("veri_tarihi") ile doner;
    birlestirme kurali (sira_puani) gun ici canli kotasyonla hangisinin
    one gececegine bu tarihe bakarak karar verir.
    """
    bugun = datetime.now(ortak.TR_SAAT).date()
    baslangic = (bugun - timedelta(days=EVDS_GUN)).strftime("%d-%m-%Y")
    bitis = bugun.strftime("%d-%m-%Y")

    kodlar = [t["kod"] for t in EVDS_SERI.values()] + [EVDS_ALTIN_GRAM_KOD]
    # Yuk alanlari birebir SPA'nin gonderdigi gibi olmali: groupSeperator,
    # isRaporSayfasi ve ozelFormuller alanlarindan biri EKSIKSE sunucu 500
    # doner (uc alan da tek tek olculdu). ozelFormuller bos liste olabilir.
    yuk = {
        "type": "json",
        "series": "-".join(kodlar),
        "aggregationTypes": "-".join(["last"] * len(kodlar)),
        "formulas": "-".join(["0"] * len(kodlar)),
        "startDate": baslangic,
        "endDate": bitis,
        "frequency": EVDS_FREKANS,
        "decimalSeperator": ".",
        "decimal": "4",
        "ozelFormuller": [],
        "groupSeperator": True,
        "isRaporSayfasi": True,
    }
    # Origin BILEREK gonderilmiyor. Gonderilirse tam olarak
    # "https://evds3.tcmb.gov.tr" olmak zorunda; evds2 yazilirsa sunucu
    # 403 "Invalid CORS request" doner. Hic gondermemek en dayaniklisi.
    ham = ortak.getir(
        EVDS_UC,
        basliklar={"Accept": "application/json, text/plain, */*",
                   "Content-Type": "application/json"},
        veri=json.dumps(yuk).encode("utf-8"))
    try:
        d = json.loads(ham)
    except json.JSONDecodeError:
        raise ortak.CekmeHatasi(
            "EVDS JSON yerine %d baytlik baska bir yanit dondurdu "
            "(uc degismis olabilir)" % len(ham))
    satir = d.get("items")
    if not isinstance(satir, list) or not satir:
        raise ortak.CekmeHatasi("EVDS bos seri dondurdu (items yok)")

    def son_iki(kod):
        """Seri icin (son_deger, son_tarih, onceki_deger) dondurur.

        EVDS alan adinda noktalari alt cizgiye cevirir; tatil gunleri null
        gelir, bu yuzden once dolu gozlemler suzuluyor.
        """
        alan = kod.replace(".", "_")
        dolu = [(s.get("Tarih", ""), sayi_coz(s.get(alan)))
                for s in satir if sayi_coz(s.get(alan)) is not None]
        if not dolu:
            return None, "", None
        return dolu[-1][1], dolu[-1][0], (dolu[-2][1] if len(dolu) > 1 else None)

    gelen = {}
    for anahtar, tanim in EVDS_SERI.items():
        deger, tarih, onceki = son_iki(tanim["kod"])
        if deger is None:
            continue
        c = tanim["carpan"]
        deger = deger * c
        onceki = onceki * c if onceki is not None else None
        kayit = {
            "deger": round(deger, 4),
            "onceki": round(onceki, 4) if onceki is not None else None,
            "degisim": None, "degisim_yuzde": None,
            "kaynak_durumu": "resmi_kapanis",
            "kaynak_zamani": tarih,
            "kaynak_sembol": tanim["kod"],
            # Gun ici canli kotasyonla yarisirken bu tarihe bakilir.
            "veri_tarihi": tarih,
            "birim_notu": tanim["birim_notu"],
        }
        # Degisim yuzdesi kaynaktan gelmiyor, IKI KAPANISTAN hesaplaniyor:
        # gazetelerin "onceki kapanisa gore" dedigi sey tam olarak budur.
        if onceki:
            kayit["degisim"] = round(deger - onceki, 4)
            kayit["degisim_yuzde"] = round((deger - onceki) / onceki * 100, 2)
        gelen[anahtar] = kayit

    if not gelen:
        raise ortak.CekmeHatasi(
            "EVDS yanitinda beklenen seri alanlari yok (%s) - seri kodlari "
            "degismis olabilir" % ", ".join(t["kod"] for t in EVDS_SERI.values()))

    ek = {"uc": EVDS_UC, "seri": {a: t["kod"] for a, t in EVDS_SERI.items()},
          "frekans": "İŞ GÜNÜ", "aralik": [baslangic, bitis],
          "donen_gozlem": len(satir)}

    # KAP05 (TL/gr) dolu bir gun varsa KAP02/1000 ile karsilastir: birim
    # cevrimini biz uydurmuyoruz, kaynagin kendi gram serisiyle olculuyor.
    gram_deger, gram_tarih, _ = son_iki(EVDS_ALTIN_GRAM_KOD)
    if gram_deger is not None and "gram_altin" in gelen:
        ek["gram_serisi_kontrolu"] = {
            "seri": EVDS_ALTIN_GRAM_KOD, "tarih": gram_tarih,
            "kote_edilen_tl_gram": gram_deger,
            "not": ("Seyrek dolu olduğu için yayına girmez; birim çevrimini "
                    "doğrulamak için okunur."),
        }
    return gelen, ek


# -- kaynak 2: Google Finance (bassiz Chrome) -----------------------------

GOOGLE_ADRES = "https://www.google.com/finance/quote/%s"

# Google'da hangi kalem hangi sembolde (olculdu 27 Agustos 2026).
# XAU-TRY ve XAU-USD YOK; altin yalnizca COMEX vadeli sozlesmesinde var.
GOOGLE_SEMBOL = {
    "dolar": "USD-TRY",
    "euro": "EUR-TRY",
    "sterlin": "GBP-TRY",
    "bist100": "XU100:INDEXIST",
}
GOOGLE_ALTIN_SEMBOL = "GCW00:COMEX"

CHROME_ADAY = [
    r"C:/Program Files/Google/Chrome/Application/chrome.exe",
    r"C:/Program Files (x86)/Google/Chrome/Application/chrome.exe",
    r"C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
    r"C:/Program Files/Microsoft/Edge/Application/msedge.exe",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
]

OK_ISARET = ("arrow_upward", "arrow_downward", "arrow_flat", "remove")


class _GoogleHatasi(ortak.CekmeHatasi):
    """Cekme hatasini tanı bilgisiyle birlikte tasir.

    Google dustugunde "neden dustu" en degerli bilgidir: CAPTCHA mi gordu,
    sayfa duzeni mi degisti, sembol mu kayboldu? Duz bir istisna bunu
    ciktiya tasiyamiyordu - engel izi kayboluyordu. Ek bilgi burada
    tasinir ve calistir() ciktiya yazar.
    """

    def __init__(self, mesaj, ek):
        super().__init__(mesaj)
        self.ek = ek


def chrome_bul():
    """Chrome'u bulur. BH_CHROME ortam degiskeni her seyi ezer."""
    ozel = os.environ.get("BH_CHROME")
    if ozel and Path(ozel).exists():
        return ozel
    for a in CHROME_ADAY:
        if Path(a).exists():
            return a
    for ad in ("chrome", "google-chrome", "chromium", "msedge"):
        y = shutil.which(ad)
        if y:
            return y
    return None


def dom_al(chrome: str, url: str, zaman_asimi: int = 90) -> str:
    """Sayfayi bassiz Chrome'da acar ve OLUSAN DOM'u dondurur.

    --dump-dom sarttir: Google Finance fiyati JS ile basiyor, ham HTML'de
    fiyat yok. --virtual-time-budget zamanlayicilari ileri sarar, boylece
    sabit bir "bekle" suresine gerek kalmaz.
    """
    gecici = Path(os.environ.get("TEMP") or "/tmp") / "bh-piyasa-chrome"
    p = subprocess.run(
        [chrome, "--headless=new", "--disable-gpu", "--no-first-run",
         "--no-default-browser-check", "--disable-extensions",
         "--lang=tr-TR", "--accept-lang=tr-TR",
         "--virtual-time-budget=10000",
         "--user-data-dir=" + str(gecici), "--dump-dom", url],
        capture_output=True, timeout=zaman_asimi)
    return p.stdout.decode("utf-8", "replace")


def dom_metne(dom: str) -> list:
    """DOM'u satir listesine cevirir (tarayicidaki innerText'e yakin).

    Script/style/svg atilir; blok ve satirici etiketler satir sonuna
    donusur. Google'in sinif adlari karistirilmis oldugu icin CSS secici
    yazilamaz - metin yapisi tek saglam tutamaktir.
    """
    d = re.sub(r"(?is)<(script|style|noscript|svg|template)\b.*?</\1>", " ", dom)
    d = re.sub(r"(?i)<(br|div|p|li|tr|h[1-6]|span|i|td)\b[^>]*>", "\n", d)
    d = re.sub(r"(?i)</(div|p|li|tr|h[1-6]|span|i|td)>", "\n", d)
    d = re.sub(r"<[^>]+>", " ", d)
    d = _html.unescape(d)
    return [s.strip() for s in d.split("\n") if s.strip()]


def google_kotasyon(satir: list):
    """Ana kotasyonu satir yapisindan ayiklar.

    Sayfada ONLARCA fiyat var (kenardaki dunya endeksleri seridi). Ana
    kotasyonu ayiran YAPI sudur - olculdu, sirasi sabit:

        XU100:INDEXIST     <- sembol
        add                <- "portfoye ekle" dugmesi
        BIST 100           <- ad
        14.686,70          <- FIYAT
        arrow_upward       <- yon
        +0,52%             <- degisim yuzdesi
        (                  <- ayri satira dusuyor
        +75,78             <- degisim
        ) 1G
        27 Ağu, 11:04:55 UTC+3

    Kenar seridindeki kalemlerde "add" satiri yoktur; ayirt edici olan o.
    Yapiya uymayan sayfada None doner - tahmin yurutulmez.
    """
    for i in range(len(satir) - 6):
        if satir[i + 1] != "add":
            continue
        fiyat = sayi_coz(satir[i + 3])
        if fiyat is None or satir[i + 4] not in OK_ISARET:
            continue
        yuzde = sayi_coz(satir[i + 5]) if "%" in satir[i + 5] else None
        if yuzde is not None and satir[i + 5].lstrip().startswith(("-", "\u2212")):
            yuzde = -abs(yuzde)
        fark = None
        for j in range(i + 6, min(i + 10, len(satir))):
            if re.fullmatch(r"[+\-\u2212][\d.,]+", satir[j]):
                fark = sayi_coz(satir[j].replace("\u2212", "-"))
                if satir[j].startswith(("-", "\u2212")):
                    fark = -abs(fark)
                break
        zaman = ""
        for j in range(i + 6, min(i + 12, len(satir))):
            if re.search(r"\d{1,2}:\d{2}", satir[j]):
                zaman = satir[j]
                break
        # Para birimi kodu zaman satirinin sonunda gecebiliyor: "... · USD"
        pb = ""
        m = re.search(r"[·|]\s*([A-Z]{3})\s*$", zaman)
        if m:
            pb = m.group(1)
        elif satir[i + 3].strip().startswith("$"):
            pb = "USD"
        elif satir[i + 3].strip().startswith("\u20ba"):
            pb = "TRY"
        # Onceki kapanis sayfada tek yerde gecer, kotasyon blogunun disinda.
        onceki = None
        for j, s in enumerate(satir):
            if s.startswith("Önc. kpş") and j + 1 < len(satir):
                onceki = sayi_coz(satir[j + 1])
                break
        return {"sembol": satir[i], "ad": satir[i + 2], "deger": fiyat,
                "yon_ham": satir[i + 4], "degisim_yuzde": yuzde,
                "degisim": fark, "zaman": zaman, "para_birimi": pb,
                "onceki": onceki}
    return None


def google_cek():
    """Google Finance'ten cekim. (kalemler, ek_bilgi) dondurur."""
    chrome = chrome_bul()
    if not chrome:
        raise ortak.CekmeHatasi(
            "Chrome bulunamadi; Google yolu bassiz tarayici ister "
            "(BH_CHROME ortam degiskeniyle yol verilebilir)")

    gelen = {}
    ek = {"chrome": chrome, "sembol": {}, "engel_izi": []}

    def bir_sembol(sembol):
        url = GOOGLE_ADRES % sembol
        try:
            dom = dom_al(chrome, url)
        except subprocess.TimeoutExpired:
            raise ortak.CekmeHatasi("Chrome %s icin zaman asimina ugradi" % sembol)
        if not dom.strip():
            raise ortak.CekmeHatasi("Chrome %s icin bos DOM dondurdu" % sembol)
        satir = dom_metne(dom)
        duz = " ".join(satir[:80])
        # Engelleme belirtisi: sessizce gecmeyelim, ciktiya yazalim.
        if re.search(r"unusual traffic|olağan dışı|not a robot|robot değil|"
                     r"recaptcha", duz, re.I) or "/sorry/" in dom[:6000]:
            ek["engel_izi"].append(sembol)
            raise _GoogleHatasi(
                "Google %s icin dogrulama istedi (CAPTCHA/engel)" % sembol, ek)
        if re.search(r"Sayfa Bulunamad|Page not found", duz, re.I):
            raise _GoogleHatasi("Google'da %s sembolu yok" % sembol, ek)
        k = google_kotasyon(satir)
        if not k:
            raise _GoogleHatasi(
                "Google %s sayfasinda kotasyon yapisi taninamadi "
                "(sayfa duzeni degismis olabilir)" % sembol, ek)
        ek["sembol"][sembol] = {"ad": k["ad"], "zaman": k["zaman"],
                                "para_birimi": k["para_birimi"]}
        return k

    for anahtar, sembol in GOOGLE_SEMBOL.items():
        k = bir_sembol(sembol)
        gelen[anahtar] = {
            "deger": k["deger"], "onceki": k["onceki"],
            "degisim": k["degisim"], "degisim_yuzde": k["degisim_yuzde"],
            "kaynak_durumu": "taze", "kaynak_zamani": k["zaman"],
            "kaynak_sembol": sembol,
        }
        ortak.bekle()

    # Altin: TRY cinsi kotasyon yok, USD/ons vadeli fiyattan HESAPLANIR.
    altin = bir_sembol(GOOGLE_ALTIN_SEMBOL)
    usd = gelen.get("dolar", {}).get("deger")
    if altin["deger"] and usd:
        gram = altin["deger"] * usd / ONS_GRAM
        gelen["gram_altin"] = {
            "deger": round(gram, 2), "onceki": None,
            "degisim": None, "degisim_yuzde": altin["degisim_yuzde"],
            "kaynak_durumu": "hesaplanan", "kaynak_zamani": altin["zaman"],
            "kaynak_sembol": GOOGLE_ALTIN_SEMBOL,
            "hesap": {
                "yontem": "ons_usd * usd_try / ons_gram",
                "ons_usd": altin["deger"],
                "ons_usd_kaynak": GOOGLE_ALTIN_SEMBOL + " (COMEX vadeli, spot değil)",
                "usd_try": usd,
                "usd_try_kaynak": "Google Finance USD-TRY",
                "ons_gram": ONS_GRAM,
                "sonuc_tl_gram": round(gram, 2),
                "uyari": ("Vadeli sözleşme fiyatından türetilmiş yaklaşık "
                          "paritedir; Kapalıçarşı gram altını bundan sapar. "
                          "Doğrudan kote eden bir kaynak varsa o kullanılır."),
            },
        }
        if altin["onceki"]:
            onceki_gram = altin["onceki"] * usd / ONS_GRAM
            gelen["gram_altin"]["onceki"] = round(onceki_gram, 2)
            gelen["gram_altin"]["degisim"] = round(gram - onceki_gram, 2)
    return gelen, ek


# -- kaynak 3: doviz.com (duz HTTP) ---------------------------------------

DOVIZ_ADRES = "https://www.doviz.com/"

# Sayfada her deger data-socket-key/data-socket-attr ciftiyle isaretli:
#   attr "s" son fiyat, "c" degisim yuzdesi, "a" degisim tutari.
DOVIZ_ANAHTAR = {"gram_altin": "gram-altin", "bist100": "XU100",
                 "dolar": "USD", "euro": "EUR", "sterlin": "GBP"}


def _socket_oku(ham: str, anahtar: str, attr: str):
    kalip = (r'data-socket-key="' + re.escape(anahtar) +
             r'"\s+data-socket-attr="' + attr + r'"[^>]*>\s*%?\s*([0-9.,\-]+)')
    m = re.search(kalip, ham)
    return sayi_coz(m.group(1)) if m else None


def doviz_cek():
    ham = ortak.getir(DOVIZ_ADRES)
    gelen = {}
    for kalem, anahtar in DOVIZ_ANAHTAR.items():
        deger = _socket_oku(ham, anahtar, "s")
        if deger is None:
            continue
        yuzde = _socket_oku(ham, anahtar, "c")
        fark = _socket_oku(ham, anahtar, "a")
        # Yon ayri bir sinifta ("status up"/"status down") veriliyor; yuzdenin
        # isareti metinde yok, bu yuzden sinifa bakilir.
        m = re.search(r'class="change-rate status (up|down)"\s+'
                      r'data-socket-key="' + re.escape(anahtar) + r'"', ham)
        if m and yuzde is not None:
            isaret = 1 if m.group(1) == "up" else -1
            yuzde = abs(yuzde) * isaret
            if fark is not None:
                fark = abs(fark) * isaret
        gelen[kalem] = {
            "deger": deger, "onceki": None, "degisim": fark,
            "degisim_yuzde": yuzde, "kaynak_durumu": "taze",
            "kaynak_zamani": "", "kaynak_sembol": anahtar,
        }
    if not gelen:
        raise ortak.CekmeHatasi(
            "doviz.com sayfasinda data-socket-key isaretleri bulunamadi "
            "(sayfa duzeni degismis olabilir)")
    return gelen, {"adres": DOVIZ_ADRES}


# -- kaynak 4: Mynet Finans (duz HTTP) ------------------------------------

MYNET_ADRES = "https://finans.mynet.com/borsa/endeks/xu100-bist-100/"

# Ust seritte dynamic-price-<KOD> / dynamic-direction-<KOD> siniflari var.
MYNET_ANAHTAR = {"gram_altin": "GAUTRY", "bist100": "XU100",
                 "dolar": "USDTRY", "euro": "EURTRY", "sterlin": "GBPTRY"}


def mynet_cek():
    ham = ortak.getir(MYNET_ADRES)
    gelen = {}
    for kalem, kod in MYNET_ANAHTAR.items():
        m = re.search(r'dynamic-price-' + kod + r'">\s*([0-9.,]+)\s*<', ham)
        if not m:
            continue
        y = re.search(r'dynamic-direction-' + kod + r'">\s*%?\s*([0-9.,]+)', ham)
        yuzde = sayi_coz(y.group(1)) if y else None
        # Yon ayri bir sinifta: change-up / change-down
        d = re.search(r'change-icon change-(up|down) '
                      r'dynamic-daily-direction-icon-' + kod, ham)
        if d and yuzde is not None:
            yuzde = abs(yuzde) * (1 if d.group(1) == "up" else -1)
        gelen[kalem] = {
            "deger": sayi_coz(m.group(1)), "onceki": None, "degisim": None,
            "degisim_yuzde": yuzde, "kaynak_durumu": "taze",
            "kaynak_zamani": "", "kaynak_sembol": kod,
        }
    if not gelen:
        raise ortak.CekmeHatasi(
            "Mynet seridinde dynamic-price isaretleri bulunamadi "
            "(sayfa duzeni degismis olabilir)")
    return gelen, {"adres": MYNET_ADRES}


CEKICI = {"evds": evds_cek, "google": google_cek, "doviz": doviz_cek,
          "mynet": mynet_cek}


# -- birlestirme ----------------------------------------------------------

# Bir kaydin ne kadar "iyi" oldugu. Buyuk olan kazanir; esitlikte kaynak
# sirasinda ONDE olan kalir.
#
#   4  resmi_kapanis, gozlemi BUGUNE ait    TCMB EVDS - o gunun nihai
#                                           kapanisi. Borsa kapandiktan
#                                           sonra bundan dogrusu yok.
#   3  taze                                 gun ici DOGRUDAN kotasyon
#                                           (doviz.com, Mynet, Google)
#   2  resmi_kapanis, gozlemi DAHA ESKI     EVDS'nin bir onceki is gunu
#                                           kapanisi. Resmidir ama gun
#                                           icinde bayattir; canli
#                                           kotasyon varsa o one gecer.
#   1  hesaplanan                           Google'in vadeli onstan
#                                           turettigi gram altin (%1,2
#                                           olculmus sapma)
#
# Neden 3 > 2: bant 15 dakikada bir yenileniyor ve gun icinde okunuyor.
# Dun kapanmis bir degeri "su anki fiyat" gibi gostermek yanlis olur.
# Neden 4 > 3: borsa kapandiktan sonra resmi kapanis nihai degerdir;
# canli kotasyon veren siteler o saatten sonra da oynayabiliyor.
KAYNAK_SIRA_PUANI = {"resmi_kapanis_bugun": 4, "taze": 3,
                     "resmi_kapanis": 2, "hesaplanan": 1}


def sira_puani(kayit: dict) -> int:
    durum = kayit.get("kaynak_durumu", "")
    if durum == "resmi_kapanis":
        bugun = datetime.now(ortak.TR_SAAT).strftime("%d-%m-%Y")
        if kayit.get("veri_tarihi") == bugun:
            return KAYNAK_SIRA_PUANI["resmi_kapanis_bugun"]
    return KAYNAK_SIRA_PUANI.get(durum, 0)


# Bu puani asan bir sey gelmez; bu esikteki kalem icin baska kaynak
# yoklanmaz (kaynaklara saygili hiz).
YETERLI_PUAN = KAYNAK_SIRA_PUANI["taze"]


def daha_iyi(yeni: dict, eski) -> bool:
    """Yeni kayit eldekinin yerini almali mi? (bkz. sira_puani)"""
    if eski is None:
        return True
    return sira_puani(yeni) > sira_puani(eski)


def tcmb_karsilastir(kok: Path, kalemler: list) -> dict:
    """Cekilen dolar/euro'yu TCMB bulteniyle karsilastirir.

    Amac dogrulama: kaynak sapmis mi, ayristirma kaymis mi burada gorulur.
    doviz.json yoksa sessizce atlanir; o dosyaya YAZILMAZ.
    """
    d = ortak.json_oku(kok / "doviz.json")
    if not d:
        return {"yapildi": False, "neden": "doviz.json yok"}
    tcmb = {k.get("anahtar"): k.get("deger") for k in d.get("kalemler", [])}
    cik = {"yapildi": True, "bulten": d.get("bulten", {}).get("tarih", ""),
           "karsilastirma": []}
    for k in kalemler:
        if k["anahtar"] not in ("dolar", "euro", "sterlin"):
            continue
        t = tcmb.get(k["anahtar"])
        if t is None or k["deger"] is None:
            continue
        sapma = (k["deger"] - t) / t * 100
        cik["karsilastirma"].append({
            "kalem": k["anahtar"], "piyasa": k["deger"], "tcmb": t,
            "sapma_yuzde": round(sapma, 3),
            # TCMB gunde bir sabit bulten yayimlar, piyasa gun ici hareket
            # eder. Bir gunluk hareket icin %1 makul bir tolerans.
            "tutuyor": abs(sapma) < 1.0,
        })
    return cik


def calistir(kok: Path, sira: list) -> int:
    cikti = kok / (BILESEN + ".json")
    basladi = time.time()

    toplanan = {}
    denenen = []
    kunyeler = []
    capraz = {}
    resmi_fark = []

    for kaynak in sira:
        # Her ASIL kalem icin daha iyisi gelemeyecek bir deger eldeyse
        # dur: gereksiz istek atma, kaynaklara saygili ol. EVDS'nin BAYAT
        # kapanisi (puan 2) bu esigi gecmez - gun ici canli kotasyon icin
        # sonraki kaynaklar yine denenir.
        if toplanan and all(sira_puani(toplanan.get(a, {})) >= YETERLI_PUAN
                            for a in ASIL_KALEM):
            denenen.append({"kaynak": kaynak, "sonuc": "atlandi",
                            "not": "asil kalemler yeterli kaynakla doldu"})
            continue
        t0 = time.time()
        try:
            gelen, ek = CEKICI[kaynak]()
        except ortak.CekmeHatasi as e:
            ortak.log("  %s: DÜŞTÜ — %s" % (kaynak, e))
            satir = {"kaynak": kaynak, "sonuc": "dustu", "hata": str(e),
                     "sure_sn": round(time.time() - t0, 1)}
            # Tanı bilgisi varsa kaydet: engel izi burada goruluyor.
            if getattr(e, "ek", None):
                satir["ek"] = e.ek
            denenen.append(satir)
            continue
        except Exception as e:  # ayristirma / beklenmedik
            ortak.log("  %s: DÜŞTÜ — %r" % (kaynak, e))
            denenen.append({"kaynak": kaynak, "sonuc": "dustu", "hata": repr(e),
                            "sure_sn": round(time.time() - t0, 1)})
            continue

        alinan = []
        for anahtar, kayit in gelen.items():
            if kayit.get("deger") is None:
                continue
            eldeki = toplanan.get(anahtar)
            # RESMI KAPANIS ile gun ici PIYASA kotasyonu arasindaki farki
            # olc. Yayina hangisi girerse girsin bu fark yazilir: TCMB'nin
            # resmi rakami ile bandin gosterdigi rakam arasinda ne kadar
            # acik oldugu okuyucudan da bizden de gizlenmemeli.
            if (eldeki and eldeki.get("kaynak_durumu") == "resmi_kapanis"
                    and kayit.get("kaynak_durumu") == "taze"):
                r, p = eldeki["deger"], kayit["deger"]
                resmi_fark.append({
                    "kalem": anahtar,
                    "resmi_kapanis": r,
                    "resmi_kaynak": eldeki.get("kaynak", ""),
                    "resmi_seri": eldeki.get("kaynak_sembol", ""),
                    "resmi_tarih": eldeki.get("veri_tarihi", ""),
                    "piyasa": p, "piyasa_kaynak": kaynak,
                    "sapma_yuzde": round((p - r) / r * 100, 2) if r else None,
                    "yayina_giden": ("piyasa" if daha_iyi(kayit, eldeki)
                                     else "resmi_kapanis"),
                })
            # Hesaplanan altin ile dogrudan kotasyon arasindaki farki OLC -
            # ikisi de eldeyse bu bir capraz kontroldur, gizlenmez.
            if (anahtar == "gram_altin" and eldeki
                    and eldeki.get("kaynak_durumu") == "hesaplanan"
                    and kayit.get("kaynak_durumu") == "taze"):
                h, g = eldeki["deger"], kayit["deger"]
                capraz["gram_altin"] = {
                    "hesaplanan": h, "hesaplayan_kaynak": eldeki.get("kaynak", ""),
                    "dogrudan": g, "dogrudan_kaynak": kaynak,
                    "sapma_yuzde": round((h - g) / g * 100, 2),
                    "yayina_giden": "dogrudan",
                }
            if daha_iyi(kayit, eldeki):
                kayit["kaynak"] = kaynak
                toplanan[anahtar] = kayit
                alinan.append(anahtar)

        kunyeler.append(dict(KAYNAK_KUNYE[kaynak], anahtar=kaynak))
        kayit_satiri = {"kaynak": kaynak, "sonuc": "tamam", "alinan": alinan,
                        "sure_sn": round(time.time() - t0, 1)}
        if kaynak in ("google", "evds"):
            kayit_satiri["ek"] = ek
        denenen.append(kayit_satiri)
        ortak.log("  %s: %d kalem (%s) %.1f sn"
                  % (kaynak, len(alinan), ", ".join(alinan) or "—",
                     time.time() - t0))

    # Asil kalemlerin hicbiri gelmediyse bu bir DUSMEDIR: eldeki dosyaya
    # dokunulmaz, durum dosyasi yazilir, cikis kodu 2 ya da 1 olur.
    if not any(toplanan.get(a, {}).get("deger") is not None for a in ASIL_KALEM):
        hatalar = "; ".join("%s: %s" % (d["kaynak"], d.get("hata", d["sonuc"]))
                            for d in denenen)
        return ortak.dusme_ile_bitir(
            kok, BILESEN, cikti, "hicbir kaynaktan veri alinamadi (%s)" % hatalar)

    kalemler = []
    for t in KALEMLER:
        kayit = {"anahtar": t["anahtar"], "ad": t["ad"], "birim": t["birim"],
                 "rol": "yayin" if t["asil"] else "dogrulama",
                 "deger": None, "onceki": None, "degisim": None,
                 "degisim_yuzde": None, "yon": "", "kaynak": "",
                 "kaynak_durumu": "yok"}
        g = toplanan.get(t["anahtar"])
        if g:
            kayit.update(g)
            y = kayit.get("degisim_yuzde")
            kayit["yon"] = ("yukari" if (y or 0) > 0
                            else ("asagi" if (y or 0) < 0 else "esit"))
        kalemler.append(kayit)

    veri = {
        "_not": ("Gram altın ve BIST 100 için dört kaynak sırayla denenir: "
                 "TCMB EVDS (resmi kapanış), Google Finance (başsız Chrome), "
                 "doviz.com, Mynet Finans. Hangi kalemin hangi kaynaktan "
                 "geldiği kalem başına yazılır. EVDS resmî kapanış verir, "
                 "gün içi fiyat vermez: gün içinde canlı kotasyon öne geçer, "
                 "kapanış o güne aitse EVDS öne geçer (kaynak_durumu alanı "
                 "ve capraz_kontrol.resmi_kapanis_piyasa_farki bunu gösterir). "
                 "Dolar ve euro yayın için değil, TCMB kuruyla karşılaştırıp "
                 "kaynağı doğrulamak için çekilir. Değer uydurulmaz."),
        "guncelleme": ortak.simdi(),
        "bayat_esik_dakika": BAYAT_ESIK_DAKIKA,
        "kaynak_sirasi": sira,
        "kaynak": kunyeler,
        "denenen_kaynaklar": denenen,
        "kalemler": kalemler,
        "gram_altin_cevrimi": {
            "birim": "TL / gram",
            "ons_gram": ONS_GRAM,
            "not": ("Doğrudan kote eden kaynak varsa çevrim YAPILMAZ. Yalnız "
                    "Google yolunda gerekir: Google'da TRY cinsi altın "
                    "kotasyonu yoktur, COMEX vadeli ons fiyatından "
                    "ons_usd * usd_try / 31,1034768 ile hesaplanır ve "
                    "'hesaplanan' damgasıyla işaretlenir."),
        },
        "capraz_kontrol": dict(
            {"tcmb": tcmb_karsilastir(kok, kalemler),
             "resmi_kapanis_piyasa_farki": resmi_fark},
            **capraz),
        "denetim": {
            "kalem": len(kalemler),
            "dolu": sum(1 for k in kalemler if k["deger"] is not None),
            "asil_kalem_dolu": sum(1 for k in kalemler
                                   if k["anahtar"] in ASIL_KALEM
                                   and k["deger"] is not None),
            "hesaplanan": [k["anahtar"] for k in kalemler
                           if k["kaynak_durumu"] == "hesaplanan"],
            "resmi_kapanis": [k["anahtar"] for k in kalemler
                              if k["kaynak_durumu"] == "resmi_kapanis"],
            "bos": [k["anahtar"] for k in kalemler if k["deger"] is None],
            "kaynak_dagilimi": dict((k["anahtar"], k["kaynak"])
                                    for k in kalemler if k["kaynak"]),
            "google_engel_izi": [i for d in denenen
                                 for i in d.get("ek", {}).get("engel_izi", [])],
            "toplam_sure_sn": round(time.time() - basladi, 1),
        },
    }

    ortak.json_yaz(cikti, veri)
    ortak.durum_yaz(kok, BILESEN, "taze")

    for k in kalemler:
        if k["deger"] is None:
            ortak.log("    %-12s —  (alınamadı)" % k["ad"])
        else:
            yuzde = ("" if k["degisim_yuzde"] is None
                     else " %+.2f%%" % k["degisim_yuzde"])
            ortak.log("    %-12s %s%s  [%s · %s]"
                      % (k["ad"], k["deger"], yuzde, k["kaynak"],
                         k["kaynak_durumu"]))
    ortak.log("Bitti: %d/%d kalem, %s sn -> %s"
              % (veri["denetim"]["dolu"], len(kalemler),
                 veri["denetim"]["toplam_sure_sn"], cikti))
    return 0


# -- akis -----------------------------------------------------------------

def main() -> int:
    ayristi = argparse.ArgumentParser(
        description="Gram altın ve BIST 100'ü çeker (TCMB EVDS + yedekler).")
    ayristi.add_argument("--kok", default=None,
                         help="cikti koku (ortam degiskeni: BH_CANLI_KOK)")
    ayristi.add_argument("--kaynak", nargs="+", default=VARSAYILAN_SIRA,
                         choices=list(CEKICI),
                         help="denenecek kaynaklar, sirayla "
                              "(varsayilan: evds google doviz mynet)")
    ayristi.add_argument("--surekli", type=int, metavar="DAKIKA", default=0,
                         help="verilirse betik durmaz, her DAKIKA'da bir "
                              "yeniden ceker (ornek: --surekli 15)")
    arg = ayristi.parse_args()

    kok = ortak.kok_coz(arg.kok)
    ortak.log_kur(kok, BILESEN)

    if not arg.surekli:
        ortak.log("Piyasa çekiliyor (%s) -> %s" % (" > ".join(arg.kaynak), kok))
        return calistir(kok, arg.kaynak)

    # Surekli kip. Sunucuda Gorev Zamanlayici tercih edilir - betik cokerse
    # onu yeniden baslatan bir sey olmali. Bu kip gelistirme ve tek makinede
    # elle calistirma icindir.
    ortak.log("Sürekli kip: her %d dakikada bir (%s) -> %s"
              % (arg.surekli, " > ".join(arg.kaynak), kok))
    son = 0
    try:
        while True:
            basladi = time.time()
            try:
                son = calistir(kok, arg.kaynak)
            except Exception as e:  # dongu tek bir hatada olmemeli
                ortak.log("HATA (döngü sürüyor): %r" % (e,))
                son = 1
            kalan = arg.surekli * 60 - (time.time() - basladi)
            if kalan > 0:
                ortak.log("  sonraki koşuya %.1f dk" % (kalan / 60))
                time.sleep(kalan)
    except KeyboardInterrupt:
        ortak.log("Sürekli kip durduruldu.")
    return son


if __name__ == "__main__":
    raise SystemExit(main())
