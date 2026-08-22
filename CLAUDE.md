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

**Erişilebilirlik.** Her etkileşimli öğede odak görünür olmalı, `aria-*` nitelikleri korunmalı, `prefers-reduced-motion` kuralları silinmemeli.

**Responsive.** Her değişiklikten sonra dar ekranda da kontrol et. Kırılma noktaları `DEMO-NOTLARI.md`de yazılı.

## Yapma

- Dosyaları "temizlemek" veya "modernize etmek" için yeniden yazma — istenen değişikliği yap, gerisine dokunma
- Tailwind, React, bundler önerme
- Başka haber sitelerinden fotoğraf veya başlık kopyalama
- İçerikteki gerçek haberleri uydurma bilgiyle değiştirme; yeni içerik gerekiyorsa bana sor
- Web3 / blockchain önerme (proje kapsamından çıkarıldı)

## Değişiklik isteği geldiğinde

1. Hangi dosyada olduğunu netleştir (üçünde mi, birinde mi)
2. İlgili bölümü oku, sonra düzenle — tüm dosyayı yeniden yazma
3. Değişiklikten sonra kırılma noktalarında kontrol edilmesi gerekenleri söyle
