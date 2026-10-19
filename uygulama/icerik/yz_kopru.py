# -*- coding: utf-8 -*-
"""Yapay zekâ editör aracını (`arac/`) panele bağlayan köprü.

Araç demo döneminde yazıldı ve kendi başına çalışan bir Python paketidir:
adresi indirir (`ayiklayici`), taslağı kurar (`kural_motoru` / `yz_cli` /
`yz_skill`) ve JSON döndürür. Ürüne geçince araç orada kaldı; `arac/yayin.py`
hâlâ `tasarim-*.html` demo şablonlarına yazıyor. Bu modül o boşluğu kapatır:
aynı paketi alır, **veritabanında bir `Haber` taslağı** açar.

## Üç sınır — bilerek

1. **Taslak açar, yayınlamaz.** Kayıt `durum=Pasif · hazirlik=taslak` doğar.
   Yayına alma kararı panelin kendi formundan, kendi yetkisiyle ve kendi
   eşiğiyle (spot + en az iki paragraf + etiket) verilir. Buradan yayına
   giden hiçbir yol yok.
2. **Görsel indirilmez.** Kaynağın fotoğrafının adresi `gorsel_url`e yazılır,
   dosya indirilmez (`gorsel_var=False`). Demo kararı fotoğrafı indiriyordu
   ama orada izleyici yayın ekibiydi; burada gerçek gazete yayınlıyor ve hak
   durumu haber haber doğrulanmalı. İndirme ayrı ve açık bir düğmedir.
3. **Slug boş bırakılır.** Kural motoru başlık yazmaz; taslağın başlığı
   `[yazılacak] …` işaretiyle doğar. O başlıktan slug üretilseydi adres
   kalıcı olarak bozulurdu — panelin kaydı slug'ı ilk kaydedişte, editörün
   yazdığı gerçek başlıktan kurar (`panel._kaydet`).

Araç `arac/` klasöründen **tembel** içe aktarılır: Django açılışında
`sys.path`e dokunulmaz, sunucu araç olmadan da ayağa kalkar.
"""

from __future__ import annotations

import json
import re
import sys
from html import escape
from pathlib import Path

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from taksonomi.models import Ilce, Kategori, Kaynak

from . import goc_kaynak
from .arama_metni import anahtar
from .formlar import etiketleri_kur
from .kimlik import yeni_kayit_kaydet
from .models import YZ_BASLIK_ISARETI, Haber

ARAC_KOK = Path(settings.BASE_DIR).parent / "arac"
CIKTI_KOK = ARAC_KOK / "cikti"

#: Panelde gösterilen sağlayıcılar. Sıra editör sayfasındakiyle aynı: önce
#: model kullanmayan yol. `claude` sağlayıcısı listede yok — API anahtarı
#: ister, bu makinede anahtar yok ve `cli` aynı işi anahtarsız yapıyor.
SAGLAYICILAR = [
    ("kural", "Kural motoru",
     "Model kullanmaz; kategori, ilçe, etiket ve uyarıları doldurur, "
     "gövdeyi yazmaz. Anlık."),
    ("cli", "Yapay zekâ",
     "Makinedeki `claude` oturumuyla tam taslak — başlık, spot ve gövde "
     "dahil. Yaklaşık 1 dakika."),
    ("skill", "Yapay zekâ + denetim",
     "Aynı taslağı üretir, sonra `denetim.py` ile kendi çıktısını denetleyip "
     "bulguları düzeltir. Yaklaşık 2-3 dakika."),
]
SAGLAYICI_KODLARI = [k for k, _, _ in SAGLAYICILAR]

#: Kural motoru başlık yazmadığında taslağın başına konan işaret. Değer
#: `models` içinde duruyor; formun yayın kapısı da onu okuyor ve bu işareti
#: taşıyan haberi yayına almıyor.
BASLIK_ISARETI = YZ_BASLIK_ISARETI

#: Aracın 14 sözlük kategorisi → gazetenin 13 gerçek kategorisi.
#: Araç demo döneminde kendi kategori listesiyle yazıldı (`arac/sozluk.json`),
#: gazetenin listesi ise `taksonomi_kategori` tablosunda ve donmuş slug'lara
#: bağlı. İkisi bire bir örtüşmüyor; eşleme burada, tek yerde durur.
KATEGORI_ESLEME = {
    "Çevre ve su": "BURSA",
    "Ulaşım": "BURSA",
    "Ekonomi": "EKONOMİ",
    "Asayiş": "GÜNDEM",
    "Yargı": "GÜNDEM",
    "Siyaset": "GÜNDEM",
    "Sağlık": "SAĞLIK",
    "Eğitim": "YAŞAM",
    "Spor": "SPOR",
    "Kültür": "YAŞAM",
    "Tarım": "EKONOMİ",
    "Teknoloji": "TEKNOLOJİ",
    "Yaşam": "YAŞAM",
    "Gündem": "GÜNDEM",
}
VARSAYILAN_KATEGORI = "GÜNDEM"
BURSA_KATEGORI = "BURSA"


class YzHatasi(Exception):
    """Editöre gösterilebilecek, anlaşılır hata."""


# ---------------------------------------------------------------------------
# Aracı yükleme
# ---------------------------------------------------------------------------

def arac_var_mi() -> bool:
    return (ARAC_KOK / "ayiklayici.py").exists()


def _arac():
    """`arac/` modüllerini tembel yükler ve modül nesnelerini döndürür.

    Araç dosyaları birbirine düz adla bakıyor (`import konu_eslestirme`),
    bu yüzden klasör `sys.path`e girmek zorunda. Giriş bir kez yapılır.
    """
    if not arac_var_mi():
        raise YzHatasi(
            "Araç klasörü bulunamadı: %s. Depo eksik indirilmiş olabilir."
            % ARAC_KOK)
    yol = str(ARAC_KOK)
    if yol not in sys.path:
        sys.path.insert(0, yol)
    import ayiklayici
    import kural_motoru
    return ayiklayici, kural_motoru


# ---------------------------------------------------------------------------
# Paket üretimi
# ---------------------------------------------------------------------------

def paket_uret(adres: str, saglayici: str = "kural") -> dict:
    """Adresi indirir, ayıklar ve seçilen sağlayıcıyla taslak paketi kurar.

    Veritabanına dokunmaz; dönen sözlük aracın kendi paket biçimidir
    (`kaynak` · `taslak` · `uretim` · `tezgah`).
    """
    adres = (adres or "").strip()
    if not adres.lower().startswith(("http://", "https://")):
        raise YzHatasi("Geçerli bir adres verin (http:// ya da https:// ile).")
    if saglayici not in SAGLAYICI_KODLARI:
        raise YzHatasi("Bilinmeyen sağlayıcı: %s" % saglayici)

    ayiklayici, kural_motoru = _arac()
    try:
        kaynak = ayiklayici.ayikla(ayiklayici.getir(adres), adres)
    except Exception as e:                      # noqa: BLE001 — editöre göster
        raise YzHatasi("Kaynak alınamadı: %s" % e) from e
    if not (kaynak.get("orijinal_govde") or "").strip():
        raise YzHatasi(
            "Sayfadan metin çıkarılamadı. Sayfa JavaScript ile kuruluyor ya da "
            "ödeme duvarı arkasında olabilir.")

    paket = {"kaynak": kaynak}
    try:
        if saglayici == "kural":
            paket.update(kural_motoru.taslak_uret_kural(kaynak))
        elif saglayici == "cli":
            import yz_cli
            paket.update(yz_cli.taslak_uret_cli(kaynak))
        else:
            import yz_skill
            paket.update(yz_skill.taslak_uret_skill(kaynak))
    except YzHatasi:
        raise
    except Exception as e:                      # noqa: BLE001 — editöre göster
        raise YzHatasi("Taslak üretilemedi: %s" % e) from e
    return paket


def paket_kaydet(paket: dict, haber_id: int) -> Path:
    """Paketi `arac/cikti/haber-<id>.json` olarak diske yazar.

    İki işe yarar: taslak ekranı kaynağı ve tezgahı buradan okur, dosya
    ayrıca `yapay-zeka-editor.html` sayfasına sürüklenip bırakılabilir.
    """
    CIKTI_KOK.mkdir(parents=True, exist_ok=True)
    yol = CIKTI_KOK / ("haber-%d.json" % haber_id)
    yol.write_text(json.dumps(paket, ensure_ascii=False, indent=2),
                   encoding="utf-8")
    return yol


def paket_oku(haber_id: int) -> dict | None:
    yol = CIKTI_KOK / ("haber-%d.json" % haber_id)
    if not yol.exists():
        return None
    try:
        return json.loads(yol.read_text(encoding="utf-8"))
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Paket → Haber alanları
# ---------------------------------------------------------------------------

def _metin_havuzu(paket: dict) -> str:
    k = paket.get("kaynak") or {}
    return " ".join([k.get("orijinal_baslik") or "",
                     k.get("orijinal_spot") or "",
                     k.get("orijinal_govde") or ""]).lower()


def kategori_sec(paket: dict):
    """Aracın kategori tahminini gazetenin kategorisine çevirir.

    Gerekçe de döner: editör neyin neden seçildiğini görmeli, ekranda yazıyor.
    """
    taslak = paket.get("taslak") or {}
    arac_adi = (taslak.get("kategori") or "").strip()
    hedef = KATEGORI_ESLEME.get(arac_adi, VARSAYILAN_KATEGORI)
    gerekce = "Araç '%s' dedi → %s." % (arac_adi or "—", hedef)

    # Yerel gazete kuralı: ulusal eksende "Gündem"e düşen ama Bursa ilgisi
    # ölçülen haber BURSA'ya gider.
    bursa = (taslak.get("bursa_ilgisi") or {}).get("var_mi")
    if hedef == VARSAYILAN_KATEGORI and bursa:
        hedef = BURSA_KATEGORI
        gerekce += " Bursa ilgisi ölçüldüğü için BURSA'ya alındı."
    if hedef == "SPOR" and "bursaspor" in _metin_havuzu(paket):
        hedef = "BURSASPOR"
        gerekce += " Metinde Bursaspor geçtiği için BURSASPOR'a alındı."

    kategori = Kategori.objects.filter(ad=hedef, aktif=True).first()
    if kategori is None:
        kategori = (Kategori.objects.filter(ad=VARSAYILAN_KATEGORI, aktif=True).first()
                    or Kategori.objects.filter(aktif=True).order_by("sira", "ad").first())
        gerekce += " (%s bulunamadı, ilk aktif kategoriye düşüldü.)" % hedef
    return kategori, gerekce


def ilce_sec(paket: dict):
    ad = ((paket.get("taslak") or {}).get("ilce") or "").strip()
    if not ad:
        return None
    return Ilce.objects.filter(ad__iexact=ad).first()


def kaynak_sec(paket: dict):
    """Kaynak kaydını bulur/açar. Döner: (kaynak, kaynak_turu, gerekce).

    İki kural birleşiyor:

    - `CLAUDE.md`: haberi aldığımız sayfa kendi kaynağını belirtmişse **kaynak
      odur**; aracı yayın kaynak diye anılmaz. `ayiklayici.asil_kaynak_bul`
      bunu zaten arıyor, önceliği onun.
    - `goc_kaynak.kaynak_kabul`: meta yazar değerleri ("Haber Merkezi"),
      kendi yayınımız ve cümle parçaları kaynak sayılmaz. Reddedilen haber
      **kaynaksız** kalır; taksonomi tablosuna çöp kayıt açılmaz.
    """
    k = paket.get("kaynak") or {}
    ad = (k.get("asil_kaynak") or "").strip() or (k.get("kaynak_adi") or "").strip()
    if not ad:
        return None, "", "Kaynak adı ayıklanamadı; kaynak boş bırakıldı."

    kabul, sebep = goc_kaynak.kaynak_kabul(ad)
    if not kabul:
        return None, "", ("'%s' kaynak sayılmadı (%s); kaynak boş bırakıldı."
                          % (ad, sebep))

    tur = Kaynak.TUR_AJANS if _ajans_mi(ad) else Kaynak.TUR_DIS_YAYIN
    kayit = Kaynak.objects.filter(ad__iexact=ad).first()
    if kayit is None:
        kayit = Kaynak.objects.create(ad=ad[:120], tur=tur, aktif=True)
        gerekce = "'%s' kaynak listesinde yoktu, açıldı." % kayit.ad
    else:
        kayit = kayit.birlesti_ile or kayit
        tur = kayit.tur
        gerekce = "Kaynak: %s." % kayit.ad
    haber_turu = (Haber.KAYNAK_AJANS if tur == Kaynak.TUR_AJANS
                  else Haber.KAYNAK_DIS_YAYIN)
    return kayit, haber_turu, gerekce


def _ajans_mi(ad: str) -> bool:
    try:
        _, kural_motoru = _arac()
        ajanslar = kural_motoru.sozluk_yukle().get("ajanslar") or []
    except Exception:                            # noqa: BLE001 — sözlük yoksa
        return False
    duz = anahtar(ad)
    return any(anahtar(a) == duz for a in ajanslar)


def baslik_al(paket: dict):
    """(başlık, editör_yazacak_mı). Kural motoru başlık yazmaz."""
    taslak = paket.get("taslak") or {}
    secenekler = taslak.get("baslik_secenekleri") or []
    sira = taslak.get("onerilen_baslik_indeksi") or 0
    metin = ""
    if isinstance(sira, int) and 0 <= sira < len(secenekler):
        metin = (secenekler[sira].get("metin") or "").strip()
    if not metin:
        metin = (taslak.get("baslik") or "").strip()
    if metin:
        return metin[:300], False
    ham = ((paket.get("kaynak") or {}).get("orijinal_baslik") or "").strip()
    return ("%s %s" % (BASLIK_ISARETI, ham)).strip()[:300], True


def govde_html(paket: dict) -> str:
    """Taslak bloklarını panelin beklediği HTML'e çevirir.

    Kural motorunda bloklar boş gelir ve sonuç boş string olur — gövdeyi
    editör yazar, kaynaktan cümle taşınmaz.

    **`quote=False` bilerek.** `html.escape` varsayılan olarak tırnakları da
    kaçırır (`'` → `&#x27;`, `"` → `&quot;`); bu NİTELİK DEĞERİ içindir.
    Burada yazdığımız yer metin gövdesi ve tırnak orada olduğu gibi
    durabilir. Varsayılanla bırakıldığında modelin yazdığı gövde panele
    `İstanbul&#x27;da` diye düşüyordu (5 Eylül 2026'da görüldü).
    `&`, `<`, `>` kaçırılmaya devam ediyor — işaretlemeyi onlar bozar.
    """
    parcalar = []
    for blok in (paket.get("taslak") or {}).get("govde") or []:
        metin = (blok.get("metin") or "").strip()
        if not metin:
            continue
        etiket = "h2" if blok.get("tur") == "ara_baslik" else "p"
        parcalar.append("<%s>%s</%s>"
                        % (etiket, escape(metin, quote=False), etiket))
    return "\n\n".join(parcalar)


def _kelime_say(govde: str) -> int:
    return len([p for p in re.sub(r"<[^>]+>", " ", govde).split() if p])


# ---------------------------------------------------------------------------
# Taslağı veritabanına yazma
# ---------------------------------------------------------------------------

@transaction.atomic
def taslak_yaz(paket: dict, kullanici):
    """Paketten **taslak** bir `Haber` açar. Yayına almaz.

    İkinci dönen değer, ekranda gösterilecek gerekçe satırlarıdır.
    """
    taslak = paket.get("taslak") or {}
    kaynak = paket.get("kaynak") or {}
    notlar = []

    kategori, kategori_gerekce = kategori_sec(paket)
    if kategori is None:
        raise YzHatasi("Veritabanında aktif kategori yok; önce taksonomi kurulmalı.")
    notlar.append(kategori_gerekce)

    ilce = ilce_sec(paket)
    if ilce is not None:
        notlar.append("İlçe: %s." % ilce.ad)

    kaynak_kaydi, kaynak_turu, kaynak_gerekce = kaynak_sec(paket)
    notlar.append(kaynak_gerekce)

    baslik, yazilacak = baslik_al(paket)
    if yazilacak:
        notlar.append("Başlığı motor yazmadı; '%s' işaretiyle bırakıldı. "
                      "Yayına alınabilmesi için editör yazacak."
                      % BASLIK_ISARETI)
    govde = govde_html(paket)
    if not govde:
        notlar.append("Gövde boş: kural motoru dil üretmez, kaynağın ham "
                      "cümleleri tezgahta duruyor.")

    haber = Haber(
        slug="",                       # editörün yazacağı başlıktan kurulacak
        baslik=baslik,
        spot=(taslak.get("spot") or "").strip(),
        govde=govde,
        kategori=kategori,
        ilce=ilce,
        kaynak_turu=kaynak_turu,
        olusturan=kullanici,
        durum=Haber.DURUM_PASIF,       # yayınlamaz — panel formu yayınlar
        hazirlik="taslak",
        gorsel_url=(kaynak.get("gorsel_url") or "")[:600],
        gorsel_alt=((taslak.get("gorsel_alt") or kaynak.get("gorsel_alt") or "")
                    .strip()[:300]),
        gorsel_var=False,              # dosya indirilmedi; hak durumu ayrı karar
        odak_kelime=(taslak.get("odak_kelime") or "").strip()[:120],
        seo_baslik=(taslak.get("seo_baslik") or "").strip()[:200],
        kelime_sayisi=_kelime_say(govde),
    )
    # Kimlik tek kaynaktan (`icerik/kimlik.py`): eski sitenin aralığıyla
    # çakışmayan taban, `force_insert` ve çakışmada yeniden deneme.
    yeni_kayit_kaydet(haber)

    if kaynak_kaydi is not None:
        haber.kaynaklar.set([kaynak_kaydi])
    etiketler = [e for e in (taslak.get("etiketler") or []) if (e or "").strip()]
    if etiketler:
        haber.etiketler.set(etiketleri_kur(etiketler))
        notlar.append("Etiketler: %s." % ", ".join(etiketler))

    # Gerekçeler pakete de yazılıyor: taslak ekranı sayfa yenilendiğinde de
    # "kategori neden bu" sorusunu yanıtlayabilmeli, oturuma bağlı olmamalı.
    paket["panel_notlari"] = notlar
    paket_kaydet(paket, haber.pk)
    return haber, notlar


def taslak_al(adres: str, kullanici, saglayici: str = "kural"):
    """Adres → taslak `Haber`. Panelin ve yönetim komutunun ortak girişi."""
    paket = paket_uret(adres, saglayici)
    haber, notlar = taslak_yaz(paket, kullanici)
    return haber, paket, notlar


# ---------------------------------------------------------------------------
# Görsel — ayrı ve açık karar
# ---------------------------------------------------------------------------

EN_BUYUK_GORSEL = 8 * 1024 * 1024
UZANTI = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp",
          "image/avif": ".avif", "image/gif": ".gif"}
TARAYICI = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/128.0 Safari/537.36")


def gorsel_indir(haber: Haber):
    """Kaynağın fotoğrafını arşive indirir ve habere bağlar.

    Taslak açılırken **çağrılmaz**. Fotoğrafın hak durumu haber haber
    değerlendirilir; indirme editörün ayrı bir kararıdır ve panelde ayrı bir
    düğmedir. Döner: (başarılı_mı, mesaj).
    """
    import urllib.error
    import urllib.request

    url = (haber.gorsel_url or "").strip()
    if not url.lower().startswith(("http://", "https://")):
        return False, "Bu haberde indirilecek bir görsel adresi yok."

    istek = urllib.request.Request(url, headers={
        "User-Agent": TARAYICI,
        "Accept": "image/avif,image/webp,image/png,image/jpeg,*/*;q=0.8",
        "Referer": url,
    })
    try:
        with urllib.request.urlopen(istek, timeout=30) as yanit:
            tur = (yanit.headers.get("Content-Type") or "").split(";")[0].strip().lower()
            if not tur.startswith("image/"):
                return False, "Adres görsel döndürmedi (%s)." % (tur or "tür yok")
            veri = yanit.read(EN_BUYUK_GORSEL + 1)
    except (urllib.error.URLError, OSError, ValueError) as e:
        return False, "Görsel indirilemedi: %s" % e
    if not veri:
        return False, "Görsel boş geldi."
    if len(veri) > EN_BUYUK_GORSEL:
        return False, "Görsel 8 MB sınırını aştı."

    uzanti = UZANTI.get(tur) or Path(url.split("?")[0]).suffix.lower() or ".jpg"
    ay = (haber.yayin_zamani or timezone.now()).strftime("%Y-%m")
    klasor = Path(settings.ARSIV_GORSEL_KOK) / ay
    klasor.mkdir(parents=True, exist_ok=True)
    ad = "yz-%d%s" % (haber.pk, uzanti)
    (klasor / ad).write_bytes(veri)

    haber.gorsel_dosya = "gorseller/%s/%s" % (ay, ad)
    haber.gorsel_var = True
    haber.save(update_fields=["gorsel_dosya", "gorsel_var"])
    return True, "Görsel indirildi: %s (%d KB)." % (haber.gorsel_dosya,
                                                    len(veri) // 1024)
