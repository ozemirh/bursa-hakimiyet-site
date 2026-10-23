# BBC News

> **İkincil kaynak — otomatik erişim yok.** bbc.com / bbc.co.uk ve BBC'ye ait
> diğer alan adlarına (BBC Studios basın sitesi dahil) hiçbir istek atılmadı.
> Kaynaklar: üçüncü taraf yayınlar ve BBC'nin **GitHub'daki** açık kaynak deposu
> (github.com). "Arama özeti" işaretliler açılmadı, doğrulanmadı sayılır.
> Not: BBC Türkçe aynı kural kapsamında (SITELER.md).

- Adres: https://www.bbc.com/news
- Katman: global (kamu yayıncısı; uluslararası sürüm reklamlı)
- Neden seçildi: kademeli bölüm sayfası, göreli zaman (§44, §46), yerel demokrasi muhabirliği
- İnceleme: 2026-10-20 · koşul: üçüncü taraf kaynaklar · konum: Türkiye
- İncelenen sayfalar: yok

## Özet — en öğretici 3 çözüm
1. **Seçili haberlerin başında "bir bakışta" madde özeti, insan onaylı.** Haziran 2025 pilotu: tek bir onaylı istem (prompt) ile kısa, taranabilir madde özeti üretiliyor, her çıktıyı gazeteci düzenliyor/onaylıyor; gerekçe kısa özetlerin özellikle genç okurda sevilmesi; YZ kullanımının okura açıklanacağı belirtiliyor ([NewscastStudio](https://www.newscaststudio.com/2025/06/27/bbc-begins-public-trials-of-two-generative-ai-news-production-tools), 2025-06-27, arama özeti — sayfa 403). — BH'ye: **kısmen**; "üç madde" alanı BH taslağında zaten var (kural motoru boş bırakır, editör yazar). **Okura YZ etiketi BH için reddedildi (kullanıcı kararı)** — yalnız madde bloğu deseni alınır.
2. **Yerel demokrasi haberlerini biçime sokan "Style Assist".** BH'nin işine en yakın örnek: BBC'nin finanse ettiği Yerel Demokrasi Muhabirliği (LDRS) metinleri BBC'nin eğittiği dil modeliyle BBC biçimine çevriliyor, kıdemli gazeteci doğruluk/açıklık için gözden geçiriyor (aynı kaynak, arama özeti). — **kısmen**; BH'de kaynak metinden cümle kopyalanmaz kuralı var; "biçime sokma" değil "taslağa ham malzeme" olarak kalmalı (CLAUDE.md, kural motoru).
3. **Hafif ("lite") sayfa ve çok dilli açık kaynak render.** World Service siteleri (41 dil) BBC'nin açık kaynak uygulaması Simorgh ile; makaleler için AMP sürümü (`.amp`) var ([bbc/simorgh README](https://github.com/bbc/simorgh), erişim 2026-10-20). Bir BBC geliştiricisinin forum notuna göre `.lite` sayfaları istemci hidrasyonunu atlıyor, örnekte ~1,65 MB → ~135 KB (Lemmy forum gönderisi — adres kişisel alan adı içeriyor, URL gizlendi; arama özeti, ~2020). — **kısmen**; BH zaten sunucu render ve JS'siz okunabilir; "düşük veri sürümü" fikri başarım bütçesi tartışmasına girdi olur. → `web-tasarim-direktoru`.

## 1. Anasayfa bilgi mimarisi
- Ölçülmedi (otomatik erişim yok).
- Yeniden tasarlanan BBC.com Aralık 2023'te Kuzey Amerika'da, Mart 2024'te küresel olarak açıldı; uluslararası BBC News uygulamasının yerini yeni BBC uygulaması aldı; gerekçe reklam teknolojisi ve "daha premium ticari teklif" ([DigitalTVEurope](https://digitaltveurope.com/2024/03/22/bbc-studios-and-bbc-news-launch-new-app-and-site-globally), 2024-03-22, arama özeti).

## 2. Bölüm sayfası
Ölçülmedi (otomatik erişim yok). SITELER.md'deki "kademeli bölüm sayfası" iddiası doğrulanmadı.

## 3. Haber detay
Ölçülmedi (otomatik erişim yok).

## 4. Son dakika / canlı
- 2011'de Guardian'ın blog editörü, BBC canlı sayfasının üstünde **son gelişmelerin kalıcı özeti** bulunmasını örnek gösteriyordu ([Press Gazette](https://pressgazette.co.uk/news/guardiancouk-looks-to-improve-live-news-format), 2011, arama özeti). Güncel biçim doğrulanmadı.
- Göreli zaman (§44): doğrulanmadı.

## 5. Yerel ve servis içerikleri
- Yerel Demokrasi Muhabirliği (LDRS) metinleri BBC sistemine giriyor ve Style Assist pilotunda biçime sokuluyor (bkz. Özet 2).
- İlçe/il sayfası, hava, trafik: ölçülmedi. 2000'lerin sonundaki yeniden tasarımda anasayfaya kişiselleştirilmiş yerel haber ve hava eklenmişti ([journalism.co.uk](https://www.journalism.co.uk/bbc-launches-redesigned-news-website/), arama özeti, tarih belirsiz).

## 6. Mobil davranış
Ölçülmedi (otomatik erişim yok).

## 7. Başarım
- Doğrudan ölçülmedi.
- CrUX saha verisine dayalı üçüncü taraf sıralamada (en büyük 50 İngilizce haber sitesi, 2025 4. çeyrek) bbc.com **10.**, puan 83 (göreli, 0–100) ([Site Speed Awards](https://sitespeedawards.catchmetrics.io/), erişim 2026-10-20).

## 8. SEO yapısı
- Doğrudan ölçülmedi.
- Simorgh README: World Service ve Public Service News makaleleri için AMP sayfaları (`.amp` soneki); World Service anasayfalarında AMP yok ([bbc/simorgh](https://github.com/bbc/simorgh), erişim 2026-10-20).

## 9. Reklam
- Uluslararası sürüm reklamla finanse ediliyor (bkz. §1). Yerleşim ölçülmedi.

## 10. Gelir ve okur ilişkisi
- **ABD'de dinamik ödeme duvarı** (26 Haziran 2025): sabit ücretsiz haber sayısı yok; okuma miktarı ve süresine göre "etkileşim temelli" model; aylık 8,99 $ / yıllık 49,99 $; ücretsiz kalanlar: seçili küresel son dakika haberleri, radyo canlı yayınları, **World Service dil siteleri** (BBC Türkçe dahil), bazı bülten ve podcast'ler; BBC.com'un 139 milyon küresel ziyaretçisinin ~60 milyonu ABD'de ([Press Gazette](https://pressgazette.co.uk/paywalls/bbc-com-launches-dynamic-paywall-for-us-users/), 2025-06-26; erişim 2026-10-20).
- Türkiye'den görünüm: ölçülmedi.

## 11. Erişilebilirlik
- Doğrudan ölçülmedi.
- Simorgh README hızlı ve erişilebilir deneyimi, geniş cihaz yelpazesini ilke olarak koyuyor ([bbc/simorgh](https://github.com/bbc/simorgh)). Uygulama ölçülmedi.

## 12. Yapay zekâ kullanımı
- "Bir bakışta" özet ve Style Assist pilotları (bkz. Özet 1–2). Okura açıklama yapılacağı söyleniyor; biçimi doğrulanmadı.
- **BH için: okura "yapay zekâ destekli" etiketi reddedildi.**

## Teknik not
Simorgh yığını: React, Next.js, TypeScript, Express, Emotion ([README](https://github.com/bbc/simorgh)). **BH için: React/bundler reddedildi** — yalnız kayıt.

## Ölçüm dökümü
| ölçü | değer | yöntem |
|---|---|---|
| CrUX göreli puan | 83 (10./50) | üçüncü taraf, 2025 Ç4 |
| lite sayfa boyutu | ~1,65 MB → ~135 KB | geliştirici forum notu, arama özeti, doğrulanmadı |
| diğer | ölçülmedi | otomatik erişim yok |

İstek sayısı (bbc.com / bbc.co.uk): **0**. (github.com'a WebFetch: 1.)
