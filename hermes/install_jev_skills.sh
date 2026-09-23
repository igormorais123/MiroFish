#!/usr/bin/env bash
# Install the JEV skill category into the Hermes Agent skills directory.
# Usage: hermes/install_jev_skills.sh [--dry-run]
# Target: ${HERMES_HOME:-$HOME/.hermes}/skills/jev
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_DIR="${SCRIPT_DIR}/skills/jev"
HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
TARGET_DIR="${HERMES_HOME}/skills/jev"
DRY_RUN=0

usage() {
  echo "usage: $(basename "$0") [--dry-run]"
  echo "Installs the JEV skills into \${HERMES_HOME:-\$HOME/.hermes}/skills/jev"
}

# Any unknown argument aborts before touching the installed skills.
for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=1 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "unknown option: $arg" >&2; usage >&2; exit 2 ;;
  esac
done

EXPECTED=(
  jev-evals
  jev-orquestracao-equipe
  jev-orquestracao-modelos
  jev-triagem
  jev-benchmark
  jev-loop-observa-decide-age
)

for skill in "${EXPECTED[@]}"; do
  file="${SOURCE_DIR}/${skill}/SKILL.md"
  [[ -f "$file" ]] || { echo "missing: $file" >&2; exit 1; }
  head -n 1 "$file" | grep -qx -- '---' || { echo "no frontmatter: $file" >&2; exit 1; }
  grep -q "^name: ${skill}$" "$file" || { echo "name mismatch: $file" >&2; exit 1; }
  grep -q '^description: ' "$file" || { echo "no description: $file" >&2; exit 1; }
done
echo "validated ${#EXPECTED[@]} skills in ${SOURCE_DIR}"

if (( DRY_RUN )); then
  echo "dry-run: would install into ${TARGET_DIR}"
  exit 0
fi

if [[ -d "$TARGET_DIR" ]]; then
  backup="${HERMES_HOME}/skills/.backup-jev-$(date -u +%Y%m%dT%H%M%SZ)"
  cp -a "$TARGET_DIR" "$backup"
  echo "backup: ${backup}"
  rm -rf "$TARGET_DIR"
fi

mkdir -p "$(dirname "$TARGET_DIR")"
cp -a "$SOURCE_DIR" "$TARGET_DIR"
chmod +x "$TARGET_DIR"/*/scripts/*.py 2>/dev/null || true
echo "installed into ${TARGET_DIR}:"
find "$TARGET_DIR" -name SKILL.md | sort
