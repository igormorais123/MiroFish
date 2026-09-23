---
description: Seis usos práticos do JEV como nó de decisão — eval, roteamento de equipe, roteamento de modelos, triagem, benchmark e loop observa-decide-age.
---

# JEV — categoria de skills

O JEV é sempre o mesmo papel: **o ponto do fluxo em que o estado vira decisão**.
Cada skill desta categoria aplica esse papel a um problema diferente:

| Skill | Pergunta que o JEV responde | Saídas |
|-------|-----------------------------|--------|
| `jev-evals` | Ficou bom o suficiente para seguir? | `PASS` · `RETRY` · `HUMAN` |
| `jev-orquestracao-equipe` | Quem trabalha agora? | `RESEARCHER` · `CODER` · `TESTER` · `REVIEWER` · `DONE` |
| `jev-orquestracao-modelos` | Vale gastar inteligência aqui? | `SMALL` · `CODING` · `FRONTIER` |
| `jev-triagem` | O que chegou e qual fluxo nasce disso? | `CRITICAL_BUG` · `SALES_LEAD` · `FEATURE_REQUEST` · `NOISE` |
| `jev-benchmark` | Qual arquitetura funciona melhor sob as mesmas condições? | relatório comparativo |
| `jev-loop-observa-decide-age` | Qual é a próxima ação? | ação de ferramenta · `NEED_USER` · `DONE` |

Regra comum a todas: a decisão do JEV **muda o fluxo**. Nota, rótulo ou
comentário que não altera o próximo passo não é saída válida.
