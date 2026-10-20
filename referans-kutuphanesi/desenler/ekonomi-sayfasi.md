# Ekonomi sayfası — siteler arası desenler

Son güncelleme: 2026-10-20 (sentez) · Açık iş: **özel tasarım, kategori 4**
(EKIP.md). Kaynak siteler: Habertürk, Bursada Bugün, Bursa Saati, Ege'de Son
Söz (doğrudan); Hürriyet/Bigpara, Milliyet/Uzmanpara, FT, Reuters (ikincil).

Kanıt: **D** doğrudan (Türkiye, 2026-10-20) · **İ** ikincil (sayfalar
açılmadı; arama özeti olanlar doğrulanmadı sayılır).

| Site | K. | Çözüm | Kaynak |
|---|---|---|---|
| Habertürk — bölüm | D | 11 kalemlik piyasa şeridi → manşet → **hisseler tablosu** → **kur çevirici** (12 birim) → kripto özeti → **KAP bildirim listesi** (tarih-saatli), aralarda 9'luk haber blokları; 14 kalemli alt menü (Altın, Döviz, Borsa, KAP, Kripto, Otomobil, Emlak, Sosyal Güvenlik …). Şeritte **veri zamanı yok** | `siteler/haberturk.md` §2 · [/ekonomi](https://www.haberturk.com/ekonomi), 2026-10-20 |
| Habertürk — enstrüman sayfası | D | Her şerit kalemi kalıcı adrese gidiyor: değer + % değişim → alış/satış/fark/önceki kapanış/en yüksek/en düşük → **saniyeli "Güncelleme" damgası** → sekmeli kur tabloları → benzer haberler → hesaplayıcı + çevirici. `<title>` soru kalıbında. Finansal şema yok | `siteler/haberturk.md` Özet 1, §2 · [dolar](https://www.haberturk.com/ekonomi/piyasa/88-dolar), 2026-10-20 |
| Bursada Bugün · Bursa Saati · Ege | D | Başlıkta piyasa bandı (dolar, euro, altın, BIST; Bursada Bugün'de bitcoin). Ege'de sektör kategorileri: Tarım, Turizm, Enerji, İnşaat/Emlak, İş Dünyası, Otomobil | `bursada-bugun.md` §1, `bursa-saati.md` §1, `egede-son-soz.md` §5 |
| Hürriyet → Bigpara | İ | Piyasa verisi **ayrı markada**; serbest piyasa kurları, TCMB için ayrı sayfa; günlük/haftalık/aylık geçmiş + çevirici; veri sağlayıcı anılıyor; hisse verisi "15 dk gecikmeli", gecikmesiz veri üye girişli | `siteler/hurriyet.md` Özet 1, §2 (arama özeti, 2026-10-20) |
| Milliyet → Uzmanpara | İ | Aynı kalıp: canlı borsa, döviz, altın, değerli metaller ayrı markada | `siteler/milliyet.md` Özet 3 |
| FT | İ | Grafik türünü veri ilişkisine göre seçtiren "Visual Vocabulary" (9 sınıf: sapma, korelasyon, sıralama, dağılım, zaman içinde değişim, parça-bütün, büyüklük, mekânsal, akış). Poster/şablon tüm hakları saklı — **yalnız yöntem** | `siteler/ft.md` Özet 2 · [chart-doctor README](https://github.com/Financial-Times/chart-doctor/blob/main/visual-vocabulary/README.md), 2026-10-20 |
| Reuters | İ | Ödeme modeli profesyonel/B2B kitleye göre; BH'ye benzemez | `siteler/reuters.md` Özet 2 |

**Ortak ders.**
- Türk ekonomi sayfası iki katmanlı: **rakam arayan okur** (şerit → kalıcı
  enstrüman adresi) ve **haber okuru** (bölüm akışı). Kalıcı enstrüman adresi
  "dolar kaç TL" aramasına iniş sayfasıdır.
- Rakamın güveni **kaynak + zaman + gecikme** notundan gelir (Bigpara'nın
  "15 dk gecikmeli" notu; Habertürk enstrüman sayfasındaki saniyeli damga).
  Habertürk şeridinde zaman olmaması bunun tersi.
- Büyük gruplar veriyi ayrı markaya taşıyor (Bigpara, Uzmanpara); bu, üyelik
  ve veri lisansı gerektiren bir ölçek.

**Hangi koşulda işe yarıyor.** Saniyeli canlı veri ücretli veri sağlayıcı
ister; BH'nin kaynağı TCMB/EVDS bülteni (anahtarsız, iş günü ~15:30). Bülten
verisiyle kalıcı enstrüman sayfası yapılabilir, "canlı borsa" yapılamaz.
KAP listesi ve hisse tablosu veri lisansı ister → açık soru. Ayrı veri markası
yerel gazeteye taşınmaz.

**Bursa Hakimiyet'te durum.**
- Ekonomi teması kurulu (`icerik/temalar.py`, `parca/bolum/ekonomi.html`,
  URUN-PLANI §70 Paket E): `bas` yuvasında **PİYASA CETVELİ** (kalem · son ·
  değişim · alış · satış; renk yalnız değişim sütununda ve kuralı altta yazılı;
  veri bayatsa tablonun **üstünde** "GÜNCEL DEĞİL" + tarih; kaynağı olmayan
  kalem "–"; TCMB bülten tarihi/no + "Veri kaynakları" bağlantısı) ve
  **BURSA EKONOMİSİ** listesi (başlıkta Bursa/BTSO ya da ilçeye bağlı haber;
  seçim kuralı altta).
- Kaynak + zaman + bayatlık: BH bu konuda incelenen Habertürk şeridinden daha
  sıkı (`bayat veri tarihle gösterilir` kararı).
- Kalıcı enstrüman sayfası, kur geçmişi, çevirici, grafik: **kodda yok**
  (`canli-veri/doviz.py`, `piyasa.py` var; adres yok).

**Öneri.**
- Kalıcı enstrüman sayfaları (dolar, euro, gram altın; bülten verisi, geçmiş
  tablo, kaynak + zaman + bayatlık notu, benzer haberler) → P1 · M ·
  → `veri-entegrasyon-muhendisi` (geçmiş seri) + `backend-gelistirici`
  (adres/görünüm) + `seo-buyume-uzmani` (başlık kalıbı).
- Kur/enstrüman geçmişi için tek grafik; tür seçimi FT yöntemiyle ("zaman
  içinde değişim" → çizgi), "her grafik kendini anlatsın" kuralı → P2 · S ·
  → `web-tasarim-direktoru`.
- Bursa'ya özgü sektör kırılımı (Ege'nin sektör kategorileri gibi; Bursa için
  hangi sektörler) → P2 · S · → `haber-muduru`.
- KAP bildirimleri / hisse tablosu: veri kaynağı ve lisans açık soru →
  `veri-entegrasyon-muhendisi` + `hukuk-guvenlik-uyum-uzmani`; şimdilik önerilmez.

**Açık sorular.** FT ve Reuters ekonomi/piyasa sayfalarının düzeni ikincil
kaynakta bulunamadı. Hürriyet'in `/ekonomi` bölüm sayfası ölçülmedi.
Bursa'ya özgü ekonomi verisi (BTSO, ihracat) için izinli kaynak var mı →
`veri-entegrasyon-muhendisi`.
