# Proxima Acao

## Escolha recomendada

Executar `MF-RL-003`: revisar e aplicar, se aprovado, o patch proposto em `.autoresearch/experiments/openswarm-specialist-routing-v1/PATCH_PROPOSTO.diff`.

## Por que agora

O estudo encontrou uma melhoria pequena e acionavel para o gargalo de PM/roteamento: classificar tarefas AutoResearch por lanes especialistas antes de deixar o executor agir.

## Evidencia esperada

- `.ralph/AUTORESEARCH.md`, `.ralph/PM.md` e `.ralph/TASK_TEMPLATE.md` atualizados.
- `git diff --check` passa.
- Novo run registra que a regra de uma unidade por ciclo continua preservada.

