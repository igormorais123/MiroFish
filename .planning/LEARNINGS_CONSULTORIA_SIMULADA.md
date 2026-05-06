# Aprendizados — Consultoria por Simulacao Auditavel

Data: 2026-05-04

## Contexto

A fase aplicou ao MiroFish INTEIA a promessa das reportagens da Mirante/INTEIA sobre consultoria por simulacao, agentes sinteticos, gemeos digitais e opiniao publica simulada.

Fontes-base:

- https://mirantenews.com.br/artigos/inteia-consultoria-simulacoes-agentes-gemeos-digitais
- https://mirantenews.com.br/artigos/opiniao-publica-agentes-sinteticos
- Scientific Reports 2026: `10.1038/s41598-026-44206-z`
- Scientific Reports 2025: `10.1038/s41598-025-99704-3`

## Aprendizados

1. Relatorio nao pode ser tratado como ultima etapa textual; precisa ser produto de uma simulacao verificavel.
2. Volume de posts nao prova opiniao publica. E necessario medir diversidade semantica, distribuicao de agentes e tipos de acao.
3. Simulacoes antigas com muitas acoes `CREATE_POST` eram tecnicamente completas, mas metodologicamente fracas.
4. O trace OASIS e mais confiavel que logs narrativos para provar interacao social real.
5. Citacoes diretas sao risco alto: se nao existem literalmente no corpus local, devem bloquear a entrega ou virar parafrase marcada.
6. Interface tambem e governanca: o usuario nao deve conseguir gerar relatorio cliente quando o backend ja sabe que a evidencia e insuficiente.
7. Smoke test e entrega cliente precisam de modos separados.

## Criacoes

- Gate estrutural de relatorio.
- Auditoria local de evidencias e citacoes.
- Auditoria numerica para percentuais, probabilidades e contagens.
- Manifesto de evidencias por relatorio.
- API de artefatos auditaveis.
- API de qualidade da simulacao.
- Status `publishable` e estados de bloqueio.
- Status `diagnostic_only` para smoke/demo nao publicavel.
- Cadeia de custodia visual na etapa de relatorio.
- Pulso social inicial OASIS.
- Testes especificos para gate, governanca de entrega, auditoria, diversidade, estado e bootstrap social.

## Decisao operacional

Relatorio cliente INTEIA so e publicavel se atravessar:

`briefing -> grafo -> perfis -> config -> simulacao -> diversidade -> trace OASIS -> auditoria de citacoes/numeros -> relatorio`

Se qualquer etapa falhar, a saida deve ser diagnostico tecnico ou bloqueio, nao recomendacao consultiva.

## Proxima validacao

Rodar nova simulacao real com LLM ativo e volume suficiente, verificar `quality` e gerar relatorio. O objetivo e confirmar que o pulso social e o contrato comportamental produzem interacoes persistidas e diversidade acima dos limites.
