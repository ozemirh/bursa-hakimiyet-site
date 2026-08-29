"""`kaynak_turu` boş olabilir hâle gelir ve uydurulmuş `ajans` değerleri silinir.

NEDEN. Alan `default="ajans"` ile açılmıştı; arşivden gelen 356.839 haberin
**hiçbirinde** kaynak türü kaydı yoktu, hepsi bu varsayılanla yazıldı.
`meta_yazar` backfill'i (URUN-PLANI.md §25) kaynak alanından `haber_merkezi`
(336.547) ve `bulten` (545) değerlerini ölçtü ama bu kayıtlar için doğru bir
kaynak türü **yok**, o yüzden alana dokunmadı — 337.450 kayıt hâlâ "ajans"
görünüyordu.

RİSK. Bu kayıtlardan biri panelden kaydedilse `Haber.save()` içindeki
`meta_yazar = META_TURETIM["ajans"]` türetimi ölçülen değeri `haber_ajansi`
yapardı: kaynağı olmayan haberi "ajanstan geldi" diye damgalamak.

ÖLÇÜT, uydurma değil: kaynak türü ile meta yazar birbirini tutmuyorsa o
kaynak türü hiç ölçülmemiştir ve boşaltılır. `meta_yazar_elle=True` olan
kayda dokunulmaz — editörün elle seçtiği değer türetimi zaten durdurur ve
kaynak türü orada bağımsız bilgidir.
"""

from django.db import migrations, models

# Kaynak türü <-> ölçülmüş meta yazar eşleşmesi (Haber.META_TURETIM).
TUTARLI = {
    "ajans": "haber_ajansi",
    "dis_yayin": "alinti",
    "muhabir": "fikir_iscisi",
}


def bosalt(apps, schema_editor):
    Haber = apps.get_model("icerik", "Haber")
    for tur, meta in TUTARLI.items():
        (Haber.objects
         .filter(kaynak_turu=tur, meta_yazar_elle=False)
         .exclude(meta_yazar=meta)
         .update(kaynak_turu=""))


def geri_al(apps, schema_editor):
    # Alan boş olamayacağı için eski varsayılana dönülür; bilgi kazanılmaz,
    # migration'ın geri alınabilir kalması için var.
    Haber = apps.get_model("icerik", "Haber")
    Haber.objects.filter(kaynak_turu="").update(kaynak_turu="ajans")


class Migration(migrations.Migration):

    dependencies = [
        ('icerik', '0007_haber_bagli_galeriler'),
    ]

    operations = [
        migrations.AlterField(
            model_name='haber',
            name='kaynak_turu',
            field=models.CharField(blank=True, choices=[('ajans', 'Ajans'), ('dis_yayin', 'Dış yayın'), ('muhabir', 'Kendi muhabirimiz')], default='', help_text="Boş = ölçülemedi. Arşivden gelen 337 bin haberin kaynak türü kayıtlarda yoktu; varsayılan 'Ajans' bunu uydurmuş oluyordu.", max_length=12),
        ),
        migrations.RunPython(bosalt, geri_al),
    ]
