# Relatorio de reconciliacao da VPS - MiroFish - 2026-05-10

## Resumo

Foi executada a ordem segura para acertar a casa entre o estado vivo da VPS em
`/opt/mirofish` e o clone limpo do GitHub em `/opt/mirofish-git`.

O estado vivo foi preservado antes de qualquer mudanca, o clone limpo foi
atualizado a partir de `origin/main`, e a comparacao foi feita sem trazer para o
Git arquivos de ambiente, uploads, logs, backups, cache ou build gerado.

## Backup feito na VPS

- Diretorio do backup: `/opt/mirofish-backups/reconcile-20260510-014614`.
- Imagem de rollback Docker: `mirofish-inteia:rollback-reconcile-20260510-014614`.
- Pacote de codigo sem runtime: `live-code-no-runtime.tar.gz`.
- Pacote sensivel de runtime: `live-runtime-sensitive.tar.gz`.
- Pacote sensivel do clone limpo: `clean-clone-env-sensitive.tar.gz`.
- Checksums: `SHA256SUMS`.

Os pacotes sensiveis ficam somente na VPS. Eles existem para rollback e
auditoria operacional, nao para versionamento.

## Base comparada

- Clone limpo: `/opt/mirofish-git`.
- Fonte: `https://github.com/igormorais123/MiroFish`.
- Branch: `main`.
- Commit comparado: `4e8f469` (`fix: usa gunicorn no container de producao`).

## Resultado da comparacao

- Arquivos rastreados divergentes: 436.
- Arquivos rastreados ausentes no vivo: 222.
- Arquivos rastreados modificados no vivo: 214.
- Arquivos extras filtrados no vivo: 284.

A maior parte da divergencia vinha do fato de `/opt/mirofish` estar atrasado em
relacao ao GitHub, alem de conter backups, cache, uploads, assets de exemplo,
scripts manuais e artefatos operacionais.

## Patch migrado para o Git

- `backend/app/utils/zep_paging.py`: shim de compatibilidade para imports legados
  do antigo SDK Zep. O backend atual usa Graphiti Server via REST, entao o shim
  retorna listas vazias e registra aviso em log.
- `backend/tests/test_zep_paging_compat.py`: cobre o comportamento fail-closed do
  shim.

## Itens intencionalmente nao migrados

- `.env`, variaveis e pacotes sensiveis: permanecem fora do Git.
- `backend/uploads/**`: dados vivos de usuario/projeto, preservados fora do Git.
- Logs e caches, incluindo `.pytest_cache` e `backend/run.err`: runtime, nao
  codigo-fonte.
- `backend.bak/**`: copia operacional antiga, preservada apenas pelo backup.
- `frontend/src/views/Process.vue`: tela legada do estado vivo, substituida no
  Git atual pelo fluxo em `MainView`.
- `patches/apply-max-tokens.sh`: patch manual obsoleto que altera container em
  execucao. Se o limite de tokens precisar mudar, deve virar configuracao ou PR
  normal, nao hot patch pos-start.
- `static/image/**`: assets de exemplo upstream antigos, sem uso no produto
  atual.
- `docker-compose.yml.upstream-DISABLED-*`: copia historica desativada.

## Regra operacional apos o merge

Depois do merge deste PR, o deploy da VPS deve sair de `/opt/mirofish-git`, nao
do diretorio historico `/opt/mirofish`.

Comando operacional esperado dentro de `/opt/mirofish-git`:

```bash
docker compose --env-file .env -f deploy/docker-compose.vps.yaml up -d --build
```

Antes de cada deploy, usar:

```bash
git fetch origin
git pull --ff-only origin main
```

## Garantias mantidas

- O Git continua livre de segredos e dados vivos.
- O estado antigo continua recuperavel pelo backup da VPS.
- O deploy passa a ter fonte unica: GitHub `main` no clone limpo.
- Mudancas futuras devem ser feitas por branch, PR e merge, nunca por patch
  manual direto em container.

## Limpeza operacional posterior

- URL canonica de uso: `https://inteia.com.br/mirofish/`.
- `https://mirofish.inteia.com.br/` deve redirecionar para a URL canonica.
- `https://mirofish.inteia.com.br/api/...` permanece apenas como ponte tecnica
  para a Vercel.
- Diretórios antigos da VPS devem conter `README_DEPLOY_OBSOLETO_NAO_USAR.txt`.
- Compose legados fora de `/opt/mirofish-git` devem permanecer desativados.
- Portas do container MiroFish devem ficar vinculadas a `127.0.0.1`, evitando
  abertura direta por IP publico.
