"""Paket H — masanın kararları siteye ulaşıyor mu (19 Ekim 2026).

DEGERLENDIRME-2026-10 §3 bulgu 5: manşet bayrakları sitede 0 kez okunuyordu,
son dakika bandı `SonDakika` tablosuna bakmıyordu, "Yayına hazır" haber masa
ekranında görünmüyordu, imza sabit "Haber Merkezi"ydi, düz metin gövde tek
paragraf basılıyordu. Her test GERÇEK kayıt yaratır ve sayfayı ya da paneli
gerçekten ister.
"""

from datetime import timedelta

from django.contrib.auth.models import Group, User
from django.core.management import call_command
from django.test import Client, TestCase, override_settings
from django.utils import timezone

from taksonomi.models import Etiket, Ilce, Kategori, KategoriTur, Kaynak

from . import anasayfa_dizilimi as ad
from .models import Haber, LogKaydi, SonDakika
from .tests_basarim import SAYFA_ACIK

TABAN = 5_900_000


class Temel(TestCase):

    @classmethod
    def setUpTestData(cls):
        call_command("taksonomi_kur", verbosity=0)
        call_command("roller_kur", verbosity=0)

        def kat(slug):
            return KategoriTur.objects.get(tur=Kategori.TUR_HABER, slug=slug).kategori
        cls.gundem, cls.bursa, cls.spor = kat("gundem"), kat("bursa"), kat("spor")
        cls.saglik = kat("saglik")
        cls.nilufer = Ilce.objects.get(slug="nilufer")
        cls.etiket = Etiket.objects.create(ad="Masa etiketi", slug="masa-etiketi")
        cls.ajans = Kaynak.objects.create(ad="Anadolu Ajansı", tur=Kaynak.TUR_AJANS)
        cls.dis = Kaynak.objects.create(ad="Sözcü", tur=Kaynak.TUR_DIS_YAYIN)
        cls.roller = {}
        for rol in ("Muhabir", "Editör", "Sayfa Sekreteri", "Yayın Yönetmeni"):
            k = User.objects.create_user(f"h-{len(cls.roller)}")
            k.groups.add(Group.objects.get(name=rol))
            cls.roller[rol] = k

    _sayac = 0

    def haber(self, baslik, *, kategori=None, dakika=0, ilce=None, **alanlar):
        Temel._sayac += 1
        kimlik = TABAN + Temel._sayac
        varsayilan = dict(
            id=kimlik, slug=alanlar.pop("slug", f"h-{kimlik}"), baslik=baslik,
            kategori=kategori or self.gundem, ilce=ilce, spot="Spot",
            govde="<p>Bir.</p><p>İki.</p>", durum=Haber.DURUM_AKTIF,
            kaynak_turu=Haber.KAYNAK_MUHABIR, muhabir="",
            yayin_zamani=timezone.now() - timedelta(minutes=dakika))
        varsayilan.update(alanlar)
        h = Haber.objects.create(**varsayilan)
        h.etiketler.add(self.etiket)
        return h

    def bayrak_logu(self, haber, alan, saat_once):
        LogKaydi.objects.create(fiil="mansete_alma", hedef_tur="haber", hedef_id=haber.pk,
                                sonrasi={alan: True},
                                zaman=timezone.now() - timedelta(hours=saat_once))

    def gir(self, rol):
        self.client.force_login(self.roller[rol])


# --------------------------------------------------------------------------
# 1. Bayraklı manşet ve düşüş kuralı

class Dizilim(Temel):

    def test_bayrakli_ana_manset_onde_ve_bayrak_sirasiyla(self):
        """Eski haber bile olsa bayrak onu öne alır; en yeni bayrak önde."""
        for n in range(20):
            self.haber(f"Yeni ulusal {n}", dakika=n)
        eski = self.haber("Dünün bayraklı haberi", dakika=60 * 20, manset_ana=True)
        daha_eski = self.haber("Bayrağı yeni verilen haber", dakika=60 * 30, manset_ana=True)
        self.bayrak_logu(eski, "manset_ana", saat_once=5)
        self.bayrak_logu(daha_eski, "manset_ana", saat_once=1)
        yanit = self.client.get("/")
        manset = [h.pk for h in yanit.context["manset"]]
        self.assertEqual(manset[:2], [daha_eski.pk, eski.pk])
        self.assertEqual(len(manset), ad.MANSET)

    def test_logsuz_bayrak_yayin_zamanina_gore(self):
        a = self.haber("Bayraklı A", dakika=10, manset_ana=True)
        b = self.haber("Bayraklı B", dakika=5, manset_ana=True)
        d = ad.kur()
        self.assertEqual([h.pk for h in d.manset[:2]], [b.pk, a.pk])
        self.assertTrue(all(k.neden == "bayrak" for k in d.kalemler[:2]))

    def test_tepe_dortluye_kare_yan_slayta(self):
        for n in range(50):
            self.haber(f"Dolgu {n}", dakika=n)
        tepe = self.haber("Tepe manşet haberi", dakika=500, manset_tepe=True)
        kare = self.haber("Kare manşet haberi", dakika=600, manset_kare=True)
        yanit = self.client.get("/")
        self.assertEqual(yanit.context["dortlu"][0].pk, tepe.pk)
        self.assertEqual(yanit.context["ikincil"][0].pk, kare.pk)
        self.assertEqual(len(yanit.context["dortlu"]), ad.DORTLU)
        self.assertEqual(len(yanit.context["ikincil"]), ad.IKINCIL)

    def test_birden_cok_bayrak_tek_yuvada_bir_kez(self):
        h = self.haber("Hem ana hem kare", manset_ana=True, manset_kare=True)
        d = ad.kur()
        self.assertIn(h, d.manset)
        self.assertNotIn(h, d.ikincil)
        self.assertEqual(d.kullanilan.count(h.pk), 1)

    def test_suresi_dolan_bayrak_onceligini_yitirir(self):
        for n in range(20):
            self.haber(f"Taze {n}", dakika=n)
        bayat = self.haber("Unutulmuş bayrak", dakika=60 * 60, manset_ana=True)
        self.bayrak_logu(bayat, "manset_ana", saat_once=49)
        d = ad.kur()
        self.assertNotIn(bayat, d.manset)
        self.assertEqual([x.neden for x in d.disarida if x.haber.pk == bayat.pk],
                         ["suresi_doldu"])
        with override_settings(MANSET_BAYRAK_SAAT=72):
            self.assertEqual(ad.kur().manset[0].pk, bayat.pk)

    def test_yayinda_olmayan_bayrak_sitede_yok_panelde_gerekceli(self):
        pasif = self.haber("Yayından çekilmiş manşet", manset_ana=True,
                           durum=Haber.DURUM_PASIF)
        self.haber("Sıradan haber")
        d = ad.kur()
        self.assertNotIn(pasif.pk, d.kullanilan)
        self.assertEqual([x.neden for x in d.disarida], ["yayinda_degil"])

    def test_dusus_kurali_ilk_15te_en_az_10_bursa(self):
        """Ulusal haberler daha yeni olsa da ilk 15'in en az 10'u Bursa."""
        for n in range(20):
            self.haber(f"Ulusal gündem {n}", dakika=n)
        bursalilar = [self.haber(f"Yerel {n}", kategori=self.bursa, dakika=100 + n)
                      for n in range(12)]
        d = ad.kur()
        bursa_kimlik = {h.pk for h in bursalilar}
        ilk15 = [h.pk for h in d.manset]
        self.assertEqual(len(ilk15), 15)
        self.assertEqual(sum(1 for k in ilk15 if k in bursa_kimlik), 10)
        # İkinci kademe: Bursa haberleri slaytta önce.
        self.assertTrue(all(k in bursa_kimlik for k in ilk15[:10]))
        # Bursa grubu kendi içinde en yeniden eskiye.
        self.assertEqual(ilk15[:10], [h.pk for h in bursalilar[:10]])
        self.assertEqual(d.bursa_sayisi(), 10)

    @override_settings(MANSET_BURSA_ORANI="5/15")
    def test_oran_ayardan(self):
        for n in range(20):
            self.haber(f"Ulusal {n}", dakika=n)
        bursalilar = {self.haber(f"Yerel {n}", kategori=self.bursa, dakika=100 + n).pk
                      for n in range(12)}
        d = ad.kur()
        self.assertEqual(sum(1 for h in d.manset if h.pk in bursalilar), 5)
        self.assertEqual(d.en_az_bursa, 5)

    def test_bayrakli_bursa_haberi_orana_dahil(self):
        for n in range(20):
            self.haber(f"Ulusal {n}", dakika=n)
        yerel = [self.haber(f"Yerel {n}", kategori=self.bursa, dakika=100 + n)
                 for n in range(12)]
        bayrakli = self.haber("Bayraklı Bursa", kategori=self.bursa, dakika=900,
                              manset_ana=True)
        d = ad.kur()
        self.assertEqual(d.manset[0].pk, bayrakli.pk)
        bursa = {h.pk for h in yerel} | {bayrakli.pk}
        self.assertEqual(sum(1 for h in d.manset if h.pk in bursa), 10)

    def test_bursa_siniflamasi(self):
        self.assertTrue(ad.bursali_mi(self.haber("Kategoriden", kategori=self.bursa)))
        self.assertTrue(ad.bursali_mi(self.haber("İlçeden", ilce=self.nilufer)))
        self.assertTrue(ad.bursali_mi(self.haber("Nilüfer'de su kesintisi")))
        self.assertTrue(ad.bursali_mi(self.haber("Bursaspor kampa girdi")))
        self.assertTrue(ad.bursali_mi(self.haber("İNEGÖL'DE YANGIN")))
        # "Yıldırım" başlıkta aranmaz: yaygın soyad ve sözcük.
        self.assertFalse(ad.bursali_mi(self.haber("Binali Yıldırım açıklama yaptı")))
        self.assertFalse(ad.bursali_mi(self.haber("Ankara'da toplantı")))

    def test_eczane_servis_haberi_mansete_dususle_girmez(self):
        eczane = self.haber("19 Ekim 2026 Bursa nöbetçi eczaneler", kategori=self.saglik,
                            slug="19-ekim-2026-bursa-nobetci-eczaneler")
        for n in range(5):
            self.haber(f"Haber {n}", dakika=10 + n)
        d = ad.kur()
        self.assertNotIn(eczane, d.manset + d.manset_liste + d.ikincil + d.dortlu)
        self.assertIn(eczane, d.kutular)

    def test_bloklar_tekrar_etmez(self):
        for n in range(60):
            self.haber(f"H {n}", dakika=n, kategori=self.bursa if n % 3 else self.gundem,
                       manset_ana=n in (5, 40), manset_tepe=n == 7, manset_kare=n == 50)
        yanit = self.client.get("/")
        kimlikler = [h.pk for a in ("manset", "manset_liste", "ikincil", "dortlu",
                                    "kutular", "en_cok") for h in yanit.context[a]]
        self.assertEqual(len(kimlikler), len(set(kimlikler)))


# --------------------------------------------------------------------------
# 2. Panelin manşet ekranı = anasayfanın dizilimi; önbellek anında düşer

class PanelVeOnbellek(Temel):

    def test_manset_ekrani_anasayfayla_ayni_dizilimi_gosterir(self):
        for n in range(20):
            self.haber(f"Ulusal {n}", dakika=n)
        for n in range(12):
            self.haber(f"Yerel {n}", kategori=self.bursa, dakika=100 + n)
        bayrakli = self.haber("Panelde görünen bayrak", manset_ana=True, dakika=999)
        site = [h.pk for h in self.client.get("/").context["manset"]]
        self.gir("Sayfa Sekreteri")
        yanit = self.client.get("/panel/mansetler")
        self.assertEqual(yanit.status_code, 200)
        dizilim = yanit.context["dizilim"]
        panel = [s["haber"].pk for y in dizilim["yuvalar"] if y["kod"] == "manset"
                 for s in y["satirlar"]]
        self.assertEqual(panel, site)
        self.assertEqual(dizilim["bursa"], 10)
        self.assertContains(yanit, "Anasayfada şu an")
        self.assertContains(yanit, "Panelde görünen bayrak")
        self.assertContains(yanit, "Düşüş · Bursa")

    def test_editor_manset_ekranini_goremez(self):
        self.gir("Editör")
        self.assertEqual(self.client.get("/panel/mansetler").status_code, 403)


@SAYFA_ACIK
class BayrakOnbellegi(Temel):

    def test_toplu_manset_bayragi_anasayfayi_aninda_degistirir(self):
        for n in range(20):
            self.haber(f"Önbellek ulusal {n}", dakika=n)
        hedef = self.haber("Masanın seçtiği manşet", dakika=5000)
        okur = Client()
        ilk = okur.get("/")
        self.assertEqual(ilk["X-Onbellek"], "kayit")
        self.assertEqual(okur.get("/")["X-Onbellek"], "isabet")
        self.assertNotEqual(ilk.context["manset"][0].pk, hedef.pk)

        masa = Client()
        masa.force_login(self.roller["Sayfa Sekreteri"])
        masa.post("/panel/toplu", {"fiil": "mansete_al", "manset_slot": "manset_ana",
                                    "kimlikler": [hedef.pk]})
        yanit = okur.get("/")
        self.assertEqual(yanit["X-Onbellek"], "kayit")
        self.assertEqual(yanit.context["manset"][0].pk, hedef.pk)
        # Denetim kaydı yazıldı ve sıranın kaynağı o.
        self.assertTrue(LogKaydi.objects.filter(fiil="mansete_alma", hedef_id=hedef.pk).exists())

        masa.post("/panel/toplu", {"fiil": "mansetten_cikar", "kimlikler": [hedef.pk]})
        yanit = okur.get("/")
        self.assertEqual(yanit["X-Onbellek"], "kayit")
        self.assertNotEqual(yanit.context["manset"][0].pk, hedef.pk)

    def test_son_dakika_kaydi_anasayfayi_aninda_degistirir(self):
        self.haber("Sıradan haber")
        okur = Client()
        self.assertNotContains(okur.get("/"), "Deprem uyarısı")
        SonDakika.objects.create(baslik="Deprem uyarısı", adres="/gundem/x-1")
        self.assertContains(okur.get("/"), "Deprem uyarısı")


# --------------------------------------------------------------------------
# 3. Son dakika bandı

class SonDakikaBandi(Temel):

    def _bant(self, yanit):
        """Sayfa tepesindeki bant (23 Ekim 2026'dan beri anasayfada son
        dakika YALNIZ orada; kutu kalktı). Bant başlığı büyütmez."""
        metin = yanit.content.decode()
        bas = metin.index('class="sd-bant"')
        return metin[bas:metin.index("</section>", bas)]

    def test_tablodan_beslenir_ve_canli_etiketi(self):
        self.haber("Sıradan son haber")
        SonDakika.objects.create(baslik="Köprüde kaza", adres="/gundem/kopru-1")
        bant = self._bant(self.client.get("/"))
        self.assertIn("SON DAKİKA", bant)
        self.assertIn("sd-bant-nokta", bant)     # nabız: masanın kaydı
        self.assertIn("Köprüde kaza", bant)
        self.assertNotIn("Sıradan son haber", bant)

    def test_tablo_bosken_son_haberler_etiketi(self):
        """23 Ekim 2026, kullanıcı kararı: etiket masa boşken de SON DAKİKA;
        CANLI pili yalnız masanın kaydına aittir."""
        self.haber("En yeni haber")
        bant = self._bant(self.client.get("/"))
        self.assertIn("SON DAKİKA", bant)
        self.assertNotIn("SON HABERLER", bant)
        self.assertNotIn("sd-bant-nokta", bant)
        self.assertIn("En yeni haber", bant)

    def test_suresi_dolan_ve_pasif_kayit_bantta_yok(self):
        self.haber("Yedek haber")
        simdi = timezone.now()
        SonDakika.objects.create(baslik="Biten", adres="/a-1",
                                 baslangic=simdi - timedelta(hours=3),
                                 bitis=simdi - timedelta(hours=1))
        SonDakika.objects.create(baslik="Kapalı", adres="/b-1", aktif=False)
        SonDakika.objects.create(baslik="Gelecek", adres="/c-1",
                                 baslangic=simdi + timedelta(hours=1))
        bant = self._bant(self.client.get("/"))
        self.assertNotIn("sd-bant-nokta", bant)   # masa kaydı yok: yedek liste
        self.assertIn("Yedek haber", bant)
        for baslik in ("Biten", "Kapalı", "Gelecek"):
            self.assertNotIn(baslik, bant)

    def test_yayindan_cekilen_bagli_haber_dusurulur(self):
        cekilen = self.haber("Çekilen", durum=Haber.DURUM_PASIF)
        canli = self.haber("Yayındaki")
        SonDakika.objects.create(baslik="Çekilen haberin bandı", haber=cekilen)
        SonDakika.objects.create(baslik="Yayındaki haberin bandı", haber=canli)
        bant = self._bant(self.client.get("/"))
        self.assertNotIn("Çekilen haberin bandı", bant)
        self.assertIn(canli.get_absolute_url(), bant)

    def test_tehlikeli_adres_basilmaz_ve_form_reddeder(self):
        SonDakika.objects.create(baslik="Kötü", adres="javascript:alert(1)")
        self.haber("Yedek")
        self.assertNotIn("javascript:", self._bant(self.client.get("/")))
        from .formlar import SonDakikaForm
        form = SonDakikaForm(data={"baslik": "X", "adres": "javascript:alert(1)",
                                   "baslangic": timezone.now(), "sira": 0, "aktif": True})
        self.assertFalse(form.is_valid())
        self.assertIn("adres", form.errors)

    def test_eczane_servis_haberi_bantta_yok(self):
        self.haber("Gerçek haber", dakika=5)
        self.haber("19 Ekim 2026 Bursa nöbetçi eczaneler", kategori=self.saglik,
                   slug="19-ekim-2026-bursa-nobetci-eczaneler")
        bant = self._bant(self.client.get("/"))
        self.assertNotIn("ECZANELER", bant.upper().replace("İ", "I"))
        self.assertIn("Gerçek haber", bant)

    def test_haber_detayinin_rayi_da_ayni_bant(self):
        h = self.haber("Detay haberi")
        SonDakika.objects.create(baslik="Raydaki son dakika", adres="/gundem/r-1")
        self.assertContains(self.client.get(h.get_absolute_url()), "RAYDAKİ SON DAKİKA")


# --------------------------------------------------------------------------
# 4. Bugün ekranı: Yayına hazır kuyruğu ve tek tık yayın

class YayinaHazirKuyrugu(Temel):

    def _hazir(self, baslik, **alanlar):
        varsayilan = dict(durum=Haber.DURUM_PASIF, hazirlik="hazir",
                          muhabir="Ayşe Muhabir", yayin_zamani=None)
        varsayilan.update(alanlar)
        return self.haber(baslik, **varsayilan)

    def test_uc_kuyruk_birden(self):
        self.haber("Taslak haber", durum=Haber.DURUM_PASIF, hazirlik="taslak")
        self.haber("İncelemedeki haber", durum=Haber.DURUM_PASIF, hazirlik="incelemede")
        self._hazir("Masaya bırakılan haber")
        self.gir("Editör")
        yanit = self.client.get("/panel/")
        self.assertEqual(yanit.context["kuyruk_sayisi"], 3)
        self.assertEqual(yanit.context["hazir_sayisi"], 1)
        self.assertContains(yanit, "Masaya bırakılan haber")
        self.assertContains(yanit, "Yayına al</button>")

    def test_muhabir_kuyrugu_gorur_dugmeyi_gormez_ve_yayinlayamaz(self):
        h = self._hazir("Muhabirin hazır haberi")
        self.gir("Muhabir")
        yanit = self.client.get("/panel/")
        self.assertContains(yanit, "Muhabirin hazır haberi")
        self.assertNotContains(yanit, "Yayına al</button>")
        self.assertEqual(self.client.post(f"/panel/haber/{h.pk}/yayinla").status_code, 403)
        h.refresh_from_db()
        self.assertEqual(h.durum, Haber.DURUM_PASIF)

    def test_tek_tikla_yayina_alma(self):
        h = self._hazir("Tek tıkla yayınlanan haber")
        self.assertEqual(self.client.get(h.get_absolute_url()).status_code, 404)
        self.gir("Editör")
        yanit = self.client.post(f"/panel/haber/{h.pk}/yayinla")
        self.assertEqual(yanit.status_code, 302)
        h.refresh_from_db()
        self.assertEqual(h.durum, Haber.DURUM_AKTIF)
        self.assertIsNotNone(h.yayin_zamani)
        self.assertTrue(LogKaydi.objects.filter(fiil="yayina_alma", hedef_id=h.pk).exists())
        self.client.logout()
        self.assertEqual(self.client.get(h.get_absolute_url()).status_code, 200)

    def test_esigi_gecmeyen_yayina_alinmaz(self):
        h = self._hazir("Spotsuz haber", spot="")
        self.gir("Editör")
        yanit = self.client.get("/panel/")
        self.assertContains(yanit, "Yayına alınamaz — eksik: spot")
        self.client.post(f"/panel/haber/{h.pk}/yayinla")
        h.refresh_from_db()
        self.assertEqual(h.durum, Haber.DURUM_PASIF)

    def test_get_yayinlamaz(self):
        h = self._hazir("GET ile denenen")
        self.gir("Editör")
        self.client.get(f"/panel/haber/{h.pk}/yayinla")
        h.refresh_from_db()
        self.assertEqual(h.durum, Haber.DURUM_PASIF)


# --------------------------------------------------------------------------
# 5. Haber sayfası: imza, gövde, form alanlarının karşılığı

class HaberSayfasi(Temel):

    def _kunye(self, haber):
        metin = self.client.get(haber.get_absolute_url()).content.decode()
        bas = metin.index('class="detay-kunye"')
        return metin, metin[bas:metin.index('class="arac"', bas)]

    def test_imza_muhabir(self):
        h = self.haber("Muhabir haberi", muhabir="Ayşe Yılmaz")
        _, kunye = self._kunye(h)
        self.assertIn("Ayşe Yılmaz", kunye)
        self.assertNotIn("Haber Merkezi", kunye)

    def test_imza_ajans(self):
        h = self.haber("Ajans haberi", kaynak_turu=Haber.KAYNAK_AJANS)
        h.kaynaklar.add(self.ajans)
        _, kunye = self._kunye(h)
        self.assertIn("Anadolu Ajansı", kunye)
        self.assertIn('data-imza="ajans"', kunye)

    def test_imza_dis_yayin(self):
        h = self.haber("Alıntı haber", kaynak_turu=Haber.KAYNAK_DIS_YAYIN)
        h.kaynaklar.add(self.dis)
        _, kunye = self._kunye(h)
        self.assertIn("Kaynak: Sözcü", kunye)

    def test_imza_yedegi_ve_meta_yazar_basilmaz(self):
        h = self.haber("Arşiv haberi", kaynak_turu="", meta_yazar="fikir_iscisi",
                       meta_yazar_elle=True)
        metin, kunye = self._kunye(h)
        self.assertIn("Haber Merkezi", kunye)
        self.assertNotIn("Fikir İşçisi", metin)

    def test_imza_sorgu_acmaz(self):
        h = self.haber("Ön çekim", kaynak_turu=Haber.KAYNAK_AJANS)
        h.kaynaklar.add(self.ajans)
        kayit = Haber.objects.prefetch_related("kaynaklar").get(pk=h.pk)
        with self.assertNumQueries(0):
            self.assertEqual(kayit.imza()["metin"], "Anadolu Ajansı")

    def test_fotograf_notu_korunuyor(self):
        h = self.haber("Fotoğrafsız yeni haber")
        metin, _ = self._kunye(h)
        self.assertIn("Görsel temsilîdir.", metin)

    def test_ikinci_baslik_ve_etiketler(self):
        h = self.haber("Ana başlık", ikinci_baslik="Altındaki ikinci başlık")
        metin, _ = self._kunye(h)
        self.assertIn('<p class="ikinci-baslik">Altındaki ikinci başlık</p>', metin)
        self.assertIn("ETİKETLER", metin)
        self.assertIn("<li>Masa etiketi</li>", metin)
        # Etiket sayfası yok: bağlantı verilmez.
        self.assertNotIn('href="/etiket', metin)

    def test_gomulu_kod_ham_basilmaz_beyaz_listeden_kart(self):
        kod = ('<iframe src="https://www.youtube.com/embed/dQw4w9WgXcQ" onload="x()"></iframe>'
               '<blockquote class="twitter-tweet"><a href="https://twitter.com/bursaspor/'
               'status/1234567890123">t</a></blockquote><script src="https://platform.'
               'twitter.com/widgets.js"></script><img src=x onerror=alert(1)>'
               '<iframe src="https://kotu.example/x"></iframe>')
        h = self.haber("Gömülü kodlu haber", gomulu_kod=kod)
        metin, _ = self._kunye(h)
        self.assertIn('href="https://www.youtube.com/watch?v=dQw4w9WgXcQ"', metin)
        self.assertIn('href="https://x.com/bursaspor/status/1234567890123"', metin)
        for yasak in ("<iframe", "widgets.js", "onerror", "kotu.example", "onload"):
            self.assertNotIn(yasak, metin)

    def test_instagram_karti(self):
        from .temizle import gomulu_kartlari
        kartlar = gomulu_kartlari('<blockquote class="instagram-media" data-instgrm-permalink='
                                  '"https://www.instagram.com/p/CxYz123abc/"></blockquote>')
        self.assertEqual(kartlar[0]["adres"], "https://www.instagram.com/p/CxYz123abc/")
        self.assertEqual(gomulu_kartlari("<script>alert(1)</script>"), [])

    def test_ilgili_haberler_once_editorun_secimi(self):
        h = self.haber("Asıl haber")
        uzak = self.haber("Editörün seçtiği eski haber", dakika=60 * 24 * 400)
        cekilmis = self.haber("Seçilmiş ama çekilmiş", durum=Haber.DURUM_PASIF)
        h.ilgili_haberler.add(uzak, cekilmis)
        for n in range(8):
            self.haber(f"Aynı kategoriden {n}", dakika=10 + n)
        yanit = self.client.get(h.get_absolute_url())
        ilgili = [x.pk for x in yanit.context["ilgili"]]
        self.assertEqual(ilgili[0], uzak.pk)
        self.assertNotIn(cekilmis.pk, ilgili)
        self.assertEqual(len(ilgili), 6)


class DuzMetinGovde(Temel):

    def _form_verisi(self, govde):
        return {"baslik": "Düz metin haber", "spot": "Spot", "govde": govde,
                "kategori": self.gundem.pk, "etiketler": self.etiket.ad,
                "durum": Haber.DURUM_PASIF, "hazirlik": "taslak",
                "kaynak_turu": Haber.KAYNAK_MUHABIR, "muhabir": "A"}

    def test_form_duz_metni_paragraflar(self):
        self.gir("Editör")
        self.client.post("/panel/haber/ekle", self._form_verisi(
            "Birinci paragraf.\r\n\r\nİkinci paragraf\r\nyeni satır.\n\n\nÜçüncü <b>değil</b>"))
        h = Haber.objects.get(baslik="Düz metin haber")
        # Etiket görüldüğü için (<b>) gövde HTML sayılır ve dokunulmaz.
        self.assertIn("<b>değil</b>", h.govde)
        self.client.post("/panel/haber/ekle", {**self._form_verisi(
            "Birinci paragraf.\r\n\r\nİkinci paragraf\r\nyeni satır.\n\n\n5 < 6 & x>y"),
            "baslik": "Düz metin iki"})
        h = Haber.objects.get(baslik="Düz metin iki")
        self.assertEqual(h.govde, "<p>Birinci paragraf.</p><p>İkinci paragraf<br>yeni "
                                  "satır.</p><p>5 &lt; 6 &amp; x&gt;y</p>")

    def test_html_govdeye_dokunulmaz(self):
        from .temizle import duz_metni_paragrafla
        html = "<p>Bir.</p>\n\n<p>İki.</p>"
        self.assertEqual(duz_metni_paragrafla(html), html)

    def test_eski_duz_metin_kayit_sayfada_paragrafli(self):
        h = self.haber("Eski düz kayıt", govde="İlk.\n\nİkinci.\n\n<script>x</script>")
        # Etiket var → HTML sayılır; betik temizleyicide düşer.
        metin = self.client.get(h.get_absolute_url()).content.decode()
        self.assertNotIn("<script>x", metin)
        h2 = self.haber("Eski düz kayıt 2", govde="İlk paragraf.\n\nİkinci paragraf.")
        metin = self.client.get(h2.get_absolute_url()).content.decode()
        self.assertIn("<p>İlk paragraf.</p><p>İkinci paragraf.</p>", metin)

    def test_yayin_kapisi_sayimi_degismez(self):
        from . import yayin_kapisi
        from .temizle import duz_metni_paragrafla
        duz = "Bir.\n\nİki.\n\nÜç."
        self.assertEqual(yayin_kapisi.paragraf_sayisi(duz),
                         yayin_kapisi.paragraf_sayisi(duz_metni_paragrafla(duz)))


class FormAlanSozlesmesi(Temel):

    def test_karsiligi_olmayan_alanlar_isaretli(self):
        self.gir("Yayın Yönetmeni")
        yanit = self.client.get("/panel/haber/ekle")
        metin = yanit.content.decode()
        self.assertEqual(metin.count("data-sitede-kullanilmiyor"), 4)
        self.assertIn("Sitede okur yorumu bölümü henüz yok", metin)
        self.assertIn("Güvenlik gereği kapalı", metin)
        self.assertIn("Kod olduğu gibi BASILMAZ", metin)
