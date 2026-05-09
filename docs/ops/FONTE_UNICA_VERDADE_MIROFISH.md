# MiroFish — Fonte única de verdade e reconciliação operacional

Data: 2026-05-06
Responsável operacional: Hermes / INTEIA

## Regra principal

O repositório `igormorais123/MiroFish` é a fonte única de verdade para código, documentação, deploy e configuração não secreta.

Nunca aplicar patch direto em `/opt/mirofish` sem depois transformar em commit/PR neste repositório.

## Mapa oficial

### Código oficial
- GitHub: https://github.com/igormorais123/MiroFish
- Branch estável: `main`
- Pull requests: https://github.com/igormorais123/MiroFish/pulls
- Actions: https://github.com/igormorais123/MiroFish/actions

### Site público correto
- Frontend público: https://inteia.com.br/mirofish
- API pública correta: https://inteia.com.br/mirofish/api/simulation/history?limit=1

### Rotas erradas ou legadas
- `https://inteia.com.br/api/...` não é API do MiroFish.
- `https://mirofish.inteia.com.br` está legado/quebrado enquanto apontar para `127.0.0.1:4000` sem serviço real.

### VPS atual observada
- Diretório vivo: `/opt/mirofish`
- Clone Git limpo preparado: `/opt/mirofish-git`
- Backend vivo: `http://127.0.0.1:5001`
- Frontend/container dev: `http://127.0.0.1:3001`
- Containers observados: `mirofish-inteia` e `mirofish`
- Imagem legada observada: `ghcr.io/666ghj/mirofish:latest`

## Estado observado em 2026-05-06

1. O site público `https://inteia.com.br/mirofish` está na Vercel.
2. A API pública sob `/mirofish/api/...` chega no backend da VPS.
3. `/opt/mirofish` não é repositório Git.
4. `/opt/mirofish-git` é o clone limpo do GitHub para reconciliação segura.
5. `/opt/mirofish-inteia` também não é repositório Git.
6. O container legado local serve frontend dev/chinês em `3001`, diferente do frontend público da Vercel.
7. A Vercel, o GitHub e o `/opt/mirofish/frontend/dist` tinham builds diferentes.
8. O `deploy/docker-compose.vps.yaml` no GitHub e o da VPS divergiam de forma relevante.
9. Segredos vivos da VPS foram espelhados para GitHub Secrets e para o ambiente `vps-production`, sem versionar valores.

## Estado operacional atualizado em 2026-05-09

- `main` contém o código publicado; o frontend direto da Vercel fica em `https://mirofish-inteia.vercel.app/mirofish`.
- `inteia.com.br/mirofish` é roteado pelo projeto Vercel raiz `frontend`, com rotas de projeto para app, assets e API. A configuração detalhada está em [`VERCEL_DEPLOY.md`](VERCEL_DEPLOY.md).
- A API pública correta é `https://inteia.com.br/mirofish/api/...`, que reescreve para `https://mirofish.inteia.com.br/api/...`.
- A porta pública `72.62.108.24:5001` fica bloqueada por firewall; não usar esse destino em Vercel.
- O deploy da VPS deve partir de `/opt/mirofish-git` e carregar explicitamente o `.env` da raiz:

  ```bash
  cd /opt/mirofish-git
  git fetch origin
  git pull --ff-only origin main
  docker compose --env-file .env -f deploy/docker-compose.vps.yaml up -d --build
  ```

- Antes de recriar container, recomenda-se marcar a imagem atual para rollback:

  ```bash
  docker tag "$(docker inspect mirofish-inteia --format '{{.Image}}')" "mirofish-inteia:rollback-$(date +%Y%m%d-%H%M%S)"
  ```

## Política de merge entre instâncias

Quando Igor estiver usando Claude Code no PC e Codex em outra instância:

1. Toda instância deve começar com:
   ```bash
   git fetch origin
   git checkout main
   git pull --ff-only origin main
   git checkout -b tipo/descricao-curta
   ```

2. Nenhuma instância deve trabalhar direto em `main`.

3. Antes de enviar mudança:
   ```bash
   npm install
   cd frontend && npm install && npm run build
   cd ../backend && uv run python -m pytest tests -q
   ```

4. Se não conseguir rodar teste, registrar explicitamente no PR:
   - comando tentado;
   - erro;
   - motivo provável;
   - risco.

5. Toda mudança deve virar PR no GitHub.

6. A VPS só deve receber código já mergeado em `main`, salvo hotfix emergencial. Hotfix emergencial precisa virar commit depois.

## Ordem segura para acertar a casa

1. Fazer backup do estado vivo da VPS.
2. Criar clone limpo do GitHub na VPS.
3. Comparar `/opt/mirofish` contra o clone limpo.
4. Migrar apenas patches reais, não backups/lixo/build gerado.
5. Preservar `.env`, uploads, logs e dados vivos fora do Git.
6. Fazer PR de reconciliação.
7. Depois do merge, apontar deploy para o clone limpo.

## Não versionar

Nunca commitar:
- `.env`
- `.env.bak*`
- tokens/chaves/segredos
- `backend/uploads/`
- logs vivos
- `frontend/dist/` salvo decisão explícita de deploy estático
- `node_modules/`
- backups `*.bak-*`

## Critério de casa arrumada

A casa só está arrumada quando:

- GitHub contém o código final.
- Vercel faz deploy do GitHub.
- VPS roda código derivado do GitHub.
- `/opt/mirofish` ou equivalente é repositório Git limpo.
- API pública correta responde 200 em `/mirofish/api/...`.
- Build frontend passa.
- Testes backend passam ou falhas ficam documentadas.
- Ninguém precisa lembrar comando de cabeça: tudo fica documentado aqui.
