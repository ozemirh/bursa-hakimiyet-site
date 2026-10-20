# Reklam yerleşimi — siteler arası desenler

Son güncelleme: 2026-10-20 (sentez) · Kaynak siteler: Bursada Bugün, Bursa
Saati, Ege'de Son Söz, Habertürk, Spiegel (doğrudan: ekran görüntüsü + DOM
seçici sayımı, çerez kabul edilmedi); Guardian, Reach/MEN, Axios Local,
Hürriyet (ikincil). Yerel rakip ölçüleri tek ölçüm, 2026-10-20, Türkiye.

| Site | K. | İlk ekran (1440) | Diğer | Kaynak |
|---|---|---|---|---|
| Bursada Bugün | D | **4 yuva**: sol/sağ dikey pano, sağ sütunda 300×250, manşet altı 970×90 | kendi reklam sunucusu + yerel ağ + Google; yapışkan reklam görülmedi; yerel kurum ilanları | `bursada-bugun.md` §9 · [anasayfa](https://www.bursadabugun.com/), 2026-10-20 |
| Bursa Saati | D | **3 yuva + 1 boş ayrılmış alan** (üst tam genişlik, menü altı tam genişlik, sağda `fixed` 160×600); 390'da ilk ekranda ~270 px boş ayrılmış alan | menüde **"Advertorial"** ve "Resmi Reklam" kategorileri; detayda başlık 573 px'te | `bursa-saati.md` §9, §6 · [anasayfa](https://www.bursasaati.com.tr/) |
| Ege'de Son Söz | D | **0 yuva** (1440 ve 390; detayda da) | aynı platformda Bursa Saati ile fark yayıncı kararından | `egede-son-soz.md` §9 · [anasayfa](https://www.egedesonsoz.com/) |
| Habertürk | D | anasayfa: 970×250 + iki yanda **sabit** 160×600 + sponsor logosu/bandı; detay: 4–5 yuva | gövde içi yuva "REKLAM" etiketli, **yeri önceden ayrılmış**; mobil 320×100; anasayfada 25 öğe; **kendini yenileyen yapışkan yuva** | `haberturk.md` §9 · [anasayfa](https://www.haberturk.com/) |
| Spiegel | D | rıza verilmediği için ölçülmedi (72 `data-advertisement` işareti) | **"pay or consent"** rıza katmanı (reklamla devam / ücretli reklamsız); `/tests/` kümelerinde etiketli sponsorlu kart | `spiegel.md` §9 · [/ausland/](https://www.spiegel.de/ausland/) |
| Özgür Kocaeli | D | ölçülmedi (tam ekran pencere) | anasayfada resmi ilan kaydırıcısı (18 bağlantı) | `ozgur-kocaeli.md` §9 |
| Guardian | İ | — | Mart 2025'ten "consent or pay": kişiselleştirilmemiş reklamlı aylık 5 £ "Ad-Lite" | `guardian.md` §9 (Press Gazette, 2025-03-14) |
| Reach / MEN | İ | — | yönetim reklam yoğunluğu eleştirisini kabul ediyor (doğrulanmadı); yeni platformla reklam kaynaklı kayma giderildi (şirket beyanı) | `manchester-evening-news.md` §7, §9 |
| Axios Local | İ | — | bülten içi **doğrudan satılan** yerel sponsorluk | `axios-local.md` Özet 3 |

**Ortak ders.**
- İlk ekrandaki yuva sayısı yayıncı kararı: aynı platformda 0 ile 3+1
  arasında (Ege ↔ Bursa Saati). Bedeli ilk ekran başlık sayısı ve detayda
  başlığın yeri (`haber-detay.md` §2).
- Kaymayı önleyen desen ucuz: **yeri önceden ayrılmış yuva** (Bursa Saati,
  Habertürk). Ayrılmamış yuva + ölçüsüz görsel CLS'yi yükseltiyor
  (`basarim.md`).
- Ücretli içerik ya ayrı kategoride (Bursa Saati) ya kart içinde etiketli
  (Spiegel) duruyor; ikisinde de okura ayrışıyor.
- Resmî ilan Türk sitelerinde reklamdan ayrı bir modül.

**Hangi koşulda.** Programatik reklam yoğunluğu sayfa görüntüleme başına geliri
artırır ama hızı ve okumayı düşürür (FT deneyi, `basarim.md`). Yerel
reklamvereni olan gazete için doğrudan satış (yerel kurum ilanı, bülten
sponsorluğu) daha az yuvayla gelir taşıyabilir (Axios, ikincil).

**Bursa Hakimiyet'te durum.**
- `taban.html`: her sayfanın üstünde 1100×150 / 970×250 / 728×90 şerit
  (≤ 600 px'te 44 px kutu, ölçü verilmez), iki yanda yapışkan 160×600
  (`site.css` 327, geniş ekranda görünür); anasayfada üç 300×250
  (manşet yanı, manşet altı, haber arası), detay rayında bir 300×250
  (`anasayfa.html` 64, 103, 198; `haber_detay.html:135`).
- Yuvalar **önceden ayrılmış** (`.reklam.tam{height:250px}`, `site.css` 334);
  site ölçümünde CLS ≤ 0,02 tavanı var.
- Gövde içi yuva yok; sponsorlu içerik kategorisi/etiketi kodda yok.
- Reklam anahtarı, yerel test hizmeti, demo ağı (URUN-PLANI §42, §65).
- İlk ekran yuva sayısı (1440/390): **yerelde ölçülecek → `test-kalite-muhendisi`**.

**Öneri.**
- İlk ekran yuva sayısı + başlık sayısı + H1 konumunu reklam-test açıkken
  ölç; detay sayfasında üst şeridin gövdeyi ilk ekrandan itip itmediğine bak
  → P1 · S · → `test-kalite-muhendisi`; karar → `web-tasarim-direktoru`.
- Sponsorlu içerik etiketleme kuralı (ayrı kategori ya da etiketli kart,
  haber akışından ayrışan) ilk ücretli içerik gelmeden → P2 · S ·
  → `haber-muduru` + `hukuk-guvenlik-uyum-uzmani`.
- Kendini yenileyen yapışkan yuva (Habertürk) → önerilmez (okuma ve ölçüm
  yükü); kayıt.
- AdSense / Google reklam alanları (Bursada Bugün, Habertürk) →
  **BH için: reddedildi (kullanıcı kararı; askıda).**
