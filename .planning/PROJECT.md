# MiroFish INTEIA

Atualizado em: 2026-07-24

## Visão

Sistema de simulação social multiagente para cenários políticos, midiáticos,
jurídico-institucionais, reputacionais e de mercado. Combina grafo de
conhecimento, perfis sintéticos, OASIS, enriquecimento factual, gate de
evidência e Helena Strategos para produzir análises com cadeia de custódia.

## Tese atual

O produto não entrega relatório publicável se a simulação e as fontes não
sustentarem a conclusão. O contrato operacional exige material-base, grafo,
configuração, perfis, simulação concluída, diversidade mínima, trace social,
auditoria de citações e separação entre fato, simulação e inferência.

O centro de comando Helena coordena esse processo por linguagem natural sem
substituir as cinco fases, sem acesso a shell ou HTTP livre e sem aprovar as
próprias ações mutantes.

## Stack

- **Frontend:** Vue 3 + Vite.
- **Backend:** Flask/Python.
- **Grafo e memória de domínio:** Graphiti + Neo4j/Zep.
- **Simulação:** OASIS em Twitter e Reddit.
- **Relatório:** ReportAgent + Helena Strategos + gate sistêmico.
- **LLM routing:** OmniRoute/OpenAI-compatible.
- **Produção:** Docker Compose + nginx na VPS `hermes`.
- **Mapas do repositório:** Graphify e Archify.

## Componentes críticos

- `frontend/src/components/HelenaCommandCenter.vue` — caixa global e aprovação.
- `frontend/src/services/helenaExecutor.js` — execução das APIs canônicas.
- `backend/app/api/helena.py` — contrato HTTP do control plane.
- `backend/app/services/helena_control.py` — plano, leases e auditoria.
- `backend/app/utils/internal_auth.py` — autenticação fail-closed.
- `backend/app/services/report_system_gate.py` — gate estrutural de relatório.
- `backend/app/utils/report_quality.py` — auditoria textual e numérica.
- `backend/app/services/simulation_data_reader.py` — diversidade e trace OASIS.

## Infraestrutura canônica

- Público: `https://inteia.com.br/mirofish/`.
- API: `https://inteia.com.br/mirofish/api/...`.
- VPS: `hermes`, checkout `/opt/mirofish-git`.
- Container: `mirofish-inteia`.
- Serviços internos: `mirofish-graphiti`, `mirofish-neo4j`,
  `omniroute-inteia`.
- Vercel: alternativa histórica, sem autoridade sobre o domínio público.

## Milestone atual

**v1.4 — Coordenação segura pela Helena**

Status: centro de comando publicado em produção em 2026-07-24 pelo PR `#99`,
commit `07306e711509772038b381176781ce80edacdfa0`. Testes automatizados,
contratos públicos, seis rotas em desktop/móvel, health, backup e rollback
foram validados. A próxima validação de produto continua sendo uma simulação
cliente longa com fontes reais e LLM ativo até um relatório publicável.
