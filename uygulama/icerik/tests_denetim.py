"""Denetim kaydı — `icerik/denetim_kaydi.py` (Paket F madde 9).

`LogKaydi` 28 Ağustos'tan beri vardı ama yazan kod yoktu; Log ekranı hep
boştu. Bu testler her olayın GERÇEK panel akışıyla (test istemcisi, gerçek
kayıt) günlüğe düştüğünü ve Log ekranında göründüğünü ölçer.
"""

from django.contrib.auth.models import Group, User
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone

from taksonomi.models import Etiket, Kategori, KategoriTur, Kaynak

from .denetim_kaydi import ip_maskele
from .models import Haber, Konu, LogKaydi, SonDakika

PAROLA = "Uzun-ve-guclu-parola-2026"


class DenetimTemel(TestCase):

    @classmethod
    def setUpTestData(cls):
        call_command("taksonomi_kur", verbosity=0)
        call_command("roller_kur", verbosity=0)
        cls.gundem = KategoriTur.objects.get(tur=Kategori.TUR_HABER, slug="gundem").kategori
        cls.spor = KategoriTur.objects.get(tur=Kategori.TUR_HABER, slug="spor").kategori
        cls.etiket = Etiket.objects.create(ad="Denetim", slug="denetim")
        cls.kaynak = Kaynak.objects.create(ad="Denetim Ajansı", tur=Kaynak.TUR_AJANS)
        cls.k = {}
        for sira, rol in enumerate(("Muhabir", "Editör", "Sayfa Sekreteri",
                                    "Yayın Yönetmeni")):
            u = User.objects.create_user(f"d{sira}", password=PAROLA,
                                         first_name="D", last_name=str(sira))
            u.groups.add(Group.objects.get(name=rol))
            cls.k[rol] = u

    def gir(self, rol):
        self.client.force_login(self.k[rol])

    def veri(self, **ek):
        v = {"baslik": "Denetlenen haber", "spot": "Spot.",
             "govde": "<p>Bir.</p><p>İki.</p>", "kategori": self.gundem.pk,
             "etiketler": self.etiket.ad, "kaynak_turu": Haber.KAYNAK_AJANS,
             "kaynaklar": [self.kaynak.pk], "durum": Haber.DURUM_PASIF,
             "hazirlik": "taslak",
             "yayin_zamani": timezone.now().strftime("%Y-%m-%d %H:%M:%S")}
        v.update(ek)
        return v

    def fiiller(self, **suz):
        return list(LogKaydi.objects.filter(**suz).order_by("pk")
                    .values_list("fiil", flat=True))


class OturumOlaylari(DenetimTemel):

    def test_giris_basarisiz_giris_ve_cikis(self):
        self.client.post("/panel/giris", {"username": "d1", "password": "yanlis"})
        self.client.post("/panel/giris", {"username": "olmayan-hesap", "password": "x"})
        self.client.post("/panel/giris", {"username": "d1", "password": PAROLA})
        self.client.post("/panel/cikis")
        self.assertEqual(self.fiiller(), ["giris_basarisiz", "giris_basarisiz",
                                          "giris", "cikis"])
        yanlis, olmayan, giris, _ = LogKaydi.objects.order_by("pk")
        self.assertEqual(yanlis.kullanici, self.k["Editör"])
        self.assertIsNone(olmayan.kullanici)
        self.assertIn("olmayan-hesap", olmayan.gerekce)
        self.assertEqual(giris.kullanici, self.k["Editör"])

    def test_ip_varsayilan_maskeli(self):
        self.client.post("/panel/giris", {"username": "d1", "password": PAROLA},
                         REMOTE_ADDR="203.0.113.57")
        self.assertEqual(LogKaydi.objects.get(fiil="giris").ip, "203.0.113.0")

    @override_settings(BH_LOG_IP="yok")
    def test_ip_yazmama_kipi(self):
        self.client.post("/panel/giris", {"username": "d1", "password": PAROLA},
                         REMOTE_ADDR="203.0.113.57", HTTP_USER_AGENT="Tarayici/1")
        kayit = LogKaydi.objects.get(fiil="giris")
        self.assertIsNone(kayit.ip)
        self.assertEqual(kayit.tarayici, "")

    @override_settings(BH_LOG_IP="tam")
    def test_ip_tam_kipi(self):
        self.client.post("/panel/giris", {"username": "d1", "password": PAROLA},
                         REMOTE_ADDR="203.0.113.57")
        self.assertEqual(LogKaydi.objects.get(fiil="giris").ip, "203.0.113.57")

    def test_ipv6_maskesi(self):
        self.assertEqual(ip_maskele("2001:db8:abcd:12::1"), "2001:db8:abcd::")
        self.assertIsNone(ip_maskele("bozuk"))


class HaberOlaylari(DenetimTemel):

    def test_olusturma_ve_yayina_alma(self):
        self.gir("Editör")
        self.client.post("/panel/haber/ekle", self.veri(durum=Haber.DURUM_AKTIF,
                                                        hazirlik="hazir"))
        haber = Haber.objects.get(baslik="Denetlenen haber")
        kayitlar = LogKaydi.objects.filter(hedef_tur="haber", hedef_id=haber.pk)
        self.assertEqual(sorted(kayitlar.values_list("fiil", flat=True)),
                         ["haber_olusturma", "yayina_alma"])
        self.assertTrue(all(k.kullanici == self.k["Editör"] for k in kayitlar))

    def test_duzenlemede_durum_kategori_ve_manset(self):
        haber = Haber.objects.create(id=5_600_001, slug="d", baslik="Denetlenen haber",
                                     kategori=self.gundem, durum=Haber.DURUM_PASIF,
                                     olusturan=self.k["Muhabir"])
        self.gir("Sayfa Sekreteri")
        self.client.post(f"/panel/haber/{haber.pk}", self.veri(
            durum=Haber.DURUM_AKTIF, hazirlik="hazir", kategori=self.spor.pk,
            manset_ana="on"))
        self.assertEqual(sorted(self.fiiller(hedef_id=haber.pk)),
                         ["kategori_degistirme", "mansete_alma", "yayina_alma"])
        self.client.post(f"/panel/haber/{haber.pk}", self.veri(
            durum=Haber.DURUM_PASIF, kategori=self.spor.pk))
        son = self.fiiller(hedef_id=haber.pk)[-2:]
        self.assertEqual(sorted(son), ["mansetten_cikarma", "yayindan_cekme"])
        cekme = LogKaydi.objects.get(fiil="yayindan_cekme")
        self.assertEqual((cekme.oncesi, cekme.sonrasi), ({"durum": 1}, {"durum": 2}))

    def test_degisiklik_yoksa_yayin_kaydi_yazilmaz(self):
        haber = Haber.objects.create(id=5_600_002, slug="d2", baslik="Denetlenen haber",
                                     kategori=self.gundem, durum=Haber.DURUM_PASIF)
        self.gir("Editör")
        self.client.post(f"/panel/haber/{haber.pk}", self.veri())
        self.assertEqual(self.fiiller(hedef_id=haber.pk), [])


class TopluOlaylar(DenetimTemel):

    def _haber(self, kimlik, **ek):
        alan = dict(id=kimlik, slug=f"t{kimlik}", baslik=f"T {kimlik}", kategori=self.gundem,
                    spot="Spot", govde="<p>Bir.</p><p>İki.</p>",
                    kaynak_turu=Haber.KAYNAK_MUHABIR, muhabir="A", durum=Haber.DURUM_PASIF)
        alan.update(ek)
        h = Haber.objects.create(**alan)
        h.etiketler.add(self.etiket)
        return h

    def test_toplu_yayina_al_yalniz_degisenleri_yazar(self):
        iyi, eksik = self._haber(5_700_001), self._haber(5_700_002, spot="")
        self.gir("Editör")
        self.client.post("/panel/toplu", {"fiil": "yayina_al",
                                          "kimlikler": [iyi.pk, eksik.pk]})
        kayitlar = LogKaydi.objects.filter(fiil="yayina_alma")
        self.assertEqual(list(kayitlar.values_list("hedef_id", flat=True)), [iyi.pk])
        self.assertTrue(kayitlar[0].toplu_islem_kimligi)
        self.assertIn("ATLANDI", kayitlar[0].gerekce)

    def test_toplu_hazirlik_her_kayda_ayni_toplu_kimlikle(self):
        h1, h2 = self._haber(5_700_003), self._haber(5_700_004)
        self.gir("Muhabir")
        self.client.post("/panel/toplu", {"fiil": "hazirlik", "hazirlik_degeri": "incelemede",
                                          "kimlikler": [h1.pk, h2.pk]})
        kayitlar = list(LogKaydi.objects.filter(fiil="toplu_islem"))
        self.assertEqual(sorted(k.hedef_id for k in kayitlar), [h1.pk, h2.pk])
        self.assertEqual(len({k.toplu_islem_kimligi for k in kayitlar}), 1)
        self.assertEqual(kayitlar[0].sonrasi, {"fiil": "hazirlik",
                                               "hazirlik_degeri": "incelemede"})
        self.assertEqual(kayitlar[0].etkilenen_sayisi, 2)


class DigerOlaylar(DenetimTemel):

    def test_son_dakika_degisikligi(self):
        kayit = SonDakika.objects.create(baslik="Eski bant", adres="/gundem")
        self.gir("Sayfa Sekreteri")
        self.client.post(f"/panel/son-dakika/{kayit.pk}", {
            "baslik": "Yeni bant", "adres": "/gundem", "haber": "",
            "baslangic": timezone.now().strftime("%Y-%m-%d %H:%M:%S"),
            "sira": 0, "aktif": "on"})
        log = LogKaydi.objects.get(fiil="son_dakika_degisikligi")
        self.assertEqual(log.oncesi["baslik"], "Eski bant")
        self.assertEqual(log.sonrasi["baslik"], "Yeni bant")

    def test_konu_onay_ve_ret(self):
        konu = Konu.objects.create(ad="Dosya", slug="dosya",
                                   baslangic=timezone.localdate(),
                                   bitis=timezone.localdate())
        self.gir("Editör")
        self.client.post(f"/panel/konu/{konu.pk}/karar", {"karar": Konu.ONAY_ONAYLI})
        self.client.post(f"/panel/konu/{konu.pk}/karar", {"karar": Konu.ONAY_RET})
        kayitlar = LogKaydi.objects.filter(fiil="konu_karari").order_by("pk")
        self.assertEqual([k.sonrasi["onay"] for k in kayitlar],
                         [Konu.ONAY_ONAYLI, Konu.ONAY_RET])

    def test_rol_degisikligi(self):
        hedef = self.k["Muhabir"]
        self.gir("Yayın Yönetmeni")
        self.client.post(f"/panel/kullanici/{hedef.pk}", {
            "username": hedef.username, "first_name": "D", "last_name": "0",
            "email": "", "is_active": "on",
            "roller": [Group.objects.get(name="Editör").pk]})
        log = LogKaydi.objects.get(fiil="kullanici_degisikligi")
        self.assertEqual(log.oncesi["roller"], ["Muhabir"])
        self.assertEqual(log.sonrasi["roller"], ["Editör"])
        self.assertEqual(log.kullanici, self.k["Yayın Yönetmeni"])

    def test_parola_degisikligi_parolayi_yazmaz(self):
        self.gir("Editör")
        yeni = "Bir-baska-guclu-parola-77"
        self.client.post("/panel/sifre", {"old_password": PAROLA,
                                          "new_password1": yeni, "new_password2": yeni})
        log = LogKaydi.objects.get(fiil="parola_degisikligi")
        self.assertNotIn(yeni, str(log.oncesi) + str(log.sonrasi) + log.gerekce)

    def test_log_ekrani_kayitlari_gosterir(self):
        self.client.post("/panel/giris", {"username": "olmayan", "password": "x"})
        self.gir("Yayın Yönetmeni")
        yanit = self.client.get("/panel/log")
        self.assertEqual(yanit.status_code, 200)
        self.assertContains(yanit, "Başarısız oturum denemesi")
        self.assertContains(yanit, "olmayan")
        kayit = LogKaydi.objects.filter(kullanici__isnull=True).first()
        self.assertEqual(self.client.get(f"/panel/log/{kayit.pk}").status_code, 200)
