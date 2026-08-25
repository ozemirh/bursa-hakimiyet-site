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

Mevcut ilerlemeyi taşımak isterseniz arşiv klasörünü zip'leyip yeni makinede
aynı köke açın; taranmış haberler tekrar indirilmez.

---

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
