# Mapa de documentação — MiroFish INTEIA

Atualizado em: 2026-07-24

## Ordem de leitura

1. `README.md` — produto e operação básica.
2. `CLAUDE.md` / `AGENTS.md` — regras de trabalho.
3. `.planning/STATE.md` — estado efetivo e pendências.
4. `docs/ops/FONTE_UNICA_VERDADE_MIROFISH.md` — produção canônica.
5. `docs/ops/HELENA_CONTROL_PLANE.md` — contrato do centro de comando.
6. `.planning/ROADMAP.md` — próximos marcos.
7. mapas estruturais e documentos de código abaixo.

## Fontes operacionais

| Documento | Papel | Estado |
|---|---|---|
| `docs/ops/FONTE_UNICA_VERDADE_MIROFISH.md` | URLs, VPS, checkout e regra de publicação | Canônico |
| `docs/ops/COMANDOS_SEGUROS_MIROFISH.md` | validação, backup, deploy e smoke | Canônico |
| `docs/ops/SEGREDOS_E_AMBIENTES_MIROFISH.md` | nomes, cofres e fronteiras de segredo | Canônico |
| `docs/ops/HELENA_CONTROL_PLANE.md` | ferramentas, autorização, auditoria e limites | Atual |
| `docs/ops/PUBLICACAO_HELENA_2026-07-24.md` | commit, imagem, backup, testes e rollback | Registro imutável |
| `docs/ops/VERCEL_DEPLOY.md` | alternativa estática sem domínio canônico | Histórico/alternativo |
| `docs/ops/PUBLICACAO_VPS_2026-07-15.md` | cutover do domínio para a VPS | Registro histórico |

## Estado e planejamento

| Documento | Papel |
|---|---|
| `.planning/PROJECT.md` | visão, stack, componentes e infraestrutura |
| `.planning/STATE.md` | estado vivo, evidências e pendências |
| `.planning/ROADMAP.md` | marcos concluídos e próximos |
| `.planning/PLANO_IMPLEMENTACAO_CONSULTORIA_SIMULADA_INTEIA.md` | contrato da consultoria auditável |
| `docs/superpowers/plans/2026-07-24-helena-control-plane-v2.md` | plano implementado da Helena |

## Mapas vivos

| Artefato | Origem | Uso |
|---|---|---|
| `.planning/architecture/system.architecture.json` | Archify, fonte editável | topologia completa |
| `.planning/architecture/system-architecture.html` | Archify, gerado | inspeção visual do sistema |
| `.planning/architecture/helena-control-plane.architecture.json` | Archify, fonte editável | control plane detalhado |
| `.planning/architecture/helena-control-plane.html` | Archify, gerado | inspeção visual da Helena |
| `graphify-out/graph.json` | Graphify, gerado | grafo estrutural serializado |
| `graphify-out/graph.html` | Graphify, gerado | navegação interativa |
| `graphify-out/GRAPH_REPORT.md` | Graphify, gerado | inventário e métricas do grafo |

Não edite manualmente os arquivos gerados por Graphify ou os HTMLs do Archify.
Atualize as fontes e execute novamente as ferramentas.

## Mapas técnicos de código

| Documento | Escopo |
|---|---|
| `.planning/codebase/ARCHITECTURE.md` | camadas, fluxos e autenticação |
| `.planning/codebase/STRUCTURE.md` | pastas e arquivos centrais |
| `.planning/codebase/INTEGRATIONS.md` | serviços, deploy e variáveis |
| `.planning/codebase/TESTING.md` | suítes, comandos e lacunas |
| `.planning/codebase/CONCERNS.md` | riscos e dívida técnica |
| `.planning/codebase/STACK.md` | runtimes, dependências e ferramentas |
| `.planning/codebase/CONVENTIONS.md` | convenções locais |

## Histórico

Documentos com data anterior preservam decisões e evidências do momento em que
foram escritos. Quando contradisserem `STATE.md` ou a fonte operacional, trate-os
como históricos. `_archive/`, runtime em `backend/uploads/`, logs, caches,
backups e builds não fazem parte da documentação versionada.
