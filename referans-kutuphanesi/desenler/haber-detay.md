# Haber detay — siteler arası desenler

Son güncelleme: 2026-10-20 (sentez; tohum 2026-10-19 korundu) · Kaynak siteler:
Bursada Bugün, Bursa Saati, Ege'de Son Söz, Özgür Kocaeli, Habertürk, Spiegel
(doğrudan); Reuters, Guardian, Axios Local (ikincil); NYT, BBC, Guardian
tipografisi (eski kayıt).

Kanıt: **D** doğrudan (başsız Chrome `getComputedStyle`, 1440 px, Türkiye) ·
**İ** ikincil · **E** eski kayıt, doğrulanmadı. Yerel rakip ölçüleri tek
ölçüm, 2026-10-20.

## 1. Gövde tipografisi

| Site | K. | Punto / satır aralığı | Sütun | Karakter/satır | Kaynak |
|---|---|---|---|---|---|
| Spiegel | D | 20/30 px (1,5) serif · mobil 18/27 | 624 px | ~60 · mobil ~38 | `siteler/spiegel.md` §3 · [haber 1](https://www.spiegel.de/ausland/mallorca-hoechste-sturmwarnung-fuer-baleareninsel-ausgerufen-a-e4318c01-6ad7-4e03-8859-8482b32fde6c) |
| Habertürk | D | 16/24 px · mobil aynı | 514 px · mobil 350 | ~66 · mobil ~45 | `siteler/haberturk.md` §3 · [HD1](https://www.haberturk.com/ekonomi/fon-yasasi-teklifi-bugun-tbmm-genel-kurulu-nda-3920983) |
| Bursa Saati | D | 20/30 px (1,5) | 685 px | ~77 (alt sınır) | `siteler/bursa-saati.md` §3 · [detay 1](https://www.bursasaati.com.tr/bursada-dev-karincayiyenin-ozel-menusu-dana-yureginden-muza-kadar-her-sey-var) |
| Özgür Kocaeli | D | 23,1/32,2 px (1,39) | 970 px | ~77 (alt sınır) | `siteler/ozgur-kocaeli.md` §3 · [detay 1](https://www.ozgurkocaeli.com.tr/haber/29013193/kocaelide-104-saglik-yatirimi-tamam-saglik-icin-dev-yatirim-listesi-ortaya-cikti) |
| Bursada Bugün | D | 20/30 px (1,5) | 970 px | ~84 (alt sınır) | `siteler/bursada-bugun.md` §3 · [detay 1](https://www.bursadabugun.com/haber/bursa-hayvanat-bahcesi-nde-dev-karincayiyenin-ozel-menusu-40-dakikada-hazirlaniyor-1957734.html) |
| Ege'de Son Söz | D | 20/30 px (1,5) | 832 px | ~94 (alt sınır) | `siteler/egede-son-soz.md` §3 · [detay 1](https://www.egedesonsoz.com/yamanlara-yeni-yasam-alani-semt-merkezi-ve-kutuphane) |
| NYT · BBC · Guardian | E | 20 · 19 · 17 px | — | — | tohum (`site.css` yorumu, 29 Ağustos 2026) — **doğrulanmadı (eski kayıt)**; bu taramada ikincil kaynakta da bulunamadı (`nyt.md` §3) |

Yöntem farkı: Spiegel metin ÷ satır sayısı; Habertürk `canvas.measureText`;
yerel siteler ilk uzun paragrafta `Range.getClientRects` (son satır kısmi,
alt sınır). Sayılar yaklaşık karşılaştırılabilir.

## 2. Başlık bloğu ve künye

| Öğe | Görülen | Kaynak (2026-10-20) |
|---|---|---|
| Yayın + **güncelleme** zamanı ayrı | Bursada Bugün ("Son Güncellenme"), Habertürk ("Giriş"/"Güncelleme", `<time>`) | D · `bursada-bugun.md` §3, `haberturk.md` §3 |
| Okuma süresi | Bursa Saati, Ege | D · `bursa-saati.md` §3, `egede-son-soz.md` §3 |
| A−/A+ punto | Bursada Bugün, Bursa Saati, Ege, Habertürk | D · aynı dosyalar §3 |
| Paylaşım (WhatsApp dahil) | Bursada Bugün, Bursa Saati, Ege, Habertürk (UTM'li), Spiegel (yapışkan çubuk) | D · aynı dosyalar §3 |
| Google "tercih edilen kaynak" | Habertürk (bilgi satırı altı), Spiegel, Özgür Kocaeli (tam ekran pencere) | D · `haberturk.md` §10, `spiegel.md` §3, `ozgur-kocaeli.md` Özet 1 |
| H1'in üst kenarı (1440) | Ege 160 px · Habertürk 539 px (gövde 1.268 px, ilk ekran altında) · Bursa Saati 573 px | D · `egede-son-soz.md` Özet 3, `haberturk.md` §3, `bursa-saati.md` §3 |

## 3. Kaynak, muhabir, düzeltme

| Öğe | Görülen | Kaynak |
|---|---|---|
| Kaynak satırı | Bursa Saati gövde sonu "Kaynak: <ajans>"; Bursada Bugün künyede ajans; Habertürk kaynak simgesi + ad; Spiegel gövde sonu ajans kodu + **ayrı fotoğraf kredisi** | D · ilgili dosyalar §3 |
| Muhabir | Özgür Kocaeli fotoğraflı yazar satırı; Spiegel ajans haberinde `author` = kurum | D · `ozgur-kocaeli.md` §3, `spiegel.md` §3 |
| Görünür düzeltme notu | **Hiçbir doğrudan örnekte görülmedi** | D · altı site §3 |
| Okur hata bildirimi | Spiegel sayfa sonunda "redaksiyon hatası bildir" katmanı | D · `spiegel.md` §3 |
| Hata kalır, düzeltme ayrıca | Reuters (2011 kuralı, el kitabı) | İ · `reuters.md` Özet 1 |

## 4. Okumaya devam, ilgili, yorum, reklam

| Öğe | Görülen | Kaynak |
|---|---|---|
| Gövde içi ilgili kutusu | Spiegel, gövdenin 6. öğesinden sonra | D · `spiegel.md` §3 |
| Sonda ilgili blok | Bursa Saati, Ege "Bunlar da ilginizi çekebilir"; Spiegel öneri motoru + yedek liste | D |
| Sonsuz akış (sıradaki haber aynı sayfada) | Habertürk (1 → 2 `article` ölçüldü; uç bota kapalı), Özgür Kocaeli (betikte; kaydırarak doğrulanmadı); NTV robots'ta `/api/next-news` (davranış doğrulanmadı) | D · `haberturk.md` Özet 3, `ozgur-kocaeli.md` §3; `ntv.md` Özet 3 |
| Yorum | Özgür Kocaeli var (topluluk kuralları + ajans haberine dair uyarı); Habertürk ve Spiegel'de yok | D |
| Gövde içi reklam | Habertürk "REKLAM" etiketli, yeri önceden ayrılmış (CLS 0,013) | D · `haberturk.md` §9 |
| Kısa yazı biçimi | Axios "Smart Brevity": kalın ara etiketler + maddeler | İ · `axios-local.md` Özet 2 |

**Ortak ders.**
- Türk sitelerinde künye satırı standart: zaman + kaynak + paylaşım + punto
  düğmesi. Güncelleme zamanı iki sitede **ayrı** gösteriliyor.
- Düzeltme notu Türk örneklerinde görünmüyor; görülen tek okur yolu Spiegel'in
  hata bildirimi. Bu bir boşluk; güven getirisi için fırsat (Reuters, ikincil).
- İlk ekranda başlığın yerini reklam belirliyor (Ege 160 px ↔ Bursa Saati 573
  px, aynı platform).
- Satır uzunluğu yerel sitelerde rahat okuma bandının (60–75) üstünde
  (77–94); Spiegel ve Habertürk bandın içinde.

**Hangi koşulda işe yarıyor.** Sonsuz akış sayfa başına gösterimi artırır ama
JS, ölçüm ve tarama (uçları bota kapatmak) yükü getirir; büyük ulusal masaya
göre. Sunucu render + küçük masa için "ilgili haber" bloğu daha ucuz
(`haberturk.md` Özet 3). Hata bildirimi, gelen bildirimi okuyacak bir kişi
gerektirir.

**Bursa Hakimiyet'te durum** (`uygulama/sablonlar/haber_detay.html`).
- Sıra: kırıntı (ilçe dahil) → bölüm rozeti → H1 → ikinci başlık → spot →
  künye (imza · yayın · güncelleme yalnız ≥ 1 dk sonraysa · okuma süresi ·
  BAĞLANTIYI KOPYALA · A−/A+ · YAZDIR) → ana görsel (srcset, öncelikli) →
  seslendirme → gövde → gömülü kartlar → **KAYNAK bölmesi** → etiketler
  (bağlantısız) → konunun akışı → İLGİLİ HABERLER; rayda son dakika, 300×250,
  en çok okunanlar, ilçe haberleri (satır 19–158).
- Gövde 18 px / 1,66, `max-width: 38em` (`site.css` 1990, 2627). Tohumdaki
  "68ch" Paket L1'de `em`'e çevrildi (URUN-PLANI §70); gerçek karakter/satır
  **yerelde ölçülecek → `test-kalite-muhendisi`**.
- **Sosyal paylaşım düğmesi yok** (yalnız bağlantı kopyala).
- **Görünür düzeltme notu yok**; menüdeki "Düzeltme ve cevap" ve "Yayın
  ilkeleri" bağlantıları `href="#"` (`parca/kategori_bandi.html` 107–108).
  Cevap/düzeltme modeli DEGERLENDIRME-2026-10 Aşama 4'te "kesim öncesi şart".
- Gövde içi reklam yuvası yok; gövde içi ilgili kutusu yok.
- H1'in ilk ekrandaki yeri: üstte her sayfada 250 px'lik reklam şeridi var
  (`taban.html` 148, `site.css` 334) → **yerelde ölçülecek →
  `test-kalite-muhendisi`**.

**Öneri.**
- Görünür düzeltme/cevap notu + "Düzeltme ve cevap" sayfası → P0 · M ·
  → `full-stack-gelistirici` + `haber-muduru` (yasal kısmı →
  `hukuk-guvenlik-uyum-uzmani`).
- Paylaşım düğmeleri (WhatsApp, X, Facebook; betiksiz düz bağlantı, dış betik
  yok) → P1 · S · → `frontend-gelistirici`.
- İlk ekranda H1 + spot + gövde başlangıcı ölçümü (1440/390, reklam
  açık/kapalı) → P1 · S · → `test-kalite-muhendisi`; sonuca göre şerit kararı
  → `web-tasarim-direktoru`.
- Gövde içi tek ilgili haber kutusu (Spiegel) → P2 · S · → `frontend-gelistirici`.
- Okur hata bildirimi (Spiegel) → P2 · M · → `full-stack-gelistirici`
  (form verisi KVKK → `hukuk-guvenlik-uyum-uzmani`).
- Sonsuz akış → şimdilik önerilmez (yukarıdaki koşul); ilgili haber bloğu
  zaten var.
