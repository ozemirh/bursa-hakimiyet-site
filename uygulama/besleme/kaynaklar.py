"""Ailelerin veri kaynakları.

Bugün deftere yazılan tek aile **haber** (`icerik.Haber`, 92.666 kayıt).
Diğer dört aile — köşe yazısı, video, foto galeri, yazar — `uygulama/medya/`
altında ayrı yazılıyor. Bu dosya onlara **bağımlı değildir** ve adlarını
bile geçmez: uygulama hazır olurken her uygulamanın `besleme_kaynaklari`
modülü aranıp içe aktarılıyor (Django'nun `admin.autodiscover`
düzeninin aynısı). O modül `aile_kaydet()` çağırdığı anda aile
indekse ve üretime girer; burada tek satır değişmez.

Örnek — `medya/besleme_kaynaklari.py` böyle bir şey olur:

    from besleme.kaynaklar import zamanli_aile
    from besleme.aileler import aile_kaydet
    from .models import KoseYazisi

    def _sorgu():
        return KoseYazisi.yayindakiler().select_related("yazar")

    aile_kaydet(zamanli_aile("kose", "articles", "köşe yazısı", _sorgu))

`zamanli_aile` sözleşmesi: sorgunun kayıtlarında `yayin_zamani` ve
`get_absolute_url()` bulunmalı; `guncelleme_zamani` ile `baslik` varsa
kullanılır, yoksa atlanır. `medya` modelleri (`ArsivIcerigi` soyu) bu
sözleşmeyi zaten karşılıyor.

**Yazar ailesi ayrık.** `authors_YYYY-MM.xml` dosyaları var (canlı
indekste 17 dosya) ama yazar sayfasının bir "yayın anı" yok; o aile
`aylar()` ve `kayitlar()` işlevlerini kendi yazmalı. `zamanli_aile`
oraya uymaz.

**Performans notu (ölçüldü, 27 Ağustos 2026).** Aylık sorgu
`WHERE durum=1 AND yayin_zamani >= ? AND < ? ORDER BY yayin_zamani DESC`
biçiminde. SQLite'ın planlayıcısı istatistik yokken `durum` dizinini
seçip her ay için bütün tabloyu tarıyor: bir ay **0,32 sn**.
`yayin_zamani` dizini kullanıldığında aynı ay **0,06 sn** — 5 kat fark.
`ANALYZE` bir kez çalıştırılınca planlayıcı doğru dizini kendi seçiyor
(556.824 satırlık denemede 0,129 → 0,014 sn), o yüzden yönetim komutu
üretimden önce `ANALYZE` çağırıyor. Burada `INDEXED BY` ile dizin
**zorlanmıyor**: o sözdizimi yalnız SQLite'ta var ve veritabanı
değişince sessizce kırılır.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Callable, Iterator

from django.db.models import Count, Max
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.utils.module_loading import autodiscover_modules

from icerik.models import Haber

from .aileler import Aile, AyOzeti, Kayit, aile_kaydet
from .zaman import ay_adi, ay_dizisi, ay_sinirlari


# -- genel üretici --------------------------------------------------------

def _kayda_cevir(nesne) -> Kayit:
    """Model nesnesini sitemap kaydına indirger.

    `lastmod` güncelleme varsa onu söyler, yoksa yayın anını: arama
    motoru bu alana bakıp yeniden taramaya karar veriyor.
    """
    return Kayit(
        yol=nesne.get_absolute_url(),
        son_degisiklik=getattr(nesne, "guncelleme_zamani", None) or nesne.yayin_zamani,
        yayin=nesne.yayin_zamani,
        baslik=getattr(nesne, "baslik", "") or "",
    )


def zamanli_aile(anahtar: str, dosya_oneki: str, ad: str,
                 sorgu_ureteci: Callable[[], object],
                 son_kayit_verir: bool = False) -> Aile:
    """`yayin_zamani` üzerinden aylara bölünen bir aile kurar.

    Beş ailenin dördü (haber · köşe · video · galeri) bu kalıba uyuyor;
    aralarındaki tek fark model ve adres deseni, ikisi de
    `get_absolute_url()` içinde. Aynı kodu dört kez yazmamak için buradan
    üretiliyor.
    """

    def aylar() -> list[AyOzeti]:
        """Dolu aylar, adres sayıları ve son değişiklik anları.

        Yol: en eski ve en yeni kaydın anı okunur (iki dizinli sorgu),
        aradaki her ay için tek bir `COUNT` + `MAX` çalıştırılır, adedi
        sıfır olan ay listeye girmez. Canlı indeks de yalnız dolu ayları
        içeriyor.

        **Neden `TruncMonth` ile tek grup sorgusu değil.** Denendi ve
        ölçüldü (27 Ağustos 2026, 92.666 kayıt): `TruncMonth(tzinfo=…)`
        SQLite'ta yerleşik değil, Django her satır için Python tarafında
        bir kullanıcı işlevi çağırıyor — ay özeti tek başına **9,4 sn**
        sürüyordu ve tam arşivde (556.824) altı katına çıkardı. Aylık
        aralık sorgusu ise `yayin_zamani` dizinini kullanıyor: ay başına
        ~0,04 sn, on iki ay **0,4 sn**. Sorgu sayısı arttı, süre düştü.

        `Coalesce` şart: güncelleme zamanı arşiv kayıtlarının çoğunda boş
        ve düz `Max("guncelleme_zamani")` o ayları `None` döndürür.
        """
        # Ön çekim ve birleştirme özet sorgusunda yalnız yük: adres
        # kurulmuyor, kategori okunmuyor.
        hafif = sorgu_ureteci().select_related(None).prefetch_related(None)
        anlar = hafif.order_by("yayin_zamani").values_list("yayin_zamani", flat=True)
        ilk = anlar.first()
        if ilk is None:
            return []
        son_an = hafif.order_by("-yayin_zamani").values_list(
            "yayin_zamani", flat=True).first()

        ozetler: list[AyOzeti] = []
        for ay in ay_dizisi(ay_adi(ilk), ay_adi(son_an)):
            bas, bit = ay_sinirlari(ay)
            satir = (hafif.filter(yayin_zamani__gte=bas, yayin_zamani__lt=bit)
                     .aggregate(adet=Count("id"),
                                son=Max(Coalesce("guncelleme_zamani",
                                                 "yayin_zamani"))))
            if satir["adet"]:
                ozetler.append(AyOzeti(ay, satir["adet"], satir["son"]))
        ozetler.reverse()  # yeniden eskiye — canlı indeksteki sıra
        return ozetler

    def kayitlar(ay: str) -> Iterator[Kayit]:
        """Bir ayın kayıtları, akış hâlinde.

        `iterator()` şart: bir ay ortalama ~8.500, en yoğun ay ~15.000
        kayıt ve Django varsayılanı bütün sonucu belleğe alıp önbelleğe
        koyuyor. `chunk_size` sürücüden gelen satırları öbekliyor; ön
        çekim (prefetch) de öbek başına bir kez çalışıyor.

        Sıralama `-yayin_zamani`: dizinin doğal sırası, ek sıralama
        maliyeti yok. sitemaps.org dosya içi sıra şartı koymuyor, canlı
        dosyalar da zaten yeniden eskiye dizili.
        """
        bas, son = ay_sinirlari(ay)
        sorgu = (sorgu_ureteci()
                 .filter(yayin_zamani__gte=bas, yayin_zamani__lt=son)
                 .order_by("-yayin_zamani"))
        for nesne in sorgu.iterator(chunk_size=2000):
            yield _kayda_cevir(nesne)

    def son_kayitlar(saat: int = 48) -> Iterator[Kayit]:
        """Google News sitemap'i için son N saatin kayıtları.

        Google News yalnız **son iki günü** kabul ediyor; daha eskisi
        dosyayı şişirmekten başka işe yaramaz. Canlı `googleNews.xml`
        ölçüldüğünde 473 adres içeriyordu.
        """
        esik = timezone.now() - timedelta(hours=saat)
        sorgu = (sorgu_ureteci()
                 .filter(yayin_zamani__gte=esik)
                 .order_by("-yayin_zamani"))
        for nesne in sorgu.iterator(chunk_size=500):
            yield _kayda_cevir(nesne)

    return Aile(anahtar=anahtar, dosya_oneki=dosya_oneki, ad=ad,
                aylar=aylar, kayitlar=kayitlar,
                son_kayitlar=son_kayitlar if son_kayit_verir else None)


# -- haber ailesi ---------------------------------------------------------

def haber_sorgusu():
    """Sitemap'e girecek haberler.

    `Haber.yayindakiler()` tek doğruluk kaynağıdır: Aktif olmayan (Pasif ·
    Silinmiş · Arşiv) ve yayın zamanı olmayan kayıtlar sayfada da
    görünmüyor, sitemap'te de görünmemeli — arama motoruna 404 vaat etmek
    en pahalı hatadır.

    `kategori__turler` ön çekimi şart: adres `get_absolute_url()` içinden
    kategorinin haber slug'ını okuyor. Ön çekim olmadan haber başına bir
    sorgu daha açılır; 556.824 kayıtta bu tek başına saatler eder.
    """
    return (Haber.yayindakiler()
            .select_related("kategori")
            .prefetch_related("kategori__turler"))


HABER = zamanli_aile("haber", "news", "haber", haber_sorgusu,
                     son_kayit_verir=True)

aile_kaydet(HABER)

# Diğer aileler kendi uygulamalarından katılır. Modül yoksa Django
# sessizce geçer; modül varsa içindeki hata **yükselir** — sessizce eksik
# sitemap üretmek, gürültülü çökmekten kötüdür.
autodiscover_modules("besleme_kaynaklari")
