---
name: jev-evals
description: Portão de avaliação operacional do JEV. Use depois que um coding agent (ou você mesmo) implementar algo e for preciso decidir, com base em diff, testes e logs, se o trabalho segue (PASS), volta para o implementador com instruções precisas (RETRY) ou sobe para o Igor (HUMAN). Não produz nota de 0 a 10; produz uma decisão que muda o fluxo.
version: 1.0.0
author: INTEIA
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [jev, eval, qualidade, code-review, gate]
    category: jev
    related_skills: [jev-orquestracao-equipe, jev-benchmark]
---

# JEV · Evals — "ficou bom o suficiente para seguir?"

```
CODING AGENT ──► diff + testes + logs ──► JEV eval ──► PASS   → segue o fluxo (merge, deploy, próxima tarefa)
     ▲                                          ├────► RETRY  → volta ao implementador com o que corrigir
     └──────────────── RETRY ◄──────────────────┘────► HUMAN  → para e chama o Igor
```

Princípio: **eval operacional > nota de 0 a 10**. O eval não gera só uma nota — ele muda o fluxo.
É no ramo RETRY, que devolve o trabalho ao implementador com instrução acionável, que o valor aparece.

## Quando usar

- Após qualquer implementação feita por coding agent (Claude Code, Codex, subagente do Hermes).
- Antes de abrir ou mesclar Pull Request.
- Quando um cron ou webhook entregar um diff para ser julgado.

## Entradas obrigatórias

Monte o pacote de evidências antes de decidir. Sem evidência, a decisão é `HUMAN`.

1. **Objetivo**: o pedido original (issue, mensagem, critério de aceite).
2. **Diff**: `git diff --stat` e `git diff` da branch contra a base.
3. **Testes**: comando executado, código de saída, resumo de falhas.
4. **Logs**: build, lint, erros de execução relevantes.
5. **Histórico de tentativas**: quantos RETRY já ocorreram nesta tarefa.

Comandos típicos no repositório MiroFish:

```bash
git diff --stat origin/main...HEAD
git diff origin/main...HEAD
cd backend && python -m pytest tests -q; echo "exit=$?"
cd frontend && npm run build; echo "exit=$?"
```

## Procedimento

1. **Pré-portão determinístico** (sem gastar modelo). Rode:
   ```bash
   python3 ~/.hermes/skills/jev/jev-evals/scripts/pre_gate.py evidencias.json
   ```
   O script aplica as regras duras abaixo. Se ele já decidir, respeite e pule para o passo 4.
   A saída é sempre um JSON com `decision`; evidência ilegível, truncada ou mal formada sai como `HUMAN`, nunca como erro.
2. **Avaliação por critério** (só se o pré-portão devolver `EVALUATE`). Verifique, nesta ordem:
   - o diff resolve o objetivo pedido, e não outro;
   - nada fora do escopo foi alterado (arquivos, dependências, configuração de deploy);
   - testes cobrem o comportamento novo ou alterado;
   - não há segredo, token ou arquivo proibido no diff (`.env`, `dist/`, `node_modules/`, `backend/uploads/`);
   - logs não mostram erro silenciado (except vazio, `|| true`, teste pulado).
3. **Decida** com a tabela:

   | Situação | Decisão |
   |----------|---------|
   | Todos os critérios atendidos, testes verdes | `PASS` |
   | Falha concreta e corrigível pelo implementador | `RETRY` |
   | Terceira tentativa sem convergir | `HUMAN` |
   | Mudança em produção, esquema, URL pública, `Dockerfile`, `.github/workflows/`, `deploy/` | `HUMAN` |
   | Evidência ausente ou contraditória | `HUMAN` |
   | Pedido ambíguo (duas leituras válidas do objetivo) | `HUMAN` |

4. **Emita a decisão** no contrato abaixo e aja sobre ela:
   - `PASS` → prossiga (abrir Pull Request, marcar tarefa concluída, liberar próxima etapa).
   - `RETRY` → reenvie ao implementador **apenas** `retry_instructions`, sem reescrever o pedido todo.
   - `HUMAN` → pare, mande ao Igor o resumo e a pergunta objetiva que destrava.

## Contrato de saída

```json
{
  "decision": "PASS | RETRY | HUMAN",
  "attempt": 2,
  "evidence": {
    "tests": "124 passed, 0 failed",
    "build": "ok",
    "diff_scope": "backend/app/services/x.py, backend/tests/test_x.py"
  },
  "failed_criteria": ["testes não cobrem o caso de lista vazia"],
  "retry_instructions": [
    "Adicionar teste para lista vazia em backend/tests/test_x.py",
    "Tratar retorno None em x.py:88 sem mascarar exceção"
  ],
  "human_question": null
}
```

Regras do contrato:
- `retry_instructions` é obrigatório em `RETRY`, com ações verificáveis (arquivo, linha, comportamento).
- `human_question` é obrigatório em `HUMAN`, formulada para ser respondida sem reler a conversa.
- Nunca emita número de nota. Se alguém pedir nota, responda com a decisão e os critérios.

## Armadilhas

- **Nota disfarçada**: "está 8/10, quase lá" não é decisão. Converta em `RETRY` com a lista do que falta.
- **Loop infinito de RETRY**: o limite padrão é 3 tentativas. Na terceira sem convergir, `HUMAN`.
- **Julgar o texto do agente em vez da evidência**: "todos os testes passaram" no relato do agente não vale; vale o código de saída.
- **PASS com escopo inflado**: diff correto mais refatoração não pedida é `RETRY` ("reverter alterações fora do escopo").

## Verificação

- A decisão cita evidência concreta (saída de teste, arquivo do diff).
- Em `RETRY`, cada instrução pode ser checada no próximo ciclo.
- O contador de tentativas foi incrementado e persistido no estado da tarefa.
