"""`panel_veri_al` ayıklama kurallarının gerileme testleri.

Gerçek döküm depoda değil (`C:\\Users\\Asus\\Downloads\\bursa_hakimiyet_panel`),
o yüzden testler dökümün **ölçülmüş biçimini** taklit eden küçük sayfalar
kurar. Taklit edilen şeyler tahmin değil, 29 Ağustos 2026'da dökümden
okunanlar:

* durum düğmesi kayıtın **şu anki** durumunu gösterir (`Aktif` / `Pasif`),
  arşiv düğmesi ise **eylemi** yazar (`Arşivden çıkar` = kayıt arşivde);
* kampanyanın yuva listesi hücrede kısaltılır ama tamamı `data-bs-title`
  ipucunda durur — kısalmış metni okumak yuva kaybettirir;
* DataTables'ın `1 - 25 / 131` satırı dökümün **eksik** olduğunu söyler.
"""

from __future__ import annotations

import tempfile
from io import StringIO
from pathlib import Path

from django.core.management import call_command
from django.test import TestCase

from .models import Bildirim, Gazete, ReklamKampanyasi, ReklamYuvasi, ResmiIlan

KABUK = """<html><body>
<div class="dt-info">1 - {gosterilen} / {toplam} arasındaki kayıtlar gösteriliyor</div>
<table>{satirlar}</table>
{ekler}
</body></html>"""


def _sayfa(basliklar, satirlar, gosterilen, toplam, ekler=""):
    bas = "<tr>" + "".join(f"<th>{b}</th>" for b in basliklar) + "</tr>"
    return KABUK.format(satirlar=bas + "".join(satirlar), gosterilen=gosterilen,
                        toplam=toplam, ekler=ekler)


AKTIF = '<button data-bs-title="Aktif"></button>'
PASIF = '<button data-bs-title="Pasif"></button>'
ARSIVDE = '<button data-bs-title="Arşivden çıkar"></button>'


class DokumAyiklama(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._gecici = tempfile.TemporaryDirectory()
        cls.kok = Path(cls._gecici.name)
        cls._dokum_kur()

    @classmethod
    def tearDownClass(cls):
        cls._gecici.cleanup()
        super().tearDownClass()

    @classmethod
    def _dokum_kur(cls):
        (cls.kok / "gazete.html").write_text(_sayfa(
            ["", "Başlık", "BIK Kodu", "İşlemler"],
            [f"<tr><td></td><td>BURSA HAKİMİYET</td><td>YYN-000132</td>"
             f"<td>{AKTIF}</td></tr>",
             f"<tr><td></td><td>AKŞAM</td><td>YYN-000867</td>"
             f"<td>{PASIF}</td></tr>"],
            2, 2), encoding="utf-8")

        (cls.kok / "ilan.html").write_text(_sayfa(
            ["", "ID", "Başlık", "İlan Türü", "Tarih", "Editör", "İşlemler"],
            [f"<tr><td></td><td>1718</td><td>YANGIN RAPORU İŞİ</td><td>İHALE</td>"
             f"<td>24-08-2026 00:00:00</td><td>Coşkun SAİTOĞLU</td>"
             f"<td>{ARSIVDE}</td></tr>",
             f"<tr><td></td><td>1712</td><td>TAŞINMAZ SATIŞI</td><td>TEBLİGAT</td>"
             f"<td>21-08-2026 00:00:00</td><td>Coşkun SAİTOĞLU</td>"
             f"<td>{PASIF}</td></tr>"],
            2, 2), encoding="utf-8")

        secim = ('<select><option>Reklam Alanı Seç</option>'
                 '<option>-Manşet yanı- 300x250</option>'
                 '<option>-Haber arası- 728*90</option>'
                 '<option>1000x940 mobil</option>'
                 '<option>hakimiyet</option>'
                 '<option>Bu alana reklam verebilirsiniz 970x250</option>'
                 '</select>')
        ipucu = ('<div data-bs-title="-Manşet yanı- 300x250 / '
                 '-Haber arası- 728*90">-Manşet yanı- 300x250 / -...</div>')
        (cls.kok / "kampanya.html").write_text(_sayfa(
            ["", "Başlık", "Fotoğraf", "Başlangıç / Bitiş Tarihi",
             "Reklam Alanı", "Editör", "İşlemler"],
            ['<tr><td></td><td><a href="advertisement_edit.php?id=530">'
             'Nilüfer Belediyesi 300*250</a></td><td>Kod Reklam</td>'
             '<td>07-08-2026 / 31-12-2026</td>'
             f'<td>{ipucu}</td><td>Coşkun SAİTOĞLU</td><td>{AKTIF}</td></tr>',
             '<tr><td></td><td><a href="advertisement_edit.php?id=531">'
             'Lösev 160*600</a></td><td></td><td>08-07-2026 / 01-12-2026</td>'
             f'<td>hakimiyet</td><td>Coşkun SAİTOĞLU</td><td>{PASIF}</td></tr>'],
            2, 131, ekler=secim), encoding="utf-8")

        (cls.kok / "bildirim.html").write_text(_sayfa(
            ["Tarih", "Veri Kaynağı", "Bildirim", "Yaklaşık Hedef Kişi",
             "Açan Kişi", "İşlemler"],
            ["<tr><td>2026-05-25 14:43:33</td><td>Makale</td>"
             "<td>BURSASPOR'UN TRANSFER HARİTASI</td><td>22683</td>"
             "<td>46</td><td></td></tr>"],
            1, 2208), encoding="utf-8")

    def _calistir(self, **ek):
        cikti = StringIO()
        call_command("panel_veri_al", dokum=str(self.kok), stdout=cikti,
                     stderr=StringIO(), **ek)
        return cikti.getvalue()

    # --- durum kodları -----------------------------------------------

    def test_gazete_durumu_dugmeden_okunuyor(self):
        self._calistir()
        self.assertTrue(Gazete.objects.get(ad="BURSA HAKİMİYET").aktif)
        self.assertFalse(Gazete.objects.get(ad="AKŞAM").aktif)

    def test_bizim_yayinimiz_bik_kodundan_isaretleniyor(self):
        self._calistir()
        self.assertTrue(Gazete.objects.get(bik_kodu="YYN-000132").bizim_mi)
        self.assertFalse(Gazete.objects.get(bik_kodu="YYN-000867").bizim_mi)

    def test_arsivden_cikar_dugmesi_arsiv_demek(self):
        """Eylem adı durum sanılırsa 23 ilan yanlış duruma yazılır."""
        self._calistir()
        self.assertEqual(ResmiIlan.objects.get(pk=1718).durum,
                         ResmiIlan.DURUM_ARSIV)
        self.assertEqual(ResmiIlan.objects.get(pk=1712).durum,
                         ResmiIlan.DURUM_PASIF)

    def test_ilan_kimligi_ve_turu_korunuyor(self):
        self._calistir()
        self.assertEqual(ResmiIlan.objects.get(pk=1718).tur, ResmiIlan.TUR_IHALE)
        self.assertEqual(ResmiIlan.objects.get(pk=1712).tur,
                         ResmiIlan.TUR_TEBLIGAT)
        self.assertEqual(str(ResmiIlan.objects.get(pk=1718).yayin_tarihi),
                         "2026-08-24")

    # --- yuva alanları -----------------------------------------------

    def test_yuva_olculeri_yildizli_yazimda_da_okunuyor(self):
        self._calistir()
        self.assertEqual(ReklamYuvasi.objects.get(ad="-Haber arası- 728*90").olcu,
                         "728x90")

    def test_ayristirilamayan_alan_bos_birakiliyor(self):
        """Uydurmak yerine boş: 50 yuvanın 29'unda konum yok."""
        self._calistir()
        yuva = ReklamYuvasi.objects.get(ad="hakimiyet")
        self.assertEqual(yuva.konum, "")
        self.assertIsNone(yuva.genislik)
        self.assertEqual(yuva.olcu, "")

    def test_yer_tutucu_isaretleniyor(self):
        self._calistir()
        self.assertTrue(ReklamYuvasi.objects.get(
            ad="Bu alana reklam verebilirsiniz 970x250").yer_tutucu_mu)
        self.assertFalse(ReklamYuvasi.objects.get(
            ad="-Manşet yanı- 300x250").yer_tutucu_mu)

    def test_cihaz_adda_yaziliysa_okunuyor(self):
        self._calistir()
        self.assertEqual(ReklamYuvasi.objects.get(ad="1000x940 mobil").cihaz,
                         ReklamYuvasi.CIHAZ_MOBIL)
        self.assertEqual(ReklamYuvasi.objects.get(ad="-Manşet yanı- 300x250").cihaz,
                         ReklamYuvasi.CIHAZ_HEPSI)

    # --- kampanya ↔ yuva ---------------------------------------------

    def test_kisalmis_yuva_listesi_ipucundan_tamamlaniyor(self):
        """Hücredeki '-...' okunursa kampanyanın ikinci yuvası kaybolur."""
        self._calistir()
        kampanya = ReklamKampanyasi.objects.get(pk=530)
        self.assertEqual(
            sorted(y.ad for y in kampanya.yuvalar.all()),
            ["-Haber arası- 728*90", "-Manşet yanı- 300x250"])

    def test_kampanya_tarihleri_ve_durumu(self):
        self._calistir()
        kampanya = ReklamKampanyasi.objects.get(pk=530)
        self.assertEqual(str(kampanya.baslangic), "2026-08-07")
        self.assertEqual(str(kampanya.bitis), "2026-12-31")
        self.assertEqual(kampanya.durum, ReklamKampanyasi.DURUM_AKTIF)
        self.assertEqual(ReklamKampanyasi.objects.get(pk=531).durum,
                         ReklamKampanyasi.DURUM_PASIF)

    def test_editor_adi_kullaniciya_baglanmiyor(self):
        """Döküm ad yazıyor; gerçek kullanıcı tablosu henüz göçmedi."""
        self._calistir()
        self.assertIsNone(ReklamKampanyasi.objects.get(pk=530).olusturan)
        self.assertIsNone(ResmiIlan.objects.get(pk=1718).olusturan)

    # --- rapor ve tekrar çalıştırma -----------------------------------

    def test_eksik_dokum_raporda_isaretleniyor(self):
        cikti = self._calistir(kuru=True)
        self.assertIn("131", cikti)
        self.assertIn("2208", cikti)
        self.assertIn("EKSİK", cikti)

    def test_kuru_kosu_yazmiyor(self):
        self._calistir(kuru=True)
        self.assertEqual(Gazete.objects.count(), 0)
        self.assertEqual(ReklamYuvasi.objects.count(), 0)

    def test_tekrar_calistirilabilir(self):
        self._calistir()
        sayilar = (Gazete.objects.count(), ResmiIlan.objects.count(),
                   ReklamYuvasi.objects.count(),
                   ReklamKampanyasi.objects.count(), Bildirim.objects.count())
        self._calistir()
        self.assertEqual(sayilar, (
            Gazete.objects.count(), ResmiIlan.objects.count(),
            ReklamYuvasi.objects.count(), ReklamKampanyasi.objects.count(),
            Bildirim.objects.count()))

    def test_bildirim_sayilari_okunuyor(self):
        self._calistir()
        bildirim = Bildirim.objects.get()
        self.assertEqual(bildirim.hedef_sayisi, 22683)
        self.assertEqual(bildirim.acan_sayisi, 46)
        self.assertAlmostEqual(bildirim.acilma_orani, 0.2028, places=3)
