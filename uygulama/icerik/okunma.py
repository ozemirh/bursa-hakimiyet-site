"""Okunma sayacı — sayma, tamponlama ve "en çok okunan" sorgusu.

Site üç yerde "EN ÇOK OKUNANLAR" başlığı taşıyor: anasayfanın sağ rayı,
haber detayının rayı ve bölüm sayfasının beşli şeridi (§47). Üçü de bugüne
kadar **okunma verisi olmadığı için** listenin bir sonraki dilimini
basıyordu (URUN-PLANI.md §4, madde 8: sayaç göçte kurtarılamadı). Bu modül
o veriyi üretir ve üç modülü de tek kapıdan besler.

**Yazma okuma yolunda tamponlanır.** Her sayfa görüntülemesini doğrudan
veritabanına yazmak, `journal_mode=delete` ile çalışan bir SQLite'ta her
okurun her tıklamasında dosya kilidi almak demekti. Sayımlar süreç içinde
biriktirilir ve `BOSALT_SANIYE` saniyede bir (ya da tamponda `BOSALT_ADET`
kova birikince) tek turda yazılır — `canli.py`deki kısa bellek düzeniyle
aynı mantık. Bedeli: süreç ölürse son turun sayımı kaybolur. Bir okunma
sıralaması için bu kabul edilebilir; sayfanın 500 vermesi değildir, o
yüzden yazma hatası sayfaya hiç yansımaz.

**Liste ya tamamen gerçek olur ya hiç.** Bir modül gerçek veriye ancak
istenen sayıda haberin her biri pencerede `ESIK_OKUNMA` okunmaya ulaşmışsa
geçer; ulaşmamışsa çağıran eski davranışına döner. Yarısı gerçek yarısı
"listenin devamı" olan bir sıralama okura sayı diye yalan söylerdi —
§4 madde 8'in "başta editör seçkisi, sonra otomatik" kararı budur.
"""

from __future__ import annotations

import threading
import time
from datetime import date, timedelta

from django.db import DatabaseError
from django.db.models import F, Sum
from django.utils import timezone

from .models import Okunma

# Sıralamanın penceresi. Gazetede "en çok okunan" her zaman bir pencere
# ölçüsüdür; ömür boyu toplam eski bir haberi listeye kalıcı çakar.
PENCERE_GUN = 7

# Bir haberin sıralamaya girebilmesi için pencerede ulaşması gereken en az
# okunma. Sayacın ilk gününde üç okunmayla kurulmuş bir "en çok okunanlar"
# listesi gürültüdür; eşik onu bekletir.
ESIK_OKUNMA = 10

# Aynı okurun aynı haberi bu süre içinde yeniden açması sayılmaz (yenileme,
# geri tuşu, sekmede açık bırakma). Süre bellekte tutulur, kalıcı değildir.
TEKRAR_SANIYE = 30 * 60

# Tampon boşaltma eşikleri.
BOSALT_SANIYE = 30
BOSALT_ADET = 50

# Tekrar süzgecinin bellek tavanı. Aşılırsa tablo tamamen boşalır: sayaç
# fazladan sayar, süreç şişmez. Yanlış yön bilerek seçildi.
IMZA_TAVANI = 20_000

# Kullanıcı aracısında bunlardan biri geçiyorsa istek sayılmaz. Liste
# eksiksiz değil ve olamaz; amaç sıralamayı kaba taramalardan korumak,
# tam bir bot tespiti kurmak değil.
BOT_IZLERI = (
    "bot", "crawl", "spider", "slurp", "archiver", "wget", "curl",
    "python-requests", "httpx", "okhttp", "java/", "go-http", "headless",
    "lighthouse", "pagespeed", "monitor", "uptime", "preview",
    "facebookexternalhit", "embedly", "semrush", "ahrefs", "mj12", "dotbot",
    "petalsearch", "bytespider", "gptbot", "claudebot", "ccbot",
)

_kilit = threading.Lock()
_bekleyen: dict[tuple[int, date], int] = {}
_imzalar: dict[int, float] = {}
_son_bosaltma = time.monotonic()


# --------------------------------------------------------------------------
# Sayma

def _bot_mu(ajan: str) -> bool:
    return any(iz in ajan for iz in BOT_IZLERI)


def _on_yukleme_mi(request) -> bool:
    """Tarayıcının, okur daha tıklamadan yaptığı hazırlık isteği."""
    basliklar = (request.META.get("HTTP_SEC_PURPOSE", ""),
                 request.META.get("HTTP_PURPOSE", ""),
                 request.META.get("HTTP_X_MOZ", ""))
    return any("prefetch" in b.lower() or "prerender" in b.lower()
               for b in basliklar)


def _imza(request, haber_id: int) -> int:
    """Okurun kimliği DEĞİL — yalnız "bunu az önce saydık mı" anahtarı.

    Adres ve tarayıcı dizisi belleğe **yazılmaz**; yalnız karması tutulur ve
    `TEKRAR_SANIYE` sonunda düşer. Vekil sunucu arkasında `REMOTE_ADDR`
    bütün okurlarda aynı olurdu ve sayaç haber başına yarım saatte bir
    okunma sayardı; o yüzden `X-Forwarded-For`un ilk adımı öncelikli.
    Taklit edilebilir, ama taklidin kazancı sayacı şişirmektir, okuru
    tanımak değil.
    """
    ileten = request.META.get("HTTP_X_FORWARDED_FOR", "")
    adres = ileten.split(",")[0].strip() or request.META.get("REMOTE_ADDR", "")
    return hash((adres, request.META.get("HTTP_USER_AGENT", ""), haber_id))


def sayilmali(request, haber_id: int) -> bool:
    if request.method != "GET":
        return False
    ajan = request.META.get("HTTP_USER_AGENT", "").lower()
    if not ajan or _bot_mu(ajan) or _on_yukleme_mi(request):
        return False

    simdi = time.monotonic()
    imza = _imza(request, haber_id)
    with _kilit:
        gorulme = _imzalar.get(imza)
        if gorulme is not None and simdi - gorulme < TEKRAR_SANIYE:
            return False
        if len(_imzalar) >= IMZA_TAVANI:
            _imzalar.clear()
        _imzalar[imza] = simdi
    return True


def say(request, haber_id: int) -> None:
    """Bir haber görüntülemesini işle. **Hiçbir koşulda yükselmez.**"""
    try:
        if not sayilmali(request, haber_id):
            return
        anahtar = (haber_id, timezone.localdate())
        with _kilit:
            _bekleyen[anahtar] = _bekleyen.get(anahtar, 0) + 1
            dolu = len(_bekleyen) >= BOSALT_ADET
        if dolu:
            bosalt()
        else:
            gerekliyse_bosalt()
    except Exception:
        # Sayaç, sayfanın çalışmasının ön koşulu değildir.
        pass


# --------------------------------------------------------------------------
# Tamponu yazma

def gerekliyse_bosalt() -> None:
    if time.monotonic() - _son_bosaltma >= BOSALT_SANIYE:
        bosalt()


def bosalt() -> int:
    """Tamponu veritabanına yazar; yazılan kova sayısını döndürür.

    Yazma başarısız olursa (kilitli dosya, dolu disk) sayımlar tampona GERİ
    konur ve bir sonraki turda denenir; tavan aşılmışsa düşürülür — sayaç
    eksik sayar, süreç şişmez.
    """
    global _son_bosaltma
    with _kilit:
        _son_bosaltma = time.monotonic()
        kovalar = dict(_bekleyen)
        _bekleyen.clear()
    if not kovalar:
        return 0

    yazilan = 0
    for (haber_id, gun), adet in kovalar.items():
        if _kovayi_yaz(haber_id, gun, adet):
            yazilan += 1
        else:
            with _kilit:
                if len(_bekleyen) < BOSALT_ADET * 4:
                    anahtar = (haber_id, gun)
                    _bekleyen[anahtar] = _bekleyen.get(anahtar, 0) + adet
    return yazilan


def _kovayi_yaz(haber_id: int, gun: date, adet: int) -> bool:
    """Kovayı artır, yoksa aç. Yarışta (iki süreç aynı kovayı açtı) bir kez
    daha dener; ikisi de olmazsa `False` döner ve sayım tampona geri gider."""
    for son_deneme in (False, True):
        try:
            if (Okunma.objects.filter(haber_id=haber_id, gun=gun)
                    .update(adet=F("adet") + adet)):
                return True
            Okunma.objects.create(haber_id=haber_id, gun=gun, adet=adet)
            return True
        except DatabaseError:
            if son_deneme:
                return False
    return False


def sifirla() -> None:
    """Testler için: tamponu ve tekrar süzgecini boşaltır."""
    global _son_bosaltma
    with _kilit:
        _bekleyen.clear()
        _imzalar.clear()
        _son_bosaltma = time.monotonic()


# --------------------------------------------------------------------------
# Sıralama

def pencere_basi() -> date:
    """Pencerenin ilk günü — bugün dâhil `PENCERE_GUN` gün."""
    return timezone.localdate() - timedelta(days=PENCERE_GUN - 1)


# Sıralamadan kaç aday çekilecek. Kapsam (yayında olma, kategori, ilçe)
# çağıranın sorgusuyla uygulandığı için aday listesi istenen sayıdan geniş
# olmalı: bölüm şeridi, sitenin en çok okunanları içinden KENDİ bölümüne
# ait olanları seçiyor. Tavan bir güvenlik sınırı — haftanın en çok okunan
# 500 haberi arasında bir bölümden beş kayıt yoksa, o bölümün gösterilmeye
# değer bir sıralaması gerçekten yoktur ve geri düşüş doğru davranıştır.
ADAY_TAVANI = 500


def en_cok(sorgu, adet: int, haric=()) -> list:
    """Pencerede en çok okunan `adet` haber; kapsamı `sorgu` belirler.

    Veri yetersizse **boş liste** döner ve çağıran eski davranışına döner
    (bkz. modül başlığı). `sorgu` çağıranın kendi listesidir: yayında olma
    koşulu, kategori/ilçe daraltması ve `select_related`/`prefetch_related`
    onun üzerinden gelir, yani bu modül sayfanın sorgu düzenini
    değiştirmez.

    **Haber tablosuna HİÇ katılmıyor** ve bu bilerek böyle. İki deneme
    ölçüldü (3 Eylül 2026, 1.038.474 satır):

        haber__in=sorgu.values("pk") alt sorgusu   2.593 ms
        icerik_okunma INNER JOIN icerik_haber      2.303 ms
        katılımsız (bu hâli)                         < 1 ms

    Birincisi `yayin_zamani IS NOT NULL` koşulunu alt sorguya taşıyordu ve
    o koşul hiçbir B-ağacı indeksiyle karşılanamıyor — tabloyu baştan sona
    tarıyordu. İkincisinde planlayıcı, boş `icerik_okunma` tablosunun
    istatistiği olmadığı için birleşmeyi TERS taraftan sürdü (`SCAN
    icerik_haber`). Sıralama artık yalnız küçük tablodan çıkıyor ve
    planlayıcının kararına bağlı değil; ikinci adım en fazla
    `ADAY_TAVANI` kimlik için birincil anahtar aramasıdır.

    Dönen kayıtlara `okunma_adedi` iliştirilir; şablon isterse sayıyı
    gösterebilir, göstermek zorunda değildir.
    """
    if adet <= 0:
        return []
    gerekliyse_bosalt()

    satirlar = Okunma.objects.filter(gun__gte=pencere_basi())
    if haric:
        satirlar = satirlar.exclude(haber_id__in=list(haric))
    siralar = (satirlar.values("haber_id")
               .annotate(toplam=Sum("adet"))
               .filter(toplam__gte=ESIK_OKUNMA)
               .order_by("-toplam", "-haber_id")[:ADAY_TAVANI])
    sira = {s["haber_id"]: s["toplam"] for s in siralar}
    if len(sira) < adet:
        return []

    kayitlar = {h.pk: h for h in sorgu.filter(pk__in=list(sira))}
    sonuc = []
    for haber_id in sorted(sira, key=lambda k: (-sira[k], -k)):
        kayit = kayitlar.get(haber_id)
        if kayit is not None:
            kayit.okunma_adedi = sira[haber_id]
            sonuc.append(kayit)
            if len(sonuc) == adet:
                break
    return sonuc if len(sonuc) == adet else []


def toplamlar(haber_kimlikleri, gun_sayisi: int = PENCERE_GUN) -> dict[int, int]:
    """Panel listesi için: verilen haberlerin penceredeki okunma toplamı.

    Sayfadaki 20 satır için 20 sorgu değil, tek toplama sorgusu.
    """
    kimlikler = list(haber_kimlikleri)
    if not kimlikler:
        return {}
    bas = timezone.localdate() - timedelta(days=gun_sayisi - 1)
    satirlar = (Okunma.objects.filter(haber_id__in=kimlikler, gun__gte=bas)
                .values("haber_id").annotate(toplam=Sum("adet")))
    return {s["haber_id"]: s["toplam"] for s in satirlar}
