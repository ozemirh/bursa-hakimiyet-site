"""Kural tabanli taslak motoru — model kullanmaz, yalnizca standart kutuphane.

Ayiklanmis bir kaynaktan `haber_taslak.py:taslak_uret()` ile ayni sekilde bir
paket uretir. Fark: dil uretimi YAPMAZ. Kategori, ilce, etiket, SEO iskeleti,
onem, hassas konu ve dogrulanacaklar gibi alanlari sozluk ve sezgiyle doldurur;
govdeyi editorun yazmasi icin bos iskelet olarak birakir ve kaynagin cumlelerini
"ham malzeme" olarak ayri bir tezgah listesinde verir.

Kopyalama yok: kaynagin cumleleri taslaga girmez, yalnizca tezgahta durur.
"""

from __future__ import annotations

import json
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

SOZLUK_YOLU = Path(__file__).resolve().parent / "sozluk.json"

_UNLULER = "aeıioöuü"
_KUCUK_ESLEME = str.maketrans("İIÇĞÖŞÜ", "iıçğöşü")


def sozluk_yukle(yol: Path = SOZLUK_YOLU) -> dict:
    """Sozluk tablolarini okur."""
    return json.loads(yol.read_text(encoding="utf-8"))


# ---------------------------------------------------------------- metin araclari

def kucuk(metin: str) -> str:
    """Turkce farkindalikli kucuk harf. Python'un lower()'i I ve İ'yi bozar."""
    return metin.translate(_KUCUK_ESLEME).lower()


_TR_HARF = set("çğıöşüÇĞİÖŞÜ")


def etiket_kucuk(kelime: str) -> str:
    """Etiket icin kucuk harf. Turkce harf tasimayan yabanci adlarda ASCII
    kurali uygulanir; "Icardi" -> "icardi", "İnegöl" -> "inegöl"."""
    return kucuk(kelime) if _TR_HARF & set(kelime) else kelime.lower()


def sadelestir(metin: str) -> str:
    """Noktalama yerine bosluk koyar, kucuk harfe cevirir."""
    return re.sub(r"[^\wçğıöşüÇĞİÖŞÜ]+", " ", kucuk(metin)).strip()


def kokle(kelime: str, ekler: list[str], tur: int = 2) -> str:
    """Basit son ek dusurme. Dilbilimsel kok bulucu degil; iki tarafa da ayni
    islem uygulandigi icin eslestirmeyi ayakta tutar.

    "barajin" -> "baraj", "golcunun" -> "golcu" -> "golc"
    """
    k = kucuk(kelime)
    for _ in range(tur):
        for ek in ekler:
            if k.endswith(ek) and len(k) - len(ek) >= 3:
                k = k[: -len(ek)]
                break
        else:
            break
    return k


def gecer(anahtar: str, duz: str) -> bool:
    """Anahtarin sadelestirilmis metinde gecip gecmedigi.

    Duz alt dize aramasi yanilticidir: "kaza" kelimesi "kazandırılıyor" icinde
    de bulunur. Tek kelimelik anahtarlarda kelime sinirina bakilir, en fazla uc
    harflik cekim ekine izin verilir ("kazası", "gözaltına", "şüphelinin").
    """
    a = kucuk(anahtar)
    if " " in a:
        return a in duz
    for kelime in duz.split():
        if kelime == a or (kelime.startswith(a) and len(kelime) - len(a) <= 3):
            return True
    return False


def cumlele(metin: str) -> list[str]:
    """Govdeyi cumlelere ayirir. Kisaltmalarda bolmemeye calisir."""
    if not metin:
        return []
    ham = re.split(r"(?<=[.!?])\s+(?=[A-ZÇĞİÖŞÜ0-9])", metin.strip())
    return [c.strip() for c in ham if len(c.strip()) > 25]


def ek_ekle(isim: str) -> str:
    """Ozel ismin sonuna kesme isaretiyle tamlayan eki getirir.

    "Sozcu" -> "Sozcu'nun", "Bursa" -> "Bursa'nin", "Soylem" -> "Soylem'in"
    """
    if not isim:
        return ""
    temiz = isim.strip().rstrip(".")
    son = kucuk(temiz[-1])
    son_unlu = next((h for h in reversed(kucuk(temiz)) if h in _UNLULER), "e")
    ek = {"a": "ın", "ı": "ın", "e": "in", "i": "in",
          "o": "un", "u": "un", "ö": "ün", "ü": "ün"}[son_unlu]
    if son in _UNLULER:
        ek = "n" + ek
    return f"{temiz}'{ek}"


_CUMLE_BASI = re.compile(r"(?:^|[.!?:]\s+|\n)\s*$")


def ozel_isimler(metin: str, en_uzun_obek: int = 3) -> list[str]:
    """Cumle ortasinda buyuk harfle baslayan kelime obeklerini toplar.

    Obek uzunlugu sinirlanir; "Büyükşehir Belediyesi Başkan Vekili Şahin Biba"
    gibi unvan zincirleri tek bir etikete donusmesin diye bastan kirpilir.
    """
    if not metin:
        return []
    bulunan: list[str] = []
    for esle in re.finditer(r"[A-ZÇĞİÖŞÜ][\wçğıöşüÇĞİÖŞÜ]*(?:['’][\wçğıöşü]+)?"
                            r"(?:\s+[A-ZÇĞİÖŞÜ][\wçğıöşüÇĞİÖŞÜ]*(?:['’][\wçğıöşü]+)?)*", metin):
        parcalar = esle.group().split()
        oncesi = metin[max(0, esle.start() - 3):esle.start()]
        if _CUMLE_BASI.search(oncesi) or esle.start() == 0:
            parcalar = parcalar[1:]  # cumle basi buyuk harfi kanit degil
        if not parcalar:
            continue
        if len(parcalar) > en_uzun_obek:
            parcalar = parcalar[-en_uzun_obek:]  # unvan zinciri onde, isim sonda
        obek = re.sub(r"['’][\wçğıöşü]+$", "", " ".join(parcalar).strip())
        if len(obek) >= 3 or (obek.isupper() and len(obek) >= 2):
            bulunan.append(obek)
    gorulen: dict[str, str] = {}
    for o in bulunan:
        gorulen.setdefault(kucuk(o), o)
    return list(gorulen.values())


def yayin_adi(kaynak: dict) -> str:
    """Kaynak yayinin atifta kullanilacak adi. Alan adiysa uzantisini atar.

    Ad hic yoksa bos doner — atif uydurulmaz, editore doldurtulur.
    """
    ad = (kaynak.get("kaynak_adi") or "").strip()
    if not ad or ("." in ad and " " not in ad):
        ham = ad or (kaynak.get("kaynak_alan") or "")
        if not ham:
            return ""
        kok = ham.split(".")[0]
        ad = kok[:1].upper() + kok[1:]
    return ad


def slugla(metin: str, uzunluk: int = 60) -> str:
    """Turkce basligi dosya adina uygun sade bir slug'a cevirir."""
    esle = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")
    d = metin.translate(esle)
    d = unicodedata.normalize("NFKD", d).encode("ascii", "ignore").decode()
    d = re.sub(r"[^a-zA-Z0-9]+", "-", d).strip("-").lower()
    return (d[:uzunluk].rstrip("-") or "taslak")


ATIF_YER_TUTUCU = "[kaynak yayının adı]'nın haberine göre"


def atif_kur(kaynak: dict) -> str:
    ad = yayin_adi(kaynak)
    return f"{ek_ekle(ad)} haberine göre" if ad else ATIF_YER_TUTUCU


# ---------------------------------------------------------------- alan doldurma

def _metin_havuzu(kaynak: dict) -> tuple[str, str, str]:
    return (
        kaynak.get("orijinal_baslik") or "",
        kaynak.get("orijinal_spot") or "",
        kaynak.get("orijinal_govde") or "",
    )


def kategori_bul(kaynak: dict, s: dict) -> tuple[str, dict[str, float]]:
    """Agirlikli anahtar puani: baslik x3, spot x2, govde x1."""
    baslik, spot, govde = _metin_havuzu(kaynak)
    ekler = s["ek_listesi"]
    puanlar: dict[str, float] = {}

    for metin, agirlik in ((baslik, 3), (spot, 2), (govde, 1)):
        duz = sadelestir(metin)
        if not duz:
            continue
        koklu = {kokle(k, ekler) for k in duz.split()}
        for kategori, anahtarlar in s["kategori_anahtarlari"].items():
            for anahtar, katsayi in anahtarlar.items():
                if " " in anahtar:
                    if anahtar in duz:
                        puanlar[kategori] = puanlar.get(kategori, 0) + katsayi * agirlik
                elif anahtar in duz.split() or kokle(anahtar, ekler) in koklu:
                    puanlar[kategori] = puanlar.get(kategori, 0) + katsayi * agirlik

    if not puanlar:
        return "Gündem", {}
    en_iyi = max(puanlar.items(), key=lambda p: p[1])
    return en_iyi[0], puanlar


def ilce_bul(kaynak: dict, s: dict) -> tuple[str, bool, str]:
    """Ilce, Bursa ilgisi ve aciklamasini dondurur. Zorla yerellestirme yok."""
    baslik, spot, govde = _metin_havuzu(kaynak)
    duz = sadelestir(f"{baslik} {baslik} {spot} {govde}")

    bulunan: dict[str, int] = {}
    for ilce, ipuclari in s["ilce_ipuclari"].items():
        sayi = sum(duz.count(kucuk(ip)) for ip in ipuclari)
        if sayi:
            bulunan[ilce] = sayi

    bursa_var = any(kucuk(ip) in duz for ip in s["bursa_ipuclari"]) or bool(bulunan)

    if bulunan:
        ilce = max(bulunan.items(), key=lambda p: p[1])[0]
        return ilce, True, f"Haber {ilce} ile ilişkili; metinde {bulunan[ilce]} kez geçiyor."
    if bursa_var:
        return "Bursa geneli", True, "Bursa geçiyor ancak tek bir ilçeye bağlanmıyor."
    return "Bursa dışı", False, ("Metinde Bursa ya da ilçeleriyle bağ kuran bir ipucu yok. "
                                 "Haberi zorla yerelleştirmeyin; yerel bir açı bulunamıyorsa "
                                 "ajans/dış haber olarak girin.")


def etiket_bul(kaynak: dict, s: dict, en_fazla: int = 7) -> list[str]:
    """Durak kelimeler dusulmus frekans + ozel isimler."""
    baslik, spot, govde = _metin_havuzu(kaynak)
    ekler = s["ek_listesi"]
    durak = {kokle(d, ekler) for d in s["durak_kelimeler"]}

    sayac: dict[str, list] = {}
    for metin, agirlik in ((baslik, 3), (spot, 2), (govde, 1)):
        # Ham metinden okunur: buyuk/kucuk harf bilgisi etikette korunsun diye
        # (sadelestir "Icardi"yi "ıcardi" yapar, etiket olarak yanlis olur)
        for kelime in re.findall(r"[\wçğıöşüÇĞİÖŞÜ]+", metin):
            if len(kelime) < 4 or kelime.isdigit():
                continue
            kok = kokle(kelime, ekler)
            if kok in durak or len(kok) < 3:
                continue
            kayit = sayac.setdefault(kok, [0, kelime])
            kayit[0] += agirlik

    unvan_kok = {kokle(u, ekler) for u in s["unvanlar"]}
    siralanmis = sorted(sayac.items(), key=lambda p: -p[1][0])
    etiketler = [etiket_kucuk(v[1]) for k, v in siralanmis
                 if k not in unvan_kok][:en_fazla]

    for isim in ozel_isimler(f"{baslik}. {spot}", en_uzun_obek=2)[:3]:
        e = etiket_kucuk(isim)
        if e not in etiketler and len(e.split()) <= 2:
            etiketler.insert(0, e)

    # "biba" ile "şahin biba" birlikte durmasin; daha belirgin olani kalsin
    ayikli = [e for e in etiketler
              if not any(e != d and e in d.split() for d in etiketler)]
    return ayikli[:en_fazla]


def hassas_bul(kaynak: dict, s: dict) -> dict:
    baslik, spot, govde = _metin_havuzu(kaynak)
    duz = sadelestir(f"{baslik} {spot} {govde}")
    bulgular: list[tuple[str, int, str]] = []
    for tur, veri in s["hassas_anahtarlar"].items():
        # "çocuk parkı" gibi masum kaliplar once metinden dusulur, yoksa her
        # park haberi cocuk haberi gibi isaretlenir
        temiz = duz
        for kalip in veri.get("haric", []):
            temiz = temiz.replace(kucuk(kalip), " ")
        baglam = veri.get("baglam")
        if baglam and not any(gecer(b, temiz) for b in baglam):
            continue  # "çocuk" tek basina yeterli degil; risk baglami da aransin
        vurus = sum(1 for k in veri["kelimeler"] if gecer(k, temiz))
        if vurus:
            bulgular.append((tur, vurus, veri["uyari"]))
    if not bulgular:
        return {"var_mi": False, "turu": "", "uyari": ""}
    bulgular.sort(key=lambda b: -b[1])
    turler = ", ".join(b[0] for b in bulgular)
    return {"var_mi": True, "turu": bulgular[0][0],
            "uyari": bulgular[0][2] + (f" (Ayrıca işaretlenen başlıklar: {turler}.)"
                                       if len(bulgular) > 1 else "")}


_SAYI = re.compile(r"\b\d[\d.,]*\b")
_SAYI_BIRIM = re.compile(r"(\d[\d.,]*)((?:\s+[\wçğıöşüÇĞİÖŞÜ%]+){0,2})")
_TARIH = re.compile(r"\b\d{1,2}\s+(?:Ocak|Şubat|Mart|Nisan|Mayıs|Haziran|Temmuz|"
                    r"Ağustos|Eylül|Ekim|Kasım|Aralık)\s+\d{4}\b")


def dogrulanacaklar(kaynak: dict, s: dict, en_fazla: int = 8) -> list[str]:
    """Yayindan once teyit edilecek maddeler."""
    baslik, spot, govde = _metin_havuzu(kaynak)
    tam = f"{baslik}. {spot} {govde}"
    duz = sadelestir(tam)
    maddeler: list[str] = []

    # Sayidan sonraki birim kelimelerini oldugu gibi topla: "45 milyon TL",
    # yalnizca "45 milyon" degil. Ozgun metinde arandigi icin buyuk harf korunur.
    birim_kume = {kucuk(b) for b in s["birimler"] for b in b.split()}
    for esle in _SAYI_BIRIM.finditer(tam):
        parcalar = []
        for kelime in esle.group(2).split():
            if kucuk(kelime.strip(".,;:")) in birim_kume:
                parcalar.append(kelime.strip(".,;:"))
            else:
                break
        if parcalar:
            madde = (f"“{esle.group(1)} {' '.join(parcalar)}” rakamını "
                     "resmî kaynaktan teyit edin.")
            if madde not in maddeler:
                maddeler.append(madde)

    for tarih in _TARIH.findall(tam)[:2]:
        maddeler.append(f"“{tarih}” tarihini kaynak belgeyle karşılaştırın.")

    isimler = ozel_isimler(f"{baslik}. {spot}")[:3]
    for isim in isimler:
        maddeler.append(f"“{isim}” yazılışını ve varsa unvanını teyit edin.")

    for kalip in s["teyit_kaliplari"]:
        if kucuk(kalip) in duz:
            maddeler.append(
                f"Haberde “{kalip}” kalıbıyla verilen bilgi tek kaynağa dayanıyor; "
                "ikinci bir kaynaktan doğrulayın."
            )
            break

    if not yayin_adi(kaynak):
        maddeler.insert(0, "Kaynak yayının adı girilmedi — atıf cümlesindeki yer tutucuyu "
                           "gerçek yayın adıyla değiştirin.")
    if kaynak.get("gorsel_url"):
        maddeler.append("Kaynağın fotoğrafı yalnızca referanstır — hak durumu "
                        "doğrulanmadan yayına giremez.")
    if not kaynak.get("yayin_tarihi"):
        maddeler.append("Kaynak haberin yayın tarihi ayıklanamadı; sayfadan elle kontrol edin.")
    if kaynak.get("ayiklama_guveni") == "dusuk":
        maddeler.append("Ayıklama güveni düşük — kaynağı elle açıp gövdeyi karşılaştırın.")

    return maddeler[:en_fazla]


def tezgah_kur(kaynak: dict, s: dict, en_fazla: int = 12) -> list[dict]:
    """Kaynagin cumlelerini "ham malzeme" olarak puanlar. Bu liste TASLAGA
    GIRMEZ; yalnizca editorun yeniden yazarken bakacagi tezgah panelinde durur."""
    govde = kaynak.get("orijinal_govde") or ""
    cumleler = cumlele(govde)
    malzeme: list[dict] = []
    for i, c in enumerate(cumleler):
        sayi_var = bool(_SAYI.search(c))
        alinti_var = bool(re.search(r"[\"“”]|\bdedi\b|\bsöyledi\b|\baçıkladı\b|\bbelirtti\b", c))
        isim_sayisi = len(ozel_isimler(c))
        puan = min(100, 30 + isim_sayisi * 8 + (20 if sayi_var else 0)
                   + (10 if alinti_var else 0) + min(20, len(c) // 12))
        if i == 0:
            oneri = "giriş"
        elif sayi_var:
            oneri = "rakam"
        elif alinti_var:
            oneri = "alıntı adayı"
        else:
            oneri = "gelişme"
        malzeme.append({"metin": c, "puan": puan, "oneri": oneri})
    malzeme.sort(key=lambda m: -m["puan"])
    return malzeme[:en_fazla]


def _onem_bul(kategori: str, bursa_var: bool, kelime: int) -> str:
    if not bursa_var:
        return "normal"
    agir = {"Yargı", "Siyaset", "Çevre ve su", "Asayiş", "Ulaşım", "Sağlık"}
    if kategori in agir and kelime >= 120:
        return "one_cikan"
    return "normal"


# ---------------------------------------------------------------- genel arayuz

def taslak_uret_kural(kaynak: dict, sozluk: dict | None = None) -> dict:
    """Ayiklanmis kaynaktan kural tabanli paket uretir.

    Donen sekil `haber_taslak.py:taslak_uret()` ile ayni: {"taslak", "uretim"}.
    Ek olarak "tezgah" tasir.
    """
    s = sozluk or sozluk_yukle()

    kategori, _ = kategori_bul(kaynak, s)
    ilce, bursa_var, bursa_aciklama = ilce_bul(kaynak, s)
    kelime = int(kaynak.get("kelime_sayisi") or 0)
    atif = atif_kur(kaynak)

    taslak = {
        "baslik_secenekleri": [
            {"metin": "", "gerekce": "Düz haber başlığı: ne oldu, kim yaptı, nerede. "
                                     "En fazla 70 karakter."},
            {"metin": "", "gerekce": "Sonuç/etki odaklı: bu gelişme okur için ne değiştiriyor?"},
            {"metin": "", "gerekce": "Kısa ve vurucu: 6-7 kelime. Tıklama tuzağı yok."},
        ],
        "onerilen_baslik_indeksi": 0,
        "spot": "",
        "uc_madde": ["", "", ""],
        "govde": [
            {"tur": "paragraf", "metin": ""},
            {"tur": "paragraf", "metin": ""},
            {"tur": "ara_baslik", "metin": ""},
            {"tur": "paragraf", "metin": ""},
            {"tur": "paragraf", "metin": ""},
        ],
        "kategori": kategori,
        "ilce": ilce,
        "etiketler": etiket_bul(kaynak, s),
        "seo_baslik": "",
        "seo_aciklama": "",
        "url_slug": "",
        "gorsel_alt": "",
        "gorsel_altyazi": "",
        "okuma_suresi_dk": max(1, round(kelime / 200)) if kelime else 1,
        "onem": _onem_bul(kategori, bursa_var, kelime),
        "kaynak_atfi": atif,
        "dogrulanmasi_gerekenler": dogrulanacaklar(kaynak, s),
        "hassas_konu": hassas_bul(kaynak, s),
        "bursa_ilgisi": {"var_mi": bursa_var, "aciklama": bursa_aciklama},
        "editor_notu": (
            "Bu taslak kural tabanlı motorla hazırlandı — dil üretimi yapılmadı. "
            "Kategori, ilçe, etiketler, önem ve uyarılar sözlük ve sezgiyle dolduruldu; "
            "başlık, spot, üç madde ve gövde kasıtlı olarak boş bırakıldı. "
            "Ham malzeme panelinden yararlanarak haberi kendi cümlelerinizle yazın; "
            "kaynağın cümlelerini kopyalamayın. Kaynak, yayınlanan sayfada ayrı bir "
            "bölmede gösterilir; gövdeye atıf cümlesi koymak zorunda değilsiniz."
        ),
    }

    return {
        "taslak": taslak,
        "uretim": {
            "saglayici": "kural",
            "model": "",
            "surum": "1.0",
            "zaman": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        },
        "tezgah": tezgah_kur(kaynak, s),
    }
