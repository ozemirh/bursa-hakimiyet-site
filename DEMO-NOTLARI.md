# Demo Tasarımları — Notlar ve Devam Rehberi

> Son güncelleme: 22 Ağustos 2026 (demo derinleştirme turu)

---

## 1. Nerede kaldık

Üç tasarım yönü prototip olarak hazır. Her biri Bursa Hakimiyet'in gerçek logosu ve 18-21 Ağustos 2026 Bursa gündeminden derlenmiş içerikle çalışıyor.

**Karar bekleyen:** Hangi yönde ilerleneceği. Üç yön de artık sunuma hazır: her birinin **anasayfası zenginleştirildi**, **haber detay sayfası** çıkarıldı ve **etkileşimleri çalışır** hâle getirildi.

**Yapılan son değişiklik (22 Ağustos 2026):**
- `gorseller/` klasörü eklendi — Wikimedia Commons'tan 23 telifsiz/CC Bursa fotoğrafı, üç oranda hazır (`genis/` 1280×720, `kart/` 640×400, `kare/` 240×240). Lisanslar `gorseller/KAYNAKLAR.md` içinde.
- Üç anasayfa da kategori bölümleri, köşe yazarları, reklam yer tutucuları ve zenginleştirilmiş footer ile dolduruldu.
- Üç haber detay sayfası üretildi: `tasarim-1-haber-detay.html`, `tasarim-2-haber-detay.html`, `tasarim-3-haber-detay.html`. Üçü de Bozbey haberini işliyor.
- Menü açılır alt menüleri, mobil menü, arama/filtre, okuma ilerleme çubuğu ve sayfalar arası gerçek linkler çalışıyor.
- Tasarım 3'te tema tercihi `localStorage`'da saklanıyor ve iki sayfada da geçerli.

---

## 2. Üç yön

| | 1 · Klasik | 2 · Hibrit | 3 · Modern |
|---|---|---|---|
| Referans | Sözcü, Olay | ikisinin ortası | global editoryal siteler |
| Tanıdıklık | Yüksek | Orta-yüksek | Düşük |
| Farklılaşma | Düşük | Orta | Yüksek |
| Reklam alanı | Geniş | Orta | Dar |
| Risk | Düşük | Düşük | Orta |

**Yön 1 — Klasik.** Kayan son dakika şeridi, üç kolonlu manşet bloğu, çok okunanlar, resmi ilanlar. Lacivert + kırmızı, condensed başlıklar.
*İmza öğeler:* 17 ilçelik navigasyon şeridi, sekmeli hava/namaz/eczane kutusu.

**Yön 2 — Hibrit.** Aynı iskelet, serif başlık, kart yapısı, daha çok boşluk.
*İmza öğeler:* Üstteki tıklanabilir ilçe filtresi, manşet altındaki "3 maddede ne oldu" kutusu, sesli dinle butonu.

**Yön 3 — Modern.** Manşet fotoğrafı değil, başlığın kendisi hero. Bursa yeşili, koyu tema düğmesi, mono zaman damgaları.
*İmza öğeler:* Yatay kaydırmalı ilçe kartları, "Arşive sor" kutusu, açık/koyu tema.

**Öneri:** Yön 2 temel alınsın, Yön 3'ün arşiv araması sonraki aşamada üstüne eklensin. Lansmanda risk düşük kalır, farklılaşma kademeli gelir.

---

## 3. Dosya anatomisi

Her dosya aynı sırayla kurulu:

```
<head>
  Google Fonts linkleri
  <style>
    :root { CSS değişkenleri }
    temel sıfırlama
    .foto ve tema sınıfları (.t-mavi, .t-kirmizi ...)
    bileşen stilleri
    @media kırılma noktaları
  </style>
<body>
  <svg> SVG symbol kütüphanesi (görünmez) </svg>
  üst servis şeridi
  logo bandı
  ana menü
  içerik
  footer
  <script> küçük etkileşimler </script>
```

### CSS değişkenleri

**Tasarım 1**
```
--lacivert #1B2A6B   --lacivert-koyu #111B47   --kirmizi #E4222B
--murekkep #14181D   --gri #606A75   --cizgi #DFE3E8
--zemin #EEF1F4      --kagit #FFFFFF
--display  Roboto Condensed      --govde  Roboto
```

**Tasarım 2**
```
--murekkep #12181F   --gri #5B6672   --gri-acik #8B97A3
--kirmizi #D51C24    --lacivert #1B2A6B   --deniz #0E6E6E
--cizgi #E3E8EC      --yuzey #FFFFFF      --zemin #F4F6F8
--serif  Source Serif 4          --sans  Inter
```

**Döviz bandı.** Üç tasarımda da `.doviz` sınıfıyla, her yönün kendi diline göre: Tasarım 1'de İLÇELER şeridini yansılayan yoğun şerit, Tasarım 2'de menü altında ferah satır, Tasarım 3'te mono tipografik çizgi. Artış/azalış renkleri Tasarım 1 ve 2'de yeni `--artis` değişkeninden, Tasarım 3'te mevcut `.artis` / `.dusus` sınıflarından geliyor.

> Dikkat: Tasarım 3'te `.zaman` zaten zaman çizelgesinin sınıfı ve `border-left` taşıyor. Döviz bandındaki tarih bu yüzden `.tarih` sınıfını kullanıyor — `.zaman` demeyin.

**Tasarım 3** — `html[data-tema="koyu"]` altında tüm değişkenler yeniden tanımlı
```
--yesil #0B3D2E      --yesil-parlak #127A57   --kirmizi #D51C24
--murekkep #101210   --kagit #FBFBF9   --yuzey #FFFFFF
--gri #5E655E        --cizgi #E2E4DF
--display  Bricolage Grotesque   --okuma  Newsreader   --mono  IBM Plex Mono
```

### Ortak sınıflar

| Sınıf | İşlev |
|---|---|
| `.kapsa` | Sayfa genişliği sınırlayıcı (1240 / 1180 / 1300 px) |
| `.foto` | Görsel kutusu — içine SVG oturur |
| `.t-*` | Görsel renk teması (`.t-mavi`, `.t-kirmizi`, `.t-yesil`, `.t-gri`, `.t-turuncu`, `.t-mor`) |
| `.manset` | Ana haber bloğu |
| `.kart` / `.mini` | Haber kartları |
| `.bolum-bas` / `.bolum` | Bölüm başlığı + ayraç çizgisi |
| `.sira` / `.top-liste` | Çok okunanlar |

### SVG görsel kütüphanesi

`<body>` başında görünmez bir `<svg>` içinde `<symbol>` olarak tanımlı. Kullanımı:

```html
<div class="foto t-mavi"><svg><use href="#sc-baraj"/></svg></div>
```

Mevcut semboller:

| id | Konu |
|---|---|
| `#sc-uludag` | dağ / hava durumu |
| `#sc-cami` | şehir silueti |
| `#sc-gol` | göl / su seviyesi |
| `#sc-fabrika` | sanayi |
| `#sc-adliye` | hukuk / yargı |
| `#sc-yangin` | yangın |
| `#sc-baraj` | baraj |
| `#sc-ulasim` | toplu ulaşım |
| `#sc-muze` | kültür / arkeoloji |
| `#sc-saglik` | hastane |
| `#sc-spor` | spor |
| `#sc-tarim` | tarım |
| `#sc-market` | market / denetim |
| `#sc-kaza` | trafik |

Renkler symbol içinde `var(--s1)` … `var(--s5)` ile geliyor; `.t-*` sınıfı bunları belirliyor. Yeni sembol eklerken aynı 5 slotu kullan.

### Görsel oranları

Gerçek fotoğraf geldiğinde aynı kutulara oturacak:

- Manşet: **16:8.4**
- Kart: **16:10**
- Hero (tasarım 3): **4:3.4**
- Küçük kart (tasarım 1): sabit 132px yükseklik

### Kırılma noktaları

| Tasarım | Noktalar |
|---|---|
| 1 | 1000px (tek kolon), 600px (mobil) |
| 2 | 980px (tek kolon), 640px (mobil) |
| 3 | 1120px (yan kolon daralır), 880px (tek kolon) |

### JavaScript

Toplam 10 satırın altında, her dosyada bir tane:

- **Tasarım 1:** hava/namaz/eczane sekmeleri
- **Tasarım 2:** ilçe filtresi çipleri
- **Tasarım 3:** açık/koyu tema düğmesi

---

## 4. İçerik hakkında

Haber başlıkları 18-21 Ağustos 2026 Bursa gündeminden derlenip yeniden yazıldı — başka sitelerden kopyalanmadı. Kapsanan konular: Bozbey'in CHP'den istifası, baraj doluluğunun %81'e gerilemesi, İznik Gölü kuraklık uyarısı, Mudanya yangını, sıcaklık uyarısı, Matlı enerji yatırımı, iplik firması iflası, hastane açılış takvimi, müze projesi, market denetimi, İnegöl'deki kaza.

**Yer tutucu olanlar — gerçek veriyle değiştirilecek:**

- Yazar isimleri (`Yazar adı` yazıyor) — gazetenin gerçek köşe yazarları girilecek
- Nöbetçi eczane bilgisi — Sağlık Müdürlüğü verisiyle beslenecek
- Namaz vakitleri — örnek değerler
- Resmi ilanlar — örnek kayıtlar
- Telefon numarası (`0224 000 00 00`)

**Manşet notu:** Bozbey haberinde "suçlamaları reddediyor" ifadesi bilinçli olarak spot metinde tutuldu. Devam eden yargılama içeren haberlerde bu kalıbın demo aşamasında bile görünmesi, canlıya geçince editör ekibi için hazır bir alışkanlık oluşturur.

---

## 5. Bilinen eksikler

| Eksik | Not |
|---|---|
| Logo vektörel değil | Elimizde JPEG var; gazeteden SVG/AI sürümü istenmeli. Retina ekranlarda kenarlar yumuşak görünüyor |
| Kategori / ilçe / yazar sayfaları yok | Anasayfa ve haber detay hazır; kalan şablonlar seçim sonrası çıkarılacak |
| Fotoğraflar gazetenin değil | `gorseller/` içindekiler Commons kaynaklı yer tutucu. Canlıya geçerken gazete arşiviyle değişecek; CC BY / CC BY-SA olanlar künye ister |
| Google Fonts dışa bağımlı | İnternetsiz açılınca yedek fontlara düşer, düzen bozulmaz |
| Arama sayfa içiyle sınırlı | Yazdıkça o sayfadaki başlıkları süzüyor; gerçek arşiv araması arka uç ister |
| Menü içerikleri örnek | Açılır alt menüler çalışıyor, ama içindeki linkler `#` — hedef sayfalar henüz yok |
| Döviz bandı statik | Değerler **gerçek**: 21 Ağustos 2026 ECB referans kurları (USD 48,07 · EUR 56,23 · GBP 65,64) ve o günkü USD/TRY ile hesaplanmış gram altın. Ama sayfaya gömülü, kendiliğinden güncellenmez — canlıda bir kur servisine bağlanması gerekir. BIST 100 yok, güvenilir ücretsiz kaynak bulunamadı |
| "Arşive sor" arka planı yok | Tasarım 3'teki kutu görsel; gerçek arama altyapısı gerektirir |

---

## 6. VS Code'da nasıl devam edilir

### Kurulum

Ekstra kurulum gerekmiyor. Klasörü VS Code'da aç, dosyaya sağ tıkla → tarayıcıda aç. Canlı yenileme istersen "Live Server" eklentisi yeterli.

### Ajanla çalışma

`.claude/agents/haber-sayfasi-gelistirici.md` bu tasarımlar için tanımlı uzman ajandır — proje kurallarını, görsel yerleştirme düzenini ve erişilebilirlik zorunluluklarını içinde taşır. İş verirken **her ajana tek bir tasarım dosyası** ver; üç yön birbirinin alternatifi olduğu için tek ajana üçünü birden verme.

### Claude ile çalışma

`CLAUDE.md` dosyası Claude'un her oturumda okuduğu kural dosyası — proje bağlamını baştan anlatmana gerek kalmıyor. Bir kural değişirse orayı güncelle.

### İyi istek örnekleri

**Belirsiz:** "Tasarımı düzelt."
**Net:** "`tasarim-2-hibrit.html` dosyasında manşet başlığı mobilde çok büyük duruyor. 640px altında yazı boyutunu küçült, başka yere dokunma."

**Belirsiz:** "Detay sayfası yap."
**Net:** "`tasarim-2-hibrit.html` ile aynı stil değişkenlerini kullanarak bir haber detay sayfası oluştur: manşet görseli, başlık, spot, 3 maddede özet kutusu, gövde metni, ilgili haberler. Yeni dosya adı `tasarim-2-haber-detay.html`."

**Faydalı kalıplar:**
- "Değiştirmeden önce ilgili CSS bloğunu göster, ne yapacağını anlat."
- "Bu değişiklik hangi kırılma noktalarını etkiler?"
- "Yeni bir SVG sembolü ekle: [konu]. Mevcut 5 renk slotunu kullan."

### Sıradaki işler

1. **Tasarım yönünü seç** — yayın ekibiyle üç anasayfayı ve üç detay sayfasını birlikte gez
2. **İlçe sayfası** — 17 ilçenin şablonu; yerel arama görünürlüğünün merkezi burası
3. **Kategori ve yazar sayfaları** — seçilen yönün stiliyle
4. **Yazar isimlerini gerçekle değiştir**
5. **Fotoğrafları gazete arşiviyle değiştir** — `gorseller/` içindekiler yer tutucu
6. **Vektörel logo** — gazeteden iste, base64'ü güncelle

### Dikkat

- Dosyalarda logo base64 olarak gömülü, uzun bir satır. Claude'a "tüm dosyayı yeniden yaz" dedirtme; base64 bozulursa logo kaybolur. Hedefli düzenleme iste.
- Değişiklik öncesi `git commit` at ya da dosyanın kopyasını al.
