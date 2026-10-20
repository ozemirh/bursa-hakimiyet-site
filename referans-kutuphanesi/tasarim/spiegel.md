# Der Spiegel — tasarım çözümlemesi (kısmi)

> **Kısmi erişim.** robots.txt yalnız `Claude-User`'a belirli yolları açıyor; bu çalışmada yalnız `/ausland/` ve `/tests/` yüklendi. Anasayfa ve ekonomi (`/wirtschaft/`) **açılmadı**. Ayrıca sayfayı "öde ya da onayla" penceresi kapatıyor; reddet seçeneği yok → kapatılmadı, kaydırma kilitli. Görsel kanıt yalnız kabuk ve pencere çevresi; ölçülerin çoğu pencerenin altındaki DOM'dan `getComputedStyle` ile alındı.

- İnceleme: **2026-10-20, 10:38–10:40 TSİ** · tek ölçüm, Türkiye, başsız Chrome 155 (UA değiştirilmedi), çerez/rıza **kabul edilmedi**.
- Koşul: 1440×900 (DPR 1) / 390×844 (DPR 2, mobil + dokunma). **İşletim sistemi koyu temada → `prefers-color-scheme: dark`; Spiegel koyu temayla çizildi** (gövde zemini siyah). Aşağıdaki renkler koyu temanındır; açık tema ölçülmedi.
- Erişim: robots.txt 2026-10-20'de yeniden okundu, değişiklik yok (`Claude-User`: `/ausland/ /partnerschaft/ /gesundheit/ /familie/ /reise/ /psychologie/ /stil/ /tests/`; `ClaudeBot`/`anthropic-ai`: `Disallow: /`; dosya sonunda izinsiz otomatik erişim yasağı notu). `www.spiegel.de` üzerinde bu yollar dışındaki her alt istek tarayıcı içinde engellendi (ör. `/public/spon/json/manifest.json`).
- Yükleme: 6 (`/ausland/` ×2, bir `/ausland/` haber detayı ×2, `/tests/` ×2) + robots.txt 1. Aynı gün önceki işlevsel taramada 11 istek vardı (`siteler/spiegel.md`).
- İncelenen: [/ausland/](https://www.spiegel.de/ausland/) · [haber detayı (ajans haberi, adresinde kişi adı yok)](https://www.spiegel.de/ausland/mallorca-hoechste-sturmwarnung-fuer-baleareninsel-ausgerufen-a-e4318c01-6ad7-4e03-8859-8482b32fde6c) · [/tests/](https://www.spiegel.de/tests/)
- Görüntüler: `referans-kutuphanesi/ham/ekran/spiegel/` — "tam" görüntüler kaydırma kilidi yüzünden ilk ekranla aynı (900 / 844 px).

## 1. Tipografi

- **Üç aile, üç görev** (sitenin kendi marka yazı tipleri — lisanslı, alınmaz; yalnız görev ayrımı tarif edilir):
  - dar slab (condensed) 800 → bölüm adı ve haber başlıkları,
  - sans → arayüz, kart başlıkları, üst bilgi,
  - serif → yalnız haber gövdesi (detayda metnin %41–44'ü).
- **Ölçek:**

| kademe | 1440 | 390 |
|---|---|---|
| detay başlığı (slab 800) | 44/47,5 | 32/34,6 |
| bölüm adı (slab 800) | 36/38,9 | 28/30,2 |
| küme başlığı (slab 700–800) | 32/34,6 | 24/25,9 |
| kart başlığı (sans 700) | 20/25,2 | 20/25,2 |
| kart özeti (sans 400) | 16/22,1 | 16/22,1 |
| üst bilgi / tarih (sans 400) | 14/17,6 | 14/17,6 |
| gövde (serif 400) | **20/30**, 624 px ≈ **70 kar./satır**, paragraf arası 24 | 18/27, 44 kar./satır, 16 |

- Büyük harf dönüşümü yalnız 14/700 küçük etiketlerde (8 adet).
- Gözlem: **mobilde kart ölçeği küçülmüyor** (20/25,2 her iki genişlikte); yalnız başlık ve gövde bir kademe iniyor.

## 2. Renk (koyu tema)

- Metin `rgb(241,239,237)` (sıcak kırık beyaz) %87–91; ikincil metin `rgb(187,185,183)` %9–12.
- Zemin siyah + `rgb(31,30,28)` içerik paneli; tek vurgu turuncu-kırmızı `rgb(208,61,18)` — üst marka bandı ve bazı küme başlıkları (`bolum-tests-1440-ilk.png`).
- Toplam **iki nötr + bir vurgu**; kategori renk kodu yok. Ücretli içerik işareti kırmızı kare içinde "+" (`bolum-tests-1440-ilk.png`, başlığın solunda).

## 3. Izgara ve ritim

- İçerik genişliği **960 px** (sol 240), panel 1.008–1.020 px; detayda okuma sütunu 672 px kapsayıcı, gövde 624 px (sol 408) — sayfa sütunundan daha dar, ortada.
- Bölüm sayfası tek ana sütun (sütun izleri ağırlıkla 240 px'te), sağ ray yok; `/tests/`'te 2–3 sütunlu kart grupları (240/580/910).
- Ayraç: çizgi yerine zemin farkı (panel/sayfa) ve boşluk; `hr` bölümde 0, detayda 3.

## 4. Kart dili

- Görsel: **3:2** masaüstünde (27/35 `/ausland/`, 97/120 `/tests/`), mobilde **4:3**'e dönüyor (25/30) — aynı kart iki genişlikte farklı oran. Köşe 0; çerçeve/gölge yok.
- Kart: üst bilgi (14 px) → başlık (20/700) → özet (16/400); başlık görselin altında. Ölçülen 46 kartın hiçbirinde zemin/çerçeve yok.

## 5. Başlık hiyerarşisi

- İlk ekranda (pencere altında) bölüm adı 36 px → ilk küme başlığı → 3:2 görsel (542 px). Sayfanın kalanı görülemedi.

## 6. Gezinme ve kabuk

- Üstte 80 px turuncu-kırmızı marka bandı (logo yazısı 175×23 solda; sağda abonelik bağlantısı + giriş düğmesi) → 56 px koyu gezinme çubuğu ("Menü", bölüm bağlantıları 14/400, arama) (`detay-1440-ilk.png`).
- Mobilde logo 137×18; menü bağlantı yüksekliği 48 px.

## 7. Mobil (390)

- Rıza penceresi tüm ekranı kaplıyor (`bolum-ausland-390-ilk.png`); ilk ekran içeriği görülemedi.
- Dokunma: ilk iki ekrandaki 17 öğenin 4'ü 24 px altı (pencere altındaki DOM).

## 8. Rafine ↔ kaba

İyi işlenmiş:
1. **Ailelerin görev ayrımı** — slab başlık, sans arayüz, serif gövde; her aile tek işte (ölçüm: `detay-1440.json` aile payı).
2. **Okuma sütunu sayfa sütunundan dar** — 624 px, 20/30, ≈70 kar./satır, paragraf arası 24 px (`detay-1440.json`).
3. **Az renk** — iki nötr + bir vurgu; kategori kodu yok, hiyerarşi tipografiyle (`bolum-tests-1440-ilk.png`).

Kaba duran (görülebildiği kadarıyla):
1. **Rıza penceresi içeriği tamamen kapatıyor ve kaydırmayı kilitliyor**; reddet yolu yok (`detay-1440-ilk.png`). Bu bir gelir modeli kararı (bkz. `siteler/spiegel.md`); BH için tasarım dersi değil.
2. Diğer ayrıntılar pencere yüzünden **ölçülmedi**.
