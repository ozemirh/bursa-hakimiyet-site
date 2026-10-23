"""SQLite → PostgreSQL göçünün çekirdeği (19 Ekim 2026).

Yönetim komutu `pg_goc` bunu çağırır; buradaki işlevler komuttan ayrı
tutuldu ki dönüşüm, sıralama ve doğrulama mantığı veritabanı kurmadan
test edilebilsin (`icerik/tests_pg_goc.py`).

**Neden `dumpdata`/`loaddata` değil.** 3,7 GB ve 1.038.477 haber:
`dumpdata` bütün tabloyu belleğe alır, JSON'a çevirir, `loaddata` her
satırı ORM nesnesine kurup tek tek `INSERT` eder — saatler ve onlarca GB
bellek. Burada kaynak `sqlite3` ile **salt okunur** açılır, tablo tablo
**kimlik sırasıyla** ve anahtar kümesiyle (`WHERE pk > ? ORDER BY pk
LIMIT n`) okunur, her parti PostgreSQL'e `COPY … FROM STDIN` ile yazılır.

**Sıra.** Yabancı anahtarlar Django'da `DEFERRABLE INITIALLY DEFERRED`
kurulur, yani denetim parti işleminin sonunda yapılır. Üst tablo önce
kopyalanırsa (topolojik sıra) her parti kendi başına tutarlıdır. Kendine
bağlı tablolar (`taksonomi_kaynak.birlesti_ile`) tek işlemde kopyalanır:
bir satır kendinden SONRA gelen kimliğe bağlı olabilir.
"""

from __future__ import annotations

import hashlib
import io
from dataclasses import dataclass, field

# COPY metin biçiminin kaçışları. NUL PostgreSQL metninde YASAK; düşürülür
# ve sayılır (rapor eder, sessiz değil).
_KACIS = str.maketrans({"\\": "\\\\", "\t": "\\t", "\n": "\\n", "\r": "\\r",
                        "\x00": ""})

TAMSAYI = frozenset({
    "AutoField", "BigAutoField", "SmallAutoField", "IntegerField",
    "BigIntegerField", "SmallIntegerField", "PositiveIntegerField",
    "PositiveBigIntegerField", "PositiveSmallIntegerField",
})
MANTIKSAL = frozenset({"BooleanField", "NullBooleanField"})
IKILI = frozenset({"BinaryField"})


def alan_turu(alan) -> str:
    """Dönüşüm için tür: yabancı anahtar hedefinin türünü taşır."""
    while alan.is_relation and (alan.many_to_one or alan.one_to_one):
        alan = alan.target_field
    return alan.get_internal_type()


@dataclass
class Sayac:
    """Dönüşümde düzeltilen değerler — rapora girer."""

    nul: int = 0
    ondalik_tamsayi: int = 0


def copy_degeri(deger, tur: str, sayac: Sayac | None = None) -> str:
    """Tek değeri COPY metin biçimine çevirir.

    SQLite tür dayatmaz: mantıksal alan 0/1, tarih metin, JSON metin olarak
    gelir. PostgreSQL ise türe sıkıdır; bu işlev o farkı kapatır.
    `None` COPY'nin NULL işaretine (ters bölü + N), 1/0 `t`/`f`'ye döner.
    """
    if deger is None:
        return "\\N"
    if tur in MANTIKSAL:
        return "t" if deger in (1, True, "1", "t", "true", "True") else "f"
    if tur in TAMSAYI:
        if isinstance(deger, float):
            if not deger.is_integer():
                raise ValueError(f"tamsayı alanında kesirli değer: {deger!r}")
            if sayac:
                sayac.ondalik_tamsayi += 1
            deger = int(deger)
        return str(int(deger))
    if tur in IKILI:
        return "\\\\x" + bytes(deger).hex()
    metin = deger if isinstance(deger, str) else str(deger)
    if "\x00" in metin and sayac is not None:
        sayac.nul += 1
    return metin.translate(_KACIS)


def copy_satiri(satir, turler, sayac: Sayac | None = None) -> str:
    return "\t".join(copy_degeri(d, t, sayac) for d, t in zip(satir, turler)) + "\n"


@dataclass
class TabloPlani:
    model: object
    tablo: str
    kolonlar: list[str]
    turler: list[str]
    pk: str
    ustler: set[str] = field(default_factory=set)
    kendine_bagli: bool = False
    fkler: list[tuple[str, str, str]] = field(default_factory=list)  # (kolon, üst tablo, üst kolon)


def plan_kur(modeller) -> list[TabloPlani]:
    """Her somut, yönetilen model (otomatik M2M ara tabloları dahil) için plan."""
    planlar = {}
    for m in modeller:
        o = m._meta
        if o.proxy or not o.managed or o.swapped:
            continue
        alanlar = o.local_concrete_fields
        p = TabloPlani(model=m, tablo=o.db_table,
                       kolonlar=[a.column for a in alanlar],
                       turler=[alan_turu(a) for a in alanlar],
                       pk=o.pk.column)
        for a in alanlar:
            if a.is_relation and a.concrete and (a.many_to_one or a.one_to_one):
                ust = a.related_model._meta.db_table
                p.fkler.append((a.column, ust, a.target_field.column))
                if ust == p.tablo:
                    p.kendine_bagli = True
                else:
                    p.ustler.add(ust)
        planlar[p.tablo] = p
    return topolojik(list(planlar.values()))


def topolojik(planlar: list[TabloPlani]) -> list[TabloPlani]:
    """Üst tablo önce. Döngü varsa açık hata: sessizce yanlış sıra olmasın."""
    adlar = {p.tablo: p for p in planlar}
    sirali, gorulen, yolda = [], set(), set()

    def ziyaret(p):
        if p.tablo in gorulen:
            return
        if p.tablo in yolda:
            raise ValueError(f"yabancı anahtar döngüsü: {p.tablo}")
        yolda.add(p.tablo)
        for ust in sorted(p.ustler):
            if ust in adlar:
                ziyaret(adlar[ust])
        yolda.discard(p.tablo)
        gorulen.add(p.tablo)
        sirali.append(p)

    for p in sorted(planlar, key=lambda x: x.tablo):
        ziyaret(p)
    return sirali


def sema_farki(plan: TabloPlani, kaynak_kolonlari: list[str]) -> tuple[list[str], list[str]]:
    """(hedefte olup kaynakta olmayan, kaynakta olup hedefte olmayan) kolonlar."""
    k = set(kaynak_kolonlari)
    h = set(plan.kolonlar)
    return sorted(h - k), sorted(k - h)


class Ozet:
    """Sıralı (kimlik, değer...) akışından md5 — iki motorda aynı biçimde."""

    def __init__(self):
        self._h = hashlib.md5()
        self.adet = 0

    #: NULL işareti; boş dizeyle aynı özete düşmesin.
    BOS = "\x00NULL\x00"

    def ekle(self, *degerler):
        self._h.update(("\x1f".join(self.BOS if d is None else str(d) for d in degerler)
                        + "\x1e").encode("utf-8"))
        self.adet += 1

    def hex(self) -> str:
        return self._h.hexdigest()


@dataclass
class Karsilastirma:
    tablo: str
    kaynak_adet: int
    hedef_adet: int
    kaynak_en_buyuk: object
    hedef_en_buyuk: object

    @property
    def esit(self) -> bool:
        return (self.kaynak_adet == self.hedef_adet
                and str(self.kaynak_en_buyuk) == str(self.hedef_en_buyuk))


def kaynak_parti_sorgusu(plan: TabloPlani, kaynak_kolonlari=None) -> str:
    """SQLite'tan anahtar kümesiyle okuma sorgusu (`?` yer tutuculu)."""
    kol = ", ".join(f'"{c}"' for c in plan.kolonlar)
    return (f'SELECT {kol} FROM "{plan.tablo}" WHERE "{plan.pk}" > ? '
            f'ORDER BY "{plan.pk}" LIMIT ?')


def copy_sorgusu(plan: TabloPlani) -> str:
    kol = ", ".join(f'"{c}"' for c in plan.kolonlar)
    return f'COPY "{plan.tablo}" ({kol}) FROM STDIN'


def parti_tamponu(satirlar, turler, sayac: Sayac | None = None) -> io.StringIO:
    tampon = io.StringIO()
    tampon.writelines(copy_satiri(s, turler, sayac) for s in satirlar)
    tampon.seek(0)
    return tampon


def yetim_sorgusu(cocuk: str, kolon: str, ust: str, ust_kolon: str) -> str:
    """Yetim satır sayımı — iki motorda da geçerli SQL."""
    return (f'SELECT COUNT(*) FROM "{cocuk}" c WHERE c."{kolon}" IS NOT NULL '
            f'AND NOT EXISTS (SELECT 1 FROM "{ust}" p WHERE p."{ust_kolon}" = c."{kolon}")')
