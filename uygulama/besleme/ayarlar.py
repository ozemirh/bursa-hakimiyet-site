"""Besleme ayarları — hepsinin bir varsayılanı var, hiçbiri zorunlu değil.

Bu dosya `cekirdek/settings.py`ye dokunmamak için var. Değerler önce
Django ayarlarında, sonra ortam değişkeninde, sonra buradaki sabitte
aranır. Bağlama adımında `settings.py`ye `SITE_KOKU = ...` yazmak
yeterlidir; ortam değişkeni de aynı işi görür.
"""

import os

from django.conf import settings

# Canlı sitenin kanonik kökü. Sitemap ve RSS **mutlak adres** ister;
# göreli adres kabul edilmez. Varsayılan canlı alan adıdır, çünkü F8
# kesim ölçütü "adres sayıları kaynağıyla eşleşiyor" diyor: üretilen
# adresler kaynaktakiyle harf harf karşılaştırılabilmeli.
VARSAYILAN_SITE_KOKU = "https://www.bursahakimiyet.com.tr"

# Google News sitemap'inde geçen yayın adı ve dili (canlı dosyadan ölçüldü).
VARSAYILAN_YAYIN_ADI = "Bursa Hakimiyet"
VARSAYILAN_DIL = "tr"

# RSS kanal başlığı ve açıklaması — canlı /rss adresinden birebir alındı.
VARSAYILAN_RSS_BASLIK = "Bursa Hakimiyet"
VARSAYILAN_RSS_ACIKLAMA = (
    "Bursa Haberleri, Bursaspor Haberleri, Bursa Son Dakika Haberleri, "
    "bursa Hava Durumu, Bursa Trafik Kazası, Bursa Bölge Haberleri"
)

# Canlı /rss 60 kalem döndürüyor; okuyucular bunu yıllardır böyle görüyor.
VARSAYILAN_RSS_ADET = 60

# Üretilen dosyaların yazılacağı klasör. Canlı sitede bu dosyalar
# statiktir (`/static/sitemap/`); 556.824 adresi her tarayıcı isteğinde
# yeniden üretmek anlamsız. Yönetim komutu buraya yazar, web sunucusu
# oradan servis eder.
VARSAYILAN_CIKTI_ALT_YOLU = "statik/sitemap"


def _oku(ad: str, ortam: str, varsayilan):
    """Önce Django ayarı, sonra ortam değişkeni, sonra sabit."""
    if hasattr(settings, ad):
        return getattr(settings, ad)
    return os.environ.get(ortam) or varsayilan


def site_koku(istek=None) -> str:
    """Adreslerin başına konacak `https://alan.adi` parçası.

    `istek` verilirse ve hiçbir ayar yoksa isteğin kendi konağı kullanılır;
    geliştirmede `http://127.0.0.1:8000` çıkar ve sayfa yine tutarlıdır.
    """
    deger = None
    if hasattr(settings, "SITE_KOKU"):
        deger = settings.SITE_KOKU
    else:
        deger = os.environ.get("BH_SITE_KOKU")
    if deger:
        return deger.rstrip("/")
    if istek is not None:
        return f"{'https' if istek.is_secure() else 'http'}://{istek.get_host()}"
    return VARSAYILAN_SITE_KOKU


def yayin_adi() -> str:
    return _oku("BESLEME_YAYIN_ADI", "BH_YAYIN_ADI", VARSAYILAN_YAYIN_ADI)


def dil() -> str:
    return _oku("BESLEME_DIL", "BH_YAYIN_DILI", VARSAYILAN_DIL)


def rss_baslik() -> str:
    return _oku("BESLEME_RSS_BASLIK", "BH_RSS_BASLIK", VARSAYILAN_RSS_BASLIK)


def rss_aciklama() -> str:
    return _oku("BESLEME_RSS_ACIKLAMA", "BH_RSS_ACIKLAMA", VARSAYILAN_RSS_ACIKLAMA)


def rss_adet() -> int:
    return int(_oku("BESLEME_RSS_ADET", "BH_RSS_ADET", VARSAYILAN_RSS_ADET))


def rss_tam_metin() -> bool:
    """Beslemede tam metin mi, yalnız spot mu.

    Varsayılan **tam metin**: canlı besleme yıllardır böyle ve okuyucu
    tarafında beklenti bu. Yayın tam metni kapatmak isterse ayar ya da
    `BH_RSS_TAM_METIN=0` yeter — kod değişikliği gerekmez.
    """
    deger = _oku("BESLEME_RSS_TAM_METIN", "BH_RSS_TAM_METIN", True)
    if isinstance(deger, str):
        return deger.strip() not in ("0", "", "hayir", "hayır", "false", "False")
    return bool(deger)


def cikti_koku_yolu():
    """Yönetim komutunun varsayılan çıktı klasörü."""
    from pathlib import Path

    ozel = _oku("BESLEME_CIKTI_KOKU", "BH_SITE_HARITASI_KOK", None)
    if ozel:
        return Path(ozel)
    return Path(settings.BASE_DIR) / VARSAYILAN_CIKTI_ALT_YOLU
