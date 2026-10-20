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

    // Ertelenen kareler (19 Ekim 2026): gizli slayt `visibility:hidden` olsa da
    // tarayici `loading="lazy"`ye ragmen gorselini indiriyordu - 20 slaytin
    // 18'i ilk acilista iniyordu. Sablon onlara `data-srcset` basar; slayt
    // etkinlesince o ve SIRADAKI yuklenir, gecis aninda bos kare kalmaz.
    function yukle(s){
      if(!s){ return; }
      dizi('img[data-srcset]', s).forEach(function(im){
        im.setAttribute('srcset', im.getAttribute('data-srcset'));
        im.setAttribute('src', im.getAttribute('data-src'));
        im.removeAttribute('data-srcset');
        im.removeAttribute('data-src');
      });
    }

    function goster(i){
      aktif = ((i % toplam) + toplam) % toplam;
      yukle(slaytlar[aktif]);
      yukle(slaytlar[(aktif + 1) % toplam]);
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
      if(!otoIstendi()){ return; }
      sayac = window.setInterval(function(){ goster(aktif + 1); }, 9000);
    }
    // Otomatik gecis bir secim degil, VARSAYILAN (27 Agustos karari;
    // 29 Agustos'ta denenen duraklatma dugmesi kullanici karariyla kaldirildi).
    // Tek istisna erisilebilirlik: prefers-reduced-motion: reduce diyen
    // kullanicida hic donmez - hareket rahatsizlik verebiliyor. Fare ustune
    // gelince ve odak icerideyken de durur; okur bir seyi okumaya calisiyor.
    function otoIstendi(){ return !azalt.matches; }

    if(geri){ geri.addEventListener('click', function(){ goster(aktif - 1); }); }
    if(ileri){ ileri.addEventListener('click', function(){ goster(aktif + 1); }); }
    noktalar.forEach(function(b, j){
      b.addEventListener('click', function(){ goster(j); });
      // 31 Agustos: ileri/geri oklari kaldirildi; gezinme numaralardan olur.
      // Fare numaranin uzerine gelince o slayta gecer, tiklama sart degil -
      // kapsama girildiginde otomatik gecis zaten duruyor.
      b.addEventListener('mouseenter', function(){ goster(j); });
    });

    if(otoIstendi()){ sayacBaslat(); }
    // Kullanici hareket azaltmayi sonradan acarsa da dursun.
    if(azalt.addEventListener){
      azalt.addEventListener('change', function(){
        if(otoIstendi()){ sayacBaslat(); } else { sayacDur(); }
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

  /* ---- reklam anahtarı: sunum aracı, okur özelliği değil ----
     Düğme yalnız geliştirme/panel oturumunda ÇİZİLİYOR (icerik/baglam.py);
     burada da varlığı denetleniyor, yoksa betik sessizce geçiyor.
     Tercih `<html data-reklam>` üzerinde; ilk okuması `<head>` içindeki
     minik betikte, çünkü sayfa çizilmeden uygulanmalı. */
  var reklamAnahtar = document.querySelector('.reklam-anahtar');
  if(reklamAnahtar){
    var kok = document.documentElement;
    var yazi = reklamAnahtar.querySelector('.reklam-anahtar-yazi');
    var uygula = function(kapali, yaz){
      if(kapali){ kok.setAttribute('data-reklam', 'kapali'); }
      else { kok.removeAttribute('data-reklam'); }
      reklamAnahtar.setAttribute('aria-pressed', kapali ? 'true' : 'false');
      if(yazi){ yazi.textContent = kapali ? 'Reklamları göster' : 'Reklamları gizle'; }
      /* localStorage gizli sekmede ya da site verisi kapalıyken atar;
         atması düğmeyi çalışmaz hâle getirmemeli, tercih o oturumda
         yaşar. */
      if(yaz){ try{ localStorage.setItem('bh-reklam', kapali ? 'kapali' : 'acik'); }catch(e){} }
    };
    uygula(kok.getAttribute('data-reklam') === 'kapali', false);
    reklamAnahtar.addEventListener('click', function(){
      uygula(reklamAnahtar.getAttribute('aria-pressed') !== 'true', true);
    });
  }

  /* ---- test reklamı anahtarı: yerel hizmet, dış ağ değil ----
     Düğme yalnız sunum oturumunda çiziliyor (icerik/baglam.py). Dolguyu
     reklam-test.js yapar; burada yalnız tercih tutulup ona haber veriliyor.
     Reklamlar gizliyken test dolgusu da anlamsız — kutular görünmüyor —
     o yüzden gizleme anahtarı her değiştiğinde dolgu yeniden çalışır. */
  var testAnahtar = document.querySelector('.reklam-test-anahtar');
  if(testAnahtar){
    var kokEl = document.documentElement;
    var testYazi = testAnahtar.querySelector('.reklam-test-yazi');
    var testUygula = function(acik, yaz){
      if(acik){ kokEl.setAttribute('data-reklam-test', 'acik'); }
      else { kokEl.removeAttribute('data-reklam-test'); }
      testAnahtar.setAttribute('aria-pressed', acik ? 'true' : 'false');
      if(testYazi){ testYazi.textContent = acik ? 'Test reklamı açık' : 'Test reklamı'; }
      if(yaz){ try{ localStorage.setItem('bh-reklam-test', acik ? 'acik' : 'kapali'); }catch(e){} }
      if(window.BH_reklamTestiUygula){ window.BH_reklamTestiUygula(); }
    };
    testUygula(kokEl.getAttribute('data-reklam-test') === 'acik', false);
    testAnahtar.addEventListener('click', function(){
      testUygula(testAnahtar.getAttribute('aria-pressed') !== 'true', true);
    });
    if(reklamAnahtar){
      reklamAnahtar.addEventListener('click', function(){
        if(window.BH_reklamTestiUygula){ window.BH_reklamTestiUygula(); }
      });
    }
  }

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
    /* MEGA LEVHA (30 Agustos 2026, §35): genis ekranda bes bolumun hepsi
       acik gelir - levha bes sutunlu bir tablodur, akordeon degil. Sablona
       `open` YAZILMAZ: sunucu HTML'i bayt bayt ayni kalsin ki menunun DOM
       sozlesmeleri (dort bolum, tek acik bolum) oynamasin.
       Dar ekranda akordeon KATEGORILER-acik haliyle gelir; hepsini acmak
       100+ satirlik bir kaydirma duvari kurardi. */
    if(window.matchMedia('(min-width:1001px)').matches){
      dizi('.menu-bolum', tamMenu).forEach(function(b){ b.open = true; });
    }
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

  /* ---- resmî ilan tür süzgeci ----
     Şerit eskiden yalnızca renk kodunu tanıtan bir lejanttı. Kayıtlar
     gerçek veriye bağlanınca gezinme aracına çevrildi. Betik yüklenmezse
     bütün ilanlar görünür kalır: süzgeç bir ilerleme, bir bağımlılık
     değil. Sayılar SAYFADAKİ ilanları sayar; arşiv toplamı bölümün
     altındaki notta yazar. */
  var ilanSerit = document.querySelector('.ilan-turler');
  var ilanSatirlari = dizi('.ilan-liste li[data-tur]');
  if(ilanSerit && ilanSatirlari.length){
    var turNot = ilanSerit.querySelector('.tur-not');
    /* Varsayılan metin sayfadan OKUNUYOR, `data-varsayilan` ile
       kopyalanmıyor: aynı cümle iki yerde durunca biri güncellenip
       diğeri unutuluyordu. */
    var turVarsayilan = turNot ? turNot.textContent : '';
    var ilanDugmeleri = dizi('button.tur', ilanSerit);
    ilanSerit.addEventListener('click', function(e){
      var dugme = e.target.closest ? e.target.closest('button.tur') : null;
      if(!dugme || dugme.disabled){ return; }
      var tur = dugme.getAttribute('data-tur');
      var sayi = 0;
      ilanDugmeleri.forEach(function(d){
        d.setAttribute('aria-pressed', d === dugme ? 'true' : 'false');
      });
      ilanSatirlari.forEach(function(satir){
        var uyar = !tur || satir.getAttribute('data-tur') === tur;
        satir.classList.toggle('gizli', !uyar);
        if(uyar){ sayi++; }
      });
      if(!turNot){ return; }
      if(!tur){ turNot.textContent = turVarsayilan; return; }
      var ad = (dugme.getAttribute('data-ad') || '').toLocaleLowerCase('tr');
      turNot.textContent = 'Sayfadaki ' + sayi + ' ' + ad + ' ilanı gösteriliyor.';
    });
  }

  /* ---- nöbetçi eczane süzgeci ----
     31 Ağustos 2026: panel dosyadaki 34 eczanenin tamamını basıyor; okur
     gece yarısı "benim ilçemde hangisi açık" diye bakıyor. İki süzgeç
     birlikte çalışır: ilçe (satırdaki `data-ilce`) ve serbest arama
     (satırın metni — eczane adı, mahalle, sokak, telefon).

     Denetimler şablonda `hidden` geliyor, açan bu betik: yüklenmezse okur
     çalışmayan bir kutu görmez, listenin tamamı yine basılı durur. Aynı
     ilke resmî ilan süzgecinde de var — süzgeç bir ilerleme, bir
     bağımlılık değil. */
  var eczanePanel = document.getElementById('panel-eczane');
  var eczaneSatirlari = dizi('.eczane-liste li', eczanePanel);
  if(eczanePanel && eczaneSatirlari.length){
    var eczaneSuzgec = eczanePanel.querySelector('.eczane-suzgec');
    var eczaneIlce = document.getElementById('eczane-ilce');
    var eczaneArama = document.getElementById('eczane-ara');
    var eczaneSonuc = eczanePanel.querySelector('.eczane-sonuc');
    var eczaneListe = eczanePanel.querySelector('.eczane-liste');
    var eczaneBos = null;

    /* Metin bir kez okunur: her tuş vuruşunda 34 satırın `textContent`i
       yeniden istenirse tarayıcı her seferinde yerleşimi hesaplıyor. */
    var eczaneMetin = eczaneSatirlari.map(function(satir){
      return satir.textContent.toLocaleLowerCase('tr');
    });

    function eczaneSuz(){
      var ilce = eczaneIlce ? eczaneIlce.value : '';
      var q = eczaneArama ? eczaneArama.value.trim().toLocaleLowerCase('tr') : '';
      var sayi = 0;
      eczaneSatirlari.forEach(function(satir, i){
        var uyar = (!ilce || satir.getAttribute('data-ilce') === ilce) &&
                   (q.length < 2 || eczaneMetin[i].indexOf(q) > -1);
        satir.classList.toggle('gizli', !uyar);
        if(uyar){ sayi++; }
      });

      /* Hiçbiri eşleşmediğinde liste sessizce boşalmamalı: okur süzgecin
         mi çalıştığını yoksa verinin mi bittiğini anlayamıyor. */
      if(!sayi && !eczaneBos && eczaneListe){
        eczaneBos = document.createElement('p');
        eczaneBos.className = 'eczane-bos';
        eczaneListe.parentNode.insertBefore(eczaneBos, eczaneListe.nextSibling);
      }
      if(eczaneBos){
        eczaneBos.textContent = sayi ? '' : 'Bu aramayla eşleşen nöbetçi eczane yok.';
        eczaneBos.hidden = !!sayi;
      }

      if(!eczaneSonuc){ return; }
      if(!ilce && q.length < 2){
        eczaneSonuc.setAttribute('data-gorunur', 'false');
        eczaneSonuc.textContent = '';
        return;
      }
      var ad = ilce && eczaneIlce ?
        eczaneIlce.options[eczaneIlce.selectedIndex].text.replace(/\s*\(\d+\)$/, '') : '';
      eczaneSonuc.setAttribute('data-gorunur', 'true');
      eczaneSonuc.textContent = sayi + ' eczane gösteriliyor' +
        (ad ? ' · ' + ad : '') + (q.length > 1 ? ' · “' + q + '”' : '') + '.';
    }

    if(eczaneSuzgec){ eczaneSuzgec.hidden = false; }
    if(eczaneIlce){ eczaneIlce.addEventListener('change', eczaneSuz); }
    if(eczaneArama){
      eczaneArama.addEventListener('input', eczaneSuz);
      eczaneArama.addEventListener('keydown', function(e){
        if(e.key !== 'Escape' || eczaneArama.value === ''){ return; }
        e.stopPropagation();   /* Escape önce kutuyu boşaltsın, menüyü değil */
        eczaneArama.value = '';
        eczaneSuz();
      });
    }
  }

  /* ---- daha fazla göster (6 Eylül 2026) ----------------------------------
     Düğme HTML'de gerçek bir bağlantıdır (`?sayfa=2`, anasayfada
     `/son-haberler`) ve burası yalnızca onu ZENGİNLEŞTİRİR: tıklama
     yakalanır, dilim `data-uc` ucundan çekilir, kalemler listenin sonuna
     eklenir. Bu blok hiç çalışmazsa (eski tarayıcı, betik yüklenmedi)
     bağlantı kendi işini görür — kırılan bir şey olmaz.

     Sunucudan HTML geliyor, JSON değil: kart ve akış satırı şablonları
     sunucuda duruyor ve ikinci bir kopyayı burada tutmak ikisinin bir gün
     sessizce ayrışması demekti. */
  function dahaFazlaKur(dugme){
    var hedef = document.querySelector(dugme.getAttribute('data-hedef') || '');
    var uc = dugme.getAttribute('data-uc');
    if(!hedef || !uc || !window.fetch){ return; }

    var kap = dugme.parentNode;
    var durum = kap.querySelector('.daha-fazla-durum');
    var sayfa = parseInt(dugme.getAttribute('data-sayfa'), 10) || 1;
    var ilkMetin = dugme.textContent.trim();
    var mesgul = false;

    function bitir(metin, odakla){
      /* Arşivin sonu: düğme yerini bir satıra bırakır. Odak düğmedeydi;
         düğme silinince odak <body>'ye düşerdi. Odak zaten yeni içeriğe
         taşındıysa (aşağıya bakın) satıra ALINMAZ — okuru listenin
         başından alıp sonundaki nota atmak, yeni gelenleri atlatırdı. */
      var not = document.createElement('p');
      not.className = 'daha-fazla-son';
      not.setAttribute('tabindex', '-1');
      not.textContent = metin;
      kap.parentNode.replaceChild(not, kap);
      if(odakla){ not.focus(); }
    }

    /* Sayfayı yeni gelenlere İNDİRİR — 7 Eylül 2026, kullanıcı bildirimi:
       "daha fazla göster butonu tıklandığında sayfa aşağı ilerlemiyor yeni
       haberleri göstermek için, sadece yukarıda yeni haberler gösteriyor".

       Kalemler düğmenin ÜSTÜNE giriyor, yani düğme aşağı kayıyor ve okurun
       baktığı piksel değişmiyor. Yerleşim düzeltildikten sonra (düğme artık
       listenin hemen altında) yeni kalemler doğru yere geliyor, ama okurun
       gözü hâlâ eski son satırda kalıyordu; "daha fazla göster"in beklenen
       davranışı yeni yığının BAŞINA inmektir.

       Odak da oraya taşınıyor: klavyeyle gezen okur Tab'a bastığında yeni
       kalemlerin içinde devam etsin, listenin en başına dönmesin. Kaydırma
       `scroll-margin-top` ile yapışkan bandın altına oturur (site.css). */
    function yeniyeIn(ilk){
      if(!ilk){ return; }
      ilk.setAttribute('tabindex', '-1');
      try{ ilk.focus({preventScroll: true}); }catch(hata){ ilk.focus(); }
      try{
        ilk.scrollIntoView({block: 'start',
                            behavior: azalt.matches ? 'auto' : 'smooth'});
      }catch(hata){ ilk.scrollIntoView(true); }
    }

    dugme.addEventListener('click', function(e){
      e.preventDefault();
      if(mesgul){ return; }
      mesgul = true;
      dugme.setAttribute('aria-busy', 'true');
      dugme.textContent = 'Yükleniyor…';

      fetch(uc + (uc.indexOf('?') < 0 ? '?' : '&') + 'sayfa=' + sayfa,
            {credentials: 'same-origin'})
        .then(function(yanit){
          if(!yanit.ok){ throw new Error('HTTP ' + yanit.status); }
          return yanit.text();
        })
        .then(function(html){
          var gecici = document.createElement('div');
          gecici.innerHTML = html;
          var parca = gecici.querySelector('.akis-parca');
          if(!parca){ throw new Error('parça yok'); }

          /* Taşınan çocuklar iki biçimde geliyor: bölüm akışında
             ikili/üçlü BLOKLAR (§60), anasayfa ızgarasında tek tek kartlar.
             Sayım okura kaç HABER geldiğini söylemeli, kaç kap geldiğini
             değil — blok kendi kalemlerini sayıyor. */
          var yeniler = Array.prototype.slice.call(parca.children);
          var haber = 0;
          var ilkYeni = yeniler.length ? yeniler[0] : null;
          yeniler.forEach(function(el){
            haber += el.classList.contains('akis-blok') ? el.children.length : 1;
            hedef.appendChild(el);
          });

          mesgul = false;
          dugme.removeAttribute('aria-busy');
          dugme.textContent = ilkMetin;
          sayfa += 1;
          dugme.setAttribute('data-sayfa', sayfa);
          /* Orta tıklamayla yeni sekmede açan okur da devamını görsün.
             Adresi yalnız `sayfa` parametresi TAŞIYORSA güncelliyoruz;
             anasayfanın `/son-haberler` adresi başka bir sayfadır ve ona
             sayfa numarası eklemek yanlış yere götürürdü. */
          try{
            var adres = new URL(dugme.href, window.location.href);
            if(adres.searchParams.has('sayfa')){
              adres.searchParams.set('sayfa', sayfa);
              dugme.href = adres.pathname + adres.search;
            }
          }catch(hata){}

          if(parca.getAttribute('data-devam') !== '1'){
            /* Kalem geldiyse odak ONA gider, nota değil: not listenin
               sonunda ve okuru oraya atmak yeni gelenleri atlatırdı. */
            /* `data-son`: listenin kendi sözü (köşe yazıları akışı
               "yazılar" der); yoksa haber listelerinin cümlesi. */
            bitir(haber ? (dugme.getAttribute('data-son') || 'Bu listedeki tüm haberler yüklendi.')
                        : 'Başka haber yok.', !haber);
            yeniyeIn(ilkYeni);
            return;
          }
          /* "N haber eklendi…" satırı 7 Eylül 2026'da kullanıcı isteğiyle
             KALDIRILDI. Ekran okuyucu bilgisiz kalmıyor: aynı gün odak
             yeni yığının ilk kalemine taşınmaya başladı (§61) ve okuyucu
             odaklanılan kalemi zaten okuyor — satır o değişiklikten sonra
             aynı şeyi ikinci kez söylüyordu. Durum alanı DURUYOR, çünkü
             hata dalı hâlâ oraya yazıyor. */
          yeniyeIn(ilkYeni);
        })
        .catch(function(){
          mesgul = false;
          dugme.removeAttribute('aria-busy');
          dugme.textContent = ilkMetin;
          if(durum){
            durum.textContent = 'Haberler yüklenemedi. Bağlantıya tıklayarak sonraki sayfaya geçebilirsiniz.';
          }
          /* Uç yanıt vermiyorsa zenginleştirmeden ÇEKİLİYORUZ: bundan
             sonraki tıklama bağlantının kendi işini yapmasına bırakılır. */
          dugme.replaceWith(dugme.cloneNode(true));
        });
    });
  }
  dizi('.daha-fazla').forEach(dahaFazlaKur);

  /* ---- haber araç çubuğu: bağlantıyı kopyala · A− / A+ · yazdır ----
     20 Ekim 2026: düğmeler şablonda vardı, işleyicileri yoktu. Haber
     detayı, köşe yazısı, galeri ve video aynı `.arac` sınıfını taşır; bu
     blok hepsine bağlanır. Betik yoksa düğmeler hiç çizilmez
     (`html.js-var`, taban.html + site.css). */
  var aracDuyuru = null;
  function aracDuyur(arac, metin){
    /* Tek, görünmez canlı bölge: ekran okuyucu sonucu duyar, görsel
       yerleşim değişmez. Metin önce boşaltılır — aynı cümle ikinci kez
       yazılınca da okunsun. */
    if(!aracDuyuru){
      aracDuyuru = document.createElement('span');
      aracDuyuru.className = 'gorsel-gizli';
      aracDuyuru.setAttribute('role', 'status');
      aracDuyuru.setAttribute('aria-live', 'polite');
      arac.appendChild(aracDuyuru);
    }
    aracDuyuru.textContent = '';
    window.setTimeout(function(){ aracDuyuru.textContent = metin; }, 60);
  }

  /* Kopyalanan adres sayfanın KANONİK adresi — paylaşım bağlantılarının
     (`parca/paylas.html`) kullandığıyla aynı; `?reklam-test=…` gibi
     sorgu ekleri okura geçmez. */
  function paylasimAdresi(){
    var kanonik = document.querySelector('link[rel="canonical"]');
    return kanonik && kanonik.href ? kanonik.href : window.location.href;
  }
  function eskiYoldanKopyala(metin){
    var alan = document.createElement('textarea');
    alan.value = metin;
    alan.setAttribute('readonly', '');
    alan.className = 'gorsel-gizli';
    document.body.appendChild(alan);
    alan.select();
    var oldu = false;
    try{ oldu = document.execCommand('copy'); }catch(hata){ oldu = false; }
    document.body.removeChild(alan);
    return oldu;
  }

  var YAZI_BOYLARI = ['kucuk', '', 'buyuk', 'cok-buyuk'];
  var YAZI_ADLARI = ['küçük', 'normal', 'büyük', 'çok büyük'];
  function yaziBoyuSirasi(){
    var i = YAZI_BOYLARI.indexOf(document.documentElement.getAttribute('data-yazi-boyu') || '');
    return i < 0 ? 1 : i;
  }

  dizi('.arac').forEach(function(arac){
    var kopyala = arac.querySelector('.kopyala');
    var kucult = arac.querySelector('.yazi-kucult');
    var buyut = arac.querySelector('.yazi-buyut');
    var yazdir = arac.querySelector('.yazdir');

    if(kopyala){
      var tamamZamani = null;
      var bitti = function(oldu){
        if(oldu){
          kopyala.setAttribute('data-durum', 'tamam');
          window.clearTimeout(tamamZamani);
          tamamZamani = window.setTimeout(function(){ kopyala.removeAttribute('data-durum'); }, 2000);
          aracDuyur(arac, 'Bağlantı kopyalandı.');
        } else {
          /* Son çare: adres seçili hâlde okura gösterilir, kendisi kopyalar. */
          window.prompt('Bağlantıyı kopyalayın:', paylasimAdresi());
        }
      };
      kopyala.addEventListener('click', function(){
        var adres = paylasimAdresi();
        if(navigator.clipboard && navigator.clipboard.writeText && window.isSecureContext){
          navigator.clipboard.writeText(adres).then(function(){ bitti(true); },
            function(){ bitti(eskiYoldanKopyala(adres)); });
        } else {
          bitti(eskiYoldanKopyala(adres));
        }
      });
    }

    /* Yazı boyu: dört kademe, tercih `localStorage`da. İlk okuma
       taban.html başında (kayma olmasın diye); burada yalnız düğmeler. */
    function boyuUygula(sira, duyur){
      var kok = document.documentElement;
      if(YAZI_BOYLARI[sira]){ kok.setAttribute('data-yazi-boyu', YAZI_BOYLARI[sira]); }
      else { kok.removeAttribute('data-yazi-boyu'); }
      if(kucult){ kucult.disabled = sira <= 0; }
      if(buyut){ buyut.disabled = sira >= YAZI_BOYLARI.length - 1; }
      if(duyur){
        try{
          if(YAZI_BOYLARI[sira]){ localStorage.setItem('bh-yazi-boyu', YAZI_BOYLARI[sira]); }
          else { localStorage.removeItem('bh-yazi-boyu'); }
        }catch(hata){}
        aracDuyur(arac, 'Yazı boyutu: ' + YAZI_ADLARI[sira] + '.');
      }
    }
    function boyuDegistir(yon, dugme){
      var sira = Math.max(0, Math.min(YAZI_BOYLARI.length - 1, yaziBoyuSirasi() + yon));
      boyuUygula(sira, true);
      /* Sınıra varan düğme `disabled` olur ve odağı düşürür; odak
         öbür düğmeye geçer ki klavyeyle gezen okur sayfanın başına
         atılmasın. */
      if(dugme.disabled){
        var obur = dugme === kucult ? buyut : kucult;
        if(obur){ obur.focus(); }
      }
    }
    if(kucult || buyut){
      boyuUygula(yaziBoyuSirasi(), false);
      if(kucult){ kucult.addEventListener('click', function(){ boyuDegistir(-1, kucult); }); }
      if(buyut){ buyut.addEventListener('click', function(){ boyuDegistir(1, buyut); }); }
    }

    if(yazdir){
      yazdir.addEventListener('click', function(){ window.print(); });
    }
  });

  /* ---- yukarı çık ("Başa dön", parca/yukari.html) ----
     20 Ekim 2026: düğme YALNIZ okur yukarı kaydırırken ve bir ekrandan
     aşağıdayken görünür. Aşağı okurken ekranın köşesini kapatmaz; geri
     dönmek isteyen okur (yukarı kaydıran) onu bulur. Odaktayken
     gizlenmez. Basınca sayfa başa döner ve odak `#ana-icerik`e geçer;
     `prefers-reduced-motion`da kaydırma animasyonsuz. */
  var yukari = document.querySelector('.yukari');
  if(yukari){
    var sonKonum = window.pageYOffset;
    var donuyor = false;   /* başa dönüş kaydırması sürerken yeniden belirmesin */
    var yukariGoster = function(){
      var konum = window.pageYOffset;
      var fark = konum - sonKonum;
      if(donuyor){ sonKonum = konum; if(konum <= 0){ donuyor = false; } return; }
      if(Math.abs(fark) < 8 && konum > 0){ return; }
      var goster = konum > window.innerHeight && fark < 0;
      if(document.activeElement === yukari && konum > 0){ goster = true; }
      yukari.setAttribute('data-gorunur', goster ? 'true' : 'false');
      sonKonum = konum;
    };
    window.addEventListener('scroll', yukariGoster, {passive: true});
    yukari.addEventListener('click', function(){
      var ana = document.getElementById('ana-icerik');
      donuyor = true;
      window.setTimeout(function(){ donuyor = false; }, 1500);
      yukari.setAttribute('data-gorunur', 'false');
      if(ana){ try{ ana.focus({preventScroll: true}); }catch(hata){ ana.focus(); } }
      window.scrollTo({top: 0, behavior: azalt.matches ? 'auto' : 'smooth'});
    });
  }
})();
