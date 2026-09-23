---
name: jev-triagem
description: Triagem do JEV para entradas misturadas (email, bug, lead, alerta de monitoramento, mensagem de Telegram ou WhatsApp). Use quando chegar qualquer demanda não classificada e for preciso decidir a categoria e, principalmente, disparar o fluxo correspondente — incidente, CRM com follow-up ou backlog. O rótulo sozinho vale pouco; o valor está no que acontece depois.
version: 1.0.0
author: INTEIA
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [jev, triagem, classificacao, incidente, crm, backlog]
    category: jev
    related_skills: [jev-orquestracao-equipe, jev-orquestracao-modelos]
---

# JEV · Triagem — "o que chegou e qual fluxo nasce disso?"

```
chega tudo misturado
  email ─┐
  bug ───┤                     ┌─► CRITICAL BUG    → fluxo de incidente
  lead ──┼──► JEV triagem ─────┼─► SALES LEAD      → CRM + follow-up
  alerta ┘                     └─► FEATURE REQUEST → backlog
```

## Quando usar

- Caixa de entrada, canal do Hermes (Telegram, Discord, WhatsApp, email) ou webhook recebendo itens variados.
- Cron de varredura periódica ("o que chegou desde a última execução?").

## Categorias e fluxo disparado

| Categoria | Critério | Ação obrigatória |
|-----------|----------|------------------|
| `CRITICAL_BUG` | produção fora, erro 5xx, perda de dado, segurança, `https://inteia.com.br/mirofish` degradado | abrir incidente: avisar o Igor na hora, coletar evidência (`/mirofish/health/public`, logs do container `mirofish-inteia`), acionar `jev-orquestracao-equipe` |
| `SALES_LEAD` | interesse comercial, pedido de proposta, contato institucional | registrar no CRM (ou planilha de leads), rascunhar resposta, agendar follow-up em 2 dias úteis |
| `FEATURE_REQUEST` | pedido de melhoria sem urgência | criar item de backlog (issue no GitHub com rótulo `enhancement`), vincular à origem |
| `NOISE` | spam, notificação automática sem ação, duplicata | arquivar e registrar contagem; não notificar |

Prioridade quando um item couber em mais de uma categoria: `CRITICAL_BUG` > `SALES_LEAD` > `FEATURE_REQUEST` > `NOISE`.

## Procedimento

1. **Normalize** cada item: origem, remetente, horário, assunto, corpo, anexos, identificador externo.
2. **Deduplique** por identificador externo e por semelhança de assunto nas últimas 24 horas. Duplicata de incidente aberto vira comentário no incidente, não incidente novo.
3. **Classifique** com modelo `SMALL` (ver `jev-orquestracao-modelos`). Se a confiança for menor que 0,7, reclassifique em camada superior. Se continuar abaixo, marque `needs_human`.
4. **Dispare o fluxo** da tabela. A triagem só termina quando a ação de destino foi executada ou agendada.
5. **Registre** o lote no contrato abaixo e mande ao Igor o resumo apenas se houver `CRITICAL_BUG`, `SALES_LEAD` ou `needs_human`.

## Contrato de saída (por item)

```json
{
  "source": "email",
  "external_id": "msg-18c2f",
  "category": "CRITICAL_BUG",
  "confidence": 0.93,
  "summary": "checkout retorna 500 desde 14:02",
  "workflow": "incident",
  "action_taken": "incidente aberto; Igor notificado no Telegram",
  "follow_up_at": null,
  "needs_human": false
}
```

## Armadilhas

- **Rótulo sem ação**: classificar e parar. O item só está triado quando o fluxo de destino andou.
- **Alarme em excesso**: notificar o Igor por `FEATURE_REQUEST` ou `NOISE` treina ele a ignorar o canal.
- **Lead esquecido**: `SALES_LEAD` sem `follow_up_at` é falha de triagem.
- **Resposta automática ao remetente** sem aprovação: rascunhe, não envie, salvo regra explícita do Igor.

## Verificação

- Cada item tem categoria, ação executada e, quando cabível, data de follow-up.
- Nenhum incidente duplicado no lote.
- Contagem por categoria bate com o total recebido.
