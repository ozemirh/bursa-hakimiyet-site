"""Yavaş sorgu günlüğü — DEBUG'dan bağımsız (19 Ekim 2026).

Django'nun `django.db.backends` günlüğü yalnız `DEBUG=True` iken yazar;
üretimde yavaş sorgu hiç görünmez. Bu modül her yeni veritabanı
bağlantısına bir yürütme sarmalayıcısı takar (`connection.execute_wrappers`)
ve `settings.YAVAS_SORGU_MS` eşiğini aşan sorguyu `bh.yavas_sorgu`
günlüğüne yazar. Günlüğün nereye gittiği `settings.LOGGING`de.

Bedel: sorgu başına iki `perf_counter` çağrısı. Sorgu metni 2.000
karakterde kesilir; parametreler YAZILMAZ (kişisel veri taşıyabilir).

**Toplu yönetim komutlarında varsayılan KAPALI** (Paket L2, 19 Ekim 2026).
`arama_doldur`, `pg_goc`, `goc_al`, `metin_temizle` gibi komutlar bilerek
uzun sorgu çalıştırır (tam tablo taraması, 5.000 satırlık toplu yazım) ve
günlük her birini "yavaş" diye basıyordu — PG göçünde 109 satır gürültü,
komutun kendi raporunu boğuyordu. Komut sürecinde eşik
`settings.YAVAS_SORGU_KOMUT_MS`tir (`BH_YAVAS_SORGU_KOMUT`, varsayılan 0 =
sarmalayıcı hiç takılmaz). Sunucu (`runserver`, gunicorn) ve `test`
komut sayılmaz; onlarda `YAVAS_SORGU_MS` geçerli.
"""

from __future__ import annotations

import logging
import os
import sys
import time

from django.conf import settings
from django.db.backends.signals import connection_created

gunluk = logging.getLogger("bh.yavas_sorgu")

#: Komut olsa da istek sunan ya da sözleşmesi bu günlüğe bağlı olanlar.
SUNUCU_KOMUTLARI = frozenset({"runserver", "test"})
_YONETICILER = frozenset({"manage.py", "django-admin", "django-admin.py", "__main__.py"})


def komut_adi(argv: list[str] | None = None) -> str | None:
    """Süreç bir yönetim komutuysa adı (`arama_doldur`); değilse None."""
    argv = sys.argv if argv is None else argv
    if len(argv) > 1 and os.path.basename(argv[0]) in _YONETICILER:
        return argv[1]
    return None


def toplu_komut_mu(argv: list[str] | None = None) -> bool:
    komut = komut_adi(argv)
    return komut is not None and komut not in SUNUCU_KOMUTLARI


_TOPLU = toplu_komut_mu()


def esik_ms() -> int:
    """Bu süreçteki eşik (ms). 0 = günlük kapalı."""
    if _TOPLU:
        return int(getattr(settings, "YAVAS_SORGU_KOMUT_MS", 0))
    return int(getattr(settings, "YAVAS_SORGU_MS", 200))


def sarmalayici(execute, sql, params, many, context):
    bas = time.perf_counter()
    try:
        return execute(sql, params, many, context)
    finally:
        ms = (time.perf_counter() - bas) * 1000
        esik = esik_ms()
        if (esik > 0 or not _TOPLU) and ms >= esik:
            gunluk.warning("%.0f ms | %s", ms, str(sql)[:2000])


def _tak(sender, connection, **kwargs):
    if _TOPLU and esik_ms() <= 0:
        return
    if sarmalayici not in connection.execute_wrappers:
        connection.execute_wrappers.append(sarmalayici)


def bagla() -> None:
    connection_created.connect(_tak, dispatch_uid="bh-yavas-sorgu")
