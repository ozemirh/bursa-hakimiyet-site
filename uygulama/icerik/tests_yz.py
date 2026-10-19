"""Yapay zekâ köprüsü — `icerik/yz_kopru.py`.

Testler **ağa çıkmaz**: paket üretimi (`paket_uret`) yamalanır, çünkü ölçülen
şey aracın ayıklaması değil, paketin gazetenin veri modeline nasıl indiği.
Aracın kendi doğruluğu `arac/` tarafında, `parite.py` ve `denetim.py` ile
denetleniyor.

Kilitlenen dört karar:

1. Köprü **yayınlamaz** — taslak Pasif doğar, yayın zamanı boştur.
2. Kural motoru başlık yazmadığında başlık işaretlenir ve o işaret duran
   haber **yayına alınamaz**.
3. Slug boş doğar; adresi editörün yazdığı gerçek başlık belirler.
4. Görsel indirilmez; yalnız adresi saklanır.
"""

import tempfile
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth.models import Group, User
from django.core.management import call_command
from django.test import TestCase

from taksonomi.models import Ilce, Kategori, Kaynak

from . import yz_kopru
from .formlar import BASLIK_SINIR, SPOT_SINIR, HaberForm
from .models import Haber

PAROLA = "deneme-parola-123"


def paket_kur(**degisiklikler) -> dict:
    """Aracın kural motoru çıktısıyla aynı biçimde küçük bir paket."""
    paket = {
        "kaynak": {
            "kaynak_url": "https://ornek-yayin.com/haber/1",
            "kaynak_alan": "ornek-yayin.com",
            "kaynak_adi": "Örnek Yayın",
            "asil_kaynak": "",
            "orijinal_baslik": "Nilüfer Çayı için büyük adım",
            "orijinal_spot": "Kollektör hattının yüzde 80'i bitti.",
            "orijinal_govde": "Bursa Büyükşehir Belediyesi açıklama yaptı. " * 12,
            "gorsel_url": "https://ornek-yayin.com/foto/1.jpg",
            "gorsel_alt": "Örnek Yayın",
            "yazar": "Hande D.",
            "yayin_tarihi": "2026-07-20T11:05:16+00:00",
            "kelime_sayisi": 257,
            "ayiklama_guveni": "yuksek",
        },
        "taslak": {
            "baslik_secenekleri": [{"metin": "", "gerekce": "Düz haber başlığı."}],
            "onerilen_baslik_indeksi": 0,
            "spot": "",
            "govde": [{"tur": "paragraf", "metin": ""}],
            "kategori": "Çevre ve su",
            "ilce": "Nilüfer",
            "etiketler": ["nilüfer çayı", "atıksu"],
            "bursa_ilgisi": {"var_mi": True, "aciklama": ""},
            "hassas_konu": {"var_mi": False, "turu": "", "uyari": ""},
            "dogrulanmasi_gerekenler": ["'127 milyon' rakamını teyit edin."],
        },
        "uretim": {"saglayici": "kural", "model": "", "surum": "1.0"},
        "tezgah": [{"metin": "Kaynağın ham cümlesi.", "puan": 100}],
    }
    for anahtar, deger in degisiklikler.items():
        if anahtar in ("kaynak", "taslak"):
            paket[anahtar].update(deger)
        else:
            paket[anahtar] = deger
    return paket


class KopruTemel(TestCase):
    """Ortak kurulum.

    Paket dosyaları geçici klasöre yazılıyor: köprü gerçekte `arac/cikti/`
    altına yazar ve testler o klasöre kalıcı çöp bırakmamalı.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        gecici = tempfile.TemporaryDirectory()
        cls.addClassCleanup(gecici.cleanup)
        yama = patch.object(yz_kopru, "CIKTI_KOK", Path(gecici.name))
        yama.start()
        cls.addClassCleanup(yama.stop)

    @classmethod
    def setUpTestData(cls):
        call_command("taksonomi_kur", verbosity=0)
        call_command("roller_kur", verbosity=0)
        cls.editor = User.objects.create_user("editor", password=PAROLA)
        cls.editor.groups.add(Group.objects.get(name="Editör"))


class KaynakAyiklama(TestCase):
    """`arac/ayiklayici.py` — köprünün girdisini üreten katman.

    Ağa çıkmaz: HTML elle kuruluyor. Burada ölçülen iki kusur 5 Eylül
    2026'da olay.com.tr haberinde görüldü ve panele kadar taşınmıştı.
    """

    def _ayikla(self, html: str) -> dict:
        ayiklayici, _ = yz_kopru._arac()
        return ayiklayici.ayikla(html, "https://ornek-yayin.com/haber/1")

    JSONLD = """<html><head><title>Sayfa</title>
      <script type="application/ld+json">{"@type":"NewsArticle",
        "headline":%s,
        "description":"Bakan&#039;ın a&ccedil;ıklaması.",
        "publisher":{"name":"Örnek Gazete"}}</script>
      </head><body><p>%s</p></body></html>"""

    def test_jsonld_varlik_kacislari_cozuluyor(self):
        """<script> bloğu CDATA'dır; HTMLParser orada kaçışları çözmez."""
        html = self.JSONLD % ('"OECD&#039;den T&uuml;rkiye&#039;ye destek"',
                              "Gövde. " * 80)
        kaynak = self._ayikla(html)
        self.assertEqual(kaynak["orijinal_baslik"],
                         "OECD'den Türkiye'ye destek")
        self.assertNotIn("&#", kaynak["orijinal_baslik"])
        self.assertEqual(kaynak["orijinal_spot"], "Bakan'ın açıklaması.")

    def test_baslikta_duran_yayin_adi_atiliyor(self):
        """JSON-LD `headline` çoğu sitede sayfa <title>'ının kopyasıdır."""
        html = self.JSONLD % ('"Şehirde yeni hat - Örnek Gazete"',
                              "Gövde. " * 80)
        self.assertEqual(self._ayikla(html)["orijinal_baslik"],
                         "Şehirde yeni hat")

    def test_baslikdaki_tire_korunuyor(self):
        """Kuyruk YAYIN ADIYLA eşleşmiyorsa kesilmez: haber başlığında
        tire olabilir."""
        html = self.JSONLD % ('"Bursa - Ankara hattı açılıyor"',
                              "Gövde. " * 80)
        self.assertEqual(self._ayikla(html)["orijinal_baslik"],
                         "Bursa - Ankara hattı açılıyor")


class SinirHizasi(TestCase):
    """Aracın uzunluk sınırları panelin sözleşmesiyle hizalı mı.

    5 Eylül 2026: panelin spot sınırı 160'tı, aracın istemi "160-260 karakter"
    diyordu — model her seferinde panelin kapısına takılan taslak üretiyordu.
    Sınır 320'ye çıkınca araç da güncellendi. Bu test iki tarafın bir daha
    ayrışmasını yakalar; sayılar iki dosyada da SABİT olarak duruyor.
    """

    def test_arac_baslik_siniri_paneli_asmiyor(self):
        _, _ = yz_kopru._arac()          # `arac/` sys.path'e girsin
        import denetim
        self.assertLessEqual(denetim.BASLIK_SINIR, BASLIK_SINIR)

    def test_arac_spot_ustu_panelin_altinda(self):
        _, _ = yz_kopru._arac()
        import denetim
        self.assertLessEqual(denetim.SPOT_UST, SPOT_SINIR)
        self.assertLess(denetim.SPOT_ALT, denetim.SPOT_UST)


class KategoriEslemesi(KopruTemel):
    """Aracın 14 sözlük kategorisi gazetenin 13 kategorisine iner."""

    def test_arac_kategorisi_gazetenin_kategorisine_cevrilir(self):
        kategori, gerekce = yz_kopru.kategori_sec(paket_kur())
        self.assertEqual(kategori.ad, "BURSA")
        self.assertIn("Çevre ve su", gerekce)

    def test_bursa_ilgisi_gundemi_bursaya_cevirir(self):
        paket = paket_kur(taslak={"kategori": "Siyaset",
                                  "bursa_ilgisi": {"var_mi": True}})
        kategori, gerekce = yz_kopru.kategori_sec(paket)
        self.assertEqual(kategori.ad, "BURSA")
        self.assertIn("Bursa ilgisi", gerekce)

    def test_bursa_ilgisi_yoksa_gundemde_kalir(self):
        paket = paket_kur(taslak={"kategori": "Siyaset",
                                  "bursa_ilgisi": {"var_mi": False}})
        kategori, _ = yz_kopru.kategori_sec(paket)
        self.assertEqual(kategori.ad, "GÜNDEM")

    def test_bursaspor_gecen_spor_haberi_kulup_kategorisine_gider(self):
        paket = paket_kur(
            taslak={"kategori": "Spor", "bursa_ilgisi": {"var_mi": True}},
            kaynak={"orijinal_govde": "Bursaspor sahasında kazandı."})
        kategori, gerekce = yz_kopru.kategori_sec(paket)
        self.assertEqual(kategori.ad, "BURSASPOR")
        self.assertIn("Bursaspor", gerekce)

    def test_tanimsiz_kategori_gundeme_duser(self):
        paket = paket_kur(taslak={"kategori": "Uzay Madenciliği",
                                  "bursa_ilgisi": {"var_mi": False}})
        kategori, _ = yz_kopru.kategori_sec(paket)
        self.assertEqual(kategori.ad, "GÜNDEM")


class KaynakKapisi(KopruTemel):
    """Kaynak adı `goc_kaynak` kapısından geçer; çöp kayıt açılmaz."""

    def test_gecerli_yayin_kaynak_olarak_acilir(self):
        kayit, tur, _ = yz_kopru.kaynak_sec(paket_kur())
        self.assertEqual(kayit.ad, "Örnek Yayın")
        self.assertEqual(tur, Haber.KAYNAK_DIS_YAYIN)

    def test_meta_yazar_degeri_kaynak_sayilmaz(self):
        """"Haber Merkezi" künye türüdür, kaynak değil (goc_kaynak §)."""
        paket = paket_kur(kaynak={"kaynak_adi": "Haber Merkezi"})
        kayit, tur, gerekce = yz_kopru.kaynak_sec(paket)
        self.assertIsNone(kayit)
        self.assertEqual(tur, "")
        self.assertIn("kaynak sayılmadı", gerekce)
        self.assertFalse(Kaynak.objects.filter(ad="Haber Merkezi").exists())

    def test_asil_kaynak_araci_yayinin_onune_gecer(self):
        """Sayfa kendi kaynağını belirtmişse kaynak odur (CLAUDE.md)."""
        paket = paket_kur(kaynak={"asil_kaynak": "Anadolu Ajansı"})
        kayit, _, _ = yz_kopru.kaynak_sec(paket)
        self.assertEqual(kayit.ad, "Anadolu Ajansı")

    def test_ayni_kaynak_ikinci_kez_acilmaz(self):
        yz_kopru.kaynak_sec(paket_kur())
        yz_kopru.kaynak_sec(paket_kur())
        self.assertEqual(Kaynak.objects.filter(ad="Örnek Yayın").count(), 1)


class BaslikVeGovde(KopruTemel):

    def test_motor_baslik_yazmadiysa_baslik_isaretlenir(self):
        baslik, yazilacak = yz_kopru.baslik_al(paket_kur())
        self.assertTrue(yazilacak)
        self.assertTrue(baslik.startswith(yz_kopru.BASLIK_ISARETI))

    def test_model_baslik_yazdiysa_oldugu_gibi_alinir(self):
        paket = paket_kur(taslak={
            "baslik_secenekleri": [{"metin": "Kollektör hattı tamamlanıyor"}]})
        baslik, yazilacak = yz_kopru.baslik_al(paket)
        self.assertFalse(yazilacak)
        self.assertEqual(baslik, "Kollektör hattı tamamlanıyor")

    def test_kural_motorunda_govde_bos_gelir(self):
        """Motor dil üretmez; kaynaktan cümle taşınmaz."""
        self.assertEqual(yz_kopru.govde_html(paket_kur()), "")

    def test_govdede_tirnak_kacirilmiyor(self):
        """`html.escape` varsayılanı tırnağı da kaçırır; o NİTELİK içindir.

        5 Eylül 2026: modelin yazdığı gövde panele `İstanbul&#x27;da` diye
        düşüyordu. İşaretlemeyi bozan üçlü (`&`, `<`, `>`) kaçırılmaya
        devam ediyor.
        """
        paket = paket_kur(taslak={"govde": [
            {"tur": "paragraf",
             "metin": "İstanbul'da \"Zirve\" & sonrası <b>kalın</b>"},
        ]})
        html = yz_kopru.govde_html(paket)
        self.assertIn("İstanbul'da", html)
        self.assertIn('"Zirve"', html)
        self.assertNotIn("&#x27;", html)
        self.assertNotIn("&quot;", html)
        self.assertIn("&amp;", html)
        self.assertIn("&lt;b&gt;", html)

    def test_govde_bloklari_html_paragrafa_cevrilir(self):
        paket = paket_kur(taslak={"govde": [
            {"tur": "paragraf", "metin": "Birinci paragraf."},
            {"tur": "ara_baslik", "metin": "Ara başlık"},
            {"tur": "paragraf", "metin": "İkinci & üçüncü."},
        ]})
        html = yz_kopru.govde_html(paket)
        self.assertIn("<p>Birinci paragraf.</p>", html)
        self.assertIn("<h2>Ara başlık</h2>", html)
        self.assertIn("&amp;", html)          # kaçırılıyor


class TaslakYazma(KopruTemel):

    def test_taslak_pasif_dogar_ve_yayinlanmaz(self):
        haber, _ = yz_kopru.taslak_yaz(paket_kur(), self.editor)
        self.assertEqual(haber.durum, Haber.DURUM_PASIF)
        self.assertEqual(haber.hazirlik, "taslak")
        self.assertIsNone(haber.yayin_zamani)
        self.assertTrue(haber.masada_mi())

    def test_slug_bos_dogar(self):
        """Adres editörün yazacağı başlıktan kurulacak; işaretli başlıktan değil."""
        haber, _ = yz_kopru.taslak_yaz(paket_kur(), self.editor)
        self.assertEqual(haber.slug, "")

    def test_kategori_ilce_etiket_ve_kaynak_baglanir(self):
        haber, notlar = yz_kopru.taslak_yaz(paket_kur(), self.editor)
        self.assertEqual(haber.kategori.ad, "BURSA")
        self.assertEqual(haber.ilce, Ilce.objects.get(ad="Nilüfer"))
        self.assertEqual(
            sorted(haber.etiketler.values_list("ad", flat=True)),
            ["atıksu", "nilüfer çayı"])
        self.assertEqual([k.ad for k in haber.kaynaklar.all()], ["Örnek Yayın"])
        self.assertEqual(haber.kaynak_turu, Haber.KAYNAK_DIS_YAYIN)
        self.assertTrue(any("BURSA" in s for s in notlar))

    def test_gorsel_indirilmez_sadece_adresi_saklanir(self):
        haber, _ = yz_kopru.taslak_yaz(paket_kur(), self.editor)
        self.assertFalse(haber.gorsel_var)
        self.assertEqual(haber.gorsel_dosya, "")
        self.assertEqual(haber.gorsel_url, "https://ornek-yayin.com/foto/1.jpg")

    def test_kimlik_eski_aralikla_cakismaz(self):
        """Eski sitenin kimlikleri hesaba girmez; panel kendi tabanından
        sayar (`icerik/kimlik.py`). "En büyük + 1" 1696272–74'te canlıdaki
        haberlerle çakışmıştı."""
        gundem = Kategori.objects.get(ad="GÜNDEM")
        Haber.objects.create(id=1_732_500, slug="x", baslik="X", kategori=gundem)
        haber, _ = yz_kopru.taslak_yaz(paket_kur(), self.editor)
        self.assertEqual(haber.pk, 5_000_000)
        Haber.objects.create(id=5_000_010, slug="y", baslik="Y", kategori=gundem)
        ikinci, _ = yz_kopru.taslak_yaz(paket_kur(), self.editor)
        self.assertEqual(ikinci.pk, 5_000_011)

    def test_paket_diske_yazilir_ve_geri_okunur(self):
        haber, _ = yz_kopru.taslak_yaz(paket_kur(), self.editor)
        okunan = yz_kopru.paket_oku(haber.pk)
        self.assertEqual(okunan["kaynak"]["kaynak_adi"], "Örnek Yayın")
        self.assertTrue(okunan["panel_notlari"])


class YayinKapisi(KopruTemel):
    """İşaretli başlık yayına geçemez — formun kapısı."""

    def _veri(self, **degisiklikler):
        veri = {
            "baslik": "Kollektör hattı tamamlanıyor",
            "spot": "Hattın yüzde 80'i bitti.",
            "govde": "<p>Birinci paragraf.</p><p>İkinci paragraf.</p>",
            "kategori": Kategori.objects.get(ad="BURSA").pk,
            "etiketler": "atıksu",
            "durum": Haber.DURUM_AKTIF,
            "hazirlik": "hazir",
        }
        veri.update(degisiklikler)
        return veri

    def test_isaretli_baslik_yayina_alinamaz(self):
        form = HaberForm(self._veri(
            baslik="%s Nilüfer Çayı için büyük adım" % yz_kopru.BASLIK_ISARETI),
            kullanici=self.editor)
        self.assertFalse(form.is_valid())
        self.assertIn("başlık", " ".join(form.non_field_errors()))

    def test_isaretli_baslik_taslak_olarak_kaydedilebilir(self):
        form = HaberForm(self._veri(
            baslik="%s Nilüfer Çayı" % yz_kopru.BASLIK_ISARETI,
            durum=Haber.DURUM_PASIF, hazirlik="taslak"),
            kullanici=self.editor)
        self.assertTrue(form.is_valid(), form.errors)

    def test_baslik_yazilinca_yayina_gider(self):
        form = HaberForm(self._veri(), kullanici=self.editor)
        self.assertTrue(form.is_valid(), form.errors)


class TaslaktanYayina(KopruTemel):
    """Taslak → editör yazar → yayın. Adres bu yolda kuruluyor."""

    def _form_verisi(self, **ek):
        veri = {
            "baslik": "Nilüfer Çayı için büyük adım",
            "spot": "Kollektör hattının yüzde 80'i tamamlandı.",
            "govde": "<p>Birinci paragraf.</p><p>İkinci paragraf.</p>",
            "kategori": Kategori.objects.get(ad="BURSA").pk,
            "etiketler": "atıksu",
            "kaynak_turu": Haber.KAYNAK_DIS_YAYIN,
            "durum": Haber.DURUM_AKTIF,
            "hazirlik": "hazir",
        }
        veri.update(ek)
        return veri

    def setUp(self):
        self.client.force_login(self.editor)

    def _taslak(self):
        haber, _ = yz_kopru.taslak_yaz(paket_kur(), self.editor)
        return haber

    def test_isaretli_baslikla_kaydedilince_slug_hala_bos(self):
        """Yer tutucu başlıktan adres üretilirse adres kalıcı olarak bozulur."""
        haber = self._taslak()
        yanit = self.client.post(
            "/panel/haber/%d" % haber.pk,
            self._form_verisi(baslik=haber.baslik, durum=Haber.DURUM_PASIF,
                              hazirlik="taslak"))
        self.assertEqual(yanit.status_code, 302)
        haber.refresh_from_db()
        self.assertEqual(haber.slug, "")

    def test_gercek_baslik_yazilinca_slug_arsiv_desenine_uyuyor(self):
        haber = self._taslak()
        self.client.post("/panel/haber/%d" % haber.pk, self._form_verisi())
        haber.refresh_from_db()
        self.assertEqual(haber.slug, "nilufer-cayi-icin-buyuk-adim")
        self.assertEqual(haber.durum, Haber.DURUM_AKTIF)
        self.assertEqual(haber.get_absolute_url(),
                         "/bursa/nilufer-cayi-icin-buyuk-adim-%d" % haber.pk)

    def test_slug_bir_kez_yaziliyor(self):
        """Başlık sonradan değişse de adres sabit kalır."""
        haber = self._taslak()
        self.client.post("/panel/haber/%d" % haber.pk, self._form_verisi())
        self.client.post("/panel/haber/%d" % haber.pk,
                         self._form_verisi(baslik="Bambaşka bir başlık"))
        haber.refresh_from_db()
        self.assertEqual(haber.slug, "nilufer-cayi-icin-buyuk-adim")


class PanelEkranlari(KopruTemel):

    def setUp(self):
        self.client.force_login(self.editor)

    def test_ekran_aciliyor(self):
        yanit = self.client.get("/panel/yz-taslak")
        self.assertEqual(yanit.status_code, 200)
        self.assertContains(yanit, "Haber adresi")

    def test_yetkisiz_kullanici_giremez(self):
        User.objects.create_user("okur", password=PAROLA)
        self.client.force_login(User.objects.get(username="okur"))
        self.assertEqual(self.client.get("/panel/yz-taslak").status_code, 403)

    def test_giris_yapmadan_kapali(self):
        self.client.logout()
        yanit = self.client.get("/panel/yz-taslak")
        self.assertEqual(yanit.status_code, 302)
        self.assertIn("/panel/giris", yanit["Location"])

    @patch("icerik.yz_kopru.paket_uret")
    def test_adres_verilince_taslak_acilir(self, sahte):
        sahte.return_value = paket_kur()
        yanit = self.client.post("/panel/yz-taslak", {
            "adres": "https://ornek-yayin.com/haber/1", "saglayici": "kural"})
        haber = Haber.objects.order_by("-id").first()
        self.assertRedirects(yanit, "/panel/yz-taslak/%d" % haber.pk)
        self.assertEqual(haber.durum, Haber.DURUM_PASIF)
        sahte.assert_called_once_with("https://ornek-yayin.com/haber/1", "kural")

    @patch("icerik.yz_kopru.paket_uret")
    def test_hata_ekranda_gosterilir_ve_kayit_acilmaz(self, sahte):
        sahte.side_effect = yz_kopru.YzHatasi("Kaynak alınamadı: 403")
        once = Haber.objects.count()
        yanit = self.client.post("/panel/yz-taslak", {
            "adres": "https://ornek-yayin.com/haber/1", "saglayici": "kural"})
        self.assertEqual(yanit.status_code, 200)
        self.assertContains(yanit, "Kaynak alınamadı")
        self.assertEqual(Haber.objects.count(), once)

    @patch("icerik.yz_kopru.paket_uret")
    def test_taslak_ekrani_kaynagi_ve_tezgahi_gosterir(self, sahte):
        sahte.return_value = paket_kur()
        self.client.post("/panel/yz-taslak", {
            "adres": "https://ornek-yayin.com/haber/1", "saglayici": "kural"})
        haber = Haber.objects.order_by("-id").first()
        yanit = self.client.get("/panel/yz-taslak/%d" % haber.pk)
        self.assertEqual(yanit.status_code, 200)
        self.assertContains(yanit, "Kaynağın ham cümlesi")
        self.assertContains(yanit, "127 milyon")
        self.assertContains(yanit, "İndir ve habere bağla")

    def test_gorsel_ucu_get_ile_indirmez(self):
        haber = Haber.objects.create(
            id=900500, slug="x", baslik="X",
            kategori=Kategori.objects.get(ad="GÜNDEM"),
            gorsel_url="https://ornek-yayin.com/foto/1.jpg")
        yanit = self.client.get("/panel/yz-taslak/%d/gorsel" % haber.pk)
        self.assertRedirects(yanit, "/panel/yz-taslak/%d" % haber.pk)
        haber.refresh_from_db()
        self.assertFalse(haber.gorsel_var)
