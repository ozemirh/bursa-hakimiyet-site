"""Kök adres tablosu.

**Sıra bağlayıcıdır.** Sabit yollar (`/ara`, `/ilceler`) kategori kalıbından
önce gelmek zorunda; kategori kalıbı `^(?P<slug>[^/]+)$` her tek dilimli yolu
yakalar ve sonra gelen hiçbir şey eşleşmez.

Adres sözleşmesinin kendisi `taksonomi/adresler.py` içinde; buradaki sıralama
onun bir üst katmanıdır: önce anasayfa ve site bölümleri, sonra iki dilimli
içerik kalıpları, en sonda tek dilimli kategori.
"""

from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve

from django.contrib.auth import views as kimlik_gorunum

from icerik import panel as panel_gorunum
from icerik import views as icerik_gorunum

urlpatterns = [
    # Arsiv gorselleri repo disinda (D: surucusu). Gelistirmede Django
    # servis eder; yayinda bunu web sunucusu ustlenir.
    re_path(r"^arsiv-gorsel/(?P<path>.*)$", serve,
            {"document_root": settings.ARSIV_GORSEL_KOK}),
    path("yonetim/", admin.site.urls),

    # --- Yonetim paneli (F5). Site adreslerinden ONCE: "panel" tek dilimli
    # oldugu icin en sondaki kategori kalibina da uyar.
    path("panel/giris", kimlik_gorunum.LoginView.as_view(
        template_name="panel/giris.html", redirect_authenticated_user=True),
        name="panel-giris"),
    path("panel/cikis", kimlik_gorunum.LogoutView.as_view(next_page="/panel/giris"),
         name="panel-cikis"),
    path("panel/", panel_gorunum.bugun, name="panel-bugun"),
    path("panel/akis", panel_gorunum.akis, name="panel-akis"),
    path("panel/haber/ekle", panel_gorunum.haber_ekle, name="panel-haber-ekle"),
    path("panel/haber/<int:kimlik>", panel_gorunum.haber_duzenle,
         name="panel-haber-duzenle"),

    # Icerik bolumunun kalan aileleri. Adres kaliplari liste/duzenle
    # ciftidir; duzenle yolu tekil, liste yolu cogul adla duruyor ki
    # menudeki bagla birebir okunsun.
    # Toplu islem: yalniz POST. Fiil yetkisi gorunumun icinde denetleniyor,
    # cunku her fiilin yetkiligi ayri (PANEL-NOTLARI.md 12).
    path("panel/toplu", panel_gorunum.toplu_islem, name="panel-toplu"),
    # Medya ailelerinde toplu durum fiilleri. Aile adresin parcasi;
    # her aile kendi ekran yetkisiyle ayrica korunuyor.
    path("panel/toplu/<str:aile>", panel_gorunum.medya_toplu_islem,
         name="panel-medya-toplu"),
    path("panel/mansetler", panel_gorunum.mansetler, name="panel-mansetler"),
    path("panel/kose", panel_gorunum.kose_listesi, name="panel-kose"),
    path("panel/kose/<int:kimlik>", panel_gorunum.kose_duzenle,
         name="panel-kose-duzenle"),
    path("panel/yazarlar", panel_gorunum.yazar_listesi, name="panel-yazarlar"),
    path("panel/yazar/<int:kimlik>", panel_gorunum.yazar_duzenle,
         name="panel-yazar-duzenle"),
    path("panel/galeriler", panel_gorunum.galeri_listesi,
         name="panel-galeriler"),
    path("panel/galeri/<int:kimlik>", panel_gorunum.galeri_duzenle,
         name="panel-galeri-duzenle"),
    path("panel/videolar", panel_gorunum.video_listesi, name="panel-videolar"),
    path("panel/video/<int:kimlik>", panel_gorunum.video_duzenle,
         name="panel-video-duzenle"),

    # Ayarlar bolumu.
    path("panel/kategoriler", panel_gorunum.kategori_listesi,
         name="panel-kategoriler"),
    path("panel/kategori/<int:kimlik>", panel_gorunum.kategori_duzenle,
         name="panel-kategori-duzenle"),
    path("panel/kullanicilar", panel_gorunum.kullanici_listesi,
         name="panel-kullanicilar"),
    path("panel/kullanici/<int:kimlik>", panel_gorunum.kullanici_duzenle,
         name="panel-kullanici-duzenle"),
    path("panel/kaynaklar", panel_gorunum.kaynak_listesi,
         name="panel-kaynaklar"),
    path("panel/kaynak/<int:kimlik>", panel_gorunum.kaynak_duzenle,
         name="panel-kaynak-duzenle"),
    path("panel/roller", panel_gorunum.roller, name="panel-roller"),

    # Sifre: yetkilik YOK, herkes kendi parolasini degistirebilmeli.
    # PasswordChangeView kendi dispatch'inde login_required tasiyor.
    path("panel/sifre", panel_gorunum.SifreDegistir.as_view(),
         name="panel-sifre"),

    path("", icerik_gorunum.anasayfa, name="anasayfa"),
    path("ara", icerik_gorunum.arama, name="arama"),
    path("ilceler", icerik_gorunum.ilceler, name="ilceler"),
    re_path(r"^ilce/(?P<slug>[-\w]+)/?$", icerik_gorunum.ilce, name="ilce"),
    path("resmi-ilan", icerik_gorunum.resmi_ilan, name="resmi-ilan"),

    # Besleme: /rss tek dilimli oldugu icin en sondaki kategori kalibi onu
    # yakalardi; kategori kalibindan ONCE gelmek zorunda.
    path("", include("besleme.adresler")),

    # Medya aileleri (yazar - kose - galeri - video). Kendi liste sayfalari
    # ve iki dilimli detay kaliplari burada; taksonomi'deki taslak
    # cozumleyicilerden ONCE gelmeli ki gercek sayfalar kazansin.
    path("", include("medya.adresler")),

    # Iki dilimli icerik kaliplari (yazar, galeri, video, haber).
    path("", include("taksonomi.adresler")),

    # Tek dilimli kategori listesi — en sonda kalmali.
    re_path(r"^(?P<slug>[-\w]+)/?$", icerik_gorunum.kategori, name="kategori"),
]
