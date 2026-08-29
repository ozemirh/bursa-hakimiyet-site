# Ürün Planı — Bursa Hakimiyet

26 Ağustos 2026'da kullanıcının verdiği düzen şeması ve panel kararıyla açıldı.
**Bu belge bağlayıcıdır.** Plandan sapma gerekiyorsa önce burası güncellenir.

Önceki bağlam: `CLAUDE.md` (proje kuralları), `DEMO-NOTLARI.md` (tasarım notları),
`PANEL-NOTLARI.md` (panel arkeolojisi ve alan sözleşmesi).

---

## 0. Kararlar (kullanıcı verdi, tartışmaya kapalı)

| Karar | İçerik |
|---|---|
| **Ürün** | Demo değil, gerçek ürün. |
| **Tek yön** | Yalnız **Yön 1 (klasik)**. `tasarim-2-*` ve `tasarim-3-*` dondurulmuş. |
| **Kapsam** | Tam CMS — sağlayıcı değiştirilecek. |
| **Panel** | **Mevcut yönetim paneli birebir kopyalanacak**, gerekirse ek özellik. |
| **Göç** | Yalnız kazımayla erişilebilen ~600.000 kayıt. Ulaşılamayanlar es geçildi. |
| **Mimari** | Django + PostgreSQL, sunucu tarafında render. |

---

## 1. Anasayfa düzeni — klasik yön

Kullanıcının tarif ettiği sıra. **Yukarıdan aşağıya bağlayıcı.**

```
┌ SOL ┐                 içerik sütunu                  ┌ SAĞ ┐
│ban  │  ┌ LOGO ┐ KATEGORİ BANDI (10 kalem)           │ban  │
│ner  │  └───────┘ …………………… [ara] [☰ MENÜ]           │ner  │
│     │   ↑ 29 Ağu 2026: logo bandın İÇİNDE             │     │
│     │  SON DAKİKA BANDI                              │     │
│     │  REKLAM 1100×150                               │     │
│     │  [haber][haber][haber][haber]  ← 4 yan yana    │     │
│     │  ┌──────────────────┬──────────────┐           │     │
│     │  │ ANA MANŞET       │  REKLAM      │           │     │
│     │  │ 15 SLAYT         ├──────────────┤           │     │
│     │  │ (büyük)          │ 5 SLAYT      │           │     │
│     │  │                  │ (küçük)      │           │     │
│     │  └──────────────────┴──────────────┘           │     │
│     │  DÖVİZ BANDI                                    │     │
│     │  BASIN İLAN                                     │     │
│     │  ┌────────────────────┬─────────────────┐      │     │
│     │  │ HABER KUTULARI     │ 3 SEKME:        │      │     │
│     │  │ 2 sütun × 5 sıra   │ hava/namaz/     │      │     │
│     │  │                    │ eczane          │      │     │
│     │  │                    ├─────────────────┤      │     │
│     │  │                    │ YAZARLAR        │      │     │
│     │  │                    │ (son yazı       │      │     │
│     │  │                    │  başlığıyla)    │      │     │
│     │  │                    ├─────────────────┤      │     │
│     │  │                    │ EN ÇOK OKUNAN   │      │     │
│     │  └────────────────────┴─────────────────┘      │     │
│     │  ┌──────────┬────────────────────────────┐     │     │
│     │  │ PUAN     │ BURSASPOR HABERLERİ        │     │     │
│     │  │ DURUMU   │ (geniş)                    │     │     │
│     │  │ + o hafta│                            │     │     │
│     │  │   skoru  │                            │     │     │
│     │  │ (dar)    │                            │     │     │
│     │  └──────────┴────────────────────────────┘     │     │
│     │  GALERİLER                                      │     │
│     │  VİDEOLAR                                       │     │
│     │  VİZYONDA NELER VAR                             │     │
└─────┘                                                 └─────┘
```

### Bileşen sözleşmesi

| # | Bileşen | Ayrıntı |
|---|---|---|
| 1 | **Yan bannerlar** | Sayfanın üst kısmında iki yanda. Mevcut yuva envanterinde `-Sol pageskin1..4-` ve `-Sağ pageskin1..4-` (160×600) karşılığı var. |
| 2 | **Logo** | Sol üstte. **29 Ağustos 2026'da kendi şeridinden kategori bandının içine alındı** — şerit 93 px idi ve %82'si boştu (ölçüm: bant 1100 px, logo 196 px). Yanında hâlâ arama/abone kutusu yok; arama bandın sağ ucunda. Kazanç: içeriğin başlangıcı 379 → 284 px. Logo artık **yapışkan bantta**, yani sayfa kaydırılırken de görünür. |
| 3 | **Kategori bandı** | **Tam 10 kalem:** Yazarlar · Bursa · Bursaspor · Gündem · Ekonomi · Dünya · Spor · Magazin · İlçeler · Resmî İlan. Kalabalıklaştırma. **Arama ve menü düğmesi bandın içinde**, sağ uçta: önce arama, onun sağında menü düğmesi (26 Ağustos kararı). **Dar ekranda (≤1000 px) dördü kalır:** Bursa · Bursaspor · Gündem · Spor; kalan altısı gizlenir ama **DOM'dan düşmez** (29 Ağustos 2026). Öncesinde liste bütünüyle `display:none` idi ve 360 px'te görünen kategori sayısı **sıfırdı**. |
| 4 | **Son dakika bandı** | Kategori bandının hemen altında. |
| 5 | **Reklam** | **1100×150**, tam genişlik. |
| 6 | **Dört haber kutucuğu** | Yan yana, eşit. |
| 7 | **Ana manşet** | Sol/büyük alan, **15 slayt**. |
| 8 | **Sağ sütun (manşet hizası)** | İki satır: üstte **reklam**, altında **5 slaytlı** ikinci haber alanı — manşetten belirgin **daha küçük**. |
| 9 | **Piyasa bandı** | **Tam 5 kalem:** Dolar · Euro · Sterlin · Gram altın · BIST 100. Sekiz kalemli eski bant 1140 px altında taşıyordu; beş kalem her genişlikte sığar. **27 Ağustos: yeri değişti** — manşetin altından **sayfanın en üstüne** (dört haber kutucuğundan önce) alındı ve koyu lacivert zeminli, iri rakamlı bir şeride dönüştürüldü. |
| 10 | **Basın ilan** | = **Resmî ilan.** Editoryal içerik (İCRA · İHALE · TEBLİGAT · PERSONEL ALIMI), reklam yuvası değil. BIK yükümlülüğü. **27 Ağustos: yeri değişti** — döviz bandının altından **haber kutularının altına**, Bursaspor alanının hemen üstüne alındı; üç sütundan **iki sütuna** indirildi (üç sütun dar ekranda okunmuyordu). |
| 11 | **Haber kutuları** | **2 sütun × 5 sıra = 10 kutu.** |
| 12 | **Sağ ray — sekmeler** | 3 sekme: hava · namaz · eczane. Mevcut klasik demodaki davranış korunur. |
| 13 | **Sağ ray — yazarlar** | Yazar adı **ve son yazısının başlığı**. |
| 14 | **Sağ ray — en çok okunanlar** | Kullanıcı "uygun bir yere" dedi; sağ raya, yazarların altına konuyor. |
| 15 | **Bursaspor alanı** | Solda **dar**: **4 lig** puan durumu (Süper · 1. · 2. · 3.) + o haftaki Bursaspor maç skoru. Sağda **geniş**: Bursaspor haberleri. |
| 16 | **Galeriler** | Bursaspor alanının altında. |
| 17 | **Videolar** | Galerilerin altında. |
| 18 | **Vizyonda neler var** | Videoların altında. API ile beslenecek. |

### Canlı veri gerektiren bileşenler

Bunlar statik yapılamaz; kaynağı belirlenmeli.

| Bileşen | Kaynak durumu |
|---|---|
| Döviz bandı | Bir piyasa servisine bağlanacak. |
| Hava durumu | Servis gerekir. |
| Namaz vakitleri | Diyanet kaynaklı hesap/servis. |
| Nöbetçi eczane | İl eczacı odası kaynağı; çoğu ilde API yok, elle giriş gerekebilir. |
| Puan durumları (**4 lig**) | Spor veri servisi gerekir. 2. ve 3. Lig grup usulü — hangi grup gösterilecek kararı henüz yok. |
| Bursaspor maç skoru | Aynı kaynak. |
| Vizyondaki filmler | API gerekir; Türkiye vizyon takvimi veren kaynak doğrulanmalı. |

**İlk aşamada hepsi gerçekçi yer tutucuyla kurulur**, veri kaynağı ayrı bir iş kalemidir.

---

## 2. Yönetim paneli — birebir kopya

Kullanıcının kararı: mevcut panel **birebir kopyalanacak**, gerekirse ek özellik.

**Bu, daha önce çıkardığımız 21→7 yeniden yapılandırmayı geçersiz kılar.**
`panel-*.html` dosyaları (10 ekran) artık **referans**, hedef değil.
`PANEL-NOTLARI.md`deki **alan sözleşmesi ve ölçümler geçerli kalır** — asıl
değerleri buydu.

### Uyarı — hukuki sınır

"Birebir kopya" iki şey olabilir:

1. **İşlev ve akışın birebir kopyası** — aynı ekranlar, aynı alanlar, aynı iş akışı,
   **bizim kendi kodumuzla**. Güvenli yol, önerilen budur.
2. **Sağlayıcının kodunun kopyalanması** — HTML/CSS/JS'in alınması. Lisanslı bir
   üründen kod almak telif sorunudur; sözleşme bunu neredeyse kesin yasaklar.

**Plan 1'i uygular.** Ekip açısından fark yok: aynı ekran, aynı yerleşim, aynı
alışkanlık. Kullanıcı 2'yi istiyorsa açıkça söylemeli.

### Kopyalanacak ekranlar

Genel Bakış · Duyurular · Tüm Haberler · Son Dakika · Manşetler · Foto Galeri ·
Videolar · Yorumlar · Köşe Yazıları · Köşe Yazarları · Reklam Yönetimi ·
Gazete Listesi · Kendi Yayınlarım · Resmî İlanlar · Şifre · 2FA · Log Kayıtları ·
Kategoriler · Bildirimler · **Haber Ekle** · (menüde görünmeyenler) Roller ·
Kullanıcılar · Bot modülü.

Kullanıcının panele erişimi var → eksik ekranların dökümü alınabilir.

### Kopyalarken yine de düzeltilecekler

Birebir kopya "hatayı da kopyala" demek değil. Ölçülmüş, veri bütünlüğünü
bozan kalemler:

| Sorun | Neden düzeltilmeli |
|---|---|
| **4 hesap "Administrator" adını paylaşıyor** | Log kaydı kimin ne yaptığını söyleyemiyor. 2FA'lı bir sistemde kabul edilemez. |
| **Kaynak listesi 348 kayıt**, 6 tekrar, 7 birleşik | Çoklu seçim yokluğundan doğan kombinasyon patlaması. |
| **Taslak durumu yok** | Pasif hem "bitmedi" hem "yayından çekildi" demek. |
| **Özet kutusu şablondan geliyordu** | `yayin.py`de düzeltildi; yeni panelde tekrarlanmasın. |
| **Yıldızlı ama doğrulanmayan alanlar** | Spot, etiket, meta yazar zorunlu görünüp zorunlu değildi. |

---

## 3. Faz sırası

Her fazın "bitti" ölçütü **ölçülebilir** olmak zorundadır: bir sayı, bir eşik, ya da
"şu komut şu çıktıyı verdi" biçiminde. "Çalışıyor", "tamam", "hazır" beyanı bitti
sayılmaz.

| Faz | İş | Bitti ölçütü — ölçülür, beyan edilmez |
|---|---|---|
| **F1** | **Anasayfa yeni düzeni** — §1'deki şema, statik HTML, yer tutucu canlı veri | §3.1'deki on iki maddenin tamamı |
| **F2** | Django iskeleti + taksonomi + **adres sözleşmesi** | (a) 13 kategori slug'ı veritabanında `PANEL-NOTLARI.md` §3'teki hâliyle birebir; (b) `tum-urller.jsonl`deki **556.824 adresin %100'ü** çevrimdışı çözücüde bir kayda çözülüyor, çözülemeyen adres **sıfır**; (c) kimlikle çözüm: yanlış slug + doğru kimlik → **301** + kanonik adres, en az 20 örnekle sınandı; (d) `bursada-spor` 4 adresi için yönlendirme kaydı var |
| **F3** | Veri modeli + **göç aktarıcısı** | (a) beş sitemap ailesinin **tamamı** taranmış — haber 556.824 · video 32.006 · köşe 6.903 · galeri 4.042 · yazar 18 (**toplam 599.793**); eksik aile varsa faz kapanmaz; (b) içeri alınan kayıt sayısı taranan sayının **≥ %99,5'i**, fark satır satır listeli; (c) her kaydın adresi F2 çözücüsünden geçiyor; (d) **görsel kapsama oranı ölçülmüş ve yazılmış** — kaç kayıt yerel görsele sahip, kalanında ne gösterileceği karara bağlanmış (aşağıdaki F3 notu) |
| **F4** | Anasayfanın şablona dönmesi + iç sayfalar | (a) şablonlarda gömülü haber başlığı/gövdesi `grep` ile **0**; (b) haber detay · kategori · ilçe · yazar · köşe yazısı · galeri · video · arama sonucu · 404 sayfalarının **hepsi** veritabanından render ediliyor; (c) §3.1'deki ölçüm turu şablon hâli üzerinde **tekrarlanıp** aynı sonucu veriyor |
| **F5** | **Panel birebir kopya** + roller + 2FA | (a) §2'deki ekran listesinin tamamı çalışır — liste ekranları **ve** ekle/düzenle formları; (b) `PANEL-NOTLARI.md` §4'teki 31 satırlık alan sözleşmesi haber formunda **satır satır** doğrulanmış; (c) §2'deki düzeltme kalemlerinin her biri için "yapıldı / yapılmadı + neden" satırı var; (d) rol matrisi gerçek `usertype_list` dökümüyle karşılaştırılmış |
| **F6** | Canlı veri kaynakları | Yedi bileşenin (döviz · hava · namaz · eczane · puan · maç skoru · vizyon) **her biri** için kaynak adı, güncelleme sıklığı ve kaynak düştüğünde ne gösterileceği yazılı ve sınanmış. Kaynağı bulunamayan bileşen "elle giriş" olarak panele bağlanmış |
| **F7** | Arama, bildirim, reklam sunumu | (a) arama **p95 < 300 ms**, tam veri üzerinde en az 50 sorguluk ölçümle; (b) reklam yuvası kaydı **konum + ölçü + cihaz** üç alanlı ve mevcut **50 yuva** bu modele taşınmış; (c) bildirim gönderimi açılma oranını ekranda gösteriyor |
| **F8** | Kesim | (a) hazırlık ortamında 556.824 adresin **%100'ü** doğru içeriği döndürüyor; (b) beş sitemap ailesi yeniden üretiliyor ve adres sayıları kaynağıyla eşleşiyor; (c) geri dönüş adımı yazılı ve **bir kez denenmiş** |

**Sıra ve bağımlılık.** F1 önce — kullanıcının doğrudan istediği ve gözle onaylayacağı iş bu.
F2, F1'den bağımsızdır, paralel yürüyebilir. **F3 iki şeye bağlıdır:** F2'nin adres
çözücüsüne ve dışarıdaki arşiv taramasına. Tarama başka makinede **%16,6'da**
(92.661 / 556.824, son kayıt 25 Ağustos 2026) ve yalnız *haber* ailesini alıyor; kalan dört
aile **hiç başlamadı**. Tarama bitmeden F3 kapanamaz. F4 F1+F3'ü, F5 F3'ü, F7 F3'ü bekler.
F6 baştan itibaren paralel yürütülebilir.

> **F3 notu — ölçülmüş görsel sorunu.** Yayın, görsel düzenini
> `/static/<id>-slug-hash.jpg`ten `/static/YYYY/AA/GG/…`ya taşımış ve eski dosyaları
> sunucudan **silmiş**. Ölçüm: `basarisiz.txt` içinde **155.588 görsel 404'ü**;
> 2021-04 → 2021-10 aralığından alınan **1.405 kayıtlık örnekte indirilebilen görsel 1**.
> Yani kazımayla görsel kurtarılamıyor. Yeni düzene hangi tarihte geçildiği **ölçülmedi** —
> bu, arşivin ne kadarının görselini koruduğunu belirler ve F3 kapanmadan ölçülmelidir.
> Eski görseller ancak sunucu yedeğinden gelebilir.

### 3.1 F1 bitti ölçütü — ayrıntılı

Dosya: `tasarim-1-anasayfa.html`. F1 ancak on iki maddenin **hepsi** karşılanınca kapanır.

1. **18 bileşenin tamamı var ve §1'deki sırada.** Denetim, dosyadaki bölümlerin yukarıdan
   aşağıya okunmasıyla yapılır. Eksik ya da yer değiştirmiş bileşen fazı kapatmaz.
2. **Sayılar tutuyor.** Kategori bandı **10** kalem · dört haber kutucuğu **4** ·
   ana manşet **15** slayt · ikinci haber alanı **5** slayt · haber kutuları **2 × 5 = 10** ·
   döviz bandı **5** kalem. Hepsi DOM sayımıyla doğrulanır.
3. **Reklam yuvaları gerçek envanterden adlandırılmış.** Kullanılan adlar mevcut 50 yuvayla
   birebir: tam genişlik **`1100x150`**, manşet yanı **`-Manşet yanı- 300x250`**, yan raylar
   **`-Sol pageskin1-` / `-Sağ pageskin1- 160x600`**. Uydurma yuva adı yok.
4. **Yan bannerlar var.** Sayfanın üst kısmında iki yanda **birer** 160×600 pageskin yeter.
   (§7, 26 Ağustos: ölçüt gevşetildi — kullanıcı sayı söylemedi, dört yuva eski sitenin
   envanteriydi. Envanterin tamamı reklam modülüyle **F5**'te gelir.)
5. **Ölçüm genişlikleri.** Başsız Chrome'da **1600 · 1440 · 1280 · 1024 · 768 · 390** px.
   Her genişlikte `documentElement.scrollWidth <= clientWidth` — **yatay taşma sıfır**.
   Kendi `overflow-x:auto` kutusunda kayan şeritler ölçümden ayıklanır.
6. **Yan rayların eşiği ölçülüp yazılmış.** Pageskinlerin hangi genişlikten itibaren
   göründüğü, altında ne olduğu raporda sayıyla durur. İçerik sütunu 1100 px + 2 × 160 px ray
   + boşluk demektir; bu, bugünkü 1240 px'lik `.kapsa` ile çelişir — **çelişki çözülmüş olmalı.**
7. **Manşet erişilebilirliği.** Otomatik dönme `prefers-reduced-motion: reduce` altında
   duruyor (ölçülerek), slaytlar klavyeyle gezilebiliyor, kaçıncı slaytta olunduğu görünüyor.
8. **Sekmeler çalışıyor.** Hava · namaz · eczane sekmeleri `role="tab"` + `aria-selected` +
   `aria-controls` ile kurulu ve ok tuşlarıyla geziliyor; mevcut klasik demodaki davranış korunuyor.
9. **Yer tutucu olduğu belli.** Canlı veri gerektiren yedi bileşen gerçekçi ama **uydurma
   olmayan** değer taşıyor ve yer tutucu olduğu kodda işaretli. Uydurma haber başlığı,
   uydurma gazeteci sözü, uydurma eczane adı yok.
10. **Proje kuralları sayıyla.** **Renk property'sinde** hex/rgba **0** — §7: öğe başına
    uygulanan `--s1..--s5` değişken tanımları bu sayıya girmez · İngilizce sınıf adı **0** ·
    `alt`sız `<img>` **0** · Google Fonts dışı dış URL **0** · olmayan görsele referans **0** ·
    etiket dengesi tamam.
11. **Erişilebilirlik.** Her etkileşimli öğede görünür odak · `lang="tr"` · atlama bağlantısı ·
    başlık düzeyleri atlamasız · 4.5:1 kontrast.
12. **İnternetsiz açılıyor.** Ağ kapalıyken dosya çift tıkla açılıyor; yalnız yazı tipi düşüyor.

**F1 kapsamı dışında** — bilerek yapılmayacak, raporda "yapılmadı" diye yazılacak:
gerçek veri bağlantısı · arama · yorum · footer'ın yeniden tasarımı ·
iç sayfaların yeni düzene uyarlanması.

### 3.2 Takip düzeni

- **Faz açılışı.** `haber-sistemi-uzmani` planın o fazı ne dediğini okur ve işi yapacak ajana
  **yazılı** aktarır: faz numarası, bitti ölçütü, kapsam dışı kalemler.
- **Faz kapanışı.** Aynı ajan bitti ölçütünü **ölçer**; beyan kabul edilmez. Ölçülemeyen madde
  "ölçülmedi" diye raporlanır ve **faz kapanmaz**.
- **Sapma.** Plandan sapma gerekiyorsa **önce bu belge güncellenir**, sonra iş yapılır.
  Sessiz sapma kabul edilmez.
- **Kayıt yeri.** Faz raporu kullanıcıya dönen mesajdadır. Kalıcı ölçüm ve karar kaydı
  `PANEL-NOTLARI.md` (panel) ve `DEMO-NOTLARI.md` (site) içinde tutulur. Bu belge karar ve
  ölçüt belgesidir, günlük değildir.
- **Faz durumları.** açılmadı · sürüyor · ölçümde · kapandı. Bir faz yalnız ölçüm turundan
  sonra kapanır.

| Faz | Durum | Not |
|---|---|---|
| **F1** | **bitti** | `tasarim-1-anasayfa.html` — §3.1'in **on iki maddesi de karşılandı**, takipçi ajan bağımsız ölçtü (26 Ağustos). 18 bileşen sırada · sayılar tam (10·4·15·5·2×5·5·4 lig) · 5/5 yuva adı envanterden · altı genişlikte taşma **0** (çubuk görünür **ve** gizli) · eşik **1480**, içerik sütunu her iki çubuk durumunda **tam 1100** · reduced-motion'da manşet 20 sn'de dönmedi · sekmeler tam ARIA + ok/Home/End · atlama bağlantısı ilk Tab'da görünür, hedef yapışkan bandın altında · renk property'sinde hex **0**, `alt`sız img **0/42**, dış URL **0**, etiket hatası **0** · kontrast 306/306 · internetsiz 42/42 görsel |
| **F2** | **bitti** | Adres sözleşmesi **bağımsız ölçüldü** (26 Ağustos): (a) `taksonomi_kur` → kategori **13** · kategori-tür **39** · ilçe **17**, şema `0001_initial`; (b) `adres_dogrula` → **556.824 / 556.824**, çözülemeyen **0**, **18,9 sn**, ağsız + veritabansız; (c) yanlış slug + doğru kimlik → **301** kanonik (`/galeriler/yanlis-208/…` → `/galeriler/bursa-208/…`), bilinmeyen kategori → **404**, kanonik → **200**; (d) `bursada-spor` → **301** → `bursa-da-spor`. `taksonomi` paketi **12/12**. Sıra tuzağı (`/yazarlar/{slug}-{id}`) gerileme testine bağlı |
| F3 | **sürüyor** | Tarama **bu makinede sürdürüldü** (27 Ağustos). Beş ailenin dördü içeri alındı: yazar **17/18** · galeri **4.040/4.042** · köşe **6.713/6.906** · video sürüyor · haber %16,6. Medya ailelerinde **görsel kapsaması %99,9–100** — haberin aksine kurtarılabiliyor (kapaklar silinmiş `/static/` altında değil `/cdn/` altında). Faz haber ailesi bitmeden kapanmaz |
| F6 | **sürüyor** | Yedi kalemden **ikisi** bitti: puan durumu (4 lig) ve vizyon takvimi — betikler `canli-veri/`de, kaynak/sıklık/düşme davranışı yazılı ve ölçüldü (§8 F6a sonucu). Kalan beş: döviz · hava · namaz · eczane · (Bursaspor skoru puan betiğinin içinde geldi) |
| **F4** | **sürüyor** | Üç ölçütten **ikisi tam**, üçüncüsü büyük ölçüde: (a) gömülü başlık/gövde **0**; (b) haber detay · kategori · ilçe · **yazar · köşe yazısı · galeri · video** · arama · 404 **hepsi veritabanından render ediliyor** — kalan tek eksik köşe/video ailelerinin taramasının bitmesi; (c) ölçüm turu **11 sayfa × 8 genişlikte** tekrarlandı: yatay taşma **0/88**, bileşen sayıları 9/9, sayfa başına h1 **1**, odaksız öğe **0** |
| **F5** | **sürüyor** | Panel temeli kuruldu ve **yerleşim hatası çözüldü**: 25/25 ölçümde yatay taşma **0**. Bugün · Akış · Haber formu · Roller çalışıyor; rol matrisi 5×14 ölçüldü. Kalan: §2'deki ekran listesinin geri kalanı |
| **F8** | **hazırlık** | Sitemap üreteci ve RSS kuruldu: beş ailenin tamamı üretiliyor — **104.940 adres · 23,5 MB · 11,8 sn**. `site_haritasi_karsilastir` F8(b)'yi ölçüyor ve şu an **karşılanmadı** diyor (fark 494.952, göç eksikliğinden) |
| F7 | açılmadı | |

---

## 4. Benim önerilerim

Kullanıcı "önerin varsa söyle" dedi.

1. **15 slayt çok.** Ölçülen davranış: manşet slaytlarında 5'ten sonrası neredeyse
   görülmez. 15 kalabilir ama **küçük resim şeridi veya numara göstergesi** konsun,
   okur nerede olduğunu görsün; yoksa slayt sayısı boşa gider.
2. **Otomatik dönme kapalı başlasın** ya da yavaş olsun. Otomatik dönen manşet
   erişilebilirlik açısından sorunlu; `prefers-reduced-motion` altında zaten durmalı.
3. **Kategori bandı 10 kalem** iyi karar. Mevcut sitede 13 kategori var —
   Sağlık, Teknoloji, Yaşam, Aktüalite, Savunma Sanayi banda girmiyor. Bunlar
   "Gündem" altında alt menüde toplanabilir, adresleri yaşamaya devam eder.
4. **Nöbetçi eczane için API çoğu ilde yok.** Panelde elle giriş ekranı gerekebilir;
   F5 kapsamına alınmalı.
5. **Vizyon takvimi** için kaynak doğrulanmadan söz verilmesin. Yoksa elle giriş.
6. **Puan durumu 5 lig** ciddi veri işi. Ücretli servis gerekebilir; maliyet kalemi.
7. **Reklam yuvaları isimlendirilirken** mevcut 50 yuvanın envanteri kullanılsın —
   yuva = konum + ölçü + cihaz; reklamveren adı yuvaya yazılmasın.
8. **En çok okunanlar için okunma verisi yok** (göçte kurtarılamadı). Yeni sistemde
   sayaç sıfırdan başlar; ilk haftalar liste anlamsız olur. Başlangıçta editör
   seçimi olarak kurulup sonra otomatiğe geçmesi önerilir.

---

## 5. Süreç takibi

Kullanıcının isteği: haber sitelerinde uzmanlaşmış bir ajan tüm süreci takip etsin.
**`haber-sistemi-uzmani`** ajanı bu göreve atandı; kapsamı panelden **ürünün
tamamına** genişletildi. Tanımı `.claude/agents/haber-sistemi-uzmani.md`.

Ajanın görevi: bu plana sadakati denetlemek, faz bitti ölçütlerini doğrulamak,
sapma olduğunda önce planı güncelletmek.

---

## 6. 26 Ağustos — kullanıcı kararları

Kullanıcıya sorulan yedi sorunun cevapları. **Bunlar §1 ve §2'yi bağlar.**

| Soru | Karar |
|---|---|
| Döviz bandı kaç kalem | **5** — dolar, euro, sterlin, gram altın, BIST 100 |
| "Basın ilan" ne demek | **Resmî ilan** — editoryal içerik, reklam yuvası değil |
| İlçe şeridi kalıyor mu | **Kalkıyor.** İlçeler kategori bandında maddedir |
| Puan durumu kaç lig | **4** — Süper, 1., 2., 3. Lig |
| Görselsiz haberler | **Kurtarma denendi, mümkün değil. Görselsiz göç edilecek** |
| Panel yaklaşımı | Karar bana bırakıldı → planın §2'si (işlev kopyası) geçerli |
| `.kapsa` genişliği | Karar bana bırakıldı → aşağıda |
| Arama nereye | **Kategori bandının içine**, sağ uçta; **menü düğmesi onun sağına** |

### Görsel kurtarma — denendi, kapandı

296.207 haberin (arşivin %53,2'si) görseli **kurtarılamıyor**. Denenen ve
elenen yollar:

1. **Canlı sunucu** — dosyalar silinmiş. `/static/` yol varyantlarının hepsi 404.
2. **Wayback Machine** — alan adı 2021-2022'de arşivlenmiş (~646 sayfa kayıt),
   ama `static/*` görsel kaydı **sıfır**; arşivlenen görüntüler reklam sayaç
   GIF'leri. 2021 arşivinde **haber detay sayfası hiç yok** (400 HTML örneğinde 0),
   yani sayfa üzerinden orijinal görsel adresine de ulaşılamıyor.

**Sonuç:** 2023-07 öncesi haberler metin olarak göç eder, görselsiz. Yerine ne
konacağı bir tasarım kararıdır (kategori temsili görsel · logo · görselsiz düzen);
şablon bu durumu düzgün karşılamalı.

### `.kapsa` genişliği — karar

`.kapsa`, içeriği ortalayan ve **azami genişliğini** belirleyen CSS sınıfı.
Bugün 1240 px. Yeni düzende içerik sütunu 1100 px + iki yanda 160 px'lik
reklam rayı + boşluklar ≈ 1500 px gerekiyor.

**Karar (düzeltildi):** içerik sütunu **1100 px sabit**; yan raylar ancak pencere
**≥ 1480 px** olduğunda görünür, altında gizlenir. Ray gizlendiğinde içerik
1100 px'de ortalı kalır. Bu, F1'de uygulandı ve ölçüldü.

---

## 7. 26 Ağustos — ölçüt düzeltmeleri

F1 ölçümünde §3.1'in üç maddesinin **fazla sıkı ya da yanlış yazıldığı** çıktı.
Takipçi ajan ölçtü, kararı ben verdim.

### Madde 4 — yan reklam sayısı gevşetildi

**Eskiden:** her yanda **dört** pageskin (eski envanterdeki `-Sol/Sağ pageskin1..4-`).

**Şimdi:** F1 için **her yanda bir** yeter.

Gerekçe: kullanıcı "sayfanın üst kısmında iki yana banner reklamlar" dedi, sayı
söylemedi. Dört adet 160×600'ü üst üste koymak ~2400 px'lik reklam rayı demek —
kullanıcının istediği bu değil, eski sitenin envanteri bu. **Yuva envanterinin
tamamı reklam modülüyle (F5) gelir**; F1 bir yerleşim fazıdır, reklam
envanteri fazı değil.

### Madde 10 — "hex 0" yazımı düzeltildi

**Eskiden:** "`:root` dışında hex 0".

**Şimdi:** "**renk property'sinde** hex 0".

Gerekçe: `.t-mavi`, `.t-kirmizi` gibi altı SVG palet sınıfı `--s1..--s5`
**değişken tanımı** yapıyor ve öğe başına uygulandıkları için `:root`a
taşınamazlar. Ölçüm: renk property'sinde hex **0**, 112 `var(--sN)` çağrısı.
Eski yazım bu deseni yanlışlıkla ihlal sayıyordu.

**Değişmeyen:** İngilizce sınıf adı **0** olmalı. `footer-ic` · `footer-ust` ·
`footer-alt` bu dosyada yeni üretildi, Türkçeleştirilecek.

### §6 — ray eşiği 1460 → 1480

Ölçüm 1461-1479 px arasında içerik sütununun **1081-1090 px'e ezildiğini**
gösterdi; `.sayfa` `max-width:1480px` olduğu için ray açılınca sütundan çalıyor.
"İçerik sütunu 1100 px sabit" kararı bu aralıkta bozuluyordu.

**Karar:** eşik **1480 px**. Ray ancak içerik gerçekten 1100 px kalabildiğinde
açılır.

### Kapanmayan maddeler (sayfa ajanına gidiyor)

| # | Eksik | Karar |
|---|---|---|
| 3 | `Manşet üstü` ve `Sağ ray` envanterde yok | Gerçek adlara çekilecek: `1100x150`, `-Manşet yanı- 300x250` |
| 4 | Her yanda 1 pageskin | **Ölçüt gevşetildi — bu madde artık geçiyor** |
| 10 | 3 İngilizce sınıf adı | `footer-ic/ust/alt` Türkçeleştirilecek |
| 11 | Atlama bağlantısı yok | `<main id>` + "İçeriğe atla" eklenecek |

---

## 8. 26 Ağustos — üç yeni karar

| Konu | Karar |
|---|---|
| **Göç** | *"şu ana kadar taramış olanların göçünü başlat"* → F3, eldeki **92.666** kayıtla açıldı; tarama sürdükçe komut tekrar koşar |
| **Reklamlar** | *"reklamlar mevcut haliyle kalsın"* → her yanda **bir** pageskin kararı **onaylandı**, §7 madde 4 kapandı |
| **Ücretli servis yok** | *"puan durumu ve vizyon takvimini ücretsiz fetch etmek için scriptler yazalım"* → **F6 bütçe sorusu kapandı: ücretli servis kullanılmayacak** |

### F6a — ücretsiz veri kaynakları (ayrı oturumda yapılacak)

Kullanıcı bu işin **temizlenmiş bir oturumda** yapılmasını istedi.

**Kapsam:** dört lig puan durumu + vizyon takvimi, **maliyetsiz**.

Ücretli API yerine **kendi çekme betiklerimizi** yazacağız — `disa-aktarim/`
klasöründeki tarayıcının yaklaşımıyla aynı: doğrudan istek, saygılı hız,
kesintiye dayanıklı, çıktı yerel dosyaya.

**Araştırılacak kaynaklar (henüz doğrulanmadı):**

| Veri | Aday kaynak | Not |
|---|---|---|
| Puan durumu (Süper, 1., 2., 3. Lig) | TFF'nin kendi yayını | Resmî kaynak; grup usulü liglerde grup seçimi kararı hâlâ açık |
| Bursaspor haftalık skor | Aynı kaynak | Bursaspor'un oynadığı lig belirlenmeli |
| Vizyon takvimi | Türkiye vizyon listesi yayınlayan siteler | Afiş **telifli** — yalnız ad/tarih alınmalı, afiş yerel yer tutucu |

**Uyarılar:**
- Afiş görseli telifli; çekilmeyecek.
- Her kaynağın kullanım şartları okunacak; kazıma yasaksa o kaynak elenecek.
- Çıktı biçimi `arac/` ve `disa-aktarim/` ile tutarlı olsun (JSON, Türkçe alan adları).

**Diğer beş canlı veri kalemi** (döviz, hava, namaz, eczane) F6'da; hepsinin
ücretsiz kaynağı var, eczane çoğu ilde elle giriş isteyebilir.

### F6a sonucu — 26 Ağustos 2026, betikler yazıldı ve ölçüldü

Klasör: `canli-veri/` (`ortak.py`, `puan_durumu.py`, `vizyon_takvimi.py`,
`README.md`). Saf standart kütüphane, paket yok.

| Bileşen | Kaynak | Sıklık | Kaynak düştüğünde |
|---|---|---|---|
| Puan durumu (4 lig) | **TFF** — `www.tff.org` | maç günü saatte bir, diğer gün günde bir; bayat eşiği **48 sa** | önceki dosya korunur, `durum-*.json` → `eski`, çıkış kodu **2**; hiç veri yoksa `yok` + kod **1** |
| Bursaspor haftalık skor | Aynı çekimin içinde | Aynı | Aynı |
| Vizyon takvimi | **TMDB** (varsayılan) · Wikidata · elle · Box Office TR (yalnız yazılı izinle) | haftada bir; bayat eşiği **7 gün** | Aynı; kalıcı düşmede `--kaynak elle` (panel girişi) |

**Ölçüm (26 Ağustos 2026):** dört lig, **7 grup, 127 takım**, tutarsız satır
**0**, adı doğrulanamayan **0**. Denetim her koşuda `oynadı = G+B+M` ve
`averaj = A−Y` eşitliklerini ölçer; puan denetlenmez (TFF ceza silmesi
uyguluyor — Adana Demirspor sezona **−24** ile başladı).

**Kapanan iki açık soru:**

1. **Bursaspor'un ligi** — kodda yazılı değil, her koşuda dört ligin
   tablosunda aranıyor. Ölçüm: **Trendyol 1. Lig, 5. sıra, 6 puan**.
2. **Grup seçimi** — betik bütün grupları çektiği için bu artık bir *gösterim*
   kararı. Bursa kulüpleri: 2. Lig **Beyaz** → İnegöl Kafkas; 2. Lig
   **Kırmızı** → Karacabey Belediye + Sultan Su İnegölspor; 3. Lig
   **2. Grup** → Bursa Nilüfer + Bursa Yıldırım. Öneri: varsayılan 2. Lig
   Kırmızı, 3. Lig 2. Grup, yanında grup değiştirme düğmesi.

**Ölçülen üç TFF tuhaflığı** (ayrıntı `canli-veri/README.md`):
`tff.org.tr` DNS'te **SERVFAIL**, site `www.tff.org`'da · `pageID=198`
sayfasında sunucu Türkçe harfleri `U+FFFD` basıyor, adlar `kulupID` ile
`pageID=80`'den onarılıyor · Süper Lig'in tam tablosu yalnız `pageID=198`'de.

**Elenmeyen ama kilitlenen kaynak.** `boxofficeturkiye.com` TR takviminin en
eksiksiz açık listesi ve `robots.txt` izin veriyor; ama Kullanım Koşulları
**madde 14** içeriğin yazılı izin olmadan çoğaltılmasını ve yayınlanmasını
yasaklıyor. Ayrıştırıcı yazıldı ve çevrimdışı doğrulandı (2026 Ağustos
sayfasından **30 film, 4 vizyon günü**), ama `--yazili-izin-var` bayrağı
verilmeden **çalışmıyor**. İzin bir e-posta işi; alınırsa tek bayrakla açılır.

**Hukuk teyidine gidecek kalem.** TFF Kullanım Şartları: *"Sitede yer alan
bilgiler, kaynak gösterilmek suretiyle yayımlanabilir; ancak bu bilgiler
ticari amaçlarla kullanılamaz."* Gazete ticari yayındır. Karşı görüş: puan
cetveli olgudur, FSEK eser koruması dışıdır ve her gazete tabloyu TFF'ye atıf
vererek basar. Panel projesindeki diğer hukuki teyit kalemleriyle birlikte
sorulmalı.

---

## 9. Film afişi telifi — araştırıldı, 26 Ağustos 2026

Soru: film afişlerini yayınlamak telif gerektirir mi?

**Evet, gerektirir.** Dört katman var:

1. **Afiş bir eserdir.** Özgün grafik tasarım FSEK m.4 kapsamında güzel sanat
   eseridir; koruma kendiliğinden doğar, tescil gerekmez. Hak sahibi genelde
   yapımcı ya da Türkiye dağıtımcısıdır.
2. **Üstünde ayrıca kişilik hakkı vardır.** Afişteki oyuncu fotoğrafı,
   eser telifinden bağımsız olarak imaj/kişilik hakkı doğurur.
3. **Haber istisnası dar.** FSEK m.37, "haber mahiyetinde olmak ve
   bilgilendirme kapsamını aşmamak kaydıyla, günlük hadiselere bağlı"
   iktibası serbest bırakır — ama "hak sahibinin hukuki menfaatlerine zarar
   vermemek" ve "eserden normal yararlanmaya aykırı olmamak" şartıyla.
   Yargıtay 11. HD bu istisnayı **dar** yorumluyor: iktibasın mutlaka günlük
   olaylarla bağlantılı bir haberin içinde olması aranıyor.
4. **Bizim kullanımımız istisnaya sığmaz.** "Vizyonda neler var" bileşeni tek
   bir habere bağlı değil; **sürekli, otomatik güncellenen bir afiş
   kataloğu**. Bu, m.37'nin "günlük hadiseye bağlı haber" kalıbına değil,
   katalog kullanımına benzer.

**Kararımız (betiklerde uygulandı):** afiş dosyası **indirilmiyor**. Her
kayıtta yalnız `afis_kaynak` künyesi ve `"afis_yayinlanabilir": false` duruyor;
sayfa yerel yer tutucu gösterecek. Ad, vizyon tarihi, tür ve dağıtımcı
**olgudur**, telif korumasına girmez — bunlar serbestçe yayınlanır.

**Bir uyarı:** afişi TMDB'den çekmek meseleyi çözmez. TMDB afişin hak sahibi
değil barındırıcısıdır; TMDB'nin API izni stüdyonun iznini vermez.

**Afişi basmak isteniyorsa temiz yol:** dağıtımcıdan yazılı izin. Dağıtımcılar
zaten tanıtım için **basın kiti** yayınlar ve afişi bu amaçla kullandırır;
Türkiye'de vizyonu besleyen dağıtımcı sayısı azdır (CJ ENM, Bir Film, TME
Films, CGV Mars, UIP, Warner Bros. Türkiye…). Tek seferlik e-posta işi,
ücretsiz, kalıcı. **Bu bir iş kalemidir, betiğin işi değildir.**



---

## 10. 26 Ağustos — F4 açıldı: site şablona döndü

Anasayfa ve iç sayfalar artık `tasarim-1-*.html` içindeki gömülü içerikten
değil, **veritabanından** render ediliyor. Django uygulaması `uygulama/`
altında; 92.666 haber kaydı içeride.

### Ne yapıldı

| Parça | Yer |
|---|---|
| Taban şablon + parçalar | `uygulama/sablonlar/` — `taban.html`, `anasayfa.html`, `haber_detay.html`, `kategori.html`, `arama.html`, `ilceler.html`, `bekleyen.html`, `404.html` |
| Ortak bağlam | `icerik/baglam.py` — kategori bandı (10 kalem), son dakika, ilçeler |
| Görünümler | `icerik/views.py` (anasayfa · kategori · ilçe · arama), `taksonomi/views.py` (haber detay) |
| Stil ve betik | `uygulama/statik/` — tasarım dosyalarından çıkarıldı, detay sayfasının kuralları birleştirildi |
| Gövde temizleyicisi | `icerik/temizle.py` — beyaz liste |
| Türkçe süzgeçler | `icerik/templatetags/site_etiket.py` |

### Ölçümler (başsız Chrome, DevTools protokolü)

- **Yatay taşma:** 7 sayfa × 8 genişlik (1600 · 1480 · 1479 · 1440 · 1280 · 1024 · 768 · 390) = **56 ölçüm, taşma 0**
- **Bileşen sayıları:** bant 10 · manşet 15 · manşet noktası 15 · ikincil 5 · dörtlü 4 · haber kutusu 10 · döviz 5 · lig sekmesi 4 · servis sekmesi 3 — **9/9 tam**
- **İçerik sütunu:** her genişlikte **1100 px**; yan ray **1480 px**'te açılıyor, 1479'da kapanıyor (§7 kararıyla birebir)
- **Erişilebilirlik:** sayfa başına h1 **1**, başlık düzeyi atlaması **0**, odaklanabilir 266 öğede görünür odağı olmayan **0**, `lang="tr"`, atlama bağlantısı var
- **Proje kuralları:** dış URL **0** (Google Fonts hariç), `alt`sız `<img>` **0**, İngilizce sınıf adı **0**
- **Testler:** **41/41 geçiyor** (`taksonomi` 16 + `icerik` 25)

### Verilen kararlar

1. **Görselsiz haber kategori çizimiyle gösterilir.** Arşivin %99,98'inde yerel
   görsel yok. Uzak adrese bağlanmak iki kuralı birden bozuyordu: sayfa
   internetsiz açılmalı ve dosyaların çoğu kaynak sunucuda zaten silinmiş.
   Karar: `gorsel_var` yanlışsa tasarımın SVG simge kütüphanesinden kategori
   temsilî çizimi konur, kırık görsel gösterilmez.
2. **Yeni alan: `gorsel_dosya`.** Model yerel dosya yolunu tutmuyordu, bu
   yüzden görseli olan 18 kayıt bile yerelden gösterilemiyordu. Alan eklendi
   (`0002_haber_gorsel_dosya`), `goc_al` dolduruyor, görseller
   `/arsiv-gorsel/` altından servis ediliyor. Arşiv kökü `BH_ARSIV_KOK`
   ortam değişkeniyle taşınabilir.
3. **Gövde beyaz listeden geçirilir.** Gövde kazımayla geldi ve panelden de
   HTML girilecek. Ölçüm: 92.648 gövdede tehlikeli etiket **0**, kullanılan
   etiketler `p` · `strong` · `img` · `em` · `a` · `b`. Temizleyici bugünkü
   arşivi bozmuyor; panelden gelecek içerik için duruyor. `img` bilerek
   düşürülür (ölü adres).
4. **Ayarlar ortam değişkenine bağlandı.** `BH_GIZLI_ANAHTAR` ·
   `BH_HATA_AYIKLA` · `BH_SUNUCU_ADLARI` · `BH_ARSIV_KOK`. F8 kesim
   listesinin ön şartı.
5. **"En çok okunanlar" editör seçkisi olarak kuruldu** (§4 madde 8 uyarınca);
   okunma sayacı yok, sayfadaki not bunu okura söylüyor.
6. **Türkçe büyük/küçük harf süzgeci yazıldı.** `"EKONOMİ".title()` Python'da
   `"Ekonomi̇"` veriyor, `"Ekonomi".upper()` ise `"EKONOMI"`. Kategori adları
   kaynakta büyük harf olduğu için bu her sayfada görünür bir hataydı.
7. **`footer-*` sınıfları Türkçeleştirildi** (§7'de açık kalan kalem):
   `footer-ic/ust/alt/cizgi/ilce/yazi` → `kunye-*`, `logo-img` → `logo-gorsel`.
   Hem uygulamada hem `tasarim-1-anasayfa.html`de.

### Adres sözleşmesinde değişen davranış

F2'de haber görünümü bir taslaktı ve **kayıt olsun olmasın 200** dönüyordu.
İçerik modeli geldiği için artık veritabanına bakıyor:

| Adres | F2 | F4 |
|---|---|---|
| Tanınan kategori + **olmayan** kimlik | 200 | **404** |
| Tanınan kategori + var olan kimlik, **yanlış slug** | 200 (yönlendirmesiz) | **301** kanoniğe |
| `/` ve `/{kategori}` | çözülmüyordu | anasayfa · kategori listesi |

`taksonomi/tests.py` bu üç satıra göre güncellendi; eski hâli F2'nin taslak
davranışını ölçüyordu. Sıra tuzağı testi (`/yazarlar/{slug}-{id}` haber
sanılmamalı) **duruyor ve geçiyor** — kategori kalıbı en sona konduğu için.

### F4'ün kapanması için kalan

Tek madde: **yazar · köşe yazısı · galeri · video sayfaları**. Bunların
modeli ve verisi yok, çünkü arşiv taraması yalnız haber ailesini aldı
(F3 bitti ölçütü, madde a). Sayfaları duruyor ve boş durumu düzgün
anlatıyor; adresleri şimdiden geçerli. **F4, F3'ün dört ailesi gelmeden
kapanamaz.**


---

## 11. 26 Ağustos — F5 açıldı: panelin temeli

`PANEL-NOTLARI.md` §4 (alan sözleşmesi), §7 (meta yazar), §9 (durum/hazırlık)
ve §11 (rol matrisi) kararları koda geçirildi. Panel `/panel/` altında,
giriş zorunlu.

### Ne yapıldı

| Parça | Yer |
|---|---|
| Veri modeli tamamlandı | `icerik/models.py` — 17 yeni alan (`0003`, `0004`) |
| Rol matrisi | `icerik/yetkiler.py` (tek kaynak) + `manage.py roller_kur` |
| Haber formu | `icerik/formlar.py` — §4'ün satır satır karşılığı |
| Panel görünümleri | `icerik/panel.py` — Bugün · Akış · Haber ekle/düzenle · Roller |
| Şablonlar | `uygulama/sablonlar/panel/` |
| Stil | `uygulama/statik/stil/panel.css` (`panel-bugun.html`den, `.btn` → `.dugme`) |

### Ölçümler

- **Rol matrisi:** 5 rol · 14 yetkilik · 30 bağ — §11'deki tabloyla birebir,
  `roller_kur --dokum` ile dökülüyor
- **Testler: 80/80 geçiyor** (taksonomi 16 · içerik 25 · panel sözleşmesi 25 ·
  panel ekranları 14)
- **Canlı doğrulama:** Akış ekranı **92.666 kaydı** listeliyor; Roller ekranı
  14 satırlık matrisi basıyor; haber formunda **27 alan** var
- **Yetki denetimi adresten sınandı:** muhabir `/panel/roller` → **403**,
  formda manşet kutuları **0**, menüde roller bağlantısı **0**;
  `İlan Sorumlusu` → `/panel/haber/ekle` **403**
- **Uçtan uca:** panelden yayına alınan haber ön yüzde **200** dönüyor;
  yayına alınmadan önce **404**

### Verilen kararlar

1. **Zorunluluk yayına alırken işler, taslakta değil.** §4'ün "gerçekten
   zorunlu" sütunu (spot · etiket · iki paragraf gövde) yayın eşiğinde
   uygulanır; taslak yalnız başlık ve kategori ister. Aksi hâlde §11'deki
   "muhabir yayınlayamaz" kuralı "muhabir hiçbir şey kaydedemez"e dönerdi.
   Eşik `arac/yayin.py`deki "boş taslak yayınlanmaz" kuralıyla aynı.
2. **Meta Yazar Bilgisi kaynak türünden türetilir** (§7): Ajans → Haber
   Ajansı, Dış yayın → Alıntı/İktibas, Kendi muhabirimiz → Fikir İşçisi.
   Elle seçilirse türetim durur (`meta_yazar_elle`).
3. **Kategori değişimi yönlendirme doğurur.** Kategori adresin parçası;
   panelden değiştirilince eski adres `Yonlendirme` tablosuna 301 olarak
   yazılır. Testle bağlandı.
4. **Yeni haberin kimliği en büyük kimliğin üstünden devam eder** — göçte
   eski kimlikler korunduğu için çakışma olamaz.
5. **Menüde gizleme yetki denetimi sayılmaz.** Her görünüm yetkisini
   ayrıca denetler; testler ekranları doğrudan adresten çağırıyor.
6. **`roller_kur` sessiz kipe ve eski konsol kodlamasına dayanıklı yapıldı.**
   Matris dökümündeki `●` karakteri Windows konsolunda (cp1254) komutu
   çökertiyordu; döküm bir yan çıktı, komutu düşürmemeli.

### Açık iş — panel yerleşimi bozuk

`panel.css` `panel-bugun.html`den alındı ve o dosya **tek ekran** için
yazılmıştı. Yeni ekranlar (geniş tablolu Akış ve Roller) altında yerleşim
tutmuyor. Başsız Chrome ölçümü (5 ekran × 5 genişlik):

| Ekran | 1600 | 1280 | 1024 | 768 | 390 |
|---|---|---|---|---|---|
| Bugün | 0 | 46 | 98 | 98 | 87 |
| Akış | 38 | 358 | 411 | 411 | 411 |
| Haber formu | 0 | 46 | 99 | 99 | 99 |
| Roller | 41 | 361 | 414 | 414 | 414 |
| Giriş | 0 | 46 | 98 | 98 | 87 |

**25 ölçümün 22'sinde yatay taşma var.** Ölçülen belirti: `.panel` flex
kabında `.kenar` (212 px kenar çubuğu) x=0 yerine **x=1000**'de çiziliyor,
`.calisma` ona bitişik başlayıp 373 px'e sıkışıyor. Hesaplanan stiller
normal görünüyor (`flex:0 0 212px`, `order:0`, `margin:0`, `left:auto`),
yani sebep henüz **bulunamadı** — ekran görüntüsü alındı, incelenmedi.

Başlık düzeni ve odak tarafı temiz: her ekranda h1 **1**, başlık atlaması
**0**, odaksız öğe **0**.

**Sıradaki oturumda ilk iş budur.** Ekranlar çalışıyor ve testler geçiyor;
sorun yalnızca görsel yerleşimde.


---

## 12. 27 Ağustos — üç paralel iş kolu + tarama devri

Kullanıcı taramayı bu makinede sürdürmeyi ve birbirini etkilemeyen
paralel geliştirmeleri istedi. Üç ajan ayrık klasörlerde çalıştı.

### Tarama bu makineye geri alındı

`disa-aktarim/aileleri_tara.sh` aileleri **küçükten büyüğe** sırayla
tarıyor: galeri → köşe → video → haber. Gerekçe: dört küçük aile toplam
~43 bin kayıt ve F4'ün açık maddesini kapatıyor; haber ailesinin kalanı
~464 bin ve tek başına saatler sürüyor.

### Panel yerleşimi — sebep bulundu

`URUN-PLANI.md` §11'de "sebep bulunamadı" diye bırakılan hata: **çok
satırlı `{# … #}` yorumları**. Django'da `{# #}` yorumu **tek satırlıktır**;
çok satırlısı ayrıştırılmaz ve sayfaya **düz metin olarak basılır**. Panel
kabuğunda bu metin `.panel` flex kabında anonim bir öğe olup kenar
çubuğunu 1000 px sağa itiyordu. Hesaplanan stillerin normal görünmesinin
sebebi buydu: suçlu bir öğe değil bir **metin düğümü**ydü, dolayısıyla
`querySelectorAll('*')` taramasına hiç girmiyordu.

Aynı hata **dört şablonda** vardı (site 3 + panel 1); hepsi
`{% comment %}`'e çevrildi. Ayrıca panel şablonlarında kullanılan
**12 CSS sınıfının tanımı yoktu** — en zararlısı `gorsel-gizli`, yani
yalnız ekran okuyucuya ait metinler ("Haber listesi") sayfada görünüyordu.

**Ölçüm:** panel 5 ekran × 5 genişlik → yatay taşma **22 → 0**.

> **Ölçüm aracına dair not.** Ölçüm betiği tarayıcı önbelleğini
> kapatmıyordu ve düzeltilmiş CSS'i görmeyip yanlış rapor verdi. Artık
> `Network.setCacheDisabled` çağırıyor. Ölçüm aracının kendisi de
> doğrulanmalı — yanlış ölçüm yanlış karara yol açıyordu.

### Yeni uygulamalar

| Uygulama | İş | Ölçüm |
|---|---|---|
| `uygulama/medya/` | Köşe · galeri · video · yazar: model, göç, görünüm, şablon | 37 yazar · 6.713 köşe · 4.040 galeri · 1.484 video içeri alındı; düşen kayıt **0** |
| `uygulama/besleme/` | Sitemap (5 aile, aylık) + RSS + robots.txt | 104.940 adres · 23,5 MB · **11,8 sn** |
| `canli-veri/` (4 yeni betik) | Döviz · hava · namaz · eczane | döviz 1,9 sn · hava 5,9 sn · namaz 0,2 sn · eczane 0,4 sn |

`medya/besleme_kaynaklari.py` iki uygulamayı **birbirine bağımlı
kılmadan** birleştiriyor: `besleme` her uygulamanın bu adlı modülünü
autodiscover ile arıyor, `medya` kendini deftere kaydediyor.

### Ölçülen üç veri kusuru (medya göçünde bulundu ve düzeltildi)

1. **Köşe yazısı tarihleri ISO değil** — 1.500 örneğin tamamı
   `01.03.2021 08:04` biçiminde. Yalnız ISO kabul edilseydi 6.903 köşe
   yazısının hepsi yayın zamansız kalır ve hiçbiri listelenmezdi.
2. **Köşe sayfasının `og:image`'ı yazının değil YAZARIN portresi** —
   bundan yararlanılarak yazar görsel kapsaması %50 → **%100**.
3. **Video `contentUrl` sayfanın kendi adresi** (312/312 kayıt); gerçek
   oynatıcı `embedUrl`de. "Kaynağında aç" okuru bulunduğu sayfaya
   yollayacaktı.

### Testler

**168/168 geçiyor** (taksonomi 16 · içerik 25 · panel 39 · medya 53 ·
besleme 35). Yeni uygulamalar bağlanırken **iki test kırıldı ve
düzeltildi** — ikisi de aynı sebepten: F2'de görünümler taslaktı ve
kayıt olsun olmasın 200 dönüyordu, artık veritabanına bakıyorlar.

### Karar bekleyen dört madde

1. **`haber-213` foto kategorisi taksonomide yok** ama galerilerin
   **1.168'i (%29)** o dilimde. Şimdilik kategorisiz alınıyor, ham dilim
   adresi taşıyor, sayfa çalışıyor. 14. kategori eklenmeli mi?
2. **37 yazar kimliği köşe adreslerinde geçiyor, sitemap 18 yazar
   sayfası listeliyor.** Yazarların yarısından fazlasının sayfası yok,
   yazısı var. 20 yazar göçte geçici kayıt olarak açıldı.
3. **Gram altın ve BIST 100 için ücretsiz kaynak yok.** Elenenler: Borsa
   İstanbul (veri satılıyor), TCMB EVDS (anahtar ister), stooq ve Yahoo
   (`robots.txt: Disallow: /`), LBMA (401). Ücretsiz EVDS anahtarı almak
   bir iş kalemi.
4. **Hukuki teyit — TCMB ve MGM.** İkisinin de kullanım şartı
   "kaynak gösterilerek yayımlanabilir, **ticari kullanım yazılı izne
   tabidir**" diyor. Gazete ticari bir yayın. Bu, §2'deki BİK ve Meta
   Yazar teyitleriyle aynı listeye girer.


---

## 13. 27 Ağustos — canlı veri siteye bağlandı

Altı kalem artık anasayfada **gerçek veriyle** çiziliyor. Bağlantı katmanı
`icerik/canli.py`: çekme betikleri siteden bağımsız koşar ve JSON yazar,
site yalnızca **okur**. Bir kaynak düşerse ya da yavaşlarsa sayfa isteği
ona takılmaz.

| Bileşen | Kaynak | Sayfada |
|---|---|---|
| Döviz bandı | TCMB | 3 kalem değerli, gram altın ve BIST 100 **çizgi** (kaynak yok) |
| Üst bant + hava sekmesi | MGM | 26°C · Az bulutlu · 4 günlük şerit |
| Namaz sekmesi | hesap | 6 vakit, o anki vakit vurgulu |
| Eczane sekmesi | BEO | 36 eczane · 19 ilçe |
| Puan durumu | TFF | 4 lig sekmesi, ilk beş sıra, hafta ve grup adı başlıkta |
| Vizyon | (aşağıya bakınız) | kart yapısı hazır |

**Üç davranış teste bağlandı** (`icerik/tests_canli.py`, 17 test):
dosya yoksa bileşen **sessizce gizlenir** (uydurma değer basmaktansa hiç
göstermemek doğru) · bayat veri **atılmaz, işaretlenir** ve güncelleme
zamanı okura gösterilir · bozuk JSON sayfayı **düşürmez**.

### Ölçülen iki biçim hatası

- `baslikla` süzgeci kısaltmaları bozuyordu: **"GALATASARAY A.Ş." →
  "Galatasaray A.ş."**. Kısaltma tanıma eklendi (noktalı ve kısa, ya da
  üç harfe kadar tümü büyük).
- Üst bantta hava sıcaklığı yanlış alandan okunuyordu (`hava.sicaklik`,
  doğrusu `hava.son_durum.sicaklik`); ekranda "Bursa °C ·" çıkıyordu.
  Ekran görüntüsü alınmasa fark edilmezdi — şablon hatası sessizdir.

### Vizyon takvimi — kullanıcı kararı

Kullanıcı canlı sitede "Vizyonda Neler Var ?" bölümünün kaynak
gösterilmeden yayımlandığını hatırlattı. **Doğrulandı:** bölüm var, şehir
seçicili film şeridiyle birlikte, hiçbir kaynak atfı yok; veri sağlayıcı
CMS'in `/get-movies` ucundan geliyor.

**Karar kullanıcınındır ve verilmiştir; bu konu tekrar açılmayacak.**
Kayda geçen tek teknik ayrım: o bölüm sağlayıcının hazır özelliği, yani
varsa lisans **sağlayıcınındır ve bize geçmez**. Film adı ve tarihi
olgudur; afiş dağıtımcının eseridir — ikisi ayrı kalemlerdir.

### Testler

**185/185 geçiyor.** Site ölçümü 11 sayfa × 8 genişlik → yatay taşma
**0/88**, bileşen sayıları **9/9**, sayfa başına h1 **1**, odaksız öğe **0**.


---

## 14. 27 Ağustos — yerleşim ve görsel düzenlemeler

Kullanıcı isteği. **§1'deki bileşen sırası bu bölümle değişti**; sözleşme
tablosundaki 9 ve 10 numaralı satırlar güncellendi.

| İstenen | Yapılan | Ölçüm |
|---|---|---|
| İlçeleri menüye koy | Tam menüye ayrı **İLÇELER** sütunu; 17 ilçe + başlık | menüde 18 bağlantı |
| Piyasa bandını taşı ve çarpıcı yap | Sayfanın **en üstüne** alındı; koyu lacivert gradyan, 19 px tabular rakam, yeşil/kırmızı değişim rozetleri | 5 kalem tam |
| Resmî ilanın yerini değiştir, güzelleştir | Haber kutularının **altına**; üç sütun → **iki sütun**, satır vurgusu | 820 px altında tek sütun |
| Otomatik geçiş seçim olmasın, varsayılan olsun | `OTOMATİK GEÇİŞ` düğmesi **kaldırıldı**, sayaç açılışta başlıyor | 11 sn'de slayt 0 → 1 |
| Manşet yanı yükseklikte eşleşsin | Izgara gerdirildi, mini slayt kalan yüksekliği kaplıyor | manşet **471 px** · yan sütun **471 px** · fark **0** |
| Daha göz alıcı | Kart hover'ı (gölge + fotoğraf yakınlaşması), bölüm başlıklarına kırmızı vurgu, manşet yazısına gölge | — |

### Görselsiz kartlarda tekdüzelik giderildi

Arşivin %99,98'inde yerel görsel yok; bir kategori kutusundaki bütün
kartlar **aynı** temsilî çizimi alıyordu — Bursaspor kutusunda altı birebir
aynı yeşil saha. Çizim kategoriye bağlı kaldı (anlamı o taşıyor), **rengi
kaydın kimliğinden türetiliyor**: aynı haber her zaman aynı rengi alır,
sayfa yenilenince kart titremez. Detay sayfasının kapak rengi de tıklanan
kartla aynı.

### Erişilebilirlik korundu

Otomatik geçiş varsayılan açık ama `prefers-reduced-motion: reduce`
altında **hiç dönmüyor** (ölçüldü: 12 sn'de slayt değişmedi); fare üstüne
gelince ve odak içerideyken de duruyor. F1 ölçüt 7 bozulmadı.

**Kontrast:** sayfadaki 411 metin öğesi ölçüldü, eşiğin altında **0**.
Yatay taşma 11 sayfa × 8 genişlikte **0/88**. Testler **185/185**.

### Ölçüm aracının kendisi üç kez yanılttı — not

Bu turda kontrast ve taşma ölçerleri **üç ayrı** yanlış sonuç verdi:

1. **Tarayıcı önbelleği kapalı değildi** → düzeltilmiş CSS görülmüyordu,
   "hâlâ bozuk" deniyordu.
2. **Gradyanlı zemin `backgroundColor`'da görünmüyor** → beyaz yazı/beyaz
   zemin sanılıp oran 1.0 raporlandı.
3. **Yarı saydam zemin harmanlanmıyordu** ve **dekoratif gradyan zemin
   sanılıyordu** → afiş yer tutucusunun kontrastı 5,11 yerine 2,13
   ölçüldü. Bu yanlış ölçüme dayanıp yazı rengini **yanlış yöne**
   değiştirmeye başlamıştım; hesabı elle doğrulayınca çıktı.

Düzeltilmiş araçla gerçek bulgu: dekoratif çizgi şeridi zemini açtığı
için oran **4,15** ile eşiğin hemen altındaydı; `--afis-yazi` `#93A2B6`
→ `#A3B2C6` yapıldı, iki şeritte de eşik aşılıyor (5,00 ve 6,16).

**Ders: ölçüm aracı da doğrulanmalı.** Elle hesapla çapraz kontrol
edilmeyen bir ölçüm, olmayan hatayı düzelttirebiliyor.


---

## 15. 27 Ağustos — piyasa betiği: Google + iki yedek

Kullanıcı isteği: *"piyasa ve altın verisini her 15dk'da bir google'dan
çekecek bir script"*. `canli-veri/piyasa.py` yazıldı; **döviz bandının
son iki boş kalemi kapandı** (`doviz.json` → `kaynagi_olmayan: []`).

### Google düz istekle çekilemiyor — ölçüldü

`/finance/quote/USD-TRY` düz HTTP'de **200 + 1 MB HTML, fiyat yok**;
sayfaya JS ile basılıyor. Çözüm başsız Chrome `--dump-dom` — **paket
kurulumu gerekmedi**, `canli-veri/`'nin "saf standart kütüphane" kuralı
bozulmadı. Chrome yoksa Google kaynağı düşer, yedekler devralır.

### Gram altında ölçülmüş sapma — betik doğru olanı yayınlıyor

Google'da **TRY cinsi altın kotasyonu yok**; tek altın kalemi
`GCW00:COMEX`, yani **vadeli** sözleşme (USD/ons). Ons → gram çevrimi
yapılınca:

| Değer | Kaynak | TL/gram |
|---|---|---|
| hesaplanan | Google GCW00 × USD/TRY ÷ 31,1035 | **7.200,16** |
| doğrudan | doviz.com | **7.115,99** |

**Sapma %1,18** — vadeli baz + Kapalıçarşı primi. Gram başına ~85 TL;
bir gazete bandında yanlış sayı demek. Betik **doğrudan kotasyonu
tercih ediyor**; hesaplanan değer yalnız bütün doğrudan kaynaklar
düştüğünde, `kaynak_durumu: "hesaplanan"` damgasıyla yayına çıkıyor.

Çapraz kontrol her koşuda otomatik: Google dolar/euro TCMB bültenine
karşı **%0,04 ve %0,14** sapıyor — tutuyor.

### Kırılganlık saklanmadı

Üç kırılma biçimi kasten tetiklenip sınandı: **Chrome yok · sayfa düzeni
değişti · CAPTCHA** → üçünde de Google düşüyor, yedeklerden 4/4 kalem
geliyor, çıkış kodu 0. Üç kaynak birden düşerse eldeki dosyaya
dokunulmuyor (çıkış 2).

Dürüst değerlendirme: **9 koşuda 0 engelleme hiçbir şey kanıtlamaz.**
Engelleme birikimlidir; 15 dakikada bir koşan betik günde 96 istek atar
ve Google yolu er geç kırılır. Kırıldığında `denetim.google_engel_izi`
dolar ve `--kaynak doviz mynet` ile bant **durmaz**. Yedeklerin ikisi de
saf standart kütüphane, **0,3 sn altında** ve gram altını doğrudan kote
ediyor — yani Google düştüğünde hem hız hem doğruluk **iyileşiyor**.

> **En temiz seçenek hâlâ duruyor:** ücretsiz **TCMB EVDS API anahtarı**
> alınırsa iki kalem de resmî kaynaktan gelir ve kazımaya hiç gerek
> kalmaz. Tek seferlik bir kayıt işi.

### Zamanlama

```powershell
schtasks /Create /TN "BH piyasa" /SC MINUTE /MO 15 /RL LIMITED /F ^
  /TR "\"...\.venv\Scripts\python.exe\" \"...\canli-veri\piyasa.py\""
```
Kurulup çalıştırıldı (Last Result **0**, 24 sn), sonra **silindi** —
makinede kalıcı görev bırakılmadı. Kullanıcı isterse yeniden kurulur.

### Ölçüm tuzağı — kaydedilmeli

Python'un `urllib.robotparser`'ı Google'ın `robots.txt`'sindeki
`Disallow: /?` satırını `Disallow: /` gibi okuyor ve **her yolu yasaklı
sanıyor** (`/finance`, `/maps` dâhil hepsi `False`). Bu kütüphaneyle
kontrol eden biri kaynağı yanlışlıkla eler. Ham satırları elle
eşleştirmek gerekiyor. *(stooq ve Yahoo gerçekten `Disallow: /` diyordu —
onlar haklı olarak elenmişti.)*

**Hukuki teyit listesine eklendi:** Google Hizmet Şartları otomatik
erişimi hoş karşılamıyor — bu robots değil **sözleşme** meselesi.


---

## 16. 27 Ağustos — EVDS bulundu: Google varsayılandan çıkarıldı

Kullanıcı kararı: *"tcmb evds ile ücretsiz olarak alabileceksek verileri
o yolu kullanalım"*. **Alabiliyoruz — üstelik anahtar bile gerekmiyor.**

### Dokümantasyondaki yol ölü, yenisi açık

`evds2.tcmb.gov.tr/service/evds/...` (belgelerde geçen, `&key=` isteyen
uç) artık **her yola 1355 baytlık boş SPA kabuğu** döndürüyor —
anahtarlı ya da anahtarsız fark etmiyor. Gerçek API, uygulamanın kendi
ağ istekleri yakalanarak bulundu:

```
POST https://evds3.tcmb.gov.tr/igmevdsms-dis/fe
GET  https://evds3.tcmb.gov.tr/igmevdsms-dis/searchResults?searchVal=altın
```

**Anahtar yok · çerez yok · tarayıcı yok** — düz `urllib` ile 200.
Bağımsız doğrulandı.

| Kalem | Seri | Ne ölçüyor |
|---|---|---|
| Gram altın | `TP.ALTINPIYASA.KAP02` | BIST Kıymetli Madenler Piyasası kapanışı, **TL/kg** → ÷1000 |
| BIST 100 | `TP.MK.F.BILESIK` | **FİYAT** endeksi (XU100). `TP.MK.G.BILESIK` *getiri* endeksidir, o değil |

### Üç tuzak — üçü de ölçüldü

1. **Yük eksiksiz olmalı.** `groupSeperator` · `isRaporSayfasi` ·
   `ozelFormuller` alanlarından biri eksikse sunucu **500** döner.
2. **`Origin` gönderilirse tam `evds3` olmalı**; `evds2` yazılırsa
   **403 "Invalid CORS request"**. En dayanıklısı hiç göndermemek.
3. **Değerler binlik ayraçlı geliyor** (`6,757,000.0000`). Naif
   `float()` çağrısı çöker; ayraç temizlenmeli.

### Doğruluk — Google'ın altını neden yanlıştı

| Kalem | EVDS (26-08 kapanış) | Doğrudan kotasyon | Sapma |
|---|---|---|---|
| Gram altın | **7.121,20** | 7.115,99 (doviz.com) | **−0,07%** |
| BIST 100 | 14.610,92 | 14.586,77 | −0,17% |

Google'ın **hesaplanan** altını %1,18 sapıyordu (vadeli COMEX sözleşmesi
üzerinden çevrim). EVDS doğrudan kotasyonlarla binde bir içinde — yani
`KAP02/1000` gerçekten gram altın.

### Sıralama: resmî kapanış canlı kotasyonu ezmiyor

EVDS **kapanış** verir, gün içi vermez; gün ortasında en tazesi bir
önceki iş günüdür. Bu yüzden `sira_puani` eklendi:
**4** = bugün tarihli resmî kapanış · **3** = canlı doğrudan kotasyon ·
**2** = eski resmî kapanış · **1** = hesaplanan. Erken çıkış ölçütü
"hepsi taze" yerine "hepsi ≥ 3" oldu; EVDS başta olsa da bant gün
ortasında **donmuyor**.

### Google varsayılandan çıkarıldı

`VARSAYILAN_SIRA = ["evds", "doviz", "mynet"]`. Ölçülen fark:

| Zincir | Süre | Bağımlılık |
|---|---|---|
| eski (Google dâhil) | **18,5 sn** | Chrome |
| yeni | **0,3 sn** | yok |

Google'ın eklediği tek şey 60 kat çalışma süresi, bir Chrome
bağımlılığı ve bu işin sebebi olan **Hizmet Şartları sorunuydu**. Kodu
duruyor, `--kaynak google` ile elle çağrılabilir.

### `doviz.py` değişmedi — ölçülmüş gerekçe

`/sk-seriler`in USD/EUR'unun "daha taze" olduğu izlenimi **yanlış
çıktı**: EVDS her bülteni **bir iş günü ileri** tarihliyor. EVDS'nin
"27-08" satırı, `doviz.py`'nin `today.xml`den zaten okuduğu **26.08
bülteninin ta kendisi**. Kazanç sıfır; kayıp üç: `/sk-seriler`
**efektif alış** verir (`doviz.py` bilerek **döviz alış/satış**
kullanıyor), bülten tarihi/numarası bir gün kayar ve düz XML yerine
SPA'ya bağımlı bir uca geçilmiş olur.

**Sonuç:** döviz bandının beş kalemi de resmî ya da doğrudan kaynaktan;
`kaynagi_olmayan: []`. Testler **185/185**.


---

## 17. 27 Ağustos — bant canlı kura çevrildi, zamanlayıcı kuruldu

Kullanıcı: *"bu değerlerin günde bir güncellenecek olması bizim için iyi
olmaz, çünkü google'dan bu değerleri görmek için arama yapan insanların
karşısına bizim güncel değerlerle çıkmamız gerekir"*.

### Sorun yalnız üç kalemdeydi

Gram altın ve BIST 100 **zaten canlıydı** (doviz.com/Mynet, her koşuda
o anki değer). Günde bir güncellenen yalnız **dolar · euro · sterlin**
idi; onlar TCMB bülteninden geliyordu ve bülten iş günü ~15:30'da
**günde bir kez** yayımlanıyor.

### Karar: bantta serbest piyasa kuru gösterilir

Bandın etiketi zaten **PİYASA**. Serbest piyasa kuru sürekli hareket
eder; gazetelerin bandında gösterdiği de odur. TCMB kuru resmî
referanstır (muhasebe, gümrük, hukuk) — **kaybolmadı**, her kalemin
`tcmb_resmi` alanında duruyor ve canlı kaynakların hepsi düştüğünde
bantta o gösteriliyor.

Sterlin de canlı kaynaklara eklendi (`GBP` eşlemesi üç kaynakta da
vardı, yalnız istenmiyordu).

| | Önce | Sonra |
|---|---|---|
| Dolar · Euro · Sterlin | TCMB bülteni, **günde 1** | canlı, **15 dk** |
| Gram altın · BIST 100 | canlı | canlı |
| Bantta yazan | bülten tarihi (26.08) | **ölçüm saati** (15:09) |

### Zamanlayıcı kuruldu — üç ayrı sıklık

`canli-veri/tazele.ps1` + üç Görev Zamanlayıcı görevi. Sıklıklar verinin
gerçek değişim hızına göre ayrıldı; hepsini 15 dakikada bir koşturmak
kaynakları boşuna yorardı.

| Görev | Sıklık | Betikler |
|---|---|---|
| `BH canli veri - sik` | **15 dk** | piyasa · döviz |
| `BH canli veri - saatlik` | 1 saat | hava · eczane |
| `BH canli veri - gunluk` | günde 1 | namaz · puan durumu · vizyon |

Sık grupta **sıra bağlayıcı**: `doviz.py`, `piyasa.py`'nin yazdığı
dosyayı okuyor. Çıkış kodu 2 (kaynak düştü, önceki dosya korundu) hata
sayılmıyor; yalnız kod 1 hata.

**Doğrulandı:** görev elle tetiklendi → `LastTaskResult 0`, iki dosya da
tazelendi, sıradaki koşu zamanlandı.

### Bir düzeltme

Bant `▼ %-0,28` yazıyordu — ok zaten yönü söylediği için çift olumsuz
okunuyordu. `mutlak` süzgeci eklendi. Ayrıca `doviz.py`'nin özet satırı
"3 TCMB'den, 5 piyasa'dan (toplam 5)" gibi tutarsız sayıyordu; artık
yalnız **yayına giren** değer sayılıyor.

### Kayda geçen uyarı — SEO beklentisi

Kullanıcının gerekçesi arama trafiği. 22 Ağustos araştırması bu
kategoride ters yönde bir bulgu kaydetmişti: Google organik trafiği bir
yılda %33-38 düştü ve **en sert düşen kategori hizmet içeriğiydi**
(döviz, hava, rehber) — çünkü cevabı artık arama motorunun kendisi
veriyor. Değerlerin güncel olması **yine de doğrudur** (bayat kur bir
gazetede kötü görünür), ama bu bandın arama trafiği getirmesi
beklenmemeli. Trafik getiren şey gazetenin **kendi verisi ve haberi**.


---

## 18. 27 Ağustos — F4 kapanış ölçüm turu: **üç ölçüt de karşılandı**

Dokuz sayfa türü + 404, sekiz genişlikte bağımsız ölçüldü (başsız Chrome,
DevTools protokolü, önbellek kapalı, `BH_HATA_AYIKLA=0` ile gerçek 404 şablonu).

### Ölçüm

- **Yatay taşma 0/80** (360 · 414 · 768 · 900 · 1024 · 1280 · 1480 · 1600)
- İçerik sütunu her genişlikte **1100 px**; yan raylar **1480**'de açılıyor
- Sayfa başına `h1` **1/1** · başlık atlaması **0** · `alt`sız `<img>` **0** ·
  `lang="tr"` + atlama bağlantısı **10/10**
- Odaklanabilir **4.145** öğe, görünür odağı olmayan **0**
- Kontrast: hesaplanan stille **4.841** metin öğesi → eşik altı **0**; görsel
  arkalı **55** öğe harf pikseli farkıyla ayrıca ölçüldü → eşik altı **0**
- **Yüklenen dış kaynak 0** (Google Fonts hariç). Video sayfasındaki tek dış
  adres bir `<a href>`, yani giden bağlantı — sayfanın internetsiz açılmasını
  engellemiyor. **Bu ayrım §10'un "dış URL 0" ölçütünde yoktu, eklendi.**
- §3.1'in on iki maddesi şablon hâlinde tekrarlandı: **12/12**
- **F4(a):** şablonlarda gömülü haber başlığı/gövdesi `grep` → **0**; çok
  satırlı `{# #}` → **0**

### Bulunan ve giderilen altı kusur

1. **Kontrast 2,37** — mini slayt başlığı açık renkli temsilî çizim üstünde
   okunmuyordu. `--gradyan` %30'a kadar saydamdı, yazı bloğu ise mini slaytta
   **%31**'den başlıyor. Duraklar yeniden konuldu; en kötü zemin (saf beyaz
   fotoğraf) hesabıyla başlık ≥3,0, spot ve "sesli dinle" ≥4,5. Harf pikseli
   ölçümü **0/55**.
2. **Renk property'sinde ham hex/rgba: 22 satır** — §3.1 madde 10 ihlali.
   Hepsi `:root` değişkenine taşındı (**0**), hesaplanan renkler değişmedi,
   gerileme testi eklendi.
3. **Künye yanlış beyan veriyordu.** "Döviz, hava, namaz, eczane, puan durumu
   ve vizyon verisi henüz canlı kaynağa bağlanmamıştır" satırı §13'ten beri
   doğru değildi — altı kalemden **beşi** bağlıydı. Gerçek duruma göre yazıldı
   (kaynaklar adlarıyla: TCMB · MGM · BEO · TFF · Diyanet; bağlı olmayan tek
   kalem **vizyon**). "Fotoğraflar Wikimedia Commons" ifadesi de düzeltildi.
   **Yayınlanan bir künyede yanlış beyan bırakılmaz.**
4. **Şablona elle yazılmış üç arşiv sayısı.** "Arşivden gelen 1484 video"
   yazarken veritabanında **31.084** vardı. Veritabanından sayılıyor, 300 sn
   önbellekli.
5. **Vizyon bölümü dört sahte kart basıyordu**; `canli.py` veriyi zaten
   veriyordu ama şablon kullanmıyordu. Bağlandı; veri boşken tek satırlık boş
   durum gösteriliyor. Afiş telifli olduğu için basılmıyor (§9).
6. **Sayım kilitte sayfayı düşürebilirdi** — boşta 67 ms, göç sürerken
   **1.250 ms**. `DatabaseError` yakalanıyor, son bilinen değere düşülüyor;
   `None` ("sayılamadı") ile `0` ("hiç yok") ayrı tutuluyor.

### Ölçüm aracı yine yanılttı — **beş kez**

§12 ve §14'teki yanılmalara beş tane daha eklendi. Hiçbirine dayanıp düzeltme
yapılmadı:

1. **"50–61 bağlantıda odak halkası yok"** → hepsinin `getClientRects().length`
   **0**'dı: gizli tam menü. Çizilmeyen öğe odak *alamaz*, stili değişmez.
   Menü açılıp ölçülünce **50 → 0**.
2. **`Page.captureScreenshot`'ın `clip`'i belge koordinatı ister**, görünüm
   koordinatı değil → katlama altındaki öğelerde yanlış bölge okundu,
   **6 sahte kontrast hatası**.
3. **Kutu tabanlı piksel örneklemesi** yuvarlak oynat rozetinin *köşelerini*
   (dairenin dışı = fotoğraf) ve `.dinle-bag`'in kendi açık çerçevesini zemin
   saydı → **9 bulgu**; harf piksellerini iki ekran görüntüsünün farkıyla
   ayırınca **1**'e indi.
4. **Ölü CSS taraması 0 seçici saydı** — Chrome'un iç içe CSS desteğiyle
   `CSSStyleRule`'un da `.cssRules`'u var, her kural grup sanılıyordu.
5. **Gerileme testinin kendisi hatalıydı:** `{% if sayi %}` gerçek bir **0**'ı
   da gizliyordu.

**Doğrulama yöntemi — kayda geçsin.** Kontrast hesabı tarayıcıdan bağımsız
olarak Python'da yeniden yazıldı ve §14'ün kayıtlı sayıları yeniden üretildi
(4,97 / 6,16 / 4,12 — kayıt 5,00 / 6,16 / 4,15); aynı iki değer üçüncü kez
**gerçek ekran piksellerinden** ölçüldü (4,94 / 6,16). Üç bağımsız yöntem
uyuştu. Taşma ölçerine kasten 2000 px kutu enjekte edilip **yakaladığı**
doğrulandı — "0 bulgu" ancak araç körlüğü elenmişse bir şey söyler.

### Açık bırakılan iki kalem

- **Resmî ilan bölümündeki 6 kayıt şablonda gömülü.** F4(a)'nın lafzı
  "haber başlığı/gövdesi" diyor, bunlar ilan. **Karar: F4 bu yüzden açık
  tutulmuyor**; ilan modülü model kazandığında (F5 model turu ya da F7)
  veritabanına taşınacak. Sessizce unutulmasın diye buraya yazıldı.
- **106/407 CSS seçici hiçbir sayfada eşleşmedi ama silinmedi.** Ölçüm "ölü"
  ile "bugün tetiklenmedi"yi ayıramıyor: `.doviz .veri-yok` bugün tüm kalemler
  dolu olduğu için eşleşmiyor, yarın bir kaynak düştüğünde eşleşecek;
  `.metin[data-boyut]` A+/A- ile geliyor, `.ses-*` seslendirme durumları.
  **Doğrulanmamış bulguya dayanarak silme yapılmaz.**

### F4 durumu

**Üç ölçüt de karşılandı** — (a) gömülü içerik 0, (b) dokuz sayfa türü + 404
veritabanından render ediliyor, (c) §3.1 turu şablon hâlinde tekrarlandı ve
aynı sonucu verdi. Faz yine de **F3'e bağlı**: medya aileleri artık dolu
(yazar 37 · köşe 6.713 · galeri 4.040 · video 31.084) ama haber ailesi göçü
sürüyor.


---

## 19. 27 Ağustos — F5: panel migration'sız kısmıyla bitti

§2'deki ekran listesinden **mevcut modellerle yapılabilen her şey** kuruldu.
Sağlayıcının HTML/CSS/JS'i alınmadı; §2'nin **yol 1**'i (işlev ve akış kopyası,
kendi kodumuzla) uygulandı. Sütun ve süzgeç sözleşmesi
`C:\Users\Asus\Downloads\bursa_hakimiyet_panel` dökümünden ölçülerek çıkarıldı.

### Kurulan ekranlar — 24 panel adresi

| Ekran | Adres | Yetkilik | Kaynak döküm |
|---|---|---|---|
| Manşetler | `/panel/mansetler` | `mansete_alma` | `headline_list.php` |
| Köşe Yazıları | `/panel/kose` (+ düzenle) | `kose_yonetimi` | `editorialist_list.php` |
| Köşe Yazarları | `/panel/yazarlar` (+ düzenle) | `kose_yonetimi` | `authors_list.php` |
| Foto Galeri | `/panel/galeriler` (+ düzenle) | `haber_girme` | `gallery_list.php` |
| Videolar | `/panel/videolar` (+ düzenle) | `haber_girme` | `video_list.php` |
| Kategoriler | `/panel/kategoriler` (+ düzenle) | `taksonomi_duzenleme` | `categories_list.php` |
| Kullanıcılar | `/panel/kullanicilar` (+ düzenle) | `kullanici_yonetimi` | dökümü yok (§11) |
| Kaynaklar | `/panel/kaynaklar` (+ düzenle) | `taksonomi_duzenleme` | — |
| Şifre | `/panel/sifre` | **yetkilik yok** | Django `PasswordChangeView` |

Yedi liste ekranı **tek şablonu** paylaşıyor (`panel/liste.html`), mevcut
panelin on liste ekranının tek DataTables kabuğunu paylaşmasıyla aynı düzen.
Akış da bu kabuğa taşındı ve dökümde olup bizde eksik olan **Editör Seç**
süzgeci eklendi. Menüden **Sayfa Düzeni** ve **İlan & Reklam** bağlantıları
kaldırıldı: ikisi de Bugün'e gidiyordu, yani menü yalan söylüyordu.

**Şifre ekranı yetkiliğe bağlanmadı** — herkes kendi parolasını
değiştirebilmeli. Django'nun hazır görünümü kullanıldı: eski parola
doğrulaması, parola politikası ve `update_session_auth_hash` onunla geliyor;
kendi parola akışımızı yazmak bedava risk olurdu.

### Toplu işlem fiilleri — §12'nin açık kalemi kapandı

Mevcut panelin ölçülmüş hatası "seçim kutusu var, fiil yok"tu. İkisi birlikte
geldi (Akış ekranında, çünkü §12'nin tablosu Akış'ın tablosu): satır kutusu ·
hepsini seç · `aria-live` canlı sayaç · "süzgeçteki N kaydın tamamı" ·
gruplanmış fiil şeridi. `panel.js` yalnızca kolaylık ekliyor — **hiçbir kural
betikte uygulanmıyor**, betik hiç çalışmazsa ekran elle kullanılabiliyor.

**Dokuz fiil, hepsi yetkiye bağlı.** Yetkisi olmayan fiil şeritte **çizilmiyor**
ve sunucuda ayrıca reddediliyor. Hiç fiili olmayan rolde (İlan Sorumlusu)
seçim kutusu da yok.

**Üç kural koda geçti:**

1. **Kategori değişimi her zaman onay ekranından geçer.** Kaç adresin
   değişeceği önce söylenir, beş örnek gösterilir ve her değişen kayıt için
   **301 yönlendirme yazılır**. Atlansaydı yüzlerce eski bağlantı tek tıkla
   ölürdü.
2. **Yayına alma eşiği toplu işlemde de işler** (§4: spot · en az iki paragraf
   gövde · en az bir etiket). Eşiği geçmeyen kayıt atlanır ve sayısı sonuç
   mesajında söylenir. Uygulanmasaydı kural bir düğmeyle delinirdi.
3. **"Süzgeçteki tümü" kipinde küme sunucuda yeniden süzülür** — istemcinin
   gönderdiği kimliklere bakılmaz. Liste ve toplu işlem tek `akis_sorgusu()`
   işlevini paylaşıyor; iki kopya olsaydı "tümü" ekranda görünenden başka bir
   kümeye uygulanabilirdi.

**Kategori değiştirme yetkisi — §12'den sapma, karara bağlandı.** §12'nin
tablosu bu fiili Editör ve Sayfa Sekreteri'ne de açıyor. **Yeni kural:**
*tek kayıtta* kategori değiştirme Editör ve Sayfa Sekreteri'nde kalır (haber
formundaki mevcut davranış), *toplu* kategori değiştirme **yalnız Yayın
Yönetmeni**'ndedir (`taksonomi_duzenleme`). Gerekçe: ölçek riski farklı — tek
kayıtta bir adres taşınır ve editör ne yaptığını görür, toplu işlemde yüzlerce
adres tek tıkla taşınır. Aynı fiilin adı aynı diye yetkisi de aynı olmak
zorunda değil.

### Kaynak tablosunda ölçülen kirlilik — **göç hatası**

Kaynaklar ekranı yalnız listelemiyor, dokuz tespit kuralıyla bozuklukları
sayıyor. İlk ölçüm §2'nin beklediği tabloyu **bulamadı**:

> §2'nin "348 kayıt, 6 tekrar, 7 birleşik" sayıları **sağlayıcı panelinin
> dökümünden** geliyordu. Bizim `taksonomi.Kaynak` tablosunu `goc_al` doldurdu
> ve orada **76 kayıt** var; birebir tekrar **0**, birleşik kayıt **0**.

Onun yerine göçten gelen **başka** bir kirlilik ölçüldü — 76 kaydın **52'si**
sorunlu:

| Tespit | Adet | Ölçülen örnek |
|---|---|---|
| Cümleden düşmüş kelime | 32 | `ve` · `suyu` · `aktardi` · `tezgahi` |
| Kesik cümle (tam 40 karakter) | 7 | `MHP Genel Başkanı Bahçeli grup toplantıs` |
| Cümle parçası | 7 | `etkin ve yeşil bir ekonomiye geçişine ka` |
| Salt sayı | 5 | `525218` · `571930` |
| Alan adı | 5 | `www.sondakika.com` · `https` |
| Kendi yayınımız | 4 | `Bursa Hakimiyet` · `Bu rsahakimiyet` |
| Meta Yazar değeri | 1 | **`Haber Merkezi` — 92.564 habere bağlı** |

**İki bulgu ayrıca kayda değer:**

1. **`Haber Merkezi` bir kaynak değil, Meta Yazar Bilgisi değeridir**
   (`PANEL-NOTLARI.md` §7'nin altı değerinden biri) ve arşivin **%84'ü** ona
   kaynak diye bağlanmış. Yani göç, meta yazar alanını kaynak alanı sanıyor.
   Bu doğrudan `CLAUDE.md`nin editoryal kuralına çarpıyor: yayınlanan
   sayfadaki **Kaynak bölmesi** 92.564 haberde yanlış bilgi gösteriyor.
   **Çözüm kaynak tablosunda değil göçtedir** — o kaydı pasifleştirmek
   92.564 haberi kaynaksız bırakır. Göç iş koluna devredildi.
2. **Göç ayıklayıcısı künye metnini tam 40 karakterde kesiyor.** Yedi kaydın
   uzunluğu birebir 40. Tahmin değil, imza. Genel tablo şunu söylüyor:
   ayıklayıcı kaynak alanını **gövde metninden tahmin etmeye çalışıyor** ve
   sık yanılıyor.

**Birleştirme yeteneği kuruldu ama canlı tabloda çalıştırılmadı.** Hedef
seçilir → bağlantılar 500'lük parçalar hâlinde taşınır → kayıt pasife alınır
ve `birlesti_ile` ile hedefe bağlanır. **Silme yok, iz kalıyor.** Kendine
birleştirme ve A→B→C zinciri reddediliyor. Uygulama bir **editör kararıdır**
ve göç ayıklaması düzeldikten sonra yapılmalıdır.

### Ölçüm

- **Testler 311/311 geçiyor.** Panel ekranlarının kendi dosyası
  (`icerik/tests_panel_listeler.py`) **103 test**.
- **Yerleşim: 266 ölçüm, bulgu 0** — 154 (22 ekran × 7 genişlik: 360 · 620 ·
  768 · 880 · 1024 · 1280 · 1600) + **105 font engelli** + 7 onay ekranı.
- Sayfa başına `h1` **1**, odak alabilen **4.095** öğede halkasız **0**,
  `alt`sız `<img>` **0**, Google Fonts dışı dış kaynak **0**.
- **Gerçek veride süre** (110.005 haber · 31.084 video): akış **9 ms** ·
  köşe **22 ms** · video **35 ms** · galeri **43 ms** · kategoriler **2 ms**.

**Google Fonts panele de bağlandı** (Inter · Source Serif 4 · IBM Plex Mono),
site tarafındaki `preconnect` + `display=swap` deseniyle. Panelin sistem
yedekleriyle ayrı bir yazı diline kayması bilinçsiz bir sapmaydı. Şart: font
engellenmiş hâlde de taşma **0** (105 ölçümle doğrulandı) ve her yüzün
arkasında gerçek yedek yığını.

### İki performans hatası ölçülüp düzeltildi

| Ne | Önce | Sonra |
|---|---|---|
| Akış "Editör Seç" süzgeci | **668 ms**, 110.005 satır taraması, sonuç **boş** (göç kayıtlarında `olusturan` yok) | açık hesaplar listesi, **1,4 ms** |
| Kategoriler haber sayacı | **486 ms**, her açılışta | `?sayim=1` ile isteğe bağlı, varsayılan **2,2 ms** |

### Ölçüm aracı ve paralel çalışma — dört yeni ders

1. **Yanlış sayfa ölçülüyordu.** Oturum çerezi baştan konduğu için
   `/panel/giris` yönleniyor ve araç 7 ölçümde **Bugün ekranını** ölçüp ona
   "Giriş" adını yazıyordu. Ölçer artık her sayfada **beklenen `h1` metnini**
   doğruluyor.
2. **Araç ekran görüntüsünü kendisi bozuyordu.** Odak halkası ölçümündeki
   `focus()` döngüsü `.tablo-kaydir` kutusunu kaydırıyor; sonradan alınan
   görüntüde tablo kaymış görünüp **olmayan bir hata** sanıldı.
3. **Onay ekranı 7/7 "odak halkası yok" verdi** — sayfa değil, POST'la açan
   **ölçüm yolu** hatalıydı: `:focus-visible`i ateşleyen Tab tuşunu
   göndermiyordu. Klavye hazırlığı tek yere alındı.
4. **Tek koşuluk süre ölçümü rapor edilmemeli.** İlk turda köşe 554 ms /
   video 518 ms çıktı, tekrarında 22/35 ms. Fark kodun maliyeti değil,
   **paralel göç yazıcısıyla çekişmeydi**.

**Kalıcı korumalar:** her ölçümde gövde ve kenar çubuğu zemini doğrulanıyor
(CSS yüklenmezse sayfa çıplak akar, taşma da olmaz ve ölçüm sahte "temiz"
verir) · tablo satır sayısı doğrulanıyor · bilerek 4000 px basan bir kontrol
sayfası aracın taşmayı gördüğünü kanıtlıyor · font turunda `document.fonts`
normal turda **dolu**, engelli turda **boş** olmalı (yoksa iki tur aynı şeyi
ölçer ve "engelli turda da 0" hiçbir şey söylemez).

**Paralel ajan dersi.** İki kez `manage.py test` kırmızı döndü ve iki kez de
sebep başka ajanın o dakikada yazdığı yarım dosyaydı (`KaynakForm`,
`goc_kaynak.py`). Doğru davranış uygulandı: **başkasının dosyasına dokunma,
bekle, yeniden koş.** Paralel çalışmada tek koşuluk kırmızı suite, kendi
işinin kırdığı anlamına gelmez.

### Sayısal ölçümün göremediği bir hata

Şifre ekranında parola politikası listesi stil dışında kalıyordu. Sebep:
Django `PasswordChangeForm`un `help_text`ini `<ul><li>` olarak veriyor,
`parca/alan.html` ise ipucunu `<p>` içine koyuyordu. **`<ul>`, `<p>` içine
konamaz** — tarayıcı paragrafı erken kapatıyor ve liste `.sag-not`un dışında
kalıyor. Geçersiz işaretleme, sessiz hata, **hiçbir sayısal ölçüm görmez**.
Ekran görüntüsü gördü. Gözle bakmanın yerini ölçüm almıyor.

### Bilerek yapılmayanlar

**Model gerektirenler bir sonraki tura** — Yorumlar · Son Dakika · Resmî
İlanlar · Reklam Yönetimi · Gazete Listesi · Kendi Yayınlarım · Duyurular ·
Log Kayıtları · Bildirimler · 2FA. Bunlar bir **model turudur**; göç aynı
SQLite'a yazarken şema değiştirmek istenmedi.

**Kurtarılamayan sütunlar silinmedi.** Okunma ve Editör sütunları tire basıp
nedenini taşıyor; eksikliği görünür tutmak gizlemekten iyidir.

**Kategori slug'ı forma hiç konulmadı** — salt okunur alan değil, alan yok.
Salt okunur yapmak "bir gün açılabilir" ihtimalini bırakırdı.

**Kullanıcı formunda parola alanı yok.** Yönetici formundan parola koymak
izsiz kimliğe bürünme kapısıdır.

**Yazar listesindeki "Tarih" sütunu** dökümde var, modelde karşılığı yok →
yerine **Unvan** kondu; uydurma tarih basılmadı.

**Galeri/video `haber_girme`ye bağlandı.** §11'in 14 yetkiliğinde bu ailelere
satır yok; yeni yetkilik açmak matrisi değiştirmektir ve migration ister —
model turunda diğerleriyle birlikte ele alınacak.


---

## 20. 27 Ağustos — vizyon takvimi: anahtarsız yol ölçülüp elendi

§12'nin "karar bekleyen dört madde"sinden biri kapandı.

### Ölçüm: Wikidata bu iş için yetersiz

`vizyon-takvimi.json` **0 film** içeriyordu ve bileşen §13'te siteye
bağlanmamıştı. Anahtarsız yedek (Wikidata SPARQL) ölçüldü:

| Ne ölçüldü | Sonuç |
|---|---|
| TR yayın yeri niteleyicili (P577 + P291=Q43) film | **1.389** — sorgu doğru çalışıyor |
| Yıla göre TR vizyon kaydı | 2020:87 · 2021:13 · 2022:31 · 2023:16 · 2024:33 · 2025:53 · 2026:19 |
| Türkiye'de gerçekte vizyona giren film | yılda ~200-300 → **kapsama %10-25** |
| 2026-06-01 sonrası TR vizyon kaydı | **5 film**, biri gelecek tarihli |

**Sebep yapısal:** Wikidata **geçmişi** kaydediyor, takvimi önceden yazmıyor.
Bileşen ise "önümüzdeki haftalar" istiyor. Sorgu penceresini geriye çevirmek de
kurtarmıyor — son üç ayda 4 film. **Wikidata çapraz doğrulama için durur,
yedek olarak güvenilmez.** Ölçüm betiğin başlığına yazıldı ki sonradan biri
"anahtarsız yedek var" sanmasın.

### Karar: TMDB ücretsiz anahtarı alınacak (kullanıcı, 27 Ağustos)

Seçenekler sunuldu (elle giriş · TMDB anahtarı · bileşeni kapatma); kullanıcı
**TMDB**'yi seçti. Anahtar kullanıcı tarafından alınacak.

**Hazırlık yapıldı ve sınandı.** Anahtarlar depoya girmiyor:

- `ortak.gizli_oku(ad)` — önce ortam değişkeni, sonra `canli-veri/gizli.json`.
  Ortam değişkeni tek seferlik deneme için öncelikli; **kalıcı çözüm dosya**,
  çünkü Görev Zamanlayıcı'dan koşarken ortam değişkeni her zaman görünmez.
- `canli-veri/gizli.json` **`.gitignore`da** — `git check-ignore` ile ve
  `git status`ta görünmediği doğrulandı. Örneği `gizli-ornek.json`.
- Anahtar yokken betik **çökmüyor**: önceki dosyayı koruyor ve neyin eksik
  olduğunu söylüyor (çıkış kodu 2, hata değil).

### Zamanlayıcı doğrulandı

§17'de kurulan üç görevden yalnız "sık" grubu koşmuştu; **saatlik ve günlük
gruplar hiç çalışmamıştı** (kuruldukları günün ilk tetiklenmesini
bekliyorlardı). İkisi elle tetiklendi: **üçü de `LastTaskResult 0`**, altı
veri dosyası tazelendi. Tazelenmeyen tek dosya vizyon — kaynağı yok, ve
bileşen doğru davranıp eldeki dosyaya dokunmadı.

### Hukuki teyit listesine eklenen madde

**TMDB ticari kullanım için kendisine danışılmasını istiyor.** Gazete ticari
bir yayın. Bu, §2'deki BİK ve Meta Yazar teyitleriyle, §12'deki TCMB ve MGM
teyitleriyle ve §15'teki Google Hizmet Şartları maddesiyle **aynı listeye**
girer. Film afişleri ayrıca telifli; §9 kararı gereği afiş **indirilmiyor**,
sayfada yerel yer tutucu duruyor.


---

## 21. 28 Ağustos — F7 arama: ölçüldü, eşik karşılanmadı, **site geneli hızlandı**

### Kesinti — önce bu

27 Ağustos akşamı üç ajan da **API oturum limitine** takılıp yarıda kesildi.
İki iz bıraktı: (a) bitmiş ama raporlanmamış işler, (b) **duran tarama** —
oturum kesilince arka plandaki tarama süreci de öldü ve 18:01'den 10:39'a
kadar **16 saat** boş geçti. Log temiz, hata yok, disk 350 GB boş; betiğin
kendi hatası değil.

**Alınan önlem:** tarama artık `calistir.ps1` ile **bağımsız süreç** olarak
koşuyor (makineyi uyanık tutuyor, düşerse kaldığı yerden devam ediyor).
Oturuma bağlı arka plan görevi olarak başlatılmayacak.

**Kural:** uzun işi arka planda yürüten ajan **biten her adımı ara rapor
olarak yazacak.** Bir ajan ölçümü bitirmiş ama raporlamadan kesildiği için
durum elle yeniden ölçülmek zorunda kalındı.

### F7(a) ölçüldü — eşiğin 5,8 katı

56 sorgu × 5-9 tur, dönüşümlü (aynı veritabanı durumu, aynı çekişme):

| | p50 | **p95** | en kötü |
|---|---|---|---|
| ESKİ (tam sayım + `govde`) | 920 ms | **1.759 ms** | 1.936 ms |
| YENİ (sınırlı sayım + kapı) | **475 ms** | **1.768 ms** | 1.885 ms |
| YENİ, tam HTTP yanıtı | **486 ms** | **1.748 ms** | 1.914 ms |

**Sorgu p50 yarılandı (−%48), p95 hiç kıpırdamadı.** Eşik 300 ms → **5,8 kat**.

**Neden:** sınırlı sayım yalnız 1.000'den çok sonuç dönen sorguyu hızlandırıyor
(50 sorgunun 28'i). p95'i belirleyenler **az/hiç sonuç dönenler** — sınıra
ulaşmadıkları için tam taramayı sonuna kadar yapıyorlar. Sınıf bazında:
tek kelime −%84 · Türkçe −%72 · uzun tümce **%0** · sonuçsuz **%0**.

### Beş yol karşılaştırıldı — kazanan önek araması

Sessiz kopyada (308.602 satır), aynı 56 sorgu:

| Yol | p50 | **p95** | 300 ms | Türkçe tutarlı |
|---|---|---|---|---|
| V1 `LIKE` (bugünkü) | 328 | **732** | ✗ | ✗ |
| V2 FTS5 `unicode61` | 14 | **188** | ✓ | ✓ |
| V3 FTS5 + Türkçe, tam kelime | 14 | **216** | ✓ | ✓ |
| V4 FTS5 `trigram` | 71 | **275** | ✓ | ✓ |
| **V6 FTS5 + Türkçe + önek (≥3)** | **35** | **235** | ✓ | ✓ |

**Trigram elendi — ilk bakışta kazanan görünüyordu.** `ışık` sorgusunda 6.458
sonuç dönüyor ama eşleşen kelimeler dökülünce **%83'ü rastlantı** çıktı:
`değişikliği` 793 · `bisiklet` 566 · `bağışıklık` 284. **Ve bu kusur bugünkü
`LIKE`'ta da var** — "ışık" arayan okur bugün "değişiklik" haberleri alıyor.

**Önek araması tam ortada:** Türkçe'de ekler sona geldiği için `token*` fiilen
kök bulma yerine geçiyor. Tam kelime eşlemesi ek almış biçimlerin
**%61-89'unu** kaçırıyordu (`ışık` 688 → önekle 1.171; `öğrenci` 1.285 → 5.412).
Disk: kelime indeksi **+47 MB**, trigram +253 MB.

### Türkçe harf kusuru — p95'ten önce gelen kusur

| kelime | küçük | Başlık | BÜYÜK |
|---|---|---|---|
| ışık | 1.880 | 428 | **0** |
| çağrı | 3.647 | 249 | **0** |
| öğrenci | 5.236 | 565 | **0** |
| bursa (ASCII) | 39.752 | — | 40.817 ✓ |

`__icontains` harf duyarsızlık **vaat ediyor**; SQLite'ın `LIKE`'ı bunu yalnız
ASCII'de yapıyor. **BÜYÜK HARFLE yazan Türk okur sıfır sonuç alıyor.** Arama
235 ms'ye insin ya da inmesin, bu ayrı ve daha ciddi bir kusurdur.
`test_turkce_kusuru_HENUZ_DURUYOR` bunu kilitliyor — düzeltildiğinde kırılıp
bilinçli güncellenecek.

### Yapılanlar — indekssiz, migration'sız

**Normalizasyon çekirdeği** (`icerik/arama_metni.py`): Türkçe-doğru küçültme +
ASCII katlama + minimum uzunluk + önek kuralı. **Motordan bağımsız** — sanal
tablo, tetikleyici, `MATCH`/`to_tsquery` yok; kaynak taramasıyla doğrulanıyor.
Durak listesi `icerik/veri/turkce_durak.json`, **veri olarak** (71 kelime +
`cikarilanlar` gerekçeleri), koda gömülü değil.

**Durak listesinden çıkarılan üç kelime**, arşivle (son 60.000 başlık)
doğrulanarak: `kim` (93 başlık, çoğu **özel ad**: "Kim Milyoner Olmak İster") ·
`artık` (isim anlamı: "artık yıl", "nükleer artık") · `az` (nicelik: "en az 10
kişi"). Şüphelenilen `son` (838) ve `büyük` (545) listede hiç yoktu.

**Çok kelimeli kenar durumu:** durak ve kısa terimler **atılır**, kalanla
aranır; red **yalnız geriye hiç terim kalmayınca**. `bursa ve çevresi` →
aranır. Aksi hâlde düzeltilen kusurdan kötüsü üretilirdi.

**Okur ne görüyor:** 1.000 üstü sonuçta "1.000+ sonuç" (altında kesin sayı) ·
`ve` → "çok genel kelimelerle arama yapılamıyor" · `a` → "en az 3 harflik bir
kelime yazın".

### Planlanmamış üçüncü kazanım — **en büyüğü, ve tüm siteye**

Kapıda reddedilen sorguda arama maliyeti 0 ms olmasına rağmen HTTP yanıtının
1.200 ms sürmesine takılıp kabuk ölçüldü:

```
/ara?q=a  (arama YOK)          1.138 ms
/ilceler  (en yalın sayfa)     1.129 ms
bağlam işlemcisi tek başına    1.129 ms
  -> _tum_kategoriler()        1.118 ms   <- kabuğun tamamı
```

`icerik/baglam.py`'deki `annotate(adet=Count("haberler"))` her istekte 308 bin
satırlık tabloyu tarıyordu — ve bağlam işlemcisi **her sayfada** çalışıyor.
Üstelik `adet` **hiçbir şablonda basılmıyor**, yalnız menüyü sıralıyor.
**Site, okura gösterilmeyen bir sayı için sayfa başına 1,1 saniye ödüyordu.**

300 sn önbelleğe alındı (kilit gelirse son bilinen liste, o da yoksa boş menü —
sayfa düşmez): **HTTP p50 1.674 → 486 ms (−%71) · p95 2.954 → 1.748 (−%41).**
Artık HTTP (486) ile sorgu (475) neredeyse eşit: **kabuk darboğaz değil, arama
sorgusu.**

> **Bu bulgunun F4 turunda yakalanmamış olması öğretici.** O tur yerleşim ·
> kontrast · taşma · odak ölçüyordu; hepsi doğruydu, hepsi geçti — ama
> **hiçbiri süre ölçmüyordu.** Sayfa görsel olarak kusursuz olup yüklenmesi
> saniyeler sürebilir. Ölçüm turlarına **süre ve sorgu sayısı** eklendi.

### Site geneli tur — 14 sayfa, 9 tur

| sayfa | önce | sonra | sorgu |
|---|---|---|---|
| **kategori** | 405 ms | **21 ms** | 12 → 12 |
| **yazar listesi** | 50 ms | **32 ms** | **83 → 46** |
| **ilçe** | 734 ms | 745 ms | düzeltilmedi (veri sorunu) |
| **TOPLAM** | **1.425 ms** | **1.035 ms** | **246 → 209** |

Sonuç: **p50 17 ms · p95 291 ms**; ilçe hariç en kötü **47 ms**.

### Üç ders — ikisi olumsuz sonuçtan

1. **Az sorgu her zaman hızlı değil.** Yazar listesindeki N+1 tek sorguya
   çevrildi, sonra ölçüldü: yazar başına sorgu **19,0 ms**, tek sorgu
   **42,9 ms**, pencere fonksiyonu 41,0 ms. 37 sorgunun her biri indeksten ilk
   satırı alıyor (0,5 ms); "düzeltme" 37 başlık için **6.713 satır** çekiyor.
   Düzeltme **geri alındı**, yalnız şablonun aynı veriyi iki kez çağırması
   giderildi (83 → 46 sorgu).
2. **`defer("govde")` ölçüldü, çalışmıyor, kaldırıldı.** Medyan 4,14 → 3,77 ms
   ama **en iyi değer kötüleşti** (2,86 → 3,33); kazanç gürültü içinde. Buna
   karşılık ertelenmiş alan sessiz bir tuzak: gövdeye erişen kod satır başına
   sorgu açar. **Ölçülemeyen kazanç için tuzak taşınmaz.**
3. **Önbellek yalnız değişmeyene.** Kategori menüsü ve arşiv sayıları gün
   içinde değişmiyor → önbellek. **Haber listelerine önbellek konmadı** —
   gazetede beş dakika eski manşet kabul edilemez; kategori sayfasının
   maliyeti önbellekle değil **sayımı sınırlayarak** indirildi.

### F7'nin durumu

**(a) karşılanmadı** — p95 1.748 ms, eşiğin 5,8 katı. Neden değişmedi:
`LIKE '%…%'` indeks kullanamıyor. Türkçe harf kusuru da duruyor. **İkisini de
indeks çözecek**; kurulumu göç sonrasına ve PostgreSQL kararına bağlı.

**(b) ölçüldü, otomatik taşıma mümkün değil** — bkz. §22 ve
`PANEL-NOTLARI.md` §24: 50 yuvanın yalnız **6'sı** konum+ölçü+cihaz olarak
ayrışıyor, cihaz bilgisi **43'ünde hiç yok**. Elle eşleme kalemi.

### PostgreSQL — muhakeme, ölçüm değil

**Normalizasyon işi boşa gitmiyor.** PostgreSQL'in `lower()`'ı da veritabanı
derlemine bağlı; Türkçe olmayan bir derlemde `lower('I') = 'i'`, yani **aynı
i/I tuzağı orada da var**. Atılacak olan yalnız motora özgü ~30 satır (sanal
tablo, üç tetikleyici, `MATCH` kurucusu); karşılığı `to_tsvector` + GIN + `:*`.

**PostgreSQL'in gerçek üstünlüğü** ölçülen iki zayıf noktayı kapatıyor:
`turkish` yapılandırması **gerçek Snowball kök bulucu** (önek numarasına gerek
kalmaz) ve **hazır Türkçe durak listesi** (`bir`/`ve`/`in` sorunu biter).

**Önerilen sıra:** (a) normalizasyon şimdi — taşınabilir, yapıldı;
(b) FTS5 indeksi göç bitene kadar ertelendi — tetikleyiciler göçü 7×
yavaşlatır, indeks sonradan **5 saniyede** kurulur; (c) PostgreSQL yakınsa
indeksi doğrudan orada kurup FTS5 adımını atlayın. **Karar kullanıcıda.**


---

## 22. 28 Ağustos — F3 kapandı: göç arşive yetişti

| Aile | Diskte | Veritabanında | Oran | Görselli |
|---|---|---|---|---|
| **haber** | 357.099 | **356.839** | **%99,93** | %18,0 |
| video | 31.084 | 31.084 | %100 | %99,5 |
| köşe | 6.713 | 6.713 | %100 | %100 |
| galeri | 4.040 | 4.040 | %100 | %99,9 |

Kalan 280 dosya **taramanın göçün önünde olması**; hepsi az önce kazınmış
2024-02 kayıtları, kategorileri geçerli.

### Düşen kayıt: **sıfır**, neden bazında

| Neden | Sayı |
|---|---|
| Bozuk / yarım JSON | **0** |
| Adres çözülemedi | **0** |
| Yinelenen kimlik | **0** |
| Kategori tanınmadı | **4 → 0 (düzeltildi)** |

O dört kayıt 2022-01'deki `bursada-spor` slug sapmasıydı — F2(d)'nin 301 ile
çözdüğü tam o dört adres. **Adres katmanı biliyordu, göç bilmiyordu.**
`goc_al` artık slug'ı `Yonlendirme` tablosundan okuyor; koda slug gömülmedi,
tek doğruluk kaynağı korundu.

### Asıl bulgu: kaynak **2023-11'de başlıyor**

Ay bazında "gerçek dış kaynak adı" oranı (300 örnek/ay, arşivden doğrudan):

| Dönem | Oran |
|---|---|
| 2021-04 … 2023-08 | **%0,0 – %2,0** |
| 2023-09 | %4,7 |
| 2023-10 | %2,3 |
| **2023-11** | **%82,3** |

2023-11 örneği (600 kayıt): TRT Haber 104 · Haber Merkezi 100 · İHA 99 ·
DHA 81 · MyNet 66 · AA 65 · TRT Spor 25 · Milliyet 10.

**Arşiv JSON'unda ayrı künye alanı yok:** 22 alanın hiçbiri kaynak taşımıyor,
`yazar` %100 "Bursa Hakimiyet", `yayinci` %100 "Bursa Hakimiyet" (3.857
örnek). Gövde sonu ajans imzası %0,2, gövdede "Kaynak:" satırı %0,1.

> **Yorum tersine döndü.** "Arşivin %99,8'i kaynaksız" bir göç kusuru değil:
> **2023-10 öncesi kaynaksızlık verinin gerçeğidir** — gazete kendi yazdığına
> "Haber Merkezi" damgalıyordu. Kaynağı olmayan habere kaynak üretilemez.
>
> Gerçek kusur başkaydı: `asil_kaynak_bul` **gövdeyi html'den önce** tarıyor
> ve gövdedeki "kaynak suyu / kaynak-kodu" tamlaması sayfanın gerçek alanını
> yeniyordu. Kaynak kapısı (`icerik/goc_kaynak.py`) bunu kesiyor.

Tarama 2023-11'e girdikçe oran **kendiliğinden** yükseldi:
**721 → 19.149 bağ**, kaynak kaydı **148 → 237**.

`kaynak_denetle` komutu daha önce kurulmuş **yanlış bağları kopardı**;
`Kaynak` kayıtlarının kendisi **silinmedi** — kaydı silmek izi de siler,
hangi haberin hangi yanlış değere bağlandığı bilgisi kaybolur.

### İlçe alanı — **türetildi**, kaynakta yok

Ölçüm: `ilce_id` **309.882 kaydın hepsinde NULL**'du ve `goc_al` bu alandan
hiç söz etmiyordu. Sonucu: **17 ilçe sayfasının tamamı boştu**; menüde ve
künyede 17 bağlantı boş sayfaya gidiyordu. F4 turunun "ilçe sayfası
veritabanından render ediliyor" ölçümü **yanlış değildi** — ediyordu, veri
yoktu.

Arşivde ilçe alanı **yok**: `kategori_etiketi` yalnız 12 kategori adı veriyor,
klasik "İNEGÖL (İHA) -" tarih satırı 8.512 kayıtta **5** kez geçiyor. Tek yol
başlık+spotta ilçe adı aramak: **%5,5 tek eşleşme**, %0,2 belirsiz (elendi).

**Mahalle ipuçları bilerek kullanılmadı.** `sozluk.json`daki ipuçları %0,7 ek
kayıt getiriyor ama neredeyse tamamı yanlış:
*"Şeyh Cerrah'ta Filistinlilere müdahale" → İnegöl* ·
*"Denizli'de tarihi eser" → Osmangazi* (heykel=yontu) ·
*"Alerjik Rinit" → İnegöl* (cerrah=hekim).
**Yanlış ilçe etiketi boş sayfadan kötüdür.**

Sonuç: **20.366 haber ilçe aldı, 17 ilçenin hepsi doldu** (İnegöl 3.929 ·
Yıldırım 3.269 · Nilüfer 2.693 … Büyükorhan 62). Doldurma tamamen veritabanı
içinde çalışıyor (başlık/spot zaten kolonda), arşiv okunmuyor — **saniyeler**.

> **KARAR (28 Ağustos): çıkarım kalıyor, ama GÖRÜNÜR olacak.**
> Gerekçe: alternatif 17 boş sayfa ve menüde 17 ölü bağlantı; %5,5 muhafazakâr
> bir oran; editör panelden düzeltebiliyor ("İlçe ata" toplu fiili); geri
> alınabilir (`ilce_doldur --uzerine-yaz`).
>
> **Şart:** ilçe bilgisi **kaynakta yoktur, başlık/spot eşlemesiyle
> türetilmiştir** ve bu belgelerde yazılıdır. Türetilmiş bir değeri kaynaktan
> gelen olgu gibi sunmak, bu turda düzeltilen kaynak hatasının ta kendisidir
> (`articleAuthor` alanının kaynak sanılması).

### `ANALYZE` — standart adım oldu

SQLite istatistikleri **bayattı**: `sqlite_stat1` tabloda **92.666** satır
sanıyordu, gerçekte 356.839 vardı. Planlayıcı bu yüzden `ilce_id` indeksini
işe yaramaz sayıp **tam tarama** seçiyordu: ilçe sayfası **745 ms**, indeks
zorlanınca aynı sorgu **0,2 ms** — **3.600 kat**.

`ANALYZE` (2,0 sn) sonrası plan `SEARCH ... USING INDEX` oldu ve sayfa
**745 → 26 ms**'ye indi.

> **Kural:** `ANALYZE` göç sonrası **ve migration sonrası** standart adımdır.
> SQLite şema değişikliklerinin çoğu tabloyu kopyalar ve istatistikleri
> yeniden bayatlatır; migration paketinin sonunda `ANALYZE` yoksa ilçe sayfası
> 26 ms'den 745 ms'ye **sessizce** geri düşer.

### Maliyet sorusu — yeniden işleme gerekmiyor

Kazıyıcı her adresi bir kez yazıyor, JSON'lar değişmiyor; tam koşu aynı veriyi
okur. Kaynak bağları için de gerek yok — `kaynak_denetle` ara tabloda düzeltti.
Tam koşu **~65 dk**, `--yalniz-yeni` **~2 dk**.

### Sıradaki iki iş (model turu sonrasına bırakıldı)

1. **`meta_yazar` backfill** — migration istemiyor, alanlar duruyor:
   "Haber Merkezi" → `haber_merkezi`, "Bülten" → `bulten`; gerçek ajans →
   `kaynak_turu="ajans"`, diğerleri `dis_yayin`. Kapıdan elenen bilgi böylece
   çöpe gitmez. Açık nokta: `bulk_create` `save()` çağırmıyor ve
   `meta_yazar_elle` semantiği panelin.
2. **`Index(fields=["ilce", "-yayin_zamani"])`** — `ANALYZE` sonrası kalan
   `USE TEMP B-TREE FOR ORDER BY` maliyetini kaldırır. Migration gerektirdiği
   için model turunun paketine dahil edildi.


---

## 23. 28 Ağustos — menü sidebar'a çevrildi (kullanıcı isteği)

Kullanıcı: *"menüyü de küçült ve daha kompakt bir hale getir, ilçeleri menü
içerisinde de açılır kapanır bir liste yap, gerekirse menüyü sidebar yap"*.
Sidebar kararı koordinatörde bırakıldı ve **sidebar yapıldı** — dikey yapı
katlanır bölümlerle doğal uyuşuyor ve ekranı kaplamıyor.

### Ölçülen kompaktlık

| | önce | sonra |
|---|---|---|
| Menü içerik yüksekliği | **780 px** | **489 px** (−%37) |
| Tüm bölümler açıkken | 780 px | 1.349 px → katlanınca 489 (−%64) |
| Panel genişliği | 340–1100 px | **320 px** sabit |
| Ekranın kapladığı oran @1280 | %74 | **%25** |
| Kaydırma gerekiyor mu | evet | **hayır** |
| Konum | banda yapışık, tam genişlik | sağ kenara yaslı, tepeden tabana |

Kazancın kaynağı iki şey: dört bölümün katlanması **ve** uzun listelerin
(13 kategori, 18 ilçe) iki sütuna inmesi. Yalnız katlamayla 717 px'de kalıyordu.

**Yapı:** 5 `<details>`/`<summary>`, yalnız **KATEGORİLER `open`**. Başlıklar
`<summary><h2>` içinde — belge başlık düzeni bozulmadı (atlama 0). Perde ayrı
öğe değil, `0 0 0 100vmax` yayılımlı ikinci gölge; gölge tıklama yakalamadığı
için "dışarı tıkla kapat" davranışı olduğu gibi çalışıyor.

**Korunanlar:** bant **10 kalem** · arama ve menü düğmesinin bant içindeki yeri
· menüdeki **50 bağlantı** · **17 ilçe + "Tüm ilçeler" = 18** — hepsi DOM'da,
`hidden` yok, sonradan yükleme yok.

## Üst bant birleştirildi — 29 Ağustos 2026

Logo kendi 93 px'lik beyaz şeridindeydi ve o şeridin **%82'si boştu**: bant
1100 px, logo 196 px. Beş şerit üst üste diziliyordu (servis 38 · logo 93 ·
kategori 44 · son dakika 40 · reklam 150) ve **1280×900'de içerik y=379'da**,
yani ekranın %42'si haber görmeden geçiyordu.

**Karar:** logo şeridi kalktı, logo yapışkan kategori bandının soluna girdi.
Diğer iki seçenek — şeridi doldurmak, ya da kaydırınca daraltmak — reddedildi;
bu en çok yeri kazandıran ve JavaScript'e en az yaslanan yol.

### Bant sözleşmesi BOZULMADI

İlk hesap "10 kalem sığmaz, 6-7'ye insin" diyordu (logo 130 + kategoriler 830
+ arama 180 + menü 90 = 1230 > 1100). Sözleşme F1 ölçütü olduğu için önce
daraltma denendi ve **ölçüm haklı çıkardı**: yazı 15→13,5 px, iç boşluk
11→8 px, logo 58→30 px yükseklik.

| Genişlik | Bant | Kalem | Taşma |
|---|---|---|---|
| 1024 · 1119 | 42 px, tek satır | 10 | 0 |
| 1120 · 1280 · 1600 | 42 px, tek satır | 10 | 0 |
| 360 · 768 · 1000 | 78-82 px, iki satır | 4 (+6 DOM'da) | 0 |

**İçerik başlangıcı 379 → 284 px** (masaüstü), 379 → 344 px (360 px).

### Dar ekranda kategoriler geri geldi

`.kategori-liste{display:none}` kuralı 1000 px altında bandı boşaltıyordu —
**360 px'te görünen kategori sayısı sıfırdı**, yerel gazetenin okuru
"Bursa"ya tek dokunuşla gidemiyordu. Artık dört kalem kendi satırında
duruyor: Bursa · Bursaspor · Gündem · Spor. Kalan altısı CSS ile gizli,
**DOM'da** — menüdeki 17 ilçeyle aynı gerekçe.

Son kalemin ayracı sunucu tarafında (`mobil_son`) işaretleniyor: CSS
`:last-of-type` burada **"Resmî İlan"ı** seçerdi, o da gizli.

### İki tuzak

1. **`<header>` sarmalayıcısı yapışkanlığı öldürüyordu.** `position:sticky`
   ancak ebeveyninin kutusu içinde tutunur; nav'i yüksekliği kendisiyle aynı
   olan bir header'a almak bandı ilk kaydırmada ekrandan çıkarıyordu.
   Sarmalayıcı kaldırıldı, gizli `h1` nav'ın kardeşi olarak duruyor.
2. **Bant sözleşmesi testi yanlış nedenle kırıldı.** `<a href=` kalıbıyla
   sayıyordu; dört kaleme `class` eklenince dördünü kaçırdı ve "6 != 10"
   dedi. Sözleşme duruyordu, kalıp kırılmıştı — sayım `<a\s` oldu.

## Reklam anahtarı — 29 Ağustos 2026

Reklam panolarını kapatan düğme **sunum aracıdır, okur özelliği değil**:
yayın ekibine sayfayı reklamsız gösterebilmek için. Sıradan ziyaretçiye
**çizilmez** — reklam gizleme düğmesi gelir modeline dokunur.

- **Kapı:** geliştirme makinesi (`127.0.0.1`/`localhost`) ya da panele
  girmiş `is_staff` kullanıcı — `icerik/baglam.py`, `_reklam_dugmesi`.
- **Tercih** `<html data-reklam>` üzerinde, `localStorage`'da saklanır ve
  `<head>` içindeki minik betikle **sayfa çizilmeden** okunur; sonradan
  okunsaydı panolar bir an görünüp kaybolurdu.
- **Tek CSS kuralı yedi yuvanın hepsini** kapatıyor (ölçüldü: 7 → 0).
  Kapalıyken içerik y=234'e çıkıyor.
- `aria-pressed` durumu, düğme yazısı ("Reklamları gizle" ↔ "göster")
  ile birlikte değişir. `localStorage` atarsa düğme çalışmaya devam eder,
  tercih yalnız o oturumda yaşar.

### Bulunan iki gerçek kusur

1. **`summary` odak halkası kuralında yoktu.** Kural `a,button,input,select`
   sayıyordu; katlanır başlıklar tarayıcının soluk varsayılan halkasına
   düşüyordu. `summary:focus-visible` eklendi.
2. **Odak tuzağı kırıktı — 70 Tab'ın 53'ü menüden kaçıyordu.** Sebep ince:
   kapalı `<details>` içeriği Chrome'da `display:none` değil,
   **`content-visibility`** ile atlanıyor — kutu döndürüyor ama **odak
   alamıyor**. Tuzak "son öğe" olarak asla odaklanamayan bir bağlantıyı
   seçiyor, sarma koşulu hiç gerçekleşmiyordu. Bu kusur menü sidebar'a
   çevrilmeseydi de vardı.

### Doğrulama

Yatay taşma menü **kapalıyken 0/40**, **açıkken 0/40** (5 sayfa × 8 genişlik) ·
kontrast eşiği altında **0** (2.587 metin öğesi) · odak kaçışı **0** (70 Tab +
20 Shift+Tab, katlı ve açık hâlde) · bant kalemi **10** · h1 **1**, başlık
atlaması **0**. Testler **454/454** (15'i bu turda).

**Ölçüm artefaktı — beşinci kez.** İlk turda "37 öğede odak halkası yok"
çıktı; 37 = 6+18+6+7, yani tam olarak **katlı bölümlerdeki** bağlantılar. Odak
alamadıkları için hesaplanan stil değişmiyor. Tüm bölümler açıkken **0/212**.
§18'deki gizli menü artefaktının aynısı; halka kuralı **bu bulguya dayanarak
değiştirilmedi**, gerçek kusur olan `summary` ayrıca doğrulanıp düzeltildi.


---

## 24. 28 Ağustos — panel başarımı: **32 saniyeden 31 ms'ye**

Kullanıcı: *"panel çok ağır çalışıyor, bunu çok daha optimize etmemiz lazım,
bir de haber ekle sayfasını tekrar gözden geçir orada geliştirilebilecek
alanlar var"*. Şikâyet **ölçüldü ve doğru çıktı**.

### Teşhis — tek bir form alanı

Gerçek HTTP üzerinden, giriş yapılmış oturumla, 3 tekrar:

| sayfa | en iyi | boyut |
|---|---|---|
| **`/panel/haber/ekle`** | **32.702 ms** | **36.544.411 B** |
| `/panel/mansetler` | 3.851 ms | 6.428 B |
| `/panel/` (Bugün) | 2.287 ms | 4.798 B |
| diğer 10 ekran | 12–130 ms | |

Form alanı bazında ölçüm kök nedeni verdi:

```
select name=ilgili_haberler   option= 356.839   boyut= 34.826.896   <- sayfanın %99,9'u
select name=kaynaklar         option=     237   boyut=      10.200
diğer 28 alan                                   toplam ~12 KB
```

`ModelMultipleChoiceField` queryset'in **tamamını** `<option>` diye basıyordu.
Editör bir haber eklemek için **36 MB indirip 48 saniye** bekliyordu. Bu, §19'un
"akış 9 ms" tablosunda görünmedi çünkü o tur **liste** ekranlarını ölçmüştü;
**form ekranları hiç ölçülmemişti**.

### Sonuçlar — üç hedef de tuttu

| sayfa | önce | sonra (DEBUG=0) | bağımsız doğrulama |
|---|---|---|---|
| **Haber ekle** | 32.702 ms / 36,5 MB | **45 ms / 24 KB** | **31 ms / 24.365 B** |
| **Manşetler** | 3.851 ms | **15 ms** | **11 ms** |
| **Bugün** | 2.287 ms | **9 ms** | **9 ms** |

Sonuçlar koordinatör tarafından **sunucu yeniden başlatılıp bağımsız ölçüldü**;
ajanın sayılarıyla uyuştu.

**Çözüm:** `SecilenlerWidget` yalnız **seçili** olanları basıyor; yenisi
`/panel/haber-ara` JSON ucundan geliyor ve uç **`arama_metni.sorgu_coz`**
kullanıyor — ikinci bir arama mantığı yazılmadı, sitenin durak-kelime ve
en-az-uzunluk kapısı aynen geçerli. Doğrulama tüm haberleri kabul etmeye devam
ediyor (`pk__in` ucuz). **Betiksiz çalışıyor:** JS kapalıyken bağlı haberler
görünür, kaldırılabilir, **haber kaydedilebilir**; testle kilitli.

### Bugün'ün kök nedeni — iki tahmin de yanlıştı

Koordinatör "muhtemelen `Count` içeren annotate" dedi, ajanın ilk tahmini de
başkaydı. **Ölçüm ikisini de çürüttü:** sorun **veri dağılımı**.

`icerik_haber`in **356.839 satırının tamamı `durum=1, hazirlik=''`**.
`sqlite_stat1` bu yüzden `356839 356839 356839` diyor — "bu alanlar hiçbir şeyi
daraltmıyor". SQLite `LIMIT 20` sorgusunda indeksi bırakıp tam tarama seçiyor
ve eşleşen kayıt olmadığı için taramayı **sonuna kadar** sürdürüyor. Aynı
indeks `COUNT`ta **örtücü** kullanılıp 0,1 ms sürüyor.

**Çözüm kod tarafında:** kuyruk sayımı (0,1 ms) boşsa üç pahalı liste sorgusu
hiç çalıştırılmıyor. Aynı denemede `durum<>1` **kısmi indeksi işe yaramadı**
(738 ms) — denenip başarısız olan yol da raporlandı.

### Manşet indeksi — ilk deneme başarısız oldu, ve bu kayda değer

Django'nun `Index(condition=Q(manset_ana=True))`'i `WHERE "manset_ana"`
(**çıplak sütun**) üretiyor; ORM tek filtrede de OR'da da yine çıplak yazıyor —
ama **SQLite çıplak koşullu kısmi indeksi OR içinde eşleştirmiyor.** İndeksler
kuruldu ve **hiçbir işe yaramadı** (749 ms, plan hâlâ `SCAN`).

Yalıtılmış tabloda 3 indeks biçimi × 5 sorgu biçimi ölçüldü:

| indeks koşulu | tek çıplak | tek `=1` | OR çıplak | OR `=1` | OR `>0` |
|---|---|---|---|---|---|
| `WHERE "x"` | **KULLANDI** | hayır | hayır | hayır | hayır |
| `WHERE "x" = 1` | hayır | **KULLANDI** | hayır | **KULLANDI** | hayır |
| `WHERE "x" > 0` | hayır | hayır | hayır | hayır | **KULLANDI** |

ORM'in yazdığı biçimle eşleşen tek çalışan hücre: **çıplak indeks + tek
sütunlu sorgu**. Çözüm indeksi zorlamak değil, **görünümü OR yerine üç ayrı
indeksli sorguya çevirmek** oldu (`.order_by()` şart — Meta sıralaması
planlayıcıyı başka indekse çekiyordu). Sonuç: **752 ms → 0,69 ms**.

### Haber formu — §4'e karşı denetim

| Kalem | §4/§21 | Not |
|---|---|---|
| Başlık/spot **karakter sayacı** | alan 2, 4 | `data-sayac` işareti vardı, karşılığı yoktu |
| **Paragraf sayacı** | alan 5 | 2 altında kırmızı |
| **Adres önizlemesi** | alan 14 | slug kuralı §8'in ölçülmüş kuralı |
| **Hazırlık yalnız Pasif'te** | §9 | kural yazılıydı, **üründe uygulanmıyordu** |
| **İkinci başlık varsayılan kapalı** | alan 3 | `<details>` — betiksiz de çalışır |
| **Bağlı galeriler** | alan 27 | eksikti; **aynı `SecilenlerWidget`** kullanıldı |
| **Doğrulama sonrası odak** | §21 | `<details>` kapalıysa açıp odaklıyor |
| **Dokuz alanın Türkçe etiketi yoktu** | proje kuralı | ekranda "Gorsel url", "Gomulu kod", "Seo baslik" |

Son kalem **ekran görüntüsünden** bulundu; hiçbir sayısal ölçüm göremezdi.
Dokuzuncusu testi yazarken çıktı: `ilgili_haberler` ve `etiketler` formda
açıktan tanımlı olduğu için `Meta.labels` onlara hiç uygulanmıyordu.

**Yapılmayanlar:** etiket çip arayüzü (orta ölçekli JS) · konu bağlama (konu
modeli yok) · **görsel yükleme** (§4 alan 8 — depolama, kırpma ve boyut
politikası kararı gerektiriyor, `MEDIA_ROOT` yok; **kullanıcıya soruldu,
cevap bekleniyor**).

### Migration'lar

- **`0006`** üç kısmi manşet indeksi (koordinatör onayladı; ölçülen kazanç
  752 ms → 0,69 ms, migrate **4,26 sn**)
- **`0007`** bağlı galeriler M2M (**izin manşet indeksleri içindi**; ajan
  uyguladı, bildirdi ve geri alma yolunu yazdı — koordinatör onayladı,
  belirsizlik koordinatördeydi: galeri seçicisi istenmişti ve migration
  gerektiriyordu)

İkisinde de `sqlmigrate` **uygulamadan önce** okundu ve `icerik_haber`in
yeniden kurulmadığı doğrulandı (`new__icerik_haber` 0 · `DROP TABLE` 0 ·
`INSERT INTO` 0); paket sonunda **`ANALYZE`**; `integrity_check` **ok**,
356.839 haber değişmedi.

### Ölçüm aracı altıncı kez yanılttı

Yerleşim turu **14 bulgu** verdi: "Haber ekle, tüm genişlikler: odak halkası
yok". Araç hangi öğe olduğunu söylemiyordu; kimlik yazdırma eklenince
`#id_ikinci_baslik` çıktı — yani `<details>` içine alınan alan.

**Araç yeşile boyanmadan önce iddia sınandı:** 60 Tab basıldı, öğeye **hiç
ulaşılmadı**; `offsetParent` ise dolu (Chrome kapalı details içeriğini
sayfa-içi aramaya açık tutuyor). Kusur sayfada değil **ölçüm süzgecindeydi**.
`test_kapali_details_klavye_sirasinda_mi` kalıcı kanıt olarak duruyor — bir gün
tarayıcı davranışı değişirse test kırılır.

### Bilinen sınır

`/panel/haber-ara` yaygın terimde **7 ms**, nadir terimde **772–789 ms**
(`icontains` tam tarama). Aynı kusur sitenin kendi aramasında da var (§21);
çözümü F7'nin normalize alan + indeksi ve o göç sonrasına + PostgreSQL
kararına bağlı. Tip-ahead için ideal değil ama **eskisi 32 saniyeydi ve hiç
arama yoktu**.

### Not — ölçüm hijyeni

Ajan ölçüm için `yonetmen` parolasını değiştirdi ve **bunu bildirdi**;
koordinatör geri aldı (üç deneme hesabı da yine `deneme1234`). Kural: ölçüm
için parola değiştiren, turun sonunda kendisi geri alır.


---

## 25. 28 Ağustos — `meta_yazar` backfill: kapıdan elenen bilgi kurtarıldı

§22'nin kaynak kapısı yanlış bağları kopardığında **elenen bilgi çöpe
gitmiyordu** — "Haber Merkezi", "Bülten" gibi değerler kaynak değil **Meta
Yazar Bilgisi** (`PANEL-NOTLARI.md` §7) ve doğru alanları vardı. Backfill o
bilgiyi yerine koydu.

### Dağılım — önce / sonra

| `meta_yazar` | Önce | Sonra |
|---|---|---|
| *(boş)* | 356.839 | **358** |
| `haber_merkezi` | 0 | **336.547** |
| `alinti` | 0 | **10.412** |
| `haber_ajansi` | 0 | **8.854** |
| `bulten` | 0 | **545** |
| `fikir_iscisi` | 0 | **123** |

| `kaynak_turu` | Önce | Sonra |
|---|---|---|
| `ajans` | 356.839 *(hepsi varsayılan)* | 346.304 |
| `dis_yayin` | 0 | **10.412** |
| `muhabir` | 0 | **123** |

**Dokunulmayan 358 kayıt**, kaynak alanı çöp olan (gövdeden düşmüş parça)
kayıtlar — sayfanın gerçek değeri hiç okunmadığı için **bilinmiyor** ve
uydurulmadı. `meta_yazar_elle` korunanı 0 (tablo boştu) ama kural yine de
kodda: `filter(meta_yazar_elle=False)`.

Sınıflandırma denetlenebilir olsun diye adlar da yazdırıldı — ajans tarafı
İHA 3.540 · AA 3.107 · DHA 2.169 · Reuters 34; dış yayın tarafı TRT Haber
2.511 · MyNet 2.299 · Milliyet 2.061. **TRT Haber ve BBC bilerek `dis_yayin`
sayıldı**: §5 ayrımı yayın kuruluşlarını ajanstan ayırıyor, ajans listesi dar
tutuldu.

### `save()` bilerek çağrılmadı — tuzak tersine dönüyordu

Koordinatör "`bulk_create` `save()` çağırmıyor, bunu hesaba kat" demişti.
Ölçüm bunun **tersini** gerektirdi: `Haber.save()` içindeki
`meta_yazar = META_TURETIM[kaynak_turu]` türetimi çalışsaydı, ölçülen
`haber_merkezi` değerini varsayılan `kaynak_turu='ajans'`ten türetip
**`haber_ajansi`ye çevirirdi** — yani kaynağı olmayan 336 bin haberi "ajanstan
geldi" diye damgalardı. Bu, §22'de düzeltilen hatanın aynısı olurdu.
`QuerySet.update()` türetimi atlar ve ölçüyü korur.

### Süre

Okuma **3.481 sn (58 dk)** · yazma **22,8 sn** · `ANALYZE` **1,2 sn** ·
toplam **3.505 sn**. Yazma §24'ün ~16 sn tahminiyle uyumlu; asıl maliyet
484 bin dosyalık arşiv okuması ve arşiv taraması `D:`yi doyurduğu için
I/O bağımlıydı.

### Yan bulgu — üçüncü yer tutucu kusuru

Kaynak tablosunda **`Seçiniz` (47 haber)** ve **`Diğer` (2)** vardı: mevcut
panelin açılır listesinin **seçilmemiş hâli** kaynak diye kaydedilmiş.
Kapıya `yer tutucu (secilmemis)` reddi eklendi; `kaynak_denetle` 49 bağı
kopardı (19.149 → **19.100**), kayıtlar silinmedi.

Ayrıca **4 kaynak adı gazetenin kendi köşe yazarıydı** (Erhan Bedir 63 ·
İsmail Karaduman 45 · Süha Gürsoy 10 · Coşkun Saitoğlu 5) — §5'in işaret
ettiği kusur. `medya.Yazar` tablosuyla **ad eşleşmesinden** bulundu, tahminle
değil; o 123 haber artık `muhabir` / `fikir_iscisi`.

### Karar bekliyor — migration ister

`haber_merkezi` ve `bulten` için **doğru `kaynak_turu` yok**; üç seçenek de
yanlış olurdu, o yüzden 337.092 kayıtta alana dokunulmadı ve hâlâ varsayılan
`ajans` görünüyorlar. **Risk:** bu kayıtlardan biri panelden kaydedilirse
`save()` türetimi `meta_yazar`ı `haber_ajansi` yapıp ölçümü ezer.

**Kalıcı çözüm:** `kaynak_turu`yu `blank=True` yapmak — `meta_yazari_turet()`
zaten boş türde `"haber_merkezi"` döndürüyor, yani türetim kendiliğinden doğru
sonucu verir. Migration gerektirdiği için **bir sonraki tura bırakıldı**.

### Göç tazelemesi bekliyor

Arşiv taraması bu tur sırasında **484.678 dosyaya (%87)** ulaştı; **126.842
kayıt henüz göçmedi**. `--yalniz-yeni` ile alınacak, ardından
`meta_yazar_doldur` yeni kayıtlar için **tekrar koşmalı**.

---

## 26. 29 Ağustos — kaynak türü yalanı temizlendi, panel tabloları dolduruldu

Bu tur §25'in açık bıraktığı iki maddeyi kapatıyor ve panel model turunun
"dokuz tablo boş" kalemine giriyor. Üçü de **ölçümle** yürüdü.

### 26.1 Tarama 17,5 saat ölü yatmış

Sabah bulunan ilk şey buydu: tarama 28 Ağustos 18:45'te düşmüş, 29 Ağustos
12:18'e kadar kimse çalıştırmamış. Kayıp yok (tarama kaldığı yerden devam
ediyor), kaybedilen **zaman**. `calistir.ps1` yeniden, ayrı bir pencerede
bağımsız süreç olarak başlatıldı.

**Yan ölçüm — kaynak site bugün hasta.** Yeniden başlayan koşunun gerçek
çekim hızı iki ayrı pencerede **0,31 kayıt/sn** ölçüldü (atlanan kayıtlar
sayılmadan); aynı taramanın 27-28 Ağustos ortalaması **5-6 kayıt/sn**, tepe
değeri 12,8. Yirmi kat fark tarayıcıda değil karşı tarafta:

* canlı siteden arka arkaya üç anasayfa isteği **7,4 sn · 42,5 sn · 0,39 sn**
  sürdü;
* çekim penceresinde **50 istekten 11'i HTTP 502** aldı — sunucunun kendi
  ağ geçidi hatası, bizim hız sınırımız değil (429/403 gelmiyor).

**Bu bir tarama sorunu değil, yayın sorunu.** Aynı 502'leri ve 42 saniyelik
bekleyişi okur da yaşıyor. Kodda değişiklik yapılmadı: eşzamanlılığı artırmak
zaten zorlanan kendi sunucumuzu daha çok zorlamak olurdu. 502 alan kayıtlar
diske yazılmadığı için sonraki koşuda yeniden denenirler.

Bu hızda kalan ~90 bin çekilmemiş kayıt **günler** alır. Site toparlarsa
tarama kendiliğinden hızlanır; ölçüm `disa-aktarim/durum.py` ile bakılır.

### 26.2 `kaynak_turu` artık boş olabiliyor — 337.450 kayıttaki uydurma silindi

§25'in "karar bekliyor" kalemi. Alan `default="ajans"` ile açılmıştı ve
arşivden gelen **hiçbir** kayıtta kaynak türü yoktu; hepsi bu varsayılanla
yazılmıştı. `meta_yazar` backfill'i `haber_merkezi` ve `bulten` değerlerini
ölçmüş ama bu kayıtlar için doğru bir kaynak türü olmadığından alana
dokunmamıştı — sonuç: veritabanı 337.450 haber için "ajanstan geldi" diyordu.

`0008_kaynak_turu_bos_olabilir` alanı `blank=True, default=""` yaptı ve
**ölçüte** göre boşalttı: kaynak türü ile meta yazar birbirini tutmuyorsa o
kaynak türü hiç ölçülmemiştir. `meta_yazar_elle=True` olan kayda dokunulmadı.

| `kaynak_turu` | Önce | Sonra |
|---|---|---|
| `ajans` | 346.304 | **8.854** |
| `dis_yayin` | 10.412 | 10.412 |
| `muhabir` | 123 | 123 |
| *(boş)* | 0 | **337.450** |

Migration 39,1 sn, `ANALYZE` 0,4 sn.

**§25'in önerdiği çözüm eksikti.** Plan "`meta_yazari_turet()` zaten boş türde
`haber_merkezi` döndürüyor, türetim kendiliğinden doğru sonucu verir" diyordu.
336.547 `haber_merkezi` kaydı için doğru, **545 `bulten` kaydı için değil** —
o kayıtlar panelden kaydedilince `haber_merkezi`ye dönerdi. Türetim
düzeltildi: kaynak türü boşsa **ölçülmüş `meta_yazar` korunur**, o da boşsa
ev varsayılanı `haber_merkezi` yazılır. Üç yeni test bunu tutuyor.

Panel formunda kaynak türünün boş seçeneği "Belirtilmemiş" diye adlandırıldı;
Django'nun `---------` yer tutucusu bu ayrımı anlatmıyordu.

### 26.3 Kampanya ↔ yuva bağı çoka çok oldu

Panel tablolarını doldururken çıktı: dökümdeki 25 kampanyanın **8'i birden
çok yuvada** yayımlanıyor ("-Manşet yanı- 300x250 / -Manşet altı1- 300x250 /
-Haber arası2- 300x250"). Model tek yuvalı `ForeignKey` ile kurulmuştu.
Kampanyayı yuva başına bölmek 131 kampanyalık gerçeği bozardı.

`0009_kampanya_coka_cok_yuva` bağı `ManyToManyField`e çevirdi. Ara tablo
**elle yazıldı** (`KampanyaYuva`) çünkü Django'nun ürettiği tablo eski
bağdaki `on_delete=PROTECT` korumasını sessizce düşürüyordu: kullanımdaki bir
yuva silinince kampanya yuvasız kalırdı ve yuva adları anasayfa şablonlarında
geçiyor (F1 ölçütü 3). Gerileme testi zaten vardı ve değişikliği yakaladı.

### 26.4 `panel_veri_al` — dokuz tablonun beşi dolduruldu

Yeni komut, panel dökümünü **tablo başlığı imzasından** tanıyıp okuyor; dosya
adına bakmıyor, çünkü sayfa numaraları dökümü alan kişinin gezinme sırasından
geliyor.

| tablo | alınan | dökümde | durum |
|---|---|---|---|
| `Gazete` | 17 | 17 | tam |
| `ResmiIlan` | 24 | 24 | tam |
| `ReklamYuvasi` | 50 | 50 | tam |
| `ReklamKampanyasi` | 25 | **131** | eksik — döküm 1. sayfa |
| `Bildirim` | 25 | **2.208** | eksik — döküm 1. sayfa |

**Eksiklik bu turda ölçüldü.** "17 gazete · 24 resmî ilan · 32 bildirim ·
50 reklam yuvası" notu bildirim tarafında yanlıştı: DataTables'ın kendi bilgi
satırı (`1 - 25 / 2.208`) dökümün listenin yalnız ilk sayfası olduğunu
söylüyor. Komut bu toplamı her koşuda basıyor ve eksikse işaretliyor;
"tablo dolduruldu" denmiyor.

**Üç ölçüm kararı:**

1. **Durum kodları dökümün kendi JS'inden okundu**, renginden değil.
   `row[8] == 1|2|4` → Aktif · Pasif · Arşiv; Django modelindeki değerlerle
   birebir aynı. Düğme ipucu kaydın **şu anki durumunu** yazıyor — ama arşiv
   düğmesi **eylemi** yazıyor ("Arşivden çıkar" = kayıt arşivde). İkisi
   karıştırılsa 23 ilan yanlış duruma giderdi.
2. **Kısalmış yuva listesi ipucundan tamamlandı.** Hücrede
   "… / -..." görünen liste `data-bs-title` niteliğinde tam duruyor; ekrandaki
   metni okumak 8 kampanyada yuva kaybettirirdi.
3. **Editör adı kullanıcıya bağlanmadı.** Dökümde ad var ("Coşkun SAİTOĞLU")
   ama gerçek kullanıcı tablosu henüz göçmedi (F5(d) `usertype_list`
   dökümünü bekliyor). `olusturan` boş bırakıldı, ada bakıp kullanıcı
   uydurulmadı.

**Yuvaların ayrıştırılamayan alanları boş bırakıldı, sayıldı:** 50 yuvanın
21'inde konum · 38'inde ölçü · 7'sinde cihaz adı geçiyor; 6'sı yuva değil boş
yuvanın görünen hâli ("Bu alana reklam verebilirsiniz…") ve öyle işaretlendi.

**Alınmayan dört tablo ve nedeni:** `Yorum` ve `LogKaydi` okur yorumu ve IP
adresi taşıyor — kişisel veriyi demo doldurmak için taşımak ayrı bir karar,
sorulmadan yapılmadı. `IkiAdimli` gizli anahtar kararını bekliyor (§24.10).
`SonDakika`nın dökümde liste sayfası yok, yalnız ekleme formu var.

Komut **tekrar çalıştırılabilir** (`update_or_create`), `--kuru` ile yalnız
sayar. 15 gerileme testi ayıklama kurallarını tutuyor; testler gerçek dökümü
değil, dökümün ölçülmüş biçimini taklit eden küçük sayfaları kuruyor — döküm
depoda değil.

### 26.5 Göç tazelemesi ve `meta_yazar` ikinci turu

`goc_al --yalniz-yeni` **129.828 kayıt** aldı; veritabanı **486.667 habere**
çıktı (356.839 → +%36,4). Görselsiz gelen 325 · ilçesi türetilen 12.384 ·
kaynak bağı kurulan 93.806 · yeni kaynak kaydı 163.

`meta_yazar_doldur` komutuna **`--yalniz-yeni`** eklendi: `meta_yazar`ı zaten
dolu olan kaydın arşiv dosyasını hiç okumuyor. Tazeleme koşusu böylece
356.481 dosyayı atladı ve **58 dakikadan 11,8 dakikaya** indi (okuma 694 sn,
yazma 9 sn, `ANALYZE` 3,5 sn).

| meta_yazar | 28 Ağu | 29 Ağu | fark |
|---|---|---|---|
| `haber_merkezi` | 336.547 | **369.054** | +32.507 |
| `haber_ajansi` | 8.854 | **76.422** | +67.568 |
| `alinti` | 10.412 | **35.045** | +24.633 |
| `bulten` | 545 | **2.120** | +1.575 |
| `fikir_iscisi` | 123 | **1.728** | +1.605 |
| *(boş — kaynak alanı çöp)* | 358 | **2.298** | +1.940 |

**Yeni kayıtlar bambaşka dağılıyor.** Eski partide ajans payı %2,5 iken yeni
129.828 kayıtta **%52** (İHA 36.500 · AA 22.619 · DHA 8.297). Beklenen bir
sonuç: yeni gelen kayıtlar son yılların içeriği ve kaynak alanı o dönemde
gerçekten doldurulmuş. Aynı sebeple "kendi muhabirimiz" 123'ten 1.728'e
çıktı (İsmail Karaduman 818 · Coşkun Saitoğlu 342 · Erhan Bedir 258).

**Alan sözleşmesi 486.667 kaydın tamamında tutarlı:** `ajans` görünen her
kaydın meta yazarı `haber_ajansi`, `dis_yayin` görünenin `alinti`,
`muhabir` görünenin `fikir_iscisi`. Kaynak türü boş olan 373.472 kayıtta
ölçülmüş meta yazar duruyor ve türetim onu ezmiyor.

### 26.6 Ölçülen sonuç

* **505 test geçiyor** (önceki tur 489; 16 yeni test bu turda eklendi).
* Beş panel ekranı gerçek veriyle çiziliyor: `/panel/yuvalar` ·
  `/panel/kampanyalar` · `/panel/gazeteler` · `/panel/ilanlar` ·
  `/panel/bildirimler` — hepsi 200.
* Yüklenen verinin dağılımı dökümle birebir: ilan 23 arşiv + 1 pasif,
  14 İHALE + 10 TEBLİGAT; kampanya 11 aktif + 14 pasif, 8'i çok yuvalı,
  toplam 36 kampanya-yuva bağı; gazete 17/17 aktif.

---

## 27. 29 Ağustos — tarama 13 kat hızlandı: bağlantı yeniden kullanımı

§26.1'de "kaynak site hasta" diye yazdığım şey yanlış teşhisti. Ölçünce
sunucunun kusursuz çalıştığı, sorunun **bizim tarafımızda** olduğu çıktı.

### Teşhis — zaman nerede geçiyordu

Tek bir haber sayfası, aynı adres, sekiz kez, aşamalara bölünerek:

| tcp connect | tls | TTFB | indirme | toplam |
|---|---|---|---|---|
| 15,08 | 0,06 | 0,22 | 0,005 | 15,36 |
| 0,06 | 0,05 | 0,22 | 0,004 | 0,33 |
| 3,07 | 0,04 | 0,22 | 0,006 | 3,34 |
| 7,07 | 0,04 | 0,22 | 0,000 | 7,33 |
| **42,12** | 0,06 | 0,21 | 0,011 | **42,40** |

**TTFB her ölçümde 0,21-0,23 sn.** Gövde 31,7 KB ve 5 milisaniyede iniyor.
Sunucu hızlı; zamanın tamamı **TCP `connect`** aşamasında geçiyor ve süreler
**1 / 3 / 7 / 15 / 42 sn** diye ilerliyor — bu çekirdeğin SYN yeniden gönderim
geri çekilmesi, yani **bağlantı kurulum paketleri düşürülüyor**.

Site **Cloudflare arkasında** (yanıt başlığından okundu). Betik `urllib` ile
her istekte yeni bir TCP+TLS bağlantısı açıyordu; kayıt başına ~2,6 istek
(yönlendirme + sayfa + ortalama 1,6 görsel) demek, saatlerce süren bir koşuda
milyonlarca bağlantı kurulumu. Bağlantı hızı sınırına takılan buydu.

Kontrollü karşılaştırma, aynı sayfa altı kez:

```
A) her istekte yeni bağlantı : 78,85 sn  (13,14 sn/istek)  3,3 · 0,3 · 28,3 · 42,4 · 3,3 · 1,3
B) tek bağlantı, keep-alive  :  8,05 sn  ( 1,34 sn/istek)  7,3 · 0,17 · 0,15 · 0,15 · 0,13 · 0,14
```

B'nin ilk isteği bağlantıyı kurma bedelini ödüyor; sonraki beşi **0,15 sn**.

### Çözüm — bağımlılık eklemeden

Her iş parçacığı konak başına **bir bağlantıyı açık tutup tekrar kullanıyor**.
`requests` kullanılmadı: betik `paketle.ps1` ile başka makineye taşınabiliyor
ve yalnız standart kütüphaneye dayanması şart. `http.client` ile yazıldı.

Dikkat edilenler:

* **Her yanıtın gövdesi sonuna kadar okunuyor** — okunmazsa bağlantı tekrar
  kullanılamaz, sessizce eski davranışa düşerdik.
* **Yönlendirmeler elle izleniyor** (`urllib` bunu kendi yapıyordu). Sitemap
  adreslerinin bir kısmı eski kategori slug'ına işaret ediyor ve 301 dönüyor.
* **2xx dışı yanıt `urllib.error.HTTPError` olarak fırlatılıyor**, böylece
  `sayfa_indir` içindeki 403/429 geri çekilme mantığı olduğu gibi çalışıyor.
* **Bayat bağlantı bir kez yeniden deneniyor**: karşı taraf boştaki bağlantıyı
  sessizce kapatabilir.
* Eşzamanlılık 10'da bırakıldı; artık `BH_ESZAMANLILIK` ile ayarlanabiliyor.
  Artırılmadı — darboğaz bağlantı kurulumuydu, iş parçacığı sayısı değil.

### Ölçülen sonuç

**Çıktı birebir aynı.** Arşivde zaten var olan 12 kayıt yeni yolla yeniden
çekildi ve üretilen JSON **12/12 aynı** çıktı (`yerel_gorseller` dışında —
o alan kök yolunu taşıyor).

Üretimdeki hız, dakika dakika:

| | eski kod (13:01-13:21) | yeni kod (13:24-13:29) |
|---|---|---|
| çekim hızı | 0,32 - 0,83 kayıt/sn | **6,4 - 11,7 kayıt/sn** |
| ortalama | ~0,7 | **8,84** |
| başarısız oranı | 11/50 (%22, HTTP 502) | 27/3.182 (**%0,85**) |

**13 kat.** 502'lerin de kaybolması teşhisi doğruluyor: Cloudflare bağlantı
baskısı altında origin'e ulaşamayınca 502 döndürüyordu, sunucu çökmüş değildi.

Kalan ~66 bin kayıt bu hızda **~2 saat**; eski hızla 55 saat sürecekti.

### 502 geri çekilmeye alındı

Hız düzeldikten sonra ikinci bir ölçüm daha yapıldı: dakikada 550-700 kayıt
çekilirken hata oranı **%0**, ama 13:30'da **bir dakika** süren bir origin
kesintisi 479 kaydı birden düşürdü (%80) ve sonraki dakikada oran yine %0'a
döndü. 502 kalıcı bir red değil, geçici dalgalanma; anında başarısız saymak o
kayıtları ikinci bir koşuya bırakıyordu. `GECICI_KODLAR`a 502/503/504 eklendi
(403/429 zaten vardı). Geri çekilme sırasında iş parçacıkları beklediği için
kesinti anında sunucuya binen yük de azalıyor.

Düzeltmeden sonraki yedi dakika: **8,10 kayıt/sn ortalama, sıfır hata**
(338 · 613 · 650 · 550 · 550 · 550 kayıt/dk). Arşiv %89,5'e çıktı.

### Yanlış teşhisin kaydı

§26.1'de "kaynak site bugün hasta, okur da aynısını yaşıyor" yazmıştım.
Dayanağım canlı anasayfanın 7,4 / 42,5 / 0,39 sn'lik yanıt süreleriydi —
ama o ölçüm de **bizim** bağlantı kurulumumuzu ölçüyordu, sunucunun yanıt
süresini değil. Aşamalara bölmeden yapılan süre ölçümü hangi katmanın yavaş
olduğunu söylemez. Sunucunun okurlara yavaş olduğuna dair bir kanıt yok.
