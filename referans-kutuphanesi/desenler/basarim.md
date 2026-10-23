# Başarım — siteler arası desenler

Son güncelleme: 2026-10-20 (sentez) · Açık iş: **optimizasyon turu (başarım
bütçesi)**. Kaynak siteler: Bursada Bugün, Bursa Saati, Ege'de Son Söz, Özgür
Kocaeli, Habertürk, Spiegel (doğrudan); Guardian, BBC, FT, Manchester Evening
News (ikincil).

**Koşul (doğrudan ölçümler):** tek ölçüm, 2026-10-20, Türkiye (yerel makine,
ev bağlantısı), başsız Chrome, **ağ/CPU kısıtlanmadı**, çerez/rıza kabul
edilmedi, önbellek kapalı. LCP değerleri CrUX saha verisiyle
karşılaştırılamaz. Dinleme penceresi farklı: yerel siteler ~8 sn, Habertürk
14 sn, Spiegel 25 sn. Spiegel rıza öncesi ölçüldü (reklam/izleme betiklerinin
çoğu yüklenmemiş). PageSpeed/CrUX anahtarsız API kotası doluydu (HTTP 429).
Yerel rakipler için sıralama değildir.

## 1. Doğrudan ölçümler

| Site · sayfa | HTML (gzip / açılmış) | İstek | Aktarım | LCP | CLS | Kaynak |
|---|---|---|---|---|---|---|
| Bursada Bugün · anasayfa 1440 | 30.137 / 215.501 B | 281 | 8,26 MB | 832 ms | 0,230 | `bursada-bugun.md` §7 |
| Bursada Bugün · detay 1440 | 12.473 / 59.104 B | 104 | 1,87 MB | 952 ms | 0,201 | aynı |
| Bursa Saati · anasayfa 1440 / 390 | 40.212 / 272.489 B | 101 / 89 | 3,15 / 3,02 MB | 944 / 860 ms | 0,007 / 0 | `bursa-saati.md` §7 |
| Bursa Saati · detay 1440 | 33.992 / 192.682 B | 70 | 2,54 MB | 1.296 ms | 0,008 | aynı |
| Ege'de Son Söz · anasayfa 1440 / 390 | 29.973 / 201.916 B | 79 / 72 | 5,08 / 5,01 MB | 860 / 840 ms | 0,002 / 0 | `egede-son-soz.md` §7 |
| Ege'de Son Söz · detay 1440 | 32.830 / 179.100 B | 97 | 1,69 MB | 812 ms | 0,054 | aynı |
| Özgür Kocaeli · anasayfa 1440 / 390 | 45.530 / 288.215 B | 71 / 69 | 1,92 / 1,89 MB | 1.052 / 1.028 ms | 0,020 / 0 | `ozgur-kocaeli.md` §7 |
| Özgür Kocaeli · detay 1440 | 36.766 / 160.560 B | 100 | 2,18 MB | 1.256 ms | 0,016 | aynı |
| Habertürk · anasayfa 1440 / 390 | 57.809 / 367.066 B | 196 / 163 | 11,75 / 8,25 MB | 292 / 252 ms | 0,008 / 0 | `haberturk.md` §7 |
| Habertürk · detay 1440 / 390 | 25.824 / 117.396 B | 281 / 169 | 10,39 / 8,78 MB | 292 / 708 ms | 0,013 / 0 | aynı |
| Spiegel · bölüm 1440 / 390 | 112.460 / 667.708 B | 58 / 58 | 1,43 / 1,45 MB | 708 / 812 ms | 0,004 / 0 | `spiegel.md` §7 |
| Spiegel · haber 1440 / 390 | 116–119 KB / 546–561 KB | 54–57 | 1,47–1,55 MB | 476–1.308 ms | ≤0,004 | aynı |

## 2. Ölçümlerden okunanlar

| Gözlem | Kanıt |
|---|---|
| Aktarımın büyük kısmı **görsel ve üçüncü taraf** | Bursada Bugün anasayfa isteklerinin 159'u görsel alanına, 23'ü kendi reklam alanına; Habertürk detayda en çok istek reklam ağına (63) — `bursada-bugun.md` §7, `haberturk.md` §7 |
| CLS'yi **görsel ölçüsü ve rezerve reklam alanı** belirliyor | Bursada Bugün 182 `img`'nin 17'sinde `width/height` (CLS 0,230); Ege 110'un 108'inde (0,002); Bursa Saati boş reklam alanı önceden ayrılmış (0,007); Habertürk gövde içi yuva `min-h` ile (0,013) — ilgili dosyalar §7/§9/§11 |
| HTML'i **tekrar eden gezinme verisi** şişiriyor | Bursa Saati her sayfada 268 `SiteNavigationElement` JSON-LD + 81 il hava bağlantısı — `bursa-saati.md` §7 |
| LCP öğesi genelde manşet görseli; tembel yüklenen görselde LCP **metne** kayıyor | Habertürk detay LCP = H1 (görsel `data-src`) — `haberturk.md` §7 |
| Görselde kırılım başına kırpım + odak noktası, `width/height` bildirimi | Spiegel 3:2 masaüstü / 4:3 dar; CLS ≈ 0 — `spiegel.md` §6 |

## 3. İkincil

| Site | K. | Bulgu | Kaynak |
|---|---|---|---|
| FT | İ | 2016 A/B deneyi: aboneye yapay gecikme; 28 günde okunan haber 1 sn'de −%4,6, 3 sn'de −%7,9; etki zamanla büyüdü | `ft.md` Özet 1 · [MediaShift](https://mediashift.org/2016/04/a-faster-ft-com-how-slow-websites-damage-publishers-revenue/) |
| Guardian · BBC | İ | CrUX tabanlı göreli puan (en büyük 50 İngilizce haber sitesi, 2025 Ç4): Guardian 92 (1.), BBC 83 (10.); NYT ve Reuters ilk 15'te yok | `guardian.md` §7, `bbc-news.md` §7 · [Site Speed Awards](https://sitespeedawards.catchmetrics.io/) |
| Reach / MEN | İ | Yeni platformla sayfa hızı "üç kat", ziyaret başına sayfa +%2, reklam kaynaklı kayma giderildi — **şirket beyanı**, bağımsız ölçüm değil | `manchester-evening-news.md` §7 (Press Gazette, 2025-03-04) |
| BBC World Service | İ | JS'siz "lite" sayfa denemesi (~1,65 MB → ~135 KB); forum notu, **doğrulanmadı** | `bbc-news.md` Özet 3, `bbc-turkce.md` Özet 3 |

**Ortak ders.** Sunucu render edilen haber sayfasının kendi baytı küçük
(12–120 KB gzip); farkı **görsel ve reklam/üçüncü taraf istekleri** yaratıyor.
CLS'yi düşük tutan iki şey ucuz: görselde `width/height`, reklamda önceden
ayrılmış alan. Hızın okumaya etkisi ölçülebilir (FT).

**Hangi koşulda.** Reklamla yaşayan sitede bütçe **reklam açıkken** ölçülmeli;
rıza öncesi ölçüm (Spiegel) gerçek yükü küçük gösterir.

**Bursa Hakimiyet'te durum** (URUN-PLANI §70 ölçüm tablosu ve testler).
- Ölçülmüş: anasayfa HTML 32 KB gzip; anasayfa görsel indirme 0,15 MB (390) /
  0,23 MB (1440); `site.css` 19,7 KB gzip; dış istek (Google Fonts) 0;
  srcset/sizes/ölçülü görsel (Paket D); önbellekten anasayfa 1,5 ms.
- Test bütçesi: CLS ≤ 0,02 ve "LCP görseli `lazy` değil"
  (`icerik/tests_site_olcum.py` 32–33, 61); anasayfa HTML ≤ 200 KB açılmış
  ve sayfa başına sorgu tavanı (`icerik/tests_butce.py` 46–71).
- **Bütçede olmayan:** sayfa başına istek sayısı, toplam aktarım, LCP ms,
  detay HTML tavanı; reklam açıkken ölçüm.

**Öneri.**
- Sayfa başına **istek / aktarım / LCP** tavanı (anasayfa, bölüm, detay;
  1440 ve 390), **reklam kapalı ve reklam-test açık** iki koşulda; tavan BH'nin
  kendi ölçüsünden konur, yukarıdaki tablo bağlamdır → P0 · S ·
  → `test-kalite-muhendisi` (optimizasyon turu).
- Kısıtlı ağ/CPU profiliyle (mobil) tek ölçüm turu; PageSpeed/CrUX için
  anahtar edinmek kullanıcı adımı → P1 · S · → `test-kalite-muhendisi`.
- "Lite"/düşük veri sürümü → şimdilik önerilmez (BH zaten sunucu render,
  JS'siz okunur); kayıt.
- React/Next (BBC Simorgh), Preact/Webpack (Guardian) yığınları →
  **BH için: reddedildi (kullanıcı kararı — Tailwind/React/bundler).**
