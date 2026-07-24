# Centro de comando Helena

O plano de implementação e os critérios de aceite estão em
[`docs/superpowers/plans/2026-07-24-helena-control-plane-v2.md`](../superpowers/plans/2026-07-24-helena-control-plane-v2.md).

## Resultado

O MiroFish dispõe de uma caixa global para comandar a Helena em linguagem
natural sem substituir as cinco fases existentes. A caixa acompanha a rota
aberta, resolve os identificadores canônicos do projeto, da simulação e do
relatório e transforma o pedido em um plano estruturado antes de qualquer
execução.

O atalho `Alt+H` abre o painel. No celular, ele é exibido como uma folha inferior;
no desktop, como painel lateral flutuante.

## Fluxo operacional

1. O operador abre o painel e informa o mesmo `INTERNAL_API_TOKEN` configurado
   no backend. O token fica somente na memória da aba e é apagado ao bloquear,
   recarregar ou fechar a página.
2. A Helena recebe o pedido, a rota atual e os identificadores já presentes na
   tela.
3. O backend valida o contexto contra os dados persistidos e cria um plano
   composto exclusivamente por ferramentas permitidas.
4. Planos apenas de leitura podem ser executados diretamente. Planos que
   alteram o processo exibem impacto, etapas e exigem confirmação explícita
   com token de aprovação de uso único.
5. O navegador executa as APIs canônicas das fases e envia o resultado ao
   backend. Toda mudança de estado fica registrada em
   `backend/uploads/helena_commands/`.

## Ferramentas permitidas

| Ferramenta | Efeito | Aprovação |
|---|---|---|
| `inspect_context` | Lê o estado canônico do processo | Não |
| `navigate` | Abre uma fase existente | Não |
| `build_graph` | Constrói o grafo do projeto | Sim |
| `create_simulation` | Cria a simulação | Sim |
| `prepare_simulation` | Prepara ambiente e agentes | Sim |
| `start_simulation` | Inicia a execução | Sim |
| `stop_simulation` | Solicita parada | Sim |
| `generate_report` | Gera o relatório | Sim |
| `ask_analysis` | Envia pergunta à análise | Sim |
| `continue_analysis` | Retoma do estado atual até o relatório | Sim |
| `run_full_analysis` | Cria e conduz uma nova análise completa | Sim |

Não existem ferramentas para shell, escrita arbitrária em arquivos, chamadas
HTTP livres ou exclusão. Pedidos destrutivos e travessia de caminho são
rejeitados antes do planejamento.

## Controles de segurança

- autenticação interna obrigatória e comparação resistente a timing;
- falha fechada quando `INTERNAL_API_TOKEN` não está configurado;
- rate limit nos endpoints de planejamento e execução;
- allowlist de ferramentas validada novamente no backend;
- token de aprovação e ticket de execução com hash, expiração e uso único;
- bloqueio de comandos equivalentes já ativos;
- auditoria atômica em disco, com valores sensíveis removidos;
- prompt saneado e truncado no histórico; a impressão digital integral fica
  apenas no registro interno e nunca é retornada pela API;
- contexto informado pela interface tratado como dica: os vínculos
  projeto–simulação–relatório são revalidados no servidor;
- resultado e eventos passam por redação de segredos antes da persistência.

O centro de comando protege o fluxo da Helena. Ele não altera o modelo de
autorização dos endpoints históricos usados diretamente pelas telas do
MiroFish.

## Configuração

```env
INTERNAL_API_TOKEN=segredo-longo-e-aleatorio
HELENA_CONTROL_ENABLED=true
HELENA_COMMAND_MAX_LENGTH=4000
HELENA_PLAN_TTL_SECONDS=600
HELENA_APPROVAL_TTL_SECONDS=600
HELENA_EXECUTION_TTL_SECONDS=7200
HELENA_PLANNER_MODE=auto
```

`HELENA_PLANNER_MODE=auto` tenta o modelo definido em `LLM_HELENA_MODEL` e,
se o serviço estiver indisponível ou devolver plano inválido, usa o planejador
determinístico restrito. `rules` força esse modo restrito para homologação
local.

O endpoint público `GET /api/helena/status` informa somente disponibilidade e
limites. Os demais endpoints exigem `X-Internal-Token`; o segredo não é enviado
em query string nem armazenado no navegador.

## Limites operacionais

- `continue_analysis` acompanha tarefas no navegador; a aba deve permanecer
  aberta enquanto a sequência estiver em andamento.
- `run_full_analysis` usa o próprio comando como material textual inicial.
  Para análises apoiadas em documentos, o operador deve carregar as fontes na
  tela inicial e então pedir à Helena para continuar o processo existente.
- a Helena não aprova o próprio plano e não executa ações mutantes em segundo
  plano sem confirmação humana.
- planos prontos, aprovações e leases de execução têm expiração própria; uma
  consulta posterior reconcilia operações abandonadas como canceladas ou
  falhas, impedindo comandos zumbis.
- a mesma `Idempotency-Key` reapresenta o registro existente. Um comando
  equivalente com chave diferente é bloqueado enquanto houver operação ativa.
- uma preparação já em andamento é acompanhada em vez de reiniciada, e um
  relatório concluído é reutilizado por `continue_analysis`.

## Verificação

```powershell
cd backend
uv run pytest tests -q
uv run python -m compileall -q app
uv run pip-audit

cd ..\frontend
npm run test:helena
npm run build
npm audit --audit-level=high
```

A homologação visual deve cobrir desktop e viewport móvel nas rotas `/`,
`/process/:projectId`, `/simulation/:simulationId`,
`/simulation/:simulationId/start`, `/report/:reportId` e
`/interaction/:reportId`, incluindo bloqueio, autenticação, plano de leitura,
aprovação, cancelamento, histórico e ausência de overflow horizontal.
