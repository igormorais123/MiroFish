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

Em 2026-05-06, os valores não vazios conhecidos foram enviados para GitHub Actions Secrets do repositório `igormorais123/MiroFish`.

Fontes usadas sem expor valores:

- `.env` local deste workspace, para o primeiro espelho de variáveis já usadas pelos testes e scripts.
- Variáveis de ambiente locais do operador, quando já existiam no cofre da sessão.
- `.env` vivo da VPS em `/opt/mirofish`, apenas por SSH e sem imprimir valores.

GitHub Secrets de repositório configurados:

- `APP_CODE`
- `APP_NAME`
- `FLASK_DEBUG`
- `FLASK_HOST`
- `FLASK_PORT`
- `GEMINI_API_KEY`
- `GRAPHITI_BASE_URL`
- `GRAPHITI_MODEL`
- `GRAPHITI_TIMEOUT`
- `HERMES_NUVEM_SSH`
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
- `OMNIROUTE_API_KEY`
- `OMNIROUTE_URL`
- `OPENAI_API_KEY`
- `OPENAI_BASE_URL`
- `OPENAI_MODEL`
- `ZEP_API_KEY`
- `ZEP_BASE_URL`
- `ZEP_MODE`
- `ZEP_REQUIRED`

Variaveis esperadas apos o hardening de 2026-05-08:

- `SECRET_KEY` deve existir como segredo em producao antes de usar sessao/cookie Flask persistente.
- `CORS_ORIGINS` deve existir como configuracao nao secreta se o backend precisar aceitar origens alem da lista segura padrao.

GitHub Environment `vps-production` configurado com segredos necessários para deploy/operacao da VPS:

- `GEMINI_API_KEY`
- `GRAPHITI_BASE_URL`
- `GRAPHITI_MODEL`
- `GRAPHITI_TIMEOUT`
- `HERMES_NUVEM_SSH`
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
- `OMNIROUTE_API_KEY`
- `OMNIROUTE_URL`
- `OPENAI_API_KEY`
- `OPENAI_BASE_URL`
- `OPENAI_MODEL`
- `ZEP_API_KEY`
- `ZEP_BASE_URL`
- `ZEP_MODE`
- `ZEP_REQUIRED`

GitHub Environments existentes:

- `vps-production`: cofre para deploy/operacao da VPS.
- `vercel-production`: reservado para automacoes futuras de Vercel.
- `Production` e `Preview`: ambientes criados/integrados pelo fluxo Vercel/GitHub.

Vercel Environment Variables ficam restritas a configuracao publica de build. Em 2026-05-06 foi configurado apenas `VITE_BASE=/mirofish/` em Production, porque o site publico oficial roda no subcaminho `/mirofish`. O projeto Vercel atual e frontend estatico; chaves de LLM, OmniRoute, Zep, Supabase service role, Apify e tokens internos nao devem ir para bundle de cliente. Colocar em Vercel somente quando houver runtime server-side que realmente precise delas.

Valores reais de `APIFY_API_TOKEN`, `SUPABASE_URL`, `SUPABASE_ANON_KEY` e `SUPABASE_SERVICE_ROLE_KEY` nao foram encontrados nos ambientes vivos consultados. Permanecem pendentes ate existir projeto/token real.

## Matriz de ambientes

| Grupo | Variáveis | GitHub Secrets | Vercel | VPS |
|---|---|---:|---:|---:|
| Identidade da app | `APP_NAME`, `APP_CODE` | Sim | Só se build precisar | Sim |
| Flask/backend | `FLASK_DEBUG`, `FLASK_HOST`, `FLASK_PORT`, `SECRET_KEY`, `CORS_ORIGINS` | Sim (`SECRET_KEY` sempre como segredo; `CORS_ORIGINS` pode ser variável não secreta) | Não para frontend estático | Sim |
| LLM/OpenAI-compatible | `LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL_NAME`, `LLM_MODEL_ALIASES`, `LLM_TIMEOUT_SECONDS`, `LLM_MAX_RETRIES` | Sim | Só se runtime Vercel usar LLM | Sim |
| Modelos Helena | `LLM_AGENT_MODEL`, `LLM_PREMIUM_MODEL`, `LLM_HELENA_MODEL` | Sim | Só se runtime Vercel usar LLM | Sim |
| OmniRoute | `OMNIROUTE_URL`, `OMNIROUTE_API_KEY`, `OMNIROUTE_BASE_URL`, `OMNIROUTE_MODEL`, `OMNIROUTE_FAST_MODEL`, `OMNIROUTE_PREMIUM_MODEL`, `OMNIROUTE_TIMEOUT` | Pendente quando houver valor real | Pendente se usado no deploy | Sim |
| Provedores LLM auxiliares | `CEREBRAS_API_KEY`, `CEREBRAS_URL`, `LLM_BOOST_API_KEY`, `LLM_BOOST_BASE_URL`, `LLM_BOOST_MODEL_NAME` | Pendente quando houver valor real | Não para frontend estático | Sim |
| Graphiti | `GRAPHITI_BASE_URL`, `GRAPHITI_TIMEOUT`, `GRAPHITI_MODEL` | Sim | Não usar `localhost` em produção | Sim |
| Zep legado | `ZEP_BASE_URL`, `ZEP_API_KEY`, `ZEP_MODE`, `ZEP_REQUIRED` | Sim, quando existir no ambiente vivo | Não para frontend estático | Sim |
| Neo4j | `NEO4J_PASSWORD` | Sim | Não para frontend estático | Sim |
| Auth interna | `INTERNAL_API_TOKEN` | Sim | Só se proxy/runtime precisar | Sim; consumidores internos devem guardar o mesmo valor como `MIROFISH_INTERNAL_TOKEN` ou equivalente |
| Apify | `APIFY_API_TOKEN`, `APIFY_ENRICH_TIMEOUT_SECONDS`, `COLMEIA_SCRIPTS_PATH` | Pendente quando houver token real | Não para frontend estático | Sim |
| Supabase | `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY` | Pendente quando houver projeto/valores reais | Só publicar `SUPABASE_URL`/anon quando necessário; nunca `SERVICE_ROLE` no cliente | Sim |
| Dados locais | `MIROFISH_DATA_DIR` | Opcional | Não | Sim |
| Build publico Vercel | `VITE_BASE` | Nao e segredo | Sim, Production = `/mirofish/` | Nao |

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
