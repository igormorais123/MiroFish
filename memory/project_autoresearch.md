---
name: AutoResearch INTEIA Framework
description: Framework de otimizacao autonoma baseado no Karpathy autoresearch adaptado ao ecossistema INTEIA com 4 alvos de otimizacao
type: project
---

Framework AutoResearch implementado em `backend/autoresearch/` com 4 alvos:
1. Hookify Rules (F1 macro) — baseline 0.8832 → otimizado manualmente 0.9705, zero custo eval
2. Advogado Sobre-Humano (skill prompt) — corpus 20 casos juridicos
3. Genetic Copy (meta-otimizacao GA) — zero custo eval
4. Frontend Performance (bundle size + build time)

**Why:** Andrej Karpathy demonstrou que loops autonomos de experimentacao geram 15+ melhorias overnight. O ecossistema INTEIA tem assets mensuraveis (skills, regex, GA, frontend) ideais para essa abordagem.

**How to apply:** Rodar via CLI: `python -m backend.autoresearch.cli run --target hookify --budget 5`. Cada alvo tem seu evaluator com metricas reais (F1, composite score, fitness, bundle size). Hookify e o primeiro alvo porque eval e gratuita (regex puro).
