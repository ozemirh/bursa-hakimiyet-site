# Yapay zekâ kullanımı — siteler arası desenler

Son güncelleme: 2026-10-20 (sentez) · Kaynak siteler: Spiegel (doğrudan,
okur tarafı); beş Türk sitesi (doğrudan, görülmedi); NYT, BBC, Reuters, FT,
Reach/MEN, Le Monde, Axios Local (ikincil). Okura işaretleme yalnız kayıt
içindir: **BH'de okura "yapay zekâ destekli" etiketi yok (kullanıcı kararı).**

## 1. Okur tarafı

| Site | K. | Çözüm | Kaynak |
|---|---|---|---|
| Spiegel | D | Detayda başlık bloğu altında **YZ özeti kutusu**: varsayılan kapalı, tıklayınca açılıyor, altında otomatik üretim notu + açıklama sayfası + "yararlı mıydı" oylaması | `spiegel.md` §12 · [haber 1](https://www.spiegel.de/ausland/mallorca-hoechste-sturmwarnung-fuer-baleareninsel-ausgerufen-a-e4318c01-6ad7-4e03-8859-8482b32fde6c), 2026-10-20 |
| Spiegel | D | "Makaleyi dinle (**N dakika**)" düğmesi; ses üretim yöntemi doğrulanmadı | aynı |
| Spiegel | D | Makale altı öneri motoru + yanıt gelmezse yedek liste | `spiegel.md` §3 |
| Bursada Bugün · Bursa Saati · Ege · Özgür Kocaeli · Habertürk | D | Özet, seslendirme, öneri işareti **görülmedi** | ilgili dosyalar §12 |
| BBC | İ | Seçili haberlerde "bir bakışta" madde özeti: tek onaylı istem, **her çıktıyı gazeteci onaylıyor** (2025 pilotu) | `bbc-news.md` Özet 1 (NewscastStudio, arama özeti) |
| NYT | İ | Otomatik sesli okuma planı (2024; 2026 durumu doğrulanmadı) | `nyt.md` §12 (Axios, arama özeti) |
| FT | İ | "Ask FT": arşivden cevap, **dipnotlu kaynak haberler + yayın tarih aralığı**; kurumsal abonelere | `ft.md` Özet 3 (Voicebot.ai, 2024-03-25) |
| Le Monde | İ | İngilizce sürüm: YZ ilk çeviri + insan seçimi ve düzeltisi | `le-monde.md` Özet 2 |

## 2. Masa tarafı ve ilke

| Site | K. | Çözüm | Kaynak |
|---|---|---|---|
| NYT | İ | İç araç (Echo); **izinli:** SEO başlığı, özet, tanıtım metni, düzeltme önerisi, araştırma; **yasak:** haberi YZ'ye yazdırmak/önemli ölçüde yeniden yazdırmak, etiketsiz YZ görseli, gizli kaynak verisini araca girmek | `nyt.md` Özet 2 · [Semafor](https://semafor.com/article/02/16/2025/new-york-times-goes-all-in-on-internal-ai-tools), 2025-02-16 |
| Reuters | İ | "Sorumluluk editörde": YZ çıktısı yalnız editör denetimiyle; sonucu maddi etkileyen kullanım açıklanır | `reuters.md` Özet 3 |
| BBC | İ | "Style Assist": yerel demokrasi muhabirliği metinlerini BBC biçimine çeviren model, kıdemli gazeteci onayı | `bbc-news.md` Özet 2 |
| Reach / MEN | İ | "Guten": kardeş site, ajans ve polis metinlerini yeniden yazma; değişiklikler vurgulanıyor, YZ destekli haber adresleri kayıtta | `manchester-evening-news.md` §12 |
| Axios Local | İ | OpenAI anlaşması: iş akışı, yerel eğilim bulma; karşılığında içerikle model eğitimi | `axios-local.md` §12 |

## 3. YZ tarayıcılarına tutum (robots.txt, doğrudan okundu)

Hürriyet, NTV, Milliyet 10 botu tümden kapatıyor; Olay `ai-train=no,
use=reference` ve Claude botlarına `Disallow: /`; Sözcü `llms.txt` ile
yönlendiriyor (2026-10-19 kopyası); Spiegel `Claude-User`'a deneme açılımı;
Le Monde ve Axios içerik lisans anlaşması yapmış (ikincil). Bkz. `seo-yapisi.md`.

**Ortak ders.**
- Okur tarafında doğrudan görülen tek uygulama (Spiegel) özeti **varsayılan
  kapalı** ve geri bildirimli sunuyor. İkincil örneklerin hepsinde insan
  onayı şart (BBC, NYT, Reuters).
- Masa tarafında ayrım net: **özet, başlık, düzeltme önerisi evet; haberi
  yazdırmak hayır** (NYT). BH'nin "kural motoru gövde yazmaz" kararıyla aynı yön.
- Kaynak metni yeniden yazan araçlar (Guten, Style Assist) BH'nin "kaynaktan
  cümle kopyalanmaz" kuralıyla çelişir.

**Hangi koşulda.** İnsan onaylı özet küçük masada da mümkün (BH taslağında
zaten "üç madde" alanı var). Arşivden dipnotlu cevap (Ask FT) arşivin
temiz ve yapılandırılmış olmasını, okur tarafında açık işaretlemeyi gerektirir.

**Bursa Hakimiyet'te durum.**
- Masa: kural motoru (anahtarsız, gövde yazmaz), taslak → denetim → düzeltme
  zinciri, konu takibi **onaysız bağlamaz**, K2 olgu denetimi yayın kapısında,
  YZ köken kaydı (migration 0019) — okura etiket basılmıyor (CLAUDE.md;
  URUN-PLANI §70 M).
- Okur: "Üç maddede ne oldu", konu dosyası özeti **planlı**, editör onaylı
  (DEGERLENDIRME-2026-10 Aşama 6); ürün kodunda madde bloğu yok.
- Seslendirme: ürün şablonu hâlâ tarayıcının ses motorunu kullanıyor —
  `parca/seslendirme.html` durum metni "Haber, tarayıcınızın ses motoruyla
  okunur". EKIP.md'de tarayıcı sesi **reddedildi**, yön yerel model
  (DEGERLENDIRME Aşama 6) → `yapay-zeka-uzmani` (bilgi; yeni öneri değil).
- robots'ta YZ tarayıcılarına kural yok (`besleme/gorunumler.py` `robots`).

**Öneri.**
- Editör onaylı "üç madde" bloğu (detayda başlık bloğunun altında; BBC/Axios
  deseni, **etiketsiz**) → P1 · M · → `yapay-zeka-uzmani` + `haber-muduru`.
- Yazılı iç YZ kullanım ilkesi (NYT izin/yasak listesi biçiminde; mevcut
  SISTEM kurallarını belgeler, gevşetmez) → P2 · S · → `haber-muduru`.
- Yerel modelle üretilen seste süre gösterimi ("N dk dinle", Spiegel) →
  P2 · S · → `yapay-zeka-uzmani` (yerel model gelince).
- Okura "yapay zekâ destekli" etiketi / YZ özeti işareti (Spiegel, BBC) →
  **BH için: reddedildi (kullanıcı kararı).**
- Tarayıcı sesi (Web Speech) → **BH için: reddedildi (kullanıcı kararı).**
- Arşivden YZ cevabı (Ask FT) → kayıt; okura YZ işaretlemesi gerektirdiği
  için yukarıdaki kararla birlikte değerlendirilir, önerilmez.
