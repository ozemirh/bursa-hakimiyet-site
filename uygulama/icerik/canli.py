"""`canli-veri/` çıktılarını sayfaya taşır.

Çekme betikleri (`canli-veri/*.py`) siteden **bağımsız** çalışır: zamanlanmış
görev olarak koşar, `canli-veri/veri/<bileşen>.json` yazar. Site o dosyaları
yalnızca **okur**. Bu ayrım bilinçli — bir kaynak düştüğünde ya da yavaşladığında
sayfa isteği ona takılmasın; sayfa hep diskten okur, en kötü ihtimalle biraz
eski veriyi gösterir.

## Bayatlık

Her dosya kendi `bayat_esik_dakika` değerini taşır: döviz 1.440, hava 180,
namaz 2.880, puan durumu 2.880. Eşiği aşan veri **atılmaz**, "bayat" diye
işaretlenir ve şablon güncelleme zamanını okura gösterir. Gerekçe: haftada bir
değişen puan tablosunun bir gün gecikmesi sorun değil, ama okur neye baktığını
bilmeli. Dosya hiç yoksa bileşen sessizce gizlenir — uydurma değer basmaktansa
hiç göstermemek doğru.

## Önbellek

Dosyalar her istekte diskten okunmaz; `KISA_BELLEK_SANIYE` boyunca süreç
belleğinde tutulur. Anasayfa altı bileşeni birden istiyor ve saniyede onlarca
istek gelebilir.
"""

from __future__ import annotations

import json
import re
import time
from datetime import date, datetime
from pathlib import Path

from django.conf import settings

KISA_BELLEK_SANIYE = 30

_bellek: dict[str, tuple[float, dict | None]] = {}


def _kok() -> Path:
    return Path(getattr(settings, "CANLI_VERI_KOK",
                        settings.BASE_DIR.parent / "canli-veri" / "veri"))


def oku(bilesen: str) -> dict | None:
    """Bileşenin JSON'unu döndürür; yoksa ya da bozuksa None.

    Dönen sözlüğe iki alan eklenir:
      `bayat`      — güncelleme eşiği aştı mı
      `yas_dakika` — verinin yaşı
    """
    simdi = time.time()
    onbellek = _bellek.get(bilesen)
    if onbellek and simdi - onbellek[0] < KISA_BELLEK_SANIYE:
        return onbellek[1]

    yol = _kok() / f"{bilesen}.json"
    veri: dict | None = None
    try:
        with open(yol, "r", encoding="utf-8") as f:
            veri = json.load(f)
    except (OSError, json.JSONDecodeError):
        veri = None

    if veri is not None:
        yas = _yas_dakika(veri.get("guncelleme", ""))
        esik = veri.get("bayat_esik_dakika") or 0
        veri["yas_dakika"] = yas
        veri["bayat"] = bool(yas is not None and esik and yas > esik)

    _bellek[bilesen] = (simdi, veri)
    return veri


def _yas_dakika(damga: str):
    try:
        an = datetime.fromisoformat(damga)
    except (TypeError, ValueError):
        return None
    simdi = datetime.now(an.tzinfo) if an.tzinfo else datetime.now()
    return round((simdi - an).total_seconds() / 60, 1)


def simdiki_vakit(namaz: dict | None) -> str:
    """İçinde bulunulan namaz vaktinin anahtarı; şablon onu vurguluyor.

    Yatsıdan sonra ve imsaktan önce "yatsı" sayılır — gün dönmeden vakit
    değişmiyor.
    """
    if not namaz or not namaz.get("gunler"):
        return ""
    vakitler = namaz["gunler"][0].get("vakitler") or {}
    simdi = datetime.now().strftime("%H:%M")
    gecerli = ""
    for anahtar, saat in vakitler.items():
        if saat <= simdi:
            gecerli = anahtar
    return gecerli or "yatsi"


def _tarihe_cevir(damga: str | None):
    """`YYYY-AA-GG` → `date`; çözülemezse None (şablon o zaman hiç basmaz)."""
    try:
        return date.fromisoformat(damga)
    except (TypeError, ValueError):
        return None


def vizyon_filmleri(vizyon: dict | None, adet: int = 4) -> list[dict]:
    """Vizyon takvimini şablonun beklediği **düz** film listesine çevirir.

    Dosya haftalara bölünmüş (`haftalar[].filmler[]`); sayfadaki kart şeridi
    düz bir liste istiyor. Boş dönerse şablon sahte kart basmaz, boş durumu
    gösterir — dört tane "Vizyon filmi N — yer tutucu" kartı 27 Ağustos'ta
    bu yüzden kaldırıldı.

    **Afiş basılmaz.** Dosyanın kendi notu afişlerin telifli olduğunu ve
    dosyanın afiş taşımadığını söylüyor; ayrıca dış adrese bağlanmak sayfanın
    internetsiz açılması kuralına aykırı. Kartta yerel yer tutucu durur.
    """
    if not vizyon:
        return []
    filmler: list[dict] = []
    for hafta in vizyon.get("haftalar") or []:
        for film in hafta.get("filmler") or []:
            ad = (film.get("ad") or "").strip()
            if not ad:
                continue
            # Kaynakta olmayan alan doldurulmaz; şablon boş olanı hiç basmaz.
            turler = [t for t in (film.get("tur") or []) if t]
            filmler.append({
                "ad": ad,
                # `date` süzgeci düz metinle çalışmaz; tarih burada çözülür ki
                # sayfada "4 Aralık 2026" yazsın, "2026-12-04" değil.
                "tarih": _tarihe_cevir(film.get("tarih") or hafta.get("tarih")),
                "tur": " · ".join(turler),
                "yas_siniri": film.get("yas_siniri") or "",
                "dagitimci": film.get("dagitimci") or "",
            })
            if len(filmler) >= adet:
                return filmler
    return filmler


# Bursa'nın 17 ilçesi + il adı. Grup usulü liglerde (2. ve 3. Lig) hangi grubun
# önce gösterileceğini bu liste belirler: **Bursa kulübü barındıran grup** öne
# alınır. Liste `taksonomi` uygulamasındaki ilçe kayıtlarıyla aynı adları
# taşır ama oradan okunmaz — puan tablosunu çizmek için veritabanına gitmek
# gereksiz bir bağ olurdu.
BURSA_ADLARI = (
    "BURSA", "OSMANGAZİ", "NİLÜFER", "YILDIRIM", "GEMLİK", "İNEGÖL",
    "MUDANYA", "MUSTAFAKEMALPAŞA", "KARACABEY", "ORHANGAZİ", "İZNİK",
    "KESTEL", "GÜRSU", "YENİŞEHİR", "ORHANELİ", "BÜYÜKORHAN", "HARMANCIK",
    "KELES",
)


def _bursa_kulubu(ad: str) -> bool:
    """Takım adı bir Bursa kulübünü mü gösteriyor.

    Sözcük **başı** eşleşmesi arar: "SULTAN SU İNEGÖLSPOR" ve "İNEGÖL KAFKAS"
    yakalanır, "YENİ MALATYASPOR" (YENİŞEHİR'e takılmasın diye) yakalanmaz.
    """
    for parca in re.split(r"[^0-9A-Za-zÇĞİÖŞÜçğıöşü]+", (ad or "").upper()):
        if parca and any(parca.startswith(yer) for yer in BURSA_ADLARI):
            return True
    return False


def _mac_duzelt(mac: dict | None) -> dict | None:
    """Maç kaydına şablonun ihtiyaç duyduğu iki türetilmiş alanı ekler.

    Kaynağın tarihi `GG.AA.YYYY` metni; `<time datetime>` ISO ister ve
    `date` süzgeci `date` nesnesi ister. Kaynakta olmayan hiçbir alan
    uydurulmaz: skor yoksa `oynandi` false kalır, şablon saat/tarih basar.
    """
    if not mac:
        return None
    kopya = dict(mac)
    try:
        kopya["tarih_g"] = datetime.strptime(mac.get("tarih") or "",
                                             "%d.%m.%Y").date()
    except ValueError:
        kopya["tarih_g"] = None
    kopya["skor_var"] = bool(mac.get("oynandi")
                             and mac.get("ev_gol") is not None
                             and mac.get("deplasman_gol") is not None)
    return kopya


def puan_takibi(puan: dict | None) -> dict | None:
    """`takip` bloğunu şablona hazır hâlde döndürür (Bursaspor + haftanın maçı).

    Çekme betiği Bursaspor'u dört ligin tablosunda arayıp bulduğu satırı ve o
    haftaki maçını `takip` altına yazıyor; ligi koda gömülü değil. Blok yoksa
    şablon maç kutusunu hiç çizmez.
    """
    if not puan or not puan.get("takip"):
        return None
    takip = dict(puan["takip"])
    takip["mac"] = _mac_duzelt(takip.get("mac"))
    return takip


def puan_ligleri(puan: dict | None) -> list[dict]:
    """Lig listesini sekmeli tabloya hazırlar.

    Üç karar burada uygulanır (29 Ağustos 2026):

    1. **Açık sekme Bursaspor'un ligidir**, listenin ilki değil — okur
       gazeteyi Bursaspor için açıyor. Lig `takip.lig` alanından gelir.
    2. **Grup körlemesine seçilmez.** Bursaspor'un grubu, yoksa Bursa kulübü
       barındıran grup öne alınır; birden çok grup varsa okur değiştirebilsin
       diye hepsi çizilir.
    3. **Tablo kırpılmaz** — grubun bütün takımları gelir.
    """
    if not puan:
        return []
    takip = puan.get("takip") or {}
    acik_lig = takip.get("lig")
    bizim_id = takip.get("kulup_id")
    ligler = []
    for lig in puan.get("ligler") or []:
        gruplar = []
        for grup in lig.get("gruplar") or []:
            takimlar = []
            bizim_grup = False
            bursali = 0
            for t in grup.get("takimlar") or []:
                bizim = bool(bizim_id and t.get("kulup_id") == bizim_id)
                bursa = bizim or _bursa_kulubu(t.get("ad", ""))
                bizim_grup = bizim_grup or bizim
                bursali += 1 if bursa else 0
                takimlar.append(dict(t, bizim=bizim, bursa=bursa))
            gruplar.append({
                "grup_id": grup.get("grup_id"),
                "ad": grup.get("ad") or "",
                "takimlar": takimlar,
                "bizim_grup": bizim_grup,
                "bursali": bursali,
            })
        # Bursaspor'un grubu en önde; sonra en çok Bursa kulübü olan grup.
        # `sort` kararlı olduğu için eşitlikte kaynağın sırası korunur.
        gruplar.sort(key=lambda g: (not g["bizim_grup"], -g["bursali"]))
        for sira, grup in enumerate(gruplar):
            grup["acik"] = sira == 0
        ligler.append({
            "anahtar": lig.get("anahtar", ""),
            "ad": lig.get("ad", ""),
            "sezon": lig.get("sezon", ""),
            "hafta": lig.get("hafta"),
            "gruplar": gruplar,
            "coklu_grup": len(gruplar) > 1,
            "acik": bool(acik_lig and lig.get("anahtar") == acik_lig),
        })
    if ligler and not any(l["acik"] for l in ligler):
        ligler[0]["acik"] = True   # takip bloğu yoksa ilk lig açılır
    return ligler


# -- hava durumu paneli ---------------------------------------------------
#
# 30 Ağustos 2026: panel `servis-uclu` içinde üçte bir sütuna sıkışıyordu ve
# MGM paketinin yirmi küsur alanından yalnız beşini gösteriyordu — anlık
# sıcaklık, gün adı, en düşük/en yüksek. Saatlik dizi ve son durum ölçümleri
# (nem, rüzgâr, basınç, görüş, yağış) dosyada DURUYOR ama sayfaya hiç
# çıkmıyordu. Panel tam genişliğe alındı; aşağıdaki iki yardımcı o veriyi
# şablonun basabileceği düz yapılara çevirir.
#
# Kural aynı: **kaynakta olmayan alan uydurulmaz.** `None` gelen ölçüm
# listeye hiç girmez, şablon o kutucuğu çizmez. MGM'nin ölçemediği alanı
# sıfır gibi göstermek (rüzgâr yok / yağış yok) yanlış bilgi olurdu.

# MGM hadise kodu -> `parca/simgeler.html` içindeki `hv-*` simgesi.
# Sözlükteki 31 kodun hepsi karşılanır; tanınmayan kod `hv-bulut`a düşer
# (nötr), uydurma bir simge seçilmez.
HAVA_SIMGE = {
    "A": "hv-acik", "AB": "hv-az-bulut", "PB": "hv-parcali", "CB": "hv-kapali",
    "HY": "hv-yagmur", "Y": "hv-yagmur", "KY": "hv-yagmur", "HHY": "hv-yagmur",
    "HSY": "hv-saganak", "SY": "hv-saganak", "KSY": "hv-saganak",
    "MSY": "hv-saganak",
    "GSY": "hv-firtina", "KGY": "hv-firtina", "KGSY": "hv-firtina",
    "DY": "hv-dolu",
    "KKY": "hv-kar", "HKY": "hv-kar", "K": "hv-kar", "KYK": "hv-kar",
    "YKY": "hv-kar",
    "SIS": "hv-sis", "PUS": "hv-sis", "DNM": "hv-sis", "KF": "hv-sis",
    "R": "hv-ruzgar", "GKR": "hv-ruzgar", "KKR": "hv-ruzgar",
    "SCK": "hv-sicak", "SGK": "hv-soguk",
}


# Gece karşılığı OLAN kodlar. Güneşli simgeyi gece yarısına basmak
# (23:00'te sarı güneş) paneli inandırıcılıktan düşürüyordu; yalnız
# "gökyüzü açık" ailesinin ay karşılığı var, yağmurun gecesi ayrı çizilmez.
HAVA_SIMGE_GECE = {
    "hv-acik": "hv-acik-gece",
    "hv-az-bulut": "hv-bulut-gece",
    "hv-parcali": "hv-bulut-gece",
}

# Hadise -> renk ailesi. Saatlik şeritteki hücre zemini ve manzaranın
# paleti bundan seçilir. Beş aile var; tanınmayan kod "bulut"a düşer.
HAVA_AILE = {
    "hv-acik": "gunes", "hv-az-bulut": "gunes", "hv-sicak": "gunes",
    "hv-parcali": "bulut", "hv-kapali": "bulut", "hv-bulut": "bulut",
    "hv-sis": "bulut", "hv-ruzgar": "bulut",
    "hv-yagmur": "yagis", "hv-saganak": "yagis", "hv-firtina": "yagis",
    "hv-dolu": "kar", "hv-kar": "kar", "hv-soguk": "kar",
}


def hava_simgesi(hadise: dict | None, gece: bool = False) -> str:
    simge = HAVA_SIMGE.get((hadise or {}).get("kod", ""), "hv-bulut")
    return HAVA_SIMGE_GECE.get(simge, simge) if gece else simge


def hava_ailesi(hadise: dict | None, gece: bool = False) -> str:
    """Renk ailesi: `gunes` · `bulut` · `yagis` · `kar` · `gece`.

    Gece, havadan ÖNCE gelir: karanlıkta gökyüzünün rengini hadise değil,
    günün saati belirler. Yağış gecesi de mavi-lacivert çizilir.
    """
    if gece:
        return "gece"
    return HAVA_AILE.get(HAVA_SIMGE.get((hadise or {}).get("kod", ""),
                                        "hv-bulut"), "bulut")


def gece_mi(an, namaz: dict | None = None) -> bool:
    """Verilen an gece mi — güneş doğuşu/batışı Diyanet vakitlerinden.

    Namaz paketi zaten sayfada duruyor ve gerçek doğuş/batış saatini
    taşıyor; sabit bir "06:00-20:00" aralığı Bursa'da aralıkta bir buçuk
    saat şaşıyordu. Paket yoksa o kaba aralığa düşülür — panel yine çizilir,
    yalnız gece/gündüz kararı kabalaşır.
    """
    if an is None:
        return False
    saat = an.strftime("%H:%M")
    vakitler = ((namaz or {}).get("gunler") or [{}])[0].get("vakitler") or {}
    dogus, batis = vakitler.get("gunes"), vakitler.get("aksam")
    if dogus and batis:
        return not (dogus <= saat < batis)
    return not ("06:00" <= saat < "20:00")


def _zamana_cevir(damga: str | None):
    """ISO damga -> `datetime`; çözülemezse None (şablon o satırı atlar)."""
    try:
        return datetime.fromisoformat(str(damga))
    except (TypeError, ValueError):
        return None


def _olcumler(son: dict) -> list[dict]:
    """Son durumun ölçülebilmiş alanlarını kutucuk listesine çevirir.

    Sıra sabittir ve okurun sorduğu sıradır: nem, rüzgâr, basınç, görüş,
    yağış. `None` olan alan listeye girmez — MGM ölçmediyse kutucuk yoktur.
    Görüş metreden kilometreye çevrilir; 20.000 m okunmuyor, "20 km" okunuyor.
    """
    if not son:
        return []
    ruzgar = son.get("ruzgar_hiz")
    gorus = son.get("gorus_metre")
    kar = son.get("kar_yukseklik")
    yagis = son.get("yagis_24saat")
    adaylar = [
        ("Nem", son.get("nem"), "%", ""),
        ("Rüzgâr", ruzgar, " km/sa", son.get("ruzgar_yon") or ""),
        ("Basınç", son.get("basinc"), " hPa", ""),
        ("Görüş", None if gorus is None else round(gorus / 1000, 1),
         " km", ""),
        ("Yağış (24s)", yagis, " mm", ""),
        ("Kar", kar, " cm", ""),
    ]
    kutular = []
    for ad, deger, birim, alt in adaylar:
        if deger is None:
            continue
        # Nem yüzdesi önde işaretlenir: "%61" doğru, "61%" değil.
        metin = f"%{deger:g}" if birim == "%" else f"{deger:g}{birim}"
        kutular.append({"ad": ad, "deger": metin, "alt": alt})
    return kutular


def hava_paneli(hava: dict | None, namaz: dict | None = None,
                saat_adet: int = 8) -> dict | None:
    """Tam genişlikteki hava panelinin bütün parçalarını hazırlar.

    Dönen sözlük: `simdi` (anlık blok), `olcumler`, `saatlik`, `gunler`.
    Ayrıca `manzara` — anlık bloğun arkasındaki Uludağ çiziminin paleti.
    Renk BEZEME DEĞİL, bilgi taşır: gökyüzü havaya ve günün saatine göre
    değişir, okur sayfaya bakar bakmaz "açık mı, yağışlı mı, gece mi"
    sorusunu okumadan yanıtlar.
    Beş günün sıcaklık çubuğu için ortak bir ölçek kullanılır — her satır
    kendi ölçeğinde çizilseydi 17-31° ile 17-33° aynı boyda görünür, çubuk
    hiçbir şey anlatmazdı. `sol` ve `genislik` yüzdeleri beş günün ortak
    en düşük/en yüksek aralığına göre hesaplanır.
    """
    if not hava:
        return None

    son = hava.get("son_durum") or {}
    gunler_ham = hava.get("gunler") or []

    gunler = []
    sicakliklar = [d for g in gunler_ham
                   for d in (g.get("en_dusuk"), g.get("en_yuksek"))
                   if d is not None]
    taban = min(sicakliklar) if sicakliklar else 0
    tavan = max(sicakliklar) if sicakliklar else 0
    aralik = (tavan - taban) or 1
    for sira, g in enumerate(gunler_ham):
        dusuk, yuksek = g.get("en_dusuk"), g.get("en_yuksek")
        cubuk = None
        if dusuk is not None and yuksek is not None:
            cubuk = {
                "sol": round((dusuk - taban) / aralik * 100, 1),
                "genislik": max(round((yuksek - dusuk) / aralik * 100, 1), 4),
            }
        gunler.append({
            "tarih": _tarihe_cevir(g.get("tarih")),
            "bugun": sira == 0,
            "hadise": g.get("hadise") or {},
            "simge": hava_simgesi(g.get("hadise")),
            "aile": hava_ailesi(g.get("hadise")),
            "en_dusuk": dusuk,
            "en_yuksek": yuksek,
            "ruzgar_hiz": g.get("ruzgar_hiz"),
            "ruzgar_yon": g.get("ruzgar_yon") or "",
            "cubuk": cubuk,
        })

    # Saatlik dizi geçmiş saatleri de taşıyabiliyor; okura yalnız ÖNÜNDEKİ
    # saatler gösterilir. Hepsi geçmişte kaldıysa (veri bayatsa) dizi
    # kırpılmadan başından alınır, boş şerit çizmektense eski veriyi
    # bayatlık damgasıyla göstermek doğru.
    simdi = datetime.now()
    tum_saatler = []
    for s in hava.get("saatlik") or []:
        an = _zamana_cevir(s.get("zaman"))
        if an is None:
            continue
        karanlik = gece_mi(an, namaz)
        tum_saatler.append({
            "zaman": an,
            "gecmis": an.replace(tzinfo=None) < simdi,
            "gece": karanlik,
            "sicaklik": s.get("sicaklik"),
            "hissedilen": s.get("hissedilen"),
            "nem": s.get("nem"),
            "ruzgar_hiz": s.get("ruzgar_hiz"),
            "hadise": s.get("hadise") or {},
            "simge": hava_simgesi(s.get("hadise"), karanlik),
            "aile": hava_ailesi(s.get("hadise"), karanlik),
        })
    gelecek = [s for s in tum_saatler if not s["gecmis"]]
    saatlik = (gelecek or tum_saatler)[:saat_adet]

    # Manzaranın paleti ANLIK duruma bakar, günün tahminine değil: blok
    # "şu an" diyor, arkasındaki gökyüzü de şu anı göstermeli.
    olcum = _zamana_cevir(son.get("olcum_zamani"))
    karanlik = gece_mi(olcum or datetime.now(), namaz)
    aile = hava_ailesi(son.get("hadise"), karanlik)

    return {
        "merkez": hava.get("merkez") or {},
        "kaynak": hava.get("kaynak") or {},
        "bayat": hava.get("bayat"),
        "manzara": aile,
        "gece": karanlik,
        "simdi": {
            "sicaklik": son.get("sicaklik"),
            "hissedilen": son.get("hissedilen"),
            "hadise": son.get("hadise") or {},
            "simge": hava_simgesi(son.get("hadise"), karanlik),
            "olcum_zamani": olcum,
        },
        "olcumler": _olcumler(son),
        "saatlik": saatlik,
        "gunler": gunler,
    }


def anasayfa_verisi() -> dict:
    """Anasayfanın canlı veri bileşenleri.

    Adlar `canli-veri/veri/` altındaki dosya adlarıyla birebir; yeni bir
    kalem eklendiğinde burada tek satır yeter.
    """
    vizyon = oku("vizyon-takvimi")
    puan = oku("puan-durumu")
    hava = oku("hava-durumu")
    namaz = oku("namaz-vakitleri")
    return {
        # Doviz bandi CANLI kur gosteriyor (27 Agustos karari): serbest
        # piyasa kuru surekli hareket eder, TCMB bulteni gunde bir cikar.
        # Bayat esigi bu yuzden dosyanin kendi degerinden gelir (45 dk).
        "doviz": oku("doviz"),
        "hava": hava,
        "hava_panel": hava_paneli(hava, namaz),
        "namaz": namaz,
        "eczane": oku("nobetci-eczane"),
        "puan": puan,
        "puan_ligler": puan_ligleri(puan),
        "puan_takip": puan_takibi(puan),
        "vizyon": vizyon,
        "vizyon_filmler": vizyon_filmleri(vizyon),
        "namaz_simdiki": simdiki_vakit(namaz),
    }
