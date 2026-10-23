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
*İmza öğeler:* Üstteki tıklanabilir ilçe filtresi, manşet altındaki "3 maddede ne oldu" kutusu.
*Not:* Sesli dinle düğmesi bu yönde doğmuştu; 24 Ağustos 2026'da çalışır hâle gelip üç yöne birden taşındı (aşağıda "Haber seslendirme").

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

**Döviz bandı verisi** — 21 Ağustos 2026, sekiz kalem:

| Kalem | Değer | Kaynak |
|---|---|---|
| Dolar | 48,07 ₺ ▲%0,23 | ECB referans kuru, 21.08.2026 |
| Euro | 56,23 ₺ ▲%0,39 | ECB referans kuru |
| Sterlin | 65,64 ₺ ▲%0,45 | ECB üzerinden çapraz |
| Altın (gram) | 7.115,37 ₺ | Spot ons × o günkü USD/TRY |
| Gümüş (gram) | 106,80 ₺ | Spot ons × o günkü USD/TRY |
| BIST 100 | 14.494,61 ▲%0,68 | 21.08.2026 kapanışı |
| Bitcoin | 77.265 $ | Spot |
| Faiz | %37,00 | TCMB politika faizi (1 hafta repo) |

Değişim yüzdeleri bir önceki iş gününe göre hesaplandı. Değerli maden ve kripto fiyatları 22 Ağustos spot değerleridir, diğerleri 21 Ağustos kapanışıdır.

**Bandın doluluğu.** Sekiz kalem, 1280px ve üzerinde bandı tam dolduracak (%100) şekilde ayarlandı; tarih sağ uçta tam görünür. Daha dar ekranlarda şerit yatay kaydırılır — İLÇELER şeridiyle aynı davranış. **Kalem eklerseniz doluluğu yeniden ölçün**, yoksa tarih kenarda kesilir.

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

**Gökyüzü dolgusu (25 Ağustos 2026 düzeltmesi).** Semboller eskiden gökyüzünü
`url(#gsky)` gradyanıyla dolduruyordu; gradyanın durakları `var(--s1)/var(--s2)`
kullanıyordu. Bir `<symbol>` `<use>` ile örneklendiğinde gradyan öğesi gölge
ağacın dışında kaldığı için bu değişkenler **çözülmüyor** ve gökyüzü **siyah**
çıkıyordu — koyu şekiller siyah zemin üzerinde kayboluyordu. Başsız Chrome'da
ölçülerek doğrulandı.

Çözüm: gökyüzü dikdörtgeni `class="gok"` aldı, CSS'e `.gok{fill:var(--s2)}`
kuralı eklendi. `var()` `fill` niteliğinde sorunsuz çözülüyor — yalnız gradyan
duraklarında çözülmüyor. Gradyan yerine düz tema rengi kullanılıyor; `gsky`
tanımı dosyalarda duruyor ama artık hiçbir yerden çağrılmıyor.

**Yeni sembol eklerken gökyüzü için `url(#gsky)` kullanma, `class="gok"` kullan.**

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

Anasayfalarda tasarıma özgü küçük birer parça:

- **Tasarım 1:** hava/namaz/eczane sekmeleri
- **Tasarım 2:** ilçe filtresi çipleri
- **Tasarım 3:** açık/koyu tema düğmesi

Haber detay sayfalarında bunlara ek olarak, üçünde de **aynı** seslendirme betiği bulunur
(`</body>` öncesindeki son `<script>`). Ayrıntısı bir alt başlıkta.

### Haber seslendirme

Haberi tarayıcının kendi ses motoru (Web Speech API) okur. Dış servis, API anahtarı,
indirilen ses dosyası yok — sayfaların bağımsızlığı bozulmadı.

| Parça | Nerede |
|---|---|
| Oynatıcı | Üç haber detay sayfasında, `id="seslendirme"`. T1'de fotoğraf altında kutu, T2'de imzanın altında yuvarlak panel, T3'te paylaş satırının altında kart |
| Anasayfa girişi | Manşetteki "Sesli dinle" bağlantısı `...haber-detay.html#seslendirme` adresine gider; sayfa açılınca oynatıcı vurgulanır ve okuma kendiliğinden denenir |
| Betik | Üç dosyada birebir aynı; okunacak öğeler `data-kaynak` seçicisinden gelir |

Nasıl çalışır:

- Metin **cümlelere bölünüp** sırayla seslendirilir (parça başına en çok 150 harf).
  Tek parça uzun metin gönderildiğinde tarayıcılar okumayı 15 saniye dolayında kesiyor;
  bölme bunun içindir. `EN_UZUN` sabitini büyütmeyin.
- Okunan paragraf sayfada işaretlenir (`.ses-okunan`), görünmüyorsa ekrana getirilir.
  İlerleme çubuğu ve "5/13 paragraf · yaklaşık 3 dk kaldı" bilgisi `role="status"` ile duyurulur.
- Denetimler: oynat/duraklat, önceki/sonraki paragraf, durdur, hız (0,8× – 1,5×).
- **Ses seçimi kalitenin kendisidir.** Adında Natural / Neural / Online / Google geçen
  sesler öne alınır; birden çok Türkçe ses varsa oynatıcıda **Ses** açılır listesi çıkar ve
  seçim `localStorage`'a yazılır. Yalnızca eski sistem sesi bulunduğunda sayfa bunu söyler.
- `speechSynthesis` desteklenmiyorsa oynatıcı pasifleşir, sayfanın kalanı etkilenmez.
- Okunmayanlar: fotoğraf altları, kenar notları, "3 maddede ne oldu" kutusu, editör notu,
  kronoloji notu, `data-ses="atla"` işaretli her şey. **Kaynak bölmesinin cümlesi okunur** —
  kaynak sesli dinleyende de belirtilmiş olur.

Gövde yayında yeniden üretildiği için okunacak liste **her başlatmada yeniden toplanır**;
`yayin.py` ile üretilen `haber-*-t{1,2,3}.html` sayfalarında oynatıcı olduğu gibi çalışır.

**Bu makinede ölçülen sesler (24 Ağustos 2026):**

| Tarayıcı | Türkçe sesler | Sonuç |
|---|---|---|
| Chrome | yalnızca `Microsoft Tolga` (eski SAPI sesi) | Belirgin biçimde makine gibi duyuluyor; Chrome'da Web Speech API ile yapılabilecek başka bir şey yok |
| Edge | `Microsoft Emel Online (Natural)` + `Tolga` | Emel sinir ağı sesi, gazete demosu için kabul edilebilir |

İlk sürümde sıralama "mümkünse cihazın yerel sesi" diyordu; bu, Edge'de doğal Emel yerine
robotik Tolga'yı seçiyordu. Sıralama düzeltildi — **`localService` tercihini geri getirmeyin.**

Tarayıcı sesinin tavanı buraya kadar. Her okuyucuda aynı ve daha doğal bir ses isteniyorsa
yayın anında ses dosyası üretmek gerekir (bkz. "Bilinen eksikler").

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


### Sunum öncesi doğrulanacak tek başlık

"Prof. Dr. Okan Tüysüz'den uyarı: Binaların arasından faylar geçiyor" başlığı
anasayfa, ilçe ve kategori sayfalarında duruyor ve **adı verilen gerçek bir
kişiye bir uyarı atfediyor**, ama sitede hiçbir yerde kaynağı gösterilmiyor ve
tıklanabilir bir detay sayfası yok. Başlık 18-21 Ağustos gündeminden derlenen
mevcut içeriğin parçası, bu oturumda üretilmedi.

Sunumdan önce ya kaynağı eklenmeli ya da başlık çıkarılmalı. Karar
kullanıcınındır — içerik değişikliği sorulmadan yapılmaz.

### Gerçek gazeteciler — değişmez kural

25 Ağustos 2026'da köşe yazarı kadrosu gazetenin kendi yönetim panelinden alındı;
sayfalardaki adlar artık **gerçek kişiler**. Yazı başlıkları, tarihleri ve okunma
sayıları da gerçek.

**Bu isimlerin ağzından tek kelime yazılmaz.** Köşe yazısı metni, spot, özet,
alıntı — hiçbiri uydurulmaz. Yazı listeleri başlık + tarih + okunma sayısıyla
kalır; tasarım spot alanı istiyorsa alan boş bırakılmaz, tasarım spotsuz kurulur.

Özgeçmiş, portre ve iletişim bilgisi elimizde yok; açıkça "Yer tutucu" duruyor.
Manzara fotoğrafları yazar portresi yerine kullanılmaz.

Haber künyesindeki `Yazar adı` yer tutucuları da **bilerek** duruyor: gerçek bir
editöre yazmadığı haberi atfetmemek için.

## 4b. Yapay zekâ editör

Haber masası aracı prototipi. Bir haber adresi verilir; araç kaynağı indirir,
yapılandırılmış olgu çıkarımı yapar ve yayın alanları doldurulmuş bir **taslak**
üretir. Kaynağın metni kopyalanmaz — haber kaynak gösterilerek yeniden yazılır.

| Parça | Ne |
|---|---|
| `arac/ayiklayici.py` | JSON-LD → OpenGraph → paragraf sezgisi sırasıyla ayıklar. Yalnızca standart kütüphane. |
| `arac/haber_taslak.py` | Şema, sistem yönergesi ve komut satırı. `claude-opus-5`, yapılandırılmış çıktı. |
| `yapay-zeka-editor.html` | Kaynak ve taslağı yan yana gösteren, alanları düzenlenebilir arayüz. |
| `arac/cikti/*.json` | Sunum örnekleri (üç gerçek haber). |

**Sunumda:** `yapay-zeka-editor.html` sayfasını açın, "Hazır örnek" düğmelerinden
birine basın. Akış canlandırması çalışır, kaynak paneli gerçek ayıklanmış veriyi
gösterir, taslak alanları dolar. "Önizleme" düğmesi haberin sitede nasıl
görüneceğini gösterir.

**Canlı çekim:** Tarayıcı rastgele bir siteyi çekemez (CORS). Komut satırından
`python arac/haber_taslak.py "<adres>"` çalıştırıp çıkan JSON'u sayfaya sürükleyin.
Ayrıntı: `arac/README.md`.

**Örneklerin durumu:** Üç örneğin *kaynak ayıklaması* gerçek çalıştırmadan geldi.
*Taslak* kısımları, ortamda API anahtarı bulunmadığı için aracın sistem yönergesi
ve şemasına birebir uyularak elle hazırlandı; anahtar tanımlanınca araç aynı
şekli canlı üretir.

---

### Demonun günü: 25 Ağustos 2026, Salı

Kabuktaki üst şerit bu tarihi gösterir. 25 Ağustos'a çekilme sebebi: panelden
gelen gerçek köşe yazısı verisi o güne kadar uzanıyor ve daha eski bir "bugün"
gelecek tarihli yazı listelemek anlamına geliyordu.

Haber içerikleri 18-21 Ağustos gündeminden; anasayfada birkaç günlük haber
bulunması normaldir. **Makale künyelerindeki yayın tarihleri değiştirilmedi** —
yalnız kabuktaki "bugün" şeridi taşındı. Tasarım 3'ün kabuğunda tarih şeridi yok.

## 5. Bilinen eksikler

| Eksik | Not |
|---|---|
| Logo vektörel değil | Elimizde JPEG var; gazeteden SVG/AI sürümü istenmeli. Retina ekranlarda kenarlar yumuşak görünüyor |
| Alt konu ve arşiv sayfaları yok | Anasayfa, haber detay, ilçe, yazar ve kategori sayfaları üç yön için de hazır. `/ekonomi/piyasalar` gibi alt konu sayfaları ve tarih arşivi yok; sayfalama bileşenleri görüntüdür, çalışmaz |
| Fotoğraflar gazetenin değil | `gorseller/` içindekiler Commons kaynaklı yer tutucu. Canlıya geçerken gazete arşiviyle değişecek; CC BY / CC BY-SA olanlar künye ister |
| Google Fonts dışa bağımlı | İnternetsiz açılınca yedek fontlara düşer, düzen bozulmaz |
| Arama sayfa içiyle sınırlı | Yazdıkça o sayfadaki başlıkları süzüyor; gerçek arşiv araması arka uç ister |
| Menü içerikleri örnek | Açılır alt menüler çalışıyor, ama içindeki linkler `#` — hedef sayfalar henüz yok |
| Döviz bandı statik | Sekiz kalemin tamamı **gerçek veri** (aşağıdaki tabloya bakın), ama sayfaya gömülü ve kendiliğinden güncellenmez. Canlıda bir piyasa servisine bağlanması gerekir; `.doviz` bileşeninin yapısı buna hazır, yalnızca `<dd>` içerikleri beslenecek |
| "Arşive sor" arka planı yok | Tasarım 3'teki kutu görsel; gerçek arama altyapısı gerektirir |
| Yazar sayfasında sayfalama çalışmıyor | `tasarim-1-yazar.html` içindeki `1 2 3 … 115 Sonraki` şeridi yalnızca görüntü. Sayfada Namık GÖZ'ün son **4** yazısı var; kalan arşiv (toplam 2.288 yazı) yayın sistemine bağlanınca gelecek. Sayfa başına 20 yazı varsayımıyla 115 sayfa yazıldı |
| Köşe yazısı detay sayfası yok | Yazı **metinleri** elimizde olmadığı için yazar sayfasındaki başlıklar bilerek bağlantısız. Gerçek kişinin ağzından metin üretilmedi; özgeçmiş, köşe adı, portre ve iletişim alanları "Yer tutucu" olarak duruyor |
| Seslendirme cihaza bağlı | Ses, tarayıcının/işletim sisteminin Türkçe ses paketiyle üretilir; kalite makineden makineye değişir, bazı cihazlarda Türkçe ses hiç bulunmaz. Yayın kalitesinde tek tip ses isteniyorsa sunucu tarafında ses dosyası üreten bir servis gerekir |

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

1. **Tasarım yönünü seç** — yayın ekibiyle üç yönün beşer sayfasını birlikte gez
2. ~~İlçe sayfası~~ — **yapıldı** (`tasarim-*-ilce.html`, örnek ilçe Nilüfer, 17 ilçe gezinmede)
3. ~~Yazar sayfası~~ — **yapıldı** (`tasarim-*-yazar.html`, örnek yazar Namık GÖZ)
4. ~~Yazar isimlerini gerçekle değiştir~~ — **yapıldı**, kadro gazetenin panelinden alındı
5. ~~Kategori sayfası~~ — **yapıldı** (`tasarim-*-kategori.html`, örnek kategori Ekonomi, 13 kategori gerçek slug'larıyla)
6. **Fotoğrafları gazete arşiviyle değiştir** — `gorseller/` içindekiler yer tutucu; ayrıca `KAYNAKLAR.md`de beş dosyanın adı içeriğiyle uyuşmuyor
7. **Vektörel logo** — gazeteden iste, base64'ü güncelle

**Vefat ve anma ilanları kapsam dışı** — kullanıcı istemedi, önerme.

**Sayfa ailesi tamam:** her yön için anasayfa · haber detay · ilçe · yazar · kategori.

### Dikkat

- Dosyalarda logo base64 olarak gömülü, uzun bir satır. Claude'a "tüm dosyayı yeniden yaz" dedirtme; base64 bozulursa logo kaybolur. Hedefli düzenleme iste.
- Değişiklik öncesi `git commit` at ya da dosyanın kopyasını al.
