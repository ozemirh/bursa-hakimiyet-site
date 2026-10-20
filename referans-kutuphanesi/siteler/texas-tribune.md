# The Texas Tribune

> **İkincil kaynak — otomatik erişim durduruldu (hukuk teyidi bekliyor).**
> robots.txt açık (yalnız bir piksel parametresi kapalı). Ancak kullanım
> koşullarının "Use Restrictions" maddesi hizmeti **yalnız kişisel kullanıma**
> ayırıyor ve **ticari girişimle bağlantılı kullanımı** onaysız yasaklıyor
> ([Terms of Service](https://www.texastribune.org/terms-of-service/), 2026-10-20).
> README "ticari kullanımı yasaklayan siteye istek atılmaz" dediği için
> robots.txt ve koşullar sayfasından sonra **başka istek atılmadı**.
> → `hukuk-guvenlik-uyum-uzmani`: bu madde README kapsamına giriyor mu?
> (Aynı tip "kişisel kullanım" maddesi açık listedeki başka sitelerde de olabilir.)

- Adres: https://www.texastribune.org
- Katman: global listede **bölgesel** (Teksas eyaleti; kâr amacı gütmeyen)
- Neden seçildi: açıklayıcı/veri haberi, üyelik modeli, ücretsiz yeniden yayın
- İnceleme: 2026-10-20 · koşul: robots.txt + koşullar sayfası (curl, varsayılan UA, Türkiye) + üçüncü taraf kaynaklar
- İncelenen sayfalar: yok (bkz. üst not)

## Özet — en öğretici 3 çözüm
1. **Kalıcı veri "explorer"ları — kamu verisi aranabilir ürüne dönüşüyor.** Kamu maaşları gezgini (300 binden fazla kamu çalışanı, eyalet ajanslarından bilgi edinme başvurusuyla alınan veri, standartlaştırma hattı, çeyreklik güncelleme), okul gezgini, yasama rehberi. Ekip bunları **Django** ile kurdu ([DjangoCon US 2015 konuşma özeti](https://av.tib.eu/media/32792); [Wisconsin Üniv. vaka çalışması](https://ethics.sjmc.wisc.edu/2021/04/19/local-news-now-case-study-texas-tribune), 2021-04-19; erişim 2026-10-20). — BH'ye: **kısmen**; BH de Django. Ama veri hattı ve bilgi edinme rutini emek ister (masa ≥1 veri muhabiri). Bayat veri kuralı (bellek: "son gün tarih+uyarıyla gösterilir") burada da geçerli.
2. **Ücretsiz yeniden yayın + kanonik adres ve takip pikseli şartı.** Haberler Creative Commons lisansıyla ücretsiz yeniden yayımlanabiliyor; şart: yönergeye uymak, kanonik adresi ve sayım pikselini kullanmak (arama özeti, sayfa açılmadı). robots.txt'teki `Disallow: /?republication-pixel=` satırı piksel mekanizmasının varlığını doğruluyor ([robots.txt](https://www.texastribune.org/robots.txt), 2026-10-20). Amaç: yerel yayınlar eyalet meclisini Tribune'den alsın, kendi topluluklarına odaklansın. — **hayır/kısmen**; BH ticari bir gazete, ölçek ve ajans ilişkisi farklı.
3. **Gelir çeşitliliği: üyelik + büyük bağış + kurumsal sponsorluk + etkinlik (festival).** 2017'de 62 etkinlik; 2018 için etkinlik geliri 2 milyon $ bekleniyordu ([CJR](https://www.cjr.org/united_states_project/texas-tribune-strategic-plan.php), 2018-09-05; erişim 2026-10-20). — **kısmen**; etkinlik/sponsorluk yerel gazeteye taşınabilir, bağış modeli taşınmaz (ticari şirket).

## 1. Anasayfa bilgi mimarisi
Ölçülmedi (otomatik erişim durduruldu).

## 2. Bölüm sayfası
Ölçülmedi.

## 3. Haber detay
- Sayfa ölçülmedi.
- Yeniden yayın yönergesi haber altında duruyor (arama özetleri; doğrulanmadı).

## 4. Son dakika / canlı
Ölçülmedi.

## 5. Yerel ve servis içerikleri
- Okurların %72'si Teksas'ta; en büyük kadro Austin'de (eyalet meclisi yakınında yirmiden fazla gazeteci), bölgelerde muhabirler var ([KSAT'ta yeniden yayımlanan Tribune yazısı](https://www.ksat.com/news/texas/2025/05/08/you-spoke-we-listened-together-we-make-texas-stronger/), 2025-05-08; erişim 2026-10-20).
- Yeni gelenlere yönelik rehber ve seçim rehberleri gibi **servis/açıklayıcı projeler** ([vaka çalışması](https://ethics.sjmc.wisc.edu/2021/04/19/local-news-now-case-study-texas-tribune), 2021-04-19).
- Ocak 2025: etkinliklere ağırlık ve hizmet alamayan topluluklarda yerel haber odaları kurma planı ([A Media Operator](https://www.amediaoperator.com/news/the-texas-tribune-turns-to-irl-events-local-newsrooms-to-reach-new-readers/), 2025-01-09; yalnız ücretsiz önizleme okundu).

## 6. Mobil davranış
Ölçülmedi.

## 7. Başarım
Ölçülmedi (otomatik erişim durduruldu; PSI anahtarsız API 2026-10-20'de HTTP 429).

## 8. SEO yapısı
- robots.txt iki sitemap ilan ediyor: `/sitemap.xml` ve **`/news-sitemap.xml`** (haber sitemap'i) ([robots.txt](https://www.texastribune.org/robots.txt), 2026-10-20).
- robots.txt'teki "YOAST BLOCK" yorumu WordPress + Yoast SEO kullanımına işaret ediyor (çıkarım; CMS doğrulanmadı). Veri gezginleri ayrı Django uygulamaları (bkz. Özet 1).
- JSON-LD, kanonik, AMP: ölçülmedi.

## 9. Reklam
Ölçülmedi. Gelirde kurumsal sponsorluk önemli; 2023'teki ilk işten çıkarmalar kamu kurumlarının sponsorluğu çekmesiyle ilişkilendirildi ([Nieman Lab](https://www.niemanlab.org/2023/08/the-texas-tribunes-first-ever-layoffs-worry-the-news-industry/), arama özeti, açılmadı).

## 10. Gelir ve okur ilişkisi
- Kâr amacı gütmeyen; okurların ~%90'ı bunu biliyor; 10 günlük bahar üyelik kampanyası, hedef 500 yeni üye; aylık bağış teşvik ediliyor; günlük bülten "The Brief"; yıllık festival (TribFest) ([KSAT yeniden yayını](https://www.ksat.com/news/texas/2025/05/08/you-spoke-we-listened-together-we-make-texas-stronger/), 2025-05-08).
- Okur anketi: okurların %72'si Tribune kapanırsa başka yerde bulamayacakları bir kaynağı kaybedeceğini söylüyor (aynı kaynak — kurumun kendi bağış çağrısı, buna göre okunmalı).
- 2018 stratejik planı: üyeliği ikiye katlama, gelir 9 milyon $ beklentisi, 2012'den beri kârlılık ([CJR](https://www.cjr.org/united_states_project/texas-tribune-strategic-plan.php), 2018-09-05).
- Ödeme duvarı: yok (haberler ücretsiz; arama özetleri ve kurumun beyanı).

## 11. Erişilebilirlik
Ölçülmedi.

## 12. Yapay zekâ kullanımı
- Tribune, model eğitimi için tarama yapan bazı YZ araçlarını vaka bazında engelleyebileceğini açıklamış (arama özeti; kurumun kendi sayfası açılmadı — doğrulanmadı). robots.txt'te 2026-10-20 itibarıyla YZ tarayıcısına özel kural yok.
- Okura işaretleme: ölçülmedi.

## Ölçüm dökümü
| ölçü | değer | yöntem |
|---|---|---|
| robots.txt | 256 B, 200; yalnız `/?republication-pixel=` kapalı | `curl`, 2026-10-20, Türkiye |
| Koşullar sayfası | 246.783 B, 200 | `curl`; "Use Restrictions" maddesi okundu |
| Haber sitemap'i | `/news-sitemap.xml` ilan edilmiş | robots.txt |
| Başarım | ölçülmedi | erişim durduruldu; PSI HTTP 429 |

İstek sayısı (www.texastribune.org): **2** (robots.txt + kullanım koşulları).
