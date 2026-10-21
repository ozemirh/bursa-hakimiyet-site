"""Türkçe alfabe sıralaması — uygulamalar arası ortak anahtar.

`sorted` varsayılanı "İ"yi "Z"den sonraya atıyor, "Ç"yi "C"den uzağa
koyuyor. Küçük bir alfabe yeter; `locale` kurmak sunucunun diline bağımlılık
olurdu. İlk kullanıcı nöbetçi eczane ilçe listesiydi (`icerik/canli.py`,
eski adıyla `_tr_sirala` orada duruyor ve buraya bağlı); 21 Ekim 2026'da
köşe yazıları sayfasının yazar dizini de aynı anahtarı istedi, bu yüzden
ortak yere taşındı.
"""

TR_ALFABE = "aâbcçdefgğhıiîjklmnoöprsştuüvyz"
TR_KUCULT = str.maketrans("IİÎÂ", "ıiîâ")


def tr_sirala(metin: str) -> tuple:
    """Sıralama anahtarı: harf başına alfabedeki yer; alfabe dışı karakter
    (boşluk, rakam, noktalama) en sona."""
    kucuk = (metin or "").translate(TR_KUCULT).lower()
    return tuple(TR_ALFABE.find(h) if h in TR_ALFABE else len(TR_ALFABE)
                 for h in kucuk)
