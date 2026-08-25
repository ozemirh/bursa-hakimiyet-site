# Yapay Zekâ Editör — haber masası aracı

Bir haber adresi verilir; araç kaynağı indirir, ayıklar ve Bursa Hakimiyet'in
yayın alanlarına doldurulmuş bir **taslak** üretir. Ayrıca haberle ilgili
**açık dosyaları bulup önerir**.

> **Bu araç kopyalamaz.** Kaynağın cümleleri taslağa girmez. Kaynağın fotoğrafı
> yalnızca referans olarak taşınır ve "hak durumu doğrulanmalı" damgasıyla gelir.
> Çıkan şey bir taslaktır; editör onayı olmadan yayına girmez. Konu bağlantısı da
> onaysız kurulmaz.

## Dört sağlayıcı

| | `kural` (varsayılan) | `claude` | `cli` | `skill` |
|---|---|---|---|---|
| Model | yok | `claude-opus-5` | Claude Code oturumu | Claude Code oturumu |
| API anahtarı | gerekmez | **gerekir** | gerekmez | gerekmez |
| Maliyet | yok | haber başına ~0,08-0,10 $ | aboneliğe dahil | aboneliğe dahil |
| İnternet | gerekmez (`--kaynak-json` ile) | gerekir | gerekir | gerekir |
| Sonuç | her seferinde aynı | değişebilir | değişebilir | değişebilir |
| Süre | anlık | birkaç saniye | ~1 dakika | ~2-3 dakika |
| Doldurduğu | kategori, ilçe, etiket, SEO iskeleti, önem, uyarılar, doğrulanacaklar | hepsi + başlıklar, spot, **gövde** | aynı |
| Gövde | **yazmaz** — ham malzeme tezgahı verir, editör yazar | yazar | yazar | yazar |
| Kendini denetler | — | hayır | hayır | **evet** |

`cli` ve `skill` yolları makinede kurulu ve oturumu açık `claude` komutunu çağırır, yani anahtar yerine kullanıcının kendi aboneliğini kullanır.

**Model yolundan çıkan taslak denetimden geçmelidir.** Çıplak `cli` denemesinde `denetim.py` kaynakla üç ayrı 8 kelimelik birebir örtüşme (K1) buldu — kural motorunun yapısı gereği düşemeyeceği bir hata. `skill` yolu (`yz_skill.py`) bu boşluğu kapatır: üretir, `denetim.py` ile **kendi çıktısını** denetler, bulgu varsa modele geri verip düzelttirir ve yeniden denetler. Denemede tur 0'da 1 bulgu çıktı, tur 1'de temizlendi. Tur sayısı sınırlıdır; kapanmayan bulgu `uretim.kalan_bulgular` alanında raporlanır, sessizce yutulmaz.

Kural motoru dil üretmez. Bu bir eksiklik değil, bilinçli bir sınır: modelsiz bir
motorun "gövde yazması" ancak kaynaktan cümle kopyalamakla mümkün olurdu ve bu
hem editoryal kuralı hem telifi çiğnerdi. Bunun yerine kaynağın cümleleri
puanlanıp **ham malzeme** olarak ayrı bir panelde sunulur; editör okur ve kendi
cümleleriyle yazar. Kaynak, yayınlanan sayfadaki ayrı bölmede anılır.

---

## Kurulum

Kural motoru için kurulum **gerekmez** — yalnızca standart kütüphane kullanır.

Claude sağlayıcısını kullanacaksanız:

```bash
pip install -r arac/requirements.txt
setx ANTHROPIC_API_KEY "sk-ant-..."
```

`setx` komutundan sonra **yeni bir terminal açın** — mevcut pencere eski ortam
değişkenlerini taşır.

## Kullanım

```bash
# Varsayılan: indir → ayıkla → alanları kural motoruyla doldur → konu ara
python arac/haber_taslak.py "https://ornek-site.com/haber/..."

# Ağa çıkmadan, mevcut bir çıktının kaynağıyla yeniden üret
python arac/haber_taslak.py --kaynak-json arac/cikti/ornek.json

# Claude ile tam taslak (gövde dahil)
python arac/haber_taslak.py "https://..." --saglayici claude --efor medium

# Yalnızca ayıklama
python arac/haber_taslak.py "https://..." --yalniz-ayikla

# Taslağı bir dosyaya bağla (açık onay)
python arac/haber_taslak.py "https://..." --konu bozbey-sureci
```

Çıktı `arac/cikti/<slug>.json` dosyasına yazılır. Bu dosyayı
[`../yapay-zeka-editor.html`](../yapay-zeka-editor.html) sayfasına sürükleyip
bırakın; kaynak ve taslak yan yana açılır, alanlar düzenlenebilir hale gelir.

Sayfada ayrıca **"Metni yapıştır"** kutusu vardır: haberin metnini yapıştırınca
taslak tarayıcıda, aynı kural motoruyla kurulur — Python bile gerekmez.

### Seçenekler

| Seçenek | Varsayılan | Ne yapar |
|---|---|---|
| `--saglayici` | `kural` | `kural` / `claude` |
| `--kaynak-json` | — | Ağa çıkmaz; verilen dosyanın `kaynak` nesnesini kullanır |
| `--cikti` | `arac/cikti` | Çıktı klasörü |
| `--model` | `claude-opus-5` | Model kimliği (yalnızca `--saglayici claude`) |
| `--efor` | `high` | `low` / `medium` / `high` / `xhigh` / `max` |
| `--yalniz-ayikla` | kapalı | Taslak üretmez, sadece kaynağı ayıklar |
| `--konu` | — | Taslağı bu konu kimliğine bağlar (açık onay) |
| `--konu-yok` | kapalı | Konu aramasını atlar |

---

## Dosyalar

| Dosya | Ne yapar |
|---|---|
| `ayiklayici.py` | Sayfayı indirir ve ayıklar. Yalnızca standart kütüphane. |
| `haber_taslak.py` | Şemayı, sistem yönergesini, sağlayıcı seçimini ve komut satırını taşır. |
| `kural_motoru.py` | Modelsiz taslak motoru. Yalnızca standart kütüphane. |
| `konu_eslestirme.py` | Konu takibi: ilgili dosya/haber bulur, puanlar, gerekçe yazar. |
| `sozluk.json` | Motorun tek kaynak sözlüğü (kategori, ilçe, hassas başlık, durak kelime, ek listesi). |
| `konular.json` | Açık dosyalar ve kronolojileri. `tasarim-3`'teki "Sürecin akışı" bundan üretilir. |
| `arsiv.json` | Girilmiş haber dizini. İlgili haber araması buna karşı çalışır. |
| `motor.js` | Motorların tarayıcı sürümü. Python karşılığıyla aynı sonucu verir. |
| `gomulu_uret.py` | Veriyi ve `motor.js`'i `yapay-zeka-editor.html` içine gömer. |
| `denetim.py` | Üretilen paketi editoryal kurallara karşı denetler. Rapor verir, dosyayı değiştirmez. |
| `hiza.py` | Alan sözleşmesi altı yerde hizada mı. İki motoru çalıştırıp çıktısını şemayla karşılaştırır; sayfadaki çip ↔ paket simetrisine ve `kaynak_url` çakışmasına da bakar. |
| `parite.py` | `motor.js` ile `kural_motoru.py` aynı sonucu veriyor mu. Node gerekir. |
| `yz_cli.py` | Anahtarsız yapay zekâ yolu: taslağı yerel `claude` komutuyla üretir. |
| `yz_skill.py` | Skill zinciri: üretir, `denetim.py` ile denetler, bulguyu modele düzelttirir. |
| `yayin.py` | Onaylanan taslağı üç tasarıma birden yayınlar: detay sayfası üretir, anasayfalara kart ekler. |
| `yayinci.py` | Yerel yayın sunucusu (`127.0.0.1:8787`). Editör sayfasındaki "Yayına gönder" buraya bağlanır. |
| `cikti/` | Üretilen paketler. `kural-` önekliler kural motorundan gerçekten çıktı. |

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
| `okuma_suresi_dk` | Tahmini okuma süresi, dakika (en az 1) |
| `kaynak_atfi` | "... haberine göre" kalıbı |
| `dogrulanmasi_gerekenler` | Yayından önce teyit edilecek maddeler |
| `hassas_konu` | Yargı süreci, çocuk, sağlık gibi başlıklarda uyarı |
| `bursa_ilgisi` | Haberin Bursa ile bağı yoksa dürüstçe belirtilir |
| `editor_notu` | Masaya not: ne değiştirildi, neye dikkat edilmeli |
| `konu` | Bağlandıysa dosyanın kimliği, adı ve slug'ı |

Kural motorunda `baslik_secenekleri[].metin`, `spot`, `uc_madde`, `govde`
metinleri, `seo_*` ve `url_slug` **kasıtlı olarak boş** gelir; `gerekce`
alanları editöre ne tür bir başlık isteneceğini söyler. Paketin kökünde ayrıca
iki alan bulunur:

| Alan | Açıklama |
|---|---|
| `tezgah` | Kaynağın cümleleri, puan ve öneri etiketiyle (`giriş` / `gelişme` / `rakam` / `alıntı adayı`). **Taslağa girmez**, yalnızca yazım tezgahında gösterilir. |
| `konu_adaylari` | Skor ve gerekçeleriyle ilgili dosya/haber listesi |
| `konu_onerisi` | Hiç aday yoksa yeni dosya için ad/slug/anahtar önerisi |

---

## Yayın (yerel)

Onaylanan taslak üç tasarıma birden yayınlanır: her tasarımın **haber detay
sayfası şablon olarak** kullanılır, `haber-<slug>-t{1,2,3}.html` üretilir ve o
tasarımın anasayfasına habere bağlanan bir kart eklenir.

```bash
python arac/yayinci.py          # yerel yayın sunucusu, sonra sayfadaki düğme
python arac/yayin.py arac/cikti/<slug>.json    # ya da doğrudan komut satırından
```

Sayfa `file://` ile açıldığı için tarayıcı diske yazamaz; yazma işini
`yayinci.py` yapar ve **yalnızca `127.0.0.1`e** bağlanır. Sunucu kapalıyken
sayfa aynen çalışır, düğme "yayın sunucusu kapalı" der — bağımsızlık bozulmaz.

**Yayınlanmayan taslak:** başlık boşsa, spot boşsa, gövde iki paragraftan azsa
ise paket reddedilir ve gerekçe sayfada
görünür. Kural motorunun ürettiği iskelet bu yüzden doğrudan yayına gidemez —
yazma işi editörün. Sayfadaki "doğrulanacaklar" maddelerinin hepsi
işaretlenmeden düğme çalışmaz.

Şablonun geri kalanına dokunulmaz: kenar sütunları, döviz bandı ve ilgili
haberler demo mobilyasıdır.

**Kaynağın fotoğrafı indirilir.** `gorseller/kaynak/<slug>.<uzantı>` altına
yerelleştirilir; manşet görseli ve anasayfa kartı bunu kullanır, fotoğraf altına
`(Fotoğraf: <kaynak>)` atfı düşülür ve dosya `gorseller/KAYNAKLAR.md` içine
işlenir. Uzaktan bağlanmaz — sayfalar internetsiz de açılabilmeli. İndirme
başarısız olursa kategori görseline düşülür ve yayın durmaz.

> Bu, **demo aşamasında** alınmış bir karardır. Gerçek yayında her fotoğrafın hak
> durumu ayrıca doğrulanmalıdır; araç bunu doğrulamaz.

Aynı haber yeniden yayınlanırsa eski kart silinip yenisi konur; liste şişmez.

---

## Editoryal kurallar

Sistem yönergesi (`haber_taslak.py` içindeki `SISTEM`) şunları zorunlu tutar:

- Kaynağın cümleleri kopyalanmaz; haber baştan yazılır.
- Kaynakta olmayan olgu üretilmez. Belirsiz kalan şey
  `dogrulanmasi_gerekenler` listesine düşer.
- Kaynak her zaman belirtilir; **gövdeye atıf cümlesi koymak zorunlu değildir**.
  Yayınlanan sayfada ayrı bir "Kaynak" bölmesi vardır. Haberi aldığımız sayfa
  kendi kaynağını belirtmişse (AA, DHA, Reuters…) **kaynak odur** — aracı yayın
  kaynak diye anılmaz. (23 Ağustos 2026 kararı.)
- Devam eden yargı süreçlerinde masumiyet karinesi korunur.
- Hassas başlıklarda kimlik bilgisi verilmez.
- Başlıkta tıklama tuzağı kullanılmaz.
- Bursa ile ilgisi yoksa haber zorla yerelleştirilmez.

Kuralı değiştirmek istiyorsanız `SISTEM` metnini düzenleyin; şema
(`SEMA`) ile alan adlarının tutarlı kalmasına dikkat edin.

---

## Konu takibi

Editör yeni bir haber girerken araç, arşivdeki **açık dosyaları ve daha önce
girilmiş haberleri** tarar; eşiği geçenleri skor ve **gerekçeyle** listeler.

| Sinyal | Puan |
|---|---|
| Ortak özel isim (kişi/kurum) | her biri ×5 |
| Konunun `anahtarlar` listesinden eşleşme | her biri ×4 |
| Ortak etiket | her biri ×3 |
| Aynı kategori | +2 |
| Aynı ilçe | +2 |
| Dosyanın son maddesi ≤30 gün / ≤90 gün | +2 / +1 |
| Dosya `durum: "kapali"` | toplam ×0,5 |

Puan 0-100'e ölçeklenir. **≥60** güçlü aday, **35-59** olası aday, **<35**
gösterilmez. İlçe adları, unvanlar ve "belediyesi/mahallesi" gibi genel adlar
özel isim sinyali sayılmaz — yoksa her Osmangazi haberi her Osmangazi haberine
benzer çıkardı.

**Bağlama kararı editöründür.** Araç en yüksek skorda bile kendiliğinden
bağlamaz; komut satırında `--konu <id>`, sayfada "Bu konuya bağla" düğmesi
gerekir. Bağlandığında haber dosyanın kronolojisine tarih sırasıyla girer ve
`tasarim-3` sayfalarına yapıştırılmaya hazır `<ol class="zaman">` bloğu üretilir.

Yeni bir dosya açmak gerekiyorsa araç ad, slug ve anahtar önerisi hazırlar;
editör düzenler.

---

## Maliyet

Kural motoru **ücretsizdir** — model çağrısı yapmaz.

Claude sağlayıcısında ortalama bir haber için girdi ~2-4 bin, çıktı ~2-3 bin
token. `claude-opus-5` fiyatlarıyla haber başına yaklaşık **0,08-0,10 ABD
doları**. Yoğun kullanımda `--efor medium` maliyeti belirgin biçimde düşürür.

---

## Bilinen sınırlar

- **JavaScript ile kurulan sayfalar** ayıklanamaz; `ayiklama_guveni` düşük gelir.
- **Ödeme duvarı** arkasındaki içeriğe erişilemez.
- Araç `robots.txt` okumaz. Kaynağın kullanım şartlarına uymak
  **kullanıcının sorumluluğundadır**; yayınla ilgili bir anlaşmanız yoksa
  yalnızca atıflı özet üretin.
- Tarayıcı sayfası rastgele bir siteyi **doğrudan** çekemez (CORS). Adres
  kutusu artık `yayinci.py` açıkken çalışıyor: sayfa adresi yerel sunucuya
  yollar, indirme ve ayıklama Python tarafında olur (`POST /ayikla`, model
  kullanılmaz). Sunucu kapalıysa sayfa elle yapıştırma yoluna düşer ve nasıl
  başlatılacağını söyler.
- Kural motoru **dil üretmez**: başlık, spot, üç madde ve gövde boş gelir.
  Kategori/etiket tahminleri sözlüğe dayanır; sözlükte olmayan bir konu
  "Gündem"e düşebilir. Alanları editör düzeltir.
- Konu eşleştirme sözlük ve isim örtüşmesine bakar, anlamı kavramaz. Aynı adı
  taşıyan farklı dosyalar birbirine benzeyebilir — gerekçe satırları tam da bu
  yüzden gösteriliyor.
- Tarayıcıdaki konu bağlama **kalıcı değildir**: `konular.json` dosyasına
  yazılmaz. Kalıcı kayıt için komut satırında `--konu <id>` kullanın.
- `motor.js` ile Python motoru **elle, ayrı ayrı** güncellenir ve sessizce
  ayrışabilir. `gomulu_uret.py --kontrol` bunu görmez; o yalnızca gömülü bloğun
  taze olup olmadığına bakar. İkisinin aynı sonucu verdiğini `python arac/parite.py`
  doğrular (Node gerekir). Sözlüğü ya da motoru değiştirdiyseniz önce `parite.py`,
  sonra `python arac/gomulu_uret.py` çalıştırın.
