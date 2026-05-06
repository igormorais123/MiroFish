# Aprendizado

## O que funcionou

- OpenSwarm e uma boa fonte de padroes de roteamento e entregaveis, especialmente por ter `AGENTS.md` como guia de customizacao.
- O desenho "orquestrador nao executa" combina com a separacao Ralph entre PM, executor, verificacao e AutoResearch.
- O melhor transplante para Ralph e o contrato de handoff com contexto limpo, nao a topologia completa de agentes.

## O que nao funcionou

- A busca local com `rg` falhou por bloqueio de execucao do Windows. Foi usada busca nativa do sistema.
- O repositorio externo ainda e novo e muda rapido; o estudo precisa registrar commit e data para nao virar memoria instavel.

## Gotchas para o proximo ciclo

- Nao aplicar automaticamente patches inspirados por fonte externa sem revisao.
- Nao misturar leitura externa com acao externa na mesma sessao.
- Manter AutoResearch focado em componentes pequenos: `PM.md`, `AUTORESEARCH.md`, `TASK_TEMPLATE.md`, `VERIFY.md`.

## Deve virar melhoria no metodo?

Sim.

Alvos:

- `.ralph/AUTORESEARCH.md`
- `.ralph/PM.md`
- `.ralph/TASK_TEMPLATE.md`

## AutoResearch

- method_signal: `weak_pm`
- candidate_targets: `.ralph/AUTORESEARCH.md`, `.ralph/PM.md`, `.ralph/TASK_TEMPLATE.md`
- experiment_recommended: `true`

