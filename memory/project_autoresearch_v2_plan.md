---
name: AutoResearch v2 Implementation Plan
description: Plano de 7 fases (23-32h) para evoluir AutoResearch de hill climbing para sistema evolucionario com memoria, populacao, corpus adversarial e automacao
type: project
---

Plano salvo em `backend/autoresearch/PLANO_IMPLANTACAO.md` com 7 fases:
1. Memoria cross-session + ranking OPRO (2-3h) — sem dependencia
2. Busca populacional + operadores evolutivos (4-6h) — dep: F1
3. Avaliacao paralela + MAB adaptativo (3-4h) — dep: F2
4. Corpus adversarial (3-4h) — sem dependencia (paralelo com F1)
5. Curriculum + SA + TextGrad-lite (4-5h) — dep: F2, F4
6. Transfer entre alvos + PromptBreeder (4-6h) — dep: F1-F3
7. Automacao cron + dashboard HTML (3-4h) — dep: todas

**Why:** Sistema atual (v1) e hill climbing manual sem memoria entre sessoes. Pesquisa mostrou que OPRO, PBT, PromptBreeder e TextGrad oferecem ganhos concretos.
**How to apply:** Executar fases sequencialmente (1→2→3 como backbone, 4 em paralelo com 1). Meta: F1 hookify > 0.99, custo ~$25/mes, runs overnight autonomas.

Fontes: Karpathy autoresearch, Agent Zero (agent0ai), OPRO (DeepMind), DSPy MIPROv2 (Stanford), TextGrad (Zou), PromptBreeder (DeepMind), PBT (DeepMind).
