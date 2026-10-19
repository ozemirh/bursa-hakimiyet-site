# Referans kütüphanesi — haber siteleri

19 Ekim 2026'da kuruldu. Sahibi: `haber-siteleri-arastirmacisi` (`.claude/agents/`).

Bu klasör, ekibin "başkaları bunu nasıl yapıyor" sorusunu **bellekten değil
kanıttan** cevaplaması için var. Claude ajanları ince ayarla eğitilmez; ajanın
uzmanlığı rol tanımı + bu kütüphaneden gelir. Kütüphane bir kez derin taramayla
dolduruldu, sonra elle tazelenir (`BULUT-GOREVI.md`, "tazele" kipi). Zamanlanmış
görev yoktur (EKIP.md değişmez kararı).

## Kim neyi okur

| Dosya | Okuyan | Ne zaman |
|---|---|---|
| `desenler/<konu>.md` | tüm ekip | bir bölüm/özellik tasarlanmadan önce |
| `karsilastirma.md` | `haber-sistemi-uzmani`, `haber-muduru` | önceliklendirirken |
| `siteler/<site>.md` | araştırmacı, `web-tasarim-direktoru` | bir desenin kaynağına inmek gerektiğinde |
| `SITELER.md` | araştırmacı | tarama/tazeleme öncesi |

## Klasör düzeni

```
README.md          bu dosya: yöntem, rubrik, kanıt kuralı, şablon
SITELER.md         site listesi, katman, seçilme gerekçesi, son inceleme
siteler/<site>.md  site başına çözümleme (aşağıdaki şablon)
desenler/<konu>.md siteler arası desen kataloğu
karsilastirma.md   Bursa Hakimiyet ↔ desen fark matrisi
BULUT-GOREVI.md    bulut oturumuna yapıştırılan görev metni
ham/               ekran görüntüsü, ham HTML, ölçüm dökümü — DEPOYA GİRMEZ
```

Dosya adları Türkçe, küçük harf, tireli, ASCII (`son-dakika.md`,
`manchester-evening-news.md`).

## Kanıt kuralı

1. Her iddia **URL + inceleme tarihi** taşır: `([kaynak](https://…), 2026-10-19)`.
2. Sayı varsa yöntemi yazılır: `curl -s -o /dev/null -w '%{size_download}'`,
   başsız Chrome `PerformanceObserver` LCP, JSON-LD `@type` listesi…
3. Açılıp bakılmamış bilgi **"doğrulanmadı"**, ölçülemeyen alan
   **"ölçülmedi"** yazar. Tahmin yazılmaz.
4. Görülen koşul yazılır: masaüstü 1440 px / mobil 390 px, çerez kabulü,
   bulunulan ülke (bulut ortamı genelde ABD'dedir — bölgesel sürüm farkı olabilir).

## Sınırlar

- **Kopyalama yok:** başlık, metin, fotoğraf, logo kütüphaneye girmez. Alıntı
  ≤ 25 kelime, yalnız bir çözümü tarif etmek için.
- **Depo herkese açık:** ekran görüntüsü ve ham HTML yalnız `ham/` altına
  (`.gitignore`'da).
- **Nazik tarama:** `robots.txt`'e uy · alan adı başına ≤ 1 istek / 3 sn ·
  site başına ≤ ~15 sayfa · ödeme duvarı, giriş, CAPTCHA aşılmaz.
- **Kullanım koşulları:** otomatik erişimi açıkça yasaklayan sitede `curl`
  yerine yalnız WebFetch/WebSearch ile birkaç sayfaya bakılır; bu SITELER.md'de
  not edilir.
- **Rakipler hakkında dil:** yerel rakipler (Olay, Bursada Bugün…) için
  yalnız gözlenen çözüm ve ölçü yazılır; nitelendirme, küçümseme, tahmin yok.
- **Kişisel veri yok:** muhabir adı, yorum, okur bilgisi kütüphaneye girmez.
- **Önerilerde** EKIP.md'deki değişmez kararlar ve reddedilenler süzgeçtir;
  desen yaygın olsa bile "BH için: reddedildi" diye işaretlenir.

## Rubrik — her site dosyası bu başlıklarla

Her başlık ya kanıtla doludur ya "ölçülmedi" / "yok" yazar. Boş başlık olmaz.

1. **Anasayfa bilgi mimarisi** — üstten aşağı blok sırası; manşet tipi
   (tek / çoklu / sürmanşet); yoğunluk (ilk ekranda kaç başlık, 1440 px).
2. **Bölüm sayfası** — kademe (manşet → orta → akış), ray var mı, sayfalama.
3. **Haber detay** — gövde punto / satır uzunluğu (karakter) / satır aralığı;
   spot; kaynak ve muhabir gösterimi; düzeltme/güncelleme notu; ilgili haber
   ve okumaya devam bloğu; paylaşım.
4. **Son dakika / canlı** — anasayfada nasıl duruyor; canlı blog biçimi;
   göreli zaman kullanımı.
5. **Yerel ve servis içerikleri** — ilçe/semt sayfası, hava, eczane, namaz,
   trafik, ulaşım, ölüm/düğün değil hizmet; yerelin ulusalla dengesi.
6. **Mobil davranış** — 390 px'te ilk ekran, menü, yapışkan öğeler, reklam.
7. **Başarım** — HTML bayt, toplam istek, LCP, CLS (ölçülebildiyse; yöntemle).
8. **SEO yapısı** — JSON-LD türleri (`NewsArticle`, `BreadcrumbList`,
   `LiveBlogPosting`…), kanonik, sitemap düzeni (haber sitemap'i var mı), AMP.
9. **Reklam** — yerleşim, ilk ekrandaki yuva sayısı, yapışkan/araya giren.
10. **Gelir ve okur ilişkisi** — abonelik/ödeme duvarı tipi, bülten, bildirim,
    üyelik, yorum.
11. **Erişilebilirlik** — odak görünürlüğü, atla bağlantısı, kontrast kabaca,
    `lang`, görsel alt metinleri.
12. **Yapay zekâ kullanımı** — özet, seslendirme, öneri; okura nasıl
    işaretleniyor (BH'de okura etiket YOK — kullanıcı kararı; yalnız kayıt için).

## Site dosyası şablonu

```markdown
# <Site adı>

- Adres: https://…
- Katman: yerel | ulusal | global
- Neden seçildi: <tek cümle>
- İnceleme: 2026-10-DD · koşul: masaüstü 1440 / mobil 390 · konum: <ülke>
- İncelenen sayfalar: anasayfa, <bölüm>, <haber detay> ×2, <canlı/özel>

## Özet — en öğretici 3 çözüm
1. <çözüm> — neden işe yarıyor — BH'ye taşınabilir mi (evet/kısmen/hayır + neden)

## 1. Anasayfa bilgi mimarisi
…
## 12. Yapay zekâ kullanımı
…

## Ölçüm dökümü
| ölçü | değer | yöntem |
```

## Desen dosyası şablonu

```markdown
# <Konu> — siteler arası desenler

Son güncelleme: 2026-10-DD · Kaynak siteler: <liste>

| Site | Çözüm (kanıtlı, kısa) |
|---|---|

**Ortak ders:** …
**Hangi koşulda işe yarıyor:** (masa büyüklüğü, gelir modeli, yerel/ulusal)
**Bursa Hakimiyet'te durum:** <URUN-PLANI §/şablon kanıtıyla>
**Öneri:** P0/P1/P2 · emek S/M/L · → <sahip ajan>  (ya da "reddedildi — kullanıcı kararı")
```
