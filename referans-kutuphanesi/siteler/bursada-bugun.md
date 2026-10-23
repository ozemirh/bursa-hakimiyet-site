# Bursada Bugün

- Adres: https://www.bursadabugun.com/
- Katman: yerel
- Neden seçildi: Bursa'da dijital ağırlıklı rakip; aynı okur (SITELER.md).
- İnceleme: 2026-10-20 · koşul: masaüstü 1440×900 / mobil 390×844 (DPR 3) başsız Chrome, User-Agent değiştirilmedi, çerez bandı kabul edilmedi, önbellek kapalı · konum: Türkiye (yerel makine)
- İncelenen sayfalar: robots.txt, anasayfa, bölüm (`/bursa-bolge-haberleri`), ilçe (`/bursa-inegol-haberleri`), haber detay ×2, nöbetçi eczane, haber sitemap'i
- robots.txt (2026-10-20): `*` için yalnız `/arama/`, `/galeri/arama/`, `/video/arama/` kapalı; `Claude-User`/`ClaudeBot`/`anthropic-ai` bölümü yok, başlık yorumunda koşul yok → otomatik erişim açık.
- Rakip notu: aşağıdaki tüm ölçüler **tek ölçüm, 2026-10-20, Türkiye**; sıralama ve puan yoktur.

## Özet — en öğretici 3 çözüm
1. **İlçe sayfaları menünün içinde** — "Bursa Bölge" açılır menüsü 17 ilçe + Uludağ sayfasına gidiyor ([anasayfa](https://www.bursadabugun.com/), 2026-10-20). Neden işe yarıyor: ilçe okuru kendi adını menüde görüyor, ilçe adı aramalarına kalıcı bir açılış sayfası oluyor. BH'ye taşınabilir mi: kısmen — sayfanın kendisi kolay, ama İnegöl sayfasındaki tarih aralığı (aşağıda §5) ilçe sayfasının masa beslemesi olmadan bayatladığını gösteriyor.
2. **Detayda tek satırlık künye** — yayın zamanı, "son güncellenme" zamanı, bölüm ve ajans adı aynı satırda ([detay](https://www.bursadabugun.com/haber/bursa-hayvanat-bahcesi-nde-dev-karincayiyenin-ozel-menusu-40-dakikada-hazirlaniyor-1957734.html), 2026-10-20). Neden: okur haberin tazeliğini ve kaynağını başlığın hemen altında görüyor. BH'ye: evet (kaynak bölmesi kararıyla çelişmez; yalnız güncelleme zamanı eklenir).
3. **Eczane sayfası tek amaçlı ve hafif** — her eczanede telefon + "Haritada göster" (Google Haritalar arama bağlantısı), JSON-LD `Service` + `City` ([eczane](https://www.bursadabugun.com/bursa-nobetci-eczaneler), 2026-10-20). HTML 7.512 bayt sıkıştırılmış. BH'ye: evet.

## 1. Anasayfa bilgi mimarisi
Üstten: logo + piyasa bandı (dolar, euro, altın, BIST, bitcoin) + hava → menü (Bursa Bölge açılır, Spor, Ekonomi, Magazin, Radyo, Video, Galeri, Yazarlar, Resmi İlanlar) → "Son dakika" tek satır kayan şerit + "Tümünü göster" → numaralı (18 öğe) manşet slaytı + sağda ikinci slayt → tam genişlik reklam → 3'lü kart ızgarası ([anasayfa](https://www.bursadabugun.com/), 2026-10-20). Manşet tipi: çoklu (numaralı slayt). İlk ekranda görünür, metni ≥ 25 karakter bağlantı: **11** (1440 px; yöntem aşağıda). Sayfa yüksekliği 11.339 px.

## 2. Bölüm sayfası
`/bursa-bolge-haberleri`: JSON-LD `CollectionPage` + `BreadcrumbList`; numaralı sayfalama (`/bursa-bolge-haberleri/2.html` … `/7.html` bağlantıları HTML'de) ([bölüm](https://www.bursadabugun.com/bursa-bolge-haberleri), 2026-10-20). Kademe (manşet → orta → akış) ve ray: ölçülmedi (yalnız ham HTML okundu, ekran görüntüsü alınmadı).

## 3. Haber detay
- Gövde: 20 px / satır aralığı 30 px (1,5), Inter; gövde sütunu 970 px, ilk uzun paragrafta ortalama **~84 karakter/satır** (son satır kısmi olduğundan alt sınır) ([detay 1](https://www.bursadabugun.com/haber/bursa-hayvanat-bahcesi-nde-dev-karincayiyenin-ozel-menusu-40-dakikada-hazirlaniyor-1957734.html), 2026-10-20, 1440 px). Başlık 40 px.
- Spot: var (başlığın altında, gövdeden büyük punto; ekran görüntüsü).
- Künye satırı: yayın zamanı · "Son Güncellenme" zamanı · bölüm · ajans kısaltması (bu örnekte İHA). JSON-LD `dateModified` ayrı alan.
- Paylaşım: Facebook, X, WhatsApp, e-posta + "Google News — Abone ol" düğmesi; yazdır ve punto büyüt/küçült denetimleri.
- İlgili haber / okumaya devam: ölçülmedi.
- Düzeltme notu: görülmedi.

## 4. Son dakika / canlı
Anasayfada menünün altında tek satır "SON DAKİKA" şeridi, sağda "Tümünü göster" → `/son-dakika-haberleri` ([anasayfa](https://www.bursadabugun.com/), 2026-10-20). Canlı blog: görülmedi. Göreli zaman ("x dk önce"): ölçülmedi.

## 5. Yerel ve servis içerikleri
- **İlçe sayfaları:** 17 ilçe + Uludağ, adres deseni `/bursa-<ilçe>-haberleri`. İnegöl sayfasında 55 benzersiz haber/video bağlantısı; 29'unun adresinde ilçe adı geçiyor; sayfadaki ISO tarihler **2026-01-26 ile 2026-10-19** arasında ([İnegöl](https://www.bursadabugun.com/bursa-inegol-haberleri), 2026-10-20). Yani sayfa ~9 aylık bir pencereyi gösteriyor; ilçeye özgü akış seyrek.
- **Nöbetçi eczane:** il geneli tek sayfa, ilçe adı her kayıtta; telefon + harita bağlantısı ([eczane](https://www.bursadabugun.com/bursa-nobetci-eczaneler), 2026-10-20).
- **Hava:** başlıkta Bursa sıcaklığı → `/bursa-hava-durumu`.
- Anasayfada servis haberi olarak ilçe ilçe elektrik kesintisi galerileri görüldü (galeri biçiminde; [anasayfa](https://www.bursadabugun.com/), 2026-10-20).
- Namaz, trafik, ulaşım sayfası: menüde görülmedi.

## 6. Mobil davranış
**Ölçülmedi.** Masaüstü HTML'inde `viewport` meta etiketi yok; 390 px öykünmede sayfa masaüstü düzeniyle ölçeklenip çizildi (sayfa yüksekliği ve reklam konumları 1440 ile aynı). Detay sayfası AMP sürümünü `m.bursadabugun.com` alt alanına bağlıyor (`amphtml`). Sitenin mobil tarayıcıya ayrı sürüm verip vermediği User-Agent değiştirilmeden görülemez (kimlik gizleme yasağı).

## 7. Başarım
Tek ölçüm, 2026-10-20, Türkiye, başsız Chrome, çerez kabul edilmedi.
| sayfa | istek | aktarım | LCP | CLS |
|---|---|---|---|---|
| anasayfa 1440 | 281 | 8,26 MB | 832 ms (IMG) | 0,230 |
| anasayfa 390 (masaüstü düzeni) | 279 | 8,05 MB | 872 ms | 0,201 |
| detay 1440 | 104 | 1,87 MB | 952 ms | 0,201 |

Anasayfa isteklerinin 159'u görsel alanına (`images.`), 23'ü sitenin kendi reklam alanına (`adn.`) gidiyor. Anasayfa HTML: 30.137 bayt sıkıştırılmış / 215.501 bayt açılmış.

## 8. SEO yapısı
- Detay JSON-LD: `NewsArticle` (`articleBody`, `dateModified`, `wordCount`, `isAccessibleForFree`, `publishingPrinciples`, `author`=`Person`), `BreadcrumbList`, `WebPage`, `NewsMediaOrganization` ([detay 2](https://www.bursadabugun.com/haber/turkiye-nin-sanayi-devleri-belli-oldu-bursa-dan-bir-sirket-ilk-5-te-1957588.html), 2026-10-20).
- Anasayfa: `WebSite` + `SearchAction`, `NewsMediaOrganization`. Kanonik anasayfada şemasız (`//www…`).
- Sitemap: robots.txt'te üç dosya; haber sitemap'i (`/sitemap/news.xml`) 505 adres, `news:news` etiketli, **48 saatlik pencere** (2026-10-18 09:42 → 2026-10-20 09:40) ([news.xml](https://www.bursadabugun.com/sitemap/news.xml), 2026-10-20).
- AMP: var (`m.` alt alanında).

## 9. Reklam
1440 px ilk ekranda **4 yuva** (ekran görüntüsünden sayıldı: sol ve sağ dikey pano, sağ sütunda 300×250, manşet altında 970×90). Sayfada reklam seçicisine uyan 9 öğe. Reklamların bir kısmı yerel kurum ilanı (görsel içerik; ad yazılmadı). Ağlar: sitenin kendi reklam sunucusu (`adn.`), `turkadscdn.com`, Google reklam alanları (`pagead2.googlesyndication.com`, `doubleclick`) — **BH için AdSense: reddedildi (kullanıcı kararı).** Yapışkan reklam: görülmedi (tek yapışkan öğe çerez bandı).

## 10. Gelir ve okur ilişkisi
Ödeme duvarı yok (`isAccessibleForFree` = True). E-bülten sayfası (`/bulten.html`), WhatsApp haber hattı, Radyo, Resmi İlanlar sayfası ve `medya.ilan.gov.tr` çerçevesi; Basın İlan Kurumu analitik toplayıcısına (`analitik.bik.gov.tr`) istek görüldü ([anasayfa](https://www.bursadabugun.com/), 2026-10-20). Tarayıcı bildirimi isteği: görülmedi. Yorum: ölçülmedi.

## 11. Erişilebilirlik
`lang="tr"`. "İçeriğe atla" bağlantısı bulunamadı; ilk odaklanan öğe metinsiz logo bağlantısı. Anasayfada 182 `img`'nin 181'inde `alt` yok ya da boş; detayda 16'nın 14'ünde. Görsellerde `width/height` 182'nin 17'sinde (CLS'nin bir nedeni olabilir — doğrulanmadı). Odak görünürlüğü ve kontrast: ölçülmedi.

## 12. Yapay zekâ kullanımı
Görülmedi (özet, seslendirme, öneri işareti yok; incelenen 6 sayfa).

## Ölçüm dökümü
| ölçü | değer | yöntem |
|---|---|---|
| anasayfa HTML | 30.137 B (sıkıştırılmış) / 215.501 B | `curl --compressed -w %{size_download}` / diskteki dosya |
| detay HTML | 12.473 B / 59.104 B | aynı |
| ilk ekran başlık (1440) | 11 | CDP `Runtime.evaluate`: görünüm alanında, metni ≥ 25 karakter `a` sayısı |
| LCP / CLS | yukarıdaki tablo | `PerformanceObserver` (`largest-contentful-paint`, `layout-shift`), yüklemeden ~8 sn sonra okundu, kaydırma yok |
| istek / aktarım | yukarıdaki tablo | CDP `Network.requestWillBeSent` sayısı / `loadingFinished.encodedDataLength` toplamı |
| gövde tipografisi | 20/30 px, 970 px, ~84 kar/satır | `getComputedStyle` + `Range.getClientRects` satır sayısı |
| istek sayısı (bu site) | 11 | robots, anasayfa, bölüm, ilçe, 2 detay, eczane, news.xml (`curl`) + 3 Chrome sayfa yüklemesi |
