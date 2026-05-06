# AGENTS.md — orientação para agentes (Codex, Cursor, Copilot, etc.)

> Padrão Codex CLI / OpenAI agents. Este arquivo é **espelho do [`CLAUDE.md`](CLAUDE.md)** — leia o CLAUDE.md inteiro, ele é a fonte canônica.

## TL;DR para agentes não-Claude

1. Repo oficial: `https://github.com/igormorais123/MiroFish` (remote `origin`).
2. Branch estável: `main`. **Nunca trabalhe direto em `main`.** Sempre branch nomeada → PR.
3. Frontend: Vue 3 + Vite em `frontend/`. Backend: Flask Python em `backend/`.
4. Deploy frontend: Vercel projeto `mirofish-inteia`, auto-deploy em push pra `main`. Site público: `https://inteia.com.br/mirofish`.
5. Idioma com Igor: português brasileiro. Código/identifiers: inglês.
6. NÃO commitar: `.env`, secrets, `node_modules/`, `dist/`, `frontend/dist/`, `backend/uploads/`, logs vivos, `.vercel/`.
7. Conventional Commits em português: `feat:`, `fix:`, `chore:`, `docs:`, `refactor:`, `test:`, `ci:`.
8. Múltiplas instâncias rodam em paralelo. **Antes de começar**: `git fetch origin && git pull --ff-only origin main && git checkout -b tipo/slug`.
9. Antes de PR: `cd frontend && npm run build` deve passar; `cd backend && python -m pytest tests -q` idealmente passa (se não passar, documente no PR).

## Arquivos canônicos

- [`CLAUDE.md`](CLAUDE.md) — guia completo (regras, comandos, coordenação)
- [`docs/ops/FONTE_UNICA_VERDADE_MIROFISH.md`](docs/ops/FONTE_UNICA_VERDADE_MIROFISH.md) — política operacional
- [`docs/ops/COMANDOS_SEGUROS_MIROFISH.md`](docs/ops/COMANDOS_SEGUROS_MIROFISH.md) — receitas prontas
- [`docs/ops/VERCEL_DEPLOY.md`](docs/ops/VERCEL_DEPLOY.md) — config de deploy

## Branch prefix esperado por agente

| Agente | Prefixo |
|--------|---------|
| Codex CLI | `codex/<slug>` |
| Claude Code | `claude/<slug>` ou `feat/<slug>` |
| Cursor | `cursor/<slug>` ou `feat/<slug>` |
| Igor manual | qualquer (`main` permitido SOMENTE pra hotfix com aprovação) |

## Não fazer

- `git push --force` em branch compartilhada
- `git reset --hard` com trabalho local pendente
- editar `vercel.json`, `.github/workflows/`, `Dockerfile`, `deploy/` sem PR
- aplicar patch direto em `/opt/mirofish` sem refletir no GitHub
- iniciar trabalho na mesma branch que outra instância já abriu
