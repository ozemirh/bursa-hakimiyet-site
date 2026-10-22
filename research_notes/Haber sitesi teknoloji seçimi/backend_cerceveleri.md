# Backend çerçeveleri karşılaştırması — Bursa Hakimiyet (haber sitesi + editoryal panel + mobil uygulama API'si), Ekim 2026

> Araştırma tarihi: 21 Ekim 2026. Sabit kısıtlar: PostgreSQL değişmeyecek; mevcut kod Python 3.12 + Django 5.2, sunucu tarafı HTML, Django içinde özel panel; ekip bir kişi + yapay zekâ ajanları; sırada yerli iOS/Android uygulaması var.
> Tarihi eski olan veriler yılıyla işaretlendi. Haber siteleri doğrudan taranmadı; resmî ve ikincil kaynaklar kullanıldı.

**Yerel kod tabanı ölçümü (21 Ekim 2026, `git ls-files uygulama`, kaynak: depodaki dosyalar):** 234 Python dosyası, 54.382 satır Python, 1.671 `def test_` işlevi, 80 HTML şablonu, 28 migration dosyası. `requirements.txt` yalnızca Django 5.2.17, asgiref, sqlparse, tzdata, psycopg2, whitenoise, Brotli, Pillow, gunicorn (isteğe bağlı redis) içeriyor. Bağımlılık ağacı çok dar; Django REST Framework, Wagtail, Celery yok.

---

## 1. Çok küçük ekip için verimlilik: hazır admin/kimlik/yetki/ORM/migration/güvenlik; editoryal CMS için her çerçevede ne kadar elle yazılmalı?

### Takeaway
Django ve Laravel/Rails "piller dahil" sınıfındadır (ORM + migration + kimlik + admin ya da admin ekosistemi); Go, Express/Fastify ve büyük ölçüde NestJS/ASP.NET Core/Spring Boot'ta editoryal panelin, yetkilendirmenin ve içerik modelinin çoğu elle kurulur. Bursa Hakimiyet zaten panelini Django içinde elle yazdığı için başka bir çerçeveye geçmek bu işin tamamen yeniden yapılması demektir.

### Cited Findings
- Django 6.0 (Aralık 2025) çekirdeğe yerleşik Content Security Policy desteği (`ContentSecurityPolicyMiddleware`, `SECURE_CSP`, nonce için `csp()` bağlam işlemcisi), şablon parçaları (`{% partialdef %}` / `{% partial %}`) ve yerleşik Tasks (arka plan görevleri, `@task` + `.enqueue()`; görevleri dış işçi çalıştırır) çerçevesi ekledi — [Django 6.0 release notes](https://docs.djangoproject.com/en/dev/releases/6.0/)
- Laravel 12 başlangıç kitleri (React, Svelte, Vue, Livewire) yerleşik kimlik doğrulama sistemiyle giriş, kayıt, parola sıfırlama, e-posta doğrulama sunuyor; WorkOS AuthKit varyantı sosyal giriş, passkey ve SSO ekliyor. Breeze ve Jetstream artık güncellenmiyor — [Laravel 12 release notes](https://laravel.com/docs/12.x/releases)
- Laravel'in birinci taraf paket ekosistemi: Horizon (kuyruk), Scout (arama), Sanctum (API token), Socialite, Telescope, Pulse, Reverb (websocket), Nova (ücretli admin paneli), Octane — [Laravel 12 docs footer/packages](https://laravel.com/docs/12.x/releases)
- Wagtail (Django üzerinde CMS) her üç ayda bir özellik sürümü çıkarıyor; LTS işaretli sürümler: 7.4, 7.0, 6.3, 5.2… 7.4 LTS Django 5.2 ve 6.0'ı destekliyor — [Wagtail upgrading/compatibility](https://docs.wagtail.org/en/stable/releases/upgrading.html); takvim: [Wagtail release schedule](https://github.com/wagtail/wagtail/wiki/Release-schedule)
- Haber/yayın kuruluşlarında Wagtail örnekleri: New York Public Radio, Gothamist.com'daki ~150 bin sayfayı headless Wagtail ile yönetiyor ve WNYC/WQXR'yi çok kiracılı Wagtail platformuna taşıyor; ekip zaten Django bildiği için seçmiş — [Wagtail blog: NYPR on Wagtail](https://wagtail.org/blog/nypr-on-wagtail/). YouGov 30+ sitede 40+ dilde 20.000+ makaleyi Wagtail'e taşımayı planladı — [Wagtail blog: YouGov](https://wagtail.org/blog/yougov). Full Fact 2025'te ~10.000 doğrulama içeriğini Django Admin'den Wagtail'e taşıdı (yalnızca konuşma özeti) — [Wagtail Space 2025 talk](https://pretalx.com/wagtail-space-2025/talk/CCJYH7)
- Instagram sunucusu (2019–2020 verisi) "birkaç milyon satırlık Python monoliti", günde yüzlerce commit, birkaç dakikada bir dağıtım; PyCon 2019 konuşması "bir milyon satırlık, bin uç noktalı Django uygulaması" diye tanımlıyor — [Instagram Engineering](https://instagram-engineering.com), [PyCon 2019 talk](https://pycon-archive.python.org/2019/schedule/presentation/372). Güncel (2025–26) birinci elden doğrulama bulunamadı.

### Inferences
- Django + mevcut özel panel: admin, oturum, parola özetleme, CSRF, izin/grup sistemi, migration, form doğrulama, CSP (6.0+) ve arka plan görevi iskeleti (6.0+) çerçeveden geliyor; elle yazılan kısım editoryal iş akışı ve arayüz. Bu proje bu katmanı zaten yazmış (54 bin satır, 1.671 test).
- Laravel ve Rails Django'ya en yakın alternatiflerdir (her ikisi de ORM + migration + kimlik + kuyruk sunar); ancak geçiş, var olan panelin ve testlerin PHP/Ruby'de yeniden yazılması demektir — verimlilik kazancı değil, yatay hareket.
- Go (net/http, Gin/Echo/Fiber), Express/Fastify: ORM, migration, admin, yetki, form doğrulama ayrı kütüphanelerden seçilip birleştirilmeli; tek kişilik ekip için editoryal CMS'te en fazla elle iş bu yığınlardadır. NestJS yapı (modül/DI) sağlar ama admin/CMS sağlamaz. Spring Boot ve ASP.NET Core güçlü güvenlik/kimlik bileşenleri sunar (Spring Security, ASP.NET Identity) ama hazır içerik yönetim paneli yoktur. (Genel bilgi; bu çerçevelerin admin eksikliği için ayrıca kaynak taranmadı.)
- Wagtail, sıfırdan CMS isteyen biri için Django tarafındaki en güçlü hazır seçenek; ancak Bursa Hakimiyet'te panel zaten yazıldığından Wagtail'e geçiş de bir göç projesi olur. Değerlendirilebilecek yer: yeni sayfa türleri değil, yalnızca gelecekte "akış/sayfa düzeni" gibi blok tabanlı editör ihtiyacı doğarsa.

### Gaps
- WordPress'in "uygulama backend'i" (REST API / headless) olarak kullanımına dair 2025–26 kaynaklı karşılaştırma toplanamadı; SO 2025'te WordPress kullanım payı dışında veri yok (bkz. §6).
- Rails 8 "Solid" (Solid Queue/Cache/Cable) ve Kamal dağıtım aracı resmî kaynaktan doğrulanmadı.
- ASP.NET Core / Spring için hazır yönetim paneli ekosistemi (ör. ABP, JHipster) kaynakla incelenmedi.

---

## 2. Başarım: önbellek/CDN'den servis edilen okuma ağırlıklı bir haber sitesinde dil/çerçeve verim farkları önemli mi?

### Takeaway
Ham mikro-benchmark'larda farklar büyük (ASP.NET ≈ 36×, Django ≈ 1,9× Laravel tabanına göre, TechEmpower R23 Fortunes, ORM'li sınıf), ancak bu farklar veritabanı sorgusu eklenince hızla daralıyor ve önbellekten/CDN'den dönen sayfalarda uygulama sunucusuna hiç ulaşılmıyor. Haber sitesi için darboğaz sorgu tasarımı, önbellek isabet oranı ve ön yüz yüküdür; çerçeve verimi ikinci derecede.

### Cited Findings
- TechEmpower Round 23 (yayın: 24 Şubat 2025) Fortunes testi, yalnızca PostgreSQL, ORM'li (Full/Micro ORM, Raw hariç) filtrelenmiş ikincil derleme (istek/saniye): ASP.NET 609.966; Go Fiber 338.096 (türetilmiş değer); Rust Actix 320.144 (ayrı Mart 2025 koşusu); Java Spring 243.639; Express 78.136; Rails 42.546; Django 32.651; Laravel 16.800 (MySQL sonucundan türetilmiş). NestJS, Fastify, Gin/Echo, FastAPI yok; donanım belirtilmemiş — [dev.to: Popular backend frameworks performance benchmark](https://dev.to/tuananhpham/popular-backend-frameworks-performance-benchmark-1bkh). **Uyarı:** birincil TechEmpower sonuç sayfası doğrudan okunamadı; Fiber ve Laravel değerleri yazar tarafından tahmin edilmiş.
- TechEmpower'ın kendi blogu R23'te spring-mongo sorgu testinin ~5,9k'dan ~583 rps'ye düştüğünü, MongoDB mühendisinin bunu yapılandırma hatasına bağladığını ve düzeltmeyle ~14,2k'ya çıktığını yazıyor — sonuçların yapılandırmaya çok duyarlı olduğunun örneği — [TechEmpower blog (tfb etiketi)](https://www.techempower.com/blog/tag/tfb/)
- Bir Python benchmark yazısı: düz JSON'da 37 katlık fark, kimlik doğrulamalı veritabanı sorgusunda 1,8 kata iniyor; verimde kazanan yapılandırmaların p99 gecikmesi 2–3 kat kötü — (ikincil derleme) [pkgpulse: problem with JS framework benchmarks](https://www.pkgpulse.com/guides/problem-with-javascript-framework-benchmarks) ve arama özetindeki kaynaklar; bağımsız doğrulanmadı.
- Bir Rails bakımcısının yorumu: boş istek benchmark'ları yalnızca çerçeve "overhead"ini ölçer, "vakaların ezici çoğunluğunda bu fark önemsizdir" — [codeandmore: A perfect example of pointless benchmarks](https://codeandmore.co.uk/posts/perfect-pointless-benchmarks/)
- Karşı görüş: benchmark'lar yükü kaldıramayacak çerçeveleri elemekte işe yarar, o eşikten sonra seçim başka özelliklere göre yapılmalı — [Elixir Forum: TechEmpower benchmarks](https://elixirforum.com/t/techempower-benchmarks/171?page=2)
- Mevcut kod zaten statik dosyaları özetli adlarla, .gz/.br ve uzun önbellekle WhiteNoise üzerinden veriyor; paylaşımlı önbellek isteğe bağlı Redis — kaynak: depodaki `requirements.txt` yorumları.

### Inferences
- 32.651 rps (Django, Fortunes, tek makine) bir yerel gazetenin zirve trafiğinin çok üstünde; üstelik CDN/sayfa önbelleği isabetinde istek Django'ya hiç gelmez. Yani Django → Go/ASP.NET geçişi bu ölçekte sunucu sayısını belki 1'den 1'e değiştirir; yeniden yazma maliyetini haklı çıkarmaz.
- Asıl başarım işleri: 1 milyon makalelik tabloda indeksler (GIN/trgm), N+1 sorgularının giderilmesi (`select_related`/`prefetch_related`), sayfa/parça önbelleği, CDN önünde `Cache-Control`/stale-while-revalidate, görsel boyutları.
- Mobil API'de de okuma ağırlığı aynı; liste uç noktaları önbelleklenebilir.

### Gaps
- TechEmpower Round 23 birincil tablosu (tfb-status / techempower.com/benchmarks) doğrudan çekilemedi; R24 veya sonrası yayınlanmış mı doğrulanmadı.
- Haber yayıncısı ölçeğinde "darboğaz DB/önbellek" diyen otoriter bir mühendislik blogu (ör. Guardian, BBC, NYT) bu turda bulunamadı; elimizdeki yorumlar çoğunlukla forum/blog düzeyinde.

---

## 3. PostgreSQL desteğinin kalitesi (ORM, tam metin arama, Türkçe yapılandırma, pg_trgm, migration)

### Takeaway
PostgreSQL'in kendisi `turkish` Snowball kök bulucusuyla gelir; bunu ORM düzeyinde en eksiksiz kullanan Django'dur (`SearchVector(config=...)`, `SearchRank`, `SearchHeadline`, `SearchVectorField`, `TrigramSimilarity` ailesi, `TrigramExtension` migration'ı). EF Core/Npgsql de güçlü FTS desteği verir; Laravel yalnızca temel `whereFullText` sunar; Prisma'da PostgreSQL FTS hâlâ "preview" ve indeks kullanamıyor.

### Cited Findings
- PostgreSQL `pg_catalog` içinde `turkish_stem` — "snowball stemmer for turkish language" — PostgreSQL 18 belgelerinde listeleniyor — [PostgreSQL 18 docs: textsearch-psql](https://docs.w3cub.com/postgresql~18/textsearch-psql) (ayna); Türkçe dahil harici Snowball kök bulucuları 2015'te 9.6 için varsayılan yapılandırma olarak önerildi ve "resmî olmayan, test edilmeli" notu düşüldü — [pgsql-hackers: new full text search configurations](https://www.postgresql.org/message-id/CAF4Au4x6X_wSXFwsQYE8q5o0aQZANrvYjZJ8uOnsiHDnOVPPEg%40mail.gmail.com)
- Türkçe uyarısı: `unaccent` ile Türkçe harfleri (ç, ğ, ı, ö, ş, ü) `turkish_stem` öncesi düzleştirmek sonuçları bozuyor, çünkü bu harfler dil için anlam taşıyor — [PostgreSQL mailing list](https://www.postgresql.org/message-id/CAE2gYzzdqjeCpPk-BU1AWkFsn1yZocBWpAYd1WLA-EFy13Ozgg%40mail.gmail.com)
- Django `django.contrib.postgres.search`: `SearchVector(config=...)`, `SearchQuery(search_type='plain'|'phrase'|'raw'|'websearch')`, `SearchRank` (ağırlık A–D, `cover_density`), `SearchHeadline`, `config` parametresi `F()` ifadesi olabilir; `SearchVectorField` + trigger ile önceden hesaplanmış vektör; fonksiyonel GIN/GiST indeksi; `TrigramExtension` migration işlemi ve `TrigramSimilarity`, `TrigramWordSimilarity`, `TrigramStrictWordSimilarity`, `TrigramDistance` vb. — [Django 5.2 docs: Full text search](https://docs.djangoproject.com/en/5.2/ref/contrib/postgres/search/)
- EF Core + Npgsql: `tsvector`→`NpgsqlTsVector`, `HasGeneratedTsVectorColumn()` ile üretilmiş sütun + GIN/GiST, `EF.Functions.ToTsVector`, `ToTsQuery`, `PlainToTsQuery`, `Matches`, `Rank`, `SetWeight`, `Unaccent` LINQ'te mevcut; sayfada pg_trgm geçmiyor — [Npgsql EF Core: Full-text search](https://www.npgsql.org/efcore/mapping/full-text-search.html)
- Laravel: "Full text where clauses are currently supported by MariaDB, MySQL, and PostgreSQL"; `whereFullText` / `orWhereFullText` tam metin indeksli sütunlarda — [Laravel 12 Query Builder](https://laravel.com/docs/12.x/queries)
- Prisma: PostgreSQL FTS `fullTextSearchPostgres` preview bayrağı arkasında (v7 belgeleri), MySQL'de GA; "Prisma Client şu an tam metin aramayı hızlandırmak için indeks kullanmayı desteklemiyor", ham SQL/TypedSQL öneriliyor — [Prisma docs: Full-text search](https://www.prisma.io/docs/orm/prisma-client/queries/full-text-search), [prisma/prisma#10386](https://github.com/prisma/prisma/issues/10386)
- Prisma'nın kendi blogu da "Elasticsearch'e gerek yok, Postgres'te FTS var" diyor — [Prisma blog](https://www.prisma.io/blog/you-dont-need-elasticsearch-postgres-already-has-full-text-search)

### Inferences
- 1 milyon makalede Django'nun `SearchVectorField` + GIN + `config='turkish'` (ya da özel bir Türkçe yapılandırma) + başlıkta `pg_trgm` kombinasyonu ORM'den çıkmadan kurulabilir; mevcut kod bunu zaten kullanıyor (proje bağlamı). Node tarafında (Prisma) aynı şey ham SQL'e düşer.
- Rails için `pg_search` gem'i, Go için `pgx` + `sqlc` ile ham SQL yaygın yollardır (genel bilgi, bu turda kaynakla doğrulanmadı).
- Hibernate (Spring) çekirdeğinde PostgreSQL FTS soyutlaması yoktur; Hibernate Search Lucene/Elasticsearch'e yönelir (genel bilgi, doğrulanmadı).

### Gaps
- Rails `pg_search`, Spring/Hibernate, Go `sqlc`/GORM, Drizzle için FTS/trgm belgeleri bu turda çekilemedi.
- `turkish_stem` kalitesine (ı/i, ekler) dair nicel bir değerlendirme bulunamadı.

---

## 4. Mobil uygulama API'si: REST vs GraphQL, OpenAPI üretimi, push bildirim kütüphaneleri

### Takeaway
Django tarafında iki olgun REST yolu var: Django REST Framework (en yaygın paket, kullanımı düşüyor) ve Pydantic tabanlı, OpenAPI'yi otomatik üreten Django Ninja (yükselişte, ~%10). Push için Firebase Admin SDK resmî olarak Node.js, Java, Python, Go, C# (ve deneysel Dart) destekliyor — PHP ve Ruby resmî listede yok. Mobil API için çerçeve değiştirmek gerekmiyor.

### Cited Findings
- State of Django 2025 (DSF + JetBrains PyCharm, ~4.600 katılımcı): DRF en popüler üçüncü taraf paket — [JetBrains: The State of Django 2025](https://blog.jetbrains.com/pycharm/2025/10/the-state-of-django-2025/); django-ninja %10 ile en çok kullanılan paketler arasında — [Django weblog: Five ways to discover Django packages (Kasım 2025)](https://www.djangoproject.com/weblog/2025/nov/02/five-ways-to-discover-django-packages/)
- Topluluk özeti (resmî değil): DRF kullanımı 2022'de %60 → 2025'te %49; Django'yu REST API için kullananlar 2023'te %61 → 2025'te %51 — [Django Forum: State of Django 2025](https://forum.djangoproject.com/t/state-of-django-2025/43279)
- Django Ninja: başarımı Pydantic ve async desteğinden geliyor; tanımlanan her işlem için OpenAPI şeması ve `/api/docs` etkileşimli belge üretiyor — [PyPI: django-ninja](https://pypi.org/project/django-ninja/1.0b2); dağıtım paketlerinde 1.4.3 (Ağustos 2025) ve 1.5.1 (Aralık 2025 staging) görülüyor — [Arch Linux: python-django-ninja](https://archlinux.org/packages/extra-staging/any/python-django-ninja)
- Firebase Admin SDK (FCM dahil) desteklenen sunucu dilleri: Node.js, Java, Python, Go, C#, Dart (deneysel) — [Firebase: Add the Admin SDK](https://firebase.google.com/docs/admin/setup)

### Inferences
- Bursa Hakimiyet için en düşük maliyetli yol: mevcut Django modelleri üzerine Django Ninja (ya da DRF) ile salt-okuma ağırlıklı, sürümlenmiş (`/api/v1/`) REST; OpenAPI şemasından Swift/Kotlin istemci üretimi. GraphQL (Strawberry/Graphene) bir haber uygulamasının sabit ekranları için ek karmaşıklık getirir; gerekmedikçe önerilmez.
- Push: `firebase-admin` Python paketi + Django 6.0 Tasks (ya da mevcut zamanlanmış görev düzeni) ile FCM; iOS da FCM üzerinden APNs'e gider.
- Node/NestJS (Swagger modülü), ASP.NET Core (yerleşik OpenAPI), Spring (springdoc) de OpenAPI üretir; bu kriter Django'dan ayrılmayı gerektirmiyor.

### Gaps
- Django Ninja'nın resmî sürüm notları/sürüm tarihleri GitHub'dan doğrulanmadı.
- State of Django 2025'in DRF yüzdesi birincil rapordan doğrulanamadı (49% ikincil).

---

## 5. Uzun dönem destek ve sürüm takvimi (2026 itibarıyla)

### Takeaway
Tüm adaylar öngörülebilir takvimlere sahip. Django 5.2 LTS Nisan 2028'e kadar güvenlik desteği alıyor, sıradaki LTS 6.2 (Nisan 2027 → Nisan 2030); 2028'den itibaren Django yıllık YYYY sürümlemeye ve her sürüme 3 yıl desteğe geçiyor. En kısa pencereler Rails (1 yıl hata + 2 yıl güvenlik) ve Laravel (18 ay + 2 yıl); en uzunları .NET LTS (3 yıl) ve Spring Boot ticari destek.

### Cited Findings
- **Django:** 5.2 LTS — ana destek 3 Aralık 2025'te bitti, genişletilmiş (güvenlik) destek Nisan 2028; 6.0 — ana destek 4 Ağustos 2026, genişletilmiş Nisan 2027; 6.1 — Nisan 2027 / Aralık 2027; **6.2 LTS** — çıkış Nisan 2027, genişletilmiş destek Nisan 2030; 6.2 eski sürümleme düzenindeki son sürüm; 2028'den itibaren her Ocak'ta YYYY numaralı sürüm (2028, 2029…) ve her birine "aynı üç yıllık destek süresi" (LTS etiketi yok) — [djangoproject.com/download](https://www.djangoproject.com/download/)
- **Node.js:** 22.x (Jod) Maintenance LTS, EOL 2027-04-30; 24.x (Krypton) Active LTS, maintenance 2026-10-20, EOL 2028-04-30; 26.x Current, LTS 2026-10-28, EOL 2029-04-30; 20.x EOL 2026-04-30 — [nodejs/Release](https://github.com/nodejs/Release). Node 27'den itibaren yıllık takvim (6 ay alpha + 6 ay Current, sonra LTS; LTS toplam ~30 ay kritik düzeltme) — [nodejs.org: previous releases](https://nodejs.org/en/about/previous-releases). **Not:** nodejs.org sayfasının otomatik özeti EOL'ları yanlış sütundan okudu; tarihler için nodejs/Release tablosu esas alındı.
- **.NET:** .NET 10 LTS (11 Kasım 2025 → 14 Kasım 2028); .NET 9 STS ve .NET 8 LTS ikisi de 10 Kasım 2026'da bitiyor; .NET 11 RC2 13 Ekim 2026. LTS 3 yıl, STS 2 yıl; son 6 ay yalnızca güvenlik — [.NET support policy](https://dotnet.microsoft.com/en-us/platform/support/policy/dotnet-core)
- **Spring Boot:** 4.1 (30 Haz 2026; OSS 31 Tem 2027, ticari 31 Tem 2028); 4.0 (30 Kas 2025; OSS 31 Ara 2026); 3.5 (OSS 30 Haz 2026 bitti, ticari 30 Haz 2032) — [endoflife.date/spring-boot](https://endoflife.date/spring-boot)
- **Laravel:** her yıl (~Q1) ana sürüm; 18 ay hata + 2 yıl güvenlik düzeltmesi. 12: 24 Şub 2025 → hata 13 Ağu 2026, güvenlik 24 Şub 2027; 13: Q1 2026 → hata Q3 2027, güvenlik Q1 2028, PHP 8.3–8.5 — [Laravel 12 release notes](https://laravel.com/docs/12.x/releases); Laravel 13 asgari PHP 8.3 — [Laravel News: Laravel 13 released](https://laravel-news.com/laravel-13-released); 17 Mart 2026 çıkış tarihi yalnızca bir ajans blogunda — [Bacancy](https://www.bacancytechnology.com/blog/laravel-13) (doğrulanmadı)
- **Rails:** 8.1 (22 Eki 2025; hata 10 Eki 2026, güvenlik 10 Eki 2027; son yama 8.1.4, 24 Eyl 2026); 8.0 (güvenlik 7 Kas 2026'ya kadar); politika: her minör sürüme 1 yıl hata + 2 yıl güvenlik — [endoflife.date/rails](https://endoflife.date/rails)
- **Wagtail:** üç ayda bir özellik sürümü; güncel LTS 7.4 (Django 5.2/6.0) — [Wagtail docs](https://docs.wagtail.org/en/stable/releases/upgrading.html)

### Inferences
- Bursa Hakimiyet'in Django 5.2.17'de olması Nisan 2028'e kadar güvenlik açısından yeterli; doğal yükseltme hedefi Django 6.2 LTS (Nisan 2027 sonrası, destek Nisan 2030). Bu, çerçeve değiştirmeden ~3,5 yıllık destek görünürlüğü veriyor.
- Rails ve Laravel'in kısa pencereleri tek kişilik ekipte yıllık zorunlu yükseltme yükü yaratır; Django LTS-to-LTS ritmi (2–3 yılda bir) daha az iş.
- Python 3.12 desteği: Python'un kendi EOL'u (Ekim 2028) bu turda doğrulanmadı — bkz. Gaps.

### Gaps
- Go (her sürüm son iki ana sürüm desteklenir), Python 3.12 EOL ve PHP 8.x güvenlik takvimleri resmî sayfalardan çekilmedi.
- Wagtail LTS bitiş tarihleri release-schedule wiki'sinden okunmadı.

---

## 6. Geliştirici piyasası ve popülerlik (Türkiye ve küresel)

### Takeaway
Küresel olarak Node.js/JavaScript ve ASP.NET Core en geniş havuzlar; Django (%12,6) ve Laravel (%8,9) orta, Rails (%5,9) daha küçük. Python dil olarak %57,9 ile ikinci. Türkiye'ye özgü, teknoloji kırılımı veren güvenilir bir anket/ilan istatistiği bulunamadı; dolaylı göstergeler Türkiye'de Java ve C#'ın kurumsal (bankacılık, e-ticaret) ilanlarda güçlü olduğunu söylüyor ama nicel değil.

### Cited Findings
- Stack Overflow Developer Survey 2025, web çerçeveleri (tüm katılımcılar / profesyoneller): Node.js 48,7 / 49,1; React 44,7 / 46,9; Next.js 20,8 / 21,5; Express 19,9 / 20,3; ASP.NET Core 19,7 / 21,3; FastAPI 14,8 / 15,1; Spring Boot 14,7 / 15,6; Flask 14,4 / 13,2; ASP.NET 14,2 / 15,0; WordPress 13,6 / 12,4; **Django 12,6 / 11,7**; Laravel 8,9 / 9,3; NestJS 6,7 / 7,4; Ruby on Rails 5,9 / 6,2; Fastify 2,9 / 3,1; Gin listede yok. Web çerçevesi sorusuna 23.678 kişi yanıt verdi — [Stack Overflow Survey 2025: Technology](https://survey.stackoverflow.co/2025/technology)
- Aynı anket, diller: JavaScript %66, Python %57,9, TypeScript %43,6, Java %29,4, C# %27,8, PHP %18,9, Go %16,4, Kotlin %10,8, Ruby %6,4; veritabanı: PostgreSQL %55,6 (profesyonellerde %58,2) — [Stack Overflow Survey 2025: Technology](https://survey.stackoverflow.co/2025/technology)
- GitHub Octoverse 2025 (28 Ekim 2025): TypeScript Ağustos 2025'te Python ve JavaScript'i geçip GitHub'da aylık katkıcı sayısıyla 1 numara oldu (2.636.006 katkıcı, yıllık ~%66,6 artış); Python yapay zekâ/veri işlerinde lider kalıyor — [GitHub blog: Octoverse 2025](https://github.blog/news-insights/octoverse/octoverse-a-new-developer-joins-github-every-second-as-ai-leads-typescript-to-1/), [InfoWorld](https://www.infoworld.com/article/4080454/typescript-rises-to-the-top-on-github.html)
- Türkiye: Önceki Yazılımcı 2025 maaş anketi 9.056 katılımcı; %55,3 İstanbul, %16,7 Ankara, %7,1 İzmir; Full Stack ortalama maaş junior 50.500 TL, mid 73.500 TL, senior 122.500 TL (teknoloji kırılımı arama sonuçlarında yok) — [tamindir: Yazılımcı maaşları 2025](https://www.tamindir.com/haber/yazilimci-maaslari-2025_94742/), [ShiftDelete](https://shiftdelete.net/turkiye-2025-yili-yazilimci-maaslari-ortaya-cikti)
- Türkiye (zayıf kanıt): bir eğitim kurumu makalesi Türkiye'de ilanların %18'inin C# istediğini ve Java'nın bankacılık/e-ticaret/kurumsalda güçlü olduğunu söylüyor; kaynak belirtilmemiş — [GoIT: programlama dillerinin manzarası](https://goit.global/tr/articles/programlama-dillerinin-manzarasi-ve-en-populer-dille/), [GoIT: 2025 yazılımcı maaşları](https://goit.global/tr/articles/2025-yazilimci-maaslari-turkiye-de-sektorel-analiz-ve-kariyer-rehberi/)
- Örnek ilan (tekil): bir Diyarbakır backend ilanı Node.js, Go veya Python'dan biriyle 2+ yıl ve PostgreSQL/MongoDB istiyor — [Techcareer.net ilanı](https://www.techcareer.net/jobs/detail/yazlm-gelistirme-backend-developer-4169014)

### Inferences
- Bir kişi + ajan modelinde işe alım ikincil bir risk, ama ileride bir geliştirici eklenirse: Python geliştirici havuzu küresel olarak çok geniş (dil olarak %57,9); "Django bilen" havuzu daha dar ama Python bilen biri için öğrenme eğrisi kısa. Türkiye kurumsal piyasasında C#/Java ağırlığı muhtemel, ancak bu bir yerel gazetenin yeniden yazımını haklı çıkaracak nicel kanıta dayanmıyor.

### Gaps
- Kariyer.net / LinkedIn Türkiye'de "Django", "Laravel", ".NET", "Spring", "Node.js" ilan sayıları bulunamadı (site taraması kısıt gereği yapılmadı).
- Stack Overflow 2025 Türkiye ülke filtresi verisi ve "admired/desired" oranları çekilemedi.
- JetBrains State of Developer Ecosystem 2025 genel (Türkiye) verisi incelenmedi.

---

## 7. Yapay zekâ ajanı destekli geliştirmeye uygunluk

### Takeaway
Güvenilir, nicel bir "hangi çerçeve ajanla daha iyi yazılır" çalışması bulunamadı. Tek güçlü veri noktası GitHub Octoverse 2025: TypeScript'in 1 numaraya çıkışını GitHub, statik tiplerin ajan üretimi kodu güvenilir kılmasına ve çerçevelerin varsayılan olarak TS iskelet kurmasına bağlıyor. Python ise eğitim verisi/popülerlik açısından en üst iki dilde.

### Cited Findings
- GitHub, Octoverse 2025'te statik tiplemenin ajanla üretilen koda yardımcı olduğunu ve büyük çerçevelerin artık TypeScript iskeletini varsayılan kurduğunu, bunun TS büyümesini sürüklediğini savunuyor — [GitHub blog: Octoverse 2025](https://github.blog/news-insights/octoverse/octoverse-a-new-developer-joins-github-every-second-as-ai-leads-typescript-to-1/), [Visual Studio Magazine](https://visualstudiomagazine.com/articles/2025/10/31/typescript-tops-github-octoverse-as-ai-era-reshapes-language-choices.aspx)
- Yeni geliştiricilerin ~%80'i ilk haftalarında Copilot kullanmış — [GitHub blog: Octoverse 2025](https://github.blog/news-insights/octoverse/octoverse-a-new-developer-joins-github-every-second-as-ai-leads-typescript-to-1/)
- Laravel kendini "Artisans and agents" için çerçeve olarak pazarlıyor (pazarlama, kanıt değil) — [laravel.com](https://laravel.com/docs/12.x/releases)

### Inferences
- Bu projede ajan verimliliğinin asıl kaldıracı dil değil, test kapsamı: 1.671 test ajanların değişikliklerini doğrulayan güvenlik ağı. Başka yığına geçişte bu ağ sıfırlanır.
- Python'da tip güvencesi eksikliği, Django Ninja/Pydantic şemaları ve tip ipuçları + mypy/pyright ile kısmen kapatılabilir (genel bilgi).

### Gaps
- Dil/çerçeveye göre LLM kod üretim doğruluğunu ölçen bağımsız, güncel bir benchmark (ör. web çerçevesi bazında) bulunamadı.

---

## 8. Barındırma/işletme maliyeti ve bakım yükü (bellek, dağıtım sadeliği)

### Takeaway
Bu turda çerçeveler arası bellek/maliyet karşılaştırması için güvenilir birincil kaynak bulunamadı. Mevcut Django kurulumu (gunicorn + WhiteNoise + PostgreSQL + isteğe bağlı Redis) zaten tek sunucuda çalışabilecek, az bağımlılıklı bir yığın.

### Cited Findings
- Mevcut yığın: gunicorn (yalnız Linux), WhiteNoise ile özetli/sıkıştırılmış statik teslim, isteğe bağlı Redis, Pillow ile görsel türevleri; toplam 8–9 doğrudan bağımlılık — kaynak: depodaki `requirements.txt`
- Laravel kendi barındırma/izleme ürünlerini sunuyor (Cloud, Forge, Vapor, Nightwatch) — [laravel.com](https://laravel.com/docs/12.x/releases)
- .NET ve Spring Boot'ta destek pencereleri bitince (ör. .NET 8 ve 9 aynı gün, 10 Kasım 2026) zorunlu ana sürüm yükseltmesi gerekiyor — [.NET support policy](https://dotnet.microsoft.com/en-us/platform/support/policy/dotnet-core)

### Inferences
- Go ve ASP.NET Core tek ikili/tek süreç dağıtımı ve daha düşük istek başına bellek sunar (genel bilgi); ancak bu ölçekte sunucu maliyeti farkı aylık birkaç VPS kademesi düzeyinde kalır, bir yeniden yazımın insan maliyetinin yanında küçüktür.
- Bakım yükünü belirleyen asıl etken bağımlılık sayısı ve yükseltme sıklığı: mevcut Django kurulumu çok dar bağımlılıklı ve LTS ritminde.

### Gaps
- Django/gunicorn işçisi, Node, Go, .NET, JVM (Spring Boot) için karşılaştırmalı bellek ayak izi ölçümü bulunamadı; gerekirse aynı uç nokta için yerel ölçüm önerilir.

---

## 9. Mevcut Django kod tabanını başka yığına taşımanın gerçek maliyeti (~1.650 test, özel panel, 1M makalede URL uyumu) ve medyada göç vakaları

### Takeaway
Göçün maliyeti kod satırıyla sınırlı değil: 54 bin satır Python, 1.671 test, 80 şablon ve 28 migration yeniden yazılır; buna ek olarak 1 milyon makalenin URL'leri korunmalı ya da en az bir yıl 301 ile yönlendirilmeli. Medya göçlerinde belgelenen asıl kayıp çerçeveden değil, URL/yönlendirme ve meta veri hatalarından geliyor. Başarısız bir "büyük yeniden yazım" haber odası post-mortem'i bulunamadı.

### Cited Findings
- Yerel ölçüm: `uygulama/` altında 234 Python dosyası, 54.382 satır, 1.671 test işlevi, 80 şablon, 28 migration — kaynak: depo (`git ls-files uygulama`), 21 Ekim 2026
- Google: URL değişen site taşımalarında sunucu tarafı kalıcı yönlendirme (301/308), her eski URL doğrudan son hedefe, zincir ideal ≤3; yönlendirmeleri **en az bir yıl**, mümkünse süresiz tut; çok sayıda eski URL'yi ana sayfaya yönlendirme; orta ölçekli sitelerde yeni URL'lerin eskilerin yerini alması "birkaç hafta veya daha fazla", büyük sitelerde daha uzun; 301'ler PageRank kaybettirmez; büyük siteler bölüm bölüm taşınabilir — [Google Search Central: Site move with URL changes](https://developers.google.com/search/docs/crawling-indexing/site-move-with-url-changes)
- Reuters platform değişikliği (danışmanlık anlatımı): 24 aydan eski makaleleri yeni CMS'ten çıkarmanın organik trafiğin %22'sini (çeyrekte 6,8 milyon oturum) kaybettirebileceği modellendi — arama özetinden; ikincil/danışman kaynağı, [Newsifier: migrations without SEO traffic loss](https://www.newsifier.com/blog/development/how-newsifier-handles-website-migrations-without-seo-traffic-loss) ve ilgili arama sonuçları (doğrulanmadı)
- Satıcı iddiaları (kanıtsız): SEO önceliklendirilmeyen platform göçlerinde %30–60 organik trafik düşüşü; başka biri 90 günde %30–50 diyor — [FocusReactive: Headless CMS migration](https://focusreactive.com/blog/cms-migration/), [Newsifier](https://newsifier.com/blog/how-newsifier-handles-website-migrations-without-seo-traffic-loss) — **güvenilmez, çalışma atfı yok**
- Django ekosistemi içi göç örnekleri: NYPR (Gothamist ~150 bin sayfa → Wagtail; ekip Django bildiği için), Full Fact (Django Admin → Wagtail, ~10 bin içerik, 2025) — [Wagtail blog: NYPR](https://wagtail.org/blog/nypr-on-wagtail/), [Wagtail Space 2025](https://pretalx.com/wagtail-space-2025/talk/CCJYH7)

### Inferences
- Yığın değişikliği aynı veritabanını (PostgreSQL) koruyabilir, ama Django migration geçmişi, model kısıtları, tetikleyiciler (`SearchVectorField`), kimlik/parola özetleri (Django PBKDF2 biçimi) ve oturumlar yeni çerçeveye uyarlanmalı; parola özetleri için uyumluluk katmanı gerekir.
- URL uyumu teknik olarak her çerçevede yapılabilir, ancak mevcut Django URL çözümleyici ve testleri bu sözleşmeyi zaten kodlamış durumda; yeniden yazımda bu sözleşmenin 1.671 testlik karşılığı da yeniden yazılmalı.
- Kaba tahmin (kaynaksız): tek kişi + ajanlarla 54 bin satırlık uygulamanın eşdeğer test kapsamıyla yeniden yazımı aylar sürer ve canlıya geçişi (F8) erteler; kazanç (ham verim, tip sistemi) bu projenin ölçeğinde bu maliyeti karşılamaz. En rasyonel yol: Django 5.2 LTS'te kal, mobil API'yi aynı projeye Django Ninja/DRF ile ekle, 2027'de 6.2 LTS'ye yükselt.

### Gaps
- Bir haber kuruluşunun çerçeve değiştirdiği (ör. Django → Node, Rails → Go) ve sonucunu sayılarla paylaştığı birincil mühendislik yazısı bu turda bulunamadı.
- Reuters vakasının birincil kaynağı açılmadı; rakam danışman anlatımına dayanıyor.
