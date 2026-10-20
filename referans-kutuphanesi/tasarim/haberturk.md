# Habertürk — tasarım çözümlemesi

- İnceleme: **2026-10-20, 10:39–10:43 TSİ** · tek ölçüm, Türkiye, başsız Chrome 155 (UA değiştirilmedi), çerez **kabul edilmedi**
- Koşul: 1440×900 (DPR 1) ve 390×844 (DPR 2, mobil + dokunma öykünmesi); önbellek kapalı; temiz profil. İşletim sistemi koyu temada olduğundan tarayıcı `prefers-color-scheme: dark` bildirdi; Habertürk açık temayla çizildi (gövde/başlık zemini beyaz ölçüldü).
- Erişim: robots.txt 2026-10-20'de yeniden okundu, değişiklik yok (yalnız `*` bölümü). Robots'ta kapalı yollar ana alan adında tarayıcı içinden engellendi: `/ayar`, `/infinite/kategori/p2/ekonomi`, `/infinite/news/…` — sonsuz akış bu yüzden ikinci habere geçmedi.
- Çerez penceresi: anasayfada "Reddet" ile kapatıldı (`anasayfa-*-ilk-bantli.png` kapatmadan önceki hâl). Bölüm ve detay yüklemelerinde pencere geç geldi, kapatılamadı; sol altta (1440) / alt %22'de (390) duruyor.
- Yükleme: 8 (anasayfa 2×2, ekonomi 2, detay 2) + robots.txt 1.
- İncelenen: [anasayfa](https://www.haberturk.com/) · [ekonomi](https://www.haberturk.com/ekonomi) · [ekonomi haber detayı](https://www.haberturk.com/ekonomi/fon-yasasi-teklifi-bugun-tbmm-genel-kurulu-nda-3920983)
- Görüntüler: `referans-kutuphanesi/ham/ekran/haberturk/` (depoya girmez). İşlevsel çözümleme: `siteler/haberturk.md`.
- Yöntem: `getComputedStyle`; karakter/satır = paragraf iç genişliği ÷ aynı yazı tipiyle `canvas.measureText` ortalama karakter genişliği; zemin payı ilk üç ekranın alanıyla ağırlıklı (iç içe öğeler ayrı sayılır, kaba bir gösterge).

## 1. Tipografi

- **Tek aile:** metnin %99,8'i Poppins (geometrik sans); yazı tipi dosyaları sitenin kendi alanından geliyor. Ağırlıklar 400 · 700 · 900 (+ mobilde 600). Serif yok, büyük harf dönüşümü (`text-transform`) kullanılmıyor; bölüm başlıkları ("RESMİ İLANLAR" vb.) metnin kendisi büyük yazılmış (`anasayfa-1440-tam.png`, parça `parca/anasayfa-1440-tam-900-3000.png`).
- **Ölçek (px, boyut/satır/ağırlık):**

| kademe | 1440 | 390 |
|---|---|---|
| bölüm adı (sayfa H1, "Ekonomi") | 36/40/900 | 20/28/900 |
| detay H1 | 30/36/900 | 24/32/900 |
| manşet kartı başlığı (görsel üstü) | 30/36/700 beyaz | 20/28/700 |
| liste kartı başlığı | 20/32/700 (68 adet) | 14/24/700 (54 adet) |
| bölüm başlığı | 20/—/900 | 20/—/900 |
| spot (detay, `h2`) | 16/24/400 **kırmızı** | 16/24/400 |
| gövde | 16/24/400 | 16/24/400 |
| tarih/üst bilgi | 12/16/400 | 12/16/400 |

- **Gövde:** 16/24 Poppins, sütun 626 px ≈ **79 karakter/satır** (1440); 390'da 42 kar./satır ([detay](https://www.haberturk.com/ekonomi/fon-yasasi-teklifi-bugun-tbmm-genel-kurulu-nda-3920983), `detay-1440-ilk.png`). Satır aralığı 1,5.
- Gözlem: ölçek dar — detayda H1 (30) ile gövde (16) arasında yalnız spot (16, renkle ayrışıyor) var; hiyerarşiyi punto değil **ağırlık (900) ve renk** kuruyor.

## 2. Renk

- Metin rengi payı: siyah `rgb(0,0,0)` %83–94; beyaz (görsel üstü başlıklar) %3–15; kırmızı ve yeşil %0,5–3.
- Zemin: sayfa kenarları açık gri `rgb(243,244,246)`, içerik kutuları beyaz. Logo kırmızı blok.
- **Renk bilgi taşıyor:** piyasa şeridinde değer yeşil (artış) / kırmızı (düşüş) + ok simgesi ([ekonomi](https://www.haberturk.com/ekonomi), `bolum-ekonomi-1440-ilk.png`). Spot kırmızısı ise yalnız vurgu (bilgi taşımıyor).
- Kategori/bölüm renk kodu **yok**; bölüm kimliği büyük bölüm adıyla veriliyor.

## 3. Izgara ve ritim

- Ortalanmış kapsayıcı 1280 px; içerik sütunu 970 px (sol 235 → sağ 1205); iki yanda 160 px sabit sayfa giydirme reklamı (`anasayfa-1440-ilk.png`).
- Anasayfa: 4'lü eşit ızgara (231 px kart, 16 px aralık; sütun izleri 240/490/740/980 px). Detay: 642 px makale + 300 px sağ ray (`ASIDE`, sticky).
- Bölüm ayracı: **çizgi değil boşluk + ince yatay hat** — bölüm başlığından "TÜMÜ" bağlantısına uzanan 1 px açık gri çizgi (`parca/anasayfa-1440-tam-900-3000.png`). `hr` yok.
- Sayfa boyu: anasayfa 13.045 px (1440), 15.844 px (390).

## 4. Kart dili

- Görsel oranları (1440 anasayfa, sayılan görsel): 1:1 ×23, 16:9 ×21, dikey ~1:2 ×18 (dikey video kartları). Köşe yuvarlama **0** (64/64), gölge yok, çerçeve yok (122/127 kart).
- **Başlık görselin üstünde**, alt kısma koyu degrade ile; liste kartlarında görselin altında. Başlık çoğunlukla **"…" ile kesiliyor** (ör. 4'lü sürmanşet, `anasayfa-1440-ilk.png`).
- Manşet görsellerinin bir kısmında başlık **görselin içine basılmış** (sarı/beyaz büyük harf metin; `bolum-ekonomi-1440-ilk.png`).
- Kategori etiketi kartlarda yok; saat gösterimi anasayfada yok (`saat` deseni 0 eşleşme), ekonomi bölümünde 22 saat damgası (KAP listesi).

## 5. Başlık hiyerarşisi (ilk ekran)

- Anasayfa 1440: ilk ekranda tek kademe — 6 başlık, hepsi 20/700 beyaz görsel üstü. İlk ekranın %28'i 970×250 reklam (`anasayfa-1440-ilk.png`). Manşet (kaydırıcı, 1–20 numaralı) 676 px'ten başlıyor.
- Detay 1440: H1 539 px'te, görsel 895 px'te — H1'in üstünde reklam (250 px) + 11 kalemlik piyasa şeridi + breadcrumb. Göz akışı: reklam → piyasa rakamları → başlık.

## 6. Gezinme ve kabuk

- Üstte yapışkan piyasa şeridi 41 px + yapışkan başlık 48 px (logo ortada 80×48, solda arama + "TV Canlı", sağda il/hava + menü). Kaydırınca **89 px** (1440 ve 390'da ekranın %10'u) sabit kalıyor (`yapiskan_kaydirinca` ölçümü, scrollY 2.025–2.160).
- Bölüm/detay sayfalarında piyasa şeridi yok, başlık 48 px; bölüm adı büyük yazıyla menünün solunda — **bölüm sayfasında kabuk bölümün adını taşıyor** (`bolum-ekonomi-1440-ilk.png`).
- Detayda makale altında 56 px yapışkan araç çubuğu (anasayfa, yazı boyutu, paylaş, favoriler). 390 detayda ayrıca 100 px yapışkan reklam: kaydırınca sabit öğeler toplam **204 px = ekranın %24'ü**.

## 7. Mobil (390)

- İlk ekran (anasayfa): piyasa 41 + başlık 48 + yatay kayan menü → 320×100 reklam → 2'li sürmanşet kaydırıcısı → sponsor bandı → manşet görseli (`anasayfa-390-ilk.png`). Okunur başlık: 3.
- Tek sütuna iniş: 4'lü ızgara 3'lü kaydırıcıya (167 px kart), 1:1 manşet 350 px tam genişliğe iniyor.
- Dokunma hedefleri: ilk iki ekrandaki 67 etkileşimli öğenin **25'i 24 px'ten küçük** (WCAG 2.5.8 alt sınırı; aralık istisnası hesaba katılmadı).

## 8. Rafine ↔ kaba

İyi işlenmiş:
1. **Bölüm adı kabuğun parçası** — 36/900 bölüm adı menüyle aynı satırda; okur nerede olduğunu logo boyutunda görüyor (`bolum-ekonomi-1440-ilk.png`, H1 36/40/900).
2. **Piyasa değerinde renk + ok birlikte** — renk körü okur için de yön okunur (`bolum-ekonomi-1440-ilk.png`).
3. **Reklam yeri önceden ayrılmış ve etiketli** — gövde içi boş kutu "REKLAM" yazılı, CLS'yi önlüyor (`parca/detay-1440-tam-0-2600.png`; CLS 0,013 `siteler/haberturk.md`).

Kaba duran:
1. **Kesik başlıklar** — kart başlıkları "…" ile bitiyor; haberin ne olduğu okunmuyor (`anasayfa-1440-ilk.png`, 4'lü sürmanşet).
2. **Görsele basılmış başlık** — manşette metin piksel olarak resimde; boyut/kontrast denetlenemiyor, ekran okuyucu okuyamıyor (`bolum-ekonomi-1440-ilk.png`).
3. **Detayda başlık ilk ekranın ortasında** — H1 539 px, gövde 1440'ta ilk ekranın altında; üstte reklam + 11 kalem piyasa (`detay-1440-ilk.png`).
