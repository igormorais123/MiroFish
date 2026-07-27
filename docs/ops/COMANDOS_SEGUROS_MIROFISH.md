# MiroFish — comandos seguros para Claude Code, Codex e Hermes

## Começar trabalho novo

```bash
git fetch origin
git checkout main
git pull --ff-only origin main
git checkout -b feat/minha-mudanca
```

## Conferir onde estou

```bash
git status -sb
git remote -v
git branch --show-current
```

## Rodar frontend

```bash
npm install
cd frontend
npm install
npm run build
```

## Rodar backend

```bash
cd backend
uv run python -m pytest tests -q
```

Se `uv` não existir:

```bash
cd backend
python -m pytest tests -q
```

## Publicar na VPS com OmniRoute interno

A rede privada compartilhada deve existir antes do `docker compose`. Ela não
publica a porta do OmniRoute na internet. Confirme primeiro que o commit a
publicar já está em `origin/main`.

```bash
docker network inspect inteia-ai >/dev/null 2>&1 || docker network create inteia-ai
cd /opt/mirofish-git
git fetch origin
git pull --ff-only origin main

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "/opt/backups/mirofish/${STAMP}"
cp -a .env deploy/docker-compose.vps.yaml "/opt/backups/mirofish/${STAMP}/"
docker inspect mirofish-inteia >"/opt/backups/mirofish/${STAMP}/container-inspect.json"
docker tag "$(docker inspect mirofish-inteia --format '{{.Image}}')" \
  "mirofish-inteia:rollback-${STAMP}"

docker compose --env-file .env -f deploy/docker-compose.vps.yaml build mirofish
docker compose --env-file .env -f deploy/docker-compose.vps.yaml up -d mirofish
docker inspect mirofish-inteia --format '{{.State.Status}}/{{.State.Health.Status}} restarts={{.RestartCount}}'
curl -fsS https://inteia.com.br/mirofish/health/public
curl -fsS https://inteia.com.br/mirofish/api/helena/status
```

O `.env` da VPS deve usar `LLM_BASE_URL=http://omniroute-inteia:20128/v1`. O container `omniroute-inteia` também precisa participar da rede `inteia-ai`; seu recriador/atualizador deve usar `--network inteia-ai`.

O volume persistente de uploads precisa ser gravável pelo usuário isolado do
container (`10001:10001`). Antes de corrigir propriedade, faça backup
verificável; depois confirme com
`docker exec mirofish-inteia test -w /app/backend/uploads/projects`.

Não imprima o `INTERNAL_API_TOKEN`. Para testar uma rota autenticada da Helena,
carregue o valor no ambiente da sessão e envie apenas o cabeçalho:

```bash
curl -fsS -H "X-Internal-Token: ${INTERNAL_API_TOKEN}" \
  "https://inteia.com.br/mirofish/api/helena/commands?limit=1"
```

## Provar o modelo efetivo

Healthcheck e catálogo não bastam: um alias pode aceitar `codex/gpt-5.6-luna` e executar outro modelo. Depois de alterar o roteador ou o `.env`, faça uma chamada mínima pelo mesmo ambiente do MiroFish:

```bash
docker exec -w /app/backend mirofish-inteia \
  /app/backend/.venv/bin/python scripts/check_llm_model.py \
  --expected-model gpt-5.6-luna
```

O comando não imprime credenciais. Ele termina com erro se o modelo efetivo não for `gpt-5.6-luna` ou se a resposta não completar a prova mínima.

## Commit seguro

```bash
git status -sb
git diff --stat
git add caminho/do/arquivo
git commit -m "fix: descreve a mudança"
git push -u origin HEAD
```

## Links oficiais

- Site correto: https://inteia.com.br/mirofish/
- API correta: https://inteia.com.br/mirofish/api/simulation/history?limit=1
- GitHub: https://github.com/igormorais123/MiroFish
- Pull requests: https://github.com/igormorais123/MiroFish/pulls
- Actions: https://github.com/igormorais123/MiroFish/actions

## Aviso para agentes

Não use `https://inteia.com.br/api/...` para MiroFish.
Use sempre `/mirofish/api/...` no ambiente público.

Não use `https://mirofish.inteia.com.br/` como link do produto. A raiz desse subdomínio redireciona para `https://inteia.com.br/mirofish/`.

`https://mirofish.inteia.com.br/api/...` é ponte técnica legada. Não use IP
direto nem portas `4000`, `5001` ou `8003`.
