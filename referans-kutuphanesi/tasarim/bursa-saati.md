# Bursa Saati — tasarım çözümlemesi

- İnceleme: **2026-10-20, 10:38–10:45 TSİ** · **tek ölçüm, 2026-10-20, Türkiye, başsız Chrome, çerez kabul edilmedi** · yerel rakip: sıralama/puan yoktur.
- Koşul: 1440×900 (DPR 1) / 390×844 (DPR 2, mobil + dokunma); UA değiştirilmedi; önbellek kapalı; işletim sistemi koyu temada — site açık temayla çizildi.
- Erişim: robots.txt 2026-10-20'de yeniden okundu, değişiklik yok. Kapalı yollar tarayıcı içinde engellendi: `/cdn-cgi/*` (her yüklemede), `/service/json/featured-infinite.json` (detayda sonsuz akış besleyicisi).
- İzin pencereleri: bildirim istemi (OneSignal) "Sonra" ile kapatıldı (`*-ilk-bantli.png` öncesi). Çerez bandında yalnız "TAMAM" var → **kapatılmadı**. `anasayfa-1440-ilk.png` ilk sürümde çekildi; kapatma betiği o yüklemede yanlışlıkla gizli mobil menünün "Kapat" düğmesine bastı (zararsız), bildirim istemi bu görüntüde üstte duruyor.
- Yükleme: 9 (anasayfa 390 bir kez yeniden çekildi) + robots.txt 1.
- İncelenen: [anasayfa](https://www.bursasaati.com.tr/) · [ekonomi](https://www.bursasaati.com.tr/ekonomi) · [haber detayı](https://www.bursasaati.com.tr/satsuma-sezonu-baslarken-ihracatta-iki-kritik-sorun) · [nöbetçi eczane](https://www.bursasaati.com.tr/bursa-nobetci-eczaneler)
- Görüntüler: `referans-kutuphanesi/ham/ekran/bursa-saati/`. İşlevsel çözümleme: `siteler/bursa-saati.md`. Yöntem: `tasarim/haberturk.md` başı.
- **Platform notu:** Ege'de Son Söz ile aynı hazır haber platformu (`s.tblsm.com`). İki sitenin tip ölçeği birebir aynı çıktı (bkz. `tasarim/egede-son-soz.md`); farklar kapsayıcı genişliği, başlık rengi ve bölüm teması.

## 1. Tipografi

- **Tek aile:** Gibson (geometrik/hümanist sans; dosyalar platform CDN'inden). Ağırlıklar 300 (spot) · 400 · 600 · 700.
- **Ölçek:**

| kademe | 1440 | 390 |
|---|---|---|
| detay H1 | 40/40/700, **harf aralığı −2,3 px** | 35/35/700, −0,8 px |
| detay spot (`h2.lead`) | 25/30/**300** | 20/26/300 |
| gövde | 20/30/400 | 20/30/400 |
| manşet başlığı (görsel üstü) | 28/33,6/700 | — |
| kart başlığı | 17/24–25,5/700 | 17/24/700 |
| bölüm başlığı | 21,3/700 | 21,3/700 |

- **Gövde:** 20/30 Gibson, sütun 685 px ≈ **81 kar./satır** (1440); 390'da 43. Spot 1.075 px tam genişlikte (≈ 110+ kar./satır) ([detay](https://www.bursasaati.com.tr/satsuma-sezonu-baslarken-ihracatta-iki-kritik-sorun), `detay-1440-ilk.png`).
- Büyük harf dönüşümü: yalnız küçük etiketlerde (künye etiketleri "YAYINLANMA", "OKUMA SÜRESİ" 10,6 px; yazar adları).

## 2. Renk

- Metin: koyu lacivert-siyah `rgb(17,24,39)` / `rgb(33,37,41)` %60–76.
- Zemin: sayfa `rgb(233,236,239)` açık gri-mavi; içerik blokları beyaz; menü çubuğu **siyah**; son dakika şeridi kırmızı `rgb(202,37,39)`.
- **Bölüm teması:** ekonomi sayfasında bölüm şeridi ve sayfa zemini **koyu sarı/hardal** `rgb(211,165,0)` — ilk 3 ekran zemininin %49'u (`bolum-ekonomi-1440-ilk.png`). Ege'de Son Söz aynı platformda ekonomiyi siyah şeritle veriyor → tema site ayarı.
- Bilgi taşıyan renk: son haberler listesinde **kırmızı saat rozeti** (`parca/anasayfa-1440-tam-600-2700.png`); eczanede ilçe hapı mavi, "Yol Tarifi" sarı, telefon kırmızı (eylem türüne göre renk) (`parca/eczane-1440-tam-500-2100.png`).
- Sayfada renk sayısı yüksek: kırmızı, siyah, hardal, mor-mavi degrade (TV bloğu), takım logoları şeridi (`parca/anasayfa-1440-tam-600-2700.png`).

## 3. Izgara ve ritim

- Kapsayıcı **1.100 px** (sol 183 px). Anasayfa: manşet 710 + yan manşet 330; altında 5'li eşit şerit; sağ ray `col-lg-4` 364 px yalnız sayfanın alt kısmında (7.342 px'ten sonra).
- Detay: 685 px gövde + 364 px ray.
- Ayraç: bloklar beyaz kutu, aralarında 16–20 px gri boşluk; bazı bölümler üstte 5 px renkli çizgi (390, `bolum_basliklari` ölçümü). Bölüm başlığından sağa ince çizgi + "…" düğmesi.

## 4. Kart dili

- Görsel: **16:9** baskın (70/94 anasayfa); detay görselleri 5:3 (1,67). Köşe: görsel 0; ekonomi kartları beyaz zeminli **6,4 px yuvarlak köşe** (61 kart, `bolum-ekonomi-1440.json`).
- Başlık: anasayfada görselin **üstünde** (alt degrade), ekonomi listesinde görselin altında beyaz kartta.
- Manşet: görsele basılmış başlık + 1–16 numaralı şerit + "T" (tümü) (`parca/anasayfa-1440-tam-600-2700.png`).
- Yazar kartları: kırmızı daire zeminli yuvarlak portre + başlık üstte (aynı parça).
- Saat: son haberler listesinde kırmızı rozet `ss:dd`; anasayfada 25 saat damgası.

## 5. Başlık hiyerarşisi (ilk ekran)

- 1440 anasayfa: üst reklam (124 px) → logo+piyasa+hava (69 px) → siyah menü (51 px) → 970×120 reklam → ~145 px **boş ayrılmış alan** → son dakika şeridi → piyasa bandı → manşet 648 px'te başlıyor (`anasayfa-1440-ilk.png`). Haber başlığı ilk ekranda yalnız son dakika şeridinde.
- Detay 1440: H1 573 px'te; üstünde iki reklam bandı ve boşluk (`detay-1440-ilk.png`).

## 6. Gezinme ve kabuk

- Kabuk üç kat: reklam bandı → beyaz logo satırı (logo 304×49, sağda gram altın + il seçici + hava) → siyah kategori çubuğu (17/700 beyaz, 10 bağlantı; "Advertorial", "Resmi Reklam", "Künye" ana menüde).
- Yapışkan başlık yok; sabit öğeler: yukarı çık düğmesi + çerez bandı (1440'ta 52 px, 390'da 105 px = %12).

## 7. Mobil (390)

- İlk ekran: 84 px boş reklam alanı → logo (arama ve menü simgeleri logonun **altında**, sola yaslı) → yatay kayan menü → **~285 px boş ayrılmış reklam alanı** → son dakika → piyasa → manşet görselinin üstü (`anasayfa-390-ilk.png`). İlk ekranda tek haber başlığı (son dakika, kesik).
- Eczane 390: ilk ekranın büyük kısmı boş reklam alanı + dekoratif "eczane" görseli; liste ekranın altında (`eczane-390-ilk.png`).
- Dokunma: ilk iki ekrandaki 49 öğenin 12'si 24 px altı.

## 8. Rafine ↔ kaba

İyi işlenmiş:
1. **Künye çubuğu** — tarih/saat, okuma süresi küçük büyük harf etiketlerle sütunlu; paylaşım ve yazı boyutu aynı satırda (`detay-1440-ilk.png`).
2. **Son haberler listesi** — iki sütun, her satırda kırmızı saat rozeti + 17/700 başlık; tarama hızlı (`parca/anasayfa-1440-tam-600-2700.png`).
3. **Eczane kaydı kartı** — ad, ilçe hapı, adres, iki renkli eylem düğmesi; sağda ilçe seçici çipleri (`parca/eczane-1440-tam-500-2100.png`).

Kaba duran:
1. **H1'de −2,3 px harf aralığı ve 1,0 satır aralığı** — 40 px'te harfler birbirine değiyor (`detay-1440-ilk.png`, H1 ölçümü).
2. **Boş ayrılmış reklam alanları** — 1440'ta ~145 px, 390'da ~285 px boşluk ilk ekranı yiyor (`anasayfa-1440-ilk.png`, `anasayfa-390-ilk.png`).
3. **Mobil logo satırı** — arama/menü simgeleri logonun altına düşmüş, hizasız (`anasayfa-390-ilk.png`).
