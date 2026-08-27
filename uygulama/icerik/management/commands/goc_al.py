"""Arşivden haber göçü.

Kaynak: `D:/bursa-hakimiyet-arsiv/veri/<YIL-AY>/<id>.json` — canlı siteden
kazınan haberler.

Tasarım kararları:

- **Kimlik korunur.** `id` doğrudan yazılır; adres deseni `/{kategori}/{slug}-{id}`
  olduğu için kimliği değiştirmek her eski bağlantıyı kırardı.
- **Slug adresten çıkarılır**, başlıktan üretilmez. Başlıktan üretmek 556.824
  adresin bir kısmını kaydırırdı; adres kanonik kaynaktır.
- **Kaynak eşleşmezse kayıt düşmez.** Bilinmeyen kaynak adı `Kaynak` tablosuna
  eklenir ve raporda sayılır.
- **Yeniden çalıştırılabilir.** Var olan kaydı günceller.
- `gorsel_url` yalnız izdir; 2023-07 öncesi dosyalar sunucuda yok.

Kullanım:
    python manage.py goc_al
    python manage.py goc_al --sinirla 500 --kuru
"""

from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from icerik.goc_kaynak import kaynak_kabul
from icerik.models import Haber
from taksonomi.models import Kategori, KategoriTur, Kaynak

VARSAYILAN = Path("D:/bursa-hakimiyet-arsiv/veri")

# Adresin sonundaki `-{id}` cikarilinca kalan sey slug'dir.
_ADRES = re.compile(r"/([^/]+)/(?P<slug>[^/]+?)-(?P<id>\d+)/?$")
_TARIH = re.compile(r"^(\d{4}-\d{2}-\d{2})[T ](\d{2}:\d{2}:\d{2})")

# Kaynak baglarinin yazildigi parca boyu (bkz. asagidaki kilit notu).
PARCA = 20_000


def _zaman(ham: str):
    if not ham:
        return None
    esle = _TARIH.match(ham.strip())
    if not esle:
        return None
    try:
        naif = datetime.fromisoformat(f"{esle.group(1)}T{esle.group(2)}")
    except ValueError:
        return None
    return timezone.make_aware(naif, timezone.get_default_timezone())


class Command(BaseCommand):
    help = "Kazınan haber arşivini veritabanına aktarır."

    def add_arguments(self, parser):
        parser.add_argument("--kaynak", default=str(VARSAYILAN))
        parser.add_argument("--sinirla", type=int, default=None)
        parser.add_argument("--kuru", action="store_true",
                            help="yazmaz, yalnız ne olacağını sayar")
        parser.add_argument("--yigin", type=int, default=2000)
        parser.add_argument(
            "--yalniz-yeni", action="store_true",
            help="Veritabaninda kimligi bulunan dosyalari hic okumadan atlar. "
                 "Tarama surerken tazeleme kosusunu kisaltir; var olan kaydin "
                 "govdesini YENILEMEZ.")

    def handle(self, *args, **s):
        kok = Path(s["kaynak"])
        if not kok.exists():
            self.stderr.write(self.style.ERROR(f"Kaynak yok: {kok}"))
            return

        # Kategori slug -> Kategori (haber turu)
        slug_kategori = {
            kt.slug: kt.kategori
            for kt in KategoriTur.objects.filter(tur=Kategori.TUR_HABER).select_related("kategori")
        }
        kaynak_onbellek = {k.ad.casefold(): k for k in Kaynak.objects.all()}

        dosyalar = sorted(kok.glob("*/*.json"))
        sayac = Counter()

        if s["yalniz_yeni"]:
            # Dosya adi kimligin ta kendisi — 2.000 ornekte dogrulandi
            # (27 Agustos 2026): `<id>.json` ile adresteki `-{id}` birebir
            # ayni. Bu yuzden dosyayi ACMADAN atlayabiliyoruz; tazeleme
            # kosusu 300 bin dosya yerine yalniz yenileri okuyor.
            var_olan = set(Haber.objects.values_list("id", flat=True))
            elenmis = []
            for yol in dosyalar:
                try:
                    kimlik = int(yol.stem)
                except ValueError:
                    elenmis.append(yol)      # adi kimlik degilse yine de oku
                    continue
                if kimlik in var_olan:
                    sayac["atlandi (zaten var)"] += 1
                else:
                    elenmis.append(yol)
            dosyalar = elenmis

        if s["sinirla"]:
            dosyalar = dosyalar[: s["sinirla"]]

        yeni_kaynaklar: set[str] = set()
        ret_nedenleri: Counter = Counter()
        yigin: list[Haber] = []
        kaynak_baglari: list[tuple[int, str]] = []

        def yigin_yaz():
            if not yigin or s["kuru"]:
                yigin.clear()
                return
            with transaction.atomic():
                Haber.objects.bulk_create(
                    yigin, batch_size=1000,
                    update_conflicts=True,
                    update_fields=["slug", "baslik", "spot", "govde", "kategori",
                                   "yayin_zamani", "guncelleme_zamani", "gorsel_url",
                                   "gorsel_alt", "gorsel_var", "gorsel_dosya", "kelime_sayisi",
                                   "eski_url", "goc_guveni"],
                    unique_fields=["id"],
                )
            yigin.clear()

        for yol in dosyalar:
            try:
                d = json.loads(yol.read_text(encoding="utf-8"))
            except Exception:
                sayac["okunamadi"] += 1
                continue

            adres = _ADRES.search(d.get("url") or "")
            if not adres:
                sayac["adres cozulemedi"] += 1
                continue

            kimlik = int(adres.group("id"))
            slug = adres.group("slug")
            kategori = slug_kategori.get((d.get("kategori") or "").strip())
            if kategori is None:
                sayac["kategori taninmadi"] += 1
                continue

            yerel = d.get("yerel_gorseller") or []
            yigin.append(Haber(
                id=kimlik,
                slug=slug[:220],
                baslik=(d.get("baslik") or "")[:300],
                spot=d.get("spot") or "",
                govde=d.get("govde_html") or "",
                kategori=kategori,
                durum=Haber.DURUM_AKTIF,   # sitemap yalniz yayindakileri listeler
                yayin_zamani=_zaman(d.get("yayin_tarihi") or ""),
                guncelleme_zamani=_zaman(d.get("guncelleme_tarihi") or ""),
                gorsel_url=(d.get("gorsel_url") or "")[:600],
                gorsel_alt=(d.get("gorsel_alt") or "")[:300],
                gorsel_var=bool(yerel),
                gorsel_dosya=(yerel[0] if yerel else "")[:300],
                kelime_sayisi=int(d.get("kelime_sayisi") or 0),
                eski_url=(d.get("url") or "")[:600],
                goc_guveni=(d.get("ayiklama_guveni") or "")[:12],
            ))
            sayac["alindi"] += 1
            if not yerel:
                sayac["gorselsiz"] += 1

            # Kaynak alani guvenilmez; kapidan gecen deger baglanir.
            # Gerekce ve olcum: icerik/goc_kaynak.py
            ad = (d.get("kaynak") or "").strip()
            if ad:
                kabul, neden = kaynak_kabul(ad)
                if kabul:
                    kaynak_baglari.append((kimlik, ad))
                    if ad.casefold() not in kaynak_onbellek:
                        yeni_kaynaklar.add(ad)
                else:
                    sayac["kaynak reddi"] += 1
                    ret_nedenleri[neden] += 1

            if len(yigin) >= s["yigin"]:
                yigin_yaz()

        yigin_yaz()

        # Kaynaklari kur ve bagla
        if not s["kuru"]:
            for ad in sorted(yeni_kaynaklar):
                nesne, _ = Kaynak.objects.get_or_create(ad=ad[:120])
                kaynak_onbellek[ad.casefold()] = nesne
            ara = Haber.kaynaklar.through
            baglar = [
                ara(haber_id=hid, kaynak_id=kaynak_onbellek[ad.casefold()].id)
                for hid, ad in kaynak_baglari
                if ad.casefold() in kaynak_onbellek
            ]
            # Tek islemde 265 bin satir yazmak veritabanini uzun sure kilitler;
            # SQLite `delete` gunlugunde yazar okuyucuyu bloklar ve ayni dosyayi
            # okuyan diger surecler "database is locked" alir. Parca parca ve
            # HER PARCA AYRI ISLEMDE yazilir: kilit sureleri kisa kalir.
            for bas in range(0, len(baglar), PARCA):
                with transaction.atomic():
                    ara.objects.bulk_create(
                        baglar[bas:bas + PARCA], batch_size=2000,
                        ignore_conflicts=True)
            sayac["kaynak bagi"] = len(baglar)

        y = self.stdout.write
        y("")
        y(f"Kaynak klasör : {kok}")
        y(f"Dosya         : {len(dosyalar):,}".replace(",", "."))
        for anahtar in ("alindi", "gorselsiz", "kaynak bagi", "atlandi (zaten var)",
                        "kategori taninmadi", "adres cozulemedi", "okunamadi"):
            if sayac.get(anahtar):
                y(f"  {anahtar:20} {sayac[anahtar]:>9,}".replace(",", "."))
        if yeni_kaynaklar:
            y(f"  yeni kaynak kaydı    {len(yeni_kaynaklar):>9}")
        for neden, adet in ret_nedenleri.most_common():
            y(f"    kaynak reddi · {neden:22} {adet:>7,}".replace(",", "."))
        if s["kuru"]:
            y(self.style.WARNING("KURU ÇALIŞMA — hiçbir şey yazılmadı."))
        else:
            y("")
            y(self.style.SUCCESS(f"Veritabanında toplam haber: {Haber.objects.count():,}"
                                 .replace(",", ".")))
