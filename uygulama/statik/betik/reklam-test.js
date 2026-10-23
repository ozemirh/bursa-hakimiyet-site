/* Yerel test reklam hizmeti — 7 Eylül 2026, kullanıcı isteği.
 *
 * Sayfadaki reklam kutularını sunucunun ürettiği test yaratıcılarıyla
 * doldurur (`/reklam/test/<en>x<boy>.svg`). Dış ağ yok, çerez yok,
 * internetsiz de çalışır — demo ağının (`reklam.js`) yapamadığı üç şey.
 *
 * Betik YALNIZ sunum oturumunda basılır (`baglam.sunum_araci_mi`), yani
 * geliştirme makinesinde ya da panele girmiş kullanıcıda. Basıldığında da
 * kendiliğinden doldurmaz: üst banttaki "Test reklamı" düğmesi açılınca
 * başlar, tercih `localStorage` içinde yaşar.
 *
 * Yuva sözleşmesi (`data-gpt`, `data-gpt-harita`, yuva adı, sığma
 * hesabı) ortak parçada: `reklam-olcu.js`. Dört kural burada:
 *
 * 1. **`data-gpt-demo="kapali"` burayı BAĞLAMAZ.** O işaret dış ağın
 *    yanlış ölçü basmasına karşıydı; bu hizmet ölçüyü tam üretiyor, üst
 *    şerit de doldurulur. Bir yuvayı test dışında tutmak için ayrı işaret
 *    var: `data-gpt-test="kapali"`.
 * 2. **"Reklamları gizle" anahtarına uyar.** Anahtar açıkken hiçbir kutu
 *    doldurulmaz; yoksa düğme yalan söylerdi.
 * 3. **Başkasının doldurduğu kutuya dokunmaz.** Demo ağı (`.gpt-yuva`)
 *    ya da AdSense (`.adsbygoogle`) o yuvayı aldıysa atlanır; aynı
 *    kutuda iki reklam olmaz.
 * 4. **Görünmeyen yuva doldurulmaz** — ortak parçanın `kutular()` kuralı.
 *
 * Yaratıcıya tıklanınca yuvanın SONRAKİ ölçüsü basılır — üst şeridi
 * 1100x150 ve 970x250 hâlleriyle görmek için. Bu yüzden yaratıcı
 * `<button>` içinde: fareyle olduğu kadar klavyeyle de gezilir.
 */
(function () {
  var kok = document.documentElement;
  var kokAdres = window.BH_REKLAM_TEST_KOK;
  var olcu = window.BHReklamOlcu;
  if (!kokAdres || !olcu) { return; }

  function temizle() {
    var hepsi = document.querySelectorAll('.reklam[data-gpt]');
    for (var i = 0; i < hepsi.length; i++) {
      var eski = hepsi[i].querySelector('.test-yaratici');
      if (eski) { eski.parentNode.removeChild(eski); }
      if (hepsi[i].getAttribute('data-gpt-test-durum')) {
        hepsi[i].removeAttribute('data-gpt-test-durum');
        hepsi[i].removeAttribute('data-gpt-durum');
      }
    }
  }

  function doldur(kutu) {
    var liste = olcu.adaylar(kutu);
    if (!liste.length) { return; }

    /* Ölçü ÖNCE işaretlenip SONRA ölçülüyor: dolu kutunun dolgusu
       kalkıyor (site.css), yani sığacak alan işaretten sonra büyüyor. */
    kutu.setAttribute('data-gpt-durum', 'dolu');
    kutu.setAttribute('data-gpt-test-durum', 'dolu');

    var sigan = olcu.siganlar(kutu, liste);
    if (!sigan.length) {
      kutu.removeAttribute('data-gpt-durum');
      kutu.removeAttribute('data-gpt-test-durum');
      return;
    }
    /* Tıklama sırası: sığan ölçüler üzerinde dönülür. */
    var sira = parseInt(kutu.getAttribute('data-gpt-test-sira') || '0', 10);
    var secilen = sigan[((sira % sigan.length) + sigan.length) % sigan.length];

    var ad = olcu.yuvaAdi(kutu);
    var adres = kokAdres + secilen[0] + 'x' + secilen[1] + '.svg';
    if (ad) { adres += '?yuva=' + encodeURIComponent(ad); }

    var dugme = document.createElement('button');
    dugme.type = 'button';
    dugme.className = 'test-yaratici';
    dugme.setAttribute(
      'aria-label',
      'Test reklamı ' + secilen[0] + '×' + secilen[1] +
      (sigan.length > 1 ? ' — sonraki ölçüye geç' : ''));
    if (sigan.length > 1) { dugme.title = 'Sonraki ölçü'; }

    var gorsel = document.createElement('img');
    gorsel.src = adres;
    gorsel.width = secilen[0];
    gorsel.height = secilen[1];
    gorsel.alt = '';
    dugme.appendChild(gorsel);

    dugme.addEventListener('click', function () {
      kutu.setAttribute('data-gpt-test-sira', String(sira + 1));
      var eski = kutu.querySelector('.test-yaratici');
      if (eski) { eski.parentNode.removeChild(eski); }
      doldur(kutu);
      var yeni = kutu.querySelector('.test-yaratici');
      if (yeni) { yeni.focus(); }
    });

    kutu.appendChild(dugme);
  }

  function calistir() {
    temizle();
    if (kok.getAttribute('data-reklam-test') !== 'acik') { return; }
    if (kok.getAttribute('data-reklam') === 'kapali') { return; }
    olcu.kutular('data-gpt-test').forEach(function (kutu) {
      /* Başkasının DOLDURDUĞU kutuya dokunulmaz — ama boş bıraktığına
         girilir. Demo ağı altı yuvanın hepsini tanımlıyor, üçünü boş
         döndürüyor (ölçüldü: 970x250, 300x600 ve aynı sayfadaki ikinci
         160x600 gelmiyor); o kutular gri kalırsa iki yolu birlikte
         açmanın anlamı kalmazdı. */
      var baskasi = kutu.querySelector('.gpt-yuva, .adsbygoogle');
      if (baskasi) {
        /* "Boş döndü" bilgisi KALICI işaretleniyor: doldurduğumuz anda
           kutuyu "dolu" yapıyoruz, sonraki turda (ekran değişimi) o
           kutuyu yeniden boş sanmayalım diye. */
        if (kutu.getAttribute('data-gpt-durum') === 'bos') {
          kutu.setAttribute('data-gpt-bos', '1');
        }
        if (!kutu.hasAttribute('data-gpt-bos')) { return; }
      }
      doldur(kutu);
    });
  }

  /* Ölçü seçimi görünüm genişliğine bağlı; ekran değişince yeniden. */
  var zaman = null;
  window.addEventListener('resize', function () {
    if (zaman) { clearTimeout(zaman); }
    zaman = setTimeout(calistir, 200);
  });

  /* Demo ağı da açıksa: hangi yuvanın boş döndüğü ancak GPT yanıt
     verince belli olur, bu da bu betik çalıştıktan SONRA. Olay
     dinleniyor ve boş dönenler yerel yaratıcıyla dolduruluyor.
     Tek istek turu olduğu için biriktirip bir kez çalıştırmak yeterli. */
  if (window.googletag && window.googletag.cmd) {
    window.googletag.cmd.push(function () {
      window.googletag.pubads().addEventListener(
        'slotRenderEnded', function () {
          if (zaman) { clearTimeout(zaman); }
          zaman = setTimeout(calistir, 120);
        });
    });
  }

  /* site.js düğmeye basınca bunu çağırır; ilk çizim de burada. */
  window.BH_reklamTestiUygula = calistir;
  calistir();
})();
