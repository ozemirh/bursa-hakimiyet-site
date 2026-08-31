"""Günün nöbetçi eczane haberini açar ya da tazeler.

31 Ağustos 2026, kullanıcı isteği (URUN-PLANI.md §41). Her sabah bir kez
çalışır; o günün nöbet listesini haber olarak yayımlar.

    python manage.py eczane_haberi
    python manage.py eczane_haberi --kuru           # yazmaz, ne yapacağını söyler
    python manage.py eczane_haberi --gun 2026-08-31
    python manage.py eczane_haberi --kategori saglik

**Aynı gün iki kez çalışırsa ikinci kayıt AÇILMAZ.** Var olan haber
tazelenir — nöbet listesi gün içinde değişebiliyor, adres değişmemeli.
Ölçüt haberin `slug`'ı: gün başına tek slug üretiliyor
(`31-agustos-2026-bursa-nobetci-eczaneler`).

**Boş liste yayımlanmaz.** Dosya yoksa ya da hiç eczane taşımıyorsa komut
yazmadan çıkar. Bayat veri de yayımlanmaz: nöbet günde bir devrediliyor,
bir gün eski liste okuru kapalı eczaneye gönderir. `--bayat-da-yayimla`
bu kapıyı bilerek açar (elle kullanım için).

**Metin buradan çıkmaz.** Başlık, spot ve gövde `icerik/eczane.py`
içindedir; kalıcı sayfa da aynı yerden besleniyor. İki metin iki dosyada
yaşasaydı biri güncellenip öteki unutulurdu.

Çıkış kodu: 0 yazıldı/tazelendi · 1 yayımlanacak veri yok.
"""

from __future__ import annotations

from datetime import date, datetime, time

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify

from icerik import eczane as eczane_metni
from icerik.models import Haber
from taksonomi.models import Etiket, Kategori, Kaynak

# Haberin kategorisi. Nöbetçi eczane bir sağlık hizmeti duyurusu; GÜNDEM
# ve BURSA kategorileri günün haberi için ayrılmış durumda ve günlük
# otomatik kayıt onları doldururdu.
VARSAYILAN_KATEGORI = "saglik"

# Kaynak kaydı: haber dış bir yayından alıntı değil, resmî bir kurumun
# yayımladığı çizelgeden derleniyor. `Kaynak.TUR_DIS_YAYIN` bu yüzden
# doğru eksen — ajans değil.
KAYNAK_ADI = eczane_metni.KAYNAK_ADI


class Command(BaseCommand):
    help = "Günün nöbetçi eczane haberini yayımlar (varsa tazeler)."

    def add_arguments(self, parser):
        parser.add_argument("--kuru", action="store_true",
                            help="yazmaz, yalnız ne olacağını söyler")
        parser.add_argument("--gun", default="",
                            help="YYYY-AA-GG; dosya bu günü taşımıyorsa çıkar")
        parser.add_argument("--kategori", default=VARSAYILAN_KATEGORI,
                            help=f"kategori slug'ı (varsayılan: {VARSAYILAN_KATEGORI})")
        parser.add_argument("--bayat-da-yayimla", action="store_true",
                            help="bayat listeyi de yayımlar (varsayılan: hayır)")

    def handle(self, *args, **s):
        y = self.stdout.write

        istenen = None
        if s["gun"]:
            try:
                istenen = date.fromisoformat(s["gun"])
            except ValueError:
                y(self.style.ERROR(f"Gün çözülemedi: {s['gun']}"))
                return

        panel = eczane_metni.gunun_paketi(istenen)
        if not panel:
            y(self.style.WARNING(
                "Yayımlanacak nöbetçi eczane verisi yok "
                "(dosya okunamadı, boş ya da istenen günü taşımıyor)."))
            raise SystemExit(1)
        if panel["bayat"] and not s["bayat_da_yayimla"]:
            y(self.style.WARNING(
                "Liste bayat (nöbet günde bir devrediliyor); yayımlanmadı. "
                "Yine de istiyorsan --bayat-da-yayimla."))
            raise SystemExit(1)

        paket = eczane_metni.haber_paketi(panel)
        slug = paket["slug"]
        var_olan = Haber.objects.filter(slug=slug).first()

        y(f"Gün: {panel['gun']} · {panel['sayi']} eczane · "
          f"{len(panel['ilceler'])} ilçe")
        y(f"Başlık: {paket['baslik']}")
        y(f"Adres slug'ı: {slug}")
        if s["kuru"]:
            y(self.style.NOTICE(
                "KURU ÇALIŞMA — yazılmadı. "
                + ("Var olan kayıt tazelenecekti: " + str(var_olan.id)
                   if var_olan else "Yeni kayıt açılacaktı.")))
            y(f"Gövde {len(paket['govde'])} karakter, "
              f"{paket['govde'].count('<li>')} eczane satırı.")
            return

        kategori = Kategori.objects.filter(
            turler__tur=Kategori.TUR_HABER, turler__slug=s["kategori"],
            aktif=True).first()
        if not kategori:
            y(self.style.ERROR(f"Kategori bulunamadı: {s['kategori']}"))
            raise SystemExit(1)

        with transaction.atomic():
            haber = self._yaz(var_olan, panel, paket, kategori, slug)

        y(self.style.SUCCESS(
            ("Tazelendi: " if var_olan else "Yayımlandı: ") + haber.get_absolute_url()))

    # -- yazma ------------------------------------------------------------

    def _yaz(self, var_olan, panel, paket, kategori, slug) -> Haber:
        """Kaydı açar ya da günceller.

        Tazelemede **yayın zamanı korunur**: haber o sabah yayımlandı,
        her tazelemede öne çekmek arşiv sırasını bozar ve okura haber
        yeniden yayımlanmış gibi görünür. Güncelleme zamanı ise her
        koşuda ilerler.
        """
        simdi = timezone.now()
        haber = var_olan or Haber(
            id=(Haber.objects.order_by("-id")
                .values_list("id", flat=True).first() or 0) + 1,
            slug=slug,
            yayin_zamani=self._yayin_zamani(panel["gun"], simdi),
        )
        haber.baslik = paket["baslik"]
        haber.spot = paket["spot"]
        haber.govde = paket["govde"]
        haber.seo_baslik = paket["seo_baslik"]
        haber.odak_kelime = paket["odak_kelime"]
        haber.kategori = kategori
        haber.durum = Haber.DURUM_AKTIF
        haber.hazirlik = "hazir"
        # Kaynak türü "Dış yayın": metin gazetenin muhabirinden değil,
        # odanın yayımladığı çizelgeden geliyor. Meta yazar bu türden
        # türetilir (§7) — elle seçilmiş sayılmaz.
        haber.kaynak_turu = Haber.KAYNAK_DIS_YAYIN
        haber.meta_yazar = haber.meta_yazari_turet()
        haber.guncelleme_zamani = simdi
        haber.kelime_sayisi = len(paket["govde"].split())
        # Nöbet listesi ilçe üstü: haber Bursa geneli. İlçe alanı boş
        # bırakılıyor ki ilçe sayfaları günlük eczane kaydıyla dolmasın.
        haber.ilce = None
        haber.save()

        kaynak, _ = Kaynak.objects.get_or_create(
            ad=KAYNAK_ADI, defaults={"tur": Kaynak.TUR_DIS_YAYIN})
        haber.kaynaklar.set([kaynak])
        haber.etiketler.set([
            Etiket.objects.get_or_create(
                ad=ad, defaults={"slug": slugify(ad, allow_unicode=False)})[0]
            for ad in paket["etiketler"]])
        return haber

    @staticmethod
    def _yayin_zamani(gun: date, simdi):
        """Haberin tarihi listenin günüdür, komutun koştuğu an değil.

        Geçmiş bir gün için elle çalıştırıldığında kayıt o günün sabahına
        yazılır; bugün için koşulduğunda şu an kullanılır ki haber
        akışta ileri tarihli görünmesin.
        """
        if gun == timezone.localdate(simdi):
            return simdi
        return timezone.make_aware(datetime.combine(gun, time(8, 0)))
