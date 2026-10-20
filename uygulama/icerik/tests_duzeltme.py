"""Düzeltme / cevap notu — model, panel girişi, haber bloğu, sayfa (20 Ekim 2026).

İş: DEGERLENDIRME-2026-10 Aşama 4 ("kesim öncesi şart") + referans
kütüphanesi karşılaştırması 2. satır. Korunanlar:

1. **Model.** Kayıt silinmez (tekil, toplu, haberle birlikte); yalnız
   yayından kaldırılır, kimin kaldırdığı kalır.
2. **Panel girişi.** Not haberi giren ekrandan girilir (`/panel/haber/<id>`
   altındaki bölüm), uç yalnız POST, kapı yayın yetkisi; cevapta cevap
   veren zorunlu; yayın zamanı elle verilemez; her fiil denetim kaydı yazar.
3. **Haber detayı.** Not varsa gövdenin SONUNDA blok + başlık altında
   bloğa bağlı işaret; yoksa ikisi de HİÇ basılmaz. Metin kaçışlı.
4. **`/duzeltmeler`.** Kategori sanılmaz; en yeniden eskiye; kaldırılan not
   ve yayında olmayan haberin notu girmez; hukuki iddia cümlesi yok.
5. **JSON-LD.** `correction` → `CorrectionComment` yalnız düzeltme türü
   varsa.
6. **Önbellek ve başarım.** Not kaydı sayfa önbelleğini düşürür; sorgu
   sayısı not sayısıyla büyümez, notsuz haberde hiç artmaz.
"""

import json
import re
from datetime import timedelta

from django.contrib.auth.models import Group, Permission, User
from django.core.management import call_command
from django.db import connection
from django.db.models import ProtectedError
from django.test import TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import resolve
from django.utils import timezone

from taksonomi.models import Kategori, KategoriTur

from .models import Duzeltme, DuzeltmeSilinmez, Haber, LogKaydi

LOCMEM = "django.core.cache.backends.locmem.LocMemCache"
SAYFA_ACIK = override_settings(
    CACHES={"default": {"BACKEND": LOCMEM, "LOCATION": "bh-duzeltme-veri"},
            "sayfa": {"BACKEND": LOCMEM, "LOCATION": "bh-duzeltme-sayfa"}},
    SAYFA_ONBELLEK_SANIYE=30)

_LD = re.compile(r'<script type="application/ld\+json">(.*?)</script>', re.S)


def _ld(html):
    return [json.loads(ham) for ham in _LD.findall(html)]


def _makale(html):
    return next(x for x in _ld(html) if x.get("@type") == "NewsArticle")


class Temel(TestCase):

    @classmethod
    def setUpTestData(cls):
        call_command("taksonomi_kur", verbosity=0)
        call_command("roller_kur", verbosity=0)
        cls.gundem = KategoriTur.objects.get(tur=Kategori.TUR_HABER, slug="gundem").kategori
        simdi = timezone.now()
        cls.haber = Haber.objects.create(
            id=8800001, slug="nilufer-de-kopru-acildi", baslik="Nilüfer'de köprü açıldı",
            spot="Köprü bugün trafiğe açıldı.",
            govde="<p>Birinci paragraf.</p><p>İkinci paragraf.</p>",
            kategori=cls.gundem, durum=Haber.DURUM_AKTIF,
            yayin_zamani=simdi - timedelta(hours=5))
        cls.notsuz = Haber.objects.create(
            id=8800002, slug="notsuz-haber", baslik="Notu olmayan haber",
            spot="Spot.", govde="<p>Bir.</p><p>İki.</p>", kategori=cls.gundem,
            durum=Haber.DURUM_AKTIF, yayin_zamani=simdi - timedelta(hours=6))
        cls.pasif = Haber.objects.create(
            id=8800003, slug="pasif-haber", baslik="Yayından çekilmiş haber",
            spot="Spot.", govde="<p>Bir.</p><p>İki.</p>", kategori=cls.gundem,
            durum=Haber.DURUM_PASIF, yayin_zamani=simdi - timedelta(hours=7))
        cls.kullanicilar = {}
        for sira, rol in enumerate(("Muhabir", "Editör", "Yayın Yönetmeni")):
            u = User.objects.create_user(f"duzeltme{sira}", first_name="D",
                                         last_name=str(sira))
            u.groups.add(Group.objects.get(name=rol))
            cls.kullanicilar[rol] = u

    def _not(self, haber=None, tur=Duzeltme.TUR_DUZELTME, metin="Haberde köprünün açılış "
             "saati 10.00 yazılmıştı; doğrusu 11.00'dir.", veren="", once=0, **ek):
        return Duzeltme.objects.create(
            haber=haber or self.haber, tur=tur, metin=metin, cevap_veren=veren,
            yayin_zamani=timezone.now() - timedelta(minutes=once), **ek)

    def _sayfa(self, yol):
        yanit = self.client.get(yol)
        self.assertEqual(yanit.status_code, 200, yol)
        return yanit.content.decode()


# ------------------------------------------------------------------ model

class Model(Temel):

    def test_kayit_silinmez_tekil_toplu_haberle(self):
        kayit = self._not()
        with self.assertRaises(DuzeltmeSilinmez):
            kayit.delete()
        with self.assertRaises(DuzeltmeSilinmez):
            Duzeltme.objects.filter(pk=kayit.pk).delete()
        with self.assertRaises(ProtectedError):
            Haber.objects.get(pk=self.haber.pk).delete()
        self.assertTrue(Duzeltme.objects.filter(pk=kayit.pk).exists())

    def test_isaret_metni_turden_ve_oncelikli(self):
        cevap = self._not(tur=Duzeltme.TUR_CEVAP, veren="Kurum")
        guncel = self._not(tur=Duzeltme.TUR_GUNCELLEME)
        duz = self._not()
        self.assertEqual(Duzeltme.isaret_metni([]), "")
        self.assertEqual(Duzeltme.isaret_metni([guncel]), "Bu haberde güncelleme notu var")
        self.assertEqual(Duzeltme.isaret_metni([guncel, cevap]), "Bu habere cevap yayımlandı")
        self.assertEqual(Duzeltme.isaret_metni([guncel, cevap, duz]), "Bu haberde düzeltme var")

    def test_haber_icin_yalniz_yayindakiler_eskiden_yeniye(self):
        yeni = self._not(once=1)
        eski = self._not(once=30)
        self._not(once=10, yayinda=False)
        self.assertEqual([n.pk for n in Duzeltme.haber_icin(self.haber)], [eski.pk, yeni.pk])

    def test_haber_icin_not_yoksa_sorgu_acmaz(self):
        haber = Haber.objects.get(pk=self.notsuz.pk)
        haber.duzeltme_var = False      # görünümün EXISTS açıklaması
        with self.assertNumQueries(0):
            self.assertEqual(Duzeltme.haber_icin(haber), [])

    def test_dizin_yayindaki_habere_ve_yayindaki_nota_bakar(self):
        acik = self._not()
        self._not(yayinda=False)
        self._not(haber=self.pasif)
        self.assertEqual([n.pk for n in Duzeltme.dizin()], [acik.pk])


# ------------------------------------------------------------------ panel

class PanelGirisi(Temel):

    def _uc(self, haber=None):
        return f"/panel/haber/{(haber or self.haber).pk}/duzeltme"

    def _gir(self, rol):
        self.client.force_login(self.kullanicilar[rol])

    def test_duzenleme_ekraninda_bolum_ve_form(self):
        self._not(tur=Duzeltme.TUR_CEVAP, veren="Bursa Büyükşehir Belediyesi Basın Müdürü")
        self._gir("Editör")
        html = self._sayfa(f"/panel/haber/{self.haber.pk}")
        self.assertIn('id="duzeltme"', html)
        self.assertIn(f'action="/panel/haber/{self.haber.pk}/duzeltme"', html)
        self.assertIn('name="metin"', html)
        self.assertIn('id="duzeltme_metin"', html)       # ana formun id_… alanlarıyla çakışmaz
        self.assertIn("Bursa Büyükşehir Belediyesi Basın Müdürü", html)
        self.assertIn("Yayından kaldır", html)
        # Ayrı bir yönetim yüzü yok: tek panel kalıbı, o da yalnız POST ucu.
        self.assertEqual(self.client.get(self._uc()).status_code, 302)

    def test_editor_not_yayimlar_denetim_kaydi_yazilir(self):
        self._gir("Editör")
        once = timezone.now()
        yanit = self.client.post(self._uc(), {
            "islem": "ekle", "tur": "duzeltme",
            "metin": "  Haberde  saat 10.00 yazılmıştı.\n\n\n\nDoğrusu 11.00'dir.  ",
            # Elle tarih verilemez: alan formda yok, yok sayılır.
            "yayin_zamani": "2020-01-01 10:00"})
        self.assertEqual(yanit.status_code, 302)
        self.assertTrue(yanit["Location"].endswith(f"/panel/haber/{self.haber.pk}#duzeltme"))
        kayit = Duzeltme.objects.get(haber=self.haber)
        self.assertEqual(kayit.metin, "Haberde saat 10.00 yazılmıştı.\n\nDoğrusu 11.00'dir.")
        self.assertEqual(kayit.olusturan, self.kullanicilar["Editör"])
        self.assertTrue(kayit.yayinda)
        self.assertGreaterEqual(kayit.yayin_zamani, once)
        log = LogKaydi.objects.get(fiil="duzeltme_yayimlama")
        self.assertEqual((log.hedef_tur, log.hedef_id), ("haber", self.haber.pk))
        self.assertEqual(log.sonrasi["duzeltme_id"], kayit.pk)
        self.assertEqual(log.kullanici, self.kullanicilar["Editör"])

    def test_cevapta_cevap_veren_zorunlu_digerinde_yasak(self):
        self._gir("Editör")
        yanit = self.client.post(self._uc(), {"islem": "ekle", "tur": "cevap",
                                              "metin": "Kurumun gönderdiği cevap metni."})
        self.assertEqual(yanit.status_code, 200)
        self.assertIn("cevabı gönderenin", yanit.content.decode())
        yanit = self.client.post(self._uc(), {"islem": "ekle", "tur": "duzeltme",
                                              "cevap_veren": "Biri",
                                              "metin": "Düzeltme metni burada."})
        self.assertEqual(yanit.status_code, 200)
        self.assertIn("yalnız cevap/tekzip", yanit.content.decode())
        yanit = self.client.post(self._uc(), {"islem": "ekle", "tur": "duzeltme",
                                              "metin": "kısa"})
        self.assertEqual(yanit.status_code, 200)
        self.assertIn("en az", yanit.content.decode())
        self.assertFalse(Duzeltme.objects.exists())
        yanit = self.client.post(self._uc(), {
            "islem": "ekle", "tur": "cevap", "cevap_veren": "  Osmangazi   Belediyesi ",
            "metin": "Kurumun gönderdiği cevap metni."})
        self.assertEqual(yanit.status_code, 302)
        self.assertEqual(Duzeltme.objects.get().cevap_veren, "Osmangazi Belediyesi")

    def test_muhabir_yayimlayamaz_listeyi_gorur(self):
        self._not()
        self._gir("Muhabir")
        self.assertEqual(self.client.post(self._uc(), {
            "islem": "ekle", "tur": "duzeltme", "metin": "Muhabirin düzeltme metni."
        }).status_code, 403)
        html = self._sayfa(f"/panel/haber/{self.haber.pk}")
        self.assertIn('id="duzeltme"', html)
        self.assertNotIn(f'action="/panel/haber/{self.haber.pk}/duzeltme"', html)
        self.assertIn("yayın yetkisi ister", html)
        self.assertEqual(Duzeltme.objects.count(), 1)

    def test_baskasinin_haberinde_yalniz_kendi_yetkisi_yetmez(self):
        u = User.objects.create_user("yalniz-kendi")
        for kod in ("haber_girme", "kendi_haberini_yayinlama"):
            u.user_permissions.add(Permission.objects.get(codename=kod))
        self.client.force_login(u)
        yanit = self.client.post(self._uc(), {"islem": "ekle", "tur": "duzeltme",
                                              "metin": "Yetkisiz kişinin metni."})
        self.assertEqual(yanit.status_code, 403)
        self.assertFalse(Duzeltme.objects.exists())

    def test_yayinda_olmayan_habere_not_eklenmez(self):
        self._gir("Editör")
        yanit = self.client.post(self._uc(self.pasif), {
            "islem": "ekle", "tur": "duzeltme", "metin": "Pasif habere düzeltme."})
        self.assertEqual(yanit.status_code, 302)
        self.assertFalse(Duzeltme.objects.exists())

    def test_kaldir_ve_geri_al_kayit_silinmez(self):
        kayit = self._not()
        self._gir("Yayın Yönetmeni")
        yanit = self.client.post(self._uc(), {"islem": "kaldir", "duzeltme": kayit.pk,
                                              "gerekce": "Yanlış habere girildi"})
        self.assertEqual(yanit.status_code, 302)
        kayit.refresh_from_db()
        self.assertFalse(kayit.yayinda)
        self.assertEqual(kayit.kaldiran, self.kullanicilar["Yayın Yönetmeni"])
        self.assertEqual(kayit.kaldirma_gerekcesi, "Yanlış habere girildi")
        self.assertIsNotNone(kayit.kaldirma_zamani)
        log = LogKaydi.objects.get(fiil="duzeltme_kaldirma")
        self.assertEqual(log.gerekce, "Yanlış habere girildi")
        html = self._sayfa(f"/panel/haber/{self.haber.pk}")
        self.assertIn("Kaldırıldı", html)              # geçmiş panelde duruyor
        self.assertIn("Yeniden yayımla", html)
        self.client.post(self._uc(), {"islem": "geri_al", "duzeltme": kayit.pk})
        kayit.refresh_from_db()
        self.assertTrue(kayit.yayinda)
        self.assertEqual(LogKaydi.objects.filter(fiil="duzeltme_yayimlama").count(), 1)

    def test_baska_haberin_notu_bu_uctan_kaldirilamaz(self):
        kayit = self._not(haber=self.notsuz)
        self._gir("Editör")
        yanit = self.client.post(self._uc(), {"islem": "kaldir", "duzeltme": kayit.pk})
        self.assertEqual(yanit.status_code, 404)
        self.assertEqual(self.client.post(self._uc(), {"islem": "kaldir",
                                                       "duzeltme": "abc"}).status_code, 404)
        kayit.refresh_from_db()
        self.assertTrue(kayit.yayinda)


# ------------------------------------------------------------------ haber detayı

class HaberDetayi(Temel):

    def test_not_yoksa_blok_isaret_ve_jsonld_alani_yok(self):
        html = self._sayfa(self.notsuz.get_absolute_url())
        self.assertNotIn("duzeltme-bolmesi", html)
        self.assertNotIn("duzeltme-isaret", html)
        self.assertNotIn('id="duzeltmeler"', html)
        self.assertNotIn("correction", _makale(html))

    def test_kaldirilan_not_basilmaz(self):
        self._not(yayinda=False)
        html = self._sayfa(self.haber.get_absolute_url())
        self.assertNotIn("duzeltme-bolmesi", html)
        self.assertNotIn("duzeltme-isaret", html)

    def test_blok_govdenin_sonunda_isaret_basligin_altinda(self):
        self._not(metin="Açılış saati <script>alert(1)</script> yanlıştı.\n\nDoğrusu 11.00.")
        html = self._sayfa(self.haber.get_absolute_url())
        h1 = html.index("<h1>")
        isaret = html.index('<p class="duzeltme-isaret"><a href="#duzeltmeler">'
                            'Bu haberde düzeltme var</a></p>')
        kunye = html.index('class="detay-kunye"')
        metin = html.index('<div class="metin">')
        blok = html.index('<section class="duzeltme-bolmesi" id="duzeltmeler"')
        self.assertLess(h1, isaret)
        self.assertLess(isaret, kunye)
        self.assertLess(metin, blok)
        # Gövdenin hemen sonunda: gövde ile blok arasında başka bölüm yok.
        self.assertNotIn("<section", html[metin:blok])
        self.assertLess(blok, html.index("İLGİLİ HABERLER"))
        bolme = html[blok:html.index("</section>", blok)]
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", bolme)
        self.assertNotIn("<script>alert", html)
        self.assertIn("<p>Açılış saati", bolme)
        self.assertIn("<p>Doğrusu 11.00.</p>", bolme)
        self.assertRegex(bolme, r'<b class="duzeltme-tur">Düzeltme</b> <time datetime="[^"]+">')
        self.assertIn('<a href="/duzeltmeler">', bolme)

    def test_cevap_veren_ve_sira(self):
        self._not(tur=Duzeltme.TUR_GUNCELLEME, metin="Köprüye yaya yolu da eklendi.", once=60)
        self._not(tur=Duzeltme.TUR_CEVAP, veren="Nilüfer Belediyesi Basın Birimi",
                  metin="Belediyenin gönderdiği cevap metni.", once=5)
        html = self._sayfa(self.haber.get_absolute_url())
        self.assertIn("Bu habere cevap yayımlandı", html)
        self.assertIn('<p class="duzeltme-veren">Cevap veren: Nilüfer Belediyesi Basın Birimi</p>',
                      html)
        self.assertLess(html.index("yaya yolu"), html.index("Belediyenin gönderdiği"))
        # Cevap ve güncelleme notu `correction` değildir.
        self.assertNotIn("correction", _makale(html))


class JsonLd(Temel):

    def test_duzeltme_correction_comment(self):
        kayit = self._not()
        self._not(tur=Duzeltme.TUR_CEVAP, veren="Kurum", metin="Kurumun cevap metni.")
        makale = _makale(self._sayfa(self.haber.get_absolute_url()))
        self.assertEqual(len(makale["correction"]), 1)
        yorum = makale["correction"][0]
        self.assertEqual(yorum["@type"], "CorrectionComment")
        self.assertEqual(yorum["text"], kayit.metin)
        self.assertTrue(yorum["datePublished"].startswith(
            timezone.localtime(kayit.yayin_zamani).strftime("%Y-%m-%dT%H:%M")))


# ------------------------------------------------------------------ /duzeltmeler

class DuzeltmelerSayfasi(Temel):

    def test_adres_kategori_sanilmiyor_ve_egik_cizgi(self):
        self.assertEqual(resolve("/duzeltmeler").url_name, "duzeltmeler")
        yanit = self.client.get("/duzeltmeler/")
        self.assertEqual(yanit.status_code, 301)
        self.assertEqual(yanit["Location"], "/duzeltmeler")

    def test_bos_sayfa_uydurma_icerik_yok(self):
        html = self._sayfa("/duzeltmeler")
        self.assertIn("Yayımlanmış düzeltme ya da cevap notu yok.", html)
        self.assertNotIn('class="duzeltme"', html)
        self.assertEqual(html.count("<h1"), 1)

    def test_en_yeniden_eskiye_haberine_bagli(self):
        self._not(metin="Eski düzeltmenin metni burada.", once=120)
        self._not(tur=Duzeltme.TUR_CEVAP, veren="Kurum Sözcüsü",
                  metin="Yeni cevabın metni burada.", once=1)
        self._not(metin="Kaldırılan notun metni.", yayinda=False)
        self._not(haber=self.pasif, metin="Pasif haberin notu metni.")
        html = self._sayfa("/duzeltmeler")
        self.assertLess(html.index("Yeni cevabın"), html.index("Eski düzeltmenin"))
        self.assertNotIn("Kaldırılan notun", html)
        self.assertNotIn("Pasif haberin", html)
        self.assertEqual(html.count('<li class="duzeltme"'), 2)
        self.assertIn(f'href="{self.haber.get_absolute_url()}#duzeltmeler"', html)
        self.assertIn("Cevap veren: Kurum Sözcüsü", html)
        self.assertIn(">2 not<", html)

    def test_seo_ve_sayfalama(self):
        self._not()
        html = self._sayfa("/duzeltmeler")
        self.assertIn("<title>Düzeltme ve Cevap — Bursa Hakimiyet</title>", html)
        self.assertRegex(html, r'<link rel="canonical" href="https?://[^"]+/duzeltmeler">')
        kirinti = next(b for b in _ld(html) if b.get("@type") == "BreadcrumbList")
        self.assertEqual([o["name"] for o in kirinti["itemListElement"]],
                         ["Anasayfa", "Düzeltme ve Cevap"])
        for deger in ("2", "0", "abc"):
            with self.subTest(deger):
                self.assertEqual(self.client.get(f"/duzeltmeler?sayfa={deger}").status_code, 404)

    def test_giris_metni_hukuki_iddia_tasimaz(self):
        """Hukuki metin `hukuk-guvenlik-uyum-uzmani`ndan gelir; giriş olgusal."""
        html = self._sayfa("/duzeltmeler")
        giris = re.search(r'<p class="duzeltme-giris">(.*?)</p>', html, re.S).group(1)
        for yasak in ("5187", "Basın Kanunu", "madde", "hakkı", "hukuk", "yasa", "gün içinde"):
            self.assertNotIn(yasak, giris)


# ------------------------------------------------------------------ önbellek ve başarım

@SAYFA_ACIK
class Onbellek(Temel):

    def test_not_kaydi_haber_ve_dizin_onbellegini_dusurur(self):
        adres = self.haber.get_absolute_url()
        for yol in (adres, "/duzeltmeler"):
            self.assertEqual(self.client.get(yol)["X-Onbellek"], "kayit")
            self.assertEqual(self.client.get(yol)["X-Onbellek"], "isabet")
        kayit = self._not(metin="Önbelleği düşüren düzeltme metni.")
        for yol in (adres, "/duzeltmeler"):
            yanit = self.client.get(yol)
            self.assertEqual(yanit["X-Onbellek"], "kayit", yol)
            self.assertIn("Önbelleği düşüren", yanit.content.decode())
        # Yayından kaldırma da (save) düşürür.
        kayit.yayinda = False
        kayit.save()
        yanit = self.client.get(adres)
        self.assertEqual(yanit["X-Onbellek"], "kayit")
        self.assertNotIn("Önbelleği düşüren", yanit.content.decode())


class Basarim(Temel):

    def _say(self, yol):
        with CaptureQueriesContext(connection) as yakala:
            yanit = self.client.get(yol)
        self.assertEqual(yanit.status_code, 200, yol)
        return len(yakala.captured_queries)

    def _isinmis(self, yol):
        """Kayıt sinyali son dakika bandının önbelleğini de düşürür
        (`sinyaller._surum`); kabuk ısındıktan sonra yalnız sayfanın
        kendi sorguları sayılır."""
        self._say(yol)
        return self._say(yol)

    def test_haber_detayi_sorgusu_notla_buyumuyor(self):
        adres = self.haber.get_absolute_url()
        notsuz = self._isinmis(adres)
        self._not()
        bir = self._isinmis(adres)
        for n in range(6):
            self._not(tur=Duzeltme.TUR_GUNCELLEME, metin=f"Güncelleme notu numara {n}.")
        yedi = self._isinmis(adres)
        self.assertEqual(bir, yedi)
        # Notsuz haberde EK SORGU YOK (EXISTS ana sorguda); notlu haberde tek.
        self.assertEqual(bir, notsuz + 1)

    def test_dizin_sorgusu_notla_buyumuyor(self):
        self._not()
        az = self._isinmis("/duzeltmeler")
        haberler = [Haber.objects.create(
            id=8810000 + n, slug=f"b-{n}", baslik=f"Haber {n}", spot="S",
            govde="<p>a</p><p>b</p>", kategori=self.gundem, durum=Haber.DURUM_AKTIF,
            yayin_zamani=timezone.now() - timedelta(hours=n + 1)) for n in range(12)]
        for h in haberler:
            self._not(haber=h, tur=Duzeltme.TUR_CEVAP, veren="Kurum")
        cok = self._isinmis("/duzeltmeler")
        self.assertEqual(az, cok)
        self.assertLessEqual(cok, 3)     # sayım + dilim (+ oturumsuz kabuk ısınmış)
