# Plano revisado — Centro de Comando Helena v2

**Data:** 2026-07-24

**Estado:** implementado; aguardando regressão final e integração por PR

**Objetivo:** permitir que Helena coordene todas as fases do MiroFish a partir
de uma caixa global, com contexto completo do processo, sem acesso arbitrário
ao host e sem duplicar operações já em andamento.

## 1. Definição de concluído

A funcionalidade só está concluída quando:

1. a caixa Helena aparece nas seis rotas do produto em desktop e mobile;
2. o operador autentica sem persistir o segredo no navegador;
3. todo pedido vira plano visível antes da execução;
4. somente ferramentas da allowlist podem chegar ao executor;
5. ações mutantes exigem aprovação humana de uso único;
6. contexto, IDs e transições são revalidados no backend;
7. preparação, simulação e relatório existentes são retomados sem duplicação;
8. comandos, aprovações e leases abandonados chegam a estado terminal;
9. conclusão, falha e cancelamento ficam separados na auditoria;
10. testes de backend, frontend, build, dependências, rotas e visualização
    sustentam cada afirmação acima.

## 2. Arquitetura escolhida

O centro é um plano de controle, não um novo motor de análise:

```text
Operador
  → caixa Vue global
  → API Helena autenticada
  → planejador LLM ou regras restritas
  → validador de contexto, estado e allowlist
  → aprovação/ticket de uso único
  → executor das APIs canônicas
  → serviços existentes das cinco fases
  → recibo saneado e auditoria atômica
```

Essa divisão preserva as telas e APIs existentes. Helena coordena o fluxo, mas
não ganha shell, escrita livre em arquivos, endpoint arbitrário nem capacidade
de excluir dados.

## 3. Ferramentas e política

As ferramentas são agrupadas por efeito:

- **Leitura:** `inspect_context`, `navigate`.
- **Mutação de fase:** `build_graph`, `create_simulation`,
  `prepare_simulation`, `start_simulation`, `stop_simulation`,
  `generate_report`.
- **Análise assistida:** `ask_analysis`.
- **Macros controladas:** `continue_analysis`, `run_full_analysis`.

O backend calcula risco e aprovação; o modelo não pode reduzi-los. Uma macro
substitui ações menores redundantes no mesmo plano. Parada é exclusiva e não
pode coexistir com início ou continuação.

## 4. Regras de transição

| Ação | Pré-condição verificada |
|---|---|
| Construir grafo | projeto em `ontology_generated` |
| Criar simulação | projeto em `graph_completed` e sem simulação vinculada |
| Preparar | simulação em `created` ou `failed` |
| Iniciar | simulação em `ready` ou `paused` |
| Parar | simulação em `running` |
| Gerar relatório | simulação `completed`/`stopped` e sem relatório concluído |
| Interagir | relatório `completed` |
| Continuar | projeto e grafo canônicos disponíveis |
| Nova análise completa | briefing textual não vazio |

Uma transição impossível falha antes de emitir aprovação. A resposta da API
subjacente continua sendo a autoridade final.

## 5. Redundância e recuperação

- Uma `Idempotency-Key` repetida retorna o mesmo comando.
- Mesmo prompt no mesmo escopo, com chave diferente, é bloqueado enquanto o
  comando anterior estiver ativo.
- Planos prontos e aprovações expiram.
- Execuções sem recibo final viram falha quando o lease expira.
- Preparação em estado `preparing` é acompanhada por polling, sem novo POST.
- Simulação em `running` é acompanhada até terminar, sem novo start.
- Relatório já concluído é reutilizado por `continue_analysis`.
- O endpoint de relatório mantém seu próprio bloqueio de regeneração.

## 6. Segurança e privacidade

- `INTERNAL_API_TOKEN` é obrigatório e comparado em tempo constante.
- O token fica em `ref` de memória e é apagado no bloqueio, reload e unmount.
- Segredos são removidos de prompt, resultado e erro antes da persistência.
- Hashes de token, ticket, idempotência e prompt nunca saem na API pública.
- IDs passam por validação de armazenamento e vínculos são derivados da fonte.
- Payload, comando, número de ações, parâmetros e taxas têm limites.
- Pedidos destrutivos são recusados; não há fallback destrutivo.

## 7. Experiência operacional

- `Alt+H` abre e fecha a caixa.
- A faixa de contexto mostra fase e artefato canônico.
- O plano informa resumo, justificativa, risco, sequência e efeito de cada ação.
- Alto impacto usa confirmação explícita.
- Progresso e últimos eventos ficam visíveis durante a execução.
- Histórico diferencia `pending_approval`, `ready`, `executing`, `completed`,
  `failed` e `cancelled`.
- O layout usa painel lateral no desktop e bottom sheet no celular, sem
  interferir na navegação das fases.

## 8. Fases de implantação

### Fase A — contrato e proteção

Entregar autenticação compartilhada, status saneado, allowlist, contexto
canônico, aprovação/ticket, limites e armazenamento atômico.

**Gate:** testes de falha fechada, prompt injection, travessia, segredo,
uso único, expiração e idempotência.

### Fase B — integração das cinco fases

Conectar as ferramentas às APIs já usadas pelas telas e implementar
continuação orientada pelo estado.

**Gate:** testes do executor para ordem, polling, falha, retomada e bloqueio de
ferramenta desconhecida.

### Fase C — interface global

Montar o componente no `App.vue`, preservar responsividade e oferecer plano,
aprovação, progresso, cancelamento e histórico.

**Gate:** build de produção e inspeção real nas seis rotas em desktop e mobile.

### Fase D — observabilidade e documentação

Publicar contrato operacional, mapa Graphify, diagrama Archify e roteiro de
homologação.

**Gate:** mapa sem segredos/caches; diagrama sem erros, sobreposições ou
cruzamentos; documentação consistente com configuração e código.

### Fase E — rollout

Integrar por PR, executar CI, fazer deploy pelo fluxo existente e homologar com
token de produção sem registrar o segredo.

**Gate:** status disponível, uma leitura real, um cancelamento de alto impacto
e uma execução controlada em escopo de homologação.

## 9. Matriz de evidência

| Requisito | Evidência autoritativa |
|---|---|
| Segurança do backend | `backend/tests/test_helena_control_api.py` |
| Orquestração sem duplicação | `frontend/tests/helenaExecutor.test.js` |
| Integração visual | inspeção das seis rotas, desktop e mobile |
| Compilação | `npm run build` |
| Regressão | suite pytest completa |
| Dependências | `npm audit` e `pip-audit` |
| Estrutura | `graphify-out/graph.json` e `GRAPH_REPORT.md` |
| Arquitetura | IR e HTML validados pelo Archify |
| Operação | `docs/ops/HELENA_CONTROL_PLANE.md` |

## 10. Limites assumidos

- O centro autentica a camada Helena; não redesenha a autorização histórica de
  todas as APIs públicas do MiroFish.
- Processos longos acompanhados pelo executor local exigem a aba aberta.
  `run_full_analysis` permanece como alternativa assíncrona no servidor.
- O comando de nova análise é briefing textual. Fontes documentais devem ser
  carregadas pela tela inicial antes de usar `continue_analysis`.
- Deploy e merge seguem o fluxo de PR do repositório; não há patch direto em
  produção.
