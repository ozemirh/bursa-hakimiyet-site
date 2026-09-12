"""«Daha fazla göster» — 6 Eylül 2026 (§48).

Kullanıcı isteği: "hem anasayfada hem de kategori sayfalarında daha fazla
göster seçeneği ekle haberler için, numaralara bölme sayfaları".

Korunan üç şey:

1. **Numaralar geri gelmiyor.** Kategori ve ilçe sayfasında numaralı
   sayfalama yok; arama ve dizin sayfalarında DURUYOR (orada okur bir sonuç
   kümesinde geziniyor, "kaçıncı sayfadayım" bilgisi işine yarıyor).
2. **JavaScript'siz yol açık.** Düğme gerçek bir bağlantı; adres gerçekten
   çalışıyor. Bu kırılırsa numaralar da gitmiş olduğu için arşivin devamına
   giden hiçbir yol kalmaz — betiği kapalı okur da arama motoru da orada
   durur.
3. **Anasayfa kendini tekrarlamıyor.** Parça, ızgarada zaten basılmış
   kayıtların üstünden atlar.
"""

from django.test import TestCase
from django.utils import timezone

from taksonomi.models import Ilce, Kategori, KategoriTur

from . import views
from .models import Haber


class DahaFazlaGoster(TestCase):

    @classmethod
    def setUpTestData(cls):
        from django.core.management import call_command
        call_command("taksonomi_kur", verbosity=0)
        cls.ilce = Ilce.objects.first()
        tur = KategoriTur.objects.filter(tur=Kategori.TUR_HABER,
                                         slug="gundem").first()
        cls.kategori = tur.kategori
        # Anasayfa havuzu 45 kayıt tüketiyor; parçanın da dolması için
        # üstüne en az bir dilim daha gerekiyor.
        adet = views.ANASAYFA_ATLA + views.SAYFA_BOYU + 5
        simdi = timezone.now()
        for n in range(adet):
            Haber.objects.create(
                id=800000 + n, slug=f"daha-{n}", baslik=f"Daha fazla {n}",
                spot=f"Spot {n}", govde=f"<p>Gövde {n}</p>",
                kategori=cls.kategori, ilce=cls.ilce,
                # Gün ayracı sınanabilsin diye kayıtlar günlere yayılıyor.
                yayin_zamani=simdi - timezone.timedelta(hours=6 * n))

    # -- numaralar gitti ---------------------------------------------------

    def test_kategori_sayfasinda_numarali_sayfalama_yok(self):
        metin = self.client.get("/gundem").content.decode()
        self.assertNotIn('class="sayfalama"', metin)
        self.assertIn('class="daha-fazla"', metin)

    def test_ilce_sayfasinda_numarali_sayfalama_yok(self):
        metin = self.client.get(f"/ilce/{self.ilce.slug}").content.decode()
        self.assertNotIn('class="sayfalama"', metin)
        self.assertIn('class="daha-fazla"', metin)

    def test_numarali_sayfalama_kume_sayfalarinda_duruyor(self):
        """Karar YALNIZ haber listeleri içindi. Arama sonucu, konu dizini ve
        resmî ilan dizini birer KÜMEDİR; okur orada "kaçıncı sayfadayım"
        bilgisini kullanıyor ve parça silinmedi.

        Ölçüt şablonun kendisinde: sayfalama yalnız sonuç birden çok sayfaya
        taştığında basılıyor, fikstürle o eşiği zorlamak testi kırılgan
        yapardı."""
        from pathlib import Path
        kok = Path(__file__).resolve().parent.parent / "sablonlar"
        self.assertTrue((kok / "parca" / "sayfalama.html").exists())
        for ad in ("arama.html", "konular.html", "resmi_ilan.html"):
            self.assertIn('parca/sayfalama.html',
                          (kok / ad).read_text(encoding="utf-8"), ad)
        for ad in ("kategori.html", "anasayfa.html"):
            self.assertNotIn('parca/sayfalama.html',
                             (kok / ad).read_text(encoding="utf-8"), ad)

    # -- JavaScript'siz yol ------------------------------------------------

    def test_dugme_gercek_bir_bagalanti_ve_adres_calisiyor(self):
        """Düğme <button> olsaydı betiksiz okur arşivin devamına inemezdi."""
        metin = self.client.get("/gundem").content.decode()
        self.assertIn('<a class="daha-fazla" href="?sayfa=2"', metin)
        self.assertIn('rel="next"', metin)
        self.assertEqual(self.client.get("/gundem?sayfa=2").status_code, 200)

    def test_anasayfa_dugmesi_son_haberlere_gidiyor(self):
        metin = self.client.get("/").content.decode()
        self.assertIn('href="/son-haberler"', metin)
        self.assertEqual(self.client.get("/son-haberler").status_code, 200)

    def test_uc_arama_motoruna_kapali_gercek_sayfa_acik(self):
        """Parça bir sayfa değil; taranırsa aynı haberler künyesiz bir
        adreste ikinci kez görünür. Düğmenin kendi adresi AÇIK kalmalı."""
        robots = self.client.get("/robots.txt").content.decode()
        self.assertIn("Disallow: /daha-fazla", robots)
        self.assertNotIn("Disallow: /gundem", robots)

    # -- parça ucu ---------------------------------------------------------

    def test_parca_kalem_ve_devam_bilgisi_donuyor(self):
        yanit = self.client.get("/daha-fazla?kaynak=kategori&slug=gundem&sayfa=2")
        self.assertEqual(yanit.status_code, 200)
        self.assertEqual(len(yanit.context["kalemler"]), views.SAYFA_BOYU)
        self.assertIn('data-devam=', yanit.content.decode())

    def test_parcanin_son_dilimi_devam_yok_diyor(self):
        """`data-devam` sayımdan değil, BİR FAZLA kayıttan çıkıyor."""
        toplam = Haber.yayindakiler().filter(kategori=self.kategori).count()
        son = (toplam + views.SAYFA_BOYU - 1) // views.SAYFA_BOYU
        yanit = self.client.get(
            f"/daha-fazla?kaynak=kategori&slug=gundem&sayfa={son}")
        self.assertFalse(yanit.context["devam"])
        self.assertIn('data-devam="0"', yanit.content.decode())

    def test_bilinmeyen_kaynak_ve_bolum_404(self):
        for adres in ("/daha-fazla?kaynak=uydurma",
                      "/daha-fazla?kaynak=kategori",
                      "/daha-fazla?kaynak=kategori&slug=olmayan-bolum",
                      "/daha-fazla?kaynak=ilce&slug=olmayan-ilce"):
            self.assertEqual(self.client.get(adres).status_code, 404, adres)

    def test_bozuk_sayfa_numarasi_ilk_dilime_dusuyor(self):
        for adres in ("/daha-fazla?kaynak=kategori&slug=gundem&sayfa=abc",
                      "/daha-fazla?kaynak=kategori&slug=gundem&sayfa=-5"):
            yanit = self.client.get(adres)
            self.assertEqual(yanit.status_code, 200, adres)
            self.assertTrue(yanit.context["kalemler"], adres)

    # -- tekrar yok --------------------------------------------------------

    def test_anasayfa_parcasi_izgaradakileri_tekrarlamiyor(self):
        sayfa = self.client.get("/")
        basilan = {h.id for anahtar in ("manset", "manset_liste", "ikincil",
                                        "dortlu", "kutular")
                   for h in sayfa.context[anahtar]}
        parca = self.client.get("/daha-fazla?kaynak=anasayfa&sayfa=1")
        gelen = {h.id for h in parca.context["kalemler"]}
        self.assertEqual(len(gelen), views.ANASAYFA_DAHA)
        self.assertFalse(basilan & gelen)

    def test_ardisik_dilimler_kesismiyor(self):
        bir = self.client.get("/daha-fazla?kaynak=kategori&slug=gundem&sayfa=1")
        iki = self.client.get("/daha-fazla?kaynak=kategori&slug=gundem&sayfa=2")
        self.assertFalse({h.id for h in bir.context["kalemler"]} &
                         {h.id for h in iki.context["kalemler"]})

    def test_kategori_parcasi_yalniz_o_bolumun_haberlerini_veriyor(self):
        yanit = self.client.get("/daha-fazla?kaynak=kategori&slug=gundem&sayfa=1")
        self.assertTrue(yanit.context["kalemler"])
        for h in yanit.context["kalemler"]:
            self.assertEqual(h.kategori_id, self.kategori.id)

    # -- betiğin sözleşmesi ------------------------------------------------

    def test_betik_parcayi_ve_devam_bayragini_taniyor(self):
        """Şablonla betik arasındaki üç ad: sınıf, kap ve bayrak. Biri
        değişirse düğme sessizce hiçbir şey yapmayan bir bağlantıya döner."""
        from pathlib import Path
        betik = (Path(__file__).resolve().parent.parent / "statik" / "betik" /
                 "site.js").read_text(encoding="utf-8")
        for parca in ("daha-fazla", "akis-parca", "data-devam", "data-hedef",
                      "data-uc", "daha-fazla-son"):
            self.assertIn(parca, betik, parca)

    def test_basarida_durum_yazisi_yok_hatada_var(self):
        """7 Eylül 2026, kullanıcı isteği: "20 haber eklendi, listenin
        devamı için düğmeye basın yazısını kaldır".

        Ekran okuyucu bilgisiz kalmıyor: aynı gün odak yeni yığının ilk
        kalemine taşınmaya başladı (§61) ve okuyucu odaklanılan kalemi
        zaten okuyor — satır o değişiklikten sonra ikinci kez söylüyordu.

        Alan SİLİNMEDİ: uç çökerse düğme görünüşte hiçbir şey yapmamış
        olur ve okurun ne olduğunu okuması gerekir."""
        from pathlib import Path
        kok = Path(__file__).resolve().parent.parent
        betik = (kok / "statik" / "betik" / "site.js").read_text(encoding="utf-8")
        self.assertNotIn("Listenin devamı için düğmeye basın", betik)
        # Durum alanına YALNIZ hata dalı yazıyor. Sayım ölçüt olarak
        # seçildi: metni silip atamayı bırakmak, boş bir duyuru göndermek
        # olurdu ve ekran okuyucu yine ses çıkarırdı.
        self.assertEqual(betik.count("durum.textContent"), 1)
        self.assertIn("Haberler yüklenemedi", betik)
        sablon = (kok / "sablonlar" / "parca" / "daha_fazla.html").read_text(
            encoding="utf-8")
        self.assertIn('class="daha-fazla-durum"', sablon)
        self.assertIn('role="status"', sablon)
        # Boşken yer kaplamamalı; yoksa düğmenin altında ölü bir satır kalır.
        stil = (kok / "statik" / "stil" / "site.css").read_text(encoding="utf-8")
        self.assertIn(".daha-fazla-durum:empty{display:none}", stil)
