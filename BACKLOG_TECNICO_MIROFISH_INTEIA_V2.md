# Backlog Tecnico - MiroFish-Inteia v2

Data: 2026-03-17
Status: backlog inicial executavel

## Convencoes

- Prioridade: P0, P1, P2
- Tipo: infra, backend, frontend, dados, produto, observabilidade
- Estimativa: S, M, L

## Epic 1 - Fundacao do repositorio

### MI-001
Prioridade: P0
Tipo: produto
Estimativa: S
Descricao: criar repositório `MiroFish-Inteia` e atualizar naming principal
Aceite:
- README inicial atualizado
- nome do projeto padronizado

### MI-002
Prioridade: P0
Tipo: backend
Estimativa: S
Descricao: revisar `.env.example` para realidade INTEIA
Aceite:
- `LLM_BASE_URL` orientado a OmniRoute
- variaveis obrigatorias e opcionais separadas

### MI-003
Prioridade: P0
Tipo: backend
Estimativa: S
Descricao: centralizar configuracao de provider/modelo com fallback explicito
Aceite:
- configuracao unica de LLM
- suporte a aliases internos

## Epic 2 - OmniRoute first

### MI-010
Prioridade: P0
Tipo: backend
Estimativa: M
Descricao: adaptar `backend/app/utils/llm_client.py` para aliases OmniRoute
Aceite:
- aceita `helena-premium`
- aceita `haiku-tasks`
- aceita alias configuravel por env

### MI-011
Prioridade: P0
Tipo: backend
Estimativa: M
Descricao: adicionar timeout, retry e logging estrutural no cliente LLM
Aceite:
- retries configuraveis
- timeout configuravel
- loga modelo efetivo e latencia

### MI-012
Prioridade: P1
Tipo: observabilidade
Estimativa: S
Descricao: adicionar metricas simples de chamadas LLM
Aceite:
- contagem de chamadas
- taxa de erro
- tempo medio

## Epic 3 - API interna do motor

### MI-020
Prioridade: P0
Tipo: backend
Estimativa: M
Descricao: definir contrato de API do MiroFish-Inteia para INTEIA
Aceite:
- endpoints documentados
- payloads de request/response definidos

### MI-021
Prioridade: P0
Tipo: backend
Estimativa: M
Descricao: criar endpoint para criar projeto de simulacao
Aceite:
- retorna IDs internos e externos

### MI-022
Prioridade: P0
Tipo: backend
Estimativa: M
Descricao: criar endpoint para upload de materiais e briefing
Aceite:
- aceita arquivo e texto
- valida tipo e tamanho

### MI-022A
Prioridade: P0
Tipo: backend
Estimativa: M
Descricao: aceitar briefing estruturado INTEIA com `cenario`, `atores`, `segmentos`, `canais`, `hipoteses` e `territorio`
Aceite:
- payload estruturado validado
- contexto persistido no projeto
- contexto transformado em insumo para ontologia e simulacao

### MI-023
Prioridade: P0
Tipo: backend
Estimativa: M
Descricao: criar endpoint para iniciar preparo de simulacao
Aceite:
- job assinado
- status consultavel

### MI-024
Prioridade: P0
Tipo: backend
Estimativa: M
Descricao: criar endpoint para iniciar execucao da simulacao
Aceite:
- retorna job id
- estado inicial persistido

### MI-025
Prioridade: P0
Tipo: backend
Estimativa: S
Descricao: criar endpoint para consultar status, progresso e artefatos
Aceite:
- status, round, erros e relatorio disponiveis

### MI-026
Prioridade: P1
Tipo: produto
Estimativa: M
Descricao: executar benchmark de encaixe do MiroFish-Inteia com Lenia-RR em `http://127.0.0.1:8000/lenia.html?uf=rr`
Aceite:
- baseline Lenia-RR documentado
- teste com insumos MiroFish executado
- parecer de go ou no-go registrado

### MI-027
Prioridade: P1
Tipo: backend
Estimativa: S
Descricao: expor contrato de exportacao de sinais do MiroFish-Inteia para o Lenia-RR
Aceite:
- endpoint `/lenia-export` por projeto ou simulacao
- payload inclui territorio, atores, segmentos, canais e sinais agregados
- contrato pronto para consumo pelo teste em `lenia.html?uf=rr`

## Epic 4 - Boundary e seguranca

### MI-030
Prioridade: P0
Tipo: infra
Estimativa: M
Descricao: implementar autenticacao entre servicos INTEIA e MiroFish-Inteia
Aceite:
- service token validado
- rotas internas protegidas

### MI-031
Prioridade: P1
Tipo: observabilidade
Estimativa: S
Descricao: logar correlacao entre `project_id` INTEIA e `simulation_id` do motor
Aceite:
- correlacao visivel em logs

## Epic 5 - Helena layer

### MI-040
Prioridade: P0
Tipo: backend
Estimativa: L
Descricao: reescrever a camada de relatorio para o padrao Helena
Aceite:
- resposta direta
- fundamentacao
- insight diferencial
- recomendacao pratica

### MI-041
Prioridade: P0
Tipo: backend
Estimativa: M
Descricao: incluir marcacao de origem de evidencia no relatorio
Aceite:
- dado interno
- simulacao
- inferencia
- fonte externa

### MI-042
Prioridade: P1
Tipo: backend
Estimativa: M
Descricao: incluir campo de confianca, premissas e contradicoes
Aceite:
- relatorio sempre traz os tres blocos

## Epic 6 - Integracao com perfis INTEIA

### MI-050
Prioridade: P0
Tipo: dados
Estimativa: L
Descricao: mapear schemas de perfis INTEIA para agente MiroFish
Aceite:
- documento de mapeamento
- adaptador implementado

### MI-051
Prioridade: P0
Tipo: backend
Estimativa: M
Descricao: criar importador de perfis sinteticos
Aceite:
- importa lote de perfis
- preserva origem e metadados

### MI-052
Prioridade: P1
Tipo: dados
Estimativa: M
Descricao: suportar categorias iniciais
Aceite:
- eleitor
- consultor
- magistrado
- parlamentar
- gestor

## Epic 7 - Persistencia e auditoria

### MI-060
Prioridade: P0
Tipo: backend
Estimativa: M
Descricao: registrar metadados de execucao em storage estruturado
Aceite:
- briefing
- modelos
- timestamps
- status

### MI-061
Prioridade: P1
Tipo: backend
Estimativa: M
Descricao: versionar artefatos de simulacao
Aceite:
- input
- configuracao
- output bruto
- relatorio final

### MI-062
Prioridade: P1
Tipo: observabilidade
Estimativa: M
Descricao: consolidar trilha de auditoria por execucao
Aceite:
- usuario
- projeto
- execucao
- artefatos vinculados

## Epic 8 - Frontend INTEIA

### MI-070
Prioridade: P1
Tipo: frontend
Estimativa: M
Descricao: criar modulo `Simulacoes` no frontend INTEIA
Aceite:
- pagina listagem
- pagina nova simulacao

### MI-071
Prioridade: P1
Tipo: frontend
Estimativa: M
Descricao: criar wizard de execucao
Aceite:
- objetivo
- materiais
- motor
- confirmacao

### MI-072
Prioridade: P1
Tipo: frontend
Estimativa: M
Descricao: criar pagina de acompanhamento de execucao
Aceite:
- status
- progresso
- logs principais

### MI-073
Prioridade: P1
Tipo: frontend
Estimativa: M
Descricao: criar visualizacao do relatorio Helena
Aceite:
- resumo executivo
- sinais
- recomendacoes

## Epic 9 - Pilotos

### MI-080
Prioridade: P0
Tipo: produto
Estimativa: M
Descricao: preparar dataset e criterios do Piloto A
Aceite:
- briefing
- materiais
- KPIs

### MI-081
Prioridade: P0
Tipo: produto
Estimativa: M
Descricao: executar Piloto A e documentar benchmark
Aceite:
- comparacao com motores atuais
- parecer final go/no-go

### MI-082
Prioridade: P1
Tipo: produto
Estimativa: M
Descricao: preparar e executar Piloto B
Aceite:
- benchmark registrado

### MI-083
Prioridade: P1
Tipo: produto
Estimativa: M
Descricao: preparar e executar Piloto C
Aceite:
- benchmark registrado

## Epic 10 - Decisao estrutural sobre Zep

### MI-090
Prioridade: P1
Tipo: infra
Estimativa: M
Descricao: medir custo, valor e lock-in do uso de Zep
Aceite:
- memo tecnico com recomendacao

### MI-091
Prioridade: P1
Tipo: backend
Estimativa: L
Descricao: desenhar fallback caso Zep nao seja aprovado como dependencia estrutural
Aceite:
- estrategia documentada
- impacto mapeado

## Sequencia recomendada

Sprint 1:
- MI-001 a MI-012
- MI-020 a MI-025
- MI-030

Sprint 2:
- MI-040 a MI-042
- MI-050 a MI-051
- MI-060

Sprint 3:
- MI-070 a MI-073
- MI-080 a MI-081

Sprint 4:
- MI-082 a MI-083
- MI-090 a MI-091

## Definicao de pronto

Uma task so esta pronta quando:

- codigo foi implementado
- configuracao documentada
- logica verificada localmente
- impacto no fluxo INTEIA foi registrado
