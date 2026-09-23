---
name: jev-orquestracao-equipe
description: Roteador de trabalho do JEV entre papéis especializados (RESEARCHER, CODER, TESTER, REVIEWER). Use quando uma issue ou incidente exigir várias etapas e for preciso decidir, a cada rodada, quem trabalha agora com base no estado atual — não em pipeline fixo. Cada papel devolve um novo estado e o JEV decide de novo até DONE ou escalar ao Igor.
version: 1.0.0
author: INTEIA
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [jev, orquestracao, roteamento, subagentes, delegacao]
    category: jev
    related_skills: [jev-evals, jev-orquestracao-modelos, jev-loop-observa-decide-age]
---

# JEV · Orquestração de equipe — "quem trabalha agora?"

```
ISSUE: checkout 500 ──estado atual──► (JEV router) ──► RESEARCHER
                                           ▲      ├──► CODER
                                           │      ├──► TESTER
                                           │      └──► REVIEWER
                                           └── cada papel devolve novo estado
```

Não é pipeline fixo: é decisão baseada no estado. Se o TESTER descobrir que a
causa era outra, o próximo passo pode ser RESEARCHER de novo, e não REVIEWER.

## Quando usar

- Issue, bug ou incidente que não se resolve em um único passo.
- Tarefas em que a ordem das etapas depende do que for descoberto.
- Sempre que o Hermes for delegar a subagentes (`delegate_task`) ou a outra instância (Claude Code, Codex).

## Papéis

| Papel | Entra quando | Entrega (novo estado) |
|-------|--------------|------------------------|
| `RESEARCHER` | causa desconhecida, falta contexto, hipótese sem evidência | hipótese com evidência: arquivo, log, linha, reprodução |
| `CODER` | causa conhecida e plano de correção definido | diff aplicado em branch própria |
| `TESTER` | existe diff não verificado, ou precisa reproduzir o bug | resultado de testes, reprodução confirmada ou refutada |
| `REVIEWER` | diff testado aguardando aprovação | parecer via `jev-evals` (PASS · RETRY · HUMAN) |

## Estado compartilhado

Mantenha um único objeto de estado e atualize-o após cada papel. Nada de estado implícito em conversa.

```json
{
  "issue": "checkout retorna 500 ao aplicar cupom",
  "hypothesis": "cupom expirado gera None em price_calc",
  "evidence": ["logs/app.log:1822 TypeError NoneType"],
  "diff": null,
  "tests": null,
  "review": null,
  "history": [{"role": "RESEARCHER", "result": "hipótese confirmada por log"}],
  "rounds": 1,
  "max_rounds": 8
}
```

## Procedimento

1. **Normalize a entrada** em estado inicial (campos acima, `history` vazio).
2. **Decida o próximo papel** aplicando as regras em ordem; a primeira que casar vence:
   1. `rounds >= max_rounds` → `HUMAN`.
   2. Sem hipótese com evidência → `RESEARCHER`.
   3. Hipótese com evidência e sem diff → `CODER`.
   4. Diff sem testes, ou testes desatualizados em relação ao diff → `TESTER`.
   5. Testes falhando → `CODER` (com a falha anexada), ou `RESEARCHER` se a falha refutar a hipótese.
   6. Testes verdes e sem revisão → `REVIEWER`.
   7. Revisão `PASS` → `DONE`. Revisão `RETRY` → `CODER`. Revisão `HUMAN` → `HUMAN`.
3. **Delegue** passando ao papel só o recorte do estado de que ele precisa e o formato de retorno.
4. **Incorpore o retorno** ao estado, anexe em `history`, incremente `rounds`.
5. **Volte ao passo 2.** Encerre em `DONE` (relate ao Igor) ou `HUMAN` (pergunte ao Igor).

## Contrato de decisão do router

```json
{
  "next_role": "RESEARCHER | CODER | TESTER | REVIEWER | DONE | HUMAN",
  "why": "testes falharam em test_coupon_expired; hipótese continua válida",
  "handoff": {
    "goal": "tratar cupom expirado sem retornar None",
    "inputs": ["backend/app/services/price_calc.py", "saída do pytest"],
    "return_format": "diff + resumo de 3 linhas"
  }
}
```

## Armadilhas

- **Pipeline disfarçado**: sempre RESEARCHER → CODER → TESTER → REVIEWER, sem olhar o estado. Se a ordem nunca muda, o router não está decidindo.
- **Handoff gordo**: mandar a conversa inteira para o subagente. Passe só o recorte e o formato de retorno.
- **Dois CODERS na mesma branch**: siga o `CLAUDE.md` do repositório — uma instância por branch.
- **Retorno sem estado**: papel que responde "feito" sem evidência volta para o mesmo papel.

## Verificação

- `history` mostra a sequência real e o motivo de cada escolha.
- Toda transição para `DONE` passou por `REVIEWER` com `PASS`.
- O limite de rodadas foi respeitado.
