"""Adres sözleşmesi — canlı sitedeki her eski adres buradan çözülür.

**Sıra bağlayıcıdır.** Django kalıpları yukarıdan aşağıya dener ve ilk eşleşeni
kullanır. Buradaki tuzak şudur:

    /yazarlar/namik-goz-76        → yazar sayfası (2 dilim)
    /gundem/bir-haber-526347      → haber        (2 dilim)

İkisi de iki dilimli. Genel haber kalıbı önce gelirse yazar sayfası
"kategori=yazarlar, slug=namik-goz, id=76" diye çözülür ve yazar sayfaları
kaybolur. Bu yüzden **önekli kalıplar önce, genel haber kalıbı en sonda**.

Ölçülmüş desenler (26 Ağustos 2026):

| Tür        | Desen                                                  | Örnek                                    |
|------------|--------------------------------------------------------|------------------------------------------|
| Köşe yazısı| `/yazarlar/{yazar}-{yid}/{slug}-{id}`                   | /yazarlar/namik-goz-76/…-32099            |
| Yazar      | `/yazarlar/{yazar}-{yid}`                               | /yazarlar/namik-goz-76                    |
| Foto galeri| `/galeriler/{kategori}-{katid}/{slug}-{id}`             | /galeriler/bursa-208/…-12431              |
| Video      | `/videolar/{kategori}-{katid}/{slug}-{id}`              | /videolar/bursa-308/…-91994               |
| Haber      | `/{kategori}/{slug}-{id}`                               | /spor/lucescu-…-526347                    |

Kimlik her zaman yolun sonundaki sayıdır ve **çözüm kimlikle yapılır**; slug
uyuşmuyorsa kanonik adrese 301 verilir. Canlı site de böyle davranıyor
(`/spor/yanlis-slug-526347` → 200, kanonike yönlendirme).
"""

from django.urls import re_path

from . import views

# Yolun sonundaki `-{sayı}` kimliktir. Slug açgözlü olmamalı, yoksa
# "namik-goz-76" içindeki 76'yı slug'a katar.
KIMLIK = r"(?P<slug>[^/]+?)-(?P<kimlik>\d+)"

# Kategori/yazar dilimi: `{slug}-{eski_id}` biçiminde.
DILIM = r"(?P<dilim_slug>[^/]+?)-(?P<dilim_id>\d+)"

app_name = "taksonomi"

urlpatterns = [
    # --- ÖNEKLİ KALIPLAR (genel haber kalıbından ÖNCE gelmek zorunda) ---
    re_path(
        rf"^yazarlar/{DILIM}/{KIMLIK}/?$",
        views.kose_yazisi, name="kose",
    ),
    re_path(
        rf"^yazarlar/{DILIM}/?$",
        views.yazar, name="yazar",
    ),
    re_path(
        rf"^galeriler/{DILIM}/{KIMLIK}/?$",
        views.foto_galeri, name="galeri",
    ),
    re_path(
        rf"^videolar/{DILIM}/{KIMLIK}/?$",
        views.video, name="video",
    ),
    # --- GENEL HABER KALIBI — en sonda kalmalı ---
    re_path(
        rf"^(?P<kategori>[^/]+)/{KIMLIK}/?$",
        views.haber, name="haber",
    ),
]
