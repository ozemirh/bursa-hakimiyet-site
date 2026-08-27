# Canlı veri — ücretsiz çekme betikleri

Anasayfanın canlı veri isteyen bileşenlerini ücretsiz kaynaklardan besleyen
betikler. 26 Ağustos 2026 kararı: **ücretli servis kullanılmayacak**
(`URUN-PLANI.md` §8).

Bu klasör `arac/` ve `disa-aktarim/` ile aynı yaklaşımı izler: saf standart
kütüphane, doğrudan istek, saygılı hız, kesintiye dayanıklı, çıktı yerel
JSON dosyasına. Paket kurulumu yok.

| Dosya | Ne |
|---|---|
| `ortak.py` | HTTP/yeniden deneme, atomik JSON yazımı, log, "kaynak düştü" davranışı |
| `doviz.py` | Döviz bandının beş kalemi (TCMB + `piyasa.json`) |
| `piyasa.py` | Gram altın ve BIST 100 — TCMB EVDS (resmî kapanış) + üç piyasa yedeği, 15 dk'da bir |
| `hava_durumu.py` | Bursa hava durumu — şu an + 5 gün + saatlik |
| `namaz_vakitleri.py` | Namaz vakitleri (Diyanet ölçütleriyle hesap) |
| `nobetci_eczane.py` | Bursa nöbetçi eczaneleri |
| `puan_durumu.py` | Dört lig puan durumu + takip edilen takımın haftalık maçı |
| `vizyon_takvimi.py` | Türkiye vizyon takvimi |
| `veri/` | Çıktı (`.gitignore`de) |

```powershell
python canli-veri\doviz.py
python canli-veri\piyasa.py
python canli-veri\piyasa.py --surekli 15
python canli-veri\hava_durumu.py
python canli-veri\namaz_vakitleri.py --gun 7
python canli-veri\nobetci_eczane.py
python canli-veri\puan_durumu.py
python canli-veri\vizyon_takvimi.py --kaynak vikiveri
```

Çıktı kökü `--kok` ya da `BH_CANLI_KOK` ortam değişkeniyle değişir.

---

## F6 sözleşmesi — kaynak · sıklık · düştüğünde

Faz F6'nın bitti ölçütü her bileşen için üç satır ister. Bu klasörün
kapsadığı bileşenler:

| Bileşen | Kaynak | Sıklık · bayat eşiği | Kaynak düştüğünde |
|---|---|---|---|
| **Döviz bandı** (dolar·euro·sterlin) | TCMB günlük kur bülteni — `tcmb.gov.tr/kurlar/today.xml` | Günde bir; TCMB bülteni iş günü 15:30'da açıklanır. Eşik **24 saat** | Önceki dosya korunur, `durum-doviz.json` → `eski`, çıkış kodu **2**. Bant son bülteni tarihiyle gösterir. Hiç veri yoksa `yok` + kod **1** |
| **Gram altın · BIST 100** | TCMB EVDS → Google Finance → doviz.com → Mynet Finans (`piyasa.py`); hiçbiri gelmezse `doviz-elle.json` | **15 dakikada bir** (gün içi hareket ediyor). Eşik **45 dk** — iki koşu kaçarsa hâlâ geçerli, üçüncüde bayat | Bir sonraki kaynağa geçilir. Dördü birden düşerse önceki dosya korunur, `durum-piyasa.json` → `eski`, kod **2**; hiç veri yoksa `yok` + kod **1**. `doviz.py` bayat `piyasa.json`u kullanmaz, kutuyu boş bırakır |
| **Hava durumu** | MGM açık uçları — `servis.mgm.gov.tr` | Saatte bir (son durum saatlik güncelleniyor). Eşik **3 saat** | Aynı davranış. Kalıcı düşmede `--kaynak elle` → `hava-elle.json` |
| **Namaz vakitleri** | **Kaynak yok, hesap var.** Diyanet ölçütleriyle astronomik hesap; ağ gerektirmez | Günde bir yeter (gece yarısından sonra). Eşik **48 saat** — bu eşik kaynak düşmesini değil, zamanlayıcının durduğunu yakalar | Hesap düşmez. Yine de `--kaynak elle` → `namaz-elle.json` yolu var |
| **Nöbetçi eczane** | Bursa Eczacı Odası — `beo.org.tr/nobetci-eczaneler` | Nöbet günde bir devrediliyor (ölçüldü: 18:30 → ertesi gün 08:30). Günde iki kez yeter. Eşik **24 saat** | Aynı davranış. Kalıcı düşmede `--kaynak elle` → `eczane-elle.json` |
| **Puan durumu** | TFF — `www.tff.org` | Maç günü saatte bir, diğer gün günde bir. Eşik **48 saat** | Önceki dosya korunur, `durum-puan-durumu.json` → `eski`, kod **2**; hiç veri yoksa `yok` + kod **1** |
| **Vizyon takvimi** | TMDB (varsayılan) · Wikidata · elle · Box Office TR (yalnız yazılı izinle) | Haftada bir (perşembe akşamı yeter). Eşik **7 gün** | Aynı davranış. Kalıcı düşmede `--kaynak elle` |

Çıkış kodları: **0** taze veri · **2** çekilemedi ama önceki dosya duruyor ·
**1** çekilemedi ve elde veri de yok. Zamanlayıcı 2'yi uyarı, 1'i hata sayar.

### Kullanım şartları — hukuk teyidine giden üç kaynak

Üç resmî kaynak da aynı kalıbı kullanıyor: *kaynak göstererek yayımla, ama
ticari kullanım/önceden izin ayrı*. Gazete ticari bir yayındır. Betikler
kaynağı çıktıya yazar (`kaynak` bloğu + `kunye`), sayfada atıf görünmelidir.
**Bu üç madde birlikte hukuk teyidine gitmeli** (`URUN-PLANI.md` §8):

| Kaynak | Madde (birebir) |
|---|---|
| **TCMB** | "Sitede yer alan bilgiler, kaynak gösterilmek suretiyle yayımlanabilir; ancak bu bilgilerin ticari amaçlarla kullanımı TCMB'nin yazılı iznine tabidir." |
| **MGM** | "İnternet sitesinde bulunan hiçbir bilgi; önceden izin alınmadan ve kaynak gösterilmeden … yeniden yayımlanamaz …" |
| **TFF** | "Sitede yer alan bilgiler, kaynak gösterilmek suretiyle yayımlanabilir; ancak bu bilgiler ticari amaçlarla kullanılamaz." |

MGM ve TCMB'den yayın izni almak tek seferlik bir yazışma işidir; bu bir
**iş kalemidir**, betiğin işi değildir. Karşı görüş her üçünde de aynı: kur,
sıcaklık ve puan cetveli **olgudur**, FSEK eser koruması dışındadır.

Bursa Eczacı Odası'nın ayrı bir kullanım şartları sayfası **yok**;
`robots.txt` `/nobetci-eczaneler` yolunu açık bırakıyor (`/yonetim`,
`/eczaci` ve bütün `/dosyalar/…` kapalı — betik oralara hiç gitmiyor).

---

## Döviz bandı

Bant tam **beş** kalem (`URUN-PLANI.md` §1 madde 9): Dolar · Euro · Sterlin ·
Gram altın · BIST 100. Kaynak durumu **kalem başına** farklı, betiğin en
önemli davranışı bu.

```powershell
python canli-veri\doviz.py
```

| Kalem | Kaynak | Durum |
|---|---|---|
| Dolar · Euro · Sterlin | TCMB günlük bülten | **çalışıyor**, anahtarsız |
| Gram altın · BIST 100 | `piyasa.py` → `veri/piyasa.json` | **çalışıyor** (27 Ağustos 2026'da açıldı) |
| (hepsinin yedeği) | `veri/doviz-elle.json` | panel girişi, son çare |

Ölçüm (27 Ağustos 2026): bülten `2026/159`, **22 para birimi**, üç kalem
çekildi, bir önceki iş gününün bülteni de indirilip **değişim yüzdesi**
hesaplandı (`+0,04% · +0,09% · −0,02%`). Toplam süre **2 saniye**.

### Gram altın ve BIST 100 — kaynak bulundu

Bu iki kutu 26-27 Ağustos'ta boş kalmıştı. **27 Ağustos 2026'da kapandı:**
çekme işini `piyasa.py` yapar, `doviz.py` yalnızca `veri/piyasa.json`
dosyasını okur. TCMB mantığına dokunulmadı.

`doviz.py` doldurma sırası — **önce otomatik, sonra elle**:

1. `piyasa.json` taze mi? (eşik **45 dk**) → değeri oradan al
2. Değilse `doviz-elle.json` → panelden girilen değeri al
3. O da yoksa `deger: null` kalır ve **uydurulmaz**; sayfa kutuyu gizler

Sıra bu yönde çünkü elle giriş **son çaredir**: otomatik kaynak çalışırken
panelde unutulmuş eski bir değer yayına gitmemeli. Bayat `piyasa.json`
kullanılmaz — durmuş bir zamanlayıcı en önce burada görülür.

Önceki turda elenen adaylar kayıtta kalsın (26-27 Ağustos 2026 ölçümü):

| Aday | Neden elendi |
|---|---|
| **Borsa İstanbul** | Endeks ve kıymetli maden verisi DataStore üzerinden **satılıyor**. Açık `borsaistanbul.com/en/index/xu100` sayfasında endeksin tanımı var, **değeri yok** |
| **TCMB EVDS** | ~~API anahtarı istiyor~~ — **bu yanlıştı, 27 Ağustos 2026'da çözüldü ve 1. kaynak oldu.** Aşağıya bakın |
| **stooq.com** | `robots.txt`: `User-agent: *` → `Disallow: /` (yalnız Googlebot ve Bingbot'a izin). Projenin kendi kuralı gereği elendi |
| **Yahoo Finance** | `query1.finance.yahoo.com/robots.txt` → `Disallow: /`. Elendi |
| **LBMA** | `prices.lbma.org.uk` kimlik doğrulaması istiyor (HTTP 401) |

Elle giriş yolu **duruyor** ve değişmedi:

```json
{ "gram_altin": {"deger": 4835.20, "onceki": 4810.00,
                 "kaynak": "Bursa Kuyumcular Odası", "tarih": "2026-08-27"},
  "bist100":    {"deger": 11842.31, "onceki": 11790.05,
                 "kaynak": "Panel girişi", "tarih": "2026-08-27"} }
```

`onceki` verilirse değişim ve yön (`yukari`/`asagi`/`esit`) hesaplanır.

---

## Piyasa — gram altın ve BIST 100

Döviz bandının TCMB'de olmayan iki kalemi. Ayrı betik, çünkü **sıklığı
farklı**: TCMB bülteni günde bir kez çıkar, gram altın ve BIST 100 gün
içinde sürekli hareket eder.

```powershell
python canli-veri\piyasa.py                      # tek koşu (varsayılan)
python canli-veri\piyasa.py --surekli 15         # 15 dakikada bir, durmadan
python canli-veri\piyasa.py --kaynak doviz mynet # Chrome'suz sıra
python canli-veri\piyasa.py --kaynak google      # yalnız Google
```

### Dört kaynak, sırayla

| # | Kaynak | Nasıl | Verdiği | Ölçülen süre |
|---|---|---|---|---|
| 1 | **TCMB EVDS** | düz HTTP, tek POST, **anahtar yok** | gram altın · BIST 100 — **resmî kapanış** | **0,1-0,2 sn** |
| 2 | **Google Finance** | başsız Chrome `--dump-dom` | BIST 100 · dolar · euro (+ altın **hesapla**) | **19-28 sn** |
| 3 | **doviz.com** | düz HTTP, sunucu tarafında basılı | gram altın · BIST 100 · dolar · euro | **0,1-0,2 sn** |
| 4 | **Mynet Finans** | düz HTTP, sunucu tarafında basılı | gram altın · BIST 100 · dolar · euro | **0,3 sn** |

#### TCMB EVDS — resmî kaynak, anahtarsız (27 Ağustos 2026'da açıldı)

Belgelerde geçen `evds2.tcmb.gov.tr/service/evds/...` yolu **ölü**: her
isteğe — anahtarlı ya da anahtarsız — 1355 baytlık SPA kabuğu dönüyor.
Çalışan uç, EVDS arayüzünün kendi kullandığı uç ve **anahtar istemiyor**:

```
POST https://evds3.tcmb.gov.tr/igmevdsms-dis/fe
```

| Kalem | Seri | Ne ölçüyor |
|---|---|---|
| Gram altın | `TP.ALTINPIYASA.KAP02` | BIST Kıymetli Madenler Piyasası altın **kapanışı**, **TL/kg** → 1000'e bölünür. Kaynak: Borsa İstanbul |
| BIST 100 | `TP.MK.F.BILESIK` | **(FİYAT)** BİST 100 (XU100) kapanışı. `TP.MK.G.BILESIK` *getiri* endeksidir, o değil |

Seri kodları EVDS'nin kendi arama ucundan bulundu — o da anahtarsız:
`GET https://evds3.tcmb.gov.tr/igmevdsms-dis/searchResults?searchVal=altın`

Üç tuzak, üçü de ölçüldü:

- **Yük alanları eksiksiz olmalı.** `groupSeperator`, `isRaporSayfasi` ve
  `ozelFormuller` alanlarından biri eksikse sunucu **500** döner.
- **`Origin` gönderilecekse `evds3` olmalı.** `evds2` yazılırsa **403
  "Invalid CORS request"** gelir (sayfa evds2'den evds3'e yönleniyor).
  En dayanıklısı `Origin` hiç göndermemek — çerez/oturum da gerekmiyor.
- **`TP.ALTINPIYASA.KAP05` doğrudan TL/gr kote eder ama seyrek dolu**
  (17-26 Ağustos'ta 8 iş gününün 1'i). Yayına girmez; dolu olduğu günde
  birim çevrimini doğrulamak için okunur.

**EVDS kapanış verir, gün içi fiyat vermez.** Gün içinde en taze gözlem bir
önceki iş gününe aittir; kapanış akşam düşer. Bu yüzden EVDS kayıtları
`taze` değil **`resmi_kapanis`** damgası ve gözlem tarihiyle döner, ve
birleştirme sırası buna göre kurulur:

| Puan | Durum | Neden |
|---|---|---|
| 4 | `resmi_kapanis`, gözlemi **bugüne** ait | Borsa kapandıktan sonra bundan doğrusu yok |
| 3 | `taze` | Gün içi **doğrudan** kotasyon |
| 2 | `resmi_kapanis`, gözlemi **daha eski** | Resmî ama gün içinde bayat — canlı kotasyon öne geçer |
| 1 | `hesaplanan` | Google'ın vadeli onstan türettiği altın (%1,2 sapma) |

Yani EVDS başta olmasına rağmen **gün içinde bandı dondurmaz**: bayat
kapanış (puan 2) eşiği geçmediği için canlı kaynaklar yine denenir.

**Doğrulandı (27 Ağustos 2026, 12:30).** EVDS'nin 26-08 kapanışı, aynı anda
alınan piyasa kotasyonuyla karşılaştırıldı:

| Kalem | EVDS resmî kapanış | Piyasa (gün içi) | Sapma |
|---|---|---|---|
| Gram altın | 7.121,20 (`KAP02`/1000) | 7.115,73 (doviz.com) | **−0,08%** |
| BIST 100 | 14.610,92 | 14.586,77 (Google) | −0,17% |

Karşılaştırma çıktıya da yazılır:
`capraz_kontrol.resmi_kapanis_piyasa_farki`. Google'ın **hesaplanan** altını
%1,2 sapıyordu; EVDS'nin serisi doğrudan kotasyonla **binde bir** farkla
örtüşüyor — yani `KAP02/1000` gerçekten gram altındır.

Asıl kalemlerin ikisi de **puan 3 ya da üstü** bir değerle dolduğunda kalan
kaynaklara istek atılmaz. Hangi kalemin nereden geldiği `kalemler[].kaynak` alanında
yazar; `denetim.kaynak_dagilimi` özetler.

Dolar ve euro **yayın için değil doğrulama için** çekilir: her koşuda TCMB
bülteniyle karşılaştırılıp `capraz_kontrol.tcmb` bloğuna yazılır.

### Google düz HTTP ile olmaz — ölçüldü

`https://www.google.com/finance/quote/USD-TRY` düz istekte **200 döner ve
1 MB HTML verir, ama kur değeri içinde yoktur** — JS ile basılıyor. Bu
yüzden başsız Chrome'un `--dump-dom` kipi kullanılır: sayfa gerçekten
çalıştırılır, oluşan DOM okunur.

Ek paket **gerekmez** (websocket/CDP yolu denendi, `--dump-dom` yeterli
oldu); yalnızca makinede Chrome bulunmalı. Yol `BH_CHROME` ile verilebilir,
verilmezse bilinen konumlar ve `PATH` taranır. Chrome yoksa Google kaynağı
düşer, betik yedeklerle **tam sonuç** üretmeye devam eder.

Google sınıf adlarını karıştırdığı için CSS seçici yazılamaz. Ayıklama
**metin yapısına** dayanır — kenar şeridindeki onlarca fiyattan ana
kotasyonu ayıran şey `add` satırıdır:

```
XU100:INDEXIST  →  add  →  BIST 100  →  14.686,70  →  arrow_upward  →  +0,52%
```

Yapı tanınmazsa `None` döner ve kaynak düşer — **tahmin yürütülmez**.

### Gram altın — hesap ve birim

Birim **TL / gram**. doviz.com ve Mynet gram altını **doğrudan** kote eder,
çevrim gerekmez. Google'da ise TRY cinsinden altın kotasyonu **yoktur**
(ölçüldü: `/finance/quote/XAU-TRY` ve `XAU-USD` → "Sayfa Bulunamadı").
Google'daki tek altın kalemi `GCW00:COMEX`, yani **COMEX vadeli** sözleşme,
USD/ons. Google yolunda gram altın şöyle **hesaplanır**:

```
gram_altin_TL = ons_USD × USD/TRY ÷ 31,1034768        (1 troy ons = 31,1035 g)
```

**Bu yaklaşıktır ve ölçülerek doğrulandı.** 27 Ağustos 2026, aynı dakika:

| Değer | Kaynak | TL/gram |
|---|---|---|
| hesaplanan | Google `GCW00:COMEX` × USD/TRY ÷ 31,1035 | **7.204,34** |
| doğrudan | doviz.com | **7.121,12** |
| doğrudan | Mynet Finans | **7.120,51** |
| doğrudan | bigpara (bağımsız üçüncü ölçüm) | **7.120,34** |

Üç doğrudan kotasyon birbirine **%0,02** içinde; hesaplanan değer onlardan
**%1,17 yüksek**. Fark uydurma değil, beklenen: vadeli fiyat spotun
üzerinde durur ve Kapalıçarşı gram altını kendi arz/talebiyle fiyatlanır.

Bu yüzden betik **doğrudan kotasyonu tercih eder**. Hesaplanan değer yalnız
doğrudan kaynakların hepsi düştüğünde yayına çıkar, o zaman da
`kaynak_durumu: "hesaplanan"` damgasıyla ve `hesap` bloğuyla birlikte —
ons fiyatı, kullanılan kur, bölen ve uyarı metni dosyada durur. İki değer
de eldeyse aradaki sapma `capraz_kontrol.gram_altin` bloğuna yazılır.

### Doğrulama — TCMB ile çapraz kontrol

Her koşuda Google'ın kuru TCMB bülteniyle karşılaştırılır (27 Ağustos 2026):

| Kalem | Google | TCMB (bülten 26.08.2026) | Sapma |
|---|---|---|---|
| Dolar | 48,1354 | 48,1157 | **+%0,041** |
| Euro | 56,2272 | 56,1398 | **+%0,156** |

Tolerans **%1** — TCMB günde bir sabit bülten yayımlar, piyasa gün içinde
hareket eder. Bu eşiğin aşılması "piyasa oynadı" değil "**ayrıştırma
kaydı**" demektir; `tutuyor: false` olarak işaretlenir.

### Kullanım şartları

`google.com/robots.txt` **`/finance` yolunu kısıtlamıyor** — ham satırlar
elle eşletildiğinde `/finance/quote/…` ile eşleşen tek bir kural yok.

> **Tuzak:** Python'un kendi `urllib.robotparser`'ı burada **yanlış cevap
> verir**. `Disallow: /?` satırındaki soru işaretini düşürüp kuralı
> `Disallow: /` gibi okur ve *her* yolu yasaklı sanır. Bu kütüphaneyle
> kontrol eden biri Google'ı yanlışlıkla eler. (stooq ve Yahoo ise
> **gerçekten** `Disallow: /` diyordu; onlar haklı olarak elenmişti.)

Ayrı konu: **Google Hizmet Şartları** otomatik erişimi genel olarak hoş
karşılamaz. Bu `robots.txt` meselesi değil sözleşme meselesidir ve TCMB /
MGM / TFF maddeleriyle birlikte **hukuk teyidine gitmeli**
(`URUN-PLANI.md` §8). Yedeklerin varlığı bu kararı acil olmaktan çıkarır:
Google'sız da bant tam çalışıyor.

`doviz.com/robots.txt` → `Allow: /`; yalnız `/api/`, `/user-api/`,
`/tickerbar/`, `/kucoin/`, `/virgul/` kapalı — betik ana sayfayı okur,
o yollara hiç gitmez. `finans.mynet.com` için ilgili yollar açık.

**Elenen aday:** `bigpara.hurriyet.com.tr` veriyi sunucu tarafında basıyor
ve `User-agent: *` için ilgili yolları açıyor, ama `robots.txt`'sinde
`ClaudeBot` / `anthropic-ai` / `GPTBot` için açık `Disallow: /` var. Sınırda
bir durum olduğu için yedek listesine **alınmadı**; yukarıdaki tabloda
yalnızca bağımsız ölçüm olarak bir kez kullanıldı.

### Kırılganlık — ölçüldü, saklanmadı

Bu betiğin **er geç kırılacak** parçası Google yoludur. Ahlak dersi değil,
mühendislik gerçeği: Google sayfa yapısını haber vermeden değiştirir ve
otomatik erişimi engelleyebilir.

Ölçülen: **6 ardışık koşuda 6 başarı**, Google engelleme belirtisi (CAPTCHA,
`/sorry/` yönlendirmesi, "unusual traffic") **0 kez** görüldü. Bu, 15
dakikada bir koşacak bir betik için **hiçbir şey kanıtlamaz** — engelleme
birikimlidir.

Üç kırılma biçimi **kasten tetiklenerek** sınandı; üçünde de sonuç aynı:

| Sınama | Google | Sonuç |
|---|---|---|
| Chrome bulunamıyor | düştü | 4/4 kalem yedekten, **çıkış 0** |
| Sayfa düzeni değişti (kotasyon tanınmıyor) | düştü | 4/4 kalem yedekten, **çıkış 0** |
| CAPTCHA gösteriliyor | düştü | 4/4 kalem yedekten, **çıkış 0** + `denetim.google_engel_izi` dolu |
| **Üç kaynak birden** düştü (önceki dosya var) | — | dosyaya **dokunulmadı**, `durum-piyasa.json` → `eski`, **çıkış 2** |
| Üç kaynak birden düştü (önceki dosya yok) | — | `yok`, **çıkış 1** |

Engelleme belirtisi sessizce yutulmaz: `denetim.google_engel_izi` hangi
sembolde engel görüldüğünü yazar. **Bu alan dolmaya başlarsa Google yolu
kapanmıştır** — `--kaynak doviz mynet` ile devam edilir, bant durmaz.

Yedeklerin ikisi de saf standart kütüphaneyle çalışıyor ve **0,3 saniyenin
altında** dönüyor; yani Google düştüğünde hem hız hem sonuç iyileşiyor.
Google varsayılan sırada birinci, çünkü istenen kaynak o.

### Görev Zamanlayıcı — 15 dakikada bir

Tek koşu kipi kullanılır; zamanlayıcı çağırır. `--surekli` kipi geliştirme
ve tek makinede elle çalıştırma içindir — sunucuda zamanlayıcı tercih
edilir, çünkü betik çökerse onu yeniden başlatan bir şey olmalı.

```powershell
$py  = "C:\Users\Asus\Desktop\bursa_hakimiyet_site\.venv\Scripts\python.exe"
$bet = "C:\Users\Asus\Desktop\bursa_hakimiyet_site\canli-veri\piyasa.py"
schtasks /Create /TN "BH piyasa" /SC MINUTE /MO 15 /RL LIMITED /F /TR "`"$py`" `"$bet`""
```

Yoklama, elle çalıştırma, silme:

```powershell
schtasks /Query  /TN "BH piyasa" /V /FO LIST
schtasks /Run    /TN "BH piyasa"
schtasks /Delete /TN "BH piyasa" /F
```

`schtasks` **son çıkış kodunu** `Last Result` alanında tutar: `0` taze,
`2` çekilemedi ama önceki dosya duruyor (uyarı), `1` elde veri de yok
(hata). Google yolu ölçülen en kötü hâlinde 28 saniye sürüyor, 15 dakikalık
aralığa pay bol.

---

## Hava durumu

Kaynak MGM'nin kendi sitesinin kullandığı açık uçlar. Dört istek:
merkez çözümü → son durum → 5 günlük tahmin → saatlik tahmin.

```powershell
python canli-veri\hava_durumu.py
python canli-veri\hava_durumu.py --il Bursa --ilce Osmangazi
python canli-veri\hava_durumu.py --kaynak elle
```

**İstasyon numaraları kodda yazılı değil**; her koşuda il adından çözülür
(`merkezler?il=Bursa` → Osmangazi, `merkezId 91601`, yükseklik 100 m).
MGM istasyon değiştirdiğinde betik kendini düzeltir.

Ölçüm (27 Ağustos 2026): **1 merkez, 5 günlük tahmin, 5 saatlik adım**,
tanımsız hadise kodu **0**. Toplam süre **6 saniye** (istekler arası
saygılı bekleme dâhil).

### Ölçülen iki tuhaflık

**1. Uçlar isteğin nereden geldiğine bakıyor.** `Origin` ve `Referer`
başlıkları `www.mgm.gov.tr` olarak gönderilmezse uçlar cevap vermiyor.
`servis.mgm.gov.tr/robots.txt` de **403** dönüyor (RFC 9309: 4xx =
kısıtlama yok sayılır). Başlıklar her istekte gönderilir.

**2. Ölçülemeyen alan 0 değil `-9999` dönüyor** — deniz suyu sıcaklığı,
kar yüksekliği, METAR… Bunlar `null`'a çevrilir. Sıfır gibi göstermek
hatalı olurdu. Ondalıklı değerler ayrıca bir haneye yuvarlanır: MGM rüzgâr
hızını `0.7200000000000001` gibi kayan nokta artığıyla döndürüyor.

### Hadise kodları

Kod → Türkçe ad eşlemesi (**30 kod**) MGM'nin kendi betiğinden alındı
(`Scripts/ziko16_js/angularService/ililceler.js` içindeki `convertHadise`).
Sözlükte olmayan kod **uydurulmaz**: ham kod yazılır ve
`"ad_dogrulanmadi": true` işaretlenir; `denetim.tanimsiz_hadise_kodu`
listesi bunu sayar.

---

## Namaz vakitleri

**Bu bileşen çekilmiyor, hesaplanıyor.**

```powershell
python canli-veri\namaz_vakitleri.py --gun 7
python canli-veri\namaz_vakitleri.py --dogrula
```

### Diyanet erişilemedi — ölçüldü

`diyanet.gov.tr` alan adındaki hiçbir sunucu bu ağdan cevap vermiyor; istek
TLS tokalaşmasından sonra sıfırlanıyor. Üç bağımsız istemciyle denendi
(Python `urllib`, `curl`/Schannel, tarayıcı tabanlı getirici) — üçü de aynı:

| Sunucu | IP | Sonuç |
|---|---|---|
| `www.diyanet.gov.tr` | 88.255.37.202 | bağlantı sıfırlandı |
| `namazvakitleri.diyanet.gov.tr` | 88.255.37.167 | bağlantı sıfırlandı |
| `vakithesaplama.diyanet.gov.tr` | 88.255.37.145 | bağlantı sıfırlandı |

Hesap yolu zaten daha sağlam: ağ istemez, kaynak düşmesi diye bir sorunu
yoktur, kullanım şartı sorunu doğurmaz. Vakit bir **astronomi olgusudur**.

### Yöntem

Güneş konumu Meeus'un düşük doğruluklu algoritmasıyla; deklinasyon ve
denklem-i zaman **her vakit için o vaktin saatinde** yeniden hesaplanır
(iki yineleme — tek seferlik hesap imsak ve yatsıda bir dakikaya varan
sapma bırakıyordu). Bursa: `40.1826 N, 29.0665 E, rakım 155 m`.
Ölçütler: imsak **18°**, yatsı **17°**, ikindi **Şafii** (gölge çarpanı 1),
güneş/akşam rakım düzeltmeli ufuk (`−0.8333° − 0.0347·√rakım`).
Zaman dilimi **UTC+3 sabit** (Türkiye'de yaz saati uygulaması yok).

### Temkin — ölçüldü, uydurulmadı

Diyanet yayımladığı vakitlere temkin ekler. Değerler, Diyanet'in
yayımladığı Bursa tablosuyla karşılaştırılarak bulundu: her vakit için
−7…+7 arasındaki bütün tam sayı temkinler denendi, azami sapmayı en küçük
yapan alındı.

| Vakit | Temkin | Azami sapma | Ortalama sapma | Birebir tutan |
|---|---|---|---|---|
| İmsak | 0 dk | **0 dk** | +0,00 dk | 31/31 |
| Güneş | −5 dk | **1 dk** | −0,32 dk | 21/31 |
| Öğle | +5 dk | **1 dk** | −0,16 dk | 26/31 |
| İkindi | +4 dk | **1 dk** | −0,35 dk | 20/31 |
| Akşam | +5 dk | **1 dk** | −0,68 dk | 10/31 |
| Yatsı | +1 dk | **1 dk** | −0,42 dk | 18/31 |

Referans: **Diyanet İşleri Başkanlığı'nın Ağustos 2026 Bursa tablosu, 31
gün.** `diyanet.gov.tr` erişilemediği için tablo, Diyanet verisini yayımlayan
**iki bağımsız ulusal yayının** sayfasından alınıp birebir aynı olduğu
doğrulandı. Tablo `namaz_vakitleri.py` içine gömülüdür ve `--dogrula` onu
her koşuda yeniden ölçer — beyan değil, tekrarlanabilir ölçüm.

**Çapraz kontrol.** Aynı hesap, Diyanet yöntemini uygulayan bağımsız bir
kütüphanenin **365 günlük** Bursa çıktısıyla da karşılaştırıldı: beş vakitte
azami sapma **1 dk**, ikindide **2 dk**. Yani temkin tablosu tek bir aya
uydurulmuş değil, yıl boyu tutuyor.

**Uyarı.** Vakitler ilçe merkezine göre birkaç dakika oynar. Betik
`--enlem/--boylam/--rakim` alır; ilçe sayfaları için ayrı koşulabilir.

---

## Nöbetçi eczane

```powershell
python canli-veri\nobetci_eczane.py                  # bugün, il geneli
python canli-veri\nobetci_eczane.py --ilce İNEGÖL
python canli-veri\nobetci_eczane.py --tarih 2026-08-28
```

Planın öngörüsü *"nöbetçi eczane için API çoğu ilde yok, elle giriş
gerekebilir"* idi (`URUN-PLANI.md` §4 madde 4). **Bursa için ölçüm sonucu
farklı:** Bursa Eczacı Odası nöbet listesini kendi sayfasında sunucu
tarafında basıyor. API olmasa da düzenli veri var — ad, ilçe, açık adres,
telefon, harita konumu (enlem/boylam) ve nöbet saatleri tek tek alınıyor.

Sayfanın iki kipi var: `GET` bugünün il geneli listesini, `POST`
(`tarih1` + `ilce`) belirli gün ve/veya ilçeyi verir.

Ölçüm (27 Ağustos 2026, il geneli): **36 eczane, 20 ilçe**, telefonsuz
**0**, harita konumu olmayan **0**, nöbet saati çözülemeyen **0**.
Süre **1 saniyeden az**. İlçe süzgeci (`--ilce İNEGÖL`) **3 eczane**,
ileri tarih (`--tarih 2026-08-29`) **35 eczane** döndürdü.

İlçe listesi **kodda tutulmaz**, formdan okunur (19 seçenek). Kaynakta
telefonu ya da konumu olmayan eczane boş alanla geçer, **uydurulmaz**.

**KVKK.** Çekilen alanlar nöbet görevine ait **kamuya açık işletme**
bilgileridir. Kişisel veri — eczacının adı, üyelik bilgisi — çekilmez;
`robots.txt`'nin kapattığı `/eczaci` ve `/yonetim` yollarına hiç gidilmez.

---

## Puan durumu

Dört lig: Süper Lig · 1. Lig · 2. Lig (2 grup) · 3. Lig (3 grup).
26 Ağustos 2026 ölçümü: **127 takım, 7 grup, tutarsız satır 0**.

```powershell
python canli-veri\puan_durumu.py                    # dördü birden
python canli-veri\puan_durumu.py --lig super 1lig
python canli-veri\puan_durumu.py --takim BURSASPOR  # varsayılan
```

### Ölçülen üç tuhaflık

**1. `tff.org.tr` çözülmüyor, site `www.tff.org` adresinde.** DNS ölçümü:
`www.tff.org.tr` → SERVFAIL, `www.tff.org` → MerlinCDN. Betik `www.tff.org`
kullanır.

**2. Süper Lig puan cetvelinin takım adları kaynakta bozuk.** `pageID=198`
sayfası `windows-1254` başlığıyla dönüyor ama sunucu Türkçe harflerin yerine
`U+FFFD` basıyor: `GENÇLERBİRLİĞİ` → `GEN?LERB?RL???`. Sayısal alanlar sağlam.
Betik adları **kulüp kimliğinden** (`kulupID`) onarır: temiz adlar `pageID=80`
sayfasındaki özet tablodan gelir, kimlikle eşleşir. Onarılamayan ad
`"ad_dogrulanmadi": true` ile işaretlenir — **uydurulmaz**. Ölçüm: 127 addan
0'ı doğrulanamadı.

**3. Süper Lig'in tam tablosu yalnız `pageID=198`'de.** `pageID=80`'deki tablo
üç sütunlu (takım · O · P) özettir. Diğer üç lig kendi sayfasında tam tabloyu
verir.

### Grup seçimi — plandaki açık soru kapandı

Plan "2. ve 3. Lig grup usulü, hangi grup gösterilecek kararı yok" diyordu.
Betik **bütün grupları** çeker, yani bu artık bir çekme değil **gösterim**
kararı. Ölçülen dağılım (26 Ağustos 2026):

| Lig | Grup | Bursa bölgesi kulüpleri |
|---|---|---|
| 2. Lig | Beyaz | İnegöl Kafkas Spor |
| 2. Lig | Kırmızı | Karacabey Belediye Spor · Sultan Su İnegölspor |
| 3. Lig | 2. Grup | Bursa Nilüfer FK · Bursa Yıldırım Spor |

Önerim: 2. Lig'de **Kırmızı**, 3. Lig'de **2. Grup** varsayılan olsun, yanına
grup değiştirme düğmesi konsun. 2. Lig'de Bursa kulüpleri iki gruba dağıldığı
için tek grup göstermek bir kulübü dışarıda bırakır.

### Takip edilen takım

Bursaspor'un hangi ligde olduğu **kodda yazılı değil**; her koşuda dört ligin
tablosunda aranır. Küme düştüğünde/çıktığında betik değişmez.
26 Ağustos 2026 ölçümü: **Trendyol 1. Lig, 5. sıra, 6 puan**; 4. hafta maçı
29.08.2026 19:00, Metro Holding Kayserispor – Bursaspor (deplasman).

### Kendi kendini denetler

Her koşuda iki eşitlik ölçülür ve `denetim` bloğuna yazılır:
`oynadı = galibiyet + beraberlik + mağlubiyet` ve `averaj = attığı − yediği`.
Puan denetlenmez: TFF ceza silmesi uyguluyor (ölçüldü — Adana Demirspor
2026-2027 sezonuna −24 ile başladı), yani `puan = 3G + B` doğru değil.
Ayrıştırma kayması en önce bu iki eşitlikte görünür.

### Kullanım şartları — dikkat

TFF Kullanım Şartları (`pageID=179`):

> Sitede yer alan bilgiler, **kaynak gösterilmek suretiyle yayımlanabilir**;
> ancak bu bilgiler **ticari amaçlarla kullanılamaz**.

Gazete ticari bir yayındır. Karşı görüş: puan cetveli **olgudur**, FSEK eser
korumasına girmez ve her gazete tabloyu TFF'ye atıf vererek basar. Betik
kaynağı çıktıya yazar (`kaynak` bloğu) ve sayfada "Kaynak: TFF" görünmesi
gerekir. **Bu madde hukuk teyidine gitmeli** — panel projesindeki diğer
hukuki teyit kalemleriyle birlikte.

---

## Vizyon takvimi

Dört kaynak var, hiçbiri ötekinin yerine geçmez.

```powershell
$env:TMDB_ANAHTAR = "..."
python canli-veri\vizyon_takvimi.py                     # tmdb, 3 ay
python canli-veri\vizyon_takvimi.py --ay 6
python canli-veri\vizyon_takvimi.py --kaynak vikiveri   # anahtarsız
python canli-veri\vizyon_takvimi.py --kaynak elle
python canli-veri\vizyon_takvimi.py --kaynak boxoffice --yazili-izin-var
```

| Kaynak | Anahtar | Kapsam | Durum |
|---|---|---|---|
| `tmdb` | ücretsiz anahtar gerekir | geniş, TR vizyon tarihi doğrudan | **varsayılan** |
| `vikiveri` | yok | çok dar — ölçüldü: 2026-08/2027-01 arası TR vizyon tarihi girilmiş film **1** | yedek / çapraz kontrol |
| `boxoffice` | yok | TR takviminin en eksiksiz açık listesi | **yazılı izin olmadan çalışmaz** |
| `elle` | yok | panelden girilen kadarı | kalıcı düşmede çalışan yol |

### boxofficeturkiye neden kilitli

`robots.txt` taramaya izin veriyor ama Kullanım Koşulları madde 14 açık:

> İnternet Sitesi'nde bulunan her türlü haber, bilgi ve sair materyaller
> sadece Site'ten **yazılı izin alınması kaydıyla** … kullanılabilir …
> çoğaltılamaz … yayınlanamaz.

Planın kendi kuralı: *"Her kaynağın kullanım şartları okunacak; kazıma yasaksa
o kaynak elenecek."* Bu yüzden kaynak **kodda duruyor ve çalışıyor** ama
`--yazili-izin-var` bayrağı verilmeden başlamaz; bayrak yoksa betik nedenini
yazıp çıkış kodu 2 ile döner. Ayrıştırıcı çevrimdışı doğrulandı: 2026 Ağustos
sayfasından **30 film, 4 vizyon günü**, tür ve dağıtımcı alanlarıyla birlikte.
İzin alınırsa tek bayrakla devreye girer.

### Afiş — indirilmez

Film afişi telifli bir eserdir. Betik **afiş dosyası indirmez**. Her kayıtta:

```json
"afis_kaynak": "https://…",   // yalnız künye; dosya taşınmaz
"afis_yayinlanabilir": false
```

Sayfa yerel yer tutucu gösterir. Afişi basmak için hak sahibinden
(dağıtımcı) izin gerekir; ayrıntı için `URUN-PLANI.md` §9.

---

## Çıktı biçimi

Alan adları `arac/konular.json` ile aynı düzende: anahtarlar aksansız ASCII,
değerler tam Türkçe. Her dosyanın başında `_not`, `guncelleme`,
`bayat_esik_dakika` ve `kaynak` bulunur; şablon bayatlığı bu üçünden karar
verir.

```
veri/
  doviz.json                beş kalem + bülten künyesi + değişim
  durum-doviz.json          taze | eski | yok  + hata + yaş
  doviz-elle.json           (elle giriş — panel yazar, artık son çare)
  piyasa.json               gram altın + BIST 100 (+ doğrulama için dolar/euro)
  durum-piyasa.json
  hava-durumu.json          merkez + son durum + 5 gün + saatlik
  durum-hava-durumu.json
  hava-elle.json            (elle giriş kaynağı — panel yazar)
  namaz-vakitleri.json      gün gün altı vakit + yöntem + doğrulama ölçümü
  durum-namaz-vakitleri.json
  namaz-elle.json           (elle giriş kaynağı — panel yazar)
  nobetci-eczane.json       nöbetçi eczaneler + ilçe listesi
  durum-nobetci-eczane.json
  eczane-elle.json          (elle giriş kaynağı — panel yazar)
  puan-durumu.json          dört lig + takip edilen takım
  durum-puan-durumu.json
  vizyon-takvimi.json       vizyon günlerine bölünmüş film listesi
  durum-vizyon-takvimi.json
  vizyon-elle.json          (elle giriş kaynağı — panel yazar)
  log-*.txt
```

Her bileşen dosyasının sonunda bir `denetim` bloğu vardır: kaç kayıt geldi,
kaç alan boş kaldı, ne doğrulanamadı. Bozuk veri sessizce yayına gitmesin
diye konmuştur; şablon bu bloğa bakarak da uyarı basabilir.

## Zamanlama

Bu betikler kendi başına zamanlayıcı içermez. Sunucuda `cron`/Görev
Zamanlayıcı çağırır. Aynı anda tek koşu; iki koşu birbirinin dosyasını
bozmaz (atomik yazım) ama kaynağa gereksiz yük biner.

Önerilen sıklık:

| Betik | Ne sıklıkla |
|---|---|
| `doviz.py` | iş günü 15:35 ve 16:35 (bülten 15:30'da çıkar) |
| `piyasa.py` | **15 dakikada bir** — borsa açıkken 09:30-18:30 yeter, gün boyu da zararsız |
| `hava_durumu.py` | saat başı |
| `namaz_vakitleri.py` | günde bir, gece yarısından sonra (`--gun 30`) |
| `nobetci_eczane.py` | günde iki kez — 08:00 ve 18:00 (nöbet 18:30'da devrediliyor) |
| `puan_durumu.py` | maç günü saatte bir, diğer gün günde bir |
| `vizyon_takvimi.py` | haftada bir, perşembe akşamı |

## F6'nın durumu

Yedi bileşenden **altısı** bu klasörde çalışıyor: döviz · hava · namaz ·
eczane · puan durumu · vizyon takvimi. Bursaspor maç skoru ayrı betik
değil, `puan_durumu.py`nin içinde geliyor — yani **yedi kalemin hepsinin**
kaynağı, sıklığı ve düşme davranışı yazılı ve ölçülmüş durumda.

**27 Ağustos 2026: son açık kapandı.** Döviz bandının gram altın ve BIST 100
kutuları artık elle girişe muhtaç değil; `piyasa.py` dört kaynaktan çekiyor
(TCMB EVDS · Google Finance · doviz.com · Mynet Finans) ve `doviz.py`
sonucu okuyor.
Bandın beş kalemi de kaynaktan doluyor — `denetim.kaynagi_olmayan` boş.

Elle giriş yolu (`doviz-elle.json`) **silinmedi**, son çare olarak duruyor:
üç kaynak birden düşer ya da `piyasa.json` bayatlarsa devreye girer.

Açık kalan tek şey **çekme değil izin**: Google Hizmet Şartları maddesi,
TCMB / MGM / TFF maddeleriyle birlikte hukuk teyidine gitmeli
(`URUN-PLANI.md` §8). Google düşerse bant üç yedekle tam çalışmaya devam
ettiği için bu karar akışı bloke etmiyor.

**Google artık teknik olarak gereksiz.** Resmî kaynak (EVDS) 1. sıraya
girdi; gün içi canlı rakamı doviz.com ve Mynet zaten veriyor. Google'ın tek
özel katkısı kalmadı — üstelik Hizmet Şartları çekincesi olan tek kaynak o.
Sıradan çıkarmak için `VARSAYILAN_SIRA`'dan `"google"` silmek yeter, başka
değişiklik gerekmez; koşu süresi de **19 sn'den 0,3 sn'ye** iner (ölçüldü).
Bir kaynağı listeden çıkarmak ürün kararı olduğu için bu adım **bilerek
atılmadı**, karar sizde.

**Dolar/euro tarafı EVDS'ye taşınmadı — gerekçe ölçüldü.** EVDS'nin gösterge
ucu kurları bir gün *ileri* etiketliyor: 26.08.2026 tarihli 2026/159 numaralı
bültenin efektif alışı (47,9955) EVDS'de **27-08-2026** satırında duruyor.
Yani "daha taze" görünen rakam, `doviz.py`'nin `today.xml`'den zaten okuduğu
rakamın ta kendisi. Kazanç sıfır, kayıp üç: EVDS gösterge ucu **efektif
alış** verir (`doviz.py` bilerek **döviz alış/satış** kullanıyor), bantta
görünen bülten tarihi/numarası bir gün kayardı ve `today.xml` düz bir XML
iken diğeri bir SPA'nın arkasındaki uç. **Konu kapalı.**
