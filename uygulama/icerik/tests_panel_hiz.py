"""Panel başarım düzeltmeleri — 28 Ağustos 2026.

Ölçülen üç sorun ve testlerle kilitlenen davranışları:

1. `/panel/haber/ekle` **36.544.411 bayt** indiriyordu; `ilgili_haberler`
   alanı 356.839 `<option>` basıyordu.
2. `/panel/` (Bugün) 2.287 ms; sebep sorgu planıydı, render değil.
3. `/panel/mansetler` 3.851 ms; ekran altı tam tarama çalıştırıyordu.
"""

from django.contrib.auth.models import Group, User
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from taksonomi.models import Kategori, KategoriTur

from .formlar import HaberForm, SecilenlerWidget
from .models import Haber

PAROLA = "deneme-parola-123"


class IlgiliHaberSecicisi(TestCase):
    """356 bin `<option>` sorunu ve arama tabanlı çözümü."""

    @classmethod
    def setUpTestData(cls):
        call_command("taksonomi_kur", verbosity=0)
        call_command("roller_kur", verbosity=0)
        cls.kategori = KategoriTur.objects.get(
            tur=Kategori.TUR_HABER, slug="gundem").kategori
        cls.yonetmen = User.objects.create_user("hy", password=PAROLA)
        cls.yonetmen.groups.add(Group.objects.get(name="Yayın Yönetmeni"))
        simdi = timezone.now()
        cls.haberler = [Haber.objects.create(
            id=870000 + i, slug=f"hiz-{i}", baslik=f"Nilüfer Çayı raporu {i}",
            kategori=cls.kategori, durum=Haber.DURUM_AKTIF, yayin_zamani=simdi)
            for i in range(25)]
        cls.ana = cls.haberler[0]

    def _gir(self):
        self.client.force_login(self.yonetmen)

    # --- widget yalnız seçilileri basıyor ---

    def test_bos_formda_hic_option_basilmiyor(self):
        """Asıl kazanç burada: 356.839 yerine 0 seçenek."""
        form = HaberForm()
        html = str(form["ilgili_haberler"])
        self.assertEqual(html.count("<option"), 0)

    def test_bagli_haberler_gorunmeye_devam_ediyor(self):
        self.ana.ilgili_haberler.add(self.haberler[1], self.haberler[2])
        form = HaberForm(instance=self.ana)
        html = str(form["ilgili_haberler"])
        self.assertEqual(html.count("<option"), 2)
        self.assertIn(str(self.haberler[1].pk), html)
        self.assertIn("Nilüfer Çayı raporu 1", html)

    def test_widget_dogru_sinif(self):
        self.assertIsInstance(HaberForm().fields["ilgili_haberler"].widget,
                              SecilenlerWidget)

    def test_sayfa_boyutu_kucuk(self):
        """25 haber varken bile form sayfası küçük kalmalı."""
        self._gir()
        yanit = self.client.get("/panel/haber/ekle")
        self.assertEqual(yanit.status_code, 200)
        self.assertLess(len(yanit.content), 200_000)
        self.assertEqual(yanit.content.count(b'name="ilgili_haberler"'), 1)

    # --- doğrulama tüm haberleri kabul ediyor ---

    def test_secilmemis_haber_de_kaydedilebiliyor(self):
        """Widget onu basmıyor ama alan kabul etmeli — betik ekliyor."""
        self._gir()
        hedef = self.haberler[5]
        yanit = self.client.post(f"/panel/haber/{self.ana.pk}", {
            "baslik": self.ana.baslik, "spot": "Spot.",
            "govde": "<p>Bir.</p><p>İki.</p>", "kategori": self.kategori.pk,
            "etiketler": "", "durum": Haber.DURUM_PASIF, "hazirlik": "taslak",
            "kaynak_turu": Haber.KAYNAK_AJANS,
            "ilgili_haberler": [hedef.pk],
        })
        self.assertEqual(yanit.status_code, 302)
        self.assertIn(hedef, self.ana.ilgili_haberler.all())

    def test_gecersiz_kimlik_reddediliyor(self):
        self._gir()
        yanit = self.client.post(f"/panel/haber/{self.ana.pk}", {
            "baslik": self.ana.baslik, "spot": "", "govde": "",
            "kategori": self.kategori.pk, "etiketler": "",
            "durum": Haber.DURUM_PASIF, "hazirlik": "taslak",
            "kaynak_turu": Haber.KAYNAK_AJANS,
            "ilgili_haberler": [99999999],
        })
        self.assertEqual(yanit.status_code, 200)
        self.assertTrue(yanit.context["form"].errors)

    def test_betiksiz_kaydetme_calisiyor(self):
        """JS kapalıyken: ilgili haber eklenemez ama HABER KAYDEDİLEBİLİR."""
        self.ana.ilgili_haberler.add(self.haberler[1])
        self._gir()
        yanit = self.client.post(f"/panel/haber/{self.ana.pk}", {
            "baslik": "Betiksiz kayıt", "spot": "", "govde": "",
            "kategori": self.kategori.pk, "etiketler": "",
            "durum": Haber.DURUM_PASIF, "hazirlik": "taslak",
            "kaynak_turu": Haber.KAYNAK_AJANS,
            "ilgili_haberler": [self.haberler[1].pk],
        })
        self.assertEqual(yanit.status_code, 302)
        self.ana.refresh_from_db()
        self.assertEqual(self.ana.baslik, "Betiksiz kayıt")
        self.assertEqual(self.ana.ilgili_haberler.count(), 1)

    def test_baglanti_kaldirilabiliyor(self):
        self.ana.ilgili_haberler.add(self.haberler[1])
        self._gir()
        self.client.post(f"/panel/haber/{self.ana.pk}", {
            "baslik": self.ana.baslik, "spot": "", "govde": "",
            "kategori": self.kategori.pk, "etiketler": "",
            "durum": Haber.DURUM_PASIF, "hazirlik": "taslak",
            "kaynak_turu": Haber.KAYNAK_AJANS, "ilgili_haberler": [],
        })
        self.assertEqual(self.ana.ilgili_haberler.count(), 0)


class HaberAramaUcu(TestCase):
    """`/panel/haber-ara` — ilgili haber seçicisinin kaynağı."""

    @classmethod
    def setUpTestData(cls):
        call_command("taksonomi_kur", verbosity=0)
        call_command("roller_kur", verbosity=0)
        cls.kategori = KategoriTur.objects.get(
            tur=Kategori.TUR_HABER, slug="gundem").kategori
        cls.kullanicilar = {}
        for sira, rol in enumerate(("Muhabir", "Editör", "Sayfa Sekreteri",
                                    "İlan Sorumlusu", "Yayın Yönetmeni")):
            k = User.objects.create_user(f"a{sira}", password=PAROLA)
            k.groups.add(Group.objects.get(name=rol))
            cls.kullanicilar[rol] = k
        simdi = timezone.now()
        for i in range(5):
            Haber.objects.create(
                id=860000 + i, slug=f"ara-{i}", baslik=f"Nilüfer Çayı {i}",
                kategori=cls.kategori, durum=Haber.DURUM_AKTIF,
                yayin_zamani=simdi)
        cls.silinmis = Haber.objects.create(
            id=860099, slug="ara-silinmis", baslik="Nilüfer silinmiş",
            kategori=cls.kategori, durum=Haber.DURUM_SILINMIS)

    def _json(self, **parametre):
        return self.client.get("/panel/haber-ara", parametre).json()

    def test_oturumsuz_kapali(self):
        yanit = self.client.get("/panel/haber-ara", {"q": "Nilüfer"})
        self.assertEqual(yanit.status_code, 302)
        self.assertIn("/panel/giris", yanit["Location"])

    def test_yetkiye_bagli(self):
        beklenen = {"Muhabir": 200, "Editör": 200, "Sayfa Sekreteri": 200,
                    "İlan Sorumlusu": 403, "Yayın Yönetmeni": 200}
        for rol, kod in beklenen.items():
            with self.subTest(rol=rol):
                self.client.force_login(self.kullanicilar[rol])
                self.assertEqual(
                    self.client.get("/panel/haber-ara", {"q": "Nilüfer"})
                    .status_code, kod)

    def test_sonuc_donuyor(self):
        self.client.force_login(self.kullanicilar["Editör"])
        veri = self._json(q="Nilüfer")
        self.assertEqual(len(veri["sonuclar"]), 5)
        self.assertIn("Nilüfer", veri["sonuclar"][0]["etiket"])
        self.assertEqual(veri["uyari"], "")

    def test_silinmis_kayit_gelmiyor(self):
        self.client.force_login(self.kullanicilar["Editör"])
        kimlikler = [s["id"] for s in self._json(q="Nilüfer")["sonuclar"]]
        self.assertNotIn(self.silinmis.pk, kimlikler)

    def test_haric_tutulan_kayit_gelmiyor(self):
        """Haber kendini ilgili haber olarak gösteremez."""
        self.client.force_login(self.kullanicilar["Editör"])
        kimlikler = [s["id"] for s in
                     self._json(q="Nilüfer", haric=860000)["sonuclar"]]
        self.assertNotIn(860000, kimlikler)

    def test_kisa_sorgu_reddediliyor(self):
        self.client.force_login(self.kullanicilar["Editör"])
        veri = self._json(q="ni")
        self.assertEqual(veri["sonuclar"], [])
        self.assertIn("3 harf", veri["uyari"])

    def test_durak_kelime_reddediliyor(self):
        """`arama_metni.sorgu_coz` kapısı — ikinci arama mantığı yazılmadı."""
        self.client.force_login(self.kullanicilar["Editör"])
        veri = self._json(q="ve")
        self.assertEqual(veri["sonuclar"], [])
        self.assertTrue(veri["uyari"])

    def test_ust_sinir_uygulaniyor(self):
        for i in range(20):
            Haber.objects.create(
                id=861000 + i, slug=f"cok-{i}", baslik=f"Nilüfer ek {i}",
                kategori=self.kategori, durum=Haber.DURUM_AKTIF)
        self.client.force_login(self.kullanicilar["Editör"])
        from .panel import HABER_ARA_EN_COK
        self.assertEqual(len(self._json(q="Nilüfer")["sonuclar"]),
                         HABER_ARA_EN_COK)


class BugunUcuzKapi(TestCase):
    """Kuyruk boşken liste sorguları hiç çalışmamalı."""

    @classmethod
    def setUpTestData(cls):
        call_command("taksonomi_kur", verbosity=0)
        call_command("roller_kur", verbosity=0)
        cls.kategori = KategoriTur.objects.get(
            tur=Kategori.TUR_HABER, slug="gundem").kategori
        cls.editor = User.objects.create_user("be", password=PAROLA)
        cls.editor.groups.add(Group.objects.get(name="Editör"))

    def test_kuyruk_bosken_liste_sorgusu_calismiyor(self):
        """Sorgu SAYISI değil, PAHALI sorgunun varlığı ölçülüyor.

        `assertNumQueries` burada kırılgan: Django'nun izin ve içerik türü
        sorguları test sırasına göre önbelleklenip sayıyı oynatıyor
        (ölçüldü: aynı test tek başına 12, modülle 10). Onun yerine
        kuyruk listesini çeken sorgunun **hiç kurulmadığı** doğrulanıyor.
        """
        from django.test.utils import CaptureQueriesContext
        from django.db import connection
        self.client.force_login(self.editor)
        with CaptureQueriesContext(connection) as yakala:
            yanit = self.client.get("/panel/")
        liste_sorgulari = [q["sql"] for q in yakala.captured_queries
                           if "LIMIT 20" in q["sql"] and "icerik_haber" in q["sql"]]
        self.assertEqual(liste_sorgulari, [],
                         "Kuyruk boşken liste sorgusu çalışmamalı")
        self.assertEqual(yanit.context["kuyruk_sayisi"], 0)
        self.assertEqual(list(yanit.context["taslaklar"]), [])
        self.assertEqual(yanit.context["benim_taslaklarim"], 0)

    def test_kuyruk_doluyken_liste_geliyor(self):
        Haber.objects.create(id=850001, slug="k1", baslik="Taslak bir",
                             kategori=self.kategori, durum=Haber.DURUM_PASIF,
                             hazirlik="taslak", olusturan=self.editor)
        Haber.objects.create(id=850002, slug="k2", baslik="İncelemede bir",
                             kategori=self.kategori, durum=Haber.DURUM_PASIF,
                             hazirlik="incelemede")
        self.client.force_login(self.editor)
        yanit = self.client.get("/panel/")
        self.assertEqual(yanit.context["kuyruk_sayisi"], 2)
        self.assertEqual(len(yanit.context["taslaklar"]), 1)
        self.assertEqual(len(yanit.context["incelemedekiler"]), 1)
        self.assertEqual(yanit.context["benim_taslaklarim"], 1)


class MansetTekTarama(TestCase):
    """Altı tam tarama yerine bir küme çekimi."""

    @classmethod
    def setUpTestData(cls):
        call_command("taksonomi_kur", verbosity=0)
        call_command("roller_kur", verbosity=0)
        cls.kategori = KategoriTur.objects.get(
            tur=Kategori.TUR_HABER, slug="gundem").kategori
        cls.sekreter = User.objects.create_user("ms", password=PAROLA)
        cls.sekreter.groups.add(Group.objects.get(name="Sayfa Sekreteri"))
        simdi = timezone.now()
        Haber.objects.create(id=840001, slug="m1", baslik="Ana manşet",
                             kategori=cls.kategori, durum=Haber.DURUM_AKTIF,
                             yayin_zamani=simdi, manset_ana=True)
        Haber.objects.create(id=840002, slug="m2", baslik="Kare manşet",
                             kategori=cls.kategori, durum=Haber.DURUM_AKTIF,
                             yayin_zamani=simdi, manset_kare=True)
        Haber.objects.create(id=840003, slug="m3", baslik="Pasif manşet",
                             kategori=cls.kategori, durum=Haber.DURUM_PASIF,
                             manset_tepe=True)

    def test_doluluk_ve_uyari_dogru(self):
        self.client.force_login(self.sekreter)
        yanit = self.client.get("/panel/mansetler")
        ust = yanit.context["ust_bilgi"]
        self.assertIn("Ana manşet: 1", ust)
        self.assertIn("Tepe manşet: 1", ust)
        self.assertIn("Kare manşet: 1", ust)
        self.assertIn("1 manşet kaydı yayında değil", yanit.context["uyari"])
        self.assertEqual(yanit.context["sayfa"].paginator.count, 3)

    def test_manset_taramasi_azaldi(self):
        """Manşet koşullu sorgu sayısı ölçülüyor.

        ÖNCE altı taneydi: sayfalayıcı sayımı + üç slot sayımı + yayından
        düşmüş sayımı + sayfa dilimi. Her biri 356.839 satırı tam tarıyordu
        (~800 ms). Slot sayımları tek küme çekimine indirildi.
        """
        from django.test.utils import CaptureQueriesContext
        from django.db import connection
        self.client.force_login(self.sekreter)
        with CaptureQueriesContext(connection) as yakala:
            self.client.get("/panel/mansetler")
        manset = [q["sql"] for q in yakala.captured_queries
                  if "manset_ana" in q["sql"]]
        self.assertLessEqual(len(manset), 3,
                             f"Manşet taraması {len(manset)} sorguya çıktı; "
                             "en çok 3 olmalı (küme + sayım + dilim)")


class BagliGaleriSecicisi(TestCase):
    """§4 alan 27 — aynı desen, 4.040 galeride `<option>` tuzağı tekrarlanmasın."""

    @classmethod
    def setUpTestData(cls):
        call_command("taksonomi_kur", verbosity=0)
        call_command("roller_kur", verbosity=0)
        cls.kategori = KategoriTur.objects.get(
            tur=Kategori.TUR_HABER, slug="gundem").kategori
        cls.yonetmen = User.objects.create_user("gy", password=PAROLA)
        cls.yonetmen.groups.add(Group.objects.get(name="Yayın Yönetmeni"))
        cls.haber = Haber.objects.create(
            id=830001, slug="gal", baslik="Galeri bağlı haber",
            kategori=cls.kategori, durum=Haber.DURUM_AKTIF,
            yayin_zamani=timezone.now())
        from medya.models import FotoGaleri
        foto = KategoriTur.objects.filter(tur=Kategori.TUR_FOTO).first()
        cls.galeriler = [FotoGaleri.objects.create(
            id=831000 + i, slug=f"g-{i}", baslik=f"Nilüfer galerisi {i}",
            kategori=foto.kategori, kategori_dilimi=foto.adres_dilimi,
            yayin_zamani=timezone.now()) for i in range(6)]

    def test_bos_formda_hic_option_basilmiyor(self):
        html = str(HaberForm()["bagli_galeriler"])
        self.assertEqual(html.count("<option"), 0)

    def test_bagli_galeriler_gorunuyor(self):
        self.haber.bagli_galeriler.add(self.galeriler[0], self.galeriler[1])
        html = str(HaberForm(instance=self.haber)["bagli_galeriler"])
        self.assertEqual(html.count("<option"), 2)
        self.assertIn("Nilüfer galerisi 0", html)

    def test_ayni_widget_kullaniliyor(self):
        """İkinci bir çözüm yazılmadı."""
        f = HaberForm()
        self.assertIsInstance(f.fields["bagli_galeriler"].widget, SecilenlerWidget)
        self.assertIsInstance(f.fields["ilgili_haberler"].widget, SecilenlerWidget)

    def test_galeri_baglanabiliyor(self):
        self.client.force_login(self.yonetmen)
        yanit = self.client.post(f"/panel/haber/{self.haber.pk}", {
            "baslik": self.haber.baslik, "spot": "", "govde": "",
            "kategori": self.kategori.pk, "etiketler": "",
            "durum": Haber.DURUM_PASIF, "hazirlik": "taslak",
            "kaynak_turu": Haber.KAYNAK_AJANS,
            "bagli_galeriler": [self.galeriler[2].pk],
        })
        self.assertEqual(yanit.status_code, 302)
        self.assertIn(self.galeriler[2], self.haber.bagli_galeriler.all())

    def test_galeri_arama_ucu(self):
        self.client.force_login(self.yonetmen)
        veri = self.client.get("/panel/galeri-ara", {"q": "Nilüfer"}).json()
        self.assertEqual(len(veri["sonuclar"]), 6)
        self.assertIn("Nilüfer", veri["sonuclar"][0]["etiket"])

    def test_galeri_arama_yetkiye_bagli(self):
        ilan = User.objects.create_user("gi", password=PAROLA)
        ilan.groups.add(Group.objects.get(name="İlan Sorumlusu"))
        self.client.force_login(ilan)
        self.assertEqual(
            self.client.get("/panel/galeri-ara", {"q": "Nilüfer"}).status_code, 403)


class FormKolayliklari(TestCase):
    """§4 alan 3 ve §21 odak yönetimi."""

    @classmethod
    def setUpTestData(cls):
        call_command("taksonomi_kur", verbosity=0)
        call_command("roller_kur", verbosity=0)
        cls.kategori = KategoriTur.objects.get(
            tur=Kategori.TUR_HABER, slug="gundem").kategori
        cls.yonetmen = User.objects.create_user("fk", password=PAROLA)
        cls.yonetmen.groups.add(Group.objects.get(name="Yayın Yönetmeni"))

    def test_ikinci_baslik_varsayilan_kapali(self):
        """§4 alan 3: 'varsayılan kapalı, açılır'."""
        self.client.force_login(self.yonetmen)
        icerik = self.client.get("/panel/haber/ekle").content.decode()
        self.assertIn("<details class=\"acilir-alan\"", icerik)
        self.assertNotIn("<details class=\"acilir-alan\" open>", icerik)

    def test_dolu_ikinci_baslik_acik_geliyor(self):
        haber = Haber.objects.create(
            id=820900, slug="ib", baslik="İkinci başlıklı",
            ikinci_baslik="Var olan ikinci başlık", kategori=self.kategori,
            durum=Haber.DURUM_AKTIF, yayin_zamani=timezone.now())
        self.client.force_login(self.yonetmen)
        icerik = self.client.get(f"/panel/haber/{haber.pk}").content.decode()
        self.assertIn("acilir-alan\" open", icerik)

    def test_adres_onizleme_kutusu_var(self):
        self.client.force_login(self.yonetmen)
        icerik = self.client.get("/panel/haber/ekle").content.decode()
        self.assertIn("data-adres-onizleme", icerik)
        self.assertIn("{kategori-slug}", icerik)

    def test_sayac_isaretleri_yerinde(self):
        """Sayaçları betik çiziyor; işaretler sunucudan gelmeli."""
        self.client.force_login(self.yonetmen)
        icerik = self.client.get("/panel/haber/ekle").content.decode()
        self.assertIn('data-sayac="60"', icerik)
        self.assertIn('data-sayac="160"', icerik)

    def test_hatali_alan_isaretleniyor(self):
        """Odak yönetimi betikte; sunucu `.hatali` sınıfını basmalı."""
        self.client.force_login(self.yonetmen)
        yanit = self.client.post("/panel/haber/ekle", {
            "baslik": "", "spot": "", "govde": "", "kategori": "",
            "etiketler": "", "durum": Haber.DURUM_PASIF, "hazirlik": "taslak",
            "kaynak_turu": Haber.KAYNAK_AJANS,
        })
        self.assertEqual(yanit.status_code, 200)
        self.assertIn('class="alan hatali"', yanit.content.decode())

    def test_turkce_etiketler(self):
        """Ekranda 'Gorsel url', 'Gomulu kod' yazıyordu."""
        etiketler = {a: str(x.label) for a, x in HaberForm().fields.items()}
        for alan, beklenen in (("gorsel_url", "Görsel adresi (URL)"),
                               ("gomulu_kod", "Gömülü kod"),
                               ("seo_baslik", "SEO başlığı"),
                               ("ilgili_haberler", "İlgili haberler")):
            self.assertEqual(etiketler[alan], beklenen)
