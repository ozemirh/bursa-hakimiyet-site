"""RSS beslemeleri — genel akış ve kategori akışı.

**Burada Django'nun `contrib.syndication`'ı kullanılıyor**, sitemap
tarafının aksine. Sebep ölçek: besleme 60 kalem (canlı `/rss` adresinden
ölçüldü), sitemap 556.824 adres. 60 kalemde belleğe alma sorunu yok ve
RSS 2.0'ın can sıkıcı ayrıntısını — RFC 822 `pubDate`, `guid` kuralları,
kaçış — kütüphane doğru yapıyor. Kendi yazmak, hazır çözümü yeniden
üretmek olurdu.

Canlı beslemeden ölçülenler (27 Ağustos 2026):

- Adres `/rss`, tek besleme. `?kategori=spor` parametresi **yok sayılıyor**
  (aynı 162.880 baytlık gövde dönüyor), `/rss/spor` ise 404. Kategori
  beslemesi bu yüzden **yeni**; kimseyi kırmıyor, boşluğu dolduruyor.
- Kanal `sy:updatePeriod hourly` + `sy:updateFrequency 2` bildiriyor.
- Kalem sırası: guid · category · title · media:content · description ·
  pubDate · link · atom:link.
- `guid isPermaLink="false"` değeri `1697447-a91091f5b65ed9c76d27c2eac39b8a76`
  biçiminde ve **çözüldü**: `{kimlik}-{md5(kimlik)}`. Birebir aynı
  üretiliyor, çünkü guid değişirse okuyucular bütün arşivi "yeni" sanıp
  yeniden gösterir.

Tek bilinçli ayrım: canlı besleme metinleri `<![CDATA[…]]>` içine
koyuyor, Django kaçış (`&amp;`) kullanıyor. RSS okuyucusu için ikisi
aynı şey; Django'nun XML yazıcısını CDATA'ya zorlamak, kazandırdığından
çok kırılganlık getirirdi.
"""

from __future__ import annotations

import hashlib

from django.contrib.syndication.views import Feed
from django.http import Http404
from django.utils.feedgenerator import Rss201rev2Feed

from icerik.models import Haber
from taksonomi.models import Kategori

from . import ayarlar


def guid_uret(kimlik: int) -> str:
    """`1697447-a91091f5b65ed9c76d27c2eac39b8a76`.

    Canlı beslemedeki değerle birebir: kimliğin ondalık gösteriminin
    MD5'i. Doğrulandı — `md5(b"1697447")` canlı guid'in ikinci parçasını
    veriyor. Burada MD5 **özet değil kimlik** olarak kullanılıyor;
    güvenlik iddiası yok.
    """
    ozet = hashlib.md5(str(kimlik).encode("utf-8")).hexdigest()
    return f"{kimlik}-{ozet}"


class HakimiyetRss(Rss201rev2Feed):
    """Canlı beslemenin ad alanlarını ve iki ek etiketini ekler."""

    def rss_attributes(self):
        nitelikler = super().rss_attributes()
        nitelikler.update({
            "xmlns:media": "http://search.yahoo.com/mrss/",
            "xmlns:content": "http://purl.org/rss/1.0/modules/content/",
            "xmlns:dc": "http://purl.org/dc/elements/1.1/",
            "xmlns:sy": "http://purl.org/rss/1.0/modules/syndication/",
        })
        return nitelikler

    def add_root_elements(self, handler):
        super().add_root_elements(handler)
        # Okuyuculara "saatte iki kez bak" diyor. Canlı beslemede de var;
        # tarama sıklığını okuyucu tarafında dengeliyor.
        handler.addQuickElement("sy:updatePeriod", "hourly")
        handler.addQuickElement("sy:updateFrequency", "2")

    def add_item_elements(self, handler, item):
        super().add_item_elements(handler, item)
        gorsel = item.get("gorsel_adresi")
        if gorsel:
            # `media:content`, `enclosure`dan farklı olarak dosya boyutu
            # istemiyor. Arşivdeki görsellerin boyutu veritabanında yok;
            # `enclosure` kullansaydık uydurma bir `length` yazmak
            # gerekirdi (bkz. proje kuralı: uydurma veri yok).
            handler.addQuickElement("media:content", "", {
                "url": gorsel,
                "type": item.get("gorsel_turu") or "image/jpeg",
            })


class TemelBesleme(Feed):
    """Genel ve kategori beslemesinin ortak gövdesi."""

    feed_type = HakimiyetRss

    # Dil bilerek ayarlanmıyor: Django `settings.LANGUAGE_CODE`’a
    # (bu projede "tr") düşüyor. Paylaşılan `Feed` örneğine istek başına
    # değer yazmak yarış koşuludur; kazancı da yok.

    # -- kanal --

    def link(self, obj=None):
        return ayarlar.site_koku()

    # -- kalemler --

    def _liste(self):
        """Beslemeye girecek haberler.

        `rss` alanı §4 alan sözleşmesinden geliyor: editör tek tek haberi
        beslemeden çıkarabiliyor. Sayfada görünüp beslemede görünmemesi
        gereken haber var, tersi yok.

        `kategori__turler` ön çekimi adres kurmak için gerekli
        (`get_absolute_url` slug'ı oradan okuyor).
        """
        return (Haber.yayindakiler()
                .filter(rss=True)
                .select_related("kategori")
                .prefetch_related("kategori__turler")
                .order_by("-yayin_zamani"))

    def item_title(self, haber):
        return haber.baslik

    def item_description(self, haber):
        """Spot + temizlenmiş gövde.

        Canlı besleme tam metin veriyor; aynısı korunuyor. Yayın tam metni
        kapatmak isterse `BESLEME_RSS_TAM_METIN = False` yeter — o zaman
        yalnız spot gider.
        """
        spot = f"<p>{haber.spot}</p>" if haber.spot else ""
        if not ayarlar.rss_tam_metin():
            return spot or haber.baslik
        return spot + haber.govde_guvenli()

    def item_link(self, haber):
        # Mutlak adres: Django `add_domain` ile alan adı eklemeye çalışır,
        # ama `django.contrib.sites` kurulu değil ve istek konağı
        # geliştirmede 127.0.0.1 olur. Kanonik kök tek yerden geliyor.
        return f"{ayarlar.site_koku()}{haber.get_absolute_url()}"

    def item_guid(self, haber):
        return guid_uret(haber.id)

    item_guid_is_permalink = False

    def item_pubdate(self, haber):
        return haber.yayin_zamani

    def item_updateddate(self, haber):
        return haber.guncelleme_zamani or haber.yayin_zamani

    def item_categories(self, haber):
        return [haber.kategori.ad]

    def item_extra_kwargs(self, haber):
        """Görsel yalnız **yerelde dosyası olan** haberde verilir.

        `gorsel_yolu()` bunu zaten uyguluyor: 2023-07 öncesi görseller
        kaynak sunucudan silinmiş, `gorsel_url` yalnız iz. Beslemeye ölü
        adres koymak okuyucularda kırık görsel demek.
        """
        yol = haber.gorsel_yolu()
        if not yol:
            return {}
        return {
            "gorsel_adresi": f"{ayarlar.site_koku()}{yol}",
            "gorsel_turu": "image/webp" if yol.endswith(".webp") else "image/jpeg",
        }


class GenelBesleme(TemelBesleme):
    """`/rss` — sitenin tamamı."""

    def title(self, obj=None):
        return ayarlar.rss_baslik()

    def description(self, obj=None):
        return ayarlar.rss_aciklama()

    def feed_url(self, obj=None):
        return f"{ayarlar.site_koku()}/rss"

    def items(self):
        return self._liste()[:ayarlar.rss_adet()]


class KategoriBeslemesi(TemelBesleme):
    """`/rss/<kategori-slug>` — tek kategori.

    Slug **tür satırından** okunur, kategori adından değil: aynı
    kategorinin haber/video/foto slug'ı farklı olabiliyor
    (`bursa-da-spor` · `bursada-spor`) ve besleme haber ailesine ait.
    """

    def get_object(self, request, slug):
        kategori = (Kategori.objects
                    .filter(turler__tur=Kategori.TUR_HABER,
                            turler__slug=slug, aktif=True)
                    .first())
        if kategori is None:
            raise Http404("Kategori yok.")
        return kategori

    def title(self, kategori):
        return f"{ayarlar.rss_baslik()} — {kategori.ad}"

    def description(self, kategori):
        return f"{kategori.ad} kategorisindeki son haberler."

    def link(self, kategori):
        return f"{ayarlar.site_koku()}/{kategori.slug_al()}"

    def feed_url(self, kategori):
        return f"{ayarlar.site_koku()}/rss/{kategori.slug_al()}"

    def items(self, kategori):
        return self._liste().filter(kategori=kategori)[:ayarlar.rss_adet()]
