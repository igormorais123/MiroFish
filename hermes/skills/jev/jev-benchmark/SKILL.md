---
name: jev-benchmark
description: Benchmark de arquiteturas com o JEV. Use quando for preciso provar se uma arquitetura (por exemplo, agente com JEV decidindo) funciona melhor que outra sob as mesmas tarefas e condições, medindo taxa de sucesso, custo, latência, retentativas e intervenção humana. "Arquitetura boa" é hipótese testável; esta skill troca o "achar" por medir.
version: 1.0.0
author: INTEIA
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [jev, benchmark, avaliacao, harness, metricas, experimento]
    category: jev
    related_skills: [jev-evals, jev-orquestracao-modelos]
---

# JEV · Benchmark — "qual arquitetura funciona melhor sob as mesmas condições?"

```
MESMAS TAREFAS ──► TEST HARNESS ──► ARQ. A
(bugs · features                 └─► ARQ. B + JEV
 research · refactor)

medir, não "achar":  ✓ taxa de sucesso · $ custo · ⏱ latência · ↻ retentativas · ☝ intervenção humana
```

Benchmark = repetir + medir com as mesmas condições.

## Quando usar

- Antes de adotar uma mudança de arquitetura (novo roteador, novo modelo padrão, JEV ligado ou desligado).
- Para justificar decisão técnica ao Igor ou a cliente com número, não com impressão.

## Desenho do experimento

1. **Hipótese** escrita antes de rodar: "B + JEV aumenta a taxa de sucesso em pelo menos 10 pontos sem elevar custo médio acima de 20%".
2. **Conjunto de tarefas** fixo e versionado, com mistura declarada: bugs, features, pesquisa, refatoração. Mínimo recomendado: 20 tarefas, 3 repetições por tarefa por arquitetura.
3. **Condições congeladas**: mesmo commit do repositório, mesmo limite de tempo, mesmo orçamento, mesma temperatura, mesmo conjunto de ferramentas. Registre tudo no cabeçalho do resultado.
4. **Critério de sucesso** por tarefa definido antes: testes de aceite verdes via `jev-evals` com decisão `PASS`.
5. **Ordem aleatória** das execuções para diluir efeito de horário e de cache.

## Procedimento

1. Crie o diretório da rodada: `runs/benchmark-AAAAMMDD-slug/` com `tasks.jsonl` e `conditions.json`.
2. Para cada (tarefa, arquitetura, repetição), rode em ambiente limpo e grave uma linha em `results.jsonl`:
   ```json
   {"task_id": "bug-007", "arch": "B+JEV", "rep": 2, "success": true, "cost_usd": 0.042,
    "latency_s": 118.4, "retries": 1, "human_interventions": 0}
   ```
3. Agregue:
   ```bash
   python3 ~/.hermes/skills/jev/jev-benchmark/scripts/aggregate.py runs/benchmark-AAAAMMDD-slug/results.jsonl A
   ```
   O segundo argumento é a arquitetura de controle (base). Sem ele, a base é a primeira arquitetura que aparece no arquivo.
   O script recusa a rodada, com a lista do que falta, quando:
   - alguma linha não traz todos os campos (`task_id`, `arch`, `rep`, `success`, `cost_usd`, `latency_s`, `retries`, `human_interventions`) — métrica ausente não é zero;
   - alguma arquitetura não cobre todas as tarefas, ou alguma tarefa tem repetição faltando ou duplicada.
   Complete ou refaça as execuções faltantes em vez de comparar grades diferentes.
4. Interprete com cuidado:
   - o script reamostra **tarefas**, não execuções, e usa as mesmas tarefas sorteadas para todas as arquiteturas (bootstrap pareado); repetições de uma tarefa não são observações independentes;
   - intervalo pareado da diferença contra a base que contém zero → **sem diferença demonstrada**;
   - olhe custo por sucesso, não só custo médio: arquitetura barata que falha sai cara;
   - intervenção humana pesa mais que latência para o Igor: declare o peso no relatório.
5. Entregue ao Igor: hipótese, condições, tabela agregada, conclusão ("confirmada", "refutada" ou "inconclusiva") e próximo experimento.

## Armadilhas

- **Tarefas escolhidas depois de ver o resultado**: invalida o benchmark. Congele o conjunto antes.
- **Uma repetição só**: variação de modelo engole a diferença. Repita.
- **Contar repetição como amostra nova**: 20 tarefas × 3 repetições são 20 observações para o intervalo, não 60.
- **Mudar duas coisas ao mesmo tempo** (modelo e roteador): não se sabe o que causou o efeito.
- **Declarar vencedor com empate estatístico**: diga "inconclusivo" e aumente a amostra.

## Verificação

- `conditions.json` existe e é idêntico para as duas arquiteturas.
- O número de linhas em `results.jsonl` é tarefas × arquiteturas × repetições.
- O relatório traz as cinco métricas, o intervalo da taxa de sucesso e o intervalo pareado da diferença.
