"""`/kose-yazilari` — köşe yazıları sayfası (19 Ekim 2026).

Kullanıcı isteği: "köşe yazıları diye bir sayfamız da olsun." `/yazarlar`
yazarları listeler; bu sayfa yazıların kendisini. Korunanlar:

1. **Adres.** Tek dilimli `/kose-yazilari` medya tablosunda çözülür;
   kök tablonun sonundaki kategori kalıbı onu "kategori" sanıp 404
   vermemeli. Sondaki eğik çizgi 301 alır (Paket G).
2. **Yazarların son yazıları.** Yazar başına TEK kart, en yeniden eskiye;
   pasif yazar ve yayında olmayan yazı girmez; giriş gövdeden kırpılmış düz
   metin (yeni cümle yok).
3. **Akış.** Bütün yazılar en yeniden eskiye; "daha fazla göster" düğmesi
   `?sayfa=N` bağlantısı + `/daha-fazla?kaynak=kose` parçası, dilimler
   çakışmaz; aralık dışı sayfa 404.
4. **Başarım.** Sorgu sayısı yazar ve yazı sayısıyla BÜYÜMEZ (N+1 yok);
   anonim sayfa önbelleğine girer ve köşe yazısı kaydedilince düşer.
5. **Tema ve bağlantılar.** Köşe teması kayıttan; anasayfa yazar kuşağı
   ve `/yazarlar` sayfası bu sayfaya bağlanır.
"""

import json
import re
from datetime import timedelta

from django.db import connection
from django.test import SimpleTestCase, TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import resolve
from django.utils import timezone

from icerik import temalar

from .models import KoseYazisi, Yazar, duz_giris

LOCMEM = "django.core.cache.backends.locmem.LocMemCache"
SAYFA_ACIK = override_settings(
    CACHES={"default": {"BACKEND": LOCMEM, "LOCATION": "bh-kose-veri"},
            "sayfa": {"BACKEND": LOCMEM, "LOCATION": "bh-kose-sayfa"}},
    SAYFA_ONBELLEK_SANIYE=30)

#: Kabuğu ısınmış, sayfa önbelleği kapalı istekte sorgu tavanı. Ölçülen:
#: 3 (sayım, akış dilimi, yazar başına son yazı) — 2 yazarda da 32'de de.
#: Asıl kanıt `test_sorgu_sayisi_kayitla_buyumuyor`: az ve çok veride AYNI.
SORGU_TAVANI = 3


def _govde(yanit) -> str:
    return yanit.content.decode()


def _kartlar(metin: str) -> list[str]:
    return re.findall(r'<li class="kose-kart">.*?</li>', metin, re.S)


def _akis_adresleri(metin: str) -> list[str]:
    """Akış satırlarındaki yazı adresleri (yazar adresi değil), sırasıyla."""
    return re.findall(r'</a><a href="(/yazarlar/[^"/]+/[^"/]+)">', metin)


# ---------------------------------------------------------------- adres

class AdresCozumu(SimpleTestCase):

    def test_kose_yazilari_kategori_sanilmiyor(self):
        eslesme = resolve("/kose-yazilari")
        self.assertEqual(eslesme.view_name, "medya:kose-yazilari")
        self.assertNotEqual(eslesme.url_name, "kategori")

    def test_yazar_ve_kose_kaliplari_bozulmadi(self):
        self.assertEqual(resolve("/yazarlar").view_name, "medya:yazarlar")
        self.assertEqual(resolve("/yazarlar/ali-genc-72").view_name, "medya:yazar")
        self.assertEqual(
            resolve("/yazarlar/ali-genc-72/istihdamda-esitlik-bir-hayal-32069").view_name,
            "medya:kose")


class DuzGiris(SimpleTestCase):
    """Giriş metni gövdenin kendi cümlelerinden kırpılır."""

    def test_paragraflar_boslukla_ayrilir_varliklar_cozulur(self):
        self.assertEqual(duz_giris("<p>Bir&#039;in.</p><p>İki &amp; <b>üç</b>.</p>", 100),
                         "Bir'in. İki & üç.")

    def test_betik_ve_yarim_etiket_duser(self):
        ham = '<p>Metin</p><script>var x = "gizli";</script><p>devam</p><img src="x'
        self.assertEqual(duz_giris(ham, 100), "Metin devam")

    def test_kelime_sinirinda_kesilir(self):
        metin = duz_giris("<p>" + "kelime " * 50 + "</p>", 40)
        self.assertTrue(metin.endswith("kelime…"), metin)
        self.assertLessEqual(len(metin), 41)


# ---------------------------------------------------------------- sayfa

class KoseYazilariSayfasi(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.simdi = simdi = timezone.now().replace(microsecond=0)
        cls.ali = Yazar.objects.create(id=990072, slug="ali-genc", ad="Ali GENÇ")
        cls.ayse = Yazar.objects.create(id=990073, slug="ayse-kaya", ad="Ayşe KAYA")
        cls.eski = Yazar.objects.create(id=990074, slug="eski-yazar", ad="Eski YAZAR")
        cls.pasif = Yazar.objects.create(id=990075, slug="pasif-yazar", ad="Pasif YAZAR",
                                         aktif=False)
        # Ali'nin 25 yazısı (akış iki sayfaya taşsın): en yenisi 1 saat önce.
        for n in range(25):
            KoseYazisi.objects.create(
                id=993000 + n, slug=f"ali-yazi-{n}", baslik=f"Ali yazısı {n}",
                spot=f"Ali yazısı {n}", yazar=cls.ali, kelime_sayisi=600,
                govde=f"<p>Ali&#039;nin {n}. yazısının ilk cümlesi.</p><p>İkinci paragraf.</p>",
                yayin_zamani=simdi - timedelta(hours=1 + n))
        # Ayşe'nin EN YENİ yazısı yayında değil: kartı bir öncekinden gelmeli.
        KoseYazisi.objects.create(
            id=993100, slug="ayse-taslak", baslik="Ayşe taslak", yazar=cls.ayse,
            govde="<p>Taslak.</p>", durum=KoseYazisi.DURUM_PASIF, yayin_zamani=simdi)
        KoseYazisi.objects.create(
            id=993101, slug="ayse-yayinda", baslik="Ayşe yayında", yazar=cls.ayse,
            govde="<p>Ayşe&#039;nin yayındaki yazısı.</p>",
            yayin_zamani=simdi - timedelta(minutes=30))
        KoseYazisi.objects.create(
            id=993102, slug="ayse-eski", baslik="Ayşe eski", yazar=cls.ayse,
            govde="<p>Eski.</p>", yayin_zamani=simdi - timedelta(days=3))
        # Eski yazar: son yazısı yıllar önce — yine listelenir, tarihiyle.
        KoseYazisi.objects.create(
            id=993200, slug="eski-son", baslik="Eski yazarın son yazısı", yazar=cls.eski,
            govde="<p>" + "uzun bir giriş cümlesi " * 30 + "</p>",
            yayin_zamani=simdi - timedelta(days=900))
        # Pasif yazarın en yeni yazısı hiçbir listede görünmemeli.
        KoseYazisi.objects.create(
            id=993300, slug="pasif-yazi", baslik="Pasif yazarın yazısı", yazar=cls.pasif,
            govde="<p>Pasif.</p>", yayin_zamani=simdi - timedelta(minutes=5))

    def setUp(self):
        self.yanit = self.client.get("/kose-yazilari")
        self.assertEqual(self.yanit.status_code, 200)
        self.metin = _govde(self.yanit)

    # -- iskelet ve SEO ---------------------------------------------------

    def test_iskelet_tek_h1_ve_tema(self):
        self.assertEqual(self.metin.count("<h1"), 1)
        self.assertIn("<h1>Köşe Yazıları</h1>", self.metin)
        self.assertIn('<body data-bolum="kose">', self.metin)
        self.assertIn("<title>Köşe Yazıları — Bursa Hakimiyet</title>", self.metin)

    def test_kanonik_ve_kirinti_jsonld(self):
        self.assertRegex(self.metin, r'<link rel="canonical" href="https?://[^"]+/kose-yazilari">')
        bloklar = [json.loads(b) for b in re.findall(
            r'<script type="application/ld\+json">(.*?)</script>', self.metin, re.S)]
        kirinti = [b for b in bloklar if b.get("@type") == "BreadcrumbList"]
        self.assertEqual(len(kirinti), 1)
        ogeler = kirinti[0]["itemListElement"]
        self.assertEqual([o["name"] for o in ogeler], ["Anasayfa", "Köşe Yazıları"])
        self.assertTrue(ogeler[-1]["item"].endswith("/kose-yazilari"))

    def test_sondaki_egik_cizgi_301(self):
        yanit = self.client.get("/kose-yazilari/")
        self.assertEqual(yanit.status_code, 301)
        self.assertEqual(yanit["Location"], "/kose-yazilari")

    # -- yazarların son yazıları ----------------------------------------

    def test_yazar_basina_tek_kart_en_yeni_once(self):
        kartlar = _kartlar(self.metin)
        self.assertEqual(len(kartlar), 3)          # Ali, Ayşe, Eski — pasif yok
        adlar = [re.search(r'class="gorus-ad"[^>]*>([^<]+)<', k).group(1) for k in kartlar]
        self.assertEqual(adlar, ["Ayşe KAYA", "Ali GENÇ", "Eski YAZAR"])
        self.assertIn("Ayşe yayında", kartlar[0])  # taslak değil, yayındaki son yazı
        self.assertIn("Ali yazısı 0", kartlar[1])
        self.assertNotIn("Pasif", self.metin)

    def test_kart_tarihi_ve_girisi(self):
        kart = _kartlar(self.metin)[1]
        self.assertRegex(kart, r'<time class="gorus-sayi" datetime="[^"]+">')
        self.assertIn("<p>Ali&#x27;nin 0. yazısının ilk cümlesi. İkinci paragraf.</p>", kart)
        uzun = re.search(r"<p>(.*?)</p>", _kartlar(self.metin)[2]).group(1)
        self.assertTrue(uzun.endswith("…"), uzun)
        self.assertLessEqual(len(uzun), KoseYazisi.GIRIS_SINIRI + 1)

    def test_yazar_basina_son_tek_sorgu(self):
        with self.assertNumQueries(1):
            kartlar = list(KoseYazisi.yazar_basina_son())
            [(k.giris, k.yazar.ad, k.get_absolute_url()) for k in kartlar]
        self.assertEqual([k.pk for k in kartlar], [993101, 993000, 993200])

    # -- akış -----------------------------------------------------------

    def test_akis_en_yeni_once_ve_ilk_dilim(self):
        adresler = _akis_adresleri(self.metin)
        self.assertEqual(len(adresler), KoseYazisi.AKIS_BOYU)
        beklenen = [y.get_absolute_url() for y in KoseYazisi.akis()[:KoseYazisi.AKIS_BOYU]]
        self.assertEqual(adresler, beklenen)
        self.assertEqual(adresler[0], "/yazarlar/ayse-kaya-990073/ayse-yayinda-993101")
        self.assertEqual(adresler[1], "/yazarlar/ali-genc-990072/ali-yazi-0-993000")
        # Akışta yazar da yazılı.
        self.assertIn('<a class="kose-satir-yazar" href="/yazarlar/ayse-kaya-990073">Ayşe KAYA</a>',
                      self.metin)

    def test_dugme_baglanti_ve_parca(self):
        self.assertIn('href="?sayfa=2" rel="next"', self.metin)
        self.assertIn('data-uc="/daha-fazla?kaynak=kose"', self.metin)
        self.assertIn('data-hedef=".kose-akis"', self.metin)
        parca = self.client.get("/daha-fazla?kaynak=kose&sayfa=2")
        self.assertEqual(parca.status_code, 200)
        parca_metin = _govde(parca)
        self.assertIn('data-devam="0"', parca_metin)   # 28 yazı: ikinci dilim son
        ikinci = _akis_adresleri(parca_metin)
        self.assertEqual(len(ikinci), 28 - KoseYazisi.AKIS_BOYU)
        self.assertFalse(set(ikinci) & set(_akis_adresleri(self.metin)))
        self.assertTrue(ikinci[-1].endswith("eski-son-993200"))

    def test_ikinci_sayfa_jssiz_karsilik(self):
        yanit = self.client.get("/kose-yazilari?sayfa=2")
        self.assertEqual(yanit.status_code, 200)
        metin = _govde(yanit)
        self.assertEqual(_kartlar(metin), [])            # vitrin yalnız 1. sayfada
        self.assertIn("— Sayfa 2 — Bursa Hakimiyet</title>", metin)
        self.assertRegex(metin, r'<link rel="canonical" href="[^"]+/kose-yazilari\?sayfa=2">')
        self.assertEqual(_akis_adresleri(metin),
                         _akis_adresleri(_govde(self.client.get("/daha-fazla?kaynak=kose&sayfa=2"))))
        self.assertNotIn("daha-fazla-kap", metin)        # son sayfa: düğme yok
        self.assertEqual(metin.count("<h1"), 1)

    def test_aralik_disi_sayfa_404(self):
        for deger in ("3", "0", "abc"):
            with self.subTest(deger):
                self.assertEqual(self.client.get(f"/kose-yazilari?sayfa={deger}").status_code, 404)

    # -- bağlantılar ----------------------------------------------------

    def test_anasayfa_ve_yazarlar_baglaniyor(self):
        for yol in ("/", "/yazarlar"):
            with self.subTest(yol):
                self.assertIn('<a href="/kose-yazilari">Tüm köşe yazıları &rarr;</a>',
                              _govde(self.client.get(yol)))

    def test_tema_kaydi_sayfayi_kapsiyor(self):
        self.assertIn("/kose-yazilari", temalar.TEMALAR["kose"].kapsam)


class KoseYazilariBasarim(TestCase):
    """N+1 yok: sorgu sayısı yazar ve yazı sayısıyla büyümez."""

    @staticmethod
    def _veri(yazar_adedi: int, yazi_adedi: int, taban: int):
        simdi = timezone.now()
        for y in range(yazar_adedi):
            yazar = Yazar.objects.create(id=taban + y, slug=f"b-yazar-{taban + y}",
                                         ad=f"Yazar {taban + y}")
            for n in range(yazi_adedi):
                KoseYazisi.objects.create(
                    id=taban * 100 + y * yazi_adedi + n, slug=f"b-yazi-{n}",
                    baslik=f"Yazı {y}-{n}", yazar=yazar, govde="<p>Gövde metni.</p>",
                    yayin_zamani=simdi - timedelta(minutes=y * yazi_adedi + n))

    def _say(self, yol):
        with CaptureQueriesContext(connection) as yakala:
            yanit = self.client.get(yol)
        self.assertEqual(yanit.status_code, 200, yol)
        return len(yakala.captured_queries)

    def test_sorgu_sayisi_kayitla_buyumuyor(self):
        self._veri(2, 3, 9900)
        # İlk istek kabuğun veri önbelleğini (menü, ilçeler, sayılar) ısıtır;
        # karşılaştırma ısınmış kabukla, yalnız sayfanın kendi sorguları.
        self._say("/kose-yazilari")
        az = {yol: self._say(yol) for yol in ("/kose-yazilari", "/daha-fazla?kaynak=kose")}
        self._veri(30, 4, 9800)
        cok = {yol: self._say(yol) for yol in ("/kose-yazilari", "/daha-fazla?kaynak=kose")}
        self.assertEqual(az, cok)
        self.assertLessEqual(cok["/kose-yazilari"], SORGU_TAVANI, cok)
        # 32 yazar → 32 kart, yine aynı sorgu sayısıyla.
        self.assertEqual(len(_kartlar(_govde(self.client.get("/kose-yazilari")))), 32)

    @SAYFA_ACIK
    def test_anonim_sayfa_onbellegi_ve_kayitla_dusmesi(self):
        self._veri(2, 2, 9700)
        ilk = self.client.get("/kose-yazilari")
        self.assertEqual(ilk["X-Onbellek"], "kayit")
        with CaptureQueriesContext(connection) as yakala:
            ikinci = self.client.get("/kose-yazilari")
        self.assertEqual(ikinci["X-Onbellek"], "isabet")
        self.assertEqual(len(yakala.captured_queries), 0)
        # Panelden yeni yazı: sayfa beklemeden yenilenir.
        KoseYazisi.objects.create(
            id=9999999, slug="yeni", baslik="Yepyeni köşe yazısı", yazar=Yazar.objects.first(),
            govde="<p>Yeni.</p>", yayin_zamani=timezone.now())
        ucuncu = self.client.get("/kose-yazilari")
        self.assertEqual(ucuncu["X-Onbellek"], "kayit")
        self.assertIn("Yepyeni köşe yazısı", _govde(ucuncu))
