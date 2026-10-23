# Tasarım dili — siteler arası desenler (ekran görüntüsü + ölçüm)

Son güncelleme: 2026-10-20 · Kaynak siteler (doğrudan): Habertürk, Bursada Bugün, Bursa Saati,
Özgür Kocaeli, Ege'de Son Söz, Spiegel (kısmi: yalnız `/ausland/`, `/tests/`).

**Koşul:** tek ölçüm, 2026-10-20, Türkiye, başsız Chrome 155, UA değiştirilmedi, çerez kabul
edilmedi, 1440×900 ve 390×844 (mobil öykünme). İşletim sistemi koyu temada olduğundan tarayıcı
`prefers-color-scheme: dark` bildirdi; yalnız Spiegel koyu temaya geçti. Yerel rakipler için
sıralama/puan yoktur. Site ayrıntısı: `tasarim/<site>.md`; görüntüler `ham/ekran/<site>/`
(depoya girmez). Yöntem: `getComputedStyle`; karakter/satır = paragraf genişliği ÷
`canvas.measureText` ortalama karakter genişliği.

**BH süzgeci:** kırmızı–lacivert–beyaz, klasik, Bursa önce (EKIP.md "Tasarım dili");
reddedilenler (sarı/somon/fildişi kâğıt, Tailwind/React, vefat modülü …) aşağıda
"BH için: reddedildi" diye işaretli. Logo, ikon, fotoğraf, yazı tipi dosyası, CSS kodu alınmaz;
yalnız çözüm tarif edilir.

## 0. En önemli 7 ders (tek satır)

1. **Okuma sütunu sayfa sütunundan dar olmalı** — Spiegel 624 px ≈70 kar./satır; yerel siteler 81–100 kar./satır (`tasarim/spiegel.md` §1, `tasarim/egede-son-soz.md` §1).
2. **Başlık metin olarak kalmalı** — görsele basılı manşet metni 4 yerel sitede + Habertürk'te; tipografiden kopuk, ölçeklenmiyor (`haberturk/bolum-ekonomi-1440-ilk.png`, `ozgur-kocaeli/anasayfa-1440-ilk.png`).
3. **Başlık kesilmemeli** — "…" ile biten kart başlıkları Habertürk, Bursada Bugün, Ege 390'da (`haberturk/anasayfa-1440-ilk.png`).
4. **Haber ilk ekranda başlamalı** — Ege 131 px'te, Bursa Saati 648 px'te (arada ~145 px boş reklam yeri) (`egede-son-soz/anasayfa-1440-ilk.png`, `bursa-saati/anasayfa-1440-ilk.png`).
5. **Aile başına tek görev** — başlık ailesi / arayüz ailesi / gövde ailesi (Spiegel slab–sans–serif; Özgür Kocaeli Gotham Black–Roboto) (`ozgur-kocaeli/detay-1440-ilk.png`).
6. **Renk bilgi taşısın, az olsun** — piyasa yönü (yeşil/kırmızı + ok), saat rozeti; 6 renkli kategori kodu ise okunmuyor (`bursada-bugun/parca/anasayfa-1440-tam-800-2900.png`).
7. **Sıkı harf aralığı + 1,0 satır aralığı büyük başlıkta kaba** — Bursa Saati/Ege H1 −2,3 px (`bursa-saati/detay-1440-ilk.png`).

## 1. Tipografi ölçeği

| Site | Aileler (görev) | Detay H1 (1440 / 390) | Spot | Gövde (punto/satır, sütun, kar./satır) | Kart başlığı |
|---|---|---|---|---|---|
| Habertürk | 1 sans (her şey) | 30/36/900 · 24/32 | 16/24/400 kırmızı | 16/24, 626 px, ≈79 | 20/32/700 · mobil 14/24 |
| Bursada Bugün | 1 sans | 40/50/700 · aynı (masaüstü düzen) | 20/30/400, 970 px | 16/28, 647 px, ≈85 | 16/26/600 |
| Bursa Saati | 1 sans | 40/40/700, −2,3 px · 35/35 | 25/30/**300** | 20/30, 685 px, ≈81 | 17/24/700 |
| Ege'de Son Söz | 1 sans (aynı platform) | 60/60/700, −2,3 px · 35/35 | 25/30/300, 1.295 px | 20/30, 832 px, ≈100 | 17–20/700 |
| Özgür Kocaeli | 2: display (Black) + sans | 54,6/60,1, −1,68 px · 39,2/44,7 | 23,1/32,2/500 | ölçülmedi (~600 px sütun) | 20,7/600 · mobil 19/500 |
| Spiegel | 3: slab başlık + sans arayüz + **serif gövde** | 44/47,5/800 · 32/34,6 | ölçülmedi | **20/30, 624 px, ≈70** · mobil 18/27, 44 | 20/25,2/700 (mobilde küçülmüyor) |
| **BH (şimdi)** | 3: Roboto Condensed (başlık) + Roboto (arayüz) + Roboto Serif (gövde, spot) | 34/1,09/900 · 25 (`site.css` 1923, 2006) | 16,5–17 serif, sol 4 px çizgi (1924, 2628) | 18/1,62–1,66, `max-width:38em` (1990, 2627) → 684 px; kar./satır **ölçülmedi** | 18/1,16/700 · mobil 17 (566, 1779) |

**Ortak ders:** Yerel sitelerin hepsi tek sans aileyle çalışıyor; hiyerarşiyi punto değil
ağırlık (700–900) ve renkle kuruyor. Gövde punto olarak iyi (16–20 px) ama **satır uzun** (79–100
karakter). Okunurluğu en iyi tarif eden iki çözüm: Spiegel'in dar okuma sütunu (624 px, ≈70) ve
Özgür Kocaeli'nin başlık/metin ailesi ayrımı.

**Hangi koşulda:** dar sütun, gövde reklamla bölünmüyorsa ve ray ayrı tutuluyorsa işe yarıyor;
masa büyüklüğünden bağımsız (salt CSS). Üç aile, yükleme bütçesi (yazı tipi dosyası) izin
veriyorsa; BH zaten üç aileyi yerel dosyalarla sunuyor.

**BH için alınabilir:**
- Gövde satırını ölç (aynı yöntemle) ve ≈60–75 karakter aralığına çek; 38em sınırı 18 px'te 684 px — Spiegel'den 60 px geniş. → `test-kalite-muhendisi` ölçer, `frontend-gelistirici` uygular.
- Başlık/arayüz/gövde ayrımını koru; dördüncü aile ekleme.
- Mobilde kart başlığını küçültme konusunda Spiegel tutumu (20 px sabit) — BH 18→17 zaten yakın; daha fazla küçültme.

**BH için alınmamalı:**
- Büyük başlıkta −1,5 px'ten sıkı harf aralığı ve 1,0 satır aralığı (BH −0,3 px / 1,06–1,09 doğru tarafta).
- Spotu 300 ağırlıkta 25 px tam genişlik (Bursa Saati/Ege) — uzun satır + ince kesim.
- İki yana yaslı gövde/ara başlık (Bursada Bugün görüntüsü).

## 2. Renk

| Site | Kimlik rengi | Nötr zemin | Kategori kodu | Bilgi taşıyan renk |
|---|---|---|---|---|
| Habertürk | kırmızı logo bloğu | beyaz + `rgb(243,244,246)` kenar | yok | piyasa yeşil/kırmızı + ok |
| Bursada Bugün | kırmızı logo | beyaz + `rgb(242,242,242)` | **6 renk** (turuncu, kırmızı ×2 kategori, mor, yeşil, camgöbeği, mavi) | piyasa yönü |
| Bursa Saati | kırmızı-siyah | `rgb(233,236,239)` + beyaz | yok; ekonomi bölümü **hardal zemin** | kırmızı saat rozeti; eczanede eylem rengi |
| Ege'de Son Söz | kırmızı `rgb(217,0,0)` bant | `rgb(233,236,239)` + beyaz | tek koyu gri kutu | kalın saat, piyasa yönü |
| Özgür Kocaeli | **lacivert** `rgb(21,51,134)` bant | `rgb(227,233,238)` + beyaz | tek renk (yarı saydam lacivert hap) | ilçe başlığı mavi, piyasa yönü |
| Spiegel (koyu tema) | turuncu-kırmızı bant | siyah + koyu panel | yok | ücretli içerik "+" işareti |

**Ortak ders:** En sakin sonuç, kimlik renginin yalnız kabukta (bant/logo) durduğu ve içerikte
tek nötr + tek vurgu kaldığı sitelerde (Özgür Kocaeli, Ege, Spiegel). Renk ancak bir şey
söylediğinde (yön, saat, eylem türü) okura iş görüyor; 6 renkli kategori kodu ezberlenmiyor.

**BH için alınabilir:** Özgür Kocaeli'nin lacivert bant + açık mavi-gri sayfa zemini + beyaz kart
düzeni BH'nin `--lacivert` / `--zemin` / `--kagit` üçlüsüne en yakın örnek (renk değeri
alınmaz; BH değişkenleri zaten var). Kategori işaret rengi denemesi (§35, iki renk) bu
kanıtla tutarlı: ikiyi geçmesin. → `web-tasarim-direktoru`

**BH için alınmamalı:** bölüm zemini sarı/hardal (Bursa Saati ekonomi) — **BH için: reddedildi
(kullanıcı kararı: sarı/somon/fildişi ton)**; ekonomi özel tasarımı başka yoldan (bkz. §5).
Koyu tema kendiliğinden açılması (Spiegel) — kullanıcı kararı "beyaz kalsın"; önerilmez.

## 3. Izgara ve ritim

| Site | Kapsayıcı | Detay: gövde + ray | Ayraç |
|---|---|---|---|
| Habertürk | 1.280 (içerik 970) + iki yan 160 px giydirme | 642 + 300 (sticky) | boşluk + başlıktan "TÜMÜ"ye 1 px hat |
| Bursada Bugün | 990 + iki yan 160 px pano | 647 + 333 | boşluk; boş gri reklam hücreleri |
| Bursa Saati | 1.100 | 685 + 364 | beyaz blok + gri aralık |
| Ege'de Son Söz | **1.320** | 857 + 420 | kırmızı başlık + kırmızı ince hat |
| Özgür Kocaeli | 984–1.008 (beyaz panel) | ~600 + 346 | beyaz kart + 1 px alt çizgi |
| Spiegel | 960 (panel 1.008–1.020) | **624 (ortada, sayfa sütunundan dar)**, ray yok | zemin farkı + boşluk |
| **BH** | `.sayfa` 1.100 + ray 320 (`site.css` 322, 702) | `.metin` 38em | — |

**Ortak ders:** Kapsayıcı genişliği satır uzunluğunu belirliyor; okuma sütununu ayrıca
sınırlamayan siteler (Ege 1.320 px → ≈100 kar./satır) uzun satıra düşüyor. Ayraçta çizgi
yerine **zemin farkı + boşluk** kullanan siteler (Özgür Kocaeli, Spiegel) daha az gürültülü.

**BH için:** 1.100 + 320 ızgarası korunur; okuma sütunu §1'deki ölçümle sınırlanır. Bölüm
başı ayracı tek biçimde (BH'de lacivert başlık şeridi var) kalsın. → `frontend-gelistirici`

## 4. Kart dili

| Site | Oran | Köşe/gölge | Başlık konumu | Etiket | Kesik başlık | Görsele basılı metin |
|---|---|---|---|---|---|---|
| Habertürk | 1:1, 16:9, dikey | 0 / yok | görsel üstü (degrade) | yok | **var** | **var** (manşet) |
| Bursada Bugün | 16:9 | 0 / yok | altta | beyaz sekmede renkli yazı | **var** | **var** |
| Bursa Saati | 16:9; detay 5:3 | 0; ekonomi kartı 6,4 px | üstte (anasayfa) / altta | kırmızı hap | az | **var** |
| Ege'de Son Söz | 16:9 | 0; ekonomi 6,4 px | altta | koyu gri kutu | mobilde | anasayfa manşetinde |
| Özgür Kocaeli | 16:9, 1:1 | 0 / yok | altta | lacivert hap görsel üstünde | az | **var** |
| Spiegel | **3:2** (mobil 4:3) | 0 / yok | altta, üst bilgi → başlık → özet | yok | ölçülmedi | ölçülmedi |
| **BH** | 3:2 (`aspect-ratio:3/2`, kırpılmaz — kullanıcı kararı) | 0–4 px | altta; manşette görsel üstü degrade | `.kart .ust` 11 px büyük harf, renkli yazı | yalnız son dakika manşeti 3 satır, yazar özeti 2 satır | yok |

**Ortak ders:** Köşesiz, gölgesiz kart beşi altı sitede ortak — klasik haber dilinin çizgisi.
Fark yaratan ayrıntı kart çerçevesi değil, **başlığın tam ve metin olarak** durması. Görsele
basılmış başlık Türkiye'de yaygın (TV/gazete manşeti alışkanlığı), ama punto/kontrast
denetlenemiyor, mobilde küçülüp okunmuyor ve ekran okuyucuya ulaşmıyor.

**BH için alınabilir:** Spiegel'in kart sırası (üst bilgi → başlık → özet) BH'nin
`.kart .ust` → `h3` sırasıyla aynı; korunur. **BH için alınmamalı:** görsele basılı başlık,
"…" ile kesilen kart başlığı (bkz. §0). Görsele metin basma editoryal bir alışkanlıksa
→ `haber-muduru` (manşet görseli üretim kuralı).

## 5. İlk ekran ve başlık hiyerarşisi

| Site (1440) | İlk haber başlığının üst kenarı | Ondan önce ne var |
|---|---|---|
| Ege'de Son Söz | **131 px** | kırmızı bant + menü |
| Özgür Kocaeli | ~330 px (manşet) | lacivert başlık + son dakika + servis çubuğu |
| Habertürk | 428 px (sürmanşet) | piyasa + başlık + menü + 970×250 reklam |
| Bursada Bugün | ~189 px (manşet görseli) | başlık + menü + son dakika |
| Bursa Saati | 648 px | reklam + logo + menü + reklam + **~145 px boşluk** + son dakika + piyasa |
| Detay H1 üst kenarı | Ege 160 · Özgür Kocaeli 336 · Habertürk 539 · Bursa Saati 573 | |

**Ortak ders:** Bölüm sayfasında kabuğun bölüm adını büyük taşıması (Habertürk "Ekonomi"
36/900 menünün solunda) ve Ege'nin ekonomi başı (bölüm şeridi → alt kategoriler → piyasa
bandı → manşet + hesaplayıcı) okura "neredeyim" ve "rakam nerede" sorusunu tek ekranda
cevaplıyor. Özgür Kocaeli'nin **servis çubuğu** (il, hava, namaz geri sayımı, piyasa — tek
satır) manşetin üstünde yer kaplamadan yerel hizmeti öne alıyor.

**BH için alınabilir:** ekonomi özel tasarımı için "bölüm adı büyük + alt kategori + piyasa
bandı" katmanı (renk değil yapı) → `web-tasarim-direktoru` (özel tasarım sayfası;
uygulanacak sayfa kullanıcı kararıdır). Haber başlangıcını ölç: BH anasayfa ve detayda ilk
başlığın y değeri 1440/390'da → `test-kalite-muhendisi`.

## 6. Mobil kabuk (390)

| Site | Sabit/yapışkan (kaydırınca) | İlk ekranda okunur haber başlığı | 24 px altı dokunma hedefi |
|---|---|---|---|
| Habertürk | 89 px (detayda +100 px reklam → 204 px, %24) | 3 | 25/67 |
| Özgür Kocaeli | 85 px başlık (+ detayda 44 px alt paylaşım çubuğu) | detayda H1 + spot | **35/55** |
| Ege'de Son Söz | başlık kaydırınca gizleniyor; yalnız çerez bandı | 4 | 9/71 |
| Bursa Saati | yalnız çerez bandı (105 px) | 1 (kesik) | 12/49 |
| Bursada Bugün | viewport meta yok → masaüstü düzeni küçültülmüş | ölçülemez | — |

**Ortak ders:** Mobilde en temiz çözüm Ege'ninki: başlık aşağı kaydırınca gizleniyor
(`slideUp`, ölçümde üst kenar −70 px; yukarı kaydırınca geri gelip gelmediği **ölçülmedi**);
ilk ekranda 2×2 görselli kart. Sabit katmanlar toplamı ekranın %10'unu
geçince (Habertürk detay %24) okuma alanı daralıyor.

**BH için:** `.kategori` / `.menu` yapışkan (`site.css` 413, 1812); 390'da toplam sabit
yüksekliği ölç, %10'u geçmesin; dokunma hedeflerini 24 px alt sınırına göre denetle
→ `test-kalite-muhendisi`, düzeltme `frontend-gelistirici`.

## 7. Servis sayfası (nöbetçi eczane) görsel dili

| Site | Düzen | Kayıt kartı | Kaba ayrıntı |
|---|---|---|---|
| Özgür Kocaeli | ilçeye göre gruplu (mavi ilçe başlığı), tek sütun | ad + adres solda; biçimli telefon + küçük "Yol tarifi" sağda | — |
| Bursa Saati | tek sütun kart + sağda ilçe çipleri | ad, ilçe hapı, adres, iki renkli eylem düğmesi | listenin üstünde dekoratif görsel; mobilde ilk ekran boş reklam |
| Ege'de Son Söz | aynı platform | aynı | 111 kayıt tek sayfada, 34 bin px |
| Bursada Bugün | iki sütun | ad-ilçe, adres, telefon, kırmızı "Haritada Göster" | adres tamamen büyük harf, telefon biçimsiz |

**BH için alınabilir:** ilçe gruplaması + biçimli telefon + tek eylem düğmesi; listenin
üstüne dekoratif görsel koyma. → `frontend-gelistirici` (BH'de ilçe ve servis sayfaları var;
uygulama durumu `URUN-PLANI.md`den doğrulanmalı).

## 8. Bu taramada görülen ama BH için reddedilmiş/önerilmeyenler

- Vefat modülü (Özgür Kocaeli anasayfası, `parca/anasayfa-1440-tam-850-2900.png`) — **BH için: reddedildi (kullanıcı kararı)**.
- Sarı/hardal bölüm zemini, tam sarı "seri ilanlar" bandı — **BH için: reddedildi (sarı ton kararı)**.
- Tam ekran "Google kaynak tercihi" penceresi (Özgür Kocaeli) — okumayı kesiyor; bağlantı biçimi ayrı karar (`siteler/ozgur-kocaeli.md`) → `haber-muduru`, `seo-buyume-uzmani`.
- Rıza/ödeme duvarı (Spiegel) — gelir modeli; tasarım dersi değil.
- Habertürk DOM'unda yardımcı-sınıf (utility) kalıbında adlar görüldü (`text-2xl md:text-3xl`, `w-full sticky`) — hangi araçla üretildiği doğrulanmadı; **BH için: Tailwind/bundler reddedildi**, yalnız görsel sonuç tarif edildi.

## Öneri tablosu

| # | Öneri (çözüm düzeyinde) | Kanıt | Öncelik | Emek | Sahip |
|---|---|---|---|---|---|
| 1 | Detay gövdesinde karakter/satırı aynı yöntemle ölç; ≈60–75'e çek | §1, Spiegel 624 px ≈70 | P0 | S | `test-kalite-muhendisi` → `frontend-gelistirici` |
| 2 | Kart/manşet başlığını kesmeme ve metin olarak tutma kuralını tasarım ilkesine yaz (BH bugün uyuyor; korunacak) | §4 | P0 | S | `web-tasarim-direktoru` |
| 3 | Anasayfa ve detayda ilk haber başlığının y değerini 1440/390'da ölç; boş ayrılmış alan bırakma | §5 | P1 | S | `test-kalite-muhendisi` |
| 4 | 390'da sabit kabuk toplamı ≤ %10; aşağı kaydırınca gizlenen başlık seçeneğini değerlendir | §6, Ege | P1 | M | `web-tasarim-direktoru` → `frontend-gelistirici` |
| 5 | Dokunma hedefi 24 px alt sınır denetimi (WCAG 2.5.8) | §6 | P1 | S | `test-kalite-muhendisi` |
| 6 | Kategori işaret rengi en çok iki (§35 denemesiyle aynı yön); renk yalnız bilgi taşırken | §2 | P1 | S | `web-tasarim-direktoru` |
| 7 | Ekonomi özel tasarımında "bölüm adı büyük + alt kategori + piyasa bandı" katmanı (renk değil yapı) | §5, Habertürk/Ege | P2 | M | `web-tasarim-direktoru` (sayfa seçimi kullanıcıda) |
| 8 | Eczane/servis listesinde ilçe gruplaması, biçimli telefon, tek eylem; dekoratif görsel yok | §7 | P2 | S | `frontend-gelistirici` |
