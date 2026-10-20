"""Haber detayında paylaşım bağlantıları (20 Ekim 2026, `parca/paylas.html`).

Sözleşme:
- WhatsApp, X, Facebook — BETİKSİZ düz bağlantı; dış betik, SDK, iframe yok.
- Adres sayfanın kanonik adresi, metin haber başlığı; ikisi de tamamen
  yüzde-kodlu (Türkçe harf, boşluk, `&`, `?`, `'`).
- Yeni sekme + `rel="noopener noreferrer"`, anlamlı `aria-label`.
- "Bağlantıyı kopyala" aynı grupta durur; yazdırmada grup gizli.
"""

import html
import re
from datetime import timedelta
from pathlib import Path
from urllib.parse import parse_qs, quote, urlsplit

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from taksonomi.models import Kategori, KategoriTur

from .models import Haber

KOK = Path(__file__).resolve().parent.parent
BASLIK = "Gürsu'da çığ & şok: İnegöl yolu kapandı mı? %100 \"kapalı\""
BAG = re.compile(r'<a class="paylas-bag"([^>]*)>(.*?)</a>', re.S)


def _nit(parca, ad):
    m = re.search(rf'\b{ad}="([^"]*)"', parca)
    return html.unescape(m.group(1)) if m else None


class PaylasimBaglantilari(TestCase):

    @classmethod
    def setUpTestData(cls):
        call_command("taksonomi_kur", verbosity=0)
        kategori = KategoriTur.objects.get(tur=Kategori.TUR_HABER, slug="gundem").kategori
        cls.haber = Haber.objects.create(
            id=5_950_001, slug="gursuda-cig-ve-sok", baslik=BASLIK, kategori=kategori,
            spot="Spot", govde="<p>Bir.</p><p>İki.</p>", durum=Haber.DURUM_AKTIF,
            kaynak_turu=Haber.KAYNAK_MUHABIR, muhabir="",
            yayin_zamani=timezone.now() - timedelta(minutes=5))

    def setUp(self):
        yanit = self.client.get(self.haber.get_absolute_url())
        self.assertEqual(yanit.status_code, 200)
        self.metin = yanit.content.decode()
        self.kanonik = html.unescape(
            re.search(r'<link rel="canonical" href="([^"]+)"', self.metin).group(1))
        self.baglar = {}
        for nit, ic in BAG.findall(self.metin):
            self.baglar[_nit(nit, "aria-label")] = (nit, ic)

    def _adres(self, etiket):
        return _nit(self.baglar[etiket][0], "href")

    def test_uc_baglanti_var_ve_kopyala_ayni_grupta(self):
        self.assertEqual(set(self.baglar),
                         {"WhatsApp'ta paylaş", "X'te paylaş", "Facebook'ta paylaş"})
        bas = self.metin.index('class="paylas"')
        grup = self.metin[bas:self.metin.index("</div>", bas)]
        self.assertIn('role="group"', self.metin[bas - 20:bas + 80])
        self.assertEqual(grup.count('class="paylas-bag"'), 3)
        self.assertIn("BAĞLANTIYI KOPYALA", grup)
        # Paylaşım `.arac` içinde: künye testleri `class="arac"`a kadar keser.
        self.assertLess(self.metin.index('class="arac"'), bas)

    def test_adresler_tamamen_kodlu_ve_dogru(self):
        a, m = quote(self.kanonik, safe=""), quote(BASLIK, safe="")
        self.assertEqual(self._adres("WhatsApp'ta paylaş"), f"https://wa.me/?text={m}%20{a}")
        self.assertEqual(self._adres("X'te paylaş"),
                         f"https://x.com/intent/post?url={a}&text={m}")
        self.assertEqual(self._adres("Facebook'ta paylaş"),
                         f"https://www.facebook.com/sharer/sharer.php?u={a}")
        # Türkçe harfler UTF-8 yüzde kodu; ayraçlar kaçmış.
        for parca in ("G%C3%BCrsu", "%C3%A7%C4%B1%C4%9F", "%26", "%3F", "%27", "%25100"):
            self.assertIn(parca, self._adres("X'te paylaş"), parca)
        # Kodu çözülünce başlık ve kanonik adres birebir geri gelir.
        sorgu = parse_qs(urlsplit(self._adres("X'te paylaş")).query)
        self.assertEqual(sorgu, {"url": [self.kanonik], "text": [BASLIK]})
        sorgu = parse_qs(urlsplit(self._adres("WhatsApp'ta paylaş")).query)
        self.assertEqual(sorgu, {"text": [f"{BASLIK} {self.kanonik}"]})
        sorgu = parse_qs(urlsplit(self._adres("Facebook'ta paylaş")).query)
        self.assertEqual(sorgu, {"u": [self.kanonik]})

    def test_html_kacisi_dogru(self):
        """Ham `&` nitelikte durmaz (`&amp;`); başlıktaki tırnak niteliği kırmaz."""
        nit = self.baglar["X'te paylaş"][0]
        self.assertIn("&amp;text=", nit)
        self.assertNotIn('"kapal', nit)

    def test_yeni_sekme_ve_rel(self):
        for etiket, (nit, ic) in self.baglar.items():
            self.assertEqual(_nit(nit, "target"), "_blank", etiket)
            self.assertEqual(set(_nit(nit, "rel").split()), {"noopener", "noreferrer"}, etiket)
            self.assertEqual(_nit(nit, "title"), etiket)
            self.assertIn('aria-hidden="true"', ic, etiket)

    def test_simgeler_yerel_kutuphanede(self):
        for _, ic in self.baglar.values():
            ad = re.search(r'<use href="#([^"]+)"', ic).group(1)
            self.assertIn(f'<symbol id="{ad}"', self.metin, ad)

    def test_dis_betik_cerceve_yok(self):
        """Paylaşım için sayfaya dışarıdan hiçbir şey yüklenmez."""
        self.assertNotIn("<iframe", self.metin)
        kendi = "{0.scheme}://{0.netloc}/".format(urlsplit(self.kanonik))
        betikler = re.findall(r'<script[^>]*\bsrc="([^"]+)"', self.metin)
        self.assertTrue(betikler)          # sayfanın kendi betikleri ölçülüyor
        for src in betikler:
            yerel = src.startswith("/") and not src.startswith("//")
            self.assertTrue(yerel or src.startswith(kendi), src)
        for alan in ("wa.me", "x.com", "facebook.com", "twitter.com", "connect.facebook",
                     "platform.twitter"):
            for nitelik in re.findall(r'\b(?:src|srcset|data-src)="([^"]*)"', self.metin):
                self.assertNotIn(alan, nitelik)
        # Paylaşım alan adları yalnız paylaşım bağlantılarının href'inde geçer.
        govde = BAG.sub("", self.metin)
        for alan in ("wa.me/", "x.com/intent", "facebook.com/sharer"):
            self.assertNotIn(alan, govde, alan)

    def test_yazdirmada_gizli(self):
        css = (KOK / "statik" / "stil" / "site.css").read_text(encoding="utf-8")
        bas = css.index("@media print{")
        kural = css[bas:css.index("}", bas)]
        self.assertIn(".paylas", kural)
        self.assertIn(".arac", kural)
