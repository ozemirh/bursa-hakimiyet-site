"""Canlı veri okuyucusu ve biçim süzgeçleri.

Bu katmanın işi `canli-veri/veri/*.json` dosyalarını sayfaya taşımak.
Korunması gereken üç davranış var:

1. **Dosya yoksa bileşen sessizce gizlenir.** Uydurma değer basmaktansa
   hiç göstermemek doğru — okur olmayan bir kura bakıp işlem yapabilir.
2. **Bayat veri atılmaz, işaretlenir.** Haftada bir değişen puan
   tablosunun bir gün gecikmesi sorun değil; okur neye baktığını bilsin
   diye güncelleme zamanı gösterilir.
3. **Bozuk JSON sayfayı düşürmez.** Çekme betiği yarıda kesilirse dosya
   yarım kalabilir.
"""

import json
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

from django.test import TestCase, override_settings

from .canli import (KISA_BELLEK_SANIYE, _bellek, _bursa_kulubu, gece_mi,
                    hava_ailesi, hava_paneli, hava_simgesi, oku,
                    puan_ligleri, puan_takibi, simdiki_vakit,
                    vizyon_filmleri)
from .templatetags.site_etiket import baslikla, kisa_gun, kisa_lig, sozluk

TR = timezone(timedelta(hours=3))


class CanliVeriOkuyucu(TestCase):

    def setUp(self):
        self.klasor = tempfile.TemporaryDirectory()
        self.kok = Path(self.klasor.name)
        _bellek.clear()   # süreç belleği testler arasında sızmasın

    def tearDown(self):
        self.klasor.cleanup()
        _bellek.clear()

    def _yaz(self, ad, veri):
        (self.kok / f"{ad}.json").write_text(
            json.dumps(veri, ensure_ascii=False), encoding="utf-8")

    def _oku(self, ad):
        with override_settings(CANLI_VERI_KOK=self.kok):
            return oku(ad)

    def test_dosya_yoksa_none(self):
        self.assertIsNone(self._oku("olmayan"))

    def test_bozuk_json_sayfayi_dusurmuyor(self):
        (self.kok / "bozuk.json").write_text("{ yarim", encoding="utf-8")
        self.assertIsNone(self._oku("bozuk"))

    def test_taze_veri_bayat_degil(self):
        self._yaz("taze", {"guncelleme": datetime.now(TR).isoformat(),
                           "bayat_esik_dakika": 180, "kalemler": []})
        veri = self._oku("taze")
        self.assertFalse(veri["bayat"])
        self.assertLess(veri["yas_dakika"], 5)

    def test_esigi_asan_veri_bayat_isaretleniyor(self):
        eski = (datetime.now(TR) - timedelta(hours=10)).isoformat()
        self._yaz("eski", {"guncelleme": eski, "bayat_esik_dakika": 180})
        veri = self._oku("eski")
        self.assertTrue(veri["bayat"])
        self.assertGreater(veri["yas_dakika"], 180)

    def test_bayat_veri_yine_de_donuyor(self):
        """Bayat diye atılmaz; şablon karar verir."""
        eski = (datetime.now(TR) - timedelta(days=5)).isoformat()
        self._yaz("eski", {"guncelleme": eski, "bayat_esik_dakika": 60,
                           "kalemler": [{"ad": "Dolar"}]})
        self.assertEqual(len(self._oku("eski")["kalemler"]), 1)

    def test_esik_yoksa_bayat_sayilmaz(self):
        eski = (datetime.now(TR) - timedelta(days=30)).isoformat()
        self._yaz("esiksiz", {"guncelleme": eski})
        self.assertFalse(self._oku("esiksiz")["bayat"])

    def test_bozuk_damga_cokertmiyor(self):
        self._yaz("damga", {"guncelleme": "dün", "bayat_esik_dakika": 60})
        veri = self._oku("damga")
        self.assertIsNone(veri["yas_dakika"])
        self.assertFalse(veri["bayat"])

    def test_onbellek_diskten_tekrar_okumuyor(self):
        self._yaz("onbellek", {"guncelleme": datetime.now(TR).isoformat()})
        with override_settings(CANLI_VERI_KOK=self.kok):
            oku("onbellek")
            (self.kok / "onbellek.json").unlink()   # dosya silinse bile
            self.assertIsNotNone(oku("onbellek"))   # bellekten gelir


class SimdikiVakit(TestCase):
    """Şablon o anki namaz vaktini vurguluyor."""

    def test_veri_yoksa_bos(self):
        self.assertEqual(simdiki_vakit(None), "")
        self.assertEqual(simdiki_vakit({}), "")

    def test_gecmis_vakitlerin_sonuncusu_secilir(self):
        veri = {"gunler": [{"vakitler": {
            "imsak": "00:01", "gunes": "00:02", "ogle": "23:58",
            "ikindi": "23:59", "aksam": "23:59", "yatsi": "23:59"}}]}
        # Sabahın ilk iki vakti geçmiş, öğle ve sonrası gelmemiş olmalı.
        self.assertEqual(simdiki_vakit(veri), "gunes")

    def test_hicbiri_gecmediyse_yatsi(self):
        veri = {"gunler": [{"vakitler": {"imsak": "23:59", "yatsi": "23:59"}}]}
        self.assertEqual(simdiki_vakit(veri), "yatsi")


class BicimSuzgecleri(TestCase):

    def test_kisaltmalar_kucultulmuyor(self):
        """"GALATASARAY A.Ş." -> "Galatasaray A.ş." olurdu; A.Ş. korunmalı."""
        self.assertEqual(baslikla("GALATASARAY A.Ş."), "Galatasaray A.Ş.")
        self.assertEqual(baslikla("BURSA NİLÜFER FUTBOL A.Ş."),
                         "Bursa Nilüfer Futbol A.Ş.")

    def test_kisaltma_olmayan_ad_baslik_biciminde(self):
        self.assertEqual(baslikla("TOFAŞ"), "Tofaş")
        self.assertEqual(baslikla("GENÇLERBİRLİĞİ"), "Gençlerbirliği")

    def test_lig_adindan_sponsor_dusuyor(self):
        self.assertEqual(kisa_lig("Trendyol Süper Lig"), "SÜPER")
        self.assertEqual(kisa_lig("Trendyol 1. Lig"), "1. LİG")
        self.assertEqual(kisa_lig("Nesine 2. Lig"), "2. LİG")

    def test_kisa_gun(self):
        self.assertEqual(kisa_gun("2026-08-27"), "Per")
        self.assertEqual(kisa_gun("gecersiz"), "")
        self.assertEqual(kisa_gun(None), "")

    def test_sozluk_suzgeci(self):
        self.assertEqual(sozluk({"a": 1}, "a"), 1)
        self.assertEqual(sozluk({"a": 1}, "yok"), "")
        self.assertEqual(sozluk(None, "a"), "")


class AnasayfaCanliVeriyleAyakta(TestCase):
    """Canlı veri dosyaları yokken de anasayfa açılmalı."""

    @classmethod
    def setUpTestData(cls):
        from django.core.management import call_command
        call_command("taksonomi_kur", verbosity=0)

    def test_canli_veri_yokken_anasayfa_aciliyor(self):
        _bellek.clear()
        bos = Path(tempfile.mkdtemp())
        with override_settings(CANLI_VERI_KOK=bos):
            yanit = self.client.get("/")
        _bellek.clear()
        self.assertEqual(yanit.status_code, 200)
        # Kaynağı olmayan bileşen hiç çizilmemeli, yer tutucu değer basmamalı.
        self.assertNotContains(yanit, "doviz-ic")


class VizyonFilmleri(TestCase):
    """Vizyon bölümü canlı veriden çizilir.

    27 Ağustos 2026'ya kadar şablonda **dört sahte kart** duruyordu
    ("Vizyon filmi 1 — yer tutucu"). `canli.py` `vizyon` anahtarını zaten
    veriyordu ama şablon onu hiç kullanmıyordu. Korunması gereken davranış:
    veri varsa gerçek filmler, veri yoksa **boş durum** — sahte kart değil.
    """

    def test_veri_yoksa_bos_liste(self):
        self.assertEqual(vizyon_filmleri(None), [])

    def test_haftalar_duz_listeye_ceviriliyor(self):
        veri = {"haftalar": [
            {"tarih": "2026-09-04", "filmler": [{"ad": "Film A", "tur": ["Dram"]}]},
            {"tarih": "2026-09-11", "filmler": [{"ad": "Film B", "tarih": "2026-09-11"}]},
        ]}
        filmler = vizyon_filmleri(veri)
        self.assertEqual([f["ad"] for f in filmler], ["Film A", "Film B"])
        # Filmin kendi tarihi yoksa haftanın tarihi kullanılır.
        self.assertEqual(filmler[0]["tarih"].isoformat(), "2026-09-04")
        self.assertEqual(filmler[0]["tur"], "Dram")

    def test_adsiz_kayit_atlanir(self):
        veri = {"haftalar": [{"tarih": "2026-09-04", "filmler": [
            {"ad": ""}, {"ad": "  "}, {"ad": "Gerçek Film"}]}]}
        self.assertEqual([f["ad"] for f in vizyon_filmleri(veri)], ["Gerçek Film"])

    def test_adet_siniri(self):
        veri = {"haftalar": [{"tarih": "2026-09-04", "filmler": [
            {"ad": f"Film {i}"} for i in range(10)]}]}
        self.assertEqual(len(vizyon_filmleri(veri)), 4)

    def test_bozuk_tarih_cokertmiyor(self):
        veri = {"haftalar": [{"tarih": "olmayan-tarih",
                              "filmler": [{"ad": "Film", "tarih": "abc"}]}]}
        self.assertIsNone(vizyon_filmleri(veri)[0]["tarih"])

    def test_kaynakta_olmayan_alan_uydurulmuyor(self):
        veri = {"haftalar": [{"tarih": "2026-09-04", "filmler": [{"ad": "Film"}]}]}
        film = vizyon_filmleri(veri)[0]
        self.assertEqual(film["tur"], "")
        self.assertEqual(film["yas_siniri"], "")
        self.assertEqual(film["dagitimci"], "")


class VizyonBolumuSayfada(TestCase):

    @classmethod
    def setUpTestData(cls):
        from django.core.management import call_command
        call_command("taksonomi_kur", verbosity=0)

    def _yanit(self, kok):
        _bellek.clear()
        with override_settings(CANLI_VERI_KOK=kok):
            yanit = self.client.get("/")
        _bellek.clear()
        return yanit

    def test_veri_yokken_sahte_kart_basilmiyor(self):
        yanit = self._yanit(Path(tempfile.mkdtemp()))
        self.assertEqual(yanit.status_code, 200)
        self.assertNotContains(yanit, "yer tutucu</h3>")
        self.assertNotContains(yanit, "vizyon-izgara")
        self.assertContains(yanit, "Vizyon takvimi şu an alınamıyor.")

    def test_veri_varken_gercek_film_basiliyor(self):
        kok = Path(tempfile.mkdtemp())
        (kok / "vizyon-takvimi.json").write_text(json.dumps({
            "guncelleme": datetime.now(TR).isoformat(),
            "bayat_esik_dakika": 10080,
            "kaynak": {"ad": "Deneme Kaynağı"},
            "haftalar": [{"tarih": "2026-09-04",
                          "filmler": [{"ad": "Deneme Filmi", "tur": ["Dram"]}]}],
        }, ensure_ascii=False), encoding="utf-8")
        yanit = self._yanit(kok)
        self.assertContains(yanit, "Deneme Filmi")
        self.assertContains(yanit, "vizyon-izgara")
        # Afiş telifli: dış adrese bağlanılmaz, yerel yer tutucu durur.
        self.assertNotContains(yanit, "afis_kaynak")


class ArsivSayilariSablonaGomulmuyor(TestCase):
    """Anasayfadaki arşiv büyüklükleri veritabanından gelir.

    Şablona elle yazıldıklarında göç sürerken yanlışlaşıyorlardı (ölçüm,
    27 Ağustos: şablonda "1484 video", veritabanında 31.084).
    """

    @classmethod
    def setUpTestData(cls):
        from django.core.management import call_command
        call_command("taksonomi_kur", verbosity=0)

    def setUp(self):
        from . import views
        views._sayim_bellek = None

    def tearDown(self):
        from . import views
        views._sayim_bellek = None

    def test_sayilar_veritabanindan_geliyor(self):
        from medya.models import Yazar
        Yazar.objects.create(id=1, slug="deneme-yazar", ad="Deneme Yazar")
        Yazar.objects.create(id=2, slug="ikinci-yazar", ad="İkinci Yazar")
        _bellek.clear()
        with override_settings(CANLI_VERI_KOK=Path(tempfile.mkdtemp())):
            yanit = self.client.get("/")
        _bellek.clear()
        self.assertContains(yanit, "Arşivden gelen 2 yazar")
        self.assertContains(yanit, "Arşivden gelen 0 galeri")

    def test_sablonda_sabit_arsiv_sayisi_kalmadi(self):
        kok = Path(__file__).resolve().parent.parent / "sablonlar"
        metin = (kok / "anasayfa.html").read_text(encoding="utf-8")
        for sabit in ("1484 video", "4040 galeri", "6713 köşe", "37 yazar", "32.006"):
            self.assertNotIn(sabit, metin)

    def test_sifir_ile_sayilamadi_ayni_sey_degil(self):
        """0 gerçek bir değerdir, basılır; None "sayılamadı"dır, basılmaz."""
        from django.db import DatabaseError
        from unittest import mock
        from . import views

        _bellek.clear()
        with override_settings(CANLI_VERI_KOK=Path(tempfile.mkdtemp())):
            # gerçek sıfır: cümle basılmalı
            yanit = self.client.get("/")
            self.assertContains(yanit, "Arşivden gelen 0 galeri")

            # sayım kilide takılırsa cümle hiç basılmamalı, sayfa ayakta kalmalı
            views._sayim_bellek = None
            # `KoseYazisi` anasayfada YALNIZ sayımda kullanılıyor; bu yüzden
            # doğru dikiş yeri burası. `FotoGaleri`yi kesmek sayfanın kendi
            # galeri sorgusunu da düşürürdü (ilk denemede öyle oldu).
            with mock.patch.object(views.KoseYazisi, "yayindakiler",
                                   side_effect=DatabaseError("database is locked")):
                kilitli = self.client.get("/")
        _bellek.clear()
        self.assertEqual(kilitli.status_code, 200)
        self.assertNotContains(kilitli, "Arşivden gelen")
        self.assertContains(kilitli, "Kare sayısı kaynağın statik sayfasında yok")


class PuanDurumu(TestCase):
    """Bursaspor bölümünün üç kararı (29 Ağustos 2026).

    1. Açık sekme **Bursaspor'un ligi** — listenin ilki değil.
    2. Grup **körlemesine** seçilmez: Bursaspor'un, yoksa en çok Bursa
       kulübünün bulunduğu grup öne gelir; kalan gruplar düşmez.
    3. Tablo **kırpılmaz**; grubun bütün takımları basılır.
    """

    def _takim(self, sira, ad, kulup_id=0, puan=0):
        return {"sira": sira, "kulup_id": kulup_id, "ad": ad, "oynadi": 1,
                "galibiyet": 1, "beraberlik": 0, "maglubiyet": 0,
                "attigi": 2, "yedigi": 1, "averaj": 1, "puan": puan}

    def _veri(self, oynandi=False):
        return {
            "ligler": [
                {"anahtar": "super", "ad": "Süper Lig", "hafta": 3,
                 "gruplar": [{"grup_id": None, "ad": None,
                              "takimlar": [self._takim(i, f"TAKIM {i}")
                                           for i in range(1, 19)]}]},
                {"anahtar": "1lig", "ad": "1. Lig", "hafta": 4,
                 "gruplar": [{"grup_id": None, "ad": None, "takimlar": [
                     self._takim(1, "BAŞKA SPOR"),
                     self._takim(2, "BURSASPOR", kulup_id=3601, puan=6)]}]},
                {"anahtar": "2lig", "ad": "2. Lig", "hafta": None,
                 "gruplar": [
                     {"grup_id": 3541, "ad": "Beyaz", "takimlar": [
                         self._takim(1, "İNEGÖL KAFKAS SPOR KULÜBÜ"),
                         self._takim(2, "YENİ MALATYASPOR")]},
                     {"grup_id": 3542, "ad": "Kırmızı", "takimlar": [
                         self._takim(1, "KARACABEY BELEDİYE SPOR A.Ş."),
                         self._takim(2, "SULTAN SU İNEGÖLSPOR"),
                         self._takim(3, "SAKARYASPOR A.Ş.")]}]},
            ],
            "takip": {"kulup_id": 3601, "ad": "BURSASPOR", "lig": "1lig",
                      "lig_adi": "1. Lig", "sira": 2, "puan": 6, "hafta": 4,
                      "mac": {"tarih": "29.08.2026", "saat": "19:00",
                              "ev": "KAYSERİSPOR", "ev_kulup_id": 72,
                              "deplasman": "BURSASPOR",
                              "deplasman_kulup_id": 3601,
                              "ev_gol": 1 if oynandi else None,
                              "deplasman_gol": 2 if oynandi else None,
                              "oynandi": oynandi, "mac_id": 1}},
        }

    def test_acik_sekme_bursasporun_ligi(self):
        ligler = puan_ligleri(self._veri())
        self.assertEqual([l["anahtar"] for l in ligler if l["acik"]], ["1lig"])

    def test_takip_yoksa_ilk_lig_acilir(self):
        veri = self._veri()
        del veri["takip"]
        self.assertTrue(puan_ligleri(veri)[0]["acik"])

    def test_bursaspor_grubu_one_gelir(self):
        """Bursaspor'un kendi ligi tek gruplu; grup sırası Bursa'ya göre."""
        ligler = {l["anahtar"]: l for l in puan_ligleri(self._veri())}
        iki = ligler["2lig"]
        # Kırmızı'da iki Bursa kulübü var, Beyaz'da bir → Kırmızı önde
        self.assertEqual([g["ad"] for g in iki["gruplar"]], ["Kırmızı", "Beyaz"])
        self.assertTrue(iki["gruplar"][0]["acik"])
        self.assertTrue(iki["coklu_grup"])

    def test_gruplarin_hicbiri_dusmuyor(self):
        iki = {l["anahtar"]: l for l in puan_ligleri(self._veri())}["2lig"]
        self.assertEqual(len(iki["gruplar"]), 2)

    def test_tablo_kirpilmiyor(self):
        super_lig = puan_ligleri(self._veri())[0]
        self.assertEqual(len(super_lig["gruplar"][0]["takimlar"]), 18)

    def test_bursaspor_satiri_isaretli(self):
        bir = {l["anahtar"]: l for l in puan_ligleri(self._veri())}["1lig"]
        satirlar = bir["gruplar"][0]["takimlar"]
        self.assertEqual([t["ad"] for t in satirlar if t["bizim"]], ["BURSASPOR"])
        self.assertFalse(satirlar[0]["bursa"])

    def test_bursa_kulubu_sozcuk_basindan_taniniyor(self):
        self.assertTrue(_bursa_kulubu("SULTAN SU İNEGÖLSPOR"))
        self.assertTrue(_bursa_kulubu("KARACABEY BELEDİYE SPOR A.Ş."))
        self.assertTrue(_bursa_kulubu("BURSA YILDIRIM SPOR KULÜBÜ"))
        # YENİŞEHİR'e takılıp YENİ MALATYASPOR'u Bursa sanmamalı
        self.assertFalse(_bursa_kulubu("YENİ MALATYASPOR"))
        self.assertFalse(_bursa_kulubu("KELEŞOĞLU ANKARA"))

    def test_oynanmamis_mac_skor_basmaz(self):
        mac = puan_takibi(self._veri(oynandi=False))["mac"]
        self.assertFalse(mac["skor_var"])
        self.assertEqual(mac["tarih_g"].isoformat(), "2026-08-29")

    def test_oynanmis_mac_skor_basar(self):
        mac = puan_takibi(self._veri(oynandi=True))["mac"]
        self.assertTrue(mac["skor_var"])
        self.assertEqual((mac["ev_gol"], mac["deplasman_gol"]), (1, 2))

    def test_veri_yoksa_bolum_cizilmez(self):
        self.assertEqual(puan_ligleri(None), [])
        self.assertIsNone(puan_takibi(None))
        self.assertIsNone(puan_takibi({"ligler": []}))

    def test_kaynak_sozlugu_degismiyor(self):
        """`oku` önbelleği aynı sözlüğü döndürüyor; süslemeler ona yazılmaz."""
        veri = self._veri()
        puan_ligleri(veri)
        takim = veri["ligler"][1]["gruplar"][0]["takimlar"][1]
        self.assertNotIn("bizim", takim)


class HavaPaneli(TestCase):
    """Tam genişlikteki hava panelinin veri hazırlığı.

    Panelin taşıdığı üç iddia burada korunuyor: ölçülemeyen alan
    gösterilmez, beş günün çubuğu ORTAK ölçekte çizilir, saatlik şeritte
    geçmiş saatler okura basılmaz.
    """

    def _paket(self, **degis):
        paket = {
            "merkez": {"il": "Bursa", "ilce": "Osmangazi"},
            "kaynak": {"kisa": "MGM"},
            "son_durum": {
                "olcum_zamani": "2026-08-30T10:08:00+03:00",
                "sicaklik": 25.1, "hissedilen": 26.3, "nem": 61,
                "basinc": 1004, "gorus_metre": 20000, "ruzgar_hiz": 3.2,
                "ruzgar_yon": "kuzeydoğu", "yagis_24saat": 0.1,
                "kar_yukseklik": None,
                "hadise": {"kod": "AB", "ad": "Az bulutlu"},
            },
            "gunler": [
                {"tarih": "2026-08-30", "en_dusuk": 17, "en_yuksek": 31,
                 "hadise": {"kod": "PB", "ad": "Parçalı bulutlu"}},
                {"tarih": "2026-08-31", "en_dusuk": 21, "en_yuksek": 25,
                 "hadise": {"kod": "A", "ad": "Açık"}},
            ],
            "saatlik": [],
        }
        paket.update(degis)
        return paket

    def test_veri_yoksa_none(self):
        self.assertIsNone(hava_paneli(None))

    def test_olculemeyen_alan_kutucuk_acmiyor(self):
        """`kar_yukseklik` None; "0 cm" diye basılmamalı."""
        panel = hava_paneli(self._paket())
        adlar = [o["ad"] for o in panel["olcumler"]]
        self.assertIn("Nem", adlar)
        self.assertNotIn("Kar", adlar)

    def test_gorus_kilometreye_ceviriliyor(self):
        panel = hava_paneli(self._paket())
        gorus = [o for o in panel["olcumler"] if o["ad"] == "Görüş"][0]
        self.assertIn("20", gorus["deger"])
        self.assertIn("km", gorus["deger"])

    def test_nem_yuzdesi_onde_isaretleniyor(self):
        panel = hava_paneli(self._paket())
        nem = [o for o in panel["olcumler"] if o["ad"] == "Nem"][0]
        self.assertTrue(nem["deger"].startswith("%"))

    def test_cubuk_ortak_olcekte(self):
        """17-31 ile 21-25 aynı boyda çıkarsa çubuk hiçbir şey anlatmaz.

        Ortak aralık 17-31 (14 derece); ilk gün tam genişlik, ikinci gün
        dörtte biri kadar olmalı.
        """
        panel = hava_paneli(self._paket())
        ilk, ikinci = panel["gunler"][0]["cubuk"], panel["gunler"][1]["cubuk"]
        self.assertEqual(ilk["sol"], 0.0)
        self.assertEqual(ilk["genislik"], 100.0)
        self.assertGreater(ikinci["sol"], 0)
        self.assertLess(ikinci["genislik"], 50)

    def test_eksik_sicaklik_cubugu_cizdirmiyor(self):
        paket = self._paket(gunler=[{"tarih": "2026-08-30", "en_dusuk": None,
                                     "en_yuksek": None, "hadise": {}}])
        self.assertIsNone(hava_paneli(paket)["gunler"][0]["cubuk"])

    def test_gecmis_saatler_seride_yok(self):
        gecmis = "2020-01-01T06:00:00+03:00"
        gelecek = "2099-01-01T09:00:00+03:00"
        paket = self._paket(saatlik=[
            {"zaman": gecmis, "sicaklik": 12, "hadise": {"kod": "A"}},
            {"zaman": gelecek, "sicaklik": 20, "hadise": {"kod": "A"}},
        ])
        saatler = hava_paneli(paket)["saatlik"]
        self.assertEqual(len(saatler), 1)
        self.assertEqual(saatler[0]["sicaklik"], 20)

    def test_hepsi_gecmisteyse_serit_bos_kalmiyor(self):
        """Veri bayatsa boş şerit çizmektense eski saatleri göstermek doğru."""
        paket = self._paket(saatlik=[
            {"zaman": "2020-01-01T06:00:00+03:00", "sicaklik": 12,
             "hadise": {"kod": "A"}},
        ])
        self.assertEqual(len(hava_paneli(paket)["saatlik"]), 1)

    def test_bozuk_zaman_damgasi_atlanir(self):
        paket = self._paket(saatlik=[{"zaman": "olmayan-tarih", "sicaklik": 9,
                                      "hadise": {}}])
        self.assertEqual(hava_paneli(paket)["saatlik"], [])

    def test_tanimsiz_hadise_kodu_uydurulmuyor(self):
        """Sözlükte olmayan kod nötr buluta düşer, rastgele simge seçilmez."""
        self.assertEqual(hava_simgesi({"kod": "XYZ"}), "hv-bulut")
        self.assertEqual(hava_simgesi(None), "hv-bulut")
        self.assertEqual(hava_simgesi({"kod": "A"}), "hv-acik")


class HavaPaneliSayfada(TestCase):

    def test_veri_yokken_anasayfa_ayakta(self):
        """Hava dosyası yoksa panel gizlenir, sayfa açılmaya devam eder."""
        with tempfile.TemporaryDirectory() as bos:
            _bellek.clear()
            with override_settings(CANLI_VERI_KOK=Path(bos)):
                yanit = self.client.get("/")
            _bellek.clear()
        self.assertEqual(yanit.status_code, 200)
        self.assertContains(yanit, "Hava durumu şu an alınamıyor")


class HavaRengi(TestCase):
    """Panelin rengi bilgi taşır; bezeme olsaydı bu testler gereksizdi.

    Gökyüzünün paleti havaya ve günün saatine bağlı. İki karar korunuyor:
    gece kararı Diyanet'in doğuş/batış saatinden gelir (kaba bir saat
    aralığından değil) ve gece, hadisenin ÖNÜNE geçer — karanlıkta gökyüzü
    yağmurlu da olsa lacivert çizilir.
    """

    NAMAZ = {"gunler": [{"vakitler": {"gunes": "06:21", "aksam": "19:48"}}]}

    def _an(self, saat):
        return datetime.strptime(f"2026-08-30 {saat}", "%Y-%m-%d %H:%M")

    def test_dogus_ile_batis_arasi_gunduz(self):
        self.assertFalse(gece_mi(self._an("06:21"), self.NAMAZ))
        self.assertFalse(gece_mi(self._an("13:00"), self.NAMAZ))
        self.assertFalse(gece_mi(self._an("19:47"), self.NAMAZ))

    def test_batistan_sonra_gece(self):
        self.assertTrue(gece_mi(self._an("19:48"), self.NAMAZ))
        self.assertTrue(gece_mi(self._an("23:30"), self.NAMAZ))
        self.assertTrue(gece_mi(self._an("05:00"), self.NAMAZ))

    def test_namaz_paketi_yoksa_kaba_aralik(self):
        """Vakitler gelmezse panel yine çizilir, karar kabalaşır."""
        self.assertFalse(gece_mi(self._an("12:00")))
        self.assertTrue(gece_mi(self._an("23:00")))

    def test_gece_yalniz_acik_ailesinde_ay_simgesi(self):
        self.assertEqual(hava_simgesi({"kod": "A"}, gece=True), "hv-acik-gece")
        self.assertEqual(hava_simgesi({"kod": "AB"}, gece=True), "hv-bulut-gece")
        # Yağmurun gecesi ayrı çizilmez; damla damladır.
        self.assertEqual(hava_simgesi({"kod": "Y"}, gece=True), "hv-yagmur")

    def test_gece_hadisenin_onune_geciyor(self):
        self.assertEqual(hava_ailesi({"kod": "A"}), "gunes")
        self.assertEqual(hava_ailesi({"kod": "Y"}), "yagis")
        self.assertEqual(hava_ailesi({"kod": "Y"}, gece=True), "gece")

    def test_bilinmeyen_kod_notr_aileye_dusuyor(self):
        self.assertEqual(hava_ailesi({"kod": "XYZ"}), "bulut")
        self.assertEqual(hava_ailesi(None), "bulut")

    def test_panel_manzara_paletini_veriyor(self):
        paket = {
            "son_durum": {"olcum_zamani": "2026-08-30T13:00:00+03:00",
                          "sicaklik": 25, "hadise": {"kod": "A", "ad": "Açık"}},
            "gunler": [], "saatlik": [],
        }
        panel = hava_paneli(paket, self.NAMAZ)
        self.assertEqual(panel["manzara"], "gunes")
        self.assertFalse(panel["gece"])

        paket["son_durum"]["olcum_zamani"] = "2026-08-30T22:00:00+03:00"
        gece = hava_paneli(paket, self.NAMAZ)
        self.assertEqual(gece["manzara"], "gece")
        self.assertTrue(gece["gece"])
        self.assertEqual(gece["simdi"]["simge"], "hv-acik-gece")
