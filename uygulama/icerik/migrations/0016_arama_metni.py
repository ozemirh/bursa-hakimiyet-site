"""F7 arama indeksi — 19 Ekim 2026.

Yeni tablo `icerik_haberarama`; `icerik_haber`e DOKUNMAZ (SQLite'ta tablo
yeniden kurulmaz, `sqlmigrate` ile doğrulandı: `new__icerik_haber` 0).

PostgreSQL'de ORM'in bilmediği üç ek kurulur:

1. `pg_trgm` uzantısı. PG 13'ten beri "güvenilir" uzantı; veritabanı sahibi
   süper kullanıcı olmadan kurabilir.
2. `vektor` — üretilmiş (`GENERATED ALWAYS ... STORED`) `tsvector` sütunu.
   Kelimeler `to_tsvector`'ın ayrıştırıcısından DEĞİL, `metin` sütunundaki
   hazır kelime dizisinden gelir (`array_to_tsvector`). Gerekçe: kelime
   bölme ve harf kuralı Python'da tek yerde (`arama_metni.kayit_metni`);
   `to_tsvector('simple', …)` aynı metni kendi kuralıyla yeniden bölerdi
   (`covid_19` → iki kelime, `3.5` → sayı) ve saklanan kelime ile aranan
   kelime ayrışırdı. Üç işlev de IMMUTABLE (pg_proc'tan doğrulandı), yani
   üretilmiş sütunda kullanılabilir; sütun her yazımda kendiliğinden tazelenir,
   tetikleyici gerekmez.
3. İki GIN indeksi: `vektor` (okur araması, `kelime:*`) ve `baslik`
   üzerinde `gin_trgm_ops` (panelin alt dizi araması, `LIKE '%…%'`).

Geri alma: tablo düşünce sütun ve indeksler de düşer; uzantı bırakılır
(başka nesne kullanıyor olabilir).
"""

import django.db.models.deletion
from django.db import migrations, models

PG_KUR = [
    "CREATE EXTENSION IF NOT EXISTS pg_trgm",
    "ALTER TABLE icerik_haberarama ADD COLUMN vektor tsvector "
    "GENERATED ALWAYS AS "
    "(array_to_tsvector(array_remove(string_to_array(metin, ' '), ''))) STORED",
    "CREATE INDEX haberarama_vektor_gin ON icerik_haberarama USING gin (vektor)",
    "CREATE INDEX haberarama_baslik_trgm ON icerik_haberarama "
    "USING gin (baslik gin_trgm_ops)",
]


def pg_ekleri(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    for sql in PG_KUR:
        schema_editor.execute(sql)


class Migration(migrations.Migration):

    dependencies = [
        ("icerik", "0015_basarim_indeksleri"),
    ]

    operations = [
        migrations.CreateModel(
            name="HaberArama",
            fields=[
                ("haber", models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE, primary_key=True,
                    related_name="arama", serialize=False, to="icerik.haber")),
                ("baslik", models.TextField(blank=True, help_text="Normalize başlık.")),
                ("metin", models.TextField(blank=True,
                                           help_text="Normalize başlık + spot.")),
            ],
            options={
                "verbose_name": "haber arama metni",
                "verbose_name_plural": "haber arama metinleri",
            },
        ),
        migrations.RunPython(pg_ekleri, migrations.RunPython.noop),
    ]
