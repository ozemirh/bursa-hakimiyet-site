"""Tek yayın kapısı — `icerik/yayin_kapisi.py` (Paket F madde 2).

Gerileme matrisi: muhabir × (ekle, düzenle, toplu, yapay zekâ taslağı).
Değerlendirmede (DEGERLENDIRME-2026-10 §3 bulgu 4) muhabirin "Haber ekle"
formunda `durum=Aktif` gönderip haberi doğrudan yayına aldığı doğrulanmıştı;
toplu "Yayına al" da `[yazılacak]` işaretli, slug'ı boş taslağı
`/bursa/-1696500` gibi 404 veren bir adresle yayına çıkarıyordu.
"""

import tempfile
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth.models import Group, User
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from taksonomi.models import Etiket, Kategori, KategoriTur, Kaynak

from . import yayin_kapisi, yz_kopru
from .formlar import HaberForm
from .models import YZ_BASLIK_ISARETI, Haber
from .tests_yz import paket_kur


def _tam_veri(kategori, etiket, kaynak, **ek):
    veri = {
        "baslik": "Kollektör hattı tamamlanıyor",
        "spot": "Hattın yüzde 80'i bitti.",
        "govde": "<p>Birinci paragraf.</p><p>İkinci paragraf.</p>",
        "kategori": kategori.pk, "etiketler": etiket.ad,
        "kaynak_turu": Haber.KAYNAK_AJANS, "kaynaklar": [kaynak.pk],
        "hazirlik": "hazir",
        "yayin_zamani": timezone.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    veri.update(ek)
    return veri


class KapiTemel(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        gecici = tempfile.TemporaryDirectory()
        cls.addClassCleanup(gecici.cleanup)
        yama = patch.object(yz_kopru, "CIKTI_KOK", Path(gecici.name))
        yama.start()
        cls.addClassCleanup(yama.stop)

    @classmethod
    def setUpTestData(cls):
        call_command("taksonomi_kur", verbosity=0)
        call_command("roller_kur", verbosity=0)
        cls.kategori = KategoriTur.objects.get(
            tur=Kategori.TUR_HABER, slug="gundem").kategori
        cls.etiket = Etiket.objects.create(ad="Kapı", slug="kapi")
        cls.kaynak = Kaynak.objects.create(ad="Kapı Ajansı", tur=Kaynak.TUR_AJANS)
        cls.k = {}
        for sira, rol in enumerate(("Muhabir", "Editör", "Yayın Yönetmeni")):
            u = User.objects.create_user(f"kapi{sira}", first_name="K",
                                         last_name=str(sira))
            u.groups.add(Group.objects.get(name=rol))
            cls.k[rol] = u

    def veri(self, **ek):
        return _tam_veri(self.kategori, self.etiket, self.kaynak, **ek)

    def gir(self, rol):
        self.client.force_login(self.k[rol])


class MuhabirYayinlayamaz(KapiTemel):
    """Muhabir × (ekle, düzenle, toplu, yz-taslak)."""

    # --- ekle ---
    def test_ekle_formunda_durum_alani_yok(self):
        self.gir("Muhabir")
        yanit = self.client.get("/panel/haber/ekle")
        self.assertEqual(yanit.status_code, 200)
        self.assertNotIn("durum", yanit.context["form"].fields)
        self.assertNotContains(yanit, 'name="durum"')

    def test_ekle_durum_aktif_gonderilirse_reddedilir(self):
        self.gir("Muhabir")
        yanit = self.client.post("/panel/haber/ekle",
                                 self.veri(durum=Haber.DURUM_AKTIF))
        self.assertEqual(yanit.status_code, 200)
        self.assertContains(yanit, "yayına alma yetkiniz yok")
        self.assertFalse(Haber.objects.filter(
            baslik="Kollektör hattı tamamlanıyor").exists())

    def test_ekle_tam_haber_pasif_dogar(self):
        """Eşiği geçen haber bile muhabirden Pasif + Yayına hazır doğar."""
        self.gir("Muhabir")
        yanit = self.client.post("/panel/haber/ekle", self.veri())
        self.assertEqual(yanit.status_code, 302)
        haber = Haber.objects.get(baslik="Kollektör hattı tamamlanıyor")
        self.assertEqual(haber.durum, Haber.DURUM_PASIF)
        self.assertEqual(haber.hazirlik, "hazir")
        self.assertEqual(self.client.get(haber.get_absolute_url()).status_code, 404)

    # --- düzenle ---
    def test_duzenle_kendi_taslagini_yayina_alamaz(self):
        haber = Haber.objects.create(
            id=5_100_001, slug="t", baslik="Taslak", kategori=self.kategori,
            durum=Haber.DURUM_PASIF, hazirlik="taslak", olusturan=self.k["Muhabir"])
        self.gir("Muhabir")
        yanit = self.client.post(f"/panel/haber/{haber.pk}",
                                 self.veri(durum=Haber.DURUM_AKTIF))
        self.assertEqual(yanit.status_code, 200)
        haber.refresh_from_db()
        self.assertEqual(haber.durum, Haber.DURUM_PASIF)

    def test_duzenle_yayindaki_haberi_degistiremez(self):
        """Yayındaki metni değiştirmek de yayımlamaktır."""
        haber = Haber.objects.create(
            id=5_100_002, slug="y", baslik="Yayında", kategori=self.kategori,
            spot="Spot", govde="<p>Bir.</p><p>İki.</p>",
            durum=Haber.DURUM_AKTIF, yayin_zamani=timezone.now(),
            olusturan=self.k["Muhabir"])
        self.gir("Muhabir")
        yanit = self.client.post(f"/panel/haber/{haber.pk}",
                                 self.veri(baslik="Değiştirilmiş başlık"))
        self.assertEqual(yanit.status_code, 200)
        self.assertContains(yanit, "yayındaki haberi değiştirme yetkiniz yok")
        haber.refresh_from_db()
        self.assertEqual(haber.baslik, "Yayında")

    # --- toplu ---
    def test_toplu_yayina_al_yasak(self):
        haber = Haber.objects.create(
            id=5_100_003, slug="t3", baslik="Taslak 3", kategori=self.kategori,
            spot="Spot", govde="<p>Bir.</p><p>İki.</p>",
            kaynak_turu=Haber.KAYNAK_MUHABIR, muhabir="A",
            durum=Haber.DURUM_PASIF, olusturan=self.k["Muhabir"])
        haber.etiketler.add(self.etiket)
        self.gir("Muhabir")
        yanit = self.client.post("/panel/toplu", {"fiil": "yayina_al",
                                                  "kimlikler": [haber.pk]})
        self.assertEqual(yanit.status_code, 403)
        haber.refresh_from_db()
        self.assertEqual(haber.durum, Haber.DURUM_PASIF)

    # --- yapay zekâ taslağı ---
    def test_yz_taslagi_pasif_acilir_ve_yayina_alinamaz(self):
        self.gir("Muhabir")
        with patch.object(yz_kopru, "paket_uret", return_value=paket_kur()):
            yanit = self.client.post("/panel/yz-taslak",
                                     {"adres": "https://ornek-yayin.com/haber/1",
                                      "saglayici": "kural"})
        self.assertEqual(yanit.status_code, 302)
        haber = Haber.objects.get(olusturan=self.k["Muhabir"])
        self.assertEqual(haber.durum, Haber.DURUM_PASIF)
        self.assertTrue(haber.baslik.startswith(YZ_BASLIK_ISARETI))
        yanit = self.client.post(f"/panel/haber/{haber.pk}",
                                 self.veri(durum=Haber.DURUM_AKTIF))
        self.assertEqual(yanit.status_code, 200)
        haber.refresh_from_db()
        self.assertEqual(haber.durum, Haber.DURUM_PASIF)

    def test_yz_taslak_notlari_ayni_kapidan_gelir(self):
        haber, notlar = yz_kopru.taslak_yaz(paket_kur(), self.k["Muhabir"])
        beklenen = yayin_kapisi.haber_eksikleri(haber)
        self.assertTrue(beklenen)
        self.assertTrue(any(", ".join(beklenen) in n for n in notlar), notlar)


class VarsayilanPasif(KapiTemel):

    def test_yeni_haber_formu_pasif_ve_taslak_acilir(self):
        self.gir("Editör")
        form = self.client.get("/panel/haber/ekle").context["form"]
        self.assertEqual(form["durum"].value(), Haber.DURUM_PASIF)
        self.assertEqual(form["hazirlik"].value(), "taslak")

    def test_editor_yayina_alabilir(self):
        self.gir("Editör")
        yanit = self.client.post("/panel/haber/ekle",
                                 self.veri(durum=Haber.DURUM_AKTIF))
        self.assertEqual(yanit.status_code, 302)
        haber = Haber.objects.get(baslik="Kollektör hattı tamamlanıyor")
        self.assertEqual(haber.durum, Haber.DURUM_AKTIF)
        self.assertEqual(self.client.get(haber.get_absolute_url()).status_code, 200)


class KaynakKurali(KapiTemel):
    """Kaynak her zaman belirtilir — kapıda uygulanır, gevşetilmez."""

    def _form(self, **ek):
        return HaberForm(data=self.veri(durum=Haber.DURUM_AKTIF, **ek),
                         kullanici=self.k["Editör"])

    def test_ajans_haberi_kaynaksiz_yayinlanmaz(self):
        form = self._form(kaynaklar=[])
        self.assertFalse(form.is_valid())
        self.assertIn("kaynak", " ".join(form.non_field_errors()))

    def test_dis_yayin_kaynaksiz_yayinlanmaz(self):
        form = self._form(kaynak_turu=Haber.KAYNAK_DIS_YAYIN, kaynaklar=[])
        self.assertFalse(form.is_valid())

    def test_muhabir_haberi_muhabir_adi_ister(self):
        self.assertFalse(self._form(kaynak_turu=Haber.KAYNAK_MUHABIR,
                                    kaynaklar=[], muhabir="").is_valid())
        self.assertTrue(self._form(kaynak_turu=Haber.KAYNAK_MUHABIR,
                                   kaynaklar=[], muhabir="A. Yılmaz").is_valid())

    def test_kaynak_turu_secilmeden_yeni_yayin_olmaz(self):
        form = self._form(kaynak_turu="", kaynaklar=[])
        self.assertFalse(form.is_valid())
        self.assertIn("kaynak türü", " ".join(form.non_field_errors()))

    def test_taslakta_kaynak_aranmaz(self):
        form = HaberForm(data=self.veri(durum=Haber.DURUM_PASIF,
                                        hazirlik="taslak", kaynaklar=[]),
                         kullanici=self.k["Editör"])
        self.assertTrue(form.is_valid(), form.errors)


class TopluKapi(KapiTemel):
    """Toplu "Yayına al" formla aynı eşikten geçer."""

    def _haber(self, kimlik, **ek):
        alanlar = dict(id=kimlik, slug=f"h-{kimlik}", baslik=f"Haber {kimlik}",
                       kategori=self.kategori, spot="Spot",
                       govde="<p>Bir.</p><p>İki.</p>",
                       kaynak_turu=Haber.KAYNAK_AJANS, durum=Haber.DURUM_PASIF)
        alanlar.update(ek)
        haber = Haber.objects.create(**alanlar)
        haber.etiketler.add(self.etiket)
        haber.kaynaklar.add(self.kaynak)
        return haber

    def test_isaretli_bos_slug_ve_kaynaksiz_atlanir(self):
        iyi = self._haber(5_200_001)
        isaretli = self._haber(5_200_002, slug="",
                               baslik=f"{YZ_BASLIK_ISARETI} Kaynağın başlığı")
        bos_slug = self._haber(5_200_003, slug="")
        kaynaksiz = self._haber(5_200_004)
        kaynaksiz.kaynaklar.clear()
        self.gir("Editör")
        yanit = self.client.post("/panel/toplu", {
            "fiil": "yayina_al",
            "kimlikler": [iyi.pk, isaretli.pk, bos_slug.pk, kaynaksiz.pk]})
        self.assertEqual(yanit.status_code, 302)
        durumlar = dict(Haber.objects.filter(pk__gte=5_200_001)
                        .values_list("pk", "durum"))
        self.assertEqual(durumlar[iyi.pk], Haber.DURUM_AKTIF)
        for h in (isaretli, bos_slug, kaynaksiz):
            with self.subTest(haber=h.pk):
                self.assertEqual(durumlar[h.pk], Haber.DURUM_PASIF)
        # 404 adresi doğmadı: yayındaki her haberin slug'ı dolu.
        self.assertFalse(Haber.yayindakiler().filter(slug="").exists())

    def test_eczane_komutu_da_kapidan_gecer(self):
        from pathlib import Path as Yol
        kaynak = (Yol(__file__).parent / "management" / "commands"
                  / "eczane_haberi.py").read_text(encoding="utf-8")
        self.assertIn("yayin_kapisi.icerik_eksikleri", kaynak)
