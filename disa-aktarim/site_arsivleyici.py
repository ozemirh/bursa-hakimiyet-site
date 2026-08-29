"""bursahakimiyet.com.tr canli sitesinden tum haber arsivini indirir.

Tek seferlik veri tasima araci: yeni site icin eski veritabanina erisim
olmadigindan, canli sitedeki haberler (baslik, spot, govde, gorsel, kaynak,
tarih) taranip yerel diske yapilandirilmis JSON + gorsel dosyasi olarak
kaydedilir. arac/ klasorundeki yapay-zeka editor aracindan bagimsizdir;
yalnizca arac/ayiklayici.py'yi salt-okunur import eder (degistirmez).

Kullanim:
    python site_arsivleyici.py                 # kaldigi yerden devam eder
    python site_arsivleyici.py --sitemap-yenile # url listesini yeniden kurar
    python site_arsivleyici.py --sinirla 20     # deneme: yalnizca 20 haber
    python site_arsivleyici.py --kok E:/arsiv   # ciktiyi baska surucuye/makineye al

Cikti koku --kok argumani ya da BH_ARSIV_KOK ortam degiskeniyle degistirilir.

Cikti (varsayilan D:/bursa-hakimiyet-arsiv altinda):
    tum-urller.jsonl       - sitemap'ten cikarilan tum haber adresleri
    ilerleme.json          - calisan/kaldigi ilerleme ozeti
    veri/<YIL-AY>/<id>.json    - haber basina yapilandirilmis veri
    gorseller/<YIL-AY>/<dosya> - indirilen gorseller
    log.txt                - calisma kaydi
    basarisiz.txt          - indirilemeyen adresler + neden
"""

from __future__ import annotations

import argparse
import gzip
import http.client
import json
import os
import random
import re
import socket
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

# arac/ayiklayici.py'yi salt-okunur import et (bu dosyayi degistirmiyoruz)
REPO_KOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_KOK / "arac"))
import ayiklayici  # noqa: E402

# -- ayarlar ------------------------------------------------------------

VARSAYILAN_KOK = "D:/bursa-hakimiyet-arsiv"


def kok_ayarla(yol: str | Path) -> None:
    """Cikti kokunu ve ona bagli tum yollari kurar.

    Makine degistiginde (baska laptop, baska surucu) yalnizca burasi degisir;
    --kok argumani ya da BH_ARSIV_KOK ortam degiskeni bu islevi cagirir.
    """
    global KOK, VERI_KOK, GORSEL_KOK, URL_LISTESI, ILERLEME_DOSYA, LOG_DOSYA, BASARISIZ_DOSYA
    KOK = Path(yol).expanduser()
    # "haber" ailesi eski yollari BIREBIR korur; calisan tarama etkilenmez.
    # Diger aileler kendi dosyalarina yazar, boylece ayni kok altinda yan yana
    # calisabilirler.
    ek = "" if AILE == "haber" else f"-{AILE}"
    VERI_KOK = KOK / f"veri{ek}"
    GORSEL_KOK = KOK / f"gorseller{ek}"
    URL_LISTESI = KOK / f"tum-urller{ek}.jsonl"
    ILERLEME_DOSYA = KOK / f"ilerleme{ek}.json"
    LOG_DOSYA = KOK / f"log{ek}.txt"
    BASARISIZ_DOSYA = KOK / f"basarisiz{ek}.txt"


# Sitemap indeksinde bes icerik ailesi var; tarayici uzun sure yalnizca
# "news" ailesini aliyordu. Digerlerinin gocte kaynagi yoktu.
#   news            556.824  haber
#   articles         24.111  kose yazisi   /yazarlar/{yazar}-{yid}/{slug}-{id}
#   videoGalleries   49.164  video         /videolar/{kat}-{katid}/{slug}-{id}
#   photoGalleries    8.815  foto galeri   /galeriler/{kat}-{katid}/{slug}-{id}
#   authors              71  yazar sayfasi /yazarlar/{slug}-{id}
AILELER = {
    "haber":  {"onek": "news",           "ad": "haber"},
    "kose":   {"onek": "articles",       "ad": "kose yazisi"},
    "video":  {"onek": "videoGalleries", "ad": "video"},
    "galeri": {"onek": "photoGalleries", "ad": "foto galeri"},
    "yazar":  {"onek": "authors",        "ad": "yazar sayfasi"},
}
AILE = "haber"

kok_ayarla(os.environ.get("BH_ARSIV_KOK", VARSAYILAN_KOK))

SITEMAP_INDEX = "https://www.bursahakimiyet.com.tr/static/sitemap/sitemap.xml"
DISK_GUVENLI_ESIK_GB = 10
ESZAMANLILIK = int(os.environ.get("BH_ESZAMANLILIK", "10"))
DENEME_SAYISI = 3
# Yonlendirme zinciri siniri: sitemap adreslerinin bir kismi eski kategori
# slug'ina isaret ediyor ve 301 donuyor.
EN_COK_YONLENDIRME = 5
ILERLEME_ARALIGI = 50  # bu kadar haberde bir ilerleme.json guncellenir

_ID_KATEGORI = re.compile(r"bursahakimiyet\.com\.tr/([a-z0-9-]+)/[a-z0-9-]+-(\d+)$")
_KAYNAK_P = re.compile(r"<p>\s*Kaynak\s*:\s*([^<]{2,40})</p>", re.I)
_IMG_SRC = re.compile(r'<img[^>]+src="([^"]+)"', re.I)
_VIDEO_SRC = re.compile(
    r'<iframe[^>]+src="([^"]*(?:youtube|youtu\.be|vimeo)[^"]*)"', re.I
)

_kilit = None  # log/ilerleme yazarken thread'ler birbirine girmesin


def _kilit_al():
    global _kilit
    if _kilit is None:
        import threading

        _kilit = threading.Lock()
    return _kilit


def log(mesaj: str) -> None:
    satir = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {mesaj}"
    print(satir)
    with _kilit_al():
        with open(LOG_DOSYA, "a", encoding="utf-8") as f:
            f.write(satir + "\n")


def basarisiz_kaydet(url: str, neden: str) -> None:
    with _kilit_al():
        with open(BASARISIZ_DOSYA, "a", encoding="utf-8") as f:
            f.write(f"{url}\t{neden}\n")


# -- disk guvenligi -------------------------------------------------------

def disk_yeterli_mi() -> bool:
    import shutil

    try:
        bos_gb = shutil.disk_usage(KOK).free / (1024**3)
    except FileNotFoundError:
        return True
    if bos_gb < DISK_GUVENLI_ESIK_GB:
        log(f"UYARI: hedef surucude yalnizca {bos_gb:.1f} GB bos alan kaldi, durduruluyor.")
        return False
    return True


# -- sitemap --------------------------------------------------------------

# -- kalici baglanti havuzu -------------------------------------------------
#
# NEDEN VAR (29 Agustos 2026'da olculdu). Betik once her istek icin yeni bir
# TCP+TLS baglantisi aciyordu (urllib boyle calisir). Ayni sayfa icin ardarda
# olculen sureler:
#
#     her istekte yeni baglanti : 13,14 sn/istek  (3,3 · 0,3 · 28,3 · 42,4 ...)
#     tek baglanti, keep-alive  :  1,34 sn/istek  (ilki 7,3 sonrakiler 0,15)
#
# Fark **9,8 kat**. Sebep sunucunun yavasligi degil: TTFB her olcumde
# 0,21-0,23 sn, govde indirmesi 0,005 sn. Zamanin tamami TCP `connect`
# asamasinda gecti ve sureler 1 / 3 / 7 / 15 / 42 sn diye ilerledi -- bu
# cekirdegin SYN yeniden gonderim deseni, yani **baglanti kurulum paketleri
# dusuruluyor**. Site Cloudflare arkasinda; her istekte yeni baglanti acan
# bir tarayici baglanti hizi sinirina takiliyor.
#
# Cozum bagimlilik eklemeden: her is parcacigi konak basina BIR baglantiyi
# acik tutar ve tekrar kullanir. `requests` kullanilmadi, betik salt standart
# kutuphaneyle calismali (baska makineye `paketle.ps1` ile tasinabiliyor).
#
# ONEMLI: keep-alive'in calismasi icin her yanitin GOVDESI SONUNA KADAR
# OKUNMALI, yoksa baglanti tekrar kullanilamaz.

_yerel = threading.local()


def _baglanti(konak: str, guvenli: bool, zaman_asimi: int):
    havuz = getattr(_yerel, "havuz", None)
    if havuz is None:
        havuz = _yerel.havuz = {}
    baglanti = havuz.get(konak)
    if baglanti is None:
        kurucu = http.client.HTTPSConnection if guvenli else http.client.HTTPConnection
        baglanti = havuz[konak] = kurucu(konak, timeout=zaman_asimi)
    return baglanti


def _baglantiyi_kapat(konak: str) -> None:
    havuz = getattr(_yerel, "havuz", None)
    if havuz and konak in havuz:
        try:
            havuz[konak].close()
        except Exception:
            pass
        del havuz[konak]


def baglantilari_kapat() -> None:
    """Is parcacigi isini bitirince kendi baglantilarini birakir."""
    for konak in list(getattr(_yerel, "havuz", {})):
        _baglantiyi_kapat(konak)


def istek_yap(url: str, zaman_asimi: int = 30) -> tuple[bytes, str]:
    """Kalici baglanti uzerinden GET; (govde, content-type) dondurur.

    Yonlendirmeleri kendisi izler. 2xx disi yanitta `urllib.error.HTTPError`
    firlatir -- cagiran taraftaki `e.code` denetimleri (403/429 geri cekilmesi)
    boylece oldugu gibi calismaya devam eder.
    """
    gorulen = 0
    while True:
        parca = urllib.parse.urlsplit(url)
        konak = parca.netloc
        guvenli = parca.scheme != "http"
        yol = urllib.parse.urlunsplit(("", "", parca.path or "/", parca.query, ""))
        basliklar = {
            "User-Agent": ayiklayici.TARAYICI,
            "Accept-Language": "tr,en;q=0.8",
            "Accept-Encoding": "gzip",
            "Connection": "keep-alive",
        }

        yanit = None
        for deneme in (1, 2):
            baglanti = _baglanti(konak, guvenli, zaman_asimi)
            try:
                baglanti.request("GET", yol, headers=basliklar)
                yanit = baglanti.getresponse()
                govde = yanit.read()
                break
            except (http.client.HTTPException, OSError, socket.timeout):
                # Bayat baglanti: karsi taraf sessizce kapatmis olabilir.
                # Bir kez yeni baglantiyla tekrar denenir.
                _baglantiyi_kapat(konak)
                if deneme == 2:
                    raise
        if yanit.headers.get("Content-Encoding") == "gzip":
            try:
                govde = gzip.decompress(govde)
            except (OSError, EOFError):
                pass

        if yanit.status in (301, 302, 303, 307, 308):
            hedef = yanit.headers.get("Location")
            gorulen += 1
            if hedef and gorulen <= EN_COK_YONLENDIRME:
                url = urllib.parse.urljoin(url, hedef)
                continue
        if not 200 <= yanit.status < 300:
            raise urllib.error.HTTPError(
                url, yanit.status, yanit.reason, yanit.headers, None)
        return govde, yanit.headers.get("Content-Type", "")


def _cozumle(govde: bytes, icerik_turu: str) -> str:
    """`ayiklayici.getir` ile ayni kodlama sirasi -- o dosya degistirilmiyor."""
    tur = None
    for parca in icerik_turu.split(";"):
        parca = parca.strip()
        if parca.lower().startswith("charset="):
            tur = parca.split("=", 1)[1].strip().strip('"')
    for kodlama in filter(None, [tur, "utf-8", "windows-1254", "latin-1"]):
        try:
            return govde.decode(kodlama)
        except (UnicodeDecodeError, LookupError):
            continue
    return govde.decode("utf-8", errors="replace")


def _getir_ham(url: str, zaman_asimi: int = 30) -> bytes:
    return istek_yap(url, zaman_asimi)[0]


def _sayfa_metni(url: str, zaman_asimi: int = 30) -> str:
    govde, tur = istek_yap(url, zaman_asimi)
    return _cozumle(govde, tur)


def sitemap_ay_dosyalari() -> list[str]:
    onek = AILELER[AILE]["onek"]
    ham = _getir_ham(SITEMAP_INDEX).decode("utf-8", errors="replace")
    tumu = re.findall(r"<loc>([^<]+)</loc>", ham)
    desen = re.compile(r"/%s_\d{4}-\d{2}\.xml$" % re.escape(onek))
    return sorted(u for u in tumu if desen.search(u))


def sitemap_url_kur(zorla: bool = False) -> int:
    """tum-urller.jsonl dosyasini kurar/yeniler, toplam url sayisini dondurur."""
    if URL_LISTESI.exists() and not zorla:
        with open(URL_LISTESI, "r", encoding="utf-8-sig") as f:
            return sum(1 for _ in f)

    log("Sitemap indeksi indiriliyor...")
    aylar = sitemap_ay_dosyalari()
    log(f"{len(aylar)} aylik {AILELER[AILE]['ad']} sitemap'i bulundu.")

    gorulen: set[str] = set()
    with open(URL_LISTESI, "w", encoding="utf-8") as cikti:
        for i, ay_url in enumerate(aylar, 1):
            ay_adi = re.search(r"_(\d{4}-\d{2})\.xml$", ay_url).group(1)
            try:
                ham = _getir_ham(ay_url).decode("utf-8", errors="replace")
            except Exception as e:
                log(f"UYARI: {ay_url} indirilemedi ({e}), atlaniyor.")
                continue
            ciftler = re.findall(
                r"<url>\s*<loc>([^<]+)</loc>\s*<lastmod>([^<]*)</lastmod>", ham
            )
            yeni = 0
            for url, lastmod in ciftler:
                if url in gorulen:
                    continue
                gorulen.add(url)
                cikti.write(json.dumps(
                    {"url": url, "lastmod": lastmod, "ay": ay_adi},
                    ensure_ascii=False,
                ) + "\n")
                yeni += 1
            log(f"  [{i}/{len(aylar)}] {ay_adi}: {yeni} adres")

    log(f"Sitemap tarama tamamlandi: {len(gorulen)} benzersiz adres.")
    return len(gorulen)


# -- tek haber isleme -------------------------------------------------------

_SON_ID = re.compile(r"-(\d+)/?$")


def id_kategori_cikar(url: str) -> tuple[int | None, str]:
    if AILE == "haber":
        esle = _ID_KATEGORI.search(url)
        if not esle:
            return None, ""
        return int(esle.group(2)), esle.group(1)
    # kose/video/galeri/yazar: kimlik her zaman yolun son sayisi.
    # Kategori/yazar dilimi ayrica ayiklayicida saklanir.
    esle = _SON_ID.search(url.rstrip("/"))
    if not esle:
        return None, ""
    dilim = url.rstrip("/").split("/")
    ust = dilim[-2] if len(dilim) >= 2 else ""
    return int(esle.group(1)), ust


def zaten_islendi_mi(ay: str, id_: int) -> bool:
    return (VERI_KOK / ay / f"{id_}.json").exists()


# Gecici sayilan ve geri cekilerek TEKRAR DENENEN yanit kodlari.
# 403/429 hiz siniri; 5xx ag gecidi hatalari (Cloudflare origin'e ulasamiyor).
#
# 502 NEDEN BURADA (29 Agustos 2026'da olculdu). Once yalniz 403/429 tekrar
# deneniyordu, 502 aninda basarisiz sayiliyordu. Olcum: dakikada 550-700 kayit
# cekilirken hata orani **%0**, ama 13:30'da BIR dakika suren origin kesintisi
# 479 kaydi birden dusurdu (%80) ve sonraki dakikada oran yine %0'a dondu.
# Yani 502 kalici bir red degil, gecici bir dalgalanma; geri cekilip tekrar
# denemek hem o kayitlari kurtariyor hem de kesinti aninda yuku azaltiyor.
GECICI_KODLAR = (403, 429, 502, 503, 504)


def sayfa_indir(url: str) -> str | None:
    for deneme in range(1, DENEME_SAYISI + 1):
        try:
            return _sayfa_metni(url)
        except urllib.error.HTTPError as e:
            if e.code in GECICI_KODLAR and deneme < DENEME_SAYISI:
                bekle = 5 * deneme + random.uniform(0, 3)
                log(f"  {url} -> HTTP {e.code}, {bekle:.0f}sn sonra tekrar denenecek.")
                time.sleep(bekle)
                continue
            basarisiz_kaydet(url, f"HTTP {e.code}")
            return None
        except Exception as e:
            if deneme < DENEME_SAYISI:
                time.sleep(3 * deneme)
                continue
            basarisiz_kaydet(url, str(e))
            return None
    return None


def haberi_ayikla(html: str, url: str, lastmod: str = "") -> dict:
    taban = ayiklayici.ayikla(html, url)

    ayristirici = ayiklayici._Toplayici()
    try:
        ayristirici.feed(html)
    except Exception:
        pass
    ld = ayiklayici._jsonld_haber(ayristirici.jsonld)

    govde_html = ld.get("articleBody") if isinstance(ld.get("articleBody"), str) else ""
    if not govde_html and taban.get("orijinal_govde"):
        govde_html = "".join(f"<p>{p}</p>\n" for p in taban["orijinal_govde"].split("\n\n"))

    ek_gorseller = []
    if govde_html:
        for aday in _IMG_SRC.findall(govde_html):
            aday = aday.strip()
            if aday and not aday.startswith("data:") and aday != taban.get("gorsel_url"):
                ek_gorseller.append(aday)

    video_url = ""
    video_esle = _VIDEO_SRC.search(html)
    if video_esle:
        video_url = video_esle.group(1)

    kaynak_p = _KAYNAK_P.search(html)
    kaynak = taban.get("asil_kaynak") or (kaynak_p.group(1).strip() if kaynak_p else "")

    id_, kategori = id_kategori_cikar(url)

    yayin_tarihi = (
        taban.get("yayin_tarihi")
        or ayiklayici._duz(ld.get("dateCreated"))
        or lastmod
        or ""
    )

    return {
        "id": id_,
        "url": url,
        "kategori": kategori,
        "kategori_etiketi": ld.get("articleSection", ""),
        "baslik": taban.get("orijinal_baslik", ""),
        "spot": taban.get("orijinal_spot", ""),
        "govde_html": govde_html,
        "govde_metin": taban.get("orijinal_govde", ""),
        "yazar": taban.get("yazar", ""),
        "kaynak": kaynak,
        "yayinci": taban.get("kaynak_adi", ""),
        "yayin_tarihi": yayin_tarihi,
        "guncelleme_tarihi": taban.get("guncelleme_tarihi", ""),
        "anahtar_kelimeler": ld.get("keywords", ""),
        "kelime_sayisi": taban.get("kelime_sayisi", 0),
        "gorsel_url": taban.get("gorsel_url", ""),
        "gorsel_alt": taban.get("gorsel_alt", ""),
        "ek_gorseller": ek_gorseller,
        "video_url": video_url,
        "ayiklama_yontemleri": taban.get("ayiklama_yontemleri", []),
        "ayiklama_guveni": taban.get("ayiklama_guveni", ""),
        "yerel_gorseller": [],
    }


# Site gorsel duzenini /static/<id>-slug-hash.jpg'dan /static/YYYY/MM/DD/... a tasidi ve
# eski dosyalari sunucudan sildi. Tarihsiz /static/ adresleri istisnasiz 404 donuyor, yani
# her eski haberde bos bir istek + basarisiz.txt yazimi demek. Adresi JSON'da duruyor:
# gorseller baska bir yedekten kurtarilirsa bu kayitlar yeniden eslestirilebilir.
_TARIHLI_GORSEL = re.compile(r"/static/\d{4}/\d{2}/\d{2}/")
TUM_GORSELLERI_DENE = False


# -- haber disi aileler -----------------------------------------------------

def _ld_dugumleri(html: str) -> list:
    """Sayfadaki tum JSON-LD dugumlerini duz liste olarak dondurur."""
    ayristirici = ayiklayici._Toplayici()
    try:
        ayristirici.feed(html)
    except Exception:
        pass
    cikti = []
    for ham in ayristirici.jsonld:
        try:
            veri = json.loads(ham)
        except Exception:
            continue
        for dugum in (veri if isinstance(veri, list) else [veri]):
            if isinstance(dugum, dict):
                cikti.append(dugum)
    return cikti


def _ld_tur(html: str, tur: str) -> dict:
    for dugum in _ld_dugumleri(html):
        if dugum.get("@type") == tur:
            return dugum
    return {}


_H1 = re.compile(r"(?is)<h1[^>]*>(.*?)</h1>")
_OG_BASLIK = re.compile(r'(?is)<meta[^>]+property="og:title"[^>]+content="([^"]*)"')
_SITE_EKI = re.compile(r"\s*[-|]\s*Bursa Hakimiyet\s*$", re.I)
_IFRAME_SRC = re.compile(r'(?is)<iframe[^>]+src="([^"]+)"')


def _og_baslik(html: str) -> str:
    """Galeri ve video sayfalarinda <h1> bos; gercek baslik og:title'da.
    Site eki ve (kose yazilarinda) yazar eki temizlenir."""
    esle = _OG_BASLIK.search(html)
    ham = ayiklayici._etiketsiz(esle.group(1)).strip() if esle else ""
    return _SITE_EKI.sub("", ham).strip()


def _baslik_temizle(baslik: str, yazar: str = "") -> str:
    temiz = _SITE_EKI.sub("", (baslik or "").strip()).strip()
    if yazar:
        temiz = re.sub(r"\s*-\s*%s\s*$" % re.escape(yazar), "", temiz).strip()
    # "... - Namik GOZ" gibi kalan tek yazar ekini de dusur
    temiz = re.sub(r"\s*-\s*[A-ZÇĞİÖŞÜ][\wçğıöşü]+(?:\s+[A-ZÇĞİÖŞÜ]{2,}[\wçğıöşü]*)+\s*$", "", temiz).strip()
    return temiz
_OG_GORSEL = re.compile(r'(?is)<meta[^>]+property="og:image"[^>]+content="([^"]*)"')


def _h1_metni(html: str) -> str:
    esle = _H1.search(html)
    return ayiklayici._etiketsiz(esle.group(1)).strip() if esle else ""


def _og_gorsel(html: str) -> str:
    esle = _OG_GORSEL.search(html)
    return esle.group(1).strip() if esle else ""


def _ust_dilim(url: str) -> str:
    """/videolar/bursa-308/... -> 'bursa-308' (kategori slug + katid)."""
    parcalar = url.rstrip("/").split("/")
    return parcalar[-2] if len(parcalar) >= 2 else ""


def _gomulu_cikar(deger) -> str:
    """embedUrl bazen komple <iframe> HTML'i donuyor; src'yi ayikla."""
    ham = ayiklayici._duz(deger)
    if "<iframe" in ham.lower():
        esle = _IFRAME_SRC.search(ham)
        return esle.group(1).strip() if esle else ""
    return ham


def _mutlak_gorsel(deger) -> str:
    ham = ayiklayici._duz(deger)
    if not ham:
        return ""
    if ham.startswith("http"):
        return ham
    return ""  # goreli parca: guvenilir degil, og:image'a birak


def videoyu_ayikla(html: str, url: str, lastmod: str = "") -> dict:
    ld = _ld_tur(html, "VideoObject")
    kucuk = ld.get("thumbnailUrl") or ""
    if isinstance(kucuk, list):
        kucuk = kucuk[0] if kucuk else ""
    return {
        "tur": "video",
        "url": url,
        "baslik": _baslik_temizle(ayiklayici._duz(ld.get("name")) or _og_baslik(html)),
        "spot": ayiklayici._duz(ld.get("description")),
        "yayin_tarihi": (ayiklayici._duz(ld.get("uploadDate")) or lastmod)[:19],
        "video_url": ayiklayici._duz(ld.get("contentUrl")),
        "gomulu_url": _gomulu_cikar(ld.get("embedUrl")),
        "sure": ayiklayici._duz(ld.get("duration")),
        "kategori_dilimi": _ust_dilim(url),
        # thumbnailUrl bazen uzantisiz goreli parca donuyor; og:image guvenilir.
        "gorsel_url": _mutlak_gorsel(kucuk) or _og_gorsel(html),
        "ek_gorseller": [],
    }


def galeriyi_ayikla(html: str, url: str, lastmod: str = "") -> dict:
    """DIKKAT: galeri kareleri statik HTML'de YOK.

    Olculdu (26 Agustos 2026): galeri sayfasindaki tek ItemList, sitenin
    "son galeriler" kutusudur -- o galerinin fotograflari degil. Kareler
    JavaScript ile geliyor ve sayfada bir ajax/api ucu bulunamadi.
    Bu yuzden buradan yalnizca KAPAK ve kunye alinir; kareler icin ya
    JS calistiran bir tarayici ya da saglayicidan veritabani dokumu gerekir.
    """
    koleksiyon = _ld_tur(html, "CollectionPage")
    aciklama = ayiklayici._duz(koleksiyon.get("description"))
    if aciklama.lower().startswith("description of my image"):
        aciklama = ""  # sitenin kendi sablon yer tutucusu
    return {
        "tur": "galeri",
        "url": url,
        "baslik": _baslik_temizle(_h1_metni(html) or _og_baslik(html)),
        "spot": aciklama,
        "yayin_tarihi": lastmod[:19],
        "kategori_dilimi": _ust_dilim(url),
        "kareler": [],
        "kareler_eksik": True,
        "kareler_notu": "Kareler statik HTML'de yok (JS ile yukleniyor); kapak disi gorseller alinamadi.",
        "gorsel_url": _og_gorsel(html),
        "ek_gorseller": [],
    }


def yazari_ayikla(html: str, url: str, lastmod: str = "") -> dict:
    """Yazar sayfasinda Person semasi yok; ad h1'de, portre og:image'da.
    Kose yazisi listesi JS ile geliyor, statik HTML'de yok."""
    return {
        "tur": "yazar",
        "url": url,
        "ad": _h1_metni(html),
        "yazar_dilimi": url.rstrip("/").split("/")[-1],
        "yayin_tarihi": lastmod[:19],
        "gorsel_url": _og_gorsel(html),
        "ek_gorseller": [],
    }


def ayikla_dagit(html: str, url: str, lastmod: str = "") -> dict:
    """Aileye gore dogru ayiklayiciyi cagirir.
    'kose' ailesi NewsArticle semasi tasidigi icin haber yolunu kullanir."""
    if AILE in ("haber", "kose"):
        veri = haberi_ayikla(html, url, lastmod)
        if AILE == "kose":
            veri["tur"] = "kose"
            veri["yazar_dilimi"] = _ust_dilim(url)
            # kose basliklari "<baslik> - <Yazar> - Bursa Hakimiyet" bicimindeydi
            veri["baslik"] = _baslik_temizle(veri.get("baslik", ""),
                                             ayiklayici._duz(veri.get("yazar")))
        return veri
    if AILE == "video":
        return videoyu_ayikla(html, url, lastmod)
    if AILE == "galeri":
        return galeriyi_ayikla(html, url, lastmod)
    return yazari_ayikla(html, url, lastmod)


def gorsel_denenmeli_mi(url: str) -> bool:
    """Indirmeye deger mi: tarihsiz /static/ adresleri bos yere denenmez."""
    if TUM_GORSELLERI_DENE or "/static/" not in url:
        return True
    return bool(_TARIHLI_GORSEL.search(url))


def gorsel_indir(url: str, hedef_klasor: Path) -> str:
    if not disk_yeterli_mi():
        return ""
    dosya_adi = url.split("/")[-1].split("?")[0]
    if not dosya_adi:
        return ""
    hedef = hedef_klasor / dosya_adi
    if hedef.exists():
        return hedef.relative_to(KOK).as_posix()
    try:
        ham = _getir_ham(url, zaman_asimi=30)
    except Exception as e:
        basarisiz_kaydet(url, f"gorsel indirilemedi: {e}")
        return ""
    hedef_klasor.mkdir(parents=True, exist_ok=True)
    gecici = hedef.with_suffix(hedef.suffix + ".tmp")
    gecici.write_bytes(ham)
    gecici.replace(hedef)
    return hedef.relative_to(KOK).as_posix()


def haberi_isle_ve_kaydet(kayit: dict) -> str:
    url, ay = kayit["url"], kayit["ay"]
    id_, _ = id_kategori_cikar(url)
    if id_ is None:
        basarisiz_kaydet(url, "id cikarilamadi")
        return "basarisiz"
    if zaten_islendi_mi(ay, id_):
        return "atlandi"

    html = sayfa_indir(url)
    if html is None:
        return "basarisiz"

    veri = ayikla_dagit(html, url, kayit.get("lastmod", ""))
    gercek_ay = (veri.get("yayin_tarihi") or "")[:7] or ay
    if not re.match(r"^\d{4}-\d{2}$", gercek_ay):
        gercek_ay = ay

    gorsel_klasor = GORSEL_KOK / gercek_ay
    yerel_gorseller = []
    for g_url in filter(None, [veri["gorsel_url"], *veri["ek_gorseller"]]):
        if not gorsel_denenmeli_mi(g_url):
            continue
        yerel = gorsel_indir(g_url, gorsel_klasor)
        if yerel:
            yerel_gorseller.append(yerel)
    veri["yerel_gorseller"] = yerel_gorseller

    veri_klasor = VERI_KOK / gercek_ay
    veri_klasor.mkdir(parents=True, exist_ok=True)
    hedef = veri_klasor / f"{id_}.json"
    gecici = hedef.with_suffix(".tmp")
    gecici.write_text(json.dumps(veri, ensure_ascii=False, indent=2), encoding="utf-8")
    gecici.replace(hedef)
    return "tamamlandi"


# -- ana dongu --------------------------------------------------------------

def ilerleme_yaz(toplam: int, tamamlanan: int, atlanan: int, basarisiz: int, baslangic: float) -> None:
    with _kilit_al():
        ILERLEME_DOSYA.write_text(json.dumps({
            "toplam_url": toplam,
            "tamamlanan": tamamlanan,
            "onceden_vardi": atlanan,
            "basarisiz": basarisiz,
            "gecen_saniye": round(time.time() - baslangic),
            "son_guncelleme": datetime.now().isoformat(timespec="seconds"),
        }, ensure_ascii=False, indent=2), encoding="utf-8")


def calistir(sitemap_yenile: bool, sinirla: int | None) -> None:
    for klasor in (KOK, VERI_KOK, GORSEL_KOK):
        klasor.mkdir(parents=True, exist_ok=True)

    toplam = sitemap_url_kur(zorla=sitemap_yenile)
    log(f"[{AILE}] Toplam {toplam} adres ile calisiliyor (esazamanlilik={ESZAMANLILIK}).")

    kayitlar = []
    with open(URL_LISTESI, "r", encoding="utf-8-sig") as f:
        for satir in f:
            kayitlar.append(json.loads(satir))
    if sinirla:
        kayitlar = kayitlar[:sinirla]

    baslangic = time.time()
    tamamlanan = atlanan = basarisiz = 0

    if not disk_yeterli_mi():
        return

    with ThreadPoolExecutor(max_workers=ESZAMANLILIK) as havuz:
        gelecekler = {havuz.submit(haberi_isle_ve_kaydet, k): k for k in kayitlar}
        for i, gelecek in enumerate(as_completed(gelecekler), 1):
            k = gelecekler[gelecek]
            try:
                sonuc = gelecek.result()
            except Exception as e:
                sonuc = "basarisiz"
                basarisiz_kaydet(k["url"], f"beklenmeyen hata: {e}")

            if sonuc == "tamamlandi":
                tamamlanan += 1
            elif sonuc == "atlandi":
                atlanan += 1
            else:
                basarisiz += 1

            if i % ILERLEME_ARALIGI == 0 or i == len(kayitlar):
                ilerleme_yaz(len(kayitlar), tamamlanan, atlanan, basarisiz, baslangic)
                log(f"[{i}/{len(kayitlar)}] tamamlanan={tamamlanan} atlanan={atlanan} basarisiz={basarisiz}")
                if not disk_yeterli_mi():
                    log("Disk alani yetersiz, kalan islerin tamamlanmasi beklenmeden durduruluyor.")
                    break

    log(f"Bitti. tamamlanan={tamamlanan} atlanan={atlanan} basarisiz={basarisiz}")


if __name__ == "__main__":
    ayristi = argparse.ArgumentParser(description=__doc__)
    ayristi.add_argument("--aile", default="haber", choices=sorted(AILELER),
                         help="hangi icerik ailesi taranacak (varsayilan: haber)")
    ayristi.add_argument("--sitemap-yenile", action="store_true", help="url listesini yeniden kurar")
    ayristi.add_argument("--sinirla", type=int, default=None, help="yalnizca ilk N haberi isler (deneme icin)")
    ayristi.add_argument("--tum-gorselleri-dene", action="store_true",
                         help="silinmis eski gorselleri de dener (varsayilan: tarihsiz adresler atlanir)")
    ayristi.add_argument("--kok", default=None,
                         help=f"cikti kokunu degistirir (varsayilan: {VARSAYILAN_KOK}, ortam: BH_ARSIV_KOK)")
    argumanlar = ayristi.parse_args()

    # Aile YOLLARI belirledigi icin kok_ayarla'dan ONCE kurulmali.
    AILE = argumanlar.aile
    kok_ayarla(argumanlar.kok or os.environ.get("BH_ARSIV_KOK", VARSAYILAN_KOK))
    TUM_GORSELLERI_DENE = argumanlar.tum_gorselleri_dene

    KOK.mkdir(parents=True, exist_ok=True)
    print(f"Cikti koku: {KOK}   aile: {AILE} ({AILELER[AILE]['ad']})")
    print(f"Url listesi: {URL_LISTESI.name}   veri: {VERI_KOK.name}")
    try:
        calistir(argumanlar.sitemap_yenile, argumanlar.sinirla)
    except KeyboardInterrupt:
        log("Kullanici tarafindan durduruldu. Tekrar calistirinca kaldigi yerden devam eder.")
