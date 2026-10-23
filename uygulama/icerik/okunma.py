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

**Tek işlem, tek deyim (19 Ekim 2026).** Boşaltma eskiden kova başına bir
`UPDATE` + gerekirse `INSERT` açıyordu; her biri kendi işleminde, yani
`journal_mode=delete` altında kova başına bir disk eşitlemesi ve yazma
kilidi. Artık bütün tampon `transaction.atomic()` içinde çok satırlı tek
bir `INSERT … ON CONFLICT DO UPDATE SET adet = adet + excluded.adet`
deyimiyle yazılıyor; sözdizimi SQLite (3.24+) ve PostgreSQL'de aynı.

**Okuma yolu yazmaz.** `en_cok()` eskiden boşaltmayı da tetikliyordu; yani
en çok okunanları SORAN her sayfa yazma kilidine girebiliyordu. Boşaltma
yalnız sayım yolunda (`say`) ve `okunma_bosalt` komutunda.

**İki yazım düzeni** (`settings.OKUNMA_YAZIM`): `istek` (varsayılan) —
yukarıdaki gibi istek yolu yazar; `komut` — istek yolu tamponu yalnız
kuyruk dosyasına bırakır, veritabanına `manage.py okunma_bosalt` taşır.
Zamanlanmış görev kullanıcı kararıdır ve açılmadı; `komut` düzeni ancak o
görev kurulunca seçilmeli, yoksa sayım kuyrukta bekler. Süreç kapanırken
tampon her iki düzende de kuyruk dosyasına bırakılır, kaybolmaz.

**Liste ya tamamen gerçek olur ya hiç.** Bir modül gerçek veriye ancak
istenen sayıda haberin her biri pencerede `ESIK_OKUNMA` okunmaya ulaşmışsa
geçer; ulaşmamışsa çağıran eski davranışına döner. Yarısı gerçek yarısı
"listenin devamı" olan bir sıralama okura sayı diye yalan söylerdi —
§4 madde 8'in "başta editör seçkisi, sonra otomatik" kararı budur.
"""

from __future__ import annotations

import atexit
import ipaddress
import json
import os
import threading
import time
from datetime import date, timedelta
from functools import lru_cache
from pathlib import Path

from django.conf import settings
from django.db import DatabaseError, IntegrityError, connection, transaction
from django.db.models import Sum
from django.utils import timezone

from .models import Haber, Okunma

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


@lru_cache(maxsize=8)
def _vekil_aglari(tanim: tuple[str, ...]) -> tuple:
    aglar = []
    for parca in tanim:
        try:
            aglar.append(ipaddress.ip_network(parca, strict=False))
        except ValueError:
            continue    # bozuk girdi ayarı düşürmez, yalnız o satır yok sayılır
    return tuple(aglar)


def _guvenilir(adres: str, aglar) -> bool:
    try:
        ip = ipaddress.ip_address(adres)
    except ValueError:
        return False
    return any(ip in ag for ag in aglar)


def ziyaretci_adresi(request) -> str:
    """Okurun adresi — `X-Forwarded-For`a KOŞULSUZ güvenmeden.

    Başlık yalnız istek güvenilir bir vekilden geldiyse
    (`settings.GUVENILIR_VEKILLER`) okunur ve SAĞDAN SOLA yürünür: zincirin
    sağ ucu bizim vekilimizin gördüğü adrestir, sol ucu ise istemcinin
    kendi yazdığı, taklit edilebilen kısım. İlk güvenilmeyen adım okurdur.
    Liste boşsa başlık hiç okunmaz: eskiden ilk adım koşulsuz alınıyordu ve
    herkes başlığa rastgele adres yazıp tekrar süzgecini atlatabiliyordu.
    """
    uzak = request.META.get("REMOTE_ADDR", "")
    aglar = _vekil_aglari(tuple(getattr(settings, "GUVENILIR_VEKILLER", ()) or ()))
    if not aglar or not _guvenilir(uzak, aglar):
        return uzak
    zincir = [a.strip() for a in
              request.META.get("HTTP_X_FORWARDED_FOR", "").split(",") if a.strip()]
    for adres in reversed(zincir):
        if not _guvenilir(adres, aglar):
            return adres
    return zincir[0] if zincir else uzak


def _imza(request, haber_id: int) -> int:
    """Okurun kimliği DEĞİL — yalnız "bunu az önce saydık mı" anahtarı.

    Adres ve tarayıcı dizisi belleğe **yazılmaz**; yalnız karması tutulur ve
    `TEKRAR_SANIYE` sonunda düşer. Vekil sunucu arkasında `REMOTE_ADDR`
    bütün okurlarda aynı olurdu ve sayaç haber başına yarım saatte bir
    okunma sayardı; adresin nasıl bulunduğu `ziyaretci_adresi`nde.
    """
    return hash((ziyaretci_adresi(request), request.META.get("HTTP_USER_AGENT", ""),
                 haber_id))


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


def _tamponu_al() -> dict[tuple[int, date], int]:
    global _son_bosaltma
    with _kilit:
        _son_bosaltma = time.monotonic()
        kovalar = dict(_bekleyen)
        _bekleyen.clear()
    return kovalar


def _tampona_geri_koy(kovalar: dict) -> None:
    """Yazılamayan sayım bir sonraki tura kalır; tavan aşılmışsa yeni kova
    düşer — sayaç eksik sayar, süreç şişmez."""
    with _kilit:
        for anahtar, adet in kovalar.items():
            if anahtar not in _bekleyen and len(_bekleyen) >= BOSALT_ADET * 4:
                continue
            _bekleyen[anahtar] = _bekleyen.get(anahtar, 0) + adet


def bosalt() -> int:
    """Tamponu boşaltır; işlenen kova sayısını döndürür.

    `istek` düzeninde veritabanına yazar (varsa kuyruk dosyalarını da aynı
    işleme katar), `komut` düzeninde yalnız kuyruk dosyasına bırakır.
    Yazma başarısız olursa (kilitli dosya, dolu disk) sayımlar tampona GERİ
    konur ve bir sonraki turda denenir.
    """
    kovalar = _tamponu_al()
    if getattr(settings, "OKUNMA_YAZIM", "istek") == "komut":
        if kovalar and not kuyruga_yaz(kovalar):
            _tampona_geri_koy(kovalar)
            return 0
        return len(kovalar)
    if not kovalar and not _kuyruk_dosyalari():
        return 0
    try:
        return kuyrugu_bosalt(ek=kovalar)
    except DatabaseError:
        _tampona_geri_koy(kovalar)
        return 0


def _upsert(kovalar: dict[tuple[int, date], int]) -> None:
    """Bütün kovalar TEK işlemde, parti başına çok satırlı TEK deyimle.

    `ON CONFLICT (haber_id, gun) DO UPDATE` iki sürecin aynı kovayı aynı
    anda açma yarışını da kapatıyor: eskiden UPDATE boş dönünce INSERT
    deneniyor, yarışı kaybeden süreç bütünlük hatası alıp yeniden
    deniyordu.
    """
    q = connection.ops.quote_name
    tablo = q(Okunma._meta.db_table)
    haber_s, gun_s, adet_s = q(Okunma._meta.get_field("haber").column), q("gun"), q("adet")
    satirlar = [(h, g.isoformat(), a) for (h, g), a in kovalar.items() if a > 0]
    parti = 300   # 3 değişken × 300 = 900: SQLite'ın eski 999 sınırının altında
    with transaction.atomic():
        with connection.cursor() as imlec:
            for i in range(0, len(satirlar), parti):
                dilim = satirlar[i:i + parti]
                yer = ", ".join(["(%s, %s, %s)"] * len(dilim))
                imlec.execute(
                    f"INSERT INTO {tablo} ({haber_s}, {gun_s}, {adet_s}) VALUES {yer} "
                    f"ON CONFLICT ({haber_s}, {gun_s}) DO UPDATE SET "
                    f"{adet_s} = {tablo}.{adet_s} + excluded.{adet_s}",
                    [d for satir in dilim for d in satir])
        # Yabancı anahtarlar iki motorda da DEFERRABLE INITIALLY DEFERRED:
        # ihlal deyimde değil işlem SONUNDA patlar. Bu blok dış bir işlemin
        # içindeyse (savepoint) hata `kovalari_yaz`ın `IntegrityError`
        # dalına hiç düşmez, dış işlemin commit'inde patlayıp onu da geri
        # alırdı (B paketi, 19 Ekim 2026; tests_pg_uyum.OkunmaYetimKova).
        # Denetim burada zorlanır: PG `SET CONSTRAINTS ALL IMMEDIATE`,
        # SQLite `PRAGMA foreign_key_check(tablo)`.
        connection.check_constraints(table_names=[Okunma._meta.db_table])


def kovalari_yaz(kovalar: dict[tuple[int, date], int]) -> int:
    """Kovaları veritabanına yazar; yazılan kova sayısını döndürür.

    Arada silinmiş bir haberin kovası bütün partiyi bütünlük hatasıyla
    düşürmesin diye hata alınırsa var olmayan kimlikler ayıklanıp bir kez
    daha denenir. `DatabaseError` çağırana yükselir.
    """
    if not kovalar:
        return 0
    try:
        _upsert(kovalar)
        return len(kovalar)
    except IntegrityError:
        var = set(Haber.objects.filter(pk__in={h for h, _ in kovalar})
                  .values_list("pk", flat=True))
        temiz = {k: a for k, a in kovalar.items() if k[0] in var}
        _upsert(temiz)
        return len(temiz)


# --------------------------------------------------------------------------
# Kuyruk dosyaları — `komut` düzeni ve süreç kapanışı

def _kuyruk_koku() -> Path:
    return Path(getattr(settings, "OKUNMA_KUYRUK_KOK", "okunma-kuyrugu"))


def _kuyruk_dosyalari() -> list[Path]:
    kok = _kuyruk_koku()
    if not kok.is_dir():
        return []
    return sorted(kok.glob("okunma-*.json"))


def kuyruga_yaz(kovalar: dict[tuple[int, date], int]) -> bool:
    """Kovaları süreç adına benzersiz bir dosyaya bırakır.

    Önce `.tmp` yazılıp sonra adı değiştiriliyor: komut yarım dosya
    okumasın. Dosya adı süreç kimliği + nanosaniye; iki süreç aynı dosyaya
    hiç yazmaz, kilit gerekmez.
    """
    if not kovalar:
        return True
    try:
        kok = _kuyruk_koku()
        kok.mkdir(parents=True, exist_ok=True)
        ad = kok / f"okunma-{os.getpid()}-{time.time_ns()}.json"
        gecici = ad.with_name(ad.name + ".tmp")
        gecici.write_text(json.dumps([[h, g.isoformat(), a]
                                      for (h, g), a in kovalar.items()]),
                          encoding="utf-8")
        os.replace(gecici, ad)
        return True
    except OSError:
        return False


def kuyrugu_bosalt(ek: dict | None = None) -> int:
    """Kuyruk dosyalarını (ve `ek` tamponunu) TEK işlemde veritabanına yazar.

    Her dosya önce sürece özel bir ada taşınarak SAHİPLENİLİR; aynı anda
    çalışan ikinci bir boşaltıcı o dosyayı göremez, sayım iki kez yazılmaz.
    Yazım düşerse dosyalar eski adlarına döner ve sayım kaybolmaz.
    """
    toplam: dict[tuple[int, date], int] = dict(ek or {})
    sahiplenilen: list[tuple[Path, Path]] = []
    for dosya in _kuyruk_dosyalari():
        hedef = dosya.with_name(f"{dosya.stem}.isleniyor-{os.getpid()}")
        try:
            os.replace(dosya, hedef)
        except OSError:
            continue    # başka bir boşaltıcı aldı
        try:
            for h, g, a in json.loads(hedef.read_text(encoding="utf-8")):
                anahtar = (int(h), date.fromisoformat(g))
                toplam[anahtar] = toplam.get(anahtar, 0) + int(a)
        except (OSError, ValueError, TypeError):
            # Bozuk dosya sonsuza dek yeniden denenmesin: kenara alınır.
            os.replace(hedef, hedef.with_name(dosya.stem + ".bozuk"))
            continue
        sahiplenilen.append((dosya, hedef))
    try:
        yazilan = kovalari_yaz(toplam)
    except DatabaseError:
        for dosya, hedef in sahiplenilen:
            os.replace(hedef, dosya)
        raise
    for _, hedef in sahiplenilen:
        hedef.unlink(missing_ok=True)
    return yazilan


def _kapanista_birak() -> None:
    """Süreç kapanırken tampon veritabanına DEĞİL kuyruk dosyasına gider:
    kapanışta veritabanını beklemek süreci asabilir. Bir sonraki boşaltma
    (istek yolu ya da komut) dosyayı toplar."""
    kovalar = _tamponu_al()
    if kovalar:
        kuyruga_yaz(kovalar)


atexit.register(_kapanista_birak)


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
    # Boşaltma burada ÇAĞRILMIYOR (19 Ekim 2026): okuma yolu yazmaz. Tampon
    # en geç `BOSALT_SANIYE` sonra sayım yolunda ya da komutla yazılır.

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
