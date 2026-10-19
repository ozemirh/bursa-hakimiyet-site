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

import re
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


#: Metinde HTML etiketi var mı: `<p`, `</p`, `<br`, `<!--`. "5 < 6" gibi
#: düz metindeki küçüktür işareti etiket sayılmaz.
_ETIKET_IZI = re.compile(r"<[a-zA-Z/!]")
_BOS_SATIR = re.compile(r"\r?\n[ \t]*\r?\n+")


def duz_metni_paragrafla(ham: str) -> str:
    """Düz metin gövdeyi `<p>` paragraflarına çevirir (Paket H, 19 Ekim 2026).

    Panel formunun gövde alanı düz bir metin kutusu; editör paragrafları boş
    satırla ayırıyor. Temizleyici etiketsiz metni tek parça kaçırıyordu ve
    sayfada tek paragraf görünüyordu (DEGERLENDIRME-2026-10, full stack).

    * **Etiket taşıyan gövdeye dokunulmaz** — arşivin 1 milyon gövdesi HTML.
    * Boş satır paragraf sınırı, tek satır sonu `<br>`.
    * Metin kaçırılır; sonuç yine `govde_temizle`den geçer, yani beyaz
      liste dışına çıkan hiçbir şey üretilmez.

    Yayın kapısının paragraf sayımı (`yayin_kapisi.paragraf_sayisi`) düz
    metinde de boş satırı sayıyor; çeviri o sayıyı değiştirmez.
    """
    if not ham or _ETIKET_IZI.search(ham):
        return ham
    bloklar = [b.strip() for b in _BOS_SATIR.split(ham.strip()) if b.strip()]
    return "".join(
        "<p>" + "<br>".join(escape(s.strip(), quote=False)
                            for s in blok.splitlines() if s.strip()) + "</p>"
        for blok in bloklar)


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


# ===========================================================================
# Gömülü kod — beyaz liste (Paket H, 19 Ekim 2026)
#
# Panelin "Gömülü kod" alanı (§4 alan 23-26) serbest HTML kabul ediyor ve
# sitede hiç okunmuyordu. Ham basmak betik enjeksiyonu demek; panel
# kullanıcısının hesabı ele geçerse okurun tarayıcısı da geçer.
#
# KARAR: kod BASILMAZ, yalnız içinden tanınan üç kalıbın KİMLİĞİ çıkarılır
# ve bağlantı kartı bizim şablonumuzdan kurulur:
#
#     YouTube    embed / watch / shorts / youtu.be → 11 karakterlik video kimliği
#     X          twitter.com|x.com/<hesap>/status/<sayı>
#     Instagram  instagram.com/(p|reel|tv)/<kod>
#
# Gerçek gömme (iframe, platform betiği) YAPILMIYOR: CSP `frame-src 'self'`
# ve betik kökeni yalnız site; üçüncü taraf çerçevesi okurun tarayıcısına
# platform çerezi bırakır (KVKK). İkisi de bu paketin kararı değil —
# → devops-altyapi-muhendisi (CSP) ve hukuk-guvenlik-uyum-uzmani (çerez).
# Kart internetsiz de açılır ve hiçbir dış kaynak yüklemez.
# ===========================================================================

_GOMULU_KALIPLARI = (
    ("youtube", re.compile(
        r"(?:youtube(?:-nocookie)?\.com/(?:embed/|shorts/|watch\?(?:[^\"'\s<>]*&)?v=)"
        r"|youtu\.be/)([A-Za-z0-9_-]{11})(?![A-Za-z0-9_-])", re.I)),
    ("x", re.compile(
        r"(?:twitter|x)\.com/([A-Za-z0-9_]{1,15})/status(?:es)?/(\d{5,25})", re.I)),
    ("instagram", re.compile(
        r"instagram\.com/(p|reel|tv)/([A-Za-z0-9_-]{5,40})", re.I)),
)
GOMULU_EN_COK = 5


def gomulu_kartlari(ham: str) -> list[dict]:
    """Gömülü koddan tanınan içerikler: `[{"tur", "adres", "etiket"}]`.

    Tanınmayan her şey düşer. Adres girdiden kopyalanmaz, kimlikten
    yeniden kurulur — nitelik enjeksiyonu yolu kalmaz.
    """
    if not ham:
        return []
    kartlar, gorulen = [], set()
    for tur, kalip in _GOMULU_KALIPLARI:
        for m in kalip.finditer(ham):
            if tur == "youtube":
                adres = f"https://www.youtube.com/watch?v={m.group(1)}"
                etiket = "Videoyu YouTube'da izleyin"
            elif tur == "x":
                adres = f"https://x.com/{m.group(1)}/status/{m.group(2)}"
                etiket = f"@{m.group(1)} gönderisini X'te görün"
            else:
                adres = f"https://www.instagram.com/{m.group(1).lower()}/{m.group(2)}/"
                etiket = "Gönderiyi Instagram'da görün"
            if adres in gorulen:
                continue
            gorulen.add(adres)
            kartlar.append({"tur": tur, "adres": adres, "etiket": etiket})
    return kartlar[:GOMULU_EN_COK]
