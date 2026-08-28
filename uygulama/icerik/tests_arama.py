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


class AramaGorunumuKazanimlari(TestCase):
    """Migration gerektirmeyen iki kazanım ve okurun gördüğü.

    27 Ağustos 2026 ölçüm turu: arama sorgu başına iki tam tarama yapıyor ve
    liste sayfaları kullanmadıkları `govde` alanını çekiyordu.
    """

    @classmethod
    def setUpTestData(cls):
        from django.core.management import call_command
        from django.utils import timezone

        from taksonomi.models import Kategori, KategoriTur

        from .models import Haber
        call_command("taksonomi_kur", verbosity=0)
        cls.kategori = Kategori.objects.get(ad="GÜNDEM")
        simdi = timezone.now()
        for i in range(30):
            Haber.objects.create(
                id=9000 + i, slug=f"deneme-{i}", baslik=f"Deneme haberi {i} ışık",
                spot="Spot metni", govde="<p>Gövde</p>" * 50,
                kategori=cls.kategori, durum=Haber.DURUM_AKTIF,
                yayin_zamani=simdi)

    def test_liste_ertelenmis_alan_tasimiyor(self):
        """`.defer("govde")` geri alındı: ölçülemeyen kazanç, sessiz N+1 riski.

        Ertelenmiş alan bırakmamak bir karardır; bu test onu kilitler.
        """
        from .views import _liste
        kayit = _liste().first()
        self.assertEqual(kayit.get_deferred_fields(), set())

    def test_detay_sayfasi_govdeyi_hala_basiyor(self):
        """`_liste()`ten gövde düşürüldü; detay sayfası ETKİLENMEMELİ."""
        from .models import Haber
        kayit = Haber.objects.get(pk=9000)
        yanit = self.client.get(kayit.get_absolute_url())
        self.assertEqual(yanit.status_code, 200)
        self.assertContains(yanit, "Gövde")

    def test_sayim_ust_sinirda_kesiliyor(self):
        from .views import SinirliSayfalayici
        from .models import Haber

        class Kucuk(SinirliSayfalayici):
            UST_SINIR = 10

        s = Kucuk(Haber.objects.all(), 20)
        self.assertEqual(s.count, 10)
        self.assertTrue(s.kesildi_mi)

    def test_sinir_altinda_kesin_sayi(self):
        from .views import SinirliSayfalayici
        from .models import Haber
        s = SinirliSayfalayici(Haber.objects.filter(pk=9000), 20)
        self.assertEqual(s.count, 1)
        self.assertFalse(s.kesildi_mi)

    def test_okura_gosterilen_sayi(self):
        yanit = self.client.get("/ara", {"q": "ışık"})
        self.assertContains(yanit, "30 sonuç")

    def test_cok_genel_sorgu_aranmiyor(self):
        """Durak kelime: veritabanına HİÇ gidilmemeli."""
        from django.db import connection
        from django.test.utils import CaptureQueriesContext
        with CaptureQueriesContext(connection) as yakala:
            yanit = self.client.get("/ara", {"q": "ve"})
        self.assertContains(yanit, "çok genel kelimelerle arama yapılamıyor")
        # Sayfa kabuğu (son dakika bandı, kategori bandı) zaten `icerik_haber`
        # sorguluyor; ölçülmesi gereken ARAMANIN kendisi, yani LIKE taraması.
        tarama = [s["sql"] for s in yakala.captured_queries if "LIKE" in s["sql"].upper()]
        self.assertEqual(tarama, [], f"durak sorgusu icin tarama acildi: {tarama[:1]}")

    def test_kisa_sorgu_aranmiyor(self):
        yanit = self.client.get("/ara", {"q": "a"})
        self.assertContains(yanit, "en az 3 harflik")
        self.assertNotContains(yanit, "sonuç bulunamadı")

    def test_normal_sorgu_hala_calisiyor(self):
        yanit = self.client.get("/ara", {"q": "Deneme"})
        self.assertEqual(yanit.status_code, 200)
        self.assertContains(yanit, "Deneme haberi")

    def test_bos_sorgu(self):
        yanit = self.client.get("/ara")
        self.assertEqual(yanit.status_code, 200)
        self.assertContains(yanit, "Aramak istediğiniz kelimeyi yazın")

    def test_turkce_kusuru_HENUZ_DURUYOR(self):
        """Bu tur harf kusurunu ÇÖZMEDİ; indeks çözecek.

        Test bunu bilerek kilitliyor: kusur sessizce "çözüldü" sanılmasın.
        Düzeltildiğinde bu test kırılacak ve o an bilinçli güncellenecek.
        """
        kucuk = self.client.get("/ara", {"q": "ışık"})
        buyuk = self.client.get("/ara", {"q": "IŞIK"})
        self.assertContains(kucuk, "30 sonuç")
        self.assertContains(buyuk, "sonuç bulunamadı")


class CokKelimeliSorguKenarDurumlari(TestCase):
    """Durak/kısa terim TEK BAŞINA sorguyu reddettirmez.

    Kural: durak ve kısa terimler **atılır**, kalanla aranır; arama ancak
    geriye hiç aranabilir terim kalmazsa reddedilir. Aksi hâlde
    "bursa ve çevresi" arayan okur, içinde "ve" geçtiği için sonuç alamazdı —
    bu, giderilmek istenen kusurdan daha kötü olurdu.
    """

    def _kapi(self, q):
        """`icerik.views.arama` kapısının aynısı."""
        from .views import ARAMA_EN_AZ
        c = sorgu_coz(q)
        if not c:
            return None, c.sebep
        if max(len(t.kelime) for t in c.terimler) < ARAMA_EN_AZ:
            return None, "kisa"
        return [t.kelime for t in c.terimler], ""

    def test_durak_atilir_kalanla_aranir(self):
        terimler, sebep = self._kapi("bursa ve çevresi")
        self.assertEqual(terimler, ["bursa", "cevresi"])
        self.assertEqual(sebep, "")
        self.assertEqual(sorgu_coz("bursa ve çevresi").dusen_durak, ("ve",))

    def test_kisa_terim_sorguyu_reddettirmez(self):
        terimler, sebep = self._kapi("su ürünleri")
        self.assertEqual(terimler, ["urunleri"])
        self.assertEqual(sebep, "")

    def test_kisa_terim_uzun_terimle_birlikte_korunur(self):
        """'a takımı' — 'a' durak değil, yalnız öneksiz aranır; atılmaz."""
        terimler, sebep = self._kapi("a takımı")
        self.assertEqual(terimler, ["a", "takimi"])
        c = sorgu_coz("a takımı")
        self.assertFalse(c.terimler[0].onek)   # 'a' önek almaz
        self.assertTrue(c.terimler[1].onek)    # 'takimi' alır

    def test_araya_giren_durak_sorguyu_bozmuyor(self):
        terimler, _ = self._kapi("trafik kazası ve yangın")
        self.assertEqual(terimler, ["trafik", "kazasi", "yangin"])

    def test_yalniz_hepsi_atilinca_reddedilir(self):
        self.assertEqual(self._kapi("ve")[1], "hepsi_durak")
        self.assertEqual(self._kapi("bir ve")[1], "hepsi_durak")
        self.assertEqual(self._kapi("dr öz")[1], "kisa")   # ikisi de 2 harf

    def test_gazete_icin_anlamli_kelimeler_durak_degil(self):
        """Durak listesi haber aramasını körleştirmemeli."""
        for kelime in ("son", "büyük", "var", "yok", "dakika", "yeni", "ilk",
                       "kim", "artık", "az", "genç", "beyaz"):
            with self.subTest(kelime=kelime):
                self.assertFalse(durak_mi(kelime),
                                 f"'{kelime}' haber aramasında anlamlı, durak olmamalı")


class MenuSiralamasiOnbellekli(TestCase):
    """Tam menü sıralaması her istekte yeniden sayılmamalı.

    Ölçüm (27 Ağustos 2026, 308.602 haber): `annotate(Count("haberler"))`
    **1.113 ms** sürüyordu ve bağlam işlemcisi her sayfada çalıştığı için
    sitenin tamamı bu bedeli ödüyordu. `adet` ekranda gösterilmiyor,
    yalnız sıralama için.
    """

    @classmethod
    def setUpTestData(cls):
        from django.core.management import call_command
        call_command("taksonomi_kur", verbosity=0)

    def setUp(self):
        from icerik import baglam
        baglam._menu_bellek = None

    def tearDown(self):
        from icerik import baglam
        baglam._menu_bellek = None

    def test_ikinci_cagri_veritabanina_gitmiyor(self):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        from icerik.baglam import _tum_kategoriler
        ilk = _tum_kategoriler()
        with CaptureQueriesContext(connection) as yakala:
            ikinci = _tum_kategoriler()
        self.assertEqual(ilk, ikinci)
        self.assertEqual(len(yakala.captured_queries), 0)

    def test_sayim_kilitliyken_menu_yine_ciziliyor(self):
        from unittest import mock

        from django.db import DatabaseError

        from icerik import baglam
        with mock.patch.object(baglam.Kategori.objects, "filter",
                               side_effect=DatabaseError("database is locked")):
            try:
                sonuc = baglam._tum_kategoriler()
            except DatabaseError:
                self.fail("sayım kilidi menüyü düşürdü")
        self.assertEqual(sonuc, [])   # menü boş çizilir, sayfa düşmez

    def test_sayfa_her_istekte_toplama_yapmiyor(self):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext
        self.client.get("/ilceler")
        with CaptureQueriesContext(connection) as yakala:
            self.client.get("/ilceler")
        toplama = [s["sql"] for s in yakala.captured_queries
                   if "COUNT" in s["sql"].upper() and "icerik_haber" in s["sql"]]
        self.assertEqual(toplama, [], f"her istekte toplama sorgusu açılıyor: {toplama[:1]}")


class SayfaSorguProfili(TestCase):
    """Sayfa başına SQL sorgu sayısı — N+1 gerileme kilidi.

    Ölçüm (28 Ağustos 2026): `/yazarlar` 83 sorgu açıyordu, 74'ü
    `medya_koseyazisi` üzerinde. Sebep `Yazar.son_yazi` özelliğinin yazar
    başına sorgu atması ve şablonun onu iki kez çağırması.
    """

    @classmethod
    def setUpTestData(cls):
        from django.core.management import call_command
        from django.utils import timezone

        from medya.models import KoseYazisi, Yazar
        call_command("taksonomi_kur", verbosity=0)
        from datetime import timedelta
        simdi = timezone.now()
        for i in range(12):
            y = Yazar.objects.create(id=700 + i, slug=f"yazar-{i}", ad=f"Yazar {i}",
                                     sayfasi_tarandi=True)
            for j in range(3):
                # Zamanlar AYRIK olmalı: eşit olsaydı "en yeni yazı"
                # sıralaması belirsiz kalır ve test kodu değil veriyi ölçerdi.
                KoseYazisi.objects.create(
                    id=8000 + i * 10 + j, slug=f"yazi-{i}-{j}",
                    baslik=f"Yazar {i} yazi {j}", yazar=y,
                    durum=KoseYazisi.DURUM_AKTIF,
                    yayin_zamani=simdi - timedelta(days=10 - j))

    def setUp(self):
        from icerik import baglam
        baglam._menu_bellek = None
        self.client.get("/ilceler")      # menü önbelleğini ısıt

    def _sorgu_sayisi(self, yol):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext
        with CaptureQueriesContext(connection) as y:
            yanit = self.client.get(yol)
        self.assertEqual(yanit.status_code, 200)
        return len(y.captured_queries), y.captured_queries

    def test_yazar_listesi_son_yaziyi_iki_kez_sormuyor(self):
        """Yazar başına EN ÇOK BİR köşe sorgusu.

        Şablon `{% if y.son_yazi %}{{ y.son_yazi }}` yazımıyla özelliği iki
        kez çağırıyordu: 37 yazar → 74 sorgu. `with` ile tek çağrıya indi.

        Sorguyu tümden kaldırmak DENENDİ ve geri alındı: tek sorguyla harita
        kurmak 6.713 satır çekip 42,9 ms sürüyor, yazar başına indeks
        araması 19,0 ms. Az sorgu her zaman hızlı değildir.
        """
        from medya.models import Yazar
        yazar_adedi = Yazar.listedekiler().count()
        _, sorgular = self._sorgu_sayisi("/yazarlar")
        kose = [s for s in sorgular if "medya_koseyazisi" in s["sql"]]
        self.assertLessEqual(
            len(kose), yazar_adedi,
            f"{yazar_adedi} yazar için {len(kose)} köşe sorgusu — çift çağrı geri gelmiş")

    def test_yazar_listesi_son_yaziyi_hala_gosteriyor(self):
        govde = self.client.get("/yazarlar").content.decode()
        self.assertIn("Yazar 0 yazi 2", govde)     # en yeni yazı
        self.assertNotIn("Yazar 0 yazi 0", govde)  # en eski gösterilmemeli

    def test_anasayfa_yazar_kutusu_cift_sormuyor(self):
        """Sağ raydaki yazar kutusu 5 yazar gösteriyor; `son_yazi` yazar
        başına bir kez sorulmalı (+1 arşiv sayımı meşru)."""
        _, sorgular = self._sorgu_sayisi("/")
        kose = [s for s in sorgular if "medya_koseyazisi" in s["sql"]]
        sayim = [s for s in kose if "COUNT" in s["sql"].upper()]
        self.assertLessEqual(len(kose) - len(sayim), 5,
                             f"5 yazar için {len(kose) - len(sayim)} sorgu")

    def test_kategori_sayimi_sinirli(self):
        from icerik.views import SinirliSayfalayici
        yanit = self.client.get("/gundem")
        self.assertEqual(yanit.status_code, 200)
        self.assertIsInstance(yanit.context["sayfa"].paginator, SinirliSayfalayici)

    def test_ilce_sayimi_sinirli(self):
        from icerik.views import SinirliSayfalayici
        yanit = self.client.get("/ilce/osmangazi")
        self.assertEqual(yanit.status_code, 200)
        self.assertIsInstance(yanit.context["sayfa"].paginator, SinirliSayfalayici)
