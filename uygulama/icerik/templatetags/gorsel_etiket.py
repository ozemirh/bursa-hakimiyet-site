"""Görsel etiketi — `srcset`/`sizes`/ölçü/öncelik tek yerden (19 Ekim 2026).

Kullanım:

    {% load gorsel_etiket %}
    {% gorsel h "kart" %}                         tembel yüklenen kart görseli
    {% gorsel h "manset" oncelikli=True %}        LCP: eager + fetchpriority=high
    {% gorsel h "dortlu" hemen=True %}            ilk ekran: eager, öncelik normal
    {% gorsel y "portre" alt="" %}                bezeme: boş alt, açıkça
    <img {% gorsel_ozellik "site/uludag.jpg" "panel" %} alt="" …>   yalnız nitelikler

Yuva anahtarları (`YUVALAR`) yerleşimin **ölçülmüş** genişliklerinden yazıldı
(başsız Chrome, 390–1920 px, 19 Ekim 2026). Yerleşim değişirse `sizes`
yeniden ölçülmeli; yanlış `sizes` görseli bulanıklaştırır (küçük tahmin) ya
da boşuna büyütür (büyük tahmin) — büyük tahmin her zaman daha zararsızdır.

Görselsiz kayıt bu etikete hiç gelmez: şablon `gorsel_yolu` boşken kategori
temsilî SVG'sini çizmeye devam eder.
"""

from django import template
from django.conf import settings
from django.utils.html import format_html

from icerik import gorsel_turev as gt

register = template.Library()

#: anahtar → (sizes, src için varsayılan genişlik). Yorumdaki sayılar
#: 1200 px ve üstünde ölçülen çizim genişliği.
YUVALAR = {
    # anasayfa dörtlüsü: 263 px; ≤600 yatay kart (fotoğraf 112 px, 20 Ekim
    # 2026 R1), 601–799 iki sütun, 800–1199 dört sütun
    "dortlu": ("(max-width: 600px) 112px, (max-width: 799px) 50vw, "
               "(max-width: 1199px) 25vw, 270px", 320),
    # kutu ızgarası (son haberler, arama): 359 px
    "kart": ("(max-width: 639px) 100vw, (max-width: 1023px) 50vw, "
             "(max-width: 1199px) 33vw, 360px", 480),
    # detayın ilgili haberleri ve anasayfa Bursaspor şeridi: ≤600 yatay kart
    # (fotoğraf 112 px, R1), üstünde kutu ızgarasıyla aynı
    "kart-yatay": ("(max-width: 600px) 112px, (max-width: 1023px) 50vw, "
                   "(max-width: 1199px) 33vw, 360px", 480),
    "kart-genis": ("(max-width: 767px) 100vw, (max-width: 1023px) 50vw, "
                   "(max-width: 1199px) 33vw, 360px", 480),
    # bölüm sayfasının üst kademesi (liste-izgara): 528 px
    "liste": ("(max-width: 639px) 100vw, (max-width: 1199px) 50vw, 530px", 640),
    "liste-genis": ("(max-width: 767px) 100vw, (max-width: 1199px) 50vw, 530px", 640),
    # bölüm akışı: ikili 512 px, üçlü 336 px
    "ikili": ("(max-width: 767px) 100vw, (max-width: 1199px) 50vw, 512px", 640),
    "uclu": ("(max-width: 767px) 100vw, (max-width: 1199px) 33vw, 340px", 480),
    # manşet slaytı 760 px, mini slayt 318 px
    "manset": ("(max-width: 1023px) 100vw, (max-width: 1199px) 70vw, 760px", 960),
    "mini": ("(max-width: 767px) 100vw, (max-width: 1023px) 62vw, 320px", 480),
    # haber/galeri/video/köşe detayının ana görseli: 712 px
    "detay": ("(max-width: 1023px) 100vw, 720px", 960),
    # galeri ve video kartları, galeri kareleri: 256 px
    "galeri": ("(max-width: 639px) 100vw, (max-width: 1023px) 50vw, 260px", 320),
    # konu sayfasının akış satırı: 150 px'lik sütun
    "satir": ("150px", 320),
    # yazar kuşağı portresi (afiş şablonları %288 yakınlaştırılıyor): 259 px
    "portre": ("260px", 320),
    "vesika": ("58px", 320),
    # hava ve namaz panellerinin site fotoğrafları: 329 / 504 px
    "panel": ("(max-width: 1023px) 100vw, 520px", 640),
}

#: Görsel alt metni olarak bilgi taşımayan sabit değerler. Arşivin
#: 1.038.222 haberinde `gorsel_alt` = "Google News"; 11'inde "son dakika".
#: Veri DEĞİŞTİRİLMEZ (geri alınamaz toplu işlem); render anında boş sayılır.
ANLAMSIZ_ALT = {
    "google news", "son dakika", "bursa hakimiyet", "bursahakimiyet",
    "haber", "görsel", "resim", "foto", "fotoğraf", "image", "photo",
}


def _sade(metin) -> str:
    metin = str(metin or "").replace("İ", "i").replace("I", "ı").lower()
    return " ".join(metin.split())


def anlamli(metin) -> str:
    """Bilgi taşımayan alt metni boşa çevirir; anlamlıysa olduğu gibi döner."""
    if not metin or _sade(metin) in ANLAMSIZ_ALT:
        return ""
    return str(metin).strip()


@register.filter
def anlamli_alt(metin):
    return anlamli(metin)


@register.filter
def foto_alti(nesne):
    """Fotoğrafın altına basılacak satır: anlamlı ve başlığın tekrarı değilse."""
    metin = anlamli(getattr(nesne, "gorsel_alt", ""))
    if metin and _sade(metin) == _sade(getattr(nesne, "baslik", "")):
        return ""
    return metin


@register.filter
def arsiv_gorseli_kayip(haber) -> bool:
    """Görseli kaynak sunucudan silinmiş ARŞİV haberi mi?

    Arşivden göç eden kayıt panelde girilmemiştir (`olusturan` boş) ve
    kaynak sunucudaki görselin izini (`gorsel_url`) taşır. Panelden girilen
    ya da hiç görseli olmayan haberde "silinmiş" demek yanlış bilgi olur.
    """
    if _gorsel_yolu(haber):
        return False
    return (getattr(haber, "olusturan_id", None) is None
            and bool(getattr(haber, "gorsel_url", "")))


def _gorsel_yolu(nesne) -> str:
    deger = getattr(nesne, "gorsel_yolu", "")
    return (deger() if callable(deger) else deger) or ""


def kaynak_yolu(nesne) -> str:
    """Nesneden arşiv köküne göreli kaynak yol (`gorseller/2026-08/x.webp`).

    Modellerin `gorsel_yolu` adresinden türetilir; böylece Haber, medya
    aileleri ve galeri kareleri tek sözleşmeyle çalışır. Tanınmayan adres
    için boş döner ve etiket düz `<img src>` basar.
    """
    if isinstance(nesne, str):
        yol = nesne
    else:
        adres = _gorsel_yolu(nesne)
        arsiv = settings.ARSIV_GORSEL_URL
        medya = getattr(settings, "MEDYA_GORSEL_URL", "/arsiv-medya/")
        if adres.startswith(arsiv):
            yol = "gorseller/" + adres[len(arsiv):]
        elif adres.startswith(medya):
            yol = adres[len(medya):]
        else:
            return ""
    try:
        dilimler = gt._dilimler(yol)
    except gt.GecersizIstek:
        return ""
    if len(dilimler) < 2 or dilimler[0] not in gt.kaynak_kokleri():
        return ""
    return yol


def nitelikler(kaynak: str, yuva: str) -> dict:
    """src, srcset, sizes, width, height — ölçü orijinalden, yoksa 3:2."""
    sizes, varsayilan = YUVALAR.get(yuva, YUVALAR["kart"])
    (en, boy), _ = gt.olcu(kaynak)
    adaylar = []
    for g in gt.GENISLIKLER:
        if g < en:
            adaylar.append((g, g))
        else:
            adaylar.append((g, en))    # büyütme yok: türev orijinal enindedir
            break
    src_g = next((g for g, _ in adaylar if g >= varsayilan), adaylar[-1][0])
    if en > gt.GENISLIKLER[-1]:
        boy = max(1, round(boy * gt.GENISLIKLER[-1] / en))
        en = gt.GENISLIKLER[-1]
    return {
        "src": gt.adres(src_g, kaynak),
        "srcset": ", ".join(f"{gt.adres(g, kaynak)} {w}w" for g, w in adaylar),
        "sizes": sizes,
        "width": en,
        "height": boy,
    }


def _yukleme(oncelikli, hemen):
    if oncelikli:
        return "eager", "high"
    return ("eager" if hemen else "lazy"), ""


@register.simple_tag
def gorsel(nesne, yuva="kart", alt=None, oncelikli=False, hemen=False,
           genis=False, sinif="", ertele=False):
    """Tam `<img>`. `alt` verilmezse anlamlı `gorsel_alt` → başlık → ad.

    `ertele`: slaytın görünmeyen kareleri için. `visibility:hidden` öğe de
    yerleşimde yer kapladığından tarayıcı `loading="lazy"`ye rağmen onu
    indiriyor (ölçüldü: anasayfada 20 slayttan 18'i ilk açılışta iniyordu).
    Ertelenen görsel `src`/`srcset` yerine `data-src`/`data-srcset` taşır;
    `site.js` slayt etkinleşince (ve bir sonrakini) yükler. Betiksiz okur
    zaten yalnız ilk slaytı görür.
    """
    if genis and f"{yuva}-genis" in YUVALAR:
        yuva = f"{yuva}-genis"
    if alt is None:
        alt = (anlamli(getattr(nesne, "gorsel_alt", ""))
               or getattr(nesne, "baslik", "") or getattr(nesne, "ad", ""))
    yukleme, oncelik = _yukleme(oncelikli, hemen)
    kaynak = kaynak_yolu(nesne)
    if not kaynak:
        adres = _gorsel_yolu(nesne)
        if not adres:
            return ""
        return format_html(
            '<img src="{}" alt="{}" loading="{}"{} decoding="async"{}>',
            adres, alt, yukleme,
            format_html(' fetchpriority="{}"', oncelik) if oncelik else "",
            format_html(' class="{}"', sinif) if sinif else "")
    n = nitelikler(kaynak, yuva)
    on_ek = "data-" if (ertele and not oncelikli and not hemen) else ""
    return format_html(
        '<img {}src="{}" {}srcset="{}" sizes="{}" width="{}" height="{}" alt="{}" '
        'loading="{}"{} decoding="async"{}>',
        on_ek, n["src"], on_ek, n["srcset"], n["sizes"], n["width"], n["height"],
        alt, yukleme,
        format_html(' fetchpriority="{}"', oncelik) if oncelik else "",
        format_html(' class="{}"', sinif) if sinif else "")


@register.simple_tag
def gorsel_ozellik(kaynak, yuva="kart"):
    """Yalnız `src srcset sizes width height` — kalan nitelikler şablonda."""
    yol = kaynak_yolu(kaynak)
    if not yol:
        return ""
    n = nitelikler(yol, yuva)
    return format_html('src="{}" srcset="{}" sizes="{}" width="{}" height="{}"',
                       n["src"], n["srcset"], n["sizes"], n["width"], n["height"])


@register.filter
def og_gorsel_adresi(nesne) -> str:
    """og:image / twitter:image için 1200×630 JPEG türevinin MUTLAK adresi.

    Kanonik kök `SITE_KOKU`dan gelir, istek konağından değil (SEO bulgusu).
    Görsel yoksa boş döner; meta etiketini basan şablon boşsa basmamalı.
    """
    kaynak = kaynak_yolu(nesne)
    if not kaynak:
        return ""
    return settings.SITE_KOKU.rstrip("/") + gt.adres("og", kaynak)
