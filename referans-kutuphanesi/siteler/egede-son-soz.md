# Ege'de Son Söz

- Adres: https://www.egedesonsoz.com/
- Katman: yerel (başka şehir — İzmir)
- Neden seçildi: büyükşehir statüsünde, çok ilçeli bir kentin yerel gazetesi; menüde **30 ilçe sayfası** ve ayrı "Yerel Yönetimler", "Yerel Politika" kategorileri var — ilçe içeriği ölçütüne en doğrudan uyan aday. Aday havuzu Similarweb benzer site listelerinden kuruldu ([kaynak](https://www.similarweb.com/website/egedesonsoz.com/competitors/), Eylül 2026 verisi, 2026-10-20); Konya (Merhaba Haber) ve Kayseri (Kayseri Olay) adaylarının anasayfası da okundu, ilçe/servis sayfası bu kadar ayrışmış değildi.
- İnceleme: 2026-10-20 · koşul: masaüstü 1440×900 / mobil 390×844 (DPR 3) başsız Chrome, User-Agent değiştirilmedi, çerez kabul edilmedi, önbellek kapalı · konum: Türkiye (yerel makine)
- İncelenen sayfalar: robots.txt, anasayfa, bölüm (`/yerel-yonetimler`), ilçe (`/bornova-haberleri`), haber detay ×2, nöbetçi eczane, sitemap dizini
- robots.txt (2026-10-20): Bursa Saati ile birebir aynı şablon — yapay zekâ ajanları `*` ile aynı grupta, `Disallow: /` yok; `/service/`, `/api`, `/arama/` vb. kapalı → otomatik erişim açık.
- Altyapı gözlemi: Bursa Saati ile aynı hazır haber platformu (`s.tblsm.com`, `*.teimg.com`). Aynı platformda iki sitenin farklı reklam kararları karşılaştırma için doğal bir kontrol sağlıyor (bkz. §9).

## Özet — en öğretici 3 çözüm
1. **İlçe sayfası her ilçe için, menüde alfabetik** — `/<ilçe>-haberleri` deseniyle 30 ilçe ([anasayfa](https://www.egedesonsoz.com/), 2026-10-20). Bornova sayfasında 79 haber adresinin 42'sinde ilçe adı geçiyor; 17'sinde "başkan/belediye/meclis" ([Bornova](https://www.egedesonsoz.com/bornova-haberleri), 2026-10-20). Neden işe yarıyor: ilçe okuru kendi sayfasını buluyor; ilçe belediyelerinin bülten akışı sayfayı dolu tutuyor. Koşul: ilçe sayfası belediye bülteniyle dolunca ilçe sayfası bir "belediye duyuru panosu"na dönüşebilir — masa ayrımı gerekir. BH'ye: kısmen (ilçe sayfası var; besleme dengesi `haber-muduru` kararı).
2. **İlçe adresli eczane sayfaları + yapısal veri** — il sayfasında 71 `Pharmacy` JSON-LD kaydı, 31 ilçe eczane adresi (`/izmir-<ilçe>-nobetci-eczaneler`) ([eczane](https://www.egedesonsoz.com/izmir-nobetci-eczaneler), 2026-10-20). BH'ye: evet.
3. **Reklamsız ilk ekran, başlık yukarıda** — detayda başlığın üst kenarı 160 px'te; künye şeridinde yayın zamanı, paylaşım sayısı, okuma süresi; sağda saat damgalı "Son Haberler" rayı ([detay 1](https://www.egedesonsoz.com/yamanlara-yeni-yasam-alani-semt-merkezi-ve-kutuphane), 2026-10-20). Aynı platformdaki Bursa Saati detayında başlık 573 px'te (iki üst reklam). Neden: aynı şablon, farklı reklam kararıyla ilk ekranın içeriği değişiyor. BH'ye: evet (ilke olarak: ilk ekranda başlık).

## 1. Anasayfa bilgi mimarisi
1440 px'te üstten: kırmızı başlık bandı (logo, ilçe adıyla hava, borsa, Günün Haberleri, Foto Galeri, Video, Yazarlar) → beyaz menü (Güncel, Ege, Yerel Yönetimler, Ekonomi, Politika, Spor, Magazin, Dünyadan, Sağlık, Röportajlar + açılır menü) → **4'lü görselli sürmanşet şeridi** → büyük slayt manşet + sağda iki büyük kart ([anasayfa](https://www.egedesonsoz.com/), 2026-10-20; ekran görüntüsü). Manşet tipi: sürmanşet + slayt (numaralı değil, çizgi göstergeli). İlk ekranda görünür, metni ≥ 25 karakter bağlantı: **8**. İlk ekranda reklam görülmedi. Sayfa yüksekliği 7.136 px.

## 2. Bölüm sayfası
`/yerel-yonetimler`: `BreadcrumbList`; 16 `h3` + 59 `h4` kart başlığı; **"Daha fazla göster"** düğmesi (JSON uç noktası `/service/…`, robots'ta kapalı — istek atılmadı) ([bölüm](https://www.egedesonsoz.com/yerel-yonetimler), 2026-10-20). Kademe ve ray: ölçülmedi.

## 3. Haber detay
- Gövde: 20 px / 30 px (1,5), Gibson; sütun 832 px, ilk uzun paragrafta **~94 karakter/satır** (alt sınır) ([detay 1](https://www.egedesonsoz.com/yamanlara-yeni-yasam-alani-semt-merkezi-ve-kutuphane), 2026-10-20, 1440 px). Başlık 60 px.
- Spot: var (`description` sınıfı, büyük punto). Künye şeridi: yayın zamanı · paylaşım sayısı · okuma süresi · paylaşım düğmeleri · A−/A+ · Google News simgesi.
- Güncelleme: JSON-LD `dateModified` yayından 2 dk sonra (08:41 → 08:43); sayfada görünür "güncellendi" ibaresi görülmedi.
- İlgili: "Bunlar da ilginizi çekebilir" bloğu; sağ rayda saat damgalı son haberler ([detay 2](https://www.egedesonsoz.com/bornovada-can-dostlara-sicak-yuva-2), 2026-10-20).
- Muhabir: JSON-LD `author`/`creator`/`editor` alanları var; sayfada gösterimi ölçülmedi.

## 4. Son dakika / canlı
`/sondakika-haberleri` sayfası ve detay rayında saat damgalı son haberler ([detay 1](https://www.egedesonsoz.com/yamanlara-yeni-yasam-alani-semt-merkezi-ve-kutuphane), 2026-10-20). Anasayfada son dakika şeridi: 1440 ilk ekranda görülmedi. Canlı blog: görülmedi. Göreli zaman: kullanılmıyor, mutlak saat (HH:MM).

## 5. Yerel ve servis içerikleri
- **İlçe:** 30 ilçe sayfası (menüde alfabetik); ayrıca "Ege" (bölge illeri), "Yerel Yönetimler", "Yerel Politika" kategorileri; sektör kategorileri: Tarım, Turizm, Enerji, İnşaat/Emlak, İş Dünyası, Otomobil ([anasayfa](https://www.egedesonsoz.com/), 2026-10-20).
- **Bornova sayfası** içeriği: §Özet 1'deki sayım. Sayfada görünür tarih HTML'de yok (tazelik ölçülmedi).
- **Servis:** nöbetçi eczane (il + 31 ilçe adresi), trafik yoğunluk haritası, hava durumu (başlıkta ilçe adıyla), Süper Lig puan durumu.
- Namaz vakitleri: menüde görülmedi (HTML'de 4 geçiş, sayfa doğrulanmadı).

## 6. Mobil davranış
390 px ilk ekran (ekran görüntüsü): kırmızı başlık (logo, arama, menü) → yatay kayan kategori menüsü → **2×2 görselli haber kartı** → slayt manşet başlangıcı; alt kenarda çerez bandı (105 px) ([anasayfa 390](https://www.egedesonsoz.com/), 2026-10-20). Ölçütün saydığı başlık: 8. Bildirim istemi yok; yapışkan başlık yok. Sayfa yüksekliği 10.031 px; yatay taşma yok.

## 7. Başarım
Tek ölçüm, 2026-10-20, Türkiye, başsız Chrome, çerez kabul edilmedi.
| sayfa | istek | aktarım | LCP | CLS |
|---|---|---|---|---|
| anasayfa 1440 | 79 | 5,08 MB | 860 ms (IMG) | 0,002 |
| anasayfa 390 | 72 | 5,01 MB | 840 ms | 0,000 |
| detay 1440 | 97 | 1,69 MB | 812 ms | 0,054 |

Anasayfa HTML 29.973 B sıkıştırılmış / 201.916 B açılmış. Anasayfada 110 `img`'nin 102'si `loading="lazy"`, 108'i `width/height` taşıyor. Aktarımın büyük kısmı görseller (`egedesonsozcom.teimg.com`, 32 istek).

## 8. SEO yapısı
- Detay JSON-LD: `NewsArticle` (`articleBody`, `keywords`, `wordCount`, `isAccessibleForFree`, `author`/`creator`/`editor`), `BreadcrumbList`, `WebPage`; her sayfada 62 `SiteNavigationElement`.
- Eczane sayfası: 71 `Pharmacy`.
- Sitemap: dizinde 32 alt harita — `sitemap-news.xml` + aylık `sitemap/sitemap-YYYY-MM.xml` ([sitemap.xml](https://www.egedesonsoz.com/sitemap.xml), 2026-10-20). Haber sitemap'inin içi açılmadı.
- AMP: `amphtml` görülmedi. Analitik: Google + Yandex Metrica.

## 9. Reklam
1440 ve 390 px ilk ekranda **reklam yuvası görülmedi** (ekran görüntüsü + seçici sayımı); sayfada reklam seçicisine uyan 1 öğe; HTML'de Google reklam etiketi yok. Detayda da ilk ekranda reklam görülmedi. "Resmi Reklamlar" kategorisi var. Aynı platformdaki [Bursa Saati](https://www.bursasaati.com.tr/) ilk ekranında 3 yuva + boş ayrılmış alan var (aynı gün) — fark platformdan değil yayıncı kararından.

## 10. Gelir ve okur ilişkisi
Ödeme duvarı yok (`isAccessibleForFree` True). Üyelik girişi, RSS, Google News simgesi detayda. Tarayıcı bildirimi istemi görülmedi. Yayın ilkeleri, topluluk kuralları, gizlilik sayfaları altbilgide. Yorum: ölçülmedi. BİK analitik / `ilan.gov.tr`: anasayfa HTML'inde ve ilk 14 istek alanında görülmedi.

## 11. Erişilebilirlik
`lang="tr-TR"`. "İçeriğe atla" bağlantısı bulunamadı; ilk odak logo bağlantısı. Anasayfada 110 `img`'nin hepsinde `alt` dolu. Odak görünürlüğü, kontrast: ölçülmedi.

## 12. Yapay zekâ kullanımı
Görülmedi (incelenen 7 sayfa).

## Ölçüm dökümü
| ölçü | değer | yöntem |
|---|---|---|
| anasayfa HTML | 29.973 B / 201.916 B | `curl --compressed -w %{size_download}` / disk |
| detay HTML | 32.830 B / 179.100 B | aynı |
| ilk ekran başlık | 8 (1440) · 8 (390) | CDP: görünür, metni ≥ 25 karakter `a` |
| LCP / CLS / istek / aktarım | tablo §7 | `PerformanceObserver`; CDP Network olayları |
| gövde tipografisi | 20/30 px, 832 px, ~94 kar/satır | `getComputedStyle` + `Range.getClientRects` |
| Bornova sayfası | 79 haber adresi; 42'sinde ilçe adı, 17'sinde başkan/belediye/meclis | ham HTML, adres slug'larında sözcük arama |
| istek sayısı (bu site) | 11 | robots, anasayfa, bölüm, ilçe, 2 detay, eczane, sitemap (`curl`) + 3 Chrome yüklemesi |
