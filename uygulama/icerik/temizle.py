"""Haber gövdesini beyaz listeye göre temizler.

Gövde kazımayla geldi ve panelden de HTML girilecek; ikisi de doğrudan
`|safe` ile basılamaz. Burada **izin verilenler dışındaki her şey** düşer —
kara liste değil beyaz liste, çünkü kara liste her zaman eksik kalır.

Ölçüm (26 Ağustos 2026, 92.648 gövde): tehlikeli etiket **0**. Kullanılan
etiketler `p` 658.417 · `strong` 324.525 · `img` 62.934 · `em` 4.626 ·
`a` 2.913 · `b` 29. Yani temizleyici bugünkü arşivi bozmuyor; panelden
gelecek içerik için duruyor.

**`img` bilerek düşürülür.** 2023-07 öncesi görseller sağlayıcı tarafından
sunucudan silindi (URUN-PLANI.md F3 notu); gövdedeki `<img>` etiketleri ölü
adrese bakıyor ve kırık görsel olarak çizilirdi.
"""

from html import escape
from html.parser import HTMLParser
from urllib.parse import urlparse

from django.utils.safestring import mark_safe

# Metni korunan, kendisi geçerli olan etiketler.
IZINLI = {
    "p", "br", "strong", "b", "em", "i", "u",
    "ul", "ol", "li", "h2", "h3", "h4", "blockquote", "a",
}

# Kendi kendine kapanan etiketler.
TEKIL = {"br"}

# Etiketi de içeriği de tamamen atılanlar.
GOMULU_AT = {"script", "style", "iframe", "object", "embed", "form", "noscript"}

# Etiketi atılıp içeriği korunanlar bunların dışında kalan her şeydir
# (ör. `div`, `span`, `font`). `img` içerik taşımadığı için iz bırakmaz.

GUVENLI_SEMA = {"http", "https", "mailto", ""}


class _Temizleyici(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parca = []
        self._at_derinlik = 0
        self._acik = []

    # -- etiketler --
    def handle_starttag(self, etiket, nitelikler):
        if etiket in GOMULU_AT:
            self._at_derinlik += 1
            return
        if self._at_derinlik:
            return
        if etiket not in IZINLI:
            return  # etiketi at, içeriği akmaya devam etsin
        if etiket in TEKIL:
            self.parca.append("<br>")
            return
        if etiket == "a":
            hedef = self._baglanti(nitelikler)
            if hedef is None:
                self._acik.append(None)  # bağlantıyı düz metne indir
                return
            self.parca.append(f'<a href="{escape(hedef, quote=True)}" '
                              f'rel="noopener nofollow">')
            self._acik.append("a")
            return
        self.parca.append(f"<{etiket}>")
        self._acik.append(etiket)

    def handle_endtag(self, etiket):
        if etiket in GOMULU_AT:
            self._at_derinlik = max(0, self._at_derinlik - 1)
            return
        if self._at_derinlik or etiket not in IZINLI or etiket in TEKIL:
            return
        # Yalnızca gerçekten açtığımız etiketi kapat; kaynaktaki fazladan
        # kapanış etiketleri sessizce düşsün.
        if etiket in self._acik:
            while self._acik:
                son = self._acik.pop()
                if son is not None:
                    self.parca.append(f"</{son}>")
                if son == etiket:
                    break

    def handle_data(self, veri):
        if not self._at_derinlik:
            self.parca.append(escape(veri))

    def sonuc(self) -> str:
        while self._acik:
            son = self._acik.pop()
            if son is not None:
                self.parca.append(f"</{son}>")
        return "".join(self.parca)

    @staticmethod
    def _baglanti(nitelikler):
        for ad, deger in nitelikler:
            if ad.lower() != "href" or not deger:
                continue
            hedef = deger.strip()
            if hedef.startswith("/"):
                return hedef
            if urlparse(hedef).scheme.lower() in GUVENLI_SEMA:
                return hedef
            return None
        return None


def govde_temizle(ham: str) -> str:
    """Beyaz listeye indirgenmiş, şablonda `|safe` ile basılabilir HTML."""
    if not ham:
        return ""
    temizleyici = _Temizleyici()
    temizleyici.feed(ham)
    temizleyici.close()
    return mark_safe(temizleyici.sonuc())


# ===========================================================================
# Düz metin alanlarının onarımı — başlık · spot (5 Eylül 2026)
#
# Arşiv eski siteden olduğu gibi alındı ve düz metin alanlarında dört tür
# artık kaldı. Ölçüm (1.038.477 haber + medya aileleri):
#
#   1. ÇÖZÜLMEMİŞ VARLIK KAÇIŞI — `Ug&#774;ur Aslan'dan…` (başlıkta 72,
#      spotta 535). Eski sitenin şablonu bir kez fazla kaçırmış.
#   2. AYRIŞMIŞ HARF — "Atatu" + U+0308. Ekranda ü gibi görünür ama arama
#      ve sıralama için başka bir dizidir (başlıkta 54, spotta 130).
#   3. GÖRÜNMEZ KARAKTER — sıfır genişlikli boşluk, satır ayırıcı, BOM
#      (619 kayıt). Kopyala-yapıştır izi; metni sessizce bozar.
#   4. BOŞLUK ÇEŞİTLERİ — kırılmaz boşluk, dar boşluk. Görünüşte boşluk,
#      eşleşmede değil.
#
# **Gövdeye dokunulmuyor.** Gövde HTML ve orada `&amp;` kaçışı DOĞRUdur;
# çözmek işaretlemeyi bozardı. Bu işlev yalnız düz metin alanları içindir.
#
# U+FFFD (`&#65533;`) ONARILAMAZ: özgün karakter kodlama hatasında zaten
# kaybolmuş, geri getirilemez. Sayılıyor ve raporlanıyor, uydurulmuyor.
# ===========================================================================

import re
import unicodedata
from html import unescape

#: Silinecek görünmez karakterler: sıfır genişlikli boşluk/birleştirici,
#: BOM, satır ve paragraf ayırıcı. KAÇIŞLA yazılıyor — bu karakterlerin
#: kendileri kaynak dosyaya konsaydı satırı bölerlerdi (denendi, bozdu).
GORUNMEZ = re.compile("[​‌‍﻿  ]")

#: Sıradan boşluğa indirilecek boşluk çeşitleri.
BOSLUKLAR = re.compile("[    ⁠]")

#: Kodlama hatasında kaybolmuş karakterin izi. Onarılamaz, sayılır.
KURTARILAMAZ = "�"


def metin_duzelt(ham: str, bosluk: bool = False) -> str:
    """Düz metin alanını (başlık, spot) onarır.

    Sıra önemli: önce kaçış çözülür, sonra NFC ile ayrışmış harfler
    birleşir, sonra görünmezler düşer. Ters sırada `&#776;` henüz bir
    birleşen işarete dönüşmemiş olurdu ve NFC harfi birleştiremezdi.

    **Boşluk düzenlemesi YAPILMAZ** — çift boşluk, baştaki ve sondaki
    boşluk olduğu gibi kalır. Ölçüldü: boşluk da daraltılsaydı arşivde
    37.580 kayıt değişecekti ve çoğu bozuk değil, yalnız fazladan
    boşlukluydu. Bu işlev BOZULMAYI onarır, metni yeniden biçimlendirmez.

    `bosluk=True` ayrıca kırılmaz/dar boşlukları sıradan boşluğa indirir.
    Varsayılan KAPALI: ölçüldü, arşivde 15.950 kayıt yalnız bunun için
    değişirdi ve kırılmaz boşluk ekranda bozuk görünmüyor — yalnız arama
    ve eşleştirmede ayrı bir karakter. Ayrı bir karar, ayrı bayrak.
    """
    if not ham:
        return ham
    metin = unescape(ham)
    metin = unicodedata.normalize("NFC", metin)
    # NFC "i" + U+0307'yi birleştirmez (noktası zaten var). Türkçe "İ"nin
    # yanlış küçültülmesinden kalan bu artık okunurluğu bozuyor: "İngi̇liz".
    metin = metin.replace("i̇", "i")
    metin = GORUNMEZ.sub("", metin)
    return BOSLUKLAR.sub(" ", metin) if bosluk else metin
