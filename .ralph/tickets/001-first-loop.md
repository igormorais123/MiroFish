---
id: MF-RL-001
status: done
mode: code
owner: ralphloop
expected_minutes: 30
risk: low
labels: [implantacao, autoresearch, approved-candidate]
---

# Aprovar Mirofish como piloto RalphLoop + AutoResearch

## Intent

Escolher e preparar um projeto existente para receber o metodo depois do sistema de sonhos.

## Acceptance

- [x] Mirofish comparado com Paperclip local.
- [x] Baseline verificado.
- [x] `.ralph`, `runs` e `.autoresearch` criados.
- [x] Metodo adaptado ao dominio Mirofish.
- [x] Primeiro run registrado.

## Required Evidence

- Backend: `171 passed in 4.87s`.
- Frontend: `npm run build` passou.
- Paperclip local visivel nao tinha `.git` nem manifestos.
- Mirofish tem Git, package.json, backend tests, frontend build, roadmap e `backend/autoresearch`.

## Scope

Do:

- Implantar metodo.
- Registrar decisao.
- Nao alterar codigo de produto.

Do not:

- Rodar simulacao longa.
- Usar LLM/Apify/deploy.
- Tocar `.env`.

## Context

Roadmap atual: P0.1 validacao empirica com nova simulacao. Este loop prepara a disciplina antes de gastar recursos.

## Blockers

Nenhum para implantacao. Simulacao real com LLM ativo requer decisao humana.

## Handoff

Proximo ciclo recomendado: `MF-RL-002` fazer assessment de prontidao P0.1 sem executar simulacao longa.

## AutoResearch Signal

method_signal: none
candidate_targets: none
