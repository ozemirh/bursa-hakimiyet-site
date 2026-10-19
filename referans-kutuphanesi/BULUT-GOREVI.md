# Bulut görevi — kütüphaneyi doldur / tazele

Bu metin Claude Code bulut oturumuna (claude.ai/code) **olduğu gibi
yapıştırılır**. Elle tazeleme de aynı metinle yapılır; yalnız kip değişir.

## Oturumu açmadan önce (kullanıcı)

1. claude.ai/code → depo `ozemirh/bursa-hakimiyet-site` → dal
   `referans-kutuphanesi` (ya da birleştirildiyse `main`).
2. Ortam ayarında **ağ erişimi: tam** (ya da `SITELER.md`deki alan adlarına
   izin listesi). `curl` ve başsız Chrome için gerekli; WebSearch/WebFetch
   bundan bağımsız çalışır.
3. Aşağıdaki "Görev" bölümünü kopyala, ilk satırdaki kipi seç.

---

## Görev

KİP: ilk-tarama   (tazeleme için: KİP: tazele)

Sen bu depoda `haber-siteleri-arastirmacisi` ajanının koordinatörüsün.
Önce oku: `.claude/agents/haber-siteleri-arastirmacisi.md`,
`referans-kutuphanesi/README.md`, `referans-kutuphanesi/SITELER.md`, `EKIP.md`.

**1. Hazırlık.** Başsız Chromium kurulabiliyor mu dene (ör. `npx playwright
install chromium` ya da sistem paketi). Kurulursa başarım ölçümü yap, kurulmazsa
rubriğin 7. başlığı "ölçülmedi (bulutta Chrome yok)" kalır. Depoya hiçbir paket
dosyası (`package.json`, `node_modules`, `requirements`) ekleme.

**2. Paralel tarama — üç alt ajan, aynı anda.** `haber-siteleri-arastirmacisi`
ajan türünü kullan (kayıtlı değilse `general-purpose` + "önce
`.claude/agents/haber-siteleri-arastirmacisi.md` dosyasını oku ve ona göre
çalış"):

- Alt ajan **yerel**: `SITELER.md` Yerel tablosu. Önce "aday" satırlarını
  kesinleştir (gerekçe yaz), sonra her site için `siteler/<site>.md`.
- Alt ajan **ulusal**: Ulusal tablosu.
- Alt ajan **global**: Global tablosu.

Her alt ajan: README'deki rubrik ve şablon, kanıt kuralı, nazik tarama
sınırları. Ekran görüntüsü/ham HTML yalnız `referans-kutuphanesi/ham/`.
`SITELER.md`de kendi satırlarının "Son inceleme" sütununu doldurur.
`KİP: tazele` ise: site dosyasını baştan yazma; değişeni bul, ilgili başlığı
güncelle, başlığa "(güncellendi 2026-MM-GG)" ekle, değişmeyeni dokunma.

**3. Sentez — alt ajanlar bitince, tek geçiş.**
- `desenler/` altında en az şu konular: `anasayfa-mimarisi`, `bolum-sayfasi`,
  `haber-detay`, `son-dakika`, `yerel-servis`, `ekonomi-sayfasi`,
  `teknoloji-sayfasi`, `spor-kulup-sayfasi`, `basarim`, `seo-yapisi`,
  `reklam-yerlesimi`, `gelir-okur-iliskisi`, `erisilebilirlik`,
  `yapay-zeka-kullanimi`. Var olan desen dosyaları (tohumlar) silinmez,
  genişletilir.
- `karsilastirma.md`: her desen için Bursa Hakimiyet'in durumu. Bulutta
  geliştirme sunucusu ve veritabanı **yok** (veritabanı depoda değil); bizim
  tarafı `URUN-PLANI.md` (`grep -n '^## '`), `uygulama/sablonlar/`,
  `uygulama/statik/stil/site.css` üzerinden kanıtla. Canlı ölçüm gerekiyorsa
  "yerelde ölçülecek → test-kalite-muhendisi" yaz.
- Öneri sütunu EKIP.md'deki reddedilenlerle süzülür.

**4. Öz denetim.**
- Her `siteler/*.md` dosyasında rubriğin 12 başlığı var mı (dolu ya da
  "ölçülmedi")?
- Uzun alıntı taraması: kaynak sayfadan 25 kelimeden uzun ardışık metin yok.
- `git status`: `ham/` altından hiçbir dosya izlenmiyor; `referans-kutuphanesi/`
  dışında değişiklik yok.

**5. Teslim.** Tek commit ("Referans kütüphanesi: <kip>, <tarih>"), dalı it,
PR aç. PR açıklamasında: taranan/atlanan siteler (atlananın nedeni), bulutta
ölçülemeyenler, en önemli 5 P0/P1 öneri.

Ürün kodu, şablon, CSS, `URUN-PLANI.md`, `EKIP.md`, ajan tanımlarını
**değiştirme**.
