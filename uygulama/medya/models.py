"""Medya modelleri — yazar · köşe yazısı · foto galeri · video.

`icerik.Haber` ile aynı sözleşmeye uyar, çünkü aynı adres kuralına tabidirler:

    /yazarlar/{yazar-slug}-{yazar_id}/{slug}-{id}   köşe yazısı
    /yazarlar/{yazar-slug}-{yazar_id}               yazar
    /galeriler/{kategori-slug}-{katid}/{slug}-{id}  foto galeri
    /videolar/{kategori-slug}-{katid}/{slug}-{id}   video

**Birincil anahtar = eski kimlik.** Kimlik adresin parçasıdır ve site adresi
kimlikten çözer; kimliği değiştirmek 599.793 eski bağlantının bir kısmını
sessizce kırardı. Bu yüzden `id` göçte açıkça yazılır, otomatik üretilmez.

**Slug adresten çıkarılır, başlıktan üretilmez.** Aynı gerekçe: adres kanonik
kaynaktır, başlık değil. Başlıktan slug üretmek Türkçe harf dönüşümü yüzünden
kayıtların bir bölümünü kaydırırdı.

Ölçülmüş üç gerçek bu dosyanın biçimini belirledi (27 Ağustos 2026):

1. **`haber-213` diye bir foto kategorisi var ve taksonomide karşılığı yok.**
   Taranan 3.660 galerinin 998'i (%27) bu dilimde. Kategori kimliği tanınmıyor
   diye kaydı düşürmek arşivin dörtte birini ve o adreslerin hepsini yok
   ederdi. Karar: `kategori` bağı **boş bırakılabilir**, ham dilim
   (`kategori_dilimi`) her kayıtta **birebir** saklanır ve adres ondan kurulur.
2. **Galeri ve yazar görsellerinin %100'ü indirilebiliyor.** Haber tarafında
   yerel görsel oranı %0,02 idi (dosyalar sunucudan silinmiş); medya ailelerinde
   kapak `/cdn/` altından geliyor ve duruyor. Yani bu modellerde görsel istisna
   değil kural — şablon önce yerel dosyayı dener.
3. **Galeri kareleri statik HTML'de yok** (arşivleyicinin ölçümü): sayfadaki tek
   `ItemList` sitenin "son galeriler" kutusu. Bu yüzden `kareler_eksik` alanı
   var ve varsayılanı **doğru**; kareler ancak sağlayıcı dökümünden ya da
   panelden gelir. Eksikliği kaydın içinde taşımak, sonradan "neden boş?"
   sorusunu ölçüyle cevaplar.
"""

from django.conf import settings
from django.db import models

from taksonomi.models import Kategori, KategoriTur

# Arşiv görsellerinin adres öneki.
#
# `icerik.Haber` görselini `settings.ARSIV_GORSEL_URL` (= /arsiv-gorsel/)
# altından servis eder ve o adres `<arşiv kökü>/gorseller/` klasörüne bakar.
# Medya aileleri **kardeş klasörlere** yazıyor: `gorseller-galeri/`,
# `gorseller-video/`, `gorseller-yazar/`, `gorseller-kose/`. Bunlar
# `/arsiv-gorsel/` kökünün altında değil, yanındadır; o yüzden kendi önekleri
# var. `gorsel_dosya` da bu yüzden **arşiv köküne** göreli saklanır (arşivin
# JSON'a yazdığı hâliyle birebir), `gorseller/` köküne değil.
MEDYA_GORSEL_URL = getattr(settings, "MEDYA_GORSEL_URL", "/arsiv-medya/")


class ArsivIcerigi(models.Model):
    """Dört ailenin ortak gövdesi. Alanlar `icerik.Haber` ile birebir aynı adı
    taşır ki panel formları ve şablon parçaları tek bir sözleşmeyle çalışsın."""

    DURUM_AKTIF, DURUM_PASIF, DURUM_SILINMIS, DURUM_ARSIV = 1, 2, 3, 4
    DURUMLAR = [
        (DURUM_AKTIF, "Aktif"), (DURUM_PASIF, "Pasif"),
        (DURUM_SILINMIS, "Silinmiş"), (DURUM_ARSIV, "Arşiv"),
    ]

    id = models.BigIntegerField(
        primary_key=True, editable=False,
        help_text="Eski sistemdeki kimlik. Adresin parçası; değiştirilemez.")
    slug = models.SlugField(
        max_length=220, editable=False,
        help_text="DONDURULMUŞ. Eski adresten çıkarıldı, başlıktan üretilmedi.")
    baslik = models.CharField(max_length=300)
    spot = models.TextField(blank=True)

    durum = models.PositiveSmallIntegerField(choices=DURUMLAR, default=DURUM_AKTIF)
    yayin_zamani = models.DateTimeField(null=True, blank=True, db_index=True)
    guncelleme_zamani = models.DateTimeField(null=True, blank=True)

    gorsel_url = models.URLField(
        max_length=600, blank=True,
        help_text="Kaynaktaki adres. Yalnız izdir; sayfa uzağa bağlanmaz.")
    gorsel_alt = models.CharField(max_length=300, blank=True)
    gorsel_var = models.BooleanField(default=False, help_text="Yerelde dosya var mı.")
    gorsel_dosya = models.CharField(
        max_length=300, blank=True,
        help_text="ARŞİV KÖKÜNE göreli yol, ör. gorseller-galeri/2021-02/x.webp.")

    eski_url = models.URLField(max_length=600, blank=True)
    goc_guveni = models.CharField(max_length=12, blank=True)

    class Meta:
        abstract = True

    def __str__(self) -> str:
        return f"[{self.pk}] {self.baslik[:60]}"

    @classmethod
    def yayindakiler(cls):
        """Sayfada gösterilebilir kayıtlar.

        Sitemap yalnız yayındakileri listeliyor, yani göç eden her kayıt
        Aktif geliyor; süzgeç panelden gelecek içerik için duruyor. Yayın
        zamanı olmayan kayıt listelenmez — sıralama ona dayanıyor.
        """
        return cls.objects.filter(durum=cls.DURUM_AKTIF, yayin_zamani__isnull=False)

    def gorsel_yolu(self) -> str:
        """Sayfada basılacak görsel adresi — **yerel**, uzak değil.

        Sayfanın internetsiz açılması kuralı burada da geçerli: dosya yereldeyse
        gösterilir, değilse boş döner ve şablon kategori temsilî çizimine düşer.
        """
        if not (self.gorsel_var and self.gorsel_dosya):
            return ""
        return MEDYA_GORSEL_URL + self.gorsel_dosya.lstrip("/")


class KategoriliIcerik(ArsivIcerigi):
    """Adres diliminin kategoriden geldiği aileler: foto galeri ve video.

    `TUR` alt sınıfta doldurulur; `KategoriTur` satırı ondan bulunur.
    """

    TUR = ""  # alt sınıf Kategori.TUR_FOTO / TUR_VIDEO ile doldurur

    kategori = models.ForeignKey(
        Kategori, null=True, blank=True, on_delete=models.PROTECT,
        related_name="+",
        help_text="Taksonomide karşılığı yoksa boş kalır; adres yine çalışır.")
    kategori_dilimi = models.CharField(
        max_length=120,
        help_text="Adresteki `{slug}-{katid}` parçası, kaynaktan BİREBİR. "
                  "Taksonomi tanımayan dilimler (ör. haber-213) buradan yaşar.")

    class Meta:
        abstract = True

    def adres_dilimi(self) -> str:
        """Adreste geçecek `{slug}-{katid}`.

        Taksonomi kategoriyi tanıyorsa **kanonik** dilim oradan gelir; sapan
        slug'lar (ölçüldü: `bursada-spor-250`) böylece kendiliğinden kanoniğe
        çekilir. Tanımıyorsa kaynaktaki ham dilim kullanılır.

        `.filter()` değil `.all()` üzerinden dönülüyor: liste sayfasında onlarca
        kayıt adresini buradan kuruyor ve `.filter()` prefetch önbelleğini
        atlayıp her çağrıda veritabanına giderdi (`Kategori.slug_al` ile aynı
        gerekçe).
        """
        if self.kategori_id:
            for satir in self.kategori.turler.all():
                if satir.tur == self.TUR:
                    return satir.adres_dilimi
        return self.kategori_dilimi

    @classmethod
    def kategori_bul(cls, kategori_id: int):
        """Adres dilimindeki kimlikten `Kategori` bulur. Yoksa None."""
        satir = KategoriTur.objects.filter(tur=cls.TUR, eski_id=kategori_id).first()
        return satir.kategori if satir else None


class Yazar(models.Model):
    """Köşe yazarı.

    Kimlik yine adresin parçası (`/yazarlar/{slug}-{id}`), o yüzden birincil
    anahtar eski kimliktir.

    **Eksik kayıt sorunu — ölçüldü, sanılandan büyük.** Sitemap yalnız **18**
    yazar sayfası listeliyor ve biri 404 (17 alınabildi); ama köşe yazılarının
    adreslerinde **37 ayrı yazar kimliği** geçiyor (27 Ağustos 2026, 5.755
    yazı taranmışken). Yani yazarların yarısından fazlasının sayfası yok, köşe
    yazıları var. Bağlanacak kayıt bulunamayınca yazının düşmesi 6.903 adresin
    büyük bölümünü yok ederdi.

    Karar: göç, adresteki dilimden (`namik-goz-76`) ve yazının künyesinden
    geçici bir yazar kaydı açar, `sayfasi_tarandi` alanını yanlış bırakır.
    Portre de yazıdan gelir — köşe sayfasının og:image'ı yazının değil
    **yazarın** fotoğrafıdır. Yazar sayfası sonradan taranırsa aynı kayıt
    künyesiyle tamamlanır; taranamazsa sayfa yine de eksiksiz görünür.
    """

    id = models.BigIntegerField(
        primary_key=True, editable=False,
        help_text="Eski sistemdeki yazar kimliği. Adresin parçası.")
    slug = models.SlugField(
        max_length=120, editable=False,
        help_text="DONDURULMUŞ. Eski adresten çıkarıldı.")
    ad = models.CharField(max_length=120)
    unvan = models.CharField(max_length=120, blank=True)
    ozgecmis = models.TextField(blank=True)
    eposta = models.EmailField(blank=True)

    aktif = models.BooleanField(
        default=True,
        help_text="Yalnız LİSTELERİ süzer. Pasif yazarın sayfası yine açılır; "
                  "eski bağlantılar 404 olmamalı.")
    sira = models.PositiveSmallIntegerField(default=0)
    sayfasi_tarandi = models.BooleanField(
        default=False,
        help_text="Yazar sayfası arşivden alındı mı. Yanlışsa kayıt köşe "
                  "yazısından türetilmiş geçici kayıttır.")

    gorsel_url = models.URLField(max_length=600, blank=True)
    gorsel_var = models.BooleanField(default=False)
    gorsel_dosya = models.CharField(max_length=300, blank=True)

    eski_url = models.URLField(max_length=600, blank=True)

    class Meta:
        ordering = ["sira", "ad"]
        verbose_name = "yazar"
        verbose_name_plural = "yazarlar"

    def __str__(self) -> str:
        return f"[{self.pk}] {self.ad}"

    @classmethod
    def listedekiler(cls):
        return cls.objects.filter(aktif=True)

    def get_absolute_url(self) -> str:
        return f"/yazarlar/{self.slug}-{self.pk}"

    @property
    def yol(self) -> str:
        """Anasayfadaki `parca` şablonları `y.yol` bekliyor; aynı adres."""
        return self.get_absolute_url()

    @property
    def adres_dilimi(self) -> str:
        return f"{self.slug}-{self.pk}"

    @property
    def basharfler(self) -> str:
        """Portresi olmayan yazar için vesika yerine baş harfler basılır.

        Türkçe büyük harf dönüşümü `str.upper()` ile yanlış çıkıyor
        ("ismail" → "ISMAIL"), o yüzden i/ı çifti elle çevriliyor —
        `site_etiket.buyult` ile aynı gerekçe.
        """
        harfler = [k[0] for k in self.ad.split() if k]
        cikti = "".join(harfler[:2])
        return "".join({"i": "İ", "ı": "I"}.get(h, h) for h in cikti).upper()

    def gorsel_yolu(self) -> str:
        if not (self.gorsel_var and self.gorsel_dosya):
            return ""
        return MEDYA_GORSEL_URL + self.gorsel_dosya.lstrip("/")

    def yazilari(self):
        return KoseYazisi.yayindakiler().filter(yazar=self)

    @property
    def son_yazi(self) -> str:
        """Sağ raydaki yazar kutusu yazar adının altında son yazının başlığını
        gösteriyor (URUN-PLANI.md §1, bileşen 13)."""
        yazi = self.yazilari().only("baslik").first()
        return yazi.baslik if yazi else ""


class KoseYazisi(ArsivIcerigi):
    """Köşe yazısı. Adresi **yazarın** dilimine bağlıdır.

    Yazar bağı zorunlu (`PROTECT`): bağ olmadan kanonik adres kurulamaz, yani
    bağsız kayıt adressiz kayıt demektir.

    `kategori` isteğe bağlıdır. Kaynakta köşe yazısının kategorisi ayrı bir
    adres dilimi değil, JSON-LD'deki `articleSection` alanıdır (ölçüldü: 3.000
    haber örneğinde değerler kategori adlarıyla birebir eşleşiyor); tanınmayan
    değer kaydı düşürmez.
    """

    yazar = models.ForeignKey(Yazar, on_delete=models.PROTECT, related_name="tum_yazilari")
    kategori = models.ForeignKey(
        Kategori, null=True, blank=True, on_delete=models.PROTECT, related_name="+")
    govde = models.TextField(blank=True)
    kelime_sayisi = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-yayin_zamani"]
        verbose_name = "köşe yazısı"
        verbose_name_plural = "köşe yazıları"
        indexes = [models.Index(fields=["yazar", "-yayin_zamani"])]

    def get_absolute_url(self) -> str:
        return f"/yazarlar/{self.yazar.adres_dilimi}/{self.slug}-{self.pk}"

    def govde_guvenli(self):
        """Şablonda basılacak hâli. Beyaz liste dışındaki HTML düşer.

        Gövde kazımayla geldi ve panelden de HTML girilecek; temizleyici
        `icerik.temizle` ile ortaktır — iki ayrı beyaz liste iki ayrı açık
        demek olurdu.
        """
        from icerik.temizle import govde_temizle
        return govde_temizle(self.govde)


class FotoGaleri(KategoriliIcerik):
    """Foto galeri.

    `kareler_eksik` varsayılanı **doğru**: arşivleyici ölçtü, kareler statik
    HTML'de yok ve sayfada bir ajax ucu bulunamadı. Kapak alınabiliyor.
    """

    TUR = Kategori.TUR_FOTO

    kareler_eksik = models.BooleanField(
        default=True,
        help_text="Kareler kaynaktan alınamadıysa doğru. Sayfa bunu okura söyler.")
    kareler_notu = models.CharField(max_length=300, blank=True)

    class Meta:
        ordering = ["-yayin_zamani"]
        verbose_name = "foto galeri"
        verbose_name_plural = "foto galeriler"
        indexes = [models.Index(fields=["kategori", "-yayin_zamani"])]

    def get_absolute_url(self) -> str:
        return f"/galeriler/{self.adres_dilimi()}/{self.slug}-{self.pk}"

    @property
    def kare_sayisi(self) -> int:
        return self.kareler.count()


class GaleriKaresi(models.Model):
    """Galerinin tek fotoğrafı.

    Göçte boş kalır (kareler kaynaktan alınamıyor); panelin Foto Galeri
    ekranı buraya yazacak. Kimliği eski sistemden gelmiyor, bu yüzden burada
    birincil anahtar **otomatiktir** — kare adresin parçası değil.
    """

    galeri = models.ForeignKey(FotoGaleri, on_delete=models.CASCADE, related_name="kareler")
    sira = models.PositiveSmallIntegerField(default=0)
    dosya = models.CharField(max_length=300, help_text="Arşiv köküne göreli yol.")
    alt = models.CharField(max_length=300, blank=True)
    aciklama = models.TextField(blank=True)

    class Meta:
        ordering = ["sira", "id"]
        verbose_name = "galeri karesi"
        verbose_name_plural = "galeri kareleri"

    def __str__(self) -> str:
        return f"{self.galeri_id}/{self.sira}"

    def gorsel_yolu(self) -> str:
        return MEDYA_GORSEL_URL + self.dosya.lstrip("/") if self.dosya else ""


class Video(KategoriliIcerik):
    """Video.

    İki adres saklanır ama **eşit değiller** (ölçüldü, 312 kayıt): JSON-LD
    `contentUrl` bir medya dosyası değil, **sayfanın kendi adresi**; gerçek
    oynatıcı `embedUrl`de duruyor (`bursahakimiyet.web.tv/embed/...`). İkisi
    de saklanıyor çünkü `contentUrl` ileride düzelirse iz gerekli, ama
    bağlantı `oynatma_adresi` üzerinden kuruluyor.

    Kaynak `embedUrl` alanına bazen komple `<iframe>` HTML'i koyuyor;
    arşivleyici `src`yi ayıklıyor, biz ham HTML saklamıyoruz.

    Sayfa videoyu **kendiliğinden gömmez**: gömülü çerçeve dış adrese bağlanır
    ve bu, sayfanın internetsiz açılması kuralına aykırıdır. Şablon kapak
    görselini ve kaynağa giden açık bir bağlantıyı gösterir; gömme kararı
    ayrı bir iştir.
    """

    TUR = Kategori.TUR_VIDEO

    video_url = models.URLField(max_length=600, blank=True)
    gomulu_url = models.URLField(max_length=600, blank=True)
    sure = models.CharField(
        max_length=40, blank=True,
        help_text="Kaynaktaki hâli (ISO 8601, ör. PT2M30S). İz olarak durur.")
    sure_saniye = models.PositiveIntegerField(
        default=0, help_text="Gösterim ve sıralama için çözülmüş hâli.")

    class Meta:
        ordering = ["-yayin_zamani"]
        verbose_name = "video"
        verbose_name_plural = "videolar"
        indexes = [models.Index(fields=["kategori", "-yayin_zamani"])]

    def get_absolute_url(self) -> str:
        return f"/videolar/{self.adres_dilimi()}/{self.slug}-{self.pk}"

    @property
    def oynatma_adresi(self) -> str:
        """Videoyu açacak dış adres; yoksa boş.

        Kendi adresine dönen bağlantı hiç basılmaz: okuru zaten bulunduğu
        sayfaya yollamak kırık bağlantıdan beterdir. Ölçüm bunun kural
        olduğunu gösterdi — `video_url` 312 kaydın hepsinde sayfanın kendisi.
        """
        for aday in (self.gomulu_url, self.video_url):
            if aday and not aday.rstrip("/").endswith(self.get_absolute_url()):
                return aday
        return ""

    @property
    def sure_yazi(self) -> str:
        """"2:05" · "1:02:05". Süresi bilinmeyen videoda boş döner ki şablon
        uydurma bir değer basmasın."""
        if not self.sure_saniye:
            return ""
        saat, kalan = divmod(self.sure_saniye, 3600)
        dakika, saniye = divmod(kalan, 60)
        if saat:
            return f"{saat}:{dakika:02d}:{saniye:02d}"
        return f"{dakika}:{saniye:02d}"
