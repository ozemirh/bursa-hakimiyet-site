---
name: taslak-denetimi
description: Yapay zekâ editör aracının ürettiği haber taslaklarını kaynakla karşılaştırıp editoryal kurallara karşı denetler, alan sözleşmesinin altı dosya arasındaki hizasını kontrol eder ve yapay-zeka-editor.html sayfasına yeni örnek gömer. arac/cikti/*.json paketleri incelenirken, SEMA/SISTEM/kural motoru değiştiğinde ve editöre örnek eklenirken kullan.
---

# Taslak denetimi

Editör aracının ürettiği taslak, editör onayı olmadan yayına girmez. Bu skill o onaydan
önceki mekanik katmanı yapar: model kurallara uydu mu, alan sözleşmesi hizada mı, örnek
sayfaya doğru gömüldü mü.

Üç mod var. İstekten hangisi olduğunu anla, yalnızca onu çalıştır.

| Tetikleyici | Mod |
|---|---|
| `arac/cikti/*.json` denetlensin, "bu taslak yayına uygun mu" | **1 — Taslak denetimi** |
| `SEMA` / `SISTEM` / `kural_motoru.py` / `motor.js` değişti, alan eklendi | **2 — Alan sözleşmesi hizası** |
| Editöre yeni örnek eklenecek | **3 — Örnek gömme** |

## İki motor var

Paketi kimin ürettiğini bilmeden denetleme:

- **Model yolu** — [`haber_taslak.py`](../../../arac/haber_taslak.py), Claude çağırır, her alanı doldurur.
  İki sağlayıcısı var: `claude` (API anahtarıyla) ve `cli` (anahtarsız, yerel `claude` komutu —
  [`yz_cli.py`](../../../arac/yz_cli.py)). İkisi de `uretim.saglayici` alanında görünür ve
  betikte **model** hâline düşer, yani tam denetime girer. Model yolu K1'i çiğneyebilir:
  ilk `cli` denemesinde kaynakla üç ayrı 8 kelimelik örtüşme çıktı. Bu yolun çıktısını
  denetimden geçirmeden yayına önerme.
- **Skill zinciri** — `--saglayici skill` ([`yz_skill.py`](../../../arac/yz_skill.py)) bu modun
  1. adımını makineleştirir: model üretir, `denetim.py` çıktıyı denetler, bulgu varsa modele
  geri verilip düzelttirilir. `uretim.turlar` kaç tur döndüğünü, `uretim.kalan_bulgular`
  kapanmayan bulguyu taşır. Bu paketlerde önce o iki alana bak: zincir zaten denemişse
  aynı bulguyu tekrar raporlamak yerine neden kapanmadığını yaz.
- **Kural yolu** — [`kural_motoru.py`](../../../arac/kural_motoru.py) (ve tarayıcı ikizi `motor.js`), model
  kullanmaz. Kategori, ilçe, etiket, önem, uyarıları sözlükle doldurur; **başlık, spot,
  üç madde ve gövdeyi kasıtlı boş bırakır** ve kaynağın ham cümlelerini ayrı bir `tezgah`
  listesinde editörün yanına koyar.

Kural paketindeki boş alan ihlal değil, tasarım. Ayırt edici alan `uretim.saglayici`.

---

## Mod 1 — Taslak denetimi

### Adım 1 — Betiği çalıştır

    python arac/denetim.py "arac/cikti/*.json"

[`arac/denetim.py`](../../../arac/denetim.py) paketin halini kendi bulur ve ona göre denetler:

| Hal | Ne demek | Ne denetlenir |
|---|---|---|
| `model` | `haber_taslak.py` üretmiş | Tam denetim |
| `kural-bos` | Kural iskeleti, henüz yazılmamış | İskelet doğru mu, dil alanları atlanır |
| `kural-dolu` | İskeleti editör doldurmuş | Tam denetim |

Çıkış kodu: `0` temiz, `2` bulgu var. Betik dosyayı **değiştirmez**.

Betiğin mekanikleştirdiği kurallar: **K1** (kopyalama — kaynakla 8 kelimelik birebir
örtüşme; `alinti` blokları muaf, paragraf içindeki tırnaklı **aralık** metinden düşülür ve
kalanı denetlenir), **K3** (`kaynak_atfi` dolu mu — 23 Ağustos 2026'dan beri gövdede geçmesi
aranmıyor, kaynak yayınlanan sayfada ayrı bölmede gösteriliyor),
**K4** (kesin hüküm dili, `hassas_konu` işaretli mi), **K5** (uyarı boş mu), **K6**
(tıklama tuzağı), **K7** (zorla yerelleştirme), artı bütün alan sınırları.

### Adım 2 — Elle kalan: K2

**Uydurma olgu kontrolü mekanikleştirilemez, betik bunu yapmaz.** `taslak` içindeki her
özel ismi, rakamı, tarihi, kurumu, unvanı, ölü/yaralı sayısını `kaynak.orijinal_govde`
ile karşılaştır. Kaynakta yoksa iki ihtimal var: ya ihlaldir, ya `dogrulanmasi_gerekenler`
listesinde karşılığı vardır. İkincisi de değilse bulgu yaz.

`kaynak.ayiklama_guveni` `dusuk` ise raporun başına şunu yaz: *kaynak eksik ayıklanmış
olabilir, "kaynakta yok" bulguları elle doğrulanmalı.* Betik bu uyarıyı zaten basar.

### Adım 3 — Tezgah riski

`kural-dolu` paketlerde **K1'e ayrı dikkat et.** Tezgah paneli kaynağın ham cümlelerini
editörün yazma alanının hemen yanına koyuyor; kopyala-yapıştır buradaki en gerçekçi
kaza — üstelik tezgahın en yüksek puanlı cümleleri alıntı taşıyanlardır, yani tırnak
muafiyetinin en çok işlediği yerdir. Betik yakalar, ama bulgu çıkarsa bunu editöre "motor hatası" diye değil, "tezgahtan
cümle taşınmış" diye rapor et — düzeltmesi farklıdır.

### Adım 4 — Rapor

Betiğin çıktısını olduğu gibi yapıştırma; her bulgu için kanıtı kaynaktan çıkar:

    K1 · govde[0] · Kaynakla birebir ortusen cumle
         taslak: "Nilüfer Belediyesi, 2026 yılında ihale süreçleri tamamlanan..."
         kaynak: "Nilüfer Belediyesi, 2026 yılında ihale süreçleri tamamlanan..."

Sonunda tek satır hüküm: **yayına uygun** / **düzeltilmeli** / **elle kaynağa bakılmalı**.

**Rapor düzeltme değildir.** İçeriği kendiliğinden değiştirme — `CLAUDE.md` gerçek haber
içeriğinin uydurma bilgiyle değiştirilmesini yasaklıyor. Karakter sınırı aşımı ve bozuk
slug gibi mekanik şeyleri ancak kullanıcı isterse düzelt; olgu ve cümle düzeltmesi her
zaman kullanıcıya sorulur.

---

## Mod 2 — Alan sözleşmesi hizası

Bir alan **altı yerde** tanımlıdır. Biri güncellenip diğeri unutulursa sayfa sessizce boş
alan gösterir:

| Yer | Ne tutar |
|---|---|
| `arac/haber_taslak.py` → `SEMA` | `properties` + `required` (sözleşmenin aslı) |
| `arac/haber_taslak.py` → `SISTEM` → ALAN KURALLARI | alanın yazım kuralı |
| `arac/kural_motoru.py` → `taslak_uret_kural()` | kural yolunun ürettiği karşılık |
| `arac/motor.js` | aynı motorun tarayıcı ikizi |
| `yapay-zeka-editor.html` | `t.<alan>` render kodu + `ORNEKLER` paketleri |
| `arac/README.md` → "Üretilen alanlar" | tablo satırı |

Hizayı çıkarmak için:

    python arac/hiza.py     # 0 hizali, 2 bosluk var

[`arac/hiza.py`](../../../arac/hiza.py) altı yerin hepsine bakar: `SEMA` içindeki
`required`/`properties` tutarlılığı, `SISTEM` alan kuralı, sayfadaki `t.<alan>` render
kodu, **her** `ORNEKLER` paketi ve `README` tablosu. İki motoru grep'lemez, **çalıştırır**
— `kural_motoru.py` ve `motor.js` verilen kaynakla üretim yapar, ürettikleri anahtarlar
şemayla karşılaştırılır. Metin araması alan adı yorumda geçtiğinde yanılıyordu.

Boş liste hizanın tam olduğu anlamına gelir. Ters yön (HTML'de okunup şemada olmayan alan)
bilerek kontrol edilmiyor: `t.` öneki sayfada DOM çağrıları için de kullanılıyor
(`t.add`, `t.class`) ve liste kullanılamayacak kadar gürültülü çıkıyor.

### Gömülü blok da senkron olmalı

`sozluk.json`, `konular.json`, `arsiv.json` veya `motor.js` değiştiyse HTML içindeki
üretilmiş blok eskimiştir:

    python arac/gomulu_uret.py --kontrol    # 0 guncel, 2 eskimis
    python arac/gomulu_uret.py              # yazar

### İki motor da aynı sonucu vermeli

`gomulu_uret.py --kontrol` gömülü bloğun **taze** olup olmadığına bakar; iki motorun aynı
çıktıyı verip vermediğine bakmaz. `kural_motoru.py` ya da `motor.js` değiştiyse:

    python arac/parite.py    # 0 ayni, 2 sapma

Aynı kaynağı iki motora verir ve sonucu diffler (`uretim.zaman` hariç). Node gerekir;
yoksa hata verir — atlanan parite testi yok hükmündedir. Sapma çıkarsa **`kural_motoru.py`
esastır**, `motor.js` ona göre düzeltilir; düzelttikten sonra `gomulu_uret.py` çalıştır.

### Çelişki çıkarsa

Aynı alan iki yerde farklı tarif ediliyorsa **`README` esastır**; `SISTEM` ve `SEMA` ona
göre düzeltilir. (22 Ağustos 2026'da `etiketler` adedi bu kuralla 3-8'de birleştirildi.)

### Alan eklerken

Altısını da aynı düzenlemede yap: `SEMA.properties` + `SEMA.required` → `SISTEM` ALAN
KURALLARI → `kural_motoru.py` → `motor.js` → HTML render + **her** `ORNEKLER` paketi →
`README` tablosu. Sonra `gomulu_uret.py` çalıştır. Şema `additionalProperties: False`
olduğu için `required` listesine girmiş ama üretilmeyen alan doğrudan hataya düşer.

---

## Mod 3 — Örnek gömme

`yapay-zeka-editor.html` bağımsız açılabilir olmalı; örnekler dosyaya gömülüdür.

1. Paketi al: `arac/cikti/<slug>.json`.
2. **Mod 1'i çalıştır.** Denetimden geçmeyen taslak sayfaya gömülmez.
3. İki yeri `grep` ile bul — **satır numarasına güvenme**, sayfa büyüdükçe kayıyor:

       grep -n "const ORNEKLER = {" yapay-zeka-editor.html    # paket bloğu
       grep -n "data-ornek=" yapay-zeka-editor.html           # çip düğmeleri

4. `const ORNEKLER = {` bloğuna slug anahtarıyla, mevcut girdilerin girinti düzeninde
   ekle. Bir önceki girdinin sonuna virgül koymayı unutma. Sonra çip düğmesini
   `data-ornek` satırlarının yanına ekle:
   `<button class="cip" type="button" data-ornek="<slug>">Konu · Kaynak</button>`
   Etiket, mevcutlarla aynı `Konu · Kaynak adı` biçiminde olsun.
5. Pakete `uretim.not` alanı ekle: taslağın temsili olduğunu, canlı üretilmediğini yaz.
   API anahtarı tanımlı olmadığı için depodaki taslakların hiçbiri canlı üretilmedi.
6. `python arac/hiza.py` çalıştır. Alan sözleşmesinin yanı sıra çip ↔ paket simetrisini
   ve **`kaynak_url` çakışmasını** da denetler: adres kutusu `Object.keys(...).find(...)`
   ile **ilk** eşleşen örneği yükler, yani aynı kaynaktan ikinci bir örnek eklersen o
   örnek yalnızca çipinden erişilebilir olur — sessizce. Ya farklı kaynaklı bir paket
   seç, ya da bunu bilerek kabul et.
7. Dosyayı tarayıcıda aç, yeni çipe tıkla, akış sonuna kadar çalışıyor mu bak: tezgah
   paneli açılıyor mu, alanlar doluyor mu, konsolda hata var mı.

**Üretilmiş bloğa dokunma.** `/* === ÜRETİLMİŞ BLOK ... === */` ile
`/* === ÜRETİLMİŞ BLOK SONU === */` arası `gomulu_uret.py` tarafından yazılıyor; oraya
elle yapılan her düzenleme bir sonraki çalıştırmada silinir. Sözlük, konu veya motor
değişikliği kaynak dosyalarda yapılır, sonra betik çalıştırılır.

Dosyanın geri kalanına dokunma — base64 logoyu, CSS'i, akış kodunu yeniden biçimlendirme.



---

## Her modda geçerli

- `SISTEM` içindeki yedi mutlak kuralı gevşetme; `CLAUDE.md` bunu açıkça yasaklıyor.
- Depodaki taslaklar temsilidir, canlı üretilmedi. Denetim raporunda modelin canlı
  davranışına dair genelleme yapma.
- `arac/` bağımlılıksızlık kuralının dışındadır, buraya Python yazmak serbesttir.
  Bu skill `tasarim-*.html` dosyalarına dokunmaz.
