# Proje değerlendirmesi — 19 Ekim 2026

On rol ajanı (`EKIP.md`) projeyi aynı gün, birbirinden bağımsız olarak değerlendirdi:
haber müdürü · full stack · frontend · backend · yapay zekâ · veri-entegrasyon ·
SEO-büyüme · DevOps · hukuk-güvenlik-uyum · test-kalite.

Hepsi **salt okunur** çalıştı: depo, veritabanı ve zamanlanmış görevler değişmedi.
Veritabanı `mode=ro` ile okundu. Ölçümler başsız Chrome, Django test istemcisi ve
SQL planlarıyla alındı. Aşağıdaki her sayı bir ölçümden ya da dosya satırından
geliyor; doğrulanamayanlar ayrıca işaretli.

**Ürünün amacı (kullanıcı, 19 Ekim):** Bursa özelinde ve kısmen ulusala hitap
eden, klasik haber sitesi temasında, yapay zekâ ve modern teknolojiden
faydalanan bir haber sitesi. Tasarım dili kırmızı · lacivert · beyaz; Bursaspor
yeşil-beyaz; seçili sayfalarda sayfaya özel tasarım.

---

## 1. Tek paragrafta

Temel sağlam. 1.038.474 haber göç edildi, yetim kayıt sıfır. 556.824 eski adres
korunuyor, yanlış slug tek adımda 301 ile kanonik adrese gidiyor. 879 test hem
sırayla hem rastgele sırayla, ağ kapalıyken de geçiyor. Hiçbir sayfada, hiçbir
genişlikte yatay taşma yok. Gövde temizleyici 16 saldırı yükünün hepsini
durdurdu ve yetki matrisi sunucuda gerçekten uygulanıyor.

Ama ürün **canlıya çıkmaya hazır değil.** Engel tasarım değil; şu dört alan:

- **Altyapı:** yedek yok, izleme yok, PostgreSQL göçü başlamadı.
- **Masanın kontrolü:** manşet ve son dakika kararları siteye ulaşmıyor; muhabir
  yayın kapısını aşabiliyor.
- **Veri akışı:** arşiv 6 Eylül'de duruyor, canlı site ~11 bin haber önde ve
  kimlikler çakışmaya başladı.
- **Yasal zorunluluklar:** künye, cevap hakkı, KVKK metinleri ve sürüm
  geçmişi eksik.

Bunların çoğu küçük ya da orta iş. Ortak bir yol haritasıyla kapanabilirler (§5).

---

## 2. Bugüne kadar iyi gidenler

- **Adres sözleşmesi:** 556.824/556.824 adres çözülüyor. Yanlış slug 301 alıyor,
  olmayan kimlik gerçek 404 alıyor. Beş sitemap ailesi var ve dosya adları canlı
  siteyle birebir aynı. `googleNews.xml` 48 saat kuralına uyuyor.
- **Veri modeli:** 10 bütünlük denetiminin hepsinde yetim kayıt 0.
  `makemigrations --check` temiz. Kısıtlar bilinçli kurulmuş (`PROTECT`/`SET_NULL`,
  tekillik, kısmi manşet indeksleri). Anasayfa, haber detay ve ilçe sorguları
  1 ms'nin altında.
- **Panel → site zinciri:** panelden girilen haber 11 adresin hepsinde görünüyor:
  detay, anasayfa, bölüm, ilçe, son haberler, RSS, googleNews, aylık sitemap,
  arama ve sosyal kuyruk.
- **Güvenlik temeli:**
  - Muhabir 11 yasak ekranda 403 alıyor, yönetmen 19 ekranın 19'unu açıyor.
  - CSRF muafiyeti yok, ham SQL yok, dosya yükleme ucu yok.
  - Herkese açık depoda ve 25 commit'lik geçmişte gizli anahtar bulunmadı.
- **Ön yüz disiplini:**
  - Taşma 9 sayfa × 7 genişlikte 0. CLS 0. Metin kontrastında AA'nın altında öğe yok.
  - Hex renk yasağı testle korunuyor.
  - `site.js` gzip ile 8,5 KB ve framework yok.
- **Canlı veri tasarımı:** betik yazıyor, site okuyor. Yedek kaynak zinciri var.
  10 Eylül'deki DNS kesintisinde düşme davranışı gerçekten çalıştı.
- **Editoryal kurallar koda bağlı:**
  - Kural motoru gövde yazmıyor.
  - Yapay zekâ taslağı Pasif doğuyor; `[yazılacak]` işareti yayın kapısında takılıyor.
  - Konu takibinde onaysız dosya sitede 404 veriyor.
  - Hassas dosyalara masumiyet uyarısı otomatik düşüyor.
- **Hukuki dikkat:** ilan.gov.tr kazıması kullanım koşulları gerekçesiyle
  reddedildi, afiş telifi FSEK m.37'ye göre incelendi, `Yorum` ve `LogKaydi`
  IP verisi yüzünden taşınmadı.

---

## 3. En kritik on bulgu

Birden çok ajanın bağımsız olarak vardığı bulgular önde.

| # | Bulgu | Kanıt | Bulan |
|---|---|---|---|
| 1 | **Yedek yok.** 3,7 GB veritabanının ve 155 GB arşiv görselinin tek kopyası bu dizüstünde. Eski görseller kaynak sunucudan silindiği için bu kopya kaybolursa geri gelmez | `db.sqlite3` 3.697.836.032 bayt; `D:\bursa-hakimiyet-arsiv\gorseller` 499.480 dosya / 147 GB; başka kopya bulunamadı | DevOps, backend |
| 2 | **Kimlik çakışması başladı.** Panel yeni haberin kimliğini "en büyük + 1" diye veriyor ve bu kural üç ayrı yerde yazılı. Bizim 1696272–74 kimliklerimiz canlıda zaten başka haberler. Taze içe alma yapılırsa ya haber sessizce kaybolur ya da panel kaydı ezilip melez bir kayıt doğar | `panel.py:569`, `yz_kopru.py:402`, `eczane_haberi.py:130`; canlıda `-1696274` = "Cem Küçük soruşturması" | veri, full stack, test, backend |
| 3 | **Taze haber akışı yok.** Canlıdan alınan son haber 25 Ağustos'ta yayımlanmış, veritabanına son yazım 6 Eylül'de. Canlı site o tarihten beri ~11 bin haber bastı (Ekim'in ilk 19 gününde 3.899) | sitemap sayımı; veritabanı sorgusu | veri, haber müdürü, SEO, full stack |
| 4 | **Muhabir haberi doğrudan yayına alabiliyor.** "Haber ekle" yolunda yayın yetkisi denetlenmiyor ve form varsayılan olarak "Aktif" açılıyor. Toplu "Yayına al" `[yazılacak]` işaretini ve boş slug'ı denetlemiyor; sonuç `/bursa/-1696500` adresinde 404. İleri tarihli haber hemen yayına çıkıyor | `panel.py:503-517`, `:1297`; `models.py:261-269`; üçü de geçici testle doğrulandı | haber müdürü, test, full stack, backend |
| 5 | **Masanın kararları siteye ulaşmıyor.** Manşet bayrakları sitede 0 kez okunuyor; anasayfa son 15 haberi tarih sırasıyla basıyor. Son dakika bandı `SonDakika` tablosunu değil son 7 haberi gösteriyor. Reklam yuvası ve kampanya kayıtları da okunmuyor | `views.py:158-181`, `baglam.py:104` | haber müdürü, full stack |
| 6 | **Güvenlik açıkları:** (a) ayarlar ortam değişkeni yoksa `DEBUG=1`'e ve depodaki sabit anahtara düşüyor; (b) adresten taslakta SSRF: iç ağ ve 169.254.x açık, boyut sınırı yok; (c) görsel indirme `.svg`/`.html` dosyası bırakıp site kökeninde çalıştırabiliyor; (d) `arac/yayinci.py` `CORS *` ile her web sitesinden tetiklenebiliyor; (e) nöbetçi eczane JSON-LD'sinde betik enjeksiyonu (doğrulandı); (f) giriş denemesi sınırı ve 2FA yok; (g) denetim günlüğüne yazan kod yok (0 satır) | `settings.py:27-31`; `ayiklayici.getir`; `gorsel_indir`; `nobetci_eczane.html:82`; `LogKaydi` | hukuk-güvenlik, test, DevOps |
| 7 | **Yasal zorunluluklar eksik (5187, 7418 sonrası):** ana sayfadan ulaşılabilen künye/iletişim (3 Eylül'de kaldırılmış); sabit ilk yayın tarihi ve güncelleme damgaları; iki yıl saklama için sürüm geçmişi; cevap ve düzeltme süreci; KVKK aydınlatma ve çerez metinleri. Ayrıca GitHub Pages, gazeteye ait olmayan fotoğrafları ve tam haber metinlerini şu an yayımlıyor | `parca/kunye.html`; `gorseller/kaynak/` HTTP 200; `arac/cikti/*.json` | hukuk-güvenlik |
| 8 | **SEO'da kesimde gerileme olur.** Hiçbir sayfada OG, Twitter kartı, `max-image-preview:large` ya da NewsArticle/BreadcrumbList/WebSite JSON-LD yok; canlıda hepsi var. Canlıdaki her haberin AMP ikizi (`/amp/...`) bizde 404. 1.038.222 haberin görsel alt metni "Google News" ve bu yazı okura foto altı olarak da görünüyor. Kanonik adres istek konağından kuruluyor | `taban.html`; `haber_detay.html:44` | SEO, yapay zekâ, frontend |
| 9 | **Başarım üç yerde çöküyor:** arama sonuçsuz sorguda 2,8–31 sn (bir işçiyi kilitliyor, DoS yüzeyi); her sayfanın menüsündeki sayım 6–44 sn ve kilitsiz; panel "Bugün" ekranı 7,2 sn. Anasayfa telefonda 7 MB, masaüstünde 9,2 MB görsel indiriyor: küçük kartlara 1280 px görsel gidiyor ve ilk ekran görselleri tembel yükleniyor. Sıkıştırma ve `Cache-Control` yok | `views.py:942`; `baglam.py:188`; `panel.py:334`; `parca/kart.html:46` | backend, frontend |
| 10 | **Zamanlayıcı 37 gündür sessizce duruyor ve bayat veri canlı gibi görünüyor.** Dört görev de kapalı. Tanımlar üretime uygun değil: yalnız oturum açıkken ve prizdeyken çalışıyor, kaçan koşu telafi edilmiyor. Eczane haberi görevi bir kez bile kendiliğinden haber açmadı. Namaz paneli 12 Eylül vakitlerini "ŞİMDİ" diye, haftanın maçı 13 Eylül maçını "bekliyor" diye gösteriyor | görev tanımları; `canli.py:91` | veri, DevOps, full stack |

---

## 4. Alan alan özet

### Haber müdürü
- **"Önce Bursa" ilkesinin kodda karşılığı yok.**
  - Anasayfa havuzundaki 49 kaydın yalnız 10'u Bursa ya da Bursaspor.
  - Bugünkü ana manşet bir Fenerbahçe haberi.
  - Haziran–Eylül üretiminin %26'sı Bursa'yla ilgili.
- **"Yayına hazır" haber masa ekranında görünmüyor.** Bugün ekranı yalnız Taslak
  ve İncelemede listeliyor.
- **Kaynak kuralı yayın kapısında aranmıyor.** 2026'daki 51.621 haberin 14.511'inde
  kaynak yok.
- **İmza satırı sabit "Haber Merkezi".** Muhabir, ajans ve Meta Yazar Bilgisi
  okura yansımıyor.
- **"Arşiv fotoğrafı silinmiş" notu yanlış yerde.** Fotoğrafsız her habere, yeni
  haberlere de basılıyor.
- **Okurla kanal yok.** Yorum, bülten ve ihbar yok; bildirim açılma oranı %0,21.

### Full stack
- Panel formundaki 27 alanın ~13'ü sitede okunmuyor. Örnekler: ikinci başlık,
  etiketler, muhabir, kaynak türü, SEO başlığı, gömülü kod.
- Görsel yükleme yok, panelden girilen haber fotoğrafsız kalıyor. Instagram
  paylaşımı görsel zorunlu tuttuğu için hep düşüyor. Karar 28 Ağustos'tan beri bekliyor.
- Düz metin gövde tek paragraf basılıyor (`govde_temizle`).
- **Bursaspor işi yarım commit'e açık.** `views.py`, takip edilmeyen
  `bursaspor.py`yi içe aktarıyor; yalnız değişen dosyalar commit edilirse tüm
  site `ImportError` verir.
- `panel.py` 3.157 satır; `bursaspor.py` ile `canli.py` arasında yinelenen
  kod ve ölü alanlar var.

### Frontend
- **Görsel ağırlığı kritik.** Yalnız `_large` türev var, hiçbir şablonda
  `srcset`/`sizes` yok. LCP görseli `loading="lazy"`.
- **Odak halkası kontrastı yetersiz** (WCAG 2.4.11). Kırmızı halka lacivert
  üstünde 2,87:1, Bursaspor'da 1,48:1. Doğru desen dosyada zaten var:
  `.sondakika-serit` beyaz halka kullanıyor.
- **`site.css` 197 KB'ın %46'sı yorum.** Gzip'li boyut bu yüzden 58 KB; yorumlar
  olmasa 19,5 KB olurdu. Dosya tur tur katmanlanmış: aynı seçici 4 yerde, 20
  farklı kırılma eşiği var.
- **Bursaspor teması ölçeklenmiyor.** 39 ayrı geçersiz kılmayla kurulmuş.
  `tests_bolum_bloklari.py:338-371` ikinci bir temaya izin vermiyor; yeni tasarım
  kararıyla birlikte güncellenmeli (§6).
- Slaytta duraklatma düğmesi yok (WCAG 2.2.2). Düğme 29 Ağustos'ta kaldırılmıştı.
- Panelde aynı adlı değişkenler farklı değerler taşıyor (`--kirmizi` #D51C24 ve #E4222B).

### Backend
- **PostgreSQL göçü yapılmalı.** Önerilen sıra: akışla, `id` sırasıyla aktarım →
  satır sayımı ve md5 örneklemi → 10 bin adreslik 200/301 denetimi → `ANALYZE`.
  `DATABASES` bugün SQLite'a sabit; önce ortamdan seçilebilir olmalı.
- **Arama:** önce normalize edilmiş arama alanı, sonra `to_tsvector` + GIN +
  önek; panel için `pg_trgm`. Hedef p95 ≤ 300 ms.
- **Önbellek** modül düzeyindeki global değişkenlerde duruyor: süreçler arasında
  paylaşılmıyor, kilidi yok. Paylaşılan bir önbellek (Redis ya da veritabanı) gerekli.
- **Okunma sayacı** okuma yolunda yazıyor (`okunma.py:151-191`); boşaltma
  zamanlanmış göreve alınmalı.
- Site haritası indeksi 385 sorgu ve 3,6 sn; panel kuyruğu için kısmi indeks
  bu süreyi 3.124 ms'den 0,3 ms'ye indiriyor.

### Yapay zekâ
- **Bugün çalışan yapay zekâ kural tabanlı.** Konu motorunda 19.966 onaylı dosya
  ve 133.543 bağ var. Model yoluyla ürüne yalnız 3 taslak girmiş.
- **Kullanıcının reddettiği periyodik türler sitede onaylı dosya olarak duruyor:**
  borsa açılışı (300 haber), "tarihte bugün" (160), Brent, Loto, BUSKİ kesintisi,
  fiyat endeksleri. Şüpheli dosya sayısı 210. Hiçbir dosyayı bir editör
  onaylamamış; onayların hepsi 5 Eylül'de eşik komutuyla verilmiş.
- **`cli` yolu üretimde kullanılamaz.** Anthropic koşullarına göre abonelik
  girişi bireysel kullanım içindir. Ayrıca `--model` verilmediği için hangi
  modelin yazdığı bilinmiyor, ve araç kısıtı olmadığı için kazınmış metin istem
  enjeksiyonu yüzeyi oluyor.
- **Model taslağı neredeyse aynen yayımlanmış:** benzerlik 0,999.
  Uydurma olgu denetimi (K2) hâlâ elle yapılıyor.
- **Sitedeki seslendirme hâlâ reddedilen tarayıcı sesiyle çalışıyor** ve adres
  `#seslendirme` ile açılınca kendiliğinden başlıyor. Chatterbox denemesi bu
  makinenin GPU'suyla (RTX 3050, 4 GB) masrafsız yapılabilir.
- **İlçe kapsaması düşük:** 2026'daki 51.612 haberin yalnız 5.926'sında ilçe dolu.

### Veri ve entegrasyon
- **İçe alma hattı (`taze_al`) yok.** Kurulacak hat: sitemap `(id, lastmod)` farkı
  → yeni ve düzeltilmiş kayıtların çekilmesi → panelde düzenlenmiş kayda
  dokunmayan upsert → canlıdan kaldırılan haberin bizde pasife alınması.
  Bugünkü `site_arsivleyici` düzeltilen ve kaldırılan haberi yakalamıyor.
- **Vizyon kaynağı sessizce bozuldu.** Başka Sinema 6 Eylül'den beri 0 film
  döndürüyor (site yeniden tasarlanmış), ama durum dosyası "taze" diyor. Kaynak
  başına asgari kayıt eşiği gerekli.
- **Fikstür taşıması sezon kontrolü yapmıyor;** maç günü saatlik koşu da yok.
- Ajans akışının (AA, İHA, DHA) içe alınması kesimden sonra şart: son göç
  partisinde içeriğin %52'si ajanstı.

### SEO ve büyüme
- **Kesimden önce şart olanlar:** meta bloğu ve JSON-LD; `/amp/*` → 301;
  kanonik adresin `SITE_KOKU`dan kurulması; alt metin temizliği; `og:image` için
  1200×630 türev; analitik.
- **Google News'e yeni kayıt gerekmiyor.** Mart 2025'ten beri yayın sayfaları
  otomatik oluşuyor; alan adı aynı kaldığı için Search Console'da adres
  değişikliği de gerekmiyor.
- **İnce içerik riski:** 19.966 konu sayfasının 11.559'unda yalnız 3–4 haber var
  ve hepsi dizine açık. Az haberli olanlara `noindex` önerildi.
- **Kopacak kanallar:** canlıdaki GA4 mülkü (`G-4RVSYL5WQM`) ve 22.683 kişilik
  push kitlesi eski sağlayıcının Firebase projesine bağlı.
- **Büyüme:** sabah bülteni ve WhatsApp kanalı (künyede zaten planlı).

### DevOps
- **Önerilen üretim düzeni:**
  - nginx → gunicorn (systemd), görseller nginx'ten `X-Accel-Redirect` ile.
  - Anonim HTML için 5–30 sn'lik mikro önbellek.
  - Önde Cloudflare.
  - Yedek: gece `pg_dump`, görsellerin artımlı kopyası, **ayda bir geri yükleme provası**.
- **Sunucu boyutu:** 4 vCPU / 16 GB / ≥ 400 GB NVMe. Kaba maliyet: Türkiye
  VDS'de ayda ~500–1.500 TL; site dışı yedek ~2,5 $/ay (R2); Cloudflare Free 0 $.
- **Eksikler:** CI yok, `main` korumasız, `requirements.txt` yok (`tzdata`
  gizli bir bağımlılık).
- **Depo şişiyor:** sitemap klasörü (388 dosya, ~240 MB) git'te izleniyor.
- Kesim günü adım listesi ve geri dönüş planı raporda yazılı; geri dönüş için
  eski barındırma en az 14 gün açık kalmalı.

### Hukuk, güvenlik ve uyum
- §3'teki 6. ve 7. bulgular. Bunlara ek olarak:
  - **Google Fonts** her ziyaretçinin IP adresini Google'a gönderiyor; KVKK md.9
    kapsamında yurt dışı aktarım sayılabilir (avukat teyidi gerekir). Fontlar
    yerelden sunulursa sorun kalkar.
  - **Yapay zekâ izi:** yayımlanan haberde yapay zekâ desteğini gösteren kalıcı
    bir işaret yok. Yürürlükte bir yapay zekâ kanunu bulunamadı, ama 2025'teki
    kanun teklifleri etiketleme öngörüyor.
  - **BİK:** Aralık 2025 yönetmelik değişikliğinin CMS değişikliğine etkisi belirsiz.
- Avukat teyidi isteyen kalemler tek bir hukuki teyit paketinde toplanmalı.

### Test ve kalite
- **Paket hermetik:** rastgele sırayla ve ağ kapalıyken 879/879 geçti, dış
  bağlantı denemesi 0.
- **Testsiz alanlar:** 18 yönetim komutunun 10'u (1 milyon satıra yazan onarım
  komutları dahil) ve `canli-veri` ayrıştırıcıları (4.170 satır).
- **Ölçüm aracı 7. kez yanılttı.** Sitede odak ölçümü `el.focus()` ile yapıldığı
  için "halkasız" görünüyordu; gerçek Tab tuşuyla halkasız öğe 0.
- **Kırılgan bağımlılık:** testler gerçek `canli-veri/veri/*.json` dosyalarını
  okuyor. Bu klasör git'te olmadığı için temiz klonda ya da CI'da sonuç değişir.
- RSS, spottaki tek bir `\x1d` karakteriyle 500 veriyor.
- **PostgreSQL'e geçiş riskleri:** `icontains` İ/ı davranışı değişecek; eşit
  zamanlı haberlerde sıra belirsiz.

---

## 5. Yol haritası

Aşamalar sırayla, aşama içindeki işler paralel yürür. Emek: S küçük, M orta, L büyük.

### Aşama 0 — Hemen (bu hafta; kullanıcı onayıyla)
| İş | Sahip | Emek |
|---|---|---|
| Harici diske soğuk yedek: veritabanı (`.backup`) + `D:\bursa-hakimiyet-arsiv`; geri yükleyip sayımla doğrula | DevOps | S (+ ≥ 500 GB disk) |
| Bursaspor işini **tek ve bütün** bir commit olarak al (12 dosya + `EKIP.md` + ajanlar) | full stack | S |
| Zamanlayıcı kararı: görevler bu makinede yeniden açılsın mı? Açılacaksa koşullar düzeltilsin (oturumsuz çalışma, pil, kaçan koşunun telafisi) | veri + DevOps | S |

### Aşama 1 — Bütünlük ve güvenlik (ekip içinde, küçük işler)
| İş | Sahip | Emek |
|---|---|---|
| Tek `yeni_kimlik()`; canlıyla çakışmayan bir aralık (ör. ≥ 5.000.000) ve `force_insert`; 1696272–74'ün taşınması (geri alınamaz → kullanıcı) | backend + veri | S–M |
| Tek yayın kapısı: form, toplu fiil ve yapay zekâ taslağı aynı işlevden geçsin (yetki + işaret + slug + kaynak); yeni haberin varsayılanı Pasif; `yayin_zamani <= şimdi` | backend + full stack | S |
| Ayarlarda fail-closed: anahtar yoksa uygulama açılmasın, `DEBUG` varsayılanı 0; HSTS, SSL yönlendirmesi, güvenli çerezler, CSP | DevOps + backend | S |
| SSRF kapısı (IP denetimi, yönlendirme başına yeniden denetim, boyut sınırı); görsel indirmede yalnız raster türler; `yayinci.py` CORS ve Host denetimi; `claude -p` araçsız ve `--model claude-opus-5` ile | backend + yapay zekâ | M |
| JSON-LD'yi `json_script` ile basmak, `|safe` enjeksiyon testleri; RSS'te XML'de geçersiz karakter temizliği | frontend + test | S |
| Giriş denemesi sınırı, boşta oturum düşmesi; `LogKaydi`'nin giriş, yayın ve toplu işlemlerde yazılması | backend | M |
| URL çözücüden türetilen yetki testi (her kalıp × 5 rol × GET/POST) | test | M |

### Aşama 2 — Masa siteyi yönetsin
| İş | Sahip | Emek |
|---|---|---|
| Manşet bayraklarının anasayfaya bağlanması, bayrak yoksa "önce Bursa" düşüş kuralı | full stack + frontend | M |
| Son dakika bandının `SonDakika` tablosundan beslenmesi | full stack | S |
| Bugün ekranına "Yayına hazır" kuyruğu; panel kuyruğuna kısmi indeks | backend | S |
| İmza satırının muhabir/ajans/meta yazardan gelmesi; fotoğraf notunun yalnız arşiv haberine basılması | frontend | S |
| Konu temizliği: `RUTIN_KALIPLARI` genişletilsin, 210 şüpheli dosya panelde tek tek ret için listelensin, "sürüyor" bilgisi okuma anında hesaplansın | yapay zekâ + haber müdürü | M |
| Bayatlık gösterimi: namazda bugünün satırı, maç ve vizyona işaret, döviz bandına tarih; kaynak başına asgari kayıt eşiği | veri + frontend | S |

### Aşama 3 — Altyapı ve başarım
| İş | Sahip | Emek |
|---|---|---|
| `requirements.txt` (+ gunicorn, tzdata), CI (GitHub Actions, Ubuntu), `main`e dal koruması | DevOps + test | M |
| `DATABASES` ortamdan seçilsin → PostgreSQL göç betiği + iki zamanlı prova + doğrulama sayıları | backend | L |
| Arama indeksi (GIN + önek, `pg_trgm`); menüden canlı `Count`'un kaldırılması; paylaşılan önbellek; okunma sayacının okuma yolundan çıkarılması | backend | M |
| Görsel türevleri (360/640/960/1280) + `srcset` + `width/height`; LCP görselinin hemen yüklenmesi; gzip/Brotli + `Cache-Control` + sürümlü statik dosyalar | backend + frontend + DevOps | L |
| Odak halkası kontrastı; ölü değişkenler; yorumların dağıtımda ayıklanması | frontend | S |
| Zamanlayıcının platformdan bağımsız koşucuya, üretimde systemd timer'a taşınması; `/_durum` sağlık ucu ve dış yoklama | veri + DevOps | M |

### Aşama 4 — Uyum ve SEO eşitliği (kesim öncesi şart)
| İş | Sahip | Emek |
|---|---|---|
| `/iletisim` ve `/kunye` sayfaları, ana sayfadan bağlantı (gerçek bilgiler gazeteden) | frontend + haber müdürü | S |
| Sabit ilk yayın tarihi, kendiliğinden yazılan güncelleme damgası, sürüm geçmişi (2 yıl) | backend | M |
| Cevap/düzeltme modeli, haber sayfası bloğu, ana sayfada 24 saat; içerik kaldırma prosedürü | full stack + haber müdürü | M |
| KVKK aydınlatma, gizlilik ve çerez metinleri (avukat); fontların yerelden sunulması | hukuk + frontend | M |
| Meta bloğu + JSON-LD (NewsArticle, BreadcrumbList, WebSite, Organization); `/amp/*` → 301; kanonik adres `SITE_KOKU`dan | frontend + backend + SEO | M |
| "Google News" alt metninin temizliği (1 milyon kayıt, geri alınamaz → kullanıcı); `og:image` 1200×630 | backend | S–M |
| Analitik (mevcut GA4 mülkü + izin bandı) | SEO + hukuk | S |

### Aşama 5 — Taze akış ve kesim (F8)
| İş | Sahip | Emek |
|---|---|---|
| `taze_al` hattı: önce ~11 binlik açık kapatılır, sonra 15 dakikada bir | veri + backend | L |
| Ajans içe alma: haber havuza düşer, oradan taslak olur | veri + yapay zekâ + haber müdürü | L |
| Kesim provası, kesim günü listesi ve geri dönüşün bir kez denenmesi | DevOps + `haber-sistemi-uzmani` | M |

### Aşama 6 — Fark yaratan katman (kesimle paralel başlayabilir)
| İş | Sahip | Emek |
|---|---|---|
| **Sayfaya özel tema düzeneği** (§6) ve seçilen sayfalar | frontend + `web-tasarim-direktoru` + test | M |
| Uydurma olgu denetimi (K2) otomatik; yapay zekâ köken kaydı; taslakta "doğrulanacaklar" tek tek işaretlenmeden yayın yok | yapay zekâ + backend | M |
| Chatterbox dinleme testi; geçerse sesin yerel modelle üretilmesi ve kendiliğinden başlatmanın kaldırılması | yapay zekâ | M → L |
| Okur için yapay zekâ: "Üç maddede ne oldu", konu dosyası özeti, yeni haberde konu ve ilçe önerisi (hepsi editör onaylı) | yapay zekâ + full stack | M |
| Sabah e-bülteni (Bursa manşetleri, eczane, hava, Bursaspor); WhatsApp kanalı | full stack + haber müdürü + SEO | M |

---

## 6. Sayfaya özel tasarım

**Mekanizma** (frontend ve test ajanlarının ortak önerisi):

1. `:root` içinde rol değişkenleri tanımlanır, varsayılanları kırmızı-lacivert:
   `--tema-baslik`, `--tema-baslik-koyu`, `--tema-baslik-yazi`, `--tema-vurgu`,
   `--tema-vurgu-yazi`, `--tema-cizgi`, `--tema-ak`, `--tema-odak`. Bu değişkenleri
   yalnız içerik sütunu bileşenleri kullanır. Üst kabuk ham marka renginde kalır;
   böylece "kabuk değişmez" kuralını CSS'in kendisi garanti eder.
2. Tema bloğu yalnız değişkenleri yeniden tanımlar:
   `body[data-bolum="bursaspor"] main{--tema-baslik:var(--yesil);…}`. Bugünkü
   39 geçersiz kılma ~8 satıra iner; yeni bir tema ~10 satır olur.
3. Tek kayıt yeri `icerik/temalar.py`. Kayda giren her satır kullanıcı kararının
   izidir. Düzen farkı gerekiyorsa `parca/bolum/<slug>.html` kullanılır; bugünkü
   Bursaspor örüntüsü budur.
4. Testler:
   - Kayıt, CSS ve plandaki liste birbirine eşit olmalı.
   - Her tema için kontrast hesaplanır: metin ≥ 4,5:1, odak ≥ 3:1.
   - Temalı sayfada üst kabuğun rengi Chrome ile ölçülür ve değişmemiş olmalı.
   - `test_bolume_ozel_renk_yok` bu kayıt tabanlı teste dönüşür.

**Aday sayfalar** (seçim kullanıcının; ajanların gerekçeleriyle):

| Aday | Ne farklı olur | Öneren |
|---|---|---|
| Nöbetçi eczane | Eczane tabelasının kırmızı "E"si (yeni renk gerekmez), büyük punto, ilçe süzgeci; yaşlı okura hizmet | frontend |
| Resmî ilan | Gazete ilan sayfası tipografisi: ağırbaşlı, siyah-beyaz, sütunlu | frontend, haber müdürü |
| Köşe yazıları / yazar sayfaları | Serif ve kâğıt tonu; "görüş" sayfası ayrımı | frontend |
| Konu dosyası (`/konu`) | Zaman çizgisi ve "nereden nereye" özeti; renkten çok düzen farkı | frontend, haber müdürü |
| İlçe sayfaları | İlçe kimliği: belediye, eczane, muhtarlık, harita; düzen özelleşir | haber müdürü |
| Bursa ekonomi ve sanayi | Otomotiv, tekstil, OSB, BTSO, piyasa bandı. Not: amber vurgu §62'de denenmiş, §63'te geri alınmıştı | haber müdürü |
| Seçim sayfası (ileride) | 17 ilçenin sonuç tablosu ve aday dosyaları | haber müdürü |
| Afet ve deprem hazırlığı | Kalıcı hizmet sayfası. Yeni içerik ister, yani kullanıcı kararı | haber müdürü |

---

## 7. Kullanıcı kararı gerektirenler

**Acil**
1. Harici diske soğuk yedek alınsın mı (disk alımı)?
2. Zamanlayıcı görevleri bu makinede yeniden açılsın mı? Görevler 12–13 Eylül'de
   kapatılmış, kimin kapattığı bilinmiyor.
3. Geçiş dönemi: kesime kadar haber eski CMS'ten mi girilecek (o zaman içe alma
   kurulur), yeni panelden mi? Kimlik aralığı da bu karara bağlı.
4. Çakışan üç kayıt (1696272–74) taşınsın mı, silinsin mi? Geri alınamaz.

**Altyapı ve para**
5. PostgreSQL: bu makinedeki kurulum mu, ücretli bir sunucu mu? Veritabanının
   Türkçe sıralama ayarı (ICU `tr-TR`) sonradan değiştirilemez.
6. Barındırma Türkiye'de mi, yurt dışında mı; aylık bütçe tavanı. Gazetenin
   mevcut barındırma, DNS ve e-posta altyapısı nerede?
7. Kabul edilebilir veri kaybı ve kesinti süresi (örneğin 24 saat / 4 saat).
8. GitHub Pages demosu ne olacak? Ürünün `main` dalına birleşmesi buna bağlı.
9. Avukat paketi: 5187, KVKK, BİK ve telif kalemleri için tek seferlik teyit.

**Editoryal**
10. Anasayfada Bursa/ulusal oranı ve düşüş kuralı. Öneri: ilk 15 manşetin en az
    10'u Bursa.
11. Son dakika yalnız editör kaydıyla mı yansın; eczane servis haberi banttan
    çıkarılsın mı?
12. Eşikle verilen 19.966 konu onayı: örneklemle mi denetlensin, yoksa 2026
    dosyaları bekleyene mi geri alınsın?
13. Yapay zekâ katkısı okura beyan edilsin mi? "Yayın ilkeleri" sayfası olsun mu?
14. Canlıda kaldırılan haber bizde otomatik pasife düşsün mü?

**Hukuk**
15. Künye/iletişim bilgilerinin geri gelmesi (3 Eylül'de kaldırılmıştı, 7418
    sonrası yasal zorunluluk).
16. Herkese açık depodaki üçüncü taraf fotoğraf ve metinler: ağaçtan, gerekirse
    geçmişten silinsin mi?
17. 2FA anahtarının saklanması; `Yorum`/`LogKaydi` IP verisi; Google Fonts
    yerine yerel font.
18. "Google News" alt metninin 1 milyon kayıtta temizlenmesi.

**Ürün**
19. Görsel yükleme politikası (depolama, kırpma, boyut).
20. Model yolu ürüne nasıl girecek: (a) API anahtarı ile, taslak başına
    ~0,08–0,10 $; (b) yalnız editör makinesinde kalır. Okur özeti için ayda
    ~45–90 $.
21. Seslendirme: Chatterbox testi geçene kadar tarayıcı sesi sitede kalsın mı,
    gizlensin mi?
22. Slayt duraklatma düğmesi geri gelsin mi (WCAG 2.2.2)? Bursa ve ekonominin
    turkuaz/amber işaret renkleri kalsın mı?
23. **Hangi sayfalar özel tasarım alacak** (§6)?

---

## 8. Düzeltmeler (bu oturumun önceki raporuna göre)

- **Eczane görevinin hata kodu `0x800710E0`** ("istek reddedildi"), `0x80070520`
  değil. Önceki raporda onaltılık çevirisi yanlış yapılmıştı.
- **PostgreSQL bugün çalışmıyor:** 16, 17 ve 18 sürümleri kurulu, ama kayıtlı
  hizmet yok ve 5432 dinlenmiyor. Hafızadaki "çalışıyor" notu eskimişti.
- Arama ölçümü plandaki "p95 1.748 ms" değerini geçersiz kılıyor: o ölçüm 308 bin
  kayıtta yapılmıştı, bugün kayıt 1 milyon.
