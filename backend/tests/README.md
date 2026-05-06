# Backend tests

Atualizado em: 2026-05-04

Suite pytest cobrindo contratos criticos do MiroFish INTEIA.

## Como rodar

Da raiz do repositorio:

```bash
python -m pytest backend\tests
```

Ou a partir de `backend/`:

```bash
python -m pytest tests
```

Com cobertura:

```bash
python -m pytest backend\tests --cov=backend/app --cov-report=term-missing
```

## Cobertura atual

Validacao mais recente: **70 testes aprovados** em 2026-05-04.

| Area | Arquivos | Notas |
|---|---|---|
| Tradução PT-BR | `test_translation.py` | mapa EN->PT de relações de grafo |
| Qualidade do relatório | `test_report_quality.py` | overlap, gate editorial, auditoria de citações |
| Artefatos de relatório | `test_report_manager_artifacts.py` | `system_gate`, auditoria e status publicável |
| Diversidade/trace | `test_simulation_data_reader.py` | Distinct, entropia e ações OASIS |
| Estado de simulação | `test_simulation_manager.py` | sincronização de runner/status |
| Pulso social | `test_social_bootstrap.py` | plano determinístico de interações iniciais |
| Perfis OASIS | `test_oasis_profile_generator.py` | contrato comportamental dos agentes |
| Retry/paginação/tokens | `test_retry.py`, `test_pagination.py`, `test_token_tracker.py` | utilitários críticos |
| Graph builder | `test_graph_builder.py` | materialização e degradação graciosa |

## Lacunas restantes

- Testes de rotas Flask para `/api/report/generate`, artefatos e `/api/simulation/<id>/quality`.
- Teste end-to-end com simulação nova e LLM ativo.
- Testes de frontend para Step 3 gate e Step 4 cadeia de custódia.
- Cobertura de encerramento de subprocessos no runner.

## Convenções

- Português brasileiro nos nomes de teste quando fizer sentido.
- Fixtures isoladas em `conftest.py`.
- Mocks via `monkeypatch`, `unittest.mock` ou `pytest-mock`.
- Preferir testar contrato observável: status, artefato, métrica e bloqueio.
