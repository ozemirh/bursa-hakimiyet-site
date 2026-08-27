#!/usr/bin/env bash
# Kalan sitemap ailelerini kucukten buyuge sirayla tarar.
# Kucuk aileler once: dordu birden ~43 bin kayit ve F4'un acik maddesini
# (yazar - kose - galeri - video sayfalari) kapatiyor; haber ailesinin
# kalani ~464 bin ve tek basina saatler suruyor.
PY="C:/Users/Asus/Desktop/bursa_hakimiyet_site/.venv/Scripts/python.exe"
BETIK="C:/Users/Asus/Desktop/bursa_hakimiyet_site/disa-aktarim/site_arsivleyici.py"
for aile in galeri kose video haber; do
  echo "=================== $aile basliyor: $(date '+%Y-%m-%d %H:%M:%S') ==================="
  "$PY" "$BETIK" --aile "$aile"
  echo "=================== $aile bitti: $(date '+%Y-%m-%d %H:%M:%S') (cikis=$?) ==================="
done
echo "TUM AILELER TAMAMLANDI: $(date '+%Y-%m-%d %H:%M:%S')"
