"""13 kategoriyi, üç türdeki slug ve kimlikleriyle kurar. 17 ilçeyi ekler.

Veriler **ölçülmüş**, uydurma değil:

- Kategori adları ve haber kimlikleri: panelin kategori açılır listesinden
  (`PANEL-NOTLARI.md`).
- Haber slug'ları: canlı sitenin 556.824 adresinden çıkarıldı.
- Foto/video kimlikleri: ölçülen kural — **foto = haber_id + 200**,
  **video = haber_id + 300** (19/19 örnekte doğrulandı).
- İlçe listesi: kanonik 17 ilçe.

Tekrar çalıştırılabilir; var olan kaydı günceller, kopya üretmez.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from taksonomi.models import Ilce, Kategori, KategoriTur, Yonlendirme

# (ad, haber_kimligi, haber_slug, sira)
# haber_slug canli sitemap'in TAMAMINDAN olculdu (556.824 adres, 14 slug).
# Sayilar: gundem 211.205 · spor 81.342 · bursa 81.336 · dunya 68.680 ·
# ekonomi 54.215 · magazin 28.845 · bursaspor 11.577 · saglik 6.752 ·
# teknoloji 4.705 · yasam 3.495 · bursa-da-spor 3.331 · aktualite 859 ·
# savunma-sanayi 478. 14. slug `bursada-spor` (4 adres) bir sapmadir,
# YONLENDIRME olarak kurulur.
KATEGORILER = [
    ("GÜNDEM",         12,   "gundem",         1, True),
    ("BURSA",           8,   "bursa",          2, True),
    ("BURSASPOR",       9,   "bursaspor",      3, True),
    ("EKONOMİ",         5,   "ekonomi",        4, True),
    ("DÜNYA",           4,   "dunya",          5, True),
    ("SPOR",            7,   "spor",           6, True),
    ("MAGAZİN",         3,   "magazin",        7, True),
    ("SAĞLIK",         11,   "saglik",         8, True),
    ("TEKNOLOJİ",      48,   "teknoloji",      9, True),
    ("YAŞAM",          49,   "yasam",         10, True),
    ("BURSA'DA SPOR",  50,   "bursa-da-spor", 11, True),
    ("AKTÜALİTE",    1019,   "aktualite",     12, True),
    ("SAVUNMA SANAYİ", 1021, "savunma-sanayi", 13, True),
]

FOTO_FARKI = 200
VIDEO_FARKI = 300

ILCELER = [
    "Osmangazi", "Nilüfer", "Yıldırım", "İnegöl", "Gemlik", "Mudanya",
    "İznik", "Karacabey", "Orhangazi", "Yenişehir", "Mustafakemalpaşa",
    "Kestel", "Gürsu", "Orhaneli", "Keles", "Harmancık", "Büyükorhan",
]

ILCE_SLUG = {
    "Osmangazi": "osmangazi", "Nilüfer": "nilufer", "Yıldırım": "yildirim",
    "İnegöl": "inegol", "Gemlik": "gemlik", "Mudanya": "mudanya",
    "İznik": "iznik", "Karacabey": "karacabey", "Orhangazi": "orhangazi",
    "Yenişehir": "yenisehir", "Mustafakemalpaşa": "mustafakemalpasa",
    "Kestel": "kestel", "Gürsu": "gursu", "Orhaneli": "orhaneli",
    "Keles": "keles", "Harmancık": "harmancik", "Büyükorhan": "buyukorhan",
}


class Command(BaseCommand):
    help = "Kategori, kategori türü ve ilçe tohum verisini kurar."

    @transaction.atomic
    def handle(self, *args, **secenekler):
        y = self.stdout.write
        olculmemis = []

        for ad, haber_id, slug, sira, olculdu in KATEGORILER:
            kategori, _ = Kategori.objects.update_or_create(
                ad=ad, defaults={"sira": sira, "aktif": True},
            )
            if not olculdu:
                olculmemis.append(f"{ad} (/{slug}/)")

            for tur, kimlik in (
                (Kategori.TUR_HABER, haber_id),
                (Kategori.TUR_FOTO, haber_id + FOTO_FARKI),
                (Kategori.TUR_VIDEO, haber_id + VIDEO_FARKI),
            ):
                KategoriTur.objects.update_or_create(
                    kategori=kategori, tur=tur,
                    defaults={"eski_id": kimlik, "slug": slug},
                )

        # Tek aylik slug sapmasi: 2022-01'de 4 haber `bursada-spor` altinda
        # yayimlanmis. Kimlikle cozum bunu zaten kurtarir, ama kanonik adres
        # `bursa-da-spor` oldugu icin yonlendirme kaydi aciyoruz.
        Yonlendirme.objects.update_or_create(
            eski_yol="/bursada-spor/",
            defaults={
                "yeni_yol": "/bursa-da-spor/",
                "kod": 301,
                "sebep": "2022-01'de tek aylik slug sapmasi (4 adres).",
            },
        )

        for sira, ad in enumerate(ILCELER, 1):
            Ilce.objects.update_or_create(
                ad=ad, defaults={"slug": ILCE_SLUG[ad], "sira": sira},
            )

        y(self.style.SUCCESS(
            f"Kategori {Kategori.objects.count()} · "
            f"kategori türü {KategoriTur.objects.count()} · "
            f"ilçe {Ilce.objects.count()}"
        ))
        if olculmemis:
            y(self.style.WARNING(
                "Slug'ı ÖLÇÜLMEDİ, standart dönüşümle türetildi — göç öncesi "
                "canlı siteden doğrulanmalı:"
            ))
            for satir in olculmemis:
                y(self.style.WARNING(f"  {satir}"))
