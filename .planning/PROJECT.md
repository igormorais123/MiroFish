# MiroFish INTEIA

Atualizado em: 2026-05-04

## Visao

Sistema de simulacao social multiagente para cenarios politicos, midiaticos, juridico-institucionais, reputacionais e de mercado. O produto combina grafo de conhecimento, perfis sinteticos, OASIS em Twitter/Reddit, enriquecimento factual e Helena Strategos para produzir relatorios de inteligencia com trilha de evidencia.

## Tese atual

O MiroFish INTEIA nao deve entregar "relatorio bonito" se a simulacao nao sustentou a conclusao. A promessa da consultoria por simulacao foi transformada em contrato operacional:

1. briefing e material-base obrigatorios;
2. grafo, perfis e configuracao persistidos;
3. simulacao OASIS concluida e auditavel;
4. diversidade minima semantica, comportamental e de agentes;
5. trace OASIS com interacao social real;
6. auditoria literal de citacoes diretas;
7. relatorio separado por fato, simulacao, inferencia e campo necessario.

## Stack

- **Frontend:** Vue.js 3 + Vite
- **Backend:** Flask/Python
- **Grafo/memoria:** Graphiti + Zep/Neo4j, com fallback local de evidencias
- **Simulacao:** OASIS multi-plataforma (Twitter + Reddit)
- **Relatorio:** ReportAgent + Helena Strategos + gate sistemico
- **LLM routing:** OmniRoute/OpenAI-compatible
- **Deploy:** Docker/nginx em VPS, com execucao local suportada

## Componentes criticos

- `backend/app/services/report_system_gate.py` — gate estrutural antes/depois do relatorio.
- `backend/app/utils/report_quality.py` — auditoria de citacoes e qualidade textual.
- `backend/app/services/simulation_data_reader.py` — metricas de diversidade e trace OASIS.
- `backend/app/services/social_bootstrap.py` — pulso social inicial deterministico.
- `backend/scripts/run_parallel_simulation.py` — execucao OASIS com interacoes persistidas.
- `frontend/src/components/Step3Simulation.vue` — bloqueio visual antes do relatorio.
- `frontend/src/components/Step4Report.vue` — cadeia de custodia do relatorio.

## Infraestrutura conhecida

- Frontend local validado: `http://localhost:5173`
- Backend local validado: `http://localhost:5001`
- VPS historico: `kvm4` / `72.62.108.24`
- Containers historicos: `mirofish-inteia`, `zep-graphiti`, `zep-neo4j`, `omniroute-inteia`

## Milestone atual

**v1.3 — Consultoria por Simulacao Auditavel**

Status: P0 estrutural implementado e validado localmente em 2026-05-04.

Proxima validacao de produto: executar uma simulacao nova, longa o suficiente, com LLM ativo, e verificar se atravessa o gate ate um relatorio publicavel.
