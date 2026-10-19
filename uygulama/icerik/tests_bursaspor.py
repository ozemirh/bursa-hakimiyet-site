"""Bursaspor bölüm sayfası — fikstür ve yeşil-beyaz kabuk (12 Eylül 2026).

Kullanıcı kararı: *"haftanın maçı, puan tablosu ve fikstür kalsın, geri
kalanı kaldır; ama bursaspor sayfasını da yeşil beyaz renklerine büründür"*.
Denetlenen üç kural:

1. **Veri yoksa blok yok.** Fikstür boşsa tablo çizilmez; sahte satır yok.
2. **Kaynakta olmayan alan uydurulmaz.** Skor yoksa "–", saat yoksa boş.
3. **Fikstür ve yeşil kabuk yalnız `/bursaspor`ta.** `/spor` ve diğer
   bölümler lacivert-kırmızı kalır (§63).
"""

from datetime import date
from unittest import mock

from django.test import TestCase
from django.utils import timezone

from taksonomi.models import Kategori, KategoriTur

from . import bursaspor, views
from .models import Haber


def _mac(hafta, ev, dep, ev_gol=None, dep_gol=None, tarih="01.01.2027",
         saat="20:00", ev_id=1, dep_id=2):
    return {"hafta": hafta, "tarih": tarih, "saat": saat, "ev": ev,
            "deplasman": dep, "ev_kulup_id": ev_id, "deplasman_kulup_id": dep_id,
            "ev_gol": ev_gol, "deplasman_gol": dep_gol,
            "oynandi": ev_gol is not None, "mac_id": 1000 + hafta}


BIZ = 3601
PUAN = {
    "guncelleme": "2026-09-12T16:06:00+03:00", "bayat": False,
    "kaynak": {"ad": "Türkiye Futbol Federasyonu"},
    "takip": {
        "ad": "BURSASPOR", "kulup_id": BIZ, "sira": 2, "puan": 15, "oynadi": 6,
        "galibiyet": 5, "beraberlik": 0, "maglubiyet": 1, "averaj": 8,
        "attigi": 12, "yedigi": 4, "hafta": 7, "lig": "1lig",
        "lig_adi": "Trendyol 1. Lig", "grup_id": None, "grup_adi": None,
        "mac": _mac(7, "BURSASPOR", "EROKSPOR", tarih="13.09.2026", ev_id=BIZ, dep_id=964),
        "fikstur": [
            _mac(1, "BODRUM FK", "BURSASPOR", 0, 2, "09.08.2026", ev_id=5, dep_id=BIZ),
            _mac(2, "BURSASPOR", "IĞDIR FK", 1, 0, "15.08.2026", ev_id=BIZ, dep_id=6),
            _mac(3, "KARAGÜMRÜK", "BURSASPOR", 2, 1, "21.08.2026", ev_id=7, dep_id=BIZ),
            _mac(4, "KAYSERİSPOR", "BURSASPOR", 1, 1, "29.08.2026", ev_id=8, dep_id=BIZ),
            _mac(5, "BURSASPOR", "İSTANBULSPOR", 4, 0, "03.09.2026", ev_id=BIZ, dep_id=9),
            _mac(6, "MANİSA FK", "BURSASPOR", 1, 2, "07.09.2026", ev_id=10, dep_id=BIZ),
            _mac(7, "BURSASPOR", "EROKSPOR", tarih="13.09.2026", ev_id=BIZ, dep_id=964),
            _mac(8, "BATMAN PETROLSPOR", "BURSASPOR", tarih="19.09.2026", ev_id=11, dep_id=BIZ),
            _mac(9, "BURSASPOR", "MARDİN 1969", tarih="11.10.2026", saat="", ev_id=BIZ, dep_id=12),
        ],
    },
}


# Paket 12 Eylül 2026'da çekilmiş gibi kurulu; "sıradaki maç" ve maç durumu
# 19 Ekim 2026'dan beri BUGÜNE göre hesaplanıyor (`canli.mac_takvimi`), o
# yüzden gün sabitlenir. Bugünden bağımsız davranış `tests_canli`de.
GUN = mock.patch("icerik.canli.bugunun_tarihi", new=lambda: date(2026, 9, 12))


@GUN
class FiksturHazirlama(TestCase):

    def test_fikstur_yoksa_none(self):
        self.assertIsNone(bursaspor.fikstur_hazirla(None))
        self.assertIsNone(bursaspor.fikstur_hazirla({"takip": {"kulup_id": BIZ}}))
        self.assertIsNone(bursaspor.bolum_verisi(None))

    def test_sonuc_harfi_bizim_acidan(self):
        f = bursaspor.fikstur_hazirla(PUAN)
        # Deplasmanda 0-2 galibiyet, evde 1-0, deplasmanda 2-1 mağlubiyet,
        # 1-1 beraberlik, evde 4-0, deplasmanda 1-2 galibiyet.
        self.assertEqual([m["sonuc"] for m in f["maclar"][:6]],
                         ["G", "G", "M", "B", "G", "G"])
        self.assertEqual([m["sonuc"] for m in f["maclar"][6:]], ["", "", ""])

    def test_sonraki_ilk_oynanmamis_mac(self):
        f = bursaspor.fikstur_hazirla(PUAN)
        self.assertEqual(f["sonraki"]["hafta"], 7)
        self.assertTrue(f["sonraki"]["bizim_ev"])
        self.assertEqual(f["sonraki"]["rakip"], "EROKSPOR")
        self.assertEqual([m["hafta"] for m in f["son_maclar"]], [6, 5, 4])
        self.assertEqual([m["hafta"] for m in f["siradakiler"]], [7, 8, 9])
        self.assertEqual((f["oynanan"], f["toplam"]), (6, 9))

    def test_skor_olmayan_mac_sifir_sifir_sayilmaz(self):
        f = bursaspor.fikstur_hazirla(PUAN)
        self.assertFalse(f["maclar"][6]["skor_var"])
        self.assertIsNone(f["maclar"][6]["ev_gol"])

    def test_rakip_ev_ve_deplasmanda_dogru(self):
        f = bursaspor.fikstur_hazirla(PUAN)
        self.assertEqual(f["maclar"][0]["rakip"], "BODRUM FK")
        self.assertFalse(f["maclar"][0]["bizim_ev"])
        self.assertEqual(f["maclar"][1]["rakip"], "IĞDIR FK")
        self.assertTrue(f["maclar"][1]["bizim_ev"])


@GUN
class BursasporSayfasi(TestCase):

    @classmethod
    def setUpTestData(cls):
        from django.core.management import call_command
        call_command("taksonomi_kur", verbosity=0)
        cls.kategori = KategoriTur.objects.filter(
            tur=Kategori.TUR_HABER, slug="bursaspor").first().kategori
        Haber.objects.create(
            id=940000, slug="bs-0", baslik="Bursaspor'da rekabet arttı",
            govde="<p>Gövde</p>", kategori=cls.kategori, yayin_zamani=timezone.now())

    def _sayfa(self, yol="/bursaspor", puan=None):
        def sahte(bilesen):
            return {"puan-durumu": puan}.get(bilesen)
        with mock.patch.object(views, "oku", sahte):
            return self.client.get(yol)

    def test_fikstur_tablosu_ve_yesil_kabuk(self):
        metin = self._sayfa(puan=PUAN).content.decode()
        self.assertIn('<body data-bolum="bursaspor">', metin)
        # `puan-pencere` burada aranmıyor: sahte pakette `ligler` yok,
        # pencere sessizce çizilmiyor (tests_bolum_bloklari ile aynı durum).
        for parca in ("bs-fikstur", "FİKSTÜR VE SONUÇLAR", "6/9 maç oynandı",
                      'class="sonraki"', "mac-karti"):
            self.assertIn(parca, metin, parca)
        # Oynanmamış üç maç skor basmıyor; skorlar kaynaktaki yönüyle.
        self.assertEqual(metin.count('aria-label="oynanmadı"'), 3)
        self.assertIn("0&ndash;2", metin)
        self.assertIn('class="sonuc f-M"', metin)

    def test_kaldirilan_bloklar_geri_gelmedi(self):
        """Kullanıcı kararı (12 Eylül 2026): form şeridi, kadro, diziler,
        basketbol, künye, konu şeridi kalktı."""
        metin = self._sayfa(puan=PUAN).content.decode()
        for yok in ("form-seridi", "son-sonuclar", "bs-kadro", "bs-gazete",
                    "bs-basketbol", "bs-kunye", "bs-konular", "Hangi kanalda"):
            self.assertNotIn(yok, metin, yok)

    def test_fikstur_yokken_tablo_yok_kabuk_yesil_degil(self):
        """Fikstür gelmediyse `bursaspor` bağlamı None: tablo çizilmez,
        kabuk da lacivert-kırmızı kalır — yarım yeşil sayfa yok."""
        puan = {"takip": dict(PUAN["takip"], fikstur=[])}
        metin = self._sayfa(puan=puan).content.decode()
        self.assertNotIn("bs-fikstur", metin)
        self.assertNotIn('data-bolum="bursaspor"', metin)
        self.assertIn("mac-karti", metin)
        metin = self._sayfa().content.decode()
        self.assertNotIn("bs-fikstur", metin)
        self.assertNotIn("data-bolum", metin)

    def test_baska_bolumler_lacivert_kirmizi(self):
        for yol in ("/spor", "/gundem"):
            metin = self._sayfa(yol, puan=PUAN).content.decode()
            self.assertNotIn("bs-fikstur", metin, yol)
            self.assertNotIn("data-bolum", metin, yol)
            self.assertIn("<body>", metin, yol)

    def test_kural_sablonda_degil_gorunumde(self):
        kok = views.__file__.rsplit("icerik", 1)[0] + "sablonlar"
        with open(kok + "/parca/bolum/bursaspor.html", encoding="utf-8") as d:
            sablon = d.read()
        self.assertNotIn("slug ==", sablon)
        self.assertNotIn("kategori.slug", sablon)
        # Yeşil kabuk YALNIZ gövde niteliğiyle: her kural o seçicinin altında.
        with open(kok.replace("sablonlar", "statik/stil/site.css"), encoding="utf-8") as d:
            css = d.read()
        bolum = css.split("BURSASPOR BÖLÜM SAYFASI — 12 Eylül 2026", 1)[1]
        for satir in bolum.splitlines():
            if "--yesil" in satir and not satir.lstrip().startswith(("/*", "*", "`", "-")):
                self.assertTrue(satir.startswith('body[data-bolum="bursaspor"]'), satir)
