# -*- coding: utf-8 -*-
"""Konu dosyası okuma yardımcıları — site tarafı.

Yazma yok: dosyalar `konu_tara` komutu ve panelden gelir. Burada yalnız
"bu haber hangi onaylı dosyada" ve "dosyanın akışı" soruları yanıtlanır.
Sitede **yalnız onaylı** dosya görünür; süzgeç tek yerde, `Konu.yayindakiler`.
"""

from __future__ import annotations

from .models import Haber, Konu, KonuHaber

# Haber sayfasındaki akış penceresi: okunan haberle birlikte EN ÇOK 5
# satır (5 Eylül 2026, kullanıcı: "konu takibinde 5 haberi geçme").
# Dosyanın başında/sonunda pencere öbür yöne kayar, satır sayısı sabit kalır.
EN_COK_SATIR = 5


def uyeler(konu: Konu):
    """Dosyanın yayındaki haberleri, tarih sırasında."""
    return [b.haber for b in (
        konu.baglar
        .filter(haber__durum=Haber.DURUM_AKTIF, haber__yayin_zamani__isnull=False)
        .select_related("haber", "haber__kategori", "haber__ilce")
        .prefetch_related("haber__kategori__turler")
        .order_by("tarih", "haber_id"))]


def akis(haber: Haber) -> dict | None:
    """Haberin bağlı olduğu onaylı dosya ve etrafındaki akış.

    Haber birden çok dosyadaysa en kalabalık olan gösterilir; ikinci dosya
    konu sayfasından bulunur. Dönen sözlük: `konu`, `oncekiler`,
    `sonrakiler`, `gizli_once`, `gizli_sonra` (pencere dışında kalan sayı).
    Öncekiler + okunan + sonrakiler en çok `EN_COK_SATIR` satırdır.
    """
    bag = (KonuHaber.objects
           .filter(haber=haber, konu__onay=Konu.ONAY_ONAYLI)
           .select_related("konu")
           .order_by("-konu__haber_sayisi", "konu_id")
           .first())
    if bag is None:
        return None
    konu = bag.konu
    hepsi = uyeler(konu)
    try:
        i = next(n for n, h in enumerate(hepsi) if h.pk == haber.pk)
    except StopIteration:
        return None
    pay = EN_COK_SATIR - 1
    once = min(i, pay // 2)
    sonra = min(len(hepsi) - i - 1, pay - once)
    once = min(i, pay - sonra)          # sonda kalan yer öne verilir
    oncekiler = hepsi[i - once:i]
    sonrakiler = hepsi[i + 1:i + 1 + sonra]
    return {
        "konu": konu,
        "oncekiler": oncekiler,
        "sonrakiler": sonrakiler,
        "gizli_once": i - len(oncekiler),
        "gizli_sonra": len(hepsi) - (i + 1) - len(sonrakiler),
        "toplam": len(hepsi),
    }
