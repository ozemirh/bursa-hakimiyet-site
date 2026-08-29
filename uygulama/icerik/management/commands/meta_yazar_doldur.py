"""Arşivin `kaynak` alanından `meta_yazar` ve `kaynak_turu` doldurur.

NEDEN ARŞİVİ OKUYOR. Kaynak kapısı (`icerik/goc_kaynak.py`) meta yazar
değerlerini bağ kurmadan **eliyor**, o yüzden veritabanında izleri yok:
"Haber Merkezi" damgalı bir haberle kaynağı hiç okunamamış bir haber bugün
birbirinden ayırt edilemiyor. Ayrım yalnız arşiv JSON'undaki `kaynak`
alanında duruyor; bu yüzden komut arşivi bir kez baştan sona okur.

SINIFLANDIRMA — hepsi ölçüme dayanır, tahmin yok:

  kaynak alanı           -> meta_yazar        kaynak_turu
  ---------------------------------------------------------------
  "Haber Merkezi"           haber_merkezi      DOKUNULMAZ
  "Bülten"                  bulten             DOKUNULMAZ
  kendi yazarımızın adı     fikir_iscisi       muhabir
  gerçek haber ajansı       haber_ajansi       ajans
  başka bir yayın           alinti             dis_yayin
  çöp / boş                 DOKUNULMAZ         DOKUNULMAZ

"Kendi yazarımız" tahmin değil: `medya.Yazar` tablosuyla ad eşleşmesi.
ÖLÇÜLDÜ (28 Ağustos 2026): kaynak diye kaydedilmiş 4 ad (123 haber) aslında
gazetenin kendi köşe yazarı — `PANEL-NOTLARI.md` §5'in "Coşkun Saitoğlu hem
kaynak listesinde hem editör listesinde" dediği kusurun ta kendisi.

`save()` ÇAĞRILMIYOR — BİLEREK. `QuerySet.update()` kullanılıyor. Sebep
`Haber.save()` içindeki türetim: `meta_yazar = META_TURETIM[kaynak_turu]`.
Bu türetim çalışsaydı, ölçtüğümüz "haber_merkezi" değerini kaynak türünün
varsayılanından (`ajans`) türetip **"haber_ajansi"ye çevirirdi** — yani
kaynağı olmayan 337 bin haberi "ajanstan geldi" diye damgalardı. Ölçülen
olguyu türetimle ezmemek için `update()` doğru araç.

`meta_yazar_elle=True` olan kayıt **hiç güncellenmez**: editörün elle
girdiği değeri otomatik çıkarımla ezmek, bu turda düzelttiğimiz hatanın
aynısı olur. Bugün tablo boş, kural yine de kodda.

Kullanım:
    python manage.py meta_yazar_doldur --kuru
    python manage.py meta_yazar_doldur
"""

from __future__ import annotations

import json
import time
from collections import Counter, defaultdict
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from icerik.goc_kaynak import META_YAZAR_DEGERLERI, kaynak_kabul
from icerik.models import Haber
from medya.models import Yazar

PARCA = 5_000

# Arsivdeki metin -> modeldeki anahtar (Haber.META_YAZARLAR).
METIN_ANAHTAR = {
    "haber merkezi": "haber_merkezi",
    "bülten": "bulten",
    "haber ajansı": "haber_ajansi",
    "fikir işçisi": "fikir_iscisi",
    "içerik aktarımı": "icerik_aktarimi",
    "alıntı/iktibas": "alinti",
}

# DAR ve bilerek dar: yalnizca tartismasiz haber ajanslari. TRT Haber, BBC,
# Milliyet gibi yayin kuruluslari `dis_yayin` sayilir -- PANEL-NOTLARI.md §5
# ayrimi boyle kuruyor ("Halk TV" ornegi dis yayin tarafinda).
AJANSLAR = {
    "aa", "anadolu ajansı", "dha", "demirören haber ajansı",
    "İha", "iha", "ihlas haber ajansı", "İhlas haber ajansı",
    "anka", "reuters", "afp", "ap",
}


def _kucult(metin: str) -> str:
    return "".join({"İ": "i", "I": "ı"}.get(c, c) for c in metin).lower()


class Command(BaseCommand):
    help = "meta_yazar ve kaynak_turu alanlarını arşivdeki kaynak alanından doldurur."

    def add_arguments(self, parser):
        parser.add_argument("--kok", default=str(
            Path(getattr(settings, "ARSIV_KOK", "D:/bursa-hakimiyet-arsiv")) / "veri"))
        parser.add_argument("--kuru", action="store_true",
                            help="yazmaz, yalnız ne olacağını sayar")
        parser.add_argument(
            "--yalniz-yeni", action="store_true",
            help="meta_yazar'ı zaten dolu olan kaydın dosyasını hiç okumaz. "
                 "Göç tazelemesinden sonraki koşuyu kısaltır; ölçülmüş "
                 "değeri yeniden hesaplamaz.")

    def handle(self, *args, **s):
        y = self.stdout.write
        kok = Path(s["kok"])
        basla = time.time()

        yazarlar = {_kucult(a) for a in Yazar.objects.values_list("ad", flat=True)}
        vt = set(Haber.objects.values_list("id", flat=True))
        # Zaten siniflandirilmis kayitlarin dosyasini okumamak icin.
        hazir = (set(Haber.objects.exclude(meta_yazar="")
                     .values_list("id", flat=True)) if s["yalniz_yeni"] else set())

        # hedef (meta_yazar, kaynak_turu|None) -> [id...]
        kova: dict[tuple, list[int]] = defaultdict(list)
        sayac = Counter()
        kaynak_ornek: dict[str, Counter] = defaultdict(Counter)

        for yol in kok.glob("*/*.json"):
            try:
                kimlik = int(yol.stem)
            except ValueError:
                sayac["dosya adi kimlik degil"] += 1
                continue
            if kimlik not in vt:
                sayac["veritabaninda yok (henuz gocmedi)"] += 1
                continue
            if kimlik in hazir:
                sayac["atlandi (meta_yazar zaten dolu)"] += 1
                continue
            try:
                d = json.loads(yol.read_text(encoding="utf-8"))
            except Exception:
                sayac["bozuk json"] += 1
                continue

            ham = (d.get("kaynak") or "").strip()
            kucuk = _kucult(ham)

            if kucuk in METIN_ANAHTAR and kucuk in {
                    _kucult(m) for m in META_YAZAR_DEGERLERI}:
                kova[(METIN_ANAHTAR[kucuk], None)].append(kimlik)
                sayac[f"meta yazar: {METIN_ANAHTAR[kucuk]}"] += 1
                continue

            kabul, _neden = kaynak_kabul(ham)
            if not kabul:
                sayac["belirsiz - dokunulmadi"] += 1
                continue

            if kucuk in yazarlar:
                hedef = ("fikir_iscisi", Haber.KAYNAK_MUHABIR)
                etiket = "kendi muhabirimiz"
            elif kucuk in AJANSLAR:
                hedef = ("haber_ajansi", Haber.KAYNAK_AJANS)
                etiket = "haber ajansi"
            else:
                hedef = ("alinti", Haber.KAYNAK_DIS_YAYIN)
                etiket = "dis yayin"
            kova[hedef].append(kimlik)
            sayac[f"kaynakli: {etiket}"] += 1
            kaynak_ornek[etiket][ham] += 1

        okuma = time.time() - basla

        y("")
        y(f"Arşiv klasörü : {kok}")
        y(f"Okuma süresi  : {okuma:.1f} sn")
        y("")
        for k, n in sorted(sayac.items(), key=lambda x: -x[1]):
            y(f"  {k:38} {n:>9,}".replace(",", "."))

        y("")
        y("  --- kaynaklı kayıtlarda en sık adlar ---")
        for etiket, sayim in kaynak_ornek.items():
            ilk = ", ".join(f"{a} ({n:,})".replace(",", ".")
                            for a, n in sayim.most_common(6))
            y(f"    {etiket:18} {ilk}")

        if s["kuru"]:
            y(self.style.WARNING("\nKURU ÇALIŞMA — hiçbir şey yazılmadı."))
            return

        yazma = time.time()
        guncellenen = Counter()
        korunan = 0
        for (meta, tur), kimlikler in kova.items():
            alanlar = {"meta_yazar": meta}
            if tur is not None:
                alanlar["kaynak_turu"] = tur
            for bas in range(0, len(kimlikler), PARCA):
                dilim = kimlikler[bas:bas + PARCA]
                with transaction.atomic():
                    n = (Haber.objects
                         .filter(id__in=dilim, meta_yazar_elle=False)
                         .update(**alanlar))
                guncellenen[(meta, tur)] += n
                korunan += len(dilim) - n

        y("")
        y(f"Yazma süresi  : {time.time() - yazma:.1f} sn")
        y("")
        y(f"  {'meta_yazar':18} {'kaynak_turu':12} {'guncellenen':>12}")
        for (meta, tur), n in sorted(guncellenen.items(), key=lambda x: -x[1]):
            y(f"  {meta:18} {str(tur or '(dokunulmadi)'):12} {n:>12,}".replace(",", "."))
        y(f"\n  meta_yazar_elle korundu       {korunan:>9,}".replace(",", "."))
        # 356 bin satirlik UPDATE istatistikleri bayatlatir; planlayici bayat
        # istatistikle indeksi birakip tam taramaya donebiliyor (olculdu:
        # ilce sayfasi 745 -> 26 ms). Goc/backfill sonrasi ANALYZE standart adim.
        from django.db import connection
        t_analiz = time.time()
        with connection.cursor() as imlec:
            imlec.execute("ANALYZE")
        y(f"  ANALYZE                       {time.time() - t_analiz:>8.1f} sn")
        y(self.style.SUCCESS(
            f"\nToplam süre {time.time() - basla:.1f} sn"))
