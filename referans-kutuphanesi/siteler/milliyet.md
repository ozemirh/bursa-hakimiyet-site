# Milliyet

> **İkincil kaynak — otomatik erişim yok.** Siteye robots.txt dışında hiçbir istek atılmadı.

- Adres: https://www.milliyet.com.tr (piyasa verisi: https://uzmanpara.milliyet.com.tr)
- Katman: ulusal
- Neden seçildi: Bölüm sayfası kalıbı (URUN-PLANI §46 kaynağı).
- İnceleme: 2026-10-20 · koşul: sayfa açılmadı · konum: Türkiye
- **Erişim kararı (2026-10-20):** `User-agent: *` yalnız `/root/*`, `/arama/`, `/Milliyet.aspx` yollarını kapatıyor. `ClaudeBot`, `Claude-Web`, `anthropic-ai` için `Disallow: /` (ayrıca `GPTBot`, `ChatGPT-User`, `OAI-SearchBot`, `PerplexityBot` …). `Claude-User` bölümü yok. "En kısıtlayıcısı geçerli" → **yasak** ([robots](https://www.milliyet.com.tr/robots.txt), 2026-10-20). Bot listesi Hürriyet'inkiyle aynı. `uzmanpara` alt alan adının robots.txt'i okunmadı; ona istek atılmadı.
- İstek: 1 (robots.txt).
- Başarım: PageSpeed Insights anahtarsız kota dolu (HTTP 429, 2026-10-20) → ölçülmedi.

## Özet — en öğretici 3 çözüm
1. **Son dakika: nav altında tam genişlikte tek satır şerit, kırmızı `#ETİKET` önekli başlıklar** (URUN-PLANI §44, 2 Eylül 2026; **bu taramada doğrulanmadı**). Neden işe yarayabilir: tek satır dikkat çekiyor, ilk ekranı yemiyor. BH'ye: kısmen; BH §44 zaten şerit kalıbını kurdu.
2. **Bölüm sayfası: manşet + sağ ray, sonra gri bantta 4'lü küçük kart şeridi** (URUN-PLANI §46, 2 Eylül 2026, `/gundem`; **doğrulanmadı**).
3. **Piyasa verisi ayrı markada (Uzmanpara).** Arama sonucu özetine göre menüde Canlı Borsa, Günün Özeti, Hisse Fiyatları; döviz (dolar, euro, sterlin …) ve altın (gram, çeyrek, ons) sayfaları; değerli metaller ayrı. Bu menü Milliyet haber sayfalarında da tekrarlanıyor (WebSearch, 2026-10-20; sayfalar açılmadı). Hürriyet–Bigpara ile aynı kalıp.

## 1. Anasayfa bilgi mimarisi
Önceki gözlem: nav altında tam genişlik tek satır son dakika şeridi (URUN-PLANI §44; **doğrulanmadı**). Gerisi ölçülmedi (otomatik erişim yok).

## 2. Bölüm sayfası
Önceki gözlem (`/gundem`): manşet + sağ ray → gri bantta 4'lü küçük kart şeridi (URUN-PLANI §46; **doğrulanmadı**). Ekonomi: piyasa verisi Uzmanpara'da (yukarıda). `milliyet.com.tr/ekonomi`: ölçülmedi.

## 3. Haber detay
Ölçülmedi (otomatik erişim yok).

## 4. Son dakika / canlı
Önceki gözlem: kırmızı `#ETİKET` önekli tek satır şerit (§44; **doğrulanmadı**). Canlı blog: ölçülmedi.

## 5. Yerel ve servis içerikleri
Ölçülmedi (otomatik erişim yok). Servis: Uzmanpara (yukarıda).

## 6. Mobil davranış
Ölçülmedi (otomatik erişim yok).

## 7. Başarım
Ölçülmedi (PSI kota 429, 2026-10-20).

## 8. SEO yapısı
Ölçülmedi (otomatik erişim yok). robots.txt'de `Sitemap:` satırı yok ([robots](https://www.milliyet.com.tr/robots.txt), 2026-10-20).

## 9. Reklam
Ölçülmedi (otomatik erişim yok). robots.txt'de `AmazonAdBot`'a `Allow: /` var ([robots](https://www.milliyet.com.tr/robots.txt), 2026-10-20).

## 10. Gelir ve okur ilişkisi
Ölçülmedi (otomatik erişim yok).

## 11. Erişilebilirlik
Ölçülmedi (otomatik erişim yok).

## 12. Yapay zekâ kullanımı
Ölçülmedi (otomatik erişim yok). Yapay zekâ ajanlarına tutum: 10 bot adı tümden kapalı.

## Bağlam (ikincil)
- Milliyet, Hürriyet ve Uzmanpara aynı grubun dijital varlıkları arasında listeleniyor ([MOM-RSF, milliyet.com.tr](https://turkey.mom-rsf.org/en/media/detail/outlet/milliyetcomtr/) ve [grup sayfası](https://turkey.mom-rsf.org/en/owners/companies/detail/company/821/), 2026-10-20; WebSearch özeti, sayfalar açılmadı, tarihi belirsiz). Ortak bot listesi bununla tutarlı; ortak platform olup olmadığı **doğrulanmadı**.

## Ölçüm dökümü
| ölçü | değer | yöntem |
|---|---|---|
| robots.txt `*` | 3 `Disallow` | `curl`, 2026-10-20 |
| robots.txt `ClaudeBot` / `Claude-Web` / `anthropic-ai` | `Disallow: /` | aynı |
| PSI | 429 kota | googleapis, 2026-10-20 |
| diğer tüm ölçüler | ölçülmedi (otomatik erişim yok) | — |
