# Documentation Map — MiroFish INTEIA

Atualizado em: 2026-05-04

## Como usar

Este mapa evita duplicacao e documento fora de lugar. Para retomadas futuras:

1. leia `README.md` para visao publica;
2. leia `.planning/STATE.md` para estado real;
3. leia `.planning/ROADMAP.md` para proximas fases;
4. leia `.planning/PLANO_IMPLEMENTACAO_CONSULTORIA_SIMULADA_INTEIA.md` para a implementacao da promessa INTEIA/Mirante;
5. leia `.planning/codebase/*` para mapas tecnicos.

## Raiz do projeto

| Arquivo | Papel | Status |
|---|---|---|
| `README.md` | Visao publica e operacao basica | Atualizado para v1.3 |
| `README-EN.md` | Versao historica em ingles | Legado; nao e fonte primaria |
| `PRD_MIROFISH_INTEIA_V2.md` | Requisitos originais do produto | Referencia |
| `BACKLOG_TECNICO_MIROFISH_INTEIA_V2.md` | Backlog tecnico anterior | Referencia historica |
| `PLANO_ADAPTACAO_MIROFISH_INTEIA_V2.md` | Plano original do fork INTEIA | Referencia historica |
| `MAPEAMENTO_PT-BR.md` | Mapa de traducao PT-BR | Referencia |
| `LENIA_MIROFISH_INTEGRACAO.md` | Ponte com sistema Lenia | Referencia |
| `RELATORIO_HELENA_EFESTO_MIROFISH.md` | Diagnostico Helena/Efesto de 2026-04-24 | Referencia estrategica |

## `.planning`

| Arquivo | Papel | Status |
|---|---|---|
| `PROJECT.md` | Visao atual, stack e milestone | Atualizado |
| `STATE.md` | Estado real pos-implementacao | Atualizado |
| `ROADMAP.md` | Proximas fases priorizadas | Atualizado |
| `DOCUMENTATION_MAP.md` | Este mapa | Novo |
| `PLANO_IMPLEMENTACAO_CONSULTORIA_SIMULADA_INTEIA.md` | Plano e registro da implementacao da consultoria por simulacao | Atualizado |
| `LEARNINGS_CONSULTORIA_SIMULADA.md` | Aprendizados e decisoes da fase v1.3 | Novo |
| `PLANO_CORRECAO_MIROFISH.md` | Diagnostico/correcao historica de pipeline | Historico |
| `SPRINT_2026-04.md` | Sprint anterior | Historico |
| `UPSTREAM_SYNC.md` | Sincronizacao com upstream | Referencia |

## `.planning/codebase`

| Arquivo | Papel | Status |
|---|---|---|
| `ARCHITECTURE.md` | Arquitetura e fluxo de dados | Atualizar quando mudar pipeline |
| `STRUCTURE.md` | Mapa de pastas e arquivos centrais | Atualizar quando criar modulos |
| `INTEGRATIONS.md` | Servicos externos e persistencia | Atualizar quando mudar APIs/env |
| `TESTING.md` | Como validar e lacunas de teste | Atualizar a cada mudanca de suite |
| `CONCERNS.md` | Riscos, dividas e areas frageis | Atualizar ao mitigar risco |
| `STACK.md` | Stack tecnologica | Atualizar ao mudar runtime/dependencias |
| `CONVENTIONS.md` | Convencoes locais | Referencia |

## Codigo central desta fase

- `backend/app/services/report_system_gate.py`: gate estrutural de relatorio.
- `backend/app/services/delivery_governance.py`: politica cliente vs demo/smoke.
- `backend/app/services/social_bootstrap.py`: pulso social inicial OASIS.
- `backend/app/services/report_agent.py`: status de entrega e artefatos do relatorio.

## `memory`

| Arquivo | Papel | Status |
|---|---|---|
| `MEMORY.md` | Indice de memorias persistentes | Atualizado |
| `project_apify_integration.md` | Integracao Apify | Referencia |
| `feedback_apify_costs.md` | Custos Apify | Referencia |
| `reference_omniroute_apify.md` | Ponte OmniRoute/Apify | Referencia |
| `decision_codex_oauth_5_5.md` | Decisao historica de modelo | Referencia |

## `_archive`

Arquivo morto de sprints, relatorios antigos e comparativos. Nao usar como fonte primaria para estado atual. Use apenas para auditoria historica ou recuperacao de contexto.

## Regras de limpeza

- Nao mover documentos historicos para fora de `_archive` sem motivo.
- Nao criar plano novo quando `STATE.md`, `ROADMAP.md` ou o plano consolidado puderem receber a atualizacao.
- Logs e caches locais nao sao documentacao; podem ser limpos se estiverem ignorados pelo Git.
- Relatorios gerados em `backend/uploads/reports` sao artefatos runtime; nao entram no mapa de documentacao do repositorio.
- Simulacoes em `backend/uploads/simulations` sao evidencias runtime; referenciar por `simulation_id`, nao copiar para docs.
