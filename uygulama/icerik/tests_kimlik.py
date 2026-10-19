"""Yeni kimlik stratejisi — `icerik/kimlik.py` (Paket F madde 1).

Kilitlenen kararlar:

1. Panelin kimlikleri eski sitenin aralığından AYRI bir tabandan başlar
   (varsayılan 5.000.000); tabanın altındaki kimlikler hesaba girmez.
2. Kimliği veren TEK işlev vardır; panel formu, yapay zekâ taslağı ve
   eczane komutu aynı işlevden geçer.
3. Kayıt `force_insert` ile yazılır: aynı adayı hesaplayan iki istek
   birbirinin kaydını EZEMEZ; ikincisi yeniden dener ve bir sonrakini alır.
"""

import threading
from unittest.mock import patch

from django.contrib.auth.models import Group, User
from django.core.management import call_command
from django.db import IntegrityError, connection
from django.test import TestCase, TransactionTestCase, override_settings

from taksonomi.models import Etiket, Kategori, KategoriTur

from . import kimlik
from .models import Haber


def _kategori():
    return KategoriTur.objects.get(tur=Kategori.TUR_HABER, slug="gundem").kategori


class KimlikTabani(TestCase):

    @classmethod
    def setUpTestData(cls):
        call_command("taksonomi_kur", verbosity=0)
        cls.kategori = _kategori()

    def test_bos_tabloda_taban_doner(self):
        self.assertEqual(kimlik.aday_kimlik(Haber), 5_000_000)

    def test_eski_aralik_hesaba_girmez(self):
        Haber.objects.create(id=1_732_500, slug="e", baslik="Eski", kategori=self.kategori)
        Haber.objects.create(id=1_696_274, slug="c", baslik="Çakışan", kategori=self.kategori)
        self.assertEqual(kimlik.aday_kimlik(Haber), 5_000_000)

    def test_taban_ustunde_en_buyuk_arti_bir(self):
        Haber.objects.create(id=5_000_041, slug="p", baslik="Panel", kategori=self.kategori)
        self.assertEqual(kimlik.aday_kimlik(Haber), 5_000_042)

    @override_settings(BH_YENI_KIMLIK_TABANI=7_000_000)
    def test_taban_ayarla_degisir(self):
        self.assertEqual(kimlik.aday_kimlik(Haber), 7_000_000)

    @override_settings(BH_YENI_KIMLIK_TABANI=1000)
    def test_taban_eski_araliga_dusurulemez(self):
        """Yanlış ayar sessizce canlıyla çakışma doğurmasın."""
        self.assertGreaterEqual(kimlik.taban(), 2_000_000)

    def test_var_olan_kaydin_ustune_yazilmaz(self):
        """Aday bayatsa (başka istek yazdı) kayıt ezilmez, sıradakini alır."""
        var_olan = Haber.objects.create(id=5_000_000, slug="ilk", baslik="İlk",
                                        kategori=self.kategori)
        adaylar = iter([5_000_000, 5_000_001])
        yeni = Haber(slug="ikinci", baslik="İkinci", kategori=self.kategori)
        with patch.object(kimlik, "aday_kimlik", lambda model: next(adaylar)):
            kimlik.yeni_kayit_kaydet(yeni)
        self.assertEqual(yeni.pk, 5_000_001)
        var_olan.refresh_from_db()
        self.assertEqual(var_olan.baslik, "İlk")

    def test_kimlik_disi_butunluk_hatasi_yeniden_denenmez(self):
        """Boş zorunlu alan gibi hatalar tekrar denemekle düzelmez."""
        bozuk = Haber(slug="b", baslik=None, kategori=self.kategori)
        with self.assertRaises(IntegrityError):
            kimlik.yeni_kayit_kaydet(bozuk)


class UcYolAyniKimlik(TestCase):
    """Panel formu, yapay zekâ taslağı ve eczane komutu aynı kuraldan geçer."""

    @classmethod
    def setUpTestData(cls):
        call_command("taksonomi_kur", verbosity=0)
        call_command("roller_kur", verbosity=0)
        cls.kategori = _kategori()
        cls.editor = User.objects.create_user("editor-k", password="x")
        cls.editor.groups.add(Group.objects.get(name="Editör"))
        Haber.objects.create(id=1_732_500, slug="e", baslik="Eski", kategori=cls.kategori)

    def test_panel_formu_tabandan_verir(self):
        self.client.force_login(self.editor)
        yanit = self.client.post("/panel/haber/ekle", {
            "baslik": "Panelden ilk haber", "kategori": self.kategori.pk,
            "durum": Haber.DURUM_PASIF,
            "hazirlik": "taslak", "spot": "", "govde": "", "etiketler": "",
        })
        self.assertEqual(yanit.status_code, 302, getattr(yanit, "context", None)
                         and yanit.context["form"].errors)
        haber = Haber.objects.get(baslik="Panelden ilk haber")
        self.assertEqual(haber.pk, 5_000_000)
        self.assertEqual(haber.slug, "panelden-ilk-haber")

    def test_eczane_komutu_ayni_isleve_baglidir(self):
        """Komutun kaynağında kendi kimlik hesabı kalmamalı."""
        from pathlib import Path
        kaynak = (Path(__file__).parent / "management" / "commands"
                  / "eczane_haberi.py").read_text(encoding="utf-8")
        self.assertIn("yeni_kayit_kaydet", kaynak)
        self.assertNotIn('order_by("-id")', kaynak)

    def test_kopyalar_kalmadi(self):
        """"En büyük + 1" kuralının eski kopyaları geri gelmesin."""
        from pathlib import Path
        kok = Path(__file__).parent
        for ad in ("panel.py", "yz_kopru.py"):
            with self.subTest(dosya=ad):
                metin = (kok / ad).read_text(encoding="utf-8")
                self.assertNotIn('order_by("-id").values_list("id", flat=True).first()',
                                 metin)


class EszamanliKayit(TransactionTestCase):
    """İki bağlantı aynı adayı hesaplar; ikisi de kaydedilir, biri ezilmez.

    Gerçek iki veritabanı bağlantısıyla (iki iş parçacığı). Sıra
    belirlenimli: ikisi de adayı hesaplamadan hiçbiri yazmaz (bariyer),
    sonra ilki yazar, ikincisi bayat adayla dener ve yeniden hesaplar.
    """

    def test_ayni_adayi_hesaplayan_iki_kayit_cakismaz(self):
        call_command("taksonomi_kur", verbosity=0)
        kategori_id = _kategori().pk

        asil = kimlik.aday_kimlik
        bariyer = threading.Barrier(2, timeout=20)
        ilki_yazdi = threading.Event()
        ilk_cagri = {}
        kilit = threading.Lock()
        sonuc, hatalar = {}, []

        def bekleten_aday(model):
            aday = asil(model)
            ad = threading.current_thread().name
            with kilit:
                ilk_mi = ad not in ilk_cagri
                ilk_cagri.setdefault(ad, aday)
            if ilk_mi:
                bariyer.wait()                 # ikisi de aynı adayı gördü
                if ad == "ikinci":
                    ilki_yazdi.wait(timeout=20)
            return aday

        def is_parcacigi():
            ad = threading.current_thread().name
            try:
                haber = Haber(slug=ad, baslik=ad, kategori_id=kategori_id)
                kimlik.yeni_kayit_kaydet(haber)
                sonuc[ad] = haber.pk
            except Exception as e:             # noqa: BLE001 — teste taşınır
                hatalar.append(repr(e))
            finally:
                if ad == "birinci":
                    ilki_yazdi.set()
                connection.close()

        with patch.object(kimlik, "aday_kimlik", bekleten_aday):
            parcalar = [threading.Thread(target=is_parcacigi, name=n)
                        for n in ("birinci", "ikinci")]
            for p in parcalar:
                p.start()
            for p in parcalar:
                p.join(timeout=60)

        self.assertEqual(hatalar, [])
        self.assertEqual(ilk_cagri["birinci"], ilk_cagri["ikinci"],
                         "Yarış kurulamadı: iki bağlantı aynı adayı görmedi.")
        self.assertEqual(sorted(sonuc.values()), [5_000_000, 5_000_001])
        self.assertEqual(Haber.objects.get(pk=5_000_000).baslik, "birinci")
        self.assertEqual(Haber.objects.get(pk=5_000_001).baslik, "ikinci")
