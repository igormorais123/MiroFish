# Rollout Inteligencia Sistemica Mirofish

Data: 2026-05-07
Responsavel desta atualizacao: Codex

## Objetivo

Fechar a rodada Ralph/OpenSwarm/AutoResearch aplicada ao Mirofish sem importar runtime externo, mantendo GitHub como fonte de verdade e Codex trabalhando somente em branches `codex/*`.

Esta rodada transforma inteligencia interna ja existente em experiencia de produto:

- readiness e proxima acao no Step 3;
- checklist metodologico e reparo de finalizacao;
- exportacao verificada;
- pacote executivo auditavel;
- previsoes/calibracao visiveis no Step 4;
- AutoResearch/Ralph como metodo interno, nao UI de usuario.

## Cadeia de PRs

Merge deve seguir esta ordem, porque os PRs estao empilhados:

| Ordem | PR | Branch | Base | Conteudo principal | Validacao local |
| --- | --- | --- | --- | --- | --- |
| 1 | #25 | `codex/pr2-method-checklist-repair-main` | `main` | checklist metodologico e reparo de finalizacao | backend 213, frontend build |
| 2 | #26 | `codex/pr3-verified-bundle-export` | #25 | export HTML verificado com manifesto/hash | backend 231, frontend build |
| 3 | #27 | `codex/pr4-autoresearch-ralph-method` | #26 | AutoResearch targets e `.ralph/SWARM.md` | backend 235, frontend build, baselines 1.0000 |
| 4 | #28 | `codex/pr5-forecast-calibration-ledger` | #27 | forecast ledger com Brier/log-loss/chart data | backend 238, frontend build |
| 5 | #29 | `codex/pr6-forecast-artifact-enrichment` | #28 | enriquecimento de `forecast_ledger.json` no report/bundle | backend 238, frontend build |
| 6 | #30 | `codex/pr7-forecast-calibration-ux` | #29 | painel de calibracao de previsoes no Step 4 | backend 238, frontend build |
| 7 | #31 | `codex/pr8-step3-readiness-contract` | #30 | Step 3 alinhado ao contrato real de readiness | backend 238, frontend build |
| 8 | #32 | `codex/pr9-executive-package-service` | #31 | servico/API de pacote executivo auditavel | backend 244, frontend build |
| 9 | #33 | `codex/pr10-executive-package-step4` | #32 | acionamento do pacote executivo no Step 4 | backend 244, frontend build |
| 10 | #34 | `codex/pr11-executive-package-downloads` | #33 | downloads allowlisted do pacote executivo | backend 248, frontend build |
| 11 | #35 | `codex/pr12-systemic-rollout-closeout` | #34 | este fechamento operacional | docs/diff |

Todos os PRs de #25 a #34 estavam `MERGEABLE` e com Vercel green quando verificados nesta sessao.

## O que foi incorporado

### Ralph Loop

Incorporado como disciplina de trabalho:

- uma unidade pequena por PR;
- validacao objetiva antes do PR;
- branch `codex/*`;
- registro claro de resultado e proxima acao.

Nao foi incorporado como runtime de produto.

### OpenSwarm

Incorporado como padrao de handoff e especializacao leve:

- `.ralph/SWARM.md`;
- lanes internas;
- pacote executivo como entregavel composto;
- handoff limpo entre artefatos: relatorio, evidencia, previsao, export, manifesto.

Nao foi importado o runtime OpenSwarm, nem dependencia de agentes externos.

### AutoResearch

Incorporado como avaliador interno de metodo:

- target `report_delivery`;
- target `ralph`;
- baseline sem LLM para medir qualidade de entrega/metodo.

Nao aplica patch de producao automaticamente.

### Helena/Vox/Efesto

Foram usados como referencia de arquitetura, rubrica e disciplina de pacote, sem copiar chaves, sessoes, interacoes privadas ou acoplamento de infraestrutura.

## Estado de produto apos merge da pilha

### Step 3

O usuario passa a receber uma leitura de prontidao alinhada ao backend:

- pronto para relatorio;
- ajuste necessario;
- relatorio em andamento;
- execucao diagnostica;
- pronto para pacote executivo.

O botao de relatorio continua bloqueado pelo gate estrutural existente.

### Step 4

O usuario passa a ver:

- cadeia de custodia;
- valor da missao;
- previsoes e calibracao;
- pacote final da missao;
- exportacao verificada;
- pacote executivo auditavel;
- downloads do resumo, anexo e manifesto.

Termos internos como Ralph, Swarm, AutoResearch, lane e handoff nao aparecem na UI normal.

## Controles de seguranca

- Pacote executivo exige `Report.delivery_status() == "publishable"`.
- Relatorio diagnostico ou bloqueado nao gera pacote executivo.
- Downloads do pacote executivo usam allowlist do manifesto.
- `internal_path` nao e exposto no manifesto publico.
- Export verificado continua separado do pacote executivo.
- Nenhum segredo, `.env`, `.vercel`, `dist`, upload ou log vivo foi versionado.

## Ordem segura de merge

Atualizacao de fechamento: o PR #25 foi mergeado primeiro em `main`. Depois disso, as revisoes automatizadas abriram conversas tecnicas nos PRs empilhados #26 a #36. Para nao levar bugs conhecidos em cadeia nem depender de varias branches `BEHIND`, o restante da pilha deve ser consolidado em um PR unico final criado a partir da `main` atualizada.

Ordem final recomendada:

1. #25 ja mergeado em `main`.
2. Mergear o PR consolidado final `codex/final-systemic-intelligence-stack`.
3. Fechar #26 a #36 como substituidos pelo PR consolidado, se ainda estiverem abertos.
4. Aguardar Vercel production apos o merge do consolidado.
5. Executar a validacao pos-merge descrita abaixo.

Historico original da pilha:

1. Confirmar que `main` esta atualizado e sem incidentes.
2. Conferir checks de #25.
3. Mergear #25.
4. Atualizar base/revalidar #26 se o GitHub pedir.
5. Repetir a ordem ate #35.
6. Apos cada merge em `main`, aguardar Vercel production.
7. Se algum PR ficar com conflito, resolver no PR da vez; nao pular a cadeia.

## Validacao recomendada apos merge final

Backend:

```powershell
python -m pytest backend\tests -q
```

Frontend:

```powershell
cd frontend
npm run build
```

UX manual:

- rodar uma simulacao concluida;
- verificar Step 3 com readiness;
- gerar relatorio;
- confirmar que relatorio diagnostico nao habilita pacote executivo;
- em relatorio publicavel, gerar pacote executivo;
- baixar Resumo, Anexo e Manifesto;
- conferir que os arquivos abrem localmente.

## Pendencias fora desta rodada

- PDF/DOCX real a partir do pacote executivo.
- QA visual automatizado por screenshot.
- Deck executivo curto.
- Historico de pacotes executivos por versao.
- Experimentos AutoResearch apos 3 a 5 runs comparaveis.

Essas pendencias devem virar PRs separados, nao ser acopladas ao merge desta pilha.

