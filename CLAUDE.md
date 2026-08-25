# CLAUDE.md — Bursa Hakimiyet Demo Tasarımları

Bu klasörde Bursa Hakimiyet haber sitesinin **üç tasarım prototipi** var. Amaç, yayın ekibine sunulacak demo sayfaları geliştirmek. Henüz gerçek uygulama yazılmıyor.

Ayrıntılı bilgi: `DEMO-NOTLARI.md`

---

## Bu klasörde ne var

| Dosya | Ne |
|---|---|
| `tasarim-1-klasik.html` | Ulusal haber sitelerinin yoğun bilgi mimarisi — anasayfa |
| `tasarim-1-haber-detay.html` | Aynı yönün haber detay sayfası |
| `tasarim-2-hibrit.html` | Klasik iskelet + modern tipografi — anasayfa |
| `tasarim-2-haber-detay.html` | Aynı yönün haber detay sayfası |
| `tasarim-3-modern.html` | Tipografi öncelikli, farklılaşmayı hedefleyen — anasayfa |
| `tasarim-3-haber-detay.html` | Aynı yönün haber detay sayfası |
| `gorseller/` | Demo fotoğrafları (`genis/` `kart/` `kare/`) + `KAYNAKLAR.md` |
| `logo-seffaf.png` | Şeffaf zeminli logo (dosyalara base64 gömülü) |
| `yapay-zeka-editor.html` | Haber masası aracı prototipi — kaynak ayıklama, alan doldurma, konu bağlama arayüzü |
| `arac/` | Aracın Python tarafı: `ayiklayici.py`, `haber_taslak.py`, `kural_motoru.py`, `konu_eslestirme.py`, veri dosyaları, `cikti/` |
| `.claude/agents/haber-sayfasi-gelistirici.md` | Bu tasarımlar üzerinde çalışan uzman ajan tanımı |

Her tasarım yönü kendi içinde **anasayfa + haber detay** çiftinden oluşuyor ve ikisi birbirine bağlı. Build adımı, npm paketi, framework yok — dosyalar çift tıkla açılır. Dışarıdan yalnızca Google Fonts gelir; fotoğraflar yereldir.

**Ajan kullanımı:** Tasarımlar üzerinde iş yaptırırken `haber-sayfasi-gelistirici` ajanını kullan. Her ajana **tek bir tasarım dosyası** ver — üçünü aynı anda tek ajana verme.

## Çalışma kuralları

**Bağımsızlık korunacak.** Bu dosyalar tek başına açılabilir olmalı. npm paketi, build aracı, framework ekleme. CSS aynı dosyanın `<style>` bloğunda, JS `<script>` bloğunda kalacak.

**Üçünü senkron tutma zorunluluğu yok.** Bunlar birbirinin alternatifi, aynı ürünün parçaları değil. Bir tasarımda yapılan değişikliği açıkça istenmedikçe diğerlerine taşıma.

**Sınıf adları Türkçe.** Mevcut kod `.kapsa`, `.manset`, `.kart`, `.bolum-bas` gibi Türkçe sınıf adları kullanıyor; bu düzeni bozma. İngilizce sınıf adı ekleme.

**Renkler CSS değişkeninden.** Doğrudan hex yazma; `var(--kirmizi)`, `var(--lacivert)` gibi tanımlı değişkenleri kullan. Yeni renk gerekiyorsa önce `:root` içine tanımla.

**Görseller yerel.** Demo fotoğrafları `gorseller/` klasöründe, göreli yolla çağrılıyor (`gorseller/kart/baraj.jpg`). Kaynak ve lisanslar `gorseller/KAYNAKLAR.md` içinde. SVG `<symbol>` kütüphanesi (`#sc-adliye`, `#sc-baraj`) duruyor ve fotoğrafı olmayan konularda kullanılmaya devam ediyor — silme. Dışarıdan görsel URL'si ekleme; internetsiz de açılabilmeli.

> Not: 22 Ağustos 2026'da alınan kararla demo sayfaları artık tek dosya değil — `gorseller/` klasörüyle birlikte taşınıyor. Kod bağımsızlığı (build yok, paket yok) aynen sürüyor.

**Seslendirme tarayıcının kendi motoruyla.** Haber detay sayfalarındaki sesli okuma (`#seslendirme`) Web Speech API ile çalışır: dış servis, API anahtarı, ses dosyası yok. Kullanıcıya sormadan bulut tabanlı bir TTS servisine geçirme. Ses sıralaması Natural/Neural/Online/Google adlı sesleri öne alır; `localService` tercihi bilerek kaldırıldı (Edge'de doğal sesi eleyip robotik sesi seçiyordu) — geri getirme. Betik üç detay sayfasında birebir aynıdır; birinde değiştirdiğini üçünde de değiştir. Okunacak öğeler `data-kaynak` seçicisinden gelir, cümle parçası sınırı (`EN_UZUN`) tarayıcıların 15 saniyelik kesme davranışı için vardır — büyütme.

**Erişilebilirlik.** Her etkileşimli öğede odak görünür olmalı, `aria-*` nitelikleri korunmalı, `prefers-reduced-motion` kuralları silinmemeli.

**Responsive.** Her değişiklikten sonra dar ekranda da kontrol et. Kırılma noktaları `DEMO-NOTLARI.md`de yazılı.

## Yapma

- Dosyaları "temizlemek" veya "modernize etmek" için yeniden yazma — istenen değişikliği yap, gerisine dokunma
- Tailwind, React, bundler önerme
- Başka haber sitelerinden fotoğraf veya başlık kopyalama
- İçerikteki gerçek haberleri uydurma bilgiyle değiştirme; yeni içerik gerekiyorsa bana sor
- Web3 / blockchain önerme (proje kapsamından çıkarıldı)

## Yapay zekâ editör aracı

`arac/` klasörü tasarım demolarından **ayrı bir parçadır** ve kendi kuralları vardır:

- Python ile yazılır. "Bağımlılıksız tek dosya" kuralı **buraya uygulanmaz**; o kural `tasarim-*.html` dosyaları içindir.
- **Dört sağlayıcı var.** Varsayılan `kural`: model kullanmaz, anahtar istemez, yalnızca standart kütüphaneye dayanır (`kural_motoru.py`). `--saglayici claude` mevcut yolu çalıştırır ve `anthropic` SDK'sını ister. `--saglayici cli` (23 Ağustos 2026'da eklendi, `yz_cli.py`) aynı işi **anahtarsız** yapar: makinede kurulu `claude` komutunu çağırır, kullanıcının kendi oturumunu kullanır. `--saglayici skill` (`yz_skill.py`) `cli` yolunu çalıştırıp çıktısını `denetim.py` ile denetler ve bulgu varsa modele düzelttirir — `taslak-denetimi` Mod 1 zincirinin makineleşmiş hâli. Hiçbirini silme, `kural` dışındakini varsayılan yapma.
- **Editör sayfasında üç yol seçilebilir:** A (kural motoru), B (skill zinciri: üret → denetle → düzelt), C (çıplak yapay zekâ). Üçü de aynı adresi kabul eder, karşılaştırma için. Sunucunun `yontem: "tarayici"` ucu da duruyor: taslağı `motor.js` kurar, `parite.py`nin doğruladığı eşitliği tarayıcıda göstermek için.
- Claude çağrıları `claude-opus-5` ile, yapılandırılmış çıktı (`output_config.format`) kullanarak yapılır. Model kimliğini kullanıcı istemeden değiştirme.
- Editoryal kurallar `haber_taslak.py` içindeki `SISTEM` metnindedir: kopyalama yok, uydurma olgu yok, kaynak her zaman belirtilir (23 Ağustos 2026'dan beri gövdede değil, yayınlanan sayfadaki ayrı **Kaynak bölmesinde**; haberi aldığımız sayfa kendi kaynağını belirtmişse — `ayiklayici.asil_kaynak_bul` "Kaynak:" satırını, parantezli ajans kodunu ve yazar alanını tarar — **kaynak odur**, aracı yayın kaynak diye anılmaz), masumiyet karinesi korunur. **Bu kuralları gevşetme.**
- **Kural motoru gövde yazmaz.** Başlık, spot, üç madde ve gövde bilerek boş gelir; kaynağın cümleleri yalnızca `tezgah` alanında "ham malzeme" olarak durur. Bu boşluğu kaynaktan cümle kopyalayarak doldurma — kuralın kendisi bu.
- **Konu takibi onaysız bağlamaz.** `konu_eslestirme.py` aday listeler ve gerekçe yazar; bağlama yalnızca `--konu <id>` ya da sayfadaki düğmeyle olur. Otomatik bağlama ekleme.
- Konu verisi `konular.json`, haber dizini `arsiv.json` dosyasındadır; `tasarim-3`'teki "Sürecin akışı" bloğu buradan üretilir. Konu/kronoloji tarafında araç tasarım dosyalarını düzenlemez — yapıştırılacak HTML üretir.
- **Yayın ayrı iştir.** 23 Ağustos 2026'da alınan kararla "Yayına gönder" düğmesi gerçekten yayınlıyor: `yayin.py` üç tasarımın haber detay sayfasını şablon alıp `haber-<slug>-t{1,2,3}.html` üretir ve üç anasayfaya birer kart ekler. Yazma işini `yayinci.py` (yalnız `127.0.0.1`) yapar; sunucu kapalıyken sayfa aynen çalışır. Şablonların geri kalanına — kenar sütunları, döviz bandı, ilgili haberler — dokunulmaz. Kaynağın fotoğrafı 23 Ağustos 2026'daki demo kararıyla **indirilip** `gorseller/kaynak/` altına yerelleştirilir ve `KAYNAKLAR.md`ye işlenir; uzaktan bağlanmaz, sayfalar internetsiz de açılmalı. Gerçek yayında hak durumu ayrıca doğrulanmalı. Boş taslak yayınlanmaz; başlık, spot ve en az iki paragraf şart. Kaynak bölmesi, etiketler ve manşet görseli üç şablonda da haberinkiyle değiştirilir.
- `sozluk.json` ve `motor.js` değiştiğinde `python arac/gomulu_uret.py` çalıştır; yoksa Python ve tarayıcı motorları ayrışır.
- `yapay-zeka-editor.html` demo sayfasıdır ve diğer HTML dosyaları gibi bağımlılıksızdır; motor, sözlük ve örnekler dosyaya gömülüdür.

## Değişiklik isteği geldiğinde

1. Hangi dosyada olduğunu netleştir (üçünde mi, birinde mi)
2. İlgili bölümü oku, sonra düzenle — tüm dosyayı yeniden yazma
3. Değişiklikten sonra kırılma noktalarında kontrol edilmesi gerekenleri söyle
