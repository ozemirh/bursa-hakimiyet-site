"""Sitemap dosyalarını diske yazar.

    python manage.py site_haritasi_uret
    python manage.py site_haritasi_uret --kuru          # yazmaz, sayar
    python manage.py site_haritasi_uret --aile haber
    python manage.py site_haritasi_uret --ay 2026-08
    python manage.py site_haritasi_uret --kok D:/yayin/static/sitemap

Canlı sitede bu dosyalar **statik**tir; web sunucusu servis eder ve
tarayıcı isteği veritabanına hiç inmez. Bu komut günde bir (ya da yayın
sonrası) çalıştırılıp dosyaları tazeler.

**`ANALYZE` neden var.** Ölçüm (27 Ağustos 2026, gerçek veritabanı,
92.666 kayıt): aylık sorgu `WHERE durum=1 AND yayin_zamani BETWEEN …`
biçiminde ve SQLite istatistik yokken `durum` dizinini seçip her ay için
bütün tabloyu tarıyor — bir ay **0,32 sn**. `yayin_zamani` dizini
kullanıldığında aynı ay **0,06 sn**. 556.824 satırlık denemede fark daha
da açılıyor: 0,129 sn → 0,014 sn. `ANALYZE` bir kez çalışıp
`sqlite_stat1` tablosunu doldurunca planlayıcı doğru dizini kendisi
seçiyor ve komutun kendisi 0,1 sn sürüyor. `--cozumleme-yok` ile
kapatılabilir.
"""

from __future__ import annotations

import time
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import connection

from besleme import ayarlar, siteharitasi
from besleme.aileler import aile as aile_bul
from besleme.aileler import dosya_adi, kayitli_aileler


class Command(BaseCommand):
    help = "Beş sitemap ailesinin aylık dosyalarını ve indeksi üretir."

    def add_arguments(self, ayristirici):
        ayristirici.add_argument(
            "--kok", default=None,
            help="Çıktı klasörü. Varsayılan: <BASE_DIR>/statik/sitemap "
                 "(BH_SITE_HARITASI_KOK ile de verilebilir).")
        ayristirici.add_argument(
            "--aile", action="append", default=None,
            help="Yalnız bu aile(ler). Birden çok kez verilebilir.")
        ayristirici.add_argument(
            "--ay", action="append", default=None,
            help="Yalnız bu ay(lar), YYYY-AA. Verilirse indeks yazılmaz.")
        ayristirici.add_argument(
            "--site-koku", default=None,
            help="Adreslerin başına konacak kök. Varsayılan: ayarlardaki "
                 "SITE_KOKU ya da canlı alan adı.")
        ayristirici.add_argument(
            "--kuru", action="store_true",
            help="Dosya yazmaz; yalnız ay ve adres sayılarını raporlar.")
        ayristirici.add_argument(
            "--cozumleme-yok", action="store_true",
            help="SQLite ANALYZE adımını atlar.")

    def handle(self, *args, **secenekler):
        aileler = self._aileleri_sec(secenekler["aile"])
        if not aileler:
            raise CommandError(
                "Deftere kayıtlı aile yok. `besleme` INSTALLED_APPS içinde mi?")

        kok_adres = secenekler["site_koku"] or ayarlar.site_koku()
        kok_adres = kok_adres.rstrip("/")
        klasor = Path(secenekler["kok"]) if secenekler["kok"] else ayarlar.cikti_koku_yolu()
        kuru = secenekler["kuru"]
        istenen_aylar = set(secenekler["ay"] or [])

        if not secenekler["cozumleme_yok"]:
            self._cozumle()

        if not kuru:
            klasor.mkdir(parents=True, exist_ok=True)

        baslangic = time.perf_counter()
        ozetler: dict[str, list] = {}
        toplam_adres = 0
        toplam_bayt = 0
        uyarilar: list[str] = []

        for aile in aileler:
            t0 = time.perf_counter()
            aylar = aile.aylar()
            if istenen_aylar:
                aylar = [o for o in aylar if o.ay in istenen_aylar]
            ozetler[aile.anahtar] = aylar
            aile_adres = 0
            aile_bayt = 0

            for ozet in aylar:
                ad = dosya_adi(aile, ozet.ay)
                if ozet.adet > siteharitasi.ADRES_SINIRI:
                    uyarilar.append(
                        f"{ad}: {ozet.adet:n} adres — sitemaps.org sınırı "
                        f"{siteharitasi.ADRES_SINIRI:n}. Dosya bölünmedi; "
                        f"bölmek dosya adını değiştirir ve kayıtlı "
                        f"adresleri kırar. Karar gerekiyor.")
                if kuru:
                    aile_adres += ozet.adet
                    continue
                sayac: dict = {}
                bayt = siteharitasi.dosyaya_yaz(
                    klasor / ad,
                    siteharitasi.aylik_parcalar(kok_adres, aile, ozet.ay, sayac))
                yazilan = sayac.get("adet", 0)
                if yazilan != ozet.adet:
                    # Özet sorgusu ile yazma sorgusu arasında kayıt
                    # eklenmiş/çıkmış olabilir. Sessiz geçmiyoruz: F8
                    # ölçütü sayı eşitliği üzerine kurulu.
                    uyarilar.append(
                        f"{ad}: özet {ozet.adet}, yazılan {yazilan} — "
                        f"üretim sırasında kayıt değişti.")
                aile_adres += yazilan
                aile_bayt += bayt

            sure = time.perf_counter() - t0
            toplam_adres += aile_adres
            toplam_bayt += aile_bayt
            self.stdout.write(
                f"{aile.ad:<14} {len(aylar):>3} ay  {aile_adres:>9,} adres"
                f"  {aile_bayt / 1_048_576:>8.1f} MB  {sure:>7.1f} sn"
                .replace(",", "."))

        # Google News dosyası: yalnız haber ailesi verir, yalnız son 48 saat.
        gn_adet = 0
        haber = aile_bul("haber")
        if haber is not None and haber.son_kayitlar is not None and not istenen_aylar:
            sayac = {}
            if kuru:
                gn_adet = sum(1 for _ in haber.son_kayitlar(48))
            else:
                siteharitasi.dosyaya_yaz(
                    klasor / siteharitasi.GOOGLE_NEWS_ADI,
                    siteharitasi.google_news_parcalari(kok_adres, haber, 48, sayac))
                gn_adet = sayac.get("adet", 0)
            self.stdout.write(
                f"{'googleNews':<14}   -      {gn_adet:>9,} adres (son 48 saat)"
                .replace(",", "."))

        # İndeks en sonda: aylık dosyalar hazır olmadan indeks yayımlamak,
        # arama motoruna var olmayan dosyaları göstermek demek.
        if not kuru and not istenen_aylar:
            siteharitasi.dosyaya_yaz(
                klasor / siteharitasi.INDEKS_ADI,
                siteharitasi.indeks_parcalari(kok_adres, ozetler, aileler))

        sure = time.perf_counter() - baslangic
        self.stdout.write("")
        self.stdout.write(
            f"TOPLAM {toplam_adres:,} adres · {toplam_bayt / 1_048_576:.1f} MB "
            f"· {sure:.1f} sn".replace(",", "."))
        if not kuru:
            self.stdout.write(f"Klasör: {klasor}")
        if istenen_aylar:
            self.stdout.write(self.style.WARNING(
                "Tek ay üretildi; indeks yazılmadı (eksik indeks yayımlamamak için)."))
        for uyari in uyarilar:
            self.stdout.write(self.style.WARNING("UYARI: " + uyari))

    # -- yardımcılar --

    def _aileleri_sec(self, istenen):
        kayitli = kayitli_aileler()
        if not istenen:
            return kayitli
        secili = []
        for anahtar in istenen:
            bulunan = aile_bul(anahtar)
            if bulunan is None:
                raise CommandError(
                    f"{anahtar!r} ailesi deftere kayıtlı değil. "
                    f"Kayıtlılar: {', '.join(a.anahtar for a in kayitli) or '(yok)'}")
            secili.append(bulunan)
        return secili

    def _cozumle(self):
        """SQLite'ın sorgu planlayıcısına istatistik verir. Bkz. dosya başı."""
        if connection.vendor != "sqlite":
            return
        t0 = time.perf_counter()
        with connection.cursor() as imlec:
            imlec.execute("ANALYZE")
        self.stdout.write(f"ANALYZE: {time.perf_counter() - t0:.1f} sn")
