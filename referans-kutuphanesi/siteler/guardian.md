# The Guardian

> **İkincil kaynak — otomatik erişim yok.** theguardian.com'a hiçbir istek
> atılmadı (robots.txt dahil). Kaynaklar: üçüncü taraf yayınlar ve Guardian'ın
> **GitHub'daki** açık kaynak deposu (github.com — Guardian alan adı değil).
> "Arama özeti" işaretliler açılmadı, doğrulanmadı sayılır.

- Adres: https://www.theguardian.com
- Katman: global
- Neden seçildi: açık erişim + okur desteği; bölüm sayfası (§46)
- İnceleme: 2026-10-20 · koşul: üçüncü taraf kaynaklar · konum: Türkiye
- İncelenen sayfalar: yok

## Özet — en öğretici 3 çözüm
1. **Duvar yok, haber sonunda destek çağrısı ("epic").** Okurdan katkı istemeye 2016'da başladı; haber sonu çağrıları ana araçlardan biri. Mart 2026'da biten mali yılda dijital okur geliri ~125–126 milyon £, düzenli destekçi 1,4 milyon (Press Gazette, 2026 — adres kişi adı içeriyor, URL gizlendi; arama özeti). — BH'ye: **kısmen**; haber sonu çağrısı ucuz bir bileşen, ama Guardian'ın vakıf yapısı ve uluslararası kitlesi yok; yerel ticari gazetede karşılığı bülten kaydı ya da abonelik çağrısı olur.
2. **Canlı blog trafiğin ana taşıyıcısı ve özet yerine başlık gezinmesi.** Ortalama bir günde toplam sayfa görüntülemenin %15'e kadarı canlı bloglardan; üstte yazılı özet yok, okur tek tek gönderilerin başlıkları arasında gezinme aracıyla dolaşıyor; kurum içi araç çok yazarlı, sosyal medya/fotoğraf içe aktarabiliyor (Press Gazette, 2026-08-05 — adres kişi adı içeriyor, URL gizlendi; erişim 2026-10-20). Aynı kaynak: küçük yayıncı da tek gönüllü muhabirle canlı blog yürütebilir. — **evet**; "gönderi başlıkları gezinmesi" BH canlı sayfasına küçük emekle taşınır.
3. **Görsel regresyon testi + JSON modelden render.** Sayfa üretimi ayrı bir render servisinde: arka uç JSON veri modeli gönderiyor, render servisi sunucuda HTML üretiyor; bileşenler Storybook + Chromatic görsel regresyon testinden, Playwright tarayıcı testinden geçiyor ([guardian/dotcom-rendering README](https://github.com/guardian/dotcom-rendering/blob/main/dotcom-rendering/README.md), erişim 2026-10-20). — **kısmen**: test disiplini taşınır (BH zaten başsız Chrome ile ölçüyor); **yığın (Preact/React, Emotion, Webpack) BH için reddedildi** (Tailwind/React/bundler — değişmez karar).

## 1. Anasayfa bilgi mimarisi
- Sayfa ölçülmedi (otomatik erişim yok).
- 2014 yeniden tasarımında sütunlar yerine yapılandırılabilir **yatay bant kapsayıcılar** geldi ([journalism.co.uk](https://www.journalism.co.uk/key-principles-behind-the-new-guardian-website/), arama özeti). Güncel düzen doğrulanmadı.

## 2. Bölüm sayfası
Ölçülmedi (otomatik erişim yok). 2014'teki bant kapsayıcı düzeninin bölüm sayfalarında da kullanıldığı varsayılmadı — doğrulanmadı.

## 3. Haber detay
- Sayfa ölçülmedi.
- Render servisi makale uç noktası üzerinden çalışıyor; tasarım/görüntü tipine göre dallanan desen dokümante edilmiş ("switch on display design", "decide layout") ([README](https://github.com/guardian/dotcom-rendering/blob/main/dotcom-rendering/README.md)). Yani haber tipi (haber, görüş, analiz, canlı) farklı bir yerleşim seçiyor.

## 4. Son dakika / canlı
- Bkz. Özet 2. Bu yıl canlı bloglar yarım milyar sayfa görüntülemesi ve 14 milyon saat okuma süresi getirdi (Press Gazette, 2026-08-05).
- Uygun konular: sürekli değişen siyaset/spor; rutin, yeni bilgi getirmeyen olaylar uygun değil (aynı kaynak).

## 5. Yerel ve servis içerikleri
Ölçülmedi. Yerel katman bu sitenin odağı değil.

## 6. Mobil davranış
Ölçülmedi (otomatik erişim yok).

## 7. Başarım
- Doğrudan ölçülmedi.
- CrUX saha verisine dayalı üçüncü taraf sıralamada (en büyük 50 İngilizce haber sitesi, 2025 4. çeyrek, LCP/INP/CLS'nin 0–100 normalize ortalaması) theguardian.com **1.**, puan 92 ([Site Speed Awards](https://sitespeedawards.catchmetrics.io/), erişim 2026-10-20). Puan görelidir; mutlak LCP değeri yayımlanmamış.

## 8. SEO yapısı
Ölçülmedi (otomatik erişim yok).

## 9. Reklam
- Mart 2025'ten beri **"consent or pay"**: kişiselleştirilmiş reklamı reddeden okura aylık 5 £'lık "Ad-Lite" katmanı (reklam var ama kişiselleştirilmemiş); 2023'te kullanıcıların %30'u "hepsini reddet" diyordu ([Press Gazette](https://pressgazette.co.uk/marketing/cookies-consent-or-pay-guardian-gb-news-newsquest-city-am/), 2025-03-14; erişim 2026-10-20).
- Yerleşim/yuva sayısı: ölçülmedi.

## 10. Gelir ve okur ilişkisi
- Okur desteği: bkz. Özet 1. ABD'de 500 binden fazla düzenli destekçi (arama özeti).
- Ödeme duvarı yok (haberler açık); Ad-Lite yalnız reklam tercihi için.

## 11. Erişilebilirlik
Ölçülmedi (otomatik erişim yok). README'de erişilebilirlik ilkesi anılmıyor.

## 12. Yapay zekâ kullanımı
Ölçülmedi. Üçüncü taraf karşılaştırmada Guardian'ın YZ ilkeleri anılıyor ([Nieman Lab](https://www.niemanlab.org/?p=216334), arama özeti) — içerik doğrulanmadı. **BH için: okura "yapay zekâ destekli" etiketi reddedildi.**

## Ölçüm dökümü
| ölçü | değer | yöntem |
|---|---|---|
| CrUX göreli puan | 92 (1./50) | üçüncü taraf, 2025 Ç4, kaynak sitede |
| diğer | ölçülmedi | otomatik erişim yok; PSI HTTP 429 |

İstek sayısı (theguardian.com): **0**. (github.com'a WebFetch: 2.)
