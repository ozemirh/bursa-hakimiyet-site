# Erişilebilirlik — siteler arası desenler

Son güncelleme: 2026-10-20 (sentez) · Kaynak siteler: Bursada Bugün, Bursa
Saati, Ege'de Son Söz, Özgür Kocaeli, Habertürk, Spiegel (doğrudan: HTML ve
DOM sayımı); BBC, Guardian (ikincil, depo README'leri). **Veri az:** odak
görünürlüğü ve kontrast hiçbir sitede ölçülmedi.

| Ölçüt | Görülen (2026-10-20, tek ölçüm) | Kaynak |
|---|---|---|
| "İçeriğe atla" bağlantısı | **Var:** Spiegel (odakta görünür). **Bulunamadı:** Bursada Bugün, Bursa Saati, Ege, Habertürk. Özgür Kocaeli: doğrulanmadı | `spiegel.md` §11 · [/ausland/](https://www.spiegel.de/ausland/); diğerleri §11 |
| İlk odaklanan öğe | metinsiz logo (Bursada Bugün), `javascript:void(0)` bağlantı (Bursa Saati), logo (Ege), WhatsApp ihbar (Özgür Kocaeli) | ilgili §11 |
| `lang` | hepsinde var (`tr` / `tr-TR` / `de`) | ilgili §11 |
| Görsel `alt` (anasayfa) | Bursada Bugün 182'nin 181'i eksik/boş; Özgür Kocaeli 289'un 12'si eksik; Bursa Saati 107'nin 1'i; Ege 110'un 0'ı; Habertürk detayda 41'in 0'ı | ilgili §11 |
| Kart görselinde boş `alt` + `article aria-label` | Spiegel: dekoratif görsel boş alt, kart adı `aria-label` ile | `spiegel.md` §11 |
| Başlık yapısı | Habertürk anasayfasında `h1` yok; detayda tek | `haberturk.md` §11 |
| Odak stili | Habertürk anasayfada ilk bağlantıda `outline: none` (programatik ölçüm; klavye `:focus-visible` ölçülmedi) | `haberturk.md` §11 |
| Punto denetimi | A−/A+: Bursada Bugün, Bursa Saati, Ege, Habertürk | ilgili §3 |
| Çerez bandı | Habertürk: "Tercih Et / Reddet / Kabul Et" eş ağırlıklı | `haberturk.md` §6 |
| Kurumsal ilke ve test | BBC Simorgh erişilebilirliği ilke koyuyor, cihazlar arası test kılavuzu; Guardian görsel regresyon (Chromatic) + Playwright | İ · `bbc-turkce.md` §11, `guardian.md` Özet 3 |

**Ortak ders.** Türk yerel sitelerinin hiçbirinde atla bağlantısı bulunamadı;
`alt` doluluğu aynı platformda bile değişiyor (yayıncının giriş disiplini).
Doğrudan ölçülen tek iyi örnek Spiegel: atla bağlantısı, `aria-hidden`
simgeler, kartta `aria-label`.

**Hangi koşulda.** `alt` doluluğu panelin alanı zorunlu kılmasına bağlı;
masa disiplini tek başına yetmiyor (Bursada Bugün ↔ Ege, aynı katman).

**Bursa Hakimiyet'te durum.**
- Atla bağlantısı var (`taban.html:70`, `site.css` 273–274; odakta görünür).
- `:focus-visible` 3 px `--tema-odak` halkası (`site.css` 253–254); tema
  kontrast sözleşmesinde odak ≥ 3:1, metin ≥ 4,5:1 testle denetleniyor
  (`icerik/temalar.py` `KONTRAST`, `tests_temalar.py`).
- Site ölçümü (11 sayfa × 8 genişlik): halkasız odak 0, `h1` 1, taşma 0
  (URUN-PLANI §70).
- `{% gorsel %}` etiketi dekoratif görsele açıkça boş `alt`, diğerine metin
  (`icerik/templatetags/gorsel_etiket.py`); arşivdeki anlamsız "Google News"
  alt metni okura basılmıyor (`haber_detay.html` 58–62).
- `prefers-reduced-motion` kuralları var (`site.css` 589, 1645); slayt
  hareket azaltılmışta dönmez, üzerine gelince/odakta durur. Duraklatma
  düğmesi **kullanıcı kararıyla kaldırıldı** (`statik/betik/site.js` 86–87).
- A−/A+ ve yazdır düğmesi detayda.

**Öneri.** Bu taramada BH'nin gerisinde kaldığı doğrudan bir desen
görülmedi. Kontrast ve klavye gezinmesi için karşılaştırma verisi yok →
açık soru. Panelde görsel alt metnini zorunlu tutmak (Bursada Bugün ↔ Ege
farkı) → P2 · S · → `full-stack-gelistirici` (panel formu) — mevcut durum
ölçülmedi, önce `test-kalite-muhendisi` yeni haberlerde `alt` doluluğunu saysın.

**Açık sorular — nasıl güçlenir.** Rakip sitelerde klavye ile gezinme ve
`:focus-visible` halkası, kontrast ölçümü (axe/Lighthouse tek tur, izinli
sitelerde) bir sonraki taramada yapılabilir.
