"""Onaylanan taslagi UC tasarima birden yayinlar — yerelde, dosyaya yazarak.

    python arac/yayin.py arac/cikti/<slug>.json

Her tasarimin haber detay sayfasi SABLON olarak kullanilir; basligi, spotu,
govdesi, kunyesi ve etiketleri taslaktan doldurulup `haber-<slug>-t<N>.html`
olarak yazilir. Sonra o tasarimin anasayfasina, uretilen sayfaya baglanan bir
kart eklenir.

Sablonlarin geri kalanina (kenar sutunlari, doviz bandi, ilgili haberler)
DOKUNULMAZ: bunlar demo mobilyasidir.

Kaynagin fotografi INDIRILIR ve `gorseller/kaynak/` altina yerellestirilir; mansset
gorseli ve anasayfa karti bunu kullanir, fotograf altina atif dusulur. Uzaktan
baglanmaz — sayfalar internetsiz de acilabilmeli. Inmezse kategori gorseline
dusulur ve yayin durmaz. Bu, demo asamasinda alinmis bir karardir; gercek
yayinda her fotografin hak durumu ayrica dogrulanmalidir.

Bos taslak yayinlanmaz. Kural motoru basligi, spotu ve govdeyi kasitli bos
birakir; o hâliyle gelen paket reddedilir, cunku yazma isi editorundur.
"""

from __future__ import annotations

import io
import json
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ayiklayici import TARAYICI  # noqa: E402
from kural_motoru import kucuk, slugla, sozluk_yukle  # noqa: E402

KOK = Path(__file__).resolve().parent.parent

AYLAR = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
         "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
GUNLER = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]

# Kategoriye gore yerel kart gorseli. Yoksa kent.jpg.
FOTO = {
    "Yargı": "adliye", "Asayiş": "adliye", "Siyaset": "belediye",
    "Gündem": "kent", "Ekonomi": "sanayi", "Sağlık": "hastane",
    "Eğitim": "okul", "Çevre ve su": "baraj", "Ulaşım": "tramvay",
    "Spor": "spor", "Kültür": "muze", "Yaşam": "carsi",
    "Teknoloji": "sanayi", "Tarım": "tarim",
}

TASARIMLAR = {
    "1": {"sablon": "tasarim-1-haber-detay.html", "anasayfa": "tasarim-1-klasik.html"},
    "2": {"sablon": "tasarim-2-haber-detay.html", "anasayfa": "tasarim-2-hibrit.html"},
    "3": {"sablon": "tasarim-3-haber-detay.html", "anasayfa": "tasarim-3-modern.html"},
}


# Kaynagin fotografi buraya iner. Uzaktan baglanmaz: CLAUDE.md sayfalarin
# internetsiz de acilmasini sart kosuyor, o yuzden gorsel yerellestirilir.
GORSEL_KLASOR = "gorseller/kaynak"
EN_BUYUK_GORSEL = 8 * 1024 * 1024
UZANTI = {"image/jpeg": ".jpg", "image/jpg": ".jpg", "image/png": ".png",
          "image/webp": ".webp", "image/gif": ".gif", "image/avif": ".avif"}


class YayinHatasi(Exception):
    """Yayina uygun olmayan paket. Mesaji dogrudan editore gosterilir."""


# ----------------------------------------------------------------- yardimci

def kacir(m: str) -> str:
    return (str(m or "").replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def blok_sinirlari(metin: str, acilis: str, tur: str, nereden: int = 0) -> tuple[int, int, int]:
    """`acilis` etiketinden baslayip ayni turden ic ice etiketleri sayarak
    kapanisi bulur. (ic_bas, ic_son, blok_son) dondurur. `nereden`, ayni etiketten
    birkac tane oldugunda aramanin baslayacagi yeri verir."""
    bas = metin.index(acilis, nereden)
    ic_bas = bas + len(acilis)
    derinlik, i = 1, ic_bas
    ac, kapa = "<" + tur, "</" + tur + ">"
    while derinlik:
        sonraki_ac = metin.find(ac, i)
        sonraki_kapa = metin.find(kapa, i)
        if sonraki_kapa == -1:
            raise YayinHatasi("Sablonda <%s> blogu kapanmamis." % tur)
        if sonraki_ac != -1 and sonraki_ac < sonraki_kapa:
            derinlik += 1
            i = sonraki_ac + len(ac)
        else:
            derinlik -= 1
            i = sonraki_kapa + len(kapa)
    return ic_bas, i - len(kapa), i


def ic_degistir(metin: str, acilis: str, tur: str, yeni: str, nereden: int = 0) -> str:
    ic_bas, ic_son, _ = blok_sinirlari(metin, acilis, tur, nereden)
    return metin[:ic_bas] + yeni + metin[ic_son:]


def basa_ekle(metin: str, acilis: str, tur: str, yeni: str, nereden: int = 0) -> str:
    ic_bas, _, _ = blok_sinirlari(metin, acilis, tur, nereden)
    return metin[:ic_bas] + "\n" + yeni + metin[ic_bas:]


def kart_sil(metin: str, link: str) -> str:
    """Ayni habere baglanan eski karti kaldirir; yeniden yayinda cift kart olmaz."""
    while True:
        yer = metin.find(link)
        if yer == -1:
            return metin
        bas = metin.rfind("<article", 0, yer)
        if bas == -1:
            return metin
        acilis_son = metin.index(">", bas) + 1
        # Acilis etiketi belgede birden cok gecer; aramayi BU karttan baslat.
        _, _, blok_son = blok_sinirlari(metin, metin[bas:acilis_son], "article", bas)
        satir_bas = metin.rfind("\n", 0, bas)
        kisa = metin[:satir_bas if satir_bas != -1 else bas] + metin[blok_son:]
        if len(kisa) >= len(metin):   # kisalmadiysa dongu kirilmali
            return metin
        metin = kisa


def tek(metin: str, desen: str, yeni: str, ad: str) -> str:
    yeni_metin, adet = re.subn(desen, lambda m: yeni, metin, count=1, flags=re.S)
    if not adet:
        raise YayinHatasi("Sablonda %s bulunamadi." % ad)
    return yeni_metin


# ----------------------------------------------------------------- dogrulama

def dogrula(paket: dict) -> dict:
    t = paket.get("taslak") or {}
    secenekler = t.get("baslik_secenekleri") or []
    i = t.get("onerilen_baslik_indeksi") or 0
    baslik = (secenekler[i]["metin"] if i < len(secenekler) else "").strip()
    if not baslik:
        raise YayinHatasi("Başlık boş. Kural motoru başlık yazmaz; yayından önce editör yazmalı.")
    if not (t.get("spot") or "").strip():
        raise YayinHatasi("Spot boş. Yayından önce doldurulmalı.")
    paragraflar = [b for b in (t.get("govde") or [])
                   if b.get("tur") == "paragraf" and (b.get("metin") or "").strip()]
    if len(paragraflar) < 2:
        raise YayinHatasi("Gövde boş ya da tek paragraf. Kural motoru gövde yazmaz — "
                          "ham malzeme tezgahına bakıp haberi kendi cümlelerinizle yazın.")
    # Atif govdede aranmaz: 23 Agustos 2026'da alinan kararla kaynak, yayinlanan
    # sayfada ayri bir bolmede gosteriliyor. Haberi masa kendi cumleleriyle yazar.
    return {"baslik": baslik, "spot": t["spot"].strip(), "taslak": t}


# ----------------------------------------------------------------- govde

def govde_html(bloklar: list, bicim: str, girinti: str, foto_bloku: str = "",
               son_blok: str = "") -> str:
    """`foto_bloku` verilirse ilk paragraftan sonra araya girer. Tasarim 3'te
    mansset gorseli govdenin ICINDE duruyor; govde yeniden uretildigi icin
    fotografi de burada yerlestirmek gerekiyor."""
    cikti, ilk = [], True
    for b in bloklar:
        metin = (b.get("metin") or "").strip()
        if not metin:
            continue
        tur = b.get("tur")
        if tur == "ara_baslik":
            cikti.append('%s<h2 id="%s">%s</h2>' % (girinti, slugla(metin, 40), kacir(metin)))
        elif tur == "alinti":
            kaynak = kacir(b.get("kaynak") or "Yayın ilkeleri")
            if bicim == "1":
                cikti.append('%s<div class="alinti">%s<cite>%s</cite></div>'
                             % (girinti, kacir(metin), kaynak))
            else:
                cikti.append('%s<blockquote class="alinti">\n%s  <p>%s</p>\n%s  <cite>%s</cite>\n%s</blockquote>'
                             % (girinti, girinti, kacir(metin), girinti, kaynak, girinti))
        else:
            sinif = ' class="giris"' if (ilk and bicim == "3") else ""
            cikti.append("%s<p%s>%s</p>" % (girinti, sinif, kacir(metin)))
            if ilk and foto_bloku:
                cikti.append(foto_bloku)
            ilk = False
    if son_blok:
        cikti.append(son_blok)
    return "\n" + "\n\n".join(cikti) + "\n" + girinti[:-2]


def icindekiler_html(bloklar: list, girinti: str) -> str:
    ogeler = [b for b in bloklar if b.get("tur") == "ara_baslik" and (b.get("metin") or "").strip()]
    if not ogeler:
        return ""
    satirlar = ['%s<li><a href="#%s">%s</a></li>'
                % (girinti, slugla(b["metin"].strip(), 40), kacir(b["metin"].strip()))
                for b in ogeler]
    return "\n" + "\n".join(satirlar) + "\n" + girinti[:-2]


FOTO_ALT = {
    "adliye": "Adliye binası", "belediye": "Bursa Büyükşehir Belediyesi hizmet binası",
    "kent": "Bursa kent merkezinden görünüm", "sanayi": "Sanayi bölgesinden görünüm",
    "hastane": "Hastane binası", "okul": "Okul binası ve bahçesi",
    "baraj": "Baraj gövdesi ve su seviyesi", "tramvay": "Kent içi raylı sistem aracı",
    "spor": "Spor tesisinden görünüm", "muze": "Müze binası",
    "carsi": "Tarihi çarşıdan görünüm", "tarim": "Tarım arazisi",
}


def istege_bagli(f):
    """Sablonda karsiligi olmayabilecek degisiklikler icin. Kritik olan
    (baslik, spot, govde) bu sarmalayiciyi KULLANMAZ; orada eksik = hata."""
    try:
        return f()
    except (YayinHatasi, ValueError):
        return None


def gorsel_indir(kaynak: dict, slug: str, kok: Path) -> str | None:
    """Kaynagin fotografini `gorseller/kaynak/` altina indirir, goreli yolu doner.

    Basarisiz olursa None doner ve yayin durmaz — sablonun kategori gorseli
    kullanilir. Fotograf yuzunden haber yayinlanamamasi dogru olmaz."""
    url = (kaynak.get("gorsel_url") or "").strip()
    if not url.lower().startswith(("http://", "https://")):
        return None
    istek = urllib.request.Request(url, headers={
        "User-Agent": TARAYICI,
        "Accept": "image/avif,image/webp,image/png,image/jpeg,*/*;q=0.8",
        "Referer": kaynak.get("kaynak_url") or url,
    })
    try:
        with urllib.request.urlopen(istek, timeout=30) as yanit:
            tur = (yanit.headers.get("Content-Type") or "").split(";")[0].strip().lower()
            if not tur.startswith("image/"):
                return None
            veri = yanit.read(EN_BUYUK_GORSEL + 1)
    except (urllib.error.URLError, OSError, ValueError):
        return None
    if not veri or len(veri) > EN_BUYUK_GORSEL:
        return None

    uzanti = UZANTI.get(tur) or Path(url.split("?")[0]).suffix.lower() or ".jpg"
    klasor = kok / GORSEL_KLASOR
    klasor.mkdir(parents=True, exist_ok=True)
    (klasor / (slug + uzanti)).write_bytes(veri)
    return "%s/%s%s" % (GORSEL_KLASOR, slug, uzanti)


def kaynaklara_yaz(kok: Path, goreli: str, kaynak: dict) -> None:
    """Indirilen gorseli `gorseller/KAYNAKLAR.md` dosyasina isler."""
    yol = kok / "gorseller" / "KAYNAKLAR.md"
    satir = "- `%s` — %s, %s (demo için indirildi, %s)\n" % (
        goreli, kaynak.get("kaynak_adi") or kaynak.get("kaynak_alan") or "?",
        kaynak.get("gorsel_url") or "", datetime.now().strftime("%d.%m.%Y"))
    baslik = "## Yayından inen kaynak görselleri\n"
    mevcut = yol.read_text(encoding="utf-8") if yol.exists() else "# Görsel kaynakları\n"
    if goreli in mevcut:
        return
    if baslik not in mevcut:
        mevcut += "\n" + baslik + "\n"
    yol.write_text(mevcut + satir, encoding="utf-8")


def asil_kaynak_bul(kaynak: dict) -> str:
    """Kaynak sayfa kendi kaynagini belirtmisse onu doner (AA, DHA, Reuters...).

    Ayiklayici bunu `yazar` alaninda tasiyor: haber siteleri ajans kaynakli
    haberlerde yazar yerine ajans kodunu yaziyor. Kisi adi ya da "Haber Merkezi"
    gibi genel bir imza ajans sayilmaz."""
    # Ayiklayici sayfadaki "Kaynak:" satirini, parantezli ajans kodunu ve yazar
    # alanini zaten tarayip `asil_kaynak` alanina yaziyor; oncelik onun.
    bulunan = (kaynak.get("asil_kaynak") or "").strip()
    if bulunan:
        return bulunan
    yazar = (kaynak.get("yazar") or "").strip()
    if not yazar:
        return ""
    duz = kucuk(yazar)
    for ajans in sozluk_yukle().get("ajanslar", []):
        if kucuk(ajans) == duz or kucuk(ajans) in duz.split():
            return ajans
    return ""


def kaynak_bolmesi(v: dict, girinti: str) -> str:
    """Yayinlanan sayfadaki "Kaynak" bolmesi. Atif govdeye girmiyor, buraya
    yaziliyor; kaynak sayfa kendi kaynagini belirtmisse o da anilir."""
    # Sayfa kendi kaynagini belirtmisse kaynak ODUR; haberi okudugumuz site
    # araci yayindir, kaynak diye anilmaz.
    kaynak_adi = kacir(v["asil_kaynak"] or v["kaynak_adi"] or v.get("kaynak_alan") or "kaynak")
    cumle = ("Kaynak: <b>%s</b>. Haber, Bursa Hakimiyet haber masasında yazılmıştır."
             % kaynak_adi)
    if v["kaynak_url"]:
        # data-ses: baglanti metni sesli okumaya girmez, kaynak cumlesi girer.
        cumle += (' <a href="%s" rel="nofollow noopener" target="_blank"'
                  ' data-ses="atla">Habere git</a>' % kacir(v["kaynak_url"]))
    return ('%s<aside class="kaynak-bolmesi" style="border-top:1px solid var(--cizgi);'
            'margin:30px 0 0;padding:14px 0 0">\n'
            '%s  <b style="display:block;font-size:11.5px;letter-spacing:.8px;'
            'text-transform:uppercase;color:var(--gri);margin-bottom:6px">Kaynak</b>\n'
            '%s  <p style="margin:0;font-size:14px;line-height:1.55">%s</p>\n'
            '%s</aside>' % (girinti, girinti, girinti, cumle, girinti))


def veri_kur(paket: dict, kok: Path = KOK) -> dict:
    d = dogrula(paket)
    t = d["taslak"]
    simdi = datetime.now()
    foto = FOTO.get(t.get("kategori", ""), "kent")
    slug = (t.get("url_slug") or slugla(d["baslik"])).strip()
    # Kaynagin fotografi indirilip yerellestirilir; inmezse kategori gorseli.
    inen = gorsel_indir(paket.get("kaynak") or {}, slug, kok)
    return {
        "gorsel_inen": inen,
        "hero_gorsel": inen or ("gorseller/genis/%s.jpg" % foto),
        "kart_gorsel": inen or ("gorseller/kart/%s.jpg" % foto),
        "gorsel_alt": (t.get("gorsel_alt") or "").strip() or FOTO_ALT.get(foto, "Habere ait görsel"),
        "gorsel_altyazi": (t.get("gorsel_altyazi") or "").strip(),
        "kaynak_adi": (paket.get("kaynak") or {}).get("kaynak_adi") or "",
        "kaynak_alan": (paket.get("kaynak") or {}).get("kaynak_alan") or "",
        "kaynak_url": (paket.get("kaynak") or {}).get("kaynak_url") or "",
        "asil_kaynak": asil_kaynak_bul(paket.get("kaynak") or {}),
        "baslik": d["baslik"], "spot": d["spot"], "taslak": t,
        "kategori": t.get("kategori") or "Gündem",
        "ilce": t.get("ilce") or "Bursa geneli",
        "etiketler": t.get("etiketler") or [],
        "okuma": t.get("okuma_suresi_dk") or 1,
        "slug": slug,
        "tarih_uzun": "%d %s %d, %s" % (simdi.day, AYLAR[simdi.month - 1], simdi.year,
                                        GUNLER[simdi.weekday()]),
        "tarih_kisa": simdi.strftime("%d.%m.%Y"),
        "saat": simdi.strftime("%H:%M"),
        "iso": simdi.strftime("%Y-%m-%dT%H:%M"),
    }


def ortak(sayfa: str, v: dict) -> str:
    sayfa = tek(sayfa, r"<title>.*?</title>",
                "<title>%s — Bursa Hakimiyet</title>" % kacir(v["baslik"]), "<title>")
    istege_bagli(lambda: None)
    yeni, adet = re.subn(r'(<meta name="description" content=")[^"]*(")',
                         lambda m: m.group(1) + kacir(v["spot"])[:300] + m.group(2),
                         sayfa, count=1)
    return yeni if adet else sayfa


def kirinti_degistir(s: str, v: dict, tasarim: str) -> str:
    """Kirinti navigasyonunu haberin kategorisi ve ilcesiyle gunceller.
    Uc tasarimda uc ayri isaretleme var; her biri kendi bicimiyle yazilir."""
    nav = '<nav class="kirinti" aria-label="Kırıntı navigasyonu">'
    kategori, ilce = kacir(v["kategori"]), kacir(v["ilce"])
    if tasarim == "1":
        nereden = s.index(nav)
        ic = ('\n        <li><a href="tasarim-1-klasik.html">Anasayfa</a></li>'
              '\n        <li><a href="#">%s</a></li>'
              '\n        <li><a href="#">%s</a></li>\n      ' % (kategori, ilce))
        return ic_degistir(s, "<ol>", "ol", ic, nereden)
    if tasarim == "2":
        ic = ('\n      <a href="tasarim-2-hibrit.html">Anasayfa</a>'
              '<span aria-hidden="true">›</span>'
              '\n      <a href="#">%s</a><span aria-hidden="true">›</span>'
              '\n      <a href="#">%s</a>\n    ' % (kategori, ilce))
        return ic_degistir(s, nav, "nav", ic)
    ic = ('\n  <a href="tasarim-3-modern.html">Anasayfa</a> · '
          '<a href="#">%s</a> · <a href="#">%s</a>\n' % (kategori, ilce))
    return ic_degistir(s, '<nav class="iz kapsa" aria-label="Neredesiniz">', "nav", ic)


def altyazi_metni(v: dict) -> str:
    """Fotograf alti. Kaynagin fotografi kullanildiginda atif eklenir."""
    yazi = v["gorsel_altyazi"] or v["gorsel_alt"]
    foto_kaynak = v["asil_kaynak"] or v["kaynak_adi"]
    if v["gorsel_inen"] and foto_kaynak:
        yazi += " (Fotoğraf: %s)" % foto_kaynak
    return kacir(yazi)


def hero_degistir(s: str, v: dict, altyazi_acilis: str, altyazi_kapanis: str) -> str:
    """Sablonun mansset gorselini ve fotograf altini haberinkiyle degistirir."""
    def img_yenile(esle):
        etiket = esle.group(0)
        etiket = re.sub(r'src="[^"]*"', lambda x: 'src="%s"' % v["hero_gorsel"], etiket, count=1)
        return re.sub(r'alt="[^"]*"', lambda x: 'alt="%s"' % kacir(v["gorsel_alt"]),
                      etiket, count=1)

    s = re.sub(r'<img[^>]*src="gorseller/genis/[^"]*"[^>]*>', img_yenile, s, count=1)
    desen = re.escape(altyazi_acilis) + "[^<]*" + re.escape(altyazi_kapanis)
    return re.sub(desen, lambda x: altyazi_acilis + altyazi_metni(v) + altyazi_kapanis,
                  s, count=1)


def detay_1(sablon: str, v: dict) -> str:
    s = ortak(sablon, v)
    s = kirinti_degistir(s, v, "1")
    s = hero_degistir(s, v, '<p class="foto-alt">', '</p>')
    s = tek(s, r'<span class="rozet-k">.*?</span>',
            '<span class="rozet-k">%s</span>' % kacir(v["kategori"].upper()), "rozet-k")
    s = tek(s, r"<h1>.*?</h1>", "<h1>%s</h1>" % kacir(v["baslik"]), "<h1>")
    s = tek(s, r'<p class="spot">.*?</p>',
            '<p class="spot">%s</p>' % kacir(v["spot"]), "spot")
    s = tek(s, r'<time datetime="[^"]*">[^<]*</time>',
            '<time datetime="%s">%s, %s</time>' % (v["iso"], v["tarih_uzun"], v["saat"]), "time")
    s = ic_degistir(s, '<div class="metin" data-boyut="orta">', "div",
                    govde_html(v["taslak"]["govde"], "1", " " * 12,
                               son_blok=kaynak_bolmesi(v, " " * 12)))
    if v["etiketler"]:
        etiketler = "\n            <b>ETİKETLER</b>\n            " + "".join(
            '<a href="#">%s</a>' % kacir(e) for e in v["etiketler"]) + "\n          "
        istege_bagli(lambda: None)
        s = ic_degistir(s, '<div class="etiketler">', "div", etiketler)
    return s


def detay_2(sablon: str, v: dict) -> str:
    s = ortak(sablon, v)
    s = kirinti_degistir(s, v, "2")
    s = hero_degistir(s, v, '<figcaption class="foto-alt">', '</figcaption>')
    s = tek(s, r"<h1>.*?</h1>", "<h1>%s</h1>" % kacir(v["baslik"]), "<h1>")
    s = tek(s, r'<p class="spot">.*?</p>',
            '<p class="spot">%s</p>' % kacir(v["spot"]), "spot")
    s = tek(s, r'<div class="etiket-k">.*?</div>',
            '<div class="etiket-k">%s</div>' % kacir(v["kategori"].upper()), "etiket-k")
    s = ic_degistir(s, '<div class="govde" id="govde">', "div",
                    govde_html(v["taslak"]["govde"], "2", " " * 10,
                               son_blok=kaynak_bolmesi(v, " " * 10)))
    if v["etiketler"]:
        s = ic_degistir(s, '<div class="etiketler">', "div", "\n" + "\n".join(
            '          <a class="etiket-oge" href="#">%s</a>' % kacir(e)
            for e in v["etiketler"]) + "\n        ")
    return s


def foto_bloku_3(v: dict) -> str:
    return ('    <div class="detay-foto genis">\n'
            '      <div class="foto t-gri">\n'
            '        <img src="%s" alt="%s" width="1280" height="720" '
            'loading="lazy" decoding="async">\n'
            '      </div>\n'
            '      <p class="foto-yazi">%s</p>\n'
            '    </div>'
            % (v["hero_gorsel"], kacir(v["gorsel_alt"]), altyazi_metni(v)))


def son_blok_3(v: dict) -> str:
    """Tasarim 3'un govde sonu: kaynak bolmesi, ardindan etiketler. Ikisi de
    sablonda `article.govde` icinde duruyor; govde yeniden uretildigi icin
    burada kuruluyorlar."""
    parcalar = [kaynak_bolmesi(v, " " * 4)]
    if v["etiketler"]:
        parcalar.append('    <div class="etiketler">\n' + "\n".join(
            '      <a href="#">%s</a>' % kacir(e) for e in v["etiketler"])
            + "\n    </div>")
    return "\n\n".join(parcalar)


def detay_3(sablon: str, v: dict) -> str:
    s = ortak(sablon, v)
    s = kirinti_degistir(s, v, "3")
    s = tek(s, r"<h1>.*?</h1>", "<h1>%s</h1>" % kacir(v["baslik"]), "<h1>")
    s = tek(s, r'<p class="spot">.*?</p>',
            '<p class="spot">%s</p>' % kacir(v["spot"]), "spot")
    s = ic_degistir(s, '<div class="kunye">', "div",
                    "\n      <span>%s</span>\n      <span>Güncelleme %s</span>"
                    "\n      <span>%d dk okuma</span>\n      <span>Haber Merkezi</span>\n    "
                    % (v["tarih_uzun"], v["saat"], v["okuma"]))
    s = ic_degistir(s, '<article class="govde" id="govde">', "article",
                    govde_html(v["taslak"]["govde"], "3", " " * 4, foto_bloku_3(v),
                               son_blok=son_blok_3(v)))
    icindekiler = icindekiler_html(v["taslak"]["govde"], " " * 6)
    if icindekiler:
        s = ic_degistir(s, "<ol>", "ol", icindekiler)
    return s


def kart_1(v: dict, link: str) -> str:
    return ('            <article class="kart">\n'
            '              <div class="foto"><img src="%s" alt="%s" '
            'width="640" height="400" loading="lazy" decoding="async"></div>\n'
            '              <div class="ic"><div class="ust">%s</div>'
            '<h3><a href="%s">%s</a></h3></div>\n'
            '            </article>'
            % (v["kart_gorsel"], kacir(v["gorsel_alt"]), kacir(v["kategori"]), link, kacir(v["baslik"])))


def kart_2(v: dict, link: str) -> str:
    return ('            <article class="mini suzulen" data-ilce="%s">\n'
            '              <div class="foto t-kirmizi"><img src="%s" '
            'width="640" height="400" loading="lazy" decoding="async" alt="%s"></div>\n'
            '              <h3><a href="%s">%s</a></h3>'
            '<span class="zaman">Az önce · %s</span>\n'
            '            </article>'
            % (slugla(v["ilce"], 30), v["kart_gorsel"], kacir(v["gorsel_alt"]), link,
               kacir(v["baslik"]), kacir(v["kategori"])))


def kart_3(v: dict, link: str) -> str:
    ozet = v["spot"] if len(v["spot"]) <= 150 else v["spot"][:147].rstrip() + "…"
    return ('      <article class="kart">\n'
            '        <div class="foto t-mavi"><img src="%s" alt="%s" '
            'width="640" height="400" loading="lazy" decoding="async"></div>\n'
            '        <span class="etiket">%s</span>\n'
            '        <h3><a href="%s">%s</a></h3>\n'
            '        <p>%s</p>\n'
            '        <div class="alt"><span>Haber Merkezi</span><span>·</span>'
            '<span>%d dk okuma</span></div>\n'
            '      </article>'
            % (v["kart_gorsel"], kacir(v["gorsel_alt"]), kacir(v["kategori"]), link,
               kacir(v["baslik"]), kacir(ozet), v["okuma"]))


# ----------------------------------------------------------------- yayin

URETICI = {"1": (detay_1, kart_1), "2": (detay_2, kart_2), "3": (detay_3, kart_3)}


def kart_yerlestir(anasayfa: str, tasarim: str, kart: str, link: str) -> str:
    """Karti anasayfanin ilk sirasina koyar. Ayni habere ait eski kart varsa
    once silinir; yeniden yayinda liste sismesin."""
    anasayfa = kart_sil(anasayfa, link)
    if tasarim == "1":
        return basa_ekle(anasayfa, '<div class="kartlar">', "div", kart)
    if tasarim == "2":
        nereden = anasayfa.index("Bursa gündemi")
        return basa_ekle(anasayfa, '<div class="uclu">', "div", kart, nereden)
    return basa_ekle(anasayfa, '<div class="buyuk">', "div", kart)


def yayinla(paket: dict, kok: Path = KOK) -> dict:
    """Uc tasarima birden yayinlar. Once hepsini bellekte uretir, sonra yazar:
    ucuncu tasarimda patlayan bir sey ilk ikisini yarim birakmasin."""
    v = veri_kur(paket, kok)
    yazilacak: dict[Path, str] = {}
    sonuc = []

    for tasarim, yollar in sorted(TASARIMLAR.items()):
        detay_uret, kart_uret = URETICI[tasarim]
        sablon = io.open(kok / yollar["sablon"], encoding="utf-8").read()
        ad = "haber-%s-t%s.html" % (v["slug"], tasarim)
        yazilacak[kok / ad] = detay_uret(sablon, v)

        anasayfa_yolu = kok / yollar["anasayfa"]
        mevcut = yazilacak.get(anasayfa_yolu) or io.open(anasayfa_yolu, encoding="utf-8").read()
        yazilacak[anasayfa_yolu] = kart_yerlestir(mevcut, tasarim, kart_uret(v, ad), ad)
        sonuc.append({"tasarim": tasarim, "sayfa": ad, "anasayfa": yollar["anasayfa"]})

    for yol, icerik in yazilacak.items():
        io.open(yol, "w", encoding="utf-8").write(icerik)

    if v["gorsel_inen"]:
        kaynaklara_yaz(kok, v["gorsel_inen"], paket.get("kaynak") or {})

    return {"baslik": v["baslik"], "slug": v["slug"],
            "gorsel": v["gorsel_inen"], "yayinlar": sonuc}


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    paket = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    try:
        s = yayinla(paket)
    except YayinHatasi as e:
        print("Yayinlanmadi: %s" % e)
        return 2
    print("Yayinlandi: %s" % s["baslik"])
    for y in s["yayinlar"]:
        print("  tasarim %s -> %s  (kart: %s)" % (y["tasarim"], y["sayfa"], y["anasayfa"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
