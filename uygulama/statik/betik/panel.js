/* Panelin toplu işlem şeridi — PANEL-NOTLARI.md §12.
 *
 * Betik YALNIZCA kolaylık ekler: "hepsini seç" kutusu ve canlı sayaç.
 * Betik hiç çalışmazsa ekran yine çalışır — kutular tek tek işaretlenir,
 * düğmeler POST eder. Yetki denetimi ve sınırlar sunucuda; buradaki hiçbir
 * satır bir kuralı uygulamıyor.
 *
 * Bağımlılık yok, tek IIFE, Türkçe işlev adları — panelin geri kalanıyla
 * aynı düzen.
 */
(function () {
  "use strict";

  var serit = document.querySelector("[data-toplu]");
  if (!serit) { return; }

  var sayac = serit.querySelector("[data-toplu-sayac]");
  var suzgecKutusu = serit.querySelector("[data-toplu-suzgec]");
  var hepsi = document.querySelector("[data-toplu-hepsi]");
  var kutular = Array.prototype.slice.call(
    document.querySelectorAll("[data-toplu-kutu]"));

  /* Sayi metinden ayristirilmiyor, serit onu veri olarak tasiyor: binlik
     ayraci ya da metin degisirse ayristirma sessizce bozulurdu. */
  var suzgecSayisi = parseInt(serit.getAttribute("data-toplu-sayi"), 10) || 0;

  function sayiyiYaz() {
    if (!sayac) { return; }
    if (suzgecKutusu && suzgecKutusu.checked) {
      sayac.textContent = "Süzgeçteki " + suzgecSayisi + " kaydın tamamı seçili";
      return;
    }
    var secili = kutular.filter(function (k) { return k.checked; }).length;
    sayac.textContent = secili + " kayıt seçili";
  }

  function kutulariKilitle(kilit) {
    kutular.forEach(function (k) { k.disabled = kilit; });
    if (hepsi) { hepsi.disabled = kilit; }
  }

  if (hepsi) {
    hepsi.addEventListener("change", function () {
      kutular.forEach(function (k) { k.checked = hepsi.checked; });
      sayiyiYaz();
    });
  }

  kutular.forEach(function (kutu) {
    kutu.addEventListener("change", function () {
      if (hepsi) {
        var tumu = kutular.length > 0 &&
          kutular.every(function (k) { return k.checked; });
        hepsi.checked = tumu;
        hepsi.indeterminate = !tumu &&
          kutular.some(function (k) { return k.checked; });
      }
      sayiyiYaz();
    });
  });

  if (suzgecKutusu) {
    /* "Süzgeçteki tümü" seçiliyken tek tek seçim anlamsız: sunucu zaten
       süzgeci yeniden koşuyor. Kutuları kilitlemek, kullanıcının iki
       farklı küme seçtiğini sanmasını engelliyor. */
    suzgecKutusu.addEventListener("change", function () {
      kutulariKilitle(suzgecKutusu.checked);
      sayiyiYaz();
    });
  }

  sayiyiYaz();
})();
