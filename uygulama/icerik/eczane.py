"""Nöbetçi eczane sayfaları ve günlük haber metni — tek kaynak.

`canli.eczane_paneli()` dosyayı okunabilir bir yapıya çeviriyor; burası o
yapıyı **iki tüketiciye** hazırlıyor:

1. `/nobetci-eczane` ve `/nobetci-eczane/<ilçe>` kalıcı sayfaları
   (`views.nobetci_eczane`),
2. her sabah açılan günlük haber kaydı
   (`management/commands/eczane_haberi.py`).

İkisinin de metni buradan çıkıyor. Ayrı ayrı yazılsalardı başlık kalıbı,
ilçe adı çözümü ve kaynak cümlesi iki yerde yaşar, biri güncellenip öteki
unuturdu.

## Neden kalıcı sayfa VE günlük haber

"bursa nöbetçi eczane" her gün aranan **aynı** sorgudur; arama motoru
böyle sorgularda tek bir güncel adresi sıralar. Her gün yeni bir haber
açmak birbirinin neredeyse aynısı yüzlerce sayfa üretir ve bunlar
birbiriyle yarışır. Bu yüzden asıl hedef kalıcı sayfalardır:
`/nobetci-eczane` ile 17 ilçe adresi her gün kendini tazeler, adres
değişmez.

Günlük haber ayrı bir işi yapar: tarihli sorgular ("31 ağustos nöbetçi
eczane"), gazetenin kendi akışı, RSS ve Google News. Haberin kanonik
adresi kendisidir — arşivde o günün kaydı olarak kalır — ama gövdesi
okuru **güncel** liste için kalıcı sayfaya yollar.

## İki kural

**Uydurma yok.** Sayfa da haber de yalnız `nobetci-eczane.json` içindeki
alanları basar. Telefonu ya da konumu olmayan eczane o satır olmadan
geçer. "Bugün bu ilçede nöbetçi eczane yok" cümlesi de veridir: kaynak o
ilçe için kayıt döndürmediyse öyle yazılır, yakın ilçeye yönlendirilir.

**Kaynak her zaman görünür.** Her sayfanın ve her haberin sonunda Bursa
Eczacı Odası adı ve nöbet listesinin resmî sahibi olduğu yazar. Nöbet
saatleri de eczaneden doğrulanabilsin diye telefon hep basılır.
"""

from __future__ import annotations

from datetime import date

from django.utils import formats
from django.utils.text import slugify

from taksonomi.models import Ilce

from .canli import _tr_sirala, eczane_paneli, oku
# Python'un `.title()` ve `.lower()` metotları Türkçeyi bozuyor: "ECZANESİ"
# → "Eczanesi̇" (harfin üstünde birleşen nokta kalıyor, ölçüldü). Sayfanın
# geri kalanı da bu süzgeci kullanıyor.
from .templatetags.site_etiket import baslikla

# Nöbet listesinin resmî sahibi. Metinlerde adı ve niteliği birlikte
# geçer: okur bilgiyi kimin verdiğini bilmeli.
KAYNAK_ADI = "Bursa Eczacı Odası"
KAYNAK_NITELIK = ("Türk Eczacıları Birliği 7. Bölge odası, nöbet "
                  "listesinin resmî sahibi")

KOK_YOL = "/nobetci-eczane"


def _tarih_yaz(gun) -> str:
    """`date` → "31 Ağustos 2026". Ay adı Django'nun tr yerelinden."""
    return formats.date_format(gun, "j F Y") if gun else ""


def _gun_adi(gun) -> str:
    return formats.date_format(gun, "l") if gun else ""


def ilce_yolu(anahtar: str) -> str:
    return f"{KOK_YOL}/{anahtar}" if anahtar else KOK_YOL


def ilce_adlari() -> dict[str, str]:
    """`{"osmangazi": "Osmangazi", …}` — 17 ilçe, veritabanından.

    Kaynak ilçeyi büyük harfle ve nöbet bölgesi olarak veriyor
    ("OSMANGAZİ - DEMİRTAŞ"); sayfada gazetenin kendi ilçe adı yazmalı ki
    ilçe sayfasıyla (`/ilce/osmangazi`) aynı sözcük görünsün.
    `canli._ilce_anahtar()` ile `Ilce.slug` birebir aynı 17 değeri
    üretiyor (ölçüldü, 31 Ağustos 2026).
    """
    return {i.slug: i.ad for i in Ilce.objects.all()}


def gunun_paketi(gun: date | None = None) -> dict | None:
    """Kalıcı sayfaların ve haberin ortak veri paketi.

    `gun` yalnızca **denetim** içindir: dosya hangi günü taşıyorsa o
    basılır, istenen günün verisi uydurulmaz. İstenen gün dosyadakinden
    farklıysa None döner — dünün listesini bugünün haberi diye yayımlamak
    okuru kapalı eczaneye gönderir.
    """
    panel = eczane_paneli(oku("nobetci-eczane"))
    if not panel:
        return None
    if gun and panel["gun"] != gun:
        return None
    return panel


def ilcelere_bol(panel: dict) -> list[dict]:
    """Eczaneleri ilçe ilçe gruplar; sıra `canli.eczane_paneli`den gelir.

    Dönen her öğe: `anahtar`, `ad` (gazetenin ilçe adı), `yol`,
    `eczaneler`. Bugün nöbetçisi olmayan ilçe listede **yer almaz** —
    boş başlık basmak "veri yok"u "eczane yok" gibi gösterir.
    """
    adlar = ilce_adlari()
    sepet: dict[str, dict] = {}
    sira: list[dict] = []
    for e in panel["eczaneler"]:
        anahtar = e["ilce_anahtar"]
        kutu = sepet.get(anahtar)
        if kutu is None:
            kutu = {"anahtar": anahtar,
                    "ad": adlar.get(anahtar) or baslikla(e["ilce"].split(" - ")[0]),
                    "yol": ilce_yolu(anahtar),
                    "eczaneler": []}
            sepet[anahtar] = kutu
            sira.append(kutu)
        kutu["eczaneler"].append(e)
    return sira


# -- kalıcı sayfa ---------------------------------------------------------

def sayfa_basligi(ilce_ad: str, gun) -> str:
    """Sekmede ve arama sonucunda görünen başlık.

    Kalıp okurun arama kutusuna yazdığı sırayla: yer + "nöbetçi eczane" +
    tarih. Tarih başlıkta çünkü liste günlük; tarihsiz başlık okura
    verinin ne kadar taze olduğunu söylemiyor.
    """
    yer = ilce_ad or "Bursa"
    tarih = _tarih_yaz(gun)
    return f"{yer} Nöbetçi Eczaneler — {tarih}" if tarih \
        else f"{yer} Nöbetçi Eczaneler"


def sayfa_aciklamasi(ilce_ad: str, panel: dict | None, adet: int) -> str:
    yer = ilce_ad or "Bursa"
    if not panel:
        return (f"{yer} nöbetçi eczane listesi: adres, telefon ve nöbet "
                f"saatleri. Kaynak: {KAYNAK_ADI}.")
    tarih = _tarih_yaz(panel["gun"])
    if not adet:
        return (f"{tarih} tarihinde {yer} ilçesinde nöbetçi eczane "
                f"görünmüyor. Bursa genelindeki nöbetçi eczaneler ve "
                f"telefonları bu sayfada.")
    return (f"{tarih} {yer} nöbetçi eczaneler: {adet} eczanenin adresi, "
            f"telefonu ve nöbet saati. Kaynak: {KAYNAK_ADI}.")


def sayfa_baglami(slug: str = "") -> dict:
    """Sayfanın bütün bağlamı. Veri yoksa da sözlük döner — sayfa 200'dür.

    Gerekçe: adres kalıcı ve arama motoruna kayıtlı. Çekme betiği bir tur
    kaçırdı diye 404 vermek, sayfayı dizinden düşürür. Veri yoksa okur
    bunu açıkça okur ve odanın kendi sayfasına yönlendirilir.
    """
    panel = gunun_paketi()
    adlar = ilce_adlari()
    ilce_ad = adlar.get(slug, "") if slug else ""

    tumu = panel["eczaneler"] if panel else []
    kayitlar = [e for e in tumu if e["ilce_anahtar"] == slug] if slug else tumu
    gruplar = [] if slug else (ilcelere_bol(panel) if panel else [])

    # Gezinme şeridi 17 ilçenin TAMAMINI taşır, yalnız bugün nöbetçisi
    # olanları değil: okur kendi ilçesini listede bulamazsa sayfanın
    # eksik olduğunu düşünür. Bugün nöbetçisi olmayan ilçe adedi 0 ile
    # işaretli görünür.
    sayilar: dict[str, int] = {}
    for e in tumu:
        sayilar[e["ilce_anahtar"]] = sayilar.get(e["ilce_anahtar"], 0) + 1
    # Sıra Türkçe alfabeyle: `sorted` varsayılanı İnegöl ve İznik'i
    # şeridin EN SONUNA atıyordu (ölçüldü, ekran görüntüsüyle görüldü).
    serit = [{"anahtar": a, "ad": ad, "yol": ilce_yolu(a),
              "adet": sayilar.get(a, 0), "secili": a == slug}
             for a, ad in sorted(adlar.items(), key=lambda p: _tr_sirala(p[1]))]

    return {
        "panel": panel,
        "ilce_slug": slug,
        "ilce_ad": ilce_ad,
        "eczaneler": kayitlar,
        "gruplar": gruplar,
        "serit": serit,
        "adet": len(kayitlar),
        "yol": ilce_yolu(slug),
        "baslik": sayfa_basligi(ilce_ad, panel["gun"] if panel else None),
        "aciklama": sayfa_aciklamasi(ilce_ad, panel, len(kayitlar)),
        "kaynak_adi": KAYNAK_ADI,
        "kaynak_nitelik": KAYNAK_NITELIK,
        "kok_yol": KOK_YOL,
    }


def yapisal_veri(baglam: dict) -> dict:
    """Sayfanın JSON-LD'si: nöbetçi eczanelerin sıralı listesi.

    Yalnızca dosyada **olan** alanlar yazılır. Telefonu olmayan eczanede
    `telephone` anahtarı hiç açılmaz; boş dize yazmak yapısal veride de
    uydurmadır. `openingHours` yerine `openingHoursSpecification` var
    çünkü nöbet bir haftalık düzen değil, o güne ait tek aralık.
    """
    panel = baglam["panel"]
    if not panel or not baglam["eczaneler"]:
        return {}
    ogeler = []
    for sira, e in enumerate(baglam["eczaneler"], start=1):
        eczane = {
            "@type": "Pharmacy",
            "name": baslikla(e["ad"]),
            "address": {"@type": "PostalAddress",
                        "addressLocality": baslikla(e["ilce"].split(" - ")[0]),
                        "addressRegion": "Bursa",
                        "addressCountry": "TR"},
        }
        if e["adres"]:
            eczane["address"]["streetAddress"] = e["adres"]
        if e["telefon"]:
            eczane["telephone"] = e["telefon_baglanti"] or e["telefon"]
        if e["enlem"] is not None and e["boylam"] is not None:
            eczane["geo"] = {"@type": "GeoCoordinates",
                             "latitude": e["enlem"], "longitude": e["boylam"]}
        if e["baslangic"] and e["bitis"]:
            eczane["openingHoursSpecification"] = {
                "@type": "OpeningHoursSpecification",
                "opens": e["baslangic"].isoformat(),
                "closes": e["bitis"].isoformat(),
            }
        ogeler.append({"@type": "ListItem", "position": sira,
                       "item": eczane})
    return {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": baglam["baslik"],
        "numberOfItems": len(ogeler),
        "itemListElement": ogeler,
    }


# -- günlük haber ---------------------------------------------------------

def haber_basligi(panel: dict) -> str:
    """Tarih önde: okur "31 ağustos nöbetçi eczane" diye arıyor.

    İlçe adları başlığa girmez — başlık 300 karakteri aşmasa da okunmaz
    hâle gelir ve ilçe sorgusunun karşılığı ilçenin **kendi kalıcı
    sayfasıdır**, haber değil.
    """
    return (f"{_tarih_yaz(panel['gun'])} Bursa nöbetçi eczaneler: "
            f"ilçe ilçe adres ve telefon listesi")


def haber_slug(panel: dict) -> str:
    """Günlük haberin adres dilimi — **başlıktan değil, günden** türer.

    Başlıktan türetilseydi başlık kalıbını değiştirdiğimiz gün slug da
    değişir, komut aynı günün haberini bulamayıp ikinci kayıt açardı.
    Ayrıca "…-ilce-ilce-adres-ve-telefon-listesi" kuyruğu adresi uzatıyor;
    adres okurun aradığı üç sözcüğü taşımalı.
    """
    return slugify(f"{_tarih_yaz(panel['gun'])} Bursa nobetci eczaneler",
                   allow_unicode=False)


def haber_spotu(panel: dict) -> str:
    gun_adi = _gun_adi(panel["gun"])
    ilce_adedi = len({e["ilce_anahtar"] for e in panel["eczaneler"]})
    pencere = f" Nöbet çoğu eczanede {panel['pencere']}." if panel["pencere"] else ""
    return (f"{_tarih_yaz(panel['gun'])} {gun_adi} günü Bursa'da "
            f"{panel['sayi']} eczane {ilce_adedi} ilçede nöbet tutuyor."
            f"{pencere} Adresler, telefonlar ve nöbet saatleri aşağıda.")


def _kacis(metin: str) -> str:
    return (str(metin).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;"))


def haber_govdesi(panel: dict) -> str:
    """Haberin HTML gövdesi.

    `icerik/temizle.py` beyaz listesine göre yazılır (`p`, `h3`, `ul`,
    `li`, `strong`, `a`) — `div`, `span`, `table` temizleyicide düşerdi.
    """
    tarih = _tarih_yaz(panel["gun"])
    gruplar = ilcelere_bol(panel)
    satir = [
        f"<p><strong>{_kacis(tarih)}</strong> tarihinde Bursa'da "
        f"{panel['sayi']} eczane nöbetçi. Liste ilçe ilçe aşağıda; her "
        f"eczanenin adresi, telefonu ve nöbetinin bittiği saat yazıyor. "
        f"Nöbet saatleri eczaneden eczaneye değişiyor, yola çıkmadan önce "
        f"telefonla teyit edilmesi yararlı olur.</p>",
        f'<p>Gün içinde değişen <a href="{KOK_YOL}">güncel Bursa nöbetçi '
        f"eczane listesi</a> ayrı sayfada tutuluyor; bu haber "
        f"{_kacis(tarih)} gününün kaydıdır.</p>",
    ]
    for grup in gruplar:
        satir.append(f'<h3>{_kacis(grup["ad"])} nöbetçi eczaneler</h3>')
        satir.append("<ul>")
        for e in grup["eczaneler"]:
            parca = [f'<strong>{_kacis(baslikla(e["ad"]))}</strong>']
            if e["adres"]:
                parca.append(_kacis(e["adres"]))
            if e["telefon"]:
                parca.append(f'Tel: {_kacis(e["telefon"])}')
            if e["saat"]:
                parca.append(f'Nöbet: {_kacis(e["saat"])}')
            satir.append("<li>" + " &mdash; ".join(parca) + "</li>")
        satir.append("</ul>")
        satir.append(
            f'<p><a href="{grup["yol"]}">{_kacis(grup["ad"])} nöbetçi eczane '
            f"sayfası</a> her gün güncelleniyor.</p>")
    satir.append(
        f"<p>Liste {_kacis(KAYNAK_ADI)} ({_kacis(KAYNAK_NITELIK)}) "
        f"tarafından yayımlanan nöbet çizelgesinden alınmıştır. Nöbet "
        f"devri gün içinde yapıldığı için saatler ilçeye göre değişebilir.</p>")
    return "\n".join(satir)


def haber_paketi(panel: dict) -> dict:
    """Komutun `Haber` alanlarına yazacağı sözlük."""
    tarih = _tarih_yaz(panel["gun"])
    return {
        "baslik": haber_basligi(panel),
        "spot": haber_spotu(panel),
        "govde": haber_govdesi(panel),
        "seo_baslik": f"{tarih} Bursa Nöbetçi Eczaneler | Bursa Hakimiyet",
        "slug": haber_slug(panel),
        "odak_kelime": "bursa nöbetçi eczane",
        "etiketler": ["Nöbetçi eczane", "Bursa", "Eczane"],
    }
