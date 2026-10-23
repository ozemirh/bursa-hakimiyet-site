"""Başlık kademesi, mobil ilk ekran ve dokunma hedefleri — 20 Ekim 2026 (tur B).

Tasarım önerisi `referans-kutuphanesi/tasarim/bursa-hakimiyet-oneri.md`
R4–R8, R11, R12; kullanıcı kararları K2, K3, K4. Ölçüm (başsız Chrome, okur
hâli, 390x844):

    anasayfa: dörtlünün ilk kartı 2.066 → 597 px, ilk ekranda tam başlık 1 → 3,
              manşet sayfalayıcısı 96 → 41 px
    ekonomi:  H1 1.109 → 247 px (bursaspor 742, sağlık 884, teknoloji 640 → 247)
    sağlık:   eczane `a.tel`/`a.harita` 18 → 44 px (≤600), masaüstünde 28

Sözleşmeler:

1. **İki kademe (K4).** Dolu çubuk yalnız sayfa başlığı (`h1`) ve kimlik
   blokları: anasayfanın BURSASPOR kutusu ve SON DAKİKA plakası. Geri
   kalan her bölüm başlığı `.kutu-bas.hafif`.
2. **Sayfa başı önce (K3).** Bölüm sayfasında h1 servis şeridinin üstünde.
3. **Telefonda dörtlü manşetin altında, reklamın önünde (K2).**
4. **Tek satır sayfalayıcı, katlanır seçim kuralı (R5, R7.3).**
5. **Eczane bağlantısı dokunmatikte 44x44 (R12).**
"""

import re
from pathlib import Path

from django.core.management import call_command
from django.test import SimpleTestCase, TestCase
from django.utils import timezone

from taksonomi.models import Kategori, KategoriTur

from .models import Haber
from .tests_cerceve import KURAL, _blok, medya_blogu

KOK = Path(__file__).resolve().parent.parent
SABLON = KOK / "sablonlar"
#: Medya uygulamasının şablon kökü ayrı (`medya/sablonlar/medya/...`); KAPSAM'daki
#: `medya/...` adları oradan okunur — Django'nun şablon adıyla aynı biçim.
MEDYA_SABLON = KOK / "medya" / "sablonlar"
KUTU_BAS = re.compile(r'<div class="(kutu-bas[^"]*)">\s*<(h1|h2)[^>]*>([^<{]*)')


def _sablon(ad: str) -> Path:
    return (MEDYA_SABLON if ad.startswith("medya/") else SABLON) / ad

#: Dolu çubukta kalmasına izin verilen h2'ler: (şablon, başlık) → gerekçe.
DOLU_IZINLI = {
    ("anasayfa.html", "BURSASPOR"): "kulüp kimliği; yeşil `#bursaspor` kuralından",
}

#: Kademeye bağlanan şablonlar (anasayfa, bölüm ve bölümün parçaları;
#: 21 Ekim 2026'dan beri köşe yazıları sayfası — K4 orada kapandı).
KAPSAM = ["anasayfa.html", "kategori.html", "parca/bolum_servis.html",
          "parca/bolum/ekonomi.html", "parca/bolum/teknoloji.html",
          "parca/bolum/bursaspor.html", "medya/kose_yazilari.html"]


class IkiKademe(SimpleTestCase):

    def test_kapsamdaki_her_baslik_hafif_ya_da_izinli(self):
        dolu = []
        for ad in KAPSAM:
            for sinif, etiket, metin in KUTU_BAS.findall(_sablon(ad).read_text(encoding="utf-8")):
                if "hafif" in sinif.split() or etiket == "h1":
                    continue
                if (Path(ad).name, metin.strip()) in DOLU_IZINLI:
                    continue
                dolu.append(f"{ad}: {sinif} {metin.strip()}")
        self.assertEqual(dolu, [], "dolu çubuk yalnız sayfa başlığı ve kimlik bloğu")

    def test_kose_yazilari_kapsamda_ve_okunuyor(self):
        """Yol düzeltmesi boşa düşmesin: medya kökünden okunan şablonda
        tek dolu çubuk h1, üç blok hafif (21 Ekim 2026; ikinci turdan beri
        sıra onaylı iskeletteki gibi: son → önceki → dizin)."""
        bulunan = KUTU_BAS.findall(_sablon("medya/kose_yazilari.html").read_text(encoding="utf-8"))
        self.assertEqual([(s, e, m.strip()) for s, e, m in bulunan], [
            ("kutu-bas vurgu", "h1", "KÖŞE YAZILARI"),
            ("kutu-bas hafif", "h2", "SON YAZILAR"),
            ("kutu-bas hafif", "h2", "ÖNCEKİ YAZILAR"),
            ("kutu-bas hafif", "h2", "YAZARLAR A–Z")])

    def test_sayfa_basligi_dolu_cubukta(self):
        metin = (SABLON / "kategori.html").read_text(encoding="utf-8")
        self.assertIn(("kutu-bas vurgu", "h1"), [(s, e) for s, e, _ in KUTU_BAS.findall(metin)])

    def test_kimlik_bloklari_yerinde(self):
        ana = (SABLON / "anasayfa.html").read_text(encoding="utf-8")
        self.assertRegex(ana, r'<div class="kutu-bas vurgu"><h2>BURSASPOR</h2>')
        self.assertIn("#bursaspor .kutu-bas.vurgu{background:var(--yesil)}", KURAL)
        # 23 Ekim 2026: anasayfada son dakika kutusu yok, tepedeki bant var
        # (taban.html); ikisi de aynı koyu plakayı taşıyor.
        self.assertNotIn('include "parca/son_dakika.html"', ana)
        taban = (SABLON / "taban.html").read_text(encoding="utf-8")
        self.assertIn('include "parca/son_dakika_bandi.html"', taban)
        self.assertIn("background:var(--sd-plaka)", _blok(".sd-bant-plaka"))
        self.assertIn("background:var(--sd-plaka)", _blok(".sondakika-plaka"))

    def test_eski_bes_bicim_kalkti(self):
        """Günün manşetleri, resmî ilan ve bölümün en çok okunanları kendi
        başlık biçimini taşıyordu; üçü de hafif kademeye bağlandı."""
        for secici in (".manset-liste h2", ".ilan-bas h2", ".en-cok h2"):
            with self.assertRaises(AssertionError, msg=secici):
                _blok(secici)
        self.assertNotIn("border-top", _blok(".manset-liste"))
        self.assertNotIn("border-top", _blok(".en-cok"))
        ana = (SABLON / "anasayfa.html").read_text(encoding="utf-8")
        self.assertIn('<div class="kutu-bas hafif ilan-bas">', ana)
        self.assertIn('<div class="kutu-bas hafif"><h2 id="manset-liste-bas">', ana)

    def test_hafif_kademe_rol_degiskenleriyle(self):
        """Temalı sayfada üç rol değişir; ham renk yazılmaz."""
        b = _blok(".kutu-bas.hafif")
        self.assertIn("background:var(--tema-kagit)", b)
        self.assertIn("border-bottom:2px solid var(--tema-hafif-cizgi)", b)
        self.assertIn("color:var(--tema-koyu)", _blok(".kutu-bas.hafif h2"))
        self.assertIn("background:var(--tema-fitil-ak)", _blok(".kutu-bas.hafif h2::before"))
        # Varsayılan temada fitil kırmızı: kırmızı seyrelir, kaybolmaz.
        kok = re.search(r":root\s*\{([^}]*)\}", KURAL).group(1)
        self.assertIn("--tema-fitil-ak:var(--kirmizi);", kok)


class SayfaBasiOnce(TestCase):
    """K3: bölüm adı servis şeridinin üstünde."""

    @classmethod
    def setUpTestData(cls):
        call_command("taksonomi_kur", verbosity=0)
        kategori = KategoriTur.objects.filter(
            tur=Kategori.TUR_HABER, slug="gundem").first().kategori
        Haber.objects.create(id=952000, slug="kademe-1", baslik="Kademe haberi",
                             spot="Spot", govde="<p>Gövde</p>", kategori=kategori,
                             yayin_zamani=timezone.now())

    def test_sablonda_baslik_servisten_once(self):
        metin = (SABLON / "kategori.html").read_text(encoding="utf-8")
        h1 = metin.index('<header class="kutu bolum-bas">')
        self.assertLess(h1, metin.index('{% include "parca/bolum_servis.html" %}'))
        self.assertLess(h1, metin.index('{% include tema.duzen with yer="bas" %}'))
        self.assertLess(metin.index('{% include "parca/bolum_servis.html" %}'),
                        metin.index('<section class="kutu bolum"'))

    def test_sayfada_h1_kirintidan_hemen_sonra(self):
        metin = self.client.get("/gundem").content.decode()
        self.assertRegex(metin, r'</nav>\s*(?:\s*)<header class="kutu bolum-bas">')
        self.assertLess(metin.index("<h1>"), metin.index('<section class="kutu bolum"'))

    def test_bitisik_kutular_birlesir(self):
        self.assertIn("margin-bottom:0", _blok(".bolum-bas:has(+.bolum)"))
        self.assertIn("border-top:0", _blok(".bolum-bas+.bolum"))


class MobilIlkEkran(SimpleTestCase):

    def test_dortlu_manset_yani_reklamin_onunde(self):
        """K2 — ≤600'de manşet → dörtlü → reklam → mini slayt (23 Ekim 2026:
        sondaki son dakika satırı kutusu ve panosuyla kalktı)."""
        govde = medya_blogu(KURAL, "max-width:600px", ".ust-blok .manset-alani,.ust-blok .manset-yan")
        self.assertIn(".ust-blok .manset-alani,.ust-blok .manset-yan{display:contents}", govde)
        sira = {}
        for sec in (".manset-slayt", ".dortlu", ".manset-yan .reklam", ".mini-slayt"):
            m = re.search(r"\.ust-blok %s\{[^}]*order:(\d)" % re.escape(sec), govde)
            self.assertIsNotNone(m, sec)
            sira[sec] = int(m.group(1))
        self.assertEqual(sorted(sira, key=sira.get), [".manset-slayt", ".dortlu", ".manset-yan .reklam",
                                                      ".mini-slayt"])

    def test_ust_blok_dom_sirasi_degismedi(self):
        """Sarmalayıcılar `display:contents` ile açılıyor; DOM'da reklam
        `.manset-yan`ın içinde kalmalı ki masaüstü düzeni aynen dursun."""
        ana = (SABLON / "anasayfa.html").read_text(encoding="utf-8")
        self.assertLess(ana.index('<section class="dortlu"'), ana.index('<div class="manset-alani">'))
        yan = ana.index('<div class="manset-yan">')
        self.assertLess(yan, ana.index("-Manşet yanı- 300x250"))
        self.assertLess(ana.index("-Manşet yanı- 300x250"), ana.index('<section class="slayt-kap mini-slayt"'))

    def test_sayfalayici_tek_satir(self):
        govde = medya_blogu(KURAL, "max-width:600px", ".slayt-noktalar{")
        self.assertIn(".slayt-denetim{flex-wrap:nowrap}", govde)
        m = re.search(r"\.slayt-noktalar\{([^}]*)\}", govde)
        self.assertIn("flex-wrap:nowrap", m.group(1))
        self.assertIn("overflow-x:auto", m.group(1))
        self.assertNotIn("flex-basis:100%", govde)
        self.assertIn(".slayt-noktalar button{flex:none}", govde)

    def test_secim_kurali_katlanir(self):
        """R7.3: "önce Bursa" listelerinin seçim kuralı silinmedi, katlandı."""
        for ad in ("ekonomi.html", "teknoloji.html"):
            metin = (SABLON / "parca" / "bolum" / ad).read_text(encoding="utf-8")
            self.assertRegex(metin, r'<details class="yer-not[^"]*"><summary>Bu liste nasıl seçildi\?</summary><p>[^<]{40,}</p></details>', ad)


class DokunmaHedefi(SimpleTestCase):

    def test_eczane_baglantilari(self):
        self.assertIn("margin:-5px 0", _blok(".eczane-izgara .baglar a"))
        govde = medya_blogu(KURAL, "max-width:600px),(pointer:coarse", ".eczane-izgara .baglar a")
        m = re.search(r"\.eczane-izgara \.baglar a,[^{]*\{([^}]*)\}", govde)
        self.assertIsNotNone(m)
        self.assertIn("min-height:44px", m.group(1))
        self.assertIn("min-width:44px", m.group(1))
        for sec in (".eczane-liste .baglantilar a", ".eczane-kartlar .baglantilar a"):
            self.assertIn(sec, govde)


class KartOlcegi(SimpleTestCase):
    """R8 (ikili satırda 21 px başlık) ve R11 (kart özeti 14 px)."""

    def test_kart_ozeti_14(self):
        self.assertIn("font-size:14px", _blok(".kart p"))

    def test_ikili_satir_21(self):
        self.assertIn("font-size:21px", _blok(".akis-blok.ikili h3"))
        govde = medya_blogu(KURAL, "min-width:601px", ".liste-izgara .kart:not(.genis) h3")
        self.assertIn(".liste-izgara .kart:not(.genis) h3{font-size:21px;line-height:1.2}", govde)
