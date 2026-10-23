# Spor / kulüp sayfası — siteler arası desenler

Son güncelleme: 2026-10-20 (sentez) · Bursaspor sayfası **yapıldı**; bu dosya
yalnız karşılaştırma. **Veri az:** odak listesindeki Sözcü (erişim engelli),
NTV ve MEN (otomatik erişim yok) kulüp sayfaları ölçülmedi.

| Site | K. | Çözüm | Kaynak |
|---|---|---|---|
| Bursa Saati | D | Menüde "Bursaspor" kategorisi; anasayfada Süper Lig puan durumu + fikstür. Puan tablosu logoları dış spor API'sinin görsel alanından (anasayfada 17 istek) | `siteler/bursa-saati.md` §1, §5, §7 · [anasayfa](https://www.bursasaati.com.tr/), 2026-10-20 |
| Özgür Kocaeli | D | Menüde yerel kulüp ("Kocaelispor") genel "Spor"dan ayrı; Süper Lig fikstürü servis menüsünde | `siteler/ozgur-kocaeli.md` §1, §5, 2026-10-20 |
| Ege'de Son Söz | D | Süper Lig puan durumu servis olarak | `siteler/egede-son-soz.md` §5 |
| Habertürk | D | Anasayfada spor bandı ve 5'li Spor bloğu | `siteler/haberturk.md` §1 |
| Manchester Evening News | İ | Kulüp kapsamı sitenin dışına taşıyor: kulübe özel **WhatsApp kanalı** (~84 bin takipçi), Reach'in haftalık kulüp bülteni (ücretsiz önizleme + ücretli katman), kulüp başına editör; merkezi spor ekibi masanın dışında | `siteler/manchester-evening-news.md` Özet 3, §10 ([WhatsApp kanalı](https://www.whatsapp.com/channel/0029Va5la6v3bbV7no7rii2X), [bülten hakkında](https://insideoldtrafford.substack.com/about), 2026-10-20) |

**Ortak ders.** Yerel sitede kulüp, genel spordan ayrı bir menü girişi;
puan durumu ve fikstür en yaygın servis. Büyük yerel markada (MEN) kulüp
kitlesi sayfa dışı kanala (WhatsApp, bülten) taşınıyor.

**Hangi koşulda işe yarıyor.** Kanal/bülten düzenli içerik ister (kulüp başına
editör — MEN). Tek kulüplü şehirde tek kanal yeter.

**Bursa Hakimiyet'te durum.** `/bursaspor` yeşil-beyaz tema (`icerik/temalar.py`,
koşul: fikstür gelmediyse kabuk da yeşile dönmez); servis panelinde haftanın
maçı + puan penceresi; `alt` yuvada **FİKSTÜR VE SONUÇLAR** tablosu (kaynak
TFF, bayatsa "güncel değil", oynanmayan maçta tarih, bilgi yoksa "?")
(`parca/bolum/bursaspor.html`; URUN-PLANI §67–§68). Görseller yerel; dış spor
API'sinden logo çekilmiyor (görseller yerel kararı).

**Öneri.**
- Bursaspor için sayfa dışı dağıtım: WhatsApp kanalı ya da haftalık e-bülten
  (sayfa kararını değiştirmez) → P2 · S–M · → `haber-muduru` + `seo-buyume-uzmani`.
- Kadro, gazetenin dizileri, basketbol, kulüp künyesi, form şeridi →
  **BH için: reddedildi (kullanıcı kararı).**
- YouTube'a otomatik haber paylaşımı → **BH için: reddedildi (kullanıcı kararı).**

**Açık sorular — nasıl güçlenir.** MEN kulüp sayfaları, Sözcü ve NTV spor
bölümleri elle gözlemle; maç günü canlı anlatım biçimi (canlı blog — bkz.
`son-dakika.md`) hiçbir doğrudan örnekte görülmedi.
