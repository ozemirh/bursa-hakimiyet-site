"""Yavaş sorgu günlüğü — DEBUG'dan bağımsız (19 Ekim 2026).

Django'nun `django.db.backends` günlüğü yalnız `DEBUG=True` iken yazar;
üretimde yavaş sorgu hiç görünmez. Bu modül her yeni veritabanı
bağlantısına bir yürütme sarmalayıcısı takar (`connection.execute_wrappers`)
ve `settings.YAVAS_SORGU_MS` eşiğini aşan sorguyu `bh.yavas_sorgu`
günlüğüne yazar. Günlüğün nereye gittiği `settings.LOGGING`de.

Bedel: sorgu başına iki `perf_counter` çağrısı. Sorgu metni 2.000
karakterde kesilir; parametreler YAZILMAZ (kişisel veri taşıyabilir).
"""

from __future__ import annotations

import logging
import time

from django.conf import settings
from django.db.backends.signals import connection_created

gunluk = logging.getLogger("bh.yavas_sorgu")


def sarmalayici(execute, sql, params, many, context):
    bas = time.perf_counter()
    try:
        return execute(sql, params, many, context)
    finally:
        ms = (time.perf_counter() - bas) * 1000
        if ms >= getattr(settings, "YAVAS_SORGU_MS", 200):
            gunluk.warning("%.0f ms | %s", ms, str(sql)[:2000])


def _tak(sender, connection, **kwargs):
    if sarmalayici not in connection.execute_wrappers:
        connection.execute_wrappers.append(sarmalayici)


def bagla() -> None:
    connection_created.connect(_tak, dispatch_uid="bh-yavas-sorgu")
