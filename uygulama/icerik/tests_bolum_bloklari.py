"""Bölüm sayfasının iki yeni bloğu — 6 Eylül 2026 (§59).

Kullanıcı isteği: *"kategori sayfalarının içeriğini çeşitlendirmeni de
istiyorum"*. Seçilen ikisi **görüntü kuşağı** (bölümün videoları ve
galerileri) ve **servis şeridi** (bölümü okuyanın işine yarayan canlı veri).

Korunan üç kural:

1. **Veri yoksa blok yok.** Sahte satır, "alınamadı" kutusu ya da boş
   çerçeve basılmaz. Bölüm sayfasında o cümle okura hiçbir şey anlatmaz.
2. **Kuşak o bölümün kendi arşivinden gelir.** Başka bölümün videosu
   sızarsa kuşak yalan söyler.
3. **Kural şablonda değil görünümde.** Hangi bölümün hangi servisi gördüğü
   `_bolum_servisi`de; şablon yalnız çiziyor.
"""

from unittest import mock

from django.test import TestCase
from django.utils import timezone

from medya.models import FotoGaleri, Video
from taksonomi.models import Ilce, Kategori, KategoriTur

from . import views
from .models import Haber


class BolumBloklari(TestCase):

    @classmethod
    def setUpTestData(cls):
        from django.core.management import call_command
        call_command("taksonomi_kur", verbosity=0)
        cls.ilce = Ilce.objects.first()
        cls.ekonomi = KategoriTur.objects.filter(
            tur=Kategori.TUR_HABER, slug="ekonomi").first().kategori
        cls.gundem = KategoriTur.objects.filter(
            tur=Kategori.TUR_HABER, slug="gundem").first().kategori
        simdi = timezone.now()
        # Bir sayfadan FAZLA kayıt: "daha fazla göster" düğmesi ancak
        # `sayfa.has_next` doğruyken basılıyor ve yerleşim testi onu arıyor.
        for n in range(views.SAYFA_BOYU + 5):
            Haber.objects.create(
                id=900000 + n, slug=f"blok-{n}", baslik=f"Blok haberi {n}",
                govde="<p>Gövde</p>", kategori=cls.ekonomi, ilce=cls.ilce,
                yayin_zamani=simdi)
            Haber.objects.create(
                id=910000 + n, slug=f"blok-g-{n}", baslik=f"Gündem haberi {n}",
                govde="<p>Gövde</p>", kategori=cls.gundem,
                yayin_zamani=simdi)
        # Kuşağın malzemesi: ekonomide iki video + iki galeri, gündemde hiç.
        for n in range(2):
            Video.objects.create(
                id=920000 + n, slug=f"blok-video-{n}", baslik=f"Ekonomi videosu {n}",
                kategori=cls.ekonomi, yayin_zamani=simdi)
            FotoGaleri.objects.create(
                id=930000 + n, slug=f"blok-galeri-{n}", baslik=f"Ekonomi galerisi {n}",
                kategori=cls.ekonomi, yayin_zamani=simdi)

    # -- görüntü kuşağı ----------------------------------------------------

    def test_kusak_bolumun_kendi_video_ve_galerisini_veriyor(self):
        yanit = self.client.get("/ekonomi")
        self.assertEqual(len(yanit.context["bolum_videolari"]), 2)
        self.assertEqual(len(yanit.context["bolum_galerileri"]), 2)
        for kalem in (list(yanit.context["bolum_videolari"]) +
                      list(yanit.context["bolum_galerileri"])):
            self.assertEqual(kalem.kategori_id, self.ekonomi.id)
        self.assertContains(yanit, "GÖRÜNTÜLER")
        self.assertContains(yanit, "Ekonomi videosu 0")

    def test_kusak_verisi_olmayan_bolumde_hic_cizilmiyor(self):
        """Gündemde galeri yok, aktüalitede ikisi de yok (canlı ölçüm)."""
        metin = self.client.get("/gundem").content.decode()
        self.assertNotIn("bolum-goruntu", metin)
        self.assertNotIn("GÖRÜNTÜLER", metin)

    def test_kusak_ilce_sayfasinda_yok(self):
        """Galeri ve videonun kategorisi var, ilçesi yok; uydurma eşleme
        yapmaktansa blok hiç çizilmiyor."""
        metin = self.client.get(f"/ilce/{self.ilce.slug}").content.decode()
        self.assertNotIn("bolum-goruntu", metin)

    def test_kusak_adedi_sabitlerden_geliyor(self):
        self.assertEqual(views.BOLUM_GALERI, 4)
        self.assertEqual(views.BOLUM_VIDEO, 4)

    # -- servis şeridi -----------------------------------------------------

    DOVIZ = {"kalemler": [{"ad": "Dolar", "birim": "TL", "deger": 48.4,
                           "degisim_yuzde": 0.22, "yon": "yukari"}],
             "guncelleme": "2026-09-06T21:12:05+03:00", "bayat": False}
    PUAN = {"takip": {"ad": "BURSASPOR", "sira": 2, "puan": 12, "oynadi": 5,
                      "galibiyet": 4, "beraberlik": 0, "maglubiyet": 1,
                      "averaj": 7, "attigi": 10, "yedigi": 3, "hafta": 6,
                      "lig_adi": "Trendyol 1. Lig", "grup_adi": None,
                      "kulup_id": 7,
                      "mac": {"ev": "MANİSA FK", "ev_kulup_id": 2861,
                              "deplasman": "BURSASPOR", "deplasman_kulup_id": 7,
                              "ev_gol": None, "deplasman_gol": None,
                              "oynandi": False, "saat": "20:00",
                              "tarih": "07.09.2026"}}}
    # Sahte lig tablosu: pencere testleri gerçek veriye bağlanmasın.
    LIGLER = [{"gruplar": [{"takimlar": [
        {"sira": i + 1, "ad": f"Takım {i}", "oynadi": 5, "averaj": 9 - i,
         "puan": 15 - i, "bizim": i == 1, "bursa": False}
        for i in range(10)]}]}]

    def _oku(self, doviz=None, puan=None):
        def sahte(bilesen):
            return {"doviz": doviz, "puan-durumu": puan}.get(bilesen)
        return mock.patch.object(views, "oku", sahte)

    def test_ekonomide_doviz_bandi_ciziliyor(self):
        with self._oku(doviz=self.DOVIZ):
            metin = self.client.get("/ekonomi").content.decode()
        self.assertIn('bolum-servis s-doviz', metin)
        self.assertIn("PİYASA", metin)
        self.assertIn("Dolar", metin)

    def test_spor_bolumlerinde_lig_satiri_ciziliyor(self):
        for yol in ("/bursaspor", "/spor"):
            with self._oku(puan=self.PUAN):
                metin = self.client.get(yol).content.decode()
            self.assertIn('bolum-servis s-puan', metin, yol)
            self.assertIn("2. sıra", metin, yol)
            self.assertIn("Trendyol 1. Lig", metin, yol)
            # Şerit bir ÖZET: puan tablosunun kendisi taşınmadı.
            # Panel tablonun TAMAMINI taşımıyor; bu turda tablo verisi hiç
            # yok (fikstürde yalnız `takip` var) ve pencere sessizce
            # çizilmiyor — maç kartı ile künye tek başlarına ayakta duruyor.
            self.assertIn('mac-karti', metin, yol)
            self.assertNotIn('puan-pencere', metin, yol)
            self.assertNotIn('<table', metin, yol)

    def test_veri_yoksa_serit_hic_cizilmiyor(self):
        with self._oku():
            for yol in ("/ekonomi", "/bursaspor"):
                metin = self.client.get(yol).content.decode()
                self.assertNotIn("bolum-servis", metin, yol)

    def test_servissiz_bolumde_serit_yok(self):
        with self._oku(doviz=self.DOVIZ, puan=self.PUAN):
            metin = self.client.get("/gundem").content.decode()
        self.assertNotIn("bolum-servis", metin)

    def test_nobet_seridi_bos_listede_cizilmiyor(self):
        with mock.patch.object(views.eczane_sayfa, "gunun_paketi",
                               lambda *a, **k: None):
            self.assertIsNone(views._bolum_servisi(slug="saglik"))
            self.assertIsNone(views._bolum_servisi(ilce=self.ilce))

    def test_nobet_seridi_ilceye_suzuluyor(self):
        """İlçe sayfasında yalnız O İLÇENİN nöbetçisi görünür; sayı ise
        şeritte görünenin değil, ilçenin bugünkü TOPLAMININ sayısıdır
        (URUN-PLANI.md §32.2: düğmedeki sayı basınca geleni sayar)."""
        oteki = Ilce.objects.exclude(pk=self.ilce.pk).first()
        paket = {"gun": None, "eczaneler": [
            {"ad": f"Eczane {n}", "ilce": self.ilce.ad,
             "ilce_anahtar": self.ilce.slug, "telefon": "", "telefon_baglanti": ""}
            for n in range(5)] + [
            {"ad": "Öteki eczane", "ilce": oteki.ad, "ilce_anahtar": oteki.slug,
             "telefon": "", "telefon_baglanti": ""}]}
        with mock.patch.object(views.eczane_sayfa, "gunun_paketi",
                               lambda *a, **k: paket):
            servis = views._bolum_servisi(ilce=self.ilce)
        self.assertEqual(servis["tur"], "nobet")
        self.assertEqual(servis["adet"], 5)
        self.assertEqual(len(servis["eczaneler"]), views.SERVIS_ECZANE)
        for e in servis["eczaneler"]:
            self.assertEqual(e["ilce_anahtar"], self.ilce.slug)

    def test_hangi_bolum_hangi_servis_gorunumde(self):
        """Kural şablonda değil görünümde; şablon yalnız çiziyor."""
        self.assertIn("ekonomi", views.SERVIS_DOVIZ)
        self.assertIn("bursaspor", views.SERVIS_PUAN)
        self.assertIn("saglik", views.SERVIS_NOBET)
        kok = views.__file__.rsplit("icerik", 1)[0] + "sablonlar"
        with open(kok + "/parca/bolum_servis.html", encoding="utf-8") as d:
            sablon = d.read()
        # Şablon bölüm slug'ına BAKMIYOR: dallanma `servis.tur` üzerinden.
        # (`/bursaspor` şablonda geçiyor ama bir karar değil, bağlantıdır.)
        self.assertNotIn("slug ==", sablon)
        self.assertNotIn("kategori.slug", sablon)
        self.assertEqual(sablon.count('servis.tur =='), 3)

    def test_doviz_iki_sayfada_da_tek_VERIDEN(self):
        """Ortak olan veri, biçim değil (7 Eylül 2026, §62).

        6 Eylül'de bant `parca/doviz.html`e çıkarılmıştı ve bölüm sayfası
        onu aynen basıyordu. Panel geldiğinde biçim BİLEREK ayrıldı:
        anasayfada tek satırlık bant, bölümde beş gözlü ızgara — aynı
        veriyi iki farklı yerde iki farklı işe koşuyoruz.

        Korunan şey sayının kaynağı: ikisi de `oku("doviz")` paketini
        okur, ikinci bir kur listesi yoktur."""
        kok = views.__file__.rsplit("icerik", 1)[0] + "sablonlar"
        with open(f"{kok}/anasayfa.html", encoding="utf-8") as d:
            self.assertIn("parca/doviz.html", d.read())
        with open(f"{kok}/parca/bolum_servis.html", encoding="utf-8") as d:
            panel = d.read()
        self.assertIn("servis.doviz.kalemler", panel)
        self.assertNotIn("parca/doviz.html", panel)
        # Tek kaynak: görünüm her iki yolda da aynı bileşeni okuyor.
        with self._oku(doviz=self.DOVIZ):
            servis = views._bolum_servisi(slug="ekonomi")
        self.assertEqual(servis["doviz"], self.DOVIZ)

    def test_dugme_kusagin_USTUNDE_ve_akisin_hemen_altinda(self):
        """7 Eylül 2026, kullanıcı bildirimi: "butona tıklandığında sayfa
        aşağı ilerlemiyor, sadece yukarıda yeni haberler gösteriyor".

        Kusur yerleşimdeydi: düğme §59'da görüntü kuşağının ALTINA konmuştu
        ve kuşak 372 px yer kaplıyordu; okur düğmeye bakarken akışın sonu
        ekranın çok yukarısında kalıyor, eklenen 20 haber oraya giriyordu.

        Sıra ARTIK bağlayıcı: akış → düğme → kuşak. Kuşak düğmenin altında
        kalır ki her tıklamada onunla birlikte aşağı kaysın ve kaç kalem
        yüklenirse yüklensin erişilebilir olsun.
        """
        metin = self.client.get("/ekonomi").content.decode()
        akis = metin.index('class="akis-ritim"')
        dugme = metin.index('class="daha-fazla"')
        kusak = metin.index("bolum-goruntu")
        self.assertLess(akis, dugme, "düğme akıştan sonra gelmeli")
        self.assertLess(dugme, kusak, "düğme kuşaktan ÖNCE gelmeli")
        # Düğme listenin kendi kutusunun içinde: kuşak ayrı bir <section>.
        self.assertLess(dugme, metin.index('<section class="kutu bolum-goruntu"'))

    def test_betik_yeni_kalemlere_iniyor(self):
        """Ekleme sonrası sayfa yeni yığının başına iner ve odak oraya
        taşınır; kaydırma yapışkan bandın altına oturur."""
        from pathlib import Path
        kok = Path(__file__).resolve().parent.parent
        betik = (kok / "statik" / "betik" / "site.js").read_text(encoding="utf-8")
        self.assertIn("scrollIntoView", betik)
        self.assertIn("preventScroll", betik)
        # Hareket azaltma isteyen okurda yumuşak kaydırma yok.
        self.assertIn("azalt.matches ? 'auto' : 'smooth'", betik)
        stil = (kok / "statik" / "stil" / "site.css").read_text(encoding="utf-8")
        self.assertIn("scroll-margin-top", stil)
        self.assertIn(".akis-blok:focus-visible", stil)

    # -- panel biçimi (7 Eylül 2026, §62) ---------------------------------

    def test_serit_gitti_panel_geldi(self):
        """Kullanıcı kararı: "tek satırlık şerit hoş bir görüntü değil, bu
        alanları düzgün bir alan olarak koymalıyız". Şeridin sınıfları
        sayfadan da biçim dosyasından da kalktı."""
        with self._oku(doviz=self.DOVIZ):
            metin = self.client.get("/ekonomi").content.decode()
        for eski in ("servis-satir", "servis-etiket", "servis-ana", "servis-tumu"):
            self.assertNotIn(eski, metin, eski)
        # Panel sitenin kendi kutusu: başlık çubuğu + gövde + künye.
        self.assertIn('<section class="kutu bolum-servis', metin)
        self.assertIn("kutu-bas", metin)
        self.assertIn("servis-kunye", metin)
        from pathlib import Path
        stil = (Path(__file__).resolve().parent.parent / "statik" / "stil" /
                "site.css").read_text(encoding="utf-8")
        self.assertNotIn(".servis-satir", stil)
        self.assertNotIn(".servis-etiket", stil)

    def test_piyasa_paneli_bes_kalemi_ayri_ayri_veriyor(self):
        """Şeritte beş kalem tek satıra sıkışıyor, alış/satış hiç
        görünmüyordu."""
        doviz = dict(self.DOVIZ)
        doviz["kalemler"] = [
            {"ad": "Dolar", "birim": "TL", "deger": 48.4, "alis": 48.23,
             "satis": 48.32, "degisim_yuzde": 0.22, "yon": "yukari"},
            {"ad": "BIST 100", "birim": "puan", "deger": 14012.42,
             "degisim_yuzde": 0.57, "yon": "yukari"},
        ]
        with self._oku(doviz=doviz):
            metin = self.client.get("/ekonomi").content.decode()
        self.assertEqual(metin.count("piyasa-kalem"), 2)
        self.assertIn("Alış 48,23", metin)
        # Alış/satışı OLMAYAN kalemde alan hiç basılmaz: boş bir "Alış –"
        # okura yanlış bir eksiklik duygusu verirdi.
        self.assertEqual(metin.count("alis-satis"), 1)

    def test_puan_paneli_mac_ve_pencere_veriyor(self):
        puan = self.PUAN
        with mock.patch.object(views, "oku", lambda b: puan if b == "puan-durumu" else None), \
             mock.patch.object(views, "puan_ligleri", lambda p: self.LIGLER):
            yanit = self.client.get("/bursaspor")
        servis = yanit.context["servis"]
        self.assertEqual(servis["tur"], "puan")
        self.assertEqual(len(servis["pencere"]), 2 * views.PUAN_PENCERE + 1)
        self.assertTrue(any(t.get("bizim") for t in servis["pencere"]))
        metin = yanit.content.decode()
        self.assertIn("mac-karti", metin)
        self.assertIn("puan-pencere", metin)

    def test_puan_penceresi_tablonun_ucunda_kaydiriliyor(self):
        """Bursaspor birinciyken de sonuncuyken de beş satır gösterilir;
        pencerenin üstü ya da altı boş bırakılmaz."""
        boy = 2 * views.PUAN_PENCERE + 1
        for yer in (0, 1, 5, 9):
            takimlar = [{"sira": i + 1, "ad": f"T{i}", "bizim": i == yer}
                        for i in range(10)]
            ligler = [{"gruplar": [{"takimlar": takimlar}]}]
            with mock.patch.object(views, "puan_ligleri", lambda p: ligler):
                pencere = views._puan_penceresi({}, self.PUAN["takip"])
            self.assertEqual(len(pencere), boy, yer)
            self.assertTrue(any(t["bizim"] for t in pencere), yer)

    def test_puan_penceresi_takip_yoksa_bos(self):
        self.assertEqual(views._puan_penceresi({}, None), [])

    def test_eczane_paneli_adres_ve_haritayi_veriyor(self):
        """Şeritte yalnız ad ve telefon vardı; okurun gece yarısı ihtiyacı
        olan şey adres ve harita."""
        paket = {"gun": None, "pencere": "08:30 – 08:30 ertesi gün",
                 "kaynak": {"ad": "Bursa Eczacı Odası"}, "eczaneler": [
                     {"ad": f"Eczane {n}", "ilce": "GEMLİK", "ilce_anahtar": "gemlik",
                      "adres": f"MAH. SOK. NO:{n}", "telefon": "0224 000 00 00",
                      "telefon_baglanti": "+902240000000",
                      "harita": "https://ornek.tr/harita"} for n in range(6)]}
        with mock.patch.object(views.eczane_sayfa, "gunun_paketi",
                               lambda *a, **k: paket):
            metin = self.client.get("/saglik").content.decode()
        self.assertEqual(metin.count("eczane-izgara"), 1)
        self.assertIn("MAH. SOK. NO:0", metin)
        self.assertIn("Haritada göster", metin)
        # Dış bağlantı yeni sekmede ve `rel` ile açılır.
        self.assertIn('rel="noopener noreferrer"', metin)
        # Panelde SERVIS_ECZANE kadar kalem var; ölçüt panelin kendi
        # işaretleri (sayfanın tamamında `<li>` menüde de geçiyor).
        self.assertEqual(metin.count("Haritada göster"), views.SERVIS_ECZANE)
        self.assertEqual(metin.count('class="tel"'), views.SERVIS_ECZANE)
        # Adet PANELİN GÖSTERDİĞİ değil, bugünkü TOPLAM.
        self.assertIn("6 eczanenin tamamı", metin)

    # -- renk temaları geri alındı (7 Eylül 2026, §63) --------------------

    def test_bolume_ozel_renk_yok(self):
        """Kullanıcı kararı: "farklı renk temalarını geri al".

        §62'de dört bölüm kendi vurgusunu almıştı (kulüp yeşili, kent
        mavisi, piyasa amberi, sağlık turkuazı); düzeneğin tamamı kalktı.
        Bu test kararı tutuyor: düzenek geri gelirse burada düşer ve
        kullanıcıya yeniden sorulması gerektiği anlaşılır.

        §35'in "site lacivert-kırmızı kalır" kuralı böylece istisnasız
        sürüyor; tek istisna anasayfadaki `#bursaspor` kutusudur ve o
        29 Ağustos 2026'da ayrıca kararlaştırılmıştı."""
        for yol in ("/bursaspor", "/bursa", "/ekonomi", "/saglik",
                    "/gundem", f"/ilce/{self.ilce.slug}"):
            self.assertNotIn("data-bolum", self.client.get(yol).content.decode(), yol)
        self.assertFalse(hasattr(views, "BOLUM_TEMA"))
        self.assertFalse(hasattr(views, "ILCE_TEMA"))
        from pathlib import Path
        kok = Path(__file__).resolve().parent.parent
        stil = (kok / "statik" / "stil" / "site.css").read_text(encoding="utf-8")
        # Yorumlar ayıklanıyor: kararın NEDEN geri alındığı dosyada yazılı
        # kalmalı ve o metinde `[data-bolum]` geçiyor. Aranan şey KURAL.
        import re
        kural = re.sub(r"/\*.*?\*/", "", stil, flags=re.S)
        for iz in ("--bolum-vurgu", "--bolum-koyu", "--bolum-ak", "--bolum-cizgi",
                   "data-bolum", "--saglik"):
            self.assertNotIn(iz, kural, iz)
        taban = (kok / "sablonlar" / "taban.html").read_text(encoding="utf-8")
        self.assertNotIn("ana_nitelik", taban)

    def test_servis_panelleri_kaldi(self):
        """Geri alınan RENKTİ, panel değil: §62'nin birinci yarısı duruyor."""
        with self._oku(doviz=self.DOVIZ):
            self.assertIn("piyasa-izgara", self.client.get("/ekonomi").content.decode())
        self.assertIn("eczane-izgara", self.client.get("/saglik").content.decode())

