"""Taksonomi — kategori, ilçe, etiket, kaynak ve yönlendirme.

Adres sözleşmesinin taşıyıcısı burasıdır. Ölçülmüş gerçekler:

- Haber adresi `/{kategori-slug}/{slug}-{id}`; canlı sitedeki 556.824 adresin
  %100'ü bu desende.
- Site adresi **kimlikle** çözüyor, slug'ı yok sayıp kanonik adrese
  yönlendiriyor. Yeni sistem de aynı davranışı kurar.
- Kategori kimliği türe göre kayıyor: foto = haber_id + 200, video = +300.
  19/19 örnekte doğrulandı.
- Aynı kategorinin slug'ı türe göre farklı olabiliyor: haberde `bursa-da-spor`
  (id 50), videoda `bursada-spor` (id 350). Bu yüzden slug kategoride değil,
  **tür satırında** saklanır.
"""

from django.db import models


class Kategori(models.Model):
    """Konu ekseni. İlçeden ve içerik türünden bağımsızdır."""

    TUR_HABER = "haber"
    TUR_FOTO = "foto"
    TUR_VIDEO = "video"

    ad = models.CharField(max_length=80, unique=True)
    sira = models.PositiveSmallIntegerField(default=0)
    ust = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.PROTECT,
        related_name="altlar",
    )
    aktif = models.BooleanField(default=True)

    class Meta:
        ordering = ["sira", "ad"]
        verbose_name = "kategori"
        verbose_name_plural = "kategoriler"

    def __str__(self) -> str:
        return self.ad

    def slug_al(self, tur: str = TUR_HABER) -> str:
        """Kategorinin bu türdeki slug'ı.

        `.filter()` yerine `.all()` üzerinden dönülüyor: sayfada onlarca
        haber varken her biri adresini buradan kuruyor ve `.filter()`
        prefetch önbelleğini atlayıp her çağrıda veritabanına gidiyordu.
        """
        for satir in self.turler.all():
            if satir.tur == tur:
                return satir.slug
        return ""


class KategoriTur(models.Model):
    """Bir kategorinin belirli bir içerik türündeki slug'ı ve eski kimliği.

    Eski sistemde her tür kategoriyi ayrı kayıtta tutuyordu (37 kayıt, 15 ad).
    Kararı: adlar birleşti, **slug'lar donduruldu**. Slug bu tabloda durur ve
    değiştirilemez — adresin parçasıdır.
    """

    TURLER = [
        (Kategori.TUR_HABER, "Haber"),
        (Kategori.TUR_FOTO, "Foto galeri"),
        (Kategori.TUR_VIDEO, "Video"),
    ]

    kategori = models.ForeignKey(Kategori, on_delete=models.PROTECT, related_name="turler")
    tur = models.CharField(max_length=8, choices=TURLER)
    eski_id = models.PositiveIntegerField(
        help_text="Eski sistemdeki kategori kimliği. Foto/video adresinde geçer.",
    )
    slug = models.SlugField(
        max_length=80,
        help_text="DONDURULMUŞ. Adresin parçası; değiştirmek eski bağlantıları kırar.",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["tur", "slug"], name="tur_slug_tekil"),
            models.UniqueConstraint(fields=["tur", "eski_id"], name="tur_eskiid_tekil"),
            models.UniqueConstraint(fields=["kategori", "tur"], name="kategori_tur_tekil"),
        ]
        ordering = ["kategori__sira", "tur"]
        verbose_name = "kategori türü"
        verbose_name_plural = "kategori türleri"

    def __str__(self) -> str:
        return f"{self.kategori.ad} ({self.get_tur_display()}) /{self.slug}/"

    @property
    def adres_dilimi(self) -> str:
        """Foto ve video adresindeki `{slug}-{katid}` parçası."""
        return f"{self.slug}-{self.eski_id}"


class Ilce(models.Model):
    """Yer ekseni. Kategoriden ayrıdır: kategori konuyu, ilçe yeri söyler."""

    ad = models.CharField(max_length=40, unique=True)
    slug = models.SlugField(max_length=40, unique=True)
    sira = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["sira", "ad"]
        verbose_name = "ilçe"
        verbose_name_plural = "ilçeler"

    def __str__(self) -> str:
        return self.ad


class Etiket(models.Model):
    ad = models.CharField(max_length=60, unique=True)
    slug = models.SlugField(max_length=60, unique=True)

    class Meta:
        ordering = ["ad"]
        verbose_name = "etiket"
        verbose_name_plural = "etiketler"

    def __str__(self) -> str:
        return self.ad


class Kaynak(models.Model):
    """Haberin geldiği yer.

    Eski sistemde 348 kayıt vardı: 6 birebir tekrar, 7 birleşik kayıt
    (`İHA, DHA` gibi) ve muhabir adlarıyla yayın adları aynı listede karışıktı.
    Sebep, alanın çoklu seçime izin vermemesiydi.

    Çözüm: kaynak çoklu seçilir, **muhabir ayrı alandır** (içerik tarafında
    kullanıcıya bağlanır), tekrarlar `birlesti_ile` ile kapatılır.
    """

    TUR_AJANS = "ajans"
    TUR_DIS_YAYIN = "dis_yayin"
    TURLER = [(TUR_AJANS, "Ajans"), (TUR_DIS_YAYIN, "Dış yayın")]

    ad = models.CharField(max_length=120, unique=True)
    tur = models.CharField(max_length=12, choices=TURLER, default=TUR_DIS_YAYIN)
    aktif = models.BooleanField(default=True)
    birlesti_ile = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="birlesenler",
        help_text="Tekrar eden kayıt buraya bağlanır; bağlantı kaybolmaz.",
    )

    class Meta:
        ordering = ["ad"]
        verbose_name = "kaynak"
        verbose_name_plural = "kaynaklar"

    def __str__(self) -> str:
        return self.ad


class Yonlendirme(models.Model):
    """Eski adresi yeni adrese bağlar.

    Kimlikle çözüm çoğu durumu kendiliğinden kurtarır; bu tablo onun
    yetmediği yerler içindir (slug göçü, birleşen kategori, elle taşıma).
    """

    eski_yol = models.CharField(max_length=400, unique=True, db_index=True)
    yeni_yol = models.CharField(max_length=400)
    kod = models.PositiveSmallIntegerField(default=301)
    sebep = models.CharField(max_length=200, blank=True)
    olusturma = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["eski_yol"]
        verbose_name = "yönlendirme"
        verbose_name_plural = "yönlendirmeler"

    def __str__(self) -> str:
        return f"{self.eski_yol} → {self.yeni_yol} ({self.kod})"
