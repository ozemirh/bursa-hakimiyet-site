"""Haber formu — `PANEL-NOTLARI.md` §4'teki 31 satırlık alan sözleşmesi.

Sözleşmenin "Gerçekten zorunlu" sütunu mevcut panelin ölçülmüş hâlidir:
ekranda kırmızı yıldız görünen üç alan (`summery`, `tagElementName`,
`articleAuthor`) `formControl` muafiyet listesinde olduğu için **boş
kaydedilebiliyordu**. Yeni panelde bu yalan kapatıldı.

## Ne zaman zorunlu

Zorunluluk **yayına alırken** işler, taslak kaydederken değil. Gerekçe:
sahadan giren haber Pasif/Taslak'ta doğar (§9) ve muhabir yarım işi
kaydedebilmelidir; aksi hâlde §11'deki "Muhabir yayınlayamaz" kuralı
muhabirin hiçbir şey kaydedemediği anlamına gelirdi.

    Taslak kaydı   → yalnızca başlık ve kategori şart
    Yayına alma    → başlık · spot · en az iki paragraf gövde · etiket ·
                     kategori · yayın zamanı

Bu, `arac/yayin.py`deki "boş taslak yayınlanmaz" kuralıyla aynı eşiktir.

## Adres uyarısı

Kategori değişimi haberin **adresini** değiştirir (`/{kategori}/{slug}-{id}`)
ve 556.824 adresin deseni budur. Yayımlanmış bir haberin kategorisi
değiştirilirse form eski adresi `Yonlendirme` tablosuna yazar; bağlantı
kırılmaz.
"""

from django import forms
from django.contrib.auth.models import Group, User
from django.utils import timezone

from medya.models import FotoGaleri, KoseYazisi, Video, Yazar
from taksonomi.models import Etiket, Ilce, Kategori, Kaynak, Yonlendirme

from .models import Haber
from .yetkiler import ROLLER

BASLIK_SINIR = 60      # §4 alan 2 — ekranda sayaç görünür
SPOT_SINIR = 160       # §4 alan 4
EN_AZ_PARAGRAF = 2     # §4 alan 5


class HaberForm(forms.ModelForm):
    """Panelin haber ekle/düzenle formu."""

    etiketler = forms.ModelMultipleChoiceField(
        queryset=Etiket.objects.all(), required=False,
        widget=forms.SelectMultiple(attrs={"data-cip": "1"}),
        help_text="Çip arayüzü. Yayına alırken en az bir etiket şart.")

    class Meta:
        model = Haber
        fields = [
            "baslik", "ikinci_baslik", "spot", "govde",
            "kategori", "ilce", "etiketler",
            "kaynak_turu", "muhabir", "kaynaklar", "meta_yazar",
            "gorsel_url", "gorsel_alt",
            "durum", "hazirlik",
            "yayin_zamani", "guncelleme_zamani",
            "manset_ana", "manset_tepe", "manset_kare",
            "rss", "yorumlar_acik", "yonlendirme_url", "gomulu_kod",
            "ilgili_haberler", "odak_kelime", "seo_baslik",
        ]
        widgets = {
            "baslik": forms.TextInput(attrs={"maxlength": BASLIK_SINIR,
                                             "data-sayac": BASLIK_SINIR}),
            "ikinci_baslik": forms.TextInput(attrs={"maxlength": BASLIK_SINIR}),
            "spot": forms.Textarea(attrs={"rows": 3, "maxlength": SPOT_SINIR,
                                          "data-sayac": SPOT_SINIR}),
            "govde": forms.Textarea(attrs={"rows": 18}),
        }
        labels = {
            "baslik": "Başlık", "ikinci_baslik": "İkinci başlık",
            "spot": "Spot", "govde": "Gövde", "kategori": "Kategori",
            "ilce": "İlçe", "kaynak_turu": "Kaynak türü",
            "muhabir": "Muhabir", "kaynaklar": "Kaynak",
            "meta_yazar": "Meta Yazar Bilgisi",
            "gorsel_alt": "Görsel alt metni",
            "durum": "Durum", "hazirlik": "Hazırlık",
            "yayin_zamani": "Yayın zamanı",
            "guncelleme_zamani": "Güncelleme zamanı",
            "manset_ana": "Ana manşet", "manset_tepe": "Tepe manşet",
            "manset_kare": "Kare manşet",
        }

    def __init__(self, *args, kullanici=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.kullanici = kullanici
        self._eski_kategori_id = self.instance.kategori_id if self.instance.pk else None

        self.fields["kategori"].queryset = Kategori.objects.filter(aktif=True)
        self.fields["kaynaklar"].queryset = Kaynak.objects.filter(
            aktif=True, birlesti_ile__isnull=True)
        self.fields["ilce"].queryset = Ilce.objects.all()
        self.fields["ilce"].required = False

        # §7: değer kaynak türünden türetilir, editör isterse ezer.
        self.fields["meta_yazar"].required = False
        self.fields["meta_yazar"].help_text = (
            "Boş bırakılırsa kaynak türünden türetilir. Elle seçilirse türetim durur.")

        # Yalnızca taslak kaydında zorunlu olan iki alan; gerisi clean()'de.
        for ad in ("spot", "govde", "yayin_zamani"):
            self.fields[ad].required = False

        # §11: manşete alma ayrı yetkidir. Yetkisi olmayan bu üç kutuyu
        # göremez — formda tutulup sessizce yok sayılması yanlış olurdu.
        if kullanici is not None and not kullanici.has_perm("icerik.mansete_alma"):
            for ad in ("manset_ana", "manset_tepe", "manset_kare"):
                self.fields.pop(ad)

    # -- alan denetimleri --------------------------------------------------

    def clean_baslik(self):
        baslik = (self.cleaned_data.get("baslik") or "").strip()
        if not baslik:
            raise forms.ValidationError("Başlık zorunludur.")
        if len(baslik) > BASLIK_SINIR:
            raise forms.ValidationError(
                f"Başlık en çok {BASLIK_SINIR} karakter olabilir "
                f"(şu an {len(baslik)}).")
        return baslik

    def clean_spot(self):
        spot = (self.cleaned_data.get("spot") or "").strip()
        if len(spot) > SPOT_SINIR:
            raise forms.ValidationError(
                f"Spot en çok {SPOT_SINIR} karakter olabilir (şu an {len(spot)}).")
        return spot

    def clean_muhabir(self):
        muhabir = (self.cleaned_data.get("muhabir") or "").strip()
        if self.data.get("kaynak_turu") == Haber.KAYNAK_MUHABIR and not muhabir:
            raise forms.ValidationError(
                "Kaynak türü 'Kendi muhabirimiz' seçildiyse muhabir adı yazılmalı.")
        return muhabir

    # -- bütün form --------------------------------------------------------

    def clean(self):
        veri = super().clean()
        durum = veri.get("durum")
        hazirlik = veri.get("hazirlik")
        yayina_gidiyor = (durum == Haber.DURUM_AKTIF) or (hazirlik == "hazir")

        # §7: meta yazar elle seçildiyse türetim durur.
        veri["meta_yazar_elle"] = bool(veri.get("meta_yazar"))

        if not yayina_gidiyor:
            return veri

        eksik = []
        if not (veri.get("spot") or "").strip():
            eksik.append("spot")
        govde = (veri.get("govde") or "").strip()
        if self._paragraf_sayisi(govde) < EN_AZ_PARAGRAF:
            eksik.append(f"gövde (en az {EN_AZ_PARAGRAF} paragraf)")
        if not veri.get("etiketler"):
            eksik.append("en az bir etiket")
        if not veri.get("yayin_zamani"):
            veri["yayin_zamani"] = timezone.now()

        if eksik:
            raise forms.ValidationError(
                "Yayına almak için şunlar gerekli: " + ", ".join(eksik) +
                ". Taslak olarak kaydedebilirsiniz.")
        return veri

    @staticmethod
    def _paragraf_sayisi(govde: str) -> int:
        """Gövdedeki paragraf sayısı.

        Panelden HTML gelir (`<p>…</p>`), yapıştırmadan düz metin de gelebilir;
        ikisi de sayılır.
        """
        if not govde:
            return 0
        etiketli = govde.lower().count("<p")
        if etiketli:
            return etiketli
        return len([p for p in govde.split("\n\n") if p.strip()])

    # -- kayıt -------------------------------------------------------------

    def save(self, commit=True):
        haber = super().save(commit=False)
        haber.meta_yazar_elle = self.cleaned_data.get("meta_yazar_elle", False)
        if self.kullanici is not None and haber.olusturan_id is None:
            haber.olusturan = self.kullanici
        if commit:
            haber.save()
            self.save_m2m()
            self._kategori_degisimini_yonlendir(haber)
        return haber

    def _kategori_degisimini_yonlendir(self, haber):
        """Kategori değiştiyse eski adresi yeni adrese bağlar.

        Adres deseni `/{kategori}/{slug}-{id}`; kategori değişince eski
        bağlantı ölür. Kimlikten çözüm çoğu durumu kurtarır ama eski
        kategori slug'ı artık o haberi göstermeyeceği için kayıt şart.
        """
        eski = self._eski_kategori_id
        if eski is None or eski == haber.kategori_id:
            return
        eski_kategori = Kategori.objects.filter(pk=eski).first()
        if eski_kategori is None:
            return
        eski_slug = eski_kategori.slug_al()
        if not eski_slug:
            return
        Yonlendirme.objects.update_or_create(
            eski_yol=f"/{eski_slug}/{haber.slug}-{haber.id}",
            defaults={"yeni_yol": haber.get_absolute_url(), "kod": 301,
                      "sebep": "Kategori panelden değiştirildi."},
        )


# ===========================================================================
# Medya ve ayar formları
#
# **Dürüstlük notu:** bu beş formun arkasında haber formununki gibi ölçülmüş
# bir alan sözleşmesi YOK. `PANEL-NOTLARI.md` §11: mevcut panelin
# `gallery_add`, `video_add`, `editorialist_add` ekranlarının dökümü elimizde
# değil — alan sözleşmesi yalnız haber için ölçüldü. Bu yüzden alanlar
# **modelimizin kendi alanlarıdır**; sağlayıcının formundan alan uydurulmadı.
# Döküm gelirse sözleşme buraya yazılır.
#
# Ortak kural: **kimlik ve slug adresin parçasıdır ve dondurulmuştur.**
# İkisi de `editable=False` olduğu için ModelForm'a hiç girmiyor; künye
# olarak salt okunur gösteriliyor.
# ===========================================================================


class ArsivKaydiForm(forms.ModelForm):
    """Köşe · galeri · video formlarının ortak gövdesi.

    Yayın zamanı **zorunlu tutulmuyor** ama boşsa kayıt listelerde görünmez
    (`yayindakiler()` sıralamayı ona dayandırıyor); form bunu söylüyor.
    """

    class Meta:
        fields = ["baslik", "spot", "durum", "yayin_zamani",
                  "guncelleme_zamani", "gorsel_alt"]
        labels = {
            "baslik": "Başlık", "spot": "Spot", "durum": "Durum",
            "yayin_zamani": "Yayın zamanı",
            "guncelleme_zamani": "Güncelleme zamanı",
            "gorsel_alt": "Görsel alt metni",
        }
        help_texts = {
            "gorsel_alt": "Ekran okuyucu için. Eski panelde bu alan hiç yoktu.",
            "yayin_zamani": "Boşsa kayıt yayın listelerinde görünmez.",
        }
        widgets = {"spot": forms.Textarea(attrs={"rows": 3})}

    def clean_baslik(self):
        baslik = (self.cleaned_data.get("baslik") or "").strip()
        if not baslik:
            raise forms.ValidationError("Başlık zorunludur.")
        return baslik


class KoseYazisiForm(ArsivKaydiForm):
    """Köşe yazısı.

    **Yazar adresin parçasıdır** (`/yazarlar/{yazar-slug}-{id}/{slug}-{id}`).
    Yazarı değiştirmek yazının adresini değiştirir; form bunu uyarı olarak
    söylüyor. Yönlendirme kaydı haber formundaki gibi otomatik yazılmıyor —
    o davranış köşe tarafında henüz karara bağlanmadı, sessizce varsaymak
    yerine uyarı veriliyor.
    """

    class Meta(ArsivKaydiForm.Meta):
        model = KoseYazisi
        fields = ["baslik", "yazar", "kategori", "spot", "govde", "durum",
                  "yayin_zamani", "guncelleme_zamani", "gorsel_alt"]
        labels = dict(ArsivKaydiForm.Meta.labels,
                      yazar="Yazar", kategori="Kategori", govde="Gövde")
        help_texts = dict(
            ArsivKaydiForm.Meta.help_texts,
            yazar="ADRESİN parçasıdır. Değiştirirseniz yazının adresi değişir "
                  "ve eski bağlantı kırılır.",
            kategori="İsteğe bağlı. Köşe yazısının adresi kategoriye bağlı "
                     "değildir.")
        widgets = dict(ArsivKaydiForm.Meta.widgets,
                       govde=forms.Textarea(attrs={"rows": 18}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["kategori"].queryset = Kategori.objects.filter(aktif=True)
        self.fields["kategori"].required = False


class YazarForm(forms.ModelForm):
    """Köşe yazarı.

    Göçte 20 kayıt köşe yazısının künyesinden türetildi ve
    `sayfasi_tarandi = False` işaretli; bu form o kayıtları tamamlamak için
    var. Alan salt okunur değil ama **el değdiğini** işaretliyor: ad
    doldurulduğunda kayıt artık geçici sayılmaz.
    """

    class Meta:
        model = Yazar
        fields = ["ad", "unvan", "ozgecmis", "eposta", "aktif", "sira"]
        labels = {"ad": "Ad Soyad", "unvan": "Unvan", "ozgecmis": "Özgeçmiş",
                  "eposta": "E-posta", "aktif": "Listelerde göster",
                  "sira": "Sıra"}
        help_texts = {
            "aktif": "Kapalıyken yalnız LİSTELERDEN düşer; yazarın sayfası "
                     "yine açılır. Eski bağlantılar 404 olmamalı.",
        }
        widgets = {"ozgecmis": forms.Textarea(attrs={"rows": 5})}

    def clean_ad(self):
        ad = (self.cleaned_data.get("ad") or "").strip()
        if not ad:
            raise forms.ValidationError("Yazar adı zorunludur.")
        return ad


class FotoGaleriForm(ArsivKaydiForm):
    """Foto galeri.

    `kareler_eksik` ölçülmüş bir gerçeği taşır: kareler kaynak sayfanın
    statik HTML'inde yok ve bir api ucu bulunamadı, yalnız kapak alınabildi.
    Kutu, kareler panelden girildiğinde elle kapatılır.
    """

    class Meta(ArsivKaydiForm.Meta):
        model = FotoGaleri
        fields = ["baslik", "kategori", "spot", "durum", "yayin_zamani",
                  "guncelleme_zamani", "gorsel_alt", "kareler_eksik",
                  "kareler_notu"]
        labels = dict(ArsivKaydiForm.Meta.labels, kategori="Kategori",
                      kareler_eksik="Kareler eksik",
                      kareler_notu="Kareler notu")
        help_texts = dict(
            ArsivKaydiForm.Meta.help_texts,
            kategori="Adres dilimi kategoriden gelir ve DONDURULMUŞTUR; "
                     "kategoriyi değiştirmek galerinin adresini değiştirir.",
            kareler_eksik="Ölçüldü: kareler kaynaktan alınamadı. Kareler "
                          "girildiğinde bu kutu kapatılır.")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        kimlikler = Kategori.objects.filter(turler__tur=Kategori.TUR_FOTO)
        self.fields["kategori"].queryset = kimlikler.distinct()
        self.fields["kategori"].required = False


class VideoForm(ArsivKaydiForm):
    """Video.

    İki adres alanı bilerek duruyor ve **eşit değiller** (312/312 ölçüm):
    `video_url` kaynakta sayfanın kendi adresini taşıyor, gerçek oynatıcı
    `gomulu_url`de. Okura basılan bağlantı `oynatma_adresi`nden gelir ve
    kendi adresine dönen değeri hiç basmaz.
    """

    class Meta(ArsivKaydiForm.Meta):
        model = Video
        fields = ["baslik", "kategori", "spot", "durum", "yayin_zamani",
                  "guncelleme_zamani", "gorsel_alt", "gomulu_url",
                  "video_url", "sure"]
        labels = dict(ArsivKaydiForm.Meta.labels, kategori="Kategori",
                      gomulu_url="Oynatıcı adresi (embed)",
                      video_url="Kaynaktaki içerik adresi", sure="Süre")
        help_texts = dict(
            ArsivKaydiForm.Meta.help_texts,
            gomulu_url="Okura gösterilen bağlantı buradan gelir.",
            video_url="Kaynakta çoğu kayıtta sayfanın KENDİ adresi; yalnız "
                      "iz olarak duruyor.",
            sure="Kaynaktaki hâli (ISO 8601, ör. PT2M30S).")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        kimlikler = Kategori.objects.filter(turler__tur=Kategori.TUR_VIDEO)
        self.fields["kategori"].queryset = kimlikler.distinct()
        self.fields["kategori"].required = False


class KategoriForm(forms.ModelForm):
    """Kategori — **slug alanı yok, olmayacak.**

    Karar §18: adlar birleşti, slug'lar donduruldu. Slug
    `/{kategori}/{slug}-{id}` adresinin ilk parçası ve 556.824 haber
    adresini taşıyor. Bu yüzden slug forma hiç konulmadı: "salt okunur alan"
    yapmak onu bir gün düzenlenebilir kılma ihtimalini açık bırakırdı.
    """

    class Meta:
        model = Kategori
        fields = ["ad", "ust", "sira", "aktif"]
        labels = {"ad": "Kategori adı", "ust": "Üst kategori",
                  "sira": "Sıra", "aktif": "Aktif"}
        help_texts = {
            "ad": "Ad değişebilir; ADRES değişmez. Slug dondurulmuştur.",
            "aktif": "Pasif kategori süzgeçlerde ve menüde görünmez; "
                     "adresleri çalışmaya devam eder.",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["ust"].required = False
        if self.instance.pk:
            self.fields["ust"].queryset = Kategori.objects.exclude(
                pk=self.instance.pk)

    def clean_ad(self):
        ad = (self.cleaned_data.get("ad") or "").strip()
        if not ad:
            raise forms.ValidationError("Kategori adı zorunludur.")
        return ad

    def clean_ust(self):
        ust = self.cleaned_data.get("ust")
        if ust and self.instance.pk and ust.pk == self.instance.pk:
            raise forms.ValidationError("Kategori kendi üstü olamaz.")
        return ust


class KullaniciForm(forms.ModelForm):
    """Kullanıcı hesabı ve rolü.

    §2'nin düzeltme kalemi burada uygulanıyor: mevcut sistemde **dört hesap
    "Administrator" adını paylaşıyor** ve log kaydı kimin ne yaptığını
    söyleyemiyor. Form, görünen adın başka bir hesapla çakışmasını
    engelliyor.

    **Parola bu formda yok.** Parola değiştirme ayrı bir akıştır ve hesabın
    sahibine aittir; yönetici formundan parola koymak izsiz kimliğe bürünme
    kapısı açar.
    """

    roller = forms.ModelMultipleChoiceField(
        queryset=Group.objects.none(), required=False, label="Roller",
        help_text="Yetkiler rol matrisinden gelir (Ayarlar › Roller).",
        widget=forms.SelectMultiple)

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "is_active"]
        labels = {"username": "Kullanıcı adı", "first_name": "Ad",
                  "last_name": "Soyad", "email": "E-posta",
                  "is_active": "Hesap açık"}
        help_texts = {
            "is_active": "Kapatılan hesap giriş yapamaz; ürettiği kayıtlar "
                         "ve log izleri durur.",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["roller"].queryset = Group.objects.filter(name__in=ROLLER)
        if self.instance.pk:
            self.initial["roller"] = self.instance.groups.all()
        for ad in ("first_name", "last_name"):
            self.fields[ad].required = True

    def clean(self):
        veri = super().clean()
        ad = " ".join(x for x in [(veri.get("first_name") or "").strip(),
                                  (veri.get("last_name") or "").strip()] if x)
        if not ad:
            return veri
        cakisan = User.objects.filter(
            first_name=veri.get("first_name") or "",
            last_name=veri.get("last_name") or "")
        if self.instance.pk:
            cakisan = cakisan.exclude(pk=self.instance.pk)
        if cakisan.exists():
            raise forms.ValidationError(
                f"“{ad}” adı başka bir hesapta kullanılıyor "
                f"({cakisan.first().get_username()}). Log kaydı kimin ne "
                "yaptığını söyleyebilmeli; adlar ayırt edilebilir olmalı.")
        return veri

    def save(self, commit=True):
        kullanici = super().save(commit=commit)
        if commit:
            kullanici.groups.set(self.cleaned_data.get("roller") or [])
        return kullanici


class KaynakForm(forms.ModelForm):
    """Kaynak kaydı ve birleştirme — `PANEL-NOTLARI.md` §17.

    §17'nin üç sorun bloğundan ikisinin çözümü burada:

    - **Birebir tekrar** → birleştirilir, bağlantılar kalan kayda taşınır.
    - **Birleşik kayıt** (`İHA, DHA`) → çoklu seçim geldiği için artık
      gerekmiyor; kayıt pasife alınır ve haberde iki kaynak işaretlenir.

    Üçüncüsü (muhabir/yayın karışıklığı) bir **model** kararıdır: "Kendi
    muhabirimiz" kullanıcı tablosundan beslenir, ayrı kaynak kaydı tutulmaz.
    `icerik.Haber.muhabir` alanı bunu zaten karşılıyor.

    **Silme yok.** Birleştirilen kayıt pasife alınır ve `birlesti_ile` ile
    hedefe bağlanır; iz kalır. Kaydı silmek geri alınamaz bir işlemdir ve
    bir editör düğmesinin arkasına konmaz.
    """

    baglantilari_tasi = forms.BooleanField(
        required=False, initial=True, label="Bağlantıları hedefe taşı",
        help_text="Bu kaynağa bağlı haberler hedef kaynağa eklenir ve buradan "
                  "çözülür. Birleştirme seçilmediyse etkisizdir.")

    class Meta:
        model = Kaynak
        fields = ["ad", "tur", "aktif", "birlesti_ile"]
        labels = {"ad": "Kaynak adı", "tur": "Tür",
                  "aktif": "Seçim listesinde göster",
                  "birlesti_ile": "Şu kayda birleştir"}
        help_texts = {
            "tur": "Ajans listesi kapalıdır (§17): AA · DHA · İHA · ANKA.",
            "aktif": "Kapalıyken seçim listesinden düşer; bağlı haberler ve "
                     "bağlantılar durur, kayıt silinmez.",
            "birlesti_ile": "Doldurulursa bu kayıt hedefe birleştirilmiş "
                            "sayılır ve pasife alınır.",
        }

    # M2M taşıması tek seferde değil parça parça yapılıyor: ölçülen en büyük
    # kaynak 92.564 habere bağlı ve tek işlemde taşımak veritabanını uzun
    # süre kilitler. Göç hâlâ aynı dosyaya yazıyor olabilir.
    TASIMA_ADIMI = 500

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["birlesti_ile"].required = False
        secenek = Kaynak.objects.filter(aktif=True)
        if self.instance.pk:
            secenek = secenek.exclude(pk=self.instance.pk)
        self.fields["birlesti_ile"].queryset = secenek.order_by("ad")

    def clean_ad(self):
        ad = (self.cleaned_data.get("ad") or "").strip()
        if not ad:
            raise forms.ValidationError("Kaynak adı zorunludur.")
        return ad

    def clean_birlesti_ile(self):
        hedef = self.cleaned_data.get("birlesti_ile")
        if not hedef or not self.instance.pk:
            return hedef
        if hedef.pk == self.instance.pk:
            raise forms.ValidationError("Kayıt kendine birleştirilemez.")
        # Zincir kurulmasın: A→B→A ya da A→B→C. Hedefin kendisi
        # birleştirilmişse bağlantılar iki kez taşınmak zorunda kalırdı.
        if hedef.birlesti_ile_id:
            raise forms.ValidationError(
                f"“{hedef.ad}” zaten başka bir kayda birleştirilmiş. "
                "Önce zincirin sonundaki kaydı seçin.")
        return hedef

    def save(self, commit=True):
        kaynak = super().save(commit=False)
        hedef = self.cleaned_data.get("birlesti_ile")
        if hedef:
            # Birleştirilen kayıt seçim listesinde kalmamalı.
            kaynak.aktif = False
        if commit:
            kaynak.save()
            if hedef and self.cleaned_data.get("baglantilari_tasi"):
                self.tasinan = self._baglantilari_tasi(kaynak, hedef)
        return kaynak

    @classmethod
    def _baglantilari_tasi(cls, kaynak, hedef) -> int:
        """Haber bağlantılarını hedefe taşır, taşınan sayıyı döndürür."""
        from .models import Haber

        kimlikler = list(Haber.objects.filter(kaynaklar=kaynak)
                         .values_list("pk", flat=True))
        for bas in range(0, len(kimlikler), cls.TASIMA_ADIMI):
            dilim = kimlikler[bas:bas + cls.TASIMA_ADIMI]
            hedef.haberler.add(*dilim)
        kaynak.haberler.clear()
        return len(kimlikler)
