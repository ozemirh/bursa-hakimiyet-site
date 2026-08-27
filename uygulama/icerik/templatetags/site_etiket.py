"""Şablon süzgeçleri — görselsiz haberi kategori temsiliyle çizmek için.

Arşivin büyük bölümünde yerel görsel yok (URUN-PLANI.md F3 notu: 2023-07
öncesi dosyalar sağlayıcı tarafından silindi, kurtarılamıyor). Karar:
uzak adrese bağlanmak yerine kategoriye ait **temsilî SVG** çizilir. Simge
kütüphanesi `parca/simgeler.html` içinde duruyor ve tasarımdan geliyor.

Eşleme kategori **adına** göredir; slug adresin parçası olduğu için burada
kullanılmaz — slug değişmez ama ad birleştirilebilir.
"""

from django import template

register = template.Library()

# kategori adı -> (svg simge kimliği, renk sınıfı)
ESLEME = {
    "GÜNDEM": ("sc-cami", "t-mavi"),
    "BURSA": ("sc-cami", "t-mavi"),
    "BURSASPOR": ("sc-spor", "t-yesil"),
    "SPOR": ("sc-spor", "t-yesil"),
    "EKONOMİ": ("sc-fabrika", "t-turuncu"),
    "DÜNYA": ("sc-gol", "t-mavi"),
    "MAGAZİN": ("sc-muze", "t-mor"),
    "SAĞLIK": ("sc-saglik", "t-kirmizi"),
    "TEKNOLOJİ": ("sc-fabrika", "t-mor"),
    "YAŞAM": ("sc-tarim", "t-yesil"),
    "AKTÜALİTE": ("sc-adliye", "t-gri"),
    "SAVUNMA SANAYİ": ("sc-fabrika", "t-gri"),
    "KÜLTÜR": ("sc-muze", "t-mor"),
    "ASAYİŞ": ("sc-adliye", "t-gri"),
}

VARSAYILAN = ("sc-uludag", "t-gri")


def _esle(kategori):
    if kategori is None:
        return VARSAYILAN
    return ESLEME.get((kategori.ad or "").upper(), VARSAYILAN)


@register.filter
def simge_adi(kategori) -> str:
    return _esle(kategori)[0]


@register.filter
def renk_sinifi(kategori) -> str:
    return _esle(kategori)[1]


# -- Türkçe büyük/küçük harf ----------------------------------------------
#
# Kategori adları kaynakta BÜYÜK harf ("EKONOMİ"); sayfada kimi yerde başlık,
# kimi yerde büyük harf isteniyor. Python'un kendi metotları Türkçe'de yanlış
# sonuç verir:
#   "EKONOMİ".title()   -> "Ekonomi̇"  (İ'nin noktası ayrı birleşen kalır)
#   "IĞDIR".lower()     -> "iğdir"    (doğrusu "ığdır")
#   "Ekonomi".upper()   -> "EKONOMI"  (doğrusu "EKONOMİ")
# Bu yüzden i/ı ve İ/I çiftleri elle çevrilir.

_KUCULT = {"I": "ı", "İ": "i"}
_BUYULT = {"i": "İ", "ı": "I"}


def _kucult(metin: str) -> str:
    return "".join(_KUCULT.get(c, c) for c in metin).lower()


def _buyult(metin: str) -> str:
    return "".join(_BUYULT.get(c, c) for c in metin).upper()


def _kisaltma_mi(kelime: str) -> bool:
    """Kısaltmalar küçültülmemeli: "A.Ş." -> "A.ş." olurdu.

    Ölçüt: noktalı ve kısa (A.Ş. · T.C.) ya da üç harfe kadar tümü büyük
    (FK · TFF · BB). "TOFAŞ" gibi beş harfli adlar kısaltma sayılmaz,
    onlar başlık biçimine girer.
    """
    if not kelime:
        return False
    if "." in kelime and len(kelime) <= 5:
        return True
    harfler = [c for c in kelime if c.isalpha()]
    return bool(harfler) and len(harfler) <= 3 and kelime == _buyult(kelime)


@register.filter
def baslikla(metin) -> str:
    '''"EKONOMİ" -> "Ekonomi", "GALATASARAY A.Ş." -> "Galatasaray A.Ş.".'''
    if not metin:
        return ""
    cikti = []
    for kelime in str(metin).split():
        if _kisaltma_mi(kelime):
            cikti.append(kelime)
            continue
        kucuk = _kucult(kelime)
        cikti.append(_buyult(kucuk[:1]) + kucuk[1:])
    return " ".join(cikti)


@register.filter
def buyult(metin) -> str:
    '''"Ekonomi" -> "EKONOMİ". Django'nun `|upper` süzgeci i harfini bozar.'''
    return _buyult(str(metin)) if metin else ""


# -- canlı veri süzgeçleri ------------------------------------------------

GUN_KISA = ["Pzt", "Sal", "Çar", "Per", "Cum", "Cmt", "Paz"]


@register.filter
def kisa_gun(tarih_iso) -> str:
    """`2026-08-28` -> `Cum`. Hava şeridinde yalnız üç harf sığıyor."""
    from datetime import date
    try:
        return GUN_KISA[date.fromisoformat(str(tarih_iso)).weekday()]
    except (TypeError, ValueError):
        return ""


@register.filter
def sozluk(kaynak, anahtar):
    """Şablonda `sozluk[anahtar]` yazılamaz; anahtar değişkense bu gerekir."""
    try:
        return kaynak.get(anahtar, "")
    except AttributeError:
        return ""


@register.filter
def kisa_lig(ad) -> str:
    """Sekmeye sığan kısa lig adı: sponsor adı düşer.

    "Trendyol Süper Lig" -> "SÜPER", "Nesine 2. Lig" -> "2. LİG".
    Sponsor adları sezon başında değiştiği için kodda sabit tutulamaz;
    baştaki sponsor kelimesi atılıyor.
    """
    parcalar = str(ad).split()
    if len(parcalar) > 2:          # sponsor adı baştan düşer
        parcalar = parcalar[1:]
    kisa = _buyult(" ".join(parcalar))
    # Tasarımdaki sekme adları: SÜPER · 1. LİG · 2. LİG · 3. LİG
    return "SÜPER" if kisa.startswith("SÜPER") else kisa


# -- görselsiz kartlar ----------------------------------------------------
#
# Arşivin %99,98'inde yerel görsel yok, yani bir kategori kutusundaki
# kartların hepsi aynı temsilî çizimi alıyordu: Bursaspor kutusunda altı
# birebir aynı yeşil saha. Ölü ve dikkat dağıtıcı duruyordu.
#
# Çözüm: çizim kategoriye bağlı kalır (anlamını korur), **rengi** kaydın
# kimliğinden türetilir. Aynı haber her zaman aynı rengi alır — sayfa
# yenilenince kart rengi değişmez, bu da titremeyi önler.

# Gri bilerek yok: cesitleme paletinde soluk kaliyordu. Yalnizca
# kategorisi bilinmeyen kayitlarin taban rengi olarak duruyor.
PALET = ["t-mavi", "t-yesil", "t-turuncu", "t-mor", "t-kirmizi"]


@register.filter
def kart_rengi(kayit) -> str:
    """Kaydın kimliğinden türeyen, sabit ve tekrarlanabilir renk sınıfı."""
    kategori = getattr(kayit, "kategori", None)
    taban = _esle(kategori)[1]
    kimlik = getattr(kayit, "pk", None)
    if not kimlik:
        return taban
    # Kategorinin kendi rengi listenin başına alınır ki baskın renk o olsun.
    sirali = [taban] + [r for r in PALET if r != taban]
    return sirali[kimlik % len(sirali)]


@register.filter
def kart_simgesi(kayit) -> str:
    """Çizim kategoriye bağlı kalır; anlamı taşıyan taraf budur."""
    return _esle(getattr(kayit, "kategori", None))[0]


@register.filter
def mutlak(sayi):
    """İşaretsiz değer.

    Bandda yön zaten okla gösteriliyor; değerin başındaki eksi ile
    birlikte "▼ %-0,28" gibi çift olumsuz okunuyordu.
    """
    try:
        return abs(float(sayi))
    except (TypeError, ValueError):
        return sayi
