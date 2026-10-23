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

/* ---------------------------------------------------------------------------
 * İlgili haber seçicisi — 28 Ağustos 2026
 *
 * Sorun ölçüldü: haber formu 356.839 <option> basıyordu (36,5 MB, 32,7 sn).
 * Alan artık yalnız SEÇİLİ olanları basıyor; yenisi arama ucundan geliyor.
 *
 * Bu betik YALNIZCA kolaylık ekler. Yoksa: bağlı haberler görünür,
 * kaldırılabilir ve haber kaydedilebilir — sadece yeni ilgili haber
 * eklenemez. Hiçbir kural burada uygulanmıyor; doğrulama sunucuda.
 * ------------------------------------------------------------------------ */
(function () {
  "use strict";

  /* Birden çok kap olabilir: ilgili haberler ve bağlı galeriler aynı
     deseni paylaşıyor (§4 alan 27, alan 28). İkinci bir çözüm yazılmadı. */
  document.querySelectorAll("[data-ilgili-kap]").forEach(kur);

  function kur(kap) {
  var secici = kap.getAttribute("data-secim") || "select[data-ilgili]";
  var secim = kap.querySelector(secici);
  if (!secim) { return; }

  var adres = kap.getAttribute("data-ara-adres");
  var haric = kap.getAttribute("data-haric") || "";

  /* Arama kutusu betikle ekleniyor: betik yoksa işlevsiz bir kutu
     görünmesin. */
  var kutu = document.createElement("div");
  kutu.className = "ilgili-ara";
  kutu.innerHTML =
    '<label for="ilgili-ara-girdi">İlgili haber ara</label>' +
    '<input id="ilgili-ara-girdi" type="search" autocomplete="off" ' +
    'placeholder="Başlıkta ara — en az 3 harf">' +
    '<p class="sag-not" data-ilgili-durum role="status" aria-live="polite"></p>' +
    '<ul class="ilgili-sonuc" data-ilgili-sonuc></ul>';
  secim.parentNode.insertBefore(kutu, secim);

  var girdi = kutu.querySelector("#ilgili-ara-girdi");
  var durum = kutu.querySelector("[data-ilgili-durum]");
  var liste = kutu.querySelector("[data-ilgili-sonuc]");
  var zamanlayici = null;
  var sonIstek = 0;

  function yaz(metin) { durum.textContent = metin || ""; }

  function ekle(kimlik, etiket) {
    var varMi = Array.prototype.some.call(secim.options, function (o) {
      return o.value === String(kimlik);
    });
    if (varMi) { yaz("Bu haber zaten bağlı."); return; }
    var secenek = document.createElement("option");
    secenek.value = kimlik;
    secenek.textContent = etiket;
    secenek.selected = true;
    secim.appendChild(secenek);
    yaz("Eklendi: " + etiket);
    liste.innerHTML = "";
    girdi.value = "";
  }

  function ara() {
    var q = girdi.value.trim();
    liste.innerHTML = "";
    if (q.length < 3) { yaz(q ? "En az 3 harf yazın." : ""); return; }
    yaz("Aranıyor…");
    var bu = ++sonIstek;
    var url = adres + "?q=" + encodeURIComponent(q) +
              (haric ? "&haric=" + encodeURIComponent(haric) : "");
    fetch(url, { headers: { "X-Requested-With": "fetch" } })
      .then(function (y) { return y.json(); })
      .then(function (veri) {
        if (bu !== sonIstek) { return; }        /* eski istek, at */
        if (veri.uyari) { yaz(veri.uyari); return; }
        if (!veri.sonuclar.length) { yaz("Eşleşen haber yok."); return; }
        yaz(veri.sonuclar.length + " sonuç");
        veri.sonuclar.forEach(function (h) {
          var satir = document.createElement("li");
          var dugme = document.createElement("button");
          dugme.type = "button";
          dugme.className = "dugme ufak";
          dugme.textContent = h.etiket + (h.tarih ? " · " + h.tarih : "");
          dugme.addEventListener("click", function () {
            ekle(h.id, h.etiket);
          });
          satir.appendChild(dugme);
          liste.appendChild(satir);
        });
      })
      .catch(function () { yaz("Arama başarısız oldu."); });
  }

  girdi.addEventListener("input", function () {
    clearTimeout(zamanlayici);
    zamanlayici = setTimeout(ara, 250);
  });
  girdi.addEventListener("keydown", function (olay) {
    /* Enter formu göndermesin: kullanıcı arama yapmak istiyor. */
    if (olay.key === "Enter") { olay.preventDefault(); clearTimeout(zamanlayici); ara(); }
  });
  }
})();

/* ---------------------------------------------------------------------------
 * Doğrulama sonrası odak — PANEL-NOTLARI.md §21
 *
 * Sunucu doğrulaması zaten çalışıyor ("Yayınlanamaz — eksik: spot, etiket.")
 * ama sayfa yenilendiğinde odak en başa dönüyordu; uzun formda editör hatayı
 * aramak zorunda kalıyor. §21'de ölçülen davranış "odak ilk eksiğe gitti"
 * idi ve üründe eksikti.
 *
 * Erişilebilirlik kalemi: klavye ve ekran okuyucu kullanıcısı hatayı
 * kendiliğinden buluyor. Hiçbir kural burada uygulanmıyor.
 * ------------------------------------------------------------------------ */
(function () {
  "use strict";
  var ilkHata = document.querySelector(".haber-form .alan.hatali, " +
                                       ".kayit-form .alan.hatali");
  if (!ilkHata) { return; }
  var girdi = ilkHata.querySelector("input, select, textarea");
  if (!girdi) { return; }
  /* `details` içindeyse önce aç — kapalı kutudaki hata görünmez. */
  var kutu = girdi.closest("details");
  if (kutu) { kutu.open = true; }
  girdi.focus({ preventScroll: false });
  ilkHata.scrollIntoView({ block: "center" });
})();

/* ---------------------------------------------------------------------------
 * Haber formu kolaylıkları — PANEL-NOTLARI.md §4 ve §21
 *
 * §21'de ölçülmüş ama üründe eksik kalan dört davranış buraya taşındı:
 * karakter sayaçları · paragraf sayacı · adres önizlemesi · hazırlık
 * ekseninin yalnız Pasif durumda görünmesi (§9).
 *
 * Hepsi KOLAYLIK. Hiçbir kural burada uygulanmıyor: zorunluluk, yayın eşiği
 * ve yetki denetimi sunucuda (`formlar.py`, `panel.py`). Betik kapalıyken
 * form eksiksiz çalışır, yalnız bu göstergeler görünmez.
 * ------------------------------------------------------------------------ */
(function () {
  "use strict";

  var form = document.querySelector("form.haber-form");
  if (!form) { return; }

  /* --- karakter sayaçları: alanlarda zaten `data-sayac` var --- */
  form.querySelectorAll("[data-sayac]").forEach(function (girdi) {
    var sinir = parseInt(girdi.getAttribute("data-sayac"), 10);
    if (!sinir) { return; }
    var etiket = form.querySelector('label[for="' + girdi.id + '"]');
    if (!etiket) { return; }
    var sayac = document.createElement("span");
    sayac.className = "sayac";
    etiket.appendChild(sayac);
    function yaz() {
      var n = girdi.value.length;
      sayac.textContent = n + "/" + sinir;
      sayac.classList.toggle("dolmak-uzere", n > sinir * 0.85 && n <= sinir);
      sayac.classList.toggle("tasti", n > sinir);
    }
    girdi.addEventListener("input", yaz);
    yaz();
  });

  /* --- paragraf sayacı: yayın eşiği en az iki paragraf ister (§4) --- */
  var govde = form.querySelector("#id_govde");
  if (govde) {
    var etiketG = form.querySelector('label[for="id_govde"]');
    if (etiketG) {
      var psayac = document.createElement("span");
      psayac.className = "sayac";
      etiketG.appendChild(psayac);
      var yazP = function () {
        var m = govde.value.toLowerCase().match(/<p[\s>]/g);
        var n = m ? m.length
                  : govde.value.split(/\n\s*\n/).filter(function (p) {
                      return p.trim();
                    }).length;
        psayac.textContent = n + " paragraf";
        psayac.classList.toggle("tasti", n < 2);
      };
      govde.addEventListener("input", yazP);
      yazP();
    }
  }

  /* --- adres önizlemesi: /{kategori-slug}/{slug}-{id} ---
     Slug kuralı PANEL-NOTLARI.md §8'de ölçülmüş: Türkçe harf sadeleştirme
     + küçük harf + tire. Sunucu kendi slug'ını kendi üretir; bu yalnız
     önizleme, kaydedilen değer değil. */
  var SADE = { "ç": "c", "ğ": "g", "ı": "i", "ö": "o", "ş": "s", "ü": "u",
               "Ç": "c", "Ğ": "g", "İ": "i", "I": "i", "Ö": "o", "Ş": "s",
               "Ü": "u", "â": "a", "î": "i", "û": "u" };
  function slugla(metin) {
    var cikti = "";
    for (var i = 0; i < metin.length; i++) {
      var h = metin[i];
      cikti += Object.prototype.hasOwnProperty.call(SADE, h) ? SADE[h] : h;
    }
    return cikti.toLowerCase().replace(/[^a-z0-9]+/g, "-")
                .replace(/^-+|-+$/g, "").slice(0, 220);
  }

  var baslik = form.querySelector("#id_baslik");
  var kategori = form.querySelector("#id_kategori");
  var kap = form.querySelector("[data-adres-onizleme]");
  if (baslik && kategori && kap) {
    var kimlik = kap.getAttribute("data-kimlik") || "{id}";
    var yazA = function () {
      var secili = kategori.options[kategori.selectedIndex];
      /* Kategori seçilmemişken Django "---------" basar; onu slug'a
         çevirmek boş dize verir ve adres "//" gibi görünürdü. */
      var kslug = (secili && secili.value)
                  ? (slugla(secili.textContent.trim()) || "{kategori}")
                  : "{kategori}";
      kap.innerHTML =
        '<span class="kok">/</span><span class="kat">' + kslug +
        '</span><span class="kok">/</span><span class="slug">' +
        (slugla(baslik.value) || "{slug}") +
        '</span><span class="kimlik">-' + kimlik + "</span>";
    };
    baslik.addEventListener("input", yazA);
    kategori.addEventListener("change", yazA);
    yazA();
  }

  /* --- hazırlık ekseni yalnız durum Pasif iken anlamlı (§9) --- */
  var durum = form.querySelector("#id_durum");
  var hazirlik = form.querySelector("#id_hazirlik");
  if (durum && hazirlik) {
    var kutuH = hazirlik.closest(".alan");
    var PASIF = "2";
    var yazH = function () {
      var goster = durum.value === PASIF;
      if (kutuH) { kutuH.hidden = !goster; }
    };
    durum.addEventListener("change", yazH);
    yazH();
  }
})();
