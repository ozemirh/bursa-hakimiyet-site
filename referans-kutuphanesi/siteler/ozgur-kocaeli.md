# Özgür Kocaeli

- Adres: https://www.ozgurkocaeli.com.tr/
- Katman: yerel (başka şehir — Kocaeli)
- Neden seçildi: basılı günlük gazetesi olan bağımsız bir il gazetesi; Bursa'ya benzer sanayi kenti; Similarweb'in Olay için listelediği benzer sitelerde Bursa dışından çıkan tek yerel gazete ([kaynak](https://www.similarweb.com/website/olay.com.tr/competitors/), Eylül 2026 verisi, 2026-10-20). Servis menüsü (hava, eczane, namaz, trafik, sinema, şehir rehberi) geniş.
- İnceleme: 2026-10-20 · koşul: masaüstü 1440×900 / mobil 390×844 (DPR 3) başsız Chrome, User-Agent değiştirilmedi, çerez ve açılır pencere kabul edilmedi, önbellek kapalı · konum: Türkiye (yerel makine)
- İncelenen sayfalar: robots.txt, anasayfa, bölüm (`/kocaeli-haberleri`), haber detay ×2, nöbetçi eczane, şehir rehberi, haber sitemap'i
- robots.txt (2026-10-20): `*` için `/api/`, `/service/`, `/user/`, `/ara`, `/paylas` vb. kapalı; yapay zekâ ajanlarına özel bölüm yok, başlık yorumu yok → otomatik erişim açık.
- Altyapı gözlemi: statik dosyalar `static.daktilo.com` alanından (hazır haber platformu); bildirim `bildirt.com`.

## Özet — en öğretici 3 çözüm
1. **Google "tercih edilen kaynak" çağrısı** — ilk ziyarette sayfanın üstüne tam ekran pencere; düğme `google.com/preferences/source?q=<alan adı>` adresine gidiyor; "Sonra hatırlat" seçeneği var. Anasayfada ve detayda, iki genişlikte de görüldü ([anasayfa](https://www.ozgurkocaeli.com.tr/), 2026-10-20). Detayda ayrıca Google News "ABONE OL" bağlantısı. Neden: yerel gazete için Google arama ve Haberler en büyük dağıtım kanalı; okurun açık tercihi sıralamada yerel kaynağı öne alıyor. BH'ye: kısmen — tercih bağlantısı/düğmesi taşınır; okumayı kesen tam ekran pencere ayrı bir karar (→ `haber-muduru`, `seo-buyume-uzmani`).
2. **İlçe filtreli eczane + yol tarifi** — tek sayfada ilçe seçici (12 ilçe + "Hepsi"), her eczanede `tel:` bağlantısı ve koordinatlı Google Haritalar "Yol tarifi" ([eczane](https://www.ozgurkocaeli.com.tr/kocaeli-nobetci-eczaneler), 2026-10-20). Neden: gece eczane arayan okurun iki işi (ara, git) tek dokunuş. BH'ye: evet.
3. **Detayda bağlam alanları** — JSON-LD `NewsArticle.contentLocation` = `AdministrativeArea` (il adı) ve `publishingPrinciples` (yayın ilkeleri sayfası); site altbilgisinde "Yayın İlkeleri", "Topluluk Kuralları", "Kuruluş Hakkında" sayfaları ([detay 1](https://www.ozgurkocaeli.com.tr/haber/29013193/kocaelide-104-saglik-yatirimi-tamam-saglik-icin-dev-yatirim-listesi-ortaya-cikti), 2026-10-20). Neden: yerellik ve güvenilirlik sinyali makineye de okura da açık. BH'ye: evet (S emek).

## 1. Anasayfa bilgi mimarisi
1440 px'te üstten: lacivert başlık bandı (sol WhatsApp ihbar hattı, ortada logo, sağda sosyal) → menü (Yazarlar, Gündem, Ekonomi, Siyaset, Asayiş, Perde Arkası, Resmi İlanlar, Kocaelispor, Spor, Menü) → büyük manşet + numaralı manşet seçici → 4'lü kart şeridi ([anasayfa](https://www.ozgurkocaeli.com.tr/), 2026-10-20; yerleşim tam ekran pencerenin arkasındaki bulanık görüntüden okundu). HTML'de mini servis bağlantıları var (hava sıcaklığı, trafik, namaza kalan süre); konumu doğrulanmadı. Manşet tipi: çoklu. İlk ekranda görünür, metni ≥ 25 karakter bağlantı: **13** (DOM ölçüsü, pencere arkasında). Aşağıda: köşe yazarları, "Perde Arkası", video/foto, **birinci sayfa** (basılı gazetenin ön sayfası, arşive bağlantı), nostalji, resmi ilan kaydırıcısı, vefat listesi. Sayfa yüksekliği 7.711 px.

## 2. Bölüm sayfası
`/kocaeli-haberleri`: `CollectionPage` + `BreadcrumbList`; 35 `h3` kart; numaralı sayfalama yerine **bölüm arşivine** bağlantı (`/arsiv/kocaeli-haberleri`) ([bölüm](https://www.ozgurkocaeli.com.tr/kocaeli-haberleri), 2026-10-20). Kademe ve ray: ölçülmedi.

## 3. Haber detay
- Gövde: **23,1 px / 32,2 px** (1,39), Roboto; sütun 970 px, ilk uzun paragrafta **~77 karakter/satır** (alt sınır) ([detay 1](https://www.ozgurkocaeli.com.tr/haber/29013193/kocaelide-104-saglik-yatirimi-tamam-saglik-icin-dev-yatirim-listesi-ortaya-cikti), 2026-10-20, 1440 px). Başlık 54,6 px.
- Muhabir: fotoğraflı yazar satırı başlık bloğunun altında (ekran görüntüsü; ad yazılmadı). JSON-LD `author` = `Person`.
- Okumaya devam: **sonsuz kaydırma** — sayfa sonuna gelinince sıradaki haber aynı sayfaya yükleniyor (betikte "sıradaki haber" mantığı) ([detay 2](https://www.ozgurkocaeli.com.tr/haber/29010758/gebze-6-parselin-imar-plani-degisti-planlar-askiya-cikti), 2026-10-20). Davranış tarayıcıda kaydırılarak doğrulanmadı.
- Yorum: var; formun yanında topluluk kuralları ve ajans haberlerinin hukuki muhatabına dair uyarı metni.
- Video oynatıcı (video.js + Google IMA reklam SDK'sı) detayda yüklü.
- Düzeltme notu: görülmedi. Bu örnekte `dateModified` = `datePublished`.

## 4. Son dakika / canlı
`/son-dakika` sayfası menüde ([anasayfa](https://www.ozgurkocaeli.com.tr/), 2026-10-20). Anasayfadaki biçimi: ölçülmedi (pencere arkasında). Canlı blog: görülmedi.

## 5. Yerel ve servis içerikleri
- Servis menüsü: hava durumu, nöbetçi eczane, namaz vakti, **trafik durumu**, **sinemalar**, **şehir rehberi** (81 kategori: eczane, doktor, avukat, benzin istasyonu, ATM … — [rehber](https://www.ozgurkocaeli.com.tr/rehber), 2026-10-20), seri ilanlar, gazete manşetleri, Süper Lig fikstürü, resmi ilanlar.
- Vefatlar sayfası ve anasayfada vefat listesi var — **BH için: reddedildi (kullanıcı kararı).**
- İlçe sayfası: menüde görülmedi; ilçe kırılımı yalnız eczane filtresinde.
- Haber ihbar sayfası (`/haber-ihbar`) ve WhatsApp ihbar hattı başlıkta ilk odak öğesi.
- Yerel/ulusal denge: menünün tamamına yakını il adlı kategori (`kocaeli-ekonomi-haberleri`, `kocaeli-siyaset-haberleri` …); ulusal içerik "Güncel", "Dünya" altında.

## 6. Mobil davranış
390 px: başlık `position: fixed` (85 px); alt kenarda yapışkan veri politikası şeridi (135 px); ilk ziyarette tam ekran Google kaynak tercihi penceresi içeriği kapatıyor ([anasayfa 390](https://www.ozgurkocaeli.com.tr/), 2026-10-20). Pencere kapalıyken ilk ekran: ölçülmedi (etkileşim yapılmadı). Ölçütün saydığı başlık: 9. Sayfa yüksekliği 18.215 px; yatay taşma yok.

## 7. Başarım
Tek ölçüm, 2026-10-20, Türkiye, başsız Chrome, çerez/pencere kabul edilmedi.
| sayfa | istek | aktarım | LCP | CLS |
|---|---|---|---|---|
| anasayfa 1440 | 71 | 1,92 MB | 1.052 ms (IMG) | 0,020 |
| anasayfa 390 | 69 | 1,89 MB | 1.028 ms | 0,000 |
| detay 1440 | 100 | 2,18 MB | 1.256 ms | 0,016 |

Anasayfa HTML 45.530 B sıkıştırılmış / 288.215 B açılmış. Anasayfada 289 `img`; HTML'de `loading="lazy"` yok (gecikmeli yükleme betikle yapılıyor olabilir — doğrulanmadı).

## 8. SEO yapısı
- Detay JSON-LD: `NewsArticle` (`contentLocation`, `publishingPrinciples`, `wordCount`, `dateModified`, `image` dizisi), `BreadcrumbList`, `WebPage`, `NewsMediaOrganization` ×2 ([detay 1](https://www.ozgurkocaeli.com.tr/haber/29013193/kocaelide-104-saglik-yatirimi-tamam-saglik-icin-dev-yatirim-listesi-ortaya-cikti), 2026-10-20).
- Adres deseni: `/haber/<sayısal kimlik>/<slug>` (BH'deki `/{kategori}/{slug}-{id}` ile aynı fikir: kimlik adreste).
- Haber sitemap'i `google-news.xml`: 165 adres, **48 saatlik pencere** (2026-10-18 09:51 → 2026-10-20 09:38) ([google-news.xml](https://www.ozgurkocaeli.com.tr/google-news.xml), 2026-10-20); ayrıca `sitemap.xml`, `sitemap-latest.xml`.
- AMP: var (`/amp/haber/…`).

## 9. Reklam
Reklam seçicisine uyan görünür öğe: 0 (iki genişlikte); reklamlar betikle kanal bazlı yükleniyor (`/service/advertchannels`, robots'ta kapalı — istek atılmadı). Ekran görüntüsü pencere arkasında kaldığı için ilk ekran yuva sayısı: **ölçülmedi**. Resmi ilan kaydırıcısı (ilan.gov.tr ilanları, 18 bağlantı) anasayfada ([anasayfa](https://www.ozgurkocaeli.com.tr/), 2026-10-20).

## 10. Gelir ve okur ilişkisi
Ödeme duvarı görülmedi. Basılı gazete **abonelik** sayfası ve banka hesapları sayfası; üye girişi; tarayıcı bildirimi (Bildirt, manifest bağlantılı); yorumlar + topluluk kuralları; Google News takip ve Google kaynak tercihi çağrıları. Basın İlan Kurumu analitik toplayıcısına ve `medya.ilan.gov.tr`'ye istek görüldü.

## 11. Erişilebilirlik
`lang="tr"`. "İçeriğe atla" bağlantısı ölçütle bulunamadı (HTML'de "skip" sözcüğü 1 kez geçiyor; işlevi doğrulanmadı). İlk odak WhatsApp ihbar bağlantısı. Anasayfada 289 `img`'nin 12'sinde `alt` eksik, hiçbirinde `width/height` yok. Odak görünürlüğü, kontrast: ölçülmedi.

## 12. Yapay zekâ kullanımı
Görülmedi (incelenen 7 sayfa).

## Ölçüm dökümü
| ölçü | değer | yöntem |
|---|---|---|
| anasayfa HTML | 45.530 B / 288.215 B | `curl --compressed -w %{size_download}` / disk |
| detay HTML | 36.766 B / 160.560 B | aynı |
| ilk ekran başlık | 13 (1440) · 9 (390) | CDP: görünür, metni ≥ 25 karakter `a` (pencere arkasındakiler dahil) |
| LCP / CLS / istek / aktarım | tablo §7 | `PerformanceObserver`; CDP Network olayları |
| gövde tipografisi | 23,1/32,2 px, 970 px, ~77 kar/satır | `getComputedStyle` + `Range.getClientRects` |
| eczane ilçe filtresi | 14 `option` (yer tutucu + Hepsi + 12 ilçe) | ham HTML |
| şehir rehberi | 81 kategori adresi | `/rehber/<slug>` benzersiz sayım |
| istek sayısı (bu site) | 11 | robots, anasayfa, bölüm, 2 detay, eczane, rehber, google-news.xml (`curl`) + 3 Chrome yüklemesi |
