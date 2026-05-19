# PLAN — Fase 03: Vox Academic Hardening

**Versão:** 1.0
**Data:** 2026-05-19
**Modo:** `--auto`
**Origem:** `03-SPEC.md` (8 entregas falsificáveis)
**Alvo principal:** `backend/app/services/vox_science/artifacts.py` (577 linhas, 11 builders) + `frontend/src/components/Step4Report.vue` (7291 linhas).

## Estratégia de execução

**Ondas paralelas (commits atômicos):**

### Onda 1 — Backend artefatos (sem UI)

| # | Tarefa | Arquivo | LoC est. | Testes |
|---|---|---|---|---|
| T1 | Helper `_metric_distance` (Wasserstein + KL puro-python; fallback `scipy`) | `vox_science/metrics.py` (novo) | +120 | `test_vox_metrics.py` (novo, 6 testes) |
| T2 | R1 — estender `_fidelity_report` com `wasserstein/kl/mae/dpd/intra_group_variance/temporal_stability` | `vox_science/artifacts.py` | +80 | `test_vox_science_artifacts.py` (+3 testes) |
| T3 | R2 — estender `_science_gate` com blocker DPD>0.15 | `vox_science/artifacts.py` | +30 | +2 testes |
| T4 | R4 — `prompt_hash` SHA-256 + `git_commit_sha` em `_prompt_registry` | `vox_science/artifacts.py` | +25 | +2 testes |
| T5 | R5 — `latent_construct_ceiling=0.50` + `correlation_alert_threshold=0.65` + `blocked_claims` em `_claim_policy_audit` | `vox_science/artifacts.py` | +40 | +3 testes |
| T6 | R6 — `replicators[]` + `inter_model_divergence` opcional em `_model_run_registry` | `vox_science/artifacts.py` | +50 | +2 testes |
| T7 | R7 — schema 3-campos em `_prompt_registry` + back-compat `legacy=true` | `vox_science/artifacts.py` | +60 | +3 testes |
| T8 | R8 — `blind_test` em `_fidelity_report` com validação literal | `vox_science/artifacts.py` | +45 | +3 testes |

Commit pattern: `feat(vox-science): T{N} — {curta descrição}`.

### Onda 2 — Disclaimer + Executive Package

| # | Tarefa | Arquivo | LoC est. | Testes |
|---|---|---|---|---|
| T9 | R3a — Constante `LGPD_DISCLAIMER` + injetar em `executive_package.py` sumário | `backend/app/services/executive_package.py` | +20 | snapshot test |
| T10 | R3b — Injetar disclaimer em rodapé MD/HTML/PDF em `report_exporter.py` | `backend/app/services/report_exporter.py` | +30 | +3 testes |

### Onda 3 — Frontend UI

| # | Tarefa | Arquivo | LoC est. | Testes |
|---|---|---|---|---|
| T11 | R3c — Banner LGPD persistente acima do conteúdo no Step4Report | `frontend/src/components/Step4Report.vue` | +25 | manual |
| T12 | R1+R2 UI — cards DPD/Wasserstein/KL no painel science | `frontend/src/components/Step4Report.vue` | +80 | manual |
| T13 | R5 UI — label "Teto epistêmico ≤0.50" no claim level card | `frontend/src/components/Step4Report.vue` | +15 | manual |
| T14 | R6 UI — chip "Replicado em N modelos" se replicators>0 | `frontend/src/components/Step4Report.vue` | +20 | manual |

### Onda 4 — Roadmap doc + atualização docs

| # | Tarefa | Arquivo | LoC est. |
|---|---|---|---|
| T15 | R10 — escrever `docs/superpowers/plans/2026-05-19-mirofish-roadmap-coleta-humana-futura.md` | novo | 200 |
| T16 | Atualizar `docs/MAPA_SISTEMA.md` com novos campos | edit | +30 |
| T17 | Atualizar `README.md` com "exploratório auditado" + link para SPEC | edit | +10 |

### Onda 5 — Validação

| # | Tarefa | Comando |
|---|---|---|
| T18 | Rodar suite pytest | `cd backend && python -m pytest tests -q` |
| T19 | Rodar build frontend | `cd frontend && npm run build` |
| T20 | Subir backend local | `cd backend && python -m flask --app app:create_app run --port 5001` (background) |
| T21 | Subir frontend local | `cd frontend && npx vite --host --port 5173` (background) |
| T22 | Smoke test API: gerar 1 relatório, validar 11 artefatos + campos R1–R8 | curl |
| T23 | Playwright E2E: Step1→Step4, captura console, assert UI elements | mcp__playwright__ tools |

### Onda 6 — Memórias e fechamento

| # | Tarefa | Arquivo |
|---|---|---|
| T24 | Criar `.planning/LEARNINGS_VOX_ACADEMIC_HARDENING.md` | novo |
| T25 | Atualizar memória global `MEMORY.md` (decisão F:7+: posicionamento exploratório auditado, teto 0.50, blocker DPD) | edit |
| T26 | Atualizar `.memoria/CONTEXTO_ATIVO.md` (se existir) | edit |
| T27 | Atualizar `.planning/STATE.md` com pendências resolvidas | edit |
| T28 | Criar PR via `gh pr create` base=main head=codex/mapa-ativos-ia | bash |

## Cronograma estimado

- Onda 1 (backend metrics+artifacts): **3–4 h**
- Onda 2 (disclaimer): **30 min**
- Onda 3 (UI): **1–2 h**
- Onda 4 (docs): **45 min**
- Onda 5 (validação E2E): **1 h**
- Onda 6 (memórias + PR): **30 min**

**Total:** ~7–9 horas de trabalho cumulativo. Recomendado dividir em ≥2 sessões.

## Pontos de checkpoint (commitar trabalho a cada)

1. Após Onda 1 (vox_science endurecido + testes).
2. Após Onda 2 (disclaimer).
3. Após Onda 3 (UI).
4. Após Onda 4 (docs).
5. Após Onda 5 com TUDO verde (caso contrário, voltar e corrigir).
6. Final: PR aberto.

## Dependências externas

- `scipy` opcional (fallback puro-Python pronto).
- `subprocess` para `git rev-parse HEAD` (R4) — usar com try/except, fallback null.
- LLM secundários (R6) **opt-in**: testes usam mocks, produção decide via env var `VOX_REPLICATORS`.

## Riscos identificados

| Risco | Mitigação |
|---|---|
| Hook pt_accent_guard bloqueia edits | Sempre acentuar PT-BR; usar `--fix` em arquivos legados |
| Step4Report.vue tem 7291 linhas — pode haver merge conflict | Branch dedicada já tem mods; editar com cuidado seções específicas |
| E2E Playwright depende de backend + frontend rodando | Subir os dois em background antes |
| Smoke test pode falhar se LLM_API_KEY ausente | Mockar via env stub se ausente |

## Critério de "fase pronta"

Marcar fase 03 = `done` somente quando todos 7 critérios do SPEC §5 verdes. Antes disso, status = `in_progress`.

## Próximo comando

`/gsd-execute-phase 03` (ou execução manual onda-a-onda).
