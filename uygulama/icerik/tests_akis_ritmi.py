"""Bölüm akışının ikili/üçlü ritmi — 7 Eylül 2026 (§60).

Kullanıcı isteği: *"kategori sayfalarında haberlerin tarihlere bölünmesini
kaldır, onun yerine 2'li ve 3'lü haberlerin sunulacağı bir akış hazırla"*.

Korunan dört şey:

1. **Tarih ayracı gitti** — kategori ve ilçe sayfasında. Konu dosyasında
   DURUYOR: orada kronoloji sayfanın konusudur.
2. **Zaman bilgisi gitmedi.** Ayraç kalkarken kartın kendi damgası kaldı;
   `kisa_zaman` aynı günde saat, eskisinde tarih basıyor.
3. **Ritim tam bölünüyor.** 1. sayfa akışı 17, sonrakiler 20; ikisi de
   2+3 turuna tam oturuyor ve hiçbir blok yarım kalmıyor. Sayfa boyu ya da
   kart kademesi değişirse bu test düşer — hesap yeniden yapılmalıdır.
4. **Seamde tekleme yok.** 1. sayfa ikiliyle biter, "daha fazla göster"in
   getirdiği dilim üçlüyle başlar.
"""

from django.test import TestCase
from django.utils import timezone

from taksonomi.models import Ilce, Kategori, KategoriTur

from . import views
from .models import Haber


class AkisRitmi(TestCase):

    @classmethod
    def setUpTestData(cls):
        from django.core.management import call_command
        call_command("taksonomi_kur", verbosity=0)
        cls.ilce = Ilce.objects.first()
        cls.kategori = KategoriTur.objects.filter(
            tur=Kategori.TUR_HABER, slug="gundem").first().kategori
        simdi = timezone.now()
        # Üç tam sayfa: ritmin sayfa sınırında ne yaptığı görülsün.
        for n in range(3 * views.SAYFA_BOYU + 4):
            Haber.objects.create(
                id=940000 + n, slug=f"ritim-{n}", baslik=f"Ritim haberi {n}",
                spot=f"Ritim spotu {n}", govde="<p>Gövde</p>",
                kategori=cls.kategori, ilce=cls.ilce,
                # Kayıtlar GÜNLERE yayılıyor: ayraç hâlâ basılıyor olsaydı
                # bu fikstürle görünürdü.
                yayin_zamani=simdi - timezone.timedelta(hours=8 * n))

    # -- ayraç gitti -------------------------------------------------------

    def test_kategori_ve_ilce_sayfasinda_tarih_ayraci_yok(self):
        for yol in ("/gundem", f"/ilce/{self.ilce.slug}", "/son-haberler"):
            metin = self.client.get(yol).content.decode()
            self.assertNotIn('class="gun"', metin, yol)
            self.assertIn("akis-ritim", metin, yol)

    def test_parcada_da_tarih_ayraci_yok(self):
        metin = self.client.get(
            "/daha-fazla?kaynak=kategori&slug=gundem&sayfa=2").content.decode()
        self.assertNotIn('class="gun"', metin)
        self.assertIn("akis-blok", metin)

    def test_zaman_damgasi_kartta_duruyor(self):
        """Ayraç kalktı, "ne zaman" bilgisi kalkmadı."""
        metin = self.client.get("/gundem").content.decode()
        self.assertIn("<time datetime=", metin)

    def test_konu_dosyasinda_ayrac_duruyor(self):
        """Karar YALNIZ bölüm sayfası içindi; konu dosyasında kronoloji
        sayfanın konusudur ve eski liste orada sürüyor."""
        from pathlib import Path
        kok = Path(__file__).resolve().parent.parent / "sablonlar"
        konu = (kok / "konu.html").read_text(encoding="utf-8")
        self.assertIn('class="gun"', konu)
        self.assertIn("parca/akis_satiri.html", konu)

    # -- ritim -------------------------------------------------------------

    def test_bloklar_ikili_uclu_diye_gidiyor(self):
        bloklar = views._akis_bloklari(list(range(17)))
        self.assertEqual([b["boy"] for b in bloklar], [2, 3, 2, 3, 2, 3, 2])
        self.assertEqual([b["tur"] for b in bloklar],
                         ["ikili", "uclu", "ikili", "uclu", "ikili", "uclu", "ikili"])

    def test_spot_yalniz_ikilide(self):
        for blok in views._akis_bloklari(list(range(17))):
            self.assertEqual(blok["spot"], blok["boy"] == 2)

    def test_sayfa_boylari_ritme_tam_oturuyor(self):
        """Hesap: 1. sayfa 20−3 = 17 = 2+3+2+3+2+3+2, sonrakiler 20 =
        3+2+3+2+3+2+3+2. Sayı değişirse burası düşer ve yeniden hesaplanır."""
        tur = sum(views.AKIS_RITMI)
        ilk = views.SAYFA_BOYU - views.KATEGORI_KART
        for kalem, ilk_uclu in ((ilk, False), (views.SAYFA_BOYU, True)):
            bloklar = views._akis_bloklari(list(range(kalem)), ilk_uclu=ilk_uclu)
            self.assertEqual(sum(b["boy"] for b in bloklar), kalem)
            for b in bloklar:
                self.assertEqual(len(b["kalemler"]), b["boy"],
                                 "hiçbir blok yarım kalmamalı")
        self.assertEqual(tur, 5)

    def test_seam_teklemiyor(self):
        """1. sayfa ikiliyle biter, sonraki dilim üçlüyle başlar."""
        ilk = views._akis_bloklari(
            list(range(views.SAYFA_BOYU - views.KATEGORI_KART)), ilk_uclu=False)
        sonraki = views._akis_bloklari(list(range(views.SAYFA_BOYU)), ilk_uclu=True)
        self.assertEqual(ilk[-1]["tur"], "ikili")
        self.assertEqual(sonraki[0]["tur"], "uclu")
        self.assertEqual(sonraki[-1]["tur"], "ikili")

    def test_son_blok_eksik_kalabilir(self):
        """Bölümün son sayfasında kalem sayısı 5'in katı olmayabilir;
        ızgara hücreyi boş bırakır, kalem uydurulmaz."""
        bloklar = views._akis_bloklari(list(range(4)))
        self.assertEqual([len(b["kalemler"]) for b in bloklar], [2, 2])
        self.assertEqual(bloklar[-1]["boy"], 3)

    def test_bos_liste_blok_uretmiyor(self):
        self.assertEqual(views._akis_bloklari([]), [])

    # -- sayfa üstünde -----------------------------------------------------

    def test_ilk_sayfa_akisi_kart_kademesini_tekrarlamiyor(self):
        yanit = self.client.get("/gundem")
        kademe = [h.pk for h in list(yanit.context["sayfa"])[:views.KATEGORI_KART]]
        akista = [h.pk for blok in yanit.context["akis"] for h in blok["kalemler"]]
        self.assertEqual(len(akista), views.SAYFA_BOYU - views.KATEGORI_KART)
        self.assertFalse(set(kademe) & set(akista))

    def test_ikinci_sayfada_kademe_yok_akis_tam(self):
        yanit = self.client.get("/gundem?sayfa=2")
        akista = [h.pk for blok in yanit.context["akis"] for h in blok["kalemler"]]
        self.assertEqual(len(akista), views.SAYFA_BOYU)
        self.assertEqual(yanit.context["akis"][0]["tur"], "uclu")

    def test_parca_sayfadakini_tekrarlamiyor(self):
        sayfa = self.client.get("/gundem")
        parca = self.client.get("/daha-fazla?kaynak=kategori&slug=gundem&sayfa=2")
        sayfada = {h.pk for h in sayfa.context["sayfa"]}
        gelen = {h.pk for blok in parca.context["akis"] for h in blok["kalemler"]}
        self.assertFalse(sayfada & gelen)

    def test_dugmenin_hedefi_yeni_kap(self):
        """`data-hedef` ile kabın sınıfı aynı olmak zorunda; ayrışırsa
        düğme hiçbir şey yapmayan bir bağlantıya döner."""
        metin = self.client.get("/gundem").content.decode()
        self.assertIn('data-hedef=".akis-ritim"', metin)
        self.assertIn('<div class="akis-ritim">', metin)

    def test_betik_blok_kalemlerini_sayiyor(self):
        """Durum satırı kaç HABER geldiğini söylemeli, kaç kap geldiğini
        değil — blok kendi kalemlerini taşıyor."""
        from pathlib import Path
        betik = (Path(__file__).resolve().parent.parent / "statik" / "betik" /
                 "site.js").read_text(encoding="utf-8")
        self.assertIn("akis-blok", betik)
        # Ayraç tekilleştirme yardımcısı ayraçla birlikte kalktı.
        self.assertNotIn("ayraciTekille", betik)

    # -- fotoğraf çerçeveleri (7 Eylül 2026, §64) -------------------------

    def test_cerceve_orani_arsivin_oraniyla_ayni(self):
        """Kullanıcı bildirimi: "en üstteki 3 büyük haberin görselleri tam
        sığmamış gibi görünüyor çerçevelerine".

        Nedeni ölçüldü: ARŞİVİN TAMAMI 3:2. Rastgele 1.498 dosyanın 1.498'i
        (%100) tam 1,5 oranında — kaynak sistem `_large` görselini sabit
        oranda üretiyor. `object-fit:cover` farkı kırparak kapatıyordu:

            üst kademe · geniş   4:3  → %11 YANLARDAN
            akış blokları       16:9  → %16 ALTTAN VE ÜSTTEN

        İkisi de 3:2'ye çekildi ve kırpma sıfırlandı (dört kırılma
        noktasında ölçüldü). Bu test oranı bağlıyor: kart çerçevelerinde
        3:2 dışında bir `aspect-ratio` görünürse arşivle uyuşmaz."""
        from pathlib import Path
        stil = (Path(__file__).resolve().parent.parent / "statik" / "stil" /
                "site.css").read_text(encoding="utf-8")
        import re
        kural = re.sub(r"/\*.*?\*/", "", stil, flags=re.S)
        # Kart/akış çerçevelerinin oranı: hepsi 3/2. 20 Ekim 2026 (R1):
        # oran tek kaynaktan, `:root`taki `--cerceve-orani` değişkeninden.
        self.assertIn("--cerceve-orani:3/2;", kural)
        for secici in (".liste-izgara .kart:not(.genis) .foto",
                       ".liste-izgara .kart.genis .foto",
                       ".akis-blok .foto",
                       ".akis .foto"):
            yer = kural.find(secici)
            self.assertNotEqual(yer, -1, secici)
            blok = kural[yer:kural.index("}", yer)]
            self.assertIn("aspect-ratio:var(--cerceve-orani)", blok, secici)
        # Arşivle uyuşmayan iki oran hiçbir kart çerçevesinde kalmadı.
        for oran in ("aspect-ratio:4/3", "aspect-ratio:16/9"):
            self.assertNotIn(oran, kural, oran)
