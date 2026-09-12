/* AdSense — kendi yayıncı kimliğiyle (7 Eylül 2026, kullanıcı kararı).
 *
 * Google demo ağı (`reklam.js`) başkasının envanteri; bu dosya gazetenin
 * KENDİ `ca-pub-` kimliğiyle çalışır. Yuvaları `<ins class="adsbygoogle">`
 * ile doldurur, ölçüyü yine şablondaki işaretten okur (`reklam-olcu.js`).
 *
 * Beş kural:
 *
 * 1. **Ölçü SABİT verilir.** `<ins>` kutunun ölçüsünde inline-block olarak
 *    kurulur; `data-ad-format` ve tam genişlik esnetmesi bilerek kapalı
 *    (`data-full-width-responsive="false"`). Yuvalarımızın ölçüsü
 *    yerleşimin parçası — esneyen birim üst şeridi 250 px'lik kutuda
 *    kendi boyuna çekerdi.
 * 2. **Birim kimliği yuva ADIYLA eşleşir.** `data-ad-slot` değeri
 *    ayarlardaki eşleşmeden gelir (`yuvalar`), yoksa varsayılan birim
 *    kullanılır. Yuva adı panelin `ReklamYuvasi.ad` sözleşmesiyle aynı —
 *    envanterdeki adla AdSense birimi böyle bağlanır.
 * 3. **Test modu görünür olmalı.** `data-adtest="on"` iken AdSense test
 *    yaratıcısı döner ve gösterim sayılmaz; kutuya ayrıca `TEST` şeridi
 *    çizilir ki ekrandakinin gerçek reklam olmadığı belli olsun.
 * 4. **Dolmayan yuva daraltılmaz.** AdSense `<ins>` üzerine
 *    `data-ad-status="unfilled"` yazar; o durumda gri yer tutucu geri
 *    gelir, kutunun yüksekliği yerleşimin parçası olduğu için durur.
 * 5. **"Reklamları gizle" anahtarına uyar** ve görünmeyen yuvayı
 *    istemez — dolmayacak bir istek geçersiz gösterim sayılır.
 *
 * Yuva başına birim TANIMLI DEĞİLSE o yuva boş bırakılır: uydurma bir
 * `data-ad-slot` göndermek AdSense tarafında hatalı istek demek.
 */
(function () {
  var kok = document.documentElement;
  var olcu = window.BHReklamOlcu;
  var ayarDugum = document.getElementById('adsense-ayar');
  if (!olcu || !ayarDugum) { return; }

  var ayar = {};
  try { ayar = JSON.parse(ayarDugum.textContent) || {}; } catch (e) { return; }
  if (!ayar.kimlik) { return; }
  if (kok.getAttribute('data-reklam') === 'kapali') { return; }

  var yuvalar = ayar.yuvalar || {};

  function birimKimligi(ad) {
    if (ad && Object.prototype.hasOwnProperty.call(yuvalar, ad)) {
      return yuvalar[ad];
    }
    return ayar.varsayilan || '';
  }

  /* Test modunda kutunun köşesine şerit: ekrandaki gerçek reklam değil. */
  function testSeridi(kutu) {
    if (!ayar.test) { return; }
    if (kutu.querySelector('.adsense-test-seridi')) { return; }
    var etiket = document.createElement('span');
    etiket.className = 'adsense-test-seridi';
    etiket.textContent = 'TEST';
    kutu.appendChild(etiket);
  }

  /* AdSense dolduramazsa `data-ad-status="unfilled"` yazar; gri pano
     geri gelsin diye izleniyor. Doldurursa kutu "dolu" işaretlenir ve
     yer tutucu gizlenir (site.css). */
  function durumuIzle(kutu, ins) {
    var uygula = function () {
      var durum = ins.getAttribute('data-ad-status');
      if (durum === 'unfilled') {
        kutu.removeAttribute('data-gpt-durum');
      } else if (durum === 'filled') {
        kutu.setAttribute('data-gpt-durum', 'dolu');
      }
    };
    if (window.MutationObserver) {
      new MutationObserver(uygula).observe(
        ins, {attributes: true, attributeFilter: ['data-ad-status']});
    }
    uygula();
  }

  function doldur(kutu) {
    if (kutu.querySelector('.adsbygoogle, .gpt-yuva')) { return; }

    var sigan = olcu.siganlar(kutu);
    if (!sigan.length) { return; }
    /* Sığanların İLKİ — yani işaretteki sıra. Sıra rastgele değil: üst
       şeritte 1100x150 gazetenin kendi sattığı ölçü, 970x250 programatik
       karşılığı, 728x90 yedek (31 Ağustos kararı). "En büyüğü seç" deseydik
       gazetenin kendi yuvası hiç istenmezdi. */
    var secilen = sigan[0];

    var birim = birimKimligi(olcu.yuvaAdi(kutu));
    if (!birim) { return; }   // tanımsız yuvaya uydurma kimlik gönderilmez

    var ins = document.createElement('ins');
    ins.className = 'adsbygoogle';
    ins.style.display = 'inline-block';
    ins.style.width = secilen[0] + 'px';
    ins.style.height = secilen[1] + 'px';
    ins.setAttribute('data-ad-client', ayar.kimlik);
    ins.setAttribute('data-ad-slot', birim);
    ins.setAttribute('data-full-width-responsive', 'false');
    if (ayar.test) { ins.setAttribute('data-adtest', 'on'); }
    kutu.appendChild(ins);

    kutu.setAttribute('data-gpt-durum', 'dolu');
    testSeridi(kutu);
    durumuIzle(kutu, ins);

    (window.adsbygoogle = window.adsbygoogle || []).push({});
  }

  /* Tek geçiş: AdSense birimi bir kez `push` edilir, yeniden ölçülünce
     tekrar istenemez ("All ins elements ... already have ads"). Ekran
     genişliği değişse de kutu yeniden kurulmuyor; bu bilinçli. */
  olcu.kutular('data-adsense').forEach(doldur);
})();
