# -*- coding: utf-8 -*-
"""Yapay zekâ taslağının köken kaydı ve K2 bulguları — 19 Ekim 2026, Paket M.

İki iş:

1. **Köken.** Taslak açılırken hangi sağlayıcı/model ve hangi denetim
   sonucuyla üretildiği (`YzKoken`) yazılır; yayına alınırken editörün metni
   ne kadar değiştirdiği (`benzerlik`, kelime düzeyinde `difflib`) eklenir.
   DEGERLENDIRME-2026-10 §4: bir model taslağı 0,999 benzerlikle yayımlanmış,
   bunu gösteren kalıcı kayıt yoktu. Okura etiket basılmaz (kullanıcı kararı
   bekliyor); kayıt yalnız panel ve denetim içindir.
2. **K2 kapısı.** `arac/denetim.py` taslakta kaynakta geçmeyen sayı, tarih,
   yüzde ve özel adları bulur; her biri bir `YzBulgu` olur. Açık bulgu varken
   haber yayına alınamaz (`yayin_kapisi`) ve taslak "İncelemede" doğar. Editör
   her bulguyu kaynağa bakıp tek tek kapatır; toplu kapatma yok.

Veritabanı işi burada; denetimin kendisi araçta (`yz_kopru.denetim_sonucu`).
"""

from __future__ import annotations

import html
import re
from difflib import SequenceMatcher

from django.db import transaction
from django.utils import timezone

from .models import Haber, YzBulgu, YzKoken

_ETIKET = re.compile(r"<[^>]+>")
_KELIME = re.compile(r"\w+", re.UNICODE)


def duz_metin(baslik: str, spot: str, govde_html: str) -> str:
    """Başlık + spot + gövde, etiketsiz düz metin. Karşılaştırmanın iki ucu
    da bu işlevden geçer."""
    govde = html.unescape(_ETIKET.sub(" ", govde_html or ""))
    return "\n".join(p.strip() for p in (baslik or "", spot or "", govde) if p and p.strip())


def benzerlik(once: str, sonra: str) -> float:
    """Kelime düzeyinde benzerlik (0-1). Harf düzeyi uzun metinde yavaş ve bir
    noktalama değişikliğini de "değişim" sayar; kelime düzeyi editörün
    yazdığını ölçer."""
    a = [k.lower() for k in _KELIME.findall(once or "")]
    b = [k.lower() for k in _KELIME.findall(sonra or "")]
    if not a and not b:
        return 1.0
    return round(SequenceMatcher(None, a, b, autojunk=False).ratio(), 4)


@transaction.atomic
def kaydet(haber: Haber, paket: dict, denetim: dict, kullanici=None,
           uretilen_metin: str = "") -> YzKoken:
    """Taslak açılırken köken ve K2 bulgularını yazar."""
    uretim = paket.get("uretim") or {}
    kaynak = paket.get("kaynak") or {}
    koken = YzKoken.objects.create(
        haber=haber,
        saglayici=(uretim.get("saglayici") or "")[:12],
        model=(uretim.get("model") or "")[:80],
        kaynak_adres=(kaynak.get("kaynak_url") or "")[:600],
        denetim=denetim,
        uretilen_metin=uretilen_metin,
        olusturan=kullanici if getattr(kullanici, "pk", None) else None,
    )
    YzBulgu.objects.bulk_create([
        YzBulgu(koken=koken, kural=b.get("kural", "K2")[:4], tur=b["tur"][:8],
                deger=str(b.get("deger", ""))[:200], alan=str(b.get("alan", ""))[:40],
                baglam=str(b.get("baglam", ""))[:300])
        for b in denetim.get("k2") or []])
    return koken


def acik_k2_sayisi(haber_id) -> int:
    """Haberin kapatılmamış K2 bulgusu. Kaydedilmemiş haberde 0."""
    if not haber_id:
        return 0
    return YzBulgu.objects.filter(koken__haber_id=haber_id, kural="K2",
                                  kapandi=False).count()


def acik_k2_haberleri(haber_idleri) -> set[int]:
    """Toplu fiil için: verilen kimliklerden açık K2 bulgusu olanlar, tek sorgu."""
    return set(YzBulgu.objects.filter(koken__haber_id__in=list(haber_idleri), kural="K2",
                                      kapandi=False)
               .values_list("koken__haber_id", flat=True).distinct())


def acik_k2_tumu() -> set[int]:
    """Açık K2 bulgusu olan bütün haberler. Küme küçüktür (yalnız araçtan
    gelen taslaklar); toplu fiil binlerce satırda tek sorgu açsın diye."""
    return set(YzBulgu.objects.filter(kural="K2", kapandi=False)
               .values_list("koken__haber_id", flat=True).distinct())


def bulgu_kapat(bulgu: YzBulgu, kullanici) -> bool:
    """Editör "kontrol ettim" dedi. Zaten kapalıysa değişmez, False döner."""
    if bulgu.kapandi:
        return False
    bulgu.kapandi = True
    bulgu.kapatan = kullanici
    bulgu.kapanma = timezone.now()
    bulgu.save(update_fields=["kapandi", "kapatan", "kapanma"])
    return True


def yayina_alindi(haber_idleri, kullanici=None) -> int:
    """Yayına alınan haberlerin köken kaydına ilk yayın anını ve editörün
    değiştirdiği oranı yazar. Köken kaydı olmayan (araçtan gelmeyen) haber
    ve daha önce yayına alınmış kayıt atlanır. Döner: yazılan kayıt sayısı."""
    yazilan = 0
    for koken in (YzKoken.objects.filter(haber_id__in=list(haber_idleri),
                                         yayin_zamani__isnull=True,
                                         haber__durum=Haber.DURUM_AKTIF)
                  .select_related("haber")):
        h = koken.haber
        koken.benzerlik = benzerlik(koken.uretilen_metin, duz_metin(h.baslik, h.spot, h.govde))
        koken.yayin_zamani = timezone.now()
        koken.yayinlayan = kullanici if getattr(kullanici, "pk", None) else None
        koken.save(update_fields=["benzerlik", "yayin_zamani", "yayinlayan"])
        yazilan += 1
    return yazilan
