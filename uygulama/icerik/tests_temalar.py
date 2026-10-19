"""Sayfaya özel tasarım düzeneği — 19 Ekim 2026.

Kullanıcı kararı: site kırmızı · lacivert · beyaz; Bursaspor yeşil-beyaz;
seçili sayfalar (köşe yazıları, ekonomi, teknoloji) kendi tasarımını alır.
`tests_bolum_bloklari.test_bolume_ozel_renk_yok` (§63, "renk teması yok")
bu dosyanın kayıt tabanlı testlerine dönüştü (§69'daki not).

Korunan dört şey:

a. **Tek kayıt.** `icerik/temalar.py`deki temalar ile `site.css`teki
   `data-bolum` değerleri birebir aynı; şablonlar ve görünümler slug'a
   bakarak nitelik yazmıyor.
b. **Takım eksiksiz, ham renk yok.** Her tema bloğu rol listesinin tamamını
   ve yalnız onu tanımlar; değerler `var(--…)`, hex `:root`ta kalır.
c. **Kontrast hesapla doğrulanır.** Her tema için metin/zemin ≥ 4,5,
   odak ve grafik ≥ 3 — değerler `:root`taki hex'lerden çözülerek.
d. **Üst kabuk değişmez.** Tema kuralları yalnız `body[data-bolum] main`
   altında; kabuk seçicileri rol değişkenine bağlanmıyor. (Tarayıcıda
   hesaplanmış renkle ölçüm de yapıldı — rapor, 19 Ekim 2026.)
"""

import re
from pathlib import Path

from django.test import TestCase
from django.utils import timezone

from medya.models import KoseYazisi, Yazar
from taksonomi.models import Ilce, Kategori, KategoriTur

from . import temalar, views
from .models import Haber

KOK = Path(__file__).resolve().parent.parent
STIL = (KOK / "statik" / "stil" / "site.css").read_text(encoding="utf-8")
KURAL = re.sub(r"/\*.*?\*/", "", STIL, flags=re.S)
TEMA_BLOGU = re.compile(r'body\[data-bolum="([^"]+)"\]\s+main\s*\{([^}]*)\}')


def _kok_degiskenleri() -> dict:
    blok = re.search(r":root\s*\{([^}]*)\}", KURAL).group(1)
    return dict(re.findall(r"(--[\w-]+)\s*:\s*([^;]+);", blok))


def _tema_takimi(anahtar: str) -> dict:
    for ad, govde in TEMA_BLOGU.findall(KURAL):
        if ad == anahtar:
            return dict(re.findall(r"(--[\w-]+)\s*:\s*([^;]+);", govde))
    return {}


def _coz(ad: str, takim: dict, kok: dict, derinlik=0) -> str:
    """Değişkeni hex'e çözer: önce temanın takımı, sonra `:root`."""
    assert derinlik < 10, ad
    deger = (takim.get(ad) or kok.get(ad) or "").strip()
    m = re.fullmatch(r"var\((--[\w-]+)\)", deger)
    if m:
        # Takımdaki bir rol başka bir rolü değil, ham renge işaret eder;
        # zincir `:root`ta çözülür.
        return _coz(m.group(1), {}, kok, derinlik + 1)
    return deger


def _parlaklik(hex_: str) -> float:
    h = hex_.lstrip("#")
    assert len(h) == 6, hex_
    def kanal(c):
        c = int(c, 16) / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (kanal(h[i:i + 2]) for i in (0, 2, 4))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def kontrast(a: str, b: str) -> float:
    x, y = _parlaklik(a), _parlaklik(b)
    return (max(x, y) + 0.05) / (min(x, y) + 0.05)


class TemaKaydi(TestCase):
    """(a) kayıt ↔ CSS, (b) takım, (c) kontrast, (d) kabuk — dosya düzeyi."""

    def test_kayit_ve_css_ayni_temalari_taniyor(self):
        css = {ad for ad, _ in TEMA_BLOGU.findall(KURAL)}
        self.assertEqual(css, set(temalar.TEMALAR))
        # `data-bolum` CSS'te YALNIZ tema bloğu seçicisi olarak geçer;
        # bileşen kuralı (`body[data-bolum] .kutu{…}`) geri gelirse düşer.
        tum = re.findall(r'data-bolum(?:="([^"]*)"|\])[^{,]*', KURAL)
        self.assertEqual(set(tum), set(temalar.TEMALAR))
        for eslesme in re.finditer(r'body\[data-bolum="[^"]+"\]([^{]*)\{', KURAL):
            self.assertEqual(eslesme.group(1).strip(), "main", eslesme.group(0))

    def test_kullanici_karari_kaydi(self):
        """Kayıttaki dört tema kullanıcının seçtikleri; ajan satır eklemez
        (EKIP.md eşik konu 7). Liste değişirse karar da değişmiş olmalı."""
        self.assertEqual(set(temalar.TEMALAR), {"bursaspor", "ekonomi", "teknoloji", "kose"})
        for tema in temalar.TEMALAR.values():
            self.assertTrue(tema.karar, tema.anahtar)
            for yuva in tema.yuvalar:
                self.assertIn(yuva, ("bas", "alt"))
                self.assertTrue((KOK / "sablonlar" / tema.duzen).exists(), tema.duzen)

    def test_rol_listesi_kokteki_tanimla_ayni(self):
        kok = _kok_degiskenleri()
        tanimli = {ad for ad in kok if ad.startswith("--tema-")}
        self.assertEqual(tanimli, set(temalar.ROLLER))

    def test_her_tema_takimi_eksiksiz_ve_ham_renksiz(self):
        kok = _kok_degiskenleri()
        for anahtar in temalar.TEMALAR:
            takim = _tema_takimi(anahtar)
            self.assertEqual(set(takim), set(temalar.ROLLER), anahtar)
            for ad, deger in takim.items():
                deger = deger.strip()
                if ad == "--tema-kirinti-agirlik":
                    self.assertRegex(deger, r"^[1-9]00$", ad)
                    continue
                self.assertRegex(deger, r"^var\(--[\w-]+\)$", f"{anahtar} {ad}")
                hedef = deger[4:-1]
                self.assertIn(hedef, kok, f"{anahtar} {ad} → {hedef} tanımsız")
                self.assertFalse(hedef.startswith("--tema-"), f"{anahtar} {ad}")

    def test_kontrast_her_temada_esigin_ustunde(self):
        kok = _kok_degiskenleri()
        bulgu = []
        for anahtar in [None, *temalar.TEMALAR]:
            takim = _tema_takimi(anahtar) if anahtar else {}
            for on, arka, esik in temalar.KONTRAST:
                a, b = _coz(on, takim, kok), _coz(arka, takim, kok)
                self.assertRegex(a, r"^#[0-9A-Fa-f]{6}$", f"{anahtar} {on}={a}")
                self.assertRegex(b, r"^#[0-9A-Fa-f]{6}$", f"{anahtar} {arka}={b}")
                oran = kontrast(a, b)
                if oran < esik:
                    bulgu.append(f"{anahtar or 'varsayılan'}: {on} / {arka} = {oran:.2f} < {esik}")
        self.assertEqual(bulgu, [])

    def test_odak_halkasi_koyu_zeminde_beyaz(self):
        """Kırmızı halka lacivertte 2,87, yeşil çubukta 1,48 ölçülmüştü."""
        kok = _kok_degiskenleri()
        self.assertLess(kontrast(kok["--kirmizi"], kok["--lacivert"]), 3)
        self.assertIn("{outline:3px solid var(--tema-odak);outline-offset:2px}", KURAL)
        for secici in (".servis", "footer", ".kategori-liste", ".menu-dugme", ".bant-logo"):
            self.assertRegex(KURAL, re.escape(secici) + r"[^{]*\{--tema-odak:var\(--kagit\)\}")
        self.assertIn(".kutu-bas:not(.hafif){--tema-odak:var(--tema-odak-koyu)}", KURAL)

    def test_kabuk_rol_degiskeni_okumuyor(self):
        """(d) Kabuk seçicileri `--tema-` rolüne bağlanmaz: kabuk `main`in
        dışında, ama kural kendisi de ham marka renginde kalmalı. Tek
        istisna odak halkasının kabukta BEYAZA sabitlenmesi."""
        # Kabuğun kökleri: servis şeridi, kategori bandı (ve içindeki arama,
        # menü), künye. `.servis-kunye` gibi İÇERİK sınıfları adı benzese de
        # kabuk değil — eşleşme sınıfın tamamıyla.
        kabuk = re.compile(r"^(\.servis|\.kategori|\.kategori-ic|\.kategori-liste|\.menu-dugme"
                           r"|\.tam-menu|\.menu-bolum|\.bant-logo|\.ara|\.ara-ac|\.ara-git"
                           r"|footer|\.kunye-[\w-]+|\.sosyal)(?![\w-])")
        for secici, govde in re.findall(r"([^{}]+)\{([^{}]*)\}", KURAL):
            secici = secici.strip()
            if not any(kabuk.match(s.strip()) for s in secici.split(",")):
                continue
            for kullanim in re.findall(r"var\((--tema-[\w-]+)\)", govde):
                self.fail(f"kabuk kuralı rol okuyor: {secici} → {kullanim}")

    def test_olu_degiskenler_silindi(self):
        for ad in ("--ak-zemin", "--saha", "--menu-bas", "--hv-damla", "--hv-zemin-alt"):
            self.assertNotRegex(KURAL, re.escape(ad) + r"\b", ad)

    def test_eski_bolum_duzenegi_donmedi(self):
        for iz in ("--bolum-vurgu", "--bolum-koyu", "--bolum-ak", "--bolum-cizgi", "--saglik"):
            self.assertNotIn(iz, KURAL, iz)
        self.assertFalse(hasattr(views, "BOLUM_TEMA"))
        self.assertFalse(hasattr(views, "ILCE_TEMA"))
        taban = (KOK / "sablonlar" / "taban.html").read_text(encoding="utf-8")
        self.assertNotIn("ana_nitelik", taban)
        # Nitelik kayıttan: şablonlarda slug'a bakan bir `data-bolum` yok.
        for yol in (KOK / "sablonlar").rglob("*.html"):
            metin = yol.read_text(encoding="utf-8")
            if "data-bolum=" in metin:
                self.assertEqual(yol.name, "taban.html", yol)
                self.assertIn('data-bolum="{{ tema.anahtar }}"', metin)


class TemaSayfalari(TestCase):
    """Görünüm temayı kayıttan basıyor; temasız sayfa düz `<body>`."""

    @classmethod
    def setUpTestData(cls):
        from django.core.management import call_command
        call_command("taksonomi_kur", verbosity=0)
        cls.ilce = Ilce.objects.first()
        tur = lambda s: KategoriTur.objects.filter(tur=Kategori.TUR_HABER, slug=s).first().kategori
        cls.ekonomi, cls.teknoloji, cls.bursa = tur("ekonomi"), tur("teknoloji"), tur("bursa")
        cls.gundem = tur("gundem")
        simdi = timezone.now()
        # Bir sayfadan fazla ulusal ekonomi haberi: Bursa haberi akışın
        # DIŞINDA kalsın ki listede görünsün.
        for n in range(views.SAYFA_BOYU + 2):
            Haber.objects.create(id=950100 + n, slug=f"eko-ulusal-{n}", baslik=f"Faiz kararı {n}",
                                 govde="<p>g</p>", kategori=cls.ekonomi,
                                 yayin_zamani=simdi - timezone.timedelta(hours=n + 1))
        # En yeni haber Bursa'yı anıyor ve kademede basılıyor: listede TEKRAR
        # etmemeli.
        Haber.objects.create(id=950000, slug="eko-bursa-yeni", baslik="Bursa'da fabrika açıldı",
                             govde="<p>g</p>", kategori=cls.ekonomi, yayin_zamani=simdi)
        Haber.objects.create(id=950001, slug="eko-bursa", baslik="BTSO ihracat rakamlarını açıkladı",
                             govde="<p>g</p>", kategori=cls.ekonomi,
                             yayin_zamani=simdi - timezone.timedelta(days=40))
        Haber.objects.create(id=950002, slug="tek-ulusal", baslik="Yeni telefon tanıtıldı",
                             govde="<p>g</p>", kategori=cls.teknoloji, yayin_zamani=simdi)
        Haber.objects.create(id=950003, slug="bursa-tek", baslik="Bursa'da yapay zeka atölyesi açıldı",
                             govde="<p>g</p>", kategori=cls.bursa,
                             yayin_zamani=simdi - timezone.timedelta(days=3))
        Haber.objects.create(id=950004, slug="bursa-baska", baslik="Bursa'da yol çalışması",
                             govde="<p>g</p>", kategori=cls.bursa, yayin_zamani=simdi)
        Haber.objects.create(id=950005, slug="gundem-0", baslik="Gündem haberi",
                             govde="<p>g</p>", kategori=cls.gundem, yayin_zamani=simdi)
        cls.yazar = Yazar.objects.create(id=990001, slug="deneme-yazar", ad="Deneme YAZAR")
        cls.yazi = KoseYazisi.objects.create(
            id=990101, slug="deneme-yazi", baslik="Kentin bekleyişi", spot="Kentin bekleyişi",
            yazar=cls.yazar, govde="<p>Gövde.</p>", yayin_zamani=simdi)

    def setUp(self):
        temalar._BELLEK.clear()

    def _govde(self, yol):
        yanit = self.client.get(yol)
        self.assertEqual(yanit.status_code, 200, yol)
        return yanit.content.decode()

    def test_nitelik_kayittan(self):
        for yol, beklenen in (("/ekonomi", "ekonomi"), ("/teknoloji", "teknoloji"),
                              ("/yazarlar", "kose"), (self.yazar.get_absolute_url(), "kose"),
                              (self.yazi.get_absolute_url(), "kose")):
            self.assertIn(f'<body data-bolum="{beklenen}">', self._govde(yol), yol)
        for yol in ("/gundem", "/bursa", f"/ilce/{self.ilce.slug}", "/"):
            metin = self._govde(yol)
            self.assertNotIn("data-bolum", metin, yol)
            self.assertIn("<body>", metin, yol)

    def test_ekonomi_bursa_listesi_kurali(self):
        """Ekonomi bölümünden Bursa'yı ananlar; ulusal haber listede yok."""
        metin = self._govde("/ekonomi")
        self.assertIn("BURSA EKONOMİSİ", metin)
        bolum = metin.split("BURSA EKONOMİSİ", 1)[1].split("</section>", 1)[0]
        self.assertNotIn("Faiz kararı", bolum)
        self.assertIn("BTSO ihracat rakamlarını açıkladı", bolum)
        # Sayfada zaten basılan haber listede tekrar etmez.
        self.assertEqual(metin.count("Bursa&#x27;da fabrika açıldı"), 1)
        self.assertNotIn("fabrika", bolum)
        self.assertIn("başlığında Bursa ya da BTSO geçen", bolum)

    def test_teknoloji_listesi_baska_bolumden_ve_bolumunu_soyluyor(self):
        metin = self._govde("/teknoloji")
        bolum = metin.split("BURSA'DA TEKNOLOJİ", 1)[1].split("</section>", 1)[0]
        self.assertIn("yapay zeka atölyesi", bolum)
        self.assertNotIn("yol çalışması", bolum)      # Bursa ama teknoloji değil
        self.assertNotIn("Yeni telefon", bolum)       # teknoloji ama Bursa değil
        self.assertIn('class="bolum-ad">Bursa<', bolum)

    def test_liste_bossa_yuva_cizilmiyor(self):
        Haber.objects.filter(pk=950003).delete()
        metin = self._govde("/teknoloji")
        self.assertNotIn("BURSA'DA TEKNOLOJİ", metin)
        self.assertNotIn("bursa-listesi", metin)

    def test_kose_sutun_basi_ve_tekrarsiz_spot(self):
        metin = self._govde(self.yazi.get_absolute_url())
        self.assertIn('class="gorus-bas"', metin)
        self.assertIn('class="gorus-ad"', metin)
        # Spot başlığın aynısı: ikinci kez basılmıyor.
        self.assertNotIn('class="spot"', metin)
        # Yazar afişi yazının üstüne basılmıyor.
        self.assertNotIn("ana-gorsel", metin)
        # Köşe adı (`unvan`) boş: satır yok.
        self.assertNotIn("gorus-kose", metin)
        self.assertEqual(metin.count("<h1"), 1)

    def test_yazar_sayfasi_h1_yazarin_adi(self):
        metin = self._govde(self.yazar.get_absolute_url())
        self.assertIn('<h1 id="yazar-bas">Deneme YAZAR</h1>', metin)
        self.assertEqual(metin.count("<h1"), 1)
        self.assertIn("gorus-liste", metin)
        self.assertIn("Kentin bekleyişi", metin)
