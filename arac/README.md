# Yapay Zekâ Editör — haber masası aracı

Bir haber adresi verilir; araç kaynağı indirir, yapılandırılmış olgu çıkarımı yapar
ve Bursa Hakimiyet'in yayın alanlarına doldurulmuş bir **taslak** üretir.

> **Bu araç kopyalamaz.** Kaynağın cümleleri alınmaz. Olgular çıkarılır, haber
> kaynak gösterilerek yeniden yazılır, doğrulanması gereken noktalar işaretlenir.
> Kaynağın fotoğrafı yalnızca referans olarak taşınır ve "hak durumu doğrulanmalı"
> damgasıyla gelir. Çıkan şey bir taslaktır; editör onayı olmadan yayına girmez.

---

## Kurulum

```bash
pip install -r arac/requirements.txt
```

API anahtarını tanımlayın (Windows, kalıcı):

```
setx ANTHROPIC_API_KEY "sk-ant-..."
```

Komutu çalıştırdıktan sonra **yeni bir terminal açın** — mevcut pencere eski
ortam değişkenlerini taşır.

## Kullanım

```bash
# Tam akış: indir → ayıkla → taslak üret
python arac/haber_taslak.py "https://ornek-site.com/haber/..."

# Yalnızca ayıklama (API çağrısı yapmaz, anahtar gerekmez)
python arac/haber_taslak.py "https://..." --yalniz-ayikla

# Daha ucuz/hızlı çalıştırma
python arac/haber_taslak.py "https://..." --efor medium
```

Çıktı `arac/cikti/<slug>.json` dosyasına yazılır. Bu dosyayı
[`../yapay-zeka-editor.html`](../yapay-zeka-editor.html) sayfasına sürükleyip
bırakın; kaynak ve taslak yan yana açılır, alanlar düzenlenebilir hale gelir.

### Seçenekler

| Seçenek | Varsayılan | Ne yapar |
|---|---|---|
| `--cikti` | `arac/cikti` | Çıktı klasörü |
| `--model` | `claude-opus-5` | Model kimliği |
| `--efor` | `high` | `low` / `medium` / `high` / `xhigh` / `max` |
| `--yalniz-ayikla` | kapalı | API'ye hiç gitmez, sadece kaynağı ayıklar |

---

## Dosyalar

| Dosya | Ne yapar |
|---|---|
| `ayiklayici.py` | Sayfayı indirir ve ayıklar. Yalnızca standart kütüphane. |
| `haber_taslak.py` | Şemayı, sistem yönergesini ve komut satırını taşır. |
| `cikti/` | Üretilen paketler. Depodakiler sunum örnekleridir. |

### Ayıklama nasıl çalışıyor

Sırayla üç yöntem denenir ve hangisinin işe yaradığı çıktıda
`ayiklama_yontemleri` alanında raporlanır:

1. **JSON-LD** — `NewsArticle` / `Article` şeması. En güvenilir kaynak.
2. **OpenGraph / Twitter meta** — `og:title`, `og:description`, `og:image`.
3. **Paragraf sezgisi** — en çok gerçek cümle taşıyan kapsayıcı seçilir.

`ayiklama_guveni` alanı `yuksek` / `orta` / `dusuk` değerlerini alır. `dusuk`
ise kaynağı elle kontrol edin; muhtemelen sayfa JavaScript ile kuruluyordur.

---

## Üretilen alanlar

`taslak` nesnesi şunları taşır:

| Alan | Açıklama |
|---|---|
| `baslik_secenekleri` | 3 seçenek, her biri gerekçeli (düz / etki odaklı / kısa) |
| `onerilen_baslik_indeksi` | Modelin önerdiği seçenek |
| `spot` | 1-2 cümle, 160-260 karakter |
| `uc_madde` | "3 maddede ne oldu" kutusu |
| `govde` | `paragraf` / `ara_baslik` / `alinti` blokları |
| `kategori`, `ilce`, `onem` | Kapalı listelerden seçilir |
| `etiketler` | 3-8 adet |
| `seo_baslik`, `seo_aciklama`, `url_slug` | Arama alanları |
| `gorsel_alt`, `gorsel_altyazi` | Erişilebilirlik ve fotoğraf altı |
| `kaynak_atfi` | "... haberine göre" kalıbı |
| `dogrulanmasi_gerekenler` | Yayından önce teyit edilecek maddeler |
| `hassas_konu` | Yargı süreci, çocuk, sağlık gibi başlıklarda uyarı |
| `bursa_ilgisi` | Haberin Bursa ile bağı yoksa dürüstçe belirtilir |
| `editor_notu` | Masaya not: ne değiştirildi, neye dikkat edilmeli |

---

## Editoryal kurallar

Sistem yönergesi (`haber_taslak.py` içindeki `SISTEM`) şunları zorunlu tutar:

- Kaynağın cümleleri kopyalanmaz; haber baştan yazılır.
- Kaynakta olmayan olgu üretilmez. Belirsiz kalan şey
  `dogrulanmasi_gerekenler` listesine düşer.
- Atıf zorunludur ve ilk iki paragraftan birinde geçer.
- Devam eden yargı süreçlerinde masumiyet karinesi korunur.
- Hassas başlıklarda kimlik bilgisi verilmez.
- Başlıkta tıklama tuzağı kullanılmaz.
- Bursa ile ilgisi yoksa haber zorla yerelleştirilmez.

Kuralı değiştirmek istiyorsanız `SISTEM` metnini düzenleyin; şema
(`SEMA`) ile alan adlarının tutarlı kalmasına dikkat edin.

---

## Maliyet

Ortalama bir haber için girdi ~2-4 bin, çıktı ~2-3 bin token.
`claude-opus-5` fiyatlarıyla haber başına yaklaşık **0,08-0,10 ABD doları**.
Yoğun kullanımda `--efor medium` maliyeti belirgin biçimde düşürür.

---

## Bilinen sınırlar

- **JavaScript ile kurulan sayfalar** ayıklanamaz; `ayiklama_guveni` düşük gelir.
- **Ödeme duvarı** arkasındaki içeriğe erişilemez.
- Araç `robots.txt` okumaz. Kaynağın kullanım şartlarına uymak
  **kullanıcının sorumluluğundadır**; yayınla ilgili bir anlaşmanız yoksa
  yalnızca atıflı özet üretin.
- Tarayıcı sayfası rastgele bir siteyi doğrudan çekemez (CORS). Canlı çekim
  için bu komut satırı aracını kullanın, çıkan JSON'u sayfaya bırakın.
