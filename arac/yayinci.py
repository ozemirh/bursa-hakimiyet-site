"""Yerel yayin sunucusu — editor sayfasindaki "Yayina gonder" dugmesi buraya baglanir.

    python arac/yayinci.py            # 127.0.0.1:8787
    python arac/yayinci.py --port 9000

Editor sayfasini YAYINCININ KENDISINDEN acin: http://127.0.0.1:8787/
Yalnizca standart kutuphane kullanir ve SADECE 127.0.0.1'e baglanir.

## Guvenlik (19 Ekim 2026, Paket F madde 5)

"Yalniz 127.0.0.1'e baglanir" tek basina koruma degildi: sunucu
`Access-Control-Allow-Origin: *` ve `Allow-Private-Network: true` gonderiyordu,
yani kullanicinin actigi HERHANGI bir web sitesi tarayici uzerinden
`/yayinla` ve `/ayikla` uclarini tetikleyebiliyordu (dosya yazma + sunucudan
istek). Simdi uc kapi var:

1. **Host denetimi** — `Host` basligi yalniz `127.0.0.1:PORT` ya da
   `localhost:PORT`. DNS rebinding (saldirganin alan adinin 127.0.0.1'e
   donmesi) bu basligi degistiremez.
2. **Koken denetimi** — `Origin` geldiyse izinli listede olmali: sayfanin
   acildigi yerel koken (`http://127.0.0.1:PORT`, `http://localhost:PORT`)
   ve `BH_YAYINCI_KOKENLER` ile verilenler. `*` yok, ozel ag izni yok.
   Dosyadan (file://) acilan sayfanin kokeni `null`dur ve kabul edilmez —
   `null` kokeni her sandbox iframe'i de tasir.
3. **Paylasilan jeton** — her POST `X-Yayinci-Jetonu` basligi tasimali.
   Jeton `BH_YAYINCI_JETONU` ortam degiskeninden, yoksa
   `arac/.yayinci-jetonu` dosyasindan okunur; o da yoksa sunucu her
   acilista rastgele uretir. Sayfa yayincidan acilinca jeton sayfaya
   gomulur (baska koken bu sayfayi okuyamaz).

Sunucu kapaliyken sayfa calismaya devam eder: dugme "yayin sunucusu kapali" der
ve baska hicbir sey degismez. Sayfanin bagimsizligi bozulmaz.
"""

from __future__ import annotations

import argparse
import functools
import hmac
import json
import os
import secrets
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import konu_eslestirme as ke  # noqa: E402
from ayiklayici import ayikla, getir  # noqa: E402
from kural_motoru import slugla, taslak_uret_kural  # noqa: E402
from yayin import KOK, YayinHatasi, yayinla  # noqa: E402

EN_BUYUK = 4 * 1024 * 1024   # 4 MB; taslak paketi bunun cok altinda
JETON_BASLIGI = "X-Yayinci-Jetonu"
JETON_DOSYASI = Path(__file__).resolve().parent / ".yayinci-jetonu"
EDITOR_SAYFASI = KOK / "yapay-zeka-editor.html"


# stdout yonlendirildiginde blok tamponlanir ve bilgi satirlari gunluge hic
# dusmez; erisim satirlari stderr'den gectigi icin yaniltici oluyordu.
yaz = functools.partial(print, flush=True)


def jeton_bul() -> str:
    """Ortam > yerel dosya > her acilista rastgele."""
    jeton = os.environ.get("BH_YAYINCI_JETONU", "").strip()
    if not jeton and JETON_DOSYASI.exists():
        jeton = JETON_DOSYASI.read_text(encoding="utf-8").strip()
    return jeton or secrets.token_urlsafe(32)


def izinli_kumeler(port: int) -> tuple[frozenset, frozenset]:
    """(izinli Host degerleri, izinli Origin degerleri)."""
    konaklar = {f"127.0.0.1:{port}", f"localhost:{port}"}
    kokenler = {f"http://127.0.0.1:{port}", f"http://localhost:{port}"}
    for k in os.environ.get("BH_YAYINCI_KOKENLER", "").split(","):
        k = k.strip().rstrip("/")
        if k and k != "null" and k != "*":
            kokenler.add(k)
    return frozenset(konaklar), frozenset(kokenler)


class Islem(BaseHTTPRequestHandler):
    server_version = "BHYayinci/1.1"

    # -- kapi --------------------------------------------------------------

    def _koken(self) -> str:
        return (self.headers.get("Origin") or "").strip()

    def _konak_gecerli(self) -> bool:
        """DNS rebinding: Host yalniz yerel ad + port olabilir."""
        return (self.headers.get("Host") or "").strip().lower() in self.server.izinli_konaklar

    def _koken_gecerli(self) -> bool:
        koken = self._koken()
        return not koken or koken in self.server.izinli_kokenler

    def _jeton_gecerli(self) -> bool:
        gelen = (self.headers.get(JETON_BASLIGI) or "").strip()
        return bool(gelen) and hmac.compare_digest(gelen, self.server.jeton)

    def _reddet(self, kod: int, neden: str) -> None:
        self.log_message("reddedildi (%s): %s %s", neden, self.command, self.path)
        self._yanit(kod, {"ok": False, "hata": "İstek reddedildi."}, cors=False)

    # -- yanit -------------------------------------------------------------

    def _basliklar(self, kod: int, uzunluk: int = 0, *, cors: bool = True,
                   tur: str = "application/json; charset=utf-8") -> None:
        self.send_response(kod)
        self.send_header("Content-Type", tur)
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        koken = self._koken()
        # Yalniz izinli kokene, adiyla. `*` ve ozel ag izni YOK.
        if cors and koken and koken in self.server.izinli_kokenler:
            self.send_header("Access-Control-Allow-Origin", koken)
            self.send_header("Vary", "Origin")
            self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
            self.send_header("Access-Control-Allow-Headers",
                             "Content-Type, " + JETON_BASLIGI)
        if uzunluk:
            self.send_header("Content-Length", str(uzunluk))
        self.end_headers()

    def _yanit(self, kod: int, veri: dict, cors: bool = True) -> None:
        govde = json.dumps(veri, ensure_ascii=False).encode("utf-8")
        self._basliklar(kod, len(govde), cors=cors)
        self.wfile.write(govde)

    def do_OPTIONS(self) -> None:            # noqa: N802
        if not self._konak_gecerli():
            self._reddet(421, "host")
            return
        if not self._koken() or not self._koken_gecerli():
            self._reddet(403, "origin")
            return
        self._basliklar(204)

    def do_GET(self) -> None:                # noqa: N802
        if not self._konak_gecerli():
            self._reddet(421, "host")
            return
        yol = self.path.split("?", 1)[0].rstrip("/")
        if yol in ("", "/editor"):
            self._editor()
        elif yol == "/durum":
            self._yanit(200, {"ok": True})
        else:
            self._yanit(404, {"ok": False, "hata": "Bilinmeyen adres."})

    def _editor(self) -> None:
        """Editor sayfasi, jeton gomulu. Baska koken bu yaniti OKUYAMAZ:
        CORS basligi yok, Host denetimi rebinding'i kapatiyor."""
        if not EDITOR_SAYFASI.exists():
            self._yanit(404, {"ok": False, "hata": "Editör sayfası bulunamadı."})
            return
        html = EDITOR_SAYFASI.read_text(encoding="utf-8")
        meta = '<meta name="bh-yayinci-jetonu" content="%s">' % self.server.jeton
        html = html.replace("<head>", "<head>\n" + meta, 1)
        govde = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(govde)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.end_headers()
        self.wfile.write(govde)

    def do_POST(self) -> None:               # noqa: N802
        if not self._konak_gecerli():
            self._reddet(421, "host")
            return
        if not self._koken_gecerli():
            self._reddet(403, "origin")
            return
        if not self._jeton_gecerli():
            self._reddet(403, "jeton")
            return
        adres = self.path.rstrip("/")
        if adres not in ("/yayinla", "/ayikla"):
            self._yanit(404, {"ok": False, "hata": "Bilinmeyen adres."})
            return
        try:
            uzunluk = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            uzunluk = 0
        if not 0 < uzunluk <= EN_BUYUK:
            self._yanit(413, {"ok": False, "hata": "Paket boyutu uygun degil."})
            return
        try:
            paket = json.loads(self.rfile.read(uzunluk).decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            self._yanit(400, {"ok": False, "hata": "Paket okunamadi (bozuk JSON)."})
            return

        if adres == "/ayikla":
            self._ayikla(paket)
            return

        try:
            sonuc = yayinla(paket)
        except YayinHatasi as e:
            self._yanit(200, {"ok": False, "hata": str(e)})
            return
        except Exception as e:               # noqa: BLE001 — sunucu ayakta kalsin
            self.log_error("yayin hatasi: %r", e)
            self._yanit(500, {"ok": False, "hata": "Yayin sirasinda beklenmeyen hata: %s" % e})
            return

        yaz("  yayinlandi: %s" % sonuc["baslik"])
        for y in sonuc["yayinlar"]:
            yaz("    tasarim %s -> %s" % (y["tasarim"], y["sayfa"]))
        self._yanit(200, {"ok": True, **sonuc})

    def _ayikla(self, istek: dict) -> None:
        """Adresi indirir, ayiklar ve kural motoruyla taslak iskeleti kurar.

        Tarayici CORS yuzunden rastgele bir siteyi cekemiyor; sayfa bu ucu
        cagirinca adres kutusu calisir hale geliyor. Model kullanilmaz —
        `haber_taslak.py --saglayici kural` ile ayni yol."""
        adres = (istek.get("adres") or "").strip()
        yontem = (istek.get("yontem") or "kural").strip()
        if not adres.lower().startswith(("http://", "https://")):
            self._yanit(200, {"ok": False, "hata": "Geçerli bir adres verin (http/https)."})
            return
        try:
            kaynak = ayikla(getir(adres), adres)
        except Exception as e:                # noqa: BLE001 — sunucu ayakta kalsin
            self._yanit(200, {"ok": False, "hata": "Kaynak alınamadı: %s" % e})
            return
        if not (kaynak.get("orijinal_govde") or "").strip():
            self._yanit(200, {"ok": False,
                              "hata": "Sayfadan metin çıkarılamadı (JavaScript ile "
                                      "kuruluyor ya da ödeme duvarı olabilir)."})
            return

        paket = {"kaynak": kaynak}
        if yontem == "tarayici":
            # B yolu: taslagi tarayicidaki motor.js kuracak, sunucu yalniz ayiklar.
            yaz("  ayiklandi (B yolu, taslagi tarayici kuracak): %s"
                  % (kaynak.get("orijinal_baslik") or "")[:55])
            self._yanit(200, {"ok": True, "paket": paket, "yontem": yontem})
            return
        if yontem in ("yz", "skill"):
            try:
                if yontem == "skill":
                    import yz_skill
                    paket.update(yz_skill.taslak_uret_skill(kaynak))
                else:
                    import yz_cli
                    paket.update(yz_cli.taslak_uret_cli(kaynak))
            except Exception as e:                # noqa: BLE001
                self._yanit(200, {"ok": False, "hata": str(e)})
                return
        else:
            paket.update(taslak_uret_kural(kaynak))
        t = paket.get("taslak")
        if t:
            konular, arsiv = ke.veri_yukle()
            parmak = ke.parmak_izi(t, kaynak)
            adaylar = ke.ilgili_bul(parmak, konular, arsiv)
            paket["konu_adaylari"] = adaylar
            if not adaylar:
                paket["konu_onerisi"] = ke.konu_onerisi(parmak, t)

        # Depodaki duzen: kural motoru ciktilari `kural-` onekli, model ciktilari
        # duz slug. Onek olmasa iki yol birbirinin dosyasini eziyordu.
        slug = slugla(kaynak.get("orijinal_baslik") or "haber")
        onek = "kural-" if yontem == "kural" else ""
        dosya = KOK / "arac" / "cikti" / (onek + slug + ".json")
        dosya.write_text(json.dumps(paket, ensure_ascii=False, indent=2), encoding="utf-8")
        yaz("  ayiklandi: %s — %s (guven: %s) -> %s"
              % ((kaynak.get("orijinal_baslik") or "")[:55], kaynak.get("kaynak_adi") or "?",
                 kaynak.get("ayiklama_guveni"), dosya.name))
        self._yanit(200, {"ok": True, "paket": paket, "dosya": dosya.name,
                          "yontem": yontem})

    def log_message(self, bicim: str, *args) -> None:
        sys.stderr.write("  %s\n" % (bicim % args))


def sunucu_kur(port: int, jeton: str | None = None) -> ThreadingHTTPServer:
    """Sunucuyu kurar (testler de kullanir). Port 0 = bos port."""
    sunucu = ThreadingHTTPServer(("127.0.0.1", port), Islem)
    gercek_port = sunucu.server_address[1]
    sunucu.jeton = jeton or jeton_bul()
    sunucu.izinli_konaklar, sunucu.izinli_kokenler = izinli_kumeler(gercek_port)
    return sunucu


def main() -> int:
    ayrist = argparse.ArgumentParser(description="Yerel yayin sunucusu")
    ayrist.add_argument("--port", type=int, default=8787)
    secim = ayrist.parse_args()

    sunucu = sunucu_kur(secim.port)
    print("Yayin sunucusu calisiyor: http://127.0.0.1:%d" % secim.port)
    print("Yayin klasoru: %s" % KOK)
    print("Editor sayfasini buradan acin: http://127.0.0.1:%d/" % secim.port)
    print("(Dosyadan acilan sayfa yayinciyi kullanamaz: koken ve jeton denetimi.)")
    print("Durdurmak icin Ctrl+C.")
    try:
        sunucu.serve_forever()
    except KeyboardInterrupt:
        print("\nDurduruldu.")
    finally:
        sunucu.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
