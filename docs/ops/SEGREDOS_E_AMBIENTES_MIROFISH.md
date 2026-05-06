# Segredos e ambientes — MiroFish INTEIA

Data de referência: 2026-05-06

Este arquivo define onde cada chave deve viver. Ele nunca deve conter valores reais.

## Regra operacional

- Valores reais ficam em cofres: GitHub Secrets, Vercel Environment Variables, VPS `.env` fora do Git ou painel do provedor.
- `.env`, `.env.local`, `.vercel/`, backups, logs e uploads nunca entram no repositório.
- Agentes devem listar apenas nomes de variáveis. Não imprimir valores de `.env` no terminal compartilhado.
- Variáveis com `localhost`, caminhos de máquina pessoal ou tokens locais não devem ir para Vercel produção.
- Ao adicionar uma integração externa, atualizar este arquivo, `.env.example`, GitHub Secrets e o ambiente de deploy aplicável.

## Estado aplicado

Em 2026-05-06, os valores locais não vazios de `.env` foram enviados para GitHub Actions Secrets do repositório `igormorais123/MiroFish`.

GitHub Secrets configurados:

- `APP_CODE`
- `APP_NAME`
- `FLASK_DEBUG`
- `FLASK_HOST`
- `FLASK_PORT`
- `GRAPHITI_BASE_URL`
- `GRAPHITI_MODEL`
- `GRAPHITI_TIMEOUT`
- `INTERNAL_API_TOKEN`
- `LLM_AGENT_MODEL`
- `LLM_API_KEY`
- `LLM_BASE_URL`
- `LLM_HELENA_MODEL`
- `LLM_MAX_RETRIES`
- `LLM_MODEL_ALIASES`
- `LLM_MODEL_NAME`
- `LLM_PREMIUM_MODEL`
- `LLM_TIMEOUT_SECONDS`
- `NEO4J_PASSWORD`

Não foram enviados para Vercel porque os valores locais atuais são de desenvolvimento e incluem endpoints `localhost`. Vercel produção precisa receber valores reais de produção pelo painel ou CLI.

## Matriz de ambientes

| Grupo | Variáveis | GitHub Secrets | Vercel | VPS |
|---|---|---:|---:|---:|
| Identidade da app | `APP_NAME`, `APP_CODE` | Sim | Só se build precisar | Sim |
| Flask/backend | `FLASK_DEBUG`, `FLASK_HOST`, `FLASK_PORT` | Sim | Não para frontend estático | Sim |
| LLM/OpenAI-compatible | `LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL_NAME`, `LLM_MODEL_ALIASES`, `LLM_TIMEOUT_SECONDS`, `LLM_MAX_RETRIES` | Sim | Só se runtime Vercel usar LLM | Sim |
| Modelos Helena | `LLM_AGENT_MODEL`, `LLM_PREMIUM_MODEL`, `LLM_HELENA_MODEL` | Sim | Só se runtime Vercel usar LLM | Sim |
| OmniRoute | `OMNIROUTE_URL`, `OMNIROUTE_API_KEY`, `OMNIROUTE_BASE_URL`, `OMNIROUTE_MODEL`, `OMNIROUTE_FAST_MODEL`, `OMNIROUTE_PREMIUM_MODEL`, `OMNIROUTE_TIMEOUT` | Pendente quando houver valor real | Pendente se usado no deploy | Sim |
| Graphiti | `GRAPHITI_BASE_URL`, `GRAPHITI_TIMEOUT`, `GRAPHITI_MODEL` | Sim | Não usar `localhost` em produção | Sim |
| Neo4j | `NEO4J_PASSWORD` | Sim | Não para frontend estático | Sim |
| Auth interna | `INTERNAL_API_TOKEN` | Sim | Só se proxy/runtime precisar | Sim |
| Apify | `APIFY_API_TOKEN`, `APIFY_ENRICH_TIMEOUT_SECONDS`, `COLMEIA_SCRIPTS_PATH` | Pendente quando houver token real | Não para frontend estático | Sim |
| Supabase | `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY` | Pendente quando houver projeto/valores reais | Só publicar `SUPABASE_URL`/anon quando necessário; nunca `SERVICE_ROLE` no cliente | Sim |
| Dados locais | `MIROFISH_DATA_DIR` | Opcional | Não | Sim |

## Comandos seguros

Listar nomes no GitHub:

```bash
gh secret list --repo igormorais123/MiroFish
```

Listar nomes no Vercel:

```bash
vercel env ls
```

Adicionar segredo ao GitHub sem registrar valor em arquivo:

```bash
gh secret set NOME_DA_VARIAVEL --repo igormorais123/MiroFish
```

Adicionar segredo ao Vercel somente com valor correto de produção:

```bash
vercel env add NOME_DA_VARIAVEL production preview development
```

## Checklist para novas integrações

- [ ] A variável aparece em `.env.example` com valor placeholder.
- [ ] O valor real foi colocado no cofre correto.
- [ ] O valor não apareceu em commit, log, screenshot, PR body ou issue pública.
- [ ] Se a variável roda em Vercel, ela não aponta para `localhost`.
- [ ] Se a variável começa com `VITE_`, `NEXT_PUBLIC_` ou equivalente público, ela não contém segredo.
- [ ] Supabase `SERVICE_ROLE` fica apenas no backend/servidor, nunca no cliente.
