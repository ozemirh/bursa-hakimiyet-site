# -*- coding: utf-8 -*-
"""İlgili haberler — başlık benzerliğiyle (5 Eylül 2026, kullanıcı isteği).

Eskiden "aynı kategoriden en yeni 5 haber" idi; okur Bozbey davasını
okurken yanında Bursaspor transferi görüyordu. Şimdi haberin başlığındaki
**varlık kökleri** (büyük harfli kişi/kurum/yer adları, `konu_motoru`
ile aynı ayrıştırma) yakın tarihli başlıklarda aranır ve ortak köke göre
puanlanır. Yeterli aday çıkmazsa liste eski kuralla (aynı kategori, en
yeni) tamamlanır — kutu hiç boş kalmaz.

Araştırma notu (kullanıcı isteğiyle, 5 Eylül 2026): yayıncıların yaygın
yöntemi varlık ağırlıklı TF-IDF benzerliği + yakın tarih + çeşitlilik.
Burası aynı düzenin sade hâli: varlık kökü ağır, yer adı hafif,
beraberlikte tarih yakınlığı.

## Aday sorgusu — arama indeksinden (19 Ekim 2026, Paket L2)

Eski aday sorgusu `UPPER(baslik) LIKE '%kök%'` idi: ±60 günlük pencerede
(2021'de ~50 bin satır) her satırı büyük harfe çevirip kalıplarla
karşılaştırıyordu. PostgreSQL'de, 1.038.477 haberde ölçüldü: 200 rastgele
haber detayında sayfa p50 179 ms, p95 496 ms; aday sorgusu en kötü
1.250 ms. Ayrıca `UPPER` veritabanı derlemesine bağlıydı ("İnegöl" ile
"inegöl" aynı büyük harfe çıkmıyordu).

Şimdi aday, **normalize başlıkta** (`HaberArama.baslik`, `arama_metni`
kuralı) **kelime başı** eşleşmesidir — kök zaten kelimenin başıdır
(`konu_motoru.kokle` yalnız son ek düşürür):

- **Hafif çapa** (PostgreSQL): YALNIZ BAŞLIKTAN kurulan ifade GIN indeksi
  (`haberarama_baslik_vektor_gin`, migration 0018) ve `'kok':* | …`
  sorgusu. Okur aramasının `vektor`ü başlık+spot taşıdığı için burada
  kullanılmaz: yalnız spotta geçen ad aday sınırını doldurur ama başlık
  puanından geçemez (ölçüldü: aday 2–14 kat artıyordu).
- **Zaman penceresi kimlik aralığına çevrilir.** Arama tablosunda yayın
  zamanı yok; ama kimlik zamanla neredeyse birebir artıyor (pg_stats
  korelasyonu 0,9998). Pencere uçlarının kimliği kapsayan indeksten
  yoklanır (`kimlik_araligi`) ve GIN bitmap'i birincil anahtar aralığıyla
  kesişir (`BitmapAnd`). Kesin yayın zamanı süzgeci birleşmede yine
  uygulanır.
- **Ağır çapa** ("burs" = Bursa, başlıkların %13'ü) GIN'e sokulmaz;
  makaleden iki yöne birincil anahtar sırasıyla yürünür (`_pg_aday_sorgusu`).
  Hangi çapanın ağır olduğunu planlayıcının kendi istatistiği söyler
  (`siklik`).
- **Aday sınırı yakınlığa göre: makaleye en yakın EN_COK_ADAY (200).**
  Eski sorgu pencerenin EN YENİ 400 başlığını alıyordu — makalenin
  tarihinden bağımsız, yani Bursa'lı bir başlıkta adayların hepsi
  pencerenin son haftalarındandı. Yakınlık sırası bu yüzden 200'de bile
  eskisinden isabetli; 200 rastgele haberde eski/yeni listelerin
  ortalama 5,1–5,4'ü ortak, farklar yakın tarihli aynı konulu haber
  lehine (ölçüm notu: Paket L2 raporu). Sınır Python puanlamasının da
  bedelidir (aday başına ~0,06 ms).
- **SQLite** (yedek yol): aynı normalize başlıkta `LIKE '% kök%'`,
  pencere `yayin_zamani` indeksinden. Anlam iki motorda aynı.

Sonuç kimlik listesi olarak 6 saat önbelleklenir (süreçler arasında
paylaşılan önbellek, `settings.py` başarım bloğu).
"""

from __future__ import annotations

from datetime import datetime, timedelta
from functools import lru_cache

from django.core.cache import cache
from django.db import connection
from django.db.models import Q
from django.db.models.expressions import RawSQL
from django.utils import timezone

from . import konu_motoru as km
from .arama_metni import kelimeler
from .models import Haber

PENCERE_GUN = 60
EN_COK_ADAY = 200
EN_COK_CAPA = 3
ONBELLEK_SN = 6 * 3600

#: `haberarama_baslik_vektor_gin` indeksinin ifadesi. Sorgu bu ifadeyi
#: BİREBİR taşımak zorunda; aksi hâlde planlayıcı indeksi tanımaz.
BASLIK_VEKTOR = "array_to_tsvector(array_remove(string_to_array(baslik, ' '), ''))"


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
    # İkilinin parçalarını ayrıca arama: önek zaten parçayı da yakalar.
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


def _terimler(capalar: list[str]) -> list[list[str]]:
    """Çapaların arama biçimi: her çapa normalize kelime listesi
    (`arama_metni.kelimeler`; "İnegöl" → ["inegol"]). Kelimesiz çapa düşer."""
    cikti = []
    for k in capalar:
        parca = [w.replace("'", "").replace("\\", "") for w in kelimeler(k)]
        parca = [w for w in parca if w]
        if parca:
            cikti.append(parca)
    return cikti


def _tsquery(terimler: list[list[str]]) -> str:
    """`'pfizer':* | 'biontech':*` — her çapa kelime başı öneki, çapalar VEYA."""
    return " | ".join("(" + " & ".join(f"'{w}':*" for w in t) + ")" for t in terimler)


#: Pencere ucundaki kimlik yoklamasının boyu (uçtan içeri bu kadar kayıt).
UC_ORNEK = 51


def _uc_kimligi(an: datetime, ileri: bool) -> int | None:
    """Pencere ucunun kimliği: zaman sırasında `an`dan içeri doğru ilk
    UC_ORNEK kaydın en küçüğü (alt uç) ya da en büyüğü (üst uç) — AYKIRI
    kimlik ayıklanarak (kapsayan indeksten, ~0,2 ms).

    Düz en küçük/en büyük yetmiyor: arşivde sonradan yeniden tarihlenmiş
    birkaç eski kayıt var ve uçları savuruyor (ölçüldü: 2022-10 penceresinin
    en küçük kimliği 186.868, kayıtların %99'u ise 827.309–939.940
    arasında). Uçtaki ardışık kayıtların kimliği birbirine yakındır; ortancaya
    `10 × UC_ORNEK`ten uzak kimlik aykırı sayılır.
    """
    sorgu = Haber.yayindakiler()
    if ileri:
        sorgu = sorgu.filter(yayin_zamani__lte=an).order_by("-yayin_zamani", "-id")
    else:
        sorgu = sorgu.filter(yayin_zamani__gte=an).order_by("yayin_zamani", "id")
    kimlikler = sorted(sorgu.values_list("id", flat=True)[:UC_ORNEK])
    if not kimlikler:
        return None
    ortanca, pay = kimlikler[len(kimlikler) // 2], 10 * UC_ORNEK
    if ileri:
        return max(k for k in kimlikler if k <= ortanca + pay)
    return min(k for k in kimlikler if k >= ortanca - pay)


def kimlik_araligi(bas: datetime, son: datetime) -> tuple[int, int | None] | None:
    """Zaman penceresinin kimlik aralığı `(alt, ust)`; pencere boşsa None.

    Kimlik zamanla birlikte artıyor (pg_stats korelasyonu 0,9998); aralık
    pencerenin ÇEKİRDEĞİDİR. Zamanı pencerede ama kimliği çekirdeğin
    dışında kalan tek tük kayıt (yeniden tarihlenmiş arşiv kaydı ya da
    uçtaki sıra kayması) aday olmaz — kesin zaman süzgeci ayrıca uygulanır.
    Bugüne değen pencerede üst sınır yok (None).
    """
    alt = _uc_kimligi(bas, ileri=False)
    if alt is None:
        return None
    if son >= timezone.now():
        return alt, None
    ust = _uc_kimligi(son, ileri=True)
    if ust is None or ust < alt:
        return None
    return alt, ust


#: Başlıkların bu oranından fazlasında geçen önek "ağır" sayılır (aşağıda).
AGIR_ORAN = 0.03
SIKLIK_ONBELLEK_SN = 24 * 3600


def siklik() -> dict[str, float]:
    """Başlık kelimelerinin sıklığı — planlayıcının KENDİ istatistiği.

    `ANALYZE` ifade indeksinin (`haberarama_baslik_vektor_gin`) en sık
    1.000 kelimesini ve satır oranını `pg_stats`a yazar ("bursa" 0,131,
    "turkiye" 0,025, "erdogan" 0,017 — 19 Ekim 2026). Ek tablo ya da
    sayım yok; istatistik yoksa sözlük boş döner ve her çapa hafif sayılır
    (doğru ama ağır çapada yavaş).
    """
    def uret():
        with connection.cursor() as imlec:
            imlec.execute(
                "SELECT most_common_elems::text::text[], most_common_elem_freqs "
                "FROM pg_stats WHERE tablename = 'haberarama_baslik_vektor_gin'")
            satir = imlec.fetchone()
        if not satir or not satir[0]:
            return {}
        # Oran dizisinin sonunda üç ek değer var (en küçük, en büyük, boş
        # oranı); zip onları kelimesiz bırakır.
        return dict(zip(satir[0], satir[1]))

    anahtar = "ilgili:siklik"
    deger = cache.get(anahtar)
    if deger is None:
        deger = uret()
        cache.set(anahtar, deger, SIKLIK_ONBELLEK_SN)
    return deger


def agir_mi(terim: list[str], sozluk: dict[str, float]) -> bool:
    """Tek kelimelik önek başlıkların AGIR_ORAN'ından fazlasında mı geçiyor?"""
    if len(terim) != 1:
        return False
    onek = terim[0]
    return sum(f for k, f in sozluk.items() if k.startswith(onek)) >= AGIR_ORAN


def _pg_aday_sorgusu(kimlik: int, terimler, aralik, haric_adet: int):
    """Aday kimlikleri veren alt sorgu ve parametreleri.

    **Hafif çapalar** (ör. "pfizer", "inegol") tek GIN taramasında
    birleşir: `'a':* | 'b':*` bitmap'i kimlik aralığıyla kesişir, makaleye
    kimlikçe en yakın EN_COK_ADAY satır alınır.

    **Ağır çapa** ("burs" = Bursa: başlıkların %13'ü, 159.625 kayıt) GIN'e
    hiç sokulmaz: önek listesini okumak tek başına ~45 ms (ölçüldü,
    `Bitmap Index Scan … rows=161545`). Onun yerine birincil anahtar
    makaleden İKİ YÖNE sırayla yürünür ve her yönde yeterli eşleşme
    bulununca durulur (`ORDER BY haber_id … LIMIT`): yoğunluk yüksek
    olduğu için birkaç bin satırda biter (~2–5 ms). Süzgeç `strpos` —
    bilerek indekslenmeyen biçim; `LIKE` yazılsa planlayıcı trigram
    indeksine dönüp aynı ağır listeyi okuyabilirdi.

    Sonuç iki yolun birleşimidir; kesin zaman süzgeci ve en yakın
    EN_COK_ADAY seçimi çağıranda.
    """
    alt, ust = aralik
    sozluk = siklik()
    hafif = [t for t in terimler if not agir_mi(t, sozluk)]
    agir = [t for t in terimler if agir_mi(t, sozluk)]
    sinir = EN_COK_ADAY + haric_adet
    parcalar, parametre = [], []
    ust_kosul = " AND haber_id <= %s" if ust is not None else ""
    ust_param = [ust] if ust is not None else []
    if hafif:
        parcalar.append(
            "(SELECT haber_id FROM icerik_haberarama "
            f"WHERE haber_id >= %s{ust_kosul} AND {BASLIK_VEKTOR} @@ %s::tsquery "
            "ORDER BY abs(haber_id - %s) LIMIT %s)")
        parametre += [alt, *ust_param, _tsquery(hafif), kimlik, sinir]
    if agir:
        suzgec = " OR ".join(["strpos(baslik, %s) > 0"] * len(agir))
        kelime = [" " + " ".join(t) for t in agir]
        parcalar.append(
            "(SELECT haber_id FROM icerik_haberarama "
            f"WHERE haber_id <= %s AND haber_id >= %s AND ({suzgec}) "
            "ORDER BY haber_id DESC LIMIT %s)")
        parametre += [kimlik, alt, *kelime, sinir // 2 + haric_adet]
        parcalar.append(
            "(SELECT haber_id FROM icerik_haberarama "
            f"WHERE haber_id > %s{ust_kosul} AND ({suzgec}) "
            "ORDER BY haber_id LIMIT %s)")
        parametre += [kimlik, *ust_param, *kelime, sinir // 2 + haric_adet]
    return " UNION ALL ".join(parcalar), parametre


def _adaylar(haber: Haber, terimler, bas, son, haric) -> list[tuple]:
    """Pencere içinde başlığı çapalardan biriyle kelime başında eşleşen
    yayındaki haberler: `(id, baslik, yayin_zamani)`, en çok EN_COK_ADAY."""
    taban = (Haber.yayindakiler().order_by()
             .filter(yayin_zamani__range=(bas, son))
             .exclude(pk__in=haric))
    if connection.vendor == "postgresql":
        aralik = kimlik_araligi(bas, son)
        if aralik is None:
            return []
        ic, parametre = _pg_aday_sorgusu(haber.pk, terimler, aralik, len(haric))
        satirlar = list(taban.filter(pk__in=RawSQL(ic, parametre))
                        .values_list("id", "baslik", "yayin_zamani"))
    else:
        suzgec = Q()
        for t in terimler:
            suzgec |= Q(arama__baslik__contains=" " + " ".join(t))
        satirlar = list(taban.filter(suzgec).order_by("-yayin_zamani", "-id")
                        .values_list("id", "baslik", "yayin_zamani")[:EN_COK_ADAY * 2])
    # Makaleye zamanca en yakın EN_COK_ADAY aday — iki motorda aynı kural.
    satirlar.sort(key=lambda s: (abs(s[2] - haber.yayin_zamani), s[0]))
    return satirlar[:EN_COK_ADAY]


def bul(haber: Haber, adet: int = 6, haric=()) -> list[Haber]:
    """`haber`e başlıkça en yakın `adet` yayındaki haber; `haric` kimlikleri
    (ör. konu akışında zaten görünenler) atlanır."""
    haric = set(haric) | {haber.pk}
    anahtar = f"ilgili:{haber.pk}:{adet}:{','.join(map(str, sorted(haric)))}"
    secilen = cache.get(anahtar)
    if secilen is not None:
        return _nesneler(secilen)
    capalar = _capalar(haber.baslik)[:EN_COK_CAPA]
    terimler = _terimler(capalar)
    secilen = []

    if terimler and haber.yayin_zamani:
        bas = haber.yayin_zamani - timedelta(days=PENCERE_GUN)
        son = haber.yayin_zamani + timedelta(days=PENCERE_GUN)
        adaylar = _adaylar(haber, terimler, bas, son, haric)
        kendi = _kokler(haber.baslik)
        capa_kumesi = set(capalar) | {k for k in kendi if "_" in k}
        puanli = []
        for kimlik, baslik, zaman in adaylar:
            onun = _kokler(baslik)
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


@lru_cache(maxsize=20_000)
def _kokler(baslik: str) -> frozenset[str]:
    """Başlığın kökleri + ikili adları. Süreç içi bellekli: aday puanlamanın
    asıl Python bedeli bu (aday başına ~0,06 ms; 400 adayda ~25 ms) ve
    yakın tarihli haberler aynı adayları paylaşıyor — arşiv sırayla
    gezildiğinde (site haritası, tarayıcı) adayların çoğu bellekten gelir."""
    parcalar = km.parcala(baslik)
    return frozenset([p.kok for p in parcalar] + [k for k, _ in km.ikililer(parcalar)])


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
