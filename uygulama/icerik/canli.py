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

## Tazelik sözleşmesi (19 Ekim 2026)

Zamanlayıcı 12 Eylül'de durdu ve site 37 gün boyunca 12 Eylül vakitlerini
"ŞİMDİ", 13 Eylül maçını "bekliyor" diye gösterdi (DEĞERLENDİRME-2026-10
bulgu 10). Kural artık TEK YERDE, `tazelik()`te: her bileşen
`veri["tazelik"]` taşır —

  `durum`      taze | bayat | yok
  `guncelleme` verinin zamanı (aware `datetime`) ya da None
  `bugun`      güncelleme bugün mü (bant tarihi ancak o zaman saklar)
  `metin`      okura basılacak hazır cümle ("12 Eylül 2026, 21:57 tarihli,
               güncel değil"); taze veride boş
  `elle`       veri panelden elle mi girildi (`kaynak.kisa == "panel"`)

Okura kural: bayat veri ya açık tarih + "güncel değil" işaretiyle gösterilir
ya da gizlenir — ASLA canlıymış gibi gösterilmez. Damgası okunamayan veri de
bayat sayılır: yaşını bilmediğimiz şey taze diye sunulamaz.

Namaz bu sözleşmenin dışında kalır, çünkü artık dosyadan okunmuyor:
`namaz_verisi()` vakitleri istek anında hesaplar (`canli-veri/namaz_hesap.py`,
saf Python, ağsız). Yalnız panelden elle giriş varsa dosya esastır ve o
zaman bugünün satırı yoksa panel "güncel değil" der.
"""

from __future__ import annotations

import importlib.util
import json
import re
import time
from datetime import date, datetime, timedelta
from pathlib import Path

from django.conf import settings
from django.utils import formats, timezone

KISA_BELLEK_SANIYE = 30

_bellek: dict[str, tuple[float, dict | None]] = {}

TAZE, BAYAT, YOK = "taze", "bayat", "yok"

# Dosya `bayat_esik_dakika` taşımıyorsa kullanılacak eşik — betiklerdeki
# sabitlerle aynı. Bilinmeyen bileşen için eşik yoktur (bayat sayılmaz).
VARSAYILAN_ESIK = {
    "doviz": 1440, "piyasa": 45, "hava-durumu": 180,
    "namaz-vakitleri": 2880, "nobetci-eczane": 1440,
    "puan-durumu": 2880, "vizyon-takvimi": 10080,
}


def _kok() -> Path:
    return Path(getattr(settings, "CANLI_VERI_KOK",
                        settings.BASE_DIR.parent / "canli-veri" / "veri"))


def oku(bilesen: str) -> dict | None:
    """Bileşenin JSON'unu döndürür; yoksa ya da bozuksa None.

    Dönen sözlüğe üç alan eklenir:
      `tazelik`    — sözleşme (bkz. modül notu)
      `bayat`      — `tazelik.durum != "taze"` (eski şablonlar için)
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
    if veri is not None and not isinstance(veri, dict):
        veri = None

    if veri is not None:
        veri["tazelik"] = tazelik(veri, VARSAYILAN_ESIK.get(bilesen))
        veri["yas_dakika"] = veri["tazelik"]["yas_dakika"]
        veri["bayat"] = veri["tazelik"]["durum"] != TAZE

    _bellek[bilesen] = (simdi, veri)
    return veri


def _yas_dakika(damga: str):
    try:
        an = datetime.fromisoformat(damga)
    except (TypeError, ValueError):
        return None
    simdi = datetime.now(an.tzinfo) if an.tzinfo else datetime.now()
    return round((simdi - an).total_seconds() / 60, 1)


def bugunun_tarihi() -> date:
    """Yerel (İstanbul) bugün. Testler gün sabitlemek için bunu yamar."""
    return timezone.localdate()


def _aware(an: datetime) -> datetime:
    return timezone.make_aware(an) if timezone.is_naive(an) else an


def tazelik(veri: dict | None, varsayilan_esik: int | None = None,
            simdi: datetime | None = None) -> dict:
    """Tek tazelik kuralı. Şablonlar yalnız bunu okur."""
    if not veri:
        return {"durum": YOK, "guncelleme": None, "yas_dakika": None,
                "bugun": False, "metin": "", "elle": False}
    simdi = simdi or timezone.now()
    try:
        guncelleme = _aware(datetime.fromisoformat(str(veri.get("guncelleme"))))
    except (TypeError, ValueError):
        guncelleme = None
    esik = veri.get("bayat_esik_dakika") or varsayilan_esik or 0
    yas = (round((simdi - guncelleme).total_seconds() / 60, 1)
           if guncelleme else None)
    if guncelleme is None:
        # Yaşı bilinmeyen veri taze diye sunulamaz — eşiği olan bileşende.
        durum = BAYAT if esik else TAZE
    else:
        durum = BAYAT if (esik and yas > esik) else TAZE
    yerel = timezone.localtime(guncelleme) if guncelleme else None
    bugun = bool(yerel and yerel.date() == timezone.localtime(simdi).date())
    if durum == BAYAT:
        metin = (f"{formats.date_format(yerel, 'j F Y, H:i')} tarihli, "
                 "güncel değil" if yerel else "güncelleme zamanı bilinmiyor, "
                 "güncel değil")
    else:
        metin = ""
    kaynak = veri.get("kaynak")
    elle = isinstance(kaynak, dict) and kaynak.get("kisa") == "panel"
    return {"durum": durum, "guncelleme": guncelleme, "yas_dakika": yas,
            "bugun": bugun, "metin": metin, "elle": elle}


# -- namaz: istek anında hesap --------------------------------------------

_namaz_modulu = None
_namaz_gunleri: dict[str, dict] = {}


def _namaz_hesap():
    """`canli-veri/namaz_hesap.py`yi dosya yolundan yükler (bir kez).

    Modül hiçbir şey içe aktarmıyor; `sys.path`e dokunulmaz. Yüklenemezse
    (dosya yok, sözdizimi bozuk) None — site dosyadaki vakitlere düşer.
    """
    global _namaz_modulu
    if _namaz_modulu is not None:
        return _namaz_modulu or None
    yol = Path(getattr(settings, "CANLI_BETIK_KOK",
                       settings.BASE_DIR.parent / "canli-veri")) / "namaz_hesap.py"
    try:
        spec = importlib.util.spec_from_file_location("bh_namaz_hesap", yol)
        modul = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modul)
        _namaz_modulu = modul
    except Exception:  # noqa: BLE001 - hesap yoksa dosya yolu var
        _namaz_modulu = False
        return None
    return modul


def _hesap_gunu(modul, gun: date) -> dict:
    anahtar = gun.isoformat()
    kayit = _namaz_gunleri.get(anahtar)
    if kayit is None:
        if len(_namaz_gunleri) > 60:
            _namaz_gunleri.clear()
        kayit = modul.gun_kaydi(gun)
        _namaz_gunleri[anahtar] = kayit
    return kayit


def bugunun_satiri(namaz: dict | None, gun: date | None = None) -> dict | None:
    """`gunler` içinden VERİLEN GÜNÜN satırı; yoksa None (asla `gunler[0]`)."""
    if not namaz:
        return None
    hedef = (gun or bugunun_tarihi()).isoformat()
    for satir in namaz.get("gunler") or []:
        if satir.get("tarih") == hedef:
            return satir
    return None


def namaz_verisi(simdi: datetime | None = None) -> dict | None:
    """Namaz paneli paketi; `bugun` alanı BUGÜNÜN satırıdır ya da None.

    Sıra: (1) panelden elle giriş dosyası varsa o esastır — editör hesabı
    bilerek reddetmiştir; (2) yoksa istek anında hesap (bugün + yarın);
    (3) hesap modülü yüklenemezse dosyadaki satırlar. (1) ve (3)'te bugünün
    satırı yoksa `bugun` None kalır ve panel "güncel değil" der.
    """
    yerel = timezone.localtime(simdi) if simdi else timezone.localtime()
    gun = yerel.date()
    dosya = oku("namaz-vakitleri")
    elle = bool(dosya and dosya["tazelik"]["elle"])
    modul = None if elle else _namaz_hesap()
    if modul is not None:
        paket = {
            "guncelleme": yerel.isoformat(timespec="seconds"),
            "kaynak": dict(modul.KAYNAK),
            "yer": dict(modul.BURSA),
            "vakit_adlari": dict(modul.VAKIT_ADI),
            "gunler": [_hesap_gunu(modul, gun),
                       _hesap_gunu(modul, gun + timedelta(days=1))],
            "hesap": True,
        }
        paket["tazelik"] = {"durum": TAZE, "guncelleme": yerel,
                            "yas_dakika": 0, "bugun": True, "metin": "",
                            "elle": False}
        paket["bayat"] = False
    elif dosya:
        paket = dict(dosya, hesap=False)
    else:
        return None
    paket["bugun"] = bugunun_satiri(paket, gun)
    if paket["bugun"] is not None and not paket["hesap"]:
        # Elle girilmiş tablo günlerce ileriyi kapsayabilir; ölçüt dosyanın
        # yaşı değil, BUGÜNÜN satırının varlığı.
        paket["tazelik"] = dict(paket["tazelik"], durum=TAZE, metin="")
        paket["bayat"] = False
    if paket["bugun"] is None:
        son = (paket.get("gunler") or [{}])[-1].get("tarih") or ""
        paket["tazelik"] = dict(paket["tazelik"], durum=BAYAT, metin=(
            f"vakit bilgisi güncel değil (son gün {son})" if son
            else "vakit bilgisi güncel değil"))
        paket["bayat"] = True
    return paket


def simdiki_vakit(namaz: dict | None, simdi: datetime | None = None) -> str:
    """İçinde bulunulan namaz vaktinin anahtarı; şablon onu vurguluyor.

    YALNIZ BUGÜNÜN satırına bakar: bugünün satırı yoksa boş döner ve "ŞİMDİ"
    şeridi hiç çizilmez (19 Ekim 2026'ya kadar `gunler[0]` okunuyordu ve
    12 Eylül vakitleri "şimdi" diye gösteriliyordu). Yatsıdan sonra ve
    imsaktan önce "yatsı" sayılır — gün dönmeden vakit değişmiyor.
    """
    yerel = timezone.localtime(simdi) if simdi else timezone.localtime()
    satir = bugunun_satiri(namaz, yerel.date())
    if not satir:
        return ""
    vakitler = satir.get("vakitler") or {}
    saat = yerel.strftime("%H:%M")
    gecerli = ""
    for anahtar, deger in vakitler.items():
        if deger and deger <= saat:
            gecerli = anahtar
    return gecerli or "yatsi"


def _tarihe_cevir(damga: str | None):
    """`YYYY-AA-GG` → `date`; çözülemezse None (şablon o zaman hiç basmaz)."""
    try:
        return date.fromisoformat(damga)
    except (TypeError, ValueError):
        return None


def vizyon_filmleri(vizyon: dict | None, adet: int = 4,
                    bugun: date | None = None) -> list[dict]:
    """Vizyon takvimini şablonun beklediği **düz** film listesine çevirir.

    Dosya haftalara bölünmüş (`haftalar[].filmler[]`); sayfadaki kart şeridi
    düz bir liste istiyor. Boş dönerse şablon sahte kart basmaz, boş durumu
    gösterir — dört tane "Vizyon filmi N — yer tutucu" kartı 27 Ağustos'ta
    bu yüzden kaldırıldı.

    **Afiş basılmaz.** Dosyanın kendi notu afişlerin telifli olduğunu ve
    dosyanın afiş taşımadığını söylüyor; ayrıca dış adrese bağlanmak sayfanın
    internetsiz açılması kuralına aykırı. Kartta yerel yer tutucu durur.

    **Geçmiş tarihli film süzülür** (19 Ekim 2026): bölüm "vizyona
    girecekler" diyor; dosya donunca 18 Eylül filmi Ekim'de hâlâ "yakında"
    görünüyordu. Bugün giren film kalır. Tarihi çözülemeyen film kalır —
    süzgeç bilmediği tarihi geçmiş saymaz.
    """
    if not vizyon:
        return []
    bugun = bugun or bugunun_tarihi()
    filmler: list[dict] = []
    for hafta in vizyon.get("haftalar") or []:
        for film in hafta.get("filmler") or []:
            ad = (film.get("ad") or "").strip()
            if not ad:
                continue
            tarih = _tarihe_cevir(film.get("tarih") or hafta.get("tarih"))
            if tarih is not None and tarih < bugun:
                continue
            # Kaynakta olmayan alan doldurulmaz; şablon boş olanı hiç basmaz.
            turler = [t for t in (film.get("tur") or []) if t]
            filmler.append({
                "ad": ad,
                # `date` süzgeci düz metinle çalışmaz; tarih burada çözülür ki
                # sayfada "4 Aralık 2026" yazsın, "2026-12-04" değil.
                "tarih": tarih,
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


# Geçmiş maç kutuda kaç gün daha "haftanın maçı" olarak kalır: maç
# pazar oynandıysa sonuç salıya kadar durur, sonra sıradaki maça geçilir.
SONUC_GOSTER_GUN = 3


def mac_takvimi(puan: dict | None, bugun: date | None = None) -> dict | None:
    """Haftanın maçı ile fikstürün sıradaki maçı TEK kaynaktan (19 Ekim 2026).

    Eskiden kutu `takip.mac`i (betiğin son koşusundaki hafta), fikstür ise
    "ilk oynanmamış maç"ı gösteriyordu; dosya donunca ikisi de 13 Eylül
    maçını "bekliyor" diye basıyordu. Şimdi ikisi de bugüne göre karar
    verir:

      her maç   `durum`: sonuc (skor var) · bekliyor (tarihi bugün/ileride)
                · bilgi_yok (tarihi geçti, skor yok — sonuç UYDURULMAZ)
      sonraki   tarihi bugün ya da ileride olan ilk oynanmamış maç
      haftanin  bugünün maçı; yoksa son SONUC_GOSTER_GUN içindeki maç;
                yoksa sıradaki; yoksa en son maç

    `takip.mac` fikstürde yoksa listeye eklenir (aynı `mac_id` varsa skoru
    olan kayıt esastır).
    """
    takip = (puan or {}).get("takip") or {}
    if not takip:
        return None
    bugun = bugun or bugunun_tarihi()
    ham: dict = {}
    sira: list = []
    for m in list(takip.get("fikstur") or []) + ([takip["mac"]] if takip.get("mac") else []):
        anahtar = m.get("mac_id") or (m.get("tarih"), m.get("ev"), m.get("deplasman"))
        onceki = ham.get(anahtar)
        if onceki is None:
            ham[anahtar] = m
            sira.append(anahtar)
        elif m.get("oynandi") and not onceki.get("oynandi"):
            ham[anahtar] = dict(onceki, **m)
    if not sira:
        return None
    maclar = []
    for anahtar in sira:
        m = _mac_duzelt(ham[anahtar])
        g = m["tarih_g"]
        if m["skor_var"]:
            m["durum"] = "sonuc"
        elif g is not None and g < bugun:
            m["durum"] = "bilgi_yok"
        else:
            m["durum"] = "bekliyor"
        maclar.append(m)
    maclar.sort(key=lambda m: (m["tarih_g"] or date.max, m.get("hafta") or 0))
    gecmis = [m for m in maclar if m["tarih_g"] and m["tarih_g"] < bugun]
    bugunku = [m for m in maclar if m["tarih_g"] == bugun]
    sonraki = next((m for m in maclar if m["durum"] == "bekliyor"
                    and m["tarih_g"] is not None), None)
    if bugunku:
        haftanin = bugunku[0]
    elif gecmis and (bugun - gecmis[-1]["tarih_g"]).days <= SONUC_GOSTER_GUN:
        haftanin = gecmis[-1]
    elif sonraki:
        haftanin = sonraki
    else:
        haftanin = gecmis[-1] if gecmis else maclar[-1]
    return {"maclar": maclar, "sonraki": sonraki, "haftanin": haftanin}


def puan_takibi(puan: dict | None, bugun: date | None = None) -> dict | None:
    """`takip` bloğunu şablona hazır hâlde döndürür (Bursaspor + haftanın maçı).

    Çekme betiği Bursaspor'u dört ligin tablosunda arayıp bulduğu satırı
    `takip` altına yazıyor; ligi koda gömülü değil. Haftanın maçı
    `mac_takvimi()`nden gelir (bugüne göre). `tazelik` dosyanınkidir: kutu
    bayat veride tarihle "güncel değil" der. Blok yoksa şablon maç kutusunu
    hiç çizmez.
    """
    if not puan or not puan.get("takip"):
        return None
    takip = dict(puan["takip"])
    takvim = mac_takvimi(puan, bugun)
    takip["mac"] = takvim["haftanin"] if takvim else None
    takip["tazelik"] = puan.get("tazelik") or tazelik(
        puan, VARSAYILAN_ESIK["puan-durumu"])
    return takip


def puan_ligleri(puan: dict | None) -> list[dict]:
    """Lig listesini sekmeli tabloya hazırlar.

    Üç karar burada uygulanır (29 Ağustos 2026):

    1. **Açık sekme Bursaspor'un ligidir**, listenin ilki değil — okur
       gazeteyi Bursaspor için açıyor. Lig `takip.lig` alanından gelir.
    2. **Grup körlemesine seçilmez.** Bursaspor'un grubu öne alınır; birden
       çok grup varsa okur değiştirebilsin diye hepsi çizilir. Kalan gruplar
       KAYNAKTAKİ sırayla dizilir — 3. Lig'de sekmeler 1. Grup'tan başlar
       (6 Eylül 2026, kullanıcı isteği). Eskiden ikinci ölçüt "en çok Bursa
       kulübü olan grup" idi ve 3. Lig, tek Bursa takımı (Bursa Yıldırım)
       2. Grup'ta olduğu için oradan açılıyordu. Bursa kulüpleri satır
       renginden zaten seçiliyor (`.bursali`), sekme sırasını bozmaya gerek
       yok; Bursaspor'un KENDİ grubu önde kalmaya devam eder.
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
            for t in grup.get("takimlar") or []:
                bizim = bool(bizim_id and t.get("kulup_id") == bizim_id)
                bursa = bizim or _bursa_kulubu(t.get("ad", ""))
                bizim_grup = bizim_grup or bizim
                takimlar.append(dict(t, bizim=bizim, bursa=bursa))
            gruplar.append({
                "grup_id": grup.get("grup_id"),
                "ad": grup.get("ad") or "",
                "takimlar": takimlar,
                "bizim_grup": bizim_grup,
            })
        # Yalnız Bursaspor'un grubu öne alınır; `sort` kararlı olduğu için
        # kalan gruplar kaynaktaki sırayı (1. Grup, 2. Grup, 3. Grup) korur.
        gruplar.sort(key=lambda g: not g["bizim_grup"])
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


# Rüzgâr yönünün kısaltması. MGM on altı yönün adını TAM yazıyla veriyor
# ("doğu-kuzeydoğu"); beş günlük tablonun sütunu o kadar geniş değil.
# Kısaltma parça parça kuruluyor — on altı yönü tek tek listelemeye gerek
# yok, tireyle ayrılan her parçanın karşılığı zaten aşağıdaki sekiz satırda.
# Tanınmayan parça sessizce atlanır; uydurma harf üretilmez, en kötü hâlde
# kısaltma boş kalır ve tabloda yalnız hız görünür.
_YON_HARF = {
    "kuzeydogu": "KD", "kuzeybati": "KB",
    "guneydogu": "GD", "guneybati": "GB",
    "kuzey": "K", "guney": "G", "dogu": "D", "bati": "B",
}
_YON_SADE = str.maketrans("çğıöşüâî", "cgiosuai")


def _yon_kisalt(ad: str | None) -> str:
    """"doğu-kuzeydoğu" -> "DKD"."""
    if not ad:
        return ""
    sade = ad.strip().lower().translate(_YON_SADE)
    return "".join(_YON_HARF.get(parca, "") for parca in sade.split("-"))


def _ok_acisi(derece) -> int | None:
    """Rüzgâr okunun döneceği açı.

    MGM'nin `ruzgar_yon_derece` alanı rüzgârın GELDİĞİ yönü söyler
    (meteoroloji sözleşmesi). Tablodaki ok ise rüzgârın GİTTİĞİ yönü
    gösterir — gazete grafiğinin sözleşmesi bu. Aradaki fark 180 derece.
    Simge yukarı bakarak çizildi, yani 0 derece kuzeyi gösteriyor.
    """
    if derece is None:
        return None
    try:
        return (int(derece) + 180) % 360
    except (TypeError, ValueError):
        return None


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
    # O GÜNÜN satırı; tarihsiz/eşleşmeyen pakette ilk satır yaklaşık değer
    # olarak kullanılır (doğuş/batış günde 1-2 dk kayar, kaba aralıktan iyi).
    gunler = (namaz or {}).get("gunler") or [{}]
    satir = bugunun_satiri(namaz, an.date()) or gunler[0]
    vakitler = satir.get("vakitler") or {}
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
    Ayrıca `manzara` — anlık bloğun arkasındaki fotoğrafın paleti.
    Renk BEZEME DEĞİL, bilgi taşır: panelin tonu havaya ve günün saatine
    göre değişir, okur sayfaya bakar bakmaz "açık mı, yağışlı mı, gece mi"
    sorusunu okumadan yanıtlar.

    Beş günün sıcaklığı 6 Eylül 2026'ya kadar ortak ölçekli bir ÇUBUKLA da
    çiziliyordu (`cubuk`: `sol` ve `genislik` yüzdeleri). Kullanıcı grafiği
    beğenmedi; en düşük/en yüksek artık yalnız yazıyla veriliyor ve
    yüzdeler hesaplanmıyor.
    """
    if not hava:
        return None

    son = hava.get("son_durum") or {}
    gunler_ham = hava.get("gunler") or []

    gunler = []
    for sira, g in enumerate(gunler_ham):
        dusuk, yuksek = g.get("en_dusuk"), g.get("en_yuksek")
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
            # 6 Eylül 2026, kullanıcı isteği ("panel çok boş"): bu üç alan
            # MGM paketinde ZATEN vardı, beş günlük listede basılmıyordu.
            # Yeni bir kaynağa gidilmedi, açılan tek şey sunum.
            "ruzgar_kisa": _yon_kisalt(g.get("ruzgar_yon")),
            "ruzgar_ok": _ok_acisi(g.get("ruzgar_yon_derece")),
            "nem_dusuk": g.get("en_dusuk_nem"),
            "nem_yuksek": g.get("en_yuksek_nem"),
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

    taze = hava.get("tazelik") or tazelik(hava, VARSAYILAN_ESIK["hava-durumu"])
    return {
        "merkez": hava.get("merkez") or {},
        "kaynak": hava.get("kaynak") or {},
        "tazelik": taze,
        "bayat": taze["durum"] != TAZE,
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


# -- nöbetçi eczane paneli ------------------------------------------------

# 31 Ağustos 2026, kullanıcı isteği: panel dosyadaki 34 eczaneden yalnızca
# ÜÇÜNÜ basıyordu ve okurun kalan otuz birine ulaşmasının bir yolu yoktu.
# Nöbetçi eczane bilgisi gece yarısı aranan bir bilgidir: okur "en yakını
# hangisi, telefonu ne, nasıl giderim, kaça kadar açık" sorularının
# dördünü de sorar. Dördünün yanıtı da `nobetci-eczane.json` içinde ZATEN
# duruyordu — eksik olan tek şey sunumdu.
#
# Nöbet saati eczane eczane DEĞİŞİYOR (31 Ağustos ölçümü: 34 eczane, sekiz
# ayrı pencere; biri 20:00'de kapanıyor). Bu yüzden tek bir "18:30-08:30"
# cümlesi basmak yanlış olurdu; her satır kendi saatini taşır, panelin
# başlığındaki pencere yalnızca EN YAYGIN olanı söyler.
#
# Kaynakta olmayan alan uydurulmaz: telefonu ya da harita konumu boş gelen
# eczane o bağlantı olmadan basılır (`ayiklayici` boş alanla geçiriyor).

# Konum bağlantısı DIŞ bir adrestir; sayfanın internetsiz açılması kuralını
# bozmaz — bağlantı bir kaynak değil, okurun kendi tıkladığı bir çıkıştır.
# Koordinat BEO'nun kendi sayfasından geliyor, tahmin edilmiyor.
HARITA_ADRESI = "https://www.google.com/maps/search/?api=1&query={},{}"

# Türkçe sıralama: `sorted` varsayılanı "İ"yi "Z"den sonraya atıyor,
# İnegöl ilçe listesinin en altında kalıyordu. Küçük bir alfabe yeter;
# `locale` kurmak sunucunun diline bağımlılık olurdu.
_TR_ALFABE = "aâbcçdefgğhıiîjklmnoöprsştuüvyz"
_TR_KUCULT = str.maketrans("IİÎÂ", "ıiîâ")
_ASCIYE = str.maketrans("çğıöşüâî", "cgiosuai")


def _tr_sirala(metin: str) -> tuple:
    kucuk = (metin or "").translate(_TR_KUCULT).lower()
    return tuple(_TR_ALFABE.find(h) if h in _TR_ALFABE else len(_TR_ALFABE)
                 for h in kucuk)


def _ilce_anahtar(ilce: str) -> str:
    """"OSMANGAZİ - DEMİRTAŞ" -> "osmangazi".

    Süzgeç ANA ilçeye göre çalışır: Demirtaş, Ovaakça ve Çalı ayrı birer
    nöbet bölgesi ama okur için Osmangazi ve Nilüfer'dir. Satırda tam ad
    durmaya devam eder.
    """
    ana = (ilce or "").split(" - ")[0].strip()
    ana = ana.translate(_TR_KUCULT).lower().translate(_ASCIYE)
    ana = re.sub(r"[^a-z0-9]+", "-", ana).strip("-")
    return ana or "belirtilmemis"


def _telefon_baglanti(ham: str) -> str:
    """Kaynaktaki telefonu `tel:` bağlantısına çevirir.

    Kaynak iki biçim veriyor ("0224 451 42 00" ve "0224-4437956"); ikisi de
    aynı numara. Çözülemeyen biçim olduğu gibi bırakılır, kırpılmaz.
    """
    rakam = re.sub(r"\D", "", ham or "")
    if len(rakam) == 11 and rakam.startswith("0"):
        return "+90" + rakam[1:]
    if len(rakam) == 10:
        return "+90" + rakam
    return rakam


def _nobet_metni(baslangic, bitis) -> str:
    if not baslangic or not bitis:
        return ""
    metin = f"{baslangic:%H:%M} – {bitis:%H:%M}"
    return metin + (" ertesi gün" if bitis.date() > baslangic.date() else "")


def eczane_paneli(eczane: dict | None, simdi: datetime | None = None):
    """Nöbet listesini süzülebilir bir panele çevirir.

    Dönen sözlük: `eczaneler` (ilçe, sonra ad sırasında), `ilceler`
    (süzgeç için ana ilçe + adet), `pencere` (en yaygın nöbet aralığı) ve
    `nobette` (şu an nöbeti sürenlerin sayısı).

    Dosya yoksa ya da hiç eczane taşımıyorsa None döner; şablon o zaman
    "şu an alınamıyor" der, sahte satır basmaz.
    """
    if not eczane:
        return None
    simdi = simdi or datetime.now()

    kayitlar = []
    for e in eczane.get("eczaneler") or []:
        ad = (e.get("ad") or "").strip()
        if not ad:
            continue
        ilce = (e.get("ilce") or "").strip()
        enlem, boylam = e.get("enlem"), e.get("boylam")
        baslangic = _zamana_cevir(e.get("nobet_baslangic"))
        bitis = _zamana_cevir(e.get("nobet_bitis"))
        kayitlar.append({
            "ad": ad,
            "ilce": ilce,
            "ilce_anahtar": _ilce_anahtar(ilce),
            "adres": (e.get("adres") or "").strip(),
            "telefon": (e.get("telefon") or "").strip(),
            "telefon_baglanti": _telefon_baglanti(e.get("telefon")),
            "harita": (HARITA_ADRESI.format(enlem, boylam)
                       if enlem is not None and boylam is not None else ""),
            # Ham koordinat da duruyor: sayfanın JSON-LD'si `geo` alanını
            # buradan yazıyor (`icerik/eczane.py`), hazır bağlantıyı
            # geri ayrıştırmıyor.
            "enlem": enlem,
            "boylam": boylam,
            "baslangic": baslangic,
            "bitis": bitis,
            "saat": _nobet_metni(baslangic, bitis),
            "nobette": bool(baslangic and bitis
                            and baslangic <= simdi < bitis),
        })
    if not kayitlar:
        return None
    kayitlar.sort(key=lambda k: (_tr_sirala(k["ilce"]), _tr_sirala(k["ad"])))
    taze = eczane.get("tazelik") or tazelik(eczane,
                                            VARSAYILAN_ESIK["nobetci-eczane"])

    ilceler: list[dict] = []
    sepet: dict[str, dict] = {}
    for k in kayitlar:
        kutu = sepet.get(k["ilce_anahtar"])
        if kutu is None:
            kutu = {"anahtar": k["ilce_anahtar"],
                    "ad": k["ilce"].split(" - ")[0].strip() or "Belirtilmemiş",
                    "adet": 0}
            sepet[k["ilce_anahtar"]] = kutu
            ilceler.append(kutu)
        kutu["adet"] += 1
    ilceler.sort(key=lambda i: _tr_sirala(i["ad"]))

    # Başlıktaki pencere EN YAYGIN aralıktır, tek doğru aralık değil:
    # sekiz ayrı pencere olduğu için "hepsi şu saatte" demek yalan olurdu.
    pencereler: dict[str, int] = {}
    for k in kayitlar:
        if k["saat"]:
            pencereler[k["saat"]] = pencereler.get(k["saat"], 0) + 1
    pencere = max(pencereler, key=pencereler.get) if pencereler else ""

    return {
        "gun": _tarihe_cevir(eczane.get("gun")),
        "sayi": len(kayitlar),
        "eczaneler": kayitlar,
        "ilceler": ilceler,
        "pencere": pencere,
        "pencere_adet": pencereler.get(pencere, 0),
        "nobette": sum(1 for k in kayitlar if k["nobette"]),
        "kaynak": eczane.get("kaynak") or {},
        "tazelik": taze,
        "bayat": taze["durum"] != TAZE,
    }


def anasayfa_verisi() -> dict:
    """Anasayfanın canlı veri bileşenleri.

    Adlar `canli-veri/veri/` altındaki dosya adlarıyla birebir; yeni bir
    kalem eklendiğinde burada tek satır yeter.
    """
    vizyon = oku("vizyon-takvimi")
    puan = oku("puan-durumu")
    hava = oku("hava-durumu")
    namaz = namaz_verisi()
    eczane = oku("nobetci-eczane")
    return {
        # Doviz bandi CANLI kur gosteriyor (27 Agustos karari): serbest
        # piyasa kuru surekli hareket eder, TCMB bulteni gunde bir cikar.
        # Bayat esigi bu yuzden dosyanin kendi degerinden gelir (45 dk).
        "doviz": oku("doviz"),
        "hava": hava,
        "hava_panel": hava_paneli(hava, namaz),
        "namaz": namaz,
        "eczane": eczane,
        "eczane_panel": eczane_paneli(eczane),
        "puan": puan,
        "puan_ligler": puan_ligleri(puan),
        "puan_takip": puan_takibi(puan),
        "vizyon": vizyon,
        "vizyon_filmler": vizyon_filmleri(vizyon),
        "namaz_simdiki": simdiki_vakit(namaz),
    }
