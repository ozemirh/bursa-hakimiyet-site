"""Anasayfadaki doviz bandinin bes kalemini ceker.

Bilesen sozlesmesi (URUN-PLANI.md bolum 1, madde 9) tam bes kalem istiyor:
Dolar - Euro - Sterlin - Gram altin - BIST 100.

Kaynak durumu KALEM BASINA farklidir; bu betigin en onemli davranisi budur:

  Dolar / Euro / Sterlin  TCMB gunluk kur bulteni (resmi, ucretsiz, anahtarsiz).
  Gram altin / BIST 100   Bu betik cekmez; piyasa.py ceker ve piyasa.json'a
                          yazar, buradan okunur. Orada da bulunamazsa
                          <kok>/doviz-elle.json okunur, o da yoksa deger null
                          kalir ve sayfa o iki kutuyu gizler. UYDURULMAZ.

Neden gram altin ve BIST 100 icin kaynak yok (26-27 Agustos 2026 olcumu):

  Borsa Istanbul   Endeks ve kiymetli maden verisi DataStore uzerinden
                   satiliyor; acik sayfalarda gunluk deger yok (olculdu:
                   borsaistanbul.com/en/index/xu100 sayfasinda endeks
                   tanimi var, degeri yok).
  TCMB EVDS        COZULDU (27 Agustos 2026). Anahtar GEREKMIYOR: eski
                   /service/evds/ ucu olmus (her istege SPA kabugu doner)
                   ama EVDS arayuzunun kendi ucu anahtarsiz calisiyor.
                   Gram altin ve BIST 100 artik oradan geliyor - ayrinti
                   ve seri kodlari piyasa.py'nin "kaynak 1" bolumunde.
                   Not: EVDS gun ici fiyat degil KAPANIS verir.
  stooq.com        robots.txt yalnizca Googlebot ve Bingbot'a izin veriyor,
                   "User-agent: * Disallow: /". Elendi.
  Yahoo Finance    query1.finance.yahoo.com/robots.txt "Disallow: /". Elendi.
  LBMA             prices.lbma.org.uk kimlik dogrulama istiyor (401).

Kullanim:
    python doviz.py
    python doviz.py --kok D:/canli

Cikti: <kok>/doviz.json ve <kok>/durum-doviz.json

Cikis kodu: 0 taze veri - 2 cekilemedi, onceki dosya korundu -
1 cekilemedi ve elde onceki veri de yok.

Dolar/euro icin neden EVDS'ye GECILMEDI (olculdu, 27 Agustos 2026):

EVDS'nin gosterge ucu (/sk-seriler) dolar ve euroyu "27-08-2026" tarihiyle
verirken today.xml hala 26.08.2026 bultenini gosteriyordu; ilk bakista
EVDS daha tazeymis gibi duruyor. DEGIL. EVDS her bulteni BIR SONRAKI is
gunuyle etiketliyor - ayni sayilar, kaydirilmis tarih:

    bulten 24.08.2026 (2026/157) EfektifAlis 47,9588  ->  EVDS satiri 25-08
    bulten 25.08.2026 (2026/158) EfektifAlis 47,9781  ->  EVDS satiri 26-08
    bulten 26.08.2026 (2026/159) EfektifAlis 47,9955  ->  EVDS satiri 27-08

Yani EVDS'nin "bugunku" dedigi rakam, bu betigin today.xml'den zaten
okudugu rakamin ta kendisi. Kazanc sifir, uc kayip var: (1) EVDS'nin
gosterge ucu EFEKTIF ALIS veriyor, bu betik ise bilerek DOVIZ ALIS/SATIS
kullaniyor (bkz. asagisi) - farkli kur; (2) bantta gosterilen bulten
tarihi/numarasi bir gun kayardi; (3) today.xml duz bir XML, digeri bir
SPA'nin arkasindaki uc. Konu kapali: kur tarafi today.xml'de kalir.

TCMB Kullanim Sartlari (olculdu, 27 Agustos 2026):

    "Sitede yer alan bilgiler, kaynak gosterilmek suretiyle yayimlanabilir;
     ancak bu bilgilerin ticari amaclarla kullanimi TCMB'nin yazili iznine
     tabidir."

Gazete ticari bir yayindir. Bu madde TFF'nin ayni bicimdeki maddesiyle
birlikte HUKUK TEYIDINE gitmeli (URUN-PLANI.md bolum 8). Betik kaynagi
ciktiya yazar; sayfada "Kaynak: TCMB" gorunmelidir.
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ortak  # noqa: E402

BILESEN = "doviz"

TCMB_BUGUN = "https://www.tcmb.gov.tr/kurlar/today.xml"
TCMB_GUN = "https://www.tcmb.gov.tr/kurlar/%s/%s.xml"  # YYYYAA / GGAAYYYY

# Kur gunde bir kez (is gunu 15:30) aciklanir. Bir gunluk gecikme sonrasi
# bant "guncel degil" demeli. Hafta sonu ve bayramda TCMB yeni bulten
# yayimlamaz; o gunlerde betik yine calisir, bulten tarihi eski kalir ve
# bunu "bulten" blogu soyler - bayatlik olcusu bizim CEKME animizdir.
BAYAT_ESIK_DAKIKA = 1440  # 24 saat

# Bandin sirasi URUN-PLANI.md bolum 1 madde 9'dan gelir; degistirilmez.
KALEMLER = [
    {"anahtar": "dolar", "ad": "Dolar", "kod": "USD", "birim": "TL"},
    {"anahtar": "euro", "ad": "Euro", "kod": "EUR", "birim": "TL"},
    {"anahtar": "sterlin", "ad": "Sterlin", "kod": "GBP", "birim": "TL"},
    {"anahtar": "gram_altin", "ad": "Gram altın", "kod": None, "birim": "TL"},
    {"anahtar": "bist100", "ad": "BIST 100", "kod": None, "birim": "puan"},
]

KAYNAKSIZ_NOT = ("Ücretsiz ve kullanım şartları uygun bir kaynak bulunamadı; "
                 "değer panelden elle girilir (doviz-elle.json).")

ELLE_DOSYA = "doviz-elle.json"

# 27 Agustos 2026: gram altin ve BIST 100 icin kaynak BULUNDU. Cekme isini
# piyasa.py yapar (TCMB EVDS + Google Finance + doviz.com + Mynet, 15
# dakikada bir) ve
# sonucu piyasa.json'a yazar. Burasi yalnizca o dosyayi OKUR. TCMB mantigi
# degismedi; dolar/euro/sterlin eskisi gibi bultenden gelir.
PIYASA_DOSYA = "piyasa.json"


# -- TCMB ayristirma ------------------------------------------------------

def bulten_ayikla(xml_metin: str) -> tuple[dict, dict]:
    """TCMB gunluk bultenini (kod -> kur) sozlugune ve bulten kunyesine ayirir.

    Doviz alis/satis (ForexBuying/ForexSelling) alinir; banknot kuru degil.
    Gazete bandinda gosterilen deger doviz satis kurudur.
    """
    kok = ET.fromstring(xml_metin)
    kunye = {
        "tarih": kok.get("Tarih", ""),
        "tarih_iso": _iso(kok.get("Tarih", "")),
        "no": (kok.get("Bulten_No") or "").strip(),
    }
    kurlar = {}
    for para in kok.findall("Currency"):
        kod = para.get("Kod") or para.get("CurrencyCode")
        if not kod:
            continue
        kurlar[kod] = {
            "isim": (para.findtext("Isim") or "").strip(),
            "birim": _sayi(para.findtext("Unit")),
            "alis": _sayi(para.findtext("ForexBuying")),
            "satis": _sayi(para.findtext("ForexSelling")),
        }
    return kurlar, kunye


def _sayi(deger):
    if deger is None:
        return None
    d = deger.strip().replace(",", ".")
    if not d:
        return None
    try:
        return float(d) if "." in d else int(d)
    except ValueError:
        return None


def _iso(tarih: str) -> str:
    """TCMB'nin '26.08.2026' bicimini ISO'ya cevirir; cozemezse bos doner."""
    parca = tarih.split(".")
    if len(parca) != 3:
        return ""
    try:
        return date(int(parca[2]), int(parca[1]), int(parca[0])).isoformat()
    except ValueError:
        return ""


def onceki_bulteni_bul(bulten_tarihi: str, geriye: int = 7):
    """Bir onceki is gununun bultenini arar; yoksa (None, '') doner.

    TCMB hafta sonu ve resmi tatilde dosya yayimlamaz, bu yuzden gun gun
    geriye gidilir. Bulunamazsa degisim hesabi atlanir - uydurulmaz.
    """
    iso = _iso(bulten_tarihi)
    if not iso:
        return None, ""
    g = date.fromisoformat(iso)
    for _ in range(geriye):
        g -= timedelta(days=1)
        if g.weekday() >= 5:  # cumartesi/pazar: dosya yok, istek bile atma
            continue
        adres = TCMB_GUN % (f"{g.year}{g.month:02d}", f"{g.day:02d}{g.month:02d}{g.year}")
        try:
            ham = ortak.getir(adres)
        except ortak.CekmeHatasi:
            continue
        try:
            kurlar, _ = bulten_ayikla(ham)
        except ET.ParseError:
            continue
        if kurlar:
            return kurlar, g.isoformat()
        ortak.bekle()
    return None, ""


# -- kalem kurma ----------------------------------------------------------

def kalem_kur(tanim: dict, kurlar: dict, onceki: dict | None) -> dict:
    kayit = {
        "anahtar": tanim["anahtar"],
        "ad": tanim["ad"],
        "birim": tanim["birim"],
        "deger": None,
        "alis": None,
        "satis": None,
        "onceki": None,
        "degisim": None,
        "degisim_yuzde": None,
        "yon": "",
        "kaynak": "",
        "kaynak_durumu": "yok",
    }
    kur = kurlar.get(tanim["kod"]) if tanim["kod"] else None
    if not kur or kur.get("satis") is None:
        kayit["not"] = KAYNAKSIZ_NOT
        return kayit

    kayit.update({
        "deger": kur["satis"],
        "alis": kur["alis"],
        "satis": kur["satis"],
        "kaynak": "TCMB",
        "kaynak_durumu": "taze",
    })
    if kur.get("birim") and kur["birim"] != 1:
        kayit["birim_carpani"] = kur["birim"]

    eski = (onceki or {}).get(tanim["kod"]) or {}
    if eski.get("satis"):
        fark = kur["satis"] - eski["satis"]
        kayit["onceki"] = eski["satis"]
        kayit["degisim"] = round(fark, 4)
        kayit["degisim_yuzde"] = round(fark / eski["satis"] * 100, 2)
        kayit["yon"] = "yukari" if fark > 0 else ("asagi" if fark < 0 else "esit")
    return kayit


def piyasadan_yerlestir(kalemler: list[dict], kok: Path) -> int:
    """Kaynagi TCMB olmayan kalemleri piyasa.json'dan doldurur.

    piyasa.py gram altin ve BIST 100'u ceker; bu betik onun yazdigi dosyayi
    okur. Dosya yoksa ya da bayatsa hicbir sey yapilmaz - kalemler null
    kalir ve elle giris yolu devreye girer. UYDURULMAZ.

    Bayatlik kontrolu burada ayrica yapilir cunku piyasa.py cok daha sik
    kosar (15 dk) ve durmus bir zamanlayici en once burada gorulur.
    """
    p = ortak.json_oku(kok / PIYASA_DOSYA)
    if not p:
        return 0
    yas = ortak.yas_dakika(p.get("guncelleme", ""))
    esik = p.get("bayat_esik_dakika", 45)
    if yas is None or yas > esik:
        ortak.log(f"  UYARI: {PIYASA_DOSYA} bayat "
                  f"({'yaş çözülemedi' if yas is None else f'{yas:.0f} dk > {esik} dk'})"
                  ", gram altın/BIST 100 boş bırakıldı")
        return 0

    piyasa = {k.get("anahtar"): k for k in p.get("kalemler", [])}
    dolan = 0
    for k in kalemler:
        # 27 Agustos karari: BANTTA CANLI KUR GOSTERILIR.
        #
        # Eskiden dolar/euro/sterlin yalniz TCMB bulteninden geliyordu ve
        # bulten gunde BIR kez (is gunu ~15:30) yayimlaniyor. Bandda gun
        # boyu dunku rakam duruyordu; okur baska yerde guncel kuru gorup
        # bizimkini bayat buluyor. Serbest piyasa kuru surekli hareket
        # eder ve gazetelerin bandinda gosterdigi de odur - bandin etiketi
        # zaten "PIYASA".
        #
        # TCMB kuru KAYBOLMUYOR: resmi referans olarak kayitta duruyor
        # (`tcmb_resmi` alani) ve canli kaynaklarin hepsi dustugunde
        # bandda o gosteriliyor. Muhasebe/hukuk icin gecerli kur odur.
        canli = piyasa.get(k["anahtar"])
        if (k["kaynak_durumu"] != "yok" and canli
                and canli.get("deger") is not None
                and canli.get("kaynak_durumu") == "taze"):
            k["tcmb_resmi"] = {"deger": k.get("deger"), "alis": k.get("alis"),
                               "satis": k.get("satis"),
                               "bulten": p.get("bulten") or None}
            k["kaynak_durumu"] = "yok"   # asagidaki blok canliyla doldursun
        if k["kaynak_durumu"] != "yok":
            continue
        g = piyasa.get(k["anahtar"])
        if not g or g.get("deger") is None:
            continue
        k["deger"] = g["deger"]
        k["onceki"] = g.get("onceki")
        k["degisim"] = g.get("degisim")
        k["degisim_yuzde"] = g.get("degisim_yuzde")
        k["yon"] = g.get("yon", "")
        k["kaynak"] = g.get("kaynak", "")
        # "taze"          gun ici dogrudan kotasyon
        # "resmi_kapanis"  TCMB EVDS - o gunun ya da bir onceki is gununun
        #                  RESMI KAPANISI; gun ici fiyat degil
        # "hesaplanan"     ons pariteden turetilmis yaklasik deger
        # Ayrimi tasi ki sayfa gerekirse uyari basabilsin.
        k["kaynak_durumu"] = g.get("kaynak_durumu", "taze")
        # Kapanis degeri yayina girdiyse HANGI GUNUN kapanisi oldugu
        # yazilmali; sayfa "26 Agustos kapanisi" diyebilsin diye tasiniyor.
        if g.get("veri_tarihi"):
            k["veri_tarihi"] = g["veri_tarihi"]
        k["piyasa_damgasi"] = p.get("guncelleme", "")
        if g.get("hesap"):
            k["hesap"] = g["hesap"]
        k.pop("not", None)
        dolan += 1
    return dolan


def elle_gireni_yerlestir(kalemler: list[dict], kok: Path) -> int:
    """Kaynagi olmayan kalemleri panelden girilen dosyadan doldurur.

    Bicim:
      {"gram_altin": {"deger": 5432.1, "kaynak": "Kuyumcu ortalaması",
                      "tarih": "2026-08-27"},
       "bist100":    {"deger": 11234.56, "kaynak": "...", "tarih": "..."}}

    Dosya yoksa hicbir sey yapilmaz; kalemler null kalir.
    """
    elle = ortak.json_oku(kok / ELLE_DOSYA)
    if not elle:
        return 0
    dolan = 0
    for k in kalemler:
        if k["kaynak_durumu"] != "yok":
            continue
        girdi = elle.get(k["anahtar"])
        if not isinstance(girdi, dict) or girdi.get("deger") is None:
            continue
        k["deger"] = girdi["deger"]
        k["kaynak"] = girdi.get("kaynak", "Elle giriş")
        k["kaynak_durumu"] = "elle"
        k["girildi"] = girdi.get("tarih", "")
        if girdi.get("onceki"):
            fark = k["deger"] - girdi["onceki"]
            k["onceki"] = girdi["onceki"]
            k["degisim"] = round(fark, 4)
            k["degisim_yuzde"] = round(fark / girdi["onceki"] * 100, 2)
            k["yon"] = "yukari" if fark > 0 else ("asagi" if fark < 0 else "esit")
        k.pop("not", None)
        dolan += 1
    return dolan


# -- akis -----------------------------------------------------------------

def calistir(kok: Path) -> int:
    cikti = kok / f"{BILESEN}.json"
    try:
        ortak.log(f"  TCMB: {TCMB_BUGUN}")
        ham = ortak.getir(TCMB_BUGUN)
        kurlar, kunye = bulten_ayikla(ham)
    except ortak.CekmeHatasi as e:
        return ortak.dusme_ile_bitir(kok, BILESEN, cikti, str(e))
    except ET.ParseError as e:
        return ortak.dusme_ile_bitir(
            kok, BILESEN, cikti, f"TCMB bulteni cozulemedi: {e}")

    eksik = [t["kod"] for t in KALEMLER if t["kod"] and t["kod"] not in kurlar]
    if eksik:
        return ortak.dusme_ile_bitir(
            kok, BILESEN, cikti,
            "TCMB bulteninde su kodlar yok: " + ", ".join(eksik))

    ortak.log(f"  Bülten {kunye['no']} / {kunye['tarih']}, "
              f"{len(kurlar)} para birimi")

    ortak.bekle()
    onceki, onceki_tarih = onceki_bulteni_bul(kunye["tarih"])
    if onceki:
        ortak.log(f"  Önceki bülten: {onceki_tarih} (değişim hesaplandı)")
    else:
        ortak.log("  UYARI: önceki bülten bulunamadı, değişim boş kalacak")

    kalemler = [kalem_kur(t, kurlar, onceki) for t in KALEMLER]
    # TCMB'den gercekten geleni burada say: asagidaki doldurmalar da
    # kaynak_durumu'nu "taze" yapiyor, sonradan sayilirsa TCMB'ye mal edilir.
    tcmb_gelen = [k["anahtar"] for k in kalemler if k["kaynak_durumu"] == "taze"]
    # Once otomatik kaynak (piyasa.py), sonra elle giris. Sira boyle cunku
    # elle giris SON CARE: otomatik kaynak calisiyorken panelde unutulmus
    # eski bir deger yayina gitmemeli.
    piyasa_dolan = piyasadan_yerlestir(kalemler, kok)
    if piyasa_dolan:
        ortak.log(f"  {piyasa_dolan} kalem {PIYASA_DOSYA} dosyasından dolduruldu")
    elle_dolan = elle_gireni_yerlestir(kalemler, kok)
    if elle_dolan:
        ortak.log(f"  {elle_dolan} kalem {ELLE_DOSYA} dosyasından dolduruldu")

    kaynaksiz = [k["anahtar"] for k in kalemler if k["kaynak_durumu"] == "yok"]

    veri = {
        "_not": ("Dolar, euro ve sterlin TCMB'nin açık günlük kur "
                 "bülteninden çekildi. Gram altın ve BIST 100 TCMB'de yok; "
                 "onları piyasa.py çeker (TCMB EVDS · Google Finance · "
                 "doviz.com · Mynet) "
                 "ve bu betik piyasa.json'dan okur. O dosya yoksa ya da "
                 "bayatsa panelden elle giriş devreye girer; hiçbir koşulda "
                 "değer uydurulmaz. Yayınlanırken her kalemin kaynağı "
                 "belirtilir."),
        "guncelleme": ortak.simdi(),
        "bayat_esik_dakika": BAYAT_ESIK_DAKIKA,
        "kaynak": {
            "ad": "Türkiye Cumhuriyet Merkez Bankası",
            "kisa": "TCMB",
            "adres": "https://www.tcmb.gov.tr/kurlar/today.xml",
            "kosullar": ("https://www.tcmb.gov.tr/wps/wcm/connect/TR/TCMB+TR/"
                         "Bottom+Menu/Diger/Kullanim+Sartlari"),
            "kunye": "Kaynak: TCMB döviz kurları.",
        },
        "bulten": kunye,
        "onceki_bulten": onceki_tarih,
        "kalemler": kalemler,
        "denetim": {
            "kalem": len(kalemler),
            "kaynaktan_gelen": len(tcmb_gelen),
            "piyasadan_gelen": piyasa_dolan,
            "elle_girilen": elle_dolan,
            "kaynagi_olmayan": kaynaksiz,
            "kaynak_dagilimi": {k["anahtar"]: (k["kaynak"] or "—")
                                for k in kalemler},
        },
    }

    ortak.json_yaz(cikti, veri)
    ortak.durum_yaz(kok, BILESEN, "taze")

    for k in kalemler:
        if k["deger"] is None:
            ortak.log(f"    {k['ad']:12s} —  (kaynak yok)")
        else:
            yuzde = (f" {k['degisim_yuzde']:+.2f}%"
                     if k["degisim_yuzde"] is not None else "")
            ortak.log(f"    {k['ad']:12s} {k['deger']}{yuzde}"
                      f"  [{k['kaynak_durumu']}]")
    # Sayimi YAYINA GIREN degerden yap. Eskiden TCMB'den okunan kalemler
    # canli deger onlari ezse bile sayiliyordu ve toplam kalem sayisini
    # asiyordu ("3 TCMB'den, 5 piyasa'dan (toplam 5)").
    from collections import Counter
    dagilim = Counter(k.get("kaynak") or "-" for k in kalemler
                      if k.get("deger") is not None)
    ozet = " · ".join(f"{n} {ad}" for ad, n in dagilim.most_common())
    ortak.log(f"Bitti: {sum(dagilim.values())}/{len(kalemler)} kalem "
              f"({ozet}) -> {cikti}")
    return 0


def main() -> int:
    ayristi = argparse.ArgumentParser(
        description="Döviz bandının beş kalemini çeker (TCMB + elle giriş).")
    ayristi.add_argument("--kok", default=None,
                         help="cikti koku (ortam degiskeni: BH_CANLI_KOK)")
    arg = ayristi.parse_args()

    kok = ortak.kok_coz(arg.kok)
    ortak.log_kur(kok, BILESEN)
    ortak.log(f"Döviz bandı çekiliyor -> {kok}")
    return calistir(kok)


if __name__ == "__main__":
    raise SystemExit(main())
