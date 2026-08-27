"""İçerik tarafı gerileme testleri.

İki şey korunuyor:

1. **Gövde temizleyicisi.** Gövde kazımayla geldi ve panelden de HTML
   girilecek. Beyaz liste delinirse sayfaya betik enjekte edilebilir; bu
   dosya o kapıyı kapalı tutar.
2. **Anasayfa bileşen sayıları.** URUN-PLANI.md §1'deki sözleşme sayıları
   (manşet 15, ikincil 5, dörtlü 4, kutu 10) şablon değişiminde sessizce
   kaymasın diye ölçülüyor.
"""

import re
from pathlib import Path

from django.test import TestCase
from django.utils import timezone

from taksonomi.models import Ilce, Kategori, KategoriTur

from .models import Haber
from .temizle import govde_temizle
from .templatetags.site_etiket import baslikla, buyult


class GovdeTemizleyici(TestCase):
    """Beyaz liste: izin verilmeyen her şey düşer."""

    def test_izinli_etiketler_korunuyor(self):
        for ham in ("<p>Merhaba</p>",
                    "<p><strong>Kalın</strong> ve <em>eğik</em></p>",
                    "<ul><li>Bir</li><li>İki</li></ul>",
                    "<h2>Ara başlık</h2>"):
            self.assertEqual(govde_temizle(ham), ham)

    def test_betik_etiketi_ve_icerigi_dusuyor(self):
        cikti = govde_temizle('<p>A</p><script>alert(1)</script><p>B</p>')
        self.assertEqual(cikti, "<p>A</p><p>B</p>")
        self.assertNotIn("alert", cikti)

    def test_gomulu_cerceve_dusuyor(self):
        self.assertNotIn("iframe", govde_temizle('<iframe src="x"></iframe><p>A</p>'))

    def test_olay_nitelikleri_dusuyor(self):
        cikti = govde_temizle('<p onclick="kotu()">Metin</p>')
        self.assertEqual(cikti, "<p>Metin</p>")

    def test_javascript_semali_baglanti_duz_metne_iniyor(self):
        cikti = govde_temizle('<p><a href="javascript:alert(1)">Tıkla</a></p>')
        self.assertNotIn("javascript", cikti)
        self.assertIn("Tıkla", cikti)

    def test_guvenli_baglanti_korunuyor_ve_isaretleniyor(self):
        cikti = govde_temizle('<p><a href="https://ornek.tr/a">Bağlantı</a></p>')
        self.assertIn('href="https://ornek.tr/a"', cikti)
        self.assertIn('rel="noopener nofollow"', cikti)

    def test_gorsel_dusuyor(self):
        """Arşiv görselleri kaynak sunucudan silindi; gövdedeki <img> ölü
        adrese bakıyor ve kırık görsel çizerdi."""
        self.assertEqual(govde_temizle('<p>A</p><img src="http://x/y.jpg"><p>B</p>'),
                         "<p>A</p><p>B</p>")

    def test_bilinmeyen_etiket_dusuyor_icerik_kaliyor(self):
        self.assertEqual(govde_temizle('<div><span>Metin</span></div>'), "Metin")

    def test_metin_kacisliyor(self):
        self.assertIn("&lt;", govde_temizle('<p>5 < 7 ve a & b</p>'))

    def test_fazladan_kapanis_etiketi_cokertmiyor(self):
        self.assertEqual(govde_temizle("<p>A</p></p></div>"), "<p>A</p>")

    def test_kapanmamis_etiket_kapatiliyor(self):
        self.assertEqual(govde_temizle("<p>A"), "<p>A</p>")

    def test_bos_govde(self):
        self.assertEqual(govde_temizle(""), "")


class TurkceBuyukKucuk(TestCase):
    """Python'un `.title()`/`.upper()` metotları Türkçe'de yanlış sonuç verir."""

    def test_baslikla(self):
        self.assertEqual(baslikla("EKONOMİ"), "Ekonomi")
        self.assertEqual(baslikla("IĞDIR"), "Iğdır")
        self.assertEqual(baslikla("SAVUNMA SANAYİ"), "Savunma Sanayi")

    def test_buyult(self):
        self.assertEqual(buyult("Ekonomi"), "EKONOMİ")
        self.assertEqual(buyult("Iğdır"), "IĞDIR")


class SayfalarVeritabanindanRender(TestCase):
    """F4 bitti ölçütü (b): sayfalar veritabanından render ediliyor."""

    @classmethod
    def setUpTestData(cls):
        from django.core.management import call_command
        call_command("taksonomi_kur", verbosity=0)
        cls.ilce = Ilce.objects.first()
        # Anasayfa 34 kayıt tüketiyor (15 + 5 + 4 + 10); havuz dolsun.
        for n in range(40):
            tur = KategoriTur.objects.filter(
                tur=Kategori.TUR_HABER, slug="gundem").first()
            Haber.objects.create(
                id=700000 + n, slug=f"haber-{n}", baslik=f"Deneme başlığı {n}",
                spot=f"Deneme spotu {n}", govde=f"<p>Gövde {n}</p>",
                kategori=tur.kategori,
                ilce=cls.ilce if n % 2 == 0 else None,
                yayin_zamani=timezone.now())

    def test_anasayfa_bilesen_sayilari(self):
        yanit = self.client.get("/")
        self.assertEqual(yanit.status_code, 200)
        icerik = yanit.content.decode()
        self.assertEqual(icerik.count('aria-roledescription="slayt"'), 15 + 5)
        self.assertEqual(len(yanit.context["manset"]), 15)
        self.assertEqual(len(yanit.context["ikincil"]), 5)
        self.assertEqual(len(yanit.context["dortlu"]), 4)
        self.assertEqual(len(yanit.context["kutular"]), 10)

    def test_anasayfa_bloklari_ayni_haberi_tekrarlamiyor(self):
        yanit = self.client.get("/")
        kimlikler = [h.id for anahtar in ("manset", "ikincil", "dortlu", "kutular")
                     for h in yanit.context[anahtar]]
        self.assertEqual(len(kimlikler), len(set(kimlikler)))

    def test_haber_detay(self):
        haber = Haber.objects.get(id=700000)
        yanit = self.client.get(haber.get_absolute_url())
        self.assertEqual(yanit.status_code, 200)
        self.assertContains(yanit, "Deneme başlığı 0")
        self.assertContains(yanit, "Gövde 0")

    def test_kategori_sayfasi(self):
        yanit = self.client.get("/gundem")
        self.assertEqual(yanit.status_code, 200)
        self.assertEqual(yanit.context["sayfa"].paginator.count, 40)

    def test_ilce_sayfasi(self):
        yanit = self.client.get(f"/ilce/{self.ilce.slug}")
        self.assertEqual(yanit.status_code, 200)
        self.assertEqual(yanit.context["sayfa"].paginator.count, 20)

    def test_arama_bulur(self):
        yanit = self.client.get("/ara", {"q": "Deneme başlığı 3"})
        self.assertEqual(yanit.status_code, 200)
        self.assertGreaterEqual(yanit.context["toplam"], 1)

    def test_arama_bos_sorgu_hata_vermiyor(self):
        self.assertEqual(self.client.get("/ara").status_code, 200)

    def test_yayindan_kaldirilan_haber_gorunmuyor(self):
        haber = Haber.objects.get(id=700001)
        haber.durum = Haber.DURUM_PASIF
        haber.save(update_fields=["durum"])
        self.assertEqual(self.client.get(haber.get_absolute_url()).status_code, 404)

    def test_sayfalama_ikinci_sayfa(self):
        yanit = self.client.get("/gundem", {"sayfa": 2})
        self.assertEqual(yanit.status_code, 200)
        self.assertEqual(yanit.context["sayfa"].number, 2)

    def test_bekleyen_aile_sayfalari(self):
        for yol in ("/yazarlar", "/galeriler", "/videolar", "/resmi-ilan"):
            with self.subTest(yol=yol):
                self.assertEqual(self.client.get(yol).status_code, 200)

    def test_sablonda_gomulu_haber_basligi_yok(self):
        """F4 ölçüt (a): şablonlarda gömülü başlık/gövde olmamalı.

        Boş veritabanıyla render edilen anasayfada hiçbir haber başlığı
        çıkmamalı; çıkıyorsa şablona metin gömülmüş demektir.
        """
        Haber.objects.all().delete()
        icerik = self.client.get("/").content.decode()
        self.assertNotIn("Deneme başlığı", icerik)
        self.assertEqual(icerik.count('aria-roledescription="slayt"'), 0)


class ProjeKurallariSayiyla(TestCase):
    """URUN-PLANI.md §3.1 madde 10 ve CLAUDE.md renk kuralı — ölçülerek.

    F4 bitti ölçütü (c) §3.1'in ölçüm turunun şablon hâli üzerinde
    tekrarlanmasını istiyor; bu madde grep'le ölçülebilen kısmıdır.
    Kural: renk taşıyan property'lerde doğrudan hex/rgba yazılmaz,
    `:root` içindeki değişkenden gelir.
    """

    KOK = Path(__file__).resolve().parent.parent
    RENK_PROPERTY = re.compile(
        r"(?:^|[;{\s])(?:color|background|background-color|border[a-z-]*|"
        r"outline-color|fill|stroke|box-shadow|text-shadow)\s*:[^;}]*", re.I)
    HAM_RENK = re.compile(r"#[0-9a-fA-F]{3,8}\b|rgba?\(")

    def _stil(self, ad):
        return (self.KOK / "statik" / "stil" / ad).read_text(encoding="utf-8")

    def _kok_disi_govde(self, metin):
        """`:root{...}` bloğu ölçüme girmez: değişken TANIMI orada olacak."""
        return re.sub(r":root\s*\{[^}]*\}", "", metin, flags=re.S)

    def test_renk_propertysinde_ham_renk_yok(self):
        govde = self._kok_disi_govde(self._stil("site.css"))
        # `.t-mavi{--s1:#...}` gibi öğe başına değişken TANIMLARI sayılmaz
        # (URUN-PLANI.md §7 kararı).
        govde = re.sub(r"--[a-z0-9-]+\s*:[^;}]*", "", govde)
        suclu = [p.strip() for p in self.RENK_PROPERTY.findall(govde)
                 if self.HAM_RENK.search(p)]
        self.assertEqual(suclu, [], f"renk property'sinde ham renk: {suclu[:5]}")

    def test_ingilizce_sinif_adi_yok(self):
        yasak = {"header", "footer", "sidebar", "wrapper", "container", "btn",
                 "card", "title", "hidden", "active", "content", "search"}
        for klasor in ("sablonlar", "medya/sablonlar"):
            for yol in (self.KOK / klasor).rglob("*.html"):
                if "panel" in yol.parts:
                    continue
                for sinif in re.findall(r'class="([^"]*)"', yol.read_text(encoding="utf-8")):
                    for ad in sinif.split():
                        self.assertNotIn(ad, yasak, f"{yol.name}: {ad}")

    def test_cok_satirli_django_yorumu_yok(self):
        """`{# … #}` TEK SATIRLIKTIR; çok satırlısı sayfaya düz metin basılır.

        Bu hata 27 Ağustos'ta panel yerleşimini bozdu (URUN-PLANI.md §12).
        """
        for klasor in ("sablonlar", "medya/sablonlar"):
            for yol in (self.KOK / klasor).rglob("*.html"):
                for no, satir in enumerate(yol.read_text(encoding="utf-8").splitlines(), 1):
                    if "{#" in satir:
                        self.assertIn("#}", satir, f"{yol.name}:{no} çok satırlı {{# #}}")

    def test_kunyede_canli_veri_beyani_dogru(self):
        """Künye okura beyan veriyor; yanlış beyan bırakılmaz.

        27 Ağustos: altı kalemin beşi canlı kaynağa bağlandı, künye hâlâ
        "hiçbiri bağlanmadı" diyordu.
        """
        metin = (self.KOK / "sablonlar" / "parca" / "kunye.html").read_text(encoding="utf-8")
        self.assertNotIn("henüz canlı kaynağa bağlanmamıştır", metin)
        self.assertNotIn("Wikimedia Commons", metin)
        for kaynak in ("TCMB", "MGM", "TFF", "Diyanet"):
            self.assertIn(kaynak, metin)
