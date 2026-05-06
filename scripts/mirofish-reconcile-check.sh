#!/usr/bin/env bash
set -euo pipefail

SITE_URL="${SITE_URL:-https://inteia.com.br/mirofish}"
API_URL="${API_URL:-https://inteia.com.br/mirofish/api/simulation/history?limit=1}"
LOCAL_API="${LOCAL_API:-http://127.0.0.1:5001/api/simulation/history?limit=1}"
LOCAL_DIR="${LOCAL_DIR:-/opt/mirofish}"

printf '== MiroFish reconcile check ==\n'
printf 'site=%s\napi=%s\nlocal_dir=%s\n\n' "$SITE_URL" "$API_URL" "$LOCAL_DIR"

printf '== Git local ==\n'
if [ -d "$LOCAL_DIR" ]; then
  (cd "$LOCAL_DIR" && git status -sb 2>&1 || true)
else
  echo "diretório local ausente: $LOCAL_DIR"
fi

printf '\n== Site público ==\n'
curl -sS -m 20 -D - -o /tmp/mirofish-site-check.html "$SITE_URL" | sed -n '1,25p'
printf 'assets públicos:\n'
grep -o '/mirofish/assets/[^" ]*' /tmp/mirofish-site-check.html | sort -u || true

printf '\n== API pública ==\n'
curl -sS -m 20 -i "$API_URL" | sed -n '1,35p'

printf '\n== API local ==\n'
curl -sS -m 20 -i "$LOCAL_API" | sed -n '1,35p' || true

printf '\n== Docker ==\n'
docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}' | grep -i -E 'miro|NAMES' || true

printf '\n== Portas ==\n'
ss -ltnp | grep -E ':3001|:5001|:4000|:3000' || true
