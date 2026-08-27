"""İçerik modelleri.

**Birincil anahtar = eski kimlik.** Adres deseni `/{kategori}/{slug}-{id}`
olduğu ve site kimlikle çözdüğü için, eski kimliği korumak adresleri doğal
olarak korur. Göçte `id` açıkça yazılır.

Görsel notu: 2023-07 öncesi görseller sağlayıcı tarafından sunucudan
silinmiş (296.207 haber, arşivin %53,2'si). Kazımayla da Wayback'ten de
kurtarılamıyor. `gorsel_url` yalnız **iz** olarak saklanır; dosya yoktur.
"""

from django.conf import settings
from django.db import models

from .temizle import govde_temizle
from .yetkiler import OZEL_IZINLER

from taksonomi.models import Etiket, Ilce, Kategori, Kaynak


class Haber(models.Model):
    DURUM_AKTIF, DURUM_PASIF, DURUM_SILINMIS, DURUM_ARSIV = 1, 2, 3, 4
    DURUMLAR = [
        (DURUM_AKTIF, "Aktif"), (DURUM_PASIF, "Pasif"),
        (DURUM_SILINMIS, "Silinmiş"), (DURUM_ARSIV, "Arşiv"),
    ]
    HAZIRLIK = [("taslak", "Taslak"), ("incelemede", "İncelemede"), ("hazir", "Yayına hazır")]

    # PANEL-NOTLARI.md §16: kaynak türü. "Kendi muhabirimiz" eski sistemde
    # kaynak listesinin içine karışmıştı; ayrı eksene alındı.
    KAYNAK_AJANS = "ajans"
    KAYNAK_DIS_YAYIN = "dis_yayin"
    KAYNAK_MUHABIR = "muhabir"
    KAYNAK_TURLERI = [
        (KAYNAK_AJANS, "Ajans"),
        (KAYNAK_DIS_YAYIN, "Dış yayın"),
        (KAYNAK_MUHABIR, "Kendi muhabirimiz"),
    ]

    # PANEL-NOTLARI.md §7: altı yasal değer. Eskiden serbest metindi ve
    # yıldızlı görünmesine rağmen boş kaydedilebiliyordu.
    META_YAZARLAR = [
        ("fikir_iscisi", "Fikir İşçisi"),
        ("bulten", "Bülten"),
        ("haber_ajansi", "Haber Ajansı"),
        ("haber_merkezi", "Haber Merkezi"),
        ("icerik_aktarimi", "İçerik Aktarımı"),
        ("alinti", "Alıntı/İktibas"),
    ]

    # Kaynak türünden türetim tablosu (§7).
    META_TURETIM = {
        KAYNAK_AJANS: "haber_ajansi",
        KAYNAK_DIS_YAYIN: "alinti",
        KAYNAK_MUHABIR: "fikir_iscisi",
    }

    id = models.BigIntegerField(primary_key=True, editable=False,
                                help_text="Eski sistemdeki kimlik. Adresin parçası.")
    slug = models.SlugField(max_length=220, editable=False)
    baslik = models.CharField(max_length=300)
    ikinci_baslik = models.CharField(
        max_length=300, blank=True,
        help_text="Panelde varsayılan kapalı, açılır alan.")
    spot = models.TextField(blank=True)
    govde = models.TextField(blank=True)

    kategori = models.ForeignKey(Kategori, on_delete=models.PROTECT, related_name="haberler")
    ilce = models.ForeignKey(Ilce, null=True, blank=True, on_delete=models.SET_NULL,
                             related_name="haberler")
    kaynaklar = models.ManyToManyField(Kaynak, blank=True, related_name="haberler")
    etiketler = models.ManyToManyField(Etiket, blank=True, related_name="haberler")

    # -- kaynak ve sorumluluk (PANEL-NOTLARI.md §5, §7) --
    kaynak_turu = models.CharField(max_length=12, choices=KAYNAK_TURLERI,
                                   default=KAYNAK_AJANS)
    muhabir = models.CharField(max_length=120, blank=True,
                               help_text="Kaynak türü 'Kendi muhabirimiz' ise doldurulur.")
    meta_yazar = models.CharField(
        max_length=20, choices=META_YAZARLAR, blank=True,
        help_text="Yasal sonuç doğurur. Kaynak türünden türetilir; "
                  "elle değiştirilirse türetim durur.")
    meta_yazar_elle = models.BooleanField(
        default=False,
        help_text="Editör meta yazar değerini elle seçtiyse doğru; türetim artık ezmez.")
    olusturan = models.ForeignKey(
        "auth.User", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="haberleri",
        help_text="Haberi giren kullanıcı. 'Kendi haberini yayınlama' yetkisi buna bakar.")

    durum = models.PositiveSmallIntegerField(choices=DURUMLAR, default=DURUM_AKTIF)
    hazirlik = models.CharField(max_length=12, choices=HAZIRLIK, blank=True)

    yayin_zamani = models.DateTimeField(null=True, blank=True, db_index=True)
    guncelleme_zamani = models.DateTimeField(null=True, blank=True)

    gorsel_url = models.URLField(max_length=600, blank=True,
                                 help_text="Uzak adres. 2023-07 öncesinde dosya SUNUCUDA YOK.")
    gorsel_alt = models.CharField(max_length=300, blank=True)
    gorsel_var = models.BooleanField(default=False, help_text="Yerelde dosya var mı.")
    gorsel_dosya = models.CharField(
        max_length=300, blank=True,
        help_text="Arşiv köküne göreli yol, ör. gorseller/2026-01/dosya.webp. "
                  "Sayfa bunu kullanır; gorsel_url yalnız izdir.")

    # -- manşet (PANEL-NOTLARI.md §4, alan 18-20 · §14) --
    manset_ana = models.BooleanField(default=False)
    manset_tepe = models.BooleanField(default=False)
    manset_kare = models.BooleanField(default=False)

    # -- seçenekler (alan 23-26) --
    rss = models.BooleanField(default=True)
    yorumlar_acik = models.BooleanField(default=True)
    yonlendirme_url = models.URLField(max_length=600, blank=True)
    gomulu_kod = models.TextField(blank=True)

    # -- SEO (alan 29-30) --
    odak_kelime = models.CharField(max_length=120, blank=True)
    seo_baslik = models.CharField(max_length=200, blank=True)

    # -- ilgili haberler (alan 28) --
    ilgili_haberler = models.ManyToManyField("self", blank=True, symmetrical=False,
                                             related_name="ilgili_olduklari")

    kelime_sayisi = models.PositiveIntegerField(default=0)
    eski_url = models.URLField(max_length=600, blank=True)
    goc_guveni = models.CharField(max_length=12, blank=True)

    class Meta:
        ordering = ["-yayin_zamani"]
        verbose_name = "haber"
        verbose_name_plural = "haberler"
        indexes = [
            models.Index(fields=["kategori", "-yayin_zamani"]),
            # Bugün ekranının kuyruğu bu iki alanla süzülüyor (§9).
            models.Index(fields=["durum", "hazirlik"]),
        ]
        # Rol matrisinin dayandığı özel izinler; ayrıntı icerik/yetkiler.py.
        permissions = OZEL_IZINLER

    def __str__(self) -> str:
        return f"[{self.id}] {self.baslik[:60]}"

    def meta_yazari_turet(self) -> str:
        """Kaynak türünden meta yazar değerini türetir (§7).

        Editör elle seçmişse (`meta_yazar_elle`) dokunulmaz — türetimin amacı
        kolaylık, dayatma değil.
        """
        if self.meta_yazar_elle and self.meta_yazar:
            return self.meta_yazar
        return self.META_TURETIM.get(self.kaynak_turu, "haber_merkezi")

    def save(self, *args, **kwargs):
        # Hazirlik bos gelirse Taslak sayilir (§9).
        if not self.hazirlik:
            self.hazirlik = "taslak"
        self.meta_yazar = self.meta_yazari_turet()
        super().save(*args, **kwargs)

    def masada_mi(self) -> bool:
        """Bugün ekranının kuyruğu: Pasif + (Taslak | İncelemede) — §9."""
        return self.durum == self.DURUM_PASIF and self.hazirlik in ("taslak", "incelemede")

    @classmethod
    def masadakiler(cls):
        return cls.objects.filter(durum=cls.DURUM_PASIF,
                                  hazirlik__in=("taslak", "incelemede"))

    @classmethod
    def yayindakiler(cls):
        """Sayfada gösterilebilir haberler.

        Göçte durum alanı eski sistemden birebir geldi; "Aktif" dışındakiler
        (Pasif · Silinmiş · Arşiv) yayına çıkmaz. Yayın zamanı olmayan kayıt
        da listelenmez — sıralama ona dayanıyor.
        """
        return cls.objects.filter(durum=cls.DURUM_AKTIF,
                                  yayin_zamani__isnull=False)

    def get_absolute_url(self) -> str:
        return f"/{self.kategori.slug_al()}/{self.slug}-{self.id}"

    def gorsel_yolu(self) -> str:
        """Sayfada basılacak görsel adresi — **yerel**, uzak değil.

        `gorsel_url` kaynak sunucudaki adresin izidir ve o dosyaların büyük
        bölümü silinmiştir (URUN-PLANI.md F3 notu); ayrıca sayfanın dışarıya
        bağlanmaması gerekiyor. Bu yüzden yalnızca yerelde dosyası olan
        haberler görsel gösterir.
        """
        if not (self.gorsel_var and self.gorsel_dosya):
            return ""
        return settings.ARSIV_GORSEL_URL + self.gorsel_dosya.split("gorseller/", 1)[-1]

    def govde_guvenli(self):
        """Şablonda basılacak hâli. Beyaz liste dışındaki HTML düşer.

        Ayrıntı ve ölçüm `icerik/temizle.py` içinde.
        """
        return govde_temizle(self.govde)
