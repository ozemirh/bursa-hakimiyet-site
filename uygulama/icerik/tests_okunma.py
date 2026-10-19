"""Okunma sayacı — sayma kuralları, geri düşüş ve panel raporu.

Sayaç 3 Eylül 2026'da açıldı (URUN-PLANI.md §4, madde 8: eski okunma verisi
göçte kurtarılamadı). Buradaki testler üç şeyi kilitliyor:

1. **Ne sayılır.** Robot, ön yükleme ve aynı okurun tekrar yüklemesi
   sayılmaz; sayılmayan istek sayfayı da bozmaz.
2. **Geri düşüş.** Eşiğe ulaşılmadan hiçbir modül gerçek veri gösteriyormuş
   gibi davranmaz — üçü de eski "listenin devamı" kuralına döner. Yarısı
   gerçek yarısı dolgu bir sıralama okura sayı diye yalan söylerdi.
3. **Beyan veriden okunur.** `/veri-kaynaklari` sayfasındaki cümle listenin
   O ANDAKİ hâlini anlatır; şablona çakılı değildir (§30/§32'nin dersi).
"""

from datetime import timedelta

from django.contrib.auth.models import Group, User
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone

from taksonomi.models import Kategori, KategoriTur

from . import okunma
from .models import Haber, Okunma

PAROLA = "deneme-parola-123"
TARAYICI = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/128.0 Safari/537.36")


class OkunmaTemeli(TestCase):
    """Ortak kurulum: kategori sözleşmesi + istenen sayıda haber."""

    @classmethod
    def setUpTestData(cls):
        call_command("taksonomi_kur", verbosity=0)
        cls.tur = KategoriTur.objects.filter(
            tur=Kategori.TUR_HABER, slug="bursaspor").first()
        cls.kategori = cls.tur.kategori

    def setUp(self):
        okunma.sifirla()

    def tearDown(self):
        okunma.sifirla()

    def _haber(self, n, kategori=None, **fazla):
        return Haber.objects.create(
            id=910000 + n, slug=f"okunma-{n}", baslik=f"Okunma başlığı {n}",
            spot="spot", govde="<p>gövde</p>",
            kategori=kategori or self.kategori,
            yayin_zamani=timezone.now() - timedelta(minutes=n), **fazla)

    def _okut(self, haber, adet, gun_once=0):
        """Sayacı doğrudan besler — istek yolundan geçmeden."""
        Okunma.objects.create(
            haber=haber, adet=adet,
            gun=timezone.localdate() - timedelta(days=gun_once))


class NeSayilir(OkunmaTemeli):

    def _istek(self, **basliklar):
        from django.test import RequestFactory
        return RequestFactory().get("/", **basliklar)

    def test_olagan_tarayici_sayiliyor(self):
        self.assertTrue(
            okunma.sayilmali(self._istek(HTTP_USER_AGENT=TARAYICI), 1))

    def test_robot_sayilmiyor(self):
        for ajan in ("Googlebot/2.1 (+http://www.google.com/bot.html)",
                     "Mozilla/5.0 (compatible; bingbot/2.0)",
                     "python-requests/2.31.0",
                     "curl/8.4.0",
                     "Mozilla/5.0 (X11; Linux x86_64) HeadlessChrome/128.0"):
            with self.subTest(ajan=ajan):
                self.assertFalse(
                    okunma.sayilmali(self._istek(HTTP_USER_AGENT=ajan), 1))

    def test_ajansiz_istek_sayilmiyor(self):
        self.assertFalse(okunma.sayilmali(self._istek(), 1))

    def test_on_yukleme_sayilmiyor(self):
        """Okur daha tıklamadan tarayıcının çektiği sayfa okunma değildir."""
        for baslik in ({"HTTP_SEC_PURPOSE": "prefetch;prerender"},
                       {"HTTP_PURPOSE": "prefetch"},
                       {"HTTP_X_MOZ": "prefetch"}):
            with self.subTest(baslik=baslik):
                istek = self._istek(HTTP_USER_AGENT=TARAYICI, **baslik)
                self.assertFalse(okunma.sayilmali(istek, 1))

    def test_ayni_okur_yarim_saat_icinde_bir_kez_sayiliyor(self):
        istek = self._istek(HTTP_USER_AGENT=TARAYICI, REMOTE_ADDR="10.0.0.9")
        self.assertTrue(okunma.sayilmali(istek, 7))
        self.assertFalse(okunma.sayilmali(istek, 7))
        # Aynı okur BAŞKA haberi açarsa sayılır.
        self.assertTrue(okunma.sayilmali(istek, 8))

    def test_farkli_okurlar_ayri_sayiliyor(self):
        birinci = self._istek(HTTP_USER_AGENT=TARAYICI, REMOTE_ADDR="10.0.0.1")
        ikinci = self._istek(HTTP_USER_AGENT=TARAYICI, REMOTE_ADDR="10.0.0.2")
        self.assertTrue(okunma.sayilmali(birinci, 7))
        self.assertTrue(okunma.sayilmali(ikinci, 7))

    @override_settings(GUVENILIR_VEKILLER=["127.0.0.1"])
    def test_vekil_arkasindaki_okurlar_ayrisiyor(self):
        """`REMOTE_ADDR` vekilde herkeste aynıdır; ileten başlık ayrıştırır.

        19 Ekim 2026'dan beri yalnız GÜVENİLİR vekilden gelen istekte."""
        ortak = {"HTTP_USER_AGENT": TARAYICI, "REMOTE_ADDR": "127.0.0.1"}
        birinci = self._istek(HTTP_X_FORWARDED_FOR="203.0.113.7", **ortak)
        ikinci = self._istek(HTTP_X_FORWARDED_FOR="203.0.113.8", **ortak)
        self.assertTrue(okunma.sayilmali(birinci, 7))
        self.assertTrue(okunma.sayilmali(ikinci, 7))
        self.assertEqual(okunma.ziyaretci_adresi(birinci), "203.0.113.7")

    def test_guvenilir_vekil_yoksa_ileten_baslik_okunmuyor(self):
        """Başlığı herkes yazabilir: koşulsuz güvenilseydi aynı okur her
        istekte başka bir adres yazıp tekrar süzgecini atlatırdı."""
        ortak = {"HTTP_USER_AGENT": TARAYICI, "REMOTE_ADDR": "198.51.100.4"}
        birinci = self._istek(HTTP_X_FORWARDED_FOR="203.0.113.7", **ortak)
        ikinci = self._istek(HTTP_X_FORWARDED_FOR="203.0.113.8", **ortak)
        self.assertEqual(okunma.ziyaretci_adresi(birinci), "198.51.100.4")
        self.assertTrue(okunma.sayilmali(birinci, 7))
        self.assertFalse(okunma.sayilmali(ikinci, 7))

    @override_settings(GUVENILIR_VEKILLER=["10.0.0.0/8"])
    def test_zincir_sagdan_okunuyor_taklit_sol_uc_atlanir(self):
        """Okur başlığa kendi sahte adresini yazarsa zincirin SOL ucunda
        durur; okurun gerçek adresi güvenilir vekilin eklediği sağ uçtadır."""
        istek = self._istek(HTTP_USER_AGENT=TARAYICI, REMOTE_ADDR="10.0.0.2",
                            HTTP_X_FORWARDED_FOR="1.2.3.4, 198.51.100.9, 10.0.0.1")
        self.assertEqual(okunma.ziyaretci_adresi(istek), "198.51.100.9")

    def test_guvenilmeyen_kaynaktan_gelen_vekil_basligi_yok_sayilir(self):
        with override_settings(GUVENILIR_VEKILLER=["127.0.0.1"]):
            istek = self._istek(HTTP_USER_AGENT=TARAYICI, REMOTE_ADDR="198.51.100.4",
                                HTTP_X_FORWARDED_FOR="203.0.113.7")
            self.assertEqual(okunma.ziyaretci_adresi(istek), "198.51.100.4")


class TamponVeKova(OkunmaTemeli):

    def test_sayim_gunluk_kovaya_yaziliyor(self):
        haber = self._haber(1)
        for adres in ("10.0.0.1", "10.0.0.2", "10.0.0.3"):
            from django.test import RequestFactory
            istek = RequestFactory().get("/", HTTP_USER_AGENT=TARAYICI,
                                         REMOTE_ADDR=adres)
            okunma.say(istek, haber.pk)
        # Tampon henüz yazılmamış olabilir; boşaltma sayımı diske indirir.
        okunma.bosalt()
        kova = Okunma.objects.get(haber=haber, gun=timezone.localdate())
        self.assertEqual(kova.adet, 3)

    def test_ikinci_bosaltma_ayni_kovayi_artiriyor(self):
        haber = self._haber(2)
        self._okut(haber, 4)
        from django.test import RequestFactory
        istek = RequestFactory().get("/", HTTP_USER_AGENT=TARAYICI,
                                     REMOTE_ADDR="10.0.0.5")
        okunma.say(istek, haber.pk)
        okunma.bosalt()
        self.assertEqual(Okunma.objects.get(haber=haber).adet, 5)
        self.assertEqual(Okunma.objects.filter(haber=haber).count(), 1)

    def test_bos_tampon_yazmaya_gitmiyor(self):
        self.assertEqual(okunma.bosalt(), 0)


class SiralamaVeGeriDusus(OkunmaTemeli):

    def test_esik_altinda_bos_donuyor(self):
        """Üç okunmayla kurulmuş bir "en çok okunanlar" listesi gürültüdür."""
        for n in range(5):
            self._okut(self._haber(n), okunma.ESIK_OKUNMA - 1)
        self.assertEqual(okunma.en_cok(Haber.yayindakiler(), 5), [])

    def test_eksik_kayitla_bos_donuyor(self):
        """Beş isteniyorsa dördü gerçek biri dolgu OLMAZ; liste ya hep ya hiç."""
        for n in range(4):
            self._okut(self._haber(n), 100)
        self._haber(9)
        self.assertEqual(okunma.en_cok(Haber.yayindakiler(), 5), [])
        self.assertEqual(len(okunma.en_cok(Haber.yayindakiler(), 4)), 4)

    def test_esik_ustunde_cok_okunandan_aza_siraliyor(self):
        beklenen = []
        for n in range(5):
            haber = self._haber(n)
            self._okut(haber, 100 - n * 10)
            beklenen.append(haber.pk)
        sonuc = okunma.en_cok(Haber.yayindakiler(), 5)
        self.assertEqual([h.pk for h in sonuc], beklenen)
        self.assertEqual(sonuc[0].okunma_adedi, 100)

    def test_pencere_disindaki_okunma_sayilmiyor(self):
        for n in range(5):
            self._okut(self._haber(n), 100,
                       gun_once=okunma.PENCERE_GUN + 1)
        self.assertEqual(okunma.en_cok(Haber.yayindakiler(), 5), [])

    def test_pencere_icindeki_gunler_toplaniyor(self):
        haber = self._haber(0)
        self._okut(haber, 6, gun_once=0)
        self._okut(haber, 6, gun_once=1)
        for n in range(1, 5):
            self._okut(self._haber(n), 20)
        sonuc = okunma.en_cok(Haber.yayindakiler(), 5)
        self.assertEqual({h.pk for h in sonuc}, {h.pk for h in Haber.objects.all()})
        self.assertEqual(
            next(h.okunma_adedi for h in sonuc if h.pk == haber.pk), 12)

    def test_yayinda_olmayan_haber_siralamaya_girmiyor(self):
        gizli = self._haber(0, durum=Haber.DURUM_PASIF)
        self._okut(gizli, 500)
        for n in range(1, 6):
            self._okut(self._haber(n), 20)
        sonuc = okunma.en_cok(Haber.yayindakiler(), 5)
        self.assertNotIn(gizli.pk, {h.pk for h in sonuc})

    def test_haric_listesi_uygulaniyor(self):
        haberler = []
        for n in range(6):
            haber = self._haber(n)
            self._okut(haber, 100 - n)
            haberler.append(haber)
        sonuc = okunma.en_cok(Haber.yayindakiler(), 5,
                              haric=[haberler[0].pk])
        self.assertNotIn(haberler[0].pk, {h.pk for h in sonuc})
        self.assertEqual(len(sonuc), 5)


class SayfalardakiModuller(OkunmaTemeli):
    """Üç modül de aynı kapıdan besleniyor mu, ve sayfada tekrar var mı."""

    def _bol_bol_haber(self, adet, kategori=None):
        return [self._haber(n, kategori=kategori) for n in range(adet)]

    def test_anasayfa_esik_altinda_eski_kurala_donuyor(self):
        from .views import EN_COK
        self._bol_bol_haber(60)
        yanit = self.client.get("/")
        self.assertEqual(len(yanit.context["en_cok"]), EN_COK)
        # Gerçek veri yok; kutu havuzun devamından geliyor, sayfayla
        # çakışmıyor.
        ust = {h.pk for h in yanit.context["manset"]}
        self.assertEqual({h.pk for h in yanit.context["en_cok"]} & ust, set())

    def test_anasayfa_gercek_veriye_geciyor_ve_manseti_tekrarlamiyor(self):
        from .views import EN_COK
        haberler = self._bol_bol_haber(60)
        # En çok okunanlar BİLEREK manşetin ilk beşi seçildi: gerçek
        # hayatta da en çok okunan haber çoğu zaman manşettir ve kutu onu
        # tekrarlarsa 29 Ağustos'ta ölçülen kusur geri gelir.
        for sira, haber in enumerate(haberler[:5]):
            self._okut(haber, 500 - sira)
        # Sayfaya HİÇ girmeyen beş haber de eşiği aşsın ki kutu dolabilsin.
        # Havuz 45 kayıt harcıyor; eski kural olsaydı kutu 45-49 arasını
        # basardı, o yüzden gerçek veri BİLEREK 50-54 arasına konuldu:
        # iki davranış aynı sonucu verseydi test hiçbir şey ölçmezdi.
        for sira, haber in enumerate(haberler[50:55]):
            self._okut(haber, 300 - sira)
        yanit = self.client.get("/")
        en_cok = yanit.context["en_cok"]
        self.assertEqual(len(en_cok), EN_COK)
        self.assertEqual([h.pk for h in en_cok],
                         [h.pk for h in haberler[50:55]])
        sayfadakiler = set()
        for ad in ("manset", "manset_liste", "ikincil", "dortlu", "kutular"):
            sayfadakiler |= {h.pk for h in yanit.context[ad]}
        self.assertEqual({h.pk for h in en_cok} & sayfadakiler, set())

    def test_bolum_seridi_gercek_veriyle_o_bolumden_geliyor(self):
        from .views import KATEGORI_EN_COK, SAYFA_BOYU
        baska = KategoriTur.objects.filter(
            tur=Kategori.TUR_HABER).exclude(pk=self.tur.pk).first().kategori
        bizimkiler = [self._haber(n) for n in range(SAYFA_BOYU + 10)]
        yabanci = self._haber(500, kategori=baska)
        self._okut(yabanci, 9999)
        # Sayfada GÖRÜNEN kayıtlar da çok okunmuş olsun: şerit yine de
        # onları tekrarlamamalı.
        for haber in bizimkiler[:5]:
            self._okut(haber, 900)
        for sira, haber in enumerate(bizimkiler[SAYFA_BOYU:SAYFA_BOYU + 5]):
            self._okut(haber, 100 - sira)
        yanit = self.client.get("/bursaspor")
        en_cok = yanit.context["en_cok"]
        sayfadakiler = {h.pk for h in yanit.context["sayfa"]}
        self.assertEqual(len(en_cok), KATEGORI_EN_COK)
        self.assertEqual({h.pk for h in en_cok} & sayfadakiler, set())
        self.assertNotIn(yabanci.pk, {h.pk for h in en_cok})
        for h in en_cok:
            self.assertEqual(h.kategori_id, self.kategori.pk)

    def test_haber_detayi_okunmayi_sayiyor(self):
        haber = self._haber(1)
        yanit = self.client.get(haber.get_absolute_url(),
                                HTTP_USER_AGENT=TARAYICI,
                                REMOTE_ADDR="10.0.0.11")
        self.assertEqual(yanit.status_code, 200)
        okunma.bosalt()
        self.assertEqual(Okunma.objects.get(haber=haber).adet, 1)

    def test_yonlendirilen_istek_iki_kez_saymiyor(self):
        """Yanlış slug 301 veriyor; sayım kanonik denetimden SONRA."""
        haber = self._haber(1)
        yanlis = f"/{haber.kategori.slug_al()}/yanlis-slug-{haber.pk}"
        self.client.get(yanlis, HTTP_USER_AGENT=TARAYICI,
                        REMOTE_ADDR="10.0.0.12", follow=True)
        okunma.bosalt()
        self.assertEqual(Okunma.objects.get(haber=haber).adet, 1)

    def test_robot_istegi_sayaci_kimildatmiyor(self):
        haber = self._haber(1)
        yanit = self.client.get(haber.get_absolute_url(),
                                HTTP_USER_AGENT="Googlebot/2.1")
        self.assertEqual(yanit.status_code, 200)
        okunma.bosalt()
        self.assertFalse(Okunma.objects.filter(haber=haber).exists())

    def test_detay_rayi_gercek_veriden_besleniyor(self):
        haberler = [self._haber(n) for n in range(12)]
        acilan = haberler[0]
        for sira, haber in enumerate(haberler[1:6]):
            self._okut(haber, 200 - sira)
        yanit = self.client.get(acilan.get_absolute_url(),
                                HTTP_USER_AGENT=TARAYICI,
                                REMOTE_ADDR="10.0.0.13")
        en_cok = yanit.context["en_cok"]
        self.assertEqual([h.pk for h in en_cok],
                         [h.pk for h in haberler[1:6]])
        # Okunan haberin kendisi kendi rayında durmaz.
        self.assertNotIn(acilan.pk, {h.pk for h in en_cok})


class BeyanVeriyleUyumlu(OkunmaTemeli):
    """`/veri-kaynaklari` cümlesi listenin O ANDAKİ hâlini anlatmalı."""

    def test_esik_altinda_editor_seckisi_diyor(self):
        for n in range(10):
            self._haber(n)
        govde = self.client.get("/veri-kaynaklari").content.decode()
        self.assertIn("Şimdilik editör seçkisi", govde)
        self.assertNotIn("Liste gerçek okunma sayımından çıkar", govde)

    def test_gercek_veriye_gecince_beyan_degisiyor(self):
        for n in range(10):
            haber = self._haber(n)
            if n < 6:
                self._okut(haber, 100 - n)
        govde = self.client.get("/veri-kaynaklari").content.decode()
        self.assertIn("Liste gerçek okunma sayımından çıkar", govde)
        self.assertNotIn("Şimdilik editör seçkisi", govde)


class PanelOkunmaEkranlari(OkunmaTemeli):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        call_command("roller_kur", verbosity=0)
        cls.yonetmen = User.objects.create_user("yonetmen", password=PAROLA)
        cls.yonetmen.groups.add(Group.objects.get(name="Yayın Yönetmeni"))

    def _gir(self):
        self.client.force_login(self.yonetmen)

    def test_akis_okunma_sutunu_sayiyi_gosteriyor(self):
        haber = self._haber(1)
        self._okut(haber, 42)
        self._gir()
        yanit = self.client.get("/panel/akis")
        satir = next(s for s in yanit.context["satirlar"]
                     if s["kimlik"] == haber.pk)
        # Başlık · Kategori · Resim · Tarih · Okunma · ...
        self.assertEqual(satir["hucreler"][4]["metin"], 42)

    def test_akis_okunmamis_haberde_sifir_yaziyor(self):
        haber = self._haber(1)
        self._gir()
        yanit = self.client.get("/panel/akis")
        satir = next(s for s in yanit.context["satirlar"]
                     if s["kimlik"] == haber.pk)
        self.assertEqual(satir["hucreler"][4]["metin"], 0)

    def test_okunma_sutunu_satir_basina_sorgu_acmiyor(self):
        """25 satır için tek toplama sorgusu — §28'in sayım maliyeti dersi."""
        for n in range(25):
            self._okut(self._haber(n), 5)
        self._gir()
        from django.db import connection
        from django.test.utils import CaptureQueriesContext
        with CaptureQueriesContext(connection) as sorgular:
            self.client.get("/panel/akis")
        okunma_sorgulari = [s for s in sorgular.captured_queries
                            if "icerik_okunma" in s["sql"]]
        self.assertEqual(len(okunma_sorgulari), 1, okunma_sorgulari)

    def test_rapor_cok_okunandan_aza_siraliyor(self):
        az, cok = self._haber(1), self._haber(2)
        self._okut(az, 3)
        self._okut(cok, 30)
        self._gir()
        yanit = self.client.get("/panel/okunma")
        self.assertEqual(yanit.status_code, 200)
        kimlikler = [s["kimlik"] for s in yanit.context["satirlar"]]
        self.assertEqual(kimlikler, [cok.pk, az.pk])
        self.assertEqual(yanit.context["satirlar"][0]["hucreler"][0]["metin"], 30)

    def test_rapor_okunmamis_haberi_listelemiyor(self):
        okunan = self._haber(1)
        okunmayan = self._haber(2)
        self._okut(okunan, 3)
        self._gir()
        yanit = self.client.get("/panel/okunma")
        self.assertEqual([s["kimlik"] for s in yanit.context["satirlar"]],
                         [okunan.pk])
        self.assertNotIn(okunmayan.pk,
                         [s["kimlik"] for s in yanit.context["satirlar"]])

    def test_rapor_penceresi_adresten_seciliyor(self):
        eski = self._haber(1)
        self._okut(eski, 50, gun_once=10)
        self._gir()
        bugun = self.client.get("/panel/okunma?pencere=1")
        self.assertEqual(bugun.context["satirlar"], [])
        otuz = self.client.get("/panel/okunma?pencere=30")
        self.assertEqual([s["kimlik"] for s in otuz.context["satirlar"]],
                         [eski.pk])

    def test_rapor_gecersiz_pencereyi_varsayilana_dusuruyor(self):
        self._gir()
        yanit = self.client.get("/panel/okunma?pencere=abc")
        self.assertEqual(yanit.status_code, 200)

    def test_rapor_oturumsuz_girise_yonlendiriyor(self):
        yanit = self.client.get("/panel/okunma")
        self.assertEqual(yanit.status_code, 302)
        self.assertIn("/panel/giris", yanit["Location"])
