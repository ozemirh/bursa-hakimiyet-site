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

from .canli import (KISA_BELLEK_SANIYE, _bellek, oku, simdiki_vakit,
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
