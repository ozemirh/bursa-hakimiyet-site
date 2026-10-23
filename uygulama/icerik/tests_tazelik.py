"""Paket J (19 Ekim 2026): bayat veri dürüst gösterilsin, kaynak sağlığı ölçülsün.

Zamanlayıcı 12 Eylül'de durdu; site 37 gün boyunca 12 Eylül vakitlerini
"ŞİMDİ", 13 Eylül maçını "bekliyor" diye gösterdi. Korunan kurallar:

1. **Tek tazelik sözleşmesi** (`canli.tazelik`): her bileşen taze / bayat /
   yok; bayat veri tarih + "güncel değil" ile basılır ya da gizlenir.
2. **Namaz istek anında hesaplanır**; vakit yalnız BUGÜNÜN satırından gelir.
3. **Maç durumu bugüne göre**: tarihi geçmiş, skorsuz maç "bekliyor" değil
   "güncel bilgi yok"; haftanın maçı ile fikstürün sıradakisi tek işlevden.
4. **Geçmiş tarihli film süzülür.**
5. **Betikler asgari kayıt eşiği uygular**: eşik altı veri yazılmaz, önceki
   iyi dosya korunur, durum "supheli"; `/_durum` bunu gösterir.

Bütün testler geçici klasördeki FIXTURE dosyalarıyla çalışır; gerçek
`canli-veri/veri` dosyalarına bağlanmaz.
"""

import importlib
import json
import shutil
import sys
import tempfile
from datetime import date, datetime, timedelta
from pathlib import Path
from unittest import mock

from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.utils import timezone

from . import bursaspor, canli
from .canli import _bellek

BETIK_KOK = Path(settings.BASE_DIR).parent / "canli-veri"
ORNEK = BETIK_KOK / "ornekler" / "baskasinema-yakinda.html"


def _betik(ad):
    """`canli-veri/<ad>.py` modülünü yükler (betikler `ortak`ı düz içe aktarır)."""
    if str(BETIK_KOK) not in sys.path:
        sys.path.insert(0, str(BETIK_KOK))
    return importlib.import_module(ad)


def _damga(dakika_once=0):
    return (timezone.now() - timedelta(minutes=dakika_once)).astimezone().isoformat(
        timespec="seconds")


class KlasorluTest(TestCase):
    """Geçici canlı veri kökü + temiz süreç belleği."""

    @classmethod
    def setUpTestData(cls):
        from django.core.management import call_command
        call_command("taksonomi_kur", verbosity=0)

    def setUp(self):
        self.kok = Path(tempfile.mkdtemp(prefix="bh-tazelik-"))
        _bellek.clear()

    def tearDown(self):
        shutil.rmtree(self.kok, ignore_errors=True)
        _bellek.clear()

    def yaz(self, ad, veri):
        (self.kok / f"{ad}.json").write_text(
            json.dumps(veri, ensure_ascii=False), encoding="utf-8")

    def sayfa(self, yol="/"):
        _bellek.clear()
        with override_settings(CANLI_VERI_KOK=self.kok):
            yanit = self.client.get(yol)
        _bellek.clear()
        self.assertEqual(yanit.status_code, 200)
        return yanit.content.decode()


# -- 1. sözleşme --------------------------------------------------------------

class TazelikSozlesmesi(TestCase):

    def test_taze(self):
        t = canli.tazelik({"guncelleme": _damga(5), "bayat_esik_dakika": 60})
        self.assertEqual(t["durum"], "taze")
        self.assertTrue(t["bugun"])
        self.assertEqual(t["metin"], "")

    def test_bayat_tarih_ve_guncel_degil_der(self):
        t = canli.tazelik({"guncelleme": "2026-09-12T21:57:07+03:00",
                           "bayat_esik_dakika": 1440},
                          simdi=datetime(2026, 10, 19, 12, tzinfo=timezone.get_current_timezone()))
        self.assertEqual(t["durum"], "bayat")
        self.assertFalse(t["bugun"])
        self.assertIn("12 Eylül 2026, 21:57", t["metin"])
        self.assertIn("güncel değil", t["metin"])

    def test_yok(self):
        self.assertEqual(canli.tazelik(None)["durum"], "yok")

    def test_dosyada_esik_yoksa_bilesenin_varsayilani(self):
        t = canli.tazelik({"guncelleme": _damga(60 * 30)},
                          canli.VARSAYILAN_ESIK["doviz"])
        self.assertEqual(t["durum"], "bayat")

    def test_elle_giris_isaretlenir(self):
        t = canli.tazelik({"guncelleme": _damga(1), "bayat_esik_dakika": 60,
                           "kaynak": {"kisa": "panel"}})
        self.assertTrue(t["elle"])


# -- 2. namaz -----------------------------------------------------------------

class NamazBugununSatiri(KlasorluTest):

    def test_hesap_bugunu_uretir_ve_dosyaya_bakmaz(self):
        # Dosyada yalnız 12 Eylül var (donmuş zamanlayıcı); site yine bugünü hesaplar.
        self.yaz("namaz-vakitleri", {"guncelleme": "2026-09-12T15:12:02+03:00",
                                     "bayat_esik_dakika": 2880,
                                     "kaynak": {"kisa": "hesap"},
                                     "gunler": [{"tarih": "2026-09-12", "vakitler": {
                                         "imsak": "05:11"}}]})
        with override_settings(CANLI_VERI_KOK=self.kok):
            n = canli.namaz_verisi()
        self.assertTrue(n["hesap"])
        self.assertEqual(n["bugun"]["tarih"], timezone.localdate().isoformat())
        self.assertEqual(n["tazelik"]["durum"], "taze")
        self.assertRegex(n["bugun"]["vakitler"]["ogle"], r"^1[23]:\d\d$")

    def test_hesap_diyanet_tablosuyla_ayni(self):
        """Site aynı modülü kullanır: 27 Ağustos 2026 Diyanet tablosu."""
        n = canli.namaz_verisi(datetime(2026, 8, 27, 12, tzinfo=timezone.get_current_timezone()))
        self.assertEqual(n["bugun"]["vakitler"]["imsak"], "04:49")
        self.assertEqual(n["bugun"]["vakitler"]["ogle"], "13:10")

    def test_simdi_yalniz_bugunun_satirinda(self):
        dun = {"gunler": [{"tarih": (timezone.localdate() - timedelta(days=1)).isoformat(),
                           "vakitler": {"imsak": "00:01", "yatsi": "00:02"}}]}
        self.assertEqual(canli.simdiki_vakit(dun), "")

    def test_elle_tablo_bittiyse_panel_guncel_degil_der(self):
        self.yaz("namaz-vakitleri", {
            "guncelleme": "2026-09-12T15:12:02+03:00", "bayat_esik_dakika": 2880,
            "kaynak": {"kisa": "panel", "ad": "Elle giriş"}, "yer": {"ad": "Bursa"},
            "vakit_adlari": {"imsak": "İmsak"},
            "gunler": [{"tarih": "2026-09-12", "vakitler": {"imsak": "05:11"}}]})
        with override_settings(CANLI_VERI_KOK=self.kok):
            n = canli.namaz_verisi()
        self.assertFalse(n["hesap"])
        self.assertIsNone(n["bugun"])
        self.assertEqual(n["tazelik"]["durum"], "bayat")
        metin = self.sayfa()
        self.assertIn("Vakit bilgisi şu an alınamıyor.", metin)
        self.assertNotIn("vakit-simdi", metin)

    def test_elle_tabloda_bugun_varsa_o_gosterilir(self):
        bugun = timezone.localdate().isoformat()
        self.yaz("namaz-vakitleri", {
            "guncelleme": "2026-09-12T15:12:02+03:00", "bayat_esik_dakika": 2880,
            "kaynak": {"kisa": "panel"}, "yer": {"ad": "Bursa"},
            "vakit_adlari": {"imsak": "İmsak", "ogle": "Öğle"},
            "gunler": [{"tarih": bugun, "vakitler": {"imsak": "04:44", "ogle": "12:34"}}]})
        metin = self.sayfa()
        self.assertIn("12:34", metin)
        self.assertNotIn("Vakit bilgisi güncel değil.", metin)

    def test_hesap_modulu_yoksa_dosyadan_bugunun_satiri(self):
        bugun = timezone.localdate().isoformat()
        self.yaz("namaz-vakitleri", {
            "guncelleme": _damga(10), "bayat_esik_dakika": 2880,
            "kaynak": {"kisa": "hesap"},
            "gunler": [{"tarih": "2026-09-12", "vakitler": {"imsak": "05:11"}},
                       {"tarih": bugun, "vakitler": {"imsak": "06:06"}}]})
        with override_settings(CANLI_VERI_KOK=self.kok), \
                mock.patch.object(canli, "_namaz_hesap", return_value=None):
            n = canli.namaz_verisi()
        self.assertEqual(n["bugun"]["vakitler"]["imsak"], "06:06")

    def test_anasayfa_bugunun_vaktini_basar(self):
        beklenen = canli.namaz_verisi()["bugun"]["vakitler"]["ikindi"]
        metin = self.sayfa()
        self.assertIn(f"<span>{beklenen}</span>", metin)


# -- 3. haftanın maçı -----------------------------------------------------------

def _mac(hafta, tarih, ev_gol=None, dep_gol=None, mac_id=None):
    return {"hafta": hafta, "tarih": tarih, "saat": "20:00", "ev": "BURSASPOR",
            "ev_kulup_id": 3601, "deplasman": f"RAKİP {hafta}",
            "deplasman_kulup_id": 900 + hafta, "ev_gol": ev_gol,
            "deplasman_gol": dep_gol, "oynandi": ev_gol is not None,
            "mac_id": mac_id or 5000 + hafta}


def _puan(guncelleme, fikstur, mac=None):
    return {"guncelleme": guncelleme, "bayat_esik_dakika": 2880,
            "kaynak": {"ad": "TFF"}, "ligler": [],
            "takip": {"ad": "BURSASPOR", "kulup_id": 3601, "lig": "1lig",
                      "lig_adi": "1. Lig", "sira": 2, "puan": 15, "oynadi": 6,
                      "galibiyet": 5, "beraberlik": 0, "maglubiyet": 1,
                      "attigi": 12, "yedigi": 4, "averaj": 8, "hafta": 7,
                      "mac": mac, "fikstur": fikstur}}


DONMUS = _puan("2026-09-12T16:04:53+03:00",
               [_mac(6, "07.09.2026", 1, 2), _mac(7, "13.09.2026"),
                _mac(8, "19.09.2026"), _mac(11, "18.10.2026"),
                _mac(12, "25.10.2026")],
               mac=_mac(7, "13.09.2026"))


class HaftaninMaci(KlasorluTest):

    def test_gecmis_tarihli_skorsuz_mac_bekliyor_degil(self):
        t = canli.mac_takvimi(DONMUS, date(2026, 10, 19))
        self.assertEqual(t["haftanin"]["hafta"], 11)       # dün oynandı (18 Ekim)
        self.assertEqual(t["haftanin"]["durum"], "bilgi_yok")
        self.assertEqual(t["sonraki"]["hafta"], 12)

    def test_sonuc_varsa_sonuc(self):
        t = canli.mac_takvimi(DONMUS, date(2026, 9, 8))
        self.assertEqual(t["haftanin"]["hafta"], 6)
        self.assertEqual(t["haftanin"]["durum"], "sonuc")

    def test_uzak_gecmisten_sonra_siradaki(self):
        t = canli.mac_takvimi(DONMUS, date(2026, 10, 23))
        self.assertEqual(t["haftanin"]["hafta"], 12)
        self.assertEqual(t["haftanin"]["durum"], "bekliyor")

    def test_bugunku_mac_once(self):
        t = canli.mac_takvimi(DONMUS, date(2026, 9, 13))
        self.assertEqual(t["haftanin"]["hafta"], 7)
        self.assertEqual(t["haftanin"]["durum"], "bekliyor")

    def test_fikstur_yokken_takip_maci_kullanilir(self):
        t = canli.mac_takvimi(_puan(_damga(), [], mac=_mac(7, "13.09.2026")),
                              date(2026, 10, 19))
        self.assertEqual(t["haftanin"]["durum"], "bilgi_yok")

    def test_kutu_ve_fikstur_ayni_kaynaktan(self):
        with mock.patch.object(canli, "bugunun_tarihi", lambda: date(2026, 10, 19)):
            kutu = canli.puan_takibi(DONMUS)["mac"]
            fikstur = bursaspor.fikstur_hazirla(DONMUS)
        self.assertEqual(kutu["mac_id"], 5011)
        self.assertEqual(fikstur["sonraki"]["mac_id"], 5012)
        durum = {m["hafta"]: m["durum"] for m in fikstur["maclar"]}
        self.assertEqual(durum[7], "bilgi_yok")
        self.assertEqual(durum[12], "bekliyor")

    def test_anasayfa_bilgi_yok_damgasiz(self):
        """23 Ekim 2026, kullanıcı kararı: bayat veride de tarih/uyarı basılmaz."""
        self.yaz("puan-durumu", DONMUS)
        with mock.patch.object(canli, "bugunun_tarihi", lambda: date(2026, 10, 19)):
            metin = self.sayfa()
        self.assertIn('aria-label="sonuç bilgisi yok"', metin)
        self.assertNotIn("güncel bilgi yok", metin)
        self.assertNotIn("son güncelleme", metin)
        self.assertNotIn('<span class="sonuc bekliyor">20:00</span>', metin)

    def test_bursaspor_sayfasinda_soru_isareti_ve_tarih(self):
        self.yaz("puan-durumu", DONMUS)
        with mock.patch.object(canli, "bugunun_tarihi", lambda: date(2026, 10, 19)):
            metin = self.sayfa("/bursaspor")
        self.assertIn('aria-label="sonuç bilgisi yok"', metin)
        self.assertNotIn("itibarıyla", metin)
        self.assertIn("sonuç bilgisi yok", metin)        # servis panelindeki kart


# -- 4. vizyon ------------------------------------------------------------------

class VizyonSuzgeci(KlasorluTest):

    def _vizyon(self, guncelleme, *tarihler):
        return {"guncelleme": guncelleme, "bayat_esik_dakika": 10080,
                "kaynak": {"ad": "Deneme"},
                "haftalar": [{"tarih": t, "filmler": [{"ad": f"Film {t}"}]}
                             for t in tarihler]}

    def test_gecmis_film_suzulur_bugunku_kalir(self):
        v = self._vizyon(_damga(), "2026-10-18", "2026-10-19", "2026-10-30")
        filmler = canli.vizyon_filmleri(v, bugun=date(2026, 10, 19))
        self.assertEqual([f["ad"] for f in filmler], ["Film 2026-10-19", "Film 2026-10-30"])

    def test_bayat_liste_uyarisiz(self):
        ileri = (timezone.localdate() + timedelta(days=11)).isoformat()
        self.yaz("vizyon-takvimi", self._vizyon("2026-09-12T15:12:35+03:00",
                                                "2026-09-18", ileri))
        metin = self.sayfa()
        self.assertNotIn("güncel değil", metin)
        self.assertNotIn("Film 2026-09-18", metin)
        self.assertIn(f"Film {ileri}", metin)

    def test_hepsi_gecmisse_son_filmler_gosterilir(self):
        """Kullanıcı kararı (19 Ekim 2026 akşamı): bölüm boş kalmaz; elimizdeki
        son filmler "vizyona girdi" diye durur. 23 Ekim 2026, kullanıcı kararı: bayat veride de tarih/uyarı basılmaz."""
        self.yaz("vizyon-takvimi", self._vizyon("2026-09-12T15:12:35+03:00",
                                                "2026-09-11", "2026-09-18"))
        metin = self.sayfa()
        self.assertIn("vizyon-izgara", metin)
        self.assertIn("Film 2026-09-18", metin)
        self.assertIn("vizyona girdi:", metin)
        self.assertNotIn("güncel değil", metin)
        self.assertNotIn("Önümüzdeki haftalar için vizyon bilgisi yok.", metin)
        # En yeni vizyon tarihi önde.
        self.assertLess(metin.index("Film 2026-09-18"), metin.index("Film 2026-09-11"))

    def test_ileri_film_varsa_gecmisler_basilmaz(self):
        ileri = (timezone.localdate() + timedelta(days=3)).isoformat()
        filmler = canli.vizyon_filmleri(self._vizyon(_damga(), "2026-09-18", ileri))
        self.assertEqual([f["ad"] for f in filmler], [f"Film {ileri}"])
        self.assertFalse(filmler[0]["gecmis"])

    def test_taze_listede_uyari_yok(self):
        ileri = (timezone.localdate() + timedelta(days=4)).isoformat()
        self.yaz("vizyon-takvimi", self._vizyon(_damga(5), ileri))
        self.assertNotIn("Vizyon takvimi ", self.sayfa().split('id="vizyon"')[1][:600])


# -- 5. döviz bandı ve üst şerit -----------------------------------------------------

def _doviz(guncelleme):
    return {"guncelleme": guncelleme, "bayat_esik_dakika": 1440,
            "kaynak": {"ad": "TCMB", "kunye": "Kaynak: TCMB."},
            "kalemler": [{"anahtar": "dolar", "ad": "Dolar", "birim": "TL",
                          "deger": 48.5, "degisim_yuzde": 0.1, "yon": "yukari"}]}


class DovizBandi(KlasorluTest):

    def test_bayat_bantta_da_damga_yok(self):
        """23 Ekim 2026, kullanıcı kararı: bayat veride de tarih/uyarı basılmaz."""
        self.yaz("doviz", _doviz("2026-09-12T21:57:07+03:00"))
        metin = self.sayfa()
        self.assertIn("doviz-ic", metin)
        self.assertNotIn("güncel değil", metin)
        self.assertNotIn('<span class="tarih">', metin)

    def test_taze_bantta_damga_yok(self):
        """23 Ekim 2026, kullanıcı isteği: bantta saat de basılmaz."""
        self.yaz("doviz", _doviz(_damga(3)))
        import re
        metin = self.sayfa()
        self.assertIn("doviz-ic", metin)
        self.assertIsNone(re.search(r'<span class="tarih">', metin))

    def test_yok(self):
        self.assertNotIn("doviz-ic", self.sayfa())

    def test_ekonomi_bayat_damgasiz(self):
        self.yaz("doviz", _doviz("2026-09-12T21:57:07+03:00"))
        metin = self.sayfa("/ekonomi")
        self.assertIn("piyasa-cetveli", metin)
        self.assertNotIn("GÜNCEL DEĞİL", metin)
        self.assertNotIn("12 Eylül 2026", metin)


def _hava(guncelleme, kisa="MGM"):
    return {"guncelleme": guncelleme, "bayat_esik_dakika": 180,
            "kaynak": {"kisa": kisa, "ad": "MGM"},
            "merkez": {"il": "Bursa"},
            "son_durum": {"olcum_zamani": "2026-09-12T22:00:00+03:00",
                          "sicaklik": 24.4, "hadise": {"kod": "A", "ad": "Açık"}},
            "gunler": [{"tarih": "2026-09-12", "en_dusuk": 17, "en_yuksek": 29,
                        "hadise": {"kod": "A", "ad": "Açık"}}],
            "saatlik": []}


class HavaVeEczane(KlasorluTest):
    """Kaynak sözleşmedir; damga ve uyarı yok. 23 Ekim 2026, kullanıcı kararı: bayat veride de tarih/uyarı basılmaz."""

    def test_bayat_hava_ust_seritte_damgasiz(self):
        """Şerit boş kalmaz (19 Ekim 2026); ölçüm damgası 23 Ekim'de kalktı."""
        self.yaz("hava-durumu", _hava("2026-09-12T22:12:11+03:00"))
        metin = self.sayfa()
        self.assertIn("Bursa 24°C", metin)
        self.assertNotIn("veri tazelenemedi", metin)
        self.assertNotIn("ölçümü", metin)

    def test_taze_hava_ust_seritte(self):
        self.yaz("hava-durumu", _hava(_damga(5)))
        metin = self.sayfa()
        self.assertIn("Bursa 24°C", metin)
        self.assertNotIn("veri tazelenemedi", metin)

    def test_elle_girilen_hava_kaynagi_panel(self):
        self.yaz("hava-durumu", _hava(_damga(5), kisa="panel"))
        metin = self.sayfa()
        # Taze ölçümde damga yok (23 Ekim 2026), kaynak adı tek başına kalır.
        self.assertIn('<p class="hava-damga">Kaynak: panel</p>', metin)
        self.assertNotIn("ölçümü", metin)
        self.assertIn("Bursa 24°C", metin)

    def _eczane(self, guncelleme, kisa="BEO"):
        return {"guncelleme": guncelleme, "bayat_esik_dakika": 1440,
                "gun": "2026-09-12", "kaynak": {"ad": "Bursa Eczacı Odası", "kisa": kisa},
                "eczaneler": [{"ad": "DENEME ECZANESİ", "ilce": "NİLÜFER",
                               "telefon": "0224 000 00 00",
                               "nobet_baslangic": "2026-09-12T18:30",
                               "nobet_bitis": "2026-09-13T08:30"}]}

    @staticmethod
    def _dun_sabah():
        """Dün 00:01 (yerel): eşik (1.440 dk) aşılmış ama liste DÜNÜN.

        19 Ekim 2026'dan beri dünden eski liste hiç basılmıyor
        (`canli.GECERLIK_GUN`, tests_nobet_gecerlik); "bayat ama uyarıyla
        gösterilir" hâli yalnız dünkü listede kaldı.
        """
        bugun = timezone.localdate()
        an = timezone.make_aware(datetime.combine(bugun - timedelta(days=1),
                                                  datetime.min.time()))
        return (an + timedelta(minutes=1)).isoformat()

    def test_bayat_eczane_uyarisiz(self):
        self.yaz("nobetci-eczane", self._eczane(self._dun_sabah()))
        for yol in ("/", "/nobetci-eczane"):
            metin = self.sayfa(yol)
            self.assertIn("Deneme Eczanesi", metin)
            self.assertNotIn("elimizdeki son liste", metin)

    def test_elle_girilen_taze_eczane_uyarisiz(self):
        self.yaz("nobetci-eczane", self._eczane(_damga(5), kisa="panel"))
        metin = self.sayfa()
        self.assertIn("Deneme Eczanesi", metin)
        self.assertNotIn("elimizdeki son liste", metin)

    def test_bolum_servis_panelinde_de_uyarisiz(self):
        self.yaz("nobetci-eczane", self._eczane(self._dun_sabah()))
        metin = self.sayfa("/saglik")
        self.assertIn("Deneme Eczanesi", metin)
        self.assertNotIn("Elimizdeki son liste", metin)


# -- 6. betikler: asgari eşik ve kaynak sağlığı -----------------------------------------

class BetikEsikleri(TestCase):

    def setUp(self):
        self.kok = Path(tempfile.mkdtemp(prefix="bh-betik-"))
        self.ortak = _betik("ortak")
        self._log = mock.patch.object(self.ortak, "log", lambda *_: None)
        self._log.start()
        self._bekle = mock.patch.object(self.ortak, "bekle", lambda: None)
        self._bekle.start()

    def tearDown(self):
        self._log.stop()
        self._bekle.stop()
        shutil.rmtree(self.kok, ignore_errors=True)

    def _durum(self, bilesen):
        return json.loads((self.kok / f"durum-{bilesen}.json").read_text(encoding="utf-8"))

    def test_eczane_esik_alti_supheli_onceki_korunur(self):
        modul = _betik("nobetci_eczane")
        eski = {"guncelleme": "2026-09-12T22:12:11+03:00", "eczaneler": [{"ad": "ESKİ"}]}
        (self.kok / "nobetci-eczane.json").write_text(json.dumps(eski), encoding="utf-8")
        paket = {"eczaneler": [{"ad": f"E{i}", "ilce": "NİLÜFER", "adres": "", "telefon": "",
                                "enlem": None, "boylam": None, "nobet_metni": "",
                                "nobet_baslangic": "", "nobet_bitis": ""} for i in range(5)],
                 "kaynak": {"ad": "Bursa Eczacı Odası"}}
        with mock.patch.object(modul, "beo_cek", return_value=paket):
            kod = modul.calistir(self.kok, "beo", "", "")
        self.assertEqual(kod, 2)
        durum = self._durum("nobetci-eczane")
        self.assertEqual(durum["durum"], "supheli")
        self.assertEqual(durum["esik"], {"alan": "eczane", "asgari": 20, "gelen": 5,
                                         "gecti": False})
        self.assertEqual(durum["kaynaklar"][0]["sonuc"], "bos")
        kalan = json.loads((self.kok / "nobetci-eczane.json").read_text(encoding="utf-8"))
        self.assertEqual(kalan["eczaneler"][0]["ad"], "ESKİ")

    def test_eczane_esik_ustu_taze(self):
        modul = _betik("nobetci_eczane")
        paket = {"eczaneler": [{"ad": f"E{i}", "ilce": "NİLÜFER", "adres": "", "telefon": "",
                                "enlem": None, "boylam": None, "nobet_metni": "",
                                "nobet_baslangic": "", "nobet_bitis": ""} for i in range(25)],
                 "kaynak": {"ad": "Bursa Eczacı Odası"}}
        with mock.patch.object(modul, "beo_cek", return_value=paket):
            self.assertEqual(modul.calistir(self.kok, "beo", "", ""), 0)
        durum = self._durum("nobetci-eczane")
        self.assertEqual(durum["durum"], "taze")
        self.assertTrue(durum["esik"]["gecti"])

    def test_vizyon_kaynak_basina_esik(self):
        modul = _betik("vizyon_takvimi")
        film = modul.film_kaydi("Film", (date.today() + timedelta(days=5)).isoformat())
        with mock.patch.object(modul, "_baska_cek", return_value=[]), \
                mock.patch.object(modul, "_birfilm_cek", return_value=[film]):
            kod = modul.calistir(self.kok, "dagitimci", 3, False, baska_izni=True)
        self.assertEqual(kod, 1)   # elde önceki dosya yok
        durum = self._durum("vizyon-takvimi")
        self.assertEqual(durum["durum"], "yok")
        sonuc = {k["ad"]: k["sonuc"] for k in durum["kaynaklar"]}
        self.assertEqual(sonuc, {"Başka Sinema": "bos", "Bir Film": "tamam"})
        self.assertFalse((self.kok / "vizyon-takvimi.json").exists())

    def test_vizyon_baska_sinema_izinsiz_denenmez(self):
        modul = _betik("vizyon_takvimi")
        film = modul.film_kaydi("Film", (date.today() + timedelta(days=5)).isoformat())
        with mock.patch.object(modul, "_baska_cek",
                               side_effect=AssertionError("izinsiz istek")), \
                mock.patch.object(modul, "_birfilm_cek", return_value=[film]):
            self.assertEqual(modul.calistir(self.kok, "dagitimci", 3, False), 0)
        veri = json.loads((self.kok / "vizyon-takvimi.json").read_text(encoding="utf-8"))
        self.assertEqual(veri["kaynak"]["kisa"], "Bir Film")
        self.assertEqual(self._durum("vizyon-takvimi")["durum"], "taze")

    def test_puan_takim_sayisi_azalirsa_supheli(self):
        modul = _betik("puan_durumu")
        def lig(n):
            return {"anahtar": "1lig", "sezon": "2026-2027",
                    "gruplar": [{"takimlar": [{"ad": f"T{i}"} for i in range(n)]}]}
        eski = {"ligler": [lig(20)]}
        self.assertTrue(modul.takim_sagligi([lig(20)], eski)["esik"]["gecti"])
        self.assertFalse(modul.takim_sagligi([lig(14)], eski)["esik"]["gecti"])
        self.assertFalse(modul.takim_sagligi([lig(5)], {})["esik"]["gecti"])
        # Yeni sezon: önceki sezonun sayısı bağlamaz.
        yeni = dict(lig(18), sezon="2027-2028")
        self.assertTrue(modul.takim_sagligi([yeni], eski)["esik"]["gecti"])

    def test_fikstur_baska_sezondan_tasinmaz(self):
        modul = _betik("puan_durumu")
        eski = {"ligler": [{"anahtar": "1lig", "sezon": "2025-2026"}],
                "takip": {"lig": "1lig", "grup_id": None,
                          "fikstur": [{"hafta": 1, "oynandi": True}]}}
        bu = {"lig": "1lig", "sezon": "2026-2027", "grup_id": None}
        self.assertEqual(modul.tasinabilir_fikstur(eski, bu), [])
        ayni = dict(eski, ligler=[{"anahtar": "1lig", "sezon": "2026-2027"}])
        self.assertEqual(len(modul.tasinabilir_fikstur(ayni, bu)), 1)
        baska_lig = dict(bu, lig="super")
        self.assertEqual(modul.tasinabilir_fikstur(ayni, baska_lig), [])

    def test_oynanmis_hafta_sinirli_sayida_yeniden_dogrulanir(self):
        modul = _betik("puan_durumu")
        bugun = date.today().isoformat()
        eski = [{"hafta": h, "oynandi": True, "ev_kulup_id": 1, "deplasman_kulup_id": 2,
                 "dogrulandi": "2026-09-01" if h <= 6 else bugun} for h in range(1, 9)]
        istenen = []

        def sahte_getir(adres, **_):
            istenen.append(adres)
            return '<a href="x&hafta=8">8</a>'
        with mock.patch.object(self.ortak, "getir", sahte_getir), \
                mock.patch.object(modul, "maclari_ayikla", return_value=[]):
            cikti = modul.fikstur_cek("L", 1, eski, {})
        hafta_istekleri = [a for a in istenen if "&hafta=" in a]
        self.assertEqual(len(hafta_istekleri), modul.YENIDEN_DOGRULA_AZAMI)
        # Sayfada maç bulunamayınca oynanmış skor silinmez.
        self.assertEqual(len(cikti), 8)

    def test_durum_dosyasi_eski_davranis_kodlari(self):
        cikti = self.kok / "x.json"
        self.assertEqual(self.ortak.dusme_ile_bitir(self.kok, "x", cikti, "hata"), 1)
        cikti.write_text(json.dumps({"guncelleme": "2026-09-12T10:00:00+03:00"}),
                         encoding="utf-8")
        self.assertEqual(self.ortak.dusme_ile_bitir(self.kok, "x", cikti, "hata"), 2)
        self.assertEqual(self._durum("x")["durum"], "eski")


class BaskaSinemaAyristirici(TestCase):
    """Kaydedilmiş (kırpılmış) gerçek sayfa: 19 Ekim 2026, /filmler?tab=yakinda."""

    def test_yalniz_yakinda_vizyon_filmleri(self):
        modul = _betik("vizyon_takvimi")
        filmler = modul._bs_yeni_ayikla(ORNEK.read_text(encoding="utf-8"))
        ad_tarih = sorted((f["tarih"], f["ad"]) for f in filmler)
        self.assertEqual(ad_tarih, [("2026-10-23", "Devrinin Adamı"),
                                    ("2026-10-29", "Akira"),
                                    ("2026-10-30", "Nöbet"),
                                    ("2027-01-08", "Fjord")])
        devrin = next(f for f in filmler if f["ad"] == "Devrinin Adamı")
        self.assertEqual(devrin["ozgun_ad"], "A Man of His Time")
        self.assertEqual(devrin["tur"], ["Savaş", "Dram", "Tarih"])
        self.assertEqual(devrin["dagitimci"], "Başka Sinema")
        self.assertFalse(devrin["afis_yayinlanabilir"])

    def test_bozuk_sayfa_bos_liste(self):
        modul = _betik("vizyon_takvimi")
        self.assertEqual(modul._bs_yeni_ayikla("<html>yeni tasarım</html>"), [])


# -- 7. /_durum -----------------------------------------------------------------

class DurumUcuKaynakSagligi(TestCase):

    def setUp(self):
        self.kok = Path(tempfile.mkdtemp(prefix="bh-durum-"))
        self.client.force_login(User.objects.create_user("n", password="x", is_staff=True))

    def tearDown(self):
        shutil.rmtree(self.kok, ignore_errors=True)

    def test_supheli_kosu_ve_duran_zamanlayici(self):
        (self.kok / "vizyon-takvimi.json").write_text(json.dumps(
            {"guncelleme": _damga(60), "bayat_esik_dakika": 10080}), encoding="utf-8")
        (self.kok / "durum-vizyon-takvimi.json").write_text(json.dumps({
            "bilesen": "vizyon-takvimi", "durum": "supheli", "denendi": _damga(60 * 24 * 37),
            "esik": {"alan": "film", "asgari": 1, "gelen": 6, "gecti": False},
            "kaynaklar": [{"ad": "Başka Sinema", "sonuc": "bos", "kayit": 0}]}),
            encoding="utf-8")
        with override_settings(CANLI_VERI_KOK=self.kok):
            veri = self.client.get("/_durum").json()
        self.assertEqual(veri["genel"], "uyari")
        cv = veri["canli_veri"]
        self.assertEqual(cv["sorunlu_kosu"], ["vizyon-takvimi"])
        self.assertEqual(cv["zamanlayici_durdu"], ["vizyon-takvimi"])
        b = cv["bilesenler"]["vizyon-takvimi"]
        self.assertFalse(b["esik"]["gecti"])
        self.assertEqual(b["kaynaklar"][0]["ad"], "Başka Sinema")
