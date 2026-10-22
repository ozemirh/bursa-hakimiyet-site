# Haber sitesi ve haber uygulamasına özgü teknik gereksinimler (2024–2026)

> Araştırma tarihi: 21 Ekim 2026. Çerçeveden bağımsız. Her iddianın yanında kaynak var. "[resmî belge — bu oturumda açılmadı]" işaretli kaynaklar, adresi bilinen resmî dokümanlardır ama bu oturumda içerikleri tekrar okunmadı; rapor yazarı bunları "doğrulanması gereken" diye ele almalıdır. Eski veriler yılıyla işaretlendi.

## 1. Google News ve Google Discover teknik gereksinimleri (2025–2026)

### Takeaway
Discover ve Google News için özel bir "katılım" yok; dizine eklenen ve politikalara uyan içerik otomatik olarak uygun sayılıyor. Teknik yığın şunları üretebilmeli: ≥1200 px geniş, 16:9 ve >300 bin piksel manşet görseli; `max-image-preview:large`; son 2 günün haberlerini içeren ve en fazla 1000 URL'lik news sitemap; doğru `datePublished`/`dateModified`; iyi Core Web Vitals. 2024–2026'daki en önemli değişiklikler: Publisher Center'da yayın sayfalarının otomatik üretilmesi (Mart 2025), site itibarı kötüye kullanımı politikasının genişletilmesi (Kasım 2024) ve AEA'da uygulamanın değiştirilmesi (Ağustos 2026; Türkiye AEA dışında).

### Cited Findings
**Discover**
- İçerik, Google tarafından dizine eklenmişse ve Discover içerik politikalarına uyuyorsa Discover'da çıkmaya otomatik olarak uygundur. Özel etiket ya da yapılandırılmış veri gerekmez, ama uygunluk görünmeyi garanti etmez. Sayfanın son güncellenme tarihi 2026-03-09 — [Google Search Central: Discover](https://developers.google.com/search/docs/appearance/google-discover)
- Görsel önerileri: en az 1200 px genişlik, 300.000 pikselden fazla çözünürlük, 16x9 en-boy oranı. `max-image-preview:large` ayarıyla ya da AMP ile etkinleştirilir. Tercih edilen görsel schema.org birincil görsel işaretlemesi ya da `og:image` ile belirtilir. Genel logo ve yazı ağırlıklı görsellerden kaçınılmalıdır. Elle kırpılacaksa önemli ayrıntılar `og:image` sürümünde korunmalıdır — [Google Search Central: Discover](https://developers.google.com/search/docs/appearance/google-discover)
- Başlıklarda tık tuzağı, yanıltıcı önizleme ve sansasyondan kaçınılmalı. "Genel olarak harika bir sayfa deneyimi" sağlanmalı. Politika ihlalleri Search Console'da elle işleme (manual action) yol açabilir. Discover Performans raporu 16 ayı gösterir — [Google Search Central: Discover](https://developers.google.com/search/docs/appearance/google-discover)
- Uygulama notu: Arc XP, Google'ın 1200 px önerisinin "aşırı büyük görsel sunmayın" önerisiyle çeliştiğini belirtiyor ve yalnızca `og:image`'ı ≥1200 px vermeyi öneriyor. Bu, görsel türetme (rendition) hattının en az iki boyut üretmesi gerektiği anlamına geliyor — [Arc XP FAQ: Google Discover](https://docs.arcxp.com/en/products/general/faq--google-discover.html)
- `max-image-preview` robots meta değerleri: none, standard, large. Mevcut etiket çoğaltılmamalı, değeri "large" yapılmalı — [Search Engine Journal](https://www.searchenginejournal.com/increase-google-traffic-with-max-image-preview-tag/)

**News sitemap**
- Bir news sitemap en fazla 1000 `<news:url>` içerebilir; fazlası birden çok dosyaya bölünür. `news:publication_date` W3C biçiminde (YYYY-MM-DD ya da saat dilimli tam zaman) olmalı ve sitemap'e eklenme zamanı değil, özgün yayın zamanı olmalı — [Google Search Central: News sitemaps](https://developers.google.com/search/docs/advanced/sitemaps/news-sitemap?hl=en)
- İki günden eski makalelerin URL'leri news sitemap'ten çıkarılmalı ya da news etiketi kaldırılmalı — [Google News Publisher Help: News sitemaps](https://support.google.com/news/publisher/answer/74288)
- Üçüncü taraf bir rehber en az saatlik güncellemeyi öneriyor (resmî değil) — [seo-day.de](https://www.seo-day.de/wiki/spezielle-anwendungsfaelle/news-seo/news-sitemaps?lang=en)

**NewsArticle yapılandırılmış verisi**
- `Article`/`NewsArticle` için zorunlu alan yok. Önerilenler: `headline`, `image` (birden çok en-boy oranı: 16x9, 4x3, 1x1), `datePublished`, `dateModified`, `author` (author.name, author.url) — [Google Search Central: Article structured data](https://developers.google.com/search/docs/appearance/structured-data/article) [resmî belge — bu oturumda açılmadı]

**Sayfa deneyimi / Core Web Vitals**
- "Core Web Vitals are used by our ranking systems." Ama iyi skor üst sırayı garanti etmez ve yalnızca SEO için kusursuz skor peşinde koşmaya değmeyebilir. "There is no single signal": sayfa deneyimi tek bir sıralama sistemi değil. Sayfanın son güncellenme tarihi 2026-09-22 — [Google Search Central: Understanding page experience](https://developers.google.com/search/docs/appearance/page-experience)
- INP, Mart 2024'te FID'in yerine Core Web Vitals metriği oldu (duyuru Mayıs 2023) — [Google Search Central Blog, 2023](https://developers.google.com/search/blog/2023/05/introducing-inp?authuser=1); [Search Engine Land](https://searchengineland.com/google-replace-fid-inp-core-web-vitals-414546)
- Top Stories için AMP şartı Mayıs 2021'de kalktı. O tarihten beri Google News içerik politikalarına uyan ve sayfa deneyimi iyi olan her sayfa Top Stories'e girebiliyor — [Search Engine Land (2021)](https://searchengineland.com/will-publishers-drop-amp-when-its-no-longer-a-requirement-for-top-stories-335612)

**Google News Publisher Center değişiklikleri**
- Nisan 2024: Publisher Center'a yeni yayın eklenemez oldu — [Search Engine Land](https://searchengineland.com/google-publisher-center-to-stop-allowing-you-to-add-publications-439978)
- Mart 2025 sonu: Google News tamamen otomatik üretilen yayın sayfalarına geçti. Publisher Center'da gönderilen RSS akışları ve web konumları artık kullanılmıyor, gereksiz özelleştirmeler kaldırıldı. Google'a göre bu değişiklik içerik uygunluğunu etkilemiyor — [Google News Publisher Center Help](https://support.google.com/news/publisher-center/answer/15898024); [Search Engine Land](https://searchengineland.com/google-news-automated-publication-pages-to-start-in-march-451831)

**Site itibarı kötüye kullanımı (site reputation abuse)**
- 19 Kasım 2024: Politika, ev sahibi sitenin birinci taraf katılımı ya da gözetimi olsa bile (beyaz etiket hizmetleri, lisans anlaşmaları, kısmi ortaklık) üçüncü taraf içerikle sitenin sıralamasından yararlanmayı kapsayacak şekilde genişletildi — [Google Search Central Blog, Kasım 2024](https://developers.google.cn/search/blog/2024/11/site-reputation-abuse)
- 28 Ağustos 2026: Avrupa Komisyonu ile görüşmelerin ardından AEA (EEA) içindeki uygulama değişti. 30 Ağustos'tan itibaren AEA içindeki kullanıcılar için sıralamayı etkileyen elle işlem uygulanmıyor; ihlal eden bölüm sistemde ayrıştırılıp kendi değeriyle sıralanıyor. AEA dışındaki kullanıcılar için elle işlem ihlal eden bölüme uygulanmaya devam ediyor — [Google Search Central Blog, Ağustos 2026](https://developers.google.com/search/blog/2026/08/update-site-reputation-policy) (gövde metni bu oturumda okunamadı; ayrıntı [Search Engine Journal](https://www.searchenginejournal.com/google-updates-site-reputation-abuse-policy-removes-penalties-in-eea/)'dan)

### Inferences
- Türkiye AEA'da olmadığından, Bursa Hakimiyet'in Türkiye'deki okurlarına site itibarı kötüye kullanımı elle işlemi uygulanmaya devam eder. Pratik sonuç: "haber reklam", sponsorlu içerik, kupon ya da ortaklık bölümleri ayrı ve açıkça işaretlenmiş olmalı. Bu, BİK'in `articleSection=haberreklam` şartıyla da örtüşüyor (§9).
- Teknoloji seçiminde gerekenler: (a) en az 1200 px'lik 16:9 türev üretebilen bir görsel hattı ve birden çok en-boy oranı (1x1, 4x3, 16x9); (b) son 48 saatin haberlerini dinamik olarak üreten ve yayında anında güncellenen bir news sitemap; (c) 1M arşiv için ayrı, bölünmüş standart sitemap'ler; (d) sunucu tarafında üretilen (SSR) ve JSON-LD'si HTML'de olan sayfalar.
- Publisher Center artık bir "kayıt" adımı olmadığına göre Google News görünürlüğü tamamen site sinyallerine (sitemap, yapılandırılmış veri, politika uyumu) dayanıyor.

### Gaps
- Article structured data sayfasının 2026 sürümünde değişiklik olup olmadığı bu oturumda doğrulanmadı.
- Core Web Vitals'ın Top Stories ya da Discover'a özel ağırlığına dair resmî bir kaynak bulunamadı.
- Discover'ın masaüstüne genişlemesi ya da "takip et" özelliği gibi 2025–2026 değişiklikleri resmî Discover sayfasında yer almıyor; başka kaynaklarda da aranmadı.

## 2. AMP'nin haberler için güncel durumu

### Takeaway
AMP, 2021'den beri Top Stories için şart değil. 2024–2026 için AMP'yi öneren resmî bir Google belgesi bulunamadı; Discover dokümanı AMP'yi büyük görsel için yalnızca `max-image-preview:large`'a bir alternatif olarak anıyor. Yeni bir yığında AMP gerekli değil.

### Cited Findings
- Top Stories'te AMP şartı Mayıs 2021'de kaldırıldı — [Search Engine Land (2021)](https://searchengineland.com/will-publishers-drop-amp-when-its-no-longer-a-requirement-for-top-stories-335612)
- 2021–2022 itibarıyla ABD ve İngiltere'de Top Stories URL'lerinin yaklaşık üçte biri AMP dışıydı. Çoğu yayıncı "bekle-gör" tutumundaydı. AMP'nin değeri en çok ücretsiz, reklamla gelir elde eden yayıncılar için sürüyordu — [Press Gazette (2021–22)](https://pressgazette.co.uk/google-amp-publishers-top-stories)
- AMP'den çıkışı test eden müşterilerde arama performansında olumsuz etki görülmedi (danışmanlık firması beyanı) — [SearchPilot](https://www.searchpilot.com/resources/blog/amp-seo-decline)
- Twitter AMP desteğini kaldırdı (Press Gazette, 2021–22) — [Press Gazette](https://pressgazette.co.uk/google-amp-publishers-top-stories)
- Yayıncıların AMP'yi yeniden değerlendirmesi — [A Media Operator](https://www.amediaoperator.com/analysis/publishers-are-reconsidering-google-amp/)
- Discover'da büyük görsel için `max-image-preview:large` ya da AMP yeterli (2026) — [Google Search Central: Discover](https://developers.google.com/search/docs/appearance/google-discover)

### Inferences
- AMP ikinci bir şablon setinin ve reklam entegrasyonunun bakımını gerektirir. Küçük ekip için maliyet getiriden fazla. Bunun yerine iyi Core Web Vitals ve `max-image-preview:large` yeterli.
- Mevcut sitede AMP URL'leri varsa, kaldırırken AMP adreslerinden kanonik adrese 301 vermek gerekir (genel SEO pratiği; bu oturumda kaynakla doğrulanmadı).

### Gaps
- 2024–2026'ya ait güncel AMP kullanım oranı (kaç yayıncının bıraktığı) için güvenilir bir istatistik bulunamadı.

## 3. Önbellek ve CDN stratejileri

### Takeaway
Haber sitelerinde yerleşik desen şöyle: kenarda (edge) uzun TTL, tarayıcıda kısa TTL; yayın ya da güncelleme anında anahtar (surrogate key / cache tag) ile hedefli temizleme; temizlemeyi "soft purge" ile yapıp `stale-while-revalidate` + `stale-if-error` ile kaynağı korumak. Cloudflare, etiketle temizlemeyi 2025'te tüm planlara açtı. Bu, küçük bir ekip için Enterprise sözleşmesi olmadan bu deseni mümkün kılıyor.

### Cited Findings
- Fastly'nin önerisi: makale yanıtlarını bir surrogate key ile etiketle, haber değiştiğinde anahtar ya da URL ile temizle; kenarda uzun TTL, tarayıcıda kısa TTL ver. Yol öneki anahtarlarıyla bir bölümün tamamı tek çağrıda temizlenebilir — [Fastly Blog: Is purging still the hardest problem in computer science?](https://www.fastly.com/es/blog/is-purging-still-the-hardest-problem-in-computer-science)
- `Cache-Control`'de `stale-while-revalidate` ile `stale-if-error`'ı soft purge ile birlikte kullanma önerisi — [Fastly Blog](https://quic.fastly.com/blog/is-purging-still-the-hardest-problem-in-computer-science)
- Soft purge nesneyi silmez, bayat olarak işaretler (`Fastly-Soft-Purge` başlığı). Önce ETag ya da Last-Modified ayarlanmalı, yoksa `stale_while_revalidate` ile `stale_if_error` yapılandırılmalı — [Fastly Docs: Soft purges](https://www.fastly.com/documentation/guides/full-site-delivery/purging/soft-purges)
- Cloudflare, "Instant Purge for All" ile etiket, önek ve hostname temizlemesini tüm planlara açtı (Birthday Week 2024'te duyuruldu, 2025'te yayına alındı). Daha önce URL ve "hepsini temizle" dışındaki yöntemler yalnızca Enterprise'daydı. Yeni hat tutarlı olarak 150 ms'nin altında çalışıyor — [Cloudflare Blog: Instant Purge for all](https://blog.cloudflare.com/ko-kr/instant-purge-for-all)
- Bir Drupal modülünün tablosuna göre etiketle temizleme istek başına 30 etikete kadar kabul ediyor (üçüncü taraf beyanı; plan bazlı hız sınırları resmî dokümanda doğrulanmadı) — [Drupal cloudflare_purge](https://drupal.org/project/cloudflare_purge)
- BİK tebliği, DDoS gibi ani trafik artışlarında gerçek olmayan kullanıcıları engellemek için CAPTCHA kullanılmasını zorunlu tutuyor ve BİK denetim IP'lerinin (82.222.188.222, 213.74.78.242) beyaz listeye alınmasını istiyor — [BİK Tebliği (2024), Md. 4/9 ve 6/3](https://bik.gov.tr/storage/2024/05/Internet-Haber-Sitelerinin-Teknik-Olarak-Uymasi-Gereken-Kurallara-Dair-Usul-ve-Esaslar-Hakkinda-Teblig.pdf)

### Inferences
- Kontrol listesi maddeleri: (1) her HTML yanıtına anlamlı cache tag'ler (`haber-<id>`, `kategori-<slug>`, `anasayfa`, `yazar-<id>`); (2) yayın ya da güncelleme olayında CMS'ten CDN API'sine otomatik temizleme; (3) `s-maxage` uzun, `max-age` kısa, `stale-while-revalidate` ve `stale-if-error` açık; (4) kaynak sunucuda kısa süreli mikro önbellek (1–10 sn) ile ani taleplerde istek birleştirme; (5) WAF ve bot koruması BİK IP'lerini engellememeli, DDoS anında CAPTCHA devreye girebilmeli.
- Deprem gibi ani trafik patlamalarında asıl koruma, anonim okur trafiğinin neredeyse tamamının CDN'den karşılanmasıdır. Bu nedenle kişiselleştirme (oturum, çerez) HTML önbelleğini bozmamalı; kişisel bölümler istemci tarafında ayrı bir uç noktadan gelmeli.
- Origin shielding, yani tek bir ara katmanın kaynağa gitmesi, kaynağın yükünü düşürür. Fastly ve Cloudflare'de (Tiered Cache) bulunur; bu oturumda dokümanla doğrulanmadı.

### Gaps
- Guardian, BBC ya da NYT'nin önbellek mimarisine dair 2024–2026 tarihli bir mühendislik yazısı bu oturumda bulunamadı. Fastly'nin kaynakları satıcı materyali.
- Türkiye'deki deprem (Şubat 2023) sırasında haber sitelerinin trafik ve altyapı deneyimine dair güvenilir bir kaynak bulunamadı.
- Mikro önbellek ve origin shielding için birincil kaynak bu oturumda getirilmedi.

## 4. Son dakika ve canlı yayın blogları: yoklama (polling), SSE, WebSocket

### Takeaway
Canlı bloglar tek yönlü bir veri akışıdır (sunucudan okura). Bu nedenle CDN'de önbelleklenen bir JSON uç noktasını kısa aralıklarla yoklamak ya da SSE kullanmak, WebSocket'ten daha basit ve ölçeklenebilir. Büyük yayıncıların 2024–2026 tarihli uygulama ayrıntıları bu oturumda birincil kaynaktan bulunamadı.

### Cited Findings
- Guardian'da toplam sayfa görüntülemelerinin yaklaşık %15'i canlı bloglardan geliyor (Andrew Sparrow röportajı) — [Press Gazette](https://pressgazette.co.uk/?p=255587)
- Yoklamada her tarayıcı, değişiklik olsun olmasın her 10 saniyede istek atar. Sunucu yükü okur sayısıyla doğrusal artar — [Eric Mann: Live Blogging – AJAX Polling](https://eric.mann.blog/live-blogging-ajax-polling/)
- SSE düz HTTP üzerinden çalışır, otomatik yeniden bağlanır, sıradan proxy'lerden geçer. Tek yönlü akışta en basit araçtır. Yoklama, ortalama olarak aralığın yarısı kadar gecikme ekler — [Back4App glossary](https://www.back4app.com/glossary/sse-vs-websockets-vs-polling.md)
- Ghent/imec çalışması (2020): 25 bin istemcide HTTP yoklama ile SSE karşılaştırıldı; itme (push) genelde daha düşük gecikme veriyor — [Ruben Verborgh, ICWE 2020](https://ruben.verborgh.org/publications/vandevyvere_icwe_2020/)
- Geleneksel uygulama sunucularında her SSE bağlantısı bir süreci açık tutar (örn. PHP-FPM'de süreç sınırı bağlantı tavanını belirler). Yaygın desen: HTML uzun süre önbelleklenir, güncellemeler yayın sırasıyla anahtarlanan, önceden işlenmiş HTML içeren JSON ile gelir — [craft-live (Packagist)](https://packagist.org/packages/justinholtweb/craft-live)
- Akamai gibi CDN'lerle çalışan, Alman ve Avusturya yayıncıları için yapılmış bir Drupal liveblog modülü var — [Drupal liveblog](https://www.drupal.org/node/1264170)

### Inferences
- Django gibi senkron WSGI sunucularında SSE ya da WebSocket, her bağlantı için bir işçi tutar. Bu nedenle küçük ekip için en güvenli yol, CDN'de 5–15 sn önbelleklenen bir JSON uç noktasını yoklamaktır: kaynak yükü okur sayısından bağımsızlaşır. SSE ya da WebSocket ancak ASGI veya ayrı bir yayın hizmeti (yönetilen pub/sub) ile düşünülmeli.
- Canlı blog sayfasının kendisi de ayrı yapılandırılmış veri taşıyabilir (`LiveBlogPosting`; bu oturumda doğrulanmadı).

### Gaps
- Guardian, BBC ve NYT canlı bloglarının 2024–2026 teknik uygulaması (yoklama aralığı, SSE ya da WebSocket kullanımı) için birincil mühendislik kaynağı bulunamadı.
- Google'ın `LiveBlogPosting` yapılandırılmış verisinin güncel durumu bu oturumda kontrol edilmedi.

## 5. ~1M haberlik arşivde arama: PostgreSQL FTS mi, ayrı arama motoru mu; Türkçe desteği

### Takeaway
PostgreSQL'in yerleşik "turkish" Snowball sözlüğü var, ama i/İ ve ı/I büyük-küçük harf dönüşümü yerel ayara ve işletim sistemine bağlı; Windows'ta hata raporları mevcut. ICU tabanlı belirleyici olmayan (nondeterministic) collation bir çözüm olarak öneriliyor. Meilisearch'ün tokenizer'ı (Charabia) Türkçe noktalı/noktasız i için özel harf katlama uyguluyor, ama Türkçe kök bulmayı (stemming) belgelemiyor. 1M kayıtlık ölçek için yayımlanmış karşılaştırmalı bir ölçüm bulunamadı.

### Cited Findings
- PostgreSQL, Snowball tabanlı bir `turkish` metin arama yapılandırmasıyla gelir — [PostgreSQL Docs: Text Search Dictionaries](https://www.postgresql.org/docs/current/textsearch-dictionaries.html) [resmî belge — bu oturumda açılmadı]
- 2025 tarihli pgsql-bugs raporu: Windows'ta Türkçe collation ile `ILIKE`, "ŞİLİ" ile "şili"yi eşleştirmedi, Linux'ta eşleştirdi. Laurenz Albe'nin önerisi ICU tabanlı belirleyici olmayan collation: `LOCALE = 'tr-TR@colStrength=level2'` — [PostgreSQL mailing list (2025)](https://www.postgresql.org/message-id/e9427abbe32a10733eb9451fa466e4a591531a27.camel@cybertec.at); [hackorum: BUG #19048](https://hackorum.dev/topics/73295)
- ICU'da "İ" (U+0130) küçük harfe çevrilirken iki geçerli sonuç çıkabiliyor: Türkçe ve Azerice yerel ayarlarda düz "i", diğerlerinde "i" + birleşik nokta — [hackorum: citext Turkish I](https://hackorum.dev/topics/46818)
- 2009'da Türkçe yerel ayarla tsearch testleri kök bulma işlevleri yüzünden başarısız oluyordu (eski; düzeltildiğine dair güncel bir teyit bulunamadı) — [pgsql-hackers (2009)](https://www.postgresql.org/message-id/49749645.5070801%40gmx.net)
- Meilisearch'ün Charabia tokenizer'ı Türkçeyi varsayılan bölümlemeyle ve noktalı/noktasız i için özel bir harf katlama kuralıyla destekliyor. Özel bölümleme hatları yalnızca Çince, Japonca, İbranice, Tayca ve Kmerce için var — [Meilisearch Docs: Language](https://www.meilisearch.com/docs/learn/what_is_meilisearch/language); [Meilisearch Docs: Tokenization](https://www.meilisearch.com/docs/learn/advanced/tokenization)
- Meilisearch dil desteği konusunda FOSDEM 2026 sunumu — [FOSDEM 2026](https://fosdem.org/2026/schedule/event/meilisearch-laguage-support)

### Inferences
- PostgreSQL sabit olduğundan ilk seçenek FTS'dir: `tsvector` için oluşturulmuş sütun + GIN indeksi; normalizasyon uygulama tarafında Türkçe kurallara göre yapılır (İ→i, I→ı); `unaccent` ve `pg_trgm` yazım hatası toleransı için eklenir. Üretim ortamı Linux ve ICU olmalı; Windows geliştirme makinesinde sonuçlar farklı çıkabilir.
- Yazım hatası toleransı, eşanlamlı kelime ve faset gibi "arama ürünü" özellikleri istenirse ikinci bir motor (Meilisearch, Typesense, OpenSearch) eklenir. Bu, eşitleme hattı (CDC ya da sinyal tabanlı) ve ek işletim yükü demek. Küçük ekip için bu maliyet açıkça hesaba katılmalı.
- Türkçe eklemeli bir dil olduğundan kök bulma kalitesi kritik. Snowball Turkish ile Meilisearch'ün ön ek tabanlı eşleşmesi gerçek arşiv sorgularıyla denenmeli (ör. "Bursaspor'un", "belediyesinden").

### Gaps
- Typesense'in Türkçe desteği (tokenizer, stemming, ı/i) için kaynak bulunamadı.
- OpenSearch/Elasticsearch Türkçe analizörü (turkish_lowercase, turkish stemmer) için bu oturumda kaynak getirilmedi.
- ~1M makalede PostgreSQL FTS gecikmesi ile ayrı motorların karşılaştırmasını veren güvenilir bir ölçüm bulunamadı.
- Meilisearch'ün Türkçe kök bulma yapıp yapmadığı doğrulanamadı.

## 6. Mobil uygulama arka ucu: API, push bildirimi, derin bağlantı, çevrimdışı okuma, görsel türevleri

### Takeaway
FCM'in varsayılan kotası proje başına dakikada 600 bin mesaj; topic mesajlaşması gecikme için değil, yüksek hacim için optimize edilmiş. Yerel bir gazetenin son dakika bildirimleri için topic'ler (kategori, ilçe) yeterli. Guardian, BBC ve NYT uygulamalarının aynı arka uçtan nasıl beslendiğine dair güncel birincil kaynak bulunamadı; elde yalnızca 2009 tarihli bir Guardian notu var.

### Cited Findings
- FCM'in varsayılan aşağı yön kotası proje başına dakikada 600 bin mesaj; geliştiricilerin %99'undan fazlasına yetiyor. Kota aşılınca HTTP 429 RESOURCE_EXHAUSTED dönüyor. Kota istek değil mesaj sayar; dakika pencereleri saate hizalı değil; sınırlar değişebilir — [Firebase: Throttling and quotas](https://firebase.google.com/docs/cloud-messaging/throttling-and-quotas.md.txt)
- Topic mesajlaşması gecikme için değil, yüksek hacim için optimize edilmiştir. Tek cihaza ya da küçük gruba hızlı teslim için registration token hedeflenmelidir. Uygulama örneği başına en fazla 2000 topic aboneliği olabilir, toplu abonelik isteği en fazla 1000 örnek içerir — [Firebase: Topic messaging](https://firebase.google.com/docs/cloud-messaging/topic-messaging?hl=de)
- Bir FCM v1 mesajında `token`, `topic` ve `condition` birbirini dışlar; `condition` topic'lerin mantıksal birleşimine izin verir — [FCM REST v1: projects.messages](https://firebase.google.com/docs/reference/fcm/rest/v1/projects.messages?hl=de)
- Guardian'ın ilk iPhone uygulamasının arka ucu EC2 üzerinde çalışan bir Django uygulamasıydı (Simon Willison, 2009; güncel mimariyi yansıtmaz) — [Simon Willison (2009)](https://simonwillison.net/2009/Dec/14/iphone/)
- iOS Universal Links için `apple-app-site-association` dosyası — [Apple Developer: Supporting associated domains](https://developer.apple.com/documentation/xcode/supporting-associated-domains) [resmî belge — bu oturumda açılmadı]
- Android App Links için `/.well-known/assetlinks.json` — [Android Developers: Verify App Links](https://developer.android.com/training/app-links/verify-android-applinks) [resmî belge — bu oturumda açılmadı]

### Inferences
- Arka uç kontrol listesi: (1) web ile aynı içerik modelinden beslenen, sürümlü bir okuma API'si (REST + JSON yeterli; manşet, kategori, haber detayı, canlı blog); (2) API yanıtları da CDN'de cache tag'le önbelleklenmeli, web ile aynı temizleme olayına bağlanmalı; (3) haber gövdesi, uygulamanın yerel olarak çizebileceği yapılandırılmış bloklar hâlinde olmalı (paragraf, görsel, gömülü içerik), ham HTML olmamalı; (4) görsel türevleri: liste, detay, Discover ≥1200 ve 1x1 boyutlarında WebP/AVIF; (5) push: "son-dakika", kategori ve ilçe topic'leri; panelde "bildirim gönder" yetkisi ve tekrar gönderimi önleme; (6) web URL'leri doğrudan uygulamada açılabilmeli (AASA + assetlinks), bu yüzden URL yapısı kalıcı olmalı; (7) çevrimdışı okuma için son N haberin JSON'u ve görselleri cihazda önbelleklenir; arka ucun işi, `updated_at` ve ETag ile artımlı eşitlemeyi desteklemek.
- GraphQL, birden fazla istemci ekibi olan büyük yapılarda anlamlı. Tek ekip ve tek istemci için REST + CDN önbelleği daha basit, çünkü GraphQL POST yanıtlarını CDN'de önbelleklemek zor (genel bilgi; bu oturumda kaynakla doğrulanmadı).

### Gaps
- Guardian (MAPI), BBC ve NYT'nin uygulama arka uçlarına dair 2024–2026 birincil kaynakları bulunamadı.
- APNs `interruption-level: time-sensitive` ve iOS bildirim özetleri hakkında Apple dokümanı bu oturumda getirilmedi.
- Push segmentasyonuna dair yayıncı vaka çalışması bulunamadı.

## 7. Reklamların etkisi: GAM/AdSense, header bidding, tembel yükleme, CLS rezervasyonu

### Takeaway
Reklam alanları için yer önceden ayrılmalı, reklam betikleri `async` yüklenmeli, ekranın altındaki alanlar tembel yüklenmeli. Header bidding LCP ve INP'yi kötüleştirir; satıcı kaynakları LCP'ye 200–800 ms eklendiğini söylüyor (doğrulanmamış). Yenileme aralığı 30–240 sn arasında olmalı.

### Cited Findings
- web.dev (son güncelleme 2023-09-23): reklamlar için yer ayrılmalı; ekranın altındaki reklamlar görünüme yaklaşana kadar ertelenmeli (iframe'lerde `loading=lazy`); reklam betikleri `async` yüklenmeli (AdSense, auto ads, `gpt.js` örnekleri); header bidding uygulamalarının başarımı ölçülmeli; reklamlar sayfa yenilenmeden 30–240 sn'de bir yenilenebilir, bazı alıcılar en az 240 sn istiyor — [web.dev: Effectively loading ads without impacting page speed](https://web.dev/articles/loading-ads-page-speed)
- Çok boyutlu alanlarda en büyük boyut ya da en sık sunulan boyut için yer ayrılmalı; uygun boyut sayısı sınırlanmalı — [headerbidding.co](https://headerbidding.co/ads-and-core-web-vitals)
- Header bidding LCP'ye tahminen 200–800 ms ekler; ekranın üst kısmındaki büyük bir reklam kreatifi LCP öğesi olabilir; açık artırma ana iş parçacığını meşgul edip INP'yi etkiler (satıcı kaynağı, doğrulanmamış) — [pubperf](https://www.pubperf.com/blog/ads-core-web-vitals-guide)
- BİK: ana sayfa, resmî ilan kategori sayfası ve künye sayfasında denetimi engelleyebilecek geçiş reklamı (interstitial) kullanılamaz — [BİK Tebliği (2024), Md. 4/5](https://bik.gov.tr/storage/2024/05/Internet-Haber-Sitelerinin-Teknik-Olarak-Uymasi-Gereken-Kurallara-Dair-Usul-ve-Esaslar-Hakkinda-Teblig.pdf)
- BİK'in 9 Ekim 2026 tarihli değişikliği "dinamik reklamlar ve üçüncü taraf sistemlerle yayınlanan reklamların işaretlenmesi" kurallarını güncelliyor (ayrıntı haberde yok) — [Yeni Ankara](https://www.yeniankara.com.tr/guncel/internet-haber-sitelerinde-yeni-donem-bikin-teknik-kurallari-2027de-degisiyor-185723)

### Inferences
- Şablon sistemi her reklam yuvası için sabit `min-height` (kırılma noktasına göre) üretebilmeli. Reklam yuvaları bir yapılandırmadan (panel) yönetilmeli. GPT'nin `enableLazyLoad` ayarı ya da Prebid yalnızca istemci tarafında çalışır; bu sunucu çerçevesinden bağımsızdır.
- Reklam ve analitik çerezleri KVKK açık rızasına bağlı olduğundan (§8), rıza vermeyen okur için reklam isteğinin kişiselleştirilmemiş moda geçebilmesi gerekir.

### Gaps
- GPT `enableLazyLoad` parametreleri için Google Ad Manager dokümanı bu oturumda getirilmedi.
- Header bidding'in Core Web Vitals'a etkisine dair bağımsız ve hakemli bir ölçüm bulunamadı.

## 8. Erişilebilirlik (WCAG 2.2) ve hukuki bağlam (KVKK, AB Erişilebilirlik Yasası)

### Takeaway
AB Erişilebilirlik Yasası (EAA) 28 Haziran 2025'te yürürlüğe girdi. Kapsamı belirli ürün ve hizmetlerle sınırlı (e-kitap, e-ticaret, bankacılık…); haber sitelerini doğrudan kapsadığına dair kaynak bulunamadı. Türkiye'deki ve AB'ye ürün satmayan bir yerel gazete için doğrudan bağlayıcı olması düşük olasılık. Yine de WCAG 2.2 AA iyi bir hedef. KVKK'nın çerez rehberi analitik ve reklam çerezlerini açık rızaya bağlıyor; güncel sürüm Temmuz 2025 tarihli.

### Cited Findings
- EAA 28 Haziran 2025'te yürürlüğe girdi. Kapsamında e-kitaplar, e-okuyucular, e-ticaret, bankacılık ve bunlara ait web siteleri ile mobil uygulamalar var. Belirleyici olan hizmetin nerede sunulduğu, firmanın nerede olduğu değil. Mikro işletmeler (10 kişiden az çalışan ve 2 milyon €'dan az ciro) genelde muaf. Uygulama üye devletlerin piyasa gözetimiyle yapılıyor — [BCLP](https://www.bclplaw.com/en-US/events-insights-news/what-is-the-european-accessibility-act-and-what-impact-will-it-have-on-your-business.html); [KGL EAA FAQ (2025)](https://kwglobal.com/wp-content/uploads/2025/02/KGL-European-Accessibility-Act-FAQ.pdf)
- Eski e-kitaplar için geçiş süresi konusunda kaynaklar çelişiyor — [DAISY](https://daisy.org/news-events/articles/eaa-backlist-confusion-looking-at-regional-differences/)
- KVKK Çerez Uygulamaları Hakkında Rehber: taslak 11 Ocak 2022'de, nihai metin 20 Haziran 2022'de yayımlandı. Çerezler yerleştirilmeden önce açık rıza alınmalı. "Kişisel verilerimin işlenmesini kabul ediyorum" gibi genel bir ifade ya da siteyi ziyaret etmek açık rıza sayılmaz — [Hukuki Haber](https://www.hukukihaber.net/kvk-kurumunun-cerez-uygulamalari-hakkinda-yayinladigi-rehber); [Global Compliance News (2022)](https://www.globalcompliancenews.com/2022/07/08/the-guideline-on-use-of-cookies-has-been-published-29062022/)
- KVKK sitesindeki rehber Temmuz 2025 tarihli ve "KVKK Yayınları No: 69" olarak görünüyor (içerik ayrıntılı incelenmedi) — [KVKK: Çerez Uygulamaları Hakkında Rehber](https://kvkk.gov.tr/Icerik/7353/Cerez-Uygulamalari-Hakkinda-Rehber)
- Rehberde birinci taraf analitik çerezler ve sosyal eklenti çerezleri açık rıza gerektiren kategoriler arasında anılıyor; rızasız analitik ve reklam çerezi kullanan bir e-ticaret sitesine ceza verildiği aktarılıyor (ikincil kaynak) — [Kazım Ceylan Hukuk](https://www.kazimceylan.av.tr/cerez-politikasi-ornegi)
- WCAG 2.2, W3C Önerisi (Ekim 2023) — [W3C WCAG 2.2](https://www.w3.org/TR/WCAG22/) [resmî belge — bu oturumda açılmadı]

### Inferences
- Teknik sonuçlar: (1) rıza yönetimi (CMP) analitik ve reklam etiketlerini rızadan önce yüklememeli. BİK Analitik kodu tebliğ gereği `<head>`'de ve diğer ölçüm kodlarından önce olmak zorunda (§9); bu kodun KVKK rızasıyla ilişkisi hukukçuya sorulmalı. (2) WCAG 2.2 AA: odak görünürlüğü, hedef boyutu (2.5.8), sürükle-bırak alternatifi, erişilebilir kimlik doğrulama (panel girişi için).
- EAA: Bursa Hakimiyet AB'de ürün ya da hizmet (abonelik, e-kitap) satmıyorsa doğrudan kapsam dışında olması muhtemel. Hukuki teyit gerekir.

### Gaps
- EAA metninde (Direktif 2019/882) haber sitelerinin açıkça kapsam dışı olup olmadığı birincil metinden doğrulanmadı.
- KVKK 2025 rehberinin 2022'den farkları incelenmedi.
- Türkiye'de web erişilebilirliğini zorunlu kılan bir düzenleme (ör. kamu siteleri için) özel yayıncıya uygulanıyor mu, araştırılmadı.

## 9. Türkiye'ye özgü: Basın İlan Kurumu (BİK) teknik kuralları

### Takeaway
Resmî ilan ve reklam alan internet haber siteleri için BİK'in 1 Haziran 2024'te yürürlüğe giren tebliği somut HTML şartları koyuyor: belirli `<meta>` adları (`title`, `description`, `datePublished`, `dateModified`, `url`, `articleSection`, `articleAuthor`; "Meta Yazar Bilgisi" pratikte `articleAuthor` mahreç etiketidir), `property="articleBody"` kapsayıcısı, `bik-kunye-*` kimlikli künye div'leri, `<head>`'de diğer ölçüm kodlarından önce gelen BİK Analitik kodu, XML sitemap index, SSL, canonical, CAPTCHA ve BİK IP'lerinin beyaz listeye alınması. 9 Ekim 2026'da kabul edilen yeni tebliğ 1 Ocak 2027'de yürürlüğe girecek; tam metni bu oturumda bulunamadı.

### Cited Findings (hepsi: [BİK Tebliği, YK karar tarihi 10.05.2024, yürürlük 1.6.2024](https://bik.gov.tr/storage/2024/05/Internet-Haber-Sitelerinin-Teknik-Olarak-Uymasi-Gereken-Kurallara-Dair-Usul-ve-Esaslar-Hakkinda-Teblig.pdf); duyuru: [bik.gov.tr, 13 Mayıs 2024](https://bik.gov.tr/kurumsal-haberler/internet-haber-sitelerine-iliskin-teknik-esaslar-yeniden-duzenlendi/))
- **Md. 4 Genel:** (1) güncel ve geçerli SSL/TLS sertifikası; (2) 5651/8-1'deki suç içeriği barındıran sitelere bağlantı verilemez; (3) description ve anahtar kelime alanlarında içerikle ilgisiz ifade olamaz; (4) sayfaların kaynak koduna erişilebilmeli; (5) ana sayfa, resmî ilan kategori sayfası ve künyede geçiş reklamı yasak; (6) ana sayfa başka alan adına yönlendirilemez; (7) yanıltıcı yönlendirme yasak, dış siteye çıkışta geçiş sayfası zorunlu; (8) birden çok sürüm ya da adres varsa canonical belirtilmeli; (9) DDoS gibi ani trafik artışlarında CAPTCHA kullanılmalı.
- **Md. 5 BİK Analitik:** gazetecilikle ilgisiz alt alanlar dışındaki tüm sayfalarda `<head>` içinde, diğer ölçüm kodlarından önce ve kesintisiz bulunmalı; değiştirilemez, kısaltılamaz; bir sayfada birden çok kez yer alamaz; alan adı, barındırma ya da CMS kaynaklı arızalardan yayıncı sorumludur.
- **Md. 6 İçerik meta etiketleri:** `<meta name="title">` (h1 ile aynı), `<meta name="description">` (h2 ile belirtilen açıklama), `<meta name="datePublished" content="2019-09-27T11:55:00+0300">` ve `dateModified` (ISO-8601), `<meta name="url">` (esas link), `<meta name="articleSection">` değerleri: `news`, `columnist`, `resmiilan`, `reklam`, `haberreklam`, `video`, `gallery`. (2) ilk yayın tarihi (`datePublished`) değiştirilemez. (3) BİK denetim IP'leri 82.222.188.222 ve 213.74.78.242 beyaz listeye alınmalı. (4) haber gövdesi benzersiz id ya da class'lı ve `property="articleBody"` olan bir kapsayıcıda olmalı, içinde haberle ilgisiz içerik bulunmamalı. (5) resmî ilan metni için de aynı şekilde `property="ilanBody"`.
- **Md. 7 Mahreç:** `<meta name="articleAuthor" content="...">`. Değer haber ya da köşe yazısı içindeki mahreçle aynı olmalı: fikir işçisi adı (ör. "AHMET YILMAZ"), ajans ("AA"), "BULTEN", "HABER MERKEZI", alıntıda kaynağın adı.
- **Md. 8 Künye:** künyenin tamamı `id="bik-kunye-main"` div'inde, metin olarak (görsel değil). Zorunlu alan id'leri: `bik-kunye-ticaret-unvani`, `-tuzel-temsilcisi`, `-yayinci`, `-sorumlu-yim`, `-yonetim-yeri`, `-telefon`, `-eposta`, `-uets`, `-yer-saglayici-unvan`, `-yer-saglayici-adres`. Bu div'lerde yalnızca ilgili veri bulunmalı. Künye adresi değişirse Kuruma yazılı bildirim yapılmalı.
- **Md. 9 Trafik:** 1 saniye ve altındaki ziyaretler sayılmaz; kodu tetiklemek için otomatik program ya da URL dizini kullanılamaz; gerçek dışı davranış (hız, tekrar oranı, yüksek sayfa görüntüleme) manipülasyon sayılır ve Yönetmelik Md. 63 uygulanır.
- **Md. 10 Site haritası:** içeriklerin son güncelleme zamanını ve tam URL'sini içeren XML site haritası zorunlu. Birden fazla harita varsa ana haritada `<sitemap>` etiketiyle dizin verilir. Haritadaki içerikler ana sayfada ya da bir kategori adresinde yayımlanmış olmalı. Kodlama UTF-8.
- **Yeni tebliğ (9 Ekim 2026 YK kararı, yürürlük 1 Ocak 2027):** adı "İnternet Haber Sitelerinin Teknik Kurallarına Dair Tebliğ" oldu. Haber ve köşe yazısı kategorileri ile ana site haritası adresi bildirimleri yazılı yöntem yerine İLANBİS üzerinden yapılacak. Birden çok site haritası günlük, haftalık ya da aylık dönemlere göre hazırlanabilecek. BİK Analitik takip kodunun kullanımı ve değiştirilmesi yeniden düzenlendi. Dinamik ve üçüncü taraf reklamların işaretlenmesi güncellendi — [Yeni Ankara](https://www.yeniankara.com.tr/guncel/internet-haber-sitelerinde-yeni-donem-bikin-teknik-kurallari-2027de-degisiyor-185723). İlan detay sayfalarının meta bilgilerinin ve site haritası kayıtlarının güncel tutulması zorunlu olacak — [yazanhaber.com.tr (BİK haberi aktarımı)](https://yazanhaber.com.tr/haber/bikten-internet-haber-sitelerinin-teknik-kurallarina-ayar-198196)
- Asgari doğrudan tekil ziyaretçi oranı %15'ten %10'a indirildi (ikincil haber kaynağı; tarihi ve bağlamı doğrulanmadı) — [Türkgün](https://www.turkgun.com/gundem/internet-haber-sitelerinin-resm-ilan-ve-reklam-icin-yol-haritasi-netlesti/346985)

### Inferences
- BİK meta adları schema.org ya da Open Graph değil, BİK'e özgü `<meta name>` etiketleri. Hangi teknoloji seçilirse seçilsin, şablon katmanı JSON-LD'nin (Google için) yanında bu düz meta etiketlerini de basabilmeli. `articleSection` için CMS'te içerik türü alanı (haber, köşe, resmî ilan, reklam, haber-reklam, video, galeri) zorunlu bir model alanı olmalı.
- `datePublished` hiçbir zaman değiştirilmemeli: veri modelinde ilk yayın zamanı değiştirilemez (immutable) bir alan olmalı. Bu, Google'ın "özgün yayın zamanı" kuralıyla da örtüşüyor (§1).
- "Kaynak koduna erişilebilir olma" ve BİK IP beyaz listesi, CDN/WAF bot korumasının BİK denetim botunu engellememesini gerektiriyor. Ama DDoS sırasında CAPTCHA zorunlu. WAF'ta istisna kuralı tasarlanmalı.
- Site haritası: BİK'in istediği tüm içeriği kapsayan XML sitemap index (1M arşiv için dönemlere bölünmüş) ve Google News'in 48 saatlik news sitemap'i iki ayrı çıktıdır; ikisi de üretilmeli. 2027 tebliği dönemsel (günlük, haftalık, aylık) bölmeye açıkça izin veriyor.
- Tek sayfa uygulaması (SPA) ya da istemci tarafında çizilen sayfalar, `articleBody` kapsayıcısı ve meta etiketlerin ilk HTML'de bulunması şartını riske atar. Sunucu tarafında çizim (SSR) ya da statik üretim pratikte zorunlu.

### Gaps
- 9 Ekim 2026 tarihli yeni tebliğin tam metni (meta etiketlerinde, özellikle `articleAuthor`'da değişiklik olup olmadığı) bulunamadı. bik.gov.tr'de yayımlandığında yeniden kontrol edilmeli.
- Kadro, trafik eşikleri ve kategori şartları (Resmî İlan ve Reklam Yönetmeliği) bu oturumda incelenmedi.
- Barındırmanın yurt içinde olmasına dair bir regülatör şartı bulunamadı. Tebliğde yalnızca yer sağlayıcının unvanını ve adresini künyede gösterme şartı var. 5651 kapsamındaki yükümlülükler (erişim engeli kararlarına uyum vb.) ayrıca araştırılmalı.
