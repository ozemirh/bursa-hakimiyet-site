"""XML 1.0'da geçersiz karakterlerin temizliği — 19 Ekim 2026, Paket F madde 7.

Ölçüldü: tek bir haberin spotundaki `\\x1d` (grup ayırıcı — kelime
işlemcisinden yapıştırılan metinle geliyor) `/rss`i **500**'e düşürüyordu.
Django'nun XML yazıcısı denetim karakterini görünce bilerek hata fırlatır
("Control characters are not supported in XML 1.0"). Sitemap tarafı kendi
metnini yazdığı için hata vermez ama aynı karakterle **geçersiz XML** üretir
ve arama motoru tüm dosyayı atar.

XML 1.0'ın izin verdiği küme: `#x9 | #xA | #xD | [#x20-#xD7FF] |
[#xE000-#xFFFD] | [#x10000-#x10FFFF]`. Dışında kalanlar (C0 denetim
karakterleri, eşlenmemiş vekil kodlar, U+FFFE/U+FFFF) silinir; metnin geri
kalanı değişmez. Veritabanındaki kayda dokunulmaz — temizlik çıktıda.
"""

from __future__ import annotations

import re

_GECERSIZ = re.compile("[\x00-\x08\x0b\x0c\x0e-\x1f\ud800-\udfff￾￿]")


def xml_temizle(metin):
    """XML 1.0'da yazılamayan karakterleri atar. Metin değilse olduğu gibi döner."""
    if not isinstance(metin, str) or not metin:
        return metin
    return _GECERSIZ.sub("", metin)
