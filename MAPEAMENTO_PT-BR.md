# Mapeamento do Projeto MiroFish

## Visão geral

O projeto é dividido em dois blocos principais:

- `frontend/`: interface em Vue 3 com Vite.
- `backend/`: API em Flask/Python responsável por ontologia, grafo, simulação, relatório e interação.

Na prática, o fluxo do sistema é:

1. Upload de arquivos e definição do objetivo da simulação.
2. Geração de ontologia a partir dos documentos.
3. Construção do grafo de conhecimento.
4. Criação e preparação do ambiente de simulação.
5. Execução da simulação em duas plataformas.
6. Geração de relatório analítico.
7. Interação com o agente de relatório e com agentes simulados.

## Estrutura principal

### Raiz

- `package.json`: scripts principais para subir frontend e backend juntos.
- `docker-compose.yml` e `Dockerfile`: execução via contêiner.
- `README.md` e `README-EN.md`: documentação original.

### Frontend

- `frontend/src/router/index.js`: rotas da aplicação.
- `frontend/src/views/Home.vue`: tela inicial com upload e entrada do cenário.
- `frontend/src/views/MainView.vue`: etapa 1, construção do grafo.
- `frontend/src/views/SimulationView.vue`: etapa 2, configuração do ambiente.
- `frontend/src/views/SimulationRunView.vue`: etapa 3, execução da simulação.
- `frontend/src/views/ReportView.vue`: etapa 4, geração do relatório.
- `frontend/src/views/InteractionView.vue`: etapa 5, interação profunda.

### Componentes-chave do frontend

- `frontend/src/components/Step1GraphBuild.vue`: acompanhamento de ontologia e GraphRAG.
- `frontend/src/components/Step2EnvSetup.vue`: preparação dos agentes, parâmetros e eventos iniciais.
- `frontend/src/components/Step3Simulation.vue`: monitor da simulação e timeline de ações.
- `frontend/src/components/Step4Report.vue`: progresso e visualização do relatório.
- `frontend/src/components/Step5Interaction.vue`: chat com relatório, chat com agentes e questionários.
- `frontend/src/components/GraphPanel.vue`: visualização interativa do grafo.
- `frontend/src/components/HistoryDatabase.vue`: histórico das execuções.

### Backend

- `backend/run.py`: ponto de entrada da API.
- `backend/app/api/graph.py`: upload, ontologia, build do grafo e tarefas.
- `backend/app/api/simulation.py`: criação, preparação, execução e status da simulação.
- `backend/app/api/report.py`: geração, status, leitura e chat do relatório.
- `backend/app/services/`: serviços centrais de ontologia, simulação, relatório e integração com Zep.
- `backend/app/models/`: modelos de projeto e tarefas.

## APIs principais

### Grafo

- `POST /api/graph/ontology/generate`
- `POST /api/graph/build`
- `GET /api/graph/project/<project_id>`
- `GET /api/graph/data/<graph_id>`
- `GET /api/graph/task/<task_id>`

### Simulação

- `POST /api/simulation/create`
- `POST /api/simulation/prepare`
- `GET /api/simulation/prepare/status`
- `POST /api/simulation/start`
- `POST /api/simulation/stop`
- `GET /api/simulation/run_status/<simulation_id>`
- `GET /api/simulation/run_status_detail/<simulation_id>`

### Relatório

- `POST /api/report/generate`
- `POST /api/report/generate/status`
- `GET /api/report/<report_id>`
- `POST /api/report/chat`

## O que foi traduzido

A interface visível do frontend foi ajustada para português nos pontos mais críticos:

- landing page;
- navegação entre etapas;
- painel do grafo;
- histórico de execuções;
- etapas de construção, ambiente, simulação, relatório e interação;
- placeholders, botões, logs exibidos ao usuário e mensagens de erro da interface.

## Observação importante

Ainda existem trechos em chinês no código-fonte interno, principalmente:

- comentários;
- parsers e regex do relatório;
- arquivos antigos não conectados ao fluxo principal atual;
- descrições internas do backend.

Esses trechos não impedem o uso da interface em português, mas podem ser limpos em uma segunda passada se você quiser uma base 100% localizada também no código e na documentação.
