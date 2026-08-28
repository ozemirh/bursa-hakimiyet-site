# -*- coding: utf-8 -*-
"""Manşet ekranı için üç KISMİ indeks — 28 Ağustos 2026.

## Ölçülen kural: indeksin koşulu, ORM'in yazdığı biçimle EŞLEŞMELİ

SQLite kısmi indeksi ancak sorgunun WHERE'i indeksin WHERE'ini örtük olarak
içeriyorsa kullanır ve bu eşleşme **sözdizimsel**. Django boolean alanları
her yerde **çıplak sütun** olarak yazıyor (`WHERE "manset_ana"`), `= 1`
olarak değil — tek filtrede de, OR içinde de.

ÖLÇÜM (yalıtılmış tabloda, üç indeks biçimi × beş sorgu biçimi):

    indeks koşulu    tek çıplak   tek =1   OR çıplak   OR =1   OR >0
    WHERE "x"        KULLANDI     hayır    hayır       hayır   hayır
    WHERE "x" = 1    hayır        KULLANDI hayır       KULLANDI hayır
    WHERE "x" > 0    hayır        hayır    hayır       hayır   KULLANDI

Django'nun `Index(condition=Q(x=True))`'i **çıplak** biçimi üretiyor. Yani
ORM ile eşleşen tek çalışan hücre: **çıplak indeks + tek sütunlu sorgu.**

`OR` biçiminin hiçbir çıplak eşleşmesi yok. Bu yüzden indeksler Django'nun
kendi `AddIndex`iyle kuruluyor (ham SQL gerekmiyor) ve **görünüm OR yerine
üç ayrı indeksli sorgu** çalıştırıyor (`icerik/panel.py`, `mansetler`).

Ölçülen kazanç: manşet sorgusu **752 ms → 0,2 ms** (tam tarama yerine
örtücü indeks taraması). İndeksler kısmi olduğu için yalnız işaretli
satırları taşır; manşetli kayıt doğası gereği azdır.

Geri alma: `DROP INDEX` — şemayı bozmaz, veri kaybı yok.
"""

from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):

    dependencies = [
        ("icerik", "0005_bildirim_gazete_ikiadimli_logkaydi_reklamkampanyasi_and_more"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="haber",
            index=models.Index(fields=["manset_ana"], condition=Q(manset_ana=True),
                               name="haber_manset_ana_kismi"),
        ),
        migrations.AddIndex(
            model_name="haber",
            index=models.Index(fields=["manset_tepe"], condition=Q(manset_tepe=True),
                               name="haber_manset_tepe_kismi"),
        ),
        migrations.AddIndex(
            model_name="haber",
            index=models.Index(fields=["manset_kare"], condition=Q(manset_kare=True),
                               name="haber_manset_kare_kismi"),
        ),
        # PAKETİN SONU: istatistikleri tazele (0005'te öğrenildi).
        migrations.RunSQL(sql="ANALYZE;", reverse_sql=migrations.RunSQL.noop),
    ]
