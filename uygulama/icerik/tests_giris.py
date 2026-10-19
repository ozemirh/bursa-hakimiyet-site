"""Giriş güvenliği — `icerik/giris_guvenligi.py` (Paket F madde 8).

Başarısız deneme sınırı, kilit, oturumun mutlak/boşta süresi ve kurulum
uyarısı. Testler gerçek giriş formunu (`/panel/giris`) kullanır.
"""

import io
import time

from django.contrib.auth.models import Group, User
from django.core.cache import cache
from django.core.management import call_command
from django.test import TestCase, override_settings

from . import giris_guvenligi
from .models import LogKaydi

PAROLA = "Uzun-ve-guclu-parola-2026"


class GirisTemel(TestCase):

    @classmethod
    def setUpTestData(cls):
        call_command("roller_kur", verbosity=0)
        cls.editor = User.objects.create_user("g-editor", password=PAROLA)
        cls.editor.groups.add(Group.objects.get(name="Editör"))
        cls.diger = User.objects.create_user("g-diger", password=PAROLA)

    def setUp(self):
        cache.clear()

    def tearDown(self):
        cache.clear()

    def dene(self, ad="g-editor", parola="yanlis", ip="198.51.100.7"):
        return self.client.post("/panel/giris", {"username": ad, "password": parola},
                                REMOTE_ADDR=ip)


class BasarisizDenemeSiniri(GirisTemel):

    def test_bes_hatadan_sonra_dogru_parola_da_reddedilir(self):
        for _ in range(5):
            self.assertEqual(self.dene().status_code, 200)
        yanit = self.dene(parola=PAROLA)
        self.assertEqual(yanit.status_code, 200)
        self.assertContains(yanit, "Çok sayıda başarısız giriş denemesi")
        self.assertNotIn("_auth_user_id", self.client.session)
        # Kilitliyken parola denenmez: altıncı istek başarısız giriş sinyali
        # üretmedi; kilidin başlangıcı bir kez yazıldı.
        self.assertEqual(LogKaydi.objects.filter(fiil="giris_basarisiz").count(), 5)
        self.assertEqual(LogKaydi.objects.filter(fiil="giris_kilidi").count(), 1)

    def test_kilit_mesaji_hesabin_varligini_soylemez(self):
        for _ in range(5):
            self.dene(ad="hic-olmayan")
        yanit = self.dene(ad="hic-olmayan")
        self.assertContains(yanit, "Çok sayıda başarısız giriş denemesi")

    def test_baska_adresten_ayni_hesap_kilitli_degil(self):
        for _ in range(5):
            self.dene()
        yanit = self.dene(parola=PAROLA, ip="203.0.113.9")
        self.assertEqual(yanit.status_code, 302)

    def test_ip_genelinde_parola_puskurtme_kesilir(self):
        for sira in range(20):
            self.dene(ad=f"rastgele-{sira}")
        yanit = self.dene(ad="g-diger", parola=PAROLA)
        self.assertContains(yanit, "Çok sayıda başarısız giriş denemesi")

    def test_basarili_giris_sayaci_sifirlar(self):
        for _ in range(4):
            self.dene()
        self.assertEqual(self.dene(parola=PAROLA).status_code, 302)
        self.client.logout()
        for _ in range(4):
            self.dene()
        self.assertEqual(self.dene(parola=PAROLA).status_code, 302)

    @override_settings(BH_GIRIS_KILIT_SANIYE=1)
    def test_kilit_suresi_dolunca_acilir(self):
        for _ in range(5):
            self.dene()
        self.assertContains(self.dene(parola=PAROLA), "Çok sayıda")
        time.sleep(1.2)
        self.assertEqual(self.dene(parola=PAROLA).status_code, 302)


class OturumSuresi(GirisTemel):

    def _gir(self):
        self.assertEqual(self.dene(parola=PAROLA).status_code, 302)

    def _damgala(self, **saniye_once):
        oturum = self.client.session
        simdi = int(time.time())
        for anahtar, once in saniye_once.items():
            oturum[anahtar] = simdi - once
        oturum.save()

    def test_bosta_kalan_oturum_duser(self):
        self._gir()
        self.assertEqual(self.client.get("/panel/").status_code, 200)
        self._damgala(bh_son_etkinlik=61 * 60)
        yanit = self.client.get("/panel/")
        self.assertEqual(yanit.status_code, 302)
        self.assertIn("/panel/giris", yanit["Location"])
        cikis = LogKaydi.objects.filter(fiil="cikis").latest("pk")
        self.assertIn("boşta", cikis.gerekce)

    def test_mutlak_sure_dolunca_duser(self):
        self._gir()
        self._damgala(bh_giris_zamani=8 * 3600 + 5, bh_son_etkinlik=10)
        yanit = self.client.get("/panel/")
        self.assertEqual(yanit.status_code, 302)
        self.assertIn("mutlak", LogKaydi.objects.filter(fiil="cikis").latest("pk").gerekce)

    def test_etkin_oturum_surer(self):
        self._gir()
        self._damgala(bh_son_etkinlik=30 * 60)
        self.assertEqual(self.client.get("/panel/").status_code, 200)

    @override_settings(BH_OTURUM_BOSTA_SANIYE=120)
    def test_sure_ayarla_degisir(self):
        self._gir()
        self._damgala(bh_son_etkinlik=150)
        self.assertEqual(self.client.get("/panel/").status_code, 302)

    def test_cerez_omru_mutlak_sureyi_asmaz(self):
        from django.conf import settings
        self.assertLessEqual(settings.SESSION_COOKIE_AGE, giris_guvenligi.mutlak_sure())
        self.assertIn("icerik.giris_guvenligi.OturumSuresi", settings.MIDDLEWARE)


class KurulumUyarisi(TestCase):

    def test_is_staff_ve_deneme_parolasi_uyarilir(self):
        User.objects.create_user("deneme-editor", password="deneme1234", is_staff=True)
        cikti = io.StringIO()
        call_command("roller_kur", stdout=cikti)
        metin = cikti.getvalue()
        self.assertIn("is_staff panel için gerekmez", metin)
        self.assertIn("deneme parolası taşıyan açık hesap(lar): deneme-editor", metin)
        # Komut hesabı DEĞİŞTİRMEZ.
        self.assertTrue(User.objects.get(username="deneme-editor").is_staff)
