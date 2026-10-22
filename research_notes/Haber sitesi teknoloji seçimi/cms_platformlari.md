# Haber yayıncıları için CMS platformları (headless ve yönetilen), 2024–2026 — Bursa Hakimiyet için değerlendirme

> Araştırma tarihi: 21 Ekim 2026. Haber sitesi taranmadı, User-Agent değiştirilmedi; yalnızca üretici belgeleri, Google News Initiative (GNI) CMS dizini, güvenlik raporları ve ikincil kaynaklar kullanıldı.
> İşaretler: **[ikincil]** = üretici dışı blog/derleme; **[üretici]** = üreticinin kendi pazarlama metni; **[genel bilgi, doğrulanmadı]** = bu oturumda kaynakla teyit edilemedi, rapor yazarı kullanmadan önce doğrulamalı.
> Bağlam: PostgreSQL sabit; mevcut yığın Python 3.12 + Django 5.2 + özel panel; ~1.038.474 haber zaten yeni sisteme alınmış durumda (proje belleği); tek kişi + yapay zekâ ajanları; sırada yerel iOS/Android uygulaması.

## 1. PostgreSQL desteği ve SaaS-only ayrımı

### Takeaway
Doğal PostgreSQL desteği olan adaylar Wagtail, Payload (Postgres adaptörü), Strapi ve Directus; Ghost (yalnız MySQL 8) ve WordPress (resmî olarak yalnız MySQL/MariaDB) PostgreSQL şartını karşılamıyor. Sanity, Contentful ve Arc XP veriyi kendi bulutlarında tutan SaaS ürünleri; bunlarda "PostgreSQL sabit" şartı ancak PG'yi ikincil kopya/arşiv olarak tutarak sağlanabilir.

### Cited Findings
- **Ghost:** Resmî belgeye göre üretimde desteklenen tek veritabanı MySQL 8; SQLite yalnız geliştirme içindir. Ekip bunu bakım yükünü sınırlamak için bilinçli bir dar destek kümesi olarak tanımlıyor — [Ghost Docs: Supported databases](https://docs.ghost.org/faq/supported-databases)
- **WordPress:** Yalnız MySQL ve MariaDB'yi destekliyor (2019 tarihli kaynak) — [Severalnines](https://severalnines.com/?p=12539). PostgreSQL ancak resmî olmayan PG4WP eklentisiyle mümkün; eklenti `wpdb` sınıfındaki `mysqli_` çağrılarını yakalayıp SQL'i yeniden yazıyor, PHP 8.1+ ve PostgreSQL 14.2 ile, WordPress 6.5.3/6.4.3 (v3 dalı) üzerinde test edilmiş — [PG4WP GitHub](https://github.com/PostgreSQL-For-Wordpress/postgresql-for-wordpress). PG4WP'nin her sayfada SQL yeniden yazdığı için MySQL'e göre yavaş olması beklendiği ve son büyük sürümlerle test edilmediği bildiriliyor **[ikincil]** — [Hevo](https://hevodata.com/learn/wordpress-postgresql)
- **Payload:** Resmî `@payloadcms/db-postgres` paketi Drizzle ORM ve `node-postgres` ile "sizin sağladığınız" bir Postgres'e bağlanır; okuma kopyası (`readReplicas`), çok sayıda blok için `blocksAsJSON` seçeneği, üretimde migration denetimi ve doğrudan Drizzle erişimi (`payload generate:db-schema`) var — [Payload Docs: Postgres](https://payloadcms.com/docs/database/postgres). Belge sitesinde `v4` yolu da bulunuyor — [Payload Docs v4: Postgres](https://payloadcms.com/docs/v4/database/postgres.md)
- **Strapi:** Strapi Cloud'da barındırılan her uygulama otomatik olarak PostgreSQL'e bağlanır — [Strapi Cloud fundamentals](https://docs.strapi.io/cloud/cloud-fundamentals)
- **Directus:** Self-host sayfası veritabanını "sizin sağlayıp bakımını yaptığınız altyapı" olarak sayıyor; desteklenen motor listesi ayrı "Requirements" sayfasında (bu oturumda açılamadı) — [Directus Docs: Self-hosting overview](https://directus.com/docs/self-hosting/overview)
- **Wagtail:** Wagtail 7.0 (LTS, 6 Mayıs 2025) Django 5.2'yi resmî olarak destekleyen ilk sürüm — [Wagtail 7.0 release notes](https://docs.wagtail.org/en/7.0/releases/7.0.html); 7.0 LTS Django 4.2/5.1/5.2 ve Python 3.9–3.13 ile uyumlu — [endoflife.date/wagtail](https://endoflife.date/wagtail)
- **Arc XP:** Çok kiracılı (multitenant) SaaS, AWS tabanlı mikroservisler, lisansa yönetilen barındırma ve CDN dahil; GNI incelemesi veritabanından söz etmiyor (inceleme 2023, "2024 Updates" bölümüyle) — [GNI CMS dizini: Arc XP](https://newsinitiative.withgoogle.com/cms-providers/arc-xp/)
- **Brightspot:** Yerel kurulumda MySQL, Maven, Tomcat, Solr ve Java SE ile ortam kurulduğu yazılıyor (üçüncü taraf entegratör, resmî mimari beyanı değil) **[ikincil]** — [Chetu](https://www.chetu.com/solutions/cms/brightspot.php)

### Inferences
- Wagtail bir Django uygulaması olduğu ve Django ORM'yi kullandığı için PostgreSQL birinci sınıf hedeftir; mevcut Django 5.2 + PG yığınıyla aynı veritabanını ve aynı süreç içini paylaşabilir **[genel bilgi, doğrulanmadı — Wagtail "Installation/Database" belgesiyle teyit edilmeli]**.
- Strapi self-host'ta PostgreSQL, MySQL/MariaDB ve SQLite'ı; Directus PostgreSQL, MySQL, SQLite, MS SQL, Oracle, CockroachDB gibi motorları destekler ve Directus mevcut bir şemayı "database-first" yaklaşımla içgözlemleyebilir **[genel bilgi, doğrulanmadı]**. Bu Directus özelliği, mevcut Django tablolarının üzerine yönetim arayüzü olarak oturtulabileceği anlamına gelir; ama Django migration'larıyla aynı şemayı iki aracın yönetmesi çakışma riski taşır.
- Sanity (Content Lake) ve Contentful verileri yalnızca üreticinin bulutunda tutulur; self-host seçeneği yoktur **[genel bilgi, doğrulanmadı]**. "PostgreSQL sabit" şartı bu ikisiyle ancak PG'yi ayna/yedek olarak tutmakla sağlanır; bu da ana kaynağın PG olmadığı anlamına gelir — şartı fiilen ihlal eder.
- Eleme sonucu (yalnız veritabanı şartına göre): Ghost ve self-host WordPress/WordPress VIP/Newspack **dışarıda** (PG4WP üretimde 1M haber için savunulamaz); Arc XP, Sanity, Contentful **şartı karşılamıyor** (SaaS); Brightspot belirsiz/Java-MySQL yığını.

### Gaps
- Directus'un güncel (v12) desteklenen veritabanı ve sürüm listesi bu oturumda açılamadı.
- Brightspot'un resmî veritabanı desteği (PostgreSQL var mı) için birincil kaynak bulunamadı.
- Strapi self-host veritabanı listesinin resmî belge bağlantısı bu oturumda açılmadı.

## 2. Fiyatlandırma ve lisans (2025–2026)

### Takeaway
Açık kaynak/self-host seçenekler (Wagtail, Payload, Strapi Community) lisans ücretsiz, maliyet barındırma ve emekte; ancak Strapi'de editoryal onay akışı ücretli sürümde, Directus 2026'da lisansını yine sıkılaştırdı. Kurumsal haber platformları yerel bir gazete için büyüklük sırası olarak pahalı: WordPress VIP yıllık 25.000 $'dan, Arc XP yıllık 50 bin–3 milyon $ (medyan 400–500 bin $) ve kurulum yaklaşık bir yıllık ücret kadar.

### Cited Findings
- **Arc XP:** Yönetilen barındırma dahil ticari lisans; yıllık ücret 50 bin $ – 3 milyon $, tahmini medyan 400–500 bin $/yıl; ilk uygulama maliyeti genellikle yıllık ücrete yakın; modüller tek tek alınabilir ama büyük müşteriler çoğunu/tamamını alıyor (GNI incelemesi 2023) — [GNI: Arc XP](https://newsinitiative.withgoogle.com/cms-providers/arc-xp/). Arc XP kendi SSS'inde fiyatı "modüler, genellikle kullanım, ölçek ve seçilen yeteneklere göre" diye tanımlıyor — [Arc XP FAQ](https://www.arcxp.com/faqs/)
- **WordPress VIP:** Resmî sitede planların yıllık 25.000 $'dan başladığı ve aylık tekil ziyaretçiye (MUV) göre ölçeklendiği yazıyor (arama özeti; sayfa bu oturumda 404 döndü) — [wpvip.com: How much does WordPress VIP cost?](https://wpvip.com/?p=98790). VIP Gold Partner Multidots, orta ölçekli yayıncıların tipik olarak yılda 50–200 bin $ ödediğini tahmin ediyor **[ikincil, ortaklık beyanlı]** — [Multidots](https://www.multidots.com/blog/wordpress-vip-pricing/). Vendr tek yüksek trafikli site için aylık 2.000–5.000 $ veriyor **[ikincil]** — [Vendr](https://www.vendr.com/marketplace/wordpress)
- **Newspack (Automattic, WordPress tabanlı, küçük yayıncılar):** Yıllık geliri 300 bin $ altı yayınlar için aylık 750 $; 300–600 bin $ için 1.500 $; 600 bin–1 milyon $ için 2.500 $; üstü ve çok siteli yapılar teklifle — [Newspack pricing](https://newspack.com/pricing/). 2023 GNI incelemesi gelir payına (%3–6) dayalı bir modelden söz ediyordu; güncel sayfa ile çelişiyor — [GNI: Newspack](https://newsinitiative.withgoogle.com/cms-providers/automattic-newspack/)
- **Brightspot:** Fiyat yayımlamıyor, teklifle; teklif bazlı planlar ve rehberli kurulum tek siteli küçük ekiplerin ihtiyacını aşabilir **[ikincil]** — [TheCMO Brightspot review 2026](https://thecmo.com/tools/brightspot-review/). Brightspot kendi karşılaştırmasında Arc XP'den düşük toplam sahip olma maliyeti iddia ediyor **[üretici]** — [Brightspot vs Arc XP](https://www.brightspot.com/cms-resources/cms-selection-guide/arc-xp-cms-alternative)
- **Sanity:** Free 0 $; Growth koltuk başına aylık 15 $ (en fazla 50 koltuk; Viewer rolü ücretsiz); Enterprise teklifle; ek kota 299 $/ay, ek dataset 999 $/ay **[ikincil, 2026]** — [Flow Ninja](https://www.flowninja.com/blog/sanity-cms-pricing); [Webstacks](https://www.webstacks.com/blog/sanity-pricing-plans-compared) (Webstacks "10 kullanıcı 199 $/ay" diyerek çelişiyor; eski tier olabilir)
- **Contentful:** Free plan aylık 100.000 API çağrısı, 50 GB bant genişliği, **ticari kullanım yasak**; Lite aylık 1.000.000 çağrı, 100 GB, aşım 1M çağrı başına 5 $; Premium özel fiyat, sınırsız çağrı — [Contentful usage limits](https://www.contentful.com/help/admin/usage/usage-limit/). Lite fiyatı resmî sayfada 300 $/ay; CostBench 850 $/ay diyor (orta güven) **[çelişki]** — [Costbench](https://costbench.com/software/headless-cms/contentful/)
- **Strapi:** Topluluk çekirdeği MIT; `ee/` klasörlerindeki Enterprise özellikleri ayrı ticari lisans — [Geekflare](https://geekflare.com/open-source/strapi/). Review Workflows (çok aşamalı editoryal onay) yalnız Enterprise'da — [Strapi Docs: Review workflows](https://docs.strapi.io/cms/features/review-workflows). SSO ve audit log da ücretli; Growth planı 3 kullanıcı için aylık 45 $ ve Releases, Live Preview, 14 gün içerik geçmişi ekliyor **[ikincil]** — [Geekflare](https://geekflare.com/open-source/strapi/). Strapi Cloud: 1 ücretsiz + 3 ücretli plan (Essential, Pro, Scale); Essential 29 $'dan 15 $'a indi — [Strapi blog](https://strapi.io/blog/lower-prices-and-greater-flexibility-with-improved-strapi-cloud-pricing); varlık depolama Free 10 GB, Essential 50 GB, Pro 250 GB, Scale 1.000 GB — [Strapi Cloud billing](https://docs.strapi.io/cloud/getting-started/usage-billing.md)
- **Directus:** Önce BSL 1.1 idi (toplam finansmanı 5 milyon $ üzeri kuruluşlar lisans almalı) — [Directus: why we are relicensing](https://directus.io/blog/why-we-are-relicensing-directus). **Directus v12 (Mayıs 2026) ile lisans "Monospace Sustainable Core License (MSCL-1.0-GPL)" oldu**: kaynak-erişilebilir (açık kaynak değil), Fair Core License türevi, 4 yıl sonra GPL'e dönüşüyor; ücretsiz kullanım ayrı bir "Innovation Grant" ile tanımlanıyor; eşik kaynaklarda farklı (yıllık gelir 5 M $ altı ve 50 çalışan / 25 çalışan) **[çelişki]**; onur sistemi yerine kayıt anahtarı geliyor — [Directus v12 license change](https://directus.com/resources/directus-v12-license-change); [MSCL metni](https://directus.io/mscl); [Topluluk tartışması](https://community.directus.io/t/directus-license-revision-community-feedback-requested/2125). Topluluk eleştirisi: "her seferinde yeni lisans öncekinden daha kısıtlayıcı" — aynı tartışma. Directus Cloud Core/Team için 99 $/ay eklenti — [Directus pricing](https://directus.com/pricing)
- **Ghost(Pro):** Temmuz 2025 itibarıyla Starter 15 $/ay, Publisher 29 $/ay, Business 199 $/ay (yıllık faturalamada); mevcut müşteriler eski fiyattan devam — [Ghost Forum, Temmuz 2025](https://forum.ghost.org/t/updated-ghost-pro-pricing-july-2025-15-mo-starter-29-mo-publisher-199-mo-business/59090)
- **Payload:** Figma, 17 Haziran 2025'te Payload'ı satın aldığını duyurdu; Payload'ın "açık kaynak ürün olarak kalacağını" ve "yakın gelecekte kullanıcılar için hiçbir şeyin değişmeyeceğini" yazdı; MIT lisansı, self-host ve Payload Cloud hakkında yazıda bilgi yok — [Figma blog: Payload joins Figma](https://www.figma.com/blog/payload-joins-figma/). Satın alma sonrası Payload Cloud'un yeni kayıt almayı durdurduğu bildiriliyor **[ikincil]** — [Build with Matija: Payload 4.0](https://buildwithmatija.com/blog/payload-4-0)
- **Türk "haber yazılımı" satıcıları:** HaberSoft 2016'da yerel gazeteler için 1.500 TL'den başlayan paketlerle tanıtılmıştı, 15 sitede kullanılıyordu (2016 verisi) — [Webrazzi, 2016](https://webrazzi.com/2016/04/08/habersoft-yerel-gazete-ve-haber-siteleri-icin-icerik-yonetim-sistemi-yazilimi/). 2024 tarihli bir forum başlığında Tebilişim (kendi sunucu zorunluluğu, pahalı bulunuyor; seçim sonuçları ve imsakiye botları var), Daktilo (sunucu + ayrı yazılım ücreti), Cmbilişim (yıllık güncelleme ücreti belirsiz/pahalı), Tumeva, Gazisoft (eski içeriği 301 ile ID tabanlı adrese taşıdığı iddiası), Kanthemes, Esenhaberi anılıyor; bir kullanıcı satıcıların çoğunun kodu kendi sunucusunda (şifreli) tuttuğunu ya da sonradan yüksek sunucu ücreti istediğini yazıyor **[forum görüşü, tek kaynak]** — [R10.net, 6 Nisan 2024](https://www.r10.net/sorum-var/4047648-hangi-haber-yazilimini-sizce-secmeliyim.html)

### Inferences
- Bursa Hakimiyet ölçeğinde (tek kişi, yerel gazete) Arc XP'nin medyan yıllık ücreti tek başına küçük bir haber merkezinin tüm bütçesini aşar; WordPress VIP'nin 25 bin $ taban fiyatı da PostgreSQL şartı nedeniyle zaten tartışma dışı.
- Strapi'nin "ücretsiz" sürümü haber masası için gereken onay akışını (Review Workflows) içermiyor; mevcut Django panelinde bu zaten özel yazılmışsa, Strapi'ye geçiş ya Enterprise ücreti ya da aynı işi yeniden yazmak demek.
- Directus'un lisansı iki yılda iki kez değişti (BSL → MSCL); "lisans riski" bu aday için gerçek ve süregelen bir risk.
- Türk haber yazılımı paketlerinin ortak örüntüsü (forum beyanlarına göre) kapalı kod + satıcı sunucusu; bu, PostgreSQL şartı, özel konu takibi motoru ve yapay zekâ editörü gibi özelliklerle bağdaşmaz; ayrıca bu ürünlerin hangi veritabanını kullandığına dair kaynak bulunamadı.

### Gaps
- Arc XP için 2025–2026 güncel fiyat aralığı (GNI verisi 2023) bulunamadı.
- Brightspot için hiçbir fiyat göstergesi bulunamadı.
- Türk satıcıların (Tebilişim, Daktilo, Cmbilişim, Gazisoft vb.) güncel fiyat listesi, veritabanı ve kaynak kodu teslim koşulları için birincil kaynak bulunamadı; satıcı siteleri bu oturumda taranmadı.
- Payload Cloud'un kapanışı yalnız ikincil kaynakta; resmî duyuru bulunamadı.

## 3. Hazır haber masası özellikleri (iş akışı, zamanlama, canlı blog, son dakika, revizyon, SEO, Google News sitemap, görsel türevleri, AMP, push, paywall/reklam)

### Takeaway
Haber masasına özgü özellikleri "kutudan" sunan tek aday grubu Arc XP / Brightspot / WordPress VIP (+ eklentiler) gibi kurumsal platformlar; genel amaçlı headless CMS'lerde (Payload, Strapi, Directus, Sanity, Contentful) canlı blog, son dakika, Google News sitemap, push ve paywall hazır gelmez, yazılması gerekir — yani Django'da zaten yapılmış olan işin bir kısmı yeniden yapılır.

### Cited Findings
- **Arc XP:** Çekirdekte içerik yaşam döngüsü (yazma, sınıflama, düzenleme, onay, yayın, yeniden kullanım, arşiv), WebSked ile planlama/görevlendirme, bildirimler ve uyarılar, dijital + basılı abonelik yönetimi, video/foto yönetimi, A/B testi, SEO, çoklu yayın yönetimi, kullanıcı kaydı, mobil uygulama yönetimi, React tabanlı ön yüz (PageBuilder Engine), AI Editor aracı; reklam yönetimi, site içi arama, bülten, yorum, basılı yayın ve sosyal paylaşım eklenti/üçüncü taraf; canlı blog ve AMP incelemede anılmıyor; arayüz dilleri arasında Türkçe yok (Almanca, İngilizce, İspanyolca, Fransızca, Japonca, Korece) — [GNI: Arc XP](https://newsinitiative.withgoogle.com/cms-providers/arc-xp/)
- **Strapi:** Draft & publish, rol tabanlı izinler ve içerik geçmişi topluluk sürümünde; çok aşamalı onay (Review Workflows), SSO, audit log Enterprise'da; Releases ve Live Preview Growth planında — [Strapi Docs: Review workflows](https://docs.strapi.io/cms/features/review-workflows); [Geekflare](https://geekflare.com/open-source/strapi/)
- **Wagtail (headless kullanımda):** Taslak sayfalar genel API'den sunulamadığı için önizleme `wagtail-headless-preview` gibi üçüncü taraf paketle çözülüyor; görsel türevleri için `ImageRenditionField` (önceden tanımlı boyutlar) ya da imzalı anahtar isteyen dinamik görsel servisi var; zengin metin API'de işlenmemiş geliyor; form gönderimi için resmî API yok — [Wagtail Docs: Headless](https://docs.wagtail.org/en/stable/advanced_topics/headless.html)
- **Wagtail 7.0:** Taslak kaydederken zorunlu alan doğrulaması erteleniyor (taslak kaydı kolaylaşıyor) — [Wagtail 7.0 release notes](https://docs.wagtail.org/en/7.0/releases/7.0.html)
- **Sanity:** Kendini "haber merkezleri için Content Operating System" olarak pazarlıyor **[üretici]** — [Sanity: Newspaper CMS](https://www.sanity.io/newspaper-cms)
- **Payload 4.0 (önizleme):** Yeniden tasarlanan yönetim arayüzü, yerel hiyerarşi/klasör/etiket, MCP ve yapay zekâ ajan iş akışları; olası kırıcı değişiklikler (stil, klasörler, eklenti yapılandırması); 1 Temmuz 2026 itibarıyla kararlı sürüm yok, beta tarihi kaynaklarda çelişkili (Nisan 2026 beta iddiası tek kaynakta) **[ikincil]** — [Build with Matija](https://buildwithmatija.com/blog/payload-4-0); [Distill Intelligence](https://distillintelligence.com/news/payload); [Oflight](https://www.oflight.co.jp/en/columns/payload-cms-nextjs-figma-2026)
- **Newspack:** Küçük yayıncılar için "paketlenmiş ve fiyatlandırılmış" (çoğunlukla Kuzey Amerika) — [GNI CMS dizini](https://newsinitiative.withgoogle.com/cms-providers/); barındırma ve 200 GB depolama dahil, taşıma kurulum ücreti yok — [Newspack pricing](https://newspack.com/pricing/)

### Inferences
- Django'nun `django.contrib.sitemaps` ve Wagtail'in `wagtail.contrib.sitemaps` modülleri standart sitemap üretir; Google News sitemap (`news:` ad alanı) ikisinde de hazır değildir ve elle yazılır **[genel bilgi, doğrulanmadı]**. Bu, mevcut Django kodunda zaten yazılmış/yazılacak bir parçadır; hiçbir headless aday bunu bedavaya getirmez.
- Canlı blog, son dakika bandı, Basın İlan Kurumu resmî ilan biçimi, döviz/hava/namaz/eczane bileşenleri, konu takibi motoru, eski site adres uyumluluğu gibi özellikler hiçbir genel CMS'te hazır değil; hepsi her durumda özel kod. Türkiye'ye özgü olanlar (BİK, namaz vakitleri, nöbetçi eczane) yalnız Türk haber yazılımlarında hazır gelebilir (forumda "seçim sonuçları, imsakiye botları" anılıyor — [R10.net](https://www.r10.net/sorum-var/4047648-hangi-haber-yazilimini-sizce-secmeliyim.html)).
- AMP: Google'ın Top Stories için AMP şartını 2021'de kaldırdığı bilinir; AMP desteği bir seçim ölçütü olmamalı **[genel bilgi, doğrulanmadı]**.

### Gaps
- Payload, Directus, Sanity, Contentful için canlı blog / son dakika / Google News sitemap / push / paywall hazır özellik tablosu kaynaklı olarak çıkarılamadı (araştırma bütçesi; üretici belge sayfaları tek tek açılmadı).
- Brightspot'un haber masası özellik listesi için yalnız pazarlama sayfaları var, bağımsız inceleme yok (GNI dizini Brightspot'u kapsam dışı bırakmış — [GNI CMS dizini](https://newsinitiative.withgoogle.com/cms-providers/)).
- WordPress VIP'nin hazır haber özellikleri (Live Blog eklentisi vb.) için birincil kaynak bu oturumda açılmadı.

## 4. Mobil uygulama için API kalitesi (REST/GraphQL, webhook, önizleme)

### Takeaway
Tüm headless adaylar REST ve/veya GraphQL sunuyor; Wagtail'in yerleşik REST API'si var ama GraphQL, taslak önizleme ve zengin metin işleme için ek paket/işçilik gerekiyor. Mevcut Django projesine mobil API eklemek için ayrı bir CMS'e gerek yok; Django REST Framework ya da Django Ninja aynı işi aynı veritabanı üzerinde görür.

### Cited Findings
- **Wagtail:** Yerleşik REST API (önbelleğe alınabilir; ama bazen çoklu istek, gereksiz veri ve sabit veri yapısı sorunu); GraphQL yerel değil, `wagtail-grapple` (Torchbox) ya da `strawberry-wagtail` gerekir; özel API için Django REST Framework kullanılabilir; çoklu site, ön yüz ve API alan adları farklıysa Host başlığı çakışması yüzünden "🛑" olarak işaretlenmiş; parola korumalı sayfalar headless ön yüzde görüntülenemiyor — [Wagtail Docs: Headless](https://docs.wagtail.org/en/stable/advanced_topics/headless.html)
- **Wagtail 7.0:** Django Ninja kurulum rehberi eklendi — [Wagtail 7.0 release notes](https://docs.wagtail.org/en/7.0/releases/7.0.html)
- **Payload:** Postgres adaptöründe Drizzle doğrudan erişilebilir; okuma kopyaları destekleniyor (yüksek okuma yükü olan mobil API için ilgili) — [Payload Docs: Postgres](https://payloadcms.com/docs/database/postgres)
- **Contentful:** Teslim (CDA), önizleme (CPA) ve yönetim (CMA) API'leri ayrı; Lite'ta aylık 1M çağrı sınırı ve aşımda 1M başına 5 $ — [Contentful usage limits](https://www.contentful.com/help/admin/usage/usage-limit/)
- **Arc XP:** "Mobil uygulama yönetimi" çekirdek modüller arasında — [GNI: Arc XP](https://newsinitiative.withgoogle.com/cms-providers/arc-xp/)
- **Strapi:** Live Preview Growth planında (ücretli) — [Geekflare](https://geekflare.com/open-source/strapi/)

### Inferences
- Contentful'da mobil uygulama trafiği doğrudan API çağrısı sayacına yazılır; push sonrası ani okuma dalgaları kotayı hızla tüketebilir (CDN önbelleği çağrı sayısını azaltır ama sınır modeli SaaS maliyetini trafikle bağlar).
- Payload'ın REST + GraphQL + "Local API" üçlüsü, Strapi'nin REST + GraphQL eklentisi, Directus'un REST + GraphQL + WebSocket, Sanity'nin GROQ + GraphQL ve webhook'ları, WordPress'in REST API + WPGraphQL eklentisi yaygın bilinir **[genel bilgi, doğrulanmadı]**. API kalitesi adaylar arasında ayırt edici değil; ayırt edici olan veritabanı ve sahiplik.
- Bursa Hakimiyet için: mobil uygulamanın ihtiyacı (haber listesi, detay, kategori, son dakika, push token kaydı) dar ve bellidir; mevcut Django modelleri üzerine DRF/Ninja ile versiyonlu bir `/api/v1/` yazmak, ikinci bir CMS'i senkron tutmaktan daha az hareketli parça demektir.

### Gaps
- Adayların webhook ve önizleme özelliklerinin resmî belgelerle karşılaştırmalı tablosu bu oturumda çıkarılamadı.

## 5. Ölçek kanıtı: hangi yayıncılar kullanıyor, milyonluk arşiv var mı

### Takeaway
Kurumsal platformların büyük yayıncı listesi var (Arc XP: Boston Globe, El País; Brightspot: Politico, LA Times; Sanity: Semafor, Politico, NRK — üretici beyanı), ancak kaynaklı "1 milyon makale arşivi" rakamı hiçbir aday için bulunamadı. Wagtail'in en güçlü haber kanıtı NYPR/Gothamist (150 bin sayfa, 2021); Payload, Strapi, Directus için kaynaklı haber yayıncısı vaka çalışması bulunamadı.

### Cited Findings
- **Arc XP:** Atlanta Journal-Constitution, Boston Globe, La Nación (Arjantin), El País (İspanya); Washington Post kökeni; ilk dış lisanslayan Willamette Week (2016); şirket ~300 kişi, gelirin 100 M $/yıl üzerinde olduğu ama hâlâ zarar ettiği ve sahiplik belirsizliği bildiriliyor (GNI 2023) — [GNI: Arc XP](https://newsinitiative.withgoogle.com/cms-providers/arc-xp/)
- **Brightspot:** POLITICO, Los Angeles Times, U.S. News & World Report, Univision **[üretici]** — [Brightspot media & publishing](https://www.brightspot.com/cms-use-cases/media-publishing/6-media-and-publishing-success-stories); POLITICO vakası: eski ev yapımı CMS'ten taşındı, 3 site (POLITICO, POLITICO PRO, POLITICO Magazine), **190 bin makale taşındı**, 600+ içerik yayımcısı **[üretici]** — [Brightspot: POLITICO case study](https://www.brightspot.com/customers/case-studies/politico)
- **Wagtail:** New York Public Radio, Gothamist.com için headless Wagtail'e geçti, **150 bin sayfa (20 yıllık içerik)**; WNYC, WQXR, WNYC Studios gibi markaları çok kiracılı Wagtail platformuna taşıyor; seçimde maliyet/hız ve ekibin Django'ya aşinalığı belirleyici (2021) — [Wagtail blog: NYPR on Wagtail](https://wagtail.org/blog/nypr-on-wagtail/). Finfeed (Avustralya finans haberi) haber sitelerini Wagtail'le çalıştırıyor ve üretim/revizyon/onay akışını Wagtail'de kuruyor — [Torchbox](https://torchbox.com/wagtail-cms-services/blog/wagtail-conference-and-sprint-philly/). Wagtail Space US'de "Running a Multi-Site Newsroom in Wagtail" (StocksDigital) sunumu — [Columbia CTL](https://compiled.ctl.columbia.edu/articles/wagtailspace-us-event)
- **Sanity:** Medya müşterileri Semafor, Complex, CoinDesk, National Geographic, Politico, NRK; Morning Brew 13 markayı 6 mühendisle tek sistemde yönetiyor **[üretici]** — [Sanity: media publishing](https://www.sanity.io/campaign/media-publishing)
- **Payload:** Figma, "birkaç Fortune 100 şirketinin" Payload kullandığını yazıyor; haber yayıncısı adı yok — [Figma blog](https://www.figma.com/blog/payload-joins-figma/)
- **Strapi:** Haber yayıncısına özgü vaka çalışması bulunamadı **[ikincil özet]** — [Geekflare](https://geekflare.com/open-source/strapi/)
- **Arc XP uygunluğu:** Büyük haber kuruluşlarına uygun; "kayda değer iç geliştirici ekibi olmayan" kuruluşlara "kötü uyuyor"; 200 kişilik bir haber merkezinin 10 Arc eğitimli geliştirici çalıştırdığı bildiriliyor — [GNI: Arc XP](https://newsinitiative.withgoogle.com/cms-providers/arc-xp/)
- **GNI dizini:** 20 sağlayıcı içeriyor (Arc XP, Atex, BLOX, Drupal, Eidosmedia, Ghost, InterRed, Layout, Livingdocs, Naviga, Newspack, Quintype, Ring Publishing, Stibo DX, Tresite, WhiteBeard, WoodWing, WordPress Foundation, WordPress VIP, Xalok); Brightspot, CoreMedia, Sirius kapsam dışı; Türk satıcı yok — [GNI CMS dizini](https://newsinitiative.withgoogle.com/cms-providers/)

### Inferences
- Bursa Hakimiyet'in 1.038.474 haberlik arşivi, kaynaklı vaka çalışmalarındaki rakamların (Politico 190 bin, Gothamist 150 bin) 5–7 katı. Milyonluk ölçek, bir CMS markasından çok PostgreSQL indeksleri, sayfalama stratejisi (keyset), tam metin arama ve önbellekle ilgili; bunlar mevcut Django + PG yığınında zaten yönetilebilir.
- Wagtail'in sayfa ağacı (`Page` modeli, treebeard materyalize yol) 1M kayıtlı tek bir ebeveyn altında performans ayarı ister; haberleri `Page` yerine snippet/özel model olarak tutmak gerekebilir **[genel bilgi, doğrulanmadı — Wagtail topluluğunda bilinen bir konu; benchmark bulunamadı]**.

### Gaps
- Hiçbir aday için kaynaklı "milyonlarca makale" arşiv rakamı bulunamadı.
- Türkiye'de hangi ulusal/yerel gazetenin hangi CMS'i kullandığına dair kaynaklı liste bulunamadı (haber siteleri taranmadı).

## 6. Bağımlılık (lock-in), veri taşınabilirliği ve özel özelliklerle genişletilebilirlik

### Takeaway
En düşük bağımlılık, verinin zaten sizin PostgreSQL'inizde ve sizin Django modellerinizde durduğu mevcut yapı; Wagtail aynı yığında kaldığı için ikinci en düşük risk. SaaS platformlarında (Arc XP, Sanity, Contentful) veri ve iş akışı üreticiye bağlanır; açık-çekirdek ürünlerde lisans değişikliği (Directus) ve satın alma sonrası belirsizlik (Payload/Figma) somut risk.

### Cited Findings
- **Payload/Figma:** Satın alma Haziran 2025; "açık kaynak kalacak", "yakın gelecekte hiçbir şey değişmiyor" — [Figma blog](https://www.figma.com/blog/payload-joins-figma/); Figma'nın tasarım ile içeriği birleştirme (Figma Sites) stratejisi yorumlanıyor **[ikincil]** — [Moving Primates](https://www.movingprimates.de/en/blog/power-shift-figma-swallows-headless-cms-payload); [CMSWire](https://www.cmswire.com/digital-experience/when-cms-meets-ux-design-what-figmas-payload-deal-really-means/); Payload Cloud yeni kayıt almıyor **[ikincil]** — [Build with Matija](https://buildwithmatija.com/blog/payload-4-0)
- **Directus:** BSL 1.1 → MSCL (v12, 2026); kayıt anahtarıyla denetim; topluluk "her lisans bir öncekinden kısıtlayıcı" diyor — [Directus v12 license change](https://directus.com/resources/directus-v12-license-change); [Topluluk](https://community.directus.io/t/directus-license-revision-community-feedback-requested/2125)
- **Strapi:** MIT çekirdek + kapalı `ee/` kodu; editoryal onay akışı kapalı kodda — [Geekflare](https://geekflare.com/open-source/strapi/)
- **Contentful:** Kota aşımında ücretsiz plan ek çağrıya izin vermiyor; büyük kullanımda özel Enterprise sözleşmesine geçiş gerekiyor **[ikincil]** — [FocusReactive](https://focusreactive.com/blog/contentful-pricing/); [Contentful usage limits](https://www.contentful.com/help/admin/usage/usage-limit/)
- **Arc XP:** Ön yüz React tabanlı PageBuilder Engine; modüller AWS üzerinde çok kiracılı; "sahiplik belirsizliği" not edilmiş — [GNI: Arc XP](https://newsinitiative.withgoogle.com/cms-providers/arc-xp/)
- **Türk haber yazılımları:** Satıcıların kodu kendi sunucularında şifreli tuttuğu / sonradan yüksek sunucu ücreti istediği iddiası **[forum, tek kaynak, 2024]** — [R10.net](https://www.r10.net/sorum-var/4047648-hangi-haber-yazilimini-sizce-secmeliyim.html)
- **Wagtail:** Özel API için Django REST Framework kullanılabilir (yani Django ekosistemi açık) — [Wagtail Docs: Headless](https://docs.wagtail.org/en/stable/advanced_topics/headless.html); NYPR'nin seçiminde Django aşinalığı belirleyici — [Wagtail blog](https://wagtail.org/blog/nypr-on-wagtail/)

### Inferences
- Projede yazılmış özel özellikler (konu takibi motoru, yapay zekâ editör yardımcısı, canlı veri bileşenleri, BİK resmî ilan, eski site URL uyumu) Python/Django kodu. Wagtail dışındaki her aday (Node.js: Payload/Strapi/Directus; SaaS: Sanity/Contentful/Arc XP; PHP: WordPress; Java: Brightspot) bu kodun **başka bir dile/çalışma ortamına taşınmasını ya da yan servis olarak ayrı yaşatılmasını** gerektirir.
- Payload'ın Postgres şeması Drizzle ile Payload'ın kendi koleksiyon tanımından üretilir; mevcut Django tablolarını "olduğu gibi" kullanmaz — yeni şemaya veri göçü gerekir **[genel bilgi, doğrulanmadı]**. Directus mevcut şemayı içgözlemleyebildiği için teorik olarak en az göçlü Node seçeneğidir, ancak lisans riski en yüksek olanlardan biridir.
- Satın alma riski: Payload artık tasarım aracı şirketinin stratejisine bağlı; Figma'nın taahhüdü "yakın gelecek" ile sınırlı.

### Gaps
- Sanity/Contentful/Arc XP için tam veri dışa aktarma (export) biçimleri ve sözleşme sonu veri iadesi koşulları bu oturumda belgelenmedi.

## 7. Tek kişilik ekip için bakım yükü (yükseltme, güvenlik yaması, eklenti ekosistemi riski)

### Takeaway
WordPress ekosisteminde 2025'te 11.334 yeni açık (yıllık +%42), %91'i eklentilerde, %46'sı açıklandığında yamasız ve kitlesel istismara medyan 5 saat — tek kişilik bir ekip için eklenti yoğun WordPress en yüksek güvenlik bakım yüküdür. Wagtail LTS döngüsü yaklaşık yıllık; Payload 4.0 ve Directus v12 gibi büyük sürümler kırıcı değişiklik ve lisans değişikliği getiriyor.

### Cited Findings
- **WordPress (Patchstack, 2025 verisi, 2026 raporu):** 11.334 yeni açık (+%42); 4.124'ü (%36) gerçek tehdit; 1.966'sı (%17) yüksek önem; ~%91 eklenti, ~%9 tema, çekirdekte yalnız 6 (düşük öncelikli); %46'sı açıklandığında geliştirici yaması yoktu; yüksek etkili açıkların yaklaşık yarısı 24 saat içinde istismar edildi; yoğun istismar edilenlerde kitlesel istismara ağırlıklı medyan süre 5 saat; yüksek istismar edilebilir açıklar +%113; premium bileşenler geçerli raporların %29'u, bunların %76'sı istismar edilebilir; yaygın barındırma güvenlik ayarları saldırıların yalnız %26'sını engelledi — [Patchstack: State of WordPress Security in 2026](https://patchstack.com/whitepaper/state-of-wordpress-security-in-2026/)
- Yamasız açık oranı ikincil kaynaklarda "üçte bir" olarak da geçiyor **[çelişki; birincil kaynak %46 diyor]** — [web60.ie](https://web60.ie/blog/wordpress-plugin-vulnerabilities-record-2025)
- **Ghost:** Bakımı yönetilebilir tutmak için yalnız MySQL 8 desteği — [Ghost Docs](https://docs.ghost.org/faq/supported-databases)
- **Wagtail:** LTS sürümleri bir sonraki LTS'ye kadar (tipik ~12 ay) güvenlik ve veri kaybı düzeltmesi alıyor; 7.0 LTS 6 Mayıs 2025 — [Wagtail 7.0 release notes](https://docs.wagtail.org/en/7.0/releases/7.0.html); belge sitesinde 7.1–7.4 sürümleri mevcut — [Wagtail 7.4 docs](https://docs.wagtail.org/en/v7.4/releases/7.0.html.md)
- **Payload 4.0:** Stil, klasörler ve eklenti yapılandırmasında olası kırıcı değişiklikler **[ikincil]** — [Build with Matija](https://buildwithmatija.com/blog/payload-4-0)
- **Arc XP:** 7/24/365 e-posta/bilet ve Slack desteği; ama iç geliştirici ekibi gerektiriyor (200 kişilik merkezde 10 Arc geliştiricisi) — [GNI: Arc XP](https://newsinitiative.withgoogle.com/cms-providers/arc-xp/)
- **Türk haber yazılımları:** "Yıllık güncelleme ücreti" ve "sunucu zorunluluğu" şikâyetleri **[forum]** — [R10.net](https://www.r10.net/sorum-var/4047648-hangi-haber-yazilimini-sizce-secmeliyim.html)

### Inferences
- Mevcut özel Django çözümünde bakım yüzeyi: Django (LTS 5.2, Nisan 2028'e kadar destek — **[genel bilgi, doğrulanmadı]**), Python, PostgreSQL ve az sayıda bağımlılık. Wagtail eklemek bu yüzeye bir büyük bağımlılık ekler ama aynı dil/araç zincirinde kalır. Node tabanlı bir CMS eklemek ikinci bir çalışma zamanı, ikinci bir paket yöneticisi (npm tedarik zinciri) ve iki ayrı güvenlik yaması takvimi demektir.
- Tek kişi + yapay zekâ ajanları modelinde kodun tek dilde ve tek depoda olması, ajanların bağlamı kavrayabilmesi açısından da avantajlıdır.

### Gaps
- Strapi, Payload, Directus, Wagtail için yıllık güvenlik danışmanlığı (CVE) sayıları bu oturumda toplanmadı; GitHub yıldız sayıları ve sürüm sıklığı doğrudan repo sayfalarından alınmadı.

## 8. 1 milyon haberlik özel Django modelinden göç maliyeti

### Takeaway
Hiçbir kaynak bu göç için somut maliyet vermiyor; ancak Arc XP için "ilk uygulama ≈ bir yıllık lisans ücreti" (yani on binlerce–milyonlarca dolar) kaydı var. Bursa Hakimiyet'te 1M haber zaten PostgreSQL'deki Django modellerine alınmış olduğundan, herhangi bir CMS'e geçiş ikinci bir büyük göç, adres uyumluluğu katmanının yeniden kurulması ve özel özelliklerin taşınması anlamına gelir.

### Cited Findings
- **Arc XP:** İlk uygulama maliyeti tipik olarak yıllık ücrete yakın (yıllık 50 bin–3 M $) — [GNI: Arc XP](https://newsinitiative.withgoogle.com/cms-providers/arc-xp/)
- **Newspack:** Taşımada kurulum ücreti yok (bazı kısıtlarla) — [Newspack pricing](https://newspack.com/pricing/)
- **Brightspot / POLITICO:** Ev yapımı CMS'ten 190 bin makale taşındı **[üretici]** — [Brightspot: POLITICO](https://www.brightspot.com/customers/case-studies/politico)
- **NYPR / Wagtail:** 20 yıllık 150 bin sayfa headless Wagtail'e taşındı; seçimde mevcut Django becerisi belirleyici (2021) — [Wagtail blog](https://wagtail.org/blog/nypr-on-wagtail/)
- **Türk satıcılarda göç:** Tumeva'nın 13 bin içeriğin %90'ını, Gazisoft'un %100'ünü 301 yönlendirmeyle ID tabanlı adreslere taşıyabildiği iddiası **[forum, 2024]** — [R10.net](https://www.r10.net/sorum-var/4047648-hangi-haber-yazilimini-sizce-secmeliyim.html)
- **Wagtail headless yönlendirme:** Wagtail'in kendi rotalarına bağlı kalmak öneriliyor; özel ön yüz rotaları daha fazla bakım gerektiriyor ve "View Live" bağlantıları yanlış adrese gidebiliyor — [Wagtail Docs: Headless](https://docs.wagtail.org/en/stable/advanced_topics/headless.html)

### Inferences
- **Göç maliyetini belirleyen kalemler** (kaynaksız, mühendislik çıkarımı): (1) şema eşlemesi — haber, kategori, yazar, etiket, görsel, resmî ilan alanlarının hedef modele eşlenmesi; (2) gövde HTML'inin hedef zengin metin/blok biçimine dönüştürülmesi (Wagtail StreamField, Payload Lexical, Sanity Portable Text — her biri ayrı dönüştürücü ister); (3) görsellerin hedef medya kütüphanesine yeniden yüklenmesi ve türev üretimi; (4) eski site adres uyumluluğunun (301 haritası) yeni yönlendirme katmanında yeniden kurulması — SEO açısından en riskli kalem; (5) özel özelliklerin (konu takibi, yapay zekâ editör, canlı veri, BİK) yeniden bağlanması; (6) panelin editör eğitimi.
- Kaba ölçek: 1M kayıtlık toplu yükleme teknik olarak bir hafta sonu işi olabilir; asıl maliyet (2), (4) ve (5)'tir ve ayları bulabilir. Mevcut durumda bu iş Django tarafında zaten yapılmış (1.038.474 haber alınmış), yani bir CMS'e geçiş "sıfırdan göç" değil, **yapılmış bir göçün tekrarı** olur.
- Wagtail, mevcut Django projesine **kademeli** eklenebilen tek adaydır (aynı veritabanı, aynı kullanıcı modeli); örneğin yalnız statik/kurumsal sayfalar veya özel sayfalar için Wagtail kullanıp haber modelini mevcut haliyle bırakmak mümkündür **[genel bilgi, doğrulanmadı]**. Diğer tüm adaylar "ya hep ya hiç" geçiş ya da iki sistemi senkron tutma gerektirir.
- **Genel değerlendirme (rapor yazarı için):** Zorunlu PostgreSQL + Python/Django'da yazılmış özel özellikler + tek kişilik ekip + bütçe kısıtı birlikte düşünüldüğünde, hazır bir platforma geçmenin sağladığı ek değer (kurumsal haber özellikleri) yalnız Arc XP / Brightspot / WordPress VIP sınıfında anlamlı; bu sınıf ise ya PG şartını karşılamıyor ya da maliyet olarak yerel gazete ölçeğinin çok üstünde. Headless genel CMS'ler (Payload, Strapi, Directus, Sanity, Contentful) haber masası özelliklerini hazır getirmediği için özel Django panelinin yerine geçmekten çok, onu farklı bir dilde yeniden yazdırır. En makul "hazır parça" seçeneği, gerekirse mevcut Django projesinin içine Wagtail'i kısmi olarak eklemek; mobil uygulama API'si için ise DRF/Django Ninja yeterli.

### Gaps
- 1M kayıtlık Django → (Wagtail/Payload/Strapi/Sanity) göçü için yayımlanmış maliyet veya süre verisi bulunamadı.
- Türk haber yazılımı satıcılarının 1M haberlik arşivi taşıyıp taşıyamadığına ve hangi veritabanını kullandığına dair kaynak bulunamadı.
