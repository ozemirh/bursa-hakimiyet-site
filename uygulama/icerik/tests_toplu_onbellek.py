"""Toplu fiil → sayfa mikro önbelleği ve güvenilir IP (Paket F, ana dalla birleşme).

1. Panelin toplu fiilleri `QuerySet.update()` kullanır; kayıt sinyali gitmez.
   Yayına alınan / çekilen haber okurun önbellekli sayfasına ANINDA
   yansımalı (`onbellek.surumu_artir`).
2. Giriş sınırı ve denetim kaydı IP'yi okunma sayacının güvenilir vekil
   kuralıyla alır: güvenilmeyen istemcinin `X-Forwarded-For`u yok sayılır.
"""

from django.contrib.auth.models import Group, User
from django.core.cache import cache
from django.core.management import call_command
from django.test import Client, TestCase, override_settings
from django.utils import timezone

from taksonomi.models import Etiket, Kategori, KategoriTur

from .models import Haber, LogKaydi
from .tests_basarim import SAYFA_ACIK

PAROLA = "Uzun-ve-guclu-parola-2026"


@SAYFA_ACIK
class TopluFiilSayfaOnbellegi(TestCase):

    @classmethod
    def setUpTestData(cls):
        call_command("taksonomi_kur", verbosity=0)
        call_command("roller_kur", verbosity=0)
        cls.kategori = KategoriTur.objects.get(tur=Kategori.TUR_HABER, slug="gundem").kategori
        cls.etiket = Etiket.objects.create(ad="Önbellek", slug="onbellek")
        cls.editor = User.objects.create_user("o-editor")
        cls.editor.groups.add(Group.objects.get(name="Editör"))

    def setUp(self):
        self.okur = Client()
        self.masa = Client()
        self.masa.force_login(self.editor)

    def _haber(self, kimlik, baslik, durum):
        h = Haber.objects.create(
            id=kimlik, slug=f"o-{kimlik}", baslik=baslik, kategori=self.kategori,
            spot="Spot", govde="<p>Bir.</p><p>İki.</p>", durum=durum,
            kaynak_turu=Haber.KAYNAK_MUHABIR, muhabir="A",
            yayin_zamani=timezone.now())
        h.etiketler.add(self.etiket)
        return h

    def test_toplu_yayina_al_ve_cek_aninda_yansir(self):
        h = self._haber(5_800_001, "Toplu yayına alınan haber", Haber.DURUM_PASIF)
        ilk = self.okur.get("/")
        self.assertEqual(ilk["X-Onbellek"], "kayit")
        self.assertNotContains(ilk, "Toplu yayına alınan haber")
        self.assertEqual(self.okur.get("/")["X-Onbellek"], "isabet")

        self.masa.post("/panel/toplu", {"fiil": "yayina_al", "kimlikler": [h.pk]})
        yanit = self.okur.get("/")
        self.assertEqual(yanit["X-Onbellek"], "kayit")
        self.assertContains(yanit, "Toplu yayına alınan haber")

        self.masa.post("/panel/toplu", {"fiil": "yayindan_cek", "kimlikler": [h.pk]})
        yanit = self.okur.get("/")
        self.assertEqual(yanit["X-Onbellek"], "kayit")
        self.assertNotContains(yanit, "Toplu yayına alınan haber")

    def test_haber_detay_da_tazelenir(self):
        h = self._haber(5_800_002, "Detayı önbellekte duran haber", Haber.DURUM_AKTIF)
        adres = h.get_absolute_url()
        self.assertEqual(self.okur.get(adres).status_code, 200)
        self.assertEqual(self.okur.get(adres)["X-Onbellek"], "isabet")
        self.masa.post("/panel/toplu", {"fiil": "yayindan_cek", "kimlikler": [h.pk]})
        self.assertEqual(self.okur.get(adres).status_code, 404)


class GuvenilirIp(TestCase):

    @classmethod
    def setUpTestData(cls):
        call_command("roller_kur", verbosity=0)
        User.objects.create_user("ip-editor", password=PAROLA)

    def setUp(self):
        cache.clear()

    def _dene(self, xff, parola="yanlis", uzak="198.51.100.7"):
        return self.client.post("/panel/giris", {"username": "ip-editor", "password": parola},
                                REMOTE_ADDR=uzak, HTTP_X_FORWARDED_FOR=xff)

    def test_guvenilmeyen_xff_kilidi_atlatamaz(self):
        """Vekil listesi boş: başlığa her seferinde başka adres yazmak işe yaramaz."""
        for sira in range(5):
            self._dene(f"203.0.113.{sira}")
        self.assertContains(self._dene("203.0.113.99", parola=PAROLA),
                            "Çok sayıda başarısız giriş denemesi")
        self.assertEqual(LogKaydi.objects.filter(fiil="giris_basarisiz")
                         .values_list("ip", flat=True).distinct().count(), 1)

    @override_settings(GUVENILIR_VEKILLER=["127.0.0.1"])
    def test_guvenilir_vekil_arkasinda_istemci_adresi_kullanilir(self):
        self._dene("203.0.113.57", uzak="127.0.0.1")
        kayit = LogKaydi.objects.get(fiil="giris_basarisiz")
        self.assertEqual(kayit.ip, "203.0.113.0")       # maskeli istemci adresi
