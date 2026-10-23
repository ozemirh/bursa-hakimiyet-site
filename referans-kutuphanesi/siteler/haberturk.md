# Habertürk

- Adres: https://www.haberturk.com
- Katman: ulusal
- Neden seçildi: Video/TV entegrasyonu ve servis sayfaları; ekonomi sayfası odak konusu (piyasa verisi + haber aynı bölümde).
- İnceleme: 2026-10-20 (09:32–09:41 TSİ) · koşul: masaüstü 1440×900 / mobil 390×844 (DPR 3, dokunma öykünmesi) · çerez **kabul edilmedi** (bant açık) · önbellek kapalı, temiz profil · konum: Türkiye (yerel makine, ev bağlantısı)
- Erişim: robots.txt okundu (2026-10-20): yalnız `User-agent: *` bölümü var; `Claude-User`/`ClaudeBot`/`anthropic-ai` için ayrı kural ve başlık yorumu **yok** → izinli. Yasak yollar (`/infinite/news/*`, `/liste/sonhaberler`, `/chart/*`, `/etiket/`, `/yorumlar` …) istenmedi. ([robots](https://www.haberturk.com/robots.txt), 2026-10-20)
- İstek: 14 (curl 9 · başsız Chrome 5) · `curl` varsayılan UA, Chrome UA'sı değiştirilmedi.
- İncelenen sayfalar: anasayfa ([A](https://www.haberturk.com/)), ekonomi bölümü ([E](https://www.haberturk.com/ekonomi)), dolar enstrüman sayfası ([D](https://www.haberturk.com/ekonomi/piyasa/88-dolar)), ekonomi haber detay ([HD1](https://www.haberturk.com/ekonomi/fon-yasasi-teklifi-bugun-tbmm-genel-kurulu-nda-3920983)), son dakika etiketli haber detay ([HD2](https://www.haberturk.com/gundem/son-dakika-haberi-meteoroloji-den-dogu-karadeniz-icin-yagmur-uyarisi-sicakliklar-mevsim-normali-altinda-20-ekim-hava-durumu-3920978)), son dakika listesi ([SD](https://www.haberturk.com/son-dakika-haberleri)), Google News sitemap ([S](https://www.haberturk.com/sitemap_google_news.xml)).

## Özet — en öğretici 3 çözüm

1. **İki katmanlı ekonomi: piyasa şeridi → enstrüman sayfası → haber.** Her ekonomi sayfasında (bölüm ve detay) 11 kalemlik piyasa şeridi duruyor; her kalem kendi enstrüman sayfasına gidiyor. Enstrüman sayfasında alış/satış/fark/önceki kapanış/en yüksek/en düşük ve **saniyeli "Güncelleme" damgası** var. Bu, rakam arayan okuru haber akışından ayırıp kalıcı, arama motorunda sıralanan bir adrese topluyor ([E](https://www.haberturk.com/ekonomi), [D](https://www.haberturk.com/ekonomi/piyasa/88-dolar), 2026-10-20). BH'ye: **kısmen**. Enstrüman sayfası kalıbı taşınabilir. Şeritte veri zamanı yazmıyor; BH'nin "bayat veri tarihle gösterilir" kararı bunu zaten daha sıkı istiyor.
2. **"Son dakika" görünen başlıkta değil, SEO katmanında.** Son dakika haberinde `<title>` ve JSON-LD `headline` "SON DAKİKA HABERİ:" önekiyle başlıyor; görünen H1 temiz ve kısa (86 karakter), `alternativeHeadline` = H1. Adres de `son-dakika-haberi-…` önekli ([HD2](https://www.haberturk.com/gundem/son-dakika-haberi-meteoroloji-den-dogu-karadeniz-icin-yagmur-uyarisi-sicakliklar-mevsim-normali-altinda-20-ekim-hava-durumu-3920978), 2026-10-20). Neden: arama ve Discover'da "son dakika" sorgusunu yakalarken sayfadaki başlığı bağırmaktan kurtarıyor. BH'ye: **kısmen**. Başlık ile SEO başlığını ayırmak işe yarar. Etiketin sürekli kullanılması "son dakika"nın anlamını aşındırır; bu editoryal karar `haber-muduru`nundur.
3. **Haber detayda sonsuz akış + ayrı adres.** Detay `<article>` bir sonraki haberin adresini (`/infinite/news/<id>`) veri niteliğinde taşıyor; kaydırınca ikinci haber aynı sayfaya yükleniyor (1440'ta ölçüldü: 1 → 2 `article`). Bot için yol robots.txt'de kapalı, yani her haberin kanonik adresi tek ([HD1](https://www.haberturk.com/ekonomi/fon-yasasi-teklifi-bugun-tbmm-genel-kurulu-nda-3920983), [robots](https://www.haberturk.com/robots.txt), 2026-10-20). BH'ye: **kısmen**. Sayfa başına gösterim için güçlü bir yol, ama JS ve ölçüm yükü getiriyor. Sunucu render + küçük masa için "okumaya devam" bloğu daha ucuz.

## 1. Anasayfa bilgi mimarisi

Kaynak: [A](https://www.haberturk.com/) HTML'inde `data-section` sırası (curl, 2026-10-20 09:32) + 1440 ekran görüntüsü (Chrome, 09:38).

- **Üstten aşağı sıra:** yapışkan piyasa şeridi (BIST 100, dolar, euro, gram altın, bitcoin, faiz) → yapışkan başlık (arama, "TV Canlı", logo, il ve hava) → ana menü (12 bölüm + "Resmi İlanlar") → 970×250 masthead reklam + iki yanda sabit 160×600 sayfa giydirme → **`topHeadlinesOfDay`: 4 kartlık sürmanşet** → tam genişlik sponsor bandı → **Manşet** (iki parça: 3 öğe + numaralı ~20 öğelik kaydırıcı) → Başlıca Haberler (3) → Resmi İlanlar → spor bandı → Son Yazılar (10 köşe yazısı) → Kahve Molası (10) → Bilgi (10) → Karikatür (5) → HT Trend → HT Hayat → Akıl Oyunları → Keşfet (5) → Ekonomi (5) → Şirketler (sponsorlu) → Magazin (5) → Spor (5) → İnfografik (8) → Yaşam (5) → Gastro (10) → Dünya (5) → Günlük burç → Show TV bandı → HT Kulüp → **Yerel Haberler (10)** → altbilgi (bülten formu, uygulama, sosyal).
- **Manşet tipi:** çoklu. 4'lü sürmanşet + kaydırıcı manşet.
- **Yoğunluk (1440, ilk ekran):** 11 başlık bağlantısı (görünür, metni ≥ 25 karakter olan `<a>`; başsız Chrome, çerez bandı açık). İlk ekranın büyük kısmı 970×250 reklam + sponsor bandı.
- **Resmi ilan yuvaları:** HTML'de `officialAnnouncements1…15` adlı 16 yuva var; bu ölçümde ikisi doluydu (mahkeme/belediye ilanları, `/resmi-ilanlar/...` adresleri), diğerleri boş yer tutucu. Resmi ilan anasayfada bölümler arasına serpiştirilmiş bir modül.
- Sayfa boyu 13.314 px (1440), DOM 2.934 öğe.

## 2. Bölüm sayfası

Kaynak: [E](https://www.haberturk.com/ekonomi), curl + `data-section`/`data-type` sırası, 2026-10-20.

- **Kademe:** piyasa şeridi (`financeSSI`, 11 kalem: BIST 100, dolar, euro, gram altın, bitcoin, faiz, gümüş gram, GBP/TRY, EUR/USD, Brent, çeyrek altın) → **Manşet** kaydırıcı (10) + 4 küçük kutu → **Hisseler** tablosu → Başlıca Haberler (3) → mobil reklam → **Kur çevirici** (12 para birimi) → **Kripto para** özeti → Ekonomi Haberleri (9) → Resmi İlanlar → Elektrikli Araçlar → Alışveriş → **KAP Haberleri** (tarih-saat damgalı bildirim listesi) → Ekonomi Haberleri ×3 (9'ar) → En Çok Okunanlar.
- **Veri ve haber dönüşümlü:** Haber blokları ile veri blokları (hisseler, kur çevirici, kripto, KAP) sırayla dizilmiş. Ekonomi bölümü bir "piyasa paneli" gibi davranıyor.
- **Alt menü** (ekonomi detayında görüldü, 1440 ekran görüntüsü): Altın, Döviz, Borsa, KAP Haberleri, Kripto Para, İş-Yaşam, Otomobil, Turizm, Maden, Enerji, Emlak, Girişimcilik, Sigorta, Sosyal Güvenlik ([HD1](https://www.haberturk.com/ekonomi/fon-yasasi-teklifi-bugun-tbmm-genel-kurulu-nda-3920983), 2026-10-20).
- **Ray:** ekonomi detayda sağ rayda kardeş marka (BloombergHT) haberleri.
- **Sayfalama:** sayfa numarası yok; sonsuz yükleme (`/infinite/kategori/p2/ekonomi` sayfa yapılandırmasında; yol robots.txt'de bota kapalı).
- **Piyasa şeridinde veri zamanı yok** (HTML'de damga bulunmadı). Değerler sunucuda HTML'e basılmış; `data-connection` niteliği canlı güncellemeye işaret ediyor, ama güncelleme davranışı ölçülmedi.
- **Enstrüman sayfası** ([D](https://www.haberturk.com/ekonomi/piyasa/88-dolar), 2026-10-20): başlıkta değer + yüzde değişim → alış, satış, fark, önceki kapanış, en yüksek, en düşük → "Güncelleme: gg/aa/yyyy ss:dd:ss" → sekmeli tablolar (döviz/pariteler/gelişen piyasa kurları) → benzer haberler → yakıt hesaplayıcı ("depo kaça dolar") → kur çevirici. `<title>` soru kalıbında ("… Ne Kadar? … Kaç TL?"). Grafik uç noktası `/chart/*` robots.txt'de kapalı, istenmedi; grafik ölçülmedi. Meta açıklamada verinin kaynağı olarak bir serbest piyasa ve TCMB anılıyor; sayfada kaynak satırı olup olmadığı ölçülmedi.

## 3. Haber detay

Kaynak: [HD1](https://www.haberturk.com/ekonomi/fon-yasasi-teklifi-bugun-tbmm-genel-kurulu-nda-3920983) ve [HD2](https://www.haberturk.com/gundem/son-dakika-haberi-meteoroloji-den-dogu-karadeniz-icin-yagmur-uyarisi-sicakliklar-mevsim-normali-altinda-20-ekim-hava-durumu-3920978); başsız Chrome `getComputedStyle`, 2026-10-20.

| ölçü | 1440 | 390 |
|---|---|---|
| H1 | 30/36 px, 900, Poppins | 24/32 px, 900 |
| Spot (`h2`) | 16 px, kırmızı, 400 | 16 px, kırmızı |
| Gövde | 16/24 px Poppins, siyah | 16/24 px |
| Gövde sütunu | 514 px ≈ **66 karakter/satır** | 350 px ≈ 45 karakter/satır |
| H1'in üst kenarı | 539 px | 330 px |
| Gövdenin başladığı yer | **1.268 px — ilk ekranın altında** | 1.051 px — ilk ekranın altında |

(Satır başına karakter: paragraf genişliği ÷ aynı fontla `canvas.measureText` ortalama karakter genişliği.)

- **Sıra:** breadcrumb (Haberler › Ekonomi › İş-Yaşam) → H1 → kırmızı spot → bilgi satırı (kaynak simgesi + ad, **"Giriş"** ve **"Güncelleme"** mutlak tarih-saat, `<time datetime>`) → paylaşım ikonları → Google "tercih edilen kaynak" bağlantısı → 16:9 görsel (tam ekran düğmesi) → gövde (ara başlıklar `h2`) → gövde içi reklam.
- **Kaynak gösterimi:** ajans/kaynak simgesi (`alt="Kaynak"`) + kaynak adı; muhabir adı bilgi satırında görülmedi, JSON-LD `author` = `Person`.
- **Düzeltme notu:** görülmedi (iki detayda da "düzeltme" metni yok). Giriş ve güncelleme zamanı her haberde ayrı satırda.
- **Paylaşım:** Facebook, X, NSosyal, LinkedIn, WhatsApp, e-posta, yazdır, bağlantı kopyala; paylaşım bağlantıları `utm_source/medium/campaign` taşıyor. Makale sütununun altında yapışkan bir araç çubuğu var (yazı boyutu, paylaş, favoriler; 1440 ve 390 ekran görüntüsü).
- **İlgili / okumaya devam:** sağ rayda 20 kartlık "günün başlıkları" listesi + 2 kart + yazarlar bloğu; asıl "devam" mekanizması **sonsuz akış**: `data-it` içinde `next: /infinite/news/<id>`, kaydırınca ikinci haber aynı sayfaya geliyor (1440'ta 1 → 2 `article`; 390'da 5 sn içinde gelmedi).
- **Hizmet içi veri:** hava durumu haberinde gövde içinde "İllere göre hava durumu" ara bölümü ([HD2](https://www.haberturk.com/gundem/son-dakika-haberi-meteoroloji-den-dogu-karadeniz-icin-yagmur-uyarisi-sicakliklar-mevsim-normali-altinda-20-ekim-hava-durumu-3920978), 2026-10-20).

## 4. Son dakika / canlı

- **Anasayfada son dakika paneli yok.** HTML'de ve 1440 ekranda şerit veya kutu bulunmadı. Erişim, sabit **alt gezinme çubuğundaki** "Son Dakika" sekmesinden (çubuk masaüstünde de var: Anasayfa · Son Dakika · Canlı Yayın · Radyo · Bildirimler, bildirim rozeti sayılı). Ayrıca ilk ekranda 4'lü sürmanşet var ([A](https://www.haberturk.com/), 1440 ekran görüntüsü, 2026-10-20). URUN-PLANI §44'teki 2 Eylül gözlemiyle tutarlı.
- **Son dakika etiketi:** `<title>` + JSON-LD `headline` "SON DAKİKA HABERİ:" önekli; H1 öneksiz; adres `son-dakika-haberi-…` önekli. Normal ekonomi haberinde `<title>` sonuna "Son Dakika Ekonomi Haberleri" ekleniyor ([HD1](https://www.haberturk.com/ekonomi/fon-yasasi-teklifi-bugun-tbmm-genel-kurulu-nda-3920983), [HD2](https://www.haberturk.com/gundem/son-dakika-haberi-meteoroloji-den-dogu-karadeniz-icin-yagmur-uyarisi-sicakliklar-mevsim-normali-altinda-20-ekim-hava-durumu-3920978), 2026-10-20). Sitemap'teki 435 haber adresinin 60'ı `son-dakika` içeriyor (%14); 87'si `bilgi/` servis şablonunda ([S](https://www.haberturk.com/sitemap_google_news.xml), 2026-10-20).
- **Son dakika sayfası** ([SD](https://www.haberturk.com/son-dakika-haberleri), 2026-10-20): "Son Dakika" (4 kart) → bölüm bölüm bloklar (Gündem, Ekonomi, Spor, Magazin, Dünya, Yaşam, Sağlık; 6'şar kare kart) → "Öne Çıkanlar". Kartlarda tarih alanı (`data-name="date"`) var ama **boş**: ne HTML'de ne JS sonrası (Chrome 1440) saat görünmedi. Göreli zaman ("… dk önce") yok. Sayfalama yok.
- **Canlı blog:** iki detayda ve anasayfada `LiveBlogPosting` yok; ayrı bir canlı blog sayfası aranmadı, ölçülmedi. "Canlı" bağlantısı TV yayınına (`/canliyayin`) gidiyor.

## 5. Yerel ve servis içerikleri

- **Yerel:** ayrı alt alan adı `yerel-haberler.haberturk.com`; anasayfanın en altında 10 kartlık "Yerel Haberler" bloğu (kimlik aralığı ana haberlerden farklı) ([A](https://www.haberturk.com/), 2026-10-20). İl/ilçe sayfası incelenmedi, ölçülmedi.
- **Servis:** başlıkta il + anlık hava; ekonomi tarafında kur çevirici, yakıt hesaplayıcı, KAP listesi, enstrüman sayfaları. Google News sitemap'inde `bilgi/foto/` şablonunda çok sayıda **servis haberi** var: deprem listesi, akaryakıt fiyatı, baraj doluluk, Resmi Gazete özeti, sınav sonucu sorgulama, tatil günleri ([S](https://www.haberturk.com/sitemap_google_news.xml), 2026-10-20). Servis verisi kalıcı bir sayfa yerine günlük haber olarak üretiliyor.
- **Resmi ilan:** menüde "Resmi İlanlar", anasayfa ve ekonomi bölümünde resmi ilan blokları ([A](https://www.haberturk.com/), [E](https://www.haberturk.com/ekonomi), 2026-10-20).
- Eczane, namaz, trafik, ulaşım: ölçülmedi.

## 6. Mobil davranış

Kaynak: başsız Chrome 390×844, [A](https://www.haberturk.com/) (09:38) ve [HD2](https://www.haberturk.com/gundem/son-dakika-haberi-meteoroloji-den-dogu-karadeniz-icin-yagmur-uyarisi-sicakliklar-mevsim-normali-altinda-20-ekim-hava-durumu-3920978) (09:40), 2026-10-20.

- **Sabit/yapışkan öğeler (anasayfa):** piyasa şeridi 41 px (sticky) + başlık 48 px (sticky) + alt gezinme 56 px (fixed) = **145 px, ekranın %17'si** sürekli dolu. Detayda piyasa şeridi yok: başlık 48 + alt çubuk 56.
- **İlk ekran (anasayfa):** 320×100 reklam (üstten 168 px) + sponsor banner; görünür başlık bağlantısı 2.
- **İlk ekran (detay):** 320×100 masthead → breadcrumb → H1 (330 px) → spot; gövde ilk ekranın altında. Çerez bandı ekranın alt ~%22'sini kaplıyor; "Tercih Et / Reddet / Kabul Et" üç eş ağırlıklı düğme.
- Yatay taşma yok (0 px). Menü: ana menü yatay kaydırılıyor (ekran görüntüsünde "Mag…" kesik).

## 7. Başarım

Tek ölçüm, 2026-10-20, Türkiye, ev bağlantısı, kısıtlama yok. CDN önbelleği HIT (`x-cache-status: HIT`, `Cache-Control: max-age=60`). LCP değerleri CrUX saha verisiyle **karşılaştırılamaz**: ağ ve CPU kısıtlanmadı.

| sayfa | HTML (açılmış / gzip aktarım) | istek | aktarım | LCP | CLS |
|---|---|---|---|---|---|
| anasayfa 1440 | 367.066 B / 57.809 B | 196 (28 alan adı) | 11,75 MB | 292 ms (manşet görseli) | 0,008 |
| anasayfa 390 | — | 163 | 8,25 MB | 252 ms | 0 |
| ekonomi | 218.711 B / 35.004 B | ölçülmedi | ölçülmedi | ölçülmedi | ölçülmedi |
| dolar sayfası | 107.129 B / 18.011 B | ölçülmedi | ölçülmedi | ölçülmedi | ölçülmedi |
| detay 1440 (HD1) | 117.396 B / 25.824 B | 281 (38 alan adı) | 10,39 MB | 292 ms (H1) | 0,013 |
| detay 390 (HD2) | 118.891 B / 24.602 B | 169 | 8,78 MB | 708 ms (H1) | 0 |
| son dakika 1440 | 95.319 B / 17.516 B | 118 | 8,60 MB | 188 ms | 0,009 |

- Aktarılan baytın büyük kısmı üçüncü taraf: detay 1440'ta en çok istek atan alan adları `pagead2.googlesyndication.com` (63), `im.haberturk.com` (26), `s2.adform.net` (23), `www.haberturk.com` (22).
- LCP öğesi detayda **H1 metni**: görsel `data-src` ile tembel yükleniyor.
- Yöntem: HTML baytı için `curl --compressed` (dosya boyu) ve `%{size_download}`; istek, aktarım, LCP ve CLS için başsız Chrome DevTools (`Network.loadingFinished.encodedDataLength` toplamı, 14 sn pencere; `PerformanceObserver`).

## 8. SEO yapısı

- **JSON-LD:** anasayfada `Organization`, `WebSite` + `SearchAction`, `ItemList` (21 `ListItem`). Detayda `NewsArticle` (alanlar: `headline`, `alternativeHeadline`, `articleBody`, `articleSection`, `author: Person`, `dateCreated`, `datePublished`, `dateModified`, `genre: news`, `wordCount`, `inLanguage: tr-TR`, `keywords`, `image`, `publisher`, `mainEntityOfPage`) + `BreadcrumbList`. `isAccessibleForFree`, `speakable`, `LiveBlogPosting` yok ([HD1](https://www.haberturk.com/ekonomi/fon-yasasi-teklifi-bugun-tbmm-genel-kurulu-nda-3920983), 2026-10-20).
- Enstrüman sayfasında yalnız `Organization` + `WebSite`; finansal veri şeması yok ([D](https://www.haberturk.com/ekonomi/piyasa/88-dolar), 2026-10-20).
- **Kanonik:** her sayfada var; anasayfa kanoniği sondaki `/` olmadan.
- **Sitemap:** robots.txt'de 5 sitemap (genel, Google News, video, yeni video, kardeş site Google News). Google News sitemap'i 435 adres; `news:publication_date`, `news:title`, `news:language`, `image:image`, `lastmod` taşıyor ([S](https://www.haberturk.com/sitemap_google_news.xml), 2026-10-20).
- **AMP:** `amphtml` bağlantısı yok.
- `meta robots`: `max-image-preview:large, max-video-preview:-1`.
- robots.txt sonsuz yükleme uçlarını, etiket ve arama sayfalarını, yorum uçlarını bota kapatıyor: tarama bütçesini kanonik haberlere ayırıyor.

## 9. Reklam

Ekran görüntüsü + DOM ölçümü, 2026-10-20, çerez kabul edilmedi.

- **Anasayfa 1440 ilk ekran:** 970×250 masthead + iki yanda **sabit** 160×600 sayfa giydirme (3 yuva) + menüde sponsor logosu + manşet altında tam genişlik sponsor bandı.
- **Detay 1440 ilk ekran:** 970×250 masthead, iki yan giydirme (160×600, sabit), sağ rayda 300×250 → 4–5 yuva. Gövde içi yuva "REKLAM" etiketli ve **önceden yer ayrılmış** (`min-h-80`); CLS 0,013'te kaldı.
- **Mobil:** anasayfa ve detayda ilk ekranda 320×100; anasayfanın tamamında 25 reklam öğesi sayıldı.
- Altyapı: Google Ad Manager (`/31903365/Haberturk/...` yuva adları), Adform, yerel RTB, doğrulama pikseli; HTML'de `zone_auto_refresh_sticky` adlı **kendini yenileyen** yapışkan yuva.
- BH notu: AdSense BH için reddedildi (kullanıcı kararı); burada yalnız yerleşim kaydedildi.

## 10. Gelir ve okur ilişkisi

- **Ödeme duvarı yok:** iki detayın gövdesi açık; JSON-LD'de `isAccessibleForFree` yok.
- **Bülten:** altbilgide e-posta bülteni formu (günün manşetleri + en çok okunanlar, her sabah) ([A](https://www.haberturk.com/), 2026-10-20).
- **Bildirim:** alt çubukta "Bildirimler" sekmesi ve sayılı rozet (ekran görüntüsü). Tarayıcı push izni istendi mi: ölçülmedi.
- **Google tercih edilen kaynak:** detayda bilgi satırının altında `google.com/preferences/source?q=haberturk.com` bağlantılı kutu ([HD1](https://www.haberturk.com/ekonomi/fon-yasasi-teklifi-bugun-tbmm-genel-kurulu-nda-3920983), 2026-10-20). Arama sonuçlarında kaynağı öne çıkarmak için okura tek tıklık çağrı.
- Uygulama indirme çağrısı, favoriler (detay araç çubuğu). Üyelik yolu `/uyelik` var (robots.txt'de kapalı, istenmedi).
- **Yorum:** detay HTML'inde yorum bloğu bulunmadı; `/yorumlar` uçları robots.txt'de kapalı.

## 11. Erişilebilirlik

- `lang="tr"` var (tüm sayfalar).
- **Atla bağlantısı yok:** ilk `#` bağlantılar arasında "içeriğe geç" türü bir bağlantı bulunmadı.
- **Anasayfada H1 yok** (0 adet). Detayda tek H1.
- Görsel alt metni: detayda 41 `<img>`, alt'ı eksik 0, boş alt 1.
- Odak: programatik `focus()` ile detayda ilk bağlantı `outline: solid 2px`; anasayfada ilk bağlantıda `outline: none`. Klavye ile `:focus-visible` davranışı ölçülmedi.
- Spot metni kırmızı (rgb 220,38,38) beyaz zeminde. Kontrast oranı hesaplanmadı.
- Detayda yazı boyutu düğmesi var (araç çubuğu).

## 12. Yapay zekâ kullanımı

İki detay sayfasında yapay zekâ özeti, seslendirme ya da "yapay zekâ ile" etiketi bulunmadı ("dinle", "seslendir", "okuma süresi" yok; "yapay zeka" geçişleri yalnız başka bir haberin başlığında) ([HD1](https://www.haberturk.com/ekonomi/fon-yasasi-teklifi-bugun-tbmm-genel-kurulu-nda-3920983), [HD2](https://www.haberturk.com/gundem/son-dakika-haberi-meteoroloji-den-dogu-karadeniz-icin-yagmur-uyarisi-sicakliklar-mevsim-normali-altinda-20-ekim-hava-durumu-3920978), 2026-10-20). Öneri motoru: ölçülmedi.

## Ölçüm dökümü

| ölçü | değer | yöntem |
|---|---|---|
| anasayfa HTML | 367.066 B açılmış, 57.809 B gzip | `curl --compressed`, `%{size_download}`, 09:32 TSİ |
| ekonomi HTML | 218.711 / 35.004 B | aynı |
| dolar sayfası HTML | 107.129 / 18.011 B | aynı |
| detay HTML (HD1 / HD2) | 117.396 / 25.824 B · 118.891 / 24.602 B | aynı |
| son dakika HTML | 95.319 / 17.516 B | aynı |
| anasayfa 1440: istek / aktarım / alan adı | 196 / 11,75 MB / 28 | Chrome CDP, 14 sn |
| anasayfa 1440: LCP / CLS / load | 292 ms / 0,008 / 1.387 ms | `PerformanceObserver`, Navigation Timing |
| anasayfa 390: istek / aktarım / LCP / CLS | 163 / 8,25 MB / 252 ms / 0 | Chrome CDP, DPR 3 |
| detay 1440: istek / aktarım / LCP / CLS | 281 / 10,39 MB / 292 ms / 0,013 | Chrome CDP |
| detay 390: istek / aktarım / LCP / CLS / TTFB | 169 / 8,78 MB / 708 ms / 0 / 588 ms | Chrome CDP |
| son dakika 1440: istek / LCP / CLS | 118 / 188 ms / 0,009 | Chrome CDP |
| ilk ekran başlık sayısı (1440 / 390) | 11 / 2 | görünür `<a>`, metin ≥ 25 karakter |
| sabit öğe yüksekliği 390 (anasayfa) | 41 + 48 + 56 = 145 px | `getComputedStyle().position` fixed/sticky |
| gövde (1440) | 16/24 px, 514 px ≈ 66 kar./satır | `getComputedStyle`, `canvas.measureText` |
| Google News sitemap | 435 adres | `<loc>` sayımı |
