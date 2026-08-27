"""Göç kapılarının gerileme testleri.

Ayrı dosyada duruyor: `tests.py` ve `tests_panel*.py` başka iş kollarının
alanı, göç kuralları burada toplanıyor.
"""

from django.test import SimpleTestCase

from .goc_kaynak import kaynak_kabul


class KaynakKabulKapisi(SimpleTestCase):
    """27 Ağustos 2026 ölçümündeki 148 kaynak kaydından türetilmiştir."""

    def test_gercek_kaynaklar_kabul_edilir(self):
        for ad in ("AA", "İHA", "DHA", "BBC", "Milliyet", "Sözcü",
                   "Independent Türkçe", "Deutsche Welle Türkçe",
                   "TRT Haber", "Our World in Data", "Anadolu Ajansı"):
            with self.subTest(ad=ad):
                kabul, neden = kaynak_kabul(ad)
                self.assertTrue(kabul, f"{ad} reddedildi: {neden}")

    def test_meta_yazar_degeri_kaynak_degildir(self):
        """PANEL-NOTLARI §7'nin altı değeri künye türüdür, kaynak değil.

        En ağır kalem: tek başına 270.508 haber bu değere bağlanmıştı.
        """
        for ad in ("Haber Merkezi", "haber merkezi", "Fikir İşçisi", "Bülten",
                   "Haber Ajansı", "İçerik Aktarımı", "Alıntı/İktibas"):
            with self.subTest(ad=ad):
                kabul, neden = kaynak_kabul(ad)
                self.assertFalse(kabul)
                self.assertEqual(neden, "meta yazar degeri")

    def test_kendi_yayinimiz_kaynak_diye_anilmaz(self):
        for ad in ("Bursa Hakimiyet", "bursahakimiyet.com.tr",
                   "Bu rsahakimiyet"):
            with self.subTest(ad=ad):
                self.assertFalse(kaynak_kabul(ad)[0])

    def test_kirk_karakterde_kesik_reddedilir(self):
        ad = "MHP Genel Başkanı Bahçeli grup toplantıs"
        self.assertEqual(len(ad), 40)
        self.assertEqual(kaynak_kabul(ad), (False, "40 karakterde kesik"))

    def test_govdeden_dusen_kelimeler_reddedilir(self):
        for ad in ("ve", "suyu", "aktardi", "holding", "tedarik", "yapildi",
                   "kodu", "verimliligi"):
            with self.subTest(ad=ad):
                self.assertEqual(
                    kaynak_kabul(ad)[1], "buyuk harfsiz (cumle parcasi)")

    def test_salt_sayi_ve_alan_adi_reddedilir(self):
        self.assertEqual(kaynak_kabul("525218"), (False, "salt sayi"))
        self.assertEqual(kaynak_kabul("https"), (False, "alan adi"))
        self.assertEqual(kaynak_kabul("www.sondakika.com"), (False, "alan adi"))

    def test_bos_deger_reddedilir(self):
        for ad in ("", "   ", None):
            with self.subTest(ad=ad):
                self.assertEqual(kaynak_kabul(ad), (False, "bos"))

    def test_bosluk_normalize_edilir(self):
        self.assertTrue(kaynak_kabul("  TRT   Haber ")[0])
