# Olay

- Adres: https://www.olay.com.tr/
- Katman: yerel
- Neden seçildi: Bursa'nın doğrudan rakibi; aynı okur (SITELER.md).
- İnceleme: 2026-10-20 · **otomatik erişim yok — yalnız ikincil kaynak**
- İncelenen sayfalar: yalnız `robots.txt` (izin kontrolü için tek istek). Başka sayfaya WebFetch, `curl` ya da Chrome ile istek atılmadı.

## Erişim durumu (robots.txt, 2026-10-20)
- Başlık yorumu, siteye erişimi içerik sinyallerine uyma **koşuluna** bağlıyor ve bu sinyalleri AB 2019/790 Direktifi m.4 kapsamında açık hak saklaması olarak tanımlıyor ([robots.txt](https://www.olay.com.tr/robots.txt), 2026-10-20).
- `User-agent: *` → `Content-Signal: search=yes, ai-train=no, use=reference`, `Allow: /`.
- `ClaudeBot`, `anthropic-ai`, `Claude-Web` → **`Disallow: /`**. `Claude-User` için ayrı bölüm yok.
- README kuralı: `*` ve `Claude-User`/`ClaudeBot`/`anthropic-ai` bölümlerinin en kısıtlayıcısı geçerli → **otomatik erişim yok.** (SITELER.md "Erişim durumu"nda Olay "Açık" listesinde; bu bulguyla güncellenmesi gerekiyor → SITELER.md sahibi.)
- Başarım için PageSpeed Insights API anahtarsız denendi (2026-10-20): günlük kota 0, HTTP 429 — CrUX verisi alınamadı.

## Özet — en öğretici 3 çözüm
Ölçülmedi (otomatik erişim yok). Bu dosya, kullanıcının ya da ekipten birinin tarayıcıda elle gözlemiyle doldurulabilir (kim, ne zaman, hangi koşul yazılarak).

## 1. Anasayfa bilgi mimarisi
Ölçülmedi (otomatik erişim yok).
## 2. Bölüm sayfası
Ölçülmedi (otomatik erişim yok).
## 3. Haber detay
Ölçülmedi (otomatik erişim yok).
## 4. Son dakika / canlı
Ölçülmedi (otomatik erişim yok).
## 5. Yerel ve servis içerikleri
Ölçülmedi (otomatik erişim yok).
## 6. Mobil davranış
Ölçülmedi (otomatik erişim yok).
## 7. Başarım
Ölçülmedi (otomatik erişim yok; PageSpeed Insights anahtarsız kota 0).
## 8. SEO yapısı
robots.txt'te tek sitemap: `/sitemap_index.xml` (dosya açılmadı). `/wp-admin/` kapalı — WordPress altyapısına işaret ediyor, doğrulanmadı. Gerisi ölçülmedi.
## 9. Reklam
Ölçülmedi (otomatik erişim yok).
## 10. Gelir ve okur ilişkisi
- İkincil kaynak (arama motoru özeti, 2026-10-20): App Store'da "Olay E-Gazete" adlı bir uygulama; basılı yayınların dijital sürümü, 1987'den bu yana arşiv ve haftalıktan yıllığa abonelik paketleri anılıyor. **Doğrulanmadı** — uygulama sayfası (`apps.apple.com/…/id1440668513`) WebFetch'te 404 döndü.
- Gerisi ölçülmedi.
## 11. Erişilebilirlik
Ölçülmedi (otomatik erişim yok).
## 12. Yapay zekâ kullanımı
Ölçülmedi (otomatik erişim yok). robots.txt'teki içerik sinyalleri: yapay zekâ eğitimi `no`, kullanım `reference`.

## Ölçüm dökümü
| ölçü | değer | yöntem |
|---|---|---|
| robots.txt | 1.063 B, HTTP 200 | `curl --compressed`, varsayılan User-Agent, 2026-10-20 |
| istek sayısı (bu site) | 1 | yalnız robots.txt |
