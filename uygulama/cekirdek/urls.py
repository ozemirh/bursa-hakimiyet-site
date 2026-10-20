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

from cekirdek import adres_duzeni
from cekirdek import durum as durum_gorunum

from icerik import gorsel_turev
from icerik import panel as panel_gorunum
from icerik import piyasa as piyasa_sayfa
from icerik import panel_yz
from icerik.giris_guvenligi import GirisGorunumu
from icerik import reklam as reklam_gorunum
from icerik import views as icerik_gorunum
from sosyal import panel as sosyal_gorunum

urlpatterns = [
    # Arsiv gorselleri repo disinda (D: surucusu). Gelistirmede Django
    # servis eder; yayinda bunu web sunucusu ustlenir.
    re_path(r"^arsiv-gorsel/(?P<path>.*)$", serve,
            {"document_root": settings.ARSIV_GORSEL_KOK}),
    # Gorsel turevleri (19 Ekim 2026): /gorsel/<genislik|og>/<kaynak yol>.webp
    # Ilk istekte uretir, diske yazar; yayinda nginx dosyadan verir.
    # Sabit oranlı kırpımlar (og, 16x9, 4x3, 1x1) JSON-LD görsel dizisi için.
    re_path(r"^gorsel/(?P<boyut>\d{3,4}|og|16x9|4x3|1x1)/(?P<yol>.+)$", gorsel_turev.gorunum,
            name="gorsel-turev"),
    path("yonetim/", admin.site.urls),
    # Saglik ucu (19 Ekim 2026). `\w` alt cizgiyi de yakaladigi icin
    # kategori kalibindan ONCE olmak zorunda; `/saglik` bir kategori slug'i.
    path("_durum", durum_gorunum.durum, name="durum"),

    # --- Yonetim paneli (F5). Site adreslerinden ONCE: "panel" tek dilimli
    # oldugu icin en sondaki kategori kalibina da uyar.
    # Giriş: başarısız deneme sınırı (kullanıcı adı + IP, IP) ve kilit —
    # icerik/giris_guvenligi.py (Paket F madde 8).
    path("panel/giris", GirisGorunumu.as_view(), name="panel-giris"),
    path("panel/cikis", kimlik_gorunum.LogoutView.as_view(next_page="/panel/giris"),
         name="panel-cikis"),
    path("panel/", panel_gorunum.bugun, name="panel-bugun"),
    path("panel/akis", panel_gorunum.akis, name="panel-akis"),
    # Okunma raporu salt okuma; ayri bir yetkilik acilmadi.
    path("panel/okunma", panel_gorunum.okunma_raporu, name="panel-okunma"),
    path("panel/haber/ekle", panel_gorunum.haber_ekle, name="panel-haber-ekle"),
    # Yapay zeka koprusu: adresten taslak acar, yayinlamaz.
    path("panel/yz-taslak", panel_gorunum.yz_taslak_ekle,
         name="panel-yz-taslak-ekle"),
    path("panel/yz-taslak/<int:kimlik>", panel_gorunum.yz_taslak_detay,
         name="panel-yz-taslak"),
    path("panel/yz-taslak/<int:kimlik>/gorsel", panel_gorunum.yz_gorsel_indir,
         name="panel-yz-gorsel"),
    # K2 bulgusu tek tek kapatilir (Paket M); gorunum ayri dosyada.
    path("panel/yz-taslak/<int:kimlik>/bulgu/<int:bulgu>", panel_yz.bulgu_kapat,
         name="panel-yz-bulgu-kapat"),
    # Ilgili haber secicisinin JSON ucu. Salt okuma; haber formunun
    # 356 bin secenekli <select>ini bu ucla degistirdik.
    path("panel/haber-ara", panel_gorunum.haber_ara,
         name="panel-haber-ara"),
    path("panel/galeri-ara", panel_gorunum.galeri_ara,
         name="panel-galeri-ara"),
    path("panel/haber/<int:kimlik>", panel_gorunum.haber_duzenle,
         name="panel-haber-duzenle"),
    # Bugun ekraninin tek tik "Yayina al" fiili (Paket H). Yalniz POST;
    # tek yayin kapisindan gecer.
    path("panel/haber/<int:kimlik>/yayinla", panel_gorunum.haber_yayinla,
         name="panel-haber-yayinla"),

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
    # Konu takibi (5 Eylul 2026): liste, dosya, onay fiili, haber cikarma.
    # Yetkilik `konu_yonetimi` (Editor, Yayin Yonetmeni).
    path("panel/konular", panel_gorunum.konu_listesi, name="panel-konular"),
    path("panel/konu/<int:kimlik>", panel_gorunum.konu_duzenle,
         name="panel-konu-duzenle"),
    path("panel/konu/<int:kimlik>/karar", panel_gorunum.konu_karar,
         name="panel-konu-karar"),
    path("panel/konu/<int:kimlik>/cikar/<int:haber_id>", panel_gorunum.konu_haber_cikar,
         name="panel-konu-haber-cikar"),
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
    # --- Model turu ekranlari (PANEL-NOTLARI.md 24). Dokuz model, dokuz
    # liste + dokuz duzenleme. Yeni yetkilik acilmadi; her ekran mevcut 14
    # yetkilikten birine bagli.
    path("panel/yorumlar", panel_gorunum.yorum_listesi, name="panel-yorumlar"),
    path("panel/yorum/<int:kimlik>", panel_gorunum.yorum_duzenle,
         name="panel-yorum-duzenle"),
    path("panel/son-dakika", panel_gorunum.son_dakika_listesi,
         name="panel-son-dakika"),
    path("panel/son-dakika/<int:kimlik>", panel_gorunum.son_dakika_duzenle,
         name="panel-son-dakika-duzenle"),
    path("panel/ilanlar", panel_gorunum.ilan_listesi, name="panel-ilanlar"),
    path("panel/ilan/<int:kimlik>", panel_gorunum.ilan_duzenle,
         name="panel-ilan-duzenle"),
    path("panel/yuvalar", panel_gorunum.yuva_listesi, name="panel-yuvalar"),
    path("panel/yuva/<int:kimlik>", panel_gorunum.yuva_duzenle,
         name="panel-yuva-duzenle"),
    path("panel/kampanyalar", panel_gorunum.kampanya_listesi,
         name="panel-kampanyalar"),
    path("panel/kampanya/<int:kimlik>", panel_gorunum.kampanya_duzenle,
         name="panel-kampanya-duzenle"),
    path("panel/gazeteler", panel_gorunum.gazete_listesi,
         name="panel-gazeteler"),
    path("panel/gazete/<int:kimlik>", panel_gorunum.gazete_duzenle,
         name="panel-gazete-duzenle"),
    path("panel/bildirimler", panel_gorunum.bildirim_listesi,
         name="panel-bildirimler"),
    path("panel/bildirim/<int:kimlik>", panel_gorunum.bildirim_duzenle,
         name="panel-bildirim-duzenle"),

    # --- Sosyal medya paylasimi (5 Eylul 2026). Sabit yollar
    # ("hesaplar", "ekle", "gonder") <int:kimlik> kalibindan ONCE gelmek
    # zorunda degil (int kalibi harf yakalamaz) ama okunurluk icin once
    # yaziliyor. Yetkilik acilmadi; ekranlar mevcut ikisine bagli.
    path("panel/sosyal", sosyal_gorunum.gonderi_listesi, name="panel-sosyal"),
    path("panel/sosyal/gonder", sosyal_gorunum.bekleyenleri_gonder,
         name="panel-sosyal-gonder"),
    path("panel/sosyal/ekle", sosyal_gorunum.gonderi_ekle,
         name="panel-sosyal-ekle"),
    path("panel/sosyal/hesaplar", sosyal_gorunum.hesap_listesi,
         name="panel-sosyal-hesaplar"),
    path("panel/sosyal/hesap/ekle", sosyal_gorunum.hesap_ekle,
         name="panel-sosyal-hesap-ekle"),
    path("panel/sosyal/hesap/<int:kimlik>", sosyal_gorunum.hesap_duzenle,
         name="panel-sosyal-hesap"),
    path("panel/sosyal/<int:kimlik>", sosyal_gorunum.gonderi_detay,
         name="panel-sosyal-gonderi"),
    # Log SALT OKUNUR: duzenlenebilen log, log degildir.
    path("panel/log", panel_gorunum.log_listesi, name="panel-log"),
    path("panel/log/<int:kimlik>", panel_gorunum.log_detay,
         name="panel-log-detay"),
    # 2FA: yetkilik yok, kendi hesabi. Kurulum akisi BILEREK acilmadi.
    path("panel/iki-adimli", panel_gorunum.iki_adimli, name="panel-iki-adimli"),

    path("panel/roller", panel_gorunum.roller, name="panel-roller"),

    # Sifre: yetkilik YOK, herkes kendi parolasini degistirebilmeli.
    # PasswordChangeView kendi dispatch'inde login_required tasiyor.
    path("panel/sifre", panel_gorunum.SifreDegistir.as_view(),
         name="panel-sifre"),

    # Yerel test reklam hizmeti (7 Eylul 2026). Iki dilimli oldugu icin
    # taksonomi kaliplarindan ONCE gelmeli. Kapisi sunum oturumu; siradan
    # ziyaretci 404 alir (bkz. icerik/reklam.py).
    re_path(r"^reklam/test/(?P<en>\d{2,4})x(?P<boy>\d{2,4})\.svg$",
            reklam_gorunum.test_yaratici, name="reklam-test"),

    # ads.txt — AdSense kimligi verildiyse yayimlanir, yoksa 404.
    path("ads.txt", reklam_gorunum.ads_txt, name="ads-txt"),
    path("favicon.ico", adres_duzeni.favicon, name="favicon"),

    path("", icerik_gorunum.anasayfa, name="anasayfa"),
    path("ara", icerik_gorunum.arama, name="arama"),
    path("ilceler", icerik_gorunum.ilceler, name="ilceler"),

    # "Daha fazla göster" (6 Eylul 2026). `/daha-fazla` sayfa degil PARCA
    # dondurur; `/son-haberler` o dugmenin JavaScript'siz karsiligidir.
    # Ikisi de tek dilimli, kategori kalibindan ONCE gelmek zorunda.
    path("daha-fazla", icerik_gorunum.daha_fazla, name="daha-fazla"),
    path("son-haberler", icerik_gorunum.son_haberler, name="son-haberler"),
    re_path(r"^ilce/(?P<slug>[-\w]+)/?$", icerik_gorunum.ilce, name="ilce"),
    path("resmi-ilan", icerik_gorunum.resmi_ilan, name="resmi-ilan"),

    # Nobetci eczane: kalici servis sayfalari (31 Agustos 2026).
    # "nobetci-eczane" tek dilimli, kategori kalibindan ONCE gelmeli.
    # Ilce kalibi `/ilce/<slug>` ile ayni slug kumesini kullanir.
    path("nobetci-eczane", icerik_gorunum.nobetci_eczane,
         name="nobetci-eczane"),
    re_path(r"^nobetci-eczane/(?P<slug>[-\w]+)/?$",
            icerik_gorunum.nobetci_eczane, name="nobetci-eczane-ilce"),
    # Kalici enstruman sayfalari (20 Ekim 2026): /piyasa/dolar, /piyasa/euro,
    # /piyasa/gram-altin. Iki dilimli; haber kalibi `/{kategori}/{slug}-{id}`
    # sondaki SAYIYI ister, bu adlarin hicbiri sayiyla bitmez — yine de
    # medya/taksonomi kaliplarindan ONCE (onekli kaliplar once kurali).
    # Secenekler acik liste (`icerik/piyasa.ENSTRUMANLAR`): `/piyasa/<x>`
    # bicimindeki baska adres bu gorunume dusmez. Sondaki egik cizgiyi
    # Paket G'nin ara katmani 301'ler; kalip egik cizgisiz.
    re_path(rf"^piyasa/(?P<slug>{piyasa_sayfa.ADRES_KALIBI})$",
            icerik_gorunum.piyasa_enstrumani, name="piyasa"),
    # Kunyedeki beyan sayfasi. Tek dilimli; kategori kalibindan ONCE.
    path("veri-kaynaklari", icerik_gorunum.veri_kaynaklari,
         name="veri-kaynaklari"),
    # Konu dosyalari (5 Eylul 2026). "konular" tek dilimli, kategori
    # kalibindan ONCE; "konu/<slug>" iki dilimli, haber kalibindan ONCE
    # (haber kalibi sondaki sayiyi kimlik sanir).
    path("konular", icerik_gorunum.konular, name="konular"),
    re_path(r"^konu/(?P<slug>[-\w]+)/?$", icerik_gorunum.konu, name="konu"),

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
