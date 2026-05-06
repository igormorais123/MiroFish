# MiroFish INTEIA — Guia para agentes IA (Claude Code, Codex, Cursor, Copilot)

> Este arquivo é o **ponto de entrada obrigatório** para qualquer instância IA que abrir este repositório. Leia inteiro antes de editar qualquer arquivo. Igor opera múltiplas instâncias em paralelo (PC pessoal, servidor, VPS, browser) — sem coordenação por aqui, ninguém ganha.

## 1. Quem manda

- Repositório oficial: **https://github.com/igormorais123/MiroFish** (remote `origin`)
- Upstream chinês original (NÃO commitar lá): `https://github.com/666ghj/MiroFish.git` (remote `upstream`)
- Branch estável: **`main`** (deploy de produção sai daqui)
- Site público: **https://inteia.com.br/mirofish**
- API pública: `https://inteia.com.br/mirofish/api/...` (NUNCA `inteia.com.br/api/...`)
- Plataforma de deploy frontend: **Vercel** — projeto `mirofish-inteia`. Detalhes em [`docs/ops/VERCEL_DEPLOY.md`](docs/ops/VERCEL_DEPLOY.md).
- Hospedagem backend: VPS, container `mirofish` em `/opt/mirofish/`. Detalhes em [`docs/ops/FONTE_UNICA_VERDADE_MIROFISH.md`](docs/ops/FONTE_UNICA_VERDADE_MIROFISH.md).

## 2. Regra Zero — fonte única de verdade

**Tudo passa pelo GitHub.** Nada é "patch direto na VPS", "edição local sem commit", "branch local que ninguém vê". Toda mudança vira:

1. branch nomeada (`feat/...`, `fix/...`, `chore/...`, `docs/...`)
2. commit assinado
3. push pra `origin`
4. Pull Request pra `main`
5. (após CI passar) merge

Quem aplicar patch direto em produção sem refletir no GitHub está quebrando o sistema para todas as outras instâncias.

## 3. Procedimento obrigatório no início de cada sessão

```bash
git fetch origin
git checkout main
git pull --ff-only origin main
git status -sb        # se houver edits pendentes, INVESTIGUE antes de continuar
git log --oneline -5  # entenda o que outras instâncias fizeram desde sua última sessão
git checkout -b tipo/descricao-curta
```

**Se `git status` mostrar arquivos modificados que você não escreveu**: outra instância está/estava trabalhando aqui. Pare. Pergunte ao Igor (ou faça `git stash push -m "found-on-checkout"` para preservar e investigar).

## 4. Procedimento ao terminar trabalho

```bash
# 4.1 Validar localmente
cd frontend && npm install && npm run build       # frontend deve buildar sem erro
cd ../backend && python -m pytest tests -q        # ou: uv run python -m pytest tests -q

# 4.2 Commit + push
git status -sb
git add caminho/especifico/do/arquivo            # NUNCA git add -A sem revisar
git commit -m "tipo: descrição curta no imperativo"
git push -u origin HEAD

# 4.3 Abrir PR
gh pr create --base main --head $(git branch --show-current) \
  --title "tipo: descrição" \
  --body "## O que muda\n...\n## Por que\n...\n## Como testar\n..."
```

**Se não conseguiu rodar build/teste**: escreva isso explicitamente no corpo do PR (comando tentado, erro, motivo provável, risco).

## 5. Convenção de commits

Prefixo obrigatório (Conventional Commits simplificado):

| Prefixo | Quando |
|---------|--------|
| `feat:` | nova funcionalidade visível ao usuário |
| `fix:` | correção de bug |
| `chore:` | tarefa interna (build, deps, governance) |
| `docs:` | só documentação |
| `refactor:` | sem mudança de comportamento |
| `test:` | só testes |
| `ci:` | GitHub Actions, vercel.json, deploy config |

Mensagem em **português**, voz ativa, ≤72 chars na primeira linha.

## 6. Convenção de branches

- `feat/<slug-curto>` — nova feature
- `fix/<slug-curto>` — bugfix
- `chore/<slug-curto>` — limpeza, governance
- `docs/<slug-curto>` — só doc
- `codex/<slug>` — branch criada por Codex CLI (preservar prefixo)
- `claude/<slug>` — opcional, branch criada por Claude Code

**Nunca trabalhe direto em `main`.** Mesmo para "uma mudancinha pequena".

## 7. Coordenação multi-instância

Igor roda 2+ instâncias IA simultaneamente. Para evitar conflito:

1. **Cada instância em sua própria branch**. Nunca duas instâncias na mesma branch ao mesmo tempo.
2. **Antes de criar branch nova**: `git fetch origin && git branch -r | grep <area>` — veja se já existe branch viva nessa área.
3. **PR pequeno e atômico**. Quanto menor, mais rápido o merge, menor o conflito.
4. **Não faça merge de PR de outra instância sem o Igor pedir.** Espere review.
5. **Se encontrar conflito ao fazer pull**: pare, mostre o conflito ao Igor, não force.
6. **`.vercel/` é local da máquina**: já está no `.gitignore`. Cada instância terá o seu após `vercel link`.

## 8. NÃO fazer (irreversível ou perigoso)

- `git push --force` em `main` (NUNCA)
- `git reset --hard origin/main` se houver trabalho local não commitado
- `git push --force-with-lease` em branch que outra instância pode estar usando
- `vercel --prod` direto sem aprovação do Igor (deploy de produção é via merge em `main`)
- editar `vercel.json`, `.github/workflows/*`, `Dockerfile`, `deploy/` sem PR + review
- commitar `.env`, secrets, tokens, `node_modules/`, `dist/`, `frontend/dist/`, `backend/uploads/`, logs vivos
- editar `/opt/mirofish/` direto na VPS sem fazer commit/PR no GitHub depois

## 9. Stack rápida

- Frontend: **Vue 3 + Vite**, em `frontend/`. Hero/views em `frontend/src/views/`. Tema "paper mode" (fundo creme `#f5f2ea`, paleta dourada `#c9952a`).
- Backend: **Python (Flask)**, em `backend/`. Tests em `backend/tests/`.
- Build: `vercel.json` na raiz manda Vercel rodar `npm install && cd frontend && npm install` e `npm run build`, output em `frontend/dist`.
- Deploy:
  - Frontend → Vercel (auto-deploy em push pra `main`)
  - Backend → VPS manual (ver `docs/ops/`)

## 10. Referências obrigatórias

Antes de mexer em algo grande, leia também:

- [`docs/ops/FONTE_UNICA_VERDADE_MIROFISH.md`](docs/ops/FONTE_UNICA_VERDADE_MIROFISH.md) — política operacional (rotas, VPS, ordem de reconciliação)
- [`docs/ops/COMANDOS_SEGUROS_MIROFISH.md`](docs/ops/COMANDOS_SEGUROS_MIROFISH.md) — comandos prontos pra copiar
- [`docs/ops/VERCEL_DEPLOY.md`](docs/ops/VERCEL_DEPLOY.md) — config Vercel, project ID, env vars
- [`README.md`](README.md) — visão de produto

## 11. Idioma

- **Comunicação com Igor: português brasileiro** (acentos completos, sem ASCII puro).
- **Código, comentários técnicos, identifiers**: inglês.
- **Mensagens de commit, PR, docs internas**: português.

## 12. Quando em dúvida

Pergunte ao Igor antes de:
- mudar comportamento de produção (URLs, endpoints, schema)
- adicionar dependência nova
- mudar branch policy ou CI
- consumir crédito Vercel/API com volume alto
- deletar arquivo, branch ou PR de outra instância
