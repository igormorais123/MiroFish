# Publicação do centro de comando Helena — 2026-07-24

Este registro consolida a implementação, a publicação e a homologação do centro
de comando Helena no MiroFish INTEIA. Ele complementa, sem substituir:

- [`FONTE_UNICA_VERDADE_MIROFISH.md`](FONTE_UNICA_VERDADE_MIROFISH.md);
- [`HELENA_CONTROL_PLANE.md`](HELENA_CONTROL_PLANE.md);
- [`COMANDOS_SEGUROS_MIROFISH.md`](COMANDOS_SEGUROS_MIROFISH.md);
- [mapa sistêmico Archify](../../.planning/architecture/system-architecture.html);
- [mapa específico da Helena](../../.planning/architecture/helena-control-plane.html).

## Identidade da publicação

| Campo | Valor verificado |
|---|---|
| Repositório | `igormorais123/MiroFish` |
| Pull request | [#99](https://github.com/igormorais123/MiroFish/pull/99) |
| Commit em `main` | `07306e711509772038b381176781ce80edacdfa0` |
| URL pública | `https://inteia.com.br/mirofish/` |
| Health público | `https://inteia.com.br/mirofish/health/public` |
| Status público Helena | `https://inteia.com.br/mirofish/api/helena/status` |
| Deploy da VPS | `/opt/mirofish-git` |
| Container | `mirofish-inteia` |
| Imagem publicada | `sha256:b7d6b8f552ce28c90613511a2cf7948130a3cd66f2a9464aeb328d152c27a497` |
| Backup pré-corte | `/opt/backups/mirofish-helena/20260724T072013Z` |
| Imagem de rollback | `mirofish-inteia:rollback-20260724T072013Z` |

Recorte observado em 2026-07-24:

- `origin/main` e `/opt/mirofish-git` apontavam para o mesmo commit;
- container `running/healthy`, `RestartCount=0`;
- health público `status=ok`;
- Helena `available=true`, versão `1.0`;
- nenhum erro recente compatível com traceback, fatal, panic ou resposta 5xx nos
  logs do container.

## Resultado funcional

A caixa da Helena está montada globalmente em `frontend/src/App.vue` e acompanha
as seis superfícies do fluxo:

1. `/`;
2. `/process/:projectId`;
3. `/simulation/:simulationId`;
4. `/simulation/:simulationId/start`;
5. `/report/:reportId`;
6. `/interaction/:reportId`.

O operador pode abrir o painel pelo botão flutuante ou por `Alt+H`. O painel:

- resolve a rota e os IDs atuais;
- pede ao backend um plano estruturado;
- mostra impacto e etapas antes de executar;
- exige confirmação para qualquer ação mutante;
- executa somente as APIs já existentes das fases;
- registra o resultado sem guardar o token no armazenamento do navegador.

No desktop, a interface usa painel lateral. Em viewport móvel, usa folha
inferior contida na largura da tela.

## Componentes implementados

| Superfície | Arquivo principal | Responsabilidade |
|---|---|---|
| UI global | `frontend/src/components/HelenaCommandCenter.vue` | autenticação, comando, plano, confirmação, histórico e progresso |
| Cliente de controle | `frontend/src/api/helena.js` | chamadas autenticadas ao contrato `/api/helena/*` |
| Executor | `frontend/src/services/helenaExecutor.js` | tradução da allowlist para APIs canônicas |
| Dependências | `frontend/src/services/helenaDependencies.js` | adaptadores para os clientes de projeto, simulação e relatório |
| Blueprint Flask | `backend/app/api/helena.py` | sessão, contexto, plano, execução, conclusão, cancelamento e consulta |
| Domínio de controle | `backend/app/services/helena_control.py` | contexto canônico, políticas, TTL, idempotência, leases e auditoria |
| Autenticação | `backend/app/utils/internal_auth.py` | validação fail-closed do token interno |
| Configuração | `backend/app/config.py` | limites e parâmetros do plano de controle |

## Contrato HTTP

`GET /api/helena/status` é público e sanitizado. Os demais endpoints exigem
`X-Internal-Token`.

| Método e rota | Papel | Mutação do processo |
|---|---|---:|
| `GET /api/helena/status` | disponibilidade e versão | Não |
| `POST /api/helena/session` | valida token e abre capacidades | Não |
| `POST /api/helena/context` | resolve contexto persistido | Não |
| `POST /api/helena/commands/plan` | cria plano restrito | Não |
| `POST /api/helena/commands/:id/execute` | emite ticket e inicia lease | Sim |
| `POST /api/helena/commands/:id/complete` | conclui execução com evidência | Sim |
| `POST /api/helena/commands/:id/cancel` | cancela plano não concluído | Sim |
| `GET /api/helena/commands/:id` | consulta registro | Não |
| `GET /api/helena/commands` | lista histórico saneado | Não |

## Modelo de segurança

O centro de comando não entrega acesso completo ao host. “Acesso completo”,
neste contexto, significa capacidade de coordenar todo o fluxo funcional do
MiroFish por uma lista fechada de ferramentas.

Controles ativos:

- autenticação interna com comparação resistente a timing;
- indisponibilidade fail-closed se `INTERNAL_API_TOKEN` estiver ausente;
- allowlist revalidada pelo backend;
- comandos destrutivos, shell, arquivo arbitrário e HTTP livre inexistentes;
- rate limit nos endpoints do plano de controle;
- token de aprovação e ticket de execução de uso único;
- TTL independente para plano, aprovação e execução;
- idempotência por chave e bloqueio de comando equivalente ativo;
- reconciliação de leases abandonados;
- validação dos vínculos projeto–simulação–relatório no backend;
- gravação atômica em `backend/uploads/helena_commands/`;
- redação de segredos, prompt e resultados antes da resposta/persistência.

## Homologação executada

### Regressão local

- backend completo: `390 passed`;
- backend focado da Helena: `15 passed`;
- executor frontend da Helena: `8 passed`;
- `python -m compileall -q app`: aprovado;
- build Vite: aprovado;
- `npm audit`: zero vulnerabilidades;
- `pip-audit`: nenhuma vulnerabilidade conhecida.

### Produção

- página pública, health, histórico de simulação e status Helena responderam
  `200`;
- requisição de sessão sem token respondeu `401`;
- sessão autenticada pelo domínio público respondeu `200`;
- comando de leitura `inspect_context` percorreu plano → execução → conclusão;
- repetição com a mesma `Idempotency-Key` retornou o registro existente;
- plano `run_full_analysis` foi classificado como mutante e exigiu aprovação;
- cancelamento manteve estado distinto de conclusão;
- as seis rotas exibiram um único acionador global da Helena;
- desktop e mobile ficaram sem overflow horizontal;
- console do navegador não registrou erros na homologação;
- container permaneceu saudável e com zero reinicializações.

### CI externo

O workflow do GitHub encerrou antes de iniciar qualquer passo e não disponibilizou
log de job. Por isso, não foi usado como evidência de teste. A decisão de publicar
foi baseada na regressão local completa e nos smokes de produção acima.

## Procedimento de atualização

O caminho normal continua sendo:

1. branch isolada;
2. testes locais;
3. PR para `main`;
4. backup do runtime;
5. `git pull --ff-only origin main` em `/opt/mirofish-git`;
6. build da imagem sem interromper o container atual;
7. `docker compose ... up -d --no-deps mirofish`;
8. health, autenticação, smoke somente leitura e validação visual.

Os comandos completos e os gates de rollback ficam em
[`COMANDOS_SEGUROS_MIROFISH.md`](COMANDOS_SEGUROS_MIROFISH.md).

## Rollback

Se uma regressão futura exigir reversão:

1. registrar o commit/imagem que falhou;
2. restaurar a imagem `mirofish-inteia:rollback-20260724T072013Z`;
3. restaurar `.env`, Nginx ou uploads somente quando o incidente envolver esses
   ativos;
4. validar checksums em
   `/opt/backups/mirofish-helena/20260724T072013Z/SHA256SUMS`;
5. confirmar health, portas locais, domínio público, API e logs;
6. abrir PR de correção no GitHub.

O backup é privado e contém ambiente operacional. Seu conteúdo não deve ser
copiado para issue, PR, log público ou repositório.

## Evidência e limites

- `[FATO VERIFICADO]` Identidades de commit, imagem, health e container foram
  reconfirmadas em 2026-07-24.
- `[FATO VERIFICADO]` O backup passou em `sha256sum -c`.
- `[FATO VERIFICADO]` O teste visual cobriu as seis rotas e viewport móvel.
- `[LIMITE]` A Helena não substitui autorização humana para ações mutantes.
- `[LIMITE]` `continue_analysis` depende da aba aberta para acompanhar o fluxo.
- `[LIMITE]` O token interno não deve ser exposto ao bundle, documentação ou
  armazenamento persistente do navegador.
