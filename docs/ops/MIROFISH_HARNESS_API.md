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
    "calibrationMode": "public_data_and_existing_assets",
    "newHumanCollection": false,
    "readiness": "passed",
    "availableArtifacts": ["methodology_manifest.json"],
    "recommendedMissingArtifacts": [],
    "population": "publico-alvo declarado na missao MiroFish",
    "publicDataAnchors": ["IBGE Censo 2022"],
    "robustness": {
      "overall_score": 0.78,
      "variance_ratio": 0.72,
      "passes_gate": true
    }
  },
  "qualityGates": [
    {
      "id": "harness-science-gate",
      "artifact": "harness_science_gate.json",
      "status": "passed",
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
- `passed`: `harness_science_gate.json` aprovou.

## Base URL para consumidores

Para o Vox, configure:

```env
MIROFISH_API_URL=https://<host-mirofish>/api/internal/v1/harness
MIROFISH_INTERNAL_TOKEN=<mesmo valor de INTERNAL_API_TOKEN do MiroFish>
```

Em ambiente local, troque o host pelo backend Flask que estiver expondo a API
interna. Nunca coloque esse token em frontend/bundle de cliente.
