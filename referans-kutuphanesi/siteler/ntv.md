# NTV

> **İkincil kaynak — otomatik erişim yok.** Siteye robots.txt dışında hiçbir istek atılmadı.

- Adres: https://www.ntv.com.tr
- Katman: ulusal
- Neden seçildi: Sakin, hızlı, düzenli bilgi mimarisi.
- İnceleme: 2026-10-20 · koşul: sayfa açılmadı · konum: Türkiye
- **Erişim kararı (2026-10-20):** `User-agent: *` için `Allow: /` (birkaç yol hariç). Ama `ClaudeBot`, `Claude-Web`, `anthropic-ai` için `Disallow: /` (ayrıca `GPTBot`, `ChatGPT-User`, `OAI-SearchBot`, `PerplexityBot`, `cohere-ai` …). `Claude-User` bölümü yok. "En kısıtlayıcısı geçerli" → **yasak** ([robots](https://www.ntv.com.tr/robots.txt), 2026-10-20). SITELER.md'deki "açık" sınıflaması bu okumayla çelişiyor; okuma ajanları da (`Claude-Web`, `ChatGPT-User`) kapalı.
- İstek: 1 (robots.txt).
- Başarım: PageSpeed Insights anahtarsız kota dolu (HTTP 429, 2026-10-20) → ölçülmedi.

## Özet — en öğretici 3 çözüm
1. **Son dakikayı anasayfada panelle değil, üst şeritte bir bağlantıyla taşıyor.** Önceki gözlem (URUN-PLANI §44, 2 Eylül 2026; **bu taramada doğrulanmadı**). Neden işe yarayabilir: anasayfa sakin kalıyor, son dakika tek bir hedefe toplanıyor. BH'ye: kısmen; doğrulanmadan desene taşınmamalı.
2. **Haber sitemap'i ayrı ve robots.txt'de ilk sırada** (`/sitemaps/news-sitemap.xml`), genel sitemap dizini ayrı ([robots](https://www.ntv.com.tr/robots.txt), 2026-10-20).
3. **"Sonraki haber" uçları bota kapalı** (`/api/next-news`, `/getNextGalleryNews/`). Detayda bir sonraki haberi/galeri karesini yükleyen bir mekanizma olduğuna işaret ediyor; davranışın kendisi **doğrulanmadı** ([robots](https://www.ntv.com.tr/robots.txt), 2026-10-20). Habertürk'teki `/infinite/news/*` kapatmasıyla aynı mantık (bkz. `haberturk.md`).

## 1. Anasayfa bilgi mimarisi
Önceki gözlem: son dakika paneli yok, "Son Dakika" üst şeritte bağlantı (URUN-PLANI §44, 2 Eylül 2026; **doğrulanmadı**). Gerisi ölçülmedi (otomatik erişim yok).

## 2. Bölüm sayfası
Ölçülmedi (otomatik erişim yok).

## 3. Haber detay
Ölçülmedi (otomatik erişim yok). robots.txt'deki `/api/next-news` ucu, detayda sonraki haberin dinamik yüklendiğine işaret ediyor (doğrulanmadı).

## 4. Son dakika / canlı
Önceki gözlem yukarıda (§44). Canlı blog arandı, arama sonuçlarında bulunamadı (2026-10-20). Ölçülmedi.

## 5. Yerel ve servis içerikleri
Ölçülmedi (otomatik erişim yok).

## 6. Mobil davranış
Ölçülmedi (otomatik erişim yok).

## 7. Başarım
Ölçülmedi (PSI kota 429, 2026-10-20).

## 8. SEO yapısı
robots.txt: `Sitemap: /sitemaps/news-sitemap.xml` ve `/sitemaps`; `/ara/` (iç arama) bota kapalı ([robots](https://www.ntv.com.tr/robots.txt), 2026-10-20). JSON-LD, kanonik, AMP: ölçülmedi (otomatik erişim yok).

## 9. Reklam
Ölçülmedi (otomatik erişim yok).

## 10. Gelir ve okur ilişkisi
Ölçülmedi (otomatik erişim yok).

## 11. Erişilebilirlik
Ölçülmedi (otomatik erişim yok).

## 12. Yapay zekâ kullanımı
Ölçülmedi (otomatik erişim yok). Yapay zekâ ajanlarına tutum: 10 bot adı tümden kapalı ([robots](https://www.ntv.com.tr/robots.txt), 2026-10-20).

## Tarihsel bağlam (ikincil)
- 2014 Aralık: ntvmsnbc.com, NTV kimliğiyle ntv.com.tr'ye taşındı ve yeni tasarıma geçti ([Webrazzi, 2014-12-22](https://webrazzi.com/2014/12/22/ntvmsnbc-com-haber-sitesi-yenilenen-kimligiyle-artik-ntv-com-trde/)). Güncel tasarımı temsil etmez; sonraki bir yeniden tasarım haberi bulunamadı (WebSearch, 2026-10-20).

## Ölçüm dökümü
| ölçü | değer | yöntem |
|---|---|---|
| robots.txt `*` | `Allow: /` + 4 `Disallow` | `curl`, 2026-10-20 |
| robots.txt `ClaudeBot` / `Claude-Web` / `anthropic-ai` | `Disallow: /` | aynı |
| PSI | 429 kota | googleapis, 2026-10-20 |
| diğer tüm ölçüler | ölçülmedi (otomatik erişim yok) | — |
