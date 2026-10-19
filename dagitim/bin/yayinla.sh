#!/usr/bin/env bash
# Kod sürümü yayınlama / geri alma — Linux üretimi. YALNIZ DOSYA.
#
#   sudo -u bh dagitim/bin/yayinla.sh <git-etiketi-ya-da-commit>
#
# Aynı betik geri dönüştür: önceki etiketi verirsiniz. Migration içeren bir
# sürümü geri almak kodu geri almakla bitmez — KURULUM.md §8 "kod geri
# dönüşü"ne bakın (önce migrate geri, sonra kod).
#
# Adımlar: kod → bağımlılık → denetim → migrate → statik → yeniden yükle →
# duman testi. Herhangi biri başarısızsa betik durur. Reload'a kadar çalışan
# süreç eski kodla hizmet verir (Python modülleri bellekte); reload yalnız
# önceki adımların hepsi geçtiyse yapılır. Duman testi reload'dan sonra yeni
# kodu doğrular; düşerse son satırdaki komutla önceki sürüme dönülür.
set -euo pipefail

HEDEF="${1:?kullanim: yayinla.sh <etiket|commit>}"
KOD=/srv/bursahakimiyet/kod
VENV=/srv/bursahakimiyet/venv
ORTAM=/etc/bursahakimiyet/ortam
ALAN="${BH_ANA_ALAN:-www.bursahakimiyet.com.tr}"

set -a; . "$ORTAM"; set +a

cd "$KOD"
ONCEKI=$(git rev-parse HEAD)
git fetch --tags --quiet origin
git checkout --quiet --detach "$HEDEF"
YENI=$(git rev-parse HEAD)
echo "kod: $ONCEKI -> $YENI"

"$VENV/bin/pip" install --quiet -r requirements.txt

cd "$KOD/uygulama"
export BH_SURUM="$YENI"
"$VENV/bin/python" manage.py check --deploy --fail-level ERROR
# Bekleyen migration'ı göster; uygula. (Göç planı her sürümün notunda.)
"$VENV/bin/python" manage.py migrate --plan | tail -n 20
"$VENV/bin/python" manage.py migrate --noinput
# --clear YOK: eski özetli dosyalar kalır; mikro önbellekteki ve okurun
# tarayıcısındaki eski HTML eski CSS'i istemeye devam edebilir, geri dönüşte
# de eski adlar hazırdır.
"$VENV/bin/python" manage.py collectstatic --noinput --verbosity 0

sed -i "s/^BH_SURUM=.*/BH_SURUM=$YENI/" "$ORTAM" 2>/dev/null || true
sudo systemctl reload bursahakimiyet

# Duman testi: sağlık ucu (makinenin içinden, Host başlığıyla) + anasayfa.
sleep 3
curl -fsS -m 10 -H "Host: $ALAN" http://127.0.0.1/_durum >/dev/null
curl -fsS -m 30 -o /dev/null -H "Host: $ALAN" -H "X-Forwarded-Proto: https" \
  --unix-socket /run/bursahakimiyet/gunicorn.sock http://localhost/
echo "yayinda: $YENI (geri almak icin: yayinla.sh $ONCEKI)"
