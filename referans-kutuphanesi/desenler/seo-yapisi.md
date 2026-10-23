# SEO yapısı — siteler arası desenler

Son güncelleme: 2026-10-20 (sentez) · Kaynak siteler: Bursada Bugün, Bursa
Saati, Ege'de Son Söz, Özgür Kocaeli, Habertürk, Spiegel (doğrudan: JSON-LD
ayrıştırma, sitemap `<loc>` sayımı); NTV, Hürriyet, Milliyet, MEN, Texas
Tribune, Axios (yalnız robots.txt okundu — doğrudan); BBC (ikincil).

## 1. Haber detay JSON-LD

| Site | K. | Türler ve dikkat çeken alanlar | Kaynak |
|---|---|---|---|
| Bursada Bugün | D | `NewsArticle` (`articleBody`, `dateModified`, `wordCount`, `isAccessibleForFree`, **`publishingPrinciples`**, `author` Person) + `BreadcrumbList`, `WebPage`, `NewsMediaOrganization` | `bursada-bugun.md` §8 · [detay 2](https://www.bursadabugun.com/haber/turkiye-nin-sanayi-devleri-belli-oldu-bursa-dan-bir-sirket-ilk-5-te-1957588.html), 2026-10-20 |
| Özgür Kocaeli | D | `NewsArticle` (**`contentLocation` = `AdministrativeArea`**, **`publishingPrinciples`**, `wordCount`, `image` dizisi) + `BreadcrumbList`, `WebPage`, `NewsMediaOrganization` | `ozgur-kocaeli.md` Özet 3, §8 · [detay 1](https://www.ozgurkocaeli.com.tr/haber/29013193/kocaelide-104-saglik-yatirimi-tamam-saglik-icin-dev-yatirim-listesi-ortaya-cikti), 2026-10-20 |
| Bursa Saati · Ege | D | `NewsArticle` (`keywords`, `wordCount`, `author`/`creator`/`editor`) + `BreadcrumbList`, `WebPage`; her sayfada 268 / 62 `SiteNavigationElement` (HTML'i şişiriyor) | `bursa-saati.md` §8, `egede-son-soz.md` §8 |
| Habertürk | D | `NewsArticle` (**`alternativeHeadline`** = H1, `headline` SEO önekli, `genre`, `wordCount`, `keywords`) + `BreadcrumbList`; anasayfada `ItemList` (21). `isAccessibleForFree`, `LiveBlogPosting` yok; enstrüman sayfasında finansal şema yok | `haberturk.md` §8 |
| Spiegel | D | `NewsArticle` (`isAccessibleForFree` ücretsiz haberde `true`; ajans haberinde `author` kurum) + `ImageObject`, `BreadcrumbList`; bölümde `WebPage` | `spiegel.md` §8 |
| Eczane sayfaları | D | Bursa Saati `Pharmacy` ×32, Ege ×71; Bursada Bugün `Service` + `City` | `yerel-servis.md` |
| Bölüm sayfası | D | Bursada Bugün ve Özgür Kocaeli `CollectionPage` + `BreadcrumbList` | `bolum-sayfasi.md` |

## 2. Sitemap, AMP, robots

| Konu | Görülen | Kaynak |
|---|---|---|
| Haber sitemap'i 48 saat | Bursada Bugün 505 adres (48 sa), Özgür Kocaeli 165 (48 sa), Habertürk 435 | D · [news.xml](https://www.bursadabugun.com/sitemap/news.xml), [google-news.xml](https://www.ozgurkocaeli.com.tr/google-news.xml), [Habertürk](https://www.haberturk.com/sitemap_google_news.xml), 2026-10-20 |
| Aylık arşiv sitemap'i | Bursa Saati 25, Ege 32 alt harita (`sitemap-YYYY-MM.xml`) | D · [sitemap](https://www.bursasaati.com.tr/sitemap.xml), [sitemap](https://www.egedesonsoz.com/sitemap.xml) |
| Ayrı haber sitemap'i robots'ta | NTV, Spiegel (+ video, ücretli içerik), MEN, Texas Tribune | D (robots.txt) · ilgili dosyalar §8 |
| Konuya özel sitemap | Sözcü turnuva sitemap'i (2026-10-19 kopyası, doğrulanmadı) | E · `sozcu.md` Özet 2 |
| AMP | Var: Bursada Bugün (`m.`), Özgür Kocaeli (`/amp/`); yok: Habertürk, Spiegel, Bursa Saati, Ege | D · ilgili §8 |
| robots ile tarama bütçesi | Habertürk sonsuz yükleme, etiket, arama, yorum uçlarını kapatıyor; NTV `/api/next-news`; MEN `/topics` | D · `haberturk.md` §8, `ntv.md` §8, `manchester-evening-news.md` §2 |
| `meta robots` | `max-image-preview:large` (Habertürk, Spiegel) | D |
| Google "tercih edilen kaynak" çağrısı | Habertürk, Spiegel, Özgür Kocaeli | D · `haber-detay.md` §2 |
| YZ tarayıcılarına tutum | Hürriyet/NTV/Milliyet 10 botu tümden kapatıyor; Olay `Content-Signal: ai-train=no`; Sözcü `llms.txt` ile yönlendiriyor (eski kopya); Spiegel `Claude-User`'a deneme açılımı | D (robots.txt) · ilgili dosyalar |

**Ortak ders.** Yerel Türk siteleri `NewsArticle` + `BreadcrumbList` + 48
saatlik haber sitemap'inde birleşiyor. Fark yaratan alanlar küçük:
`publishingPrinciples` (yayın ilkeleri sayfası), `contentLocation` (yer),
`CollectionPage` (bölüm). `SiteNavigationElement`'i her sayfaya basmak HTML'i
şişiriyor; anti-desen.

**Hangi koşulda.** `publishingPrinciples` gerçek bir yayın ilkeleri sayfası
gerektirir; boş sayfaya işaret eden alan güven sinyali değildir.

**Bursa Hakimiyet'te durum** (Paket G, URUN-PLANI §70).
- `icerik/seo.py`: `NewsArticle` (`headline`, `isAccessibleForFree`,
  `datePublished`/`dateModified`, `author` muhabir varsa Person yoksa
  kurum, `articleSection`, 4 kırpımlı `image`), `BreadcrumbList`,
  `NewsMediaOrganization`, `WebSite` + `SearchAction`, `OpinionNewsArticle`,
  `ProfilePage`, `ImageGallery`. Eczanede `Pharmacy` (`icerik/eczane.py`).
- `taban.html`: meta/OG/Twitter, `max-image-preview:large`, kanonik
  `SITE_KOKU`'dan; ayrı `seo_baslik` alanı (Habertürk'ün başlık ayrımıyla aynı fikir).
- `besleme/siteharitasi.py`: `googleNews.xml` **son 48 saat**, beş ailenin
  aylık dosyaları; RSS genel + bölüm. `/amp/*` → 301. robots: `/ara`,
  `/panel/`, `/yonetim/`, `/daha-fazla` kapalı (`besleme/gorunumler.py`).
- **Eksik:** `publishingPrinciples` (yayın ilkeleri sayfası yok; menü
  bağlantısı `href="#"`), `contentLocation` (haberin ilçesi var, şemaya
  girmiyor), bölümde `CollectionPage`; haber JSON-LD kırıntısında ilçe yok
  (`seo.py` `haber_kirintisi` 3 öğe) ama görünen kırıntıda var
  (`haber_detay.html:23`); Google tercih edilen kaynak bağlantısı yok; robots'ta
  YZ tarayıcılarına kural yok.

**Öneri.**
- Yayın ilkeleri sayfası + `publishingPrinciples` → P1 · S · → `haber-muduru`
  (metin, gazeteden — yeni içerik eşiği) + `seo-buyume-uzmani`.
- `contentLocation` = haberin ilçesi (`AdministrativeArea`) ve JSON-LD
  kırıntısına ilçe → P1 · S · → `seo-buyume-uzmani`.
- Haber detayında Google "tercih edilen kaynak" bağlantısı (künye altında,
  tam ekran pencere değil) → P1 · S · → `seo-buyume-uzmani` + `haber-muduru`.
- Bölüm sayfasında `CollectionPage` → P2 · S · → `seo-buyume-uzmani`.
- YZ tarayıcılarına robots tutumu (açık / kapalı / içerik sinyali) bir karar
  → P2 · S · → `seo-buyume-uzmani` + `hukuk-guvenlik-uyum-uzmani`, kararı kullanıcı verir.
- Etiket sayfası / etiket sitemap'i → **BH için: reddedildi (kullanıcı kararı).**
