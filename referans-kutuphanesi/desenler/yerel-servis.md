# Yerel ve servis içerikleri — siteler arası desenler

Son güncelleme: 2026-10-20 (sentez) · Kaynak siteler: Bursada Bugün, Bursa
Saati, Ege'de Son Söz, Özgür Kocaeli, Habertürk (doğrudan); Manchester Evening
News, Texas Tribune, Axios Local, BBC News (ikincil). Olay: ölçülmedi
(otomatik erişim yok).

Kanıt: **D** doğrudan (Türkiye, 2026-10-20) · **İ** ikincil. Yerel rakip
ölçüleri tek ölçüm; sıralama değildir.

## 1. İlçe / semt sayfası

| Site | K. | Çözüm | Kaynak |
|---|---|---|---|
| Bursada Bugün | D | "Bursa Bölge" açılır menüsünde 17 ilçe + Uludağ, `/bursa-<ilçe>-haberleri`. İnegöl sayfasında 55 bağlantı, tarihler **2026-01-26 → 2026-10-19** (~9 aylık pencere: ilçeye özgü akış seyrek) | `siteler/bursada-bugun.md` Özet 1, §5 · [İnegöl](https://www.bursadabugun.com/bursa-inegol-haberleri), 2026-10-20 |
| Ege'de Son Söz | D | Menüde alfabetik 30 ilçe, `/<ilçe>-haberleri`. Bornova'da 79 haberin 42'sinde ilçe adı, 17'sinde başkan/belediye/meclis — **belediye bülteni ağırlığı riski**. Ayrıca "Yerel Yönetimler", "Yerel Politika" kategorileri | `siteler/egede-son-soz.md` Özet 1, §5 · [Bornova](https://www.egedesonsoz.com/bornova-haberleri), 2026-10-20 |
| Bursa Saati · Özgür Kocaeli | D | İlçe sayfası menüde görülmedi; Özgür Kocaeli'de kategoriler il adlı (`kocaeli-ekonomi-haberleri`…) | `bursa-saati.md` §5, `ozgur-kocaeli.md` §5 |
| Habertürk | D | Yerel ayrı alt alan adında; anasayfanın en altında 10 kart | `siteler/haberturk.md` §5 |
| Manchester Evening News | İ | Semt markaları (My Bolton/Bury/Salford): ana sitede bölüm + kendi sosyal hesabı + kısa alan adı; ~6 muhabirle başladı (2020); 2026 durumu doğrulanmadı | `siteler/manchester-evening-news.md` Özet 1 (Press Gazette, 2020-03-03) |

## 2. Servis sayfaları

| Servis | Görülen | Kaynak |
|---|---|---|
| Nöbetçi eczane, ilçe adresli | Bursa Saati il + 18 ilçe adresi, `Pharmacy` ×32; Ege il + 31 ilçe adresi, `Pharmacy` ×71 | D · `bursa-saati.md` Özet 1 · [eczane](https://www.bursasaati.com.tr/bursa-nobetci-eczaneler); `egede-son-soz.md` Özet 2 · [eczane](https://www.egedesonsoz.com/izmir-nobetci-eczaneler), 2026-10-20 |
| Nöbetçi eczane, tek sayfa | Bursada Bugün: il geneli, telefon + "Haritada göster", `Service` + `City`, HTML 7.512 B sıkıştırılmış; Özgür Kocaeli: ilçe seçici (12 ilçe), `tel:` + koordinatlı yol tarifi | D · `bursada-bugun.md` Özet 3 · [eczane](https://www.bursadabugun.com/bursa-nobetci-eczaneler); `ozgur-kocaeli.md` Özet 2 · [eczane](https://www.ozgurkocaeli.com.tr/kocaeli-nobetci-eczaneler) |
| Trafik | Bursa Saati harita sağlayıcısının trafik katmanı (dış betik); Ege trafik yoğunluk haritası; Özgür Kocaeli trafik sayfası | D · [trafik](https://www.bursasaati.com.tr/bursa-trafik-durumu), 2026-10-20 |
| Kesinti | Bursada Bugün anasayfada ilçe ilçe elektrik kesintisi **galerileri** | D · `bursada-bugun.md` §5 |
| Şehir rehberi | Özgür Kocaeli 81 kategori (eczane, doktor, ATM …) | D · [rehber](https://www.ozgurkocaeli.com.tr/rehber) |
| Tarihli günlük servis haberi | Bursa Saati namaz, döviz, altın için günlük ayrı haber adresi; Habertürk `bilgi/` şablonunda deprem, akaryakıt, baraj, Resmi Gazete özeti | D · `bursa-saati.md` Özet 2; `haberturk.md` §5 |
| Hava | Ege başlıkta ilçe adıyla; Bursa Saati 81 il (platform modülü); Bursada Bugün `/bursa-hava-durumu` | D |
| Veri gezgini | Texas Tribune kamu maaşları, okul, yasama gezginleri (Django; bilgi edinme başvurusu, çeyreklik güncelleme) | İ · `texas-tribune.md` Özet 1 |
| İhbar hattı | Özgür Kocaeli (başlıkta ilk odak), Bursa Saati, Bursada Bugün WhatsApp hattı | D |

**Ortak ders.**
- Eczane servisi yerel sitelerde olgun ve aynı kalıpta: **kalıcı adres + ilçe
  kırılımı + `Pharmacy` yapısal veri + telefon + yol tarifi.**
- İlçe sayfası kolay, **dolu tutmak** zor: Bursada Bugün'de 9 aylık pencere,
  Ege'de belediye bülteni ağırlığı. İlçe sayfası masanın beslemesine bağlı.
- Servis verisi iki biçimde: kalıcı sayfa (eczane) ve tarihli günlük haber
  (namaz, akaryakıt). İkincisi arama trafiği içindir.

**Hangi koşulda işe yarıyor.** Eczane/namaz/hava hazır veriyle küçük masada
yürür. İlçe sayfası her ilçeden haftada birkaç haber çıkarabilen masayı ister;
MEN'in semt markası ~6 muhabirle kuruldu. Şehir rehberi (81 kategori) ve veri
gezgini sürekli bakım ister; bakılmazsa bayat veri olur.

**Bursa Hakimiyet'te durum.**
- `/ilceler` + `/ilce/<slug>` (17 ilçe), `kategori.html` şablonuyla; servis
  şeridi o ilçenin bugünkü nöbetçileri; hava ilçeye inmiyor (merkez verisi
  ilçede basılmaz) (`icerik/views.py` `ilce`, `_bolum_servisi` 464–476).
  İlçe sayfasında görüntü kuşağı yok (galeri/videonun ilçesi yok).
- `/nobetci-eczane` + `/nobetci-eczane/<ilçe>` kalıcı, veri yoksa da 200
  (`views.py` `nobetci_eczane`); `Pharmacy` JSON-LD (`icerik/eczane.py:229`);
  `tel:` + "Yol tarifi" (`parca/eczane_liste.html`); günlük eczane haberi
  ayrı komut (`eczane_haberi`, URUN-PLANI §41).
- Anasayfada ŞEHİR SERVİSLERİ (eczane, namaz, hava…); canlı veri: döviz,
  hava, namaz, eczane, piyasa, puan, vizyon (`canli-veri/`).
- Trafik, kesinti, şehir rehberi: **kodda yok.**
- İhbar hattı bağlantısı `href="#kunye"`, WhatsApp kanalı `href="#"`
  (`parca/ust_bant.html` 25, 30).
- İlçe sayfası tazeliği: **yerelde ölçülecek → `test-kalite-muhendisi`**
  (ilçe başına son 30 günde haber sayısı; en eski kalemin yaşı).

**Öneri.**
- İlçe sayfası tazelik ölçümü + besleme dengesi (belediye bülteni oranı)
  → P1 · S · → `test-kalite-muhendisi` (ölçüm) + `haber-muduru` (denge kuralı).
- Elektrik/su kesintisi kalıcı servis sayfası (eczane modeliyle; veri
  kaynağı ve kullanım koşulu açık soru) → P2 · M ·
  → `veri-entegrasyon-muhendisi` (kaynak) + `hukuk-guvenlik-uyum-uzmani`
  (kaynak koşulları).
- Trafik sayfası: dış harita betiği CSP ve "dış kaynak 0" ölçütüyle çelişir
  (URUN-PLANI §70) → şimdilik önerilmez.
- Şehir rehberi → P2 · L; bakım yükü nedeniyle önerilmez, kayıt.
- Periyodik türleri (namaz, döviz, hava) günlük haber olarak üretmek serbest,
  ama **konu saymak → BH için: reddedildi (kullanıcı kararı).**
- Vefat/anma ilanları (Özgür Kocaeli "Vefatlar") → **BH için: reddedildi
  (kullanıcı kararı).**

**Açık sorular.** Olay'ın ilçe/servis kalıbı (aynı okur) elle gözlem
gerektirir. Bursa'da kesinti verisinin kamuya açık, koşulları izinli bir
kaynağı var mı → `veri-entegrasyon-muhendisi`.
