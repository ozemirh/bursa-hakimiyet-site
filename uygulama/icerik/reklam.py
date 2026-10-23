"""Yerel test reklam hizmeti — 7 Eylül 2026, kullanıcı isteği.

Mevcut reklam kutularının **gerçek bir yaratıcıyla nasıl durduğunu** görmek
için. Gelir sunumu ya da reklam sunucusu değil; o F7(b)'nin işi.

**Neden dış ağ değil, yerel hizmet.** Google demo ağı (`REKLAM_DEMO`,
31 Ağustos 2026) yerinde duruyor ama üç kısıtı var ve üçü de ölçüldü:
üç ölçüyü dolduruyor (300x250, 160x600, 728x90), gerisi boş dönüyor —
yani 1100x150 üst şerit, 970x250 billboard ve 300x600 hiç görünmüyor;
üçüncü taraf çerezi bırakıyor, canlıda çerez aydınlatması gerektiriyor;
internet olmadan hiçbir kutu dolmuyor. Bu hizmet üçünü de çözer: yaratıcı
sunucuda, istenen ölçüde, tam olarak üretilir.

**Yaratıcı sahte reklam DEĞİL.** Marka adı, reklamveren, ürün, fiyat yok —
üstünde "TEST REKLAMI" yazar, ölçüsü ve yuva adı okunur. Okur bunu gerçek
bir reklamla karıştırmasın diye böyle; sahte reklamveren üretmek
`CLAUDE.md`nin "uydurma içerik yok" kuralına da girerdi.

**Kapı: sunum aracı, okur özelliği değil.** `baglam.sunum_araci_mi` —
geliştirme makinesi ya da panele girmiş kullanıcı. Sıradan ziyaretçi bu
adresten 404 alır; canlıda bir yuvaya test görseli düşmesi bu yüzden
mümkün değil.
"""

from __future__ import annotations

from django.conf import settings
from django.http import Http404, HttpResponse
from django.utils.html import escape

from .baglam import sunum_araci_mi

# Yaratıcı ölçüsü sınırları. 50 px altı hiçbir standart yuvada yok;
# 2000 px üstü de yok — sınır adresi çöp değerlere karşı kapatır.
EN_KUCUK, EN_BUYUK = 50, 2000

# Dört palet. Amaç sayfadaki yuvaların BİRBİRİNDEN AYIRT EDİLMESİ: aynı
# sayfada altı kutu aynı gri dikdörtgen olursa hangi yuvanın dolduğu
# görünmez. Renkler sitenin kendi değişkenlerinden alındı (site.css :root);
# yeni renk uydurulmadı.
PALETLER = (
    # zemin, yazı, ikincil yazı, vurgu
    ("#1B2A6B", "#FFFFFF", "#B9C6D4", "#E4222B"),  # lacivert
    ("#F6F8FA", "#14181D", "#606A75", "#1B2A6B"),  # yumuşak kâğıt
    ("#243044", "#FFFFFF", "#A3B2C6", "#E4222B"),  # afiş zemini
    ("#0E5C36", "#FFFFFF", "#B6D9C5", "#EAF4EE"),  # saha yeşili
)


def _palet(anahtar: str) -> tuple[str, str, str, str]:
    """Yuva adına göre SABİT palet.

    Rastgele seçilmiyor: aynı yuva her yenilemede aynı renkte kalsın,
    sunum sırasında kutular yer değiştirmiş gibi görünmesin.
    """
    toplam = sum(ord(k) for k in anahtar) if anahtar else 0
    return PALETLER[toplam % len(PALETLER)]


def _kirp(deger: float, alt: float, ust: float) -> float:
    return max(alt, min(ust, deger))


def _okunur_yazi(zemin: str) -> str:
    """Verilen zemin üstünde okunan yazı rengi: koyu mürekkep ya da kâğıt.

    "TEST" rozeti vurgu renginde basılıyor ve vurgu her palette koyu
    değil — saha yeşilinde açık yeşil (`#EAF4EE`). Rozet yazısı sabit
    beyaz bırakılınca o palette GÖRÜNMÜYORDU (ölçüldü); renk artık
    zeminin parlaklığından hesaplanıyor.
    """
    r, g, b = (int(zemin[i:i + 2], 16) / 255 for i in (1, 3, 5))
    parlaklik = 0.2126 * r + 0.7152 * g + 0.0722 * b
    return "#14181D" if parlaklik > 0.5 else "#FFFFFF"


def _metin(x, y, punto, renk, icerik, aile="Arial, sans-serif",
           kalin=False, aralik=0.0, hiza="middle", opaklik=None):
    ek = f' fill-opacity="{opaklik}"' if opaklik is not None else ""
    agirlik = ' font-weight="700"' if kalin else ""
    return (f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{hiza}" '
            f'font-family="{aile}" font-size="{punto:.1f}"{agirlik} '
            f'letter-spacing="{aralik:.2f}" fill="{renk}"{ek}>{icerik}</text>')


def _gorsel_alani(x, y, en, boy, vurgu, ikincil):
    """Reklamın görsel alanı — SOYUT.

    Gerçek bir reklamda buranın yerinde ürün fotoğrafı ya da marka
    görseli olur; test yaratıcısında **şekil** var: marka, ürün, logo,
    fotoğraf uydurulmuyor. Amaç kutunun ağırlığını göstermek — düz gri
    dikdörtgen sayfanın reklamla nasıl duracağını anlatmıyordu.
    """
    r = min(en, boy) * 0.30
    return (
        f'<g><rect x="{x:.1f}" y="{y:.1f}" width="{en:.1f}" '
        f'height="{boy:.1f}" fill="{vurgu}" fill-opacity=".16"/>'
        f'<circle cx="{x + en * 0.34:.1f}" cy="{y + boy * 0.46:.1f}" '
        f'r="{r:.1f}" fill="{vurgu}" fill-opacity=".55"/>'
        f'<path d="M{x + en * 0.52:.1f} {y + boy * 0.80:.1f} '
        f'L{x + en * 0.70:.1f} {y + boy * 0.34:.1f} '
        f'L{x + en * 0.88:.1f} {y + boy * 0.80:.1f} Z" '
        f'fill="{ikincil}" fill-opacity=".42"/>'
        f'<rect x="{x:.1f}" y="{y + boy - 3:.1f}" width="{en:.1f}" '
        f'height="3" fill="{vurgu}"/></g>')


def _rozet(x, y, punto, vurgu):
    """Sol üstteki TEST şeridi — her ölçüde, her palette."""
    return (f'<g><rect x="{x:.1f}" y="{y:.1f}" width="{punto * 4.4:.1f}" '
            f'height="{punto * 1.9:.1f}" fill="{vurgu}"/>'
            + _metin(x + punto * 2.2, y + punto * 1.36, punto,
                     _okunur_yazi(vurgu), "TEST",
                     aile="Arial Narrow, Arial, sans-serif", kalin=True,
                     aralik=1.4) + '</g>')


def _dugme(x, y, en, boy, dolgu, metin, punto):
    """Çağrı düğmesinin AYAK İZİ.

    Üstünde ölçü yazıyor; sahte bir kampanya çağrısı ("Hemen al",
    "Detaylı bilgi") yazılmıyor — reklamveren de teklif de uydurulmuyor.
    Düğme burada biçimin parçası: gerçek yaratıcıların çoğunda var ve
    kutunun görsel ağırlığını o taşıyor.
    """
    return (f'<g><rect x="{x:.1f}" y="{y:.1f}" width="{en:.1f}" '
            f'height="{boy:.1f}" rx="{boy / 2:.1f}" fill="{dolgu}"/>'
            + _metin(x + en / 2, y + boy * 0.68, punto, _okunur_yazi(dolgu),
                     metin, aile="Arial Narrow, Arial, sans-serif",
                     kalin=True, aralik=punto * 0.08) + '</g>')


def _yatay(en, boy, olcu_metin, yuva, yazi, ikincil, vurgu):
    """Şerit yuvalar (728x90, 970x250, 1100x150): görsel solda, yazı sağda."""
    kenar = _kirp(min(en, boy) * 0.10, 8, 24)
    gorsel = boy - 2 * kenar
    dugme_en = _kirp(en * 0.15, 84, 190)
    dugme_boy = _kirp(boy * 0.26, 22, 46)
    metin_x = kenar * 2 + gorsel
    metin_en = en - metin_x - dugme_en - kenar * 2
    baslik_p = _kirp(min(metin_en / 8.2, boy / 3.4), 12, 38)
    kucuk_p = _kirp(baslik_p * 0.46, 9, 15)

    parcalar = [
        _gorsel_alani(kenar, kenar, gorsel, gorsel, vurgu, ikincil),
        _metin(metin_x, boy / 2 - kucuk_p * 0.1, baslik_p, yazi,
               "TEST REKLAMI", aile="Arial Narrow, Arial, sans-serif",
               kalin=True, aralik=baslik_p * 0.08, hiza="start"),
        _metin(metin_x, boy / 2 + kucuk_p * 1.7, kucuk_p, ikincil,
               escape(yuva) if yuva else "yerel test görseli",
               aralik=0.4, hiza="start"),
        _dugme(en - kenar - dugme_en, (boy - dugme_boy) / 2, dugme_en,
               dugme_boy, vurgu, olcu_metin, _kirp(dugme_boy * 0.42, 10, 17)),
        _rozet(kenar, kenar * 0.5, _kirp(kucuk_p * 0.85, 8, 12), vurgu),
    ]
    return "".join(parcalar)


def _dusey(en, boy, olcu_metin, yuva, yazi, ikincil, vurgu):
    """Kare ve dikey yuvalar (300x250, 160x600): görsel üstte, yazı altta.

    Yazı bloğu görselle düğme ARASINA ortalanıyor, görselin hemen altına
    yapıştırılmıyor. İlk sürümde öyleydi ve iki kusur veriyordu (ölçüldü,
    12 Eylül 2026): 300x250'de yuva adı düğmenin altında kalıyordu,
    160x600'ün alt yarısı bomboştu. Satırlar sığdıkça ekleniyor; sığmayan
    satır basılmaz, üst üste binmez.
    """
    kenar = _kirp(min(en, boy) * 0.08, 8, 22)
    ic_en = en - 2 * kenar
    # Uzun pageskin'de görsel alanı büyür: 160x600'de %38 kalınca kutunun
    # yarısı boş duruyordu.
    oran = 0.56 if boy >= en * 2.5 else (0.42 if boy > en else 0.46)
    gorsel_boy = boy * oran
    baslik_p = _kirp(min(ic_en / 7.6, boy / 8.0), 11, 30)
    kucuk_p = _kirp(baslik_p * 0.52, 9, 14)
    dugme_boy = _kirp(boy * 0.10, 22, 40)
    dugme_en = _kirp(ic_en * 0.62, 74, 190)

    parcalar = [
        _gorsel_alani(kenar, kenar, ic_en, gorsel_boy, vurgu, ikincil),
        _rozet(kenar, kenar * 0.55, _kirp(kucuk_p * 0.82, 8, 12), vurgu),
        _dugme((en - dugme_en) / 2, boy - kenar - dugme_boy, dugme_en,
               dugme_boy, vurgu, olcu_metin, _kirp(dugme_boy * 0.40, 10, 16)),
    ]

    # Dar yuvada (160x600) başlık tek satıra sığmıyor — ölçüldü, iki satır.
    bas = dict(aile="Arial Narrow, Arial, sans-serif", kalin=True,
               aralik=baslik_p * 0.08)
    satirlar = []
    if ic_en >= baslik_p * 6.6:
        satirlar.append((baslik_p * 1.15, baslik_p, yazi, "TEST REKLAMI", bas))
    else:
        satirlar.append((baslik_p * 1.12, baslik_p, yazi, "TEST", bas))
        satirlar.append((baslik_p * 1.15, baslik_p, yazi, "REKLAMI", bas))
    kucuk = dict(aralik=0.4)
    if yuva:
        satirlar.append((kucuk_p * 1.7, kucuk_p, ikincil, escape(yuva), kucuk))
    satirlar.append((kucuk_p * 1.5, kucuk_p, ikincil, "reklam değil",
                     dict(aralik=0.4, opaklik=".75")))

    ust = kenar + gorsel_boy
    alt = boy - kenar - dugme_boy - 6
    while satirlar and sum(s[0] for s in satirlar) > alt - ust:
        satirlar.pop()          # sığmayan satır basılmaz
    y = (ust + alt - sum(s[0] for s in satirlar)) / 2
    for yukseklik, punto, renk, metin, ek in satirlar:
        y += yukseklik
        parcalar.append(_metin(en / 2, y - yukseklik * 0.28, punto, renk,
                               metin, **ek))
    return "".join(parcalar)


def yaratici_svg(en: int, boy: int, yuva: str = "") -> str:
    """İstenen ölçüde test yaratıcısı. Dışarıya hiçbir şey bağlamaz.

    **Neden reklam BİÇİMİNDE.** İlk sürüm ortalanmış yazıdan ibaretti ve
    ekranda Google demo ağının gri örnek kutularından ayrılmıyordu —
    kullanıcı haklı olarak "hepsi yer tutucu" dedi (12 Eylül 2026).
    Yaratıcı artık gerçek bir görüntülü reklamın parçalarını taşıyor:
    görsel alanı, başlık, çağrı düğmesi.

    **Ama sahte reklam değil.** Marka, reklamveren, ürün, fiyat, kampanya
    çağrısı YOK; görsel alanı soyut şekil, düğmenin üstünde ölçü yazıyor.
    Uydurma içerik yasağı (CLAUDE.md) burada da geçerli.
    """
    zemin, yazi, ikincil, vurgu = _palet(yuva or f"{en}x{boy}")
    olcu_metin = f"{en} &#215; {boy}"
    bicim = _yatay if en >= boy * 2.2 else _dusey
    ic = bicim(en, boy, olcu_metin, yuva, yazi, ikincil, vurgu)

    baslik = escape(f"Test reklamı {en}×{boy}")
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{en}" height="{boy}" '
        f'viewBox="0 0 {en} {boy}" role="img" aria-label="{baslik}">'
        f'<title>{baslik}</title>'
        f'<rect width="{en}" height="{boy}" fill="{zemin}"/>'
        f'<rect x=".5" y=".5" width="{en - 1}" height="{boy - 1}" fill="none" '
        f'stroke="{vurgu}" stroke-opacity=".45"/>'
        f'{ic}</svg>')


def test_yaratici(request, en, boy):
    """`/reklam/test/300x250.svg` — sunum aracı, herkese açık değil."""
    if not sunum_araci_mi(request):
        raise Http404("test reklam hizmeti yalnız sunum oturumunda açık")

    en, boy = int(en), int(boy)
    if not (EN_KUCUK <= en <= EN_BUYUK and EN_KUCUK <= boy <= EN_BUYUK):
        raise Http404("ölçü sınır dışı")

    yuva = (request.GET.get("yuva") or "").strip()[:60]
    yanit = HttpResponse(yaratici_svg(en, boy, yuva),
                         content_type="image/svg+xml; charset=utf-8")
    # Sunum aracının çıktısı: paylaşılan önbelleğe (CDN, vekil) girmesin.
    yanit["Cache-Control"] = "private, max-age=300"
    return yanit


def ads_txt(request):
    """`/ads.txt` — AdSense kimliği verildiyse yayımlanır (IAB sözleşmesi).

    Dosya "bu alan adında reklam satmaya kim yetkili" beyanıdır; yoksa
    gerçek yayında talebin büyük kısmı düşer. İçerik kimlikten üretiliyor,
    elle tutulan ikinci bir kopya olmasın diye:

        google.com, pub-<kimlik>, DIRECT, f08c47fec0942fa0

    Sondaki değer Google'ın **sabit** sertifika kimliği (TAG ID), hesaba
    göre değişmez. Kimlik yokken 404: boş ya da yanlış bir ads.txt
    yayımlamak, dosyanın hiç olmamasından kötüdür.
    """
    kimlik = settings.ADSENSE_ID
    if not kimlik:
        raise Http404("AdSense kimliği tanımlı değil")
    # "ca-pub-123" -> "pub-123"; ads.txt satırı ca- öneki almaz.
    yayinci = kimlik[3:] if kimlik.startswith("ca-") else kimlik
    return HttpResponse(
        f"google.com, {yayinci}, DIRECT, f08c47fec0942fa0\n",
        content_type="text/plain; charset=utf-8")
