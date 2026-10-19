#!/usr/bin/env bash
# Cloudflare IP aralıklarını yeniler: /etc/nginx/snippets/bh-cloudflare-ip.conf
# Ayda bir elle ya da bir timer'la. Değişiklik yoksa nginx'e dokunmaz.
set -euo pipefail
HEDEF=/etc/nginx/snippets/bh-cloudflare-ip.conf
GECICI=$(mktemp)
{
  echo "# Uretildi: $(date -Is) — cloudflare-ip-guncelle.sh"
  for a in $(curl -fsS -m 20 https://www.cloudflare.com/ips-v4) \
           $(curl -fsS -m 20 https://www.cloudflare.com/ips-v6); do
    echo "set_real_ip_from $a;"
  done
  echo "real_ip_header CF-Connecting-IP;"
} > "$GECICI"
# En az 10 aralık yoksa indirme bozuktur; eskisini koru.
[[ $(grep -c set_real_ip_from "$GECICI") -ge 10 ]] || { echo "liste bozuk"; exit 1; }
if ! diff -q <(grep -v '^#' "$GECICI") <(grep -v '^#' "$HEDEF" 2>/dev/null) >/dev/null; then
  install -m 0644 "$GECICI" "$HEDEF"
  nginx -t && systemctl reload nginx
fi
rm -f "$GECICI"
