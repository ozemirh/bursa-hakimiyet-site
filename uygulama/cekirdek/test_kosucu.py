"""Test koşucusu — her testten önce önbellekleri ve süreç belleğini temizler.

19 Ekim 2026 (başarım paketi): menü, künye ve arşiv sayıları modül
değişkeninden `django.core.cache`e taşındı. Eskiden her test sınıfı
`baglam._menu_bellek = None` gibi satırlarla kendi değişkenini sıfırlıyordu;
paylaşılan önbellekte bu düzen kırılgan olurdu — bir testin ısıttığı değer
öbür testin veritabanında olmayan kayıtları gösterir. Temizlik tek yerde,
Django'nun her test için çağırdığı `_pre_setup` kancasında yapılır.

19 Ekim 2026 (test altyapısı paketi, K) — üç ek:

1. **Bütün LocMem depoları** temizlenir, yalnız o an `caches`'e bağlı
   olanlar değil. `override_settings(CACHES=...)` ile açılan önbellek
   (ör. `tests_basarim.SAYFA_ACIK`, LOCATION "bh-t-sayfa") test bittikten
   sonra `caches`'ten düşer ama LocMem'in deposu modül düzeyinde bir
   sözlüktür ve KALIR; sıradaki aynı adlı önbellek önceki testin
   değerlerini görür. Bu, sıraya bağlı kararsızlığın bir kaynağıydı.
2. **`icerik.canli._bellek`** (canlı veri dosyalarının 30 sn'lik süreç
   belleği) temizlenir: `override_settings(CANLI_VERI_KOK=...)` kuran bir
   testin okuduğu değer sonraki teste sızmasın. Ad değişirse sessizce
   atlanır (paket J bu modülü değiştiriyor).
3. **Paralel koşu** (`--parallel`): Windows'ta işçi süreçleri `spawn` ile
   doğar ve Django onlarda koşucunun `setup_test_environment`ini DEĞİL
   modül düzeyindeki işlevi çağırır; temizlik kancası işçiye ulaşmazdı.
   `ParalelTakim.process_setup` kancayı her işçide yeniden takar.

Gerçek dosya kökleri (canlı veri, arşiv, türev) test ayarında depodaki
fixture'a ve var olmayan geçici yola gider: `settings.py`nin sonundaki
"test ortamı" bloğu.
"""

from django.core.cache import caches
from django.test import SimpleTestCase
from django.test.runner import DiscoverRunner, ParallelTestSuite

_ozgun_pre_setup = SimpleTestCase.__dict__["_pre_setup"].__func__


def _onbellekleri_temizle():
    for onbellek in caches.all(initialized_only=True):
        onbellek.clear()
    # Adı ne olursa olsun bütün LocMem depoları (bkz. modül başı, madde 1).
    from django.core.cache.backends import locmem
    for depo in (locmem._caches, locmem._expire_info):
        for icerik in depo.values():
            icerik.clear()
    # Süreç içi eşlemeler (kategori slug'ı) da sıfırlanır.
    from taksonomi import slug_eslemesi
    slug_eslemesi.sifirla()
    from icerik import canli
    bellek = getattr(canli, "_bellek", None)
    if hasattr(bellek, "clear"):
        bellek.clear()


def _pre_setup(cls):
    _onbellekleri_temizle()
    _ozgun_pre_setup(cls)


def _kancayi_tak():
    SimpleTestCase._pre_setup = classmethod(_pre_setup)


def _isci_kur(*_):
    """Paralel işçide (spawn) `django.setup()`tan ÖNCE çağrılır."""
    _kancayi_tak()


class ParalelTakim(ParallelTestSuite):
    process_setup = _isci_kur


class Kosucu(DiscoverRunner):
    parallel_test_suite = ParalelTakim

    def setup_test_environment(self, **kwargs):
        super().setup_test_environment(**kwargs)
        _kancayi_tak()

    def teardown_test_environment(self, **kwargs):
        SimpleTestCase._pre_setup = classmethod(_ozgun_pre_setup)
        super().teardown_test_environment(**kwargs)
        self._yok_kok_denetimi()

    def _yok_kok_denetimi(self):
        """Test ayarındaki "var olmayan" arşiv kökü koşu sonunda hâlâ yok mu?

        Varsa bir test kendi geçici klasörünü kurmadan arşive yazmış demektir;
        sonraki koşuda o dosya "arşivde var" sayılır ve sonuç sıraya bağlanır.
        """
        from django.conf import settings
        kok = getattr(settings, "_TEST_KOK", None)
        if kok is not None and kok.exists():
            dosyalar = [str(p) for p in kok.rglob("*") if p.is_file()][:10]
            self.log(
                f"UYARI: test koşusu var olmaması gereken {kok} altına yazdı: "
                f"{dosyalar or '(boş klasör)'}")
