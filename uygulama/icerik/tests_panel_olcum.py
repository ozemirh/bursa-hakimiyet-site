"""Panel yerleşim ölçümü — başsız Chrome, DevTools protokolü.

**Tahmin değil ölçüm.** Yatay taşma, sayfa başına `h1` sayısı ve odak halkası
olmayan odaklanabilir öğe sayısı gerçek bir tarayıcıda, gerçek bir sunucuya
karşı ölçülür.

Çalıştırma (varsayılan test turunda **hiç yüklenmez**, Chrome gerektirir):

    set BH_PANEL_OLCUM=1
    python manage.py test icerik.tests_panel_olcum -v 2

Neden koşullu: ölçüm Chrome'a bağlı ve saniyeler sürüyor; `manage.py test`in
her koşusunda çalışması gereken bir birim testi değil. Ama ayrı bir betik de
değil — kendi test veritabanını ve canlı sunucusunu test çatısından alıyor.

## Ölçüm aracının kendisi de doğrulanmalı

`URUN-PLANI.md` §12 ve §14 kayda geçirdi: bu araç **üç kez** yanlış rapor
verdi. Biri önbellekti — düzeltilmiş CSS görülmüyordu. Bu yüzden burada
`Network.setCacheDisabled` **her sayfada** çağrılıyor ve ölçüm, bilerek
bozulmuş bir kontrol sayfasıyla (`test_olcer_gercekten_tasmayi_goruyor`)
çapraz kontrol ediliyor: araç taşmayı görmüyorsa "taşma 0" sonucu da
değersizdir.
"""

import json
import os
import shutil
import socket
import subprocess
import tempfile
import time
import urllib.request

CHROME = os.environ.get(
    "BH_CHROME", r"C:\Program Files\Google\Chrome\Application\chrome.exe")

# Ölçüm genişlikleri. 620 · 880 panel.css'in kendi kırılma noktaları;
# 360 · 768 · 1024 · 1280 · 1600 faz ölçütünün istediği beş genişlik.
GENISLIKLER = [360, 620, 768, 880, 1024, 1280, 1600]

# Taşma ölçümünden ayıklanacak kutular: kendi `overflow-x:auto` kabında
# kayan geniş tablolar sayfayı taşırmaz (PANEL-NOTLARI.md §21).
OLCUM_BETIGI = r"""
(() => {
  const de = document.documentElement;
  const tasma = de.scrollWidth - de.clientWidth;

  const kayanKapta = (el) => {
    for (let p = el.parentElement; p; p = p.parentElement) {
      const s = getComputedStyle(p);
      if (s.overflowX === 'auto' || s.overflowX === 'scroll') return true;
    }
    return false;
  };

  const tasanlar = [];
  if (tasma > 0) {
    for (const el of document.querySelectorAll('body *')) {
      const k = el.getBoundingClientRect();
      if (k.width === 0 && k.height === 0) continue;
      if (k.right > de.clientWidth + 1 && !kayanKapta(el)) {
        tasanlar.push(el.tagName.toLowerCase() + '.' +
                      (el.className || '').toString().split(' ')[0] +
                      ' sag=' + Math.round(k.right));
      }
    }
  }

  const odaklanabilir = [...document.querySelectorAll(
    'a[href], button, input:not([type=hidden]), select, textarea, [tabindex]')]
    .filter(el => !el.disabled && el.offsetParent !== null);

  const halkasiz = [];
  for (const el of odaklanabilir) {
    el.focus();
    const s = getComputedStyle(el);
    const halka = (s.outlineStyle !== 'none' && parseFloat(s.outlineWidth) > 0)
                  || (s.boxShadow && s.boxShadow !== 'none');
    if (!halka) {
      halkasiz.push(el.tagName.toLowerCase() + '.' +
                    (el.className || '').toString().split(' ')[0]);
    }
  }
  if (document.activeElement) document.activeElement.blur();

  const altsiz = [...document.images].filter(g => !g.alt).length;
  const disKaynak = [...document.querySelectorAll('[src],[href]')]
    .map(e => e.getAttribute('src') || e.getAttribute('href'))
    .filter(u => u && /^https?:\/\//.test(u) &&
                 !u.startsWith('https://fonts.googleapis.com') &&
                 !u.startsWith('https://fonts.gstatic.com')).length;

  const kenar = document.querySelector('.kenar');
  const h1 = document.querySelector('h1');

  return JSON.stringify({
    tasma, tasanlar,
    h1sayi: document.querySelectorAll('h1').length,
    h1metin: h1 ? h1.textContent.trim() : '',
    odaklanabilir: odaklanabilir.length,
    halkasiz,
    altsiz, disKaynak,
    genislik: de.clientWidth,
    // --- ölçüm aracının kendi doğrulaması ---
    // CSS yüklenmediyse sayfa çıplak akar, taşma da olmaz ve ölçüm
    // "temiz" görünür. Bu üç alan onu yakalar.
    zemin: getComputedStyle(document.body).backgroundColor,
    kenarZemin: kenar ? getComputedStyle(kenar).backgroundColor : '',
    kenarGenislik: kenar ? Math.round(kenar.getBoundingClientRect().width) : 0,
    // Google Fonts gercekten geldi mi. Gelmediyse "font engelli" turu ile
    // normal tur ayni seyi olcer ve testin kendisi anlamsizlasir.
    yuzSayisi: document.fonts ? document.fonts.size : -1,
    yuzler: document.fonts
      ? [...new Set([...document.fonts].map(f => f.family))].sort() : [],
    satir: document.querySelectorAll('table.liste tbody tr').length,
  });
})()
"""


class Cdp:
    """Küçük DevTools protokolü istemcisi.

    Selenium/Playwright kurmamak için: `canli-veri/` ve `disa-aktarim/`
    tarafındaki "saf standart kütüphane + kurulu Chrome" düzeniyle aynı
    yaklaşım. Tek dış paket `websocket-client`, o da ortamda zaten var.
    """

    def __init__(self):
        from websocket import create_connection  # noqa: F401  (kurulu mu)
        self.klasor = tempfile.mkdtemp(prefix="bh-olcum-")
        self.port = self._bos_port()
        self.surec = subprocess.Popen([
            CHROME, "--headless=new", "--disable-gpu", "--no-first-run",
            "--no-default-browser-check", "--disable-extensions",
            "--disable-background-networking", "--mute-audio",
            # Chrome 111'den beri DevTools soketi Origin denetliyor;
            # websocket-client `http://127.0.0.1:<port>` Origin'i gönderiyor
            # ve bayrak olmadan el sıkışma 403 dönüyor.
            "--remote-allow-origins=*",
            f"--remote-debugging-port={self.port}",
            f"--user-data-dir={self.klasor}", "about:blank",
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.ws = self._bagla()
        self._no = 0

    @staticmethod
    def _bos_port() -> int:
        with socket.socket() as s:
            s.bind(("127.0.0.1", 0))
            return s.getsockname()[1]

    def _bagla(self):
        from websocket import create_connection
        son = None
        for _ in range(120):
            try:
                with urllib.request.urlopen(
                        f"http://127.0.0.1:{self.port}/json/list", timeout=1) as y:
                    hedefler = json.loads(y.read().decode())
                sayfa = [h for h in hedefler if h.get("type") == "page"]
                if sayfa:
                    return create_connection(sayfa[0]["webSocketDebuggerUrl"],
                                             timeout=30)
            except Exception as hata:      # Chrome henüz açılmadı
                son = hata
            time.sleep(0.25)
        raise RuntimeError(f"Chrome DevTools ucuna bağlanılamadı: {son}")

    def cagir(self, yontem, **parametre):
        self._no += 1
        self.ws.send(json.dumps({"id": self._no, "method": yontem,
                                 "params": parametre}))
        while True:
            yanit = json.loads(self.ws.recv())
            if yanit.get("id") == self._no:
                if "error" in yanit:
                    raise RuntimeError(f"{yontem}: {yanit['error']}")
                return yanit.get("result", {})

    def olay_bekle(self, ad, saniye=20):
        bitis = time.time() + saniye
        while time.time() < bitis:
            self.ws.settimeout(max(0.5, bitis - time.time()))
            try:
                yanit = json.loads(self.ws.recv())
            except Exception:
                continue
            if yanit.get("method") == ad:
                return True
        return False

    def kapat(self):
        try:
            self.ws.close()
        except Exception:
            pass
        self.surec.terminate()
        try:
            self.surec.wait(timeout=10)
        except Exception:
            self.surec.kill()
        shutil.rmtree(self.klasor, ignore_errors=True)


if os.environ.get("BH_PANEL_OLCUM") == "1":

    from django.contrib.auth.models import Group, User
    from django.contrib.staticfiles.testing import StaticLiveServerTestCase
    from django.core.management import call_command
    from django.utils import timezone

    from medya.models import FotoGaleri, KoseYazisi, Video, Yazar
    from taksonomi.models import Etiket, Kategori, KategoriTur, Kaynak

    from .models import Haber

    class PanelYerlesimOlcumu(StaticLiveServerTestCase):
        """Bütün panel ekranları × yedi genişlik."""

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
            simdi = timezone.now()

            self.yonetmen = User.objects.create_user(
                "yonetmen", password="olcum-parola-123",
                first_name="Yayın", last_name="Yönetmeni")
            self.yonetmen.groups.add(Group.objects.get(name="Yayın Yönetmeni"))

            kategori = KategoriTur.objects.get(
                tur=Kategori.TUR_HABER, slug="gundem").kategori
            Etiket.objects.create(ad="Etiket", slug="etiket")

            # Uzun başlıklar bilerek: taşmayı en çok zorlayan şey uzun
            # kesintisiz metindir, kısa örnekle ölçüm yanıltıcı olur.
            uzun = ("Bursa Büyükşehir Belediyesi'nin Nilüfer Çayı "
                    "kirliliğine karşı yürüttüğü çalışmalarda yeni aşama")
            for sira in range(12):
                Haber.objects.create(
                    id=990000 + sira, slug=f"olcum-{sira}",
                    baslik=f"{uzun} {sira}", kategori=kategori,
                    durum=Haber.DURUM_AKTIF, yayin_zamani=simdi,
                    olusturan=self.yonetmen)

            self.yazar = Yazar.objects.create(
                id=991, slug="olcum-yazari", ad="Ölçüm Yazarı",
                unvan="Köşe yazarı", sayfasi_tarandi=False)
            for sira in range(6):
                KoseYazisi.objects.create(
                    id=992000 + sira, slug=f"olcum-yazi-{sira}",
                    baslik=f"{uzun} {sira}", yazar=self.yazar,
                    kategori=kategori, yayin_zamani=simdi)

            foto = KategoriTur.objects.filter(tur=Kategori.TUR_FOTO).first()
            video = KategoriTur.objects.filter(tur=Kategori.TUR_VIDEO).first()
            for sira in range(6):
                FotoGaleri.objects.create(
                    id=993000 + sira, slug=f"olcum-galeri-{sira}",
                    baslik=f"{uzun} {sira}", kategori=foto.kategori,
                    kategori_dilimi=foto.adres_dilimi, yayin_zamani=simdi)
                Video.objects.create(
                    id=994000 + sira, slug=f"olcum-video-{sira}",
                    baslik=f"{uzun} {sira}", kategori=video.kategori,
                    kategori_dilimi=video.adres_dilimi, sure_saniye=125,
                    yayin_zamani=simdi)

            # Kaynaklar ekranı: dört ölçülmüş bozukluk biçimi + bir temiz
            # kayıt. Uzun ad bilerek var — tespit sütunu en genişleyen sütun.
            for ad in ("Sözcü", "525218", "aktarildi",
                       "MHP Genel Başkanı Bahçeli grup toplantıs",
                       "Bursa Hakimiyet"):
                Kaynak.objects.create(ad=ad)
            self.kaynak = Kaynak.objects.get(ad="Sözcü")

            # Manşetler ekranı için üç slotu da doldur (§14).
            for kimlik, alan in ((990000, "manset_ana"),
                                 (990001, "manset_tepe"),
                                 (990002, "manset_kare")):
                Haber.objects.filter(pk=kimlik).update(**{alan: True})

            self.kategori = kategori
            self.spor = KategoriTur.objects.get(
                tur=Kategori.TUR_HABER, slug="spor").kategori
            self.haber = Haber.objects.get(pk=990000)
            self.yazi = KoseYazisi.objects.get(pk=992000)
            self.galeri = FotoGaleri.objects.get(pk=993000)
            self.video = Video.objects.get(pk=994000)

            self.client.force_login(self.yonetmen)
            self.oturum = self.client.cookies["sessionid"].value

        # -- yardımcılar ------------------------------------------------

        def _sayfalar(self):
            """(ad, yol, beklenen h1, en az kaç tablo satırı olmalı).

            Beklenen `h1` metni bilerek var: oturum çerezi işlemezse bütün
            adresler giriş sayfasına düşer ve ölçüm 18 kez aynı sayfayı
            ölçüp "hepsi temiz" der. Bu sütun o sessiz yanılmayı kapatıyor.
            """
            return [
                ("Giriş", "/panel/giris", "Yönetim Paneli", 0),
                ("Bugün", "/panel/", "Bugün", 0),
                ("Tüm Haberler", "/panel/akis", "Tüm haberler", 12),
                ("Haber ekle", "/panel/haber/ekle", "Haber ekle", 0),
                ("Haber düzenle", f"/panel/haber/{self.haber.pk}",
                 self.haber.baslik, 0),
                ("Manşetler", "/panel/mansetler", "Manşetler", 3),
                ("Köşe Yazıları", "/panel/kose", "Köşe yazıları", 6),
                ("Köşe yazısı düzenle", f"/panel/kose/{self.yazi.pk}",
                 self.yazi.baslik, 0),
                ("Köşe Yazarları", "/panel/yazarlar", "Köşe yazarları", 1),
                ("Yazar düzenle", f"/panel/yazar/{self.yazar.pk}",
                 self.yazar.ad, 0),
                ("Foto Galeri", "/panel/galeriler", "Foto galeri", 6),
                ("Galeri düzenle", f"/panel/galeri/{self.galeri.pk}",
                 self.galeri.baslik, 0),
                ("Videolar", "/panel/videolar", "Videolar", 6),
                ("Video düzenle", f"/panel/video/{self.video.pk}",
                 self.video.baslik, 0),
                ("Kategoriler", "/panel/kategoriler", "Kategoriler", 13),
                ("Kategori düzenle", f"/panel/kategori/{self.kategori.pk}",
                 self.kategori.ad, 0),
                ("Kullanıcılar", "/panel/kullanicilar", "Kullanıcılar", 1),
                ("Kullanıcı düzenle", f"/panel/kullanici/{self.yonetmen.pk}",
                 "Yayın Yönetmeni", 0),
                ("Kaynaklar", "/panel/kaynaklar", "Kaynaklar", 4),
                ("Kaynak düzenle", f"/panel/kaynak/{self.kaynak.pk}",
                 self.kaynak.ad, 0),
                ("Roller", "/panel/roller", "Roller", 0),
                ("Şifre", "/panel/sifre", "Şifre", 0),
            ]

        def _hazirla(self):
            cdp = self.cdp
            cdp.cagir("Page.enable")
            cdp.cagir("Runtime.enable")
            cdp.cagir("Network.enable")
            # ÖNBELLEK KAPALI. Bu satır olmadığı için araç daha önce
            # düzeltilmiş CSS'i görmeyip üç kez yanlış rapor verdi.
            cdp.cagir("Network.setCacheDisabled", cacheDisabled=True)
            cdp.cagir("Network.clearBrowserCookies")

        def _oturum_ac(self):
            """Çerezi sonradan koyuyoruz.

            Sebep ölçülerek bulundu: `LoginView` `redirect_authenticated_user`
            ile kurulu, yani oturum açıkken `/panel/giris` **yönlendiriyor**.
            Çerez baştan konsaydı ölçer giriş sayfası yerine Bugün ekranını
            ölçüp ona "Giriş" adını yazacaktı — sessiz bir yanılma.
            """
            kok = self.live_server_url.split("//")[1].split(":")[0]
            self.cdp.cagir("Network.setCookie", name="sessionid",
                           value=self.oturum, domain=kok, path="/")

        def _klavye_hazirla(self):
            """Tarayıcıya "son etkileşim klavyeydi" dedirtir.

            `:focus-visible` düğme ve bağlantılarda ancak böyle eşleşir;
            bu adım atlanırsa ölçer **her** öğeyi "odak halkası yok" diye
            raporlar. Onay ekranı ölçümünde tam olarak bu oldu: aynı CSS ve
            aynı öğeler 154 ölçümde temizken burada 7/7 bulgu verdi. Hata
            sayfada değil, ölçüm yolundaydı — bu yüzden hazırlık tek bir
            yere alındı, iki ayrı kopya olarak durmuyor.
            """
            for tur in ("rawKeyDown", "keyUp"):
                self.cdp.cagir("Input.dispatchKeyEvent", type=tur,
                               windowsVirtualKeyCode=9, key="Tab", code="Tab")

        def _git(self, yol, genislik):
            """Yalnız açar. Ölçümden ayrı tutuluyor.

            Sebep ölçülerek bulundu: `OLCUM_BETIGI` her odaklanabilir öğeye
            `focus()` uyguluyor ve bu, `.tablo-kaydir` kutusunu **sağa
            kaydırıyor**. Ekran görüntüsü ölçümden sonra alınınca tablo
            kaymış görünüyor ve olmayan bir yerleşim hatası sanılıyor.
            """
            cdp = self.cdp
            cdp.cagir("Emulation.setDeviceMetricsOverride",
                      width=genislik, height=900, deviceScaleFactor=1,
                      mobile=False)
            cdp.cagir("Page.navigate", url=self.live_server_url + yol)
            cdp.olay_bekle("Page.loadEventFired")

        def _post_ile_ac(self, yol, alanlar, genislik):
            """POST ile açılan ekranı ölçmek için: sayfaya bir form basıp
            gönderiyoruz. Onay ekranı yalnız POST'la geliyor ve ölçüm
            dışında kalması, en riskli ekranın ölçülmemesi demekti."""
            self._git("/panel/akis", genislik)
            girdiler = "".join(
                f"<input name='{ad}' value='{deger}'>" for ad, deger in alanlar)
            betik = (
                "(() => { const f = document.createElement('form');"
                "f.method='post'; f.action='" + yol + "';"
                "f.innerHTML = `" + girdiler + "` +"
                " document.querySelector('[name=csrfmiddlewaretoken]').outerHTML;"
                "document.body.appendChild(f); f.submit(); })()")
            self.cdp.cagir("Runtime.evaluate", expression=betik)
            self.cdp.olay_bekle("Page.loadEventFired")
            self._klavye_hazirla()

        def _olc(self, yol, genislik):
            cdp = self.cdp
            self._git(yol, genislik)
            self._klavye_hazirla()
            sonuc = cdp.cagir("Runtime.evaluate", expression=OLCUM_BETIGI,
                              returnByValue=True, awaitPromise=True)
            return json.loads(sonuc["result"]["value"])

        # -- ölçümler ---------------------------------------------------

        def test_olcer_gercekten_tasmayi_goruyor(self):
            """Aracın kendi doğrulaması.

            Bilerek 4000 px genişliğinde bir kutu basan bir sayfa açılıyor;
            ölçer bunu görmüyorsa "taşma 0" sonucu hiçbir şey söylemez.
            """
            self._hazirla()
            self.cdp.cagir("Emulation.setDeviceMetricsOverride",
                           width=1024, height=900, deviceScaleFactor=1,
                           mobile=False)
            self.cdp.cagir("Page.navigate", url="data:text/html,<body>"
                           "<div style='width:4000px;height:20px'></div>")
            self.cdp.olay_bekle("Page.loadEventFired")
            sonuc = self.cdp.cagir("Runtime.evaluate",
                                   expression=OLCUM_BETIGI,
                                   returnByValue=True)
            olcum = json.loads(sonuc["result"]["value"])
            self.assertGreater(olcum["tasma"], 2000,
                               "Ölçer taşmayı görmüyor; sonuçlar geçersiz.")
            self.assertTrue(olcum["tasanlar"])

        def test_kutu_kenarlari(self):
            """Kutu kenarlarının sayısal dökümü — göz kararının doğrulanması.

            Ekran görüntüsünde "süzgeç kutusu sağ kenardan taşıyor gibi"
            görünüyordu. Göz yanılabilir; kenarlar ölçülüyor.
            """
            betik = os.environ.get("BH_OLCUM_BETIK")
            if not betik:
                self.skipTest("BH_OLCUM_BETIK verilmedi")
            with open(betik, encoding="utf-8") as dosya:
                kod = dosya.read()
            self._hazirla()
            self._oturum_ac()
            for yol in ("/panel/galeriler", "/panel/kullanicilar"):
                for genislik in (360, 620, 1024, 1600):
                    self._git(yol, genislik)
                    sonuc = self.cdp.cagir("Runtime.evaluate", expression=kod,
                                           returnByValue=True)
                    print(f"\n{yol} @{genislik}")
                    for ad, kutu in json.loads(
                            sonuc["result"]["value"]).items():
                        print("  ", ad, kutu)

        def test_ekran_goruntusu_al(self):
            """Sayısal ölçümün gözle çapraz kontrolü.

            Ölçer "taşma 0" diyorsa yerleşim doğru **görünüyor** demek
            değildir; §14'te kaydedilen üç yanılmanın ikisi ancak ekran
            görüntüsüne bakılınca çıktı. Görüntüler `BH_OLCUM_KLASOR`
            verilirse oraya yazılır.
            """
            klasor = os.environ.get("BH_OLCUM_KLASOR")
            if not klasor:
                self.skipTest("BH_OLCUM_KLASOR verilmedi")
            self._hazirla()
            self._oturum_ac()
            import base64
            # Onay ekrani POST'la aciliyor; once onu al.
            kimlikler = list(Haber.objects.values_list("pk", flat=True)[:6])
            alanlar = [("fiil", "kategori"),
                       ("kategori_degeri", self.spor.pk)]
            alanlar += [("kimlikler", k) for k in kimlikler]
            for genislik in (360, 1280):
                self._post_ile_ac("/panel/toplu", alanlar, genislik)
                veri = self.cdp.cagir("Page.captureScreenshot", format="png",
                                      captureBeyondViewport=True)
                yol_disk = os.path.join(klasor, f"toplu-onay-{genislik}.png")
                with open(yol_disk, "wb") as dosya:
                    dosya.write(base64.b64decode(veri["data"]))
                print("görüntü:", yol_disk)

            for ad, yol in [("akis-toplu", "/panel/akis"),
                            ("kaynaklar", "/panel/kaynaklar")]:
                for genislik in (360, 1280):
                    self._git(yol, genislik)
                    veri = self.cdp.cagir("Page.captureScreenshot",
                                          format="png",
                                          captureBeyondViewport=True)
                    yol_disk = os.path.join(klasor, f"{ad}-{genislik}.png")
                    with open(yol_disk, "wb") as dosya:
                        dosya.write(base64.b64decode(veri["data"]))
                    print("görüntü:", yol_disk)

        def test_font_engellendiginde_de_tasma_yok(self):
            """Google Fonts gelmezse yerleşim bozulmamalı.

            Panel 27 Ağustos'ta Google Fonts'a bağlandı. Şart: her yüzün
            arkasında gerçek bir yedek yığını olacak ve font düşerse
            yerleşim **aynı kalacak**. Bu tur onu ölçüyor — istekler
            tarayıcı düzeyinde engelleniyor, yani gerçekten yedek yüzler
            çiziliyor.
            """
            self._hazirla()
            self.cdp.cagir("Network.setBlockedURLs", urls=[
                "*fonts.googleapis.com*", "*fonts.gstatic.com*"])
            self._oturum_ac()
            hatalar, olculen = [], 0
            for ad, yol, beklenen_h1, _ in self._sayfalar():
                if ad == "Giriş":
                    continue
                for genislik in (360, 768, 1024, 1280, 1600):
                    o = self._olc(yol, genislik)
                    olculen += 1
                    if o["tasma"] > 0:
                        hatalar.append(f"{ad} @{genislik}: taşma {o['tasma']}")
                    if o["h1metin"] != beklenen_h1:
                        hatalar.append(f"{ad} @{genislik}: yanlış sayfa")
                    if o["zemin"] != "rgb(244, 246, 248)":
                        hatalar.append(f"{ad} @{genislik}: panel.css yok")
                    if o["yuzler"]:
                        hatalar.append(
                            f"{ad} @{genislik}: engelleme İŞLEMEDİ, "
                            f"yüzler {o['yuzler']}")
            print(f"\n--- font ENGELLİ ölçüm: {olculen} ölçüm, "
                  f"bulgu {len(hatalar)} ---")
            for hata in hatalar[:20]:
                print("  ! " + hata)
            self.cdp.cagir("Network.setBlockedURLs", urls=[])
            self.assertEqual(hatalar, [])

        def test_toplu_onay_ekrani_tasmiyor(self):
            """Onay ekranı POST'la açılıyor; ölçüm dışında bırakılmadı."""
            self._hazirla()
            self._oturum_ac()
            kimlikler = list(
                Haber.objects.values_list("pk", flat=True)[:6])
            alanlar = [("fiil", "kategori"),
                       ("kategori_degeri", self.spor.pk)]
            alanlar += [("kimlikler", k) for k in kimlikler]
            hatalar = []
            for genislik in GENISLIKLER:
                self._post_ile_ac("/panel/toplu", alanlar, genislik)
                sonuc = self.cdp.cagir("Runtime.evaluate",
                                       expression=OLCUM_BETIGI,
                                       returnByValue=True)
                o = json.loads(sonuc["result"]["value"])
                if o["h1metin"] != "Toplu işlem onayı":
                    hatalar.append(
                        f"@{genislik}: onay ekranı açılmadı "
                        f"(h1 “{o['h1metin']}”)")
                if o["tasma"] > 0:
                    hatalar.append(f"@{genislik}: taşma {o['tasma']}")
                if o["h1sayi"] != 1:
                    hatalar.append(f"@{genislik}: h1 = {o['h1sayi']}")
                if o["halkasiz"]:
                    hatalar.append(f"@{genislik}: odaksız {o['halkasiz'][:3]}")
            print(f"\n--- toplu işlem onay ekranı: {len(GENISLIKLER)} ölçüm, "
                  f"bulgu {len(hatalar)} ---")
            for hata in hatalar:
                print("  ! " + hata)
            self.assertEqual(hatalar, [])

        def test_toplu_serit_ve_secim_kutulari_cizildi(self):
            """Şeridin gerçekten çizildiğini doğrular.

            Şerit çizilmezse "Akış'ta taşma 0" ölçümü toplu işlem arayüzü
            hakkında hiçbir şey söylemez — ölçülmeyen bir şey ölçülmüş
            sayılamaz.
            """
            self._hazirla()
            self._oturum_ac()
            self._git("/panel/akis", 1280)
            sonuc = self.cdp.cagir("Runtime.evaluate", returnByValue=True,
                                   expression="""(() => JSON.stringify({
                serit: !!document.querySelector('.toplu-serit'),
                kutu: document.querySelectorAll('[data-toplu-kutu]').length,
                hepsi: !!document.querySelector('[data-toplu-hepsi]'),
                dugme: [...document.querySelectorAll('button[name=fiil]')]
                         .map(d => d.textContent.trim()),
                sayac: (document.querySelector('[data-toplu-sayac]')||{})
                         .textContent,
              }))()""")
            o = json.loads(sonuc["result"]["value"])
            print("\n--- toplu şerit ---")
            print("  şerit:", o["serit"], "· satır kutusu:", o["kutu"],
                  "· hepsini seç:", o["hepsi"])
            print("  fiiller:", o["dugme"])
            print("  sayaç:", o["sayac"])
            self.assertTrue(o["serit"])
            self.assertTrue(o["hepsi"])
            self.assertGreater(o["kutu"], 0)
            self.assertIn("Kategori değiştir", o["dugme"])
            self.assertIn("Manşete al", o["dugme"])

        def test_medya_seritleri_cizildi(self):
            """Kose, galeri ve video listelerinde serit gercekten var mi.

            Olculmeyen sey olculmus sayilamaz: bu ekranlarda "tasma 0"
            sonucu, serit hic cizilmemisse toplu arayuz hakkinda hicbir sey
            soylemez.
            """
            self._hazirla()
            self._oturum_ac()
            bulgular = []
            for aile, yol in (("kose", "/panel/kose"),
                              ("galeri", "/panel/galeriler"),
                              ("video", "/panel/videolar")):
                self._git(yol, 1280)
                sonuc = self.cdp.cagir(
                    "Runtime.evaluate", returnByValue=True,
                    expression="""(() => JSON.stringify({
                        serit: !!document.querySelector('.toplu-serit'),
                        kutu: document.querySelectorAll('[data-toplu-kutu]').length,
                        hedef: (document.querySelector('.toplu-serit')
                                 ? document.querySelector('.toplu-serit')
                                     .closest('form').getAttribute('action') : ''),
                        dugme: [...document.querySelectorAll('button[name=fiil]')]
                                 .map(d => d.textContent.trim()),
                      }))()""")
                o = json.loads(sonuc["result"]["value"])
                print(f"  {aile:<8} serit={o['serit']} kutu={o['kutu']} "
                      f"hedef={o['hedef']} fiiller={o['dugme']}")
                if not o["serit"]:
                    bulgular.append(f"{aile}: serit yok")
                if o["kutu"] < 1:
                    bulgular.append(f"{aile}: secim kutusu yok")
                if o["hedef"] != f"/panel/toplu/{aile}":
                    bulgular.append(f"{aile}: form hedefi {o['hedef']}")
                if o["dugme"] != ["Yayına al", "Yayından çek", "Arşive al"]:
                    bulgular.append(f"{aile}: fiil kumesi {o['dugme']}")
            print(f"--- medya serit bulgusu: {len(bulgular)} ---")
            for b in bulgular:
                print("  ! " + b)
            self.assertEqual(bulgular, [])

        def test_panel_ekranlari_tasmiyor_ve_erisilebilir(self):
            self._hazirla()
            satirlar, hatalar = [], []
            toplam_odak = 0
            yuzler = set()
            for ad, yol, beklenen_h1, en_az_satir in self._sayfalar():
                if ad != "Giriş":
                    self._oturum_ac()
                olculen, kenar_olculen = [], []
                for genislik in GENISLIKLER:
                    o = self._olc(yol, genislik)
                    olculen.append(o["tasma"])
                    kenar_olculen.append(o["kenarGenislik"])
                    toplam_odak += o["odaklanabilir"]
                    yuzler.update(o["yuzler"])

                    # --- aracın kendi doğrulaması, her ölçümde ---
                    if o["zemin"] != "rgb(244, 246, 248)":
                        hatalar.append(
                            f"{ad} @{genislik}: panel.css YÜKLENMEMİŞ "
                            f"(gövde zemini {o['zemin']}); ölçüm geçersiz")
                    if o["h1metin"] != beklenen_h1:
                        hatalar.append(
                            f"{ad} @{genislik}: beklenen h1 "
                            f"“{beklenen_h1}”, ölçülen “{o['h1metin']}” — "
                            "yanlış sayfa ölçülmüş olabilir")
                    if o["satir"] < en_az_satir:
                        hatalar.append(
                            f"{ad} @{genislik}: tabloda {o['satir']} satır, "
                            f"en az {en_az_satir} bekleniyordu")
                    if not o["yuzler"]:
                        hatalar.append(
                            f"{ad} @{genislik}: Google Fonts YÜKLENMEDİ "
                            "(@font-face 0); font ölçümü anlamsız olur")
                    if ad != "Giriş" and o["kenarZemin"] != "rgb(18, 24, 31)":
                        hatalar.append(
                            f"{ad} @{genislik}: kenar çubuğu zemini "
                            f"{o['kenarZemin'] or 'yok'}")

                    # --- faz ölçütünün istediği dört sayı ---
                    if o["tasma"] > 0:
                        hatalar.append(
                            f"{ad} @{genislik}: taşma {o['tasma']} px "
                            f"→ {o['tasanlar'][:3]}")
                    if o["h1sayi"] != 1:
                        hatalar.append(f"{ad} @{genislik}: h1 = {o['h1sayi']}")
                    if o["halkasiz"]:
                        hatalar.append(
                            f"{ad} @{genislik}: odak halkası yok "
                            f"→ {o['halkasiz'][:3]}")
                    if o["altsiz"]:
                        hatalar.append(f"{ad} @{genislik}: alt'sız img "
                                       f"{o['altsiz']}")
                    if o["disKaynak"]:
                        hatalar.append(f"{ad} @{genislik}: dış kaynak "
                                       f"{o['disKaynak']}")
                satirlar.append(
                    f"{ad:<24} taşma " +
                    " ".join(f"{g}:{t}" for g, t in zip(GENISLIKLER, olculen)) +
                    "  | kenar " +
                    " ".join(str(k) for k in kenar_olculen))

            print("\n--- panel yerleşim ölçümü "
                  f"({len(self._sayfalar())} ekran × {len(GENISLIKLER)} "
                  f"genişlik = {len(self._sayfalar()) * len(GENISLIKLER)} "
                  "ölçüm) ---")
            for satir in satirlar:
                print(satir)
            print(f"yüklenen yazı tipi aileleri: {sorted(yuzler)}")
            print(f"odaklanabilir öğe (toplam): {toplam_odak}")
            print(f"bulgu: {len(hatalar)}")
            for hata in hatalar[:40]:
                print("  ! " + hata)
            self.assertEqual(hatalar, [])
