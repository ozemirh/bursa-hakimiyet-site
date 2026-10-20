# Manchester Evening News (MEN)

> **İkincil kaynak — otomatik erişim yok.** SITELER.md'de "açık" listesindeydi;
> 2026-10-20'de yeniden okunan robots.txt `ClaudeBot`, `anthropic-ai` ve
> `Claude-Web` için `Disallow: /` diyor. README kuralı "en kısıtlayıcısı
> geçerlidir" olduğundan robots.txt dışında siteye **hiç istek atılmadı**.
> → SITELER.md "Erişim durumu" güncellenmeli (koordinatör / araştırmacı).

- Adres: https://www.manchestereveningnews.co.uk
- Katman: global listede **yerel** (Büyük Manchester; sahibi Reach plc)
- Neden seçildi: büyük ölçekli yerel gazete; semt/ilçe bölümleri, iki kulüp kapsamı, reklam yoğunluğu
- İnceleme: 2026-10-20 · koşul: yalnız robots.txt (curl, varsayılan UA, Türkiye) + üçüncü taraf yayınlar (WebSearch/WebFetch)
- İncelenen sayfalar: hiçbiri (otomatik erişim yok)

### robots.txt'ten okunabilenler (2026-10-20)
([robots.txt](https://www.manchestereveningnews.co.uk/robots.txt))
- `*` için `Crawl-delay: 10`; `/topics` ve `/topics/*`, `/search/`, `*token=*`, `*service=ajax`, `*.ece` kapalı.
- İki sitemap ilan edilmiş: `/map_news.xml` (haber sitemap'i) ve `/sitemaps/sitemap_index.xml`.
- Yapay zekâ tarayıcılarının neredeyse tamamı `Disallow: /`; reklam/bağlam tarayıcılarına (grapeshot, ozone, AmazonAdBot) `Crawl-delay: 0`.

## Özet — en öğretici 3 çözüm
1. **Semt markası = ana sitede bölüm + kendi sosyal hesabı + kısa adres.** Reach, MEN içinde "My Bolton / My Bury / My Salford" bölümleri açtı; her birinin ayrı sosyal hesabı ve kendine ait kısa alan adı (ör. mybolton.news) var, ~6 muhabirle başladı ([Press Gazette](https://pressgazette.co.uk/?p=149106), 2020-03-03; erişim 2026-10-20). — BH'ye: **kısmen**; ilçe sayfası zaten var (bellek: "ilçe sayfası yapıldı"); ayrı alan adı/sosyal hesap masa büyüklüğüne bağlı. 2026'daki durumu doğrulanmadı.
2. **Ücretli katman "son dakika ve kamu yararı ücretsiz; röportaj/görüş/derinlik ücretli + daha az reklam".** MEN Premium 27 Kasım 2025'te açıldı: aylık £4,99 / yıllık £39,99 ([Press Gazette](https://pressgazette.co.uk/paywalls/manchester-evening-news-launches-online-paywall/), 2025-11-27; [Press Gazette](https://pressgazette.co.uk/news-leaders/manchester-evening-news-editor-fed-up-of-playing-algorithmic-games/), 2025-12-22; erişim 2026-10-20). — **kısmen**; BH'nin gelir modeli kararı yok, desen kaydı.
3. **Kulüp kapsamı sitenin dışına da taşınıyor:** kulübe özel WhatsApp kanalı (~84 bin takipçi; içerik + kampanya) ve Reach'in haftalık, ücretsiz önizleme + ücretli katmanlı kulüp bülteni ([WhatsApp kanalı](https://www.whatsapp.com/channel/0029Va5la6v3bbV7no7rii2X), [Substack hakkında](https://insideoldtrafford.substack.com/about); erişim 2026-10-20). — **kısmen**; BH Bursaspor sayfası "maç + puan penceresi + fikstür" ile sınırlı (kullanıcı kararı); kanal/bülten sayfa dışı dağıtım olduğu için bu kararla çelişmez ama → `haber-muduru` değerlendirir.

## 1. Anasayfa bilgi mimarisi
Ölçülmedi (otomatik erişim yok).

## 2. Bölüm sayfası
Ölçülmedi (otomatik erişim yok). Not: robots.txt `/topics` yollarını tarayıcılara kapatıyor — konu/etiket sayfaları dizin dışında tutuluyor ([robots.txt](https://www.manchestereveningnews.co.uk/robots.txt), 2026-10-20).

## 3. Haber detay
Ölçülmedi (otomatik erişim yok).

## 4. Son dakika / canlı
- Sayfa biçimi ölçülmedi.
- Masa düzeni: MEN haber masası ~50 kişi; **merkezi spor ekibi ve Reach'in canlı haber ağı bu sayının dışında**; sabah 6'dan gece yarısına, haftanın 7 günü kordon/meclis/mahkeme kapsamı için kadro gerektiği ifade ediliyor ([Press Gazette](https://pressgazette.co.uk/news-leaders/manchester-evening-news-editor-fed-up-of-playing-algorithmic-games/), 2025-12-22; erişim 2026-10-20). Yerel masanın canlı/son dakikayı grup düzeyinde paylaşılan bir ağla beslediği anlaşılıyor.

## 5. Yerel ve servis içerikleri
- **Semt bölümleri:** My Bolton, My Bury, My Salford — MEN sitesinde ayrı bölüm, ayrı sosyal hesap, kendi kısa alan adı (bkz. Özet 1). Reach'in ayrıca "In Your Area" adlı mahalle düzeyi platformu var; MEN sitesindeki yeri doğrulanmadı ([Prolific North](https://prolificnorth.co.uk/?p=43716), arama özeti, açılmadı).
- Hava, ulaşım, trafik servis sayfaları: ölçülmedi.
- Yerel–ulusal dengesi: ölçülmedi.

## 6. Mobil davranış
Ölçülmedi (otomatik erişim yok).

## 7. Başarım
- Ölçülmedi (otomatik erişim yok; PageSpeed Insights anahtarsız API 2026-10-20'de günlük kota hatası verdi — HTTP 429).
- İkincil: Reach'in yeni web platformu Liverpool Echo'da denendikten sonra MEN'e geçti; Reach'e göre sayfa yükleme hızı **üç katına** çıktı, ziyaret başına sayfa **%2** arttı, reklam kaynaklı sayfa kayması giderildi — **şirketin kendi beyanı**, bağımsız ölçüm değil ([Press Gazette](https://pressgazette.co.uk/media_business/reach-results-2024-revenue-digital-growth-profits/), 2025-03-04; erişim 2026-10-20).

## 8. SEO yapısı
- Haber sitemap'i var: `/map_news.xml`; ayrıca sitemap dizini ([robots.txt](https://www.manchestereveningnews.co.uk/robots.txt), 2026-10-20). Dosyalar açılmadı.
- `/topics` sayfaları tarayıcılara kapalı (bkz. §2). JSON-LD, kanonik, AMP: ölçülmedi.
- Bağlam: Reach'te Google yönlendirme trafiği 2026'nın ilk yarısında bir önceki yıla göre %55 düştü ([Press Gazette](https://pressgazette.co.uk/news/reach-hits-50000-paid-subscribers-in-under-nine-months/), 2026-08-19; erişim 2026-10-20). Yayın yönetmeni Google'ın son dakika haberlerini ele alışını ve AI Overviews'u ciddi sorun olarak tarif ediyor (aynı kaynak, 2025-12-22).

## 9. Reklam
- Yerleşim ve yuva sayısı ölçülmedi.
- Reach yönetimi reklam yoğunluğu eleştirisini kabul ediyor; reklam sayısının önümüzdeki yıllarda "kademeli" azalacağı söylendi (arama özeti: [Hold the Front Page](https://www.holdthefrontpage.co.uk/2025/news/reach-boss-defends-free-to-access-websites-but-admits-user-experience-must-improve), 2025 — sayfa 403 döndü, açılamadı; **doğrulanmadı**).
- Mart 2025 itibarıyla Reach'in yerel siteleri "consent or pay" modeline geçmemişti ([Press Gazette](https://pressgazette.co.uk/marketing/cookies-consent-or-pay-guardian-gb-news-newsquest-city-am/), 2025-03-14; erişim 2026-10-20).

## 10. Gelir ve okur ilişkisi
- **Ücretli katman (Kasım 2025):** MEN Premium, aylık £4,99 / yıllık £39,99; daha az reklam + bazı yalnız-abone yazılar; son dakika ve kamu yararı haberleri ücretsiz; ücretli olan röportaj, uzun dosya, görüş ([Press Gazette](https://pressgazette.co.uk/news-leaders/manchester-evening-news-editor-fed-up-of-playing-algorithmic-games/), 2025-12-22). Reach'in ilk ücretli katmanıydı.
- **Ölçek (Ağustos 2026):** Reach 19 markada 50 bin ücretli dijital aboneye ulaştı; MEN 6 binin üzerinde ([Press Gazette](https://pressgazette.co.uk/news/reach-hits-50000-paid-subscribers-in-under-nine-months/), 2026-08-19). Reach CEO'su abonelik modelinin reklam modelini **tamamlayıcı** olduğunu söylüyor.
- Öncesi: yalnız uygulamada ölçülü (haftada 25 haber) premium deneme ([Press Gazette](https://pressgazette.co.uk/publishers/regional-newspapers/manchester-evening-news-men-trials-premium-app-with-metered-paywall/), arama özeti, açılmadı).
- Kulüp kanalları: WhatsApp kanalı ve haftalık ücretli/ücretsiz katmanlı kulüp bülteni (bkz. Özet 3). Kulüp başına ayrı editör atanmış ([Prolific North](https://www.prolificnorth.co.uk/?p=13694), arama özeti, açılmadı).
- Kayıt duvarı: Reach'in kayıtlı kullanıcı stratejisi 2020'den beri var; MEN'deki kayıt akışı ölçülmedi.
- Kitle (kaynakların verdiği sayı, tahmin değil): Eylül 2025'te aylık 14 milyon ziyaretçi (Ipsos iris, Press Gazette 2025-11-27).

## 11. Erişilebilirlik
Ölçülmedi (otomatik erişim yok).

## 12. Yapay zekâ kullanımı
- Reach'in kurum içi aracı **Guten**: kardeş sitelerdeki haberleri, ajans metinlerini ve bazı polis açıklamalarını yeniden yazmak için kullanılıyor; değişiklikler vurgulanıyor, YZ destekli haberlerin adresleri tabloya kaydediliyor ([Press Gazette](https://pressgazette.co.uk/publishers/nationals/reach-ai-guten/), 2024, arama özeti, açılmadı).
- Reach'e göre gazetecilerin yayın öncesi gözden geçirdiği YZ yazımı haberler bir yılda 1,8 milyar sayfa görüntülemesi getirdi; Guten hava bültenlerini yerel habere de çeviriyor ([Press Gazette](https://pressgazette.co.uk/media_business/reach-results-2024-revenue-digital-growth-profits/), 2025-03-04).
- Okura nasıl işaretlendiği: ölçülmedi. **BH için: okura "yapay zekâ destekli" etiketi reddedildi; "kopyalama yok / kaynaktan cümle alınmaz" kuralı nedeniyle Guten tipi yeniden yazım BH editoryal kurallarıyla çelişir** (CLAUDE.md, `haber_taslak.py` SISTEM).

## Ölçüm dökümü
| ölçü | değer | yöntem |
|---|---|---|
| robots.txt | 996 B, 200 | `curl -w '%{http_code} %{size_download}'`, 2026-10-20, Türkiye |
| Claude erişimi | `ClaudeBot`, `anthropic-ai`, `Claude-Web`: `Disallow: /` | robots.txt |
| Haber sitemap'i | `/map_news.xml` ilan edilmiş | robots.txt |
| Başarım | ölçülmedi | PSI anahtarsız API HTTP 429 (kota) |

İstek sayısı (manchestereveningnews.co.uk): **1** (robots.txt).
