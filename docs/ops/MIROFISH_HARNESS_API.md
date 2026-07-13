# MiroFish Harness API

Data de referencia: 2026-05-13

Este contrato permite que sistemas internos, como `voxsintetica-platform`, iniciem
pesquisas no MiroFish e consumam evidencias estruturadas depois que o pipeline
terminar.

## Autenticacao

Todas as rotas abaixo exigem:

```http
X-Internal-Token: <INTERNAL_API_TOKEN>
```

O valor real deve ficar apenas em cofres/ambientes. No consumidor, use um nome
local como `MIROFISH_INTERNAL_TOKEN` ou `MIROFISH_API_TOKEN`.

## Fluxo recomendado

1. Iniciar pesquisa:

```http
POST /api/internal/v1/harness/runs
```

Payload: mesmo contrato de `/api/internal/v1/run-preset`, com `name`,
`simulation_requirement`, `materials`, `structured_context`, `preset`,
`max_rounds` e flags de plataformas quando aplicavel.

Resposta `202`:

```json
{
  "success": true,
  "data": {
    "task_id": "task_...",
    "status": "processing"
  }
}
```

2. Acompanhar a task:

```http
GET /api/internal/v1/tasks/<task_id>
```

Quando a task completar, `data.result` inclui `project_id`, `graph_id`,
`simulation_id`, `report_id` e `report_url`.

3. Buscar pacote de evidencias:

```http
GET /api/internal/v1/harness/evidence-bundles/<simulation_id>
```

Resposta direta no contrato `mirofish.harness.v1`:

```json
{
  "id": "mirofish_bundle_sim_...",
  "missionId": "sim_...",
  "title": "Titulo do pacote",
  "source": "mirofish",
  "generatedAt": "2026-05-13T00:00:00+00:00",
  "evidence": [
    {
      "id": "report_...:report",
      "title": "Relatorio MiroFish report_...",
      "sourceUri": "https://host/api/report/report_...",
      "claim": "Sintese rastreavel do relatorio",
      "confidence": 0.9,
      "tags": ["mirofish", "report", "publishable"]
    }
  ],
  "graph": {
    "nodes": [],
    "edges": []
  },
  "forecasts": [
    {
      "horizon": "30 dias",
      "forecast": "Previsao estruturada",
      "probability": 0.68,
      "uncertainty": 0.5,
      "assumptions": []
    }
  ],
  "methodology": {
    "contractVersion": "mirofish.vox_science.v1",
    "mode": "public_data_grounded_synthetic_harness",
    "calibrationMode": "synthetic_trace_only",
    "verificationStatus": "verified",
    "claimLevel": "C1",
    "passesExecutionGate": true,
    "calibrationEvidence": null,
    "authority": {
      "status": "server_verified",
      "verified": true,
      "claimLevel": "C1",
      "passesExecutionGate": true
    },
    "newHumanCollection": false,
    "readiness": "passed",
    "availableArtifacts": ["methodology_manifest.json"],
    "recommendedMissingArtifacts": [],
    "population": null,
    "publicDataAnchors": [],
    "robustness": null
  },
  "qualityGates": [
    {
      "id": "harness-science-gate",
      "artifact": "harness_science_gate.json",
      "status": "passed",
      "authority": "server_verified",
      "description": "Gate cientifico final do harness Vox."
    }
  ],
  "limitations": ["delivery_status=publishable; publishable=true"]
}
```

### Camada Vox Science v1

O bundle preserva o contrato anterior e acrescenta, quando disponivel, duas
chaves para consumidores internos:

- `methodology`: resumo leve da metodologia, populacao, fontes publicas,
  modo de calibracao e prontidao cientifica.
- `qualityGates`: estado dos gates cientificos vinculados a artefatos JSON.
- `verified_vox_claim` na resposta de `/api/report/<id>/artifacts`: unica
  projecao de claim confiavel para clientes. Se `verified=false`, clientes devem
  exibir "nao verificado / sem claim" (`claim_level=null`) e ignorar claims,
  metricas, fontes e linguagem crua dos JSONs. C0 e reservado ao bundle
  autentico e corrente cujo gate de execucao foi bloqueado; C1 e reservado ao
  trace sintetico autentico que passou a execucao.
- `calibrationMode` e enum fechado:
  `unverified_no_calibration`, `synthetic_trace_only` ou
  `materialized_external_baseline`. O campo legado `mode` permanece
  `public_data_grounded_synthetic_harness` no contrato v1 e nao carrega estado
  de autoridade.
- `authority` informa se a superficie e `server_verified` ou apenas
  `diagnostic_only`. Population, anchors e robustness crus nunca sao
  republicados quando a geracao e nao verificada/C0; C1 permanece diagnostico.
- A verificacao exige HMAC do host, binding exato ao `report_id`, ancora corrente
  por relatorio e reabertura da autoridade materializada. `qualityGates` ficam
  `review/diagnostic_only` quando essa verificacao falha.
- C4 exige criterios de desempenho material congelados no recibo pre-cutoff:
  politica `vox-c4-material-v1`, piso de Brier skill 0.05 e razao maxima de
  log loss 0.99 contra o baseline constante. Customizacao so pode ser mais
  estrita; politica desconhecida, skill 0.01 ou ratio 1.0 sao rejeitados. Sao criterios
  operacionais pre-registrados, nao significancia estatistica ou intervalo de
  confianca.
- Baseline `rows` e aceito como entrada, mas nao promove C2+ no contrato atual;
  somente massas `distributions` somando `1 +/- 1e-6` alimentam as metricas de
  probabilidade rotulada.
- C2 ja exige MAE, KL e Wasserstein categorial materializados e dentro dos
  limiares declarados (atualmente <= 0.15 cada). C3 nao introduz esse piso:
  acrescenta runs/seeds materializados, estabilidade >= 0.70 e auditoria de
  todos os subgrupos com erro <= 0.15.

Artefatos Vox Science reconhecidos:

- `methodology_manifest.json`
- `baseline_registry.json`
- `public_data_anchors.json`
- `prompt_registry.json`
- `model_run_registry.json`
- `synthetic_interviews_manifest.json`
- `fidelity_report.json`
- `pimmur_audit.json`
- `compost_audit.json`
- `claim_policy_audit.json`
- `harness_science_gate.json`

Valores de `methodology.readiness`:

- `legacy`: relatorio antigo sem artefatos Vox Science.
- `partial`: parte dos artefatos existe.
- `ready_for_science_gate`: artefatos minimos existem, mas o gate final ainda
  nao aprovou.
- `blocked`: existe gate, mas ele falhou ou a geracao/hash nao e confiavel.
- `passed`: gate v2 com `passes_execution_gate=true`, geracao comum, hashes
  canonicos e consistencia cruzada de fidelity/policy/methodology foi verificado.
  Clientes consultam `verified_vox_claim.claim_level`, nunca o gate cru.

## Base URL para consumidores

Para o Vox, configure:

```env
MIROFISH_API_URL=https://<host-mirofish>/api/internal/v1/harness
MIROFISH_INTERNAL_TOKEN=<mesmo valor de INTERNAL_API_TOKEN do MiroFish>
```

Em ambiente local, troque o host pelo backend Flask que estiver expondo a API
interna. Nunca coloque esse token em frontend/bundle de cliente.
