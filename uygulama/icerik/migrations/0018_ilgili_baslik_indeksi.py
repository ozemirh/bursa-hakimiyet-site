"""İlgili haberlerin aday indeksi — 19 Ekim 2026, Paket L2.

YALNIZ PostgreSQL; SQLite'ta işlem yok (orada ilgili haber normalize
başlıkta `LIKE` ile ve `yayin_zamani` penceresinden çalışır).

`icerik_haberarama.baslik` (normalize BAŞLIK, spotsuz) üzerinde ifade
GIN indeksi. İfade `0016_arama_metni`deki `vektor` sütununun ifadesiyle
aynı, yalnız `metin` yerine `baslik`: kelime bölme Python'da tek yerde
(`arama_metni.kayit_metni`), veritabanı yeniden bölmez. Üç işlev de
IMMUTABLE (0016 notu). Sorgu ifadeyi BİREBİR taşır
(`icerik/ilgili.py` → `BASLIK_VEKTOR`).

Neden okur aramasının `vektor`ü yetmiyor: o başlık + spot taşır; ilgili
haber başlıkça puanlanıyor ve yalnız spotta geçen ad aday sınırını
dolduruyordu (ölçüldü: aday sayısı 2–14 kat).

ÖLÇÜM (yerel PG 18, 1.038.477 haber): kurulum 6,9 sn, boyut 44 MB.
`CONCURRENTLY`: tablo yazmaya kapanmaz; bu yüzden migration işlem dışı
(`atomic = False`). Sonra `ANALYZE icerik_haberarama` — ZORUNLU: ilgili
haberin "ağır çapa" kararı (`ilgili.siklik`) bu indeksin ifade
istatistiğini (`pg_stats.most_common_elems`) okur.

Geri alma: indeks düşer (`DROP INDEX CONCURRENTLY IF EXISTS`).
"""

from django.db import migrations

INDEKS = "haberarama_baslik_vektor_gin"
KUR = (
    f"CREATE INDEX CONCURRENTLY IF NOT EXISTS {INDEKS} ON icerik_haberarama "
    "USING gin ((array_to_tsvector(array_remove(string_to_array(baslik, ' '), ''))))"
)


def kur(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    schema_editor.execute(KUR)
    schema_editor.execute("ANALYZE icerik_haberarama")


def kaldir(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    schema_editor.execute(f"DROP INDEX CONCURRENTLY IF EXISTS {INDEKS}")


class Migration(migrations.Migration):

    atomic = False

    dependencies = [
        ("icerik", "0017_merge_0016_arama_metni_0016_guvenlik_logkaydi"),
    ]

    operations = [
        migrations.RunPython(kur, kaldir, elidable=False),
    ]
