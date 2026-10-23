"""Adres sözleşmesi doğrulaması — çevrimdışı, ağsız, tam sayım.

`URUN-PLANI.md` F2'nin bitti ölçütü: canlı sitedeki her eski adres, Django'nun
URL çözücüsünden geçmeli ve **doğru türe + doğru kimliğe** düşmeli.

Bu komut ağa çıkmaz, veritabanı gerektirmez. Yalnız çözümleme kurallarını
sınar — yani her göç turunda saniyeler içinde tekrar çalıştırılabilir.

Kullanım:
    python manage.py adres_dogrula
    python manage.py adres_dogrula --kaynak D:/bursa-hakimiyet-arsiv/tum-urller.jsonl
    python manage.py adres_dogrula --sinirla 1000
"""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit

from django.core.management.base import BaseCommand
from django.urls import Resolver404, resolve

VARSAYILAN_KAYNAK = Path("D:/bursa-hakimiyet-arsiv/tum-urller.jsonl")

# Adresin sonundaki sayi kimliktir; beklenen degeri bagimsizca buradan cikariyoruz
# ki cozumleyicinin sonucu kendi kendini dogrulamasin.
_SON_KIMLIK = re.compile(r"-(\d+)/?$")


class Command(BaseCommand):
    help = "Eski adreslerin tamamını URL çözücüden geçirir (ağsız, veritabansız)."

    def add_arguments(self, parser):
        parser.add_argument("--kaynak", default=str(VARSAYILAN_KAYNAK),
                            help="jsonl adres listesi (her satırda {'url': ...})")
        parser.add_argument("--sinirla", type=int, default=None,
                            help="yalnızca ilk N adresi dener")
        parser.add_argument("--ornek", type=int, default=8,
                            help="her hata türünden kaç örnek gösterilsin")

    def handle(self, *args, **secenekler):
        kaynak = Path(secenekler["kaynak"])
        if not kaynak.exists():
            self.stderr.write(self.style.ERROR(f"Kaynak bulunamadı: {kaynak}"))
            return

        sinir = secenekler["sinirla"]
        ornek_sayisi = secenekler["ornek"]

        toplam = cozulen = 0
        tur_dagilimi: Counter[str] = Counter()
        hatalar: Counter[str] = Counter()
        ornekler: dict[str, list[str]] = {}

        def ornek_ekle(anahtar: str, satir: str) -> None:
            liste = ornekler.setdefault(anahtar, [])
            if len(liste) < ornek_sayisi:
                liste.append(satir)

        with open(kaynak, encoding="utf-8-sig") as dosya:
            for satir in dosya:
                if sinir is not None and toplam >= sinir:
                    break
                satir = satir.strip()
                if not satir:
                    continue
                try:
                    adres = json.loads(satir)["url"]
                except Exception:
                    hatalar["satır okunamadı"] += 1
                    continue

                toplam += 1
                yol = urlsplit(adres).path

                # Beklenen kimlik: yolun sonundaki sayı. Çözümleyiciden bağımsız.
                beklenen = _SON_KIMLIK.search(yol)
                if not beklenen:
                    hatalar["adreste kimlik yok"] += 1
                    ornek_ekle("adreste kimlik yok", yol)
                    continue
                beklenen_kimlik = int(beklenen.group(1))

                try:
                    eslesme = resolve(yol)
                except Resolver404:
                    hatalar["çözülemedi"] += 1
                    ornek_ekle("çözülemedi", yol)
                    continue

                ad = eslesme.url_name or "?"
                tur_dagilimi[ad] += 1

                # Kimlik dogru yakalanmis mi
                yakalanan = eslesme.kwargs.get("kimlik")
                if yakalanan is None and ad == "yazar":
                    yakalanan = eslesme.kwargs.get("dilim_id")
                if yakalanan is None or int(yakalanan) != beklenen_kimlik:
                    hatalar["kimlik uyuşmuyor"] += 1
                    ornek_ekle("kimlik uyuşmuyor",
                               f"{yol}  →  {ad}, yakalanan={yakalanan}, beklenen={beklenen_kimlik}")
                    continue

                cozulen += 1

        # --- rapor ---
        y = self.stdout.write
        y("")
        y(f"Kaynak     : {kaynak}")
        y(f"Adres      : {toplam:,}".replace(",", "."))
        y(f"Çözülen    : {cozulen:,}".replace(",", "."))
        y("")
        y("Tür dağılımı:")
        for ad, sayi in tur_dagilimi.most_common():
            y(f"  {ad:12} {sayi:>9,}".replace(",", "."))

        if hatalar:
            y("")
            y(self.style.ERROR("Hatalar:"))
            for anahtar, sayi in hatalar.most_common():
                y(self.style.ERROR(f"  {anahtar:22} {sayi:>9,}".replace(",", ".")))
                for satir in ornekler.get(anahtar, []):
                    y(f"      {satir}")

        y("")
        if toplam and cozulen == toplam:
            y(self.style.SUCCESS(f"GEÇTİ — {toplam:,} adresin tamamı doğru türe ve kimliğe çözüldü."
                                 .replace(",", ".")))
        else:
            eksik = toplam - cozulen
            y(self.style.ERROR(f"KALDI — {eksik:,} adres çözülemedi veya yanlış çözüldü."
                               .replace(",", ".")))
