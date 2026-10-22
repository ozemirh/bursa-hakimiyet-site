# Önbellek ve CDN planı

21 Ekim 2026 · sahibi `devops-altyapi-muhendisi` · durum: **PLAN**.

Bu belge için hiçbir hesap açılmadı. DNS'e, canlı siteye ve sunucuya dokunulmadı,
kod değiştirilmedi, commit atılmadı. Belge `KURULUM.md`'nin §1, §7a, §9 ve §10
bölümlerini tamamlıyor. Çelişen yerler §2'de "B" kodlu bulgu olarak yazıldı.

**Kaynak gösterimi.** `[K#]` işareti §14'teki kaynak listesine gider. Listede URL,
sayfanın kendi güncelleme tarihi ve okunduğu gün (21 Ekim 2026) var. Belgedeki
etiketlerin anlamı şöyle:

- **Ölçüldü:** Bu belge yazılırken bu makineden yapıldı; komut yanında yazılı.
- **Okundu:** Depodaki dosyadan, satır numarasıyla.
- **Doğrulanmadı:** Kaynak bulunamadı ya da ölçülemedi. Bunlar §13'te toplu duruyor.

---

## 0. Yönetici özeti

Bir haber sitesinin en kötü günü, en çok okunduğu gündür: deprem, seçim, derbi
gecesi. Bugünkü kurulum tasarısında her okurun her isteği tek sunucuya gidiyor.
Böyle bir gecede o sunucunun hem işlemcisi hem de internet bağlantısı tıkanır.
Saniyede 400 sayfa açılırsa görsellerle birlikte yaklaşık 1 Gbit/s trafik
oluşur; bu, tipik bir sanal sunucunun bağlantı sınırıdır (§7).

**CDN** (içerik dağıtım ağı) bu sorunu çözer. CDN, sayfaların kopyasını okura
yakın sunuculardan veren bir hizmettir. Trafiğin %90–97'sini bizim sunucumuza
hiç uğratmadan karşılar.

**Ölçülen iki sürpriz var:**

1. **Gazetenin alan adı zaten Cloudflare'de.** Ad sunucuları Cloudflare'in.
   Eski site görselleri Cloudflare önbelleğinden veriyor, ama sayfaların
   kendisini (HTML) önbelleğe almıyor. `KURULUM.md`'deki "DNS'i Cloudflare'e
   taşımak gerekir" varsayımı bu yüzden geçersiz. Hesabın kimde olduğu ise
   bilinmiyor.
2. **Türkiye'den gelen okur Avrupa'dan karşılanıyor.** Bu makineden yapılan
   istekler gazetenin alan adında Amsterdam ve Londra'ya gitti. Aynı anda
   Cloudflare'in kendi sitesi İstanbul'dan geldi. Bağlantı kurulumu 160 ms'ye
   karşı 47 ms sürdü. Cloudflare, hangi veri merkezinin hangi müşteriye hizmet
   verdiğinin müşteriden müşteriye değiştiğini kendisi yazıyor [K18].

**Öneri: Cloudflare'de kalmak, Pro plan (ayda 20–25 $).** Gerekçeler:

- DNS taşınmaz.
- Kesim günü geri dönüş süresi 10 dakikadan 1 dakikaya iner (§9).
- Etiketle temizleme ücretsiz planda da var [K1].

Pro'nun gerekçesi temizleme hızı: Pro'da saniyede 5 istek, ücretsiz planda
dakikada 5 istek [K1]. Ama önce iki şey öğrenilmeli: hesap kimin, ve Pro planda
İstanbul'dan hizmet alınıyor mu (§3.4).

Alternatifler:

| Sağlayıcı | Türkiye'de sunucu | Aylık maliyet |
|---|---|---|
| Bunny | İstanbul | Trafiğe göre ~3–360 $ |
| Medianova (Türk) | İstanbul ve Ankara | Fiyat teklifle |
| Amazon CloudFront | İstanbul | En az 200 $ |
| Fastly | Yok | 20 milyon görüntülemede ~1.000 $ |

**Para ve izin gerektirmeyen kod işleri (P0):**

1. Sayfalar bugün hiçbir önbellek talimatı göndermiyor (ölçüldü). Her sayfa
   türüne ne kadar saklanacağı yazılmalı.
2. Okunma sayacı sayfa isteğinin içinde. CDN açılınca sayaç durur ve "en çok
   okunanlar" boşalır. Sayaç ayrı bir küçük isteğe taşınmalı.
3. Panelde "kaydet"e basılınca yalnız o haberle ilgili sayfalar CDN'den
   silinmeli. Hedef: son dakika haberi 10 saniye içinde anasayfada.

Kod işi 6–9 gün sürer. Aylık bedel 0–25 $. Kullanıcının vermesi gereken
kararlar §11'de.

---

## 1. Terimler

| Terim | Anlamı |
|---|---|
| **Kaynak sunucu (origin)** | Sayfayı üreten kendi sunucumuz: nginx + gunicorn + Django + PostgreSQL. |
| **Uç sunucu, PoP** | CDN'in okura yakın veri merkezi. Örneğin IST İstanbul'dur, AMS Amsterdam'dır. |
| **Önbellek isabeti (HIT) / ıskası (MISS)** | İstek kopyadan karşılandıysa isabet, kaynağa gitmek zorunda kaldıysa ıska. **İsabet oranı** isabetlerin tüm isteklere oranıdır. |
| **TTL** | Bir kopyanın "taze" sayıldığı süre (saniye). |
| **`Cache-Control`** | Sunucunun yanıta eklediği önbellek talimatı. `max-age` tarayıcı ve önbellekler için süredir. `private` "yalnız bu okurun tarayıcısı saklasın", `no-store` "kimse saklamasın" demektir. |
| **`s-maxage`** | Yalnız ortak önbelleklere (CDN) süre verir. Cloudflare'de bayat kopya özelliklerini kapatır, bu yüzden bu planda **kullanılmaz** [K4][K5]. |
| **`CDN-Cache-Control`** | Yalnız CDN'e talimat veren standart başlık (RFC 9213 [K38]). Tarayıcı bunu görmezden gelir. Böylece CDN'e uzun, tarayıcıya kısa süre verilebilir [K6]. |
| **stale-while-revalidate (SWR)** | Süresi dolan kopya, yenisi arka planda hazırlanırken okura verilmeye devam eder (RFC 5861 [K39]). Okur beklemez. |
| **stale-if-error (SIE)** | Kaynak sunucu hata verirse ya da çökerse bayat kopya verilir. Site düşmüş görünmez. |
| **Temizleme (purge)** | Kopyayı CDN'den silmek. Bir sonraki istek kaynağa gider. |
| **Geçersizleştirme (invalidate, soft purge)** | Kopyayı silmeden bayat işaretlemek. Yenisi hazırlanırken eskisi verilebilir [K3]. |
| **Etiket (cache tag, surrogate key)** | Yanıta iliştirilen ad, örneğin `h-1691702`. Tek komutla o etiketi taşıyan bütün kopyalar temizlenir [K2]. |
| **Kademeli önbellek (tiered cache, origin shield)** | Uç sunucular kaynağa doğrudan değil, bir üst katman üzerinden gider. Kaynağa giden istek sayısı düşer [K9]. |
| **`Vary`** | "Bu yanıt şu istek başlığına göre değişir" bildirimi. `Vary: Cookie` her okurun ayrı kopya alması demektir ve önbelleği işe yaramaz kılar. |
| **WAF / challenge / CAPTCHA** | Güvenlik duvarı kuralları. Challenge şüpheli ziyaretçiye "insan mısın" sınaması gösterir. CAPTCHA bunun etkileşimli biçimidir. |

---

## 2. Bugünkü durum: ne var, ne eksik

### 2.1 Var olan katmanlar

| Katman | Durum | Kanıt |
|---|---|---|
| Uygulama sayfa önbelleği | Anonim okur HTML'ini 30 sn saklıyor. Kayıtta tamamı geçersizleşiyor. Okunma sayımı bu katmanda. 7 görünümde açık: anasayfa, kategori, haber, köşe listesi, konular, konu, düzeltmeler. | Okundu: `icerik/sayfa_onbellegi.py`, `settings.py:445-449`. `X-Onbellek: kayit → isabet` ölçüldü. Anasayfa isabette 7 ms, haber detayı ıskada 205 ms, isabette 9 ms (geliştirme sunucusu, yerel PG). |
| Veri önbelleği | Menü, sayım ve sitemap özetleri. Yığılma kilidi var, bayat değer veriliyor. | Okundu: `icerik/onbellek.py:61-112`. |
| Paylaşılan önbellek arka ucu | Redis yolu hazır (`BH_REDIS`). Yoksa dosya önbelleği. | Okundu: `settings.py:424-441`. |
| Statik dosyalar | Özetli adlı dosyalar 1 yıl `immutable`, özetsizler 1 saat. `.gz`/`.br` hazır üretiliyor. | Okundu: `settings.py:254-263`, `nginx/bursahakimiyet.conf:128-143`. |
| Görsel türevleri | Diskte varsa nginx veriyor, yoksa Django üretiyor ve 1 yıl `immutable` gönderiyor. | Okundu: `nginx/bursahakimiyet.conf:173-188`, `gorsel_turev.py:117`. |
| Arşiv görselleri | nginx'ten, 30 gün. | Okundu: `nginx/bursahakimiyet.conf:157-162`. |
| Site haritası | Dosyadan, 300 sn. | Okundu: `nginx/...conf:147-154`, `ara_katman.py:96-97`. |
| nginx HTML mikro önbelleği | Tasarlandı, **kapalı** (okunma sayımı yüzünden). | Okundu: `nginx/...conf:226,233,239`, `KURULUM.md` §7a. |
| Gerçek IP ve hız sınırı | Cloudflare aralıkları `real_ip` ile tanımlı. `/ara` için saniyede 2, `/panel/giris` için dakikada 10 istek sınırı. | Okundu: `snippets/bh-cloudflare-ip.conf`, `nginx/...conf:48-50`. |
| Çerez temizliği | Okur sayfaları çerez bırakmıyor. Okur şablonlarında `csrf_token` yok. | Ölçüldü: 10 okur adresinde `Set-Cookie` yok. Okundu: `grep csrf_token sablonlar` (panel dışında boş). |

### 2.2 Bulgular

| # | Önc. | Bulgu | Kanıt | Emek |
|---|---|---|---|---|
| B1 | **P0** | **Okur HTML'inde `Cache-Control` yok, hepsi `Vary: Cookie` taşıyor.** CDN neyi ne kadar saklayacağını bilemez. Cloudflare HTML'i zaten varsayılan olarak saklamaz [K7]. | Ölçüldü (`curl -D -` ile `/`, `/bursa`, `/ara?q=bursa`, `/daha-fazla?...`, `/rss`, `/static/sitemap/googleNews.xml`, `/kose-yazilari`, `/nobetci-eczane`, `/piyasa/dolar`, `/robots.txt`): `Cache-Control` yok; her yanıtta, isabette de `Vary: Cookie, Accept-Encoding`. `Vary: Cookie` oturuma dokunan ara katmanlardan geliyor (`settings.py:101,131,529`). | 1,5 gün (§4) |
| B2 | **P0** | **Okunma sayımı HTML isteğinde.** CDN'den dönen istek Django'ya ulaşmaz. Sayaç durur, "en çok okunanlar" sessizce eski davranışına düşer. | Okundu: `sayfa_onbellegi.py:25-29, 100, 109, 118`. `KURULUM.md` §7a aynı engeli nginx için yazmış. | 1,5 gün (§6.3) |
| B3 | **P0** | **Alan adı zaten Cloudflare'de, `KURULUM.md` bunu bilmiyor.** Hesabın kimde olduğu bilinmiyor. Kesim ve geri dönüş planı değişir (§9). | Ölçüldü: `nslookup -type=NS` sonucu `molly/stan.ns.cloudflare.com`. Canlı anasayfa `cf-cache-status: DYNAMIC` + `x-cache: HIT` (kaynakta kendi önbelleği var). Canlı görsel `cf-cache-status: HIT`, `max-age=86400`. Canlı `googleNews.xml` `max-age=86400`, `DYNAMIC`. Eskiyen satırlar: `KURULUM.md:52` ve §9 madde 8. | 0,5 gün belge + kullanıcıya soru |
| B4 | P1 | **Türkiye'den gelen istek Avrupa'dan karşılanıyor.** | Ölçüldü (`/cdn-cgi/trace`, 6+1 deneme): `bursahakimiyet.com.tr` 6 kez `colo=AMS`, ilk denemede `LHR`. Aynı anda `www.cloudflare.com` ve `developers.cloudflare.com` 6/6 `colo=IST`. İstemci `loc=TR`. Ortanca TCP 76 ms'ye karşı 21 ms, TLS 160 ms'ye karşı 47 ms. Cloudflare veri merkezi kümesinin müşteriye göre değiştiğini yazıyor [K18]. Plan tablosunda "Network Prioritization" yalnız sözleşmeli planda var [K17]. | Ölçüm: §3.4 |
| B5 | P1 | **Önbellek isabetinde başlıklar kayboluyor.** İsabette yanıt yalnız gövde ve içerik türüyle yeniden kuruluyor. Görünümün eklediği etiket ya da politika başlığı isabette düşer. | Okundu: `sayfa_onbellegi.py:107-110` (kurulum), `:115-116` (saklanan alanlar). | 0,5 gün |
| B6 | P1 | **Toptan geçersizleştirme.** Herhangi bir haber, köşe, son dakika ya da düzeltme kaydı **bütün** sayfa önbelleğini öldürüyor. CDN'e aynen taşınırsa her kayıtta "hepsini temizle" olur. Deprem gecesi her düzeltmede önbellek sıfırlanır. | Okundu: `sinyaller.py:150-155, 210-214`, `onbellek.py:139-146`. | Etiketli temizleme (§5) |
| B7 | P1 | **Yarış penceresi.** Sürüm, işlem bitmeden (`post_save`) artırılıyor. İlişkili kayıtlar sinyalden sonra yazılıyor. Bu arada gelen bir istek eski içeriği yeni sürüm anahtarıyla 30 sn saklayabilir. Ardından CDN temizliği gelirse eski kopya CDN'e de girer. | Okundu: yeni kayıt `transaction.atomic` içinde (`kimlik.py:82`), alıcı `post_save` (`sinyaller.py:213`), depoda hiç `on_commit` yok (`grep on_commit` boş). | 0,5 gün |
| B8 | P1 | **Göreli zaman ve bugünün tarihi HTML'e basılıyor.** CDN süresi bu metinleri bayatlatır: 4 dakikalık kopyada "14 dk önce" yazısı 18 dakikayı gösterir. | Okundu: `parca/son_dakika.html:50,67` (`goreli_zaman`), `parca/ust_bant.html:11` (`{% now %}`). | 0,5 gün (frontend) |
| B9 | P1 | **Paylaşım parametreleri CDN'de her tıkı ıska yapar.** Uygulama `utm_*` ve `fbclid` parametrelerini anahtardan atıyor. Cloudflare'de sorgu dizesini anahtardan çıkarmak Free, Pro ve Business'ta yok (Enterprise) [K8]. Her `fbclid`'li Facebook tıkı ayrı bir ıska olur. | Okundu: `sayfa_onbellegi.py:31-33, 49`. Çözüm: istek yeniden yazma kuralında `remove_query_args` [K16]. | Kural (§4.5) |
| B10 | P1 | **nginx mikro önbelleği yayın temizliğinden habersiz.** CDN temizlendiğinde nginx eski kopyayı verir. Ayrıca Django'nun `Cache-Control` değeri nginx'in `proxy_cache_valid` süresini ezer [K40]. | Okundu: `snippets/bh-mikro-onbellek.conf:8`. | Karar: CDN varken kapalı kalır (§4.1) |
| B11 | P1 | **Uygulama önbelleği yalnız 7 görünümde.** Köşe yazısı detayı, yazar, `/son-haberler`, RSS, eczane, piyasa, `/ara`, `/daha-fazla` önbelleksiz. CDN'siz bir trafik sıçramasında bunlar veritabanına gider. | Okundu: `grep @sayfa_onbellegi` (icerik 5: anasayfa, kategori, konular, konu, düzeltmeler; medya 1: köşe listesi; taksonomi 1: haber). | 0,5 gün (CDN'siz yedek kip için) |
| B12 | P2 | **`googleNews.xml` 300 sn.** Haberin News haritasına girmesini 5 dk geciktirebilir. Eski site 86.400 sn veriyordu (ölçüldü). | Okundu: `nginx/...conf:152`, `ara_katman.py:96-97`. | §4.3 |
| B13 | P2 | **`ETag` ve `Last-Modified` yok** (`/rss` dışında). CDN yeniden doğrularken `304` alamaz, tam gövdeyi indirir [K3]. | Ölçüldü. | 0,5 gün |
| B14 | P2 | **Belge hatası.** `gunicorn.conf.py:41` "unix soketi" diyor, oysa `bind` TCP (`:17`). | Okundu. | 5 dk |
| B15 | P2 | **`/gorsel/` 1 yıl `immutable`.** Kaynak görsel aynı adla değiştirilirse eski türev okura bir yıl kalır. Panel yüklemelerinin benzersiz ad aldığı doğrulanmalı. | Okundu: `nginx/...conf:177`. | → backend |

---

## 3. CDN seçimi

### 3.1 Ölçütler

| Ölçüt | Neden önemli |
|---|---|
| Türkiye'de uç sunucu | Okurun çoğu Türkiye'de, mobilde. Ölçülen fark ilk bağlantıda ~110 ms (B4). |
| Etiketle temizleme ve hızı | Son dakika hedefi (§4.4). Toptan temizleme sıçramada kaynağı boğar. |
| SWR ve SIE desteği | Yayın anında ve kaynak çöktüğünde okur beklemesin, hata görmesin. |
| DDoS koruması ve challenge/CAPTCHA | BİK Tebliği md. 4/9: "DDOS saldırıları gibi ani trafik artışlarında … çevrimiçi test (CAPTCHA) kullanılması gerekmektedir" [K37]. |
| BİK IP istisnası | BİK Tebliği md. 6/3: 82.222.188.222 ve 213.74.78.242 beyaz listede olmalı [K37]. |
| Fiyat | Kullanıcı eşiği 6. |
| KVKK, veri yerelliği | CDN okur IP adresini işler. Yurt dışındaki sağlayıcıda yurt dışına aktarım kuralları devreye girer [K36]. |
| Satıcı bağımlılığı | Kod standart başlıklarla yazılır, temizleme bir adaptörün arkasında durur (§5.3). Sağlayıcı değişirse yalnız adaptör değişir. |

### 3.2 Karşılaştırma

Kaynaklar 21 Ekim 2026'da okundu.

| | Cloudflare Free | Cloudflare Pro | Cloudflare Business | Bunny CDN | Fastly | Amazon CloudFront | Medianova | Erstream (eski Merlin CDN) |
|---|---|---|---|---|---|---|---|---|
| **Fiyat** | 0 $ [K17] | 20 $/ay yıllık, 25 $ aylık [K17] | 200 $/ay yıllık, 250 $ aylık [K17] | Avrupa 0,01 $/GB, Asya 0,03, Orta Doğu 0,06; aylık en az 1 $ [K20]. Shield: Basic 0, Advanced 9,5 $, Business 99 $ [K22] | 100 GB bedava, sonra Avrupa 0,12 $/GB; 1 milyon istek bedava, sonra 10 bin istek 0,01 $ [K25] | Sabit plan: Free 0 $ (1 milyon istek, 100 GB), Pro 15 $ (10 milyon, 50 TB), Business 200 $ (125 milyon, 50 TB), Premium 1.000 $ (500 milyon) [K29] | Yayımlanmıyor ("Talk to an Expert") [K34] | Yayımlanmıyor |
| **Türkiye'de PoP** | Ağda IST var, ama bu alan adı ölçümde AMS/LHR'den karşılandı (B4) | Doğrulanmadı | Doğrulanmadı. "Network Prioritization" yalnız sözleşmeli planda [K17] | İstanbul listede [K21]. Fatura bölgesi doğrulanmadı | **Yok**; en yakını Sofya [K26] | İstanbul listede [K30] | **İstanbul + Ankara** [K34] | Doğrulanmadı |
| **Etiketle temizleme** | Var. Hesap başına dakikada 5 istek, istek başına 100 etiket, kova 25 [K1] | Var, saniyede 5 istek [K1] | Var, saniyede 10 istek [K1] | Var (`CDN-Tag`, en çok 1.024 bayt). 120'lik kova, saniyede 5 [K23] | Var (`Surrogate-Key`, en çok 16 KB) [K27] | Var. Nesne başına en çok 50 etiket. Ayda ilk 1.000 yol/etiket bedava [K31][K32] | Doğrulanmadı | Doğrulanmadı |
| **Temizleme hızı** | "150 ms altı" (satıcı iddiası, araştırma raporundan) | aynı | aynı | Doğrulanmadı | Doğrulanmadı | Doğrulanmadı | "Avg. purge time" ifadesi var, değer belirsiz [K34] | — |
| **Geçersizleştirme (soft purge)** | Var [K3] | Var | Var | Yok (yalnız silme) [K23] | Var [K28] | Doğrulanmadı | Doğrulanmadı | — |
| **SWR / SIE** | Var. SWR artık eşzamansız. **`s-maxage` ikisini de kapatır** [K4][K5] | aynı | aynı | `STALE` ve `UPDATING` durumları var [K24]. Başlık desteği doğrulanmadı | Var [K28] | Var [K33] | Doğrulanmadı | — |
| **HTML'i önbelleğe alma** | Kuralla ("Eligible for cache"). Varsayılan değil [K7]. Free'de 10 kural [K8] | 25 kural | 50 kural | `Cache-Control`'e uyar. Smart Cache açıksa yalnız statik [K24] | Var | Pro planda "Custom Caching Rules" **yok**, Business'ta var [K29] | Var ("Dynamic Site Caching") [K34] | Video odaklı |
| **DDoS** | Ölçümsüz ("Unmetered") [K17] | aynı | aynı + %100 SLA [K17] | Shield [K22] | Ayrı ürün [K25] | Her planda; gelişmiş koruma Business'tan itibaren [K29] | Var [K34] | — |
| **Challenge / CAPTCHA** | Managed, Non-Interactive ve Interactive Challenge kuralları her planda [K14]. "I'm Under Attack" kipi [K10]. Hız sınırı kuralı 1, 10 sn pencere [K13] | Hız sınırı kuralı 2, 1 dk pencere [K13] | Hız sınırı kuralı 5 [K13] | "Block & challenge page" [K22] | Doğrulanmadı | JavaScript Challenge Pro'da **yok**, Business'ta var [K29] | Bot yönetimi var [K34] | — |
| **BİK IP istisnası** | IP Access Rules "Allow" her planda, 50.000 kural. Özel kuralları, hız sınırını ve yönetilen kuralları atlar [K12] | aynı | aynı | WAF kuralıyla, doğrulanmadı | Doğrulanmadı | WAF kuralıyla, doğrulanmadı | Doğrulanmadı | — |
| **KVKK** | ABD şirketi, yurt dışına aktarım | aynı | aynı | Doğrulanmadı | ABD | ABD | Türk şirketi, yurt içi PoP | Türk |
| **Taşıma bedeli** | **Yok**, bölge zaten orada (B3) | Plan yükseltme | Plan yükseltme | DNS ya da CNAME değişikliği | Aynı | Aynı | Aynı | Aynı |

Bunny'nin ağ sayfası İstanbul'u Asya bloğunda listeliyor [K21]. Türkiye trafiğinin
0,01 $ mı, 0,03 $ mı, 0,06 $ mı faturalanacağı yazılı olarak sorulmalı.
`merlincdn.com` adresi `erstream.com`'a yönleniyor (ölçüldü: `curl -L`). Site
canlı yayın, OTT ve video ürünlerini anlatıyor; HTML sitesi için değerlendirilmedi.

### 3.3 Trafik senaryoları ve aylık maliyet

Eski sitenin trafik verisi elde yok. GA4 eski sağlayıcının hesabında
(`KURULUM.md:10-11`). Mevcut Cloudflare bölgesinin analitiği gerçek sayıyı verir
(karar K3). O gelene kadar üç senaryo kullanıldı:

- **Sayfa ağırlığı (ölçüldü):** Haber detayı gzip ile 13,9 KB HTML, 8 `<img>`,
  11 statik dosya. Anasayfa gzip ile 35 KB HTML. Anasayfa görselleri 0,15–0,23 MB
  (`URUN-PLANI.md` §70).
- **Varsayım:** Görüntüleme başına ortalama 0,3 MB aktarım ve 15 istek (ilk
  görüntüleme fazla, tekrarda tarayıcı önbelleği düşürür). Reklam ağları bu
  hesaba girmez, kendi sunucularından gelir.

| Ay başına | 1 milyon görüntüleme | 5 milyon | 20 milyon |
|---|---|---|---|
| Aktarım / istek | 0,3 TB / 15 milyon | 1,5 TB / 75 milyon | 6 TB / 300 milyon |
| Cloudflare Free / Pro / Business | 0 / 20–25 / 200–250 $ | aynı (trafikten bağımsız) | aynı |
| Bunny (0,01–0,06 $/GB) + Shield Advanced 9,5 $ | ~13–28 $ | ~25–100 $ | ~70–370 $ |
| Fastly (Avrupa) | ~38 $ | ~240 $ | ~1.000 $ |
| CloudFront sabit plan | 200 $ (Pro'nun 10 milyon istek kotası aşılır; challenge ve kural için de Business gerekir) | 200 $ | 1.000 $ (Premium) |
| Medianova | teklif | teklif | teklif |

Bu sayılar varsayım üzerine hesap. Gerçek trafik verisi gelince yeniden hesaplanır.

**CloudFront için dikkat:** Sabit planlarda aşım ücreti yok [K29], ama kota
aşılınca ne olduğu ayrı bir belgede ve okunmadı. Etiket temizlemeleri ayda 1.000
"yol" kotasından düşüyor [K31]. Günde ~150 yayın ve yayın başına ~8 etiketle
ayda ~36.000 yol eder. Bunun sabit planda ücretlenip ücretlenmediği doğrulanmadı.

### 3.4 Öneri

**Birincil öneri: Cloudflare, Pro plan.**

1. **Taşıma yok.** Bölge, DNS ve TLS zaten orada (B3). Kesim günü yalnız kaynak
   adresi değişir. Geri dönüş tek ayar ve ~1 dakika sürer (§9). `KURULUM.md`
   §10'daki "TTL 300 sn sayesinde ≤ 10 dk" yerine.
2. **Free ile Pro arasındaki asıl fark temizleme hızı:** dakikada 5 istek
   (kova 25) ile saniyede 5 istek [K1]. Deprem gecesi masada dakikada 10–20
   kayıt olabilir. Free'de etiketler 15 sn'lik paketlere toplanarak sığdırılabilir
   (§5.3), ama son dakika gecikmesi 15 sn'ye çıkar. Pro'da ayrıca 25 önbellek
   kuralı, 20 özel WAF kuralı ve 2 hız sınırı kuralı (1 dk pencere) var
   [K8][K11][K13].
3. **Business ancak ölçüm gerektirirse.** Pro'da İstanbul'dan hizmet gelmiyorsa
   ve ~110 ms'lik ilk bağlantı farkı kabul edilmezse, ayda 200–250 $ ile
   Business denenir. Business'ta da İstanbul garantisi yok ("Network
   Prioritization" yalnız sözleşmeli planda [K17]). Bu durumda eşdeğer seçenek
   şu karma kurgudur: HTML ve güvenlik Cloudflare'de kalır, görseller Bunny'nin
   İstanbul PoP'una bir görsel alt alanıyla taşınır. Bu P2'dir, ek DNS ve ek
   hesap gerektirir.
4. **Yerel seçenek (Medianova):** Türkiye'de iki PoP var ve KVKK açısından en
   temiz yol. Ama fiyat, etiketle temizleme, SWR/SIE ve API belgesi herkese açık
   değil (dokümantasyon müşteri paneline yönleniyor, ölçüldü). Teklif
   isteğinde sorulacaklar: §13.

**Pro'ya geçmeden yapılacak ölçüm** (0 $; hesap erişimi gerekir):

- Hazırlık alt alanında (§9) Free bölgeden `/cdn-cgi/trace` ölç.
- Farklı ağlardan (Türk Telekom, Turkcell, Vodafone mobil, bir fiber sağlayıcı)
  `colo=` dağılımını topla.
- Pro'ya bir ay geç ve aynı ölçümü tekrarla. Pro aylık ödenip iptal edilebilir:
  25 $.

---

## 4. Önbellek katmanları ve `Cache-Control` politikası

### 4.1 Katmanlar

```
okur ─► tarayıcı önbelleği (kısa: 0–60 sn HTML; statik 1 yıl)
      ─► CDN uç sunucu (HTML 60 sn–1 sa; yayında etiketle temizlenir; SWR + SIE)
      ─► CDN üst katmanı (Smart Tiered Cache, Free'de var [K9])
      ─► nginx: statik/görsel diskten · HTML önbelleği KAPALI (B10)
      ─► gunicorn → Django sayfa önbelleği (Redis, 30 sn, kayıtta sürümle düşer)
      ─► PostgreSQL
```

**nginx HTML önbelleği CDN varken kapalı kalır.** Yayın temizliğinden haberi
olan tek kaynak katmanı uygulama önbelleğidir. nginx önbelleği yalnız "CDN'siz
kip" yedeği olarak, 5 saniyelik ve `X-Accel-Expires` ile açılır. nginx bu
başlığı `Cache-Control`'den önce okur ve okura göndermez [K40].

### 4.2 Başlık sözleşmesi

Uygulama her okur yanıtına şu başlıkları yazar:

- **`Cache-Control`:** Tarayıcı içindir. `public, max-age=N`.
- **`CDN-Cache-Control`:** CDN içindir. `max-age=N, stale-while-revalidate=N, stale-if-error=N`.
  Cloudflare bu başlık varken önbellek kararını yalnız ona göre verir ve
  `Cache-Control`'ü olduğu gibi tarayıcıya geçirir [K6]. Böylece `s-maxage`
  kullanmadan CDN'e uzun, tarayıcıya kısa süre verilir. `s-maxage` Cloudflare'de
  SWR ve SIE'yi kapatır [K4][K5]. Başlık standarttır (RFC 9213 [K38]); sağlayıcı
  değişince başlıklar aynı kalır. Fastly kendi `Surrogate-Control` başlığını da
  okur [K28].
- **Etiket başlığı:** Sağlayıcıya göre ad değişir. `BH_CDN_ETIKET_BASLIGI`
  ayarıyla `Cache-Tag` (Cloudflare [K2]), `CDN-Tag` (Bunny [K23]) ya da
  `Surrogate-Key` (Fastly [K27]). Değer ASCII, boşluksuz, en çok 50 etiket.
  50, en dar sınırdır (CloudFront [K32]).
- **`ETag`:** Saklanan gövdenin özeti. Geçersizleştirmeden sonra CDN `304` alır
  ve gövdeyi yeniden indirmez [K3] (B13).
- **Yasak:** Okur sayfasında `Vary: Cookie` ve `Set-Cookie` yok. Oturumlu ya da
  çerez yazan yanıt `Cache-Control: private, no-store` alır ve CDN başlığı almaz.

### 4.3 Sayfa türüne göre politika

Kısaltmalar: **T** = `Cache-Control` (tarayıcı), **C** = `CDN-Cache-Control`,
`swr` = stale-while-revalidate, `sie` = stale-if-error. Süreler saniye. "1g" = 86.400.

| Tür | Adres | T | C | Etiketler | Gerekçe |
|---|---|---|---|---|---|
| Anasayfa | `/` | `public, max-age=30` | `max-age=60, swr=30, sie=86400` | `bh t-anasayfa l-anasayfa sd-bandi` | Yayında anında temizlenir. 60 sn, temizlemenin kaçırdığı şeylerin (en çok okunan, döviz, hava, göreli zaman) en geç ne zaman tazeleneceğini belirler. En kötü durum 90 sn, §21'deki "beş dakika eski manşet kabul edilemez" kuralının altında. |
| Kategori | `/<kat>`, `/son-haberler`, `?sayfa=N` | `public, max-age=30` | `max-age=120, swr=60, sie=86400` | `bh t-kategori l-kat-<slug>` (`l-son`) | Yayında temizlenir. Liste trafiği anasayfadan az. |
| Haber (son 48 saat) | `/<kat>/<slug>-<id>` | `public, max-age=60` | `max-age=240, swr=60, sie=604800` | `bh t-haber h-<id> k-<slug> sd-bandi` | Düzeltmede temizlenir. Temizleme düşerse en kötü durum 300 sn (§21 sınırı). SIE 7 gün: kaynak çökse de okunan haber açık kalır. |
| Haber (7 günden eski) | aynı kalıp | `public, max-age=300` | `max-age=3600, swr=600, sie=2592000` | aynı | Arşiv sayfası nadiren değişir. Kenar kutuları en geç 1 saatte tazelenir (B8 düzeltilince göreli zaman sorun olmaz). |
| Köşe yazısı detayı | `/yazarlar/.../<slug>-<id>` | `public, max-age=60` | `max-age=600, swr=120, sie=2592000` | `bh t-kose ky-<id> y-<yazar>` | |
| Köşe listesi, yazar, yazarlar | `/kose-yazilari`, `/yazarlar/...` | `public, max-age=60` | `max-age=300, swr=60, sie=86400` | `l-kose`, `y-<id>` | |
| Konu, konular, düzeltmeler | `/konu/<slug>`, `/konular`, `/duzeltmeler` | `public, max-age=60` | `max-age=300, swr=60, sie=86400` | `konu-<id>`, `l-konular`, `l-duzeltmeler` | |
| Resmî ilan | `/resmi-ilan` | `public, max-age=60` | `max-age=300, swr=60, sie=86400` | `l-resmi-ilan` | BİK md. 4/5: geçiş reklamı yok. Önbellek etkilemez. |
| "Daha fazla" parçası | `/daha-fazla?...` | `public, max-age=60` | `max-age=120, swr=60, sie=3600` | `l-anasayfa` / `l-kat-<slug>` / `l-son` / `l-kose` | Sayfa değil parça; `X-Robots-Tag: noindex` eklenmeli. |
| Arama | `/ara?q=` | `public, max-age=60` | `max-age=300, swr=60` | `t-ara` | Çok sayıda farklı sorgu, isabet düşük. Asıl koruma hız sınırı (nginx `limit_req` + CDN kuralı). `noindex` korunur. |
| Nöbetçi eczane | `/nobetci-eczane[/<ilce>]` | `public, max-age=60` | `max-age=600, swr=120, sie=86400` | `canli-eczane` | Veri yazılınca betik etiketi temizler (→ veri-entegrasyon). |
| Piyasa | `/piyasa/<x>` | `public, max-age=30` | `max-age=60, swr=30, sie=3600` | `canli-piyasa` | Kur sık değişir; bayat veri tarihiyle gösterilir. |
| RSS | `/rss`, `/rss/<kat>` | `public, max-age=300` | `max-age=300, swr=60, sie=86400` | `rss rss-<slug>` | Yayında temizlenir. Okuyucular sık yoklar. |
| Google News haritası | `/static/sitemap/googleNews.xml` | `public, max-age=60` | `max-age=60, swr=30, sie=3600` | `sm-news` | B12. Yayında temizlenir. |
| Site haritası dizini ve aylık dosyalar | `/static/sitemap/*.xml` | `public, max-age=300` | bu ay `max-age=600`, geçmiş aylar `max-age=86400`; `sie=604800` | `sm-index`, `sm-<önek>-<ay>` | `besleme/bellek.py`'nin `ay_degisti` sinyali etiketi verir. |
| `robots.txt`, `ads.txt` | | `public, max-age=3600` | `max-age=3600` | `bh` | |
| Statik, özetli | `/statik/*.<özet>.*` | `public, max-age=31536000, immutable` | (aynısı yeter) | — | Var. Değişmez. |
| Statik, özetsiz | `/statik/...` | `public, max-age=3600` | aynı | — | Var. |
| Görsel türevi | `/gorsel/...` | `public, max-age=31536000, immutable` | aynı | — | Var. B15 doğrulanmalı. |
| Arşiv görseli | `/arsiv-gorsel/...` | `public, max-age=2592000` | `max-age=31536000` | — | Dosyalar değişmez. |
| 301 (adres düzeni) | | `public, max-age=604800` | aynı | — | Var (`adres_duzeni.py:103`). |
| 404 | | `public, max-age=60` | `max-age=60` | `bh` | Yanlış adres taraması kaynağı yormasın, yeni yayımlanan adres de takılı kalmasın. |
| 5xx | | `no-store` | — | — | CDN bayat kopyayı verir (SIE). Hata saklanmaz. |
| Panel, yönetim, durum, giriş, okunma işareti | `/panel/*`, `/yonetim/*`, `/_durum`, `/okunma` | `private, no-store` | — | — | **Asla.** Ayrıca CDN'de atlama kuralı (§4.5). |
| Oturumlu okur (personel siteyi geziyor) | herhangi bir okur adresi | `private, no-store` | — | — | Sunum düğmeleri basılıyor (`baglam.py:292-296`). |

`bh` etiketi her okur yanıtında bulunur. Menü ya da kategori adı değişirse
gereken "tüm siteyi temizle" bu etiketle yapılır.

### 4.4 Son dakika hedefi

| Ölçüt | Hedef | Nasıl |
|---|---|---|
| Panelde "Yayına al"dan anasayfada görünmeye (p95) | **≤ 10 sn** | İşlem bitince (`on_commit`) temizleme isteği gönderilir (~1 sn). Cloudflare temizlemesi "150 ms altı" (satıcı iddiası). Ardından ilk istekte kaynak ~0,1 sn'de üretir. |
| Temizleme düşerse en kötü durum, anasayfa | ≤ 90 sn | `max-age=60` + `swr=30` |
| Temizleme düşerse en kötü durum, haber detayı | ≤ 300 sn | `max-age=240` + `swr=60` (§21 sınırı) |
| Düzeltme notunun görünmesi (p95) | ≤ 10 sn | `h-<id>` temizlenir |
| Hukuki kaldırma (5651) | ≤ 10 sn **ve** bayat kopya yok | Geçersizleştirme değil **silme**. Ardından tarayıcı süresi (≤ 60 sn) dolar. |

Free planda temizleme istekleri 15 sn'lik paketlere toplanır, hedef ≤ 20 sn olur.

### 4.5 Cloudflare kural taslağı

Bölge ayarları, kullanıcı onayından sonra uygulanır. Free sınırlarına sığar.

| Tür | Kural | Not |
|---|---|---|
| URL yeniden yazma 1/10 | Okur adreslerinde `remove_query_args(http.request.uri.query, "fbclid","gclid","utm_source","utm_medium","utm_campaign","utm_term","utm_content")` | B9. Sorgu kaynağa ve önbellek anahtarına temiz gider [K16]. Önbellekten önce çalıştığı hazırlıkta doğrulanmalı. |
| Önbellek kuralı 1/10: **atla** | Yol `/panel/`, `/yonetim/`, `/_durum`, `/okunma` ile başlıyorsa **ya da** çerezde `sessionid=` veya `messages=` varsa | `csrftoken` atlama sebebi değil: oturumsuz CSRF çerezi sayfayı değiştirmez. Çerez yazan yanıtı Cloudflare zaten saklamaz [K4]. |
| Önbellek kuralı 2/10: **önbelleğe uygun** | Konak `www.bursahakimiyet.com.tr`, GET/HEAD. Edge TTL: "kaynak başlığı varsa ona uy". Bayat kopyayı yenilerken verme: **açık** | HTML varsayılan olarak saklanmaz [K7]. `CDN-Cache-Control` okunur [K6]. |
| IP Access Rule "Allow" | 82.222.188.222, 213.74.78.242 | BİK md. 6/3 [K37]. Özel kuralları, hız sınırını ve yönetilen kuralları atlar [K12]. "I'm Under Attack"i atlayıp atlamadığı **doğrulanmadı**, hazırlıkta denenmeli. |
| Hız sınırı 1/1 (Free) | `/ara` IP başına 10 sn'de N istek → Managed Challenge | Free'de alan yalnız yol, pencere 10 sn [K13]. |
| Hız sınırı 2/2 (Pro) | Tüm okur yolları, IP başına 1 dk'da çok yüksek istek → Interactive Challenge | BİK md. 4/9'daki "yüksek hızlı istek gönderimleri" [K37]. Gerçek okura dokunmaz. |
| Ayar | **Always Online kapalı** | Açıkken `stale-while-revalidate` ve `stale-if-error` yok sayılır [K4]. |
| Ayar | Smart Tiered Cache açık | Free'de var [K9]. Kaynağa giden ıskayı toplar. |
| Ayar | SSL "Full (strict)" + Authenticated Origin Pulls | AOP her planda var [K15]. Kaynak yalnız Cloudflare'den bağlantı kabul eder. |

**DDoS ve CAPTCHA çalışma kılavuzu (taslak):**

- Deprem trafiği gerçek okurdur. **Herkese challenge gösterilmez.**
- Yalnız hız sınırı kuralı tetiklenen IP'ler sınanır.
- "I'm Under Attack" kipi yalnız doğrulanmış saldırıda açılır. Cloudflare bu
  kipin analitiği etkilediğini yazıyor [K10]. BİK md. 5/4'e göre ölçüm kodunun
  çalışmamasından yayıncı sorumlu [K37].
- Cloudflare'in Managed ya da Interactive Challenge'ının BİK'in "çevrimiçi test
  (CAPTCHA)" ifadesini karşılayıp karşılamadığı hukuki bir yorum. →
  `hukuk-guvenlik-uyum-uzmani` (karar K6).

---

## 5. Yayında temizleme (purge-on-publish)

### 5.1 Hangi olay hangi etiketi temizler

| Olay | Temizlenen etiketler | Kip |
|---|---|---|
| Haber yayına alındı | `h-<id>`, `l-anasayfa`, `l-kat-<slug>`, `l-son`, `rss`, `rss-<slug>`, `sm-news`, `sm-news-<ay>`, `sm-index`; varsa `konu-<id>`, `l-konular` | geçersizleştir |
| Haber düzenlendi | Yukarıdakiler. Kategori değiştiyse **eski** `l-kat-` ve `rss-` de (eski değer `pre_save` ile alınır; `besleme/bellek.py:_once` aynı deseni kullanıyor) | geçersizleştir |
| Haber yayından kaldırıldı ya da silindi | Yukarıdakiler | **sil** |
| Düzeltme notu | `h-<haber_id>`, `l-duzeltmeler` | geçersizleştir |
| Son dakika kaydı | `sd-bandi` (anasayfa ve bütün haber detayları) | geçersizleştir |
| Köşe yazısı | `ky-<id>`, `y-<yazar>`, `l-kose`, `l-anasayfa` (yazar kuşağı) | geçersizleştir |
| Yazar | `y-<id>` | geçersizleştir |
| Resmî ilan | `l-resmi-ilan`, `l-anasayfa` | geçersizleştir |
| Konu onayı ya da çıkarma | `konu-<id>`, `l-konular`, ilgili `h-<id>` | geçersizleştir |
| Kategori ya da tür değişti (menü) | `bh` | geçersizleştir |
| Canlı veri yazıldı | `canli-eczane`, `canli-piyasa` | geçersizleştir |
| Acil (5651 kararı, yanlış yayın) | `bh` | **sil** |

**`sd-bandi` maliyeti.** Bu etiket önbellekteki bütün haber detaylarını bayatlatır.
Geçersizleştirme ve SWR ile her sayfa ilk istendiğinde bir kez, arka planda
yenilenir. Okur beklemez [K3][K5]. Örneğin önbellekte 2.000 sıcak sayfa ve
sayfa başına ~60–200 ms ile 9 işçi dakikalar içinde bitirir. Yük testinde (§8.3,
S3) bu ölçülecek. Fazla gelirse kutu ayrı, kısa ömürlü bir parça adresine
taşınır (P2).

### 5.2 Neden silme değil geçersizleştirme

Silinen kopyanın ilk isteği kaynağı bekler. Bütün uç sunucular aynı anda ıska
yaşarsa kaynağa yığılma olur. Geçersizleştirilen kopya ise yenisi gelene kadar
verilir. `ETag` varsa ve içerik değişmediyse `304` ile yeniden kullanılır [K3].

**Silme yalnız iki durumda kullanılır:** içerik okura bir daha gösterilmemeli
(kaldırma, hukuk) ya da sayfa bozuk yayımlandı. Bunny'de geçersizleştirme yok,
her temizleme silmedir [K23].

### 5.3 Django tarafı tasarımı

Kod değişmedi; öneri dosya düzeyinde.

1. **`icerik/cdn.py` (yeni): sağlayıcıdan bağımsız arayüz.**
   - İşlev: `temizle(etiketler: set[str], kip: "gecersiz" | "sil")`.
   - Adaptörler: `Kuru` (yalnız günlüğe yazar; **varsayılan**, geliştirme ve
     test), `Cloudflare` (`purge_cache` ve `invalidate_cache` uçları [K1][K3]),
     `Bunny` (tag purge [K23]). Fastly ve CloudFront gerekirse eklenir.
   - Ayarlar `BH_CDN`, `BH_CDN_BOLGE`, `BH_CDN_ANAHTAR`, `BH_CDN_ETIKET_BASLIGI`
     ortamdan okunur (`settings.py` başarım bloğu).
2. **`icerik/sinyaller.py`: değişiklik.**
   - `_surum` ve kardeşleri etiket kümesini hesaplar (§5.1 tablosu).
   - Sürüm artırma ve CDN temizliği **`transaction.on_commit`** içinde yapılır
     (B7). Sürüm, okur yarışını kapatmak için işlem içinde de bir kez artırılır.
   - Sıra bağlayıcıdır: **önce uygulama önbelleği sürümü, sonra CDN.** Tersi
     olursa CDN yeniden doğrularken eski kopyayı uygulama önbelleğinden alır.
3. **Giden kutusu: `CdnTemizlik` modeli (yeni, migration ister).**
   - Alanlar: etiketler (JSON), kip, oluşturma zamanı, deneme sayısı, son hata,
     tamamlanma zamanı.
   - `on_commit` satırı yazar ve kısa ömürlü bir arka plan iş parçacığında
     gönderir (panel kaydı beklemez).
   - Başarısız satır kalır. Bir sonraki yayında ya da
     `manage.py cdn_temizle --bekleyenler` komutuyla yeniden denenir.
   - Zamanlayıcıyla yeniden deneme bir systemd timer'ı ister. Timer açmak
     kullanıcı kararıdır (EKIP değişmez kararları; karar K9).
4. **Toplama.** Kuyruktaki etiketler birleştirilip istek başına ≤ 100 etiketle
   gönderilir [K1]. Free kipinde 15 sn'lik pencereyle toplanır: dakikada en çok
   4 istek, kova 25.
5. **Görünürlük.**
   - `/_durum` yanıtında `cdn_kuyrugu` alanı (adet ve en eski kaydın yaşı)
     bulunur. 60 sn'yi aşarsa `uyari`.
   - Panel "Bugün" ekranında bir şerit gösterilir.
   - Her temizleme denetim kaydına yazılır (kim, ne zaman, hangi etiketler).
6. **Görünüm sözleşmesi.**
   - Görünüm `yanit.onbellek_etiketleri` ve `yanit.onbellek_turu` alanlarını
     iliştirir. `okunma_haber` bugün aynı yolla iliştiriliyor.
   - `sayfa_onbellegi` ikisini kayıtla saklar ve isabette geri koyar (B5).
     `ETag`'i saklanan gövdenin özetinden üretir, `If-None-Match` gelirse `304`
     döner.
7. **Politika ara katmanı: `cekirdek/onbellek_politikasi.py` (yeni).**
   - §4.3 tablosu `url_name`'e göre tek yerde durur.
   - `MIDDLEWARE` içinde `AdresDuzeni`'nin hemen altına, `SessionMiddleware`'in
     üstüne konur. Böylece yanıt yolunda oturum, CSRF ve `OturumSuresi`'nden
     **sonra** çalışır ve okur sayfasından `Vary: Cookie`'yi kaldırabilir.
   - Oturumlu istek ya da `Set-Cookie` taşıyan yanıt `private, no-store` alır.
     5xx yanıt `no-store` alır.
8. **Panel düğmeleri.**
   - Haber ekranında "Bu haberin önbelleğini temizle" (yayın yetkisi).
   - "Acil: tüm siteyi temizle" yalnız Yayın Yönetmeni için olur, dakikada 1
     sınırı ve gerekçe alanı taşır, denetim kaydına yazılır. Kimin yetkili
     olacağı karar K7.

### 5.4 API anahtarının gizliliği

Depo herkese açık.

- **Jeton kapsamı:** Cloudflare API jetonu yalnız "Zone · Cache Purge" iznini ve
  yalnız bu bölgeyi kapsar. Hesap genel anahtarı (Global API Key) kullanılmaz.
- **Yeri:** `/etc/bursahakimiyet/ortam` (0640 root:bh; `KURULUM.md` §5).
  `dagitim/.env.ornek`'e yalnız boş `BH_CDN_ANAHTAR=` satırı eklenir.
  `.gitignore` zaten `.env`, `*.env` ve `.env.*` desenlerini dışlıyor (okundu).
- **Denetim:** `cekirdek/denetimler.py`'ye bir kontrol eklenir: `BH_CDN` gerçek
  bir sağlayıcıysa ve anahtar boşsa `check --deploy` hata verir. Anahtar
  günlüğe ve `/_durum`'a hiçbir zaman basılmaz.
- **Sızıntı önlemi:** CI'a gizli bilgi taraması eklenir (P1, → test-kalite).
  GitHub'ın herkese açık depolardaki "push protection" özelliği ayrıca açılabilir
  (doğrulanmadı).
- **Rotasyon:** 90 günde bir. Jetonun kaynak IP'yle kısıtlanabildiği
  doğrulanmadı; doğrulanırsa sunucu IP'siyle kısıtlanır.

---

## 6. Çerez, oturum ve kişiselleştirme

### 6.1 Önbelleği bozan çerezler

| Çerez | Nerede | CDN'deki davranış |
|---|---|---|
| `sessionid` | Panel girişinden sonra | **Atla** (§4.5). Yanıt da `private, no-store`. |
| `messages` | Panel işlemlerinden sonra | Atla. |
| `csrftoken` | Panel giriş formu | Atlama sebebi değil. Okur şablonunda form yok (okundu). Yanıtta `Set-Cookie` varsa CDN saklamaz [K4]. |
| Rıza çerezi (henüz yok, KVKK aydınlatmasıyla gelecek) | İstemcide | HTML'e etki **etmemeli**. Rıza durumu yalnız JavaScript'te okunur. Sunucuya giden çerez sayfayı değiştirmez. |
| Reklam ve analitik çerezleri (GA4, AdSense, BİK Analitik) | Üçüncü taraf ya da istemci | HTML'e etki etmez. Cloudflare varsayılan anahtarı çerez içermez. Bunlar okur sayfalarını önbelleğe uygun bırakır. |

### 6.2 `Vary`

- Okur sayfalarından `Vary: Cookie` kaldırılır (B1, §5.3 madde 7).
  `Accept-Encoding` kalır.
- Cloudflare'in yeni Vary desteği, kurala yazılan başlıklarda `Vary`'yi anahtara
  katıyor ya da önbelleği atlatıyor [K19]. `Cookie`'nin anahtara girmemesi için
  kaynakta hiç gönderilmemesi en güvenli yol.
- nginx tasarısı bunu zaten `proxy_ignore_headers Vary` ile yapıyordu
  (`bh-mikro-onbellek.conf:24`).

### 6.3 Okunma sayacı: HTML isteğinden ayrılması (B2)

1. **Yeni uç: `POST /okunma`.**
   - Gövde `{"h": <id>}`.
   - Yanıt `204`, `Cache-Control: no-store`.
   - CSRF muafiyeti var; yerine `Origin` ya da `Sec-Fetch-Site: same-origin`
     denetimi yapılır.
   - nginx'te IP başına `limit_req` uygulanır. Yalnız yayında olan haber sayılır.
2. **`site.js`.** Haber detayında `navigator.sendBeacon('/okunma', …)` bir kez
   çağrılır (sayfa görünür olduğunda).
3. **Geçiş anahtarı.** `BH_OKUNMA_KAYNAGI=istek|isaret`. `sayfa_onbellegi._say`
   yalnız `istek` kipinde çalışır. Kesim öncesi hazırlıkta iki kip yan yana
   karşılaştırılır.
4. **Davranış farkı.** JavaScript çalıştırmayan botlar ve JavaScript'i kapalı
   okurlar artık sayılmaz. Bu, sayıyı daha "gerçek okur"a yaklaştırır.
   "En çok okunanlar" eşiği (`okunma.ESIK_OKUNMA`) yeniden ölçülmeli.
   → `haber-sistemi-uzmani`'ne bilgi.

---

## 7. Trafik sıçraması senaryosu (deprem gecesi)

| | Normal gün (20 milyon/ay senaryosu) | Sıçrama ×20 | Sıçrama ×50 |
|---|---|---|---|
| Sayfa görüntüleme/sn | ~8 | ~150 | ~400 |
| Aktarım (0,3 MB/görüntüleme) | ~19 Mbit/s | ~360 Mbit/s | **~960 Mbit/s** |
| **CDN yok:** kaynağa giden HTML | ~8/sn | ~150/sn | ~400/sn + ~6.000 statik/görsel isteği/sn |
| **CDN var, HTML isabeti %97:** kaynağa giden HTML | <1/sn | ~5/sn | ~12/sn + yenilemeler |

**Darboğaz CDN'siz kurguda bağlantı hattıdır, işlemci değil.** Uygulama
önbelleği isabette 7–9 ms (ölçüldü). 9 işçi saniyede yüzlerce isabeti kaldırır.
Ama ×50 sıçramada görseller dahil ~1 Gbit/s gerekir. Türkiye'deki VDS
tekliflerinin bağlantı sınırı kiralamadan önce sorulmalı (`KURULUM.md` §2).

**Kaynağı koruma:**

- **Bayat kopya:** CDN'de SWR + SIE (§4.3). Kaynak çökse de okunan sayfalar
  7–30 gün açık kalır. 404 bu kapsama girmez [K4].
- **Iskanın toplanması:** Smart Tiered Cache, Cloudflare'de bütün planlarda var
  [K9]. Uygulama önbelleğinin yığılma kilidi var (`onbellek.py:82-99`). Sayfa
  önbelleğinde kilit yok, eşzamanlı ıska aynı sayfayı birkaç kez kurar. CDN
  önündeyken bu önemsizleşir.
- **Kaynağa erişim:** Güvenlik duvarında 443 yalnız Cloudflare aralıklarına açık
  olur (`cloudflare-ip-guncelle.sh` listesi `ufw`'ye de yazılır) ve AOP kullanılır
  [K15]. Kaynak IP'si hiçbir yerde yayımlanmaz (e-posta, eski DNS kaydı, SPF).

**gunicorn.** 4 vCPU'da 9 sync işçi yeterli (`gunicorn.conf.py:19`). Iska
üretimi ~60–200 ms: haber detayı p95 63 ms (§70), ıska 205 ms (ölçüldü). Bu,
saniyede ~45–150 ıska eder. %97 isabette ×50 sıçramanın gerektirdiği ~12/sn'nin
çok üstünde. İşçi sayısını artırmak yerine isabeti artırmak doğru kaldıraç.
`timeout 30` kalır.

**PostgreSQL ve bağlantı havuzu.**

- Bağlantı sayısı: 9 işçi × kalıcı bağlantı (`CONN_MAX_AGE=60`,
  `settings.py:478-480`) + timer işleri + panel ≈ 15. `max_connections = 50`
  (`postgresql/bursahakimiyet.conf:81`).
- **pgBouncer gerekmez.** Eşik: işçi sayısı 30'u geçerse, ikinci bir uygulama
  makinesi gelirse ya da ASGI'ye geçilirse.
- O gün önce Django'nun yerleşik PostgreSQL havuzu (5.1'den beri,
  `OPTIONS["pool"]` [K41]) denenir, pgBouncer sonra.

**Redis.** Üretimde zorunlu sayılmalı. 9 süreç dosya önbelleğinde dizin
listeleme maliyeti ödüyor (`settings.py:432-433`). Aynı makinede, ücretsiz.

**Canlı blog (ileride, P2).** Araştırma raporunun önerisi: CDN'de 5–15 sn
saklanan bir JSON ucu ve istemcide yoklama. SSE ya da WebSocket sync işçiyi
tutar (`reports/Haber sitesi teknoloji seçimi.md`, "Canlı blog").
`/canli/<id>.json` için `C: max-age=5, swr=5` önerilir.

---

## 8. Ölçüm ve doğrulama

### 8.1 Hedefler

| Ölçü | Hedef | Nereden |
|---|---|---|
| HTML isabet oranı, normal gün | ≥ %90 | Cloudflare Cache Analytics (istek sayısıyla) |
| HTML isabet oranı, sıçrama | ≥ %97 | aynı |
| Statik ve görsel isabeti | ≥ %98 | aynı |
| Kaynağa giden HTML/sn | Sıçramada ≤ 20 | nginx erişim günlüğü (`$upstream_response_time` ile) |
| Yayın → görünme p95 | ≤ 10 sn (Free'de 20) | §8.3 S5 |
| `cdn_kuyrugu` en eski kayıt | ≤ 60 sn | `/_durum` |
| 5xx oranı (okura giden) | < %0,1 | Cloudflare analitiği; kaynak 5xx'leri SIE ile örtülmeli |

### 8.2 Başlık sözleşme testleri

Yeni dosya: `cekirdek/tests_onbellek_sozlesmesi.py`.

1. **Tablo tabanlı.** §4.3'teki her `url_name` için anonim GET: `Cache-Control`
   ve `CDN-Cache-Control` birebir beklenen değerde, etiket başlığı beklenen
   etiketleri içeriyor, `Set-Cookie` yok, `Vary`'de `Cookie` yok.
2. **İsabet = ıska.** Aynı adres ikinci kez istenir (`SAYFA_ONBELLEK_SANIYE=30`).
   Politika, etiket ve `ETag` başlıkları ilk yanıtla aynı olmalı (B5).
3. **Oturum.** Personel girişliyken okur adresi `private, no-store`, CDN başlığı
   yok, etiket yok.
4. **Asla önbelleklenmeyecekler.** `/panel/*`, `/yonetim/*`, `/_durum`, `/okunma`
   her durumda `no-store`.
5. **Sınıflandırılmamış adres yok.** `urlpatterns` taranır. Politikası olmayan
   yeni bir okur adresi testi düşürür, böylece yeni sayfa sessizce önbelleksiz
   kalmaz.
6. **Hata yanıtları.** 404 kısa politika alır. Zorlanan 500 `no-store` alır.
7. **CSRF.** Okur şablonlarında `csrfmiddlewaretoken` yok.
8. **Temizleme.** Haber kaydı → `Kuru` adaptör beklenen etiket kümesini kaydeder.
   İşlem geri alınırsa hiçbir şey gönderilmez. Gönderim, sürüm artışından sonra
   olur (B7).
9. **Giden kutusu.** Adaptör hata verirse satır kalır. Yeniden deneme başarılı
   olunca satır kapanır.
10. **Koşullu istek.** `If-None-Match` → `304`.
11. **Etiket sınırı.** Başlık ASCII, ≤ 50 etiket, ≤ 1.024 bayt (en dar sağlayıcı
    sınırı: Bunny [K23], CloudFront [K32]).
12. **Paylaşım parametreleri.** `?utm_source=x&fbclid=y` ile aynı uygulama anahtarı.

### 8.3 Yük ve davranış testi

**Ortam.** Yalnız yerel ya da hazırlık sunucusunda yapılır. **Canlıya, eski
siteye, CDN'in herkese açık uçlarına ve üçüncü taraf sitelere yük testi
yapılmaz.**

Windows geliştirme sunucusu (`runserver --noreload`) ölçüye uygun değil. Linux
hazırlıkta (ya da WSL2'de) nginx, gunicorn, PostgreSQL ve Redis birlikte
kurulur. Araç olarak ücretsiz tek dosyalık `k6` ya da `oha` kullanılır; depoya
bağımlılık eklenmez.

| Senaryo | Ne | Ölçülen |
|---|---|---|
| S1 Soğuk başlangıç | 200 eşzamanlı istek, anasayfa + 20 haber, 2 dk (`KURULUM.md` §9/7) | p50/p95, hata, kaynak istek/sn, okunma = istek sayısı (işaret kipinde: işaret sayısı) |
| S2 Gerçekçi dağılım | 5.000 haber adresi, Zipf (trafiğin %80'i 50 adreste) | Uygulama önbelleği isabeti, PG bağlantısı, işlemci |
| S3 Yayın anı | S2 sürerken 10 sn'de bir haber kaydı, ayrıca 1 son dakika kaydı | Kaynak sıçraması (`sd-bandi` maliyeti, §5.1) |
| S4 Kaynak çöktü | Hazırlık CDN bölgesinde gunicorn durdurulur | Okur adresleri 200 (bayat) dönmeli, `/panel` 5xx. Hız düşük tutulur. |
| S5 Temizleme gecikmesi | Kayıt → `curl` döngüsü (`cf-cache-status`, `Age`, içerik özeti) | Saniye (p50/p95). Yük yok, tek istemci. |

### 8.4 İzleme

`KURULUM.md` §7'ye eklenecekler:

- **`dagitim/bin/onbellek-denetle.sh` (yeni).** 10 adres için
  `cf-cache-status`, `Age` ve politika başlıklarını beklenen tabloyla
  karşılaştırır. Kesim günü ve T+1..T+14 boyunca elle çalıştırılır.
- **Cloudflare Cache Analytics.** Haftalık isabet oranı raporu (Free planda var).
- **`/_durum`.** `cdn_kuyrugu` alanı.

---

## 9. Kesim günü (F8) CDN adımları ve geri dönüş

Varsayım: Bölge Cloudflare'de kalıyor ve hesaba erişim alındı (K1). Her adım
kullanıcı eşiğidir (EKIP 1 ve 6).

**T−14 … T−7**

1. **Okuma.** Mevcut bölgenin DNS kayıtları, kuralları, SSL kipi ve WAF ayarları
   dışa aktarılır, belgeye yazılır. Hiçbir şey değişmez.
2. **Hazırlık alt alanı.** `hazirlik.bursahakimiyet.com.tr` proxied kayıtla yeni
   sunucuya yönlenir. DNS kaydı ekleme eşik konudur. Kurallar konak koşuluyla
   yalnız bu alt alana uygulanır.
3. **Uygulama.** `BH_CDN=cloudflare`, kapsamı dar API jetonu, §4.5 kuralları,
   BİK IP kuralı, AOP, kaynakta güvenlik duvarı.
4. **Testler.** §8.3 S1–S5. Farklı ağlardan `colo=` ölçümü (§3.4).
5. **Geri dönüş provası** (aşağıda), süresi belgeye yazılır.

**T0**

6. Önbellek kuralları `www` için etkinleştirilir. Eski site `DYNAMIC` olduğu
   için HTML'i zaten saklanmıyor. Kural, kaynak değişene kadar eski sitenin
   HTML'ine uygulanmamalı: konak koşuluyla birlikte kesim anında açılır.
7. `www` ve kök alan kayıtlarının **kaynak adresi** yeni sunucuya çevrilir.
   Kayıt proxied kaldığı için okurun gördüğü IP değişmez, geçiş TTL beklemeden
   olur. `KURULUM.md` §9/8'deki "TTL 300'e indir" adımı proxied kayıtlarda
   gereksiz; proxied olmayan kayıtlar varsa onlar için kalır. MX ve TXT
   kayıtlarına dokunulmaz.
8. Isıtma: anasayfa, 12 kategori ve en çok okunan 200 adres bir kez istenir.
9. Duman testi (`KURULUM.md` §9/15'e ek): ikinci istekte `cf-cache-status: HIT`
   gelmeli. Var olan bir haber içerik değiştirilmeden yeniden kaydedilir;
   `MISS`/`EXPIRED`'dan sonra `HIT` gelmeli. Uydurma test haberi açılmaz.

**Geri dönüş (≤ 2 dk; `KURULUM.md` §10'u değiştirir)**

1. Önce `www` önbellek kuralları kapatılır. Eski sitenin HTML'i önbelleğe
   girerse, çerez ve oturum davranışı bilinmediği için okurlar arasında karışma
   riski olur.
2. Kaynak adresi eski sunucuya döndürülür.
3. "Purge everything": yeni sitenin HTML'i uçta kalmasın.
4. `BH_CDN=kuru` yapılır. Yeni sistemde girilen haberler §10/3'teki gibi
   listelenir.

---

## 10. Aşamalı yol haritası

| Aşama | Ne | Öncelik | Emek | Maliyet | Eşik |
|---|---|---|---|---|---|
| A0 | Planın koordinatörce kabulü. `URUN-PLANI.md`'ye bölüm. `KURULUM.md` düzeltmeleri (B3, B14; §2 maliyet satırı, §7a, §9/8, §10). | P0 | 0,5 gün | 0 | Ekip içi |
| A1 | Politika ara katmanı + sözleşme testleri (§4.2–4.3, §8.2); isabette başlık saklama + `ETag` (B5, B13); `Vary: Cookie` temizliği (B1) | P0 | 2 gün | 0 | Ekip içi |
| A2 | Okunma işaret ucu + `site.js` + geçiş anahtarı (B2, §6.3) | P0 | 1,5 gün | 0 | Ekip içi (davranış farkı koordinatöre bilgi) |
| A3 | Etiketler, `on_commit`, giden kutusu, `Kuru` ve `Cloudflare` adaptörleri, `/_durum` alanı, panel düğmeleri (§5) | P0 | 2 gün | 0 | Ekip içi; acil temizleme yetkisi K7 |
| A4 | Göreli zaman istemcide (B8); CDN'siz kip için eksik görünümlere uygulama önbelleği (B11); `googleNews` politikası (B12) | P1 | 1 gün | 0 | Ekip içi |
| A5 | Mevcut bölgeyi okuma ve gerçek trafik verisi (K1, K3) | P0 | 0,5 gün | 0 | **Kullanıcı:** erişim |
| A6 | Hazırlık alt alanı, kurallar, S1–S5, `colo` ölçümü; Free'de mi kalınır, Pro'ya mı geçilir? | P1 | 2 gün | 0–25 $ | **Kullanıcı:** DNS kaydı (K4), plan (K2) |
| A7 | KVKK ve BİK hukuk görüşü (K5, K6) | P1 | — | (hukuk) | **Kullanıcı:** yasal |
| A8 | Kesim (F8) CDN adımları ve provalı geri dönüş (§9) | P0 (F8 içinde) | 0,5 gün | 20–25 $/ay (Pro) | **Kullanıcı:** canlı |
| A9 | T+1…T+14: isabet raporu, süre ayarı, saldırı kılavuzu provası (hazırlıkta) | P1 | 1 gün | 0 | Ekip içi |
| A10 | P2 seçenekleri: canlı blog JSON ucu; panel için Cloudflare Access (Zero Trust Free 50 kullanıcıya kadar [K17]); görselleri Bunny İstanbul'a taşıyan karma kurgu; uygulama önbelleğinde etiket bazlı sürüm | P2 | 1–3 gün/kalem | 0–~20 $/ay | Karma kurgu ve Access kullanıcı kararı |

Toplam kod işi (A1–A4): **~6,5 gün**. Aylık bedel: Free'de 0, Pro'da 20–25 $.

---

## 11. Kullanıcının vermesi gereken kararlar

| # | Karar | Seçenekler ve bedel | Önerim |
|---|---|---|---|
| K1 | **Mevcut Cloudflare hesabı kimin?** Erişim kimde? Gazetenin mi, eski sağlayıcının mı? | Bilgi | Hesap gazetenin değilse bölge gazetenin hesabına alınmalı. Bu bir DNS ve canlı işlemidir, ayrı planlanır. |
| K2 | CDN planı | Free 0 $ · **Pro 20 $/ay yıllık, 25 $ aylık** · Business 200–250 $ · Bunny ~13–370 $ · Medianova teklif | Hazırlıkta Free ile başla, kesimde Pro. İstanbul ölçümü kötü çıkarsa Business'a karşı Bunny karma kurgusu yeniden karşılaştırılır. |
| K3 | Gerçek trafik verisine erişim (mevcut bölgenin Cloudflare analitiği ya da GA4) | Bilgi | Senaryoların yerine gerçek sayı (§3.3). |
| K4 | Hazırlık alt alanı açılması (DNS kaydı **ekleme**; mevcut kayıtlara dokunulmaz) | 0 $ | Evet, T−14'te. |
| K5 | KVKK: yurt dışındaki CDN'de okur IP'si işleniyor. Standart sözleşme ve Kurul'a bildirim gerekiyor mu [K36]? Eski site zaten Cloudflare'de; bunun için bir bildirim yapılmış mı? | Hukuk görüşü | → `hukuk-guvenlik-uyum-uzmani`. Yerel seçenek (Medianova) bu soruyu küçültür. |
| K6 | BİK md. 4/9 "CAPTCHA": Cloudflare challenge'ı yeterli sayılır mı? "Deprem trafiğinde herkese challenge yok, yalnız hız sınırını aşana" ilkesi uygun mu? | Hukuk görüşü | İlke uygun; yorum hukukta. |
| K7 | "Acil: tüm siteyi temizle" yetkisi kimde (5651 kaldırma kararları, yanlış yayın)? | Yayın Yönetmeni / Sorumlu Müdür | Yayın Yönetmeni, gerekçe zorunlu. |
| K8 | Uyarı kanalı (giden kutusu takılırsa kime haber gidecek)? | E-posta, mesaj | `KURULUM.md` §11/7 ile aynı soru. |
| K9 | Temizleme yeniden deneme timer'ı (`bh-cdn-temizle.timer`) | Aç / kapalı kalsın | Kesimde aç. Kapalıysa yeniden deneme bir sonraki yayına ve elle komuta kalır. |

---

## 12. Ekip içi devirler

| Ajan | İş |
|---|---|
| `backend-gelistirici` | `sayfa_onbellegi` (etiket, `ETag`, isabet), `sinyaller` (`on_commit`, etiket kümesi), `CdnTemizlik` modeli, `cdn.py`, okunma ucu, B11, B15 |
| `frontend-gelistirici` | `site.js` `sendBeacon`; göreli zaman ve bugünün tarihi istemcide (B8) |
| `devops-altyapi-muhendisi` | `onbellek_politikasi` ara katmanı, `denetimler` kontrolü, nginx ve `ufw` güncellemesi, `KURULUM.md` düzeltmeleri, Cloudflare kuralları, `onbellek-denetle.sh` |
| `test-kalite-muhendisi` | §8.2 sözleşme testleri, §8.3 yük senaryoları, CI'da gizli bilgi taraması |
| `veri-entegrasyon-muhendisi` | Canlı veri yazıldıktan sonra `canli-*` etiket temizliği (`canli-tazele.sh`) |
| `seo-buyume-uzmani` | `googleNews.xml` süresi, `/daha-fazla` `noindex`, `utm` ve `fbclid` ayıklamasının kanonikle tutarlılığı |
| `hukuk-guvenlik-uyum-uzmani` | K5, K6; 5651 kaldırmada temizleme prosedürü |
| `haber-muduru` | K7 prosedürü; okunma sayısının "JavaScript'li okur" tanımına geçmesinin editoryal etkisi |
| `haber-sistemi-uzmani` | Planın `URUN-PLANI.md`'ye işlenmesi, A-aşamalarının sıraya alınması |

---

## 13. Doğrulanmadı ya da bilinmiyor

1. Cloudflare Pro ve Business planlarında Türkiye'den gelen okurun İstanbul'dan
   karşılanıp karşılanmadığı. Ölçülmeden bilinemez (§3.4).
2. Bunny'de Türkiye trafiğinin fatura bölgesi (Avrupa, Asya ya da Orta Doğu) ve
   Türk ağlarından İstanbul PoP'una gerçekten gidilip gidilmediği. Bunny'nin
   `Cache-Control: stale-*` başlıklarına uyup uymadığı.
3. CloudFront sabit planlarında kota aşımında ne olduğu; etiket temizlemelerinin
   sabit planda ücretlenip ücretlenmediği. Kullandıkça öde fiyat tablosu sayfada
   betikle yükleniyor ve okunamadı.
4. Medianova'nın fiyatı, etiketle ya da öneke göre temizleme desteği, SWR/SIE,
   API ve hız sınırları. Teklif isteğinde bu dört başlık sorulmalı.
5. Cloudflare IP Access Rule "Allow"un "I'm Under Attack" ve challenge'ları
   atlayıp atlamadığı. Belgede açık değil [K10][K12].
6. Cloudflare API jetonunda kaynak IP kısıtı.
7. URL yeniden yazmanın önbellek anahtarından önce çalıştığı. Hazırlıkta
   `cf-cache-status` ile doğrulanacak.
8. Cloudflare temizleme süresi "150 ms altı": satıcı iddiası, araştırma
   raporundan aktarıldı.
9. KVKK açısından Kurul'un yayımlanmış bir yeterlilik kararı olup olmadığı [K36].
10. 9 Ekim 2026 tarihli yeni BİK tebliğinin (1 Ocak 2027'de yürürlüğe girecek)
    tam metni. Araştırma raporuna göre bulunamadı. CAPTCHA ve IP maddeleri
    değişmiş olabilir.

---

## 14. Kaynaklar

Hepsi 21 Ekim 2026'da okundu. Parantez içindeki tarih sayfanın kendi "son
güncelleme" tarihidir.

- [K1] Cloudflare, Purge cache: planlara göre temizleme yöntemleri ve sınırları. https://developers.cloudflare.com/cache/how-to/purge-cache/ (29 Eyl 2026)
- [K2] Cloudflare, Purge cache by cache-tags. https://developers.cloudflare.com/cache/how-to/purge-cache/purge-by-tags/ (21 Ağu 2026)
- [K3] Cloudflare, Invalidate cached content (soft purge, ETag ile 304, bayat sunum). https://developers.cloudflare.com/cache/guides/invalidate-cache/ (29 Eyl 2026)
- [K4] Cloudflare, Cache-Control directives (`s-maxage` SWR'i kapatır; Always Online açıkken SWR/SIE yok sayılır; Set-Cookie davranışı). https://developers.cloudflare.com/cache/concepts/cache-control/
- [K5] Cloudflare, Revalidation (eşzamansız SWR; SWR'i kapatan yönergeler). https://developers.cloudflare.com/cache/concepts/revalidation/ (29 Eyl 2026)
- [K6] Cloudflare, CDN-Cache-Control. https://developers.cloudflare.com/cache/concepts/cdn-cache-control/ (16 Nis 2026)
- [K7] Cloudflare, Default cache behavior ("HTML ve JSON varsayılan olarak önbelleklenmez"). https://developers.cloudflare.com/cache/concepts/default-cache-behavior/ (14 Eyl 2026)
- [K8] Cloudflare, Cache Rules (planlara göre kural sayısı) ve Settings (sorgu dizesi anahtarı yalnız Enterprise). https://developers.cloudflare.com/cache/how-to/cache-rules/ · https://developers.cloudflare.com/cache/how-to/cache-rules/settings/ (15 Eki 2026)
- [K9] Cloudflare, Tiered Cache (Smart Tiered Cache her planda). https://developers.cloudflare.com/cache/how-to/tiered-cache/
- [K10] Cloudflare, Under Attack mode. https://developers.cloudflare.com/fundamentals/reference/under-attack-mode/ (20 Nis 2026)
- [K11] Cloudflare, WAF custom rules (Free 5, Pro 20, Business 100 kural). https://developers.cloudflare.com/waf/custom-rules/ (16 Eki 2026)
- [K12] Cloudflare, IP Access rules ("Allow" neleri atlar; her planda 50.000 kural). https://developers.cloudflare.com/waf/tools/ip-access-rules/ (14 Ağu 2026)
- [K13] Cloudflare, Rate limiting rules (Free 1 kural, 10 sn; Pro 2, 1 dk; Business 5). https://developers.cloudflare.com/waf/rate-limiting-rules/
- [K14] Cloudflare, Rules language actions (Managed, Non-Interactive, Interactive Challenge). https://developers.cloudflare.com/ruleset-engine/rules-language/actions/
- [K15] Cloudflare, Authenticated Origin Pulls (her planda). https://developers.cloudflare.com/ssl/origin-configuration/authenticated-origin-pull/
- [K16] Cloudflare, Transform Rules (Free 10 kural) ve `remove_query_args`. https://developers.cloudflare.com/rules/transform/ · https://developers.cloudflare.com/ruleset-engine/rules-language/functions/
- [K17] Cloudflare, Plans (Free 0 $; Pro 20 $ yıllık, 25 $ aylık; Business 200 $ yıllık, 250 $ aylık; "Network Prioritization" yalnız Contract). https://www.cloudflare.com/plans/
- [K18] Cloudflare, "Cloudflare traffic not being sent to the geographically closest data center". https://developers.cloudflare.com/support/troubleshooting/general-troubleshooting/geographic-traffic-routing/ (14 Eki 2026)
- [K19] Cloudflare, Vary. https://developers.cloudflare.com/cache/concepts/vary/ (14 Ağu 2026)
- [K20] Bunny, CDN Pricing. https://bunny.net/pricing/cdn/
- [K21] Bunny, Network (İstanbul PoP). https://bunny.net/network/
- [K22] Bunny, Shield (Basic Free, Advanced 9,5 $, Business 99 $; challenge sayfası). https://bunny.net/shield/
- [K23] Bunny, Purge Cache (`CDN-Tag`, 1.024 bayt; hız sınırları; Perma-Cache'te etiketle temizleme yok). https://bunny.net/docs/cdn/purge-cache.md
- [K24] Bunny, Logging API önbellek durumları (`STALE`, `UPDATING`) ve Smart Cache. https://bunny.net/docs/api-reference/cdn-logging/index · https://bunny.net/docs/cdn/smart-cache.md
- [K25] Fastly, Pricing (Full Site Delivery bant genişliği ve istek ücretleri). https://www.fastly.com/pricing
- [K26] Fastly, POP listesi. https://www.fastly.com/documentation/guides/concepts/pop/
- [K27] Fastly, Working with surrogate keys (16 KB sınırı). https://www.fastly.com/documentation/guides/full-site-delivery/purging/working-with-surrogate-keys/
- [K28] Fastly, Serving stale content (SWR, SIE, soft purge, `Surrogate-Control`). https://www.fastly.com/documentation/guides/full-site-delivery/performance/serving-stale-content/
- [K29] AWS, CloudFront pricing (sabit planlar ve özellik tablosu). https://aws.amazon.com/cloudfront/pricing/
- [K30] AWS, CloudFront features (uç konumları: İstanbul). https://aws.amazon.com/cloudfront/features/
- [K31] AWS, Pay for file invalidation (ayda 1.000 yol bedava; etiketler yol sayılır). https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/PayingForInvalidation.html
- [K32] AWS, Invalidating content by cache tags (nesne başına 50 etiket, 256 karakter). https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/invalidation-by-tags.html
- [K33] AWS, Manage how long content stays in the cache (SWR, SIE). https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/Expiration.html
- [K34] Medianova, ana sayfa ve Network Map (İstanbul, Ankara). https://www.medianova.com/ · https://www.medianova.com/network-map/
- [K35] Erstream (merlincdn.com yönlendirmesi, ölçüldü). https://www.erstream.com/
- [K36] KVKK, Yurtdışına aktarım (6698 m.9 değişikliği 01.06.2024'te yürürlükte; standart sözleşme + Kurul'a bildirim) ve Standart Sözleşmeler. https://www.kvkk.gov.tr/Icerik/2053/Yurtdisina-Aktarim · https://www.kvkk.gov.tr/Icerik/7929/Standart-Sozlesmeler
- [K37] BİK, İnternet Haber Sitelerinin Teknik Olarak Uyması Gereken Kurallara Dair Usul ve Esaslar Hakkında Tebliğ (YK 10.05.2024; md. 4/9 CAPTCHA, md. 5/4, md. 6/3 IP listesi). PDF doğrudan okundu. https://bik.gov.tr/storage/2024/05/Internet-Haber-Sitelerinin-Teknik-Olarak-Uymasi-Gereken-Kurallara-Dair-Usul-ve-Esaslar-Hakkinda-Teblig.pdf
- [K38] RFC 9213, Targeted HTTP Cache Control. https://www.rfc-editor.org/rfc/rfc9213
- [K39] RFC 5861, HTTP Cache-Control Extensions for Stale Content. https://www.rfc-editor.org/rfc/rfc5861
- [K40] nginx, `ngx_http_proxy_module` (`X-Accel-Expires` önceliği, `X-Accel-*` başlıkları okura geçmez). https://nginx.org/en/docs/http/ngx_http_proxy_module.html
- [K41] Django 5.1 sürüm notları, "PostgreSQL Connection Pools". https://docs.djangoproject.com/en/5.2/releases/5.1/
- Depo içi: `reports/Haber sitesi teknoloji seçimi.md` (önbellek/CDN deseni, canlı blog), `research_notes/Haber sitesi teknoloji seçimi/haber_gereksinimleri.md` §3 ve §9.

**Ölçüm komutları** (bu makine, 21 Ekim 2026, istemci `loc=TR`):

- `nslookup -type=NS bursahakimiyet.com.tr`
- `curl -I https://www.bursahakimiyet.com.tr/` ve bir görsel adresi
- `curl https://{www.bursahakimiyet.com.tr,www.cloudflare.com}/cdn-cgi/trace` (6 kez)
- `curl -w "%{time_connect} %{time_appconnect}"` (5'er kez, ortanca)
- Yerel 8731'de 10 okur adresine `curl -D -`, isabet ve ıska süresi, gzip boyu
