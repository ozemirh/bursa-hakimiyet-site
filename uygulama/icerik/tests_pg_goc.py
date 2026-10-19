# -*- coding: utf-8 -*-
"""`pg_goc` — SQLite → PostgreSQL göçünün testleri (19 Ekim 2026).

Saf mantık (dönüşüm, sıra, özet, şema farkı) iki motorda koşar. Uçtan uca
gidiş-dönüş yalnız PostgreSQL'de: test veritabanının içeriği Django'nun
kendi SQLite şemasıyla geçici bir dosyaya yazılır, sonra `pg_goc` o
dosyadan geri taşır ve kendi doğrulamasını geçmek zorundadır.
"""

import io
from contextlib import closing
import sqlite3
import tempfile
from datetime import date, datetime, timezone as dt_tz
from decimal import Decimal
from pathlib import Path
from unittest import skipIf, skipUnless

from django.apps import apps
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import connection
from django.test import SimpleTestCase, TestCase, TransactionTestCase
from django.utils import timezone

from . import pg_goc as goc
from .management.commands.pg_goc import _kaynak_adresi, _olagan

PG = connection.vendor == "postgresql"


def _copy_coz(alan: str):
    """COPY metin biçiminin tersi — yalnız testte, gidiş-dönüşü sınamak için."""
    if alan == "\\N":
        return None
    cikti, i = [], 0
    while i < len(alan):
        c = alan[i]
        if c == "\\":
            sonraki = alan[i + 1]
            cikti.append({"\\": "\\", "t": "\t", "n": "\n", "r": "\r"}[sonraki])
            i += 2
        else:
            cikti.append(c)
            i += 1
    return "".join(cikti)


class CopyDonusumu(SimpleTestCase):

    def test_null_ve_mantiksal(self):
        self.assertEqual(goc.copy_degeri(None, "TextField"), "\\N")
        self.assertEqual(goc.copy_degeri(1, "BooleanField"), "t")
        self.assertEqual(goc.copy_degeri(0, "BooleanField"), "f")

    def test_tamsayi(self):
        sayac = goc.Sayac()
        self.assertEqual(goc.copy_degeri(5.0, "BigIntegerField", sayac), "5")
        self.assertEqual(sayac.ondalik_tamsayi, 1)
        with self.assertRaises(ValueError):
            goc.copy_degeri(5.5, "IntegerField")

    def test_kacis_gidis_donus(self):
        ham = "satır\nsonu\tsekme\\ters\rCR İ ı ş"
        self.assertEqual(_copy_coz(goc.copy_degeri(ham, "TextField")), ham)
        self.assertNotIn("\n", goc.copy_degeri(ham, "TextField"))

    def test_nul_dusurulur_ve_sayilir(self):
        sayac = goc.Sayac()
        self.assertEqual(goc.copy_degeri("a\x00b", "TextField", sayac), "ab")
        self.assertEqual(sayac.nul, 1)

    def test_ikili(self):
        self.assertEqual(goc.copy_degeri(b"\x01\xff", "BinaryField"), "\\\\x01ff")

    def test_satir(self):
        tampon = goc.parti_tamponu([(1, "a\tb", None, 1)],
                                   ["BigIntegerField", "TextField", "TextField", "BooleanField"])
        self.assertEqual(tampon.getvalue(), "1\ta\\tb\t\\N\tt\n")


class Plan(SimpleTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.planlar = goc.plan_kur(apps.get_models(include_auto_created=True))
        cls.sira = [p.tablo for p in cls.planlar]

    def test_ust_tablo_once(self):
        for p in self.planlar:
            for ust in p.ustler:
                with self.subTest(tablo=p.tablo, ust=ust):
                    self.assertLess(self.sira.index(ust), self.sira.index(p.tablo))

    def test_ara_tablolar_ve_arama_tablosu_planda(self):
        for t in ("icerik_haber_kaynaklar", "icerik_haber_ilgili_haberler",
                  "icerik_kampanyayuva", "icerik_haberarama"):
            self.assertIn(t, self.sira)
        self.assertLess(self.sira.index("icerik_haber"), self.sira.index("icerik_haberarama"))

    def test_kendine_bagli_tablolar_isaretli(self):
        kendine = {p.tablo for p in self.planlar if p.kendine_bagli}
        self.assertIn("taksonomi_kaynak", kendine)   # birlesti_ile

    def test_haber_kolon_turleri(self):
        p = next(p for p in self.planlar if p.tablo == "icerik_haber")
        tur = dict(zip(p.kolonlar, p.turler))
        self.assertEqual(tur["id"], "BigIntegerField")
        self.assertEqual(tur["kategori_id"], "BigAutoField")   # FK hedefin türünü taşır
        self.assertEqual(tur["manset_ana"], "BooleanField")

    def test_dongu_acik_hata(self):
        a = goc.TabloPlani(None, "a", [], [], "id", ustler={"b"})
        b = goc.TabloPlani(None, "b", [], [], "id", ustler={"a"})
        with self.assertRaises(ValueError):
            goc.topolojik([a, b])

    def test_sema_farki(self):
        p = goc.TabloPlani(None, "t", ["id", "ad", "yeni"], [], "id")
        self.assertEqual(goc.sema_farki(p, ["id", "ad", "eski"]), (["yeni"], ["eski"]))


class OzetVeOlagan(SimpleTestCase):

    def test_ozet_null_bos_dizeden_farkli(self):
        a, b = goc.Ozet(), goc.Ozet()
        a.ekle(1, None)
        b.ekle(1, "")
        self.assertNotEqual(a.hex(), b.hex())

    def test_ozet_kararli(self):
        a, b = goc.Ozet(), goc.Ozet()
        for o in (a, b):
            o.ekle(1, "Işık")
            o.ekle(2, "İnegöl")
        self.assertEqual(a.hex(), b.hex())
        self.assertEqual(a.adet, 2)

    def test_iki_motorun_degeri_ayni_bicime_iner(self):
        # SQLite metin + 0/1; PostgreSQL datetime(tz) + bool.
        from zoneinfo import ZoneInfo
        self.assertEqual(_olagan("2026-08-25 10:00:00", "DateTimeField"),
                         _olagan(datetime(2026, 8, 25, 13, 0, tzinfo=ZoneInfo("Europe/Istanbul")),
                                 "DateTimeField"))
        self.assertEqual(_olagan("2026-08-25 10:00:00", "DateTimeField"),
                         _olagan(datetime(2026, 8, 25, 10, 0, tzinfo=dt_tz.utc),
                                 "DateTimeField"))
        self.assertEqual(_olagan(1, "BooleanField"), _olagan(True, "BooleanField"))
        self.assertEqual(_olagan('{"b": 1, "a": [2]}', "JSONField"),
                         _olagan({"a": [2], "b": 1}, "JSONField"))
        self.assertEqual(_olagan("2026-08-25", "DateField"),
                         _olagan(date(2026, 8, 25), "DateField"))
        self.assertEqual(_olagan("a\x00b", "TextField"), "ab")

    def test_kaynak_salt_okunur(self):
        self.assertEqual(_kaynak_adresi("C:\\veri\\db.sqlite3"),
                         "file:C:/veri/db.sqlite3?mode=ro")
        with self.assertRaises(CommandError):
            _kaynak_adresi("file:C:/veri/db.sqlite3")


@skipIf(PG, "hedef PostgreSQL iken anlamsız")
class HedefPostgresDegilse(TestCase):

    def test_reddeder(self):
        with self.assertRaisesMessage(CommandError, "PostgreSQL değil"):
            call_command("pg_goc", kaynak="file:x.sqlite3?mode=ro", stdout=io.StringIO())


def _sqlite_disa_aktar(yol: Path):
    """PG test veritabanının içeriğini Django'nun SQLite şemasıyla dosyaya yazar.

    Şema Django'nun kendi SQLite şema düzenleyicisiyle kurulur — gerçek
    kaynakla aynı DDL. Değerler SQLite'ın sakladığı biçime çevrilir
    (zaman UTC metin, mantıksal 0/1, JSON metin).
    """
    from django.db.backends.sqlite3.base import DatabaseWrapper
    ayar = {"ENGINE": "django.db.backends.sqlite3", "NAME": str(yol), "OPTIONS": {},
            "TIME_ZONE": None, "CONN_MAX_AGE": 0, "CONN_HEALTH_CHECKS": False,
            "AUTOCOMMIT": True, "ATOMIC_REQUESTS": False, "USER": "", "PASSWORD": "",
            "HOST": "", "PORT": "", "TEST": {}}
    from django.db import connections
    hedef = DatabaseWrapper(ayar, alias="goc_test_kaynak")
    # Şema düzenleyicinin işlemi bağlantıyı adıyla arıyor; geçici kayıt.
    connections["goc_test_kaynak"] = hedef
    try:
        with hedef.schema_editor() as se:
            for model in apps.get_models():
                if model._meta.managed and not model._meta.proxy:
                    se.create_model(model)
    finally:
        del connections["goc_test_kaynak"]

    def cevir(d):
        if isinstance(d, datetime):
            return d.astimezone(dt_tz.utc).replace(tzinfo=None).isoformat(" ")
        if isinstance(d, date):
            return d.isoformat()
        if isinstance(d, bool):
            return int(d)
        if isinstance(d, Decimal):
            return str(d)
        if isinstance(d, memoryview):
            return bytes(d)
        return d

    qn = connection.ops.quote_name
    with connection.cursor() as c, hedef.cursor() as h:
        for p in goc.plan_kur(apps.get_models(include_auto_created=True)):
            if p.tablo in ("icerik_haberarama",):
                continue
            kol = ", ".join(qn(x) for x in p.kolonlar)
            c.execute(f"SELECT {kol} FROM {qn(p.tablo)}")
            satirlar = [tuple(cevir(d) for d in s) for s in c.fetchall()]
            if satirlar:
                yer = ", ".join("?" * len(p.kolonlar))
                h.executemany(f'INSERT INTO "{p.tablo}" ({kol}) VALUES ({yer})', satirlar)
    hedef.close()


@skipUnless(PG, "uçtan uca göç hedefi PostgreSQL")
class UctanUcaGoc(TransactionTestCase):
    """Gidiş-dönüş: PG → SQLite dosyası → `pg_goc` → PG, doğrulama EŞİT olmalı."""

    ZOR_GOVDE = "<p>satır\nsonu</p>\t<p>ters \\ bölü</p>\r İ ı ş ğ ü ö ç"

    def setUp(self):
        from taksonomi.models import Kategori, KategoriTur

        from .models import Haber, HaberArama
        call_command("taksonomi_kur", verbosity=0)
        kategori = KategoriTur.objects.get(tur=Kategori.TUR_HABER, slug="gundem").kategori
        simdi = timezone.now()
        for i in range(1, 31):
            Haber.objects.create(
                id=1000 + i, slug=f"goc-{i}", baslik=f"Göç sınaması {i} IŞIK",
                spot="Spot", govde=self.ZOR_GOVDE if i == 1 else "<p>Gövde</p>",
                kategori=kategori, durum=Haber.DURUM_AKTIF, yayin_zamani=simdi,
                manset_ana=(i == 2))
        self.haber_sayisi = Haber.objects.count()
        self.assertEqual(HaberArama.objects.count(), self.haber_sayisi)
        self.dizin = tempfile.TemporaryDirectory()
        self.kaynak = Path(self.dizin.name) / "kaynak.sqlite3"
        _sqlite_disa_aktar(self.kaynak)
        # Kaynakta NUL karakteri: PG metni bunu taşıyamaz; göç düşürüp saymalı.
        with closing(sqlite3.connect(self.kaynak)) as k, k:
            k.execute("UPDATE icerik_haber SET spot = 'Sp' || char(0) || 'ot' WHERE id = 1003")
        self.uri = f"file:{self.kaynak.as_posix()}?mode=ro"

    def tearDown(self):
        self.dizin.cleanup()

    def _goc(self, **ek):
        cikti = io.StringIO()
        call_command("pg_goc", kaynak=self.uri, adres_ornek=20, ornek=10,
                     stdout=cikti, **ek)
        return cikti.getvalue()

    def test_gidis_donus_esit(self):
        from .models import Haber, HaberArama
        cikti = self._goc(sifirla=True)
        self.assertIn("doğrulama EŞİT", cikti)
        self.assertIn("NUL düşürülen değer 1", cikti)
        self.assertIn("yetim 0", cikti)
        self.assertEqual(Haber.objects.count(), self.haber_sayisi)
        self.assertEqual(Haber.objects.get(pk=1001).govde, self.ZOR_GOVDE)
        self.assertEqual(Haber.objects.get(pk=1003).spot, "Spot")
        self.assertTrue(Haber.objects.get(pk=1002).manset_ana)
        self.assertEqual(HaberArama.objects.count(), self.haber_sayisi)
        # Göçten sonra yeni kayıt: dizi sıfırlanmasaydı kimlik 1'den başlar
        # ve taşınan 17 ilçeden biriyle çakışırdı.
        from taksonomi.models import Ilce
        yeni = Ilce.objects.create(ad="Deneme İlçesi", slug="deneme-ilcesi")
        self.assertGreater(yeni.pk, max(Ilce.objects.exclude(pk=yeni.pk)
                                        .values_list("pk", flat=True)))

    def test_dolu_hedef_sifirlamasiz_reddedilir(self):
        with self.assertRaisesMessage(CommandError, "--sifirla"):
            self._goc()

    def test_kaynakta_yetim_varsa_durur(self):
        with closing(sqlite3.connect(self.kaynak)) as k, k:
            k.execute("INSERT INTO icerik_haber_etiketler (haber_id, etiket_id) "
                      "VALUES (1001, 999999)")
        with self.assertRaisesMessage(CommandError, "yetim"):
            self._goc(sifirla=True)

    def test_yalniz_dogrula_farki_yakalar(self):
        self._goc(sifirla=True)
        from .models import Haber
        Haber.objects.filter(pk=1005).update(baslik="Değişmiş başlık")
        with self.assertRaisesMessage(CommandError, "Doğrulama farkı"):
            self._goc(yalniz_dogrula=True)
