/* Reklam yuvası ölçü sözleşmesi — ortak parça (7 Eylül 2026).
 *
 * Yuvalar şablonlarda `data-gpt` (ölçü listesi) ve `data-gpt-harita`
 * (görünüm haritası) ile işaretli. Bu dosya o işareti okuyan ve kutuya
 * hangi ölçünün SIĞDIĞINI söyleyen ortak koddur; ölçü listesi burada da
 * tekrarlanmaz — yuva nerede duruyorsa ölçüsü de orada yazar.
 *
 * İki tüketicisi var: `reklam-test.js` (yerel test hizmeti) ve
 * `reklam-adsense.js` (kendi yayıncı kimliğiyle AdSense).
 *
 * **`reklam.js` bilerek dışarıda.** Google demo ağı yolu 31 Ağustos'ta
 * ölçülerek yazıldı ve kendi testleri var; çalışan tek dosyayı bu
 * ayıklama uğruna kırmanın karşılığı yok. Üçünü birleştirmek gerçek
 * sunum (F7b) geldiğinde, demo yolu kalkarken yapılacak iş.
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

  /* Görünüm haritası: "1140>1100x150,970x250; 601>728x90; 0>"
     Her giriş "en dar görüntü genişliği > o genişlikten itibaren geçerli
     ölçüler". Liste boş bırakılabilir — o genişlikte yuvaya hiçbir şey
     basılmaz (üst şeridin ≤600 px hâli böyle: kutu 44 px, hiçbir standart
     yaratıcı sığmıyor). */
  function haritadanOlculer(metin, genislik) {
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
    for (var i = 0; i < girisler.length; i++) {
      if (genislik >= girisler[i][0]) { return girisler[i][1]; }
    }
    return [];
  }

  /* Bu görünüm genişliğinde yuvanın geçerli ölçüleri. */
  function adaylar(kutu) {
    var harita = haritadanOlculer(
      kutu.getAttribute('data-gpt-harita'),
      document.documentElement.clientWidth);
    if (harita) { return harita; }
    return olculeriCoz(kutu.getAttribute('data-gpt'));
  }

  /* Kutuya SIĞAN adaylar. 1 px tolerans: kenarlık/yuvarlama yüzünden tam
     ölçüde bir yaratıcı "sığmıyor" görünebiliyor. Sığmayanı istemek demo
     ağının kusuruydu — 728x90 yaratıcı 250 px'lik billboard kutusunun
     ortasında duruyordu (31 Ağustos ölçümü). */
  function siganlar(kutu, liste) {
    var en = kutu.clientWidth + 1;
    var boy = kutu.clientHeight + 1;
    return (liste || adaylar(kutu)).filter(function (o) {
      return o[0] <= en && o[1] <= boy;
    });
  }

  /* Yuva adı gri yer tutucunun kendi yazısında duruyor:
     "-Manşet yanı- 300x250" ya da "1100x150 · 970x250". Ölçü yaratıcının
     üstünde zaten yazdığı için addan atılır; geriye yalnız ayraç
     kalıyorsa ad yok demektir. Ad panelin yuva adıyla aynı sözleşme
     (`ReklamYuvasi.ad`, F1 ölçütü 3) — AdSense birimi de bununla eşleşir. */
  function yuvaAdi(kutu) {
    var el = kutu.querySelector('.olcu');
    var metin = el ? (el.textContent || '').trim() : '';
    metin = metin.replace(/\d{2,4}\s*[x×]\s*\d{2,4}/gi, '');
    metin = metin.replace(/[·–—,\-]+/g, ' ');
    return metin.replace(/\s+/g, ' ').trim();
  }

  /* Doldurulabilir yuvalar: görünen, işaretli ve `atlaNiteligi` ile
     dışarıda bırakılmamış olanlar. Görünmeyen yuva (dar ekranda yan
     pageskin) hiç istenmez — gerçek sunumda geçersiz gösterim sayılır. */
  function kutular(atlaNiteligi) {
    var cikti = [];
    var hepsi = document.querySelectorAll('.reklam[data-gpt]');
    for (var i = 0; i < hepsi.length; i++) {
      if (hepsi[i].offsetParent === null) { continue; }
      if (atlaNiteligi &&
          hepsi[i].getAttribute(atlaNiteligi) === 'kapali') { continue; }
      cikti.push(hepsi[i]);
    }
    return cikti;
  }

  window.BHReklamOlcu = {
    olculeriCoz: olculeriCoz,
    haritadanOlculer: haritadanOlculer,
    adaylar: adaylar,
    siganlar: siganlar,
    yuvaAdi: yuvaAdi,
    kutular: kutular
  };
})();
