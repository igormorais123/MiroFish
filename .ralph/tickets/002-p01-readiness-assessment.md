---
id: MF-RL-002
status: ready
mode: code
owner: ralphloop
expected_minutes: 30
risk: low
labels: [p0-1, readiness, no-external-calls]
---

# Assessment de prontidao P0.1 sem simulacao longa

## Intent

Preparar a validacao empirica P0.1 do Mirofish sem gastar LLM/Apify, sem rodar simulacao longa e sem tocar `.env`.

## Acceptance

- [ ] Ler `.planning/ROADMAP.md` e `.planning/STATE.md`.
- [ ] Mapear os comandos e artefatos necessarios para P0.1.
- [ ] Identificar quais passos sao read-only, quais persistem artefatos e quais exigem aprovacao humana.
- [ ] Registrar resultado em `runs/`.
- [ ] Preencher `METRICS.json.autoresearch`.

## Required Evidence

Relatorio em `runs/LOOP-*/OUTPUT.md` com:

- checklist P0.1;
- preflight seguro;
- bloqueios humanos;
- proxima acao pequena.

## Scope

Do:

- Assessment documental e local.
- Comandos read-only.
- Preparar decisao.

Do not:

- Rodar simulacao real longa.
- Chamar LLM/Apify.
- Editar `.env`.
- Fazer deploy.

## Context

P0.1 no roadmap pede simulacao nova com LLM ativo e volume suficiente para confirmar gate ate relatorio publicavel. Isso e valioso, mas precisa de decisao humana porque envolve custo, tempo, chaves e possivel estado persistido.

## Blockers

Execucao real de P0.1 depende de Igor aprovar uso de LLM/Apify/tempo de simulacao.

## Handoff

Se o assessment confirmar baixo risco, criar uma tarefa separada para smoke controlado ou pedir aprovacao humana para simulacao real.

## AutoResearch Signal

method_signal: none
candidate_targets: none
