# -*- coding: utf-8 -*-
"""Konu takibi motoru — arşivdeki haberleri başlık ve tarihten zincirler.

Veritabanı görmez, model tanımaz, dış servis çağırmaz. Girdi
`(kimlik, başlık, tarih)` üçlüleri, çıktı `Konu` nesneleridir. Böyle
olması bilinçli: 1.038.474 başlık üzerinde çalışacak; her satırda ORM
açmak saatler sürer, ayrıca aynı motor testte üç satırla da çalışmalı.

## Ne yapar

1. Her başlığı köklerine ayırır (Türkçe küçültme, durak kelime, basit
   son ek düşürme — `arac/kural_motoru.kokle` ile aynı yaklaşım). Yan yana
   iki büyük harfli kelime ayrıca **ikili** kök olur ("ece_gürel"); ad
   iki kelimeyken tek kelimeden çok daha ayırt edicidir.
2. Her kökün kaç başlıkta geçtiğini (belge sıklığı) ve cümle ortasında
   kaç kez büyük harfle yazıldığını sayar. Cümle ortasında hep büyük
   yazılan kök bir **varlıktır** — kişi, kurum, yer. 5 Eylül 2026 ölçümü
   (2024 sonrası başlıklar): bozbey 799/799, gürel 27/27, chp 627/627;
   yakalandı 1/4074, yaralı 13/5779, operasyon 1/941. Ayrım nettir.
3. Başlıkları tarih sırasında dolaşır. Yeni başlık, son `PENCERE_GUN`
   içindeki ve en az bir varlık kökü paylaştığı başlıklarla puanlanır;
   puan paylaşılan köklerin nadirlik ağırlığı toplamıdır. Eşiği geçen en
   iyi eşleşmenin zincirine katılır; yoksa yeni zincir açar.
4. Zincir iki üyeye ulaşınca **çekirdeği** oluşur (üyelerin yarısında,
   en az ikisinde geçen kökler) ve yeni üye çekirdekten en az bir kök
   paylaşmak zorundadır. Bu, ortak kelimelerle zincirin konu değiştirip
   şişmesini keser. Eşik 4 üyeydi; 5 Eylül 2026'da kullanıcı kararıyla
   2'ye indi — sayfada en çok 5 satır gösteriliyor, dosyanın kimliği
   ilk iki haberin ortak adı olsun.

## Neyi konu SAYMAZ — kullanıcının 5 Eylül 2026 kararı

"Önü arkası takip edilmesi gereken" konular hedef; TÜİK'in aylık
enflasyon açıklaması, hava durumu, döviz ve altın fiyatı, nöbetçi eczane,
maç öncesi/sonrası kalıp haberler **değil**. Bunlar üç yerde ayıklanır:

- `RUTIN_KALIPLARI`: başlığa bakarak tanınan periyodik türler. Rutin
  başlık zincire hiç girmez.
- Zincirleme yalnız varlık kökü üzerinden olur. "Yaralı", "kaza",
  "ele geçirildi" gibi olay-türü kelimeler zincir kuramaz; 2025
  denemesinde bu kelimeler 400 üyelik "konular" üretmişti.
- Yer adı tek başına zincir kuramaz: "Şanlıurfa'da yangın" ile
  "Şanlıurfa'da operasyon" aynı dosya değildir. Yer köküyle birlikte
  yer olmayan bir ortak kök gerekir.
- `konu_mu()`: zincir bittikten sonra ölçülen yapı. Üç ayrı gün şart
  (aynı günün beş haberi tek olaydır, dosya değildir); zincirin
  yarısından fazlasında geçen ve arşivde nadir olan bir çekirdek kök
  şart; en fazla `EN_UZUN_SURE` gün (ötesi dosya değil, sürekli bir alan).

Motor **bağlamaz**, öneri üretir. `konu_tara` komutu bunları güven
puanıyla kaydeder; sitede yalnız onaylı konu görünür (CLAUDE.md:
"Konu takibi onaysız bağlamaz").
"""

from __future__ import annotations

import math
import re
from collections import Counter, defaultdict, deque
from dataclasses import dataclass, field
from datetime import date

# ---------------------------------------------------------------- ayarlar

PENCERE_GUN = 45          # aday aranan geriye dönük gün sayısı
ESIK = 1.0                # zincire katılmak için ağırlık toplamı (0-1 ölçek)
AGIRLIK_EN_AZ = 0.3       # bundan hafif kök puanlamaz (arşivin ~%1'inden sık)
CAPA_ORANI = 0.003        # varlık kökü arşivin bu payından sıksa çapa değil
CAPA_EN_AZ_DF = 20        # küçük derlemde (test) oran sıfıra iner; taban
VARLIK_ORANI = 0.6        # cümle ortasında büyük harf payı
CEKIRDEK_ORANI = 0.5      # çekirdek: üyelerin bu oranında geçen kök
CEKIRDEK_EN_AZ_UYE = 2    # çekirdek denetimi bu üye sayısından sonra (5 Eylül:
                          # kullanıcı kararıyla 4 → 2; zincirin kimliği ilk iki
                          # haberin ortak adıdır, üçüncü haber onu taşımalı)
EN_AZ_UYE = 3
EN_AZ_GUN = 3
EN_UZUN_SURE = 3 * 365
EN_COK_UYE = 300          # ötesi dosya değil, konu alanı
KAPSAMA_EN_AZ = 0.6       # çekirdek kökün üyelerdeki payı
YOGUNLUK_GUN = 30         # "patlama" ölçülen pencere
YOGUNLUK_EN_AZ = 0.5      # üyelerin bu payı tek pencereye düşmeli (n ≥ 12)
KUCUK_ZINCIR = 12         # bunun altında ikinci çekirdek YA DA yoğunluk 0.6

# ---------------------------------------------------------------- sözlük
#
# arac/sozluk.json ile aynı listeler; uygulama o dosyayı okumasın diye
# buraya kopyalandı (uygulama arac/ klasörünü tanımaz).

DURAK = set("""
ve ile bir bu şu da de ki mi mı mu mü için gibi kadar sonra önce daha çok en
ama fakat ancak veya ya hem ne her bazı tüm olarak olan oldu olduğu olur
olması var yok göre üzere diye böyle şöyle yine ise değil kendi aynı başka
diğer ilk son yeni büyük küçük iki üç dört beş dedi söyledi yaptı etti bulunan
yapılan edilen verilen alınan eden yapan arasında içinde üzerinde birlikte
nedeniyle sebebiyle yaklaşık ayrıca bugün dün yarın geçen sırasında hakkında
karşı doğru kez defa adet yıl ay gün saat kişi sayıda ilgili konusunda şekilde
durumu yönelik
işte flaş dakika açıklama açıkladı geldi çıktı belli neden nasıl kim kaç hangi
nerede zaman ait olacak oluyor dair bin milyon milyar lira
ocak şubat mart nisan mayıs haziran temmuz ağustos eylül ekim kasım aralık
pazartesi salı çarşamba perşembe cuma cumartesi pazar
""".split())

# Unvanlar ad değildir: "Başkanı Enes" bir kişi değil, "Enes Çelik"tir.
# Kökten düşürülür; "Cumhurbaşkanı Erdoğan" → "Erdoğan".
UNVAN = set("""
başkan başkanı başkanlığı vekil vekili vali valisi kaymakam kaymakamı müdür
müdürü bakan bakanı bakanlığı milletvekili cumhurbaşkanı başbakan genel
avukat doktor profesör prof doç savcı hakim müfettiş rektör komutan sözcü
başhekim teknik direktör direktörü lider lideri eski
""".split())

EKLER = ["larının", "lerinin", "larından", "lerinden", "larına", "lerine",
         "larını", "lerini", "ların", "lerin", "ları", "leri", "ndan", "nden",
         "tan", "ten", "dan", "den", "nın", "nin", "nun", "nün", "ın", "in",
         "un", "ün", "ya", "ye", "da", "de", "ta", "te", "la", "le", "yı",
         "yi", "yu", "yü", "ı", "i", "u", "ü", "a", "e"]

# Yer adları: 81 il, Bursa'nın 17 ilçesi, sık geçen ülke ve şehirler.
# Yer kökü varlıktır ama TEK BAŞINA zincir kuramaz (bkz. modül notu).
_YERLER = """
adana adıyaman afyonkarahisar afyon ağrı amasya ankara antalya artvin aydın
balıkesir bilecik bingöl bitlis bolu burdur bursa çanakkale çankırı çorum
denizli diyarbakır edirne elazığ erzincan erzurum eskişehir gaziantep giresun
gümüşhane hakkari hatay isparta mersin istanbul izmir kars kastamonu kayseri
kırklareli kırşehir kocaeli konya kütahya malatya manisa kahramanmaraş mardin
muğla muş nevşehir niğde ordu rize sakarya samsun siirt sinop sivas tekirdağ
tokat trabzon tunceli şanlıurfa uşak van yozgat zonguldak aksaray bayburt
karaman kırıkkale batman şırnak bartın ardahan iğdır yalova karabük kilis
osmaniye düzce
osmangazi nilüfer yıldırım gemlik mudanya inegöl iznik karacabey keles
kestel gürsu harmancık mustafakemalpaşa orhaneli orhangazi yenişehir
büyükorhan
türkiye abd amerika rusya almanya fransa ingiltere italya ispanya çin japonya
iran irak suriye israil filistin gazze ukrayna yunanistan azerbaycan mısır
suudi arabistan katar hollanda belçika avusturya kanada hindistan pakistan
afganistan libya lübnan ürdün avrupa asya afrika ortadoğu balkanlar
londra paris berlin moskova washington newyork tahran bağdat şam kudüs
kıbrıs kktc anadolu marmara ege akdeniz karadeniz
siverek gebze esenyurt
""".split()

# Zincire yalnız üye sayısıyla değil, "gelişme" diliyle de bakılır. Bu
# kelimelerden biri geçen zincir bir sürecin ilerlediğini gösterir;
# konu puanına katkı verir, şart değildir.
GELISME = tuple("""
tutukla gözaltı soruştur dava duruş mahkeme karar tahliye iddianame ifade
istifa görevden operasyon protesto grev ihale proje itiraz tepki iddia
kayıp bulun cenaze otopsi rapor komisyon toplantı imza uzlaş
anlaş transfer imzala ayrıl görüş yasa teklif meclis onay ret yıkım inşaat
temel açılış
""".split())

# ---------------------------------------------------------------- rutin
#
# Periyodik, "takip edilmesi gerekmeyen" haber türleri. Her kalıp kullanıcı
# örnekleriyle (TÜİK enflasyonu) ve arşivin kendi başlıklarıyla seçildi.
RUTIN_KALIPLARI = [re.compile(k, re.IGNORECASE) for k in [
    r"hava durumu", r"meteoroloji", r"sıcaklık", r"yağış",
    r"namaz vakit", r"iftar (saat|vakt)", r"sahur (saat|vakt)", r"imsak",
    r"nöbetçi eczane",
    r"\b(dolar|euro|sterlin|altın|gram altın|çeyrek altın|döviz)\b.*"
    r"(fiyat|kur|ne kadar|kaç (tl|lira)|güncel|bugün|son durum)",
    r"(fiyat|kur|ne kadar|kaç (tl|lira)|güncel).*"
    r"\b(dolar|euro|sterlin|altın|döviz)\b",
    r"(benzin|motorin|mazot|lpg|akaryakıt).*(fiyat|zam|indirim|litre)",
    r"sigara fiyat", r"güncel .*fiyatlar", r"fiyat listesi",
    r"\b(borsa|bist ?100)\b.*(güne|haftaya|kapan|açıl|yükseliş|düşüş)",
    r"\btüik\b", r"enflasyon.*(açıklandı|belli oldu|rakam|oran|yüzde)",
    r"(sanayi üretimi|işsizlik oranı|cari (açık|fazla)|dış ticaret)",
    r"faiz kararı", r"\bppk\b",
    r"burç", r"günlük burç", r"astroloji",
    r"\(\d{1,2} \w+ \d{4}", r"\d{1,2} \w+ \d{4} .*(fiyat|hava|vakit|eczane)",
    r"canlı (izle|yayın|anlatım)", r"hangi kanalda", r"saat kaçta",
    r"maç(ı|ın)? (özeti|sonucu|kadrosu|hakemi|11'i|ilk 11)",
    r"muhtemel 11", r"ilk 11", r"puan durumu", r"maç sonucu",
    r"kaç kaç", r"\d+-\d+ ?(mağlup|galip|yendi|kazandı|berabere)",
    r"bu akşam .*(dizi|film|bölüm)", r"reyting", r"yeni bölüm fragman",
    r"günün (menü|sözü|fotoğraf|karikatür)",
    r"bugün ne (var|oldu)", r"trafik yoğunluk",
    r"piyasalar(da|ı)? (bugün|güne|hafta)",
    r"asgari ücret .*(ne kadar|kaç|zam)",
    r"emekli (maaş|zam).*(ne kadar|kaç|hesap)",
    r"kira artış oranı", r"vergi dilim", r"harç .*ne kadar",
    r"can kaybı .*(yükseldi|çıktı|arttı)",   # günlük sayaç, gelişme değil
    r"etkisiz h[aâ]le getirildi",             # haftalık bilanço
    r"meclisi? (toplan|gündem)", r"meclis toplantısı",   # aylık meclis
    r"(ile|’la|’le|'la|'le) (telefonda |telefonla )?görüştü\W*$",  # protokol görüşmesi
    r"telefonda görüştü", r"emsal karar",                # dizi biçimli köşe
    r"#\d+", r"\| [A-ZÇĞİÖŞÜ ]{4,}$",                # video dizisi numarası
    r"(hafta|ay|yıl)(lık|ın) (bilanço|özet)",
    r"kolonya|çay demleme|tarif",  # yaşam köşesi
]]

_KUCUK_ESLEME = str.maketrans("IİÇĞÖŞÜ", "ıiçğöşü")
_HARF = "\\wçğıöşüÇĞİÖŞÜ"
_KELIME = re.compile(rf"[{_HARF}]+")
_KESME = re.compile(rf"['’][{_HARF}]*")
_CUMLE_SINIRI = re.compile(r"[!?:.\"“”(\-|;]\s*$")


def kucuk(metin: str) -> str:
    return metin.translate(_KUCUK_ESLEME).lower()


def kokle(kelime: str, tur: int = 2) -> str:
    """Basit son ek düşürme; dilbilimsel kök bulucu değil. İki tarafa da aynı
    işlem uygulandığı için eşleştirmeyi ayakta tutar."""
    k = kucuk(kelime)
    for _ in range(tur):
        for ek in EKLER:
            if k.endswith(ek) and len(k) - len(ek) >= 3:
                k = k[: -len(ek)]
                break
        else:
            break
    return k


YERLER = frozenset(kokle(y) for y in _YERLER)


def rutin_mu(baslik: str) -> bool:
    b = kucuk(baslik)
    return any(k.search(b) for k in RUTIN_KALIPLARI)


@dataclass(frozen=True)
class Parca:
    kok: str
    yuzey: str
    buyuk: bool      # büyük harfle mi yazılmış
    orta: bool       # cümle ortasında mı (büyük harf kanıt sayılır)


def parcala(baslik: str) -> list[Parca]:
    """Başlığın kökleri; sırası korunur, tekrar yok."""
    temiz = _KESME.sub("", baslik)
    bulunan: list[Parca] = []
    gorulen: set[str] = set()
    konum = 0
    for esle in _KELIME.finditer(temiz):
        kelime = esle.group()
        ara = temiz[konum:esle.start()]
        sinir = konum == 0 or _CUMLE_SINIRI.search(ara) is not None
        konum = esle.end()
        if len(kelime) < 3 or kelime.isdigit():
            continue
        if kucuk(kelime) in DURAK or kucuk(kelime) in UNVAN:
            continue
        kok = kokle(kelime)
        if len(kok) < 3 or kok in DURAK or kok in gorulen:
            continue
        gorulen.add(kok)
        bulunan.append(Parca(kok, kelime, kelime[0].isupper(), not sinir))
    return bulunan


def ikililer(parcalar: list[Parca]) -> list[tuple[str, str]]:
    """Yan yana iki büyük harfli kelime: (kök, yüzey). "Ece Gürel" gibi."""
    cikti = []
    for a, b in zip(parcalar, parcalar[1:]):
        if a.buyuk and b.buyuk and b.orta:
            cikti.append((f"{a.kok}_{b.kok}", f"{a.yuzey} {b.yuzey}"))
    return cikti


# ---------------------------------------------------------------- veri

@dataclass
class Haber:
    kimlik: int
    baslik: str
    tarih: date
    kokler: tuple[str, ...]
    konu: "Zincir | None" = None


@dataclass
class Zincir:
    uyeler: list[Haber] = field(default_factory=list)
    sayac: Counter = field(default_factory=Counter)

    def ekle(self, h: Haber) -> None:
        self.uyeler.append(h)
        self.sayac.update(h.kokler)
        h.konu = self

    def cekirdek(self) -> set[str]:
        """Üyelerin en az yarısında geçen kökler. Taban 2: iki üyeli zincirde
        "yarısı" tek üye demek olurdu ve her kök çekirdek sayılırdı."""
        if len(self.uyeler) < CEKIRDEK_EN_AZ_UYE:
            return set()
        esik = max(2, len(self.uyeler) * CEKIRDEK_ORANI)
        return {k for k, n in self.sayac.items() if n >= esik}


@dataclass
class Konu:
    ad: str
    anahtarlar: list[str]
    uyeler: list[Haber]
    guven: int
    gerekce: str

    @property
    def baslangic(self) -> date:
        return self.uyeler[0].tarih

    @property
    def bitis(self) -> date:
        return self.uyeler[-1].tarih


# ---------------------------------------------------------------- motor

class Motor:
    """İki geçişli: önce `say()` ile belge sıklığı, sonra `zincirle()`."""

    def __init__(self):
        self.df: Counter = Counter()
        self.orta: Counter = Counter()       # cümle ortasında geçiş
        self.orta_buyuk: Counter = Counter() # ...büyük harfle
        self.toplam = 0
        self.yuzey: dict[str, Counter] = defaultdict(Counter)
        self._varlik: dict[str, bool] = {}
        self._agirlik: dict[str, float] = {}

    # --- 1. geçiş
    def say(self, baslik: str) -> None:
        self.toplam += 1
        parcalar = parcala(baslik)
        self.df.update({p.kok for p in parcalar})
        for p in parcalar:
            if p.orta:
                self.orta[p.kok] += 1
                if p.buyuk:
                    self.orta_buyuk[p.kok] += 1
        for kok, yuzey in ikililer(parcalar):
            self.df[kok] += 1
            self.yuzey[kok][yuzey] += 1

    def hazirla(self) -> None:
        """Sayım bitince türetilen tabloları kurar; zincirle() öncesi şart."""
        self._varlik.clear()
        self._agirlik.clear()

    def agirlik(self, kok: str) -> float:
        """0-1: arşivde nadirlik. df=1 → ~1, arşivin tamamı → 0."""
        a = self._agirlik.get(kok)
        if a is None:
            a = 1.0 - math.log(self.df.get(kok, 0) + 1) / math.log(self.toplam + 1)
            self._agirlik[kok] = a
        return a

    def varlik_mi(self, kok: str) -> bool:
        """Kişi, kurum ya da yer adı mı? Cümle ortasında büyük harf payı."""
        v = self._varlik.get(kok)
        if v is None:
            if "_" in kok:
                v = True
            else:
                orta = self.orta.get(kok, 0)
                v = orta > 0 and self.orta_buyuk.get(kok, 0) / orta >= VARLIK_ORANI
            self._varlik[kok] = v
        return v

    def capa_mi(self, kok: str) -> bool:
        """Zincir kurabilen kök: varlık VE arşivde nadir."""
        return (self.df.get(kok, 0) <= max(CAPA_EN_AZ_DF, self.toplam * CAPA_ORANI)
                and self.varlik_mi(kok))

    def yer_mi(self, kok: str) -> bool:
        if "_" in kok:
            a, b = kok.split("_", 1)
            return a in YERLER and b in YERLER
        return kok in YERLER

    # --- 2. geçiş
    def _kokler(self, baslik: str) -> tuple[str, ...]:
        parcalar = parcala(baslik)
        kokler = [p.kok for p in parcalar]
        for kok, yuzey in ikililer(parcalar):
            kokler.append(kok)
        # Tek kelimelik özel adların gösterim biçimi
        for p in parcalar:
            if p.buyuk and p.orta and self.capa_mi(p.kok):
                self.yuzey[p.kok][p.yuzey] += 1
        return tuple(kokler)

    def zincirle(self, kayitlar) -> list[Zincir]:
        """`kayitlar`: tarih sırasında `(kimlik, baslik, tarih)` üçlüleri.
        Sırasız verilirse pencere yanlış çalışır; çağıran sıralar."""
        self.hazirla()
        son_tarih: date | None = None

        def haberler():
            nonlocal son_tarih
            for kimlik, baslik, tarih in kayitlar:
                if son_tarih is not None and tarih < son_tarih:
                    raise ValueError("kayıtlar tarih sırasında değil")
                son_tarih = tarih
                if rutin_mu(baslik):
                    continue
                kokler = self._kokler(baslik)
                if len(kokler) < 2:
                    continue
                yield Haber(kimlik, baslik, tarih, kokler)

        return self._zincirle(haberler())

    def _zincirle(self, haberler, siki: bool = False) -> list[Zincir]:
        pencere: dict[str, deque[Haber]] = defaultdict(deque)
        zincirler: list[Zincir] = []
        for h in haberler:
            en_iyi = self._en_iyi_aday(h, pencere, siki)
            if en_iyi is not None:
                en_iyi.konu.ekle(h)
            else:
                z = Zincir()
                z.ekle(h)
                zincirler.append(z)
            for kok in h.kokler:
                if self.capa_mi(kok):
                    kuyruk = pencere[kok]
                    kuyruk.append(h)
                    while kuyruk and (h.tarih - kuyruk[0].tarih).days > PENCERE_GUN:
                        kuyruk.popleft()
        return zincirler

    def bol(self, z: Zincir) -> list[Zincir]:
        """Kişi kapsaması zincirini olaylara böler.

        "Bozbey" 2026'da Ocak-Ağustos 180 haber: saldırı girişimi (Ocak),
        rüşvet operasyonu ve tutuklama (Nisan), günlük belediye haberleri.
        Bütünü dosya değildir ama içinde dosyalar vardır. Üyeler yalnız
        ad dışı ortak kökle (`siki`) yeniden zincirlenir.
        """
        uyeler = sorted(z.uyeler, key=lambda h: (h.tarih, h.kimlik))
        kopyalar = (Haber(h.kimlik, h.baslik, h.tarih, h.kokler) for h in uyeler)
        return self._zincirle(kopyalar, siki=True)

    def birlestir(self, zincirler: list[Zincir]) -> list[Zincir]:
        """Aynı ikili adı çekirdek edinmiş, zamanca bitişik zincirleri
        birleştirir. "Ece Gürel" 2025'te iki zincire bölünmüştü: ilk
        haber başka bir "Ece"nin zincirine, kalanlar yenisine gitmişti."""
        sahip: dict[str, Zincir] = {}
        cikti: list[Zincir] = []
        for z in zincirler:
            if len(z.uyeler) < EN_AZ_UYE:
                cikti.append(z)
                continue
            esik = len(z.uyeler) * KAPSAMA_EN_AZ
            adlar = [k for k, n in z.sayac.items()
                     if "_" in k and n >= esik and self.capa_mi(k)
                     and not self.yer_mi(k)]
            hedef = None
            for ad in adlar:
                onceki = sahip.get(ad)
                if onceki is not None and onceki is not z and \
                        (z.uyeler[0].tarih - onceki.uyeler[-1].tarih).days <= PENCERE_GUN:
                    hedef = onceki
                    break
            if hedef is None:
                cikti.append(z)
                hedef = z
            else:
                for h in z.uyeler:
                    hedef.ekle(h)
                hedef.uyeler.sort(key=lambda h: (h.tarih, h.kimlik))
            for ad in adlar:
                sahip[ad] = hedef
        return cikti

    def puanla(self, a: tuple[str, ...], b: tuple[str, ...],
               siki: bool = False) -> float:
        """İki başlığın ortak köklerinden puan. Şartlar sağlanmazsa 0.

        - Ağırlığı `AGIRLIK_EN_AZ` altındaki kök sayılmaz.
        - En az bir ortak ÇAPA (nadir varlık) şart.
        - Ortak çapalar yalnız yer adıysa, yer olmayan ikinci bir ortak kök
          şart: "Şanlıurfa" iki ayrı olayı bağlamaz.
        - Tek ortak kök ancak ikili ad ise yeter ("Ece Gürel").
        - `siki`: ad dışında bir ortak kök de şart. Kişi kapsaması
          zincirini olaylara bölerken kullanılır ("Bozbey · rüşvet").
        """
        ortak = [k for k in set(a) & set(b) if self.agirlik(k) >= AGIRLIK_EN_AZ]
        if not ortak:
            return 0.0
        if siki and not any(not self.varlik_mi(k) and self.agirlik(k) >= 0.4
                            for k in ortak):
            return 0.0
        capalar = [k for k in ortak if self.capa_mi(k)]
        if not capalar:
            return 0.0
        if all(self.yer_mi(k) for k in capalar) and \
                not any(not self.yer_mi(k) and self.agirlik(k) >= 0.5
                        for k in ortak):
            return 0.0
        if len(ortak) < 2 and not any("_" in k for k in capalar):
            return 0.0
        return sum(self.agirlik(k) for k in ortak)

    def _en_iyi_aday(self, h: Haber, pencere, siki: bool = False) -> Haber | None:
        kokler_kume = set(h.kokler)
        gorulen: set[int] = set()
        en_iyi, en_iyi_puan = None, 0.0
        for kok in h.kokler:
            if not self.capa_mi(kok):
                continue
            for aday in reversed(pencere.get(kok, ())):
                if (h.tarih - aday.tarih).days > PENCERE_GUN:
                    break
                if id(aday) in gorulen:
                    continue
                gorulen.add(id(aday))
                puan = self.puanla(h.kokler, aday.kokler, siki)
                if puan < ESIK or puan <= en_iyi_puan:
                    continue
                zincir = aday.konu
                if len(zincir.uyeler) >= EN_COK_UYE:
                    continue
                cekirdek = zincir.cekirdek()
                if cekirdek and not (cekirdek & kokler_kume):
                    continue
                en_iyi, en_iyi_puan = aday, puan
        return en_iyi

    # --- 3. ayıklama
    def konu_mu(self, z: Zincir, bolunmus: bool = False) -> Konu | None:
        uyeler = sorted(z.uyeler, key=lambda h: (h.tarih, h.kimlik))
        n = len(uyeler)
        if n < EN_AZ_UYE or n > EN_COK_UYE:
            return None
        gunler = {h.tarih for h in uyeler}
        if len(gunler) < EN_AZ_GUN:
            return None
        # Aynı başlığın tekrarı (reklam metni, yeniden yayın) gelişme değil.
        if len({kucuk(h.baslik).strip() for h in uyeler}) < EN_AZ_UYE:
            return None
        sure = (uyeler[-1].tarih - uyeler[0].tarih).days
        if sure > EN_UZUN_SURE:
            return None

        # Çekirdek: üyelerin çoğunda geçen, arşivde nadir kökler. En az
        # biri yer olmayan bir çapa ya da yer + ayırt edici ikinci kök.
        cekirdek = sorted(
            ((sayi / n, k) for k, sayi in z.sayac.items()
             if sayi / n >= KAPSAMA_EN_AZ and self.agirlik(k) >= AGIRLIK_EN_AZ),
            reverse=True)
        capalar = [(o, k) for o, k in cekirdek if self.capa_mi(k)]
        if not capalar:
            return None
        if all(self.yer_mi(k) for _, k in capalar) and \
                not any(not self.yer_mi(k) and self.agirlik(k) >= 0.5
                        for _, k in cekirdek):
            return None
        # Ad için: ikili ad > yer olmayan varlık > kapsama
        capalar.sort(key=lambda ok: ("_" in ok[1], not self.yer_mi(ok[1]),
                                     ok[0]), reverse=True)
        en_kapsayan, ana_kok = capalar[0]

        # Dosya mı, sürekli kapsama mı? Bir dosyanın patlama anı vardır:
        # üyelerin çoğu bir aya düşer ("Ece Gürel" 20 haberin 19'u Mart
        # 2025). Bir kişinin yıl boyu haberi ise düz yayılır ("Arda Güler"
        # 2025'te 191 haber, her ay benzer) — o kapsama, dosya değil.
        yogunluk = self._yogunluk(uyeler)
        ikinci_cekirdek = any(
            not self.varlik_mi(k) and k not in ana_kok.split("_")
            for _, k in cekirdek if self.agirlik(k) >= 0.4)
        if bolunmus:
            # Olay kelimesiyle bölünmüş alt zincir: ikinci çekirdek zaten
            # kuruluşundan geliyor; yoğunluk şartı gevşer.
            if not ikinci_cekirdek and yogunluk < 0.6:
                return None
        elif n >= KUCUK_ZINCIR:
            if yogunluk < YOGUNLUK_EN_AZ:
                return None
        elif not ikinci_cekirdek and yogunluk < 0.6:
            return None

        gelisme = sum(1 for h in uyeler if any(
            k.startswith(GELISME) for k in h.kokler))

        guven = self._guven(n, len(gunler), en_kapsayan, ana_kok, gelisme)
        # İkili ad zaten iki kelimeyi kapsıyor; parçalarını ve onunla kelime
        # paylaşan ikinci bir ikiliyi ("Aziz İhsan" + "İhsan Aktaş") ayrıca sayma.
        anahtar_kokleri: list[str] = []
        kapli: set[str] = set()
        for _, k in capalar + [(o, k) for o, k in cekirdek if not self.capa_mi(k)]:
            parcalar = k.split("_")
            if k in anahtar_kokleri or any(p in kapli for p in parcalar):
                continue
            anahtar_kokleri.append(k)
            if "_" in k:
                kapli.update(parcalar)
        anahtarlar = [self._ad(k, uyeler) for k in anahtar_kokleri[:4]]
        ad = anahtarlar[0]
        if len(anahtarlar) > 1 and " " not in ad:
            ad = f"{ad} · {anahtarlar[1]}"
        gerekce = (f"{n} haber, {len(gunler)} ayrı gün, {sure} günlük süre; "
                   f"'{anahtarlar[0]}' üyelerin %{round(en_kapsayan * 100)}'inde, "
                   f"arşivde {self.df[ana_kok]} başlıkta; "
                   f"{gelisme} başlıkta gelişme dili.")
        return Konu(ad=ad, anahtarlar=anahtarlar, uyeler=uyeler,
                    guven=guven, gerekce=gerekce)

    @staticmethod
    def _yogunluk(uyeler) -> float:
        """Üyelerin en yoğun `YOGUNLUK_GUN` günlük pencereye düşen payı."""
        tarihler = [h.tarih for h in uyeler]
        en_cok, bas = 0, 0
        for son in range(len(tarihler)):
            while (tarihler[son] - tarihler[bas]).days > YOGUNLUK_GUN:
                bas += 1
            en_cok = max(en_cok, son - bas + 1)
        return en_cok / len(tarihler)

    def _guven(self, n, gun, kapsama, ana_kok, gelisme) -> int:
        """0-100. Kapsama ve nadirlik ağır basar; üye sayısı doyar."""
        puan = (40 * kapsama + 30 * self.agirlik(ana_kok)
                + 15 * min(1.0, gun / 6) + 15 * min(1.0, gelisme / max(1, n)))
        return int(round(min(100, puan)))

    def _ad(self, kok: str, uyeler=()) -> str:
        """Kökün gösterim biçimi. Çapa köklerin özel ad yüzeyi sayılmıştır;
        ötekiler için üyelerin başlıklarındaki en sık kelime alınır — "davas"
        yerine "davası", "beşiktaş" yerine "Beşiktaş"."""
        yuzeyler = self.yuzey.get(kok)
        if yuzeyler:
            obek, _ = max(yuzeyler.items(), key=lambda ci: (ci[1], len(ci[0])))
            return obek
        sayac: Counter = Counter()
        for h in uyeler:
            for p in parcala(h.baslik):
                if p.kok == kok:
                    sayac[p.yuzey if self.varlik_mi(kok) else kucuk(p.yuzey)] += 1
        if sayac:
            return sayac.most_common(1)[0][0]
        return kok.replace("_", " ")

    def konular(self, zincirler) -> list[Konu]:
        bulunan: list[Konu] = []
        for z in self.birlestir(zincirler):
            k = self.konu_mu(z)
            if k is not None:
                bulunan.append(k)
            elif len(z.uyeler) >= KUCUK_ZINCIR:
                for alt in self.bol(z):
                    k = self.konu_mu(alt, bolunmus=True)
                    if k is not None:
                        bulunan.append(k)
        bulunan.sort(key=lambda k: (k.baslangic, k.uyeler[0].kimlik))
        return bulunan


def tara(kayitlar) -> list[Konu]:
    """Tek çağrıda iki geçiş. `kayitlar` iki kez dolaşılır; liste ver."""
    kayitlar = list(kayitlar)
    kayitlar.sort(key=lambda k: (k[2], k[0]))
    m = Motor()
    for _, baslik, _ in kayitlar:
        m.say(baslik)
    return m.konular(m.zincirle(kayitlar))
