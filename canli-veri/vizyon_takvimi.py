"""Turkiye vizyon takvimini ceker: hangi film hangi cuma vizyona giriyor.

Anasayfanin en altindaki "Vizyonda neler var" bilesenini besler.
Ucretli servis kullanilmaz (26 Agustos 2026 karari, URUN-PLANI.md bolum 8).

AFIS UYARISI. Film afisi telifli bir eserdir ve bu betik afis DOSYASI
indirmez. Yalnizca afisin kaynaktaki adresi kunye olarak saklanir
("afis_kaynak"), her kayitta "afis_yayinlanabilir": false yazar. Sayfa
yerel yer tutucu gosterir. Afisi yayina koymak icin hak sahibinden
(dagitimci) yazili izin gerekir; bu betigin isi degildir.

Bes kaynak var, hicbiri otekinin yerine gecmez:

  dagitimci Filmi vizyona sokan DAGITIMCININ kendi duyuru/basin sayfasi:
            Baska Sinema (/basin/) ve Bir Film (/sinemalarda). VARSAYILAN.
            Anahtarsiz. Ikisinde de icerigi kisitlayan kullanim kosullari
            sayfasi YOK ve robots.txt bu yollari acik birakiyor (29 Agustos
            2026 olcumu). Kapsam DAR ve bilerek dar: ulusal takvimin tamami
            degil, yalnizca bu iki dagitimcinin getirdigi filmler.
            Olcum (29 Agustos 2026): 9 film, 6 vizyon gunu.
  tmdb      The Movie Database. Ucretsiz API anahtari ister. ELENDI
            (29 Agustos 2026): TMDB'nin sartlari reklam geliri olan
            siteleri "commercial use" sayiyor ve ayri yazili anlasma
            istiyor; Bursa Hakimiyet reklamli ticari bir gazete. Kod
            duruyor ama varsayilan degil, --kaynak tmdb ile cagrilir.
  vikiveri  Wikidata SPARQL. Anahtarsiz, veri CC0 - hukuken en temiz yol,
            ama VIZYON TAKVIMI ICIN YETERSIZ oldugu olculdu (27 Agustos
            2026). Sorgu dogru calisiyor: P577'ye P291=Q43 niteleyicisi
            girilmis 1.389 film var. Sorun kapsam ve yon:
              yila gore TR vizyon kaydi  2020:87 2021:13 2022:31
              2023:16 2024:33 2025:53 2026:19
              (Turkiye'de yilda ~200-300 film vizyona giriyor -> %10-25)
              2026-06-01 sonrasi TR vizyon kaydi: 5 film, biri gelecek.
            Wikidata GECMISI kaydeder, takvimi onceden yazmaz; bu bilesen
            ise "onumuzdeki haftalar" istiyor. Sorgu penceresini geriye
            cevirmek de kurtarmaz - son 3 ayda 4 film. Capraz dogrulama
            icin durur, yedek olarak GUVENILMEZ.
  boxoffice boxofficeturkiye.com. TR vizyon takviminin en eksiksiz acik
            listesi, ama Kullanim Kosullari madde 14 iceriginin yazili
            izin olmadan cogaltilmasini ve yayinlanmasini yasakliyor.
            Bu yuzden --yazili-izin-var bayragi verilmeden CALISMAZ.
  elle      Panelden elle girilen liste (vizyon-elle.json). Kaynak
            bulunamadiginda ya da dustugunde calisan yol budur.

Elenen kaynaklar ve gerekcesi (29 Agustos 2026 olcumu, URUN-PLANI.md
bolum 31): sinemalar.com, beyazperde.com, biletinial.com, Paribu
Cineverse ve UIP Turkiye'nin HEPSINDE "yazili izin olmadan cogaltilamaz /
yayinlanamaz" maddesi var - Box Office TR madde 14 ile ayni kalip.
TME Films'in robots.txt'si ClaudeBot'a dogrudan "Disallow: /" diyor.

Kullanim:
    python vizyon_takvimi.py                      # dagitimci, 3 ay
    python vizyon_takvimi.py --ay 6
    python vizyon_takvimi.py --kaynak vikiveri    # anahtarsiz
    set TMDB_ANAHTAR=...            # tmdb yolu icin (elendi, bkz. yukari)
    (kalici: canli-veri/gizli.json -> {"TMDB_ANAHTAR": "..."};
     ornegi gizli-ornek.json, dosya .gitignore'da)
    python vizyon_takvimi.py --kaynak elle
    python vizyon_takvimi.py --kaynak boxoffice --yazili-izin-var

Cikti: <kok>/vizyon-takvimi.json ve <kok>/durum-vizyon-takvimi.json

Cikis kodu: 0 taze veri - 2 cekilemedi, onceki dosya korundu -
1 cekilemedi ve elde onceki veri de yok.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.parse
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ortak  # noqa: E402

BILESEN = "vizyon-takvimi"

# Vizyon takvimi haftada bir degisir; bir haftalik gecikme tolere edilir.
BAYAT_ESIK_DAKIKA = 10080  # 7 gun

AFIS_NOTU = ("Afisler teliflidir. Bu dosya afis dosyasi tasimaz; yalnizca "
             "kaynaktaki adresi kunye olarak tutar. Yayinda yerel yer tutucu "
             "kullanilir. Afisi basmak icin dagitimcidan yazili izin gerekir.")

GUNLER = ["pazartesi", "salı", "çarşamba", "perşembe",
          "cuma", "cumartesi", "pazar"]

AYLAR = ["ocak", "subat", "mart", "nisan", "mayis", "haziran",
         "temmuz", "agustos", "eylul", "ekim", "kasim", "aralik"]


# -- ortak bicimlendirme --------------------------------------------------

def film_kaydi(ad: str, tarih: str, **ek) -> dict:
    kayit = {
        "ad": ad,
        "ozgun_ad": ek.get("ozgun_ad", ""),
        "tarih": tarih,
        "tur": ek.get("tur", []),
        "dagitimci": ek.get("dagitimci", ""),
        "ozet": ek.get("ozet", ""),
        "yas_siniri": ek.get("yas_siniri", ""),
        "kaynak_kimlik": ek.get("kaynak_kimlik", ""),
        # Afis DOSYASI indirilmez; yalnizca adres kunye olarak durur.
        "afis_kaynak": ek.get("afis_kaynak", ""),
        "afis_yayinlanabilir": False,
    }
    return kayit


def haftalara_bol(filmler: list[dict]) -> list[dict]:
    """Filmleri vizyon tarihine gore gruplar, tarihe gore siralar."""
    kutu: dict[str, list[dict]] = {}
    for f in filmler:
        kutu.setdefault(f["tarih"], []).append(f)
    cikti = []
    for tarih in sorted(kutu):
        try:
            g = date.fromisoformat(tarih)
            gun = GUNLER[g.weekday()]
        except ValueError:
            gun = ""
        cikti.append({
            "tarih": tarih,
            "gun": gun,
            "filmler": sorted(kutu[tarih], key=lambda x: x["ad"]),
        })
    return cikti


def aralik(ay_sayisi: int) -> tuple[str, str]:
    bas = date.today()
    son = bas
    for _ in range(ay_sayisi):
        son = (son.replace(day=1) + timedelta(days=32)).replace(day=1)
    return bas.isoformat(), (son - timedelta(days=1)).isoformat()


# -- kaynak: TMDB ---------------------------------------------------------

TMDB_KOK = "https://api.themoviedb.org/3"


def _tmdb_json(yol: str, anahtar: str, **parametre):
    parametre["api_key"] = anahtar
    adres = f"{TMDB_KOK}{yol}?{urllib.parse.urlencode(parametre)}"
    return json.loads(ortak.getir(adres))


def tmdb_cek(ay_sayisi: int) -> tuple[list[dict], dict]:
    anahtar = ortak.gizli_oku("TMDB_ANAHTAR")
    if not anahtar:
        raise ortak.CekmeHatasi(
            "TMDB_ANAHTAR bulunamadi (ne ortam degiskeninde ne "
            "canli-veri/gizli.json icinde). themoviedb.org uzerinden "
            "ucretsiz anahtar alinir; ya da --kaynak vikiveri / elle kullanin.")

    bas, son = aralik(ay_sayisi)
    ortak.log(f"  TMDB: {bas} .. {son} (bolge TR, vizyon tipi 3=sinema)")

    turler = {}
    try:
        for t in _tmdb_json("/genre/movie/list", anahtar,
                            language="tr-TR").get("genres", []):
            turler[t["id"]] = t["name"]
        ortak.bekle()
    except Exception as e:  # tur adi olmasa da film listesi ise yarar
        ortak.log(f"  UYARI: tur listesi alinamadi ({e!r}); tur adlari bos kalacak")

    filmler = []
    sayfa = 1
    while True:
        d = _tmdb_json(
            "/discover/movie", anahtar,
            region="TR",
            with_release_type=3,          # 3 = Theatrical
            **{"release_date.gte": bas, "release_date.lte": son},
            language="tr-TR",
            sort_by="primary_release_date.asc",
            page=sayfa,
        )
        for f in d.get("results", []):
            tarih = (f.get("release_date") or "").strip()
            if not tarih or not (bas <= tarih <= son):
                continue
            afis = f.get("poster_path") or ""
            filmler.append(film_kaydi(
                f.get("title") or f.get("original_title") or "",
                tarih,
                ozgun_ad=f.get("original_title", ""),
                tur=[turler[g] for g in f.get("genre_ids", []) if g in turler],
                ozet=(f.get("overview") or "").strip(),
                kaynak_kimlik=f"tmdb:{f.get('id')}",
                afis_kaynak=f"https://image.tmdb.org/t/p/w342{afis}" if afis else "",
            ))
        toplam = d.get("total_pages", 1)
        ortak.log(f"    sayfa {sayfa}/{toplam}: {len(filmler)} film")
        if sayfa >= min(toplam, 20):
            break
        sayfa += 1
        ortak.bekle()

    kaynak = {
        "ad": "The Movie Database",
        "kisa": "TMDB",
        "adres": "https://www.themoviedb.org/",
        "kosullar": "https://www.themoviedb.org/api-terms-of-use",
        # TMDB'nin istedigi kunye; sayfada gorunmesi gerekir.
        "kunye": ("Bu ürün TMDb API'sini kullanır; TMDb tarafından "
                  "onaylanmış veya belgelenmiş değildir."),
    }
    return filmler, kaynak


# -- kaynak: Wikidata -----------------------------------------------------

VIKI_UC = "https://query.wikidata.org/sparql"

VIKI_SORGU = """
SELECT ?film ?filmLabel ?ozgunLabel ?tarih WHERE {
  ?film wdt:P31 wd:Q11424 .
  ?film p:P577 ?st .
  ?st ps:P577 ?tarih .
  ?st pq:P291 wd:Q43 .
  OPTIONAL { ?film wdt:P1476 ?ozgun . }
  FILTER(?tarih >= "%sT00:00:00Z"^^xsd:dateTime &&
         ?tarih <= "%sT23:59:59Z"^^xsd:dateTime)
  SERVICE wikibase:label { bd:serviceParam wikibase:language "tr,en". }
}
ORDER BY ?tarih
LIMIT 500
"""


def vikiveri_cek(ay_sayisi: int) -> tuple[list[dict], dict]:
    bas, son = aralik(ay_sayisi)
    ortak.log(f"  Wikidata: {bas} .. {son}")
    adres = VIKI_UC + "?format=json&query=" + urllib.parse.quote(
        VIKI_SORGU % (bas, son))
    # Wikidata kendini tanitan bir User-Agent ister.
    d = json.loads(ortak.getir(adres, basliklar={
        "Accept": "application/sparql-results+json",
        "User-Agent": "BursaHakimiyet-vizyon/1.0 (+https://www.bursahakimiyet.com.tr/)",
    }, zaman_asimi=60))

    filmler = []
    for s in d["results"]["bindings"]:
        tarih = s["tarih"]["value"][:10]
        kimlik = s["film"]["value"].rsplit("/", 1)[-1]
        filmler.append(film_kaydi(
            s["filmLabel"]["value"],
            tarih,
            ozgun_ad=s.get("ozgunLabel", {}).get("value", ""),
            kaynak_kimlik=f"wikidata:{kimlik}",
        ))
    kaynak = {
        "ad": "Wikidata",
        "kisa": "Wikidata",
        "adres": "https://www.wikidata.org/",
        "kosullar": "https://www.wikidata.org/wiki/Wikidata:Licensing",
        "kunye": "Veri: Wikidata (CC0).",
    }
    return filmler, kaynak


# -- kaynak: boxofficeturkiye (yazili izne bagli) --------------------------

BOX_KOK = "https://boxofficeturkiye.com"

_BOX_GUN = re.compile(
    r"<h3[^>]*>.*?(\d{1,2})\s+([a-zçğıöşü]+)\s*<span[^>]*>([a-zçğıöşü]+)</span>",
    re.S | re.I)
_BOX_FILM = re.compile(r'<div class="calendar-item__movie"(.*?)(?=<div class="calendar-item__movie"|</section|\Z)', re.S)
_BOX_AD = re.compile(r'class="calendar-item__movie-name"><a[^>]*>([^<]+)</a>', re.S)
_BOX_TUR = re.compile(r'class="calendar-item__genre">([^<]*)<', re.S)
_BOX_AFIS = re.compile(r'<img src="(https://static\.boxofficeturkiye\.com/[^"]+)"')
_BOX_SLUG = re.compile(r'href="(/film/[^"]+)"')
_BOX_DAGITIMCI = re.compile(r'Dağıtımcı.*?<span[^>]*>([^<]+)</span>', re.S)


def boxoffice_cek(ay_sayisi: int, izin_var: bool) -> tuple[list[dict], dict]:
    if not izin_var:
        raise ortak.CekmeHatasi(
            "boxofficeturkiye.com Kullanim Kosullari madde 14, icerigin yazili "
            "izin olmadan cogaltilmasini ve yayinlanmasini yasakliyor. Izin "
            "alindiysa --yazili-izin-var ile calistirin.")

    bugun = date.today()
    filmler = []
    for k in range(ay_sayisi):
        y = bugun.year + (bugun.month - 1 + k) // 12
        a = (bugun.month - 1 + k) % 12
        adres = f"{BOX_KOK}/takvim/{y}/{AYLAR[a]}"
        ortak.log(f"  {adres}")
        html = ortak.getir(adres)
        filmler.extend(_boxoffice_ay_ayikla(html, y))
        ortak.bekle()

    kaynak = {
        "ad": "Box Office Türkiye",
        "kisa": "boxofficeturkiye.com",
        "adres": BOX_KOK,
        "kosullar": f"{BOX_KOK}/kurumsal/kullanim-kosullari",
        "kunye": "Kaynak: Box Office Türkiye (yazılı izinle).",
    }
    return filmler, kaynak


def _boxoffice_ay_ayikla(html: str, yil: int) -> list[dict]:
    """Ay sayfasini gun basliklarina bolup her gunun filmlerini okur."""
    isaretler = [(m.start(), m) for m in _BOX_GUN.finditer(html)]
    cikti = []
    for i, (konum, m) in enumerate(isaretler):
        bitis = isaretler[i + 1][0] if i + 1 < len(isaretler) else len(html)
        gun_no = int(m.group(1))
        ay_adi = m.group(2).lower()
        ay_no = _ay_no(ay_adi)
        if not ay_no:
            continue
        tarih = f"{yil:04d}-{ay_no:02d}-{gun_no:02d}"
        for blok in _BOX_FILM.findall(html[konum:bitis]):
            ad = _BOX_AD.search(blok)
            if not ad:
                continue
            slug = _BOX_SLUG.search(blok)
            tur = _BOX_TUR.search(blok)
            afis = _BOX_AFIS.search(blok)
            dag = _BOX_DAGITIMCI.search(blok)
            cikti.append(film_kaydi(
                _coz(ad.group(1)),
                tarih,
                # Kaynak turleri tek hucrede virgulle yaziyor: "Dram, Korku"
                tur=[p.strip() for p in _coz(tur.group(1)).split(",")
                     if p.strip()] if tur else [],
                dagitimci=_coz(dag.group(1)) if dag else "",
                kaynak_kimlik="boxoffice:" + (slug.group(1) if slug else ""),
                afis_kaynak=afis.group(1) if afis else "",
            ))
    return cikti


def _ay_no(ad: str) -> int | None:
    sade = (ad.replace("ş", "s").replace("ğ", "g").replace("ı", "i")
              .replace("ö", "o").replace("ü", "u").replace("ç", "c"))
    return AYLAR.index(sade) + 1 if sade in AYLAR else None


def _coz(s: str) -> str:
    from html import unescape
    return re.sub(r"\s+", " ", unescape(s)).strip()


# -- kaynak: dagitimci duyuru/basin sayfalari -----------------------------
#
# Turkiye vizyon takvimini yayimlayan portallarin HEPSINDE ayni kalipta
# "yazili izin olmadan cogaltilamaz / yayinlanamaz" maddesi cikti: Box
# Office TR (madde 14), sinemalar.com, beyazperde.com (madde 3.12),
# biletinial.com, Paribu Cineverse (madde 2), UIP Turkiye. Olcum
# URUN-PLANI.md bolum 31'de. Bu yuzden hicbiri kullanilmiyor.
#
# Buradaki iki kaynak hukuken farkli bir seydir: filmi vizyona sokan
# DAGITIMCININ kendi duyuru/basin sayfasi. "Filmimiz su tarihte vizyonda"
# duyurusu zaten basinin yayinlamasi icin yapilir. Ikisinde de icerigin
# kullanimini kisitlayan bir kullanim kosullari sayfasi YOK (site
# haritalarinin tamami tarandi) ve robots.txt bu yollari acik birakiyor.
# Olcum tarihi 29 Agustos 2026.
#
# TME Films'e (tmefilm.com) BILEREK gidilmiyor: robots.txt'sinde
# "User-agent: ClaudeBot -> Disallow: /" var.
#
# Kapsam bilerek dar: yalnizca bu iki dagitimcinin getirdigi filmler.
# Listede olmayan film UYDURULMAZ.

BASKA_KOK = "http://www.baskasinema.com"
BIR_KOK = "https://www.birfilm.net"

# Bir Film'de her film ayri sayfada; bir kosuda acilacak azami sayfa.
BIR_AZAMI_SAYFA = 25

# Baska Sinema: WordPress, film bloklari tek kalipta basiliyor.
_BS_BLOK = re.compile(r'<div class="movie_box.*?(?=<div class="movie_box|\Z)', re.S)
_BS_AD = re.compile(r'class="movie_title"[^>]*><span>(.*?)</span>', re.S)
_BS_SLUG = re.compile(r'href="[^"]*/filmler/([^"/]+)/"')
_BS_TARIH = re.compile(r'<strong>\s*(\d{1,2})\s+([^\s<]+)\s+(\d{4})\s*</strong>')
_BS_TUR = re.compile(r'Tür:\s*([^<]*)')

# Bir Film: Wix galerisi. Baglanti film sayfasina, aciklama vizyon gunune.
_BF_OGE = re.compile(
    r'href="(https://www\.birfilm\.net/sinemalarda-[^"]+)"(?:.{0,4000}?)'
    r'gallery-item-description"[^>]*>([^<]*)<', re.S)
_BF_GUN = re.compile("(\\d{1,2})\\s+([^\\s<\u2019']+)")
_BF_TARIH = re.compile(r"Vizyon Tarihi:\s*(\d{1,2})\s+(\S+)\s+(\d{4})")


def _satirlar(html_metni: str) -> list[str]:
    """Sayfayi duz metin satirlarina indirger.

    Bir Film'in sayfasinda "Tur:" etiketi ile degeri ayri ogelerde duruyor;
    etiket/deger ikilisini yakalamanin en dayanikli yolu metin sirasi.
    """
    g = re.sub(r"(?s)<(script|style|noscript)[^>]*>.*?</\1>", " ", html_metni)
    g = re.sub(r"(?s)<[^>]+>", "\n", g)
    from html import unescape
    return [s.strip() for s in unescape(g).split("\n") if s.strip()]


def _bs_ayikla(html_metni: str) -> list[dict]:
    """Baska Sinema sayfasindaki film bloklarini okur."""
    cikti = []
    for blok in _BS_BLOK.findall(html_metni):
        ad_e = _BS_AD.search(blok)
        tar = _BS_TARIH.search(blok)
        if not (ad_e and tar):
            continue
        ay = _ay_no(tar.group(2).lower())
        if not ay:
            continue
        # Baslik "Orijinal Ad / Turkce Ad" kalibinda gelir; tek adli da olur.
        tam = _coz(ad_e.group(1))
        ozgun, ad = "", tam
        if " / " in tam:
            ozgun, ad = [p.strip() for p in tam.split(" / ", 1)]
        tur_e = _BS_TUR.search(blok)
        slug = _BS_SLUG.search(blok)
        cikti.append(film_kaydi(
            ad,
            "%04d-%02d-%02d" % (int(tar.group(3)), ay, int(tar.group(1))),
            ozgun_ad=ozgun,
            tur=[p.strip() for p in _coz(tur_e.group(1)).split(" - ")
                 if p.strip()] if tur_e else [],
            # Sayfa "Dagitimci:" diye bir alan basmiyor; alan sayfanin kendi
            # kimliginden geliyor - burasi Baska Sinema'nin kendi duyurusu.
            dagitimci="Başka Sinema",
            kaynak_kimlik="baskasinema:" + (slug.group(1) if slug else ""),
        ))
    return cikti


def _baska_cek(bas: str, son: str) -> list[dict]:
    tekil: dict[tuple, dict] = {}
    for yol in ("/gelecek-filmler/", "/basin/"):
        adres = BASKA_KOK + yol
        ortak.log(f"  {adres}")
        for f in _bs_ayikla(ortak.getir(adres)):
            if bas <= f["tarih"] <= son:
                tekil[(f["ad"].lower(), f["tarih"])] = f
        ortak.bekle()
    return list(tekil.values())


def _birfilm_cek(bas: str, son: str) -> list[dict]:
    """Once liste sayfasi, sonra yalnizca ARALIKTAKI filmlerin sayfasi.

    Liste sayfasi gunu ve ayi verir ama yili vermez ("13 Kasim'da
    Sinemalarda!"); yil yalnizca film sayfasinda yazili. Bu yuzden liste
    kaba bir SUZGEC olarak kullanilir, tarih film sayfasindan okunur.
    """
    adres = BIR_KOK + "/sinemalarda"
    ortak.log(f"  {adres}")
    html_metni = ortak.getir(adres)
    bugun = date.today()
    adaylar = []
    for baglanti, aciklama in _BF_OGE.findall(html_metni):
        m = _BF_GUN.search(_coz(aciklama))
        if not m:
            continue
        ay = _ay_no(m.group(2).lower())
        if not ay:
            continue
        try:
            kaba = date(bugun.year, ay, int(m.group(1)))
        except ValueError:
            continue
        # Yil yazmadigi icin gecmis gorunen gun bir sonraki yila ait olabilir.
        if kaba < bugun:
            try:
                kaba = kaba.replace(year=bugun.year + 1)
            except ValueError:
                continue
        if kaba.isoformat() > son:
            continue
        adaylar.append(baglanti)

    filmler = []
    for baglanti in adaylar[:BIR_AZAMI_SAYFA]:
        ortak.bekle()
        try:
            sayfa = ortak.getir(baglanti)
        except ortak.CekmeHatasi as e:
            ortak.log(f"    UYARI: {baglanti} alinamadi ({e})")
            continue
        satir = _satirlar(sayfa)
        tarih = ""
        tur: list[str] = []
        for i, s in enumerate(satir):
            m = _BF_TARIH.match(s)
            if m:
                ay = _ay_no(m.group(2).lower())
                if ay:
                    tarih = "%04d-%02d-%02d" % (
                        int(m.group(3)), ay, int(m.group(1)))
            if s.rstrip(":") == "Tür" and i + 1 < len(satir):
                tur = [p.strip() for p in re.split(r"[-,]", satir[i + 1])
                       if p.strip()]
        # Ad sayfa basligindan: "Bir Film | Sinemalarda | Buruk Noel"
        ad = ""
        b = re.search(r"<title>(.*?)</title>", sayfa, re.S)
        if b:
            parca = [p.strip() for p in _coz(b.group(1)).split("|")]
            ad = parca[-1] if parca else ""
        if not (ad and tarih) or not (bas <= tarih <= son):
            continue
        filmler.append(film_kaydi(
            ad, tarih, tur=tur, dagitimci="Bir Film",
            kaynak_kimlik="birfilm:" + baglanti.rsplit("/", 1)[-1],
        ))
    return filmler


def dagitimci_cek(ay_sayisi: int) -> tuple[list[dict], dict]:
    bas, son = aralik(ay_sayisi)
    ortak.log(f"  Dagitimci duyurulari: {bas} .. {son}")
    filmler: list[dict] = []
    dusen = []
    # Biri dusunce oteki yayina devam etsin; ikisi birden dusunce hata.
    for ad, islev in (("Başka Sinema", _baska_cek), ("Bir Film", _birfilm_cek)):
        try:
            bulunan = islev(bas, son)
            ortak.log(f"    {ad}: {len(bulunan)} film")
            filmler.extend(bulunan)
        except Exception as e:
            dusen.append(f"{ad} ({e!r})")
            ortak.log(f"    UYARI: {ad} alinamadi ({e!r})")
    if not filmler and dusen:
        raise ortak.CekmeHatasi(
            "dagitimci kaynaklarinin hepsi dustu: " + " | ".join(dusen))

    kaynak = {
        "ad": "Dağıtımcı vizyon duyuruları",
        "kisa": "Başka Sinema · Bir Film",
        "adres": f"{BASKA_KOK}/basin/ · {BIR_KOK}/sinemalarda",
        "kosullar": ("Her iki sitede de içeriğin kullanımını kısıtlayan bir "
                     "kullanım koşulları sayfası yok (29 Ağustos 2026'da site "
                     "haritalarının tamamı tarandı); robots.txt bu yolları "
                     "açık bırakıyor."),
        "kunye": "Vizyon tarihleri: Başka Sinema ve Bir Film duyuruları.",
        "kaynaklar": [
            {"ad": "Başka Sinema", "adres": BASKA_KOK + "/basin/",
             "kosullar": "", "kunye": "Kaynak: Başka Sinema"},
            {"ad": "Bir Film", "adres": BIR_KOK + "/sinemalarda",
             "kosullar": "", "kunye": "Kaynak: Bir Film"},
        ],
        "kapsam_uyarisi": ("Bu liste ulusal vizyon takviminin tamamı değildir; "
                           "yalnızca bu iki dağıtımcının getirdiği filmleri "
                           "kapsar."),
    }
    return filmler, kaynak


# -- kaynak: elle girilen -------------------------------------------------

def elle_cek(kok: Path) -> tuple[list[dict], dict]:
    """Panelden elle girilen liste. Kaynak bulunamadiginda calisan yol.

    Bicim: {"filmler": [{"ad": "...", "tarih": "2026-09-04", ...}]}
    """
    yol = kok / "vizyon-elle.json"
    d = ortak.json_oku(yol)
    if not d:
        raise ortak.CekmeHatasi(f"{yol} yok ya da okunamadi.")
    filmler = [film_kaydi(f.get("ad", ""), f.get("tarih", ""),
                          ozgun_ad=f.get("ozgun_ad", ""),
                          tur=f.get("tur", []),
                          dagitimci=f.get("dagitimci", ""),
                          ozet=f.get("ozet", ""),
                          yas_siniri=f.get("yas_siniri", ""),
                          kaynak_kimlik="elle")
               for f in d.get("filmler", []) if f.get("ad") and f.get("tarih")]
    kaynak = {
        "ad": "Elle giriş",
        "kisa": "panel",
        "adres": str(yol),
        "kosullar": "",
        "kunye": "",
    }
    return filmler, kaynak


# -- akis -----------------------------------------------------------------

def calistir(kok: Path, kaynak_adi: str, ay_sayisi: int, izin_var: bool) -> int:
    cikti = kok / f"{BILESEN}.json"
    try:
        if kaynak_adi == "tmdb":
            filmler, kaynak = tmdb_cek(ay_sayisi)
        elif kaynak_adi == "vikiveri":
            filmler, kaynak = vikiveri_cek(ay_sayisi)
        elif kaynak_adi == "boxoffice":
            filmler, kaynak = boxoffice_cek(ay_sayisi, izin_var)
        elif kaynak_adi == "dagitimci":
            filmler, kaynak = dagitimci_cek(ay_sayisi)
        else:
            filmler, kaynak = elle_cek(kok)
    except ortak.CekmeHatasi as e:
        return ortak.dusme_ile_bitir(kok, BILESEN, cikti, str(e))
    except Exception as e:
        return ortak.dusme_ile_bitir(kok, BILESEN, cikti, repr(e))

    if not filmler:
        return ortak.dusme_ile_bitir(
            kok, BILESEN, cikti, f"{kaynak_adi} kaynagi bos liste dondurdu")

    # Ayni film iki sayfada gecebilir; ad + tarih ikilisi tekil anahtardir.
    tekil = {}
    for f in filmler:
        tekil.setdefault((f["ad"].lower(), f["tarih"]), f)
    filmler = list(tekil.values())

    bas, son = aralik(ay_sayisi)
    veri = {
        "_not": ("Vizyon takvimi. Afis dosyasi tasinmaz - bkz. afis_notu. "
                 "Film adi ve tarihi disindaki alanlar kaynakta yoksa bos "
                 "kalir; doldurulmaz."),
        "guncelleme": ortak.simdi(),
        "bayat_esik_dakika": BAYAT_ESIK_DAKIKA,
        "aralik": {"baslangic": bas, "bitis": son, "ay": ay_sayisi},
        "kaynak": kaynak,
        "afis_notu": AFIS_NOTU,
        "film_sayisi": len(filmler),
        "haftalar": haftalara_bol(filmler),
    }

    ortak.json_yaz(cikti, veri)
    ortak.durum_yaz(kok, BILESEN, "taze")
    ortak.log(f"Bitti: {len(filmler)} film, {len(veri['haftalar'])} vizyon gunu "
              f"({bas} .. {son}) -> {cikti}")
    return 0


def main() -> int:
    ayristi = argparse.ArgumentParser(
        description="Turkiye vizyon takvimini ceker.")
    ayristi.add_argument("--kaynak", default="dagitimci",
                         choices=["dagitimci", "tmdb", "vikiveri",
                                  "boxoffice", "elle"],
                         help="veri kaynagi (varsayilan: dagitimci)")
    ayristi.add_argument("--ay", type=int, default=3,
                         help="kac ay ileriye bakilacak (varsayilan: 3)")
    ayristi.add_argument("--yazili-izin-var", action="store_true",
                         help="boxoffice kaynagi icin: yazili izin alindi")
    ayristi.add_argument("--kok", default=None,
                         help="cikti koku (ortam degiskeni: BH_CANLI_KOK)")
    arg = ayristi.parse_args()

    kok = ortak.kok_coz(arg.kok)
    ortak.log_kur(kok, BILESEN)
    ortak.log(f"Vizyon takvimi cekiliyor (kaynak: {arg.kaynak}) -> {kok}")
    return calistir(kok, arg.kaynak, max(1, arg.ay), arg.yazili_izin_var)


if __name__ == "__main__":
    raise SystemExit(main())
