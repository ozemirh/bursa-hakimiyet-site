/* Reklam demo ağı — Google Publisher Tag (31 Ağustos 2026, kullanıcı kararı).
 *
 * Bu dosya YALNIZ `BH_REKLAM_DEMO=1` iken yüklenir (bkz. taban.html). Amacı
 * yuvaların gerçek bir reklamla nasıl durduğunu görmek; gelir sunumu değil,
 * o F7(b)'nin işi.
 *
 * Üç kural:
 *
 * 1. **Yuvalar işaretten okunur.** Şablonlarda `.reklam[data-gpt="300x250"]`
 *    duruyor; betik sayfada ne varsa onu tanımlar. Ölçü listesi burada
 *    tekrarlanmaz — yuva nerede duruyorsa ölçüsü de orada yazar.
 * 2. **"Reklamları gizle" anahtarına uyar.** Anahtar açıkken hiçbir slot
 *    tanımlanmaz; yoksa düğme yalan söylerdi (panolar gizli ama reklam
 *    yine de çekiliyor olurdu).
 * 3. **`data-gpt-demo="kapali"` olan yuva atlanır.** Ölçüsü işarette
 *    durur ama demo yaratıcısı basılmaz; gri yer tutucu kalır.
 * 4. **Görünmeyen yuva çekilmez.** Yan pageskin'ler yalnız ≥1480 px'te
 *    çiziliyor (`.yan-reklam{display:none}`); dar ekranda `offsetParent`
 *    null döner ve o yuva atlanır — görünmeyen reklam için istek atmak
 *    hem gereksiz hem de gerçek sunumda geçersiz gösterim sayılır.
 *
 * Yer tutucu ile reklam AYNI ızgara hücresinde duruyor (site.css
 * `.reklam>span,.reklam>.gpt-yuva{grid-area:1/1}`): reklam gelene kadar
 * gri pano görünür, geldiğinde `data-gpt-durum="dolu"` panoyu gizler.
 * Böylece yükleme sırasında kutu yerinden oynamıyor.
 */
(function () {
  /* "300x250,160x600" -> [[300,250],[160,600]] */
  function olculeriCoz(metin) {
    var cikti = [];
    (metin || '').split(',').forEach(function (parca) {
      var xy = parca.trim().split('x');
      var en = parseInt(xy[0], 10);
      var boy = parseInt(xy[1], 10);
      if (en > 0 && boy > 0) { cikti.push([en, boy]); }
    });
    return cikti;
  }

  /* Görünüm haritası: "1024>970x250,728x90; 601>728x90; 0>"
   *
   * Her giriş "en dar görüntü genişliği > o genişlikten itibaren geçerli
   * ölçüler". Ölçü listesi BOŞ bırakılabilir — o genişlikte yuvaya hiçbir
   * şey basılmaz (üst şeridin ≤600 px hâli böyle: kutu 44 px, hiçbir
   * standart yaratıcı sığmıyor).
   *
   * GPT haritayı geniş→dar sırada bekliyor; kaynak sıradan bağımsız olsun
   * diye burada sıralanıyor.
   */
  function haritaCoz(metin) {
    if (!metin) { return null; }
    var girisler = [];
    metin.split(';').forEach(function (satir) {
      var ikili = satir.split('>');
      if (ikili.length !== 2) { return; }
      var en = parseInt(ikili[0].trim(), 10);
      if (!(en >= 0)) { return; }
      girisler.push([en, olculeriCoz(ikili[1])]);
    });
    if (!girisler.length) { return null; }
    girisler.sort(function (a, b) { return b[0] - a[0]; });
    return girisler;
  }

  var kok = document.documentElement;
  if (kok.getAttribute('data-reklam') === 'kapali') { return; }

  var yol = window.BH_REKLAM_YOLU;
  if (!yol) { return; }

  var yuvalar = [];
  var kutular = document.querySelectorAll('.reklam[data-gpt]');
  for (var i = 0; i < kutular.length; i++) {
    var el = kutular[i];
    if (el.offsetParent === null) { continue; }   // gizli yuva çekilmez
    /* Yuva ölçüsünü bildiriyor ama DEMO doldurmasını istemiyor: ölçü
       sözleşmesi işarette kalsın, demo yaratıcısı basılmasın. Üst şerit
       böyle — bkz. taban.html'deki gerekçe. */
    if (el.getAttribute('data-gpt-demo') === 'kapali') { continue; }

    var olculer = olculeriCoz(el.getAttribute('data-gpt'));
    if (!olculer.length) { continue; }

    var kimlik = 'gpt-yuva-' + yuvalar.length;
    var kap = document.createElement('div');
    kap.className = 'gpt-yuva';
    kap.id = kimlik;
    el.appendChild(kap);
    yuvalar.push({
      kimlik: kimlik, olculer: olculer, kutu: el,
      harita: haritaCoz(el.getAttribute('data-gpt-harita'))
    });
  }
  if (!yuvalar.length) { return; }

  window.googletag = window.googletag || { cmd: [] };
  googletag.cmd.push(function () {
    var dizin = {};
    yuvalar.forEach(function (y) {
      dizin[y.kimlik] = y.kutu;
      var slot = googletag.defineSlot(yol, y.olculer, y.kimlik);
      if (y.harita) {
        var kurucu = googletag.sizeMapping();
        y.harita.forEach(function (giris) {
          kurucu.addSize([giris[0], 0], giris[1]);
        });
        slot.defineSizeMapping(kurucu.build());
      }
      slot.addService(googletag.pubads());
    });

    /* Boş dönen yuva DARALTILMAZ: kutunun yüksekliği yerleşimin parçası
       (üst şerit 250, kare 250, pageskin 600 px) ve daraltmak sayfayı
       reklam geldiğinde zıplatırdı. Boş kalırsa gri pano görünür. */
    googletag.pubads().collapseEmptyDivs(false);
    googletag.pubads().addEventListener('slotRenderEnded', function (olay) {
      var kutu = dizin[olay.slot.getSlotElementId()];
      if (kutu) {
        kutu.setAttribute('data-gpt-durum', olay.isEmpty ? 'bos' : 'dolu');
      }
    });
    googletag.pubads().enableSingleRequest();
    googletag.enableServices();

    yuvalar.forEach(function (y) { googletag.display(y.kimlik); });
  });
})();
