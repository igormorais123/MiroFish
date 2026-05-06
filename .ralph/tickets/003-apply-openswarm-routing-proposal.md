---
id: MF-RL-003
status: ready
mode: autoresearch
owner: ralphloop
expected_minutes: 30
risk: low
labels: [autoresearch, openswarm, method]
---

# Aplicar proposta OpenSwarm de roteamento especialista

## Intent

Incorporar ao metodo Ralph Loop AutoResearch a melhoria pequena proposta no estudo OpenSwarm: lanes especialistas e context packet para tarefas de pesquisa/metodo.

## Acceptance

- [ ] Revisar `.autoresearch/experiments/openswarm-specialist-routing-v1/PATCH_PROPOSTO.diff`.
- [ ] Aplicar o patch somente se ele preservar uma unidade por ciclo.
- [ ] Rodar `git diff --check`.
- [ ] Registrar run com `METRICS.json.autoresearch`.
- [ ] Provar que nenhuma permissao externa, deploy, segredo ou acao de producao foi adicionada.

## Required Evidence

- Diff aplicado nos arquivos `.ralph`.
- Resultado de `git diff --check`.
- `runs/LOOP-*/OUTPUT.md` explicando o que foi aplicado e o que ficou fora.

## Scope

Do:

- Atualizar metodo `.ralph`.
- Manter proposta restrita a roteamento e contexto.

Do not:

- Copiar codigo do OpenSwarm.
- Criar runtime multiagente.
- Rodar LLM externo.
- Usar chaves, deploy ou publicacao.

## Context

Experimento:

- `.autoresearch/experiments/openswarm-specialist-routing-v1/`

Fonte:

- `https://github.com/VRSEN/OpenSwarm`
- Commit estudado: `92c8062bfeb58a9e96db8b7ac72da5f95c33479e`

## Blockers

Se a revisao concluir que o patch cria complexidade demais, bloquear e propor alternativa menor.

## Handoff

Comecar lendo `DECISAO.md`, depois `PATCH_PROPOSTO.diff`.

## AutoResearch Signal

method_signal: weak_pm
candidate_targets: `.ralph/AUTORESEARCH.md`, `.ralph/PM.md`, `.ralph/TASK_TEMPLATE.md`

