# Bursa Hakimiyet ↔ desen fark matrisi

Son güncelleme: 2026-10-20 (ilk taramanın sentez geçişi; yeni ağ isteği yok).
Önceliklendirme kararı `haber-sistemi-uzmani`nındır; seçilenler
`URUN-PLANI.md`ye yeni bölüm olarak işlenir.

BH durumu **koddan** okundu (worktree `referans-kutuphanesi`, 2026-10-20):
`uygulama/sablonlar/`, `uygulama/statik/stil/site.css`, `uygulama/icerik/*.py`,
`uygulama/besleme/*.py`, URUN-PLANI §44–§70, DEGERLENDIRME-2026-10. Canlı ölçüm
gerektirenler "yerelde ölçülecek → `test-kalite-muhendisi`" diye işaretli.
Site ölçüleri: yerel rakiplerde **tek ölçüm, 2026-10-20, Türkiye, başsız
Chrome, kısıtlamasız, çerez kabul edilmedi**; sıralama değildir. Ayrıntı ve
URL'ler ilgili `desenler/*.md` dosyasında.

Açık işe bağlı satırlar: **[OPT]** optimizasyon turu (başarım bütçesi) ·
**[EKO]** ekonomi özel tasarımı (kategori 4) · **[TEK]** teknoloji özel
tasarımı (kategori 9) · **[KESİM]** DEGERLENDIRME Aşama 4 "kesim öncesi şart".

| # | Desen | Siteler (K.) | BH'de durum (kanıt) | Öneri | Öncelik | Emek | Sahip |
|---|---|---|---|---|---|---|---|
| 1 | Okur kanalları ve kurumsal sayfalar **çalışır bağlantıda** | Ege, Özgür Kocaeli altbilgide yayın ilkeleri/topluluk kuralları; Bursada Bugün WhatsApp hattı; Özgür Kocaeli basılı ön sayfa (D) | "Yayın ilkeleri", "Düzeltme ve cevap", "E-gazete" `href="#"` (`parca/kategori_bandi.html` 97, 107, 108); "İHBAR HATTI" `#kunye`, WhatsApp kanalı ve "E-Gazete" `#` (`parca/ust_bant.html` 25, 30, 36); künye sosyal bağlantıları `#` (`parca/kunye.html:39`) | Gerçek hedefe bağla ya da gerçek bilgi gelene kadar kaldır **[KESİM]** | P0 | S | `frontend-gelistirici` + `haber-muduru` (bilgiler gazeteden, kullanıcıya sorulur) |
| 2 | Görünür düzeltme/cevap notu + sayfası | Reuters hata kalır, düzeltme ayrıca (İ); Spiegel okur hata bildirimi (D); Habertürk ayrı Giriş/Güncelleme (D); Türk örneklerinde görünür düzeltme notu yok (D) | Güncelleme damgası var, ≥ 1 dk sonraysa (`haber_detay.html:46`); düzeltme/cevap modeli ve bloğu **yok**; DEGERLENDIRME Aşama 4 | Haber sayfasında düzeltme bloğu + "Düzeltme ve cevap" sayfası **[KESİM]** | P0 | M | `full-stack-gelistirici` + `haber-muduru`; yasal kısım → `hukuk-guvenlik-uyum-uzmani` |
| 3 | Sayfa başına **istek / aktarım / LCP** bütçesi, reklam açık ve kapalı | Türk sitelerinde aktarımı görsel + reklam belirliyor (Habertürk detay 281 istek, 63'ü reklam ağı; Bursada Bugün anasayfa 281 istek) (D); FT gecikme deneyi (İ) — `desenler/basarim.md` | Testte CLS ≤ 0,02, LCP görseli lazy değil (`icerik/tests_site_olcum.py` 32–33, 61); anasayfa HTML ≤ 200 KB + sorgu tavanları (`icerik/tests_butce.py` 46–71); istek/aktarım/LCP ms/detay HTML tavanı **yok** | Tavanları BH'nin kendi ölçüsünden koy; 1440/390; reklam-test açık/kapalı **[OPT]** | P0 | S | `test-kalite-muhendisi` |
| 4 | Kalıcı enstrüman sayfası (rakam arayan okura iniş adresi) | Habertürk şerit → `/ekonomi/piyasa/88-dolar` (saniyeli güncelleme damgası) (D); Bigpara kaynak + gecikme notu (İ) | Ekonomi teması: PİYASA CETVELİ (kaynak, bülten no, bayatlık uyarısı) + BURSA EKONOMİSİ (`parca/bolum/ekonomi.html`); enstrüman adresi, geçmiş, çevirici **yok** | Dolar/euro/gram altın kalıcı sayfa: bülten verisi + geçmiş tablo + kaynak/zaman/bayatlık **[EKO]** | P1 | M | `veri-entegrasyon-muhendisi` + `backend-gelistirici` + `seo-buyume-uzmani` |
| 5 | Detayda ilk ekran: H1 + spot + gövde başı | Ege H1 160 px (ilk ekranda reklam yok) ↔ Bursa Saati 573 px ↔ Habertürk gövde 1.268 px (D) | Her sayfada üstte 250 px'lik reklam şeridi (`taban.html` 148; `site.css` 334); H1 konumu **yerelde ölçülecek** | 1440/390, reklam açık/kapalı ölç; sonuca göre detayda şerit kararı | P1 | S | `test-kalite-muhendisi` → `web-tasarim-direktoru` |
| 6 | Paylaşım düğmeleri (WhatsApp dahil) | Bursada Bugün, Bursa Saati, Ege, Habertürk, Spiegel (D) | Detayda yalnız "BAĞLANTIYI KOPYALA", A−/A+, yazdır (`haber_detay.html` 50–55) | Betiksiz düz paylaşım bağlantıları (dış betik yok, CSP'ye uygun) | P1 | S | `frontend-gelistirici` |
| 7 | Olay bazlı canlı sayfa (`LiveBlogPosting`) | Guardian gönderi başlıkları gezinmesi, tek muhabirle yürütülebilir (İ); NYT canlı brifing (İ); doğrudan incelemede hiç görülmedi | `SonDakika` tablosu + CANLI pili (`parca/son_dakika.html`, `icerik/models.py:929`); canlı sayfa ve şeması **yok** | Üstte elle "şu ana kadar" özeti + damgalı gönderiler + başlık gezinmesi + şema; yalnız seçili olaylar | P1 | M | `full-stack-gelistirici` + `haber-muduru` + `seo-buyume-uzmani` |
| 8 | Sabah e-bülteni | Habertürk sabah bülteni formu, Bursada Bugün bülten sayfası (D); Axios bülten = ürün (İ) | Bülten yok; "Okurla kanal yok" (DEGERLENDIRME §4); Aşama 6'da önerilmiş | Bursa manşetleri + eczane + hava + Bursaspor; **gönderim elle** (zamanlanmış görev yok — değişmez karar) | P1 | M | `full-stack-gelistirici` + `haber-muduru`; izin metni → `hukuk-guvenlik-uyum-uzmani` |
| 9 | Yayın ilkeleri + `publishingPrinciples`, `contentLocation` (ilçe) | Bursada Bugün, Özgür Kocaeli `publishingPrinciples`; Özgür Kocaeli `contentLocation` (D) | `icerik/seo.py` `haber_makalesi`: ikisi de yok; haberin ilçesi var; JSON-LD kırıntısında ilçe yok, görünen kırıntıda var (`haber_detay.html:23`) | Sayfa (1. satır) gelince alanı ekle; `contentLocation` + kırıntıya ilçe | P1 | S | `seo-buyume-uzmani` (+ `haber-muduru` metin) |
| 10 | Google "tercih edilen kaynak" çağrısı | Habertürk künye altında kutu, Spiegel düğme, Özgür Kocaeli tam ekran pencere (D) | Yok (kodda geçmiyor) | Künye altında küçük bağlantı; okumayı kesen pencere değil | P1 | S | `seo-buyume-uzmani` + `haber-muduru` |
| 11 | İlçe sayfası tazeliği ve besleme dengesi | Bursada Bugün İnegöl ~9 aylık pencere; Ege Bornova 79 haberin 17'si belediye (D); MEN semt markası ~6 muhabir (İ) | `/ilce/<slug>` 17 ilçe, nöbetçi şeridiyle (`icerik/views.py` `ilce`); tazelik **yerelde ölçülecek** | İlçe başına son 30 gün haber sayısı ve en eski kalem yaşı; belediye bülteni oranı kuralı | P1 | S | `test-kalite-muhendisi` (ölçüm) + `haber-muduru` |
| 12 | Editör onaylı "üç madde" özeti (etiketsiz) | BBC "bir bakışta", insan onaylı (İ); Axios maddeli kısa yazı (İ); Spiegel özet kutusu (D, etiketli — etiket reddedildi) | Taslakta "üç madde" alanı var; sayfada madde bloğu yok; Aşama 6'da planlı | Detayda başlık bloğu altında editörün onayladığı üç madde; okura YZ etiketi yok | P1 | M | `yapay-zeka-uzmani` + `haber-muduru` |
| 13 | Resmî ilan teknik şartları (BİK analitik) | Bursada Bugün, Özgür Kocaeli'de BİK analitik isteği + `ilan.gov.tr`; Bursa Saati, Ege'de ilk isteklerde görülmedi (D) | Resmî ilan bölümü + `/resmi-ilan` var; BİK/`ilan.gov.tr` isteği kodda **yok** | Yükümlülük var mı teyit (açık soru; hukuki nitelendirme yapılmadı) | P1 | S | `hukuk-guvenlik-uyum-uzmani` |
| 14 | Mobil ilk ekran ve yapışkan öğe yüksekliği | Habertürk 390'da sabit/yapışkan 145 px (%17) (D); Bursa Saati 390'da bildirim istemi + ~270 px boş reklam alanı (D); Spiegel ~100 px (D) | Kategori bandı yapışkan (`site.css` 413); ≤ 600 px'te reklam şeridi 44 px; toplam **yerelde ölçülecek** | 390'da yapışkan toplamı ve ilk ekran başlık sayısını ölç, hedef koy **[OPT]** | P1 | S | `test-kalite-muhendisi` |
| 15 | Bölümde konu kümesi + kronolojik akış | Spiegel `/ausland/` 3 küme + 20'lik liste (D) | Üç kart kademesi + ritimli akış (`kategori.html`); konu dosyaları var, bölüme kümelenmiyor | Bölümde süren konu varsa 1–2 küme, yoksa yuva çizilmez | P2 | M | `web-tasarim-direktoru` + `haber-muduru` |
| 16 | Teknoloji bölümünde kümeleme (veri az) | Spiegel `/tests/` ürün kategorisi kümeleri (D, tek örnek) | Tema: BURSA'DA TEKNOLOJİ listesi (`parca/bolum/teknoloji.html`) | Bursa sanayi/teknopark gibi 1–2 konu kümesi; önce Guardian/NYT elle gözlemi **[TEK]** | P2 | M | `web-tasarim-direktoru` + `haber-muduru` |
| 17 | Ekonomi grafiği: tür veri ilişkisinden | FT Visual Vocabulary — yalnız yöntem (İ) | Cetvel tablo, grafik yok | Enstrüman geçmişinde tek çizgi grafik, "kendini anlatan" **[EKO]** | P2 | S | `web-tasarim-direktoru` |
| 18 | Gövde içi tek ilgili haber kutusu | Spiegel gövdenin 6. öğesinden sonra (D) | Sonda İLGİLİ HABERLER kutusu var; gövde içinde yok | Uzun haberde gövde içinde tek kutu | P2 | S | `frontend-gelistirici` |
| 19 | Okur hata bildirimi | Spiegel "redaksiyon hatası bildir" (D) | Yok | 2. satırdaki düzeltme akışına bağlı form | P2 | M | `full-stack-gelistirici`; KVKK → `hukuk-guvenlik-uyum-uzmani` |
| 20 | Sponsorlu içerik etiketleme | Bursa Saati "Advertorial" kategorisi; Spiegel küme içi etiketli kart (D) | Kodda sponsorlu içerik kavramı yok | İlk ücretli içerik gelmeden ayrışma ve etiket kuralı | P2 | S | `haber-muduru` + `hukuk-guvenlik-uyum-uzmani` |
| 21 | Kesinti (elektrik/su) servisi | Bursada Bugün ilçe ilçe kesinti galerileri (D) | Canlı veride yok (`canli-veri/`) | Eczane modeliyle kalıcı sayfa; izinli kaynak açık soru | P2 | M | `veri-entegrasyon-muhendisi` + `hukuk-guvenlik-uyum-uzmani` |
| 22 | Kulüp için sayfa dışı kanal | MEN kulüp WhatsApp kanalı ~84 bin, haftalık kulüp bülteni (İ) | Bursaspor sayfası yalnız maç + puan + fikstür (karar); kanal yok | WhatsApp kanalı ya da haftalık bülten; sayfa kararı değişmez | P2 | S | `haber-muduru` + `seo-buyume-uzmani` |
| 23 | Bölüm sayfasında `CollectionPage` | Bursada Bugün, Özgür Kocaeli (D) | Bölümde yalnız `BreadcrumbList` (`kategori.html:11`) | Şema ekle | P2 | S | `seo-buyume-uzmani` |
| 24 | YZ tarayıcılarına robots tutumu | Hürriyet/NTV/Milliyet tümden kapalı; Olay içerik sinyali; Sözcü `llms.txt` (D, robots.txt) | robots'ta YZ kuralı yok (`besleme/gorunumler.py` `robots`) | Seçenekleri yaz, kararı kullanıcı verir | P2 | S | `seo-buyume-uzmani` + `hukuk-guvenlik-uyum-uzmani` |

Öncelik: **P0** okuru/masayı doğrudan etkiler, açık bir işe girdi · **P1**
belirgin kazanç · **P2** iyi olur. Emek: S (gün) · M (hafta) · L (daha uzun).
K.: **D** doğrudan · **İ** ikincil. Reddedilenler satıra yazılmaz; desen
dosyasında "BH için: reddedildi (kullanıcı kararı)" diye işaretlidir (AdSense,
vefat/anma, tarayıcı sesi, okura YZ etiketi, Bursaspor kadro/diziler/
basketbol/künye/form, etiket sayfası, YouTube otomatik paylaşım, periyodik
türleri konu saymak, React/bundler).

**Bilgi (satır değil):** ürün şablonu `parca/seslendirme.html` hâlâ tarayıcı
ses motorunu kullanıyor ve okura öyle yazıyor; EKIP.md'de tarayıcı sesi
reddedildi, yön yerel model → `yapay-zeka-uzmani`.
