# MiroFish INTEIA

## Visao
Sistema de simulacao social com agentes sinteticos para previsao de cenarios politicos, midiaticos e eleitorais. Combina GraphRAG + OASIS simulation engine + LLM analysis para gerar relatorios de inteligencia.

## Stack
- **Frontend**: Vue.js 3 + Vite
- **Backend**: Flask (Python 3.12)
- **GraphRAG**: Graphiti + Neo4j + Zep
- **Simulacao**: OASIS engine (multi-platform: Twitter/Reddit)
- **LLM Routing**: OmniRoute (Claude Opus 4.6, Sonnet 4.6, DeepSeek, GPT-5.4)
- **Deploy**: Docker containers em VPS KVM4 (72.62.108.24)

## Infraestrutura
- Container `mirofish-inteia`: nginx (porta 3001) + Flask (porta 5001)
- Container `zep-graphiti`: Graphiti API (porta 8003)
- Container `zep-neo4j`: Neo4j graph DB
- Container `omniroute-inteia`: LLM router (porta 20128)

## Acesso
- Frontend: http://72.62.108.24:3001
- Backend API: http://72.62.108.24:5001
- SSH: `ssh kvm4`

## Configuracao de Modelos (Qualidade)
- LLM_PREMIUM_MODEL: claude/claude-sonnet-4-6 (relatorios)
- LLM_HELENA_MODEL: claude/claude-opus-4-6 (analise estrategica)
- LLM_AGENT_MODEL: mirofish-smart (simulacao)
- LLM_MODEL_NAME: BestFREE (volume alto / grafos)

## Milestone Atual
v1.1 — Relatorio Premium + Melhorias de Qualidade
