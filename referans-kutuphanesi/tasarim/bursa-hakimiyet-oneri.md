# Bursa Hakimiyet — rafine tasarım önerisi (ölçüm + ekran görüntüsü)

Son güncelleme: 2026-10-20 · Yazan: `web-tasarim-direktoru` · Durum: **öneri** (kod değişmedi).

Bu belge BH'nin bugünkü hâlini kütüphanedeki altı sitenin (`tasarim/*.md`) aynı yöntemle
alınmış ölçüleriyle yan yana koyar ve **en fazla 12** rafineleştirme önerir. Görsel kimliği
değiştiren her şey sonda "Kullanıcı kararı gerekenler" altındadır; orada karar verilmedi.

## 0. Koşul ve kaynak

- **BH ölçümü:** 2026-10-20, 10:57–11:20 TSİ, yerel geliştirme sunucusu (`127.0.0.1:8793`,
  `--noreload`, veritabanı ana ağacın `.env`'i; okunma yazımı `komut` kipine alındı, yani istekler
  veritabanına yazmadı). Başsız Chrome (`icerik/tests_panel_olcum.Cdp`), önbellek kapalı
  (`Network.setCacheDisabled`), `prefers-color-scheme: light` öykünmesi. 1440×900 (DPR 1) ve
  390×844 (DPR 2, mobil + dokunma). Tembel görseller sayfa kaydırılarak yüklendikten sonra ölçüldü.
- **Ölçüm farkı:** sunucu yerel olduğu için üst şeritte **sunum araçları** ("Reklamları gizle",
  "Test reklamı") görünüyor ve reklam yuvaları gri yer tutucu. Sıradan okurun 390'daki servis
  şeridi yüksekliği **ölçülmedi** (sunum düğmeleri yokken daha kısa olmalı).
- **Veri bayat:** yerel veritabanında son veri 12 Eylül 2026; "güncel değil" uyarıları bu yüzden
  görünüyor (bayat veri gösterim kuralı gereği). Tasarım bulgusu sayılmadı.
- **Sayfalar:** anasayfa `/` · ekonomi `/ekonomi` · haber detay
  `/bursa/bursa-orhangazi-de-500-toki-konutu-icin-kritik-asama-gozler-arsa-kararinda-1696268`
  (yerel, ilçeli, 16 paragraf) · ilçe `/ilce/orhangazi` · teknoloji `/teknoloji` (özel tasarım bölümü için).
- **Görüntüler:** `ham/ekran/bursa-hakimiyet/` (depoya girmez) — her sayfa için `<sayfa>-<1440|390>-ilk.png`,
  `-tam.png` (anasayfa-390 iki parça: `-tam.png` + `-tam-2.png`), ölçüm `-<genişlik>.json`, okunur
  dilimler `parca/<sayfa>-<genişlik>-tam-<y1>-<y2>.png`.
- **Yöntem:** kütüphaneyle aynı (`tasarim/haberturk.md` başı): `getComputedStyle`; karakter/satır
  iki yolla — **gerçek** (paragraf harf harf `Range.getClientRects` ile satıra bölünüp son satır
  hariç ortalama) ve **canvas** (iç genişlik ÷ `measureText` ortalaması). İlk ekran başlık sayısı:
  görünür, metni ≥ 25 karakter `a`. Kırpma: `object-fit: cover` görselde kutu oranı ↔ doğal oran,
  kayıp = 1 − küçük/büyük oran.

---

## 1. Yan yana karşılaştırma

### 1.1 Tipografi ölçeği (px: punto/satır/ağırlık)

| Kademe | **BH 1440 · 390** | Spiegel | Özgür Kocaeli | Habertürk | Bursa Saati / Ege | Bursada Bugün |
|---|---|---|---|---|---|---|
| Manşet (görsel üstü) | 42/44,5/900 Condensed · 26/27,6 | — | 31–59 (görsele basılı) | 30/36/700 | 28/33,6 | görsele basılı |
| Detay H1 | **34/37,1/900**, −0,3 · 25/27,3 | 44/47,5/800 · 32 | 54,6/60,1 · 39,2 | 30/36/900 · 24 | 40/40 · 60/60, −2,3 | 40/50/700 |
| Detay spot | **17/26,4/400 serif** · aynı | — | 23,1/32,2/500 | 16/24 kırmızı | 25/30/300 | 20/30 |
| Gövde | **18/29,9/400 serif** · aynı | 20/30 serif · 18/27 | ölçülmedi | 16/24 | 20/30 | 16/28 |
| Kart başlığı | liste 18/20,9 · dörtlü 21/24,4 · geniş 26/29,1 · mobil 17 | 20/25,2 (mobilde aynı) | 20,7/600 · 19 | 20/32 · 14/24 | 17/24 | 16/26/600 |
| Kart özeti | anasayfa 12,5 · bölüm 14/20,3 | 16/22,1 | — | — | — | — |
| Bölüm başlığı (h2) | 18/900 (hafif) · 16,5/700 (dolu) · +5 başka biçim (§1.5) | 32/34,6 küme | 28/700 | 20/900 | 21,3/700 | 30/36/600 |
| Bölüm sayfası H1 | **30/700 Roboto (biçimsiz, tarayıcı varsayılanı)** | 36/38,9 slab | 28/700 | 36/40/900 | 28 · 18 (390) | 30/36/600 |

Oranlar: **H1 ÷ gövde** BH 1,89 (Habertürk 1,88 · Bursa Saati 2,0 · Spiegel 2,2). **Spot ÷ gövde**
BH **0,94** — spot gövdeden *küçük* ve aynı ailede (Bursa Saati 1,25 · Bursada Bugün 1,25 · Habertürk
1,0 ama renkle ayrışıyor · Özgür Kocaeli spotu ayrı ağırlık ve ailede). Kanıt: `detay-1440.json`
(`tip.detay_spot`, `govde`), `detay-1440-ilk.png`, `detay-390-ilk.png`; referans
`ozgur-kocaeli/detay-1440-ilk.png`.

Aile payı (detay 1440): Roboto %42,7 · Roboto Serif %38,6 · Roboto Condensed %18,7 — üç aile, üç
görev (Spiegel modeli). `detay-1440.json` `aile_payi`.

### 1.2 Satır başına karakter (detay gövdesi, gerçek ölçüm)

| | BH | Spiegel | Habertürk | Bursa Saati | Bursada Bugün | Ege |
|---|---|---|---|---|---|---|
| 1440 | **71,5** (68–75; canvas 75), sütun 684 px | ≈70 · 624 px | 79 · 626 | 81 · 685 | 85 · 647 | 100 · 832 |
| 390 | **32,8** (29–39; canvas 37), sütun 340 px | 44 (tasarım) / ~38 (desen) | 42 | 43 | — | 44 |
| Paragraf arası | 14 px (satır 29,9) | 24 px (satır 30) | — | — | — | 17 |
| Spot satırı | 74 · 390'da 33,8 (9 satır, 237 px) | — | — | ≈110+ | ≈100+ | ≈1.295 px |

Masaüstünde BH rahat okuma bandının (60–75) içinde ve yerel rakiplerin hepsinden iyi; **390'da en
düşük** (33): `.detay` 14 px iç dolgu + 18 px serif 340 px'lik sütunda 33 karaktere iniyor.
Kanıt: `detay-1440.json` / `detay-390.json` → `govde`, `spot_satir`; `parca/detay-1440-tam-0-2600.png`.

### 1.3 Izgara ve dikey ritim

| | BH | Referans |
|---|---|---|
| Kapsayıcı | 1.100 px (sol 163) | Bursa Saati 1.100 · Özgür 1.008 · Habertürk 970 içerik · Spiegel 960 · Ege 1.320 |
| Ana ızgara | anasayfa `762 + 18 + 320`, detay `758 + 22 + 320` → **ray dikişi iki sayfada da x = 943** | Habertürk 642+300 · Bursa Saati 685+364 · Ege 857+420 |
| Ana bloklar arası | 16 px (anasayfada 9 aralığın 8'i 16; reklam→günün manşetleri 14) | Özgür 10–16 gri boşluk · Bursa Saati 16–20 |
| Bölüm/ilçe akışı | `530 + 14 + 530` ikili / üçlü ritim, ray yok (§46) | Spiegel tek sütun + kümeler |

Kanıt: `anasayfa-1440.json`, `detay-1440.json` (`izgara`), ayrı ritim ölçümü (bu belge §0 koşulu).

### 1.4 Kart dili ve görsel oranı

| | BH | Referans |
|---|---|---|
| Kart | köşe 0, gölge yok, 1 px `--cizgi` kenar, beyaz kart `--zemin` tepsisinde | 5/6 sitede köşe 0, gölge yok |
| Başlık | görselin altında, tam, metin; **kesik başlık 0** (10 ölçümün hepsinde) | Habertürk, Bursada Bugün, Ege 390 "…" ile kesiyor |
| Görsele basılı başlık | yok | Habertürk, Özgür, Ege, Bursa Saati, Bursada Bugün'de var |
| Etiket | `.kart .ust` 11/700 büyük harf, kırmızı (anasayfa) · lacivert (ekonomi) · `--isaret-bursa` (ilçe) + gri saat | Özgür lacivert hap · Ege koyu gri kutu |
| Oran | bölüm/ilçe listesi **3:2, kırpılan 0** · anasayfa, detay ilgili haberler, Bursaspor şeridi, video kartı **sabit yükseklik + kırpma** (§2 R1) | Spiegel 3:2 (mobil 4:3) |

### 1.5 Başlık hiyerarşisi (anasayfa 1440, h2 biçimleri)

Aynı kademedeki (bölüm başlığı) h2 **7 ayrı biçimde**: `.kutu-bas.hafif` 18/900 lacivert, beyaz zemin,
2 px lacivert alt çizgi + kırmızı fitil (Yazarlar, Son haberler, Bursa ilçeleri, Galeriler, Videolar) ·
`.kutu-bas` dolu lacivert 16,5/700 (Şehir servisleri, Vizyonda) · `.kutu-bas.vurgu` dolu kırmızı (En çok
okunanlar) · dolu yeşil (Bursaspor — kimlik, bilinçli) · son dakika plakası 14,5/900 · "Günün manşetleri"
11,5/900 kırmızı yazı · "Resmî ilanlar" 14/900 açık zeminde. Detay rayında ayrıca dolu lacivert
("Orhangazi haberleri") + dolu kırmızı ("En çok okunanlar") yan yana. Referans: Ege tek biçim (kırmızı
başlık + ince çizgi), Habertürk tek biçim (20/900 + 1 px hat), Spiegel çizgisiz. Kanıt:
`parca/anasayfa-1440-tam-0-2600.png`, `parca/anasayfa-1440-tam-2600-5200.png`,
`parca/detay-1440-tam-0-2600.png`.

### 1.6 Renk kullanımı

- **Metin rengi payı (anasayfa 1440):** `--gri` %32,4 · `--murekkep` %29,3 · `--lacivert` %22,6 ·
  beyaz %4,4 · `--kirmizi-koyu` %3,0. Detayda `--murekkep` %71. İkincil (gri) metin anasayfada
  birincil metinden fazla (tarih, özet, tablo, adres); Spiegel'de ikincil %9–12.
- **Zemin payı (ilk 3 ekran, anasayfa 1440):** `--zemin` ≈%47 · `--kagit` %30,7 · `--foto-bekleme`
  + `--reklam-zemin` %14 (yer tutucular) · `--gece` %4,3 (slayt penceresi).
- **Bilgi taşıyan renk:** piyasa cetvelinde yön rengi + ok + kural yazılı, bayatlık uyarısı tablonun
  üstünde (`bolum-ekonomi-1440-ilk.png`) — Habertürk şeridinde veri zamanı yok
  (`haberturk/bolum-ekonomi-1440-ilk.png`). Kategori işareti iki renkle sınırlı (§35).
- **Kontrast (hesaplandı):** `--kirmizi`/`--kagit` 4,60 (eşiğe çok yakın; kart etiketi 11 px bunu
  kullanıyor) · `--kirmizi`/`--zemin` **4,06 (AA altı — bu çift metinde kullanılmamalı)** ·
  `--gri`/`--kagit` 5,50 · `--gri`/`--zemin` 4,85 · `--lacivert`/`--kagit` 13,21.

### 1.7 İlk ekran ve mobil kabuk

| Ölçü | **BH** | Referans |
|---|---|---|
| 1440 anasayfa: ilk haber başlığı / ilk büyük görsel | dörtlü başlıkları **609** · görsel 444; önünde 250 px reklam şeridi + 62 px piyasa | Ege 131 · Bursada Bugün ~189 · Özgür ~330 · Habertürk 428 · Bursa Saati 648 |
| 1440 anasayfa: ilk ekran başlık sayısı | **4** | Ege 8 · Bursa Saati 6 · Habertürk 11 · Bursada Bugün 11 · Özgür 13 |
| 1440 detay: H1 üst kenarı | **478** · gövde 1.336'da (ilk ekranın altında) | Ege 160 · Özgür 336 · Habertürk 539 · Bursa Saati 573 |
| 1440 ekonomi: bölüm adı / ilk bölüm haberi | **846 / 1.051** | Ege ~114 / ~283 (`egede-son-soz/bolum-ekonomi-1440-ilk.png`) · Habertürk adı kabukta (~80) |
| 390 kabuk (kaydırmadan) | servis 66 (sunum düğmeleriyle) + `.kategori` 82 + reklam yer tutucu 44 → içerik **206**'da | Ege 70 + menü · Habertürk 89 + reklam |
| 390 kaydırınca sabit | **82 px = %9,7** (yalnız `.kategori`) — beş sayfada aynı | Habertürk 89 (%10), detayda 204 (%24) · Özgür 85 (+44 detay) · Ege 0 (gizleniyor) |
| 390 anasayfa: ilk ekran okunur başlık | **1** (manşet, y = 406); dörtlü **2.066**'da, iki 300×250 ve son dakikadan sonra | Ege 4 (2×2) · Habertürk 3 · Bursa Saati 1 |
| 390 manşet denetimi | 15 numara **iki satır, 96 px** (slayt 250 + 96) | Ege tek satır ince çizgi göstergesi |
| 390 detay: H1 / ilk görsel / gövde | 363 / 797 / 1.221 (H1 + spot ilk ekranda) | Özgür: H1 + spot ilk ekranda |
| 390 ekonomi: ilk bölüm haberi | **1.466**, ilk ekranda 0 başlık (ekranı piyasa cetveli dolduruyor) | Ege ekonomi bandı tek satır |
| 24 px altı dokunma hedefi (ilk 2 ekran, 390) | anasayfa 1/47 · detay 1/27 · ekonomi 2/24 · **ilçe 3/40** (eczane `a.tel` 78×18, `a.harita` 87×18) · "İçeriğe atla" 1×1 (odakta açılır, sayılmaz) | Habertürk 25/67 · Özgür 35/55 · Bursa Saati 12/49 · Ege 9/71 |

Kanıt: `anasayfa-1440-ilk.png`, `anasayfa-390-ilk.png`, `detay-1440-ilk.png`, `detay-390-ilk.png`,
`bolum-ekonomi-1440-ilk.png`, `bolum-ekonomi-390-ilk.png`, ilgili `.json` (`ilk_haber_basligi`,
`ilk_ekran_baslik_sayisi`, `sabit_kaydirinca_1500`, `dokunma`).

---

## 2. Korunacaklar (BH'nin zaten iyi yaptıkları)

1. **Okuma sütunu.** 18/29,9 serif, 684 px, gerçek ölçümde **71,5 kar./satır** — incelenen yerel
   sitelerin hepsinden (79–100) iyi, Spiegel'le (≈70) aynı bantta. `.metin{max-width:38em}`
   dokunulmasın. `detay-1440.json` `govde`.
2. **Üç aile, üç görev.** Condensed başlık · Roboto arayüz · Serif gövde/spot; dördüncü aile yok.
   `detay-1440.json` `aile_payi`.
3. **Başlık tam ve metin.** 10 ölçümde kesik başlık 0, görsele basılı başlık yok; incelenen altı
   siteden beşinin düştüğü iki kusur BH'de yok (tek istisna kırıntı, R10).
4. **Köşesiz, gölgesiz kart; tepsi zemini.** Beyaz kart `--zemin` tepsisinde — 20 kartın duvar gibi
   okunmasını önleyen §29 Ağustos çözümü; Özgür Kocaeli'nin beyaz kart + gri zemin düzeniyle aynı yön.
5. **Ray dikişi.** Anasayfa ve detayda sağ ray x = 943, genişlik 320 — sayfa boyunca kayma yok.
6. **Dikey ritim.** Ana bloklar arası 16 px (bir istisna 14) — tek ölçek.
7. **Renk bilgi taşıyor.** Piyasa cetvelinde yön rengi + ok + yazılı kural + bayatlık uyarısı +
   kaynak/bülten no (`bolum-ekonomi-1440-ilk.png`) — referanslardaki en sıkı örnek.
8. **Mobil yapışkan kabuk %9,7.** Kaydırınca yalnız 82 px'lik bant kalıyor; Habertürk detayının
   %24'ünün çok altında. Dokunma hedeflerinde 24 px altı neredeyse yok (ilçe sayfası hariç, R12).
9. **Bölüm/ilçe listesinde 3:2, kırpma 0.** Kullanıcı kararı (`liste-izgara`, §64) bu sayfalarda
   tam uygulanmış (`bolum-ekonomi-1440.json`, `ilce-1440.json` → `kirpilan` yalnız video kartı).

---

## 3. Rafineleştirilecekler (12 madde)

Biçim: **Sorun** (BH ölçüsü + görüntü) → **Referans çözüm** → **Öneri** (değişken/sınıf düzeyinde)
→ **Etki** · **Emek** · **Öncelik** · **Uygulayacak**.

### R1 — Kart görseli kırpılmasın kararı anasayfa ve detayda uygulanmamış

- **Sorun.** Liste sayfaları 3:2'ye çekilmiş ama başka yüzeyler hâlâ sabit px yükseklik +
  `object-fit: cover` (`site.css`, 20 Ekim 2026 sürümü; seçiciler tabloda):

  | Yüzey | Seçici | 1440 kutu → kayıp | 390 kutu → kayıp |
  |---|---|---|---|
  | Anasayfa dörtlü | `.dortlu .kart .foto` 132 px | 1,99 → **%24** | 2,79 → **%46** |
  | Anasayfa son haberler | `.son-haberler .kart .foto` 185 px | 1,94 → %23 | 1,85 → %19 |
  | Bursaspor şeridi | `.bursaspor-haber .kart .foto` 140 px | 1,54 → %2 | 2,44 → **%39** |
  | Detay ilgili haberler | `.kart .foto` 150 px | 2,38 → **%37** | 2,28 → %34 |
  | Detay ana görsel | `.ana-gorsel` 420 / 210 px | 1,70 → %12 | 1,62 → %7 |
  | Video kartı (16:9 kaynak) | `.video-kart .foto` 150 px | 1,71 → %10 | ekonomi 390'da 1,09 → **%43** |

  Görüntü: `parca/anasayfa-390-tam-1700-3400.png` (dörtlüde yüzler alnından ve çenesinden kesik),
  `parca/detay-1440-tam-2600-3684.png`. Ölçü: `*.json` → `kirpilan_gorseller`.
- **Referans.** Spiegel kartı 3:2'de tutuyor, başlığı altta (`tasarim/spiegel.md` §4); BH'nin kendi
  `.liste-izgara .kart:not(.genis) .foto` çözümü (`aspect-ratio: 3/2`).
- **Öneri.** `:root`'a `--cerceve-orani: 3/2` (renk değil, oran) ve `--video-orani: 16/9`. Yukarıdaki
  seçicilerde `height` yerine `height:auto; aspect-ratio: var(--cerceve-orani)`; video/galeri
  `.foto-bag` için `var(--video-orani)`. Mobilde dikey boyu büyütmemek için **≤600'de dörtlü ve
  ilgili haberler** mevcut `.yatay` kart düzenine geçsin (görsel solda 112 px, 3:2 → 75 px yükseklik,
  başlık sağda) — 3:2 korunur, kart 245 px yerine ~90 px olur. Hava/namaz panelindeki dekoratif
  servis fotoğrafları (`.hava-foto`, `.vakit-foto`) haber görseli değil; kapsam dışı.
- **Etki.** Kullanıcı kararına uyum; haberin fotoğrafı eksik görünmez. 1440 dörtlü +44 px (ilk
  ekranda kalır); detay ana görsel 420 → 475 px. **Emek** M · **Öncelik P0** ·
  **Uygulayacak** `frontend-gelistirici`; kırpılan haber görseli = 0 sözleşme testi → `test-kalite-muhendisi`.

### R2 — Bölüm/ilçe sayfası H1'i biçimsiz

- **Sorun.** `kategori.html:65` `<h1>` için kural yok; tarayıcı varsayılanına düşüyor: **30/700
  Roboto** (2 × 15 px gövde). Sitedeki bütün başlıklar `--display`/`--tema-baslik-aile`'de;
  sayfanın en önemli başlığı arayüz ailesinde (`bolum-ekonomi-1440.json`, `ilce-1440.json` →
  `tip.sayfa_h1`; `bolum-teknoloji-390-ilk.png`). `.ilan-dizin .kutu-bas h1` ve
  `.kose-sayfa-bas h1` kuralı var, bu yok.
- **Referans.** Habertürk bölüm adı 36/900 (`haberturk/bolum-ekonomi-1440-ilk.png`); Spiegel 36 slab.
- **Öneri.** `.bolum > .kutu-bas h1 { font-family: var(--tema-baslik-aile); font-weight: 900;
  font-size: 32px; letter-spacing: .3px; line-height: 1.1 }`, ≤600'de 26 px — `.kose-sayfa-bas h1`
  ile aynı ölçek (tek kaynak olsun diye ikisi tek kurala bağlanabilir).
- **Etki.** Bölüm kimliği temanın başlık ailesiyle (ekonomi/teknoloji temalarında da) okunur.
  **Emek** S · **Öncelik P0** · **Uygulayacak** `frontend-gelistirici`.

### R3 — Detay başlık bloğu: spot gövdeden küçük, hiyerarşi ters

- **Sorun.** Spot 17/26,4 serif 400, gövde 18/29,9 serif 400 → spot ÷ gövde **0,94**; spotu gövdeden
  ayıran tek şey soldaki 4 px fitil. 390'da spot 9 satır, 237 px — H1'den (82 px) üç kat uzun ve
  gövdenin ilk paragrafı gibi okunuyor (`detay-390-ilk.png`, `detay-1440-ilk.png`).
- **Referans.** Özgür Kocaeli: 54,6 Black → spot 23,1 Medium → gövde Regular; kademe tek bakışta
  (`ozgur-kocaeli/detay-1440-ilk.png`). Bursa Saati/Bursada Bugün spotu gövdeden 1,25 kat büyük.
- **Öneri (aile değişmez).** Roboto Serif yerelde 400–700 değişken yüklü (`fontlar.css` 78–90);
  `.detay .spot { font-weight: 500; font-size: 20px; line-height: 1.45 }` (≥1001), ≤600'de
  `17px` + `font-weight: 500` (gövde R11 ile 17 px'e iner; ayrım ağırlıkla). Fitil `--tema-isaret`
  kalır. İsteğe bağlı: `.detay h1` 34 → 38 px (H1 ÷ gövde 2,1; Spiegel 2,2) — 712 px sütunda ortalama
  başlık yine iki satır.
- **Etki.** H1 → spot → gövde üç kademe; okur spotu "haberin özeti" olarak tanır. **Emek** S ·
  **Öncelik P1** · **Uygulayacak** `frontend-gelistirici` (§35 "spot serif" kuralı korunuyor; plan
  değişikliği gerekmez).

### R4 — Bölüm başlığı (h2) yedi biçimde; iki kademeye indir

- **Sorun.** §1.5: anasayfada aynı kademe 7 biçim; detay rayında dolu lacivert ile dolu kırmızı yan
  yana. Renk burada bilgi taşımıyor ("En çok okunanlar" neden kırmızı, "Vizyonda" neden lacivert
  dolu, "Galeriler" neden hafif?) — `klasik-gorsel-dil` ilkesine aykırı.
- **Referans.** Ege tek biçim (kırmızı yazı + sağa uzanan ince çizgi), Habertürk tek biçim (20/900 +
  1 px hat → "TÜMÜ"), Spiegel hiyerarşiyi tipografiyle kuruyor (`tasarim/egede-son-soz.md` §3,
  `tasarim/haberturk.md` §3).
- **Öneri.** İki kademe:
  1. **Sayfa başı** (dolu çubuk, `--tema-bant` / `--tema-bant-vurgu`): yalnız sayfanın H1'i
     (bölüm adı, ilçe adı) ve kimlik blokları (Bursaspor `--yesil`, son dakika plakası — bunlar
     haber sinyali, başlık değil).
  2. **Bölüm başı** (`.kutu-bas.hafif`: 18/900 `--tema-koyu`, kırmızı fitil, 2 px alt çizgi): geri
     kalan her h2 — Şehir servisleri, Vizyonda, En çok okunanlar, Günün manşetleri, Resmî ilanlar,
     detaydaki İlgili haberler ve ilçe haberleri.
  "En çok okunanlar"da kırmızı, sıra numaralarında zaten var (bilgi taşıyan yerde kalır).
- **Etki.** Sayfa "rastgele renkli kutular" yerine tek gazete sayfası gibi okunur; kırmızı yalnız
  sinyal (son dakika, sıra, fitil). **Emek** M · **Öncelik P1** · **Uygulayacak** `frontend-gelistirici`.
  Kırmızı alanın azalması görünür bir değişiklik → **Kullanıcı kararı K4**.

### R5 — 390'da manşet denetimi iki satır, 96 px

- **Sorun.** 15 numaralı düğme 390'da iki satıra kırılıyor; manşet bloğunun %28'i (96/348 px)
  sayfalayıcı (`anasayfa-390-ilk.png`). 1440'ta 41 px, sorun yok.
- **Referans.** Ege 390'da görselin altında tek satır ince çizgi göstergesi
  (`egede-son-soz/anasayfa-390-ilk.png`); Özgür'ün 25'li sayfalayıcısı kütüphanede "kaba" diye
  işaretli (`tasarim/ozgur-kocaeli.md` §8).
- **Öneri.** ≤600'de `.slayt-denetim` tek satır: "1 / 15" sayacı + önceki/sonraki düğmeleri (44 px
  hedef); numaralar `flex-wrap: nowrap; overflow-x: auto` ile yatay kayan tek satır. `aria-*` ve
  klavye gezinmesi aynen; `prefers-reduced-motion` kuralı korunur.
- **Etki.** ~50 px kazanç; ilk ekranda manşet + bir sonraki blok başlar. **Emek** S · **Öncelik P1**
  · **Uygulayacak** `frontend-gelistirici`.

### R6 — 390 anasayfa ilk ekranında tek başlık; dörtlü 2.066 px'te

- **Sorun.** 390'da ilk ekranda okunur başlık 1 (Ege 4, Habertürk 3). Sıra: manşet → 300×250 → son
  dakika → 300×250 → dörtlü (y = 2.066) (`parca/anasayfa-390-tam-0-1700.png`,
  `parca/anasayfa-390-tam-1700-3400.png`).
- **Referans.** Ege 390: kabuktan hemen sonra 2×2 kart, sonra manşet (`egede-son-soz/anasayfa-390-ilk.png`).
- **Öneri.** ≤600'de dörtlü manşetin hemen altına, R1'deki `.yatay` kompakt biçimde (4 × ~90 px);
  1440 düzeni değişmez. Uygulama yolu `.ust-blok` içinde `order` (şablon sırası ve ekran okuyucu
  sırası ayrışmasın diye tercihen şablonda dar ekran sırası).
- **Etki.** 390'da ilk iki ekranda 5 başlık. **Emek** M · **Öncelik P1** · **Uygulayacak**
  `frontend-gelistirici`. Reklam yuvalarının görünürlüğünü değiştirir → **Kullanıcı kararı K2**.

### R7 — Bölüm başı sırası: bölüm adı ve haber ilk ekranın altında

- **Sorun.** Ekonomi 1440: reklam → kırıntı → piyasa cetveli + Bursa ekonomisi → **bölüm adı 846** →
  ilk bölüm haberi 1.051 (`bolum-ekonomi-1440-ilk.png`, `parca/bolum-ekonomi-1440-tam-0-2600.png`).
  390'da ilk ekranı cetvel dolduruyor, ilk bölüm haberi **1.466** (`bolum-ekonomi-390-ilk.png`).
  Teknolojide aynı: Bursa'da teknoloji listesi + 5 satırlık seçim kuralı → "TEKNOLOJİ" başlığı
  (`bolum-teknoloji-390-ilk.png`). İlçede eczane kutusu bölüm adının üstünde (`ilce-1440-ilk.png`).
- **Referans.** Ege ekonomi: bölüm şeridi → alt kategoriler → **tek satır** piyasa bandı → manşet,
  hepsi ilk ekranda (`egede-son-soz/bolum-ekonomi-1440-ilk.png`); Habertürk bölüm adını kabukta
  taşıyor (`haberturk/bolum-ekonomi-1440-ilk.png`).
- **Öneri.**
  1. Sayfa H1'i (R2 biçimiyle) kırıntının hemen altına; tema `bas` yuvası ve servis şeridi onun
     altında kalır.
  2. ≤600'de ekonomi `bas` yuvası: cetvelin yerine ilk ekranda anasayfadaki `.doviz` bandı
     (`parca/doviz.html`, tek satır, yön rengi + ok) + "Piyasa cetvelinin tamamı" açılır
     (`<details>`); 1440'ta cetvel aynen.
  3. Seçim kuralı notları (`.yer-not`) ≤600'de mevcut `details.yer-not` desenine ("Bu liste nasıl
     seçildi?") — metin silinmez, katlanır.
- **Etki.** Okur "neredeyim" ve "rakam nerede" sorusunu tek ekranda yanıtlar; 390'da ilk bölüm haberi
  ~1.466 → ~700. **Emek** M · **Öncelik P1** · **Uygulayacak** `frontend-gelistirici`. Servis
  şeridinin "bölüm kutusunun üstünde" yeri §59'da kullanıcı kararı → **Kullanıcı kararı K3**.

### R8 — Bölüm akışında ikili satır: görsel büyük, başlık küçük

- **Sorun.** Ekonomi/ilçe ikili satırında kart 530 px, 3:2 görsel ~506×337, altında 18/20,9 başlık ve
  14 px özet; 900 px'lik ekranda yalnız 2 haber (`parca/bolum-ekonomi-1440-tam-0-2600.png`,
  `parca/ilce-1440-tam-0-2600.png`). Görsel/metin oranı anasayfa dörtlüsünden (21 px başlık) zayıf.
- **Referans.** Spiegel kart ölçeği: 3:2 görsel + 20/25,2 başlık + 16/22 özet; başlık görseli
  taşıyacak ağırlıkta (`tasarim/spiegel.md` §1, §4).
- **Öneri.** §60 ritmi (ikili/üçlü) korunur, kart içi ölçek değişir: ikili satırda `.liste-izgara
  .kart h3` 21/24,4 (dörtlüyle aynı), `.kart p` 15/21; üçlüde 18 kalır. Satır başına kart başlık
  satır aralığı 1,16 → 1,2 (çok satırlı Condensed başlıkta sıkışmayı açar).
- **Etki.** Bölüm akışı "fotoğraf albümü" değil haber listesi gibi okunur. **Emek** S · **Öncelik
  P2** · **Uygulayacak** `frontend-gelistirici`.

### R9 — Mobil gövde 33 kar./satır ve sıkı paragraf aralığı

- **Sorun.** 390'da gövde 32,8 kar./satır (incelenen sitelerin en düşüğü; Habertürk 42, Ege 44);
  paragraf arası 14 px, satır aralığı 29,9 — paragraf sınırı satır boşluğundan zor ayrılıyor
  (`detay-390.json` `govde`, `parca/detay-390-tam-1700-3400.png`).
- **Referans.** Spiegel 18/27 mobil, paragraf arası 16 (masaüstünde 24/30) (`tasarim/spiegel.md` §1).
- **Öneri.** ≤600: `.metin { font-size: 17px }`, `.detay` yatay iç dolgu 14 → 12 px → ≈40 kar./satır;
  her genişlikte `.metin p { margin-bottom: .9em }` (18 px'te ~16). `data-boyut` (A−/A+) kademeleri
  aynı oranla kayar.
- **Etki.** Telefonda satır kırılması azalır, sayfa ~%15 kısalır. **Emek** S · **Öncelik P2** ·
  **Uygulayacak** `frontend-gelistirici`; satır ölçümü → `test-kalite-muhendisi`.

### R10 — Kırıntıda kesik başlık

- **Sorun.** `haber_detay.html:24` `truncatechars:60` → "…Gözler arsa kararında" yerine "Gözle…";
  390'da kırıntı 2 satır, 78 px (`detay-1440-ilk.png`, `detay-390-ilk.png`). Başlık zaten 20 px
  altında H1 olarak tam duruyor.
- **Referans.** Kütüphane dersi 3 ("başlık kesilmemeli", `desenler/tasarim-dili.md` §0); Özgür
  Kocaeli detayında başlığın üstünde yalnız tarih + bölüm (`ozgur-kocaeli/detay-1440-ilk.png`).
- **Öneri.** Son öğe (`aria-current="page"`) görsel olarak gizlensin (mevcut `gorsel-gizli`
  sınıfı), DOM'da ve `BreadcrumbList` JSON-LD'de tam başlıkla kalsın; kırıntı tek satır.
- **Etki.** 390'da ~42 px kazanç, tekrarlanan kesik metin kalkar. **Emek** S · **Öncelik P2** ·
  **Uygulayacak** `frontend-gelistirici`; JSON-LD dokunulmadığının denetimi → `seo-buyume-uzmani`.

### R11 — Anasayfa kart özeti 12,5 px ve gri metin payı

- **Sorun.** Anasayfa kart özeti 12,5 px `--gri` (bölümde 14); anasayfada gri metin payı %32,4,
  birincil metinden (%29,3) fazla (`anasayfa-1440.json` `metin_renk_payi`). Küçük + gri metin
  `--zemin` tepsisine yakın kartlarda 4,85 kontrastla duruyor.
- **Referans.** Spiegel kart özeti 16/22, ikincil metin %9–12 (`tasarim/spiegel.md` §1–2).
- **Öneri.** `.kart p` tabanı 14/20 (bölümle aynı); özet yalnız geniş kartta ve yazar kartında,
  dörtlü/son haberler küçük kartlarında özet yok (zaten yok) — gri yalnız zaman ve kaynak gibi
  meta bilgide.
- **Etki.** Anasayfa ikincil metin okunur hâle gelir. **Emek** S · **Öncelik P2** · **Uygulayacak**
  `frontend-gelistirici`.

### R12 — İlçe sayfası eczane eylemleri 18 px yükseklik

- **Sorun.** `a.tel` 78×18, `a.harita` 87×18 — WCAG 2.5.8 alt sınırı 24 (`ilce-390.json` `dokunma`;
  `ilce-390-ilk.png`). Telefonda en çok dokunulacak bağlantılar bunlar.
- **Referans.** Bursa Saati eczane kartında eylem düğmeleri (`tasarim/bursa-saati.md` §8);
  BH'nin kendi çözümü `.detay-kunye .yazan a { padding:4px 0; margin:-4px 0 }`.
- **Öneri.** Aynı negatif kenar boşluklu dolgu: `.eczane-izgara .tel, .eczane-izgara .harita`
  (`parca/bolum_servis.html` 136, 139) `display:inline-block; padding:5px 0; margin:-5px 0`
  → ≥ 28 px, satır yüksekliği değişmez.
- **Etki.** Dokunma hedefi denetimi beş sayfada da temiz. **Emek** S · **Öncelik P1** ·
  **Uygulayacak** `frontend-gelistirici`.

### Öncelik özeti

| # | Kısa | Öncelik | Emek | Sahip |
|---|---|---|---|---|
| R1 | Kırpma kararını anasayfa/detay/Bursaspor/video kartına uygula | **P0** | M | frontend + test-kalite |
| R2 | Bölüm/ilçe H1'ine başlık ailesi ve ölçek | **P0** | S | frontend |
| R3 | Spot > gövde (serif 500, 20 px), isteğe bağlı H1 38 | P1 | S | frontend |
| R4 | Bölüm başlığı 7 biçim → 2 kademe | P1 | M | frontend (K4) |
| R5 | 390 manşet denetimi tek satır | P1 | S | frontend |
| R6 | 390'da dörtlü manşetin altına, yatay kart | P1 | M | frontend (K2) |
| R7 | Bölüm başı: önce ad, mobilde tek satır piyasa | P1 | M | frontend (K3) |
| R12 | Eczane eylem hedefleri ≥ 24 px | P1 | S | frontend |
| R8 | Bölüm ikili satırında başlık 21 px | P2 | S | frontend |
| R9 | Mobil gövde 17 px, paragraf arası .9em | P2 | S | frontend + test-kalite |
| R10 | Kırıntıda kesik başlığı gizle | P2 | S | frontend + seo |
| R11 | Kart özeti 14 px | P2 | S | frontend |

Her madde uygulandıktan sonra denetim: 360 · 768 · 1024 · 1280 · 1600'de ölçüm + ekran görüntüsü
(`web-tasarim-direktoru`), `icerik/tests_yerlesim.py` (ray 320) yeşil.

---

## 4. Özel tasarım sayfaları (ekonomi, teknoloji)

Bursaspor yapıldı (yeşil–beyaz, `body[data-bolum="bursaspor"]`). Kural: ayrışma **kâğıt
rengiyle değil** (sarı/somon/fildişi reddedildi) düzen, tipografi ve çubuk rengiyle; üst kabuk değişmez.

**Ekonomi (kategori 4) — bugün:** lacivert çubuklar, PİYASA CETVELİ + BURSA EKONOMİSİ yan yana,
bölüm adı `--lacivert-koyu` vurgu çubuğunda (`bolum-ekonomi-1440-ilk.png`). Renk dili doğru (yön
rengi yalnız değişim sütununda). Eksik olan **yapı**:
1. Sayfa başı sırası R7 (ad → tek satır piyasa → manşet; cetvel ikinci kademe).
2. Alt konu satırı (Ege'nin sektör satırı gibi) — Bursa'ya özgü sektörler (otomotiv, tekstil, tarım,
   BTSO) **yalnız** sitede gerçek bir hedef sayfası varsa; etiket sayfası olmadığı için şimdilik
   yok. Hangi sektörler → `haber-muduru`.
3. Rakamlar Condensed + `font-variant-numeric: tabular-nums` (cetvel sütunları alt alta hizalı);
   cetvel 390'da kalem başına iki satır (`Alış · Satış` alta) iyi, korunur.
4. Enstrüman sayfası gelirse tek çizgi grafik (FT "zaman içinde değişim" → çizgi), her grafik ne
   gösterdiğini yazıyla söyler (`desenler/ekonomi-sayfasi.md`). Yeni renk gerekmez: çizgi
   `--tema-dolgu`, artış/azalış `--artis` / `--kirmizi-koyu`.

**Teknoloji (kategori 9) — bugün:** grafit takımı (`--grafit`, `--grafit-koyu`, `--grafit-ak`,
`--grafit-zemin`, `--grafit-cizgi`; kontrastlar `site.css` yorumunda ölçülü), BURSA'DA TEKNOLOJİ
listesi + uzun seçim kuralı ilk ekranda (`bolum-teknoloji-1440-ilk.png`, `bolum-teknoloji-390-ilk.png`).
1. Seçim kuralı R7.3 ile katlansın; liste ilk ekranda kalsın (Bursa önce).
2. Spiegel `/tests/` kümeleme **ilkesi** (ürün testi değil): onaylı ve süren konu dosyası varsa
   (ör. TEKNOFEST, yapay zekâ, Bursa sanayisinde dönüşüm) 1–2 küme — 1 büyük + 3 küçük kart; konu
   dosyası yoksa yuva çizilmez. "Süren konu" tanımı → `haber-muduru`, konu verisi → `yapay-zeka-uzmani`.
3. Grafit dolu çubuk yalnız sayfa başında; iç başlıklar R4'ün hafif kademesinde, fitil `--tema-fitil`.

**Köşe yazıları** da seçili sayfalar arasında; bu turda ölçülmedi.

---

## 5. Kullanıcı kararı gerekenler (karar verilmedi)

- **K1 — Üst reklam şeridinin haber detaydaki yeri.** Her sayfada haberin üstünde 250 px (970×250,
  §42 eki 2 kullanıcı kararı). Detayda H1'i **478 px**'e, gövdeyi 1.336 px'e itiyor (Ege 160, Özgür
  336, Habertürk 539, Bursa Saati 573). Seçenekler: (a) aynen; (b) detayda şerit künye/ana görselin
  altına (H1 ≈ 228'e çıkar); (c) detayda yalnız 1100×150 / 728×90 (150 px; H1 ≈ 378); (d) 250 px
  yalnız anasayfa ve bölüm sayfalarında. Gelir kararı; tasarım tercihi (b).
- **K2 — Mobil anasayfada blok sırası (R6).** Dörtlünün "Manşet yanı 300×250"nin önüne alınması
  reklam yuvasının görünürlüğünü aşağı iter.
- **K3 — Bölüm sayfasında başlık ↔ servis şeridi sırası (R7).** §59'da kullanıcı "servis şeridi
  kırıntının hemen altında, bölüm kutusunun üstünde" dedi; bölüm adını şeridin üstüne almak bu
  sırayı değiştirir (şerit yine haber akışının üstünde kalır).
- **K4 — Kırmızı dolu başlıkların hafif başlığa dönmesi (R4).** "En çok okunanlar" ve detay rayındaki
  kırmızı dolu çubuk kalkınca sayfadaki kırmızı alan görünür biçimde azalır; kimlik renkleri
  değişmiyor ama ağırlıkları değişiyor. Önce/sonra görüntüsüyle gösterilmeli.
- **Önerilmeyenler (bilinçli):** yazı ailesi değişikliği yok (R3 aileyi değil ağırlığı değiştirir;
  spotun sans'a geçmesi istenirse §35'i değiştirir → kullanıcı); logo bölgesine dokunulmadı; renk
  değeri değişikliği yok; koyu tema yok ("beyaz kalsın").

---

## 6. Alan dışı gözlemler (devir)

- Detayda seslendirme kutusu okura kırmızı teknik not gösteriyor ("Bu tarayıcıda yalnızca sistemin
  standart Türkçe sesi bulundu…", `parca/detay-1440-tam-0-2600.png`); seslendirme yönü artık yerel
  model → `yapay-zeka-uzmani`.
- Arşivden gelen başlıkların bir kısmı "…" ile bitiyor ("Gözler arsa kararında...", "Zara, Eypio...")
  — kesilmiş başlık gibi okunuyor; panelde yeni haberler için kural → `haber-muduru`.
- `--kirmizi` `--zemin` üstünde 4,06 (AA altı): bu çiftin metinde kullanılmadığının taraması →
  `test-kalite-muhendisi`.

## 7. Kopyalama notu

Rakiplerin logosu, simgesi, yazı tipi dosyası, CSS'i, fotoğrafı veya başlığı alınmadı; yalnız
çözüm tarif edildi. BH'nin kendi değişken ve sınıf adları kullanıldı; yeni önerilen iki değişken
(`--cerceve-orani`, `--video-orani`) renk değil, oran.
