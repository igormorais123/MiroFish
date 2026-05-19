# Phase 03 — Vox Academic Hardening

**Criada:** 2026-05-19
**Milestone:** v1.3 — Consultoria por Simulação Auditável
**Slug:** `vox-academic-hardening`
**Status:** planejada (aguardando `/gsd-spec-phase`)

## Goal

Implementar 8 recomendações acadêmicas derivadas da revisão de literatura 2024–2026 sobre limitações metodológicas de biografias sintéticas (918 arquivos no doutorado de Igor sobre agentes sintéticos para servidores públicos). Preservar o posicionamento "exploratório auditado" do Mirofish INTEIA. Compatível com a restrição operacional "zero coleta humana nova".

## Posicionamento travado (decisão Igor 2026-05-19)

**Exploratório auditado** — Mirofish gera "mapas de sinais" e "simulações exploratórias" com auditoria rigorosa. Níveis C0–C2 permitidos. C3–C4 bloqueados sem painel humano. Risco residual estimado: ~15% (contra ~70% no cenário confirmatório).

## Entregas (8)

| Código | Entrega | Onde |
|--------|---------|------|
| E1 | Dashboard multi-métrica: Wasserstein, KL, MAE, DPD, variância intra-grupo, estabilidade temporal; blocker DPD>15% | `vox_science/artifacts.py` (fidelity_report + harness_science_gate), `Step4Report.vue` |
| E2 | Disclaimer legal LGPD art. 7º IV em todo relatório | `executive_package.py`, `report_exporter.py`, `Step4Report.vue` |
| E4 | Pré-registro versionado: prompt_hash SHA-256 + git_commit_sha | `vox_science/artifacts.py` (prompt_registry) |
| E5 | Teto epistêmico latent_construct_ceiling=0.50; bloqueio >0.65 sem evidência | `vox_science/artifacts.py` (claim_policy_audit), UI |
| E6 | Replicabilidade ≥2 LLMs com inter_model_divergence | `vox_science/artifacts.py` (model_run_registry) |
| E7 | Prompt biográfico estruturado curto (3 campos, 200 tokens cada) | `vox_science/artifacts.py` (prompt_registry schema) |
| E8 | Teste-cego: campo blind_test em fidelity_report + validação no builder | `vox_science/artifacts.py` |
| E10 | Roadmap doc para coleta humana Tier S contingente | `docs/superpowers/plans/2026-05-19-mirofish-roadmap-coleta-humana-futura.md` |

## Fora de escopo

- E3 calibração com painel humano (fere "zero coleta humana nova").
- E9 IPF/SIAPE via LAI (processo de meses; vira follow-up dentro de E10).
- Coleta humana real, fine-tuning, integração OSF API real.

## Critérios de pronto (verificação obrigatória)

1. `python -m pytest backend/tests -q` verde (novos testes para cada artefato modificado).
2. `cd frontend && npm run build` verde sem warning.
3. Smoke test backend: `POST /api/report/...` gera relatório com 11 artefatos + campos novos.
4. Playwright E2E: front local em `http://localhost:5173`; navegar Step1→Step4; console limpo (zero error/warning); UI exibe: science gate, claim level, disclaimer LGPD, métricas Wasserstein/KL/DPD, ceiling 0.50.
5. `docs/MAPA_SISTEMA.md` atualizado com novos campos e fluxos.
6. `README.md` declara posicionamento "exploratório auditado".
7. Memórias atualizadas: `MEMORY.md` global, `CONTEXTO_ATIVO.md`, `.planning/STATE.md`, `.planning/LEARNINGS_VOX_ACADEMIC_HARDENING.md`.

## Dependências / pré-requisitos

- Branch `codex/mapa-ativos-ia` tem 13 arquivos modificados não commitados (red-team, harness interno, pacote decisão). **Decidir antes de iniciar:** commit, stash ou continuar em cima.
- `scipy` disponível para Wasserstein/KL (alternativa: implementação pura).
- Acesso a chaves LLM secundárias (Claude + Llama via OmniRoute) para E6.

## Referências acadêmicas-chave (rastreabilidade)

- Park et al. 2024 (Tier S backstory) — 85% acurácia.
- Kambhatla et al. 2025 (calibração supervisionada) — +16,3% alinhamento.
- Bisbee et al. 2024 (Political Analysis 32(4)) — instabilidade temporal.
- Boelaert et al. 2025 (SMR 54(3)) — machine bias sistemático.
- Tjuatja et al. 2024 (TACL 12) — vieses humanos não reproduzidos.
- Hu & Collier 2024 (ACL) — teto ~40–50% para construtos latentes.
- Wang et al. 2024 (Nature MI) + Cheng et al. 2023 (CoMPosT) — flattening.
- Anthis et al. 2025 — pré-registro de prompts.
- Turpin et al. 2023 (Nature) — sycophancy/desejabilidade.
- NIST AI 600-1 + ICC/ESOMAR 2025 — agentes apenas exploratórios.

## Próximos passos

1. `/gsd-spec-phase 03` — produzir SPEC.md falsificável.
2. `/gsd-discuss-phase 03 --auto` — Helena/Efesto resolvem áreas cinzas.
3. `/gsd-plan-phase 03` — gerar PLAN.md.
4. `/gsd-execute-phase 03` — build atômico.
5. `/gsd-validate-phase 03` — verificação goal-backward.
6. Playwright E2E.
7. Docs + memórias.
