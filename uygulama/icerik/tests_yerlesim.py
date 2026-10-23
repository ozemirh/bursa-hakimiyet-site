# -*- coding: utf-8 -*-
"""Yerleşim değişmezleri — sütun genişlikleri ve dikiş hizası.

Buradaki kurallar göz kararıyla değil **ölçümle** kondu (başsız Chrome,
`tests_panel_olcum.Cdp`). Testler ölçümü tekrarlamaz; ölçümün vardığı
sonucu CSS metninde kilitler, çünkü kayma her seferinde tek bir sayının
elle değişmesinden doğuyor.
"""

import re
from pathlib import Path

from django.test import TestCase

KOK = Path(__file__).resolve().parent.parent
CSS = (KOK / "statik" / "stil" / "site.css").read_text(encoding="utf-8")


def sag_ray(secici):
    """`grid-template-columns: minmax(0,1fr) <N>px` içindeki N."""
    kural = re.search(re.escape(secici) + r"\{([^}]*)\}", CSS).group(1)
    return re.search(r"grid-template-columns:minmax\(0,1fr\) (\d+)px", kural).group(1)


class SagRayHizasi(TestCase):
    """Sağ ray sayfanın her satırında AYNI genişlikte olmalı.

    29 Ağustos 2026'da kaçık yakalandı: manşet satırı 340 px, altındaki ana
    ızgara 320 px idi. Sol sütun manşetin bittiği yerde 742'den 762'ye
    atlıyor, sayfanın dikey ek yeri 20 px kayıyordu — ölçüldü: dikiş manşette
    x=1003, hemen altındaki bölümde x=1023. Göz bu kaymayı yakalıyor.

    1140 px altında iki kural da 300 px'e iniyor; kaçık yalnız geniş
    ekranda görünüyordu.
    """

    def test_manset_ve_ana_izgara_ayni_rayi_kullaniyor(self):
        self.assertEqual(sag_ray(".manset-alani"), sag_ray(".ana-izgara"))

    def test_ray_olcusu_sitenin_geri_kalaniyla_ayni(self):
        """Haber detayın `.izgara`sı da aynı rayı kullanır."""
        self.assertEqual(sag_ray(".ana-izgara"), sag_ray(".izgara"))

    def test_dar_ekranda_hepsi_birlikte_daraliyor(self):
        """Kırılma noktasında biri daralıp öteki kalırsa dikiş yine kayar.

        29 Ağustos doğrulama turu (K4): `.izgara` 1001-1140 bandında 320'de
        kalmıştı — anasayfa↔makale geçişinde ray 20 px kayıyordu. Makale
        ızgarasının daraltması KENDİ bandında (1001-1140, iki uçtan sınırlı)
        durur: ≤1000'de `.izgara` tek sütuna iner ve dosyanın sonundaki açık
        uçlu bir kural onu ezerdi; `sag_ray(".izgara")` da ilk eşleşmeyi
        okuduğu için taban kural (320) dosyada önce kalmalı.
        """
        blok = re.search(r"@media\(max-width:1140px\)\{(.*?)\n\}", CSS, re.S).group(1)
        self.assertEqual(
            re.findall(r"\.(manset-alani|ana-izgara)\{grid-template-columns:"
                       r"minmax\(0,1fr\) (\d+)px\}", blok),
            [("manset-alani", "300"), ("ana-izgara", "300")])
        makale = re.search(r"@media\(min-width:1001px\) and \(max-width:1140px\)"
                           r"\{(.*?)\n\}", CSS, re.S).group(1)
        self.assertIn(".izgara{grid-template-columns:minmax(0,1fr) 300px}", makale)


class MakaleRayi(TestCase):
    """Makale sayfalarının ızgarası ikinci sütunu DOLDURMALI.

    29 Ağustos 2026 görsel denetimi: `.izgara` iki sütun ayırıyordu
    (1fr + 320 px), haber detay ve köşe yazısı şablonları tek çocuk
    koyuyordu — her makale sayfasında 342 px ölü sütun (ölçüldü,
    1280 px'te `.detay` 758 px / `.izgara` 1100 px). Sözleşme: iki
    makale şablonunda da ızgaranın ikinci hücresini dolduran bir
    `aside.ray` bulunur.
    """

    def test_haber_detayda_ray_var(self):
        metin = (KOK / "sablonlar" / "haber_detay.html").read_text(encoding="utf-8")
        self.assertIn('<aside class="ray"', metin)

    def test_kose_yazisinda_ray_var(self):
        metin = (KOK / "medya" / "sablonlar" / "medya" /
                 "kose_yazisi.html").read_text(encoding="utf-8")
        self.assertIn('<aside class="ray"', metin)
