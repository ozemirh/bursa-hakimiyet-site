# -*- coding: utf-8 -*-
"""Konu takibi — motor, komut, site sayfaları ve panel (5 Eylül 2026).

Motor testleri veritabanı görmez: sentetik bir derlem kurulur, içinde bir
gerçek dosya (Ece Gürel, 6 haber, 5 gün), bir periyodik tür (TÜİK, aylık)
ve bir tek günlük olay (Maydonoz Döner, 5 haber aynı gün) vardır. Yalnız
ilkinin konu sayılması beklenir — kullanıcının 5 Eylül kararı budur.
"""

from datetime import date, timedelta

from django.contrib.auth.models import Group, User
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from taksonomi.models import Kategori, KategoriTur

from . import konu_motoru
from .models import Haber, Konu, KonuHaber

PAROLA = "deneme-parola-123"
GUN0 = date(2026, 3, 4)

DOSYA = [
    (0, "Belgrad Ormanı'nda kaybolan Ece Gürel aranıyor"),
    (0, "Kayıp mimar Ece Gürel için arama çalışması sürüyor"),
    (1, "Arama ekipleri Ece Gürel'in eşyalarını buldu"),
    (2, "Kayıp mimar Ece Gürel sağ bulundu"),
    (3, "Hastaneye kaldırılan Ece Gürel hayatını kaybetti"),
    (4, "Mimar Ece Gürel'in cenazesi toprağa verildi"),
]
PERIYODIK = [(30 * n, "TÜİK enflasyon rakamlarını açıkladı") for n in range(6)]
TEK_GUN = [(10, f"Maydonoz Döner zehirlenmesinde {n} kişi hastanelik oldu")
           for n in range(5)]
DOLGU_KELIME = ["yol", "park", "okul", "cami", "köprü", "kavşak", "pazar",
                "sahil", "tesis", "meydan"]


def sentetik():
    """`(kimlik, baslik, tarih)` listesi; dolgu başlıklar birbirine bağlanmaz."""
    kayitlar = []
    kimlik = 1000
    for i in range(400):
        kelime = DOLGU_KELIME[i % len(DOLGU_KELIME)]
        kayitlar.append((kimlik, f"Bursa'da {i}. mahallede {kelime} çalışması başladı",
                         GUN0 + timedelta(days=i % 180)))
        kimlik += 1
    for grup in (DOSYA, PERIYODIK, TEK_GUN):
        for gun, baslik in grup:
            kayitlar.append((kimlik, baslik, GUN0 + timedelta(days=gun)))
            kimlik += 1
    return kayitlar


class MotorTesti(TestCase):
    def test_rutin_kaliplari(self):
        self.assertTrue(konu_motoru.rutin_mu("Meteoroloji Bursa için gün gün açıkladı"))
        self.assertTrue(konu_motoru.rutin_mu("TÜİK enflasyon rakamlarını açıkladı"))
        self.assertTrue(konu_motoru.rutin_mu("Dolar ne kadar oldu? (10 Mart 2025)"))
        self.assertTrue(konu_motoru.rutin_mu("Bursa'da nöbetçi eczaneler"))
        self.assertFalse(konu_motoru.rutin_mu("Ece Gürel'in cenazesi toprağa verildi"))
        self.assertFalse(konu_motoru.rutin_mu("Bozbey rüşvet soruşturmasında tutuklandı"))

    def test_parcala_kesme_ve_unvan(self):
        kokler = [p.kok for p in konu_motoru.parcala("Cumhurbaşkanı Erdoğan, Bozbey'in tutuklanmasını değerlendirdi")]
        self.assertIn("bozbey", kokler)
        self.assertIn("erdoğan", kokler)
        self.assertNotIn("cumhurbaşkan", kokler)
        self.assertNotIn("cumhurbaşkanı", kokler)

    def test_ikili_ad(self):
        parcalar = konu_motoru.parcala("Kayıp mimar Ece Gürel sağ bulundu")
        self.assertEqual(konu_motoru.ikililer(parcalar), [("ece_gürel", "Ece Gürel")])

    def test_yalniz_gercek_dosya_konu_olur(self):
        konular = konu_motoru.tara(sentetik())
        adlar = [k.ad for k in konular]
        self.assertEqual(len(konular), 1, adlar)
        konu = konular[0]
        self.assertIn("Ece Gürel", konu.ad)
        self.assertEqual(len(konu.uyeler), 6)
        self.assertEqual(konu.baslangic, GUN0)
        self.assertEqual(konu.bitis, GUN0 + timedelta(days=4))
        self.assertGreaterEqual(konu.guven, 60)
        # Periyodik ve tek günlük olay hiçbir konuda yok
        basliklar = " ".join(h.baslik for h in konu.uyeler)
        self.assertNotIn("TÜİK", basliklar)
        self.assertNotIn("Maydonoz", basliklar)

    def test_sirasiz_girdi_reddedilir(self):
        m = konu_motoru.Motor()
        m.say("Ece Gürel bulundu")
        with self.assertRaises(ValueError):
            m.zincirle([(1, "Ece Gürel bulundu", GUN0),
                        (2, "Ece Gürel kayıp", GUN0 - timedelta(days=1))])


class VeriTemel(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("taksonomi_kur", verbosity=0)
        call_command("roller_kur", verbosity=0)
        cls.kategori = KategoriTur.objects.get(
            tur=Kategori.TUR_HABER, slug="gundem").kategori
        cls.kullanicilar = {}
        for sira, rol in enumerate(("Muhabir", "Editör", "Sayfa Sekreteri",
                                    "İlan Sorumlusu", "Yayın Yönetmeni")):
            k = User.objects.create_user(f"k{sira}", password=PAROLA)
            k.groups.add(Group.objects.get(name=rol))
            cls.kullanicilar[rol] = k
        cls.haberler = []
        saat = timezone.now().replace(hour=10, minute=0, second=0, microsecond=0)
        for kimlik, baslik, tarih in sentetik():
            zaman = saat.replace(year=tarih.year, month=tarih.month, day=tarih.day)
            cls.haberler.append(Haber.objects.create(
                id=kimlik, slug=f"h-{kimlik}", baslik=baslik, kategori=cls.kategori,
                durum=Haber.DURUM_AKTIF, yayin_zamani=zaman))
        cls.dosya_ids = [h.id for h in cls.haberler if "Ece Gürel" in h.baslik]


class KomutTesti(VeriTemel):
    def test_tarama_oneri_yazar(self):
        call_command("konu_tara", verbosity=0)
        self.assertEqual(Konu.objects.count(), 1)
        konu = Konu.objects.get()
        self.assertEqual(konu.onay, Konu.ONAY_BEKLIYOR)
        self.assertEqual(konu.kaynak, Konu.KAYNAK_MOTOR)
        self.assertEqual(konu.haber_sayisi, 6)
        self.assertEqual(set(konu.baglar.values_list("haber_id", flat=True)),
                         set(self.dosya_ids))
        self.assertTrue(konu.slug.startswith("ece-gurel-2026-03"))
        # Yeniden çalıştırma bekleyeni silip yeniden yazar: sayı sabit
        call_command("konu_tara", verbosity=0)
        self.assertEqual(Konu.objects.count(), 1)

    def test_onay_esigi(self):
        call_command("konu_tara", onay_esigi=0, verbosity=0)
        konu = Konu.objects.get()
        self.assertEqual(konu.onay, Konu.ONAY_ONAYLI)
        # Onaylı dosya yeniden taramada korunur ve örtüşen öneri yazılmaz
        call_command("konu_tara", verbosity=0)
        self.assertEqual(Konu.objects.count(), 1)
        self.assertEqual(Konu.objects.get().onay, Konu.ONAY_ONAYLI)

    def test_sifirla_komut_onayini_siler_editor_onayini_korur(self):
        call_command("konu_tara", onay_esigi=0, verbosity=0)
        call_command("konu_tara", sifirla=True, verbosity=0)
        self.assertEqual(Konu.objects.get().onay, Konu.ONAY_BEKLIYOR)
        konu = Konu.objects.get()
        konu.onay, konu.onaylayan = Konu.ONAY_ONAYLI, self.kullanicilar["Editör"]
        konu.save()
        call_command("konu_tara", sifirla=True, verbosity=0)
        self.assertEqual(Konu.objects.count(), 1)
        self.assertEqual(Konu.objects.get().pk, konu.pk)

    def test_kuru_calisma_yazmaz(self):
        call_command("konu_tara", kuru=True, verbosity=0)
        self.assertEqual(Konu.objects.count(), 0)

    def test_toplu_onay_donem_ve_geri_alma(self):
        """`konu_onayla --son` dönem dosyalarını açar, `--geri` yalnız komutun
        açtığını kapatır; editör onayı korunur."""
        call_command("konu_tara", verbosity=0)
        konu = Konu.objects.get()   # biter: GUN0 + 4 gün (2026-03-08)
        call_command("konu_onayla", son="2026-03-07", verbosity=0)
        konu.refresh_from_db()
        self.assertEqual(konu.onay, Konu.ONAY_BEKLIYOR)
        call_command("konu_onayla", son="2026-03-08", kuru=True, verbosity=0)
        konu.refresh_from_db()
        self.assertEqual(konu.onay, Konu.ONAY_BEKLIYOR)
        call_command("konu_onayla", son="2026-03-08", verbosity=0)
        konu.refresh_from_db()
        self.assertEqual(konu.onay, Konu.ONAY_ONAYLI)
        self.assertIsNotNone(konu.onay_zamani)
        call_command("konu_onayla", son="2026-12-31", geri=True, verbosity=0)
        konu.refresh_from_db()
        self.assertEqual(konu.onay, Konu.ONAY_BEKLIYOR)
        # Editör onayı geri alınmaz
        konu.onay, konu.onaylayan = Konu.ONAY_ONAYLI, self.kullanicilar["Editör"]
        konu.save()
        call_command("konu_onayla", son="2026-12-31", geri=True, verbosity=0)
        konu.refresh_from_db()
        self.assertEqual(konu.onay, Konu.ONAY_ONAYLI)


class SiteTesti(VeriTemel):
    def setUp(self):
        call_command("konu_tara", verbosity=0)
        self.konu = Konu.objects.get()
        self.haber = Haber.objects.get(pk=self.dosya_ids[2])

    def test_onaysiz_dosya_sitede_yok(self):
        self.assertEqual(self.client.get(f"/konu/{self.konu.slug}").status_code, 404)
        yanit = self.client.get("/konular")
        self.assertEqual(yanit.status_code, 200)
        self.assertNotContains(yanit, self.konu.ad)
        yanit = self.client.get(self.haber.get_absolute_url())
        self.assertEqual(yanit.status_code, 200)
        self.assertNotContains(yanit, "KONUNUN AKIŞI")

    def test_ilgili_haberler_basliga_gore(self):
        """Dosya onaysızken bile ilgili kutusu Ece Gürel haberlerini bulur;
        kalan yerler aynı kategoriden doldurulur, toplam 6."""
        yanit = self.client.get(self.haber.get_absolute_url())
        ilgili = list(yanit.context["ilgili"])
        self.assertEqual(len(ilgili), 6)
        self.assertNotIn(self.haber.pk, [h.pk for h in ilgili])
        gurel = [h for h in ilgili if "Ece Gürel" in h.baslik]
        self.assertEqual(len(gurel), 5)
        self.assertEqual([h.pk for h in ilgili[:5]], [h.pk for h in gurel])

    def test_ilgili_akistakini_tekrarlamaz(self):
        self.konu.onay = Konu.ONAY_ONAYLI
        self.konu.save()
        yanit = self.client.get(self.haber.get_absolute_url())
        akis = yanit.context["konu_akisi"]
        gorunen = {h.pk for h in akis["oncekiler"]} | {h.pk for h in akis["sonrakiler"]}
        ilgili = {h.pk for h in yanit.context["ilgili"]}
        self.assertFalse(gorunen & ilgili)
        self.assertEqual(len(ilgili), 6)

    def test_onayli_dosya_sayfasi_ve_akis(self):
        self.konu.onay = Konu.ONAY_ONAYLI
        self.konu.save()
        yanit = self.client.get(f"/konu/{self.konu.slug}")
        self.assertEqual(yanit.status_code, 200)
        for kimlik in self.dosya_ids:
            self.assertContains(yanit, f"-{kimlik}\"")
        yanit = self.client.get("/konular")
        self.assertContains(yanit, self.konu.ad)
        yanit = self.client.get(self.haber.get_absolute_url())
        self.assertContains(yanit, "KONUNUN AKIŞI")
        self.assertContains(yanit, f"/konu/{self.konu.slug}")
        # Okunan haber listede işaretli ve bağlantı değil
        self.assertContains(yanit, 'class="simdi" aria-current="page"')
        akis = yanit.context["konu_akisi"]
        self.assertEqual(len(akis["oncekiler"]), 2)
        self.assertEqual(len(akis["sonrakiler"]), 2)
        self.assertEqual(akis["gizli_sonra"], 1)
        self.assertEqual(akis["toplam"], 6)
        # Dosyanın ilk haberinde pencere ileri kayar: yine 5 satır
        ilk = Haber.objects.get(pk=self.dosya_ids[0])
        akis = self.client.get(ilk.get_absolute_url()).context["konu_akisi"]
        self.assertEqual((len(akis["oncekiler"]), len(akis["sonrakiler"])), (0, 4))
        son = Haber.objects.get(pk=self.dosya_ids[-1])
        akis = self.client.get(son.get_absolute_url()).context["konu_akisi"]
        self.assertEqual((len(akis["oncekiler"]), len(akis["sonrakiler"])), (4, 0))


class PanelTesti(VeriTemel):
    def setUp(self):
        call_command("konu_tara", verbosity=0)
        self.konu = Konu.objects.get()

    def _gir(self, rol):
        self.client.login(username=self.kullanicilar[rol].username, password=PAROLA)

    def test_yetki(self):
        for rol, kod in (("Editör", 200), ("Yayın Yönetmeni", 200),
                         ("Muhabir", 403), ("Sayfa Sekreteri", 403),
                         ("İlan Sorumlusu", 403)):
            self._gir(rol)
            self.assertEqual(self.client.get("/panel/konular").status_code, kod, rol)
            self.assertEqual(self.client.get(f"/panel/konu/{self.konu.pk}").status_code, kod, rol)
            self.client.logout()
        self.assertEqual(self.client.get("/panel/konular").status_code, 302)

    def test_liste_ve_menu(self):
        self._gir("Editör")
        yanit = self.client.get("/panel/konular")
        self.assertContains(yanit, self.konu.ad)
        self.assertContains(yanit, "Konu Takibi")
        self.assertContains(yanit, "Onay bekleyen öneri: 1")

    def test_onay_yalniz_post(self):
        self._gir("Editör")
        self.client.get(f"/panel/konu/{self.konu.pk}/karar")
        self.konu.refresh_from_db()
        self.assertEqual(self.konu.onay, Konu.ONAY_BEKLIYOR)
        self.client.post(f"/panel/konu/{self.konu.pk}/karar", {"karar": "onayli"})
        self.konu.refresh_from_db()
        self.assertEqual(self.konu.onay, Konu.ONAY_ONAYLI)
        self.assertEqual(self.konu.onaylayan, self.kullanicilar["Editör"])
        self.assertIsNotNone(self.konu.onay_zamani)
        self.client.post(f"/panel/konu/{self.konu.pk}/karar", {"karar": "ret"})
        self.konu.refresh_from_db()
        self.assertEqual(self.konu.onay, Konu.ONAY_RET)

    def test_haber_cikar_ve_kunye(self):
        self._gir("Yayın Yönetmeni")
        haber_id = self.dosya_ids[0]
        self.client.post(f"/panel/konu/{self.konu.pk}/cikar/{haber_id}")
        self.konu.refresh_from_db()
        self.assertEqual(self.konu.haber_sayisi, 5)
        self.assertFalse(KonuHaber.objects.filter(konu=self.konu, haber_id=haber_id).exists())
        self.assertEqual(self.konu.baslangic, GUN0)
        yanit = self.client.post(f"/panel/konu/{self.konu.pk}", {
            "ad": "Ece Gürel dosyası", "ozet": "Belgrad Ormanı'nda kaybolan mimar.",
            "hassas_uyari": "", "acik": ""}, follow=True)
        self.assertEqual(yanit.status_code, 200)
        self.konu.refresh_from_db()
        self.assertEqual(self.konu.ad, "Ece Gürel dosyası")
        self.assertContains(yanit, "Ece Gürel dosyası")
