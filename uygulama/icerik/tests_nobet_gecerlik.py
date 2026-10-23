"""Eski nöbet listesi: sayfalarda SON LİSTE gösterilir, haber olarak çıkmaz.

Tarihçe: Paket L1 (19 Ekim 2026) dünden eski listeyi gizliyordu. Aynı
akşam kullanıcı kararı: "güncel veriye sahip olmadığın alanlar için sahip
olduğun son günü göster, boş kalmasın". Kural tek yerde:

* `canli.GECERLIK_GUN` BOŞ — liste dünden eski olsa da basılır; listenin
  hangi güne ait olduğu ve "elimizdeki son liste; bugünkü nöbetçiyi Eczacı
  Odası'ndan doğrulayın" uyarısı yazılır (anasayfa paneli, `/nobetci-eczane`,
  ilçe sayfası servis paneli);
* `tazelik(gecerlik_gun=…)` düzeneği duruyor: bir bileşen yeniden gizlenmek
  istenirse sözlüğe yazılır (sözleşme testleri aşağıda);
* günlük HABER komutu ayrı ve katı: dünden eski liste bayrakla bile haber
  olmaz (`tests_eczane.EczaneHaberi.test_bayat_liste_yayimlanmiyor`).

Puan servis panelinin başlığı: bayat tabloda hafta numarasının yanında
"güncel değil" yazılır.
"""

import json
import shutil
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

from django.test import SimpleTestCase, TestCase, override_settings
from django.utils import timezone

from . import canli, eczane
from .canli import _bellek

ESKI = "2026-09-12T22:12:11+03:00"


def _yerel(gun_once, saat=10):
    gun = timezone.localdate() - timedelta(days=gun_once)
    return timezone.make_aware(datetime.combine(gun, datetime.min.time())
                               + timedelta(hours=saat)).isoformat()


def _eczane(guncelleme, gun="2026-09-12"):
    return {"guncelleme": guncelleme, "bayat_esik_dakika": 1440, "gun": gun,
            "kaynak": {"ad": "Bursa Eczacı Odası", "kisa": "BEO",
                       "adres": "https://www.beo.org.tr/nobetci-eczaneler"},
            "eczaneler": [{"ad": "DENEME ECZANESİ", "ilce": "NİLÜFER",
                           "telefon": "0224 999 88 77", "enlem": 40.2, "boylam": 29.0,
                           "nobet_baslangic": "2026-09-12T18:30",
                           "nobet_bitis": "2026-09-13T08:30"}]}


class GecerlikKurali(SimpleTestCase):
    """Sözleşme: `gecerli` ve `gun_farki`."""

    def test_bugun_ve_dun_gecerli(self):
        for gun_once in (0, 1):
            t = canli.tazelik({"guncelleme": _yerel(gun_once, 0), "bayat_esik_dakika": 1440},
                              gecerlik_gun=1)
            self.assertEqual(t["gun_farki"], gun_once)
            self.assertTrue(t["gecerli"], gun_once)

    def test_dunden_eski_gecersiz(self):
        t = canli.tazelik({"guncelleme": _yerel(2, 23), "bayat_esik_dakika": 1440},
                          gecerlik_gun=1)
        self.assertEqual(t["gun_farki"], 2)
        self.assertFalse(t["gecerli"])
        self.assertEqual(t["durum"], "bayat")

    def test_zamani_bilinmeyen_gecersiz(self):
        self.assertFalse(canli.tazelik({"bayat_esik_dakika": 1440}, gecerlik_gun=1)["gecerli"])

    def test_kurali_olmayan_bilesen_hep_gecerli(self):
        t = canli.tazelik({"guncelleme": ESKI, "bayat_esik_dakika": 2880})
        self.assertEqual(t["durum"], "bayat")
        self.assertTrue(t["gecerli"])

    def test_hicbir_bilesen_gizlenmiyor(self):
        """Kullanıcı kararı: son veri her bileşende gösterilir."""
        self.assertEqual(canli.GECERLIK_GUN, {})

    def test_eski_liste_panelde_bayat_ama_dolu(self):
        panel = canli.eczane_paneli(_eczane(ESKI))
        self.assertFalse(panel["gecersiz"])
        self.assertTrue(panel["bayat"])
        self.assertEqual(panel["sayi"], 1)
        self.assertEqual(panel["kaynak_adresi"], "https://www.beo.org.tr/nobetci-eczaneler")
        self.assertEqual(panel["kaynak_adi"], "Bursa Eczacı Odası")
        self.assertEqual(timezone.localtime(panel["guncelleme"]).date().isoformat(), "2026-09-12")

    def test_kaynaksiz_dosyada_yedek_adres(self):
        veri = _eczane(ESKI)
        veri.pop("kaynak")
        panel = canli.eczane_paneli(veri)
        self.assertEqual(panel["kaynak_adresi"], canli.ECZANE_KAYNAK_ADRESI)

    def test_dunku_liste_gosterilir(self):
        panel = canli.eczane_paneli(_eczane(_yerel(1, 22)))
        self.assertFalse(panel["gecersiz"])
        self.assertEqual(panel["sayi"], 1)


class _Klasorlu(TestCase):
    """Geçici canlı veri kökü + temiz süreç belleği."""

    @classmethod
    def setUpTestData(cls):
        from django.core.management import call_command
        call_command("taksonomi_kur", verbosity=0)

    def setUp(self):
        self.kok = Path(tempfile.mkdtemp(prefix="bh-nobet-"))
        _bellek.clear()

    def tearDown(self):
        shutil.rmtree(self.kok, ignore_errors=True)
        _bellek.clear()

    def yaz(self, ad, veri):
        (self.kok / f"{ad}.json").write_text(json.dumps(veri, ensure_ascii=False),
                                              encoding="utf-8")

    def sayfa(self, yol):
        _bellek.clear()
        with override_settings(CANLI_VERI_KOK=self.kok):
            yanit = self.client.get(yol)
        _bellek.clear()
        self.assertEqual(yanit.status_code, 200)
        return yanit.content.decode()


class EskiListeSayfalarda(_Klasorlu):
    """Eski liste boş bırakılmaz: eczane görünür. 23 Ekim 2026, kullanıcı kararı: bayat veride de tarih/uyarı basılmaz."""

    def _son_liste_mi(self, metin):
        # Sekme başlığı/meta (head) ve JSON-LD arama için günü taşır;
        # okurun gördüğü gövde taşımaz.
        import re
        metin = re.sub(r'<script type="application/ld\+json">.*?</script>', '',
                       metin.split("</head>", 1)[1], flags=re.S)
        self.assertIn("Deneme Eczanesi", metin)
        self.assertIn("0224 999 88 77", metin)
        self.assertNotIn("12 Eylül 2026", metin)
        self.assertNotIn("elimizdeki son liste", metin.lower())
        self.assertNotIn("Nöbet listesi şu an alınamıyor", metin)

    def test_anasayfa(self):
        self.yaz("nobetci-eczane", _eczane(ESKI))
        self._son_liste_mi(self.sayfa("/"))

    def test_nobetci_eczane_sayfasi(self):
        self.yaz("nobetci-eczane", _eczane(ESKI))
        self._son_liste_mi(self.sayfa("/nobetci-eczane"))

    def test_ilce_eczane_sayfasi(self):
        self.yaz("nobetci-eczane", _eczane(ESKI))
        metin = self.sayfa("/nobetci-eczane/nilufer")
        self.assertIn("Deneme Eczanesi", metin)
        self.assertNotIn("elimizdeki son liste", metin.lower())

    def test_bolum_servis_paneli(self):
        # Eskiden ilçe sayfasının servis paneli (20 Ekim 2026'da kalktı);
        # aynı panel Sağlık bölümünde Bursa geneliyle çiziliyor.
        self.yaz("nobetci-eczane", _eczane(ESKI))
        self._son_liste_mi(self.sayfa("/saglik"))

    def test_taze_liste_uyarisiz(self):
        self.yaz("nobetci-eczane", _eczane(_yerel(0, 0)))
        metin = self.sayfa("/nobetci-eczane")
        self.assertIn("Deneme Eczanesi", metin)
        self.assertNotIn("elimizdeki son liste", metin.lower())

    def test_sayfa_paketi_eski_listeyi_verir(self):
        """Sayfa paketi doludur; HABER komutunun katı kuralı ayrı yerde."""
        self.yaz("nobetci-eczane", _eczane(ESKI))
        with override_settings(CANLI_VERI_KOK=self.kok):
            _bellek.clear()
            paket = eczane.gunun_paketi()
            self.assertIsNotNone(paket)
            self.assertFalse(paket["gecersiz"])
            self.assertTrue(paket["bayat"])
        _bellek.clear()


class PuanBasligiBayat(_Klasorlu):
    """Servis panelinin başlığı hafta numarasını yazar. 23 Ekim 2026, kullanıcı kararı: bayat veride de tarih/uyarı basılmaz."""

    def _puan(self, guncelleme):
        return {"guncelleme": guncelleme, "bayat_esik_dakika": 2880,
                "kaynak": {"ad": "TFF"}, "ligler": [],
                "takip": {"ad": "BURSASPOR", "kulup_id": 3601, "lig": "1lig",
                          "lig_adi": "1. Lig", "sira": 2, "puan": 15, "oynadi": 6,
                          "galibiyet": 5, "beraberlik": 0, "maglubiyet": 1,
                          "attigi": 12, "yedigi": 4, "averaj": 8, "hafta": 7,
                          "mac": None, "fikstur": []}}

    def test_bayat_tabloda_da_yalniz_hafta(self):
        self.yaz("puan-durumu", self._puan(ESKI))
        metin = self.sayfa("/bursaspor")
        self.assertIn("7. hafta &middot;", metin)
        self.assertNotIn("güncel değil", metin)

    def test_taze_tabloda_yalniz_hafta(self):
        self.yaz("puan-durumu", self._puan(_yerel(0, 0)))
        metin = self.sayfa("/bursaspor")
        self.assertIn("7. hafta &middot;", metin)
        self.assertNotIn("7. hafta, <b>güncel değil</b>", metin)
