"""Medya adres kalıpları.

**Sıra bağlayıcıdır** ve `taksonomi/adresler.py`deki tuzağın aynısı burada da
geçerli: `/yazarlar/namik-goz-76` iki dilimlidir ve genel haber kalıbına da
uyar. Bu yüzden bu tablo kök adres tablosunda **genel haber kalıbından önce**
bağlanmak zorundadır.

Kalıp parçaları (`KIMLIK`, `DILIM`) taksonomiden **ithal edilir**, burada
yeniden yazılmaz: iki yerde iki kopya olsaydı biri düzeltilip diğeri unutulur
ve adresler sessizce ayrışırdı.
"""

from django.conf import settings
from django.urls import path, re_path
from django.views.static import serve

from taksonomi.adresler import DILIM, KIMLIK

from . import views

app_name = "medya"

# Medya ailelerinin görselleri arşiv kökünün altında **kardeş** klasörlerde:
# `gorseller-galeri/`, `gorseller-video/`, `gorseller-yazar/`, `gorseller-kose/`.
# `/arsiv-gorsel/` yalnız `gorseller/` klasörüne bakıyor, o yüzden bunların
# kendi öneki var. Aile aile açılıyor ki `veri-*` klasörlerindeki JSON
# dökümleri adresten okunabilir olmasın.
# Geliştirmede Django servis eder; yayında bunu web sunucusu üstlenir —
# kök adres tablosundaki `/arsiv-gorsel/` ile aynı düzen.
_GORSEL_KLASORLERI = ["gorseller-galeri", "gorseller-video",
                      "gorseller-yazar", "gorseller-kose"]

urlpatterns = [
    *[
        re_path(rf"^arsiv-medya/{klasor}/(?P<path>.*)$", serve,
                {"document_root": settings.ARSIV_KOK / klasor})
        for klasor in _GORSEL_KLASORLERI
    ],

    # --- Bölüm listeleri. Tek dilimli oldukları için kategori kalıbından da
    # önce gelmeliler. Kök tabloda şu an `icerik.bekleyen_aile` bu üç yolu
    # tutuyor; veri geldiğinde onların yerini bunlar alır.
    path("yazarlar", views.yazar_listesi, name="yazarlar"),
    path("galeriler", views.galeri_listesi, name="galeriler"),
    path("videolar", views.video_listesi, name="videolar"),

    # --- İki/üç dilimli içerik kalıpları. Uzun olan (köşe yazısı) yazar
    # kalıbından ÖNCE gelmeli, yoksa `/yazarlar/{yazar}/{yazi}` yazar
    # sayfası sanılıp son dilim yutulur.
    re_path(rf"^yazarlar/{DILIM}/{KIMLIK}/?$", views.kose_yazisi, name="kose"),
    re_path(rf"^yazarlar/{DILIM}/?$", views.yazar, name="yazar"),
    re_path(rf"^galeriler/{DILIM}/{KIMLIK}/?$", views.foto_galeri, name="galeri"),
    re_path(rf"^videolar/{DILIM}/{KIMLIK}/?$", views.video, name="video"),
]
