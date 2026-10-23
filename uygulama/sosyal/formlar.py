"""Sosyal hesap ve gönderi formları.

## Gizli alanlar geri gösterilmez

Jeton alanları formda **boş** doğar ve boş bırakılırsa kayıtlı değer
korunur. Ekrana basılmayan bir jeton, ekran görüntüsünde, tarayıcı
geçmişinde ve omuz üstünden bakan gözde yoktur. Değerin girilmiş olup
olmadığı ayrıca yazılıyor ki editör "kayıtlı mı" diye tahmin etmesin.

Anahtar alanları **yalnız hesap düzenleme ekranında** çıkar: yeni hesapta
platform daha seçilmemişken hangi alanların isteneceği bilinemez. Önce
hesap tanımlanır, sonra anahtar girilir.
"""

from django import forms

from .models import SosyalGonderi, SosyalHesap

GIZLI_ONEK = "gizli_"


class SosyalHesapForm(forms.ModelForm):
    class Meta:
        model = SosyalHesap
        fields = ["platform", "ad", "kullanici_adi", "aktif", "varsayilan",
                  "sira", "metin_kalibi"]
        labels = {
            "platform": "Platform", "ad": "Hesap adı",
            "kullanici_adi": "Kullanıcı adı", "aktif": "Aktif",
            "varsayilan": "Haber formunda işaretli gelsin",
            "sira": "Sıra", "metin_kalibi": "Metin kalıbı",
        }
        widgets = {"metin_kalibi": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.gizli_alanlar = []
        if not self.instance.pk:
            return
        saglayici = self.instance.saglayici()
        for kod, ad in saglayici.gerekli:
            alan_adi = GIZLI_ONEK + kod
            kayitli = bool(self.instance.gizli(kod))
            self.fields[alan_adi] = forms.CharField(
                required=False, label=ad,
                widget=forms.PasswordInput(render_value=False, attrs={
                    "autocomplete": "off",
                    "placeholder": "kayıtlı değeri korumak için boş bırakın"
                    if kayitli else "girilmedi"}),
                help_text=("Kayıtlı. Değiştirmek için yeni değeri yazın."
                           if kayitli else
                           "Girilmedi. Bu alan boşken hesap otomatik "
                           "gönderemez."))
            self.gizli_alanlar.append(alan_adi)

    def save(self, commit=True):
        hesap = super().save(commit=False)
        gizli = dict(hesap.gizli_ayar or {})
        for alan_adi in self.gizli_alanlar:
            deger = (self.cleaned_data.get(alan_adi) or "").strip()
            if deger:
                gizli[alan_adi[len(GIZLI_ONEK):]] = deger
        hesap.gizli_ayar = gizli or None
        if commit:
            hesap.save()
        return hesap


class SosyalGonderiForm(forms.ModelForm):
    """Kuyruk satırının elle düzenlenebilen üç alanı."""

    class Meta:
        model = SosyalGonderi
        fields = ["metin", "gorsel_adres", "dis_adres"]
        labels = {
            "metin": "Gönderi metni",
            "gorsel_adres": "Görsel adresi",
            "dis_adres": "Paylaşımın adresi",
        }
        widgets = {"metin": forms.Textarea(attrs={"rows": 6})}
        help_texts = {
            "gorsel_adres": "Instagram için zorunlu; platform bu adresten "
                            "indirir, yerel yol iş görmez.",
            "dis_adres": "Elle paylaştıysanız gönderinin adresini buraya "
                         "yazın; kayıt böylece tamamlanır.",
        }

    def clean_metin(self):
        from .metin import SINIRLAR, olculen_uzunluk
        metin = (self.cleaned_data.get("metin") or "").strip()
        platform = self.instance.hesap.platform
        sinir = SINIRLAR.get(platform)
        if sinir and olculen_uzunluk(metin, platform) > sinir:
            raise forms.ValidationError(
                f"{self.instance.hesap.get_platform_display()} sınırı {sinir} "
                f"karakter; bu metin {olculen_uzunluk(metin, platform)} "
                "sayılıyor (X'te bağlantı 23 karakter sayılır).")
        return metin


class YeniGonderiForm(forms.Form):
    """Kuyruğa elle satır açma — YouTube videosu bu yoldan girer."""

    haber_kimligi = forms.IntegerField(
        label="Haber kimliği",
        help_text="Akış ekranındaki köşeli parantez içindeki sayı.")
    hesap = forms.ModelChoiceField(
        queryset=SosyalHesap.objects.filter(aktif=True), label="Hesap")

    def clean_haber_kimligi(self):
        from icerik.models import Haber
        kimlik = self.cleaned_data["haber_kimligi"]
        if not Haber.objects.filter(pk=kimlik).exists():
            raise forms.ValidationError("Bu kimlikte haber yok.")
        return kimlik
