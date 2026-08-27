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
