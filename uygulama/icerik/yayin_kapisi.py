"""Tek yayın kapısı — 19 Ekim 2026, Paket F madde 2.

Bir haberin yayına çıkabileceği her yol BURADAN geçer:

    panel formu (ekle / düzenle)   → `formlar.HaberForm.clean`
    toplu "Yayına al"              → `panel._fiil_yayina_al`
    yapay zekâ taslağı             → `yz_kopru.taslak_yaz` (Pasif doğar;
                                     eksik listesi bu işlevden yazılır)
    eczane servis haberi           → `eczane_haberi` komutu

Önceden üç yolun üç ayrı eşiği vardı ve biri hiç yoktu: muhabir "Haber ekle"
formunda `durum=Aktif` gönderince haber doğrudan yayına çıkıyordu; toplu fiil
`[yazılacak]` işaretini ve boş slug'ı denetlemediği için `/bursa/-1696500`
gibi 404 veren adresler doğuyordu (DEGERLENDIRME-2026-10 §3 bulgu 4).

İki ayrı soru, iki ayrı işlev:

1. **Yetki** (`yayin_yetkisi`): kim yayınlar? §11 — muhabir yayınlayamaz;
   kendi haberi ile başkasınınki ayrı yetkiliktir.
2. **İçerik** (`icerik_eksikleri`): ne yayınlanır? §4 eşiği + editoryal
   kurallar: başlıkta yapay zekâ işareti yok, adres (slug) kurulabiliyor,
   spot, en az iki paragraf, en az bir etiket ve **kaynak kuralı**:

       ajans / dış yayın  → en az bir kaynak kaydı
       kendi muhabirimiz  → muhabir adı
       belirtilmemiş      → yeni yayında kaynak türü seçilmeli

Kaynak kuralı yeni bir kural değil, `CLAUDE.md`deki "kaynak her zaman
belirtilir" kuralının kapıda uygulanmasıdır. Tek istisna: ZATEN yayında olan
arşiv kaydının kaynak türü boşsa (göçte ölçülemedi, 337 bin haber) düzeltme
kaydı engellenmez — düzeltme hakkı yasal bir yükümlülüktür ve olmayan kaynağı
editöre uydurtmak kuralın tersidir. Kaynak türü SEÇİLMİŞSE kural her zaman
işler.
"""

from __future__ import annotations

from .arama_metni import slugla
from .models import YZ_BASLIK_ISARETI, Haber

EN_AZ_PARAGRAF = 2


def paragraf_sayisi(govde: str) -> int:
    """Gövdedeki paragraf sayısı (HTML `<p>` ya da boş satırla ayrılmış düz metin)."""
    if not govde:
        return 0
    etiketli = govde.lower().count("<p")
    if etiketli:
        return etiketli
    return len([p for p in govde.split("\n\n") if p.strip()])


def yayin_yetkisi(kullanici, haber=None) -> bool:
    """Bu kullanıcı bu haberi yayına alabilir / yayında değiştirebilir mi?

    Kaydedilmemiş haber kullanıcının kendi haberidir. Arşiv kaydının
    (`olusturan` boş) sahibi yoktur, "başkasının haberi" sayılır.
    """
    if kullanici is None or not getattr(kullanici, "is_authenticated", False):
        return False
    kendisinin = (haber is None or haber.pk is None
                  or haber.olusturan_id == kullanici.pk)
    return kullanici.has_perm("icerik.kendi_haberini_yayinlama" if kendisinin
                              else "icerik.baskasinin_haberini_yayinlama")


def icerik_eksikleri(*, baslik: str, slug: str, spot: str, govde: str,
                     etiket_sayisi: int, kaynak_turu: str, kaynak_sayisi: int,
                     muhabir: str, kaynak_turu_sart: bool = True) -> list[str]:
    """Yayına çıkmak için eksik olanların okunur listesi. Boş liste = geçer."""
    eksik = []
    baslik = (baslik or "").strip()
    if baslik.startswith(YZ_BASLIK_ISARETI):
        eksik.append("başlık (taslakta '%s' işareti duruyor)" % YZ_BASLIK_ISARETI)
    elif not (slug or "").strip():
        eksik.append("adres (başlıktan slug kurulamadı)")
    if not (spot or "").strip():
        eksik.append("spot")
    if paragraf_sayisi((govde or "").strip()) < EN_AZ_PARAGRAF:
        eksik.append(f"gövde (en az {EN_AZ_PARAGRAF} paragraf)")
    if etiket_sayisi < 1:
        eksik.append("en az bir etiket")
    if kaynak_turu in (Haber.KAYNAK_AJANS, Haber.KAYNAK_DIS_YAYIN):
        if kaynak_sayisi < 1:
            eksik.append("kaynak (ajans ya da dış yayın haberinde en az bir "
                         "kaynak seçilmeli)")
    elif kaynak_turu == Haber.KAYNAK_MUHABIR:
        if not (muhabir or "").strip():
            eksik.append("muhabir adı")
    elif kaynak_turu_sart:
        eksik.append("kaynak türü")
    return eksik


def haber_eksikleri(haber: Haber) -> list[str]:
    """Kayıtlı bir haber için — toplu fiil ve komutlar.

    `etiketler` ve `kaynaklar` ön çekimliyse ek sorgu açmaz.
    """
    return icerik_eksikleri(
        baslik=haber.baslik, slug=haber.slug, spot=haber.spot,
        govde=haber.govde,
        etiket_sayisi=len(haber.etiketler.all()),
        kaynak_turu=haber.kaynak_turu,
        kaynak_sayisi=len(haber.kaynaklar.all()),
        muhabir=haber.muhabir,
        kaynak_turu_sart=haber.durum != Haber.DURUM_AKTIF)


def form_eksikleri(veri: dict, ornek: Haber) -> list[str]:
    """Haber formunun temizlenmiş verisi için. Slug, kaydedilince
    başlıktan kurulacak değerle denetlenir (`panel._kaydet`)."""
    baslik = veri.get("baslik") or ""
    slug = ornek.slug or ("" if baslik.startswith(YZ_BASLIK_ISARETI)
                          else slugla(baslik, 220) or "haber")
    return icerik_eksikleri(
        baslik=baslik, slug=slug, spot=veri.get("spot") or "",
        govde=veri.get("govde") or "",
        etiket_sayisi=len(veri.get("etiketler") or []),
        kaynak_turu=veri.get("kaynak_turu") or "",
        kaynak_sayisi=len(veri.get("kaynaklar") or []),
        muhabir=veri.get("muhabir") or "",
        kaynak_turu_sart=(ornek.pk is None or ornek.durum != Haber.DURUM_AKTIF))
