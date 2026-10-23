"""Yavaş sorgu günlüğü toplu komutlarda varsayılan kapalı (Paket L2)."""

from __future__ import annotations

from unittest import mock

from django.db import connection
from django.test import SimpleTestCase, TestCase, override_settings

from . import yavas_sorgu
from .models import Haber


class KomutTanima(SimpleTestCase):

    def test_komut_adi(self):
        self.assertEqual(yavas_sorgu.komut_adi(["manage.py", "arama_doldur"]), "arama_doldur")
        self.assertEqual(yavas_sorgu.komut_adi(["/srv/x/manage.py", "pg_goc"]), "pg_goc")
        self.assertIsNone(yavas_sorgu.komut_adi(["gunicorn", "cekirdek.wsgi"]))
        self.assertIsNone(yavas_sorgu.komut_adi(["manage.py"]))

    def test_sunucu_ve_test_toplu_sayilmaz(self):
        for argv in (["manage.py", "runserver", "8731"], ["manage.py", "test"],
                     ["gunicorn", "cekirdek.wsgi"]):
            with self.subTest(argv):
                self.assertFalse(yavas_sorgu.toplu_komut_mu(argv))
        for argv in (["manage.py", "arama_doldur"], ["manage.py", "goc_al"],
                     ["manage.py", "migrate"]):
            with self.subTest(argv):
                self.assertTrue(yavas_sorgu.toplu_komut_mu(argv))


class TopluKomutEsigi(TestCase):

    @override_settings(YAVAS_SORGU_MS=0, YAVAS_SORGU_KOMUT_MS=0)
    def test_toplu_komutta_varsayilan_sessiz(self):
        with mock.patch.object(yavas_sorgu, "_TOPLU", True), \
                mock.patch.object(yavas_sorgu.gunluk, "warning") as uyari:
            self.assertEqual(yavas_sorgu.esik_ms(), 0)
            Haber.objects.count()
        uyari.assert_not_called()

    @override_settings(YAVAS_SORGU_MS=10_000, YAVAS_SORGU_KOMUT_MS=1)
    def test_toplu_komutta_esik_acilabilir(self):
        with mock.patch.object(yavas_sorgu, "_TOPLU", True):
            self.assertEqual(yavas_sorgu.esik_ms(), 1)
            with mock.patch("time.perf_counter", side_effect=[0.0, 0.005]), \
                    self.assertLogs("bh.yavas_sorgu", "WARNING"):
                yavas_sorgu.sarmalayici(lambda *a: None, "SELECT 1", (), False, {})

    def test_toplu_komutta_sarmalayici_takilmaz(self):
        sahte = mock.Mock(execute_wrappers=[])
        with mock.patch.object(yavas_sorgu, "_TOPLU", True), \
                override_settings(YAVAS_SORGU_KOMUT_MS=0):
            yavas_sorgu._tak(None, sahte)
        self.assertEqual(sahte.execute_wrappers, [])
        with mock.patch.object(yavas_sorgu, "_TOPLU", False):
            yavas_sorgu._tak(None, sahte)
        self.assertEqual(sahte.execute_wrappers, [yavas_sorgu.sarmalayici])

    def test_test_kosusunda_sunucu_esigi_gecerli(self):
        self.assertFalse(yavas_sorgu._TOPLU)
        self.assertIn(yavas_sorgu.sarmalayici, connection.execute_wrappers)
