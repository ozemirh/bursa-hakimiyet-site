"""Panelin liste ekranları — erişim, yetki, süzgeç ve düzenleme formu.

`tests_panel_ekran.py` ile aynı gerekçe: **menüde bağlantının görünmemesi
yetki denetimi değildir.** Her ekran doğrudan adresten çağrılıyor.

Ölçülen sütun sözleşmeleri mevcut panelin dökümünden geliyor
(`gallery_list.php`, `video_list.php`, `editorialist_list.php`,
`authors_list.php`, `categories_list.php`); testler o sütunların ekranda
olduğunu da doğruluyor.
"""

from django.contrib.auth.models import Group, User
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from medya.models import FotoGaleri, KoseYazisi, Video, Yazar
from taksonomi.models import (Etiket, Ilce, Kategori, KategoriTur,
                              Kaynak, Yonlendirme)

from .models import Haber
from .panel import (TOPLU_ONAY_ESIGI, TOPLU_UST_SINIR, kaynak_anahtari,
                    kaynak_olcumu, kaynak_tespitleri)

PAROLA = "deneme-parola-123"

# Her ekranın adresi ve o ekrana giren rol(ler). Yetkisiz rol 403 almalı.
EKRANLAR = {
    "/panel/mansetler":     {"Sayfa Sekreteri", "Yayın Yönetmeni"},
    "/panel/kose":          {"Editör", "Yayın Yönetmeni"},
    "/panel/yazarlar":      {"Editör", "Yayın Yönetmeni"},
    "/panel/galeriler":     {"Muhabir", "Editör", "Sayfa Sekreteri",
                             "Yayın Yönetmeni"},
    "/panel/videolar":      {"Muhabir", "Editör", "Sayfa Sekreteri",
                             "Yayın Yönetmeni"},
    "/panel/kategoriler":   {"Yayın Yönetmeni"},
    "/panel/kullanicilar":  {"Yayın Yönetmeni"},
}


class PanelListeleri(TestCase):

    @classmethod
    def setUpTestData(cls):
        call_command("taksonomi_kur", verbosity=0)
        call_command("roller_kur", verbosity=0)

        cls.kategori = KategoriTur.objects.get(
            tur=Kategori.TUR_HABER, slug="gundem").kategori
        cls.spor = KategoriTur.objects.get(
            tur=Kategori.TUR_HABER, slug="spor").kategori

        cls.kullanicilar = {}
        for sira, rol in enumerate(("Muhabir", "Editör", "Sayfa Sekreteri",
                                    "İlan Sorumlusu", "Yayın Yönetmeni")):
            k = User.objects.create_user(f"k{sira}", password=PAROLA,
                                         first_name="Kişi", last_name=str(sira))
            k.groups.add(Group.objects.get(name=rol))
            cls.kullanicilar[rol] = k

        simdi = timezone.now()

        cls.yazar = Yazar.objects.create(
            id=76, slug="namik-goz", ad="Namık Göz", unvan="Yazar",
            sayfasi_tarandi=True)
        cls.gecici_yazar = Yazar.objects.create(
            id=77, slug="gecici-kayit", ad="Geçici Kayıt",
            sayfasi_tarandi=False)

        cls.yazi = KoseYazisi.objects.create(
            id=900001, slug="kose-yazisi-bir", baslik="Köşe yazısı bir",
            yazar=cls.yazar, kategori=cls.kategori, yayin_zamani=simdi)
        cls.yazi_iki = KoseYazisi.objects.create(
            id=900002, slug="kose-yazisi-iki", baslik="Köşe yazısı iki",
            yazar=cls.gecici_yazar, yayin_zamani=simdi)
        KoseYazisi.objects.create(
            id=900003, slug="silinmis-yazi", baslik="Silinmiş yazı",
            yazar=cls.yazar, durum=KoseYazisi.DURUM_SILINMIS)

        foto = KategoriTur.objects.filter(tur=Kategori.TUR_FOTO).first()
        cls.galeri = FotoGaleri.objects.create(
            id=910001, slug="galeri-bir", baslik="Galeri bir",
            kategori=foto.kategori, kategori_dilimi=foto.adres_dilimi,
            yayin_zamani=simdi)
        cls.galeri_iki = FotoGaleri.objects.create(
            id=910002, slug="galeri-iki", baslik="Tanınmayan dilim",
            kategori=None, kategori_dilimi="haber-213", yayin_zamani=simdi)

        video = KategoriTur.objects.filter(tur=Kategori.TUR_VIDEO).first()
        cls.video = Video.objects.create(
            id=920001, slug="video-bir", baslik="Video bir",
            kategori=video.kategori, kategori_dilimi=video.adres_dilimi,
            gomulu_url="https://ornek.example/embed/1", sure_saniye=125,
            yayin_zamani=simdi)
        cls.video_iki = Video.objects.create(
            id=920002, slug="video-iki", baslik="Oynatıcısız video",
            kategori=video.kategori, kategori_dilimi=video.adres_dilimi,
            yayin_zamani=simdi)

    def _gir(self, rol):
        self.client.force_login(self.kullanicilar[rol])

    # ------------------------------------------------------------------
    # 1. Giriş zorunluluğu — oturumsuz istek giriş sayfasına gider
    # ------------------------------------------------------------------

    def test_oturumsuz_butun_ekranlar_girise_yonlendiriyor(self):
        yollar = list(EKRANLAR) + [
            f"/panel/kose/{self.yazi.pk}",
            f"/panel/yazar/{self.yazar.pk}",
            f"/panel/galeri/{self.galeri.pk}",
            f"/panel/video/{self.video.pk}",
            f"/panel/kategori/{self.kategori.pk}",
            f"/panel/kullanici/{self.kullanicilar['Editör'].pk}",
        ]
        for yol in yollar:
            with self.subTest(yol=yol):
                yanit = self.client.get(yol)
                self.assertEqual(yanit.status_code, 302)
                self.assertIn("/panel/giris", yanit["Location"])

    # ------------------------------------------------------------------
    # 2. Yetki — yetkili 200, yetkisiz 403
    # ------------------------------------------------------------------

    def test_liste_ekranlari_yetkiye_gore_aciliyor(self):
        for yol, yetkililer in EKRANLAR.items():
            for rol in self.kullanicilar:
                with self.subTest(yol=yol, rol=rol):
                    self._gir(rol)
                    beklenen = 200 if rol in yetkililer else 403
                    self.assertEqual(self.client.get(yol).status_code, beklenen)

    def test_duzenleme_ekranlari_yetkiye_gore_aciliyor(self):
        beklenen = {
            f"/panel/kose/{self.yazi.pk}": {"Editör", "Yayın Yönetmeni"},
            f"/panel/yazar/{self.yazar.pk}": {"Editör", "Yayın Yönetmeni"},
            f"/panel/galeri/{self.galeri.pk}": {
                "Muhabir", "Editör", "Sayfa Sekreteri", "Yayın Yönetmeni"},
            f"/panel/video/{self.video.pk}": {
                "Muhabir", "Editör", "Sayfa Sekreteri", "Yayın Yönetmeni"},
            f"/panel/kategori/{self.kategori.pk}": {"Yayın Yönetmeni"},
            f"/panel/kullanici/{self.kullanicilar['Editör'].pk}": {
                "Yayın Yönetmeni"},
        }
        for yol, yetkililer in beklenen.items():
            for rol in self.kullanicilar:
                with self.subTest(yol=yol, rol=rol):
                    self._gir(rol)
                    kod = 200 if rol in yetkililer else 403
                    self.assertEqual(self.client.get(yol).status_code, kod)

    # ------------------------------------------------------------------
    # 3. Liste içeriği
    # ------------------------------------------------------------------

    def test_kose_listesi_kayitlari_ve_sutunlari_basiyor(self):
        self._gir("Editör")
        yanit = self.client.get("/panel/kose")
        self.assertContains(yanit, "Köşe yazısı bir")
        self.assertContains(yanit, "Namık Göz")
        for sutun in ("Başlık", "Yazar", "Gösterim", "Tarih", "Editör"):
            self.assertContains(yanit, sutun)
        # Yumuşak silme: durum 3 içerik ekranlarında görünmez (§9).
        self.assertNotContains(yanit, "Silinmiş yazı")
        self.assertEqual(yanit.context["sayfa"].paginator.count, 2)

    def test_yazar_listesi_yazi_sayisini_sayiyor(self):
        """Sayaç yumuşak silinmişleri saymaz — liste de onları gizliyor (§9)."""
        self._gir("Editör")
        yanit = self.client.get("/panel/yazarlar")
        self.assertContains(yanit, "Namık Göz")
        satirlar = {s["duzenle"]: s for s in yanit.context["satirlar"]}
        # Ad · fotoğraf · unvan · okunma · yazı sayısı · durum · kayıt
        namik = satirlar[f"/panel/yazar/{self.yazar.pk}"]
        self.assertEqual(namik["hucreler"][4]["metin"], 1)
        gecici = satirlar[f"/panel/yazar/{self.gecici_yazar.pk}"]
        self.assertEqual(gecici["hucreler"][4]["metin"], 1)

    def test_yazar_listesi_gecici_kayitlari_uyariyor(self):
        self._gir("Editör")
        yanit = self.client.get("/panel/yazarlar")
        self.assertIn("1 yazarın sayfası arşivde yok", yanit.context["uyari"])

    def test_galeri_listesi_taninmayan_dilimi_ham_gosteriyor(self):
        self._gir("Editör")
        yanit = self.client.get("/panel/galeriler")
        self.assertContains(yanit, "haber-213")
        self.assertEqual(yanit.context["sayfa"].paginator.count, 2)

    def test_video_listesi_sureyi_cozuyor(self):
        self._gir("Editör")
        yanit = self.client.get("/panel/videolar")
        self.assertContains(yanit, "2:05")
        self.assertIn("1 videoda oynatma adresi yok", yanit.context["uyari"])

    def test_kategori_listesi_dondurulmus_sluglari_gosteriyor(self):
        self._gir("Yayın Yönetmeni")
        yanit = self.client.get("/panel/kategoriler")
        self.assertContains(yanit, "gundem")
        self.assertIn("DONDURULMUŞ", yanit.context["uyari"])
        self.assertEqual(yanit.context["sayfa"].paginator.count,
                         Kategori.objects.count())

    # ------------------------------------------------------------------
    # Manşetler — §14 "defterden slota"
    # ------------------------------------------------------------------

    def test_manset_listesi_yalniz_isaretlileri_gosteriyor(self):
        from .models import Haber
        kategori = self.kategori
        simdi = timezone.now()
        Haber.objects.create(id=940001, slug="m1", baslik="Ana manşetteki",
                             kategori=kategori, durum=Haber.DURUM_AKTIF,
                             yayin_zamani=simdi, manset_ana=True)
        Haber.objects.create(id=940002, slug="m2", baslik="Kare manşetteki",
                             kategori=kategori, durum=Haber.DURUM_AKTIF,
                             yayin_zamani=simdi, manset_kare=True)
        Haber.objects.create(id=940003, slug="m3", baslik="Manşetsiz",
                             kategori=kategori, durum=Haber.DURUM_AKTIF,
                             yayin_zamani=simdi)
        self._gir("Sayfa Sekreteri")
        yanit = self.client.get("/panel/mansetler")
        self.assertEqual(yanit.context["sayfa"].paginator.count, 2)
        self.assertContains(yanit, "Ana manşetteki")
        self.assertNotContains(yanit, "Manşetsiz")
        self.assertIn("Slot doluluğu", yanit.context["ust_bilgi"])

        # slot süzgeci
        yanit = self.client.get("/panel/mansetler", {"slot": "kare"})
        self.assertEqual(yanit.context["sayfa"].paginator.count, 1)

    def test_manset_listesi_yayindan_dusmusu_uyariyor(self):
        from .models import Haber
        Haber.objects.create(id=940004, slug="m4", baslik="Pasif manşet",
                             kategori=self.kategori, durum=Haber.DURUM_PASIF,
                             manset_ana=True)
        self._gir("Yayın Yönetmeni")
        yanit = self.client.get("/panel/mansetler")
        self.assertIn("1 manşet kaydı yayında değil", yanit.context["uyari"])

    def test_editor_manset_ekranina_giremiyor(self):
        """§11: manşete alma Editör'de YOK, Sayfa Sekreteri'nde var."""
        self._gir("Editör")
        self.assertEqual(self.client.get("/panel/mansetler").status_code, 403)
        self.assertNotContains(self.client.get("/panel/"), "/panel/mansetler")

    def test_kategori_haber_sayimi_istege_bagli(self):
        """Ölçüm kararı: gruplu sayım 96.473 haberde 486 ms sürüyordu.

        Ayar ekranı her açılışta tam tablo taraması yapmamalı; sayı
        `?sayim=1` ile isteniyor.
        """
        self._gir("Yayın Yönetmeni")
        varsayilan = self.client.get("/panel/kategoriler")
        ilk = varsayilan.context["satirlar"][0]["hucreler"][5]
        self.assertEqual(ilk["tur"], "yok")
        self.assertIn("Haber sayılarını hesapla",
                      [ad for _, ad in varsayilan.context["ek_baglantilar"]])

        sayimli = self.client.get("/panel/kategoriler", {"sayim": "1"})
        ilk = sayimli.context["satirlar"][0]["hucreler"][5]
        self.assertEqual(ilk["tur"], "metin")
        self.assertEqual(sayimli.context["ek_baglantilar"], [])

    def test_akis_editor_suzgeci_acik_hesaplari_listeliyor(self):
        """Mevcut panelin 'Editör Seç' listesi de bütün hesapları gösteriyordu.

        Haberi olan kullanıcıları aramak 96.473 satırı tarayıp **668 ms**
        sürüyordu ve göç kayıtlarında `olusturan` boş olduğu için liste
        boş dönüyordu.
        """
        pasif = User.objects.create_user("kapali", first_name="Kapalı",
                                         last_name="Hesap")
        pasif.is_active = False
        pasif.save()
        self._gir("Editör")
        yanit = self.client.get("/panel/akis")
        editor = [s for s in yanit.context["suzgecler"]
                  if s["ad"] == "editor"][0]
        adlar = [ad for _, ad in editor["secenekler"]]
        self.assertIn("k1", adlar)                 # Editör hesabı
        self.assertNotIn("kapali", adlar)          # kapalı hesap listede yok

    def test_kullanici_listesi_cakisan_adi_isaretliyor(self):
        """§2 düzeltme kalemi: dört hesap 'Administrator' adını paylaşıyordu."""
        User.objects.create_user("admin1", first_name="Administrator",
                                 last_name="")
        User.objects.create_user("admin2", first_name="Administrator",
                                 last_name="")
        self._gir("Yayın Yönetmeni")
        yanit = self.client.get("/panel/kullanicilar")
        self.assertIn("Administrator", yanit.context["uyari"])
        self.assertIn("görünen ad birden çok hesapta", yanit.context["uyari"])

    # ------------------------------------------------------------------
    # 4. Süzgeçler daraltıyor
    # ------------------------------------------------------------------

    def test_kose_suzgeci_daraltiyor(self):
        self._gir("Editör")
        yanit = self.client.get("/panel/kose", {"yazar": self.yazar.pk})
        self.assertEqual(yanit.context["sayfa"].paginator.count, 1)
        yanit = self.client.get("/panel/kose", {"q": "iki"})
        self.assertEqual(yanit.context["sayfa"].paginator.count, 1)

    def test_galeri_kategori_suzgeci_daraltiyor(self):
        self._gir("Editör")
        yanit = self.client.get("/panel/galeriler",
                                {"kategori": self.galeri.kategori_id})
        self.assertEqual(yanit.context["sayfa"].paginator.count, 1)

    def test_video_durum_suzgeci_daraltiyor(self):
        Video.objects.filter(pk=self.video_iki.pk).update(
            durum=Video.DURUM_PASIF)
        self._gir("Editör")
        yanit = self.client.get("/panel/videolar",
                                {"durum": Video.DURUM_PASIF})
        self.assertEqual(yanit.context["sayfa"].paginator.count, 1)

    def test_kategori_tur_suzgeci_daraltiyor(self):
        self._gir("Yayın Yönetmeni")
        toplam = Kategori.objects.count()
        yanit = self.client.get("/panel/kategoriler",
                                {"tur": Kategori.TUR_VIDEO})
        sayi = yanit.context["sayfa"].paginator.count
        self.assertGreater(sayi, 0)
        self.assertLessEqual(sayi, toplam)

    def test_yazar_kayit_suzgeci_gecicileri_ayiriyor(self):
        self._gir("Editör")
        yanit = self.client.get("/panel/yazarlar", {"kayit": "gecici"})
        self.assertEqual(yanit.context["sayfa"].paginator.count, 1)

    def test_kullanici_rol_suzgeci_daraltiyor(self):
        self._gir("Yayın Yönetmeni")
        grup = Group.objects.get(name="Muhabir")
        yanit = self.client.get("/panel/kullanicilar", {"rol": grup.pk})
        self.assertEqual(yanit.context["sayfa"].paginator.count, 1)

    # ------------------------------------------------------------------
    # 5. Sayfalama
    # ------------------------------------------------------------------

    def test_sayfa_boyu_secenegi_isliyor(self):
        self._gir("Editör")
        yanit = self.client.get("/panel/kose", {"boyut": 10})
        self.assertEqual(yanit.context["sayfa"].paginator.per_page, 10)

    def test_gecersiz_sayfa_boyu_varsayilana_duser(self):
        self._gir("Editör")
        for deger in ("999", "abc", ""):
            with self.subTest(deger=deger):
                yanit = self.client.get("/panel/kose", {"boyut": deger})
                self.assertEqual(yanit.context["sayfa"].paginator.per_page, 25)

    def test_sayfalama_baglantisi_suzgeci_koruyor(self):
        for sira in range(30):
            KoseYazisi.objects.create(
                id=930000 + sira, slug=f"toplu-{sira}", baslik=f"Toplu {sira}",
                yazar=self.yazar, yayin_zamani=timezone.now())
        self._gir("Editör")
        yanit = self.client.get("/panel/kose", {"yazar": self.yazar.pk})
        self.assertIn(f"yazar={self.yazar.pk}", yanit.context["korunan"])
        self.assertNotIn("sayfa=", yanit.context["korunan"])
        self.assertTrue(yanit.context["sayfa"].has_next())

    # ------------------------------------------------------------------
    # 6. Düzenleme formları gerçekten kaydediyor
    # ------------------------------------------------------------------

    def test_kose_yazisi_kaydediliyor(self):
        self._gir("Editör")
        yanit = self.client.post(f"/panel/kose/{self.yazi.pk}", {
            "baslik": "Yeni başlık", "yazar": self.yazar.pk,
            "kategori": self.kategori.pk, "spot": "Spot",
            "govde": "<p>Bir.</p>", "durum": KoseYazisi.DURUM_AKTIF,
            "yayin_zamani": timezone.now().strftime("%Y-%m-%d %H:%M:%S"),
            "guncelleme_zamani": "", "gorsel_alt": "",
        })
        self.assertEqual(yanit.status_code, 302)
        self.yazi.refresh_from_db()
        self.assertEqual(self.yazi.baslik, "Yeni başlık")

    def test_kose_yazisinin_slugu_ve_kimligi_formda_yok(self):
        """Adresin parçası olan iki alan forma hiç girmiyor."""
        self._gir("Editör")
        alanlar = self.client.get(
            f"/panel/kose/{self.yazi.pk}").context["form"].fields
        self.assertNotIn("slug", alanlar)
        self.assertNotIn("id", alanlar)

    def test_yazar_kaydediliyor(self):
        self._gir("Editör")
        yanit = self.client.post(f"/panel/yazar/{self.gecici_yazar.pk}", {
            "ad": "Tamamlanan Ad", "unvan": "Köşe yazarı", "ozgecmis": "",
            "eposta": "", "aktif": "on", "sira": 0,
        })
        self.assertEqual(yanit.status_code, 302)
        self.gecici_yazar.refresh_from_db()
        self.assertEqual(self.gecici_yazar.ad, "Tamamlanan Ad")

    def test_galeri_kareler_notu_kaydediliyor(self):
        self._gir("Editör")
        yanit = self.client.post(f"/panel/galeri/{self.galeri.pk}", {
            "baslik": "Galeri bir", "kategori": self.galeri.kategori_id,
            "spot": "", "durum": FotoGaleri.DURUM_AKTIF,
            "yayin_zamani": timezone.now().strftime("%Y-%m-%d %H:%M:%S"),
            "guncelleme_zamani": "", "gorsel_alt": "Kapak",
            "kareler_notu": "Kareler sağlayıcı dökümünden gelecek.",
        })
        self.assertEqual(yanit.status_code, 302)
        self.galeri.refresh_from_db()
        self.assertFalse(self.galeri.kareler_eksik)
        self.assertEqual(self.galeri.gorsel_alt, "Kapak")

    def test_video_oynatici_adresi_kaydediliyor(self):
        self._gir("Editör")
        yanit = self.client.post(f"/panel/video/{self.video_iki.pk}", {
            "baslik": "Oynatıcısız video", "kategori": self.video_iki.kategori_id,
            "spot": "", "durum": Video.DURUM_AKTIF,
            "yayin_zamani": timezone.now().strftime("%Y-%m-%d %H:%M:%S"),
            "guncelleme_zamani": "", "gorsel_alt": "",
            "gomulu_url": "https://ornek.example/embed/2",
            "video_url": "", "sure": "",
        })
        self.assertEqual(yanit.status_code, 302)
        self.video_iki.refresh_from_db()
        self.assertEqual(self.video_iki.oynatma_adresi,
                         "https://ornek.example/embed/2")

    def test_kategori_formunda_slug_alani_yok(self):
        """§18: slug'lar dondurulmuştur; forma hiç konulmadı."""
        self._gir("Yayın Yönetmeni")
        yanit = self.client.get(f"/panel/kategori/{self.kategori.pk}")
        self.assertNotIn("slug", yanit.context["form"].fields)

    def test_kategori_adi_degisince_adres_degismiyor(self):
        self._gir("Yayın Yönetmeni")
        onceki = self.kategori.slug_al()
        yanit = self.client.post(f"/panel/kategori/{self.kategori.pk}", {
            "ad": "GÜNDEM HABERLERİ", "ust": "", "sira": 1, "aktif": "on",
        })
        self.assertEqual(yanit.status_code, 302)
        self.kategori.refresh_from_db()
        self.assertEqual(self.kategori.ad, "GÜNDEM HABERLERİ")
        self.assertEqual(self.kategori.slug_al(), onceki)

    def test_kategori_kendi_ustu_olamiyor(self):
        self._gir("Yayın Yönetmeni")
        yanit = self.client.post(f"/panel/kategori/{self.kategori.pk}", {
            "ad": self.kategori.ad, "ust": self.kategori.pk, "sira": 1,
            "aktif": "on",
        })
        self.assertEqual(yanit.status_code, 200)
        self.assertTrue(yanit.context["form"].errors)

    def test_kullanici_rolu_degistirilebiliyor(self):
        hedef = self.kullanicilar["Muhabir"]
        self._gir("Yayın Yönetmeni")
        editor_grubu = Group.objects.get(name="Editör")
        yanit = self.client.post(f"/panel/kullanici/{hedef.pk}", {
            "username": hedef.get_username(), "first_name": "Yeni",
            "last_name": "Muhabir", "email": "", "is_active": "on",
            "roller": [editor_grubu.pk],
        })
        self.assertEqual(yanit.status_code, 302)
        hedef.refresh_from_db()
        self.assertEqual([g.name for g in hedef.groups.all()], ["Editör"])

    def test_ayni_gorunen_ad_ikinci_kez_kaydedilemiyor(self):
        """§2 düzeltme kalemi kod düzeyinde: ad çakışması engelleniyor."""
        hedef = self.kullanicilar["Muhabir"]
        baskasi = self.kullanicilar["Editör"]
        self._gir("Yayın Yönetmeni")
        yanit = self.client.post(f"/panel/kullanici/{hedef.pk}", {
            "username": hedef.get_username(),
            "first_name": baskasi.first_name,
            "last_name": baskasi.last_name,
            "email": "", "is_active": "on", "roller": [],
        })
        self.assertEqual(yanit.status_code, 200)
        self.assertContains(yanit, "başka bir hesapta kullanılıyor")

    def test_kullanici_formunda_parola_alani_yok(self):
        self._gir("Yayın Yönetmeni")
        alanlar = self.client.get(
            f"/panel/kullanici/{self.kullanicilar['Editör'].pk}"
        ).context["form"].fields
        self.assertNotIn("password", alanlar)

    # ------------------------------------------------------------------
    # 7. Menü yetkiye göre kısılıyor
    # ------------------------------------------------------------------

    def test_menude_kose_baglantisi_yalniz_kose_yetkilisinde(self):
        self._gir("Muhabir")
        self.assertNotContains(self.client.get("/panel/"), "/panel/kose")
        self._gir("Editör")
        self.assertContains(self.client.get("/panel/"), "/panel/kose")

    def test_menude_ayarlar_yalniz_yayin_yonetmeninde(self):
        self._gir("Editör")
        yanit = self.client.get("/panel/")
        self.assertNotContains(yanit, "/panel/kategoriler")
        self.assertNotContains(yanit, "/panel/kullanicilar")
        self._gir("Yayın Yönetmeni")
        yanit = self.client.get("/panel/")
        self.assertContains(yanit, "/panel/kategoriler")
        self.assertContains(yanit, "/panel/kullanicilar")

    def test_ilan_sorumlusu_galeri_ve_videoya_giremiyor(self):
        """İlan Sorumlusu içerik girme yetkiliğinde yok (§11)."""
        self._gir("İlan Sorumlusu")
        for yol in ("/panel/galeriler", "/panel/videolar",
                    "/panel/kose", "/panel/kategoriler"):
            with self.subTest(yol=yol):
                self.assertEqual(self.client.get(yol).status_code, 403)

    # ------------------------------------------------------------------
    # 8. Adres kalıpları site adreslerini gölgelemiyor
    # ------------------------------------------------------------------

    def test_panel_yollari_site_kaliplarini_golgelemedi(self):
        from django.urls import resolve
        self.assertEqual(resolve("/panel/yazarlar").url_name, "panel-yazarlar")
        self.assertEqual(resolve("/yazarlar").url_name, "yazarlar")
        self.assertEqual(resolve("/panel/videolar").url_name, "panel-videolar")
        self.assertEqual(resolve("/videolar").url_name, "videolar")
        self.assertEqual(resolve("/panel/galeriler").url_name, "panel-galeriler")
        self.assertEqual(resolve("/galeriler").url_name, "galeriler")


class KaynakTespitMotoru(TestCase):
    """Tespit kurallarının birim testleri.

    Kurallar canlı veriden ölçülerek çıkarıldı (76 kayıt, 27 Ağustos 2026).
    İki tanesi ilk ölçümde **fazla ateşliyordu** ve burada kilitlendi:
    sayılar ve küçük harfle başlayan cümleler "cümleden düşmüş kelime"
    sayılıyordu.
    """

    def test_sayi_kaynak_adi_olamaz(self):
        self.assertIn("sayisal", kaynak_tespitleri("525218"))

    def test_sayi_ayrica_kucuk_parca_sayilmiyor(self):
        self.assertNotIn("kucuk_parca", kaynak_tespitleri("525218"))

    def test_alan_adi_yakalaniyor(self):
        for ad in ("www.sondakika.com", "bursahakimiyet.com.tr", "https"):
            with self.subTest(ad=ad):
                self.assertIn("alan_adi", kaynak_tespitleri(ad))

    def test_kirk_karakterlik_kesme_imzasi(self):
        ad = "MHP Genel Başkanı Bahçeli grup toplantıs"
        self.assertEqual(len(ad), 40)
        self.assertIn("kesik", kaynak_tespitleri(ad))

    def test_cumle_parcasi_yakalaniyor(self):
        self.assertIn("cumle",
                      kaynak_tespitleri("Polis uyuşturucu tacirlerine göz açtırmı"))

    def test_cumle_ayrica_kucuk_parca_sayilmiyor(self):
        bulgular = kaynak_tespitleri("etkin bir ekonomiye geçişini desteklemey")
        self.assertIn("cumle", bulgular)
        self.assertNotIn("kucuk_parca", bulgular)

    def test_tek_kelimelik_kucuk_harf_parcasi(self):
        for ad in ("aktardi", "suyu", "ve"):
            with self.subTest(ad=ad):
                self.assertIn("kucuk_parca", kaynak_tespitleri(ad))

    def test_gercek_yayin_adlari_temiz_kaliyor(self):
        for ad in ("Sözcü", "BBC", "Independent Türkçe", "Our World in Data",
                   "TRT Haber", "İHA"):
            with self.subTest(ad=ad):
                self.assertEqual(kaynak_tespitleri(ad), [])

    def test_kendi_yayinimiz_bosluk_hatasina_ragmen_yakalaniyor(self):
        """Ölçülen kayıt: 'Bu rsahakimiyet' — boşluk yanlış yere düşmüş."""
        for ad in ("Bursa Hakimiyet", "Bu rsahakimiyet", "bursahakimiyet.com.tr"):
            with self.subTest(ad=ad):
                self.assertIn("kendi_yayinimiz", kaynak_tespitleri(ad))

    def test_meta_yazar_degeri_kaynak_degildir(self):
        self.assertIn("meta_yazar", kaynak_tespitleri("Haber Merkezi"))

    def test_birlesik_kayit_imzasi(self):
        for ad in ("İHA, DHA", "İHA - DHA - AA", "Haber Merkezi / İHA",
                   "Recep Saka-Metin Araç"):
            with self.subTest(ad=ad):
                self.assertIn("birlesik", kaynak_tespitleri(ad))

    def test_tekrar_yalniz_verilen_kumeye_gore(self):
        anahtar = kaynak_anahtari("Hürriyet")
        self.assertEqual(anahtar, "hurriyet")
        self.assertIn("tekrar", kaynak_tespitleri("HÜRRİYET", {anahtar}))
        self.assertNotIn("tekrar", kaynak_tespitleri("HÜRRİYET"))


class KaynakEkrani(TestCase):

    @classmethod
    def setUpTestData(cls):
        call_command("taksonomi_kur", verbosity=0)
        call_command("roller_kur", verbosity=0)
        cls.kategori = KategoriTur.objects.get(
            tur=Kategori.TUR_HABER, slug="gundem").kategori
        cls.kullanicilar = {}
        for sira, rol in enumerate(("Muhabir", "Editör", "Sayfa Sekreteri",
                                    "İlan Sorumlusu", "Yayın Yönetmeni")):
            k = User.objects.create_user(f"s{sira}", password=PAROLA,
                                         first_name="Kaynak", last_name=str(sira))
            k.groups.add(Group.objects.get(name=rol))
            cls.kullanicilar[rol] = k

        cls.iha = Kaynak.objects.create(ad="İHA", tur=Kaynak.TUR_AJANS)
        cls.iha_tekrar = Kaynak.objects.create(ad="iha")
        cls.cop = Kaynak.objects.create(ad="aktarildi")
        cls.sayi = Kaynak.objects.create(ad="525218")

        simdi = timezone.now()
        cls.haberler = []
        for sira in range(3):
            haber = Haber.objects.create(
                id=950000 + sira, slug=f"k{sira}", baslik=f"Kaynak haberi {sira}",
                kategori=cls.kategori, durum=Haber.DURUM_AKTIF,
                yayin_zamani=simdi)
            haber.kaynaklar.add(cls.iha_tekrar)
            cls.haberler.append(haber)

    def _gir(self, rol):
        self.client.force_login(self.kullanicilar[rol])

    # --- erişim ---

    def test_oturumsuz_girise_yonleniyor(self):
        for yol in ("/panel/kaynaklar", f"/panel/kaynak/{self.iha.pk}"):
            with self.subTest(yol=yol):
                yanit = self.client.get(yol)
                self.assertEqual(yanit.status_code, 302)
                self.assertIn("/panel/giris", yanit["Location"])

    def test_yalniz_yayin_yonetmeni_girebiliyor(self):
        for rol in self.kullanicilar:
            with self.subTest(rol=rol):
                self._gir(rol)
                beklenen = 200 if rol == "Yayın Yönetmeni" else 403
                self.assertEqual(
                    self.client.get("/panel/kaynaklar").status_code, beklenen)
                self.assertEqual(
                    self.client.get(f"/panel/kaynak/{self.iha.pk}").status_code,
                    beklenen)

    # --- liste ---

    def test_liste_kayitlari_ve_olcumu_basiyor(self):
        self._gir("Yayın Yönetmeni")
        yanit = self.client.get("/panel/kaynaklar")
        self.assertContains(yanit, "aktarildi")
        self.assertEqual(yanit.context["sayfa"].paginator.count, 4)
        self.assertIn("4 kayıt", yanit.context["ust_bilgi"])
        self.assertIn("3 sadeleşmiş ad", yanit.context["ust_bilgi"])

    def test_tespit_suzgeci_daraltiyor(self):
        self._gir("Yayın Yönetmeni")
        yanit = self.client.get("/panel/kaynaklar", {"tespit": "sayisal"})
        self.assertEqual(yanit.context["sayfa"].paginator.count, 1)
        yanit = self.client.get("/panel/kaynaklar", {"tespit": "tekrar"})
        self.assertEqual(yanit.context["sayfa"].paginator.count, 2)

    def test_tur_suzgeci_daraltiyor(self):
        self._gir("Yayın Yönetmeni")
        yanit = self.client.get("/panel/kaynaklar", {"tur": Kaynak.TUR_AJANS})
        self.assertEqual(yanit.context["sayfa"].paginator.count, 1)

    def test_olcum_sayilari(self):
        olcum = kaynak_olcumu()
        self.assertEqual(olcum["toplam"], 4)
        self.assertEqual(olcum["tekil"], 3)          # "İHA" ile "iha" aynı anahtar
        self.assertEqual(olcum["dagilim"]["tekrar"], 2)
        self.assertEqual(olcum["dagilim"]["sayisal"], 1)
        self.assertEqual(olcum["pasif"], 0)

    # --- birleştirme ---

    def test_birlestirme_baglantilari_tasiyor_ve_iz_birakiyor(self):
        self._gir("Yayın Yönetmeni")
        self.assertEqual(self.iha.haberler.count(), 0)
        self.assertEqual(self.iha_tekrar.haberler.count(), 3)

        yanit = self.client.post(f"/panel/kaynak/{self.iha_tekrar.pk}", {
            "ad": "iha", "tur": Kaynak.TUR_DIS_YAYIN,
            "birlesti_ile": self.iha.pk, "baglantilari_tasi": "on",
        })
        self.assertEqual(yanit.status_code, 302)

        self.iha_tekrar.refresh_from_db()
        self.assertEqual(self.iha.haberler.count(), 3)
        self.assertEqual(self.iha_tekrar.haberler.count(), 0)
        self.assertFalse(self.iha_tekrar.aktif)             # seçim listesinden düştü
        self.assertEqual(self.iha_tekrar.birlesti_ile_id, self.iha.pk)
        # Kayıt SİLİNMEDİ — iz duruyor.
        self.assertTrue(Kaynak.objects.filter(pk=self.iha_tekrar.pk).exists())

    def test_birlestirme_baglantilari_tasimadan_da_yapilabiliyor(self):
        self._gir("Yayın Yönetmeni")
        self.client.post(f"/panel/kaynak/{self.iha_tekrar.pk}", {
            "ad": "iha", "tur": Kaynak.TUR_DIS_YAYIN,
            "birlesti_ile": self.iha.pk,
        })
        self.iha_tekrar.refresh_from_db()
        self.assertEqual(self.iha_tekrar.haberler.count(), 3)
        self.assertFalse(self.iha_tekrar.aktif)

    def test_kendine_birlestirilemiyor(self):
        self._gir("Yayın Yönetmeni")
        yanit = self.client.post(f"/panel/kaynak/{self.iha.pk}", {
            "ad": "İHA", "tur": Kaynak.TUR_AJANS,
            "birlesti_ile": self.iha.pk, "aktif": "on",
        })
        self.assertEqual(yanit.status_code, 200)
        self.assertTrue(yanit.context["form"].errors)

    def test_birlestirme_zinciri_engelleniyor(self):
        """A→B→C zinciri bağlantıları iki kez taşımak zorunda bırakırdı."""
        # Hedef AKTIF birakiliyor: pasif olsaydi zaten secim listesine hic
        # girmezdi ve Django genel "gecerli bir secenek secin" hatasini
        # verirdi. Bu test ozel zincir korumasini sinamali.
        Kaynak.objects.filter(pk=self.iha.pk).update(birlesti_ile=self.cop.pk)
        self._gir("Yayın Yönetmeni")
        yanit = self.client.post(f"/panel/kaynak/{self.iha_tekrar.pk}", {
            "ad": "iha", "tur": Kaynak.TUR_DIS_YAYIN,
            "birlesti_ile": self.iha.pk, "baglantilari_tasi": "on",
        })
        self.assertEqual(yanit.status_code, 200)
        self.assertContains(yanit, "zaten başka bir kayda birleştirilmiş")

    def test_pasif_kaynak_birlestirme_hedefi_olarak_sunulmuyor(self):
        Kaynak.objects.filter(pk=self.iha.pk).update(aktif=False)
        self._gir("Yayın Yönetmeni")
        yanit = self.client.get(f"/panel/kaynak/{self.iha_tekrar.pk}")
        hedefler = yanit.context["form"].fields["birlesti_ile"].queryset
        self.assertNotIn(self.iha, hedefler)

    def test_tur_ajansa_cevrilebiliyor(self):
        self._gir("Yayın Yönetmeni")
        yanit = self.client.post(f"/panel/kaynak/{self.cop.pk}", {
            "ad": "AA", "tur": Kaynak.TUR_AJANS, "aktif": "on",
        })
        self.assertEqual(yanit.status_code, 302)
        self.cop.refresh_from_db()
        self.assertEqual(self.cop.tur, Kaynak.TUR_AJANS)
        self.assertEqual(self.cop.ad, "AA")

    def test_pasiflestirilen_kaynak_haber_formunda_gorunmuyor(self):
        from .formlar import HaberForm
        self.assertIn(self.cop, HaberForm().fields["kaynaklar"].queryset)
        Kaynak.objects.filter(pk=self.cop.pk).update(aktif=False)
        self.assertNotIn(self.cop, HaberForm().fields["kaynaklar"].queryset)

    def test_birlestirilen_kaynak_haber_formunda_gorunmuyor(self):
        from .formlar import HaberForm
        Kaynak.objects.filter(pk=self.iha_tekrar.pk).update(
            birlesti_ile=self.iha.pk)
        self.assertNotIn(self.iha_tekrar,
                         HaberForm().fields["kaynaklar"].queryset)

    def test_menude_kaynaklar_yalniz_taksonomi_yetkisinde(self):
        self._gir("Editör")
        self.assertNotContains(self.client.get("/panel/"), "/panel/kaynaklar")
        self._gir("Yayın Yönetmeni")
        self.assertContains(self.client.get("/panel/"), "/panel/kaynaklar")


class SifreEkrani(TestCase):

    @classmethod
    def setUpTestData(cls):
        call_command("roller_kur", verbosity=0)
        cls.kullanici = User.objects.create_user("sifreli", password=PAROLA)
        cls.kullanici.groups.add(Group.objects.get(name="Muhabir"))

    def test_oturumsuz_girise_yonleniyor(self):
        yanit = self.client.get("/panel/sifre")
        self.assertEqual(yanit.status_code, 302)
        self.assertIn("/panel/giris", yanit["Location"])

    def test_her_role_acik(self):
        """Yetkilik yok, bilerek: herkes kendi parolasını değiştirebilmeli."""
        for rol in ("Muhabir", "Editör", "Sayfa Sekreteri",
                    "İlan Sorumlusu", "Yayın Yönetmeni"):
            with self.subTest(rol=rol):
                kullanici = User.objects.create_user(f"p-{rol}", password=PAROLA)
                kullanici.groups.add(Group.objects.get(name=rol))
                self.client.force_login(kullanici)
                self.assertEqual(self.client.get("/panel/sifre").status_code, 200)

    def test_parola_gercekten_degisiyor_ve_oturum_dusmuyor(self):
        self.client.login(username="sifreli", password=PAROLA)
        yeni = "yeni-parola-987654"
        yanit = self.client.post("/panel/sifre", {
            "old_password": PAROLA,
            "new_password1": yeni, "new_password2": yeni,
        })
        self.assertEqual(yanit.status_code, 302)
        self.kullanici.refresh_from_db()
        self.assertTrue(self.kullanici.check_password(yeni))
        # `update_session_auth_hash` sayesinde oturum düşmemeli.
        self.assertEqual(self.client.get("/panel/").status_code, 200)

    def test_yanlis_eski_parola_reddediliyor(self):
        self.client.force_login(self.kullanici)
        yanit = self.client.post("/panel/sifre", {
            "old_password": "yanlis-parola",
            "new_password1": "yeni-parola-987654",
            "new_password2": "yeni-parola-987654",
        })
        self.assertEqual(yanit.status_code, 200)
        self.assertTrue(yanit.context["form"].errors)
        self.kullanici.refresh_from_db()
        self.assertTrue(self.kullanici.check_password(PAROLA))

    def test_zayif_parola_reddediliyor(self):
        self.client.force_login(self.kullanici)
        yanit = self.client.post("/panel/sifre", {
            "old_password": PAROLA, "new_password1": "1234",
            "new_password2": "1234",
        })
        self.assertEqual(yanit.status_code, 200)
        self.assertTrue(yanit.context["form"].errors)

    def test_menude_sifre_her_kullanicida_var(self):
        self.client.force_login(self.kullanici)
        self.assertContains(self.client.get("/panel/"), "/panel/sifre")


# Fiil → o fiili yapabilen roller. PANEL-NOTLARI.md §12'nin tablosundan
# geldi; tek sapma "kategori" satırıdır ve bilinçlidir (bkz. TOPLU_FIILLER
# içindeki not).
FIIL_ROLLERI = {
    "yayina_al":       {"Editör", "Sayfa Sekreteri", "Yayın Yönetmeni"},
    "yayindan_cek":    {"Editör", "Sayfa Sekreteri", "Yayın Yönetmeni"},
    "arsivle":         {"Editör", "Sayfa Sekreteri", "Yayın Yönetmeni"},
    "hazirlik":        {"Muhabir", "Editör", "Sayfa Sekreteri", "Yayın Yönetmeni"},
    "ilce":            {"Muhabir", "Editör", "Sayfa Sekreteri", "Yayın Yönetmeni"},
    "etiket":          {"Muhabir", "Editör", "Sayfa Sekreteri", "Yayın Yönetmeni"},
    "mansete_al":      {"Sayfa Sekreteri", "Yayın Yönetmeni"},
    "mansetten_cikar": {"Sayfa Sekreteri", "Yayın Yönetmeni"},
    "kategori":        {"Yayın Yönetmeni"},
}


class TopluIslem(TestCase):
    """Toplu işlem fiilleri — PANEL-NOTLARI.md §12.

    Mevcut panelin ölçülmüş hatası "seçim kutusu var, fiil yok"tu. Buradaki
    testler üç şeyi birden ölçüyor: fiil çalışıyor mu, yetkisiz reddediliyor
    mu, ve yetkisiz kullanıcının şeridinde **görünüyor mu**.
    """

    @classmethod
    def setUpTestData(cls):
        call_command("taksonomi_kur", verbosity=0)
        call_command("roller_kur", verbosity=0)
        cls.gundem = KategoriTur.objects.get(
            tur=Kategori.TUR_HABER, slug="gundem").kategori
        cls.spor = KategoriTur.objects.get(
            tur=Kategori.TUR_HABER, slug="spor").kategori
        cls.etiket = Etiket.objects.create(ad="Toplu", slug="toplu")
        cls.ilce = Ilce.objects.first()

        cls.kullanicilar = {}
        for sira, rol in enumerate(("Muhabir", "Editör", "Sayfa Sekreteri",
                                    "İlan Sorumlusu", "Yayın Yönetmeni")):
            k = User.objects.create_user(f"t{sira}", password=PAROLA,
                                         first_name="Toplu", last_name=str(sira))
            k.groups.add(Group.objects.get(name=rol))
            cls.kullanicilar[rol] = k

    def setUp(self):
        self.haberler = []
        for sira in range(4):
            haber = Haber.objects.create(
                id=960000 + sira, slug=f"toplu-{sira}",
                baslik=f"Toplu haber {sira}", kategori=self.gundem,
                spot="Spot metni.", govde="<p>Bir.</p><p>İki.</p>",
                durum=Haber.DURUM_PASIF, hazirlik="taslak")
            haber.etiketler.add(self.etiket)
            self.haberler.append(haber)
        self.kimlikler = [h.pk for h in self.haberler]

    def _gir(self, rol):
        self.client.force_login(self.kullanicilar[rol])

    def _gonder(self, fiil, **ek):
        veri = {"fiil": fiil, "kimlikler": self.kimlikler}
        veri.update(ek)
        return self.client.post("/panel/toplu", veri)

    # ------------------------------------------------------------------
    # 1. Yetki — her fiil × her rol
    # ------------------------------------------------------------------

    def test_her_fiil_her_rol_yetki_denetimi(self):
        ek = {"hazirlik_degeri": "incelemede", "ilce_degeri": self.ilce.pk,
              "etiket_degeri": self.etiket.pk, "manset_slot": "manset_ana",
              "kategori_degeri": self.spor.pk, "onay": "1"}
        for fiil, yetkililer in FIIL_ROLLERI.items():
            for rol in self.kullanicilar:
                with self.subTest(fiil=fiil, rol=rol):
                    self._gir(rol)
                    yanit = self._gonder(fiil, **ek)
                    if rol in yetkililer:
                        self.assertEqual(yanit.status_code, 302,
                                         f"{rol} {fiil} yapabilmeliydi")
                    else:
                        self.assertEqual(yanit.status_code, 403,
                                         f"{rol} {fiil} yapamamalıydı")

    def test_yetkisiz_fiil_seritte_gorunmuyor(self):
        """Şeritte görünmemek yetki denetimi DEĞİLDİR ama gereklidir:
        kullanıcıya yapamayacağı düğme gösterilmez."""
        beklenen = {
            "Muhabir": {"gorunur": ["Hazırlık ata", "İlçe ata", "Etiket ekle"],
                        "gorunmez": ["Yayına al", "Manşete al", "Kategori değiştir"]},
            "Editör": {"gorunur": ["Yayına al", "Arşive al", "Hazırlık ata"],
                       "gorunmez": ["Manşete al", "Kategori değiştir"]},
            "Sayfa Sekreteri": {"gorunur": ["Yayına al", "Manşete al"],
                                "gorunmez": ["Kategori değiştir"]},
            "Yayın Yönetmeni": {"gorunur": ["Yayına al", "Manşete al",
                                            "Kategori değiştir"],
                                "gorunmez": []},
        }
        for rol, kume in beklenen.items():
            self._gir(rol)
            yanit = self.client.get("/panel/akis")
            for ad in kume["gorunur"]:
                with self.subTest(rol=rol, fiil=ad, beklenen="görünür"):
                    self.assertContains(yanit, ad)
            for ad in kume["gorunmez"]:
                with self.subTest(rol=rol, fiil=ad, beklenen="görünmez"):
                    self.assertNotContains(yanit, ad)

    def test_hicbir_fiili_olmayan_rolde_secim_kutusu_da_yok(self):
        """Fiili olmayan seçim kutusu mevcut panelin hatasıydı; tekrarlanmıyor."""
        self._gir("İlan Sorumlusu")
        yanit = self.client.get("/panel/akis")
        self.assertIsNone(yanit.context["toplu"])
        self.assertNotContains(yanit, "data-toplu-kutu")
        self.assertNotContains(yanit, "toplu-serit")

    # ------------------------------------------------------------------
    # 2. Fiiller gerçekten uyguluyor
    # ------------------------------------------------------------------

    def test_yayindan_cek_ve_arsivle(self):
        Haber.objects.filter(pk__in=self.kimlikler).update(
            durum=Haber.DURUM_AKTIF)
        self._gir("Editör")
        self._gonder("yayindan_cek")
        self.assertEqual(Haber.objects.filter(
            pk__in=self.kimlikler, durum=Haber.DURUM_PASIF).count(), 4)
        self._gonder("arsivle")
        self.assertEqual(Haber.objects.filter(
            pk__in=self.kimlikler, durum=Haber.DURUM_ARSIV).count(), 4)

    def test_yayina_al_esigi_toplu_islemde_de_isliyor(self):
        """§4'ün yayın eşiği bir düğmeyle delinmemeli.

        İki kaydın spotu siliniyor; onlar atlanmalı, diğer ikisi yayına
        alınmalı.
        """
        Haber.objects.filter(pk__in=self.kimlikler[:2]).update(spot="")
        self._gir("Editör")
        yanit = self._gonder("yayina_al")
        self.assertEqual(yanit.status_code, 302)
        self.assertEqual(Haber.objects.filter(
            pk__in=self.kimlikler, durum=Haber.DURUM_AKTIF).count(), 2)
        self.assertEqual(Haber.objects.filter(
            pk__in=self.kimlikler[:2], durum=Haber.DURUM_PASIF).count(), 2)

    def test_yayina_alinan_haberin_yayin_zamani_doluyor(self):
        self._gir("Editör")
        self._gonder("yayina_al")
        for haber in Haber.objects.filter(pk__in=self.kimlikler):
            self.assertIsNotNone(haber.yayin_zamani)

    def test_hazirlik_atama(self):
        self._gir("Muhabir")
        self._gonder("hazirlik", hazirlik_degeri="incelemede")
        self.assertEqual(Haber.objects.filter(
            pk__in=self.kimlikler, hazirlik="incelemede").count(), 4)

    def test_ilce_atama(self):
        """§12: 556.824 haberin hiçbirinde ilçe yok; toplu atama bunun için."""
        self._gir("Muhabir")
        self._gonder("ilce", ilce_degeri=self.ilce.pk)
        self.assertEqual(Haber.objects.filter(
            pk__in=self.kimlikler, ilce=self.ilce).count(), 4)

    def test_etiket_ekleme_mevcut_etiketi_silmiyor(self):
        yeni = Etiket.objects.create(ad="İkinci", slug="ikinci")
        self._gir("Muhabir")
        self._gonder("etiket", etiket_degeri=yeni.pk)
        haber = Haber.objects.get(pk=self.kimlikler[0])
        self.assertEqual(haber.etiketler.count(), 2)

    def test_mansete_al_ve_cikar(self):
        self._gir("Sayfa Sekreteri")
        self._gonder("mansete_al", manset_slot="manset_kare")
        self.assertEqual(Haber.objects.filter(
            pk__in=self.kimlikler, manset_kare=True).count(), 4)
        self._gonder("mansetten_cikar")
        self.assertEqual(Haber.objects.filter(
            pk__in=self.kimlikler, manset_kare=True).count(), 0)

    # ------------------------------------------------------------------
    # 3. Kategori değişimi — adres uyarısı ve yönlendirme
    # ------------------------------------------------------------------

    def test_kategori_degisimi_once_onay_ekrani_aciyor(self):
        self._gir("Yayın Yönetmeni")
        yanit = self._gonder("kategori", kategori_degeri=self.spor.pk)
        self.assertEqual(yanit.status_code, 200)
        self.assertTemplateUsed(yanit, "panel/toplu_onay.html")
        # Hiçbir şey değişmemiş olmalı.
        self.assertEqual(Haber.objects.filter(
            pk__in=self.kimlikler, kategori=self.gundem).count(), 4)

    def test_onay_ekrani_dogru_adres_sayisini_veriyor(self):
        """Dördün biri zaten hedef kategoride; üç adres değişecek."""
        Haber.objects.filter(pk=self.kimlikler[0]).update(kategori=self.spor)
        self._gir("Yayın Yönetmeni")
        yanit = self._gonder("kategori", kategori_degeri=self.spor.pk)
        self.assertEqual(yanit.context["sayi"], 4)
        self.assertEqual(yanit.context["adres_degisecek"], 3)
        self.assertContains(yanit, "adresleri değiştirir")
        self.assertContains(yanit, "{kategori-slug}")

    def test_onay_ekrani_ornek_adresleri_gosteriyor(self):
        self._gir("Yayın Yönetmeni")
        yanit = self._gonder("kategori", kategori_degeri=self.spor.pk)
        ornekler = yanit.context["ornekler"]
        self.assertTrue(ornekler)
        eski, yeni = ornekler[0]
        self.assertTrue(eski.startswith("/gundem/"))
        self.assertTrue(yeni.startswith("/spor/"))

    def test_onaylandiginda_kategori_degisiyor_ve_yonlendirme_yaziliyor(self):
        self._gir("Yayın Yönetmeni")
        yanit = self._gonder("kategori", kategori_degeri=self.spor.pk, onay="1")
        self.assertEqual(yanit.status_code, 302)
        self.assertEqual(Haber.objects.filter(
            pk__in=self.kimlikler, kategori=self.spor).count(), 4)
        for haber in Haber.objects.filter(pk__in=self.kimlikler):
            eski = f"/gundem/{haber.slug}-{haber.pk}"
            self.assertTrue(
                Yonlendirme.objects.filter(eski_yol=eski, kod=301).exists(),
                f"{eski} için yönlendirme yazılmadı")

    def test_yonlendirme_eski_adresi_yeniye_bagliyor(self):
        self._gir("Yayın Yönetmeni")
        self._gonder("kategori", kategori_degeri=self.spor.pk, onay="1")
        haber = Haber.objects.get(pk=self.kimlikler[0])
        kayit = Yonlendirme.objects.get(
            eski_yol=f"/gundem/{haber.slug}-{haber.pk}")
        self.assertEqual(kayit.yeni_yol, haber.get_absolute_url())
        self.assertTrue(kayit.yeni_yol.startswith("/spor/"))

    def test_ayni_kategoriye_tasimada_yonlendirme_yazilmiyor(self):
        """Yalnız TOPLU İŞLEMİN yazdıkları sayılıyor.

        `taksonomi_kur` zaten bir yönlendirme kuruyor (`bursada-spor` →
        `bursa-da-spor`, F2 ölçütü (d)); toplam sayıya bakmak onu da
        sayardı ve test yanlış sebeple kırmızı olurdu.
        """
        self._gir("Yayın Yönetmeni")
        self._gonder("kategori", kategori_degeri=self.gundem.pk, onay="1")
        self.assertEqual(Yonlendirme.objects.filter(
            sebep="Kategori toplu işlemle değiştirildi.").count(), 0)

    # ------------------------------------------------------------------
    # 4. Sınırlar ve onay eşiği
    # ------------------------------------------------------------------

    def test_cok_alanli_istegi_django_kendisi_reddediyor(self):
        """Ölçülmüş davranış: açık kimlik kipinde ilk duvar bizim değil.

        `DATA_UPLOAD_MAX_NUMBER_FIELDS` varsayılanı 1000; 5.001 kimlik
        gönderen istek daha görünüme ulaşmadan **400** ile düşüyor. Yani
        `TOPLU_UST_SINIR` açık kimlik kipinde hiç devreye girmiyor —
        asıl işini "süzgeçteki tümü" kipinde yapıyor.
        """
        self._gir("Editör")
        yanit = self.client.post("/panel/toplu", {
            "fiil": "arsivle",
            "kimlikler": list(range(1, TOPLU_UST_SINIR + 2)),
        })
        self.assertEqual(yanit.status_code, 400)
        self.assertEqual(Haber.objects.filter(
            durum=Haber.DURUM_ARSIV).count(), 0)

    def test_ust_sinir_suzgec_kipinde_isliyor(self):
        """Üst sınırın gerçekten iş yaptığı yer burası.

        Sınır testte küçültülüyor; 5.000 kayıt üretmek testi dakikalarca
        sürdürürdü ve ölçülen şey sınırın kendisi, değeri değil.
        """
        from unittest import mock
        self._gir("Editör")
        with mock.patch("icerik.panel.TOPLU_UST_SINIR", 2):
            yanit = self.client.post("/panel/toplu", {
                "fiil": "arsivle", "tumu": "1",
                "suzgec": f"kategori={self.gundem.pk}",
            })
        self.assertEqual(yanit.status_code, 302)
        self.assertEqual(Haber.objects.filter(
            durum=Haber.DURUM_ARSIV).count(), 0)   # 4 kayıt > sınır 2

    def test_ust_sinir_altinda_suzgec_kipi_calisiyor(self):
        from unittest import mock
        self._gir("Editör")
        with mock.patch("icerik.panel.TOPLU_UST_SINIR", 10):
            self.client.post("/panel/toplu", {
                "fiil": "arsivle", "tumu": "1",
                "suzgec": f"kategori={self.gundem.pk}", "onay": "1",
            })
        self.assertEqual(Haber.objects.filter(
            durum=Haber.DURUM_ARSIV).count(), 4)

    def test_genis_secim_onay_istiyor(self):
        for sira in range(TOPLU_ONAY_ESIGI + 1):
            Haber.objects.create(
                id=970000 + sira, slug=f"genis-{sira}", baslik=f"Geniş {sira}",
                kategori=self.gundem, durum=Haber.DURUM_PASIF)
        genis = list(Haber.objects.filter(slug__startswith="genis-")
                     .values_list("pk", flat=True))
        self._gir("Editör")
        yanit = self.client.post("/panel/toplu",
                                 {"fiil": "arsivle", "kimlikler": genis})
        self.assertEqual(yanit.status_code, 200)
        self.assertTemplateUsed(yanit, "panel/toplu_onay.html")
        self.assertEqual(Haber.objects.filter(
            pk__in=genis, durum=Haber.DURUM_ARSIV).count(), 0)

        yanit = self.client.post("/panel/toplu", {
            "fiil": "arsivle", "kimlikler": genis, "onay": "1"})
        self.assertEqual(yanit.status_code, 302)
        self.assertEqual(Haber.objects.filter(
            pk__in=genis, durum=Haber.DURUM_ARSIV).count(), len(genis))

    def test_secim_yoksa_islem_yok(self):
        self._gir("Editör")
        yanit = self.client.post("/panel/toplu", {"fiil": "arsivle"})
        self.assertEqual(yanit.status_code, 302)
        self.assertEqual(Haber.objects.filter(
            durum=Haber.DURUM_ARSIV).count(), 0)

    def test_taninmayan_fiil_reddediliyor(self):
        self._gir("Yayın Yönetmeni")
        yanit = self.client.post("/panel/toplu", {
            "fiil": "her_seyi_sil", "kimlikler": self.kimlikler})
        self.assertEqual(yanit.status_code, 302)
        self.assertEqual(Haber.objects.filter(pk__in=self.kimlikler).count(), 4)

    def test_get_istegi_islem_yapmiyor(self):
        self._gir("Yayın Yönetmeni")
        yanit = self.client.get("/panel/toplu", {"fiil": "arsivle"})
        self.assertEqual(yanit.status_code, 302)
        self.assertEqual(Haber.objects.filter(
            durum=Haber.DURUM_ARSIV).count(), 0)

    def test_oturumsuz_toplu_islem_kapali(self):
        yanit = self.client.post("/panel/toplu", {
            "fiil": "arsivle", "kimlikler": self.kimlikler})
        self.assertEqual(yanit.status_code, 302)
        self.assertIn("/panel/giris", yanit["Location"])

    # ------------------------------------------------------------------
    # 5. "Süzgeçteki tümü" kipi — küme sunucuda yeniden kuruluyor
    # ------------------------------------------------------------------

    def test_tumu_kipi_suzgeci_sunucuda_yeniden_koşuyor(self):
        Haber.objects.filter(pk=self.kimlikler[0]).update(kategori=self.spor)
        self._gir("Editör")
        yanit = self.client.post("/panel/toplu", {
            "fiil": "arsivle", "tumu": "1",
            "suzgec": f"kategori={self.spor.pk}",
        })
        self.assertEqual(yanit.status_code, 302)
        # Yalnız süzgece uyan tek kayıt arşivlenmeli.
        self.assertEqual(Haber.objects.filter(
            durum=Haber.DURUM_ARSIV).count(), 1)
        self.assertEqual(Haber.objects.get(
            pk=self.kimlikler[0]).durum, Haber.DURUM_ARSIV)

    def test_tumu_kipi_istemciden_gelen_kimliklere_guvenmiyor(self):
        """İstemci hem `tumu` hem kimlik gönderse bile küme süzgeçten gelir."""
        Haber.objects.filter(pk=self.kimlikler[0]).update(kategori=self.spor)
        self._gir("Editör")
        self.client.post("/panel/toplu", {
            "fiil": "arsivle", "tumu": "1",
            "suzgec": f"kategori={self.spor.pk}",
            "kimlikler": self.kimlikler,        # yok sayılmalı
        })
        self.assertEqual(Haber.objects.filter(
            durum=Haber.DURUM_ARSIV).count(), 1)

    def test_silinmis_kayit_toplu_islemden_de_haric(self):
        Haber.objects.filter(pk=self.kimlikler[0]).update(
            durum=Haber.DURUM_SILINMIS)
        self._gir("Editör")
        self._gonder("arsivle")
        self.assertEqual(Haber.objects.get(
            pk=self.kimlikler[0]).durum, Haber.DURUM_SILINMIS)
        self.assertEqual(Haber.objects.filter(
            durum=Haber.DURUM_ARSIV).count(), 3)

    # ------------------------------------------------------------------
    # 6. Arayüz
    # ------------------------------------------------------------------

    def test_akis_ekraninda_secim_kutulari_ve_serit_var(self):
        self._gir("Yayın Yönetmeni")
        yanit = self.client.get("/panel/akis")
        self.assertContains(yanit, "data-toplu-kutu")
        self.assertContains(yanit, "data-toplu-hepsi")
        self.assertContains(yanit, "kayıt seçili")
        self.assertContains(yanit, "kaydın tamamını seç")

    def test_serit_suzgeci_tasiyor(self):
        self._gir("Yayın Yönetmeni")
        yanit = self.client.get("/panel/akis", {"kategori": self.spor.pk})
        self.assertEqual(yanit.context["toplu"]["suzgec"],
                         f"kategori={self.spor.pk}")

    def test_serit_suzgec_sayisini_dogru_veriyor(self):
        Haber.objects.filter(pk=self.kimlikler[0]).update(kategori=self.spor)
        self._gir("Yayın Yönetmeni")
        yanit = self.client.get("/panel/akis", {"kategori": self.spor.pk})
        self.assertEqual(yanit.context["toplu"]["suzgec_sayisi"], 1)

    def test_sonuc_duyurusu_basiliyor(self):
        self._gir("Editör")
        self._gonder("arsivle")
        yanit = self.client.get("/panel/akis")
        self.assertContains(yanit, "4 haber arşive alındı")
        self.assertContains(yanit, "duyuru gorunur")


class MedyaTopluIslem(TestCase):
    """Köşe, galeri ve video listelerinde toplu durum fiilleri.

    Akıştaki desenin aynısı, **daraltılmış fiil kümesiyle**: kategori
    değiştirme burada bilerek YOK. Galeri/video adres dilimini kategorinin
    tür satırı taşıyor (foto = +200, video = +300) ve taksonomide karşılığı
    olmayan dilimler var (`haber-213`); orada adres etkisi ayrı bir iş.
    """

    @classmethod
    def setUpTestData(cls):
        call_command("taksonomi_kur", verbosity=0)
        call_command("roller_kur", verbosity=0)
        cls.kullanicilar = {}
        for sira, rol in enumerate(("Muhabir", "Editör", "Sayfa Sekreteri",
                                    "İlan Sorumlusu", "Yayın Yönetmeni")):
            k = User.objects.create_user(f"m{sira}", password=PAROLA,
                                         first_name="Medya", last_name=str(sira))
            k.groups.add(Group.objects.get(name=rol))
            cls.kullanicilar[rol] = k
        cls.yazar = Yazar.objects.create(id=800, slug="toplu-yazar",
                                         ad="Toplu Yazar")
        cls.foto = KategoriTur.objects.filter(tur=Kategori.TUR_FOTO).first()
        cls.video_tur = KategoriTur.objects.filter(tur=Kategori.TUR_VIDEO).first()

    def setUp(self):
        simdi = timezone.now()
        self.kayitlar = {"kose": [], "galeri": [], "video": []}
        for sira in range(3):
            self.kayitlar["kose"].append(KoseYazisi.objects.create(
                id=810000 + sira, slug=f"tk-{sira}", baslik=f"Köşe {sira}",
                yazar=self.yazar, yayin_zamani=simdi))
            self.kayitlar["galeri"].append(FotoGaleri.objects.create(
                id=811000 + sira, slug=f"tg-{sira}", baslik=f"Galeri {sira}",
                kategori=self.foto.kategori,
                kategori_dilimi=self.foto.adres_dilimi, yayin_zamani=simdi))
            self.kayitlar["video"].append(Video.objects.create(
                id=812000 + sira, slug=f"tv-{sira}", baslik=f"Video {sira}",
                kategori=self.video_tur.kategori,
                kategori_dilimi=self.video_tur.adres_dilimi,
                yayin_zamani=simdi))
        self.modeller = {"kose": KoseYazisi, "galeri": FotoGaleri,
                         "video": Video}
        self.listeler = {"kose": "/panel/kose", "galeri": "/panel/galeriler",
                         "video": "/panel/videolar"}

    def _gir(self, rol):
        self.client.force_login(self.kullanicilar[rol])

    def _kimlikler(self, aile):
        return [k.pk for k in self.kayitlar[aile]]

    def test_fiil_yetkisi_her_aile_her_rol(self):
        beklenen = {
            "kose":   {"Editör", "Yayın Yönetmeni"},
            "galeri": {"Editör", "Sayfa Sekreteri", "Yayın Yönetmeni"},
            "video":  {"Editör", "Sayfa Sekreteri", "Yayın Yönetmeni"},
        }
        for aile, yetkililer in beklenen.items():
            for rol in self.kullanicilar:
                with self.subTest(aile=aile, rol=rol):
                    self._gir(rol)
                    yanit = self.client.post(f"/panel/toplu/{aile}", {
                        "fiil": "arsivle", "kimlikler": self._kimlikler(aile)})
                    if rol in yetkililer:
                        self.assertEqual(yanit.status_code, 302)
                    else:
                        self.assertEqual(yanit.status_code, 403)

    def test_muhabir_galeriyi_gorur_ama_arsivleyemez(self):
        """İki kapının ayrı olduğunu gösteren kalem.

        Muhabir `haber_girme` taşıdığı için galeri ekranını AÇAR, ama
        `haberi_arsivleme` taşımadığı için fiili uygulayamaz.
        """
        self._gir("Muhabir")
        self.assertEqual(self.client.get("/panel/galeriler").status_code, 200)
        yanit = self.client.post("/panel/toplu/galeri", {
            "fiil": "arsivle", "kimlikler": self._kimlikler("galeri")})
        self.assertEqual(yanit.status_code, 403)

    def test_muhabirde_serit_hic_cizilmiyor(self):
        self._gir("Muhabir")
        yanit = self.client.get("/panel/galeriler")
        self.assertIsNone(yanit.context["toplu"])
        self.assertNotContains(yanit, "data-toplu-kutu")

    def test_ilan_sorumlusu_ekrana_da_giremiyor(self):
        self._gir("İlan Sorumlusu")
        yanit = self.client.post("/panel/toplu/galeri", {
            "fiil": "arsivle", "kimlikler": self._kimlikler("galeri")})
        self.assertEqual(yanit.status_code, 403)

    def test_uc_ailede_de_durum_fiilleri_calisiyor(self):
        for aile in ("kose", "galeri", "video"):
            with self.subTest(aile=aile):
                model = self.modeller[aile]
                kimlikler = self._kimlikler(aile)
                self._gir("Yayın Yönetmeni")
                self.client.post(f"/panel/toplu/{aile}", {
                    "fiil": "yayindan_cek", "kimlikler": kimlikler})
                self.assertEqual(model.objects.filter(
                    pk__in=kimlikler, durum=model.DURUM_PASIF).count(), 3)
                self.client.post(f"/panel/toplu/{aile}", {
                    "fiil": "arsivle", "kimlikler": kimlikler})
                self.assertEqual(model.objects.filter(
                    pk__in=kimlikler, durum=model.DURUM_ARSIV).count(), 3)
                self.client.post(f"/panel/toplu/{aile}", {
                    "fiil": "yayina_al", "kimlikler": kimlikler})
                self.assertEqual(model.objects.filter(
                    pk__in=kimlikler, durum=model.DURUM_AKTIF).count(), 3)

    def test_yayin_zamani_bos_kayit_yayina_alinirken_doluyor(self):
        KoseYazisi.objects.filter(pk__in=self._kimlikler("kose")).update(
            yayin_zamani=None, durum=KoseYazisi.DURUM_PASIF)
        self._gir("Yayın Yönetmeni")
        self.client.post("/panel/toplu/kose", {
            "fiil": "yayina_al", "kimlikler": self._kimlikler("kose")})
        for kayit in KoseYazisi.objects.filter(pk__in=self._kimlikler("kose")):
            self.assertIsNotNone(kayit.yayin_zamani)
            self.assertEqual(kayit.durum, KoseYazisi.DURUM_AKTIF)

    def test_silinmis_kayit_toplu_islemden_haric(self):
        kimlikler = self._kimlikler("video")
        Video.objects.filter(pk=kimlikler[0]).update(durum=Video.DURUM_SILINMIS)
        self._gir("Yayın Yönetmeni")
        self.client.post("/panel/toplu/video", {
            "fiil": "arsivle", "kimlikler": kimlikler})
        self.assertEqual(Video.objects.get(pk=kimlikler[0]).durum,
                         Video.DURUM_SILINMIS)
        self.assertEqual(Video.objects.filter(
            pk__in=kimlikler, durum=Video.DURUM_ARSIV).count(), 2)

    def test_kategori_fiili_medyada_taninmiyor(self):
        self._gir("Yayın Yönetmeni")
        yanit = self.client.post("/panel/toplu/galeri", {
            "fiil": "kategori", "kimlikler": self._kimlikler("galeri"),
            "kategori_degeri": self.foto.kategori.pk})
        self.assertEqual(yanit.status_code, 302)
        for kayit in FotoGaleri.objects.filter(pk__in=self._kimlikler("galeri")):
            self.assertEqual(kayit.kategori_id, self.foto.kategori.pk)

    def test_kategori_dugmesi_medya_seridinde_gorunmuyor(self):
        self._gir("Yayın Yönetmeni")
        for yol in self.listeler.values():
            with self.subTest(yol=yol):
                yanit = self.client.get(yol)
                self.assertNotContains(yanit, "Kategori değiştir")
                self.assertNotContains(yanit, "Manşete al")
                self.assertContains(yanit, "Arşive al")

    def test_medya_seridinde_yalniz_durum_grubu_var(self):
        self._gir("Yayın Yönetmeni")
        yanit = self.client.get("/panel/kose")
        self.assertEqual(yanit.context["toplu"]["gruplar"], {"durum"})
        self.assertEqual(len(yanit.context["toplu"]["fiiller"]), 3)

    def test_bilinmeyen_aile_404(self):
        self._gir("Yayın Yönetmeni")
        yanit = self.client.post("/panel/toplu/yorumlar", {"fiil": "arsivle"})
        self.assertEqual(yanit.status_code, 404)

    def test_get_istegi_islem_yapmiyor(self):
        self._gir("Yayın Yönetmeni")
        yanit = self.client.get("/panel/toplu/kose", {"fiil": "arsivle"})
        self.assertEqual(yanit.status_code, 302)
        self.assertEqual(KoseYazisi.objects.filter(
            durum=KoseYazisi.DURUM_ARSIV).count(), 0)

    def test_oturumsuz_kapali(self):
        yanit = self.client.post("/panel/toplu/kose", {
            "fiil": "arsivle", "kimlikler": self._kimlikler("kose")})
        self.assertEqual(yanit.status_code, 302)
        self.assertIn("/panel/giris", yanit["Location"])

    def test_secim_yoksa_islem_yok(self):
        self._gir("Yayın Yönetmeni")
        self.client.post("/panel/toplu/kose", {"fiil": "arsivle"})
        self.assertEqual(KoseYazisi.objects.filter(
            durum=KoseYazisi.DURUM_ARSIV).count(), 0)

    def test_tumu_kipi_sunucuda_yeniden_suzuyor(self):
        kimlikler = self._kimlikler("kose")
        baska = Yazar.objects.create(id=801, slug="baska", ad="Başka Yazar")
        KoseYazisi.objects.filter(pk=kimlikler[0]).update(yazar=baska)
        self._gir("Yayın Yönetmeni")
        self.client.post("/panel/toplu/kose", {
            "fiil": "arsivle", "tumu": "1", "suzgec": f"yazar={baska.pk}",
            "kimlikler": kimlikler,
        })
        self.assertEqual(KoseYazisi.objects.filter(
            durum=KoseYazisi.DURUM_ARSIV).count(), 1)

    def test_ust_sinir_suzgec_kipinde_isliyor(self):
        from unittest import mock
        self._gir("Yayın Yönetmeni")
        with mock.patch("icerik.panel.TOPLU_UST_SINIR", 2):
            self.client.post("/panel/toplu/kose", {
                "fiil": "arsivle", "tumu": "1", "suzgec": ""})
        self.assertEqual(KoseYazisi.objects.filter(
            durum=KoseYazisi.DURUM_ARSIV).count(), 0)

    def test_genis_secim_onay_istiyor(self):
        from unittest import mock
        self._gir("Yayın Yönetmeni")
        with mock.patch("icerik.panel.TOPLU_ONAY_ESIGI", 1):
            yanit = self.client.post("/panel/toplu/kose", {
                "fiil": "arsivle", "kimlikler": self._kimlikler("kose")})
            self.assertEqual(yanit.status_code, 200)
            self.assertTemplateUsed(yanit, "panel/toplu_onay.html")
            self.assertEqual(KoseYazisi.objects.filter(
                durum=KoseYazisi.DURUM_ARSIV).count(), 0)
            yanit = self.client.post("/panel/toplu/kose", {
                "fiil": "arsivle", "kimlikler": self._kimlikler("kose"),
                "onay": "1"})
        self.assertEqual(yanit.status_code, 302)
        self.assertEqual(KoseYazisi.objects.filter(
            durum=KoseYazisi.DURUM_ARSIV).count(), 3)

    def test_sonuc_duyurusu_basiliyor(self):
        self._gir("Yayın Yönetmeni")
        self.client.post("/panel/toplu/video", {
            "fiil": "arsivle", "kimlikler": self._kimlikler("video")})
        yanit = self.client.get("/panel/videolar")
        self.assertContains(yanit, "3 kayıt arşive alındı")

    def test_form_hedefi_aileye_gore_kuruluyor(self):
        self._gir("Yayın Yönetmeni")
        for aile, yol in self.listeler.items():
            with self.subTest(aile=aile):
                yanit = self.client.get(yol)
                self.assertContains(yanit, f'action="/panel/toplu/{aile}"')
        yanit = self.client.get("/panel/akis")
        self.assertContains(yanit, 'action="/panel/toplu"')
