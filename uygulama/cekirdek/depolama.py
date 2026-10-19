"""Statik dosya teslimi: sürüm özetli adlar, sıkıştırma, CSS yorum ayıklama.

**Bundler değil.** `collectstatic` zaten her dosyayı tek tek okuyup özet
adıyla yazıyor; bu modül o adıma iki küçük iş ekliyor:

1. **CSS yorumları ayıklanır.** Ölçüm (19 Ekim 2026): `site.css` 200 KB'ın
   %46'sı yorum, gzip'li boyutu bu yüzden 58 KB. Yorumlar kaynakta KALIR —
   ekibin karar kaydı onlar — yalnız okura giden kopyadan düşer. `/*! … */`
   biçimindeki lisans yorumları korunur. Ayıklama özet hesaplanmadan ÖNCE
   yapılır: yalnız yorumu değişen bir dosya aynı sürüm adını korur ve
   okurun önbelleği boşa düşmez.
2. **Site haritası klasörü toplanmaz.** `statik/sitemap/` canlıyla aynı
   adreste (`/static/sitemap/…`) ve özetsiz servis edilmek zorunda (adres
   sözleşmesi, `besleme/adresler.py`). Toplansaydı `/statik/sitemap/
   news_2026-08.3f9c….xml` gibi kimsenin bilmediği bir adrese ve 3 × 240 MB
   (ham + .gz + .br) diske dönüşürdü.

Sıkıştırma (`.gz` + `.br`) ve özetli adların uzun önbelleği WhiteNoise'tan
gelir (`CompressedManifestStaticFilesStorage`); nginx aynı dosyaları
`gzip_static` ile doğrudan da verebilir (dagitim/nginx).
"""

from __future__ import annotations

import re

from django.contrib.staticfiles.finders import FileSystemFinder
from django.core.files.base import ContentFile
from whitenoise.storage import CompressedManifestStaticFilesStorage

# `collectstatic` bu adlı klasörleri hiç görmez.
TOPLANMAYAN_KLASORLER = ["sitemap"]

_ILGINC = re.compile(r"""["'/]|url\(""", re.IGNORECASE)
_ADSIL = re.compile(r"[A-Za-z0-9_\-]")


def yorum_ayikla(metin: str) -> str:
    """CSS'ten `/* … */` yorumlarını çıkarır; dize ve `url(...)` içine dokunmaz.

    Kurallar (CSS Syntax 3):
      - Dize içindeki `/*` yorum değildir: `content: "/* değil */"`.
      - Tırnaksız `url(...)` içinde yorum tanınmaz.
      - Yorum iki belirteci ayırıyorsa (`a/**/b`) yerine boşluk konur;
        aksi hâlde iki ad tek ada kaynardı.
      - `/*!` ile başlayan lisans yorumu korunur.
    Sonra yalnız boşluktan ibaret kalan satırlar silinir. Başka hiçbir
    küçültme yapılmaz: girinti gzip'te zaten neredeyse bedava.
    """
    parcalar: list[str] = []
    i, n = 0, len(metin)
    while i < n:
        m = _ILGINC.search(metin, i)
        if m is None:
            parcalar.append(metin[i:])
            break
        bas = m.start()
        parcalar.append(metin[i:bas])
        belirtec = m.group(0)
        if belirtec in ("'", '"'):
            j = bas + 1
            while j < n:
                c = metin[j]
                if c == "\\":
                    j += 2
                    continue
                j += 1
                if c == belirtec or c == "\n":
                    break
            parcalar.append(metin[bas:j])
            i = j
        elif belirtec.lower() == "url(":
            j = bas + 4
            while j < n and metin[j] in " \t\n":
                j += 1
            if j < n and metin[j] in "'\"":
                # Tırnaklı url: dize kuralı işlesin.
                parcalar.append(metin[bas:j])
                i = j
            else:
                son = metin.find(")", j)
                son = n if son == -1 else son + 1
                parcalar.append(metin[bas:son])
                i = son
        elif metin.startswith("/*", bas):
            son = metin.find("*/", bas + 2)
            son = n if son == -1 else son + 2
            yorum = metin[bas:son]
            if yorum.startswith("/*!"):
                parcalar.append(yorum)
            else:
                onceki = parcalar[-1][-1:] if parcalar and parcalar[-1] else ""
                sonraki = metin[son:son + 1]
                if onceki and sonraki and _ADSIL.match(onceki) and _ADSIL.match(sonraki):
                    parcalar.append(" ")
            i = son
        else:  # tek "/"
            parcalar.append("/")
            i = bas + 1
    sonuc = "".join(parcalar)
    satirlar = [s.rstrip() for s in sonuc.split("\n")]
    return "\n".join(s for s in satirlar if s.strip()) + "\n"


class TeslimDepolamasi(CompressedManifestStaticFilesStorage):
    """Özetli adlar + .gz/.br + CSS yorum ayıklama (yalnız üretim ayarında)."""

    def post_process(self, paths, dry_run=False, **options):
        if not dry_run:
            yeni = {}
            for ad, kaynak in paths.items():
                if ad.endswith(".css"):
                    # Toplanan kopya (STATIC_ROOT) yerinde ayıklanır ve özet
                    # hesabı kaynaktan değil BU kopyadan okur: `_post_process`
                    # dosyayı `paths[ad]` içindeki depodan açıyor.
                    with self.open(ad) as dosya:
                        ham = dosya.read().decode("utf-8")
                    temiz = yorum_ayikla(ham)
                    if temiz != ham:
                        self.delete(ad)
                        self._save(ad, ContentFile(temiz.encode("utf-8")))
                    yeni[ad] = (self, ad)
                else:
                    yeni[ad] = kaynak
            paths = yeni
        yield from super().post_process(paths, dry_run=dry_run, **options)


class KlasorBulucu(FileSystemFinder):
    """`STATICFILES_DIRS` bulucusu; site haritası klasörünü listelemez."""

    def list(self, ignore_patterns):
        desen = list(ignore_patterns or []) + TOPLANMAYAN_KLASORLER
        return super().list(desen)
