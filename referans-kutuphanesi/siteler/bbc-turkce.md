# BBC Türkçe (BBC News Türkçe)

> **İkincil kaynak — otomatik erişim yok.** bbc.com'a hiçbir istek atılmadı (SITELER.md "Erişim durumu", 20 Ekim 2026 kullanıcı kararı).

- Adres: https://www.bbc.com/turkce
- Katman: ulusal (kamu yayıncısının dil servisi)
- Neden seçildi: Kamu yayıncısı disiplini, reklamsız okuma.
- İnceleme: 2026-10-20 · koşul: sayfa açılmadı · konum: Türkiye
- İstek: 0 (bbc.com). Kullanılan kaynaklar: BBC'nin açık kaynak deposu (GitHub, WebFetch), arama sonuçları (WebSearch).
- Başarım: PageSpeed Insights anahtarsız kota dolu (HTTP 429, 2026-10-20) → ölçülmedi.

## Özet — en öğretici 3 çözüm
1. **Dil servisleri tek açık kaynak platformda.** BBC'nin `simorgh` deposu, World Service haber sitelerini React/Next.js ile üreten uygulama. README 41 dil desteği yazıyor. Erişilebilirlik ve başarım hedef olarak anılıyor. Lighthouse testleri iç CD sürecinde, uçtan uca testler Cypress ile ([github.com/bbc/simorgh](https://github.com/bbc/simorgh), 2026-10-20). Türkçe servis README'de **adıyla geçmiyor**; BBC Türkçe'nin bu platformda çalıştığı **doğrulanmadı**. Neden işe yarar: 40+ küçük masa tek bileşen kütüphanesini paylaşıyor. BH'ye: **hayır** (React/Next yığını BH'de reddedildi, kullanıcı kararı). Ders yalnız "küçük masa, ortak şablon".
2. **Makale ve anasayfa farklı ele alınıyor.** README'ye göre makale adresi `/<servis>/articles/:id`, AMP sürümü aynı adres + `.amp`; servis anasayfalarında AMP yok ([simorgh README](https://github.com/bbc/simorgh), 2026-10-20). BBC Türkçe için doğrulanmadı.
3. **".lite" hafif sayfa.** Doğrulanmamış bir ikinci el gönderiye göre World Service, makalelerin JS'siz HTML+CSS "lite" sürümünü denemiş: adrese `.lite` ekleniyor, aktarım ~600 KB'tan ~30 KB'a iniyor. Örnek İspanyolca servis; Türkçe anılmıyor; gönderi sonradan silinmiş ([lemmy.johnnei.org](https://lemmy.johnnei.org/post/147716/507707), 2026-10-20). Resmî BBC kaynağı bulunamadı. Neden ilginç: sunucu render + JS'siz okuma, BH'nin Django/sunucu render mimarisine yakın bir hedef. BH için yalnız bir fikir; ölçü değil.

## 1. Anasayfa bilgi mimarisi
Ölçülmedi (otomatik erişim yok).
## 2. Bölüm sayfası
Ölçülmedi (otomatik erişim yok). Simorgh README konu (topic) sayfası türü tarif ediyor, verisi iç API'den geliyor; BBC Türkçe için doğrulanmadı.
## 3. Haber detay
Ölçülmedi (otomatik erişim yok). Platform düzeyi: makale + AMP makale (yukarıda).
## 4. Son dakika / canlı
Ölçülmedi (otomatik erişim yok). Tarihsel basın haberleri BBC Türkçe'nin olaylar için canlı metin/blog sayfası işlettiğini gösteriyor (ör. 2017 ve 2021 olaylarına ilişkin aktarımlar, WebSearch özeti, 2026-10-20); güncel biçim doğrulanmadı.
## 5. Yerel ve servis içerikleri
Ölçülmedi (otomatik erişim yok).
## 6. Mobil davranış
Ölçülmedi (otomatik erişim yok).
## 7. Başarım
Ölçülmedi (PSI kota 429). Platform düzeyinde README sayısal başarım bütçesi yazmıyor; her derlemede paket boyutu raporu üretiliyor ([simorgh](https://github.com/bbc/simorgh), 2026-10-20).
## 8. SEO yapısı
Ölçülmedi (otomatik erişim yok). Platformda AMP makale sürümü var (yukarıda).
## 9. Reklam
Ölçülmedi (otomatik erişim yok). "Reklamsız okuma" seçilme gerekçesi bu taramada **doğrulanmadı**; dil servislerinde reklam politikasına dair kaynak bulunamadı (WebSearch, 2026-10-20).
## 10. Gelir ve okur ilişkisi
Ölçülmedi (otomatik erişim yok). Bağlam: World Service 43 dil servisi işletiyor, 18'i yalnız dijital (İngiltere Sayıştayı NAO özeti, Kasım 2025, [nao.org.uk](https://www.nao.org.uk/wp-content/uploads/2025/11/bbc-world-service-saving-programmes-summary.pdf), WebSearch özeti, belge açılmadı).
## 11. Erişilebilirlik
Ölçülmedi (otomatik erişim yok). Platform düzeyi: cihazlar arası erişilebilirlik test kılavuzu ve Storybook üzerinde tarayıcılar arası görsel test (Chromatic) ([simorgh](https://github.com/bbc/simorgh), 2026-10-20).
## 12. Yapay zekâ kullanımı
Ölçülmedi (otomatik erişim yok).

## Ölçüm dökümü
| ölçü | değer | yöntem |
|---|---|---|
| bbc.com istekleri | 0 | kural: otomatik erişim yok |
| Simorgh desteklenen dil | 41 | GitHub README, WebFetch, 2026-10-20 |
| PSI | 429 kota | googleapis, 2026-10-20 |
| diğer tüm ölçüler | ölçülmedi (otomatik erişim yok) | — |
