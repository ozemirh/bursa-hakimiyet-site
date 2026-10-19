"""Site simgelerini depodaki logodan üretir (Paket G, 19 Ekim 2026).

    python manage.py simge_uret

Kaynak `statik/logo-seffaf.png` (406×120, şeffaf). Logonun sol başındaki
"BH" işareti kare simgelere, logonun tamamı varsayılan paylaşım görseline
gider. Çıktılar `statik/simge/` altına yazılır ve depoya girer; komut yalnız
logo değiştiğinde yeniden çalıştırılır. Dış URL yok, her şey yerel.

| Dosya | Ölçü | Nerede |
|---|---|---|
| `favicon.ico` | 16·32·48 | `/favicon.ico` (tarayıcılar kökten ister) |
| `simge-32.png` | 32×32 | `<link rel="icon">` |
| `apple-touch-icon.png` | 180×180 | iOS ana ekran |
| `simge-192.png`, `simge-512.png` | | Android, JSON-LD `logo` |
| `paylasim.png` | 1200×630 | görseli olmayan sayfanın `og:image`'ı |
"""

from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

#: Logonun "BH" işaretinin sütun aralığı — saydamlık kanalından ölçüldü:
#: 4–166 arası tek parça, 167'den sonra bayrak ve yazı başlıyor.
ISARET_KUTUSU = (4, 0, 167, 120)
BEYAZ = (255, 255, 255, 255)


def _kok() -> Path:
    return Path(settings.BASE_DIR) / "statik"


def _kare(isaret, olcu: int, bosluk: float = 0.12):
    from PIL import Image
    tuval = Image.new("RGBA", (olcu, olcu), BEYAZ)
    ic = int(olcu * (1 - 2 * bosluk))
    oran = min(ic / isaret.width, ic / isaret.height)
    kucuk = isaret.resize((max(1, round(isaret.width * oran)),
                           max(1, round(isaret.height * oran))), Image.LANCZOS)
    tuval.alpha_composite(kucuk, ((olcu - kucuk.width) // 2,
                                  (olcu - kucuk.height) // 2))
    return tuval.convert("RGB")


class Command(BaseCommand):
    help = "statik/simge/ altındaki favicon, dokunma simgesi ve paylaşım görselini üretir."

    def handle(self, *args, **opts):
        from PIL import Image
        kok = _kok()
        logo = Image.open(kok / "logo-seffaf.png").convert("RGBA")
        isaret = logo.crop(ISARET_KUTUSU)
        hedef = kok / "simge"
        hedef.mkdir(exist_ok=True)

        _kare(isaret, 48, 0.06).save(hedef / "favicon.ico",
                                     sizes=[(16, 16), (32, 32), (48, 48)])
        _kare(isaret, 32, 0.06).save(hedef / "simge-32.png", optimize=True)
        _kare(isaret, 180).save(hedef / "apple-touch-icon.png", optimize=True)
        _kare(isaret, 192).save(hedef / "simge-192.png", optimize=True)
        _kare(isaret, 512).save(hedef / "simge-512.png", optimize=True)

        paylasim = Image.new("RGBA", (1200, 630), BEYAZ)
        oran = 900 / logo.width
        buyuk = logo.resize((900, round(logo.height * oran)), Image.LANCZOS)
        paylasim.alpha_composite(buyuk, ((1200 - buyuk.width) // 2,
                                         (630 - buyuk.height) // 2))
        paylasim.convert("RGB").save(hedef / "paylasim.png", optimize=True)
        self.stdout.write(f"Simgeler yazıldı: {hedef}")
