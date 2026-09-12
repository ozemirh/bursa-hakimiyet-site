"""X (Twitter) — API v2 `POST /2/tweets`.

Kimlik doğrulama **OAuth 1.0a**: X'in gönderi ucu uygulama jetonuyla
(bearer) yazmaya izin vermiyor, kullanıcı bağlamı istiyor. İmzalama
`hmac` + `hashlib` ile yapılıyor; dışarıdan paket gelmedi.

JSON gövdeli isteklerde gövde imzaya girmez: imza yalnız yöntem, adres ve
`oauth_*` parametreleri üzerinden kurulur. Bu, X'in kendi dökümanındaki
kuraldır ve yanlış uygulandığında 401 döner.

**Görsel gönderilmiyor.** Medya yükleme ayrı bir uç (v1.1 `media/upload`)
ve üç adımlı; haber gönderisinde bağlantının kart önizlemesi zaten görseli
gösteriyor. Gerekirse ayrıca karara bağlanır.
"""

import base64
import hashlib
import hmac
import secrets
import time
import urllib.parse

from .taban import Saglayici, Sonuc, istek

GONDERI_UCU = "https://api.x.com/2/tweets"


def _kacir(deger: str) -> str:
    return urllib.parse.quote(str(deger), safe="~")


def oauth_basligi(yontem: str, adres: str, hesap) -> str:
    """OAuth 1.0a `Authorization` başlığı."""
    parametreler = {
        "oauth_consumer_key": hesap.gizli("tuketici_anahtari"),
        "oauth_nonce": secrets.token_hex(16),
        "oauth_signature_method": "HMAC-SHA1",
        "oauth_timestamp": str(int(time.time())),
        "oauth_token": hesap.gizli("erisim_jetonu"),
        "oauth_version": "1.0",
    }
    sirali = "&".join(
        f"{_kacir(k)}={_kacir(v)}" for k, v in sorted(parametreler.items()))
    taban = "&".join([yontem.upper(), _kacir(adres), _kacir(sirali)])
    anahtar = (_kacir(hesap.gizli("tuketici_gizi")) + "&"
               + _kacir(hesap.gizli("erisim_gizi")))
    imza = hmac.new(anahtar.encode(), taban.encode(), hashlib.sha1).digest()
    parametreler["oauth_signature"] = base64.b64encode(imza).decode()
    return "OAuth " + ", ".join(
        f'{_kacir(k)}="{_kacir(v)}"' for k, v in sorted(parametreler.items()))


class XSaglayici(Saglayici):
    kod = "x"
    ad = "X (Twitter)"
    gerekli = (
        ("tuketici_anahtari", "API anahtarı"),
        ("tuketici_gizi", "API gizli anahtarı"),
        ("erisim_jetonu", "Erişim jetonu"),
        ("erisim_gizi", "Erişim jetonu gizi"),
    )
    yardim = ("developer.x.com → Projects & Apps → Keys and tokens. "
              "Gönderi atabilmek için uygulamanın izni “Read and write” "
              "olmalı; ücretsiz katman aylık gönderi sınırı taşır.")

    def gonder(self, hesap, gonderi) -> Sonuc:
        baslik = oauth_basligi("POST", GONDERI_UCU, hesap)
        yanit = istek(GONDERI_UCU, json_govde={"text": gonderi.metin},
                      basliklar={"Authorization": baslik})
        veri = yanit.get("data") or {}
        kimlik = str(veri.get("id") or "")
        kullanici = hesap.kullanici_adi or "i"
        adres = f"https://x.com/{kullanici}/status/{kimlik}" if kimlik else ""
        return Sonuc(bool(kimlik), dis_kimlik=kimlik, dis_adres=adres,
                     hata="" if kimlik else "X gönderi kimliği döndürmedi.")
