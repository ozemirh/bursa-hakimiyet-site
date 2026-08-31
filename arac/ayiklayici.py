"""Haber sayfasindan yapilandirilmis kaynak verisi cikarir.

Sadece Python standart kutuphanesini kullanir. Sirayla dener:
  1. JSON-LD (NewsArticle / Article / ReportageNewsArticle)
  2. OpenGraph ve Twitter meta etiketleri
  3. <p> yogunluguna dayali govde sezgisi

Disari verdigi sozluk `haber_taslak.py` tarafindan kullanilir.
"""

from __future__ import annotations

import gzip
import io
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from html import unescape
from html.parser import HTMLParser
from pathlib import Path

TARAYICI = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)

# Govde disinda kalmasi gereken bloklar
ATLANACAK = {
    "script", "style", "noscript", "nav", "header", "footer",
    "aside", "form", "figure", "figcaption", "iframe", "svg", "button",
}

# Reklam / ilgili haber / abonelik bloklarini ele veren sinif adlari
GURULTU = re.compile(
    r"(reklam|advert|banner|ilgili|related|abone|subscri|newsletter|bulten"
    r"|paylas|share|social|yorum|comment|etiket|tag-|breadcrumb|kirinti"
    r"|cok-okunan|populer|popular|menu|footer|header|sidebar|widget)",
    re.I,
)


class _Toplayici(HTMLParser):
    """Sayfayi tek gecisde ayristirir: meta, JSON-LD, gorseller ve paragraflar."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.metalar: dict[str, str] = {}
        self.jsonld: list[str] = []
        self.baslik_etiketi = ""
        self.gorseller: list[dict] = []
        self.paragraflar: list[tuple[str, str, str]] = []  # (etiket, sinif_zinciri, metin)

        self._yigin: list[tuple[str, str]] = []  # (etiket, sinif)
        self._tampon: list[str] = []
        self._acik: str | None = None
        self._jsonld_acik = False
        self._title_acik = False

    # -- yardimcilar -------------------------------------------------
    def _sinif_zinciri(self) -> str:
        return " ".join(s for _, s in self._yigin if s)

    def _atlaniyor_mu(self) -> bool:
        return any(e in ATLANACAK for e, _ in self._yigin)

    def _kapat_metin(self) -> None:
        if self._acik and self._tampon:
            metin = re.sub(r"\s+", " ", "".join(self._tampon)).strip()
            if metin:
                self.paragraflar.append((self._acik, self._sinif_zinciri(), metin))
        self._acik = None
        self._tampon = []

    # -- HTMLParser kancalari ---------------------------------------
    def handle_starttag(self, etiket, oznitelikler):
        o = {k.lower(): (v or "") for k, v in oznitelikler}
        self._yigin.append((etiket, o.get("class", "")))

        if etiket == "meta":
            ad = (o.get("property") or o.get("name") or "").lower()
            if ad and o.get("content"):
                self.metalar.setdefault(ad, o["content"])

        elif etiket == "script" and "ld+json" in o.get("type", "").lower():
            self._jsonld_acik = True
            self._tampon = []

        elif etiket == "title":
            self._title_acik = True
            self._tampon = []

        elif etiket == "img" and not self._atlaniyor_mu():
            kaynak = (
                o.get("src") or o.get("data-src") or o.get("data-original")
                or o.get("data-lazy-src") or ""
            )
            if kaynak and not kaynak.startswith("data:"):
                self.gorseller.append({
                    "url": kaynak,
                    "alt": o.get("alt", ""),
                    "genislik": o.get("width", ""),
                    "sinif": o.get("class", ""),
                })

        elif etiket in ("p", "h2", "h3", "blockquote", "li") and not self._atlaniyor_mu():
            self._kapat_metin()
            self._acik = etiket
            self._tampon = []

    def handle_endtag(self, etiket):
        if etiket == "script" and self._jsonld_acik:
            self.jsonld.append("".join(self._tampon))
            self._jsonld_acik = False
            self._tampon = []
        elif etiket == "title" and self._title_acik:
            self.baslik_etiketi = re.sub(r"\s+", " ", "".join(self._tampon)).strip()
            self._title_acik = False
            self._tampon = []
        elif etiket == self._acik:
            self._kapat_metin()

        for i in range(len(self._yigin) - 1, -1, -1):
            if self._yigin[i][0] == etiket:
                del self._yigin[i:]
                break

    def handle_data(self, veri):
        if self._jsonld_acik or self._title_acik or self._acik:
            self._tampon.append(veri)


# -- ag ---------------------------------------------------------------

def getir(url: str, zaman_asimi: int = 30) -> str:
    """Sayfayi indirir ve metin olarak dondurur."""
    istek = urllib.request.Request(url, headers={
        "User-Agent": TARAYICI,
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "tr,en;q=0.8",
        "Accept-Encoding": "gzip",
    })
    with urllib.request.urlopen(istek, timeout=zaman_asimi) as yanit:
        ham = yanit.read()
        if yanit.headers.get("Content-Encoding") == "gzip":
            ham = gzip.decompress(ham)
        tur = yanit.headers.get_content_charset()
    for kodlama in filter(None, [tur, "utf-8", "windows-1254", "latin-1"]):
        try:
            return ham.decode(kodlama)
        except (UnicodeDecodeError, LookupError):
            continue
    return ham.decode("utf-8", errors="replace")


# -- JSON-LD ----------------------------------------------------------

def _jsonld_haber(bloklar: list[str]) -> dict:
    """JSON-LD bloklari icinden haber nesnesini bulur."""
    ilgili = {"newsarticle", "article", "reportagenewsarticle", "blogposting"}

    def gez(dugum):
        if isinstance(dugum, list):
            for x in dugum:
                sonuc = gez(x)
                if sonuc:
                    return sonuc
        elif isinstance(dugum, dict):
            tur = dugum.get("@type", "")
            turler = [tur] if isinstance(tur, str) else list(tur or [])
            if any(str(t).lower() in ilgili for t in turler):
                return dugum
            for anahtar in ("@graph", "mainEntity", "itemListElement"):
                if anahtar in dugum:
                    sonuc = gez(dugum[anahtar])
                    if sonuc:
                        return sonuc
        return None

    for ham in bloklar:
        try:
            veri = json.loads(ham.strip())
        except (json.JSONDecodeError, ValueError):
            continue
        bulunan = gez(veri)
        if bulunan:
            return bulunan
    return {}


def _duz(deger) -> str:
    """JSON-LD alanlarindaki degisken sekilleri tek bir metne indirger."""
    if isinstance(deger, str):
        return deger.strip()
    if isinstance(deger, dict):
        for anahtar in ("name", "url", "@id", "contentUrl", "headline"):
            if deger.get(anahtar):
                return _duz(deger[anahtar])
    if isinstance(deger, list) and deger:
        return _duz(deger[0])
    return ""


def _isim(deger) -> str:
    """Yazar/yayinci alanlarindan yalnizca insan okunur adi alir.

    JSON-LD'de bu alanlar sik sik yalnizca @id tasir; URL dondurmek yerine
    bos donup meta etiketlerine dusmek daha dogru sonuc veriyor.
    """
    if isinstance(deger, dict):
        for anahtar in ("name", "legalName", "alternateName"):
            if isinstance(deger.get(anahtar), str) and deger[anahtar].strip():
                return deger[anahtar].strip()
        return ""
    if isinstance(deger, list) and deger:
        return _isim(deger[0])
    if isinstance(deger, str):
        d = deger.strip()
        return "" if re.match(r"https?://|^#", d) else d
    return ""


def _gorsel_adayi(deger) -> str:
    """JSON-LD image alanindan gercek bir gorsel adresi cikarmayi dener."""
    if isinstance(deger, list) and deger:
        for x in deger:
            bulunan = _gorsel_adayi(x)
            if bulunan:
                return bulunan
        return ""
    if isinstance(deger, dict):
        for anahtar in ("url", "contentUrl"):
            if isinstance(deger.get(anahtar), str):
                return _gorsel_adayi(deger[anahtar])
        return ""
    if not isinstance(deger, str):
        return ""
    d = deger.strip()
    if not d or "#" in d:          # "...html#primaryimage" gibi @id degerleri
        return ""
    return d if re.search(r"\.(jpe?g|png|webp|avif|gif)(\?|$)", d, re.I) else ""


def _etiketsiz(metin: str) -> str:
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", metin or ""))).strip()


# -- ana giris --------------------------------------------------------

_KAYNAK_SATIRI = re.compile(
    r"[Kk]aynak\s*[:\-–]\s*([A-Za-z0-9ÇĞİÖŞÜçğıöşü .\'&/]{2,40})")
_PARANTEZ_AJANS = re.compile(r"[(\[]\s*([A-ZÇĞİÖŞÜ]{2,6})\s*[)\]]")


def _ajanslar() -> list[str]:
    """Sozlukteki ajans listesi. Sozluk okunamazsa bos doner, akis durmaz."""
    try:
        yol = Path(__file__).resolve().parent / "sozluk.json"
        return json.loads(yol.read_text(encoding="utf-8")).get("ajanslar", [])
    except Exception:
        return []


def asil_kaynak_bul(html: str, govde: str, yazar: str) -> str:
    """Sayfanin KENDI belirttigi kaynak. Bulunamazsa bos doner.

    Haber siteleri kaynagi uc bicimde yaziyor: acik "Kaynak: AA" satiri, govde
    sonunda parantezli ajans kodu "(DHA)", ya da yazar alanina ajans adi. Ucu de
    aranir; ajans listesiyle eslesen kanonik ada cevrilir.
    """
    ajanslar = _ajanslar()
    kucuk_ajans = {a.lower(): a for a in ajanslar}

    def kanon(deger: str) -> str:
        d = " ".join((deger or "").split()).strip(" .,:;-")
        if not d:
            return ""
        if d.lower() in kucuk_ajans:
            return kucuk_ajans[d.lower()]
        for a in ajanslar:                      # "AA muhabirine gore" gibi
            if a.lower() in d.lower().split():
                return a
        return d

    for kaynak_metni in (govde, html):
        esle = _KAYNAK_SATIRI.search(kaynak_metni or "")
        if esle:
            bulunan = kanon(esle.group(1))
            if bulunan:
                return bulunan

    esle = _PARANTEZ_AJANS.search(govde or "")
    if esle and esle.group(1).lower() in kucuk_ajans:
        return kucuk_ajans[esle.group(1).lower()]

    return kanon(yazar) if kanon(yazar) in ajanslar else ""


def ayikla(html: str, url: str) -> dict:
    """Sayfa kaynagindan yapilandirilmis haber verisi cikarir."""
    ayristirici = _Toplayici()
    try:
        ayristirici.feed(html)
    except Exception:
        pass  # bozuk isaretlemede o ana kadar toplananla devam et

    meta = ayristirici.metalar
    ld = _jsonld_haber(ayristirici.jsonld)
    alan = urllib.parse.urlparse(url).netloc.replace("www.", "")
    yontemler: list[str] = []

    # basliklar
    baslik = _duz(ld.get("headline")) or meta.get("og:title", "") or meta.get("twitter:title", "")
    if baslik:
        yontemler.append("jsonld:headline" if ld.get("headline") else "og:title")
    else:
        baslik = re.split(r"\s+[|\-–]\s+", ayristirici.baslik_etiketi)[0]
        if baslik:
            yontemler.append("title")

    # spot
    spot = (
        _duz(ld.get("description"))
        or meta.get("og:description", "")
        or meta.get("description", "")
        or meta.get("twitter:description", "")
    )
    if spot:
        yontemler.append("jsonld:description" if ld.get("description") else "og:description")

    # govde -- iki aday: JSON-LD articleBody ve paragraf sezgisi.
    #
    # ESKIDEN 400 karakterin altindaki articleBody tumden atiliyordu; eski
    # sayfalarda (2014-2016 duzeni) paragraf sezgisi de tutmadigi icin haber
    # GOVDESIZ kaliyordu -- 31 Agustos 2026'da 1.000 haberlik ornekte 2015
    # icin %21, 2016 icin %12 olculdu. Artik sezgi bos donerse kisa
    # adayi son care olarak kullaniliyor. 400 esigi ve articleBody tercihi
    # aynen duruyor -- modern sayfalarda davranis degismiyor.
    ld_govde = _etiketsiz(_duz(ld.get("articleBody")))
    if ld_govde and len(ld_govde) > 400:
        govde = ld_govde
        yontemler.append("jsonld:articleBody")
    else:
        govde = _govde_sezgisi(ayristirici.paragraflar)
        if govde:
            yontemler.append("paragraf-sezgisi")
        elif ld_govde:
            # Son care: sezgi bos dondu, elimizde kisa da olsa articleBody var.
            govde = ld_govde
            yontemler.append("jsonld:articleBody")

    # gorsel — JSON-LD'de image alani sik sik yalnizca @id tasir ve bu @id
    # sayfanin kendi adresi olur ("...html#primaryimage"). Gercek bir gorsele
    # benzemiyorsa meta etiketlerine ve sezgiye dusuyoruz.
    gorsel = ""
    for aday, etiket in (
        (_gorsel_adayi(ld.get("image")), "jsonld:image"),
        (meta.get("og:image", ""), "og:image"),
        (meta.get("twitter:image", ""), "twitter:image"),
        (_en_iyi_gorsel(ayristirici.gorseller), "img-sezgisi"),
    ):
        if aday:
            gorsel = aday
            yontemler.append(etiket)
            break
    if gorsel:
        gorsel = urllib.parse.urljoin(url, gorsel)

    # yazar / tarih / kaynak
    yazar = _isim(ld.get("author")) or _isim(meta.get("article:author", "")) or _isim(meta.get("author", ""))
    tarih = (
        _duz(ld.get("datePublished"))
        or meta.get("article:published_time", "")
        or meta.get("date", "")
    )
    guncelleme = _duz(ld.get("dateModified")) or meta.get("article:modified_time", "")
    kaynak_adi = _isim(ld.get("publisher")) or meta.get("og:site_name", "") or alan

    kelime = len(govde.split()) if govde else 0
    return {
        "kaynak_url": url,
        "kaynak_alan": alan,
        "kaynak_adi": kaynak_adi,
        "orijinal_baslik": baslik,
        "orijinal_spot": spot,
        "orijinal_govde": govde,
        "gorsel_url": gorsel,
        "gorsel_alt": next(
            (g["alt"] for g in ayristirici.gorseller if g.get("alt")), ""
        ),
        "yazar": yazar,
        "asil_kaynak": asil_kaynak_bul(html, govde, yazar),
        "yayin_tarihi": tarih,
        "guncelleme_tarihi": guncelleme,
        "dil": meta.get("og:locale", "") or "tr",
        "kelime_sayisi": kelime,
        "ayiklama_yontemleri": yontemler,
        "ayiklama_guveni": _guven(baslik, govde, gorsel, kelime),
    }


def _govde_sezgisi(paragraflar: list[tuple[str, str, str]]) -> str:
    """En cok gercek cumle tasiyan kapsayiciyi secip govdeyi birlestirir."""
    # Gurultu taramasi yalnizca en yakin atalara bakar. Tum ata zincirine
    # bakilirsa, disarida bir yerde "header" sinifi tasiyan her sayfada butun
    # paragraflar elenir ve geriye gezinti seridi kalir.
    adaylar = [
        (etiket, sinif, metin)
        for etiket, sinif, metin in paragraflar
        if not GURULTU.search(" ".join(sinif.split()[-3:]))
        and (etiket != "li" or len(metin) > 120)
    ]
    if not adaylar:
        adaylar = paragraflar

    gruplar: dict[str, list[tuple[str, str]]] = {}
    for etiket, sinif, metin in adaylar:
        if etiket == "p" and len(metin) < 40:
            continue
        # En yakin atalarin sinifiyla grupla. Dis kapsayicilarla gruplanirsa
        # gezinti seridi ile makale ayni gruba duser ve govdeye menu karisir.
        anahtar = " ".join(sinif.split()[-4:])
        gruplar.setdefault(anahtar, []).append((etiket, metin))

    if not gruplar:
        return ""

    def puan(ogeler: list[tuple[str, str]]) -> int:
        """Yalnizca gercek govde cumleleri puan getirir.

        Gezinti seritleri cok sayida kisa baglantidan olusur; uzunluk toplami
        yuksek cikabilir ama cumle tasimazlar. Bu yuzden sadece cumle
        noktalamasi tasiyan uzun paragraflari sayiyoruz.
        """
        return sum(
            len(metin)
            for etiket, metin in ogeler
            if etiket in ("p", "blockquote") and len(metin) >= 80 and re.search(r"[.!?]", metin)
        )

    en_iyi = max(gruplar, key=lambda k: puan(gruplar[k]))
    if puan(gruplar[en_iyi]) == 0:
        return ""
    return "\n\n".join(m for _, m in gruplar[en_iyi]).strip()


def _en_iyi_gorsel(gorseller: list[dict]) -> str:
    """Meta gorseli yoksa sayfadaki en olasi haber gorselini secer."""
    puanli = []
    for g in gorseller:
        if GURULTU.search(g.get("sinif", "")):
            continue
        url = g["url"]
        if re.search(r"(logo|icon|avatar|placeholder|sprite|1x1|pixel)", url, re.I):
            continue
        puan = 0
        try:
            puan += min(int(g.get("genislik") or 0), 2000)
        except ValueError:
            pass
        if g.get("alt"):
            puan += 200
        puanli.append((puan, url))
    if not puanli:
        return ""
    return max(puanli)[1]


def _guven(baslik: str, govde: str, gorsel: str, kelime: int) -> str:
    puan = 0
    if baslik:
        puan += 1
    if kelime >= 150:
        puan += 2
    elif kelime >= 60:
        puan += 1
    if gorsel:
        puan += 1
    return {4: "yuksek", 5: "yuksek", 3: "orta", 2: "orta"}.get(puan, "dusuk")


def coz(url: str) -> dict:
    """Adresi indirip ayiklar. Ag hatalarini anlasilir mesaja cevirir."""
    parcali = urllib.parse.urlparse(url)
    if parcali.scheme not in ("http", "https"):
        raise ValueError(f"Desteklenmeyen adres: {url}")
    try:
        html = getir(url)
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Kaynak {e.code} dondurdu: {url}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"Kaynaga ulasilamadi ({e.reason}): {url}") from e
    return ayikla(html, url)
