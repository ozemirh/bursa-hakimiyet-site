/* ===== haber seslendirme ====================================================
   Tarayıcının kendi ses motoruyla (Web Speech API) okur: dış servis yok,
   anahtar yok, indirilen ses dosyası yok — sayfa bağımsız kalır.
   Metin cümlelere bölünüp sırayla seslendirilir; tek parça uzun metin
   gönderildiğinde bazı tarayıcılar okumayı 15 saniye dolaylarında kesiyor.
   Okunacak öğeler `data-kaynak` seçicisinden gelir; gövde yayında yeniden
   üretildiği için liste her başlatmada yeniden toplanır.
   ========================================================================= */
(function(){
  var kutu = document.querySelector("[data-seslendirme]");
  if(!kutu){ return; }

  var oynat  = kutu.querySelector(".ses-oynat");
  var durdur = kutu.querySelector(".ses-dur");
  var geri   = kutu.querySelector(".ses-geri");
  var ileri  = kutu.querySelector(".ses-ileri");
  var hizSec = kutu.querySelector(".ses-hiz");
  var sesSecim = kutu.querySelector(".ses-secim");
  var sesSecimAlan = kutu.querySelector(".ses-secim-alan");
  var cizgi  = kutu.querySelector(".ses-cubuk span");
  var durum  = kutu.querySelector(".ses-durum");
  var notlar = kutu.querySelector(".ses-not");
  var motor  = window.speechSynthesis;

  function bildir(m){ if(durum){ durum.textContent = m; } }
  function azalt(){ return window.matchMedia("(prefers-reduced-motion: reduce)").matches; }

  if(!motor || typeof window.SpeechSynthesisUtterance === "undefined"){
    kutu.classList.add("ses-yok");
    [oynat, durdur, geri, ileri, hizSec, sesSecim].forEach(function(d){ if(d){ d.disabled = true; } });
    bildir("Bu tarayıcı sesli okumayı desteklemiyor.");
    return;
  }

  /* ---- okunacak metnin toplanması ---- */
  var ATLA = "cite, figcaption, .foto-alt, .foto-yazi, .editor-not, .kenar-not, " +
             ".zaman-not, .not, .not-kutu, .ozet, [data-ses='atla']";
  var EN_UZUN = 150;   /* harf; tek sözcede 15 sn sınırının altında kalmak için */
  var paragraflar = [], sira = [], toplamHarf = 0;

  function metinAl(og){
    var kopya = og.cloneNode(true);
    var cop = kopya.querySelectorAll(ATLA);
    for(var i = 0; i < cop.length; i++){
      if(cop[i].parentNode){ cop[i].parentNode.removeChild(cop[i]); }
    }
    return (kopya.textContent || "").replace(/\s+/g, " ").trim();
  }

  function bol(metin){
    var cumleler = metin.match(/[^.!?…]+[.!?…]*\s*/g) || [metin];
    var parca = [], tampon = "";
    function bosalt(){ var t = tampon.trim(); if(t){ parca.push(t); } tampon = ""; }
    for(var i = 0; i < cumleler.length; i++){
      var c = cumleler[i];
      while(c.length > EN_UZUN){        /* çok uzun cümle: virgülden, olmazsa boşluktan kır */
        var kes = c.lastIndexOf(", ", EN_UZUN);
        if(kes < 50){ kes = c.lastIndexOf(" ", EN_UZUN); }
        if(kes < 30){ kes = EN_UZUN; }
        bosalt();
        parca.push(c.slice(0, kes + 1).trim());
        c = c.slice(kes + 1);
      }
      if((tampon + c).length > EN_UZUN){ bosalt(); }
      tampon += c;
    }
    bosalt();
    return parca;
  }

  function kur(){
    paragraflar = []; sira = []; toplamHarf = 0;
    var ogeler = document.querySelectorAll(kutu.getAttribute("data-kaynak"));
    for(var i = 0; i < ogeler.length; i++){
      var og = ogeler[i];
      if(og.closest && og.closest(ATLA)){ continue; }
      var metin = metinAl(og);
      if(metin.length < 2){ continue; }
      var no = paragraflar.length;
      paragraflar.push(og);
      var parcalar = bol(metin);
      for(var j = 0; j < parcalar.length; j++){
        sira.push({p: no, metin: parcalar[j]});
        toplamHarf += parcalar[j].length;
      }
    }
  }

  /* ---- ses seçimi ----
     Sıralama işin kalitesini belirliyor: eski SAPI sesleri (ör. "Microsoft
     Tolga") sinir ağı seslerinin yanında belirgin biçimde makine gibi duyuluyor.
     Adında Natural / Neural / Online / Google geçenler öne alınır. Önceki
     "yerel sesi tercih et" sıralaması bilerek kaldırıldı: doğal Türkçe sesler
     çoğu makinede ağ üzerinden geliyor, yerel olan eski ses oluyordu. */
  var ses = null, sesBakildi = false, trSesler = [];

  function sesPuani(v){
    var ad = v.name || "", puan = 0;
    if(/natural|neural|premium|enhanced/i.test(ad)){ puan += 100; }
    if(/online/i.test(ad)){ puan += 60; }
    if(/google/i.test(ad)){ puan += 50; }
    if(v.default){ puan += 5; }
    return puan;
  }

  function sesAdi(v){
    var ad = (v.name || "").replace(/\s*[-–]\s*Turkish.*$/i, "").replace(/^Microsoft\s+/i, "");
    var dogal = /natural|neural|online/i.test(v.name || "");
    ad = ad.replace(/\(Natural\)/i, "").replace(/\bOnline\b/i, "").replace(/\s+/g, " ").trim();
    return ad + (dogal ? " · doğal" : "");
  }

  function sesSec(){
    var liste = motor.getVoices() || [];
    if(!liste.length){ return; }
    sesBakildi = true;
    trSesler = [];
    for(var i = 0; i < liste.length; i++){
      if(/^tr(-|_|$)/i.test(liste[i].lang || "")){ trSesler.push(liste[i]); }
    }
    trSesler.sort(function(a, b){ return sesPuani(b) - sesPuani(a); });

    var kayitli = null;
    try{ kayitli = window.localStorage.getItem("bh-ses"); }catch(e){}
    ses = trSesler[0] || null;
    for(var j = 0; j < trSesler.length; j++){
      if(trSesler[j].name === kayitli){ ses = trSesler[j]; }
    }

    if(sesSecim){
      sesSecim.innerHTML = "";
      for(var k = 0; k < trSesler.length; k++){
        var o = document.createElement("option");
        o.value = trSesler[k].name;
        o.textContent = sesAdi(trSesler[k]);
        if(ses && trSesler[k].name === ses.name){ o.selected = true; }
        sesSecim.appendChild(o);
      }
      if(sesSecimAlan){ sesSecimAlan.hidden = trSesler.length < 2; }
    }
    if(notlar){
      if(!trSesler.length){
        notlar.hidden = false;
        notlar.textContent = "Bu cihazda Türkçe ses paketi bulunamadı; sistemin varsayılan sesi kullanılıyor.";
      } else if(sesPuani(trSesler[0]) === 0){
        notlar.hidden = false;
        notlar.textContent = "Bu tarayıcıda yalnızca sistemin standart Türkçe sesi bulundu. " +
          "Daha doğal bir okuma için sayfayı Microsoft Edge'de açmayı deneyin.";
      } else {
        notlar.hidden = true;
        notlar.textContent = "";
      }
    }
  }
  if(motor.addEventListener){ motor.addEventListener("voiceschanged", sesSec); }
  else { motor.onvoiceschanged = sesSec; }
  sesSec();

  /* ---- durum ve gösterim ---- */
  var konum = 0, calisiyor = false, duraklatildi = false, suanki = null;

  function hiz(){ return parseFloat(hizSec && hizSec.value) || 1; }

  function isaretle(no){
    for(var i = 0; i < paragraflar.length; i++){ paragraflar[i].classList.remove("ses-okunan"); }
    if(no === null || !paragraflar[no]){ return; }
    var og = paragraflar[no];
    og.classList.add("ses-okunan");
    var k = og.getBoundingClientRect();
    if(k.top < 90 || k.bottom > window.innerHeight - 30){
      og.scrollIntoView({block: "center", behavior: azalt() ? "auto" : "smooth"});
    }
  }

  function ilerlemeYaz(){
    var okunan = 0;
    for(var i = 0; i < konum && i < sira.length; i++){ okunan += sira[i].metin.length; }
    if(cizgi){ cizgi.style.width = (toplamHarf ? (okunan / toplamHarf) * 100 : 0).toFixed(1) + "%"; }
  }

  function kalanYaz(){
    if(!sira.length){ return; }
    var kalan = 0;
    for(var i = konum; i < sira.length; i++){ kalan += sira[i].metin.length; }
    var dk = Math.max(1, Math.round(kalan / (14.5 * hiz()) / 60));
    var no = sira[konum] ? sira[konum].p + 1 : paragraflar.length;
    bildir((duraklatildi ? "Duraklatıldı" : "Okunuyor") + " · " + no + "/" + paragraflar.length +
           " paragraf · yaklaşık " + dk + " dk kaldı");
  }

  function goster(){
    var oynuyor = calisiyor && !duraklatildi;
    var simge = oynat.querySelector(".ses-simge");
    var yazi  = oynat.querySelector(".ses-yazi");
    if(simge){ simge.textContent = oynuyor ? "❚❚" : "▶"; }
    if(yazi){ yazi.textContent = oynuyor ? "Duraklat" : (calisiyor ? "Sürdür" : "Sesli dinle"); }
    oynat.setAttribute("aria-pressed", oynuyor ? "true" : "false");
    kutu.classList.toggle("ses-acik", calisiyor);
    if(durdur){ durdur.disabled = !calisiyor; }
  }

  /* ---- okuma ---- */
  function soyle(){
    if(konum >= sira.length){ bitir(true); return; }
    var sozce = new SpeechSynthesisUtterance(sira[konum].metin);
    if(!sesBakildi){ sesSec(); }
    sozce.lang = ses ? ses.lang : "tr-TR";
    if(ses){ sozce.voice = ses; }
    sozce.rate = hiz();
    sozce.onend = function(){
      if(!calisiyor || sozce !== suanki){ return; }
      konum++;
      ilerlemeYaz();
      if(konum < sira.length){ isaretle(sira[konum].p); kalanYaz(); soyle(); }
      else { bitir(true); }
    };
    sozce.onerror = function(e){
      var tur = e && e.error;
      if(!calisiyor || sozce !== suanki || tur === "interrupted" || tur === "canceled"){ return; }
      calisiyor = false; duraklatildi = false; suanki = null;
      isaretle(null); goster();
      /* Adres doğrudan yapıştırılıp açıldığında tarayıcı kendiliğinden başlayan
         okumayı engeller; bu bir arıza değil, düğmeye basılması gerekiyor. */
      bildir(tur === "not-allowed"
        ? "Tarayıcı kendiliğinden başlayan okumayı engelledi. Dinlemek için ▶ düğmesine basın."
        : "Ses motoru yanıt vermedi. Sistemin ses ayarlarını kontrol edip yeniden deneyin.");
    };
    suanki = sozce;
    motor.speak(sozce);
  }

  function basla(){
    kur();
    if(!sira.length){ bildir("Okunacak metin bulunamadı."); return; }
    if(konum >= sira.length){ konum = 0; }
    motor.cancel();
    calisiyor = true; duraklatildi = false;
    goster(); isaretle(sira[konum].p); ilerlemeYaz(); kalanYaz();
    window.setTimeout(soyle, 60);   /* cancel'in hemen ardından speak: bazı tarayıcılar yutuyor */
  }

  function duraklat(){ duraklatildi = true; motor.pause(); goster(); kalanYaz(); }
  function surdur(){ duraklatildi = false; motor.resume(); goster(); kalanYaz(); }

  function bitir(tamamlandi){
    calisiyor = false; duraklatildi = false; suanki = null; konum = 0;
    motor.cancel();
    isaretle(null); ilerlemeYaz(); goster();
    bildir(tamamlandi ? "Okuma tamamlandı." : "Durduruldu.");
  }

  function paragrafaGit(yon){
    if(!sira.length){ kur(); }
    if(!sira.length){ return; }
    var hedef = sira[Math.min(konum, sira.length - 1)].p + yon;
    if(hedef < 0){ hedef = 0; }
    if(hedef > paragraflar.length - 1){ hedef = paragraflar.length - 1; }
    for(var i = 0; i < sira.length; i++){
      if(sira[i].p === hedef){ konum = i; break; }
    }
    isaretle(hedef); ilerlemeYaz();
    if(calisiyor){
      duraklatildi = false; suanki = null; motor.cancel();
      goster(); kalanYaz();
      window.setTimeout(soyle, 60);
    } else {
      bildir((hedef + 1) + ". paragraf seçildi. Dinlemek için ▶ düğmesine basın.");
    }
  }

  /* ---- düğmeler ---- */
  oynat.addEventListener("click", function(){
    if(!calisiyor){ basla(); }
    else if(duraklatildi){ surdur(); }
    else { duraklat(); }
  });
  if(durdur){ durdur.addEventListener("click", function(){ bitir(false); }); }
  if(geri){ geri.addEventListener("click", function(){ paragrafaGit(-1); }); }
  if(ileri){ ileri.addEventListener("click", function(){ paragrafaGit(1); }); }
  if(sesSecim){
    sesSecim.addEventListener("change", function(){
      for(var i = 0; i < trSesler.length; i++){
        if(trSesler[i].name === sesSecim.value){ ses = trSesler[i]; }
      }
      try{ window.localStorage.setItem("bh-ses", sesSecim.value); }catch(e){}
      if(calisiyor && !duraklatildi){
        suanki = null; motor.cancel();
        window.setTimeout(soyle, 60);
      }
      if(notlar && sesPuani(ses || {}) > 0){ notlar.hidden = true; notlar.textContent = ""; }
    });
  }
  if(hizSec){
    hizSec.addEventListener("change", function(){
      if(calisiyor && !duraklatildi){
        suanki = null; motor.cancel();
        window.setTimeout(soyle, 60);
      }
      kalanYaz();
    });
  }

  /* Sayfadan ayrılırken ses susmalı; Firefox konuşmayı sürdürebiliyor. */
  window.addEventListener("pagehide", function(){ motor.cancel(); });
  window.addEventListener("beforeunload", function(){ motor.cancel(); });

  /* Anasayfadaki "Sesli dinle" bağlantısı buraya #seslendirme ile gelir.
     Otomatik başlatmayı tarayıcı engellerse düğme odakta bekler. */
  function odakla(){
    /* Çengelle gelen gezinme odağı gövdeye alabiliyor; kullanıcı başka bir yere
       geçtiyse odak çalınmaz. */
    if(document.activeElement === document.body){ oynat.focus({preventScroll: true}); }
  }
  if(window.location.hash === "#seslendirme"){
    kutu.classList.add("ses-cagri");
    window.setTimeout(odakla, 0);
    basla();
    window.setTimeout(function(){
      if(calisiyor && !motor.speaking && !motor.pending){
        calisiyor = false; duraklatildi = false; suanki = null;
        isaretle(null); goster();
        bildir("Dinlemek için ▶ düğmesine basın.");
      }
      odakla();
    }, 900);
  }
})();
