# Decisao: OpenSwarm Specialist Routing v1

## Recomendacao

Aplicar em ciclo separado o patch proposto em `PATCH_PROPOSTO.diff`.

## Decisao atual

Nao aplicado neste run.

## Motivo

Este ciclo leu fonte externa e gerou proposta de metodo. Pela politica Ralph/AutoResearch, a leitura externa e a aplicacao de patch devem ficar separadas quando o patch altera o metodo de execucao.

## Condicoes para aplicar

- Revisar se as lanes nao viram permissao para orquestracao grande.
- Garantir que `specialist_lane` e apenas metadado de tarefa.
- Rodar `git diff --check`.
- Registrar novo run com `method_signal` e evidencia.

## Resultado esperado

Ralph continua simples:

```text
selecionar tarefa -> executar -> verificar -> auditar -> registrar aprendizado -> gerar proxima acao
```

Mas AutoResearch ganha um mecanismo de roteamento leve inspirado no OpenSwarm:

```text
fonte externa -> context packet -> lane especialista -> ranking -> patch proposto -> decisao
```

