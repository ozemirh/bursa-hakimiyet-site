"""Anasayfanın dizilimi — masanın kararı + "önce Bursa" düşüş kuralı.

19 Ekim 2026, Paket H (DEGERLENDIRME-2026-10 §3 bulgu 5). Bu dosyadan önce
panelin manşet bayrakları (`manset_ana` · `manset_tepe` · `manset_kare`)
sitede SIFIR kez okunuyordu; anasayfa son 50 haberi tarih sırasıyla
dilimliyordu. Masa "bu haber manşet" dediğinde okur bunu görmüyordu.

Anasayfa (`views.anasayfa`) ve panelin manşet ekranı (`panel.mansetler`)
AYNI işlevi çağırır: `kur()`. Panelin "şu an anasayfada ne var" sorusunun
cevabı böylece sitenin kendisiyle aynı hesaptan gelir; ikinci bir kural
yazılmaz.

## Bayrak → yuva (bileşen sözleşmesi URUN-PLANI.md §1, sayılar `views.py`)

    manset_ana   → ana manşet slaytı (15) + altındaki "GÜNÜN MANŞETLERİ" (10)
    manset_tepe  → dörtlü kutucuk (4)  — panel: "Manşet üstü şerit"
    manset_kare  → yan slayt (5)       — panel: "Kare formatlı manşet kutusu"

Eşleme panelin kendi tanımından (`panel-haber-ekle.html`, PANEL-NOTLARI
§14 şeması: "tepe manşet → (ana manşet · kare manşet)"). Tepe manşet
manşetin ÜSTÜNDEKİ şerit, kare manşet YANINDAKİ kutudur; anasayfada bu
iki yer dörtlü kutucuk ile yan slayttır. Eşleme tek sözlükte
(`BAYRAK_YUVASI`); değişirse yalnız burası değişir.

Bir haber birden çok bayrak taşıyorsa en üst yuvaya girer (ana > tepe >
kare) ve sayfada bir kez görünür.

## Sıra

Panelde sıra alanı YOK (§4 alan 18-20 yalnız üç kutu). Bayraklı haberler
**bayrağın verildiği ana** göre, en yeni karar önde dizilir. O an denetim
kaydından okunur (`LogKaydi`, fiil `mansete_alma`: form ve toplu fiil
ikisi de yazıyor); kaydı olmayan bayrakta (göç, kabuk) yayın zamanı
kullanılır. Ayrı bir sıra alanı `icerik_haber`e sütun eklemek demekti
(1 milyon satırda tablo yeniden kurma); karar defterini yeniden icat
etmeden mevcut kayıttan okunuyor.

## Bayrağın ömrü — KARAR

Panel sözleşmesinde bayrağın süresi yok (§4, §14). Bayrak **kalıcıdır**:
silinmez, düşürülmez. Ama öncelik süresi `BH_MANSET_BAYRAK_SAAT`
(varsayılan 48 saat): bayrağın verilmesinden bu kadar zaman geçince haber
yuvayı ayırtmaz, düşüş havuzunda sıradan bir aday gibi yarışır. Gerekçe:
§21 "beş dakika eski manşet kabul edilemez" diyor; unutulmuş bir bayrak
anasayfanın tepesini günlerce kilitlemesin. Panel bu durumu "öncelik
süresi doldu" diye gösterir; editör bayrağı yeniden verirse süre baştan
başlar (yeni denetim satırı).

## Düşüş kuralı — "önce Bursa"

Bayraklı haber yuvayı doldurmuyorsa kalan yuvalar son yayımlananlar
havuzundan (`HAVUZ`) dolar:

1. **Bursa haberi** = kategorisi BURSA / BURSASPOR / BURSA'DA SPOR, ya da
   ilçe alanı dolu, ya da başlığında "Bursa" ya da bir ilçe adı geçen
   haber (`bursali_mi`).
2. Ana manşetin ilk 15 kaydında en az `BH_MANSET_BURSA_ORANI` (varsayılan
   10/15) Bursa haberi olur. Bayraklı Bursa haberleri bu sayıya dâhildir;
   eksik kalan en yeni Bursa haberleriyle tamamlanır, kalan yuvalar
   tarih sırasıyla (Bursa ya da ulusal) dolar.
3. Slaytta Bursa haberleri ulusaldan önce gelir (ikinci kademe kuralı);
   her grup kendi içinde en yeniden eskiye. Bayraklı haberler her zaman
   en önde: masanın kararı kuralın üstündedir. Editör 15 ulusal haberi
   bayraklarsa oran tutmaz — bu bilinçli.
4. Diğer yuvalar (günün manşetleri, yan slayt, dörtlü, haber kutuları)
   bayraklılardan sonra tarih sırasıyla dolar; oran yalnız ilk 15'e
   uygulanır.
5. Nöbetçi eczane servis haberi (günlük otomatik kayıt, §41) manşet,
   yan slayt ve dörtlüye düşüşle GİRMEZ; haber kutularında ve
   akışta kalır. Editör bayraklarsa girer.

Havuzda oranı tutturacak kadar Bursa haberi yoksa (yoğun ulusal gün)
kural elindekiyle yetinir; havuz dışına ek sorgu açılmaz — `kategori IN
(…) ORDER BY yayin_zamani` SQLite'ta geçici sıralama ağacı kuruyor.

## Sorgu bütçesi (ölçüm 19 Ekim 2026, 1.038.477 haber, salt okunur kopya)

    bayrak kimlikleri  3 sorgu × 0,3 ms   kısmi indeks (0006)
    bayraklı kayıtlar  1 sorgu  ~1,4 ms   yalnız bayrak varsa
    bayrak zamanları   1 sorgu            yalnız bayrak varsa
    havuz              1 sorgu  ~4,5 ms   son 80 haber

**Bayrak sorgusu `yayindakiler()` ile BİRLEŞTİRİLMEZ.** Ölçüldü:
`durum=1 AND yayin_zamani<=… AND manset_ana` planlayıcıyı `haber_okur_kismi`
indeksine çekiyor ve kısmi manşet indeksini bırakıyor: 30–41 SANİYE.
Kimlikler önce çıplak bayrak sorgusuyla (0,3 ms) alınır, yayın süzgeci
birincil anahtar üstünden uygulanır.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from fractions import Fraction

from django.conf import settings
from django.utils import timezone

from .arama_metni import anahtar, kelimeler

#: Yuva sayıları — `views.py` sabitleriyle aynı (§1 bileşen sözleşmesi).
MANSET = 15
MANSET_LISTE = 10
IKINCIL = 5
DORTLU = 4
KUTU = 11
EN_COK = 5

#: Düşüş havuzu: son yayımlanan N haber. Eski düzen 50 kayıt çekiyordu
#: (yuvaların toplamı); Bursa oranını tutturmak için havuz genişletildi.
#: Ölçüm (kopya veritabanı): 50 satır 3,9 ms · 100 satır ~6 ms · 150 satır
#: 7,6–12,7 ms. Son 150 haberin ~%33'ü Bursa (BURSA 44, BURSASPOR 2,
#: ilçeli/başlıklı ek) — 80 satırda ~26 aday, 10 için yeter. 100'de kur()
#: 10,5 ms ölçüldü; 80 satır + sınıflama belleğiyle 7,3 ms (eski 50'lik
#: dilimleme 3,1 ms). Bayrak kimlikleri bunun ~0,9 ms'si.
HAVUZ = 80

#: Bayrak alanı → yuva. Öncelik sırası listedeki sıradır.
BAYRAK_YUVASI = (
    ("manset_ana", "manset"),
    ("manset_tepe", "dortlu"),
    ("manset_kare", "ikincil"),
)
#: Bayraklının sığabileceği yer sayısı. Ana manşet bayrağı slayt dolunca
#: "günün manşetleri" listesine taşar.
BAYRAK_KAPASITESI = {"manset": MANSET + MANSET_LISTE, "dortlu": DORTLU,
                     "ikincil": IKINCIL}

YUVA_ADLARI = {"manset": "Ana manşet (slayt)", "manset_liste": "Günün manşetleri",
               "ikincil": "Kare manşet (yan slayt)", "dortlu": "Tepe manşet (dörtlü)",
               "kutular": "Haber kutuları"}

#: Bursa sayılan kategoriler (adla; taksonomi_kur'un adları).
BURSA_KATEGORILERI = ("BURSA", "BURSASPOR", "BURSA'DA SPOR")

#: Başlıkta aranan yer adları (normalize). İlçeler veritabanından gelir;
#: "Yıldırım" BAŞLIKTA aranmaz: yaygın soyadı ve sözcük ("Binali Yıldırım",
#: "yıldırım düştü"). O ilçenin haberi ilçe alanıyla yakalanır.
BASLIKTA_ARANMAZ = {"yildirim"}

#: Nöbetçi eczane servis haberinin slug soneki (`eczane.haber_slug`).
SERVIS_SLUG_SONEKI = "bursa-nobetci-eczaneler"


def servis_haberi_mi(haber) -> bool:
    """Günlük otomatik eczane haberi mi (§41). Bant ve manşet için gürültü."""
    return (haber.slug or "").endswith(SERVIS_SLUG_SONEKI)


# ---------------------------------------------------------------------------
# Ayarlar
# ---------------------------------------------------------------------------

def bursa_orani() -> Fraction:
    """`BH_MANSET_BURSA_ORANI` — "10/15" ya da "0.66". Bozuksa 10/15."""
    ham = str(getattr(settings, "MANSET_BURSA_ORANI", "10/15") or "10/15")
    try:
        oran = Fraction(ham.replace(",", ".").strip())
    except (ValueError, ZeroDivisionError):
        oran = Fraction(10, 15)
    return min(max(oran, Fraction(0)), Fraction(1))


def en_az_bursa(yuva: int = MANSET) -> int:
    """İlk `yuva` manşette olması gereken en az Bursa haberi (yukarı yuvarlanır)."""
    oran = bursa_orani()
    return -(-oran.numerator * yuva // oran.denominator)


def bayrak_omru() -> timedelta:
    return timedelta(hours=int(getattr(settings, "MANSET_BAYRAK_SAAT", 48)))


# ---------------------------------------------------------------------------
# Bursa sınıflaması
# ---------------------------------------------------------------------------

#: Kategori kaydı değişince `sinyaller._kategori_degisti` siler.
BURSA_KATEGORI_ANAHTARI = "bh:bursa-kategorileri:v1"


def _bursa_kategori_kimlikleri() -> frozenset:
    from taksonomi.models import Kategori

    from . import onbellek
    return onbellek.hesapla(
        BURSA_KATEGORI_ANAHTARI,
        lambda: frozenset(Kategori.objects.filter(ad__in=BURSA_KATEGORILERI)
                          .values_list("pk", flat=True)),
        taze=3600, hata=20, yedek=frozenset)


def _yer_adlari() -> tuple:
    from .baglam import _ilceler
    adlar = {"bursa"} | {anahtar(i.ad) for i in _ilceler()}
    return tuple(sorted(a for a in adlar if a and a not in BASLIKTA_ARANMAZ))


@dataclass
class _Siniflayici:
    kategoriler: frozenset
    yerler: tuple

    def __call__(self, haber) -> bool:
        if haber.kategori_id in self.kategoriler or haber.ilce_id:
            return True
        # Kelime BAŞI eşleşmesi: "Bursaspor", "Nilüferli" yakalanır;
        # "Kabursa" gibi iç eşleşme yakalanmaz.
        return any(k.startswith(self.yerler) for k in kelimeler(haber.baslik))


def siniflayici() -> _Siniflayici:
    return _Siniflayici(_bursa_kategori_kimlikleri(), _yer_adlari())


def bursali_mi(haber) -> bool:
    return siniflayici()(haber)


# ---------------------------------------------------------------------------
# Dizilim
# ---------------------------------------------------------------------------

@dataclass
class Kalem:
    """Bir yuvadaki haber ve oraya NEDEN girdiği (panel bunu gösterir)."""
    haber: object
    yuva: str
    sira: int
    neden: str                    # "bayrak" | "dusus"
    bursa: bool
    bayrak_zamani: datetime | None = None


@dataclass
class Disarida:
    """Bayrağı olduğu hâlde yuvasına girmeyen haber."""
    haber: object
    bayrak: str
    neden: str                    # "yayinda_degil" | "suresi_doldu" | "yuva_dolu"
    bayrak_zamani: datetime | None = None


@dataclass
class Dizilim:
    manset: list = field(default_factory=list)
    manset_liste: list = field(default_factory=list)
    ikincil: list = field(default_factory=list)
    dortlu: list = field(default_factory=list)
    kutular: list = field(default_factory=list)
    #: Havuzun kullanılmayan kalanı, tarih sırasıyla ("en çok okunanlar"
    #: sayaç yetersizken buradan dolar).
    kalan: list = field(default_factory=list)
    kalemler: list = field(default_factory=list)
    disarida: list = field(default_factory=list)
    en_az_bursa: int = 0
    oran: str = ""

    @property
    def kullanilan(self) -> list:
        return [k.haber.pk for k in self.kalemler]

    def bursa_sayisi(self) -> int:
        return sum(1 for k in self.kalemler if k.yuva == "manset" and k.bursa)


def _bayrakli_kimlikler() -> dict:
    """Bayrak alanı → kimlikler. Üç ayrı kısmi indeksli sorgu (OR değil,
    `panel.mansetler` notu); `.order_by()` şart, yoksa Meta sıralaması
    planlayıcıyı `haber_siralama`ya çekiyor."""
    from .models import Haber
    return {alan: list(Haber.objects.filter(**{alan: True}).order_by()
                       .values_list("pk", flat=True))
            for alan, _ in BAYRAK_YUVASI}


def _bayrak_zamanlari(kimlikler) -> dict:
    """(kimlik, alan) → bayrağın en son verildiği an, denetim kaydından.

    Form yolu `sonrasi={alan: True, ...}`, toplu fiil `sonrasi={"fiil":
    "mansete_al", "manset_slot": alan}` yazar (`denetim_kaydi`). İkisi de
    okunur. Kayıt yazılamamışsa (günlük düştü) yayın zamanına düşülür.
    """
    from .models import LogKaydi
    zamanlar = {}
    satirlar = (LogKaydi.objects.filter(hedef_tur="haber", hedef_id__in=list(kimlikler),
                                        fiil="mansete_alma")
                .order_by().values_list("hedef_id", "zaman", "sonrasi"))
    for kimlik, zaman, sonrasi in satirlar:
        sonrasi = sonrasi if isinstance(sonrasi, dict) else {}
        alanlar = {a for a, _ in BAYRAK_YUVASI if sonrasi.get(a) is True}
        if sonrasi.get("manset_slot"):
            alanlar.add(sonrasi["manset_slot"])
        for alan in alanlar:
            onceki = zamanlar.get((kimlik, alan))
            if onceki is None or zaman > onceki:
                zamanlar[(kimlik, alan)] = zaman
    return zamanlar


def _liste():
    from .models import Haber
    return Haber.yayindakiler().select_related("kategori", "ilce")


def kur(simdi: datetime | None = None, bayrakli: dict | None = None) -> Dizilim:
    """Anasayfanın bütün haber yuvaları. Anasayfa ve panel AYNI işlevi çağırır.

    `bayrakli`: alan → kimlikler; panel bunları zaten topladıysa verir ve
    aynı üç sorgu ikinci kez açılmaz. Verilmezse burada toplanır.
    """
    simdi = simdi or timezone.now()
    _sinif = siniflayici()
    _bellek = {}

    def bursa(h):
        # Aynı haber sıralama ve seçimde birkaç kez sorulur; başlık
        # normalleştirmesi bir kez yapılsın.
        if h.pk not in _bellek:
            _bellek[h.pk] = _sinif(h)
        return _bellek[h.pk]

    omur = bayrak_omru()
    d = Dizilim(en_az_bursa=en_az_bursa(MANSET),
                oran=str(getattr(settings, "MANSET_BURSA_ORANI", "10/15")))

    # -- 1. bayraklılar ---------------------------------------------------
    kimlikler = bayrakli if bayrakli is not None else _bayrakli_kimlikler()
    tum = {k for liste in kimlikler.values() for k in liste}
    ayrilan = {"manset": [], "dortlu": [], "ikincil": []}
    yerlesen = set()
    if tum:
        kayitlar = {h.pk: h for h in _liste().filter(pk__in=tum)}
        yayinda_olmayan = tum - set(kayitlar)
        if yayinda_olmayan:
            from .models import Haber
            for h in (Haber.objects.select_related("kategori")
                      .filter(pk__in=yayinda_olmayan).order_by()):
                alan = next(a for a, _ in BAYRAK_YUVASI if getattr(h, a))
                d.disarida.append(Disarida(h, alan, "yayinda_degil"))
        zamanlar = _bayrak_zamanlari(set(kayitlar))
        adaylar = {yuva: [] for yuva in ayrilan}
        for alan, yuva in BAYRAK_YUVASI:
            for pk in kimlikler[alan]:
                h = kayitlar.get(pk)
                if h is None or pk in yerlesen:
                    continue
                yerlesen.add(pk)          # en üst bayrağın yuvası kazanır
                zaman = zamanlar.get((pk, alan)) or h.yayin_zamani
                if zaman and simdi - zaman > omur:
                    d.disarida.append(Disarida(h, alan, "suresi_doldu", zaman))
                    continue
                adaylar[yuva].append((zaman, h))
        for yuva, liste in adaylar.items():
            liste.sort(key=lambda z: (z[0], z[1].yayin_zamani, z[1].pk), reverse=True)
            sig = BAYRAK_KAPASITESI[yuva]
            ayrilan[yuva] = liste[:sig]
            for zaman, h in liste[sig:]:
                alan = next(a for a, y in BAYRAK_YUVASI if y == yuva)
                d.disarida.append(Disarida(h, alan, "yuva_dolu", zaman))
    ayrilan_kimlik = {h.pk for liste in ayrilan.values() for _, h in liste}

    # -- 2. düşüş havuzu --------------------------------------------------
    havuz = [h for h in _liste()[:HAVUZ] if h.pk not in ayrilan_kimlik]
    kullanildi = set()

    def yerlestir(yuva, haber, neden, zaman=None):
        kullanildi.add(haber.pk)
        hedef = getattr(d, yuva)
        d.kalemler.append(Kalem(haber, yuva, len(hedef) + 1, neden, bursa(haber), zaman))
        hedef.append(haber)

    def adaylar(servissiz=True):
        return [h for h in havuz if h.pk not in kullanildi
                and not (servissiz and servis_haberi_mi(h))]

    # -- 3. ana manşet: bayraklılar + "önce Bursa" ------------------------
    bayrakli_ana = ayrilan["manset"]
    for zaman, h in bayrakli_ana[:MANSET]:
        yerlestir("manset", h, "bayrak", zaman)
    bos = MANSET - len(d.manset)
    if bos:
        eksik = max(0, d.en_az_bursa - sum(1 for h in d.manset if bursa(h)))
        aday = adaylar()
        secilen = [h for h in aday if bursa(h)][:min(eksik, bos)]
        secilen_kimlik = {h.pk for h in secilen}
        secilen += [h for h in aday if h.pk not in secilen_kimlik][:bos - len(secilen)]
        # İkinci kademe: Bursa önce, ulusal sonra; her grup en yeniden.
        secilen.sort(key=lambda h: (not bursa(h), -(h.yayin_zamani.timestamp()), -h.pk))
        for h in secilen:
            yerlestir("manset", h, "dusus")

    # -- 4. günün manşetleri: taşan ana bayrakları + tarih sırası ---------
    for zaman, h in bayrakli_ana[MANSET:]:
        yerlestir("manset_liste", h, "bayrak", zaman)
    for h in adaylar()[:MANSET_LISTE - len(d.manset_liste)]:
        yerlestir("manset_liste", h, "dusus")

    # -- 5. kare (yan slayt) ve tepe (dörtlü) -----------------------------
    for yuva, adet in (("ikincil", IKINCIL), ("dortlu", DORTLU)):
        for zaman, h in ayrilan[yuva]:
            yerlestir(yuva, h, "bayrak", zaman)
        for h in adaylar()[:adet - len(getattr(d, yuva))]:
            yerlestir(yuva, h, "dusus")

    # -- 6. haber kutuları: kalan, tarih sırası (servis haberi dâhil) -----
    for h in adaylar(servissiz=False)[:KUTU]:
        yerlestir("kutular", h, "dusus")
    d.kalan = adaylar(servissiz=False)
    return d
