"""Model turu ekranları — PANEL-NOTLARI.md §24.

Dokuz yeni model, dokuz liste + dokuz düzenleme ekranı. Aynı disiplin:
her ekran doğrudan adresten çağrılıyor, çünkü **menüde bağlantının
görünmemesi yetki denetimi değildir**.

Yeni yetkilik açılmadı; her ekran §11'in 14 yetkiliğinden birine bağlı.
Testler o bağı satır satır kilitliyor.
"""

from django.contrib.auth.models import Group, User
from django.core.management import call_command
from django.db.models import ProtectedError
from django.test import TestCase
from django.utils import timezone

from taksonomi.models import Kategori, KategoriTur

from .models import (Bildirim, Gazete, Haber, IkiAdimli, LogKaydi,
                     ReklamKampanyasi, ReklamYuvasi, ResmiIlan, SonDakika,
                     Yorum)

PAROLA = "deneme-parola-123"

# Ekran → o ekrana girebilen roller. Yetkisiz rol 403 almalı.
EKRANLAR = {
    "/panel/yorumlar":     {"Editör", "Yayın Yönetmeni"},
    "/panel/bildirimler":  {"Sayfa Sekreteri", "Yayın Yönetmeni"},
    "/panel/son-dakika":   {"Sayfa Sekreteri", "Yayın Yönetmeni"},
    "/panel/ilanlar":      {"İlan Sorumlusu", "Yayın Yönetmeni"},
    "/panel/gazeteler":    {"İlan Sorumlusu", "Yayın Yönetmeni"},
    "/panel/yuvalar":      {"Sayfa Sekreteri", "Yayın Yönetmeni"},
    "/panel/kampanyalar":  {"İlan Sorumlusu", "Yayın Yönetmeni"},
    "/panel/log":          {"Yayın Yönetmeni"},
}


class ModelTuruTemel(TestCase):
    """Ortak kurulum: beş rol, birer örnek kayıt."""

    @classmethod
    def setUpTestData(cls):
        call_command("taksonomi_kur", verbosity=0)
        call_command("roller_kur", verbosity=0)
        cls.kategori = KategoriTur.objects.get(
            tur=Kategori.TUR_HABER, slug="gundem").kategori
        cls.kullanicilar = {}
        for sira, rol in enumerate(("Muhabir", "Editör", "Sayfa Sekreteri",
                                    "İlan Sorumlusu", "Yayın Yönetmeni")):
            k = User.objects.create_user(f"n{sira}", password=PAROLA,
                                         first_name="Model", last_name=str(sira))
            k.groups.add(Group.objects.get(name=rol))
            cls.kullanicilar[rol] = k
        cls.yonetmen = cls.kullanicilar["Yayın Yönetmeni"]

        simdi = timezone.now()
        cls.haber = Haber.objects.create(
            id=880001, slug="model-turu", baslik="Model turu haberi",
            kategori=cls.kategori, durum=Haber.DURUM_AKTIF, yayin_zamani=simdi)

        cls.yorum = Yorum.objects.create(
            icerik_turu=Yorum.TUR_HABER, icerik_id=cls.haber.pk,
            okur_adi="Okur Bir", metin="İlk yorum metni.", ip="10.0.0.1")
        cls.yuva = ReklamYuvasi.objects.create(
            ad="-Manşet yanı- 300x250", konum="Manşet yanı",
            genislik=300, yukseklik=250)
        cls.olcusuz_yuva = ReklamYuvasi.objects.create(
            ad="hakimiyet", konum="hakimiyet")
        cls.kampanya = ReklamKampanyasi.objects.create(
            baslik="Deneme kampanyası")
        cls.kampanya.yuvalar.add(cls.yuva)
        cls.gazete = Gazete.objects.create(
            ad="BURSA HAKİMİYET", bik_kodu="YYN-000132", bizim_mi=True)
        cls.ilan = ResmiIlan.objects.create(
            baslik="İhale ilanı", tur=ResmiIlan.TUR_IHALE,
            yayin_tarihi=timezone.localdate())
        cls.bildirim = Bildirim.objects.create(
            baslik="Deneme bildirimi", icerik_id=cls.haber.pk,
            hedef_sayisi=1000, acan_sayisi=25, gonderim_zamani=simdi)
        cls.son_dakika = SonDakika.objects.create(
            baslik="Son dakika bandı", haber=cls.haber)
        cls.log = LogKaydi.objects.create(
            kullanici=cls.yonetmen, fiil="yayina_alma", hedef_tur="haber",
            hedef_id=cls.haber.pk, oncesi={"durum": 2}, sonrasi={"durum": 1})

    def _gir(self, rol):
        self.client.force_login(self.kullanicilar[rol])


class ModelTuruErisim(ModelTuruTemel):

    def test_oturumsuz_hepsi_girise_yonleniyor(self):
        yollar = list(EKRANLAR) + [
            "/panel/iki-adimli",
            f"/panel/yorum/{self.yorum.pk}",
            f"/panel/yuva/{self.yuva.pk}",
            f"/panel/kampanya/{self.kampanya.pk}",
            f"/panel/gazete/{self.gazete.pk}",
            f"/panel/ilan/{self.ilan.pk}",
            f"/panel/bildirim/{self.bildirim.pk}",
            f"/panel/son-dakika/{self.son_dakika.pk}",
            f"/panel/log/{self.log.pk}",
        ]
        for yol in yollar:
            with self.subTest(yol=yol):
                yanit = self.client.get(yol)
                self.assertEqual(yanit.status_code, 302)
                self.assertIn("/panel/giris", yanit["Location"])

    def test_liste_ekranlari_yetkiye_gore(self):
        for yol, yetkililer in EKRANLAR.items():
            for rol in self.kullanicilar:
                with self.subTest(yol=yol, rol=rol):
                    self._gir(rol)
                    beklenen = 200 if rol in yetkililer else 403
                    self.assertEqual(self.client.get(yol).status_code, beklenen)

    def test_duzenleme_ekranlari_yetkiye_gore(self):
        beklenen = {
            f"/panel/yorum/{self.yorum.pk}": {"Editör", "Yayın Yönetmeni"},
            f"/panel/yuva/{self.yuva.pk}": {"Sayfa Sekreteri", "Yayın Yönetmeni"},
            f"/panel/kampanya/{self.kampanya.pk}": {"İlan Sorumlusu", "Yayın Yönetmeni"},
            f"/panel/gazete/{self.gazete.pk}": {"İlan Sorumlusu", "Yayın Yönetmeni"},
            f"/panel/ilan/{self.ilan.pk}": {"İlan Sorumlusu", "Yayın Yönetmeni"},
            f"/panel/bildirim/{self.bildirim.pk}": {"Sayfa Sekreteri", "Yayın Yönetmeni"},
            f"/panel/son-dakika/{self.son_dakika.pk}": {"Sayfa Sekreteri", "Yayın Yönetmeni"},
            f"/panel/log/{self.log.pk}": {"Yayın Yönetmeni"},
        }
        for yol, yetkililer in beklenen.items():
            for rol in self.kullanicilar:
                with self.subTest(yol=yol, rol=rol):
                    self._gir(rol)
                    kod = 200 if rol in yetkililer else 403
                    self.assertEqual(self.client.get(yol).status_code, kod)

    def test_iki_adimli_her_role_acik(self):
        """Yetkilik YOK, bilerek: herkes kendi hesabının durumunu görmeli."""
        for rol in self.kullanicilar:
            with self.subTest(rol=rol):
                self._gir(rol)
                self.assertEqual(
                    self.client.get("/panel/iki-adimli").status_code, 200)

    def test_yeni_yetkilik_acilmadi(self):
        """§11'in 14 yetkiliği ve 5×14 matrisi olduğu gibi durmalı."""
        from .yetkiler import MATRIS, OZEL_IZINLER, ROLLER
        self.assertEqual(len(OZEL_IZINLER), 14)
        self.assertEqual(len(ROLLER), 5)
        self.assertEqual(sum(len(v) for v in MATRIS.values()), 30)


class YorumEkrani(ModelTuruTemel):
    """§13'ün üç şartı: gerekçe zorunlu · iz görünür · özgün metin saklanır."""

    def test_liste_kayitlari_ve_sutunlari(self):
        self._gir("Editör")
        yanit = self.client.get("/panel/yorumlar")
        self.assertContains(yanit, "Okur Bir")
        for sutun in ("Yorum", "Yorumu yapan", "Sayfa tipi", "İçerik ID", "IP"):
            self.assertContains(yanit, sutun)
        self.assertIn("karar bekliyor", yanit.context["ust_bilgi"])

    def test_durum_enumu_uc_degerli(self):
        """Dökümde ölçüldü: yorumlarda Arşiv YOK (§9)."""
        self.assertEqual(len(Yorum.DURUMLAR), 3)
        adlar = [ad for _, ad in Yorum.DURUMLAR]
        self.assertEqual(adlar, ["Aktif", "Pasif", "Silinmiş"])
        self.assertNotIn("Arşiv", adlar)

    def test_suzgecler_daraltiyor(self):
        Yorum.objects.create(icerik_turu=Yorum.TUR_VIDEO, icerik_id=5,
                             okur_adi="Okur İki", metin="Video yorumu",
                             durum=Yorum.DURUM_AKTIF)
        self._gir("Editör")
        yanit = self.client.get("/panel/yorumlar", {"icerik_turu": "video"})
        self.assertEqual(yanit.context["sayfa"].paginator.count, 1)
        yanit = self.client.get("/panel/yorumlar", {"durum": Yorum.DURUM_AKTIF})
        self.assertEqual(yanit.context["sayfa"].paginator.count, 1)
        yanit = self.client.get("/panel/yorumlar", {"q": "İlk"})
        self.assertEqual(yanit.context["sayfa"].paginator.count, 1)

    def test_metin_degismeden_kaydedilebiliyor(self):
        self._gir("Editör")
        yanit = self.client.post(f"/panel/yorum/{self.yorum.pk}", {
            "okur_adi": "Okur Bir", "metin": "İlk yorum metni.",
            "durum": Yorum.DURUM_AKTIF, "duzenleme_gerekcesi": "",
        })
        self.assertEqual(yanit.status_code, 302)
        self.yorum.refresh_from_db()
        self.assertEqual(self.yorum.durum, Yorum.DURUM_AKTIF)
        self.assertFalse(self.yorum.duzenlendi_mi)

    def test_gerekcesiz_metin_degisikligi_reddediliyor(self):
        self._gir("Editör")
        yanit = self.client.post(f"/panel/yorum/{self.yorum.pk}", {
            "okur_adi": "Okur Bir", "metin": "Değiştirilmiş metin.",
            "durum": Yorum.DURUM_AKTIF, "duzenleme_gerekcesi": "",
        })
        self.assertEqual(yanit.status_code, 200)
        self.assertContains(yanit, "gerekçe zorunludur")
        self.yorum.refresh_from_db()
        self.assertEqual(self.yorum.metin, "İlk yorum metni.")

    def test_gerekceli_duzenleme_ozgun_metni_sakliyor(self):
        self._gir("Editör")
        yanit = self.client.post(f"/panel/yorum/{self.yorum.pk}", {
            "okur_adi": "Okur Bir", "metin": "Telefon numarası çıkarıldı.",
            "durum": Yorum.DURUM_AKTIF,
            "duzenleme_gerekcesi": "kişisel veri",
        })
        self.assertEqual(yanit.status_code, 302)
        self.yorum.refresh_from_db()
        self.assertEqual(self.yorum.metin, "Telefon numarası çıkarıldı.")
        self.assertTrue(self.yorum.duzenlendi_mi)
        self.assertEqual(self.yorum.ozgun_metin, "İlk yorum metni.")
        self.assertEqual(self.yorum.duzenleyen, self.kullanicilar["Editör"])

    def test_duzenlenmis_yorum_listede_isaretli(self):
        Yorum.objects.filter(pk=self.yorum.pk).update(duzenlendi_mi=True)
        self._gir("Editör")
        self.assertContains(self.client.get("/panel/yorumlar"), "Düzenlendi")


class LogEkrani(ModelTuruTemel):
    """§24.8'in beş zorunlu alanı ve salt okunurluk."""

    def test_bes_zorunlu_alan_kayitta(self):
        for alan in ("kullanici", "fiil", "hedef_tur", "hedef_id", "zaman",
                     "oncesi", "sonrasi"):
            with self.subTest(alan=alan):
                self.assertTrue(hasattr(self.log, alan))
        self.assertEqual(self.log.hedef_tur, "haber")
        self.assertEqual(self.log.hedef_id, self.haber.pk)
        self.assertEqual(self.log.oncesi, {"durum": 2})
        self.assertEqual(self.log.sonrasi, {"durum": 1})

    def test_kullanici_bagi_protect(self):
        """Hesap silinirse log okunamaz hâle gelirdi; PROTECT engelliyor."""
        with self.assertRaises(ProtectedError):
            self.yonetmen.delete()

    def test_detay_salt_okunur(self):
        """Düzenlenebilen log, log değildir: sayfada form yok."""
        self._gir("Yayın Yönetmeni")
        yanit = self.client.get(f"/panel/log/{self.log.pk}")
        self.assertEqual(yanit.status_code, 200)
        self.assertContains(yanit, "salt okunur")
        self.assertNotContains(yanit, "<form method=\"post\"")

    def test_oturum_kaydi_ayrimi(self):
        """Saklama süresi ayrımı: oturum 12 ay, eylem süresiz."""
        giris = LogKaydi.objects.create(kullanici=self.yonetmen, fiil="giris")
        self.assertTrue(giris.oturum_kaydi_mi)
        self.assertFalse(self.log.oturum_kaydi_mi)

    def test_hedefsiz_kayit_listede_isaretli(self):
        LogKaydi.objects.create(kullanici=self.yonetmen, fiil="giris")
        self._gir("Yayın Yönetmeni")
        yanit = self.client.get("/panel/log")
        satirlar = yanit.context["satirlar"]
        hedefsiz = [s for s in satirlar if s["hucreler"][3]["tur"] == "yok"]
        self.assertEqual(len(hedefsiz), 1)

    def test_fiil_suzgeci(self):
        LogKaydi.objects.create(kullanici=self.yonetmen, fiil="giris")
        self._gir("Yayın Yönetmeni")
        yanit = self.client.get("/panel/log", {"fiil": "giris"})
        self.assertEqual(yanit.context["sayfa"].paginator.count, 1)

    def test_fiil_kapali_liste(self):
        """Serbest metin olsaydı log aranamazdı."""
        kodlar = [k for k, _ in LogKaydi.FIILLER]
        self.assertIn("toplu_islem", kodlar)
        self.assertIn("kategori_degistirme", kodlar)
        self.assertIn("kaynak_birlestirme", kodlar)
        self.assertEqual(len(kodlar), len(set(kodlar)))

    def test_indeksler_bastan_kuruldu(self):
        """Tablo büyüdükten sonra indeks eklemek pahalı (Ö1)."""
        adlar = [tuple(i.fields) for i in LogKaydi._meta.indexes]
        self.assertIn(("hedef_tur", "hedef_id"), adlar)
        self.assertIn(("kullanici", "-zaman"), adlar)


class ReklamEkranlari(ModelTuruTemel):
    """F7(b): yuva = konum + ölçü + cihaz; reklamveren adı KAMPANYAYA yazılır."""

    def test_yuva_uc_alanli(self):
        for alan in ("konum", "genislik", "yukseklik", "cihaz"):
            self.assertTrue(hasattr(self.yuva, alan))
        self.assertEqual(self.yuva.olcu, "300x250")

    def test_olcusuz_yuva_uyariliyor(self):
        self._gir("Sayfa Sekreteri")
        yanit = self.client.get("/panel/yuvalar")
        self.assertIn("ölçüsü boş", yanit.context["uyari"])
        self.assertIn("yalnız 6", yanit.context["uyari"])

    def test_olcusuz_yuvanin_olcu_hucresi_bos_degil_isaretli(self):
        self._gir("Sayfa Sekreteri")
        yanit = self.client.get("/panel/yuvalar", {"q": "hakimiyet"})
        satir = yanit.context["satirlar"][0]
        self.assertEqual(satir["hucreler"][2]["tur"], "yok")

    def test_olcu_ya_tam_ya_hic(self):
        self._gir("Sayfa Sekreteri")
        yanit = self.client.post(f"/panel/yuva/{self.yuva.pk}", {
            "ad": self.yuva.ad, "konum": "Manşet yanı", "genislik": 300,
            "yukseklik": "", "cihaz": ReklamYuvasi.CIHAZ_HEPSI, "aktif": "on",
        })
        self.assertEqual(yanit.status_code, 200)
        self.assertContains(yanit, "ya tam verilmeli ya hiç")

    def test_yuva_kaydediliyor(self):
        self._gir("Sayfa Sekreteri")
        yanit = self.client.post(f"/panel/yuva/{self.olcusuz_yuva.pk}", {
            "ad": "hakimiyet", "konum": "Anasayfa üst", "genislik": 970,
            "yukseklik": 250, "cihaz": ReklamYuvasi.CIHAZ_MASAUSTU,
            "aktif": "on",
        })
        self.assertEqual(yanit.status_code, 302)
        self.olcusuz_yuva.refresh_from_db()
        self.assertEqual(self.olcusuz_yuva.olcu, "970x250")
        self.assertEqual(self.olcusuz_yuva.cihaz, ReklamYuvasi.CIHAZ_MASAUSTU)

    def test_kampanya_yuvaya_bagli(self):
        self._gir("İlan Sorumlusu")
        yanit = self.client.get("/panel/kampanyalar")
        self.assertContains(yanit, "Deneme kampanyası")
        self.assertContains(yanit, "-Manşet yanı- 300x250")

    def test_kampanya_tarih_sirasi_denetleniyor(self):
        self._gir("İlan Sorumlusu")
        yanit = self.client.post(f"/panel/kampanya/{self.kampanya.pk}", {
            "baslik": "Deneme kampanyası", "yuva": self.yuva.pk,
            "gorsel_dosya": "", "gorsel_alt": "", "hedef_adres": "",
            "baslangic": "2026-09-10", "bitis": "2026-09-01",
            "durum": ReklamKampanyasi.DURUM_AKTIF,
        })
        self.assertEqual(yanit.status_code, 200)
        self.assertContains(yanit, "başlangıçtan önce olamaz")

    def test_kampanya_kaydediliyor(self):
        self._gir("İlan Sorumlusu")
        yanit = self.client.post(f"/panel/kampanya/{self.kampanya.pk}", {
            "baslik": "Güncellenen kampanya", "yuvalar": [self.yuva.pk],
            "gorsel_dosya": "reklam/ornek.jpg", "gorsel_alt": "Örnek",
            "hedef_adres": "https://ornek.example/",
            "baslangic": "2026-09-01", "bitis": "2026-09-30",
            "durum": ReklamKampanyasi.DURUM_AKTIF,
        })
        self.assertEqual(yanit.status_code, 302)
        self.kampanya.refresh_from_db()
        self.assertEqual(self.kampanya.baslik, "Güncellenen kampanya")

    def test_yuva_silinemez_kampanya_varken(self):
        """PROTECT: yuva silinirse kampanya sahipsiz kalırdı.

        Bağ çoka çok olduktan sonra da geçerli: koruma `KampanyaYuva` ara
        modelindeki `on_delete=PROTECT` ile taşınıyor.
        """
        with self.assertRaises(ProtectedError):
            self.yuva.delete()

    def test_kampanya_birden_cok_yuvada_olabiliyor(self):
        """Ölçüm: dökümdeki 25 kampanyanın 8'i çok yuvalı."""
        self.kampanya.yuvalar.add(self.olcusuz_yuva)
        self.assertEqual(self.kampanya.yuvalar.count(), 2)
        self.assertEqual(self.yuva.kampanyalar.count(), 1)


class GazeteVeIlanEkranlari(ModelTuruTemel):

    def test_gazete_listesi_bik_kodunu_gosteriyor(self):
        self._gir("İlan Sorumlusu")
        yanit = self.client.get("/panel/gazeteler")
        self.assertContains(yanit, "YYN-000132")
        self.assertContains(yanit, "Bizim")

    def test_gazete_kaydediliyor(self):
        self._gir("İlan Sorumlusu")
        yanit = self.client.post(f"/panel/gazete/{self.gazete.pk}", {
            "ad": "BURSA HAKİMİYET", "bik_kodu": "YYN-000132", "sira": 1,
            "aktif": "on", "bizim_mi": "on",
        })
        self.assertEqual(yanit.status_code, 302)
        self.gazete.refresh_from_db()
        self.assertEqual(self.gazete.sira, 1)

    def test_ilan_turleri_dortlu(self):
        """Dört tür yasal karşılığı olduğu için korunuyor (§16)."""
        adlar = [ad for _, ad in ResmiIlan.TURLER]
        self.assertEqual(adlar, ["İCRA", "İHALE", "TEBLİGAT", "PERSONEL ALIMI"])

    def test_ilan_listesi_ve_tur_suzgeci(self):
        ResmiIlan.objects.create(baslik="Tebligat ilanı",
                                 tur=ResmiIlan.TUR_TEBLIGAT)
        self._gir("İlan Sorumlusu")
        yanit = self.client.get("/panel/ilanlar")
        self.assertEqual(yanit.context["sayfa"].paginator.count, 2)
        yanit = self.client.get("/panel/ilanlar", {"tur": ResmiIlan.TUR_TEBLIGAT})
        self.assertEqual(yanit.context["sayfa"].paginator.count, 1)

    def test_ilan_kaydediliyor_ve_gazeteye_baglanabiliyor(self):
        self._gir("İlan Sorumlusu")
        yanit = self.client.post(f"/panel/ilan/{self.ilan.pk}", {
            "baslik": "İhale ilanı — güncel", "tur": ResmiIlan.TUR_IHALE,
            "metin": "İlan metni.", "yayin_tarihi": "2026-08-28",
            "bitis_tarihi": "", "bik_kodu": "BIK-1", "gazete": self.gazete.pk,
            "durum": ResmiIlan.DURUM_AKTIF,
        })
        self.assertEqual(yanit.status_code, 302)
        self.ilan.refresh_from_db()
        self.assertEqual(self.ilan.gazete, self.gazete)

    def test_alan_sozlesmesinin_olculemedigi_yazili(self):
        self._gir("İlan Sorumlusu")
        yanit = self.client.get("/panel/ilanlar")
        notlar = " ".join(yanit.context["notlar"])
        self.assertIn("ÖLÇÜLEMEDİ", notlar)


class BildirimEkrani(ModelTuruTemel):
    """§13: oran türetilir, başlık 50 karakter, içerik şart."""

    def test_oran_saklanmiyor_turetiliyor(self):
        self.assertAlmostEqual(self.bildirim.acilma_orani, 2.5, places=2)
        alanlar = {a.name for a in Bildirim._meta.get_fields()}
        self.assertNotIn("acilma_orani", alanlar)

    def test_hedef_sifirsa_oran_sifir(self):
        b = Bildirim.objects.create(baslik="Gönderilmedi", icerik_id=1)
        self.assertEqual(b.acilma_orani, 0.0)

    def test_liste_ortalama_orani_gosteriyor(self):
        self._gir("Sayfa Sekreteri")
        yanit = self.client.get("/panel/bildirimler")
        self.assertIn("Ortalama açılma oranı", yanit.context["ust_bilgi"])

    def test_gonderilmemis_bildirim_isaretli(self):
        Bildirim.objects.create(baslik="Gönderilmedi", icerik_id=1)
        self._gir("Sayfa Sekreteri")
        yanit = self.client.get("/panel/bildirimler", {"q": "Gönderilmedi"})
        satir = yanit.context["satirlar"][0]
        self.assertEqual(satir["hucreler"][5]["tur"], "yok")

    def test_baslik_sinirini_asamaz(self):
        self._gir("Sayfa Sekreteri")
        yanit = self.client.post(f"/panel/bildirim/{self.bildirim.pk}", {
            "baslik": "x" * 60, "icerik_turu": "haber",
            "icerik_id": self.haber.pk, "hedef_sayisi": 10, "acan_sayisi": 1,
        })
        self.assertEqual(yanit.status_code, 200)
        self.assertTrue(yanit.context["form"].errors)

    def test_iceriksiz_bildirim_kaydedilemiyor(self):
        self._gir("Sayfa Sekreteri")
        yanit = self.client.post(f"/panel/bildirim/{self.bildirim.pk}", {
            "baslik": "İçeriksiz", "icerik_turu": "haber", "icerik_id": "",
            "hedef_sayisi": 10, "acan_sayisi": 1,
        })
        self.assertEqual(yanit.status_code, 200)
        self.assertContains(yanit, "İçerik seçilmeden")

    def test_bildirim_kaydediliyor(self):
        self._gir("Sayfa Sekreteri")
        yanit = self.client.post(f"/panel/bildirim/{self.bildirim.pk}", {
            "baslik": "Güncel bildirim", "icerik_turu": "haber",
            "icerik_id": self.haber.pk, "hedef_sayisi": 2000,
            "acan_sayisi": 40,
        })
        self.assertEqual(yanit.status_code, 302)
        self.bildirim.refresh_from_db()
        self.assertAlmostEqual(self.bildirim.acilma_orani, 2.0, places=2)


class SonDakikaEkrani(ModelTuruTemel):
    """§24.2: ayrı model, haberde bayrak değil."""

    def test_haberde_bayrak_alani_acilmadi(self):
        """`icerik_haber`e bayrak eklemek 356 binde ~34 sn'lik yeniden kurma."""
        alanlar = {a.name for a in Haber._meta.get_fields()}
        self.assertNotIn("son_dakika", alanlar)
        self.assertNotIn("son_dakika_mi", alanlar)

    def test_serbest_adres_habere_ustun(self):
        self.son_dakika.adres = "https://disardan.example/haber"
        self.son_dakika.save()
        self.assertEqual(self.son_dakika.yol, "https://disardan.example/haber")

    def test_adressiz_ve_habersiz_kayit_reddediliyor(self):
        self._gir("Sayfa Sekreteri")
        yanit = self.client.post(f"/panel/son-dakika/{self.son_dakika.pk}", {
            "baslik": "Boş", "adres": "", "haber": "",
            "baslangic": "2026-08-28 10:00:00", "bitis": "", "sira": 0,
            "aktif": "on",
        })
        self.assertEqual(yanit.status_code, 200)
        self.assertContains(yanit, "tıklanamayan kayıt olmamalı")

    def test_bandakiler_bitis_tarihine_bakiyor(self):
        import datetime
        gecmis = SonDakika.objects.create(
            baslik="Süresi dolmuş", adres="/x",
            baslangic=timezone.now() - datetime.timedelta(days=2),
            bitis=timezone.now() - datetime.timedelta(days=1))
        bantta = list(SonDakika.bandakiler())
        self.assertIn(self.son_dakika, bantta)
        self.assertNotIn(gecmis, bantta)

    def test_liste_bantta_sayisini_veriyor(self):
        self._gir("Sayfa Sekreteri")
        yanit = self.client.get("/panel/son-dakika")
        self.assertIn("bantta görünen kayıt: 1", yanit.context["ust_bilgi"])

    def test_kaydediliyor(self):
        self._gir("Sayfa Sekreteri")
        yanit = self.client.post(f"/panel/son-dakika/{self.son_dakika.pk}", {
            "baslik": "Güncel bant", "adres": "/gundem/x-1", "haber": "",
            "baslangic": "2026-08-28 10:00:00", "bitis": "", "sira": 3,
            "aktif": "on",
        })
        self.assertEqual(yanit.status_code, 302)
        self.son_dakika.refresh_from_db()
        self.assertEqual(self.son_dakika.sira, 3)
        self.assertEqual(self.son_dakika.yol, "/gundem/x-1")


class IkiAdimliEkrani(ModelTuruTemel):
    """§24.10: model var, KURULUM AKIŞI bilerek yok."""

    def test_gizli_anahtari_dolduran_form_yok(self):
        self._gir("Yayın Yönetmeni")
        yanit = self.client.get("/panel/iki-adimli")
        self.assertNotIn("form", yanit.context)
        self.assertNotContains(yanit, 'name="gizli_anahtar"')

    def test_ekran_neden_acilmadigini_soyluyor(self):
        self._gir("Yayın Yönetmeni")
        yanit = self.client.get("/panel/iki-adimli")
        self.assertContains(yanit, "Kurulum akışı henüz açılmadı")
        self.assertContains(yanit, "yarım bir")

    def test_zorunlu_rol_isareti(self):
        self._gir("Yayın Yönetmeni")
        self.assertTrue(self.client.get("/panel/iki-adimli").context["zorunlu_mu"])
        self._gir("Muhabir")
        self.assertFalse(self.client.get("/panel/iki-adimli").context["zorunlu_mu"])

    def test_kurulu_mu_anahtarsiz_yanlis(self):
        kayit = IkiAdimli.objects.create(kullanici=self.yonetmen,
                                         dogrulandi_mi=True)
        self.assertFalse(kayit.kurulu_mu)

    def test_iki_yontem_tanimli(self):
        adlar = [ad for _, ad in IkiAdimli.YONTEMLER]
        self.assertEqual(adlar, ["Google Authenticator", "SMS"])


class MenuVeIndeks(ModelTuruTemel):

    def test_menu_yetkiye_gore_kisiliyor(self):
        beklenen = {
            "Muhabir": {"gorunur": ["/panel/iki-adimli"],
                        "gorunmez": ["/panel/yorumlar", "/panel/ilanlar",
                                     "/panel/log", "/panel/yuvalar"]},
            "Editör": {"gorunur": ["/panel/yorumlar"],
                       "gorunmez": ["/panel/ilanlar", "/panel/log",
                                    "/panel/yuvalar"]},
            "Sayfa Sekreteri": {"gorunur": ["/panel/yuvalar",
                                            "/panel/bildirimler",
                                            "/panel/son-dakika"],
                                "gorunmez": ["/panel/yorumlar", "/panel/log"]},
            "İlan Sorumlusu": {"gorunur": ["/panel/ilanlar", "/panel/gazeteler",
                                           "/panel/kampanyalar"],
                               "gorunmez": ["/panel/yorumlar", "/panel/log"]},
            "Yayın Yönetmeni": {"gorunur": ["/panel/yorumlar", "/panel/ilanlar",
                                            "/panel/log", "/panel/yuvalar"],
                                "gorunmez": []},
        }
        for rol, kume in beklenen.items():
            self._gir(rol)
            yanit = self.client.get("/panel/")
            for yol in kume["gorunur"]:
                with self.subTest(rol=rol, yol=yol, bekle="gorunur"):
                    self.assertContains(yanit, yol)
            for yol in kume["gorunmez"]:
                with self.subTest(rol=rol, yol=yol, bekle="gorunmez"):
                    self.assertNotContains(yanit, yol)

    def test_haber_ilce_indeksi_eklendi(self):
        adlar = [tuple(i.fields) for i in Haber._meta.indexes]
        self.assertIn(("ilce", "-yayin_zamani"), adlar)

    def test_panel_yollari_site_kaliplarini_golgelemedi(self):
        from django.urls import resolve
        self.assertEqual(resolve("/panel/yorumlar").url_name, "panel-yorumlar")
        self.assertEqual(resolve("/panel/log").url_name, "panel-log")
        self.assertEqual(resolve("/gundem").url_name, "kategori")
