"""Test koşucusu — her testten önce önbellekleri temizler.

19 Ekim 2026 (başarım paketi): menü, künye ve arşiv sayıları modül
değişkeninden `django.core.cache`e taşındı. Eskiden her test sınıfı
`baglam._menu_bellek = None` gibi satırlarla kendi değişkenini sıfırlıyordu;
paylaşılan önbellekte bu düzen kırılgan olurdu — bir testin ısıttığı değer
öbür testin veritabanında olmayan kayıtları gösterir. Temizlik tek yerde,
Django'nun her test için çağırdığı `_pre_setup` kancasında yapılır.
"""

from django.core.cache import caches
from django.test import SimpleTestCase
from django.test.runner import DiscoverRunner

_ozgun_pre_setup = SimpleTestCase.__dict__["_pre_setup"].__func__


def _onbellekleri_temizle():
    for onbellek in caches.all(initialized_only=True):
        onbellek.clear()
    # Süreç içi eşlemeler (kategori slug'ı) da sıfırlanır.
    from taksonomi import slug_eslemesi
    slug_eslemesi.sifirla()


def _pre_setup(cls):
    _onbellekleri_temizle()
    _ozgun_pre_setup(cls)


class Kosucu(DiscoverRunner):
    def setup_test_environment(self, **kwargs):
        super().setup_test_environment(**kwargs)
        SimpleTestCase._pre_setup = classmethod(_pre_setup)

    def teardown_test_environment(self, **kwargs):
        SimpleTestCase._pre_setup = classmethod(_ozgun_pre_setup)
        super().teardown_test_environment(**kwargs)
