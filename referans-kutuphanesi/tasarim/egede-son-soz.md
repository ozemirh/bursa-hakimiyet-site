# Ege'de Son Söz — tasarım çözümlemesi

- İnceleme: **2026-10-20, 10:38–10:45 TSİ** · **tek ölçüm, 2026-10-20, Türkiye, başsız Chrome, çerez kabul edilmedi** · yerel gazete (başka il): sıralama/puan yoktur.
- Koşul: 1440×900 (DPR 1) / 390×844 (DPR 2, mobil + dokunma); UA değiştirilmedi; önbellek kapalı; işletim sistemi koyu temada — site açık temayla çizildi.
- Erişim: robots.txt 2026-10-20'de yeniden okundu, değişiklik yok. Kapalı yollar tarayıcı içinde engellendi: `/cdn-cgi/*`, `/service/json/infinite/…` (detayda sonsuz akış).
- Çerez bandında yalnız "TAMAM" var → **kapatılmadı** (1440'ta altta 52 px, 390'da 105 px). Anasayfa yüklemelerinde betik gizli mobil menünün "Kapat" düğmesine bastı (görünür etki yok).
- Ekonomi adresi menüdeki bağlantıdan değil platform kalıbından (`/ekonomi`) alındı; sayfa 200 döndü, H1 "Ekonomi".
- Yükleme: 8 + robots.txt 1.
- İncelenen: [anasayfa](https://www.egedesonsoz.com/) · [ekonomi](https://www.egedesonsoz.com/ekonomi) · [haber detayı](https://www.egedesonsoz.com/yamanlara-yeni-yasam-alani-semt-merkezi-ve-kutuphane) · [nöbetçi eczane](https://www.egedesonsoz.com/izmir-nobetci-eczaneler)
- Görüntüler: `referans-kutuphanesi/ham/ekran/egede-son-soz/`. İşlevsel çözümleme: `siteler/egede-son-soz.md`. Yöntem: `tasarim/haberturk.md` başı. Eczane sayfası 34.295 px (1440) / 50.837 px (390); tam görüntü ilk 20.000 px ile sınırlı.
- **Platform notu:** Bursa Saati ile aynı platform; tip ölçeği birebir aynı (Gibson; H1 −2,3 px; kart 17/700; spot 25/300; gövde 20/30). Bu dosya yalnız farkları ayrıntılandırır.

## 1. Tipografi

- Gibson %100. Ölçek Bursa Saati ile aynı; **kapsayıcı daha geniş olduğu için satırlar daha uzun:**

| kademe | 1440 | 390 |
|---|---|---|
| detay H1 | **60/60/700**, −2,3 px | 35/35/700, −0,8 px |
| detay spot | 25/30/300, 1.295 px genişlik | 20/26/300 |
| gövde | 20/30/400, 832 px ≈ **100 kar./satır** | 20/30, 44 kar./satır |
| kart başlığı | 17–20/24/700 | 16–17/700 |
| bölüm adı (siyah şerit) | 28/33,6/700 beyaz | 18/21,6/700 |

([detay](https://www.egedesonsoz.com/yamanlara-yeni-yasam-alani-semt-merkezi-ve-kutuphane), `detay-1440-ilk.png`)

## 2. Renk

- **Kimlik rengi kırmızı** `rgb(217,0,0)`: başlık bandı (70 px), "Son Haberler" başlığı ve çizgisi, piyasa bandı (ekonomide), döviz hesaplayıcı kutusu (`bolum-ekonomi-1440-ilk.png`).
- Metin `rgb(17,24,39)`/`rgb(33,37,41)`; zemin `rgb(233,236,239)` + beyaz bloklar.
- Ekonomi bölümü: siyah bölüm şeridi + beyaz alt kategori satırı + kırmızı piyasa bandı (`bolum-ekonomi-1440-ilk.png`) — aynı platformda Bursa Saati ekonomiyi hardal zeminle veriyor.
- Kategori etiketi: koyu gri `rgb(51,51,51)` kutu, beyaz 12,8/700 — renk kategori kodlamıyor (tek renk) (`detay-1440-ilk.png`, Son Haberler rayı).
- Bilgi taşıyan renk: piyasa yeşil/kırmızı; Son Haberler'de **kalın saat** (`10:36`) başlığın başında.

## 3. Izgara ve ritim

- Kapsayıcı **1.320 px** (sol 73 px) — incelenen yerel siteler içinde en geniş.
- Anasayfa ilk ekran: 4'lü eşit kart şeridi (310 px görsel) → manşet 860 px + sağda 2 yan kart (`anasayfa-1440-ilk.png`).
- Detay: 857 px görsel/gövde + 420 px ray ("Son Haberler", yapışkan değil).
- Ayraç: bölüm başlığı kırmızı yazı + sağa uzanan kırmızı ince çizgi + "…" (`detay-1440-ilk.png`).

## 4. Kart dili

- Görsel: 16:9 baskın; detay görselleri 5:3; köşe 0 (anasayfa), ekonomi listesinde beyaz kart 6,4 px köşe (59).
- Başlık görselin altında, görselin hemen bitiminde 17–20/700, zeminsiz (anasayfa) (`anasayfa-1440-ilk.png`).
- Manşet: görsel üstü beyaz başlık + altta 1–15 numaralı kutucuk şeridi, etkin numara kırmızı (`bolum-ekonomi-1440-ilk.png`). Anasayfa manşetinde başlık görsele basılmış (`anasayfa-1440-ilk.png`).
- Ray kartı: küçük görsel + koyu kategori kutusu + kalın saat + başlık.

## 5. Başlık hiyerarşisi (ilk ekran)

- Anasayfa 1440: kırmızı başlık (70) → beyaz menü (44) → hemen 4'lü kart şeridi; **reklam yok, boşluk yok** — haber 131 px'ten başlıyor. 12 başlık ilk ekranda (`anasayfa-1440-ilk.png`).
- Detay: breadcrumb → H1 160 px'te → spot → künye çubuğu → görsel 462 px'te (`detay-1440-ilk.png`).

## 6. Gezinme ve kabuk

- Kırmızı üst bant: logo (170×51) solda; sağda ilçe+hava, piyasa (tek kalem, döngülü), simgeli kısa yollar (Günün Haberleri, Foto Galeri, Video, Yazarlar), sosyal, arama. Altında beyaz kategori satırı (10 bağlantı, 17/700 koyu) + menü düğmesi.
- Başlık kaydırınca yukarı kayıp gizleniyor (`header-8 sticky-header slideUp`, ölçümde `ust: −70`); sabit öğe yalnız çerez bandı + yukarı çık düğmesi.

## 7. Mobil (390)

- İlk ekran: kırmızı başlık (logo + arama + menü, 70 px) → yatay kayan kategori menüsü → **2×2 görselli kart** → manşet (`anasayfa-390-ilk.png`). İlk ekranda 4 okunur başlık; reklam yok.
- Kart başlıkları 2 satırda "…" ile kesiliyor (aynı görüntü).
- Dokunma: ilk iki ekrandaki 71 öğenin 9'u 24 px altı.

## 8. Rafine ↔ kaba

İyi işlenmiş:
1. **Haber hemen başlıyor** — 1440'ta 131 px, 390'da ~285 px'ten itibaren haber kartı; kabuk ince (`anasayfa-1440-ilk.png`, `anasayfa-390-ilk.png`).
2. **Ray listesinde saat başta, kalın** — `10:36` + başlık; kronoloji göz ucuyla okunuyor (`detay-1440-ilk.png`).
3. **Ekonomi bölüm başı katmanlı** — bölüm şeridi → alt kategoriler → piyasa bandı → manşet + hesaplayıcı; veri ve haber aynı ekranda (`bolum-ekonomi-1440-ilk.png`).

Kaba duran:
1. **Satır uzunluğu** — gövde ≈100, spot 1.295 px genişlikte; 1.320 px kapsayıcı okuma sütununu daraltmıyor (`detay-1440.json`).
2. **60 px H1, −2,3 px aralık, satır aralığı 1,0** — iki satırlık başlıkta harfler sıkışık (`detay-1440-ilk.png`).
3. **Eczane sayfasında liste ilk ekranın altında** — kırmızı başlık şeridinden sonra ~475 px dekoratif "eczane" görseli, ardından il/ilçe seçicileri; sağda 30 ilçe çipi iyi, ama sayfa 111 kayıtla (kayıt başına bir ilçe hapı sayıldı) 34.295 px (`eczane-1440-ilk.png`, `eczane-1440.json`). Aynı dekoratif görsel Bursa Saati'nde de var (platform şablonu).
