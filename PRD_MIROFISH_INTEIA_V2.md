# PRD - MiroFish-Inteia v2

Data: 2026-03-17
Owner proposto: INTEIA
Status: draft executivo

## 1. Visao do produto

`MiroFish-Inteia` e o motor premium de simulacao social, narrativa e cenarios complexos da INTEIA.

Ele transforma materiais-base, atores e contexto em:

- grafo de entidades e relacoes
- simulacao multiagente
- sinais narrativos
- cenarios de repercussao
- relatorio executivo no padrao Helena

## 2. Problema

A INTEIA ja possui ativos fortes em pesquisa sintetica, simulacao leve, entrevistas e analise.
O que ainda falta e uma camada robusta para:

- transformar documentos e fatos em grafo contextual
- simular dinamicas sociais complexas entre multiplos atores
- ensaiar repercussao e evolucao de narrativa
- comparar cenarios de forma mais estruturada

## 3. Objetivo do produto

Dar a analistas e liderancas da INTEIA um ambiente de simulacao rica para:

- eleitoral
- juridico-institucional
- crise reputacional
- opiniao publica
- testes de narrativa
- acoplamento analitico com Lenia quando houver ganho real

## 4. Nao-objetivos

- nao substituir toda a plataforma INTEIA
- nao substituir a UI principal da INTEIA
- nao ser um chatbot isolado
- nao virar dependente obrigatorio de Zep sem validacao

## 5. Usuarios

### Primarios

- analista estrategico INTEIA
- lider de projeto
- equipe de guerra narrativa/crise

### Secundarios

- consultor senior
- area comercial em demonstracoes controladas
- parceiro interno de pesquisa e dossie

## 6. Jobs to be done

- "Quero simular como um tema vai repercutir entre atores distintos antes de agir."
- "Quero transformar material disperso em cenario narrativo consistente."
- "Quero comparar meu entendimento atual com um ensaio multiagente."
- "Quero um parecer Helena que extraia o que interessa de uma simulacao complexa."

## 7. Proposta de valor

O usuario nao recebe apenas um resumo.
Ele recebe:

- uma simulacao estruturada
- um mapa de atores e relacoes
- um conjunto de cenarios
- uma leitura executiva de Helena

## 8. Escopo funcional v1

## 8.1 Criar projeto de simulacao

O usuario ou backend INTEIA deve conseguir:

- criar projeto
- informar objetivo da simulacao
- anexar materiais-base
- informar briefing estruturado com cenario, atores, segmentos, canais, hipoteses e territorio
- selecionar tipo de simulacao

## 8.2 Construir contexto

O sistema deve:

- extrair texto
- gerar ontologia/grafo
- identificar entidades
- preparar contexto de simulacao

## 8.3 Preparar agentes

O sistema deve:

- gerar agentes do proprio MiroFish
ou
- importar perfis sinteticos da INTEIA

## 8.4 Rodar simulacao

O sistema deve:

- configurar parametros automaticamente
- rodar simulacao
- registrar estado, progresso e eventos

## 8.5 Produzir relatorio Helena

O sistema deve entregar:

- resumo executivo
- principais sinais
- hipoteses e contradicoes
- recomendacoes praticas

## 8.6 Expor artefatos para INTEIA

Deve ser possivel consultar:

- status
- logs
- entidades
- resultados
- relatorio

## 9. Requisitos funcionais

### RF-01
Permitir criar uma execucao via API.

### RF-02
Permitir subir materiais-base por arquivo e texto.

### RF-02A
Permitir criar projeto por briefing estruturado da INTEIA.

### RF-03
Permitir construir grafo contextual da execucao.

### RF-04
Permitir usar perfis importados da INTEIA como insumo de agentes.

### RF-05
Permitir acompanhar status da simulacao.

### RF-06
Gerar relatorio final em formato consumivel pela INTEIA.

### RF-07
Associar cada execucao a projeto, usuario, timestamp e configuracao.

### RF-08
Registrar evidencias e premissas do relatorio.

### RF-09
Permitir benchmark de utilidade entre Lenia-RR puro e Lenia-RR com insumos do MiroFish-Inteia.

## 10. Requisitos nao funcionais

### RNF-01
Integracao padrao com OmniRoute.

### RNF-02
Autenticacao entre servicos.

### RNF-03
Observabilidade minima:

- latencia
- modelo usado
- erros
- estado da execucao

### RNF-04
Persistencia reproduzivel de execucao.

### RNF-05
Compatibilidade com operacao Windows local e Linux de servidor.

## 11. UX esperada

O usuario final na INTEIA deve ver um fluxo simples:

1. novo projeto de simulacao
2. objetivo
3. materiais
4. escolha do motor
5. acompanhar execucao
6. ler parecer Helena

O usuario nao deve ter que lidar diretamente com:

- Zep
- OASIS
- scripts do MiroFish
- terminal

## 12. Dependencias

### Obrigatorias

- backend INTEIA
- frontend INTEIA
- OmniRoute
- storage de artefatos

### Opcionais

- Zep
- frontend Vue do MiroFish como console tecnico
- ambiente Lenia em `http://127.0.0.1:8000/lenia.html?uf=rr` como superficie de validacao de encaixe

## 13. Metricas de sucesso

### Produto

- tempo medio para gerar simulacao aproveitavel
- taxa de execucoes concluidas com sucesso
- uso recorrente por analistas

### Qualidade

- utilidade percebida do relatorio Helena
- numero de insights aproveitaveis por execucao
- taxa de reuso em dossies/war rooms

### Benchmark

- comparacao favoravel com motores atuais da INTEIA em ao menos um piloto

## 14. Fases de release

### Release 0

- fork
- setup OmniRoute
- backend rodando local

### Release 1

- API de simulacao interna
- relatorio Helena minimo

### Release 2

- importador de perfis INTEIA
- Piloto A

### Release 3

- governanca e trilha de auditoria
- telas INTEIA

### Release 4

- pilotos B e C
- decisao de escalonamento

## 15. Criterio de prontidao para rollout interno

- auth entre servicos funcionando
- uma simulacao ponta a ponta pela UI INTEIA
- relatorio Helena com confianca e evidencias
- benchmark com ganho real em pelo menos um piloto
- logs e auditoria suficientes para uso interno
