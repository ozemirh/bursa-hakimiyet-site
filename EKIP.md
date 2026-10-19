# EKIP.md — Bursa Hakimiyet ürün ekibi

19 Ekim 2026'da kuruldu. Ajan tanımları `.claude/agents/` altında. Her ajan işe
başlamadan **bu dosyayı**, `CLAUDE.md`yi ve `URUN-PLANI.md`nin kendi alanına
giren bölümlerini okur.

> `URUN-PLANI.md` ~6.500 satır. Tamamını okuma; `grep -n '^## ' URUN-PLANI.md`
> ile başlıklara bak, alanına giren bölümleri aç. Plan bağlayıcıdır: plandan
> sapma gerekiyorsa önce plan güncellenir, sessiz sapma yok.

---

## Ürünün amacı (kullanıcının sözüyle, 19 Ekim 2026)

Bursa özelinde ve kısmen ulusala hitap eden, **klasik haber sitesi temasında**
ama **yapay zekânın ve modern teknolojinin getirdiği imkânlardan da
faydalanan** bir haber sitesi.

Bu üç şey birlikte okunur:

1. **Önce Bursa.** Okur önce kendi ilçesine, belediyesine, Bursaspor'una bakar.
   Ulusal gündem Bursa'ya dokunduğu ölçüde ve ikinci kademede yer alır.
2. **Klasik.** Türk gazete sayfa mimarisi: manşet hiyerarşisi, sürmanşet, spot,
   çok okunanlar, köşe yazarları, resmî ilanlar, künye. Klasik ≠ renksiz:
   tablo düzeni klasiktir, renk bilgi taşıdığı sürece kalır.
3. **Modern altyapı, görünmez yerde.** Yapay zekâ ve modern teknoloji okura
   "gösteriş" olarak değil, işe yarayan hizmet olarak çıkar: konu takibi,
   canlı veri, seslendirme, editöre taslak/denetim desteği, hızlı arama.

## Tasarım dili (kullanıcı kararı, 19 Ekim 2026)

| Kapsam | Renk | Değişkenler (`site.css` `:root`) |
|---|---|---|
| Sitenin geneli | **Kırmızı · koyu mavi (lacivert) · beyaz** | `--kirmizi` `--kirmizi-koyu` `--lacivert` `--lacivert-koyu` `--kagit` |
| Bursaspor sayfası | **Yeşil · beyaz** | `--yesil` `--yesil-koyu` `--yesil-ak` `--yesil-cizgi` |
| Seçili diğer sayfalar | **Sayfaya özel tasarım** | Sayfa başına yeni Türkçe adlı değişken takımı |

**Seçilen sayfalar (kullanıcı, 19 Ekim 2026):** Bursaspor (yapıldı) · **köşe yazıları**
· **ekonomi** (kategori 4) · **teknoloji** (kategori 9). Listeye ekleme kullanıcı kararıdır.

**Sayfaya özel tasarım** kararı §63'teki "bölüm renk temaları geri alındı"
kuralını ve §68'deki "Bursaspor tek istisnadır" notunu **günceller**: Bursaspor
artık tek istisna değil, ilk örnektir. Mekanizma §68'deki
`<body data-bolum="…">` + `site.css` altında `body[data-bolum="…"]` desenidir.

- **Hangi sayfaların** özel tasarım alacağına kullanıcı karar verir. Ajanlar aday
  önerir, gerekçesini yazar, kendiliğinden uygulamaz.
- Özel tasarım yalnız renk değildir; sayfanın içeriğine göre bileşen ve düzen de
  değişebilir. Üst kabuk (servis şeridi, kategori bandı, menü) değişmez.
- WCAG AA kontrastı ölçülür; kimlik rengi okunurluğu bozamaz.

## Ekip

| Ajan | Rol | Sahip olduğu alan |
|---|---|---|
| `haber-sistemi-uzmani` | Ürün sahibi, süreç takipçisi | `URUN-PLANI.md`, faz ölçütleri, mimari kararlar. **Koordinatör budur.** |
| `web-tasarim-direktoru` | Tasarım direktörü | Görsel yön, tasarım denetimi |
| `haber-muduru` | Haber müdürü | Editoryal strateji, içerik mimarisi, masa iş akışı, editoryal kurallar |
| `full-stack-gelistirici` | Full stack geliştirici | Uçtan uca özellikler; site ↔ panel ↔ araç bağlantısı |
| `frontend-gelistirici` | Frontend geliştirici | Şablonlar, `site.css`, istemci betikleri, tasarım dilinin uygulanması, erişilebilirlik |
| `backend-gelistirici` | Backend geliştirici | Django modelleri, sorgular, komutlar, PostgreSQL, arama (F7), önbellek |
| `yapay-zeka-uzmani` | Yapay zekâ uzmanı | `arac/`, konu motoru, taslak/denetim, seslendirme, okur tarafı yapay zekâ özellikleri |
| `veri-entegrasyon-muhendisi` | Veri ve entegrasyon mühendisi | `canli-veri/`, zamanlayıcı, dış kaynaklar, arşiv/kazıma, içe alma |
| `seo-buyume-uzmani` | SEO ve büyüme uzmanı | Teknik SEO, Google News/Discover, yapılandırılmış veri, sosyal dağıtım, okur kazanımı |
| `devops-altyapi-muhendisi` | DevOps / altyapı mühendisi | Barındırma, dağıtım, F8 kesim, yedek, izleme, zamanlanmış görevler |
| `hukuk-guvenlik-uyum-uzmani` | Hukuk, güvenlik ve uyum uzmanı | KVKK, Basın Kanunu, BİK, telif, uygulama güvenliği, 2FA |
| `test-kalite-muhendisi` | Test ve kalite mühendisi | Test stratejisi, ölçümle doğrulama, erişilebilirlik ve başarım denetimi |
| `haber-sayfasi-gelistirici` | (demo dönemi) | Yalnız `tasarim-*.html` demo dosyaları; ürün işinde kullanılmaz |

**Devretme kuralı.** Bir ajan kendi alanı dışına düşen bir sorun bulursa onu
çözmez; raporunda "→ `<ajan-adı>`" diye sahibine yönlendirir.

## Kullanıcıya gidilecek eşik konular

Bunlar dışındaki kararlar ekip içinde verilir (koordinatör: `haber-sistemi-uzmani`).

1. Canlı siteye / yayına dokunan her şey
2. Geri alınamaz işlemler (veri silme, adres değişimi, göç tekrarı)
3. Editoryal kural değişikliği
4. Yeni haber içeriği ihtiyacı (uydurma içerik yasak)
5. Yasal belirsizlik (BİK, Meta Yazar Bilgisi, telif, KVKK)
6. Kapsam büyümesi, para gerektiren her şey (ücretli servis, lisans, sunucu)
7. Hangi sayfaların özel tasarım alacağı

## Değişmez kararlar — yeniden önerme

- Geliştirme yalnız **Yön 1 (klasik)** üzerinde; `tasarim-2-*`, `tasarim-3-*` donduruldu.
- **Haberler yeni panelden girilir** (19 Ekim 2026); eski CMS'ten düzenli içe alma kurulmaz.
  Yeni kimlikler eski sitenin aralığıyla çakışmayan bir tabandan verilir.
- **Yedek alınmaz, zamanlanmış görevler açılmaz** (19 Ekim 2026, kullanıcı kararı) —
  ajanlar görev kurmaz/açmaz; yeniden önerilmez.
- Optimizasyon ve altyapıda **köklü değişiklik izinli** (19 Ekim 2026); push ve canlıya
  dokunma yine eşik konudur.
- **Adres deseni** `/{kategori-slug}/{slug}-{id}` korunur; birincil anahtar = eski kimlik.
- Mimari: **Django + PostgreSQL, sunucu render.** Tailwind, React, bundler önerilmez.
- Sınıf adları ve CSS değişken adları **Türkçe**; renk her zaman değişkenden, hex yazılmaz.
- Görseller yerel; dış görsel URL'si yok.
- **Uydurma içerik yok**; kaynak her zaman belirtilir; masumiyet karinesi korunur.
- Yapay zekâ aracında varsayılan sağlayıcı `kural`; Claude çağrıları `claude-opus-5`.
  Konu takibi **onaysız bağlamaz**.
- Reddedilenler: vefat/anma ilanları modülü · AdSense (askıda) · tarayıcı sesi
  (Web Speech) · elenen TTS adayları (`SESLENDIRME-NOTLARI.md`) · Bursaspor
  sayfasına kadro/diziler/basketbol/künye/form şeridi · Web3/blockchain ·
  YouTube'a otomatik haber paylaşımı · periyodik türleri (enflasyon, hava, döviz)
  konu saymak.

## Çalışma yöntemi

- **Ölç, tahmin etme.** Yerleşim için başsız Chrome (`icerik/tests_panel_olcum.py`
  içindeki `Cdp`); başarım için sorgu süresi; bitti için sayı.
- Testler: `cd uygulama && ../.venv/Scripts/python.exe manage.py test`
  (19 Ekim 2026: **879/879**).
- Geliştirme sunucusu 8731 (`--noreload`); açmadan önce port kontrolü
  (`netstat -ano | findstr :8731`), şablon değişikliğinden sonra yeniden başlat.
- Django şablonunda `{# #}` **tek satırlıktır**; çok satırlı yorum `{% comment %}`.
- Türkçe büyük/küçük harf için `site_etiket` süzgeçleri; `.title()`/`.upper()` kullanma.
- Göç ve migration sonrası `ANALYZE`.
- Kaynak dosyayı Bash heredoc'uyla yazma; Edit/Write aracını kullan.
