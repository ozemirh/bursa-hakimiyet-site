"""Yerel yayin sunucusu — editor sayfasindaki "Yayina gonder" dugmesi buraya baglanir.

    python arac/yayinci.py            # 127.0.0.1:8787
    python arac/yayinci.py --port 9000

Sayfa dosyadan (file://) acildigi icin tarayici disariya yazamaz; yazma isini bu
kucuk sunucu yapar. Yalnizca standart kutuphane kullanir ve SADECE 127.0.0.1'e
baglanir — disaridan erisilemez.

Sunucu kapaliyken sayfa calismaya devam eder: dugme "yayin sunucusu kapali" der
ve baska hicbir sey degismez. Sayfanin bagimsizligi bozulmaz.
"""

from __future__ import annotations

import argparse
import functools
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import konu_eslestirme as ke  # noqa: E402
from ayiklayici import ayikla, getir  # noqa: E402
from kural_motoru import slugla, taslak_uret_kural  # noqa: E402
from yayin import KOK, YayinHatasi, yayinla  # noqa: E402

EN_BUYUK = 4 * 1024 * 1024   # 4 MB; taslak paketi bunun cok altinda


# stdout yonlendirildiginde blok tamponlanir ve bilgi satirlari gunluge hic
# dusmez; erisim satirlari stderr'den gectigi icin yaniltici oluyordu.
yaz = functools.partial(print, flush=True)


class Islem(BaseHTTPRequestHandler):
    server_version = "BHYayinci/1.0"

    def _basliklar(self, kod: int, uzunluk: int = 0) -> None:
        self.send_response(kod)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        # Chrome, ozel aga (localhost) giden istekler icin bunu arayabiliyor.
        self.send_header("Access-Control-Allow-Private-Network", "true")
        if uzunluk:
            self.send_header("Content-Length", str(uzunluk))
        self.end_headers()

    def _yanit(self, kod: int, veri: dict) -> None:
        govde = json.dumps(veri, ensure_ascii=False).encode("utf-8")
        self._basliklar(kod, len(govde))
        self.wfile.write(govde)

    def do_OPTIONS(self) -> None:            # noqa: N802
        self._basliklar(204)

    def do_GET(self) -> None:                # noqa: N802
        if self.path.rstrip("/") in ("/durum", ""):
            self._yanit(200, {"ok": True, "kok": str(KOK)})
        else:
            self._yanit(404, {"ok": False, "hata": "Bilinmeyen adres."})

    def do_POST(self) -> None:               # noqa: N802
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


def main() -> int:
    ayrist = argparse.ArgumentParser(description="Yerel yayin sunucusu")
    ayrist.add_argument("--port", type=int, default=8787)
    secim = ayrist.parse_args()

    sunucu = ThreadingHTTPServer(("127.0.0.1", secim.port), Islem)
    print("Yayin sunucusu calisiyor: http://127.0.0.1:%d" % secim.port)
    print("Yayin klasoru: %s" % KOK)
    print("yapay-zeka-editor.html sayfasini acip \"Yayina gonder\" diyebilirsiniz.")
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
