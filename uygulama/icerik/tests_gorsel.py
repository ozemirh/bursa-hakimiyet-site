"""Görsel hattı — türev görünümü, şablon etiketi, alt metin (19 Ekim 2026).

Arşiv ve türev kökleri her testte geçici klasöre çevrilir; gerçek arşive
(`D:/bursa-hakimiyet-arsiv`) ne okunur ne yazılır.
"""

import re
import shutil
import tempfile
import threading
import time
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from django.contrib.auth.models import User
from django.core.management import call_command
from django.template import Context, Template
from django.test import SimpleTestCase, TestCase, override_settings
from django.utils import timezone

from icerik import gorsel_turev as gt
from icerik.templatetags import gorsel_etiket as ge
from taksonomi.models import Kategori, KategoriTur

from .models import Haber


def _jpeg(yol: Path, en=1600, boy=1067, yon=None, renk=(180, 40, 40)):
    from PIL import Image
    yol.parent.mkdir(parents=True, exist_ok=True)
    im = Image.new("RGB", (en, boy), renk)
    if yon:
        exif = Image.Exif()
        exif[0x0112] = yon
        im.save(yol, "JPEG", quality=90, exif=exif)
    else:
        im.save(yol, "JPEG", quality=90)
    return yol


class _GeciciKokler:
    """Her test için boş arşiv + boş türev kökü."""

    def setUp(self):
        super().setUp()
        self.arsiv = Path(tempfile.mkdtemp(prefix="bh-arsiv-"))
        self.turev = Path(tempfile.mkdtemp(prefix="bh-turev-"))
        self.ayar = override_settings(ARSIV_KOK=self.arsiv, TUREV_KOK=self.turev,
                                      ARSIV_GORSEL_KOK=self.arsiv / "gorseller")
        self.ayar.enable()
        gt._olcu_oku.cache_clear()
        self.kaynak = _jpeg(self.arsiv / "gorseller" / "2026-08" / "a_large.jpg")
        self.adres = "/gorsel/480/gorseller/2026-08/a_large.jpg.webp"

    def tearDown(self):
        self.ayar.disable()
        gt._olcu_oku.cache_clear()
        shutil.rmtree(self.arsiv, ignore_errors=True)
        shutil.rmtree(self.turev, ignore_errors=True)
        super().tearDown()


class TurevGorunumu(_GeciciKokler, TestCase):

    def _olcu(self, yanit):
        from io import BytesIO
        from PIL import Image
        with Image.open(BytesIO(yanit.content)) as im:
            return im.format, im.size

    def test_ilk_istek_uretir_diske_yazar_ve_webp_doner(self):
        yanit = self.client.get(self.adres)
        self.assertEqual(yanit.status_code, 200)
        self.assertEqual(yanit["Content-Type"], "image/webp")
        self.assertEqual(self._olcu(yanit), ("WEBP", (480, 320)))
        self.assertTrue((self.turev / "480" / "gorseller" / "2026-08"
                         / "a_large.jpg.webp").is_file())

    def test_onbellek_basliklari_ve_kosullu_istek(self):
        yanit = self.client.get(self.adres)
        self.assertIn("max-age=31536000", yanit["Cache-Control"])
        self.assertIn("public", yanit["Cache-Control"])
        self.assertTrue(yanit["ETag"].startswith('"'))
        self.assertIn("Last-Modified", yanit)
        ikinci = self.client.get(self.adres, HTTP_IF_NONE_MATCH=yanit["ETag"])
        self.assertEqual(ikinci.status_code, 304)
        self.assertEqual(ikinci["ETag"], yanit["ETag"])

    def test_ikinci_istek_dosyadan_gelir(self):
        self.client.get(self.adres)
        with mock.patch.object(gt, "_hazirla", side_effect=AssertionError("yeniden üretildi")):
            yanit = self.client.get(self.adres)
        self.assertEqual(yanit.status_code, 200)

    def test_kaynak_yenilenirse_turev_yenilenir(self):
        self.client.get(self.adres)
        hedef = self.turev / "480" / "gorseller" / "2026-08" / "a_large.jpg.webp"
        eski = hedef.stat().st_mtime_ns
        time.sleep(0.02)
        _jpeg(self.kaynak, renk=(10, 10, 200))
        self.client.get(self.adres)
        self.assertGreater(hedef.stat().st_mtime_ns, eski)

    def test_beyaz_liste_disi_genislik_404(self):
        for boyut in ("500", "100", "2560", "0480"):
            with self.subTest(boyut=boyut):
                yanit = self.client.get(f"/gorsel/{boyut}/gorseller/2026-08/a_large.jpg.webp")
                self.assertEqual(yanit.status_code, 404)
        self.assertEqual(list(self.turev.rglob("*.webp")), [])

    def test_yol_gecisi_reddedilir(self):
        (self.arsiv / "veri").mkdir()
        _jpeg(self.arsiv / "veri" / "gizli.jpg")
        for yol in ("gorseller/../veri/gizli.jpg.webp",
                    "gorseller/%2e%2e/veri/gizli.jpg.webp",
                    "gorseller/2026-08/..%2f..%2fveri/gizli.jpg.webp",
                    "gorseller\\..\\veri\\gizli.jpg.webp",
                    "/gorseller/2026-08/a_large.jpg.webp",
                    "C:/Windows/x.jpg.webp",
                    "veri/gizli.jpg.webp",
                    "gorseller/./2026-08/a_large.jpg.webp",
                    "gorseller//2026-08/a_large.jpg.webp"):
            with self.subTest(yol=yol):
                self.assertEqual(self.client.get("/gorsel/480/" + yol).status_code, 404)
        self.assertEqual(list(self.turev.rglob("*.webp")), [])

    def test_kok_disina_cikan_baglanti_reddedilir(self):
        """Çözülen yol kökün içinde kalmalı (sembolik bağ/junction dahil)."""
        with self.assertRaises(gt.GecersizIstek):
            gt.kaynak_coz("gorseller/2026-08/../../veri/gizli.jpg")

    def test_raster_disi_kaynak_reddedilir(self):
        klasor = self.arsiv / "gorseller" / "2026-08"
        (klasor / "kotu.svg").write_text("<svg onload='alert(1)'/>", encoding="utf-8")
        (klasor / "sahte.jpg").write_text("<html><script>alert(1)</script></html>",
                                          encoding="utf-8")
        (klasor / "not.txt").write_text("x", encoding="utf-8")
        for ad in ("kotu.svg", "sahte.jpg", "not.txt"):
            with self.subTest(ad=ad):
                yanit = self.client.get(f"/gorsel/480/gorseller/2026-08/{ad}.webp")
                self.assertEqual(yanit.status_code, 404)

    def test_cikti_uzantisi_zorunlu(self):
        self.assertEqual(self.client.get(
            "/gorsel/480/gorseller/2026-08/a_large.jpg").status_code, 404)
        self.assertEqual(self.client.get(
            "/gorsel/og/gorseller/2026-08/a_large.jpg.webp").status_code, 404)

    def test_olmayan_kaynak_404(self):
        self.assertEqual(self.client.get(
            "/gorsel/480/gorseller/2026-08/yok.jpg.webp").status_code, 404)

    def test_piksel_ve_bayt_siniri(self):
        with mock.patch.object(gt, "EN_BUYUK_PIKSEL", 1000):
            self.assertEqual(self.client.get(self.adres).status_code, 404)
        with mock.patch.object(gt, "EN_BUYUK_BAYT", 10):
            self.assertEqual(self.client.get(
                "/gorsel/320/gorseller/2026-08/a_large.jpg.webp").status_code, 404)

    def test_buyutme_yok(self):
        _jpeg(self.arsiv / "gorseller" / "2026-08" / "kucuk.jpg", en=800, boy=533)
        yanit = self.client.get("/gorsel/1280/gorseller/2026-08/kucuk.jpg.webp")
        self.assertEqual(self._olcu(yanit), ("WEBP", (800, 533)))

    def test_exif_yonu_duzeltilir(self):
        # Yön 6: kayıtlı 600x400, okura 400x600 görünür.
        _jpeg(self.arsiv / "gorseller" / "2026-08" / "dik.jpg", en=600, boy=400, yon=6)
        yanit = self.client.get("/gorsel/320/gorseller/2026-08/dik.jpg.webp")
        self.assertEqual(self._olcu(yanit), ("WEBP", (320, 480)))
        self.assertEqual(gt.olcu("gorseller/2026-08/dik.jpg"), ((400, 600), True))

    def test_og_kirpimi_1200x630_jpeg(self):
        yanit = self.client.get("/gorsel/og/gorseller/2026-08/a_large.jpg.jpg")
        self.assertEqual(yanit.status_code, 200)
        self.assertEqual(yanit["Content-Type"], "image/jpeg")
        self.assertEqual(self._olcu(yanit), ("JPEG", (1200, 630)))

    def test_yazma_istegi_reddedilir(self):
        self.assertEqual(self.client.post(self.adres).status_code, 405)

    def test_eszamanli_istek_tek_uretim(self):
        sayac = []
        asil = gt._yaz

        def yavas_yaz(*a, **k):
            sayac.append(1)
            time.sleep(0.3)
            return asil(*a, **k)

        sonuclar = []
        with mock.patch.object(gt, "_yaz", side_effect=yavas_yaz):
            isler = [threading.Thread(target=lambda: sonuclar.append(
                gt.turev_hazirla("640", "gorseller/2026-08/a_large.jpg.webp")))
                for _ in range(4)]
            for i in isler:
                i.start()
            for i in isler:
                i.join()
        self.assertEqual(len(sayac), 1)
        self.assertEqual(len(set(sonuclar)), 1)
        # Geçici dosya ve kilit artığı kalmaz.
        artik = [p.name for p in self.turev.rglob("*") if p.is_file()
                 and (p.name.endswith(".kilit") or p.name.endswith(".gecici"))]
        self.assertEqual(artik, [])

    def test_bayat_kilit_temizlenir(self):
        hedef = self.turev / "640" / "gorseller" / "2026-08" / "a_large.jpg.webp"
        hedef.parent.mkdir(parents=True)
        kilit = hedef.with_name(hedef.name + ".kilit")
        kilit.write_text("")
        eski = time.time() - gt.BAYAT_KILIT_SN - 5
        import os
        os.utime(kilit, (eski, eski))
        self.assertEqual(self.client.get(
            "/gorsel/640/gorseller/2026-08/a_large.jpg.webp").status_code, 200)

    def test_toplu_uretim_tek_cozumle_hepsini_yazar(self):
        sonuc = gt.tum_turevler("gorseller/2026-08/a_large.jpg")
        self.assertEqual(sonuc["uretilen"], len(gt.GENISLIKLER) + 1)
        tekrar = gt.tum_turevler("gorseller/2026-08/a_large.jpg")
        self.assertEqual((tekrar["uretilen"], tekrar["atlanan"]),
                         (0, len(gt.GENISLIKLER) + 1))


class GorselEtiketi(_GeciciKokler, SimpleTestCase):

    def _bas(self, sablon, **baglam):
        return Template("{% load gorsel_etiket %}" + sablon).render(Context(baglam))

    def _haber(self, dosya="2026-08/a_large.jpg", alt="Google News"):
        return SimpleNamespace(gorsel_yolu="/arsiv-gorsel/" + dosya,
                               gorsel_alt=alt, baslik="Nilüfer'de yeni köprü")

    def test_kart_ciktisi(self):
        html = self._bas('{% gorsel h "kart" %}', h=self._haber())
        for g in gt.GENISLIKLER:
            self.assertIn(f"/gorsel/{g}/gorseller/2026-08/a_large.jpg.webp {g}w", html)
        self.assertIn(f'sizes="{ge.YUVALAR["kart"][0]}"', html)
        self.assertIn('width="1280" height="854"', html)   # 1600x1067 → 1280'e
        self.assertIn('loading="lazy"', html)
        self.assertIn('decoding="async"', html)
        self.assertNotIn("fetchpriority", html)
        self.assertIn('src="/gorsel/480/', html)

    def test_oncelikli_ve_hemen(self):
        html = self._bas('{% gorsel h "manset" oncelikli=True %}', h=self._haber())
        self.assertIn('loading="eager" fetchpriority="high"', html)
        self.assertIn('src="/gorsel/960/', html)
        html = self._bas('{% gorsel h "dortlu" hemen=True %}', h=self._haber())
        self.assertIn('loading="eager"', html)
        self.assertNotIn("fetchpriority", html)

    def test_ertelenen_slayt_karesi(self):
        html = self._bas('{% gorsel h "manset" ertele=True %}', h=self._haber())
        self.assertIn('data-src="/gorsel/960/', html)
        self.assertIn('data-srcset="', html)
        self.assertNotRegex(html, r'\s(src|srcset)="')
        # Öncelikli görsel hiçbir koşulda ertelenmez.
        html = self._bas('{% gorsel h "manset" ertele=True oncelikli=True %}', h=self._haber())
        self.assertRegex(html, r'<img src="/gorsel/960/')

    def test_yuvalar_farkli_sizes_basar(self):
        gorulen = set()
        for yuva in ("kart", "dortlu", "manset", "mini", "detay", "liste", "ikili",
                     "uclu", "galeri", "satir", "portre", "vesika"):
            html = self._bas("{% gorsel h yuva %}", h=self._haber(), yuva=yuva)
            gorulen.add(re.search(r'sizes="([^"]+)"', html).group(1))
        self.assertGreaterEqual(len(gorulen), 11)

    def test_genis_bayragi_genis_yuvayi_secer(self):
        html = self._bas('{% gorsel h "liste" genis=True %}', h=self._haber())
        self.assertIn(ge.YUVALAR["liste-genis"][0], html)

    def test_kucuk_kaynakta_srcset_kaynakta_durur(self):
        _jpeg(self.arsiv / "gorseller" / "2026-08" / "k.jpg", en=800, boy=533)
        html = self._bas('{% gorsel h "kart" %}', h=self._haber("2026-08/k.jpg"))
        self.assertIn("/gorsel/960/gorseller/2026-08/k.jpg.webp 800w", html)
        self.assertNotIn("/gorsel/1280/", html)
        self.assertIn('width="800" height="533"', html)

    def test_olcu_okunamazsa_cerceve_orani(self):
        html = self._bas('{% gorsel h "kart" %}', h=self._haber("2026-08/kayip.jpg"))
        self.assertIn('width="1280" height="853"', html)

    def test_google_news_alti_basliga_doner(self):
        html = self._bas('{% gorsel h "kart" %}', h=self._haber())
        self.assertIn('alt="Nilüfer&#x27;de yeni köprü"', html)
        self.assertNotIn("Google News", html)
        for anlamsiz in ("Google News", "google  news", "SON DAKİKA", " ", ""):
            self.assertEqual(ge.anlamli(anlamsiz), "", anlamsiz)
        self.assertEqual(ge.anlamli("Foto: Barış YALIM"), "Foto: Barış YALIM")

    def test_acik_bos_alt_korunur(self):
        html = self._bas('{% gorsel y "portre" alt="" %}',
                         y=SimpleNamespace(gorsel_yolu="/arsiv-medya/gorseller-yazar/a-portre.jpg",
                                           ad="Yazar Adı"))
        self.assertIn('alt=""', html)
        # CSS dosya adına bakıyor (img[src*="-portre"]): ad adreste korunur.
        self.assertIn('src="/gorsel/320/gorseller-yazar/a-portre.jpg.webp"', html)

    def test_site_fotografi_nitelikleri(self):
        html = self._bas('<img {% gorsel_ozellik "site/uludag.jpg" "panel" %} alt="">')
        self.assertIn('src="/gorsel/640/site/uludag.jpg.webp"', html)
        self.assertRegex(html, r'width="\d+" height="\d+"')

    def test_taninmayan_adres_duz_img(self):
        html = self._bas('{% gorsel h "kart" %}',
                         h=SimpleNamespace(gorsel_yolu="/statik/x.png", gorsel_alt="", baslik="B"))
        self.assertIn('src="/statik/x.png"', html)
        self.assertNotIn("srcset", html)

    def test_dis_adres_ve_ham_renk_yok(self):
        html = self._bas('{% gorsel h "detay" oncelikli=True %}', h=self._haber())
        self.assertNotRegex(html, r"https?://")
        kok = Path(__file__).resolve().parent
        for yol in (kok / "gorsel_turev.py", kok / "templatetags" / "gorsel_etiket.py"):
            metin = yol.read_text(encoding="utf-8")
            self.assertNotRegex(metin, r"#[0-9a-fA-F]{6}\b", yol.name)
            self.assertNotRegex(metin, r"https?://", yol.name)

    def test_og_adresi_site_kokunden(self):
        with override_settings(SITE_KOKU="https://ornek.test"):
            adres = ge.og_gorsel_adresi(self._haber())
        self.assertEqual(adres, "https://ornek.test/gorsel/og/gorseller/2026-08/a_large.jpg.jpg")


class AltMetinVeArsivNotu(_GeciciKokler, TestCase):
    """Haber detayında foto altı ve "silinmiş" notu — veritabanıyla."""

    @classmethod
    def setUpTestData(cls):
        call_command("taksonomi_kur", verbosity=0)
        cls.kategori = KategoriTur.objects.filter(
            tur=Kategori.TUR_HABER, slug="gundem").first().kategori
        cls.editor = User.objects.create_user("editor-gorsel", password="x-parola-123")

    def _haber(self, kimlik, **alan):
        return Haber.objects.create(
            id=kimlik, slug=f"gorsel-{kimlik}", baslik=f"Görsel deneme {kimlik}",
            spot="Spot", govde="<p>Gövde</p>", kategori=self.kategori,
            yayin_zamani=timezone.now(), **alan)

    def test_google_news_foto_alti_basilmaz_alt_basliktan(self):
        h = self._haber(880001, gorsel_var=True, gorsel_dosya="gorseller/2026-08/a_large.jpg",
                        gorsel_alt="Google News")
        icerik = self.client.get(h.get_absolute_url()).content.decode()
        self.assertNotIn("Google News", icerik)
        self.assertNotIn('<p class="foto-alt">', icerik)
        self.assertIn(f'alt="{h.baslik}"', icerik)
        self.assertRegex(icerik, r'<img src="/gorsel/960/[^"]+" srcset="[^"]+" sizes="[^"]+" '
                                 r'width="1280" height="854" alt="[^"]+" loading="eager" '
                                 r'fetchpriority="high"')

    def test_anlamli_foto_alti_basilir(self):
        h = self._haber(880002, gorsel_var=True, gorsel_dosya="gorseller/2026-08/a_large.jpg",
                        gorsel_alt="Foto: Barış YALIM")
        self.assertContains(self.client.get(h.get_absolute_url()),
                            '<p class="foto-alt">Foto: Barış YALIM</p>', html=False)

    def test_silinmis_notu_yalniz_arsiv_haberine(self):
        arsiv = self._haber(880003, gorsel_url="https://www.bursahakimiyet.com.tr/static/eski.jpg")
        panel = self._haber(880004, olusturan=self.editor,
                            gorsel_url="https://kaynak.example/foto.jpg")
        bos = self._haber(880005)
        notu = "arşiv fotoğrafı kaynak sunucudan silinmiş"
        self.assertContains(self.client.get(arsiv.get_absolute_url()), notu)
        for h in (panel, bos):
            with self.subTest(h=h.id):
                yanit = self.client.get(h.get_absolute_url())
                self.assertNotContains(yanit, notu)
                self.assertContains(yanit, "Görsel temsilîdir.")

    def test_sayfalarda_eski_tam_boy_adres_kalmadi(self):
        for n in range(56):
            self._haber(881000 + n, gorsel_var=True,
                        gorsel_dosya="gorseller/2026-08/a_large.jpg")
        for yol in ("/", "/gundem", Haber.objects.get(id=881000).get_absolute_url()):
            with self.subTest(yol=yol):
                icerik = self.client.get(yol).content.decode()
                imgler = re.findall(r"<img[^>]*>", icerik)
                arsivli = [i for i in imgler if "/gorsel/" in i or "/arsiv-gorsel/" in i]
                self.assertTrue(arsivli)
                self.assertFalse([i for i in arsivli if "/arsiv-gorsel/" in i])
                self.assertFalse([i for i in arsivli if "srcset" not in i])
                self.assertFalse([i for i in arsivli if "width=" not in i])
                self.assertNotRegex(" ".join(imgler), r'(src|srcset)="https?://')

    def test_ilk_ekran_oncelikleri(self):
        for n in range(56):
            self._haber(882000 + n, gorsel_var=True,
                        gorsel_dosya="gorseller/2026-08/a_large.jpg")
        anasayfa = self.client.get("/").content.decode()
        # Manşetin ilk slaytı: tek fetchpriority=high.
        self.assertEqual(anasayfa.count('fetchpriority="high"'), 1)
        dortlu = anasayfa.split('class="dortlu"', 1)[1].split("</section>", 1)[0]
        self.assertEqual(dortlu.count('loading="eager"'), 4)
        # 15 manşet + 5 mini slayt: ilk ikisi hemen, kalan 18'i ertelenir.
        self.assertEqual(anasayfa.count("data-srcset="), 18)
        bolum = self.client.get("/gundem").content.decode()
        self.assertEqual(bolum.count('fetchpriority="high"'), 1)
        izgara = bolum.split("liste-izgara", 1)[1]
        ilk = re.search(r"<img[^>]*>", izgara).group(0)
        self.assertIn('fetchpriority="high"', ilk)
