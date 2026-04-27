# Backend tests

Suite pytest cobrindo as utilities críticas do MiroFish INTEIA.

## Como rodar

```bash
cd backend
PYTHONPATH=. python -m pytest tests/ -v
```

Ou com cobertura:

```bash
PYTHONPATH=. python -m pytest tests/ --cov=app --cov-report=term-missing
```

## Cobertura atual (2026-04-27)

| Módulo | Testes | Notas |
|---|---|---|
| `utils/translation.py` | 12 | mapa EN→PT de relações de grafo |
| `utils/report_quality.py` | 13 | jaccard, overlap, gate editorial (Phase 3) |
| `utils/retry.py` | 8 | decorator + RetryableAPIClient (Phase 10) |
| `utils/pagination.py` | 9 | clamps, defaults, bounds (Phase 10) |
| `utils/token_tracker.py` | 11 | singleton, sessions, custos (Phase 10) |
| **TOTAL** | **53** | passa em ~0.7s |

## Roadmap de cobertura

Pendente Phase 10 (target 60% em `services/`):
- `services/simulation_manager.py` — requer mocks de Zep/Graphiti
- `services/report_agent.py` — testar `_parse_tool_calls`, `_fix_truncated_json`
- `services/oasis_profile_generator.py` — testar geração de perfis (mock LLM)
- `services/apify_enricher.py` — mock de subprocess

## Convenções

- Português brasileiro nos nomes de teste e docstrings
- Sem emojis (CLAUDE.md global)
- Fixtures pytest isoladas (`autouse=True` quando há estado global)
- Mocks via `unittest.mock` ou `pytest-mock` (já em deps)
