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
import json
import os
import random
import re
import sys
import time
import urllib.error
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
    VERI_KOK = KOK / "veri"
    GORSEL_KOK = KOK / "gorseller"
    URL_LISTESI = KOK / "tum-urller.jsonl"
    ILERLEME_DOSYA = KOK / "ilerleme.json"
    LOG_DOSYA = KOK / "log.txt"
    BASARISIZ_DOSYA = KOK / "basarisiz.txt"


kok_ayarla(os.environ.get("BH_ARSIV_KOK", VARSAYILAN_KOK))

SITEMAP_INDEX = "https://www.bursahakimiyet.com.tr/static/sitemap/sitemap.xml"
DISK_GUVENLI_ESIK_GB = 10
ESZAMANLILIK = 10
DENEME_SAYISI = 3
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

def _getir_ham(url: str, zaman_asimi: int = 30) -> bytes:
    istek = urllib.request.Request(url, headers={
        "User-Agent": ayiklayici.TARAYICI,
        "Accept-Language": "tr,en;q=0.8",
    })
    with urllib.request.urlopen(istek, timeout=zaman_asimi) as yanit:
        return yanit.read()


def sitemap_ay_dosyalari() -> list[str]:
    ham = _getir_ham(SITEMAP_INDEX).decode("utf-8", errors="replace")
    tumu = re.findall(r"<loc>([^<]+)</loc>", ham)
    return sorted(u for u in tumu if re.search(r"/news_\d{4}-\d{2}\.xml$", u))


def sitemap_url_kur(zorla: bool = False) -> int:
    """tum-urller.jsonl dosyasini kurar/yeniler, toplam url sayisini dondurur."""
    if URL_LISTESI.exists() and not zorla:
        with open(URL_LISTESI, "r", encoding="utf-8-sig") as f:
            return sum(1 for _ in f)

    log("Sitemap indeksi indiriliyor...")
    aylar = sitemap_ay_dosyalari()
    log(f"{len(aylar)} aylik haber sitemap'i bulundu.")

    gorulen: set[str] = set()
    with open(URL_LISTESI, "w", encoding="utf-8") as cikti:
        for i, ay_url in enumerate(aylar, 1):
            ay_adi = re.search(r"news_(\d{4}-\d{2})\.xml$", ay_url).group(1)
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
            log(f"  [{i}/{len(aylar)}] {ay_adi}: {yeni} haber")

    log(f"Sitemap tarama tamamlandi: {len(gorulen)} benzersiz haber adresi.")
    return len(gorulen)


# -- tek haber isleme -------------------------------------------------------

def id_kategori_cikar(url: str) -> tuple[int | None, str]:
    esle = _ID_KATEGORI.search(url)
    if not esle:
        return None, ""
    return int(esle.group(2)), esle.group(1)


def zaten_islendi_mi(ay: str, id_: int) -> bool:
    return (VERI_KOK / ay / f"{id_}.json").exists()


def sayfa_indir(url: str) -> str | None:
    for deneme in range(1, DENEME_SAYISI + 1):
        try:
            return ayiklayici.getir(url)
        except urllib.error.HTTPError as e:
            if e.code in (403, 429) and deneme < DENEME_SAYISI:
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

    veri = haberi_ayikla(html, url, kayit.get("lastmod", ""))
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
    log(f"Toplam {toplam} haber adresi ile calisiliyor (esazamanlilik={ESZAMANLILIK}).")

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
    ayristi.add_argument("--sitemap-yenile", action="store_true", help="url listesini yeniden kurar")
    ayristi.add_argument("--sinirla", type=int, default=None, help="yalnizca ilk N haberi isler (deneme icin)")
    ayristi.add_argument("--tum-gorselleri-dene", action="store_true",
                         help="silinmis eski gorselleri de dener (varsayilan: tarihsiz adresler atlanir)")
    ayristi.add_argument("--kok", default=None,
                         help=f"cikti kokunu degistirir (varsayilan: {VARSAYILAN_KOK}, ortam: BH_ARSIV_KOK)")
    argumanlar = ayristi.parse_args()

    if argumanlar.kok:
        kok_ayarla(argumanlar.kok)
    TUM_GORSELLERI_DENE = argumanlar.tum_gorselleri_dene

    KOK.mkdir(parents=True, exist_ok=True)
    print(f"Cikti koku: {KOK}")
    try:
        calistir(argumanlar.sitemap_yenile, argumanlar.sinirla)
    except KeyboardInterrupt:
        log("Kullanici tarafindan durduruldu. Tekrar calistirinca kaldigi yerden devam eder.")
