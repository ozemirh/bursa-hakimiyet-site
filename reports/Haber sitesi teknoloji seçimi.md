# Django'yu koruyun, önbelleği kurun, API'yi ekleyin

Bursa Hakimiyet için en iyi teknoloji seçimi, büyük ölçüde elde zaten olan yığındır. Arka uçta (backend: veritabanıyla konuşan, sayfaları ve verileri üreten sunucu tarafı) **Python + Django kalmalı**; 5.2 LTS sürümü Nisan 2028'e kadar destek alıyor, Nisan 2027'de 6.2 LTS'ye geçilmeli. Ön yüzde (frontend: okurun tarayıcısında görünen ve çalışan katman) **sunucuda üretilen HTML + elle yazılmış CSS + az miktarda sade JavaScript** sürmeli; yalnızca "daha fazla yükle" ya da canlı blog gibi parçalarda, derleme adımı gerektirmeyen htmx benzeri küçük bir kütüphane eklenebilir. Önüne etiketle temizleme (tag purge) yapabilen bir CDN (içerik dağıtım ağı: sayfaların kopyalarını okura yakın sunuculardan veren hizmet) konmalı. Mobil uygulama için ayrı bir sistem kurulmamalı: aynı Django projesine Django Ninja ile sürümlü bir REST API (uygulamanın veri istediği adresler) ve Firebase üzerinden anlık bildirim eklenmeli. Bunun gerekçesi sadakat değil, veri. Eylül 2026 saha ölçümlerinde Django siteleri mobilde **%60,5**, Next.js siteleri **%35,7** oranında Core Web Vitals sınavını geçiyor. Önbellek arkasında çerçeve hızı farkı önemini yitiriyor. PostgreSQL'in Türkçe tam metin aramasını en eksiksiz kullanan çerçeve Django. Hazır haber platformlarının kimi PostgreSQL'i hiç desteklemiyor, kimi ise yerel bir gazetenin bütçesini katbekat aşıyor. Göç maliyeti tarafında da tablo açık: 54 bin satırlık kod, 1.671 test ve 1,04 milyon haberin adres uyumu yeniden yazılmak zorunda kalır. Asıl risk teknoloji değil, kodun tek bir kişiye bağlı olması. Bu risk de çerçeve değiştirerek değil, test kapsamı, dar bağımlılık ve belgelemeyle yönetilir.

> **Kaynak etiketleri.** Her önemli iddianın yanında kaynağın türü ve yılı var. **[birincil]**: resmî belge, standart metni, yayıncının kendi deposu ya da doğrudan çekilmiş ölçüm verisi. **[ikincil]**: basın, bağımsız derleme, W3Techs gibi dış tespit siteleri. **[satıcı iddiası]**: ürünü satan ya da uygulayan firmanın kendi yayını, bağımsız doğrulaması yok. **[zayıf]**: tek kaynak, forum ya da tarihsiz içerik. Araştırma 21 Ekim 2026'da yapıldı. Haber sitelerinin kendisi taranmadı.

## Haber sitesinin şartları çerçeve seçmiyor, sunucuda hazır HTML istiyor

Teknoloji tartışmasından önce, bir haber sitesinin ne yapabilmesi gerektiğini netleştirmek gerekiyor. Ortaya çıkan tablo şu: Google, Basın İlan Kurumu (BİK) ve reklam şartlarının neredeyse tamamı, sayfanın sunucuda eksiksiz HTML olarak üretilmesini ve önbellekle (cache: bir kez üretilen sayfanın kopyasının saklanıp tekrar verilmesi) hızlı dağıtılmasını varsayıyor. Bu şartları karşılamayan tek mimari, içeriği okurun tarayıcısında JavaScript'le sonradan çizen tek sayfa uygulamasıdır (SPA). Geri kalan her ciddi seçenek bu şartları karşılayabilir. Bu yüzden şartlar bir çerçeveyi öne çıkarmıyor, yalnızca bir mimariyi eliyor.

**Google News ve Discover için ayrıca başvurmak gerekmiyor.** Dizine eklenen ve politikalara uyan içerik Discover'a otomatik olarak uygun sayılıyor. Teknik beklenti somut: manşet görseli en az **1200 px genişlikte**, 300 bin pikselin üzerinde ve 16:9 oranında olmalı, sayfada `max-image-preview:large` ayarı bulunmalı ([Google Search Central: Discover](https://developers.google.com/search/docs/appearance/google-discover), [birincil], sayfa 2026-03-09'da güncellendi). Arc XP, bu önerinin "aşırı büyük görsel sunmayın" ilkesiyle çeliştiğini belirtip büyük görseli yalnızca paylaşım görseline (`og:image`) vermeyi öneriyor ([Arc XP FAQ](https://docs.arcxp.com/en/products/general/faq--google-discover.html), [satıcı belgesi]). Pratikteki sonucu şu: görsel hattı her fotoğraftan en az iki boyut üretmeli. Google News için ayrı bir haber site haritası (news sitemap) gerekiyor. Bu dosya **en fazla 1.000 adres** içerebilir, yalnızca son iki günün haberlerini taşır ve özgün yayın zamanını kullanır ([Google: News sitemaps](https://developers.google.com/search/docs/advanced/sitemaps/news-sitemap?hl=en), [Google News Publisher Help](https://support.google.com/news/publisher/answer/74288), [birincil]). Mart 2025'ten beri Google News yayın sayfalarını tamamen otomatik üretiyor ve Publisher Center'a gönderilen RSS akışlarını artık kullanmıyor ([Google News Publisher Center Help](https://support.google.com/news/publisher-center/answer/15898024), [birincil], 2025). Bu değişiklikle görünürlük tamamen site sinyallerine bağlandı: site haritası, yapılandırılmış veri ve politika uyumu.

**AMP artık bir seçim ölçütü değil.** AMP, Google'ın hızlı mobil sayfa biçimidir ve ayrı bir şablon seti gerektirir. Top Stories (Google'daki "Öne çıkan haberler" bandı) için AMP şartı **Mayıs 2021'de kaldırıldı** ([Search Engine Land, 2021](https://searchengineland.com/will-publishers-drop-amp-when-its-no-longer-a-requirement-for-top-stories-335612), [ikincil]). Güncel Discover belgesi de AMP'yi büyük görsel için `max-image-preview:large` ayarının yalnızca bir alternatifi olarak anıyor. 2024–2026 için AMP'yi öneren resmî bir Google belgesi bulunamadı. Yeni bir sistemde ikinci bir AMP şablon setinin bakımını üstlenmenin karşılığı yok.

**Core Web Vitals sıralamada kullanılıyor, ama tek başına sıra belirlemiyor.** Core Web Vitals (CWV), Google'ın sayfa deneyimini ölçtüğü üç metrik. **LCP** ana içeriğin ne kadar sürede göründüğünü, **INP** dokunuş ya da tıklamaya ne kadar hızlı tepki verildiğini, **CLS** ise sayfanın yüklenirken ne kadar kaydığını ölçer. Google bu metriklerin "sıralama sistemlerince kullanıldığını" söylüyor, ama "tek bir sinyal yok" diye de ekliyor ([Google: Understanding page experience](https://developers.google.com/search/docs/appearance/page-experience), [birincil], 2026-09-22). INP, Mart 2024'te eski FID metriğinin yerini aldı ([Google Search Central Blog, 2023](https://developers.google.com/search/blog/2023/05/introducing-inp?authuser=1), [birincil]). Bir de Türkiye'ye özgü bir ayrıntı var. Google, sitenin itibarını üçüncü taraf içerikle sömürmeye karşı politikasını Kasım 2024'te genişletti ([Google Search Central Blog, 2024](https://developers.google.cn/search/blog/2024/11/site-reputation-abuse), [birincil]). Ağustos 2026'da elle cezayı yalnızca Avrupa Ekonomik Alanı için kaldırdı ([Search Engine Journal](https://www.searchenginejournal.com/google-updates-site-reputation-abuse-policy-removes-penalties-in-eea/), [ikincil], 2026). Türkiye bu alanın dışında olduğundan, sponsorlu içerik ve "haber-reklam" bölümlerinin açıkça ayrılması gerekiyor.

**BİK tebliği, doğrudan HTML'e yazılan şartlar koyuyor.** Resmî ilan ve reklam alan siteler için 1 Haziran 2024'te yürürlüğe giren tebliğ şunları istiyor ([BİK Tebliği, 2024](https://bik.gov.tr/storage/2024/05/Internet-Haber-Sitelerinin-Teknik-Olarak-Uymasi-Gereken-Kurallara-Dair-Usul-ve-Esaslar-Hakkinda-Teblig.pdf), [birincil]):

- Belirli `<meta>` etiketleri: `title`, `description`, `datePublished`, `dateModified`, `url`, `articleSection` ve mahreç için `articleAuthor`.
- `datePublished` değeri hiç değiştirilmemeli.
- Haber gövdesi `property="articleBody"` olan bir kapsayıcıda durmalı.
- Künye, `bik-kunye-*` kimlikli kutularda metin olarak verilmeli.
- BİK Analitik kodu `<head>` içinde, diğer ölçüm kodlarından önce bulunmalı.
- XML site haritası dizini olmalı.
- DDoS (sahte trafikle siteyi boğma saldırısı) sırasında CAPTCHA kullanılmalı.
- BİK'in denetim IP'leri (82.222.188.222 ve 213.74.78.242) beyaz listeye alınmalı.
- Ana sayfada, resmî ilan sayfasında ve künyede geçiş reklamı (interstitial) kullanılmamalı.

**9 Ekim 2026'da kabul edilen yeni tebliğ 1 Ocak 2027'de yürürlüğe girecek.** Site haritasının günlük, haftalık ya da aylık dönemlere bölünmesine izin veriyor, bildirimleri İLANBİS'e taşıyor ([Yeni Ankara](https://www.yeniankara.com.tr/guncel/internet-haber-sitelerinde-yeni-donem-bikin-teknik-kurallari-2027de-degisiyor-185723), [ikincil], 2026). Yeni tebliğin tam metni bu araştırmada bulunamadı. Meta etiketlerinde bir değişiklik olup olmadığı yayımlandığında kontrol edilmeli. Bu şartların teknoloji açısından anlamı şu: BİK etiketleri schema.org ya da Open Graph değil, BİK'e özgü. Şablon katmanı bunları Google'ın JSON-LD'sinin (sayfaya gömülen yapılandırılmış veri) yanında, sayfanın ilk HTML'inde basabilmeli. İçerik türü ve değiştirilemez ilk yayın zamanı da veri modelinde zorunlu alanlar olmalı.

**Önbellek ve CDN deseni yerleşik ve artık ucuz.** Haber sitelerinde bilinen yöntem şöyle işliyor:

- Sayfaların kopyası CDN'de uzun, tarayıcıda kısa süre tutulur.
- Bir haber yayımlandığında ya da güncellendiğinde, yalnızca ona bağlı sayfalar etiketle hedefli olarak temizlenir.
- `stale-while-revalidate` ve `stale-if-error` ayarları açılır. Böylece yenisi hazırlanırken ya da sunucu hata verdiğinde okura eski kopya gösterilir.

([Fastly Blog](https://www.fastly.com/es/blog/is-purging-still-the-hardest-problem-in-computer-science), [satıcı belgesi]). Önemli bir 2025 değişikliği var: Cloudflare etiket, önek ve alan adı bazlı temizlemeyi **tüm planlara açtı**. Daha önce bu özellik yalnızca Enterprise sözleşmesinde vardı. Temizleme 150 ms'nin altında tamamlanıyor ([Cloudflare Blog](https://blog.cloudflare.com/ko-kr/instant-purge-for-all), [satıcı iddiası], 2024 duyuru / 2025 yayın). Böylece "son dakika saniyeler içinde görünsün, deprem gecesi trafik patlamasında site ayakta kalsın" hedefi, kurumsal bir sözleşme olmadan da tek kişilik bir ekibin erişebileceği bir yere geldi. Kişiselleştirilmiş parçalar (giriş yapmış okur, hava, döviz) önbelleği bozmamalı. Bunlar sayfaya sonradan, ayrı bir adresten çekilmeli.

**Canlı blog için en basit yöntem, okurun tarayıcısının kısa aralıklarla sormasıdır.** Canlı blogun önemi küçük değil: Guardian'da toplam sayfa görüntülemelerinin yaklaşık **%15'i** canlı bloglardan geliyor ([Press Gazette](https://pressgazette.co.uk/?p=255587), [ikincil], tarih belirtilmemiş). Canlı blogda veri tek yönlü akar: sunucudan okura. Teknik seçenekler üç tane:

- **Yoklama (polling):** Tarayıcı birkaç saniyede bir "yeni bir şey var mı" diye sorar.
- **SSE (sunucu tarafından gönderilen olaylar):** Sunucu açık tutulan bir bağlantı üzerinden yeni girdileri kendisi iter.
- **WebSocket:** İki yönlü, sürekli açık bir bağlantıdır.

Yoklamada sunucu yükü okur sayısıyla doğrusal artar ([Eric Mann](https://eric.mann.blog/live-blogging-ajax-polling/), [ikincil]). Ama yanıt CDN'de 5–15 saniye önbelleklenirse sunucuya giden istek okur sayısından bağımsızlaşır. Geleneksel uygulama sunucularında her SSE bağlantısı bir işçi süreci açık tutar ([craft-live](https://packagist.org/packages/justinholtweb/craft-live), [ikincil]). Django'nun standart senkron kurulumunda da durum aynıdır. Guardian, BBC ve NYT'nin canlı blog altyapısına dair 2024–2026 tarihli birincil bir mühendislik kaynağı bulunamadı.

**Reklam ve erişilebilirlik çerçeveden bağımsız kurallar getiriyor.** Reklamlar için yapılması gerekenler ([web.dev](https://web.dev/articles/loading-ads-page-speed), [birincil], 2023):

- Her reklam alanının yeri önceden ayrılmalı.
- Reklam betikleri `async` (sayfanın geri kalanını bekletmeden) yüklenmeli.
- Ekranın altındaki alanlar okur oraya yaklaşınca yüklenmeli.
- Reklamlar 30–240 saniyeden sık yenilenmemeli.

Reklamın hangi okura gideceğini birkaç alıcı arasında tarayıcıda açık artırmayla belirleyen yöntem (header bidding), LCP'ye 200–800 ms ekliyor ([pubperf](https://www.pubperf.com/blog/ads-core-web-vitals-guide), [satıcı iddiası, doğrulanmamış]). Hukuki tarafta KVKK'nın çerez rehberi, analitik ve reklam çerezlerini açık rızaya bağlıyor. Güncel sürüm Temmuz 2025 tarihli ([KVKK](https://kvkk.gov.tr/Icerik/7353/Cerez-Uygulamalari-Hakkinda-Rehber), [birincil]). Bu, rıza vermeyen okura kişiselleştirilmemiş reklam gösterilebilmesini gerektiriyor. BİK Analitik kodunun `<head>` içinde en önde olma şartıyla KVKK rızası arasındaki ilişki bir hukukçuya sorulmalı. AB Erişilebilirlik Yasası 28 Haziran 2025'te yürürlüğe girdi, ama kapsamı e-ticaret, bankacılık ve e-kitap gibi alanlarla sınırlı ([BCLP](https://www.bclplaw.com/en-US/events-insights-news/what-is-the-european-accessibility-act-and-what-impact-will-it-have-on-your-business.html), [ikincil], 2025). Yasanın Türkiye'deki bir yerel gazeteyi doğrudan bağladığına dair kaynak bulunamadı. Yine de WCAG 2.2 AA, yani erişilebilirlik standardının orta seviyesi ([W3C](https://www.w3.org/TR/WCAG22/), [birincil], 2023), makul bir hedef.

| Şart | Kaynak (yıl) | Teknolojiden beklenen |
|---|---|---|
| Discover görseli ≥1200 px, 16:9 | Google (2026) | Görsel hattı birden çok boyut üretmeli |
| News sitemap: ≤1000 adres, son 48 saat | Google (güncel) | Yayın anında güncellenen dinamik dosya |
| BİK meta etiketleri, `articleBody`, künye kimlikleri | BİK Tebliği (2024; yenisi 1.1.2027) | İlk HTML'de sunucu tarafından basılmalı |
| `datePublished` değişmez | BİK (2024) + Google | Veri modelinde değiştirilemez alan |
| DDoS'ta CAPTCHA + BİK IP'leri beyaz listede | BİK (2024) | CDN/WAF'ta istisna kuralı |
| Etiketle önbellek temizleme | Cloudflare (2025) | Yayın olayından CDN'e otomatik çağrı |
| Reklam yerinin önceden ayrılması | web.dev (2023) | Şablonda sabit yükseklikli reklam yuvaları |
| Çerez rızası | KVKK (2022/2025) | Rızadan önce etiket yüklememe |
| AMP | Google (2021'den beri şart değil) | Gerek yok |

## Ön yüzde az JavaScript kazanıyor: Django siteleri mobilde %60, Next.js %36

### Saha verisi, sunucuda HTML üreten yığınları öne çıkarıyor

Ön yüz tartışmasının en sağlam verisi HTTP Archive'ın Technology Report'u. Bu rapor, Chrome kullanıcılarından toplanan gerçek ölçümleri (CrUX) teknolojiye göre ayırıyor. Aşağıdaki değerler 21 Ekim 2026'da raporun herkese açık API'sinden doğrudan çekildi. En son ay Eylül 2026, ölçüm site (origin) düzeyinde, dünya geneli ([HTTP Archive Tech Report](https://httparchive.org/reports/techreport/tech?client=mobile&tech=Astro%2CWordPress%2CGatsby%2CNext.js%2CNuxt.js&geo=ALL&rank=ALL&page=1), [birincil ölçüm], 2026). Yüzdeler, üç metriğin üçünde de "iyi" sonuç alan sitelerin oranı:

| Teknoloji | Yaklaşım | CWV iyi (mobil) | CWV iyi (masaüstü) | INP iyi (mobil) | Medyan JS (mobil) |
|---|---|---|---|---|---|
| Tüm web | – | %52,8 | %60,8 | %79,4 | 714 KB |
| Astro | Statik/ada | **%71,1** | %84,6 | %85,0 | 399 KB |
| Turbo (Hotwire) | Sunucu HTML + kısmi güncelleme | %66,7 | %78,0 | %85,2 | 695 KB |
| Drupal | Sunucu HTML (CMS) | %64,7 | %66,1 | %89,1 | 650 KB |
| Alpine.js | Küçük istemci kütüphanesi | %61,2 | %66,8 | %87,1 | 809 KB |
| **Django** | Sunucu HTML | **%60,5** | %68,3 | %83,7 | 618 KB |
| Ruby on Rails | Sunucu HTML | %56,9 | %59,7 | %86,8 | – |
| Laravel | Sunucu HTML | %52,2 | %64,4 | %77,6 | – |
| SvelteKit | Meta-çerçeve | %48,3 | %63,1 | %73,4 | 439 KB |
| WordPress | Sunucu HTML (CMS) | %48,3 | %53,7 | %90,3 | 661 KB |
| **Next.js** | React meta-çerçeve | **%35,7** | %56,9 | %59,7 | 802 KB |
| Remix | React meta-çerçeve | %32,3 | %53,4 | %73,5 | 999 KB |
| Nuxt | Vue meta-çerçeve | %28,8 | %42,2 | %64,1 | 1.039 KB |
| React Router | React | %24,3 | %39,2 | %53,3 | 993 KB |
| Qwik | Devam ettirilebilir | %62,1 (yalnız 1.378 site) | %92,5 | %72,6 | 3.073 KB (anormal) |
| Google Publisher Tag (GAM reklamı) | Reklam | %38,8 | %46,9 | %61,6 | **1.867 KB** |
| Google AdSense | Reklam | %38,1 | %53,3 | %74,2 | 938 KB |

Bu tablo dikkatle okunmalı. **Korelasyon gösteriyor, nedensellik değil.** Astro'yu seçenler çoğunlukla içerik siteleri yapıyor. Vercel'in de Astro'nun yüksek oranını kısmen bu seçime bağladığı aktarılıyor ([Straffe Sites](https://straffesites.com/en/blog/astro-vs-next-js), [ikincil], Ekim 2026). Aynı yazı Temmuz 2026 verisiyle Astro için %69,8, Next.js için %33,9 bildiriyor; bu, Eylül çekimiyle tutarlı. Astro'nun kendi 2023 raporu da benzer bir sıralama vermişti ([Astro, 2023](https://astro.build/blog/2023-web-framework-performance-report/), [satıcı iddiası], 2023). Yöntemi belirsiz ve HTTP Archive'la çelişen bir kaynak Next.js için %58,4 veriyor ([justanalytics.app](https://justanalytics.app/blog/core-web-vitals-statistics-2026), [zayıf]). Bu kaynağa güvenilmemeli.

Sınırlara rağmen sonuç Bursa Hakimiyet için açık. **Ortalama bir Next.js sitesi, ortalama bir Django sitesinden mobilde yaklaşık 25 puan kötü.** Next.js'in masaüstüyle mobil arasındaki 21 puanlık uçurum, telefon işlemcisinde React'ın "hidrasyon" maliyetine işaret ediyor. Hidrasyon, sunucuda üretilen sayfanın tarayıcıda JavaScript'le yeniden canlandırılmasıdır. Türkiye'deki Next.js sitelerinde oran daha da düşük: Ağustos 2026'da mobilde **%30,6** ([HTTP Archive API, geo=Turkey](https://cdn.httparchive.org/v1/cwv?technology=Next.js&geo=Turkey&rank=ALL&start=2026-08-01), [birincil ölçüm]). Haber trafiği ağırlıkla mobilden geldiği için esas alınması gereken sütun mobil sütunu. Django'nun zayıf noktası ilk baytın gelme süresi (TTFB). Django sitelerinin yalnızca %42,4'ü bu metrikte iyi. Ama bu bir ön yüz meselesi değil, sunucu ve önbellek meselesi. Tam sayfa CDN önbelleği bu sorunu doğrudan çözer. Bir haber sitesi için ayrıca şu da önemli: anasayfalar ikincil sayfalardan daha az geçiyor, mobilde %45'e karşı %56 ([Web Almanac 2025](https://almanac.httparchive.org/en/2025/performance), [birincil], 2025). Yoğun anasayfa, en çok emek isteyen sayfa olacak.

### Asıl JavaScript yükünü reklam getiriyor

Tablonun en önemli satırı bir çerçeve değil, reklam. Google Ad Manager'ın reklam etiketini (GPT) kullanan sitelerde mobilde medyan **1.867 KB JavaScript** yükleniyor ve bu sitelerin yalnızca %38,8'i CWV'yi geçiyor. INP iyi oranı tüm webden 18 puan düşük. Bursa Hakimiyet'in mevcut liste sayfası yaklaşık 13 KB sıkıştırılmış HTML. JavaScript'i de az ve sade (depo ölçümü). Bu durumda sayfadaki JavaScript'in neredeyse tamamı reklamdan gelecek. Reklam ve Next.js'in INP kayıpları üst üste binerse mobil risk katlanır. Bu iki kümenin kesişimi ölçülmedi, yani bu bir çıkarım. Reklamların yerleşim kaymasındaki payı da büyük. web.dev reklamları kaymanın "en büyük katkıcılarından biri" sayıyor. Reklam gelmediğinde ayrılan alanı kaldırmanın da kayma yarattığını vurguluyor ([web.dev: Optimize CLS](https://web.dev/articles/optimize-cls), [birincil]). Pratik ders şu: JavaScript bütçesi zaten reklama gidecek. Ön yüz teknolojisinin bu bütçeye bir de kendi hidrasyon maliyetini eklememesi gerekiyor.

### "Son dakika saniyeler içinde" her yığında aynı mekanizmaya iniyor

Next.js, "artımlı statik yeniden üretim" (ISR) ve etiketle geçersiz kılma (`revalidateTag`) özelliklerini çerçevenin içine alıyor. Ama kendi sunucunuzda birden çok kopya çalıştırdığınızda bedeli var. Resmî belgeye göre önbellek her sunucu kopyasının kendi diskinde tutuluyor. `revalidateTag` yalnızca çağrıldığı kopyada çalışıyor, diğerleri "bağımsızca fark edene kadar" eski içerik sunuyor. Bunu düzeltmek için Redis gibi paylaşımlı bir önbellek, ortak şifreleme anahtarı ve sürüm kimliği yapılandırmak gerekiyor ([Next.js Docs: Self-Hosting](https://nextjs.org/docs/app/guides/self-hosting), [birincil], Ekim 2026). Django tarafında aynı sonuç çerçeve dışında alınır: görünüm `Cache-Control: public, s-maxage=…, stale-while-revalidate=…` başlığını döner, nginx ya da CDN önbellekler, panelde "yayınla" anında ilgili adresler etiketle temizlenir. Next.js'in bu konudaki avantajı en sorunsuz biçimde Vercel'in yönetilen platformunda ortaya çıkıyor. Bu da pratikte bir platform bağımlılığı (lock-in) baskısı yaratıyor.

### React ekosistemi 2025'te tek kişilik ekibe ağır bir güvenlik yükü bindirdi

2025, Next.js ve React Server Components (RSC: React bileşenlerinin sunucuda çalışan türü) için zor bir yıl oldu. Yaşanan başlıca açıklar şunlar:

- **Mart 2025, CVE-2025-29927.** CVSS puanı (açığın ciddiyetini 10 üzerinden ölçen ölçek) 9,1. Tek bir HTTP başlığıyla Next.js'in yetki denetimini atlamak mümkündü. Kendi sunucusunda barındıranlar etkilendi, Vercel ve Netlify müşterileri etkilenmedi ([Snyk](https://snyk.io/blog/cve-2025-29927-authorization-bypass-in-next-js-middleware/), [ikincil], 2025).
- **3 Aralık 2025, "React2Shell", CVE-2025-55182.** CVSS 10,0. Kimlik doğrulaması gerektirmeden sunucuda kod çalıştırmaya izin veriyordu. CISA'nın aktif olarak sömürülen açıklar listesine girdi ([Rapid7](https://rapid7.com/blog/post/etr-react2shell-cve-2025-55182-critical-unauthenticated-rce-affecting-react-server-components), [ikincil], 2025). İlk yamalar eksik çıktı ([Zscaler](https://www.zscaler.com/jp/blogs/security-research/react2shell-remote-code-execution-vulnerability-cve-2025-55182), [ikincil]).
- **11 Aralık 2025.** İki yeni açık geldi: biri hizmet dışı bırakma, biri kaynak kod sızıntısı ([Next.js Blog](https://nextjs.org/blog/security-update-2025-12-11), [birincil]). Bunların yamaları da eksik çıktı ve bir kez daha güncelleme gerekti ([Netlify Changelog](https://www.netlify.com/changelog/2025-12-11-action-required-two-more-react-nextjs-vulns.md), [birincil]).

Yön değişiklikleri de ayrı bir yük. Remix, Mayıs 2024'te React Router'la birleşeceğini duyurdu ([Remix Blog](https://remix.run/blog/merging-remix-and-react-router), [birincil]). Bir yıl sonra Remix 3'ün React'i hiç kullanmayacağı açıklandı ([Appwrite](https://appwrite.io/blog/post/remix-3-whats-changing-and-why-it-matters.md), [ikincil], 2025). Next.js 16'da önbellek modelinin varsayılanı tersine döndü ([noqta.tn](https://noqta.tn/en/tutorials/nextjs-16-cache-components-use-cache-guide-2026), [ikincil]). Tek kişilik bir ekip için bu, Django'nun kendi güvenlik takviminin yanına ikinci bir takvim, ikinci bir bağımlılık ağacı ve internete açık ikinci bir sunucu süreci eklemek demek.

### Sunucuda HTML üreten yapıda erişilebilirlik kendiliğinden geliyor

Sayfadan sayfaya klasik geçişte tarayıcı başlığı, odağı ve ekran okuyucu duyurusunu kendisi yönetir. İstemci tarafı yönlendirmede ise bu işler geliştiriciye kalır. React Router'ın kendi belgesi de rota değişiminde odak yönetimini ve canlı bölge duyurusunu iki ana iş olarak sayıyor ([React Router Docs](https://cdn.jsdelivr.net/npm/react-router@7.17.0/docs/how-to/accessibility.md), [birincil]). Gatsby'nin 2019–2020'de yaptırdığı kullanıcı testlerinde, düzeltmelerden sonra bile NVDA ve VoiceOver ekran okuyucularında sorunlar sürüyordu ([Gatsby Blog, 2020](https://v2.gatsbyjs.com/blog/2020-02-10-accessible-client-side-routing-improvements), [birincil], 2020). Mevcut Django düzeni bu sorunları yapısı gereği yaşamıyor. Kısmi güncellemelerde ("daha fazla yükle") gereken `aria-live` ve odak işi küçük ve bilinen bir kapsamda kalıyor.

### Adaylar tek tek: hangi ön yüz yaklaşımı ne zaman anlamlı

Google, sunucu tarafında üretmenin (SSR) ya da önceden üretmenin "hâlâ çok iyi bir fikir" olduğunu söylüyor. Çünkü JavaScript'le çizilen sayfalar bir render kuyruğunda bekliyor ve "tüm botlar JavaScript çalıştıramıyor" ([Google Search Central: JavaScript SEO basics](https://developers.google.com/search/docs/crawling-indexing/javascript/javascript-seo-basics), [birincil]). Sunucuda tam HTML üreten her yaklaşım SEO açısından eşdeğer. Bu yüzden ayrım başarım, bakım ve uyum üzerinden yapılmalı.

| Yaklaşım | Ne yapar | Bursa Hakimiyet için değerlendirme |
|---|---|---|
| **Django şablonu + sade JS (mevcut)** | Sayfayı sunucuda üretir, tarayıcıya hazır gönderir | Saha verisinde %60,5. Derleme adımı yok, ek çalışma ortamı yok. **Önerilen.** |
| **+ htmx / Alpine.js** | Tek dosyalık kütüphaneyle sayfanın bir parçasını sunucudan yeniler | Derlemesiz eklenebilir. htmx'e özgü CWV verisi yok. İçerik ağırlıklı bir Django SaaS'ında React'ten htmx'e geçiş kodu %67, JS bağımlılıklarını 255'ten 9'a indirdi ([htmx.org](https://four.htmx.org/essays/a-real-world-react-to-htmx-port), [kendi beyanı], 2022). Gerekli yerlerde **önerilen.** |
| **Hotwire (Turbo/Stimulus)** | htmx'in Rails dünyasındaki karşılığı | Saha verisi iyi (%66,7). Django'yla da kullanılabilir, ama htmx'ten açık bir üstünlüğü yok. |
| **Astro** | Statik sayfa + gerektiğinde etkileşimli "adalar" | En iyi saha verisi (%71,1). Ama 1 milyon haberlik dinamik arşivle ve Django paneliyle nasıl birleşeceği ayrı bir mimari soru. Sunucu adaları bir Node adaptörü gerektiriyor ([Astro Docs](https://docs.astro.build/en/guides/server-islands/), [birincil]). Seçim haritası gibi **izole özel projeler** için uygun. |
| **Next.js** | React ile SSR/ISR, Vercel'de en kolay | Mobilde %35,7, TR'de %30,6. 2025'te birden çok kritik açık. Kendi sunucusunda önbellek koordinasyonu ek altyapı istiyor. Ayrı bir ön yüz ekibi yoksa **önerilmez.** |
| **Nuxt** | Vue ile Next.js'in karşılığı | Mobilde %28,8, medyan JS 1.039 KB. Önerilmez. |
| **SvelteKit** | Daha az JS üreten derleyici tabanlı çerçeve | JS hafif (439 KB), ama CWV %48,3. Haber örneği bulunamadı. |
| **React Router / Remix** | React tabanlı | %24,3 / %32,3. Çatallanan yol haritası. Önerilmez. |
| **Qwik** | Hidrasyonsuz "devam ettirilebilir" model | Örneklem çok küçük (1.378 site), JS ölçümü anormal. Kanıt yetersiz. |

Astro, Nuxt, SvelteKit, Qwik, Hotwire ya da htmx kullanan haber sitelerine dair kaynaklı bir örnek bulunamadı. Haber siteleri doğrudan taranmadığı için bu konuda tespit yapılamadı.

## Arka uçta hız farkı CDN arkasında kayboluyor, PostgreSQL uyumu ve destek takvimi belirleyici

### Ham hız ölçümleri büyük fark gösteriyor, ama bu ölçekte anlamsız

TechEmpower Round 23 (Şubat 2025), çerçeveleri veritabanından veri çeken aynı görev üzerinde yarıştırıyor. Bu ölçümün ORM'li (veritabanına kod içinden nesne olarak erişen katman) PostgreSQL sonuçlarını derleyen ikincil bir kaynağa göre saniyedeki istek sayıları şöyle: ASP.NET **609.966**, Go Fiber 338.096, Spring 243.639, Express 78.136, Rails 42.546, **Django 32.651**, Laravel 16.800 ([dev.to derlemesi](https://dev.to/tuananhpham/popular-backend-frameworks-performance-benchmark-1bkh), [ikincil], 2025). Bu rakamlara temkinle yaklaşmak gerekiyor. Birincil sonuç sayfası okunamadı ve Fiber ile Laravel değerleri derleyenin tahmini. TechEmpower'ın kendi blogu da sonuçların yapılandırmaya ne kadar duyarlı olduğunu gösteriyor: bir testin sonucu 5,9 binden 583'e düşmüş, yapılandırma hatası düzeltilince 14,2 bine çıkmış ([TechEmpower blog](https://www.techempower.com/blog/tag/tfb/), [birincil]). Bir Rails bakımcısı, boş istek ölçümlerinin yalnızca çerçevenin kendi ek yükünü ölçtüğünü ve bu farkın "vakaların ezici çoğunluğunda önemsiz" olduğunu yazıyor ([codeandmore](https://codeandmore.co.uk/posts/perfect-pointless-benchmarks/), [ikincil]). Asıl önemli nokta şu: tek makinede saniyede 32 bin istek, bir yerel gazetenin en yoğun anının çok üstünde. Üstelik CDN'den dönen bir sayfa Django'ya hiç ulaşmaz. Haber sitesinde darboğaz çerçeve değil. Darboğaz sorgu tasarımı, önbellek isabet oranı ve reklam yükü.

### PostgreSQL'in Türkçe aramasını en eksiksiz Django kullanıyor

PostgreSQL sabit kalacağına göre, çerçevenin bu veritabanını ne kadar iyi kullandığı hız ölçümlerinden daha önemli. PostgreSQL'in kendi içinde Türkçe kök bulucu (`turkish_stem`, "belediyesinden" sözcüğünü "belediye" köküne indirir) geliyor ([PostgreSQL 18 docs, ayna](https://docs.w3cub.com/postgresql~18/textsearch-psql), [birincil]). Çerçeveler bu özelliği farklı düzeylerde destekliyor:

- **Django:** Tam metin araması (FTS) için ağırlıklı sıralama, vurgulu özet, önceden hesaplanmış arama vektörü alanı ve yazım hatası toleransı sağlayan `pg_trgm` benzerlik işlevlerini doğrudan veriyor. Gereken veritabanı eklentisini kendi migration'ıyla (şema değişikliği betiği) kuruyor ([Django 5.2 docs](https://docs.djangoproject.com/en/5.2/ref/contrib/postgres/search/), [birincil]).
- **.NET (EF Core + Npgsql):** Tam metin araması güçlü, ama belgede `pg_trgm` geçmiyor ([Npgsql](https://www.npgsql.org/efcore/mapping/full-text-search.html), [birincil]).
- **Laravel:** Yalnızca temel bir `whereFullText` sunuyor ([Laravel 12](https://laravel.com/docs/12.x/queries), [birincil]).
- **Prisma (Node.js'in popüler ORM'i):** PostgreSQL tam metin araması hâlâ "önizleme" aşamasında ve hızlandırmak için indeks kullanamıyor ([Prisma docs](https://www.prisma.io/docs/orm/prisma-client/queries/full-text-search), [birincil]).

Türkçeye özgü iki tuzak var ve ikisi de çerçeveden bağımsız. Birincisi, `unaccent` ile ç, ğ, ı, ö, ş, ü harflerini düzleştirmek kök bulmayı bozuyor ([PostgreSQL listesi](https://www.postgresql.org/message-id/CAE2gYzzdqjeCpPk-BU1AWkFsn1yZocBWpAYd1WLA-EFy13Ozgg%40mail.gmail.com), [birincil]). İkincisi, 2025 tarihli bir hata raporunda Windows'ta Türkçe sıralama kuralıyla "ŞİLİ" ile "şili" eşleşmedi, Linux'ta eşleşti. Önerilen çözüm ICU tabanlı bir sıralama kuralı ([PostgreSQL listesi, 2025](https://www.postgresql.org/message-id/e9427abbe32a10733eb9451fa466e4a591531a27.camel@cybertec.at), [birincil]). Sonuç olarak üretim sunucusu Linux + ICU olmalı. Windows geliştirme makinesindeki arama sonuçları üretimdekiyle aynı varsayılmamalı. İleride eşanlamlı sözcük ya da gelişmiş filtre gibi "arama ürünü" özellikleri istenirse ikinci bir motor eklenebilir. Meilisearch, Türkçe noktalı ve noktasız i için özel bir harf katlama uyguluyor, ama Türkçe kök bulmayı belgelemiyor ([Meilisearch Docs](https://www.meilisearch.com/docs/learn/what_is_meilisearch/language), [birincil]). İkinci motor ayrıca bir eşitleme hattı ve ek işletim yükü getirir. Yaklaşık 1 milyon makalede PostgreSQL araması ile ayrı motorları karşılaştıran güvenilir bir ölçüm bulunamadı.

### Destek takvimi Django'yu en az yükseltme isteyen aday yapıyor

LTS (uzun süreli destek), bir sürümün yıllarca güvenlik yaması alacağının taahhüdü. Tek kişilik bir ekip için kritik: her zorunlu büyük yükseltme haftalarca iş demek.

| Çerçeve | Güncel destek durumu (Ekim 2026) | Ritim | Kaynak |
|---|---|---|---|
| **Django** | 5.2 LTS → Nisan 2028. **6.2 LTS: Nisan 2027 → Nisan 2030.** 2028'den itibaren her Ocak bir sürüm, her birine 3 yıl destek | 2–3 yılda bir LTS | [djangoproject.com](https://www.djangoproject.com/download/) [birincil] |
| Node.js | 24 LTS → Nisan 2028. 26 LTS → Nisan 2029 | Yıllık | [nodejs/Release](https://github.com/nodejs/Release) [birincil] |
| .NET | 10 LTS → Kasım 2028. **8 ve 9 aynı gün, 10 Kasım 2026'da bitiyor** | LTS 3 yıl | [.NET policy](https://dotnet.microsoft.com/en-us/platform/support/policy/dotnet-core) [birincil] |
| Spring Boot | 4.1: açık kaynak desteği Temmuz 2027'ye kadar | Yaklaşık yıllık | [endoflife.date](https://endoflife.date/spring-boot) [ikincil] |
| Laravel | 12: güvenlik desteği Şubat 2027'de bitiyor. 13: Q1 2028 | Her yıl yeni ana sürüm | [Laravel 12](https://laravel.com/docs/12.x/releases) [birincil] |
| Rails | 8.1: güvenlik desteği Ekim 2027'de bitiyor | Her sürüme yaklaşık 2 yıl | [endoflife.date](https://endoflife.date/rails) [ikincil] |
| Wagtail | 7.4 LTS, Django 5.2 ve 6.0'ı destekliyor | 3 ayda bir sürüm | [Wagtail docs](https://docs.wagtail.org/en/stable/releases/upgrading.html) [birincil] |

Django son iki sürümde haber sitesine doğrudan yarayan özellikleri de çekirdeğe aldı. Django 6.0 (Aralık 2025) şunları ekledi ([Django 6.0 notes](https://docs.djangoproject.com/en/dev/releases/6.0/), [birincil]):

- Yerleşik **içerik güvenlik politikası (CSP).** Reklam ve analitik betiklerinin denetimi için gerekli.
- Şablon parçaları. htmx tarzı kısmi güncellemeyi kolaylaştırıyor.
- Yerleşik **arka plan görevleri.** Bildirim gönderme ve önbellek temizleme gibi işler için kullanılabiliyor.

Mevcut bağımlılık listesi de çok dar. Django dışında yalnızca veritabanı sürücüsü, statik dosya sunucusu (WhiteNoise), görsel işleme (Pillow), uygulama sunucusu (gunicorn) ve isteğe bağlı Redis var (depo ölçümü, `requirements.txt`).

### Geliştirici havuzu ve yapay zekâ ajanları kararı değiştirmiyor

Stack Overflow'un 2025 anketinde web çerçeveleri arasında kullanım oranları şöyle: Node.js %48,7, React %44,7, Next.js %20,8, ASP.NET Core %19,7, Spring Boot %14,7, WordPress %13,6, **Django %12,6**, Laravel %8,9, Rails %5,9. Python dil olarak %57,9 ile ikinci. PostgreSQL %55,6 ile en çok kullanılan veritabanı ([Stack Overflow Survey 2025](https://survey.stackoverflow.co/2025/technology), [birincil], 2025). Türkiye'ye özgü, teknoloji kırılımı veren güvenilir bir ilan ya da anket istatistiği bulunamadı. Java ve C#'ın kurumsal ilanlarda güçlü olduğu yalnızca kaynak göstermeyen bir eğitim kurumu yazısında geçiyor ([GoIT](https://goit.global/tr/articles/programlama-dillerinin-manzarasi-ve-en-populer-dille/), [zayıf]).

Yapay zekâ ajanları açısından tek güçlü veri GitHub Octoverse 2025'ten geliyor. TypeScript Ağustos 2025'te GitHub'da 1 numaraya çıktı. GitHub bunu kısmen statik tiplerin ajanla üretilen kodu daha güvenilir kılmasına bağlıyor ([GitHub Octoverse 2025](https://github.blog/news-insights/octoverse/octoverse-a-new-developer-joins-github-every-second-as-ai-leads-typescript-to-1/), [birincil], 2025). Bu, TypeScript lehine en makul argüman. Ama dil ya da çerçeveye göre yapay zekâ kod doğruluğunu ölçen bağımsız bir çalışma bulunamadı. Bu projede ajan verimliliğinin asıl dayanağı 1.671 testlik güvenlik ağı. Başka bir yığına geçişte bu ağ sıfırdan kurulmak zorunda.

| Arka uç | Hazır gelenler (admin, kimlik, ORM, migration) | PostgreSQL araması | Firebase resmî SDK | Bu proje için durum |
|---|---|---|---|---|
| **Django (+ Wagtail seçeneği)** | Hepsi; panel zaten yazılı | En eksiksiz | Var (Python) | **Mevcut, önerilen** |
| Laravel / WordPress | Laravel: hepsi + ekosistem. WordPress: CMS | Laravel temel; WordPress PG desteklemiyor | **PHP resmî listede yok** | Yatay geçiş, kazanç yok |
| Rails | Hepsi | Ek paketle | **Ruby resmî listede yok** | Yatay geçiş, kazanç yok |
| Node.js (Express/NestJS) | Admin ve CMS yok; parçalar ayrı seçilir | Prisma'da önizleme | Var | Panelin tamamen yeniden yazılması |
| Go | Çoğu elle | Ham SQL | Var | En fazla elle iş |
| Spring Boot / .NET | Güçlü güvenlik ve kimlik; hazır CMS paneli yok | .NET güçlü | Var (Java, C#) | Kurumsal ölçek için anlamlı |

Firebase Admin SDK'nın resmî dil listesi: Node.js, Java, Python, Go, C# ve deneysel olarak Dart ([Firebase](https://firebase.google.com/docs/admin/setup), [birincil]).

## Hazır CMS'ler ya PostgreSQL'i reddediyor ya yıllık 25 bin dolardan başlıyor

CMS (içerik yönetim sistemi), editörlerin haber yazıp yayımladığı paneldir. "Headless" CMS ise yalnızca paneli ve veri API'sini sunar, okura bakan sayfaları başka bir katmanın çizmesini bekler. Hazır bir platforma geçmenin tek gerçek getirisi, haber masasına özgü özelliklerin kutudan çıkması olurdu. Bu getiriyi gerçekten sunanlar Arc XP, Brightspot ve WordPress VIP gibi kurumsal platformlar. Genel amaçlı headless CMS'lerde (Payload, Strapi, Directus, Sanity, Contentful) canlı blog, son dakika, Google News site haritası ve anlık bildirim hazır gelmiyor. Yani bunlara geçmek, Django'da zaten yapılmış işin bir kısmını başka bir dilde yeniden yaptırıyor.

| Platform | PostgreSQL | Lisans / fiyat | Haber masası özellikleri | Kaynak ve güven |
|---|---|---|---|---|
| **Ghost** | **Yok**, üretimde yalnız MySQL 8 | Ghost(Pro) 15/29/199 $/ay (Temmuz 2025) | Bülten ve abonelik odaklı | [Ghost Docs](https://docs.ghost.org/faq/supported-databases) [birincil]; [Ghost Forum](https://forum.ghost.org/t/updated-ghost-pro-pricing-july-2025-15-mo-starter-29-mo-publisher-199-mo-business/59090) [birincil] |
| **WordPress / VIP / Newspack** | **Yok**, yalnız MySQL/MariaDB; PG yalnız resmî olmayan eklentiyle | VIP yıllık 25.000 $'dan; Newspack yıllık geliri 300 bin $ altı yayın için 750 $/ay | Eklentilerle geniş | [PG4WP](https://github.com/PostgreSQL-For-Wordpress/postgresql-for-wordpress) [birincil]; [wpvip.com](https://wpvip.com/?p=98790) [satıcı; sayfa 404, arama özetinden]; [Newspack](https://newspack.com/pricing/) [birincil] |
| **Arc XP** | SaaS, veri üreticide | **Yıllık 50 bin–3 milyon $, medyan 400–500 bin $**; kurulum ≈ bir yıllık ücret | Kapsamlı; Türkçe arayüz yok | [GNI](https://newsinitiative.withgoogle.com/cms-providers/arc-xp/) [ikincil, 2023] |
| **Sanity / Contentful** | SaaS, veri üreticide | Sanity koltuk başına 15 $/ay; Contentful ücretsiz planda ticari kullanım yasak | Genel amaçlı | [Flow Ninja](https://www.flowninja.com/blog/sanity-cms-pricing) [ikincil]; [Contentful](https://www.contentful.com/help/admin/usage/usage-limit/) [birincil] |
| **Strapi** | Var | Çekirdek MIT; **editoryal onay akışı yalnız Enterprise'da** | Genel amaçlı | [Strapi Docs](https://docs.strapi.io/cms/features/review-workflows) [birincil] |
| **Directus** | Var | **v12 (Mayıs 2026) ile lisans yine değişti**: açık kaynak değil, kaynak-erişilebilir | Genel amaçlı | [Directus](https://directus.com/resources/directus-v12-license-change) [birincil] |
| **Payload** | Var (Drizzle) | MIT. **Haziran 2025'te Figma satın aldı**, Payload Cloud yeni kayıt almıyor | Genel amaçlı; 4.0 kırıcı değişiklikler getirebilir | [Figma](https://www.figma.com/blog/payload-joins-figma/) [birincil]; [Build with Matija](https://buildwithmatija.com/blog/payload-4-0) [ikincil] |
| **Wagtail** | Var (Django ORM) | Açık kaynak; 7.0 LTS Django 5.2'yi destekleyen ilk sürüm | Sayfa ve blok editörü güçlü; haber özellikleri elle | [Wagtail 7.0](https://docs.wagtail.org/en/7.0/releases/7.0.html) [birincil] |
| **Türk "haber yazılımları"** | Bilinmiyor | Bir listede 10–60 bin TL; kod çoğunlukla satıcının sunucusunda | Seçim sonuçları, imsakiye gibi yerel özellikler | [kobazoglu](https://kobazoglu.com/en-iyi-haber-yazilimlari.html) [zayıf]; [R10.net, 2024](https://www.r10.net/sorum-var/4047648-hangi-haber-yazilimini-sizce-secmeliyim.html) [forum] |

Tablodan üç sonuç çıkıyor. Birincisi, PostgreSQL şartı Ghost'u ve WordPress ailesini doğrudan eliyor. Arc XP, Sanity ve Contentful veriyi kendi bulutlarında tuttuğu için PostgreSQL ancak bir kopya olarak kalabilir, yani şart fiilen ihlal edilir. İkincisi, kurumsal platformlar ölçek olarak bambaşka bir dünyada. Arc XP'nin medyan yıllık ücreti tek başına bir yerel gazetenin tüm bütçesini aşar. GNI incelemesi Arc XP'nin "kayda değer iç geliştirici ekibi olmayan" kuruluşlara "kötü uyduğunu" ve 200 kişilik bir haber merkezinin 10 Arc geliştiricisi çalıştırdığını kaydediyor ([GNI](https://newsinitiative.withgoogle.com/cms-providers/arc-xp/), [ikincil], 2023). Üçüncüsü, açık kaynak headless adaylarda yönetişim riski somut. Directus'un lisansı iki yılda iki kez sıkılaştı. Payload artık bir tasarım aracı şirketinin stratejisine bağlı ve Figma'nın taahhüdü "yakın gelecek" ile sınırlı.

WordPress ayrıca güvenlik açısından tek kişilik bir ekip için en ağır seçenek. Patchstack'in 2025 verisine göre WordPress ekosisteminde **11.334 yeni açık** bulundu (yıllık +%42). Bu açıkların **%91'i eklentilerde**, %46'sı açıklandığı anda yamasızdı. Yoğun sömürülen açıklarda kitlesel saldırıya geçiş süresinin medyanı **5 saat** ([Patchstack 2026](https://patchstack.com/whitepaper/state-of-wordpress-security-in-2026/), [ikincil, güvenlik firması], 2026). Bursa'daki yerel rakip Olay'ın WordPress + Cloudflare üzerinde çalıştığı görülüyor ([W3Techs](https://w3techs.com/sites/info/olay.com.tr), [ikincil, tarihsiz]). Yerel pazarın tipik çözümü bu. Ama PostgreSQL şartı ve proje için yazılmış özel özellikler (konu takibi, yapay zekâ editörü, canlı veri bileşenleri, BİK resmî ilan biçimi) bu yolu kapatıyor.

Haber kuruluşlarında Wagtail kullanımının en güçlü kanıtı New York Public Radio. Gothamist'in 20 yıllık yaklaşık **150 bin sayfasını** headless Wagtail'e taşıdılar ve seçimde ekibin Django bilmesi belirleyici oldu ([Wagtail blog](https://wagtail.org/blog/nypr-on-wagtail/), [satıcı/topluluk yayını], 2021). Full Fact de 2025'te yaklaşık 10 bin içeriği Django Admin'den Wagtail'e taşıdı ([Wagtail Space 2025](https://pretalx.com/wagtail-space-2025/talk/CCJYH7), [ikincil]). Bursa Hakimiyet'in 1.038.474 haberlik arşivi, kaynaklı vaka çalışmalarındaki en büyük rakamların (Politico 190 bin, Gothamist 150 bin) 5–7 katı. Hiçbir aday için kaynaklı "milyon makale" rakamı bulunamadı. Wagtail'in gerçek değeri, mevcut Django projesine **kademeli** eklenebilen tek CMS olması: aynı veritabanını ve aynı kullanıcı modelini kullanabiliyor. Bu bilgi Wagtail kurulum belgesiyle teyit edilmeli.

## Devler yüzlerce mühendisle kendi yığınını yazıyor, küçükler bakımı devrediyor

### Okura bakan katmanda React baskın, arka uç dili ise çok çeşitli

Büyük yayıncıların gerçek yığınları iki ayrı yol gösteriyor. Bir grup yıllardır büyük ekiplerle kendi platformunu yazıyor. Diğer grup son beş yılda kendi CMS'ini bırakıp bakımı başkasında olan bir ürüne geçti.

| Yayıncı | CMS / arka uç | Okura bakan katman | Güven ve yıl |
|---|---|---|---|
| The Guardian | Scala/Play, artık yalnız JSON üretiyor | TypeScript + Node + React (`dotcom-rendering`); **uygulama içi içeriği de çiziyor** | [GitHub](https://github.com/guardian/dotcom-rendering) [birincil, 2026] |
| The New York Times | Scoop, kurum içi, Java | React + GraphQL; W3Techs'e göre Next.js ve Svelte | [SED](https://softwareengineeringdaily.com/2018/10/22/react-and-graphql-at-the-nytimes/) [ikincil, 2017–18]; [W3Techs](https://w3techs.com/sites/info/nytimes.com) [ikincil, tarihsiz] |
| BBC | Simorgh (React); WebCore sunucusuz platform | Next.js (W3Techs) | [GitHub](https://github.com/bbc/simorgh) [birincil]; [InfoQ](https://infoq.com/news/2022/04/bbc-one-year-serverless) [ikincil, 2022] |
| Washington Post | Arc XP (kendi ürünü) | React tabanlı PageBuilder; seçim sayfaları Next.js + Vercel | [Arc XP](https://docs.arcxp.com/en/products/pagebuilder/pagebuilder-engine.html) [birincil]; [Vercel](https://vercel.com/blog/washington-post-next.js-vercel-engineering-at-the-speed-of-breaking-news) [satıcı, 2023] |
| Financial Times | Node.js mikroservisler | React, Preact, Handlebars | [builtin](https://builtin.com/job/full-stack-engineer-nodereact/2982243) [ikincil, ilan] |
| Vox Media | Chorus (kurum içi) → WordPress VIP | Kendi Duet ön yüzü (headless) | [Axios](https://www.axios.com/2023/07/18/vox-media-chorus?stream=top) [ikincil, 2023] |
| L'Express | Symfony 1 (kurum içi) → Arc XP, **1,2 milyon makale taşındı** | Arc | [The Audiencers](https://theaudiencers.com/migrating-1-2-million-articles-to-arc-xp-a-look-behind-the-scenes-as-lexpress-changes-cms/) [ikincil, 2023] |
| NPR | Kurum içi → Grove (Brightspot) | – | [Current](https://current.org/2024/10/with-grove-adoption-nearly-complete-stations-look-to-enhancements-single-sign-on/) [ikincil, 2024] |
| Texas Tribune | Django (2009) → Armstrong (Django, terk edildi) → WordPress/Newspack | PHP | [Texas Tribune](https://www.texastribune.org/2009/11/03/the-texas-tribune-developers-tribute) [birincil, 2009]; [W3Techs](https://w3techs.com/sites/info/texastribune.org) [ikincil] |
| Star Tribune (bölgesel) | PHP + AWS → Next.js + Vercel; DevOps kadrosu 3 → 1 | Next.js | [Vercel](https://vercel.com/customers/break-the-news-not-the-site) [satıcı, 2024] |

Bu tablodan iki ders çıkıyor. Birincisi, **"ön yüz React ise arka uç da Node olmalı" diye bir sektör kuralı yok.** Guardian Scala'dan JSON alıp TypeScript'le çiziyor, Vox WordPress'ten alıp kendi ön yüzüyle çiziyor. İkincisi, "Next.js kullanan büyük yayıncı" kanıtlarının önemli kısmı Vercel'in vaka çalışmalarından geliyor. BBC örneği özellikle yanıltıcı. Vercel'in "Simorgh'u Next.js'e taşıdık" yazısı BBC'nin bir kararı değil, Vercel'in kendi kopyası üzerinde yaptığı bir kodlama alıştırması. Bu alıştırmada bile Lighthouse puanları BBC'nin mevcut sitesiyle "aşağı yukarı eşit" çıktı ([Vercel](https://vercel.com/blog/migrating-a-large-open-source-react-application-to-next-js-and-vercel), [satıcı demosu], 2022). Yani çerçeve değişikliği tek başına hız kazandırmadı. Birincil kaynaklı tek somut başarım kuralı Guardian'dan geliyor: her uç noktada ortalama yanıt 500 ms'nin altında olmalı, 2 saniyeyi aşan istek kesilir ([guardian/frontend](https://github.com/guardian/frontend), [birincil]). FT'nin 2018 konuşması ise mikroservis mimarisinin başarımı düşürebileceği uyarısını yapıyordu ([Speaker Deck](https://speakerdeck.com/wheresrhys/speeding-up-without-slowing-down-1?slide=36), [birincil], 2018). Bu mimarilerin arkasındaki ekip büyüklüğü de unutulmamalı. NYT'de 2021'de 650'den fazla teknoloji çalışanı sendika kurdu ([Nieman Lab](https://www.niemanlab.org/reading/tech-workers-at-the-new-york-times-form-a-union/), [ikincil], 2021). Vox'un yalnızca ürün CMS'e geçişi bile **42 kişilik** bir teslim ekibi gerektirdi ([XWP](https://xwp.co/case-studies/vox-media/), [satıcı], 2023). Tek kişilik bir ekibin mikroservis, ayrı render servisi ve Kubernetes'i taklit etmesi, görüntüyü kopyalayıp sonucu alamamak olur.

### Türkiye'de büyük gruplar ASP.NET'te, yerel pazar hazır PHP sistemlerinde

W3Techs'in tespitlerine göre Hürriyet ve Milliyet **ASP.NET + jQuery + Merlin CDN + Amazon** üzerinde. Sabah ASP.NET ve CloudFront kullanıyor, Cumhuriyet ASP.NET ve Cloudflare. Next.js tespit edilen iki büyük kurum NTV ve Anadolu Ajansı. T24 PHP'de, Bursa'daki Olay WordPress'te ([W3Techs: hurriyet](https://w3techs.com/sites/info/hurriyet.com.tr), [ntv](https://w3techs.com/sites/info/ntv.com.tr), [aa](https://w3techs.com/sites/info/aa.com.tr), [ikincil, tarama tarihi gösterilmiyor]). W3Techs sayfalarında tarama tarihi yazmıyor. CDN arkasındaki sitelerde sunucu dili çoğu zaman görünmüyor. Bu tespitler "şu an" diye okunmamalı. Hiçbir Türk yayıncının mühendislik blogu, konferans konuşması ya da göç gerekçesi bulunamadı. Türk sitelerinin mobil uygulama teknolojisine dair de kaynak yok.

### Küçük yayıncıların dersi, kendi kodunu yazanlar için bir uyarı

Bu raporun önerisine karşı en güçlü argüman Bursa Hakimiyet ölçeğindeki vakalardan geliyor ve dürüstçe ele alınmalı. Texas Tribune 2009'da siteyi Django ile "üç haftadan kısa sürede" yazdı. Sonra Knight Vakfı'nın 975 bin dolarlık desteğiyle Django tabanlı açık kaynak bir CMS (Armstrong) kurdu. Bu CMS'in sitesi 2014'ten sonra güncellenmedi ve gazete sonunda WordPress/Newspack'e geçti ([Nieman Lab](https://www.niemanlab.org/2011/03/wordpress-for-news-orgs-knight-gives-bay-citizen-texas-tribune-975000-for-open-source-cms/), [ikincil], 2011; [Wikipedia](https://en.wikipedia.org/wiki/Armstrong_(content_management_system)), [ikincil]). L'Express'in kurum içi CMS'i, teknolojisi "tamamen eskidiği" ve geliştirici bulunamadığı için terk edildi. Vox, tescilli platformunun bakım maliyeti tırmandığı için kendi CMS'ini bıraktı. Açıklanan gerekçelerin ortak noktası teknoloji modası değil. Ortak nokta **bakım maliyeti ve işe alım**. Ürün CMS'ten kurum içi koda dönen bir 2018–2026 vakası ise bulunamadı.

Bu ders Bursa Hakimiyet'e üç noktada farklı uygulanıyor. Birincisi, bu vakalarda kaçılan şey eskimiş ya da sahipsiz bir teknolojiydi (Symfony 1, terk edilmiş Armstrong). Django ise 2030'a kadar takvimi belli, ana akım bir çerçeve. İkincisi, bu kuruluşların geçtiği ürünler (WordPress VIP, Newspack, Arc XP) PostgreSQL şartını karşılamıyor. Üçüncüsü, Türkiye'ye özgü özellikler (BİK, nöbetçi eczane, namaz vakitleri) hiçbir global üründe hazır gelmiyor. Yine de risk gerçek: kodun tek bir kişiye ve onun ajanlarına bağlı olması. Bu risk çerçeve değiştirerek değil, ana akım bir çerçevede kalarak, bağımlılıkları dar tutarak, testleri koruyarak ve mimariyi belgeleyerek yönetilir. Wagtail de aynı ekosistem içinde bir acil çıkış kapısı olarak elde tutulur.

## Mobil uygulama ayrı bir yığın değil, aynı Django'nun okuma API'si

Mobil uygulamanın arka ucu için yeni bir sistem kurmak gerekmiyor. Gereken, web ile **aynı içerik modelinden** beslenen, sürümlü (`/api/v1/`) ve okuma ağırlıklı bir REST API. Django'da bunun iki olgun yolu var. Django REST Framework en popüler üçüncü taraf paket ([JetBrains: State of Django 2025](https://blog.jetbrains.com/pycharm/2025/10/the-state-of-django-2025/), [ikincil], 2025). Django Ninja ise yükselişte (%10) ve her uç nokta için OpenAPI şemasını otomatik üretiyor ([Django weblog](https://www.djangoproject.com/weblog/2025/nov/02/five-ways-to-discover-django-packages/), [birincil], 2025; [PyPI](https://pypi.org/project/django-ninja/1.0b2), [birincil]). OpenAPI, API'nin makine tarafından okunabilir tarifi. Bu tariften iOS (Swift) ve Android (Kotlin) için istemci kodu üretilebiliyor. Bu da tek kişilik ekipte el emeğini azaltıyor. Wagtail 7.0'ın Django Ninja kurulum rehberi eklemesi de bu yolun ekosistemde kabul gördüğünü gösteriyor ([Wagtail 7.0](https://docs.wagtail.org/en/7.0/releases/7.0.html), [birincil]).

GraphQL (istemcinin tek sorguda istediği alanları seçtiği API türü) birden çok istemci ekibi olan büyük yapılarda anlamlı. NYT bunu farklı dilleri birleştirmek için seçmişti ([SED, 2017](https://softwareengineeringdaily.com/2017/11/30/react-and-graphql-at-new-york-times/), [ikincil]). Tek ekip ve sabit ekranlı bir haber uygulaması için REST + CDN önbelleği daha basit. API yanıtları da web sayfalarıyla aynı etiketle önbelleklenmeli ve aynı yayın olayıyla temizlenmeli. Böylece bildirim sonrası gelen ani okuma dalgası sunucuya ulaşmaz.

**Anlık bildirim (push) için Firebase Cloud Messaging (FCM) yeterli ve ucuz.** iOS bildirimleri de FCM üzerinden Apple'ın servisine gidebiliyor. Varsayılan kota proje başına **dakikada 600 bin mesaj**. Firebase bu kotanın geliştiricilerin %99'undan fazlasına yettiğini belirtiyor ([Firebase: quotas](https://firebase.google.com/docs/cloud-messaging/throttling-and-quotas.md.txt), [birincil]). "Konu" (topic) mesajlaşması gecikme için değil, yüksek hacim için tasarlanmış. Bir uygulama kopyası en fazla 2.000 konuya abone olabiliyor ([Firebase: Topic messaging](https://firebase.google.com/docs/cloud-messaging/topic-messaging?hl=de), [birincil]). Yerel bir gazete için "son dakika", kategori ve konu bazlı topic'ler yeterli. Python, Firebase'in resmî sunucu SDK'ları arasında. PHP ve Ruby bu listede değil, bu da Laravel ve Rails aleyhine küçük ama somut bir nokta. Bildirim gönderimi Django 6.0'ın arka plan görevleriyle ya da mevcut zamanlanmış görev düzeniyle yapılabilir. Panelde "bildirim gönder" yetkisi ve aynı bildirimin iki kez gitmesini önleyen bir kilit olmalı.

API'nin taşıması gereken üç özellik daha var. Birincisi, web adresleri doğrudan uygulamada açılabilmeli. Bunun için iOS'ta `apple-app-site-association` ([Apple](https://developer.apple.com/documentation/xcode/supporting-associated-domains), [birincil]), Android'de `assetlinks.json` dosyası gerekiyor ([Android](https://developer.android.com/training/app-links/verify-android-applinks), [birincil]). Bu belgeler bu araştırmada yeniden açılmadı. Bu yüzden adres yapısı kalıcı olmalı. İkincisi, haber gövdesi uygulamanın kendi arayüzüyle çizebileceği bloklar halinde (paragraf, görsel, gömülü içerik) verilmeli. Üçüncüsü, çevrimdışı okuma için değişiklik zamanı ve ETag (içeriğin değişip değişmediğini gösteren parmak izi) ile artımlı eşitleme desteklenmeli. Burada bir alternatif de var. Guardian'ın `dotcom-rendering` servisi web sitesinin yanında uygulama içi içeriği de çiziyor ([GitHub](https://github.com/guardian/dotcom-rendering), [birincil]). Yani iyi bir sunucu şablonu, uygulamadaki makale görünümüne de doğrudan hizmet edebilir.

Mobil uygulamanın kendisinin hangi teknolojiyle yazılacağı (Swift ve Kotlin ile ayrı ayrı mı, React Native/Expo gibi ortak bir kod tabanıyla mı) **bu araştırmanın verisiyle cevaplanamıyor**. Haber uygulamaları için kaynaklı tek bulgu, Guardian Android uygulamasının %90'dan fazla Kotlin olduğu ([itjobswatch](https://www.itjobswatch.co.uk/jv/GUARDIAN-NEWS-AND-MEDIA/Senior-Android-Developer-Job-London-UK-51dhct), [ikincil, iş ilanı]). Web ile React Native arasında kod paylaşımı mümkün ([Expo Blog](https://expo.dev/blog/from-a-brownfield-react-native-and-next-js-stack-to-one-expo-app), [birincil], 2025). Ama ölçülmüş bir paylaşım oranı bulunamadı. "%80" iddiası yalnızca bir forum gönderisinde hedef olarak geçiyor ([SuperTokens](https://community.supertokens.com/t/9838743/hey-all-so-i-m-working-on-a-next-and-expo-universal-app-basi?t=v2), [zayıf]). Bu yüzden web için React seçmek, mobil uygulamayı ancak uygulama da React Native ile yazılırsa ve arayüzün büyük kısmı web'e özgü değilse kazançlı kılar. Asıl paylaşılması gereken şey arayüz kodu değil, API. Uygulama teknolojisi ayrı ve hedefli bir araştırmayla seçilmeli.

## Toplam maliyetin büyük kalemi yazılım lisansı değil, göç ve insan emeği

Toplam sahip olma maliyeti (TCO), lisans ücretlerinin yanında barındırma, bakım, güvenlik yaması, yükseltme ve en önemlisi insan emeğini de kapsar. Bu araştırmada çerçeveler arası karşılaştırmalı barındırma ya da bellek maliyeti için güvenilir bir kaynak **bulunamadı**. Vercel ya da Netlify'ın haber trafiği ölçeğindeki 2026 fiyatları da çekilmedi. Bu yüzden tablo kaynaklı rakamları ve yapısal farkları gösteriyor, uydurma bir toplam vermiyor.

| Seçenek | Lisans | Ek çalışma ortamı / güvenlik takvimi | Göç işi | PostgreSQL şartı |
|---|---|---|---|---|
| **A. Mevcut Django + CDN + Ninja API** | Yok | Yok; tek dil, tek takvim | Yok | Karşılıyor |
| B. Django arka uç + Next.js ön yüz | Yok (Vercel kullanılırsa ücretli) | +Node, +npm bağımlılık ağacı, +React/Next açıkları; çok kopyada Redis | 80 şablonun yeniden yazımı | Karşılıyor |
| C. Node CMS (Payload/Strapi) + Next.js | Strapi onay akışı ücretli | Yalnız Node; Python araçları (yapay zekâ editörü, canlı veri) yan servis olarak kalır | Panel, modeller, 1.671 test, adres uyumu | Karşılıyor |
| D. Laravel / Rails | Yok | PHP/Ruby; Firebase resmî SDK yok | Tüm uygulama | Karşılıyor |
| E. WordPress VIP / Newspack | VIP ≥25.000 $/yıl; Newspack ≥750 $/ay | Eklenti güvenliği (2025'te 11.334 açık) | Tüm uygulama + ikinci arşiv göçü | **Karşılamıyor** |
| F. Arc XP | 50 bin–3 M $/yıl + kurulum ≈ 1 yıllık ücret | Satıcı yönetir, ama iç geliştirici ekibi ister | Tüm uygulama + ikinci arşiv göçü | **Karşılamıyor** |
| G. Türk haber yazılımı | 10–60 bin TL (zayıf kaynak) + yıllık ücret şikâyetleri | Satıcıya bağlı; kod çoğunlukla satıcıda | Özel özellikler kaybolur | Bilinmiyor |

Göçün gerçek bedeli kod satırıyla da sınırlı değil. Yeniden yazılacak olanlar: `uygulama/` altındaki **234 Python dosyası, 54.382 satır, 1.671 test, 80 şablon ve 28 migration** (depo ölçümü, 21 Ekim 2026). Bunlara Django'nun parola özeti biçimi için bir uyumluluk katmanı ve arama vektörlerini besleyen tetikleyicilerin yeniden kurulması da eklenir. Belgelenmiş medya göçlerinde asıl kayıp çerçeveden değil, adres ve yönlendirme hatalarından geliyor. Google, adres değişen taşımalarda her eski adresin doğrudan son hedefe kalıcı yönlendirmeyle (301) bağlanmasını istiyor. Bu yönlendirmeler **en az bir yıl**, mümkünse süresiz tutulmalı. Büyük sitelerde yeni adreslerin eskilerin yerini alması haftalar ya da daha uzun sürüyor ([Google Search Central: Site move](https://developers.google.com/search/docs/crawling-indexing/site-move-with-url-changes), [birincil]). Bir danışmanlık anlatımına göre Reuters'ta 24 aydan eski makaleleri yeni CMS'e almamanın organik trafiğin %22'sini kaybettireceği modellendi ([Newsifier](https://www.newsifier.com/blog/development/how-newsifier-handles-website-migrations-without-seo-traffic-loss), [satıcı iddiası, birincil kaynak açılmadı]). Satıcıların "%30–60 trafik kaybı" iddiaları ise hiçbir çalışmaya dayanmıyor ve dikkate alınmamalı ([FocusReactive](https://focusreactive.com/blog/cms-migration/), [satıcı iddiası]).

Bu noktada güçlü bir karşı argüman var: site henüz yayında değil, yani bir değişiklik için en ucuz an şimdi. Bu argüman doğru, ama sonucu değiştirmiyor. Maliyet en düşük noktasında olsa bile kazanç ortaya çıkmıyor. Saha verisi önerilen alternatiflerin mobilde daha kötü olduğunu gösteriyor. SEO, sunucuda HTML üreten tüm yaklaşımlarda eşdeğer. Hız farkı CDN arkasında önemsizleşiyor. Getirisi olmayan bir yatırımın en ucuz anı da yine zarardır. Üstelik eski sitenin adresleriyle uyum sözleşmesi zaten Django'da kodlanmış ve testlerle korunuyor. Yeniden yazım, BİK'in yeni tebliğinin yürürlüğe girdiği 1 Ocak 2027'ye hazırlık gibi gerçek takvim işlerinin önüne geçer. İnsan maliyeti tarafında tek kaynaklı veri şu: Türkiye'de 2025'te full stack geliştiricinin ortalama maaşı junior'da 50.500 TL, kıdemlide 122.500 TL ([tamindir](https://www.tamindir.com/haber/yazilimci-maaslari-2025_94742/), [ikincil], 2025). Aylık birkaç sunucu kademesi farkı, bir yeniden yazımın tek bir ayının yanında küçük kalır.

## Öneri: Django, sunucu şablonu, CDN ve Ninja API; alternatifler şu koşullarda kazanır

| Katman | Öneri | Neden |
|---|---|---|
| Arka uç | **Django 5.2 LTS → Nisan 2027 sonrası 6.2 LTS** (destek Nisan 2030) | En az yükseltme yükü, eksiksiz PostgreSQL araması, panel ve 1.671 test elde |
| Veritabanı / arama | PostgreSQL FTS (`turkish`) + GIN indeksi + `pg_trgm`; üretimde Linux + ICU; `unaccent` Türkçe harflere uygulanmaz | Ek motor ve eşitleme hattı yok; Windows'taki Türkçe harf hatasından korunur |
| Ön yüz | Django şablonları + elle CSS + sade JS; gerekli yerlerde derlemesiz htmx (ya da Alpine) | Saha verisinde mobilde %60,5; JS bütçesi reklama kalır; erişilebilirlik kendiliğinden |
| Önbellek / CDN | Etiketle temizleme yapan CDN (Cloudflare'de tüm planlarda); `s-maxage` + `stale-while-revalidate` + `stale-if-error`; BİK IP istisnası ve DDoS'ta CAPTCHA | Son dakika saniyeler içinde görünür, trafik patlamasında sunucu korunur |
| Canlı blog | CDN'de 5–15 sn önbelleklenen JSON'u yoklama; SSE yalnız ASGI ya da yönetilen bir yayın servisiyle | Sunucu yükü okur sayısından bağımsız kalır |
| Reklam | Sabit yükseklikli yuvalar, `async` ve tembel yükleme, rızaya bağlı kişiselleştirme | En büyük CWV riski reklamda |
| Mobil API | Django Ninja ile `/api/v1/` REST + OpenAPI; blok yapılı gövde; ETag ile artımlı eşitleme | Aynı model ve aynı önbellek; istemci kodu otomatik üretilir |
| Bildirim | `firebase-admin` (Python) + FCM topic'leri; Django görevleriyle gönderim | Dakikada 600 bin mesaj kotası; resmî SDK |
| Mobil uygulama | Ayrı araştırma | Haber uygulaması teknolojisine dair kaynak yetersiz |

Alternatiflerin bu önerinin önüne geçeceği somut koşullar var:

- **Wagtail:** Editörler sürükle-bırak blok düzeniyle özel sayfa (seçim özeli, dosya haberi) kurmak isterse daha iyi olur. Haber modeline dokunmadan, aynı projeye kısmi olarak eklenmeli.
- **Astro ya da Next.js:** Ekibe ayrı bir ön yüz ekibi katılırsa ya da seçim sonuç haritası gibi yoğun etkileşimli bir ürün gerekirse anlamlı hale gelir. O zaman bile Washington Post'un seçim sayfalarında yaptığı gibi izole bir alt alan adında tutulmalı, sitenin tamamına yayılmamalı.
- **ASP.NET ya da Spring:** Bursa Hakimiyet .NET kadrosu olan büyük bir Türk medya grubuna entegre olursa, işe alım havuzu nedeniyle gündeme gelir.
- **Go:** On binlerce eşzamanlı bağlantıyla seçim gecesi canlı sonuç akışı gibi tek ve dar bir servis gerekirse yalnızca o servis için düşünülebilir.
- **Meilisearch ya da OpenSearch:** Okurdan yazım hatası toleransı ve filtreli arama talebi gelirse ve PostgreSQL araması gerçek arşiv sorgularında yetersiz kalırsa eklenir.
- **WordPress/Newspack ya da Türk haber yazılımı:** PostgreSQL şartı kalkarsa ve kurum tüm yazılım bakımını dışarı devretmeye karar verirse, Texas Tribune'ün izlediği yol mantıklı hale gelir. Bu, yönetimin vereceği stratejik bir karar.
- **Arc XP:** Ancak Bursa Hakimiyet birden çok yayın organını yöneten bir gruba dönüşürse ve yıllık altı haneli dolar bütçe ayrılırsa anlamlı olur.

## Sonuç

Bu araştırmanın vardığı sonuç, sorunun kendisinin yanlış yerde durduğu. Bir haber sitesinin başarısını belirleyen değişken çerçevenin adı değil. Belirleyici olanlar üç şey: önbellek isabet oranı, reklam betiklerinin sayfaya getirdiği yük ve 1 milyon adresin kesintisiz yaşaması. Bu üçü her yığında aynı mühendislik işidir ve Django'da bunların altyapısı zaten kurulu. Dünyanın en büyük yayıncılarını taklit etmek, onların yüzlerce mühendisle çözdüğü bir problemi tek kişiyle çözmeye kalkmak olur. Bölgesel gazetelerin dersi de "kendi kodunu yazma" değil, "sahipsiz ve modası geçmiş koda bağlanma". Ana akım, uzun destekli ve dar bağımlılıklı bir Django kurulumu, bu dersin tam karşılığı.

Önümüzdeki 18 ayın takvimi teknoloji değişikliğinden daha önemli. BİK'in yeni tebliği 1 Ocak 2027'de yürürlüğe giriyor ve tam metni yayımlandığında meta etiketleri yeniden kontrol edilmeli. Django 6.2 LTS Nisan 2027'de çıkıyor, 5.2'nin güvenlik desteği Nisan 2028'de bitiyor. Mobil uygulamaya başlanmadan önce API sözleşmesi ve kalıcı adres yapısı sabitlenmeli. Ölçülmesi gereken iki yerel veri de var: reklamlar yerleştirildikten sonra mobil INP'nin ne olduğu ve Türkçe aramanın gerçek arşiv sorgularında ne kadar isabetli çalıştığı. Bunlar, hangi çerçevenin seçildiğinden çok daha fazlasını söyleyecek.
