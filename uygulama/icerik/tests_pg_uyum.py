# -*- coding: utf-8 -*-
"""Başarım paketinin (A) motora bağlı yolları — iki motorda da (19 Ekim 2026).

A'nın PostgreSQL dalları paket birleşene kadar hiç koşmamıştı. Buradaki
testler aynı beklentiyi iki motordan ister: sitemap ay özeti (SQLite saat
kovası / PG `TruncMonth`), okunma boşaltmasının yetim kova dalı (gerçek
yabancı anahtar, taklit değil) ve PG'de kısmi indekslerin kurulumu.
"""

from datetime import datetime, timezone as dt_tz
from unittest import skipUnless

from django.core.management import call_command
from django.db import connection
from django.test import TestCase
from django.utils import timezone

from taksonomi.models import Kategori, KategoriTur

from . import okunma
from .models import Haber, Okunma

PG = connection.vendor == "postgresql"


def _kategori():
    return KategoriTur.objects.get(tur=Kategori.TUR_HABER, slug="gundem").kategori


class SitemapAyOzeti(TestCase):
    """Ay sınırı YEREL saatte (Europe/Istanbul, UTC+3) çizilir."""

    @classmethod
    def setUpTestData(cls):
        call_command("taksonomi_kur", verbosity=0)
        anlar = [
            datetime(2026, 8, 31, 20, 59, tzinfo=dt_tz.utc),   # yerel 23:59 → Ağustos
            datetime(2026, 8, 31, 21, 0, tzinfo=dt_tz.utc),    # yerel 00:00 → Eylül
            datetime(2026, 9, 15, 9, 0, tzinfo=dt_tz.utc),
            datetime(2026, 7, 1, 0, 0, tzinfo=dt_tz.utc),
        ]
        for i, an in enumerate(anlar):
            Haber.objects.create(id=7000 + i, slug=f"ay-{i}", baslik=f"Ay sınaması {i}",
                                 kategori=_kategori(), durum=Haber.DURUM_AKTIF,
                                 yayin_zamani=an)

    def test_toplu_ozet_ay_ay_ozetle_ayni(self):
        from besleme.aileler import aile
        haber = aile("haber")
        toplu = {o.ay: o.adet for o in haber.aylar()}
        self.assertEqual(toplu, {"2026-09": 2, "2026-08": 1, "2026-07": 1})
        for ay, adet in toplu.items():
            with self.subTest(ay=ay):
                self.assertEqual(haber.ay_ozeti(ay).adet, adet)

    def test_sira_yeniden_eskiye(self):
        from besleme.aileler import aile
        self.assertEqual([o.ay for o in aile("haber").aylar()],
                         ["2026-09", "2026-08", "2026-07"])


class OkunmaYetimKova(TestCase):
    """Silinmiş haberin kovası partiyi düşürmemeli — GERÇEK yabancı anahtarla.

    Django'nun yabancı anahtarları iki motorda da `DEFERRABLE INITIALLY
    DEFERRED`: ihlal deyimde değil işlem sonunda patlar. `_upsert` dış bir
    işlemin içinde çağrılırsa (test, `ATOMIC_REQUESTS`, toplu komut) hata
    `IntegrityError` dalına hiç düşmez, dış işlemin commit'inde patlar ve
    o işlemdeki her şeyi geri alır.
    """

    @classmethod
    def setUpTestData(cls):
        call_command("taksonomi_kur", verbosity=0)
        cls.h = Haber.objects.create(id=7100, slug="okunma", baslik="Okunma",
                                     kategori=_kategori(), durum=Haber.DURUM_AKTIF,
                                     yayin_zamani=timezone.now())

    def test_yetim_kova_ayiklanir(self):
        bugun = timezone.localdate()
        yazilan = okunma.kovalari_yaz({(self.h.pk, bugun): 2, (999999999, bugun): 1})
        self.assertEqual(yazilan, 1)
        self.assertEqual(Okunma.objects.get(haber=self.h).adet, 2)
        self.assertFalse(Okunma.objects.filter(haber_id=999999999).exists())
        connection.check_constraints()   # dış işlemde bekleyen ihlal kalmadı


@skipUnless(PG, "PostgreSQL'de kısmi indeks kurulumu")
class PgKismiIndeksler(TestCase):

    def _indeksler(self, tablo):
        with connection.cursor() as c:
            c.execute("SELECT indexname, indexdef FROM pg_indexes WHERE tablename = %s", [tablo])
            return dict(c.fetchall())

    def test_kismi_indeksler_kosulla_kurulu(self):
        ind = self._indeksler("icerik_haber")
        self.assertIn("WHERE ((durum = 1) AND (yayin_zamani IS NOT NULL))", ind["haber_okur_kismi"])
        self.assertIn("WHERE (NOT ((hazirlik)::text = ''::text))", ind["haber_masa_kismi"])
        for ad in ("haber_kategori_sira", "haber_ilce_sira", "haber_olusturan_sira",
                   "haber_siralama"):
            self.assertIn(ad, ind)

    def test_tek_sutunlu_indeksler_dustu(self):
        ind = self._indeksler("icerik_haber")
        for ad in ("icerik_haber_kategori_id_44e1a6d4", "icerik_haber_ilce_id_f7d38216",
                   "icerik_haber_olusturan_id_e0c72ac9", "icerik_haber_yayin_zamani_659599b2"):
            self.assertNotIn(ad, ind)
        self.assertNotIn("icerik_konuhaber_konu_id_df6efd6d", self._indeksler("icerik_konuhaber"))
