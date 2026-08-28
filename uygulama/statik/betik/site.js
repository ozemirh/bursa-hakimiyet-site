(function(){
  var dizi = function(secici, kap){ return Array.prototype.slice.call((kap || document).querySelectorAll(secici)); };

  /* ---- sekme grupları: hava/namaz/eczane ve lig puan durumları ---- */
  function sekmeKur(kap){
    var sekmeler = dizi('[role="tab"]', kap);
    if(!sekmeler.length){ return; }
    function sekmeAc(btn, odakla){
      sekmeler.forEach(function(b){
        var secili = b === btn;
        b.setAttribute('aria-selected', secili ? 'true' : 'false');
        b.setAttribute('tabindex', secili ? '0' : '-1');
        var panel = document.getElementById(b.getAttribute('aria-controls'));
        if(panel){ panel.setAttribute('data-acik', secili ? 'true' : 'false'); }
      });
      if(odakla){ btn.focus(); }
    }
    sekmeler.forEach(function(btn, i){
      btn.addEventListener('click', function(){ sekmeAc(btn, false); });
      btn.addEventListener('keydown', function(e){
        var yon = 0;
        if(e.key === 'ArrowRight'){ yon = 1; }
        else if(e.key === 'ArrowLeft'){ yon = -1; }
        else if(e.key === 'Home'){ e.preventDefault(); sekmeAc(sekmeler[0], true); return; }
        else if(e.key === 'End'){ e.preventDefault(); sekmeAc(sekmeler[sekmeler.length - 1], true); return; }
        if(!yon){ return; }
        e.preventDefault();
        sekmeAc(sekmeler[(i + yon + sekmeler.length) % sekmeler.length], true);
      });
    });
  }
  dizi('.sek').forEach(function(sek){ sekmeKur(sek.parentNode); });

  /* ---- slayt alanları: manşet (15) ve yan haber alanı (5) ---- */
  var azalt = window.matchMedia('(prefers-reduced-motion: reduce)');

  function slaytKur(kok){
    var slaytlar = dizi('.slayt', kok);
    var noktalar = dizi('.slayt-noktalar button', kok);
    var sayacEl = kok.querySelector('.slayt-sayac');
    var durumEl = kok.querySelector('.slayt-durum');
    var geri = kok.querySelector('.slayt-ok.geri');
    var ileri = kok.querySelector('.slayt-ok.ileri');
    var toplam = slaytlar.length;
    var aktif = 0;
    var sayac = null;

    if(!toplam){ return; }

    function goster(i){
      aktif = ((i % toplam) + toplam) % toplam;
      slaytlar.forEach(function(s, j){ s.setAttribute('data-aktif', j === aktif ? 'true' : 'false'); });
      noktalar.forEach(function(b, j){
        if(j === aktif){ b.setAttribute('aria-current', 'true'); }
        else { b.removeAttribute('aria-current'); }
      });
      if(sayacEl){ sayacEl.textContent = (aktif + 1) + ' / ' + toplam; }
      if(durumEl){
        var bas = slaytlar[aktif].querySelector('h3');
        durumEl.textContent = (aktif + 1) + ' / ' + toplam + (bas ? ' · ' + bas.textContent.trim() : '');
      }
    }

    function sayacDur(){ if(sayac){ window.clearInterval(sayac); sayac = null; } }
    function sayacBaslat(){
      sayacDur();
      if(azalt.matches){ return; }
      sayac = window.setInterval(function(){ goster(aktif + 1); }, 9000);
    }
    // Otomatik gecis artik bir secim degil, VARSAYILAN (27 Agustos karari).
    // Tek istisna erisilebilirlik: prefers-reduced-motion: reduce diyen
    // kullanicida hic donmez - hareket rahatsizlik verebiliyor. Fare ustune
    // gelince ve odak icerideyken de durur; okur bir seyi okumaya calisiyor.
    function otoIstendi(){ return !azalt.matches; }

    if(geri){ geri.addEventListener('click', function(){ goster(aktif - 1); }); }
    if(ileri){ ileri.addEventListener('click', function(){ goster(aktif + 1); }); }
    noktalar.forEach(function(b, j){ b.addEventListener('click', function(){ goster(j); }); });

    if(otoIstendi()){ sayacBaslat(); }
    // Kullanici hareket azaltmayi sonradan acarsa da dursun.
    if(azalt.addEventListener){
      azalt.addEventListener('change', function(){
        if(azalt.matches){ sayacDur(); } else { sayacBaslat(); }
      });
    }

    kok.addEventListener('mouseenter', sayacDur);
    kok.addEventListener('focusin', sayacDur);
    kok.addEventListener('mouseleave', function(){ if(otoIstendi()){ sayacBaslat(); } });
    kok.addEventListener('focusout', function(e){
      if(otoIstendi() && !kok.contains(e.relatedTarget)){ sayacBaslat(); }
    });

    kok.addEventListener('keydown', function(e){
      if(!e.target.closest || !e.target.closest('.slayt-ok, .slayt-noktalar')){ return; }
      if(e.key === 'ArrowRight'){ e.preventDefault(); goster(aktif + 1); }
      else if(e.key === 'ArrowLeft'){ e.preventDefault(); goster(aktif - 1); }
      else if(e.key === 'Home'){ e.preventDefault(); goster(0); }
      else if(e.key === 'End'){ e.preventDefault(); goster(toplam - 1); }
    });

    goster(0);
  }
  dizi('.slayt-kap').forEach(slaytKur);

  /* ---- bandda arama: dar ekranda simgeyle açılır ---- */
  var aramaDugme = document.querySelector('.ara-ac');
  var aramaFormu = document.getElementById('bant-ara');

  function aramaAcikMi(){ return !!aramaDugme && aramaDugme.getAttribute('aria-expanded') === 'true'; }
  function aramaKapat(odakla){
    if(!aramaAcikMi()){ return; }
    aramaDugme.setAttribute('aria-expanded', 'false');
    aramaFormu.setAttribute('data-acik', 'false');
    if(odakla){ aramaDugme.focus(); }
  }
  if(aramaDugme && aramaFormu){
    aramaDugme.addEventListener('click', function(){
      if(aramaAcikMi()){ aramaKapat(true); return; }
      aramaDugme.setAttribute('aria-expanded', 'true');
      aramaFormu.setAttribute('data-acik', 'true');
      var alan = document.getElementById('ara-kutu');
      if(alan){ alan.focus(); }
    });
  }

  /* ---- tam menü: her genişlikte açılır, banda sığmayanlar burada ---- */
  var bant = document.querySelector('.kategori');
  var menuDugme = document.querySelector('.menu-dugme');
  var tamMenu = document.getElementById('tam-menu');

  function menuAcikMi(){ return !!menuDugme && menuDugme.getAttribute('aria-expanded') === 'true'; }
  function menuOdaklar(){
    if(!tamMenu){ return []; }
    /* `summary` de odaklanabilir: bölümler <details> ile katlanıyor ve
       klavye kullanıcısı onları Tab ile gezip Enter/Space ile açıyor.
       Yalnız `a[href]` toplansaydı katlanır başlıklar odak tuzağının
       dışında kalır, kapalı bölümler klavyeyle hiç açılamazdı. */
    return [menuDugme].concat(dizi('summary, a[href]', tamMenu)).filter(function(o){
      if(!o || o.getClientRects().length === 0){ return false; }
      /* KAPALI <details> içindeki bağlantılar ODAK ALAMAZ ama Chrome onlara
         yine de kutu (client rect) veriyor — kapalı içerik `content-visibility`
         ile atlanıyor, `display:none` ile değil. Bu yüzden salt "kutusu var mı"
         süzgeci onları listeye alıyordu ve tuzağın "son öğe"si asla odak
         alamayan bir bağlantı oluyordu: sarma koşulu hiç gerçekleşmiyor, odak
         menüden kaçıyordu (ölçüldü: 70 Tab adımının 53'ü dışarı çıktı).
         `summary` kendi kapalı bölümünün içinde sayılmaz — o odaklanabilir. */
      return o.tagName === 'SUMMARY' || !o.closest('details:not([open])');
    });
  }
  function menuKapat(odakla){
    if(!menuAcikMi()){ return; }
    menuDugme.setAttribute('aria-expanded', 'false');
    tamMenu.hidden = true;
    if(odakla){ menuDugme.focus(); }
  }
  function menuAc(){
    menuDugme.setAttribute('aria-expanded', 'true');
    tamMenu.hidden = false;
    /* Odak panelin ilk odaklanabilir öğesine gider — artık bu bir
       `summary`. Odak sırası görsel sırayla aynı kalsın diye DOM sırasının
       ilki alınıyor. */
    var ilkOdak = tamMenu.querySelector('summary, a[href]');
    if(ilkOdak){ ilkOdak.focus(); }
  }
  if(menuDugme && tamMenu){
    menuDugme.addEventListener('click', function(){
      if(menuAcikMi()){ menuKapat(true); } else { menuAc(); }
    });
    /* menü açıkken odak düğme ile panel arasında döner */
    document.addEventListener('keydown', function(e){
      if(e.key !== 'Tab' || !menuAcikMi()){ return; }
      var odaklar = menuOdaklar();
      if(odaklar.length < 2){ return; }
      var ilk = odaklar[0], son = odaklar[odaklar.length - 1];
      if(e.shiftKey && document.activeElement === ilk){ e.preventDefault(); son.focus(); }
      else if(!e.shiftKey && document.activeElement === son){ e.preventDefault(); ilk.focus(); }
    });
    /* dışarı tıklayınca kapanır; bağlantıya tıklanırsa da kapanır */
    document.addEventListener('click', function(e){
      if(!menuAcikMi()){ return; }
      if(tamMenu.contains(e.target) && e.target.closest && e.target.closest('a[href]')){ menuKapat(false); return; }
      if(bant && bant.contains(e.target)){ return; }
      menuKapat(false);
    });
  }

  document.addEventListener('keydown', function(e){
    if(e.key !== 'Escape'){ return; }
    if(menuAcikMi()){ menuKapat(true); return; }
    if(aramaAcikMi()){ aramaKapat(true); }
  });

  /* ---- arama: sayfadaki başlıkları süz ---- */
  var aramaKutusu = document.getElementById('ara-kutu');
  var suzBilgi = document.querySelector('.suz-bilgi');
  var suzulenler = dizi('.kart, .galeri-kart, .video-kart, .film, .sira li, .yazar-ray li, .ilan-liste li');
  function haberSuz(){
    var q = aramaKutusu.value.trim().toLocaleLowerCase('tr');
    if(q.length < 2){
      suzulenler.forEach(function(o){ o.classList.remove('gizli'); });
      suzBilgi.setAttribute('data-gorunur', 'false');
      suzBilgi.textContent = '';
      return;
    }
    var sayi = 0;
    suzulenler.forEach(function(o){
      var uyar = o.textContent.toLocaleLowerCase('tr').indexOf(q) > -1;
      o.classList.toggle('gizli', !uyar);
      if(uyar){ sayi++; }
    });
    suzBilgi.setAttribute('data-gorunur', 'true');
    suzBilgi.textContent = '“' + aramaKutusu.value.trim() + '” için ' + sayi +
      ' başlık eşleşti. Manşet slaytları süzmeye dahil değildir; tümünü görmek için kutuyu boşaltın.';
  }
  if(aramaKutusu && suzBilgi){
    aramaKutusu.addEventListener('input', haberSuz);
    aramaKutusu.addEventListener('keydown', function(e){
      if(e.key !== 'Escape'){ return; }
      if(aramaKutusu.value !== ''){ e.stopPropagation(); aramaKutusu.value = ''; haberSuz(); }
    });
  }

  /* ---- yukarı çık ---- */
  var yukari = document.querySelector('.yukari');
  if(yukari){
    var yukariGoster = function(){
      yukari.setAttribute('data-gorunur', window.pageYOffset > 420 ? 'true' : 'false');
    };
    window.addEventListener('scroll', yukariGoster, {passive: true});
    yukariGoster();
    yukari.addEventListener('click', function(){
      window.scrollTo({top: 0, behavior: azalt.matches ? 'auto' : 'smooth'});
    });
  }
})();
