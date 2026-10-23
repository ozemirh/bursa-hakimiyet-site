# Teknoloji sayfası — siteler arası desenler

Son güncelleme: 2026-10-20 (sentez) · Açık iş: **özel tasarım, kategori 9**
(EKIP.md). **Veri az.** Odak listesindeki Guardian ve NYT otomatik erişime
kapalı, T24 erişim engelli; teknoloji bölümleri ölçülmedi. Doğrudan veri
yalnız Spiegel `/tests/` (tüketici/servis bölümü) ve Habertürk alt menüsünden.

| Site | K. | Çözüm | Kaynak |
|---|---|---|---|
| Spiegel `/tests/` | D | Alt kategori hapları → "yeni test edilenler" kümesi → **ürün kategorisine göre ~15 konu kümesi** (her biri 1 büyük + 3–6 küçük kart) → kronolojik liste + sayfalama. Küme içine **"ANZEIGE" (reklam) etiketli sponsorlu kart** yerleşmiş. 135 kart, 1,3 MB açılmış HTML | `siteler/spiegel.md` §2 · [/tests/](https://www.spiegel.de/tests/), 2026-10-20 |
| Habertürk | D | Teknolojiye yakın başlıklar ekonomi alt menüsünde: Elektrikli Araçlar, Girişimcilik, Otomobil | `siteler/haberturk.md` §2, 2026-10-20 |
| Guardian · NYT | — | Ölçülmedi (otomatik erişim yok) | `guardian.md` §2, `nyt.md` §2 |
| T24 | — | Ölçülmedi (erişim engelli) | `t24.md` |

**Ortak ders (sınırlı veri).** Spiegel teknolojiyi "haber akışı" değil
**ürün kategorisine göre kümelenmiş servis** olarak sunuyor; sponsorlu kart
içerik kartı biçiminde ama etiketli. Tek örnekten genel ders çıkarılmaz.

**Hangi koşulda işe yarıyor.** Ürün testi kümeleri test eden bir ekip ve
satış ortaklığı geliri ister; ulusal ölçek. Yerel gazeteye doğrudan taşınmaz.

**Bursa Hakimiyet'te durum.** Teknoloji teması kurulu (`icerik/temalar.py`,
`parca/bolum/teknoloji.html`, URUN-PLANI §70 Paket E): `bas` yuvasında
**BURSA'DA TEKNOLOJİ** listesi — bütün bölümlerden, Bursa'yı anan ve başlıkta
teknoloji konusu geçen haberler, yanında bölüm/ilçe; seçim kuralı altta yazılı.
Şablon yorumuna göre teknoloji kategorisinin son 400 haberinin hiçbiri Bursa'yı
anmıyor (arşiv ölçümü, 19 Ekim 2026). Liste boşsa yuva çizilmez.

**Öneri.**
- Bölümde 1–2 konu kümesi (ör. Bursa sanayisinde dönüşüm, teknopark/üniversite;
  konu dosyası varsa) — Spiegel'in kümeleme ilkesi, ürün testi değil → P2 · M ·
  → `web-tasarim-direktoru` + `haber-muduru`.
- Sponsorlu içerik gelirse etiketli kart ilkesi (bkz. `reklam-yerlesimi.md`)
  → P2 · S · → `haber-muduru`.

**Açık sorular — nasıl güçlenir.**
- Guardian, NYT teknoloji bölümleri: elle gözlem (kim, ne zaman, hangi koşul).
- Türkçe teknoloji yayınları (ör. teknoloji odaklı ulusal siteler) kütüphane
  listesinde yok; `SITELER.md`'ye aday eklemek hedefli mini tarama işidir
  (araştırmacı, kullanıcı onayıyla kapsam).
- Yerel sanayi kentlerindeki gazetelerin (Özgür Kocaeli) teknoloji/sanayi
  bölümü bu taramada ayrıca incelenmedi.
