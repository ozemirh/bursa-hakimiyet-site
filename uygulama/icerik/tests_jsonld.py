"""Şablon enjeksiyonu — `|safe` taraması ve JSON-LD (Paket F madde 6).

1. Hiçbir şablonda `|safe` ya da `{% autoescape off %}` yok. Güvenli
   işaretleme Python'da, gerekçesiyle yapılır (`icerik/jsonld.py`,
   `icerik/temizle.py`); yeni bir `|safe` bu testi düşürür ve gerekçesi
   olan bir istisna olarak İZİN LİSTESİNE yazılmak zorundadır.
2. Python'daki her `mark_safe` çağrısı da listelidir; yenisi testi düşürür.
3. Nöbetçi eczane JSON-LD'si dış kaynaktan gelen `</script>` ile
   kapatılamaz (doğrulanmış açıktı).
4. Haber gövdesi beyaz listeden geçer: betik ve olay niteliği basılmaz.
"""

import json
import re
from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase, TestCase
from django.utils import timezone

from taksonomi.models import Kategori, KategoriTur

from .jsonld import betik_json
from .models import Haber
from .tests_eczane import ECZANELER, EczaneTabani, paket

KOK = Path(settings.BASE_DIR)
SABLON_KOKLERI = [KOK / "sablonlar", KOK / "medya" / "sablonlar"]

#: Gerekçeli istisnalar: (dosya, satır parçası). Bugün BOŞ.
SAFE_IZINLI: list[tuple[str, str]] = []

#: `mark_safe` kullanan modüller ve gerekçeleri.
MARK_SAFE_IZINLI = {
    "icerik/temizle.py": "Gövde beyaz liste temizleyicisinin çıktısı.",
    "icerik/jsonld.py": "JSON-LD: <, >, & kaçışlı JSON.",
    "icerik/templatetags/gorsel_etiket.py": "Görsel türev etiketi (Paket D): "
        "yalnız format_html — argümanlar kaçışlanır.",
}

ZARARLI_AD = 'KÖTÜ</script><script>alert(1)</script> ECZANESİ'
ZARARLI_ADRES = 'X MAH. <!-- </SCRIPT> & Y SOK.'


class SablonTaramasi(SimpleTestCase):

    def test_sablonlarda_safe_ve_autoescape_off_yok(self):
        bulunan = []
        for kok in SABLON_KOKLERI:
            for yol in kok.rglob("*.html"):
                for no, satir in enumerate(yol.read_text(encoding="utf-8").splitlines(), 1):
                    if re.search(r"\|\s*safe\b|\|\s*safeseq\b|autoescape\s+off", satir):
                        goreli = yol.relative_to(KOK).as_posix()
                        if not any(d == goreli and p in satir for d, p in SAFE_IZINLI):
                            bulunan.append(f"{goreli}:{no}: {satir.strip()[:80]}")
        self.assertEqual(bulunan, [], "Gerekçesiz |safe / autoescape off bulundu.")

    def test_mark_safe_yalniz_listelenen_modullerde(self):
        bulunan = set()
        for yol in KOK.rglob("*.py"):
            goreli = yol.relative_to(KOK).as_posix()
            if "/tests" in "/" + goreli or goreli.startswith(("tests", ".")) \
                    or "/migrations/" in goreli or goreli.split("/")[-1].startswith("tests"):
                continue
            metin = yol.read_text(encoding="utf-8", errors="replace")
            if re.search(r"\bmark_safe\(|SafeString\(|format_html\(", metin):
                bulunan.add(goreli)
        self.assertEqual(bulunan - set(MARK_SAFE_IZINLI), set())


class JsonLdKacisi(SimpleTestCase):

    def test_betik_kapatilamaz_ve_deger_korunur(self):
        veri = {"name": ZARARLI_AD, "adres": ZARARLI_ADRES, "x": "a b"}
        cikti = str(betik_json(veri))
        self.assertNotIn("<", cikti)
        self.assertNotIn(">", cikti)
        self.assertNotIn("&", cikti)
        self.assertEqual(json.loads(cikti), veri)


class EczaneEnjeksiyonu(EczaneTabani):

    def test_dis_kaynaktan_gelen_script_kapanisi_etkisiz(self):
        zararli = dict(ECZANELER[0], ad=ZARARLI_AD, adres=ZARARLI_ADRES)
        self._yaz(paket([zararli]))
        icerik = self._al("/nobetci-eczane").content.decode()
        # Ham betik bloğu sayfaya hiç düşmüyor ...
        self.assertNotIn("<script>alert(1)", icerik.lower())
        self.assertNotIn("<!-- </script>", icerik.lower())
        # ... ve JSON-LD tek parça, ayrıştırılabilir, değeri koruyor.
        ham = icerik.split('type="application/ld+json">')[1].split("</script>")[0]
        ld = json.loads(ham)
        oge = ld["itemListElement"][0]["item"]
        self.assertIn("alert(1)", oge["name"].lower())
        self.assertIn("<!--", oge["address"]["streetAddress"])


class GovdeEnjeksiyonu(TestCase):

    def test_haber_govdesinde_betik_ve_olay_niteligi_basilmaz(self):
        from django.core.management import call_command
        call_command("taksonomi_kur", verbosity=0)
        kategori = KategoriTur.objects.get(tur=Kategori.TUR_HABER, slug="gundem").kategori
        haber = Haber.objects.create(
            id=5_400_001, slug="enjeksiyon", baslik="Enjeksiyon denemesi",
            kategori=kategori, durum=Haber.DURUM_AKTIF, yayin_zamani=timezone.now(),
            spot='<script>alert("spot")</script>',
            govde='<p>Bir.</p><script>alert(1)</script>'
                  '<p><img src="x" onerror="alert(2)">İki.</p>'
                  '<p><a href="javascript:alert(3)">bağ</a></p>')
        icerik = self.client.get(haber.get_absolute_url()).content.decode()
        self.assertNotIn("<script>alert", icerik)
        self.assertNotIn("onerror", icerik)
        self.assertNotIn("javascript:alert", icerik)
