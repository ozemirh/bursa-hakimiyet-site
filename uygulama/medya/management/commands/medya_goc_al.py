"""Arşivden medya göçü — yazar · köşe yazısı · foto galeri · video.

`icerik.goc_al` haber ailesini alıyor; bu komut kalan **dört aileyi** alır.
Kaynak klasörler arşiv kökünün altında ve aile başına ayrı:

    <kök>/veri-yazar/<YIL-AY>/<id>.json
    <kök>/veri-kose/<YIL-AY>/<id>.json
    <kök>/veri-galeri/<YIL-AY>/<id>.json
    <kök>/veri-video/<YIL-AY>/<id>.json

Tasarım kararları — hepsi `goc_al` ile aynı gerekçelere dayanıyor:

- **Kimlik korunur.** `id` doğrudan yazılır; kimlik adresin parçası.
- **Slug adresten çıkarılır**, başlıktan üretilmez.
- **Yeniden çalıştırılabilir.** Tarama sürerken defalarca koşacak; var olan
  kaydı günceller, kopya üretmez.
- **Tanınmayan kategori kaydı düşürmez.** Ölçüm (27 Ağustos 2026): taranan
  3.660 galerinin 998'i `haber-213` dilimindeydi ve taksonomide 213 diye bir
  foto kimliği yok. Ham dilim saklanır, adres yaşar, taksonomi bağı boş kalır.
  Komut bunları **sayar ve raporlar** ki karar ölçüyle verilsin.
- **Yazarı olmayan köşe yazısı düşmez.** Yazar sayfası henüz taranmamışsa
  adres diliminden geçici yazar kaydı açılır (`sayfasi_tarandi=False`).

Kullanım:
    python manage.py medya_goc_al
    python manage.py medya_goc_al --aile galeri --sinirla 500 --kuru
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from medya.ayikla import adresten_slug_kimlik, dilim_ayir, sure_saniyeye, zaman
from medya.models import FotoGaleri, KoseYazisi, Video, Yazar
from taksonomi.models import Kategori, KategoriTur

# Sıra bağlayıcı: yazarlar önce gelirse köşe yazıları geçici kayıt açmak
# yerine gerçek yazara bağlanır.
AILELER = ["yazar", "kose", "galeri", "video"]

VARSAYILAN_KOK = Path(getattr(settings, "ARSIV_KOK", "D:/bursa-hakimiyet-arsiv"))


def _kategori_haritasi(tur: str) -> dict[int, Kategori]:
    return {
        satir.eski_id: satir.kategori
        for satir in KategoriTur.objects.filter(tur=tur).select_related("kategori")
    }


def _ad_haritasi() -> dict[str, Kategori]:
    """Kategori ADINDAN kategori.

    Köşe yazısında kategori bir adres dilimi değil, JSON-LD `articleSection`
    alanıdır. ÖLÇÜM (27 Ağustos 2026): köşe sayfalarında bu alan 1.500 örneğin
    hepsinde **boş**, yani bugün eşleşme olmuyor ve `kategori` boş kalıyor.
    Eşleme yine de duruyor: panelden girilecek yazılarda alan dolacak ve
    haber tarafında (3.000 örnek) değerler kategori adlarıyla birebir tutuyor.
    """
    return {k.ad.casefold(): k for k in Kategori.objects.all()}


class Command(BaseCommand):
    help = "Kazınan yazar, köşe yazısı, foto galeri ve video arşivini aktarır."

    def add_arguments(self, parser):
        parser.add_argument("--kok", default=str(VARSAYILAN_KOK),
                            help="Arşiv kökü (veri-* klasörlerinin üstü).")
        parser.add_argument("--aile", default="hepsi",
                            choices=[*AILELER, "hepsi"])
        parser.add_argument("--sinirla", type=int, default=None)
        parser.add_argument("--kuru", action="store_true",
                            help="yazmaz, yalnız ne olacağını sayar")
        parser.add_argument("--yigin", type=int, default=2000)

    def handle(self, *args, **s):
        kok = Path(s["kok"])
        aileler = AILELER if s["aile"] == "hepsi" else [s["aile"]]

        y = self.stdout.write
        y("")
        y(f"Arşiv kökü : {kok}")

        toplam = Counter()
        for aile in aileler:
            klasor = kok / f"veri-{aile}"
            if not klasor.exists():
                y(self.style.WARNING(
                    f"  {aile:8} veri-{aile}/ yok — bu aile henüz taranmadı."))
                continue
            sayac = getattr(self, f"_{aile}")(klasor, s)
            self._rapor(aile, sayac)
            toplam.update(sayac)

        y("")
        if s["kuru"]:
            y(self.style.WARNING("KURU ÇALIŞMA — hiçbir şey yazılmadı."))
        else:
            y(self.style.SUCCESS(
                f"Veritabanında yazar {Yazar.objects.count()} · "
                f"köşe yazısı {KoseYazisi.objects.count()} · "
                f"galeri {FotoGaleri.objects.count()} · "
                f"video {Video.objects.count()}"))

    # -- ortak yardımcılar --------------------------------------------------

    def _dosyalar(self, klasor: Path, s) -> list[Path]:
        dosyalar = sorted(klasor.glob("*/*.json"))
        return dosyalar[: s["sinirla"]] if s["sinirla"] else dosyalar

    def _oku(self, yol: Path, sayac: Counter):
        try:
            return json.loads(yol.read_text(encoding="utf-8"))
        except Exception:
            sayac["okunamadi"] += 1
            return None

    def _rapor(self, aile: str, sayac: Counter) -> None:
        y = self.stdout.write
        y(f"  {aile}")
        for anahtar in ("dosya", "alindi", "yerel gorselli", "gorselsiz",
                        "kategorisiz", "gecici yazar", "kimlik cozulemedi",
                        "yayin zamani yok", "okunamadi"):
            if sayac.get(anahtar):
                y(f"    {anahtar:22} {sayac[anahtar]:>8,}".replace(",", "."))

    def _yaz(self, model, yigin: list, alanlar: list[str], s) -> None:
        """Yığını yazar. `update_conflicts` sayesinde komut tekrar koşabilir:
        var olan kimlik güncellenir, ikinci kayıt açılmaz."""
        if not yigin or s["kuru"]:
            yigin.clear()
            return
        with transaction.atomic():
            model.objects.bulk_create(
                yigin, batch_size=1000, update_conflicts=True,
                update_fields=alanlar, unique_fields=["id"])
        yigin.clear()

    # -- yazar --------------------------------------------------------------

    def _yazar(self, klasor: Path, s) -> Counter:
        sayac = Counter()
        for yol in self._dosyalar(klasor, s):
            sayac["dosya"] += 1
            d = self._oku(yol, sayac)
            if d is None:
                continue

            slug, kimlik = dilim_ayir(d.get("yazar_dilimi") or "")
            if kimlik is None:
                slug, kimlik = adresten_slug_kimlik(d.get("url") or "")
            if kimlik is None:
                sayac["kimlik cozulemedi"] += 1
                continue

            yerel = d.get("yerel_gorseller") or []
            alanlar = {
                "slug": slug[:120],
                "ad": (d.get("ad") or "").strip()[:120] or slug,
                "sayfasi_tarandi": True,
                "gorsel_url": (d.get("gorsel_url") or "")[:600],
                "gorsel_var": bool(yerel),
                "gorsel_dosya": (yerel[0] if yerel else "")[:300],
                "eski_url": (d.get("url") or "")[:600],
            }
            sayac["alindi"] += 1
            sayac["yerel gorselli" if yerel else "gorselsiz"] += 1
            if not s["kuru"]:
                Yazar.objects.update_or_create(pk=kimlik, defaults=alanlar)
        return sayac

    # -- köşe yazısı --------------------------------------------------------

    def _kose(self, klasor: Path, s) -> Counter:
        sayac = Counter()
        ad_haritasi = _ad_haritasi()
        bilinen_yazar = set(Yazar.objects.values_list("pk", flat=True))
        yigin: list[KoseYazisi] = []
        alanlar = ["slug", "baslik", "spot", "govde", "yazar", "kategori",
                   "yayin_zamani", "guncelleme_zamani", "gorsel_url", "gorsel_alt",
                   "gorsel_var", "gorsel_dosya", "kelime_sayisi", "eski_url",
                   "goc_guveni"]

        for yol in self._dosyalar(klasor, s):
            sayac["dosya"] += 1
            d = self._oku(yol, sayac)
            if d is None:
                continue

            url = d.get("url") or ""
            slug, kimlik = adresten_slug_kimlik(url)
            if kimlik is None:
                sayac["kimlik cozulemedi"] += 1
                continue

            # Yazar dilimi arşivde iki alandan gelebiliyor: `yazar_dilimi`
            # (köşe ayıklayıcısının koyduğu) ve `kategori` (haber ayıklayıcısı
            # üst dilimi oraya yazıyor). İkisi de aynı değeri taşır.
            dilim = d.get("yazar_dilimi") or d.get("kategori") or ""
            y_slug, y_kimlik = dilim_ayir(dilim)
            if y_kimlik is None:
                sayac["kimlik cozulemedi"] += 1
                continue

            yerel = d.get("yerel_gorseller") or []

            if y_kimlik not in bilinen_yazar:
                # Yazar sayfası henüz taranmadı; adresin kurulabilmesi için
                # geçici kayıt açılır. Yazının künyesindeki ad kullanılır.
                #
                # Portre de buradan gelir: köşe sayfasının og:image'ı yazının
                # fotoğrafı değil **yazarın portresidir** (ölçüldü: gorsel_alt
                # alanı yazarın adını taşıyor). Yazar sayfası taranamamış 17
                # yazarın vesikası ancak böyle doluyor.
                sayac["gecici yazar"] += 1
                if not s["kuru"]:
                    # `get_or_create`, `update_or_create` değil: taranmış bir
                    # yazar kaydının künyesini yazının verisiyle ezmemeli.
                    Yazar.objects.get_or_create(
                        pk=y_kimlik,
                        defaults={
                            "slug": y_slug[:120],
                            "ad": (d.get("yazar") or "").strip()[:120] or y_slug,
                            "sayfasi_tarandi": False,
                            "gorsel_url": (d.get("gorsel_url") or "")[:600],
                            "gorsel_var": bool(yerel),
                            "gorsel_dosya": (yerel[0] if yerel else "")[:300],
                        },
                    )
                bilinen_yazar.add(y_kimlik)
            zaman_ = zaman(d.get("yayin_tarihi") or "")
            if zaman_ is None:
                sayac["yayin zamani yok"] += 1

            yigin.append(KoseYazisi(
                id=kimlik,
                slug=slug[:220],
                baslik=(d.get("baslik") or "")[:300],
                spot=d.get("spot") or "",
                govde=d.get("govde_html") or "",
                yazar_id=y_kimlik,
                kategori=ad_haritasi.get((d.get("kategori_etiketi") or "").casefold()),
                durum=KoseYazisi.DURUM_AKTIF,
                yayin_zamani=zaman_,
                guncelleme_zamani=zaman(d.get("guncelleme_tarihi") or ""),
                gorsel_url=(d.get("gorsel_url") or "")[:600],
                gorsel_alt=(d.get("gorsel_alt") or "")[:300],
                gorsel_var=bool(yerel),
                gorsel_dosya=(yerel[0] if yerel else "")[:300],
                kelime_sayisi=int(d.get("kelime_sayisi") or 0),
                eski_url=url[:600],
                goc_guveni=(d.get("ayiklama_guveni") or "")[:12],
            ))
            sayac["alindi"] += 1
            sayac["yerel gorselli" if yerel else "gorselsiz"] += 1
            if len(yigin) >= s["yigin"]:
                self._yaz(KoseYazisi, yigin, alanlar, s)

        self._yaz(KoseYazisi, yigin, alanlar, s)
        return sayac

    # -- foto galeri --------------------------------------------------------

    def _galeri(self, klasor: Path, s) -> Counter:
        harita = _kategori_haritasi(Kategori.TUR_FOTO)
        sayac = Counter()
        yigin: list[FotoGaleri] = []
        alanlar = ["slug", "baslik", "spot", "kategori", "kategori_dilimi",
                   "yayin_zamani", "gorsel_url", "gorsel_alt", "gorsel_var",
                   "gorsel_dosya", "kareler_eksik", "kareler_notu", "eski_url"]

        for yol in self._dosyalar(klasor, s):
            sayac["dosya"] += 1
            d = self._oku(yol, sayac)
            if d is None:
                continue

            url = d.get("url") or ""
            slug, kimlik = adresten_slug_kimlik(url)
            if kimlik is None:
                sayac["kimlik cozulemedi"] += 1
                continue

            dilim = (d.get("kategori_dilimi") or "").strip()
            _, kat_id = dilim_ayir(dilim)
            kategori = harita.get(kat_id) if kat_id is not None else None
            if kategori is None:
                sayac["kategorisiz"] += 1

            yerel = d.get("yerel_gorseller") or []
            zaman_ = zaman(d.get("yayin_tarihi") or "")
            if zaman_ is None:
                sayac["yayin zamani yok"] += 1

            yigin.append(FotoGaleri(
                id=kimlik,
                slug=slug[:220],
                baslik=(d.get("baslik") or "")[:300],
                spot=d.get("spot") or "",
                kategori=kategori,
                kategori_dilimi=dilim[:120],
                durum=FotoGaleri.DURUM_AKTIF,
                yayin_zamani=zaman_,
                gorsel_url=(d.get("gorsel_url") or "")[:600],
                gorsel_alt=(d.get("gorsel_alt") or "")[:300],
                gorsel_var=bool(yerel),
                gorsel_dosya=(yerel[0] if yerel else "")[:300],
                kareler_eksik=bool(d.get("kareler_eksik", True)),
                kareler_notu=(d.get("kareler_notu") or "")[:300],
                eski_url=url[:600],
            ))
            sayac["alindi"] += 1
            sayac["yerel gorselli" if yerel else "gorselsiz"] += 1
            if len(yigin) >= s["yigin"]:
                self._yaz(FotoGaleri, yigin, alanlar, s)

        self._yaz(FotoGaleri, yigin, alanlar, s)
        return sayac

    # -- video --------------------------------------------------------------

    def _video(self, klasor: Path, s) -> Counter:
        harita = _kategori_haritasi(Kategori.TUR_VIDEO)
        sayac = Counter()
        yigin: list[Video] = []
        alanlar = ["slug", "baslik", "spot", "kategori", "kategori_dilimi",
                   "yayin_zamani", "gorsel_url", "gorsel_alt", "gorsel_var",
                   "gorsel_dosya", "video_url", "gomulu_url", "sure",
                   "sure_saniye", "eski_url"]

        for yol in self._dosyalar(klasor, s):
            sayac["dosya"] += 1
            d = self._oku(yol, sayac)
            if d is None:
                continue

            url = d.get("url") or ""
            slug, kimlik = adresten_slug_kimlik(url)
            if kimlik is None:
                sayac["kimlik cozulemedi"] += 1
                continue

            dilim = (d.get("kategori_dilimi") or "").strip()
            _, kat_id = dilim_ayir(dilim)
            kategori = harita.get(kat_id) if kat_id is not None else None
            if kategori is None:
                sayac["kategorisiz"] += 1

            yerel = d.get("yerel_gorseller") or []
            zaman_ = zaman(d.get("yayin_tarihi") or "")
            if zaman_ is None:
                sayac["yayin zamani yok"] += 1

            ham_sure = d.get("sure") or ""
            yigin.append(Video(
                id=kimlik,
                slug=slug[:220],
                baslik=(d.get("baslik") or "")[:300],
                spot=d.get("spot") or "",
                kategori=kategori,
                kategori_dilimi=dilim[:120],
                durum=Video.DURUM_AKTIF,
                yayin_zamani=zaman_,
                gorsel_url=(d.get("gorsel_url") or "")[:600],
                gorsel_alt=(d.get("gorsel_alt") or "")[:300],
                gorsel_var=bool(yerel),
                gorsel_dosya=(yerel[0] if yerel else "")[:300],
                video_url=(d.get("video_url") or "")[:600],
                gomulu_url=(d.get("gomulu_url") or "")[:600],
                sure=str(ham_sure)[:40],
                sure_saniye=sure_saniyeye(str(ham_sure)),
                eski_url=url[:600],
            ))
            sayac["alindi"] += 1
            sayac["yerel gorselli" if yerel else "gorselsiz"] += 1
            if len(yigin) >= s["yigin"]:
                self._yaz(Video, yigin, alanlar, s)

        self._yaz(Video, yigin, alanlar, s)
        return sayac
