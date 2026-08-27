# Yönetim Paneli — Notlar, Kararlar ve Alan Sözleşmesi

> Son güncelleme: 25 Ağustos 2026 (kararlar turu — dört ekran)
> Kardeş belge: `DEMO-NOTLARI.md` (site tasarımları). Bu belge **panel** içindir.

---

## 1. Nerede kaldık

Mevcut panelin 21 ekranı incelendi (`C:\Users\Asus\Downloads\bursa_hakimiyet_panel`).
Sağlayıcı `haberyazilimi.com`; taban Bootstrap 5 + jQuery 3.7.1 + DataTables + CKEditor 4.

Bilgi mimarisi: **21 ekran → 7 bölüm** — Bugün · İçerik · Sayfa Düzeni · Konu Takibi ·
Etkileşim · İlan & Reklam · Ayarlar.

**Elimizdeki 21 döküm bir operatör hesabına ait.** Yönetici katmanı dökümde yok; kuruldu (§11).

### Yapılan ekranlar

| Dosya | Ne |
|---|---|
| `panel-haber-ekle.html` | Panelin en yoğun ekranı. Kabuk, form dili ve doğrulama dili burada doğdu |
| `panel-bugun.html` | Genel Bakış'ın yerine geçen iş kuyruğu |
| `panel-akis.html` | Haber + foto + video tek liste, köşe ayrı sekme, toplu işlem |
| `panel-etkilesim.html` | Yorum kuyruğu ve bildirimler |
| `panel-sayfa-duzeni.html` | Manşet slotları + 50 reklam alanının envanteri — **şematik** |
| `panel-konu-takibi.html` | Konu dosyaları, kronoloji, aday eşleştirme, yayın bloğu üretici |
| `panel-ilan-reklam.html` | Resmi ilanlar, kampanyalar, BIK kodları, kendi yayınlarım |
| `panel-ayarlar.html` | Taksonomi · Kullanıcılar & Roller · Hesap |
| `panel-roller.html` | Rol tanımları ve yetki dağılımı — **yönetici ekranı** |
| `panel-kullanicilar.html` | Hesap yönetimi — **yönetici ekranı** |

---

## 2. İki kalıcı karar

**Görsel dil.** Panel, `yapay-zeka-editor.html`'in araç dilini miras alır (Inter + Source Serif 4
+ IBM Plex Mono; `.kapsa`, `.bant`, `.btn`, `.cip`, `.rozet`; `--uyari-*` `--tehlike-*` `--bilgi-*`
durum renkleri). **Üç site tasarımının hiçbirine bağlı değildir** — panel okura değil masaya bakar,
ve yön seçimi henüz yapılmadı.

**Ortak kabuk dosyası yok.** Bağımsızlık kuralı gereği kabuk her panel dosyasına gömülür.
**Birinde değişen hepsinde değişir** — seslendirme betiğindeki düzenin aynısı.

Kabuğun parçaları: `:root` değişkenleri · `.atla` · `header.bant` · `nav.kenar` (7 bölüm) ·
`.sayfa-bas` · `.duyuru` · `.btn` `.kutu` `.rozet` bileşenleri.

---

## 3. Permalink — ölçülmüş gerçek

`D:\bursa-hakimiyet-arsiv\tum-urller.jsonl` üzerinde **556.824 adresin tamamı** ölçüldü
(2021-04 → 2026-08, 65 ay). Salt okunur kullanıldı.

**Haber deseni: `/{kategori-slug}/{slug}-{id}` — %100 eşleşme. `/haber/` önekli adres: 0.**

Haber Ekle formundaki `[category]/[slug]-[id]` önizlemesi **doğruyu gösteriyor.**

| Kategori slug | Adres sayısı |
|---|---|
| gundem | 211.205 |
| spor | 81.342 |
| bursa | 81.336 |
| dunya | 68.680 |
| ekonomi | 54.215 |
| magazin | 28.845 |
| bursaspor | 11.577 |
| saglik | 6.752 |
| teknoloji | 4.705 |
| yasam | 3.495 |
| bursa-da-spor | 3.331 |
| aktualite | 859 (ilk kayıt 2024-01) |
| savunma-sanayi | 478 (ilk kayıt 2024-03) |
| bursada-spor | **4** (yalnız 2022-01) |

14 slug = Haber Ekle'nin 13 kategorisi + 1 artık yazım. **URL segmenti kategori slug'ının
kendisidir, birebir.**

> **Sonucu ağır:** kategori adını/slug'ını değiştirmek ya da iki kategoriyi birleştirmek
> **556 binden fazla haber adresini kırar.**

`bursada-spor` yalnız 2022-01'de 4 kayıt; `bursa-da-spor` 2021-04'ten bugüne kesintisiz.
Yani slug göçü değil, **tek aylık bir sapma** — ama sonucu aynı: sapan adresler sitemap'te
duruyor, yönlendirme ihtiyacı zaten var.

**Diğer türlerin desenleri** (panel dökümünden; sitemap'te ölçülmedi):

| Tür | Desen |
|---|---|
| Foto galeri | `/galeriler/{kategori-slug}-{katid}/{slug}-{id}` |
| Video | `/videolar/{kategori-slug}-{katid}/{slug}-{id}` |
| Köşe yazısı | `/yazarlar/{yazar-slug}-{yazarid}/{slug}-{id}` |

---

## 4. Haber Ekle — alan sözleşmesi

Kaynak: `__Haber Ekle__.html`, `news_form` (`enctype=multipart/form-data`,
`news_save_ajax.php`, `action=upsertNews`).

**"Gerçekten zorunlu" sütunu:** ekranda kırmızı yıldız var mı / `newsSave()` gerçekten engelliyor mu.
`formControl("news_form", ['do','csrf','img-type','galleries','tags','news-image','articleAuthor','summery'])`
çağrısındaki dizi muafiyet listesi olarak okundu — `formControl`'ün gövdesi kaydedilmiş
dosyalarda yok, bu bir çıkarımdı (bkz. §18, karar 6).

| # | Alan (mevcut) | Tip | Sınır | Yıldız | Gerçekten zorunlu | Yeni paneldeki karşılığı |
|---|---|---|---|---|---|---|
| 1 | `csrf` | hidden | — | — | evet | Korunur, gizli |
| 2 | `title` | text | **60** | var | **evet** | Başlık — sayaç görünür |
| 3 | `title2` | text | 60 | — | hayır | İkinci başlık — varsayılan kapalı, açılır |
| 4 | `summery` | textarea | **160** | var | **hayır** | Spot — **gerçekten zorunlu yapıldı** |
| 5 | `ckeditor` | textarea | — | var | evet | Gövde — en az 2 paragraf |
| 6 | `status` | select | — | — | evet | Durum — Aktif/Pasif/Arşiv (§9) |
| 7 | `tagElementName[i]` / `tagElementValue[i]` | dinamik | — | var | **hayır** | Etiketler — **gerçekten zorunlu yapıldı**, çip arayüzü |
| 8 | `image` | file | — | — | `imageSizeControl` | Manşet görseli |
| 9 | `image-url-name` | text | — | — | hayır | URL'den çek |
| 10 | `news-image` / `img-type` / `4_3Size` | hidden | — | — | — | Görsel iç alanları |
| 11 | *(yok)* | — | — | — | — | **`gorsel_alt` — YENİ.** Panelde alt metin alanı hiç yok |
| 12 | `category` | select (13) | — | — | evet | Kategori — **adresi belirler**, değişimde uyarı |
| 13 | *(yok)* | — | — | — | — | **`ilce` — YENİ.** 17 ilçe, tek seçim, isteğe bağlı (§8) |
| 14 | `permalink` | text | — | — | otomatik | Adres — `/{kategori}/{slug}-{id}` canlı önizleme |
| 15 | `source_news_id` | select (**348**) | — | — | hayır | **Üçe bölündü:** Ajans / Dış yayın / Kendi muhabirimiz (§5) |
| 16 | `contentSourceType` | radio | — | — | hayır | Kaynak türü (Kaynak / Muhabir) belirteci |
| 17 | `articleAuthor` | **text** | — | var | **hayır** | Meta Yazar Bilgisi — **kapalı liste + türetim** (§7) |
| 18-20 | `headlines[...]` | checkbox | — | — | hayır | Ana / Tepe / Kare Manşet |
| 21 | `created_time` | datetime | — | — | evet | Yayın zamanı |
| 22 | `updated_time` + kutu | datetime+cb | — | — | hayır | Güncelleme zamanı |
| 23-26 | `rss_control` · `comments` · `redirect` · `embed` | cb (+alan) | — | — | hayır | Seçenekler |
| 27 | `galleriesSelect2` → `galleries` | multi | — | — | hayır | Bağlı galeriler |
| 28 | `elval` | hidden | — | — | hayır | İlgili haberler |
| 29-30 | `focus_keyword` · `seo_baslik` | text/hidden | — | — | hayır | SEO alanları |
| 31 | *(yok)* | — | — | — | — | **Konu bağlama — YENİ.** Onaysız bağlanmaz |
| 32 | *(yok)* | — | — | — | — | **`hazirlik` — YENİ.** Masa ekseni (§9) |

---

## 5. Kaynak alanı — 348 kaydın hâli

348 kayıt / 342 benzersiz. Ölçülen bozukluklar:

- **6 birebir tekrar:** CNBC-E, Star Gazetesi, Nesine TV, Patronlar Dünyası, Uğur Dinar, Gerçek Gündem
- **7 birleşik kayıt:** `İHA, DHA` · `İHA - DHA - AA` · `Haber Merkezi / İHA` ·
  `Coşkun Saitoğlu - İsmail Karaduman` · `Recep Saka-Metin Araç` ·
  `Simlanur İnce İzci / Ceren Sümbül` · `Patronlar Dünyası - İHA - DHA - AA`
- **Üç farklı şey tek listede:** ajans (İHA, DHA, AA) · dış yayın (Gemlik Körfez Gazetesi,
  Halk TV) · kendi muhabiri (Ceren Sümbül, Barış Yalım)
- "Coşkun Saitoğlu" hem kaynak listesinde hem editör listesinde ("Coşkun SAİTOĞLU") —
  aynı insan, iki tablo, iki yazım

Çoklu seçim olmadığı için her kombinasyon ayrı kayıt açılmış. **Yeni panelde alan üçe bölündü.**

---

## 6. Yapay zekâ düğmeleri — yön değişti

Mevcut panelde üç düğme (`newsDetailAI.php`) ve üçü de **aşağı yönlü**:
`getSummaryWithAI()` · `getTagsWithAI()` · `generateContentWithAI()`.
`checkAISummary()` **en az 250 karakter** içerik şart koşuyor — metin zaten yapıştırılmış olmalı.

`generateContentWithAI()` ("İçeriği Yeniden Üret") başka bir yayının metnini yeniden yazdırıyor.
**Bu düğme yeni panelden kaldırıldı**; yerine ekranın en üstüne **kaynak adresi → taslak** akışı
geldi. Editoryal kural gevşetilmedi, ekranın kendisinden çıkarıldı.

Üç yol seçilebilir: A kural motoru · B skill zinciri · C çıplak yapay zekâ.

---

## 7. Meta Yazar Bilgisi — karar

Mevcut hâli **serbest metin**; altı yasal değer yalnızca etiketin yanındaki `<small>` içinde
ipucu olarak yazıyor, ve `formControl` muafiyeti yüzünden kırmızı yıldıza rağmen boş
kaydedilebiliyor.

### Karar: kapalı liste + kaynak türünden türetim

Alan artık altı değerli bir açılır liste. **Değer, editörün zaten seçtiği "Kaynak türü"nden
kendiliğinden türetiliyor**; editör isterse üzerine yazabilir (elle değiştirince türetim durur).

| Kaynak türü | Türetilen Meta Yazar Bilgisi |
|---|---|
| Ajans | **Haber Ajansı** |
| Dış yayın | **Alıntı/İktibas** |
| Kendi muhabirimiz | **Fikir İşçisi** |

Varsayılan kaynak türü **Ajans** olduğu için varsayılan değer **Haber Ajansı** olur.
Gerekçe: masa günde ~220 haber üretiyor ve kaynak listesinin başı ajanslarla dolu.

### Her değerin ne zaman seçileceği (ekranda görünen yardım metni)

| Değer | Ne zaman |
|---|---|
| **Fikir İşçisi** | Haberi gazetenin kendi kadrosundaki gazeteci yazdıysa |
| **Bülten** | Bir kurum veya şirketin gönderdiği basın bülteninden üretildiyse |
| **Haber Ajansı** | İHA, DHA, AA gibi bir haber ajansından geldiyse |
| **Haber Merkezi** | Haber merkezinde derlendiyse ve tek bir imzaya bağlanamıyorsa |
| **İçerik Aktarımı** | Anlaşmalı bir içerik ortağından toplu aktarıldıysa |
| **Alıntı/İktibas** | Başka bir yayından kaynak gösterilerek alıntılandıysa |

Türetimin asıl faydası: yasal sonuç doğuran bir alanı serbest seçimden çıkarıp, editörün
zaten beyan ettiği bir olguya bağlamak. Yanlış işaretleme olasılığı düşer.

---

## 8. İlçe — karar

**17 ilçe, tek seçim, isteğe bağlı.**

- **"Bursa geneli" / "Bursa dışı" gibi kalem yok.** İl düzeyini `BURSA` kategorisi zaten
  taşıyor; ilçe onun üstüne kırılım ekler.
- **Tek seçim.** `arac/arsiv.json` tek `ilce` değeri tutuyor; çoklu yapmak araç tarafında
  karşılığı olmayan bir alan üretirdi.
- **İsteğe bağlı.** İl düzeyi kategoriyle karşılandığı için ilçe zorunlu tutulmuyor;
  seçilirse haber ilçe sayfasında da görünür.

Yazımlar `tasarim-1-klasik.html` ilçe şeridi ve `arac/arsiv.json` ile birebir tutuyor
(Osmangazi, Nilüfer, Yıldırım, İnegöl, Gemlik, Mudanya, İznik, Karacabey, Orhangazi,
Yenişehir, Mustafakemalpaşa, Kestel, Gürsu, Orhaneli, Keles, Harmancık, Büyükorhan).

**Slug'ların kaynağı — kural doğrulandı.** Dönüştürme kuralı ölçülerek sınandı:
Türkçe karakter sadeleştirme (`ç→c ğ→g ı→i ö→o ş→s ü→u`) + küçük harf + tire.

| Ölçüm | Sonuç |
|---|---|
| Kuralın panel slug'ıyla uyuştuğu ilçe | **17 / 17** |
| `tasarim-2-hibrit.html`'deki `data-ilce` ile çapraz doğrulanan | **10** |
| Çakışma | **yok** |

`tasarim-2`'de yalnızca 10 ilçe geçiyor (Osmangazi, Nilüfer, Yıldırım, İnegöl, Gemlik,
Mudanya, İznik, Karacabey, Orhangazi, Yenişehir) ve onunun slug'ı birebir tutuyor.
Kalan 7 ilçe (Mustafakemalpaşa, Kestel, Gürsu, Orhaneli, Keles, Harmancık, Büyükorhan)
**aynı kuralı** izliyor — tasarım dosyalarında henüz hiç geçmiyorlar, o kadar.

Yani bu bir **risk değil, eksiklik**: panelin 17'lik listesi **kanoniktir**; ilçe sayfaları
yapılırken tasarım dosyaları bu listeyi alacak.

> **Göç notu:** `arsiv.json`'da 13 kayıt `"ilce": "Bursa geneli"` taşıyor. Panelde bu değerin
> karşılığı yok. Taşımada bu kayıtların ilçesi **boşaltılmalı**, kategorileri `BURSA` olmalı.

---

## 9. Durum ve hazırlık — karar

### Durum enum'u üç değil dört

Süzgeç seçenekleri karşılaştırıldığında ortak çıktı:

`1 = Aktif · 2 = Pasif · 3 = Silinmiş · 4 = Arşiv`

İçerik ekranları **3'ü gizler** (yumuşak silme), Yorumlar ekranı 3'ü gösterip 4'ü gizler.

### Karar: yayın durumu ile masa durumu ayrıldı

Mevcut sistemde Pasif hem "henüz bitmedi" hem "yayından çekildi" anlamına geliyor. Bu yüzden
iş kuyruğu kurulamıyor — Bugün ekranı bu ayrımı gerektiriyor.

**Yayın durumuna dokunulmadı.** Üç görünen ad (Aktif / Pasif / Arşiv) aynen korundu, yeni
sözlük icat edilmedi. Onun yerine **ayrı bir eksen** eklendi:

| Eksen | Değerler | Ne söyler |
|---|---|---|
| `status` (mevcut) | Aktif · Pasif · Arşiv | Haber yayında mı |
| `hazirlik` (**yeni**) | Taslak · İncelemede · Yayına hazır | Masada hangi aşamada |

`hazirlik` yalnız `status = Pasif` iken anlamlıdır ve ekranda yalnız o zaman görünür.
Yayına alınan haberin hazırlığı örtük olarak "hazır"dır.

**Bugün ekranının kuyruğu** = `status = Pasif` **ve** `hazirlik ∈ (Taslak, İncelemede)`.

Bu kararın avantajı: eski enum'a hiç dokunulmadı, dolayısıyla 1 milyondan fazla mevcut kaydın
durumu yeniden yorumlanmıyor. Yeni alan boş gelirse "Taslak" varsayılır.

---

## 10. Mevcut panelden taşınmayan davranışlar

| Davranış | Neden taşınmadı |
|---|---|
| Üç sekme (Genel / Görsel / Seçenekler) | `newsSave()` iki sekmeye tıklanmamışsa **sessizce sekmeye atlayıp geri dönüyor**, uyarı vermiyor. Yerine tek sayfa akış + sağda kontrol listesi |
| Kırmızı yıldızın anlamsızlığı | Spot ve etiket gerçekten zorunlu yapıldı |
| Fiilsiz seçim kutuları | `dataTables.checkboxes` yüklü ama "toplu"/"seçilen" kelimesi 21 dosyada **0 kez** geçiyor. Toplu işlem İçerik listesinde fiiliyle gelecek |
| Manşetin kayıt defteri olması | ~1.900 kayıt birikmiş, "şu an anasayfada ne var" sorusunun cevabı yok. Slot görünümü Sayfa Düzeni'ne taşınacak |

---

## 11. Roller ve kullanıcılar — karar

Elimizdeki 21 döküm bir **operatör** hesabına ait. Yazılımın menü betiği
(`menuPatterns`) yönetici uçlarını ele veriyor:

- `usertype_list / usertype_add / usertype_edit` → rol tanımları
- `operator_list / operator_add / operator_edit` → kullanıcı yönetimi
- `bots/list · bot_news · bots/add · bots/edit` → otomatik haber alma

Ayrıca `gallery_add`, `video_add`, `editorialist_add`, `advertisement_add`,
`official_announcement_add` ekranlarının dökümü yok — **alan sözleşmesi yalnız haber için
elimizde.**

### Beş rol

Gazete masasının gerçek iş bölümünden çıkarıldı. Dökümdeki kanıt: manşet kayıtlarının ve
resmi ilanların neredeyse tamamı **iki kişide** toplanmış — ayrım fiilen zaten var, sistemde
karşılığı yoktu.

| Yetki | Muhabir | Editör | Sayfa Sekreteri | İlan Sorumlusu | Yayın Yönetmeni |
|---|:--:|:--:|:--:|:--:|:--:|
| Haber girme (taslak) | ● | ● | ● | – | ● |
| Kendi haberini yayınlama | – | ● | ● | – | ● |
| Başkasının haberini yayınlama | – | ● | ● | – | ● |
| Haberi arşive alma | – | ● | ● | – | ● |
| Manşete alma | – | – | ● | – | ● |
| Sayfa düzeni ve reklam alanları | – | – | ● | – | ● |
| Resmi ilan girme | – | – | – | ● | ● |
| Reklam kampanyası | – | – | – | ● | ● |
| Yorum onaylama | – | ● | – | – | ● |
| Köşe yazısı ve yazar yönetimi | – | ● | – | – | ● |
| Konu açma ve bağlama | – | ● | – | – | ● |
| Taksonomi düzenleme | – | – | – | – | ● |
| Kullanıcı ve rol yönetimi | – | – | – | – | ● |
| Log kayıtları | – | – | – | – | ● |

Dayandığı gerekçeler:

- **Muhabir yayınlayamaz.** Sahadan giren haber Pasif/Taslak'ta doğar; yayına alma kararı
  masada verilir. Bu, §9'daki hazırlık ekseninin karşılığıdır.
- **Manşet ayrı yetkidir.** Anasayfanın sırasını değiştirmek yayınlamaktan farklı bir karardır.
- **Resmi ilan ayrı yetkidir.** BIK yükümlülüğü taşır, yasal sonuç doğurur.
- **Yorum onayı editördedir.** Sorumluluk yayın tarafındadır.
- **Taksonomi yalnız Yayın Yönetmeni'nde.** Kategori slug'ı **556.824 adresin** parçası;
  günlük yetkiye bırakılamaz.

### Kullanıcı tarafında bulunan sorun

Editör süzgecinde **dört hesap "Administrator" adını paylaşıyor**. Log kayıtları ve "Editör"
sütunu bunlara işaret ettiğinde kimin ne yaptığı anlaşılamıyor. Adlandırılmalı ya da
kapatılmalı. Ayrıca `BackOffice` ve `Haberyazılımı Seo` sağlayıcı hesapları duruyor.

**Öneri:** yayınlama, manşet ve resmi ilan yetkisi olan rollerde 2FA zorunlu olsun.
Altyapı hazır (Google Authenticator + SMS), şu an isteğe bağlı.

---

## 12. Akış — toplu işlem ve daralt-ve-bul

### Daralt-ve-bul

Listede 1.044.757 kayıt var; mevcut panel bunu 269 sayfa olarak **baştan döküyor**.
Yeni ekranda liste **süzgeçten sonra** geliyor. Açılışta beş hızlı giriş var:
Bugün girilenler · Masada bekleyenler · Benim haberlerim · Son 7 gün · Süzgeci kendim kurayım.

Süzgeç ekseni: tür · durum · **hazırlık** · kategori · ilçe · başlıkta ara.
Etkin süzgeçler çip olarak görünür ve tek tek kaldırılabilir.

### Toplu işlem — fiiller yetkiye bağlı

Mevcut panelde her liste ekranında `dataTables.checkboxes` yüklü ve seçim kutuları var, ama
"toplu" ve "seçilen" kelimeleri **21 ekranda 0 kez** geçiyor. Seçim var, fiil yok.

Eklenen fiiller ve hangi rolde açık olduğu (§11 matrisiyle birebir):

| Fiil | Muhabir | Editör | Sayfa Sekreteri | İlan Sor. | Yayın Yön. |
|---|:--:|:--:|:--:|:--:|:--:|
| Yayına al / Yayından çek / Arşive al | – | ● | ● | – | ● |
| Hazırlık değiştir | ● | ● | ● | – | ● |
| İlçe ata | ● | ● | ● | – | ● |
| Etiket ekle | ● | ● | ● | – | ● |
| Kategori değiştir | – | ● | ● | – | ● |
| **Manşete al** | – | **–** | ● | – | ● |

Ekranda oturum **Editör** rolüyle açılıyor; bu yüzden **"Manşete al" kilitli** ve neden
kilitli olduğu satır altında yazıyor. Yetki modelinin çalıştığı burada görünüyor.

**İlçe ata**, yeni alanın geçmişe uygulanabilmesi için özellikle önemli: 556.824 haberin
hiçbirinde ilçe yok.

### Kategori değiştirme ayrı uyarı alıyor

Toplu kategori değişimi, onaydan önce kırmızı bir uyarı açıyor: seçili kayıt sayısını
söylüyor, adres deseninin `/{kategori}/{slug}-{id}` olduğunu hatırlatıyor ve **eski
adreslerin kırılacağını** belirtiyor. "Yine de değiştir" seçilirse gerçek panelde
yönlendirme kaydı da üretilmesi gerektiği not düşülüyor.

### Köşe neden ayrı sekmede

Haber, foto ve video aynı eksenlerde süzülüyor (kategori · ilçe · durum · editör).
Köşe yazısında **kategori yok, yazar var**, ve adres yazara bağlı:
`/yazarlar/{yazar-slug}-{yazarid}/{slug}-{id}`. Tek listede birleştirmek iki farklı
süzgeç eksenini aynı tabloya sıkıştırmak olurdu.

---

## 13. Etkileşim — kuyruk ve bildirim

### Yorum: liste değil sıra

Mevcut panelde yorumlar 61 sayfalık bir tabloda ve tek fiil durum çevirmek
(`toggle_status_ajax`). Yeni ekranda yorumlar **sırayla** geliyor: karar verilir, sıradakine
geçilir. İlerleme (`3 / 7`) ve kalan sayısı görünür; okurun kimliği, IP'si ve yorumun
yazıldığı içerik yan yana duruyor.

Klavye: <kbd>A</kbd> onayla · <kbd>R</kbd> reddet · <kbd>D</kbd> düzenle · <kbd>S</kbd> sonraki.
Kısayollar bir alana yazarken çalışmaz.

> **Demo sınırı:** dökümden yalnız **bir** yorumun tam metni çıkarılabildi. Kuyruk 7 kayıt
> gösteriyor (gerçek bekleyen sayısı), kalan 6'sı "metin dökümde yok" diye işaretli.
> Uydurma yorum yazılmadı.

### Karar: yorum düzenleme kaldırılmadı, üç şarta bağlandı

Mevcut panelde editör okurun yorumunu **izsiz** değiştirebiliyor
(`comments_edit` + `saveComments`). Kaldırmayı düşündüm, kaldırmadım.

**Gerekçe:** hakaret ve kişisel veri (telefon, adres, ad) çıkarmak gerçek bir moderasyon
ihtiyacı; bu yetki alınırsa editörün elinde yalnız "tümünü reddet" kalır ve yayınlanabilecek
yorumlar da gider. Ama **izsiz düzenleme okur adına beyanda bulunmaktır**.

Üç şart eklendi:

1. **Gerekçe zorunlu** — kişisel veri / hakaret / reklam. Gerekçesiz kaydedilmiyor.
2. **Yorumda "düzenlendi" işareti görünür** — okur değiştirildiğini görebilir.
3. **Özgün metin log kaydında saklanır.**

### Bildirim: oran ekranın en üstünde

Mevcut panelde hedef ve açan sütunları var ama **oran hesaplanmıyor** — yani %0,2'lik
performans hiçbir yerde görünmüyor. Yeni ekranda oran en üste alındı.

Ölçülen 10 gönderim, ortalama **%0,21**:

| En iyi | %0,56 — "İŞTE SERBEST KALANLAR" (21.823 → 122) |
|---|---|
| En kötü | %0,10 — "BURSA'NIN NOSTALJİ DURAĞI!" (22.038 → 21) |

**Bulgu:** hedef kitle 2025 ortasında 9.207 cihazdı, bugün 22.683 — iki buçuk katı.
Ama açan sayısı 21-47 bandında sıkışmış (tek istisna 122). **Büyüyen kitle, sabit ilgi.**
Bildirim sayısını artırmanın oranı düşürüyor olabileceği ekranda yazılı.

Gönderim formunda başlık 50 karakterle sınırlı (kilit ekranında kesilmemesi için) ve
haber seçilmeden gönderim yapılamıyor.

---

## 14. Sayfa Düzeni — slotlar ve reklam envanteri

### Manşet: defterden slota

Mevcut panelde Manşetler bir **kayıt defteri**: her işaretleme yeni satır açıyor, ~1.900 kayıt
birikmiş, ve hiçbiri "şu anda hangisi yayında" demiyor. Ekranın tek işi bu soruyu cevaplamak.

Üç slot (Ana · Tepe · Kare) dolu hâlleriyle duruyor; her birinde içindeki haber, kimin
koyduğu, ne zaman koyduğu ve **ne kadar süredir orada olduğu** var. Ana manşetin yaşı
eşiği geçince amber renge dönüyor — Bugün ekranındaki "2 sa 51 dk" uyarısının kaynağı bu.

Defter silinmedi: "Slot geçmişi" olarak duruyor ama **ikincil**. Soru yukarıda cevaplanıyor.

### Şema neden ölçüsüz

Site yönü seçilmediği için şema **ölçü ve oran vermiyor** — yalnız **sıra ve komşuluk**
gösteriyor: masthead reklam → logo bandı → menü → döviz bandı → tepe manşet →
(sol pageskin · ana manşet · kare manşet · sağ pageskin) → manşet altı reklam →
kategori blokları → haber arası reklam → alt bölümler. Bu sıra üç tasarım yönünde de aynı.

**Seçim yapıldığında ne değişecek:** şemadaki kutular soyut adlar olmaktan çıkıp seçilen
tasarımın gerçek ölçülerini alacak — Tasarım 1'de üç kolonlu manşet bloğu, Tasarım 2'de
kart yapısı, Tasarım 3'te başlığın kendisinin hero olduğu tek kolon. Kutuların **oranları**
o yönün `DEMO-NOTLARI.md`de yazılı görsel oranlarından (manşet 16:8.4, kart 16:10,
hero 4:3.4) gelecek ve şema, düzenin küçültülmüş bir önizlemesine dönüşecek. Slot sayısı
da yönle birlikte kesinleşecek: Tasarım 1'in üç kolonlu manşeti üç ayrı yuva ister,
Tasarım 3'ün tek hero'su bir tane. Bugünkü üç slot (Ana/Tepe/Kare) mevcut panelin
`headlines[]` alanlarından geliyor ve **yön seçilene kadar bağlayıcı sayılmamalı**.

### Reklam alanları: envanter değil birikinti

50 tanımlı alan ölçüldü:

| Ölçüm | Sayı |
|---|---|
| Düzenli adlandırılmış (`-Konum- ÖlçüxÖlçü`) | **21** |
| Ad-hoc açılmış | **29** |
| Yer tutucu ("Bu alana reklam verebilirsiniz …") | **6** |
| Reklamveren adıyla açılmış | **5** (hepsiburada 2/3/4, hastavuk fullpage, Almira) |
| Ölçü `*` ile yazılmış (`728*90`) | **4** |
| Ölçü hiç yok | **12** |

Ayrıca **`-Manşet altı4-` eksik**: 1, 2, 3, 5, 6 var, 4 yok.

Ekranda her satırın konumu ve ölçüsü **ayrıştırılarak** gösteriliyor ve tespit edilen
sorunlar çip olarak işaretleniyor. Amaç, yuvanın serbest metin olmadığını görünür kılmak.

**Önerilen model:** yuva kaydı üç alanlı olur — **konum** · **ölçü** (genişlik × yükseklik) ·
**cihaz** (masaüstü / mobil). Reklamverenin adı yuvaya değil **kampanyaya** yazılır;
kampanyalar İlan & Reklam bölümünde durur. Böylece reklamveren değişince yuva yerinde kalır
ve "hepsiburada 4" gibi kayıtlar oluşmaz.

---

## 15. Konu Takibi — dosya, kronoloji, aday

### Hassas uyarı ilk sırada

Konunun `hassas.uyari` metni, konu sütununun **ilk öğesi**. Bozbey dosyasında bu şu:

> Yargılama sürüyor. Masumiyet karinesi korunacak: kesin hüküm dili kullanılmaz,
> Bozbey'in suçlamaları reddettiği her haberde belirtilir.

Bu konuya haber bağlayan editörün göreceği ilk şey bu olmalı; bağlama düğmesinin yanında da
"bağlarsanız masumiyet karinesi uyarısı habere iliştirilir" notu var.

### Onaysız bağlama yok — korundu

`konu_eslestirme.py` davranışı birebir taşındı: araç **aday listeler ve gerekçe yazar**,
bağlama yalnız açık düğmeyle olur. "Yoksay" hiçbir bağlama yapmadan adayı kapatır.

**Ekrandaki puanlar gerçek.** `arac/konu_eslestirme.py` çalıştırılarak alındı, elle yazılmadı:

| Aday | Skor | Gerekçeler |
|---|---|---|
| **Konu:** Bozbey süreci | **100 · güçlü** | 2 ortak özel isim (Bozbey CHP, Mustafa Bozbey) · 6 konu anahtarı · aynı kategori · aynı ilçe · son gelişme 0 gün önce |
| **Haber:** Bozbey dosyasında süreç nasıl işleyecek? | 92 · güçlü | 1 ortak özel isim · 4 ortak etiket · aynı kategori · aynı ilçe |
| **Haber:** Tutukluluk, görevden uzaklaştırma, istifa | 56 · olası | 1 ortak özel isim · 1 ortak etiket · aynı kategori · aynı ilçe |

Eşikler motordan: `OLASI_ESIK = 35`, `GUCLU_ESIK = 60`.

> **Motoru sınarken düştüğüm hata — not:** `parmak_izi()` metni `kaynak` sözlüğünün
> `orijinal_baslik` / `orijinal_spot` / `orijinal_govde` alanlarından okur, taslağın kendi
> alanlarından değil. İlk denememde yanlış anahtar verdiğim için tüm konular eşiğin altında
> kaldı ve motoru hatalı sandım. Motor sağlam; **çağırırken alan adlarına dikkat.**

### Yayın bloğu üretici

Panel tasarım dosyalarını **düzenlemez** — yapıştırılacak HTML üretir. Ekran, konunun
kronolojisinden `tasarim-3-haber-detay.html` içindeki `<div class="kutu-zaman">` bloğunu
üretiyor ve panoya kopyalatıyor.

**Doğrulandı:** üretilen blok, tasarım dosyasındaki gerçek blokla (boşluk normalize
edildikten sonra) **birebir aynı** — 1.055 karakter, karakter karakter eşleşiyor.
Tarih gösterimleri de korundu (`2026-05` → "Mayıs — Temmuz 2026").

### Konu künyesi

Kategori · ilçe · durum · **kişiler** · **kurumlar** · **anahtarlar** yüzeyde.
Anahtarlar eşleştirme motorunun girdisi olduğu için ayrıca belirtiliyor.
Dört dosya da listede: Bozbey süreci (hassas) · Su ve kuraklık dosyası ·
Yeni müze binası · Ali Osman Sönmez Devlet Hastanesi.

---

## 16. İlan & Reklam

Dört sekme: **Resmi ilanlar · Kampanyalar · Gazete listesi · Kendi yayınlarım.**
Bölümün tamamı oturumdaki **Editör** rolü için salt okunur — resmi ilan girme ve reklam
kampanyası yetkisi İlan Sorumlusu ve Yayın Yönetmeni'nde (§11).

### Resmi ilanlar

24 gerçek kayıt (ID 1646–1718): **14 İHALE, 10 TEBLİGAT.** İki kişi giriyor —
Coşkun SAİTOĞLU ve Tulga AYKAÇ; rol matrisindeki İlan Sorumlusu ayrımının kanıtı bu.

**Dört ilan türü tanımlı:** İCRA · İHALE · TEBLİGAT · PERSONEL ALIMI. Kayıtlı 24 ilanın
hiçbiri İCRA veya PERSONEL ALIMI değil, ama bu türler **yasal karşılığı olduğu için
korundu** — kullanılmıyor diye kaldırılmadı.

### Kampanya yuvaya bağlanır, yuvayı tanımlamaz

Reklam **yuvalarının** tanımı (konum · ölçü · cihaz) Sayfa Düzeni'nde (§14).
Burada yalnız hangi reklamverenin hangi yuvada, hangi tarihler arasında olduğu tutulur.
Mevcut panelde bu ayrım olmadığı için "hepsiburada 2/3/4" gibi yuvalar açılmış;
ayrım kurulunca reklamveren değişse de yuva yerinde kalır.

> Kampanya satırları **demodur** — mevcut panelin Reklam Yönetimi ekranında kampanya listesi
> var ama dökümde satırları yakalanamadı. Bağlı oldukları **yuva adları gerçek**.

### Gazete listesi ve Kendi yayınlarım

Karar gereği (§18, madde 2-3) ikisi de ayrı ekran değil, bu bölümün sekmeleri:

- **Gazete listesi** — 17 kayıt, hepsi BIK yayın kodlu. **Bursa Hakimiyet: `YYN-000132`**;
  gazetenin kendi yayın kodu ve resmi ilan yükümlülüklerinin dayanağı, değiştirilmemeli.
  Ekranda ayrı renkle işaretli.
- **Kendi yayınlarım** — boş durum ekranı. Mevcut panelde "Kayıt bulunamadı." diyor;
  `my_newspapers_add/edit` uçları duruyor ama kullanılmıyor.

---

## 17. Ayarlar — taksonomi ve hesap

Üç sekme: **Taksonomi · Kullanıcılar & Roller · Hesap.** Kullanıcılar ve Roller kendi
ekranlarında; bu sekme onlara bağlanır, kopyalamaz.

### Kaynakların üçe bölünmesi

348 kayıt üç kutuya ayrıldı: **Ajans** (4 kalem, kapalı liste) · **Dış yayın** (~263) ·
**Kendi muhabirimiz** (~75).

> **Bölme tam otomatik yapılamıyor — ölçüldü.** 348 kaydı ad kalıbına göre ayırmayı denedim;
> iki kelimeli özel adlar kişi sanılıyor ama bir kısmı yayın: **Çağdaş Kocaeli**,
> **Bursa Tanık**, **Kocaeli Gündem**, **Gemlik Basın**. Bu yüzden dış yayın ve muhabir
> sayıları **yaklaşık** verildi; son ayrımı editör onaylamalı. Ajans tarafı kesin.

Üç sorun bloğu ve çözümleri ekranda:

| Sorun | Sayı | Çözüm |
|---|---|---|
| Birebir tekrar | 6 | Birleştirilir, bağlantılar kalan kayda taşınır |
| Birleşik kayıt | 7 | **Çoklu seçim gelince gerek kalmıyor** — `İHA, DHA` yerine ikisi işaretlenir |
| Muhabir/yayın karışıklığı | 2 tablo | "Kendi muhabirimiz" kullanıcı tablosundan beslenir, ayrı kaynak kaydı tutulmaz |

Son maddenin somut örneği: **Coşkun Saitoğlu** hem kaynak listesinde hem editör listesinde
("Coşkun SAİTOĞLU") — aynı insan, iki tablo, iki yazım.

### Kategoriler — karar uygulandı

Ekran artık **birleşme haritası** gösteriyor: 37 kayıt → 15 ad. Her satırda kaç kayıttan
toplandığı (`3 → 1`), korunan haber slug'ı (kilitli), foto ve video kategori kimlikleri,
ve sitemap'ten sayılmış yayındaki haber sayısı var.

Kararın ayrıntısı ve gerekçesi §18'de. Ekrandaki karşılıkları:

- **Slug salt okunur.** Kilit işareti ve "dondurulmuş" açıklaması taşıyor.
- **Çöp kayıtlar ayrı:** Foto altındaki `HABER`, Video altındaki `Video Galeri Arşivi`.
- **`katid` uyarısı** ayrı kutuda; ölçülemeyen kimlikler "ölçülmedi" diye işaretli.
- **"Birleştirmeyi uygula"** düğmesi var, Editör rolüne kapalı.

Önceki turlarda bu bölümde "karar verilmedi" bloğu vardı ve birleştirme düğmesi
**bilerek yoktu**; karar gelince blok kararla, boşluk akışla değiştirildi.

### Hesap

Parola · 2FA · oturum kayıtları. Mevcut panelin Log Kayıtları ekranı buraya alındı —
ayrı menü maddesi olacak kadar sık bakılan bir yer değil. 2FA'nın iki yöntemi
(Google Authenticator, SMS) ve parmak izine bağlı oturum davranışı korundu.

---

## 18. Karara bağlananlar

Önceki turda "varsayımla ilerlenebilir" diye işaretlenenler karar seviyesine yükseltildi.

| # | Konu | Karar | Gerekçe |
|---|---|---|---|
| 1 | **Duyurular** | Ayrı ekran yok; Ayarlar altında "Sistem duyuruları" rafı | URL `system-announcements`, megafon ikonu, hedef kitle alanı yok — sağlayıcının sürüm duyurusu, gazetenin aracı değil |
| 2 | **Kendi Yayınlarım** | Ayrı ekran yok; İlan & Reklam altında sekme | Liste boş, ama `my_newspapers_add/edit` uçları var — BIK'e karşı kendi künye kaydı, kullanılmıyor |
| 3 | **Gazete Listesi** | Ayrı ekran yok; İlan & Reklam'ın referans tablosu | 17 kayıt, hepsi YYN kodlu; resmi ilan yayın haklarının kod defteri |
| 4 | **Canlı anlatım** | Yeniden icat edilecek; mevcut Son Dakika davranışı korunmayacak | En yeni kayıt 2025-12-20 — sekiz aydır kullanılmıyor, korunacak alışkanlık yok |
| 5 | **Bot modülü** | **Kapsam dışı** | Kanıt yalnızca menü betiğindeki ad; ekran, alan ve akış hakkında hiçbir veri yok. Kapsamı büyütmeye değmez. Ajans akışının oradan geldiği doğrulanırsa ayrıca ele alınır |
| 6 | **`formControl` muafiyeti** | Mesele kapandı | Yeni panelde her alan gerçekten doğrulanıyor; muafiyet listesinin ne yaptığı artık önemsiz |
| 7 | **Duyuru listesinin boşluğu** | Özellik ölü sayılmadı | Filtre son 30 güne kilitli; boşluk kanıt değil |

### Kategori kararı — verildi

**Karar: adları birleştir, slug'ları dondur.** (25 Ağustos 2026)

Panelde **tek paylaşımlı taksonomi** kurulur: "BURSA" üç ayrı kayıt değil, bir kategori olur.
İçerik türü kategorinin özelliği değil, **kaydın** özelliğidir — aynı kategori hem haberde
hem fotoda hem videoda kullanılır. 37 kayıt 15 ada toplanır.

**Her kategorinin mevcut URL slug'ı olduğu gibi kalır.** Hiçbir adres değişmez, yönlendirme
tablosu gerekmez, sitemap yenilenmez.

| Reddedilen seçenek | Neden |
|---|---|
| Tam temizlik + 301 yönlendirme | 556.824 adresi riske atıyor |
| Hiç dokunmama | 37 kayıtlık kopyalanmış taksonomi kalıyordu |

**Neden slug'lar dağınık kaldı** — ileride sorulursa cevabı burada:

Slug düzensizliği veri olarak duruyor. `bursa-da-spor` (3.331 adres) yanında
`bursada-spor` (4 adres, yalnız 2022-01) gibi artıklar var ve **temizlenmedi**, çünkü
temizliğin bedeli o adreslerin kırılması. Kategori slug'ı `/{kategori}/{slug}-{id}`
deseninin ilk parçası; adı değiştirmek adresi değiştirir. Karar, **düzeni panelde kurup
adresleri olduğu gibi bırakmak** oldu.

Ekrandaki sonuçları:

- Mevcut kategorilerde **slug salt okunur** — kilit işaretiyle gösteriliyor,
  yanında "dondurulmuş" açıklaması var
- Yeni açılan kategoride slug serbest, **kaydedildikten sonra kilitlenir**
- Birleşme haritası 15 satır: hangi adın kaç kayıttan toplandığı (`3 → 1`),
  hangi slug'ın korunduğu, foto ve video kategori kimlikleri
- Çöp kayıtlar ayrı işaretli: Foto altındaki `HABER`, Video altındaki `Video Galeri Arşivi`
- **Birleştirmeyi uygula** düğmesi var ama Editör rolüne kapalı (taksonomi düzenleme
  Yayın Yönetmeni'nde)

### katid — birleştirmede kaybolmaması gereken parça

Foto ve video adresleri `/galeriler/{slug}-{katid}/…` deseninde. Adresi taşıyan şey slug
değil, **slug + kategori kimliği**. Adlar tek kategoriye toplanırken bu kimlikler
**tür bazında korunmalı**; yoksa foto ve video adresleri kırılır.

> **Ölçüm sınırı — dürüstlük notu:** panel dökümünden yalnız **iki** `katid` okunabildi:
> foto `bursa-208`, video `bursa-308`. Diğer kategorilerin `katid` değerleri dökümde yok;
> ekranda ve tabloda "ölçülmedi" diye işaretli ve **göç öncesi veritabanından okunmalı**.
> İki örnek 2xx/3xx düzenine benziyor ama tek gözlemden kural çıkarılmadı.

---

## 19. Hukuki teyit bekliyor

> Bu bölüm bir geliştirme notudur. **Ekranda kullanıcıya uyarı gösterilmiyor** — editörün
> işi değil. Gerçek yayına geçmeden önce doğrulatılması gereken tek yer burası.

**Konu: Meta Yazar Bilgisi eşlemesi (§7).**

Gazete resmi ilan alıyor; bu alan BIK tarafına karşı yasal sonuç doğuruyor ve mevcut panelin
kendi ipucu satırı "resmi ilan alan müşterilerin doldurması zorunludur" diyor.

Kurduğum eşleme ve dayandığı akıl yürütme:

| Eşleme | Gerekçem |
|---|---|
| Ajans → **Haber Ajansı** | Değerin adı zaten kaynağın türünü söylüyor; ajanstan gelen içerik fikir işçisi eseri sayılmaz |
| Dış yayın → **Alıntı/İktibas** | Başka bir yayından kaynak göstererek aktarma, Basın Kanunu'nun iktibas çerçevesine giren durumdur |
| Kendi muhabirimiz → **Fikir İşçisi** | Gazetenin kadrolu gazetecisinin ürettiği içerik; 212 sayılı düzenlemenin kapsadığı çalışan tanımı |
| Varsayılan → **Haber Ajansı** | Kaynak türü varsayılanı Ajans olduğu için; masa hacminin çoğunluğu ajans kaynaklı |

**Doğrulatılması gerekenler:**

1. Üç eşlemenin de BIK pratiğine uygun olup olmadığı — özellikle "Dış yayın → Alıntı/İktibas"
   ayrımının "İçerik Aktarımı"ndan nerede ayrıldığı. Anlaşmalı içerik ortağı ile serbest
   iktibas arasındaki sınırı ben editoryal olarak çizdim; hukuki tanımı farklı olabilir.
2. Alanın **resmi ilan almayan haberlerde de zorunlu olup olmadığı**. Şu an isteğe bağlı
   bırakıldı; mevcut panelde de doğrulamada muaftı.
3. "Haber Merkezi" ile "Fikir İşçisi" arasındaki seçimin kime ait olduğu — imzasız derleme
   haberlerde hangisinin doğru işaret olduğu.
4. Varsayılan değerin bulunmasının kendisinin risk yaratıp yaratmadığı. Alan boş bırakılamıyorsa
   varsayılan iyidir; ama yanlış varsayılan, boş alandan daha kötü olabilir.

**Bu doğrulanana kadar:** eşleme çalışır durumda, editör her zaman üzerine yazabiliyor,
ve altı değerin hiçbiri listeden çıkarılmadı.

---

## 20. Ölçülen sayılar

| Ne | Değer | Nereden |
|---|---|---|
| Yayındaki haber | 556.824 | sitemap dökümü, tam sayım |
| Panel haber sayacı | 1.044.757 | Genel Bakış |
| Aradaki fark | ~488.000 | Büyük olasılıkla Pasif + Arşiv + Silinmiş (**çıkarım**) |
| Günlük üretim | **~200-240 haber/gün** | son 14 ayın ortalaması |
| 2021 üretimi | ~470/gün | hacim yarılanmış |
| Manşet kaydı | ~1.900 | 76 sayfa × 25; append-only |
| Reklam alanı | **50** | `getZone` |
| Kayıtlı kullanıcı | 17 (4'ü "Administrator") | editör süzgeci |
| Köşe yazarı | 15 | `getAuthorsEditorialist` |
| Kaynak | 348 (342 benzersiz) | `source_news_id` |
| Kategori kaydı | 37 · 15 benzersiz ad · 10 ortak | üç açılır liste |
| Bildirim açılma oranı | **~%0,2** | 22.683 hedef → 46 açan |
| Depolama | 10 GB ücretsiz, **261 GB aşım** | Genel Bakış |
| Son Dakika son kaydı | 2025-12-20 | sekiz aydır kullanılmıyor |

---

## 21. Dosya anatomisi ve kırılma noktaları

### Ortak düzen

```
<head>  Google Fonts + <style>   (:root → kabuk → bileşen → ekrana özgü → @media)
<body>  .atla
        header.bant             logo · Yönetim Paneli · Demo rozeti · kullanıcı
        .panel
          nav.kenar             7 bölüm; aktif olan aria-current="page"
          main.calisma
            .sayfa-bas          kırıntı yolu · başlık · rozet · eylemler
            ekrana özgü gövde
        .duyuru                 role="status"
<script> tek IIFE, Türkçe işlev adları
```

### Kırılma noktaları — başsız Chrome'da ölçüldü

| Genişlik | Kenar çubuğu | Haber Ekle | Bugün | Liste / kuyruk | Sayfa Düzeni | Konu Takibi |
|---|---|---|---|---|---|---|
| 1440px | 212px, tam | 823 + 316 | 4 iş kartı · 2 kolon | tablo tam · kuyruk 2 kolon | 3 slot yan yana | liste + detay |
| 1180px | 212px, tam | tek kolon | 2 iş kartı · 1 kolon | kuyruk tek kolon | slotlar alt alta | tek kolon |
| 880px | **60px, simge** | tek kolon | 2 iş kartı | tablo kendi kutusunda kayar | şema daralır | tek kolon |
| 620px | 60px | dolgu daralır | 1 iş kartı | süzgeç alanları alt alta | şema daralır | tek kolon |
| 380px | 60px | tek kolon | 1 iş kartı | toplu şerit sarar | **şema kutuları alt alta** | tek kolon |

**On ekranın hiçbirinde yatay taşma yok** — üç genişlikte ölçüldü ve taşan öğe araması
kaydırma kutusu içindekileri ayıklayacak şekilde yapıldı. Geniş tablolar kendi
`.tablo-sar` kutusunda kayıyor (380px'te kapsayıcı 230px, içerik 680px, `overflow-x:auto`);
sayfa gövdesi hiçbir genişlikte kaymıyor. Sayfa Düzeni'ndeki anasayfa şeması 560px altında
tek sütuna iniyor.

### Çalışan etkileşimler — ölçülerek doğrulandı

| Ne | Ölçülen sonuç |
|---|---|
| Slug üretimi (Türkçe harfler) | "Bursa Kestel'de 40 yıllık sulama sorunu çözülüyor" → `bursa-kestel-de-40-yillik-sulama-sorunu-cozuluyor` |
| Adres önizlemesi | `.../bursa/bursa-kestel-de-...-{id}` — kategori segmenti canlı |
| Karakter sayaçları | başlık 49/60 · spot 160 sınırı |
| Paragraf sayacı | 2 paragraf |
| Hazırlık ölçeri | 3/6 |
| **Doğrulama gerçekten engelliyor** | "Yayınlanamaz — eksik: spot, etiket." · 2 alan kırmızı · odak ilk eksiğe gitti |
| Kaynak türü → liste + meta türetimi | "Kendi muhabirimiz" → 6 seçenek, Meta Yazar = Fikir İşçisi |
| Hazırlık ekseni | Yalnız durum = Pasif iken görünüyor |
| Konu bağlama | Yalnız düğmeye basınca bağlandı; hassas konu uyarısı göründü |
| **Akış:** daralt-ve-bul | Açılışta liste gizli; hızlı girişten sonra süzgeç + liste geldi |
| **Akış:** tür süzgeci | "video" → 20 kayıttan 3'e indi, çip göründü, temizleyince 20'ye döndü |
| **Akış:** toplu seçim | 2 seçim → şerit açıldı; "hepsini seç" → 20 |
| **Akış:** kategori uyarısı | Seçili sayıyı gösteren adres uyarısı açıldı |
| **Akış:** yetki kilidi | "Manşete al" `aria-disabled`, basınca gerekçe duyuruldu |
| **Etkileşim:** gerekçesiz düzenleme | Engellendi, hata görünür oldu |
| **Etkileşim:** gerekçeli düzenleme | Kaydedildi, metin güncellendi |
| **Etkileşim:** klavye | Odak alan dışındayken <kbd>A</kbd> onayladı, sayaç 1/7 → 2/7 |
| **Etkileşim:** eksik gönderim | Haber/başlık yokken bildirim gönderilmedi |
| **Sayfa Düzeni:** slotlar | 3 slot, 13 şema kutusu, ana manşet yaşı "2 sa 51 dk" amber |
| **Sayfa Düzeni:** envanter | 50 alan satırı, 50 tespit çipi |
| **Konu Takibi:** hassas şerit | Konu sütununun **ilk öğesi** olduğu ölçüldü |
| **Konu Takibi:** aday | 3 aday, güçlü skor "100 · güçlü" (motordan) |
| **Konu Takibi:** onaysız bağlama yok | "Yoksay" bağlamadan kapattı, "Bağla" açık düğmeyle bağladı |
| **Konu Takibi:** yayın bloğu | 1.192 karakter üretildi; tasarım-3'teki blokla birebir |
| **İlan & Reklam:** süzgeç | TEBLİGAT → 24 kayıttan 10'a indi, temizleyince 24 |
| **İlan & Reklam:** BIK | `YYN-000132` ayrı renkte, "Bizim" rozetiyle |
| **Ayarlar:** birleşme haritası | 15 satır · 15 kilitli slug · 23 "ölçülmedi" · 2 çöp kayıt |
| **Ayarlar:** birleştirme kilidi | Düğme var, `aria-disabled`, basınca "Yayın Yönetmeni rolünde" |
| **Ayarlar:** sekmeler | Kullanıcılar & Roller sekmesi iki bağlantı kartı, kopya yok |

### Erişilebilirlik denetimi (on ekran)

- Etiketsiz girdi: **yok** · hedefsiz `label for` / `aria-*`: **yok** · `alt`sız `<img>`: **yok**
- Boş metinli bağlantı: **yok** · etiket dengesi: tamam
- Tablolarda `<caption>` ve `th[scope]` tam
- Tablolarda `<caption>`, sekmelerde `role="tab"` + `aria-selected` + `aria-controls`
- Kenar çubuğundaki bekleyen-yorum rozeti ekran okuyucuda "Etkileşim, 7 bekleyen yorum" okunur
- `prefers-reduced-motion`, `:focus-visible`, `aria-live`, `aria-current`, `aria-pressed`,
  `aria-expanded` on dosyada da yerinde
- Sınıf adlarının tamamı Türkçe; İngilizce sınıf yok
- `:root` dışında hex/rgba renk **yok**
- Dış kaynak yalnız Google Fonts


### Bütünlük turu — on ekran birlikte

Parçalar ayrı ayrı üretildiği için sonda bir kez bütün olarak ölçüldü:

| Denetim | Sonuç |
|---|---|
| `:root` değişken seti | **40 değişken, on ekranda birebir aynı** |
| Kenar çubuğu gezinmesi | **13 bağlantı, on ekranda birebir aynı** |
| Kalan `#` bağlantı | **0** |
| `aria-current` işareti | Her ekranda 1 veya 2 (üst bölüm + alt madde) |
| Kabuk bileşenleri | `.atla` · `.bant` · `.kenar` · `.sayfa-bas` · `.duyuru` · `prefers-reduced-motion` · `:focus-visible` · `lang="tr"` · `noindex` — **onunda da tam** |
| Kaçak renk / İngilizce sınıf / kırık bağlantı / dış kaynak | **0** |

**Bütünlük turunda bulunan ve düzeltilen tutarsızlık:** rol matrisine göre Editör'ün
yapamadığı **yedi iş** var, ama gating yalnız ikisinde görünüyordu (Akış'ta "Manşete al",
İlan & Reklam'da bölümün tamamı). Sayfa Düzeni, Ayarlar, Roller ve Kullanıcılar ekranları
"Yönetici ekranı" rozeti taşıyor ama Editör'ün serbestçe işlem yapmasına izin veriyordu.
Dördüne de aynı `.yetki-serit` bileşeni eklendi ve stil ortak `LISTE_STIL`e taşındı
(önce yalnız İlan & Reklam'da tanımlıydı).

Gating'in son hâli:

| Ekran | Kilit | Gerekli rol |
|---|---|---|
| Bugün · Haber Ekle · Etkileşim · Konu Takibi | yok | Editör'ün yetkisi var |
| Akış | "Manşete al" düğmesi | Sayfa Sekreteri / Yayın Yönetmeni |
| Sayfa Düzeni | bölümün tamamı | Sayfa Sekreteri / Yayın Yönetmeni |
| İlan & Reklam | bölümün tamamı | İlan Sorumlusu / Yayın Yönetmeni |
| Ayarlar · Roller · Kullanıcılar | bölümün tamamı | Yayın Yönetmeni |

**Karar:** kilitli ekranlar menüden gizlenmedi, **salt okunur gösterildi**. Gerçek sistemde
gizlemek de savunulabilir; demoda görünür kalması rol modelinin çalıştığını gösteriyor.

### Yapılmayanlar (bilerek)

Görsel yükleme ve kırpma · galeri seçici · ilgili haber seçici · zengin metin editörü ·
gerçek kaydetme · gerçek kaynak ayıklama · rol ve kullanıcı düzenleme formları ·
sayfalama (tek sayfa veri) · toplu işlemlerin gerçekten uygulanması ·
kuyruğun 2-7. yorumları (dökümde metinleri yok) · manşet slotu değiştirme seçicisi ·
kampanya ekleme formu · parola ve 2FA işlemleri.

---

## 22. Sıradaki işler

1. ~~Alan sözleşmesi tablosu~~ — §4
2. ~~Haber Ekle~~ — `panel-haber-ekle.html`
3. ~~Bugün~~ — `panel-bugun.html`
4. ~~Roller ve Kullanıcılar~~ — `panel-roller.html`, `panel-kullanicilar.html`
5. ~~İçerik / Akış~~ — `panel-akis.html`
6. ~~Etkileşim~~ — `panel-etkilesim.html`
7. ~~Sayfa Düzeni~~ — `panel-sayfa-duzeni.html`
8. ~~Konu Takibi~~ — `panel-konu-takibi.html`
9. ~~İlan & Reklam~~ — `panel-ilan-reklam.html`
10. ~~Ayarlar / Taksonomi~~ — `panel-ayarlar.html`

**On ekranın hepsi yapıldı. Kenar çubuğunda `#` bağlantı kalmadı.**

Sırada kalan iki madde (ekran değil, karar ve veri):

- **Meta Yazar Bilgisi eşlemesinin hukuki teyidi** — canlıya geçmeden bir kez (§19)
- **Site yönü seçilince Sayfa Düzeni'nin somutlaşması** — nasıl olacağı §14'te yazılı

Kategori birleştirme kararı **verildi ve kapandı** (§18).
İlçe slug kuralı **doğrulandı ve kapandı** (§8) — panelin listesi kanonik,
tasarım tarafında 7 ilçe eklenecek.

---

## 23. Dikkat

- `D:\bursa-hakimiyet-arsiv\` **salt okunur** — tarama çalışıyor, altına yazma
- **Kategori slug'ları dondurulmuştur** — mevcut hiçbiri değiştirilemez (§18)
- Kabuk her panel dosyasına gömülü: **birinde değişen hepsinde değişir**
- Panel dosyaları `noindex, nofollow` taşır — demo, aramaya çıkmamalı
- Meta Yazar Bilgisi eşlemesi hukuki teyit bekliyor (§19)
