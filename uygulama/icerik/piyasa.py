"""Kalıcı enstrüman sayfaları — `/piyasa/dolar` · `/piyasa/euro` · `/piyasa/gram-altin`.

20 Ekim 2026 (ekonomi özel tasarımının parçası, P1). "Dolar kaç TL" diye
arayan okurun iniş adresi. Desen referans kütüphanesinden
(`desenler/ekonomi-sayfasi.md`): şerit kalemi → kalıcı enstrüman sayfası;
rakamın güveni **kaynak + zaman + gecikme** notundan gelir.

## Veri — yeni model yok

Sayfa `canli-veri/` betiklerinin yazdığı dosyaları okur, kendisi hiçbir şey
yazmaz (betik yazar, site okur — `icerik/canli.py`):

* `doviz.json` — sayfanın **tek doğruluk kaynağı**. Kalemin `deger`i
  yayına giden değerdir (canlı piyasa kotasyonu ya da TCMB bülteni; hangisi
  olduğu `kaynak` alanında). `alis`/`satis` YALNIZ TCMB'den gelir: canlı
  değer `deger`i ezdiğinde de iki alan TCMB bülteninin kurlarıdır
  (`canli-veri/doviz.py`, `piyasadan_yerlestir`).
* `piyasa.json` — yalnız iki şey için: koşuda kullanılan kaynakların okunur
  adları (`kaynak` listesi) ve gram altının TCMB EVDS resmî kapanışı
  (`capraz_kontrol.resmi_kapanis_piyasa_farki`).

Bayatlık tek yerden (`canli.tazelik`, `oku()` onu `veri["tazelik"]` olarak
iliştirir): bayat veri GİZLENMEZ, tarihiyle ve "güncel değil" uyarısıyla
basılır (19 Ekim 2026 akşamı kullanıcı kararı).

## Kaynakta olmayan alan çizilmez

Alış/satış yalnız TCMB'nin verdiği kalemde; en yüksek/en düşük hiçbir
kaynakta yok; değişim kaynak vermediyse yok. Şablon boş alanı "–" diye bile
basmaz — satır hiç yoktur.

## Geçmiş — sözleşme var, yazan betik yok (20 Ekim 2026)

Betikler bugün geçmiş seri YAZMIYOR. Sayfa, kalem şu iki alanı taşırsa
tabloyu ve çizgi grafiği çizer, taşımazsa bölüm hiç yoktur:

    "gecmis": [{"tarih": "2026-09-11", "deger": 48.5178}, ...]
    "gecmis_kaynak": "TCMB günlük bülten (döviz satış)"

`gecmis_kaynak` ZORUNLU: kaynağı yazılmamış seri basılmaz. Tarih ISO
(`YYYY-AA-GG`) ya da EVDS biçimi (`GG-AA-YYYY`). Sözleşme
`canli-veri/README.md` "Enstrüman sayfaları" bölümünde de yazılı.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime

from django.utils import formats, timezone

# Tablodaki en yeni gözlem sayısı ve grafiğin taşıdığı en çok gözlem.
GECMIS_TABLO = 10
GECMIS_GRAFIK = 30


@dataclass(frozen=True)
class Enstruman:
    slug: str          # adres dilimi: /piyasa/<slug>
    anahtar: str       # `doviz.json` kalem anahtarı
    ad: str            # "Dolar"
    tam_ad: str        # alt başlık
    soru: str          # h1 — aramanın kendisi
    seo_baslik: str    # <title> gövdesi (site adı şablonda eklenir)
    birim: str         # çeviricide birim adı
    ondalik: int       # TCMB 4 hane verir; gram altın 2
    oran: str          # grafik/tablo başlığı: "USD/TL"


ENSTRUMANLAR: dict[str, Enstruman] = {e.slug: e for e in (
    Enstruman("dolar", "dolar", "Dolar", "ABD doları — Türk lirası karşılığı",
              "Dolar kaç TL?", "Dolar kaç TL? Dolar kuru, TCMB alış-satış ve çevirici",
              "dolar", 4, "USD/TL"),
    Enstruman("euro", "euro", "Euro", "Euro — Türk lirası karşılığı",
              "Euro kaç TL?", "Euro kaç TL? Euro kuru, TCMB alış-satış ve çevirici",
              "euro", 4, "EUR/TL"),
    Enstruman("gram-altin", "gram_altin", "Gram altın", "Bir gram altının Türk lirası karşılığı",
              "Gram altın kaç TL?", "Gram altın kaç TL? Gram altın fiyatı ve çevirici",
              "gram", 2, "TL/gram"),
)}

_ANAHTARDAN = {e.anahtar: e for e in ENSTRUMANLAR.values()}

#: Kök adres tablosundaki kalıbın seçenekleri. Açık liste: `/piyasa/<x>`
#: biçimindeki başka hiçbir adres bu görünüme düşmez (haber kalıbı
#: `/{kategori}/{slug}-{id}` sondaki sayıyı ister; buradaki adların hiçbiri
#: sayıyla bitmez — çakışma yok).
ADRES_KALIBI = "|".join(re.escape(s) for s in ENSTRUMANLAR)

# Kaynak kısa adlarının okunur karşılığı. İlk tercih `piyasa.json`un kendi
# `kaynak` listesidir (betik koşuda kullandığı kaynakları adlarıyla yazar);
# bu sözlük yalnız o dosya düştüğünde devreye girer. Ad betiklerdeki
# `CEKICI` anahtarlarıyla aynı.
KAYNAK_ADLARI = {"TCMB": "TCMB", "evds": "TCMB EVDS", "doviz": "doviz.com",
                 "mynet": "Mynet Finans", "google": "Google Finance"}


def adres(anahtar: str) -> str:
    """Kalem anahtarının (`doviz.json`) enstrüman sayfası; yoksa boş."""
    e = _ANAHTARDAN.get(anahtar or "")
    return f"/piyasa/{e.slug}" if e else ""


# -- biçim ---------------------------------------------------------------------

def bicim(deger, ondalik: int) -> str:
    """Türkçe sayı: binlik nokta, ondalık virgül (`48,5250`, `6.784,88`).

    Önce yuvarlanır: `number_format` fazla haneyi KESİYOR (ölçüldü: grafik
    ortası 48,12999… → "48,1299").
    """
    return formats.number_format(round(float(deger), ondalik), ondalik,
                                 use_l10n=True, force_grouping=True)


def _sayi(deger):
    if isinstance(deger, bool):
        return None
    if isinstance(deger, (int, float)):
        return float(deger)
    return None


def _tarih(metin) -> date | None:
    """`2026-09-11` ya da EVDS'nin `11-09-2026` biçimi → `date`."""
    m = str(metin or "").strip()[:10]
    for kalip in ("%Y-%m-%d", "%d-%m-%Y", "%d.%m.%Y"):
        try:
            return datetime.strptime(m, kalip).date()
        except ValueError:
            continue
    return None


def _an(metin) -> datetime | None:
    try:
        an = datetime.fromisoformat(str(metin))
    except (TypeError, ValueError):
        return None
    an = timezone.make_aware(an) if timezone.is_naive(an) else an
    return timezone.localtime(an)


def kaynak_adi(anahtar: str, piyasa: dict | None) -> str:
    for k in (piyasa or {}).get("kaynak") or []:
        if isinstance(k, dict) and k.get("anahtar") == anahtar:
            return k.get("kisa") or k.get("ad") or anahtar
    return KAYNAK_ADLARI.get(anahtar, anahtar)


# -- sayfa verisi --------------------------------------------------------------

def _kalem(doviz: dict | None, anahtar: str) -> dict | None:
    for k in (doviz or {}).get("kalemler") or []:
        if isinstance(k, dict) and k.get("anahtar") == anahtar:
            return k
    return None


def _son_deger(kalem: dict, doviz: dict, piyasa: dict | None) -> dict:
    """Yayına giden değerin kaynağı, zamanı ve değişiminin ne olduğu."""
    kaynak = kalem.get("kaynak") or ""
    durum = kalem.get("kaynak_durumu") or ""
    bulten = doviz.get("bulten") or {}
    sonuc = {"zaman": None, "gun": None, "zaman_metni": "", "uyari": ""}
    if kaynak == "TCMB":
        sonuc["kaynak"] = "TCMB"
        sonuc["gun"] = _tarih(bulten.get("tarih_iso") or bulten.get("tarih"))
        sonuc["zaman_metni"] = "döviz satış kuru, gösterge niteliğinde"
        sonuc["degisim_neye"] = "bir önceki TCMB bültenine göre"
    elif durum == "elle":
        sonuc["kaynak"] = f"{kaynak or 'Elle giriş'} (panelden girildi)"
        sonuc["gun"] = _tarih(kalem.get("girildi"))
        sonuc["degisim_neye"] = "panelde girilen önceki değere göre"
    else:
        sonuc["kaynak"] = kaynak_adi(kaynak, piyasa)
        sonuc["zaman"] = _an(kalem.get("piyasa_damgasi"))
        if durum == "resmi_kapanis":
            sonuc["gun"] = _tarih(kalem.get("veri_tarihi"))
            sonuc["zaman_metni"] = "resmî kapanış"
            sonuc["degisim_neye"] = "bir önceki kapanışa göre"
        else:
            sonuc["degisim_neye"] = f"{sonuc['kaynak']} kaynağının bildirdiği günlük değişim"
        if durum == "hesaplanan":
            sonuc["uyari"] = ("Yaklaşık değer: doğrudan kotasyon alınamadığı için ons "
                              "fiyatından hesaplandı.")
    return sonuc


def _degisim(kalem: dict, ondalik: int) -> dict | None:
    yuzde = _sayi(kalem.get("degisim_yuzde"))
    if yuzde is None:
        return None
    yon = kalem.get("yon") or ("yukari" if yuzde > 0 else "asagi" if yuzde < 0 else "esit")
    tutar = _sayi(kalem.get("degisim"))
    return {
        "yuzde": abs(yuzde),
        "yon": yon,
        # Sıfır tutar basılmaz: "(0,0000 ₺)" okura yüzdenin söylediğinden
        # fazlasını söylemiyor.
        "tutar": bicim(abs(tutar), ondalik) if tutar else "",
        "isaret": "+" if yon == "yukari" else "−" if yon == "asagi" else "",
        "fiil": {"yukari": "yükseldi", "asagi": "geriledi"}.get(yon, "değişmedi"),
    }


def _resmi_kapanis(anahtar: str, kalem: dict, piyasa: dict | None) -> dict | None:
    """Gram altın: TCMB EVDS'nin resmî kapanışı (piyasa.py çapraz kontrolü).

    Yayına giden değer zaten EVDS kapanışıysa ikinci kez basılmaz.
    """
    if kalem.get("kaynak_durumu") == "resmi_kapanis":
        return None
    for satir in (((piyasa or {}).get("capraz_kontrol") or {})
                  .get("resmi_kapanis_piyasa_farki") or []):
        if not isinstance(satir, dict) or satir.get("kalem") != anahtar:
            continue
        deger = _sayi(satir.get("resmi_kapanis"))
        gun = _tarih(satir.get("resmi_tarih"))
        if deger is None or gun is None:
            return None
        return {"deger": deger, "gun": gun,
                "kaynak": kaynak_adi(satir.get("resmi_kaynak") or "evds", piyasa),
                "seri": satir.get("resmi_seri") or ""}
    return None


def gecmis_serisi(kalem: dict) -> list[dict]:
    """Geçerli gözlemler, eskiden yeniye; kaynağı yazılmamışsa boş."""
    if not (kalem.get("gecmis_kaynak") or "").strip():
        return []
    gunler: dict[date, float] = {}
    for satir in kalem.get("gecmis") or []:
        if not isinstance(satir, dict):
            continue
        gun, deger = _tarih(satir.get("tarih")), _sayi(satir.get("deger"))
        if gun is None or deger is None or deger <= 0:
            continue
        gunler[gun] = deger
    return [{"tarih": g, "deger": gunler[g]} for g in sorted(gunler)][-GECMIS_GRAFIK:]


def gecmis_tablosu(seri: list[dict], ondalik: int) -> list[dict]:
    """Tablo satırları, yeniden eskiye; değişim serideki bir önceki gözleme göre."""
    satirlar = []
    for i, s in enumerate(seri):
        onceki = seri[i - 1]["deger"] if i else None
        fark = None
        if onceki:
            yuzde = (s["deger"] - onceki) / onceki * 100
            yon = "yukari" if yuzde > 0 else "asagi" if yuzde < 0 else "esit"
            fark = {"yuzde": abs(round(yuzde, 2)), "yon": yon,
                    "fiil": {"yukari": "yükseldi", "asagi": "geriledi"}.get(yon, "değişmedi")}
        satirlar.append({"tarih": s["tarih"], "deger": bicim(s["deger"], ondalik), "fark": fark})
    return list(reversed(satirlar))[:GECMIS_TABLO]


# Grafiğin çizim alanı (viewBox). Eksen yazıları SVG'nin DIŞINDA, HTML'de
# durur: viewBox ölçeklenirken SVG içindeki yazı da küçülürdü — 360 px'te
# 6 px'e iniyordu. Çizgi `vector-effect: non-scaling-stroke` ile her
# genişlikte aynı kalınlıkta.
GRAFIK_EN, GRAFIK_BOY = 600, 200


def grafik(seri: list[dict], ondalik: int) -> dict | None:
    """Tek çizgi: x ekseni TARİHLE orantılı (hafta sonu boşluğu görünür)."""
    if len(seri) < 2:
        return None
    ilk, son = seri[0]["tarih"], seri[-1]["tarih"]
    gun_araligi = (son - ilk).days or 1
    degerler = [s["deger"] for s in seri]
    alt, ust = min(degerler), max(degerler)
    aralik = ust - alt

    def y(deger):
        if not aralik:
            return GRAFIK_BOY / 2
        return round((ust - deger) / aralik * GRAFIK_BOY, 2)

    noktalar = " ".join(
        f"{round((s['tarih'] - ilk).days / gun_araligi * GRAFIK_EN, 2)},{y(s['deger'])}"
        for s in seri)
    en_dusuk = min(seri, key=lambda s: s["deger"])
    en_yuksek = max(seri, key=lambda s: s["deger"])
    return {
        "en": GRAFIK_EN, "boy": GRAFIK_BOY, "noktalar": noktalar,
        "ilk": ilk, "son": son, "adet": len(seri),
        # Y ekseni: en yüksek · orta · en düşük — çizgi tam bu üç çizgiye
        # oturur (çizim alanı verinin aralığıdır, pay bırakılmaz).
        "y_etiketleri": ([bicim(ust, ondalik), bicim((ust + alt) / 2, ondalik), bicim(alt, ondalik)]
                         if aralik else [bicim(ust, ondalik)]),
        "en_dusuk": {"deger": bicim(en_dusuk["deger"], ondalik), "tarih": en_dusuk["tarih"]},
        "en_yuksek": {"deger": bicim(en_yuksek["deger"], ondalik), "tarih": en_yuksek["tarih"]},
        "son_deger": bicim(seri[-1]["deger"], ondalik),
        "yatay": [0, GRAFIK_BOY / 2, GRAFIK_BOY] if aralik else [GRAFIK_BOY / 2],
    }


def sayfa_verisi(enstruman: Enstruman, doviz: dict | None, piyasa: dict | None) -> dict:
    """Şablonun okuduğu paket. `doviz` yoksa yalnız `var: False` döner."""
    kalem = _kalem(doviz, enstruman.anahtar)
    if not doviz or kalem is None:
        return {"var": False, "tazelik": (doviz or {}).get("tazelik")}
    deger = _sayi(kalem.get("deger"))
    alis, satis = _sayi(kalem.get("alis")), _sayi(kalem.get("satis"))
    bulten = doviz.get("bulten") or {}
    paket = {
        "var": True,
        "tazelik": doviz.get("tazelik"),
        "deger": deger,
        "deger_metni": bicim(deger, enstruman.ondalik) if deger is not None else "",
        "birim_isareti": "₺" if kalem.get("birim") == "TL" else (kalem.get("birim") or ""),
        "son": _son_deger(kalem, doviz, piyasa) if deger is not None else None,
        "degisim": _degisim(kalem, enstruman.ondalik) if deger is not None else None,
        # TCMB alış/satış ikisi birlikte varsa; biri eksikse çift basılmaz.
        "tcmb": ({"alis": bicim(alis, enstruman.ondalik), "satis": bicim(satis, enstruman.ondalik),
                  "gun": _tarih(bulten.get("tarih_iso") or bulten.get("tarih")),
                  "no": bulten.get("no") or ""}
                 if alis is not None and satis is not None else None),
        "resmi_kapanis": None,
        "kunye": ((doviz.get("kaynak") or {}).get("kunye") or ""),
    }
    kapanis = _resmi_kapanis(enstruman.anahtar, kalem, piyasa)
    if kapanis:
        kapanis["deger_metni"] = bicim(kapanis["deger"], enstruman.ondalik)
        paket["resmi_kapanis"] = kapanis
    seri = gecmis_serisi(kalem)
    paket["gecmis"] = gecmis_tablosu(seri, enstruman.ondalik) if seri else []
    paket["gecmis_kaynak"] = (kalem.get("gecmis_kaynak") or "").strip() if seri else ""
    paket["grafik"] = grafik(seri, enstruman.ondalik)
    return paket


def cetvel_kaynaklari(doviz: dict | None, piyasa: dict | None) -> dict:
    """Ekonomi cetvelinin künyesi: hangi sütun hangi kaynaktan, ne zaman.

    20 Ekim 2026 (P1 düzeltmesi). Cetvelin künyesi yalnız "TCMB bülteni …
    Kaynak: TCMB döviz kurları" diyordu; oysa "Son" ve "Değişim" sütunları
    canlı kaynak tazeyken o kaynağın (doviz.com vb.) kotasyonudur,
    `alis`/`satis` ise HER ZAMAN TCMB bülteni (`canli-veri/doviz.py`,
    `piyasadan_yerlestir`). Kaynak adı, zamanı ve değişimin neye göre
    olduğu enstrüman sayfasıyla aynı yoldan gelir (`_son_deger`) — iki
    sayfa aynı rakamı farklı kaynağa atfedemez.

    `son`: aynı kaynak + zaman + değişim tanımını paylaşan kalemlerin
    grupları, cetveldeki sırayla. `tcmb`: alış/satış basılan bir kalem
    varsa bülten günü ve numarası, yoksa None. `adlar`: başlık çubuğu
    için geçen kaynak adları, tekrarsız.
    """
    sonuc = {"son": [], "tcmb": None, "adlar": []}
    if not doviz:
        return sonuc
    gruplar: dict[tuple, dict] = {}
    alis_satis_var = False
    for kalem in doviz.get("kalemler") or []:
        if not isinstance(kalem, dict):
            continue
        if _sayi(kalem.get("alis")) is not None and _sayi(kalem.get("satis")) is not None:
            alis_satis_var = True
        # Şablonun "–" bastığı (değersiz) kalemin kaynağı yok.
        if not _sayi(kalem.get("deger")):
            continue
        son = _son_deger(kalem, doviz, piyasa)
        anahtar = (son["kaynak"], son["zaman"], son["gun"], son["zaman_metni"],
                   son.get("degisim_neye", ""))
        grup = gruplar.setdefault(anahtar, {**son, "kalemler": []})
        grup["kalemler"].append(kalem.get("ad") or kalem.get("anahtar") or "")
    sonuc["son"] = list(gruplar.values())
    if alis_satis_var:
        bulten = doviz.get("bulten") or {}
        sonuc["tcmb"] = {"gun": _tarih(bulten.get("tarih_iso") or bulten.get("tarih")),
                         "no": bulten.get("no") or ""}
    adlar = [g["kaynak"] for g in sonuc["son"]] + (["TCMB"] if sonuc["tcmb"] else [])
    sonuc["adlar"] = list(dict.fromkeys(adlar))
    return sonuc


# -- çevirici (betiksiz form, GET) ---------------------------------------------

AZAMI_MIKTAR = 1e12


def miktar_coz(ham: str):
    """`1.250,50` · `1250,5` · `1250.5` · `100` → float; çözülemezse None."""
    m = re.sub(r"\s+", "", ham or "")
    if not m or not re.fullmatch(r"[0-9.,]+", m):
        return None
    if "," in m:
        m = m.replace(".", "").replace(",", ".")
    elif m.count(".") > 1 or re.fullmatch(r"\d{1,3}(\.\d{3})+", m):
        m = m.replace(".", "")          # binlik nokta: 1.000 / 1.000.000
    try:
        return float(m)
    except ValueError:
        return None


def cevir(get, paket: dict, enstruman: Enstruman) -> dict:
    """`?miktar=…&yon=doviz|tl` → sonuç cümlesi. Kur yoksa form çizilmez."""
    ham = (get.get("miktar") or "").strip()[:40]
    yon = get.get("yon") if get.get("yon") in ("doviz", "tl") else "doviz"
    sonuc = {"istendi": bool(ham), "ham": ham, "yon": yon, "metin": "", "hata": ""}
    if not ham:
        return sonuc
    miktar = miktar_coz(ham)
    deger = paket.get("deger")
    if miktar is None or not 0 < miktar <= AZAMI_MIKTAR:
        sonuc["hata"] = "Geçerli bir miktar girin (ör. 100 ya da 1.250,50)."
    elif not deger:
        sonuc["hata"] = "Değer bilgisi olmadığı için çevrilemiyor."
    elif yon == "doviz":
        sonuc["metin"] = (f"{bicim(miktar, 2)} {enstruman.birim} = "
                          f"{bicim(miktar * deger, 2)} TL")
    else:
        sonuc["metin"] = (f"{bicim(miktar, 2)} TL = "
                          f"{bicim(miktar / deger, 4)} {enstruman.birim}")
    return sonuc


def aciklama(enstruman: Enstruman, paket: dict) -> str:
    """Meta açıklama: değer, kaynağı ve ZAMANI birlikte (bayatsa tarih görünür)."""
    if not paket.get("var") or paket.get("deger") is None:
        return (f"{enstruman.ad} kaç TL? Bursa Hakimiyet piyasa sayfası: değer, "
                "kaynak ve güncelleme zamanı.")
    son = paket["son"]
    zaman = son["zaman"] or son["gun"]
    parcalar = [f"{enstruman.ad} {paket['deger_metni']} TL"]
    if zaman:
        parcalar[0] += f" ({formats.date_format(zaman, 'j F Y')}, {son['kaynak']})"
    if paket["tcmb"]:
        parcalar.append(f"TCMB döviz alış {paket['tcmb']['alis']}, satış {paket['tcmb']['satis']}")
    parcalar.append("TL çevirici ve kaynak bilgisi")
    return ". ".join(parcalar) + "."
