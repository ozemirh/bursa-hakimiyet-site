# Özgür Kocaeli — tasarım çözümlemesi

- İnceleme: **2026-10-20, 10:38–10:43 TSİ** · **tek ölçüm, 2026-10-20, Türkiye, başsız Chrome, çerez kabul edilmedi** · yerel gazete (başka il): sıralama/puan yoktur.
- Koşul: 1440×900 (DPR 1) / 390×844 (DPR 2, mobil + dokunma); UA değiştirilmedi; önbellek kapalı; işletim sistemi koyu temada — site açık temayla çizildi.
- Erişim: robots.txt 2026-10-20'de yeniden okundu, değişiklik yok. Kapalı yollar tarayıcı içinde engellendi: `/service/advertchannels` (her yüklemede), `/api/v1/entry/scrollids/…` (detayda sonraki haber akışı).
- İzin pencereleri: tam ekran "Google kaynak tercihi" penceresi **×** ile, veri politikası şeridi "Kapat" ile kapatıldı; ikisi de onay değil. Kapatmadan önceki hâl: `*-ilk-bantli.png` (8 görüntü). `anasayfa-390` ilk yüklemede betik gizli menünün kapat düğmesine bastığı için bir kez yeniden çekildi.
- Yükleme: 9 + robots.txt 1.
- İncelenen: [anasayfa](https://www.ozgurkocaeli.com.tr/) · [ekonomi](https://www.ozgurkocaeli.com.tr/kocaeli-ekonomi-haberleri) · [haber detayı](https://www.ozgurkocaeli.com.tr/haber/29010758/gebze-6-parselin-imar-plani-degisti-planlar-askiya-cikti) · [nöbetçi eczane](https://www.ozgurkocaeli.com.tr/kocaeli-nobetci-eczaneler)
- Görüntüler: `referans-kutuphanesi/ham/ekran/ozgur-kocaeli/`. İşlevsel çözümleme: `siteler/ozgur-kocaeli.md`. Yöntem: `tasarim/haberturk.md` başı.
- Not: detay görüntülerinde muhabir adı ve portresi görünüyor; kütüphaneye yazılmadı (README kişisel veri kuralı).

## 1. Tipografi

- **İki aile, görev ayrımıyla:** başlık/görüntü ailesi Gotham (Black ve Bold kesimleri; site kendi alanından sunuyor) + metin/arayüz Roboto (Google Fonts). 1440 anasayfada metnin %91'i Roboto; 390'da kart başlıkları Gotham Bold'a geçiyor (%54).
- **Ölçek:**

| kademe | 1440 | 390 |
|---|---|---|
| detay H1 (Gotham Black) | **54,6/60,1**, harf aralığı −1,68 px | 39,2/44,7, −1,18 px |
| detay spot (Roboto 500) | 23,1/32,2 | 22,4/30,4 |
| manşet başlığı (görsel içi, Gotham 900) | 31–59 px | 26/31,2 |
| kart başlığı | 20,7/25,9/600 Roboto | 19/24,7/500 Gotham Bold |
| bölüm H1 ("Ekonomi") | 28/700 Roboto | 28/700 |
| gövde | ölçülmedi (Roboto, ~600 px sütun görüntüde) | ölçülmedi |

- Gövde paragrafı ölçülemedi: metin `p` dışındaki öğelerde; ölçütün yakaladığı `p` alt bilgiye ait (14 px). Görüntüde gövde sütunu ≈ 600 px (`parca/detay-1440-tam-900-2600.png`); punto, satır aralığı ve karakter/satır **ölçülmedi**.
- Detayda başlık-spot farkı belirgin: 54,6 Black → 23,1 Medium → gövde Regular (`detay-1440-ilk.png`).

## 2. Renk

- **Kimlik rengi lacivert** `rgb(21,51,134)`: başlık bandı, menü, mobil başlık, kategori hapı (yarı saydam lacivert `rgba(21,51,134,0.7)`, 11/700, 5 px köşe — 22 adet) (`anasayfa-1440-ilk.png`, `parca/anasayfa-1440-tam-850-2900.png`).
- Sayfa zemini açık mavi-gri `rgb(227,233,238)`; kartlar beyaz/açık gri `rgb(234,234,234)`.
- Vurgu: sarı (manşet görsel metinleri, "seri ilanlar" bandı tam sarı zemin), kırmızı (manşet üst satırı), mavi bağlantı (eczanede ilçe adı `rgb(0,131,193)`).
- Bilgi taşıyan renk: piyasa oklarında yeşil/kırmızı; eczanede ilçe başlıkları mavi (gruplama).

## 3. Izgara ve ritim

- Kapsayıcı **984–1.008 px**; detay ve bölüm sayfaları beyaz "kâğıt" panel (1.008 px) gri zemin üstünde (`detay-1440-ilk.png`).
- Anasayfa: manşet tam genişlik (974 px) + solda 1–6 numaralı dikey sekme; altında 4'lü eşit kart; sonra 3 sütun + sağ ray 328 px ("Çok okunan / Çok konuşulan" sekmeli).
- Detay: ~600 px gövde + 346 px sağ ray.
- Ayraç: beyaz kart blokları arası 10–16 px gri boşluk; bölüm başlıklarında 1 px alt çizgi.

## 4. Kart dili

- Görsel: 16:9 (43) ve 1:1 (37); köşe 0; gölge yok; kart zemini açık gri ya da beyaz.
- Başlık görselin **altında** (4'lü şerit, 20,7/600); kategori hapı görselin sol altına biniyor (`parca/anasayfa-1440-tam-850-2900.png`).
- Manşet: görsele basılmış metin + sağda/üstte büyük sarı başlık; yatay sayfalayıcı 1–25 + "1. Sayfa" (`parca/anasayfa-1440-tam-850-2900.png`) ve ilk ekranda dikey 1–6 sekme (`anasayfa-1440-ilk.png`).
- Saat: son dakika şeridinde gri saat + başlık (`ss:dd`); detayda "19 Eki 2026 - 13:38" kısaltılmış ay.

## 5. Başlık hiyerarşisi (ilk ekran, 1440)

- Lacivert başlık (194 px) → son dakika şeridi → **servis çubuğu** (il seçici, hava, İlan, Rehber, Sinema, Trafik, namaz vakti geri sayımı, 4 piyasa kalemi) → manşet (330 px'ten) → 4'lü kartın görselleri (`anasayfa-1440-ilk.png`). 16 başlık kademesi sayıldı; en baskını görsel içi manşet metni.
- Detay: tarih + kategori → H1 (336 px) → spot → muhabir satırı → görsel; içerik ilk ekranda başlıyor, reklam yok (`detay-1440-ilk.png`).

## 6. Gezinme ve kabuk

- Masaüstü: lacivert tek blok — solda WhatsApp ihbar hattı, ortada logo (548–815 px), sağda sosyal simgeler; altında ince ayraçla 8 bölüm (Gotham, beyaz) + "Menü". Eczane sayfasında ikinci satırda beyaz **servis alt menüsü** (Sinemalar, Şehir Rehberi, Hava, Seri İlanlar, Eczaneler, Lig Fikstürü, Namaz Vakti, Gazete Manşetleri) (`eczane-1440-ilk.png`).
- Masaüstünde yapışkan başlık yok. Mobilde 85 px sabit lacivert başlık; detayda altta 44 px sabit paylaşım + yazı boyutu çubuğu (`detay-390-ilk.png`).

## 7. Mobil (390)

- Detay ilk ekran: lacivert başlık → son dakika → tarih/kategori → H1 (39 px Black, 4 satır) → Google News düğmesi → spot → muhabir; görsel ilk ekranın altında (`detay-390-ilk.png`).
- Dokunma hedefleri: anasayfada ilk iki ekrandaki 55 öğenin **35'i 24 px altı** (kategori hapları, küçük bağlantılar).
- Tek sütuna iniş: 4'lü şerit tek sütuna, servis çubuğu menüye taşınıyor.

## 8. Rafine ↔ kaba

İyi işlenmiş:
1. **Başlık için ayrı aile, metin için ayrı aile** — Gotham Black H1 + Roboto spot/gövde; detay hiyerarşisi tek bakışta okunuyor (`detay-1440-ilk.png`, 54,6 → 23,1 px).
2. **Servis çubuğu** — il, hava, namaz geri sayımı, piyasa tek 56 px satırda, manşetin hemen üstünde (`anasayfa-1440-ilk.png`).
3. **Eczane: ilçeye göre gruplu liste** — mavi ilçe başlığı, gri kart, sağda biçimli telefon + küçük "Yol tarifi" (`eczane-1440-ilk.png`).

Kaba duran:
1. **Görsel içi manşet metni** — üç farklı renk/boyutta basılmış başlık, sayfa tipografisinden kopuk (`anasayfa-1440-ilk.png`).
2. **25'li sayfalayıcı** — 1–25 rakam + "1. Sayfa" düğmesi tek satırda sıkışık (`parca/anasayfa-1440-tam-850-2900.png`).
3. **Mobilde küçük hedefler** — 55 hedefin 35'i 24 px altı (`anasayfa-390.json`).
