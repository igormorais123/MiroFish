---
name: jev-loop-observa-decide-age
description: Loop observa-decide-age do JEV para tarefas de várias etapas com ferramentas e interação com o usuário (agendar consulta, reservar, comprar, preencher cadastro, pesquisar e confirmar). Use quando o próximo passo não puder ser totalmente pré-programado e depender do resultado da última ação. A cada volta o JEV lê o estado, escolhe uma ação (ferramenta, perguntar ao usuário ou encerrar), observa o resultado e atualiza o estado até DONE.
version: 1.0.0
author: INTEIA
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [jev, loop, ferramentas, agendamento, estado, react]
    category: jev
    related_skills: [jev-orquestracao-equipe, jev-orquestracao-modelos]
---

# JEV · Loop observa-decide-age — exemplo: agendar uma consulta

O agente não executa roteiro fixo: observa o resultado e decide o próximo passo.

```
REQUEST "Agende um dermatologista semana que vem à tarde."
  │ entra no loop
  ▼
1. ESTADO ─decide─► JEV: próxima ação? ─SEARCH_SLOT─► 2. TOOL CALL buscar disponibilidade
                         ▲                                     │ resultado da ferramenta
                         │ LOOP: resultado vira novo estado    ▼
                         └──────────────────────────── 3. OBSERVAÇÃO  Ter 14:00 Dra. Ana · Qua 16:30 Dr. Paulo · Qui 15:00 Dra. Bia
                                                               │ atualiza memória
4. NOVO ESTADO "há horários" ─► JEV: próximo passo? ─NEED_USER─► 5. ASK USER "Encontrei 3 horários. Qual prefere?"
                                                               │ "Quarta às 16:30." (nova observação)
6. ESTADO ATUALIZADO "falta efetivar reserva" ─► JEV ─BOOK─► 7. TOOL CALL book_appointment(Qua 16:30, Dr. Paulo)
                                                               │
8. OBSERVAÇÃO status: CONFIRMED, protocolo ─► JEV: terminou? ─DONE─► 9. RESPOSTA FINAL "Consulta confirmada para quarta às 16:30."

se NÃO houver horários → mudar filtros / buscar outra clínica / tentar outra ferramenta
ciclo: OBSERVE → DECIDE → ACT → OBSERVE ↻ repete até DONE
```

## Quando usar

- Pedido com objetivo claro, mas caminho dependente de resposta de sistemas externos.
- Fluxos que exigem confirmação do usuário antes de ação com efeito real (reservar, pagar, enviar, publicar).

## Estado do loop

```json
{
  "goal": "consulta com dermatologista",
  "constraints": {"period": "próxima semana", "shift": "tarde"},
  "context": {"user_timezone": "America/Sao_Paulo"},
  "observations": [],
  "pending": "encontrar horários",
  "tried": [],
  "step": 0,
  "max_steps": 12
}
```

## Ações permitidas ao JEV

| Ação | Quando | Efeito |
|------|--------|--------|
| `TOOL:<nome>` | falta informação obtível por ferramenta, ou é hora de executar | chama a ferramenta e anexa o resultado em `observations` |
| `NEED_USER` | há escolha que só o usuário pode fazer, ou ação irreversível a confirmar | pergunta objetiva com opções numeradas |
| `REPLAN` | ferramenta falhou ou voltou vazia | muda filtros, fonte ou ferramenta; registra em `tried` |
| `DONE` | objetivo cumprido **e** confirmado por observação (status, protocolo) | resposta final ao usuário |
| `HUMAN` | `step >= max_steps` ou erro persistente | relata o que foi tentado e pede direção |

## Procedimento

1. **Monte o estado inicial** a partir do pedido: objetivo, restrições explícitas, contexto conhecido.
2. **Decida** uma única ação por volta, usando o contrato abaixo. Justifique pela diferença entre `goal` e estado atual.
3. **Aja** e **observe**: grave a saída bruta da ferramenta ou a resposta do usuário em `observations`.
4. **Atualize** `pending` e `step`. Nunca apague observações anteriores.
5. **Repita** até `DONE` ou `HUMAN`.

## Contrato de decisão por volta

```json
{
  "step": 3,
  "state_gap": "horário escolhido; falta efetivar a reserva",
  "action": "TOOL:book_appointment",
  "args": {"slot": "quarta 16:30", "doctor": "Dr. Paulo"},
  "requires_confirmation": false,
  "stop_if": "status != CONFIRMED → REPLAN"
}
```

## Regras duras

- Ação com efeito real (reservar, pagar, enviar mensagem, publicar) exige confirmação explícita do usuário no estado, salvo autorização permanente registrada.
- `DONE` só com prova observada (status `CONFIRMED`, protocolo, identificador). "Deve ter dado certo" não encerra o loop.
- Ferramenta vazia duas vezes com os mesmos argumentos → `REPLAN` obrigatório, nunca terceira chamada igual.

## Armadilhas

- **Roteiro disfarçado**: decidir todas as ações no início e só executá-las. Se o resultado não muda o próximo passo, não há loop.
- **Perguntar demais**: `NEED_USER` para algo que uma ferramenta responde.
- **Perguntar de menos**: reservar o primeiro horário sem o usuário escolher.
- **Perder o protocolo**: a resposta final deve repetir o identificador de confirmação observado.

## Verificação

- `observations` contém cada resultado de ferramenta e cada resposta do usuário, em ordem.
- A resposta final cita o dado confirmado (data, hora, responsável, protocolo).
- Nenhuma ação irreversível ocorreu sem confirmação registrada.
