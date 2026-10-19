"""Planlayıcı istatistiklerini tazeler — iki motorda da (19 Ekim 2026).

`ANALYZE` göç, toplu onarım ve migration sonrası standart adımdır
(URUN-PLANI.md §22: bayat istatistikle ilçe sayfası 26 → 745 ms).

- **SQLite:** düz `ANALYZE` (`sqlite_stat1` dolar).
- **PostgreSQL:** autovacuum zamanla kendisi yapar ama toplu yazımdan hemen
  sonra beklemek planı dakikalarca bayat bırakır. Düz `ANALYZE` süper
  kullanıcı olmayan uygulama kullanıcısında sistem tabloları için uyarı
  basar; bu yüzden yalnız Django'nun tabloları sayılır.
"""

from __future__ import annotations

import time

from django.db import connection


def tazele(tablolar: list[str] | None = None) -> float:
    """İstatistikleri tazeler, süreyi saniye olarak döndürür."""
    t0 = time.perf_counter()
    with connection.cursor() as imlec:
        if connection.vendor == "postgresql":
            adlar = tablolar or sorted(connection.introspection.django_table_names(
                only_existing=True, include_views=False))
            qn = connection.ops.quote_name
            for ad in adlar:
                imlec.execute(f"ANALYZE {qn(ad)}")
        else:
            imlec.execute("ANALYZE")
    return time.perf_counter() - t0
