# Son dakika ve canlı — siteler arası desenler

Son güncelleme: 2026-10-20 (sentez; tohum 2026-10-19 korundu) · Kaynak siteler:
Bursada Bugün, Bursa Saati, Ege'de Son Söz, Habertürk, Spiegel (doğrudan);
NYT, Guardian, BBC, Le Monde, Manchester Evening News (ikincil); Sözcü,
Milliyet, Hürriyet, CNN Türk, NTV (eski kayıt).

Kanıt: **D** doğrudan · **İ** ikincil · **E** eski kayıt (URUN-PLANI §44,
2 Eylül 2026; URL/ölçü kaydı yok), bu taramada **doğrulanmadı**.

## 1. Anasayfada son dakika

| Site | K. | Çözüm | Kaynak |
|---|---|---|---|
| Bursada Bugün | D | Menü altında tek satır kayan "SON DAKİKA" şeridi + "Tümünü göster" → ayrı sayfa | `siteler/bursada-bugun.md` §4 · [anasayfa](https://www.bursadabugun.com/), 2026-10-20 |
| Bursa Saati | D | Kırmızı şerit, her öğede **mutlak saat** ("09:00 \| …"), oklarla gezinme + ayrı sayfa | `siteler/bursa-saati.md` §4 · [anasayfa](https://www.bursasaati.com.tr/), 2026-10-20 |
| Ege'de Son Söz | D | 1440 ilk ekranda şerit görülmedi; ayrı sayfa + detay rayında saat damgalı son haberler; göreli zaman yok | `siteler/egede-son-soz.md` §4, 2026-10-20 |
| Habertürk | D | Anasayfada panel yok; "Son Dakika" sabit **alt gezinme çubuğunda** (masaüstünde de) — tohumdaki 2 Eylül gözlemi **doğrulandı** | `siteler/haberturk.md` §4 · [anasayfa](https://www.haberturk.com/), 2026-10-20 |
| Spiegel | D (kısmi) | Her sayfada üst menü altında son dakika şeridi **yuvası**; içerik JS ile, inceleme anında boş. Bölüm/detayda mutlak tarih-saat. Anasayfa açılmadı → "son üç başlık + göreli zaman" **doğrulanmadı** | `siteler/spiegel.md` §4 · [/ausland/](https://www.spiegel.de/ausland/), 2026-10-20 |
| Sözcü | E | Koyu plaka + dolu kırmızı şeritte tek manşet | doğrulanmadı (eski kayıt; site erişim engelli) |
| Milliyet | E | Nav altında tek satır şerit, kırmızı `#ETİKET` önekli | doğrulanmadı (eski kayıt) |
| Hürriyet | E | "Bugün neler oldu?" ince şeridi + "SICAK GÜNDEM" üç kart | doğrulanmadı (eski kayıt) |
| CNN Türk | E | "CANLI ANLATIM" panosu, noktalı dikey zaman rayı, göreli damga | doğrulanmadı (eski kayıt; kütüphane listesinde değil) |
| NTV | E | Panel yok; üst şeritte bağlantı | doğrulanmadı (eski kayıt) |
| BBC · Guardian | E | Panel yok; kırmızı ● LIVE rozeti + göreli zaman | doğrulanmadı (eski kayıt) |

## 2. Son dakika etiketi ve SEO

| Site | K. | Çözüm | Kaynak |
|---|---|---|---|
| Habertürk | D | `<title>` ve JSON-LD `headline` "SON DAKİKA HABERİ:" önekli, **H1 öneksiz**, `alternativeHeadline` = H1; adres önekli. Haber sitemap'indeki 435 adresin 60'ı (%14) `son-dakika` içeriyor | `siteler/haberturk.md` Özet 2, §4 · [HD2](https://www.haberturk.com/gundem/son-dakika-haberi-meteoroloji-den-dogu-karadeniz-icin-yagmur-uyarisi-sicakliklar-mevsim-normali-altinda-20-ekim-hava-durumu-3920978), 2026-10-20 |
| Habertürk son dakika sayfası | D | Kartlarda tarih alanı var ama **boş** — sayfa tazelik söylemiyor (anti-desen) | `siteler/haberturk.md` §4 · [SD](https://www.haberturk.com/son-dakika-haberleri), 2026-10-20 |

## 3. Canlı blog

Doğrudan incelenen hiçbir sayfada `LiveBlogPosting` görülmedi (Habertürk,
Spiegel açık yolları, beş yerel site). Bilgi yalnız ikincil:

| Site | K. | Çözüm | Kaynak |
|---|---|---|---|
| NYT | İ | İki biçim: önem sırasına göre "canlı brifing" ve ters kronolojik blog | `siteler/nyt.md` Özet 1 (Nieman Lab, arama özeti) |
| Guardian | İ | Canlı blog günlük sayfa görüntülemesinin %15'ine kadar; üstte yazılı özet yok, **gönderi başlıkları arasında gezinme**; çok yazarlı araç. Uygun konu: sürekli değişen siyaset/spor; rutin olay uygun değil. Küçük yayıncı tek muhabirle yürütebilir | `siteler/guardian.md` Özet 2, §4 (Press Gazette, 2026-08-05) |
| BBC | İ | 2011'de canlı sayfanın üstünde son gelişmelerin kalıcı özeti örnek gösterilmiş; güncel biçim doğrulanmadı | `siteler/bbc-news.md` §4 |
| Le Monde | İ | Canlı yayın sitenin merkezinde; okur yorumları seçilerek canlıya alınıyor | `siteler/le-monde.md` Özet 3 |
| Manchester Evening News | İ | ~50 kişilik yerel masa; canlı/son dakika grup düzeyindeki ağla besleniyor | `siteler/manchester-evening-news.md` §4 (Press Gazette, 2025-12-22) |

**Ortak ders.**
- Türk yerel sitelerin cevabı aynı: **tek satır şerit + ayrı son dakika
  sayfası, mutlak saat.** Bu taramada göreli zaman ("x dk önce") doğrudan
  hiçbir sitede görülmedi; BH'nin §44'teki göreli zaman gerekçesi (BBC,
  Spiegel, CNN Türk) eski kayda dayanıyor ve doğrulanmadı.
- "Son dakika" kelimesini görünen başlıktan SEO katmanına taşımak (Habertürk)
  sayfayı sakin tutar; kelimenin sık kullanımı anlamını aşındırır.
- Canlı blogda iki ayrı soru var: "şu ana kadar ne biliyoruz" (özet/brifing)
  ve "en son ne oldu" (ters kronoloji). Guardian özeti kaldırıp gönderi
  başlıklarıyla gezinmeyi seçmiş.

**Hangi koşulda işe yarıyor.** Canlı sayfa yalnız sürekli yeni bilgi gelen
olaylarda (seçim gecesi, afet, büyük kaza) değer üretir. Guardian kaynağına
göre tek muhabirle yürütülebilir; MEN gibi masalar bunu grup ağına devrediyor.
Sürekli "son dakika" etiketi küçük masada yorgunluk yaratır.

**Bursa Hakimiyet'te durum.**
- `parca/son_dakika.html` (§44): şerit manşeti (koyu plaka + kırmızı alan,
  tek kalem) + beyaz zeminde zaman rayı; damga `goreli_zaman` (24 saate kadar),
  sonra `kisa_zaman`. Kutu rayda (anasayfa geniş, detayda tek sütun); kayan
  yazı değil. Paket H'den beri kalemler masanın `SonDakika` kayıtlarından:
  varsa "SON DAKİKA" + CANLI pili, yoksa "SON HABERLER" pilsiz
  (`icerik/models.py:929`; URUN-PLANI §70 H).
- `/son-haberler` sayfası var (`icerik/views.py` `son_haberler`).
- Ayrı SEO başlığı alanı var (`Haber.seo_baslik` → `<title>`/og;
  `haber_detay.html:6`). JSON-LD `headline` H1'den geliyor (`icerik/seo.py`).
- Canlı blog / `LiveBlogPosting`: **yok** (kodda geçmiyor).

**Öneri.**
- Olay bazlı canlı sayfa: üstte elle yazılan "şu ana kadar" özeti +
  zaman damgalı gönderiler + gönderi başlıklarıyla gezinme +
  `LiveBlogPosting` → P1 · M · → `full-stack-gelistirici` + `haber-muduru`
  (hangi olay canlıya alınır) + `seo-buyume-uzmani` (yapısal veri).
- Göreli zaman kararını **elle gözlemle** yeniden dayandır (BBC/Guardian/
  Spiegel anasayfaları) ya da okurla sına; şimdilik değişiklik önerilmez →
  açık soru, → `web-tasarim-direktoru`.
- "Son dakika" önekinin yalnız `seo_baslik`ta kullanılması bir editoryal
  karar → P2 · S · → `haber-muduru`.

**Açık sorular.** Olay ve MEN son dakika biçimi: ikisi de otomatik erişime
kapalı; yalnız elle gözlemle yazılabilir. CNN Türk kütüphane listesinde yok.
