"""SEO sinyalleri: kanonik adres, paylaşım görseli, JSON-LD (Paket G, 19 Ekim 2026).

DEGERLENDIRME-2026-10 §3 bulgu 8: canlı sitede olup bizde olmayan her sinyal
kesim günü gerileme demektir. Bu modül üç şeyi tek yerden kurar:

1. **Kanonik adres `SITE_KOKU`dan.** Eskiden şablonlar
   `request.scheme://request.get_host` yazıyordu; vekil arkasında bu
   `http://` ya da `www`'suz çıkar ve Google iki kopya görür. Kanonik yalnız
   **yol + geçerli `?sayfa=N` (N>1)** taşır — sayfa önbelleğinin anahtarıyla
   aynı küme (`sayfa_onbellegi.ANAHTAR_PARAMETRELERI`), yani önbellekten gelen
   sayfanın kanoniği de doğrudur. `utm_*`, `fbclid` kanoniğe girmez.
2. **Paylaşım görseli.** Görseli olan kayıtta 1200×630 türev
   (`gorsel_etiket.og_gorsel_adresi`), olmayan sayfada logodan üretilmiş
   `statik/simge/paylasim.png`.
3. **JSON-LD sözlükleri.** Basım `icerik/jsonld.betik_json` ile yapılır
   (şablonda `|safe` yasak, `tests_jsonld`). Alanlar Google'ın Article,
   Breadcrumb ve Organization belgelerindeki zorunlu/önerilen listeden.

Görünür olmayan şey işaretlenmez (Google yapılandırılmış veri ilkesi):
video sayfası oynatıcı gömmediği için `VideoObject` değil `WebPage` alır;
oynatıcı gömüldüğünde `VideoObject`e geçilir.
"""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

from django.conf import settings
from django.templatetags.static import static
from django.utils import timezone
from django.utils.encoding import iri_to_uri
from django.utils.html import strip_tags
from django.utils.text import Truncator

SITE_ADI = "Bursa Hakimiyet"
DIL = "tr-TR"

#: Gazetenin resmî hesapları. Kaynak: canlı sitenin kendi Organization
#: JSON-LD'si ve alt bilgisi (19 Ekim 2026'da okundu). Uydurma değil; yeni
#: hesap ancak gazete bildirirse eklenir.
RESMI_HESAPLAR = (
    "https://www.facebook.com/bursahakimiyet/",
    "https://x.com/b_hakimiyet",
    "https://www.instagram.com/bursahakimiyetcomtr/",
    "https://www.youtube.com/channel/UC6G3b-ZS2OrB_v4thAXP9EQ",
)

#: Google: başlık 110 karakteri aşmamalı.
BASLIK_SINIRI = 110
ACIKLAMA_SINIRI = 300

#: Konu sayfası bu sayının altında haber taşıyorsa `noindex,follow`
#: (ince içerik; 19.966 dosyanın 11.559'u 3–4 haberli, SEO değerlendirmesi).
INCE_KONU_ESIGI = 5

ROBOTS_ACIK = "index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1"
ROBOTS_KAPALI = "noindex, follow"


# --- adres -------------------------------------------------------------------

def kok() -> str:
    return settings.SITE_KOKU.rstrip("/")


def mutlak(yol: str) -> str:
    if not yol:
        return ""
    if yol.startswith(("http://", "https://")):
        return yol
    return kok() + iri_to_uri(yol)


def sayfa_numarasi(request) -> int:
    """`?sayfa=N` geçerli bir tamsayıysa N, değilse 1."""
    ham = (request.GET.get("sayfa") or "").strip()
    try:
        return max(int(ham), 1) if ham else 1
    except ValueError:
        return 1


def kanonik_adres(request, yol: str | None = None) -> str:
    adres = mutlak(yol if yol is not None else request.path)
    numara = sayfa_numarasi(request)
    if numara > 1:
        adres += f"?sayfa={numara}"
    return adres


def statik_mutlak(yol: str) -> str:
    return mutlak(static(yol))


@lru_cache(maxsize=1)
def tema_rengi() -> str:
    """`theme-color` — `site.css` `:root`taki `--lacivert`ten okunur.

    Renk şablona elle yazılmaz (renk her zaman değişkenden); değişken
    değişirse tarayıcı çubuğu da kendiliğinden değişir.
    """
    yol = Path(settings.BASE_DIR) / "statik" / "stil" / "site.css"
    try:
        eslesme = re.search(r"--lacivert\s*:\s*(#[0-9a-fA-F]{3,8})",
                            yol.read_text(encoding="utf-8"))
    except OSError:
        eslesme = None
    return eslesme.group(1) if eslesme else ""


def baglam(request):
    """Bağlam işlemcisi: her sayfanın varsayılan kanoniği ve site kökü."""
    return {
        "site_koku": kok(),
        "kanonik_adres": kanonik_adres(request),
        "seo_varsayilan_gorsel": statik_mutlak("simge/paylasim.png"),
        "seo_tema_rengi": tema_rengi(),
    }


# --- yardımcılar ---------------------------------------------------------------

def _metin(deger, sinir: int) -> str:
    duz = " ".join(strip_tags(str(deger or "")).split())
    return Truncator(duz).chars(sinir) if duz else ""


def _zaman(deger) -> str | None:
    if not deger:
        return None
    if timezone.is_naive(deger):
        deger = timezone.make_aware(deger)
    return timezone.localtime(deger).isoformat(timespec="seconds")


def degisiklik_zamani(kayit):
    """Güncelleme ancak yayından SONRAYSA güncellemedir.

    Arşivin 431 bin haberinde `guncelleme_zamani` yayın anına eşit (ölçüldü);
    eşitlik "güncellendi" diye okunmaz. Bir dakikadan kısa fark da sayılmaz.
    """
    yayin = getattr(kayit, "yayin_zamani", None)
    guncel = getattr(kayit, "guncelleme_zamani", None)
    if yayin and guncel and (guncel - yayin).total_seconds() >= 60:
        return guncel
    return None


def _baslikla(metin) -> str:
    from .templatetags.site_etiket import baslikla
    return baslikla(metin)


def logo() -> dict:
    return {"@type": "ImageObject", "url": statik_mutlak("simge/simge-512.png"),
            "width": 512, "height": 512}


def yayinci() -> dict:
    return {"@type": "NewsMediaOrganization", "@id": kok() + "/#kurulus",
            "name": SITE_ADI, "url": kok() + "/", "logo": logo()}


def kurulus() -> dict:
    veri = {"@context": "https://schema.org", **yayinci(),
            "sameAs": list(RESMI_HESAPLAR)}
    veri["inLanguage"] = DIL
    return veri


def web_sitesi() -> dict:
    return {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "@id": kok() + "/#site",
        "name": SITE_ADI,
        "url": kok() + "/",
        "inLanguage": DIL,
        "publisher": {"@id": kok() + "/#kurulus"},
        "potentialAction": {
            "@type": "SearchAction",
            "target": {"@type": "EntryPoint",
                       "urlTemplate": kok() + "/ara?q={search_term_string}"},
            "query-input": "required name=search_term_string",
        },
    }


def kirinti(ogeler) -> dict:
    """`ogeler`: [(ad, yol), …]. Son öğenin yolu boş olabilir (Google izinli)."""
    liste = []
    for sira, (ad, yol) in enumerate(ogeler, start=1):
        oge = {"@type": "ListItem", "position": sira, "name": _metin(ad, 200)}
        if yol:
            oge["item"] = mutlak(yol)
        liste.append(oge)
    return {"@context": "https://schema.org", "@type": "BreadcrumbList",
            "itemListElement": liste}


def gorsel_dizisi(nesne) -> list[dict]:
    """og (1200×630) + 16:9 + 4:3 + 1:1 kırpımları; görsel yoksa boş."""
    from . import gorsel_turev as gt
    from .templatetags.gorsel_etiket import kaynak_yolu
    kaynak = kaynak_yolu(nesne)
    if not kaynak:
        yol = getattr(nesne, "gorsel_yolu", "")
        yol = yol() if callable(yol) else yol
        return [{"@type": "ImageObject", "url": mutlak(yol)}] if yol else []
    dizi = []
    for ad in ("16x9", "4x3", "1x1", "og"):
        en, boy = gt.KIRPIMLAR[ad]
        dizi.append({"@type": "ImageObject", "url": mutlak(gt.adres(ad, kaynak)),
                     "width": en, "height": boy})
    return dizi


def _makale_ortak(kayit, tur: str, adres: str) -> dict:
    yayin = getattr(kayit, "yayin_zamani", None)
    degisti = degisiklik_zamani(kayit) or yayin
    veri = {
        "@context": "https://schema.org",
        "@type": tur,
        "headline": _metin(kayit.baslik, BASLIK_SINIRI),
        "url": adres,
        "mainEntityOfPage": {"@type": "WebPage", "@id": adres},
        "inLanguage": DIL,
        "isAccessibleForFree": True,
        "publisher": yayinci(),
    }
    aciklama = _metin(getattr(kayit, "spot", ""), ACIKLAMA_SINIRI)
    if aciklama:
        veri["description"] = aciklama
    if yayin:
        veri["datePublished"] = _zaman(yayin)
        veri["dateModified"] = _zaman(degisti)
    gorseller = gorsel_dizisi(kayit)
    if gorseller:
        veri["image"] = gorseller
    return veri


# --- sayfa türleri -----------------------------------------------------------------

def haber_makalesi(haber) -> dict:
    adres = mutlak(haber.get_absolute_url())
    veri = _makale_ortak(haber, "NewsArticle", adres)
    # Yazar: imza satırıyla AYNI kaynak (`muhabir`, Paket H). Muhabir yoksa
    # haber gazetenin kurumsal imzasıyladır — uydurma kişi adı yazılmaz.
    muhabir = (getattr(haber, "muhabir", "") or "").strip()
    if muhabir:
        veri["author"] = [{"@type": "Person", "name": muhabir}]
    else:
        veri["author"] = [{"@type": "Organization", "name": SITE_ADI,
                           "url": kok() + "/"}]
    if haber.kategori_id:
        veri["articleSection"] = _baslikla(haber.kategori.ad)
    return veri


def haber_kirintisi(haber) -> dict:
    return kirinti([("Anasayfa", "/"),
                    (_baslikla(haber.kategori.ad), f"/{haber.kategori.slug_al()}"),
                    (haber.baslik, haber.get_absolute_url())])


def kose_makalesi(yazi) -> dict:
    adres = mutlak(yazi.get_absolute_url())
    veri = _makale_ortak(yazi, "OpinionNewsArticle", adres)
    yazar = yazi.yazar
    veri["author"] = [{"@type": "Person", "name": yazar.ad,
                       "url": mutlak(yazar.get_absolute_url())}]
    veri["articleSection"] = "Köşe Yazıları"
    if not veri.get("image"):
        portre = gorsel_dizisi(yazar)
        if portre:
            veri["image"] = portre
    return veri


def kose_kirintisi(yazi) -> dict:
    return kirinti([("Anasayfa", "/"), ("Yazarlar", "/yazarlar"),
                    (yazi.yazar.ad, yazi.yazar.get_absolute_url()),
                    (yazi.baslik, yazi.get_absolute_url())])


def yazar_profili(yazar) -> dict:
    adres = mutlak(yazar.get_absolute_url())
    kisi = {"@type": "Person", "name": yazar.ad, "url": adres}
    if getattr(yazar, "unvan", ""):
        kisi["jobTitle"] = yazar.unvan
    portre = gorsel_dizisi(yazar)
    if portre:
        kisi["image"] = portre[0]["url"]
    kisi["worksFor"] = {"@id": kok() + "/#kurulus"}
    return {"@context": "https://schema.org", "@type": "ProfilePage",
            "url": adres, "inLanguage": DIL, "mainEntity": kisi}


def galeri_sayfasi(galeri, kareler=()) -> dict:
    adres = mutlak(galeri.get_absolute_url())
    veri = {"@context": "https://schema.org", "@type": "ImageGallery",
            "name": _metin(galeri.baslik, BASLIK_SINIRI), "url": adres,
            "inLanguage": DIL, "publisher": yayinci()}
    aciklama = _metin(galeri.spot, ACIKLAMA_SINIRI)
    if aciklama:
        veri["description"] = aciklama
    if galeri.yayin_zamani:
        veri["datePublished"] = _zaman(galeri.yayin_zamani)
        veri["dateModified"] = _zaman(degisiklik_zamani(galeri) or galeri.yayin_zamani)
    gorseller = gorsel_dizisi(galeri)
    for kare in list(kareler)[:20]:
        yol = kare.gorsel_yolu() if callable(kare.gorsel_yolu) else kare.gorsel_yolu
        if yol:
            oge = {"@type": "ImageObject", "contentUrl": mutlak(yol)}
            alt = _metin(getattr(kare, "aciklama", "") or getattr(kare, "alt", ""), 200)
            if alt:
                oge["caption"] = alt
            gorseller.append(oge)
    if gorseller:
        veri["image"] = gorseller
    return veri


def video_sayfasi(video) -> dict:
    adres = mutlak(video.get_absolute_url())
    veri = {"@context": "https://schema.org", "@type": "WebPage",
            "name": _metin(video.baslik, BASLIK_SINIRI), "url": adres,
            "inLanguage": DIL, "publisher": yayinci()}
    aciklama = _metin(video.spot, ACIKLAMA_SINIRI)
    if aciklama:
        veri["description"] = aciklama
    if video.yayin_zamani:
        veri["datePublished"] = _zaman(video.yayin_zamani)
    gorseller = gorsel_dizisi(video)
    if gorseller:
        veri["primaryImageOfPage"] = gorseller[0]
    return veri


def medya_kirintisi(kayit, bolum_ad: str, bolum_yol: str) -> dict:
    return kirinti([("Anasayfa", "/"), (bolum_ad, bolum_yol),
                    (kayit.baslik, kayit.get_absolute_url())])


def ince_konu_mu(konu) -> bool:
    return (getattr(konu, "haber_sayisi", 0) or 0) < INCE_KONU_ESIGI
