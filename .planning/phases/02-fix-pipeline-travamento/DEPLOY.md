# Deploy — Phase 2 Tasks 3, 4, 6

**Data:** 2026-04-18 05:00 UTC
**Executor:** Efesto (autônomo)
**VPS:** kvm4 (72.62.108.24)

## O que foi aplicado

| Task | Arquivo | Mudança | Confirmado no container |
|---|---|---|---|
| 3 | `report_agent.py:940` | `MAX_TOOL_CALLS_PER_CHAT 2→3` | ✅ |
| 4.1 | `llm_client.py:115` | backoff exponencial 5-30s + jitter | ✅ |
| 4.2 | `config.py:110` | `LLM_MAX_RETRIES` default 3→8 | ✅ |
| 4.3 | `docker-compose.vps.yaml:16` | `LLM_MAX_RETRIES=3` → `=8` | ✅ |
| 6 | `simulation_runner.py:427` | chmod 0o666 nos .db antes do spawn | ✅ |

## Verificação pós-deploy

```
docker ps: mirofish-inteia  Up (healthy)
curl localhost:4000/: HTTP 200
curl localhost:4000/api/simulation/list: {"count": 0, "data": [], "success": true}
env LLM_MAX_RETRIES=8 OK
grep MAX_TOOL_CALLS_PER_CHAT = 3 OK
grep "Backoff exponencial 5-30s" OK
grep "Phase 2 Task 6" OK
```

## Rollback

Backups em `/opt/mirofish/backend/app/{utils,services}/*.bak-20260418` + `/opt/mirofish/deploy/docker-compose.vps.yaml.bak-20260418`.

Comando:
```bash
ssh kvm4
cd /opt/mirofish
cp backend/app/utils/llm_client.py.bak-20260418 backend/app/utils/llm_client.py
cp backend/app/config.py.bak-20260418 backend/app/config.py
cp backend/app/services/report_agent.py.bak-20260418 backend/app/services/report_agent.py
cp backend/app/services/simulation_runner.py.bak-20260418 backend/app/services/simulation_runner.py
cp deploy/docker-compose.vps.yaml.bak-20260418 deploy/docker-compose.vps.yaml
docker compose -f deploy/docker-compose.vps.yaml up -d --build --no-deps mirofish
```

## Pendente (próxima sessão, precisa validação runtime mais profunda)

- Task 1 (fix think/code-fence upstream `985f89f`) — INTEIA já tem equivalente, sem ação
- Task 2 (None fallback upstream `54f1291`) — adiar, arquivo tem 2770 linhas customizadas
- Task 5 (provider fallback chain) — requer chaves `DEEPSEEK_API_KEY`, `GROQ_API_KEY`
- Task 7 (Graphiti health check real) — precisa mapear `zep_entity_reader.count_entities`

## UAT — rodar na próxima simulação real

1. [ ] Upload de material típico INTEIA
2. [ ] Simulação completa 40 rodadas sem intervenção
3. [ ] Medir: `tool_calls_count` médio por seção (esperado aumentar vs baseline)
4. [ ] Matar OmniRoute por 2min durante execução: retoma sozinho?
5. [ ] Restart do container + re-start de simulação: sem "readonly database"
