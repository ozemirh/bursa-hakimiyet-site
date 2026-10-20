# Financial Times

> **İkincil kaynak — otomatik erişim yok.** ft.com ve FT'ye ait diğer alan
> adlarına (FT Strategies dahil) hiçbir istek atılmadı. Kaynaklar: üçüncü taraf
> yayınlar ve FT'nin **GitHub'daki** herkese açık deposu (github.com).
> "Arama özeti" işaretliler açılmadı, doğrulanmadı sayılır.

- Adres: https://www.ft.com
- Katman: global (iş/ekonomi)
- Neden seçildi: veri gösterimi, ekonomi sayfası (özel tasarım adayı: ekonomi), başarım kültürü
- İnceleme: 2026-10-20 · koşul: üçüncü taraf kaynaklar · konum: Türkiye
- İncelenen sayfalar: yok

## Özet — en öğretici 3 çözüm
1. **Hızın okumaya etkisini kendi abonesinde A/B ile ölçmek.** 2016 deneyi: abonelerin bir kısmına her sayfaya bloklayan bir CSS çağrısıyla yapay gecikme eklendi; 28 gün sonunda okunan haber sayısı 1 sn gecikmede %4,6, 3 sn'de %7,9 düştü; etki zamanla büyüdü; çok sadık okur ve mobil kullanıcı kısa gecikmeye daha toleranslı ([MediaShift yeniden yayını](https://mediashift.org/2016/04/a-faster-ft-com-how-slow-websites-damage-publishers-revenue/), 2016-04-26, asıl yazı 2016-04-04; erişim 2026-10-20). — BH'ye: **evet** (yöntem olarak); BH'nin başarım bütçesine gerekçe. Kendi trafiğimizde böyle bir A/B testi yapmak ayrı karar ister. → `seo-buyume-uzmani` / `test-kalite-muhendisi`.
2. **Grafiği "veri ilişkisi"nden seçmek (Visual Vocabulary).** FT görsel gazetecilik ekibinin poster/rehberi grafik türünü 9 ilişki sınıfına göre seçtiriyor: sapma, korelasyon, sıralama, dağılım, zaman içinde değişim, parça-bütün, büyüklük, mekânsal, akış ([Financial-Times/chart-doctor README](https://github.com/Financial-Times/chart-doctor/blob/main/visual-vocabulary/README.md), erişim 2026-10-20). Lisans: tüm hakları saklı — poster/şablon **alınmaz**, yalnız yöntem. — **evet**; ekonomi özel tasarımı ve "her grafik kendini anlatsın" kararıyla (bellek: klasik görsel dil) örtüşüyor. → `web-tasarim-direktoru`.
3. **Arşivden kaynak gösteren YZ cevabı ("Ask FT").** Mart 2024: kurumsal abonelere, FT arşivinden cevap üreten sohbet aracı; cevapta hangi FT haberlerinden geldiğini gösteren **dipnotlar** ve kullanılan haberlerin **yayın tarih aralığı** ([Voicebot.ai](https://voicebot.ai/2024/03/25/financial-times-launches-generative-ai-chatbot-for-subscribers-powered-by-anthropics-claude-3-llm/), 2024-03-25; erişim 2026-10-20). — **hayır** (şimdilik); arşiv BH'de var (1 milyondan fazla haber) ama ürün okur tarafında YZ etiketi gerektirir; **BH için okura YZ etiketi reddedildi**. Kayıt için.

## 1. Anasayfa bilgi mimarisi
Ölçülmedi (otomatik erişim yok).

## 2. Bölüm sayfası
Ölçülmedi (otomatik erişim yok). Ekonomi/piyasa veri sayfalarının düzeni ikincil kaynakta bulunamadı.

## 3. Haber detay
Ölçülmedi (otomatik erişim yok).

## 4. Son dakika / canlı
Ölçülmedi (otomatik erişim yok).

## 5. Yerel ve servis içerikleri
Ölçülmedi. Ekonomi servisi (piyasa verisi) sayfaları doğrulanmadı.

## 6. Mobil davranış
- Sayfa ölçülmedi.
- FT tasarım sisteminin (Origami) başlık bileşeninde birincil gezinme 740 px altında çekmeceye dönüşüyor ve giriş bağlantısı sağda, sabit metinle ([npm o-header-services belgesi](https://www.npmjs.org/package/@financial-times/o-header-services), arama özeti). Hizmet sitelerine yönelik bileşen; ft.com'daki davranış doğrulanmadı.

## 7. Başarım
- Doğrudan ölçülmedi (otomatik erişim yok; PSI HTTP 429).
- Hız kültürü: bkz. Özet 1. Sonraki yeniden tasarımda hedef sayfaların 1 sn altında yüklenmesiydi; eski sitede tam yükleme 14 sn'ye çıkabiliyordu ([Digiday](https://digiday.com/media/financial-times-page-speed-vroom/), arama özeti).

## 8. SEO yapısı
Ölçülmedi (otomatik erişim yok).

## 9. Reklam
Ölçülmedi (otomatik erişim yok).

## 10. Gelir ve okur ilişkisi
- **Hediye haber:** aboneler abone olmayanlara e-postayla ayda 10 haber gönderebiliyor (başlangıçta beta) ([InPublishing](https://www.inpublishing.co.uk/articles/ft-introduces-gift-article-for-subscribers-7577), arama özeti); bir ortak program sayfası Standard planda 10, Premium'da 20 hediye haber listeliyor (arama özeti).
- **FT Edit** (Mart 2022): sosyal medyada FT'yi izleyen ama abone olmayanlara düşük fiyatlı, seçilmiş haber uygulaması (arama özeti — [Twipe](https://www.twipemobile.com/the-financial-times-launches-ft-edit-a-new-digital-edition/)).
- Ödeme duvarı tipi: ölçülmedi.

## 11. Erişilebilirlik
Ölçülmedi (otomatik erişim yok).

## 12. Yapay zekâ kullanımı
- Ask FT: bkz. Özet 3. Sonradan tüm kurumsal abonelere açıldığı ve uygulamada "gelişen haberler için özet yoldaşı" olarak düşünüldüğü FT'nin danışmanlık sitesindeki yazıda geçiyor (arama özeti; FT'ye ait alan adı, açılmadı).
- **BH için: okura "yapay zekâ destekli" etiketi reddedildi.**

## Ölçüm dökümü
| ölçü | değer | yöntem |
|---|---|---|
| Gecikme deneyi | 1 sn: −%4,9 (7 gün) / −%4,6 (28 gün); 2 sn: −%5,0 (28 gün); 3 sn: −%7,2 / −%7,9 | FT'nin 2016 A/B deneyi (MediaShift yeniden yayını) |
| diğer | ölçülmedi | otomatik erişim yok |

İstek sayısı (ft.com): **0**. (github.com'a WebFetch: 1.)
