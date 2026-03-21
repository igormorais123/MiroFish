# Plano de Adaptacao MiroFish-Inteia v2

Data: 2026-03-17
Status: aprovado para refinamento tecnico
Projeto Git: `MiroFish-Inteia`

## 1. Veredito v2

O plano anterior estava correto na direcao, mas ainda amplo demais em tres pontos:

1. faltava separar claramente o que fica no ecossistema INTEIA e o que fica dentro do MiroFish-Inteia;
2. faltava definir a estrategia de produto para nao criar um sistema duplicado ao que ja existe em `C:\Agentes`;
3. faltava detalhar os pilotos com criterio objetivo de aprovacao.

Nesta v2, a decisao fica assim:

- INTEIA continua sendo a plataforma principal.
- MiroFish-Inteia vira um motor especializado de simulacao social e GraphRAG.
- Helena continua sendo a interface cognitiva final do produto.
- OmniRoute continua sendo o gateway padrao de modelos.
- Zep entra como dependencia premium validada por benchmark, nao como premissa obrigatoria.

## 2. Arquitetura-alvo fechada

## 2.1 O que permanece na INTEIA

- autenticacao e autorizacao
- cadastro de usuarios, projetos e permissoes
- UI principal em Next.js
- orquestracao de jobs no backend FastAPI
- armazenamento canonico de execucoes e auditoria
- padrao visual, textos, tom e relatorios Helena
- governanca de dados e historico

## 2.2 O que fica no MiroFish-Inteia

- ingestao de material-base para simulacao
- construcao de grafo e ontologia de simulacao
- geracao e adaptacao de agentes
- configuracao automatica da simulacao
- execucao do motor social
- memoria temporal de simulacao
- geracao de artefatos brutos da simulacao

## 2.3 Boundary entre os dois sistemas

O boundary deve ser API-first.

A INTEIA nao deve incorporar o frontend Vue do MiroFish em producao.
O Vue fica apenas como console tecnico temporario para:

- debugging
- homologacao
- comparacao de comportamento

Em producao, a INTEIA fala com o MiroFish-Inteia por API.

## 3. Estrategia de integracao

## 3.1 Integracao minima obrigatoria

- MiroFish-Inteia aceita chamadas autenticadas do backend INTEIA
- MiroFish-Inteia usa OmniRoute por padrao
- MiroFish-Inteia devolve artefatos em formato consumivel pela INTEIA
- Helena reinterpreta a simulacao antes de entregar ao usuario final

## 3.2 Integracao premium

- importacao direta de perfis sinteticos INTEIA
- benchmark lado a lado com Vila e FlockVote Lite
- teste de encaixe com Lenia em `http://127.0.0.1:8000/lenia.html?uf=rr`
- persistencia cruzada de projeto, simulacao, relatorio e evidencias
- trilha de auditoria unificada

## 3.3 Checkpoint Lenia-RR

Antes de consolidar o `MiroFish-Inteia` como engine premium, a INTEIA deve testar se o sistema Lenia ja em uso para Roraima ganha densidade analitica real com a incorporacao do MiroFish adaptado.

Ambiente de teste:

- `http://127.0.0.1:8000/lenia.html?uf=rr`

Pergunta de validacao:

- o Lenia-RR fica mais util quando recebe do MiroFish-Inteia camadas de atores, narrativas, escalada de eventos, clusters de influencia e hipoteses de repercussao?

Teste minimo:

1. rodar o Lenia-RR puro como baseline
2. rodar o Lenia-RR com insumos exportados do MiroFish-Inteia
3. comparar utilidade analitica, clareza operacional e valor para decisao

Go:

- o acoplamento melhora a leitura do territorio sem aumentar ruido de forma desproporcional
- os analistas conseguem extrair hipoteses mais acionaveis
- Helena consegue sintetizar a combinacao Lenia + MiroFish sem perda de rastreabilidade

Nao-go:

- o MiroFish apenas duplica sinais que o Lenia ja entrega
- o ganho visual ou narrativo nao se converte em ganho analitico
- a integracao aumenta complexidade operacional sem retorno claro

## 4. Mapa de adaptacao do codigo

## 4.1 Adaptacoes obrigatorias no MiroFish

### Camada de configuracao

- trocar defaults de `LLM_BASE_URL` e `LLM_MODEL_NAME` para o padrao OmniRoute INTEIA
- aceitar aliases internos como:
  - `helena-premium`
  - `haiku-tasks`
  - `sonnet-analysis`

### Camada de cliente LLM

- reforcar `backend/app/utils/llm_client.py`
- adicionar:
  - timeout configuravel
  - retry exponencial
  - observabilidade de latencia
  - log de provider/modelo efetivo
  - limpeza robusta de output

### Camada de relatorio

- reposicionar o `ReportAgent`
- retirar tom generico
- reescrever para padrao Helena:
  - resposta direta
  - fundamentacao
  - insight diferencial
  - recomendacao pratica
  - grau de confianca
  - premissas
  - contradicoes

### Camada de dados

- criar adaptadores para ingestao de perfis da INTEIA
- separar:
  - agente nativo MiroFish
  - agente importado da INTEIA
- preservar metadados de origem e versao do perfil

### Camada operacional

- expor endpoints estaveis para criar/rodar/consultar simulacao
- adicionar auth entre servicos
- formalizar estados da execucao
- amarrar logs e run state a IDs externos da INTEIA

## 4.2 Adaptacoes obrigatorias na INTEIA

- adicionar modulo `Simulacoes`
- criar tela de submissao de materiais
- criar tela de acompanhamento de execucao
- criar tela de leitura do relatorio Helena
- registrar execucoes, custos, latencia e artefatos

## 5. Pilotos v2 com criterio de aprovacao

## Piloto A - Eleitoral narrativo

Pergunta:
o MiroFish-Inteia melhora a leitura de repercussao e narrativa alem do que a INTEIA ja faz?

Entrada:

- noticias
- fatos de campanha
- perfis de eleitores
- atores politicos e de midia

Saida:

- sequencia de narrativas provaveis
- atores que puxam pauta
- topicos quentes
- pontos de ruptura
- parecer Helena

Go:

- analistas consideram o output mais util do que a rotina atual
- surgem ao menos 3 sinais nao triviais aproveitaveis
- tempo de execucao fica abaixo do limite acordado para operacao

## Piloto B - Crise reputacional

Pergunta:
o motor antecipa melhor escalada, contragolpes e pontos de contencao?

Entrada:

- dossie de crise
- cronologia
- atores
- material-base

Saida:

- mapa de escalada
- resposta provavel dos atores
- janelas de mitigacao
- recomendacao de resposta

Go:

- time de crise considera o mapa acionavel
- Helena consegue sintetizar com rastreabilidade
- simulacao nao colapsa em alucinacao evidente

## Piloto C - Juridico-institucional

Pergunta:
o MiroFish-Inteia adiciona valor real na leitura de influencia cruzada entre judiciario, legislativo, midia e opiniao publica?

Entrada:

- perfis sinteticos do judiciario
- materiais publicos
- cronologia do caso

Saida:

- cadeias de influencia
- cenarios de repercussao
- hotspots de conflito institucional

Go:

- ganho real em relacao a leitura estatica de dossie
- utilidade percebida para parecer especial

## 6. Ordem recomendada de execucao

1. abrir repositório `MiroFish-Inteia`
2. adaptar LLM para OmniRoute
3. transformar o backend do MiroFish em servico interno
4. integrar Helena na camada de relatorio
5. criar importador de perfis INTEIA
6. rodar Piloto A
7. decidir se Zep permanece como componente estrutural
8. testar encaixe no Lenia-RR em `http://127.0.0.1:8000/lenia.html?uf=rr`
9. rodar Piloto B
10. integrar telas na INTEIA
11. rodar Piloto C
12. decidir rollout interno

## 7. Riscos v2 e resposta

### Risco: duplicar o que a INTEIA ja tem

Resposta:
benchmark explicito com Vila e FlockVote Lite.

### Risco: custo e lock-in do Zep

Resposta:
tratar como modulo premium e medir retorno.

### Risco: frontend duplicado

Resposta:
producao apenas na UI INTEIA.

### Risco: saida bonita e fraca

Resposta:
Helena precisa marcar fato, inferencia, simulacao e confianca.

## 8. Decisao final v2

O `MiroFish-Inteia` deve avancar.

Mas deve avancar como:

- engine especializada
- integrada ao ecossistema INTEIA
- sob comando da camada Helena
- validada por pilotos com criterio de negocio

Se superar os motores atuais da INTEIA em pelo menos um piloto de alta relevancia, vira motor premium.
Se nao superar, seus componentes ainda devem ser reaproveitados no stack INTEIA.
