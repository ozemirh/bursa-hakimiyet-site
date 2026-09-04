"""Tarama durumunu dogru sayar ve yazar.

DIKKAT: `ilerleme.json` iki ayri sayac tutuyor:
  tamamlanan     - BU kosuda yeni cekilen
  onceden_vardi  - kosu basladiginda diskte zaten olan
Toplam ilerleme ikisinin TOPLAMIDIR. Yalniz `tamamlanan`a bakmak,
kaldigi yerden devam eden bir taramada ilerlemeyi olduğundan cok
dusuk gosterir (olcum hatasi yasandi: 106.468 kayit 13.807 sanildi).
"""
import json, os, sys, time
from datetime import datetime


def oku(yol, deneme=5):
    """Tarama surerken ilerleme dosyasi saniyede bir bastan yaziliyor; tam o
    anda okursak yarim JSON gelir. Bu bir hata degil, yaris; kisa bekleyip
    tekrar dene."""
    for kalan in range(deneme, 0, -1):
        try:
            with open(yol, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, ValueError):
            if kalan == 1:
                return None
            time.sleep(0.3)

KOK = os.environ.get("BH_ARSIV_KOK", "D:/bursa-hakimiyet-arsiv")
AILELER = [("yazar", "ilerleme-yazar.json"), ("galeri", "ilerleme-galeri.json"),
           ("kose", "ilerleme-kose.json"), ("video", "ilerleme-video.json"),
           ("haber", "ilerleme.json"),
           # Sitemap disi eski haberler (2012 - 2021 Mart), kimlik sayarak
           # taraniyor. Hedef = kimlik araliginin buyuklugu; araliktaki olu
           # kimlikler yuzunden oran %100'e ulasmaz, %96 civari beklenir.
           ("eski", "ilerleme-eski.json")]

print(f"Arsiv koku: {KOK}\n")
print(f"  {'aile':8} {'ilerleme':>19}  {'oran':>6}  {'basarisiz':>9}  son guncelleme")
toplam_c = toplam_t = 0
for aile, dosya in AILELER:
    yol = os.path.join(KOK, dosya)
    if not os.path.exists(yol):
        print(f"  {aile:8} {'baslamadi':>19}")
        continue
    d = oku(yol)
    if d is None:
        print(f"  {aile:8} {'yaziliyor - okunamadi':>19}")
        continue
    hedef = d["toplam_url"]
    yapilan = d["tamamlanan"] + d.get("onceden_vardi", 0)
    toplam_c += yapilan; toplam_t += hedef
    an = d.get("son_guncelleme", "")[11:19]
    print(f"  {aile:8} {yapilan:>8,} / {hedef:>8,}  %{100*yapilan/hedef:5.1f}  "
          f"{d.get('basarisiz', 0):>9,}  {an}")
print(f"\n  {'TOPLAM':8} {toplam_c:>8,} / {toplam_t:>8,}  %{100*toplam_c/toplam_t:5.1f}")
