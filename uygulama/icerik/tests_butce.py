"""Başarım bütçesi — sorgu sayısı tavanı, HTML boyutu, sayfa önbelleği.

Paket K (19 Ekim 2026). Başarım paketi (A) sorgu sayılarını ölçtü ve
düşürdü; bu dosya düşen sayının sessizce geri tırmanmasını engeller. Tavan
ölçülen değerin biraz ÜSTÜ: tek bir yeni sorgu bütçeyi bozmaz, döngüye
düşmüş sorgu (N+1) bozar. Bu yüzden her sayfa iki kez ölçülür — az kayıtla
ve çok kayıtla — ve sayının kayıt sayısıyla BÜYÜMEMESİ ayrıca denetlenir.

Ölçüm (bu dosyanın verisiyle, önbelleksiz, 19 Ekim 2026) `TAVAN` sözlüğünün
yanında yazılı. Tavanı yükseltmek gerekiyorsa önce sorgunun neden geldiği
bulunur; "test kırmızı, sayıyı artır" çözüm değildir.

Canlı veri dosyalarına bağlı değil (test ayarı depodaki fixture'ı okur, bkz.
cekirdek/tests_hermetik.py); sonuç paket J'nin bayatlık değişikliğinden
bağımsız olsun diye canlı bileşenlerin İÇERİĞİ denetlenmez.
"""

from __future__ import annotations

import os
import re
from datetime import timedelta

from django.core.management import call_command
from django.db import connection
from django.test import TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from medya.models import KoseYazisi, Yazar
from taksonomi.models import Ilce, Kategori, KategoriTur

from . import okunma
from .models import Haber

LOCMEM = "django.core.cache.backends.locmem.LocMemCache"
SAYFA_ACIK = override_settings(
    CACHES={"default": {"BACKEND": LOCMEM, "LOCATION": "bh-butce-veri"},
            "sayfa": {"BACKEND": LOCMEM, "LOCATION": "bh-butce-sayfa"}},
    SAYFA_ONBELLEK_SANIYE=30)

# Sayfa adı → önbelleksiz istekteki sorgu tavanı (yollar: `Temel.yollar`).
#             ölçülen az kayıt / 4 kat kayıt
TAVAN = {
    "anasayfa": 30,             # 24 / 24 (L2: yazar kuşağı tek sorgu)
    "haber_detay": 12,          # 12 / 12 (H: editörün ilgili seçimi + etiketler)
    "kategori_bursa": 12,       #  7 / 7
    "kategori_ekonomi": 12,     #  9 / 7
    "kategori_bursaspor": 12,   #  7 / 7
    "ilce": 10,                 #  5 / 5
    # 11 / 14 idi — BÜYÜYORDU: "yazarın diğer yazıları" her kalem için
    # yazarı ayrıca çekiyordu. Paket L2: `select_related("yazar")` +
    # raydaki yazarların son yazısı tek sorguda (`Yazar.son_yazisiyla`).
    "kose_yazisi": 12,          #  7 / 7
    #  1 / 1 — yazar başına "son yazı" sorgusu kalktı (Paket L2; PG'de 38 idi).
    "yazarlar": 4,
    # 19 Ekim 2026: sayım + akış dilimi + yazar başına son yazı (tek sorgu,
    # `KoseYazisi.yazar_basina_son`). Yazar sayısı çok kayıt turunda büyüyor.
    "kose_yazilari": 6,         #  3 / 3
    "konular": 4,               #  2 / 2
}

#: PostgreSQL'de motora özgü EK sorgular (Paket L2). İlgili haberin PG yolu
#: iki sorgu daha açar: pencere uçlarının kimlik yoklaması (istek başına) ve
#: ağır çapa istatistiği (`pg_stats`; süreç başına günde BİR kez, burada
#: soğuk süreç ölçüldüğü için sayılıyor). Sabit bedeldir, kayıtla büyümez —
#: çok kayıt turu bunu ayrıca denetler.
PG_EK = {"haber_detay": 2}


def tavan(ad: str) -> int:
    return TAVAN[ad] + (PG_EK.get(ad, 0) if connection.vendor == "postgresql" else 0)

#: Anasayfa HTML'i (sıkıştırmasız) en çok bu kadar.
#:
#: DİKKAT (20 Ekim 2026 ölçümü): bu tavan bu dosyanın KÜÇÜK verisiyle
#: sınanıyor. Gerçek veriyle (PG, 1.038.474 haber) anasayfa 229–234 KB
#: açılmış / 35 KB gzip — 200 KB'ı aşıyor. Payı ardışık boşluk (%17),
#: `<img>` srcset'leri (%22) ve SVG sembol kütüphanesi (%8) yiyor. Gerçek
#: veri tavanı `tests_sayfa_butcesi.HTML_TAVAN_KB` (tarayıcıda, isteğe bağlı).
ANASAYFA_HTML_TAVAN = 200 * 1024

#: Diğer sayfaların HTML'i (sıkıştırmasız, bu dosyanın verisiyle). 20 Ekim
#: 2026'ya kadar detayda HİÇ tavan yoktu (referans kütüphanesi fark matrisi,
#: satır 3). Ölçülen değer yanında; pay ~%25 — şablona yeni bir blok girer,
#: bir sembol kütüphanesi ya da gömülü veri yığını girmez. Gerçek veriyle
#: ölçüm ve tavan: `tests_sayfa_butcesi`.
HTML_TAVAN = {              # KB   ölçülen az kayıt / 4 kat kayıt (B)
    "haber_detay": 58,      #      45.940 / 45.961  (gerçek veri: 58 KB)
    "kategori_ekonomi": 65,  #     46.973 / 51.940  (gerçek veri: 83 KB)
    "ilce": 64,             #      50.490 / 50.467  (gerçek veri: 72 KB)
}

#: Okurun sayfası kaç ayrı betik/stil DOSYASI istiyor (sunum araçları hariç:
#: test istemcisinin Host'u yerel değil, `baglam.sunum_araci_mi` kapalı).
#: 20 Ekim 2026 tarayıcı ölçümü: her sayfada 1 betik (site.js) + okunan
#: metinde seslendirme.js; 2 stil (site.css, fontlar.css). Yeni bir dosya
#: her ziyarette bir istek daha demek — bilinçli eklenir, sayı da artırılır.
BETIK_TAVAN = {"haber_detay": 2, "kose_yazisi": 2}
BETIK_TAVAN_VARSAYILAN = 1
STIL_TAVAN = 2


class Temel(TestCase):
    ARTIS = 0  # alt sınıf "çok kayıt" turu için ek haber sayısı

    @classmethod
    def setUpTestData(cls):
        call_command("taksonomi_kur", verbosity=0)
        cls.kategoriler = {
            kt.slug: kt.kategori for kt in
            KategoriTur.objects.filter(tur=Kategori.TUR_HABER).select_related("kategori")}
        cls.ilce = Ilce.objects.get(slug="osmangazi")
        simdi = timezone.now()
        adet = 40 + cls.ARTIS
        sluglar = sorted(cls.kategoriler)
        for n in range(adet):
            slug = sluglar[n % len(sluglar)]
            Haber.objects.create(
                id=960000 + n, slug=f"butce-{n}", baslik=f"Bütçe haberi {n}",
                spot="Spot metni", govde="<p>Birinci paragraf.</p><p>İkinci.</p>",
                kategori=cls.kategoriler[slug],
                ilce=cls.ilce if n % 3 == 0 else None,
                durum=Haber.DURUM_AKTIF, yayin_zamani=simdi - timedelta(minutes=n))
        # Bursa ve ekonomi en az birkaç sayfa dolu olsun.
        for n in range(12 + cls.ARTIS // 2):
            for i, slug in enumerate(("bursa", "ekonomi", "bursaspor")):
                if slug not in cls.kategoriler:
                    continue
                Haber.objects.create(
                    id=965000 + n * 10 + i, slug=f"butce-{slug}-{n}",
                    baslik=f"{slug} haberi {n}", spot="Spot",
                    govde="<p>a</p><p>b</p>", kategori=cls.kategoriler[slug],
                    ilce=cls.ilce, durum=Haber.DURUM_AKTIF,
                    yayin_zamani=simdi - timedelta(minutes=200 + n))
        cls.haber = Haber.objects.get(pk=960000)
        cls.yazar = Yazar.objects.create(id=9601, slug="butce-yazari", ad="Bütçe Yazarı",
                                         unvan="Köşe yazarı", sayfasi_tarandi=False)
        # Yazar sayısı da büyüsün: "son yazı" yazar başına sorgu açarsa
        # çok kayıt turunda tavanı deler.
        for n in range(2 + cls.ARTIS // 20):
            ek = Yazar.objects.create(id=9610 + n, slug=f"butce-ek-{n}", ad=f"Ek Yazar {n}",
                                      sayfasi_tarandi=False)
            KoseYazisi.objects.create(
                id=962000 + n, slug=f"butce-ek-yazi-{n}", baslik=f"Ek yazı {n}",
                yazar=ek, govde="<p>a</p>", yayin_zamani=simdi - timedelta(hours=n))
        for n in range(3 + cls.ARTIS // 10):
            KoseYazisi.objects.create(
                id=961000 + n, slug=f"butce-yazi-{n}", baslik=f"Köşe yazısı {n}",
                yazar=cls.yazar, kategori=cls.kategoriler.get("gundem", cls.haber.kategori),
                govde="<p>a</p><p>b</p>", yayin_zamani=simdi - timedelta(hours=n))
        cls.yazi = KoseYazisi.objects.get(pk=961000)

    def setUp(self):
        okunma.sifirla()

    def tearDown(self):
        okunma.sifirla()

    def yollar(self):
        return {
            "anasayfa": "/",
            "haber_detay": self.haber.get_absolute_url(),
            "kategori_bursa": "/bursa",
            "kategori_ekonomi": "/ekonomi",
            "kategori_bursaspor": "/bursaspor",
            "ilce": "/ilce/osmangazi",
            "kose_yazisi": self.yazi.get_absolute_url(),
            "yazarlar": "/yazarlar",
            "kose_yazilari": "/kose-yazilari",
            "konular": "/konular",
        }

    def sorgu_say(self, yol):
        with CaptureQueriesContext(connection) as y:
            yanit = self.client.get(yol)
        self.assertEqual(yanit.status_code, 200, yol)
        return len(y.captured_queries), yanit


class SorguTavani(Temel):

    def test_sayfa_basina_sorgu_tavani(self):
        olcum = {}
        for ad, yol in self.yollar().items():
            with self.subTest(ad):
                n, _ = self.sorgu_say(yol)
                olcum[ad] = n
                self.assertLessEqual(n, tavan(ad), f"{ad} {yol}: {n} sorgu")
        if os.environ.get("BH_BUTCE_RAPOR") == "1":
            print(type(self).__name__, olcum)

    def test_anasayfa_html_boyutu(self):
        _, yanit = self.sorgu_say("/")
        self.assertLessEqual(len(yanit.content), ANASAYFA_HTML_TAVAN,
                             f"anasayfa {len(yanit.content)} bayt")

    def test_detay_kategori_ilce_html_boyutu(self):
        yollar = self.yollar()
        olcum = {}
        for ad, tavan_kb in HTML_TAVAN.items():
            with self.subTest(ad):
                _, yanit = self.sorgu_say(yollar[ad])
                olcum[ad] = len(yanit.content)
                self.assertLessEqual(len(yanit.content), tavan_kb * 1024,
                                     f"{ad}: {len(yanit.content)} bayt")
        if os.environ.get("BH_BUTCE_RAPOR") == "1":
            print(type(self).__name__, "html", olcum)

    def test_betik_ve_stil_dosyasi_sayisi(self):
        for ad, yol in self.yollar().items():
            with self.subTest(ad):
                _, yanit = self.sorgu_say(yol)
                html = yanit.content.decode("utf-8")
                betik = re.findall(r"<script\b[^>]*\bsrc=\"([^\"]+)\"", html)
                stil = re.findall(r"<link\b[^>]*\brel=\"stylesheet\"[^>]*>", html)
                self.assertLessEqual(len(betik), BETIK_TAVAN.get(ad, BETIK_TAVAN_VARSAYILAN),
                                     f"{ad}: {betik}")
                self.assertLessEqual(len(stil), STIL_TAVAN, f"{ad}: {stil}")
                # Okur görünümünde sunum aracı yok — bu sayımın ön koşulu.
                self.assertNotIn("reklam-test.js", html, ad)


class SorguTavaniCokKayit(SorguTavani):
    """Aynı sayfalar 4 kat veriyle: sorgu sayısı kayıt sayısıyla büyümemeli."""
    ARTIS = 120

    # Asıl kanıt: miras alınan `test_sayfa_basina_sorgu_tavani` 4 kat
    # veride de aynı tavanın altında kalıyor. Döngüye düşmüş sorgu veriyle
    # büyür ve burada tavanı deler.


@SAYFA_ACIK
class SayfaOnbellegiButcesi(Temel):
    """Anonim okur: ikinci istek önbellekten, veritabanına HİÇ inmeden."""

    ONBELLEKLI = ("anasayfa", "haber_detay", "kategori_bursa", "ilce", "konular",
                  "kose_yazilari")

    def test_ikinci_istekte_sorgu_sifir(self):
        for ad in self.ONBELLEKLI:
            yol = self.yollar()[ad]
            with self.subTest(ad):
                ilk = self.client.get(yol)
                self.assertEqual(ilk["X-Onbellek"], "kayit", ad)
                n, ikinci = self.sorgu_say(yol)
                self.assertEqual(ikinci["X-Onbellek"], "isabet", ad)
                self.assertEqual(n, 0, f"{ad}: önbellek isabetinde {n} sorgu")
                self.assertEqual(ilk.content, ikinci.content, ad)

    def test_oturumlu_istek_onbellege_girmiyor(self):
        from django.contrib.auth.models import User
        User.objects.create_user("butce", password="butce-parola-123")
        self.client.login(username="butce", password="butce-parola-123")
        for _ in range(2):
            yanit = self.client.get("/")
            self.assertNotIn("X-Onbellek", yanit)

    def test_kayit_degisince_onbellek_duser(self):
        self.client.get("/")
        self.assertEqual(self.client.get("/")["X-Onbellek"], "isabet")
        h = Haber.objects.get(pk=self.haber.pk)
        h.baslik = "Bütçe haberi değişti"
        h.save()
        yanit = self.client.get("/")
        self.assertEqual(yanit["X-Onbellek"], "kayit")

    def test_paylasim_parametresi_ayri_kayit_acmaz(self):
        self.client.get("/bursa")
        yanit = self.client.get("/bursa?utm_source=x&fbclid=y")
        self.assertEqual(yanit["X-Onbellek"], "isabet")

    def test_404_onbellege_girmiyor(self):
        for _ in range(2):
            yanit = self.client.get("/gundem/yok-boyle-bir-haber-1")
            self.assertNotIn("X-Onbellek", yanit)
