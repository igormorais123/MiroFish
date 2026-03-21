# Integracao Lenia-RR + MiroFish-Inteia

Data: 2026-03-18
Status: contrato inicial implementado no backend

## Objetivo

Permitir que o Lenia-RR consuma sinais agregados do `MiroFish-Inteia` sem depender do motor completo de simulacao no frontend.

## Endpoint inicial

- `GET /api/internal/v1/projects/<project_id>/lenia-export`
- `GET /api/internal/v1/simulations/<simulation_id>/lenia-export`

Header:

- `X-Internal-Token: <token>`

## Payload atual

```json
{
  "version": "1.0",
  "target_system": "lenia",
  "uf": "rr",
  "territorio": "Roraima",
  "project_id": "proj_xxx",
  "simulation_id": "sim_xxx",
  "project_status": "created",
  "simulation_status": "ready",
  "simulation_requirement": "Avaliar repercussao eleitoral e institucional em Roraima.",
  "cenario": "Disputa acirrada...",
  "atores": ["midia local", "liderancas regionais"],
  "segmentos": ["interior", "capital"],
  "canais": ["whatsapp", "instagram"],
  "hipoteses": ["escalada rapida de boatos"],
  "restricoes": [],
  "objetivos_analiticos": [],
  "signals": {
    "complexity_score": 48,
    "narrative_pressure": 15,
    "mobilization_score": 24,
    "territorial_sensitivity": 85
  },
  "recommended_overlays": [
    "narrative_pressure",
    "mobilization_score",
    "territorial_sensitivity"
  ],
  "source_summary": {
    "total_text_length": 244,
    "files_count": 1,
    "entities_count": null,
    "profiles_count": null
  },
  "helena_prompt_hint": "Ler o baseline do Lenia-RR em conjunto com pressao narrativa..."
}
```

## Uso recomendado no Lenia

1. Ler `uf` para validar compatibilidade com a tela atual.
2. Exibir `cenario` e `simulation_requirement` como contexto adicional.
3. Mostrar `atores`, `segmentos` e `hipoteses` em card lateral.
4. Traduzir `signals` em overlays ou badges operacionais.
5. Acrescentar `helena_prompt_hint` no bloco de insights.

## Query params sugeridos para o Lenia

- `mirofish_project_id`
- `mirofish_simulation_id`
- `mirofish_base_url`
- `mirofish_token`

Exemplo:

`http://127.0.0.1:8000/lenia.html?uf=rr&mirofish_project_id=proj_xxx&mirofish_base_url=http://127.0.0.1:5001&mirofish_token=inteia-local-dev-token`

## Proximo passo

Conectar o frontend do Lenia para:

- buscar automaticamente o `/lenia-export`
- enriquecer os insights da tela
- sinalizar se o acoplamento agrega valor real ao baseline do Lenia-RR
