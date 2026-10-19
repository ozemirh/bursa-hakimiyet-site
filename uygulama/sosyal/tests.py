"""Sosyal paylaşım testleri — PANEL-NOTLARI.md §25.

Ölçülen dört söz:

  1. Metin platformun saydığı uzunluğa sığar (X'te bağlantı 23 karakter).
  2. Kuyruk aynı haberi aynı hesapta iki kez açmaz.
  3. Arşivden bir haberi açıp kaydetmek onu sosyal medyada paylaşmaz.
  4. Anahtarı olmayan hesap sessizce başarısız olmaz: satır ELLE durumunda
     doğar ve panelde metniyle görünür.

Ağa çıkan tek katman `saglayicilar`; testlerde yerine sahte sağlayıcı
konuyor. Gerçek uçlara istek atan test YOK — böyle bir test, çalıştığı her
seferde gazetenin hesabına gönderi atardı.
"""

from unittest import mock

from django.contrib.auth.models import Group, User
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from icerik.formlar import HaberForm
from icerik.models import Haber
from taksonomi.models import Etiket, Kategori, KategoriTur

from . import kuyruk
from .metin import (SINIRLAR, etiket_yaz, gonderi_metni, olculen_uzunluk,
                    paylas_adresi)
from .models import SosyalGonderi, SosyalHesap
from .saglayicilar import Sonuc, SosyalHata
from .saglayicilar.x import oauth_basligi

PAROLA = "sosyal-parola-1234"

TAM_X = {"tuketici_anahtari": "a", "tuketici_gizi": "b",
         "erisim_jetonu": "c", "erisim_gizi": "d"}


class Temel(TestCase):
    """Ortak kurulum: taksonomi, roller, bir kategori ve bir haber."""

    @classmethod
    def setUpTestData(cls):
        call_command("taksonomi_kur", verbosity=0)
        call_command("roller_kur", verbosity=0)
        cls.kategori = KategoriTur.objects.get(
            tur=Kategori.TUR_HABER, slug="gundem").kategori
        cls.etiket = Etiket.objects.create(ad="nilüfer çayı",
                                           slug="nilufer-cayi")
        cls.kullanicilar = {}
        for sira, rol in enumerate(("Muhabir", "Editör", "Yayın Yönetmeni")):
            k = User.objects.create_user(f"s{sira}", password=PAROLA)
            k.groups.add(Group.objects.get(name=rol))
            cls.kullanicilar[rol] = k

    def _gir(self, rol):
        self.client.force_login(self.kullanicilar[rol])

    def _haber(self, kimlik=900001, yayinda=True, **ek):
        alanlar = {
            "id": kimlik, "slug": "test-haber", "baslik": "Baraj doluluğu düştü",
            "spot": "Nilüfer Çayı havzasındaki barajlarda doluluk oranı "
                    "geçen yılın altında kaldı.",
            "govde": "<p>Bir.</p><p>İki.</p>",
            "kategori": self.kategori,
            "durum": Haber.DURUM_AKTIF if yayinda else Haber.DURUM_PASIF,
            "yayin_zamani": timezone.now() if yayinda else None,
        }
        alanlar.update(ek)
        haber = Haber.objects.create(**alanlar)
        haber.etiketler.add(self.etiket)
        return haber

    def _hesap(self, platform=SosyalHesap.X, gizli=None, **ek):
        alanlar = {"platform": platform, "ad": f"BH {platform}",
                   "kullanici_adi": f"bh_{platform}",
                   "gizli_ayar": gizli}
        alanlar.update(ek)
        return SosyalHesap.objects.create(**alanlar)


class MetinKurma(Temel):

    def test_x_metni_sinira_sigar(self):
        hesap = self._hesap(SosyalHesap.X)
        haber = self._haber(baslik="B" * 60)
        metin = gonderi_metni(haber, hesap)
        self.assertLessEqual(olculen_uzunluk(metin, SosyalHesap.X),
                             SINIRLAR[SosyalHesap.X])

    def test_baglanti_yirmi_uc_karakter_sayilir(self):
        """Ham `len` ile ölçmek 280'e sığdığını sandığımız gönderiyi kestirir."""
        metin = "abc https://www.bursahakimiyet.com.tr/gundem/uzun-bir-slug-1234"
        self.assertLess(olculen_uzunluk(metin, SosyalHesap.X), len(metin))
        self.assertEqual(olculen_uzunluk(metin, SosyalHesap.FACEBOOK),
                         len(metin))

    def test_etiket_turkce_buyuk_harf(self):
        self.assertEqual(etiket_yaz("nilüfer çayı"), "#NilüferÇayı")
        self.assertEqual(etiket_yaz("izmir yolu"), "#İzmirYolu")
        self.assertEqual(etiket_yaz("!!!"), "")

    def test_instagram_metninde_adres_yok(self):
        """Instagram altyazısındaki bağlantı tıklanmıyor; kalıpta da yok."""
        hesap = self._hesap(SosyalHesap.INSTAGRAM)
        metin = gonderi_metni(self._haber(), hesap)
        self.assertNotIn("http", metin)
        self.assertIn("profilimizdeki bağlantıda", metin)

    def test_uzun_spot_kisalir_baslik_kalir(self):
        hesap = self._hesap(SosyalHesap.X, metin_kalibi="{baslik} — {spot} {adres}")
        haber = self._haber(baslik="Kısa başlık", spot="Uzun " * 60)
        metin = gonderi_metni(haber, hesap)
        self.assertIn("Kısa başlık", metin)
        self.assertLessEqual(olculen_uzunluk(metin, SosyalHesap.X), 280)

    def test_paylas_adresi_yalniz_iki_platformda(self):
        self.assertTrue(paylas_adresi(self._hesap(SosyalHesap.X), "m", "a"))
        self.assertTrue(paylas_adresi(self._hesap(SosyalHesap.FACEBOOK), "m", "a"))
        self.assertEqual(paylas_adresi(self._hesap(SosyalHesap.INSTAGRAM),
                                       "m", "a"), "")


class KuyrukKurallari(Temel):

    def test_anahtarsiz_hesap_elle_satiri_acar(self):
        hesap = self._hesap(SosyalHesap.X)          # gizli_ayar boş
        (gonderi,) = kuyruk.kuyruga_al(self._haber(), [hesap])
        self.assertEqual(gonderi.durum, SosyalGonderi.ELLE)
        self.assertTrue(gonderi.metin)

    def test_anahtarli_hesap_bekleyen_satir_acar(self):
        hesap = self._hesap(SosyalHesap.X, gizli=TAM_X)
        (gonderi,) = kuyruk.kuyruga_al(self._haber(), [hesap])
        self.assertEqual(gonderi.durum, SosyalGonderi.BEKLIYOR)
        self.assertTrue(gonderi.gonderilebilir_mi())

    def test_ayni_hesapta_ikinci_satir_acilmaz(self):
        hesap = self._hesap(SosyalHesap.X, gizli=TAM_X)
        haber = self._haber()
        kuyruk.kuyruga_al(haber, [hesap])
        self.assertEqual(kuyruk.kuyruga_al(haber, [hesap]), [])
        self.assertEqual(SosyalGonderi.objects.filter(haber=haber).count(), 1)

    def test_taslak_haber_gonderilmez_ama_kuyrukta_kalir(self):
        hesap = self._hesap(SosyalHesap.X, gizli=TAM_X)
        (gonderi,) = kuyruk.kuyruga_al(self._haber(yayinda=False), [hesap])
        self.assertFalse(gonderi.gonderilebilir_mi())
        ozet = kuyruk.bekleyenleri_gonder()
        self.assertEqual(ozet["yayin_bekliyor"], 1)
        gonderi.refresh_from_db()
        self.assertEqual(gonderi.durum, SosyalGonderi.BEKLIYOR)

    def test_youtube_otomatik_secime_girmez(self):
        self._hesap(SosyalHesap.YOUTUBE)
        x = self._hesap(SosyalHesap.X, gizli=TAM_X)
        secilebilir = list(kuyruk.secilebilir_hesaplar())
        self.assertEqual(secilebilir, [x])

    def test_youtube_satiri_elle_acilir_ve_gonderilmez(self):
        hesap = self._hesap(SosyalHesap.YOUTUBE)
        (gonderi,) = kuyruk.kuyruga_al(self._haber(), [hesap],
                                       kaynak=SosyalGonderi.ELLE_ACILDI)
        self.assertEqual(gonderi.durum, SosyalGonderi.ELLE)
        self.assertFalse(gonderi.gonderilebilir_mi())

    def test_secimden_cikan_hesabin_satiri_iptal_olur(self):
        hesap = self._hesap(SosyalHesap.X, gizli=TAM_X)
        haber = self._haber()
        (gonderi,) = kuyruk.kuyruga_al(haber, [hesap])
        kuyruk.haber_kaydedildi(haber, [])
        gonderi.refresh_from_db()
        self.assertEqual(gonderi.durum, SosyalGonderi.IPTAL)

    def test_elle_acilan_satir_haber_kaydinda_iptal_olmaz(self):
        """YouTube satırını haber formu kapatmaz; onu açan kapatır."""
        youtube = self._hesap(SosyalHesap.YOUTUBE)
        haber = self._haber()
        (gonderi,) = kuyruk.kuyruga_al(haber, [youtube],
                                       kaynak=SosyalGonderi.ELLE_ACILDI)
        kuyruk.haber_kaydedildi(haber, [])
        gonderi.refresh_from_db()
        self.assertEqual(gonderi.durum, SosyalGonderi.ELLE)

    def test_gonderilmis_satir_iptal_edilmez(self):
        hesap = self._hesap(SosyalHesap.X, gizli=TAM_X)
        haber = self._haber()
        (gonderi,) = kuyruk.kuyruga_al(haber, [hesap])
        SosyalGonderi.objects.filter(pk=gonderi.pk).update(
            durum=SosyalGonderi.GONDERILDI)
        kuyruk.haber_kaydedildi(haber, [])
        gonderi.refresh_from_db()
        self.assertEqual(gonderi.durum, SosyalGonderi.GONDERILDI)


class SahteGonderim(Temel):
    """Gönderim sonucunun kayda nasıl yazıldığı."""

    def _gonderi(self, **ek):
        hesap = self._hesap(SosyalHesap.X, gizli=TAM_X, **ek)
        return kuyruk.kuyruga_al(self._haber(), [hesap])[0]

    def test_basarili_gonderim_damgayi_yazar(self):
        gonderi = self._gonderi()
        sahte = mock.Mock()
        sahte.gonder.return_value = Sonuc(True, dis_kimlik="42",
                                          dis_adres="https://x.com/bh/status/42")
        with mock.patch.object(SosyalHesap, "saglayici", return_value=sahte):
            self.assertTrue(kuyruk.gonder(gonderi))
        gonderi.refresh_from_db()
        self.assertEqual(gonderi.durum, SosyalGonderi.GONDERILDI)
        self.assertEqual(gonderi.dis_kimlik, "42")
        self.assertIsNotNone(gonderi.gonderim_zamani)
        self.assertEqual(gonderi.hesap.son_hata, "")

    def test_ag_hatasi_satira_yazilir(self):
        gonderi = self._gonderi()
        sahte = mock.Mock()
        sahte.gonder.side_effect = SosyalHata("HTTP 401: Unauthorized")
        with mock.patch.object(SosyalHesap, "saglayici", return_value=sahte):
            self.assertFalse(kuyruk.gonder(gonderi))
        gonderi.refresh_from_db()
        self.assertEqual(gonderi.durum, SosyalGonderi.HATA)
        self.assertIn("401", gonderi.hata_metni)
        self.assertEqual(gonderi.deneme, 1)
        # Hatalı satır kuyrukta kalır ve yeniden denenebilir.
        self.assertIn(gonderi, SosyalGonderi.bekleyenler())

    def test_beklenmeyen_cokme_de_yutulmaz(self):
        gonderi = self._gonderi()
        sahte = mock.Mock()
        sahte.gonder.side_effect = ValueError("bozuk yanıt")
        with mock.patch.object(SosyalHesap, "saglayici", return_value=sahte):
            self.assertFalse(kuyruk.gonder(gonderi))
        gonderi.refresh_from_db()
        self.assertEqual(gonderi.durum, SosyalGonderi.HATA)
        self.assertIn("bozuk yanıt", gonderi.hata_metni)


class XImzasi(Temel):

    def test_oauth_basligi_gerekli_alanlari_tasir(self):
        hesap = self._hesap(SosyalHesap.X, gizli=TAM_X)
        baslik = oauth_basligi("POST", "https://api.x.com/2/tweets", hesap)
        self.assertTrue(baslik.startswith("OAuth "))
        for parca in ("oauth_consumer_key", "oauth_nonce", "oauth_signature",
                      "oauth_signature_method", "oauth_timestamp",
                      "oauth_token", "oauth_version"):
            self.assertIn(parca, baslik)

    def test_ortam_degiskeni_veritabanini_ezer(self):
        hesap = self._hesap(SosyalHesap.X, gizli={"erisim_jetonu": "kayitli"})
        self.assertEqual(hesap.gizli("erisim_jetonu"), "kayitli")
        with mock.patch.dict("os.environ",
                             {"BH_SOSYAL_X_ERISIM_JETONU": "ortamdan"}):
            self.assertEqual(hesap.gizli("erisim_jetonu"), "ortamdan")


class HaberFormuBagi(Temel):
    """Formun kuyruğa dokunma biçimi — §25'in en kolay kırılan yeri."""

    def _gonderi_verisi(self, haber, **ek):
        veri = {
            "baslik": haber.baslik, "spot": haber.spot, "govde": haber.govde,
            "kategori": self.kategori.pk, "etiketler": self.etiket.ad,
            "durum": Haber.DURUM_AKTIF, "hazirlik": "hazir",
            "yayin_zamani": timezone.now().strftime("%Y-%m-%d %H:%M:%S"),
            "kaynak_turu": "", "muhabir": "", "meta_yazar": "",
        }
        veri.update(ek)
        return veri

    def test_yeni_haberde_varsayilan_hesaplar_isaretli(self):
        hesap = self._hesap(SosyalHesap.X, varsayilan=True)
        form = HaberForm(kullanici=self.kullanicilar["Editör"])
        self.assertEqual(list(form.initial["sosyal_hesaplar"]), [hesap.pk])

    def test_kayitli_haberde_kutu_kendiliginden_isaretlenmez(self):
        """Arşivden açılan haber, kaydedilince sosyal medyada paylaşılmaz."""
        self._hesap(SosyalHesap.X, varsayilan=True)
        haber = self._haber()
        form = HaberForm(instance=haber, kullanici=self.kullanicilar["Editör"])
        self.assertEqual(list(form.initial["sosyal_hesaplar"]), [])

    def test_muhabir_kutulari_gormez(self):
        self._hesap(SosyalHesap.X)
        form = HaberForm(kullanici=self.kullanicilar["Muhabir"])
        self.assertNotIn("sosyal_hesaplar", form.fields)

    def test_form_kaydi_kuyruga_satir_acar(self):
        hesap = self._hesap(SosyalHesap.X, gizli=TAM_X)
        haber = self._haber(kimlik=900010, durum=Haber.DURUM_PASIF,
                            yayin_zamani=None)
        self._gir("Editör")
        yanit = self.client.post(
            f"/panel/haber/{haber.pk}",
            self._gonderi_verisi(haber, sosyal_hesaplar=[hesap.pk],
                                 kaynak_turu=Haber.KAYNAK_MUHABIR,
                                 muhabir="A. Yılmaz"))
        self.assertEqual(yanit.status_code, 302)
        gonderi = SosyalGonderi.objects.get(haber=haber, hesap=hesap)
        self.assertEqual(gonderi.durum, SosyalGonderi.BEKLIYOR)
        self.assertEqual(gonderi.olusturan, self.kullanicilar["Editör"])

    def test_muhabir_kaydi_baskasinin_satirini_iptal_etmez(self):
        """Alan formda yoksa kuyruğa DOKUNULMAZ (boş seçim sanılmaz)."""
        hesap = self._hesap(SosyalHesap.X, gizli=TAM_X)
        haber = self._haber(kimlik=900011, durum=Haber.DURUM_PASIF,
                            yayin_zamani=None,
                            olusturan=self.kullanicilar["Muhabir"])
        (gonderi,) = kuyruk.kuyruga_al(haber, [hesap])
        self._gir("Muhabir")
        self.client.post(f"/panel/haber/{haber.pk}",
                         self._gonderi_verisi(haber, durum=Haber.DURUM_PASIF,
                                              hazirlik="taslak"))
        gonderi.refresh_from_db()
        self.assertEqual(gonderi.durum, SosyalGonderi.BEKLIYOR)


class Ekranlar(Temel):

    def test_kuyruk_ekrani_yayinlayanda_acilir(self):
        self._gir("Editör")
        self.assertEqual(self.client.get("/panel/sosyal").status_code, 200)

    def test_kuyruk_ekrani_muhabire_kapali(self):
        self._gir("Muhabir")
        self.assertEqual(self.client.get("/panel/sosyal").status_code, 403)

    def test_hesap_ekrani_yalniz_kullanici_yonetiminde(self):
        self._gir("Editör")
        self.assertEqual(self.client.get("/panel/sosyal/hesaplar").status_code,
                         403)
        self._gir("Yayın Yönetmeni")
        self.assertEqual(self.client.get("/panel/sosyal/hesaplar").status_code,
                         200)

    def test_gonderi_ekrani_ve_elle_isaretleme(self):
        hesap = self._hesap(SosyalHesap.X)          # anahtarsız → ELLE
        (gonderi,) = kuyruk.kuyruga_al(self._haber(), [hesap])
        self._gir("Editör")
        yanit = self.client.get(f"/panel/sosyal/{gonderi.pk}")
        self.assertEqual(yanit.status_code, 200)
        self.assertContains(yanit, "Paylaşıldı işaretle")

        self.client.post(f"/panel/sosyal/{gonderi.pk}", {
            "eylem": "paylasildi", "metin": gonderi.metin,
            "gorsel_adres": "", "dis_adres": "https://x.com/bh/status/9"})
        gonderi.refresh_from_db()
        self.assertEqual(gonderi.durum, SosyalGonderi.GONDERILDI)
        self.assertEqual(gonderi.dis_adres, "https://x.com/bh/status/9")

    def test_sinirin_ustundeki_metin_kaydedilemez(self):
        hesap = self._hesap(SosyalHesap.X, gizli=TAM_X)
        (gonderi,) = kuyruk.kuyruga_al(self._haber(), [hesap])
        self._gir("Editör")
        yanit = self.client.post(f"/panel/sosyal/{gonderi.pk}", {
            "eylem": "kaydet", "metin": "x" * 400,
            "gorsel_adres": "", "dis_adres": ""})
        self.assertEqual(yanit.status_code, 200)
        self.assertContains(yanit, "sınırı 280")

    def test_gonder_ekrani_hazir_satirlari_sayar(self):
        hesap = self._hesap(SosyalHesap.X, gizli=TAM_X)
        kuyruk.kuyruga_al(self._haber(), [hesap])
        self._gir("Editör")
        yanit = self.client.get("/panel/sosyal/gonder")
        self.assertEqual(yanit.status_code, 200)
        self.assertContains(yanit, "1</b> satır")

    def test_haber_formunda_kutular_gorunur(self):
        self._hesap(SosyalHesap.X)
        self._gir("Editör")
        yanit = self.client.get("/panel/haber/ekle")
        self.assertContains(yanit, "Sosyal medyada paylaş")
        self.assertContains(yanit, "sosyal_hesaplar")
