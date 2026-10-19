"""SEO şablon etiketleri (Paket G, 19 Ekim 2026).

    {% load seo_etiket %}
    {% blok_tekrar "aciklama" %}                      aynı bloğu ikinci kez basar
    <script type="application/ld+json">{% jsonld "haber" haber %}</script>
    <script type="application/ld+json">{% jsonld_kirinti "Ekonomi" "/ekonomi" %}</script>

`blok_tekrar`: `<meta name="description">` bir kez yazılır, `og:description`
ve `twitter:description` aynı metni ister. Django bir bloğu iki kez
basamaz; etiket o bloğun en alt şablondaki hâlini yeniden çizer. Böylece her
sayfa açıklamasını **tek yerde** yazar, üç etiket ayrışmaz.

JSON-LD çıktısı `jsonld.betik_json`dan gelir (kaçışlı, güvenli işaretli);
bu modülde `mark_safe` yok.
"""

from django import template
from django.template.loader_tags import BLOCK_CONTEXT_KEY

from icerik import seo
from icerik.jsonld import betik_json

register = template.Library()


@register.simple_tag(takes_context=True)
def blok_tekrar(context, ad):
    blok_baglami = context.render_context.get(BLOCK_CONTEXT_KEY)
    if blok_baglami is None:
        return ""
    blok = blok_baglami.get_block(ad)
    if blok is None:
        return ""
    with context.push():
        context["block"] = blok
        return blok.nodelist.render(context)


#: Şablondan çağrılabilecek kurucular. Beyaz liste: şablon rastgele işlev
#: adı veremez.
KURUCULAR = {
    "haber": seo.haber_makalesi,
    "haber_kirinti": seo.haber_kirintisi,
    "kose": seo.kose_makalesi,
    "kose_kirinti": seo.kose_kirintisi,
    "yazar": seo.yazar_profili,
    "galeri": seo.galeri_sayfasi,
    "video": seo.video_sayfasi,
    "kurulus": seo.kurulus,
    "site": seo.web_sitesi,
}


@register.simple_tag
def jsonld(tur, *argumanlar):
    return betik_json(KURUCULAR[tur](*argumanlar))


@register.simple_tag
def jsonld_kirinti(*ad_yol):
    """Anasayfa kendiliğinden başa eklenir: `"Ekonomi" "/ekonomi" ...`."""
    ciftler = [("Anasayfa", "/")]
    ciftler += [(ad_yol[i], ad_yol[i + 1]) for i in range(0, len(ad_yol) - 1, 2)]
    return betik_json(seo.kirinti(ciftler))


@register.simple_tag
def jsonld_medya_kirinti(kayit, bolum_ad, bolum_yol):
    return betik_json(seo.medya_kirintisi(kayit, bolum_ad, bolum_yol))


@register.filter
def mutlak_adres(yol):
    return seo.mutlak(str(yol or ""))


@register.filter
def og_alt(nesne):
    """og:image:alt — anlamlı alt metin, yoksa başlık, yoksa ad (yazar)."""
    from icerik.templatetags.gorsel_etiket import anlamli
    return (anlamli(getattr(nesne, "gorsel_alt", ""))
            or getattr(nesne, "baslik", "") or getattr(nesne, "ad", "")
            or seo.SITE_ADI)


@register.filter
def guncelleme(kayit):
    """Yayından en az bir dakika sonraki güncelleme zamanı; yoksa None."""
    return seo.degisiklik_zamani(kayit)


@register.filter
def ince_konu(konu):
    return seo.ince_konu_mu(konu)


@register.simple_tag
def robots_kapali():
    return seo.ROBOTS_KAPALI
