# Dışa aktarım — canlı siteden arşiv taraması

Yeni site için eski veritabanına erişim olmadığından, `bursahakimiyet.com.tr`
üzerindeki tüm haber arşivi canlı siteden taranıp yerel diske yapılandırılmış
JSON + görsel olarak indiriliyor. **Tek seferlik veri taşıma işi.**

Bu klasör tasarım demolarından ve `arac/` klasöründeki yapay zekâ editöründen
bağımsızdır; `arac/ayiklayici.py` dosyasını yalnızca salt-okunur kullanır.

---

## Başka bir bilgisayarda çalıştırma

Tarama saatler sürdüğü için sürekli açık kalabilen bir makinede çalıştırılır.

### Gerekenler

| | |
|---|---|
| Python | 3.10 veya üstü |
| Paket | **yok** — saf standart kütüphane |
| Disk | **~130 GB boş** (aşağıya bakın) |
| RAM | ~2 GB boş |
| Süre | 24–36 saat (bağlantı hızına göre) |

### Adımlar

```powershell
git clone https://github.com/ozemirh/bursa-hakimiyet-site.git
cd bursa-hakimiyet-site
.\disa-aktarim\calistir.ps1
```

Betik "bu sistemde komut dosyası çalıştırılması devre dışı" hatası verirse
(yeni kurulmuş Windows'ta olağan), ilkeyi kalıcı değiştirmeden:

```powershell
powershell -ExecutionPolicy Bypass -File .\disa-aktarim\calistir.ps1
```

Varsayılan çıktı kökü `D:\bursa-hakimiyet-arsiv`. Başka bir sürücü için:

```powershell
.\disa-aktarim\calistir.ps1 -Kok E:\arsiv
```

`calistir.ps1` üç işi üstlenir: makineyi uyanık tutar, diskte yer var mı bakar,
koşu düşerse 60 saniye sonra kaldığı yerden yeniden başlatır.

> **Kapak ayarı.** Betik sistemi uyanık tutar ama **kapağı kapatmak** yine
> uyutabilir. Denetim Masası → Güç Seçenekleri → "Kapağı kapatmanın yapacağı
> işlem" → **Hiçbir şey**. Ya da betiği `-UykuAyariniYap` ile çalıştırın
> (yönetici PowerShell ister).

### Yarıda kesme ve devam

Ctrl+C ile güvenle durdurulur. Tekrar çalıştırınca kaldığı yerden devam eder —
indirilmiş haberler `veri/<YIL-AY>/<id>.json` dosyasının varlığına bakılarak
atlanır. İlerleme `ilerleme.json` dosyasından okunur.

---

## Yarım kalan taramayı başka makineye devretme

Taramanın bir kısmı bir makinede yapıldıysa, o ilerlemeyi taşıyıp kaldığı
yerden devam edebilirsiniz. **Eski makinede:**

```powershell
.\disa-aktarim\paketle.ps1
```

Arşivi masaüstünde tek bir `.tar.gz` dosyasına toplar ve yanına SHA256 damgası
yazar. 92 bin küçük dosyayı USB'ye tek tek kopyalamak saatler sürer; tek paket
saniyeler.

> Paketlemeden önce taramayı durdurun — çalışırken paketlenirse yarım yazılmış
> dosyalar pakete girebilir. Betik açık bir Python süreci görürse uyarır.

**Yeni makinede:**

```powershell
tar -xzf bursa-arsiv-devir.tar.gz -C D:\
.\disa-aktarim\calistir.ps1
```

İlk turda `atlanan` sayısı devredilen haber sayısına eşit olmalı ve
`tamamlanan` sıfırdan başlamalı. Eşitse devir tamamdır. Başka bir sürücüye
açtıysanız `-Kok` ile yolu verin.

Damgayı doğrulamak için (USB aktarımı sessizce bozulabilir):

```powershell
(Get-FileHash bursa-arsiv-devir.tar.gz -Algorithm SHA256).Hash
Get-Content bursa-arsiv-devir.tar.gz.sha256
```

---

## Tarama bu makinede neden yavaş?

```powershell
.\disa-aktarim\tani.ps1
```

Hiçbir şeyi değiştirmez, taramayı başlatmaz — yedi şeyi ölçüp yazar: log'daki
gerçek hız, güç durumu, hedef diskin türü, antivirüs, ağ/DNS, gerçek sayfa ve
görsel indirme süresi, küçük dosya yazma hızı. **İki makinede de çalıştırıp
çıktıyı yan yana koyun.**

İşin doğası gereği **CPU hiçbir şeyi hızlandırmaz.** On iş parçacığı var ve her
sayfa/görsel için ayrı bir TLS bağlantısı açılıyor; hız kabaca

```
hız ≈ 10 / (sayfa süresi + görsel süresi × 3)
```

Ölçüm (25 Ağustos 2026, bu laptop): sayfa 0,62 sn + görsel 0,26 sn × ~3 →
öngörülen 7,1 url/sn, gerçekleşen **6,3 url/sn**. Yani süreyi belirleyen tek
şey **bağlantı gecikmesi**. Daha güçlü işlemci, daha çok RAM fark etmez;
Wi-Fi yerine kablo, VPN'i kapatmak, antivirüsün klasörü taramasını durdurmak
eder.

---

## İçerik aileleri — ÖNEMLİ

26 Ağustos 2026'da bulundu: tarayıcı uzun süre sitemap indeksindeki **beş içerik
ailesinden yalnızca birini** alıyordu. Süzgeç `news_` ile sınırlıydı, diğer dört
ailenin göçte kaynağı yoktu.

| Aile | `--aile` | Sitemap'te | Panelde | Adres deseni |
|---|---|---|---|---|
| Haber | `haber` *(varsayılan)* | 556.824 | 1.044.757 | `/{kategori}/{slug}-{id}` |
| Video | `video` | 32.006 | 49.164 | `/videolar/{kategori}-{katid}/{slug}-{id}` |
| Köşe yazısı | `kose` | 6.903 | 24.111 | `/yazarlar/{yazar}-{yid}/{slug}-{id}` |
| Foto galeri | `galeri` | 4.042 | 8.815 | `/galeriler/{kategori}-{katid}/{slug}-{id}` |
| Yazar sayfası | `yazar` | 18 | 71 | `/yazarlar/{slug}-{id}` |

**Sitemap sayıları panel sayılarından düşük.** Sitemap yalnızca yayında olan ve
görece yeni içeriği listeliyor; aradaki fark kazımayla kurtarılamaz, sağlayıcıdan
veritabanı dökümü ister.

### Çalıştırma

Her aile kendi dosyalarına yazar, birbirini etkilemez:

```
python site_arsivleyici.py                 # haber (eskisiyle birebir aynı)
python site_arsivleyici.py --aile kose
python site_arsivleyici.py --aile video
python site_arsivleyici.py --aile galeri
python site_arsivleyici.py --aile yazar
```

`haber` ailesinin dosya yolları **hiç değişmedi** — süren bir tarama varken
diğer aileleri başlatmak güvenlidir:

| Aile | Url listesi | Veri | İlerleme |
|---|---|---|---|
| `haber` | `tum-urller.jsonl` | `veri/` | `ilerleme.json` |
| diğerleri | `tum-urller-<aile>.jsonl` | `veri-<aile>/` | `ilerleme-<aile>.json` |

### Ailelere özgü bilinmesi gerekenler

- **Köşe yazısı** haberle aynı `NewsArticle` şemasını taşır; gövde tam gelir.
  Başlıktaki `- Yazar - Bursa Hakimiyet` eki temizlenir, yazar ayrı alandadır.
- **Video**: `embedUrl` bazen komple `<iframe>` HTML'i döner, `src` ayıklanır.
  Sonuç `bursahakimiyet.web.tv/embed/...` adresidir. Video **dosyası indirilmez**,
  yalnızca gömme adresi ve küçük resim saklanır.
- **Foto galeri — kareler alınamıyor.** Galeri sayfasındaki tek `ItemList`
  sitenin "son galeriler" kutusudur, o galerinin fotoğrafları değil; kareler
  JavaScript ile yükleniyor ve sayfada ajax/api ucu yok. Bu yüzden yalnızca
  **kapak** ve künye alınır, kayda `kareler_eksik: true` düşülür. Kareler için
  ya JS çalıştıran bir tarayıcı ya da veritabanı dökümü gerekir.
- **Yazar sayfası**: `Person` şeması yok; ad `<h1>`den, **portre `og:image`den**
  gelir — yazar fotoğraflarının tek kaynağı budur. Sitemap ölü adres içerir
  (örn. `abdullah-basay-134` → 404); bunlar `basarisiz-yazar.txt`e düşer, normaldir.
  Yazar kimliklerinin daha eksiksiz kaynağı köşe yazısı adresleridir
  (`/yazarlar/{slug}-{id}/...` içinde yazar kimliği geçer).

## Çıktı

```
<kök>/
  tum-urller.jsonl        sitemap'ten çıkarılan tüm haber adresleri
  ilerleme.json           kaldığı yer / özet
  veri/<YIL-AY>/<id>.json haber başına yapılandırılmış veri
  gorseller/<YIL-AY>/     indirilen görseller
  log.txt                 çalışma kaydı
  basarisiz.txt           indirilemeyen adresler + neden
```

---

## Bilinmesi gerekenler

**Eski haberlerin görselleri kaynakta yok.** Site görsel düzenini
`/static/<id>-slug-hash.jpg` biçiminden `/static/YYYY/AA/GG/...` biçimine
taşımış ve eski dosyaları sunucudan silmiş. Ölçüm: 2023-04 ve öncesi
istisnasız 404, 2023-10 ve sonrası 200.

Bu yüzden betik tarihsiz `/static/` adreslerini **denemeden atlar** — eski
dönemde haber başına ~1,7 boşa istek demekti. Ölçülen kazanç: eski haberlerde
4 haber için 85 sn → 22 sn. Görsel adresi JSON'da saklanmaya devam eder; eski
görseller bir yedekten kurtarılırsa kayıtlar yeniden eşleştirilebilir.

Site eski görselleri geri koyarsa `--tum-gorselleri-dene` ile eski davranışa
dönülür.

**Boyut.** Görselsiz dönem (296.207 haber) ~2,5 GB. Görselli dönem
(260.617 haber) haber başına ~450 KB, yani **~112 GB**. Betik hedef sürücüde
10 GB kalınca kendini durdurur.

**Aynı anda tek koşu.** İki makinede birden çalıştırmayın; kendi canlı sitenize
çift yük biner.

---

## Doğrudan Python ile

```
python disa-aktarim/site_arsivleyici.py --help

  --kok KOK               çıktı kökü (ortam değişkeni: BH_ARSIV_KOK)
  --sinirla N             yalnızca ilk N haber (deneme için)
  --sitemap-yenile        adres listesini yeniden kurar
  --tum-gorselleri-dene   silinmiş eski görselleri de dener
```
