"""Tekrarlanabilir site ölçümü — başsız Chrome, gerçek sunucu (Paket K).

Varsayılan test turunda **hiç yüklenmez**. Gerçek veriyle, salt okunur:

    set BH_SITE_OLCUM=1
    set BH_SQLITE_YOLU=file:C:/Users/Asus/Desktop/bursa_hakimiyet_site/uygulama/db.sqlite3?mode=ro
    set BH_CANLI_VERI_KOK=C:/Users/Asus/Desktop/bursa_hakimiyet_site/canli-veri/veri
    python manage.py test icerik.tests_site_olcum -v 2

İsteğe bağlı: `BH_SITE_OLCUM_PORT` (varsayılan 8754), `BH_SITE_OLCUM_CIKTI`
(sonuç tablosunun JSON'u buraya yazılır), `BH_CHROME`.

Test KENDİ sunucusunu açar ve kapatır (`manage.py runserver --noreload`,
`BH_ORTAM=gelistirme`): taze süreç, taze önbellek kökü (geçici klasör) —
"eski süreç portu tutuyordu", "önbellek eski CSS'i verdi" tuzakları
(URUN-PLANI §12, §14) burada kapanır. Port doluysa test başlamaz.

## Ölçülenler (11 sayfa × 7 genişlik)

* yatay taşma 0 (`scrollWidth - clientWidth`);
* `h1` = 1;
* **gerçek Tab tuşuyla** odak: her durakta `document.activeElement`
  `:focus-visible` mi ve halka (outline/box-shadow) var mı. `el.focus()`
  YANILTIYOR (7. yanılma, DEGERLENDIRME-2026-10 §4): betikle verilen odakta
  tarayıcı `:focus-visible`'ı çoğu öğede açmaz, ölçüm "halkasız" der.
  Tab ölçümü pahalı olduğu için yalnız 390 ve 1440 genişlikte;
* dış kaynak 0: `performance` kayıtlarında ve `[src]`/`link[href]`
  niteliklerinde SAYFANIN KENDİ KÖKENİ HARİÇ her köken. Eski araç
  `^https?://` ile süzdüğü için sitenin kendi mutlak adreslerini (kanonik,
  og) "dış" sayıyordu;
* boyutsuz `<img>` 0 (`width` ve `height` niteliği yoksa);
* CLS ≤ 0,02 (`layout-shift`, kullanıcı girdisi olmayan kaymalar toplamı);
* LCP öğesi görselse `loading="lazy"` DEĞİL.

## Ölçüm aracının kendi doğrulaması

İki kontrol sayfası bilerek bozuktur: biri yatay taşar, birinde odak
halkası kaldırılmış bir düğme vardır. Araç bunları görmüyorsa "0" sonucu da
değersizdir; o durumda test ölçüme hiç başlamadan düşer. Ayrıca her
sayfada stil dosyasının gerçekten yüklendiği (`:root`'ta `--tema-odak`)
denetlenir: CSS gelmezse sayfa çıplak akar ve taşma görünmez.
"""

import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

GENISLIKLER = [390, 430, 600, 820, 1000, 1200, 1440]
ODAK_GENISLIKLERI = (390, 1440)
TAB_SAYISI = 40
CLS_TAVAN = 0.02

#: Sayfaya enjekte edilir — gezinmeden ÖNCE, böylece ilk kaymalar ve LCP
#: kaçırılmaz.
GOZLEMCI = r"""
window.__bh = {cls: 0, kaymalar: [], lcp: null};
try {
  new PerformanceObserver((l) => {
    for (const e of l.getEntries()) {
      if (e.hadRecentInput) continue;
      window.__bh.cls += e.value;
      const k = (e.sources || []).map(s => s.node && s.node.nodeName
        ? (s.node.nodeName.toLowerCase() + '.' + ((s.node.className || '') + '').split(' ')[0])
        : '?');
      window.__bh.kaymalar.push([Math.round(e.value * 1000) / 1000, k.join(',')]);
    }
  }).observe({type: 'layout-shift', buffered: true});
  new PerformanceObserver((l) => {
    const son = l.getEntries().slice(-1)[0];
    if (son) window.__bh.lcp = son;
  }).observe({type: 'largest-contentful-paint', buffered: true});
} catch (e) { window.__bh.hata = String(e); }
"""

OLCUM = r"""
(() => {
  const de = document.documentElement;
  const koken = location.origin;
  const tasma = de.scrollWidth - de.clientWidth;
  const tasanlar = [];
  if (tasma > 0) {
    for (const el of document.querySelectorAll('body *')) {
      const k = el.getBoundingClientRect();
      if (k.width && k.right > de.clientWidth + 1) {
        let kayan = false;
        for (let p = el.parentElement; p; p = p.parentElement) {
          const o = getComputedStyle(p).overflowX;
          if (o === 'auto' || o === 'scroll' || o === 'hidden') { kayan = true; break; }
        }
        if (!kayan) tasanlar.push(el.tagName.toLowerCase() + '.' +
          ((el.className || '') + '').split(' ')[0] + ' sag=' + Math.round(k.right));
      }
      if (tasanlar.length > 5) break;
    }
  }
  const dis = (u) => {
    if (!u || u.startsWith('data:') || u.startsWith('blob:') || u.startsWith('#')) return false;
    try { const a = new URL(u, location.href);
          return (a.protocol === 'http:' || a.protocol === 'https:') && a.origin !== koken; }
    catch (e) { return false; }
  };
  const nitelik = [...document.querySelectorAll(
      'script[src], img[src], iframe[src], source[src], video[src], audio[src], embed[src], ' +
      'link[rel~=stylesheet][href], link[rel~=preload][href], link[rel~=icon][href], ' +
      'link[rel~=modulepreload][href]')]
    .map(e => e.getAttribute('src') || e.getAttribute('href')).filter(dis);
  const srcset = [...document.querySelectorAll('img[srcset], source[srcset]')]
    .flatMap(e => e.getAttribute('srcset').split(',').map(s => s.trim().split(/\s+/)[0]))
    .filter(dis);
  const yuklenen = performance.getEntriesByType('resource').map(r => r.name).filter(dis);
  const boyutsuz = [...document.images]
    .filter(g => !(g.hasAttribute('width') && g.hasAttribute('height')))
    .map(g => (g.getAttribute('src') || '').slice(0, 80));
  const lcp = window.__bh && window.__bh.lcp;
  const lcpEl = lcp && lcp.element;
  return JSON.stringify({
    tasma, tasanlar,
    h1: document.querySelectorAll('h1').length,
    dis: [...new Set([...nitelik, ...srcset, ...yuklenen])].slice(0, 10),
    boyutsuz,
    cls: window.__bh ? Math.round(window.__bh.cls * 10000) / 10000 : -1,
    kaymalar: window.__bh ? window.__bh.kaymalar.slice(0, 5) : [],
    lcpEtiket: lcpEl ? lcpEl.tagName.toLowerCase() : (lcp ? '(öğe yok)' : ''),
    lcpLoading: lcpEl && lcpEl.tagName === 'IMG' ? (lcpEl.getAttribute('loading') || '(yok)') : '',
    lcpSrc: lcpEl && lcpEl.tagName === 'IMG' ? (lcpEl.currentSrc || '').slice(-60) : '',
    stil: document.styleSheets.length,
    temaOdak: getComputedStyle(de).getPropertyValue('--tema-odak').trim(),
    genislik: de.clientWidth,
    adres: location.pathname + location.search,
  });
})()
"""

ODAK = r"""
(() => {
  const el = document.activeElement;
  if (!el || el === document.body || el === document.documentElement) return 'yok';
  const s = getComputedStyle(el);
  const halka = (s.outlineStyle !== 'none' && parseFloat(s.outlineWidth) > 0)
             || (s.boxShadow && s.boxShadow !== 'none');
  const ad = el.tagName.toLowerCase() + (el.id ? '#' + el.id : '') + '.' +
             ((el.className || '') + '').split(' ')[0] +
             (el.getAttribute('href') ? '[' + el.getAttribute('href').slice(0, 40) + ']' : '');
  return JSON.stringify({ad, gorunur: el.matches(':focus-visible'), halka,
                         kutu: el.getBoundingClientRect().width > 0});
})()
"""

KONTROL_TASMA = "data:text/html,<html><body style='margin:0'><div style='width:2400px'>x</div></body></html>"
KONTROL_ODAK = ("data:text/html,<html><head><style>button{outline:none!important;"
                "box-shadow:none!important}</style></head><body><button>a</button></body></html>")


def _port_bos(port):
    with socket.socket() as s:
        return s.connect_ex(("127.0.0.1", port)) != 0


def _getir(adres, saniye=180):
    istek = urllib.request.Request(adres, headers={"User-Agent": "bh-site-olcum"})
    with urllib.request.urlopen(istek, timeout=saniye) as y:
        return y.status, y.read().decode("utf-8", "replace")


if os.environ.get("BH_SITE_OLCUM") == "1":

    from django.test import SimpleTestCase

    from .tests_panel_olcum import Cdp

    class SiteOlcumu(SimpleTestCase):
        databases = set()
        PORT = int(os.environ.get("BH_SITE_OLCUM_PORT", "8754"))

        @classmethod
        def setUpClass(cls):
            super().setUpClass()
            if not (os.environ.get("BH_SQLITE_YOLU") or os.environ.get("BH_VERITABANI")):
                raise RuntimeError("BH_SQLITE_YOLU (salt okunur) ya da BH_VERITABANI ver: "
                                   "ölçüm gerçek veriye karşı yapılır.")
            if not _port_bos(cls.PORT):
                raise RuntimeError(f"Port {cls.PORT} dolu — eski süreç olabilir "
                                   f"(netstat -ano | findstr :{cls.PORT}).")
            cls.onbellek = tempfile.mkdtemp(prefix="bh-olcum-onbellek-")
            ortam = dict(os.environ, BH_ORTAM="gelistirme", BH_HATA_AYIKLA="1",
                         BH_ONBELLEK_KOK=cls.onbellek, PYTHONIOENCODING="utf-8")
            ortam.pop("BH_SITE_OLCUM", None)
            cls.gunluk = open(Path(cls.onbellek) / "sunucu.log", "w", encoding="utf-8")
            cls.sunucu = subprocess.Popen(
                [sys.executable, "manage.py", "runserver", f"127.0.0.1:{cls.PORT}",
                 "--noreload"],
                cwd=str(Path(__file__).resolve().parent.parent), env=ortam,
                stdout=cls.gunluk, stderr=subprocess.STDOUT)
            cls.kok = f"http://127.0.0.1:{cls.PORT}"
            cls.cdp = None
            try:
                cls._sunucuyu_bekle()
                cls.sayfalar = cls._sayfalari_bul()
                cls.cdp = Cdp()
                cls.cdp.cagir("Page.enable")
                cls.cdp.cagir("Network.enable")
                cls.cdp.cagir("Network.setCacheDisabled", cacheDisabled=True)
                cls.cdp.cagir("Page.addScriptToEvaluateOnNewDocument", source=GOZLEMCI)
            except Exception:
                cls._kapat()
                raise

        @classmethod
        def _kapat(cls):
            if getattr(cls, "cdp", None):
                cls.cdp.kapat()
            cls.sunucu.terminate()
            try:
                cls.sunucu.wait(timeout=15)
            except subprocess.TimeoutExpired:
                cls.sunucu.kill()
            cls.gunluk.close()
            shutil.rmtree(cls.onbellek, ignore_errors=True)

        @classmethod
        def tearDownClass(cls):
            cls._kapat()
            super().tearDownClass()

        @classmethod
        def _sunucuyu_bekle(cls):
            son = time.time() + 240
            while time.time() < son:
                if cls.sunucu.poll() is not None:
                    raise RuntimeError("sunucu açılmadı; günlük: "
                                       + (Path(cls.onbellek) / "sunucu.log").read_text("utf-8")[-2000:])
                try:
                    if _getir(cls.kok + "/_durum", 5)[0] == 200:
                        return
                except Exception:
                    time.sleep(0.5)
            raise RuntimeError("sunucu 240 sn içinde yanıt vermedi")

        @classmethod
        def _sayfalari_bul(cls):
            """Haber ve köşe yazısı adresini gerçek veriden keşfeder."""
            _, ana = _getir(cls.kok + "/")
            hrefler = re.findall(r'href="(/[^"#?]+)"', ana)
            haber = next((h for h in hrefler if re.fullmatch(r"/[a-z0-9-]+/[^/]+-\d+", h)
                          and not h.startswith(("/yazarlar/", "/galeriler/", "/videolar/",
                                                "/konu/", "/ilce/"))), None)
            kose = next((h for h in hrefler
                         if re.fullmatch(r"/yazarlar/[^/]+-\d+/[^/]+-\d+", h)), None)
            if kose is None:
                _, yazarlar = _getir(cls.kok + "/yazarlar")
                yazar = next(iter(re.findall(r'href="(/yazarlar/[^/"]+-\d+)"', yazarlar)), None)
                if yazar:
                    _, sayfa = _getir(cls.kok + yazar)
                    kose = next(iter(re.findall(
                        r'href="(/yazarlar/[^/"]+-\d+/[^/"]+-\d+)"', sayfa)), None)
            sayfalar = [("anasayfa", "/"), ("haber detay", haber), ("bursa", "/bursa"),
                        ("bursaspor", "/bursaspor"), ("ekonomi", "/ekonomi"),
                        ("teknoloji", "/teknoloji"), ("köşe yazısı", kose),
                        ("ilçe", "/ilce/osmangazi"), ("konular", "/konular"),
                        ("nöbetçi eczane", "/nobetci-eczane"), ("arama", "/ara?q=bursa")]
            eksik = [ad for ad, yol in sayfalar if not yol]
            if eksik:
                raise RuntimeError(f"adres bulunamadı: {eksik}")
            return sayfalar

        # -- tarayıcı ---------------------------------------------------

        def _git(self, adres, genislik):
            self.cdp.cagir("Emulation.setDeviceMetricsOverride", width=genislik, height=900,
                           deviceScaleFactor=1, mobile=genislik < 600)
            self.cdp.cagir("Page.navigate", url=adres)
            if not self.cdp.olay_bekle("Page.loadEventFired", 120):
                raise AssertionError(f"yüklenmedi: {adres} @{genislik}")
            time.sleep(0.8)   # geç gelen kayma ve LCP adayları

        def _degerlendir(self, ifade):
            return self.cdp.cagir("Runtime.evaluate", expression=ifade,
                                  returnByValue=True)["result"].get("value")

        def _tab(self):
            for tur in ("keyDown", "keyUp"):
                self.cdp.cagir("Input.dispatchKeyEvent", type=tur, key="Tab", code="Tab",
                               windowsVirtualKeyCode=9, nativeVirtualKeyCode=9)

        def _odak_tur(self):
            halkasiz, goruldu = [], set()
            for _ in range(TAB_SAYISI):
                self._tab()
                ham = self._degerlendir(ODAK)
                if ham == "yok":
                    continue
                o = json.loads(ham)
                if o["ad"] in goruldu:
                    continue
                goruldu.add(o["ad"])
                if o["kutu"] and not (o["gorunur"] and o["halka"]):
                    halkasiz.append(o["ad"])
            return len(goruldu), halkasiz

        # -- testler ----------------------------------------------------

        def test_1_olcer_bozuk_sayfayi_goruyor(self):
            self._git(KONTROL_TASMA, 390)
            self.assertGreater(json.loads(self._degerlendir(OLCUM))["tasma"], 0,
                               "ölçer taşmayı görmüyor")
            self._git(KONTROL_ODAK, 1440)
            _, halkasiz = self._odak_tur()
            self.assertTrue(halkasiz, "ölçer halkasız düğmeyi görmüyor")

        def test_2_sayfalar_genislikler(self):
            sonuc, bulgular = [], []
            for ad, yol in self.sayfalar:
                for g in GENISLIKLER:
                    t0 = time.perf_counter()
                    self._git(self.kok + yol, g)
                    sure = time.perf_counter() - t0
                    o = json.loads(self._degerlendir(OLCUM))
                    if g in ODAK_GENISLIKLERI:
                        o["odak_durak"], o["halkasiz"] = self._odak_tur()
                    o.update(sayfa=ad, yol=yol, g=g, yukleme_sn=round(sure, 2))
                    sonuc.append(o)
                    on = f"{ad} @{g}"
                    if not o["stil"] or not o["temaOdak"]:
                        bulgular.append(f"{on}: stil yüklenmedi (ölçüm geçersiz)")
                    if o["tasma"] > 0:
                        bulgular.append(f"{on}: taşma {o['tasma']} px {o['tasanlar']}")
                    if o["h1"] != 1:
                        bulgular.append(f"{on}: h1 = {o['h1']}")
                    if o["dis"]:
                        bulgular.append(f"{on}: dış kaynak {o['dis']}")
                    if o["boyutsuz"]:
                        bulgular.append(f"{on}: boyutsuz img {o['boyutsuz'][:3]}")
                    if o["cls"] > CLS_TAVAN:
                        bulgular.append(f"{on}: CLS {o['cls']} {o['kaymalar']}")
                    if o["lcpLoading"] == "lazy":
                        bulgular.append(f"{on}: LCP görseli lazy ({o['lcpSrc']})")
                    if o.get("halkasiz"):
                        bulgular.append(f"{on}: halkasız odak {o['halkasiz'][:5]}")
            self._rapor(sonuc, bulgular)
            self.assertEqual(bulgular, [], "\n" + "\n".join(bulgular))

        def _rapor(self, sonuc, bulgular):
            cikti = os.environ.get("BH_SITE_OLCUM_CIKTI")
            if cikti:
                Path(cikti).write_text(json.dumps({"sonuc": sonuc, "bulgular": bulgular},
                                                  ensure_ascii=False, indent=1),
                                       encoding="utf-8")
            satirlar = ["", f"{'sayfa':16}{'g':>6}{'taşma':>7}{'h1':>4}{'dış':>5}"
                        f"{'boyutsuz':>9}{'CLS':>8}{'LCP':>6}{'loading':>9}{'odak':>6}"
                        f"{'halkasız':>9}{'sn':>6}"]
            for o in sonuc:
                satirlar.append(
                    f"{o['sayfa'][:15]:16}{o['g']:>6}{o['tasma']:>7}{o['h1']:>4}"
                    f"{len(o['dis']):>5}{len(o['boyutsuz']):>9}{o['cls']:>8}"
                    f"{o['lcpEtiket'][:5]:>6}{o['lcpLoading'][:8]:>9}"
                    f"{o.get('odak_durak', ''):>6}{len(o.get('halkasiz') or []) if 'halkasiz' in o else '':>9}"
                    f"{o['yukleme_sn']:>6}")
            print("\n".join(satirlar))
            sys.stdout.flush()
