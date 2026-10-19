# -*- coding: utf-8 -*-
"""Paket M (19 Ekim 2026) — konu takibi temizliği ve yapay zekâ yayın güvenliği.

1. Periyodik tür kalıpları (`RUTIN_GRUPLARI`) ve yapısal dizi süzgeci.
2. Okunur dosya adları (ikili ad, kurum başı, çekimli olay sözcüğü, harf biçimi).
3. `konu_temizle`: onaylı periyodik dosyayı beklemeye alır, JSON'a yazar,
   `konu_tara` onu silmez, `--geri-yukle` geri döndürür.
4. "Sürüyor" okuma anında.
5. K2 (uydurma olgu) denetimi, yayın kapısı ve tek tek kapatma.
6. Yapay zekâ köken kaydı ve editörün değiştirdiği oran.
"""

import json
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth.models import Group, User
from django.core.management import call_command
from django.test import SimpleTestCase, TestCase
from django.utils import timezone

from taksonomi.models import Etiket, Kategori, KategoriTur, Kaynak

from . import konu_motoru, yayin_kapisi, yz_koken, yz_kopru
from .models import Haber, Konu, KonuHaber, LogKaydi, YzBulgu, YzKoken
from .tests_konu import GUN0, sentetik
from .tests_yz import paket_kur

ARAC = Path(__file__).resolve().parents[2] / "arac"
if str(ARAC) not in sys.path:
    sys.path.insert(0, str(ARAC))
import denetim  # noqa: E402


# ---------------------------------------------------------------- 1. kalıplar
class RutinKaliplari(SimpleTestCase):
    """Her grup, sitede onaylı duran örnek dosyasının başlığıyla tanınmalı."""

    ORNEKLER = {
        "borsa açılış ve kapanışı": "New York borsası yükselişle açıldı",
        "petrol ve emtia fiyatı": "Brent petrolün varili 68,50 dolar oldu",
        "şans oyunu sonucu": "Süper Loto sonuçları açıklandı",
        "tarihte bugün": "Bursa Hakimiyet Gazetesi'nin arşivinden tarihte bugün | 1 Mart",
        "planlı kesinti ve kurum duyurusu":
            "BUSKİ'den o mahallelere kötü haber! Bursa'da 10 saatlik su kesintisi",
        "sefer iptali duyurusu": "Bursalılar dikkat! BUDO seferleri iptal",
        "tüik ve ekonomik gösterge": "Konut Fiyat Endeksi mart ayında arttı",
        "dini gün ve resmi tatil": "Ramazan Bayramı tatili kaç gün olacak?",
        "maç günü rutini": "Süper Lig'de 27. haftanın hakemleri açıklandı",
        "sayaç ve bilanço": "Asya ülkelerinde koronavirüs bilançosu açıklandı",
        "asayiş bülteni": "Kayseri'de kesinleşmiş cezası bulunan ihraç müdür yakalandı",
        "gemi geçişi": "Rus savaş gemisi Çanakkale Boğazı'ndan geçti",
        "ilan ve kadro duyurusu": "Koç Üniversitesi 2 öğretim üyesi alacak!",
        "kripto para durumu": "Bitcoin, Ethereum ve Altcoin'lerde son durum ne?",
        "hava durumu": "Marmara Denizi'nde fırtına uyarısı",
        "televizyon programı": "İbo Show'un bu haftaki konukları belli oldu",
    }

    def test_her_grubun_ornegi_taninir(self):
        for grup, baslik in self.ORNEKLER.items():
            with self.subTest(grup=grup):
                self.assertEqual(konu_motoru.rutin_turu(baslik), grup)

    def test_her_grubun_gerekcesi_var(self):
        for ad, gerekce, kaliplar in konu_motoru.RUTIN_GRUPLARI:
            with self.subTest(grup=ad):
                self.assertTrue(gerekce.strip())
                self.assertTrue(kaliplar)

    def test_dosya_basliklari_rutin_degil(self):
        """Geniş ad (Süper Lig, Borsa, Bursaspor) tek başına kalıp değildir."""
        for baslik in (
            "Fenerbahçe Leroy Sane transferi için devrede!",
            "Süper Lig'de şampiyonluk yarışı kızıştı",
            "Bursa Ticaret Borsası yeni başkanını seçti",
            "Bozbey rüşvet soruşturmasında tutuklandı",
            "Ece Gürel'in cenazesi toprağa verildi",
            "Bursaspor'da teknik direktör Batalla ile yollar ayrıldı",
            "Kaçak göçmenleri taşıyan bot battı: soruşturma başlatıldı",
        ):
            with self.subTest(baslik=baslik):
                self.assertIsNone(konu_motoru.rutin_turu(baslik))

    def test_eski_borsa_kalibi_hatasi_kapandi(self):
        # 5 Eylül kalıbı `\bborsa\b` "borsası"nı tanımıyordu (300 haberlik dosya).
        self.assertTrue(konu_motoru.rutin_mu("Tokyo borsası güne düşüşle başladı"))


class YapisalSuzgec(SimpleTestCase):

    @staticmethod
    def _derlem(basliklar):
        kayitlar = [k for k in sentetik() if k[0] < 1400]   # yalnız dolgu
        kimlik = 9000
        for gun, baslik in basliklar:
            kayitlar.append((kimlik, baslik, GUN0 + timedelta(days=gun)))
            kimlik += 1
        return kayitlar

    DIZI = [(g, f"Mudanya'da Zeytinbağı Kooperatifi {g + 1}. teslim listesini paylaştı")
            for g in range(16)]

    def test_her_gun_tekrarlanan_dizi_konu_degil(self):
        konular = konu_motoru.tara(self._derlem(self.DIZI))
        self.assertFalse([k for k in konular if "Zeytinbağı" in k.ad], [k.ad for k in konular])

    def test_gelisme_dili_olan_ayni_zincir_konu(self):
        surec = list(self.DIZI)
        surec[3] = (3, "Mudanya'da Zeytinbağı Kooperatifi teslim listesine itiraz etti")
        surec[9] = (9, "Mudanya'da Zeytinbağı Kooperatifi teslim davası mahkemede")
        konular = konu_motoru.tara(self._derlem(surec))
        adlar = [k.ad for k in konular]
        self.assertTrue([a for a in adlar if "Zeytinbağı" in a], adlar)

    def test_periyodik_mi_esikleri(self):
        self.assertTrue(konu_motoru.Motor._periyodik_mi(20, 19, 0))
        self.assertFalse(konu_motoru.Motor._periyodik_mi(14, 14, 0))    # az haber
        self.assertFalse(konu_motoru.Motor._periyodik_mi(20, 10, 0))    # aynı günlere yığılmış
        self.assertFalse(konu_motoru.Motor._periyodik_mi(20, 19, 2))    # gelişme %10

    def test_periyodik_gerekce(self):
        borsa = [(GUN0 + timedelta(days=g), "New York borsası yükselişle açıldı")
                 for g in range(6)]
        self.assertIn("borsa açılış", konu_motoru.periyodik_gerekce(borsa))
        dosya = [(GUN0 + timedelta(days=g), b) for g, b in [
            (0, "Kayıp mimar Ece Gürel aranıyor"), (1, "Ece Gürel sağ bulundu"),
            (2, "Ece Gürel'in cenazesi toprağa verildi")]]
        self.assertEqual(konu_motoru.periyodik_gerekce(dosya), "")


# ---------------------------------------------------------------- 2. ad
class DosyaAdi(SimpleTestCase):

    def test_unvan_araya_girince_ikili_kurulmaz(self):
        parcalar = konu_motoru.parcala("Sağlık Bakanı Müezzinoğlu açıklama yaptı")
        self.assertEqual(konu_motoru.ikililer(parcalar), [])
        parcalar = konu_motoru.parcala("Kayıp mimar Ece Gürel sağ bulundu")
        self.assertEqual(konu_motoru.ikililer(parcalar), [("ece_gürel", "Ece Gürel")])

    def _motor(self, basliklar):
        m = konu_motoru.Motor()
        for b in basliklar:
            m.say(b)
        m.hazirla()
        return m

    def test_baslik_basi_ikilisi_ad_degil(self):
        """"Peki Bursa" yalnız başlığın ilk iki kelimesi; "peki" cümle
        ortasında küçük yazılıyor."""
        m = self._motor(["Peki Bursa kaçıncı sırada?"] * 5
                        + ["Bu iş peki nasıl olacak?"] * 5
                        + ["Bursa'da yeni park açıldı"] * 5)
        kok = "_".join(konu_motoru.kokle(k) for k in ("Peki", "Bursa"))
        self.assertFalse(m._ikili_ad_mi(kok))

    def test_cumle_ortasinda_gecen_ikili_ad(self):
        m = self._motor(["Sinan Ateş davasında karar"] * 3
                        + ["Ankara'da Sinan Ateş anıldı"] * 3
                        + ["Ormanda ateş söndürüldü"] * 5)
        kok = "_".join(konu_motoru.kokle(k) for k in ("Sinan", "Ateş"))
        self.assertTrue(m._ikili_ad_mi(kok))

    def test_kurum_basi_genisler(self):
        m = self._motor([])
        uyeler = [konu_motoru.Haber(i, b, GUN0, ()) for i, b in enumerate([
            "Koç Üniversitesi 2 öğretim üyesi alacak",
            "Koç Üniversitesi yeni kampüs açıyor",
            "Koç Üniversitesi'nde mezuniyet töreni"])]
        kok = konu_motoru.kokle("Üniversitesi")
        self.assertIn(kok, konu_motoru.KURUM_BASI)
        self.assertEqual(m._kurum_genislet(kok, uyeler), "Koç Üniversitesi")

    def test_cekimli_olay_sozcugu_secilmez(self):
        for yuzey in ("saldırganından", "önündeki", "görüntülendi", "alacak", "varsa"):
            with self.subTest(yuzey=yuzey):
                self.assertTrue(konu_motoru._CEKIMLI.search(yuzey))
        for yuzey in ("saldırgan", "deprem", "rapor", "ihale"):
            with self.subTest(yuzey=yuzey):
                self.assertFalse(konu_motoru._CEKIMLI.search(yuzey))

    def test_harf_bicimi_turkce(self):
        self.assertEqual(konu_motoru._harf_bicimi("BURSA BÜYÜKŞEHİR BELEDİYESİ"),
                         "Bursa Büyükşehir Belediyesi")
        self.assertEqual(konu_motoru._harf_bicimi("IĞDIR İNEGÖL"), "Iğdır İnegöl")
        self.assertEqual(konu_motoru._harf_bicimi("ASELSAN"), "ASELSAN")
        self.assertEqual(konu_motoru._harf_bicimi("Ece Gürel"), "Ece Gürel")

    def test_ece_gurel_adi_korunur(self):
        konular = konu_motoru.tara(sentetik())
        self.assertEqual(konular[0].ad, "Ece Gürel")


# ---------------------------------------------------------------- 3-4. veritabanı
class KonuVeri(TestCase):

    @classmethod
    def setUpTestData(cls):
        call_command("taksonomi_kur", verbosity=0)
        call_command("roller_kur", verbosity=0)
        cls.kategori = KategoriTur.objects.get(tur=Kategori.TUR_HABER, slug="gundem").kategori
        cls.editor = User.objects.create_user("m-editor")
        cls.editor.groups.add(Group.objects.get(name="Editör"))
        saat = timezone.now().replace(hour=10, minute=0, second=0, microsecond=0)
        cls.haberler = []
        for kimlik, baslik, tarih in sentetik():
            cls.haberler.append(Haber.objects.create(
                id=kimlik, slug=f"h-{kimlik}", baslik=baslik, kategori=cls.kategori,
                durum=Haber.DURUM_AKTIF,
                yayin_zamani=saat.replace(year=tarih.year, month=tarih.month, day=tarih.day)))
        cls.borsa = []
        for g in range(6):
            t = GUN0 + timedelta(days=200 + g)
            cls.borsa.append(Haber.objects.create(
                id=8000 + g, slug=f"b-{g}", baslik="New York borsası yükselişle açıldı",
                kategori=cls.kategori, durum=Haber.DURUM_AKTIF,
                yayin_zamani=saat.replace(year=t.year, month=t.month, day=t.day)))

    def _onayli_borsa(self, onaylayan=None):
        zaman = timezone.now() - timedelta(days=44)
        konu = Konu.objects.create(
            ad="New York", slug="new-york-2026-09", kaynak=Konu.KAYNAK_MOTOR,
            onay=Konu.ONAY_ONAYLI, onay_zamani=zaman, onaylayan=onaylayan, guven=70,
            baslangic=self.borsa[0].yayin_zamani.date(),
            bitis=self.borsa[-1].yayin_zamani.date(), haber_sayisi=6, acik=True)
        KonuHaber.objects.bulk_create([KonuHaber(konu=konu, haber=h, tarih=h.yayin_zamani.date())
                                       for h in self.borsa])
        return konu

    def test_temizle_geri_al_tara_korur_geri_yukle(self):
        call_command("konu_tara", onay_esigi=0, verbosity=0)     # Ece Gürel onaylı
        ece = Konu.objects.get(ad__contains="Ece")
        borsa = self._onayli_borsa()
        onceki_zaman = borsa.onay_zamani
        self.assertEqual(self.client.get(borsa.get_absolute_url()).status_code, 200)

        with tempfile.TemporaryDirectory() as klasor:
            yol = Path(klasor) / "konu_geri_alma.json"
            call_command("konu_temizle", kuru=True, verbosity=0)
            self.assertEqual(Konu.objects.get(pk=borsa.pk).onay, Konu.ONAY_ONAYLI)

            call_command("konu_temizle", yaz=str(yol), verbosity=0)
            borsa.refresh_from_db()
            self.assertEqual(borsa.onay, Konu.ONAY_BEKLIYOR)
            self.assertIn("borsa açılış", borsa.geri_alma)
            self.assertEqual(Konu.objects.get(pk=ece.pk).onay, Konu.ONAY_ONAYLI)
            veri = json.loads(yol.read_text(encoding="utf-8"))
            self.assertEqual([d["id"] for d in veri["dosyalar"]], [borsa.pk])
            self.assertEqual(veri["toplam"], {"dosya": 1, "bag": 6})
            self.assertEqual(veri["dosyalar"][0]["onceki"]["onay"], Konu.ONAY_ONAYLI)
            # Onaysız dosya sitede yok
            self.assertEqual(self.client.get(borsa.get_absolute_url()).status_code, 404)
            # Aynı dosyanın üzerine yazılmaz
            from django.core.management.base import CommandError
            with self.assertRaises(CommandError):
                call_command("konu_temizle", yaz=str(yol), verbosity=0)

            # Yeniden tarama geri alınmış dosyayı silmez (motor önerisi değil)
            call_command("konu_tara", verbosity=0)
            call_command("konu_tara", sifirla=True, verbosity=0)
            self.assertTrue(Konu.objects.filter(pk=borsa.pk).exists())
            self.assertEqual(KonuHaber.objects.filter(konu=borsa).count(), 6)

            call_command("konu_temizle", geri_yukle=str(yol), verbosity=0)
            borsa.refresh_from_db()
            self.assertEqual(borsa.onay, Konu.ONAY_ONAYLI)
            self.assertEqual(borsa.onay_zamani, onceki_zaman)
            self.assertEqual(borsa.geri_alma, "")

    def test_geri_yukleme_editor_kararina_dokunmaz(self):
        borsa = self._onayli_borsa()
        with tempfile.TemporaryDirectory() as klasor:
            yol = Path(klasor) / "g.json"
            call_command("konu_temizle", yaz=str(yol), verbosity=0)
            borsa.refresh_from_db()
            borsa.onay = Konu.ONAY_RET            # editör panelde reddetti
            borsa.save()
            call_command("konu_temizle", geri_yukle=str(yol), verbosity=0)
            borsa.refresh_from_db()
            self.assertEqual(borsa.onay, Konu.ONAY_RET)

    def test_editor_onayi_temizlige_girmez(self):
        borsa = self._onayli_borsa(onaylayan=self.editor)
        with tempfile.TemporaryDirectory() as klasor:
            call_command("konu_temizle", yaz=str(Path(klasor) / "g.json"), verbosity=0)
        borsa.refresh_from_db()
        self.assertEqual(borsa.onay, Konu.ONAY_ONAYLI)

    # --- 4. sürüyor
    def test_suruyor_okuma_aninda(self):
        bugun = timezone.localdate()
        konu = Konu(ad="x", slug="x", acik=True, onay=Konu.ONAY_ONAYLI,
                    baslangic=bugun - timedelta(days=50), bitis=bugun - timedelta(days=5))
        self.assertTrue(konu.suruyor)
        konu.bitis = bugun - timedelta(days=Konu.SURUYOR_GUN + 1)
        self.assertFalse(konu.suruyor)
        konu.bitis, konu.acik = bugun, False         # editör kapattı
        self.assertFalse(konu.suruyor)

    def test_tarama_acik_yazar_sayfa_hesaplar(self):
        call_command("konu_tara", onay_esigi=0, verbosity=0)
        konu = Konu.objects.get()
        self.assertTrue(konu.acik)                    # kapatılmadı
        self.assertFalse(konu.suruyor)                # son haber Mart 2026
        self.assertEqual(Konu.surenler().count(), 0)
        yanit = self.client.get(konu.get_absolute_url())
        self.assertNotContains(yanit, ">SÜRÜYOR<")
        self.assertContains(yanit, "Kapandı")
        Konu.objects.filter(pk=konu.pk).update(bitis=timezone.localdate())
        self.assertEqual(Konu.surenler().count(), 1)
        self.assertContains(self.client.get("/konular"), "1 sürüyor")


# ---------------------------------------------------------------- 5. K2
def model_paketi(govde_metni, **kaynak):
    """`cli` sağlayıcısının biçiminde küçük bir model paketi."""
    paket = paket_kur(
        uretim={"saglayici": "cli", "model": "claude-test", "surum": "1.0"},
        kaynak={"orijinal_govde": (
            "Bursa Büyükşehir Belediyesi 12 Mart'ta 45 milyon liralık ihale yaptı. "
            "Hattın yüzde 80'i bitti. Toplam 10.000 metre boru döşendi. "
            "Üç mahalle etkilendi. Toplantı 14.30'da başladı."), **kaynak},
        taslak={
            "baslik_secenekleri": [{"metin": "Kollektör hattında ihale tamam",
                                    "gerekce": "Düz"}],
            "spot": "Bursa Büyükşehir Belediyesi'nin ihalesi tamamlandı.",
            "uc_madde": ["İhale yapıldı.", "Boru döşendi.", "Mahalleler etkilendi."],
            "govde": [{"tur": "paragraf", "metin": govde_metni},
                      {"tur": "paragraf", "metin": "İkinci paragraf burada."}],
            "etiketler": ["ihale", "kollektör", "nilüfer"],
            "kaynak_atfi": "Örnek Yayın", "okuma_suresi_dk": 1,
        })
    return paket


class OlguDenetimi(SimpleTestCase):

    def test_kaynakta_olan_olgu_bulgu_degil(self):
        paket = model_paketi(
            "Bursa Büyükşehir Belediyesi'nin 12 Mart'taki 45 milyon liralık ihalesi "
            "sonuçlandı. Hattın %80'i tamam; 10 bin metre boru döşendi, 3 mahalle "
            "etkilendi. Toplantı 14:30'da başladı.")
        self.assertEqual(denetim.olgu_bulgulari(paket), [])

    def test_uydurma_olgular_bulgu(self):
        paket = model_paketi(
            "Toplantıda Ahmet Yılmaz konuştu. İhale 13 Nisan 2026'da imzalandı; "
            "maliyet yüzde 20 arttı ve 57 işçi çalıştı. Kapanış 16.45'te yapıldı.")
        bulgular = {(b["tur"], b["deger"]) for b in denetim.olgu_bulgulari(paket)}
        self.assertIn(("ozel_ad", "Ahmet Yılmaz"), bulgular)
        self.assertIn(("tarih", "13 Nisan 2026"), bulgular)
        self.assertIn(("yuzde", "yüzde 20"), bulgular)
        self.assertIn(("sayi", "57"), bulgular)
        self.assertIn(("saat", "16.45"), bulgular)
        # "Toplantıda" cümle başı, ekli sözcük: ada dahil edilmez
        self.assertNotIn(("ozel_ad", "Toplantıda Ahmet Yılmaz"), bulgular)

    def test_kural_denetimine_girer_iskelete_girmez(self):
        paket = model_paketi("Ahmet Yılmaz 57 kişiyle geldi.")
        self.assertTrue(any(b.startswith("K2 ") for b in
                            denetim.kural_denetimi(paket, denetim.hal_bul(paket))))
        self.assertEqual(denetim.olgu_bulgulari(paket_kur()), [])   # kural iskeleti boş


class KapiVeKoken(TestCase):

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
        cls.kategori = KategoriTur.objects.get(tur=Kategori.TUR_HABER, slug="gundem").kategori
        cls.etiket = Etiket.objects.create(ad="K2", slug="k2")
        cls.kaynak = Kaynak.objects.create(ad="K2 Ajansı", tur=Kaynak.TUR_AJANS)
        cls.editor = User.objects.create_user("k2-editor")
        cls.editor.groups.add(Group.objects.get(name="Editör"))

    def _taslak(self, govde="Ahmet Yılmaz 57 kişiyle geldi."):
        haber, notlar = yz_kopru.taslak_yaz(model_paketi(govde), self.editor)
        return haber, notlar

    def _yayin_verisi(self, haber, **ek):
        veri = {
            "baslik": haber.baslik, "spot": haber.spot or "Spot metni.",
            "govde": haber.govde, "kategori": self.kategori.pk,
            "etiketler": self.etiket.ad, "kaynak_turu": Haber.KAYNAK_AJANS,
            "kaynaklar": [self.kaynak.pk], "hazirlik": "hazir",
            "durum": Haber.DURUM_AKTIF,
            "yayin_zamani": timezone.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        veri.update(ek)
        return veri

    def test_koken_kaydi_ve_incelemede(self):
        haber, notlar = self._taslak()
        self.assertEqual(haber.hazirlik, "incelemede")
        koken = YzKoken.objects.get(haber=haber)
        self.assertEqual((koken.saglayici, koken.model), ("cli", "claude-test"))
        self.assertIn("Ahmet Yılmaz", koken.uretilen_metin)
        self.assertEqual(koken.denetim["hal"], "model")
        degerler = set(koken.bulgular.values_list("deger", flat=True))
        self.assertTrue({"Ahmet Yılmaz", "57"} <= degerler, degerler)
        self.assertTrue(any("K2" in n for n in notlar), notlar)
        self.assertTrue(any("olgu denetimi" in e for e in yayin_kapisi.haber_eksikleri(haber)))

    def test_temiz_model_taslagi_kapidan_k2_ile_takilmaz(self):
        haber, _ = self._taslak("Bursa Büyükşehir Belediyesi ihaleyi bitirdi.")
        self.assertEqual(haber.hazirlik, "taslak")
        self.assertEqual(yz_koken.acik_k2_sayisi(haber.pk), 0)

    def test_kural_taslaginda_k2_yok_koken_var(self):
        haber, _ = yz_kopru.taslak_yaz(paket_kur(), self.editor)
        koken = YzKoken.objects.get(haber=haber)
        self.assertEqual(koken.saglayici, "kural")
        self.assertEqual(koken.uretilen_metin, "")
        self.assertFalse(koken.bulgular.exists())

    def test_form_yayini_k2_kapanmadan_olmaz_kapaninca_olur(self):
        haber, _ = self._taslak()
        self.client.force_login(self.editor)
        yanit = self.client.post(f"/panel/haber/{haber.pk}", self._yayin_verisi(haber))
        self.assertEqual(yanit.status_code, 200)
        self.assertContains(yanit, "açık K2 bulgusu")
        haber.refresh_from_db()
        self.assertEqual(haber.durum, Haber.DURUM_PASIF)

        # Tek tek kapatma; GET kapatmaz
        bulgular = list(YzBulgu.objects.filter(koken__haber=haber))
        self.client.get(f"/panel/yz-taslak/{haber.pk}/bulgu/{bulgular[0].pk}")
        self.assertFalse(YzBulgu.objects.get(pk=bulgular[0].pk).kapandi)
        sayfa = self.client.get(f"/panel/yz-taslak/{haber.pk}")
        self.assertContains(sayfa, "Kontrol ettim")
        for b in bulgular:
            yanit = self.client.post(f"/panel/yz-taslak/{haber.pk}/bulgu/{b.pk}")
            self.assertEqual(yanit.status_code, 302)
        b = YzBulgu.objects.get(pk=bulgular[0].pk)
        self.assertTrue(b.kapandi)
        self.assertEqual(b.kapatan, self.editor)
        self.assertTrue(LogKaydi.objects.filter(fiil="yz_bulgu_kapatma",
                                                hedef_id=haber.pk).exists())

        yeni_govde = haber.govde + "<p>Editörün eklediği üçüncü paragraf.</p>"
        yanit = self.client.post(f"/panel/haber/{haber.pk}",
                                 self._yayin_verisi(haber, govde=yeni_govde))
        self.assertEqual(yanit.status_code, 302, getattr(yanit, "context", None)
                         and yanit.context["form"].errors)
        haber.refresh_from_db()
        self.assertEqual(haber.durum, Haber.DURUM_AKTIF)
        koken = YzKoken.objects.get(haber=haber)
        self.assertIsNotNone(koken.yayin_zamani)
        self.assertEqual(koken.yayinlayan, self.editor)
        self.assertGreater(koken.benzerlik, 0.3)
        self.assertLess(koken.benzerlik, 1.0)
        self.assertAlmostEqual(koken.degisim_orani, 1 - koken.benzerlik, places=4)

    def test_toplu_yayin_ve_hazirlik_k2_atlar(self):
        haber, _ = self._taslak()
        Haber.objects.filter(pk=haber.pk).update(
            slug="k2-haber", spot="Spot.", kaynak_turu=Haber.KAYNAK_AJANS)
        haber.etiketler.add(self.etiket)
        haber.kaynaklar.add(self.kaynak)
        self.client.force_login(self.editor)
        self.client.post("/panel/toplu", {"fiil": "hazirlik", "hazirlik_degeri": "hazir",
                                          "kimlikler": [haber.pk]})
        haber.refresh_from_db()
        self.assertEqual(haber.hazirlik, "incelemede")
        self.client.post("/panel/toplu", {"fiil": "yayina_al", "kimlikler": [haber.pk]})
        haber.refresh_from_db()
        self.assertEqual(haber.durum, Haber.DURUM_PASIF)
        for b in YzBulgu.objects.filter(koken__haber=haber):
            yz_koken.bulgu_kapat(b, self.editor)
        self.client.post("/panel/toplu", {"fiil": "yayina_al", "kimlikler": [haber.pk]})
        haber.refresh_from_db()
        self.assertEqual(haber.durum, Haber.DURUM_AKTIF)
        self.assertIsNotNone(YzKoken.objects.get(haber=haber).benzerlik)

    def test_denetim_calismazsa_kapi_kapali(self):
        with patch.object(denetim, "olgu_bulgulari", side_effect=RuntimeError("bozuk")), \
                self.assertLogs("bh.yz_kopru", level="ERROR"):
            haber, _ = self._taslak("Temiz metin.")
        self.assertEqual(list(YzBulgu.objects.filter(koken__haber=haber)
                              .values_list("tur", flat=True)), ["denetim"])
        self.assertEqual(yz_koken.acik_k2_sayisi(haber.pk), 1)

    def test_benzerlik_kelime_duzeyi(self):
        self.assertEqual(yz_koken.benzerlik("bir iki üç", "bir iki üç"), 1.0)
        self.assertEqual(yz_koken.benzerlik("", "yeni metin"), 0.0)
        self.assertEqual(yz_koken.duz_metin("Başlık", "Spot", "<p>A &amp; B</p>"),
                         "Başlık\nSpot\nA & B")
