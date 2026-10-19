"""Kancayı atlayan toplu yazımlarda arama metni tazelenir (Paket L2).

`goc_al` (`bulk_create … update_conflicts`) ve `metin_temizle`
(`bulk_update`) başlık/spot yazar ama `post_save` kancası
(`arama.haber_kaydedildi`) çalışmaz; komutlar etkilenen kimliklerin arama
satırını kendileri yazar. `arama_doldur --kimlikler` aynı işi elle yapar.
"""

from __future__ import annotations

import io
import json
import shutil
import tempfile
from datetime import timedelta
from pathlib import Path

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from django.utils import timezone

from taksonomi.models import Kategori, KategoriTur

from . import arama
from .arama_metni import kayit_metni
from .models import Haber, HaberArama


def _kos(komut, **secenek):
    cikti = io.StringIO()
    call_command(komut, stdout=cikti, stderr=io.StringIO(), **secenek)
    return cikti.getvalue()


class Temel(TestCase):

    @classmethod
    def setUpTestData(cls):
        call_command("taksonomi_kur", verbosity=0)
        cls.gundem = KategoriTur.objects.get(tur=Kategori.TUR_HABER, slug="gundem").kategori

    def arama_basligi(self, kimlik):
        return HaberArama.objects.get(haber_id=kimlik).baslik


class GocAl(Temel):

    def setUp(self):
        self.gecici = Path(tempfile.mkdtemp(prefix="bh-arama-tazele-"))
        self.addCleanup(shutil.rmtree, self.gecici, ignore_errors=True)

    def _dosya(self, kimlik, baslik, spot="Spot"):
        d = {"url": f"https://www.bursahakimiyet.com.tr/gundem/goc-{kimlik}",
             "kategori": "gundem", "baslik": baslik, "spot": spot,
             "govde_html": "<p>a</p>", "yayin_tarihi": "2025-03-04T10:20:30"}
        klasor = self.gecici / "2025-03"
        klasor.mkdir(exist_ok=True)
        (klasor / f"{kimlik}.json").write_text(json.dumps(d, ensure_ascii=False),
                                               encoding="utf-8")

    def test_yeni_ve_guncellenen_kayit_aramaya_yansir(self):
        self._dosya(941001, "Gemlik'te LİMAN genişliyor", spot="Körfez projesi")
        _kos("goc_al", kaynak=str(self.gecici))
        self.assertEqual(self.arama_basligi(941001), kayit_metni("Gemlik'te LİMAN genişliyor"))
        self.assertIn(" korfez ", HaberArama.objects.get(haber_id=941001).metin)
        # Aynı kimlik yeni başlıkla: `update_conflicts` yolu, kanca YOK.
        self._dosya(941001, "Mudanya iskelesi yenilendi", spot="Sahil")
        _kos("goc_al", kaynak=str(self.gecici))
        self.assertEqual(Haber.objects.get(pk=941001).baslik, "Mudanya iskelesi yenilendi")
        self.assertEqual(self.arama_basligi(941001), kayit_metni("Mudanya iskelesi yenilendi"))

    def test_kuru_kosu_aramaya_yazmaz(self):
        self._dosya(941002, "Kuru koşu başlığı")
        _kos("goc_al", kaynak=str(self.gecici), kuru=True)
        self.assertFalse(HaberArama.objects.exists())


class MetinTemizle(Temel):

    KIRLI = "Ug&#774;ur Aslan​ geldi"

    def test_duzelen_baslik_aramaya_yansir(self):
        h = Haber.objects.create(
            id=951001, slug="kirli", baslik=self.KIRLI, spot="Atatu&#776;rk caddesi",
            kategori=self.gundem, durum=Haber.DURUM_AKTIF,
            yayin_zamani=timezone.now() - timedelta(days=1))
        self.assertNotIn(" ugur ", self.arama_basligi(h.pk))   # kancanın yazdığı kirli hâl
        _kos("metin_temizle")
        h.refresh_from_db()
        self.assertEqual(self.arama_basligi(h.pk), kayit_metni(h.baslik))
        self.assertIn(" ugur ", self.arama_basligi(h.pk))
        self.assertIn(" ataturk ", HaberArama.objects.get(haber_id=h.pk).metin)


class AramaDoldurKimlikler(Temel):

    def setUp(self):
        self.a = Haber.objects.create(id=952001, slug="a", baslik="Eski başlık A",
                                      kategori=self.gundem, durum=Haber.DURUM_AKTIF)
        self.b = Haber.objects.create(id=952002, slug="b", baslik="Eski başlık B",
                                      kategori=self.gundem, durum=Haber.DURUM_AKTIF)
        # `update()` kancayı atlar: iki satır da bayat kalır.
        Haber.objects.filter(pk__in=[self.a.pk, self.b.pk]).update(baslik="Yeni başlık")

    def test_yalniz_verilen_kimlik_tazelenir(self):
        cikti = _kos("arama_doldur", kimlikler=f"{self.a.pk},999999")
        self.assertIn("1 / 2 kimlik", cikti)
        self.assertEqual(self.arama_basligi(self.a.pk), kayit_metni("Yeni başlık"))
        self.assertEqual(self.arama_basligi(self.b.pk), kayit_metni("Eski başlık B"))

    def test_tazele_islevi(self):
        self.assertEqual(arama.tazele([self.a.pk, self.b.pk, self.a.pk]), 2)
        self.assertEqual(self.arama_basligi(self.b.pk), kayit_metni("Yeni başlık"))

    def test_gecersiz_liste(self):
        with self.assertRaises(CommandError):
            _kos("arama_doldur", kimlikler="12,abc")
