"""JSON-LD'yi `<script>` içine güvenle basmak — 19 Ekim 2026, Paket F madde 6.

`nobetci_eczane.html` yapısal veriyi `{{ yapisal_veri|safe }}` ile basıyordu.
`json.dumps` `<` ve `/` karakterlerini kaçırmaz; eczane adında ya da
adresinde `</script><script>…` geçerse (veri dış kaynaktan, Eczacı
Odası'nın sayfasından kazınıyor) tarayıcı betik bloğunu orada kapatıp
ikinci betiği çalıştırıyordu — doğrulandı (DEGERLENDIRME-2026-10 §3 6e).

Django'nun `json_script` süzgeci aynı kaçışı yapar ama `type` niteliğini
`application/json` diye sabitler; arama motorları `application/ld+json`
ister. Bu yüzden kaçış burada, `json_script` ile aynı karakter kümesiyle
yapılır ve sonuç güvenli işaretlenir — şablonda `|safe` GEREKMEZ.

JSON içinde `\\u003C` ile `<` aynı değerdir; ayrıştırıcı farkı görmez.
"""

from __future__ import annotations

import json

from django.utils.safestring import SafeString, mark_safe

_KACIS = {
    ord("<"): "\\u003C",
    ord(">"): "\\u003E",
    ord("&"): "\\u0026",
    0x2028: "\\u2028",      # JS satır ayırıcıları: eski ayrıştırıcıları kırar
    0x2029: "\\u2029",
}


def betik_json(veri) -> SafeString:
    """`<script type="application/ld+json">` içine doğrudan basılabilir JSON."""
    return mark_safe(json.dumps(veri, ensure_ascii=False).translate(_KACIS))
