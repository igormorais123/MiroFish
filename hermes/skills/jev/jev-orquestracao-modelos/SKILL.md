---
name: jev-orquestracao-modelos
description: Roteador de modelos do JEV com orçamento. Use quando uma tarefa for quebrada em subtarefas e for preciso decidir, para cada uma, se vai para modelo barato (SMALL), especialista em código (CODING) ou de fronteira (FRONTIER), controlando o gasto restante. Alocar inteligência é parte da arquitetura, não escolha do "melhor modelo".
version: 1.0.0
author: INTEIA
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [jev, roteamento-de-modelos, custo, orcamento, llm]
    category: jev
    related_skills: [jev-orquestracao-equipe, jev-benchmark]
---

# JEV · Orquestração de modelos — "vale gastar inteligência aqui?"

```
budget US$ 1.00   (restante: US$ 0.73)

SUBTASK ──► JEV model router ──barato──────► SMALL      $
                             ├─especialista─► CODING     $$
                             └─difícil──────► FRONTIER   $$$$

meta de referência: 42 decisões → só 3 escaladas para FRONTIER
```

Não escolha "o melhor modelo". Escolha o **mais barato que resolve**, e escale
só quando a evidência pedir.

## Quando usar

- Execuções longas com muitas chamadas de modelo (relatórios, simulações, análise de lote).
- Qualquer tarefa com orçamento declarado em dólares ou tokens.
- Cron jobs do Hermes que rodam sem supervisão.

## Camadas

A configuração concreta de cada camada vem do ambiente, nunca fixada nesta skill.
No MiroFish os nomes vivem nas variáveis `LLM_MODEL_NAME`, `LLM_AGENT_MODEL`,
`LLM_PREMIUM_MODEL` e `LLM_MODEL_ALIASES` (ver `docs/ops/SEGREDOS_E_AMBIENTES_MIROFISH.md`).

| Camada | Serve para | Sinais de entrada |
|--------|-----------|-------------------|
| `SMALL` | classificar, extrair, resumir, formatar, traduzir, checar sintaxe | saída curta, verificável, sem raciocínio em cadeia |
| `CODING` | escrever ou corrigir código, gerar testes, ler stack trace | arquivo de código envolvido, saída testável |
| `FRONTIER` | arquitetura, ambiguidade real, jurídico ou estratégico com risco, síntese final | múltiplas restrições em conflito, custo de erro alto, falha prévia em camada inferior |

## Procedimento

1. **Abra o livro-caixa** da execução:
   ```json
   {"budget_usd": 1.00, "spent_usd": 0.27, "decisions": 17, "escalations": 1, "reserve_usd": 0.15}
   ```
   `reserve_usd` é o piso que só a síntese final pode consumir.
2. **Para cada subtarefa**, pontue três eixos de 0 a 2:
   - `complexidade` (0 mecânica · 1 exige domínio · 2 exige raciocínio aberto);
   - `custo_do_erro` (0 refaz barato · 1 atrasa · 2 chega ao cliente ou à produção);
   - `verificabilidade` (0 verificável automaticamente · 1 parcialmente · 2 só humano julga).
3. **Mapeie**:
   - soma 0–2 → `SMALL`;
   - soma 3–4, ou subtarefa de código → `CODING`;
   - soma 5–6 → `FRONTIER`.
4. **Regras de escalonamento**:
   - começou em `SMALL` e a saída falhou na verificação → uma tentativa em `CODING`/`FRONTIER`, nunca duas em `SMALL`;
   - `restante - custo_estimado < reserve_usd` → rebaixe uma camada ou pare e avise o Igor;
   - escaladas para `FRONTIER` acima de 10% das decisões → reveja a decomposição, as subtarefas estão grandes demais.
5. **Registre** cada decisão no livro-caixa e reporte o resumo ao final.

## Contrato de decisão

```json
{
  "subtask": "extrair datas das 40 atas",
  "scores": {"complexidade": 0, "custo_do_erro": 1, "verificabilidade": 0},
  "tier": "SMALL",
  "estimated_cost_usd": 0.01,
  "remaining_after_usd": 0.72,
  "escalated_from": null
}
```

Resumo final obrigatório:

```
decisões: 42 · SMALL 31 · CODING 8 · FRONTIER 3
gasto: US$ 0.81 de US$ 1.00 · reserva intacta: sim
```

## Armadilhas

- **Tudo em FRONTIER "por segurança"**: queima orçamento e não melhora subtarefa mecânica.
- **Tudo em SMALL "por economia"**: retrabalho custa mais que a chamada certa.
- **Estimar custo sem medir**: use os tokens reais das respostas para ajustar a estimativa ao longo da execução.
- **Nome de modelo fixado na skill**: modelos mudam; a skill decide a camada, o ambiente resolve o nome.

## Verificação

- Toda escalada para `FRONTIER` tem motivo registrado.
- Orçamento e reserva respeitados.
- A proporção de camadas aparece no relatório final.
