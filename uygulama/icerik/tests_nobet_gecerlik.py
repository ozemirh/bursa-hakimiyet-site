"""Paket L1 (19 Ekim 2026): dünden eski nöbet listesi gösterilmez.

Nöbetçi eczane günde bir devreder. 12 Eylül listesi 37 gün boyunca
"tazelenemedi" uyarısıyla basılmıştı: uyarı okuru kapalı eczaneye gitmekten
korumuyordu. Kural tek yerde, `canli.tazelik(gecerlik_gun=…)` ve
`canli.GECERLIK_GUN`:

* liste dünden eskiyse eczane satırı HİÇ basılmaz (anasayfa paneli,
  `/nobetci-eczane`, ilçe sayfası servis paneli);
* yerine "Nöbet listesi güncel değil — Bursa Eczacı Odası" bağlantısı ve son
  güncelleme tarihi;
* sayfa başlığı eski tarihi taşımaz, JSON-LD eski eczaneleri yazmaz;
* günlük haber komutunun paketi geçersiz listeyi "veri yok" sayar.

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

    def test_kural_yalniz_eczanede(self):
        self.assertEqual(canli.GECERLIK_GUN, {"nobetci-eczane": 1})

    def test_panel_eczane_basmaz_kaynak_ve_tarih_verir(self):
        panel = canli.eczane_paneli(_eczane(ESKI))
        self.assertTrue(panel["gecersiz"])
        self.assertEqual(panel["eczaneler"], [])
        self.assertEqual(panel["sayi"], 0)
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


class GecersizListeSayfalarda(_Klasorlu):

    def _gecersiz_mi(self, metin):
        self.assertIn("Nöbet listesi güncel değil", metin)
        self.assertIn('href="https://www.beo.org.tr/nobetci-eczaneler"', metin)
        self.assertIn("Son güncelleme:", metin)
        self.assertIn("12 Eylül 2026, 22:12", metin)
        self.assertNotIn("Deneme Eczanesi", metin)
        self.assertNotIn("0224 999 88 77", metin)
        self.assertNotIn("liste tazelenemedi", metin)

    def test_anasayfa(self):
        self.yaz("nobetci-eczane", _eczane(ESKI))
        self._gecersiz_mi(self.sayfa("/"))

    def test_nobetci_eczane_sayfasi(self):
        self.yaz("nobetci-eczane", _eczane(ESKI))
        metin = self.sayfa("/nobetci-eczane")
        self._gecersiz_mi(metin)
        baslik = metin.split("<title>")[1].split("</title>")[0]
        self.assertNotIn("Eylül", baslik)
        self.assertNotIn("Pharmacy", metin)

    def test_ilce_eczane_sayfasi_yok_demez(self):
        self.yaz("nobetci-eczane", _eczane(ESKI))
        metin = self.sayfa("/nobetci-eczane/osmangazi")
        self._gecersiz_mi(metin)
        self.assertNotIn("nöbetçi eczane görünmüyor", metin)

    def test_ilce_sayfasi_servis_paneli(self):
        self.yaz("nobetci-eczane", _eczane(ESKI))
        self._gecersiz_mi(self.sayfa("/ilce/nilufer"))

    def test_taze_liste_aynen(self):
        self.yaz("nobetci-eczane", _eczane(_yerel(0, 0)))
        metin = self.sayfa("/nobetci-eczane")
        self.assertIn("Deneme Eczanesi", metin)
        self.assertNotIn("Nöbet listesi güncel değil", metin)

    def test_haber_paketi_gecersizi_veri_yok_sayar(self):
        self.yaz("nobetci-eczane", _eczane(ESKI))
        with override_settings(CANLI_VERI_KOK=self.kok):
            _bellek.clear()
            self.assertIsNone(eczane.gunun_paketi())
            self.assertTrue(eczane.gunun_paketi(gecersizi_de=True)["gecersiz"])
        _bellek.clear()


class PuanBasligiBayat(_Klasorlu):
    """Servis panelinin başlığındaki hafta numarası bayatlığı da söyler."""

    def _puan(self, guncelleme):
        return {"guncelleme": guncelleme, "bayat_esik_dakika": 2880,
                "kaynak": {"ad": "TFF"}, "ligler": [],
                "takip": {"ad": "BURSASPOR", "kulup_id": 3601, "lig": "1lig",
                          "lig_adi": "1. Lig", "sira": 2, "puan": 15, "oynadi": 6,
                          "galibiyet": 5, "beraberlik": 0, "maglubiyet": 1,
                          "attigi": 12, "yedigi": 4, "averaj": 8, "hafta": 7,
                          "mac": None, "fikstur": []}}

    def test_bayat_tabloda_hafta_guncel_degil(self):
        self.yaz("puan-durumu", self._puan(ESKI))
        self.assertIn("7. hafta, <b>güncel değil</b>", self.sayfa("/bursaspor"))

    def test_taze_tabloda_yalniz_hafta(self):
        self.yaz("puan-durumu", self._puan(_yerel(0, 0)))
        metin = self.sayfa("/bursaspor")
        self.assertIn("7. hafta &middot;", metin)
        self.assertNotIn("7. hafta, <b>güncel değil</b>", metin)
