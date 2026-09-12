"""Sağlayıcı defteri.

Platform kodu → sağlayıcı nesnesi. Yeni platform eklemek bu sözlüğe bir
satır ve bir dosya demek; kuyruk, panel ve metin katmanı değişmez.

Tanımsız bir platform kodu **sessizce** geçilmez: `BilinmeyenSaglayici`
her zaman eksik kimlik bildirir ve otomatik gönderime girmez, böylece
veritabanında kalmış eski bir kod yüzünden gönderi kaybolmaz.
"""

from .meta import FacebookSaglayici, InstagramSaglayici
from .taban import Saglayici, Sonuc, SosyalHata
from .x import XSaglayici
from .youtube import YouTubeSaglayici

DEFTER = {
    XSaglayici.kod: XSaglayici(),
    FacebookSaglayici.kod: FacebookSaglayici(),
    InstagramSaglayici.kod: InstagramSaglayici(),
    YouTubeSaglayici.kod: YouTubeSaglayici(),
}


class BilinmeyenSaglayici(Saglayici):
    kod = ""
    ad = "Tanınmayan platform"
    otomatik_olur = False

    def eksik_alanlar(self, hesap) -> list:
        return ["tanınmayan platform"]

    def gonder(self, hesap, gonderi) -> Sonuc:
        return Sonuc(False, hata=f"Tanınmayan platform: {hesap.platform}")


def saglayici_bul(platform: str) -> Saglayici:
    return DEFTER.get(platform) or BilinmeyenSaglayici()


__all__ = ["DEFTER", "Saglayici", "Sonuc", "SosyalHata", "saglayici_bul"]
