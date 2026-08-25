/* Kural motoru + konu eslestirme — tarayici surumu.
 *
 * arac/kural_motoru.py ve arac/konu_eslestirme.py dosyalarinin bire bir
 * karsiligidir. Sozluk, konular ve arsiv verisi disaridan gelir (window.BHVeri);
 * bu dosyayla birlikte gomulu_uret.py tarafindan yapay-zeka-editor.html icine
 * gomulur. Sayfa bagimsizligini bozmaz: ag istegi yok, bagimlilik yok.
 *
 * Model kullanmaz. Govde YAZILMAZ; kaynagin cumleleri yalnizca tezgahta durur.
 * Konu baglantisi kendiliginden kurulmaz, yalnizca aday onerilir.
 */
(function (kok) {
  "use strict";

  var V = kok.BHVeri || {};
  var S = V.sozluk || {};
  var KONULAR = V.konular || [];
  var ARSIV = V.arsiv || [];

  var UNLULER = "aeıioöuü";
  var GUCLU_ESIK = 60, OLASI_ESIK = 35;
  var AYLAR = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
               "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"];
  var GENEL_ISIMLER = ["mahalle", "mahallesi", "cadde", "caddesi", "sokak", "bulvar",
                       "belediye", "belediyesi", "müdürlüğü", "valiliği", "ilçe", "köyü",
                       "semti", "bölgesi", "merkezi", "projesi", "alanı"];

  var HARF = "A-Za-zÇĞİÖŞÜçğıöşü0-9_";
  var BUYUK = "A-ZÇĞİÖŞÜ";

  /* ------------------------------------------------------------ metin */

  function kucuk(m) {
    return String(m || "").replace(/İ/g, "i").replace(/I/g, "ı")
      .replace(/Ç/g, "ç").replace(/Ğ/g, "ğ").replace(/Ö/g, "ö")
      .replace(/Ş/g, "ş").replace(/Ü/g, "ü").toLowerCase();
  }

  var TR_HARF = /[çğıöşüÇĞİÖŞÜ]/;
  function etiketKucuk(k) { return TR_HARF.test(k) ? kucuk(k) : String(k).toLowerCase(); }

  function sadelestir(m) {
    return kucuk(m).replace(new RegExp("[^" + HARF + "]+", "g"), " ").trim();
  }

  function kokle(kelime, tur) {
    var ekler = S.ek_listesi || [], k = kucuk(kelime), i, ek, bulundu;
    tur = tur || 2;
    for (var t = 0; t < tur; t++) {
      bulundu = false;
      for (i = 0; i < ekler.length; i++) {
        ek = ekler[i];
        if (k.length - ek.length >= 3 && k.slice(-ek.length) === ek) {
          k = k.slice(0, -ek.length); bulundu = true; break;
        }
      }
      if (!bulundu) break;
    }
    return k;
  }

  /* "kaza" kelimesi "kazandırılıyor" icinde bulunmasin diye kelime sinirina bakar */
  function gecer(anahtar, duz) {
    var a = kucuk(anahtar);
    if (a.indexOf(" ") >= 0) return duz.indexOf(a) >= 0;
    var parcalar = duz.split(" ");
    for (var i = 0; i < parcalar.length; i++) {
      var p = parcalar[i];
      if (p === a || (p.indexOf(a) === 0 && p.length - a.length <= 3)) return true;
    }
    return false;
  }

  function cumlele(metin) {
    if (!metin) return [];
    return String(metin).trim()
      .split(new RegExp("(?<=[.!?])\\s+(?=[" + BUYUK + "0-9])"))
      .map(function (c) { return c.trim(); })
      .filter(function (c) { return c.length > 25; });
  }

  function ekEkle(isim) {
    if (!isim) return "";
    var temiz = String(isim).trim().replace(/\.+$/, "");
    var kucukHal = kucuk(temiz);
    var son = kucukHal.slice(-1);
    var sonUnlu = "e";
    for (var i = kucukHal.length - 1; i >= 0; i--) {
      if (UNLULER.indexOf(kucukHal[i]) >= 0) { sonUnlu = kucukHal[i]; break; }
    }
    var tablo = { a: "ın", "ı": "ın", e: "in", i: "in", o: "un", u: "un", "ö": "ün", "ü": "ün" };
    var ek = tablo[sonUnlu] || "in";
    if (UNLULER.indexOf(son) >= 0) ek = "n" + ek;
    return temiz + "'" + ek;
  }

  var OZEL_RE = new RegExp(
    "[" + BUYUK + "][" + HARF + "]*(?:['’][" + HARF + "]+)?" +
    "(?:\\s+[" + BUYUK + "][" + HARF + "]*(?:['’][" + HARF + "]+)?)*", "g");
  var CUMLE_BASI = /(?:^|[.!?:]\s+|\n)\s*$/;

  function ozelIsimler(metin, enUzunObek) {
    if (!metin) return [];
    enUzunObek = enUzunObek || 3;
    var bulunan = [], esle;
    OZEL_RE.lastIndex = 0;
    while ((esle = OZEL_RE.exec(metin)) !== null) {
      var parcalar = esle[0].split(/\s+/);
      var oncesi = metin.slice(Math.max(0, esle.index - 3), esle.index);
      if (CUMLE_BASI.test(oncesi) || esle.index === 0) parcalar = parcalar.slice(1);
      if (!parcalar.length) continue;
      if (parcalar.length > enUzunObek) parcalar = parcalar.slice(-enUzunObek);
      var obek = parcalar.join(" ").trim().replace(new RegExp("['’][" + HARF + "]+$"), "");
      // Python tarafi 2 harfli buyuk kisaltmalari da isim sayar: TL, AB, BB.
      var kisaltma = obek.length >= 2 && /[A-ZÇĞİÖŞÜ]/.test(obek) && !/[a-zçğıöşü]/.test(obek);
      if (obek.length >= 3 || kisaltma) bulunan.push(obek);
    }
    var gorulen = {}, sonuc = [];
    bulunan.forEach(function (o) {
      var k = kucuk(o);
      if (!gorulen[k]) { gorulen[k] = true; sonuc.push(o); }
    });
    return sonuc;
  }

  /* Ad hic yoksa bos doner — atif uydurulmaz, editore doldurtulur. */
  function yayinAdi(kaynak) {
    var ad = (kaynak.kaynak_adi || "").trim();
    if (!ad || (ad.indexOf(".") >= 0 && ad.indexOf(" ") < 0)) {
      var ham = ad || kaynak.kaynak_alan || "";
      if (!ham) return "";
      var kokAd = ham.split(".")[0];
      ad = kokAd.charAt(0).toUpperCase() + kokAd.slice(1);
    }
    return ad;
  }

  var ATIF_YER_TUTUCU = "[kaynak yayının adı]'nın haberine göre";

  function atifKur(kaynak) {
    var ad = yayinAdi(kaynak);
    return ad ? (ekEkle(ad) + " haberine göre") : ATIF_YER_TUTUCU;
  }

  function slugla(metin, uzunluk) {
    var esle = { "ç": "c", "ğ": "g", "ı": "i", "ö": "o", "ş": "s", "ü": "u" };
    var d = kucuk(metin).replace(/[çğıöşü]/g, function (h) { return esle[h]; });
    d = d.replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
    return d.slice(0, uzunluk || 60).replace(/-+$/, "") || "taslak";
  }

  /* ------------------------------------------------------------ alanlar */

  function havuz(k) {
    return [k.orijinal_baslik || "", k.orijinal_spot || "", k.orijinal_govde || ""];
  }

  function kategoriBul(kaynak) {
    var h = havuz(kaynak), agirliklar = [3, 2, 1], puanlar = {};
    h.forEach(function (metin, i) {
      var duz = sadelestir(metin);
      if (!duz) return;
      var kelimeler = duz.split(" "), koklu = {};
      kelimeler.forEach(function (k) { koklu[kokle(k)] = true; });
      var kelimeKume = {};
      kelimeler.forEach(function (k) { kelimeKume[k] = true; });
      Object.keys(S.kategori_anahtarlari || {}).forEach(function (kategori) {
        var anahtarlar = S.kategori_anahtarlari[kategori];
        Object.keys(anahtarlar).forEach(function (anahtar) {
          var katsayi = anahtarlar[anahtar], vurdu;
          if (anahtar.indexOf(" ") >= 0) vurdu = duz.indexOf(anahtar) >= 0;
          else vurdu = !!kelimeKume[anahtar] || !!koklu[kokle(anahtar)];
          if (vurdu) puanlar[kategori] = (puanlar[kategori] || 0) + katsayi * agirliklar[i];
        });
      });
    });
    var enIyi = "Gündem", enYuksek = 0;
    Object.keys(puanlar).forEach(function (k) {
      if (puanlar[k] > enYuksek) { enYuksek = puanlar[k]; enIyi = k; }
    });
    return enIyi;
  }

  function ilceBul(kaynak) {
    var h = havuz(kaynak);
    var duz = sadelestir(h[0] + " " + h[0] + " " + h[1] + " " + h[2]);
    var bulunan = {}, enIyi = null, enYuksek = 0;
    Object.keys(S.ilce_ipuclari || {}).forEach(function (ilce) {
      var sayi = 0;
      S.ilce_ipuclari[ilce].forEach(function (ip) {
        var parca = kucuk(ip), idx = duz.indexOf(parca);
        while (idx >= 0) { sayi++; idx = duz.indexOf(parca, idx + parca.length); }
      });
      if (sayi) {
        bulunan[ilce] = sayi;
        if (sayi > enYuksek) { enYuksek = sayi; enIyi = ilce; }
      }
    });
    var bursaVar = enIyi !== null || (S.bursa_ipuclari || []).some(function (ip) {
      return duz.indexOf(kucuk(ip)) >= 0;
    });
    if (enIyi) {
      return { ilce: enIyi, bursa: true,
        aciklama: "Haber " + enIyi + " ile ilişkili; metinde " + enYuksek + " kez geçiyor." };
    }
    if (bursaVar) {
      return { ilce: "Bursa geneli", bursa: true,
        aciklama: "Bursa geçiyor ancak tek bir ilçeye bağlanmıyor." };
    }
    return { ilce: "Bursa dışı", bursa: false,
      aciklama: "Metinde Bursa ya da ilçeleriyle bağ kuran bir ipucu yok. Haberi zorla " +
                "yerelleştirmeyin; yerel bir açı bulunamıyorsa ajans/dış haber olarak girin." };
  }

  function etiketBul(kaynak, enFazla) {
    enFazla = enFazla || 7;
    var h = havuz(kaynak), agirliklar = [3, 2, 1];
    var durak = {}, unvan = {};
    (S.durak_kelimeler || []).forEach(function (d) { durak[kokle(d)] = true; });
    (S.unvanlar || []).forEach(function (u) { unvan[kokle(u)] = true; });

    var sayac = {};
    var kelimeRe = new RegExp("[" + HARF + "]+", "g");
    h.forEach(function (metin, i) {
      var esle;
      kelimeRe.lastIndex = 0;
      while ((esle = kelimeRe.exec(metin)) !== null) {
        var kelime = esle[0];
        if (kelime.length < 4 || /^\d+$/.test(kelime)) continue;
        var kok = kokle(kelime);
        if (durak[kok] || unvan[kok] || kok.length < 3) continue;
        if (!sayac[kok]) sayac[kok] = { puan: 0, ham: kelime };
        sayac[kok].puan += agirliklar[i];
      }
    });

    var etiketler = Object.keys(sayac)
      .sort(function (a, b) { return sayac[b].puan - sayac[a].puan; })
      .slice(0, enFazla)
      .map(function (k) { return etiketKucuk(sayac[k].ham); });

    ozelIsimler(h[0] + ". " + h[1], 2).slice(0, 3).forEach(function (isim) {
      var e = etiketKucuk(isim);
      if (etiketler.indexOf(e) < 0 && e.split(" ").length <= 2) etiketler.unshift(e);
    });

    return etiketler.filter(function (e) {
      return !etiketler.some(function (d) { return e !== d && d.split(" ").indexOf(e) >= 0; });
    }).slice(0, enFazla);
  }

  function hassasBul(kaynak) {
    var h = havuz(kaynak), duz = sadelestir(h.join(" "));
    var bulgular = [];
    Object.keys(S.hassas_anahtarlar || {}).forEach(function (tur) {
      var veri = S.hassas_anahtarlar[tur], temiz = duz;
      (veri.haric || []).forEach(function (kalip) {
        temiz = temiz.split(kucuk(kalip)).join(" ");
      });
      if (veri.baglam && !veri.baglam.some(function (b) { return gecer(b, temiz); })) return;
      var vurus = veri.kelimeler.filter(function (k) { return gecer(k, temiz); }).length;
      if (vurus) bulgular.push({ tur: tur, vurus: vurus, uyari: veri.uyari });
    });
    if (!bulgular.length) return { var_mi: false, turu: "", uyari: "" };
    bulgular.sort(function (a, b) { return b.vurus - a.vurus; });
    var turler = bulgular.map(function (b) { return b.tur; }).join(", ");
    return {
      var_mi: true, turu: bulgular[0].tur,
      uyari: bulgular[0].uyari + (bulgular.length > 1
        ? " (Ayrıca işaretlenen başlıklar: " + turler + ".)" : "")
    };
  }

  var TARIH_RE = /\b\d{1,2}\s+(?:Ocak|Şubat|Mart|Nisan|Mayıs|Haziran|Temmuz|Ağustos|Eylül|Ekim|Kasım|Aralık)\s+\d{4}\b/g;

  function dogrulanacaklar(kaynak, enFazla) {
    enFazla = enFazla || 8;
    var h = havuz(kaynak);
    var tam = h[0] + ". " + h[1] + " " + h[2];
    var duz = sadelestir(tam), maddeler = [];

    // Sayidan sonraki birim kelimelerini oldugu gibi topla: "45 milyon TL",
    // yalnizca "45 milyon" degil. Ozgun metinde arandigi icin buyuk harf korunur.
    var birimKume = {};
    (S.birimler || []).forEach(function (b) {
      b.split(" ").forEach(function (p) { birimKume[kucuk(p)] = true; });
    });
    var sayiRe = new RegExp("(\\d[\\d.,]*)((?:\\s+[" + HARF + "%]+){0,2})", "g");
    var sesle;
    while ((sesle = sayiRe.exec(tam)) !== null) {
      var parcalar = [];
      var kelimeler = sesle[2].split(/\s+/).filter(function (k) { return k; });
      for (var ki = 0; ki < kelimeler.length; ki++) {
        var temizK = kelimeler[ki].replace(/[.,;:]+$/, "");
        if (birimKume[kucuk(temizK)]) parcalar.push(temizK); else break;
      }
      if (parcalar.length) {
        var madde = "\u201C" + sesle[1] + " " + parcalar.join(" ") +
                    "\u201D rakam\u0131n\u0131 resm\u00EE kaynaktan teyit edin.";
        if (maddeler.indexOf(madde) < 0) maddeler.push(madde);
      }
    }

    TARIH_RE.lastIndex = 0;
    (tam.match(TARIH_RE) || []).slice(0, 2).forEach(function (t) {
      maddeler.push("“" + t + "” tarihini kaynak belgeyle karşılaştırın.");
    });

    ozelIsimler(h[0] + ". " + h[1], 3).slice(0, 3).forEach(function (isim) {
      maddeler.push("“" + isim + "” yazılışını ve varsa unvanını teyit edin.");
    });

    for (var i = 0; i < (S.teyit_kaliplari || []).length; i++) {
      if (duz.indexOf(kucuk(S.teyit_kaliplari[i])) >= 0) {
        maddeler.push("Haberde “" + S.teyit_kaliplari[i] + "” kalıbıyla verilen bilgi tek " +
                      "kaynağa dayanıyor; ikinci bir kaynaktan doğrulayın.");
        break;
      }
    }

    if (!yayinAdi(kaynak)) {
      maddeler.unshift("Kaynak yayının adı girilmedi — atıf cümlesindeki yer tutucuyu " +
                       "gerçek yayın adıyla değiştirin.");
    }
    if (kaynak.gorsel_url) {
      maddeler.push("Kaynağın fotoğrafı yalnızca referanstır — hak durumu doğrulanmadan " +
                    "yayına giremez.");
    }
    if (!kaynak.yayin_tarihi) {
      maddeler.push("Kaynak haberin yayın tarihi ayıklanamadı; sayfadan elle kontrol edin.");
    }
    if (kaynak.ayiklama_guveni === "dusuk") {
      maddeler.push("Ayıklama güveni düşük — kaynağı elle açıp gövdeyi karşılaştırın.");
    }
    return maddeler.slice(0, enFazla);
  }

  function tezgahKur(kaynak, enFazla) {
    enFazla = enFazla || 12;
    var cumleler = cumlele(kaynak.orijinal_govde || "");
    var malzeme = cumleler.map(function (c, i) {
      var sayiVar = /\d/.test(c);
      var alintiVar = /["“”]|\bdedi\b|\bsöyledi\b|\baçıkladı\b|\bbelirtti\b/.test(c);
      var isimSayisi = ozelIsimler(c).length;
      var puan = Math.min(100, 30 + isimSayisi * 8 + (sayiVar ? 20 : 0) +
                          (alintiVar ? 10 : 0) + Math.min(20, Math.floor(c.length / 12)));
      var oneri = i === 0 ? "giriş" : (sayiVar ? "rakam" : (alintiVar ? "alıntı adayı" : "gelişme"));
      return { metin: c, puan: puan, oneri: oneri };
    });
    malzeme.sort(function (a, b) { return b.puan - a.puan; });
    return malzeme.slice(0, enFazla);
  }

  function onemBul(kategori, bursaVar, kelime) {
    if (!bursaVar) return "normal";
    var agir = ["Yargı", "Siyaset", "Çevre ve su", "Asayiş", "Ulaşım", "Sağlık"];
    return (agir.indexOf(kategori) >= 0 && kelime >= 120) ? "one_cikan" : "normal";
  }

  function taslakUretKural(kaynak) {
    var kategori = kategoriBul(kaynak);
    var yer = ilceBul(kaynak);
    var kelime = parseInt(kaynak.kelime_sayisi, 10) || 0;
    var atif = atifKur(kaynak);

    var taslak = {
      baslik_secenekleri: [
        { metin: "", gerekce: "Düz haber başlığı: ne oldu, kim yaptı, nerede. En fazla 70 karakter." },
        { metin: "", gerekce: "Sonuç/etki odaklı: bu gelişme okur için ne değiştiriyor?" },
        { metin: "", gerekce: "Kısa ve vurucu: 6-7 kelime. Tıklama tuzağı yok." }
      ],
      onerilen_baslik_indeksi: 0,
      spot: "",
      uc_madde: ["", "", ""],
      govde: [
        { tur: "paragraf", metin: "" },
        { tur: "paragraf", metin: "" },
        { tur: "ara_baslik", metin: "" },
        { tur: "paragraf", metin: "" },
        { tur: "paragraf", metin: "" }
      ],
      kategori: kategori,
      ilce: yer.ilce,
      etiketler: etiketBul(kaynak),
      seo_baslik: "", seo_aciklama: "", url_slug: "",
      gorsel_alt: "", gorsel_altyazi: "",
      okuma_suresi_dk: kelime ? Math.max(1, Math.round(kelime / 200)) : 1,
      onem: onemBul(kategori, yer.bursa, kelime),
      kaynak_atfi: atif,
      dogrulanmasi_gerekenler: dogrulanacaklar(kaynak),
      hassas_konu: hassasBul(kaynak),
      bursa_ilgisi: { var_mi: yer.bursa, aciklama: yer.aciklama },
      editor_notu: "Bu taslak kural tabanlı motorla hazırlandı — dil üretimi yapılmadı. " +
        "Kategori, ilçe, etiketler, önem ve uyarılar sözlük ve sezgiyle dolduruldu; başlık, " +
        "spot, üç madde ve gövde kasıtlı olarak boş bırakıldı. Ham malzeme panelinden " +
        "yararlanarak haberi kendi cümlelerinizle yazın; kaynağın cümlelerini kopyalamayın. " +
        "Kaynak, yayınlanan sayfada ayrı bir bölmede gösterilir; gövdeye atıf " +
        "cümlesi koymak zorunda değilsiniz."
    };

    return {
      taslak: taslak,
      uretim: { saglayici: "kural", model: "", surum: "1.0",
                zaman: new Date().toISOString().slice(0, 19) + "+00:00" },
      tezgah: tezgahKur(kaynak)
    };
  }

  /* ------------------------------------------------------------ konu takibi */

  var KESME_EKI = /['’][a-zçğıöşü]{1,6}/g;

  function kokluKume(degerler) {
    var kume = {};
    (degerler || []).forEach(function (d) {
      sadelestir(String(d)).split(" ").forEach(function (p) {
        if (p.length >= 3) kume[kokle(p)] = true;
      });
    });
    return kume;
  }

  function isimHaritasi(isimler) {
    var harita = {};
    (isimler || []).forEach(function (isim) {
      var gosterim = String(isim || "").trim();
      if (!gosterim) return;
      sadelestir(gosterim.replace(KESME_EKI, "")).split(" ").forEach(function (p) {
        if (p.length >= 4 && !harita[kokle(p)]) harita[kokle(p)] = gosterim;
      });
    });
    return harita;
  }

  function zayifKokler() {
    var zayif = Object.keys(S.ilce_ipuclari || {}).concat(["Bursa", "Bursa geneli", "Bursa dışı"]);
    Object.keys(S.ilce_ipuclari || {}).forEach(function (i) {
      zayif = zayif.concat(S.ilce_ipuclari[i]);
    });
    zayif = zayif.concat(S.unvanlar || [], S.durak_kelimeler || [], GENEL_ISIMLER);
    return kokluKume(zayif);
  }

  function gosterimTemizle(obek) {
    var atilacak = {};
    (S.unvanlar || []).concat(GENEL_ISIMLER).forEach(function (u) { atilacak[kucuk(u)] = true; });
    var parcalar = String(obek).replace(KESME_EKI, "").split(/\s+/);
    while (parcalar.length > 1 && atilacak[kucuk(parcalar[0])]) parcalar.shift();
    return parcalar.join(" ");
  }

  function secilenBaslik(taslak) {
    var secenekler = taslak.baslik_secenekleri || [];
    if (!secenekler.length) return "";
    var i = taslak.onerilen_baslik_indeksi || 0;
    return (secenekler[i] || secenekler[0]).metin || "";
  }

  function parmakIzi(taslak, kaynak) {
    var baslik = kaynak.orijinal_baslik || "", spot = kaynak.orijinal_spot || "";
    var govde = kaynak.orijinal_govde || "", secili = secilenBaslik(taslak);
    var isimler = ozelIsimler(secili + ". " + baslik + ". " + spot, 3)
      .map(function (i) { return gosterimTemizle(i); });
    return {
      isimler: isimHaritasi(isimler),
      zayif: zayifKokler(),
      etiketler: kokluKume(taslak.etiketler || []),
      kategori: taslak.kategori || "",
      ilce: taslak.ilce || "",
      tarih: (kaynak.yayin_tarihi || "").slice(0, 10) || new Date().toISOString().slice(0, 10),
      duz: sadelestir(secili + ". " + baslik + ". " + spot + " " + govde)
    };
  }

  function tarihCoz(metin) {
    var m = /^(\d{4})-(\d{2})(?:-(\d{2}))?/.exec(metin || "");
    if (!m) return null;
    return new Date(Date.UTC(+m[1], +m[2] - 1, +(m[3] || 1)));
  }

  function gunFarki(a, b) {
    var ta = tarihCoz(a), tb = tarihCoz(b);
    if (!ta || !tb) return null;
    return Math.abs(Math.round((ta - tb) / 86400000));
  }

  function puanla(parmak, aday, tur) {
    var ham = 0, gerekceler = [];

    var adayIsimKaynagi = tur === "haber"
      ? ozelIsimler(aday.baslik || "", 3)
      : (aday.kisiler || []).concat(aday.kurumlar || []);
    adayIsimKaynagi = adayIsimKaynagi.concat([aday.ad || aday.baslik || ""]);
    var adayKokler = isimHaritasi(adayIsimKaynagi);

    var ortakIsim = [];
    Object.keys(parmak.isimler).forEach(function (kok) {
      if (parmak.zayif[kok] || !adayKokler[kok]) return;
      var g = parmak.isimler[kok];
      if (ortakIsim.indexOf(g) < 0) ortakIsim.push(g);
    });
    if (ortakIsim.length) {
      ham += 5 * ortakIsim.length;
      gerekceler.push(ortakIsim.length + " ortak özel isim: " + ortakIsim.slice(0, 4).join(", "));
    }

    if (tur === "konu") {
      var eslesen = (aday.anahtarlar || []).filter(function (a) { return gecer(a, parmak.duz); });
      if (eslesen.length) {
        ham += 4 * eslesen.length;
        gerekceler.push(eslesen.length + " konu anahtarı: " + eslesen.slice(0, 4).join(", "));
      }
    }

    var adayEtiket = kokluKume(aday.etiketler || []);
    var ortakEtiket = Object.keys(parmak.etiketler).filter(function (e) { return adayEtiket[e]; });
    if (ortakEtiket.length) {
      ham += 3 * ortakEtiket.length;
      gerekceler.push(ortakEtiket.length + " ortak etiket");
    }

    if (parmak.kategori && parmak.kategori === aday.kategori) {
      ham += 2; gerekceler.push("Aynı kategori: " + parmak.kategori);
    }
    if (parmak.ilce && parmak.ilce === aday.ilce) {
      ham += 2; gerekceler.push("Aynı ilçe: " + parmak.ilce);
    }

    var sonTarih = aday.tarih || "";
    if (tur === "konu" && (aday.maddeler || []).length) {
      sonTarih = aday.maddeler.reduce(function (en, m) {
        return (m.tarih || "") > en ? (m.tarih || "") : en;
      }, "");
    }
    var fark = gunFarki(parmak.tarih, sonTarih);
    if (fark !== null && fark <= 90) {
      ham += fark <= 30 ? 2 : 1;
      gerekceler.push("Son gelişme " + fark + " gün önce");
    }

    if (aday.durum === "kapali") {
      ham *= 0.5;
      gerekceler.push("Dosya kapalı — puan yarıya indirildi");
    }

    return { skor: Math.min(100, Math.round(ham * 100 / 25)), gerekceler: gerekceler };
  }

  function ilgiliBul(parmak, enFazla) {
    enFazla = enFazla || 5;
    var adaylar = [];

    KONULAR.forEach(function (konu) {
      var p = puanla(parmak, konu, "konu");
      if (p.skor >= OLASI_ESIK) {
        adaylar.push({
          tur: "konu", id: konu.id, ad: konu.ad, skor: p.skor,
          guclu: p.skor >= GUCLU_ESIK, gerekceler: p.gerekceler,
          madde_sayisi: (konu.maddeler || []).length,
          son_maddeler: (konu.maddeler || []).slice(-2),
          hassas: konu.hassas || { var_mi: false }
        });
      }
    });

    ARSIV.forEach(function (haber) {
      var p = puanla(parmak, haber, "haber");
      if (p.skor >= OLASI_ESIK) {
        adaylar.push({
          tur: "haber", id: haber.slug, ad: haber.baslik, skor: p.skor,
          guclu: p.skor >= GUCLU_ESIK, gerekceler: p.gerekceler,
          tarih: haber.tarih || "", konu_id: haber.konu_id || null
        });
      }
    });

    adaylar.sort(function (a, b) {
      if (b.skor !== a.skor) return b.skor - a.skor;
      return (a.tur === "konu" ? 0 : 1) - (b.tur === "konu" ? 0 : 1);
    });
    return adaylar.slice(0, enFazla);
  }

  // Python karsiligi: konu_eslestirme._ad_turu
  var YER_SONU = ["mahallesi", "caddesi", "sokağı", "sokak", "bulvarı", "meydanı",
    "parkı", "çayı", "deresi", "barajı", "köyü", "ovası", "tepesi", "yolu", "kavşağı"];
  var KURUM_SONU = ["belediyesi", "başkanlığı", "müdürlüğü", "bakanlığı", "üniversitesi",
    "hastanesi", "genel müdürlüğü", "odası", "birliği", "derneği", "vakfı", "kulübü",
    "a.ş.", "valiliği", "kaymakamlığı"];
  var FIIL_SONU = ["ıyor", "iyor", "uyor", "üyor", "acak", "ecek", "mış", "miş", "muş",
    "müş", "ldı", "ldi", "ldu", "ldü", "tı", "ti", "du", "dü", "yor"];

  function biterMi(metin, sonlar) {
    for (var i = 0; i < sonlar.length; i++) {
      if (metin.slice(-sonlar[i].length) === sonlar[i]) return true;
    }
    return false;
  }

  function adTuru(ad) {
    var k = kucuk(ad).trim();
    if (biterMi(k, FIIL_SONU)) return "artik";
    if (biterMi(k, KURUM_SONU)) return "kurum";
    if (biterMi(k, YER_SONU)) return "yer";
    return ad.split(/\s+/).length >= 2 ? "kisi" : "tekil";
  }

  function konuOnerisi(parmak, taslak) {
    var gorulen = {};
    var isimler = [];
    Object.keys(parmak.isimler).forEach(function (k) {
      if (parmak.zayif[k]) return;
      var g = parmak.isimler[k];
      if (gorulen[g]) return;           // ayni gosterimi tekrar uretme
      gorulen[g] = true;
      isimler.push(g);
    });
    isimler.sort(function (a, b) { return b.length - a.length; });

    var turler = {};
    isimler.forEach(function (i) { turler[i] = adTuru(i); });

    // Dosya adi yer/kurum/kisi/tekil olabilir; fiil kalintisi ve ay adi olamaz.
    var adaylar = isimler.filter(function (i) {
      return turler[i] !== "artik" && AYLAR.indexOf(i) < 0;
    });
    var ad = adaylar[0] || taslak.kategori || "Yeni dosya";
    var slug = slugla(ad);
    return {
      id: slug, ad: ad, slug: slug, durum: "acik",
      kategori: taslak.kategori || "", ilce: taslak.ilce || "",
      anahtarlar: (taslak.etiketler || []).slice(0, 5),
      kisiler: isimler.filter(function (i) { return turler[i] === "kisi"; }).slice(0, 3),
      kurumlar: isimler.filter(function (i) { return turler[i] === "kurum"; }).slice(0, 3),
      hassas: taslak.hassas_konu || { var_mi: false, turu: "", uyari: "" },
      not: "", maddeler: []
    };
  }

  function konuyaBagla(konu, taslak, kaynak) {
    var baslik = secilenBaslik(taslak) || kaynak.orijinal_baslik || "(başlık yazılmadı)";
    var madde = {
      tarih: (kaynak.yayin_tarihi || new Date().toISOString()).slice(0, 10),
      baslik: baslik,
      ozet: taslak.spot || "",
      // Editor slug yazmadiysa basliktan turet; yoksa haber arsive dusmez
      haber_slug: taslak.url_slug || slugla(baslik),
      yeni: true
    };
    konu.maddeler = (konu.maddeler || []).concat([madde]);
    konu.maddeler.sort(function (a, b) {
      return (a.tarih || "") < (b.tarih || "") ? -1 : ((a.tarih || "") > (b.tarih || "") ? 1 : 0);
    });
    taslak.konu = { id: konu.id, ad: konu.ad, slug: konu.slug };
    return madde;
  }

  function tarihYaz(tarih, gorunen) {
    if (gorunen) return gorunen;
    var m = /^(\d{4})-(\d{2})(?:-(\d{2}))?$/.exec(tarih || "");
    if (!m) return tarih || "";
    return m[3] ? (parseInt(m[3], 10) + " " + AYLAR[+m[2] - 1] + " " + m[1])
                : (AYLAR[+m[2] - 1] + " " + m[1]);
  }

  function kacir(m) {
    return String(m == null ? "" : m).replace(/&/g, "&amp;").replace(/</g, "&lt;")
      .replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }

  function kronolojiHtml(konu) {
    var satirlar = ['<ol class="zaman">'];
    (konu.maddeler || []).forEach(function (m) {
      satirlar.push("  <li>");
      satirlar.push('    <time datetime="' + kacir(m.tarih) + '">' +
                    kacir(tarihYaz(m.tarih, m.gorunen)) + "</time>");
      satirlar.push("    <h3>" + kacir(m.baslik) + "</h3>");
      if (m.ozet) satirlar.push("    <p>" + kacir(m.ozet) + "</p>");
      satirlar.push("  </li>");
    });
    satirlar.push("</ol>");
    if (konu.not) satirlar.push('<p class="zaman-not">' + kacir(konu.not) + "</p>");
    return satirlar.join("\n");
  }

  /* Yapistirilan metinden ayiklayici ciktisina benzer bir kaynak nesnesi kurar. */
  function metindenKaynak(alanlar) {
    var govde = (alanlar.govde || "").replace(/\r/g, "").trim();
    var satirlar = govde.split(/\n+/).map(function (s) { return s.trim(); })
      .filter(function (s) { return s; });
    var baslik = (alanlar.baslik || "").trim() || satirlar.shift() || "";
    var spot = (alanlar.spot || "").trim();
    if (!spot && satirlar.length > 1 && satirlar[0].length < 320) spot = satirlar.shift();
    var tam = satirlar.join(" ");
    var kelime = tam ? tam.split(/\s+/).length : 0;
    var adres = (alanlar.adres || "").trim();
    var alan = "";
    try { if (adres) alan = new URL(adres).hostname.replace(/^www\./, ""); } catch (e) { alan = ""; }
    return {
      kaynak_url: adres, kaynak_alan: alan,
      kaynak_adi: (alanlar.yayin || "").trim() || alan || "",
      orijinal_baslik: baslik, orijinal_spot: spot, orijinal_govde: tam,
      gorsel_url: "", gorsel_alt: "", yazar: "", yayin_tarihi: "", guncelleme_tarihi: "",
      dil: "tr", kelime_sayisi: kelime,
      ayiklama_yontemleri: ["elle-yapistirma"],
      ayiklama_guveni: kelime >= 150 ? "yuksek" : (kelime >= 60 ? "orta" : "dusuk")
    };
  }

  kok.BHMotor = {
    kucuk: kucuk, sadelestir: sadelestir, slugla: slugla, ekEkle: ekEkle,
    taslakUretKural: taslakUretKural, metindenKaynak: metindenKaynak,
    parmakIzi: parmakIzi, ilgiliBul: ilgiliBul, konuOnerisi: konuOnerisi,
    konuyaBagla: konuyaBagla, kronolojiHtml: kronolojiHtml, tarihYaz: tarihYaz,
    konular: KONULAR, arsiv: ARSIV,
    GUCLU_ESIK: GUCLU_ESIK, OLASI_ESIK: OLASI_ESIK
  };
})(window);
