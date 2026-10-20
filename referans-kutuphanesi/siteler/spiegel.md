# Der Spiegel

> **Kısmi erişim.** Doğrudan istek yalnız robots.txt'in `Claude-User`'a açtığı
> yollara atıldı (`/ausland/`, `/tests/`). Anasayfa, `/wirtschaft/`,
> `/netzwelt/` ve diğer yollar **açılmadı**; bu başlıklar ikincil kaynakla ya da
> "ölçülmedi" diye yazıldı.

- Adres: https://www.spiegel.de
- Katman: global (Almanya, ulusal haftalık dergi + günlük site)
- Neden seçildi: son başlık rayı, bölüm kademesi, ücretli içerik işareti (SITELER.md §44/§46)
- İnceleme: 2026-10-20 · koşul: masaüstü 1440×900 / mobil 390×844 (DPR 3, mobil öykünme) · konum: **Türkiye** · çerez/rıza katmanı **kabul edilmedi** (ölçümler rıza öncesi)
- Araç: `curl 8.2.1` varsayılan User-Agent; başsız Chrome (UA değiştirilmedi, yalnız görüntü alanı)
- İncelenen sayfalar: `/ausland/` (bölüm), `/ausland/` altında 2 haber detay (ajans kaynaklı, adresinde kişi adı yok), `/tests/` (tüketici/teknoloji servis bölümü)

### Erişim kuralı (robots.txt, 2026-10-20 yeniden okundu)
- `Claude-User`: yalnız `/ausland/ /partnerschaft/ /gesundheit/ /familie/ /reise/ /psychologie/ /stil/ /tests/` açık, gerisi `Disallow: /`. Yorum satırı bunu "deneme amaçlı" açılım diye tanımlıyor — her taramada yeniden okunmalı.
- `ClaudeBot` ve `anthropic-ai`: `Disallow: /`.
- Dosya sonundaki yasal not: izinsiz otomatik erişim yasak, metin-veri madenciliği hakkı saklı. Bu nedenle yalnız açık yollarda kalındı.
([robots.txt](https://www.spiegel.de/robots.txt), 2026-10-20)

## Özet — en öğretici 3 çözüm

1. **Bölüm sayfasında "konu kümesi + kronolojik akış" ikilisi.** `/ausland/` önce 3 konu kümesi (her biri kendi başlığıyla, 1 büyük + birkaç küçük kart), sonra 20 kartlık kronolojik liste ve 500 sayfalık sayfalama. Kümeler editörün gündemi, akış "kaçırdığım var mı" sorusunu cevaplıyor. — BH'ye taşınabilir: **evet**; küme sayısı masa büyüklüğüne göre 1–2'ye inebilir.
2. **Gövde içine gömülü ilgili haber kutusu + sonda okur hata bildirimi.** İlgili haber kutusu gövdenin 6. öğesinden sonra duruyor; sayfa sonunda "redaksiyon hatası bildir" katmanı var. — **evet**, ikisi de küçük emek; hata bildirimi düzeltme notu akışıyla bağlanabilir.
3. **Ajans haberinde kurum imzası + gövde sonunda kısaltma/ajans kodu.** JSON-LD `author` = kurum; gövdenin sonunda editör kısaltması/ajans kodu. Fotoğrafta ayrı "Foto: … / ajans" kredisi. — **evet**; BH'nin "kaynak bölmesi" kararıyla aynı yönde (CLAUDE.md, 23 Ağustos 2026).

## 1. Anasayfa bilgi mimarisi
Ölçülmedi (otomatik erişim yok — anasayfa `Claude-User`'a kapalı). SITELER.md'deki "son başlık rayı / göreli zaman" iddiası **doğrulanmadı**.

## 2. Bölüm sayfası
`/ausland/` ([sayfa](https://www.spiegel.de/ausland/), 2026-10-20; HTML'deki `data-area` sırasından):
- Üstten alta: üst çubuk → ana menü → **son dakika şeridi yuvası** (statik HTML'de boş şablon; JS ile doluyor) → bölüm başlığı + tek satır tanım → **konu hapları** (yatay kaydırmalı, "tümü" + güncel konular) → **konu kümesi 1** (xxl manşet + 2 geniş kart) → **konu kümesi 2** (görüş kartı + xl + 3 orta kart) → **konu kümesi 3** (xxl) → **kronolojik liste** (20 geniş satır kartı) → sayfalama (sayfa 1/500, "daha eski haberler" bağlantısı) → alt bilgi + servis bağlantıları + dergi kaydırıcısı.
- Toplam 29 haber kartı, 31 `h2`. Ray (yan sütun) **yok**; tek sütun, kümeler içinde ızgara.
- Kart anatomisi: Spitzmarke (üst etiket) → başlık → 1–2 cümle özet → alt satırda **mutlak tarih-saat** (gün, ay adı, yıl, saat biçimi) + medya simgesi ve süresi (ör. video 1 dk) → yer imi listesine ekleme düğmesi. Bölüm sayfasında göreli zaman ("X dk önce" tipi) statik HTML'de **yok**; JS sonrası değişip değişmediği ölçülmedi.
- Ücretli içerik kartı, başlık önünde kırmızı "+" simgesiyle işaretli (1440 ekran görüntüsü, `ham/sp-olcum-ausland-1440.png`).

`/tests/` ([sayfa](https://www.spiegel.de/tests/), 2026-10-20) — tüketici teknolojisi/servis bölümü:
- Alt kategori hapları (Elektronik, Haushalt, Fahrrad, Küche, Camping, Garten, Brettspiele…) → "yeni test edilenler" kümesi → **ürün kategorisine göre ~15 konu kümesi** (Gadgets, Kopfhörer, Smartphones, Spiele, Foto, Gaming, Fitness…; her biri 1 büyük + 3–6 küçük kart) → kronolojik "tüm yazılar" listesi (20 kart) + sayfalama.
- Kümelerin içine **"ANZEIGE" etiketli sponsorlu kart** yerleşmiş (iki küme içinde 1'er tane), hedefi grup içi fırsat/indirim alt alanı.
- 135 kart, 1,3 MB açılmış HTML — tek sayfada çok yoğun.

## 3. Haber detay
İki ajans haberi ([haber 1](https://www.spiegel.de/ausland/mallorca-hoechste-sturmwarnung-fuer-baleareninsel-ausgerufen-a-e4318c01-6ad7-4e03-8859-8482b32fde6c), [haber 2](https://www.spiegel.de/ausland/gaza-welternaehrungsprogramm-reduziert-hilfe-um-ein-drittel-a-d06980bf-ada9-4dbb-aa16-fdaa920f4cb1), 2026-10-20). Blok sırası ikisinde aynı:
1. **Giriş:** Spitzmarke → `h1` → spot (1–2 cümle) → tarih-saat → yer imi.
2. **Özellik çubuğu** (yapışkan `aside`, 1440'ta 60 px / 390'da 52 px): yer imi, "makaleyi dinle (N dakika)" düğmesi, paylaşım (X, Facebook, e-posta, Messenger, WhatsApp, bağlantı kopyala).
3. "Google'da SPIEGEL'i tercih et" düğmesi (Google tercih edilen kaynaklar).
4. **YZ özeti kutusu** — bkz. §12.
5. Ana görsel + altyazı + ayrı fotoğraf kredisi (fotoğrafçı / ajans).
6. Gövde; 6. öğeden sonra gövde içine **"konuyla ilgili daha fazlası"** kutusu, sonra gövde devamı.
7. Gövde sonunda **editör kısaltması / ajans kodu** (kısaltma/ajans biçiminde).
8. Makale altı → **smartfeed** (öneri motoru; yanıt gelmezse yedek liste — betikte `RECO` + `fallback` ayrımı görülüyor).
9. **Okur geri bildirim katmanı**: "redaksiyon hatası bildir" + teknik sorun bildirimi.

- **Gövde tipografi** (başsız Chrome, `[data-area="text"] p` hesaplanan stil; karakter/satır = paragraf metni ÷ satır sayısı):
  - 1440: 20 px / 30 px (1,5), serif, sütun 624 px, **~60 karakter/satır**.
  - 390: 18 px / 27 px (1,5), sütun 358 px, **~38 karakter/satır**.
- Kaynak/muhabir: ajans haberinde JSON-LD `author` kişi değil kurum (`Organization`). Muhabirli haber incelenmedi.
- Düzeltme/güncelleme notu: iki örnekte `datePublished = dateModified`; görünür güncelleme notu yok. Düzeltme biçimi ölçülmedi.

## 4. Son dakika / canlı
- Her sayfada üst menünün altında **son dakika şeridi yuvası** (`breaking-bar`, "son dakika" şablonu) var; statik HTML'de boş, içerik JS ile basılıyor. İnceleme anında dolu görülmedi.
- Canlı blog: incelenen yollarda yoktu; ölçülmedi.
- Göreli zaman: bölüm ve detayda mutlak tarih-saat görüldü; anasayfa açılmadığı için §44 iddiası doğrulanmadı.

## 5. Yerel ve servis içerikleri
- Yerel/ilçe sayfası: yok (ulusal yayın; açık yollarda yerel bölüm görülmedi).
- Servis: alt bilgi "services" bloğunda araç/hesaplayıcı bağlantıları (ör. trafik cezası hesaplayıcı, şirket aracı vergi hesaplayıcı) ([/ausland/ alt bilgi](https://www.spiegel.de/ausland/), 2026-10-20). Hava/eczane/ulaşım servisi görülmedi.
- `/tests/` bölümü tüketiciye yönelik "servis gazeteciliği"nin kategori bazlı kümelenmiş hâli (bkz. §2).

## 6. Mobil davranış
- 390 px: başlık çubuğu yapışkan (48 px), haber detayda özellik çubuğu da yapışkan (52 px) — ikisi toplam ~100 px sürekli yer kaplıyor.
- İlk ekranı **rıza katmanı** tam kapatıyor (bkz. §9–10); rıza verilmeden ilk ekran içeriği ölçülemedi.
- Görsellerde kırılım başına ayrı kırpım: aynı fotoğraf masaüstünde 3:2 (r1.5), dar ekranda 4:3 (r1.33) oranında, adreste **odak noktası** parametresiyle (fpx/fpy) — sanat yönetimi sunucuda. Gerçek boyut `width/height` nitelikleriyle bildiriliyor (CLS ≈ 0).

## 7. Başarım
Başsız Chrome, önbellek kapalı, gezinmeden sonra 25 sn dinleme, **rıza verilmeden** (reklam/izleme betiklerinin çoğu yüklenmemiş durum — gerçek okur yükü daha yüksek olabilir, ölçülmedi). Türkiye'den.

| Sayfa | Genişlik | LCP | CLS | İstek | Aktarılan | TTFB |
|---|---|---|---|---|---|---|
| /ausland/ | 1440 | 708 ms | 0,004 | 58 | 1,43 MB | 308 ms |
| /ausland/ | 390 | 812 ms | 0 | 58 | 1,45 MB | 304 ms |
| haber 1 | 1440 | 1308 ms | 0,004 | 54 | 1,52 MB | 411 ms |
| haber 1 | 390 | 476 ms | 0 | 54 | 1,55 MB | 287 ms |
| haber 2 | 1440 | 736 ms | 0,004 | 57 | 1,47 MB | 284 ms |
| haber 2 | 390 | 564 ms | 0 | 54 | 1,49 MB | 265 ms |

- HTML (`curl --compressed`, `%{size_download}`): /ausland/ 112.460 B sıkıştırılmış / 667.708 B açılmış; haber 1 116.549 / 546.450; haber 2 118.797 / 561.091; /tests/ 159.106 / 1.299.610.
- 22 `<script>` etiketi, 5'i dış dosya; istekler 7 alan adına dağılıyor (görsel CDN 20, rıza sağlayıcı 10, ölçüm 6…).
- Görseller: `/ausland/`'da 153 `img` (noscript yedekleri dahil), 73 `loading="lazy"`; görünmeyenler `data-src` ile JS'le yükleniyor, `noscript` içinde yedek var.
- LCP öğesi her ölçümde manşet görseli.

## 8. SEO yapısı
- JSON-LD: bölüm sayfasında `WebPage` + `Organization` + `BreadcrumbList`; haber detayda `NewsArticle` (+ `ImageObject`, `BreadcrumbList`). `NewsArticle` alanları: `articleSection`, `author` (Organization), `dateCreated/datePublished/dateModified`, `isAccessibleForFree` (ücretsiz haberde `true`), `keywords`, `mainEntityOfPage`, `thumbnailUrl`.
- Kanonik: kendine işaret ediyor. `robots` meta: `max-image-preview:large`, `max-snippet:-1`, `noarchive`.
- AMP: `amphtml` bağlantısı **yok**.
- Sitemap: robots.txt'te ayrı **haber sitemap'i** (`/sitemaps/news-de.xml`), video sitemap'i, SPIEGEL+ sitemap'i ve genel sitemap ilan edilmiş ([robots.txt](https://www.spiegel.de/robots.txt), 2026-10-20). Sitemap dosyaları açılmadı.
- Adres deseni: `/<bölüm>/<slug>-a-<uuid>`.

## 9. Reklam
- `/ausland/` HTML'inde 72 `data-advertisement` işaretli öğe (yuva/yer tutucu). Rıza verilmediği için reklam doldurulmadı; yerleşim ve ilk ekran yuva sayısı **ölçülmedi**.
- `/tests/` kümelerinde içerik kartı biçiminde "reklam" etiketli sponsorlu kart (bkz. §2).
- Rıza katmanı **"pay or consent"** biçiminde: "reklam ve izlemeyle devam" ya da "ücretli, reklamsız oku" seçenekleri yan yana; Türkiye'den İngilizce gösterildi (ekran görüntüsü `ham/sp-olcum-ausland-1440.png`, 2026-10-20).

## 10. Gelir ve okur ilişkisi
- **SPIEGEL+**: ücretli içerik; kartta "+" simgesi, menüde ayrı giriş. Ücretli haber gövdesi okunmadı (kural).
- Eşzamanlı kullanım tek cihazla sınırlı (sayfadaki oturum katmanı metni).
- **Yer imi listesi** her kartta; hesap/giriş katmanına bağlı.
- Bülten, bildirim: ölçülmedi. Yorum: incelenen haberlerde yorum alanı görülmedi.

## 11. Erişilebilirlik
- `lang="de"`.
- **Atla bağlantısı** var ("İçeriğe atla", `#Inhalt`); normalde gizli, odaklanınca görünür hale gelen sınıflarla.
- Kart görsellerinde `alt` boş, açıklama `title` niteliğinde — ekran okuyucu için kart başlığı `article aria-label` ile veriliyor.
- Simgeler `aria-hidden="true"`. Odak stili sınıflarla tanımlı (`focus:` önekleri); görsel odak halkası ölçülmedi.
- Kontrast: ölçülmedi.

## 12. Yapay zekâ kullanımı
- **YZ özeti kutusu** (haber detay, başlık bloğunun altında): varsayılan **kapalı**, tıklayınca açılıyor; içerik istemci tarafında sonradan yükleniyor; altında "otomatik olarak YZ ile oluşturuldu" notu + açıklama sayfası bağlantısı + "yararlı mıydı" olumlu/olumsuz oylaması ([haber 1](https://www.spiegel.de/ausland/mallorca-hoechste-sturmwarnung-fuer-baleareninsel-ausgerufen-a-e4318c01-6ad7-4e03-8859-8482b32fde6c), 2026-10-20).
  - **BH için: okura "yapay zekâ destekli" etiketi reddedildi (kullanıcı kararı).** Desen yalnız kayıt için.
- **Sesli dinleme**: "makaleyi dinle (N dakika)" düğmesi, süre gösteriyor. Ses üretim yöntemi (sunucu TTS / insan / tarayıcı) doğrulanmadı. **BH için: tarayıcı sesi (Web Speech) reddedildi; seslendirme yönü yerel model.**
- **Öneri**: smartfeed öneri motoru + yedek liste (bkz. §3).

## Teknik not (desen değil, kayıt)
- Sayfa sunucuda render ediliyor; etkileşim `x-data`/`x-show`/`x-cloak` sözdizimli hafif bir katmanla (Alpine.js sözdizimine benziyor — kütüphane kimliği doğrulanmadı). Sınıflar yardımcı-sınıf (utility) düzeninde. **BH için: Tailwind/React/bundler reddedildi**; "sunucu render + küçük etkileşim katmanı" ilkesi BH mimarisiyle zaten aynı.

## Ölçüm dökümü
| ölçü | değer | yöntem |
|---|---|---|
| HTML /ausland/ | 112.460 B (sıkıştırılmış) / 667.708 B | `curl --compressed -w %{size_download}` + dosya boyutu |
| HTML haber | 116.549–118.797 B / 546–561 KB | aynı |
| HTML /tests/ | 159.106 B / 1.299.610 B | aynı |
| LCP /ausland/ | 708 ms (1440) · 812 ms (390) | başsız Chrome `PerformanceObserver` LCP, rıza öncesi |
| LCP haber | 476–1308 ms | aynı |
| CLS | 0–0,004 | `layout-shift` toplamı (girdi sonrası hariç) |
| İstek | 54–58 | DevTools `Network.requestWillBeSent`, 25 sn |
| Aktarılan | 1,43–1,55 MB | `Network.loadingFinished.encodedDataLength` toplamı |
| Gövde punto | 20/30 px (1440) · 18/27 px (390) | `getComputedStyle` |
| Karakter/satır | ~60 (1440) · ~38 (390) | metin uzunluğu ÷ (yükseklik ÷ satır aralığı) |
| JSON-LD | NewsArticle, BreadcrumbList, ImageObject, Organization | `application/ld+json` ayrıştırma |
| Kart sayısı /ausland/ | 29 | `data-area="article_teaser>…"` |
| Atla bağlantısı | var | HTML |

İstek sayısı (www.spiegel.de, sayfa düzeyi): robots.txt 1 + `curl` 4 + Chrome sayfa yüklemesi 6 = **11**. Chrome yüklemelerinin alt kaynakları cdn.prod.www.spiegel.de, sp-spiegel-de.spiegel.de, sams.spiegel.de, assets.adobedtm.com ve birkaç alan adına gitti.
