"""Kuyruk — satır açma, kapatma ve gönderme.

Panelin sosyal medyaya bakan tek kapısı burasıdır. Görünümler sağlayıcıyı
doğrudan çağırmaz; hepsi bu modülden geçer ki "gönderildi" damgası tek bir
yerde vurulsun.

## Neden istek içinde gönderilmiyor

Haber kaydeden editörü üç ağ isteği kadar bekletmek kabul edilemezdi:
X yavaşsa kayıt yavaşlar, X düşükse kayıt hata verirmiş gibi görünür.
Bu yüzden kaydetme yalnız **satır açar**; gönderimi ya zamanlanmış görev
(`manage.py sosyal_gonder`) ya da panelin "Şimdi gönder" düğmesi yapar.

## Açık satır ikinci kez açılmaz

Aynı haberi aynı hesapta iki kez paylaşmak, bu aracın yapabileceği en
görünür hatadır. `acik_gonderiler` kontrolü form her kaydedildiğinde
çalışır; veritabanı tarafında da kısıt var (`sosyal_tek_gonderim`).
"""

from django.db import transaction
from django.utils import timezone

from . import metin as metin_kur
from .models import SosyalGonderi, SosyalHesap
from .saglayicilar import SosyalHata

# Satır "açık" sayılıyorsa yenisi açılmaz: ya sırada bekliyor, ya elle
# paylaşılacak, ya da zaten paylaşılmış.
ACIK_DURUMLAR = (SosyalGonderi.BEKLIYOR, SosyalGonderi.HATA,
                 SosyalGonderi.ELLE, SosyalGonderi.GONDERILDI)


def secilebilir_hesaplar(otomatik=True):
    """Haber formunda kutusu çizilecek hesaplar.

    `otomatik=True` YouTube'u eler: orada paylaşılan şey haber değil, ayrıca
    çekilmiş özel video (`saglayicilar/youtube.py`).
    """
    sorgu = SosyalHesap.objects.filter(aktif=True)
    if otomatik:
        kodlar = [h.pk for h in sorgu if h.otomatik_olur]
        return SosyalHesap.objects.filter(pk__in=kodlar)
    return sorgu


def acik_gonderiler(haber):
    return SosyalGonderi.objects.filter(haber=haber, durum__in=ACIK_DURUMLAR)


def _baslangic_durumu(hesap) -> str:
    """Satır hangi durumda doğar.

    Anahtar tam ve platform otomatik ise BEKLIYOR (gönderici alır); değilse
    ELLE — editör metni kopyalayıp kendi paylaşır. Bu ikilik aracın anahtar
    gelmeden de çalışmasını sağlıyor.
    """
    if hesap.otomatik_olur and hesap.kimligi_tam_mi():
        return SosyalGonderi.BEKLIYOR
    return SosyalGonderi.ELLE


@transaction.atomic
def kuyruga_al(haber, hesaplar, kullanici=None,
               kaynak=SosyalGonderi.OTOMATIK) -> list:
    """Seçilen hesaplar için satır açar; açık satırı olanı atlar."""
    varolan = set(acik_gonderiler(haber).values_list("hesap_id", flat=True))
    acilan = []
    for hesap in hesaplar:
        if hesap.pk in varolan:
            continue
        acilan.append(SosyalGonderi.objects.create(
            haber=haber,
            hesap=hesap,
            metin=metin_kur.gonderi_metni(haber, hesap),
            gorsel_adres=metin_kur.gorsel_adresi(haber),
            durum=_baslangic_durumu(hesap),
            kaynak=kaynak,
            olusturan=kullanici if (kullanici and kullanici.is_authenticated)
            else None,
        ))
    return acilan


@transaction.atomic
def kuyruktan_cikar(haber, hesaplar) -> int:
    """Kutusu kaldırılan hesapların satırlarını İPTAL eder.

    Satır silinmiyor: gönderilmiş bir paylaşımın izi kalmalı ve "kim ne
    zaman vazgeçti" sorusunun cevabı da kayıtta durmalı. Gönderilmiş satıra
    dokunulmaz — gerçekte paylaşılmış bir gönderiyi iptal saymak yalan olur.

    **Yalnız formun kendi açtığı satırlar iptal edilir** (`kaynak` otomatik).
    Editörün elle açtığı satır — YouTube videosu böyle giriyor — haber formu
    kaydedildi diye kapanmaz; onu açan kişi kapatır.
    """
    kimlikler = [h.pk for h in hesaplar]
    if not kimlikler:
        return 0
    return SosyalGonderi.objects.filter(
        haber=haber, hesap_id__in=kimlikler,
        kaynak=SosyalGonderi.OTOMATIK,
        durum__in=(SosyalGonderi.BEKLIYOR, SosyalGonderi.HATA,
                   SosyalGonderi.ELLE),
    ).update(durum=SosyalGonderi.IPTAL)


def haber_kaydedildi(haber, secilen, kullanici=None) -> dict:
    """Haber formu kaydedildiğinde kuyruğu seçimle eşitler."""
    secilen = list(secilen or [])
    secili_kimlikler = {h.pk for h in secilen}
    cikarilacak = [h for h in secilebilir_hesaplar()
                   if h.pk not in secili_kimlikler]
    iptal = kuyruktan_cikar(haber, cikarilacak)
    acilan = kuyruga_al(haber, secilen, kullanici)
    return {"acilan": acilan, "iptal": iptal}


def metni_tazele(gonderi) -> None:
    """Metni haberin bugünkü hâlinden yeniden kurar.

    Yalnız gönderilmemiş satırda anlamlı; gönderilmiş gönderinin metni
    olduğu gibi kalır — dışarıda ne yayımlandıysa kayıtta o yazmalı.
    """
    if gonderi.durum in SosyalGonderi.KAPALI_DURUMLAR:
        return
    gonderi.metin = metin_kur.gonderi_metni(gonderi.haber, gonderi.hesap)
    gonderi.gorsel_adres = metin_kur.gorsel_adresi(gonderi.haber)
    gonderi.save(update_fields=["metin", "gorsel_adres"])


def gonder(gonderi) -> bool:
    """Tek satırı gönderir. Sonucu satıra ve hesaba yazar."""
    hesap = gonderi.hesap
    if not gonderi.metin:
        metni_tazele(gonderi)

    gonderi.deneme += 1
    try:
        sonuc = hesap.saglayici().gonder(hesap, gonderi)
    except SosyalHata as hata:
        sonuc = None
        gonderi.durum = SosyalGonderi.HATA
        gonderi.hata_metni = str(hata)[:500]
    except Exception as hata:              # sağlayıcıdaki beklenmedik çökme
        sonuc = None
        gonderi.durum = SosyalGonderi.HATA
        gonderi.hata_metni = f"Beklenmeyen hata: {hata}"[:500]

    if sonuc is not None:
        if sonuc.basarili:
            gonderi.durum = SosyalGonderi.GONDERILDI
            gonderi.gonderim_zamani = timezone.now()
            gonderi.dis_kimlik = sonuc.dis_kimlik
            gonderi.dis_adres = sonuc.dis_adres
            gonderi.hata_metni = ""
        else:
            gonderi.durum = SosyalGonderi.HATA
            gonderi.hata_metni = (sonuc.hata or "Bilinmeyen hata")[:500]

    gonderi.save(update_fields=["durum", "deneme", "gonderim_zamani",
                                "dis_kimlik", "dis_adres", "hata_metni"])
    hesap.son_hata = "" if gonderi.durum == SosyalGonderi.GONDERILDI \
        else gonderi.hata_metni[:300]
    if gonderi.durum == SosyalGonderi.GONDERILDI:
        hesap.son_gonderim = gonderi.gonderim_zamani
    hesap.save(update_fields=["son_hata", "son_gonderim"])
    return gonderi.durum == SosyalGonderi.GONDERILDI


def bekleyenleri_gonder(sinir: int = 20) -> dict:
    """Gönderilebilir satırları sırayla işler.

    Haberi henüz yayında olmayan satırlar **atlanır ve kuyrukta kalır**;
    sayıları özet içinde bildirilir ki "neden gitmedi" sorusunun cevabı
    ekranda olsun.
    """
    ozet = {"gonderildi": 0, "hata": 0, "yayin_bekliyor": 0, "elle": 0}
    sorgu = (SosyalGonderi.bekleyenler()
             .select_related("haber", "haber__kategori", "hesap")
             .order_by("olusma_zamani", "id"))
    islenen = 0
    for gonderi in sorgu:
        if islenen >= sinir:
            break
        hesap = gonderi.hesap
        if not (hesap.aktif and hesap.otomatik_olur and hesap.kimligi_tam_mi()):
            ozet["elle"] += 1
            continue
        if not gonderi.haber_yayinda_mi():
            ozet["yayin_bekliyor"] += 1
            continue
        islenen += 1
        ozet["gonderildi" if gonder(gonderi) else "hata"] += 1
    return ozet


def ozet_cumlesi(ozet: dict) -> str:
    parcalar = [f"{ozet['gonderildi']} gönderi paylaşıldı"]
    if ozet["hata"]:
        parcalar.append(f"{ozet['hata']} tanesi hata verdi")
    if ozet["yayin_bekliyor"]:
        parcalar.append(f"{ozet['yayin_bekliyor']} satır haberin yayınını "
                        "bekliyor")
    if ozet["elle"]:
        parcalar.append(f"{ozet['elle']} satır elle paylaşım "
                        "(hesabın anahtarı yok ya da kapalı)")
    return ", ".join(parcalar) + "."
