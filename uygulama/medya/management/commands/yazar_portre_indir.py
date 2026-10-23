# -*- coding: utf-8 -*-
"""Yazar portrelerini canlı siteden indirir ve arşive yerleştirir.

**Neden gerekti.** Göç, her yazarın portresi diye kaynaktaki `og:image`
karesini almıştı: 37 kaydın 37'si de **1200x630** (ölçüldü). Bu ölçü haber
paylaşım kırpımıdır, portre değil — yuvarlak avatarda yüzün üstü ve altı
kesiliyor. Canlı site aynı fotoğrafı iki biçimde daha yayımlıyor:

    /static/<YYYY/AA/GG>/<ad>_small.jpg   270x270  temiz KARE portre
    /static/<YYYY/AA/GG>/<ad>.jpg          750x500  özgün yatay kare

Ölçüldü (30 Ağustos 2026): `_small.jpg` yalnız **yeni** kayıtlarda var
(kaynağı `_large.webp` olanlar, 2025+) — 19 kayıt; 2021-2024 kayıtlarında
404 dönüyor ve elde yalnız 750x500 özgün kalıyor — 18 kayıt.

**Kritik ayrım (10 dosya açılıp GÖRÜLDÜ):** 750x500 olan şey bir portre
değil, gazetenin **afiş şablonudur** — solda yazarın adı büyük harflerle,
yüz sağ üçte birde. Ortadan kırpılırsa yuvarlak avatarda yüz değil arka
plan çıkar. Üstelik **afiş şablonu iki çeşit** ve yüzün yeri değişiyor:

    2022-01-13 partisi (7 kayıt)  "beton"  gri duvar, yüz merkezi x≈570
    2023 ve sonrası   (11 kayıt)  "harita" kırmızı harita, merkez x≈620

Tek pencere ikisine birden uymadı (ölçüldü): haritaya göre ayarlanan
pencere beton şablonunda yüzü sola itip sağ üçte biri duvara ayırıyordu.
Bu yüzden dosya adı hem biçimi hem şablonu söyler:

    {slug}-portre.jpg        270x270 kare portre -> ortadan kırpılır
    {slug}-afis-harita.jpg   750x500 afiş        -> pencere x∈[490,750]
    {slug}-afis-beton.jpg    750x500 afiş        -> pencere x∈[440,700]

Sayfa tarafı ayrımı `img[src*="-afis-harita"]` / `-afis-beton` ile yapar;
model alanı ve migration gerekmez. Pillow ile kırpmak da çözerdi ama yeni
bağımlılık getirirdi.

**Adres imzalı.** Kayıttaki `gorsel_url` thumbor adresidir
(`/cdn/<imza>=/1200x630/webp/...`) ve imza geometriyi kapsar, ölçü
değiştirilemez. Komut o adresten yalnız **tarih ve dosya adını** ayıklayıp
`/static/` ağacındaki özgün dosyaya gider.

**Nazik davranır.** Site WebFetch'i engelliyor (kazıma notu), o yüzden
Chrome imzalı doğrudan istek kullanılır; istekler arası 1 sn beklenir ve
zaman aşımı 30 sn'dir (CDN istek başına 0,4-20,6 sn ölçüldü).

**Tekrar çalıştırılabilir.** Dosya diskte varsa yeniden indirilmez.
`medya_goc_al` yeniden koşarsa `gorsel_dosya` alanını arşiv JSON'undaki
değere geri yazar (update_or_create) — o zaman bu komut yeniden koşulur.

Kullanım:
    python manage.py yazar_portre_indir            # eksikleri indirir
    python manage.py yazar_portre_indir --zorla    # var olanı da tazeler
    python manage.py yazar_portre_indir --deneme   # yazmaz, ne yapacağını söyler
"""

import re
import time
import urllib.error
import urllib.request

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.utils import OperationalError

from medya.models import Yazar

KOK_ADRES = "https://www.bursahakimiyet.com.tr"
# Portrelerin konacağı ağaç. `/arsiv-medya/` yalnız dört beyaz listeli
# klasörü servis eder (medya/adresler.py) — `gorseller-yazar` onlardan biri.
# `gorseller/` HABER ağacıdır ve `/arsiv-gorsel/` ile servis edilir; portre
# oraya konursa 404 olur.
ALT_KLASOR = "gorseller-yazar/portre"
# Gazete yazar afişini bu tarihte yeniledi: öncesi "beton", sonrası
# "harita" şablonu (gözle doğrulandı, bkz. modül başlığı). Yeni bir
# şablon çıkarsa buraya ikinci bir sınır eklenir.
AFIS_SINIRI = "2023-01-01"

BASLIK = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept": "image/avif,image/webp,image/*,*/*;q=0.8",
    "Referer": KOK_ADRES + "/",
}
BEKLEME = 1.0
ZAMAN_ASIMI = 30


def _adaylar(gorsel_url: str) -> list:
    """İmzalı CDN adresinden özgün dosya adaylarını türetir, iyiden kötüye."""
    m = re.search(r"/(\d{4}/\d{2}/\d{2})/(.+)$", gorsel_url or "")
    if not m:
        return []
    tarih, ad = m.group(1), m.group(2)
    govde = re.sub(r"_large\.webp$|\.(jpe?g|webp|png)$", "", ad)
    return [
        # 270x270 kare portre — yalnız yeni kayıtlarda var
        f"{KOK_ADRES}/static/{tarih}/{govde}_small.jpg",
        # 750x500 özgün — eski kayıtların tek seçeneği
        f"{KOK_ADRES}/static/{tarih}/{ad}",
    ]


def _indir(adres: str) -> bytes:
    istek = urllib.request.Request(adres, headers=BASLIK)
    with urllib.request.urlopen(istek, timeout=ZAMAN_ASIMI) as yanit:
        return yanit.read()


def _gorsel_mi(veri: bytes) -> bool:
    """İçerik gerçekten görüntü mü — sunucu 404 yerine HTML dönebiliyor."""
    return veri[:2] == b"\xff\xd8" or veri[:4] == b"\x89PNG" or veri[8:12] == b"WEBP"


class Command(BaseCommand):
    help = "Yazar portrelerini canlı siteden indirir (kare varsa kareyi alır)."

    def add_arguments(self, ayristirici):
        ayristirici.add_argument("--zorla", action="store_true",
                                 help="Diskte olsa da yeniden indir.")
        ayristirici.add_argument("--deneme", action="store_true",
                                 help="Hiçbir şey yazma, ne yapılacağını söyle.")
        ayristirici.add_argument("--sinir", type=int, default=0,
                                 help="En çok kaç yazar işlensin (0 = hepsi).")

    def handle(self, *args, **secenek):
        hedef_klasor = settings.ARSIV_KOK / ALT_KLASOR
        yazarlar = list(Yazar.objects.exclude(gorsel_url="").order_by("pk"))
        if secenek["sinir"]:
            yazarlar = yazarlar[:secenek["sinir"]]

        self.stdout.write(f"{len(yazarlar)} yazar · hedef {hedef_klasor}")
        if not secenek["deneme"]:
            hedef_klasor.mkdir(parents=True, exist_ok=True)

        guncellenecek, atlandi, basarisiz = {}, 0, []
        kayit_satirlari = []

        for yazar in yazarlar:
            # Ad, indirilen biçim belli olunca kesinleşir; ikisinden biri
            # zaten diskteyse yeniden indirilmez.
            varolan = next((hedef_klasor / f"{yazar.slug}-{ek}.jpg"
                            for ek in ("portre", "afis-harita", "afis-beton")
                            if (hedef_klasor / f"{yazar.slug}-{ek}.jpg").is_file()), None)
            if varolan is not None and not secenek["zorla"]:
                atlandi += 1
                guncellenecek[yazar.pk] = f"{ALT_KLASOR}/{varolan.name}"
                continue

            veri = kaynak = None
            for aday in _adaylar(yazar.gorsel_url):
                try:
                    olasi = _indir(aday)
                except (urllib.error.URLError, OSError) as hata:
                    self.stdout.write(f"  · {yazar.ad}: {aday.rsplit('/', 1)[-1]} — {hata}")
                    time.sleep(BEKLEME)
                    continue
                if _gorsel_mi(olasi):
                    veri, kaynak = olasi, aday
                    break
                time.sleep(BEKLEME)

            if veri is None:
                basarisiz.append(yazar.ad)
                self.stdout.write(self.style.WARNING(f"  ! {yazar.ad}: portre bulunamadı"))
                continue

            kare = kaynak.endswith("_small.jpg")
            if kare:
                bicim = "portre"
            else:
                tarih = re.search(r"/(\d{4}/\d{2}/\d{2})/", kaynak)
                gun = tarih.group(1).replace("/", "-") if tarih else "9999-99-99"
                bicim = "afis-beton" if gun < AFIS_SINIRI else "afis-harita"
            ad = f"{yazar.slug}-{bicim}.jpg"
            goreli = f"{ALT_KLASOR}/{ad}"
            dosya = hedef_klasor / ad
            if secenek["deneme"]:
                self.stdout.write(f"  (deneme) {yazar.ad} <- {kaynak[len(KOK_ADRES):]} -> {ad}")
            else:
                # .tmp'ye yaz, sonra yerine koy: yarım dosya bırakma.
                gecici = dosya.with_suffix(".tmp")
                gecici.write_bytes(veri)
                gecici.replace(dosya)
                # Biçim değiştiyse (kaynak yenilenmiş olabilir) öteki adlar
                # ortada kalmasın: aynı yazarın iki dosyası olmaz.
                for baska in ("portre", "afis-harita", "afis-beton"):
                    if baska == bicim:
                        continue
                    oteki = hedef_klasor / f"{yazar.slug}-{baska}.jpg"
                    if oteki.is_file():
                        oteki.unlink()
                guncellenecek[yazar.pk] = goreli
            kayit_satirlari.append(f"{yazar.pk}\t{yazar.ad}\t{kaynak}\t{bicim}\t{len(veri)}")
            self.stdout.write(f"  + {yazar.ad} ({bicim}, {len(veri)} bayt)")
            time.sleep(BEKLEME)

        if secenek["deneme"]:
            self.stdout.write(self.style.SUCCESS(
                f"Deneme bitti · {len(kayit_satirlari)} indirilecek · {atlandi} atlanacak"))
            return

        # Kaynak kaydı: hangi dosya nereden geldi. Hak teyidi bu kayda dayanır
        # (URUN-PLANI hukuki teyit kalemi) — portreler gazetenin kendi
        # yayınından alınıyor ama yayın öncesi teyit ayrıca yapılmalı.
        if kayit_satirlari:
            kayit = hedef_klasor / "KAYNAK.tsv"
            basligi_var = kayit.exists()
            with kayit.open("a", encoding="utf-8", newline="\n") as dosya_kaydi:
                if not basligi_var:
                    dosya_kaydi.write("pk\tad\tkaynak_adres\tbicim\tbayt\n")
                dosya_kaydi.write("\n".join(kayit_satirlari) + "\n")

        self._veritabanina_yaz(guncellenecek)

        self.stdout.write(self.style.SUCCESS(
            f"Bitti · {len(kayit_satirlari)} indirildi · {atlandi} zaten vardı · "
            f"{len(basarisiz)} başarısız"))
        if basarisiz:
            self.stdout.write("Portresi alınamayanlar: " + ", ".join(basarisiz))

    def _veritabanina_yaz(self, guncellenecek: dict):
        """Kısa tek işlem + geri çekilmeli tekrar.

        SQLite `delete` günlüğünde ve göç süreçleri aynı dosyaya yazıyor;
        yazar okuyucuyu bloklar. 37 pk güncellemesi milisaniyeler sürer, asıl
        risk bir göç parçası kilidi tutarken 'database is locked' almaktır.
        """
        if not guncellenecek:
            return
        # Bayrak-dosya tutarsızlığı kırık resim demek: gorsel_yolu() diske
        # BAKMAZ. O yüzden yazmadan önce dosya gerçekten var mı doğrulanır.
        for yol in guncellenecek.values():
            if not (settings.ARSIV_KOK / yol).is_file():
                raise RuntimeError(f"dosya diskte yok, DB yazılmadı: {yol}")

        for deneme in range(5):
            try:
                with transaction.atomic():
                    for pk, yol in guncellenecek.items():
                        Yazar.objects.filter(pk=pk).update(gorsel_var=True,
                                                           gorsel_dosya=yol)
                self.stdout.write(f"  DB: {len(guncellenecek)} kayıt güncellendi")
                return
            except OperationalError as hata:
                if "locked" not in str(hata).lower() or deneme == 4:
                    raise
                self.stdout.write(f"  DB kilitli, {2 ** deneme} sn sonra tekrar")
                time.sleep(2 ** deneme)
