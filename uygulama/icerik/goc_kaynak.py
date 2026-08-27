"""Göçte kaynak adının kabul kapısı.

Arşivdeki `kaynak` alanı **güvenilmez**. Kazıyıcı iki yerden okuyor ve ikisi de
yanılıyor:

1. `disa-aktarim/site_arsivleyici.py` → `_KAYNAK_P` = `<p>Kaynak:([^<]{2,40})</p>`
2. `arac/ayiklayici.py` → `asil_kaynak_bul()` → `_KAYNAK_SATIRI` =
   `[Kk]aynak\\s*[:\\-–]\\s*([...]{2,40})`

İkinci kalıp Türkçedeki **"kaynak" sözcüğünün kendisini** yakalıyor: ayırıcı
olarak tireyi de kabul ettiği için "kaynak suyu", "kaynak-kodu" gibi sıradan
tamlamalar kaynak adı sanılıyor. `{2,40}` üst sınırı da açgözlü olduğundan,
gövde metninde geçen bir "Kaynak:" ifadesinden sonra **tam 40 karakter** kesip
alıyor — tabloda cümle ortasında biten kayıtların imzası bu.

ÖLÇÜM (27 Ağustos 2026, 271.205 haber · 148 kaynak kaydı · 271.200 bağ):

    meta yazar degeri ("Haber Merkezi")     1 kayit   270.508 bag   %99,74
    gecerli gorunuyor                      53 kayit       563 bag   % 0,21
    buyuk harfsiz (cumle parcasi)          66 kayit        95 bag
    salt sayi                              11 kayit        11 bag
    40 karakterde kesik                    10 kayit        10 bag
    alan adi                                4 kayit         7 bag
    kendi yayinimiz                         3 kayit         6 bag

En ağır kalem bir ayıklama hatası değil, bir **alan karışıklığı**: canlı sitenin
şablonu `articleAuthor` (Meta Yazar Bilgisi) değerini "Kaynak" etiketiyle
basıyor. "Haber Merkezi" `PANEL-NOTLARI.md` §7'deki altı yasal Meta Yazar
değerinden biridir — "haber merkezinde derlendiyse ve tek bir imzaya
bağlanamıyorsa". Yani ne ajans ne aracı yayın: gazetenin kendi iç künyesi.

`CLAUDE.md` editoryal kuralı — "haberi aldığımız sayfa kendi kaynağını
belirtmişse kaynak odur, aracı yayın kaynak diye anılmaz" — bu değerin Kaynak
bölmesinde görünmesini yasaklar. Reddedilen haber **kaynaksız** kalır; bu bir
kayıp değil, doğrusudur: dış kaynağı zaten yoktur.

Meta yazar bilgisi bilerek atılmıyor, sadece **buraya** yazılmıyor: değer
arşiv JSON'unda duruyor ve modele `meta_yazar` alanı eklendiğinde şema göçüyle
geri doldurulabilir.
"""

from __future__ import annotations

import re

# `PANEL-NOTLARI.md` §7 — Meta Yazar Bilgisi'nin altı yasal değeri.
# Hiçbiri kaynak değildir; kaynak türü değil künye türü belirtirler.
META_YAZAR_DEGERLERI = frozenset({
    "fikir işçisi",
    "bülten",
    "haber ajansı",
    "haber merkezi",
    "içerik aktarımı",
    "alıntı/iktibas",
})

# Kendi yayınımız kaynak diye anılmaz. "Bu rsahakimiyet" ölçülmüş bir boşluk
# hatasıdır, uydurma değil.
KENDI_YAYINIMIZ = frozenset({
    "bursa hakimiyet",
    "bursahakimiyet",
    "bursahakimiyet.com.tr",
    "www.bursahakimiyet.com.tr",
    "bu rsahakimiyet",
})

# Ayıklayıcının üst sınırı; tam bu uzunluk kesilmişliğin imzasıdır.
KESME_UZUNLUGU = 40

_ALAN_ADI = re.compile(
    r"^(?:https?$|https?://|www\.|[a-z0-9-]+\.(?:com|net|org|tr|info)\b)", re.I)


# Python'un `casefold`u "İ"yi i + birleşen nokta yapar; "İçerik Aktarımı"
# böylece "içerik aktarımı" ile eşleşmez ve altı değerin ÜÇÜ kapıdan geçerdi.
# GERİLEME TESTİ: tests_goc.KaynakKabulKapisi.test_meta_yazar_degeri_kaynak_degildir
_KUCULT = {"İ": "i", "I": "ı"}


def _kucult(metin: str) -> str:
    return "".join(_KUCULT.get(c, c) for c in metin).lower()


def kaynak_kabul(ad: str) -> tuple[bool, str]:
    """(kabul_edildi_mi, ret_nedeni). Kabul edilirse neden boş döner.

    Kural sırası ölçüme göre: en çok bağ üreten kalem önce elenir.
    """
    d = " ".join((ad or "").split())
    if not d:
        return False, "bos"

    k = _kucult(d)
    if k in META_YAZAR_DEGERLERI:
        return False, "meta yazar degeri"
    if k in KENDI_YAYINIMIZ:
        return False, "kendi yayinimiz"
    if d.isdigit():
        return False, "salt sayi"
    if " " not in d and _ALAN_ADI.match(d):
        return False, "alan adi"
    if len(d) == KESME_UZUNLUGU:
        # ÖLÇÜLDÜ: bugünkü 10 kaydın onu da cümle ortasında bitiyor. Tam 40
        # karakterlik gerçek bir yayın adı gelirse bu kural onu da eler;
        # sayısı raporlanıyor ki bedeli görünsün.
        return False, "40 karakterde kesik"
    if not any(c.isupper() for c in d):
        # Ajans ve yayın adları Türkçede büyük harfle başlar (AA, İHA, Milliyet).
        # Gövdeden düşen parçalar ise küçük harflidir ("ve", "suyu", "aktardi").
        return False, "buyuk harfsiz (cumle parcasi)"
    return True, ""
