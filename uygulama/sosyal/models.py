"""Sosyal medya paylaşımı — hesaplar ve gönderi kuyruğu.

Panel bir haberi yayına aldığında aynı haberi seçilen sosyal hesaplarda da
paylaşır. İki tablo var ve **ikisi de yeni**: `icerik_haber`e tek bir alan
bile eklenmedi. Gerekçe PANEL-NOTLARI.md §24'te ölçülü duruyor — o tabloda
`blank=True` taşıyan tek bir alan bile bir milyon satırı yeniden kurdurur.

## İki durum, tek kuyruk

Kuyruğa giren her satır bir **niyet**tir: "bu haber şu hesapta paylaşılacak".
Niyetin gerçekleşmesi iki yoldan olur:

    Anahtar tanımlı   → `saglayicilar` gönderir, dış kimlik geri yazılır
    Anahtar yok       → satır ELLE durumunda bekler; panel metni ve paylaş
                        bağlantısını hazır verir, editör kendi paylaşır

Bu ikilik bilinçli: gazetenin bugün API anahtarı yok ve aracın anahtar
gelene kadar hiçbir işe yaramaması kabul edilebilir değildi.

## Yayın eşiği kuyruğun içinde değil

Kuyruk satırı haber **taslakken de** açılabilir; gönderici haberin durumuna
bakar (`gonderilebilir_mi`). Böylece "yayına alınca paylaş" kararı toplu
işlemden de (akış ekranı) geçtiğinde çalışır: toplu fiil kuyruğa hiç
dokunmaz, satır zaten orada bekliyordur.
"""

import os

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.db.models import Q
from django.utils import timezone

from icerik.models import Haber


class SosyalHesap(models.Model):
    """Gazetenin bir sosyal medya hesabı ve o hesabın kimlik bilgileri.

    **Gizli bilgi iki yerden okunur.** Öncelik ortam değişkenindedir
    (`BH_SOSYAL_X_ERISIM_JETONU` gibi); yoksa `gizli_ayar` sözlüğüne
    bakılır. Panelde bu alanlar yazılır ama **geri gösterilmez** — form
    boş gelir, boş bırakılırsa kayıtlı değer korunur.
    """

    X = "x"
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    YOUTUBE = "youtube"
    PLATFORMLAR = [
        (X, "X (Twitter)"),
        (FACEBOOK, "Facebook sayfası"),
        (INSTAGRAM, "Instagram"),
        (YOUTUBE, "YouTube (özel video)"),
    ]

    platform = models.CharField(max_length=12, choices=PLATFORMLAR)
    ad = models.CharField(
        max_length=120,
        help_text="Panelde görünecek ad: “Bursa Hakimiyet — X”.")
    kullanici_adi = models.CharField(
        max_length=120, blank=True,
        help_text="@ işareti olmadan. Gönderi adresini kurmakta kullanılır.")
    aktif = models.BooleanField(default=True)
    varsayilan = models.BooleanField(
        default=True,
        help_text="Haber formunda kutusu önceden işaretli gelsin mi.")
    sira = models.PositiveSmallIntegerField(default=0)
    metin_kalibi = models.TextField(
        blank=True,
        help_text="Boşsa platformun kalıbı kullanılır. "
                  "Yer tutucular: {baslik} {spot} {adres} {etiketler}")
    gizli_ayar = models.JSONField(null=True, blank=True)
    son_gonderim = models.DateTimeField(null=True, blank=True)
    son_hata = models.CharField(max_length=300, blank=True)

    class Meta:
        ordering = ["sira", "platform", "ad"]
        verbose_name = "sosyal hesap"
        verbose_name_plural = "sosyal hesaplar"
        constraints = [
            # Aynı platformda aynı kullanıcı adı iki kez tanımlanırsa haber
            # iki kez paylaşılır. Boş kullanıcı adı kısıttan muaf.
            models.UniqueConstraint(
                fields=["platform", "kullanici_adi"],
                condition=~Q(kullanici_adi=""),
                name="sosyal_hesap_tekil"),
        ]

    def __str__(self) -> str:
        return f"{self.ad} ({self.get_platform_display()})"

    # -- sağlayıcı köprüsü -------------------------------------------------

    def saglayici(self):
        from .saglayicilar import saglayici_bul
        return saglayici_bul(self.platform)

    def gizli(self, alan: str) -> str:
        """Kimlik bilgisi — önce ortam değişkeni, sonra veritabanı.

        Ortam önceliği bilinçli: yayında anahtarları sunucunun ortamında
        tutmak, veritabanı yedeğine yazmaktan güvenlidir.
        """
        ortam = os.environ.get(
            f"BH_SOSYAL_{self.platform.upper()}_{alan.upper()}")
        if ortam:
            return ortam
        return str((self.gizli_ayar or {}).get(alan) or "")

    def eksik_alanlar(self) -> list:
        return self.saglayici().eksik_alanlar(self)

    def kimligi_tam_mi(self) -> bool:
        return not self.eksik_alanlar()

    @property
    def otomatik_olur(self) -> bool:
        """Haber yayına alınınca kendiliğinden paylaşılabilir mi.

        YouTube'da paylaşılan şey haberin kendisi değil, ayrıca çekilmiş
        **özel bir video**. Bu yüzden YouTube hesabı otomatik akışa girmez;
        kuyruğa yalnız "elle yüklenecek" notu olarak düşer.
        """
        return self.saglayici().otomatik_olur

    def hazirlik_notu(self) -> str:
        eksik = self.eksik_alanlar()
        if not eksik:
            return ""
        return ("Kimlik bilgisi eksik (" + ", ".join(eksik) +
                "); gönderiler ELLE paylaşım olarak kuyruğa düşer.")


class SosyalGonderi(models.Model):
    """Bir haberin bir hesapta paylaşılma niyeti ve sonucu."""

    BEKLIYOR = "bekliyor"
    GONDERILDI = "gonderildi"
    HATA = "hata"
    ELLE = "elle"
    IPTAL = "iptal"
    DURUMLAR = [
        (BEKLIYOR, "Bekliyor"),
        (GONDERILDI, "Gönderildi"),
        (HATA, "Hata"),
        (ELLE, "Elle paylaşılacak"),
        (IPTAL, "İptal"),
    ]
    # Kuyruktan çıkmış, artık gönderilmeyecek durumlar.
    KAPALI_DURUMLAR = (GONDERILDI, IPTAL)

    OTOMATIK, ELLE_ACILDI = "otomatik", "elle"
    KAYNAKLAR = [(OTOMATIK, "Yayınla birlikte"), (ELLE_ACILDI, "Elle açıldı")]

    haber = models.ForeignKey(Haber, on_delete=models.CASCADE,
                              related_name="sosyal_gonderiler")
    hesap = models.ForeignKey(SosyalHesap, on_delete=models.PROTECT,
                              related_name="gonderiler")
    metin = models.TextField(
        blank=True, help_text="Boşsa gönderim anında kalıptan üretilir.")
    gorsel_adres = models.URLField(max_length=600, blank=True)
    durum = models.CharField(max_length=12, choices=DURUMLAR, default=BEKLIYOR)
    kaynak = models.CharField(max_length=10, choices=KAYNAKLAR,
                              default=OTOMATIK)
    olusturan = models.ForeignKey(User, null=True, blank=True,
                                  on_delete=models.SET_NULL,
                                  related_name="sosyal_gonderileri")
    olusma_zamani = models.DateTimeField(default=timezone.now, db_index=True)
    gonderim_zamani = models.DateTimeField(null=True, blank=True)
    dis_kimlik = models.CharField(max_length=100, blank=True)
    dis_adres = models.URLField(max_length=600, blank=True)
    hata_metni = models.CharField(max_length=500, blank=True)
    deneme = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["-olusma_zamani", "-id"]
        verbose_name = "sosyal gönderi"
        verbose_name_plural = "sosyal gönderiler"
        indexes = [
            models.Index(fields=["durum", "olusma_zamani"]),
            models.Index(fields=["haber", "hesap"]),
        ]
        constraints = [
            # Aynı haber aynı hesapta iki kez GÖNDERİLMİŞ olamaz. Kısıt
            # yalnız başarılı gönderimi kilitler: hatalı satır yeniden
            # denenebilsin, elle paylaşım ayrıca kaydedilebilsin diye.
            models.UniqueConstraint(
                fields=["haber", "hesap"],
                condition=Q(durum="gonderildi"),
                name="sosyal_tek_gonderim"),
        ]

    def __str__(self) -> str:
        return f"{self.hesap.ad} ← [{self.haber_id}]"

    # -- durum soruları ----------------------------------------------------

    def haber_yayinda_mi(self) -> bool:
        return (self.haber.durum == Haber.DURUM_AKTIF
                and self.haber.yayin_zamani is not None
                and self.haber.yayin_zamani <= timezone.now())

    def gonderilebilir_mi(self) -> bool:
        """Gönderici bu satırı şimdi işleyebilir mi.

        Haber henüz yayında değilse satır kuyrukta **kalır**; bu bir hata
        değildir. Kuyruğa taslakken girilmesi bilinçli (modül notu).
        """
        return (self.durum in (self.BEKLIYOR, self.HATA)
                and self.hesap.aktif
                and self.hesap.otomatik_olur
                and self.hesap.kimligi_tam_mi()
                and self.haber_yayinda_mi())

    def haber_adresi(self) -> str:
        """Platformun UTM'siyle (Paket G) — Facebook `link` alanı da bunu alır."""
        from .metin import haber_adresi
        return haber_adresi(self.haber, self.hesap.platform)

    def durum_sinifi(self) -> str:
        """Panelin mevcut rozet sınıflarına eşleme — yeni CSS açılmadı."""
        return {
            self.BEKLIYOR: "incelemede",
            self.GONDERILDI: "hazir",
            self.HATA: "silinmis",
            self.ELLE: "taslak",
            self.IPTAL: "arsiv",
        }.get(self.durum, "")

    @classmethod
    def bekleyenler(cls):
        return cls.objects.filter(durum__in=(cls.BEKLIYOR, cls.HATA))
