# Haber seslendirme — araç araştırması

**Tarih:** 6 Eylül 2026
**Karar gerekçesi:** Tarayıcı sesi (Web Speech API) elendi. Kalite cihazdan cihaza
değişiyor, Chrome'da Türkçe tek ses var ve o ses (`Microsoft Tolga`) belirgin biçimde
makine gibi duyuluyor. Ölçüm ve gerekçe: `DEMO-NOTLARI.md` → "Haber seslendirme".

Bu belge alternatifleri karşılaştırır. **Henüz uygulama kararı yok**; seçim
dinleme testinden sonra verilecek.

---

## 1. İşin büyüklüğü (kendi veritabanımızdan ölçüldü)

`uygulama/db.sqlite3`, `icerik_haber` tablosu. Gövdedeki HTML etiketleri ayıklanıp
başlık + spot + gövde toplandı; 3.000 haberlik rastgele örnek.

| Ölçü | Değer |
|---|---|
| Toplam haber | **1.038.477** |
| Haber başına okunacak karakter (ortalama) | **1.777** |
| Medyan / p90 | 1.322 / 3.412 |
| Haber başına ses süresi (~900 karakter/dk) | **~2 dakika** |
| Son 30 günde yayımlanan | 3.878 haber → **~6,9 milyon karakter/ay** |
| Son 1 yılda yayımlanan | 75.513 haber → ~134 milyon karakter |
| **Tüm arşiv** | **~1,85 milyar karakter ≈ 34.600 saat ses** |

**Bu tablonun tek sonucu var:** arşivin tamamını önceden seslendirmek hiçbir yolla
mümkün değil — ne parayla ne de kendi donanımımızla (aşağıda). Mimari bunun üzerine
kurulmalı.

---

## 2. Elenenler (araştırmanın en önemli çıktısı)

Bunlar teknik olarak çalışır ama **hukuken kullanamayız**. Gazete ticari bir
yayın organı; "açık kaynak" ile "ticari kullanıma açık" aynı şey değil.

| Araç | Neden elendi |
|---|---|
| **Coqui XTTS-v2** | Ağırlıklar Coqui Public Model License ile **ticari kullanıma kapalı**. Kod MPL-2.0 ama model değil. Coqui Inc. Ocak 2024'te kapandı → ticari lisans satın alınacak bir muhatap da yok. Türkçe desteği ve kalitesi iyi olduğu için en çok önerilen model bu; bizim için kullanılamaz |
| **Meta MMS-TTS (`facebook/mms-tts-tur`)** | CC-BY-NC 4.0 — ticari kullanım yasak |
| **Piper — Türkçe sesler** | Üç Türkçe ses var (`dfki`, `fahrettin`, `fettah`), hepsi "medium". `dfki` sesinin veri seti **CC BY-NC-SA 4.0** → ticari kullanım kapalı. Ayrıca kullanıcı geri bildirimleri Türkçe telaffuzun kusurlu olduğunu söylüyor (yumuşak ünlüler, `ğ`). Piper'ın kendisi (motor) sorunsuz; sorun Türkçe ses paketlerinde |
| **edge-tts** | Edge'in "Sesli Oku" ucuna anahtarsız bağlanan bir kütüphane. Emel Natural sesini bedava verir — ama bu Microsoft'un kapalı servisine belgelenmemiş erişim. Microsoft ticari kullanım için Azure aboneliğini işaret ediyor; abonesiz ticari kullanım ToS ihlali sayılabiliyor. **Bir gazetenin altyapısını buraya kuramayız** |
| **eSpeak NG** | GPL-3, her yerde çalışır, ama tarayıcıdaki Tolga'dan daha robotik. Elediğimiz sorunu geri getirir |
| **Kokoro-82M** | 2026'nın en çok önerilen açık modeli, Apache-2.0 — **ama Türkçe yok** (8 dil, Türkçe listede değil) |

---

## 3. Gerçek adaylar

### A. Bulut servisleri (anahtar gerekir, karakter başına ödeme)

| Servis | Türkçe ses | Liste fiyatı /1M karakter | Not |
|---|---|---|---|
| **Google Cloud TTS — Standard** | tr-TR var | **~4 $** | En ucuz; kalite eski nesil |
| **Google Cloud TTS — Chirp 3: HD** | **tr-TR destekleniyor** | ~30 $ | 2026'nın en iyi ses tiplerinden; Türkçe ses adları API'den (`voices.list`) çekilmeli |
| **Azure AI Speech — Neural** | `tr-TR-EmelNeural`, `tr-TR-AhmetNeural` | ~16 $ | Bu makinede Edge üzerinden zaten dinlendi: Emel kabul edilebilir bulunmuştu. Türkçe için **HD/Dragon** katmanının açık olup olmadığı doğrulanmadı |
| **Amazon Polly — Neural** | `Burcu` (Şubat 2024'te eklendi), `Filiz` (standard) | ~16 $ | Türkçe'de tek neural ses |
| **OpenAI `gpt-4o-mini-tts`** | Çok dilli | ~12 $ /1M ses çıktı jetonu | Karakter değil jeton üzerinden; talimatla ton verilebiliyor ("haber spikeri gibi oku") |
| **ElevenLabs** | 70+ dil | ~100 $ (Flash ~50 $) | En doğal ses, en pahalı yol |
| **SESTEK Knovvu** (yerli) | Türkçe ana uzmanlık alanı | Fiyat listesi yok, teklif usulü | Türkçe konuşma teknolojilerinde pazar lideri; prozodi ve kısaltma/sayı okuma Türkçe'ye göre kurulmuş olabilir. **Teklif istenmeli** |

> Fiyatlar ikincil kaynaklardan derlenen **liste fiyatlarıdır**, teyit edilmedi.
> Hacim indirimi ve ücretsiz katman (Google 4M, Azure 500K karakter/ay) hesaba katılmadı.

### B. Kendi sunucumuzda çalışan modeller (anahtar yok, aylık ücret yok)

| Model | Lisans | Türkçe | Durum |
|---|---|---|---|
| **Chatterbox Multilingual** (Resemble AI) | **MIT** | 23 dil içinde **Türkçe var** | En güçlü aday. Kendi sunucumuzda çalışır, ağırlıklar denetlenebilir, veri dışarı çıkmaz. Sıfır atışlı ses klonlama var → **gazetenin kendi spikerinin sesi** (yazılı izinle) kullanılabilir. Her çıktı PerTh ile filigranlanıyor. GPU ister |
| **Trendyol-TTS** | MIT | Türkçe'ye özel eğitilmiş | VoxCPM2 üzerine LoRA. Geliştiricisi açıkça "araştırma seviyesi, üretime hazır değil" diyor. İzlenmeli, bugün kurulmaz |
| **TurkicTTS** | Apache-2.0 | Türk dilleri | Ticari kullanıma açık nadir seçeneklerden; kalitesi dinlenmedi |

**Donanım gerçeği:** GPU'da gerçek zamanın ~3 katı hızla üretim varsayımıyla günlük
130 haber (~4,3 saat ses) tek bir GPU'da **günde ~1,5 saat** iş demek — rahatlıkla
kaldırır. Aynı hesapla **arşivin tamamı tek GPU'da ~480 gün** sürer. Yani arşiv,
parayla da donanımla da toptan seslendirilemez.

---

## 4. Önerilen mimari (araçtan bağımsız)

Hangi araç seçilirse seçilsin yapı aynı olmalı:

1. **Yayın anında üret.** Haber yayımlanınca ses dosyası bir kez üretilir, diske
   yazılır, habere bağlanır. Okuyucu her açtığında yeniden üretilmez.
2. **Arşiv istek üzerine.** Eski bir haberde "Dinle"ye ilk basan kişi üretimi
   tetikler; dosya kalıcı olarak saklanır, ikinci kişi hazır dosyayı dinler.
   1,85 milyar karakter böylece gündemden çıkar — yalnızca gerçekten dinlenen
   haberler maliyet üretir.
3. **Metin düzeltmesi ses üretiminden önce.** Türkçe'de asıl kaliteyi tarih
   ("21.08.2026"), para ("₺1.250"), kısaltma ("TBMM", "Dr.") ve büyük sayıların
   okunuşu belirler. Bu katman bizde olmalı; hiçbir servis Türkçe'ye özel bunu
   bizim istediğimiz gibi yapmıyor. `arac/sozluk.json` bunun için iyi bir başlangıç.
4. **Haber güncellenirse ses geçersizleşir.** Gövde değiştiğinde dosya silinir,
   yeniden üretilir. Yanlış ses dosyası, ses olmamasından kötüdür.
5. **Oynatıcı arayüzü aynen kalır.** `uygulama/sablonlar/parca/seslendirme.html`
   ve CSS'teki `.ses-*` düzeni korunur; değişen yalnızca sesin nereden geldiği.
   Paragraf işaretleme özelliği ses dosyasına geçince **zaman damgası** ister —
   servis kelime/cümle zamanlaması veriyorsa (Azure ve Polly `speech marks` verir)
   korunur, vermiyorsa bu özellik düşer. **Seçimde bu belirleyici olabilir.**

---

## 5. Karar bekleyen sorular

1. **Ses kimin olacak?** Hazır servis sesi mi, gazetenin kendi spikerinin klonlanmış
   sesi mi? İkincisi Chatterbox ile mümkün ama **yazılı muvafakat** ister ve
   kimlik/telif açısından ayrı bir hukuki başlıktır.
2. **Aylık gider mi, tek seferlik donanım mı?** Bulut ~110 $/ay (Azure/Polly neural,
   yalnız yeni haberler) ile başlar ve dinlenme arttıkça artar. Kendi sunucumuz
   peşin donanım + bakım ister, sonra sabittir.
3. **Paragraf takibi korunacak mı?** Bugünkü oynatıcının en iyi yanı bu. Korunacaksa
   zaman damgası veren servisler öne çıkar.
4. **Arşivin tamamı mı, son dönem mi?** Örneğin yalnız son 1 yıl (75.513 haber,
   134M karakter) önden üretilirse: Standard ~537 $, Neural ~2.148 $, Chirp3-HD
   ~4.027 $ tek seferlik.

---

## 5a. Verilen kararlar (6 Eylül 2026)

Kullanıcı kararıyla kapsam daraldı:

- **Paragraf takibi kalacak.** Bugünkü oynatıcının paragraf işaretlemesi korunur.
- **Ses hazır servis sesi olacak.** Spiker klonlama yolu (Chatterbox) kapandı;
  kendi sunucumuzda model çalıştırma da bu kararla gündemden çıktı.
- **Arşivin tamamı seslendirilmeyecek.** Kapsam: **2026'da yüklenen haberler +
  bundan sonra yayımlanacaklar.** 2025 ve öncesi (986.865 haber) kapsam dışı.

### Kapsamın ölçüsü (tam sayım, örnekleme değil)

`yayin_zamani >= 2026-01-01` olan tüm kayıtlarda HTML ayıklanıp sayıldı:

| Ölçü | Değer |
|---|---|
| 2026'da yüklenen haber (Ocak–Ağustos) | **51.612** |
| Okunacak karakter | **92.875.545 (~92,9 milyon)** |
| Haber başına ortalama | 1.799 karakter |
| Ses süresi | **~1.719 saat** |
| Aylık yayın hızı | ~6.451 haber → **~11,6 milyon karakter/ay** |
| Yıllık (ileriye dönük) | ~139 milyon karakter |

### Maliyet

Kur: **1 $ = 48,4354 TL** (6 Eylül 2026, `canli-veri/veri/doviz.json`, TCMB).
"Tek sefer" = 2026'nın 51.612 haberinin tamamı bir kerede seslendirilirse.

| Servis | 2026 tek sefer | Aylık (yeni haberler) | Yıllık |
|---|---|---|---|
| Google Standard | 372 $ (17.994 TL) | 46 $ (2.249 TL) | 557 $ |
| **Azure Neural (Emel/Ahmet)** | **1.486 $ (71.975 TL)** | **186 $ (8.997 TL)** | 2.229 $ |
| **Polly Neural (Burcu)** | 1.486 $ (71.975 TL) | 186 $ (8.997 TL) | 2.229 $ |
| Google Neural2 / WaveNet | 1.486 $ (71.975 TL) | 186 $ (8.997 TL) | 2.229 $ |
| Azure Neural HD | 2.043 $ (98.966 TL) | 255 $ (12.371 TL) | 3.065 $ |
| **Google Chirp 3: HD** | 2.786 $ (134.954 TL) | 348 $ (16.869 TL) | 4.179 $ |
| ElevenLabs Flash | 4.644 $ (224.923 TL) | 580 $ (28.115 TL) | 6.966 $ |
| ElevenLabs Multilingual | 9.288 $ (449.846 TL) | 1.161 $ (56.231 TL) | 13.931 $ |

Ücretsiz katmanlar düşülmedi (Azure 500K karakter/ay, Google premium seslerde
1M/ay) — bu ölçekte aylık faturayı ~%5-8 azaltır.

**Depolama ve trafik:** 48 kbps mono MP3 ile 2026 arşivi **~36 GB**, her yıl
**+54 GB**. Depolama önemsiz; asıl kalem trafiktir — her dinleme ~0,7 MB indirir.

### Maliyeti düşüren tek karar

**2026 arşivini önden değil, ilk dinleme isteğinde üret.** Yeni haberler yayın
anında seslendirilir (aylık gider zaten oluşuyor); 2026'nın 51.612 haberi ise
biri "Dinle"ye bastığında üretilip kalıcı saklanır. Arşiv trafiği uzun kuyruklu
olduğu için 1.486 $'lık tek seferlik kalemin büyük bölümü hiç harcanmaz.
Ödenen para = gerçekten dinlenen haber.

### Paragraf takibi: satıcı seçimini bağlamıyor

Zaman damgası API'lerine bakıldı — Azure `WordBoundary` olaylarını, Polly
`speech marks`'ı, ElevenLabs karakter düzeyinde zaman damgası veriyor; Google
Chirp 3: HD'de SSML desteği sınırlı ve zaman damgası belgelenmemiş.

**Ama buna ihtiyaç yok.** Ses **paragraf paragraf** üretilip birleştirilirse her
paragrafın başlangıç saniyesi zaten elimizde olur — süreler toplanarak. Bu yol
her servisle çalışır, karakter maliyetini değiştirmez ve haberin bir paragrafı
düzeltildiğinde yalnız o parçanın yeniden üretilmesini sağlar. Oynatıcının
`.ses-okunan` işaretlemesi ve "5/13 paragraf" göstergesi olduğu gibi korunur.
**Yani paragraf takibi şartı hiçbir adayı elemiyor.**

## 5b. Yerelde çalıştırma: hakkı satın alınabilir model araştırması (6 Eylül 2026)

Karakter başına ödemenin sürekli bir gider olması nedeniyle soru şuna döndü:
**hakkını bir kez alıp kendi sunucumuzda çalıştırabileceğimiz bir ses modeli var mı?**
Var — ve rakamlar bulut seçeneğiyle kıyaslanacak gibi değil.

### Ticari kullanıma açık + Türkçe + yerelde çalışan

| Model | Lisans | Durum |
|---|---|---|
| **Chatterbox Multilingual v3** (Resemble AI, Haziran 2026) | **MIT** | 21 dil + 4 lehçe, **Türkçe var**. 0.5B (Turbo 350M). **2-3 GB VRAM** yetiyor. RTX 4090'da gerçek zamanın ~5-6 katı hızda üretiyor. Üreticinin kör testinde dinleyiciler ElevenLabs'a karşı %63,75 oranında bunu tercih etmiş (**satıcının kendi iddiası**, Türkçe için doğrulanmadı). Çıktılar PerTh ile filigranlı — gazete için dezavantaj değil, köken kanıtı |
| **TurkicTTS** | Apache 2.0 | 10 Türk dili, Türkçe dahil. Kalitesi dinlenmedi |
| **Kendi sesimizi eğitmek** (Piper/VITS) | Motor MIT; ses bize ait olur | Seslendirmenden stüdyo kaydı satın alınır, model eğitilir. **GPU'suz, CPU'da** çalışır. Kalite orta-üstü; gazeteye özel, başka kimsede olmayan bir ses |
| **Acapela** | Ticari, on-premise SDK | Türkçe **İpek** sesi var, Windows/Linux sunucu SDK'sı satıyor. Eş zamanlı kullanıcı sayısına göre lisans; teklif alınmalı |

### Bu turda elenenler

| Aday | Neden |
|---|---|
| **Qwen3-TTS** (Alibaba, Ocak 2026) | Apache 2.0, 0.6B/1.7B, ses tasarımı ve klonlama var — **ama 10 dilinin içinde Türkçe yok** |
| **Fish Speech / OpenAudio S1** | Kod Apache ama **ağırlıklar CC-BY-NC-SA**; ayrıca Türkçe desteklenen diller arasında değil |
| **Higgs Audio V3** (Boson AI) | Araştırma / ticari olmayan lisans |
| **CereProc** | Dil listesinde Türkçe yok |

### Maliyet: kiralık GPU ile

Chatterbox 2-3 GB VRAM istediği için pahalı donanım gerekmiyor. Kiralık GPU
(RTX 4090, Vast.ai/RunPod topluluk katmanı ~0,34 $/saat) ve gerçek zamanın 5 katı
üretim hızı varsayımıyla:

| Kapsam | Ses süresi | GPU saati | **Yerel (kiralık GPU)** | Azure Neural |
|---|---|---|---|---|
| 2026 arşivi (51.612 haber) | 1.720 saat | 344 | **117 $ · 5.665 TL** (tek sefer) | 1.486 $ · 71.975 TL |
| Aylık yeni haberler | 215 saat | 43 | **15 $ · 708 TL /ay** | 186 $ · 8.997 TL /ay |
| **Tüm arşiv (1.038.477 haber)** | 34.167 saat | 6.833 | **2.323 $ · 112.532 TL** | 29.520 $ · **1.429.813 TL** |

Kendi GPU'muz alınırsa değişken gider elektriğe iner: 2026 arşivinin tamamı
~103 kWh (**~310 TL**), aylık üretim ~13 kWh (**~39 TL**).

**Tabloda en çok konuşulması gereken satır sonuncusu.** Bulutta "imkânsız" dediğimiz
tüm arşiv — bir milyon haber — yerel modelle **112.532 TL**'ye, kendi GPU'muzla
elektrik parasına iniyor. "İstek üzerine üretim" zorunluluğu bu yolda ortadan kalkıyor.

### Karşılığında kabul edilen riskler

1. **Türkçe kalitesi doğrulanmadı.** Chatterbox'ın Türkçe çıktısı dinlenmeden karar
   verilemez. Türkçe'nin ünlü uyumu, `ğ` ve kısaltma okuyuşu asıl sınav.
2. **Bakım bizde.** Bulut servisinde ses motoru satıcının derdi; burada bizim.
   Model güncellemesi, kuyruğun izlenmesi, hata durumunda yedeğe düşme.
3. **Referans ses meselesi.** Chatterbox sıfır atışlı klonlama yapan bir model;
   üreteceği ses bir referans kayıttan gelir. Bu kayıt **rastgele birinin sesi
   olamaz**. Doğru yol, bir seslendirmenden **sentetik ses hakkını sözleşmeyle
   satın almak**: sektörde bu, normal seslendirme ücretinden ayrı fiyatlanan bir
   kalemdir (NAVA'nın "AI rider" düzeni). Ses gazetenin markası hâline gelir.
   Alternatif, modelin varsayılan sesiyle yetinmek — kurulumda hangisinin mümkün
   olduğu görülmeli.
4. **İlk kurulum emeği.** Bulut servisinde bir API anahtarı yeter; burada model
   sunucusu, kuyruk ve dosya yönetimi kurulacak.

## 5c. Higgsfield ses araçları (20 Ekim 2026)

Higgsfield kendi ses modeli olan bir servis değil; başka sağlayıcıların modellerini
kredi karşılığı satan bir aracı. Fiyatlar hesabın kendi maliyet sorgusuyla
(`get_cost`, üretim yapmadan) 1.691 karakterlik Türkçe bir metinle ölçüldü,
haber başına 1.800 karaktere ölçeklendi. Hacim: **günde 50 haber → ayda 1.500
haber → ~2,7 milyon karakter.**

| Model (Higgsfield içinde) | Kredi/haber | Kredi/ay | Ultra yıllık (99 $) + ek paket |
|---|---|---|---|
| Seed Speech (ByteDance) | 3,6 | ~5.430 | ~227 $ · ~11.000 TL |
| ElevenLabs · MiniMax · Eleven v4 Turbo | 5,4 | ~8.140 | ~370 $ · ~17.900 TL |
| Eleven v4 | 8,3 | ~12.490 | ~598 $ · ~29.000 TL |
| Seed Audio 1.0 (varsayılan model) | 12,0 | ~18.040 | ~891 $ · ~43.200 TL |

Kredi fiyatı: Ultra yıllık 3.000 kredi/ay 99 $ (0,033 $/kredi), ek paket 4.000
kredi 210,53 $ (0,053 $/kredi, **90 günde sona erer**). Kur 48,52 TL (TCMB
11 Eylül bülteni — `doviz.json` o tarihten beri tazelenmemiş).

**Sonuç:** Higgsfield üzerinden ElevenLabs ~100–160 $/1M karakter ediyor;
ElevenLabs'ın doğrudan fiyatı (Flash ~50 $, Multilingual ~100 $) bundan ucuz ya
da eşit. Azure/Polly Neural aynı hacimde ~43 $/ay, yerel model birkaç dolar.
Aracıya ödeme yapmanın maliyet açısından getirisi yok.

**Doğrulanmayanlar:** Hiçbir Higgsfield sesi Türkçe etiketli değil (hazır seslerin
hepsi İngilizce adlı); Seed Speech/Seed Audio'nun Türkçe desteği belirsiz, Qwen
Audio'nun dil listesinde Türkçe **yok**, Vibe Voice ve Cozy Voice'un Türkçesi
beklenmez. Sitenin sunucusundan otomatik üretim için Higgsfield'in herkese açık
bir TTS API'si ve ticari kullanım koşulları ayrıca doğrulanmalı — buradaki ölçüm
kullanıcı hesabının MCP bağlantısıyla yapıldı.

## 5d. Geniş tarama: ücretli, ücretsiz, açık kaynak (20 Ekim 2026)

Hacim: günde 50 haber → ayda ~1.500 haber, **~2,7 milyon karakter, ~50 saat ses.**
Fiyatlar ikincil kaynaklı liste fiyatları; ücretsiz katman düşüldü.

### Yeni bulunan: Türkçeye özel, ticari kullanıma açık, CPU'da çalışan modeller

6 Eylül turunda görülmemişti. Üçü de GPU istemiyor; mevcut sunucuda çalışabilir.

| Model | Lisans | Ölçülen kalite | Not |
|---|---|---|---|
| **FreyaTTS-small** (183M) | Apache-2.0 (kod + ağırlık) | Freya-TR-Eval: WER %8,0, **MOS 3,68** (24 Türk dinleyici) — XTTS-v2 3,82 | Tek ses. CPU'da gerçek zamanlı, GPU'da 10 kat hızlı. Büyük sürüm ticari, satıcıyla görüşülür |
| **EMA-TTS** (65M) | Apache-2.0 | WER %3,0 (kendi beyanı) | Tek ses, klonlama yok. Uzun cümlede iyi, 1-2 kelimede zayıf; özel isimlerde hata |
| **Pocket TTS Turkish** (~110M) | CC-BY-4.0 (atıf şart) | WER %1,9 (kendi beyanı) | Tek CPU çekirdeğinde 5 kat gerçek zaman. Klonlama var. Eğitim sesi **sentetik**, yazarın kendi modeliyle üretilmiş — o modelin kökeni belirsiz |
| **VoxCPM2** (2B) | Apache-2.0 | Türkçe 30 dil arasında; dile göre kalite değişir | 5,5 GB VRAM, GPU ister. Trendyol-TTS bunun üzerine kurulu, Trendyol hâlâ "üretime hazır değil" diyor |

Uyarı: Freya ve EMA eğitim verisini adlandırmıyor. Ağırlık lisansı temiz, veri
kökeni doğrulanmadı. Freya-TR-Eval tablosunda en düşük hata Piper-dfki ve
MMS-TTS'te; ikisi de ticari kullanıma kapalı (§2).

### Bulut: aylık tahmini fatura (2,7M karakter)

| Servis | Türkçe | ~Aylık |
|---|---|---|
| Google Standard | var | **0 $** (4M/ay ücretsiz katmana sığıyor; kalite eski nesil) |
| Google Neural2/WaveNet | var | ~27 $ |
| Azure Neural (Emel/Ahmet) | var | ~35 $ |
| Polly Neural (Burcu) | var | ~43 $ |
| OpenAI gpt-4o-mini-tts | çok dilli | ~45 $ (~0,015 $/dk) |
| Google Chirp 3: HD | var | ~51 $ (ilk 1M ücretsiz) |
| Gemini TTS (2.5 Pro / 3.1 Flash) | 90+ dil, Türkçe teyit edilmedi | ~90 $ (ses jetonu: 25/sn, 20 $/1M) |
| ElevenLabs Flash / v3 | var | ~135 $ / ~270 $ |
| MiniMax speech-2.8 turbo / hd | var | ~162 $ / ~270 $ |
| Cartesia Sonic-3 | var | kredi tablosu yayımlanmıyor |
| Deepgram Aura-2 | 7 dil, Türkçe görünmüyor | (~30 $/1M) |
| Higgsfield (aracı) | belirsiz | 227–891 $ (§5c) |

### Haber sitelerine özel sesli makale platformları

**Trinity Audio**: oynatıcı + ses + reklam paraya çevirme bir arada; WordPress
eklentisi Türkçeyi listeliyor (bazı diller yalnız ücretli planda). Planlar makale
adedine göre (~16–150 $/ay, 1.000 kelime = 1 makale); ayda 1.500 makale büyük
olasılıkla özel teklif ister. **BeyondWords**: fiyat yayımlanmıyor, demo usulü.
İkisi de ses dosyasını kendi altyapısında tutar — paragraf takipli kendi
oynatıcımızla uyuşmaz.

## 5e. Gemini TTS denemesi — gerçek haberle ölçüldü (21 Ekim 2026)

Anahtar kökteki `.env` içinde `GEMINI_API_KEY` (git'e girmiyor). Anahtarla açık
TTS modelleri: `gemini-3.8-flash-tts`, `gemini-3.8-flash-lite-tts` (ikisi kararlı,
Türkçe resmî destekli), ayrıca 3.1/2.5 önizlemeleri.

**Fiyat** (USD / 1M jeton, ses jetonu = saniyede 25; 31 Aralık 2026'ya kadar,
parantezde 1 Ocak 2027'den itibaren):

| Model | Girdi metin | Çıktı ses | Batch/Flex çıktı |
|---|---|---|---|
| 3.8 Flash TTS | 0,50 (1,00) | 9,00 (18,00) | 4,50 (9,00) |
| 3.8 Flash-Lite TTS | 0,50 (1,00) | 6,00 (12,00) | 3,00 (6,00) |

**Deneme haberi:** #1696013 "Bursa Yıldırım'da peş peşe su kesintisi! BUSKİ…",
2.066 harf, 18 bölüm (başlık + spot + 16 paragraf; 4'ü BÜYÜK HARFLİ ara başlık).

| Deneme | Ses süresi | Çıktı jetonu | Bekleme | Bu haberin maliyeti |
|---|---|---|---|---|
| Flash-Lite, tek istek | 119,4 sn | 2.983 | 16,6 sn | 0,018 $ |
| Flash, tek istek | 126,0 sn | 3.147 | 32,4 sn | 0,029 $ |
| Flash-Lite, paragraf paragraf (18 istek) | 141,2 sn (6,3 sn'si eklenen sessizlik) | 3.316 | 2–3,5 sn/istek | 0,020 $ |

Paragraf paragraf üretim ~%11 daha fazla jeton harcıyor (her parçanın baş/son
boşluğu), karşılığında paragraf başlangıç saniyeleri doğrudan elde ediliyor.

**Aylık (2,7M karakter, paragraf paragraf):** Flash-Lite ~26 $ (2027'de ~52 $),
Flash ~41 $ (2027'de ~82 $). Batch/Flex fiyatıyla yarısı. Girdi jetonu
(~0,9M) aylık 0,5 $'ın altında, önemsiz.

**Telaffuz denetimi** (sesler `gemini-3.8-flash`'a duyulduğu gibi yazdırıldı —
bir yapay zekânın dökümü, insan kulağının yerini tutmaz):
- `09.00` → "dokuz", `25 Ağustos 2026` → "yirmi beş Ağustos iki bin yirmi altı": üçü de doğru.
- `BUSKİ` → "Buski" (kelime gibi): üçü de doğru, yerel kullanımla aynı.
- Büyük harfli ara başlıklar bağırarak/aşırı vurguyla **okunmamış**.
- Sıra sayıları: Flash ve paragraf kipindeki Lite hepsini doğru okudu
  ("kırkıncı Sokak", "yirmi birinci Cadde"). **Tek istekli Lite iki yerde
  kaçırdı**: `40. Sokak` → "kırk", `21. ve 22. Caddeler` → "yirmi bir ve yirmi ikinci".
  Metin düzeltme katmanı (§4.3) sıra sayılarını yazıya çevirirse sorun kalkar.

**Hız sınırı:** Dakikada ~15 istekten sonra 429 döndü (anahtarın katmanı
ücretsiz olabilir — doğrulanmadı). Günde 50 haber × ~18 parça ≈ 900 istek;
üretim için faturalı katman ya da istekleri yayına yayan bir kuyruk gerekir.
Ücretsiz katmanda Google verileri ürün geliştirmede kullanabilir.

### Ses seçimi ve "tek istek" riski (21 Ekim, ikinci tur)

- 30 temel ses çok dilli; ~yarısı kadın (Kore, Erinome, Gacrux, Sulafat, Zephyr,
  Leda, Aoede, Despina, Achernar…). Genişletilmiş kütüphanede 1.000 ses daha var
  ama hepsi aksana bağlı; `languageCode=tr-TR` filtresi **0** döndürüyor (aynı
  filtre de-DE için 87). Kullanıcı kararı: sesin Türkçe olması şart değil.
- Denenen kadın sesleri (Kore, Erinome, Gacrux, Sulafat) ve iki İngilizce
  kütüphane sesi (`en-gb-podcaster-2`, `en-ie-podcaster-1`) Türkçeyi aksansız
  okudu (yapay zekâ değerlendirmesi). En yüksek puan **Gacrux** (10/10, hatasız).
- **Kritik bulgu:** haber tek istekte gönderilince model metni yer yer kendisi
  kısaltıyor. Harfiyen dökümle doğrulandı: Erinome ve `en-gb-podcaster-2` bir ara
  başlığı + bir cümleyi atlayıp sonraki cümleyi yeniden kurdu; Kore bir başlıkla
  paragrafı birleştirip "2026 tarihinde"yi düşürdü. Bu, büyük dil modeli tabanlı
  seslendirmenin doğası. **Haberde kabul edilemez.**
- Paragraf paragraf üretimde (kısa parçalar) atlama görülmedi: Charon ve Gacrux
  eksiksiz, sıra sayıları doğru.
- **Sonuç:** üretim yalnız paragraf paragraf yapılmalı, her parça yayından önce
  denetlenmeli. En ucuz denetim: parçanın süresi harf sayısına göre beklenen
  aralıkta mı (~14–19 harf/sn); şüpheliyse Gemini'ye yazıya döktürüp metinle
  karşılaştırmak, tutmazsa yeniden üretmek.

Deneme betikleri ve ses dosyaları oturumun geçici klasöründe; repoya alınmadı.

## 6. Sonraki adım

Karar dinlemeden verilmemeli. Önerilen: **aynı haberi** — sayı, tarih ve kısaltma
içeren gerçek bir Bursa haberi — dört yolla seslendirip yan yana dinlemek:
Azure Emel · Google Chirp 3 HD · Polly Burcu · Chatterbox (kendi sunucuda).
Deneme katmanları anahtarsız/ücretsiz başlıyor, karşılaştırma masrafsız yapılabilir.

> `CLAUDE.md`'deki "kullanıcıya sormadan bulut TTS'e geçme" kuralı duruyor.
> Bu belge araştırmadır, uygulama değil.

## Kaynaklar

- [Piper VOICES.md](https://github.com/rhasspy/piper/blob/master/VOICES.md) · [tr_TR/dfki model kartı](https://huggingface.co/rhasspy/piper-voices/blob/main/tr/tr_TR/dfki/medium/MODEL_CARD)
- [XTTS-v2 lisansı (CPML)](https://huggingface.co/coqui/XTTS-v2/blob/main/LICENSE.txt) · [ticari kullanım tartışması](https://github.com/coqui-ai/TTS/discussions/4304)
- [Chatterbox Multilingual (Resemble AI)](https://www.resemble.ai/introducing-chatterbox-multilingual-open-source-tts-for-23-languages/) · [GitHub](https://github.com/resemble-ai/chatterbox)
- [Google Chirp 3: HD sesler](https://docs.cloud.google.com/text-to-speech/docs/chirp3-hd)
- [Azure dil ve ses desteği](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support)
- [Amazon Polly Türkçe neural ses: Burcu](https://aws.amazon.com/about-aws/whats-new/2024/02/amazon-polly-neural-turkish-voice-burcu)
- [edge-tts ticari kullanım sorusu (Microsoft Q&A)](https://learn.microsoft.com/en-au/answers/questions/5925556/commercial-use-of-edge-read-aloud-voices-via-edge)
- [Açık kaynak Türkçe TTS seçenekleri rehberi](https://www.ablt.dev/blog/turkish-tts/) · [Trendyol-TTS](https://huggingface.co/Trendyol/Trendyol-TTS)
