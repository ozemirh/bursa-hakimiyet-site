# Anasayfa mimarisi — siteler arası desenler

Son güncelleme: 2026-10-20 (sentez; yeni ağ isteği yok) · Kaynak siteler:
Bursada Bugün, Bursa Saati, Ege'de Son Söz, Özgür Kocaeli, Habertürk (doğrudan);
Guardian, BBC News (ikincil); Hürriyet, Sözcü, Milliyet, NTV (eski kayıt).

Kanıt: **D** doğrudan ölçüm (başsız Chrome / `curl`, Türkiye, çerez kabul
edilmedi) · **İ** ikincil kaynak · **E** eski kayıt (URUN-PLANI §44, 2 Eylül
2026), bu taramada doğrulanmadı. Yerel rakip ölçüleri **tek ölçüm,
2026-10-20, Türkiye**; sıralama değildir.

| Site | K. | Üstten sıra (kısa) | Manşet | İlk ekran başlık (1440) | Kaynak |
|---|---|---|---|---|---|
| Bursada Bugün | D | piyasa+hava bandı → menü (Bursa Bölge açılır) → tek satır son dakika → numaralı 18'li slayt + ikinci slayt → tam genişlik reklam → 3'lü ızgara | çoklu, numaralı | 11 | `siteler/bursada-bugun.md` §1 · [anasayfa](https://www.bursadabugun.com/), 2026-10-20 |
| Bursa Saati | D | tam genişlik reklam → logo+piyasa+hava → menü → 2. reklam → ~140 px boş alan → son dakika şeridi → piyasa → manşet | slayt, "Tüm manşetler" sayfası | 6 | `siteler/bursa-saati.md` §1 · [anasayfa](https://www.bursasaati.com.tr/), 2026-10-20 |
| Ege'de Son Söz | D | kırmızı başlık bandı (ilçe adlı hava, borsa) → menü → **4'lü sürmanşet** → slayt manşet + 2 kart; ilk ekranda reklam yok | sürmanşet + slayt | 8 | `siteler/egede-son-soz.md` §1 · [anasayfa](https://www.egedesonsoz.com/), 2026-10-20 |
| Özgür Kocaeli | D | başlık bandı (WhatsApp ihbar) → menü → manşet + numaralı seçici → 4'lü kart; aşağıda yazarlar, **basılı ön sayfa**, resmi ilan kaydırıcısı | çoklu | 13 (pencere arkasında, DOM) | `siteler/ozgur-kocaeli.md` §1 · [anasayfa](https://www.ozgurkocaeli.com.tr/), 2026-10-20 |
| Habertürk | D | yapışkan piyasa → başlık → menü → 970×250 + yan giydirme → 4'lü sürmanşet → sponsor bandı → manşet (3 + ~20 kaydırıcı) → … ~25 blok … → **Yerel Haberler en altta** | sürmanşet + kaydırıcı | 11 | `siteler/haberturk.md` §1 · [anasayfa](https://www.haberturk.com/), 2026-10-20 |
| Guardian | İ | 2014'te sütun yerine yapılandırılabilir yatay bant kapsayıcılar; güncel düzen doğrulanmadı | — | ölçülmedi | `siteler/guardian.md` §1 (journalism.co.uk, arama özeti) |
| BBC News | İ | 2024 yeniden tasarımı; gerekçe reklam teknolojisi | — | ölçülmedi | `siteler/bbc-news.md` §1 (DigitalTVEurope, 2024-03-22) |
| Hürriyet · Sözcü · Milliyet · NTV | E | son dakika şeridi/kartları (bkz. `son-dakika.md`) | — | ölçülmedi | URUN-PLANI §44 — doğrulanmadı (eski kayıt) |

**Ortak ders.**
- Türk yerel ve ulusal örneklerin hepsinde en üstte **piyasa + hava bandı**,
  altında **çoklu manşet** (numaralı slayt ya da sürmanşet + slayt) var.
  Bu, Türk okurunun beklediği klasik kalıp; BH'nin §1 düzeniyle aynı yön.
- İlk ekranın başlık sayısını en çok **reklam kararı** belirliyor. Aynı hazır
  platformda Ege'de Son Söz (ilk ekranda reklam yok) 8 başlık gösteriyor,
  Bursa Saati (3 yuva + boş ayrılmış alan) 6 (`egede-son-soz.md` §9).
- Resmî ilan anasayfada **ayrı modül** olarak duruyor (Habertürk 16 yuva,
  Özgür Kocaeli kaydırıcı, Bursada Bugün sayfa + çerçeve).
- Ulusal sitede yerel blok en altta (Habertürk). Yerel sitede ilçe girişi
  menüde (Bursada Bugün, Ege).

**Hangi koşulda işe yarıyor.** Çoklu manşet ancak masa günde yeterli manşet
adayı üretiyorsa dolu görünür. Habertürk'ün ~25 bloğu büyük ulusal masa ve
kardeş markalarla (Show TV, BloombergHT) beslenir; 10 kişilik yerel masaya
taşınmaz. Ege'nin "ilk ekranda reklam yok" kararı reklam gelirinden vazgeçmek
demek; bu bir ticari karardır.

**Bursa Hakimiyet'te durum.** `uygulama/sablonlar/anasayfa.html`: döviz bandı
→ 4'lü sürmanşet (`dortlu`) → manşet slaytı + 300×250 + mini slayt → geniş son
dakika + 300×250 → yazarlar → son haberler + "daha fazla" → en çok okunanlar →
Bursa ilçeleri → 300×250 → günün manşetleri → resmî ilanlar → şehir servisleri
→ Bursaspor → galeriler → videolar → vizyon. Her sayfanın üstünde
1100×150/970×250 şerit, iki yanda yapışkan 160×600 (`taban.html` 148, 93–95,
167–169). "Önce Bursa" oranı `BH_MANSET_BURSA_ORANI` 10/15 (URUN-PLANI §70 H).
İlk ekran başlık sayısı: **yerelde ölçülecek → `test-kalite-muhendisi`**.
Basılı gazetenin "E-gazete" bağlantısı `href="#"` (`parca/ust_bant.html:36`,
`parca/kategori_bandi.html:97`).

**Öneri.**
- İlk ekran başlık sayısını aynı yöntemle (görünür, metni ≥ 25 karakter `a`;
  1440 ve 390) ölç, reklam açık/kapalı iki koşulda → P1 · S ·
  → `test-kalite-muhendisi`; hedefin konması → `web-tasarim-direktoru`.
- Basılı ön sayfa / e-gazete bağlantısı ya gerçek hedefe bağlansın ya kalksın
  (Özgür Kocaeli basılı ön sayfayı arşive bağlıyor) → P0 · S (ölü bağlantı;
  bkz. `karsilastirma.md`) · → `frontend-gelistirici` + `haber-muduru`.
- Vefat listesi (Özgür Kocaeli anasayfası) → **BH için: reddedildi (kullanıcı kararı).**
