"""Kuyruktaki gönderileri gönderir — zamanlanmış görevin çalıştırdığı komut.

    python manage.py sosyal_gonder            # en çok 20 satır
    python manage.py sosyal_gonder --sinir 5
    python manage.py sosyal_gonder --kuru     # göndermez, yalnız listeler

Panel istek içinde gönderim yapmaz (bkz. `sosyal/kuyruk.py`); "yayına alınca
paylaşılsın" kuralının kendiliğinden işlemesi bu komutun düzenli
çalışmasına bağlıdır. Beş dakikada bir çalıştırmak yeterlidir; komut
çalışmıyorsa satırlar kaybolmaz, kuyrukta bekler ve panelden elle
gönderilebilir.
"""

from django.core.management.base import BaseCommand

from sosyal import kuyruk
from sosyal.models import SosyalGonderi


class Command(BaseCommand):
    help = "Sosyal medya kuyruğundaki bekleyen gönderileri gönderir."

    def add_arguments(self, parser):
        parser.add_argument("--sinir", type=int, default=20,
                            help="Bu çalıştırmada en çok kaç gönderi.")
        parser.add_argument("--kuru", action="store_true",
                            help="göndermez, yalnız ne gideceğini yazar")

    def handle(self, *args, **secenekler):
        sinir = secenekler["sinir"]
        if secenekler["kuru"]:
            return self._listele(sinir)
        ozet = kuyruk.bekleyenleri_gonder(sinir=sinir)
        self.stdout.write(kuyruk.ozet_cumlesi(ozet))

    def _listele(self, sinir):
        sorgu = (SosyalGonderi.bekleyenler()
                 .select_related("haber", "haber__kategori", "hesap")
                 .order_by("olusma_zamani", "id"))
        gidecek = 0
        for gonderi in sorgu:
            if gonderi.gonderilebilir_mi():
                if gidecek < sinir:
                    self.stdout.write(
                        f"gider   {gonderi.hesap.ad} ← [{gonderi.haber_id}] "
                        f"{gonderi.haber.baslik[:60]}")
                gidecek += 1
            else:
                self.stdout.write(
                    f"bekler  {gonderi.hesap.ad} ← [{gonderi.haber_id}] "
                    f"({'haber yayında değil' if not gonderi.haber_yayinda_mi() else 'hesap gönderemiyor'})")
        self.stdout.write(f"Gönderilmeye hazır: {gidecek} "
                          f"(bu çalıştırmada en çok {sinir}).")
