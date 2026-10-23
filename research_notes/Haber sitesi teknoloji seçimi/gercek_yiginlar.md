# Büyük global ve Türk haber sitelerinin gerçek teknoloji yığınları (2024–2026)

> Araştırma tarihi: 21 Ekim 2026. Yöntem: yalnızca resmî yayınlar, GitHub depoları, satıcı vaka çalışmaları, iş ilanları ve W3Techs gibi ikincil tespit sayfaları kullanıldı. Haber sitelerinin kendisi taranmadı, User-Agent değiştirilmedi.
> Güven etiketi: **[birincil]** = yayıncının kendi kaynağı (kendi blogu, GitHub deposu, kendi personelinin beyanı). **[ikincil]** = satıcı vaka çalışması, basın, W3Techs/StackShare, iş ilanı toplayıcısı. **[zayıf]** = tek kaynak, tarihsiz ya da yapay zekâ üretimi içerik.
> **W3Techs uyarısı:** W3Techs sayfalarında tarama tarihi yazmıyor (yalnız "2009–2026" telif satırı var). "Used until recently" (yakın zamana kadar) diye işaretlenen teknolojiler artık kullanılmıyor olabilir. CDN arkasındaki sitelerde sunucu dili çoğu zaman görünmüyor; "listelenmedi" demek "yok" demek değil.

---

## 1. Yayıncı → CMS / backend → frontend render → mobil → barındırma/CDN tablosu

### Takeaway
Büyükler iki yola ayrılıyor: (a) yıllarca büyük ekiple kendi CMS'ini yazanlar (NYT Scoop, Guardian Composer + Scala, Le Monde Sirius, BBC) ve (b) son beş yılda kendi CMS'ini **bırakıp** ürün CMS'e geçenler (Vox → WordPress VIP, L'Express/Libération/Le Parisien → Arc XP, NPR → Grove/Brightspot, Texas Tribune → WordPress/Newspack). Okura bakan katmanda ortak payda: **Node.js üzerinde React (çoğunlukla Next.js) + Fastly/Akamai/Cloudflare CDN**. Türkiye'de büyük grupların çoğu hâlâ **ASP.NET + jQuery + Merlin CDN + AWS**; Next.js'e geçmiş görünenler NTV ve Anadolu Ajansı; bağımsız/yerel siteler PHP (WordPress ya da yerli "haber yazılımı").

### Cited Findings

**Özet tablo** (her hücrenin kaynağı aşağıdaki maddelerde; "?" = güvenilir kaynak bulunamadı)

| Yayıncı | CMS / backend | Frontend render | Mobil uygulama | Barındırma / CDN | Kaynak yılı / güven |
|---|---|---|---|---|---|
| The New York Times | Scoop (kurum içi, Java — 2016); Oak editörü React + ProseMirror (2023) | React + GraphQL/Apollo (2017–18); W3Techs: Node.js + Next.js (iç sayfalar), Svelte (etkileşimliler) | ? | GCP/GKE Kubernetes + AWS (2018); CDN Fastly | 2016–2018 birincil/ikincil; W3Techs tarihsiz |
| The Guardian | `guardian/frontend` Play Framework 2 / Scala — artık JSON üretiyor | `dotcom-rendering` (DCR/DCAR): TypeScript, Node.js, Express, React, Emotion; uygulama içeriğini de render ediyor | Android: Kotlin (%90+) ve Java | Docker konteyner (depoda); CDN ? | GitHub, 2026 birincil |
| BBC News / World Service | Simorgh (açık kaynak React; World Service siteleri); WebCore sunucusuz platform (AWS Lambda) | W3Techs: bbc.com'da Next.js + Node.js | ? | Fastly (W3Techs); WebCore sunucusuz | GitHub birincil; WebCore 2022 ikincil |
| The Washington Post | Arc XP (WaPo'nun kendi ürettiği, satılan platform; AWS üzerinde mikroservis) | PageBuilder Engine — React tabanlı, SSR + CSR; seçim sayfaları Next.js 12 + Vercel (2022) | ? | AWS; seçim sayfaları Vercel | Arc dokümanı birincil; Vercel vaka 2023 ikincil |
| Financial Times | Node.js mikroservisler | React, Preact, Handlebars, GraphQL, TypeScript | ? | Heroku + AWS (Lambda, Kinesis, DynamoDB), Fastly + VCL | İş ilanları (tarihsiz) ikincil; 2018 konuşma |
| Reuters | Arc XP | (Arc PageBuilder → React) | ? | Akamai (Arc vaka çalışması) | 2024 ikincil |
| Bloomberg | ? | ? | ? | ? | Kaynak bulunamadı |
| The Economist | ? (WP Engine "yakın zamana kadar") | ? | ? | Cloudflare (şu an); Akamai yakın zamana kadar | W3Techs tarihsiz ikincil |
| Le Monde | Sirius (kurum içi, 2014'ten beri; L'Obs, Télérama, Courrier international, L'Équipe, Le Temps'a da satılıyor) | ? | ? | ? | ikincil |
| Der Spiegel | ? | W3Techs: Svelte | ? | Akamai + Link11; Google + Hetzner barındırma | W3Techs tarihsiz ikincil |
| El País (Prisa) | Arc XP (yalnız izleme sitesi) | ? | ? | ? | zayıf |
| Axel Springer (Bild/Welt) | Backend ilanı: Kotlin / Spring Boot / AWS | Node, React, TypeScript, SCSS (ilanlar); StackShare'deki AngularJS/jQuery listesi eski | ? | AWS | İlanlar ikincil; StackShare eski |
| Schibsted (VG/Aftonbladet) | JS/TS, Node | React, Next (abonelik ekibi) | ? | AWS, Kubernetes, Terraform | İlanlar (tarihsiz, bir kısmı ~2018–19) ikincil |
| NPR | Grove (Brightspot, 2024'te NPR de geçti); önceki Seamus kurum içi (2002, ATG Dynamo/Java + Oracle) | ? | ? | ? | 2024 ikincil (Current) |
| Texas Tribune | Şimdi WordPress + Newspack (Automattic); kuruluşta Django (2009), Armstrong (Django, 2011) | W3Techs: PHP, jQuery; React "yakın zamana kadar" | ? | Automattic/Pressable/Newspack; Nginx; Cloudflare alt alan | W3Techs + Newspack ikincil |
| ProPublica | Haber uygulamaları: Ruby on Rails (2013); "Ruby, Python, JavaScript" (2018) | ? | ? | ? | 2013/2018 birincil (kendi blog/ilan) |
| Vox Media | Chorus (kurum içi, 10+ yıl) → WordPress VIP (2023'te açıklandı) | Kendi frontend'i Duet + Overtone tasarım sistemi; WPGraphQL ile başsız (headless) | ? | WordPress VIP | 2023 birincil+ikincil |
| CNN | ? (WordPress VIP müşteri listesinde adı geçiyor) | W3Techs: Next.js + Node.js "yakın zamana kadar" | ? | Fastly (şu an); AWS | W3Techs tarihsiz; WP VIP liste ikincil |
| BuzzFeed | ? | ? | ? | ? | Kaynak bulunamadı |
| Times of India / Hindustan Times | ? (Times Internet'te Economic Times için XSLT → Next.js göçü — tek bir CV beyanı) | ? | ? | ? | zayıf |
| Star Tribune (ABD, bölgesel) | PHP + AWS → Next.js + Vercel | Next.js | ? | Vercel | 2024 ikincil (satıcı) |
| L'Express (FR) | Ocari (Symfony 1, kurum içi) → Arc XP | Arc | ? | ? | 2023 ikincil |

**Yayıncı bazında kaynaklı bulgular**

*The New York Times*
- 2017 itibarıyla NYT ön yüzü React tabanlı ve Apollo (GraphQL) kullanıyor; GraphQL'in seçilme nedeni bir "spec" olması ve NYT'nin kullandığı farklı dillerle kolay entegre olması; Relay'den React Router entegrasyonu ve esneklik sorunları yüzünden Apollo'ya geçildi **[ikincil, 2017–2018]** — [Software Engineering Daily 2017](https://softwareengineeringdaily.com/2017/11/30/react-and-graphql-at-new-york-times/); [SED 2018](https://softwareengineeringdaily.com/2018/10/22/react-and-graphql-at-the-nytimes/)
- Scoop, NYT haber masasının kurum içi CMS'i; 2016 WordCamp konuşmasında Java ile yazıldığı, editörün TinyMCE olduğu ve ProseMirror tabanlı yeni editörün yapıldığı anlatılıyor **[ikincil, 2016 — eski olabilir]** — [WordPress.tv / Eric Lewis](https://wordpress.tv/speakers/eric-lewis/)
- Oak (NYT'nin ortak çalışmalı zengin metin editörü) React ve ProseMirror kullanıyor ve nytimes.com'un okura bakan React bileşen kodunu paylaşıyor **[birincil — NYT mühendisinin kişisel yazısı, 2023]** — [smoores.dev "back to basics" (yansı)](https://backiee.wasmer.app/http_smoores_dev/post/back_to_basics)
- NYT 2016 ortasından itibaren Google Cloud + GKE (Kubernetes) değerlendirdi; bazı VM dağıtımları 45 dakikadan "birkaç saniye–birkaç dakika"ya indi; Oracle'a bağımlı uygulamalar AWS'de, gerisi GCP'de konteynerde **[ikincil/birincil karışık, 2018]** — [Kubernetes.io vaka çalışması](https://kubernetes.io/case-studies/newyorktimes/); [CNCF 2018](https://www.cncf.io/blog/2018/06/18/the-new-york-times-from-print-to-the-web-to-cloud-native/); [DatacenterDynamics](https://www.datacenterdynamics.com/en/news/for-the-new-york-times-a-move-to-the-cloud/)
- W3Techs nytimes.com için: sunucu dili JavaScript (iç sayfalar), Next.js (iç sayfalar), Svelte, Envoy Proxy, Node.js, CDN Fastly, alt alanlarda Sanity (başsız CMS), Heroku ve CloudFront **[ikincil, tarihsiz]** — [W3Techs nytimes.com](https://w3techs.com/sites/info/nytimes.com)

*The Guardian*
- `guardian/frontend` "Play Framework 2 Scala uygulamaları kümesi"; kendini "Guardian web sitesi ön yüzünün backend'i" olarak tanımlıyor ve görevi "modern render servisi Dotcom Rendering'e JSON üretmek"; her uç nokta için ortalama yanıt < 500 ms, 2 saniyeyi aşan istek kesilir kuralı **[birincil, GitHub 2026]** — [guardian/frontend](https://github.com/guardian/frontend)
- `dotcom-rendering` (DCR/DCAR) "theguardian.com ve canlı uygulamalardaki içeriğin render mantığını" barındırıyor; TypeScript, Node.js, Express, React ve Emotion kullanıyor; pnpm monorepo, Production.dockerfile **[birincil, GitHub 2026]** — [guardian/dotcom-rendering](https://github.com/guardian/dotcom-rendering); [DCR README](https://github.com/guardian/dotcom-rendering/blob/main/dotcom-rendering/README.md)
- Guardian'ın Scala geçmişi: 2012 QCon konuşmasına göre Java yığınından ve Python/Django denemelerinden sonra Content API için Scala'ya geçildi **[birincil konuşma, 2012 — tarihsel]** — [QCon London 2012](https://qconlondon.com/london-2012/qconlondon.com/london-2012/presentation/Scala_%20simplifying%20development%20at%20guardian.co.html); [InfoQ](https://www.infoq.com/presentations/How-We-Mostly-Moved-from-Java-to-Scala)
- Guardian Android uygulaması "ağırlıkla Kotlin ve Java"; kod tabanının %90+'ı Kotlin **[ikincil, iş ilanı]** — [itjobswatch Guardian Senior Android](https://www.itjobswatch.co.uk/jv/GUARDIAN-NEWS-AND-MEDIA/Senior-Android-Developer-Job-London-UK-51dhct); [builtinlondon](https://builtinlondon.uk/job/senior-android-developer/9996256)

*BBC*
- Simorgh: "BBC World Service haber sitelerini render eden ReactJS tabanlı uygulama", BBC News Web Engineering ekiplerince bakılıyor; README'de istekler Mozart adlı yönlendirme/önbellek servisinden geçip Express sunucusuna geliyor; depo `nextjs` etiketli **[birincil, GitHub]** — [bbc/simorgh](https://github.com/bbc/simorgh)
- Vercel'in 2022 "Simorgh'u Next.js'e taşıdık" yazısı **BBC'nin kararı değil**: Vercel'in kendi çatalında yaptığı bir "kodlama alıştırması"; 20.000+ satır ve 30+ bağımlılık silindi, HMR 1,3 sn → 131 ms, ağ isteği 57 → 34; Lighthouse "aşağı yukarı eşit"; yazı "BBC, ilgileniyorsan bize yaz" diye bitiyor **[ikincil — satıcı demosu, 2022]** — [Vercel blog](https://vercel.com/blog/migrating-a-large-open-source-react-application-to-next-js-and-vercel)
- WebCore: BBC'nin sunucusuz (AWS Lambda) platformu; Şubat 2022'de geçişin ~%30'u tamam, ayda 3,3 milyar fonksiyon çağrısı; editoryal güncellemenin yansıma süresi 2,5 dk → 30 sn, derleme 24 dk → 5 dk **[birincil yazı (erişilemedi, 403) + ikincil özet, 2022]** — [BBC Product & Technology Medium](https://medium.com/bbc-product-technology/bbc-online-a-year-with-serverless-ffc2ae474277); [InfoQ 2022](https://infoq.com/news/2022/04/bbc-one-year-serverless)
- W3Techs bbc.com için: JavaScript/TypeScript, Next.js, Node.js, CDN Fastly **[ikincil, tarihsiz]** — [W3Techs bbc.com](https://w3techs.com/sites/info/bbc.com)

*The Washington Post / Arc XP*
- PageBuilder Engine "React üzerine kurulu" render servisi; sunucu ve istemci tarafı render destekliyor; Editor (yerleşim) ve Engine (render) ayrı **[birincil, Arc XP dokümanı]** — [Arc XP PageBuilder Engine](https://docs.arcxp.com/en/products/pagebuilder/pagebuilder-engine.html); [Giriş](https://docs.arcxp.com/en/products/pagebuilder-engine/introduction-to-pagebuilder-engine.html)
- Arc XP, WaPo'nun geliştirdiği, AWS üzerinde mikroservis mimarili bulut platformu (Composer, Photo Center, Video Center, PageBuilder, başsız API'ler) **[ikincil]** — [Google News Initiative CMS providers](https://newsinitiative.withgoogle.com/cms-providers/arc-xp/); [fitgap](https://us.fitgap.com/products/arc-xp)
- WaPo Seçim Mühendisliği ekibi 2022 ara seçimleri öncesinde 52 sayfa / 1.000+ seçim için Next.js 12 (ISR) + Vercel'e geçti; önceki çözüm de Next.js'ti ama AWS ECS + SQS/EC2 üzerinde, "karmaşık, yeni geliştiriciyi alıştırması zor ve pahalı" idi; ön yüz TypeScript'e yeniden yazıldı. Kapsam **yalnızca seçim sayfaları**, sitenin tamamı değil **[ikincil — satıcı vakası, 2023]** — [Vercel: WaPo](https://vercel.com/blog/washington-post-next.js-vercel-engineering-at-the-speed-of-breaking-news)

*Financial Times*
- FT ilanları: TypeScript, React, GraphQL, Node.js, CircleCI, Terraform, Fastly, Heroku, AWS; bir diğeri React, Node.js, Heroku, AWS Lambda/Kinesis/DynamoDB, Handlebars, Sass, Webpack, Preact, Fastly ve VCL **[ikincil, ilanlar tarihsiz]** — [startup.jobs FT](https://startup.jobs/senior-engineer-ft-specialist-investors-chronicle-financial-times-4193390); [builtin FT Full Stack](https://builtin.com/job/full-stack-engineer-nodereact/2982243)
- 2018'de bir FT baş mühendisi "yüksek derecede bileşenleştirilmiş mikroservis yığını ve hızlı sürüm döngüsünün başarımı nasıl zedeleyebildiğini" anlattı **[birincil konuşma, 2018 — eski]** — [Speaker Deck "Speeding up without slowing down"](https://speakerdeck.com/wheresrhys/speeding-up-without-slowing-down-1?slide=36)
- StackShare FT profili (Fastly, Node.js, Heroku, Docker, GraphQL, Kubernetes) ~2 yıl güncellenmemiş **[ikincil, eski]** — [StackShare FT](https://stackshare.io/financial-times/financial-times)

*Reuters, El País, Le Monde*
- Akamai'nin Arc XP vaka çalışması (2024) Le Parisien, Reuters ve The Globe and Mail'i Arc XP kullanan markalar arasında sayıyor **[ikincil, 2024]** — [Akamai Arc XP vaka PDF](https://www.akamai.com/site/en/documents/case-study/2024/akamai-cs-arc-xp.pdf)
- elpais.com yalnızca bir izleme sitesinde Arc XP kullanıcısı olarak listeleniyor; El País'ten birincil teyit yok **[zayıf]** — [wmtips Arc XP](https://www.wmtips.com/technologies/cms/arc-xp/)
- Le Monde'un CMS'i Sirius, 2014'ten beri kurum içi geliştiriliyor; L'Équipe ve Le Temps gibi dış başlıklara satılıyor **[ikincil]** — [CB News](https://www.cbnews.fr/node/64002)

*Der Spiegel, The Economist, CNN*
- W3Techs spiegel.de: Svelte, Nginx 1.26.3 (alt alan), Akamai (alt alan), Link11 (DDoS/CDN), Google ve Hetzner barındırma **[ikincil, tarihsiz]** — [W3Techs spiegel.de](https://w3techs.com/sites/info/spiegel.de)
- W3Techs economist.com: Cloudflare (şu an); Nginx, Akamai, WP Engine "yakın zamana kadar" **[ikincil, tarihsiz]** — [W3Techs economist.com](https://w3techs.com/sites/info/economist.com)
- W3Techs cnn.com: Next.js, Node.js, JavaScript "yakın zamana kadar"; Fastly şu an; AWS barındırma **[ikincil, tarihsiz — CNN'in Next.js'ten çıkıp çıkmadığı belirsiz]** — [W3Techs cnn.com](https://w3techs.com/sites/info/cnn.com)
- WordPress VIP müşteri listeleri CNN, Bloomberg, NBC Universal, News Corp'u sayıyor (hangi alt sitede kullanıldığı belirtilmiyor) **[ikincil, satıcı]** — [WPBeginner TR: WordPress VIP nedir](https://www.wpbeginner.com/tr/beginners-guide/what-is-wordpress-vip-what-are-the-benefits-and-alternatives/)

*Axel Springer, Schibsted*
- Axel Springer Tech GmbH ilanı: Kotlin / Spring Boot / AWS backend **[ikincil, ilan]** — [Arbeitsagentur ilanı](https://www.arbeitsagentur.de/jobsuche/jobdetail/20470-963094883-S); diğer ilanlarda Node, React, TypeScript, SCSS; Golang, Python, Kubernetes, Terraform — [devjobs.de](https://devjobs.de/job/ec4d2368e0f98fb66fe0f1c98782e212); [arbeitnow](https://www.arbeitnow.com/jobs/companies/axel-springer-news-media-national/staff-fullstack-engineer-on-demand-streaming-berlin-4091)
- StackShare'de Bild için AngularJS, NGINX, Webtrekk, jQuery listeleniyor — AngularJS ömrünü tamamladığı için büyük olasılıkla eski **[ikincil, eski]** — [StackShare Bild](https://stackshare.io/companies/bild/stack)
- Aftonbladet ilanı: "JavaScript, React, Node.js, TypeScript, Travis, AWS, Datadog, Pingdom, Terraform, Kubernetes"; Schibsted haber ürün ekibi "çoğunlukla JS/TS, Node, React, GitHub Actions, AWS"; abonelik ekibi "JS/TS, Node, React, Next" **[ikincil, ilanlar tarihsiz, bir kısmı ~2018–19]** — [webbjobb Aftonbladet senior](https://webbjobb.io/jobb/187138/senior-software-engineer-aftonbladet); [NAV Fullstack Subscription](https://arbeidsplassen.nav.no/stillinger/stilling/6ccd1c28-5be8-4b8b-85d3-9871b1d04072)

*NPR, Texas Tribune, ProPublica, Vox Media*
- NPR ve 200'den fazla kamu radyosu istasyonu Grove'u (Brightspot, eski adı Perfect Sense) kullanıyor; istasyonlar 2020 başında geçmeye başladı, NPR 2024'te geçti; Grove ağırlıkla NPR yapımı Core Publisher'ın yerini aldı **[ikincil, Current, Ekim 2024]** — [Current.org 2024](https://current.org/2024/10/with-grove-adoption-nearly-complete-stations-look-to-enhancements-single-sign-on/)
- NPR'ın kurum içi CMS'i Seamus 2002'de ATG Dynamo/Java + Oracle ile çıktı; 2011'de "kendine ait tam bir ekip" bakımını yapıyordu **[birincil 2009 / ikincil 2011 — tarihsel]** — [NPR 2009](https://www.npr.org/sections/publiceditor/2009/11/05/114384108/birthdays-at-npr); [Poynter 2011](https://poynter.org/?p=134791)
- Texas Tribune sitesi 2009'da Django ile "üç haftadan kısa sürede" kodlandı **[birincil, 2009]** — [Texas Tribune 2009](https://www.texastribune.org/2009/11/03/the-texas-tribune-developers-tribute); 2011'de Knight Vakfı Bay Citizen ile birlikte Django tabanlı açık kaynak CMS (Armstrong) için 975.000 $ verdi — [Nieman Lab 2011](https://www.niemanlab.org/2011/03/wordpress-for-news-orgs-knight-gives-bay-citizen-texas-tribune-975000-for-open-source-cms/); Armstrong'un sitesi 2014'ten sonra güncellenmedi — [Wikipedia Armstrong](https://en.wikipedia.org/wiki/Armstrong_(content_management_system))
- Bugün texastribune.org: PHP, WordPress, WooCommerce, Nginx; barındırma Automattic (Pressable/Newspack); React "yakın zamana kadar" **[ikincil, W3Techs tarihsiz]** — [W3Techs texastribune.org](https://w3techs.com/sites/info/texastribune.org); Newspack yayıncı listesi Tribune'u sayıyor — [Newspack publishers](https://newspack.com/publishers/); Aralık 2025 podcast'i "bir süre kendi platformunu kurmaya çalıştı, sonra bırakıp Newspack'e geçti" diyor **[zayıf, gayriresmî]** — [WP Builds #357](https://wpbuilds.com/2025/12/02/this-week-in-wordpress-357/); 30.11.2022 itibarıyla `texastribune/base` Docker imajı artık "Texastribune web sitesi ve CMS'in temeli değil" **[birincil, Docker Hub]** — [Docker Hub texastribune/base](https://hub.docker.com/r/texastribune/base)
- ProPublica (2013): haber uygulamaları için iki öne çıkan seçenek Rails ve Django; ProPublica Rails kullanıyor **[birincil, 2013 — eski]** — [ProPublica Nerds: Our news app tech](https://www.propublica.org/nerds/our-news-app-tech); 2018 ilanı: "mevcut yığınımız Ruby, Python ve JavaScript" — [ProPublica 2018 ilan](https://www.propublica.org/jobs/news-apps-developers-for-politics-contract-june-2018)
- Vox Media, Temmuz 2023'te Chorus ve Pinnacle'dan WordPress VIP'e geçeceğini açıkladı; okura bakan deneyim için kendi Duet platformunu tutuyor; Concert (reklam) ve Coral (yorum) da anlaşmaya dahil **[ikincil, Axios 2023 + birincil WP VIP duyurusu]** — [Axios 2023](https://www.axios.com/2023/07/18/vox-media-chorus?stream=top); [WordPress VIP duyurusu](https://wpvip.com/blog/vox-media-wordpress-vip/)
- XWP vakası: 5 marka (Vox, Polygon, The Verge, Eater, SB Nation); WordPress VIP editoryal backend + Duet/Overtone frontend, WPGraphQL ile başsız; 42 kişilik teslim ekibi (XWP + Vox); Vox.com'da ilk 40 günde %40 trafik artışı ve tüm Core Web Vitals yeşil **[ikincil — uygulayıcı satıcı, iddialar bağımsız doğrulanmadı]** — [XWP Vox Media vakası](https://xwp.co/case-studies/vox-media/)

*Bölgesel örnekler (Bursa Hakimiyet ölçeğine yakın)*
- Minnesota Star Tribune, PHP + AWS yığınını Next.js + Vercel ile değiştirdi, ayrı mobil/masaüstü kod tabanlarını birleştirdi; web DevOps kadrosu 3 → 1 kişi; Core Web Vitals %30 iyileşti; RealClearPolling özel PHP CMS + AWS'den Contentful + Next.js'e 3 ayda geçti **[ikincil — satıcı vakası, Ekim 2024]** — [Vercel: Break the news, not the site](https://vercel.com/customers/break-the-news-not-the-site)
- L'Express: kurum içi CMS Ocari 2012/13'te Symfony 1 ile yazılmıştı, "tamamen eskimiş" teknoloji olduğu için geliştirici bulmak zorlaştı, 2018'den beri geliştirme durmuştu; Altice'ten ayrılınca grup CMS'i Cléo planı düştü; Eidos ve Sirius'a karşı Arc XP seçildi; 1,2 milyon makale taşındı **[ikincil — röportaj, Mart 2023]** — [The Audiencers](https://theaudiencers.com/migrating-1-2-million-articles-to-arc-xp-a-look-behind-the-scenes-as-lexpress-changes-cms/)
- Hindistan'da Jagran New Media, Google'ın başarım ve SEO kriterleri nedeniyle Next.js'e geçtiğini söylüyor **[ikincil]** — [GXPress](https://www.gxpress.net/article/8338/jagran-new-medias-new-tech-stack-best-of-both-worlds)

### Inferences
- "Next.js kullanan büyük yayıncı" listesinin önemli kısmı satıcı (Vercel) vaka çalışmalarından geliyor; BBC örneğinde Vercel yazısı BBC'nin kararı değil, bir demo. Karar gerekçesi olarak alıntılanmamalı.
- Okura bakan katmanda Node.js + React (Next.js veya kurum içi muadili) baskın; ama backend/CMS dili çok çeşitli (Java, Scala, Kotlin, PHP, Python, Ruby). Yani "frontend Next.js ise backend de Node olmalı" diye bir sektör kuralı yok — Guardian (Scala JSON → TS render) ve Vox (WordPress PHP → Duet) tam olarak bu ayrımı yapıyor.
- CDN neredeyse her yerde zorunlu bileşen: Fastly (NYT, BBC, FT, CNN), Akamai (Spiegel, Reuters/Arc), Cloudflare (Economist; Türkiye'de Sözcü, NTV, T24, Cumhuriyet, BirGün).

### Gaps
- Bloomberg, BuzzFeed, Times of India, Hindustan Times, El País (birincil), Le Monde'un frontend'i, Spiegel'in CMS'i, CNN'in güncel CMS'i için güvenilir kaynak bulunamadı.
- Mobil uygulama teknolojisi (native / React Native / Flutter / webview) yalnızca Guardian Android için bulundu (Kotlin). NYT, BBC, WaPo ve Türk sitelerinin uygulama teknolojisi için kaynak yok.
- BBC WebCore yazısının kendisine erişilemedi (Medium 403); rakamlar InfoQ özetinden.
- Guardian'ın Scala render'dan DCR'ye geçiş gerekçesini anlatan resmî blog yazısı bulunamadı (yalnız depo README'leri ve 2019 civarı ikincil bir alıntı: "trafiğin ~%20'si DCR'den" — dated).

---

## 2. 2018–2026 göçleri ve açıklanan gerekçeler

### Takeaway
Açıklanan gerekçelerin ortak noktası teknoloji modası değil, **bakım maliyeti ve işe alım**: Vox "tescilli platformun bakım maliyeti tırmandı", L'Express "Symfony 1 eskidi, geliştirici bulunamıyor", WaPo seçim ekibi "karmaşık, alıştırması zor, pahalı", Texas Tribune "kendi platformunu kurmaya çalıştı, bıraktı". Göç yönü çoğunlukla **kurum içi CMS → bakımı başkasında olan ürün CMS**.

### Cited Findings
- **Vox Media (2023→):** Chorus 10+ yıl kurum içi bakıldı; okur davranışı değişti, tescilli platformun bakım maliyeti tırmandı; amaç operasyon maliyetini düşürmek ve editörü mühendislik darboğazından kurtarmak; önce proof-of-concept ile WordPress VIP–Duet uyumu gösterildi, aşamalı geçiş Vox.com'dan başladı — [XWP](https://xwp.co/case-studies/vox-media/); Vox'un söylediği hedef "ekiplerimiz platformlara değil deneyimlere odaklansın" — [WordPress VIP](https://wpvip.com/vox-media-wordpress-vip/)
- **L'Express (2020–2023):** Symfony 1 tabanlı kurum içi CMS'in eskimesi ve işe alım güçlüğü; CMS'in baskı dahil tüm masaların giriş noktası olması şartı — [The Audiencers](https://theaudiencers.com/migrating-1-2-million-articles-to-arc-xp-a-look-behind-the-scenes-as-lexpress-changes-cms/)
- **NPR (2020–2024):** Kurum içi Core Publisher'ı istasyonlar "aşmıştı"; Brightspot tabanlı Grove'a 4 yılı aşkın geçiş — [Current.org](https://current.org/2024/10/with-grove-adoption-nearly-complete-stations-look-to-enhancements-single-sign-on/)
- **Texas Tribune:** Django (2009) → Armstrong (2011, Knight fonlu açık kaynak, 2014'ten sonra terk) → WordPress/Newspack (tarih belirsiz) — [Nieman Lab](https://www.niemanlab.org/2011/03/wordpress-for-news-orgs-knight-gives-bay-citizen-texas-tribune-975000-for-open-source-cms/); [Wikipedia](https://en.wikipedia.org/wiki/Armstrong_(content_management_system)); [W3Techs](https://w3techs.com/sites/info/texastribune.org); [WP Builds (zayıf)](https://wpbuilds.com/2025/12/02/this-week-in-wordpress-357/)
- **Guardian:** Scala/Play `frontend` render'ı bırakıp yalnızca JSON üreten backend'e dönüştü; render TypeScript/React DCR'de — [guardian/frontend](https://github.com/guardian/frontend); [dotcom-rendering](https://github.com/guardian/dotcom-rendering)
- **Washington Post seçim sayfaları (2022):** Kendi AWS ECS + SQS/EC2 kurulumundaki Next.js → Vercel üzerinde Next.js 12 ISR; gerekçe karmaşıklık, alıştırma güçlüğü, maliyet ve 8 Kasım 2022 sabit tarihi — [Vercel](https://vercel.com/blog/washington-post-next.js-vercel-engineering-at-the-speed-of-breaking-news)
- **BBC (2020–2022):** WebCore sunucusuz platform; gerekçe kişiselleştirme, güncelleme hızı, derleme süresi ve deney yapabilme — [InfoQ](https://infoq.com/news/2022/04/bbc-one-year-serverless)
- **NYT (2016–2018):** Veri merkezlerinden GCP/GKE ve AWS'ye; ~300+ uygulama taşındı; dağıtım süresi dakikalardan saniyelere — [Kubernetes.io](https://kubernetes.io/case-studies/newyorktimes/); [Diginomica 2018](https://diginomica.com/2018/05/03/new-york-times-leans-create-cloud-native-culture/)
- **Star Tribune (2024):** PHP + AWS → Next.js + Vercel; ayrı mobil/masaüstü kod tabanlarını birleştirme — [Vercel](https://vercel.com/customers/break-the-news-not-the-site)

### Inferences
- Bursa Hakimiyet için en çok ders veren vakalar devler değil, **L'Express, Texas Tribune ve Vox**: üçü de kendi CMS'ini yazdı ve sonunda "bunu bakımlı tutacak ekibimiz yok/olmamalı" noktasına geldi. Bu, çerçeve seçiminde "işe alınabilir, uzun ömürlü, geniş topluluklu" ölçütünün modadan önemli olduğunu gösteriyor.
- Ters yönde (ürün CMS'ten kurum içine) açıklanmış bir 2018–2026 göçü bulunamadı.

### Gaps
- Texas Tribune'un WordPress'e geçiş yılı ve resmî gerekçesi bulunamadı.
- Guardian'ın DCR geçişinin başlangıç/bitiş yılı ve resmî gerekçe metni bulunamadı.
- CNN'in W3Techs'te "Next.js yakın zamana kadar" görünmesinin bir göçe mi yoksa tespit hatasına mı işaret ettiği belirsiz.

---

## 3. Ekip büyüklükleri (bağlam için)

### Takeaway
Kurum içi platform yazanların teknoloji kadroları yüzlerle ölçülüyor (NYT 2021'de 650+ teknoloji çalışanı sendikası); ürün CMS'e geçen Vox'un bile göç projesi 42 kişilik bir ekip gerektirdi. Küçük/bölgesel ölçekte satıcı vakaları "DevOps 3 → 1 kişi" gibi tek haneli rakamlar veriyor.

### Cited Findings
- NYT'de 2021'de 650'den fazla teknoloji çalışanı (yazılım mühendisi, tasarımcı, veri analisti, ürün yöneticisi) sendika kurdu **[ikincil, 2021]** — [Nieman Lab](https://www.niemanlab.org/reading/tech-workers-at-the-new-york-times-form-a-union/)
- UnifyGTM profil verisine göre NYT'de ~1.025 Bilgi Teknolojisi ve ~276 Mühendislik profili (toplam ~11.071 profil; şirket toplamından farklı olabilir) **[zayıf, 2026 tahmini]** — [UnifyGTM](https://www.unifygtm.com/insights/headcount/the-new-york-times)
- Vox Media WordPress VIP geçişi: XWP + Vox'tan 42 kişilik teslim ekibi — [XWP](https://xwp.co/case-studies/vox-media/)
- NPR Seamus için 2011'de "tam bir ekip" ayrılmıştı — [Poynter 2011](https://poynter.org/?p=134791)
- Star Tribune: web DevOps kadrosu 3 → 1 — [Vercel](https://vercel.com/customers/break-the-news-not-the-site)
- Texas Tribune 2009'da siteyi Django ile üç haftadan kısa sürede kodlayan küçük bir ekiple çıktı — [Texas Tribune 2009](https://www.texastribune.org/2009/11/03/the-texas-tribune-developers-tribute)

### Inferences
- NYT, Guardian, BBC tipi kurum içi yığınlar yüzlerce mühendisin varlığını varsayıyor; tek-üç kişilik bir ekibin bu mimarileri (mikroservis, ayrı render servisi, Kubernetes) taklit etmesi tam olarak "cargo-cult" riskidir.

### Gaps
- Guardian, BBC News, FT, WaPo, Spiegel, Schibsted ve hiçbir Türk yayıncı için güvenilir mühendis sayısı bulunamadı.

---

## 4. Kamuya açık dersler (başarım, maliyet)

### Takeaway
Açıklanan kazanımlar çoğunlukla satıcı vaka çalışmalarından geliyor ve bağımsız değil; birincil kaynaklı tek somut başarım kuralı Guardian'ın "< 500 ms ortalama, 2 sn'de kes" kuralı. FT'nin 2018 konuşması ise mikroservis + hızlı sürüm döngüsünün başarımı **düşürebildiği** uyarısını yapıyor.

### Cited Findings
- Guardian `frontend`: ortalama yanıt < 500 ms, 2 sn üstü istek sonlandırılır **[birincil]** — [guardian/frontend](https://github.com/guardian/frontend)
- FT: bileşenleştirilmiş mikroservis yığını ve hızlı sürüm döngüsünün başarıma zararı **[birincil konuşma, 2018]** — [Speaker Deck](https://speakerdeck.com/wheresrhys/speeding-up-without-slowing-down-1?slide=36)
- BBC WebCore: güncelleme 2,5 dk → 30 sn, derleme 24 dk → 5 dk — [InfoQ 2022](https://infoq.com/news/2022/04/bbc-one-year-serverless)
- NYT GKE: 45 dk süren dağıtımlar saniyeler–dakikalara — [Kubernetes.io](https://kubernetes.io/case-studies/newyorktimes/)
- Vox.com: ilk 40 günde %40 trafik artışı, Core Web Vitals yeşil (satıcı iddiası) — [XWP](https://xwp.co/case-studies/vox-media/)
- Star Tribune: CWV %30 iyileşme, VP aday açıklaması trafik sıçramasında sorun yok (satıcı iddiası) — [Vercel](https://vercel.com/customers/break-the-news-not-the-site)
- WaPo seçim ekibi: önceki AWS kurulumu "pahalıydı", yeni kurulumda gece "çok daha basit" geçti; nicel rakam verilmedi — [Vercel](https://vercel.com/blog/washington-post-next.js-vercel-engineering-at-the-speed-of-breaking-news)
- Vercel'in BBC demosunda Lighthouse puanları BBC'nin mevcut sitesiyle "aşağı yukarı eşit" — yani çerçeve değişikliği tek başına başarım kazandırmadı — [Vercel](https://vercel.com/blog/migrating-a-large-open-source-react-application-to-next-js-and-vercel)
- Drupal/geleneksel CMS'ten başsız Next.js'e geçişlerde sık hata: URL takma adları, yapılandırılmış içerik, önizleme ve metaveriyi sona bırakmak; yönlendirme haritası ve SEO sürekliliği planı şart **[ikincil, ajans yazıları]** — [johnkavanagh.co.uk](https://johnkavanagh.co.uk/services/drupal-to-nextjs-migration/); [pathtoproject](https://www.pathtoproject.com/services/drupal-to-headless-migration)

### Inferences
- Bağımsız (satıcı dışı) bir "Next.js'e geçtik, şu kadar hızlandık" verisi bulunamadı; BBC demosu çerçevenin değil önbellek/CDN ve sayfa ağırlığının belirleyici olduğunu ima ediyor.
- 1 milyonluk arşivi olan bir site için (L'Express 1,2 milyon makale) en riskli iş çerçeve değil URL/SEO sürekliliği.

### Gaps
- Hiçbir yayıncı için kamuya açık maliyet (barındırma/CDN faturası, lisans) rakamı bulunamadı. Arc XP ve WordPress VIP fiyatları açık değil.

---

## 5. Türk siteleri: yaygın yığınlar, "haber yazılımı" satıcıları, Next.js benimsenmesi

### Takeaway
W3Techs'e göre büyük Türk grupları (Demirören: Hürriyet, Milliyet, CNN Türk; Turkuvaz: Sabah; Habertürk) **ASP.NET + jQuery + Merlin CDN + Amazon** çizgisinde; Cumhuriyet de ASP.NET (Cloudflare arkasında). **Next.js/Node.js** tespit edilenler NTV ve Anadolu Ajansı. **PHP** tespit edilenler T24 ve Bursa'nın yerel gazetesi Olay (WordPress). Yerel/bölgesel pazarda Habersoft, TE Bilişim, Tumeva, Gazisoft, Medya İnternet (Kulga), Webay, Webaksiyon gibi hazır "haber yazılımı" satıcıları öne çıkıyor; hiçbiri teknoloji yığınını açıkça yazmıyor.

### Cited Findings

**W3Techs tespitleri** (hepsi **[ikincil, tarama tarihi gösterilmiyor]**)

| Site | Sunucu dili / çerçeve | JS | CDN / ters vekil | Barındırma | Kaynak |
|---|---|---|---|---|---|
| hurriyet.com.tr | ASP.NET | jQuery | Merlin CDN | Amazon | [W3Techs](https://w3techs.com/sites/info/hurriyet.com.tr) |
| milliyet.com.tr | ASP.NET (alt alan) | jQuery | Merlin CDN | Amazon | [W3Techs](https://w3techs.com/sites/info/milliyet.com.tr) |
| cnnturk.com | listelenmedi | yalnız JS | Merlin CDN | Amazon | [W3Techs](https://w3techs.com/sites/info/cnnturk.com) |
| sabah.com.tr | ASP.NET 4.0.30319 + IIS 10 (alt alan); Envoy Proxy | jQuery 3.6.4, Bootstrap | Amazon CloudFront | Amazon | [W3Techs](https://w3techs.com/sites/info/sabah.com.tr) |
| haberturk.com | listelenmedi | jQuery 3.6.0 | Merlin CDN | Amazon | [W3Techs](https://w3techs.com/sites/info/haberturk.com) |
| ntv.com.tr | JavaScript, **Next.js**, Node.js (iç sayfalar) | — | Cloudflare | Cloudflare AS13335 arkasında | [W3Techs](https://w3techs.com/sites/info/ntv.com.tr) |
| aa.com.tr | JavaScript/TypeScript, **Next.js**, Node.js, Nginx | jQuery/Bootstrap "yakın zamana kadar" | listelenmedi | sunucu Türkiye'de | [W3Techs](https://w3techs.com/sites/info/aa.com.tr) |
| sozcu.com.tr | listelenmedi | yalnız JS (jsDelivr yakın zamana kadar) | Cloudflare | sunucu Türkiye'de | [W3Techs](https://w3techs.com/sites/info/sozcu.com.tr) |
| t24.com.tr | **PHP** | jQuery 3.6.0, Bootstrap, Animate | Cloudflare, cdnjs, jsDelivr | Cloudflare arkasında | [W3Techs](https://w3techs.com/sites/info/t24.com.tr) |
| cumhuriyet.com.tr | **ASP.NET** | jQuery 3.7.1 | Cloudflare | Cloudflare arkasında | [W3Techs](https://w3techs.com/sites/info/cumhuriyet.com.tr) |
| birgun.net | listelenmedi | jQuery 3.6.3, Bootstrap | Cloudflare | Cloudflare arkasında | [W3Techs](https://w3techs.com/sites/info/birgun.net) |
| olay.com.tr (Bursa yerel) | **PHP 8.5, WordPress**, Plesk, Linux | yalnız JS | Cloudflare, cdnjs | Cloudflare arkasında | [W3Techs](https://w3techs.com/sites/info/olay.com.tr) |

**Yerli "haber yazılımı" satıcıları**
- Listelerde sık geçenler: Habersoft, TE Bilişim, Tumeva, Gazisoft, Medya İnternet (Kulga), Webaksiyon; bir blog TE Bilişim için 10.000–40.000 TL, Habersoft için 20.000–60.000 TL fiyat aralığı veriyor; Habersoft satıcı sayfası 250'den fazla haber sitesi kullandığını iddia ediyor **[zayıf — SEO amaçlı listeler ve satıcı beyanı]** — [kobazoglu.com 2025](https://kobazoglu.com/en-iyi-haber-yazilimlari.html); [haberscript.com fiyatlar](https://www.haberscript.com/blog-turkiye-de-satisa-sunulan-haber-sitesi-yazilimlari-fiyatlari-41)
- Akasyam (Ocak 2025) listesi: Webay, Habersoft, TE Bilişim, Medya İnternet Kulga ("yerel ve bölgesel siteler için", "düşük maliyet"), Gazisoft; hiçbir satıcı için dil/çerçeve belirtilmemiş; listeyi yayınlayan sitenin kendisi Gazisoft altyapısında (çıkar çatışması) **[zayıf]** — [Akasyam](https://www.akasyam.com/turkiyenin-en-iyi-haber-yazilimlari-197221/)
- Diğer satıcı sayfaları: [Tumeva](https://www.tumeva.com/), [Medya İnternet](https://www.medyainternet.com/), [Gidea](https://gidea.tr/haber-yazilimi) **[birincil satıcı pazarlaması]**
- TE Bilişim'in App Store'da "TE Bilişim: Haber Yazılımı" adlı bir uygulaması var (şirket: TE Bilişim Yazılım İnternet Kiralama Hizmetleri San. ve Tic. Ltd. Şti.) — satıcının müşterilerine mobil uygulama da sunduğuna işaret ediyor, uygulama teknolojisi belirtilmiyor **[birincil, App Store]** — [App Store](https://apps.apple.com/us/app/id895746354)
- R10 forumunda PHP tabanlı "HaberSistemim" gibi küçük ölçekli scriptler, GitLab'da "haber-yazilimi" etiketli Türkçe projeler var **[zayıf]** — [R10](https://www.r10.net/1069040294-post1.html); [GitLab topic](https://gitlab.com/explore/projects/topics/haber-yazilimi)
- W3Techs bazı küçük Türk haber sitelerinde WordPress (PHP + MySQL) tespit ediyor (ör. adanahaberal.com) **[ikincil]** — [W3Techs adanahaberal.com](https://w3techs.com/sites/info/adanahaberal.com)

**İş ilanları**
- Hürriyet/Demirören'e ait güncel teknoloji ilanı bulunamadı. İstanbul'daki "Yeninesil İnternet Teknolojileri" ilanı React + Next.js + TypeScript ile "mevcut siteleri yeni altyapıya taşıma" işini tanımlıyor (yayıncı olup olmadığı belirsiz) **[ikincil]** — [Techcareer](https://www.techcareer.net/jobs/detail/kdemli-front-end-uzman-react-next.js-4250654)

### Inferences
- Merlin CDN + Amazon kombinasyonunun Demirören (Hürriyet, Milliyet, CNN Türk) ve Habertürk'te ortak çıkması, Türk büyük gruplarının ortak bir yerli CDN tercihine işaret ediyor; Sabah (Turkuvaz) ise CloudFront.
- Türkiye'de ASP.NET hâlâ büyük grup standardı; bu kadroların .NET geçmişinden geldiğini düşündürüyor (kaynakla doğrulanmadı). Next.js'e geçmiş görünen iki kurum (NTV, AA) — AA kamu kurumu, NTV büyük grup — "yerel gazete ölçeğinde" bir örnek değil.
- Bursa'daki yerel rakip Olay'ın WordPress + Cloudflare üzerinde olması, yerel pazardaki tipik çözümün "hazır PHP sistemi + Cloudflare" olduğu yönündeki genel izlenimle tutarlı.
- Hiçbir Türk yayıncının mühendislik blogu, konferans konuşması ya da göç gerekçesi bulunamadı; Türk tarafındaki her şey dış tespit verisi.

### Gaps
- Sözcü, BirGün, CNN Türk, Habertürk için sunucu dili/CMS tespit edilemedi (Cloudflare/Merlin arkasında).
- Türk satıcıların (TE Bilişim, Habersoft, Tumeva, Gazisoft, Kulga) hangi dil/çerçeveyle yazıldığı, müşteri sayıları ve pazar payları için bağımsız kaynak yok.
- Türk sitelerinin mobil uygulama teknolojisi (native/Flutter/webview) için kaynak bulunamadı.
- Kariyer.net / LinkedIn'de Demirören, Turkuvaz, Ciner, Doğuş ilanları bu turda bulunamadı; ayrı ve hedefli bir arama gerekir.
- W3Techs tarama tarihleri görünmediği için tabloda "şu an" denen değerler 2026'nın hangi ayına ait, bilinmiyor.
