"""Facebook sayfası ve Instagram — Meta Graph API.

İkisi aynı API'nin iki ucu ama **davranışları ayrı**:

    Facebook   /{sayfa}/feed          metin + bağlantı, görsel isteğe bağlı
    Instagram  /{ig}/media → publish  GÖRSEL ZORUNLU, bağlantı tıklanmaz

Instagram'ın iki adımlı olması bir tercih değil: önce kap (container)
oluşturulur, sonra yayımlanır. Birinci adım tutup ikincisi düşerse gönderi
Instagram'da **görünmez** ve bizde de "hata" yazar — sessiz yarım gönderi
olmaz.

Instagram'ın görseli kendi sunucusundan çekmesi gerekir; yani haberin
fotoğrafı dışarıdan erişilebilir bir adreste olmalı. Site yayında değilken
(yalnız 127.0.0.1) bu uç çalışmaz ve bunu hata metni açıkça söyler.
"""

from .taban import Saglayici, Sonuc, SosyalHata, istek

SURUM = "v21.0"
KOK = f"https://graph.facebook.com/{SURUM}"


class FacebookSaglayici(Saglayici):
    kod = "facebook"
    ad = "Facebook sayfası"
    gerekli = (
        ("sayfa_kimligi", "Sayfa kimliği"),
        ("sayfa_jetonu", "Sayfa erişim jetonu"),
    )
    yardim = ("developers.facebook.com → uygulama → Graph API Explorer. "
              "Sayfa jetonu `pages_manage_posts` ve `pages_read_engagement` "
              "izinlerini taşımalı; kısa ömürlü jetonu uzun ömürlüye "
              "çevirmeyi unutmayın.")

    def gonder(self, hesap, gonderi) -> Sonuc:
        sayfa = hesap.gizli("sayfa_kimligi")
        veri = {
            "message": gonderi.metin,
            "access_token": hesap.gizli("sayfa_jetonu"),
        }
        adres = gonderi.haber_adresi()
        if adres:
            veri["link"] = adres
        yanit = istek(f"{KOK}/{sayfa}/feed", veri=veri)
        kimlik = str(yanit.get("id") or "")
        if not kimlik:
            return Sonuc(False, hata="Facebook gönderi kimliği döndürmedi.")
        return Sonuc(True, dis_kimlik=kimlik,
                     dis_adres=f"https://www.facebook.com/{kimlik}")


class InstagramSaglayici(Saglayici):
    kod = "instagram"
    ad = "Instagram"
    gorsel_zorunlu = True
    gerekli = (
        ("ig_kimligi", "Instagram iş hesabı kimliği"),
        ("jeton", "Erişim jetonu"),
    )
    yardim = ("Instagram hesabı **iş/yaratıcı** olmalı ve bir Facebook "
              "sayfasına bağlı olmalı. Jeton `instagram_content_publish` "
              "izni ister. Görsel, Instagram'ın erişebileceği bir adreste "
              "olmak zorunda: site yayında değilse bu uç çalışmaz.")

    def gonder(self, hesap, gonderi) -> Sonuc:
        if not gonderi.gorsel_adres:
            raise SosyalHata(
                "Instagram görselsiz gönderi kabul etmiyor. Haberin yerel "
                "görseli yok ya da site kökü dışarıdan erişilebilir değil.")
        ig = hesap.gizli("ig_kimligi")
        jeton = hesap.gizli("jeton")

        kap = istek(f"{KOK}/{ig}/media", veri={
            "image_url": gonderi.gorsel_adres,
            "caption": gonderi.metin,
            "access_token": jeton,
        })
        kap_kimligi = str(kap.get("id") or "")
        if not kap_kimligi:
            return Sonuc(False, hata="Instagram medya kabı oluşmadı.")

        yayin = istek(f"{KOK}/{ig}/media_publish", veri={
            "creation_id": kap_kimligi,
            "access_token": jeton,
        })
        kimlik = str(yayin.get("id") or "")
        if not kimlik:
            return Sonuc(False, hata=(
                "Medya kabı oluştu ama yayımlanamadı "
                f"(kap {kap_kimligi}). Gönderi Instagram'da görünmüyor."))
        return Sonuc(True, dis_kimlik=kimlik,
                     dis_adres=self._kalici_adres(kimlik, jeton))

    @staticmethod
    def _kalici_adres(kimlik: str, jeton: str) -> str:
        """Gönderinin insan adresi ayrı bir çağrıyla alınır.

        Yayım yanıtı medya **kimliği** döndürür; `instagram.com/p/…`
        adresindeki kısa kod bu değildir. Uydurulmuş bir adres yazmaktansa
        sormak, soramazsak boş bırakmak doğru: gönderi zaten atıldı, adres
        yalnız panelde bağlantı olsun diye duruyor.
        """
        try:
            yanit = istek(f"{KOK}/{kimlik}?fields=permalink"
                          f"&access_token={jeton}", yontem="GET")
        except SosyalHata:
            return ""
        return str(yanit.get("permalink") or "")
