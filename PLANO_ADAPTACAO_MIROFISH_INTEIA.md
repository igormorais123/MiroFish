# Plano de Adaptacao MiroFish-Inteia

Data: 2026-03-17
Status: proposta executiva para decisao e execucao
Escopo: adaptar o MiroFish ao ecossistema INTEIA, aproveitando os ativos existentes em `C:\Agentes`

## 1. Tese central

O MiroFish deve entrar na INTEIA como um motor de simulacao e ensaio de cenarios, nao como produto isolado nem como sistema paralelo solto.

A adaptacao correta nao e "portar o MiroFish inteiro para dentro da INTEIA" de uma vez. A adaptacao correta e:

1. manter o MiroFish como engine especializada de simulacao social e GraphRAG;
2. usar a stack atual da INTEIA como casca de produto, autenticacao, operacao e distribuicao;
3. conectar os ativos ja existentes da INTEIA, especialmente OmniRoute, backend FastAPI, frontend Next.js, bancos sinteticos e a camada Helena;
4. validar em rotas piloto com criterio de negocio e criterio tecnico.

Nome do projeto no Git: `MiroFish-Inteia`

## 2. O que a analise em C:\Agentes mostrou

### 2.1 Ativos fortes ja existentes na INTEIA

- Stack principal ja madura em `C:\Agentes\backend` e `C:\Agentes\frontend`:
  - backend FastAPI, SQLAlchemy, Postgres, JWT, Celery, Redis
  - frontend Next.js, TypeScript, React Query, Zustand
- Gateway de modelos ja operacional via OmniRoute:
  - referencias em `C:\Agentes\vila-inteia\engine\ia_client.py`
  - configuracao e healthcheck em `C:\Agentes\scripts\manage_gateway.py`, `C:\Agentes\scripts\omniroute_health_check.py`
- Identidade Helena ja definida e valiosa como camada de analise e entrega:
  - `C:\Agentes\HELENA_STRATEGOS_COMPLETA.md`
- Base de simulacao social leve ja concebida:
  - `C:\Agentes\vila-inteia`
  - `C:\Agentes\vila-inteia\FRAMEWORK_INTERACOES.md`
- Bancos sinteticos, perfis, pesquisas e dados de validacao ja acumulados:
  - `C:\Agentes\agentes`
  - `C:\Agentes\data`
  - `C:\Agentes\resultados`
- Ha inclusive plano anterior de convergencia:
  - `C:\Agentes\output\PLANO-INTEGRACAO-MIROFISH-VILA-INTEIA-v2.md`

### 2.2 O que o MiroFish traz de diferencial

- Pipeline orientado a grafo:
  - construcao de grafo a partir de documentos
  - extracao de entidades e relacoes
  - memoria temporal via Zep
- Motor de simulacao em plataforma social:
  - geracao de agentes
  - configuracao automatica de atividade
  - execucao multi-plataforma
- Camada de relatorio agentico:
  - `ReportAgent`
  - ferramentas de consulta e entrevista
- Interface de processo por etapas:
  - upload
  - grafo
  - ambiente
  - simulacao
  - relatorio
  - interacao

### 2.3 Onde ha conflito entre os dois mundos

- MiroFish hoje usa Vue/Vite no frontend; INTEIA usa Next.js/React.
- MiroFish persiste muito em arquivos locais e estado de simulacao em disco; INTEIA opera com backend mais estruturado e tende a exigir persistencia e auth institucionais.
- MiroFish usa Zep como pilar do grafo e memoria; isso aumenta dependencia externa.
- A identidade do relatorio no MiroFish ainda e generica; a INTEIA precisa que a camada final seja Helena e padroes INTEIA.
- A INTEIA ja tem motores proprios leves de agentes; MiroFish nao pode entrar substituindo tudo antes de provar superioridade.

## 3. Decisao arquitetural recomendada

### 3.1 Arquitetura-alvo

Adotar arquitetura de composicao, nao de substituicao.

`MiroFish-Inteia` deve ter esta posicao:

- Front door:
  - frontend INTEIA em Next.js
  - auth, permissao, dashboard, operacao, historico, auditoria
- Orquestracao:
  - backend INTEIA em FastAPI
  - jobs, filas, usuarios, projetos, billing interno, rastreabilidade
- Gateway de IA:
  - OmniRoute como padrao para LLM
- Motores especializados:
  - Vila INTEIA para simulacoes leves, internas e experimentais
  - MiroFish-Inteia para simulacoes ricas com grafo, memoria e cenarios mais complexos
- Camada analitica final:
  - Helena como face unica do sistema para sintese, parecer e recomendacao

### 3.2 Regra de produto

O usuario INTEIA nao deve "entrar no MiroFish".
O usuario deve "rodar uma simulacao INTEIA".

Internamente, a execucao pode usar:

- motor Vila
- motor FlockVote Lite
- motor MiroFish-Inteia
- comparador entre motores

## 4. Principios de adaptacao

1. Reaproveitar o que a INTEIA ja tem.
2. Isolar complexidade do MiroFish atras de API.
3. Nao migrar frontend Vue para producao INTEIA.
4. Padronizar tudo no gateway OmniRoute.
5. Substituir progressivamente textos, personas e entregas pelo padrao Helena/INTEIA.
6. Tratar Zep como dependencia opcional validada por piloto, nao como dogma.
7. Toda fase precisa entregar valor proprio.

## 5. Roadmap de adaptacao

## Fase 0 - Fundacao do projeto MiroFish-Inteia

Objetivo: criar o fork de trabalho e alinhar naming, configuracao e limites.

Entregas:

- criar repositório `MiroFish-Inteia`
- ajustar README e posicionamento para INTEIA
- trocar configuracao default de LLM para OmniRoute
- padronizar PT-BR nos fluxos principais
- definir `.env.example` compativel com INTEIA
- mapear dependencias externas obrigatorias e opcionais

Decisoes:

- `LLM_BASE_URL` default deve apontar para OmniRoute em ambientes INTEIA
- `LLM_MODEL_NAME` default deve usar aliases internos da INTEIA quando possivel
- Zep deve ser marcado como dependencia de simulacao rica, nao requisito para todo caso

Gate:

- projeto sobe localmente com OmniRoute
- documentacao de setup alinhada com a realidade INTEIA

## Fase 1 - Encapsular o MiroFish como servico interno

Objetivo: transformar o MiroFish em backend especializado consumivel pela INTEIA.

Entregas:

- expor API clara para:
  - criar projeto de simulacao
  - subir materiais-base
  - construir grafo
  - preparar simulacao
  - executar simulacao
  - obter relatorio
  - consultar logs/estado
- definir contrato de payloads entre INTEIA e MiroFish-Inteia
- introduzir auth por service token ou chave interna no boundary

Recomendacao:

- manter o frontend Vue apenas como console tecnico interno durante a fase de transicao
- integrar a experiencia final pelo frontend Next.js da INTEIA

Gate:

- backend INTEIA consegue acionar uma simulacao ponta a ponta no MiroFish-Inteia sem usar a UI Vue

## Fase 2 - Integracao com ativos da INTEIA

Objetivo: conectar o que ja existe em `C:\Agentes`.

### 2.1 Integracao LLM

Trocar a dependencia mental de "OpenAI compativel qualquer" por "OmniRoute primeiro".

Acoes:

- adaptar `backend/app/utils/llm_client.py` para aliases INTEIA
- permitir modelos do tipo:
  - `helena-premium`
  - `haiku-tasks`
  - combos internos da INTEIA
- adicionar timeout, retry e observabilidade seguindo o padrao ja usado na INTEIA e Vila

### 2.2 Integracao de identidade Helena

A camada de relatorio deve ser reescrita para o padrao Helena.

Acoes:

- trocar o tom e o contrato do `ReportAgent`
- padronizar saida com:
  - resposta direta
  - fundamentacao
  - insight diferencial
  - recomendacao pratica
- incluir etiquetas de origem:
  - dado interno
  - simulacao
  - inferencia
  - fonte externa

### 2.3 Integracao com dados sinteticos INTEIA

A grande oportunidade nao e criar agentes do zero toda vez.
E usar os ativos sinteticos ja existentes da INTEIA como base de persona.

Acoes:

- permitir importar perfis/agentes de `C:\Agentes\agentes`, `C:\Agentes\data` e bancos curados
- criar adaptadores de schema:
  - eleitor INTEIA -> agente MiroFish
  - consultor INTEIA -> agente MiroFish
  - magistrado/parlamentar/gestor -> agente MiroFish

Gate:

- uma simulacao do MiroFish-Inteia roda usando perfis originados da base INTEIA

## Fase 3 - Camada de persistencia e governanca

Objetivo: sair do modelo de experimento local para produto interno auditavel.

Entregas:

- registrar projetos, execucoes, artefatos e relatorios em banco INTEIA
- criar trilha de auditoria:
  - quem rodou
  - quando rodou
  - com qual input
  - com qual modelo
  - com qual versao de configuracao
- versionar cenarios e sementes
- guardar links entre:
  - material-base
  - grafo
  - simulacao
  - relatorio Helena

Recomendacao:

- usar o backend FastAPI da INTEIA como sistema de registro mestre
- o MiroFish-Inteia guarda estado tecnico
- a INTEIA guarda estado de negocio e operacao

Gate:

- uma execucao e totalmente reproduzivel e auditavel

## Fase 4 - Produto INTEIA unificado

Objetivo: expor ao usuario final uma experiencia nativa INTEIA.

Entregas:

- dashboard Next.js com modulo `Simulacoes`
- wizard de execucao no padrao INTEIA
- visualizacao de:
  - entidades
  - grafo
  - rodadas
  - sinais narrativos
  - relatorio Helena
- comparador entre motores:
  - Vila
  - FlockVote Lite
  - MiroFish-Inteia

Gate:

- usuario interno executa simulacao sem precisar saber o que e Zep, OASIS ou MiroFish

## 6. Rotas piloto recomendadas

## Piloto 1 - Simulacao de repercussao politico-eleitoral

Objetivo:
validar se o MiroFish-Inteia melhora a INTEIA em ensaio de opiniao, repercussao e narrativa.

Input:

- noticias
- fatos politicos recentes
- perfis de eleitores e atores do DF
- contexto de campanha

Saidas esperadas:

- narrativas provaveis
- clusters de reacao
- topicos quentes
- posts iniciais provaveis
- parecer Helena

Comparador:

- FlockVote Lite
- simuladores eleitorais ja existentes em `C:\Agentes`
- MiroFish-Inteia

KPI:

- utilidade percebida pelos analistas
- coerencia dos cenarios
- capacidade de gerar sinais nao triviais

## Piloto 2 - Crise reputacional e guerra narrativa

Objetivo:
simular escalada, contra-narrativas, atores influentes e janelas de resposta.

Input:

- dossie de crise
- noticias, notas, prints, material-base
- perfis institucionais, midia, influenciadores e opositores

Saidas esperadas:

- timeline de escalada
- mapas de atores
- gatilhos de agravamento
- respostas e contrarrespostas provaveis
- recomendacao operacional Helena

KPI:

- velocidade para montar cenario
- qualidade de recomendacao
- reaproveitamento em war room

## Piloto 3 - Simulacao juridico-institucional

Objetivo:
testar interacoes entre magistrados, parlamentares, atores de midia e pressao publica.

Input:

- base sintetica do judiciario ja existente em `C:\Agentes`
- materiais processuais e publicos
- eventos de interesse

Saidas esperadas:

- leituras de repercussao
- cadeias de influencia
- cenarios de resposta institucional

KPI:

- plausibilidade das interacoes
- valor para dossies e analises especiais

## 7. O que precisa ser lapidado no MiroFish para a realidade INTEIA

### 7.1 Produto

- sair do discurso "predict anything"
- entrar no discurso "simulacao estrategica assistida"

### 7.2 Identidade

- trocar naming, textos e UX para INTEIA
- Helena deve ser a camada de leitura e entrega

### 7.3 Infra

- OmniRoute primeiro
- Zep com gate de custo/beneficio
- estado operacional integrado ao backend INTEIA

### 7.4 Dados

- perfis sinteticos da INTEIA devem virar insumo de primeira classe
- importar e normalizar ativos ja curados em vez de gerar tudo toda vez

### 7.5 Qualidade

- toda simulacao precisa ter validacao
- nao vender output bruto de LLM como verdade
- exigir:
  - confianca
  - contradicoes
  - premissas
  - sinais de monitoramento

## 8. Riscos principais

### Risco 1 - Complexidade maior que o ganho

Mitigacao:

- comparar sempre contra Vila e FlockVote Lite
- manter go/no-go por fase

### Risco 2 - Dependencia excessiva de Zep

Mitigacao:

- pilotar com Zep
- medir valor
- se o ganho nao justificar, manter grafo reduzido ou persistencia alternativa

### Risco 3 - Dupla pilha de frontend

Mitigacao:

- nao migrar Vue para a frente do produto
- usar Vue apenas como console tecnico temporario

### Risco 4 - Saida bonita e pouco confiavel

Mitigacao:

- Helena precisa marcar o que e fato, inferencia e simulacao
- benchmark com casos historicos conhecidos

### Risco 5 - Projeto virar pesquisa eterna

Mitigacao:

- pilotos com prazo e criterio de negocio
- dono de produto
- metricas de decisao

## 9. Recomendacao executiva

Recomendacao: seguir com o `MiroFish-Inteia`, mas por integracao progressiva e com tres gates.

### Gate A - viabilidade tecnica

- MiroFish-Inteia roda com OmniRoute
- INTEIA aciona por API
- Helena recebe e reformata o output

### Gate B - superioridade funcional

- pelo menos um piloto mostra ganho real sobre os motores que a INTEIA ja possui

### Gate C - prontidao de produto

- autenticacao
- auditoria
- armazenamento
- dashboard INTEIA
- workflow usavel por analista

Se o Gate B falhar, o MiroFish nao deve virar plataforma central. Deve virar fonte de ideias e componentes reaproveitaveis.

Se o Gate B passar, o MiroFish-Inteia deve virar o motor premium de simulacao complexa da INTEIA.

## 10. Ordem de execucao recomendada

1. Criar o fork `MiroFish-Inteia`
2. Adaptar configuracao LLM para OmniRoute
3. Expor o backend do MiroFish como servico interno
4. Integrar Helena na camada de relatorio
5. Integrar perfis sinteticos da INTEIA
6. Rodar Piloto 1
7. Rodar Piloto 2
8. Decidir sobre Zep como dependencia estrutural
9. Integrar dashboard INTEIA
10. Fechar produto interno

## 11. Veredito Helena

O MiroFish tem aplicabilidade para a INTEIA, mas o encaixe certo e como motor premium de simulacao dentro do ecossistema ja construido por voces.

O caminho mais inteligente nao e substituir a INTEIA pelo MiroFish.
E fazer a INTEIA absorver o que o MiroFish tem de melhor, colocar Helena na ponta, e usar rotas piloto para decidir onde esse motor realmente cria vantagem.
