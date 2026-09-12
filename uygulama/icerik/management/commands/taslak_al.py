# -*- coding: utf-8 -*-
"""Bir haber adresinden panele taslak açar (komut satırı yolu).

Panelin `Adresten Taslak` ekranıyla aynı köprüyü kullanır (`yz_kopru`);
fark, uzun süren model yollarını tarayıcıyı bekletmeden çalıştırabilmek.

    python manage.py taslak_al "https://…" --saglayici kural --kullanici emir

Taslak **pasif** doğar; yayına alma paneldeki haber formundan olur.
"""

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError

from ...yz_kopru import SAGLAYICI_KODLARI, YzHatasi, taslak_al


class Command(BaseCommand):
    help = "Haber adresinden taslak açar (yayınlamaz)."

    def add_arguments(self, ayrist):
        ayrist.add_argument("adres", help="Haberin tam adresi")
        ayrist.add_argument("--saglayici", default="kural",
                            choices=SAGLAYICI_KODLARI,
                            help="kural (anlık) · cli · skill")
        ayrist.add_argument("--kullanici", default="",
                            help="Taslağı açan kullanıcı adı. Boşsa ilk "
                                 "yönetici hesabı kullanılır.")

    def handle(self, *args, **secim):
        kullanici = self._kullanici(secim["kullanici"])
        try:
            haber, paket, notlar = taslak_al(
                secim["adres"], kullanici, secim["saglayici"])
        except YzHatasi as e:
            raise CommandError(str(e)) from e

        kaynak = paket.get("kaynak") or {}
        self.stdout.write(self.style.SUCCESS(
            "Taslak açıldı: #%s" % haber.pk))
        self.stdout.write("  kaynak      : %s (%s kelime, güven: %s)" % (
            kaynak.get("kaynak_adi") or "?", kaynak.get("kelime_sayisi") or 0,
            kaynak.get("ayiklama_guveni") or "?"))
        self.stdout.write("  başlık      : %s" % (haber.baslik or "—"))
        self.stdout.write("  kategori    : %s%s" % (
            haber.kategori.ad,
            " / %s" % haber.ilce.ad if haber.ilce else ""))
        self.stdout.write("  gövde       : %s kelime" % haber.kelime_sayisi)
        self.stdout.write("  durum       : %s · %s (yayında değil)" % (
            haber.get_durum_display(), haber.get_hazirlik_display()))
        for satir in notlar:
            self.stdout.write("  · %s" % satir)
        self.stdout.write("  panel       : /panel/yz-taslak/%s" % haber.pk)

    def _kullanici(self, ad: str) -> User:
        if ad:
            kullanici = User.objects.filter(username=ad).first()
            if kullanici is None:
                raise CommandError("Kullanıcı bulunamadı: %s" % ad)
            return kullanici
        kullanici = User.objects.filter(is_superuser=True).order_by("pk").first()
        if kullanici is None:
            raise CommandError(
                "Yönetici hesabı yok; --kullanici ile bir hesap verin.")
        return kullanici
