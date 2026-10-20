# Sözcü

> **İkincil kaynak — erişim engelli.** robots.txt isteği Cloudflare doğrulama sayfasıyla (HTTP 403) karşılandı; engel aşılmaya çalışılmadı, başka istek atılmadı.

- Adres: https://www.sozcu.com.tr
- Katman: ulusal
- Neden seçildi: Son dakika şeridi, yoğun anasayfa (URUN-PLANI §44 kaynağı).
- İnceleme: 2026-10-20 · koşul: sayfa açılmadı · konum: Türkiye
- **Erişim (2026-10-20):** `curl` varsayılan UA ile `/robots.txt` → **403, "Just a moment…" Cloudflare doğrulaması** → "erişim engelli", atlandı.
- **robots.txt içeriği (önceki kopya):** 2026-10-19 18:00'de ekibin kaydettiği kopyada `User-agent: *` (+ `Mediapartners-Google`) için `Allow: /`; yapay zekâ ajanlarına özel bölüm yok; tek `Disallow` sosyal abonelik yolu. Başlık yorumu yapay zekâ için bir `llms.txt` dosyasını gösteriyor. `llms.txt` okunamadı, koşulları bilinmiyor. Yani kural izinli görünüyor ama bugün teknik engel var. Bugün yeniden doğrulanmadı.
- İstek: 1 (robots.txt, 403).
- Başarım: PageSpeed Insights anahtarsız kota dolu (HTTP 429, 2026-10-20) → ölçülmedi.

## Özet — en öğretici 3 çözüm
1. **Son dakika: koyu plaka + dolu kırmızı şeritte tek manşet** (URUN-PLANI §44, 2 Eylül 2026; **bu taramada doğrulanmadı**). BH §44'teki şerit manşetinin kaynağı. Neden işe yarayabilir: tek haber, tek satır, yüksek kontrast; son dakikanın değerini korur.
2. **Konuya özel sitemap.** Önceki robots kopyasında genel sitemap dizini, Google News sitemap'i ve bir **turnuvaya özel sitemap** ayrı ayrı listeleniyor; ayrıca abone/yayın akışı gibi görünen bir RSS ucu var (2026-10-19 kopyası; içerikleri **doğrulanmadı**). Neden: büyük olay sayfalarını tarayıcıya ayrı bildirmek.
3. **Reklamsız ücretli sürüm (tarihsel).** 2016'da "Reklamsız Sözcü" aboneliği web ve mobilde açıldı; abone olmayanlardan reklam engelleyiciyi kapatmaları istendi ([Webrazzi, 2016-04-06](https://webrazzi.com/2016/04/06/sozcu-gazetesi-reklam-engelleyicilere-karsi-reklamsiz-sozcuyu-devreye-aliyor/)). Güncel durumu **doğrulanmadı**: bir üçüncü taraf listesi "Sözcü Plus" adlı ücretli bir üründen söz ediyor, güvenilirliği düşük ([subger](https://subger.com/tr/service/sozcu-tr), 2026-10-20).

## 1. Anasayfa bilgi mimarisi
Önceki gözlem: son dakika koyu plaka + kırmızı şerit, tek manşet (URUN-PLANI §44; **doğrulanmadı**). Gerisi ölçülmedi (erişim engelli).

## 2. Bölüm sayfası
Ölçülmedi (erişim engelli).

## 3. Haber detay
Ölçülmedi (erişim engelli).

## 4. Son dakika / canlı
Önceki gözlem yukarıda. Canlı blog: ölçülmedi.

## 5. Yerel ve servis içerikleri
Ölçülmedi (erişim engelli).

## 6. Mobil davranış
Ölçülmedi (erişim engelli).

## 7. Başarım
Ölçülmedi (PSI kota 429; site erişim engelli).

## 8. SEO yapısı
Önceki robots kopyasına göre (2026-10-19): sitemap dizini, Google News sitemap'i, turnuva sitemap'i, RSS ucu. JSON-LD, kanonik, AMP: ölçülmedi.

## 9. Reklam
Ölçülmedi. robots kopyasında `Mediapartners-Google` adı geçiyor (Google reklam tarayıcısı).

## 10. Gelir ve okur ilişkisi
Tarihsel: reklamsız abonelik (2016, yukarıda). Güncel: doğrulanmadı.

## 11. Erişilebilirlik
Ölçülmedi (erişim engelli).

## 12. Yapay zekâ kullanımı
Ölçülmedi. Yapay zekâya tutum: robots.txt yasaklamıyor, `llms.txt` ile yönlendiriyor (2026-10-19 kopyası). Ulusal katmanda bu tutumu gösteren tek site.

## Ölçüm dökümü
| ölçü | değer | yöntem |
|---|---|---|
| `/robots.txt` 2026-10-20 | HTTP 403, Cloudflare doğrulama sayfası | `curl` varsayılan UA |
| robots.txt 2026-10-19 kopyası | `*`: `Allow: /`; `llms.txt` yorumu | ekip kaydı (scratchpad) |
| PSI | 429 kota | googleapis, 2026-10-20 |
| diğer tüm ölçüler | ölçülmedi (erişim engelli) | — |
