"""Testsiz yönetim komutları — kuru koşu ve idempotans (Paket K, 19 Ekim 2026).

DEGERLENDIRME-2026-10 §4: "18 yönetim komutunun 10'u (1 milyon satıra yazan
onarım komutları dahil) testsiz." Her komut için en az:

* **kuru koşu** (`--kuru` / `--dene` / `--deneme`) veritabanına ve diske
  hiçbir şey yazmaz;
* gerçek koşu beklenen değişikliği yapar;
* **ikinci koşu aynı sonucu verir** (idempotans) — bu komutlar 1 milyon
  satırlık tabloda yeniden çalıştırılıyor; ikinci turda bir şey daha
  "düzeltmek" veriyi bozuyor demektir.

Ağ YOK: `yazar_portre_indir` indirme işlevi yamalanır, `site_haritasi_karsilastir`
yalnız `--arsiv-kok` yoluyla sınanır, `taslak_al` köprüsü yamalanır.
Arşiv/türev kökleri her testte geçici klasör (test ayarındaki kök zaten var
olmayan bir yol; bkz. cekirdek/tests_hermetik.py).
"""

from __future__ import annotations

import io
import json
import shutil
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest import mock

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings
from django.utils import timezone

from medya.models import Yazar
from taksonomi.models import Ilce, Kategori, KategoriTur, Kaynak

from .models import Haber
from .temizle import metin_duzelt


def _kos(komut, *argumanlar, **secenek):
    cikti = io.StringIO()
    call_command(komut, *argumanlar, stdout=cikti, stderr=io.StringIO(), **secenek)
    return cikti.getvalue()


class Temel(TestCase):

    @classmethod
    def setUpTestData(cls):
        call_command("taksonomi_kur", verbosity=0)
        cls.gundem = KategoriTur.objects.get(tur=Kategori.TUR_HABER, slug="gundem").kategori

    def setUp(self):
        self.gecici = Path(tempfile.mkdtemp(prefix="bh-komut-"))
        self.addCleanup(shutil.rmtree, self.gecici, ignore_errors=True)

    def haber(self, n, **ek):
        alanlar = dict(id=950000 + n, slug=f"komut-{n}", baslik=f"Komut haberi {n}",
                       spot="spot", govde="<p>a</p><p>b</p>", kategori=self.gundem,
                       durum=Haber.DURUM_AKTIF,
                       yayin_zamani=timezone.now() - timedelta(days=1, minutes=n))
        alanlar.update(ek)
        return Haber.objects.create(**alanlar)

    def durum(self, *alanlar):
        """Haber tablosunun karşılaştırılabilir fotoğrafı."""
        return list(Haber.objects.order_by("pk").values_list("pk", *alanlar))


# --------------------------------------------------------------------------
# ilce_doldur

class IlceDoldur(Temel):

    def setUp(self):
        super().setUp()
        self.osmangazi = Ilce.objects.get(slug="osmangazi")
        self.nilufer = Ilce.objects.get(slug="nilufer")
        self.haber(1, baslik="Osmangazi'de yol çalışması")
        self.haber(2, baslik="Nilüfer'de yeni park", ilce=self.osmangazi)  # elle girilmiş
        self.haber(3, baslik="Ankara'da toplantı")

    def test_kuru_yazmaz(self):
        once = self.durum("ilce")
        _kos("ilce_doldur", kuru=True)
        self.assertEqual(self.durum("ilce"), once)

    def test_doldurur_dolu_alani_ezmez_ve_tekrarda_ayni(self):
        _kos("ilce_doldur")
        ilk = self.durum("ilce")
        self.assertEqual(dict((pk, i) for pk, i in ilk),
                         {950001: self.osmangazi.pk, 950002: self.osmangazi.pk, 950003: None})
        _kos("ilce_doldur")
        self.assertEqual(self.durum("ilce"), ilk)

    def test_uzerine_yaz_secenegi(self):
        _kos("ilce_doldur", uzerine_yaz=True)
        self.assertEqual(Haber.objects.get(pk=950002).ilce, self.nilufer)


# --------------------------------------------------------------------------
# metin_temizle

class MetinTemizle(Temel):

    KIRLI = "Ug&#774;ur Aslan​ geldi"

    def setUp(self):
        super().setUp()
        self.haber(1, baslik=self.KIRLI, spot="Atatürk  caddesi")
        self.haber(2, baslik="Temiz başlık", spot="Temiz spot")

    def test_dene_yazmaz(self):
        once = self.durum("baslik", "spot")
        cikti = _kos("metin_temizle", dene=True)
        self.assertIn("deneme turu", cikti)
        self.assertEqual(self.durum("baslik", "spot"), once)

    def test_onarir_ve_ikinci_tur_bos(self):
        _kos("metin_temizle")
        h = Haber.objects.get(pk=950001)
        self.assertEqual(h.baslik, metin_duzelt(self.KIRLI))
        self.assertNotIn("&#", h.baslik)
        self.assertNotIn("​", h.baslik)
        self.assertEqual(Haber.objects.get(pk=950002).baslik, "Temiz başlık")
        ilk = self.durum("baslik", "spot", "govde", "slug")
        cikti = _kos("metin_temizle")
        self.assertIn("düzelen 0", cikti)
        self.assertEqual(self.durum("baslik", "spot", "govde", "slug"), ilk)


# --------------------------------------------------------------------------
# kaynak_denetle

class KaynakDenetle(Temel):

    def setUp(self):
        super().setUp()
        self.iyi = Kaynak.objects.create(ad="Milliyet")
        self.kotu = Kaynak.objects.create(ad="Haber Merkezi")
        h1, h2 = self.haber(1), self.haber(2)
        h1.kaynaklar.add(self.iyi, self.kotu)
        h2.kaynaklar.add(self.kotu)
        self.ara = Haber.kaynaklar.through

    def _baglar(self):
        return sorted(self.ara.objects.values_list("haber_id", "kaynak_id"))

    def test_kuru_silmez(self):
        once = self._baglar()
        _kos("kaynak_denetle", kuru=True)
        self.assertEqual(self._baglar(), once)

    def test_yanlis_bagi_koparir_kaydi_silmez_tekrarda_ayni(self):
        _kos("kaynak_denetle")
        self.assertEqual(self._baglar(), [(950001, self.iyi.pk)])
        self.assertTrue(Kaynak.objects.filter(pk=self.kotu.pk).exists())
        _kos("kaynak_denetle")
        self.assertEqual(self._baglar(), [(950001, self.iyi.pk)])


# --------------------------------------------------------------------------
# goc_al

class GocAl(Temel):

    def _dosya(self, kimlik, **ek):
        d = {"url": f"https://www.bursahakimiyet.com.tr/gundem/goc-haberi-{kimlik}",
             "kategori": "gundem", "baslik": f"Göç haberi {kimlik} Osmangazi'de",
             "spot": "Spot", "govde_html": "<p>a</p><p>b</p>",
             "yayin_tarihi": "2025-03-04T10:20:30", "kaynak": "Milliyet",
             "kelime_sayisi": 4, "ayiklama_guveni": "yuksek"}
        d.update(ek)
        klasor = self.gecici / "2025-03"
        klasor.mkdir(exist_ok=True)
        (klasor / f"{kimlik}.json").write_text(json.dumps(d, ensure_ascii=False),
                                               encoding="utf-8")

    def setUp(self):
        super().setUp()
        self._dosya(940001)
        self._dosya(940002, kaynak="Haber Merkezi")        # kapıdan geçmez
        self._dosya(940003, kategori="olmayan-kategori")   # alınmaz
        (self.gecici / "2025-03" / "bozuk.json").write_text("{", encoding="utf-8")

    def test_kuru_yazmaz(self):
        _kos("goc_al", kaynak=str(self.gecici), kuru=True)
        self.assertFalse(Haber.objects.exists())
        self.assertFalse(Kaynak.objects.filter(ad="Milliyet").exists())

    def test_alir_ve_ikinci_kosu_ayni_sonuc(self):
        cikti = _kos("goc_al", kaynak=str(self.gecici))
        self.assertIn("kategori taninmadi", cikti)
        alanlar = ("slug", "baslik", "kategori", "ilce", "yayin_zamani", "durum")
        ilk = self.durum(*alanlar)
        self.assertEqual([r[0] for r in ilk], [940001, 940002])
        self.assertEqual(Haber.objects.get(pk=940001).ilce.slug, "osmangazi")
        baglar = sorted(Haber.kaynaklar.through.objects.values_list("haber_id", "kaynak__ad"))
        self.assertEqual(baglar, [(940001, "Milliyet")])
        _kos("goc_al", kaynak=str(self.gecici))
        self.assertEqual(self.durum(*alanlar), ilk)
        self.assertEqual(Kaynak.objects.filter(ad="Milliyet").count(), 1)
        self.assertEqual(sorted(Haber.kaynaklar.through.objects.values_list(
            "haber_id", "kaynak__ad")), baglar)

    def test_yalniz_yeni_var_olani_okumaz(self):
        _kos("goc_al", kaynak=str(self.gecici))
        Haber.objects.filter(pk=940001).update(baslik="elle düzeltildi")
        cikti = _kos("goc_al", kaynak=str(self.gecici), yalniz_yeni=True)
        self.assertIn("atlandi (zaten var)", cikti)
        self.assertEqual(Haber.objects.get(pk=940001).baslik, "elle düzeltildi")

    def test_kaynak_klasoru_yoksa_yazmaz(self):
        _kos("goc_al", kaynak=str(self.gecici / "yok"))
        self.assertFalse(Haber.objects.exists())


# --------------------------------------------------------------------------
# meta_yazar_doldur

class MetaYazarDoldur(Temel):

    def _arsiv(self, kimlik, kaynak):
        klasor = self.gecici / "veri" / "2025-03"
        klasor.mkdir(parents=True, exist_ok=True)
        (klasor / f"{kimlik}.json").write_text(json.dumps({"kaynak": kaynak}),
                                               encoding="utf-8")

    def setUp(self):
        super().setUp()
        Yazar.objects.create(id=9501, slug="ayse-yazar", ad="Ayşe Yazar",
                             sayfasi_tarandi=False)
        for n, kaynak in enumerate(["Haber Merkezi", "AA", "Ayşe Yazar",
                                    "Milliyet", "seçiniz"], 1):
            self.haber(n)
            self._arsiv(950000 + n, kaynak)
        self.haber(6)
        Haber.objects.filter(pk=950006).update(meta_yazar="bulten", meta_yazar_elle=True)
        self._arsiv(950006, "AA")
        # Kaydın save() türetimini atlatıp "henüz sınıflanmamış" hâle getir.
        Haber.objects.exclude(pk=950006).update(meta_yazar="", kaynak_turu="")

    def test_kuru_yazmaz(self):
        once = self.durum("meta_yazar", "kaynak_turu")
        _kos("meta_yazar_doldur", kok=str(self.gecici / "veri"), kuru=True)
        self.assertEqual(self.durum("meta_yazar", "kaynak_turu"), once)

    def test_siniflar_elle_girileni_korur_tekrarda_ayni(self):
        _kos("meta_yazar_doldur", kok=str(self.gecici / "veri"))
        ilk = dict((pk, (m, t)) for pk, m, t in self.durum("meta_yazar", "kaynak_turu"))
        self.assertEqual(ilk[950001], ("haber_merkezi", ""))
        self.assertEqual(ilk[950002], ("haber_ajansi", Haber.KAYNAK_AJANS))
        self.assertEqual(ilk[950003], ("fikir_iscisi", Haber.KAYNAK_MUHABIR))
        self.assertEqual(ilk[950004], ("alinti", Haber.KAYNAK_DIS_YAYIN))
        self.assertEqual(ilk[950005], ("", ""))              # belirsiz: dokunulmadı
        self.assertEqual(ilk[950006][0], "bulten")           # elle girilen korundu
        _kos("meta_yazar_doldur", kok=str(self.gecici / "veri"))
        self.assertEqual(dict((pk, (m, t)) for pk, m, t in
                              self.durum("meta_yazar", "kaynak_turu")), ilk)


# --------------------------------------------------------------------------
# taslak_al (köprü yamalı — ağ yok)

class TaslakAl(Temel):

    def test_kullanici_yoksa_hata(self):
        with self.assertRaises(CommandError):
            _kos("taslak_al", "https://ornek.example/haber", kullanici="yok")
        with self.assertRaises(CommandError):
            _kos("taslak_al", "https://ornek.example/haber")   # yönetici hesabı yok

    def test_kopru_hatasi_komut_hatasina_doner(self):
        from django.contrib.auth.models import User

        from .yz_kopru import YzHatasi
        User.objects.create_superuser("yonetici", password="x-parola-123")
        with mock.patch("icerik.management.commands.taslak_al.taslak_al",
                        side_effect=YzHatasi("sayfa okunamadı")):
            with self.assertRaisesMessage(CommandError, "sayfa okunamadı"):
                _kos("taslak_al", "https://ornek.example/haber")

    def test_taslak_ozeti_basilir(self):
        from django.contrib.auth.models import User
        kullanici = User.objects.create_user("muhabir", password="x-parola-123")
        haber = self.haber(1, durum=Haber.DURUM_PASIF)
        sahte = mock.Mock(return_value=(haber, {"kaynak": {"kaynak_adi": "Ornek"}},
                                        ["not satırı"]))
        with mock.patch("icerik.management.commands.taslak_al.taslak_al", sahte):
            cikti = _kos("taslak_al", "https://ornek.example/haber", kullanici="muhabir")
        sahte.assert_called_once_with("https://ornek.example/haber", kullanici, "kural")
        self.assertIn(f"Taslak açıldı: #{haber.pk}", cikti)
        self.assertIn("not satırı", cikti)


# --------------------------------------------------------------------------
# site_haritasi_uret / site_haritasi_karsilastir

class SiteHaritasiKomutlari(Temel):

    def setUp(self):
        super().setUp()
        for n, ay in enumerate((1, 1, 2), 1):
            self.haber(n, yayin_zamani=timezone.make_aware(datetime(2025, ay, 10 + n)))
        self.cikti = self.gecici / "sitemap"

    def test_kuru_dosya_yazmaz(self):
        _kos("site_haritasi_uret", kok=str(self.cikti), kuru=True, cozumleme_yok=True)
        self.assertFalse(self.cikti.exists())

    def test_uretir_ve_ikinci_kosu_ayni_dosyalar(self):
        _kos("site_haritasi_uret", kok=str(self.cikti), site_koku="https://ornek.example")
        aylik = {p.name: p.read_bytes() for p in self.cikti.glob("news_*.xml")}
        self.assertEqual(set(aylik), {"news_2025-01.xml", "news_2025-02.xml"})
        self.assertEqual(aylik["news_2025-01.xml"].count(b"<url>"), 2)
        self.assertIn(b"https://ornek.example/", aylik["news_2025-01.xml"])
        self.assertTrue((self.cikti / "sitemap.xml").is_file())
        self.assertEqual(list(self.cikti.glob("*.tmp")), [])
        _kos("site_haritasi_uret", kok=str(self.cikti), site_koku="https://ornek.example")
        self.assertEqual({p.name: p.read_bytes() for p in self.cikti.glob("news_*.xml")},
                         aylik)

    def test_tek_ay_indeks_yazmaz(self):
        _kos("site_haritasi_uret", kok=str(self.cikti), ay=["2025-02"], cozumleme_yok=True)
        self.assertEqual([p.name for p in self.cikti.iterdir()], ["news_2025-02.xml"])

    def _jsonl(self, ekstra=0):
        """Bizim sayılarımızla birebir kaynak dosyaları (+ `ekstra` fark)."""
        from besleme.aileler import kayitli_aileler
        kok = self.gecici / "arsiv"
        kok.mkdir()
        for aile in kayitli_aileler():
            ek = "" if aile.anahtar == "haber" else f"-{aile.anahtar}"
            satirlar = [json.dumps({"url": "x", "ay": o.ay})
                        for o in aile.aylar() for _ in range(o.adet)]
            if aile.anahtar == "haber":
                satirlar += [json.dumps({"url": "x", "ay": "2025-01"})] * ekstra
            (kok / f"tum-urller{ek}.jsonl").write_text("\n".join(satirlar) + "\n",
                                                        encoding="utf-8")
        return kok

    def test_karsilastir_esitse_temiz_cikar(self):
        cikti = _kos("site_haritasi_karsilastir", arsiv_kok=str(self._jsonl()))
        self.assertIn("eşleşiyor", cikti)

    def test_karsilastir_fark_varsa_cikis_kodu_1(self):
        with self.assertRaises(SystemExit) as c:
            _kos("site_haritasi_karsilastir", arsiv_kok=str(self._jsonl(ekstra=1)))
        self.assertEqual(c.exception.code, 1)

    def test_karsilastir_kaynaksiz_calismaz(self):
        with self.assertRaises(CommandError):
            _kos("site_haritasi_karsilastir")
        with self.assertRaises(CommandError):
            _kos("site_haritasi_karsilastir", arsiv_kok=str(self.gecici / "yok"))


# --------------------------------------------------------------------------
# gorsel_turev_uret

class GorselTurevUret(Temel):

    def setUp(self):
        super().setUp()
        from PIL import Image
        arsiv, turev = self.gecici / "arsiv", self.gecici / "turev"
        yol = arsiv / "gorseller" / "2025-03" / "k_large.jpg"
        yol.parent.mkdir(parents=True)
        Image.new("RGB", (1500, 1000), (20, 90, 160)).save(yol, "JPEG")
        ayar = override_settings(ARSIV_KOK=arsiv, TUREV_KOK=turev,
                                 ARSIV_GORSEL_KOK=arsiv / "gorseller")
        ayar.enable()
        self.addCleanup(ayar.disable)
        self.turev = turev
        self.haber(1, gorsel_var=True, gorsel_dosya="2025-03/k_large.jpg",
                   yayin_zamani=timezone.make_aware(datetime(2025, 3, 5)))

    def _dosyalar(self):
        return sorted(p.relative_to(self.turev).as_posix()
                      for p in self.turev.rglob("*") if p.is_file())

    def test_kuru_uretmez(self):
        cikti = _kos("gorsel_turev_uret", kuru=True, vitrin_yok=True)
        self.assertIn("tekil kaynak: 1", cikti)
        self.assertFalse(self.turev.exists() and any(self.turev.rglob("*.webp")))

    def test_uretir_ikinci_kosu_atlar(self):
        cikti = _kos("gorsel_turev_uret", vitrin_yok=True, referans="2025-03-05",
                     genislikler="320,640", isci=1)
        self.assertIn("3 türev üretildi", cikti)   # 320 + 640 + og
        ilk = self._dosyalar()
        self.assertTrue(any(d.startswith("320/") for d in ilk), ilk)
        self.assertTrue(any(d.startswith("og/") for d in ilk), ilk)
        cikti = _kos("gorsel_turev_uret", vitrin_yok=True, referans="2025-03-05",
                     genislikler="320,640", isci=1)
        self.assertIn("0 türev üretildi", cikti)
        self.assertEqual(self._dosyalar(), ilk)

    def test_beyaz_liste_disi_genislik(self):
        with self.assertRaises(CommandError):
            _kos("gorsel_turev_uret", genislikler="333", vitrin_yok=True)


# --------------------------------------------------------------------------
# yazar_portre_indir (indirme yamalı — ağ yok)

JPEG = b"\xff\xd8\xff\xe0" + b"0" * 64


class YazarPortreIndir(Temel):

    def setUp(self):
        super().setUp()
        self.arsiv = self.gecici / "arsiv"
        ayar = override_settings(ARSIV_KOK=self.arsiv)
        ayar.enable()
        self.addCleanup(ayar.disable)
        self.yeni = Yazar.objects.create(
            id=9511, slug="yeni-yazar", ad="Yeni Yazar", sayfasi_tarandi=False,
            gorsel_url="https://www.bursahakimiyet.com.tr/cdn/i=/1200x630/webp/"
                       "2025/03/04/yeni-yazar_large.webp")
        self.eski = Yazar.objects.create(
            id=9512, slug="eski-yazar", ad="Eski Yazar", sayfasi_tarandi=False,
            gorsel_url="https://www.bursahakimiyet.com.tr/cdn/i=/1200x630/webp/"
                       "2022/01/13/eski-yazar.jpg")
        self.klasor = self.arsiv / "gorseller-yazar" / "portre"

    @staticmethod
    def _indir(adres):
        if adres.endswith("yeni-yazar_small.jpg") or adres.endswith("eski-yazar.jpg"):
            return JPEG
        return b"<html>404</html>"

    def _kos(self, **s):
        sahte = mock.Mock(side_effect=self._indir)
        with mock.patch("medya.management.commands.yazar_portre_indir._indir", sahte), \
             mock.patch("medya.management.commands.yazar_portre_indir.time.sleep"):
            cikti = _kos("yazar_portre_indir", **s)
        return cikti, sahte

    def test_deneme_yazmaz(self):
        self._kos(deneme=True)
        self.assertFalse(self.klasor.exists())
        self.assertFalse(Yazar.objects.filter(gorsel_var=True).exists())

    def test_indirir_bicimi_secer_ikinci_kosu_indirmez(self):
        self._kos()
        self.assertEqual(Yazar.objects.get(pk=9511).gorsel_dosya,
                         "gorseller-yazar/portre/yeni-yazar-portre.jpg")
        self.assertEqual(Yazar.objects.get(pk=9512).gorsel_dosya,
                         "gorseller-yazar/portre/eski-yazar-afis-beton.jpg")
        kayit = (self.klasor / "KAYNAK.tsv").read_text(encoding="utf-8")
        cikti, sahte = self._kos()
        sahte.assert_not_called()
        self.assertIn("2 zaten vardı", cikti)
        self.assertEqual((self.klasor / "KAYNAK.tsv").read_text(encoding="utf-8"), kayit)
        self.assertEqual(sorted(p.name for p in self.klasor.glob("*.jpg")),
                         ["eski-yazar-afis-beton.jpg", "yeni-yazar-portre.jpg"])


# --------------------------------------------------------------------------
# okunma_bosalt — kuyruk boşken de temiz çıkar, ikinci koşu bir şey yazmaz

class OkunmaBosalt(Temel):

    def test_bos_kuyruk_ve_tekrar(self):
        kuyruk = self.gecici / "kuyruk"
        with override_settings(OKUNMA_KUYRUK_KOK=kuyruk):
            ilk = _kos("okunma_bosalt")
            ikinci = _kos("okunma_bosalt")
        self.assertIn("0 kova yazıldı", ilk)
        self.assertIn("0 kuyruk dosyası, 0 kova yazıldı", ikinci)
