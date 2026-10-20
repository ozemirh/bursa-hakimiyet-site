"""Sayfa bütçesi — istek, aktarım, LCP, CLS, HTML; detayda ilk ekran; yapışkan toplam.

Referans kütüphanesi fark matrisi satır 3, 5, 14 (20 Ekim 2026). Mevcut
bütçe CLS ≤ 0,02 + "LCP görseli lazy değil" (`tests_site_olcum`) ve
anasayfa HTML + sorgu tavanı (`tests_butce`) idi. **Sayfa başına istek
sayısı, toplam aktarım, LCP ms ve detay HTML tavanı yoktu.** Bu dosya
onları gerçek tarayıcıda, gerçek veriyle ölçer ve tavana bağlar.

Varsayılan test turunda **hiç yüklenmez** (Chrome + gerçek veri ister).
`BH_SAYFA_BUTCESI=1` ile, `.env`'yi okuyan betik üzerinden:

    $env:BH_SAYFA_BUTCESI = "1"
    .\\gelistir.ps1 -Komut "test icerik.tests_sayfa_butcesi -v 2"

Elle: `BH_SAYFA_BUTCESI=1`, `BH_VERITABANI` ya da salt okunur
`BH_SQLITE_YOLU`, `BH_CANLI_VERI_KOK`, `BH_ORTAM=gelistirme`.

İsteğe bağlı: `BH_SAYFA_BUTCESI_PORT` (8755), `BH_SAYFA_BUTCESI_CIKTI`
(ölçüm JSON'u), `BH_SAYFA_BUTCESI_GORUNTU` (ilk ekran PNG'leri bu klasöre),
`BH_SAYFA_BUTCESI_TUR` (sayfa başına tekrar, varsayılan 3), `BH_CHROME`.
Süre: 4 sayfa × 2 ekran × 4 hâl × 3 tur — 20 Ekim 2026'da 218 sn.

## Koşul

* Test KENDİ sunucusunu açar (`runserver --noreload`, taze önbellek kökü)
  ve her sayfayı ölçmeden önce bir kez `urllib` ile ısıtır. Soğuk süreçte
  ilk istek menü sayımı yüzünden saniyeler sürebiliyor (`icerik/baglam.py`);
  üretim sıcak süreçtir.
* `Network.setCacheDisabled` — her ölçüm boş önbellekle (ilk ziyaret).
* Ağ/CPU kısıtlanmaz, `deviceScaleFactor=1`. LCP yerel makinede kısıtsız
  ağda ölçülür; CrUX saha verisiyle karşılaştırılamaz. Tavan bir
  **gerileme kilidi**dir, kullanıcı deneyimi iddiası değil.
* **Geliştirmede statik dosyalar sıkıştırılmadan gelir** (runserver
  `/statik/`'i ara katmansız verir; üretimde WhiteNoise/nginx `.gz/.br`).
* `deviceScaleFactor=1`: gerçek telefonda (DPR 3) srcset büyük görsel
  seçer — 20 Ekim ölçümü, okur 390: anasayfa görsel baytı 198 → 762 KB,
  detay 45 → 73 KB. Tavan DPR 1 sayısıdır.
  Ölçülen `aktarim` bu yüzden üretimin üst sınırıdır; yanında
  `aktarim_uretim` tahmini durur: sıkıştırılmadan gelen metin yanıtlarının
  (CSS, JS, SVG) gövdesi DevTools'tan alınıp gzip -6 ile yeniden sayılır.
  **Tavan ölçülen (`aktarim`) sayıya konur** — tahmine değil.
* **Reklam dört hâlde.** Sunum araçları ("Reklamları gizle", "Test
  reklamı" düğmeleri, `reklam-test.js`) yalnız yerel makineye ya da panel
  kullanıcısına basılır (`baglam.sunum_araci_mi`). 127.0.0.1'den bakan
  ölçüm bu yüzden okurun sayfasını GÖRMEZ: düğmeler üst bandı uzatır,
  betikler istek ekler. Okur hâli için Chrome `okur.test` adını
  127.0.0.1'e çözer (`--host-resolver-rules`), sunucu bu adı
  `BH_SUNUCU_ADLARI` ile kabul eder — Host yerel olmadığı için kapı kapalı.
    - `okur`    — sıradan ziyaretçi: gri yer tutucular, yer ayrılmış;
                  **"reklam kapalı" koşulunun gerçek hâli**;
    - `kapali`  — sunum oturumu, test reklamı kapalı;
    - `acik`    — sunum oturumu, yerel test reklam hizmeti açık
                  (`bh-reklam-test=acik`, URUN-PLANI §65);
    - `gizli`   — sunum oturumu, "Reklamları gizle" (`bh-reklam=kapali`);
                  okura çizilmez, yalnız ilk ekran karşılaştırması için.
  Tavanlar `okur` ve `acik` için konur.

## Ölçüm aracının kendi doğrulaması

* **Sayaç kontrolü:** sunucunun kendi kökenindeki bir sayfaya betikle 5
  ayrı görsel eklenir; sayaç tam 5 istek ve her birinde en az dosya boyu
  kadar aktarım görmüyorsa sayfa sayıları da değersizdir. (İlk sürümde
  kontrol `data:` belgesiydi: istekler sayıldı ama hiçbiri bitmedi —
  opak kökenden yerel adrese istek takılıyor. İkinci sürüm `/static/`
  istedi; statik kök `/statik/` olduğu için beş isteğin beşi 24 KB'lık
  404 sayfası döndü ve sayı yine "5" tuttu. Kontrolün kendisi iki kez
  yanılttı; bu yüzden durum kodu ve bayt aralığı da denetlenir.)
* Her sayfada iki bağımsız yol karşılaştırılır: DevTools ağ olayları ile
  `performance` kaynak kayıtları. İstek sayısında 1'den, aktarımda %10'dan
  fazla ayrışırlarsa ölçüm geçersizdir.
* Her ölçümde hâlin gerçekten kurulduğu denetlenir: okur hâlinde sunum
  düğmesi YOK, sunum hâllerinde VAR; `data-reklam-test`/`data-reklam`
  beklenen değerde.
"""

import base64
import gzip
import json
import os
import re
import shutil
import socket
import statistics
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path

#: (genişlik, yükseklik, mobil). Rakip ölçüleriyle aynı iki ekran
#: (referans-kutuphanesi/desenler/basarim.md, haber-detay.md).
EKRANLAR = {1440: (1440, 900, False), 390: (390, 844, True)}

#: Okur hâlinin sunucu adı (Chrome'da 127.0.0.1'e çözülür).
OKUR_ADI = "okur.test"

#: Reklam hâli → (sunum oturumu mu, localStorage anahtarları).
KOSULLAR = {
    "okur": (False, {"bh-reklam-test": None, "bh-reklam": None}),
    "kapali": (True, {"bh-reklam-test": "kapali", "bh-reklam": None}),
    "acik": (True, {"bh-reklam-test": "acik", "bh-reklam": None}),
    "gizli": (True, {"bh-reklam-test": "kapali", "bh-reklam": "kapali"}),
}
TAVAN_KOSULLARI = ("okur", "acik")

#: Ölçülen haber detayı. SABİT, çünkü manşet değiştikçe makale değişirse
#: HTML (gövde uzunluğu) ve görsel baytı da değişir, tavan anlamını yitirir.
#: Görselli, kısa (1 dk okuma) bir Bursa haberi. Veritabanında yoksa
#: manşetin ilk haberine düşülür ve çıktıda yazılır.
DETAY_VARSAYILAN = "/bursa/bursa-da-sifir-arac-soku-ekspertize-goturunce-saskina-dondu-1691702"

# -- TAVANLAR ---------------------------------------------------------------
#
# Ölçüm 20 Ekim 2026, HEAD 11b46ef, PG geliştirme veritabanı (1.038.474
# haber), iki ayrı koşu (1 tur + 3 tur), tur içinde en kötü değer. Payın
# gerekçesi her sözlüğün üstünde. Tavanı yükseltmek gerekiyorsa önce
# isteğin/baytın neden geldiği bulunur ("test kırmızı, sayıyı artır" değil).
# Rakip değerleri (referans-kutuphanesi/desenler/basarim.md) yalnız bağlam:
# yerel rakipler 70–281 istek / 1,7–8,3 MB; tavan BİZİM ölçümümüzden.

#: İstek sayısı (belge dahil, `data:` hariç). Pay: ölçülen + 4 — bir yeni
#: betik/stil/font geçer, yeni bir görsel kuşağı ya da reklam ağı geçmez.
#: Anasayfada +6: görsel sayısı manşet/akış içeriğiyle oynuyor ve tarayıcının
#: favicon isteği ("Other") bazen sayılıyor.
#:                           ölçülen   okur / açık
ISTEK_TAVAN = {
    ("anasayfa", 1440, "okur"): 37, ("anasayfa", 1440, "acik"): 42,   # 31 / 36
    ("anasayfa", 390, "okur"): 26, ("anasayfa", 390, "acik"): 31,     # 20 / 25
    ("ekonomi", 1440, "okur"): 20, ("ekonomi", 1440, "acik"): 23,     # 16 / 19
    ("ekonomi", 390, "okur"): 18, ("ekonomi", 390, "acik"): 20,       # 14 / 16
    ("detay", 1440, "okur"): 19, ("detay", 1440, "acik"): 23,         # 15 / 19
    ("detay", 390, "okur"): 19, ("detay", 390, "acik"): 22,           # 15 / 18
    ("ilce", 1440, "okur"): 20, ("ilce", 1440, "acik"): 23,           # 16 / 19
    ("ilce", 390, "okur"): 18, ("ilce", 390, "acik"): 20,             # 14 / 16
}

#: Aktarım (KB = 1024 B; başlıklar dahil; statik SIKIŞTIRILMADAN — modül
#: başına bak). Pay ×1,25 (10'a yuvarlı): görsel baytı haberden habere
#: oynuyor. Ölçülenin ~233 KB'ı sıkıştırılmamış CSS, 216–330 KB'ı font;
#: üretim tahmini (`aktarim_uretim`) yanında.
#:                           ölçülen okur / açık · üretim tahmini okur
AKTARIM_TAVAN_KB = {
    ("anasayfa", 1440, "okur"): 1050, ("anasayfa", 1440, "acik"): 1070,  # 835 / 851 · 653
    ("anasayfa", 390, "okur"): 890, ("anasayfa", 390, "acik"): 910,      # 710 / 726 · 528
    ("ekonomi", 1440, "okur"): 810, ("ekonomi", 1440, "acik"): 830,      # 646 / 658 · 463
    ("ekonomi", 390, "okur"): 730, ("ekonomi", 390, "acik"): 740,        # 577 / 588 · 395
    ("detay", 1440, "okur"): 870, ("detay", 1440, "acik"): 880,          # 689 / 704 · 498
    ("detay", 390, "okur"): 830, ("detay", 390, "acik"): 850,            # 663 / 675 · 472
    ("ilce", 1440, "okur"): 940, ("ilce", 1440, "acik"): 960,            # 748 / 761 · 566
    ("ilce", 390, "okur"): 750, ("ilce", 390, "acik"): 770,              # 599 / 610 · 417
}

#: LCP (ms, 3 turun ortancası). Ölçülen ortancalar 128–676 ms (tek turda en
#: çok 924). Kısıtsız yerel ölçüm makine yüküne göre oynuyor; tavan bu
#: yüzden geniş ve tek. Yakaladığı şey kademe sıçraması: LCP görselinin
#: tembelleşmesi, engelleyen betik, önbelleksiz soğuk sorgu.
LCP_TAVAN_MS = 1500

#: CLS — `tests_site_olcum` ile aynı tavan. Ölçülen en çok 0,0003.
CLS_TAVAN = 0.02

#: Belge HTML'i (KB): (açılmış, gzip). Pay ×1,2. Detay SABİT makale
#: (yukarıda). Anasayfa açılmış hâliyle planın 200 KB bütçesini AŞIYOR —
#: bkz. `tests_butce.ANASAYFA_HTML_TAVAN` notu; buradaki tavan bugünü kilitler.
#:                    ölçülen açılmış / gzip
HTML_TAVAN_KB = {
    "anasayfa": (280, 43),   # 230,4 / 35,7
    "ekonomi": (101, 22),    #  83,9 / 17,6
    "detay": (71, 17),       #  59,0 / 14,2
    "ilce": (88, 19),        #  72,8 / 15,5
}

#: 390 px'te kaydırırken ekranda kalan yapışık şeritlerin toplamı (px).
#: Ölçülen: 82 px (yalnız kategori bandı, `site.css` `.kategori`) = 844'ün
#: %9,7'si; altta yapışık öğe yok. Tavan ekranın ~%11'i: ikinci bir yapışık
#: şerit (son dakika bandı, yapışkan reklam) ya da bandın büyümesi geçmez.
YAPISKAN_TAVAN_PX = 90

#: Anasayfada ilk ekranda TAMAMI görünen başlık sayısının alt sınırı.
#: Ölçülen (okur ve açık): 1440 → 4 (dörtlü), 390 → 1 (manşet). Karar değil,
#: bugünün alt sınırı — bkz. test_4.
ILK_EKRAN_BASLIK_ALT = {1440: 4, 390: 1}

#: Kontrol sayfasının istediği görsel sayısı ve dosyası.
KONTROL_GORSEL = 5
KONTROL_DOSYA = "simge/simge-32.png"

#: Üretimde sıkıştırılarak giden yanıt türleri (`cekirdek.ara_katman`
#: SIKISTIRILAN_TURLER ve WhiteNoise'un sıkıştırdığı uzantılarla aynı aile).
METIN_TURLERI = ("text/", "application/javascript", "application/json",
                 "image/svg+xml", "application/xml")


GOZLEMCI = r"""
window.__bh = {cls: 0, kaymalar: [], lcp: null, lcpZaman: 0};
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
    if (son) { window.__bh.lcp = son; window.__bh.lcpZaman = son.startTime; }
  }).observe({type: 'largest-contentful-paint', buffered: true});
} catch (e) { window.__bh.hata = String(e); }
"""

#: Yükleme bittikten sonra, kaydırmadan önce: CLS, LCP, performans kayıtları,
#: ilk ekran konumları, ilk ekrandaki başlık sayısı.
OLCUM = r"""
(() => {
  const vh = innerHeight, vw = innerWidth;
  const bh = window.__bh || {};
  const lcp = bh.lcp, lcpEl = lcp && lcp.element;
  const nav = performance.getEntriesByType('navigation')[0] || {};
  const kaynak = performance.getEntriesByType('resource')
    .filter(r => !r.name.startsWith('data:'));
  const konum = (s) => {
    const e = document.querySelector(s);
    if (!e) return null;
    const r = e.getBoundingClientRect();
    if (!r.width && !r.height) return null;
    return {ust: Math.round(r.top + scrollY), alt: Math.round(r.bottom + scrollY),
            yuk: Math.round(r.height)};
  };
  // İlk ekrandaki başlıklar: haber/köşe yazısı adresine giden, en az 10
  // harflik metni olan, görüntü alanıyla kesişen VE o noktada gerçekten
  // görünen (elementFromPoint; kaydırıcıda kırpılan slayt sayılmaz) bağlantı.
  // Aynı adres bir kez sayılır. `tam`: alt kenarı da ekranda.
  const desen = /^\/(?:yazarlar\/[^/]+-\d+\/[^/]+-\d+|(?!yazarlar\/|ilce\/|konu\/|static\/)[a-z0-9-]+\/[^/]+-\d+)$/;
  const tam = new Set(), kismi = new Set(), yerler = {};
  for (const a of document.querySelectorAll('a[href]')) {
    let yol;
    try { const u = new URL(a.href); if (u.origin !== location.origin) continue; yol = u.pathname; }
    catch (e) { continue; }
    if (!desen.test(yol)) continue;
    if ((a.innerText || '').trim().length < 10) continue;
    const r = a.getBoundingClientRect();
    if (r.width < 1 || r.height < 1 || r.bottom <= 0 || r.top >= vh || r.right <= 0 || r.left >= vw) continue;
    const cx = Math.min(Math.max(r.left + r.width / 2, 0), vw - 1);
    const cy = Math.min(Math.max((Math.max(r.top, 0) + Math.min(r.bottom, vh)) / 2, 0), vh - 1);
    const ust = document.elementFromPoint(cx, cy);
    if (!ust || !(ust === a || a.contains(ust))) continue;
    if (tam.has(yol) || kismi.has(yol)) { if (r.bottom <= vh) { kismi.delete(yol); tam.add(yol); } continue; }
    (r.bottom <= vh ? tam : kismi).add(yol);
    const kap = a.parentElement && a.parentElement.closest('[class]');
    const ad = kap ? (kap.tagName.toLowerCase() + '.' + ((kap.className || '') + '').split(' ')[0]) : '?';
    yerler[ad] = (yerler[ad] || 0) + 1;
  }
  const yuvalar = [...document.querySelectorAll('.reklam')].filter(e => {
    const r = e.getBoundingClientRect(); return r.height > 0 && r.top < vh && r.bottom > 0;
  });
  return JSON.stringify({
    cls: Math.round((bh.cls || 0) * 10000) / 10000,
    kaymalar: (bh.kaymalar || []).slice(0, 5),
    lcpMs: Math.round(bh.lcpZaman || 0),
    lcpEtiket: lcpEl ? lcpEl.tagName.toLowerCase() + '.' + ((lcpEl.className || '') + '').split(' ')[0]
                     : (lcp ? '(öğe yok)' : ''),
    lcpLoading: lcpEl && lcpEl.tagName === 'IMG' ? (lcpEl.getAttribute('loading') || '(yok)') : '',
    lcpSrc: lcpEl && lcpEl.tagName === 'IMG' ? (lcpEl.currentSrc || '').slice(-70) : '',
    ttfbMs: Math.round(nav.responseStart || 0),
    perfIstek: kaynak.length + 1,
    perfAktarim: kaynak.reduce((t, r) => t + (r.transferSize || 0), 0) + (nav.transferSize || 0),
    perfTamponDolu: kaynak.length >= 250,
    konum: {
      ustBant: konum('.ust-bant') || konum('header'), serit: konum('.reklam.tam'),
      kategori: konum('.kategori'), h1: konum('h1'),
      spot: konum('article.detay .spot'), kunye: konum('article.detay .detay-kunye'),
      gorsel: konum('article.detay .ana-gorsel'), seslendirme: konum('article.detay .seslendirme'),
      govde: konum('article.detay .metin > *') || konum('article.detay .metin'),
    },
    baslikTam: tam.size, baslikKismi: kismi.size, baslikYer: yerler,
    yuvaIlkEkran: yuvalar.length,
    yuvaDolu: yuvalar.filter(e => e.getAttribute('data-gpt-durum') === 'dolu').length,
    sunum: !!document.querySelector('.reklam-anahtar'),
    vh, vw, temaOdak: getComputedStyle(document.documentElement).getPropertyValue('--tema-odak').trim(),
    reklamTest: document.documentElement.getAttribute('data-reklam-test') || '',
    reklam: document.documentElement.getAttribute('data-reklam') || '',
    adres: location.pathname,
  });
})()
"""

#: Sayfayı aşağı kaydırıp yapışık kalan öğeleri toplar. Yapışık =
#: `position: sticky|fixed`, görünür, görüntü alanıyla kesişiyor. Üst
#: kenara dayananların kapladığı dikey aralıkların BİRLEŞİMİ toplamdır
#: (üst üste binen iki şerit iki kez sayılmaz).
YAPISKAN = r"""
(() => {
  const vh = innerHeight;
  const ust = [], alt = [];
  for (const el of document.querySelectorAll('body *')) {
    const s = getComputedStyle(el);
    if (s.position !== 'sticky' && s.position !== 'fixed') continue;
    if (s.display === 'none' || s.visibility === 'hidden' || parseFloat(s.opacity) === 0) continue;
    const r = el.getBoundingClientRect();
    if (r.width < 1 || r.height < 1 || r.bottom <= 0 || r.top >= vh) continue;
    const ad = el.tagName.toLowerCase() + '.' + ((el.className || '') + '').split(' ')[0] +
               (el.id ? '#' + el.id : '');
    const k = {ad, konum: s.position, ust: Math.round(r.top), alt: Math.round(r.bottom),
               yuk: Math.round(r.height), en: Math.round(r.width)};
    (r.top <= 1 ? ust : alt).push(k);
  }
  const aralik = ust.map(k => [Math.max(k.ust, 0), Math.min(k.alt, vh)]).sort((a, b) => a[0] - b[0]);
  let toplam = 0, bas = -1, son = -1;
  for (const [a, b] of aralik) {
    if (a > son) { if (son > bas) toplam += son - bas; bas = a; son = b; }
    else son = Math.max(son, b);
  }
  if (son > bas) toplam += son - bas;
  return JSON.stringify({kaydirma: Math.round(scrollY), ustToplam: Math.round(toplam), ust, alt, vh});
})()
"""


def _port_bos(port):
    with socket.socket() as s:
        return s.connect_ex(("127.0.0.1", port)) != 0


def _getir(adres, saniye=240):
    istek = urllib.request.Request(adres, headers={"User-Agent": "bh-sayfa-butcesi"})
    with urllib.request.urlopen(istek, timeout=saniye) as y:
        return y.status, y.read()


def _ag_cdp_sinifi():
    """Olay biriktiren `Cdp` alt sınıfı (içe aktarma gecikmeli: modül
    varsayılan turda Django'suz ve websocket'siz yüklenebilsin)."""
    from . import tests_panel_olcum as po

    class AgCdp(po.Cdp):
        """Ağ olaylarını kaçırmayan, okur adını çözen Cdp.

        Üst sınıfın `cagir`/`olay_bekle`'si yanıtı beklerken gelen olayları
        ATIYOR; ağ sayımı için her olay saklanmalı. Chrome iki bayrakla
        açılır: `okur.test` → 127.0.0.1 ve HTTPS yükseltmesi kapalı (yoksa
        `http://okur.test` önce https denenir, fazladan istek/gecikme).
        """

        def __init__(self, kok_port):
            from websocket import create_connection  # noqa: F401  (kurulu mu)
            self.klasor = tempfile.mkdtemp(prefix="bh-butce-chrome-")
            self.port = self._bos_port()
            self.surec = subprocess.Popen([
                po.CHROME, "--headless=new", "--disable-gpu", "--no-first-run",
                "--no-default-browser-check", "--disable-extensions",
                "--disable-background-networking", "--mute-audio",
                "--remote-allow-origins=*",
                f"--host-resolver-rules=MAP {OKUR_ADI} 127.0.0.1",
                "--disable-features=HttpsUpgrades,HttpsFirstBalancedModeAutoEnable",
                f"--remote-debugging-port={self.port}",
                f"--user-data-dir={self.klasor}", "about:blank",
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.ws = self._bagla()
            self._no = 0
            self.olaylar = []

        def _al(self, saniye):
            self.ws.settimeout(max(0.05, saniye))
            try:
                return json.loads(self.ws.recv())
            except Exception:
                return None

        def cagir(self, yontem, **parametre):
            self._no += 1
            no = self._no
            self.ws.send(json.dumps({"id": no, "method": yontem, "params": parametre}))
            bitis = time.time() + 120
            while time.time() < bitis:
                yanit = self._al(bitis - time.time())
                if yanit is None:
                    continue
                if yanit.get("id") == no:
                    if "error" in yanit:
                        raise RuntimeError(f"{yontem}: {yanit['error']}")
                    return yanit.get("result", {})
                if "method" in yanit:
                    self.olaylar.append(yanit)
            raise RuntimeError(f"{yontem}: yanıt gelmedi")

        def pompala(self, saniye):
            bitis = time.time() + saniye
            while time.time() < bitis:
                yanit = self._al(bitis - time.time())
                if yanit and "method" in yanit:
                    self.olaylar.append(yanit)

    return AgCdp


def ag_ozeti(olaylar, kokler):
    """DevTools ağ olaylarından istek sayısı, aktarım, belge baytı, döküm.

    `kokler`: sayfanın kendi kökeni sayılan adresler (dış istek denetimi).
    """
    istekler, bitti, acilmis, tur, adres, yanit, durum = [], {}, {}, {}, {}, {}, {}
    for o in olaylar:
        m, p = o["method"], o.get("params", {})
        if m == "Network.requestWillBeSent":
            u = p["request"]["url"]
            if u.startswith("data:"):
                continue
            istekler.append(p["requestId"])
            tur[p["requestId"]] = p.get("type", "?")
            adres[p["requestId"]] = u
        elif m == "Network.responseReceived":
            r = p["response"]
            basliklar = {k.lower(): v for k, v in (r.get("headers") or {}).items()}
            yanit[p["requestId"]] = (r.get("mimeType", ""), basliklar.get("content-encoding", ""))
            durum[p["requestId"]] = r.get("status", 0)
        elif m == "Network.loadingFinished":
            bitti[p["requestId"]] = p.get("encodedDataLength", 0)
        elif m == "Network.dataReceived":
            acilmis[p["requestId"]] = acilmis.get(p["requestId"], 0) + p.get("dataLength", 0)
    tekil = list(dict.fromkeys(istekler))
    belge = next((r for r in tekil if tur[r] == "Document"), None)
    dokum = {}
    for r in tekil:
        d = dokum.setdefault(tur[r], [0, 0])
        d[0] += istekler.count(r)
        d[1] += bitti.get(r, 0)
    sikistirilmamis = [r for r in tekil if r in bitti and r in yanit
                       and yanit[r][0].startswith(METIN_TURLERI) and not yanit[r][1]]
    return {
        "istek": len(istekler),
        "aktarim": sum(bitti.get(r, 0) for r in tekil),
        "bitmeyen": [adres[r][-60:] for r in tekil if r not in bitti][:5],
        "hatali": [f"{durum[r]} {adres[r][-60:]}" for r in tekil
                   if r in durum and not 200 <= durum[r] < 400][:5],
        "dis": sorted({adres[r] for r in tekil if not adres[r].startswith(tuple(kokler))})[:10],
        "html_aktarim": bitti.get(belge, 0) if belge else 0,
        "html_acilmis": acilmis.get(belge, 0) if belge else 0,
        "dokum": {k: [v[0], round(v[1] / 1024, 1)] for k, v in sorted(dokum.items())},
        "fontlar": sorted(adres[r].rsplit("/", 1)[-1] for r in tekil if tur[r] == "Font"),
        "_sikistirilmamis": sikistirilmamis,
    }


class Olcer:
    """Tek tarayıcı; sayfa × ekran × reklam hâli ölçer.

    `kok`: sunum oturumu kökü (127.0.0.1); okur kökü aynı port, `OKUR_ADI`.
    """

    def __init__(self, kok, goruntu_klasoru=None):
        self.kok = kok
        self.kok_okur = kok.replace("127.0.0.1", OKUR_ADI)
        self.goruntu = Path(goruntu_klasoru) if goruntu_klasoru else None
        if self.goruntu:
            self.goruntu.mkdir(parents=True, exist_ok=True)
        self.cdp = _ag_cdp_sinifi()(kok)
        self.cdp.cagir("Page.enable")
        self.cdp.cagir("Network.enable")
        self.cdp.cagir("Network.setCacheDisabled", cacheDisabled=True)
        self.cdp.cagir("Page.addScriptToEvaluateOnNewDocument", source=GOZLEMCI)

    def kapat(self):
        self.cdp.kapat()

    def degerlendir(self, ifade):
        return self.cdp.cagir("Runtime.evaluate", expression=ifade,
                              returnByValue=True)["result"].get("value")

    def _ekran(self, genislik):
        en, boy, mobil = EKRANLAR[genislik]
        self.cdp.cagir("Emulation.setDeviceMetricsOverride", width=en, height=boy,
                       deviceScaleFactor=1, mobile=mobil)

    def _bosta_bekle(self, yuklendi_mi, sessiz=1.0, azami=25):
        """Ağ `sessiz` sn boşta kalana (ve gerekiyorsa `load` gelene) kadar
        olay topla. Olay listesi çağırandan ÖNCE sıfırlanmış olmalı."""
        bitis = time.time() + azami
        son_hareket = time.time()
        uctaki = set()
        islenen = 0
        yuklendi = not yuklendi_mi
        while time.time() < bitis:
            self.cdp.pompala(0.1)
            for o in self.cdp.olaylar[islenen:]:
                m, p = o["method"], o.get("params", {})
                if m == "Network.requestWillBeSent" and not p["request"]["url"].startswith("data:"):
                    uctaki.add(p["requestId"])
                    son_hareket = time.time()
                elif m in ("Network.loadingFinished", "Network.loadingFailed"):
                    uctaki.discard(p["requestId"])
                    son_hareket = time.time()
                elif m == "Page.loadEventFired":
                    yuklendi = True
            islenen = len(self.cdp.olaylar)
            if yuklendi and not uctaki and time.time() - son_hareket >= sessiz:
                return True
        return False

    def _yukle(self, adres, sessiz=1.0, azami=25):
        self.cdp.olaylar = []
        self.cdp.cagir("Page.navigate", url=adres)
        return self._bosta_bekle(True, sessiz, azami)

    def _kosul_kur(self, kosul):
        """Hâlin kökünü seçer, anahtarları o kökte localStorage'a yazar."""
        sunum, anahtarlar = KOSULLAR[kosul]
        kok = self.kok if sunum else self.kok_okur
        self._yukle(kok + "/_durum", sessiz=0.1, azami=10)
        betik = "".join(
            f"localStorage.removeItem('{a}');" if d is None else f"localStorage.setItem('{a}','{d}');"
            for a, d in anahtarlar.items())
        self.degerlendir(betik + "1")
        return kok

    def kontrol(self):
        """İstek sayacının kendi doğrulaması — bkz. modül başı."""
        self._ekran(1440)
        self._yukle(self.kok + "/_durum", sessiz=0.2, azami=10)
        self.cdp.olaylar = []
        self.degerlendir(
            f"for (let n = 0; n < {KONTROL_GORSEL}; n++) {{ const g = new Image(); "
            f"g.src = '/statik/{KONTROL_DOSYA}?k=' + n + '-' + Date.now(); "
            f"document.body.appendChild(g); }} 1")
        bosta = self._bosta_bekle(False, sessiz=0.5, azami=15)
        o = ag_ozeti(self.cdp.olaylar, [self.kok])
        o["bosta"] = bosta
        return o

    def _uretim_tahmini(self, o):
        """Sıkıştırılmadan gelen metin yanıtlarını gzip -6 ile yeniden say."""
        tasarruf = 0
        for istek in o.pop("_sikistirilmamis"):
            try:
                g = self.cdp.cagir("Network.getResponseBody", requestId=istek)
            except RuntimeError:
                continue
            govde = (base64.b64decode(g["body"]) if g.get("base64Encoded")
                     else g["body"].encode("utf-8"))
            tasarruf += max(0, len(govde) - len(gzip.compress(govde, 6)))
        return o["aktarim"] - tasarruf

    def olc(self, ad, yol, genislik, kosul, goruntu=False):
        self._ekran(genislik)
        kok = self._kosul_kur(kosul)
        tamam = self._yukle(kok + yol)
        time.sleep(0.3)   # geç LCP adayı
        o = json.loads(self.degerlendir(OLCUM))
        o.update(ag_ozeti(self.cdp.olaylar, [kok]))
        o["aktarim_uretim"] = self._uretim_tahmini(o)
        o.update(sayfa=ad, yol=yol, g=genislik, kosul=kosul, bosta=tamam)
        if goruntu and self.goruntu:
            png = self.cdp.cagir("Page.captureScreenshot", format="png")["data"]
            dosya = self.goruntu / f"{ad}-{genislik}-{kosul}.png"
            dosya.write_bytes(base64.b64decode(png))
            o["goruntu"] = str(dosya)
        return o

    def yapiskan(self, yol, genislik, kosul="okur", kaydirma=1600):
        """Sayfayı kaydırıp yapışık öğeleri ölç (ağ ölçümünden SONRA)."""
        self._ekran(genislik)
        kok = self._kosul_kur(kosul)
        self._yukle(kok + yol, sessiz=0.5)
        self.degerlendir(f"window.scrollTo(0, {kaydirma}); 1")
        time.sleep(0.6)
        return json.loads(self.degerlendir(YAPISKAN))


def gecerlilik(o):
    """Ölçümün kendisi geçerli mi? Boş liste = geçerli."""
    sorun = []
    if not o["temaOdak"]:
        sorun.append("stil yüklenmedi")
    if not o["bosta"]:
        sorun.append(f"ağ boşa düşmedi, bitmeyen {o['bitmeyen']}")
    if o["perfTamponDolu"]:
        sorun.append("performance tamponu doldu (250)")
    if abs(o["istek"] - o["perfIstek"]) > 1:
        sorun.append(f"istek: DevTools {o['istek']} ≠ performance {o['perfIstek']}")
    if o["perfAktarim"] and abs(o["aktarim"] - o["perfAktarim"]) > 0.1 * o["aktarim"]:
        sorun.append(f"aktarım: DevTools {o['aktarim']} ≠ performance {o['perfAktarim']}")
    sunum = KOSULLAR[o["kosul"]][0]
    if o["sunum"] != sunum:
        sorun.append(f"sunum düğmesi {'yok' if sunum else 'var'} (hâl kurulmadı)")
    beklenen = "acik" if o["kosul"] == "acik" else ""
    if o["reklamTest"] != beklenen:
        sorun.append(f"reklam-test hâli {o['reklamTest']!r}, beklenen {beklenen!r}")
    if (o["reklam"] == "kapali") != (o["kosul"] == "gizli"):
        sorun.append(f"reklam anahtarı {o['reklam']!r}")
    return sorun


def butce_bulgulari(o, istek=None, aktarim=None, lcp=None, html=None):
    """Birleştirilmiş tek ölçümü tavanlarla karşılaştırır. Boş liste = bütçede.

    Tavanlar parametreyle verilebilir. Karşılaştırmanın gerçekten yakaladığı
    sınandı (20 Ekim 2026, kaydedilmiş ölçümle): tavan "ölçülen − 1"
    yapılınca istek, aktarım, HTML ve LCP denetimlerinin HER BİRİ 16 tavanlı
    hâlin 16'sında bulgu üretti; gerçek tavanlarla 0. Yapışkan ölçer de
    okur sayfasına enjekte edilen 60 px'lik sabit alt şeridi yakaladı
    (82 + 60 = 142 > 90)."""
    istek = ISTEK_TAVAN if istek is None else istek
    aktarim = AKTARIM_TAVAN_KB if aktarim is None else aktarim
    lcp = LCP_TAVAN_MS if lcp is None else lcp
    html = HTML_TAVAN_KB if html is None else html
    ad, g, kosul = o["sayfa"], o["g"], o["kosul"]
    on = f"{ad} @{g} reklam={kosul}"
    b = []
    if o["dis"]:
        b.append(f"{on}: dış istek {o['dis']}")
    if o["hatali"]:
        b.append(f"{on}: başarısız yanıt {o['hatali']}")
    if o["cls"] > CLS_TAVAN:
        b.append(f"{on}: CLS {o['cls']} {o['kaymalar']}")
    if o["lcpLoading"] == "lazy":
        b.append(f"{on}: LCP görseli lazy ({o['lcpSrc']})")
    if kosul not in TAVAN_KOSULLARI:
        return b
    anahtar = (ad, g, kosul)
    if o["istek"] > istek[anahtar]:
        b.append(f"{on}: {o['istek']} istek > {istek[anahtar]} {o['dokum']}")
    if o["aktarim"] / 1024 > aktarim[anahtar]:
        b.append(f"{on}: aktarım {o['aktarim'] / 1024:.0f} KB > {aktarim[anahtar]} {o['dokum']}")
    if o["lcpMs"] > lcp:
        b.append(f"{on}: LCP {o['lcpMs']} ms > {lcp} (turlar {o['lcpTurlar']}, {o['lcpEtiket']})")
    acilmis, gz = html[ad]
    if o["html_acilmis"] / 1024 > acilmis or o["html_aktarim"] / 1024 > gz:
        b.append(f"{on}: HTML {o['html_acilmis'] / 1024:.0f} KB / gzip "
                 f"{o['html_aktarim'] / 1024:.0f} KB > {acilmis} / {gz}")
    return b


def birlestir(turlar):
    """Aynı sayfanın tekrarları: sayım ve baytta en kötü, LCP'de ortanca."""
    ilk = dict(turlar[0])
    for anahtar in ("istek", "aktarim", "aktarim_uretim", "html_aktarim", "html_acilmis", "cls"):
        ilk[anahtar] = max(t[anahtar] for t in turlar)
    ilk["lcpMs"] = int(statistics.median(t["lcpMs"] for t in turlar))
    ilk["lcpTurlar"] = [t["lcpMs"] for t in turlar]
    ilk["istekTurlar"] = [t["istek"] for t in turlar]
    return ilk


def sayfalari_bul(kok):
    """Detay: `BH_SAYFA_BUTCESI_DETAY` > `DETAY_VARSAYILAN` > manşetin ilk haberi."""
    detay = os.environ.get("BH_SAYFA_BUTCESI_DETAY") or DETAY_VARSAYILAN
    try:
        _getir(kok + detay)
    except urllib.error.HTTPError:
        _, ana = _getir(kok + "/")
        ana = ana.decode("utf-8", "replace")
        parca = ana.split('class="slayt-kap manset-slayt"', 1)[-1]
        detay = next((h for h in re.findall(r'href="(/[a-z0-9-]+/[^"#?/]+-\d+)"', parca)
                      if not h.startswith(("/yazarlar/", "/ilce/", "/konu/"))), None)
        if not detay:
            raise RuntimeError("detay adresi bulunamadı")
        print(f"UYARI: {DETAY_VARSAYILAN} yok; detay {detay} — HTML/aktarım tavanı "
              "başka makale için konmuştu.")
    return [("anasayfa", "/"), ("ekonomi", "/ekonomi"), ("detay", detay),
            ("ilce", "/ilce/osmangazi")]


def tablo(sonuc):
    satir = [f"{'sayfa':9}{'g':>5} {'reklam':7}{'istek':>6}{'KB':>6}{'~üret':>6}{'LCP':>6}"
             f"{'CLS':>7}{'HTML':>7}{'gzip':>6}{'TTFB':>6}{'başlık':>7}{'yuva':>5}"
             f"{'h1':>6}{'spot':>6}{'gövde':>6}  lcp öğesi"]
    for o in sonuc:
        k = o["konum"]
        y = lambda a: (k.get(a) or {}).get("ust", "")  # noqa: E731
        satir.append(
            f"{o['sayfa']:9}{o['g']:>5} {o['kosul']:7}{o['istek']:>6}"
            f"{o['aktarim'] / 1024:>6.0f}{o['aktarim_uretim'] / 1024:>6.0f}{o['lcpMs']:>6}"
            f"{o['cls']:>7}{o['html_acilmis'] / 1024:>7.1f}{o['html_aktarim'] / 1024:>6.1f}"
            f"{o['ttfbMs']:>6}{str(o['baslikTam']) + '+' + str(o['baslikKismi']):>7}"
            f"{o['yuvaIlkEkran']:>5}{y('h1'):>6}{y('spot'):>6}{y('govde'):>6}  {o['lcpEtiket']}")
    return "\n".join(satir)


if os.environ.get("BH_SAYFA_BUTCESI") == "1":

    from django.test import SimpleTestCase

    class SayfaButcesi(SimpleTestCase):
        databases = set()
        PORT = int(os.environ.get("BH_SAYFA_BUTCESI_PORT", "8755"))
        TUR = int(os.environ.get("BH_SAYFA_BUTCESI_TUR", "3"))

        @classmethod
        def setUpClass(cls):
            super().setUpClass()
            if not (os.environ.get("BH_SQLITE_YOLU") or os.environ.get("BH_VERITABANI")):
                raise RuntimeError("BH_VERITABANI ya da salt okunur BH_SQLITE_YOLU ver: "
                                   "bütçe gerçek veriye karşı ölçülür.")
            if not _port_bos(cls.PORT):
                raise RuntimeError(f"Port {cls.PORT} dolu — eski süreç olabilir "
                                   f"(netstat -ano | findstr :{cls.PORT}).")
            cls.onbellek = tempfile.mkdtemp(prefix="bh-butce-onbellek-")
            ortam = dict(os.environ, BH_ORTAM="gelistirme", BH_HATA_AYIKLA="1",
                         BH_ONBELLEK_KOK=cls.onbellek, PYTHONIOENCODING="utf-8",
                         BH_REKLAM_DEMO="0", BH_REKLAM_TEST="1",
                         BH_SUNUCU_ADLARI=f"127.0.0.1,localhost,{OKUR_ADI}")
            for ad in ("BH_SAYFA_BUTCESI", "BH_ADSENSE_ID"):
                ortam.pop(ad, None)
            cls.gunluk = open(Path(cls.onbellek) / "sunucu.log", "w", encoding="utf-8")
            cls.sunucu = subprocess.Popen(
                [sys.executable, "manage.py", "runserver", f"127.0.0.1:{cls.PORT}",
                 "--noreload"],
                cwd=str(Path(__file__).resolve().parent.parent), env=ortam,
                stdout=cls.gunluk, stderr=subprocess.STDOUT)
            cls.kok = f"http://127.0.0.1:{cls.PORT}"
            cls.olcer = None
            try:
                cls._sunucuyu_bekle()
                cls.sayfalar = sayfalari_bul(cls.kok)
                for _, yol in cls.sayfalar:          # ısıtma — bkz. modül başı
                    _getir(cls.kok + yol)
                cls.olcer = Olcer(cls.kok, os.environ.get("BH_SAYFA_BUTCESI_GORUNTU"))
            except Exception:
                cls._kapat()
                raise

        @classmethod
        def _kapat(cls):
            if getattr(cls, "olcer", None):
                cls.olcer.kapat()
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
                    raise RuntimeError("sunucu açılmadı; günlük: " + (
                        Path(cls.onbellek) / "sunucu.log").read_text("utf-8")[-2000:])
                try:
                    if _getir(cls.kok + "/_durum", 5)[0] == 200:
                        return
                except Exception:
                    time.sleep(0.5)
            raise RuntimeError("sunucu 240 sn içinde yanıt vermedi")

        def test_1_sayac_kontrol_sayfasini_dogru_sayiyor(self):
            o = self.olcer.kontrol()
            boy = (Path(__file__).resolve().parent.parent / "statik" / KONTROL_DOSYA).stat().st_size
            self.assertTrue(o["bosta"], o)
            self.assertFalse(o["hatali"], o)
            self.assertEqual(o["istek"], KONTROL_GORSEL, o)
            self.assertFalse(o["bitmeyen"], o)
            self.assertGreaterEqual(o["aktarim"], KONTROL_GORSEL * boy, o)
            self.assertLess(o["aktarim"], KONTROL_GORSEL * (boy + 2000), o)

        def test_2_butce(self):
            sonuc, bulgular = [], []
            for ad, yol in self.sayfalar:
                for g in EKRANLAR:
                    for kosul in KOSULLAR:
                        turlar = [self.olcer.olc(ad, yol, g, kosul, goruntu=(n == 0))
                                  for n in range(self.TUR)]
                        o = birlestir(turlar)
                        sonuc.append(o)
                        for t in turlar:
                            bulgular += [f"{ad} @{g} reklam={kosul}: ölçüm geçersiz — {s}"
                                         for s in gecerlilik(t)]
                        bulgular += butce_bulgulari(o)
            type(self)._sonuc = sonuc
            self._rapor(sonuc, bulgular)
            self.assertEqual(bulgular, [], "\n" + "\n".join(bulgular))

        def test_3_390_yapiskan_toplam(self):
            """Kaydırırken ekranda kalan yapışık şeritlerin toplamı (üst
            birleşim + alttakiler) okur hâlinde ve test reklamı açıkken."""
            for ad, yol in self.sayfalar:
                for kosul in TAVAN_KOSULLARI:
                    with self.subTest(sayfa=ad, reklam=kosul):
                        y = self.olcer.yapiskan(yol, 390, kosul)
                        toplam = y["ustToplam"] + sum(k["yuk"] for k in y["alt"])
                        self.assertLessEqual(toplam, YAPISKAN_TAVAN_PX, y)

        def test_4_ilk_ekran_alt_siniri(self):
            """Bugünkü ilk ekranın ALT SINIRI — tasarım kararı değil.

            Anasayfada ilk ekranda en az şu kadar başlık tam görünür; detayda
            H1'in alt kenarı ilk ekranda. Şerit/yerleşim kararı
            `web-tasarim-direktoru`nün; bu test yalnız sessizce kötüleşmeyi
            yakalar."""
            sonuc = getattr(type(self), "_sonuc", None)
            if not sonuc:
                self.skipTest("test_2 ölçümü yok")
            for o in sonuc:
                if o["kosul"] not in TAVAN_KOSULLARI:
                    continue
                with self.subTest(sayfa=o["sayfa"], g=o["g"], reklam=o["kosul"]):
                    if o["sayfa"] == "anasayfa":
                        self.assertGreaterEqual(o["baslikTam"], ILK_EKRAN_BASLIK_ALT[o["g"]], o["baslikYer"])
                    if o["sayfa"] == "detay":
                        self.assertLessEqual(o["konum"]["h1"]["alt"], o["vh"], o["konum"])

        @unittest.expectedFailure
        def test_5_sembol_fontlari_inmiyor(self):
            """BİLİNEN KUSUR (20 Ekim 2026) → `frontend-gelistirici`.

            Her sayfa `roboto-math.woff2` (41 KB) ve `roboto-symbols.woff2`
            (21 KB) indiriyor; tetikleyen yalnız iki-üç glif: menü simgesi
            ☰ (U+2630), "Tümü →" (U+2192, iki dosyanın aralığında birden) ve
            döviz bandındaki ▲▼ (U+25B2/25BC). Okur başına 62 KB + 2 istek.
            Düzelince bu test "beklenmeyen başarı" verir: dekoratörü kaldır."""
            sonuc = getattr(type(self), "_sonuc", None)
            if not sonuc:
                self.skipTest("test_2 ölçümü yok")
            inen = sorted({f"{o['sayfa']}@{o['g']}" for o in sonuc
                           if any(f.startswith(("roboto-math", "roboto-symbols"))
                                  for f in o["fontlar"])})
            self.assertEqual(inen, [])

        def _rapor(self, sonuc, bulgular):
            cikti = os.environ.get("BH_SAYFA_BUTCESI_CIKTI")
            if cikti:
                Path(cikti).write_text(json.dumps({"sonuc": sonuc, "bulgular": bulgular},
                                                  ensure_ascii=False, indent=1),
                                       encoding="utf-8")
            print("\n" + tablo(sonuc))
            sys.stdout.flush()
