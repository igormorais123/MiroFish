# Roadmap — MiroFish INTEIA

Atualizado em: 2026-05-04

## Milestone v1.3 — Consultoria por Simulacao Auditavel

Status: **P0 implementado localmente**.

### P0 — Garantia de entrega dentro do sistema

**Status:** concluido.

Entregue:

- Gate estrutural de relatorio em `report_system_gate.py`.
- Auditoria de citacoes em `report_quality.py`.
- Artefatos `system_gate.json`, `evidence_manifest.json` e `evidence_audit.json`.
- API de artefatos do relatorio.
- API de qualidade da simulacao.
- Sincronizacao entre runner e estado persistido da simulacao.
- Metricas de diversidade e trace OASIS.
- Bloqueio visual do relatorio na etapa 3.
- Cadeia de custodia visual na etapa 4.
- Status `publishable`, `legacy_unverified`, `blocked_by_system_gate` e `blocked_by_evidence_audit`.
- Pulso social inicial configuravel no OASIS.
- Governanca cliente vs demo/smoke com status `diagnostic_only`.
- Auditoria numerica para percentuais, probabilidades e contagens.

UAT local:

- Backend: 76 testes aprovados.
- Frontend: build aprovado.
- Backend/frontend locais responderam 200.

### P0.1 — Validacao empirica com nova simulacao

**Status:** proximo.

Objetivo: rodar uma simulacao nova com LLM ativo e volume suficiente para confirmar se as interacoes sociais, a diversidade semantica e a auditoria sustentam relatorio publicavel.

Criterio de aceite:

- Simulacao `completed`.
- `interactive_actions_total > 0`.
- `behavioral_entropy_norm` e `distinct_2` acima dos defaults.
- Report gerado como `publishable`.
- Step 4 exibe cadeia de custodia sem alertas criticos.

### P0.2 — Modo cliente vs smoke/demo

**Status:** concluido.

Objetivo: impedir que testes curtos ou tecnicos sejam confundidos com entrega consultiva.

Entregue:

- Campo `delivery_governance` no contrato de simulacao e `delivery_mode` nas APIs de gate/relatorio.
- Defaults relaxaveis para demo, defaults rigidos para cliente.
- Relatorio demo rotulado como `diagnostic_only`.

### P0.3 — Auditoria numerica

**Status:** concluido.

Objetivo: percentuais, probabilidades e contagens precisam vir de metrica ou ser rotulados como inferencia calibrada.

Entregue:

- Extrator de numeros, percentuais e contagens do relatorio.
- Verificacao literal no corpus de evidencias.
- Aceite de numeros rotulados como inferencia/simulacao/calibracao.
- Bloqueio de numeros sem suporte em modo cliente via `REPORT_FAIL_ON_UNSUPPORTED_NUMBERS`.

## P1 — Consolidar conhecimento INTEIA

1. Adaptador de perfis Helena/Colmeia para OASIS.
2. Presets por dominio: eleitoral, juridico, mercado, educacao, infraestrutura.
3. Biblioteca de hipoteses testaveis por dominio.
4. Memoria acumulada: relatorio aprovado vira insumo versionado da proxima rodada.
5. Exportacao executiva com anexo tecnico de evidencias.

## P3 — Vox Academic Hardening (Fase 03)

**Status:** planejada (2026-05-19).

**Goal:** Implementar 7 recomendações acadêmicas (revisão 2024-2026 sobre limitações metodológicas de biografias sintéticas) endurecendo o Vox Science Harness do Mirofish INTEIA. Compatível com restrição "zero coleta humana nova".

**Depends on:** P0 (gate estrutural), P0.1 (validação empírica), Vox Science Harness v2 (artefatos P0).

**Plans:**

- E1. Dashboard multi-métrica: Wasserstein, KL, MAE, DPD (blocker DPD>15%), variância intra-grupo, estabilidade temporal — em `fidelity_report.json` + UI Step4Report.
- E4. Pré-registro versionado: `prompt_hash` SHA-256 + `git_commit_sha` em `prompt_registry.json`.
- E5. Teto epistêmico: `latent_construct_ceiling=0.50` em `claim_policy_audit.json`; bloqueia claim com correlação >0.65 sem evidência adicional.
- E6. Replicabilidade ≥2 LLMs em `model_run_registry.json` com `inter_model_divergence`.
- E7. Prompt biográfico estruturado curto: `{biographical_context, role_context, scenario_context}` limite 200 tokens/campo.
- E8. Teste-cego: campo `blind_test` em `fidelity_report.json` valida variável-alvo não aparece literal no prompt.
- E10. Roadmap doc para coleta humana futura (Tier S contingente).

**Fora de escopo:** calibração com painel humano (fere zero-coleta), IPF/SIAPE via LAI (processo de meses), fine-tuning de LLM.

**Critérios de pronto:** pytest verde, `npm run build` verde, smoke API gera relatório com 11 artefatos + campos novos, Playwright E2E sem erro de console, `docs/MAPA_SISTEMA.md` e `README.md` atualizados, memórias registradas.

## P2 — Avaliação de ROI e previsão calibrada

1. Benchmark contra metodo tradicional: tempo, custo, retrabalho, contradicao e utilidade decisoria.
2. Benchmark retrospectivo com casos reais.
3. Metricas de convergencia e parada automatica.
4. Painel de prontidao pre-relatorio.

## Marcos anteriores

- **v1.1 — Relatorio Premium + Qualidade:** concluido.
- **v1.2 — Motor Confiavel:** principais correcoes de pipeline, PT-BR, seguranca basica, persistencia e QC inicial concluidas.

Detalhes historicos permanecem em `.planning/SPRINT_2026-04.md`, `.planning/PLANO_CORRECAO_MIROFISH.md` e `_archive/sprints/`.
