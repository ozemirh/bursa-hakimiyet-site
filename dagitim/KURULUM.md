# Üretim kurulumu, kesim (F8) ve geri dönüş

19 Ekim 2026. **Bu klasördeki hiçbir dosya bir yere kurulmadı.** Sunucu
yok; sunucu kiralamak, DNS değiştirmek, zamanlayıcı açmak ve yayına almak
kullanıcı kararıdır (EKIP.md eşik 1 ve 6). Belge, karar verildiğinde
adımların sırayla ve ölçerek yapılabilmesi için yazıldı.

Bilinmeyenler — **varsaymadık, sorulacak**: gazetenin bugünkü barındırma
sağlayıcısı, DNS'in kimde olduğu, e-posta altyapısı (MX kayıtları,
alt alanlar), analitik hesabı (GA4 `G-4RVSYL5WQM` eski sağlayıcının
Firebase projesinde), eski CMS'in kesimden sonra ne kadar açık kalacağı.

---

## 1. Mimari

```
okur ──► (Cloudflare, isteğe bağlı) ──► nginx :443
                                         │  /statik/*          → disk (özetli, 1 yıl, .gz/.br)
                                         │  /static/sitemap/*  → disk (özetsiz, 5 dk) ↘ yoksa Django
                                         │  /arsiv-gorsel/*    → disk (30 gün)
                                         │  /gorsel/*          → disk türev ↘ yoksa Django + 30 gün önbellek
                                         │  anonim HTML        → 10 sn mikro önbellek → gunicorn
                                         │  /panel /yonetim    → önbelleksiz → gunicorn
                                         ▼
                              gunicorn (systemd, unix soketi, 2×çekirdek+1 sync işçi)
                                         │
                              Django 5.2 ─┼─ PostgreSQL 16 (yerel)
                                         └─ canlı veri JSON (systemd timer'lar yazar, site okur)
```

| Katman | Seçim | Gerekçe |
|---|---|---|
| Uygulama sunucusu | gunicorn sync | Sunucu render, kısa istek; nginx tamponlar. Async gerekmez. |
| Ters vekil | nginx | Statik/görsel diskten, mikro önbellek, TLS, hız sınırı. |
| Statik | collectstatic + WhiteNoise depolaması | Özetli ad + .gz/.br derleme anında; nginx `gzip_static` ile verir. WhiteNoise nginx'siz kurulumda da aynı işi yapar. |
| Önbellek | nginx mikro önbellek (HTML) + Django CACHES (paket A) | Trafik günü yükünü nginx emer. |
| Veritabanı | PostgreSQL, aynı makinede | Tek makine ölçeği; ağ gecikmesi yok. |
| Zamanlanmış işler | systemd timer | `Persistent=true` kaçan koşuyu telafi eder; oturuma ve pile bağlı değil. |
| Günlük | journald (uygulama, timer) + nginx dosyası | `journalctl -u bursahakimiyet`. |
| Container/orchestrator | **yok** | Tek uygulama, tek makine, tek veritabanı. Kubernetes'in getirisi (çok düğüm, otomatik ölçek) bu ölçekte yok; bedeli (işletim karmaşıklığı) var. Trafik tek makineyi aşarsa önce Cloudflare HTML önbelleği, sonra ikinci uygulama makinesi düşünülür. |

**Boyut** (DEGERLENDIRME §4 DevOps): 4 vCPU · 16 GB RAM · ≥ 400 GB NVMe
(veritabanı ~4 GB + arşiv görselleri 147 GB + türevler + büyüme).

## 2. Maliyet — kullanıcı kararı

| Kalem | Seçenek | Kaba aylık maliyet |
|---|---|---|
| Sunucu | Türkiye'de VDS, 4 vCPU / 16 GB / 400 GB NVMe | ~500–1.500 TL |
| Sunucu | Avrupa bulut (Hetzner CPX41 sınıfı + 400 GB blok disk) | ~35–50 € |
| CDN / DDoS | Cloudflare Free | 0 $ (DNS'in Cloudflare'e taşınmasını ister) |
| TLS | Let's Encrypt | 0 |
| Dış yoklama | UptimeRobot / healthchecks.io ücretsiz katman | 0 |
| Yedek | **Kullanıcı kararıyla (19 Ekim 2026) yedek alınmıyor** | — |

> Yedek kararı kayıtlıdır ve bu belge yedek adımı içermez. Kalan risk tek
> cümle: arşiv görsellerinin kaynağı sunucudan silinmiş olduğundan, tek
> kopyanın kaybı geri getirilemez (DEGERLENDIRME §3/1).

## 3. Sunucu hazırlığı (Ubuntu 24.04)

```bash
sudo apt update && sudo apt -y full-upgrade
sudo apt -y install nginx postgresql-16 python3.12-venv python3.12-dev \
    build-essential libpq-dev git rsync curl certbot ufw \
    libnginx-mod-http-brotli-filter libnginx-mod-http-brotli-static
sudo timedatectl set-timezone Europe/Istanbul

# hizmet kullanıcısı ve dizinler
sudo adduser --system --group --home /srv/bursahakimiyet bh
sudo usermod -aG www-data bh
sudo mkdir -p /srv/bursahakimiyet/{kod,statik,sitemap,canli-veri,arsiv/gorseller,turev,medya,gunluk}
sudo chown -R bh:bh /srv/bursahakimiyet
sudo chmod 0755 /srv/bursahakimiyet /srv/bursahakimiyet/{statik,sitemap,arsiv,turev}

# güvenlik duvarı: yalnız SSH + web
sudo ufw allow OpenSSH && sudo ufw allow 'Nginx Full' && sudo ufw enable
```

Python sürümü geliştirme ortamıyla aynı olmalı (`.venv/pyvenv.cfg`: 3.12).

## 4. PostgreSQL

Veritabanı göçü paket B'nin işi (`pg_goc`, akışla aktarım → satır sayımı +
md5 örneklemi → 10 bin adreslik 200/301 denetimi → `ANALYZE`). Kurulumda
yalnız rol ve veritabanı:

```bash
sudo -u postgres createuser --pwprompt bh
sudo -u postgres createdb -O bh -E UTF8 -l tr_TR.UTF-8 -T template0 bursahakimiyet
```

`BH_VERITABANI=postgresql://bh:PAROLA@127.0.0.1:5432/bursahakimiyet`.

## 5. Kod, ortam, ilk derleme

```bash
sudo -u bh git clone https://github.com/<depo>.git /srv/bursahakimiyet/kod
cd /srv/bursahakimiyet/kod && sudo -u bh git checkout --detach <sürüm-etiketi>
sudo -u bh python3.12 -m venv /srv/bursahakimiyet/venv
sudo -u bh /srv/bursahakimiyet/venv/bin/pip install -r requirements.txt

# ortam dosyası: dagitim/.env.ornek → doldur
sudo install -d -m 0750 -o root -g bh /etc/bursahakimiyet
sudo install -m 0640 -o root -g bh dagitim/.env.ornek /etc/bursahakimiyet/ortam
sudoedit /etc/bursahakimiyet/ortam
#   BH_ORTAM=uretim
#   BH_GIZLI_ANAHTAR=<python3 -c "import secrets; print(secrets.token_urlsafe(64))">
#   BH_SUNUCU_ADLARI=www.bursahakimiyet.com.tr,bursahakimiyet.com.tr
#   BH_VERITABANI=postgresql://…
#   BH_STATIK_KOK=/srv/bursahakimiyet/statik
#   BH_ARSIV_KOK=/srv/bursahakimiyet/arsiv
#   BH_CANLI_VERI_KOK=/srv/bursahakimiyet/canli-veri   BH_CANLI_KOK=(aynısı)
#   BH_SITE_HARITASI_KOK=/srv/bursahakimiyet/sitemap
#   BH_REKLAM_TEST=0

cd /srv/bursahakimiyet/kod/uygulama
sudo -u bh sh -c 'set -a; . /etc/bursahakimiyet/ortam; set +a;
  ../../venv/bin/python manage.py check --deploy &&
  ../../venv/bin/python manage.py migrate --noinput &&
  ../../venv/bin/python manage.py collectstatic --noinput'
```

Uygulama `BH_GIZLI_ANAHTAR` ya da `BH_SUNUCU_ADLARI` olmadan **açılmaz**,
`BH_HATA_AYIKLA=1` ile de açılmaz (fail-closed, `cekirdek/ortam.py`).
`check --deploy` bugünkü ayarlarla 2 uyarı verir (W005, W021: HSTS alt alan
ve ön yükleme). İkisi de bilerek kapalı: alan adının diğer alt alanları
bilinmeden açmak geri alınamaz. Kararla `BH_HSTS_ALT_ALANLAR=1`,
`BH_HSTS_ON_YUKLEME=1` → 0 uyarı.

**Arşiv görselleri** (147 GB) kesimden günler önce aktarılır; ev bağlantısının
yükleme hızında (20 Mbit/s) bu ~16 saat:

```bash
rsync -aH --partial --info=progress2 /d/bursa-hakimiyet-arsiv/gorseller/ \
      bh@SUNUCU:/srv/bursahakimiyet/arsiv/gorseller/
```

## 6. Servisler

```bash
cd /srv/bursahakimiyet/kod/dagitim
sudo cp systemd/*.service systemd/*.timer /etc/systemd/system/
sudo cp nginx/snippets/*.conf /etc/nginx/snippets/
sudo cp nginx/bursahakimiyet.conf /etc/nginx/sites-available/
sudo ln -s /etc/nginx/sites-available/bursahakimiyet.conf /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo mkdir -p /var/cache/nginx/bh_html /var/cache/nginx/bh_gorsel /var/www/certbot
sudo chmod +x bin/*.sh

sudo systemctl daemon-reload
sudo systemctl enable --now bursahakimiyet
# sertifika: DNS sunucuyu gösterdikten SONRA (kesim günü) ya da DNS-01 ile önceden
sudo certbot certonly --webroot -w /var/www/certbot \
     -d www.bursahakimiyet.com.tr -d bursahakimiyet.com.tr
sudo nginx -t && sudo systemctl reload nginx

# bh kullanıcısı yayinla.sh içinden yalnız şunu yapabilsin:
echo 'bh ALL=(root) NOPASSWD: /usr/bin/systemctl reload bursahakimiyet' | sudo tee /etc/sudoers.d/bh
```

**Zamanlanmış işler (timer) — açmak kullanıcı kararı.** Dosyalar hazır,
etkinleştirme komutu:

```bash
sudo systemctl enable --now bh-canli-sik.timer bh-canli-saatlik.timer \
     bh-canli-gunluk.timer bh-site-haritasi.timer
# haber yazan iş ayrıca karar ister (veritabanına günlük eczane haberi açar):
sudo systemctl enable --now bh-canli-haber.timer
systemctl list-timers 'bh-*'
```

Bu Windows makinesinde Görev Zamanlayıcı görevleri **kapalı kalır**
(kullanıcı kararı, 19 Ekim 2026).

## 7. İzleme

| Ne | Nasıl | Eşik |
|---|---|---|
| Site ayakta mı | Dış yoklama `GET https://www…/_durum`, 1 dk | HTTP 503 ya da 3 ardışık zaman aşımı → uyarı |
| Ayrıntılı durum | Aynı uç, `X-Durum-Anahtari: $BH_DURUM_ANAHTARI` | `"genel": "uyari"` 30 dk sürerse bak |
| Canlı veri | `/_durum` → `canli_veri.bayat` | Döviz 24 sa, hava 3 sa (dosyadaki eşik) |
| Zamanlanmış iş | `OnFailure=bh-uyari@` → journald `crit` + `BH_UYARI_ADRESI` | Her başarısızlık |
| Disk | `/_durum` → `disk` | < %10 ya da < 10 GB uyarı, < %2 → 503 |
| Önbellek isabeti | `X-Onbellek` başlığı; `awk` ile nginx günlüğü | Trafik gününde HIT oranı ≥ %90 hedef |
| Hatalar | `journalctl -u bursahakimiyet -p err`, `/var/log/nginx/bh.error.log` | — |

`/_durum` yetkisize yalnız `{"genel": …}` döner; ayrıntı personel oturumu ya
da anahtarla. Önbelleğe alınmaz.

## 8. Güncelleme ve kod geri dönüşü

```bash
sudo -u bh /srv/bursahakimiyet/kod/dagitim/bin/yayinla.sh v2026.10.20
# geri almak: betiğin son satırda yazdığı önceki commit ile
sudo -u bh /srv/bursahakimiyet/kod/dagitim/bin/yayinla.sh <önceki-commit>
```

- `collectstatic` **`--clear` olmadan**: eski özetli CSS/JS diskte kalır,
  önbellekteki eski HTML kırılmaz, geri dönüşte eski adlar hazırdır.
- Migration içeren sürüm geri alınırken önce
  `manage.py migrate <uygulama> <önceki_migration>`, sonra kod. Geri
  alınamayan (veri silen) migration, sürüm notunda işaretlenir.

---

## 9. F8 kesim günü listesi

F8 ölçütü (URUN-PLANI §3): (a) hazırlık ortamında 556.824 adresin %100'ü
doğru içerik; (b) beş sitemap ailesi yeniden üretiliyor ve sayılar
kaynakla eşleşiyor; (c) geri dönüş **bir kez denenmiş**.

**T−14 … T−7 (hazırlık)**
1. Sunucu, PostgreSQL, kod, ortam (§3–6) — DNS'e dokunmadan.
2. Veritabanı göçü + doğrulama sayıları (paket B).
3. Arşiv görselleri rsync; dosya sayısı kaynakla eşit (`find | wc -l`).
4. Hazırlık adresiyle (ör. `hazirlik.bursahakimiyet.com.tr` ya da
   `/etc/hosts`) F8(a): adres doğrulama komutu 556.824 / 556.824.
5. F8(b): `site_haritasi_uret` + `site_haritasi_karsilastir --canli`.
6. **Geri dönüş provası** (F8/c): hazırlıkta "kesim → geri dön" bir kez
   yapılır, süre ölçülür (§10).
7. Yük denemesi: anasayfa ve 20 haber adresine 200 eşzamanlı istek;
   p95 ve `X-Onbellek` HIT oranı yazılır.

**T−2**
8. DNS kayıtlarının TTL'i 300 sn'ye indirilir (eski değer not edilir).
9. Eski sağlayıcıdan son içerik farkı planı: kesimden sonra haberler yeni
   panelden girilecek (kullanıcı kararı); eski CMS'te kesim anına kadar
   yayımlananların bize alınıp alınmayacağı karara bağlanır.

**T0 (kesim, düşük trafik saati — ör. 03:00–05:00)**
10. Eski CMS'e yeni haber girişi durdurulur (masaya duyuru).
11. Son içerik farkı alınır (karar verildiyse), `ANALYZE`.
12. `site_haritasi_uret`; `check --deploy`; `/_durum` → `tamam`/`uyari`.
13. DNS A/AAAA (www + çıplak alan) yeni sunucuya. MX ve diğer kayıtlara
    **dokunulmaz**.
14. Sertifika (HTTP-01 artık çalışır) → nginx reload.
15. Duman testi: anasayfa, 5 kategori, 20 rastgele eski haber adresi
    (200), 5 yanlış slug (301), `/static/sitemap/sitemap.xml`,
    `/static/sitemap/googleNews.xml`, `/rss`, `/robots.txt`, panel girişi.
16. Search Console: sitemap yeniden gönderilir (alan adı aynı, adres
    değişikliği bildirimi gerekmez).

**T+1 … T+14**
17. Günlük: 404 oranı (nginx günlüğü), `/_durum`, Search Console tarama
    hataları, Google News görünürlüğü.
18. HSTS kademesi: T+14'te `BH_HSTS_SANIYE=31536000`.
19. Eski barındırma **en az 14 gün açık** kalır; kapatma kullanıcı kararı.

## 10. Geri dönüş planı

**Ne zaman:** kesimden sonraki ilk 2 saatte (a) 5 dk'dan uzun süren 5xx,
(b) eski haber adreslerinde 404 oranı > %1, (c) panelden haber
yayımlanamıyor, (d) veri bütünlüğü şüphesi. Karar: `haber-sistemi-uzmani`
+ kullanıcı.

**Nasıl (≤ 10 dk, TTL 300 sn sayesinde):**
1. DNS A/AAAA kayıtları eski sağlayıcının adresine geri.
2. Eski CMS'e haber girişi yeniden açılır.
3. Yeni sistemde kesimden sonra girilen haberler listelenir
   (`yayin_zamani >= kesim anı`) ve eski CMS'e elle taşınır.
4. Yeni sunucu kapatılmaz; neden araştırılır, düzeltilip yeniden prova.

**Kod düzeyinde geri dönüş** (kesim sonrası bir sürüm bozulursa): §8.

**Prova:** T−7'de hazırlık ortamında §10'un 1–3. adımları uygulanır, süre
ve sonuç bu belgeye yazılır. Prova yapılmadan F8 kapanmaz.

## 11. Kullanıcı kararı gerektirenler

1. Sunucu seçimi ve aylık bedel (§2).
2. Cloudflare kullanımı (DNS taşınması gerekir).
3. HSTS alt alan / ön yükleme (geri alınması zor).
4. Timer'ların açılması; özellikle eczane haberi yazan iş.
5. Kesim tarihi ve saati; eski barındırmanın kapatılma tarihi.
6. Eski CMS'teki son içerik farkının alınıp alınmayacağı.
7. Uyarı kanalı (e-posta/mesaj) — altyapı bilinmiyor.
