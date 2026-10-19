"""Dış istek kapısı — `icerik/dis_istek.py` (Paket F madde 3–4).

Testler dışarıya ÇIKMAZ. İki yol kullanılır:

- gerçek bir yerel sunucu (127.0.0.1) — kapının ona HİÇ bağlanmadığı,
  sunucunun istek sayacıyla ölçülür;
- `_coz` (DNS) ve `_baglanti` (soket) yamaları — "dışarıdaki" bir sunucu
  taklit edilir ve yönlendirme ile iç ağa kaçış denenir.
"""

import gzip
import http.server
import tempfile
import threading
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth.models import Group, User
from django.core.management import call_command
from django.test import SimpleTestCase, TestCase, override_settings

from taksonomi.models import Kategori

from . import dis_istek, yz_kopru
from .models import Haber

GENEL_IP = "93.184.216.34"
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 64
SVG = b'<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>'


class _SahteYanit:
    def __init__(self, durum=200, basliklar=None, govde=b""):
        self.status = durum
        self._b = {k.lower(): v for k, v in (basliklar or {}).items()}
        self._govde = govde
        self._konum = 0

    def getheader(self, ad, varsayilan=None):
        return self._b.get(ad.lower(), varsayilan)

    def getheaders(self):
        return list(self._b.items())

    def read(self, n=-1):
        if n is None or n < 0:
            n = len(self._govde)
        parca = self._govde[self._konum:self._konum + n]
        self._konum += len(parca)
        return parca


class _SahteBaglanti:
    def __init__(self, yanit):
        self.yanit = yanit
        self.istekler = []

    def request(self, yontem, yol, headers=None):
        self.istekler.append((yontem, yol, headers))

    def getresponse(self):
        return self.yanit

    def close(self):
        pass


class _Ag:
    """`_coz` ve `_baglanti`yı yamalayan küçük sahte internet.

    `adlar`: ad → IP listesi; `yanitlar`: (ad, yol) → _SahteYanit.
    Bağlanılan her (ad, ip) `baglantilar`a yazılır.
    """

    def __init__(self, adlar, yanitlar):
        self.adlar, self.yanitlar, self.baglantilar = adlar, yanitlar, []

    def coz(self, ad, port):
        try:                       # IP yazılmış adres DNS'e gitmez, kendisidir
            import ipaddress
            return [str(ipaddress.ip_address(ad))]
        except ValueError:
            pass
        if ad not in self.adlar:
            raise OSError("bilinmeyen ad")
        return self.adlar[ad]

    def baglanti(self, sema, ad, port, ip, zaman_asimi):
        self.baglantilar.append((ad, ip))
        ag = self

        class B(_SahteBaglanti):
            def getresponse(self_):
                yol = self_.istekler[-1][1]
                return ag.yanitlar[(ad, yol)]
        return B(None)

    def __enter__(self):
        self._y1 = patch.object(dis_istek, "_coz", self.coz)
        self._y2 = patch.object(dis_istek, "_baglanti", self.baglanti)
        self._y1.start()
        self._y2.start()
        return self

    def __exit__(self, *a):
        self._y1.stop()
        self._y2.stop()


class IpDenetimi(SimpleTestCase):

    def test_ozel_yerel_ve_ozel_amacli_adresler_reddedilir(self):
        for ip in ("127.0.0.1", "127.8.9.10", "10.0.0.1", "172.16.5.4",
                   "172.31.255.255", "192.168.1.1", "169.254.169.254",
                   "100.64.0.1", "0.0.0.0", "224.0.0.1", "255.255.255.255",
                   "::1", "::", "fc00::1", "fd12:3456::1", "fe80::1", "ff02::1",
                   "::ffff:127.0.0.1", "::ffff:10.0.0.1", "64:ff9b::a00:1",
                   "2002:7f00:1::1"):
            with self.subTest(ip=ip):
                self.assertFalse(dis_istek.ip_izinli_mi(ip))

    def test_genel_adresler_gecer(self):
        for ip in (GENEL_IP, "8.8.8.8", "2606:4700:4700::1111"):
            with self.subTest(ip=ip):
                self.assertTrue(dis_istek.ip_izinli_mi(ip))


class AdresDenetimi(SimpleTestCase):

    def test_sema_kimlik_bilgisi_ve_port(self):
        for adres in ("file:///etc/passwd", "ftp://ornek.com/a", "gopher://x/",
                      "javascript:alert(1)", "http://kim:parola@ornek.com/",
                      "http://ornek.com:22/", "http://ornek.com:6379/", "http:///yol"):
            with self.subTest(adres=adres):
                with self.assertRaises(dis_istek.DisIstekHatasi):
                    dis_istek.adres_denetle(adres)

    def test_dns_cozumu_ic_aga_donerse_reddedilir(self):
        """Ad zararsız görünür, çözümü iç ağdır — denetim çözümden SONRA."""
        with _Ag({"masum.ornek.test": ["10.1.2.3"]}, {}) as ag:
            with self.assertRaises(dis_istek.DisIstekHatasi) as h:
                dis_istek.getir("https://masum.ornek.test/haber")
        self.assertEqual(ag.baglantilar, [])
        self.assertNotIn("10.1.2.3", str(h.exception))

    def test_cozumdeki_tek_ozel_adres_yeter(self):
        """Birden çok A kaydında biri bile içeriyse istek yapılmaz."""
        with _Ag({"karma.ornek.test": [GENEL_IP, "127.0.0.1"]}, {}) as ag:
            with self.assertRaises(dis_istek.DisIstekHatasi):
                dis_istek.getir("http://karma.ornek.test/")
        self.assertEqual(ag.baglantilar, [])

    def test_baglanti_denetlenen_ipye_kurulur(self):
        """DNS rebinding: bağlantı denetimden geçen IP'ye gider."""
        yanit = _SahteYanit(200, {"Content-Type": "text/html; charset=utf-8"},
                            "<p>merhaba</p>".encode())
        with _Ag({"ornek.test": [GENEL_IP]}, {("ornek.test", "/a?b=1"): yanit}) as ag:
            self.assertEqual(dis_istek.html_getir("http://ornek.test/a?b=1"),
                             "<p>merhaba</p>")
        self.assertEqual(ag.baglantilar, [("ornek.test", GENEL_IP)])


class YerelSunucu(SimpleTestCase):
    """Gerçek bir 127.0.0.1 sunucusu: kapı ona HİÇ bağlanmamalı."""

    def setUp(self):
        sayac = self.sayac = []

        class Islem(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                sayac.append(self.path)
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(b"<p>gizli</p>")

            def log_message(self, *a):
                pass

        self.sunucu = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Islem)
        self.port = self.sunucu.server_address[1]
        threading.Thread(target=self.sunucu.serve_forever, daemon=True).start()

    def tearDown(self):
        self.sunucu.shutdown()
        self.sunucu.server_close()

    def test_yerel_makineye_istek_yapilmaz(self):
        # Port izin listesinde olmadığı için de düşerdi; ikisini ayırmak
        # için izinli portlar genişletilerek denenir.
        with patch.object(dis_istek, "IZINLI_PORTLAR", frozenset({self.port})):
            for adres in (f"http://127.0.0.1:{self.port}/",
                          f"http://localhost:{self.port}/",
                          f"http://[::ffff:127.0.0.1]:{self.port}/",
                          f"http://2130706433:{self.port}/"):
                with self.subTest(adres=adres):
                    with self.assertRaises(dis_istek.DisIstekHatasi):
                        dis_istek.getir(adres)
        self.assertEqual(self.sayac, [])

    def test_ayiklayici_getir_de_kapidan_gecer(self):
        """`arac/ayiklayici.getir` (yerel editör aracı) aynı kapıyı kullanır."""
        ayiklayici, _ = yz_kopru._arac()
        kapi = ayiklayici.guvenli_kapi()
        with patch.object(kapi, "IZINLI_PORTLAR", frozenset({self.port})):
            with self.assertRaises(kapi.DisIstekHatasi):
                ayiklayici.getir(f"http://127.0.0.1:{self.port}/")
        self.assertEqual(self.sayac, [])


class Yonlendirme(SimpleTestCase):

    def test_ic_aga_yonlendirme_reddedilir(self):
        """Dışarıdaki sayfa 302 ile bulut üst veri adresine yönlendirir."""
        yanitlar = {("dis.ornek.test", "/haber"): _SahteYanit(
            302, {"Location": "http://169.254.169.254/latest/meta-data/"})}
        with _Ag({"dis.ornek.test": [GENEL_IP]}, yanitlar) as ag:
            with self.assertRaises(dis_istek.DisIstekHatasi) as h:
                dis_istek.getir("https://dis.ornek.test/haber")
        self.assertEqual(ag.baglantilar, [("dis.ornek.test", GENEL_IP)])
        self.assertNotIn("169.254", str(h.exception))

    def test_ada_yonlendirme_ve_rebinding(self):
        """Yönlendirilen ad iç ağa çözülüyorsa yine reddedilir."""
        yanitlar = {("dis.ornek.test", "/"): _SahteYanit(
            301, {"Location": "http://ic.ornek.test/yonetim"})}
        with _Ag({"dis.ornek.test": [GENEL_IP], "ic.ornek.test": ["192.168.0.10"]},
                 yanitlar) as ag:
            with self.assertRaises(dis_istek.DisIstekHatasi):
                dis_istek.getir("http://dis.ornek.test/")
        self.assertEqual(len(ag.baglantilar), 1)

    def test_yonlendirme_siniri(self):
        yanitlar = {("dis.ornek.test", f"/{i}"): _SahteYanit(
            302, {"Location": f"/{i + 1}"}) for i in range(10)}
        with _Ag({"dis.ornek.test": [GENEL_IP]}, yanitlar) as ag:
            with self.assertRaises(dis_istek.DisIstekHatasi):
                dis_istek.getir("http://dis.ornek.test/0")
        self.assertEqual(len(ag.baglantilar), dis_istek.EN_COK_YONLENDIRME + 1)

    def test_genel_yonlendirme_izlenir(self):
        yanitlar = {
            ("dis.ornek.test", "/eski"): _SahteYanit(301, {"Location": "/yeni"}),
            ("dis.ornek.test", "/yeni"): _SahteYanit(
                200, {"Content-Type": "text/html"}, b"<p>tamam</p>"),
        }
        with _Ag({"dis.ornek.test": [GENEL_IP]}, yanitlar):
            yanit = dis_istek.getir("http://dis.ornek.test/eski")
        self.assertEqual(yanit.adres, "http://dis.ornek.test/yeni")


class BoyutSiniri(SimpleTestCase):

    def _al(self, yanit, sinir=1000):
        with _Ag({"dis.ornek.test": [GENEL_IP]}, {("dis.ornek.test", "/"): yanit}):
            return dis_istek.getir("http://dis.ornek.test/", en_cok_bayt=sinir)

    def test_bildirilen_uzunluk_asarsa_okunmaz(self):
        with self.assertRaises(dis_istek.DisIstekHatasi):
            self._al(_SahteYanit(200, {"Content-Length": "5000"}, b"x" * 10))

    def test_bildirilmeyen_uzunlukta_okurken_kesilir(self):
        with self.assertRaises(dis_istek.DisIstekHatasi):
            self._al(_SahteYanit(200, {}, b"x" * 5000))

    def test_sikistirma_bombasi(self):
        bomba = gzip.compress(b"\x00" * 2_000_000)
        self.assertLess(len(bomba), 1000 * 3)
        with self.assertRaises(dis_istek.DisIstekHatasi):
            self._al(_SahteYanit(200, {"Content-Encoding": "gzip"}, bomba),
                     sinir=100_000)

    def test_gzip_acilir(self):
        yanit = self._al(_SahteYanit(200, {"Content-Encoding": "gzip"},
                                     gzip.compress(b"<p>a</p>")))
        self.assertEqual(yanit.govde, b"<p>a</p>")


class GorselTuru(SimpleTestCase):

    def _gorsel(self, tur, govde):
        yanit = _SahteYanit(200, {"Content-Type": tur}, govde)
        with _Ag({"foto.ornek.test": [GENEL_IP]}, {("foto.ornek.test", "/1.jpg"): yanit}):
            return dis_istek.gorsel_getir("https://foto.ornek.test/1.jpg")

    def test_svg_reddedilir(self):
        with self.assertRaises(dis_istek.DisIstekHatasi):
            self._gorsel("image/svg+xml", SVG)

    def test_html_reddedilir(self):
        with self.assertRaises(dis_istek.DisIstekHatasi):
            self._gorsel("text/html", b"<html><script>alert(1)</script>")

    def test_png_diye_beyan_edilen_html_reddedilir(self):
        with self.assertRaises(dis_istek.DisIstekHatasi):
            self._gorsel("image/png", b"<html><script>alert(1)</script>")

    def test_tur_ve_bayt_uyusmazsa_reddedilir(self):
        with self.assertRaises(dis_istek.DisIstekHatasi):
            self._gorsel("image/jpeg", PNG)

    def test_uzanti_turden_turetilir(self):
        """Adres `.jpg` der, dosya PNG'dir ve öyle beyan edilmiştir → `.png`."""
        veri, tur, uzanti = self._gorsel("image/png", PNG)
        self.assertEqual((tur, uzanti), ("image/png", ".png"))
        _, _, uzanti = self._gorsel("image/jpg", JPEG)
        self.assertEqual(uzanti, ".jpg")


class PanelYollari(TestCase):
    """Kapı panelin iki yolunda da işliyor: adresten taslak ve görsel indirme."""

    @classmethod
    def setUpTestData(cls):
        call_command("taksonomi_kur", verbosity=0)
        call_command("roller_kur", verbosity=0)
        cls.editor = User.objects.create_user("editor-d", password="x")
        cls.editor.groups.add(Group.objects.get(name="Editör"))

    def test_adresten_taslak_ic_aga_gitmez(self):
        with _Ag({"masum.ornek.test": ["169.254.169.254"]}, {}) as ag:
            with self.assertRaises(yz_kopru.YzHatasi) as h:
                yz_kopru.paket_uret("http://masum.ornek.test/haber", "kural")
        self.assertEqual(ag.baglantilar, [])
        self.assertNotIn("169.254", str(h.exception))

    def test_panel_ekrani_ic_ag_hatasini_ayrintisiz_gosterir(self):
        self.client.force_login(self.editor)
        with _Ag({"masum.ornek.test": ["10.0.0.5"]}, {}):
            yanit = self.client.post("/panel/yz-taslak", {
                "adres": "http://masum.ornek.test/x", "saglayici": "kural"})
        self.assertEqual(yanit.status_code, 200)
        self.assertContains(yanit, "iç ağdaki adreslere istek yapılmaz")
        self.assertNotContains(yanit, "10.0.0.5")
        self.assertFalse(Haber.objects.exists())

    def _haber(self, url):
        return Haber.objects.create(
            id=5_300_001, slug="g", baslik="Görsel", gorsel_url=url,
            kategori=Kategori.objects.filter(aktif=True).first(),
            durum=Haber.DURUM_PASIF)

    def test_gorsel_indirme_yalniz_raster_yazar(self):
        with tempfile.TemporaryDirectory() as kok:
            with override_settings(ARSIV_GORSEL_KOK=Path(kok)):
                haber = self._haber("https://foto.ornek.test/kotu.svg")
                yanitlar = {("foto.ornek.test", "/kotu.svg"): _SahteYanit(
                    200, {"Content-Type": "image/svg+xml"}, SVG)}
                with _Ag({"foto.ornek.test": [GENEL_IP]}, yanitlar):
                    oldu, mesaj = yz_kopru.gorsel_indir(haber)
                self.assertFalse(oldu)
                self.assertEqual(list(Path(kok).rglob("*")), [])

                haber.gorsel_url = "https://foto.ornek.test/sahte.html"
                yanitlar = {("foto.ornek.test", "/sahte.html"): _SahteYanit(
                    200, {"Content-Type": "image/png"}, PNG)}
                with _Ag({"foto.ornek.test": [GENEL_IP]}, yanitlar):
                    oldu, mesaj = yz_kopru.gorsel_indir(haber)
                self.assertTrue(oldu, mesaj)
                dosyalar = [p.name for p in Path(kok).rglob("*") if p.is_file()]
                self.assertEqual(dosyalar, ["yz-5300001.png"])
                haber.refresh_from_db()
                self.assertTrue(haber.gorsel_dosya.endswith(".png"))

    def test_gorsel_indirme_ic_aga_gitmez(self):
        haber = self._haber("http://169.254.169.254/latest/meta-data/iam")
        with _Ag({}, {}) as ag:
            oldu, mesaj = yz_kopru.gorsel_indir(haber)
        self.assertFalse(oldu)
        self.assertEqual(ag.baglantilar, [])
        self.assertNotIn("169.254", mesaj)
