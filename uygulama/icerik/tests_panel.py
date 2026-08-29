"""Panel tarafı gerileme testleri — rol matrisi ve alan sözleşmesi.

İki belgeye bağlı:
  - `PANEL-NOTLARI.md` §11 — 5 rol × 14 yetkilik matrisi
  - `PANEL-NOTLARI.md` §4  — 31 satırlık alan sözleşmesi

Alan sözleşmesinin can alıcı noktası şuydu: mevcut panelde `summery`,
`tagElementName` ve `articleAuthor` alanları kırmızı yıldızlı görünüyor ama
`formControl` muafiyet listesinde oldukları için **boş kaydedilebiliyordu**.
Bu dosya o yalanın geri gelmediğini ölçer.
"""

from django.contrib.auth.models import Group, User
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from taksonomi.models import Etiket, Kategori, KategoriTur, Yonlendirme

from .formlar import (BASLIK_SINIR, SPOT_SINIR, HaberForm,
                      etiketleri_kur)
from .models import Haber
from .yetkiler import ROLLER, rolun_yetkileri


def _rollu_kullanici(ad: str, rol: str) -> User:
    kullanici = User.objects.create_user(ad)
    kullanici.groups.add(Group.objects.get(name=rol))
    # Django izinleri örnek üzerinde önbelleğe alır; taze örnek gerekiyor.
    return User.objects.get(pk=kullanici.pk)


class RolMatrisi(TestCase):
    """PANEL-NOTLARI.md §11."""

    @classmethod
    def setUpTestData(cls):
        call_command("roller_kur", verbosity=0)

    def test_bes_rol_kuruldu(self):
        for rol in ROLLER:
            with self.subTest(rol=rol):
                self.assertTrue(Group.objects.filter(name=rol).exists())

    def test_her_rolun_yetki_sayisi_matrisle_ayni(self):
        for rol in ROLLER:
            with self.subTest(rol=rol):
                self.assertEqual(Group.objects.get(name=rol).permissions.count(),
                                 len(rolun_yetkileri(rol)))

    def test_muhabir_yayinlayamaz(self):
        """§11'in en kritik satırı: sahadan giren haber masada yayına alınır."""
        kullanici = _rollu_kullanici("muhabir1", "Muhabir")
        self.assertTrue(kullanici.has_perm("icerik.haber_girme"))
        self.assertFalse(kullanici.has_perm("icerik.kendi_haberini_yayinlama"))
        self.assertFalse(kullanici.has_perm("icerik.baskasinin_haberini_yayinlama"))
        self.assertFalse(kullanici.has_perm("icerik.mansete_alma"))

    def test_taksonomi_yalniz_yayin_yonetmeninde(self):
        """Kategori slug'ı 556.824 adresin parçası; günlük yetkiye bırakılamaz."""
        for rol in ROLLER:
            with self.subTest(rol=rol):
                k = _rollu_kullanici(f"t-{rol}", rol)
                self.assertEqual(k.has_perm("icerik.taksonomi_duzenleme"),
                                 rol == "Yayın Yönetmeni")

    def test_manset_yalniz_sekreter_ve_yonetmende(self):
        for rol in ROLLER:
            with self.subTest(rol=rol):
                k = _rollu_kullanici(f"m-{rol}", rol)
                self.assertEqual(k.has_perm("icerik.mansete_alma"),
                                 rol in ("Sayfa Sekreteri", "Yayın Yönetmeni"))

    def test_resmi_ilan_yalniz_ilan_sorumlusu_ve_yonetmende(self):
        """BİK yükümlülüğü taşır, yasal sonuç doğurur."""
        for rol in ROLLER:
            with self.subTest(rol=rol):
                k = _rollu_kullanici(f"i-{rol}", rol)
                self.assertEqual(k.has_perm("icerik.resmi_ilan_girme"),
                                 rol in ("İlan Sorumlusu", "Yayın Yönetmeni"))

    def test_ilan_sorumlusu_haber_giremez(self):
        k = _rollu_kullanici("ilan1", "İlan Sorumlusu")
        self.assertFalse(k.has_perm("icerik.haber_girme"))


class HaberFormuAlanSozlesmesi(TestCase):
    """PANEL-NOTLARI.md §4 — satır satır."""

    @classmethod
    def setUpTestData(cls):
        call_command("taksonomi_kur", verbosity=0)
        cls.kategori = KategoriTur.objects.get(
            tur=Kategori.TUR_HABER, slug="gundem").kategori
        cls.etiket = Etiket.objects.create(ad="Bursa gündemi", slug="bursa-gundemi")

    def _veri(self, **ek):
        temel = {
            "baslik": "Kısa bir başlık",
            "spot": "Kısa bir spot metni.",
            "govde": "<p>Birinci paragraf.</p><p>İkinci paragraf.</p>",
            "kategori": self.kategori.pk,
            "etiketler": self.etiket.ad,
            "durum": Haber.DURUM_AKTIF,
            "hazirlik": "hazir",
            "kaynak_turu": Haber.KAYNAK_AJANS,
            "yayin_zamani": timezone.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        temel.update(ek)
        return temel

    # --- alan 2: başlık ---
    def test_baslik_zorunlu(self):
        form = HaberForm(data=self._veri(baslik=""))
        self.assertFalse(form.is_valid())
        self.assertIn("baslik", form.errors)

    def test_baslik_sinirini_asamaz(self):
        form = HaberForm(data=self._veri(baslik="x" * (BASLIK_SINIR + 1)))
        self.assertFalse(form.is_valid())
        self.assertIn("baslik", form.errors)

    # --- alan 4: spot — "gerçekten zorunlu yapıldı" ---
    def test_spot_yayina_alirken_zorunlu(self):
        form = HaberForm(data=self._veri(spot=""))
        self.assertFalse(form.is_valid())
        self.assertIn("spot", str(form.errors))

    def test_spot_sinirini_asamaz(self):
        form = HaberForm(data=self._veri(spot="x" * (SPOT_SINIR + 1)))
        self.assertFalse(form.is_valid())
        self.assertIn("spot", form.errors)

    # --- alan 5: gövde — en az iki paragraf ---
    def test_govde_tek_paragrafla_yayinlanamaz(self):
        form = HaberForm(data=self._veri(govde="<p>Tek paragraf.</p>"))
        self.assertFalse(form.is_valid())
        self.assertIn("paragraf", str(form.errors))

    def test_govde_duz_metin_paragraflari_sayiliyor(self):
        form = HaberForm(data=self._veri(govde="Birinci paragraf.\n\nİkinci paragraf."))
        self.assertTrue(form.is_valid(), form.errors)

    # --- alan 7: etiket — "gerçekten zorunlu yapıldı" ---
    def test_etiketsiz_yayinlanamaz(self):
        form = HaberForm(data=self._veri(etiketler=[]))
        self.assertFalse(form.is_valid())
        self.assertIn("etiket", str(form.errors))

    # --- taslak eşiği ---
    def test_taslak_eksik_alanlarla_kaydedilebilir(self):
        """Muhabir yarım işi kaydedebilmeli; yoksa §11'deki 'muhabir
        yayınlayamaz' kuralı 'muhabir hiçbir şey kaydedemez'e dönerdi."""
        form = HaberForm(data=self._veri(
            spot="", govde="", etiketler=[],
            durum=Haber.DURUM_PASIF, hazirlik="taslak"))
        self.assertTrue(form.is_valid(), form.errors)

    def test_taslak_basliksiz_kaydedilemez(self):
        form = HaberForm(data=self._veri(
            baslik="", durum=Haber.DURUM_PASIF, hazirlik="taslak"))
        self.assertFalse(form.is_valid())

    # --- alan 16-17: kaynak türü ve meta yazar türetimi (§7) ---
    def test_meta_yazar_kaynak_turunden_turetiliyor(self):
        for tur, beklenen in ((Haber.KAYNAK_AJANS, "haber_ajansi"),
                              (Haber.KAYNAK_DIS_YAYIN, "alinti"),
                              (Haber.KAYNAK_MUHABIR, "fikir_iscisi")):
            with self.subTest(tur=tur):
                haber = Haber(id=810000 + hash(tur) % 900, slug="x", baslik="X",
                              kategori=self.kategori, kaynak_turu=tur)
                haber.save()
                self.assertEqual(haber.meta_yazar, beklenen)

    def test_elle_secilen_meta_yazar_turetimle_ezilmiyor(self):
        haber = Haber(id=810004, slug="x", baslik="X", kategori=self.kategori,
                      kaynak_turu=Haber.KAYNAK_AJANS,
                      meta_yazar="bulten", meta_yazar_elle=True)
        haber.save()
        self.assertEqual(haber.meta_yazar, "bulten")

    # --- §25: kaynak türü ölçülemediyse ölçülmüş meta yazar korunur ---
    def test_bos_kaynak_turu_olculmus_meta_yazari_ezmiyor(self):
        """Arşivden gelen 337 bin kaydın davranışı.

        Bu kayıtlarda kaynak türü hiç kaydedilmemiş; meta yazar ise arşivin
        `kaynak` alanından ÖLÇÜLDÜ. Panelden bir kaydetme ölçümü ezerse
        kurtarılan bilgi geri kaybolur.
        """
        for meta in ("haber_merkezi", "bulten"):
            with self.subTest(meta=meta):
                haber = Haber(id=810100 + len(meta), slug="x", baslik="X",
                              kategori=self.kategori, kaynak_turu="",
                              meta_yazar=meta)
                haber.save()
                haber.refresh_from_db()
                self.assertEqual(haber.meta_yazar, meta)

    def test_bos_kaynak_turu_bos_meta_yazarda_haber_merkezine_duser(self):
        haber = Haber(id=810110, slug="x", baslik="X", kategori=self.kategori,
                      kaynak_turu="", meta_yazar="")
        haber.save()
        self.assertEqual(haber.meta_yazar, "haber_merkezi")

    def test_kaynak_turu_bos_birakilabiliyor(self):
        form = HaberForm(data=self._veri(kaynak_turu="", muhabir=""))
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(
            form.fields["kaynak_turu"].choices[0], ("", "Belirtilmemiş"))

    # --- etiket alanı: boş tablo yüzünden görünmüyordu (29 Ağustos) ---
    def test_etiket_yazilarak_aciliyor(self):
        """Etiket tablosu boştu; seçilecek bir şey olmayınca alan çiziliyordu
        ama görünmüyordu ve hiçbir haber yayına alınamıyordu."""
        Etiket.objects.all().delete()
        form = HaberForm(data=self._veri(etiketler="Nilüfer Çayı, baraj"))
        self.assertTrue(form.is_valid(), form.errors)
        haber = form.save(commit=False)
        haber.id, haber.slug = 810200, "x"
        haber.save()
        form.save_m2m()
        self.assertEqual(
            sorted(haber.etiketler.values_list("ad", flat=True)),
            ["Nilüfer Çayı", "baraj"])

    def test_ayni_etiket_buyuk_kucuk_harfle_tekrarlanmiyor(self):
        form = HaberForm(data=self._veri(etiketler="BURSA, bursa, Bursa"))
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["etiketler"], ["BURSA"])

    def test_etiket_slugu_turkce_harfi_atmiyor(self):
        """Django `slugify`'ı Türkçe harfi çevirmez, ATAR: Şehreküstü→ehrekst."""
        Etiket.objects.all().delete()
        etiketleri_kur(["Şehreküstü"])
        self.assertEqual(Etiket.objects.get().slug, "sehrekustu")

    def test_gecersiz_formda_etiket_kaydi_acilmiyor(self):
        """Kayıt açma doğrulamada olsaydı öksüz etiket kalırdı."""
        Etiket.objects.all().delete()
        form = HaberForm(data=self._veri(baslik="", etiketler="yeni etiket"))
        self.assertFalse(form.is_valid())
        self.assertEqual(Etiket.objects.count(), 0)

    def test_cok_etiket_reddediliyor(self):
        form = HaberForm(data=self._veri(
            etiketler=", ".join(f"etiket{i}" for i in range(25))))
        self.assertFalse(form.is_valid())
        self.assertIn("etiketler", form.errors)

    def test_duzenlemede_mevcut_etiketler_metin_olarak_geliyor(self):
        haber = Haber.objects.create(id=810210, slug="x", baslik="X",
                                     kategori=self.kategori)
        haber.etiketler.set(etiketleri_kur(["baraj", "meclis"]))
        form = HaberForm(instance=haber)
        self.assertEqual(form.initial["etiketler"], "baraj, meclis")

    def test_muhabir_secildiyse_ad_zorunlu(self):
        form = HaberForm(data=self._veri(kaynak_turu=Haber.KAYNAK_MUHABIR, muhabir=""))
        self.assertFalse(form.is_valid())
        self.assertIn("muhabir", form.errors)

    # --- §11: manşet yetkisi forma yansıyor ---
    def test_manset_kutulari_yetkiye_bagli(self):
        call_command("roller_kur", verbosity=0)
        muhabir = _rollu_kullanici("mform", "Muhabir")
        form = HaberForm(kullanici=muhabir)
        for ad in ("manset_ana", "manset_tepe", "manset_kare"):
            self.assertNotIn(ad, form.fields)

        sekreter = _rollu_kullanici("sform", "Sayfa Sekreteri")
        self.assertIn("manset_ana", HaberForm(kullanici=sekreter).fields)

    # --- alan 32 / §9: hazırlık ekseni ---
    def test_hazirlik_bos_gelirse_taslak(self):
        haber = Haber(id=810005, slug="x", baslik="X", kategori=self.kategori)
        haber.save()
        self.assertEqual(haber.hazirlik, "taslak")

    def test_masadakiler_kuyrugu(self):
        """Bugün ekranının kuyruğu = Pasif ve (Taslak | İncelemede)."""
        Haber.objects.create(id=811001, slug="a", baslik="A", kategori=self.kategori,
                             durum=Haber.DURUM_PASIF, hazirlik="taslak")
        Haber.objects.create(id=811002, slug="b", baslik="B", kategori=self.kategori,
                             durum=Haber.DURUM_PASIF, hazirlik="incelemede")
        Haber.objects.create(id=811003, slug="c", baslik="C", kategori=self.kategori,
                             durum=Haber.DURUM_PASIF, hazirlik="hazir")
        Haber.objects.create(id=811004, slug="d", baslik="D", kategori=self.kategori,
                             durum=Haber.DURUM_AKTIF, hazirlik="taslak")
        self.assertEqual(set(Haber.masadakiler().values_list("id", flat=True)),
                         {811001, 811002})

    # --- alan 12: kategori adresi belirler ---
    def test_kategori_degisimi_yonlendirme_yaziyor(self):
        haber = Haber.objects.create(
            id=812001, slug="bir-haber", baslik="Bir haber",
            kategori=self.kategori, durum=Haber.DURUM_PASIF, hazirlik="taslak")
        spor = KategoriTur.objects.get(tur=Kategori.TUR_HABER, slug="spor").kategori
        form = HaberForm(data=self._veri(kategori=spor.pk, baslik="Bir haber"),
                         instance=haber)
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        kayit = Yonlendirme.objects.filter(eski_yol="/gundem/bir-haber-812001").first()
        self.assertIsNotNone(kayit)
        self.assertEqual(kayit.yeni_yol, "/spor/bir-haber-812001")
        self.assertEqual(kayit.kod, 301)

    def test_kategori_degismezse_yonlendirme_yazilmiyor(self):
        haber = Haber.objects.create(
            id=812002, slug="ayni", baslik="Aynı", kategori=self.kategori,
            durum=Haber.DURUM_PASIF, hazirlik="taslak")
        form = HaberForm(data=self._veri(baslik="Aynı"), instance=haber)
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        self.assertFalse(
            Yonlendirme.objects.filter(eski_yol__contains="ayni-812002").exists())

    # --- olusturan alanı: "kendi haberini yayınlama" buna bakacak ---
    def test_olusturan_formu_dolduran_kullanici(self):
        call_command("roller_kur", verbosity=0)
        muhabir = _rollu_kullanici("yazan", "Muhabir")
        form = HaberForm(data=self._veri(
            durum=Haber.DURUM_PASIF, hazirlik="taslak"), kullanici=muhabir)
        self.assertTrue(form.is_valid(), form.errors)
        haber = form.save(commit=False)
        haber.id = 813001
        haber.slug = "yazilan"
        form.instance.id = 813001
        form.instance.slug = "yazilan"
        haber = form.save()
        self.assertEqual(haber.olusturan_id, muhabir.pk)
