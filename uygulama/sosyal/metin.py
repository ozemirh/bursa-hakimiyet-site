"""Gönderi metnini haberden kuran katman.

Metin **kalıptan** üretilir; kalıp hesapta boşsa platformun varsayılanı
kullanılır. Kural motorunun editoryal çizgisi burada da geçerli: gövdeden
cümle kopyalanmaz. Gönderiye yalnız başlık, spot, adres ve etiketler girer —
spot zaten haberin kendi özetidir, uydurulmuş bir cümle değildir.

## Uzunluk ölçüsü karakter sayısı değildir

X'te bağlantı kaç karakter olursa olsun **23** sayılır (t.co kısaltması).
Ham `len()` ile ölçmek, 280 sınırına sığdığını sandığımız gönderinin
reddedilmesi demekti. `olculen_uzunluk` bu farkı kapatıyor.

## Kısaltma sırası

    1. spot kısalır (kelime sınırında, sonuna …)
    2. etiketler sondan düşer
    3. başlık kısalır — en son, çünkü başlık haberin kimliğidir

Instagram'da altyazıya konan bağlantı tıklanmaz; bu yüzden Instagram
kalıbında adres yok, yerine profildeki bağlantıya işaret eden bir cümle
var. Bu bir tercih değil, platformun davranışı.
"""

import re

from django.conf import settings

from .models import SosyalHesap

# Platform kalıpları. Yer tutucular: {baslik} {spot} {adres} {etiketler}
KALIPLAR = {
    SosyalHesap.X: "{baslik}\n\n{adres}\n{etiketler}",
    SosyalHesap.FACEBOOK: "{baslik}\n\n{spot}\n\n{adres}",
    SosyalHesap.INSTAGRAM: (
        "{baslik}\n\n{spot}\n\n"
        "Haberin tamamı profilimizdeki bağlantıda.\n\n{etiketler}"),
    SosyalHesap.YOUTUBE: "{baslik}\n\n{spot}\n\nHaberin tamamı: {adres}\n\n{etiketler}",
}

# Platformların yayımlanmış sınırları.
SINIRLAR = {
    SosyalHesap.X: 280,
    SosyalHesap.FACEBOOK: 2000,      # teknik sınır 63.206; okunurluk sınırı bu
    SosyalHesap.INSTAGRAM: 2200,
    SosyalHesap.YOUTUBE: 4900,       # açıklama sınırı 5.000
}

# Kaç etiket basılacağı. X'te iki etiket bile 280'in içinde yer kaplar.
ETIKET_SAYISI = {
    SosyalHesap.X: 2,
    SosyalHesap.FACEBOOK: 3,
    SosyalHesap.INSTAGRAM: 8,
    SosyalHesap.YOUTUBE: 5,
}

# Bağlantının kaç karakter SAYILDIĞI. Yalnız X kısaltıyor.
BAG_OLCUSU = {SosyalHesap.X: 23}

BAG_KALIBI = re.compile(r"https?://\S+")


def _bas_harf(kelime: str) -> str:
    """Türkçe büyük harf: i→İ, ı→I. `str.title()` bunu yanlış yapar."""
    if not kelime:
        return kelime
    ilk = kelime[0]
    buyuk = {"i": "İ", "ı": "I"}.get(ilk, ilk.upper())
    return buyuk + kelime[1:]


def etiket_yaz(ad: str) -> str:
    """"nilüfer çayı" → "#NilüferÇayı". Harf ve rakam dışı her şey düşer."""
    parcalar = [p for p in re.split(r"[^0-9A-Za-zÇĞİÖŞÜçğıöşü]+", ad or "") if p]
    if not parcalar:
        return ""
    return "#" + "".join(_bas_harf(p) for p in parcalar)


def etiketleri_kur(haber, adet: int) -> str:
    if adet <= 0:
        return ""
    yazilan = []
    for ad in haber.etiketler.values_list("ad", flat=True)[:adet]:
        etiket = etiket_yaz(ad)
        if etiket and etiket not in yazilan:
            yazilan.append(etiket)
    return " ".join(yazilan)


#: Platform → `utm_source` (Paket G, 19 Ekim 2026). Sosyal trafik analitikte
#: kanal kanal ayrılsın. Kanonik etiket UTM'siz kalır (icerik/seo.py) ve
#: sayfa önbelleği UTM'yi anahtara katmaz; adres çoğalmaz.
UTM_KAYNAK = {
    SosyalHesap.X: "x",
    SosyalHesap.FACEBOOK: "facebook",
    SosyalHesap.INSTAGRAM: "instagram",
    SosyalHesap.YOUTUBE: "youtube",
}


def utm_ekle(adres: str, platform: str | None) -> str:
    kaynak = UTM_KAYNAK.get(platform or "")
    if not kaynak or not adres:
        return adres
    ayrac = "&" if "?" in adres else "?"
    return f"{adres}{ayrac}utm_source={kaynak}&utm_medium=social"


def haber_adresi(haber, platform: str | None = None) -> str:
    return utm_ekle(settings.SITE_KOKU.rstrip("/") + haber.get_absolute_url(), platform)


def gorsel_adresi(haber) -> str:
    """Haberin görselinin **dışarıdan erişilebilir** adresi.

    Yerel yol (`/arsiv-gorsel/...`) sosyal medyaya verilemez; platform o
    dosyayı kendi sunucusundan çeker. Bu yüzden site kökü ekleniyor.
    Yerelde dosya yoksa boş döner — Instagram bu durumda gönderemez ve
    gönderici bunu hata olarak değil, eksik olarak bildirir.
    """
    yol = haber.gorsel_yolu()
    if not yol:
        return ""
    return settings.SITE_KOKU.rstrip("/") + yol


def olculen_uzunluk(metin: str, platform: str) -> int:
    """Platformun saydığı uzunluk; X'te bağlantılar sabit sayılır."""
    olcu = BAG_OLCUSU.get(platform)
    if not olcu:
        return len(metin)
    toplam = len(metin)
    for bag in BAG_KALIBI.findall(metin):
        toplam += olcu - len(bag)
    return toplam


def _kelimede_kes(metin: str, uzunluk: int) -> str:
    """Kelime sınırında keser, sonuna tek karakterlik … koyar."""
    if uzunluk <= 1:
        return ""
    kirpik = metin[:uzunluk - 1].rstrip()
    bosluk = kirpik.rfind(" ")
    if bosluk > uzunluk // 2:
        kirpik = kirpik[:bosluk]
    return kirpik.rstrip(" ,.;:-") + "…"


def _doldur(kalip: str, baslik: str, spot: str, adres: str, etiketler: str) -> str:
    metin = kalip.format(baslik=baslik, spot=spot, adres=adres,
                         etiketler=etiketler)
    # Boş yer tutucu üç satır boşluk bırakabiliyor; sadeleştir.
    metin = re.sub(r"\n{3,}", "\n\n", metin)
    return metin.strip()


def gonderi_metni(haber, hesap) -> str:
    """Haberi hesabın kalıbına göre yazar ve sınıra sığdırır."""
    platform = hesap.platform
    kalip = (hesap.metin_kalibi or "").strip() or KALIPLAR.get(
        platform, KALIPLAR[SosyalHesap.FACEBOOK])
    sinir = SINIRLAR.get(platform, 2000)

    baslik = (haber.baslik or "").strip()
    spot = (haber.spot or "").strip()
    adres = haber_adresi(haber, platform)
    etiketler = etiketleri_kur(haber, ETIKET_SAYISI.get(platform, 3))

    metin = _doldur(kalip, baslik, spot, adres, etiketler)
    if olculen_uzunluk(metin, platform) <= sinir:
        return metin

    # 1. Spot kısalır.
    if spot:
        fazla = olculen_uzunluk(metin, platform) - sinir
        spot = _kelimede_kes(spot, max(len(spot) - fazla, 0))
        metin = _doldur(kalip, baslik, spot, adres, etiketler)
        if olculen_uzunluk(metin, platform) <= sinir:
            return metin

    # 2. Etiketler sondan düşer.
    while etiketler:
        etiketler = " ".join(etiketler.split(" ")[:-1])
        metin = _doldur(kalip, baslik, spot, adres, etiketler)
        if olculen_uzunluk(metin, platform) <= sinir:
            return metin

    # 3. Başlık kısalır — en son.
    fazla = olculen_uzunluk(metin, platform) - sinir
    baslik = _kelimede_kes(baslik, max(len(baslik) - fazla, 1))
    return _doldur(kalip, baslik, spot, adres, etiketler)


def paylas_adresi(hesap, metin: str, adres: str) -> str:
    """Elle paylaşımda açılacak platform bağlantısı.

    Instagram ve YouTube'un web'den gönderi açan bir adresi **yok**; oralarda
    editör metni kopyalar. Boş dönmek, çalışmayan bir düğme çizmekten iyidir.
    """
    from urllib.parse import quote
    if hesap.platform == SosyalHesap.X:
        return "https://x.com/intent/post?text=" + quote(metin)
    if hesap.platform == SosyalHesap.FACEBOOK:
        return "https://www.facebook.com/sharer/sharer.php?u=" + quote(adres)
    return ""
