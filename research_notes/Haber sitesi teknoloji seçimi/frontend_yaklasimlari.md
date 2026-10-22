# Haber siteleri için ön yüz (frontend) mimarileri: karşılaştırma (2024–2026)

Bağlam: Bursa Hakimiyet sitesi şu an Django sunucu şablonları, tek elle yazılmış CSS, küçük vanilla JS ve build adımı olmadan çalışıyor (liste sayfası ~56 KB ham / ~13 KB gzip HTML). Reklam (AdSense/GAM) olacak. Native mobil uygulama ayrıca planlanıyor.
Araştırma tarihi: 21 Ekim 2026. Haber sitelerine doğrudan tarama yapılmadı; yalnızca resmî ve ikincil kaynaklar kullanıldı.

**Birincil veri notu:** Aşağıdaki "teknoloji başına CWV" sayıları HTTP Archive Technology Report'un herkese açık API'sinden (`https://cdn.httparchive.org/v1/cwv?...` ve `.../v1/page-weight?...`) 21 Ekim 2026'da doğrudan çekildi. En son ay **Eylül 2026** (CrUX verisi, origin düzeyi, dünya geneli, tüm sıralamalar). Yüzdeleri `good_number / tested` oranından ben hesapladım. Arayüz: [HTTP Archive Tech Report](https://httparchive.org/reports/techreport/tech?client=mobile&tech=Astro%2CWordPress%2CGatsby%2CNext.js%2CNuxt.js&geo=ALL&rank=ALL&page=1).

---

## 1. Teknolojiye göre gerçek dünya Core Web Vitals başarı oranları

### Takeaway
Saha verisinde sunucuda HTML üreten / az JS gönderen yığınlar (Astro, Turbo/Stimulus, Drupal, Alpine.js, Django) mobilde %60–71 CWV başarısı gösterirken, tam hidrasyonlu React/Vue meta-framework'leri (Next.js %35.7, Nuxt %28.8, React Router %24.3, Remix %32.3) genel ortalamanın (%52.8) altında kalıyor. Fark ağırlıkla mobil INP ve LCP'den geliyor. Ancak bu korelasyondur: site türü ve ekip farkı (seçim yanlılığı) büyük bir etken.

### Cited Findings
**HTTP Archive Tech Report, Eylül 2026, mobil "iyi CWV" (LCP+INP+CLS üçü de iyi) — origin oranı** (kaynak: [HTTP Archive Tech Report API, cwv uç noktası](https://cdn.httparchive.org/v1/cwv?technology=Astro&geo=ALL&rank=ALL&start=2026-01-01); her teknoloji için `technology=` parametresi değiştirilerek çekildi):

| Teknoloji | CWV mobil | CWV masaüstü | Mobil origin sayısı | LCP iyi (m) | INP iyi (m) | CLS iyi (m) | TTFB iyi (m) |
|---|---|---|---|---|---|---|---|
| **Tüm web (ALL)** | **52.8%** | **60.8%** | 8.569.446 | 65.6% | 79.4% | 83.4% | – |
| Astro | 71.1% | 84.6% | 47.277 | 81.1% | 85.0% | 93.6% | 63.1% |
| Turbo (Hotwire) | 66.7% | 78.0% | 19.326 | 80.9% | 85.2% | 88.0% | 46.0% |
| Stimulus (Hotwire) | 65.9% | 68.9% | 124.940 | 74.2% | 92.0% | 89.0% | 60.7% |
| Drupal | 64.7% | 66.1% | 93.193 | 76.1% | 89.1% | 88.6% | 45.6% |
| Qwik | 62.1% | 92.5% | 1.378 (küçük örnek) | 86.7% | 72.6% | 85.6% | 81.5% |
| Alpine.js | 61.2% | 66.8% | 106.660 | 74.0% | 87.1% | 86.5% | 45.2% |
| **Django** | **60.5%** | **68.3%** | 25.809 | 72.1% | 83.7% | 89.0% | 42.4% |
| Ruby on Rails | 56.9% | 59.7% | 104.881 | 67.7% | 86.8% | 84.4% | 41.1% |
| Svelte | 53.6% | 65.7% | 92.950 | 71.4% | 75.3% | 81.9% | 60.6% |
| Laravel | 52.2% | 64.4% | 97.363 | 68.0% | 77.6% | 83.0% | 40.8% |
| SvelteKit | 48.3% | 63.1% | 10.065 | 65.0% | 73.4% | 79.3% | 53.3% |
| WordPress | 48.3% | 53.7% | 2.658.175 | 55.4% | 90.3% | 87.3% | 22.9% |
| React (her kullanım) | 43.9% | 54.7% | 1.283.019 | 57.9% | 69.5% | 76.6% | 50.8% |
| Gatsby | 43.7% | 59.5% | 9.278 | 64.4% | 76.0% | 71.4% | 52.7% |
| Google Publisher Tag (GAM) | 38.8% | 46.9% | 202.692 | 66.9% | 61.6% | 73.0% | 56.7% |
| Google AdSense | 38.1% | 53.3% | 475.251 | 59.2% | 74.2% | 69.2% | 35.5% |
| Vue.js | 36.2% | 50.9% | 609.131 | 54.6% | 62.0% | 64.3% | 53.8% |
| **Next.js** | **35.7%** | **56.9%** | 395.345 | 53.5% | 59.7% | 73.5% | 45.6% |
| Remix | 32.3% | 53.4% | 4.547 | 44.8% | 73.5% | 74.8% | 19.2% |
| Nuxt.js | 28.8% | 42.2% | 93.276 | 47.2% | 64.1% | 60.0% | 47.0% |
| React Router | 24.3% | 39.2% | 198.071 | 37.7% | 53.3% | 63.7% | 50.5% |
| Angular | 16.5% | 27.2% | 116.296 | 33.0% | 54.6% | 45.3% | 64.3% |

- htmx ve "Hotwire" adı Tech Report'ta ayrı teknoloji olarak dönmedi (boş yanıt); Hotwire'ın parçaları olan Turbo ve Stimulus ayrı izleniyor — [HTTP Archive Tech Report API](https://cdn.httparchive.org/v1/cwv?technology=htmx&geo=ALL&rank=ALL&start=2026-01-01).
- Temmuz 2026 verisiyle bağımsız bir yazı aynı kaynaktan Astro %69.81 (38.870 origin) ve Next.js %33.89 mobil başarı bildiriyor; WordPress %49, Gatsby %45, Nuxt %28 — [Straffe Sites, "Astro vs. Next.js" (güncelleme 18 Ekim 2026)](https://straffesites.com/en/blog/astro-vs-next-js). Benim Eylül 2026 çekimimle tutarlı.
- Aynı yazı, Vercel'in de Astro'nun yüksek oranının kısmen "içerik odaklı siteler" seçiminden kaynaklandığını kabul ettiğini aktarıyor — [Straffe Sites](https://straffesites.com/en/blog/astro-vs-next-js).
- 2023 tarihli Astro raporu: Astro %50'yi aşan tek framework'tü; Next.js ~1/4, Nuxt ~1/5 site geçiyordu (**2023 verisi**, çıkar çatışması: Astro'nun kendi yayını) — [Astro, 2023 Web Framework Performance Report](https://astro.build/blog/2023-web-framework-performance-report/).
- Çelişen kaynak: justanalytics.app Next.js %58.4, Nuxt %54.1, Astro %56.8 veriyor; yöntem belirsiz ve HTTP Archive ile çelişiyor, güvenilmemeli — [justanalytics.app](https://justanalytics.app/blog/core-web-vitals-statistics-2026).
- Web Almanac 2025 (Temmuz 2025 CrUX): iyi CWV mobil %48, masaüstü %56; LCP iyi %62/%74, INP iyi %77/%97, CLS iyi %81/%72. Bölümde framework/CMS bazlı kıyas yok — [Web Almanac 2025, Performance](https://almanac.httparchive.org/en/2025/performance).
- Web Almanac 2025: anasayfalar ikincil sayfalardan daha az geçiyor (mobil %45'e karşı %56; masaüstü %47'ye karşı %61); mobil anasayfa INP iyi %80, ikincil sayfa %69 — [Web Almanac 2025, Performance](https://almanac.httparchive.org/en/2025/performance).
- Web Almanac 2025 JavaScript bölümü bu tarihte erişilebilir değil (404) — [almanac.httparchive.org/en/2025/javascript](https://almanac.httparchive.org/en/2025/javascript).

### Inferences
- Bursa Hakimiyet'in mevcut yığınına en yakın kategori olan Django origin'leri mobilde %60.5 ile genel ortalamanın ~8 puan, Next.js'in ~25 puan üstünde. Next.js'e geçmek bu istatistiklere göre CWV'yi kendiliğinden iyileştirmez; ortalama bir Next.js sitesi ortalama bir Django sitesinden belirgin biçimde kötü.
- Next.js'in masaüstü (%56.9) ile mobil (%35.7) arasındaki 21 puanlık fark, mobil CPU'da hidrasyon/JS maliyetinin (INP iyi %59.7) belirleyici olduğuna işaret ediyor. Haber trafiği ağırlıkla mobil olduğundan mobil sütun esas alınmalı.
- Django'nun zayıf noktası TTFB (%42.4 iyi) — bu sunucu/önbellek meselesidir, frontend framework meselesi değil; tam sayfa CDN önbelleğiyle çözülür (bkz. §3).
- Qwik'in mobil verisi 1.378 origin'lik küçük örnek; medyan JS ağırlığı da anormal (aşağıda), dikkatle okunmalı.

### Gaps
- htmx'e özgü CWV verisi bulunamadı (Tech Report'ta yok).
- "Yalnız haber siteleri" alt kümesi için framework bazlı CWV verisi bulunamadı; Tech Report kategori filtresi API'de denenmedi.
- Türkiye coğrafyası (`geo=Turkey`) için yalnız Next.js'e bakıldı (Ağustos 2026: mobil 5.167/16.902 ≈ %30.6) — [HTTP Archive API](https://cdn.httparchive.org/v1/cwv?technology=Next.js&geo=Turkey&rank=ALL&start=2026-08-01); diğer teknolojiler için TR kırılımı çekilmedi.

---

## 2. JavaScript yükü, hidrasyon ve INP; reklamların CWV'ye etkisi

### Takeaway
Medyan sayfa mobilde ~714 KB JS gönderiyor; Astro (399 KB) ve SvelteKit (439 KB) bunun altında, Nuxt (1.039 KB), Remix/React Router (~1 MB) üstünde. Reklam teknolojisi tek başına en ağır kalem: GPT (GAM) kullanan sitelerde medyan mobil JS 1.867 KB ve CWV başarısı %38.8. Yani Bursa Hakimiyet için JS bütçesinde asıl rakip framework değil reklam yığını olacak; framework'ün buna bir de kendi hidrasyon maliyetini eklememesi önemli.

### Cited Findings
**Medyan sayfa ağırlığı, Eylül 2026, mobil** (kaynak: [HTTP Archive Tech Report API, page-weight uç noktası](https://cdn.httparchive.org/v1/page-weight?technology=Astro&geo=ALL&rank=ALL&start=2026-09-01)):

| Teknoloji | Toplam (m) | JS (m) | JS (masaüstü) |
|---|---|---|---|
| Tüm web | 2.504 KB | 714 KB | 835 KB |
| Astro | 1.326 KB | 399 KB | 377 KB |
| SvelteKit | 1.589 KB | 439 KB | 476 KB |
| Django | 1.984 KB | 618 KB | 625 KB |
| Drupal | 2.356 KB | 650 KB | 686 KB |
| WordPress | 2.656 KB | 661 KB | 780 KB |
| Turbo | 2.481 KB | 695 KB | 688 KB |
| Next.js | 2.119 KB | 802 KB | 848 KB |
| Alpine.js | 3.058 KB | 809 KB | 937 KB |
| Google AdSense | 2.298 KB | 938 KB | 1.018 KB |
| React Router | 2.623 KB | 993 KB | 1.409 KB |
| Remix | 2.551 KB | 999 KB | 1.286 KB |
| Nuxt.js | 2.931 KB | 1.039 KB | 1.133 KB |
| Stimulus | 3.194 KB | 1.303 KB | 1.384 KB |
| Google Publisher Tag | 2.926 KB | 1.867 KB | 2.032 KB |
| Qwik | 6.591 KB | 3.073 KB | 2.921 KB (küçük örnek, anormal) |

- Web Almanac 2024: medyan JS mobilde 558 KB, masaüstünde 613 KB (önceki yıla göre +%14); mobil medyan sayfa 22 JS isteği; yüklenen JS'in ~%44'ü (mobil medyan 206 KB) kullanılmıyor (**2024 verisi**) — [Web Almanac 2024, JavaScript](https://almanac.httparchive.org/en/2024/javascript).
- Web Almanac 2024: medyan mobil sayfada 14 uzun görev, uzun görevlerde 2.366 ms; mobil TBT medyanı 1.208 ms; saha INP medyanı mobil 100 ms, p90 275 ms (eşik 200 ms) — [Web Almanac 2024, JavaScript](https://almanac.httparchive.org/en/2024/javascript).
- Web Almanac 2024: jQuery sayfaların ~%74'ünde, React %10'unda (**2024**) — [Web Almanac 2024, JavaScript](https://almanac.httparchive.org/en/2024/javascript).
- Web Almanac 2025: medyan mobil TBT 1.209 ms'den 1.916 ms'ye çıktı (+%58); mobil INP iyi oranı %74'ten %77'ye — [Web Almanac 2025, Performance](https://almanac.httparchive.org/en/2025/performance).
- Web Almanac 2025: üçüncü taraf betikler INP ve bfcache sorunlarının olası kaynağı olarak anılıyor ama reklamlar için sayısal analiz verilmiyor; `Cache-Control: no-store` kullanımı %23'e çıktı (bfcache'i engeller) — [Web Almanac 2025, Performance](https://almanac.httparchive.org/en/2025/performance).
- web.dev: reklamlar "web'deki yerleşim kaymalarının en büyük katkıcılarından biri"; çözüm `min-height` veya `aspect-ratio` ile yer ayırmak, reklam gelmezse alanı çökertmemek ("ayrılan alanı kaldırmak, içerik eklemek kadar CLS yaratabilir"), viewport'un üstüne yakın enjeksiyondan kaçınmak; iframe içi kaymalar Web API'leriyle ölçülemez ama CrUX'te görünür — [web.dev, Optimize CLS](https://web.dev/articles/optimize-cls).
- Contexte (Django tabanlı SaaS) React'ten Django şablonları + htmx'e geçişte: kod 21.500 → 7.200 satır (%67), JS bağımlılığı 255 → 9, build süresi 40 sn → 5 sn, ilk yükte etkileşime hazır olma süresi ~%50–60 iyileşme (kendi beyanı, DjangoCon 2022; yazarlar her uygulamada bu sonuçları beklemediklerini, içerik ağırlıklı uygulamada kazanç sağlandığını belirtiyor) — [htmx.org, "A Real World React -> htmx Port"](https://four.htmx.org/essays/a-real-world-react-to-htmx-port).
- OpenUnited (Django) React → htmx geçişinde %61 satır azalması (31.237 → 12.044) — [htmx.org, "Another Real World React -> htmx Port"](https://four.htmx.org/essays/another-real-world-react-to-htmx-port.md).

### Inferences
- Mevcut Bursa Hakimiyet HTML'i (~13 KB gzip) ve küçük vanilla JS'iyle, sayfanın JS ağırlığının neredeyse tamamı reklam yığınından gelecektir. GPT kullanan sitelerin mobil INP iyi oranı (%61.6) tüm webden (%79.4) ~18 puan düşük; Next.js'in kendi INP oranı (%59.7) da benzer düzeyde. İkisi üst üste binerse mobil INP riski katlanır (çıkarım; iki kümenin kesişimi ölçülmedi).
- Haber sayfası büyük ölçüde okunur içerik (statik metin + birkaç etkileşimli parça); bu, hidrasyon gerektirmeyen yaklaşımların (sunucu şablonu + progressive enhancement, ya da Astro adaları) tasarım hedefine birebir uyuyor.
- Reklam CLS'i framework'ten bağımsızdır; her yaklaşımda reklam yuvaları için sabit yükseklik/aspect-ratio ve "reklam yoksa yer tutucu" kuralı gerekir.

### Gaps
- Reklam yığınının CWV etkisini framework'ten ayıran kontrollü bir çalışma bulunamadı (GPT/AdSense ∩ framework kesişimi ölçülmedi).
- Next.js App Router (RSC) ile Pages Router arasında saha verisi ayrımı bulunamadı; Tech Report ikisini tek "Next.js" altında topluyor.

---

## 3. Önbellek modelleri ve "son dakika saniyeler içinde görünmeli"

### Takeaway
Her yaklaşım aynı temel mekanizmaya iner: HTML'i CDN/ters vekilde kısa `s-maxage` + `stale-while-revalidate` ile önbelleklemek ve yayında hedefli temizleme (purge/revalidate) yapmak. Next.js bunu ISR/`revalidateTag` ile framework içine alıyor ama kendi sunucunuzda çok örnekli çalışınca paylaşımlı önbellek (Redis) ve etiket koordinasyonu kurmanızı istiyor. Django + nginx/CDN aynı sonucu framework'süz verir.

### Cited Findings
- Next.js ISR, `Cache-Control: s-maxage=<revalidate>, stale-while-revalidate` başlığı koyar; CDN/ters vekilin bu yönergelere ve cache-key değişkenliğine uyması gerekir, yoksa yanıtlar CDN'i atlayabilir veya istemci tarafı gezinmede bayat/uyumsuz varyant sunulabilir — [Next.js Docs, Self-Hosting (güncelleme 15 Ekim 2026)](https://nextjs.org/docs/app/guides/self-hosting).
- Next.js: ISR ve sayfa önbelleği varsayılan olarak her sunucu örneğinin yerel diskinde tutulur; çok örnekte (Kubernetes vb.) her pod'un ayrı kopyası olur, özel `cacheHandler` (Redis/S3) gerekir; varsayılan olarak `revalidateTag()` yalnız çağrıldığı örnekte önbelleği geçersiz kılar, diğerleri "bağımsızca fark edene kadar" bayat içerik sunar; koordinasyon için `refreshTags()` uygulanmalı — [Next.js Docs, Self-Hosting](https://nextjs.org/docs/app/guides/self-hosting).
- Next.js: dinamik API kullanan sayfalar `private, no-cache, no-store` başlığı alır (CDN'de önbelleklenmez); tamamen ön-render edilen sayfalar `public` olur — [Next.js Docs, Self-Hosting](https://nextjs.org/docs/app/guides/self-hosting).
- Next.js 16: Cache Components (`cacheComponents: true`) ile varsayılan dinamik, önbellek `'use cache'` direktifiyle açıkça seçiliyor; `revalidateTag` ikinci argüman olarak cache-life profili alıyor; `updateTag` yalnız Server Actions'ta "read-your-writes" sağlıyor (ikincil kaynaklar) — [noqta.tn rehberi](https://noqta.tn/en/tutorials/nextjs-16-cache-components-use-cache-guide-2026), [certificates.dev](https://certificates.dev/blog/cache-components-in-nextjs); resmî sayfa: [Next.js Docs, Revalidating](https://www.nextjs.org/docs/app/getting-started/revalidating).
- Next.js streaming/PPR, nginx'te tamponlamanın kapatılmasını (`X-Accel-Buffering: no`) ve uçtan uca chunked/HTTP2 desteğini gerektiriyor; yoksa PPR'nin TTFB avantajı kaybolur — [Next.js Docs, Self-Hosting](https://nextjs.org/docs/app/guides/self-hosting).
- Washington Post seçim ekibi 2022 ara seçimleri öncesi Next.js + Vercel'e geçti; önceki özel "revalidation pipeline"ını pahalı ve ayarlaması zor buluyordu; 52 sonuç sayfasında 1.000+ yarış (satıcı yayını, bağımsız doğrulama yok; **2022–2023**) — [Vercel, Washington Post vaka çalışması](https://vercel.com/blog/washington-post-next.js-vercel-engineering-at-the-speed-of-breaking-news).
- Astro server islands: `server:defer` ile bileşen ayrı rotaya bölünür, sayfa kabuğu fallback ile hemen gelir; ada verisi GET ile istenir, böylece standart `Cache-Control` uygulanabilir (URL 2048 baytı aşarsa POST'a düşer, tarayıcı önbelleklemez); bir adapter (sunucu) gerektirir; ana içeriğin daha agresif önbelleklenmesine izin verir — [Astro Docs, Server Islands](https://docs.astro.build/en/guides/server-islands/).

### Inferences
- "Son dakika saniyeler içinde" hedefi için en basit ve en sağlam yol: Django görünümleri `Cache-Control: public, s-maxage=30–60, stale-while-revalidate=...` döner; nginx `proxy_cache` veya bir CDN önünde durur; panelde "yayınla" anında ilgili URL'ler (anasayfa, kategori, haber) hedefli olarak temizlenir. Bu, Next.js ISR'nin yaptığının framework'süz karşılığıdır ve tek sunucuda Redis/etiket koordinasyonu gerektirmez (çıkarım; Django/nginx belgeleri bu turda çekilmedi).
- Next.js'in avantajı (etiket tabanlı revalidate API'si) ancak Vercel benzeri yönetilen platformda kurulum maliyetsizdir; kendi sunucumuzda aynı güvenilirlik için ek altyapı gerekir.
- Kişiselleştirilmiş parçalar (giriş yapmış okur, hava durumu, döviz) Astro server islands benzeri bir "kabuğu önbellekle, parçayı ayrıca getir" deseniyle çözülebilir; Django'da aynı desen küçük bir `fetch`/htmx `hx-trigger="load"` ile kurulur.

### Gaps
- Nuxt (`routeRules` SWR/ISR) ve SvelteKit (ISR'nin yalnız Vercel adapter'ında olması) ayrıntıları bu turda birincil kaynaktan doğrulanamadı.
- Haber sitelerinde yayın-görünme gecikmesine (publish-to-visible latency) dair ölçülmüş, framework karşılaştırmalı bir kaynak bulunamadı.

---

## 4. SEO: taranabilirlik, Google'ın JS render rehberi, yapılandırılmış veri

### Takeaway
Google JS'i render edebiliyor ama süreç iki aşamalı ve kuyruklu; Google'ın kendisi sunucu tarafı/ön-render'ı "hâlâ çok iyi bir fikir" diye öneriyor. Sunucuda tam HTML üreten her yaklaşım (Django şablonu, Next.js SSR/SSG, Astro, Nuxt SSR, SvelteKit SSR) SEO açısından eşdeğerdir; risk yalnız istemci tarafı render'a (CSR/SPA) bağlı içerikte doğar.

### Cited Findings
- Google JS uygulamalarını üç aşamada işler: tarama, render, dizinleme; sayfa render kuyruğunda "birkaç saniye kalabilir, ama daha uzun sürebilir" — [Google Search Central, JavaScript SEO basics](https://developers.google.com/search/docs/crawling-indexing/javascript/javascript-seo-basics).
- "Sunucu tarafı veya ön-render hâlâ çok iyi bir fikirdir, çünkü sitenizi kullanıcılar ve tarayıcılar için hızlandırır"; "tüm botlar JavaScript çalıştıramaz" — [Google Search Central, JavaScript SEO basics](https://developers.google.com/search/docs/crawling-indexing/javascript/javascript-seo-basics).
- Google bağlantıları yalnız `href` nitelikli `<a>` öğeleriyse keşfeder; SPA'da History API kullanılmalı, içerik için fragment (`#`) kullanılmamalı — [Google Search Central, JavaScript SEO basics](https://developers.google.com/search/docs/crawling-indexing/javascript/javascript-seo-basics).
- JSON-LD JavaScript ile üretilip enjekte edilebilir, ama test edilmesi öneriliyor — [Google Search Central, JavaScript SEO basics](https://developers.google.com/search/docs/crawling-indexing/javascript/javascript-seo-basics).
- Vercel'in 100.000+ Googlebot isteği analizinde tarama–render gecikmesi medyanı ~10 saniye, kuyruk uzun (ikincil aktarım) — [blckalpaca.at](https://blckalpaca.at/en/knowledge-base/seo-geo/technical-seo/javascript-seo-rendering-and-indexing).
- "Dinamik render" Google'ın sayfasında yalnızca "geçici çözüm" (workaround) olarak anılıyor; kullanımdan kaldırılma tarihi konusunda ikincil kaynaklar çelişiyor (2022 mi 2025 mi) — [Google Search Central, JavaScript SEO basics](https://developers.google.com/search/docs/crawling-indexing/javascript/javascript-seo-basics); [blckalpaca.at](https://blckalpaca.at/en/knowledge-base/seo-geo/technical-seo/javascript-seo-rendering-and-indexing).

### Inferences
- Bursa Hakimiyet'in mevcut Django şablonları zaten tam HTML (NewsArticle JSON-LD dâhil sunucuda basılabilir) ürettiği için SEO açısından bir framework'e geçişin getirisi yok; yalnızca risk (yanlış yapılandırılmış CSR, `<a>` olmayan gezinme) eklenebilir.
- Google News/Discover gibi hız duyarlı yüzeylerde ilk HTML'de içeriğin olması, render kuyruğuna bağımlılığı ortadan kaldırır.

### Gaps
- Google News'e özgü JS render davranışı için resmî belge bu turda çekilmedi.
- Bing/Yandex gibi Türkiye'de de kullanılan diğer motorların JS render kapasitesine dair güncel resmî kaynak bulunamadı.

---

## 5. Tek kişilik ekip için geliştirici deneyimi ve bakım yükü (sürüm değişimi, bağımlılık, güvenlik)

### Takeaway
2024–2025'te React/Next.js ekosistemi iki kritik (CVSS 9.1 ve 10.0) ve birkaç yüksek önemde açık yaşadı; RSC açığı (React2Shell) aktif olarak sömürüldü ve ilk yamalar eksik çıktı, yani "bir kez yama" yetmedi. Remix → React Router v7 birleşmesi ve ardından React'siz Remix 3 kararı gibi yön değişimleri, tek kişilik bir ekibe sürekli göç maliyeti yükler. Build'siz Django + vanilla JS yığınında bu yüzeyin büyük kısmı yoktur.

### Cited Findings
- **CVE-2025-29927 (Mart 2025, CVSS 9.1):** Next.js middleware'de yetkilendirme atlatma; `x-middleware-subrequest` başlığıyla middleware tamamen atlanabiliyor; 12.3.5, 13.5.9, 14.2.25, 15.2.3 öncesi etkilenmiş; kendi sunucusunda `next start`/`output: 'standalone'` kullananlar acil güncellemeli; Vercel ve Netlify'da barındırılanlar etkilenmedi — [Snyk](https://snyk.io/blog/cve-2025-29927-authorization-bypass-in-next-js-middleware/), [Fastly](https://fastly.com/blog/cve-2025-29927-authorization-bypass-in-next-js), [GitLab Advisory DB](https://advisories.gitlab.com/npm/next/CVE-2025-29927/), [Security Affairs](https://securityaffairs.com/posts/next-js-react-framework-critical-issue). Etkilenen sürüm aralığı veritabanları arasında farklı listeleniyor — [CIRCL](https://vulnerability.circl.lu/vuln/CVE-2025-29927); [CERT-DK](https://vulnerability.cert.dk/vuln/cve-2025-29927).
- **CVE-2025-49826 (Temmuz 2025):** Next.js 15.0.4-canary.51 – 15.1.8 arasında önbellek zehirlenmesi; statik sayfalar için HTTP 204 yanıtı önbelleklenip tüm kullanıcılara sunulabiliyordu; Vercel müşterileri etkilenmedi — [Fluid Attacks DB](https://db.fluidattacks.com/adv/npm/next/CVE-2025-49826).
- **CVE-2025-55182 "React2Shell" (3 Aralık 2025, CVSS 10.0):** React Server Components'te güvensiz serileştirme çözme; kimlik doğrulamasız uzaktan kod çalıştırma; RSC destekleyen uygulamalar "kutudan çıktığı gibi" muhtemelen savunmasız; React 19.0, 19.1.0, 19.1.1, 19.2.0 ve Next.js 15.x/16.x etkilendi; CISA KEV listesine alındı (aktif sömürü) — [Rapid7](https://rapid7.com/blog/post/etr-react2shell-cve-2025-55182-critical-unauthenticated-rce-affecting-react-server-components), [Tenable](https://www.tenable.com/blog/react2shell-cve-2025-55182-react-server-components-rce), [NetSPI](https://www.netspi.com/?p=31134).
- İlk React2Shell yaması eksikti; 19.0.2, 19.1.3, 19.2.2 hâlâ savunmasız kaldı — [Zscaler](https://www.zscaler.com/jp/blogs/security-research/react2shell-remote-code-execution-vulnerability-cve-2025-55182).
- **11 Aralık 2025:** iki ek RSC açığı — CVE-2025-55184 (DoS, yüksek; App Router uç noktasında sonsuz döngüyle sunucuyu kilitleme) ve CVE-2025-55183 (kaynak kod ifşası, orta; Server Function'ların derlenmiş kodu ve içine gömülü sırlar sızabilir) — [Next.js Blog, Security Update 2025-12-11](https://nextjs.org/blog/security-update-2025-12-11).
- 11 Aralık yamaları da eksik çıktı; CVE-2025-67779 ile yeni yamalar yayınlandı, o aralıkta yama yapanların yeniden güncellemesi gerekti — [Netlify Changelog](https://www.netlify.com/changelog/2025-12-11-action-required-two-more-react-nextjs-vulns.md).
- Remix ekibi Mayıs 2024'te Remix'in React Router'a katılacağını, planlanan Remix v3'ün React Router v7 olarak çıkacağını duyurdu (v7: Aralık 2024) — [Remix Blog, Merging Remix and React Router](https://remix.run/blog/merging-remix-and-react-router), [Wikipedia, React Router](https://en.wikipedia.org/wiki/React_Router).
- Mayıs 2025'te Remix v3 duyuruldu: React üzerine kurulu değil, özel bir bileşen modeli kullanacak — [Appwrite blog](https://appwrite.io/blog/post/remix-3-whats-changing-and-why-it-matters.md), [Wikipedia, React Router](https://en.wikipedia.org/wiki/React_Router).
- Next.js 16'da önbellek modeli değişti (örtük → `'use cache'` ile açık; `experimental.ppr` yerine `cacheComponents`) — [noqta.tn](https://noqta.tn/en/tutorials/nextjs-16-cache-components-use-cache-guide-2026).
- Contexte örneği: React yığınında 255 JS bağımlılığı vardı, htmx'e geçişte 9'a indi — [htmx.org](https://four.htmx.org/essays/a-real-world-react-to-htmx-port).

### Inferences
- Tek kişilik ekip için RSC/Next.js, "framework sunucusu"nu internete açık bir saldırı yüzeyi hâline getiriyor: 2025'te en az dört ayrı Next.js/RSC açığı ve iki "yaman eksik, tekrar yamala" dalgası oldu. Bunları takip etmek sürekli bir operasyon yükü.
- Django'nun kendi güvenlik takvimi zaten sürdürülüyor; ek bir Node/React yığını, ikinci bir güvenlik takvimi ve ikinci bir bağımlılık ağacı demek.
- htmx/Alpine.js gibi tek dosyalık kütüphaneler vendored olarak (build'siz) eklenebilir; bu, mevcut "build adımı yok" düzenini bozmaz.

### Gaps
- Next.js, Astro, Nuxt, SvelteKit için tipik bir başlangıç projesindeki geçişli (transitive) bağımlılık sayısını karşılaştıran güvenilir bir kaynak bulunamadı.
- Astro, Nuxt, SvelteKit ve Qwik'in 2024–2026 güvenlik danışmalarının sayımı bu turda yapılmadı (GitHub Advisory DB'de ayrı ayrı bakılmalı).
- React 19'un kırıcı değişiklikleri (ref, `propTypes` kaldırılması vb.) için resmî geçiş rehberi bu turda çekilmedi.
- Remix 3'ün 2026'da yayımlanıp yayımlanmadığı doğrulanamadı.

---

## 6. Barındırma: Node sunucusu / edge platformu mu, düz nginx mi; bağımlılık (lock-in)

### Takeaway
Next.js kendi sunucunuzda çalışır ama bir Node sunucusu (`next start`) ve önünde nginx gerekir; ISR/önbellek, çok örnekte Redis + etiket koordinasyonu + şifreleme anahtarı + deploymentId gibi ek yapılandırma ister. Static export bu özelliklerin bir kısmını (Proxy/middleware) kaybeder. Astro statik çıktıda düz nginx'le çalışır, server islands için adapter (sunucu) gerekir. Django zaten bir uygulama sunucusu + nginx ile çalıştığı için ek çalışma zamanı getirmez.

### Cited Findings
- Next.js resmî belgesi kendi sunucusunda doğrudan internete açmak yerine nginx gibi bir ters vekil önerir (bozuk istekler, yavaş bağlantı saldırıları, boyut limiti, hız sınırlama için) — [Next.js Docs, Self-Hosting](https://nextjs.org/docs/app/guides/self-hosting).
- Proxy (eski middleware) `next start` ile çalışır, static export ile desteklenmez — [Next.js Docs, Self-Hosting](https://nextjs.org/docs/app/guides/self-hosting).
- Çok sunuculu kurulumda tüm örnekler aynı `NEXT_SERVER_ACTIONS_ENCRYPTION_KEY`'i kullanmalı, yoksa "Failed to find Server Action" hataları; sürüm kayması (version skew) için `deploymentId` gerekir — [Next.js Docs, Self-Hosting](https://nextjs.org/docs/app/guides/self-hosting).
- `next/image` optimizasyonu glibc Linux'ta aşırı bellek kullanımını önlemek için ek yapılandırma isteyebilir — [Next.js Docs, Self-Hosting](https://nextjs.org/docs/app/guides/self-hosting).
- Next.js 16'da Build Adapters API alfa aşamasında (`experimental.adapterPath`) — [Appwrite blog](https://vibes.appwrite.io/blog/post/everything-new-in-nextjs16); resmî referans [Next.js Docs, Self-Hosting → Deployment Adapter API](https://nextjs.org/docs/app/guides/self-hosting).
- CVE-2025-29927 ve CVE-2025-49826 Vercel'de barındırılanları etkilemedi, kendi sunucusunda barındıranları etkiledi — [Snyk](https://snyk.io/blog/cve-2025-29927-authorization-bypass-in-next-js-middleware/), [Fluid Attacks](https://db.fluidattacks.com/adv/npm/next/CVE-2025-49826).
- Astro server islands bir adapter (yani sunucu tarafı çalışma zamanı) gerektirir — [Astro Docs, Server Islands](https://docs.astro.build/en/guides/server-islands/).
- Topluluk Redis cache handler'ları (ör. `@trieb.work/nextjs-turbo-redis-cache`, `@mrjasonroy/cache-components-cache-handler`) resmî belgede listeleniyor — [Next.js Docs, Self-Hosting](https://nextjs.org/docs/app/guides/self-hosting), [GitHub, cache-components-cache-handler](https://github.com/mrjasonroy/cache-components-cache-handler).

### Inferences
- "Kendi sunucunda barındırınca daha çok açıktan etkilenme, Vercel'de daha az" deseni pratikte bir lock-in baskısıdır: Next.js'in en sorunsuz yolu Vercel'dir.
- Bursa Hakimiyet zaten Django + nginx + Python çalıştırıyor; Next.js eklemek ikinci bir süreç (Node), ikinci bir dağıtım ve (çok örnekte) Redis demektir. Astro statik çıktı ek süreç getirmez ama Django'nun dinamik sayfalarıyla (1 milyon haberlik arşiv, panel yayını) nasıl birleşeceği ayrı bir mimari soru olur.

### Gaps
- Vercel/Netlify'ın 2026 fiyatlandırmasıyla haber sitesi trafiği (ör. aylık on milyonlarca sayfa görüntüleme) için maliyet karşılaştırması bu turda çekilmedi.
- Nuxt (Nitro) ve SvelteKit adapter'larının kendi sunucuda barındırma kısıtlarına dair resmî belge bu turda okunmadı.

---

## 7. Erişilebilirlik etkileri

### Takeaway
Sunucu render'lı çok sayfalı (MPA) gezinmede tarayıcı sayfa başlığını, odağı ve ekran okuyucu duyurusunu kendisi yönetir. İstemci tarafı yönlendirme (SPA/soft navigation) bunu framework'e veya geliştiriciye devreder: odak yönetimi, canlı bölge duyurusu ve başlık güncellemesi elle çözülmelidir.

### Cited Findings
- Gatsby + Fable Tech Labs 2019 kullanıcı testleri: istemci tarafı yönlendirmede ekran okuyucu kullanıcıları için başlığa odak taşımak en iyi sonucu verdi; ilk düzeltmelerden sonra NVDA ve VoiceOver'da hâlâ sorunlar vardı (**2019–2020**) — [Gatsby Blog 2020](https://v2.gatsbyjs.com/blog/2020-02-10-accessible-client-side-routing-improvements), [Gatsby Blog 2019](https://v2.gatsbyjs.com/blog/2019-07-11-user-testing-accessible-client-routing), [Marcy Sutton](https://marcysutton.com/prototype-testing-accessible-clientside-routing/).
- React Router erişilebilirlik belgesi, rota değişiminde iki ana iş olarak odak yönetimini ve canlı bölge duyurusunu sayıyor — [React Router Docs, Accessibility](https://cdn.jsdelivr.net/npm/react-router@7.17.0/docs/how-to/accessibility.md).
- WCAG 2.4.2 SPA'larda her görünümde sayfa başlığının güncellenmesini bekler — [Vispero](https://vispero.com/resources/client-side-routing-accessibility/).
- Web Almanac 2025: soft navigation'lar mevcut Web Vitals'ta tam ölçülemiyor — [Web Almanac 2025, Performance](https://almanac.httparchive.org/en/2025/performance).

### Inferences
- Mevcut Django + MPA düzeni bu sorunları yapısal olarak yaşamaz. htmx/Turbo gibi kısmi sayfa değişimlerinde (ör. "daha fazla yükle") yine `aria-live` ve odak yönetimi gerekir, ama kapsam küçük ve bilinen.
- Framework seçimi erişilebilirliği doğrudan belirlemez; belirleyici olan HTML kalitesi ve gezinme modelidir.

### Gaps
- Framework bazında erişilebilirlik hata oranlarını (ör. Lighthouse a11y skoru, WebAIM Million) karşılaştıran güncel bir kaynak bu turda bulunamadı.

---

## 8. Aynı ön yüz kodunun mobil uygulamada yeniden kullanımı

### Takeaway
React web + React Native kod paylaşımı mümkündür (Expo Router, Solito) ama paylaşılan şey ağırlıkla UI bileşenleri ve iş mantığıdır; SSR/SEO odaklı Next.js sayfaları doğrudan uygulamaya taşınmaz. Ölçülmüş bir "paylaşım yüzdesi" kaynağı bulunamadı. Bir haber uygulaması için asıl paylaşılması gereken şey arayüz kodu değil, içerik API'sidir.

### Cited Findings
- Noona (Kasım 2025): 40+ ekranlı Expo uygulaması + ayrı Next.js web uygulaması kademeli olarak tek "universal" Expo uygulamasına taşındı; platforma özel kısımlar `.native.ts`/`.web.ts` varyantlarıyla ayrıldı; sonunda eski Next.js uygulaması silindi — [Expo Blog](https://expo.dev/blog/from-a-brownfield-react-native-and-next-js-stack-to-one-expo-app).
- Theodo: Next.js, Expo Router'ın sahip olmadığı SSR, server components ve daha iyi SEO desteği sunuyor; Expo Router'ın gençliği hâlâ hissediliyor — [Theodo Tech Radar](https://apps.theodo.com/en/radar/react-native).
- Expo Router web'de statik render ile SEO'yu destekliyor — [Expo Docs](https://docs.expo.dev/router/migrate/from-expo-webpack.md).
- Next.js + Expo universal uygulamalar için Solito öneriliyor (ikincil kaynak) — [PkgPulse](https://www.pkgpulse.com/guides/expo-router-vs-react-navigation-vs-solito-react-native-2026).
- "%80 kod paylaşımı" iddiası yalnızca bir forum gönderisinde hedef olarak geçiyor, ölçüm değil — [SuperTokens community](https://community.supertokens.com/t/9838743/hey-all-so-i-m-working-on-a-next-and-expo-universal-app-basi?t=v2).
- The Guardian'ın `dotcom-rendering` deposu hem theguardian.com'u hem "canlı uygulamalardaki içeriği" render ediyor (yani web render katmanı uygulama içi makale görünümlerine de hizmet ediyor) — [GitHub, guardian/dotcom-rendering](https://github.com/guardian/dotcom-rendering).

### Inferences
- Haber uygulamalarında makale gövdesi sıklıkla web görünümü/HTML olarak gösterilir (Guardian örneği bu yönde); bu durumda iyi bir sunucu render'lı HTML şablonu, React Native ile kod paylaşımından daha doğrudan bir yeniden kullanım sağlar (çıkarım).
- Mobil uygulamanın Django'dan JSON API ile beslenmesi, web ön yüz teknolojisinden bağımsızdır; web için React seçmek mobil uygulamayı ancak uygulama da React Native ile yazılırsa ve UI'ın web'e özgü olmayan kısmı büyükse kazandırır.

### Gaps
- Haber uygulamalarında React web ↔ React Native paylaşım oranını ölçen bir vaka çalışması bulunamadı.

---

## 9. Yaklaşımlara göre haber sitesi örnekleri

### Takeaway
Büyük haber kuruluşlarında Next.js kullanımı satıcı (Vercel) vaka çalışmalarıyla belgeli; sunucu render + kısmi etkileşim (ada benzeri) desenini kendi geliştirdikleri altyapıyla uygulayanlar da var. Bağımsız (satıcı olmayan) performans kanıtı zayıf.

### Cited Findings
- **Next.js:** Washington Post (seçim sayfaları, 2022) — [Vercel](https://vercel.com/blog/washington-post-next.js-vercel-engineering-at-the-speed-of-breaking-news); Minnesota Star Tribune (geçiş 3 ayda tamamlandı) ve RealClearPolitics — [Vercel, "Break the news, not the site"](https://vercel.com/customers/break-the-news-not-the-site). Hepsi satıcı yayını; bağımsız CWV kanıtı bulunamadı.
- **Özel sunucu render katmanı:** The Guardian, theguardian.com ve uygulama içeriğini kendi `dotcom-rendering` servisiyle (Node, Docker, pnpm) render ediyor — [GitHub, guardian/dotcom-rendering](https://github.com/guardian/dotcom-rendering).
- **Django + htmx (haber değil, içerik ağırlıklı SaaS):** Contexte — [htmx.org](https://four.htmx.org/essays/a-real-world-react-to-htmx-port).
- **Islands genel:** Preact ve Eleventy `is-land` framework'ten bağımsız kısmi hidrasyon uygulamaları sunuyor — [Preact Blog, Simplifying Islands Architecture](https://preactjs.com/blog/simplifying-islands-arch), [11ty is-land](https://www.11ty.dev/docs/plugins/is-land/).
- Mobil performans açısından Next.js sitelerinin zayıflığına dair 2022 tarihli bir analiz mevcut (**2022**) — [Web Performance Calendar 2022](https://calendar.perfplanet.com/2022/mobile-performance-of-next-js-sites/).

### Inferences
- Bursa Hakimiyet ölçeğindeki (yerel, tek geliştirici) bir gazete için Washington Post vakası doğrudan emsal değil: oradaki kazanç, büyük bir ekibin özel revalidation altyapısını Vercel'e devretmesinden geliyor.

### Gaps
- Guardian'ın Preact/islands kullandığı bilgisi bu turdaki README'de doğrulanamadı (README React/Preact/islands'tan bahsetmiyor).
- Astro, Nuxt, SvelteKit, Qwik, Hotwire ve htmx kullanan haber sitelerine dair birincil/ikincil kaynaklı örnek bulunamadı (haber sitelerine doğrudan tarama yasak olduğu için teknoloji tespiti yapılmadı).
- Türk haber sitelerinin ön yüz teknolojilerine dair kaynak bulunamadı.

