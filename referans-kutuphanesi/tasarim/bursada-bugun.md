# Bursada Bugün — tasarım çözümlemesi

- İnceleme: **2026-10-20, 10:38–10:42 TSİ** · **tek ölçüm, 2026-10-20, Türkiye, başsız Chrome, çerez kabul edilmedi** · yerel rakip: sıralama/puan yoktur.
- Koşul: 1440×900 (DPR 1) ve 390×844 (DPR 2, mobil + dokunma öykünmesi); UA değiştirilmedi (masaüstü HeadlessChrome UA'sı); önbellek kapalı; işletim sistemi koyu temada (`prefers-color-scheme: dark`) — site açık temayla çizildi.
- Erişim: robots.txt 2026-10-20'de yeniden okundu, değişiklik yok. Robots'ta kapalı yola istek gitmedi.
- Çerez bandı: yalnız "KABUL ET" düğmesi var → **kapatılmadı**; 1440'ta altta 78 px, tüm görüntülerde duruyor.
- Yükleme: 8 + robots.txt 1.
- İncelenen: [anasayfa](https://www.bursadabugun.com/) · [ekonomi](https://www.bursadabugun.com/ekonomi-haberleri) · [haber detayı](https://www.bursadabugun.com/haber/bursa-hayvanat-bahcesi-nde-dev-karincayiyenin-ozel-menusu-40-dakikada-hazirlaniyor-1957734.html) · [nöbetçi eczane](https://www.bursadabugun.com/bursa-nobetci-eczaneler)
- Görüntüler: `referans-kutuphanesi/ham/ekran/bursada-bugun/`. İşlevsel çözümleme: `siteler/bursada-bugun.md`. Yöntem: `tasarim/haberturk.md` başındaki not.
- **Mobil uyarısı:** sayfada `meta viewport` yok; 390 px öykünmede sayfa ~996 px masaüstü düzeniyle çizilip küçültüldü. Sitenin gerçek telefonlara ayrı sürüm (ör. `m.` alanı) verip vermediği UA değiştirilmeden görülemez → "390" görüntüleri telefon deneyimini **temsil etmeyebilir**.

## 1. Tipografi

- **Tek aile:** Inter (%100, Google Fonts). Ağırlıklar 400/500/600/700. Büyük harf dönüşümü neredeyse yok; ara başlıklar ve eczane adları metnin kendisinde büyük harf.
- **Ölçek (1440):**

| kademe | boyut/satır/ağırlık |
|---|---|
| detay H1 | 40/50/700 siyah |
| detay ara başlık | 32/38/600 (büyük harf metin) |
| ekonomi manşet (görsel üstü) | 28/42/600 beyaz |
| bölüm H1 ("Ekonomi Haberleri") | 30/36/600 |
| detay spot | 20/30/400 |
| kart başlığı | 16/26/600 `rgb(46,57,63)` (46 adet) |
| gövde | 16/28/400 |
| menü | 15/22,5/500 |

- **Gövde:** 16/28, sütun 647 px ≈ **85 karakter/satır**; spot 970 px tam genişlikte (≈ 100+ kar./satır) ([detay](https://www.bursadabugun.com/haber/bursa-hayvanat-bahcesi-nde-dev-karincayiyenin-ozel-menusu-40-dakikada-hazirlaniyor-1957734.html), `detay-1440-ilk.png`).
- Gövde ve ara başlıklar **iki yana yaslı** görünüyor; ara başlıkta kelime araları belirgin açılıyor (`parca/detay-1440-tam-800-2900.png`; `text-align` değeri ölçülmedi, görüntü kanıtı).

## 2. Renk

- Metin: koyu arduvaz `rgb(46,57,63)` %52–54, siyah %21; beyaz %20 (görsel üstü).
- Zemin: beyaz + açık gri `rgb(242,242,242)` bloklar (ilk 3 ekranda yaklaşık yarı yarıya).
- **Kategori renk kodu — 6 renk:** etiket beyaz sekme üstünde renkli yazı (14/500, köşesiz): turuncu (Güncel), kırmızı (Bursa Bölge/Dünya), mor (Magazin), yeşil, camgöbeği (Teknoloji), mavi (Ekonomi) (`parca/anasayfa-1440-tam-800-2900.png`). Renk kategoriyi kodluyor ama renk sayısı fazla; kırmızı iki kategoride ortak.
- Piyasa başlığında değer rengi yön taşıyor (yeşil/kırmızı) (`anasayfa-1440-ilk.png`).
- Logo iki tonlu (kırmızı + koyu).

## 3. Izgara ve ritim

- Ortalanmış kapsayıcı **990 px** (içerik 970); iki yanda 160 px dikey reklam panoları → görünür içerik + reklam ≈ 1.320 px (`anasayfa-1440-ilk.png`).
- Anasayfa: 3 eşit sütun (sütun izleri 230/560/900 px), arada 2/3 + 1/3 bloklar; sağ ray `col-4` 333 px yalnız bazı bölümlerde.
- Detay: 647 px makale + 333 px ray (sticky değil).
- Bölüm ayracı: belirgin değil — bloklar arasında boşluk; boş gri reklam kutuları ızgara hücresi gibi duruyor (`parca/anasayfa-1440-tam-800-2900.png`).

## 4. Kart dili

- Görsel oranı ağırlıkla **16:9** (44/62), köşe 0, gölge yok.
- Başlık görselin **altında**, 2 satır; etiket görselin sol alt köşesine oturan beyaz sekme (bkz. §2).
- Kart başlıkları ve ray listesi "…" ile kesiliyor (`parca/detay-1440-tam-800-2900.png` sağ ray).
- Manşet: görsele **basılmış** büyük başlık + 1–18 numaralı kutucuklu sayfalayıcı (`anasayfa-1440-ilk.png`); ekonomi manşetinde numara yerine küçük resim şeridi (`bolum-ekonomi-1440-ilk.png`).
- Saat: anasayfada 6 saat damgası; detay künyesi `2026.10.20 09:02` biçiminde (yıl-ay-gün, noktalı).

## 5. Başlık hiyerarşisi (ilk ekran, 1440)

- Kademeler: manşet görseli (metin resmin içinde) → sağda 1 kart (16/600) → son dakika şeridi tek satır. Ölçütün saydığı başlık 8, ama manşet başlığı görsel olduğu için metin olarak sayılmıyor.
- İlk ekranın yaklaşık üçte biri reklam (iki yan pano + manşet altında 970×90).

## 6. Gezinme ve kabuk

- Başlık: logo (200×30) + 5 piyasa kalemi + hava (76 px) → beyaz menü çubuğu (9 bağlantı, 15/500) → son dakika şeridi. Kabuk sakin, beyaz, gölgesiz.
- Kaydırınca 50 px sabit menü + 78 px çerez bandı = 128 px (%14); detayda 60 px "haberFixed" çubuğu (`yapiskan_kaydirinca`).

## 7. Mobil (390)

- Viewport meta olmadığından masaüstü düzeni küçülmüş çizildi: menü yazıları ~6 px görünür boyutta, dokunma hedefleri küçük (`anasayfa-390-ilk.png`). Sayfa yüksekliği 1440 ile aynı (11.339 px) — düzen değişmiyor.
- Görüntüde bir reklam yuvası kırık görsel simgesiyle boş kalmış (`anasayfa-390-ilk.png`, ikinci reklam bandı).

## 8. Rafine ↔ kaba

İyi işlenmiş:
1. **Sakin beyaz kabuk** — tek aile, beyaz başlık, ince alt gölge; logo + piyasa + hava tek satırda okunuyor (`anasayfa-1440-ilk.png`, başlık 76 px).
2. **Detay başlığı güçlü** — H1 40/50/700, spot 20/30, künye satırında yayın + güncelleme zamanı ayrı (`detay-1440-ilk.png`).
3. **Eczane listesi iki sütun, tek eylem düğmesi** — her kayıtta ad-ilçe başlığı, adres, telefon, kırmızı "Haritada Göster" (`eczane-1440-ilk.png`).

Kaba duran:
1. **İki yana yaslı gövde ve ara başlık** — dar sütunda kelime boşlukları açılıyor (`parca/detay-1440-tam-800-2900.png`).
2. **Satır uzunluğu** — gövde ≈85, spot ≈100+ kar./satır; rahat okuma aralığının (yaklaşık 45–75) üstünde (`detay-1440.json` ölçümü).
3. **Eczane verisi ham** — adresler tamamen büyük harf, telefon biçimsiz 11 hane bitişik (`eczane-1440-ilk.png`).
