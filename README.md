<div align="center">

# 🐟 MiroFish INTEIA

### Motor de Simulação Social Multiagente para Cenários Complexos

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Node.js](https://img.shields.io/badge/Node.js-20+-339933?style=flat-square&logo=node.js&logoColor=white)](https://nodejs.org)
[![Vue.js](https://img.shields.io/badge/Vue.js-3-4FC08D?style=flat-square&logo=vue.js&logoColor=white)](https://vuejs.org)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat-square&logo=docker&logoColor=white)](https://docker.com)
[![Fork](https://img.shields.io/badge/Fork%20de-666ghj%2FMiroFish-DAA520?style=flat-square)](https://github.com/666ghj/MiroFish)

*Fork adaptado para o contexto brasileiro: simulação político-eleitoral, jurídico-institucional e análise de crise.*

[Sobre](#sobre) · [O que mudou no fork](#o-que-mudou-no-fork-inteia) · [Como Rodar](#como-rodar) · [Deploy](#deploy-com-docker) · [Documentação](#documentação)

</div>

---

## Sobre

**MiroFish** é um motor de previsão baseado em múltiplos agentes, originalmente criado por [666ghj](https://github.com/666ghj/MiroFish). Transforma sinais do mundo real — notícias, relatórios, políticas, narrativas — em um ambiente digital onde agentes com memória, personalidade e lógica de ação próprias interagem para produzir dinâmicas sociais emergentes.

### Fluxo de trabalho

```
Material-base → Extração de conhecimento → Grafo de entidades
     ↓
Configuração do ambiente → Perfis dos agentes → Relações
     ↓
Simulação paralela → Interações multiagente → Memória temporal
     ↓
Relatório analítico → Conversa com agentes → Insights
```

## O que mudou no fork INTEIA

| Aspecto | MiroFish Original | Fork INTEIA |
|---------|------------------|-------------|
| **Idioma** | Chinês/Inglês | Português brasileiro completo |
| **Contexto** | Acadêmico genérico | Político-eleitoral, jurídico, crise |
| **LLM Gateway** | OpenAI direto | OmniRoute (custo zero) + fallback Anthropic |
| **Memória** | Zep Cloud obrigatório | Zep opcional, fallback keyword |
| **Segurança** | Básica | Headers CSP, CORS, iframe policy |
| **Deploy** | Local | Docker multi-stage + nginx em VPS |
| **Relatório** | ReportAgent padrão | Helena Strategos (analista-chefe INTEIA) |
| **Tradução** | — | i18n completo, conteúdo forçado em PT-BR |
| **Performance** | — | Timeout LLM 90s, fallback strategies |
| **Persistência** | — | State em disco (tasks_state.json) |
| **Mobile** | — | Responsivo (breakpoints 480px) |

### Aplicações

- **Simulação eleitoral** — cenários de campanha, repercussão de narrativa
- **Análise jurídico-institucional** — dinâmicas entre atores do sistema de justiça
- **Crise reputacional** — evolução de narrativa e opinião pública
- **Testes de narrativa** — impacto de diferentes abordagens comunicacionais
- **Pesquisa sintética** — integração com FlockVote (MAE 4.4pp no DF 2022)

## Arquitetura

```
mirofish-inteia/
├── backend/                   # Python 3.12 + FastAPI
│   ├── app/
│   │   ├── services/          # Gerenciador de simulação, ontologia, LLM
│   │   └── utils/             # Cliente LLM, Graphiti, Zep
│   ├── scripts/               # Simulação paralela, proxy LLM
│   └── tests/
│
├── frontend/                  # Vue.js 3 + Vite
│   ├── src/
│   │   ├── views/             # Home, simulação, relatório
│   │   └── api/               # Cliente da API
│   └── public/
│
├── deploy/                    # Configurações de deploy
├── docker-compose.yml         # Orquestração de containers
├── Dockerfile                 # Build multi-stage
│
├── PRD_MIROFISH_INTEIA_V2.md  # Product Requirements Document
├── BACKLOG_TECNICO_*.md       # Backlog técnico
├── PLANO_ADAPTACAO_*.md       # Plano de adaptação do fork
└── MAPEAMENTO_PT-BR.md        # Mapeamento de tradução
```

## Como Rodar

### Requisitos

| Ferramenta | Versão | Verificação |
|------------|--------|-------------|
| Node.js | 18+ | `node -v` |
| Python | 3.11–3.12 | `python --version` |
| uv | atual | `uv --version` |

### Instalação

```bash
# Clone o fork
git clone https://github.com/igormorais123/MiroFish.git
cd MiroFish

# Configure variáveis de ambiente
cp .env.example .env
# Edite .env com suas chaves

# Instale tudo
npm run setup:all

# Rode
npm run dev
```

**Endereços padrão:**
- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:5001`

### Variáveis de ambiente

```env
# LLM (via OmniRoute ou OpenAI-compatible)
LLM_API_KEY=sua_chave
LLM_BASE_URL=http://localhost:20128    # OmniRoute local
LLM_MODEL_NAME=BestFREE

# Zep Cloud (opcional)
ZEP_API_KEY=sua_chave_zep
```

## Deploy com Docker

```bash
cp .env.example .env
docker compose up -d
```

O compose expõe as portas `3000` (frontend) e `5001` (API) por padrão.

### Deploy em VPS

O fork inclui configuração para deploy em VPS com nginx como reverse proxy:

```bash
# Build e deploy
docker compose -f docker-compose.yml up -d --build

# Verificar
curl http://seu-ip:4000/api/health
```

## Documentação

| Documento | Descrição |
|-----------|-----------|
| [PRD v2](PRD_MIROFISH_INTEIA_V2.md) | Requisitos do produto |
| [Backlog Técnico](BACKLOG_TECNICO_MIROFISH_INTEIA_V2.md) | Tasks técnicas pendentes |
| [Plano de Adaptação](PLANO_ADAPTACAO_MIROFISH_INTEIA_V2.md) | Roadmap do fork |
| [Mapeamento PT-BR](MAPEAMENTO_PT-BR.md) | Referência de tradução |
| [Integração Lenia](LENIA_MIROFISH_INTEGRACAO.md) | Ponte com sistema eleitoral |

## Projeto Original

Fork de [MiroFish](https://github.com/666ghj/MiroFish) por 666ghj, baseado no framework [OASIS](https://github.com/camel-ai/oasis) (CAMEL-AI). O motor de simulação é impulsionado pelo grupo Shanda.

- [Demo original](https://666ghj.github.io/mirofish-demo/)
- [DeepWiki](https://deepwiki.com/666ghj/MiroFish)

## Projetos Relacionados

- **[Vila INTEIA](https://github.com/igormorais123/vila-inteia)** — Campus 3D com 144 consultores lendários simulados
- **[OmniRoute](https://github.com/igormorais123/omniroute)** — Gateway LLM inteligente (custo zero)

---

<div align="center">

**Fork mantido por [Igor Morais Vasconcelos](https://github.com/igormorais123)**

*[INTEIA](https://inteia.com.br) — Inteligência Artificial Estratégica*

</div>
