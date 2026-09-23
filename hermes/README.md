# Skills do Hermes versionadas no GitHub

Este diretório guarda skills do Hermes Agent que rodam na VPS `hermes`. Pela
Regra Zero do `CLAUDE.md`, a skill nasce aqui, passa por Pull Request e só
depois é instalada na VPS. Não edite `~/.hermes/skills/jev/` direto na VPS:
a próxima instalação sobrescreve.

## Categoria `jev` — seis usos práticos do JEV

| Skill | Fluxo de origem | Decisão |
|-------|-----------------|---------|
| [`jev-evals`](skills/jev/jev-evals/SKILL.md) | 1 · Evals | `PASS` · `RETRY` · `HUMAN` |
| [`jev-orquestracao-equipe`](skills/jev/jev-orquestracao-equipe/SKILL.md) | 2 · Orquestração de agentes | próximo papel |
| [`jev-orquestracao-modelos`](skills/jev/jev-orquestracao-modelos/SKILL.md) | 3 · Orquestração de modelos | `SMALL` · `CODING` · `FRONTIER` |
| [`jev-triagem`](skills/jev/jev-triagem/SKILL.md) | 4 · Triagem | categoria + fluxo disparado |
| [`jev-benchmark`](skills/jev/jev-benchmark/SKILL.md) | 5 · Benchmark | hipótese confirmada, refutada ou inconclusiva |
| [`jev-loop-observa-decide-age`](skills/jev/jev-loop-observa-decide-age/SKILL.md) | 6 · Loop agêntico | ação por volta até `DONE` |

Os nomes de diretório evitam os termos `agent`/`agente` de propósito: o
`PowerPersonaCatalog` do backend varre `~/.hermes/skills` e indexaria como
persona qualquer pasta com esses termos.

Scripts auxiliares (só biblioteca padrão do Python):

- `jev-evals/scripts/pre_gate.py` — regras duras antes de gastar modelo.
- `jev-benchmark/scripts/aggregate.py` — tabela comparativa com intervalo de confiança por bootstrap.

## Instalação na VPS `hermes`

Depois do merge em `main`:

```bash
cd /opt/mirofish-git
git fetch origin
git pull --ff-only origin main
bash hermes/install_jev_skills.sh --dry-run
bash hermes/install_jev_skills.sh
```

Se o Hermes roda com outro usuário ou outro diretório, exporte `HERMES_HOME`
antes (padrão: `~/.hermes`). O instalador valida as seis skills, faz backup da
versão anterior em `~/.hermes/skills/.backup-jev-<data>` e copia a categoria.

Confirmação no próprio Hermes:

```bash
hermes skills list | grep jev
```

Em uma conversa, as skills ficam disponíveis como comando: `/jev-evals`,
`/jev-triagem` e assim por diante.

## Validação local

```bash
cd backend && python -m pytest tests/test_hermes_jev_skills.py -q
bash hermes/install_jev_skills.sh --dry-run
```
