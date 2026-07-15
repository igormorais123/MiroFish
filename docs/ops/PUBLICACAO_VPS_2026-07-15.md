# Publicação do MiroFish na VPS principal

Data de reconciliação: 2026-07-15

VPS: `2.25.174.138` (`srv1732811.hstgr.cloud`)

URL canônica: `https://inteia.com.br/mirofish/`

## Topologia publicada

- Nginx do host recebe `/mirofish/` e encaminha para `127.0.0.1:4000`.
- Nginx do host recebe `/mirofish/api/` e encaminha para `127.0.0.1:5001/api/`.
- Nginx do host recebe `/mirofish/health/` e encaminha para `127.0.0.1:5001/health/`.
- O container `mirofish-inteia` reúne o frontend estático e o backend Flask.
- Uploads persistem no host em `/opt/mirofish/backend/uploads`.

## Publicação reproduzível

```bash
cd /opt/mirofish-git
git fetch origin
git checkout main
git pull --ff-only origin main
docker compose --env-file .env -f deploy/docker-compose.vps.yaml build mirofish
docker compose --env-file .env -f deploy/docker-compose.vps.yaml up -d --no-deps mirofish
```

O arquivo `deploy/nginx/inteia.com.br.mirofish.conf` deve ser instalado como snippet e incluído no bloco HTTPS de `inteia.com.br`. Antes de recarregar, sempre execute `nginx -t`.

## Backup e rollback

Antes de cada publicação:

1. registrar o commit em produção;
2. etiquetar a imagem atual como `mirofish-inteia:rollback-<timestamp>`;
3. copiar o `.env` para backup privado com permissão `600`;
4. arquivar uploads e configurações Nginx relevantes;
5. somente então recriar o container.

Para rollback, restaure o snippet/configuração Nginx do backup, recrie o container a partir da imagem etiquetada e restaure os uploads apenas se uma verificação comprovar perda ou corrupção. Não sobrescreva uploads íntegros por rotina.

## Smoke test obrigatório

```bash
curl -fsS https://inteia.com.br/mirofish/ >/dev/null
curl -fsS https://inteia.com.br/mirofish/health/public
curl -fsS 'https://inteia.com.br/mirofish/api/simulation/history?limit=1'
```

Os dois últimos endpoints devem responder JSON; receber `text/html` significa que o fallback do site capturou a rota e o MiroFish ainda não está corretamente publicado.
