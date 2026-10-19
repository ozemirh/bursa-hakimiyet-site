"""Okunma kuyruğunu veritabanına boşaltır (19 Ekim 2026, başarım paketi).

    python manage.py okunma_bosalt

Kuyruk dosyaları iki yerden gelir (`icerik/okunma.py`):

* `BH_OKUNMA_YAZIM=komut` düzeninde istek yolu sayımı veritabanına DEĞİL
  kuyruk dosyasına bırakır; veritabanına yazan yalnız bu komuttur.
* Her iki düzende de süreç kapanırken tampondaki sayım kuyruğa bırakılır.

Bütün dosyalar TEK işlemde, çok satırlı tek deyimle yazılır; iki komut aynı
anda çalışırsa dosyayı ilk sahiplenen yazar, sayım iki kez yazılmaz.

**Zamanlanmış görev AÇILMADI** — kullanıcı kararı. `komut` düzeni ancak
bu komut düzenli çalışacaksa seçilmeli; çalışmazsa sayım kuyrukta bekler
ve "en çok okunanlar" güncellenmez.
"""

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import DatabaseError

from icerik import okunma


class Command(BaseCommand):
    help = "Okunma kuyruğunu (ve bu sürecin tamponunu) veritabanına yazar."

    def handle(self, *args, **secenekler):
        bekleyen = len(okunma._kuyruk_dosyalari())
        try:
            yazilan = okunma.kuyrugu_bosalt(ek=okunma._tamponu_al())
        except DatabaseError as hata:
            self.stderr.write(f"Yazılamadı, dosyalar kuyrukta kaldı: {hata}")
            raise SystemExit(1)
        self.stdout.write(
            f"{bekleyen} kuyruk dosyası, {yazilan} kova yazıldı "
            f"(düzen: {getattr(settings, 'OKUNMA_YAZIM', 'istek')}, "
            f"kuyruk: {okunma._kuyruk_koku()}).")
