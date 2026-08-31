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

from django.test import TestCase, override_settings
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
        # Anasayfa 50 kayıt tüketiyor (15 manşet + 10 manşet listesi + 5
        # ikincil + 4 dörtlü + 11 kutu + 5 en çok); havuz dolsun.
        for n in range(56):
            tur = KategoriTur.objects.filter(
                tur=Kategori.TUR_HABER, slug="gundem").first()
            Haber.objects.create(
                id=700000 + n, slug=f"haber-{n}", baslik=f"Deneme başlığı {n}",
                spot=f"Deneme spotu {n}", govde=f"<p>Gövde {n}</p>",
                kategori=tur.kategori,
                ilce=cls.ilce if n % 2 == 0 else None,
                yayin_zamani=timezone.now())

    def test_anasayfa_bilesen_sayilari(self):
        """Manşet 15 slayt (30 Ağustos 2026); altındaki liste 10 başlık."""
        yanit = self.client.get("/")
        self.assertEqual(yanit.status_code, 200)
        icerik = yanit.content.decode()
        self.assertEqual(icerik.count('aria-roledescription="slayt"'), 15 + 5)
        self.assertEqual(len(yanit.context["manset"]), 15)
        self.assertEqual(len(yanit.context["manset_liste"]), 10)
        self.assertEqual(len(yanit.context["ikincil"]), 5)
        self.assertEqual(len(yanit.context["dortlu"]), 4)
        self.assertEqual(len(yanit.context["kutular"]), 11)

    def test_anasayfa_bloklari_ayni_haberi_tekrarlamiyor(self):
        """Manşet listesi de havuzun kendi dilimidir; hiçbir blokla kesişmez."""
        yanit = self.client.get("/")
        kimlikler = [h.id for anahtar in ("manset", "manset_liste", "ikincil",
                                          "dortlu", "kutular", "en_cok")
                     for h in yanit.context[anahtar]]
        self.assertEqual(len(kimlikler), len(set(kimlikler)))

    def test_manset_listesi_slayttan_sonraki_dilim(self):
        """§34 güvencesi sürüyor: en çok okunanlar manşetin kopyası değil."""
        yanit = self.client.get("/")
        manset = {h.id for h in yanit.context["manset"]}
        self.assertFalse(manset & {h.id for h in yanit.context["en_cok"]})
        self.assertFalse(manset & {h.id for h in yanit.context["manset_liste"]})

    def test_haber_detay(self):
        haber = Haber.objects.get(id=700000)
        yanit = self.client.get(haber.get_absolute_url())
        self.assertEqual(yanit.status_code, 200)
        self.assertContains(yanit, "Deneme başlığı 0")
        self.assertContains(yanit, "Gövde 0")

    def test_kategori_sayfasi(self):
        """Sayim VERIDEN turetilir: fikstur buyudugunde test kirilmasin,
        olcut "kategorideki tum yayindaki kayitlar listeleniyor mu"dur."""
        yanit = self.client.get("/gundem")
        self.assertEqual(yanit.status_code, 200)
        self.assertEqual(yanit.context["sayfa"].paginator.count,
                         Haber.yayindakiler().filter(
                             kategori__turler__slug="gundem").distinct().count())

    def test_ilce_sayfasi(self):
        yanit = self.client.get(f"/ilce/{self.ilce.slug}")
        self.assertEqual(yanit.status_code, 200)
        self.assertEqual(yanit.context["sayfa"].paginator.count,
                         Haber.yayindakiler().filter(ilce=self.ilce).count())

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


class ResmiIlanBolumu(TestCase):
    """Anasayfadaki RESMÎ İLANLAR bölümü — 29 Ağustos 2026 düzenlemesi.

    Bölüm eskiden şablona ELLE YAZILMIŞ altı `<li>` idi. Kayıtlar
    veritabanında dururken şablonda sabit metin olması, göç ilerledikçe
    yanlışlaşan bir bölüm demekti.
    """

    def setUp(self):
        from .models import ResmiIlan
        self.ResmiIlan = ResmiIlan
        import datetime
        ResmiIlan.objects.create(
            baslik="ARŞİVLENMİŞ İHALE KAYDI", tur=ResmiIlan.TUR_IHALE,
            yayin_tarihi=datetime.date(2026, 8, 24), durum=ResmiIlan.DURUM_ARSIV)
        ResmiIlan.objects.create(
            baslik="PASİF TEBLİGAT KAYDI", tur=ResmiIlan.TUR_TEBLIGAT,
            yayin_tarihi=datetime.date(2026, 8, 23), durum=ResmiIlan.DURUM_PASIF)
        ResmiIlan.objects.create(
            baslik="AKTİF TEBLİGAT KAYDI", tur=ResmiIlan.TUR_TEBLIGAT,
            yayin_tarihi=datetime.date(2026, 8, 22), durum=ResmiIlan.DURUM_AKTIF)

    def test_bolum_veritabanindan_ciziliyor(self):
        metin = self.client.get("/").content.decode()
        self.assertIn("ARŞİVLENMİŞ İHALE KAYDI", metin)
        self.assertIn("AKTİF TEBLİGAT KAYDI", metin)

    def test_pasif_kayit_yayimlanmaz(self):
        """Pasif = editörün yayından ÇEKTİĞİ kayıt; arşivden farklıdır.

        Arşiv "yayımlandı, güncelliğini yitirdi" demek ve bölümde kalır;
        ölçülen 24 kaydın 23'ü arşiv, biri pasif, hiçbiri aktif değil.
        `durum=AKTİF` süzgeci bölümü tamamen boşaltırdı.
        """
        self.assertNotIn("PASİF TEBLİGAT KAYDI",
                         self.client.get("/").content.decode())
        self.assertEqual(self.ResmiIlan.yayimlananlar().count(), 2)

    def test_dort_tur_de_gosterilir_sifir_olanlar_sonda(self):
        """§16: dört türün yasal karşılığı var, kayıt yoksa da gösterilir."""
        dagilim = self.ResmiIlan.tur_dagilimi(self.ResmiIlan.yayimlananlar())
        self.assertEqual(len(dagilim), 4)
        adetler = [t["adet"] for t in dagilim]
        self.assertEqual(adetler, sorted(adetler, reverse=True),
                         "kaydı olan türler önce gelmeli")
        bos = [t["anahtar"] for t in dagilim if t["adet"] == 0]
        self.assertEqual(set(bos), {"icra", "personel"})

    def test_olmayan_detay_sayfasina_bag_verilmez(self):
        """İlan metinleri göç etmedi; başlık `href="#"` ile bağ taklidi yapmaz."""
        metin = self.client.get("/").content.decode()
        bolum = metin[metin.index('id="resmi-ilan"'):]
        bolum = bolum[:bolum.index("</section>")]
        self.assertNotIn('href="#"', bolum)
        self.assertIn("/resmi-ilan", bolum)

    def test_uydurma_son_basvuru_tarihi_yok(self):
        """Kayıtların bitiş tarihi alanı boş; bölüm son başvuru vaat etmez."""
        bolum = (self.KOK if hasattr(self, "KOK") else Path(__file__).resolve().parent.parent)
        metin = (bolum / "sablonlar" / "anasayfa.html").read_text(encoding="utf-8")
        self.assertNotIn("bitis_tarihi", metin)

    def test_turkce_kucult_suzgeci_i_harfini_bozmuyor(self):
        """`|lower` "İHALE"yi "i̇hale" (i + U+0307) yapıyordu."""
        from .templatetags.site_etiket import kucult
        self.assertEqual(kucult("İHALE"), "ihale")
        self.assertEqual(kucult("TEBLİGAT"), "tebligat")
        self.assertNotIn("̇", kucult("İHALE"))


class BolumDurustlugu(TestCase):
    """Bölümlerin okura verdiği beyan veriyle uyumlu mu — 29 Ağustos 2026.

    İki bölüm denetimden geçti (URUN-PLANI.md §32). Buradaki testler
    denetimin vardığı kararları kilitler: bölüm notu şablona çakılı
    cümle taşımaz, resmî ilan bölümü "açık ilan listesi" gibi görünmez,
    Bursaspor listesi kartları tekrarlamaz.
    """

    KOK = Path(__file__).resolve().parent.parent

    @classmethod
    def setUpTestData(cls):
        from django.core.management import call_command
        call_command("taksonomi_kur", verbosity=0)

    def setUp(self):
        import datetime
        from .models import ResmiIlan
        self.ResmiIlan = ResmiIlan
        ResmiIlan.objects.create(
            baslik="ARŞİV İHALE", tur=ResmiIlan.TUR_IHALE,
            yayin_tarihi=datetime.date(2026, 8, 24), durum=ResmiIlan.DURUM_ARSIV)
        ResmiIlan.objects.create(
            baslik="ARŞİV TEBLİGAT", tur=ResmiIlan.TUR_TEBLIGAT,
            yayin_tarihi=datetime.date(2026, 8, 16), durum=ResmiIlan.DURUM_ARSIV)

    def _bolum(self, kimlik):
        metin = self.client.get("/").content.decode()
        bolum = metin[metin.index(f'id="{kimlik}"'):]
        return bolum[:bolum.index("</section>")]

    # -- resmî ilan --------------------------------------------------------

    def test_bos_tur_cumlesi_sablona_cakili_degil(self):
        """Not "İCRA ve PERSONEL ALIMI'nda ilan yok" cümlesini ELLE taşıyordu.

        Veri değişince not yalan söyleyecekti; boş türler dağılımdan
        okunuyor. İCRA kaydı eklendiğinde cümle kendiliğinden daralmalı.
        """
        sablon = (self.KOK / "sablonlar" / "anasayfa.html").read_text(encoding="utf-8")
        govde = re.sub(r"\{% comment %\}.*?\{% endcomment %\}", "", sablon, flags=re.S)
        self.assertNotIn("İCRA ve PERSONEL ALIMI", govde)

        self.assertIn("İCRA ve PERSONEL ALIMI", self._bolum("resmi-ilan"))
        import datetime
        self.ResmiIlan.objects.create(
            baslik="ARŞİV İCRA", tur=self.ResmiIlan.TUR_ICRA,
            yayin_tarihi=datetime.date(2026, 8, 20),
            durum=self.ResmiIlan.DURUM_ARSIV)
        yeni = self._bolum("resmi-ilan")
        self.assertNotIn("İCRA ve PERSONEL ALIMI", yeni)
        self.assertIn("PERSONEL ALIMI türünde yayımlanmış ilan yok", yeni)

    def test_bolum_acik_ilan_listesi_gibi_gorunmuyor(self):
        """Kayıtların tamamı arşiv ve `bitis_tarihi` boş.

        Okur "bunlar bugünün açık ihaleleri mi?" sorusunu satır satır
        tarihlere bakarak yanıtlıyordu. Bölüm başlığındaki dönem etiketi
        bunu ilk bakışta söylüyor.

        31 Ağustos 2026: notun uzun cümlesi bölümün altından kalktı,
        `/veri-kaynaklari` sayfasına taşındı. Beyan KAYBOLMADI — testin
        aradığı yer değişti, aranan cümle değil. İlanın kendi sayfası
        (`/resmi-ilan`) uyarıyı zaten kendi metniyle taşıyor ve bölümün
        TÜM İLANLAR bağlantısı oraya gidiyor.
        """
        bolum = self._bolum("resmi-ilan")
        self.assertIn('class="donem"', bolum)
        self.assertIn("16 Ağustos", bolum)
        self.assertIn("24 Ağustos 2026", bolum)
        self.assertIn("/resmi-ilan", bolum)

        for adres in ("/veri-kaynaklari", "/resmi-ilan"):
            self.assertContains(self.client.get(adres),
                                "açık ilanların listesi değil")

    def test_tek_tarihli_ilanda_donem_araligi_yazilmaz(self):
        self.ResmiIlan.objects.filter(baslik="ARŞİV TEBLİGAT").delete()
        bolum = self._bolum("resmi-ilan")
        self.assertIn("24 Ağustos 2026", bolum)
        self.assertNotIn("&ndash; 24 Ağustos 2026", bolum)

    # -- Bursaspor ---------------------------------------------------------

    def test_bursaspor_listesi_kartlari_tekrarlamiyor(self):
        """Liste kartların DEVAMIDIR; aynı haber iki kez görünmez.

        Liste, tam kadro tablonun açtığı 412 px'lik boşluğu kapatmak için
        var (URUN-PLANI.md §32); havuzu kartlarla ortak.
        """
        from .views import BURSASPOR, BURSASPOR_LISTE
        tur = KategoriTur.objects.filter(
            tur=Kategori.TUR_HABER, slug="bursaspor").first()
        for n in range(BURSASPOR + BURSASPOR_LISTE + 3):
            Haber.objects.create(
                id=810000 + n, slug=f"bs-{n}", baslik=f"Bursaspor başlığı {n}",
                spot="spot", govde="<p>gövde</p>", kategori=tur.kategori,
                yayin_zamani=timezone.now() - timezone.timedelta(hours=n))
        yanit = self.client.get("/")
        kart = [h.id for h in yanit.context["bursaspor_haberleri"]]
        liste = [h.id for h in yanit.context["bursaspor_liste"]]
        self.assertEqual(len(kart), BURSASPOR)
        self.assertEqual(len(liste), BURSASPOR_LISTE)
        self.assertEqual(set(kart) & set(liste), set())

    def test_kisa_zaman_yili_gizlemiyor(self):
        """Yılsız "31 Eki" 2025 haberini bu yılın haberi gibi gösteriyordu.

        Ölçüldü (29 Ağustos 2026): Bursaspor bölümündeki en yeni haber
        31 Ekim 2025 tarihli; arşiv taraması güncele yetişmedi.
        """
        from datetime import timedelta
        from .templatetags.site_etiket import kisa_zaman
        simdi = timezone.localtime()
        self.assertEqual(kisa_zaman(simdi), simdi.strftime("%H:%M"))
        gecen_yil = simdi.replace(year=simdi.year - 1)
        self.assertIn(str(simdi.year - 1), kisa_zaman(gecen_yil))
        self.assertEqual(kisa_zaman(None), "")


class ResmiIlanDizini(TestCase):
    """`/resmi-ilan` — anasayfadaki seçkinin DİZİN hâli (29 Ağustos 2026).

    Sayfa yer tutucuydu (`bekleyen.html`) ve anasayfadaki "TÜM İLANLAR"
    bağlantısı okuru boş bir sayfaya düşürüyordu. Buradaki testler dizinin
    seçkiden ayrıldığı üç noktayı kilitler — süzgecin adreste olması,
    sayıların arşivi sayması, listenin tamamının gelmesi — ve §32.5'in
    dersini sürdürür: okura verilen her olgu VERİDEN okunmalı, şablona
    çakılı olmamalı.
    """

    def _ilan(self, baslik, tur, gun, **fazla):
        import datetime
        from .models import ResmiIlan
        return ResmiIlan.objects.create(
            baslik=baslik, tur=tur, yayin_tarihi=datetime.date(2026, 8, gun),
            durum=fazla.pop("durum", ResmiIlan.DURUM_ARSIV), **fazla)

    def setUp(self):
        import datetime
        from .models import ResmiIlan
        self.ResmiIlan = ResmiIlan
        self._ilan("YENI IHALE KAYDI", ResmiIlan.TUR_IHALE, 24)
        self._ilan("ESKI IHALE KAYDI", ResmiIlan.TUR_IHALE, 3)
        self._ilan("TEBLIGAT KAYDI", ResmiIlan.TUR_TEBLIGAT, 2)
        self._ilan("PASIF KAYIT", ResmiIlan.TUR_IHALE, 20,
                   durum=ResmiIlan.DURUM_PASIF)
        # Temmuz kaydı: ay omurgasının iki başlık üretmesi için.
        ResmiIlan.objects.create(
            baslik="TEMMUZ TEBLIGATI", tur=ResmiIlan.TUR_TEBLIGAT,
            yayin_tarihi=datetime.date(2026, 7, 30),
            durum=ResmiIlan.DURUM_ARSIV)

    def _metin(self, adres="/resmi-ilan"):
        return self.client.get(adres).content.decode()

    # -- dizin seçki değil ------------------------------------------------
    def test_sayfa_yayimlanan_kayitlarin_tamamini_listeliyor(self):
        metin = self._metin()
        for baslik in ("YENI IHALE KAYDI", "ESKI IHALE KAYDI",
                       "TEBLIGAT KAYDI", "TEMMUZ TEBLIGATI"):
            self.assertIn(baslik, metin)
        self.assertNotIn("PASIF KAYIT", metin)

    def test_yer_tutucu_sablonu_kullanilmiyor(self):
        """`bekleyen.html` "henüz göç etmedi" diyor ve `noindex` basıyor."""
        yanit = self.client.get("/resmi-ilan")
        self.assertEqual([s.name for s in yanit.templates
                          if s.name == "bekleyen.html"], [])
        metin = yanit.content.decode()
        self.assertNotIn("göç etmedi", metin)
        self.assertNotIn("noindex", metin)

    def test_h1_ve_kanonik_adres_kurulu(self):
        metin = self._metin()
        self.assertEqual(metin.count("<h1"), 1)
        self.assertIn("<h1>RESMÎ İLANLAR</h1>", metin)
        self.assertIn("<title>Resmî ilanlar — Bursa Hakimiyet</title>", metin)
        self.assertIn('rel="canonical"', metin)

    def test_suzgec_adresi_kanonikte_gorunmuyor(self):
        """`?tur=…` bir sayfa değil, dizinin kesiti: kanonik dizini gösterir."""
        metin = self._metin("/resmi-ilan?tur=ihale")
        kanonik = re.search(r'rel="canonical" href="([^"]+)"', metin).group(1)
        self.assertTrue(kanonik.endswith("/resmi-ilan"), kanonik)

    # -- süzgeç adreste ---------------------------------------------------
    def test_tur_suzgeci_adres_satirindan_calisiyor(self):
        metin = self._metin("/resmi-ilan?tur=tebligat")
        self.assertIn("TEBLIGAT KAYDI", metin)
        self.assertIn("TEMMUZ TEBLIGATI", metin)
        self.assertNotIn("YENI IHALE KAYDI", metin)
        self.assertIn('href="/resmi-ilan?tur=ihale"', metin)
        self.assertIn('href="/resmi-ilan?tur=tebligat" aria-current="true"',
                      metin)

    def test_tanimsiz_tur_hata_vermiyor_dizine_dusuyor(self):
        """Adres satırından gelen bozuk süzgeç okura 404 göstermez."""
        for adres in ("/resmi-ilan?tur=uydurma", "/resmi-ilan?tur="):
            yanit = self.client.get(adres)
            self.assertEqual(yanit.status_code, 200)
            self.assertIn("YENI IHALE KAYDI", yanit.content.decode())

    def test_kaydi_olmayan_tur_baglanti_degil(self):
        """Boş listeye götüren bağlantı, bağlantı değildir (§16 dört tür)."""
        metin = self._metin()
        self.assertIn("PERSONEL ALIMI", metin)
        self.assertIn('<span class="tur icra bos"', metin)
        self.assertNotIn('href="/resmi-ilan?tur=icra"', metin)

    def test_suzgec_sayilari_sayfayi_degil_arsivi_sayiyor(self):
        """Anasayfada sayı SAYFAYI sayar (tıklama sayfayı süzer); dizinde
        tıklama arşivi süzdüğü için sayı da arşivi saymalı."""
        from .views import ILAN_SAYFA_BOYU
        for n in range(ILAN_SAYFA_BOYU + 5):
            self._ilan("TOPLU IHALE %d" % n, self.ResmiIlan.TUR_IHALE, 10)
        metin = self._metin()
        toplam = self.ResmiIlan.yayimlananlar().count()
        self.assertGreater(toplam, ILAN_SAYFA_BOYU)
        self.assertIn('>TÜMÜ <span class="adet">%d</span>' % toplam, metin)
        # Aynı sayfada listelenen satır sayısı sayfa boyuyla sınırlı.
        self.assertEqual(metin.count('class="ilan-govde"'), ILAN_SAYFA_BOYU)

    def test_sayfalama_suzgeci_koruyor(self):
        from .views import ILAN_SAYFA_BOYU
        for n in range(ILAN_SAYFA_BOYU + 5):
            self._ilan("TOPLU IHALE %d" % n, self.ResmiIlan.TUR_IHALE, 10)
        metin = self._metin("/resmi-ilan?tur=ihale")
        self.assertIn("tur=ihale&amp;sayfa=2", metin)

    def test_tur_dagilimi_iki_yolda_da_ayni(self):
        """Dizin sayımı veritabanına bırakıyor, anasayfa listeden sayıyor."""
        sorgu = self.ResmiIlan.yayimlananlar()
        self.assertEqual(self.ResmiIlan.tur_dagilimi(sorgu),
                         self.ResmiIlan.tur_dagilimi(list(sorgu)))

    # -- ay omurgası ------------------------------------------------------
    def test_ay_basliklari_veriden_geliyor(self):
        metin = self._metin()
        self.assertIn('id="ay-2026-08"', metin)
        self.assertIn('id="ay-2026-07"', metin)
        self.assertIn("AĞUSTOS 2026", metin)
        self.assertIn("TEMMUZ 2026", metin)
        self.assertLess(metin.index("AĞUSTOS 2026"), metin.index("TEMMUZ 2026"))
        # Ağustos'ta 3, Temmuz'da 1 kayıt var.
        self.assertIn('<span class="adet">3 ilan</span>', metin)
        self.assertIn('<span class="adet">1 ilan</span>', metin)

    def test_tarihsiz_kayit_kendi_grubunda_ve_sonda(self):
        """`yayin_tarihi` boş olabiliyor; ay omurgası bunu kırmamalı."""
        self.ResmiIlan.objects.create(
            baslik="TARIHSIZ KAYIT", tur=self.ResmiIlan.TUR_IHALE,
            yayin_tarihi=None, durum=self.ResmiIlan.DURUM_ARSIV)
        metin = self._metin()
        self.assertIn("Yayın tarihi kayıtlı olmayanlar", metin)
        self.assertLess(metin.index("TEMMUZ 2026"),
                        metin.index("Yayın tarihi kayıtlı olmayanlar"))

    def test_donem_etiketi_suzulen_kumeden_okunuyor(self):
        self.assertIn("30 Temmuz &ndash; 24 Ağustos 2026", self._metin())
        # Tek güne düşen süzgeçte aralık yazılmaz.
        self.ResmiIlan.objects.filter(tur=self.ResmiIlan.TUR_TEBLIGAT).delete()
        self.ResmiIlan.objects.filter(baslik="ESKI IHALE KAYDI").delete()
        metin = self._metin("/resmi-ilan?tur=ihale")
        self.assertIn('<span class="donem">24 Ağustos 2026</span>', metin)

    # -- dürüstlük çizgisi ------------------------------------------------
    def test_olu_baglanti_ve_baslik_bagi_yok(self):
        """İlan metni göç etmedi; başlık bağ taklidi yapmaz."""
        metin = self._metin()
        bolum = metin[metin.index('class="kutu ilan-dizin"'):]
        bolum = bolum[:bolum.index("</section>")]
        self.assertNotIn('href="#"', bolum)
        self.assertNotIn('<a class="ilan-adi"', bolum)

    def test_son_basvuru_cumlesi_veriden_geliyor(self):
        """Cümle şablona çakılı olsaydı bitiş tarihi gelince yalan söylerdi."""
        import datetime
        self.assertIn("Son başvuru tarihi gösterilmez", self._metin())
        kayit = self.ResmiIlan.objects.get(baslik="YENI IHALE KAYDI")
        kayit.bitis_tarihi = datetime.date(2026, 9, 10)
        kayit.save(update_fields=["bitis_tarihi"])
        self.assertNotIn("Son başvuru tarihi gösterilmez", self._metin())

    def test_ilan_metni_cumlesi_veriden_geliyor(self):
        self.assertIn("arşiv dökümünde yok", self._metin())
        kayit = self.ResmiIlan.objects.get(baslik="YENI IHALE KAYDI")
        kayit.metin = "İhale ilanının tam metni."
        kayit.save(update_fields=["metin"])
        metin = self._metin()
        self.assertNotIn("arşiv dökümünde yok", metin)
        self.assertIn("tek tek ilan sayfaları henüz açılmadı", metin)

    def test_bos_tur_cumlesi_veriden_geliyor(self):
        self.assertIn("İCRA ve PERSONEL ALIMI türünde yayımlanmış ilan yok",
                      self._metin())
        self._ilan("ICRA KAYDI", self.ResmiIlan.TUR_ICRA, 12)
        metin = self._metin()
        self.assertIn("PERSONEL ALIMI türünde yayımlanmış ilan yok", metin)
        self.assertNotIn("İCRA ve PERSONEL ALIMI türünde", metin)

    def test_kayit_yokken_sayfa_ayakta_kaliyor(self):
        self.ResmiIlan.objects.all().delete()
        yanit = self.client.get("/resmi-ilan")
        self.assertEqual(yanit.status_code, 200)
        self.assertIn("Yayımlanabilir resmî ilan kaydı yok.",
                      yanit.content.decode())


class ReklamDemoAgi(TestCase):
    """Reklam demo ağı (31 Ağustos 2026, §42).

    Üç şey kilitleniyor: bayrak kapalıyken dış betik YOK, açıkken var, ve
    üst şerit dar ekranda hiçbir yaratıcı istemiyor (sayfa 360 px'te 393 px
    yatay taşıyordu — ölçüldü, `data-gpt-harita` bunun için var).
    """

    KOK = Path(__file__).resolve().parent.parent

    @classmethod
    def setUpTestData(cls):
        from django.core.management import call_command
        call_command("taksonomi_kur", verbosity=0)

    def test_bayrak_kapaliyken_dis_betik_yok(self):
        """Varsayılan kapalı: site dışarıdan yalnız Google Fonts çeker."""
        with override_settings(REKLAM_DEMO=False):
            yanit = self.client.get("/")
        self.assertNotContains(yanit, "securepubads")
        self.assertNotContains(yanit, "betik/reklam.js")

    def test_bayrak_acikken_gpt_basiliyor(self):
        with override_settings(REKLAM_DEMO=True):
            yanit = self.client.get("/")
        self.assertContains(yanit, "securepubads.g.doubleclick.net/tag/js/gpt.js")
        self.assertContains(yanit, "betik/reklam.js")
        self.assertContains(yanit, "/6355419/")

    def test_yuvalar_olculeriyle_isaretli(self):
        """Yuva ölçüsü İŞARETTE durur; betik ölçü listesi taşımaz."""
        with override_settings(REKLAM_DEMO=True):
            metin = self.client.get("/").content.decode()
        # iki pageskin + üst şerit + üç kare
        self.assertEqual(metin.count('data-gpt="160x600"'), 2)
        self.assertEqual(metin.count('data-gpt="300x250"'), 3)
        # Üst şerit üç ölçü taşır: 1100x150 gazetenin kendi sattığı yuva,
        # 970x250 programatik billboard, 728x90 yedek.
        self.assertIn('data-gpt="1100x150,970x250,728x90"', metin)

    def test_ust_serit_haritasi_dar_ekrani_koruyor(self):
        """Üç ölçülmüş kısıt: kutu boyu 44 · 120 · 250 px, sütun 1100 px.

        ≤600 px'te kutu 44 px (§34 K8) — 728x90 oraya konunca sayfa 360'ta
        393 px yatay taşıyordu. 601-1000'de kutu 120 px, 250'lik yaratıcı
        sığmaz. 1001-1139'da kutu 250 ama içerik sütunu henüz 1100 değil,
        o yüzden 1100 genişliğindeki yaratıcı orada da verilmez.
        """
        with override_settings(REKLAM_DEMO=True):
            metin = self.client.get("/").content.decode()
        harita = re.search(r'data-gpt-harita="([^"]*)"', metin)
        self.assertIsNotNone(harita, "üst şeridin görünüm haritası yok")
        girisler = dict(
            (int(p.split(">")[0].strip()), p.split(">")[1].strip())
            for p in harita.group(1).split(";") if ">" in p)
        self.assertEqual(girisler[0], "", "dar ekranda ölçü verilmiş")
        # 601-1000: kutu 120 px, yalnız 728x90 sığar.
        self.assertEqual(girisler[601], "728x90")
        # 1001-1139: kutu 250 px ama sütun henüz 1100 değil.
        self.assertIn("970x250", girisler[1001])
        self.assertNotIn("1100x150", girisler[1001],
                         "1100 px yaratıcı 1100 px'lik sütuna sığmadan veriliyor")
        self.assertIn("1100x150", girisler[1140])

    def test_ust_serit_demo_reklami_almiyor(self):
        """Ölçü sözleşmesi işarette kalır, demo yaratıcısı basılmaz.

        Demo ağı üç ölçüden yalnız 728x90'ı dolduruyor ve o yaratıcı
        250 px'lik billboard kutusunda şeridin gerçek hâlini göstermiyordu
        (31 Ağustos 2026 kullanıcı kararı). Kalkan tek şey demo dolgusu —
        `data-gpt` ve harita yerinde, F7 geldiğinde yeniden yazılmasın.
        """
        with override_settings(REKLAM_DEMO=True):
            metin = self.client.get("/").content.decode()
        serit = metin[metin.index('class="reklam tam"'):]
        serit = serit[:serit.index("</div>")]
        self.assertIn('data-gpt-demo="kapali"', serit)
        self.assertIn("1100x150", serit)
        # İşaret YALNIZ üst şeritte; kareler ve pageskin'ler demo alır.
        self.assertEqual(metin.count('data-gpt-demo="kapali"'), 1)

        betik = (self.KOK / "statik" / "betik" / "reklam.js").read_text(
            encoding="utf-8")
        self.assertIn("data-gpt-demo", betik)

    def test_ornek_yaratici_yalniz_demoda_basiliyor(self):
        """970x250 maketi bir SUNUM aracıdır; yayında hiç üretilmez.

        Demo ağında 970x250 yaratıcı yok (ölçüldü), o yüzden formatın ayak
        izi yerel bir maketle gösteriliyor. Bayrak kapalıyken bu blok
        şablondan hiç çıkmamalı — yoksa okur onu reklam sanır.
        """
        with override_settings(REKLAM_DEMO=False):
            self.assertNotContains(self.client.get("/"), "ornek-yaratici")
        with override_settings(REKLAM_DEMO=True):
            metin = self.client.get("/").content.decode()
        self.assertIn("ornek-yaratici", metin)
        self.assertIn("ÖRNEK YARATICI", metin)
        # Maket reklam gibi görünmemeli: marka ya da reklamveren adı yok.
        self.assertIn("billboard ayak izi", metin)

    def test_betik_reklam_anahtarina_uyuyor(self):
        """Panolar gizliyken reklam ÇEKİLMEZ; yoksa düğme yalan söyler."""
        betik = (self.KOK / "statik" / "betik" / "reklam.js").read_text(
            encoding="utf-8")
        self.assertIn("data-reklam", betik)
        self.assertIn("offsetParent === null", betik)

