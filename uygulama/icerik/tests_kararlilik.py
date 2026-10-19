"""Kararlılık kilitleri — sıraya ve saate bağlı sonuçlar (Paket K, 19 Ekim 2026).

## Kararsız testin kök nedeni

`tests_basarim.SiteHaritasi.test_aylik_dosya_onbellekte_ve_kayitla_tazeleniyor`
ana dalda dört tam koşunun birinde düştü, tek başına hep geçti. Neden:
aylık site haritası dosyasının önbellek anahtarı ayın SÜRÜMÜNÜ taşıyor ve
sürüm `f"{time.time():.6f}"` idi. Windows'ta Python 3.12'nin `time.time()`
çözünürlüğü **15,625 ms** (`time.get_clock_info("time")` →
`GetSystemTimeAsFileTime`, ölçüldü). Test iki haberi aynı aya kaydediyor;
ikisi arasında yalnız iki önbellekli istek var. İkinci kayıt aynı saat
dilimine düşerse sürüm DEĞİŞMİYOR, eski dosya (1 adres) servis ediliyor ve
test "2 bekleniyordu" diye düşüyor. Tam koşuda süreç ısınmış, istekler daha
hızlı — dilime düşme ihtimali artıyor; tek başına koşuda soğuk ilk istek
dilimi aşıyor.

Aynı kusur sayfa mikro önbelleğinin yayın sürümünde de vardı
(`onbellek.surumu_artir`): aynı 15,6 ms içinde iki kayıt (panelde toplu
işlem + tek kayıt) ikincisini 30 sn görünmez kılabilirdi. Düzeltme ikisinde
de aynı: sürüm `onbellek.yeni_surum()` — zaman damgası + süreç + sayaç, her
çağrıda farklı.

Buradaki testler saati SABİTLER: kusur saatin şansına bırakılmadan, her
koşuda görünür.
"""

from __future__ import annotations

from datetime import datetime
from datetime import timezone as dt_timezone
from unittest import mock

from django.core.cache import caches
from django.core.management import call_command
from django.test import SimpleTestCase, TestCase, override_settings

from taksonomi.models import Kategori, KategoriTur

from . import onbellek
from .models import Haber

LOCMEM = "django.core.cache.backends.locmem.LocMemCache"
SAYFA_ACIK = override_settings(
    CACHES={"default": {"BACKEND": LOCMEM, "LOCATION": "bh-k-veri"},
            "sayfa": {"BACKEND": LOCMEM, "LOCATION": "bh-k-sayfa"}},
    SAYFA_ONBELLEK_SANIYE=30)

SABIT_AN = 1_790_000_000.0


class SurumBenzersiz(SimpleTestCase):

    def test_ayni_saat_diliminde_iki_surum_farkli(self):
        with mock.patch("time.time", return_value=SABIT_AN):
            self.assertNotEqual(onbellek.yeni_surum(), onbellek.yeni_surum())

    @SAYFA_ACIK
    def test_yayin_surumu_ayni_dilimde_de_degisiyor(self):
        with mock.patch("time.time", return_value=SABIT_AN):
            ilk = onbellek.surumu_artir()
            ikinci = onbellek.surumu_artir()
        self.assertNotEqual(ilk, ikinci)


class SiteHaritasiSaatSabit(TestCase):
    """Kararsız testin kendisi, saat dondurulmuş hâlde: eski kodda HER koşuda
    düşer (ölçüldü: düzeltmeden önce 1 adres döndü)."""

    @classmethod
    def setUpTestData(cls):
        call_command("taksonomi_kur", verbosity=0)
        cls.kategori = KategoriTur.objects.filter(
            tur=Kategori.TUR_HABER, slug="bursaspor").first().kategori

    def _haber(self, n, gun):
        return Haber.objects.create(
            id=970000 + n, slug=f"kararlilik-{n}", baslik=f"Kararlılık {n}",
            spot="spot", govde="<p>a</p><p>b</p>", kategori=self.kategori,
            yayin_zamani=datetime(2025, 1, gun, 9, tzinfo=dt_timezone.utc))

    def _dosya(self):
        yanit = self.client.get("/static/sitemap/news_2025-01.xml")
        return b"".join(yanit.streaming_content).decode()

    @SAYFA_ACIK
    def test_ayni_dilimde_ikinci_kayit_dosyayi_tazeliyor(self):
        # `hesapla()`nın tazelik denetimi de aynı saati görür; önbellekteki
        # dosya "taze" kalır. Tazelenmenin TEK yolu sürümün değişmesi.
        with mock.patch("time.time", return_value=SABIT_AN):
            self._haber(1, 10)
            self.assertEqual(self._dosya().count("<url>"), 1)
            self._haber(2, 11)
            self.assertEqual(self._dosya().count("<url>"), 2)


class LocMemDeposuSizmiyor(SimpleTestCase):
    """`override_settings(CACHES=...)` ile açılan LocMem deposu test bitince
    `caches`ten düşer ama deposu modül düzeyinde kalır. Koşucu bütün
    depoları temizler; iki test aynı adı kullansa da birbirini görmez.
    Sıra: `test_1_yaz` önce koşar (unittest ada göre sıralar); `--shuffle`
    ile ters sırada da geçmeli — okuyan test değeri hiç görmemeli."""

    @SAYFA_ACIK
    def test_1_yaz(self):
        caches["sayfa"].set("bh-k-sizinti", "onceki-test", None)
        self.assertEqual(caches["sayfa"].get("bh-k-sizinti"), "onceki-test")

    @SAYFA_ACIK
    def test_2_okuma(self):
        self.assertIsNone(caches["sayfa"].get("bh-k-sizinti"))


class CanliBellekSizmiyor(SimpleTestCase):
    """`icerik.canli` dosyaları 30 sn süreç belleğinde tutar. Bir testin
    kurduğu geçici veri sonraki teste sızmamalı."""

    def test_1_bellege_yaz(self):
        from . import canli
        canli._bellek["bh-k-sizinti"] = (9e18, {"sahte": True})

    def test_2_bellek_bos(self):
        from . import canli
        self.assertNotIn("bh-k-sizinti", canli._bellek)
