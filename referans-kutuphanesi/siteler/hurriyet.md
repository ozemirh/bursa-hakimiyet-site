# Hürriyet

> **İkincil kaynak — otomatik erişim yok.** Siteye robots.txt dışında hiçbir istek atılmadı.

- Adres: https://www.hurriyet.com.tr (piyasa verisi: https://bigpara.hurriyet.com.tr)
- Katman: ulusal
- Neden seçildi: Klasik Türk gazetesi mimarisinin büyük örneği; ekonomi sayfası odak konusu.
- İnceleme: 2026-10-20 · koşul: sayfa açılmadı · konum: Türkiye
- **Erişim kararı (2026-10-20):** robots.txt'de `User-agent: *` yalnız bazı yolları kapatıyor, ama `ClaudeBot`, `anthropic-ai` ve `Claude-Web` için `Disallow: /` var (ayrıca `GPTBot`, `ChatGPT-User`, `OAI-SearchBot`, `PerplexityBot` …). `Claude-User` bölümü yok. README kuralı "en kısıtlayıcısı geçerlidir" → **yasak**. `Claude-Web` ve `ChatGPT-User` model eğitimi değil, okuma ajanları. Bu yüzden SITELER.md'deki "yalnız model eğitimi kapalı" yorumu bu siteye uymuyor ([robots](https://www.hurriyet.com.tr/robots.txt), 2026-10-20). `bigpara.hurriyet.com.tr` robots.txt'i aynı listeyi taşıyor → o da yasak ([robots](https://bigpara.hurriyet.com.tr/robots.txt), 2026-10-20).
- İstek: 2 (yalnız iki robots.txt).
- Başarım kaynağı: PageSpeed Insights API anahtarsız denendi, **günlük kota dolu (HTTP 429)**, 2026-10-20 → ölçülmedi.
- İncelenen kaynaklar: arama sonucu özetleri (WebSearch), Webrazzi arşiv haberleri, ekibin 2 Eylül 2026 tarihli önceki gözlemi (URUN-PLANI §44, §46, §59).

## Özet — en öğretici 3 çözüm

1. **Piyasa verisi ayrı bir ürün markasında (Bigpara).** Döviz, altın, borsa sayfaları ana haber alan adından ayrı bir alt alan adında. Arama sonucu özetine göre döviz sayfası serbest piyasa kurlarını veriyor, TCMB kurları için ayrı sayfaya yönlendiriyor. Hisse verisi için "15 dk gecikmeli" uyarısı var; üye girişli canlı borsa sayfaları bunun dışında ([bigpara/doviz](https://bigpara.hurriyet.com.tr/doviz/), arama sonucu özeti, sayfa açılmadı, 2026-10-20). Neden: veri ürünü kendi markası ve üyelik kapısıyla gelir taşıyabiliyor. BH'ye: **hayır** (ayrı marka), ama **"veri kaynağı + gecikme" notu evet**.
2. **Gündemde "bugün neler oldu" şeridi + plakalı sıcak gündem kartları.** Önceki gözleme göre ince bir özet şeridi ve "SICAK GÜNDEM" plakalı üç kart var (URUN-PLANI §44, 2 Eylül 2026; **bu taramada doğrulanmadı**).
3. **Bölüm sayfasında manşet altında tek sütunlu, fotoğraf solda satırlar + hızlı gündem rafı** (URUN-PLANI §46, 2 Eylül 2026, `/gundem`; **doğrulanmadı**).

## 1. Anasayfa bilgi mimarisi
Önceki gözlem: "Bugün neler oldu?" ince şeridi + "SICAK GÜNDEM" plakalı üç kart (URUN-PLANI §44, 2 Eylül 2026; kim baktı ve hangi koşulda, kayıtlı değil; **doğrulanmadı**). Blok sırası, manşet tipi, ilk ekran yoğunluğu: ölçülmedi (otomatik erişim yok).

## 2. Bölüm sayfası
Önceki gözlem (`/gundem`): başlığın yanında etiketlerle hızlı gündem rafı; manşet altında tek sütun, fotoğraf solda satırlar (URUN-PLANI §46, 2 Eylül 2026; **doğrulanmadı**). §59'da Hürriyet bölüm sayfası Guardian/BBC/NYT ile ortak "ek bloklar" kaynağı olarak anılıyor; hangi bloklar olduğu siteye özgü kayıtlı değil.
**Ekonomi:** piyasa verisi Bigpara'da. Arama sonucu özetlerine göre: döviz sayfası birçok kurun alış/satış fiyatını veriyor; her kurun günlük, haftalık, aylık ve uzun dönem geçmişi ile çevirici var; menüde "Merkez Bankası Verileri" bölümü var; veri sağlayıcı olarak Foreks anılıyor; hisse verisi 15 dk gecikmeli ([bigpara/doviz](https://bigpara.hurriyet.com.tr/doviz/), [bigpara/piyasalar](https://bigpara.hurriyet.com.tr/piyasalar/), 2026-10-20; sayfalar açılmadı). `hurriyet.com.tr/ekonomi` bölüm sayfası: ölçülmedi.

## 3. Haber detay
Ölçülmedi (otomatik erişim yok). Arama sonuçlarında galeri haberleri için `/galeri-<slug>-<id>` adres kalıbı görülüyor (2026-10-20, WebSearch).

## 4. Son dakika / canlı
Önceki gözlem: anasayfada "Bugün neler oldu?" şeridi + "SICAK GÜNDEM" kartları (URUN-PLANI §44; **doğrulanmadı**). Canlı blog / "canlı anlatım" sayfası arama sonuçlarında bulunamadı (2026-10-20). Ölçülmedi (otomatik erişim yok).

## 5. Yerel ve servis içerikleri
Ölçülmedi (otomatik erişim yok). Servis: Bigpara (döviz, altın, borsa) yukarıda.

## 6. Mobil davranış
Ölçülmedi (otomatik erişim yok).

## 7. Başarım
Ölçülmedi. PageSpeed Insights anahtarsız kota dolu (429, 2026-10-20). Bir sonraki taramada PSI/CrUX ile alınmalı.

## 8. SEO yapısı
Ölçülmedi (otomatik erişim yok). robots.txt'de `Sitemap:` satırı yok ([robots](https://www.hurriyet.com.tr/robots.txt), 2026-10-20). `/arama/`, `/widgets/`, `/api/` bota kapalı.

## 9. Reklam
Ölçülmedi (otomatik erişim yok). robots.txt'de `AmazonAdBot`'a `Allow: /` var: reklam doğrulama botuna açık ([robots](https://www.hurriyet.com.tr/robots.txt), 2026-10-20). Tarihsel: 2013 yeniden tasarımında rahatsız edici reklamların azaltıldığı bildirilmiş ([Webrazzi, 2013-11-12](https://webrazzi.com/2013/11/12/hurriyet-com-tr-yeni-tasarim/); güncel değil).

## 10. Gelir ve okur ilişkisi
Bigpara'da üye girişli "canlı borsa" sayfaları gecikmesiz veri sunuyor (arama sonucu özeti, [bigpara/doviz](https://bigpara.hurriyet.com.tr/doviz/), 2026-10-20). Ödeme duvarı, bülten, bildirim, yorum: ölçülmedi.

## 11. Erişilebilirlik
Ölçülmedi (otomatik erişim yok).

## 12. Yapay zekâ kullanımı
Ölçülmedi (otomatik erişim yok). Yapay zekâ ajanlarına karşı tutum robots.txt'de açık: 10 bot adı tümden kapalı ([robots](https://www.hurriyet.com.tr/robots.txt), 2026-10-20).

## Tarihsel bağlam (ikincil)
- 2011 ve 2013'te yeniden tasarım. 2013'te yassı tasarım, okunurluk ve 6 ayı aşkın ürün/yazılım ekibi çalışması bildirilmiş ([Webrazzi 2011](https://webrazzi.com/2011/03/30/hurriyet-com-tr-yenilendi/), [Webrazzi 2013](https://webrazzi.com/2013/11/12/hurriyet-com-tr-yeni-tasarim/)). Güncel tasarımı temsil etmez.

## Ölçüm dökümü
| ölçü | değer | yöntem |
|---|---|---|
| robots.txt `*` | kısmi `Disallow` (10 yol) | `curl`, 2026-10-20 |
| robots.txt `ClaudeBot` / `anthropic-ai` / `Claude-Web` | `Disallow: /` | aynı |
| bigpara robots.txt | aynı liste | aynı |
| PSI | 429 kota | googleapis, 2026-10-20 |
| diğer tüm ölçüler | ölçülmedi (otomatik erişim yok) | — |
