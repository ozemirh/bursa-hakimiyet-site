"""Görsel türevleri — isteğe bağlı küçültme, WebP, disk önbelleği (19 Ekim 2026).

**Sorun (ölçüldü).** Arşivde her haberin yalnız `_large` (1280 px) dosyası
var ve sayfalar onu olduğu gibi basıyordu: anasayfa 390 px'te 21 görsel /
6,99 MB, 1440 px'te 35 görsel / 9,22 MB. 263 px'lik bir kart 1280 px'lik
dosya indiriyordu.

**Çözüm.** `/gorsel/<boyut>/<kaynak yol>.webp` adresi. İlk istekte orijinal
Pillow ile küçültülür, WebP'ye çevrilir ve **diske** yazılır; sonraki
istekler dosyadan gelir. Üretimde nginx bu dosyaları Django'ya hiç uğramadan
verir; Django yalnız eksik türevi üretir.

Adres → dosya eşlemesi bire birdir (nginx için):

    /gorsel/480/gorseller/2026-08/x_large.webp.webp
      → <TUREV_KOK>/480/gorseller/2026-08/x_large.webp.webp
      ← kaynak <ARSIV_KOK>/gorseller/2026-08/x_large.webp

    /gorsel/og/gorseller/2026-08/x_large.webp.jpg      (1200×630, JPEG)
      → <TUREV_KOK>/og/gorseller/2026-08/x_large.webp.jpg

Kaynak uzantısı **atılmaz, sonuna eklenir**: `x.jpg` ile `x.png` aynı
klasörde dururlarsa türevleri çakışmasın ve adres tek anlamlı kalsın. CSS'te
`img[src*="-portre"]` gibi dosya adına bakan seçiciler de (yazar kuşağı)
bu sayede çalışmayı sürdürür.

**Orijinallere dokunulmaz.** Arşiv yalnız okunur; türev ayrı bir köke yazılır
(`TUREV_KOK`: ayar → `BH_TUREV_KOK` ortam değişkeni → `ARSIV_KOK/turev`).

Güvenlik sözleşmesi (testli, `tests_gorsel.py`):
- boyut beyaz listede değilse 404;
- yol mutlak olamaz, `..`/`.`/boş dilim, ters bölü, sürücü harfi, NUL içeremez;
- ilk dilim tanımlı kaynak köklerinden biri olmalı (`veri-*` JSON klasörleri
  bu yüzden erişilemez) ve çözülmüş yol o kökün İÇİNDE kalmalı;
- yalnız raster kaynak: jpg/jpeg/png/webp/gif — hem uzantı hem Pillow'un
  okuduğu biçim denetlenir (SVG/HTML hiçbir koşulda açılmaz);
- dosya boyutu ve piksel sınırı (sıkıştırma bombası);
- aynı türevin eşzamanlı ikinci üretimi dosya kilidiyle engellenir, yazım
  geçici dosya + `os.replace` ile atomiktir; süreç başına eşzamanlı üretim
  sayısı semaforla sınırlıdır.
"""

from __future__ import annotations

import io
import os
import threading
import time
from contextlib import contextmanager
from functools import lru_cache
from pathlib import Path

from django.conf import settings
from django.http import (Http404, HttpResponse, HttpResponseNotAllowed,
                         HttpResponseNotModified)
from django.utils.http import http_date

# --- sözleşme sabitleri -----------------------------------------------------

#: Üretilen genişlikler. Ölçülmüş yuvalara göre seçildi (1440 px'te dörtlü
#: kart 263, son haberler 359, bölüm kartı 528, manşet 760, detay 712 px;
#: iki kat yoğunluklu ekranda bunların iki katı).
GENISLIKLER = (320, 480, 640, 960, 1280)

#: Sosyal paylaşım (og:image / twitter:image) için sabit kırpım.
OG_OLCU = (1200, 630)

#: Sabit oranlı kırpımlar — JPEG, ortadan. `og` paylaşım kartı içindir;
#: üç oran (16:9, 4:3, 1:1) NewsArticle JSON-LD'sinin `image` dizisi için
#: (Paket G, 19 Ekim 2026): Google haber ve Discover için bu üç oranı
#: istiyor ve en az 1200 px genişlik öneriyor. Arşivin `_large` dosyası
#: 1280×853; 4:3 ve 1:1 kırpımda boy hafifçe büyütülür — oran tutarlılığı
#: burada çözünürlükten önemli. Türevler istek gelince üretilir.
KIRPIMLAR = {
    "og": OG_OLCU,
    "16x9": (1200, 675),
    "4x3": (1200, 900),
    "1x1": (1200, 1200),
}

WEBP_KALITE = 78
OG_KALITE = 82

#: Kaynağın adresteki ilk dilimi → diskteki kök. Arşivin `veri*` klasörleri
#: (JSON dökümleri) bilerek YOK.
def kaynak_kokleri() -> dict[str, Path]:
    arsiv = Path(settings.ARSIV_KOK)
    return {
        "gorseller": arsiv / "gorseller",
        "gorseller-galeri": arsiv / "gorseller-galeri",
        "gorseller-video": arsiv / "gorseller-video",
        "gorseller-yazar": arsiv / "gorseller-yazar",
        "gorseller-kose": arsiv / "gorseller-kose",
        # Sitenin kendi fotoğrafları (hava ve namaz panelleri). Yalnız
        # `genis/` — `gorseller/kaynak/` gibi demo klasörleri açılmaz.
        "site": Path(settings.BASE_DIR).parent / "gorseller" / "genis",
    }


def turev_koku() -> Path:
    kok = getattr(settings, "TUREV_KOK", None) or os.environ.get("BH_TUREV_KOK")
    return Path(kok) if kok else Path(settings.ARSIV_KOK) / "turev"


RASTER_UZANTILAR = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
RASTER_BICIMLER = {"JPEG", "MPO", "PNG", "WEBP", "GIF"}

#: Arşivin en büyük dosyası ~1,5 MB; 25 MB her meşru fotoğrafı karşılar.
EN_BUYUK_BAYT = 25 * 1024 * 1024
#: 40 MP: 7.300×5.475'lik bir fotoğraf. Üstü bomba sayılır.
EN_BUYUK_PIKSEL = 40_000_000

KILIT_BEKLEME_SN = 20
BAYAT_KILIT_SN = 60
_URETIM_SINIRI = threading.BoundedSemaphore(4)

ONBELLEK_BASLIGI = "public, max-age=31536000, immutable"


class GecersizIstek(Exception):
    """Adres sözleşmeye uymuyor — 404."""


class GorselHatasi(Exception):
    """Kaynak okunamadı ya da sınırları aşıyor — 404."""


class Mesgul(Exception):
    """Aynı türev başka bir istekte üretiliyor ve süre doldu — 503."""


# --- yol çözümü ----------------------------------------------------------------

def _dilimler(yol: str) -> list[str]:
    if not yol or "\x00" in yol or "\\" in yol or ":" in yol:
        raise GecersizIstek("yasak karakter")
    if yol.startswith("/"):
        raise GecersizIstek("mutlak yol")
    dilimler = yol.split("/")
    for d in dilimler:
        if d in ("", ".", "..") or any(ord(c) < 32 for c in d):
            raise GecersizIstek("geçersiz dilim")
    return dilimler


def kaynak_coz(kaynak_yol: str) -> Path:
    """`gorseller/2026-08/x.webp` → mutlak kaynak dosya. Sözleşme dışı → hata."""
    dilimler = _dilimler(kaynak_yol)
    if len(dilimler) < 2:
        raise GecersizIstek("kök yok")
    kokler = kaynak_kokleri()
    if dilimler[0] not in kokler:
        raise GecersizIstek("tanımsız kök")
    if Path(dilimler[-1]).suffix.lower() not in RASTER_UZANTILAR:
        raise GecersizIstek("raster değil")
    kok = kokler[dilimler[0]].resolve()
    aday = kok.joinpath(*dilimler[1:]).resolve()
    try:
        aday.relative_to(kok)
    except ValueError:
        raise GecersizIstek("kök dışı") from None
    return aday


def turev_adi(boyut: str, kaynak_yol: str) -> str:
    """Adresin `/gorsel/<boyut>/` sonrası: kaynak yol + çıktı uzantısı."""
    return kaynak_yol + (".jpg" if boyut in KIRPIMLAR else ".webp")


def adres(boyut, kaynak_yol: str) -> str:
    from urllib.parse import quote
    return f"/gorsel/{boyut}/" + quote(turev_adi(str(boyut), kaynak_yol), safe="/")


def istek_coz(boyut: str, yol: str) -> tuple[str, Path, Path]:
    """Adres parçalarından (boyut, kaynak, hedef). Beyaz liste burada."""
    # Kanonik yazım şart: "0480" kabul edilseydi aynı türevin ikinci bir
    # kopyası üretilir, disk ve önbellek boşuna dolardı.
    if boyut not in KIRPIMLAR and boyut not in {str(g) for g in GENISLIKLER}:
        raise GecersizIstek("boyut beyaz listede değil")
    son_ek = ".jpg" if boyut in KIRPIMLAR else ".webp"
    if not yol.endswith(son_ek):
        raise GecersizIstek("çıktı uzantısı")
    kaynak_yol = yol[: -len(son_ek)]
    kaynak = kaynak_coz(kaynak_yol)
    hedef = turev_koku() / boyut / Path(*_dilimler(kaynak_yol))
    hedef = hedef.with_name(hedef.name + son_ek)
    return kaynak_yol, kaynak, hedef


# --- üretim ----------------------------------------------------------------------

def _ac(kaynak: Path):
    """Pillow ile aç; boyut, biçim ve piksel sınırını UYGULA. Yüklemez."""
    from PIL import Image
    try:
        bayt = kaynak.stat().st_size
    except FileNotFoundError:
        raise GorselHatasi("kaynak yok") from None
    if bayt > EN_BUYUK_BAYT:
        raise GorselHatasi("dosya çok büyük")
    try:
        im = Image.open(kaynak)
    except Exception as hata:          # bozuk ya da tanınmayan dosya
        raise GorselHatasi(f"açılamadı: {hata}") from None
    if im.format not in RASTER_BICIMLER:
        im.close()
        raise GorselHatasi("raster biçim değil")
    en, boy = im.size
    if en * boy > EN_BUYUK_PIKSEL:
        im.close()
        raise GorselHatasi("piksel sınırı")
    return im


def _yon(im) -> int:
    try:
        return int(im.getexif().get(0x0112, 1))
    except Exception:
        return 1


def _hazirla(im, hedef_en: int | None):
    """Taslak çözme + EXIF yönü + sRGB + kip. Dönen görüntü yüklenmiştir."""
    from PIL import Image, ImageCms, ImageOps
    en, boy = im.size
    yon = _yon(im)
    gorunen_en = boy if yon in (5, 6, 7, 8) else en
    if hedef_en and im.format in ("JPEG", "MPO") and gorunen_en > hedef_en:
        # JPEG çözücü 1/2, 1/4, 1/8 ölçekte açabilir: 4.000 px'lik bir
        # fotoğrafı 480'e indirmek için tam çözmek gerekmiyor.
        oran = hedef_en / gorunen_en
        im.draft("RGB", (max(1, int(en * oran) + 1), max(1, int(boy * oran) + 1)))
    if getattr(im, "is_animated", False):
        im.seek(0)
    im.load()
    icc = im.info.get("icc_profile")
    if im.mode == "P":
        im = im.convert("RGBA" if "transparency" in im.info else "RGB")
    if im.mode == "CMYK" or (icc and im.mode in ("RGB", "RGBA")):
        try:
            if icc:
                giris = ImageCms.ImageCmsProfile(io.BytesIO(icc))
                cikis_kip = "RGBA" if im.mode == "RGBA" else "RGB"
                im = ImageCms.profileToProfile(
                    im, giris, ImageCms.createProfile("sRGB"), outputMode=cikis_kip)
            else:
                im = im.convert("RGB")
        except Exception:
            im = im.convert("RGB")
    im = ImageOps.exif_transpose(im)
    if im.mode not in ("RGB", "RGBA"):
        im = im.convert("RGBA" if im.mode in ("LA", "PA") else "RGB")
    return im


def _kucult(im, genislik: int):
    from PIL import Image
    if im.width <= genislik:
        return im
    boy = max(1, round(im.height * genislik / im.width))
    return im.resize((genislik, boy), Image.LANCZOS, reducing_gap=3.0)


def _og(im, olcu=OG_OLCU):
    from PIL import Image, ImageOps
    if im.mode == "RGBA":
        zemin = Image.new("RGB", im.size, (255, 255, 255))
        zemin.paste(im, mask=im.getchannel("A"))
        im = zemin
    return ImageOps.fit(im, olcu, Image.LANCZOS, centering=(0.5, 0.5))


def _yaz(im, hedef: Path, og: bool) -> None:
    hedef.parent.mkdir(parents=True, exist_ok=True)
    gecici = hedef.with_name(f".{hedef.name}.{os.getpid()}.{threading.get_ident()}.gecici")
    try:
        if og:
            im.save(gecici, "JPEG", quality=OG_KALITE, optimize=True, progressive=True)
        else:
            im.save(gecici, "WEBP", quality=WEBP_KALITE, method=4)
        for deneme in range(5):
            try:
                os.replace(gecici, hedef)
                break
            except PermissionError:      # Windows: hedef o an okunuyor
                if deneme == 4:
                    raise
                time.sleep(0.05 * (deneme + 1))
    finally:
        try:
            gecici.unlink()
        except FileNotFoundError:
            pass


@contextmanager
def _kilit(hedef: Path):
    """Dosya kilidi: `O_EXCL` ile yaratılan `.kilit`. Süreçler arası geçerli."""
    hedef.parent.mkdir(parents=True, exist_ok=True)
    kilit = hedef.with_name(hedef.name + ".kilit")
    bitis = time.monotonic() + KILIT_BEKLEME_SN
    while True:
        try:
            fd = os.open(kilit, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            break
        except FileExistsError:
            try:
                if time.time() - kilit.stat().st_mtime > BAYAT_KILIT_SN:
                    kilit.unlink()           # çöken üreticinin artığı
                    continue
            except FileNotFoundError:
                continue
            if time.monotonic() > bitis:
                raise Mesgul(str(hedef)) from None
            time.sleep(0.05)
    try:
        yield
    finally:
        os.close(fd)
        try:
            kilit.unlink()
        except FileNotFoundError:
            pass


def _taze(hedef: Path, kaynak: Path) -> bool:
    try:
        return hedef.stat().st_mtime >= kaynak.stat().st_mtime
    except FileNotFoundError:
        return False


def turev_hazirla(boyut: str, yol: str) -> Path:
    """Görünümün ve komutun ortak girişi. Türev dosyasının yolunu döner."""
    _, kaynak, hedef = istek_coz(boyut, yol)
    if _taze(hedef, kaynak):
        return hedef
    if not kaynak.is_file():
        raise GorselHatasi("kaynak yok")
    with _kilit(hedef):
        if _taze(hedef, kaynak):        # beklerken başkası üretti
            return hedef
        with _URETIM_SINIRI:
            with _ac(kaynak) as im:
                kirpim = KIRPIMLAR.get(boyut)
                hedef_en = kirpim[0] if kirpim else int(boyut)
                hazir = _hazirla(im, hedef_en)
                cikti = _og(hazir, kirpim) if kirpim else _kucult(hazir, hedef_en)
                _yaz(cikti, hedef, og=bool(kirpim))
    return hedef


def tum_turevler(kaynak_yol: str, boyutlar=None, og=True) -> dict:
    """Toplu üretim: kaynak BİR kez çözülür, bütün genişlikler ondan iner.

    Dönen sözlük: {"uretilen": n, "atlanan": n, "bayt": n}. Var olan taze
    türev yeniden üretilmez.
    """
    boyutlar = list(boyutlar or GENISLIKLER)
    sonuc = {"uretilen": 0, "atlanan": 0, "bayt": 0}
    kaynak = kaynak_coz(kaynak_yol)
    eksik = []
    for b in [*map(str, boyutlar), *(["og"] if og else [])]:
        _, _, hedef = istek_coz(b, turev_adi(b, kaynak_yol))
        if _taze(hedef, kaynak):
            sonuc["atlanan"] += 1
        else:
            eksik.append((b, hedef))
    if not eksik:
        return sonuc
    with _ac(kaynak) as im:
        en_buyuk = max((int(b) for b, _ in eksik if b not in KIRPIMLAR),
                       default=OG_OLCU[0])
        if any(b in KIRPIMLAR for b, _ in eksik):
            en_buyuk = max(en_buyuk, OG_OLCU[0])
        hazir = _hazirla(im, en_buyuk)
        for b, hedef in sorted(eksik, key=lambda x: -(int(x[0]) if x[0] not in KIRPIMLAR else 9999)):
            with _kilit(hedef):
                if _taze(hedef, kaynak):
                    sonuc["atlanan"] += 1
                    continue
                kirpim = KIRPIMLAR.get(b)
                cikti = _og(hazir, kirpim) if kirpim else _kucult(hazir, int(b))
                _yaz(cikti, hedef, og=bool(kirpim))
                sonuc["uretilen"] += 1
                sonuc["bayt"] += hedef.stat().st_size
    return sonuc


# --- şablon tarafı: ölçü ------------------------------------------------------------

#: Arşivin `_large` dosyalarının tamamı 3:2 (URUN-PLANI.md §64, 1.498/1.498).
CERCEVE_OLCU = (1280, 853)


@lru_cache(maxsize=65536)
def _olcu_oku(kaynak_yol: str) -> tuple[int, int] | None:
    try:
        with _ac(kaynak_coz(kaynak_yol)) as im:
            en, boy = im.size
            if _yon(im) in (5, 6, 7, 8):
                en, boy = boy, en
            return en, boy
    except (GecersizIstek, GorselHatasi, OSError):
        return None


def olcu(kaynak_yol: str) -> tuple[tuple[int, int], bool]:
    """(en, boy), gerçek mi. Okunamazsa çerçeve oranı (3:2) döner."""
    deger = _olcu_oku(kaynak_yol)
    return (deger, True) if deger else (CERCEVE_OLCU, False)


# --- görünüm ----------------------------------------------------------------------

def gorunum(request, boyut: str, yol: str):
    """`/gorsel/<boyut>/<yol>` — türevi verir, yoksa üretip verir."""
    if request.method not in ("GET", "HEAD"):
        return HttpResponseNotAllowed(["GET", "HEAD"])
    try:
        hedef = turev_hazirla(boyut, yol)
    except (GecersizIstek, GorselHatasi):
        raise Http404("görsel yok")
    except Mesgul:
        yanit = HttpResponse("Görsel hazırlanıyor.", status=503,
                             content_type="text/plain; charset=utf-8")
        yanit["Retry-After"] = "1"
        yanit["Cache-Control"] = "no-store"
        return yanit
    durum = hedef.stat()
    etiket = f'"{durum.st_mtime_ns:x}-{durum.st_size:x}"'
    basliklar = {
        "Cache-Control": ONBELLEK_BASLIGI,
        "ETag": etiket,
        "Last-Modified": http_date(durum.st_mtime),
        "X-Content-Type-Options": "nosniff",
    }
    gelen = request.headers.get("If-None-Match", "")
    if gelen and (gelen.strip() == "*" or etiket in [e.strip() for e in gelen.split(",")]):
        yanit = HttpResponseNotModified()
    else:
        # Bellekten, akış olarak değil: türevler 10–150 KB ve açık kalan dosya
        # tutamacı Windows'ta türevin yenilenmesini (os.replace) kilitliyor.
        # Yayında bu yolu zaten nginx üstleniyor.
        yanit = HttpResponse(hedef.read_bytes(),
                             content_type="image/jpeg" if boyut == "og" else "image/webp")
    for ad, deger in basliklar.items():
        yanit[ad] = deger
    return yanit
