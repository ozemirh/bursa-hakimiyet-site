# Site listesi

Kapsam: dengeli ~20 site (kullanıcı kararı, 19 Ekim 2026). İlk taramada
araştırmacı listeyi doğrular; "aday" satırlarını gerekçesiyle kesinleştirir
ya da değiştirir. Son inceleme sütunu her taramada güncellenir.

## Erişim durumu (robots.txt, 20 Ekim 2026)

**Otomatik erişim yok — yalnız ikincil kaynak** (kullanıcı kararı, 20 Ekim
2026): NYT · Reuters · FT · BBC News · **BBC Türkçe** · Le Monde · Guardian.
Bu sitelerin robots.txt / kullanım koşulları otomatik, yapay zekâ ve ticari
erişimi yazılı izinsiz yasaklıyor. Siteye WebFetch, `curl`, Chrome ile **hiç
istek atılmaz** (robots.txt'in yeniden okunması hariç). Dosyaları yalnız şu
kaynaklarla yazılır; her birinde "ikincil kaynak" diye işaretlenir:

- **CrUX / PageSpeed Insights** (Google'ın verisi ve sunucusu) — başarım.
- **Üçüncü taraf yayınlar**: HTTP Archive Web Almanac, tasarım/vaka
  incelemeleri, basın haberleri (WebSearch ile bulunur, kendi alan adında
  değilse açılabilir).
- **Sitenin kendi mühendislik/tasarım blogu** — yalnız o alt alan adının
  robots.txt'i izin veriyorsa.
- **Elle gözlem**: kullanıcının ya da ekipten birinin tarayıcıda kendisi
  bakıp yazdığı notlar (kim, ne zaman, hangi koşulda — yazılır).

Rubrikte bu kaynaklarla doldurulamayan başlık "ölçülmedi (otomatik erişim
yok)" kalır.

**Kısmi:** Spiegel — yalnız robots.txt'in `Claude-User`'a açtığı yollar
(`/ausland/`, `/gesundheit/` …); anasayfa dahil diğer yollar ikincil kaynakla.

**Açık (yapay zekâ okumasına kural yok ya da yalnız model eğitimi kapalı):**
Hürriyet, NTV, Milliyet, Manchester Evening News, Olay, Bursada Bugün,
Habertürk, Texas Tribune, Axios. Her taramada yeniden kontrol edilir.
**Ölçülmedi:** T24 (robots.txt çekilemedi), Sözcü (incelenmedi) — ilk
istekten önce kontrol.

## Yerel

| Site | Adres | Neden | Dosya | Son inceleme |
|---|---|---|---|---|
| Olay | olay.com.tr | Bursa'nın doğrudan rakibi; aynı okur | `siteler/olay.md` | — |
| Bursada Bugün | bursadabugun.com | Bursa'da dijital ağırlıklı rakip | `siteler/bursada-bugun.md` | — |
| (aday) Bursa'dan üçüncü rakip | — | trafik sırasıyla araştırmacı seçer | — | — |
| (aday) Başka şehirden güçlü yerel | — | ör. İzmir/Kocaeli/Konya; ilçe ve servis içeriği iyi olan seçilir | — | — |
| (aday) Başka şehirden güçlü yerel | — | aynı ölçüt | — | — |

## Ulusal

| Site | Adres | Neden | Dosya | Son inceleme |
|---|---|---|---|---|
| Hürriyet | hurriyet.com.tr | Klasik Türk gazetesi mimarisinin büyük örneği | `siteler/hurriyet.md` | — |
| Sözcü | sozcu.com.tr | Son dakika şeridi, yoğun anasayfa (§44 kaynağı) | `siteler/sozcu.md` | — |
| Habertürk | haberturk.com | Video/TV entegrasyonu, servis sayfaları | `siteler/haberturk.md` | — |
| NTV | ntv.com.tr | Sakin, hızlı, düzenli bilgi mimarisi | `siteler/ntv.md` | — |
| Milliyet | milliyet.com.tr | Bölüm sayfası kalıbı (§46 kaynağı) | `siteler/milliyet.md` | — |
| T24 | t24.com.tr | Metin öncelikli, köşe yazısı ağırlıklı | `siteler/t24.md` | — |
| BBC Türkçe | bbc.com/turkce | Kamu yayıncısı disiplini, reklamsız okuma | `siteler/bbc-turkce.md` | — |

## Global

| Site | Adres | Neden | Dosya | Son inceleme |
|---|---|---|---|---|
| The New York Times | nytimes.com | Haber detay tipografisi, canlı blog | `siteler/nyt.md` | — |
| The Guardian | theguardian.com | Açık erişim + okur desteği, bölüm sayfası (§46) | `siteler/guardian.md` | — |
| BBC News | bbc.com/news | Kademeli bölüm sayfası, göreli zaman (§44, §46) | `siteler/bbc-news.md` | — |
| Reuters | reuters.com | Ajans dili, kaynak/düzeltme gösterimi | `siteler/reuters.md` | — |
| Financial Times | ft.com | Veri gösterimi, ekonomi sayfası (özel tasarım adayı: ekonomi) | `siteler/ft.md` | — |
| Le Monde | lemonde.fr | Klasik gazete kimliğinin dijitale taşınması | `siteler/le-monde.md` | — |
| Der Spiegel | spiegel.de | Son başlık rayı, "Vor 6 Min" (§44) | `siteler/spiegel.md` | — |
| Manchester Evening News | manchestereveningnews.co.uk | Global ölçekte **yerel** gazete; ilçe/semt ve reklam yoğunluğu | `siteler/manchester-evening-news.md` | — |
| Texas Tribune | texastribune.org | Kâr amacı gütmeyen bölgesel haber; açıklayıcı/veri haberi | `siteler/texas-tribune.md` | — |
| Axios Local | axios.com/local | Şehir bülteni öncelikli yerel model | `siteler/axios-local.md` | — |

## Odak konuları (ilk taramada öncelikli)

Kullanıcının açık işleriyle eşleşir; desen dosyaları önce bunlar için yazılır:

- **Ekonomi sayfası** (özel tasarım, kategori 4): FT, Reuters, Hürriyet, Habertürk.
- **Teknoloji sayfası** (özel tasarım, kategori 9): Guardian, NYT, Spiegel, T24.
- **Spor/kulüp sayfası** (Bursaspor yapıldı; yalnız karşılaştırma): Manchester
  Evening News (kulüp sayfaları), Sözcü, NTV.
- **Başarım bütçesi** (optimizasyon turu): tüm sitelerde HTML bayt, istek
  sayısı, LCP.
- **Yerel/ilçe sayfası ve servis içerikleri**: yerel katmanın tamamı.
