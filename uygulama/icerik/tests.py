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
from .temizle import govde_temizle, metin_duzelt
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


class DuzMetinOnarimi(TestCase):
    """`temizle.metin_duzelt` — arşivin başlık/spot artıkları (5 Eylül 2026).

    Örnekler uydurma değil: hepsi arşivden alındı.
    """

    def test_cozulmemis_varlik_kacisi(self):
        self.assertEqual(metin_duzelt("Ug&#774;ur Aslan'dan eşiyle pozu"),
                         "Uğur Aslan'dan eşiyle pozu")
        self.assertEqual(
            metin_duzelt("19 Mayıs Atatu&#776;rk'u&#776; Anma"),
            "19 Mayıs Atatürk'ü Anma")

    def test_ayrismis_harf_nfc_ile_birlesiyor(self):
        """Ekranda ü gibi görünür ama aramada başka bir dizidir."""
        self.assertEqual(metin_duzelt("Atatürk"), "Atatürk")

    def test_kucultmeden_kalan_nokta_dusuyor(self):
        """NFC "i" + U+0307'yi birleştirmez; artık okunurluğu bozuyordu."""
        self.assertEqual(metin_duzelt("Rus ve İngi̇liz gemileri"),
                         "Rus ve İngiliz gemileri")

    def test_gorunmez_karakterler_siliniyor(self):
        self.assertEqual(metin_duzelt("​​Yerel basının nabzı"),
                         "Yerel basının nabzı")

    def test_bosluk_varsayilan_olarak_daraltilmiyor(self):
        """Bu işlev bozulmayı onarır, metni yeniden biçimlendirmez."""
        self.assertEqual(metin_duzelt("iki  boşluk "), "iki  boşluk ")
        self.assertEqual(metin_duzelt("dar boşluk", bosluk=True),
                         "dar boşluk")

    def test_saglam_metin_degismiyor(self):
        for saglam in ("Bursa'da yeni hat açıldı", "TOFAŞ & Fiat anlaşması",
                       "Nilüfer Çayı için büyük adım"):
            self.assertEqual(metin_duzelt(saglam), saglam)

    def test_kendini_tekrar_ettiginde_degistirmiyor(self):
        """Komut iki kez çalışabilir; ikinci tur veriye dokunmamalı."""
        bir = metin_duzelt("Ug&#774;ur &amp; Ali​")
        self.assertEqual(metin_duzelt(bir), bir)


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

    def test_canli_veri_beyani_dogru_ve_ulasilabilir(self):
        """Okura verilen kaynak beyanı doğru olmalı ve künyeden ulaşılmalı.

        27 Ağustos: altı kalemin beşi canlı kaynağa bağlandı, künye hâlâ
        "hiçbiri bağlanmadı" diyordu; koruma o zaman künye şablonuna
        kondu.

        3 Eylül 2026: beyan metni kullanıcı isteğiyle künyeden çıkarıldı ve
        yalnız `/veri-kaynaklari` sayfasında kaldı. Korumanın AMACI aynı —
        yanlış beyan bırakılmaz, beyan erişilebilir kalır — o yüzden test
        silinmedi, beyanın yeni yerine taşındı.

        TCMB burada aranmıyor: döviz kaynağı şablona yazılı değil, canlı
        veri dosyasındaki künyeden geliyor (`_canli_kunyeler`), yani
        şablon metninde hiç geçmez.
        """
        kunye = (self.KOK / "sablonlar" / "parca" / "kunye.html").read_text(encoding="utf-8")
        beyan = (self.KOK / "sablonlar" / "veri_kaynaklari.html").read_text(encoding="utf-8")

        # 1. Künye yanlış ya da bayat beyan taşımaz.
        for yanlis in ("henüz canlı kaynağa bağlanmamıştır", "Wikimedia Commons"):
            self.assertNotIn(yanlis, kunye)
            self.assertNotIn(yanlis, beyan)

        # 2. Beyan sayfası kaynakları adıyla söyler.
        for kaynak in ("MGM", "TFF", "Diyanet"):
            self.assertIn(kaynak, beyan)

        # 3. Beyan künyeden bir tık uzakta ve sayfa ayakta.
        self.assertIn('href="/veri-kaynaklari"', kunye)
        self.assertEqual(self.client.get("/veri-kaynaklari").status_code, 200)


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

    def test_bursaspor_kartlari_tekrarsiz_ve_yeniden_eskiye(self):
        """Bölüm 3x3 ızgara: dokuz kart, tekrarsız, en yeniden eskiye.

        6 Eylül 2026'da kartların altındaki "SON GELİŞMELER" listesi
        kaldırıldı ve `BURSASPOR` 6 -> 9 oldu; bu test o listenin
        tekrarsızlık kontrolünün yerini alıyor. Bağlamda `bursaspor_liste`
        ARTIK YOK — şablon da onu aramıyor.
        """
        from .views import BURSASPOR
        tur = KategoriTur.objects.filter(
            tur=Kategori.TUR_HABER, slug="bursaspor").first()
        for n in range(BURSASPOR + 3):
            Haber.objects.create(
                id=810000 + n, slug=f"bs-{n}", baslik=f"Bursaspor başlığı {n}",
                spot="spot", govde="<p>gövde</p>", kategori=tur.kategori,
                yayin_zamani=timezone.now() - timezone.timedelta(hours=n))
        yanit = self.client.get("/")
        kart = [h.id for h in yanit.context["bursaspor_haberleri"]]
        self.assertEqual(len(kart), BURSASPOR)
        self.assertEqual(len(set(kart)), BURSASPOR)
        self.assertNotIn("bursaspor_liste", yanit.context)
        zamanlar = [h.yayin_zamani for h in yanit.context["bursaspor_haberleri"]]
        self.assertEqual(zamanlar, sorted(zamanlar, reverse=True))

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

    def test_goreli_zaman_taze_haberde_ne_kadar_once_yaziyor(self):
        """SON DAKİKA rayının damgası (2 Eylül 2026, §44).

        Kutuda okurun sorduğu soru "kaçta" değil "ne kadar yeni" —
        incelenen sitelerin hepsi (BBC, Spiegel, CNN Türk) burada göreli
        zaman yazıyor. Sınır 24 saat: ötesinde `kisa_zaman`a düşer, yoksa
        arşivdeki kayıt "1.437 saat önce" olurdu.
        """
        from datetime import timedelta
        from .templatetags.site_etiket import goreli_zaman, kisa_zaman
        simdi = timezone.now()
        self.assertEqual(goreli_zaman(simdi - timedelta(seconds=20)), "şimdi")
        self.assertEqual(goreli_zaman(simdi - timedelta(minutes=14)), "14 dk önce")
        self.assertEqual(goreli_zaman(simdi - timedelta(hours=3)), "3 saat önce")
        eski = simdi - timedelta(days=40)
        self.assertEqual(goreli_zaman(eski), kisa_zaman(eski))
        self.assertEqual(goreli_zaman(None), "")
        # İleri tarihli kayıtta negatif dakika basılmaz.
        self.assertEqual(goreli_zaman(simdi + timedelta(minutes=5)), "şimdi")

    def test_son_dakika_serit_manseti_listede_tekrarlamiyor(self):
        """En yeni kalem ŞERİTTE, liste ondan sonrakilerle başlar (§44).

        Panelin en yeni haberi hem kırmızı şeride hem listeye basılsaydı
        okur aynı başlığı iki kez okurdu; `SON_DAKIKA_ADET` de bu yüzden
        yediye çıktı (listede altı kalem = iki sütunda üç tam satır).
        """
        from .baglam import SON_DAKIKA_ADET
        tur = KategoriTur.objects.filter(
            tur=Kategori.TUR_HABER, slug="bursaspor").first()
        for n in range(SON_DAKIKA_ADET + 2):
            Haber.objects.create(
                id=830000 + n, slug=f"sd-{n}", baslik=f"Son dakika başlığı {n}",
                spot="spot", govde="<p>gövde</p>", kategori=tur.kategori,
                yayin_zamani=timezone.now() - timezone.timedelta(minutes=n))
        yanit = self.client.get("/")
        metin = yanit.content.decode()
        panel = metin[metin.index('id="son-dakika"'):]
        panel = panel[:panel.index("</ul>")]
        ayrac = panel.index('<div class="kutu-ic"')
        serit, liste = panel[:ayrac], panel[ayrac:]
        en_yeni = yanit.context["son_dakika"][0]
        self.assertIn(buyult(en_yeni.baslik), serit)
        self.assertNotIn(en_yeni.baslik, liste)
        self.assertEqual(liste.count("<li>"), SON_DAKIKA_ADET - 1)

    def test_ilceler_bandi_dizine_degil_osmangaziye_gidiyor(self):
        """2 Eylül 2026, §47 — kullanıcı isteği.

        Bant kalemi dizine gidince okur ilçe haberine iki tıklamada
        ulaşıyordu; ilçe sayfası artık 17 ilçelik hızlı geçiş şeridini
        taşıyor (§46), yani dizinin işini de görüyor. Dizin KALDIRILMADI:
        tam menüdeki "Tüm ilçeler" oraya gitmeye devam ediyor.
        """
        from .baglam import VARSAYILAN_ILCE
        govde = self.client.get("/").content.decode()
        bant = govde[govde.index('class="kategori-liste"'):]
        # Bant listesinin kendisi: ilk `</div>`e kadar. `</nav>` çok
        # sonra kapanıyor ve tam menüyü de içine alıyordu.
        bant = bant[:bant.index("</div>")]
        self.assertIn(f'href="/ilce/{VARSAYILAN_ILCE}"', bant)
        self.assertNotIn('href="/ilceler"', bant)
        # Dizin adresi menüde duruyor; sayfa da ayakta.
        self.assertIn('href="/ilceler"', govde)
        self.assertEqual(self.client.get("/ilceler").status_code, 200)

    def test_bolum_en_cok_seridi_sayfadaki_haberleri_tekrarlamiyor(self):
        """Bölüme özel "EN ÇOK OKUNANLAR" (2 Eylül 2026, §47).

        Okunma sayacı yok (§4, madde 8); şerit listenin DEVAMINDAN
        besleniyor. Kilitlenen şey seçimin sayfayla çakışmaması — aynı
        başlığın sayfada iki kez görünmesi kutuyu anlamsız kılardı.
        """
        from .views import KATEGORI_EN_COK, SAYFA_BOYU
        tur = KategoriTur.objects.filter(
            tur=Kategori.TUR_HABER, slug="bursaspor").first()
        for n in range(SAYFA_BOYU + KATEGORI_EN_COK + 2):
            Haber.objects.create(
                id=840000 + n, slug=f"ec-{n}", baslik=f"Bölüm başlığı {n}",
                spot="spot", govde="<p>gövde</p>", kategori=tur.kategori,
                yayin_zamani=timezone.now() - timezone.timedelta(minutes=n))
        yanit = self.client.get("/bursaspor")
        en_cok = yanit.context["en_cok"]
        sayfadakiler = {h.id for h in yanit.context["sayfa"]}
        self.assertEqual(len(en_cok), KATEGORI_EN_COK)
        self.assertEqual({h.id for h in en_cok} & sayfadakiler, set())
        # Şerit o BÖLÜME ait: başka kategoriden kayıt sızmaz.
        for h in en_cok:
            self.assertEqual(h.kategori_id, tur.kategori_id)
        self.assertIn("BU BÖLÜMDE EN ÇOK OKUNANLAR",
                      yanit.content.decode())


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


class YerelTestReklami(TestCase):
    """Yerel test reklam hizmeti (7 Eylül 2026, kullanıcı isteği).

    Dört şey kilitleniyor: kapı (sıradan ziyaretçi göremez), ölçü (istenen
    ölçüde yaratıcı gerçekten üretiliyor), dışa bağımsızlık (yaratıcıda
    dış adres yok) ve yaratıcının reklam gibi görünmemesi.
    """

    KOK = Path(__file__).resolve().parent.parent

    @classmethod
    def setUpTestData(cls):
        from django.contrib.auth.models import User
        from django.core.management import call_command
        call_command("taksonomi_kur", verbosity=0)
        cls.personel = User.objects.create_user(
            "sunumcu", password="x", is_staff=True)

    def test_siradan_ziyaretci_goremez(self):
        """Kapı sunum oturumu: anonim ziyaretçi 404 alır.

        Canlıda bir okurun yuvasına test görseli düşmesi bu yüzden
        mümkün değil — adres de düğme de betik de yok.
        """
        self.assertEqual(
            self.client.get("/reklam/test/300x250.svg").status_code, 404)
        metin = self.client.get("/").content.decode()
        self.assertNotIn("betik/reklam-test.js", metin)
        self.assertNotIn("reklam-test-anahtar", metin)

    def test_sunum_oturumunda_yaratici_uretiliyor(self):
        self.client.force_login(self.personel)
        yanit = self.client.get("/reklam/test/300x250.svg")
        self.assertEqual(yanit.status_code, 200)
        self.assertIn("image/svg+xml", yanit["Content-Type"])
        svg = yanit.content.decode()
        self.assertIn('width="300"', svg)
        self.assertIn('height="250"', svg)
        self.assertIn("TEST REKLAMI", svg)

    def test_yaratici_disariya_baglanmiyor(self):
        """Sayfanın internetsiz açılması kuralı yaratıcıda da geçerli."""
        self.client.force_login(self.personel)
        svg = self.client.get("/reklam/test/970x250.svg").content.decode()
        for iz in ("http://", "https://", "//cdn", "url("):
            if iz == "https://":
                # Tek izinli mutlak adres SVG ad alanıdır.
                self.assertEqual(svg.count(iz), 0)
                continue
            self.assertNotIn(iz, svg.replace(
                "http://www.w3.org/2000/svg", ""))

    def test_yaratici_reklam_taklidi_degil(self):
        """Marka yok, reklamveren yok: üstünde ne olduğu yazıyor."""
        self.client.force_login(self.personel)
        svg = self.client.get(
            "/reklam/test/728x90.svg?yuva=Haber arası1").content.decode()
        self.assertIn("TEST", svg)
        self.assertIn("Haber arası1", svg)

    def test_yuva_adi_kacisli_basiliyor(self):
        """Etiket adresten geliyor; ham basılırsa SVG'ye betik girerdi."""
        self.client.force_login(self.personel)
        svg = self.client.get(
            "/reklam/test/300x250.svg?yuva=%3Cscript%3E").content.decode()
        self.assertNotIn("<script>", svg)
        self.assertIn("&lt;script&gt;", svg)

    def test_olcu_sinirlari(self):
        self.client.force_login(self.personel)
        self.assertEqual(
            self.client.get("/reklam/test/10x10.svg").status_code, 404)
        self.assertEqual(
            self.client.get("/reklam/test/3000x3000.svg").status_code, 404)

    def test_sayfa_betigi_yalniz_sunum_oturumunda(self):
        self.client.force_login(self.personel)
        metin = self.client.get("/").content.decode()
        self.assertIn("betik/reklam-test.js", metin)
        self.assertIn("reklam-test-anahtar", metin)
        self.assertIn("BH_REKLAM_TEST_KOK", metin)

    def test_bayrak_kapaliyken_hicbir_sey_basilmiyor(self):
        """`BH_REKLAM_TEST=0` hizmeti tümden kapatır."""
        self.client.force_login(self.personel)
        with override_settings(REKLAM_TEST=False):
            metin = self.client.get("/").content.decode()
        self.assertNotIn("betik/reklam-test.js", metin)
        self.assertNotIn("reklam-test-anahtar", metin)

    def test_rozet_yazisi_zemine_gore_seciliyor(self):
        """Vurgu rengi her palette koyu değil; sabit beyaz rozet kaybolur.

        Saha yeşili paletinde vurgu açık yeşil (#EAF4EE) ve "TEST" rozeti
        beyaz yazıyla görünmüyordu — ölçüldü, renk artık parlaklıktan.
        """
        from .reklam import _okunur_yazi
        self.assertEqual(_okunur_yazi("#EAF4EE"), "#14181D")
        self.assertEqual(_okunur_yazi("#E4222B"), "#FFFFFF")
        self.assertEqual(_okunur_yazi("#1B2A6B"), "#FFFFFF")

    def test_betik_demo_agiyla_carpismiyor(self):
        """İki bayrak birlikte açıkken aynı kutuda iki reklam olmaz."""
        betik = (self.KOK / "statik" / "betik" / "reklam-test.js").read_text(
            encoding="utf-8")
        self.assertIn("gpt-yuva", betik)
        self.assertIn("adsbygoogle", betik)
        self.assertIn("data-reklam-test", betik)
        # Görünmeyen yuva kuralı ortak parçaya taşındı (§66).
        ortak = (self.KOK / "statik" / "betik" / "reklam-olcu.js").read_text(
            encoding="utf-8")
        self.assertIn("offsetParent === null", ortak)


class AdSenseKendiKimligi(TestCase):
    """AdSense — gazetenin kendi yayıncı kimliği (7 Eylül 2026, §66).

    Dört kapı kilitleniyor: kimlik yokken hiçbir dış betik basılmaz, test
    modu okura çizilmez, gerçek yayında herkese çizilir, ads.txt kimlikten
    üretilir.
    """

    KOK = Path(__file__).resolve().parent.parent
    KIMLIK = "ca-pub-0000000000000000"

    @classmethod
    def setUpTestData(cls):
        from django.contrib.auth.models import User
        from django.core.management import call_command
        call_command("taksonomi_kur", verbosity=0)
        cls.personel = User.objects.create_user(
            "reklamci", password="x", is_staff=True)

    def test_kimlik_yokken_dis_betik_yok(self):
        """Varsayılan: kimlik boş, site dışarıdan yalnız Google Fonts çeker."""
        self.client.force_login(self.personel)
        with override_settings(ADSENSE_ID=""):
            metin = self.client.get("/").content.decode()
        self.assertNotIn("adsbygoogle", metin)
        self.assertNotIn("pagead2.googlesyndication.com", metin)

    def test_test_modu_yalniz_sunum_oturumunda(self):
        """Test yaratıcısı okura gösterilecek şey değil.

        `data-adtest="on"` gösterim saymaz ama ekranda reklam görünür;
        sıradan ziyaretçiye çizilirse okur onu gerçek reklam sanar.
        """
        with override_settings(ADSENSE_ID=self.KIMLIK, ADSENSE_TEST=True,
                               ADSENSE_SLOT="1234567890"):
            anonim = self.client.get("/").content.decode()
            self.client.force_login(self.personel)
            sunum = self.client.get("/").content.decode()
        self.assertNotIn("adsbygoogle", anonim)
        self.assertIn("adsbygoogle.js?client=ca-pub-0000000000000000", sunum)
        self.assertIn("betik/reklam-adsense.js", sunum)
        self.assertIn("betik/reklam-olcu.js", sunum)

    def test_gercek_yayinda_herkese_ciziliyor(self):
        """Test kapatıldığında kapı da kalkar — asıl yayın hâli budur."""
        with override_settings(ADSENSE_ID=self.KIMLIK, ADSENSE_TEST=False,
                               ADSENSE_SLOT="1234567890"):
            metin = self.client.get("/").content.decode()
        self.assertIn("adsbygoogle", metin)

    def test_ayar_json_script_ile_gomuluyor(self):
        """Kimlik ve birim numaraları betiğe kaçışlı geçmeli."""
        self.client.force_login(self.personel)
        with override_settings(ADSENSE_ID=self.KIMLIK, ADSENSE_TEST=True,
                               ADSENSE_SLOT="1234567890",
                               ADSENSE_YUVALAR={"Manşet yanı": "999"}):
            metin = self.client.get("/").content.decode()
        self.assertIn('id="adsense-ayar"', metin)
        self.assertIn('"varsayilan": "1234567890"', metin)
        self.assertIn('"999"', metin)

    def test_ads_txt_kimlikten_uretiliyor(self):
        with override_settings(ADSENSE_ID=self.KIMLIK):
            yanit = self.client.get("/ads.txt")
        self.assertEqual(yanit.status_code, 200)
        self.assertIn("text/plain", yanit["Content-Type"])
        satir = yanit.content.decode().strip()
        # "ca-" öneki ads.txt satırında yer almaz.
        self.assertEqual(
            satir, "google.com, pub-0000000000000000, DIRECT, f08c47fec0942fa0")

    def test_ads_txt_kimliksiz_404(self):
        """Yanlış ya da boş ads.txt, dosyanın hiç olmamasından kötüdür."""
        with override_settings(ADSENSE_ID=""):
            self.assertEqual(self.client.get("/ads.txt").status_code, 404)

    def test_betik_sozlesmeyi_koruyor(self):
        betik = (self.KOK / "statik" / "betik" / "reklam-adsense.js").read_text(
            encoding="utf-8")
        # Test modu işareti, esnemeyen sabit ölçü ve dolmayan yuva kuralı.
        self.assertIn("data-adtest", betik)
        self.assertIn("data-full-width-responsive", betik)
        self.assertIn("unfilled", betik)
        # Tanımsız yuvaya uydurma birim kimliği gönderilmez.
        self.assertIn("if (!birim) { return; }", betik)

    def test_olcu_sozlesmesi_ortak_parcada(self):
        """Yuva sözleşmesi üç kez kopyalanmasın; ortak dosyada."""
        ortak = (self.KOK / "statik" / "betik" / "reklam-olcu.js").read_text(
            encoding="utf-8")
        self.assertIn("offsetParent === null", ortak)
        self.assertIn("data-gpt-harita", ortak)
        for ad in ("reklam-test.js", "reklam-adsense.js"):
            betik = (self.KOK / "statik" / "betik" / ad).read_text(
                encoding="utf-8")
            self.assertIn("BHReklamOlcu", betik)
