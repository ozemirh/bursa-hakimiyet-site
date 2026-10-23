"""`/kose-yazilari` — köşe yazıları sayfası (19 Ekim 2026).

Kullanıcı isteği: "köşe yazıları diye bir sayfamız da olsun." `/yazarlar`
yazarları listeler; bu sayfa yazıların kendisini. Korunanlar:

1. **Adres.** Tek dilimli `/kose-yazilari` medya tablosunda çözülür;
   kök tablonun sonundaki kategori kalıbı onu "kategori" sanıp 404
   vermemeli. Sondaki eğik çizgi 301 alır (Paket G).
2. **Son yazılar (21 Ekim 2026'dan beri kademeli).** Yazar başına TEK
   kart, en yeniden eskiye, yalnız "yazıyor" kademesi (arşivdeki en yeni
   yazıya `YAZIYOR_ESIGI`nden yakın); en yeninin yazarı eşiği hep geçer,
   vitrin boş kalmaz. Pasif yazar ve yayında olmayan yazı girmez. En yeni
   yazı `TAZELIK_UYARISI`ndan eskiyse başlık tarihini söyler. İkinci
   turdan beri (onaylı iskelet): iki sütun SÜTUN SÜTUN (`--satir` =
   ceil(n/2)), kartta giriş metni ve unvan YOK, tarih kısa.
3. **Yazar dizini.** Bütün listedeki yazarlar iki kademede, Türkçe
   alfabeyle, unvan öneki sıralamada atlanarak; "Arşivde" kapalı
   `<details>`.
4. **Önceki yazılar (akış).** Vitrindeki yazılar HARİÇ bütün yazılar en
   yeniden eskiye, GÜN BAŞLIKLI — sayfa, `?sayfa=N` ve "daha fazla"
   parçası AYNI kümeden (`KoseYazisi.onceki_akis`; SQL dışlaması Python
   kademesiyle birebir). Dilimler çakışmaz; dilim bir günün ortasında
   biterse parça o günün başlığını ikinci kez basmaz (dikiş), `?sayfa=N`
   ise hep başlıkla açılır; aralık dışı sayfa 404.
5. **Başarım.** Sorgu sayısı yazar ve yazı sayısıyla BÜYÜMEZ (N+1 yok) ve
   21 Ekim'deki iki yeniden kuruluşta ARTMADI (3 / 1 / 2,
   `assertNumQueries`; vitrin dışlaması aynı sorgunun alt sorgusu);
   anonim sayfa önbelleğine girer ve köşe yazısı kaydedilince düşer.
6. **Tema ve bağlantılar.** Köşe teması kayıttan; anasayfa yazar kuşağı
   ve `/yazarlar` sayfası bu sayfaya bağlanır.
"""

import json
import re
from datetime import datetime, timedelta
from types import SimpleNamespace
from zoneinfo import ZoneInfo

from django.db import connection
from django.test import SimpleTestCase, TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import resolve
from django.utils import dateformat, timezone

from icerik import temalar
from icerik.tests_cerceve import KURAL, _blok, medya_blogu

from .models import KoseYazisi, Yazar

LOCMEM = "django.core.cache.backends.locmem.LocMemCache"
SAYFA_ACIK = override_settings(
    CACHES={"default": {"BACKEND": LOCMEM, "LOCATION": "bh-kose-veri"},
            "sayfa": {"BACKEND": LOCMEM, "LOCATION": "bh-kose-sayfa"}},
    SAYFA_ONBELLEK_SANIYE=30)

#: Kabuğu ısınmış, sayfa önbelleği kapalı istekte sorgu tavanı. Ölçülen:
#: 3 (sayım, akış dilimi, yazar başına son yazı) — 2 yazarda da 32'de de.
#: Asıl kanıt `test_sorgu_sayisi_kayitla_buyumuyor`: az ve çok veride AYNI.
#: 21 Ekim 2026 yeniden kuruluşu ÖNCESİ gerçek PG'de ölçülen: sayfa 3,
#: `/daha-fazla?kaynak=kose&sayfa=2` 1, `?sayfa=2` 2 — `test_sorgu_sayisi_artmadi`
#: üçünü birebir kilitler. İkinci turun vitrin dışlaması (`onceki_akis`)
#: sayım ve dilimin İÇİNDE alt sorgu: sayılar aynı kaldı (PG'de ölçüldü).
SORGU_TAVANI = 3
PARCA_SORGU = 1
SAYFA_N_SORGU = 2


def _govde(yanit) -> str:
    return yanit.content.decode()


def _kartlar(metin: str) -> list[str]:
    return re.findall(r'<li class="kose-kart(?: sutun-sonu)?">.*?</li>', metin, re.S)


def _kart_adresleri(metin: str) -> list[str]:
    """Vitrin kartlarındaki YAZI adresleri, sırasıyla."""
    return [re.search(r'<h3><a href="([^"]+)">', k).group(1) for k in _kartlar(metin)]


def _akis_adresleri(metin: str) -> list[str]:
    """Akış satırlarındaki yazı adresleri (yazar adresi değil), sırasıyla.
    Satırda üst bilgi `<span class="kose-ust">` (yazar · süre; 21 Ekim 2026
    ikinci tur), ardından yazının bağlantısı."""
    return re.findall(r'</span><a href="(/yazarlar/[^"/]+/[^"/]+)">', metin)


def _gun_basliklari(metin: str) -> list[str]:
    return re.findall(r'<h3 class="kose-gun"><time datetime="[^"]+">([^<]+)</time></h3>', metin)


def _dizin(metin: str, kademe: str) -> list[str]:
    """Dizinin bir kademesindeki yazar adları, sırasıyla. "Yazıyor" bir
    `div`, "Arşivde" kapalı `details` (21 Ekim 2026 ikinci tur)."""
    etiket = "details" if kademe == "arsivde" else "div"
    blok = re.search(r'<%s class="kose-dizin-%s">(.*?)</%s>' % (etiket, kademe, etiket), metin, re.S)
    return re.findall(r'<li><a href="/yazarlar/[^"/]+">([^<]+)</a>', blok.group(1)) if blok else []


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


def _yazi(zaman):
    """Saf Python ayrıştırıcılar için yalnız `yayin_zamani` taşıyan kalem."""
    return SimpleNamespace(yayin_zamani=zaman)


TR = ZoneInfo("Europe/Istanbul")


class Kademele(SimpleTestCase):
    """"Yazıyor" eşiği — referans en yeni yazı, bugün değil."""

    def test_esik_sabitleri(self):
        self.assertEqual(KoseYazisi.YAZIYOR_ESIGI, timedelta(days=45))
        self.assertEqual(KoseYazisi.TAZELIK_UYARISI, timedelta(days=7))

    def test_esik_siniri_dahil(self):
        ref = datetime(2026, 8, 27, 9, 0, tzinfo=TR)
        en_yeni, sinirda, disarda = (_yazi(ref), _yazi(ref - timedelta(days=45)),
                                     _yazi(ref - timedelta(days=45, seconds=1)))
        yaziyor, arsivde = KoseYazisi.kademele([en_yeni, sinirda, disarda])
        self.assertEqual(yaziyor, [en_yeni, sinirda])
        self.assertEqual(arsivde, [disarda])

    def test_referans_bugun_degil_en_yeni_yazi(self):
        """Arşiv yıllar önce durmuş olsa da en yeninin yazarı eşiği geçer:
        vitrin yapısı gereği boş kalamaz."""
        eski = datetime(2021, 6, 8, 9, 0, tzinfo=TR)
        tek = _yazi(eski)
        self.assertEqual(KoseYazisi.kademele([tek]), ([tek], []))

    def test_bos_liste(self):
        self.assertEqual(KoseYazisi.kademele([]), ([], []))
        self.assertEqual(KoseYazisi.kademele(iter([])), ([], []))


class GunlereBol(SimpleTestCase):

    def test_yerel_gune_gore_gruplar(self):
        """UTC'de 21 Ağustos 21:30 olan yazı TR'de 22 Ağustos 00:30'dur."""
        a = _yazi(datetime(2026, 8, 22, 10, 0, tzinfo=TR))
        b = _yazi(datetime(2026, 8, 21, 21, 30, tzinfo=ZoneInfo("UTC")))
        c = _yazi(datetime(2026, 8, 21, 23, 0, tzinfo=TR))
        gruplar = KoseYazisi.gunlere_bol([a, b, c])
        self.assertEqual([(g["gun"].isoformat(), len(g["yazilar"]), g["surer"]) for g in gruplar],
                         [("2026-08-22", 2, False), ("2026-08-21", 1, False)])

    def test_onceki_ayni_gunse_ilk_grup_surer(self):
        onceki = _yazi(datetime(2026, 8, 22, 15, 0, tzinfo=TR))
        a = _yazi(datetime(2026, 8, 22, 14, 0, tzinfo=TR))
        b = _yazi(datetime(2026, 8, 21, 14, 0, tzinfo=TR))
        gruplar = KoseYazisi.gunlere_bol([a, b], onceki)
        self.assertEqual([g["surer"] for g in gruplar], [True, False])

    def test_onceki_baska_gunse_baslikli(self):
        onceki = _yazi(datetime(2026, 8, 23, 9, 0, tzinfo=TR))
        a = _yazi(datetime(2026, 8, 22, 14, 0, tzinfo=TR))
        self.assertFalse(KoseYazisi.gunlere_bol([a], onceki)[0]["surer"])
        self.assertEqual(KoseYazisi.gunlere_bol([], onceki), [])


class DizinSirasi(SimpleTestCase):
    """Türkçe alfabe (C < Ç, I < İ), unvan öneki atlanır, kelime kelime."""

    def test_turkce_alfabe_ve_onek(self):
        adlar = ["Av. Veysel TAYYAR", "Çetin SABIRLI", "İsmail KARADUMAN", "Cennet CANKILIÇ",
                 "Doç. Dr. Filiz ERYILMAZ", "Alican DENEME", "Irmak DENEME", "Ali GENÇ",
                 "Prof. Zeki DENEME", "Orhan DOĞAN", "Onur GENÇ", "Ömer DENEME"]
        sirali = sorted(adlar, key=lambda ad: Yazar(ad=ad).dizin_anahtari)
        self.assertEqual(sirali, [
            "Ali GENÇ", "Alican DENEME", "Cennet CANKILIÇ", "Çetin SABIRLI",
            "Doç. Dr. Filiz ERYILMAZ", "Irmak DENEME", "İsmail KARADUMAN", "Onur GENÇ",
            "Orhan DOĞAN", "Ömer DENEME", "Av. Veysel TAYYAR", "Prof. Zeki DENEME"])

    def test_canli_eski_adi_ayni_anahtar(self):
        """`icerik.canli._tr_sirala` (eczane) ortak anahtara bağlı kaldı."""
        from cekirdek.tr_siralama import tr_sirala
        from icerik.canli import _tr_sirala
        self.assertIs(_tr_sirala, tr_sirala)
        self.assertLess(_tr_sirala("İnegöl"), _tr_sirala("Yenişehir"))


class KoseStili(SimpleTestCase):
    """CSS yalnız `.kose-*` kapsamında; ortak taban kuralları yerinde."""

    def test_ortak_taban_kurallari_degismedi(self):
        self.assertIn("grid-template-columns:118px minmax(0,1fr) auto", _blok(".gorus-liste li"))
        self.assertIn("display:flex", _blok(".gorus-bas"))
        self.assertIn("width:96px", _blok(".gorus-bas .portre"))

    def test_eski_sayfa_basi_kalkti(self):
        self.assertNotIn(".kose-sayfa-bas", KURAL)

    def test_tazelik_notu_basligi_kirmaz(self):
        """360'ta ölçüldü: not uzayınca "SON / YAZILAR" iki satıra düşüyordu."""
        self.assertIn("white-space:nowrap", _blok(".kose-vitrin-kutu .kutu-bas h2"))
        self.assertIn("white-space:nowrap", _blok(".kose-tazelik time"))

    def test_kart_yatay_ve_uzatilmis_baglanti(self):
        self.assertIn("display:contents", _blok(".kose-kart .gorus-bas"))
        self.assertIn("position:relative", _blok(".kose-kart"))
        self.assertIn("inset:0", _blok(".kose-kart h3 a::after"))
        self.assertIn("z-index:1", _blok(".kose-kart a.gorus-ad"))
        self.assertIn("inset:0", _blok(".kose-gun-liste a::after"))
        self.assertIn("position:relative", _blok(".kose-gun-liste li"))

    def test_dokunma_hedefi_600(self):
        for secici in (".kose-kart a.gorus-ad{", ".kose-dizin a{",
                       ".kose-bas .kutu-bas .tumu a{",
                       ".kose-dizin-kutu .kutu-bas .tumu a{"):
            with self.subTest(secici):
                govde = medya_blogu(KURAL, "max-width:600px", secici)
                kural = govde[govde.index(secici):].split("}", 1)[0]
                self.assertIn("min-height:44px", kural)
        # Geniş ekranda bant bölüm sayfalarıyla aynı yükseklikte kalır.
        self.assertNotIn("min-height", _blok(".kose-bas .kutu-bas .tumu a"))
        self.assertIn("flex-wrap:wrap", _blok(".kose-bas .kutu-bas"))
        self.assertIn("white-space:nowrap", _blok(".kose-bas .kutu-bas .tumu"))

    def test_dikis_ve_yeni_kaba_odak(self):
        self.assertIn("border-top:1px solid var(--tema-cizgi)",
                      _blok(".kose-gun-liste+.kose-gun-liste>li:first-child"))
        self.assertIn("scroll-margin-top:58px", _blok(".kose-akis>*"))
        self.assertIn("outline:3px solid", _blok(".kose-akis>*:focus-visible"))

    def test_satirda_tarih_yok(self):
        from pathlib import Path
        satir = (Path(__file__).resolve().parent / "sablonlar" / "medya" / "parca"
                 / "kose_satiri.html").read_text(encoding="utf-8")
        self.assertNotIn("<time", satir)

    # -- 21 Ekim 2026 ikinci tur: onaylı iskelet ---------------------------

    def test_vitrin_iki_sutun_sutun_sutun(self):
        """DOM sırası = okuma sırası = sütun sütun; satır sayısı şablondan."""
        b = _blok(".kose-vitrin")
        self.assertIn("grid-template-columns:repeat(2,minmax(0,1fr))", b)
        self.assertIn("grid-template-rows:repeat(var(--satir,1),auto)", b)
        self.assertIn("grid-auto-flow:column", b)
        dar = medya_blogu(KURAL, "max-width:600px", ".kose-vitrin{")
        kural = dar[dar.index(".kose-vitrin{"):].split("}", 1)[0]
        self.assertIn("grid-auto-flow:row", kural)
        self.assertIn("grid-template-columns:minmax(0,1fr)", kural)

    def test_kart_sabit_yuvali(self):
        """Ad + tarih tek satır (ad kısalır, tarih kaymaz); başlık tam
        basılır, en az iki satırlık yer tutar; portre 72 px (≤600'de 56)."""
        ad = _blok(".kose-kart a.gorus-ad")
        for parca in ("white-space:nowrap", "text-overflow:ellipsis", "overflow:hidden", "min-width:0"):
            self.assertIn(parca, ad)
        self.assertIn("flex-wrap:nowrap", _blok(".kose-kart .gorus-kimlik"))
        self.assertIn("flex:none", _blok(".kose-kart .gorus-sayi"))
        # Başlık kırpılmaz (768'de "…" ile kesiliyordu).
        self.assertNotIn("line-clamp", _blok(".kose-kart h3 a"))
        self.assertIn("min-height:2.6em", _blok(".kose-kart h3"))
        self.assertIn("width:72px;height:72px", _blok(".kose-kart .gorus-bas .portre"))
        self.assertIn("width:56px;height:56px",
                      medya_blogu(KURAL, "max-width:600px", ".kose-kart .gorus-bas .portre{"))

    def test_akis_ve_ray(self):
        """Ana sütun + sağda yapışkan ray; ray açılınca/alçak görünümde
        yapışmaz (iç kaydırma yok); ≤1000 tek sütun."""
        self.assertIn("grid-template-columns:minmax(0,1fr) 360px", _blok(".kose-alt"))
        ray = _blok(".kose-dizin-kutu")
        self.assertIn("position:sticky", ray)
        self.assertNotIn("overflow", ray)
        self.assertIn("position:static", _blok(".kose-dizin-kutu:has(details[open])"))
        self.assertIn("position:static", medya_blogu(KURAL, "max-height:700px", ".kose-dizin-kutu{"))
        self.assertIn(".kose-alt{grid-template-columns:minmax(0,1fr)}",
                      medya_blogu(KURAL, "max-width:1000px", ".kose-alt{"))

    def test_akis_satiri_ust_bilgi_satiri(self):
        """Yazar ve süre başlığın üstünde tek satırda; sağ kenar sütunu yok.
        Akış listesi `.gorus-liste` taban kurallarını almıyor."""
        self.assertIn("display:flex", _blok(".kose-ust"))
        self.assertIn("flex:none", _blok(".kose-ust .sure"))
        self.assertNotIn("grid-template-columns", _blok(".kose-gun-liste li"))
        from pathlib import Path
        gunler = (Path(__file__).resolve().parent / "sablonlar" / "medya" / "parca"
                  / "kose_gunleri.html").read_text(encoding="utf-8")
        self.assertIn('<ol class="kose-gun-liste">', gunler)
        self.assertNotIn("gorus-liste", gunler.split("{% endcomment %}", 1)[1])

    def test_olu_kurallar_silindi(self):
        for olu in (".kose-satir-yazar", ".kose-satir{", ".kose-kart p", ".kose-kart>p",
                    ".kose-kart .gorus-kose", ".kose-dizin>:only-child"):
            with self.subTest(olu):
                self.assertNotIn(olu, KURAL)


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
        # Eski yazar: son yazısı yıllar önce — vitrine girmez (eşik), dizinin
        # "Arşivde" kademesinde ay-yılıyla durur.
        KoseYazisi.objects.create(
            id=993200, slug="eski-son", baslik="Eski yazarın son yazısı", yazar=cls.eski,
            govde="<p>Eski yazarın girişi.</p>",
            yayin_zamani=simdi - timedelta(days=900))
        # Eşiğin içinde, uzun girişli yazar: kartta giriş kırpılır.
        cls.can = Yazar.objects.create(id=990076, slug="can-uzun", ad="Can UZUN",
                                       unvan="Deneme köşesi")
        KoseYazisi.objects.create(
            id=993400, slug="can-son", baslik="Can'ın son yazısı", yazar=cls.can,
            govde="<p>" + "uzun bir giriş cümlesi " * 30 + "</p>",
            yayin_zamani=simdi - timedelta(days=10))
        # Pasif yazarın en yeni yazısı hiçbir listede görünmemeli.
        KoseYazisi.objects.create(
            id=993300, slug="pasif-yazi", baslik="Pasif yazarın yazısı", yazar=cls.pasif,
            govde="<p>Pasif.</p>", yayin_zamani=simdi - timedelta(minutes=5))
        # Hiç yazısı olmayan listedeki yazar: "son yazı" alt sorgusunda NULL
        # üretir. Vitrin dışlaması (`NOT IN`) NULL görseydi akışın tamamı
        # boşalırdı — bu kayıt o tuzağı sınar.
        Yazar.objects.create(id=990077, slug="yazisiz", ad="Yazısız YAZAR")
        # Vitrin: Ayşe, Ali, Can → akış 29 - 3 = 26 yazı (2 dilim).
        cls.vitrin_kimlikleri = {993101, 993000, 993400}

    def setUp(self):
        self.yanit = self.client.get("/kose-yazilari")
        self.assertEqual(self.yanit.status_code, 200)
        self.metin = _govde(self.yanit)

    # -- iskelet ve SEO ---------------------------------------------------

    def test_iskelet_tek_h1_ve_tema(self):
        self.assertEqual(self.metin.count("<h1"), 1)
        self.assertIn("<h1>KÖŞE YAZILARI</h1>", self.metin)
        # K4: dolu çubuk yalnız H1; geri kalan üç blok hafif.
        self.assertEqual(self.metin.count('class="kutu-bas vurgu"'), 1)
        self.assertRegex(self.metin, r'<header class="kutu bolum-bas kose-bas">\s*'
                                     r'<div class="kutu-bas vurgu">\s*<h1>')
        for baslik in ("SON YAZILAR", "ÖNCEKİ YAZILAR", "YAZARLAR A–Z"):
            self.assertRegex(self.metin, r'<div class="kutu-bas hafif"><h2 id="[^"]+">%s</h2>' % baslik)
        # Blok sırası (onaylı iskelet; ≤1000'de okuma sırası da bu): H1 →
        # son yazılar → önceki yazılar → yazar dizini. Akış ve dizin aynı
        # `kose-alt` ızgarasında (geniş ekranda dizin sağ ray).
        sira = [self.metin.index(s) for s in ("<h1>", 'id="kose-son-bas"', 'class="kose-alt"',
                                              'id="kose-onceki-bas"', 'id="kose-dizin"')]
        self.assertEqual(sira, sorted(sira))
        self.assertNotIn("TÜM KÖŞE YAZILARI", self.metin)
        self.assertIn('<a href="#kose-dizin">Yazar dizini &darr;</a>', self.metin)
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
        self.assertEqual(len(kartlar), 3)          # Ayşe, Ali, Can — eski ve pasif yok
        adlar = [re.search(r'class="gorus-ad"[^>]*>([^<]+)<', k).group(1) for k in kartlar]
        self.assertEqual(adlar, ["Ayşe KAYA", "Ali GENÇ", "Can UZUN"])
        self.assertIn("Ayşe yayında", kartlar[0])  # taslak değil, yayındaki son yazı
        self.assertIn("Ali yazısı 0", kartlar[1])
        self.assertNotIn("Eski YAZAR", "".join(kartlar))
        self.assertNotIn("Pasif", self.metin)
        self.assertIn('<span class="tumu">3 yazar</span>', self.metin)

    def test_kart_sabit_yuvalar_giris_yok(self):
        """21 Ekim 2026 ikinci tur: kart = portre · (ad + kısa tarih) ·
        başlık. Gövdeden kırpılan giriş metni ve unvan basılmaz (unvan
        doluyken de — sabit yuva; 37 yazarın hiçbirinde unvan yok)."""
        kartlar = _kartlar(self.metin)
        ali = kartlar[1]
        kisa = dateformat.format(timezone.localtime(self.simdi - timedelta(hours=1)), "j M")
        self.assertRegex(ali, r'<div class="gorus-kimlik">\s*'
                              r'<a class="gorus-ad" href="/yazarlar/ali-genc-990072">Ali GENÇ</a>\s*'
                              r'<time class="gorus-sayi" datetime="[^"]+">%s</time>\s*</div>' % kisa)
        self.assertIn('<h3><a href="/yazarlar/ali-genc-990072/ali-yazi-0-993000">Ali yazısı 0</a></h3>', ali)
        for kart in kartlar:
            self.assertNotIn("<p", kart)
            self.assertNotIn("gorus-kose", kart)
        self.assertNotIn("Deneme köşesi", self.metin)
        # Gövdenin hiçbir cümlesi sayfaya girmez (giriş de, satır da basmıyor).
        for govde_cumlesi in ("ilk cümlesi", "uzun bir giriş cümlesi", "yayındaki yazısı"):
            self.assertNotIn(govde_cumlesi, self.metin)

    def test_vitrin_sutun_sutun(self):
        """3 kart → `--satir:2`: ilk sütun en yeni iki kart, ikincinin son
        kartı ilk sütunun sonu (`sutun-sonu`). DOM sırası en yeniden eskiye."""
        self.assertIn('<ul class="kose-vitrin" style="--satir:2">', self.metin)
        kartlar = _kartlar(self.metin)
        self.assertEqual([k.startswith('<li class="kose-kart sutun-sonu">') for k in kartlar],
                         [False, True, False])

    def test_taze_arsivde_tarih_uyarisi_yok(self):
        self.assertNotIn("kose-tazelik", self.metin)

    def test_yazar_dizini_iki_kademe_alfabetik(self):
        self.assertEqual(_dizin(self.metin, "yaziyor"), ["Ali GENÇ", "Ayşe KAYA", "Can UZUN"])
        self.assertEqual(_dizin(self.metin, "arsivde"), ["Eski YAZAR"])
        ay_yil = dateformat.format(timezone.localtime(self.simdi - timedelta(days=900)), "F Y")
        self.assertRegex(self.metin, r'<a href="/yazarlar/eski-yazar-990074">Eski YAZAR</a>'
                                     r'<time datetime="\d{4}-\d{2}">%s</time>' % ay_yil)
        self.assertIn("Yazıyor &middot; 3", self.metin)
        self.assertRegex(self.metin, r'<nav class="kutu kose-dizin-kutu" id="kose-dizin" '
                                     r'aria-labelledby="kose-dizin-bas">')
        self.assertIn('<a href="/yazarlar">Yazarlar sayfası &rarr;</a>', self.metin)

    def test_arsivde_kapali_details(self):
        """Ray kısa kalsın diye "Arşivde" kapalı gelir; özet sayıyı söyler
        (yazar gizlenmiş sayılmaz), açılınca ad + ay-yılı. Klavyeyle açılır:
        yerel `<summary>`, betik yok."""
        self.assertRegex(self.metin, r'<details class="kose-dizin-arsivde">\s*'
                                     r'<summary>Arşivde &middot; 1 yazar</summary>\s*<ul>')
        # Kapalı gelir (menünün kendi `details`i ayrı, kabuğun parçası).
        self.assertNotRegex(self.metin, r'<details class="kose-dizin-arsivde"[^>]*\bopen\b')
        self.assertEqual(self.metin.count('class="kose-dizin-arsivde"'), 1)

    def test_yazar_basina_son_tek_sorgu(self):
        with self.assertNumQueries(1):
            kartlar = list(KoseYazisi.yazar_basina_son())
            [(k.yazar.ad, k.get_absolute_url()) for k in kartlar]
        self.assertEqual([k.pk for k in kartlar], [993101, 993000, 993400, 993200])

    # -- akış -----------------------------------------------------------

    def test_akis_en_yeni_once_ve_ilk_dilim(self):
        adresler = _akis_adresleri(self.metin)
        self.assertEqual(len(adresler), KoseYazisi.AKIS_BOYU)
        beklenen = [y.get_absolute_url() for y in KoseYazisi.onceki_akis()[:KoseYazisi.AKIS_BOYU]]
        self.assertEqual(adresler, beklenen)
        # Vitrindeki Ayşe ve "Ali yazısı 0" akışta yok: akış Ali'nin 1.
        # yazısıyla başlar.
        self.assertEqual(adresler[0], "/yazarlar/ali-genc-990072/ali-yazi-1-993001")
        # Akışta yazar da yazılı — bağlantı değil (yazara geçiş dizinden),
        # satırın tek bağlantısı yazının kendisi. Yazar ve süre başlığın
        # üstündeki tek üst bilgi satırında.
        self.assertRegex(self.metin, r'<li><span class="kose-ust"><span class="kose-ad">Ali GENÇ</span>'
                                     r'<span class="sure">\d+ dk</span></span>'
                                     r'<a href="/yazarlar/ali-genc-990072/ali-yazi-1-993001">')
        self.assertNotIn('class="kose-ad" href', self.metin)
        self.assertIn('<div class="kose-akis">', self.metin)
        # İlk grup başlıklı; her grubun listesi ayrı `ol`.
        self.assertRegex(self.metin, r'<div class="kose-akis">\s*<h3 class="kose-gun">')
        self.assertEqual(len(_gun_basliklari(self.metin)),
                         self.metin.count('<ol class="kose-gun-liste">'))
        # Sayaç dışlanmış kümeyi sayar.
        self.assertIn('<span class="tumu">26 yazı</span>', self.metin)

    def test_vitrin_akis_tekrari_yok(self):
        """Onaylı iskelet: önceki yazılar vitrini içermez — sayfa, `?sayfa=2`
        ve "daha fazla" parçası; dilimlerin birleşimi tam küme (atlama yok)."""
        vitrin = _kart_adresleri(self.metin)
        self.assertEqual(len(vitrin), 3)
        dilimler = [_akis_adresleri(self.metin),
                    _akis_adresleri(_govde(self.client.get("/kose-yazilari?sayfa=2"))),
                    _akis_adresleri(_govde(self.client.get("/daha-fazla?kaynak=kose&sayfa=2")))]
        for dilim in dilimler:
            self.assertFalse(set(vitrin) & set(dilim), dilim)
        self.assertEqual(dilimler[1], dilimler[2])
        tum = dilimler[0] + dilimler[1]
        self.assertEqual(len(tum), len(set(tum)))                  # tekrar 0
        beklenen = {y.get_absolute_url() for y in KoseYazisi.akis()
                    if y.pk not in self.vitrin_kimlikleri}
        self.assertEqual(set(tum), beklenen)                       # atlama 0
        self.assertEqual(len(tum), 26)

    def test_sql_dislamasi_python_kademesiyle_ayni(self):
        yaziyor, _ = KoseYazisi.kademele(KoseYazisi.yazar_basina_son())
        self.assertEqual({y.pk for y in yaziyor}, self.vitrin_kimlikleri)
        self.assertEqual(set(KoseYazisi.vitrin_kimlikleri().values_list("pk", flat=True)),
                         self.vitrin_kimlikleri)
        # Yazısız yazarın NULL'u dışlamayı bozmadı.
        self.assertEqual(KoseYazisi.onceki_akis().count(), 26)

    def test_dugme_baglanti_ve_parca(self):
        self.assertIn('href="?sayfa=2" rel="next"', self.metin)
        self.assertIn('data-uc="/daha-fazla?kaynak=kose"', self.metin)
        self.assertIn('data-hedef=".kose-akis"', self.metin)
        parca = self.client.get("/daha-fazla?kaynak=kose&sayfa=2")
        self.assertEqual(parca.status_code, 200)
        parca_metin = _govde(parca)
        self.assertIn('data-devam="0"', parca_metin)   # 26 yazı: ikinci dilim son
        ikinci = _akis_adresleri(parca_metin)
        self.assertEqual(len(ikinci), 26 - KoseYazisi.AKIS_BOYU)
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
        # Dizin yalnız 1. sayfada; çubuktaki bağlantı oraya gider.
        self.assertNotIn('id="kose-dizin"', metin)
        self.assertIn('<a href="/kose-yazilari#kose-dizin">Yazar dizini &rarr;</a>', metin)
        # Kendi başına açılan sayfa: ilk grup başlıklı.
        self.assertRegex(metin, r'<div class="kose-akis">\s*<h3 class="kose-gun">')

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


class GunDikisi(TestCase):
    """"Daha fazla" dilimi bir günün ortasında başlıyor (gerçek arşivde 1.
    dilim 22 Ağustos'ta bitiyor, 2. dilim 22 Ağustos'la başlıyor). Parça o
    günün başlığını ikinci kez basmamalı; `?sayfa=2` ise kendi başına açılan
    sayfadır, başlıkla açılmalı. Tarihler SABİT: "şimdi"ye göre kurulsaydı
    gün sınırı testin koştuğu saate göre kayardı.

    Tek yazar: en yeni yazısı (23 Ağustos 17:30) vitrinde, akışta değil
    (21 Ekim 2026 ikinci tur) — akış 25 yazı."""

    @classmethod
    def setUpTestData(cls):
        yazar = Yazar.objects.create(id=991001, slug="dikis-yazar", ad="Dikiş YAZAR")
        zamanlar = (
            # 23 Ağustos: 18 yazı, 09:00–17:30 (yerel); 17:30 vitrinde,
            # 17'si akışta.
            [datetime(2026, 8, 23, 9, 0, tzinfo=TR) + timedelta(minutes=30 * n) for n in range(18)]
            # 22 Ağustos: 7 yazı, 10:00–16:00 — 1. dilime 3'ü girer, 4'ü taşar.
            + [datetime(2026, 8, 22, 10, 0, tzinfo=TR) + timedelta(hours=n) for n in range(7)]
            # UTC'de 21 Ağustos 21:30 = TR'de 22 Ağustos 00:30: 22'nin grubuna.
            + [datetime(2026, 8, 21, 21, 30, tzinfo=ZoneInfo("UTC"))])
        for n, zaman in enumerate(zamanlar):
            KoseYazisi.objects.create(
                id=994000 + n, slug=f"dikis-{n}", baslik=f"Dikiş yazısı {n}", yazar=yazar,
                govde="<p>Gövde.</p>", yayin_zamani=zaman)

    def test_birinci_sayfa_iki_gun(self):
        metin = _govde(self.client.get("/kose-yazilari"))
        self.assertEqual(_gun_basliklari(metin), ["23 Ağustos 2026, Pazar", "22 Ağustos 2026, Cumartesi"])
        self.assertIn('<time datetime="2026-08-22">', metin)

    def test_parca_ayni_gunu_surdurur_basliksiz(self):
        metin = _govde(self.client.get("/daha-fazla?kaynak=kose&sayfa=2"))
        self.assertEqual(_gun_basliklari(metin), [])
        self.assertRegex(metin, r'<div class="akis-parca" data-devam="0">\s*'
                                r'<ol class="kose-gun-liste">')
        self.assertEqual(metin.count('<ol class="kose-gun-liste">'), 1)
        self.assertEqual(len(_akis_adresleri(metin)), 25 - KoseYazisi.AKIS_BOYU)
        # Bir satır geriden okunan kayıt basılmaz: dilimler çakışmaz.
        sayfa = _govde(self.client.get("/kose-yazilari"))
        birinci = _akis_adresleri(sayfa)
        self.assertFalse(set(birinci) & set(_akis_adresleri(metin)))
        self.assertEqual(len(birinci) + len(_akis_adresleri(metin)), 25)
        # Vitrindeki yazı (dikis-17) hiçbir dilimde yok.
        self.assertEqual(_kart_adresleri(sayfa), ["/yazarlar/dikis-yazar-991001/dikis-17-994017"])
        self.assertNotIn(_kart_adresleri(sayfa)[0], birinci + _akis_adresleri(metin))

    def test_sayfa_n_kendi_basina_baslikli(self):
        metin = _govde(self.client.get("/kose-yazilari?sayfa=2"))
        self.assertEqual(_gun_basliklari(metin), ["22 Ağustos 2026, Cumartesi"])
        self.assertEqual(_akis_adresleri(metin),
                         _akis_adresleri(_govde(self.client.get("/daha-fazla?kaynak=kose&sayfa=2"))))

    def test_bayat_arsivde_baslik_tarihi_soyler(self):
        """En yeni yazı 23 Ağustos: bugünden 7 günden eski → sayaçta tarih."""
        metin = _govde(self.client.get("/kose-yazilari"))
        self.assertIn('1 yazar<span class="kose-tazelik"> &middot; en yeni yazı '
                      '<time datetime="2026-08-23T17:30:00+03:00">23 Ağustos 2026</time></span>', metin)

    def test_aralik_disi_parca_bos(self):
        metin = _govde(self.client.get("/daha-fazla?kaynak=kose&sayfa=3"))
        self.assertIn('data-devam="0"', metin)
        self.assertEqual(_akis_adresleri(metin), [])


class YeniGunleBaslayanParca(TestCase):
    """Dilim sınırı gün sınırına denk gelirse parça başlıkla açılır. En
    yeni yazı (n=0) vitrinde: 20 Ağustos'un kalan 20 yazısı 1. dilimi tam
    doldurur."""

    @classmethod
    def setUpTestData(cls):
        yazar = Yazar.objects.create(id=991002, slug="sinir-yazar", ad="Sınır YAZAR")
        for n in range(KoseYazisi.AKIS_BOYU + 3):
            gun = 20 if n <= KoseYazisi.AKIS_BOYU else 19
            KoseYazisi.objects.create(
                id=995000 + n, slug=f"sinir-{n}", baslik=f"Sınır {n}", yazar=yazar,
                govde="<p>Gövde.</p>",
                yayin_zamani=datetime(2026, 8, gun, 8, 0, tzinfo=TR) + timedelta(minutes=30 - n))

    def test_parca_yeni_gun_basligiyla(self):
        metin = _govde(self.client.get("/daha-fazla?kaynak=kose&sayfa=2"))
        self.assertEqual(_gun_basliklari(metin), ["19 Ağustos 2026, Çarşamba"])
        self.assertRegex(metin, r'data-devam="0">\s*<h3 class="kose-gun">')


class VitrinBosKalmaz(TestCase):

    def test_bos_veritabani(self):
        yanit = self.client.get("/kose-yazilari")
        self.assertEqual(yanit.status_code, 200)
        metin = _govde(yanit)
        self.assertEqual(metin.count("<h1"), 1)
        self.assertEqual(_kartlar(metin), [])
        self.assertNotIn('id="kose-dizin"', metin)
        self.assertNotIn("Yazar dizini", metin)          # gidecek yer yok
        self.assertIn("Arşivde henüz köşe yazısı yok.", metin)
        parca = self.client.get("/daha-fazla?kaynak=kose")
        self.assertEqual(parca.status_code, 200)
        self.assertIn('data-devam="0"', _govde(parca))

    def test_yillar_once_durmus_arsivde_en_yeninin_yazari_vitrinde(self):
        """Referans bugün olsaydı eşiği kimse geçemezdi."""
        yazar = Yazar.objects.create(id=991003, slug="tek-yazar", ad="Tek YAZAR")
        diger = Yazar.objects.create(id=991004, slug="diger-yazar", ad="Diğer YAZAR")
        simdi = timezone.now()
        KoseYazisi.objects.create(id=996000, slug="tek", baslik="Tek yazı", yazar=yazar,
                                  govde="<p>Tek.</p>", yayin_zamani=simdi - timedelta(days=900))
        KoseYazisi.objects.create(id=996001, slug="diger", baslik="Diğer yazı", yazar=diger,
                                  govde="<p>Diğer.</p>", yayin_zamani=simdi - timedelta(days=1000))
        metin = _govde(self.client.get("/kose-yazilari"))
        kartlar = _kartlar(metin)
        self.assertEqual(len(kartlar), 1)
        self.assertIn("Tek YAZAR", kartlar[0])
        self.assertEqual(_dizin(metin, "yaziyor"), ["Tek YAZAR"])
        self.assertEqual(_dizin(metin, "arsivde"), ["Diğer YAZAR"])
        self.assertIn('class="kose-tazelik"', metin)


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
        # 32 yazar → 32 kart, yine aynı sorgu sayısıyla; iki sütun × 16.
        metin = _govde(self.client.get("/kose-yazilari"))
        self.assertEqual(len(_kartlar(metin)), 32)
        self.assertIn('style="--satir:16"', metin)
        self.assertEqual(metin.count("sutun-sonu"), 1)

    def test_sorgu_sayisi_artmadi(self):
        """21 Ekim 2026: vitrin kademesi, yazar dizini, gün grupları,
        parçanın bir satır geriden okuması ve (ikinci tur) vitrin
        dışlaması SORGU AÇMAZ — sayılar yeniden kuruluştan önce ölçülenle
        birebir (3 / 1 / 2)."""
        self._veri(6, 8, 9600)       # 48 yazı: üç dilim
        # Bir yazar "arşivde" kademesine: iki kademe, dizinde ay-yıl.
        KoseYazisi.objects.filter(yazar_id=9605).update(
            yayin_zamani=timezone.now() - timedelta(days=400))
        self.client.get("/kose-yazilari")            # kabuk ısınsın
        with self.assertNumQueries(SORGU_TAVANI):
            metin = _govde(self.client.get("/kose-yazilari"))
        self.assertEqual(_dizin(metin, "arsivde"), ["Yazar 9605"])
        with self.assertNumQueries(PARCA_SORGU):
            parca = _govde(self.client.get("/daha-fazla?kaynak=kose&sayfa=2"))
        with self.assertNumQueries(SAYFA_N_SORGU):
            ikinci = _govde(self.client.get("/kose-yazilari?sayfa=2"))
        # 48 yazı, 5 vitrin kartı (arşivdeki yazar kart almaz) → akış 43.
        self.assertEqual(len(_kartlar(metin)), 5)
        self.assertIn('style="--satir:3"', metin)
        self.assertIn('<span class="tumu">43 yazı</span>', metin)
        self.assertIn('<span class="tumu">43 yazı</span>', ikinci)
        self.assertFalse(set(_kart_adresleri(metin)) & set(_akis_adresleri(parca)))
        self.assertEqual(_akis_adresleri(parca), _akis_adresleri(ikinci))

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


class VitrinEsigiSql(TestCase):
    """SQL dışlaması Python kademesiyle sınırda da aynı: eşik dahil
    (tam 45 gün içeride, 45 gün + 1 sn dışarıda); referans en yeni yazı."""

    @classmethod
    def setUpTestData(cls):
        ref = datetime(2026, 8, 27, 9, 0, tzinfo=TR)
        for n, fark in enumerate((timedelta(0), timedelta(days=45),
                                  timedelta(days=45, seconds=1))):
            yazar = Yazar.objects.create(id=992000 + n, slug=f"esik-{n}", ad=f"Eşik {n}")
            KoseYazisi.objects.create(id=997000 + n, slug=f"esik-{n}", baslik=f"Eşik {n}",
                                      yazar=yazar, govde="<p>G.</p>", yayin_zamani=ref - fark)
            # Her yazarın daha eski bir yazısı: akışta kalmalı.
            KoseYazisi.objects.create(id=997100 + n, slug=f"esik-eski-{n}", baslik=f"Eski {n}",
                                      yazar=yazar, govde="<p>G.</p>",
                                      yayin_zamani=ref - fark - timedelta(days=1))

    def test_sinir_dahil_ve_python_ile_ayni(self):
        yaziyor, arsivde = KoseYazisi.kademele(KoseYazisi.yazar_basina_son())
        self.assertEqual([y.pk for y in yaziyor], [997000, 997001])
        self.assertEqual([y.pk for y in arsivde], [997002])
        self.assertEqual(sorted(KoseYazisi.vitrin_kimlikleri().values_list("pk", flat=True)),
                         [997000, 997001])
        self.assertEqual(sorted(KoseYazisi.onceki_akis().values_list("pk", flat=True)),
                         [997002, 997100, 997101, 997102])


class SayacBinlikAyraci(TestCase):
    """Sayaç Türkçe binlik ayracıyla ("1.001 yazı"), dışlanmış kümeyi sayar."""

    def test_nokta_ile(self):
        yazar = Yazar.objects.create(id=993500, slug="cok-yazan", ad="Çok YAZAN")
        simdi = timezone.now()
        KoseYazisi.objects.bulk_create([
            KoseYazisi(id=998000 + n, slug=f"cok-{n}", baslik=f"Çok {n}", yazar=yazar,
                       govde="", yayin_zamani=simdi - timedelta(hours=n))
            for n in range(1002)])
        metin = _govde(self.client.get("/kose-yazilari"))
        self.assertIn('<span class="tumu">1.001 yazı</span>', metin)
