"""Künye — 3 Eylül 2026'da yeniden kuruldu (§49).

Kullanıcı isteği iki başlıktaydı: künyenin tasarımı beğenilmiyordu ve
**"bir yanda sütunlar varken diğer yanda tek satırda ilerleyen başka bir
sıra"** kalkacaktı. Buradaki testler o kararı ve onarılan kusurları
kilitler:

1. Sütunların altından ENİNE akan iki sıra kalktı. İlçe şeridi sütun
   oldu; künye bilgileri (imtiyaz sahibi, sorumlu müdür, yayın türü) ve
   uzun veri kaynağı beyanı ise kullanıcı isteğiyle künyeden tamamen
   kaldırıldı — altta yalnız telif satırı kaldı.
2. **Ölü bağlantı kalmaz.** Sayfası olmayan kalem künyeye yazılmaz;
   anasayfa çapaları "/" önekli verilir, yoksa kategori ve haber
   sayfalarında hiçbir yere gitmezler.
3. Arşiv kapsamı cümlesi VERİDEN gelir; sayılamazsa hiç basılmaz.
"""

import re
import time

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from taksonomi.models import Ilce, Kategori, KategoriTur

from . import baglam
from .models import Haber

# Künyenin çizildiği sayfalar. Kusurun tamamı anasayfada görünmüyordu:
# `#panel-hava` gibi çapalar YALNIZ anasayfada çalışıyor, asıl kırık
# oldukları yer kategori ve haber sayfaları.
SAYFALAR = ("/", "/bursaspor")


class KunyeYapisi(TestCase):

    @classmethod
    def setUpTestData(cls):
        call_command("taksonomi_kur", verbosity=0)
        tur = KategoriTur.objects.filter(
            tur=Kategori.TUR_HABER, slug="bursaspor").first()
        for n in range(3):
            Haber.objects.create(
                id=960000 + n, slug=f"kunye-{n}", baslik=f"Künye başlığı {n}",
                spot="spot", govde="<p>gövde</p>", kategori=tur.kategori,
                yayin_zamani=timezone.now() - timezone.timedelta(minutes=n))

    def setUp(self):
        baglam._kunye_bellek = None

    def _kunye(self, yol="/"):
        govde = self.client.get(yol).content.decode()
        self.assertIn('<footer id="kunye"', govde)
        return govde[govde.index('<footer id="kunye"'):]

    # --- 1. tek ritim ----------------------------------------------------

    def test_ilceler_serit_degil_sutun(self):
        """17 ilçe artık sütun ızgarasının İÇİNDE, altından akan şerit değil."""
        kunye = self._kunye()
        izgara = kunye[kunye.index('class="kunye-ust"'):kunye.index('class="kunye-alt"')]
        for ilce in Ilce.objects.all():
            self.assertIn(f'href="/ilce/{ilce.slug}"', izgara)
        # Eski şeridin işareti: `<b>İLÇELER</b>` etiketi ve sütun dışı yer.
        self.assertNotIn("<b>İLÇELER</b>", kunye)
        self.assertIn("<h2>İLÇELER</h2>", kunye)

    def test_kunye_bilgileri_tamamen_kalkti(self):
        """İmtiyaz sahibi · sorumlu müdür · yayın türü künyeden kaldırıldı.

        Kullanıcı kararı (3 Eylül 2026). Değerler yer tutucuydu ve künyede
        durmaları istenmedi; blok tamamen kalktı, kalıntı bırakmadan.
        """
        kunye = self._kunye()
        for kalinti in ("İmtiyaz sahibi", "Sorumlu yazı işleri müdürü",
                        "Yayın türü", "Yerel süreli yayın",
                        "reklam@ornek.local", "<dl>"):
            self.assertNotIn(kalinti, kunye)

    def test_alt_satirda_yalniz_telif_var(self):
        """Uzun veri kaynağı beyanı ve yanındaki bağlantı kaldırıldı."""
        kunye = self._kunye()
        alt = kunye[kunye.index('class="kunye-alt"'):]
        self.assertIn("© 2026 Bursa Hakimiyet, hakları saklıdır.", alt)
        self.assertNotIn("Bölüm bölüm veri kaynağı ve kapsam", alt)
        self.assertNotIn("TCMB", alt)
        self.assertNotIn("<a ", alt)

    def test_beyan_sayfasi_kunyeden_hala_ulasilabilir(self):
        """Beyan SİLİNMEDİ, yalnız künyeden çıktı: sütunda bağlantısı duruyor."""
        kunye = self._kunye()
        self.assertIn('href="/veri-kaynaklari"', kunye)
        self.assertEqual(self.client.get("/veri-kaynaklari").status_code, 200)

    def test_takip_edin_sutunu_kalkti(self):
        """Sosyal şeridin hemen altında aynı hesapları tekrarlıyordu."""
        kunye = self._kunye()
        self.assertNotIn("TAKİP EDİN", kunye)

    # --- 2. olu baglanti -------------------------------------------------

    def test_liste_sutunlarinda_olu_baglanti_yok(self):
        """Sayfası olmayan kalem künyeye yazılmaz."""
        for yol in SAYFALAR:
            with self.subTest(yol=yol):
                kunye = self._kunye(yol)
                listeler = re.findall(r"<ul>(.*?)</ul>", kunye, re.S)
                self.assertTrue(listeler)
                for liste in listeler:
                    self.assertNotIn('href="#"', liste)

    def test_capalar_her_sayfada_calisan_bicimde(self):
        """`#panel-hava` yalnız anasayfada çalışırdı; artık `/#panel-hava`."""
        for yol in SAYFALAR:
            with self.subTest(yol=yol):
                kunye = self._kunye(yol)
                for capa in ("panel-hava", "panel-vakit", "vizyon"):
                    self.assertIn(f'href="/#{capa}"', kunye)
                    self.assertNotIn(f'href="#{capa}"', kunye)

    def test_kunyedeki_baglantilar_gercekten_aciliyor(self):
        """Künyede duran her yerel adres 200 ya da yönlendirme vermeli."""
        kunye = self._kunye()
        adresler = {a for a in re.findall(r'href="(/[^"#]*)"', kunye)
                    if not a.startswith("/static/")}
        self.assertGreaterEqual(len(adresler), 8)
        for adres in sorted(adresler):
            with self.subTest(adres=adres):
                yanit = self.client.get(adres)
                self.assertIn(yanit.status_code, (200, 301, 302), adres)

    def test_sosyal_hesaplar_disinda_olu_bag_kalmadi(self):
        """Dört sosyal hesabın adresi kullanıcıdan bekleniyor; RSS bağlandı."""
        kunye = self._kunye()
        self.assertEqual(kunye.count('href="#"'), 4)
        sosyal = kunye[kunye.index('class="sosyal"'):kunye.index("</div>", kunye.index('class="sosyal"'))]
        self.assertEqual(sosyal.count('href="#"'), 4)
        self.assertIn('href="/rss"', sosyal)

    # --- 3. arsiv kapsami veriden ----------------------------------------

    def test_arsiv_kapsami_veritabanindan_geliyor(self):
        kunye = self._kunye()
        self.assertIn("haber arşivde", kunye)
        self.assertIn(str(timezone.now().year), kunye)
        # Sayı şablona çakılı değil: kayıt eklenince değişiyor.
        tur = KategoriTur.objects.filter(
            tur=Kategori.TUR_HABER, slug="bursaspor").first()
        Haber.objects.create(
            id=970001, slug="kunye-yeni", baslik="Yeni", spot="s",
            govde="<p>g</p>", kategori=tur.kategori,
            yayin_zamani=timezone.now())
        baglam._kunye_bellek = None
        self.assertIn("<strong>4</strong> haber arşivde", self._kunye())

    def test_sayilamayinca_cumle_hic_basilmiyor(self):
        """Yanlış sayı yazmaktansa hiç yazmamak (27 Ağustos'un dersi).

        Sayım kilide takıldığında `_kunye_arsiv` `None` döner; buradaki
        sınama şablonun o hâlde cümleyi HİÇ basmadığını kilitliyor.
        Önbellek doğrudan kuruluyor — `Haber.yayindakiler` yamalanırsa
        sayfanın kendi haber sorgusu da düşer ve sınanan şey kaybolur.
        """
        baglam._kunye_bellek = (time.monotonic(), None)
        kunye = self._kunye()
        self.assertNotIn("haber arşivde", kunye)
        # Sayfanın geri kalanı ayakta: künye kusuru sayfayı düşürmez.
        self.assertIn("<h2>İLÇELER</h2>", kunye)

    def test_hata_onbellege_yaziliyor(self):
        """Hata önbelleklenmezse göç sürerken her istek kilide yeniden girer.

        `views.arsiv_sayilari` bu tuzağı taşıyor (hata durumunu yazmıyor);
        künye satırı sayfayı beş saniye bekletmeye değmez.
        """
        from unittest.mock import patch

        from django.db import DatabaseError
        with patch.object(Haber, "yayindakiler",
                          side_effect=DatabaseError("kilit")) as sahte:
            baglam._kunye_bellek = None
            self.assertIsNone(baglam._kunye_arsiv())
            self.assertIsNone(baglam._kunye_arsiv())
            self.assertIsNone(baglam._kunye_arsiv())
        self.assertEqual(sahte.call_count, 1)
