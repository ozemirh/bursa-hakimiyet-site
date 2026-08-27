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
│ban  │  LOGO — sol üstte, TEK BAŞINA                  │ban  │
│ner  │  ───────────────────────────────────────────   │ner  │
│     │  KATEGORİ BANDI (10 kalem, kalabalık değil)    │     │
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
| 2 | **Logo** | Sol üstte, **tek başına**. Yanında arama/abone kutusu yok — arama bandın içinde. |
| 3 | **Kategori bandı** | **Tam 10 kalem:** Yazarlar · Bursa · Bursaspor · Gündem · Ekonomi · Dünya · Spor · Magazin · İlçeler · Resmî İlan. Kalabalıklaştırma. **Arama ve menü düğmesi bandın içinde**, sağ uçta: önce arama, onun sağında menü düğmesi (26 Ağustos kararı). |
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
