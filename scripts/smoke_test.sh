#!/bin/bash
# Smoke test para MiroFish-INTEIA em producao
# Uso: ./smoke_test.sh [host]
# Default host: http://72.62.108.24:4000
#
# Valida os fixes das Phases 2, 6, 7 e 8 sem rodar simulacao completa.
# Saida: exit 0 tudo OK, exit 1 pelo menos um teste falhou.

set -u
HOST="${1:-http://72.62.108.24:4000}"
PASS=0
FAIL=0

_test() {
    local label="$1"
    local actual="$2"
    local expected="$3"
    if [[ "$actual" == "$expected" ]]; then
        echo "  ✓ $label"
        PASS=$((PASS + 1))
    else
        echo "  ✗ $label (got: $actual, expected: $expected)"
        FAIL=$((FAIL + 1))
    fi
}

echo "== Smoke test $HOST =="

# Frontend responde
code=$(curl -sS -o /dev/null -w '%{http_code}' "$HOST/")
_test "frontend responde" "$code" "200"

# API lista simulacoes
body=$(curl -sS "$HOST/api/simulation/list")
success=$(echo "$body" | grep -oE '"success":\s*true' | head -1 | tr -d ' ')
_test "API /simulation/list retorna success" "$success" '"success":true'

# Phase 7: health publico sem token
body=$(curl -sS "$HOST/api/internal/v1/health/public")
status=$(echo "$body" | grep -oE '"status":\s*"[^"]*"' | head -1 | tr -d ' ')
_test "Phase 7: /health/public retorna {up}" "$status" '"status":"up"'

# Phase 7: health publico NAO expoe config interna
llm_base=$(echo "$body" | grep -c "llm_base_url")
_test "Phase 7: /health/public nao vaza llm_base_url" "$llm_base" "0"

# Phase 7: health privado exige token
code=$(curl -sS -o /dev/null -w '%{http_code}' "$HOST/api/internal/v1/health")
_test "Phase 7: /health privado bloqueia sem token" "$code" "401"

# Phase 7: limit absurdo nao causa crash (fica clampado)
code=$(curl -sS -o /dev/null -w '%{http_code}' "$HOST/api/simulation/list?limit=9999999")
_test "Phase 7: limit=9999999 nao crasha" "$code" "200"

echo
echo "== Resultado: $PASS passed, $FAIL failed =="
[[ $FAIL -eq 0 ]] && exit 0 || exit 1
