# Verificacao

## Comandos

```powershell
.\backend\.venv\Scripts\python.exe -m pytest backend\tests -q
npm run build
git status --short
```

## Resultado

Passou.

## Evidencia

- Backend: `171 passed in 4.87s`.
- Frontend: Vite build passou.
- Git estava limpo antes da implantacao RalphLoop.

## Limite

Nao foi rodada simulacao real P0.1. Isso exige decisao humana sobre custo/LLM/tempo.
