"""Teslim katmanının ara katmanları (19 Ekim 2026).

Üç parça, `settings.MIDDLEWARE` içindeki sıralarıyla:

1. `SeciciGZip` — sayfa ve XML sıkıştırması. WhiteNoise'un ÜSTÜNDE durur ki
   dosyadan servis edilen site haritaları da sıkışsın; zaten sıkıştırılmış
   (`.br`/`.gz`) statik dosyaya ve görsellere dokunmaz.
2. `SiteHaritasiDosyalari` — `/static/sitemap/…` adresini üretilmiş
   dosyadan verir (üretimde); dosya yoksa istek görünüme düşer.
3. `IcerikPolitikasi` — Content-Security-Policy başlığı.

## BREACH değerlendirmesi

BREACH, sıkıştırılmış bir yanıtta hem gizli bir değer (CSRF jetonu) hem de
saldırganın yansıttığı bir girdi bulunduğunda, yanıt boyundan gizli değeri
tahmin etmeye dayanır. Django'da iki önlem zaten var: CSRF jetonu her
yanıtta yeniden maskelenir (aynı jeton iki kez aynı baytlarla görünmez) ve
4.2'den beri `GZipMiddleware` yanıta rastgele dolgu ekler (Heal The Breach).
Okur sayfalarında gizli değer yok. Yine de **panel ve yönetim sayfaları
sıkıştırılmaz** (`SIKISTIRMA_HARIC_ONEKLER`): oralarda hem jeton hem
kullanıcı girdisi yan yana duruyor, trafik küçük ve kazanç önemsiz.
"""

from __future__ import annotations

import base64
import hashlib
import re
from functools import lru_cache
from pathlib import Path

from django.conf import settings
from django.http import Http404
from django.middleware.gzip import GZipMiddleware
from django.views.static import serve

# --- 1. sıkıştırma ---------------------------------------------------------

SIKISTIRILAN_TURLER = (
    "text/", "application/json", "application/xml", "application/rss+xml",
    "application/atom+xml", "application/javascript", "application/ld+json",
    "application/manifest+json", "image/svg+xml",
)


class SeciciGZip(GZipMiddleware):
    """Django'nun GZip ara katmanı, iki süzgeçle: tür ve adres öneki."""

    def process_response(self, request, response):
        if any(request.path.startswith(o)
               for o in getattr(settings, "SIKISTIRMA_HARIC_ONEKLER", ())):
            return response
        tur = (response.get("Content-Type") or "").lower()
        if not tur.startswith(SIKISTIRILAN_TURLER):
            return response
        return super().process_response(request, response)


# --- 2. site haritası dosyaları ---------------------------------------------

_HARITA_ADI = re.compile(r"^[A-Za-z0-9_\-]+\.xml$")
HARITA_ONEKI = "/static/sitemap/"


class SiteHaritasiDosyalari:
    """`/static/sitemap/<ad>.xml` → `site_haritasi_uret` çıktısı, özetsiz.

    Canlı sitede bu adresler yıllardır statik dosya ve arama motorlarında
    kayıtlı; adres değişmez, ada özet eklenmez. Üretimde önce nginx dener
    (`try_files`), bu katman nginx'siz kurulumun ve tutarlılığın içindir.
    Kapalıyken (geliştirme, test) aynı adresi `besleme.gorunumler` canlı
    veriden üretir; o yol F8 karşılaştırmasının doğrulama yoludur.

    WhiteNoise'a bırakılmadı: WhiteNoise dosya listesini ve boyları açılışta
    bir kez okur, oysa bu dosyalar zamanlayıcıyla yeniden yazılır. Eski
    `Content-Length` ile yeni dosya göndermek bozuk yanıt demektir.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if (getattr(settings, "SITE_HARITASI_DOSYADAN", False)
                and request.path.startswith(HARITA_ONEKI)
                and request.method in ("GET", "HEAD")):
            ad = request.path[len(HARITA_ONEKI):]
            if _HARITA_ADI.match(ad):
                kok = _harita_koku()
                if (kok / ad).is_file():
                    try:
                        yanit = serve(request, ad, document_root=str(kok))
                    except Http404:
                        return self.get_response(request)
                    if yanit.status_code == 200:
                        yanit["Content-Type"] = "application/xml; charset=utf-8"
                    yanit["Cache-Control"] = (
                        f"public, max-age={settings.SITE_HARITASI_ONBELLEK_SANIYE}")
                    return yanit
        return self.get_response(request)


def _harita_koku() -> Path:
    from besleme import ayarlar
    return Path(ayarlar.cikti_koku_yolu())


# --- 3. içerik güvenlik politikası (CSP) ------------------------------------
#
# Django 5.2'de yerleşik CSP yok (6.0'da geliyor). Politika burada kurulur.
#
# Satır içi betikler: şablonlarda dört kısa `<script>` var (taban.html; reklam
# tercihleri, yalnız sunum oturumunda basılır). `'unsafe-inline'` yerine her
# birinin SHA-256 özeti politikaya yazılır. Özetler şablon dosyalarından
# açılışta hesaplanır: biri satır içi betiği değiştirirse özet de kendiliğinden
# değişir ve `cekirdek.tests` sayfadaki her betiğin özetinin başlıkta olduğunu
# ölçer. Saldırganın sayfaya soktuğu bir betik hiçbir şablonda olmadığı için
# özeti listede yoktur — CSP'nin bütün amacı bu.
#
# Stil: `style-src 'unsafe-inline'` bilerek açık. Şablonlarda ve panel
# betiklerinde `style="…"` nitelikleri var; CSS enjeksiyonunun zararı betik
# enjeksiyonuna göre sınırlı ve bu ilk sürümde sertlik betiğe harcandı.

_BETIK = re.compile(r"<script(?P<nit>[^>]*)>(?P<govde>.*?)</script>",
                    re.IGNORECASE | re.DOTALL)
_VERI_TURU = re.compile(
    r"""type\s*=\s*["']?(application/(ld\+)?json|text/template)""", re.I)

# Reklam açıkken izin verilen Google kökenleri. Demo ağı (GPT) ve AdSense
# betikleri kendi alt betiklerini, çerçevelerini ve ölçüm isteklerini bu
# alanlardan yükler; liste Google'ın yayıncı belgelerindeki alan adlarıdır.
REKLAM_KOKENLERI = (
    "https://*.googlesyndication.com", "https://*.doubleclick.net",
    "https://*.googletagservices.com", "https://*.google.com",
    "https://*.gstatic.com", "https://*.adtrafficquality.google",
    "https://*.googleadservices.com",
)


def _sablon_klasorleri():
    from django.template.utils import get_app_template_dirs
    klasorler = []
    for motor in settings.TEMPLATES:
        klasorler.extend(Path(k) for k in motor.get("DIRS", []))
    klasorler.extend(Path(k) for k in get_app_template_dirs("templates"))
    return klasorler


@lru_cache(maxsize=8)
def satir_ici_ozetler(reklam_yolu: str) -> tuple[str, ...]:
    """Şablonlardaki satır içi betiklerin `'sha256-…'` değerleri.

    Şablon değişkeni taşıyan betik (`{{ reklam_yolu|escapejs }}`) Django
    motoruyla, değişken ayarlardan gelerek işlenir; `{% %}` taşıyan betik
    işlenemez ve atlanır (bugün yok — test bunu da yakalar).
    """
    from django.template import engines

    motor = engines["django"]
    ozetler: set[str] = set()
    for klasor in _sablon_klasorleri():
        if not klasor.is_dir():
            continue
        for yol in klasor.rglob("*.html"):
            try:
                metin = yol.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            for m in _BETIK.finditer(metin):
                nit, govde = m.group("nit"), m.group("govde")
                if "src=" in nit or _VERI_TURU.search(nit) or not govde.strip():
                    continue
                if "{%" in govde:
                    continue
                if "{{" in govde:
                    try:
                        govde = motor.from_string(govde).render(
                            {"reklam_yolu": reklam_yolu})
                    except Exception:  # noqa: BLE001 - işlenemeyen parça atlanır
                        continue
                ozet = base64.b64encode(
                    hashlib.sha256(govde.encode("utf-8")).digest()).decode()
                ozetler.add(f"'sha256-{ozet}'")
    return tuple(sorted(ozetler))


def politika() -> str:
    reklam = bool(getattr(settings, "REKLAM_DEMO", False)
                  or getattr(settings, "ADSENSE_ID", ""))
    betik = ["'self'", *satir_ici_ozetler(getattr(settings, "REKLAM_DEMO_YOLU", ""))]
    gorsel = ["'self'", "data:"]
    cerceve = ["'self'"]
    baglanti = ["'self'"]
    if reklam:
        betik += REKLAM_KOKENLERI
        gorsel += ["https:"]
        cerceve += REKLAM_KOKENLERI
        baglanti += REKLAM_KOKENLERI
    yonergeler = [
        ("default-src", ["'self'"]),
        ("script-src", betik),
        ("style-src", ["'self'", "'unsafe-inline'"]),
        ("img-src", gorsel),
        ("font-src", ["'self'"]),
        ("connect-src", baglanti),
        ("frame-src", cerceve),
        ("object-src", ["'none'"]),
        ("base-uri", ["'self'"]),
        ("form-action", ["'self'"]),
        ("frame-ancestors", ["'none'"]),
    ]
    metin = "; ".join(f"{ad} {' '.join(deger)}" for ad, deger in yonergeler)
    # Yalnız site gerçekten HTTPS'teyken: düz HTTP'de (BH_SSL_YONLENDIR=0,
    # yerel ölçüm) tarayıcı kendi kaynaklarını https'e çevirip düşürürdü.
    if getattr(settings, "URETIM", False) and getattr(settings, "SECURE_SSL_REDIRECT", False):
        metin += "; upgrade-insecure-requests"
    return metin


class IcerikPolitikasi:
    """CSP başlığını ekler. `BH_CSP`: uygula (varsayılan) · rapor · kapali.

    `rapor` kipinde tarayıcı engellemez, yalnız konsola yazar: yeni bir dış
    hizmet denenirken kırılma görmeden ihlalleri toplamak için.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        yanit = self.get_response(request)
        kip = getattr(settings, "CSP_KIP", "uygula")
        if kip == "kapali":
            return yanit
        ad = ("Content-Security-Policy-Report-Only" if kip == "rapor"
              else "Content-Security-Policy")
        if ad not in yanit:
            yanit[ad] = politika()
        return yanit
