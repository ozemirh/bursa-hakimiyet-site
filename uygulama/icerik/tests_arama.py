# -*- coding: utf-8 -*-
"""Arama normalizasyon çekirdeği — gerileme testleri.

Vakalar uydurma değil: 27 Ağustos 2026'da 308.602 kayıt üzerinde ölçülen
kusurların kilitlenmiş hâli (URUN-PLANI.md F7 ölçüm turu).
"""

import json
import unicodedata
from pathlib import Path

from django.test import TestCase

from .arama_metni import (ONEK_EN_AZ, Cozum, anahtar, durak_mi, kelimeler,
                          sorgu_coz)


class TurkceAnahtar(TestCase):
    """Aynı kelimenin her yazımı AYNI anahtara düşmeli."""

    def test_isik_uc_yazim_ayni_anahtar(self):
        # Ölçüm: bugünkü arama bu üçüne 1.880 / 428 / 0 sonuç veriyordu.
        self.assertEqual(anahtar("ışık"), anahtar("Işık"))
        self.assertEqual(anahtar("Işık"), anahtar("IŞIK"))
        self.assertEqual(anahtar("IŞIK"), "isik")

    def test_olculen_diger_kelimeler(self):
        for yazimlar, beklenen in (
            (("çağrı", "Çağrı", "ÇAĞRI"), "cagri"),
            (("öğrenci", "Öğrenci", "ÖĞRENCİ"), "ogrenci"),
            (("İnegöl", "İNEGÖL", "inegöl"), "inegol"),
            (("bursa", "Bursa", "BURSA", "BuRsA"), "bursa"),
        ):
            with self.subTest(beklenen=beklenen):
                self.assertEqual({anahtar(y) for y in yazimlar}, {beklenen})

    def test_ascii_yazan_okur_da_bulur(self):
        """Okur çoğu zaman diyakritiksiz yazar."""
        self.assertEqual(anahtar("ogrenci"), anahtar("öğrenci"))
        self.assertEqual(anahtar("isik"), anahtar("ışık"))
        self.assertEqual(anahtar("cagri"), anahtar("çağrı"))
        self.assertEqual(anahtar("inegol"), anahtar("İnegöl"))

    def test_bos_ve_none(self):
        self.assertEqual(anahtar(None), "")
        self.assertEqual(anahtar(""), "")


class PythonLowerTuzagi(TestCase):
    """`str.lower()` KULLANILMAMALI — bozduğu iki vaka burada kilitli.

    Bu test kodun ne yaptığını değil, **neden böyle yaptığını** korur:
    biri "sadeleştirip" `.lower()`a dönerse burası kırılır.
    """

    def test_lower_inegol_yedi_karakterlik_bozuk_dize_uretir(self):
        bozuk = "İNEGÖL".lower()
        # 'i' + U+0307 COMBINING DOT ABOVE — gözle 'inegöl' görünür ama değildir
        self.assertEqual(len(bozuk), 7)
        self.assertIn("̇", bozuk)
        self.assertNotEqual(bozuk, "inegöl")
        # Bizim yolumuz doğru sonucu verir
        self.assertEqual(anahtar("İNEGÖL"), "inegol")
        self.assertEqual(len(anahtar("İNEGÖL")), 6)

    def test_lower_isik_yanlis_harf_uretir(self):
        self.assertEqual("IŞIK".lower(), "işik")      # I -> i (yanlış), doğrusu ı
        self.assertNotEqual("IŞIK".lower(), "ışık")
        self.assertEqual(anahtar("IŞIK"), anahtar("ışık"))

    def test_upper_de_bozuyor(self):
        self.assertEqual("Ekonomi".upper(), "EKONOMI")   # doğrusu EKONOMİ
        self.assertNotEqual("Ekonomi".upper(), "EKONOMİ")

    def test_anahtar_birlesen_isaret_birakmiyor(self):
        for kelime in ("İNEGÖL", "İstanbul", "İzmir", "ÖĞRENCİ"):
            with self.subTest(kelime=kelime):
                a = anahtar(kelime)
                self.assertEqual(a, unicodedata.normalize("NFC", a))
                self.assertFalse(any(unicodedata.combining(c) for c in a))


class DurakListesiVeridir(TestCase):
    """Durak listesi KOD DEĞİL VERİ; dosyadan gelir ve düzenlenebilir."""

    DOSYA = Path(__file__).resolve().parent / "veri" / "turkce_durak.json"

    def test_dosya_var_ve_gecerli(self):
        self.assertTrue(self.DOSYA.exists())
        veri = json.loads(self.DOSYA.read_text(encoding="utf-8"))
        self.assertIn("kelimeler", veri)
        self.assertGreater(len(veri["kelimeler"]), 20)

    def test_olculen_yavas_kelimeler_durak(self):
        # Ölçüm: en yavaş üç sorgu 'bir' 424 ms, 've' 412 ms.
        self.assertTrue(durak_mi("bir"))
        self.assertTrue(durak_mi("ve"))

    def test_dogal_yazim_da_eslesir(self):
        """Dosya doğal yazımıyla duruyor; karşılaştırma normalize edilir."""
        self.assertTrue(durak_mi("çünkü"))
        self.assertTrue(durak_mi("ÇÜNKÜ"))
        self.assertTrue(durak_mi("cunku"))
        self.assertTrue(durak_mi("için"))

    def test_icerik_kelimesi_durak_degil(self):
        for kelime in ("bursa", "ışık", "deprem", "belediye", "öğrenci", "trafik"):
            with self.subTest(kelime=kelime):
                self.assertFalse(durak_mi(kelime))

    def test_kod_icinde_gomulu_liste_yok(self):
        kaynak = (Path(__file__).resolve().parent / "arama_metni.py").read_text(encoding="utf-8")
        # Liste dosyadan okunmalı; modülün içinde kelime dizisi olmamalı.
        self.assertIn("turkce_durak.json", kaynak)
        self.assertNotIn('"acaba"', kaynak)


class SorguCozme(TestCase):

    def test_tek_kelime_onekli(self):
        c = sorgu_coz("ışık")
        self.assertEqual([t.kelime for t in c.terimler], ["isik"])
        self.assertTrue(c.terimler[0].onek)

    def test_kisa_kelimeye_onek_uygulanmaz(self):
        """Ölçüm: 'a*' p95'i 235 ms'den 504 ms'ye çıkarıyordu."""
        c = sorgu_coz("a")
        self.assertEqual(len(c.terimler), 1)
        self.assertFalse(c.terimler[0].onek)
        for kisa in ("ab", "x"):
            self.assertFalse(sorgu_coz(kisa).terimler[0].onek)
        self.assertTrue(sorgu_coz("abc").terimler[0].onek)
        self.assertEqual(ONEK_EN_AZ, 3)

    def test_durak_kelime_dusuruluyor(self):
        c = sorgu_coz("trafik kazası ve yangın")
        self.assertEqual([t.kelime for t in c.terimler], ["trafik", "kazasi", "yangin"])
        self.assertEqual(c.dusen_durak, ("ve",))

    def test_hepsi_durak_ise_arama_yapilmaz(self):
        c = sorgu_coz("ve bir")
        self.assertFalse(c)
        self.assertEqual(c.sebep, "hepsi_durak")
        self.assertEqual(set(c.dusen_durak), {"bir", "ve"})

    def test_bos_sorgu(self):
        for bos in ("", "   ", None, "!!! ???"):
            c = sorgu_coz(bos)
            self.assertFalse(c)
            self.assertEqual(c.sebep, "bos")

    def test_yazim_farki_ayni_cozume_gider(self):
        a = sorgu_coz("IŞIK ÇAĞRI")
        b = sorgu_coz("ışık çağrı")
        self.assertEqual([t.kelime for t in a.terimler], [t.kelime for t in b.terimler])

    def test_noktalama_ayirici(self):
        self.assertEqual(kelimeler("bursa'da, trafik!"), ["bursa", "da", "trafik"])

    def test_cozum_motora_bagli_degil(self):
        """Çekirdek FTS5/PostgreSQL sözdizimi ÜRETMEZ — taşınabilirlik şartı."""
        kaynak = (Path(__file__).resolve().parent / "arama_metni.py").read_text(encoding="utf-8")
        for motor in ("MATCH", "to_tsquery", "tsvector", "fts5", "LIKE"):
            self.assertNotIn(motor + "(", kaynak)
        self.assertIsInstance(sorgu_coz("ışık"), Cozum)
