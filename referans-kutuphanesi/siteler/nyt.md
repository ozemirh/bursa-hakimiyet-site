# The New York Times

> **İkincil kaynak — otomatik erişim yok.** nytimes.com ve alt alan adlarına
> hiçbir istek atılmadı (robots.txt dahil). Yalnız üçüncü taraf yayınlar
> (WebSearch/WebFetch) kullanıldı. "Arama özeti" işaretli bilgiler arama
> motorunun özetinden gelir, kaynak sayfa açılmamıştır — doğrulanmadı sayılır.

- Adres: https://www.nytimes.com
- Katman: global
- Neden seçildi: haber detay tipografisi, canlı blog, paket abonelik
- İnceleme: 2026-10-20 · koşul: üçüncü taraf kaynaklar · konum: Türkiye
- İncelenen sayfalar: yok

## Özet — en öğretici 3 çözüm
1. **Canlı haberde iki biçim: "canlı brifing" (önem sırası) ve klasik ters kronolojik blog.** En önemli gelişmeler öne alınan bir biçim ile en yeninin üstte olduğu blog yan yana kullanılıyor ([Nieman Lab](https://niemanlab.org/?p=112641), arama özeti). — BH'ye: **evet**; canlı sayfanın başına "şu ana kadar ne biliyoruz" bloğu küçük masada da yapılabilir. Tarih eski, güncel biçim doğrulanmadı.
2. **Editoryal YZ kuralları açık ve yasak listesi net.** Kurum içi özetleme aracı (Echo); izinli: SEO başlığı, özet, tanıtım metni, düzeltme önerisi, araştırma, quiz/SSS; yasak: haberi YZ ile yazdırmak ya da önemli ölçüde yeniden yazdırmak, ödeme duvarını aşmak, etiketlenmemiş YZ görseli/videosu yayımlamak, telifli/gizli kaynak verisini araca girmek ([Semafor](https://semafor.com/article/02/16/2025/new-york-times-goes-all-in-on-internal-ai-tools), 2025-02-16; erişim 2026-10-20). — **evet**; BH'nin `haber_taslak.py` SISTEM kurallarıyla (kopyalama yok, uydurma yok) aynı yönde.
3. **Habere ek ürünlerle paket abonelik.** Haber + oyunlar + yemek tarifleri + ürün inceleme + spor tek pakette ([Wyoming Üniv. Kütüphanesi duyurusu](https://www.uwyo.edu/news/2026/10/uw-libraries-upgrades-new-york-times-access-to-include-games-cooking-wirecutter-and-the-athletic.html), 2026-10, arama özeti). — **hayır**; 200+ kişilik masa ve ayrı ürün ekipleri gerektirir; yerel gazeteye taşınmaz.

## 1. Anasayfa bilgi mimarisi
Ölçülmedi (otomatik erişim yok).

## 2. Bölüm sayfası
Ölçülmedi (otomatik erişim yok).

## 3. Haber detay
Ölçülmedi (otomatik erişim yok). Tipografi değerleri ikincil kaynakta bulunamadı.

## 4. Son dakika / canlı
- "Canlı brifing" + ters kronolojik blog ayrımı (bkz. Özet 1).
- 2015'te canlı blog yazışması kurum içi sohbet kanalından editör onayıyla doğrudan yayına aktarılmış (deney) ([Nieman Lab](https://niemanlab.org/2015/08/the-new-york-times-live-blogged-last-nights-gop-debate-directly-from-slack), arama özeti).
- Göreli zaman / "yeni" işareti: üçüncü taraf yorumda kırmızı zaman damgası ve "new/latest" etiketlerinin aciliyet hissi verdiği anılıyor ([Medialyter](https://medialyter.substack.com/p/publishers-live-blogs-tool-cataloging-constant-crises), arama özeti) — biçim doğrulanmadı.

## 5. Yerel ve servis içerikleri
Ölçülmedi. Yerel/ilçe sayfası bu katmanda beklenmez.

## 6. Mobil davranış
Ölçülmedi (otomatik erişim yok).

## 7. Başarım
Ölçülmedi (otomatik erişim yok; PSI anahtarsız API 2026-10-20'de HTTP 429; CrUX tabanlı üçüncü taraf "Site Speed Awards" ilk 15 listesinde nytimes.com yok — [kaynak](https://sitespeedawards.catchmetrics.io/), erişim 2026-10-20).

## 8. SEO yapısı
Ölçülmedi (otomatik erişim yok).

## 9. Reklam
Ölçülmedi. Dijital reklam geliri 2026 2. çeyrekte %20,7 arttı (çeyrek sonuçları, arama özeti — [Subscription Insider](https://www.subscriptioninsider.com/blog/new-york-times-adds-280-000-digital-only-subscribers-but-subscriber-gains-slow-news)).

## 10. Gelir ve okur ilişkisi
- 2026 2. çeyrek: 12,80 milyon yalnız-dijital abone, toplam ~13,35 milyon; yalnız-dijital abone başına ortalama gelir 9,94 $; hedef 2027 sonunda 15 milyon (arama özeti, birden çok kaynak; [Subscription Insider](https://www.subscriptioninsider.com/blog/new-york-times-adds-280-000-digital-only-subscribers-but-subscriber-gains-slow-news)).
- Paket: haber + Games + Cooking + Wirecutter + The Athletic (bkz. Özet 3).
- Ödeme duvarı tipi, kayıt duvarı: ölçülmedi.

## 11. Erişilebilirlik
Ölçülmedi (otomatik erişim yok).

## 12. Yapay zekâ kullanımı
- Editoryal kurallar ve araçlar: bkz. Özet 2. Okura işaretleme yalnız YZ üretimi görsel/video için anılıyor (Semafor, 2025-02-16).
- **Otomatik sesli okuma**: Nisan 2024'te makalelerin çoğunu otomatik sesle sunma planı; ilk aşamada kullanıcıların %10'u, makale sayfalarının ~%75'i; tek sentetik ses; giriş yapmamış/abone olmayanlara sınır ([Axios](https://axios.com/2024/04/02/exclusive-nyt-to-soon-offer-most-articles-via-automated-voice), 2024-04-02, arama özeti — axios.com erişim engelli, açılmadı). 2026 durumu doğrulanmadı. **BH için: tarayıcı sesi reddedildi; yön yerel model.**
- **BH için: okura "yapay zekâ destekli" etiketi reddedildi.**

## Ölçüm dökümü
| ölçü | değer | yöntem |
|---|---|---|
| tümü | ölçülmedi | otomatik erişim yok; PSI HTTP 429 |

İstek sayısı (nytimes.com): **0**.
