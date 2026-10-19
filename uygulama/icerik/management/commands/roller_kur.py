"""Beş rolü ve on dört yetkiliği kurar; tekrar çalıştırılabilir.

`PANEL-NOTLARI.md` §11'deki matrisi Django gruplarına yazar. Matrisin
kendisi `icerik/yetkiler.py` içindedir — burası yalnızca uygular.

Kullanım:
    python manage.py roller_kur
    python manage.py roller_kur --dokum     # yalnız raporlar, yazmaz
"""

from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand
from django.db import transaction

from icerik.yetkiler import IKI_ADIMLI_ZORUNLU, MATRIS, ROLLER, rolun_yetkileri


class Command(BaseCommand):
    help = "Rol matrisini (PANEL-NOTLARI.md §11) veritabanına kurar."

    def add_arguments(self, ayristirici):
        ayristirici.add_argument("--dokum", action="store_true",
                                 help="Yazma; yalnızca mevcut durumu raporla.")

    def handle(self, *args, **secenek):
        self.sessiz = secenek.get("verbosity", 1) == 0
        izinler = {
            p.codename: p
            for p in Permission.objects.filter(codename__in=MATRIS.keys())
        }
        eksik = set(MATRIS) - set(izinler)
        if eksik:
            self.stderr.write(
                "Bu izinler veritabanında yok: " + ", ".join(sorted(eksik)) +
                "\n`manage.py migrate` çalıştırılmamış olabilir.")
            return

        if secenek["dokum"]:
            self.sessiz = False   # --dokum acikca cikti istiyor
            self._dokum()
            return

        with transaction.atomic():
            for rol in ROLLER:
                grup, yeni = Group.objects.get_or_create(name=rol)
                kodlar = rolun_yetkileri(rol)
                grup.permissions.set([izinler[k] for k in kodlar])
                isaret = "kuruldu" if yeni else "güncellendi"
                self._yaz(f"  {rol:18} {len(kodlar):>2} yetki  {isaret}")

        self._yaz("")
        self._dokum()

    def _yaz(self, metin: str) -> None:
        """Sessiz kipte yazmaz; konsol Türkçe/işaret karakterini kaldıramıyorsa
        ASCII karşılığına düşer.

        Windows konsolu varsayılan olarak cp857/cp1254 kullanıyor ve "●"
        karakterini kodlayamayıp komutu çökertiyordu — döküm bir yan çıktı,
        komutun kendisini düşürmemeli.
        """
        if self.sessiz:
            return
        try:
            self.stdout.write(metin)
        except UnicodeEncodeError:
            self.stdout.write(metin.replace("●", "+").replace("–", "-")
                              .encode("ascii", "replace").decode("ascii"))

    def _dokum(self):
        self._yaz("Rol matrisi:")
        basliklar = "".join(f"{r[:9]:>11}" for r in ROLLER)
        self._yaz(f"  {'yetki':32}{basliklar}")
        for kod in MATRIS:
            satir = "".join(
                f"{('  ●' if rol in MATRIS[kod] else '  –'):>11}" for rol in ROLLER)
            self._yaz(f"  {kod:32}{satir}")

        toplam = sum(len(v) for v in MATRIS.values())
        self._yaz(
            f"\n  {len(ROLLER)} rol · {len(MATRIS)} yetkilik · {toplam} bağ")
        self._yaz(
            "  2FA zorunlu olması önerilen roller: "
            + ", ".join(sorted(IKI_ADIMLI_ZORUNLU)))

        for rol in ROLLER:
            grup = Group.objects.filter(name=rol).first()
            if grup is None:
                self._yaz(f"  UYARI: {rol} grubu veritabanında yok.")
            elif grup.permissions.count() != len(rolun_yetkileri(rol)):
                self._yaz(
                    f"  UYARI: {rol} grubunda {grup.permissions.count()} izin var, "
                    f"matris {len(rolun_yetkileri(rol))} diyor.")
        self._hesap_denetimi()

    #: Ölçüm için açılan deneme hesaplarının ortak parolası (URUN-PLANI §24
    #: notu). Bu parolayı taşıyan açık hesap üretime TAŞINMAMALI.
    DENEME_PAROLALARI = ("deneme1234",)

    def _hesap_denetimi(self):
        """Kurulum uyarısı (Paket F madde 8, 19 Ekim 2026).

        Panel yetkisi rolden gelir; `is_staff` panel için GEREKMEZ, yalnız
        `/yonetim/` (Django admin) kapısını ve sunum araçlarını açar.
        Deneme hesapları (`yonetmen`, `editor`, `muhabir`) bugün `is_staff`
        taşıyor ve ortak bir deneme parolasıyla açık. Komut hiçbir hesabı
        DEĞİŞTİRMEZ; yalnız uyarır.
        """
        if self.sessiz:
            return
        from django.contrib.auth.hashers import check_password
        from django.contrib.auth.models import User

        personel = sorted(User.objects.filter(is_staff=True, is_superuser=False)
                          .values_list("username", flat=True))
        if personel:
            self._yaz(
                "  UYARI: is_staff panel için gerekmez (yetki rolden gelir); "
                "yalnız /yonetim/ ve sunum araçlarını açar. is_staff taşıyan "
                "hesaplar: " + ", ".join(personel))
        zayif = sorted(
            u.username for u in User.objects.filter(is_active=True).only("username", "password")
            if any(check_password(p, u.password) for p in self.DENEME_PAROLALARI))
        if zayif:
            self._yaz(
                "  UYARI: deneme parolası taşıyan açık hesap(lar): "
                + ", ".join(zayif) + ". Üretime taşınmadan önce kapatılmalı "
                "ya da parolaları değiştirilmeli.")
