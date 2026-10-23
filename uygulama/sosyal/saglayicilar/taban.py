"""Sağlayıcı sözleşmesi ve ortak HTTP katmanı.

Dışarıya çıkan **tek** yer burasıdır. Sağlayıcılar `urllib` kullanır; yeni
paket eklenmedi — `arac/` tarafındaki "standart kütüphane yeter" çizgisi
burada da tutuldu.

Ağ hatası sessizce yutulmaz: her hata `SosyalHata` olur, kuyruk satırına
metniyle yazılır ve panelde görünür. Gönderilememiş bir gönderiyi
gönderilmiş göstermek, bu aracın yapabileceği en kötü şeydir.
"""

import json
import urllib.error
import urllib.parse
import urllib.request

# Ağ beklemesi. Panelden "Şimdi gönder" denince istek kullanıcıyı bekletir;
# bu yüzden kısa. Kuyruk komutu da aynı süreyi kullanır.
ZAMAN_ASIMI = 15


class SosyalHata(Exception):
    """Gönderim başarısız — metni kuyruk satırına yazılır."""


class Sonuc:
    """Tek bir gönderimin sonucu."""

    def __init__(self, basarili: bool, dis_kimlik: str = "",
                 dis_adres: str = "", hata: str = ""):
        self.basarili = basarili
        self.dis_kimlik = dis_kimlik
        self.dis_adres = dis_adres
        self.hata = hata


class Saglayici:
    """Bir platformun gönderim yolu.

    `gerekli` alanları hesabın `gizli_ayar` sözlüğünden ya da ortam
    değişkeninden okunur (`SosyalHesap.gizli`). Biri bile eksikse hesap
    otomatik gönderemez; kuyruk satırı ELLE durumunda açılır.
    """

    kod = ""
    ad = ""
    otomatik_olur = True
    gorsel_zorunlu = False
    gerekli = ()          # ((alan_kodu, "Görünen ad"), ...)
    yardim = ""

    def eksik_alanlar(self, hesap) -> list:
        return [ad for kod, ad in self.gerekli if not hesap.gizli(kod)]

    def gonder(self, hesap, gonderi) -> Sonuc:
        raise NotImplementedError


def _govde_oku(hata) -> str:
    try:
        ham = hata.read().decode("utf-8", "replace")
    except Exception:
        return ""
    try:
        veri = json.loads(ham)
    except ValueError:
        return ham[:300]
    # Meta ve X hata gövdeleri farklı biçimde; ikisini de okunur kıl.
    if isinstance(veri, dict):
        for anahtar in ("error", "detail", "title", "message"):
            deger = veri.get(anahtar)
            if isinstance(deger, dict):
                return str(deger.get("message") or deger)[:300]
            if deger:
                return str(deger)[:300]
    return ham[:300]


def istek(adres: str, *, veri=None, json_govde=None, basliklar=None,
          yontem="POST") -> dict:
    """Tek HTTP isteği. JSON döndürür, hatayı `SosyalHata`ya çevirir."""
    basliklar = dict(basliklar or {})
    govde = None
    if json_govde is not None:
        govde = json.dumps(json_govde).encode("utf-8")
        basliklar.setdefault("Content-Type", "application/json")
    elif veri is not None:
        govde = urllib.parse.urlencode(veri).encode("utf-8")

    istek_nesnesi = urllib.request.Request(adres, data=govde,
                                           headers=basliklar, method=yontem)
    try:
        with urllib.request.urlopen(istek_nesnesi, timeout=ZAMAN_ASIMI) as yanit:
            ham = yanit.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as hata:
        raise SosyalHata(f"HTTP {hata.code}: {_govde_oku(hata)}") from hata
    except urllib.error.URLError as hata:
        raise SosyalHata(f"Bağlanılamadı: {hata.reason}") from hata
    except OSError as hata:                       # zaman aşımı da buraya düşer
        raise SosyalHata(f"Ağ hatası: {hata}") from hata

    if not ham:
        return {}
    try:
        return json.loads(ham)
    except ValueError:
        raise SosyalHata(f"Beklenmeyen yanıt: {ham[:200]}")
