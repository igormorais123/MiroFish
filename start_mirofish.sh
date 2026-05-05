#!/usr/bin/env bash
# Mirofish INTEIA — start idempotente.
# Garante: Docker (Neo4j+Graphiti), Ollama serve + modelos, backend Flask.
# Uso: bash start_mirofish.sh [--local-llm | --omniroute]
set -e

cd "$(dirname "$0")"
ROOT="$(pwd)"
MODE="${1:---auto}"

say() { echo "[mirofish] $*"; }

# 1. Descobrir Python 3.11+ e criar venv
if [ ! -x "backend/.venv/Scripts/python.exe" ] && [ ! -x "backend/.venv/bin/python" ]; then
  say "Criando venv (primeira vez)..."
  PY="$(py -3.11 -c "import sys;print(sys.executable)" 2>/dev/null || \
        py -3.12 -c "import sys;print(sys.executable)" 2>/dev/null || \
        which python3 || which python)"
  [ -z "$PY" ] && { say "Python 3.11+ nao encontrado"; exit 1; }
  "$PY" -m venv backend/.venv
  if [ -x backend/.venv/Scripts/python.exe ]; then
    VPY=backend/.venv/Scripts/python.exe
  else
    VPY=backend/.venv/bin/python
  fi
  "$VPY" -m pip install --upgrade pip -q
  (cd backend && ../backend/.venv/Scripts/python.exe -m pip install -e . -q 2>/dev/null || \
                  ../backend/.venv/bin/python -m pip install -e . -q)
fi

VPY="backend/.venv/Scripts/python.exe"
[ ! -x "$VPY" ] && VPY="backend/.venv/bin/python"

# 2. Docker (Neo4j + Graphiti)
if docker info >/dev/null 2>&1; then
  if ! docker ps --format '{{.Names}}' | grep -q mirofish-graphiti; then
    say "Subindo Neo4j + Graphiti..."
    docker compose -f deploy/docker-compose.vps.yaml --env-file .env up -d neo4j graphiti
  else
    say "Graphiti ja rodando."
  fi
else
  say "WARN: Docker nao disponivel. Graphiti offline -> simulacao sem grafo."
fi

# 3. Ollama (LLM local ou proxy Codex; Graphiti e embeddings dependem dele)
if grep -qE "^LLM_BASE_URL=.*(11434|8004)" .env 2>/dev/null || [ "$MODE" = "--local-llm" ] || [ "$MODE" = "--codex" ]; then
  if ! curl -s -m 2 http://localhost:11434/api/tags >/dev/null 2>&1; then
    OLLAMA_BIN="$HOME/bin/ollama/ollama.exe"
    [ ! -x "$OLLAMA_BIN" ] && OLLAMA_BIN="$(command -v ollama || echo ollama)"
    say "Iniciando Ollama serve (0.0.0.0)..."
    OLLAMA_HOST=0.0.0.0:11434 nohup "$OLLAMA_BIN" serve >/tmp/ollama.log 2>&1 &
    disown || true
    sleep 4
  fi
  # Garante modelos essenciais
  for m in qwen2.5:7b-instruct nomic-embed-text; do
    if ! curl -s http://localhost:11434/api/tags | grep -q "\"$m"; then
      say "Pull $m..."
      "$HOME/bin/ollama/ollama.exe" pull "$m" 2>&1 | tail -1 || ollama pull "$m"
    fi
  done
  # Alias text-embedding-3-small (Graphiti precisa)
  if ! curl -s http://localhost:11434/api/tags | grep -q "text-embedding-3-small"; then
    say "Criando alias text-embedding-3-small -> nomic-embed-text"
    echo "FROM nomic-embed-text" > /tmp/mf_alias.txt
    "$HOME/bin/ollama/ollama.exe" create text-embedding-3-small -f /tmp/mf_alias.txt 2>&1 | tail -1 || true
  fi
fi

# 4. Proxy Codex/OpenAI-compat (necessario quando LLM_BASE_URL aponta para :8004)
if grep -qE "^LLM_BASE_URL=.*8004" .env 2>/dev/null || [ "$MODE" = "--codex" ]; then
  if ! curl -s -m 3 http://localhost:8004/v1/models >/dev/null 2>&1; then
    say "Iniciando proxy Codex em :8004..."
    CODEX_HOME="${CODEX_HOME:-$HOME/.codex-pro}" \
    CODEX_PROXY_PORT="${CODEX_PROXY_PORT:-8004}" \
    CODEX_DEFAULT_MODEL="${CODEX_DEFAULT_MODEL:-gpt-5.5}" \
      nohup python codex_proxy.py > logs_codex_proxy.log 2>&1 &
    disown || true
    sleep 4
  else
    say "Proxy Codex ja rodando."
  fi
fi

# 5. Backend (mata qualquer Python preso na porta 5001)
say "Reciclando backend em :5001..."
if command -v powershell.exe >/dev/null 2>&1; then
  powershell.exe -NoProfile -Command "Get-NetTCPConnection -LocalPort 5001 -State Listen -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess | Sort-Object -Unique | ForEach-Object { Stop-Process -Id \$_ -Force -ErrorAction SilentlyContinue }" 2>/dev/null || true
else
  lsof -ti:5001 | xargs -r kill -9 2>/dev/null || true
fi
sleep 2
find backend/app -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null || true

nohup "$VPY" backend/run.py > logs_backend.log 2>&1 &
disown || true

# 6. Health
for i in 1 2 3 4 5 6 7 8 9 10; do
  if curl -s -m 3 http://localhost:5001/health >/dev/null 2>&1; then
    say "Backend OK: $(curl -s http://localhost:5001/health)"
    break
  fi
  sleep 2
done

say "Pronto. UI: http://localhost:5001/"
