"""Bursaspor bölüm sayfasının özel bloğu — sezon fikstürü (12 Eylül 2026).

Kullanıcı isteği: *"bursaspor sayfası için daha özel bir şey istiyorum"*.
İlk turda yedi blok eklendi (form şeridi, konu kısayolları, gazetenin
dizileri, kadro, basketbol, künye, fikstür). Kullanıcı aynı gün karar
verdi: *"haftanın maçı, puan tablosu ve fikstür kalsın, geri kalanı
kaldır; ama bursaspor sayfasını da yeşil beyaz renklerine büründür"*.

Kalan tek türetim bu dosyada: `takip.fikstur` listesini (TFF, hafta
hafta, `canli-veri/puan_durumu.py`) sayfanın fikstür tablosuna hazırlar.
Haftanın maçı ve puan penceresi servis panelinde zaten vardı
(`views._bolum_servisi`), buraya dokunulmadı. Yeşil-beyaz sayfa kabuğu
`kategori.html`in `<body data-bolum="bursaspor">` niteliğiyle
`site.css`te uygulanır.

Kaldırılan bloklar (kadro, diziler, basketbol, künye, form şeridi)
kullanıcı kararıyla gitti; **yeniden önerme.**

Üç kural korunur: **veri yoksa blok yok**, **kaynakta olmayan alan
uydurulmaz** (skor yoksa "–", saat yoksa boş), **kural şablonda değil
burada**.
"""

from datetime import date, datetime

# Maç merkezindeki "son sonuçlar" ve "sıradaki maçlar" adedi (şablon şu an
# yalnız `sonraki`yi işaretliyor; sayılar veri sözleşmesinin parçası).
SON_MACLAR = 3
SIRADAKI_MACLAR = 3


def _tarih(mac: dict):
    try:
        return datetime.strptime(mac.get("tarih") or "", "%d.%m.%Y").date()
    except ValueError:
        return None


def _mac_duzelt(mac: dict, kulup_id) -> dict:
    """Maç satırına Bursaspor açısından türetilmiş alanları ekler.

    `sonuc` G/B/M harfi yalnız skor varsa; `rakip` karşı takımın adı;
    `bizim_ev` iç saha mı. Skor kaynaktaki yönüyle (ev–deplasman) kalır,
    çevrilmez — okur tabloda "Bodrum FK 0–2 Bursaspor" görür, gerçek bu.
    """
    k = dict(mac)
    bizim_ev = mac.get("ev_kulup_id") == kulup_id
    k["bizim_ev"] = bizim_ev
    k["rakip"] = mac.get("deplasman") if bizim_ev else mac.get("ev")
    k["tarih_g"] = _tarih(mac)
    ev, dep = mac.get("ev_gol"), mac.get("deplasman_gol")
    k["skor_var"] = bool(mac.get("oynandi") and ev is not None and dep is not None)
    if k["skor_var"]:
        bizim, rakip = (ev, dep) if bizim_ev else (dep, ev)
        k["sonuc"] = "G" if bizim > rakip else "M" if bizim < rakip else "B"
        k["sonuc_adi"] = {"G": "galibiyet", "B": "beraberlik",
                          "M": "mağlubiyet"}[k["sonuc"]]
    else:
        k["sonuc"] = ""
        k["sonuc_adi"] = ""
    return k


def fikstur_hazirla(puan: dict | None) -> dict | None:
    """`takip.fikstur` listesini tabloya hazırlar.

    Döner: `maclar` (sezonun tamamı, hafta sırasıyla), `sonraki` (ilk
    oynanmamış maç), `son_maclar`, `siradakiler`, `oynanan`/`toplam`.
    Fikstür yoksa None — şablon tabloyu hiç çizmez.
    """
    takip = (puan or {}).get("takip") or {}
    ham = takip.get("fikstur") or []
    if not ham:
        return None
    kulup_id = takip.get("kulup_id")
    maclar = sorted((_mac_duzelt(m, kulup_id) for m in ham),
                    key=lambda m: (m.get("hafta") or 0, m["tarih_g"] or date.max))
    oynananlar = [m for m in maclar if m["skor_var"]]
    oynanmayanlar = [m for m in maclar if not m["skor_var"]]
    return {
        "maclar": maclar,
        "sonraki": oynanmayanlar[0] if oynanmayanlar else None,
        "siradakiler": oynanmayanlar[:SIRADAKI_MACLAR],
        "son_maclar": list(reversed(oynananlar[-SON_MACLAR:])),
        "oynanan": len(oynananlar),
        "toplam": len(maclar),
        "guncelleme": (puan or {}).get("guncelleme"),
        "bayat": bool((puan or {}).get("bayat")),
        "kaynak": (puan or {}).get("kaynak"),
    }


def bolum_verisi(puan: dict | None) -> dict | None:
    """Şablonun `bursaspor` adıyla aldığı bağlam; fikstür yoksa None."""
    fikstur = fikstur_hazirla(puan)
    return {"fikstur": fikstur} if fikstur else None
