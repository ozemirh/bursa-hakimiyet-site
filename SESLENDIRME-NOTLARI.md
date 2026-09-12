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
