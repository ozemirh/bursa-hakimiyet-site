"""Kalıcı enstrüman sayfaları — /piyasa/dolar · /piyasa/euro · /piyasa/gram-altin.

20 Ekim 2026. Korunan sözleşme (`icerik/piyasa.py`):

1. **Adres.** Üç kalıcı adres; `/{kategori}/{slug}-{id}` haber kalıbıyla
   çakışmaz, bilinmeyen enstrüman 404, sondaki eğik çizgi 301 (Paket G).
2. **Bayatlık.** Bayat veri gizlenmez: değer basılır, ÜSTÜNDE tarihli
   "GÜNCEL DEĞİL" uyarısı (`canli.tazelik`). Kaynak ve veri zamanı her zaman
   görünür.
3. **Eksik alan çizilmez.** Alış/satış, değişim, resmî kapanış, geçmiş:
   kaynakta yoksa satır da yok. Veri hiç yoksa sayfa 200 ve rakam yok.
4. **Bağlantılar.** Döviz bandı, piyasa cetveli ve servis paneli sayfası
   olan kalemi bağlar; sayfa ekonomi bölümünün son haberlerini listeler.
5. **Sorgu.** Sayfanın kendi sorgusu sabit; haber sayısıyla büyümez.
6. **Grafik.** Yalnız kaynağı yazılı geçmiş seride; `role="img"` + başlık
   ve açıklama; eksen yazıları ve kaynak görünür.

Testler geçici klasördeki FIXTURE dosyalarıyla çalışır.
"""

import json
import re
import shutil
import tempfile
from datetime import timedelta
from pathlib import Path

from django.db import connection
from django.test import TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import resolve
from django.utils import timezone

from taksonomi.models import Kategori, KategoriTur

from . import canli, piyasa, views
from .models import Haber

BAYAT_DAMGA = "2026-09-12T21:57:07+03:00"


def _damga(dakika_once=0):
    return (timezone.now() - timedelta(minutes=dakika_once)).astimezone().isoformat(
        timespec="seconds")


def _doviz(guncelleme=BAYAT_DAMGA, **degisiklik):
    """`canli-veri/doviz.py` çıktısının küçültülmüş hâli (12 Eylül 2026 koşusu)."""
    kalemler = {
        "dolar": {"anahtar": "dolar", "ad": "Dolar", "birim": "TL", "deger": 48.525,
                  "alis": 48.4305, "satis": 48.5178, "degisim": 0.0, "degisim_yuzde": 0.0,
                  "yon": "esit", "kaynak": "doviz", "kaynak_durumu": "taze",
                  "piyasa_damgasi": "2026-09-12T21:57:05+03:00"},
        "euro": {"anahtar": "euro", "ad": "Euro", "birim": "TL", "deger": 56.3246,
                 "alis": 56.1754, "satis": 56.2766, "degisim": -0.1695,
                 "degisim_yuzde": -0.3, "yon": "asagi", "kaynak": "doviz",
                 "kaynak_durumu": "taze", "piyasa_damgasi": "2026-09-12T21:57:05+03:00"},
        "sterlin": {"anahtar": "sterlin", "ad": "Sterlin", "birim": "TL", "deger": 65.7182,
                    "alis": 65.3215, "satis": 65.6621, "kaynak": "TCMB",
                    "kaynak_durumu": "taze"},
        "gram_altin": {"anahtar": "gram_altin", "ad": "Gram altın", "birim": "TL",
                       "deger": 6784.88, "alis": None, "satis": None, "degisim": 48.5,
                       "degisim_yuzde": 0.72, "yon": "yukari", "kaynak": "doviz",
                       "kaynak_durumu": "taze",
                       "piyasa_damgasi": "2026-09-12T21:57:05+03:00"},
        "bist100": {"anahtar": "bist100", "ad": "BIST 100", "birim": "puan",
                    "deger": 14467.25, "kaynak": "doviz", "kaynak_durumu": "taze"},
    }
    for anahtar, alanlar in degisiklik.items():
        if alanlar is None:
            kalemler.pop(anahtar)
        else:
            kalemler[anahtar] = {**kalemler[anahtar], **alanlar}
    return {"guncelleme": guncelleme, "bayat_esik_dakika": 1440,
            "kaynak": {"ad": "Türkiye Cumhuriyet Merkez Bankası", "kisa": "TCMB",
                       "kunye": "Kaynak: TCMB döviz kurları."},
            "bulten": {"tarih": "11.09.2026", "tarih_iso": "2026-09-11", "no": "2026/171"},
            "kalemler": list(kalemler.values())}


PIYASA = {
    "guncelleme": "2026-09-12T21:57:05+03:00", "bayat_esik_dakika": 45,
    "kaynak": [{"anahtar": "evds", "kisa": "TCMB EVDS", "ad": "TCMB EVDS"},
               {"anahtar": "doviz", "kisa": "doviz.com", "ad": "doviz.com"}],
    "kalemler": [],
    "capraz_kontrol": {"resmi_kapanis_piyasa_farki": [
        {"kalem": "gram_altin", "resmi_kapanis": 6808.7, "resmi_kaynak": "evds",
         "resmi_seri": "TP.ALTINPIYASA.KAP02", "resmi_tarih": "11-09-2026",
         "piyasa": 6784.88, "piyasa_kaynak": "doviz"}]},
}

# Geçmiş seri: hafta sonu boşluklu, beş iş günü.
GECMIS = [{"tarih": "2026-09-07", "deger": 48.31}, {"tarih": "2026-09-08", "deger": 48.40},
          {"tarih": "2026-09-09", "deger": 48.38}, {"tarih": "2026-09-10", "deger": 48.47},
          {"tarih": "2026-09-11", "deger": 48.5178}]


class PiyasaTesti(TestCase):

    @classmethod
    def setUpTestData(cls):
        from django.core.management import call_command
        call_command("taksonomi_kur", verbosity=0)
        tur = lambda s: KategoriTur.objects.filter(tur=Kategori.TUR_HABER, slug=s).first().kategori
        cls.ekonomi, cls.gundem = tur("ekonomi"), tur("gundem")
        simdi = timezone.now()
        for n in range(3):
            Haber.objects.create(id=960100 + n, slug=f"faiz-{n}", baslik=f"Faiz kararı {n}",
                                 govde="<p>g</p>", kategori=cls.ekonomi,
                                 yayin_zamani=simdi - timedelta(hours=n + 1))
        Haber.objects.create(id=960200, slug="gundem-haberi", baslik="Gündem haberi",
                             govde="<p>g</p>", kategori=cls.gundem, yayin_zamani=simdi)

    def setUp(self):
        self.kok = Path(tempfile.mkdtemp(prefix="bh-piyasa-"))
        canli._bellek.clear()

    def tearDown(self):
        shutil.rmtree(self.kok, ignore_errors=True)
        canli._bellek.clear()

    def yaz(self, ad, veri):
        (self.kok / f"{ad}.json").write_text(json.dumps(veri, ensure_ascii=False),
                                              encoding="utf-8")

    def iste(self, yol, durum=200):
        canli._bellek.clear()
        with override_settings(CANLI_VERI_KOK=self.kok):
            yanit = self.client.get(yol)
        self.assertEqual(yanit.status_code, durum, yol)
        return yanit

    def sayfa(self, yol="/piyasa/dolar"):
        return self.iste(yol).content.decode()

    @staticmethod
    def icerik(metin):
        return metin.split('id="ana-icerik"', 1)[1].split("</main>", 1)[0]


class Adres(PiyasaTesti):

    def test_uc_kalici_adres(self):
        self.yaz("doviz", _doviz())
        for slug, h1 in (("dolar", "DOLAR KAÇ TL?"), ("euro", "EURO KAÇ TL?"),
                         ("gram-altin", "GRAM ALTIN KAÇ TL?")):
            self.assertEqual(resolve(f"/piyasa/{slug}").url_name, "piyasa")
            metin = self.sayfa(f"/piyasa/{slug}")
            self.assertIn(f'<h1 id="piyasa-baslik">{h1}</h1>', metin)
            self.assertEqual(metin.count("<h1"), 1)
            self.assertIn('<body data-bolum="ekonomi">', metin)

    def test_bilinmeyen_enstruman_ve_kok_404(self):
        for yol in ("/piyasa/sterlin", "/piyasa/bist100", "/piyasa", "/piyasa/dolar/ek"):
            self.iste(yol, 404)

    def test_sondaki_egik_cizgi_301(self):
        yanit = self.iste("/piyasa/dolar/?utm_source=x", 301)
        self.assertEqual(yanit["Location"], "/piyasa/dolar?utm_source=x")

    def test_haber_kalibiyla_cakismaz(self):
        """`/{kategori}/{slug}-{id}` sondaki sayıyı ister: enstrüman adı
        taşıyan haber adresi haber görünümüne gider, enstrüman adresi
        haber kalıbına düşmez."""
        haber = Haber.objects.create(id=960300, slug="dolar", baslik="Dolar rekor kırdı",
                                     govde="<p>g</p>", kategori=self.ekonomi,
                                     yayin_zamani=timezone.now())
        self.assertEqual(haber.get_absolute_url(), "/ekonomi/dolar-960300")
        self.assertEqual(resolve("/ekonomi/dolar-960300").url_name, "haber")
        self.assertEqual(resolve("/piyasa/dolar-960300").url_name, "haber")
        self.assertIn("Dolar rekor kırdı", self.sayfa("/ekonomi/dolar-960300"))
        self.assertNotEqual(resolve("/piyasa/euro").url_name, "haber")
        self.assertNotEqual(resolve("/piyasa/gram-altin").url_name, "kategori")

    def test_adres_tek_kayittan(self):
        self.assertEqual(piyasa.adres("dolar"), "/piyasa/dolar")
        self.assertEqual(piyasa.adres("gram_altin"), "/piyasa/gram-altin")
        self.assertEqual(piyasa.adres("sterlin"), "")
        self.assertEqual(piyasa.adres(""), "")


class Bayatlik(PiyasaTesti):

    def test_bayat_veri_tarihle_ve_uyariyla_basilir(self):
        self.yaz("doviz", _doviz(BAYAT_DAMGA))
        metin = self.icerik(self.sayfa())
        self.assertIn("GÜNCEL DEĞİL.", metin)
        self.assertIn("12 Eylül 2026, 21:57</time> tarihli", metin)
        # Değer gizlenmez ve uyarı değerin ÜSTÜNDE.
        self.assertIn(">48,5250</data>", metin)
        self.assertLess(metin.index("GÜNCEL DEĞİL"), metin.index(">48,5250<"))
        # Çevirici de bayat değeri kullandığını söyler.
        self.assertIn("bu değer güncel değil", metin)

    def test_taze_veride_uyari_yok(self):
        self.yaz("doviz", _doviz(_damga(3)))
        metin = self.icerik(self.sayfa())
        self.assertNotIn("GÜNCEL DEĞİL", metin)
        self.assertNotIn("güncel değil", metin)
        self.assertIn(">48,5250</data>", metin)

    def test_kaynak_ve_zaman_her_zaman_gorunur(self):
        self.yaz("doviz", _doviz(_damga(3)))
        self.yaz("piyasa", PIYASA)
        metin = self.icerik(self.sayfa())
        self.assertIn("Kaynak: <b>doviz.com</b>", metin)
        self.assertIn('datetime="2026-09-12T21:57:05+03:00">12 Eylül 2026, 21:57:05</time>', metin)
        self.assertIn("TCMB bülteni", metin)
        self.assertIn("2026/171", metin)
        self.assertIn('href="/veri-kaynaklari"', metin)

    def test_tcmb_kaynakli_deger_bulten_gunuyle(self):
        self.yaz("doviz", _doviz(_damga(3), dolar={
            "deger": 48.5178, "kaynak": "TCMB", "kaynak_durumu": "taze",
            "degisim_yuzde": 0.1, "degisim": 0.0485, "yon": "yukari"}))
        metin = self.icerik(self.sayfa())
        self.assertIn("Kaynak: <b>TCMB</b>", metin)
        self.assertIn('<time datetime="2026-09-11">11 Eylül 2026</time>', metin)
        self.assertIn("bir önceki TCMB bültenine göre", metin)

    def test_piyasa_dosyasi_yoksa_kaynak_adi_yedekten(self):
        self.yaz("doviz", _doviz(_damga(3)))
        self.assertIn("Kaynak: <b>doviz.com</b>", self.icerik(self.sayfa()))


class EksikAlan(PiyasaTesti):

    def test_alis_satis_yalniz_tcmb_kaleminde(self):
        self.yaz("doviz", _doviz())
        self.assertIn("TCMB döviz alış", self.icerik(self.sayfa("/piyasa/dolar")))
        altin = self.icerik(self.sayfa("/piyasa/gram-altin"))
        self.assertNotIn("TCMB döviz", altin)
        self.assertNotIn("Alış", altin)
        # TCMB künyesi altına yapışmaz: gram altın TCMB'den gelmiyor.
        self.assertNotIn("Kaynak: TCMB döviz kurları", altin)

    def test_resmi_kapanis_yalniz_kaynakta_varsa(self):
        self.yaz("doviz", _doviz())
        self.assertNotIn("Resmî kapanış", self.icerik(self.sayfa("/piyasa/gram-altin")))
        self.yaz("piyasa", PIYASA)
        metin = self.icerik(self.sayfa("/piyasa/gram-altin"))
        self.assertIn("Resmî kapanış", metin)
        self.assertIn("6.808,70", metin)
        self.assertIn("11 Eylül 2026", metin)
        self.assertNotIn("Resmî kapanış", self.icerik(self.sayfa("/piyasa/dolar")))

    def test_degisim_yoksa_satir_yok(self):
        self.yaz("doviz", _doviz(euro={"degisim_yuzde": None, "degisim": None, "yon": ""}))
        metin = self.icerik(self.sayfa("/piyasa/euro"))
        self.assertNotIn("piyasa-fark", metin)
        self.assertIn(">56,3246</data>", metin)

    def test_degisim_yonu_ve_fiili(self):
        self.yaz("doviz", _doviz())
        metin = self.icerik(self.sayfa("/piyasa/euro"))
        self.assertIn('class="piyasa-fark azaliyor"', metin)
        self.assertIn("%0,30 (−0,1695 ₺)", metin)
        self.assertIn('<span class="gorsel-gizli"> geriledi</span>', metin)
        # Değişmeyen kalemde sıfır tutar basılmaz, renk yok, fiil "değişmedi".
        dolar = self.icerik(self.sayfa("/piyasa/dolar"))
        self.assertIn('<p class="piyasa-fark"><span aria-hidden="true">&ndash;</span> %0,00<span', dolar)
        self.assertNotIn("(0,0000", dolar)
        self.assertIn("değişmedi", dolar)

    def test_deger_yoksa_rakam_ve_cevirici_yok(self):
        self.yaz("doviz", _doviz(gram_altin={"deger": None, "kaynak": "",
                                             "kaynak_durumu": "yok"}))
        metin = self.icerik(self.sayfa("/piyasa/gram-altin"))
        self.assertIn("kaynaktan değer gelmedi", metin)
        self.assertNotIn("<data", metin)
        self.assertNotIn("ÇEVİRİCİ", metin)

    def test_dosya_yoksa_200_ve_rakam_yok(self):
        metin = self.icerik(self.sayfa("/piyasa/dolar"))
        self.assertIn("verisi şu an alınamıyor", metin)
        self.assertNotIn("<data", metin)
        self.assertNotIn("GÜNCEL DEĞİL", metin)
        self.assertNotIn("ÇEVİRİCİ", metin)

    def test_kalem_dosyada_yoksa_200(self):
        self.yaz("doviz", _doviz(euro=None))
        self.assertIn("verisi şu an alınamıyor", self.icerik(self.sayfa("/piyasa/euro")))

    def test_gecmis_yoksa_bolum_yok(self):
        self.yaz("doviz", _doviz())
        metin = self.icerik(self.sayfa())
        self.assertNotIn("GEÇMİŞ", metin)
        self.assertNotIn("<svg", metin)

    def test_kaynagi_yazilmamis_gecmis_basilmaz(self):
        self.yaz("doviz", _doviz(dolar={"gecmis": GECMIS}))
        metin = self.icerik(self.sayfa())
        self.assertNotIn("GEÇMİŞ", metin)
        self.assertNotIn("<svg", metin)

    def test_elle_giris_kaynak_olarak_soylenir(self):
        self.yaz("doviz", _doviz(gram_altin={
            "deger": 6800.0, "kaynak": "Bursa Kuyumcular Odası", "kaynak_durumu": "elle",
            "girildi": "2026-09-12", "degisim_yuzde": None, "piyasa_damgasi": None}))
        metin = self.icerik(self.sayfa("/piyasa/gram-altin"))
        self.assertIn("Bursa Kuyumcular Odası (panelden girildi)", metin)
        self.assertIn('<time datetime="2026-09-12">12 Eylül 2026</time>', metin)


class Baglantilar(PiyasaTesti):

    def test_anasayfa_bandi_baglar(self):
        self.yaz("doviz", _doviz())
        metin = self.sayfa("/")
        bant = metin.split('class="doviz-ic"', 1)[1].split("</dl>", 1)[0]
        for adres, ad in (("/piyasa/dolar", "Dolar"), ("/piyasa/euro", "Euro"),
                          ("/piyasa/gram-altin", "Gram altın")):
            self.assertIn(f'<dt><a href="{adres}">{ad}</a></dt>', bant)
        self.assertIn("<dt>Sterlin</dt>", bant)
        self.assertIn("<dt>BIST 100</dt>", bant)

    def test_ekonomi_cetveli_baglar(self):
        self.yaz("doviz", _doviz())
        metin = self.sayfa("/ekonomi")
        cetvel = metin.split("piyasa-cetveli", 1)[1].split("</table>", 1)[0]
        self.assertIn('<th scope="row"><a href="/piyasa/dolar">Dolar</a>', cetvel)
        self.assertIn('<th scope="row"><a href="/piyasa/gram-altin">Gram altın</a>', cetvel)
        self.assertIn('<th scope="row">Sterlin', cetvel)

    def test_servis_paneli_baglar(self):
        """Tema kalkarsa dönülen varsayılan panel de aynı bağı taşır."""
        from django.template.loader import render_to_string
        canli._bellek.clear()
        self.yaz("doviz", _doviz())
        with override_settings(CANLI_VERI_KOK=self.kok):
            metin = render_to_string("parca/bolum_servis.html",
                                     {"servis": {"tur": "doviz", "doviz": canli.oku("doviz")}})
        self.assertIn('<span class="ad"><a href="/piyasa/euro">Euro</a></span>', metin)
        self.assertIn('<span class="ad">Sterlin</span>', metin)

    def test_ekonomi_haberleri_ve_diger_sayfalar(self):
        self.yaz("doviz", _doviz())
        metin = self.icerik(self.sayfa("/piyasa/dolar"))
        liste = metin.split("EKONOMİDEN SON HABERLER", 1)[1].split("</section>", 1)[0]
        self.assertIn("Faiz kararı 0", liste)
        self.assertIn('href="/ekonomi/faiz-0-960100"', liste)
        self.assertNotIn("Gündem haberi", liste)
        self.assertIn('href="/ekonomi"', liste)
        diger = metin.split("DİĞER PİYASA SAYFALARI", 1)[1].split("</nav>", 1)[0]
        self.assertIn('href="/piyasa/euro"', diger)
        self.assertIn('href="/piyasa/gram-altin"', diger)
        self.assertNotIn('href="/piyasa/dolar"', diger)
        self.assertIn('<a href="/ekonomi">Ekonomi</a>', metin)  # kırıntı

    def test_href_diyez_yok(self):
        self.yaz("doviz", _doviz())
        self.assertNotIn('href="#"', self.icerik(self.sayfa()))


class CetvelKunyesi(PiyasaTesti):
    """Ekonomi cetvelinin künyesi sütun sütun kaynağı adlandırır (20 Ekim 2026).

    Kusur: künye yalnız "TCMB bülteni … Kaynak: TCMB döviz kurları"
    diyordu; "Son" sütunu ise canlı kaynak tazeyken doviz.com değeriydi
    (`canli-veri/doviz.py`: canlı değer `deger`i ezer, alış/satış TCMB'de
    kalır). Fixture karışık: dolar/euro/altın/BIST doviz.com, sterlin TCMB.
    """

    def kunye(self, yol="/ekonomi"):
        self.yaz("doviz", _doviz())
        self.yaz("piyasa", PIYASA)
        metin = self.sayfa(yol)
        bolum = metin.split("piyasa-cetveli", 1)[1].split("</section>", 1)[0]
        return bolum, bolum.split('class="servis-kunye"', 1)[1].split("</p>", 1)[0]

    def test_iki_kaynak_da_adlandirilir(self):
        bolum, kunye = self.kunye()
        # Son değer: canlı kaynak, adı ve zamanıyla.
        self.assertIn("Son ve değişim: doviz.com, "
                      '<time datetime="2026-09-12T21:57:05+03:00">12 Eylül 2026 21:57</time>'
                      " (Dolar, Euro, Gram altın)", kunye)
        # BIST 100'ün damgası yok: kaynak yine adlandırılır, zaman uydurulmaz.
        self.assertIn("Son ve değişim: doviz.com (BIST 100)", kunye)
        # TCMB'den gelen son değer de kendi adıyla ve bülten günüyle.
        self.assertIn('Son ve değişim: TCMB, <time datetime="2026-09-11">11 Eylül 2026</time>'
                      ", döviz satış kuru, gösterge niteliğinde (Sterlin)", kunye)
        # Alış/satış her zaman TCMB bülteni: gün ve numarasıyla.
        self.assertIn('Alış ve satış: TCMB bülteni <time datetime="2026-09-11">11 Eylül 2026'
                      "</time> &middot; 2026/171", kunye)
        # Değişimin neye göre olduğu kaynağa göre söylenir.
        self.assertIn("değişim doviz.com kaynağının bildirdiği günlük değişim", kunye)
        self.assertIn("değişim bir önceki TCMB bültenine göre", kunye)
        # Bütün tabloyu TCMB'ye atfeden eski cümleler yok.
        self.assertNotIn("Kaynak: TCMB döviz kurları", bolum)
        self.assertNotIn("Değişim bir önceki bültene göre", bolum)
        # Başlık çubuğu iki kaynağı da sayar.
        self.assertIn("doviz.com · TCMB &middot; <a href=\"/veri-kaynaklari\">", bolum)

    def test_canli_kaynak_yokken_hepsi_tcmb(self):
        tcmb = {"kaynak": "TCMB", "piyasa_damgasi": None}
        self.yaz("doviz", _doviz(dolar=tcmb, euro=tcmb, gram_altin=None, bist100=None))
        metin = self.sayfa("/ekonomi")
        kunye = metin.split("piyasa-cetveli", 1)[1].split('class="servis-kunye"', 1)[1]
        kunye = kunye.split("</p>", 1)[0]
        self.assertIn("Son ve değişim: TCMB, ", kunye)
        self.assertIn("(Dolar, Euro, Sterlin)", kunye)
        self.assertNotIn("doviz.com", kunye)

    def test_veri_tek_yerden(self):
        """Cetvel ile enstrüman sayfası aynı rakamı farklı kaynağa atfedemez."""
        doviz = _doviz()
        k = piyasa.cetvel_kaynaklari(doviz, PIYASA)
        self.assertEqual(k["adlar"], ["doviz.com", "TCMB"])
        dolar = next(g for g in k["son"] if "Dolar" in g["kalemler"])
        self.assertEqual(dolar["kaynak"], piyasa.sayfa_verisi(
            piyasa.ENSTRUMANLAR["dolar"], doviz, PIYASA)["son"]["kaynak"])
        self.assertEqual(piyasa.cetvel_kaynaklari(None, None),
                         {"son": [], "tcmb": None, "adlar": []})

    def test_varsayilan_servis_paneli_de_dogru_atfeder(self):
        """Tema kalkarsa dönülen panel (`parca/bolum_servis.html`) aynı künyeyi taşır."""
        from django.template.loader import render_to_string
        self.yaz("doviz", _doviz())
        canli._bellek.clear()
        with override_settings(CANLI_VERI_KOK=self.kok):
            doviz = canli.oku("doviz")
            metin = render_to_string("parca/bolum_servis.html", {"servis": {
                "tur": "doviz", "doviz": doviz,
                "kaynaklar": piyasa.cetvel_kaynaklari(doviz, PIYASA)}})
        self.assertIn("Son ve değişim: doviz.com", metin)
        self.assertIn("Alış ve satış: TCMB bülteni", metin)
        self.assertNotIn("Kaynak: TCMB döviz kurları", metin)


class Sorgu(PiyasaTesti):

    def _say(self, yol):
        canli._bellek.clear()
        with override_settings(CANLI_VERI_KOK=self.kok), \
                CaptureQueriesContext(connection) as yakala:
            self.assertEqual(self.client.get(yol).status_code, 200)
        return len(yakala.captured_queries)

    def test_sorgu_sayisi_sabit_ve_haberle_buyumuyor(self):
        self.yaz("doviz", _doviz())
        self.yaz("piyasa", PIYASA)
        self._say("/piyasa/dolar")              # kabuk önbelleğini ısıt
        az = self._say("/piyasa/dolar")
        simdi = timezone.now()
        for n in range(20):
            Haber.objects.create(id=960400 + n, slug=f"eko-{n}", baslik=f"Ekonomi {n}",
                                 govde="<p>g</p>", kategori=self.ekonomi,
                                 yayin_zamani=simdi - timedelta(minutes=n))
        self._say("/piyasa/dolar")
        cok = self._say("/piyasa/dolar")
        self.assertEqual(az, cok)
        # Isınmış kabukta: yalnız ekonomi listesi (slug eşlemesi süreçte).
        self.assertLessEqual(cok, 2, cok)
        metin = self.icerik(self.sayfa())
        self.assertEqual(metin.split("EKONOMİDEN SON HABERLER", 1)[1].count("<li>"),
                         views.PIYASA_HABER)


class Grafik(PiyasaTesti):

    def _gecmisli(self, seri=GECMIS):
        self.yaz("doviz", _doviz(dolar={"gecmis": seri,
                                        "gecmis_kaynak": "TCMB günlük bülten (döviz satış)"}))
        return self.icerik(self.sayfa())

    def test_svg_erisilebilir_ve_kendini_anlatiyor(self):
        metin = self._gecmisli()
        svg = re.search(r"<svg[^>]*>.*?</svg>", metin, re.S).group(0)
        self.assertIn('role="img"', svg)
        self.assertIn('aria-labelledby="grafik-baslik grafik-aciklama"', svg)
        baslik = re.search(r'<title id="grafik-baslik">(.*?)</title>', svg).group(1)
        self.assertIn("Dolar (USD/TL)", baslik)
        self.assertIn("7 Eylül 2026 – 11 Eylül 2026", baslik)
        self.assertIn("5 gözlem", baslik)
        aciklama = re.search(r'<desc id="grafik-aciklama">(.*?)</desc>', svg).group(1)
        self.assertIn("En düşük 48,3100 (7 Eylül)", aciklama)
        self.assertIn("en yüksek 48,5178 (11 Eylül)", aciklama)
        self.assertIn("Kaynak: TCMB günlük bülten (döviz satış)", aciklama)
        # Birim, eksen yazıları ve kaynak görünür metin olarak da var.
        self.assertIn('<span class="grafik-birim" aria-hidden="true">₺</span>', metin)
        self.assertIn("<span>48,5178</span>", metin)
        self.assertIn("<span>48,3100</span>", metin)
        self.assertIn("<figcaption>", metin)
        self.assertIn("yatay eksen tarih. Kaynak: TCMB günlük bülten", metin)
        # Ham renk yok; JS kütüphanesi yok.
        self.assertNotRegex(svg, r"#[0-9A-Fa-f]{3,6}\b")
        self.assertNotIn("<script", svg)

    def test_noktalar_tarihe_orantili_ve_ondalik_nokta(self):
        g = piyasa.grafik(piyasa.gecmis_serisi(
            {"gecmis": GECMIS, "gecmis_kaynak": "x"}), 4)
        noktalar = [tuple(map(float, n.split(","))) for n in g["noktalar"].split()]
        self.assertEqual(noktalar[0], (0.0, 200.0))       # en düşük, en solda
        self.assertEqual(noktalar[-1], (600.0, 0.0))      # en yüksek, en sağda
        self.assertAlmostEqual(noktalar[1][0], 150.0)     # 4 günde 1 gün = 1/4

    def test_tablo_yeniden_eskiye_ve_degisim(self):
        metin = self._gecmisli()
        tablo = metin.split("<tbody>", 1)[1].split("</tbody>", 1)[0]
        tarihler = re.findall(r'<time datetime="([\d-]+)">', tablo)
        self.assertEqual(tarihler[0], "2026-09-11")
        self.assertEqual(tarihler[-1], "2026-09-07")
        self.assertIn("geriledi", tablo)                  # 08 → 09 Eylül
        self.assertEqual(tablo.count("<tr"), 5)

    def test_tablo_on_satir_grafik_otuz_gozlem(self):
        from datetime import date
        seri = [{"tarih": (date(2026, 8, 1) + timedelta(days=i)).isoformat(),
                 "deger": 48 + i / 100} for i in range(40)]
        metin = self._gecmisli(seri)
        self.assertEqual(metin.split("<tbody>", 1)[1].split("</tbody>", 1)[0].count("<tr"),
                         piyasa.GECMIS_TABLO)
        self.assertIn("30 gözlem", metin)

    def test_tek_gozlemde_grafik_yok_tablo_var(self):
        metin = self._gecmisli(GECMIS[-1:])
        self.assertNotIn("<svg", metin)
        self.assertIn("GEÇMİŞ", metin)
        self.assertIn('<time datetime="2026-09-11">', metin)

    def test_bozuk_gozlem_atlanir(self):
        seri = piyasa.gecmis_serisi({"gecmis_kaynak": "x", "gecmis": [
            {"tarih": "yok", "deger": 1}, {"tarih": "2026-09-01", "deger": "48"},
            {"tarih": "11-09-2026", "deger": 48.5}, {"tarih": "2026-09-10", "deger": -1}]})
        self.assertEqual([s["tarih"].isoformat() for s in seri], ["2026-09-11"])


class Cevirici(PiyasaTesti):

    def test_dovizden_tl_ye_ve_tersi(self):
        self.yaz("doviz", _doviz())
        metin = self.icerik(self.sayfa("/piyasa/dolar?miktar=100"))
        self.assertIn("<b>100,00 dolar = 4.852,50 TL</b>", metin)
        metin = self.icerik(self.sayfa("/piyasa/dolar?miktar=1.000&yon=tl"))
        self.assertIn("<b>1.000,00 TL = 20,6079 dolar</b>", metin)
        metin = self.icerik(self.sayfa("/piyasa/gram-altin?miktar=2,5"))
        self.assertIn("<b>2,50 gram = 16.962,20 TL</b>", metin)

    def test_gecersiz_miktar_hata_ve_aria(self):
        self.yaz("doviz", _doviz())
        metin = self.icerik(self.sayfa("/piyasa/euro?miktar=abc"))
        self.assertIn("Geçerli bir miktar girin", metin)
        self.assertIn('aria-invalid="true"', metin)
        self.assertIn('<label for="cevirici-miktar">', metin)

    def test_sorgulu_adres_dizine_girmez_kanonik_temiz(self):
        self.yaz("doviz", _doviz())
        metin = self.sayfa("/piyasa/euro?miktar=100")
        self.assertIn('<meta name="robots" content="noindex, follow">', metin)
        self.assertIn('rel="canonical" href="https://www.bursahakimiyet.com.tr/piyasa/euro"', metin)
        temiz = self.sayfa("/piyasa/euro")
        self.assertIn('<meta name="robots" content="index, follow', temiz)

    def test_bicim_yuvarlar_kesmez(self):
        self.assertEqual(piyasa.bicim(48.12999999999, 4), "48,1300")
        self.assertEqual(piyasa.bicim(6784.8861, 2), "6.784,89")
        self.assertEqual(piyasa.bicim(1250000, 2), "1.250.000,00")

    def test_miktar_cozumu(self):
        for ham, beklenen in (("100", 100.0), ("1.250,50", 1250.5), ("1250,5", 1250.5),
                              ("1250.5", 1250.5), ("1.000", 1000.0), ("1.000.000", 1e6),
                              ("abc", None), ("-5", None), ("", None)):
            self.assertEqual(piyasa.miktar_coz(ham), beklenen, ham)


class Seo(PiyasaTesti):

    def test_baslik_aciklama_kanonik_jsonld(self):
        self.yaz("doviz", _doviz())
        metin = self.sayfa("/piyasa/dolar")
        self.assertIn("<title>Dolar kaç TL? Dolar kuru, TCMB alış-satış ve çevirici"
                      " — Bursa Hakimiyet</title>", metin)
        aciklama = re.search(r'name="description" content="(.*?)"', metin).group(1)
        self.assertIn("Dolar 48,5250 TL (12 Eylül 2026, doviz.com)", aciklama)
        self.assertIn('rel="canonical" href="https://www.bursahakimiyet.com.tr/piyasa/dolar"',
                      metin)
        bloklar = [json.loads(b) for b in re.findall(
            r'<script type="application/ld\+json">(.*?)</script>', metin, re.S)]
        turler = {b["@type"]: b for b in bloklar}
        kirinti = [o["name"] for o in turler["BreadcrumbList"]["itemListElement"]]
        self.assertEqual(kirinti, ["Anasayfa", "Ekonomi", "Dolar"])
        sayfa = turler["WebPage"]
        self.assertEqual(sayfa["url"], "https://www.bursahakimiyet.com.tr/piyasa/dolar")
        # dateModified VERİNİN zamanı; uydurma finans alanı yok.
        self.assertEqual(sayfa["dateModified"], "2026-09-12T21:57:07+03:00")
        self.assertNotIn("ExchangeRateSpecification", metin)

    def test_veri_yoksa_jsonld_tarihsiz(self):
        metin = self.sayfa("/piyasa/euro")
        sayfa = [json.loads(b) for b in re.findall(
            r'<script type="application/ld\+json">(.*?)</script>', metin, re.S)][1]
        self.assertNotIn("dateModified", sayfa)
