"""Düzeltme / cevap notu — başsız Chrome ölçümü (20 Ekim 2026).

Varsayılan test turunda **hiç yüklenmez** (Chrome gerektirir):

    set BH_DUZELTME_OLCUM=1
    python manage.py test icerik.tests_duzeltme_olcum -v 2

Kendi test veritabanını ve canlı sunucusunu test çatısından alır
(`StaticLiveServerTestCase`); paylaşılan veritabanına yazmaz. Uzun metin,
uzun cevap veren adı ve uzun başlık bilerek: taşmayı en çok onlar zorlar.

Ölçülenler — haber detayı (notlu), `/duzeltmeler` ve panelin haber düzenleme
ekranı × 360 · 390 · 768 · 1440:

* yatay taşma 0, `h1` = 1;
* bölümün her odaklanabilir öğesi **gerçek Tab tuşuyla** (`el.focus()`
  yanıltıyor, DEGERLENDIRME-2026-10 §4) `:focus-visible` ve halkalı;
* bölümdeki her metin öğesinin kontrastı ≥ 4,5:1 (gerçek zemin, saydam
  katmanlar atlanarak);
* ölçer kendini doğrular: bilerek taşan ve halkasız kontrol sayfalarını
  görmüyorsa sonuç değersizdir.

İlk koşuda (20 Ekim 2026) iki gerçek kusur buldu, ikisi de düzeltildi:
panelde 360 px'te 309 px taşma (kayan tablodaki mutlak konumlu gizli
etiket kırpmadan kaçıyordu) ve `.sag-not` ipuçlarında 2,75:1 kontrast.
Sonuç: üç sayfa × dört genişlikte taşma 0, h1 1, Tab ile bütün duraklar
halkalı; en düşük kontrast haber 5,17 · dizin 4,60 · panel 5,40.
"""

import json
import os
import time
from datetime import timedelta

from .tests_panel_olcum import Cdp

GENISLIKLER = [360, 390, 768, 1440]
TAB_SINIRI = 260
BOLUM = ".duzeltme-isaret, .duzeltme-bolmesi, .duzeltme-sayfa, .duzeltme-bolumu"

OLCUM = r"""
((secici) => {
  const de = document.documentElement;
  const tasma = de.scrollWidth - de.clientWidth;
  const kanal = (c) => { c /= 255; return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4; };
  const rgb = (s) => (s.match(/[\d.]+/g) || []).map(Number);
  const isik = ([r, g, b]) => 0.2126 * kanal(r) + 0.7152 * kanal(g) + 0.0722 * kanal(b);
  const zemin = (el) => {
    for (let p = el; p; p = p.parentElement) {
      const z = rgb(getComputedStyle(p).backgroundColor);
      if (z.length >= 3 && (z.length < 4 || z[3] > 0.5)) return z;
    }
    return [255, 255, 255];
  };
  const dusuk = [];
  let olculen = 0, enAz = 99;
  for (const kap of document.querySelectorAll(secici)) {
    for (const el of [kap, ...kap.querySelectorAll('*')]) {
      const metin = [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim());
      if (!metin || !el.getBoundingClientRect().width) continue;
      const a = isik(rgb(getComputedStyle(el).color)), b = isik(zemin(el));
      const oran = (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
      olculen++; enAz = Math.min(enAz, oran);
      if (oran < 4.5) dusuk.push(el.tagName.toLowerCase() + '.' + ((el.className || '') + '').split(' ')[0] + ' ' + oran.toFixed(2));
    }
  }
  const tasanlar = [];
  if (tasma > 0) for (const el of document.querySelectorAll('body *')) {
    const k = el.getBoundingClientRect();
    if (k.width && k.right > de.clientWidth + 1) {
      let kayan = false;
      for (let p = el.parentElement; p; p = p.parentElement) {
        const o = getComputedStyle(p).overflowX;
        if (o === 'auto' || o === 'scroll' || o === 'hidden') { kayan = true; break; }
      }
      if (!kayan || window.__bhTumu) tasanlar.push(el.tagName.toLowerCase() + '.' + ((el.className || '') + '').split(' ')[0] + ' w=' + Math.round(k.width));
    }
    if (tasanlar.length > 12) break;
  }
  return JSON.stringify({tasma, tasanlar, h1: document.querySelectorAll('h1').length,
    bolum: document.querySelectorAll(secici).length, olculen, enAz: Math.round(enAz * 100) / 100, dusuk,
    odaklanabilir: [...document.querySelectorAll(secici)].flatMap(k =>
      [...k.querySelectorAll('a[href], button, input:not([type=hidden]), select, textarea')]).length,
    stil: getComputedStyle(de).getPropertyValue('--kirmizi').trim() !== '' ||
          getComputedStyle(de).getPropertyValue('--deniz').trim() !== ''});
})
"""

ODAK = r"""
((secici) => {
  const el = document.activeElement;
  if (!el || el === document.body) return 'yok';
  const s = getComputedStyle(el);
  const halka = (s.outlineStyle !== 'none' && parseFloat(s.outlineWidth) > 0)
             || (s.boxShadow && s.boxShadow !== 'none');
  /* Sıra numarası adın parçası: aynı adresli üç bağlantı (aynı haberin üç
     notu) ya da üç "Yayından kaldır" düğmesi tek öğe sayılıyordu. */
  const tum = [...document.querySelectorAll(secici)].flatMap(k =>
    [...k.querySelectorAll('a[href], button, input:not([type=hidden]), select, textarea')]);
  return JSON.stringify({ad: tum.indexOf(el) + ':' + el.tagName.toLowerCase() + (el.id ? '#' + el.id : '') + '.' +
      ((el.className || '') + '').split(' ')[0] + '[' + (el.getAttribute('href') || el.name || '') + ']',
    bolumde: !!el.closest(secici), gorunur: el.matches(':focus-visible'), halka});
})
"""

KONTROL_TASMA = "data:text/html,<html><body style='margin:0'><div style='width:2400px'>x</div></body></html>"
KONTROL_ODAK = ("data:text/html,<html><head><style>a{outline:none!important}</style></head>"
                "<body><p class='duzeltme-isaret'><a href='/x'>a</a></p></body></html>")


if os.environ.get("BH_DUZELTME_OLCUM") == "1":

    from django.contrib.auth.models import Group, User
    from django.contrib.staticfiles.testing import StaticLiveServerTestCase
    from django.core.management import call_command
    from django.test import override_settings
    from django.utils import timezone

    from taksonomi.models import Kategori, KategoriTur

    from .models import Duzeltme, Haber

    @override_settings(SAYFA_ONBELLEK_SANIYE=0)
    class DuzeltmeOlcumu(StaticLiveServerTestCase):

        @classmethod
        def setUpClass(cls):
            super().setUpClass()
            cls.cdp = Cdp()

        @classmethod
        def tearDownClass(cls):
            cls.cdp.kapat()
            super().tearDownClass()

        def setUp(self):
            call_command("taksonomi_kur", verbosity=0)
            call_command("roller_kur", verbosity=0)
            kategori = KategoriTur.objects.get(tur=Kategori.TUR_HABER, slug="gundem").kategori
            simdi = timezone.now()
            self.haber = Haber.objects.create(
                id=8900001, slug="olcum-haberi",
                baslik=("Bursa Büyükşehir Belediyesi'nin Nilüfer Çayı kirliliğine karşı "
                        "yürüttüğü çalışmalarda yeni aşama"),
                spot="Spot metni.", govde="<p>Birinci paragraf.</p><p>İkinci paragraf.</p>",
                kategori=kategori, durum=Haber.DURUM_AKTIF,
                yayin_zamani=simdi - timedelta(hours=3))
            uzun = ("Haberin ilk hâlinde arıtma tesisinin kapasitesi günlük 120 bin metreküp "
                    "olarak yazılmıştı; doğrusu 102 bin metreküptür. ") * 3
            Duzeltme.objects.create(haber=self.haber, metin=uzun)
            Duzeltme.objects.create(
                haber=self.haber, tur=Duzeltme.TUR_CEVAP,
                cevap_veren=("Bursa Büyükşehir Belediyesi Kent Estetiği ve Çevre Koruma Dairesi "
                             "Başkanlığı Basın ve Halkla İlişkiler Şube Müdürü"),
                metin="Kurumun gönderdiği cevap metni.\n\nİkinci paragraf "
                      "BirleşikUzunKelimeKesintisizTaşmaDenemesiİçinYazıldıBurada.")
            Duzeltme.objects.create(haber=self.haber, tur=Duzeltme.TUR_GUNCELLEME,
                                    metin="Tesisin açılış tarihi habere eklendi.")
            yonetmen = User.objects.create_user("olcum-yonetmen", first_name="Y", last_name="Y")
            yonetmen.groups.add(Group.objects.get(name="Yayın Yönetmeni"))
            self.client.force_login(yonetmen)
            self.oturum = self.client.cookies["sessionid"].value

        def _git(self, adres, genislik):
            self.cdp.cagir("Network.enable")
            self.cdp.cagir("Network.setCacheDisabled", cacheDisabled=True)
            self.cdp.cagir("Emulation.setDeviceMetricsOverride", width=genislik, height=900,
                           deviceScaleFactor=1, mobile=genislik < 600)
            self.cdp.cagir("Page.enable")
            self.cdp.cagir("Page.navigate", url=adres)
            if not self.cdp.olay_bekle("Page.loadEventFired", 60):
                raise AssertionError(f"yüklenmedi: {adres}")
            time.sleep(0.3)

        def _deger(self, ifade):
            return self.cdp.cagir("Runtime.evaluate", expression=ifade,
                                  returnByValue=True)["result"].get("value")

        def _tab_turu(self):
            goruldu, halkasiz = {}, []
            for _ in range(TAB_SINIRI):
                for tur in ("keyDown", "keyUp"):
                    self.cdp.cagir("Input.dispatchKeyEvent", type=tur, key="Tab", code="Tab",
                                   windowsVirtualKeyCode=9, nativeVirtualKeyCode=9)
                ham = self._deger(f"{ODAK}({json.dumps(BOLUM)})")
                if ham == "yok":
                    continue
                o = json.loads(ham)
                if not o["bolumde"] or o["ad"] in goruldu:
                    continue
                goruldu[o["ad"]] = o
                if not (o["gorunur"] and o["halka"]):
                    halkasiz.append(o["ad"])
            return len(goruldu), halkasiz

        def test_olcer_ve_sayfalar(self):
            self._git(KONTROL_TASMA, 390)
            self.assertGreater(json.loads(self._deger(f"{OLCUM}('body')"))["tasma"], 0)
            self._git(KONTROL_ODAK, 390)
            self.assertTrue(self._tab_turu()[1], "ölçer halkasız bağlantıyı görmüyor")

            kok = self.live_server_url
            sayfalar = [("haber", kok + self.haber.get_absolute_url(), False),
                        ("dizin", kok + "/duzeltmeler", False),
                        ("panel", kok + f"/panel/haber/{self.haber.pk}", True)]
            bulgular, tablo = [], []
            for ad, adres, oturumlu in sayfalar:
                self.cdp.cagir("Network.enable")
                self.cdp.cagir("Network.clearBrowserCookies")
                if oturumlu:
                    self.cdp.cagir("Network.setCookie", name="sessionid", value=self.oturum,
                                   url=kok + "/")
                for g in GENISLIKLER:
                    self._git(adres, g)
                    if os.environ.get("BH_OLCUM_TUMU"):
                        # Tanı: kayan kap içindekiler dahil bütün taşanlar.
                        self._deger("window.__bhTumu = true")
                    o = json.loads(self._deger(f"{OLCUM}({json.dumps(BOLUM)})"))
                    durak, halkasiz = self._tab_turu()
                    satir = {"sayfa": ad, "genislik": g, "tasma": o["tasma"], "h1": o["h1"],
                             "bolum": o["bolum"], "metin_ogesi": o["olculen"],
                             "en_dusuk_kontrast": o["enAz"], "odak_durak": durak,
                             "odaklanabilir": o["odaklanabilir"]}
                    tablo.append(satir)
                    if not o["stil"]:
                        bulgular.append(f"{ad}@{g}: stil yüklenmedi")
                    if o["tasma"] > 0:
                        bulgular.append(f"{ad}@{g}: taşma {o['tasma']} {o['tasanlar']}")
                    if o["h1"] != 1:
                        bulgular.append(f"{ad}@{g}: h1={o['h1']}")
                    if o["bolum"] < 1:
                        bulgular.append(f"{ad}@{g}: bölüm çizilmedi")
                    if o["dusuk"]:
                        bulgular.append(f"{ad}@{g}: kontrast {o['dusuk'][:5]}")
                    if halkasiz:
                        bulgular.append(f"{ad}@{g}: halkasız {halkasiz}")
                    if durak < o["odaklanabilir"]:
                        bulgular.append(f"{ad}@{g}: Tab {durak}/{o['odaklanabilir']} öğeye ulaştı")
            print()
            for s in tablo:
                print(json.dumps(s, ensure_ascii=False))
            for b in bulgular:
                print("BULGU", b)
            self.assertEqual(bulgular, [])
