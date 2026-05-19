# STATE — MiroFish INTEIA

Atualizado em: 2026-05-19

## Current

- **Milestone:** v1.3 — Consultoria por Simulação Auditável
- **Status:** P0 + Fase 03 (Vox Academic Hardening) implementados e validados localmente.
- **Servidores locais verificados:** backend `http://127.0.0.1:5001/health` 200 e frontend `http://127.0.0.1:5173` 200.
- **Posicionamento travado:** **exploratório auditado** (C0–C2). C3–C4 bloqueados sem painel humano. Roadmap Tier S contingente em `docs/superpowers/plans/2026-05-19-mirofish-roadmap-coleta-humana-futura.md`.

## O que mudou nesta fase

1. Relatório deixou de ser apenas geração textual e passou a depender de gate sistemico.
2. O backend bloqueia relatório sem simulação concluida, material-base, grafo, config, perfis, run_state, diversidade mínima, trace OASIS e auditoria de citacoes.
3. A interface da etapa 3 consulta a qualidade da simulação e bloqueia a geração quando o sistema reprova.
4. A interface da etapa 4 exibe cadeia de custodia, artefatos e motivos de bloqueio.
5. Relatórios antigos sem `quality_gate` e `evidence_audit` são classificados como `legacy_unverified`, não publicaveis.
6. O runner OASIS ganhou pulso social inicial configuravel, com comentários, curtidas, rejeicoes, reposts e citacoes persistidas.
7. Perfis OASIS ganharam contrato comportamental para atuar como participantes sociais, não apenas observadores.
8. O sistema separa modo `client` de `demo/smoke`: diagnostico técnico pode rodar, mas nunca recebe status publicavel.
9. Auditoria de evidências passou a cobrir números: percentuais, probabilidades e contagens precisam estar no corpus ou marcados como inferencia/simulacao/calibracao.

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

## Decisões registradas

- Um relatório cliente só pode ser `publishable` se passar gate estrutural e auditoria de evidência.
- Citacao direta precisa existir literalmente no corpus local; traducao ou parafrase deve ser marcada como inferencia/simulacao.
- Volume de ações não basta: Distinct-2, entropia de agentes, entropia de tipos de ação e trace OASIS entram como criterio.
- Simulação antiga sem gate deve ser tratada como legado técnico, não entrega cliente.
- Smoke/demo existe como diagnostico técnico, separado de modo cliente e bloqueado como `diagnostic_only`.
- Número em relatório cliente e claim auditavel; se não aparece no corpus local, precisa estar rotulado como inferencia calibrada ou o relatório e bloqueado.

## Pendencias reais

1. Rodar uma nova simulação real longa com LLM ativo e verificar se atravessa o gate até relatório publicavel.
2. Criar preset de baixa atividade que gere diagnostico técnico sem fingir opiniao pública.
5. Continuar testes de API e frontend, hoje ainda sem suite automatizada de componentes.

## Roadmap Evolution

## Histórico relevante

- v1.0: sistema funcional.
- v1.1: relatório premium, graph_id, API de custos.
- v1.2: correções de pipeline, PT-BR, segurança básica, persistencia e QC inicial.
- v1.3: gate estrutural, governanca cliente/demo, auditoria de evidências/citacoes/numeros, diversidade social, cadeia de custodia e pulso OASIS.
