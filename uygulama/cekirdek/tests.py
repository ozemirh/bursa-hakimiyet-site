"""Teslim katmanı ve üretim ayarları testleri (19 Ekim 2026).

Korunanlar:

1. **Fail-closed.** Ortam söylenmezse üretim; üretimde anahtar, sunucu adı
   şart; DEBUG açılamaz; yerel ad reddedilir. `check --deploy` üretim
   ayarlarıyla ölçülür.
2. **CSS yorum ayıklama** dizeye ve `url()`'ye dokunmadan çalışır; gerçek
   `site.css`te yorum dışındaki her bayt korunur.
3. **Üretim depolaması**: özetli adlar, `.gz`/`.br`, `immutable` önbellek,
   yorumsuz CSS, site haritası klasörünün toplanmaması.
4. **Site haritası adresleri** `/static/sitemap/…` olarak, özetsiz kalır.
5. **HTML sıkıştırma** okur sayfasında var, panelde yok.
6. **CSP**: sayfadaki her satır içi betiğin özeti başlıkta; reklam bayrağı
   kapalıyken dış köken yok; sayfa dışarıya kaynak istemiyor.
7. **`/_durum`**: yetkisize özet, yetkiliye ayrıntı, önbelleksiz; bayat veri
   "uyari", veritabanı yoksa 503.
"""

from __future__ import annotations

import base64
import gzip
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest import mock

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ImproperlyConfigured
from django.core.management import call_command
from django.test import SimpleTestCase, TestCase, override_settings

from . import ortam
from .ara_katman import politika, satir_ici_ozetler
from .depolama import yorum_ayikla

UYGULAMA = Path(settings.BASE_DIR)
AYAR_DOSYASI = UYGULAMA / "cekirdek" / "settings.py"
# Gercek anahtar DEGIL: yalniz uzunluk/cesitlilik kuralini gecen bir test degeri.
GUCLU_ANAHTAR = "yalniz-test-icin-uydurma-anahtar-0123456789-abcdefghijklmnop"
URETIM_ORTAMI = {
    "BH_ORTAM": "uretim",
    "BH_GIZLI_ANAHTAR": GUCLU_ANAHTAR,
    "BH_SUNUCU_ADLARI": "www.bursahakimiyet.com.tr,bursahakimiyet.com.tr",
}


def ayarlari_yukle(degiskenler: dict, argv=("manage.py", "runserver")):
    """`settings.py`yi verilen ortamla, ayrı bir modül olarak yükler."""
    temiz = {k: v for k, v in os.environ.items() if not k.startswith("BH_")}
    temiz.update(degiskenler)
    spec = importlib.util.spec_from_file_location("cekirdek._ayar_deneme",
                                                  AYAR_DOSYASI)
    modul = importlib.util.module_from_spec(spec)
    with mock.patch.dict(os.environ, temiz, clear=True), \
            mock.patch.object(sys, "argv", list(argv)):
        spec.loader.exec_module(modul)
    return modul


def manage(*arguman, degiskenler: dict) -> subprocess.CompletedProcess:
    temiz = {k: v for k, v in os.environ.items() if not k.startswith("BH_")}
    temiz.update(degiskenler)
    temiz["PYTHONIOENCODING"] = "utf-8"
    return subprocess.run([sys.executable, "manage.py", *arguman], cwd=UYGULAMA,
                          env=temiz, capture_output=True, text=True,
                          encoding="utf-8", timeout=120)


# --- 1. fail-closed -------------------------------------------------------

class OrtamSecimi(SimpleTestCase):
    def test_ortam_soylenmezse_uretim(self):
        self.assertEqual(ortam.ortam_adi({}, ["manage.py", "runserver"]), "uretim")
        self.assertEqual(ortam.ortam_adi({}, ["gunicorn"]), "uretim")

    def test_test_komutu_kendiliginden_test(self):
        self.assertEqual(ortam.ortam_adi({}, ["manage.py", "test"]), "test")

    def test_acik_ortam_tahmini_ezer(self):
        self.assertEqual(ortam.ortam_adi({"BH_ORTAM": "uretim"},
                                         ["manage.py", "test"]), "uretim")

    def test_bilinmeyen_ortam_reddedilir(self):
        with self.assertRaises(ImproperlyConfigured):
            ortam.ortam_adi({"BH_ORTAM": "prod"}, [])


class UretimSartlari(SimpleTestCase):
    def test_anahtarsiz_acilmaz(self):
        with self.assertRaisesRegex(ImproperlyConfigured, "BH_GIZLI_ANAHTAR"):
            ortam.gizli_anahtar("uretim", {})

    def test_zayif_ya_da_eski_anahtar_reddedilir(self):
        for kotu in ("kisa", "a" * 80,
                     "django-insecure-" + GUCLU_ANAHTAR):
            with self.subTest(kotu=kotu[:20]), self.assertRaises(ImproperlyConfigured):
                ortam.gizli_anahtar("uretim", {"BH_GIZLI_ANAHTAR": kotu})

    def test_hata_ayiklama_acilamaz(self):
        with self.assertRaises(ImproperlyConfigured):
            ortam.hata_ayiklama("uretim", {"BH_HATA_AYIKLA": "1"})
        self.assertFalse(ortam.hata_ayiklama("uretim", {}))

    def test_sunucu_adi_zorunlu_ve_yerel_ad_yasak(self):
        with self.assertRaises(ImproperlyConfigured):
            ortam.sunucu_adlari("uretim", {})
        for kotu in ("localhost", "127.0.0.1", "*", "www.ornek.tr,[::1]"):
            with self.subTest(kotu=kotu), self.assertRaises(ImproperlyConfigured):
                ortam.sunucu_adlari("uretim", {"BH_SUNUCU_ADLARI": kotu})

    def test_csrf_kokenleri_sunucu_adlarindan(self):
        self.assertEqual(
            ortam.guvenilir_kokenler(["www.ornek.tr", ".ornek.tr"], {}),
            ["https://www.ornek.tr", "https://*.ornek.tr"])
        self.assertEqual(
            ortam.guvenilir_kokenler(["x"], {"BH_GUVENILIR_KOKENLER": "https://a.b"}),
            ["https://a.b"])


class GelistirmeAnahtari(SimpleTestCase):
    def test_yerel_anahtar_bir_kez_uretilir(self):
        with tempfile.TemporaryDirectory() as klasor:
            yol = Path(klasor) / ".yerel-gizli-anahtar"
            ilk = ortam.gizli_anahtar("gelistirme", {}, yol)
            ikinci = ortam.gizli_anahtar("gelistirme", {}, yol)
        self.assertEqual(ilk, ikinci)
        self.assertGreaterEqual(len(ilk), 50)
        self.assertFalse(ilk.startswith("django-insecure"))

    def test_gelistirmede_debug_varsayilan_acik(self):
        self.assertTrue(ortam.hata_ayiklama("gelistirme", {}))
        self.assertFalse(ortam.hata_ayiklama("gelistirme", {"BH_HATA_AYIKLA": "0"}))


class AyarDosyasi(SimpleTestCase):
    """`settings.py`nin kendisi, farklı ortamlarla yeniden yüklenerek."""

    def test_depoda_sabit_anahtar_yok(self):
        metin = AYAR_DOSYASI.read_text(encoding="utf-8")
        self.assertNotRegex(metin, r"[\"']django-insecure-")
        self.assertNotIn("9v%)%ub9qz", metin)

    def test_ortamsiz_yukleme_acilmaz(self):
        with self.assertRaisesRegex(ImproperlyConfigured, "BH_GIZLI_ANAHTAR"):
            ayarlari_yukle({})

    def test_uretim_ayarlari_sert(self):
        a = ayarlari_yukle(URETIM_ORTAMI)
        self.assertFalse(a.DEBUG)
        self.assertEqual(a.SECRET_KEY, GUCLU_ANAHTAR)
        self.assertTrue(a.SECURE_SSL_REDIRECT)
        self.assertTrue(a.SESSION_COOKIE_SECURE)
        self.assertTrue(a.CSRF_COOKIE_SECURE)
        self.assertGreater(a.SECURE_HSTS_SECONDS, 0)
        self.assertEqual(a.SECURE_PROXY_SSL_HEADER, ("HTTP_X_FORWARDED_PROTO", "https"))
        self.assertIn("https://www.bursahakimiyet.com.tr", a.CSRF_TRUSTED_ORIGINS)
        self.assertEqual(a.STORAGES["staticfiles"]["BACKEND"],
                         "cekirdek.depolama.TeslimDepolamasi")
        self.assertTrue(a.SITE_HARITASI_DOSYADAN)
        self.assertEqual(a.SECURE_REFERRER_POLICY, "strict-origin-when-cross-origin")

    def test_gelistirme_ayarlari(self):
        # Anahtar verilir ki test, depodaki yerel anahtar dosyasına yazmasın.
        a = ayarlari_yukle({"BH_ORTAM": "gelistirme", "BH_GIZLI_ANAHTAR": GUCLU_ANAHTAR})
        self.assertTrue(a.DEBUG)
        self.assertIn("127.0.0.1", a.ALLOWED_HOSTS)
        self.assertFalse(getattr(a, "SECURE_SSL_REDIRECT", False))
        self.assertEqual(a.STORAGES["staticfiles"]["BACKEND"],
                         "django.contrib.staticfiles.storage.StaticFilesStorage")

    def test_check_deploy_uretimde_temiz(self):
        """Ölçüt: üretim ayarlarıyla `check --deploy` 0 uyarı.

        HSTS alt alan ve ön yükleme varsayılan KAPALI (geri alınması zor,
        kullanıcı kararı); kapalıyken yalnız o iki uyarı kalır.
        """
        tam = manage("check", "--deploy", "--fail-level", "WARNING", degiskenler={
            **URETIM_ORTAMI, "BH_HSTS_ALT_ALANLAR": "1", "BH_HSTS_ON_YUKLEME": "1"})
        self.assertEqual(tam.returncode, 0, tam.stdout + tam.stderr)
        self.assertIn("no issues", tam.stdout + tam.stderr)

        varsayilan = manage("check", "--deploy", degiskenler=URETIM_ORTAMI)
        cikti = varsayilan.stdout + varsayilan.stderr
        self.assertEqual(sorted(set(re.findall(r"security\.W\d+", cikti))),
                         ["security.W005", "security.W021"], cikti)

    def test_ortamsiz_manage_acilmaz(self):
        sonuc = manage("check", degiskenler={})
        self.assertNotEqual(sonuc.returncode, 0)
        self.assertIn("BH_GIZLI_ANAHTAR", sonuc.stderr)


# --- 2. CSS yorum ayıklama -------------------------------------------------

class YorumAyiklama(SimpleTestCase):
    def test_yorum_gider(self):
        self.assertEqual(yorum_ayikla("a{b:c}/* not */\nd{e:f}"), "a{b:c}\nd{e:f}\n")

    def test_dize_icindeki_yorum_isareti_korunur(self):
        css = 'a::before{content:"/* yorum değil */"}\nb{content:\'*/\'}'
        self.assertEqual(yorum_ayikla(css), css + "\n")

    def test_tirnaksiz_url_korunur(self):
        css = "a{background:url(data:image/svg+xml;utf8,<svg>/*x*/</svg>)}"
        self.assertEqual(yorum_ayikla(css), css + "\n")

    def test_belirtecler_kaynasmaz(self):
        self.assertEqual(yorum_ayikla("a{margin:0/**/auto}"), "a{margin:0 auto}\n")
        self.assertEqual(yorum_ayikla("a{b:c;/* x */}"), "a{b:c;}\n")

    def test_lisans_yorumu_korunur(self):
        self.assertIn("/*! OFL */", yorum_ayikla("/*! OFL */\na{b:c}"))

    def test_kapanmamis_yorum_dosyayi_bozmaz(self):
        self.assertEqual(yorum_ayikla("a{b:c}\n/* yarim"), "a{b:c}\n")

    def test_gercek_dosyalarda_yorum_disinda_her_sey_korunur(self):
        """Yorum dışı içerik (boşluk hariç) birebir aynı kalmalı.

        Karşılaştırma ölçütü basit bir düzenli ifade: bu dosyalarda dize
        içinde `/*` geçmiyor, o yüzden basit yol da doğru sonucu verir ve
        ayıklayıcının bağımsız sağlaması olur.
        """
        for ad in ("site.css", "panel.css", "fontlar.css"):
            with self.subTest(ad=ad):
                ham = (UYGULAMA / "statik" / "stil" / ad).read_text(encoding="utf-8")
                basit = re.sub(r"/\*.*?\*/", "", ham, flags=re.S)
                temiz = yorum_ayikla(ham)
                self.assertNotIn("/*", temiz)
                self.assertEqual(re.sub(r"\s+", "", temiz), re.sub(r"\s+", "", basit))

    def test_site_css_gzip_boyutu(self):
        """Ölçüm: 58,6 KB → ~20 KB (gzip -9). Eşik gevşek: 26 KB."""
        ham = (UYGULAMA / "statik" / "stil" / "site.css").read_bytes()
        temiz = yorum_ayikla(ham.decode("utf-8")).encode("utf-8")
        self.assertLess(len(gzip.compress(temiz, 9)), 26 * 1024)
        self.assertLess(len(temiz), len(ham) * 0.7)


# --- 3. üretim depolaması --------------------------------------------------

class UretimDepolamasi(TestCase):
    """`collectstatic` geçici klasöre, üretim depolamasıyla, gerçek dosyalarla."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.klasor = tempfile.mkdtemp(prefix="bh-statik-")
        cls.ayar = override_settings(
            STATIC_ROOT=cls.klasor, DEBUG=False,
            STORAGES={**settings.STORAGES, "staticfiles": {
                "BACKEND": "cekirdek.depolama.TeslimDepolamasi"}})
        cls.ayar.enable()
        call_command("collectstatic", interactive=False, verbosity=0)

    @classmethod
    def tearDownClass(cls):
        cls.ayar.disable()
        shutil.rmtree(cls.klasor, ignore_errors=True)
        super().tearDownClass()

    def _manifest(self):
        with open(Path(self.klasor) / "staticfiles.json", encoding="utf-8") as f:
            return json.load(f)["paths"]

    def test_ozetli_adlar_ve_sikistirilmis_kopyalar(self):
        yollar = self._manifest()
        ozetli = yollar["stil/site.css"]
        self.assertRegex(ozetli, r"^stil/site\.[0-9a-f]{12}\.css$")
        for uzanti in ("", ".gz", ".br"):
            self.assertTrue((Path(self.klasor) / (ozetli + uzanti)).is_file(), uzanti)

    def test_toplanan_css_yorumsuz(self):
        ozetli = Path(self.klasor) / self._manifest()["stil/site.css"]
        metin = ozetli.read_text(encoding="utf-8")
        self.assertNotIn("/*", metin)
        self.assertIn("--kirmizi", metin)
        gz = (Path(str(ozetli) + ".gz")).stat().st_size
        self.assertLess(gz, 26 * 1024)

    def test_font_adresleri_ozetli(self):
        metin = (Path(self.klasor) / self._manifest()["stil/fontlar.css"]).read_text(
            encoding="utf-8")
        adresler = re.findall(r'url\("([^"]+)"\)', metin)
        self.assertGreaterEqual(len(adresler), 16)
        for adres in adresler:
            self.assertRegex(adres, r"\.[0-9a-f]{12}\.woff2$")

    def test_site_haritasi_toplanmaz(self):
        self.assertFalse((Path(self.klasor) / "sitemap").exists())
        self.assertFalse([y for y in self._manifest() if y.startswith("sitemap/")])

    def test_ozetli_dosya_uzun_onbellek_ve_br(self):
        ozetli = self._manifest()["stil/site.css"]
        yanit = self.client.get("/statik/" + ozetli, HTTP_ACCEPT_ENCODING="gzip, br")
        self.assertEqual(yanit.status_code, 200)
        self.assertEqual(yanit["Content-Encoding"], "br")
        self.assertIn("immutable", yanit["Cache-Control"])
        self.assertIn("max-age=315360000", yanit["Cache-Control"])
        yanit.close()

    def test_static_etiketi_ozetli_ad_verir(self):
        from django.templatetags.static import static
        self.assertRegex(static("stil/site.css"), r"^/statik/stil/site\.[0-9a-f]{12}\.css$")
        self.assertRegex(static("fontlar/roboto-latin.woff2"),
                         r"^/statik/fontlar/roboto-latin\.[0-9a-f]{12}\.woff2$")


# --- 4. site haritası adresleri --------------------------------------------

class SiteHaritasiAdresleri(TestCase):
    ICERIK = ('<?xml version="1.0" encoding="UTF-8"?>\n'
              '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
              '<!-- dosyadan -->' + "<url><loc>https://ornek.test/a-1</loc></url>" * 20
              + "</urlset>\n")

    def setUp(self):
        self.klasor = tempfile.mkdtemp(prefix="bh-sitemap-")
        # write_bytes: Windows'ta write_text satır sonunu CRLF'e çevirir.
        (Path(self.klasor) / "news_2026-08.xml").write_bytes(self.ICERIK.encode("utf-8"))

    def tearDown(self):
        shutil.rmtree(self.klasor, ignore_errors=True)

    def test_adres_sozlesmesi(self):
        from besleme import siteharitasi
        self.assertEqual(siteharitasi.DIZIN_YOLU, "/static/sitemap")
        self.assertEqual(siteharitasi.dosya_adresi("https://k", "news_2026-08.xml"),
                         "https://k/static/sitemap/news_2026-08.xml")

    def test_uretimde_dosyadan_ozetsiz(self):
        with override_settings(SITE_HARITASI_DOSYADAN=True,
                               BESLEME_CIKTI_KOKU=self.klasor):
            yanit = self.client.get("/static/sitemap/news_2026-08.xml")
            govde = b"".join(yanit.streaming_content).decode("utf-8")
        self.assertEqual(yanit.status_code, 200)
        self.assertEqual(govde, self.ICERIK)
        self.assertEqual(yanit["Content-Type"], "application/xml; charset=utf-8")
        self.assertIn("max-age=300", yanit["Cache-Control"])

    def test_dosyadan_verilen_harita_sikisir(self):
        with override_settings(SITE_HARITASI_DOSYADAN=True,
                               BESLEME_CIKTI_KOKU=self.klasor):
            yanit = self.client.get("/static/sitemap/news_2026-08.xml",
                                    HTTP_ACCEPT_ENCODING="gzip")
            govde = gzip.decompress(b"".join(yanit.streaming_content)).decode("utf-8")
        self.assertEqual(yanit["Content-Encoding"], "gzip")
        self.assertEqual(govde, self.ICERIK)

    def test_dosya_yoksa_gorunume_duser(self):
        with override_settings(SITE_HARITASI_DOSYADAN=True,
                               BESLEME_CIKTI_KOKU=self.klasor):
            yanit = self.client.get("/static/sitemap/sitemap.xml")
            govde = b"".join(yanit.streaming_content).decode("utf-8")
        self.assertEqual(yanit.status_code, 200)
        self.assertIn("<sitemapindex", govde)

    def test_kapaliyken_gorunum_uretir(self):
        with override_settings(SITE_HARITASI_DOSYADAN=False,
                               BESLEME_CIKTI_KOKU=self.klasor):
            yanit = self.client.get("/static/sitemap/news_2026-08.xml")
            govde = b"".join(yanit.streaming_content).decode("utf-8")
        self.assertNotIn("dosyadan", govde)

    def test_klasor_disina_cikilmaz(self):
        with override_settings(SITE_HARITASI_DOSYADAN=True,
                               BESLEME_CIKTI_KOKU=self.klasor):
            for yol in ("/static/sitemap/../settings.py",
                        "/static/sitemap/%2e%2e/x.xml",
                        "/static/sitemap/alt/news_2026-08.xml"):
                with self.subTest(yol=yol):
                    self.assertNotEqual(self.client.get(yol).status_code, 200)


# --- 5-6. sayfa: sıkıştırma, CSP, dış kaynak ---------------------------------

_DIS_KAYNAK = re.compile(
    r"""<(?:script|img|iframe|source|link)\b[^>]*\b(?:src|href|srcset)=["']https?://""",
    re.I)


class SayfaTeslimi(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("taksonomi_kur", verbosity=0)
        cls.personel = User.objects.create_user("teslim", password="x", is_staff=True)

    def test_anasayfa_gzip(self):
        yanit = self.client.get("/", HTTP_ACCEPT_ENCODING="gzip, br")
        self.assertEqual(yanit.status_code, 200)
        self.assertEqual(yanit["Content-Encoding"], "gzip")
        self.assertIn("Accept-Encoding", yanit["Vary"])
        html = gzip.decompress(yanit.content).decode("utf-8")
        self.assertIn("</html>", html)

    def test_panel_sikistirilmaz(self):
        yanit = self.client.get("/panel/giris", HTTP_ACCEPT_ENCODING="gzip")
        self.assertEqual(yanit.status_code, 200)
        self.assertFalse(yanit.has_header("Content-Encoding"))

    def test_csp_varsayilan_sert(self):
        yanit = self.client.get("/")
        csp = yanit["Content-Security-Policy"]
        for parca in ("default-src 'self'", "font-src 'self'", "object-src 'none'",
                      "frame-ancestors 'none'", "base-uri 'self'"):
            self.assertIn(parca, csp)
        # Betikte 'unsafe-inline' yok (yalnız stilde, bilerek).
        self.assertNotRegex(csp.split("style-src")[0], "unsafe-inline")
        self.assertNotIn("google", csp)
        self.assertNotIn("fonts.g", csp)

    def test_sayfa_disaridan_kaynak_istemez(self):
        """Ölçüt: dış istek 0 (Google Fonts kalktı). Bağlantılar sayılmaz."""
        for yol in ("/", "/panel/giris"):
            with self.subTest(yol=yol):
                html = self.client.get(yol).content.decode("utf-8")
                self.assertEqual(_DIS_KAYNAK.findall(html), [])
                self.assertNotIn("fonts.googleapis", html)
                self.assertNotIn("fonts.gstatic", html)

    def test_font_preload_crossorigin(self):
        html = self.client.get("/").content.decode("utf-8")
        onyukleme = [e for e in re.findall(r"<link rel=\"preload\"[^>]*>", html)
                     if 'as="font"' in e]
        self.assertEqual(len(onyukleme), 2)
        for etiket in onyukleme:
            self.assertIn("crossorigin", etiket)
            self.assertIn('type="font/woff2"', etiket)

    def test_her_satir_ici_betigin_ozeti_baslikta(self):
        """Sunum oturumu + reklam bayrakları: dört satır içi betik de basılır."""
        self.client.force_login(self.personel)
        with override_settings(REKLAM_DEMO=True, REKLAM_TEST=True):
            satir_ici_ozetler.cache_clear()
            yanit = self.client.get("/")
            csp = yanit["Content-Security-Policy"]
        html = yanit.content.decode("utf-8")
        betikler = [m.group(2) for m in re.finditer(
            r"<script(\s[^>]*)?>(.*?)</script>", html, re.S)
            if not re.search(r"src=|application/(ld\+)?json", m.group(1) or "")]
        self.assertGreaterEqual(len(betikler), 4)
        for govde in betikler:
            ozet = base64.b64encode(hashlib.sha256(govde.encode()).digest()).decode()
            self.assertIn(f"'sha256-{ozet}'", csp, govde[:60])
        self.assertIn("https://*.doubleclick.net", csp)

    def test_rapor_kipi(self):
        with override_settings(CSP_KIP="rapor"):
            yanit = self.client.get("/")
        self.assertTrue(yanit.has_header("Content-Security-Policy-Report-Only"))
        self.assertFalse(yanit.has_header("Content-Security-Policy"))

    def test_uretimde_upgrade(self):
        with override_settings(URETIM=True, SECURE_SSL_REDIRECT=True):
            self.assertIn("upgrade-insecure-requests", politika())
        with override_settings(URETIM=True, SECURE_SSL_REDIRECT=False):
            self.assertNotIn("upgrade-insecure-requests", politika())


# --- 7. sağlık ucu ----------------------------------------------------------

class SaglikUcu(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.personel = User.objects.create_user("nobetci", password="x", is_staff=True)

    def setUp(self):
        self.kok = Path(tempfile.mkdtemp(prefix="bh-canli-"))

    def tearDown(self):
        shutil.rmtree(self.kok, ignore_errors=True)

    def _bilesen(self, ad, dakika_once, esik):
        an = (datetime.now().astimezone() - timedelta(minutes=dakika_once)).isoformat(
            timespec="seconds")
        (self.kok / f"{ad}.json").write_text(json.dumps(
            {"guncelleme": an, "bayat_esik_dakika": esik}), encoding="utf-8")
        (self.kok / f"durum-{ad}.json").write_text(json.dumps(
            {"bilesen": ad, "durum": "taze", "denendi": an}), encoding="utf-8")

    def _al(self, **ek):
        with override_settings(CANLI_VERI_KOK=self.kok):
            return self.client.get("/_durum", **ek)

    def test_yetkisize_ozet(self):
        self._bilesen("doviz", 10, 1440)
        yanit = self._al()
        self.assertEqual(yanit.status_code, 200)
        self.assertEqual(set(yanit.json()), {"genel", "zaman"})
        self.assertIn("no-store", yanit["Cache-Control"])

    def test_yetkiliye_ayrinti_ve_taze(self):
        self._bilesen("doviz", 10, 1440)
        self.client.force_login(self.personel)
        veri = self._al().json()
        self.assertEqual(veri["veritabani"]["durum"], "tamam")
        self.assertEqual(veri["canli_veri"]["durum"], "taze")
        self.assertIn("commit", veri["surum"])
        self.assertIn("uygulama", veri["disk"]["bolumler"])

    def test_bayat_veri_uyari(self):
        """Zamanlayıcı kapalıyken bugünkü durum: veri günlerce eski."""
        self._bilesen("doviz", 10, 1440)
        self._bilesen("hava-durumu", 60 * 24 * 37, 180)
        self.client.force_login(self.personel)
        yanit = self._al()
        veri = yanit.json()
        self.assertEqual(yanit.status_code, 200)
        self.assertEqual(veri["genel"], "uyari")
        self.assertEqual(veri["canli_veri"]["bayat"], ["hava-durumu"])

    def test_anahtarla_ayrinti(self):
        self._bilesen("doviz", 10, 1440)
        with mock.patch.dict(os.environ, {"BH_DURUM_ANAHTARI": "gizli-deger"}):
            dogru = self._al(HTTP_X_DURUM_ANAHTARI="gizli-deger").json()
            yanlis = self._al(HTTP_X_DURUM_ANAHTARI="baska").json()
        self.assertIn("veritabani", dogru)
        self.assertNotIn("veritabani", yanlis)

    def test_veritabani_yoksa_503(self):
        self._bilesen("doviz", 10, 1440)
        with mock.patch("cekirdek.durum._veritabani",
                        return_value={"durum": "bozuk", "hata": "OperationalError"}):
            yanit = self._al()
        self.assertEqual(yanit.status_code, 503)
        self.assertEqual(yanit.json()["genel"], "bozuk")
