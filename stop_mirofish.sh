#!/usr/bin/env bash
# Mirofish INTEIA — stop idempotente. Mata backend, Ollama opcional, deixa Docker de pe.
set -e
cd "$(dirname "$0")"

echo "[mirofish] Matando backend :5001..."
if command -v powershell.exe >/dev/null 2>&1; then
  powershell.exe -NoProfile -Command "Get-NetTCPConnection -LocalPort 5001 -State Listen -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess | Sort-Object -Unique | ForEach-Object { Stop-Process -Id \$_ -Force -ErrorAction SilentlyContinue }" 2>/dev/null || true
else
  lsof -ti:5001 | xargs -r kill -9 2>/dev/null || true
fi

if [ "$1" = "--all" ]; then
  echo "[mirofish] Parando Neo4j + Graphiti..."
  docker compose -f deploy/docker-compose.vps.yaml --env-file .env stop graphiti neo4j 2>/dev/null || true
  echo "[mirofish] Parando Ollama..."
  if command -v powershell.exe >/dev/null 2>&1; then
    powershell.exe -NoProfile -Command "Get-NetTCPConnection -LocalPort 11434 -State Listen -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess | Sort-Object -Unique | ForEach-Object { Stop-Process -Id \$_ -Force -ErrorAction SilentlyContinue }" 2>/dev/null || true
  else
    lsof -ti:11434 | xargs -r kill -9 2>/dev/null || true
  fi
fi

echo "[mirofish] Stopped."
