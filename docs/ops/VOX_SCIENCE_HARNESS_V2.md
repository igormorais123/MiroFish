# Vox Science Harness v2

Data: 2026-05-18
Status: implementado como vertical slice P0

## Objetivo

O Vox Science Harness v2 adiciona uma camada cientifica auditavel ao MiroFish sem
exigir entrevistas novas, questionarios novos, painel humano ou calibracao humana
adicional.

A regra operacional permanece:

- usar dados publicos;
- usar ativos internos ja existentes;
- registrar prompts, modelos, fontes e limites de claim;
- entregar linguagem forte e executiva, com gate interno controlando a forca do
  claim.

## Artefatos produzidos

Cada relatorio novo pode receber 11 artefatos Vox Science:

| Artefato | Papel |
|---|---|
| `methodology_manifest.json` | Escopo, populacao, decisao, restricao de coleta e claim alvo. |
| `baseline_registry.json` | Fontes publicas usadas como ancoragem/validacao. |
| `public_data_anchors.json` | Variaveis ancoradas, fonte, papel e confianca. |
| `prompt_registry.json` | Perguntas, constructos, parafrases, schema e contexto proibido. |
| `model_run_registry.json` | Modelo, politica de temperatura, seeds e hashes. |
| `synthetic_interviews_manifest.json` | Unidades sinteticas, acoes observadas e matriz minima recomendada. |
| `fidelity_report.json` | Score, variancia, erro externo quando existir e modo de medicao. |
| `pimmur_audit.json` | Profile, Interaction, Memory, Minimal-Control, Unawareness, Realism. |
| `compost_audit.json` | Separacao de benchmark/outcome e risco de contaminacao. |
| `claim_policy_audit.json` | Nivel C0-C4, linguagem permitida e linguagem bloqueada. |
| `harness_science_gate.json` | Decisao final do gate cientifico. |

## Niveis de claim

| Nivel | Uso |
|---|---|
| C0 | Mapa qualitativo de sinais e friccoes sinteticas. |
| C1 | Simulacao sintetica exploratoria com rastreabilidade metodologica. |
| C2 | Simulacao sintetica calibrada por dados publicos e robustez auditada. |
| C3 | Estimativa sintetica calibrada por baseline publico comparavel. |
| C4 | Previsao operacional monitoravel com cenario base e tese adversaria. |

## Integração no backend

Pontos implementados:

- `backend/app/services/vox_science/artifacts.py`: builders deterministas dos
  artefatos P0.
- `backend/app/services/report_agent.py`: salva os artefatos no fim da geracao do
  relatorio, depois de auditoria/forecast e antes do `mission_bundle`.
- `backend/app/services/harness_evidence_bundle.py`: expõe `methodology` e
  `qualityGates` no contrato interno do harness.
- `backend/app/services/report_method_checklist.py`: reconhece os artefatos Vox
  Science como parte do checklist metodologico.
- `backend/app/services/executive_package.py`: inclui os artefatos Vox Science
  no anexo de evidencias do pacote executivo.
- `backend/app/services/report_exporter.py`: inclui os artefatos Vox Science no
  anexo de evidencias da exportacao HTML.

Os artefatos sao salvos via `ReportManager.save_json_artifact()`, na pasta do
relatorio. Isso preserva relatórios antigos e evita tornar Vox Science um hard
blocker prematuro.

## Integração no frontend

`frontend/src/components/Step4Report.vue` exibe um painel leve `Vox Science` na
tela de relatorio:

- status do science gate;
- claim C0-C4;
- linguagem maxima permitida;
- quantidade de artefatos;
- score de fidelidade;
- variancia;
- PIMMUR;
- quantidade de baselines;
- indicador de que nao houve coleta humana nova;
- fontes publicas principais;
- alertas do gate.

O painel consome apenas resumos dos artefatos já carregados pela rota de
artefatos. Os JSONs completos continuam disponiveis para auditoria.

## Regras de segurança metodológica

- Outcome usado para validacao nao entra no prompt.
- `new_human_collection` deve ser `false` neste modo.
- Linguagens bloqueadas incluem "margem de erro amostral", "resposta humana
  coletada" e claims populacionais fortes sem baseline.
- Relatorios antigos podem aparecer como `legacy` ou `partial`; isso nao quebra
  consumo anterior.

## Comandos de validação

Backend completo:

```powershell
cd backend
python -m pytest tests -q
```

Frontend:

```powershell
cd frontend
npm run build
```

Dev local usado na validação:

```powershell
npm run backend
cd frontend
npx vite --host localhost --port 5173
```

Portas observadas:

- backend: `http://localhost:5001`
- frontend: `http://localhost:5173`

## Próximo nível

O P0 cria e expõe os artefatos. O próximo avanço é instrumentar a matriz real de
`paraphrases x seeds`, para que `fidelity_report.json` deixe de ser
`trace_based_until_full_seed_paraphrase_matrix` e passe a medir dispersao real
por pergunta.
