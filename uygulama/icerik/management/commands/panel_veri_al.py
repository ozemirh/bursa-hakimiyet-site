"""Panel dökümündeki gerçek kayıtları dokuz yeni tablonun beşine aktarır.

KAYNAK. `C:\\Users\\Asus\\Downloads\\bursa_hakimiyet_panel` — mevcut panelin
tarayıcıyla kaydedilmiş sayfaları. Sayfa numaraları dökümü alan kişinin
gezinme sırasından geliyor ve yeniden kaydedilirse değişir; bu yüzden komut
dosya adına değil **tablo başlığı imzasına** bakarak eşleştirir.

NE ALINIYOR — hepsi ölçüldü, hiçbiri tahmin:

  tablo               döküm       durum
  ----------------------------------------------------------------
  Gazete              17 / 17     tam
  ResmiIlan           24 / 24     tam
  ReklamYuvasi        50 / 50     tam (reklam alanı açılır listesinden)
  ReklamKampanyasi    25 / 131    EKSİK — döküm listenin 1. sayfası
  Bildirim            25 / 2.208  EKSİK — döküm listenin 1. sayfası

Eksik olanlar bilerek alınıyor: ekran boş dururken 25 gerçek satır, sıfır
satırdan çok şey gösteriyor. Ama "tablo dolduruldu" denmiyor; komut her
tablo için **döküm toplamını** basıyor ve eksikse uyarıyor.

ALINMAYANLAR ve neden:
  * `Yorum` · `LogKaydi` — okur yorumları ve giriş kayıtları IP adresi
    taşıyor. Kişisel veriyi demo doldurmak için taşımak ayrı bir karar;
    kullanıcıya sorulmadan yapılmaz.
  * `IkiAdimli` — gizli anahtar saklama kararı bekliyor (§24.10).
  * `SonDakika` — dökümde liste sayfası değil ekleme formu var; satır yok.

DURUM KODLARI dökümün kendi JS'inden okundu (`row[8] == 1|2`, `== 4`):
1 Aktif · 2 Pasif · 4 Arşiv — Django modellerindeki değerlerle birebir aynı.
Renk değil kod esas alındı; yeşil düğme "aktif yap" değil "aktif" demek.

EDİTÖR ADI BAĞLANMIYOR. Dökümde editör adı var ("Coşkun SAİTOĞLU") ama
gerçek kullanıcı tablosu henüz göçmedi (F5(d) `usertype_list` dökümünü
bekliyor). `olusturan` boş bırakılıp sayılıyor; ada bakıp kullanıcı
uydurulmuyor.

Kullanım:
    python manage.py panel_veri_al --kuru
    python manage.py panel_veri_al
"""

from __future__ import annotations

import html
import re
from datetime import datetime
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from icerik.models import (Bildirim, Gazete, ReklamKampanyasi, ReklamYuvasi,
                           ResmiIlan, Yorum)

VARSAYILAN = Path(r"C:\Users\Asus\Downloads\bursa_hakimiyet_panel")

# Tabloyu basligindan taniyoruz; dosya adi degisebilir, sozlesme degismez.
IMZALAR = {
    "gazete": ["", "Başlık", "BIK Kodu", "İşlemler"],
    "ilan": ["", "ID", "Başlık", "İlan Türü", "Tarih", "Editör", "İşlemler"],
    "kampanya": ["", "Başlık", "Fotoğraf", "Başlangıç / Bitiş Tarihi",
                 "Reklam Alanı", "Editör", "İşlemler"],
    "bildirim": ["Tarih", "Veri Kaynağı", "Bildirim", "Yaklaşık Hedef Kişi",
                 "Açan Kişi", "İşlemler"],
}

# Hangi tablo hangi dokum sayfasindan geliyor (rapor satiri icin).
SAYFA_ANAHTARI = {
    "Gazete": "gazete", "ResmiIlan": "ilan", "ReklamYuvasi": "kampanya",
    "ReklamKampanyasi": "kampanya", "Bildirim": "bildirim",
}

# Ilan turu sutunundaki metin -> model anahtari.
ILAN_TURLERI = {
    "İHALE": ResmiIlan.TUR_IHALE, "TEBLİGAT": ResmiIlan.TUR_TEBLIGAT,
    "İCRA": ResmiIlan.TUR_ICRA, "PERSONEL ALIMI": ResmiIlan.TUR_PERSONEL,
}

# Bildirimin "Veri Kaynagi" sutunu iki deger aliyor (§24.9); ikisi de haber
# tarafina bakiyor, ayri bir icerik turumuz yok.
BILDIRIM_KAYNAK = {"Makale": Yorum.TUR_HABER, "Haber": Yorum.TUR_HABER}

_OLCU = re.compile(r"(\d{3,4})\s*[x*]\s*(\d{2,4})")
_KONUM = re.compile(r"^-([^-]+)-")
_KAMPANYA_ID = re.compile(r"advertisement_edit\.php\?id=(\d+)")
_TOPLAM = re.compile(r"\d[\d.]*\s*-\s*\d[\d.]*\s*/\s*([\d.]+)\s*arasındaki kayıtlar")
YER_TUTUCU = "Bu alana reklam verebilirsiniz"


def _duz(parca: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", parca))).strip()


def _sayi(ham: str) -> int:
    rakam = re.sub(r"[^\d]", "", ham or "")
    return int(rakam) if rakam else 0


def _tarih_gt(ham: str):
    """`24-08-2026` ya da `24-08-2026 00:00:00` -> date."""
    try:
        return datetime.strptime((ham or "").strip()[:10], "%d-%m-%Y").date()
    except ValueError:
        return None


def _zaman_iso(ham: str):
    try:
        naif = datetime.strptime((ham or "").strip(), "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None
    return timezone.make_aware(naif, timezone.get_default_timezone())


class Command(BaseCommand):
    help = "Panel dökümündeki gerçek kayıtları ilgili tablolara aktarır."

    def add_arguments(self, parser):
        parser.add_argument("--dokum", default=str(VARSAYILAN))
        parser.add_argument("--kuru", action="store_true",
                            help="yazmaz, yalnız ne olacağını sayar")

    # -- döküm okuma ------------------------------------------------------

    def _sayfalari_tara(self, kok: Path) -> dict:
        """{imza adı: (satırlar, döküm toplamı, dosya adı)}."""
        bulunan: dict = {}
        for yol in sorted(kok.glob("*.html")):
            metin = yol.read_text(encoding="utf-8", errors="replace")
            for tablo in re.findall(r"<table[^>]*>(.*?)</table>", metin, re.S):
                satirlar = re.findall(r"<tr[^>]*>(.*?)</tr>", tablo, re.S)
                if not satirlar:
                    continue
                bas = [_duz(h) for h in re.findall(
                    r"<t[hd][^>]*>(.*?)</t[hd]>", satirlar[0], re.S)]
                for ad, imza in IMZALAR.items():
                    if bas == imza and ad not in bulunan:
                        esle = _TOPLAM.search(metin)
                        bulunan[ad] = (satirlar[1:],
                                       _sayi(esle.group(1)) if esle else 0,
                                       yol.name)
        return bulunan

    @staticmethod
    def _hucreler(satir: str) -> list:
        return [_duz(h) for h in
                re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>", satir, re.S)]

    @staticmethod
    def _durum(satir: str, arsivli_mi: bool = False) -> int:
        """Dökümün kendi JS'inin ürettiği düğmeden durum kodu."""
        if 'data-bs-title="Aktif"' in satir:
            return 1
        if 'data-bs-title="Pasif"' in satir:
            return 2
        if arsivli_mi and "Arşivden çıkar" in satir:
            return 4
        return 2

    # -- ayıklayıcılar ----------------------------------------------------

    def _gazeteler(self, satirlar) -> list:
        kayit = []
        for sira, satir in enumerate(satirlar, start=1):
            h = self._hucreler(satir)
            if len(h) < 3 or not h[1]:
                continue
            kayit.append(dict(ad=h[1], bik_kodu=h[2], sira=sira,
                              aktif=self._durum(satir) == 1,
                              bizim_mi=h[2] == "YYN-000132"))
        return kayit

    def _ilanlar(self, satirlar) -> list:
        kayit = []
        for satir in satirlar:
            h = self._hucreler(satir)
            if len(h) < 5 or not h[2]:
                continue
            kayit.append(dict(pk=_sayi(h[1]) or None, baslik=h[2],
                              tur=ILAN_TURLERI.get(h[3], ResmiIlan.TUR_IHALE),
                              yayin_tarihi=_tarih_gt(h[4]),
                              durum=self._durum(satir, arsivli_mi=True)))
        return kayit

    @staticmethod
    def _cihaz(ad: str) -> str:
        kucuk = ad.replace("İ", "i").lower()
        if "mobil" in kucuk or "mobile" in kucuk:
            return ReklamYuvasi.CIHAZ_MOBIL
        if "web" in kucuk or "masaüstü" in kucuk or "desktop" in kucuk:
            return ReklamYuvasi.CIHAZ_MASAUSTU
        return ReklamYuvasi.CIHAZ_HEPSI

    def _yuvalar(self, kok: Path) -> list:
        """50 yuva, kampanya sayfasındaki 'Reklam Alanı Seç' listesinden.

        Yuvaların ayrı bir liste ekranı dökümde yok; tek tam kaynak bu
        açılır liste. Ölçü/konum çıkarılamayan yuvada alan BOŞ bırakılır.
        """
        for yol in sorted(kok.glob("*.html")):
            metin = yol.read_text(encoding="utf-8", errors="replace")
            for sec in re.findall(r"<select[^>]*>(.*?)</select>", metin, re.S):
                adlar = [_duz(o) for o in
                         re.findall(r"<option[^>]*>(.*?)</option>", sec, re.S)]
                if not adlar or adlar[0] != "Reklam Alanı Seç":
                    continue
                kayit = []
                for ad in adlar[1:]:
                    olcu = _OLCU.search(ad)
                    konum = _KONUM.match(ad)
                    kayit.append(dict(
                        ad=ad,
                        konum=konum.group(1).strip() if konum else "",
                        genislik=int(olcu.group(1)) if olcu else None,
                        yukseklik=int(olcu.group(2)) if olcu else None,
                        cihaz=self._cihaz(ad),
                        yer_tutucu_mu=ad.startswith(YER_TUTUCU)))
                return kayit
        return []

    def _kampanyalar(self, satirlar) -> list:
        kayit = []
        for satir in satirlar:
            h = self._hucreler(satir)
            if len(h) < 5 or not h[1]:
                continue
            # Ekranda "/ -..." diye kisalan yuva listesinin TAMAMI ipucunda.
            ipucu = re.search(r'data-bs-title="([^"]*[x*]\d[^"]*)"', satir)
            ham_yuva = html.unescape(ipucu.group(1)) if ipucu else h[4]
            kimlik = _KAMPANYA_ID.search(satir)
            tarih = h[3].split("/")
            kayit.append(dict(
                pk=int(kimlik.group(1)) if kimlik else None,
                baslik=h[1],
                yuva_adlari=[p.strip() for p in ham_yuva.split(" / ") if p.strip()],
                baslangic=_tarih_gt(tarih[0]) if tarih else None,
                bitis=_tarih_gt(tarih[1]) if len(tarih) > 1 else None,
                durum=self._durum(satir)))
        return kayit

    def _bildirimler(self, satirlar) -> list:
        kayit = []
        for satir in satirlar:
            h = self._hucreler(satir)
            if len(h) < 5 or not h[2]:
                continue
            kayit.append(dict(
                gonderim_zamani=_zaman_iso(h[0]),
                icerik_turu=BILDIRIM_KAYNAK.get(h[1], Yorum.TUR_HABER),
                baslik=h[2][:Bildirim.BASLIK_SINIRI],
                hedef_sayisi=_sayi(h[3]), acan_sayisi=_sayi(h[4])))
        return kayit

    # -- akış -------------------------------------------------------------

    def handle(self, *args, **s):
        kok = Path(s["dokum"])
        y = self.stdout.write
        if not kok.exists():
            self.stderr.write(self.style.ERROR(f"Döküm yok: {kok}"))
            return

        sayfa = self._sayfalari_tara(kok)
        yok = [ad for ad in IMZALAR if ad not in sayfa]
        if yok:
            self.stderr.write(self.style.WARNING(
                f"Dökümde bulunamayan tablo: {', '.join(yok)}"))

        veriler = {
            "Gazete": self._gazeteler(sayfa["gazete"][0]) if "gazete" in sayfa else [],
            "ResmiIlan": self._ilanlar(sayfa["ilan"][0]) if "ilan" in sayfa else [],
            "ReklamYuvasi": self._yuvalar(kok),
            "ReklamKampanyasi": (self._kampanyalar(sayfa["kampanya"][0])
                                 if "kampanya" in sayfa else []),
            "Bildirim": (self._bildirimler(sayfa["bildirim"][0])
                         if "bildirim" in sayfa else []),
        }

        y("")
        y(f"  {'tablo':20} {'okunan':>7} {'dökümde':>9}  kaynak")
        for ad, veri in veriler.items():
            _, toplam, dosya = sayfa.get(SAYFA_ANAHTARI[ad], ([], 0, "—"))
            if ad == "ReklamYuvasi":       # acilir listenin kendisi tam kaynak
                toplam = len(veri)
            im = "" if len(veri) == toplam else "  ← EKSİK, dökümde 1. sayfa var"
            y(f"  {ad:20} {len(veri):>7} {toplam:>9}  {dosya}{im}")

        # Ölçülemeyen alanlar sayılır, uydurulmaz.
        yuvalar = veriler["ReklamYuvasi"]
        kampanyalar = veriler["ReklamKampanyasi"]
        # Üç alan AYRI sayılıyor: birleştirilmiş bir "üçlü tam" sayısı,
        # cihazın varsayılanı ("hepsi") ölçülmüş mü boş mu ayırt edilemediği
        # için yanıltıcı olurdu.
        y("")
        y(f"  yuva: konumu olan {sum(1 for v in yuvalar if v['konum'])}"
          f" · ölçüsü olan {sum(1 for v in yuvalar if v['genislik'])}"
          f" · cihazı yazılı {sum(1 for v in yuvalar if v['cihaz'] != 'hepsi')}"
          f" · yer tutucu {sum(1 for v in yuvalar if v['yer_tutucu_mu'])}"
          f"  (toplam {len(yuvalar)})")
        y(f"  kampanya: birden çok yuvalı "
          f"{sum(1 for k in kampanyalar if len(k['yuva_adlari']) > 1)}")

        if s["kuru"]:
            y("\n  --kuru: hiçbir şey yazılmadı.\n")
            return

        bagsiz: list = []
        with transaction.atomic():
            for k in veriler["Gazete"]:
                Gazete.objects.update_or_create(ad=k["ad"], defaults=k)
            for k in veriler["ResmiIlan"]:
                alan = dict(k)
                ResmiIlan.objects.update_or_create(pk=alan.pop("pk"), defaults=alan)
            for k in yuvalar:
                ReklamYuvasi.objects.update_or_create(ad=k["ad"], defaults=k)

            dizin = {v.ad: v for v in ReklamYuvasi.objects.all()}
            for k in kampanyalar:
                alan = dict(k)
                adlar = alan.pop("yuva_adlari")
                kampanya, _ = ReklamKampanyasi.objects.update_or_create(
                    pk=alan.pop("pk"), defaults=alan)
                kampanya.yuvalar.set([dizin[a] for a in adlar if a in dizin])
                bagsiz.extend(a for a in adlar if a not in dizin)

            for k in veriler["Bildirim"]:
                Bildirim.objects.update_or_create(
                    baslik=k["baslik"], gonderim_zamani=k["gonderim_zamani"],
                    defaults=k)

        y("")
        y(f"  yazıldı: gazete {Gazete.objects.count()}"
          f" · ilan {ResmiIlan.objects.count()}"
          f" · yuva {ReklamYuvasi.objects.count()}"
          f" · kampanya {ReklamKampanyasi.objects.count()}"
          f" · bildirim {Bildirim.objects.count()}")
        if bagsiz:
            self.stderr.write(self.style.WARNING(
                f"  Yuva listesinde karşılığı olmayan {len(set(bagsiz))} ad: "
                f"{sorted(set(bagsiz))}"))
        y("")
