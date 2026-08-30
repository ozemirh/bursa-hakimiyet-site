# ilan.gov.tr araştırması — resmî ilanları oradan çekebilir miyiz?

**30 Ağustos 2026.** Soru şuydu: pek çok site resmî ilanları ilan.gov.tr'den
çekiyor gibi görünüyor; biz de çekmeli miyiz?

**Kısa yanıt: teknik olarak çekebiliriz, ama sözleşme buna izin vermiyor.**
Yol açık ve belgelenmiş durumda; ancak Basın İlan Kurumu'nun kendi kullanım
koşulları otomatik veri çekmeyi açıkça yasaklıyor. Bizim için bu sıradan bir
site değil: resmî ilan hakkımızı veren kurum orası. Bu yüzden aşağıdaki
teknik yol **izin alınmadan işletilmemeli**.

---

## 1. Teknik durum — ne var, ne çalışıyor

ilan.gov.tr bir Angular tek-sayfa uygulaması; arkasında Kong üstünden
yayımlanan bir ASP.NET Boilerplate API'si var. **Swagger belgesi herkese
açık** ve uçların çoğu anonim çalışıyor.

| Ne | Nerede |
|---|---|
| Swagger tanımı | `https://www.ilan.gov.tr/api/swagger/v1/swagger.json` (58 uç) |
| API tabanı | `https://www.ilan.gov.tr/api/api/services/app/…` (yol **iki kez** `api` içerir; SPA yapılandırması böyle) |
| Zorunlu başlık | `X-Request-Origin: IGT-UI` — bu başlık olmadan bazı uçlar 403 döner |
| Anahtar / üyelik | **gerekmiyor** (aşağıdaki iki uç hariç) |

### Kullanılabilir uçlar

**İlan listesi (POST)** — `…/Ad/AdsByFilter`

```json
{"keys": {"aci": [30]}, "skipCount": 0, "maxResultCount": 20}
```

Yanıt ABP zarfı içinde (`{"result": {...}}`) gelir: `ads[]`, `numFound`,
ayrıca **yüz sayaçları** — `cityCounts` (81 ilin ilan adedi), `categories`,
`yearCounts`. Sayfa boyu **20 ile sınırlı**; daha büyük istense de 20 döner,
sayfalama `skipCount` ile.

**İlan detayı (GET)** — `…/AdDetail/GetAdDetail?id=<id>`
İlanın **tam metnini** (`content`, HTML), ilan sahibini, kategorileri, tür
alanlarını (satış günü, muhammen bedel, dosya no) ve **`publishes[]`** —
yani ilanı hangi gazetenin yayımladığını verir.

**İlçe listesi (GET)** — `…/AddressCounty/GetAll?AddressCityId=30`
Bursa'nın 18 kaydı (17 ilçe + Merkez), kimlikler 9250–9267.

### `keys` süzgeç anahtarları

SPA'nın adres çubuğundaki sorgu parametreleriyle birebir aynı. Tarayıcıda
süzgeç uygulanırken yakalandı:

| Anahtar | Ne | Örnek |
|---|---|---|
| `aci` | il kimliği | Bursa = **30** |
| `aco` | ilçe kimliği | Nilüfer = 9262 |
| `adi` | semt kimliği | |
| `ats` | ilan türü | 2=İCRA, 3=İHALE, 4=TEBLİGAT, 5=PERSONEL ALIMI |
| `txv` | kategori (tax) | 1=Emlak, 9=İhale Duyuruları … |
| `pub` | **yayın kodu** | Bursa Hakimiyet = `YYN-000132` |
| `paci` / `paco` | yayının ili / ilçesi | Bursa merkezli yayınlar = 30 |
| `adv` | ilan sahibi kodu | |
| `ppdmin` / `ppdmax` | yayın tarihi aralığı | |
| `q` / `t` / `c` | arama / başlık / metin | |
| `prmin` / `prmax` | bedel aralığı | |
| `ay` | yıl | |
| `s` | durum (arşiv/aktif) | |

### Bizim yayın kodlarımız

Bursa merkezli yayınların ilanları taranıp `publishes[]` alanından
çıkarıldı:

- **BURSA HAKİMİYET** (basılı gazete) → `YYN-000132`
- **www.bursahakimiyet.com.tr** (internet) → `INT-000046`

Bu, işin en önemli bulgusu: `pub=YYN-000132` **yalnızca bizim yayımladığımız
ilanları** döndürüyor. Anasayfadaki bölümün bugünkü iddiası da tam olarak bu
— "gazetenin **yayımladığı** resmî ilanların dizinidir, açık ilanların
listesi değil". Yani doğru besleme zaten bu uçta duruyor.

### Ölçülen sayılar (30 Ağustos 2026)

| Sorgu | Kayıt |
|---|---|
| Türkiye geneli açık ilan | 25.282 |
| Bursa (`aci=30`) | 951 |
| ├ İCRA | 362 |
| ├ TEBLİGAT | 510 |
| ├ İHALE | 76 |
| └ PERSONEL ALIMI | 2 |
| Bursa merkezli yayınların ilanları (`paci=30`) | 108 |
| **Bursa Hakimiyet basılı (`pub=YYN-000132`)** | **17** |
| **bursahakimiyet.com.tr (`pub=INT-000046`)** | **23** |

### Kapalı olan iki uç

`AddressCity/GetAll` ve `Publisher/GetAll` üyelik istiyor (403). İkisi de
gerekmiyor: il kimliği `cityCounts` yüzünden zaten geliyor, yayın kodu da
detay kaydından okunuyor.

### robots.txt ne diyor

```
User-agent: *
Disallow: Disallow: /*tebligat        <- bozuk yazılmış satır
Sitemap: https://www.ilan.gov.tr/sitemap/ads.xml
Sitemap: https://www.ilan.gov.tr/sitemap/daily-ads.xml
```

Tebligat sayfalarını dışlamak istemişler ama satır hatalı yazılmış. Dört
site haritası ilan ediliyor; hiçbiri açılmıyor (404). Yani robots.txt
tarama izni veriyor **gibi** duruyor — fakat asıl bağlayıcı metin bu değil.

---

## 2. Hukuki durum — asıl engel burada

**ilan.gov.tr Kullanım Koşulları, MADDE 5(10):**

> "…İlan Portalı üzerinde otomatik program, robot, örümcek, web crawler,
> veri madenciliği (data mining), veri taraması (data trawling) vb. *screen
> scraping* yazılımları veya sistemleri, otomatik aletler ya da manuel
> süreçler kullanılması… **hukuka aykırı olup**; Kurumun her tür talep, dava
> ve takip hakları saklıdır."

**MADDE 6(3):**

> "Kullanıcı, İlan Portalı dahilinde bulunan her türlü… metinleri…
> veritabanlarını, katalogları ve listeleri **çoğaltmayacağı,
> kopyalamayacağı, dağıtmayacağını, işlemeyeceğini**, bu tür eylemler
> gerçekleştirerek **herhangi bir ticari faaliyette bulunmayacağını**…
> kabul ve taahhüt etmektedir."

Ayrıca MADDE 6(1) portalın veritabanını Kurum'un telif hakkına tabi eser
sayıyor, MADDE 10 uyuşmazlıkta Bakırköy mahkemelerini yetkili kılıyor.

Bu maddeler yoruma pek yer bırakmıyor. API'nin anahtarsız açık olması izin
anlamına gelmiyor; robots.txt'nin izin verir görünmesi de sözleşmeyi
geçersiz kılmıyor.

**Ek risk:** Basın İlan Kurumu bizim düzenleyicimiz. Resmî ilan yayımlama
hakkı BİK kararıyla verilir ve **BİK kararıyla durdurulabilir** — bunun
uygulandığı örnekler kurumun kendi aylık listesinde yazılı (`ilanbis.bik.gov.tr/
Uygulamalar/AylikListe`, Ağrı Hakimiyet için 2 Temmuz 2026 tarihli durdurma
kararı orada duruyor). Yani buradaki risk "belki fark edilmez" değil, doğrudan
gelir kaynağımıza dokunan bir risk.

---

## 3. Öneri

**Kazıma yapılmamalı.** Bunun yerine, aynı veriye hakkımızla ulaşmanın
iki yolu var:

1. **ILANBIS.** `https://ilanbis.bik.gov.tr` — BİK'in yayıncılara açtığı
   sistem. Bursa Hakimiyet'in zaten hesabı var (resmî ilan alıyoruz);
   bize *tahsis edilen* ilanlar oradan geliyor. Site için doğru besleme bu:
   veri zaten bizim, yayımlama hakkı zaten bizde. Kontrol edilmesi gereken:
   ILANBIS dışa aktarma (XML/Excel/API) veriyor mu — bu, panelden bakılacak
   bir iş, dışarıdan görülemiyor.

2. **BİK'ten yazılı izin.** Yukarıdaki teknik yol hazır ve belgeli;
   `pub=YYN-000132` ile yalnız kendi ilanlarımızı çekiyor. Kuruma "kendi
   yayımladığımız ilanları kendi sitemize otomatik aktarmak için" izin
   başvurusu yapılabilir. Bu, MADDE 5(10)'un yasakladığı genel tarama
   değil, dar ve gerekçesi açık bir istek.

Bu ikisinden biri olmadan çekmeye başlamak, teknik olarak kolay olduğu için
cazip görünüyor ama bize maliyeti en yüksek yer burası.

### İzin gelirse ne yapılacak

Kod tarafı `canli-veri/` düzenine birebir oturuyor: bir çekme betiği
(`canli-veri/resmi_ilan.py`) `pub=YYN-000132` ve `INT-000046` sorgularını
koşar, yeni ilanların detayını çeker, `canli-veri/veri/resmi-ilan.json`
yazar; site yalnız okur. Günde bir çekim yeterli (17 + 23 kayıt, artış
günde birkaç ilan). Mevcut `icerik.Ilan` modeliyle eşleştirme ilan numarası
(`adNo`, ör. `ILN02535759`) üzerinden yapılır — bugün elimizdeki kayıtlarda
bulunmayan **son başvuru / satış tarihi** alanı da bu uçtan geliyor
(`adTypeFilters` içinde "Birinci Satış Günü", "Muhammen Bedeli", "Dosya No").

---

## 4. Ölçüm kayıtları

Bulgular 30 Ağustos 2026'da doğrudan istekle ve başsız Chrome'la (CDP ile
ağ trafiği dinlenerek) doğrulandı. `keys` sözlüğünün anahtar adları tahmin
edilmedi — süzgeç tarayıcıda uygulanıp giden POST gövdesi okundu, ayrıca
SPA'nın `81184-es2015.*.js` yığınındaki adres çözümleyicisinden tam liste
çıkarıldı.
