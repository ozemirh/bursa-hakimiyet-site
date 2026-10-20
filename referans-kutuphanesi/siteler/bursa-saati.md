# Bursa Saati

- Adres: https://www.bursasaati.com.tr/
- Katman: yerel
- Neden seçildi: Bursa'dan üçüncü rakip. Similarweb'in Olay ve Bursada Bugün için listelediği "benzer siteler"de (Eylül 2026 verisi, [kaynak](https://www.similarweb.com/website/bursadabugun.com/competitors/), 2026-10-20) çıkan Bursa genel haber siteleri arasından seçildi (taraftar sitesi ve BH hariç). Trafik rakamı bu dosyaya yazılmaz.
- İnceleme: 2026-10-20 · koşul: masaüstü 1440×900 / mobil 390×844 (DPR 3) başsız Chrome, User-Agent değiştirilmedi, çerez ve bildirim istemi kabul edilmedi, önbellek kapalı · konum: Türkiye (yerel makine)
- İncelenen sayfalar: robots.txt, anasayfa, bölüm (`/bursa`), haber detay ×2, nöbetçi eczane, trafik durumu, sitemap dizini
- robots.txt (2026-10-20): `GPTBot`, `ClaudeBot`, `CCBot` vb. satırları `User-agent: *` ile **aynı grupta** ve grupta `Disallow: /` yok; yalnız `/service/`, `/api`, `/arama/`, `/member/` gibi yollar kapalı. `Claude-User`/`anthropic-ai` ayrı bölümü yok → otomatik erişim açık (kapalı yollara istek atılmadı).
- Altyapı gözlemi: statik dosyalar `s.tblsm.com`, görseller `*.teimg.com`, gazete manşeti görselleri `statictebilisim.teimg.com` alanından geliyor; robots.txt Ege'de Son Söz ve Bursa TV ile birebir aynı ([egedesonsoz.com/robots.txt](https://www.egedesonsoz.com/robots.txt), [bursatv.com.tr/robots.txt](https://www.bursatv.com.tr/robots.txt), 2026-10-20). Yani üçü aynı hazır haber platformunu kullanıyor; servis modülleri pakette geliyor.
- Rakip notu: tüm ölçüler **tek ölçüm, 2026-10-20, Türkiye**; sıralama ve puan yoktur.

## Özet — en öğretici 3 çözüm
1. **İlçe kırılımlı nöbetçi eczane + yapısal veri** — il sayfası ve ilçe başına ayrı adres (`/bursa-<ilçe>-nobetci-eczaneler`, 18 adres), her eczane JSON-LD `Pharmacy` (32 kayıt) ([eczane](https://www.bursasaati.com.tr/bursa-nobetci-eczaneler), 2026-10-20). Neden: "Nilüfer nöbetçi eczane" gibi aramaların her birine ayrı açılış sayfası. BH'ye: evet; ilçe adresleri BH ilçe sayfasıyla bağlanabilir.
2. **Tarihli günlük servis haberleri** — namaz vakitleri, döviz ve altın için her gün tarihli ayrı haber adresi (ör. [namaz vakitleri haberi](https://www.bursasaati.com.tr/bursada-ezan-saat-kacta-okunacak-iste-20-ekim-2026-sali-namaz-vakitleri-1), anasayfadan bağlantı, 2026-10-20). Neden: arama trafiği için. BH için dikkat: periyodik türler konu sayılmaz (kullanıcı kararı); bu desen konu takibine değil yalnız servis sayfasına ilişkin.
3. **Sponsorlu içerik menüde ayrı kategori** — "Advertorial" ve "Resmi Reklam" ana menüde kategori olarak duruyor ([anasayfa](https://www.bursasaati.com.tr/), 2026-10-20). Neden: ücretli içerik haber akışından ayrışıyor ve etiketleniyor. BH'ye: kısmen (etiketleme ilkesi taşınır; adlandırma ve yerleşim `haber-muduru` kararı).

## 1. Anasayfa bilgi mimarisi
1440 px'te üstten: tam genişlik reklam → logo + piyasa + şehir seçmeli hava → siyah menü (Bursa, Genel, Politika, Ekonomi, Bursaspor, Dünya, Magazin, Advertorial, Resmi Reklam, Künye) → ikinci tam genişlik reklam → boş ayrılmış alan (~140 px) → kırmızı "Son dakika" şeridi (saatli, oklu) → koyu piyasa bandı → büyük manşet + yan haber ([anasayfa](https://www.bursasaati.com.tr/), 2026-10-20; ekran görüntüsü). Manşet tipi: slaytlı çoklu manşet ("Tüm manşetler" sayfası var). İlk ekranda görünür, metni ≥ 25 karakter bağlantı: **6**. Sayfa yüksekliği 9.227 px. Aşağıda: yazarlar (fotoğraflı), video, foto galeri, Süper Lig puan durumu, kategori sekmeleri, ulusal gazete manşetleri.

## 2. Bölüm sayfası
`/bursa`: `BreadcrumbList`; 59 `h4` kart başlığı; sayfalama yerine **"Daha fazla göster"** düğmesi (JSON uç noktası `/service/…`, robots'ta kapalı — istek atılmadı) ([bölüm](https://www.bursasaati.com.tr/bursa), 2026-10-20). Kademe ve ray: ölçülmedi.

## 3. Haber detay
- Gövde: 20 px / 30 px (1,5), Gibson; sütun 685 px, ilk uzun paragrafta **~77 karakter/satır** (alt sınır) ([detay 1](https://www.bursasaati.com.tr/bursada-dev-karincayiyenin-ozel-menusu-dana-yureginden-muza-kadar-her-sey-var), 2026-10-20, 1440 px). Başlık 40 px; başlığın üst kenarı 573 px'te (üstte iki reklam + boş alan).
- Spot: var, büyük punto. Künye şeridi: yayın tarihi-saati · **okuma süresi** ("1 DK") · paylaşım (Facebook, X, WhatsApp, +) · punto A−/A+.
- Kaynak: gövde sonunda "Kaynak: <ajans>" satırı. JSON-LD'de `author`, `creator`, `editor` ayrı alanlar.
- İlgili: "Bunlar da ilginizi çekebilir" bloğu ([detay 2](https://www.bursasaati.com.tr/satsuma-sezonu-baslarken-ihracatta-iki-kritik-sorun), 2026-10-20).
- Düzeltme notu: görülmedi. Bu örnekte `dateModified` = `datePublished`.

## 4. Son dakika / canlı
Anasayfada kırmızı şerit, her öğede saat damgası ("09:00 | …"), oklarla gezilir; ayrıca `/sondakika-haberleri` sayfası ([anasayfa](https://www.bursasaati.com.tr/), 2026-10-20). Canlı blog: görülmedi. Göreli zaman: ölçülmedi.

## 5. Yerel ve servis içerikleri
- Nöbetçi eczane: il sayfası + 18 ilçe adresi, `Pharmacy` JSON-LD, sayfa başlığında tarih ([eczane](https://www.bursasaati.com.tr/bursa-nobetci-eczaneler), 2026-10-20).
- Trafik: harita sağlayıcısının trafik katmanını gösteren sayfa (Yandex Haritalar trafik denetimi betikte) ([trafik](https://www.bursasaati.com.tr/bursa-trafik-durumu), 2026-10-20).
- Namaz vakitleri sayfası; hava durumu (Bursa + 81 il için ayrı adres — platformun genel modülü); Süper Lig puan durumu ve fikstür.
- İlçe sayfası: menüde görülmedi.
- Yerel/ulusal denge: menüde yerel kategori tek ("Bursa"); kalan kategoriler genel. Oran ölçülmedi.

## 6. Mobil davranış
390 px ilk ekran (ekran görüntüsü): **tarayıcı bildirimi istemi** (OneSignal, 178 px) üstte → yatay kayan menü → **~270 px boş ayrılmış reklam alanı** → son dakika şeridi → piyasa bandı → manşet görseli ekranın altında başlıyor; ilk ekranda okunabilir haber başlığı yalnız son dakika şeridindeki ([anasayfa 390](https://www.bursasaati.com.tr/), 2026-10-20). Ölçütün saydığı bağlantı: 6. Yapışkan: çerez bandı (alt, 105 px). Sayfa yüksekliği 21.061 px. Yatay taşma yok.

## 7. Başarım
Tek ölçüm, 2026-10-20, Türkiye, başsız Chrome, çerez/bildirim kabul edilmedi.
| sayfa | istek | aktarım | LCP | CLS |
|---|---|---|---|---|
| anasayfa 1440 | 101 | 3,15 MB | 944 ms (IMG) | 0,007 |
| anasayfa 390 | 89 | 3,02 MB | 860 ms | 0,000 |
| detay 1440 | 70 | 2,54 MB | 1.296 ms | 0,008 |

Anasayfa HTML 40.212 B sıkıştırılmış / 272.489 B açılmış; HTML'in büyük kısmı her sayfada tekrarlanan 268 `SiteNavigationElement` JSON-LD kaydı ve 81 ilin hava bağlantıları. Anasayfada 17 istek spor API'sinin görsel alanına (`media.api-sports.io`) gidiyor (puan tablosu logoları). Boş ayrılmış reklam alanı CLS'yi düşük tutuyor (alan önceden rezerve).

## 8. SEO yapısı
- Detay JSON-LD: `NewsArticle` (`articleBody`, `keywords`, `wordCount`, `isAccessibleForFree`, `author`/`creator`/`editor`), `BreadcrumbList`, `WebPage`, `Organization`; her sayfada 268 `SiteNavigationElement` ([detay 1](https://www.bursasaati.com.tr/bursada-dev-karincayiyenin-ozel-menusu-dana-yureginden-muza-kadar-her-sey-var), 2026-10-20).
- Sitemap: dizinde 25 alt harita — `sitemap-news.xml` + **aylık** `sitemap/sitemap-YYYY-MM.xml` ([sitemap.xml](https://www.bursasaati.com.tr/sitemap.xml), 2026-10-20). Haber sitemap'inin içi açılmadı.
- AMP: `amphtml` bağlantısı görülmedi. Kanonik: var, şemalı.

## 9. Reklam
1440 px ilk ekranda **3 yuva + 1 boş ayrılmış alan** (ekran görüntüsü: üst tam genişlik, menü altı tam genişlik, sağda `position: fixed` 160×600 dikey pano). 390 px'te ilk ekranda boş ayrılmış alan. Detayda aynı iki üst yuva + sabit sağ pano. Ağ: `turkadscdn.com`; yerel kurum görselleri. Sponsorlu içerik "Advertorial" kategorisinde.

## 10. Gelir ve okur ilişkisi
Ödeme duvarı yok. İlk ziyarette OneSignal bildirim istemi ("Abone Ol / Sonra"). Üyelik girişi (`/member/login`), RSS bağlantıları, WhatsApp ihbar hattı, YouTube programları (video bölümünde stüdyo programları). Resmi ilan: "Resmi Reklam" kategorisi; `ilan.gov.tr` çerçevesi ve BİK analitik isteği anasayfa HTML'inde ve ilk 15 istek alanında **görülmedi**. Yorum: ölçülmedi.

## 11. Erişilebilirlik
`lang="tr-TR"`. "İçeriğe atla" bağlantısı bulunamadı; ilk odaklanan öğe `href="javascript:void(0)"` bir bağlantı. Anasayfada 107 `img`'nin 1'inde `alt` eksik; 99'unda `width/height`, 81'inde `loading="lazy"`. Odak görünürlüğü, kontrast: ölçülmedi.

## 12. Yapay zekâ kullanımı
Görülmedi (incelenen 7 sayfa; okuma süresi var, seslendirme/özet yok).

## Ölçüm dökümü
| ölçü | değer | yöntem |
|---|---|---|
| anasayfa HTML | 40.212 B / 272.489 B | `curl --compressed -w %{size_download}` / disk |
| detay HTML | 33.992 B / 192.682 B | aynı |
| ilk ekran başlık | 6 (1440) · 6 (390) | CDP: görünür, metni ≥ 25 karakter `a` |
| LCP / CLS / istek / aktarım | tablo §7 | `PerformanceObserver`; CDP Network olayları |
| gövde tipografisi | 20/30 px, 685 px, ~77 kar/satır | `getComputedStyle` + `Range.getClientRects` |
| eczane yapısal verisi | `Pharmacy` ×32, ilçe adresi 18 | JSON-LD `@type` sayımı; `bursa-*-nobetci-eczaneler` benzersiz adres |
| istek sayısı (bu site) | 11 | robots, anasayfa, bölüm, 2 detay, eczane, trafik, sitemap (`curl`) + 3 Chrome yüklemesi |
