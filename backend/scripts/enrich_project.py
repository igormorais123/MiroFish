"""
CLI: enriquece materiais-base de um projeto Mirofish com dados Apify.

Anexa ao texto extraido do projeto:
  - SERPs Google para fatos do caso
  - Perfis Instagram dos atores citados

Uso:
    python backend/scripts/enrich_project.py \
        --project-id abc123 \
        --query "reforma tributaria PEC 45" \
        --query "Neto 2026 Bahia" \
        --actor acmneto \
        --actor brunoreisba

Rodar ANTES de /api/simulation/prepare. Se o projeto nao tiver texto extraido
ainda (upload de arquivo nao processado), o script aborta.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.models.project import ProjectManager  # noqa: E402
from app.services.apify_enricher import ApifyEnricher  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="Enriquece projeto Mirofish via Apify")
    ap.add_argument("--project-id", required=True)
    ap.add_argument("--query", action="append", default=[], help="query Google (repetivel)")
    ap.add_argument("--actor", action="append", default=[], help="handle Instagram (repetivel)")
    ap.add_argument("--results-per-query", type=int, default=8)
    ap.add_argument("--dry-run", action="store_true", help="mostra bloco mas nao salva")
    args = ap.parse_args()

    if not args.query and not args.actor:
        print("ERRO: informe ao menos --query ou --actor", file=sys.stderr)
        return 2

    existing = ProjectManager.get_extracted_text(args.project_id)
    if existing is None:
        print(f"ERRO: projeto {args.project_id} sem texto extraido", file=sys.stderr)
        return 1

    enricher = ApifyEnricher()
    usage_before = enricher.usage()
    print(f"Apify uso antes: US$ {usage_before['usd_used']:.4f} ({usage_before['pct']}%)")

    block = enricher.build_enrichment_block(
        queries=args.query,
        actors_instagram=args.actor,
        results_per_query=args.results_per_query,
    )

    if not block:
        print("Nada coletado. Nenhuma alteracao.")
        return 0

    print("\n===== BLOCO DE ENRIQUECIMENTO =====")
    print(block)
    print("===== FIM =====\n")

    usage_after = enricher.usage()
    delta = usage_after["usd_used"] - usage_before["usd_used"]
    print(f"Apify uso depois: US$ {usage_after['usd_used']:.4f} (+US$ {delta:.4f})")

    if args.dry_run:
        print("dry-run: nada foi salvo.")
        return 0

    new_text = existing.rstrip() + "\n\n" + block + "\n"
    ProjectManager.save_extracted_text(args.project_id, new_text)
    print(f"OK: {len(block)} chars anexados ao projeto {args.project_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
