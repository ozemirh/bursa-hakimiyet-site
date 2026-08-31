"""Nöbetçi eczane sayfaları ve günlük haber (URUN-PLANI.md §41).

Korunması gereken davranışlar:

1. **Kalıcı adres kalıcıdır.** `/nobetci-eczane` ve ilçe adresleri veri
   çekilemediğinde de 200 döner; 404 sayfayı dizinden düşürür.
2. **Uydurma yok.** Telefonu ya da konumu olmayan eczane yapısal veride o
   alan olmadan geçer; "bu ilçede bugün nöbetçi yok" cümlesi kaynağın
   döndürdüğüdür, boş sayfa değildir.
3. **Günlük haber tek kayıttır.** Komut aynı gün tekrar koşarsa ikinci
   kayıt açılmaz, var olan tazelenir ve yayın zamanı korunur.
4. **Bayat liste yayımlanmaz.** Nöbet günde bir devrediliyor; bir gün
   eski liste okuru kapalı eczaneye gönderir.
"""

import json
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

from django.core.management import call_command
from django.test import TestCase, override_settings

from icerik.canli import _bellek
from icerik.models import Haber

TR = timezone(timedelta(hours=3))

ECZANELER = [
    {"ad": "METROPOL ECZANESİ", "ilce": "NİLÜFER",
     "adres": "KONAK MAH. GÜLBİTEN SOK. NO:1A/A", "telefon": "0224 451 42 00",
     "enlem": 40.2095007, "boylam": 28.9912676,
     "nobet_baslangic": "2026-08-31T18:30", "nobet_bitis": "2026-09-01T08:30"},
    {"ad": "PANAYIR ECZANESİ", "ilce": "OSMANGAZİ - DEMİRTAŞ",
     "adres": "PANAYIR MAH. 1. SOK.", "telefon": "0224 220 10 10",
     "enlem": 40.19, "boylam": 29.12,
     "nobet_baslangic": "2026-08-31T18:00", "nobet_bitis": "2026-08-31T20:00"},
    {"ad": "ULUDAĞ ECZANESİ", "ilce": "OSMANGAZİ",
     "adres": "ALTIPARMAK CAD. NO:5", "telefon": "",
     "enlem": None, "boylam": None,
     "nobet_baslangic": "2026-08-31T18:30", "nobet_bitis": "2026-09-01T08:30"},
]


def paket(eczaneler=None, gun="2026-08-31", yas_dakika=5):
    guncelleme = datetime.now(TR) - timedelta(minutes=yas_dakika)
    return {
        "guncelleme": guncelleme.isoformat(),
        "bayat_esik_dakika": 1440,
        "gun": gun,
        "kaynak": {"ad": "Bursa Eczacı Odası", "kisa": "BEO"},
        "eczaneler": ECZANELER if eczaneler is None else eczaneler,
    }


class EczaneTabani(TestCase):

    @classmethod
    def setUpTestData(cls):
        call_command("taksonomi_kur", verbosity=0)

    def setUp(self):
        self.klasor = tempfile.TemporaryDirectory()
        self.kok = Path(self.klasor.name)
        _bellek.clear()

    def tearDown(self):
        self.klasor.cleanup()
        _bellek.clear()

    def _yaz(self, veri):
        (self.kok / "nobetci-eczane.json").write_text(
            json.dumps(veri, ensure_ascii=False), encoding="utf-8")
        _bellek.clear()

    def _al(self, yol):
        with override_settings(CANLI_VERI_KOK=self.kok):
            yanit = self.client.get(yol)
        _bellek.clear()
        return yanit

    def _komut(self, **kwarg):
        from io import StringIO
        cikti = StringIO()
        with override_settings(CANLI_VERI_KOK=self.kok):
            try:
                call_command("eczane_haberi", stdout=cikti, stderr=cikti,
                             **kwarg)
                kod = 0
            except SystemExit as e:
                kod = e.code
        _bellek.clear()
        return kod, cikti.getvalue()


class EczaneSayfasi(EczaneTabani):

    def test_bursa_geneli_butun_eczaneleri_basiyor(self):
        self._yaz(paket())
        yanit = self._al("/nobetci-eczane")
        self.assertEqual(yanit.status_code, 200)
        for ad in ("Metropol Eczanesi", "Panayır Eczanesi", "Uludağ Eczanesi"):
            self.assertContains(yanit, ad)

    def test_ilce_sayfasi_yalniz_o_ilceyi_basiyor(self):
        """Demirtaş ayrı nöbet bölgesi ama Osmangazi sayfasına girer."""
        self._yaz(paket())
        yanit = self._al("/nobetci-eczane/osmangazi")
        self.assertContains(yanit, "Panayır Eczanesi")
        self.assertContains(yanit, "Uludağ Eczanesi")
        self.assertNotContains(yanit, "Metropol Eczanesi")

    def test_baslik_ve_aciklama_yer_ve_tarih_tasiyor(self):
        self._yaz(paket())
        yanit = self._al("/nobetci-eczane/nilufer")
        self.assertContains(
            yanit, "<title>Nilüfer Nöbetçi Eczaneler — 31 Ağustos 2026 "
                   "| Bursa Hakimiyet</title>")
        self.assertContains(yanit, "31 Ağustos 2026 Nilüfer nöbetçi eczaneler: "
                                   "1 eczanenin adresi")

    def test_kanonik_adres_kendisini_gosteriyor(self):
        self._yaz(paket())
        yanit = self._al("/nobetci-eczane/osmangazi")
        self.assertContains(yanit, 'rel="canonical"')
        self.assertContains(yanit, "/nobetci-eczane/osmangazi\">")

    def test_veri_yoksa_sayfa_yine_200(self):
        """Adres arama motoruna kayıtlı; bir tur kaçtı diye 404 verilmez."""
        yanit = self._al("/nobetci-eczane")
        self.assertEqual(yanit.status_code, 200)
        self.assertContains(yanit, "Nöbetçi eczane listesi şu an alınamıyor")

    def test_bilinmeyen_ilce_404(self):
        self._yaz(paket())
        self.assertEqual(self._al("/nobetci-eczane/ankara").status_code, 404)

    def test_nobetcisi_olmayan_ilce_bos_sayfa_degil(self):
        """Kaynak o ilçe için kayıt döndürmediyse cümle böyle kurulur."""
        self._yaz(paket())
        yanit = self._al("/nobetci-eczane/keles")
        self.assertEqual(yanit.status_code, 200)
        self.assertContains(yanit, "Keles ilçesinde nöbetçi eczane görünmüyor")

    def test_serit_17_ilcenin_tamamini_tasiyor(self):
        """Okur kendi ilçesini bulamazsa sayfayı eksik sanar."""
        self._yaz(paket())
        icerik = self._al("/nobetci-eczane").content.decode()
        for slug in ("osmangazi", "nilufer", "keles", "harmancik", "iznik"):
            self.assertIn(f'href="/nobetci-eczane/{slug}"', icerik)

    def test_serit_turkce_siralanmis(self):
        """`sorted` varsayılanı İnegöl ve İznik'i en sona atıyordu."""
        icerik = self._al("/nobetci-eczane").content.decode()
        sira = [p.split('"')[0] for p in
                icerik.split('href="/nobetci-eczane/')[1:]]
        temiz = []
        for s in sira:                       # şerit + bölüm başlıkları
            if s not in temiz:
                temiz.append(s)
        self.assertLess(temiz.index("inegol"), temiz.index("karacabey"))
        self.assertGreater(temiz.index("inegol"), temiz.index("harmancik"))

    def test_telefon_ve_konum_baglantilari(self):
        self._yaz(paket())
        yanit = self._al("/nobetci-eczane/nilufer")
        self.assertContains(yanit, 'href="tel:+902244514200"')
        self.assertContains(yanit, "query=40.2095007,28.9912676")

    def test_kaynak_her_sayfada_yaziyor(self):
        self._yaz(paket())
        for yol in ("/nobetci-eczane", "/nobetci-eczane/osmangazi"):
            self.assertContains(self._al(yol), "Bursa Eczacı Odası")


class EczaneYapisalVeri(EczaneTabani):

    def _ld(self, yol):
        icerik = self._al(yol).content.decode()
        ham = icerik.split('type="application/ld+json">')[1].split("</script>")[0]
        return json.loads(ham)

    def test_liste_ogeleri_eczane_olarak_isaretli(self):
        self._yaz(paket())
        ld = self._ld("/nobetci-eczane/nilufer")
        self.assertEqual(ld["@type"], "ItemList")
        self.assertEqual(ld["numberOfItems"], 1)
        self.assertEqual(ld["itemListElement"][0]["item"]["@type"], "Pharmacy")

    def test_olmayan_alan_yapisal_veriye_yazilmiyor(self):
        """Telefonu ve konumu olmayan eczanede o anahtarlar hiç açılmaz."""
        self._yaz(paket())
        ogeler = {o["item"]["name"]: o["item"]
                  for o in self._ld("/nobetci-eczane/osmangazi")["itemListElement"]}
        self.assertNotIn("telephone", ogeler["Uludağ Eczanesi"])
        self.assertNotIn("geo", ogeler["Uludağ Eczanesi"])
        self.assertIn("telephone", ogeler["Panayır Eczanesi"])

    def test_ad_turkce_bicimde(self):
        """Python'un `.title()`ı "ECZANESİ"yi "Eczanesi̇" yapıyordu."""
        self._yaz(paket())
        adlar = [o["item"]["name"]
                 for o in self._ld("/nobetci-eczane/nilufer")["itemListElement"]]
        self.assertEqual(adlar, ["Metropol Eczanesi"])

    def test_veri_yokken_yapisal_veri_basilmiyor(self):
        self.assertNotContains(self._al("/nobetci-eczane"),
                               "application/ld+json")


class EczaneHaberi(EczaneTabani):

    def test_haber_aciliyor(self):
        self._yaz(paket())
        kod, _ = self._komut()
        self.assertEqual(kod, 0)
        haber = Haber.objects.get(slug="31-agustos-2026-bursa-nobetci-eczaneler")
        self.assertEqual(haber.durum, Haber.DURUM_AKTIF)
        self.assertEqual(haber.kaynak_turu, Haber.KAYNAK_DIS_YAYIN)
        self.assertIn("31 Ağustos 2026", haber.baslik)
        self.assertEqual([k.ad for k in haber.kaynaklar.all()],
                         ["Bursa Eczacı Odası"])

    def test_govde_butun_eczaneleri_ve_kaynagi_tasiyor(self):
        self._yaz(paket())
        self._komut()
        govde = Haber.objects.get(
            slug="31-agustos-2026-bursa-nobetci-eczaneler").govde
        for ad in ("Metropol Eczanesi", "Panayır Eczanesi", "Uludağ Eczanesi"):
            self.assertIn(ad, govde)
        self.assertIn("Bursa Eczacı Odası", govde)
        # Kalıcı sayfaya ve ilçe sayfalarına bağlanır.
        self.assertIn('href="/nobetci-eczane"', govde)
        self.assertIn('href="/nobetci-eczane/osmangazi"', govde)
        # Telefonu olmayan eczanede "Tel:" satırı hiç yazılmaz.
        self.assertNotIn("Uludağ Eczanesi</strong> — ALTIPARMAK CAD. NO:5 — Tel:",
                         govde)

    def test_ikinci_kosu_ikinci_kayit_acmiyor(self):
        self._yaz(paket())
        self._komut()
        ilk = Haber.objects.get(slug="31-agustos-2026-bursa-nobetci-eczaneler")
        self._yaz(paket(eczaneler=ECZANELER[:1]))
        self._komut()
        self.assertEqual(Haber.objects.filter(
            slug="31-agustos-2026-bursa-nobetci-eczaneler").count(), 1)
        yeni = Haber.objects.get(pk=ilk.pk)
        self.assertNotIn("Panayır Eczanesi", yeni.govde)
        # Yayın zamanı korunur: haber sabah yayımlandı, tazeleme onu öne
        # çekmemeli.
        self.assertEqual(yeni.yayin_zamani, ilk.yayin_zamani)

    def test_veri_yoksa_yayimlanmiyor(self):
        kod, cikti = self._komut()
        self.assertEqual(kod, 1)
        self.assertEqual(Haber.objects.filter(
            slug__endswith="bursa-nobetci-eczaneler").count(), 0)
        self.assertIn("eczane verisi yok", cikti)

    def test_bayat_liste_yayimlanmiyor(self):
        """Nöbet günde bir devrediliyor; dünün listesi yanlış eczaneyi gösterir."""
        self._yaz(paket(yas_dakika=3000))
        kod, cikti = self._komut()
        self.assertEqual(kod, 1)
        self.assertIn("bayat", cikti)
        self.assertEqual(Haber.objects.count(), 0)

        kod, _ = self._komut(bayat_da_yayimla=True)
        self.assertEqual(kod, 0)
        self.assertEqual(Haber.objects.count(), 1)

    def test_istenen_gun_dosyadakinden_farkliysa_yayimlanmiyor(self):
        """Dünün listesini bugünün haberi diye yayımlamak okuru yanıltır."""
        self._yaz(paket())
        kod, _ = self._komut(gun="2026-09-01")
        self.assertEqual(kod, 1)
        self.assertEqual(Haber.objects.count(), 0)

    def test_kuru_calisma_yazmiyor(self):
        self._yaz(paket())
        kod, cikti = self._komut(kuru=True)
        self.assertEqual(kod, 0)
        self.assertIn("KURU ÇALIŞMA", cikti)
        self.assertEqual(Haber.objects.count(), 0)

    def test_haber_sayfasi_aciliyor(self):
        self._yaz(paket())
        self._komut()
        haber = Haber.objects.get(slug="31-agustos-2026-bursa-nobetci-eczaneler")
        yanit = self.client.get(haber.get_absolute_url())
        self.assertEqual(yanit.status_code, 200)
        self.assertContains(yanit, "Metropol Eczanesi")
