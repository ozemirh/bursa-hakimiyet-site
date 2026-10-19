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
# Yapısal periyodiklik (19 Ekim 2026, Paket M): başlık kalıbına girmeyen
# periyodik türü zincirin biçiminden tanır. Üçü birden tutarsa dosya değil
# dizidir: en az 15 haber, haberlerin %80'inden fazlası ayrı günde (her gün
# bir tane), gelişme dili %5'in altında (süreç ilerlemiyor, aynı şey
# tekrarlanıyor). "New York borsası" 300 haber, 0.84 gün/haber, gelişme 0;
# "Ece Gürel" 6 haber — eşiğin altında, hiç bakılmaz. Bir transfer sağası
# ("anlaştı", "imzaladı", "görüşme") gelişme diliyle bu süzgeçten geçer.
PERIYODIK_EN_AZ_UYE = 15
PERIYODIK_GUN_ORANI = 0.8
PERIYODIK_GELISME = 0.05

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
# Başlık `kucuk()` ile küçültülüp aranır; kesme işareti korunur.
#
# 19 Ekim 2026 (Paket M): 5 Eylül taraması bu listenin dar kaldığı türleri
# ONAYLI dosya olarak yayına çıkarmıştı. Her yeni grubun yanında o türün
# sitede onaylı duran tek bir örnek dosyası yazılı (kimlik · ad · haber
# sayısı · örnek başlık); grup o dosya yüzünden var. Ölçüt "gerçekten
# periyodik mi": takvimle, sayaçla ya da kurumun düzenli duyurusuyla gelen
# başlık. Bir kişinin, kulübün ya da ligin adı tek başına kalıp DEĞİLDİR —
# "Süper Lig" ya da "Bursaspor" başlığı bir transfer dosyasının parçası
# olabilir; o ayrımı başlık değil yapı yapar (`Motor._periyodik_mi`).
RUTIN_GRUPLARI: list[tuple[str, str, list[str]]] = [
    ("hava durumu", "5 Eylül listesi + #85528 'Marmara Denizi' 28 haber: "
     "\"Marmara Denizi'nde fırtına uyarısı\"", [
        r"hava durumu", r"meteoroloji", r"sıcaklık", r"yağış",
        r"(fırtına|lodos|kuvvetli rüzgar|sağanak|kar yağışı|zirai don|sis|"
        r"toz taşınımı) (uyarı|alarm|engeli)", r"(sarı|turuncu|kırmızı) kod",
    ]),
    ("namaz ve oruç vakti", "5 Eylül listesi", [
        r"namaz vakit", r"iftar (saat|vakt)", r"sahur (saat|vakt)", r"imsak",
        r"bayram namazı (saat|kaçta|vakt)",
    ]),
    ("nöbetçi eczane", "5 Eylül listesi", [r"nöbetçi eczane"]),
    ("döviz ve altın", "5 Eylül listesi", [
        r"\b(dolar|euro|sterlin|altın|gram altın|çeyrek altın|döviz)\b.*"
        r"(fiyat|kur|ne kadar|kaç (tl|lira)|güncel|bugün|son durum)",
        r"(fiyat|kur|ne kadar|kaç (tl|lira)|güncel).*"
        r"\b(dolar|euro|sterlin|altın|döviz)\b",
        r"ons altın",
    ]),
    ("kripto para durumu",
     "#79737 'Bitcoin Ethereum' 35 haber: \"Bitcoin, Ethereum ve Altcoin'lerde "
     "son durum ne?\"", [
        r"\b(bitcoin|btc|ethereum|altcoin|kripto ?para)\w*['’]?\w*\b.*"
        r"(son durum|fiyat|kaç (dolar|tl)|yükseliş|düşüş|değer (kazan|kaybet))",
    ]),
    ("akaryakıt ve fiyat listesi", "5 Eylül listesi", [
        r"(benzin|motorin|mazot|lpg|akaryakıt).*(fiyat|zam|indirim|litre)",
        r"sigara fiyat", r"güncel .*fiyatlar", r"fiyat listesi",
    ]),
    # 5 Eylül'deki `\b(borsa|bist ?100)\b` kalıbı "borsası"nı tanımıyordu
    # (\b ekin önünde kesilmez); 300 haberlik dosya bu yüzden geçti.
    ("borsa açılış ve kapanışı",
     "#75138 'New York' 300 haber: \"New York borsası yükselişle açıldı\"", [
        r"\b(borsa(sı|ları|lar)?|bist ?(100|30)?|nasdaq|dow jones|nikkei|dax)\b"
        r".{0,40}(güne|haftaya|kapan|açıl|yükseliş|düşüş|karışık seyir|"
        r"değer (kazan|kaybet))",
        r"piyasalar(da|ı)? (bugün|güne|hafta)",
    ]),
    ("petrol ve emtia fiyatı",
     "#74536 'Brent · petrolün' 91 haber: \"Brent petrolün varili 68,50 dolar oldu\"", [
        r"\bbrent\b", r"petrol(ün)? (varil|fiyat)", r"varil(i|ine)? \d",
        # #75152 'Kulesi · sondaj' 37 haber: haftalık sondaj kulesi sayımı
        r"sondaj kulesi sayısı",
    ]),
    ("şans oyunu sonucu",
     "#73225 'Loto · sonuçları' 69 haber: \"Süper Loto sonuçları açıklandı\"", [
        r"\bloto(su)?\b", r"şans topu", r"on numara", r"milli piyango",
    ]),
    ("tarihte bugün",
     "#93089 'Hakimiyet Gazetesi' 160 haber: \"Bursa Hakimiyet Gazetesi'nin "
     "arşivinden tarihte bugün | 1 Mart\"", [
        r"tarihte bugün", r"arşivinden",
    ]),
    ("planlı kesinti ve kurum duyurusu",
     "#92310 'BUSKİ · kesintisi' 66 haber: \"BUSKİ'den o mahallelere kötü "
     "haber! Bursa'da 10 saatlik su kesintisi\"", [
        r"(su|elektrik|doğal ?gaz|enerji)(ler)? kesinti",
        r"(su|elektrik)(ler)? (verilemeyecek|kesilecek)",
        r"\b(buski|uedaş|bursagaz)\b.{0,40}(duyuru|uyarı|kesinti|kötü haber)",
        # #74312 'Müdürlüğü · duyuru' 37: "BURSA İL SAĞLIK MÜDÜRLÜĞÜ'nden duyuru!"
        r"['’]n?(den|dan) duyuru\W*$",
    ]),
    ("sefer iptali duyurusu",
     "#74059 'BUDO · iptal' 45 haber: \"Bursalılar dikkat! BUDO seferleri iptal\"", [
        r"sefer(ler)?(i|ine)? (iptal|yapılamayacak)",
        r"\b(budo|ido|feribot|deniz otobüsü)\w*['’]?\w*\b.{0,40}(iptal|engel)",
    ]),
    ("tüik ve ekonomik gösterge", "5 Eylül listesi + #75613 'Fiyat Endeksi' 41 "
     "haber: \"Konut Fiyat Endeksi mart ayında arttı\"", [
        r"\btüik\b", r"enflasyon.*(açıklandı|belli oldu|rakam|oran|yüzde)",
        r"(sanayi üretimi|işsizlik oranı|cari (açık|fazla)|dış ticaret)",
        r"faiz kararı", r"\bppk\b",
        r"\bendeks(i|leri)?\b",
        # #90255 'KKM · düşüş' 29 haber: haftalık bakiye açıklaması
        r"\bkkm\b.*(bakiye|hesap|çıkış|düşüş)",
        r"rezerv(ler)?i? (arttı|azaldı|geriledi|yükseldi)",
    ]),
    ("dini gün ve resmi tatil",
     "takvim türü: kandil, arefe ve bayram tatili her yıl aynı başlıkla döner", [
        r"kandil(i|in|iniz)?\b.*(ne zaman|mesaj|hangi gün|kutlu)",
        r"kandil mesaj",
        r"(bayram|arefe|yılbaşı|resmi) .{0,20}tatil",
        r"(bayram|arefe|tatil).{0,20}(kaç gün|ne zaman|uzatıl)",
        r"arefe günü",
    ]),
    ("burç ve yaşam köşesi", "5 Eylül listesi", [
        r"burç", r"günlük burç", r"astroloji",
        r"kolonya|çay demleme|tarif",
        r"günün (menü|sözü|fotoğraf|karikatür)",
    ]),
    ("tarihli servis başlığı", "5 Eylül listesi", [
        r"\(\d{1,2} \w+ \d{4}", r"\d{1,2} \w+ \d{4} .*(fiyat|hava|vakit|eczane)",
        r"bugün ne (var|oldu)", r"trafik yoğunluk",
    ]),
    ("maç günü rutini", "5 Eylül listesi + #76061 'Süper Lig' 34 haber: "
     "\"Süper Lig'de 27. haftanın hakemleri açıklandı\"", [
        r"canlı (izle|yayın|anlatım)", r"hangi kanalda", r"saat kaçta",
        r"maç(ı|ın)? (özeti|sonucu|kadrosu|hakemi|11'i|ilk 11)",
        r"muhtemel 11", r"ilk 11", r"puan durumu", r"maç sonucu",
        r"kaç kaç", r"\d+-\d+ ?(mağlup|galip|yendi|kazandı|berabere)",
        r"hakem(ler)?i (açıklandı|belli oldu)", r"haftanın hakem",
        r"hazırlık(lar)?(ı|ını) sürdür", r"\bantrenman", r"hazırlık maçı",
    ]),
    ("televizyon programı", "5 Eylül listesi + #77159 'İbo Show' 34 haber: "
     "\"İbo Show'un bu haftaki konukları belli oldu\"", [
        r"bu akşam .*(dizi|film|bölüm)", r"reyting", r"yeni bölüm fragman",
        r"konukları (belli oldu|kimler|açıklandı)",
    ]),
    ("ücret ve vergi tablosu", "5 Eylül listesi", [
        r"asgari ücret .*(ne kadar|kaç|zam)",
        r"emekli (maaş|zam).*(ne kadar|kaç|hesap)",
        r"kira artış oranı", r"vergi dilim", r"harç .*ne kadar",
    ]),
    ("sayaç ve bilanço",
     "#75548 'Asya · bilançosu' 37 haber: \"Asya ülkelerinde koronavirüs "
     "bilançosu açıklandı\"", [
        r"can kaybı .*(yükseldi|çıktı|arttı)",   # günlük sayaç, gelişme değil
        r"etkisiz h[aâ]le getirildi",             # haftalık bilanço
        r"(vaka|ölü|iyileşen|aşı dozu)(lar|ların|lerin)? sayısı",
        r"(koronavirüs|kovid|covid)[\w'’-]* (bilanço|ile ilgili gelişme|"
        r"salgınına ilişkin gelişme)",
        r"son 24 saatte", r"testi pozitif",
        # #73273 'TSK · terörist' 26: "İşte öldürülen terörist sayısı"
        r"terörist sayısı",
        r"(hafta|ay|yıl)(lık|ın) (bilanço|özet)",
    ]),
    ("asayiş bülteni",
     "#91447 'Kayseri · yakalandı' 46 haber: \"Kayseri'de kesinleşmiş cezası "
     "bulunan ihraç müdür yakalandı\"", [
        r"kesinleşmiş (hapis )?ceza",
        r"aranan (hükümlü|şahıs|firari)",
        # #89476 'Çanakkale Ayvacık' 24: "Ayvacık açıklarında 29 kaçak göçmen kurtarıldı"
        # Yalnız yakalama/kurtarma bülteni: "göçmen teknesi battı" bir olaydır.
        r"(kaçak|düzensiz) göçmen\w* .{0,25}(yakalandı|kurtarıldı|yakalanırken|"
        r"gözaltına|sınır dışı)",
        r"açıklarında .{0,25}göçmen",
        # #75351 'MSB · imha' 34: "Barış Pınarı bölgesinde EYP imha edildi"
        r"\b(eyp|mayın)\w*['’]?\w* .{0,20}imha",
    ]),
    ("gemi geçişi",
     "#74894 'Boğazı · gemisi' 105 haber: \"Rus savaş gemisi Çanakkale "
     "Boğazı'ndan geçti\"", [
        r"boğaz\w*['’]?\w* (geçti|geçiş)",
    ]),
    ("ilan ve kadro duyurusu",
     "#78172 'Üniversitesi · alacak' 71 haber: \"Koç Üniversitesi 2 öğretim "
     "üyesi alacak!\"", [
        r"icradan satılık",
        r"(öğretim üyesi|akademik personel|personel|sözleşmeli|işçi|memur) "
        r"al(acak|ınacak|ımı)",
        r"istihdam edecek",
    ]),
    ("meclis ve protokol", "5 Eylül listesi", [
        r"meclisi? (toplan|gündem)", r"meclis toplantısı",   # aylık meclis
        r"(ile|’la|’le|'la|'le) (telefonda |telefonla )?görüştü\W*$",  # protokol
        r"telefonda görüştü", r"emsal karar",                # dizi biçimli köşe
    ]),
    ("numaralı dizi", "5 Eylül listesi", [
        r"#\d+", r"\| [A-ZÇĞİÖŞÜ ]{4,}$",                # video dizisi numarası
    ]),
]
RUTIN_KALIPLARI = [re.compile(k, re.IGNORECASE)
                   for _, _, kaliplar in RUTIN_GRUPLARI for k in kaliplar]
_RUTIN_GRUP = [(ad, re.compile("|".join(f"(?:{k})" for k in kaliplar), re.IGNORECASE))
               for ad, _, kaliplar in RUTIN_GRUPLARI]

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

# Kurum adlarının baş sözcüğü: cümle ortasında hep büyük yazıldığı için
# varlık sayılır ama tek başına ad değildir ("Üniversitesi", "Festivali").
# Dosya adında önündeki özel adla genişletilir (`Motor._kurum_genislet`).
KURUM_BASI = frozenset(kokle(k) for k in """
üniversitesi üniversite lisesi lise okulu festivali festival müdürlüğü
belediyesi bakanlığı hastanesi mahallesi caddesi bulvarı köyü dağı denizi
gölü boğazı otoyolu köprüsü parkı meydanı kurulu derneği vakfı odası
borsası partisi meclisi kulübü merkezi fakültesi valiliği emniyeti
başkanlığı ödülleri ödülü kupası ligi şampiyonası maratonu fuarı müzesi
sarayı camii havalimanı limanı barajı tüneli hattı organize sanayi bölgesi
radyosu gazetesi ajansı takımı ordusu rasathanesi enstitüsü komisyonu konseyi
birliği federasyonu bankası sendikası cezaevi adliyesi mahkemesi şirketi
şubesi teşkilatı nehri çayı ırmağı adası körfezi ovası yaylası şelalesi
kalesi santrali fabrikası tesisi orkestrası
""".split())

# Ad olamayacak yüzeyler: çekimli fiil (geçmiş, gelecek, şimdiki, şart,
# ulaç) ve uzun hâl ekleri. Sözlük değil, ek kalıbı; "kesinti" gibi "-ti"
# ile biten adlar da elenebilir — o zaman sıradaki kök denenir.
_CEKIMLI = re.compile(
    r"(dı|di|du|dü|tı|ti|tu|tü|dık|dik|duk|dük|tık|tik|tuk|tük|mış|miş|muş|"
    r"müş|acak|ecek|acağı|eceği|yor|ıyor|iyor|arak|erek|ınca|ince|unca|ünce|"
    r"yken|ken|ması|mesi|malı|meli|sa|se|"
    r"ndan|nden|ndaki|ndeki|daki|deki|taki|teki|nda|nde|yla|yle|larla|lerle|"
    r"nın|nin|nun|nün|ğını|ğini|ğunu|ğünü|"
    r"ına|ine|una|üne|sına|sine|suna|süne|ya|ye)$")


# Olay sözcüğü olarak bir şey söylemeyen sıfat ve zarflar.
_AD_DISI = frozenset("""
yeniden şok flaş sıcak önemli kritik acı kötü müjde sert dev tarihi resmi
""".split())


def _tumu_buyuk(metin: str) -> bool:
    harfler = [c for c in metin if c.isalpha()]
    return len(harfler) > 1 and all(c.isupper() for c in harfler)


def _harf_bicimi(metin: str) -> str:
    """Tümü büyük harfli öbeği başlık biçimine çevirir; kısaltmayı korur.

    `site_etiket.baslikla` Türkçe İ/ı çiftini doğru çevirir ve üç harfe
    kadar kısaltmayı (MSB, TFF) korur. Tek kelime olduğu gibi kalır: tek
    kelimelik tümü büyük çapa çoğunlukla bir kısaltma ya da markadır
    (BUSKİ, AFAD, ASELSAN).
    """
    if not _tumu_buyuk(metin) or " " not in metin.strip():
        return metin
    from .templatetags.site_etiket import baslikla
    return baslikla(metin)


def gelisme_var(baslik: str, kokler=()) -> bool:
    """Başlıkta gelişme dili var mı? Kök YA DA yüzey `GELISME` ile başlar.

    19 Ekim 2026: yalnız köke bakılıyordu ve son ek düşürme kökü kısaltınca
    kaçıyordu — "istifa" → "istif", "ihale" → "ihal" `GELISME`deki
    "istifa"/"ihale" ile başlamaz. Yüzeye de bakılınca "İYİ Parti'de şok
    istifa" gibi başlıklar gelişme sayılır.
    """
    if any(k.startswith(GELISME) for k in kokler):
        return True
    return any(kucuk(k).startswith(GELISME) for k in _KELIME.findall(_KESME.sub("", baslik)))


def rutin_mu(baslik: str) -> bool:
    return rutin_turu(baslik) is not None


def rutin_turu(baslik: str) -> str | None:
    """Başlık periyodik bir türe uyuyorsa grubun adı ("borsa açılış ve
    kapanışı"), uymuyorsa None. Gerekçe metinleri bu adı yazar."""
    b = kucuk(baslik)
    for ad, kalip in _RUTIN_GRUP:
        if kalip.search(b):
            return ad
    return None


@dataclass(frozen=True)
class Parca:
    kok: str
    yuzey: str
    buyuk: bool      # büyük harfle mi yazılmış
    orta: bool       # cümle ortasında mı (büyük harf kanıt sayılır)
    sira: int = -1   # başlıktaki kelime sırası; atlanan kelimeler de sayılır


def parcala(baslik: str) -> list[Parca]:
    """Başlığın kökleri; sırası korunur, tekrar yok."""
    temiz = _KESME.sub("", baslik)
    bulunan: list[Parca] = []
    gorulen: set[str] = set()
    konum = 0
    for sira, esle in enumerate(_KELIME.finditer(temiz)):
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
        bulunan.append(Parca(kok, kelime, kelime[0].isupper(), not sinir, sira))
    return bulunan


def ikililer(parcalar: list[Parca]) -> list[tuple[str, str]]:
    """Yan yana iki büyük harfli kelime: (kök, yüzey). "Ece Gürel" gibi.

    "Yan yana" başlıkta yan yana demek (19 Ekim 2026): unvan ve durak
    kelimesi kökten düşüyor, araya giren kelime atlanınca "Sağlık Bakanı
    Müezzinoğlu" → "Sağlık Müezzinoğlu", "Savunma Bakanı Katz" → "Savunma
    Katz" diye var olmayan adlar doğuyordu.
    """
    cikti = []
    for a, b in zip(parcalar, parcalar[1:]):
        if a.buyuk and b.buyuk and b.orta and b.sira == a.sira + 1:
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
        self.ikili_orta: Counter = Counter() # ikili, başlığın ilk kelimesinden başlamıyor
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
            if not yuzey.startswith(parcalar[0].yuzey + " ") or parcalar[0].orta:
                self.ikili_orta[kok] += 1

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

        gelisme = sum(1 for h in uyeler if gelisme_var(h.baslik, h.kokler))
        if self._periyodik_mi(n, len(gunler), gelisme):
            return None

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
        ad = self._dosya_adi(capalar, cekirdek, uyeler, anahtarlar)
        if not ad:
            ad = anahtarlar[0]
            ek = [a for a in anahtarlar[1:] if not _CEKIMLI.search(kucuk(a))]
            if ek and " " not in ad:
                ad = f"{ad} · {ek[0]}"
        gerekce = (f"{n} haber, {len(gunler)} ayrı gün, {sure} günlük süre; "
                   f"'{anahtarlar[0]}' üyelerin %{round(en_kapsayan * 100)}'inde, "
                   f"arşivde {self.df[ana_kok]} başlıkta; "
                   f"{gelisme} başlıkta gelişme dili.")
        return Konu(ad=ad, anahtarlar=anahtarlar, uyeler=uyeler,
                    guven=guven, gerekce=gerekce)

    @staticmethod
    def _periyodik_mi(n: int, gun: int, gelisme: int) -> bool:
        """Dizi mi, dosya mı? Bkz. `PERIYODIK_*` notu."""
        return (n >= PERIYODIK_EN_AZ_UYE and gun / n > PERIYODIK_GUN_ORANI
                and gelisme / n < PERIYODIK_GELISME)

    # --- ad
    def _dosya_adi(self, capalar, cekirdek, uyeler, anahtarlar=()) -> str:
        """Okunur dosya adı: varlık çapası + olay sözcüğü.

        5 Eylül adları kök listesinin ilk iki öğesiydi ve okunmuyordu:
        "Peki Bursa" (cümle başı + yer), "Festivali" (kurum adının başı),
        "Reina · saldırganından" (çekimli olay sözcüğü). Kural:

        1. Çapa: ikili ad yalnız iki parçası da varlıksa ("Ece Gürel" evet,
           "Peki Bursa" hayır). Kurum başı ("Üniversitesi", "Festivali")
           üyelerde önündeki özel adla genişler ("Koç Üniversitesi"); tek
           bir ad baskın değilse çapa sayılmaz. Yer adı ancak başka çapa
           yoksa.
        2. Tek kelimelik çapaya olay sözcüğü eklenir: çekirdekten, varlık
           olmayan, çekimli fiil ya da hâl ekli biçim olmayan ilk kök.
           Üyelerdeki en kısa yüzey alınır ("saldırgan", "saldırganından"
           değil).
        3. Harf biçimi `site_etiket` süzgeçleriyle (`kucult`, `baslikla`);
           `.title()`/`.upper()` Türkçe'de İ/ı'yı bozar.

        Ad bulunamazsa boş döner; çağıran eski yola (ilk anahtar) düşer.
        """
        adaylar: list[tuple[bool, str, str]] = []    # (yer_mi, kök, gösterim)
        for _, k in capalar:
            gosterim = self._capa_adi(k, uyeler)
            if gosterim:
                adaylar.append((self.yer_mi(k), k, gosterim))
        if not adaylar:
            return ""      # çağıran eski bileşime düşer
        adaylar.sort(key=lambda a: (a[0], " " not in a[2]))   # yer sona, çok kelime öne
        _, ana_kok, ana = adaylar[0]
        if " " not in ana:
            ana = self._kurum_ile(ana_kok, ana, uyeler)
        if " " in ana:
            return ana
        olay = self._olay_sozcugu(cekirdek, set(ana_kok.split("_")), uyeler)
        if olay:
            return f"{ana} · {olay}"
        ikinci = [g for yer, _, g in adaylar[1:] if not yer] + list(anahtarlar[1:]) \
            + [g for yer, _, g in adaylar[1:] if yer]
        for g in ikinci:
            if kucuk(g) != kucuk(ana) and kucuk(g) not in kucuk(ana) \
                    and not _CEKIMLI.search(kucuk(g)) and kucuk(g) not in _AD_DISI:
                return f"{ana} · {g}"
        return ana

    def _ikili_ad_mi(self, kok: str) -> bool:
        """İkili gerçek bir ad mı? İki parçası da varlıksa evet. Değilse
        başlık başı dışında da geçmeli: "Peki Bursa" yalnız başlığın ilk
        iki kelimesidir; "Sinan Ateş" ("ateş" küçük harfle de yazılır)
        cümle ortasında da geçer."""
        if not any(self._ad_degil_mi(p) for p in kok.split("_")):
            return True
        return self.ikili_orta.get(kok, 0) >= max(1, self.df.get(kok, 0) * 0.1)

    def _ad_degil_mi(self, kok: str) -> bool:
        """Cümle ortasında küçük harfle yazıldığı GÖRÜLMÜŞ kelime. Hiç cümle
        ortasında görülmeyen ("LeBron" hep başlık başında) bilinmiyor
        sayılır, ad olabilir."""
        orta = self.orta.get(kok, 0)
        return orta > 0 and self.orta_buyuk.get(kok, 0) / orta < VARLIK_ORANI

    def _capa_adi(self, kok: str, uyeler) -> str:
        if "_" in kok:
            return self._ad(kok, uyeler) if self._ikili_ad_mi(kok) else ""
        if kok in KURUM_BASI:
            return self._kurum_genislet(kok, uyeler)
        return self._ad(kok, uyeler)

    def _kurum_genislet(self, kok: str, uyeler) -> str:
        """"Üniversitesi" → üyelerde önünde en sık geçen özel adla birlikte."""
        sayac: Counter = Counter()
        for h in uyeler:
            kelimeler = _KELIME.findall(_KESME.sub("", h.baslik))
            for i, kelime in enumerate(kelimeler):
                if not kelime[:1].isupper() or kokle(kelime) != kok:
                    continue
                onu = []
                j = i - 1
                while j >= 0 and len(onu) < 3 and kelimeler[j][:1].isupper() \
                        and kucuk(kelimeler[j]) not in DURAK \
                        and kucuk(kelimeler[j]) not in UNVAN:
                    onu.insert(0, kelimeler[j])
                    j -= 1
                if onu:
                    sayac[" ".join(onu + [kelime])] += 1
                break
        if not sayac:
            return ""
        obek, kac = sayac.most_common(1)[0]
        if kac < max(2, len(uyeler) * 0.4):
            return ""
        return _harf_bicimi(obek)

    def _kurum_ile(self, kok: str, ana: str, uyeler) -> str:
        """Tek kelimelik çapanın ardından baskın bir kurum başı geliyorsa
        birlikte: "Şampiyonlar" → "Şampiyonlar Ligi", "Nilüfer" →
        "Nilüfer Belediyesi"."""
        sayac: Counter = Counter()
        for h in uyeler:
            kelimeler = _KELIME.findall(_KESME.sub("", h.baslik))
            for i, kelime in enumerate(kelimeler[:-1]):
                if kokle(kelime) == kok and kelimeler[i + 1][:1].isupper() \
                        and kokle(kelimeler[i + 1]) in KURUM_BASI:
                    sayac[f"{kelime} {kelimeler[i + 1]}"] += 1
                    break
        if sayac:
            obek, kac = sayac.most_common(1)[0]
            if kac >= max(2, len(uyeler) * 0.5):
                return _harf_bicimi(obek)
        return ana

    def _olay_sozcugu(self, cekirdek, haric: set[str], uyeler) -> str:
        for _, k in cekirdek:
            if k in haric or self.varlik_mi(k) or "_" in k or self.agirlik(k) < AGIRLIK_EN_AZ:
                continue
            yuzeyler = Counter()
            for h in uyeler:
                for p in parcala(h.baslik):
                    if p.kok == k:
                        yuzeyler[kucuk(p.yuzey)] += 1
            uygun = [y for y in yuzeyler if not _CEKIMLI.search(y) and y not in _AD_DISI]
            if uygun:
                return min(uygun, key=lambda y: (len(y), -yuzeyler[y]))
        return ""

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
            # Tümü büyük harf yüzey ("MÜDÜRLÜĞÜ") çoğunluk değilse büyük
            # harfli bir başlıktan gelmiştir; adın kendisi öyle değildir.
            # Çoğunluksa kısaltmadır ("FETÖ", "BUSKİ") ve öyle kalır.
            toplam = sum(yuzeyler.values())
            buyuk = sum(n for y, n in yuzeyler.items() if _tumu_buyuk(y))
            tercih_buyuk = buyuk * 2 >= toplam
            obek, _ = max(yuzeyler.items(), key=lambda ci: (
                _tumu_buyuk(ci[0]) == tercih_buyuk, ci[1], len(ci[0])))
            return _harf_bicimi(obek) if _tumu_buyuk(obek) and not tercih_buyuk else obek
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


RUTIN_COGUNLUK = 0.5     # üyelerin bu paydan FAZLASI periyodik kalıptaysa dosya bir türdür
                         # (yarı yarıya olan bir olaydır: "buzul faciası" + iki sayaç)


def periyodik_gerekce(uyeler) -> str:
    """Kayıtlı bir dosya kullanıcının "konu değil" dediği türden mi?

    `uyeler`: `(tarih, başlık)` çiftleri. Motorun iki ölçütü, dosyanın
    kendisine uygulanır (5 Eylül'de onaylanmış dosyalar bu ölçütlerden
    önce yazıldı):

    1. Başlık kalıbı: üyelerin yarısından fazlası periyodik bir türde
       (`rutin_turu`).
    2. Yapı: `Motor._periyodik_mi` — en az 15 haber, her gün bir tane,
       gelişme dili yok.

    Dönen metin okunur gerekçedir; ölçüt tutmazsa boş metin.
    """
    uyeler = list(uyeler)
    n = len(uyeler)
    if not n:
        return ""
    turler = Counter(t for t in (rutin_turu(b) for _, b in uyeler) if t)
    rutin = sum(turler.values())
    if rutin and rutin > n * RUTIN_COGUNLUK:
        tur, _ = turler.most_common(1)[0]
        return f"periyodik tür '{tur}': {rutin}/{n} başlık kalıba uyuyor"
    gun = len({t for t, _ in uyeler})
    gelisme = sum(1 for _, b in uyeler if gelisme_var(b))
    if Motor._periyodik_mi(n, gun, gelisme):
        return (f"dizi görünümü: {n} haber, {gun} ayrı gün "
                f"(gün/haber {gun / n:.2f}), gelişme dili {gelisme}/{n}")
    return ""


def tara(kayitlar) -> list[Konu]:
    """Tek çağrıda iki geçiş. `kayitlar` iki kez dolaşılır; liste ver."""
    kayitlar = list(kayitlar)
    kayitlar.sort(key=lambda k: (k[2], k[0]))
    m = Motor()
    for _, baslik, _ in kayitlar:
        m.say(baslik)
    return m.konular(m.zincirle(kayitlar))
