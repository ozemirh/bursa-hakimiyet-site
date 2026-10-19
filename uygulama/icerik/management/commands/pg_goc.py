"""SQLite → PostgreSQL göçü (19 Ekim 2026).

    BH_VERITABANI=postgresql://... python manage.py pg_goc \\
        --kaynak "file:C:/.../db.sqlite3?mode=ro"
    ... pg_goc --sifirla            # hedef doluysa boşaltıp yeniden kopyalar
    ... pg_goc --yalniz-dogrula     # kopyalamaz, yalnız doğrulama raporu
    ... pg_goc --adres-ornek 0      # adres denetimini atlar

Adımlar (her biri ara rapor basar):

 1. Hedef PostgreSQL mi? Kaynak SALT OKUNUR açılır (`mode=ro`); kaynağa hiçbir
    koşulda yazılmaz.
 2. `migrate` — şema hedefte Django'nun kendi migration'larıyla kurulur.
 3. Plan: her model tablosu, kolonlar, yabancı anahtarlar; kaynakla kolon
    farkı varsa DURUR (sessiz veri kaybı olmasın).
 4. Kaynakta yetim yabancı anahtar varsa DURUR: hangi satırın düşeceği bir
    kullanıcı kararıdır.
 5. Hedef boş değilse DURUR; `--sifirla` verilmişse kopyalanacak tablolar
    `TRUNCATE … CASCADE` ile boşaltılır.
 6. Tablo tablo, üst tablo önce, kimlik sırasıyla `COPY` (bkz. `icerik/pg_goc.py`).
 7. Dizi (sequence) sıfırlama — `sqlsequencereset`'in ürettiği SQL.
 8. `post_migrate` sinyali: kaynakta olmayan modellerin (ör. `HaberArama`)
    içerik türü ve izinleri eklenir.
 9. Arama metni (`arama_doldur`), sonra `VACUUM (ANALYZE)` her tabloya.
10. Doğrulama: tablo başına satır sayısı ve en büyük kimlik, `icerik_haber`
    için `sum(id)`, tüm başlıkların md5'i, 10.000 satırlık tam satır md5
    örneklemi, yetim denetimi, rastgele haber adreslerinde 200/301.

Tekrar çalıştırılabilir: hedef boşsa ya da `--sifirla` ile. `--sifirla`
yalnız HEDEFİ boşaltır; üretimde bu bir "göç tekrarı"dır ve kullanıcı kararı
ister (EKIP.md eşik 2).
"""

from __future__ import annotations

import json
import random
import sqlite3
import statistics
import time
from datetime import date, datetime, timezone as dt_tz
from unittest import mock

from django.apps import apps
from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.core.management.color import no_style
from django.core.management.sql import emit_post_migrate_signal
from django.db import connection

from icerik import pg_goc as goc

#: migrate'in kendisinin doldurduğu, kaynaktan yeniden yazılacak tablolar.
MIGRATE_DOLDURUR = {"django_content_type", "auth_permission"}
#: Kaynaktan kopyalanmayan, göç sonrası üretilen tablolar.
URETILEN = {"icerik_haberarama"}


def _kaynak_adresi(yol: str) -> str:
    if yol.startswith("file:"):
        if "mode=ro" not in yol:
            raise CommandError("Kaynak URI'si mode=ro taşımalı (salt okunur).")
        return yol
    return "file:" + yol.replace("\\", "/") + "?mode=ro"


def _copy(imlec, sql, tampon):
    """psycopg2 `copy_expert`, psycopg 3 `copy()` — ikisi de desteklenir."""
    if hasattr(imlec, "copy_expert"):
        imlec.copy_expert(sql, tampon)
    else:
        with imlec.copy(sql) as c:
            c.write(tampon.getvalue())


def _olagan(deger, tur):
    """Doğrulama md5'i için iki motordan gelen değeri aynı biçime indirir."""
    if deger is None:
        return None
    if tur in goc.MANTIKSAL:
        return bool(int(deger)) if not isinstance(deger, bool) else deger
    if tur in goc.TAMSAYI:
        return int(deger)
    if tur == "DateTimeField":
        if isinstance(deger, str):
            deger = datetime.fromisoformat(deger)
        if deger.tzinfo is not None:
            deger = deger.astimezone(dt_tz.utc).replace(tzinfo=None)
        return deger.isoformat(" ")
    if tur == "DateField":
        return deger.isoformat() if isinstance(deger, date) else str(deger)
    if tur == "JSONField":
        if isinstance(deger, str):
            deger = json.loads(deger)
        return json.dumps(deger, sort_keys=True, ensure_ascii=False)
    if isinstance(deger, (bytes, memoryview)):
        return bytes(deger).hex()
    return str(deger).replace("\x00", "")


class Command(BaseCommand):
    help = "SQLite (salt okunur) veritabanını PostgreSQL'e taşır ve doğrular."

    def add_arguments(self, a):
        a.add_argument("--kaynak", required=True,
                       help="SQLite dosyası ya da file:...?mode=ro URI'si.")
        a.add_argument("--parti", type=int, default=5000)
        a.add_argument("--sifirla", action="store_true",
                       help="Hedef doluysa kopyalanacak tabloları boşaltır.")
        a.add_argument("--yalniz-dogrula", action="store_true")
        a.add_argument("--adres-ornek", type=int, default=10000)
        a.add_argument("--ornek", type=int, default=10000,
                       help="Tam satır md5 örneklemi (icerik_haber).")
        a.add_argument("--tohum", type=int, default=20261019)

    # -- yardımcılar --------------------------------------------------------

    def y(self, metin=""):
        self.stdout.write(metin)
        self.stdout.flush()

    def handle(self, *args, **o):
        if connection.vendor != "postgresql":
            raise CommandError("Hedef PostgreSQL değil: BH_VERITABANI verilmeli.")
        self.o = o
        self.kaynak = sqlite3.connect(_kaynak_adresi(o["kaynak"]), uri=True)
        try:
            self._calis()
        finally:
            self.kaynak.close()

    def _calis(self):
        o = self.o
        self.kaynak.execute("PRAGMA query_only = ON")
        bas = time.perf_counter()

        if not o["yalniz_dogrula"]:
            self.y("1) migrate")
            t = time.perf_counter()
            call_command("migrate", interactive=False, verbosity=0)
            self.y(f"   {time.perf_counter() - t:.1f} sn")
        self.planlar = goc.plan_kur(apps.get_models(include_auto_created=True))
        self.kopyalanacak = self._plan_denetle()

        if not o["yalniz_dogrula"]:
            self._kaynak_yetim_denetle()
            self._hedefi_hazirla()
            self._kopyala()
            self._sonrasi()
            self.y(f"\nGÖÇ SÜRESİ (doğrulama hariç): {time.perf_counter() - bas:.0f} sn")

        tamam = self._dogrula()
        self.y(f"\nTOPLAM: {time.perf_counter() - bas:.0f} sn · "
               f"doğrulama {'EŞİT' if tamam else 'FARKLI'}")
        if not tamam:
            raise CommandError("Doğrulama farkı var; yukarıdaki rapora bakın.")

    # -- 3) plan ------------------------------------------------------------

    def _plan_denetle(self):
        kt = {r[0] for r in self.kaynak.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")}
        kopyalanacak, sorun = [], []
        for p in self.planlar:
            if p.tablo in URETILEN:
                continue
            if p.tablo not in kt:
                self.y(f"   UYARI kaynakta tablo yok, atlanıyor: {p.tablo}")
                continue
            kol = [r[1] for r in self.kaynak.execute(f'PRAGMA table_info("{p.tablo}")')]
            eksik, fazla = goc.sema_farki(p, kol)
            if eksik or fazla:
                sorun.append(f"{p.tablo}: hedefte fazla {eksik}, kaynakta fazla {fazla}")
            kopyalanacak.append(p)
        model_disi = sorted(kt - {p.tablo for p in self.planlar}
                            - {"django_migrations", "sqlite_sequence", "sqlite_stat1",
                               "sqlite_stat4"})
        if model_disi:
            self.y(f"   UYARI kaynakta modeli olmayan tablolar (kopyalanmaz): {model_disi}")
        if sorun:
            raise CommandError("Şema farkı:\n  " + "\n  ".join(sorun))
        self.y(f"2) plan: {len(kopyalanacak)} tablo, şema farkı yok")
        return kopyalanacak

    def _kaynak_yetim_denetle(self):
        t = time.perf_counter()
        yetim = []
        for p in self.kopyalanacak:
            for kol, ust, ust_kol in p.fkler:
                n = self.kaynak.execute(goc.yetim_sorgusu(p.tablo, kol, ust, ust_kol)).fetchone()[0]
                if n:
                    yetim.append(f"{p.tablo}.{kol} → {ust}: {n}")
        if yetim:
            raise CommandError("Kaynakta yetim yabancı anahtar var; hangi satırın "
                               "düşeceği kullanıcı kararı:\n  " + "\n  ".join(yetim))
        self.y(f"3) kaynak yetim denetimi: 0 ({time.perf_counter() - t:.1f} sn)")

    # -- 5) hedef -----------------------------------------------------------

    def _ham(self):
        """Django'nun ayarlarıyla ayrı bir ham bağlantı (işlem denetimi bizde)."""
        ham = connection.get_new_connection(connection.get_connection_params())
        ham.autocommit = False
        with ham.cursor() as c:
            c.execute("SET TIME ZONE 'UTC'")
            # Toplu yükleme: çökmede son birkaç işlem kaybolabilir; göç zaten
            # --sifirla ile baştan tekrarlanabilir.
            c.execute("SET synchronous_commit = off")
        ham.commit()
        return ham

    def _hedefi_hazirla(self):
        ham = self._ham()
        qn = connection.ops.quote_name
        with ham.cursor() as c:
            dolu = []
            for p in self.kopyalanacak:
                if p.tablo in MIGRATE_DOLDURUR:
                    continue
                c.execute(f"SELECT EXISTS (SELECT 1 FROM {qn(p.tablo)})")
                if c.fetchone()[0]:
                    dolu.append(p.tablo)
            if dolu and not self.o["sifirla"]:
                raise CommandError(f"Hedef boş değil ({', '.join(dolu[:5])}…). "
                                   "Yeniden kopyalamak için --sifirla.")
            adlar = ", ".join(qn(p.tablo) for p in self.kopyalanacak)
            adlar += ", " + ", ".join(qn(t) for t in sorted(URETILEN))
            c.execute(f"TRUNCATE {adlar} RESTART IDENTITY CASCADE")
        ham.commit()
        ham.close()
        self.y(f"4) hedef boşaltıldı ({'dolu' if dolu else 'zaten boştu'}; "
               f"{len(self.kopyalanacak) + len(URETILEN)} tablo)")

    # -- 6) kopya -----------------------------------------------------------

    def _kopyala(self):
        self.y("5) kopya (üst tablo önce, kimlik sırasıyla)")
        ham = self._ham()
        parti = self.o["parti"]
        self.sayac = goc.Sayac()
        toplam_t = time.perf_counter()
        for p in self.kopyalanacak:
            t = time.perf_counter()
            adet_k = self.kaynak.execute(f'SELECT COUNT(*) FROM "{p.tablo}"').fetchone()[0]
            sorgu = goc.kaynak_parti_sorgusu(p)
            pk_i = p.kolonlar.index(p.pk)
            son = -(2 ** 63) if p.turler[pk_i] in goc.TAMSAYI else ""
            yazilan, rapor_esigi = 0, 200_000
            with ham.cursor() as c:
                while True:
                    satirlar = self.kaynak.execute(sorgu, (son, parti)).fetchall()
                    if not satirlar:
                        break
                    _copy(c, goc.copy_sorgusu(p),
                          goc.parti_tamponu(satirlar, p.turler, self.sayac))
                    yazilan += len(satirlar)
                    son = satirlar[-1][pk_i]
                    if not p.kendine_bagli:
                        ham.commit()
                    if yazilan >= rapor_esigi:
                        hiz = yazilan / (time.perf_counter() - t)
                        self.y(f"     {p.tablo}: {yazilan:,}/{adet_k:,} · {hiz:,.0f} satır/sn")
                        rapor_esigi += 200_000
            ham.commit()
            if yazilan != adet_k:
                raise CommandError(f"{p.tablo}: kaynak {adet_k}, yazılan {yazilan}")
            if adet_k:
                self.y(f"   {p.tablo:40} {yazilan:>10,} satır {time.perf_counter() - t:7.1f} sn")
        ham.close()
        self.y(f"   kopya toplam {time.perf_counter() - toplam_t:.0f} sn · "
               f"NUL düşürülen değer {self.sayac.nul} · kesirli tamsayı {self.sayac.ondalik_tamsayi}")

    # -- 7-9) sonrası -------------------------------------------------------

    def _sonrasi(self):
        t = time.perf_counter()
        modeller = [p.model for p in self.planlar]
        with connection.cursor() as c:
            for sql in connection.ops.sequence_reset_sql(no_style(), modeller):
                c.execute(sql)
        self.y(f"6) dizi sıfırlama: {time.perf_counter() - t:.1f} sn")
        # migrate'in kurduğu içerik türleri TRUNCATE ile gitti ve kaynağın
        # kimlikleriyle yeniden yazıldı; süreç içi önbellek eski kimlikleri
        # tutuyor olabilir ve izinler var olmayan türe bağlanırdı.
        from django.contrib.contenttypes.models import ContentType
        ContentType.objects.clear_cache()
        emit_post_migrate_signal(verbosity=0, interactive=False, db=connection.alias)
        self.y("7) post_migrate: eksik içerik türü ve izinler eklendi")
        t = time.perf_counter()
        call_command("arama_doldur", hepsi=True, parti=10000, stdout=self.stdout)
        self.y(f"8) arama metni: {time.perf_counter() - t:.0f} sn")
        t = time.perf_counter()
        qn = connection.ops.quote_name
        with connection.cursor() as c:
            for p in self.planlar:
                c.execute(f"VACUUM (ANALYZE) {qn(p.tablo)}")
        self.y(f"9) VACUUM (ANALYZE): {time.perf_counter() - t:.0f} sn")

    # -- 10) doğrulama ------------------------------------------------------

    def _dogrula(self) -> bool:
        self.y("\n10) DOĞRULAMA")
        tamam = True
        ham = self._ham()
        c = ham.cursor()
        qn = connection.ops.quote_name

        # a) satır sayısı + en büyük kimlik
        self.y(f"   {'tablo':40} {'kaynak':>10} {'hedef':>10} {'en büyük k/h':>24}  sonuç")
        for p in self.kopyalanacak:
            k_adet, k_max = self.kaynak.execute(
                f'SELECT COUNT(*), MAX("{p.pk}") FROM "{p.tablo}"').fetchone()
            c.execute(f"SELECT COUNT(*), MAX({qn(p.pk)}) FROM {qn(p.tablo)}")
            h_adet, h_max = c.fetchone()
            sonuc = goc.Karsilastirma(p.tablo, k_adet, h_adet, k_max, h_max)
            esit, not_ = sonuc.esit, ""
            if not esit and p.tablo in MIGRATE_DOLDURUR:
                esit, not_ = self._post_migrate_fazlasi(p, c)
            tamam &= esit
            enb = f"{k_max}/{h_max}"
            self.y(f"   {p.tablo:40} {k_adet:>10,} {h_adet:>10,} {enb[:24]:>24}  "
                   f"{'eşit' if esit else 'FARK'}{not_}")

        # b) icerik_haber: sum(id), başlık md5, tam satır örneklemi md5
        t = time.perf_counter()
        k_top = self.kaynak.execute("SELECT SUM(id) FROM icerik_haber").fetchone()[0] or 0
        c.execute("SELECT SUM(id) FROM icerik_haber")
        h_top = int(c.fetchone()[0] or 0)
        tamam &= k_top == h_top
        self.y(f"   icerik_haber sum(id): kaynak {k_top} · hedef {h_top} · "
               f"{'eşit' if k_top == h_top else 'FARK'}")

        k_oz, h_oz = goc.Ozet(), goc.Ozet()
        for i, b in self.kaynak.execute("SELECT id, baslik FROM icerik_haber ORDER BY id"):
            k_oz.ekle(i, (b or "").replace("\x00", ""))
        with ham.cursor(name="baslik_ozet") as sc:
            sc.itersize = 20000
            sc.execute("SELECT id, baslik FROM icerik_haber ORDER BY id")
            for i, b in sc:
                h_oz.ekle(i, b)
        esit = (k_oz.hex(), k_oz.adet) == (h_oz.hex(), h_oz.adet)
        tamam &= esit
        self.y(f"   başlık md5 ({k_oz.adet:,} satır): kaynak {k_oz.hex()} · hedef "
               f"{h_oz.hex()} · {'eşit' if esit else 'FARK'} ({time.perf_counter() - t:.1f} sn)")

        plan = next(p for p in self.planlar if p.tablo == "icerik_haber")
        kimlikler = [r[0] for r in self.kaynak.execute("SELECT id FROM icerik_haber")]
        ornek = sorted(random.Random(self.o["tohum"]).sample(
            kimlikler, min(self.o["ornek"], len(kimlikler))))
        kol = ", ".join(f'"{x}"' for x in plan.kolonlar)
        k_oz, h_oz = goc.Ozet(), goc.Ozet()
        for i in range(0, len(ornek), 500):
            dilim = ornek[i:i + 500]
            yer = ",".join("?" * len(dilim))
            for s in self.kaynak.execute(
                    f'SELECT {kol} FROM icerik_haber WHERE id IN ({yer}) ORDER BY id', dilim):
                k_oz.ekle(*(_olagan(d, t_) for d, t_ in zip(s, plan.turler)))
            c.execute(f"SELECT {kol} FROM icerik_haber WHERE id = ANY(%s) ORDER BY id", (dilim,))
            for s in c.fetchall():
                h_oz.ekle(*(_olagan(d, t_) for d, t_ in zip(s, plan.turler)))
        esit = (k_oz.hex(), k_oz.adet) == (h_oz.hex(), h_oz.adet)
        tamam &= esit
        self.y(f"   tam satır md5 örneklemi ({k_oz.adet:,} haber, {len(plan.kolonlar)} kolon, "
               f"tohum {self.o['tohum']}): {'eşit' if esit else 'FARK'}")

        # c) yetim denetimi (hedef)
        t = time.perf_counter()
        yetimler, denetlenen = [], 0
        for p in self.planlar:
            for kolon, ust, ust_kol in p.fkler:
                c.execute(goc.yetim_sorgusu(p.tablo, kolon, ust, ust_kol))
                n = c.fetchone()[0]
                denetlenen += 1
                if n:
                    yetimler.append(f"{p.tablo}.{kolon}: {n}")
        tamam &= not yetimler
        self.y(f"   yetim denetimi: {denetlenen} yabancı anahtar, yetim "
               f"{len(yetimler)} {yetimler[:5]} ({time.perf_counter() - t:.1f} sn)")
        ham.rollback()
        ham.close()

        # d) adres denetimi
        if self.o["adres_ornek"]:
            tamam &= self._adres_denetle()
        return tamam

    def _post_migrate_fazlasi(self, p, c) -> tuple[bool, str]:
        """İçerik türü / izin tablosunda hedefin fazlası BEKLENEN mi?

        Kaynakta olmayan modellerin (`URETILEN`) türü ve izinleri göçten sonra
        `post_migrate` ile eklenir; bu yüzden hedef kaynaktan büyüktür. Sıkı
        kural: kaynağın her satırı hedefte AYNEN olmalı, fazlalar yalnız
        üretilen modellere ait olmalı. Başka her fark FARK'tır.
        """
        qn = connection.ops.quote_name
        kol = ", ".join(qn(x) for x in p.kolonlar)
        kaynak = set(self.kaynak.execute(f'SELECT {kol} FROM "{p.tablo}"').fetchall())
        c.execute(f"SELECT {kol} FROM {qn(p.tablo)}")
        hedef = set(c.fetchall())
        if kaynak - hedef:
            return False, f" (kaynağın {len(kaynak - hedef)} satırı hedefte yok)"
        uretilen_turler = set()
        for m in apps.get_models():
            if m._meta.db_table in URETILEN:
                uretilen_turler.add((m._meta.app_label, m._meta.model_name))
        c.execute("SELECT id, app_label, model FROM django_content_type")
        tur_kimlik = {(a, m): i for i, a, m in c.fetchall()}
        izinli = {tur_kimlik[t] for t in uretilen_turler if t in tur_kimlik}
        fazla = hedef - kaynak
        if p.tablo == "django_content_type":
            sapma = [f for f in fazla if (f[1], f[2]) not in uretilen_turler]
        else:
            ct_i = p.kolonlar.index("content_type_id")
            sapma = [f for f in fazla if f[ct_i] not in izinli]
        if sapma:
            return False, f" (beklenmeyen {len(sapma)} fazla satır)"
        adlar = ", ".join(f"{a}.{m}" for a, m in sorted(uretilen_turler))
        return True, f" (+{len(fazla)} post_migrate: {adlar})"

    def _adres_denetle(self) -> bool:
        from django.test import Client
        from django.test.utils import override_settings

        from icerik.models import Haber

        n = self.o["adres_ornek"]
        t = time.perf_counter()
        uygun = list(Haber.yayindakiler().order_by().values_list("id", flat=True))
        ornek = sorted(random.Random(self.o["tohum"] + 1).sample(uygun, min(n, len(uygun))))
        istemci = Client()
        sayim = {"200": 0, "301": 0, "hata": 0}
        hatalar, sureler = [], []
        # Okunma sayacı denetim isteklerini SAYMASIN: hedef veriye sahte
        # okuma yazmak doğrulamanın kendisini kirletirdi.
        with mock.patch("icerik.okunma.say"), override_settings(
                ALLOWED_HOSTS=[*settings.ALLOWED_HOSTS, "testserver"]):
            for i in range(0, len(ornek), 500):
                for h in (Haber.objects.filter(pk__in=ornek[i:i + 500])
                          .select_related("kategori").prefetch_related("kategori__turler")
                          .only("id", "slug", "kategori")):
                    adres = h.get_absolute_url()
                    t0 = time.perf_counter()
                    y = istemci.get(adres)
                    sureler.append((time.perf_counter() - t0) * 1000)
                    if y.status_code == 200:
                        sayim["200"] += 1
                    else:
                        sayim["hata"] += 1
                        hatalar.append(f"{adres} → {y.status_code}")
                    if h.pk % 10 == 0:
                        yanlis = adres.rsplit("/", 1)[0] + f"/yanlis-slug-{h.pk}"
                        y = istemci.get(yanlis)
                        if y.status_code == 301 and y["Location"] == adres:
                            sayim["301"] += 1
                        else:
                            sayim["hata"] += 1
                            hatalar.append(f"{yanlis} → {y.status_code} {y.get('Location')}")
                done = min(i + 500, len(ornek))
                if done % 2000 == 0 or done == len(ornek):
                    self.y(f"     adres: {done:,}/{len(ornek):,} · hata {sayim['hata']}")
        sureler.sort()
        p95 = sureler[int(len(sureler) * 0.95) - 1] if sureler else 0
        self.y(f"   adres denetimi: {len(ornek):,} haber · 200 {sayim['200']:,} · "
               f"301 (yanlış slug) {sayim['301']:,} · hata {sayim['hata']} · "
               f"detay p50 {statistics.median(sureler):.0f} ms p95 {p95:.0f} ms · "
               f"{time.perf_counter() - t:.0f} sn")
        for h in hatalar[:10]:
            self.y(f"     {h}")
        return sayim["hata"] == 0
