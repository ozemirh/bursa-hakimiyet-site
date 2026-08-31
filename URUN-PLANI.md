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
| 15 | **Bursaspor alanı** | Solda **dar**: **4 lig** puan durumu (Süper · 1. · 2. · 3.) + o haftaki Bursaspor maç skoru. Sağda **geniş**: Bursaspor haberleri. **29 Ağustos 2026:** geniş sütun karma dizgi — **6 görselli kart + 9 tarihli başlık** (§32.1). Yerleşim (solda dar / sağda geniş) değişmedi; değişen geniş sütunun içeriği: tam kadro tablo sol sütunu 958 px'e çıkardığı için altı kart sağ altta 412 px boşluk bırakıyordu. |
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

## Sağ ray hizalandı — 29 Ağustos 2026

Sayfanın dikey ek yeri manşetin altında **20 px kayıyordu**. Sebep iki
kuralın ayrı düşmesi: `.manset-alani` sağ rayı **340 px**, hemen altındaki
`.ana-izgara` **320 px** tanımlıyordu. Sol sütun 742'den 762'ye atlıyor, göz
kaymayı yakalıyordu.

| | Sol sütun biter | Sağ ray başlar | Ray genişliği |
|---|---|---|---|
| Manşet satırı (önce) | x=985 | x=1003 | 340 px |
| Son haberler satırı | x=1005 | x=1023 | 320 px |
| **İkisi de (sonra)** | **x=1005** | **x=1023** | **320 px** |

Aykırı olan manşetti: haber detayın `.izgara`sı da 320 px kullanıyor, yani
**320 sitenin ray ölçüsü**. 1140 px altında iki kural da 300'e indiği için
kaçık yalnız geniş ekranda görünüyordu.

Değişmez `icerik/tests_yerlesim.py` içinde kilitli: iki ızgara aynı rayı
kullanmalı, ray sitenin geri kalanıyla aynı olmalı ve kırılma noktasında
**birlikte** daralmalı — biri daralıp öteki kalırsa dikiş yine kayar.

## Puan tablosu genişletildi — 29 Ağustos 2026

Kullanıcı isteği: "puan durumu tablosunu biraz daha genişlet." Genişlik göz
kararıyla değil **ölçümle** seçildi; ölçüt takım adlarının alt satıra sarması.

| Sol sütun | Sarmalayan takım adı | Sol yükseklik | Haber kartı |
|---|---|---|---|
| 300 px (önce) | **9** | 1004 px | 244 px |
| 340 px | 3 | 917 px | 231 px |
| **380 px (seçilen)** | **0** | 865 px | 217 px |
| 420 px | 0 | 861 px | 204 px |
| 460 · 500 px | 0 | 861 px | 191 · 177 px |

**380 seçildi: sarmanın sıfırlandığı ilk genişlik.** Ötesi bir işe yaramıyor —
sol sütun 861 px'te dibe vuruyor, fazladan genişlik yalnız sağdaki haber
kartlarını daraltır.

**Denge yeniden kuruldu.** Tablo kısalınca (1004 → 865 px) bu kez sağ sütun
100 px uzun kaldı; §32'nin başlık listesi 9'dan **7**'ye indi (satır 41 px,
iki satır = 82 px). Ölçüm: 1280 ve 1600 px'te fark **−18 px**, 1024'te −57 px,
yatay taşma beş genişlikte de 0. Toplam kayıt 6 + 7 = 13.

Dar ekranda (≤1000 px) bölüm zaten tek sütuna iniyor; 360 px'te takım adları
yine sarıyor, orada sarmayı önleyecek genişlik yok.

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
- **Izgara da tek sütuna iner.** İlk sürümde inmiyordu ve düğme sayfayı
  bozuyordu: 1480 px üstünde `.sayfa` üç sütun (160 · 1100 · 160), yan
  raylar `display:none` olunca ızgara yerleşiminden düşüyor ve orta sütun
  **birinci sütuna — 160 px'lik raya** geçiyordu. Sayfa 160 px'e sıkışıyordu.
  Ders: bir ızgara çocuğunu gizlerken **sütun sayısı da azalmalı**. Ölçümle
  doğrulandı — orta sütun beş genişlikte de açıkken ve kapalıyken 1100 px.
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

---

## 28. 29 Ağustos — panel liste ekranları: sayım maliyeti kaldırıldı

§24'te panelin ağır ekranları düzeltilmişti; o turdan sonra veritabanı
356.839'dan **486.667 habere** çıktı ve maliyet süzgeçli listelere kaydı.
Bütün panel ekranları gerçek veriyle, süre + sorgu sayısı + en pahalı sorgu
olarak ölçüldü.

### Ölçülen dört sorun

**1. Aynı `COUNT(*)` her liste ekranında iki kez koşuyordu.** `Paginator`
sayfa sayısı için zaten sayıyor; toplu işlem şeridinin "süzgeçteki N kayıt"
satırı ve log ekranının üst bilgisi aynı sorguyu ikinci kez açıyordu. Bu
sorgular birbirinin kopyasıydı, farklı sayımlar değil.

**2. Sayımın üst sınırı yoktu.** Akış araması `LIKE '%…%'` ile yapılıyor;
baştaki joker hiçbir B-ağacı indeksinin kullanılamayacağı anlamına geliyor ve
486.667 satır taranıyordu. Ayrıştırınca ekranın **bütün** maliyetinin
kimsenin bakmadığı bir toplamı tam saymaktan geldiği çıktı:

| | süre |
|---|---|
| tam sayım (78.959 kayıt) | 1.176 ms |
| 5.001'de kesik sayım | 104 ms |
| sayfanın kendi sorgusu (`LIMIT 25`) | 0 ms |

**3. İki tamsayı süzgeci indeks kullanamıyordu.** Django'nun otomatik tek
sütunlu yabancı anahtar indeksleri yetmiyordu, çünkü sorgu ikinci bir koşul
taşıyor (`durum != Silinmiş`) ve satırlar tabloya gidilerek okunuyordu:
kategori **501 ms**, editör **1.014 ms — indeksi hiç kullanmadan tam tarama**.
Editör alanı arşivden gelen kayıtların tamamında boş olduğu için `ANALYZE`
istatistikleri "bu sütunun tek değeri var" diyor ve planlayıcı indeksi seçici
bulmuyordu; projenin üçüncü tuzağının aynısı.

**4. Kaynak listesi `LIMIT`ten faydalanamıyordu.** `annotate(Count("haberler"))`
ara tabloya JOIN atıp GROUP BY kuruyor, `ORDER BY ad` yüzünden 400 kaynağın
tamamı 112.906 bağ satırı üzerinden gruplanıyordu: **109 ms**.

### Yapılanlar

* Süzgeçli sayı tek kaynaktan geliyor: `_liste_ciz` sayfalayıcının saydığı
  değeri şeride ve üst bilgiye veriyor.
* **`SinirliSayfalayici`** sayımı `SAYIM_SINIRI + 1`de kesiyor. Sınır
  `TOPLU_UST_SINIR` ile **aynı sayı** (5.000): onu aşan küme zaten toplu
  işlenemiyor, yani tam sayısını bilmenin panelde bir karşılığı yok. İkisi tek
  sabite bağlandı; ayrışsalardı şerit "tamamını seç" der, sunucu reddederdi.
* Sınır aşıldığında ekran **"5.000+"** yazıyor ve şerit "tamamını seç"
  kutusunu çizmiyor, yerine "süzgeci daraltın" diyor. Kesik bir sayıyı kesin
  gibi göstermek ya da seçilemeyecek bir kutu çizmek — ikincisi §12'nin
  düzelttiği hatanın ta kendisi olurdu.
* İki kapsayan indeks eklendi (`0010`): `(kategori, durum)` ve
  `(olusturan, durum)`. Ölçülen bedel 4,9 MB.
* Kaynak listesindeki sayım **alt sorguya** çevrildi; sıralama `ad` indeksine
  kalıyor, sayım yalnız ekrana çıkan 25 satır için yapılıyor.
* Kampanya ekranının "süresi geçti" sayımı Python döngüsünden veritabanına
  alındı.

### Sonuç

| ekran | önce | sonra |
|---|---|---|
| `/panel/akis?q=bursa` | **3.703 ms** | **74 ms** |
| `/panel/akis?kategori=1` | 1.039 ms | **31 ms** |
| `/panel/kaynaklar` | 283 ms | **53 ms** |
| `/panel/akis?sayfa=500` | 282 ms | **45 ms** |
| `/panel/akis` | 251 ms | **38 ms** |
| `/panel/videolar` | 109 ms | **52 ms** |

**21 panel ekranının tamamı 60 ms'nin altında.** Her ekran bir sorgu daha az
çalıştırıyor. **533 test geçiyor**; 15'i bu turda eklendi.

### Yapılmayan ve nedeni

**`spot` alanına arama indeksi kurulmadı.** Kapsayan bir indeks
(`durum, baslik, spot`) aramayı 1.157 → 270 ms'ye indiriyor, ölçüldü — ama
**147,5 MB** yer kaplıyor ve daha önemlisi PostgreSQL göçüne mayın döşüyor:
`spot` en uzun 5.794 karakter, PostgreSQL'in btree indeksi ise 2.704 baytta
reddediyor (18 kayıt bu sınırın üstünde). Sınırlı sayım aynı ekranı 147 MB'sız
ve göçü bozmadan 74 ms'ye indirdi.

`LIKE '%…%'` için doğru altyapı çözümü PostgreSQL'in **`pg_trgm` GIN**
indeksidir ve F7'nin işidir. FTS5 bunun yerine geçmez: tam metin arama
sözcük/önek eşler, ortadan eşleşme yapmaz.

## 29. 29 Ağustos — BURSASPOR bölümü: yeşil-beyaz, tam tablo, haftanın maçı

Bölüm üç yerinden eksikti: tablo **beş satıra kırpılıyordu**, grup
**körlemesine** ilk gruptu, haftanın maçı **hiç** çizilmiyordu. Üçü de
kapandı; veri zaten tamdı (`canli-veri/veri/puan-durumu.json`, 127 takım),
eksik olan gösterimdi.

### Kararlar

| Konu | Karar | Nerede |
|---|---|---|
| **Renk** | Bölüm **yeşil-beyaz** — kulüp kimliği. Sitenin geri kalanı lacivert-kırmızı kalır. Dört yeni simge `:root` içinde: `--yesil` `--yesil-koyu` `--yesil-ak` `--yesil-cizgi`; kurallar `#bursaspor` ve yalnız bu bölümde geçen sınıflarla sınırlı | `site.css` §15 |
| **Açık sekme** | Listenin ilki (Süper Lig) **değil**, Bursaspor'un ligi. Lig koda gömülü değil, veri `takip.lig` alanından gelir (şu an `1lig`) | `canli.puan_ligleri` |
| **Grup seçimi** | Körlemesine `gruplar.0` **değil**: Bursaspor'un grubu, yoksa **en çok Bursa kulübü** barındıran grup öne gelir; diğer gruplar düşmez, okur sekmeyle geçer. §8'in önerdiği sonucu ölçerek veriyor: 2. Lig **Kırmızı**, 3. Lig **2. Grup** | `canli.puan_ligleri` |
| **Tablo** | Kırpma kalktı, **grubun tamamı** basılır (18-20 satır) ve sütunlar **tam**: O G B M A Y Av P | `anasayfa.html` |
| **Bursa satırları** | Bursaspor satırı dolu yeşil/beyaz yazı; diğer Bursa kulüpleri (İnegöl Kafkas, Karacabey, Sultan Su İnegölspor, Bursa Nilüfer, Bursa Yıldırım) açık yeşil zeminli. Tanıma sözcük **başı** eşleşmesi: "SULTAN SU İNEGÖLSPOR" yakalanır, "YENİ MALATYASPOR" YENİŞEHİR'e takılmaz | `canli._bursa_kulubu` |
| **Haftanın maçı** | Tablonun **üstünde** — tablolar tam kadro olduğundan altta kalsa görünmezdi. Maç oynandıysa **skor**, oynanmadıysa **tarih + saat** basılır; kaynakta olmayan sonuç uydurulmaz (`skor_var` yalnız `oynandi` **ve** iki gol alanı doluysa true) | `canli.puan_takibi` |
| **Menü çapası** | Menüdeki "Puan durumu" bağlantısı `#puan-super` idi; Süper Lig paneli artık varsayılan olarak kapalı (`display:none`) ve çapa hiçbir yere gitmiyordu → `#bursaspor` | `parca/kategori_bandi.html` |

### Sekme kümelerinin ayrılması

`site.js` sekmeleri `.sek` öğesinin **ana** öğesinde arıyor. Grup sekmeleri
lig panellerinin içine girdiği için lig sekmeleri onları da toplayıp iki küme
birbirine karışacaktı. Çözüm JS'i değiştirmek değil, her kümeye kendi
sarmalayıcısını vermek oldu: `.lig-sek` ve `.grup-sek`. Ölçüldü: lig
sekmesinde ArrowRight'a basmak grup sekmelerinin seçimini **bozmuyor**.

### Ölçüm (başsız Chrome, `Network.setCacheDisabled`)

| genişlik | yatay taşma | puan kutusu | tablo kabı | satır × sütun |
|---|---|---|---|---|
| 360 | **0** | 299 px | 273 → 273 (kaymıyor) | 20 × 10 |
| 768 | **0** | 707 px | 681 → 681 | 20 × 10 |
| 1024 · 1280 · 1600 | **0** | 300 px | 274 → 274 | 20 × 10 |

Sekiz sayı sütunu 300 px'lik kutuya **kayma olmadan** sığdı (takım adına
143 px kalıyor); yine de tablo kendi `overflow-x:auto` kabında duruyor —
daha uzun takım adı geldiğinde sayfa değil tablo kayar. Kap klavyeyle
gezilebilsin diye odak alıyor. Tıklama ölçümü: 2. Lig sekmesi → Kırmızı 17
satır, Beyaz'a geçiş → 18 satır, her adımda taşma 0. Odak halkası duruyor
(`solid 3px` kırmızı).

**500 test geçiyor**; 11'i bu turda eklendi (`tests_canli.PuanDurumu`) ve üç
kararı da kilitliyor: açık sekme Bursaspor'un ligi, grup sırası Bursa'ya
göre, tablo kırpılmıyor.

### Açık kalan

Tablo tam kadro olunca sol sütun sağdaki haber şeridinden **uzun** kalıyor;
geniş ekranda sağ altta boşluk oluşuyor. Haber sayısını artırmak ya da şeridi
iki sütuna indirmek bunu kapatır — ikisi de §8 madde 15'in yerleşimini
(solda dar puan, sağda geniş haber) değiştirmediği için ayrı bir karar.

---

## 30. 29 Ağustos — RESMÎ İLANLAR bölümü: elle yazılmış liste veriye bağlandı

Kullanıcı isteği: bölüm yeniden düzenlensin ve **daha ilgi çekici** olsun.
Resmî ilan BİK yükümlülüğü olan editoryal bir bölüm ve gazete için gelir
kalemi; ciddiyeti bozmadan okunur olması gerekiyordu.

### Asıl kusur ilgi çekicilik değildi: bölüm sahteydi

Şablondaki altı `<li>` **elle yazılmıştı**. Başlıklar gerçekti (biri
veritabanına bakıp kopyalamış) ama şablona çakılıydı: kayıt değişse sayfa
değişmeyecekti. Veritabanında zaten **24 gerçek `ResmiIlan` kaydı** vardı.
Bölüm artık `ResmiIlan.yayimlananlar()` sorgusundan çiziliyor.

### Süzgeç neden `durum=AKTİF` değil, "pasif değil"

Ölçüldü: 24 kaydın **hiçbiri AKTİF değil** — 23'ü Arşiv, 1'i Pasif.
`durum=AKTİF` süzgeci bölümü **tamamen boşaltırdı**.

Durum kodunun anlamı dökümün kendi JS'inden doğrulandı
(`__bursahakimiyet.com.tr__15.html`, 831-849. satır): `row[8]==1` →
tooltip "Aktif", `==2` → "Pasif", başka → "Arşivden çıkar". Yani tooltip
**durumu** söylüyor, eylemi değil; `panel_veri_al`ın eşlemesi doğru.
Aynı satırdaki arşiv düğmesi eylem yazıyor ("Arşivle" / "Arşivden çıkar")
olduğu için bu ayrım tek tek denetlendi.

Karar: **arşiv kalır, pasif çıkar.** Arşiv "yayımlandı, güncelliğini
yitirdi" demek — bölüm gazetenin yayımladığı ilanların dizini olduğu için
bu kayıtlar oraya aittir. Pasif ise editörün yayından çektiği kayıttır.
Kayıtlar aktifleşmeye başlayınca süzgeç yeniden değerlendirilmeli.

### Tasarım kararları ve gerekçeleri

1. **Tarih omurgası.** Düz listede sekiz başlık aynı ağırlıktaydı ve
   "bu ne kadar yeni" sorusu ancak en alttaki gri satır okunarak
   yanıtlanıyordu. Gün/ay bloğu (`.ilan-gun`) tarihi satırın soluna,
   ilk bakılan yere aldı. Notice/ilan sayfalarının klasik çözümü:
   okur türden önce **tarihe** bakar.
2. **Lejant → süzgeç.** Alttaki "İLAN TÜRLERİ" şeridi renk kodunu tanıtan
   ölü bir bilgiydi. Aynı şerit listenin üstüne alındı ve tıklanabilir
   oldu (`aria-pressed`, `role="status"` canlı bölge). Dört tür de
   duruyor (§16), kaydı olmayanlar **kesikli çerçeve + gerçek 0** ile;
   "bu gazete bu türde ilan yayımlamıyor" da bilgidir.
3. **Kaydı olan türler önce.** Yasal sıra (İCRA ilk) süzgeci boş bir
   düğmeyle açıyordu; `tur_dagilimi` sıfırları sona indiriyor.
4. **Ölü bağlantılar kaldırıldı.** Başlıklar `href="#"` idi. İlan
   metinleri göç etmedi, detay sayfası **yok**; başlık artık bağlantı
   değil, düz metin. Satır vurgusu (`li:hover`) da kaldırıldı — tıklanamayan
   satırı boyamak "buraya tıkla" sözü veriyordu. "TÜM İLANLAR" gerçek
   `/resmi-ilan` adresine bağlandı.
5. **Son başvuru vurgusu YAPILMADI.** İstenmişti ama `bitis_tarihi`
   24 kaydın **hepsinde boş**. Uydurulmadı; bölümün notu bunu okura
   açıkça söylüyor.

### Yan bulgu — `|lower` Türkçe İ harfini bozuyor

Nottaki tür adları `{{ t.ad|lower }}` ile küçültülünce tarayıcıda
**"i̇hale"** basıyordu: Unicode "İ"yi `i` + birleşen nokta (U+0307)
olarak küçültüyor. `site_etiket`te `buyult` vardı ama karşılığı yoktu;
`kucult` süzgeci eklendi.

### Ölçüm (başsız Chrome, `Network.setCacheDisabled`)

| genişlik | `clientWidth` / `scrollWidth` | sütun | bölümde taşan |
|---|---|---|---|
| 360 | 345 / 345 | 1 | 0 |
| 768 | 753 / 753 | 1 | 0 |
| 1024 | 1009 / 1009 | 2 | 0 |
| 1280 | 1265 / 1265 | 2 | 0 |
| 1600 | 1585 / 1585 | 2 | 0 |

Sayfadaki diğer taşan öğelerin tamamı `DIV.akis` (son dakika şeridi)
içinde ve **tasarımı gereği** yatay kayan kapta; sayfa yatay kaymıyor.
Sağ ray beş genişlikte de 320 px.

Kontrast (en düşükler): gün/ay etiketi 5,17 · ilan no 5,50 · kapalı süzgeç
düğmesi 5,17 · TEBLİGAT rozeti 6,62 · basılı TÜMÜ düğmesi 17,82. Hepsi
AA eşiğinin (4,5) üstünde.

Odak **gerçek Tab tuşuyla** ölçüldü (`Input.dispatchKeyEvent`):
`3px solid var(--kirmizi)`, 2 px aralık, `:focus-visible` eşleşiyor.
Kaydı olmayan iki tür `disabled` olduğu için sekme sırasında atlanıyor.
Not: `element.focus()` ile ölçüm `outline-style:none` veriyordu —
programatik odak `:focus-visible`ı tetiklemiyor, ölçüm yanıltıcıydı.

Süzgeç davranışı ölçüldü: TEBLİGAT → 2 satır kalıyor, ikisi de tebligat,
`aria-pressed` doğru, canlı bölge "Sayfadaki 2 tebligat ilanı gösteriliyor."
TÜMÜ → 8 satır geri geliyor ve not varsayılana dönüyor.

**Ekran görüntüsü açılıp bakıldı** (360 · 1280 · süzülmüş hâl). İlk kırpma
denemesi altbilgiyi yakalamıştı: `captureBeyondViewport` sayfa koordinatlarını
kaydırıyor. Bölüm görünüre kaydırılıp yeniden çekildi.

### Açık kalan

- `/resmi-ilan` sayfası hâlâ yer tutucu (`bekleyen.html`). Anasayfa artık
  gerçek kayıt gösterdiği için bu sayfanın 23 kaydı listelemesi sıradaki
  iş; kapsam dışı bırakıldı.
- İlan **metni**, BİK kodu ve bitiş tarihi dökümde yok (§24.3): ekleme
  formu kaydedilmemiş. Bu alanlar gelmeden ilan detay sayfası yapılamaz.
- Anasayfa 8 ilan gösteriyor; süzgeç sayıları **sayfadakini** sayar,
  arşiv toplamı (23) bölümün notunda ayrıca yazılı.

---

## 31. 29 Ağustos — vizyon takvimi kaynağa bağlandı: dağıtımcı duyuruları

§20'de "TMDB anahtarı alınacak" diye kapatılan konu **yeniden açıldı ve
başka türlü kapandı**. Bileşen 26 Ağustos'tan beri Wikidata'dan gelen
**1 filmle** duruyordu; artık gerçek veriyle doluyor.

### Önce eleme: bütün portallarda aynı madde var

Türkiye vizyon takvimi yayımlayan siteler tek tek okundu. `robots.txt`
çoğunda temizdi; eleyen şey **sözleşme şartları** oldu ve hepsinde aynı
kalıp çıktı.

| Kaynak | robots.txt | Kullanım koşulları — birebir |
|---|---|---|
| `sinemalar.com` | temiz (`ClaudeBot` yalnız `Crawl-delay: 60`) | *"Kişisel kullanım dışında, reklam veya **ticari amaçlı** olarak herhangi bir NOKTACOM'a ait İçeriği, NOKTACOM yazılı onayı olmaksızın kullanma, çoğaltma, modifiye etme, dağıtma, depolama/saklama yasaktır."* |
| `beyazperde.com` | temiz | md. 3.12 *"…bu malzemeler ve dokümanlar üye ve **başka kişi ile kuruluşlar** tarafından izinsiz kullanılamaz, iktisap edilemez ve değiştirilemez."* + md. 3.3 *"Otomatik programlar kullanılarak çok sayıda sorgu … yapılması … bu yasağa dahildir."* |
| `biletinial.com` | `ClaudeBot: Allow: /` | *"Kullanıcı sadece kişisel kullanım için kopya hakkına sahip olduğunu kabul eder ve Biletinial'ın **yazılı izni olmadan** … kopyalayamaz, çoğaltamaz, yayınlayamaz, satamaz…"* |
| `paribucineverse.com` | temiz | md. 2 *"…siteden herhangi bir şekilde izinsiz bir şekilde görsel veya yazılı bir parçasını veya bütününü kopyalamayacağını, çoğaltmayacağını, **başka sitelerde kullanmayacağını** kabul ve beyan eder."* |
| `uip.com.tr` | robots.txt yok | *"HERHANGİ BİR MATERYALİN YETKİ DIŞI KULLANIMI, KOPYALANMASI, ÇOĞALTILMASI, MODİFİKASYONU, YAYIMLANMASI … KESİNLİKLE YASAKTIR."* |
| `boxofficeturkiye.com` | temiz | madde 14 (§8'de yazılı) — **ama** `/kurumsal/icerik-izni` adresinde gerçek bir izin formu var |
| `tmefilm.com` | **`User-agent: ClaudeBot` → `Disallow: /`** | okunmadı; robots kapatıyor, siteye hiç gidilmedi |

Teknik gerekçeyle elenenler: **Cinemaximum** (alan adı ölü, marka Paribu
Cineverse'e geçmiş), **CJ ENM Türkiye** (alan adı ölü), **CGV Mars Dağıtım**
(web sitesi yok, yalnız YouTube kanalı), **Warner Bros. Türkiye** (global
siteye yönlendiriyor, TR takvimi yok), **Cinens** (repertuar/açık hava
gösterimleri, ulusal takvim değil), **Kültür ve Turizm Bakanlığı film
sınıflandırma portalı** (`robots.txt` `Allow: /` ve resmî kaynak, ama
tamamen istemci tarafı çiziliyor ve tuttuğu tarih **sınıflandırma** tarihi,
vizyon tarihi değil).

**TMDB de elendi** (§20'deki karar geri alındı): şartları reklam geliri olan
siteleri "commercial use" sayıyor ve ayrı yazılı anlaşma istiyor. Gazete
reklamlı ticari bir yayın. Kod duruyor, varsayılan olmaktan çıktı.

### Sonra çözüm: dağıtımcının kendi duyurusu

Portalın "içeriğimizi kopyalamayın" maddesiyle, **dağıtımcının "filmimiz
şu tarihte vizyonda" duyurusu aynı şey değil** — ikincisi zaten basının
yayınlaması için yapılan bir açıklamadır. §9'un son paragrafı bu yolu
işaret ediyordu; izlendi.

İki dağıtımcı hem teknik hem hukuki olarak temiz çıktı. İkisinde de
içeriğin kullanımını kısıtlayan bir kullanım koşulları sayfası **yok** —
site haritalarının tamamı tarandı (Başka Sinema **19** sayfa, Bir Film
**518** sayfa) — ve `robots.txt` bu yolları açık bırakıyor.

| Dağıtımcı | Adres | Ne veriyor | Ölçüm |
|---|---|---|---|
| **Başka Sinema** | `/gelecek-filmler/` + `/basin/` | Türkçe ad, orijinal ad, yıllı tarih, tür | 30 film okundu, **3'ü** pencerede |
| **Bir Film** | `/sinemalarda` → film sayfası | ad, yıllı tarih, tür | 20 öğe okundu, **5'i** pencerede |

**Toplam ölçüm (29 Ağustos 2026, `--ay 3`): 8 film, 5 vizyon günü**,
çıkış kodu **0**, durum `taze`. Anasayfada bölüm 4 kartla doluyor.

Ölçülen bir tuhaflık: **Bir Film'in liste sayfası yıl vermiyor**
("13 Kasım'da Sinemalarda!"). Yıl yalnız film sayfasında yazılı. Bu yüzden
liste kaba bir **süzgeç** olarak kullanılır ve tarih film sayfasından
okunur; bir koşuda açılan film sayfası 25 ile sınırlı.

### Kapsam dürüstlüğü

Bu liste **ulusal vizyon takviminin tamamı değildir**; yalnız bu iki
dağıtımcının getirdiği filmleri kapsar. Bu, gizlenmesi değil söylenmesi
gereken bir sınır: çıktıya `kaynak.kapsam_uyarisi` alanı yazılır ve şablon
bunu okura basar. Anasayfadaki *"doğrulanmış bir kaynak henüz yok"* yer
tutucu notu kaldırıldı, yerine gerçek künye + kapsam uyarısı geldi.

Eksik film **uydurulmaz**. Kaynakta olmayan alan (özgün ad, özet, yaş
sınırı) boş kalır.

### Açık kalan iş kalemi

**Box Office Türkiye'ye izin başvurusu.** Kapsam farkı büyük (dağıtımcı +
orijinal ad + çoklu tür + cuma bazlı hafta, ayda ~30 film) ve site
`/kurumsal/icerik-izni` adresinde **gerçek bir izin süreci** sunuyor —
yani yasak mutlak değil, izne bağlı. Ayrıştırıcı zaten yazılı ve
doğrulanmış; izin gelirse `--yazili-izin-var` bayrağıyla tek adımda açılır.
Bu bir **e-posta işidir**, betiğin işi değildir; §2/§8/§12/§15'teki diğer
hukuki teyit kalemleriyle aynı listeye girer.

İkinci sırada **Paribu Cineverse**: verisi teknik olarak en temizi
(sayfada hazır JSON-LD, ölçüldü: 34 film / 8 cuma), ama dağıtımcı alanı yok
ve madde 2 açık. İzin alınırsa güçlü bir ikinci kaynak olur.

---

## 32. 29 Ağustos — denetim turu: Bursaspor boşluğu kapandı, resmî ilan beyanı düzeltildi

İki bölüm (§29 Bursaspor, §30 Resmî ilanlar) denetlendi: şablon + CSS + JS
okundu, beş genişlikte başsız Chrome ile ölçüldü, ekran görüntüleri açılıp
incelendi. §29'un **açık bıraktığı yerleşim kararı** burada verildi.

### 32.1 Bursaspor — 412 px'lik boşluk: karar ve gerekçe

Ölçülen kusur: tam kadro tablo sol sütunu **958 px**'e çıkarıyor, sağdaki
altı kart **546 px**'te bitiyordu. 1280 ve 1600 px'te sağ altta
**412 px × 760 px** boş alan kalıyordu (1024'te 391 px). Ekran görüntüsünde
bu boşluk "içerik yüklenmemiş" gibi okunuyordu.

Tartılan seçenekler:

| Seçenek | Neden seçilmedi |
|---|---|
| Kart sayısını 6 → 12 | Üç sıra 786 px'te kalıyor (hâlâ 170 px açık), dört sıra 1048 px ile **tabloyu aşıyor**. Asıl sorun ölçü değil: on iki eşit ağırlıklı kart bölümü **düz bir kart duvarına** çevirirdi, hiyerarşi tümden düzleşirdi. |
| Sütunları takas etmek (tablo sağa) | Boşluğu kapatmıyor, sola taşıyor. Ayrıca §1 madde 15 "solda dar puan" diyor — sözleşme değişikliği gerektirirdi, karşılığı yok. |
| Tabloyu iki sütuna bölmek (1-10 / 11-20) | ~600 px genişlik ister; "solda dar" sözleşmesini bozar ve sıra sürekliliği kopunca puan tablosu okunmaz olur. |
| Tabloyu kısaltmak | Kullanıcı tam kadro istedi; kapalı. |
| **Kart bloğu + başlık listesi (seçilen)** | — |

**Karar: sağ sütun karma dizgiye geçti** — üstte altı görselli kart
(değişmedi), altında `.bursaspor-liste`: tarihli, tek satırlık dokuz
başlık. Gerekçe biçimsel değil editoryal: kulüp sayfalarının klasik
çözümü üstte görselli seçki, altında yoğun başlık dizisidir; geri dönen
okur fotoğrafa değil **başlığa** bakar. Liste dikeyde ucuz olduğu için
sütun yüksekliği tablonun yüksekliğine göre ayarlanabiliyor — kart eklemek
bu esnekliği vermiyordu.

**§1 madde 15 DEĞİŞMEDİ**: yerleşim hâlâ "solda dar puan durumu, sağda
geniş Bursaspor haberleri". Değişen, geniş sütunun *içeriği*. Sözleşmeye
eklenen tek satır: geniş sütun **6 kart + 9 başlık** taşır
(`views.BURSASPOR = 6`, `BURSASPOR_LISTE = 9`; toplam 15 kayıt tek
sorgudan dilimlenir, kart ile liste **kesişmez**).

Ölçüm (başsız Chrome, `Network.setCacheDisabled`, sol sütun − sağ sütun):

| genişlik | önce | sonra | yatay taşma |
|---|---|---|---|
| 360 | (tek sütun) | (tek sütun) | **0** |
| 768 | (tek sütun) | (tek sütun) | **0** |
| 1024 | +391 px | **−24 px** | **0** |
| 1280 | +412 px | **+14 px** | **0** |
| 1600 | +412 px | **+14 px** | **0** |

Liste satırı 41 px (sonuncusu 29 px, alt dolgusu yok). Kontrast: başlık
bağlantısı 17,82 · tarih 5,50 · "SON GELİŞMELER" başlığı 10,28 — hepsi AA
üstünde. Yeni renk **tanımlanmadı**; §15'in yeşilleri kullanıldı.

### 32.2 Tarih sütunu yılı gizliyordu — `kisa_zaman` süzgeci

Liste tarihi öne aldığı için tarihin **doğru okunması** gerekiyordu.
Ölçüldü: Bursaspor kategorisindeki en yeni haber **31 Ekim 2025**
tarihli (arşiv taraması güncele yetişmedi; kategoride 2026 kaydı yok).
Yılsız "31 Eki" bunu *bu yılın* haberi gibi gösteriyordu — üstelik
hemen yanında 29 Ağustos 2026 tarihli maç dururken.

`kisa_zaman` süzgeci eklendi: **bugünse saat, bu yılsa gün+ay, başka
yılsa gün+ay+yıl.** Gazete masasının kuralı: aynı günün haberinde okur
"kaçta", eski haberde "ne zaman" diye sorar. Bölümün notu da tarihlerin
kaydın kendi tarihi olduğunu ve taramanın bugüne yetişmediğini söylüyor.

### 32.3 Dar ekranda tablo takip edilemiyordu

Sütunlar 1000 px altında üst üste binince puan kutusu tam genişliğe
çıkıyor ve 768 px'te takım adı ile sayı sütunları arasında **~400 px
boşluk** kalıyordu; okur satırı gözle takip edemiyordu (ekran
görüntüsünde görüldü). `@media(max-width:1000px)` içinde tabloya
`max-width:560px` kondu. Kutu geniş kalıyor, tablo ölçüsü sınırlanıyor.

### 32.4 Odak halkası ölçüldü: §29'un beyanı yanlıştı

§29 "odak halkası duruyor (`solid 3px` kırmızı)" diyor. **Gerçek Tab
tuşuyla ölçüldü**: `.puan-sar` ve `.panel` `tabindex` taşıyan DIV'ler ve
sitenin odak kuralı yalnız `a, button, input, select, summary` seçiyordu —
bu ikisi Chrome'un kendi `auto 1px rgb(16,16,16)` halkasını alıyordu.
Görünmez değil ama sitenin dili değil, ve beyan yanlıştı.

Kural genişletildi: `[tabindex]:focus-visible` eklendi. Yeniden ölçüm:
`.panel` ve `.puan-sar` artık `solid 3px rgb(228,34,43)`, 2 px aralık.
Aynı düzeltme sağ raydaki servis sekmesi panellerini de kapsıyor.

### 32.5 Resmî ilanlar — bölüm okura ne söylüyordu

Süzgeç, klavye ve canlı bölge **temiz**: gerçek Tab ile üç düğmeye de
ulaşılıyor (kaydı olmayan iki tür `disabled` olduğu için atlanıyor),
Enter ve Boşluk çalışıyor, `aria-pressed` doğru, `role="status"` +
`aria-live="polite"` duyurusu "Sayfadaki 2 tebligat ilanı gösteriliyor."
basıyor, pasif düğmeye tıklama yok sayılıyor, `.gizli` satırlar
`display:none` olduğu için erişilebilirlik ağacından da düşüyor.
Tarih omurgası ve tür rozetleri sitenin diliyle uyumlu; 360 px'te de
düzgün. Yatay taşma beş genişlikte **0**.

Üç kusur bulundu ve düzeltildi:

1. **Bölüm "açık ilan listesi" gibi okunuyordu.** 24 kaydın 23'ü arşiv,
   `bitis_tarihi` hepsinde boş, en yenisi 24 Ağustos — okur 29 Ağustos'ta
   bunları hâlâ açık ihale sanabilirdi. Nottaki "yayımlanabilir 23 ilan"
   ifadesi teknik bir sözcüktü, okura bir şey söylemiyordu.
   - Başlığa **dönem etiketi** kondu: *16 Ağustos – 24 Ağustos 2026*.
     İlan sayfalarının klasik çözümü; aralık ilk bakışta "bu bir dönem
     dizini" diyor.
   - Not yeniden yazıldı: *"Bu bölüm gazetenin **yayımladığı** resmî
     ilanların dizinidir, açık ilanların listesi değil"* ve *"bir ihalenin
     ya da tebligatın hâlâ geçerli olup olmadığı ilanı veren kurumdan
     doğrulanmalıdır."* Kaydın söylemediği şey **uydurulmadı**; kaydın
     söylemediği söylendi.
2. **Not şablona çakılı bir olgu taşıyordu.** *"İCRA ve PERSONEL ALIMI
   türünde yayımlanmış ilan yok"* cümlesi elle yazılmıştı — §30'un
   düzelttiği kusurun (elle yazılmış altı `<li>`) küçük bir kopyası.
   Kayıt gelse not yalan söyleyecekti. Boş türler artık `tur_dagilimi`
   çıktısından okunuyor; test İCRA kaydı ekleyip cümlenin daraldığını
   doğruluyor.
3. **Süzgeç sayılarının neyi saydığı yazılı değildi.** Şeritte "İHALE 6",
   notta "13 ihale" duruyordu. Varsayılan not artık *"Sayılar bu sayfadaki
   8 ilanı sayar"* diye başlıyor; arşiv toplamı bölümün alt notunda.
   Sayılar sayfayı saymaya devam ediyor — tıklayınca olan bu, sayı ile
   davranış ayrışmamalı.

Yan temizlik: varsayılan not metni `data-varsayilan` niteliğiyle **iki
yerde** duruyordu; betik artık metni sayfadan okuyor, nitelik kalktı.

### 32.6 Testler

**528 test geçiyor**; beşi bu turda eklendi (`icerik.tests.BolumDurustlugu`):
boş tür cümlesinin veriden geldiği, bölümün dönem etiketi ve "açık ilan
listesi değil" beyanını taşıdığı, tek tarihli kayıtta aralık yazılmadığı,
Bursaspor listesinin kartlarla kesişmediği ve `kisa_zaman`ın yılı
gizlemediği kilitlendi.

### 32.7 Açık kalan

- **Bursaspor arşivi bayat.** Kategorinin en yeni haberi 31 Ekim 2025;
  2026 kaydı yok. Tarih sütunu bunu artık görünür kılıyor ve not okura
  söylüyor, ama asıl çözüm taramanın ilerlemesi.
- **Arşivde birebir aynı başlıklı iki kayıt var** ("Bursaspor kupaya veda
  etti!", 16. ve 17. sırada). Şu anki 15 kayıtlık dilim onlara ulaşmıyor;
  dilim büyütülürse aynı başlık iki kez basılır. Tekilleştirme bir **veri**
  işi, gösterim işi değil.
- `/resmi-ilan` sayfası hâlâ yer tutucu (§30'dan devrediyor).
- İlan metni, BİK kodu ve bitiş tarihi dökümde yok (§24.3); bu alanlar
  gelmeden "son başvuru" vurgusu da ilan detay sayfası da yapılamaz.

---

## 29. 29 Ağustos — etiket alanı ve girdi renkleri

Kullanıcının bildirdiği iki kusur; ikisi de ölçülerek doğrulandı.

### 29.1 "Etiketler gözükmüyor" — alan boş bir açılır listeydi

Alan `ModelMultipleChoiceField` idi ve `Etiket.objects.all()` üzerinden çoklu
seçim sunuyordu. **Etiket tablosu boş: 0 satır.** Arşivde de etiket verisi
yok — 400 kayıtlık örneklemde `anahtar_kelimeler` alanı **hepsinde** boştu,
canlı site etiketi HTML'de yayımlamıyor. `goc_al` da etiket taşımıyor. Boş
bir `<select multiple>` ekranda çökmüş bir kutu olarak çiziliyordu.

**Sorun görsel değildi.** `HaberForm.clean()` yayına almak için en az bir
etiket şart koşuyor; seçilecek etiket olmadığı için **panelden hiçbir haber
yayınlanamıyordu**. `data-cip="1"` niteliği de ölüydü — `panel.js` içinde
karşılığı hiç yazılmamıştı.

**Çözüm: alan yazılabilir.** `EtiketAlani`, virgülle ayrılmış adları alıyor;
olmayan etiket **kaydederken** açılıyor. Üç karar:

* **Kayıt açma `clean()`te değil `_save_m2m()`te.** Doğrulamada açsaydık
  geçersiz bir form bile veritabanında öksüz etiket bırakırdı.
* **Eşleştirme slug üzerinden**, slug Türkçe-doğru küçültme + ASCII katlamayla
  (`arama_metni.anahtar`). Django'nun `slugify`'ı Türkçe harfi çevirmez,
  **atar**: "Şehreküstü" → `ehrekst`. Bizimki `sehrekustu`. Böylece
  "BURSA · bursa · Bursa" tek etiket oluyor, üç satır değil.
* **Öneriler `<datalist>` ile**, betiksiz çalışıyor. Liste 200'le sınırlı —
  sınırsız bırakmak `ilgili_haberler`de düzeltilen 356 bin `<option>`
  hatasının küçük ölçekte tekrarı olurdu.

### 29.2 Girdiler arka planlarıyla aynı renkti

Başsız Chrome'da, 10 panel ekranındaki **62 girdinin** hesaplanmış arka planı
ile onu taşıyan kabın arka planı karşılaştırıldı:

| ekran | önce | sonra |
|---|---|---|
| `/panel/haber/ekle` | **23/23 girdi aynı renk** | 0 |
| `/panel/akis` | 4/11 | 0 |
| diğer sekiz ekran | 0 | 0 |
| **toplam** | **27/62** | **0/62** |

Sebep tek satırdı: girdiler `background: var(--zemin)` kullanıyordu ve `body`
de aynı değişkeni kullanıyor. Haber formu diğer formların aksine kart değil,
çıplak sayfanın üstünde duruyor — orada fark **1,000:1**'e düşüyordu. Beyaz
kartların üstünde bile 1,083:1'di, yani neredeyse görünmez.

**Çözüm iki yeni değişken.** `--girdi-zemin:#E4EBF1` ve
`--girdi-cizgi:#788797`. Çerçeve WCAG 1.4.11'in etkileşimli öğe sınırı için
istediği **3:1**'i komşu olduğu üç renge karşı da geçiyor: beyaz karta
3,68:1, gri sayfaya 3,39:1, kendi dolgusuna 3,06:1. Eski `--cizgi` 1,23:1'de
kalıyor ve bu ölçütü karşılamıyordu.

İlk denenen `#7C8B9B` dolgusuna karşı 2,90:1'de kalmıştı ve **test onu geri
çevirdi** — çerçevenin iki yanı da sayılıyor.

Testler tarayıcı açmıyor: açsalardı CI'da Chrome gerekirdi. Renk sözleşmesini
ve kontrast oranını sayıyla kilitliyorlar; tarayıcı ölçümü kararı verirken bir
kez yapıldı ve sonuç sonradan doğrulandı.

**565 test geçiyor**, 10'u bu turda eklendi.

---

## 33. 29 Ağustos — `/resmi-ilan`: yer tutucu sayfa dizine çevrildi

§30 ve §32.5 anasayfadaki bölümü gerçek kayıtlara bağlamıştı ama "TÜM
İLANLAR" bağlantısı hâlâ `bekleyen.html` yer tutucusuna gidiyordu: okur
gerçek sekiz ilanı görüp bağlantıya basınca **"Resmî ilan kayıtları henüz
göç etmedi"** yazısıyla karşılaşıyordu. Bölüm gerçekleştiği için tutarsızlık
göze batar olmuştu. Sayfa artık 23 kaydın tamamını listeliyor.

### 33.1 Dizin seçki değil — ayrıldığı dört nokta

Anasayfadaki bölümün tasarım dili (tarih omurgası, tür rozetleri, aynı
şerit) sürdürüldü; **düzeni** ve **mekanizması** değişti.

1. **Süzgeç adreste, düğmede değil.** Anasayfada şerit JavaScript ile
   sayfadaki satırları gizliyor. Dizinde `?tur=ihale` bir bağlantı:
   paylaşılabilir, geri tuşuyla geri alınabilir, JavaScript kapalıyken de
   çalışır. Asıl gerekçe teknik: liste **sayfalanabilir** ve sayfalanmış
   bir listede tarayıcı içi süzgeç yalnız o sayfayı süzer — düğmedeki sayı
   ile davranış ayrışır.
2. **Sayılar arşivin tamamını sayar.** İlke anasayfayla aynı ve tek
   cümleyle yazılabilir: *düğmedeki sayı, basınca geleni sayar.* Orada
   tıklama sayfayı süzdüğü için sayı sayfayı sayıyordu (§32.5, madde 3);
   burada tıklama arşivi süzüyor. Şeritteki not bunu ayrıca söylüyor.
3. **Satırlar tek sütuna alındı ve tablo gibi hizalandı.** Seçkide iki
   sütun kart benzeri satır var; dizinde tarih, tür, başlık ve ilan
   numarası her satırda aynı x'te başlıyor. Gerekçe okuma biçimi: seçki
   okunur, dizin **taranır**. Hizalı sütun olmadan tür ve tarih taranamaz.
   Ölçüldü — dört alanın sol kenarı beş genişlikte de tek değer
   (33.4'teki tablo).
   - Tür sütunu **124 px sabit**: `max-content` her satırı kendi rozetine
     göre çizer ve sütun hizası ölür. 124, dört yasal türün en genişi olan
     PERSONEL ALIMI rozetine (ölçülen ~109 px) göre seçildi — o türde kayıt
     geldiği gün yerleşim kaymasın.
   - 720 px altında hizalı sütun taşıyacak yer yok; satır anasayfadaki
     yığılmış biçimine döner.
4. **Ay omurgası.** 23 kayıt 15 ayrı güne dağılıyor; güne göre gruplamak
   1-3 satırlık 15 küme demekti ve günü zaten satırın solundaki tarih
   bloğu taşıyor. Ay başlığı, kaydırırken "neredeyim" sorusunu yanıtlayan
   tek kırılım — ve §32.2'nin yıl sorununu da çözüyor: gün bloğu yılı
   göstermiyor ama başlıkta "AĞUSTOS 2026" yazıyor.

### 33.2 Sayfalama: kuruldu, 23 kayıtta etkin değil

`ILAN_SAYFA_BOYU = 40`, yani bugün **tek sayfa** ve sayfalama gezinmesi
hiç çizilmiyor. Bilerek:

- 23 satırlık bir dizini ikiye bölmek okurdan üçte birini saklardı ve
  sayfanın asıl iddiası ("gazetenin bu dönemde yayımladığı ilanların
  tamamı bu") tek ekranda okunabilmeli.
- Sitenin haber sayfa boyu (20) buraya uymuyor: dizin satırı bir haber
  kartından çok daha kısa.
- Mekanizma yine de kurulu, çünkü ilan modülü canlıya çıkınca kayıt sayısı
  hızla büyür ve sınırsız liste bir gün sayfayı düşürür. Test 45 kayıtla
  ikinci sayfayı ve süzgecin sayfalar arasında korunduğunu doğruluyor.

**Sıralama seçeneği bilerek eklenmedi.** İlan dizininin tek anlamlı sırası
yeniden eskiye. Başlığa göre sıralamak işe yaramaz — başlıklar tekrar
ediyor ("TAŞINMAZ SATIŞI YAPILACAK" üç kayıtta birebir aynı); türe göre
sıralamanın işini zaten süzgeç görüyor. Karşılığı olmayan denetim sayfayı
zenginleştirmez, kalabalıklaştırır.

### 33.3 Dürüstlük çizgisi — §32.5'in dersi sürdürüldü

Sayfanın notu anasayfadakinin **kopyası değil**. Orada bölüm bir seçki
olduğu için "toplam 23 kayıt" demek gerekiyordu; burada liste zaten
tamamı, o yüzden notun işi kaydın **neleri içermediğini** söylemek.

İki olgu da şablona çakılı değil, veriden okunuyor:

| cümle | veriden gelen | kayıt gelirse |
|---|---|---|
| "Son başvuru tarihi gösterilmez" | `bitis_tarihi` boş mu | cümle düşer |
| "İlan metinleri … arşiv dökümünde yok" | `metin` boş mu | cümle "ilan sayfaları henüz açılmadı"ya döner |
| "İCRA ve PERSONEL ALIMI türünde ilan yok" | `tur_dagilimi` | liste daralır |

Başlıklar bağlantı değil (ilan metni yok, detay sayfası yok), `href="#"`
yok, kaydı olmayan tür bağlantı değil `span` — boş listeye götüren bir
bağlantı bağlantı sayılmaz. Adres satırından gelen tanınmayan tür
(`?tur=uydurma`) 404 vermiyor, dizinin tamamına düşüyor.

**Kanonik adres her zaman `/resmi-ilan`.** `?tur=…` bir sayfa değil,
dizinin kesiti; kesitler ayrı indekslenirse aynı başlıklar birden çok
adreste görünür. `noindex` **eklenmedi**: kanonikle birlikte kullanılınca
ikisi çelişik sinyal veriyor. Sayfa artık `bekleyen.html`in `noindex`
etiketini de taşımıyor — gerçek sayfa oldu.

### 33.4 Ölçüm (başsız Chrome, `Network.setCacheDisabled`)

| genişlik | `clientWidth` / `scrollWidth` | yatay taşma | gün · tür · başlık · ilan no (sol kenar) | satır yük. |
|---|---|---|---|---|
| 360 | 345 / 345 | 0 | 23 · 86 · 86 · (yığılmış) | 83–100 |
| 768 | 753 / 753 | 0 | 23 · 86 · 224 · sağ 730 | 63 |
| 1024 | 1009 / 1009 | 0 | 23 · 86 · 224 · sağ 986 | 63 |
| 1280 | 1265 / 1265 | 0 | 96 · 159 · 297 · sağ 1170 | 63 |
| 1600 | 1585 / 1585 | 0 | 256 · 319 · 457 · sağ 1330 | 63 |

Dört sütunun da sol kenarı her genişlikte **tek değer** — 23 satırın
hiçbiri kaymıyor. Sayfadaki taşan öğelerin tamamı `div.akis` (son dakika
şeridi) içinde, tasarımı gereği; belge yatay kaymıyor.

Kontrast (en düşükler): şerit etiketi/notu, boş tür rozeti, ay sayacı ve
gün ayı **5,17** · ilan no ve kırıntı **5,50** · TEBLİGAT rozeti **6,62** ·
sayaç **7,60** · ay başlığı ve gün rakamı **12,41** · h1 ve İHALE rozeti
**13,21** · dönem çipi **16,51** · başlık ve basılı TÜMÜ **17,82**. Hepsi
AA eşiğinin (4,5) üstünde.

Odak **gerçek Tab tuşuyla** ölçüldü (`Input.dispatchKeyEvent`): üç süzgeç
bağlantısına da ulaşılıyor, `3px solid var(--kirmizi)`, 2 px aralık,
`:focus-visible` eşleşiyor. Kaydı olmayan iki tür `span` olduğu için sekme
sırasında yok. 140 Tab boyunca odaklanan **hiçbir öğe halkasız değil**.

**Ekran görüntüleri açılıp bakıldı** (360 · 768 · 1280 · 1600 · süzülmüş
hâl · sayfanın notu). İlk kırpma denemeleri üç kez **boş gri** resim
üretti: `Page.captureScreenshot`in `clip` alanı SAYFA koordinatı ister,
öğeyi görünüre kaydırıp viewport rect'ini clip diye vermek görüntüyü
sayfanın tepesinden alıyor. Ölçüm aracı yedinci kez yanılttı; çözüm
kırpmayı bırakıp öğeyi kaydırıp viewport çekmek oldu.

### 33.5 Ölçerek bulunan iki kusur (ikisi de bu turda girdi)

1. **360 px'te tür rozeti ortalanıyordu.** `align-self:center` yalnız
   ızgarada doğru; sütun yönlü flex'te aynı değer rozeti **yatayda**
   ortalıyor. Ölçüldü: başlık x=86 iken rozet x=171 ve 180 — iki farklı
   değer, yani satırlar arası hiza da yoktu. Dar ekran kuralına
   `align-self:flex-start` eklendi.
2. **`prefers-reduced-motion` süzgeç bağlantısında çalışmıyordu.**
   Seçici dosyanın ortasındaki mevcut `@media(prefers-reduced-motion)`
   bloğuna eklenmişti; özgüllük eşit olunca **dosyada sonra gelen** kural
   kazanıyor ve geçiş `0.15s`te kalıyordu (anasayfadaki düğme aynı anda
   0s ölçülüyordu). Blok dizin kurallarından sonraya alındı, ölçüm 0s.

### 33.6 Kapsam dışında bulunan ve düzeltilen bir kusur

`parca/sayfalama.html` **hiç biçimlendirilmemişti**. Ölçüldü
(`/bursa?sayfa=2`, 1280 px): "← Önceki 2 / 50 Sonraki →" tek satırda,
gövde metniyle aynı renkte, sayfanın sol kenarına yapışık akıyordu;
bağlantı olduğu ancak imleçle anlaşılıyor, dokunma hedefi 18 px
yüksekliğinde kalıyordu. Dizin aynı parçayı kullandığı için kural yazıldı
(37 px hedef, çerçeveli düğme, ortada konum); **kategori, ilçe ve arama
sayfaları da aynı anda düzeldi**.

### 33.7 `tur_dagilimi` iki yollu oldu

Anasayfa elindeki sekiz kayıtlık **listeyi** sayıyor; dizin arşivin
tamamını sayıyor ve oradaki liste sayfalanmış. QuerySet gelirse sayım
artık veritabanına bırakılıyor (`values_list().annotate()`), yoksa dizin
yalnız sayı basmak için bütün arşivi belleğe alırdı — 23 kayıtta
görünmez, ilan modülü canlıya çıkınca görünür. `order_by()` boşaltılmak
zorunda: Meta sıralaması GROUP BY'a sızıyor. İki yolun aynı çıktıyı
verdiği testle kilitli; anasayfanın çizdiği bölümün HTML'i değişiklikten
önce ve sonra **birebir aynı** (diff ile doğrulandı).

### 33.8 Testler

**550 test geçiyor** (`icerik taksonomi medya`; depo geneli 583); 18'i bu
turda eklendi (`icerik.tests.ResmiIlanDizini`). Kilitlenenler: yer tutucu
şablonun kullanılmadığı, tek `h1` ve kanonik adres, süzgecin adresten
çalıştığı ve kanonikte görünmediği, tanınmayan türün 404 vermediği,
kaydı olmayan türün bağlantı olmadığı, sayıların sayfayı değil arşivi
saydığı, sayfalamanın süzgeci koruduğu, ay başlıklarının ve tarihsiz
kayıt grubunun veriden geldiği, dönem etiketinin süzülen kümeden
okunduğu, üç dürüstlük cümlesinin veriden geldiği ve kayıt yokken
sayfanın ayakta kaldığı.

### 33.9 Açık kalan

- **İlan metni, BİK kodu ve bitiş tarihi hâlâ yok** (§24.3): ekleme formu
  dökümde kaydedilmemiş. Bu alanlar gelmeden ilan detay sayfası da "son
  başvuru" vurgusu da yapılamaz. Sayfa bunu okura söylüyor ve alanlar
  gelince cümleler kendiliğinden düşüyor.
- **Arşivde birebir aynı başlıklı kayıtlar var** — dizinde artık
  görünüyorlar: "BURSA 11.ASLİYE CEZA MAHKEMESİNDEN İLAN" (1664) ile
  "BURSA 11. ASLİYE CEZA MAHKEMESİNDEN İLAN" (1661) aynı gün, tek fark
  bir boşluk; "TAŞINMAZ SATIŞI YAPILACAK" üç kayıtta, "YILDIRIM'DA TAŞINMAZ SATIŞI" iki kayıtta birebir aynı. Tekilleştirme
  bir **veri** işi, gösterim işi değil (§32.7'deki Bursaspor bulgusuyla
  aynı sınıf).
- **Süzülmüş görünümde tür rozeti tekrar ediyor** (10 satırda 10 TEBLİGAT).
  Bilerek bırakıldı: rozet kaydın verisi, görünümün değil; satır bileşeni
  görünüme göre değişirse aynı satır iki farklı yerde iki türlü basılır.
- `/resmi-ilan` **site haritasında değil**. Artık gerçek bir sayfa;
  `besleme` tarafının kapsamı, bu turda açılmadı.
- Kayıtlar aktifleşmeye başlayınca `yayimlananlar()` süzgeci (arşiv kalır,
  pasif çıkar) yeniden değerlendirilmeli — §30'dan devreden madde.


## 34. 29 Ağustos — görsel denetim turu: Aşama 1+2 uygulandı

`web-tasarim-direktoru` ajanı siteyi başsız Chrome ile 5 genişlikte ölçtü
(360-1600) ve 18 maddelik öneri paketi çıkardı. Kullanıcı kararı: Aşama 1
(hata onarımları + hızlı kazanımlar) ve Aşama 2 (yerleşim/okuma) uygulanır;
Aşama 3 (serif gövde, kategori işaret renkleri, mobilde bileşen sırası,
15 slayt sözleşmesi) ayrı kullanıcı kararı bekliyor — uygulanMAdı.

### Hata onarımları (tasarım tercihi değil)

- **`--ses-isaret` tanımsızdı**: `.ses-okunan` vurgusu hiç çizilmiyordu.
  Demodan taşındı (`#FFF1B8`, koyu mürekkep üstünde 15,6:1).
- **"En çok okunanlar" manşetin kopyasıydı**: `havuz[:5]` manşetin ilk
  beşiydi; aynı başlık sayfada üç kez görünüyordu. Havuz `EN_COK` kadar
  büyüdü, kutu artık dilimlerin SONRAKİ beş kaydını alır (`al(EN_COK)`).
- **OTOMATİK GEÇİŞ düğmesi geri geldi** — §14'teki "seçim değil, varsayılan"
  kararı KORUNUYOR: sayaç açılışta yine başlar, düğme yalnız okurun
  duraklatma denetimidir (WCAG 2.2.2 görünür denetim ister). Hareket
  azaltmada düğme devre dışı, sayaç hiç dönmez (eski davranış).

### Sözleşme değişiklikleri (§1/§3.1'i etkileyen)

- **Makale sayfası rayı**: `.izgara`nın ikinci sütunu (320 px) artık haber
  detay ve köşe yazısında DOLU — reklam (`-Haber arası1-`) + en çok
  okunanlar + (haberde) ilçe listesi / (köşede) yazar dizini. Ölçülen kusur:
  her makale sayfasında 342 px ölü sütun, genişliğin %31'i.
  `tests_yerlesim.MakaleRayi` iki şablonda `aside.ray` varlığını kilitler.
- **Kart yapısına zaman satırı**: `parca/kart.html` `.ust` satırı artık
  `<time>` taşır (kayıtta varsa). Kategori sayfası kendi adını kartlarda
  gizler (`kategori_gizle`); ilçe adı basılmaya devam eder.
- **Kategori sayfasında ilk haber büyük** (yalnız 1. sayfada): `.kart.genis`
  iki sütuna yayılır, fotoğraf sola geçer.
- **Tip merdiveni**: manşet 34→42 (1140'ta 34, 768'de 30, 600'de 26),
  ikincil slayt 20→26, dörtlü 17→21 (ızgara kartının 18'inin ALTINDAydı —
  inversiyon düzeldi), en-çok listesi 14→15, 600'de kart 18→17.
  Manşet/kart oranı: 1280'de 2,33 (eski 1,89), 360'ta 1,53 (eski 1,22).
- **Manşet nefesi**: `.slayt .yazi` yatay dolgu 54→24 px (oklar üst sağda
  ikili grup); mini slaytta oklar kalktı (sütunun %20'siydi), gezinme
  numaralı düğmelerle.
- **Sayfalama numaralı**: `_sayfala` `sayfa.numaralar` kurar
  (`get_elided_page_range`), parça "1 … 4 [5] 6 … 50" çizer. `icerik` ve
  `medya` sayfalayıcıları aynı sözleşmeyi taşır.

### Diğer görünür değişiklikler

- Kart ızgaraları `--zemin`e oturdu (`:has` ile; beyaz üstünde beyaz kart
  1,29:1 çizgiyle ayrışmıyordu). Tembel görsel yer tutucusu `--foto-bekleme`
  (açık nötr) oldu; slayt penceresi `--gece` kaldı (karartma gradyanı onunla
  ayarlı). Dokunma hedefleri 24 px'e çıktı (kutu-bas bağlantısı, servis
  şeridi, son dakika, mini slayt noktaları). Detay gövdesi 16→18 px,
  `max-width:68ch` (satır 79 karakterdi). Künyeye okuma süresi eklendi
  (`okuma_dakikasi`, 200 kelime/dk; kelime_sayisi boşsa basılmaz).
- **Mobil tepe**: ≤600 px'te servis şeridi tek satır (üç bağlantı gizli,
  künyede zaten varlar), piyasa bandı tek satır yatay kaydırma, boş reklam
  yuvası 70 px. Hedef: ilk editoryal piksel 603 → ≤320.
- **yer-not blokları katlandı**: 9 notun 495 px'i (sayfanın %8,5'i,
  manşetten fazla) tek satırlık `<details>` başlığına indi. Metinler
  SİLİNMEDİ — ait oldukları bölümün altında, bir tıklama uzağında.
  Direktörün önerisi metinleri künyeye taşımaktı; bağlam değişkenleri
  (ilan sayıları, arşiv adetleri) anasayfa görünümüne bağlı olduğu için
  yerinde katlama seçildi — beyan ile bölüm yan yana kalıyor.


### §34 doğrulama turu — ölçüldü, düzeltildi (aynı gün)

Uygulama sonrası direktör ajanı başsız Chrome ile yeniden ölçtü: 11 ölçüt
GEÇTİ (ses vurgusu, duraklatma düğmesi davranışı, en-çok/manşet ayrışması,
makale rayı, kartlarda saat 20/20, tip oranları 2,33 / 1,53, kategori lead,
numaralı sayfalama, kontrast — 42 px manşet başlığı en kötü zeminde 6,71 —
yatay taşma 0, sayfa içi dikiş). 8 bulgu KALDI ve aynı gün düzeltildi:

- **K1** `.kart.genis` 360 px'te sütuna dönmüyor, 126 px taşıyordu: medya
  kuralının özgüllüğü (0,2,0) taban kuralına (0,3,0) yeniliyordu. Seçici
  `.kutu-izgara .kart.genis` yapıldı; `.ic`e `min-width:0`.
- **K2** ≤600 piyasa bandında saat kalemlerin üstüne biniyordu: `dl` taban
  `flex:1`i koruyup sıkışıyordu → `flex:0 0 auto`, kaydırmayı kap yapar.
- **K3** Mini slaytta OTOMATİK GEÇİŞ ikinci satıra kırılıp manşet altında
  27-63 px boş şerit açıyordu: mini sayaç gizlendi (aria-hidden'dı,
  numaralı düğmeler aynı bilgiyi verir), düğme sıkılaştı.
- **K4** 1001-1140 bandında `.izgara` 320'de kalıyor, anasayfa↔makale ray
  dikişi 20 px kayıyordu: `.izgara` da 300'e iner;
  `tests_yerlesim` dar ekran testi artık ÜÇ seçiciyi kilitler.
- **K5** `max-width:68ch` fiilen 87 karakter veriyordu (`ch` = "0" rakamı
  genişliği 10,1 px; Türkçe gövde ortalaması 7,9 px). Ölçü **54ch** ≈ 546 px
  ≈ 68 gerçek karakter. (§34'teki "satır 79 karakterdi" tespiti doğru,
  "68ch = 68 karakter" varsayımı yanlıştı.)
- **K6** 24 px altı 68 hedef kalmıştı (44'ü künyede): künye listeleri, ilçe
  şeridi, Bursaspor listesi, kart/sıra başlık bağlantıları, ilan tür
  düğmeleri, yer-not başlığı — negatif kenar boşluğu tekniğiyle görünüm
  değişmeden 24 px'e çıkarıldı.
- **K7** yer-not oranı %4,76 (hedef ≤%3): başlık satırı sıkılaştırıldı
  (~%4). **Bilinçli kalan sapma:** ≤%3 ancak notların künyeye taşınmasıyla
  olur; not metinleri anasayfa görünümünün bağlam değişkenlerine bağlı ve
  beyanın bölümüyle yan yana durması tercih edildi. Yeniden açılacaksa
  kullanıcı kararı.
  **KAPANDI — 31 Ağustos 2026 (§39):** kullanıcı kararı geldi, notlar
  panellerden kalktı ve `/veri-kaynaklari` sayfasına taşındı. "Bağlam
  değişkenlerine bağlı" gerekçesi çözüldü: sayfa statik metin değil, aynı
  sayıları kendi görünümünden okuyor.
- **K8** 360'ta ilk editoryal piksel 354 (hedef ≤320): boş reklam yuvası
  48 px, main dolgusu 8, piyasa altı 10 → hesaplanan ≈320. Kalan iki kalem
  (kategori bandı 82, servis 56) dolu bileşenler, kırpılmadı.


### §34 kapanış — üçüncü ölçüm turu (aynı gün)

İkinci turda K1 (genis kart taşması), K2 (piyasa örtüşmesi), K4 (ray
dikişi) kapandı; üç kalem ile bir yan etki kaldı ve düzeltilip üçüncü
turda ölçüldü:

- **K3 kapandı**: manşet altı boşluğun kalan 36 px'i mini slayttan değil,
  1140 bloğundaki `.slayt-pencere{height:392px}`ten geliyordu — sağ
  sütunun katı asgarisi 472 px. Pencere o bantta 428'e alındı; boşluk
  dokuz genişlikte de 1 px, 900 px'te ≤1000 kuralı (360) hâlâ kazanıyor.
- **K5 kapandı**: 54ch ile ortalama 65,1 ölçülünce 55ch yapıldı →
  ortalama **66,6** karakter (66-70 bandı içinde).
- **K6 kapandı**: 24 px altı görünür dokunma hedefi yedi sayfa/genişlik
  ölçümünde **0** (galeri/video başlıkları ve kırıntı bağlantıları da
  eklendi; RSS bağlantısına min-width).
- **Yan etki kapandı**: künyede negatif kenar boşluğu komşu bağlantıları
  8 px bindiriyor, kenara tıklama YANLIŞ bağlantıyı açıyordu. Ders:
  negatif kenar tekniği yalnız satır adımı kutudan büyük listelerde
  güvenli. Künye `line-height:1.45` + gerçek dolguya çevrildi; örtüşme
  ve kenar isabeti hatası 0, künye görünümü normal (465 px).
- **K8 açık kaldı, bilinçli**: 360'ta ilk haber kartı y=322 (hedef 320,
  ilk ölçüm 603'tü). Kalan 2 px için boş reklam yuvasını daha da kırpmak
  gerekirdi; 322 ile 320 arasında okur davranışı farkı yok — kapatıldı.

Sağlamlık: yatay taşma 10/10 ölçümde 0; ray dikişi üç bileşende de tek
x (1024: 699 · 1280: 863). Django testleri her turda 552/552.


## 35. 30 Ağustos 2026 — tur 2: menü, yazarlar, sosyal, haber sunumu

Kullanıcı altı iş verdi: (1) slayttaki OTOMATİK GEÇİŞ düğmesi kalksın,
otomatik geçiş zaten varsayılan olsun; (2) hava/namaz/eczane paneli
aşağı insin; (3) yazarların sunuluşu tamamen değişsin ve fotoğrafları
canlı siteden çekilsin; (4) haberlerin sunumu daha dikkat çekici olsun,
konum ve kutu boyutları serbest; (5) sosyal medya bağlantıları üstte ve
etkileyici olsun; (6) menü görünümü tamamen değişsin. §34'ün 3. aşama
kalemleri (serif gövde, kategori işaret renkleri, mobilde manşet önde,
15 slayt sözleşmesi, iki ağırlıklı bölüm başlığı) bu turda onaylandı.

Tasarım, üç bağımsız öneri (ulusal-klasik · modern-vurgu · yerel-kimlik)
ve bir jüri sentezi ile seçildi; keşif ajanları canlı sitedeki portrelerin
indirilebilirliğini ve arşiv medya altyapısını önce ölçtü.

### Sözleşme değişiklikleri (§1'i günceller)

- **Bileşen 7 — ana manşet: 15 slayt → 5 slayt.** Kalan 10 kayıt slaytın
  altında **GÜNÜN MANŞETLERİ** başlık listesi (`.manset-liste`, iki sütun,
  tarihli). Gerekçe §4 madde 1'in kendi ölçümü: "5'ten sonrası neredeyse
  görülmüyor". Bursaspor bölümünde işe yaradığı ölçülen çözümün uyarlaması.
  `views.MANSET=5`, yeni `MANSET_LISTE=10`; havuz büyüdü, dilimler
  kesişmiyor ve §34'ün "en çok okunanlar manşetin kopyası değil"
  güvencesi testle yeniden kilitlendi.
- **Bileşen 11 — haber kutuları 10 → 11.** İlk kart iki sütuna yayılıyor
  (`.kart.genis`, kategori sayfasıyla ortak); 1 + 10 beş tam satır eder.
- **Bileşen 12 — şehir servisleri raydan çıktı.** Artık **RESMÎ İLANLAR ile
  BURSASPOR arasında**, tam genişlikte, **üç panel birden AÇIK**
  (`#sehir-servisleri`, `.servis-uclu`). Sekme mimarisi 300 px'lik ray
  zorunluluğuydu; genişlikte üçü de tıklamadan görünüyor. `panel-hava`,
  `panel-vakit`, `panel-eczane` kimlikleri KORUNDU — menü ve künye
  çapaları kırılmadı. `role="tablist"` DOM'u anasayfadan kalktı;
  `site.js` `.sek` bulamayınca dokunmuyor (Bursaspor sekmeleri sürüyor).
- **Bileşen 13 — yazarlar rayı, YAZAR KUŞAĞI oldu.** Tam genişlik,
  portreli, scroll-snap ile kaydırılan 10 kartlık şerit; manşet bloğunun
  altında. Sağ raydaki beş satırlık liste kalktı. `.yazar-ray` kuralları
  köşe yazısı sayfasının rayında kullanıldığı için duruyor.
- **Sağ ray yeni dizilim:** EN ÇOK OKUNANLAR → **İLÇE İLÇE BURSA** (yeni
  çip ızgarası; ilçeler menüde katlanmış duruyordu) → `-Haber arası1-`
  300×250. Reklam yuvalarının adı ve ölçüsü değişmedi.
- **Bölüm başlığı iki ağırlıkta.** Editoryal bölümler (SON HABERLER ·
  YAZARLAR · GALERİLER · VİDEOLAR · İLÇE İLÇE BURSA) `.kutu-bas.hafif`:
  beyaz zemin, lacivert başlık, lacivert alt çizgi. Servis ve yükümlülük
  bölümleri (ŞEHİR SERVİSLERİ · RESMÎ İLANLAR · VİZYON · PİYASA) dolu
  bantta kaldı; EN ÇOK OKUNANLAR dolu kırmızı; **BURSASPOR dokunulmaz**.
  Kırmızı fitil (`h2::before`) iki ağırlıkta da duruyor — ortak imza.
- **Dar ekranda (≤768 px) sıra: manşet → manşet listesi → dörtlü.**
  `.ust-blok` sarmalayıcısı ve `order`; DOM ve odak sırası değişmiyor.
  360'ta okur ana manşete 1550 px aşağıda varıyordu.

### Menü — sidebar kalktı, banda asılı beyaz mega levha geldi

Kullanıcı 28 Ağustos'ta gelen koyu sidebar'ı beğenmedi. Yeni menü bandın
altına asılan beyaz levhadır; masaüstünde **beş sütunlu** açılır
(İLÇELER en geniş sütun), dar ekranda akordeon kalır.

Kritik karar: **şablona `open` yazılmadı.** Bölümleri geniş ekranda
`site.js` `menuAc()` açıyor (3 satır). Böylece sunucu HTML'i bayt bayt
aynı kalıyor ve menünün DOM sözleşmeleri — 17 ilçe + "Tüm ilçeler",
50 bağlantı, tek açık bölüm, `<summary><h2>` düzeni, odak tuzağı —
hiç oynamadı. Perde yine ayrı öğe değil, ikinci gölge: karartma levhanın
üst kenarından aşağı uzanıyor, bant ve MENÜ düğmesi aydınlık kalıyor,
dışarı tıklayınca kapanma davranışı sürüyor. `--menu-bas` kullanımsız
kaldı, yorumla işaretlendi.

### Sosyal medya üste çıktı

Beş SVG sembolü (`sos-x` · `sos-instagram` · `sos-youtube` ·
`sos-whatsapp` · `sos-rss`) `parca/simgeler.html`e eklendi — dış kaynak
yok, sayfa internetsiz açılmaya devam ediyor. Üst servis şeridinin sağ
kümesinde **İHBAR HATTI pili** + beş ikon duruyor; künyedeki liste aynı
sembollerle güçlendi ve yerinde kaldı.

**Ayrı şerit açılmadı**: §34 K8'de piksel piksel kazanılan mobil tepe
bütçesi (ilk haber ≤322 px) geri yakılmıyor. ≤600'de yalnız metin
bağları (Künye/İletişim/E-Gazete — künyede zaten varlar) ve pilin yazısı
gizleniyor, ikonlar kalıyor; ≤420'de YouTube ve RSS düşüyor.

### Entegrasyon

- **Gövde serifi**: `--serif` = Roboto Serif → Georgia. Yalnız `.metin` ve
  `.detay .spot`; listeler ve başlıklar sans. Tek font isteği, italik
  kesim alınmadı. **Satır uzunluğu yeniden ölçülecek** — `ch` birimi "0"
  rakamının genişliğidir ve serifte farklı çıkar (§34 K5 dersi).
- **Kategori işaret rengi denemesi**: yalnız `--isaret-bursa` (#0E6E8C,
  beyaz üstünde 5,79 · zemin üstünde 5,10) ve `--isaret-ekonomi`
  (#7A5200, 6,93 · 6,10). Yalnız `.kart .ust` etiketinde, yalnız açık
  zeminde; kalan 11 kategori kırmızıda. Geri alma maliyeti iki CSS satırı.
- **Dörtlü**: dört kutucuk **EŞİT genişlikte**. İlk hâlinde ilk kutucuk
  1,5fr ve 25 px başlıktı ("ölçülü asimetri"); 30 Ağustos'ta kullanıcı
  eşit olmalarını istedi ve asimetri geri alındı. Vurgu yalnız kırmızı
  üst çizgide kaldı — ızgarayı ve tip merdivenini bozmuyor, sıralamayı
  yine de belli ediyor. Ölçüldü (768·1024·1280·1600): dört kart da
  sırasıyla 359,5 · 236,8 · 264,5 · 264,5 px, başlıklar 21 px, yatay
  taşma 0. Foto yüksekliği hiç değişmedi.

### Yazar portreleri — canlı siteden indirildi

`medya/management/commands/yazar_portre_indir.py`. Ölçülen durum: göç,
portre diye kaynağın `og:image` karesini almıştı — **37 kaydın 37'si de
1200×630**, yani paylaşım kırpımı; yuvarlak avatarda yüz kesiliyordu.

Canlı site aynı fotoğrafı `/static/<YYYY/AA/GG>/<ad>_small.jpg` olarak
**270×270 kare** de yayımlıyor, ama ölçüldü: bu biçim yalnız **yeni**
kayıtlarda (kaynağı `_large.webp` olanlar, 2025+) var — **19 kayıt**;
2021-2024 kayıtlarında 404 dönüyor ve elde yalnız 750×500 kalıyor —
**18 kayıt**. Komut sırayla dener, ilkini alır.

**Teşhis indirdikten sonra derinleşti — dosyalar açılıp GÖRÜLDÜ.**
750×500 olan şey bir portre değil, gazetenin **afiş şablonudur**: solda
yazarın adı büyük harflerle, arkada harita grafiği ve logo, yüz ise sağ
üçte birde. Ortadan kırpılsaydı yuvarlak avatarda yüz değil **harita**
görünecekti. İki biçim bu yüzden dosya adında ayrılıyor:

    {slug}-portre.jpg   270×270 gerçek portre  -> ortadan kırpılır
    {slug}-afis.jpg     750×500 afiş           -> `object-position:88%`

Ayrımı CSS `img[src*="-afis"]` ile yapıyor: model alanı ve migration
gerekmedi. Pillow ile kırpmak da çözerdi ama yeni bağımlılık getirirdi.
Ders, §34'ün "tarayıcıda ölçerek doğrula" kuralının görsellere uzanan
hâli: **boyut doğru diye içerik doğru sanılmaz, dosya açılıp bakılır.**

İlk çözüm `object-position:88%` ile pencereyi sağa kaydırmaktı; ölçümde
yetmediği görüldü — kare kırpım 500 px, yüz ise 300 px olduğu için afişin
adı ve haritası daireye sızıyor, avatarlarda "AN PÇU" gibi harf
kırıntıları okunuyordu. İkinci çözüm gerçek **yakınlaştırma**: `.portre`
bir sarmalayıcı (`<span class="portre"><img></span>`), afiş 260×260'lık
bir pencereye yakınlaştırılıyor. Yüzde kullanıldığı için 96/80/72 px'lik
üç boyda da aynı kırpım çıkıyor.

**Üçüncü katman: afiş şablonu İKİ ÇEŞİT.** Yakınlaştırma sonrası ölçümde
18 afişin 16'sı temizken 2'si hâlâ sızdırıyordu. 18 kaydın tarihleri
gruplandı, sonra **10 dosya açılıp gözle sınıflandırıldı**:

| Parti | Adet | Şablon | Yüz merkezi | Pencere |
|---|---|---|---|---|
| 2022-01-13 | 7 | "beton" — gri duvar, koyu kırmızı şevron | x≈570 | x∈[440,700] · `left:-169%` |
| 2023-07-10 ve sonrası | 11 | "harita" — kırmızı Avrupa haritası | x≈620 | x∈[490,750] · `left:-188%` |

Gazete yazar afişini 2023'te yenilemiş. Tek pencere ikisine birden
uymuyordu: haritaya göre ayarlanan pencere beton şablonunda yüzü sola
itip sağ üçte biri duvara ayırıyordu. Şablon artık dosya adında
(`-afis-harita.jpg` / `-afis-beton.jpg`, `AFIS_SINIRI = "2023-01-01"`);
CSS iki `left` değeri kullanıyor, ortak `top`/`width` değişmiyor.

**Dördüncü katman: şablon da tek başına yetmiyor.** İki pencereyle
ölçüldüğünde beton grubunun altısı isabetliydi (yüz ekseni x≈565-600,
pencere merkezi 570) ama **Av. Veysel Tayyar** x≈530'da kaldı — daire
çapının %11'i kadar kaçık. Yedi beton afişinin tamamı gözle
sınıflandırıldı; tek aykırı o. Çözüm ölçülen bir **istisna satırı**:
`img[src*="av-veysel-tayyar"]{left:-158%}`. CSS'te yorumla "bu bir yama,
kural değil" diye işaretli; yeni aykırı ölçülürse yanına eklenir. Kalıcı
çözüm görsel başına odak noktası saklamaktır (model alanı + migration) —
37 kayıt için bugün gereksiz.

**Kare portrelerde baş ölçeği eşitlendi.** 270×270 kaynaklar yarım boy
çekim: baş daireyi %33 dolduruyordu, afiş kırpımlarında %56 — şeritte baş
ölçeği iki kata yakın oynuyordu (ölçüldü). Kare portreler de
yakınlaştırıldı (`left:-21%; top:0; width:142%` = kaynağın x∈[40,230] ·
y∈[0,190] penceresi) ve baş %47'ye çıktı. Pencere karenin üst %70'ini
kapsadığı için baş kesme riski yok.

**Ders (§34'ün "ölçerek doğrula" kuralının görsel katmanı):** boyut
doğru olabilir, kırpma matematiği doğru olabilir, sınıflandırma doğru
olabilir ve iş yine yanlış görünebilir. Görsel işlerde **örneklem tek
dosya değildir** ve son söz ölçümün değil **bakmanın**dır: bu turda üç
ayrı kusur (afiş olduğu, iki şablon olduğu, bir aykırı poz olduğu)
yalnızca dosyalar açılıp görüldüğü için bulundu.

### Ölçüm ortamı tuzağı — 360 px'teki üçüncü satır

Denetimde 360'ta üst şerit 92,8 px (3 satır) ve ilk editoryal piksel 359
ölçüldü; §34'ün ≤322 hedefi tutmuyor göründü. Sebep editoryal değil:
**"Reklamları gizle" sunum düğmesi 102 px** ve `.sag` kümesini üçüncü
satıra itiyor. Düğme `icerik/baglam.py::_reklam_dugmesi` ile yalnız
`is_staff` oturumunda **ya da 127.0.0.1/localhost host'unda** çiziliyor —
yani bütün ölçümlerde var, gerçek ziyaretçide hiç yok. Düğme gizlenerek
ölçüldüğünde 360'ta şerit 55,8 px ve ilk editoryal piksel **322** (600'de
304, 768'de 60,8). Gerileme yok.

**Bundan sonraki ölçüm turları için:** yerel sunucuda alınan tepe
ölçümleri bu 102 px'i içerir; mobil tepe bütçesi ölçülürken düğme
gizlenmeli, yoksa olmayan bir kusur kovalanır.

### Ölçüm turu bulguları (aynı gün, düzeltildi)

- **K1 — bir özgüllük çatışması üç şeyi birden bozuyordu.** `.servis .sag a`
  kuralı (0,2,1) tur 2'de eklenen üç kuralı eziyordu: ihbar pili
  `inline-flex` olamıyor (ikon ile yazı **alt alta** düşüyor, yatay dolgu
  0, "İ" kırpık), sosyal ikonlar `grid` olamıyor, ≤420'deki `dar-gizle`
  hiç tutmuyordu (beş ikonun beşi de duruyordu). Kural zaten yalnız metin
  bağları içindi; hedefi `.servis .ust-baglar a` olarak daraltmak üçünü
  birden çözdü. **Ders: yeni kural eklerken var olanın özgüllüğü
  ölçülmeli — sessizce ezilen kural hata vermez, yanlış görünür.**
- **K3 — `:first-child` hiçbir şeyle eşleşmiyordu.** `.dortlu`nun ilk
  çocuğu ekran okuyucu için duran gizli `<h2>`; dört kartın dördü de
  lacivert çizgi alıyor, ilk başlık 21 px kalıyordu. `:first-of-type`
  ile düzeldi.
- **K4 — serif satırı yeniden ölçüldü.** `ch` neredeyse aynı kaldı
  (10,08 ↔ 10,12) ama Türkçe gövdenin gerçek karakter genişliği 7,79 →
  9,14 px (%17,4) çıktı ve 55ch ile satır 55,1 karaktere düştü.
  **68ch** ≈ 685 px ≈ 66-70 gerçek karakter. 1024 px'te makale sütunu
  623 px olduğu için orada satır ~62'de kalıyor — ızgara geometrisi,
  `max-width` kusuru değil.
- **K5** köşe künyesindeki yazar bağlantısı 78×18 idi, 24 px'e çıktı.
- **Eczane tarihi** ham ISO ("2026-08-29") basılıyordu; yeni `iso_tarih`
  süzgeci tür dönüşümü yapıyor, ay adı Django'nun Türkçe çevirisinden
  geliyor.

Ölçümde **GEÇEN** başlıklar: mega levha (bandın altına 0 px farkla
oturuyor, beş sütun, 407 px yükseklik, 325 Tab adımında odak kaçışı 0,
50 bağlantı ve 18 ilçe yerinde), yazar kuşağı (10 kart, kaydırma sayfayı
taşırmıyor, 10/10 portre yükleniyor), manşet 5+10, şehir servislerinin
yeni yeri ve üç açık panel, mobil sıra (manşet → liste → dörtlü), ray
dikişi (1024: 699 · 1280: 863, anasayfa = haber = köşe), 36 taşma
ölçümünün 36'sı 0, kontrast örnekleminin tamamı AA üstü, ham hex 0.

Dosyalar `D:\bursa-hakimiyet-arsiv\gorseller-yazar\portre\{slug}-portre.jpg`;
`/arsiv-medya/` yalnız dört beyaz listeli klasörü servis ediyor ve
`gorseller-yazar` onlardan biri (portre `gorseller/` ağacına konursa
404 olurdu). Yanına `KAYNAK.tsv` yazılıyor: hangi dosya hangi adresten,
hangi biçimde, kaç bayt. **Hak teyidi hâlâ açık kalem** — portreler
gazetenin kendi yayınından ama yayın öncesi teyit hukuki teyit
listesindedir.

Komut nazik: Chrome imzalı doğrudan istek (WebFetch bu sitede engelli),
istekler arası 1 sn, zaman aşımı 30 sn (CDN istek başına 0,4-20,6 sn
ölçüldü). Tekrar çalıştırılabilir; diskte olanı yeniden indirmez.
DB yazımı kısa tek işlem + geri çekilmeli tekrar, ve **dosya diskte
gerçekten var mı** diye doğrulanıyor — `gorsel_yolu()` diske bakmaz,
bayrak yanlışsa kırık resim basar. Uyarı: `medya_goc_al` yeniden koşarsa
`gorsel_dosya`yı arşiv JSON'una geri yazar; komut o zaman tekrar koşulur.

### Testler

554 test (2 yeni). Güncellenenler: bileşen sayıları (5+5 slayt, 11 kutu,
`manset_liste` 10), manşet/en-çok/liste kesişimi 0, yazar sorgu sınırı
5→10 (ölçüt "yazar başına bir sorgu", sabit sayı değil), sidebar testi
mega levha testine dönüştü (+ masaüstünde beş sütun ve JS'in açması).
Kategori/ilçe sayım testleri **veriden türetiliyor** artık — fikstür
büyüyünce kırılan sabit sayılar kalktı.

### Bu turda YAPILMAYANLAR (bilinçli)

Mega levhanın DOM'unu yeniden sıralamak · `main` düzeyinde flex/order ·
EN ÇOK OKUNANLAR'ı raydan almak · dörtlüyü yatay mini karta çevirmek ·
kart üst çizgisini kategoriye göre renklendirmek (dörtlünün çizgi diliyle
çakışıyor) · sosyal bağlantıları mega levhaya koymak (50 bağlantı
sözleşmesi) · ayrı sosyal şerit (mobil tepe bütçesi).


### §35 kapanış — son görsel doğrulama

Veysel istisnası ve kare portre yakınlaştırması gözle doğrulandı:

- **Veysel Tayyar `-158%`**: yüz ekseni kaçıklığı %16'dan **%5'e** indi
  (grubun kendi hata bandının içinde); sağdaki duvar/şevron bloğu gitti,
  sol alttan afiş yazısı girmedi. Sınır ölçüldü: `-154%`'te bordo harf
  kenarı belirir, `-150%`'de "VEYSEL"in L'si girer — yani değer güvenli
  tarafta ama payı **4 puan**; bu satır oynatılacaksa yeniden ölçülmeli.
- **Kare portrelerde baş üstü kesilmedi** (taç payı kaynakta 9-16 px);
  `top:0` zaten üst sınır, daha iyisi bu kaynaklarla alınamaz.
  Baş/daire oranı %29-46 bandından **%41-65**'e çıktı, afiş bandı (%49)
  ile aynı komşuluğa geldi.

**Açık kalan (kabul edilen) kalem:** kare portrelerin baş ölçeği kendi
içinde hâlâ 1,6× yayılıyor (Ali Genç %65 ↔ Atilla Sağım %41, üstelik
şeritte bitişikler). Sabit 1,42× katsayı kaynaktaki farkı da büyüttü.
Eşitlemek **dosya başına ölçek** ister — Veysel istisnasıyla aynı yere
çıkar: doğru çözüm görsel başına odak noktası + ölçek saklamaktır
(model alanı + migration). 37 kayıt ve tek şerit için bugün açılmadı;
yayın öncesi ya da yazar sayısı arttığında yeniden değerlendirilir.
Yayılım turun başında 2× idi, bugün 1,6× — gerileme değil, kalan pay.


---

## §36 — kategori bandı tam ekran · son dakika raya taşındı (30 Ağustos 2026)

Kullanıcı isteği (iki tur): "kategorilerin olduğu şeriti biraz daha büyüt ve
tüm ekrana genişlet" → sonra "tam ekranı kaplamıyor, belki reklam panosuyla
çakıştığı için, bunu düzelt · son dakika için D seçeneğini yap".

---

### 1. Bant — tam ekran ve büyütme

**Sorun (ölçüldü).** Bant `.orta` sütununun içindeydi, lacivert zemin
**1100 px'te kesiliyordu**. Üstündeki servis şeridi ise zaten tam ekrandı.
1920 px'lik ekranda iki şerit üst üste ama farklı genişlikteydi.

**Yapılan.**

1. **Taşıma.** `parca/kategori_bandi.html` include'ı `.orta`nın dışına,
   `.sayfa` ızgarasının üstüne — doğrudan `<body>` altına — alındı.
   `position:sticky` bozulmadı: yeni ebeveyn `<body>`. (Eski uyarı geçerli:
   bandın etrafına **sarmalayıcı eklenmeyecek**.)
2. **Kapak yok.** İlk denemede iç kutu `.servis-ic` gibi 1480 px'e
   kapatılmıştı. Kullanıcı bunu "tam ekranı kaplamıyor" diye bildirdi ve
   haklıydı: 1600 px'te zemin tam ekran ama kalemler iki yanda 60'ar px boş
   lacivert bırakıyordu. Kapak kaldırıldı — logo x=0'a, MENÜ ekranın sağ
   kenarına oturuyor. Artan genişlik `.kategori-liste a{flex:1 1 auto}` ile
   **10 kaleme eşit dağıtılıyor**; sabit bıraksaydık 2560 px'te sağda büyük
   bir boşluk kalırdı. Mega levha da aynı biçimde kenardan kenara.
   **GERİ ALINDI — 31 Ağustos 2026 (§41):** kullanıcı bu kez içeriğin
   daraltılmasını istedi; kapak 1480 px olarak geri kondu, zemin tam
   ekran kalmaya devam ediyor.
3. **Büyütme.** Kalem yazısı 13,5 → **15 px**, dikey dolgu 11 → **14 px**,
   logo 30 → **36 px**, MENÜ ve arama aynı oranda. Bant **40 → 50 px**.

### 2. Yan reklam rayı — gerçek çakışma vardı

Kullanıcının sezgisi doğru çıktı. `.yan-reklam{position:sticky;top:14px}`
idi; bant 50 px'lik yapışkan ve z-index 40 olduğu için ray panosunun **üst
36 px'i bandın arkasına giriyordu**. `top:64px` yapıldı (50 px bant + 14 px
eski pay). Kaydırılmış sayfada ölçüldü: bant.alt=50, ray.üst=64 → çakışma
yok.

### 3. Kırılma noktaları — yeniden ölçüldü

Bant büyüyünce eski 1119 px eşiği yetmez oldu: **1262 px'te MENÜ düğmesi
ikinci satıra düşüyordu** (bant 50 → 98 px). Ölçülen parça genişlikleri:
logo 155 · 10 kalem 863 · arama kutusu 220 · MENÜ 88 → **toplam ~1350 px**.
Arama simgeye inince kutu 220 → 46, gereken **~1176 px**.

| Genişlik | Bant | Durum |
|---|---|---|
| ≥ 1360 px | 50 px | Tam: logo + 10 kalem + arama kutusu + MENÜ |
| 1176–1359 | 50 px | Arama **simgeye** iner (tıklayınca alt satırda açılır) |
| 1001–1175 | 42 px | Kalemler **büyümeden önceki** ölçüye döner (13,5 px / 30 px logo) |
| ≤ 1000 px | 78–82 px | İki satır, dört kalem — **büyüme geçersiz** |

1001–1175'te kalem düşürmek yerine ölçü küçültmek seçildi: onlu bant
sözleşmesi masaüstünde bozulmasın.

**Dar ekranda büyüme bilerek uygulanmıyor.** Bant orada zaten tam
genişlikte, yani kazanç yok ama bedeli var — mobil tepe bütçesi (§34 K8,
ilk haber ≤322 px) bandın üst satırını 38'den 48 px'e çıkarırdı.

Yapışkan bant büyüdüğü için çapa payları güncellendi: `main` 52 → **62 px**,
`.servis-dilim` 64 → **74 px**.

---

### 4. SON DAKİKA — kayan şerit kaldırıldı, raya sabit liste geldi (D)

Dört seçenek sunuldu (A: şerit tam ekrana · B: banda yapıştır ve yapışkan
yap · C: manşetin üstüne indir · D: rayda sabit liste). **Kullanıcı D'yi
seçti.**

- `parca/son_dakika.html` yeniden yazıldı: `.kutu` + `.kutu-bas.vurgu`
  bileşenleriyle **kırmızı başlıklı ray kutusu**. Kayan `.akis`, ikinci
  (`aria-hidden`) kopya ve `@keyframes kay` silindi.
- **Neden:** kayan yazı okunması en zor kalıptır ve
  `prefers-reduced-motion` açık olan okurda şerit duruyordu — o okur
  listenin yalnız başını görüyordu. Sabit listede herkes aynı içeriği
  görüyor, altı başlık da arama motoruna metin olarak geçiyor.
- **Kalem sayısı 4 → 6** (`SON_DAKIKA_ADET`): şerit dördünü sırayla
  gösteriyordu, kutu altısını aynı anda gösteriyor.
- Kutu üç rayın da **en üstünde**: anasayfa, haber detay, köşe yazısı.
  Detay sayfalarında 300x250 panonun bile üstünde — son dakika rayın ilk
  kalemi olmalı.
- Zaman sütunu `kisa_zaman` filtresiyle: **bugünse saat, değilse tarih**.
  Ham `H:i` yanlıştı — arşivde farklı günlere ait kayıtlar var ve hepsi
  saat olarak basılınca liste sırasız görünüyordu (13:52 · 15:27 · 11:29
  alt alta). Sütun 64 px: `kisa_zaman`ın en uzun çıktısı "31 Eki 2025".
- Başlıktaki nabız atan nokta `prefers-reduced-motion`'da **sabit** kalır,
  kaybolmaz.
- Mega menüdeki "Son dakika" bağlantısı `#son-dakika` → **`/#son-dakika`**:
  kutu yalnız ray taşıyan sayfalarda var, çapa artık her sayfadan
  anasayfadaki kutuya gidiyor.

**Kapsam kaybı (bilinçli, kabul edildi):** kategori · ilçe · yazar dizini ·
galeri gibi **rayı olmayan sayfalarda son dakika artık görünmüyor**. Eskiden
şerit `taban.html`de olduğu için her sayfadaydı. Ray o sayfalara açılırsa
kutu oraya da girer.

---

### Doğrulama

Başsız Chrome, 2560 · 1920 · 1600 · 1480 · 1360 · 1280 · 1180 · 1100 · 1020 ·
900 · 504 px: her genişlikte yatay taşma yok (`scrollWidth == innerWidth`),
bant kenardan kenara (logo sol=0, MENÜ sağ kenarda), masaüstünde 10 kalemin
onu da görünür, bant tek satır. 1200 px kaydırılmış sayfada yan ray ile bant
çakışmıyor. **587 test geçiyor.**

### Açık kalan — karar bekliyor

**Şerit/kutu panelin son dakika kayıtlarını hâlâ okumuyor.**
`icerik/models.py` `SonDakika` docstring'i "bant önce bu tabloya bakar,
boşsa en yeni haberlere düşer" diyor ama `icerik/baglam.py` doğrudan
`Haber.yayindakiler()[:6]` veriyor; `SonDakika.bandakiler()` yalnız panelde
çağrılıyor. Yani sayfa sekreteri panelden son dakika girse bile siteye
çıkmıyor — kutuda "en son yayımlanan altı haber" duruyor. Bu tur kapsam
dışında bırakıldı, kullanıcıya soruldu, cevap beklemede.


---

## §37 — anasayfa üst blok yeniden sıralandı (30 Ağustos 2026)

Kullanıcı isteği: "günün manşetlerini daha aşağı koy, onun yerine son
dakikayı getir, son dakika'nın yanına da bir reklam panosu daha koy".

### Yeni sıra

| Önce | Sonra |
|---|---|
| piyasa · dörtlü · **manşet** · GÜNÜN MANŞETLERİ | piyasa · dörtlü · **manşet** · **SON DAKİKA + pano** |
| yazarlar · SON HABERLER+ray · resmî ilanlar | yazarlar · SON HABERLER+ray · **GÜNÜN MANŞETLERİ** · resmî ilanlar |

GÜNÜN MANŞETLERİ, SON HABERLER ızgarasının altına indi. Orada iki büyük
bloğun (haber ızgarası ↔ resmî ilanlar) arasında ayraç işi de görüyor;
`.ust-blok`tan çıktı.

### SON DAKİKA satırı

- `.sondakika-satir`: iki sütun — liste **784 px** + pano **300 px**
  (1100 px'lik orta sütunda ölçüldü).
- Pano **envanterden**: `-Manşet altı1- 300x250`. Yuva gerçekten manşetin
  altındaki 300x250 alan; ad uydurulmadı (`ReklamYuvasi` dökümünde var).
- Kutu panoyla **aynı boya çekiliyor** (`align-items:stretch`, gövde
  `flex:1` ve liste dikeyde ortalı): 6 kalem iki sütunda ~180 px sürüyor,
  yoksa panonun 250 px'i yanında beyaz kutunun altında 70 px boşluk kalırdı.
  Ölçüldü: ikisi de 250 px.
- Liste anasayfada **iki sütun** (`genis` bayrağı); raylarda tek sütun.
  Aynı parça iki yerleşimi de karşılıyor.
- **Anasayfada kutu raydan kalktı.** `id="son-dakika"` sayfada tek olmak
  zorunda; ölçüldü: 1 tane. Ray sürümü haber detay ve köşe yazısı
  sayfalarında duruyor.
- Dar ekran (≤1000 px): tek sütun, pano listenin **altına** geçer ve
  ortalanır — 300 px sabit sütun 360 px'lik ekranda listeye 40 px bırakırdı.
  ≤768 px'te liste de tek sütuna iner.
- `.ust-blok` dar ekran sırası güncellendi: manşet 1 · **son dakika 2** ·
  dörtlü 3 (eskiden 2. sıra GÜNÜN MANŞETLERİ idi).

### Doğrulama

Başsız Chrome 1600 · 1200 · 900 · 504 px: yatay taşma yok, `#son-dakika`
sayfada tek, masaüstünde liste ve pano eşit boyda (250 px), 900 px altında
pano listenin altına geçiyor. **598 test geçiyor.**


---

## §38 — SON DAKİKA paneli yeniden tasarlandı (30 Ağustos 2026)

Kullanıcı isteği: "son dakika panelinin tasarımını değiştir ve daha dikkat
çekici hale getir".

### Sorun

Panel beyaz `.kutu` + kırmızı `.kutu-bas.vurgu` idi — yani EN ÇOK OKUNANLAR,
BURSASPOR ve sayfadaki öbür bütün kutularla **aynı kalıp**. Göz onu bir uyarı
olarak değil sıradan bir liste olarak okuyordu. Ayrıca altı başlık eşit
puntodaydı; "en yenisi hangisi" sorusu gözle cevaplanamıyordu.

### Üç hamle

1. **Kendi sahası.** Panel bütünüyle koyu kırmızı zemine alındı. Sayfadaki
   tek dolu-renk blok o; manşetin hemen altında duruyor ve gri/beyaz ritmi
   kesiyor.
2. **Hiyerarşi.** İlk kalem manşet ağırlığında (`li.bas` — geniş yerleşimde
   22 px display 900, iki sütunu birden kaplar), kalan beşi 14 px.
3. **CANLI pili.** Nabız atan noktalı beyaz pil. `prefers-reduced-motion`'da
   nabız durur, pil ve nokta **görünür kalır**.

### Ölçülen kontrastlar (`:root` --sd-*)

| Katman | Değer | Beyaz üstünde |
|---|---|---|
| Saha `--sd-zemin` | #B8161E | **6,62:1** |
| Zaman `--sd-saat` | #FFD9A8 | 4,96:1 (saha üstünde) |
| CANLI pili | beyaz zemin, --sd-zemin yazı | 6,62:1 |

Düz `--kirmizi` üstünde beyaz **4,61** ölçülüyor ve 11-13 px yazı için
sınırda kalıyor (`.ihbar-bag` ile aynı gerekçe) — saha bu yüzden koyu tonda,
başlık şeridi parlak tonda.

**Odak halkası panelin içinde BEYAZA çevrildi.** Sitenin varsayılan halkası
`--kirmizi` ve kırmızı sahada görünmez olurdu. Kaldırma.

**Liste `columns` değil `grid`:** manşet kalemi iki sütunu birden kaplasın
diye (çok sütunda `column-span` güvenilir değil). Satır akışı DOM sırasını
izler, odak sırası görsel sırayla aynı kalır.

**SIRA ÖNEMLİ:** blok `.kutu` ve `.kutu-bas` tanımlarının **altında** durmak
zorunda. Yukarıda dururken `.kutu`nun beyaz zemini kazandı ve beyaz yazı
beyaz üstünde kayboldu — ekran görüntüsünde yakalandı, dosyada aşağı taşındı.

### Bu turda yaşanan kaza ve kurtarma

Panel stilini yazarken `site.css` **indeks dilimleyerek** düzenlendi; ikinci
işaretin dosyanın 250. satırında olduğu varsayıldı, gerçekte 1466'daydı.
**Aradaki ~1200 satır silindi** (dosya 1450 → 491 satır). Kurtarma:

- Git yalnız 723 satırlık HEAD'i tutuyordu; §34/§35 turlarının CSS'i hiç
  commit edilmemişti.
- Tam kopya **Claude Code'un dosya geçmişinde** bulundu
  (`~/.claude/file-history`, 30 Ağustos 00:11, 1329 satır).
- Dosya o tabandan yeniden kuruldu: taban + hava paneli turu + bu oturumun
  §36/§37/§38 düzenlemeleri. Sonuç 1664 satır, bitişik yinelenen seçici 0,
  süslü parantezler dengeli.
- Doğrulama: şablonlarda geçen 224 sınıfın karşılıksız kalanları yalnız
  JS/işaret amaçlı olanlar (`.ray`, `.ses-*`, `.yazdir` …) — kurtarma
  öncesiyle **aynı liste**. 2560·1600·1280·1100·900·504 px'te hava paneli,
  yazar kuşağı, resmî ilan dizini, günün manşetleri ve en çok okunanlar
  yerinde; yatay taşma yok. **605 test geçiyor.**

**Ders (kurala geçti):** CSS/şablon dosyaları indeksle dilimlenmez. Düzenleme
tam metin eşleşmesiyle ve `assert` ile yapılır; işaretin satır numarası
varsayılmaz, önce ölçülür.

### §38 eki — panel sütunları manşet alanıyla hizalandı

Kullanıcı isteği: "son dakika panelini manşet alanının genişliğiyle aynı yap,
aradaki boşluklar eşleşsin".

`.sondakika-satir` kendi ölçüsünü kullanıyordu (sağ sütun 300 px, boşluk
16 px); `.manset-alani` ise 320 px / 18 px. Panel manşetin tam altında
durduğu için sütun kenarları üst üste binmiyordu. Ölçü artık manşetten
kopyalanıyor:

| | Manşet alanı | Son dakika satırı |
|---|---|---|
| Sağ sütun | 320 px | **320 px** |
| Boşluk | 18 px | **18 px** |
| ≤1140 px | 300 px | **300 px** |

**Kırılma noktası dosyada nereye konacağı önemliydi:** 1140 kuralı önce
`.manset-alani`nin yanına yazıldı ama o blok dosyada çok önce geçiyor ve
satırın taban kuralı onu eziyordu — 1082 px'te sütun kenarları **20 px**
kayıyordu (ölçüldü). Kural `.sondakika-satir` tanımlarının hemen ardına
alındı.

**Doğrulama (başsız Chrome):** 1582 · 1123 · 1122 · 1064 px'te sol sütunun
sağ kenarı ve sağ sütunun sol kenarı **birebir aynı** (fark 0), boşluk iki
blokta da 18 px. 605 test geçiyor.

≤1000 px'te ikisi de tek sütuna iniyor ve dış genişlikleri eşit; iç düzen
farklı kalıyor — manşetin sağ sütununda pano ile mini galeri yan yana
diziliyor, son dakikada tek pano var ve ortalanıyor.

### §38 eki 2 — ilk kalem de ikili sütuna girdi

Kullanıcı isteği: "ilk haber tüm satırı kaplıyor sonra ikili sütunlara
ayrılıyor, bu ilk satırı da iki sütun yap".

`grid-column:1/-1` kalktı: altı kalem de ikili sütunda, **üç eşit satır**.
Vurgu duruyor ama yarım sütuna sığacak ölçüde — ilk kalem **22 → 17 px**
(komşusu 14 px, fark hâlâ okunuyor).

Kaplayan hâlden kalan iki artık temizlendi, ikisi de ölçümle görüldü:
- `padding-top:4px` komşusuyla eşitlendi (`9px 0`) — yoksa aynı satırdaki
  iki başlığın üst hizası **5 px** kayıyordu.
- Parlak ayraç (`--sd-bas-cizgi`) normale döndü; sağ hücrede karşılığı
  olmayan bir çizgi bırakıyordu.
- `:last-child` yerine `:nth-last-child(-n+2)`: ikili sütunda son SATIR iki
  kalemdir, alt kenar düz bitsin. Altı kalem üç tam satır yapıyor —
  `SON_DAKIKA_ADET` tek sayıya çekilirse bu kural yeniden ölçülmeli.

**Doğrulama:** 1582 px'te iki sütun da 352 px, üç satırın kalemleri aynı
hizada (üst=1180 · 1238 · 1295), son satırda ayraç 0. Panel ve pano yine
250 px. 605 test geçiyor.


## §39 — beyan notları panellerden çıkıp kendi sayfasına taşındı (31 Ağustos 2026)

Kullanıcı isteği: "veri kaynağı ve kapsam yazılarını kaldır panellerden,
onun yerine onu bir sayfa yap ve künyeye yerleştir."

§34 K7'de "yeniden açılacaksa kullanıcı kararı" diye bırakılan madde budur.

### Ne yapıldı

- Anasayfadaki **dokuz** `details.yer-not` bloğu (yazarlar · en çok okunan ·
  resmî ilan · şehir servisleri · puan durumu · Bursaspor · galeriler ·
  videolar · vizyon) kaldırıldı.
- `/veri-kaynaklari` açıldı: `icerik.views.veri_kaynaklari` +
  `sablonlar/veri_kaynaklari.html`. Adres **tek dilimli**, o yüzden kök
  adres tablosunda kategori kalıbından önce duruyor.
- Künyeye iki bağlantı: KURUMSAL listesinde "Veri kaynakları ve kapsam",
  telif satırının sonunda "Bölüm bölüm veri kaynağı ve kapsam →".
- Notların işaret ettiği dört bölüme çapa kimliği verildi (`#yazar-serit`,
  `#en-cok-okunan`, `#galeriler`, `#videolar`); diğer beşinde zaten vardı.
  Sayfadaki her başlık ilgili panele bağlanıyor.

### İki kural

1. **Metinler yeniden yazılmadı.** Paneldeki cümle ne diyorsa sayfada da
   aynısını diyor. Beyan "temizlenirse" okura verilen söz değişir.
2. **Sayılar veriden okunur.** `arsiv_sayilari()`, ilan dağılımı, puan ve
   vizyon künyeleri görünümden geliyor — §34'ün "bağlam değişkenlerine
   bağlı, o yüzden taşınamaz" gerekçesi böyle çözüldü.

### Sayfaya eklenen tek yeni şey: canlı veri künye tablosu

Yedi canlı kalem (döviz · piyasa · hava · namaz · eczane · puan · vizyon)
için kaynak adı, adresi, kullanım koşulları bağlantısı ve son güncelleme
damgası. **Tablo veriden üretilir**: künye bilgisi `canli-veri/veri/
<bileşen>.json` içindeki `kaynak` bloğundan okunur, koda ikinci bir kopya
yazılmadı.

Ölçümde bir kusur çıktı ve düzeltildi: `adres` alanı her zaman tek URL
değil — vizyon takvimi iki dağıtımcıdan besleniyor ve alan iki adresi
ayraçla taşıyor; `kosullar` alanı kimi kalemde adres değil düz cümle.
Alanı olduğu gibi `href`e koymak `href="http://a · https://b"` gibi kırık
bir bağlantı üretiyordu. `_baglar()` artık alanı boşluklara bölüp yalnız
`http` ile başlayan parçaları alıyor; tek adres varsa kaynağın adı
bağlantı olur, birden çoksa adresler alan adıyla ayrı ayrı basılır.

### Resmî ilan uyarısı nereye gitti

Bölümün altındaki uzun uyarı ("açık ilanların listesi değil", "son başvuru
tarihi gösterilmez") panelden kalktı ama **iki yerde duruyor**: beyan
sayfasında ve ilanın kendi sayfasında (`/resmi-ilan`, kendi metniyle).
Bölüm başlığındaki dönem etiketi ve TÜM İLANLAR bağlantısı yerinde.
`test_bolum_acik_ilan_listesi_gibi_gorunmuyor` bu üçünü birden kilitliyor.

### Doğrulama

- **618 test geçiyor.** `ArsivSayilariSablonaGomulmuyor` yeni adrese
  bakıyor; `test_notlar_anasayfadan_kalkti` anasayfada tek bir kopya
  kalmadığını ve künyenin sayfaya bağladığını kilitliyor; sabit sayı
  taraması artık iki şablonu birden geziyor.
- **Başsız Chrome, beş genişlik (360 · 768 · 1024 · 1280 · 1600):** yatay
  taşma **0**, `h1` sayısı 1, CSS yüklendi (zemin ve 58 yüz doğrulandı).
- İlk ölçümde tablo bağlantıları 14-17 px yüksekliğindeydi (§34 K6'nın
  24 px dokunma hedefinin altında); negatif kenar boşluğu tekniğiyle
  görünüm değişmeden büyütüldü, **ikinci ölçümde 24 px altı hedef yok**.
## §40 — nöbetçi eczane paneli işlevsel hâle getirildi (31 Ağustos 2026)

Kullanıcı isteği: "nöbetçi eczane panelini işlevsel hale getir."

Panel bir **özet** idi: `nobetci-eczane.json` içindeki 34 eczanenin ilk
üçünü basıyor, kalan otuz bire ulaşmanın hiçbir yolunu vermiyordu. Okur
o listeye gece yarısı bakıyor ve dört şey soruyor — hangisi benim
ilçemde, telefonu ne, nasıl giderim, kaça kadar açık. Dördünün de yanıtı
dosyada **zaten** duruyordu (ad, ilçe, açık adres, telefon, enlem/boylam,
nöbet başlangıç/bitiş); eksik olan tek şey sunumdu. Yeni bir kaynağa,
ücretli servise ya da dış pakete gidilmedi.

### Ne yapıldı

- `icerik/canli.py` → **`eczane_paneli()`**. Dosyayı şablonun basabileceği
  düz yapıya çevirir: satırlar ilçe sonra ad sırasında (Türkçe alfabeyle),
  ilçe süzgeci için ana ilçe + adet, en yaygın nöbet penceresi, şu an
  nöbeti sürenlerin sayısı. Bağlam anahtarı `eczane_panel`; ham `eczane`
  paketi de duruyor (hava panelindeki düzenin aynısı).
- Anasayfada panel yeniden yazıldı: **listenin tamamı** basılıyor, her
  satırda ad, ilçe, kendi nöbet saati, açık adres, `tel:` bağlantısı ve
  konum bağlantısı var. Liste kendi içinde kayıyor (430 px), namaz
  paneliyle aynı satırı paylaşmaya devam ediyor.
- `site.js` → ilçe seçimi ve serbest arama (ad, mahalle, sokak, telefon)
  birlikte süzüyor; eşleşme yoksa liste sessizce boşalmıyor, "eşleşen
  nöbetçi eczane yok" yazıyor.

### Üç karar

1. **Nöbet saati satırın kendisinde.** Ölçüldü (31 Ağustos, 34 eczane):
   **sekiz ayrı pencere** var, biri 20:00'de kapanıyor. Tek bir
   "18:30-08:30" cümlesi basmak okuru kapalı kapıya gönderirdi. Başlıktaki
   aralık en yaygın olanıdır ve kaç eczanenin ona uyduğu yazılır.
2. **Süzgeç ana ilçede birleşir.** Kaynak "OSMANGAZİ - DEMİRTAŞ",
   "NİLÜFER - ÇALI", "MUDANYA - GÜZELYALI" diye ayrı nöbet bölgeleri
   veriyor (20 etiket); okur için bunlar Osmangazi, Nilüfer, Mudanya —
   süzgeçte 17 ilçe var, satırda tam ad duruyor.
3. **Kaynakta olmayan alan bağlantıya dönmez.** Telefonu ya da koordinatı
   boş gelen eczane o düğme olmadan basılır. Konum bağlantısı dış bir
   adrestir ama bir *kaynak* değil: sayfa internetsiz de eksiksiz açılır,
   koordinat BEO'nun kendi sayfasından gelir, tahmin edilmez.

Süzgeç kutuları şablonda `hidden` geliyor, `site.js` açıyor: betik
yüklenmezse okur çalışmayan bir denetim görmez, liste zaten tam basılı.
Resmî ilan süzgecindeki ilkenin aynısı — süzgeç bir ilerleme, bir
bağımlılık değil.

### Ölçüm bir kusur buldu

`.ara` **bandın arama formunun sınıfı** ve 1000 px altında `display:none`
alıyor. Telefon bağlantısına aynı adı verdiğim için bağlantı dar ekranda
tamamen kayboluyordu — yani tam da telefonla aranacak ekranda. Başsız
Chrome ölçümünde görüldü (`telefon_gorunur: 0`), sınıf `.telefon` oldu.

### Doğrulama

- **Başsız Chrome, altı genişlik (360 · 700 · 768 · 1024 · 1280 · 1600):**
  34 satır, 34 telefon ve 34 konum bağlantısı her genişlikte görünür.
  Süzgeç ölçüldü: Nilüfer 6, "osmangazi" araması 7, eşleşmeyen arama boş
  durum yazısı, kutu temizlenince 34.
- **Gerçek Tab tuşuyla** gezildi: telefon ve konum bağlantıları odak
  sırasında, odak halkası `solid 3px` kırmızı (§32.5'in dersi).
- `icerik.tests_canli` içinde `EczanePaneli` (11 test) ve
  `EczanePaneliSayfada` (2 test): liste kırpılmıyor, ilçe ana ilçede
  birleşiyor, Türkçe sıralama, iki telefon biçimi de `tel:` oluyor, boş
  alan bağlantıya dönmüyor, her satır kendi saatini taşıyor, "şu an
  nöbette" işareti saate bağlı.

### Bu turda dokunulmayan bir bulgu

Anasayfada **360 px'te 9 px yatay taşma** ölçüldü. Kaynağı eczane paneli
değil: taşan kutu `.hava-foto` (§39 turunda giren Ulu Cami fotoğrafı,
360 px'lik ekranda 420 px çiziliyor). Panel işiyle ilgisi olmadığı için
düzeltilmedi, kayda geçirildi. 420 px ve üstünde taşma 0.

618 test geçiyor.
## §41 — nöbetçi eczane: kalıcı servis sayfaları + günlük haber (31 Ağustos 2026)

Kullanıcı isteği: "her gün için bursada nöbetçi eczaneler, bursa osmangazi
nöbetçi eczane gibi google seo'da aratılma değeri yüksek aramalar için
sitede otomatik haber oluştur ve o günün nöbetçi eczanelerini yaz."

**§sonraki-iş notundaki "servis modüllerine ayrı SEO sayfası üretmeyi
önerme" maddesi bu kararla kapandı.** O madde bir *öneri yasağıydı*
(22 Ağustos araştırması: hizmet içeriğinin organik trafiği düşüyor);
kullanıcı doğrudan istediğinde geçerliliği biter.

### Yapı: iki katman, biri ötekinin yerine geçmiyor

Kullanıcıya şu teknik gözlem sunuldu ve iki seçenek soruldu: "bursa
nöbetçi eczane" **her gün aynı sorgudur**, arama motoru böyle sorgularda
tek bir güncel adresi sıralar; her gün yeni haber açmak birbirinin
neredeyse aynısı yüzlerce sayfa üretir (yılda ~365, ilçe başına açılırsa
~6.200) ve bunlar birbiriyle yarışır. Kullanıcı **"sabit sayfa + günlük
haber"** ve **"17 ilçe sayfası + 1 günlük haber"** seçeneklerini seçti.

**Katman 1 — kalıcı sayfalar (asıl SEO hedefi).** `/nobetci-eczane` ve
17 ilçe adresi (`/nobetci-eczane/osmangazi` …). Adres değişmez, içerik her
gün kendini tazeler. `views.nobetci_eczane` → `sablonlar/nobetci_eczane.html`.

**Katman 2 — günlük haber.** `manage.py eczane_haberi` her sabah bir
`Haber` kaydı açar: tarihli sorgular ("31 ağustos nöbetçi eczane"),
gazetenin kendi akışı, RSS ve sitemap'in `news_YYYY-MM.xml` dosyası.
Gövdesi okuru **güncel** liste için kalıcı sayfalara yollar.

Metin tek yerden çıkıyor: `icerik/eczane.py`. Sayfanın başlığı, haberin
başlığı, ilçe adı çözümü ve kaynak cümlesi orada. İki ayrı yerde yazsalardı
biri güncellenip öteki unuturdu.

### Kararlar

1. **Adres kalıcıysa 404 verilmez.** Çekme betiği bir tur kaçırdığında
   sayfa yine 200 döner ve "liste şu an alınamıyor" der. 404, arama
   motoruna kayıtlı sayfayı dizinden düşürür. Bilinmeyen ilçe slug'ı ise
   gerçekten yoktur — o 404.
2. **"Bu ilçede bugün nöbetçi yok" da veridir.** Küçük ilçelerde nöbet
   komşuya devredilebiliyor; kaynak kayıt döndürmediyse sayfa bunu yazar
   ve il geneline yönlendirir. Boş kutu bırakmak okura sayfanın bozuk
   olduğunu düşündürürdü.
3. **Şerit 17 ilçenin tamamını taşır**, yalnız bugün nöbetçisi olanları
   değil; nöbetçisi olmayan ilçe "0" ile görünür.
4. **Günde tek kayıt.** Komutun ölçütü haberin slug'ı ve slug **günden**
   türer, başlıktan değil (`31-agustos-2026-bursa-nobetci-eczaneler`):
   başlık kalıbını değiştirdiğimiz gün slug da değişseydi komut aynı günün
   haberini bulamayıp ikinci kayıt açardı. Tazelemede yayın zamanı korunur.
5. **Bayat liste yayımlanmaz.** Nöbet günde bir devrediliyor; bir gün eski
   liste okuru kapalı eczaneye gönderir. `--bayat-da-yayimla` kapıyı elle
   açar.
6. **Haberin ilçe alanı boş.** Liste il geneli; ilçe alanı doldurulsaydı
   ilçe haber sayfaları her gün bir eczane kaydıyla dolardı.
7. **Kaynak türü "Dış yayın"**, meta yazar ondan türüyor (§7). Metin
   gazetenin muhabirinden değil, odanın çizelgesinden geliyor.

### Yapısal veri

Sayfa `ItemList` + `Pharmacy` JSON-LD basıyor (sitede ilk JSON-LD). Kural
aynı: **yalnız dosyada olan alan yazılır**. Telefonu olmayan eczanede
`telephone`, koordinatı olmayanda `geo` anahtarı hiç açılmaz. Nöbet
aralığı `openingHoursSpecification` ile veriliyor — haftalık düzen değil,
o güne ait tek aralık.

### Zamanlama

`tazele.ps1`e dördüncü grup eklendi: `-Grup haber` önce
`nobetci_eczane.py` ile listeyi tazeler, **sonra** `manage.py
eczane_haberi` çalıştırır. Sıra bağlayıcı; tersi dünün listesini yayımlar.
Görev Zamanlayıcı'ya `BH eczane haberi` kaydı açıldı (günde bir, 08:20).

### Ölçüm bir kusur buldu

İlçe şeridi `sorted(adlar.items(), key=…ad)` ile diziliyordu ve **İnegöl
ile İznik şeridin en sonuna** düşüyordu — §40'ta `canli._tr_sirala` ile
çözülen Türkçe sıralama tuzağının aynısı, ekran görüntüsünde görüldü.
İkinci kusur yapısal verideydi: `"ECZANESİ".title()` → "Eczanesi̇"
(harfin üstünde birleşen nokta). İkisi de düzeltildi; ad artık `baslikla`
süzgecinden geçiyor.

### Doğrulama

- **641 test geçiyor** (23 yeni: `icerik/tests_eczane.py`). Kilitlenen
  davranışlar: veri yokken 200, bilinmeyen ilçe 404, nöbetçisiz ilçe
  cümlesi, şeridin Türkçe sırası, olmayan alanın yapısal veriye
  yazılmaması, günde tek kayıt, bayat listenin yayımlanmaması.
- **Başsız Chrome:** `/nobetci-eczane` 1280 px'te yatay taşma 0, 34 kart,
  34 telefon bağlantısı, JSON-LD var; 360 px'te de taşma 0.
- **Uçtan uca koşuldu:** `tazele.ps1 -Grup haber` listeyi çekti ve haberi
  yayımladı → `/saglik/31-agustos-2026-bursa-nobetci-eczaneler-1529286`.
  İkinci koşu ikinci kayıt açmadı, var olanı tazeledi.

### Karar bekleyen iki kalem

- **SON DAKİKA rayı** en yeni altı haberi listeliyor (`baglam.py`), yani
  günlük eczane kaydı her sabah o rayın tepesine oturuyor. "Son dakika"
  bir servis listesi için doğru sözcük değil; dışlamak tek satırlık iş
  ama **editoryal karar**, kullanıcıya soruldu.
- **Kalıcı sayfalar sitemap'te değil.** Sitemap üreticisi canlı sitenin
  beş ailesini birebir taklit ediyor ve `site_haritasi_karsilastir` bu
  eşitliği denetliyor (F8); yeni bir aile eklemek o karşılaştırmayı bozar.
  Sayfalar şimdilik iç bağlantılarla keşfediliyor: mega menü, künye,
  anasayfa paneli ve günlük haberin gövdesi. Günlük haber zaten
  `news_YYYY-MM.xml` içinde.
## §42 — namaz paneli fotoğrafı değişti (31 Ağustos 2026)

Kullanıcı isteği: "görsel çok kötü yerleştirilmiş… sadece görseli değiştir."
(Aynı mesajdaki ikinci istek — namaz ve nöbetçi eczane panellerinin aynı
noktada bitmesi — ölçüldüğünde **zaten sağlanıyordu**: 768 px ve üstünde
iki kutunun alt kenarı arasındaki fark 0. Kullanıcı görünümü onaylayıp
yalnız fotoğrafı istedi, yerleşime dokunulmadı.)

### Sorun kırpmada değil, kaynaktaydı

Şeritteki `yesil.jpg` minarenin **şerefesine** öyle yakın bir kareydi ki
külah da kaide de kaynağın kendisinde yoktu; karenin yaklaşık üçte ikisi
boş gökyüzüydü. 530×186'lık yassı şeride girince geriye tanınmaz bir
sütun kalıyordu. `object-position` ile kurtarılamazdı — hiçbir kırpma
kadrajda olmayan külahı geri getiremez.

### Ne yapıldı

`gorseller/genis/yesil-cami.jpg` indirildi (Commons, **Dosseman, CC BY-SA
4.0**, 1280×852): Yeşil Cami uzaktan — iki minare, kubbeler, arkada kent
ve tepeler. Alt üçte biri ağaçlarla koyu, yani karartma perdesinin ve
"ŞİMDİ" satırının oturduğu bant zaten karanlık.

`yesil.jpg` **silinmedi**: "yeşil alan, park" kategorisinin temsilî
görseli olarak kullanılmaya devam ediyor. Yeni dosya 16:9 değil (Commons
küçültme servisi kırpmıyor, ortamda görüntü kütüphanesi yok); şerit
`object-fit:cover` kullandığı için sorun değil, `KAYNAKLAR.md`ye yazıldı.

Kadraj yeniden ölçüldü: `object-position` **%70 → %38**. Eski değer yeni
fotoğrafta kadrajı ağaçlara indiriyor, camiyi şeridin dışına atıyordu.

### Ölçüm (site.css'in kendi kuralı: fotoğraf değişirse kontrast yeniden ölçülür)

Yedi genişlikte (360 · 560 · 700 · 880 · 1024 · 1280 · 1600), yazı katmanı
gizlenip şerit çekilerek her satırın kutusundaki **en açık** piksel alındı.
PNG saf Python'la çözüldü — ortamda Pillow yok, kurulmadı.

| Satır | En kötü ölçüm | Eşik |
|---|---|---|
| `ŞİMDİ` etiketi | 8,78:1 | 4,5 |
| Vakit adı | 6,61:1 | 4,5 |
| Saat | 6,39:1 | 4,5 |

Künye kutucuğunun **en açık piksel** ölçümü yanıltıcı çıkıyor (1,0-1,75):
kutucuğun `border-radius`'u yüzünden köşe pikselleri arkadaki gökyüzünü
gösteriyor. Ortalama ışık 0,077-0,121, yani beyaz yazıyla 6,1-8,3:1 —
aynı turda paralel oturumun `--vk-hak-zemin`i %42'den %72'ye çekerken
ölçtüğü 7,93:1 ile örtüşüyor. Künye CC BY-SA'nın şartı; okunmuyorsa atıf
verilmemiş sayılır.

**641 test geçiyor**, 360 ve 420 px'te yatay taşma 0.


## §40 — Bursaspor "SON GELİŞMELER" listesi dörde indi (31 Ağustos 2026)

Kullanıcı isteği: "bursaspor panelindeki son gelişmeleri 4 satırla sınırla."

`BURSASPOR_LISTE` 7 → **4**. Bölümün toplam kaydı 6 + 7 = 13'ten 6 + 4 = 10'a
iniyor; kart sayısı (`BURSASPOR = 6`) ve puan tablosu değişmedi.

**Sayı artık sütun dengesinden değil karardan geliyor.** §32'de liste iki
sütunun boyunu eşitlemek için ölçülerek 9'dan 7'ye çekilmişti; o gerekçe
bu kararla yerini kullanıcı tercihine bıraktı. Denge yine de ölçüldü ve
işareti değişti (başsız Chrome, 1280 ve 1600 px — ikisinde de aynı):

| | sol sütun (puan) | sağ sütun (kart + liste) | fark |
|---|---|---|---|
| 7 satır (önce) | 794 px | 850 px (534 + 302 + boşluk) | sağ **+56** |
| 4 satır (sonra) | 794 px | 728 px (534 + 180 + boşluk) | sağ **−67** |

Fark aynı büyüklük sınıfında kaldığı için yerleşim düzeltmesi yapılmadı;
bölümün toplam boyu 921 → 865 px. Sayı bir daha oynatılırsa bu ölçüm
yenilenmeli. 641 test geçiyor.


## §41 — kategori bandının içeriği siteyle aynı raya oturdu (31 Ağustos 2026)

Kullanıcı isteği: "kategorilerin olduğu bantın kendisi ekranı kaplamaya
devam etsin ama içerikleri biraz daha daralt."

§36'da iç kutuya **bilerek** genişlik kapağı konmamıştı (bkz. yukarıdaki
madde 2). İstek onun tersini söylüyor ve zemin `.kategori` üzerinde
durduğu için **tam ekran kalmaya devam ediyor** — daralan yalnız içerik.

### Ölçü neden 1480

Sitenin kendi rayı: servis şeridi (`.servis-ic`), sayfa ızgarası
(`.sayfa`) ve künye (`.kunye-ic`) zaten bu ölçüde. Bant tek başına
kenardan kenara gidiyordu, yani geniş ekranda **hemen üstündeki servis
şeridiyle hizasızdı** — §36'nın kendi sorun tanımı ("1920 px'lik ekranda
iki şerit üst üste ama farklı genişlikte") eski düzen için yazılmıştı,
kapak kalkınca aynı kusur ters yönden geri gelmişti.

Daha dar yapılmadı ve bu **ölçüye dayanıyor**: bandın tek satırda kalma
bütçesi ~1350 px (logo 155 + 10 kalem 863 + arama 220 + MENÜ 88), ve arama
kutusunu simgeye indiren `@media` **görüntü** genişliğine bakıyor, iç
kutuya değil. Kapak 1360'ın altına inerse 1600 px'lik ekranda medya kuralı
devreye girmez ve bant ikinci satıra düşer.

### Mega levha da aynı raya

MENÜ düğmesi artık 1480'in iç kenarında; levha kenardan kenara kalsaydı
sütunlar bandın kalemleriyle hizasını kaybederdi. `.tam-menu-ic` de
kapatıldı — levhanın **zemini** yine tam ekran, içindeki beş sütun bantla
hizalı. `grid-template-columns` bloğun **son** bildirimi olarak bırakıldı:
`tests_menu` beş sütun sözleşmesini o bildirimden `}`ye kadar okuyup
sayıyor, arkasına bildirim eklenirse sayım bozuluyor (bir kez bozuldu).

### Doğrulama (başsız Chrome, 1024 · 1280 · 1400 · 1520 · 1600 · 1900 · 2560)

- Zemin her genişlikte **0 → ekran sonu**; bant boyu 50 px, yani hiçbir
  genişlikte ikinci satıra düşmüyor. Yatay taşma 0.
- İç kutu ile servis şeridi **birebir aynı** (sol ve sağ kenar, fark 0):
  1520'de 13→1493, 1900'de 203→1683, 2560'ta 533→2013.
- Menü açıkken levhanın zemini 0→1885, sütunları 203→1683 — bantla hizalı.
- 1480'in altında hiçbir şey değişmiyor (kapak devreye girmiyor).
- 641 test geçiyor.


## §42 — reklam yuvalarına Google demo ağı bağlandı (31 Ağustos 2026)

Kullanıcı isteği: "demo ağını bağla, 1100x150'yi de 970x250'ye çek."

**Bu F7(b) DEĞİL.** Gelir sunumu değil, yuvaların gerçek bir reklamla nasıl
durduğunu görmek için bir önizleme. Gerçek sunum yuva modelinden render,
kampanya eşleşmesi ve ads.txt ister; F7 hâlâ açılmadı.

### Neye bağlandı

Google Ad Manager'ın **açık demo ağı**: `/6355419/Travel/Europe/France/Paris`,
Google Publisher Tag ile. Hesap, anahtar, `ca-pub-` kimliği gerekmiyor.

**Varsayılan KAPALI** (`settings.REKLAM_DEMO`, `BH_REKLAM_DEMO=1` ile açılır).
Gerekçe: GPT dış bir betiktir ve üçüncü taraf çerezi bırakır; site şu an
dışarıdan yalnız Google Fonts çekiyor ve internetsiz açılabiliyor. Bayrak
kapalıyken `taban.html` tek satır dış betik basmaz. Canlıda açılacaksa KVKK
tarafında çerez aydınlatması **ayrı bir iştir**.

### Hangi ölçü doluyor — ölçüldü, varsayılmadı

Başsız Chrome ile canlı demo ağına karşı:

| Ölçü | Demo ağı |
|---|---|
| 300×250 · 160×600 · 728×90 | **doluyor** |
| 970×250 · 300×600 · 320×100 | boş döner |

970×250 dört ayrı örnek yuvada da (`/Travel`, `/Travel/Europe`, `…/France`,
`…/Paris`) boş döndü. Çözüm **çok ölçülü tanım**: üst şerit `970x250` +
`728x90` ister, demo ağı 728×90 ile doldurur, gerçek reklamverende ikisi de
geçerli ölçüdür.

### 1100×150 → 970×250 → **1100×150** (aynı gün geri alındı)

1100×150 IAB standardı değil ve hiçbir ağ o ölçüde yaratıcı taşımıyor;
970×250 ("billboard") standart. Kutu tam genişlikte kalıyor (1100 px),
yaratıcı ortalanıyor; kutu boyu 150 → **250 px**.

**Envanter etkisi:** `1100x150` bir yuva ADIYDI (F1 ölçütü 3, "5/5 yuva adı
envanterden"). Bu değişiklik o yuvayı yeniden adlandırıyor — F7 açıldığında
reklam sisteminde de karşılığı düzeltilmeli, yoksa şablon ile envanter
ayrışır.

### Ölçerek bulunan kusur: mobilde 393 px yatay taşma

İlk uygulamada 360 px'te sayfa **393 px yatay taşıyordu**. Sebep: üst şerit
kutusu ≤600 px'te **44 px**'lik bir şerit (§34 K8'in bilinçli kararı — mobilde
ilk editoryal piksel aşağı inmesin diye) ve 728×90'lık yaratıcı oraya
sığmıyor.

Çözüm **görünüm haritası** (`data-gpt-harita`, GPT `defineSizeMapping`):

    1024>970x250,728x90 ;  601>728x90 ;  0>

Dar ekranda ölçü listesi **boş** — yuvaya hiçbir şey basılmaz, gri yer
tutucu kalır. Ayrıca son emniyet ağı olarak `.reklam{overflow:hidden}`
kondu: haritadaki bir hata sayfanın tamamını yatay kaydırılır hâle
getirmesin.

### Uygulama kararları

- **Ölçü işarettedir, betikte değil.** Şablonda `.reklam[data-gpt="300x250"]`
  duruyor; `reklam.js` sayfada ne bulursa onu tanımlar. Yuva nerede duruyorsa
  ölçüsü de orada yazar.
- **"Reklamları gizle" anahtarına uyar.** Anahtar açıkken hiçbir slot
  tanımlanmaz; yoksa panolar gizliyken reklam yine de çekilirdi.
- **Görünmeyen yuva çekilmez.** Yan pageskin'ler yalnız ≥1480 px'te çiziliyor;
  `offsetParent === null` olan atlanır — görünmeyen reklam için istek atmak
  gerçek sunumda geçersiz gösterim sayılır.
- **Boş yuva daraltılmaz** (`collapseEmptyDivs(false)`): kutu yüksekliği
  yerleşimin parçası, daraltmak sayfayı reklam gelince zıplatırdı. Yer tutucu
  ile reklam aynı ızgara hücresinde duruyor, yükleme sırasında kutu
  yerinden oynamıyor.

### Doğrulama

- **646 test geçiyor** (5 yeni: bayrak kapalı/açık, yuva işaretleri,
  dar ekran haritası, anahtar uyumu).
- Başsız Chrome, anasayfa ve haber detay, 1600 · 1280 · 360 px: **yatay
  taşma 0**. 1600'de altı yuvanın beşi doluyor.
- Bilinen demo ağı davranışı: aynı sayfada iki 160×600 istendiğinde
  **biri boş dönüyor** (sağ pageskin). Kod tarafında kusur değil —
  `slotRenderEnded` `isEmpty:true` ile geliyor, yani istek gitti ve ağ
  yaratıcı vermedi. Gerçek reklamverende ikisi de dolar.


### §42 eki — üst şerit 1100×150'ye döndü (aynı gün)

Kullanıcı: "1100'e 150 bulamaz mıyız."

**Hiçbir reklam ağında yok** ve bu ölçüldü: Google demo ağı 970×250, 970×90,
728×250, 336×280, 300×600 ve 320×100'ün hepsini boş dönüyor; dolduğu üç ölçü
300×250, 160×600 ve 728×90. Dört ayrı örnek yuvada aynı sonuç.

**Ama bu ölçü programatik talep için değil.** 1100×150 gazetenin **kendi
sattığı** yuvanın ölçüsü — envanterdeki adı da zaten "1100x150" — ve özel
ölçüler Ad Manager'da doğrudan satışta serbesttir. Yerel reklamveren
1100×150 görseli verir, yuva dolar. Dolayısıyla doğru cevap "bulunamaz"
değil, **"programatik ağdan gelmez, kendi kampanyandan gelir"**.

Şerit `1100x150` + `728x90` ister: yuva satılmadığında programatik talep
(ve demo ağı) 728×90 ile doldurur, 150 px'lik kutuda ortalanır. Kutu boyu
250 → **150 px**'e döndü.

**970×250 düştü** — 250 px'lik yaratıcı 150 px'lik kutuya sığmaz. Billboard
formatının programatik gelirini isteyen olursa kutu 250'ye çıkarılmalı; bu
bir **gelir kararı**, yerleşim kararı değil.

Bunun yan etkisi olarak §42'de yazılan **envanter uyarısı düştü**: yuva adı
`1100x150` yerinde kaldı, F1 ölçütü 3 ("5/5 yuva adı envanterden") bozulmadı.

**Görünüm haritası** ikinci bir ölçülmüş kısıt kazandı:

    1140>1100x150,728x90 ;  601>728x90 ;  0>

601-1139 bandında 1100×150 **verilmez**: içerik sütunu 1100 px'e ancak
~1120 px görüntüde ulaşıyor, daha darında 1100 genişliğindeki yaratıcı
taşardı. Eşik mevcut 1140 kırılma noktasına oturtuldu.

**Doğrulama (1600 · 1280 · 1100 · 800 · 360 px):** yatay taşma **0**; kutu
1100×150, demo yaratıcısı 728×90 ortada; 800'de kutu 120 px ve 728×90 hâlâ
sığıyor; 360'ta yaratıcı istenmiyor, gri yer tutucu kalıyor. 646 test
geçiyor.


### §42 eki 2 — üst şerit iki ölçüyü birden taşıyor (aynı gün)

Kullanıcı: "970e 250'yi getir." Bir önceki ekte "billboard'un programatik
gelirini isteyen olursa kutu 250'ye çıkarılmalı, bu bir gelir kararı" diye
açık bırakılan madde budur; karar geldi.

Şerit artık **üç ölçü** ister ve üçünün gerekçesi ayrı:

| Ölçü | Ne için | Nereden dolar |
|---|---|---|
| **1100×150** | gazetenin kendi sattığı yuva (envanterdeki ad) | doğrudan satış |
| **970×250** | IAB billboard | programatik talep |
| **728×90** | yedek, şerit boş kalmasın | programatik + demo ağı |

Kutu boyu 150 → **250 px** (billboard için). Bedeli: 1100×150 dolduğunda alt
ve üstte 50'şer px boşluk kalıyor. Tek ölçüye inilirse kutu boyu da ona göre
ayarlanmalı.

Görünüm haritası **dört kademe** oldu; her eşik ölçülmüş bir kısıt:

    1140>1100x150,970x250,728x90 ;  1001>970x250,728x90 ;  601>728x90 ;  0>

- **≤600** kutu 44 px (§34 K8) — hiçbir ölçü; 728×90 oraya konunca sayfa
  360'ta 393 px yatay taşıyordu.
- **601-1000** kutu 120 px — 250'lik yaratıcı sığmaz.
- **1001-1139** kutu 250 px ama içerik sütunu ~981-1119 px — 970 sığar,
  1100 sığmaz.

**Doğrulama (1600 · 1280 · 1100 · 800 · 360 px):** yatay taşma **0**. Kutu
1100×250 / 1065×250 / 765×120 / 325×44; demo ağı üçünden yalnız 728×90'ı
doldurduğu için görünen yaratıcı her genişlikte o. 646 test geçiyor —
haritanın dört kademesi de teste bağlandı.


### §42 eki 3 — üst şerit demo reklamı almıyor (aynı gün)

Kullanıcı: "970'e 250'nin içine test reklamı koyma şimdilik."

Gerekçe yerinde: demo ağı üç ölçüden yalnız **728×90**'ı dolduruyor ve o
yaratıcı 250 px'lik billboard kutusunun ortasında küçücük duruyordu —
şeridin gerçek hâlini göstermek yerine yanıltıyordu. Şerit şimdilik gri yer
tutucu olarak duruyor.

**Kalkan tek şey demo dolgusu.** `data-gpt` ve `data-gpt-harita`
SİLİNMEDİ; yeni `data-gpt-demo="kapali"` işaretini yalnız `reklam.js`
okuyor, o da yalnız demo bayrağıyla yükleniyor. Gerçek sunum (F7)
geldiğinde bu şerit için yeniden ölçü yazılması gerekmeyecek.

**Doğrulama:** 1600 px'te üst şerit boş (1100×250 gri kutu), diğer beş
yuvanın dördü demo reklamıyla dolu — iki 160×600'ün biri demo ağının kendi
davranışı gereği boş. Yatay taşma 0. 647 test geçiyor; işaretin **yalnız**
üst şeritte olduğu da kilitlendi (kareler ve pageskin'ler demo almaya
devam ediyor).


### §42 eki 4 — 970×250'nin ayak izi maketle gösteriliyor (aynı gün)

Kullanıcı: "970'e 250'yi görmek istiyorum."

Demo ağında o ölçüde yaratıcı **yok** (ölçüldü, üç kez: ağ yalnız 300×250,
160×600 ve 728×90 dolduruyor). Ağın vermediği bir şeyi ağın vermiş gibi
göstermek yerine **kutunun kendisi çizildi**: şeridin ortasında tam
970×250, üzerinde "ÖRNEK YARATICI · 970 × 250 — billboard ayak izi" yazıyor.

**Sahte reklam değil:** reklamveren adı, marka, görsel yok — yalnız formatın
ayak izi. Yalnız `BH_REKLAM_DEMO=1` iken basılır; yayında blok şablondan
hiç çıkmaz ve bu teste bağlandı (okur onu reklam sanmasın).

Maket üst şeridin demo dolgusunun yerine geçmiyor — şerit hâlâ ağdan
reklam almıyor (`data-gpt-demo="kapali"`, eki 3). Ölçü sözleşmesi de
yerinde: `data-gpt` üç ölçüyü taşımaya devam ediyor.

### Ölçerken çıkan iki kusur

1. **Maket dar ekranda küçülmüyordu.** `.reklam` ızgarasının sütunu `auto`
   idi; 970 px'lik blok max-content sayılıyor, `max-width:100%` de %100'ü
   970 kabul ediyordu. Sonuç: blok küçülmüyor, `overflow:hidden` onu
   kırpıyordu. Sütun `minmax(0,1fr)` yapıldı.
2. **44 px'lik şeritte billboard ayak izi bilgi vermiyor.** Maket artık
   yalnız kutunun 250 px olduğu genişlikte (>1000 px) çiziliyor; altında
   normal gri yer tutucu geri geliyor.

**Doğrulama (1600 · 1280 · 1100 · 800 · 360 px):** maket 970×250 olarak
1600/1280/1100'de görünüyor (1100'de kutu 1065, maket yine tam ölçüsünde
sığıyor), 800 ve 360'ta gizli ve yer tutucu geri geliyor. Yatay taşma
**0**, diğer beş yuva demo reklamı almaya devam ediyor. 648 test geçiyor.

