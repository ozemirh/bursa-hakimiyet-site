"""Panel liste sayımının başarım gerilemeleri — 29 Ağustos 2026.

Ölçülen üç sorun ve testlerle kilitlenen davranışları:

1. **Süzgeçli `COUNT(*)` iki kez koşuyordu.** `Paginator` sayfa sayısı için
   zaten sayıyor, toplu işlem şeridi "süzgeçteki N kayıt" için ikinci kez
   saydırıyordu. `/panel/akis?q=bursa` 3.703 ms sürüyordu ve bunun
   2.484 + 1.188 ms'si aynı iki taramaydı.

2. **Sayım sınırsızdı.** `LIKE '%…%'` baştaki jokerle hiçbir B-ağacı
   indeksini kullanamaz; 486.667 satır taranıyordu. Ölçüm: tam sayım
   1.176 ms, 5.001'de kesik sayım 104 ms, sayfanın kendi sorgusu 0 ms.
   Yani ekranın bedelinin tamamı **kimsenin bakmadığı bir toplamdan**
   geliyordu. Sınır `TOPLU_UST_SINIR` ile aynı sayı: onu aşan küme zaten
   toplu işlenemiyor.

3. **Kaynak listesi `LIMIT`ten faydalanamıyordu.** `annotate(Count(…))`
   ara tabloya JOIN atıp GROUP BY kuruyor, `ORDER BY ad` yüzünden 400
   kaynağın tamamı 112.906 bağ satırı üzerinden gruplanıyordu: 109 ms.

Testler süreyi ölçmez — süre makineye göre değişir, gerileme testi olmaz.
**Sorgu sayısını ve sayımın kesilme davranışını** kilitler; ikisi de
yukarıdaki üç sorunun doğrudan imzasıdır.
"""

from unittest import mock

from django.contrib.auth.models import Group, User
from django.core.management import call_command
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from taksonomi.models import Kategori, KategoriTur, Kaynak

from . import panel
from .models import Haber
from .panel import SAYIM_SINIRI, TOPLU_UST_SINIR, SinirliSayfalayici

PAROLA = "deneme-parola-123"


def _sayim_sorgulari(sorgular, tablo="icerik_haber"):
    """Verilen tabloyu sayan sorgular."""
    return [s["sql"] for s in sorgular
            if "COUNT(" in s["sql"].upper() and tablo in s["sql"]]


def _tekrarlayan(sorgular):
    """BİREBİR AYNI olup birden çok kez koşan sorgular.

    Ölçtüğümüz şey tam olarak budur. "Ekranda kaç sayım var" diye sormak
    yanlış olurdu: bir liste ekranı meşru olarak birden çok FARKLI sayım
    çalıştırabiliyor (videolarda "oynatması olmayan", logda "oturum olayı"
    uyarı satırları gibi). Hata, aynı sayımın iki kez açılmasıydı.
    """
    gorulen, tekrar = set(), []
    for s in sorgular:
        sql = " ".join(s["sql"].split())
        if "COUNT(" not in sql.upper():
            continue
        if sql in gorulen:
            tekrar.append(sql)
        gorulen.add(sql)
    return tekrar


class SuzgecliSayimBirKezKosar(TestCase):

    @classmethod
    def setUpTestData(cls):
        call_command("taksonomi_kur", verbosity=0)
        call_command("roller_kur", verbosity=0)
        cls.kategori = KategoriTur.objects.get(
            tur=Kategori.TUR_HABER, slug="gundem").kategori
        cls.yonetmen = User.objects.create_user("hsay", password=PAROLA)
        cls.yonetmen.groups.add(Group.objects.get(name="Yayın Yönetmeni"))
        simdi = timezone.now()
        Haber.objects.bulk_create([Haber(
            id=880000 + i, slug=f"sayim-{i}", baslik=f"Bursa raporu {i}",
            kategori=cls.kategori, durum=Haber.DURUM_AKTIF,
            yayin_zamani=simdi) for i in range(40)])

    def setUp(self):
        self.client.force_login(self.yonetmen)

    def _tekrar(self, adres):
        with CaptureQueriesContext(connection) as yakalanan:
            yanit = self.client.get(adres)
        self.assertEqual(yanit.status_code, 200)
        return _tekrarlayan(yakalanan.captured_queries)

    def test_suzgecsiz_listede_sayim_tekrarlanmiyor(self):
        self.assertEqual(self._tekrar("/panel/akis"), [])

    def test_aramada_sayim_tekrarlanmiyor(self):
        """En pahalı hâli: `LIKE '%…%'` taraması iki kez açılmamalı."""
        self.assertEqual(self._tekrar("/panel/akis?q=bursa"), [])

    def test_kategori_suzgecinde_sayim_tekrarlanmiyor(self):
        self.assertEqual(self._tekrar(f"/panel/akis?kategori={self.kategori.pk}"), [])

    def test_medya_listesinde_de_tekrarlanmiyor(self):
        self.assertEqual(self._tekrar("/panel/videolar"), [])

    def test_log_ust_bilgisi_ayri_sayim_acmiyor(self):
        """Üst bilgi satırı sayıyı sayfalayıcıdan almalı."""
        self.assertEqual(self._tekrar("/panel/log"), [])

    def test_serit_sayisi_sayfalayicinin_sayisiyla_ayni(self):
        """Şerit ayrı saymayı bıraktı; gösterdiği sayı yine doğru olmalı."""
        yanit = self.client.get("/panel/akis")
        self.assertContains(yanit, 'data-toplu-sayi="40"')


class SinirliSayim(TestCase):
    """Sayım üst sınırda kesilir ve bu ekranda dürüstçe söylenir."""

    @classmethod
    def setUpTestData(cls):
        call_command("taksonomi_kur", verbosity=0)
        cls.kategori = KategoriTur.objects.get(
            tur=Kategori.TUR_HABER, slug="gundem").kategori
        simdi = timezone.now()
        Haber.objects.bulk_create([Haber(
            id=890000 + i, slug=f"sinir-{i}", baslik=f"Kayıt {i}",
            kategori=cls.kategori, durum=Haber.DURUM_AKTIF,
            yayin_zamani=simdi) for i in range(30)])

    def test_sinir_altinda_sayi_kesin(self):
        s = SinirliSayfalayici(Haber.objects.all(), 10, sayim_siniri=100)
        self.assertEqual(s.count, 30)
        self.assertFalse(s.asildi)

    def test_sinir_ustunde_sayim_kesiliyor(self):
        s = SinirliSayfalayici(Haber.objects.all(), 10, sayim_siniri=12)
        self.assertEqual(s.count, 12)
        self.assertTrue(s.asildi)

    def test_kesik_sayim_veritabanini_sinirda_birakiyor(self):
        """Kesme SQL'de olmalı; Python'da kırpmak taramayı kısaltmaz."""
        with CaptureQueriesContext(connection) as yakalanan:
            SinirliSayfalayici(Haber.objects.all(), 10, sayim_siniri=12).count
        sayim = _sayim_sorgulari(yakalanan.captured_queries)
        self.assertEqual(len(sayim), 1)
        self.assertIn("LIMIT 13", sayim[0])

    def test_bellekteki_liste_kesilmiyor(self):
        """Listede sayım bedava ve kesin; `asildi` yanlışlıkla doğru olmamalı."""
        s = SinirliSayfalayici(list(range(50)), 10, sayim_siniri=12)
        self.assertEqual(s.count, 50)
        self.assertFalse(s.asildi)

    def test_sinir_toplu_islem_siniriyla_ayni(self):
        """Ayrışırlarsa şerit 'tamamını seç' der, sunucu reddeder."""
        self.assertEqual(SAYIM_SINIRI, TOPLU_UST_SINIR)


class SeritKesikSayimdaSecimSunmuyor(TestCase):

    @classmethod
    def setUpTestData(cls):
        call_command("taksonomi_kur", verbosity=0)
        call_command("roller_kur", verbosity=0)
        cls.kategori = KategoriTur.objects.get(
            tur=Kategori.TUR_HABER, slug="gundem").kategori
        cls.yonetmen = User.objects.create_user("hser", password=PAROLA)
        cls.yonetmen.groups.add(Group.objects.get(name="Yayın Yönetmeni"))
        simdi = timezone.now()
        Haber.objects.bulk_create([Haber(
            id=900000 + i, slug=f"serit-{i}", baslik=f"Kayıt {i}",
            kategori=cls.kategori, durum=Haber.DURUM_AKTIF,
            yayin_zamani=simdi) for i in range(30)])

    def test_sinir_altinda_tamamini_sec_cikiyor(self):
        self.client.force_login(self.yonetmen)
        icerik = self.client.get("/panel/akis").content.decode()
        self.assertIn("kaydın tamamını seç", icerik)

    def test_sinir_asilinca_kutu_yerine_uyari(self):
        """Seçilemeyecek kutuyu çizmek, şeridin düzelttiği hatanın kendisi."""
        self.client.force_login(self.yonetmen)
        with mock.patch.object(panel, "SAYIM_SINIRI", 5):
            icerik = self.client.get("/panel/akis").content.decode()
        self.assertNotIn("kaydın tamamını seç", icerik)
        self.assertIn("Süzgeci daraltın", icerik)


class KaynakListesiAltSorguKullaniyor(TestCase):
    """`ORDER BY` + `GROUP BY` birleşimi `LIMIT`i işlevsiz bırakıyordu."""

    @classmethod
    def setUpTestData(cls):
        call_command("taksonomi_kur", verbosity=0)
        call_command("roller_kur", verbosity=0)
        cls.kategori = KategoriTur.objects.get(
            tur=Kategori.TUR_HABER, slug="gundem").kategori
        cls.yonetmen = User.objects.create_user("hkay", password=PAROLA)
        cls.yonetmen.groups.add(Group.objects.get(name="Yayın Yönetmeni"))
        simdi = timezone.now()
        cls.kaynak = Kaynak.objects.create(ad="AA", tur=Kaynak.TUR_AJANS)
        for i in range(5):
            haber = Haber.objects.create(
                id=910000 + i, slug=f"kay-{i}", baslik=f"Kayıt {i}",
                kategori=cls.kategori, durum=Haber.DURUM_AKTIF,
                yayin_zamani=simdi)
            haber.kaynaklar.add(cls.kaynak)

    def test_bagli_haber_sayisi_dogru(self):
        """Hız düzeltmesi sayıyı bozmamalı — asıl risk bu."""
        self.client.force_login(self.yonetmen)
        icerik = self.client.get("/panel/kaynaklar").content.decode()
        self.assertIn("AA", icerik)
        self.assertIn(">5<", icerik)

    def test_sayfa_sorgusunda_group_by_yok(self):
        self.client.force_login(self.yonetmen)
        with CaptureQueriesContext(connection) as yakalanan:
            self.client.get("/panel/kaynaklar")
        sayfa_sorgulari = [
            s["sql"] for s in yakalanan.captured_queries
            if "taksonomi_kaynak" in s["sql"] and "LIMIT" in s["sql"]
            and "COUNT(*)" not in s["sql"].upper()]
        self.assertTrue(sayfa_sorgulari, "kaynak sayfa sorgusu bulunamadı")
        for sql in sayfa_sorgulari:
            # Eski biçimin imzası: ara tablo DIŞ sorguya JOIN'leniyordu ve
            # `ORDER BY ad` yüzünden `LIMIT` hiçbir şeyi kısaltmıyordu.
            # (Alt sorgunun kendi içindeki GROUP BY meşrudur.)
            self.assertNotIn('LEFT OUTER JOIN "icerik_haber_kaynaklar"', sql)
