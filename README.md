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

> 🤖 **Agentes IA (Claude Code, Codex, Cursor, Copilot)**: leiam **[`CLAUDE.md`](CLAUDE.md)** e **[`AGENTS.md`](AGENTS.md)** antes de editar qualquer arquivo. Múltiplas instâncias trabalham em paralelo neste repositório — a coordenação está documentada lá.

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
| **Enriquecimento** | — | Apify (Google SERP + Instagram) para contexto factual |
| **QC do relatório** | — | Overlap upload×relatório (jaccard 5-gram, alerta >30%) + gate editorial por seção |
| **Gate de entrega** | — | Bloqueio estrutural de relatório sem simulação concluída, evidência local, diversidade mínima, trace OASIS com ação social real e auditoria de citações |
| **Auditoria numérica** | — | Percentuais, probabilidades e contagens precisam estar no corpus ou marcados como inferência calibrada |
| **Interface de gate** | — | Step 03 consulta qualidade sistêmica e bloqueia o botão de relatório quando o gate reprova |
| **Dinâmica social** | — | Pulso social inicial configurável no OASIS para gerar comentários, curtidas, rejeições, reposts e citações auditáveis |
| **Governança cliente/demo** | — | Modo `client` é estrito e publicável só com gate completo; `demo/smoke` fica sempre como `diagnostic_only` |
| **Anti-viés** | — | Devil's advocate em ~20% dos perfis + diversidade intra-grupo |
| **Helena cenários** | Análise narrativa | Tabela obrigatória de 3 cenários probabilísticos (Base/Otimista/Contrário, soma=100%) |
| **Testes** | — | Suite pytest com 70 testes em contratos críticos |

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
│   │   ├── services/          # Gerenciador de simulação, ontologia, LLM, Apify
│   │   └── utils/             # Cliente LLM, Graphiti, Zep
│   ├── scripts/               # Simulação paralela, proxy LLM, enrich_project
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

## Enriquecimento Apify

O Mirofish pode coletar fatos web e perfis sociais reais via [Apify](https://apify.com) antes de construir o grafo, aumentando a fidelidade dos agentes simulados.

### Via interface (Step 02)

O painel "Enriquecimento Apify" aparece antes da geração de perfis. Fontes disponíveis:
- **Buscas Google**: fatos web atualizados sobre o caso
- **Perfis Instagram**: bio, seguidores, categoria, verificação
- **Posts recentes Instagram**: legendas, curtidas, comentários, menções, hashtags
- **Tagged posts**: quem marcou os atores em publicações
- **Comentários YouTube**: opinião pública em vídeos relacionados
- **Extração automática**: checkbox que detecta @handles, queries e URLs do briefing

Os dados coletados são injetados no texto-base antes da construção do grafo. Cache em disco evita reprocessamento.

### Via API

```bash
POST /api/simulation/prepare
{
  "simulation_id": "sim_xxxx",
  "enrich_queries": ["reforma tributária PEC 45"],
  "enrich_actors": ["acmneto", "brunoreisba"],
  "enrich_ig_posts": ["acmneto"],
  "enrich_ig_tagged": ["acmneto"],
  "enrich_youtube": ["https://youtube.com/watch?v=..."],
  "enrich_auto": true
}
```

### Via CLI

```bash
cd backend
python scripts/enrich_project.py \
  --project-id <id> \
  --query "reforma tributária PEC 45" \
  --actor acmneto \
  --dry-run  # mostra bloco sem salvar
```

### Custo

| Operação | Custo aproximado |
|----------|-----------------|
| Google SERP (1 query, 8 resultados) | US$ 0,002 |
| Perfil Instagram (1 handle) | US$ 0,0015 |
| Posts Instagram (5 posts) | US$ 0,003 |
| Tagged posts (5 posts) | US$ 0,003 |
| Comentários YouTube (20 comentários) | US$ 0,005 |
| Enriquecimento completo (10 queries + 5 atores) | US$ 0,07 |

Requer conta Apify com token em `APIFY_TOKEN`. O Mirofish prossegue normalmente se o Apify falhar.

## Documentação

| Documento | Descrição |
|-----------|-----------|
| [PRD v2](PRD_MIROFISH_INTEIA_V2.md) | Requisitos do produto |
| [Backlog Técnico](BACKLOG_TECNICO_MIROFISH_INTEIA_V2.md) | Tasks técnicas pendentes |
| [Plano de Adaptação](PLANO_ADAPTACAO_MIROFISH_INTEIA_V2.md) | Roadmap do fork |
| [Estado Atual](.planning/STATE.md) | Status real da implementação, validações e pendências |
| [Roadmap Atual](.planning/ROADMAP.md) | Próximas fases após o gate estrutural |
| [Mapa de Documentação](.planning/DOCUMENTATION_MAP.md) | Onde ficam planos, mapas técnicos, memória e arquivos históricos |
| [Plano Consultoria Simulada](.planning/PLANO_IMPLEMENTACAO_CONSULTORIA_SIMULADA_INTEIA.md) | Implementação estrutural da promessa INTEIA de simular, verificar e entregar |
| [Mapas Técnicos](.planning/codebase/STRUCTURE.md) | Estrutura, arquitetura, integrações, testes e riscos do código |
| [Aprendizados Consultoria Auditável](.planning/LEARNINGS_CONSULTORIA_SIMULADA.md) | Aprendizados e decisões da fase v1.3 |
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
