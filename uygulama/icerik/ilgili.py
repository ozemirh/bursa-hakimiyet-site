# -*- coding: utf-8 -*-
"""İlgili haberler — başlık benzerliğiyle (5 Eylül 2026, kullanıcı isteği).

Eskiden "aynı kategoriden en yeni 5 haber" idi; okur Bozbey davasını
okurken yanında Bursaspor transferi görüyordu. Şimdi haberin başlığındaki
**varlık kökleri** (büyük harfli kişi/kurum/yer adları, `konu_motoru`
ile aynı ayrıştırma) yakın tarihli başlıklarda aranır ve ortak köke göre
puanlanır. Yeterli aday çıkmazsa liste eski kuralla (aynı kategori, en
yeni) tamamlanır — kutu hiç boş kalmaz.

Arşivde tam metin indeksi yok (URUN-PLANI.md F7 bekliyor); `LIKE` 1
milyon satırda saniyeler sürer. Bu yüzden arama **±PENCERE_GUN** ile
kısılır: yayın zamanı indeksli. Ölçüm 5 Eylül 2026: ±180 günlük dilim
2021'de 165.667 satır ve terim başına 410 ms (dört terimle 4,6 s);
±60 günde dilim üçte bire, süre onda bire iner. İlgili haber zaten yakın
tarihlidir; üç yıl önceki aynı adlı haber "ilgili" değil, arşivdir.
Sonuç kimlik listesi olarak 6 saat önbelleklenir; arşiv sayfasında
ilgili liste her okurda yeniden hesaplanmaz. 19 Ekim 2026'dan beri bu
önbellek süreçler arasında paylaşılıyor (`settings.py` başarım bloğu);
eskiden her işçi sürecin kendi LocMem kopyası vardı.

Araştırma notu (kullanıcı isteğiyle, 5 Eylül 2026): yayıncıların yaygın
yöntemi varlık ağırlıklı TF-IDF benzerliği + yakın tarih + çeşitlilik.
Burası aynı düzenin indekssiz hâli: varlık kökü ağır, yer adı hafif,
beraberlikte tarih yakınlığı. Gerçek TF-IDF/FTS indeksi F7 kalemidir.
"""

from __future__ import annotations

from datetime import timedelta

from django.core.cache import cache
from django.db.models import Q

from . import konu_motoru as km
from .models import Haber

PENCERE_GUN = 60
EN_COK_ADAY = 400
EN_COK_CAPA = 3
ONBELLEK_SN = 6 * 3600


def _capalar(baslik: str) -> list[str]:
    """Başlıktan aranacak kökler: ikili adlar önce, sonra cümle ortasındaki
    büyük harfli kelimeler, en sonda cümle başındakiler ("Kandıra'da …",
    "Lucescu, …" — başlıkta ad çoğu zaman en baştadır). Yer adı kendi
    grubunun sonuna."""
    parcalar = km.parcala(baslik)
    ikili = [k for k, _ in km.ikililer(parcalar)]
    tekler = [p.kok for p in parcalar if p.buyuk and len(p.kok) >= 4]
    tekler.sort(key=lambda k: k in km.YERLER)
    tekler.sort(key=lambda k: not any(p.kok == k and p.orta for p in parcalar))
    # İkilinin parçalarını ayrıca arama: LIKE zaten parçayı da yakalar.
    kapli = {parca for k in ikili for parca in k.split("_")}
    return [k.split("_")[-1] for k in ikili] + [k for k in tekler if k not in kapli]


def _puan(a: set[str], b: set[str]) -> float:
    ortak = a & b
    puan = 0.0
    for k in ortak:
        if "_" in k:
            puan += 3
        elif k in km.YERLER:
            puan += 0.5
        else:
            puan += 1
    return puan


def bul(haber: Haber, adet: int = 6, haric=()) -> list[Haber]:
    """`haber`e başlıkça en yakın `adet` yayındaki haber; `haric` kimlikleri
    (ör. konu akışında zaten görünenler) atlanır."""
    haric = set(haric) | {haber.pk}
    anahtar = f"ilgili:{haber.pk}:{adet}:{','.join(map(str, sorted(haric)))}"
    secilen = cache.get(anahtar)
    if secilen is not None:
        return _nesneler(secilen)
    capalar = _capalar(haber.baslik)[:EN_COK_CAPA]
    secilen = []

    if capalar and haber.yayin_zamani:
        bas = haber.yayin_zamani - timedelta(days=PENCERE_GUN)
        son = haber.yayin_zamani + timedelta(days=PENCERE_GUN)
        suzgec = Q()
        for k in capalar:
            suzgec |= Q(baslik__icontains=k)
        adaylar = (Haber.yayindakiler()
                   .filter(yayin_zamani__range=(bas, son))
                   .filter(suzgec)
                   .exclude(pk__in=haric)
                   .values_list("id", "baslik", "yayin_zamani")[:EN_COK_ADAY])
        kendi = set(_kokler(haber.baslik))
        capa_kumesi = set(capalar) | {k for k in kendi if "_" in k}
        puanli = []
        for kimlik, baslik, zaman in adaylar:
            onun = set(_kokler(baslik))
            # "plaj" gibi sıradan bir ortak kelime yetmez; ad ortak olmalı.
            if not (onun & capa_kumesi):
                continue
            puan = _puan(kendi, onun)
            if puan >= 1:
                uzaklik = abs((zaman - haber.yayin_zamani).days)
                puanli.append((-puan, uzaklik, kimlik))
        puanli.sort()
        secilen = [k for _, _, k in puanli[:adet]]

    sonuc = _nesneler(secilen)
    if len(sonuc) < adet:
        # Dolgu: aynı kategoriden, haberin KENDİ DÖNEMİNDEN geriye doğru.
        # Bugünkü haberde "en yeniler" demek; 2023'teki bir arşiv sayfasında
        # 2026'nın haberleri değil, o günlerin haberleri gelir.
        dolgu = (Haber.yayindakiler()
                 .select_related("kategori", "ilce")
                 .filter(kategori_id=haber.kategori_id)
                 .exclude(pk__in=haric | set(secilen)))
        if haber.yayin_zamani:
            dolgu = dolgu.filter(yayin_zamani__lte=haber.yayin_zamani)
        sonuc.extend(dolgu[:adet - len(sonuc)])
    cache.set(anahtar, [h.pk for h in sonuc], ONBELLEK_SN)
    return sonuc


def _kokler(baslik: str) -> list[str]:
    parcalar = km.parcala(baslik)
    return [p.kok for p in parcalar] + [k for k, _ in km.ikililer(parcalar)]


def _nesneler(kimlikler: list[int]) -> list[Haber]:
    """Önbellekteki kimliklerden kayıtlar — YALNIZ hâlâ yayında olanlar.

    Liste 6 saat önbellekte duruyor (19 Ekim 2026'dan beri süreçler
    arasında paylaşılan önbellekte); o arada yayından çekilen bir haber
    okura bağlantı olarak gösterilmemeli.
    """
    if not kimlikler:
        return []
    sira = {k: i for i, k in enumerate(kimlikler)}
    nesneler = (Haber.yayindakiler().filter(pk__in=kimlikler)
                .select_related("kategori", "ilce"))
    return sorted(nesneler, key=lambda h: sira[h.pk])
