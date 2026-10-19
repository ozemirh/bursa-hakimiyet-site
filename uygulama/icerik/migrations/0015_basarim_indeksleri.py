# Elle yazıldı — 19 Ekim 2026, başarım paketi. Django'nun ürettiği hâli
# KULLANILMADI: beş `AlterField` (db_index=False) SQLite'ta `_remake_table`
# ile 3,7 GB'lık `icerik_haber`i kopyalayıp yeniden kurardı. Burada alan
# değişiklikleri yalnız DURUMA işleniyor (`SeparateDatabaseAndState`);
# veritabanında yalnız indeks düşürülüyor. Tablo yeniden kurulmuyor:
# `sqlmigrate` çıktısında `new__icerik_haber` 0 · `DROP TABLE` 0 ·
# `INSERT INTO` 0.
#
# Bütün SQL SQLite ve PostgreSQL'de aynı sözdizimiyle geçerli: indeks
# adları Django'nun motordan bağımsız ad üreticisinden (tablo + sütun
# karması) geliyor, `DROP INDEX IF EXISTS` ve `ANALYZE tablo` iki motorda
# da var.
#
# ÖLÇÜM — 1.038.477 haberlik veritabanının kopyası (EXPLAIN QUERY PLAN +
# süre; gerçek veritabanına UYGULANMADI, salt okunur):
#
#   sorgu                                önce                 sonra
#   panel masa kuyruğu (LIMIT 20)        68.300 ms (SCAN)     1,1 ms
#   panel editör süzgeci (LIMIT 25)      67.000 ms (SCAN)     indeksli
#   kategori sayfası (21 satır)          6,0 ms + TEMP B-TREE 0,9 ms
#   kategori sınırlı sayım (1.001)       118 ms               6,3 ms
#   ilçe sayfası (20 satır)              6,0 ms + TEMP B-TREE 1,0 ms
#   site haritası ay özeti               51–87 ms             1,0 ms (kapsayan)
#   site haritası toplu gruplama         49.641 ms            865 ms (kapsayan)
#   menü sayımı (GROUP BY kategori)      3.694 ms (soğuk)     138–226 ms
#   konu üyeleri (300 bağ)               TEMP B-TREE          indeks sırası
#
# Düşürülen tek sütunlu indekslerin her biri bir bileşik indeksin ÖNEKİ;
# düşürüldükten sonra koruma denetimleri bileşikten kapsayan okunuyor:
#   kategori PROTECT  `kategori_id IN (…)`  → haber_kategori_sira (COVERING)
#   ilçe SET NULL     `ilce_id IN (…)`      → haber_ilce_sira (COVERING)
#   kullanıcı SET NULL `olusturan_id IN (…)` → (olusturan, durum)
#   `yayin_zamani` aralıkları                → haber_okur_kismi / haber_siralama
# `yayin_zamani` tek sütunlu indeksi gereksiz olmanın ötesinde ZARARLIYDI:
# planlayıcı onu seçince kapsayan indeksi bırakıp her satırda tabloya
# gidiyordu (toplu gruplama 49,6 sn → indeks kalkınca 1,1 sn).
#
# SÜRE (kopyada, soğuk disk): her CREATE INDEX tabloyu bir kez tarar —
# masa 21 sn · okur 42–83 sn · kategori 43 sn · ilçe 40 sn · konu 0,2 sn;
# ANALYZE 7,5 sn. Gerçek migrate süresi raporda (kopyada ölçüldü).
# Göç sonrası `ANALYZE` standart adım: planlayıcı yeni indeksleri ancak
# istatistikle doğru seçer (§24'ün bayat istatistik tuzağı).

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def _dusur(ad, tablo, sutun):
    """Tek sütunlu indeksi düşür; geri alırken aynı adla yeniden kur."""
    return migrations.RunSQL(
        sql=f'DROP INDEX IF EXISTS "{ad}"',
        reverse_sql=f'CREATE INDEX IF NOT EXISTS "{ad}" ON "{tablo}" ("{sutun}")')


class Migration(migrations.Migration):

    dependencies = [
        ('icerik', '0014_konu_takibi'),
        ('taksonomi', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # 1. Yeni indeksler ÖNCE kurulur; eskiler sonra düşer. Arada hiçbir
        #    sorgu indekssiz kalmaz.
        migrations.AddIndex(
            model_name='haber',
            index=models.Index(condition=models.Q(('durum', 1), ('yayin_zamani__isnull', False)),
                               fields=['-yayin_zamani', '-id', 'guncelleme_zamani', 'durum'],
                               name='haber_okur_kismi'),
        ),
        migrations.AddIndex(
            model_name='haber',
            index=models.Index(fields=['kategori', '-yayin_zamani', '-id'],
                               name='haber_kategori_sira'),
        ),
        migrations.AddIndex(
            model_name='haber',
            index=models.Index(fields=['ilce', '-yayin_zamani', '-id'], name='haber_ilce_sira'),
        ),
        migrations.AddIndex(
            model_name='haber',
            index=models.Index(fields=['olusturan', '-yayin_zamani', '-id'],
                               name='haber_olusturan_sira'),
        ),
        migrations.AddIndex(
            model_name='haber',
            index=models.Index(condition=models.Q(('hazirlik', ''), _negated=True),
                               fields=['hazirlik', '-yayin_zamani', '-id'],
                               name='haber_masa_kismi'),
        ),
        migrations.AddIndex(
            model_name='konuhaber',
            index=models.Index(fields=['konu', 'tarih', 'haber'], name='konuhaber_sira'),
        ),

        # 2. Yerini yenisine bırakan iki bileşik indeks (ikinci sıralama
        #    anahtarı `-id` eksikti). RemoveIndex düz DROP INDEX'tir.
        migrations.RemoveIndex(model_name='haber', name='icerik_habe_kategor_32060b_idx'),
        migrations.RemoveIndex(model_name='haber', name='icerik_habe_ilce_id_72bdcf_idx'),

        # 3. Tek sütunlu indeksler: durum değişikliği + yalnız DROP INDEX.
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterField(
                    model_name='haber',
                    name='kategori',
                    field=models.ForeignKey(db_index=False,
                                            on_delete=django.db.models.deletion.PROTECT,
                                            related_name='haberler', to='taksonomi.kategori'),
                ),
                migrations.AlterField(
                    model_name='haber',
                    name='ilce',
                    field=models.ForeignKey(blank=True, db_index=False, null=True,
                                            on_delete=django.db.models.deletion.SET_NULL,
                                            related_name='haberler', to='taksonomi.ilce'),
                ),
                migrations.AlterField(
                    model_name='haber',
                    name='olusturan',
                    field=models.ForeignKey(
                        blank=True, db_index=False, null=True,
                        help_text="Haberi giren kullanıcı. 'Kendi haberini yayınlama' "
                                  "yetkisi buna bakar.",
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name='haberleri', to=settings.AUTH_USER_MODEL),
                ),
                migrations.AlterField(
                    model_name='haber',
                    name='yayin_zamani',
                    field=models.DateTimeField(blank=True, null=True),
                ),
                migrations.AlterField(
                    model_name='konuhaber',
                    name='konu',
                    field=models.ForeignKey(db_index=False,
                                            on_delete=django.db.models.deletion.CASCADE,
                                            related_name='baglar', to='icerik.konu'),
                ),
            ],
            database_operations=[
                _dusur('icerik_haber_kategori_id_44e1a6d4', 'icerik_haber', 'kategori_id'),
                _dusur('icerik_haber_ilce_id_f7d38216', 'icerik_haber', 'ilce_id'),
                _dusur('icerik_haber_olusturan_id_e0c72ac9', 'icerik_haber', 'olusturan_id'),
                _dusur('icerik_haber_yayin_zamani_659599b2', 'icerik_haber', 'yayin_zamani'),
                _dusur('icerik_konuhaber_konu_id_df6efd6d', 'icerik_konuhaber', 'konu_id'),
            ],
        ),

        # 4. İstatistik. İki motorda da `ANALYZE tablo` geçerli.
        migrations.RunSQL(sql='ANALYZE icerik_haber', reverse_sql=migrations.RunSQL.noop),
        migrations.RunSQL(sql='ANALYZE icerik_konuhaber', reverse_sql=migrations.RunSQL.noop),
    ]
