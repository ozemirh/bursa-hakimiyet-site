"""Panel ekranları — yetkiye göre erişim ve iş akışı.

Bu dosyanın varlık sebebi: **menüde bağlantının görünmemesi yetki denetimi
değildir.** Adres elle yazılabilir. Testler her ekranı doğrudan adresten
çağırıp rolün gerçekten girip giremediğini ölçer.
"""

from django.contrib.auth.models import Group, User
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from taksonomi.models import Etiket, Kategori, KategoriTur

from .models import Haber

PAROLA = "deneme-parola-123"


class PanelErisim(TestCase):

    @classmethod
    def setUpTestData(cls):
        call_command("taksonomi_kur", verbosity=0)
        call_command("roller_kur", verbosity=0)
        cls.kategori = KategoriTur.objects.get(
            tur=Kategori.TUR_HABER, slug="gundem").kategori
        cls.etiket = Etiket.objects.create(ad="Etiket", slug="etiket")
        cls.kullanicilar = {}
        for rol in ("Muhabir", "Editör", "Sayfa Sekreteri",
                    "İlan Sorumlusu", "Yayın Yönetmeni"):
            k = User.objects.create_user(f"u{len(cls.kullanicilar)}", password=PAROLA)
            k.groups.add(Group.objects.get(name=rol))
            cls.kullanicilar[rol] = k

    def _gir(self, rol):
        self.client.force_login(self.kullanicilar[rol])

    # --- giriş zorunluluğu ---
    def test_giris_yapmadan_panel_kapali(self):
        for yol in ("/panel/", "/panel/akis", "/panel/haber/ekle", "/panel/roller"):
            with self.subTest(yol=yol):
                yanit = self.client.get(yol)
                self.assertEqual(yanit.status_code, 302)
                self.assertIn("/panel/giris", yanit["Location"])

    def test_giris_sayfasi_aciliyor(self):
        self.assertEqual(self.client.get("/panel/giris").status_code, 200)

    # --- ekranlar ---
    def test_bugun_ekrani_her_role_acik(self):
        for rol in self.kullanicilar:
            with self.subTest(rol=rol):
                self._gir(rol)
                self.assertEqual(self.client.get("/panel/").status_code, 200)

    def test_haber_ekle_yalniz_haber_girebilenlere_acik(self):
        beklenen = {"Muhabir": 200, "Editör": 200, "Sayfa Sekreteri": 200,
                    "İlan Sorumlusu": 403, "Yayın Yönetmeni": 200}
        for rol, kod in beklenen.items():
            with self.subTest(rol=rol):
                self._gir(rol)
                self.assertEqual(self.client.get("/panel/haber/ekle").status_code, kod)

    def test_roller_ekrani_yalniz_yayin_yonetmenine_acik(self):
        for rol in self.kullanicilar:
            with self.subTest(rol=rol):
                self._gir(rol)
                beklenen = 200 if rol == "Yayın Yönetmeni" else 403
                self.assertEqual(self.client.get("/panel/roller").status_code, beklenen)

    # --- iş akışı: muhabir yayınlayamaz ---
    def test_muhabir_taslak_kaydedebilir(self):
        self._gir("Muhabir")
        yanit = self.client.post("/panel/haber/ekle", {
            "baslik": "Muhabirin taslağı",
            "spot": "", "govde": "", "etiketler": [],
            "kategori": self.kategori.pk,
            "durum": Haber.DURUM_PASIF, "hazirlik": "taslak",
            "kaynak_turu": Haber.KAYNAK_MUHABIR, "muhabir": "A. Yılmaz",
        })
        self.assertEqual(yanit.status_code, 302)
        haber = Haber.objects.get(baslik="Muhabirin taslağı")
        self.assertEqual(haber.durum, Haber.DURUM_PASIF)
        self.assertEqual(haber.olusturan, self.kullanicilar["Muhabir"])
        self.assertEqual(haber.meta_yazar, "fikir_iscisi")

    def test_muhabir_kendi_haberini_yayina_alamaz(self):
        haber = Haber.objects.create(
            id=820001, slug="t", baslik="Taslak", kategori=self.kategori,
            durum=Haber.DURUM_PASIF, hazirlik="taslak",
            olusturan=self.kullanicilar["Muhabir"])
        self._gir("Muhabir")
        yanit = self.client.post(f"/panel/haber/{haber.pk}", {
            "baslik": "Taslak", "spot": "Spot metni.",
            "govde": "<p>Bir.</p><p>İki.</p>",
            "kategori": self.kategori.pk, "etiketler": [self.etiket.pk],
            "durum": Haber.DURUM_AKTIF, "hazirlik": "hazir",
            "kaynak_turu": Haber.KAYNAK_AJANS,
            "yayin_zamani": timezone.now().strftime("%Y-%m-%d %H:%M:%S"),
        })
        self.assertEqual(yanit.status_code, 200)   # form hatayla geri döner
        self.assertContains(yanit, "yayına alma yetkiniz yok")
        haber.refresh_from_db()
        self.assertEqual(haber.durum, Haber.DURUM_PASIF)

    def test_editor_baskasinin_haberini_yayina_alabilir(self):
        haber = Haber.objects.create(
            id=820002, slug="t2", baslik="Taslak 2", kategori=self.kategori,
            durum=Haber.DURUM_PASIF, hazirlik="taslak",
            olusturan=self.kullanicilar["Muhabir"])
        self._gir("Editör")
        yanit = self.client.post(f"/panel/haber/{haber.pk}", {
            "baslik": "Taslak 2", "spot": "Spot metni.",
            "govde": "<p>Bir.</p><p>İki.</p>",
            "kategori": self.kategori.pk, "etiketler": [self.etiket.pk],
            "durum": Haber.DURUM_AKTIF, "hazirlik": "hazir",
            "kaynak_turu": Haber.KAYNAK_AJANS,
            "yayin_zamani": timezone.now().strftime("%Y-%m-%d %H:%M:%S"),
        })
        self.assertEqual(yanit.status_code, 302)
        haber.refresh_from_db()
        self.assertEqual(haber.durum, Haber.DURUM_AKTIF)

    def test_yayinlanan_haber_sitede_gorunuyor(self):
        """Panelden yayına alınan haber ön yüzde açılmalı — uçtan uca."""
        haber = Haber.objects.create(
            id=820003, slug="ucdan-uca", baslik="Uçtan uca", kategori=self.kategori,
            spot="Spot", govde="<p>Bir.</p><p>İki.</p>",
            durum=Haber.DURUM_PASIF, hazirlik="taslak")
        self.assertEqual(self.client.get(haber.get_absolute_url()).status_code, 404)

        self._gir("Yayın Yönetmeni")
        self.client.post(f"/panel/haber/{haber.pk}", {
            "baslik": "Uçtan uca", "spot": "Spot",
            "govde": "<p>Bir.</p><p>İki.</p>",
            "kategori": self.kategori.pk, "etiketler": [self.etiket.pk],
            "durum": Haber.DURUM_AKTIF, "hazirlik": "hazir",
            "kaynak_turu": Haber.KAYNAK_AJANS,
            "yayin_zamani": timezone.now().strftime("%Y-%m-%d %H:%M:%S"),
        })
        self.client.logout()
        self.assertEqual(self.client.get(haber.get_absolute_url()).status_code, 200)

    # --- Bugün kuyruğu ---
    def test_bugun_kuyrugu_sadece_masadakileri_sayiyor(self):
        Haber.objects.create(id=821001, slug="a", baslik="A", kategori=self.kategori,
                             durum=Haber.DURUM_PASIF, hazirlik="taslak")
        Haber.objects.create(id=821002, slug="b", baslik="B", kategori=self.kategori,
                             durum=Haber.DURUM_AKTIF, hazirlik="hazir",
                             yayin_zamani=timezone.now())
        self._gir("Editör")
        yanit = self.client.get("/panel/")
        self.assertEqual(yanit.context["kuyruk_sayisi"], 1)

    # --- Akış süzgeci ---
    def test_akis_suzgeci_daraltiyor(self):
        spor = KategoriTur.objects.get(tur=Kategori.TUR_HABER, slug="spor").kategori
        Haber.objects.create(id=822001, slug="g", baslik="Gündem haberi",
                             kategori=self.kategori, durum=Haber.DURUM_AKTIF,
                             yayin_zamani=timezone.now())
        Haber.objects.create(id=822002, slug="s", baslik="Spor haberi",
                             kategori=spor, durum=Haber.DURUM_AKTIF,
                             yayin_zamani=timezone.now())
        self._gir("Editör")
        yanit = self.client.get("/panel/akis", {"kategori": spor.pk})
        self.assertEqual(yanit.context["sayfa"].paginator.count, 1)
        yanit = self.client.get("/panel/akis", {"q": "Gündem"})
        self.assertEqual(yanit.context["sayfa"].paginator.count, 1)

    def test_akis_silinmisleri_gizliyor(self):
        """Yumuşak silme: durum 3 içerik ekranlarında görünmez (§9)."""
        Haber.objects.create(id=823001, slug="x", baslik="Silinmiş",
                             kategori=self.kategori, durum=Haber.DURUM_SILINMIS)
        self._gir("Editör")
        yanit = self.client.get("/panel/akis")
        self.assertEqual(yanit.context["sayfa"].paginator.count, 0)

    # --- menü yetkiye göre kısılıyor ---
    def test_menude_roller_baglantisi_yalniz_yetkilide(self):
        self._gir("Muhabir")
        self.assertNotContains(self.client.get("/panel/"), "/panel/roller")
        self._gir("Yayın Yönetmeni")
        self.assertContains(self.client.get("/panel/"), "/panel/roller")

    # --- panel adresi site kategorisini gölgelemiyor ---
    def test_panel_adresi_kategori_kalibini_golgelemedi(self):
        """`/panel/...` tek dilimli olduğu için kategori kalıbına da uyardı."""
        from django.urls import resolve
        self.assertEqual(resolve("/panel/").url_name, "panel-bugun")
        self.assertEqual(resolve("/gundem").url_name, "kategori")
