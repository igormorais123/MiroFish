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
| Ultimo main confirmado localmente | `fcc0606` |
| PR de governanca | `#4` — `chore/multi-instance-governance` |
| PR de layout Codex | `#5` — `feat/report-split-adaptive` |
| GitHub Actions PR #4 | `backend-tests` passou em 2026-05-06 |
| GitHub Actions PR #5 | `backend-tests` passou em 2026-05-06 |
| Vercel project | `mirofish-inteia` |
| Vercel project ID | `prj_enAVMOreJOeLH7VFrOzY9UIzF98s` |
| Vercel team/org ID | `team_Af2JN68IUUA7lwsIGKuJiN66` |
| Site publico | `https://inteia.com.br/mirofish` |
| API publica correta | `https://inteia.com.br/mirofish/api/...` |

## PRs abertos nesta rodada

### PR #4 — governanca multi-instancia

URL: `https://github.com/igormorais123/MiroFish/pull/4`

Conteudo:
- `CLAUDE.md`
- `AGENTS.md`
- referencia no `README.md`
- `docs/ops/VERCEL_DEPLOY.md`
- este relatorio de centralizacao

Uso esperado:
- mergear antes de novas mudancas grandes;
- servir como placa de entrada para todas as instancias.

### PR #5 — layout do relatorio

URL: `https://github.com/igormorais123/MiroFish/pull/5`

Conteudo:
- split adaptativo no relatorio;
- console inferior compacto;
- painel de relatorio mais denso;
- timeline de geracao mais legivel.

Uso esperado:
- revisar depois da PR #4 ou em paralelo, pois toca somente frontend.

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

Observacao: a consulta pelo conector Vercel retornou `403 Forbidden` nesta sessao. Portanto, qualquer acao no painel Vercel deve ser confirmada por CLI autenticada (`vercel whoami`, `vercel project ls`, `vercel deployments ls`) ou pelo painel web antes de alterar producao.

## Ordem segura de merge/deploy

1. Revisar e mergear PR #4 primeiro.
2. Atualizar todas as instancias:

   ```bash
   git fetch origin
   git checkout main
   git pull --ff-only origin main
   ```

3. Revisar PR #5.
4. Se PR #5 passar, merge em `main`.
5. Vercel deve publicar producao automaticamente a partir de `main`.
6. VPS so deve ser reconciliada depois do GitHub estar consolidado.

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
