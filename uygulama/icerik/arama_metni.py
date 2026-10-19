# -*- coding: utf-8 -*-
"""Arama metni normalizasyonu — **motordan bağımsız** çekirdek.

Bu modül veritabanı görmez, sorgu kurmaz, Django modeli tanımaz. Yalnız
metni alır ve aranabilir hâle getirir. Böyle olması bilinçli: 27 Ağustos
2026 ölçüm turunda arama motorunun SQLite FTS5 mi PostgreSQL mü olacağı
karara bağlanmadı, ama **normalizasyon kararı iki yolda da aynı**.
Motora özgü olan (sanal tablo, tetikleyici, `MATCH` / `to_tsquery`
sözdizimi) buraya girmez.

## Neden gerekli — ölçülmüş kusur

Bugünkü arama `__icontains` kullanıyor ve SQLite'ın `LIKE`'ı büyük/küçük
harf duyarsızlığını **yalnız ASCII için** yapıyor. 27 Ağustos 2026,
308.602 kayıt üzerinde ölçüldü:

    ışık   → 1.880 sonuç      IŞIK   → 0        Işık → 428
    çağrı  → 3.647 sonuç      ÇAĞRI  → 0        Çağrı → 249
    öğrenci→ 5.236 sonuç      ÖĞRENCİ→ 0
    bursa  → 39.752 sonuç     BURSA  → 40.817   (ASCII çalışıyor)

Yani **büyük harfle yazan Türk okur sıfır sonuç alıyor.**

## Üç kural, üçü de ölçümden çıktı

1. **Türkçe-doğru küçültme.** Python'un `.lower()`'ı i/I ve ı/İ çiftlerini
   bozar: `"İNEGÖL".lower()` yedi karakterlik `'i̇negöl'` (i + birleşen
   nokta) üretir, `"IŞIK".lower()` `'işik'` verir. Doğrusu
   `site_etiket._kucult` — tek kaynak odur, burada yeniden yazılmaz.

2. **ASCII katlama.** Okur çoğu zaman `ogrenci` yazıp `öğrenci` bulmak
   ister. ı/i ayrımı da aramada birleştirilir.

3. **Önek, ama kısa kelimede değil.** Türkçe eklemeli ve ekler **sona**
   gelir; bu yüzden önek araması fiilen kök bulma yerine geçer. Ölçüm:
   tam kelime eşlemesi ek almış biçimlerin %61-89'unu kaçırıyordu
   (`ışık` 688 → önekle 1.171; `öğrenci` 1.285 → 5.412). Ama önek her
   kelimeye uygulanamaz: `a*` sözlüğün yarısını açar (ölçüldü: p95
   235 ms → 504 ms). Eşik `ONEK_EN_AZ`.

**Alt dizi (`LIKE %x%`) bilerek seçilmedi.** Ölçüm: `ışık` alt dizi ile
6.458 kayıt buluyor ve bunların **%83'ü rastlantı** — `değişikliği`,
`bisiklet`, `bağışıklık`, `karışık`. Bu kusur bugünkü aramada da var.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

# Türkçe küçültmenin TEK kaynağı. Burada kopyası tutulmuyor: iki yerde iki
# kopya olsaydı biri düzeltilip diğeri unutulurdu.
from .templatetags.site_etiket import _kucult

# Türkçe'ye özgü harfleri ASCII karşılığına katlar. Aramaya özeldir —
# gösterimde ASLA kullanılmaz, başlıklar kendi yazımıyla basılır.
_KATLAMA = str.maketrans({
    "ı": "i", "ş": "s", "ğ": "g", "ç": "c", "ö": "o", "ü": "u", "â": "a",
    "î": "i", "û": "u",
})

# Önek araması bu uzunluktan kısa kelimeye uygulanmaz (ölçüm: p95 504 → 235 ms).
ONEK_EN_AZ = 3

_VERI = Path(__file__).resolve().parent / "veri" / "turkce_durak.json"
_KELIME_AYIRICI = re.compile(r"[^\w]+", re.UNICODE)

# Slug'da yalnız ASCII harf/rakam kalır; gerisi tek tireye iner.
_SLUG_AYIRICI = re.compile(r"[^a-z0-9]+")


def anahtar(metin: str | None) -> str:
    """Metnin aranabilir hâli: Türkçe-doğru küçük harf + ASCII katlama.

    >>> anahtar("IŞIK") == anahtar("Işık") == anahtar("ışık") == "isik"
    True
    """
    return _kucult(metin or "").translate(_KATLAMA)


def slugla(metin: str | None, uzunluk: int = 220) -> str:
    """Adres parçası: Türkçe-doğru küçültme + ASCII katlama + tireleme.

    **Django'nun `slugify`'ı bu iş için yanlış — iki noktada.** NFKD
    ayrıştırması ü/ö/ç/ş/ğ'yi doğru katlıyor, ama (5 Eylül 2026'da ölçüldü):

        girdi                          slugify              slugla
        Nilüfer Çayı için büyük adım   nilufer-cay-icin-    nilufer-cayi-icin-
                                       buyuk-adm            buyuk-adim
        Bursa'da ışık ve İnegöl        bursada-sk-ve-inegol bursa-da-isik-ve-inegol
        Kurban Bayramı'nda … açık      kurban-bayramnda-…-  kurban-bayrami-nda-…-
                                       ack                  acik

    1. **Noktasız `ı` düşüyor.** NFKD karşılığı yok, `encode("ascii","ignore")`
       harfi tamamen atıyor: "adım" → `adm`, "ışık" → `sk`.
    2. **Kesme işareti tire olmuyor**, siliniyor: `bursada` — arşiv ise
       `bursa-da` diyor.

    Arşivdeki 1.038.474 adres eski sistemin katlamasıyla üretilmiş ve ikisini
    de doğru yapıyor (`kurban-bayrami-nda-bursa-da-hangi-eczaneler-acik`),
    yani panelden girilen yeni haber arşivdeki desene uymuyordu.

    Katlama burada, aramayla aynı kaynaktan (`anahtar`) geliyor: iki ayrı
    tablo tutulsaydı biri düzeltilip diğeri unutulurdu. Modülün "katlama
    yalnız aramada, gösterimde asla" kuralı bozulmuyor — slug gösterim
    değil, **adres**tir; başlık sayfada kendi yazımıyla basılmaya devam eder.
    """
    ham = _SLUG_AYIRICI.sub("-", anahtar(metin)).strip("-")
    return ham[:uzunluk].strip("-")


def kelimeler(metin: str | None) -> list[str]:
    """Normalize edilmiş kelime listesi. Noktalama ve boşluk ayırıcıdır."""
    return [k for k in _KELIME_AYIRICI.split(anahtar(metin)) if k]


def kayit_metni(*parcalar: str | None) -> str:
    """Saklanacak aranabilir metin: kelimeler tek boşlukla, iki uçta boşluk.

    >>> kayit_metni("Bursa'da IŞIK", None, "Gölge")
    ' bursa da isik golge '

    Biçim bir **sözleşmedir**, iki motor da ona dayanır:

    - Kelime sınırı her zaman tek boşluk olduğu için "kelimeyle başlayan"
      koşulu `" isik"` alt dizisi, "tam kelime" koşulu `" a "` alt dizisi
      olarak yazılabilir — motorun kelime bölücüsüne güvenmeye gerek kalmaz.
    - Kelime bölme burada, `kelimeler()` ile yapılır; motor metni yeniden
      bölmez. Sorgu tarafı da aynı işlevden geçtiği için saklanan kelime ile
      aranan kelime her zaman aynı kuralla üretilmiş olur.

    Kelime yoksa boş dize döner (iki boşluk değil): boş metin boş kalır.
    """
    hepsi = [k for p in parcalar for k in kelimeler(p)]
    return f" {' '.join(hepsi)} " if hepsi else ""


def _duraklar() -> frozenset[str]:
    """Durak listesi dosyadan okunur ve **normalize edilerek** saklanır.

    Dosya doğal yazımıyla duruyor ki elle düzenlenebilsin; karşılaştırma
    normalize hâl üzerinden yapılır ("çünkü" → "cunku").
    """
    global _DURAK_BELLEK
    if _DURAK_BELLEK is None:
        try:
            with open(_VERI, encoding="utf-8") as f:
                ham = json.load(f).get("kelimeler") or []
        except (OSError, json.JSONDecodeError):
            # Liste okunamazsa arama ÇALIŞMAYA DEVAM ETMELİ; durak süzme
            # bir iyileştirmedir, doğruluk şartı değil.
            ham = []
        _DURAK_BELLEK = frozenset(anahtar(k) for k in ham if k)
    return _DURAK_BELLEK


_DURAK_BELLEK: frozenset[str] | None = None


def durak_mi(kelime: str) -> bool:
    """Kelime içerik taşımayan bir işlev kelimesi mi (normalize hâliyle)."""
    return anahtar(kelime) in _duraklar()


@dataclass(frozen=True)
class Terim:
    """Aranacak tek kelime. `onek` doğruysa sonuna joker gelir.

    Motor tanımaz: FTS5 bunu `"kelime"*`, PostgreSQL `kelime:*` diye
    yazar. Bu sınıf hangisi olduğunu bilmez.
    """

    kelime: str
    onek: bool


@dataclass(frozen=True)
class Cozum:
    """Sorgunun çözümlenmiş hâli.

    `terimler` boşsa arama yapılmamalı; `sebep` okura ne söyleneceğini
    belirler. "Sonuç bulunamadı" demek yanlış olurdu — sorgu hiç
    çalıştırılmadı.
    """

    terimler: tuple[Terim, ...]
    dusen_durak: tuple[str, ...]
    sebep: str = ""

    def __bool__(self) -> bool:
        return bool(self.terimler)


def sorgu_coz(sorgu: str | None) -> Cozum:
    """Ham sorguyu terimlere çevirir; durak ve kısa kelime kurallarını uygular.

    Durak kelimeler düşürülür — ama sorgunun **tamamı** duraksa düşürülmez:
    "ve" arayan okura boş sayfa yerine "daha belirgin bir kelime yazın"
    demek doğru, ama hiçbir şey aramamak da yanlış olurdu; bu yüzden sebep
    döner ve karar çağırana bırakılır.
    """
    hepsi = kelimeler(sorgu)
    if not hepsi:
        return Cozum((), (), "bos")

    duraksiz = [k for k in hepsi if k not in _duraklar()]
    dusen = tuple(k for k in hepsi if k in _duraklar())

    if not duraksiz:
        # Tamamı durak: aranacak bir şey yok.
        return Cozum((), dusen, "hepsi_durak")

    terimler = tuple(Terim(k, len(k) >= ONEK_EN_AZ) for k in duraksiz)
    return Cozum(terimler, dusen)
