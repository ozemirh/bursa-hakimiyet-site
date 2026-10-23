"""Göç yardımcıları — arşiv JSON'undaki ham değerleri modele çevirir.

Ayrı dosyada duruyorlar çünkü **saf** işlevler: veritabanına dokunmazlar,
Django kurulumuna ihtiyaç duymazlar ve tek tek sınanabilirler. Göç komutu
tekrar tekrar koşacak (tarama sürdükçe), o yüzden buradaki her kural bir
gerileme testine bağlı.
"""

from __future__ import annotations

import re
from datetime import datetime

from django.utils import timezone

# `namik-goz-76` → ("namik-goz", 76). Slug açgözlü olmamalı, yoksa kimliği
# kendi içine katar — `taksonomi/adresler.py`deki KIMLIK kalıbıyla aynı tuzak.
_DILIM = re.compile(r"^(?P<slug>.+?)-(?P<kimlik>\d+)$")

# Adresin sonundaki `-{sayı}` kimliktir; ondan öncesi slug'dır.
_ADRES_SON = re.compile(r"/(?P<slug>[^/]+?)-(?P<kimlik>\d+)/?$")

# ISO: "2021-02-01T10:18:46". Haber, galeri ve yazar aileleri bunu veriyor.
_TARIH = re.compile(r"^(\d{4}-\d{2}-\d{2})[T ](\d{2}):(\d{2})(?::(\d{2}))?")

# Türkçe: "01.03.2021 08:04". ÖLÇÜM (27 Ağustos 2026): köşe ailesindeki 1.500
# örneğin **tamamında** tarih bu biçimde — köşe sayfalarında JSON-LD tarih
# vermiyor, değer görünür metinden okunuyor. Yalnız ISO kabul edilseydi 6.903
# köşe yazısının hepsi yayın zamansız kalır ve `yayindakiler()` hiçbirini
# listelemezdi; sayfaları da 404 olurdu.
_TARIH_TR = re.compile(
    r"^(\d{2})\.(\d{2})\.(\d{4})[T ](\d{2}):(\d{2})(?::(\d{2}))?")

# ISO 8601 süre: PT2M30S · P0DT1H2M3S · PT45S
_ISO_SURE = re.compile(
    r"^P(?:(?P<gun>\d+)D)?T?(?:(?P<saat>\d+)H)?(?:(?P<dakika>\d+)M)?"
    r"(?:(?P<saniye>\d+(?:\.\d+)?)S)?$", re.I)

# "01:02:03" ya da "02:03" — kaynak zaman zaman bu biçimi de veriyor.
#
# ÖLÇÜM (27 Ağustos 2026, 31.084 video): oynatıcı süreyi ÜÇ ayrı biçimde
# yazıyor ve eski kalıp ikisini birden eliyordu.
#   `0:1:2`       — saniye sıfır dolgusuz.  `(\d{2})` iki basamak şart
#                   koştuğu için elendi:  1.518 kayıt.
#   `00:22.0586`  — saniye ONDALIKLI (web.tv oynatıcısının ham değeri).
#                   Nokta kalıpta hiç yoktu:  7.783 kayıt.
# İkisi birlikte 9.301 video süresiz kalıyordu. Ondalık kısım atılır, saniye
# tam sayıya inilir — şablon zaten dakika:saniye basıyor.
# Kalan 5 kayıt `NaN:NaN`; onlar gerçekten bilinmiyor ve 0 doğru cevap.
_SAAT_SURE = re.compile(r"^(?:(\d+):)?(\d{1,2}):(\d{1,2}(?:\.\d+)?)$")


def dilim_ayir(dilim: str) -> tuple[str, int] | tuple[str, None]:
    """`bursa-208` → ("bursa", 208). Çözülemezse (dilim, None).

    Kimliği None dönmek kaydı düşürmez: adres dilimi ham hâliyle saklanıyor,
    yalnız taksonomi bağı kurulamaz.
    """
    esle = _DILIM.match((dilim or "").strip("/"))
    if not esle:
        return (dilim or "", None)
    return esle.group("slug"), int(esle.group("kimlik"))


def adresten_slug_kimlik(url: str) -> tuple[str, int] | tuple[str, None]:
    """Adresin son diliminden (slug, kimlik). Slug **başlıktan üretilmez**."""
    esle = _ADRES_SON.search((url or "").rstrip("/"))
    if not esle:
        return ("", None)
    return esle.group("slug"), int(esle.group("kimlik"))


def zaman(ham: str):
    """ISO benzeri metni yerel saat diliminde bilinçli zamana çevirir.

    İki biçim kabul edilir — ölçüldü, ikisi de arşivde var: ISO
    ("2021-02-01T10:18:46", haber/galeri/yazar) ve Türkçe ("01.03.2021 08:04",
    köşe).

    Ayrıştırılamayan değer None döner; kayıt yine alınır ama listelenmez
    (sıralama yayın zamanına dayanıyor). Sessizce "şimdi" yazmak arşivin
    kronolojisini bozardı.
    """
    metin = str(ham or "").strip()
    if not metin:
        return None

    esle = _TARIH.match(metin)
    if esle:
        tarih = esle.group(1)
        saat, dakika, saniye = esle.group(2), esle.group(3), esle.group(4) or "00"
    else:
        esle = _TARIH_TR.match(metin)
        if not esle:
            return None
        tarih = f"{esle.group(3)}-{esle.group(2)}-{esle.group(1)}"
        saat, dakika, saniye = esle.group(4), esle.group(5), esle.group(6) or "00"

    try:
        naif = datetime.fromisoformat(f"{tarih}T{saat}:{dakika}:{saniye}")
    except ValueError:
        return None
    return timezone.make_aware(naif, timezone.get_default_timezone())


def sure_saniyeye(ham: str) -> int:
    """`PT2M30S` → 150. Çözülemezse 0.

    Sıfır dönmek "süre bilinmiyor" demektir ve şablon o zaman süre basmaz;
    uydurma bir değer koymaktansa boş bırakmak doğrusu.
    """
    metin = (ham or "").strip()
    if not metin:
        return 0

    esle = _ISO_SURE.match(metin)
    if esle and any(esle.groupdict().values()):
        gun = int(esle.group("gun") or 0)
        saat = int(esle.group("saat") or 0)
        dakika = int(esle.group("dakika") or 0)
        saniye = float(esle.group("saniye") or 0)
        return int(gun * 86400 + saat * 3600 + dakika * 60 + saniye)

    esle = _SAAT_SURE.match(metin)
    if esle:
        saat = int(esle.group(1) or 0)
        return saat * 3600 + int(esle.group(2)) * 60 + int(float(esle.group(3)))

    return 0
