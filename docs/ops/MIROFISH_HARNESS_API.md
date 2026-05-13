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
  "limitations": ["delivery_status=publishable; publishable=true"]
}
```

## Base URL para consumidores

Para o Vox, configure:

```env
MIROFISH_API_URL=https://<host-mirofish>/api/internal/v1/harness
MIROFISH_INTERNAL_TOKEN=<mesmo valor de INTERNAL_API_TOKEN do MiroFish>
```

Em ambiente local, troque o host pelo backend Flask que estiver expondo a API
interna. Nunca coloque esse token em frontend/bundle de cliente.
