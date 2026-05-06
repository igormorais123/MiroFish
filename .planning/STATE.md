# STATE — MiroFish INTEIA

Atualizado em: 2026-05-04

## Current

- **Milestone:** v1.3 — Consultoria por Simulacao Auditavel
- **Status:** P0 estrutural implementado e validado localmente.
- **Validacao:** `python -m pytest backend\tests` com 76 testes aprovados; `npm run build` aprovado; `git diff --check` sem erro de whitespace.
- **Servidores locais verificados:** backend `http://localhost:5001/health` e frontend `http://localhost:5173` responderam 200.

## O que mudou nesta fase

1. Relatorio deixou de ser apenas geracao textual e passou a depender de gate sistemico.
2. O backend bloqueia relatorio sem simulacao concluida, material-base, grafo, config, perfis, run_state, diversidade minima, trace OASIS e auditoria de citacoes.
3. A interface da etapa 3 consulta a qualidade da simulacao e bloqueia a geracao quando o sistema reprova.
4. A interface da etapa 4 exibe cadeia de custodia, artefatos e motivos de bloqueio.
5. Relatorios antigos sem `quality_gate` e `evidence_audit` sao classificados como `legacy_unverified`, nao publicaveis.
6. O runner OASIS ganhou pulso social inicial configuravel, com comentarios, curtidas, rejeicoes, reposts e citacoes persistidas.
7. Perfis OASIS ganharam contrato comportamental para atuar como participantes sociais, nao apenas observadores.
8. O sistema separa modo `client` de `demo/smoke`: diagnostico tecnico pode rodar, mas nunca recebe status publicavel.
9. Auditoria de evidencias passou a cobrir numeros: percentuais, probabilidades e contagens precisam estar no corpus ou marcados como inferencia/simulacao/calibracao.

## Novos arquivos principais

- `.planning/PLANO_IMPLEMENTACAO_CONSULTORIA_SIMULADA_INTEIA.md`
- `.planning/DOCUMENTATION_MAP.md`
- `backend/app/services/report_system_gate.py`
- `backend/app/services/delivery_governance.py`
- `backend/app/services/social_bootstrap.py`
- `backend/tests/test_delivery_governance.py`
- `backend/tests/test_report_manager_artifacts.py`
- `backend/tests/test_report_quality.py`
- `backend/tests/test_simulation_data_reader.py`
- `backend/tests/test_simulation_manager.py`
- `backend/tests/test_social_bootstrap.py`

## Decisoes registradas

- Um relatorio cliente so pode ser `publishable` se passar gate estrutural e auditoria de evidencia.
- Citacao direta precisa existir literalmente no corpus local; traducao ou parafrase deve ser marcada como inferencia/simulacao.
- Volume de acoes nao basta: Distinct-2, entropia de agentes, entropia de tipos de acao e trace OASIS entram como criterio.
- Simulacao antiga sem gate deve ser tratada como legado tecnico, nao entrega cliente.
- Smoke/demo existe como diagnostico tecnico, separado de modo cliente e bloqueado como `diagnostic_only`.
- Numero em relatorio cliente e claim auditavel; se nao aparece no corpus local, precisa estar rotulado como inferencia calibrada ou o relatorio e bloqueado.

## Pendencias reais

1. Rodar uma nova simulacao real longa com LLM ativo e verificar se atravessa o gate ate relatorio publicavel.
2. Criar preset de baixa atividade que gere diagnostico tecnico sem fingir opiniao publica.
5. Continuar testes de API e frontend, hoje ainda sem suite automatizada de componentes.

## Historico relevante

- v1.0: sistema funcional.
- v1.1: relatorio premium, graph_id, API de custos.
- v1.2: correcoes de pipeline, PT-BR, seguranca basica, persistencia e QC inicial.
- v1.3: gate estrutural, governanca cliente/demo, auditoria de evidencias/citacoes/numeros, diversidade social, cadeia de custodia e pulso OASIS.
