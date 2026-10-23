# Axios Local

> **İkincil kaynak — erişim engelli.** robots.txt açık (YZ tarayıcısına özel
> kural yok), ancak `curl` (varsayılan UA, Türkiye) ile `/local` ve
> `/legal/terms` istekleri **HTTP 403 Cloudflare sınaması** ("Just a moment…")
> döndü (2026-10-20). Kural gereği aşılmaya çalışılmadı; kullanım koşulları da
> bu yüzden okunamadı. Dosya üçüncü taraf kaynaklarla yazıldı; axios.com
> alan adındaki sayfalar açılmadı.

- Adres: https://www.axios.com/local
- Katman: global listede **yerel** (ABD'de şehir başına bülten)
- Neden seçildi: bülten öncelikli yerel model; küçük masa (şehir başına ~2 muhabir)
- İnceleme: 2026-10-20 · koşul: robots.txt 200, sayfalar 403 (Türkiye) · üçüncü taraf kaynaklar
- İncelenen sayfalar: yok

## Özet — en öğretici 3 çözüm
1. **Ürün bülten; site bültenin arşivi.** Her şehir sayısı çoğunlukla günlük; her sayıda 3–5 özgün haber/yaşam yazısı, topluluktan gelen haberler ve **başka yayınların ilgili haberlerine bağlantılar**; her sayının ayrıca web sayfası var. Tipik kadro: şehir başına iki tam zamanlı muhabir ([Press Gazette](https://pressgazette.co.uk/newsletters/axios-local-newsletters-scale-cities-profit/), 2026-05-05; erişim 2026-10-20). — BH'ye: **kısmen**; "Bursa sabah bülteni" küçük masayla mümkün; başka yayınlara bağlantı vermek BH'nin "kaynak her zaman belirtilir" kuralıyla uyumlu. → `haber-muduru`.
2. **Sabit bölüm etiketleriyle kısa yazı ("Smart Brevity").** Kalın ara etiketler ("neden önemli", "büyük resim", "rakamlarla", "sonuç") ve madde işaretleri; ilk ekranda başlık + görsel + iki paragraf hedefi. Gerekçe: Axios araştırmasına göre okur bir haberde ortalama 26 sn kalıyor ([journalism.co.uk](https://www.journalism.co.uk/how-axios-is-reinventing-text-journalism-with-smart-brevity/), 2022, 2025-07-23 güncellendi; erişim 2026-10-20). — **kısmen**; BH'nin "üç madde" alanı (kural motoru taslağı) aynı ihtiyaca cevap veriyor; etiket sözlüğü Türkçe ve kendi sesimizle kurulmalı, Axios'un etiket adları kopyalanmaz.
3. **Yerel reklam + doğrudan satılan sponsorluk + gönüllü üyelik.** Gelir çoğunlukla reklam (doğrudan satılan premium sponsorluklar artan pay; yerel reklam 2024'te ikiye katlandı), etkinlik ve yıllık 25–500 $ arası gönüllü üyelik; üyelikte içerik çoğunlukla ücretsiz kalıyor, ayrıcalıklar sembolik (özel bülten, doğum günü anması, buluşma, tote çanta) ([Press Gazette](https://pressgazette.co.uk/newsletters/axios-local-newsletters-scale-cities-profit/), 2026-05-05). — **kısmen**; bülten sponsorluğu BH'ye uygun; AdSense değil doğrudan satış (BH için: AdSense askıda — kullanıcı kararı).

## 1. Anasayfa bilgi mimarisi
Ölçülmedi (erişim engelli).

## 2. Bölüm sayfası
Ölçülmedi. Her şehir sayısının kendi web sayfası olduğu biliniyor (Press Gazette, 2026-05-05); yapısı ölçülmedi.

## 3. Haber detay
- Sayfa ölçülmedi.
- Yazı biçimi (Smart Brevity): başlık → tek cümlelik giriş → kalın etiketli kısa bloklar → maddeler; ilk ekranda başlık, görsel ve iki paragraf ([journalism.co.uk](https://www.journalism.co.uk/how-axios-is-reinventing-text-journalism-with-smart-brevity/), 2025-07-23). Etiketlerin tam listesi resmî kaynaktan doğrulanmadı.

## 4. Son dakika / canlı
Ölçülmedi. Model günlük bülten temposunda; son dakika ürünü olarak tarif edilmiyor.

## 5. Yerel ve servis içerikleri
- 35 şehir (Nisan 2026), 2026 sonu hedefi 43; 100'den fazla yerel muhabir; 2 milyondan fazla ücretsiz abone ([Press Gazette](https://pressgazette.co.uk/newsletters/axios-local-newsletters-scale-cities-profit/), 2026-05-05).
- İçerik: özgün haber + yaşam yazıları + topluluk kaynaklı haber + başka yayınlara bağlantı. Etkinlik takvimi, restoran, emlak gibi servis listeleri bu kaynakta **anılmıyor** — doğrulanmadı.
- 2026'da Instagram, sonra LinkedIn/X/Facebook'a açılma planı (aynı kaynak).

## 6. Mobil davranış
Ölçülmedi. Gerekçe olarak "mobilde hızlı okuma" öne çıkarılıyor (journalism.co.uk, 2025-07-23).

## 7. Başarım
Ölçülmedi (erişim engelli; Cloudflare engeli nedeniyle PageSpeed de denenmedi).

## 8. SEO yapısı
- robots.txt tek sitemap ilan ediyor (`/sitemap.xml`); `/core/*`, `/admin/`, `/login/`, `/sso/`, `/api/` kapalı ([robots.txt](https://www.axios.com/robots.txt), 2026-10-20).
- JSON-LD, kanonik, haber sitemap'i: ölçülmedi.

## 9. Reklam
- Bülten içi yerel reklam ve doğrudan satılan "premium sponsorluk" (Press Gazette, 2026-05-05). Yerleşim ve sayı: ölçülmedi.

## 10. Gelir ve okur ilişkisi
- Gönüllü üyelik: yıllık 25–500 $; ücretli üye sayısı 2025 sonunda ~7 bin, Mayıs 2026'da 15 bin; içerik çoğunlukla ücretsiz (Press Gazette, 2026-05-05).
- 2021'deki ilk üyelik: şehir başına ayrı sayfa, önerilen tutar 50–500 $, üç ayda bir özel bülten; Axios'un mesajı "ayrıcalık için değil, yerel gazeteciliği desteklemek için" ([Nieman Lab](https://www.niemanlab.org/2021/10/axios-launches-paid-memberships-for-its-local-newsletters/), 2021-10, arama özeti — sayfa 403, açılamadı).
- Kârlılık: bütün olarak henüz kârlı değil; olgun pazarlar yeni şehirleri finanse ediyor; 2023'te gelir hedefi tutmayınca genişleme durduruldu, sonra yeniden başladı ([Press Gazette](https://pressgazette.co.uk/newsletters/axios-local-newsletters-scale-cities-profit/), 2026-05-05; [Adweek](https://www.adweek.com/media/axios-local-openai-2026/), 2026, yalnız ücretsiz giriş bölümü okundu).
- Ulusal bültenlerde ortalama açılma oranı %46 (2022 verisi; journalism.co.uk).

## 11. Erişilebilirlik
Ölçülmedi.

## 12. Yapay zekâ kullanımı
- Ocak 2025'te OpenAI ile üç yıllık anlaşma; yeni şehir açılışlarını destekliyor; OpenAI teknolojisi iş akışını sadeleştirme, yerel eğilimleri bulma, idari işi azaltma için kullanılıyor; karşılığında OpenAI Axios Local içeriğiyle model eğitebiliyor ([Press Gazette](https://pressgazette.co.uk/newsletters/axios-local-newsletters-scale-cities-profit/), 2026-05-05).
- Yönetim, gelen kutusunu özetleyen YZ'nin bülten etkileşimine "ters rüzgâr" olacağını öngörüyor (aynı kaynak).
- Okura işaretleme: ölçülmedi. **BH için: okura "yapay zekâ destekli" etiketi reddedildi.**

## Ölçüm dökümü
| ölçü | değer | yöntem |
|---|---|---|
| robots.txt | 645 B, 200 | `curl`, 2026-10-20, Türkiye |
| `/local` | 403, 5.365 B (Cloudflare sınama sayfası) | `curl` varsayılan UA |
| `/legal/terms` | 403, 5.404 B (Cloudflare sınama sayfası) | `curl` varsayılan UA |
| Başarım | ölçülmedi | erişim engelli |

İstek sayısı (www.axios.com): **3** (robots.txt, `/legal/terms`, `/local`).
