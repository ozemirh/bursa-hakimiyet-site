"""Arama — motora özgü katman (19 Ekim 2026).

Normalizasyon `arama_metni.py`dedir ve motor tanımaz; bu modül o çekirdeğin
çıktısını iki motordan birine çevirir:

- **PostgreSQL** (asıl yol): `icerik_haberarama.vektor @@ 'kelime':* & …`
  — üretilmiş `tsvector` sütunu + GIN indeksi (`0016_arama_metni`).
  Panel: `baslik LIKE '%kelime%'` + `pg_trgm` GIN indeksi.
- **SQLite** (yedek yol): aynı normalize sütunda `LIKE '% kelime%'`.
  İndeks yok, tam tarama; doğru ama yavaş. Bu yüzden **zaman sınırı**
  altında çalışır: sonuçsuz bir sorgu işçiyi saniyelerce kilitlemesin
  (DEGERLENDIRME-2026-10 §3 bulgu 9: 2,8–31 sn).

İki yolun anlamı aynıdır: her terim AND'lenir, önekli terim kelime BAŞINA
oturur (`isik` → "ışıklar" evet, "değişikliği" hayır — §21'deki %83
rastlantının sebebi alt dizi eşlemesiydi), öneksiz kısa terim tam kelimedir.

Zaman sınırı PostgreSQL'de de var (`statement_timeout`); orada beklenen süre
milisaniyelerdir ve sınır yalnız emniyet kemeridir.
"""

from __future__ import annotations

import time
from contextlib import contextmanager
from functools import reduce
from operator import and_

from django.conf import settings
from django.core.paginator import Paginator
from django.db import connection, transaction
from django.utils.functional import cached_property
from django.db.models import Q
from django.db.models.expressions import RawSQL

from .arama_metni import Cozum, kayit_metni

#: Okur araması için süre sınırı (ms). SQLite'ta progress handler, PG'de
#: statement_timeout. Ayarlardan `ARAMA_SURE_SINIRI_MS` ile değiştirilebilir.
VARSAYILAN_SURE_MS = 1500


def sure_siniri_ms() -> int:
    return int(getattr(settings, "ARAMA_SURE_SINIRI_MS", VARSAYILAN_SURE_MS))


# -- kayıt tarafı -----------------------------------------------------------

def satir_kur(haber_id: int, baslik: str | None, spot: str | None):
    """`HaberArama` nesnesi (kaydetmez)."""
    from .models import HaberArama
    return HaberArama(haber_id=haber_id, baslik=kayit_metni(baslik),
                      metin=kayit_metni(baslik, spot))


def yaz(satirlar) -> int:
    """Satırları tek sorguda ekler ya da tazeler (INSERT … ON CONFLICT)."""
    from .models import HaberArama
    satirlar = list(satirlar)
    if satirlar:
        HaberArama.objects.bulk_create(
            satirlar, update_conflicts=True, unique_fields=["haber"],
            update_fields=["baslik", "metin"])
    return len(satirlar)


def tazele(kimlikler, parti: int = 5000) -> int:
    """Verilen haberlerin arama satırını veritabanındaki başlık/spottan
    yeniden yazar; olmayan kimlik sessizce atlanır. Kancayı atlayan toplu
    yazımlardan (`bulk_create`, `bulk_update`, `update()`) sonra çağrılır
    — `goc_al`, `metin_temizle`, `arama_doldur --kimlikler` (Paket L2)."""
    from .models import Haber
    kimlikler = sorted(set(kimlikler))
    toplam = 0
    for bas in range(0, len(kimlikler), parti):
        satirlar = (Haber.objects.filter(pk__in=kimlikler[bas:bas + parti])
                    .values_list("id", "baslik", "spot"))
        toplam += yaz(satir_kur(i, b, s) for i, b, s in satirlar)
    return toplam


ILGILI_ALANLAR = frozenset({"baslik", "spot"})


def haber_kaydedildi(sender, instance, created, raw=False, update_fields=None, **kw):
    """`post_save` kancası (`icerik/apps.py`).

    `save(update_fields=[...])` başlık ya da spot içermiyorsa yazmaz: durum
    değiştirmek, okunma ya da manşet bayrağı aramayı etkilemez.
    `raw` (loaddata) atlanır — Django'nun kanca sözleşmesi.
    """
    if raw:
        return
    if update_fields is not None and not (ILGILI_ALANLAR & set(update_fields)):
        return
    yaz([satir_kur(instance.pk, instance.baslik, instance.spot)])


# -- sorgu tarafı -----------------------------------------------------------

def tsquery(cozum: Cozum) -> str:
    """`tsquery` metni: `'isik':* & 'a'`.

    Ayrıştırıcıdan geçmeyen `::tsquery` dönüşümüyle kullanılır; kelimeler
    yalnız `\\w` karakterleri taşıdığı için tırnak kaçışı gerekmez, yine de
    tek tırnak ve ters bölü savunma amaçlı ayıklanır.
    """
    parcalar = []
    for t in cozum.terimler:
        kelime = t.kelime.replace("'", "").replace("\\", "")
        if kelime:
            parcalar.append(f"'{kelime}'" + (":*" if t.onek else ""))
    return " & ".join(parcalar)


def _alt_dizi(t) -> str:
    """SQLite yolu: kayıt biçimi `" k1 k2 "` olduğu için kelime başı `" k"`,
    tam kelime `" k "` alt dizisidir (`arama_metni.kayit_metni`)."""
    return f" {t.kelime}" + ("" if t.onek else " ")


def haberleri_suz(sorgu, cozum: Cozum):
    """Okur araması: `sorgu` bir `Haber` QuerySet'i, sonuç süzülmüş hâli."""
    if not cozum:
        return sorgu.none()
    if connection.vendor == "postgresql":
        return sorgu.filter(pk__in=RawSQL(
            "SELECT haber_id FROM icerik_haberarama WHERE vektor @@ %s::tsquery",
            [tsquery(cozum)]))
    return sorgu.filter(reduce(and_, [Q(arama__metin__contains=_alt_dizi(t))
                                      for t in cozum.terimler]))


def panel_suz(sorgu, cozum: Cozum):
    """Panelin haber seçicisi: başlıkta ALT DİZİ (yazarken tamamlama).

    Editör "bozbe" yazıp "Bozbey"i bulmak ister; kelime sınırı burada aranmaz.
    PG'de `pg_trgm` GIN indeksi kullanılır; SQLite'ta tam tarama.
    """
    if not cozum:
        return sorgu.none()
    return sorgu.filter(reduce(and_, [Q(arama__baslik__contains=t.kelime)
                                      for t in cozum.terimler]))


# -- sayfalama --------------------------------------------------------------

class AramaSayfalayici(Paginator):
    """İki aşamalı sayfalama: önce kimlikler, sonra sayfa.

    **Ölçülen sorun (19 Ekim 2026, PG, 1.038.477 haber).** `ORDER BY
    yayin_zamani DESC LIMIT 20` ile `vektor @@ …` birlikte yazılınca
    planlayıcı bilinmeyen terim için ~2.216 eşleşme TAHMİN ediyor (taban
    seçicilik) ve "20 satırı çabuk bulurum" diye sıralama indeksini baştan
    yürüyor. Eşleşme yoksa 1 milyon satırın hepsini yoklayıp bitiriyor:
    `qxzvbn` **8.483 ms**. Aynı süzgeç sıralamasız sayımda GIN bitmap'ini
    doğru seçiyor (0 satır, ~1 ms).

    **Çözüm planı zorlamak değil, soruyu bölmek:**

    1. Sayım zaten sıralamasız ve `UST_SINIR + 1` ile sınırlı; kimlikleri
       de getirir (aynı sorgu, ek maliyet yok).
    2. Sonuç sınırın altındaysa bütün eşleşmeler elde demektir: sayfa
       `pk IN (≤ 1.000 kimlik)` ile kurulur — birincil anahtar yoklaması +
       küçük sıralama, tahmine bağlı değil.
    3. Sınırı aşan (yaygın, yoğunluğu ≥ %0,1) terimde sıralama indeksini
       yürümek doğru plandır; sorgu olduğu gibi gider.

    Motor bağımsızdır: SQLite yolunda da aynı iki adım geçerli.
    """

    UST_SINIR = 1000

    def __init__(self, taban, cozum: Cozum, boy: int):
        self.taban = taban
        super().__init__(haberleri_suz(taban, cozum), boy)

    @cached_property
    def kimlikler(self) -> list[int]:
        return list(self.object_list.order_by()
                    .values_list("pk", flat=True)[:self.UST_SINIR + 1])

    @property
    def _ham_sayim(self) -> int:
        return len(self.kimlikler)

    @property
    def count(self) -> int:
        return min(self._ham_sayim, self.UST_SINIR)

    @property
    def kesildi_mi(self) -> bool:
        return self._ham_sayim > self.UST_SINIR

    def page(self, number):
        if not self.kesildi_mi:
            self.object_list = self.taban.filter(pk__in=self.kimlikler)
        return super().page(number)


# -- zaman sınırı -----------------------------------------------------------

class ZamanAsimi(Exception):
    """Arama sorgusu süre sınırını aştı."""


def _zaman_asimi_mi(hata: BaseException) -> bool:
    neden = hata.__cause__ or hata
    if connection.vendor == "sqlite":
        return "interrupted" in str(neden).lower()
    return getattr(neden, "pgcode", None) == "57014" or \
        getattr(getattr(neden, "diag", None), "sqlstate", None) == "57014"


@contextmanager
def sure_siniri(ms: int | None = None):
    """Bloktaki sorguları `ms` milisaniyeyle sınırlar; aşılırsa `ZamanAsimi`.

    SQLite: `set_progress_handler` her N sanal makine adımında saati yoklar
    ve süre dolunca sorguyu keser ("interrupted"). PostgreSQL: blok bir
    işlem içine alınır ve `SET LOCAL statement_timeout` uygulanır; işlem
    bitince ayar kendiliğinden düşer, bağlantıya sızmaz.

    Sorgular tembel değerlendirildiği için blok içinde **listeye çevrilmeli**
    — şablonda değerlendirilen sorgu bu sınırın dışında kalır.
    """
    from django.db.utils import OperationalError

    ms = sure_siniri_ms() if ms is None else ms
    if connection.vendor == "sqlite":
        connection.ensure_connection()
        ham = connection.connection
        bitis = time.monotonic() + ms / 1000
        ham.set_progress_handler(lambda: 1 if time.monotonic() > bitis else 0, 20000)
        try:
            yield
        except OperationalError as hata:
            if _zaman_asimi_mi(hata):
                raise ZamanAsimi(str(hata)) from hata
            raise
        finally:
            ham.set_progress_handler(None, 0)
        return
    if connection.vendor == "postgresql":
        try:
            with transaction.atomic():
                with connection.cursor() as imlec:
                    imlec.execute(f"SET LOCAL statement_timeout = {int(ms)}")
                yield
                # İç içe atomic'te (testler, ATOMIC_REQUESTS) blok bir
                # savepoint'tir ve SET LOCAL dış işlem bitene kadar yaşar;
                # sınır blok dışındaki sorgulara sızmasın.
                with connection.cursor() as imlec:
                    imlec.execute("SET LOCAL statement_timeout TO DEFAULT")
        except OperationalError as hata:
            if _zaman_asimi_mi(hata):
                raise ZamanAsimi(str(hata)) from hata
            raise
        return
    yield
