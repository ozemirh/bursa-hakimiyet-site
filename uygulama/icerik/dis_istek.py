"""Dışarıya giden HTTP isteklerinin TEK kapısı — SSRF koruması.

19 Ekim 2026, Paket F madde 3–4. DEGERLENDIRME-2026-10 §3 bulgu 6(b, c):
"Adresten taslak" ekranı editörün yazdığı adresi sunucudan indiriyordu ve
iç ağ (`10.x`, `192.168.x`), yerel makine (`127.0.0.1`) ve bulut üst veri
adresi (`169.254.169.254`) açıktı; boyut sınırı yoktu. Görsel indirme de
`image/svg+xml` ya da uzantısı adresten gelen herhangi bir dosyayı arşiv
köküne yazabiliyordu — SVG/HTML site kökeninde betik çalıştırır.

## Kurallar

1. Yalnız `http` / `https`; kullanıcı adı-parola taşıyan adres yok; port
   80 · 443 · 8080 · 8443.
2. Ad DNS'te ÇÖZÜLDÜKTEN SONRA denetlenir ve bağlantı denetlenen IP'ye
   kurulur (DNS rebinding: denetimden sonra adın başka IP'ye dönmesi işe
   yaramaz). Çözümün TÜM adresleri genel olmalı; biri bile özel / yerel /
   link-local / çoklu yayın / ayrılmış ise istek yapılmaz. IPv4 gömülü
   IPv6 biçimleri (`::ffff:127.0.0.1`, 6to4, NAT64) içindeki adresle
   denetlenir.
3. Yönlendirme otomatik izlenmez; her `Location` aynı denetimden geçer,
   en çok 5 adım.
4. Boyut sınırı hem ham gövdede hem gzip/deflate açılmış hâlde işler
   (sıkıştırma bombası). Varsayılan: HTML 5 MB, görsel 15 MB.
5. Zaman aşımı hem soket işlemi başına hem toplamda.
6. Hata metni editöre gider ve İÇ AYRINTI taşımaz (IP, soket hatası,
   iç ad). Ayrıntı sunucu günlüğüne yazılır.

## Neden standart kütüphane

Bu modül Django içe aktarmaz: `arac/ayiklayici.py` (yerel editör aracı,
`arac/yayinci.py`) de aynı kapıyı dosya yolundan yükleyip kullanır. Kapının
iki kopyası olsaydı biri eninde sonunda gevşerdi.
"""

from __future__ import annotations

import http.client
import ipaddress
import logging
import socket
import ssl
import time
import zlib
from dataclasses import dataclass, field
from urllib.parse import urljoin, urlsplit

gunluk = logging.getLogger("bh.dis_istek")

IZINLI_SEMALAR = ("http", "https")
IZINLI_PORTLAR = frozenset({80, 443, 8080, 8443})
EN_COK_YONLENDIRME = 5
HTML_SINIRI = 5 * 1024 * 1024
GORSEL_SINIRI = 15 * 1024 * 1024
ZAMAN_ASIMI = 20          # soket işlemi başına, saniye
TOPLAM_SURE = 60          # bir isteğin tamamı, saniye
PARCA = 64 * 1024

TARAYICI = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/128.0 Safari/537.36")

#: Kabul edilen görsel türleri. SVG bilerek YOK: betik taşıyabilir.
RASTER_TURLER = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}
_TUR_ESANLAMLI = {"image/jpg": "image/jpeg", "image/pjpeg": "image/jpeg"}

_NAT64 = ipaddress.ip_network("64:ff9b::/96")


class DisIstekHatasi(Exception):
    """Editöre gösterilebilir hata. Metni iç ayrıntı taşımaz."""


@dataclass
class Yanit:
    adres: str                    # yönlendirmelerden sonraki son adres
    durum: int
    tur: str                      # içerik türü, küçük harf, parametresiz
    karakter_kumesi: str
    govde: bytes
    basliklar: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Adres ve IP denetimi
# ---------------------------------------------------------------------------

def _gomulu_v4(ip):
    """IPv6 içine gömülü IPv4 adresi varsa onu döndürür."""
    if ip.version != 6:
        return None
    if ip.ipv4_mapped is not None:
        return ip.ipv4_mapped
    if ip.sixtofour is not None:
        return ip.sixtofour
    if ip in _NAT64:
        return ipaddress.IPv4Address(int(ip) & 0xFFFFFFFF)
    return None


def ip_izinli_mi(metin: str) -> bool:
    """Genel (internete açık, tek hedefli) bir adres mi?"""
    try:
        ip = ipaddress.ip_address(str(metin).split("%", 1)[0])
    except ValueError:
        return False
    gomulu = _gomulu_v4(ip)
    if gomulu is not None and not ip_izinli_mi(str(gomulu)):
        return False
    if ip.version == 6 and ip.teredo is not None:
        return False
    if (ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast
            or ip.is_reserved or ip.is_unspecified):
        return False
    return ip.is_global or gomulu is not None


def _coz(ad: str, port: int) -> list[str]:
    """Adın tüm IP adresleri. Testler bu işlevi yamalar."""
    bilgi = socket.getaddrinfo(ad, port, type=socket.SOCK_STREAM)
    return list(dict.fromkeys(b[4][0] for b in bilgi))


def adres_denetle(adres: str):
    """Döner: (şema, ad, port, yol, ip). Geçmezse `DisIstekHatasi`."""
    try:
        p = urlsplit((adres or "").strip())
        port = p.port
    except ValueError as e:
        raise DisIstekHatasi("Adres çözümlenemedi.") from e
    sema = (p.scheme or "").lower()
    if sema not in IZINLI_SEMALAR:
        raise DisIstekHatasi("Yalnız http:// ya da https:// adresleri alınabilir.")
    if p.username or p.password:
        raise DisIstekHatasi("Kullanıcı adı ya da parola taşıyan adres alınmaz.")
    ad = (p.hostname or "").strip().rstrip(".")
    if not ad:
        raise DisIstekHatasi("Adreste sunucu adı yok.")
    port = port or (443 if sema == "https" else 80)
    if port not in IZINLI_PORTLAR:
        raise DisIstekHatasi("Bu bağlantı noktasına istek yapılmaz.")
    try:
        ad_idna = ad.encode("idna").decode("ascii")
    except UnicodeError as e:
        raise DisIstekHatasi("Sunucu adı geçersiz.") from e
    try:
        ipler = _coz(ad_idna, port)
    except (OSError, UnicodeError) as e:
        gunluk.info("dis_istek: ad cozulemedi %r: %s", ad, e)
        raise DisIstekHatasi("Sunucu adı çözülemedi.") from e
    if not ipler:
        raise DisIstekHatasi("Sunucu adı çözülemedi.")
    yasak = [ip for ip in ipler if not ip_izinli_mi(ip)]
    if yasak:
        gunluk.warning("dis_istek: ic aga istek reddedildi %r -> %s", ad, yasak)
        raise DisIstekHatasi(
            "Bu adres alınamaz: yerel ya da iç ağdaki adreslere istek yapılmaz.")
    yol = p.path or "/"
    if p.query:
        yol += "?" + p.query
    return sema, ad_idna, port, yol, ipler[0]


# ---------------------------------------------------------------------------
# Bağlantı
# ---------------------------------------------------------------------------

def _baglanti(sema: str, ad: str, port: int, ip: str, zaman_asimi: float):
    """Denetlenmiş IP'ye bağlanan bağlantı. `Host` ve TLS SNI adı taşır.

    Testler bu işlevi yamalar.
    """
    if sema == "https":
        baglanti = http.client.HTTPSConnection(
            ad, port, timeout=zaman_asimi, context=ssl.create_default_context())
    else:
        baglanti = http.client.HTTPConnection(ad, port, timeout=zaman_asimi)

    def kur(_adres, timeout=zaman_asimi, source_address=None):
        return socket.create_connection((ip, port), timeout, source_address)

    baglanti._create_connection = kur
    return baglanti


def _govde_oku(yanit, sinir: int, son_an: float) -> bytes:
    uzunluk = yanit.getheader("Content-Length")
    if uzunluk and uzunluk.strip().isdigit() and int(uzunluk) > sinir:
        raise DisIstekHatasi(f"Kaynak çok büyük ({sinir // (1024 * 1024)} MB sınırı).")
    parcalar, toplam = [], 0
    while True:
        if time.monotonic() > son_an:
            raise DisIstekHatasi("Kaynak zamanında yanıt vermedi.")
        parca = yanit.read(PARCA)
        if not parca:
            break
        toplam += len(parca)
        if toplam > sinir:
            raise DisIstekHatasi(f"Kaynak çok büyük ({sinir // (1024 * 1024)} MB sınırı).")
        parcalar.append(parca)
    return b"".join(parcalar)


def _ac(veri: bytes, kodlama: str, sinir: int) -> bytes:
    """gzip/deflate açar; açılmış boyut da sınıra tabidir."""
    kodlama = (kodlama or "").strip().lower()
    if kodlama in ("", "identity"):
        return veri
    if kodlama in ("gzip", "x-gzip"):
        acici = zlib.decompressobj(16 + zlib.MAX_WBITS)
    elif kodlama == "deflate":
        acici = zlib.decompressobj()
    else:
        raise DisIstekHatasi("Kaynak desteklenmeyen bir sıkıştırmayla döndü.")
    try:
        cikti = acici.decompress(veri, sinir + 1)
    except zlib.error as e:
        raise DisIstekHatasi("Kaynağın sıkıştırılmış gövdesi bozuk.") from e
    if len(cikti) > sinir or acici.unconsumed_tail:
        raise DisIstekHatasi(f"Kaynak çok büyük ({sinir // (1024 * 1024)} MB sınırı).")
    return cikti


def getir(adres: str, *, en_cok_bayt: int = HTML_SINIRI, kabul: str = "*/*",
          zaman_asimi: float = ZAMAN_ASIMI, toplam_sure: float = TOPLAM_SURE,
          ek_basliklar: dict | None = None) -> Yanit:
    """Adresi kapıdan geçirerek indirir. Yalnız 2xx yanıt döner."""
    son_an = time.monotonic() + toplam_sure
    simdiki = (adres or "").strip()
    for _adim in range(EN_COK_YONLENDIRME + 1):
        sema, ad, port, yol, ip = adres_denetle(simdiki)
        basliklar = {"User-Agent": TARAYICI, "Accept": kabul,
                     "Accept-Language": "tr,en;q=0.8",
                     "Accept-Encoding": "gzip, deflate"}
        basliklar.update(ek_basliklar or {})
        baglanti = _baglanti(sema, ad, port, ip, zaman_asimi)
        try:
            try:
                baglanti.request("GET", yol, headers=basliklar)
                yanit = baglanti.getresponse()
            except (OSError, http.client.HTTPException, ssl.SSLError) as e:
                gunluk.info("dis_istek: baglanti hatasi %r: %r", ad, e)
                raise DisIstekHatasi("Kaynağa bağlanılamadı.") from e

            if yanit.status in (301, 302, 303, 307, 308):
                hedef = yanit.getheader("Location") or ""
                if not hedef:
                    raise DisIstekHatasi("Kaynak geçersiz bir yönlendirme döndürdü.")
                simdiki = urljoin(simdiki, hedef.strip())
                continue
            if not 200 <= yanit.status < 300:
                raise DisIstekHatasi(f"Kaynak {yanit.status} döndürdü.")

            try:
                ham = _govde_oku(yanit, en_cok_bayt, son_an)
            except (OSError, http.client.HTTPException) as e:
                gunluk.info("dis_istek: okuma hatasi %r: %r", ad, e)
                raise DisIstekHatasi("Kaynak okunurken bağlantı koptu.") from e
            govde = _ac(ham, yanit.getheader("Content-Encoding") or "", en_cok_bayt)
            tur_ham = (yanit.getheader("Content-Type") or "")
            tur = tur_ham.split(";", 1)[0].strip().lower()
            kume = ""
            for parca in tur_ham.split(";")[1:]:
                anahtar, _, deger = parca.partition("=")
                if anahtar.strip().lower() == "charset":
                    kume = deger.strip().strip('"\'')
            return Yanit(adres=simdiki, durum=yanit.status, tur=tur,
                         karakter_kumesi=kume, govde=govde,
                         basliklar={k.lower(): v for k, v in yanit.getheaders()}
                         if hasattr(yanit, "getheaders") else {})
        finally:
            baglanti.close()
    raise DisIstekHatasi(f"Kaynak {EN_COK_YONLENDIRME}'ten fazla yönlendirme yaptı.")


# ---------------------------------------------------------------------------
# Kullanım biçimleri
# ---------------------------------------------------------------------------

_METIN_TURLERI = ("application/xhtml+xml", "application/xml", "")


def html_getir(adres: str, en_cok_bayt: int = HTML_SINIRI) -> str:
    """Haber sayfasını metin olarak döndürür."""
    yanit = getir(adres, en_cok_bayt=en_cok_bayt,
                  kabul="text/html,application/xhtml+xml")
    if not (yanit.tur.startswith("text/") or yanit.tur in _METIN_TURLERI):
        raise DisIstekHatasi("Adres bir web sayfası döndürmedi.")
    for kodlama in filter(None, [yanit.karakter_kumesi, "utf-8", "windows-1254"]):
        try:
            return yanit.govde.decode(kodlama)
        except (UnicodeDecodeError, LookupError):
            continue
    return yanit.govde.decode("utf-8", errors="replace")


def gorsel_turu_bul(veri: bytes) -> str:
    """Sihirli baytlardan raster türü. Tanınmazsa boş."""
    if veri.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if veri.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if veri.startswith((b"GIF87a", b"GIF89a")):
        return "image/gif"
    if len(veri) >= 12 and veri[:4] == b"RIFF" and veri[8:12] == b"WEBP":
        return "image/webp"
    return ""


def gorsel_getir(adres: str, *, en_cok_bayt: int = GORSEL_SINIRI,
                 ek_basliklar: dict | None = None):
    """Döner: (bayt, tür, uzantı). Yalnız jpeg/png/webp/gif.

    İçerik türü başlığı VE dosyanın sihirli baytları aynı raster türü
    söylemeli; uzantı türden türetilir, adresten DEĞİL. SVG, HTML ya da
    türü tutmayan dosya diske hiç ulaşmaz.
    """
    yanit = getir(adres, en_cok_bayt=en_cok_bayt,
                  kabul=",".join(RASTER_TURLER), ek_basliklar=ek_basliklar)
    beyan = _TUR_ESANLAMLI.get(yanit.tur, yanit.tur)
    if beyan not in RASTER_TURLER:
        raise DisIstekHatasi("Adres desteklenen bir görsel döndürmedi "
                             "(yalnız JPEG, PNG, WebP, GIF).")
    if not yanit.govde:
        raise DisIstekHatasi("Görsel boş geldi.")
    gercek = gorsel_turu_bul(yanit.govde)
    if gercek != beyan:
        raise DisIstekHatasi("Dosyanın içeriği beyan edilen görsel türüyle uyuşmuyor.")
    return yanit.govde, gercek, RASTER_TURLER[gercek]
