# Aprendizados — Fase 03 (Vox Academic Hardening)

**Data:** 2026-05-19
**Branch:** `codex/mapa-ativos-ia`
**Commits:** `3f45e59` → `6c0e111` (7 commits atômicos)

## Decisões travadas

1. **Posicionamento "exploratório auditado"** — Igor confirmou explicitamente. C0–C2 permitidos; C3–C4 bloqueados sem painel humano. Mantém compatibilidade com restrição "zero coleta humana nova".
2. **8 das 10 recomendações acadêmicas implementadas.** Cortadas: E3 (calibração humana, fere zero-coleta) e E9 (IPF/SIAPE via LAI, processo de meses).
3. **Constantes universais travadas em `vox_science/artifacts.py`** (single source of truth):
   - `DPD_BLOCKER_THRESHOLD = 0.15`
   - `LATENT_CONSTRUCT_CEILING = 0.50`
   - `CORRELATION_ALERT_THRESHOLD = 0.65`
   - `PROMPT_FIELD_TOKEN_LIMIT = 200`

## O que funcionou bem

- **Fluxo `/gsd-do` → `add-phase` → `spec` → `plan` → `execute` → `validate`** em ondas paraleliveis com commits atômicos preservou clareza. 7 commits, cada um corresponde a uma onda do PLAN.md.
- **Schema versionado (`schema: ...v1` → `v2`) com flag `legacy_schema=true`** preservou retro-compatibilidade do `prompt_registry`. Nenhum teste antigo quebrou.
- **Módulo `metrics.py` puro-python** (sem scipy/numpy) evitou risco operacional na VPS. Wasserstein, KL, MAE, DPD funcionando com 11/11 testes verde.
- **Helena/Efesto operando autônomos via modo `--auto`** no SPEC poupou Igor de 15+ perguntas técnicas. Coerente com CLAUDE.md ("não perguntar decisão técnica a leigo").
- **`data-testid` em pills da UI** permitiu validação Playwright determinística sem depender de texto traduzido.

## O que poderia ter rodado pior

- **Hook `pt_accent_guard`** bloqueou 4–5 edits por falta de acentos. Aprendizado: sempre escrever PT-BR completo desde o primeiro draft.
- **`READ-BEFORE-EDIT REMINDER`** dispara após cada edit mesmo quando a edição é bem-sucedida — ruído visual, mas não bloqueante.
- **Relatório seed `report_c7762071893d`** não tem `mission_bundle`, gera 409 no Step4. Não é regressão da Fase 03 mas polui console em ambiente de teste. Documentado em `PHASE03_E2E_REPORT.md`.

## Para a próxima fase (referência futura)

- Se for ativar **calibração com painel humano**: roadmap pronto em `docs/superpowers/plans/2026-05-19-mirofish-roadmap-coleta-humana-futura.md`. Infraestrutura técnica do `prompt_registry` (campo `biographical_context`) já aceita backstory direto.
- Se for adicionar **3º LLM replicator**: `model_run_registry.json` já suporta lista. Basta passar mais entries em `replicators[]`.
- Se for **conectar OSF API real**: campo `osf_preregistration_url` em `prompt_registry.json` já existe (placeholder `None`).
- Se for **endurecer mais o gate**: pode-se elevar `DPD_BLOCKER_THRESHOLD` de 0.15 para 0.10 (paridade mais rígida); está em constante única.

## Métricas finais (Fase 03)

| Métrica | Antes | Depois |
|---|---|---|
| Testes backend | 322 | **347** (+25) |
| Linhas em `vox_science/` | 599 (artifacts + __init__) | **968** (+369 com metrics.py) |
| Métricas no painel Step4 UI | 6 | **12** |
| Constantes auditáveis travadas | 0 | **5** |
| Schemas Vox Science v2 | 0 | **3** (prompt, model_run, claim_policy, fidelity) |
| Roadmap calibração humana | inexistente | documento de 200+ linhas |

## Posicionamento epistêmico declarado

