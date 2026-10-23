# Gelir ve okur ilişkisi — siteler arası desenler

Son güncelleme: 2026-10-20 (sentez) · Kaynak siteler: Bursada Bugün, Bursa
Saati, Ege'de Son Söz, Özgür Kocaeli, Habertürk, Spiegel (doğrudan); MEN,
Guardian, Axios Local, Texas Tribune, T24, Sözcü, NYT, FT, BBC, Le Monde,
Reuters (ikincil). Abone/okur sayıları kaynakların verdiği rakamdır, tahmin
değil; yerel rakipler için yalnız görülen kanal yazıldı.

## 1. Türk siteleri — görülen kanallar (doğrudan, 2026-10-20)

| Kanal | Görülen | Kaynak |
|---|---|---|
| Ödeme duvarı | Beş Türk sitesinde **yok** (`isAccessibleForFree` true ya da gövde açık) | `bursada-bugun.md` §10, `bursa-saati.md` §10, `egede-son-soz.md` §10, `ozgur-kocaeli.md` §10, `haberturk.md` §10 |
| E-bülten | Bursada Bugün `/bulten.html`; Habertürk altbilgi formu (günün manşetleri + en çok okunanlar, her sabah) | D · [anasayfa](https://www.bursadabugun.com/); `haberturk.md` §10 |
| Tarayıcı bildirimi | Bursa Saati ilk ziyarette OneSignal istemi (mobilde 178 px); Özgür Kocaeli (Bildirt); Habertürk alt çubukta sayılı "Bildirimler" | D · `bursa-saati.md` §6, §10; `ozgur-kocaeli.md` §10; `haberturk.md` §10 |
| WhatsApp hattı / ihbar | Bursada Bugün haber hattı; Bursa Saati, Özgür Kocaeli ihbar hattı (+ `/haber-ihbar` sayfası) | D |
| Google kaynak tercihi / Google News takip | Özgür Kocaeli tam ekran pencere ("Sonra hatırlat"); Habertürk detayda kutu; Bursada Bugün, Ege Google News düğmesi | D · `ozgur-kocaeli.md` Özet 1 |
| Yorum | Özgür Kocaeli var (topluluk kuralları); Habertürk yok | D |
| Basılı abonelik | Özgür Kocaeli basılı gazete abonelik + banka hesapları sayfası | D · `ozgur-kocaeli.md` §10 |
| Resmî ilan | Bursada Bugün sayfa + `ilan.gov.tr` çerçevesi + **BİK analitik isteği**; Özgür Kocaeli kaydırıcı + BİK analitik; Habertürk anasayfa/ekonomide resmi ilan blokları; Bursa Saati ve Ege'de BİK analitik ilk isteklerde görülmedi | D · `bursada-bugun.md` §10, `ozgur-kocaeli.md` §10 |
| Yayın ilkeleri / topluluk kuralları | Ege, Özgür Kocaeli altbilgide | D |
| Ücretli katman işareti | Spiegel kartta "+", pay or consent, yer imi listesi | D · `spiegel.md` §10 |

## 2. Gelir modelleri — ikincil

| Site | Model | Kaynak |
|---|---|---|
| Manchester Evening News | Premium (Kasım 2025): aylık £4,99; **son dakika ve kamu yararı ücretsiz**, röportaj/görüş/derinlik ücretli + daha az reklam; MEN 6 bin+ abone (Ağu 2026); abonelik reklamı **tamamlıyor** | `manchester-evening-news.md` Özet 2, §10 |
| Guardian | Duvar yok; haber sonu destek çağrısı; 1,4 milyon düzenli destekçi | `guardian.md` Özet 1 |
| Axios Local | Bülten ürün, site arşiv; gönüllü üyelik yıllık 25–500 $ (15 bin, Mayıs 2026); doğrudan satılan sponsorluk; şehir başına ~2 muhabir | `axios-local.md` Özet 1, 3 |
| Texas Tribune | Kâr amacı gütmeyen: üyelik + büyük bağış + kurumsal sponsorluk + etkinlik; günlük bülten | `texas-tribune.md` Özet 3, §10 |
| T24 | Ücretsiz üyelik → abonelik (reklamsız + özel içerik); erişim engeli sonrası resmi ilanların kesildiği bildirildi | `t24.md` Özet 1–2 |
| Sözcü | 2016'da reklamsız abonelik (tarihsel; güncel doğrulanmadı) | `sozcu.md` Özet 3 |
| FT | Aboneye ayda 10 hediye haber | `ft.md` §10 |
| NYT · Le Monde · BBC · Reuters | Paket abonelik / 600 bin dijital abone / ABD'de dinamik duvar / profesyonel kitle — ölçek BH'ye taşınmaz | ilgili dosyalar §10 |

**Ortak ders.**
- Türk yerel sitelerde gelir **açık erişim + reklam + resmî ilan**; okur
  ilişkisi bildirim, WhatsApp hattı ve Google takip çağrısıyla kuruluyor.
- Yerel ölçekte ücretli katmanın tek doğrudan karşılığı MEN: "acil ve kamu
  yararı ücretsiz, derinlik ücretli". Türkiye'de yerel okurun ödeme isteği bu
  kütüphanede ölçülmedi.
- Bülten küçük masanın en ucuz sadakat aracı (Axios: ürünün kendisi;
  Habertürk: sabah özeti).
- Resmî ilan geliri kırılgan ve düzenlemeye bağlı (T24, ikincil).

**Hangi koşulda.** Ödeme duvarı ayırt edici, düzenli derin içerik ister
(MEN ~50 kişilik masa). Bülten ve WhatsApp kanalı 1 editörle yürür. Tam ekran
"Google'da tercih et" penceresi okumayı keser; aynı çağrı künye altında
(Habertürk) daha az maliyetli.

**Bursa Hakimiyet'te durum.**
- Ödeme duvarı yok (`isAccessibleForFree: True`, `icerik/seo.py:230`).
- Bülten, yorum, okur kanalı **yok**; DEGERLENDIRME-2026-10 "Okurla kanal
  yok… bildirim açılma oranı %0,21"; sabah bülteni ve WhatsApp kanalı
  Aşama 6'da önerilmiş.
- Üst bantta "İHBAR HATTI" → `href="#kunye"`, "WhatsApp kanalımız" →
  `href="#"`, "E-Gazete" → `href="#"` (`parca/ust_bant.html` 25, 30, 36);
  künyede sosyal bağlantılar `href="#"` (`parca/kunye.html:39`).
- 22.683 kişilik push kitlesi eski sağlayıcıda; taşınması kullanıcı kararı
  bekliyor (URUN-PLANI §70).
- Resmî ilan bölümü ve `/resmi-ilan` var; BİK analitik / `ilan.gov.tr`
  istekleri kodda **görülmedi**.

**Öneri.**
- Ölü bağlantıları (ihbar, WhatsApp kanalı, e-gazete, sosyal) gerçek hedefe
  bağla ya da kaldır → P0 · S · → `frontend-gelistirici` + `haber-muduru`
  (gerçek bilgiler gazeteden — kullanıcıdan istenir).
- Sabah e-bülteni (Bursa manşetleri, eczane, hava, Bursaspor). **Gönderim
  elle** (panel düğmesi): zamanlanmış görev açılmaz (değişmez karar) → P1 · M ·
  → `full-stack-gelistirici` + `haber-muduru`; liste/izin metni →
  `hukuk-guvenlik-uyum-uzmani`.
- WhatsApp kanalı (sayfa dışı dağıtım) → P1 · S · → `haber-muduru` +
  `seo-buyume-uzmani`.
- BİK analitik toplayıcısı ve resmî ilan yayınının teknik şartları BH için
  geçerli mi → açık soru, P1 · S · → `hukuk-guvenlik-uyum-uzmani`.
- Ücretli katman / reklamsız abonelik → şimdilik önerilmez; yerel okurun
  ödeme isteği ölçülmeden karar verilemez → P2 · → `haber-muduru`.
- Yorum → P2 · M · moderasyon emeği + hukuk → `haber-muduru` +
  `hukuk-guvenlik-uyum-uzmani`.
- AdSense → **BH için: reddedildi (kullanıcı kararı).** YouTube'a otomatik
  paylaşım → **BH için: reddedildi (kullanıcı kararı).** Vefat/anma ilanları
  → **BH için: reddedildi (kullanıcı kararı).**
