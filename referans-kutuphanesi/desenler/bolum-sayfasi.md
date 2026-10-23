# Bölüm sayfası — siteler arası desenler

Son güncelleme: 2026-10-20 (sentez; tohum 2026-10-19 korundu) · Kaynak siteler:
Spiegel, Habertürk, Bursada Bugün, Bursa Saati, Ege'de Son Söz, Özgür Kocaeli
(doğrudan); Guardian, BBC, Hürriyet, Milliyet (eski kayıt).

Kanıt: **D** doğrudan · **İ** ikincil · **E** eski kayıt (URUN-PLANI §46/§59,
2 Eylül / 6 Eylül 2026; URL ve ölçü kaydı yok), bu taramada **doğrulanmadı**.

## Kalıp — doğrudan ölçülenler (2026-10-20)

| Site | K. | Kademe ve akış | Sonraki sayfa | Kaynak |
|---|---|---|---|---|
| Spiegel `/ausland/` | D | bölüm başlığı + tek satır tanım → **konu hapları** → **3 konu kümesi** (her biri 1 büyük + birkaç kart) → **20'lik kronolojik liste**. Ray yok, tek sütun. Kartta mutlak tarih-saat, ücretli içerikte "+" işareti | numaralı (1/500) + "daha eski" | `siteler/spiegel.md` §2 · [/ausland/](https://www.spiegel.de/ausland/), 2026-10-20 |
| Habertürk `/ekonomi` | D | piyasa şeridi → manşet kaydırıcı (10) + 4 kutu → **veri ve haber blokları dönüşümlü** (hisseler, kur çevirici, kripto, KAP listesi arasında 9'luk haber blokları) → en çok okunanlar; 14 kalemli alt menü | sonsuz yükleme (uç bota kapalı) | `siteler/haberturk.md` §2 · [/ekonomi](https://www.haberturk.com/ekonomi), 2026-10-20 |
| Bursada Bugün `/bursa-bolge-haberleri` | D | JSON-LD `CollectionPage` + `BreadcrumbList`; kademe ölçülmedi | numaralı (`/2.html`…) | `siteler/bursada-bugun.md` §2 · [bölüm](https://www.bursadabugun.com/bursa-bolge-haberleri), 2026-10-20 |
| Bursa Saati `/bursa` | D | 59 kart başlığı; kademe ölçülmedi | "Daha fazla göster" (JSON ucu, robots'ta kapalı) | `siteler/bursa-saati.md` §2 · [bölüm](https://www.bursasaati.com.tr/bursa), 2026-10-20 |
| Ege'de Son Söz `/yerel-yonetimler` | D | 16 `h3` + 59 `h4` kart; kademe ölçülmedi | "Daha fazla göster" (JSON ucu) | `siteler/egede-son-soz.md` §2 · [bölüm](https://www.egedesonsoz.com/yerel-yonetimler), 2026-10-20 |
| Özgür Kocaeli `/kocaeli-haberleri` | D | `CollectionPage`; 35 kart; kademe ölçülmedi | bölüm arşivine bağlantı (`/arsiv/…`) | `siteler/ozgur-kocaeli.md` §2 · [bölüm](https://www.ozgurkocaeli.com.tr/kocaeli-haberleri), 2026-10-20 |

## Kalıp — tohum (§46), doğrulanmadı (eski kayıt)

| Site | K. | Çözüm |
|---|---|---|
| Guardian | E | Solda bölüm adı, ortada manşet (metin solda + büyük fotoğraf sağda), altında küçük görselli iki sütunlu yoğun liste |
| BBC | E | Manşet + sağda metin öncelikli üç haber rayı, sonra 3'lü orta kart satırı, sonra 5'li küçük kart satırı |
| Hürriyet | E | Başlığın yanında etiketlerle hızlı gündem rafı; manşet altında tek sütunlu, fotoğraf solda satırlar |
| Milliyet | E | Manşet + sağ ray, sonra gri bantta 4'lü küçük kart şeridi |

Guardian, BBC, Hürriyet, Milliyet bu taramada açılamadı (otomatik erişim yok;
`SITELER.md` "Erişim durumu"). §59'daki "ek bloklar" (Guardian · BBC · NYT ·
Hürriyet) da doğrulanmadı (eski kayıt).

**Ortak ders.**
- Doğrudan görülen tek tam kademe örneği Spiegel: **editörün gündemi (konu
  kümeleri) + "kaçırdığım var mı" akışı (kronolojik liste)** ikilisi. Tohumdaki
  "manşet → orta → yoğun akış" dersiyle aynı yönde, ama kademe ölçüsü konu.
- Ekonomi bölümünde Habertürk veriyi haberin **arasına** koyuyor; bölüm bir
  piyasa paneli gibi davranıyor (ayrıntı `ekonomi-sayfasi.md`).
- Sonraki sayfa: üç cevap var: numaralı (Spiegel, Bursada Bugün), "daha
  fazla" JSON ucu (Bursa Saati, Ege), arşive bağlantı (Özgür Kocaeli). JSON
  uçları robots'ta kapalı; o sitelerde arşive giden taranabilir yolun ne
  olduğu ölçülmedi.

**Hangi koşulda işe yarıyor.** Konu kümesi, bölümde aynı anda 2–3 süren konu
varsa dolu görünür. Spiegel ulusal bir masayla 3 küme kuruyor; küçük yerel
masada 1–2 küme gerçekçi (`spiegel.md` Özet 1). Veri–haber dönüşümü yalnız
bölümün canlı verisi varsa (ekonomi, spor) anlamlı.

**Bursa Hakimiyet'te durum.**
- `uygulama/sablonlar/kategori.html`: tema `bas` yuvası ya da servis şeridi
  (`parca/bolum_servis.html`; döviz / puan / nöbetçi eczane) → üç kartlı
  kademe (ilki geniş, spotlu) → bölüme özel EN ÇOK OKUNANLAR → ikili/üçlü
  ritimli akış (§60) → "daha fazla göster" → tema `alt` yuvası → görüntü
  kuşağı (videolar + galeriler, §59).
- "Daha fazla göster" **gerçek bağlantı** (`?sayfa=N`), JS'siz de çalışır;
  parça ucu `/daha-fazla` robots'ta kapalı (`icerik/views.py` 541–555,
  `besleme/gorunumler.py` robots).
- Sağ ray bilinçli olarak yok (§46; içerik sütunu 1080 → 740 px olurdu).
- Bölüm JSON-LD'si yalnız `BreadcrumbList` (`kategori.html:11`);
  `CollectionPage` yok.
- Konu dosyaları var (konu motoru, onaylı konular, `/konular`), bölüm
  sayfasına kümelenmiyor.

**Öneri.**
- Bölüm sayfasına 1–2 **konu kümesi** (bölümdeki onaylı, süren konu dosyası
  varsa; yoksa yuva çizilmez) → P2 · M · → `web-tasarim-direktoru` +
  `haber-muduru` (hangi konu "süren" sayılır).
- `CollectionPage` JSON-LD → P2 · S · → `seo-buyume-uzmani`.
- Etiket bulutu → **BH için: reddedildi (kullanıcı kararı — etiket sayfası yok).**

**Açık sorular.** Guardian/BBC/Hürriyet/Milliyet bölüm kademeleri yalnız elle
gözlemle doğrulanabilir (kim, ne zaman, hangi koşul yazılarak). Yerel
sitelerde bölüm sayfasının kademe ve rayı ekran görüntüsüyle ölçülmedi.
