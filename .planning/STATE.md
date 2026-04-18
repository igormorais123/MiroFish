# STATE — MiroFish INTEIA

## Current
- **Milestone:** v1.2 — Motor Confiável
- **Phase:** 1 (Diagnóstico do Pipeline que Trava) — pending
- **Status:** pronto para `/gsd-plan-phase 01`

## Decisions
- 2026-04-18: Diagnóstico real de Igor sobrescreve plano antigo — problemas reais são pipeline incompleto, output superficial que repete upload, lentidão, defasagem vs upstream
- 2026-04-18: Phase 1 v1.2 é diagnóstico puro (sem fix) — evita ciclo de hipótese-sem-evidência
- 2026-04-18: Upstream `666ghj/MiroFish` adicionado ao roadmap (Phase 5) — fork estava fetch-only, sem sync
- 2026-04-18: `.playwright-mcp/` movido para `.gitignore`, 217 arquivos removidos do index
- 2026-04-09: Modelos configurados para qualidade máxima (Sonnet 4.6 report, Opus 4.6 Helena)
- 2026-04-09: BestFREE mantido para simulação/grafos (volume alto, custo proibitivo)

## Completed
- v1.0: Sistema funcional — upload, GraphRAG, simulação OASIS, relatório ReACT
- v1.1 Phase 1: Toolbar (print, share WhatsApp/Email/Link, custos estimados)
- v1.1 Phase 2: Graphiti graph_id corrigido (propagação + prevenção)
- v1.1 Phase 3: API de custos real (token tracking backend)

## Pending (v1.2)
- Phase 1: Diagnóstico do Pipeline que Trava (P0)
- Phase 2: Corrigir o Ponto de Parada Dominante (P0)
- Phase 3: Qualidade do Relatório — Não Repetir o Upload (P0)
- Phase 4: Performance <30min (P1)
- Phase 5: Sync com MiroFish Upstream (P1)
- Phase 6: Português Total (P1, parcial)
- Phase 7: Segurança Básica (P2)
- Phase 8: Persistência + CI (P2)
- Phase 9: Poder Preditivo (P2)
- Phase 10: Testes Críticos (P3)
