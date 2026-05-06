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

## Commit seguro

```bash
git status -sb
git diff --stat
git add caminho/do/arquivo
git commit -m "fix: descreve a mudança"
git push -u origin HEAD
```

## Links oficiais

- Site correto: https://inteia.com.br/mirofish
- API correta: https://inteia.com.br/mirofish/api/simulation/history?limit=1
- GitHub: https://github.com/igormorais123/MiroFish
- Pull requests: https://github.com/igormorais123/MiroFish/pulls
- Actions: https://github.com/igormorais123/MiroFish/actions

## Aviso para agentes

Não use `https://inteia.com.br/api/...` para MiroFish.
Use sempre `/mirofish/api/...` no ambiente público.

Não use `mirofish.inteia.com.br` como referência enquanto o subdomínio estiver legado.
