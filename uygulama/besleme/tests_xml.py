"""XML 1.0'da geçersiz karakterler — RSS ve sitemap (Paket F madde 7).

Değerlendirmede ölçüldü: spottaki tek bir `\\x1d` `/rss`i 500'e
düşürüyordu. Sitemap aynı karakterle hata vermeden geçersiz XML üretir.
Testler gerçek kayıt açar ve çıktıyı bir XML ayrıştırıcısına verir —
"200 döndü" yetmez, dosya ayrıştırılabilmeli.
"""

import xml.etree.ElementTree as ET

from django.test import SimpleTestCase
from django.utils import timezone

from .tests import TemelVeri
from .xml_karakter import xml_temizle

KIRLI_SPOT = "Kelime işlemciden gelen\x1d spot\x0b metni\x00."
KIRLI_BASLIK = "Başlık\x1d içinde\x08 denetim"


class Temizleyici(SimpleTestCase):

    def test_gecersizler_atilir_gecerliler_kalir(self):
        self.assertEqual(xml_temizle("a\x1db\x00c\x0bd\x0ce￾f"), "abcdef")
        self.assertEqual(xml_temizle("sekme\tsatır\nsatırbaşı\r"), "sekme\tsatır\nsatırbaşı\r")
        self.assertEqual(xml_temizle("Çağlayan ğüşiöç İı €"), "Çağlayan ğüşiöç İı €")
        self.assertIsNone(xml_temizle(None))


class KirliKayit(TemelVeri):

    def setUp(self):
        self.haber = self.haber_kur(5_500_001, timezone.now(),
                                    baslik=KIRLI_BASLIK, spot=KIRLI_SPOT,
                                    govde="<p>Gövde\x1d bir.</p><p>İki.</p>")

    def _ayristir(self, yol):
        yanit = self.client.get(yol)
        self.assertEqual(yanit.status_code, 200, yol)
        govde = b"".join(yanit.streaming_content) if yanit.streaming else yanit.content
        return ET.fromstring(govde)

    def test_rss_500_vermez_ve_ayristirilir(self):
        kok = self._ayristir("/rss")
        baslik = kok.find("channel/item/title").text
        self.assertEqual(baslik, "Başlık içinde denetim")
        self.assertIn("spot metni.", kok.find("channel/item/description").text)

    def test_kategori_beslemesi_de_temiz(self):
        kok = self._ayristir("/rss/gundem")
        self.assertEqual(kok.find("channel/item/title").text, "Başlık içinde denetim")

    def test_google_news_sitemap_gecerli_xml(self):
        kok = self._ayristir("/static/sitemap/googleNews.xml")
        ad = {"n": "http://www.google.com/schemas/sitemap-news/0.9"}
        basliklar = [e.text for e in kok.iter("{%s}title" % ad["n"])]
        self.assertIn("Başlık içinde denetim", basliklar)
