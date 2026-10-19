#!/usr/bin/env bash
# Canlı veri tazeleme — Linux üretimi (canli-veri/tazele.ps1'in karşılığı).
# systemd çağırır: bh-canli@<grup>.service  (dagitim/systemd/).
#
#   canli-tazele.sh sik       piyasa + döviz              (15 dk)
#   canli-tazele.sh saatlik   hava + eczane               (60 dk)
#   canli-tazele.sh gunluk    namaz + puan + vizyon       (günde 1)
#   canli-tazele.sh haber     eczane + günün eczane haberi (günde 1, 08:20)
#
# Çıkış kodu: 0 tamam · 1 en az bir bileşen veri üretemedi. Betiklerin 2
# kodu ("kaynak düştü, önceki dosya korundu") HATA DEĞİL — tazele.ps1 ile
# aynı kural. Hata çıkışı systemd'de birimi "failed" yapar; izleme oradan
# (OnFailure=) ve /_durum'daki veri yaşından görür.
set -u

GRUP="${1:-sik}"
KOD="${BH_KOD_KOK:-/srv/bursahakimiyet/kod}"
PY="${BH_PYTHON:-/srv/bursahakimiyet/venv/bin/python}"
export PYTHONIOENCODING=utf-8

case "$GRUP" in
  sik)     BETIKLER=(piyasa.py doviz.py) ;;          # SIRA önemli: doviz piyasa.json'u okur
  saatlik) BETIKLER=(hava_durumu.py nobetci_eczane.py) ;;
  gunluk)  BETIKLER=(namaz_vakitleri.py puan_durumu.py vizyon_takvimi.py) ;;
  haber)   BETIKLER=(nobetci_eczane.py) ;;
  *) echo "bilinmeyen grup: $GRUP" >&2; exit 64 ;;
esac

hata=0
for b in "${BETIKLER[@]}"; do
  yol="$KOD/canli-veri/$b"
  if [[ ! -f "$yol" ]]; then echo "ATLANDI (yok): $b"; continue; fi
  "$PY" "$yol"
  kod=$?
  if [[ $kod -eq 1 ]]; then hata=1; echo "HATA: $b veri uretemedi"; fi
done

# Günün nöbetçi eczane haberi: liste tazelendikten SONRA (URUN-PLANI §41).
# Komut kendi kapısını taşır: bayat listeyi yayımlamaz, aynı gün ikinci
# kaydı açmaz.
if [[ "$GRUP" == "haber" ]]; then
  ( cd "$KOD/uygulama" && "$PY" manage.py eczane_haberi ) || { hata=1; echo "HATA: eczane haberi yayimlanmadi"; }
fi

exit $hata
