"""İçerik modelleri.

**Birincil anahtar = eski kimlik.** Adres deseni `/{kategori}/{slug}-{id}`
olduğu ve site kimlikle çözdüğü için, eski kimliği korumak adresleri doğal
olarak korur. Göçte `id` açıkça yazılır.

Görsel notu: 2023-07 öncesi görseller sağlayıcı tarafından sunucudan
silinmiş (296.207 haber, arşivin %53,2'si). Kazımayla da Wayback'ten de
kurtarılamıyor. `gorsel_url` yalnız **iz** olarak saklanır; dosya yoktur.
"""

from collections import Counter

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone

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
    kaynak_turu = models.CharField(
        max_length=12, choices=KAYNAK_TURLERI, blank=True, default="",
        help_text="Boş = ölçülemedi. Arşivden gelen 337 bin haberin kaynak türü "
                  "kayıtlarda yoktu; varsayılan 'Ajans' bunu uydurmuş oluyordu.")
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

    # -- bağlı galeriler (PANEL-NOTLARI.md §4, alan 27) --
    #
    # Mevcut panelde `galleriesSelect2` → `galleries`. Bizde eksikti.
    # Seçici `ilgili_haberler`le AYNI deseni kullanır (`SecilenlerWidget`):
    # 4.040 galeriyi `<option>` diye basmak, düzelttiğimiz 356 bin seçenek
    # hatasının küçük ölçekte tekrarı olurdu.
    bagli_galeriler = models.ManyToManyField(
        "medya.FotoGaleri", blank=True, related_name="bagli_haberler",
        help_text="Habere iliştirilen foto galeriler.")

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
            # İlçe sayfası. Göç ajanının ölçümü: `ANALYZE` sonrası sorgu
            # 745 → 26 ms'ye indi ama sorgu planında `USE TEMP B-TREE FOR
            # ORDER BY` kalıntısı duruyordu; bu indeks onu kaldırıyor.
            # 20.366 haberin ilçesi dolu (17 ilçenin hiçbiri boş değil).
            models.Index(fields=["ilce", "-yayin_zamani"]),
            # Panel akış süzgeçleri — 29 Ağustos 2026 ölçümü.
            #
            # Django'nun otomatik tek sütunlu yabancı anahtar indeksleri bu
            # iki süzgece yetmiyordu, çünkü sorgu ikinci bir koşul taşıyor
            # (`durum != Silinmiş`) ve satırlar tabloya gidilerek okunuyordu:
            #
            #     kategori = 1   501 ms  (indeksi buluyor, satırları okuyor)
            #     editör   = 1 1.014 ms  (indeksi HİÇ kullanmıyor, tam tarama)
            #
            # `olusturan` alanı arşivden gelen 486.667 kaydın tamamında BOŞ;
            # `ANALYZE` istatistikleri "bu sütunun tek değeri var" dediği için
            # planlayıcı indeksi seçici bulmayıp taramaya dönüyordu — projenin
            # üçüncü tuzağının (§ bayat istatistik) aynısı.
            #
            # Durumu indekse katmak ikisini de KAPSAYAN indekse çeviriyor,
            # yani sayım tabloya hiç gitmiyor: kategori 501 → 8 ms.
            # Bedeli ölçüldü: kategori indeksi 4,9 MB.
            models.Index(fields=["kategori", "durum"]),
            models.Index(fields=["olusturan", "durum"]),
            # Manşet ekranı — KISMİ indeksler (28 Ağustos 2026).
            #
            # Ölçüldü: manşet alanlarında indeks yoktu ve `Q(ana|tepe|kare)`
            # 356.839 satırı tam tarıyordu (752 ms). Ekran altı böyle sorgu
            # çalıştırıyordu; küme çekimiyle üçe indi ama tarama kalmıştı.
            #
            # `condition` ile indeks YALNIZ işaretli satırları taşır. Manşetli
            # kayıt doğası gereği azdır (anasayfada üç slot), yani indeksler
            # küçücük. Yedek kopyada ölçülen kazanç: 752 ms → 0,1 ms
            # (MULTI-INDEX OR), kurma maliyeti 4 indeks + ANALYZE = 3,32 sn.
            models.Index(fields=["manset_ana"], condition=Q(manset_ana=True),
                         name="haber_manset_ana_kismi"),
            models.Index(fields=["manset_tepe"], condition=Q(manset_tepe=True),
                         name="haber_manset_tepe_kismi"),
            models.Index(fields=["manset_kare"], condition=Q(manset_kare=True),
                         name="haber_manset_kare_kismi"),
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
        if not self.kaynak_turu:
            # Kaynak türü ölçülemediyse türetilecek bir şey yok. Arşivden
            # ÖLÇÜLMÜŞ değer (haber_merkezi 336.547 · bulten 545) burada
            # korunur; ezilirse §25'te kurtarılan bilgi geri kaybolur.
            return self.meta_yazar or "haber_merkezi"
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


# ===========================================================================
# Model turu — PANEL-NOTLARI.md §24
#
# Dokuz model, §24.11'deki sırayla. Hepsi **yeni tablo**; hiçbiri
# `icerik_haber`e alan eklemiyor. Ö2'de ölçülen kural bunu zorunlu kıldı:
# `blank=True` ya da `default=` taşıyan tek bir alan bile 356 bin satırlık
# tabloyu yeniden kurdurur (~34 sn + tablo kopyası). Yeni tabloda bu kural
# geçerli değil — tablo boş doğuyor, varsayılan serbestçe kullanılabilir.
#
# Ertelenen ikisi (Duyurular · Kendi Yayınlarım) burada YOK: §24.6 ve §24.7,
# koordinatör kararı 28 Ağustos 2026. Kapsamdan çıkarılmadılar, sıraları
# değişti.
# ===========================================================================


class Yorum(models.Model):
    """Okur yorumu — §24.1.

    **İçerik bağı FK değil, `icerik_turu` + `icerik_id` çifti.** Yorum dört
    aileye (haber · köşe · galeri · video) bağlanabiliyor ve Django'da tek FK
    dört modele bağlanmaz. `ContentType` genel bağı yerine bu seçildi: mevcut
    panelin alanı zaten bu ("İçerik ID" + "Sayfa Tipi"), göç verisi bu
    biçimde gelecek ve genel bağın referans bütünlüğü de yok.

    Durum enum'u **üç değerli**, dört değil: dökümde ölçüldü, Yorumlar
    ekranının süzgeci Aktif · Pasif · Silinmiş gösteriyor, *Arşiv* yok (§9).
    """

    DURUM_AKTIF, DURUM_PASIF, DURUM_SILINMIS = 1, 2, 3
    DURUMLAR = [(DURUM_AKTIF, "Aktif"), (DURUM_PASIF, "Pasif"),
                (DURUM_SILINMIS, "Silinmiş")]

    TUR_HABER, TUR_KOSE, TUR_GALERI, TUR_VIDEO = "haber", "kose", "galeri", "video"
    TURLER = [(TUR_HABER, "Haber"), (TUR_KOSE, "Köşe yazısı"),
              (TUR_GALERI, "Foto galeri"), (TUR_VIDEO, "Video")]

    icerik_turu = models.CharField(max_length=8, choices=TURLER, default=TUR_HABER)
    icerik_id = models.BigIntegerField(
        help_text="Yorumlanan kaydın kimliği. FK değil: dört aileye bağlanır.")
    okur_adi = models.CharField(max_length=120)
    metin = models.TextField()
    ip = models.GenericIPAddressField(null=True, blank=True)
    tarih = models.DateTimeField(default=timezone.now, db_index=True)
    durum = models.PositiveSmallIntegerField(choices=DURUMLAR, default=DURUM_PASIF)
    onaylayan = models.ForeignKey(
        "auth.User", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="onayladigi_yorumlar")

    # --- §13'ün üç şartı: izsiz düzenleme okur adına beyanda bulunmaktır ---
    duzenlendi_mi = models.BooleanField(
        default=False, help_text="Okur, yorumunun değiştirildiğini görebilmeli.")
    duzenleyen = models.ForeignKey(
        "auth.User", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="duzenledigi_yorumlar")
    duzenleme_gerekcesi = models.CharField(
        max_length=200, blank=True,
        help_text="Kişisel veri / hakaret / reklam. Gerekçesiz kaydedilmez.")
    ozgun_metin = models.TextField(
        blank=True, help_text="Düzenlemeden önceki hâli; iz olarak saklanır.")

    class Meta:
        ordering = ["-tarih"]
        verbose_name = "yorum"
        verbose_name_plural = "yorumlar"
        indexes = [
            models.Index(fields=["icerik_turu", "icerik_id"]),
            models.Index(fields=["durum", "-tarih"]),
        ]

    def __str__(self) -> str:
        return f"{self.okur_adi}: {self.metin[:40]}"

    @classmethod
    def bekleyenler(cls):
        """Etkileşim kuyruğu: karar verilmemiş yorumlar (§13)."""
        return cls.objects.filter(durum=cls.DURUM_PASIF)


class LogKaydi(models.Model):
    """Eylem günlüğü — §24.8.

    **Mevcut paneldeki `login_logs` bir OTURUM AÇMA günlüğüdür, eylem günlüğü
    değil** (ölçüldü: sütunlar ID · IP · Tarayıcı · Durum · Tarih, hangi
    kaydın değiştiğini söyleyen tek sütun yok). §2'nin düzeltme kalemi bu
    yüzden iki katmanlıydı: adlar çakışıyordu *ve* log zaten eylemi
    kaydetmiyordu. Bu model ikinci katmanı kapatır.

    §24.8'de belirlenen **beş zorunlu alan** burada: `kullanici` (PROTECT) ·
    `fiil` (kapalı liste) · `hedef_tur` + `hedef_id` · `zaman` (indeksli) ·
    `oncesi` / `sonrasi`.
    """

    # Kapalı liste. Serbest metin olsaydı log aranamazdı.
    FIILLER = [
        ("giris", "Oturum açma"),
        ("giris_basarisiz", "Başarısız oturum denemesi"),
        ("cikis", "Oturum kapatma"),
        ("yayina_alma", "Yayına alma"),
        ("yayindan_cekme", "Yayından çekme"),
        ("arsivleme", "Arşive alma"),
        ("mansete_alma", "Manşete alma"),
        ("mansetten_cikarma", "Manşetten çıkarma"),
        ("kategori_degistirme", "Kategori değiştirme"),
        ("toplu_islem", "Toplu işlem"),
        ("kaynak_birlestirme", "Kaynak birleştirme"),
        ("yorum_duzenleme", "Yorum düzenleme"),
        ("yorum_karari", "Yorum onaylama/reddetme"),
        ("kullanici_degisikligi", "Kullanıcı veya rol değişikliği"),
        ("parola_degisikligi", "Parola değişikliği"),
        ("resmi_ilan", "Resmî ilan girme/silme"),
    ]

    # PROTECT: kullanıcı silinirse log okunamaz hâle gelir. Kimliği ada değil
    # KAYDA bağlamak, "dört hesap Administrator" sorununun asıl çözümü.
    kullanici = models.ForeignKey(
        "auth.User", on_delete=models.PROTECT, related_name="log_kayitlari")
    fiil = models.CharField(max_length=32, choices=FIILLER)
    hedef_tur = models.CharField(
        max_length=24, blank=True,
        help_text="Neyin değiştiği. Bu alan olmadan kayıt işe yaramaz.")
    hedef_id = models.BigIntegerField(null=True, blank=True)
    zaman = models.DateTimeField(default=timezone.now, db_index=True)

    # Değişen alanın iki hâli. Bunlar olmadan "yayından çekildi" kaydı NEYİN
    # değiştiğini söyler ama NEREDEN NEREYE olduğunu söylemez.
    oncesi = models.JSONField(null=True, blank=True)
    sonrasi = models.JSONField(null=True, blank=True)

    ip = models.GenericIPAddressField(null=True, blank=True)
    tarayici = models.CharField(max_length=300, blank=True)
    toplu_islem_kimligi = models.CharField(
        max_length=36, blank=True,
        help_text="Aynı toplu fiilin kayıtlarını birbirine bağlar.")
    gerekce = models.CharField(max_length=200, blank=True)
    etkilenen_sayisi = models.PositiveIntegerField(
        default=1, help_text="Toplu işlemde kaç kayıt etkilendi.")

    class Meta:
        ordering = ["-zaman"]
        verbose_name = "log kaydı"
        verbose_name_plural = "log kayıtları"
        # İndeksler BAŞTAN: tablo büyüdükten sonra indeks eklemek 300 binde
        # 1,2 sn, milyonda dakikalara çıkıyor (Ö1).
        indexes = [
            models.Index(fields=["hedef_tur", "hedef_id"]),
            models.Index(fields=["kullanici", "-zaman"]),
            models.Index(fields=["fiil", "-zaman"]),
            models.Index(fields=["toplu_islem_kimligi"]),
        ]

    def __str__(self) -> str:
        return f"{self.zaman:%d.%m.%Y %H:%M} {self.kullanici_id} {self.fiil}"

    @property
    def oturum_kaydi_mi(self) -> bool:
        """Saklama süresi ayrımı: oturum 12 ay, eylem süresiz (§24.8)."""
        return self.fiil in ("giris", "giris_basarisiz", "cikis")


class ReklamYuvasi(models.Model):
    """Reklam yuvası — §24.4, `URUN-PLANI.md` §3 F7(b).

    **Üç alan: konum · ölçü · cihaz.** Reklamverenin adı buraya YAZILMAZ;
    kampanyaya yazılır (§14, §16). Böylece reklamveren değişince yuva yerinde
    kalır ve "hepsiburada 2/3/4" gibi kayıtlar oluşmaz.

    **Ölçülmüş uyarı — taşıma otomatik değil.** Dökümdeki 50 yuvanın yalnız
    **6'sı** üç alana ayrışıyor; cihaz bilgisi **43'ünde hiç yok**, ölçü
    12'sinde yok, 4'ü yıldızlı yazım (`728*90`), 6'sı yer tutucu metni
    ("Bu alana reklam verebilirsiniz…") yani yuva değil boş yuvanın görünen
    hâli. F7(b)'nin "50 yuva bu modele taşınmış" ölçütü **elle eşlemeyle**
    karşılanır.

    `ad` alanı korunuyor çünkü anasayfa şablonları yuvayı ADIYLA çağırıyor
    (F1 ölçütü 3: `1100x150`, `-Manşet yanı- 300x250`, `-Sol pageskin1- 160x600`).
    Adı değiştirmek o ölçütü bozar.
    """

    CIHAZ_HEPSI, CIHAZ_MASAUSTU, CIHAZ_MOBIL = "hepsi", "masaustu", "mobil"
    CIHAZLAR = [(CIHAZ_HEPSI, "Hepsi"), (CIHAZ_MASAUSTU, "Masaüstü"),
                (CIHAZ_MOBIL, "Mobil")]

    ad = models.CharField(
        max_length=120, unique=True,
        help_text="Şablonun çağırdığı ad. DEĞİŞTİRİLMEMELİ: anasayfa "
                  "yuvaları bu adla arıyor.")
    konum = models.CharField(max_length=80, help_text="Sayfadaki yeri.")
    genislik = models.PositiveSmallIntegerField(null=True, blank=True)
    yukseklik = models.PositiveSmallIntegerField(null=True, blank=True)
    cihaz = models.CharField(max_length=10, choices=CIHAZLAR, default=CIHAZ_HEPSI)
    aktif = models.BooleanField(default=True)
    yer_tutucu_mu = models.BooleanField(
        default=False,
        help_text="Dökümde 6 kayıt yuva değil, boş yuvanın görünen hâliydi.")

    class Meta:
        ordering = ["konum", "ad"]
        verbose_name = "reklam yuvası"
        verbose_name_plural = "reklam yuvaları"

    def __str__(self) -> str:
        return self.ad

    @property
    def olcu(self) -> str:
        """"970x250" ya da boş. Ölçüsü bilinmeyen yuvada uydurma değer basma."""
        if self.genislik and self.yukseklik:
            return f"{self.genislik}x{self.yukseklik}"
        return ""


class ReklamKampanyasi(models.Model):
    """Reklam kampanyası — §24.4.

    Dökümdeki sütun sözleşmesi (`advertisement_list.php`): Başlık · Fotoğraf ·
    Başlangıç / Bitiş Tarihi · Reklam Alanı · Editör · İşlemler.

    Görsel **yerel dosya yolu** olarak tutuluyor; sayfanın internetsiz
    açılması kuralı reklam görselinde de geçerli.

    **Yuva bağı ÇOKA ÇOK** — 29 Ağustos 2026'da ölçülerek düzeltildi. Model
    tek yuvalı (ForeignKey) kurulmuştu; dökümün "Reklam Alanı" sütununda
    kampanyaların **8'i (25'te)** birden çok yuva sayıyor
    ("-Manşet yanı- 300x250 / -Manşet altı1- 300x250 / -Haber arası2- 300x250").
    Tam liste hücrenin `data-bs-title` ipucunda duruyor; ekranda kısaltılmış
    görünen kısım kayıp değil. Tek yuvada ısrar etmek kampanyayı yuva başına
    bölmek demekti — 131 kampanyalık gerçeği bozardı.
    """

    DURUM_AKTIF, DURUM_PASIF = 1, 2
    DURUMLAR = [(DURUM_AKTIF, "Aktif"), (DURUM_PASIF, "Pasif")]

    baslik = models.CharField(max_length=200)
    yuvalar = models.ManyToManyField(
        ReklamYuvasi, related_name="kampanyalar", through="KampanyaYuva",
        help_text="Bir kampanya birden çok yuvada yayımlanabilir.")
    gorsel_dosya = models.CharField(max_length=300, blank=True)
    gorsel_alt = models.CharField(max_length=300, blank=True)
    hedef_adres = models.URLField(max_length=600, blank=True)
    baslangic = models.DateField(null=True, blank=True)
    bitis = models.DateField(null=True, blank=True)
    durum = models.PositiveSmallIntegerField(choices=DURUMLAR, default=DURUM_PASIF)
    olusturan = models.ForeignKey(
        "auth.User", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="reklam_kampanyalari")

    class Meta:
        ordering = ["-baslangic", "baslik"]
        verbose_name = "reklam kampanyası"
        verbose_name_plural = "reklam kampanyaları"
        # Yuva artık M2M; indeks yalnız duruma kurulur.
        indexes = [models.Index(fields=["durum"])]

    def __str__(self) -> str:
        return self.baslik

    def suresi_gecti_mi(self) -> bool:
        return bool(self.bitis and self.bitis < timezone.localdate())


class KampanyaYuva(models.Model):
    """Kampanya ↔ yuva bağı. Django'nun ürettiği tabloyu kendimiz yazıyoruz.

    **Tek sebebi `PROTECT`.** Bağ önce ForeignKey'di ve yuva silinmeye
    çalışılınca `ProtectedError` veriyordu; çoka çok bağa geçerken Django'nun
    varsayılan ara tablosu bu korumayı sessizce düşürüyor, kullanımdaki bir
    yuva silinince kampanya yuvasız kalıyordu. Yuva adları anasayfa
    şablonlarında geçtiği için (F1 ölçütü 3) bu sessiz kayıp pahalı.
    """

    kampanya = models.ForeignKey("ReklamKampanyasi", on_delete=models.CASCADE)
    yuva = models.ForeignKey(ReklamYuvasi, on_delete=models.PROTECT)

    class Meta:
        constraints = [models.UniqueConstraint(
            fields=["kampanya", "yuva"], name="kampanya_yuva_tek")]
        verbose_name = "kampanya-yuva bağı"
        verbose_name_plural = "kampanya-yuva bağları"

    def __str__(self) -> str:
        return f"{self.kampanya_id} → {self.yuva_id}"


class Gazete(models.Model):
    """BIK yayın kodu defteri — §24.5.

    17 kayıt, hepsi `YYN-` kodlu (ölçüldü). **Bursa Hakimiyet: `YYN-000132`** —
    gazetenin kendi yayın kodu ve resmî ilan yükümlülüklerinin dayanağı,
    değiştirilmemeli (§16).

    `save_newspaper_sort_ajax` ucu dökümde var, yani liste sıralanabilir:
    `sira` alanı ondan.
    """

    ad = models.CharField(max_length=120, unique=True)
    bik_kodu = models.CharField(max_length=20, blank=True)
    sira = models.PositiveSmallIntegerField(default=0)
    aktif = models.BooleanField(default=True)
    bizim_mi = models.BooleanField(
        default=False, help_text="Bursa Hakimiyet'in kendi kaydı; ayrı işaretlenir.")

    class Meta:
        ordering = ["sira", "ad"]
        verbose_name = "gazete"
        verbose_name_plural = "gazeteler"

    def __str__(self) -> str:
        return f"{self.ad} ({self.bik_kodu})" if self.bik_kodu else self.ad


class ResmiIlan(models.Model):
    """Resmî ilan — §24.3.

    **Dört tür yasal karşılığı olduğu için korunur** (§16): ölçülen 24 kaydın
    hiçbiri İCRA ya da PERSONEL ALIMI değil (14 İHALE + 10 TEBLİGAT), ama
    kullanılmıyor diye kaldırılmadılar.

    **Ölçüm sınırı:** dökümde ilan EKLEME formu yok
    (`official_announcement_add` ucu var, sayfası kaydedilmemiş). Metin
    uzunluğu, BIK kodu ve ek dosya alanları **ölçülemedi** — aşağıdakiler
    bizim türetimimizdir ve döküm gelirse gözden geçirilmeli (§24.3).
    """

    TUR_ICRA, TUR_IHALE, TUR_TEBLIGAT, TUR_PERSONEL = (
        "icra", "ihale", "tebligat", "personel")
    TURLER = [(TUR_ICRA, "İCRA"), (TUR_IHALE, "İHALE"),
              (TUR_TEBLIGAT, "TEBLİGAT"), (TUR_PERSONEL, "PERSONEL ALIMI")]

    DURUM_AKTIF, DURUM_PASIF, DURUM_ARSIV = 1, 2, 4
    DURUMLAR = [(DURUM_AKTIF, "Aktif"), (DURUM_PASIF, "Pasif"),
                (DURUM_ARSIV, "Arşiv")]

    baslik = models.CharField(max_length=300)
    tur = models.CharField(max_length=10, choices=TURLER, default=TUR_IHALE)
    metin = models.TextField(blank=True)
    yayin_tarihi = models.DateField(null=True, blank=True, db_index=True)
    bitis_tarihi = models.DateField(null=True, blank=True)
    bik_kodu = models.CharField(max_length=40, blank=True)
    gazete = models.ForeignKey(
        Gazete, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="ilanlar",
        help_text="Hangi gazetede yayımlandı. Dökümde bu bağ GÖRÜNMÜYOR; "
                  "isteğe bağlı bırakıldı (§24.5).")
    durum = models.PositiveSmallIntegerField(choices=DURUMLAR, default=DURUM_AKTIF)
    olusturan = models.ForeignKey(
        "auth.User", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="resmi_ilanlari")

    class Meta:
        ordering = ["-yayin_tarihi", "-id"]
        verbose_name = "resmî ilan"
        verbose_name_plural = "resmî ilanlar"
        indexes = [models.Index(fields=["tur", "-yayin_tarihi"])]

    def __str__(self) -> str:
        return f"[{self.get_tur_display()}] {self.baslik[:50]}"

    # -- anasayfa bölümünü besleyen sorgular ------------------------------
    #
    # SÜZGEÇ NEDEN "AKTİF" DEĞİL, "PASİF DEĞİL"? Ölçüldü (29 Ağustos 2026):
    # 24 kaydın **hiçbiri AKTİF değil** — 23'ü Arşiv, 1'i Pasif. Durum kodu
    # dökümün kendi JS'inden geliyor ve tooltip DURUMU söylüyor, eylemi
    # değil (`row[8]==1` → "Aktif", `==2` → "Pasif", başka → "Arşivden
    # çıkar"). Yani `durum=AKTIF` süzgeci anasayfayı BOŞ bırakırdı.
    #
    # Arşiv ile Pasif aynı şey değil: arşiv "yayımlandı, güncelliğini
    # yitirdi", pasif ise editörün yayından **çektiği** kayıt. Bölüm
    # gazetenin yayımladığı ilanların dizini olduğu için arşiv kalır,
    # pasif çıkar. Kayıtlar aktifleşmeye başlayınca bu süzgeç yeniden
    # değerlendirilmeli (URUN-PLANI.md §24.3).
    @classmethod
    def yayimlananlar(cls):
        return cls.objects.exclude(durum=cls.DURUM_PASIF)

    @classmethod
    def tur_dagilimi(cls, kayitlar):
        """Dört türü de sırayla döndürür — **sayısı sıfır olanlar dahil.**

        İCRA ve PERSONEL ALIMI türünde kayıt yok ama dört türün yasal
        karşılığı var (§16); süzgeç şeridi bunları 0 ile gösterir, çünkü
        "bu gazete bu türde ilan yayımlamıyor" da bir bilgidir.

        **İki yol, tek sonuç.** Anasayfa bölümü sayfadaki SEKİZ kaydı
        sayıyor ve elinde zaten bir liste var; dizin sayfası ise arşivin
        TAMAMINI sayıyor ve oradaki liste sayfalanmış. Liste geldiğinde
        Python'da sayılır, QuerySet geldiğinde sayım veritabanına
        bırakılır — yoksa dizin, yalnız sayı basmak için bütün arşivi
        belleğe alırdı (23 kayıtta görünmez, ilan modülü canlıya çıkınca
        görünür). İki yolun aynı çıktıyı verdiği testle kilitli.
        """
        if isinstance(kayitlar, models.QuerySet):
            # `order_by()` boşaltılmazsa Meta sıralaması GROUP BY'a
            # sızıyor ve sayım tür başına değil satır başına dönüyor.
            sayac = dict(kayitlar.order_by().values_list("tur")
                         .annotate(adet=models.Count("tur"))
                         .values_list("tur", "adet"))
        else:
            sayac = Counter(k.tur for k in kayitlar)
        dagilim = [{"anahtar": anahtar, "ad": ad, "adet": sayac.get(anahtar, 0)}
                   for anahtar, ad in cls.TURLER]
        # Kaydı olan türler önce ve çoktan aza. Yasal sıra (İCRA ilk)
        # süzgeci boş bir düğmeyle açıyordu; okur önce gerçekten ilan
        # olan türü görmeli. Sıfırlar yasal sırasını koruyarak sona iner.
        dagilim.sort(key=lambda t: (t["adet"] == 0, -t["adet"]))
        return dagilim


class Bildirim(models.Model):
    """Anlık bildirim kaydı — §24.9.

    **Açılma oranı SAKLANMAZ, türetilir** (`acan / hedef`); iki sayı zaten
    kayıtta. §13'ün kararı: mevcut panelde iki sütun var ama oran hiçbir yerde
    hesaplanmıyor, yeni ekranda en üste alınır.

    Ölçülen geçmiş (§13): 10 gönderimde ortalama **%0,21**; hedef kitle
    9.207 → 22.683'e çıkarken açan sayısı 21-47 bandında sabit kalmış.
    "Veri Kaynağı" dökümde iki değer alıyor: `Makale` ve `Haber`.

    **Bu model yalnız KAYDI tutar.** Gerçek gönderim altyapısı (push servisi)
    model turunun kapsamı dışında (§24.9).
    """

    BASLIK_SINIRI = 50   # §13: kilit ekranında kesilmesin

    icerik_turu = models.CharField(
        max_length=8, choices=Yorum.TURLER, default=Yorum.TUR_HABER)
    icerik_id = models.BigIntegerField(
        null=True, blank=True,
        help_text="§13: haber seçilmeden gönderim yapılamaz.")
    baslik = models.CharField(max_length=BASLIK_SINIRI)
    gonderen = models.ForeignKey(
        "auth.User", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="bildirimleri")
    gonderim_zamani = models.DateTimeField(null=True, blank=True, db_index=True)
    hedef_sayisi = models.PositiveIntegerField(default=0)
    acan_sayisi = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-gonderim_zamani", "-id"]
        verbose_name = "bildirim"
        verbose_name_plural = "bildirimler"

    def __str__(self) -> str:
        return self.baslik

    @property
    def acilma_orani(self) -> float:
        """Yüzde. Hedef sıfırsa 0 — bölme hatası okura yansımamalı."""
        if not self.hedef_sayisi:
            return 0.0
        return self.acan_sayisi * 100.0 / self.hedef_sayisi


class IkiAdimli(models.Model):
    """İki adımlı doğrulama ayarı — §24.10.

    **KURULUM AKIŞI BİLEREK AÇILMADI.** Gizli anahtarın nasıl saklanacağı bir
    güvenlik kararıdır ve kullanıcıya soruldu (28 Ağustos 2026), cevap
    bekleniyor. Düz metin saklamak, 2FA'nın koruduğu şeyi veritabanı erişimi
    olan herkese açar.

    Bu yüzden model duruyor ama `gizli_anahtar` alanını **dolduran hiçbir yol
    yok**: panel ekranı yalnız durumu gösterir, kurulum yaptırmaz. Yarım bir
    2FA, olmayan 2FA'dan tehlikelidir — kullanıcı korunduğunu sanır.

    Çelişki kayıtlı (§24.10): §11 "isteğe bağlı" diyor, dökümdeki ekran metni
    "zorunludur" diyor; hangisinin fiilen uygulandığı **ölçülemedi**.
    """

    YONTEM_AUTHENTICATOR, YONTEM_SMS = "authenticator", "sms"
    YONTEMLER = [(YONTEM_AUTHENTICATOR, "Google Authenticator"),
                 (YONTEM_SMS, "SMS")]

    kullanici = models.OneToOneField(
        "auth.User", on_delete=models.CASCADE, related_name="iki_adimli")
    yontem = models.CharField(max_length=16, choices=YONTEMLER,
                              default=YONTEM_AUTHENTICATOR)
    gizli_anahtar = models.CharField(
        max_length=200, blank=True,
        help_text="ŞİFRELEME KARARI BEKLİYOR — bu alana yazan bir akış "
                  "bilerek kurulmadı (§24.10).")
    telefon = models.CharField(max_length=20, blank=True)
    dogrulandi_mi = models.BooleanField(default=False)
    son_kullanim = models.DateTimeField(null=True, blank=True)
    yedek_kodlar = models.JSONField(null=True, blank=True)

    class Meta:
        verbose_name = "iki adımlı doğrulama"
        verbose_name_plural = "iki adımlı doğrulamalar"

    def __str__(self) -> str:
        return f"{self.kullanici_id} — {self.get_yontem_display()}"

    @property
    def kurulu_mu(self) -> bool:
        return bool(self.dogrulandi_mi and self.gizli_anahtar)


class SonDakika(models.Model):
    """Son dakika bandı kaydı — §24.2.

    **Ayrı model, haberde bayrak değil.** Üç ölçülmüş gerekçe (§24.2):
    dökümdeki kayıt serbest URL taşıyor (`lastMinuteUrl`), başlık habere ait
    değil (`headline_title` ayrı alan), ve `icerik_haber`e bayrak eklemek
    356 bin satırda ~34 sn'lik tablo yeniden kurma demek.

    Bant önce bu tabloya bakar, boşsa bugünkü "en yeni haberler" davranışına
    düşer (`icerik/baglam.py`) — bugünkü davranış kaybolmaz.

    §18 m.4: en yeni kayıt 2025-12-20, sekiz aydır kullanılmıyor; göçte veri
    taşınmadı, davranış yeniden kuruldu.
    """

    baslik = models.CharField(max_length=200)
    adres = models.CharField(
        max_length=600, blank=True,
        help_text="Serbest adres. Boşsa bağlı haberin adresi kullanılır.")
    haber = models.ForeignKey(
        Haber, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="son_dakika_kayitlari")
    baslangic = models.DateTimeField(default=timezone.now)
    bitis = models.DateTimeField(null=True, blank=True)
    sira = models.PositiveSmallIntegerField(default=0)
    aktif = models.BooleanField(default=True)
    olusturan = models.ForeignKey(
        "auth.User", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="son_dakikalari")

    class Meta:
        ordering = ["sira", "-baslangic"]
        verbose_name = "son dakika"
        verbose_name_plural = "son dakika kayıtları"
        indexes = [models.Index(fields=["aktif", "sira"])]

    def __str__(self) -> str:
        return self.baslik

    @property
    def yol(self) -> str:
        """Banttaki bağlantı. Serbest adres önceliklidir."""
        if self.adres:
            return self.adres
        return self.haber.get_absolute_url() if self.haber_id else ""

    @classmethod
    def bandakiler(cls):
        """Şu an bantta görünmesi gerekenler."""
        simdi = timezone.now()
        return cls.objects.filter(aktif=True, baslangic__lte=simdi).filter(
            models.Q(bitis__isnull=True) | models.Q(bitis__gte=simdi))
