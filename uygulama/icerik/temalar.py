"""Sayfaya özel tasarım — TEK KAYIT YERİ (19 Ekim 2026).

Kullanıcı kararı (19 Ekim 2026): sitenin geneli kırmızı · lacivert · beyaz;
Bursaspor sayfası yeşil-beyaz; seçilen sayfalar sayfaya özel tasarım alır.
Seçilenler: **köşe yazıları, ekonomi, teknoloji** (Bursaspor'a ek olarak).
Bu dosyaya giren her satır o kararın izidir — **hangi sayfanın** tema
alacağına kullanıcı karar verir (EKIP.md, eşik konu 7). Ajan kendiliğinden
satır eklemez.

Düzenek üç parçadır ve üçü de bu kayda bağlıdır:

1. **Gövde niteliği.** Görünüm `tema` bağlamını basar, `taban.html`
   `<body data-bolum="{{ tema.anahtar }}">` yazar.
2. **Değişken takımı.** `site.css` içinde her tema için tek bir
   `body[data-bolum="…"] main{…}` bloğu vardır ve o blok YALNIZ rol
   değişkenlerini (`ROLLER`) yeniden tanımlar. Rol değişkenlerini yalnız
   içerik sütunu bileşenleri kullanır; üst kabuk (servis şeridi, kategori
   bandı, menü, künye) `main`in DIŞINDA durduğu için temadan etkilenemez —
   "kabuk değişmez" kuralını CSS'in kendisi garanti eder.
3. **Düzen.** Renk yetmediğinde sayfa `parca/bolum/<anahtar>.html`
   parçasını kullanır. Parça bölüm sayfasının **yuvalarına** girer:
   `bas` (kırıntının altı; varsayılan servis panelinin yerine) ve `alt`
   (haber kutusunun altı). Hangi yuvayı kullandığı `yuvalar` alanında.

Kayıt, CSS ve plandaki liste birbirine eşit tutulur
(`tests_temalar.py`): CSS'te kayıtta olmayan bir `data-bolum` değeri
geçerse ya da bir tema rol değişkenlerinden birini eksik tanımlarsa test
düşer.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from django.db.models import Q


@dataclass(frozen=True)
class Tema:
    anahtar: str                 # `data-bolum` değeri; CSS'teki ile aynı
    ad: str
    karar: str                   # kullanıcı kararının izi
    kapsam: str                  # hangi sayfalar
    yuvalar: tuple = field(default_factory=tuple)
    # Temanın açılması bir bağlam anahtarına bağlıysa adı. Bursaspor:
    # fikstür gelmediyse kabuk da yeşile dönmez (12 Eylül 2026, §68 —
    # "yarım yeşil sayfa yok").
    kosul: str = ""

    @property
    def duzen(self) -> str:
        return f"parca/bolum/{self.anahtar}.html" if self.yuvalar else ""


TEMALAR: dict[str, Tema] = {t.anahtar: t for t in (
    Tema("bursaspor", "Bursaspor", "12 Eylül 2026 — \"bursaspor sayfasını da yeşil "
         "beyaz renklerine büründür\" (§68)", "/bursaspor", ("alt",), kosul="bursaspor"),
    Tema("ekonomi", "Ekonomi", "19 Ekim 2026 — seçili sayfalar: köşe yazıları, "
         "ekonomi, teknoloji", "/ekonomi, /piyasa/<enstrüman> (20 Ekim 2026)", ("bas",)),
    Tema("teknoloji", "Teknoloji", "19 Ekim 2026 — seçili sayfalar: köşe yazıları, "
         "ekonomi, teknoloji", "/teknoloji", ("bas",)),
    Tema("kose", "Köşe yazıları", "19 Ekim 2026 — seçili sayfalar: köşe yazıları, "
         "ekonomi, teknoloji",
         "/kose-yazilari, /yazarlar, /yazarlar/<yazar>, /yazarlar/<yazar>/<yazı>"),
)}

# Bölüm sayfası → tema. Anahtar kategorinin **tür satırı** slug'ıdır
# (`views.kategori` ile aynı sözleşme), kategori adından türetilmiş olan değil.
KATEGORI_TEMALARI = {"bursaspor": "bursaspor", "ekonomi": "ekonomi",
                     "teknoloji": "teknoloji"}

# Rol değişkenleri. `site.css` `:root` içinde varsayılanları (gazetenin
# kırmızı-laciverti) tanımlıdır; her tema bloğu BU LİSTENİN TAMAMINI yeniden
# tanımlar — eksik rol, temanın yarısının varsayılan renkte kalması demektir.
ROLLER = (
    "--tema-bant", "--tema-bant-vurgu", "--tema-bant-yazi",
    "--tema-bant-ikincil", "--tema-bant-vurgu-ikincil",
    "--tema-fitil", "--tema-fitil-ak",
    "--tema-koyu", "--tema-dolgu", "--tema-vurgu", "--tema-vurgu-koyu",
    "--tema-isaret", "--tema-murekkep", "--tema-sutun-bas",
    "--tema-cizgi", "--tema-yuzey-cizgi", "--tema-hafif-cizgi",
    "--tema-kagit", "--tema-zemin", "--tema-ak",
    "--tema-odak", "--tema-odak-koyu",
    "--tema-etiket-bursa", "--tema-etiket-ekonomi",
    "--tema-baslik-aile", "--tema-kirinti-agirlik",
)

# Kontrast sözleşmesi: (ön, arka, eşik). Testler her tema için bu çiftleri
# `:root`taki hex değerlerinden hesaplar. Metin 4,5 (AA), odak halkası ve
# anlam taşıyan grafik 3 (WCAG 1.4.11). `--gri` tema rolü değil ama tema
# yüzeylerinin üstünde basılıyor; o yüzden listede.
KONTRAST = (
    ("--tema-bant-yazi", "--tema-bant", 4.5),
    ("--tema-bant-yazi", "--tema-bant-vurgu", 4.5),
    ("--tema-bant-ikincil", "--tema-bant", 4.5),
    ("--tema-bant-vurgu-ikincil", "--tema-bant-vurgu", 4.5),
    ("--tema-bant-yazi", "--tema-dolgu", 4.5),
    ("--tema-koyu", "--tema-kagit", 4.5),
    ("--tema-koyu", "--tema-ak", 4.5),
    ("--tema-vurgu", "--tema-kagit", 4.5),
    ("--tema-vurgu-koyu", "--tema-kagit", 4.5),
    ("--tema-vurgu-koyu", "--tema-ak", 4.5),
    ("--tema-murekkep", "--tema-kagit", 4.5),
    ("--tema-etiket-bursa", "--tema-kagit", 4.5),
    ("--tema-etiket-ekonomi", "--tema-kagit", 4.5),
    ("--tema-sutun-bas", "--tema-kagit", 4.5),
    ("--gri", "--tema-kagit", 4.5),
    ("--gri", "--tema-ak", 4.5),
    ("--gri", "--tema-zemin", 4.5),
    ("--murekkep", "--tema-kagit", 4.5),
    ("--tema-isaret", "--tema-kagit", 3),
    ("--tema-odak", "--tema-kagit", 3),
    ("--tema-odak", "--tema-zemin", 3),
    ("--tema-odak", "--tema-ak", 3),
    ("--tema-odak-koyu", "--tema-bant", 3),
    ("--tema-odak-koyu", "--tema-bant-vurgu", 3),
)


def kategori_temasi(slug: str, baglam: dict | None = None) -> Tema | None:
    """Bölüm sayfasının teması; kayıtta yoksa ya da koşulu tutmazsa None."""
    tema = TEMALAR.get(KATEGORI_TEMALARI.get(slug, ""))
    if tema and tema.kosul and not (baglam or {}).get(tema.kosul):
        return None
    return tema


def kose_temasi() -> Tema:
    return TEMALAR["kose"]


def piyasa_temasi() -> Tema:
    """Enstrüman sayfaları (`/piyasa/dolar` …) ekonomi bölümünün parçası;
    aynı renk takımını alır. Düzen parçası (`bas` yuvası) orada basılmaz —
    sayfanın kendi şablonu var (`piyasa.html`)."""
    return TEMALAR["ekonomi"]


# ---------------------------------------------------------------------------
# DÜZEN VERİSİ — temaların `bas` yuvasında basılan "önce Bursa" listeleri.
#
# Ürünün ilk ilkesi "önce Bursa" (EKIP.md): okur ekonomi ve teknoloji
# bölümünü açtığında önce kentinin sanayisini, yazılım şirketini,
# üniversitesini görmek ister. Arşivde ölçüldü (19 Ekim 2026): ekonomi
# kategorisinin son 400 haberinin yalnız 4'ü Bursa'yı anıyor, teknoloji
# kategorisininkilerin HİÇBİRİ — Bursa'nın ekonomi ve teknoloji haberi
# çoğunlukla BURSA kategorisine giriyor. Liste bu yüzden kategoriden değil
# BAŞLIKTAN seçer ve kuralını okura tek cümleyle söyler (şablonda).
#
# Seçim yalnız gerçek başlıklar üzerinde bir süzgeçtir; yeni metin yazılmaz,
# özet üretilmez. Liste boşsa blok hiç çizilmez.
# ---------------------------------------------------------------------------

BURSA_LISTE = 5
# Bir haberin "Bursa'nın" sayılması: başlıkta Bursa ya da BTSO geçiyor veya
# haber bir ilçeye bağlı. "Bursa" ASCII olduğu için SQLite LIKE de
# büyük/küçük harfe duyarsız eşler; Türkçe harfli ilçe adları bu yüzden
# başlıkta aranmaz, ilçe alanından gelir.
_BURSA = Q(baslik__icontains="bursa") | Q(baslik__icontains="btso") | Q(ilce__isnull=False)

# Teknoloji listesinin konu süzgeci. Düz "dijital" bilerek yok: ölçümde
# "dijital pazarlamacıydı, şimdi süt sağıyor" gibi insan hikâyelerini
# yakalıyordu.
_TEKNOLOJI = (Q(baslik__icontains="teknoloji") | Q(baslik__icontains="yapay zek")
              | Q(baslik__icontains="teknofest") | Q(baslik__icontains="yazılım")
              | Q(baslik__icontains="robot") | Q(baslik__icontains="bilişim")
              | Q(baslik__icontains="dijital dönüşüm") | Q(baslik__icontains="siber")
              | Q(baslik__icontains="uzay"))

# Bellek: liste dakikada bir değişmez ve sorgu 1 milyon satırlık tabloda
# tarih sırasıyla taranıyor (ölçüldü: ekonomi 6 ms, teknoloji 44 ms soğuk).
# Süreç içi 10 dakikalık bellek, `canli.oku`daki kısa bellekle aynı düzen.
_BELLEK: dict[str, tuple[float, list]] = {}
BELLEK_SANIYE = 600


def _bellekten(anahtar, uret):
    simdi = time.time()
    kayit = _BELLEK.get(anahtar)
    if kayit and simdi - kayit[0] < BELLEK_SANIYE:
        return kayit[1]
    deger = uret()
    _BELLEK[anahtar] = (simdi, deger)
    return deger


def bursa_listesi(tema: str, kategori, haric=()) -> list:
    """Temanın "önce Bursa" listesi: en yeni `BURSA_LISTE` haber.

    ekonomi   — ekonomi kategorisinden, Bursa'yı anan
    teknoloji — bütün kategorilerden, Bursa'yı ve bir teknoloji konusunu anan
    `haric`: sayfada zaten basılan haberler (aynı haber iki kez görünmesin).
    """
    from .models import Haber

    def uret():
        sorgu = Haber.yayindakiler().select_related("kategori", "ilce").prefetch_related(
            "kategori__turler")
        if tema == "ekonomi":
            sorgu = sorgu.filter(kategori=kategori).filter(_BURSA)
        elif tema == "teknoloji":
            sorgu = sorgu.filter(_BURSA).filter(_TEKNOLOJI)
        else:
            return []
        # Fazladan alınıyor: sayfada basılanlar sonradan ayıklanıyor.
        return list(sorgu[:BURSA_LISTE + 20])

    haric = set(haric)
    return [h for h in _bellekten(f"{tema}:{getattr(kategori, 'pk', '')}", uret)
            if h.pk not in haric][:BURSA_LISTE]


def kategori_baglami(slug: str, kategori, sayfa, baglam: dict) -> dict:
    """Bölüm sayfasına temanın getirdiği bağlam: `tema` + düzen verisi."""
    tema = kategori_temasi(slug, baglam)
    ek = {"tema": tema}
    if tema and tema.anahtar in ("ekonomi", "teknoloji") and getattr(sayfa, "number", 1) == 1:
        ek["bursa_listesi"] = bursa_listesi(
            tema.anahtar, kategori, haric=[h.pk for h in sayfa])
    return ek
