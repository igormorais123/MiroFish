# Centralizacao GitHub — MiroFish INTEIA

Data: 2026-05-06
Responsavel desta atualizacao: Codex

## Objetivo

Reduzir conflito entre instancias paralelas (Claude Code, Codex, Hermes e trabalho manual) fazendo o GitHub virar o centro operacional para codigo, docs, PRs, checks e deploys.

## Estado confirmado

| Area | Estado |
|------|--------|
| Repositorio oficial | `https://github.com/igormorais123/MiroFish` |
| Branch de producao | `main` |
| Ultimo main confirmado localmente | `e666c7c` |
| PR de reconciliacao Hermes | `#3` — mergeado em `main` |
| PR de governanca Claude/Codex | `#4` — mergeado em `main` |
| PR de centralizacao Codex | `#6` — mergeado em `main` |
| PR de layout Codex | `#5` — aberto para revisao visual |
| GitHub Actions PR #4 | `backend-tests` passou em 2026-05-06 |
| GitHub Actions PR #5 | `backend-tests` passou em 2026-05-06 |
| GitHub Issues | habilitado em 2026-05-06 |
| Issue de controle operacional | `#7` — `ops: fase 2 da centralizacao operacional` |
| Protecao da branch `main` | habilitada; exige PR, `backend-tests` verde e conversas resolvidas |
| CODEOWNERS | proposto em `.github/CODEOWNERS` para marcar responsavel padrao |
| Vercel project | `mirofish-inteia` |
| Vercel project ID | `prj_enAVMOreJOeLH7VFrOzY9UIzF98s` |
| Vercel team/org ID | `team_Af2JN68IUUA7lwsIGKuJiN66` |
| Vercel CLI context | `igormorais123s-projects` |
| Vercel CLI user | `inteia` |
| Vercel direct production URL | `https://mirofish-inteia.vercel.app` |
| Site publico | `https://inteia.com.br/mirofish` |
| API publica correta | `https://inteia.com.br/mirofish/api/...` |

## PRs e controles desta rodada

### PR #3 — fonte unica de verdade

URL: `https://github.com/igormorais123/MiroFish/pull/3`

Status: mergeado em `main`.

Conteudo:
- `docs/ops/FONTE_UNICA_VERDADE_MIROFISH.md`
- `docs/ops/COMANDOS_SEGUROS_MIROFISH.md`
- `docs/ops/RELATORIO_RECONCILIACAO_2026-05-06.md`
- `scripts/mirofish-reconcile-check.sh`

### PR #4 — governanca multi-instancia

URL: `https://github.com/igormorais123/MiroFish/pull/4`

Status: mergeado em `main`.

Conteudo:
- `CLAUDE.md`
- `AGENTS.md`
- referencia no `README.md`
- `docs/ops/VERCEL_DEPLOY.md`
- este relatorio de centralizacao

Uso esperado:
- servir como placa de entrada para todas as instancias.

### PR #6 — registro operacional Codex

URL: `https://github.com/igormorais123/MiroFish/pull/6`

Status: mergeado em `main`.

Conteudo:
- consolidacao do estado GitHub/Vercel;
- referencias cruzadas em `CLAUDE.md`, `AGENTS.md` e `docs/ops/VERCEL_DEPLOY.md`.

### PR #5 — layout do relatorio

URL: `https://github.com/igormorais123/MiroFish/pull/5`

Status: aberto; `backend-tests` passou.

Conteudo:
- split adaptativo no relatorio;
- console inferior compacto;
- painel de relatorio mais denso;
- timeline de geracao mais legivel.

Uso esperado:
- revisar visualmente antes de merge, pois toca somente frontend.

### Issue #7 — fase 2 operacional

URL: `https://github.com/igormorais123/MiroFish/issues/7`

Status: aberta.

Uso esperado:
- concentrar pendencias de VPS, Vercel, CODEOWNERS, seguranca e decisao de merge do PR #5.

## Fluxo obrigatorio daqui em diante

1. Toda instancia comeca em `main` atualizado:

   ```bash
   git fetch origin
   git checkout main
   git pull --ff-only origin main
   ```

2. Toda instancia cria branch propria:

   ```bash
   git checkout -b tipo/slug-curto
   ```

3. Toda mudanca vira commit e push:

   ```bash
   git status -sb
   git diff --stat
   git add caminho/especifico
   git commit -m "tipo: descricao curta"
   git push -u origin HEAD
   ```

4. Toda mudanca entra por PR para `main`.

5. Deploy de producao acontece por merge em `main`, nao por comando solto local.

6. `main` esta protegido no GitHub: PR obrigatorio, `backend-tests` verde e conversas resolvidas antes do merge.

## Vercel

Fonte documentada: [`docs/ops/VERCEL_DEPLOY.md`](VERCEL_DEPLOY.md).

Confirmado localmente em `.vercel/project.json`:

```json
{
  "projectId": "prj_enAVMOreJOeLH7VFrOzY9UIzF98s",
  "orgId": "team_Af2JN68IUUA7lwsIGKuJiN66",
  "projectName": "mirofish-inteia"
}
```

Confirmado por CLI nesta sessao:

```bash
vercel whoami
# inteia

vercel project ls
# contexto: igormorais123s-projects
# projeto: mirofish-inteia
# latest production URL: https://mirofish-inteia.vercel.app

vercel ls mirofish-inteia
# ultimo deployment observado:
# https://mirofish-inteia-d3nk9pteh-igormorais123s-projects.vercel.app
# Status: Ready
# Environment: Production
```

Observacao: a consulta pelo conector Vercel retornou `403 Forbidden` nesta sessao, mas a CLI autenticada funcionou. Para qualquer acao de producao, confirmar por CLI autenticada ou painel web antes de alterar o ambiente.

## Ordem segura de merge/deploy

1. Atualizar todas as instancias:

   ```bash
   git fetch origin
   git checkout main
   git pull --ff-only origin main
   ```

2. Revisar PR #5.
3. Se PR #5 passar visualmente, merge em `main`.
4. Vercel deve publicar producao automaticamente a partir de `main`.
5. VPS so deve ser reconciliada depois do GitHub estar consolidado.

## O que nao fazer

- Nao trabalhar em `main`.
- Nao editar `/opt/mirofish` como fonte primaria.
- Nao usar `git push --force`.
- Nao rodar `vercel --prod` sem aprovacao direta do Igor.
- Nao commitar `.env`, `.vercel/`, `dist/`, uploads, logs vivos ou backups.

## Checklist para qualquer nova instancia

- [ ] Leu `CLAUDE.md`.
- [ ] Leu `AGENTS.md`.
- [ ] Confirmou branch atual com `git status -sb`.
- [ ] Fez `git fetch origin`.
- [ ] Checou PRs abertas no GitHub antes de mexer na mesma area.
- [ ] Criou branch propria.
- [ ] Rodou build/teste aplicavel.
- [ ] Abriu PR com comandos de validacao.
