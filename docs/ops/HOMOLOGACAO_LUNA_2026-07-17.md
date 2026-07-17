# Homologação GPT-5.6 Luna — 2026-07-17

## Decisão operacional

- Modelo homologado no OmniRoute: `openai/gpt-5.6-luna`.
- O modelo respondeu com HTTP 200 em chamada real mínima.
- `openai/gpt-5.6-luna-pro` respondeu HTTP 404 e não deve ser configurado enquanto o roteador não o disponibilizar.
- Perfil recomendado para o MiroFish: Luna em `LLM_MODEL_NAME`, `LLM_AGENT_MODEL`, `LLM_PREMIUM_MODEL`, `LLM_HELENA_MODEL` e `GRAPHITI_MODEL`.

## Tabela de preço de referência

| Componente | US$ por 1 milhão de tokens |
|---|---:|
| Entrada sem cache | 1,00 |
| Entrada em cache | 0,10 |
| Saída | 6,00 |

O medidor interno conserva o multiplicador operacional INTEIA de 5 vezes e passa a separar entrada sem cache de entrada em cache.

## Recalibração com consumo observado

Janela observada no roteador: 2026-07-10 a 2026-07-17.

- 248 chamadas, sendo 202 bem-sucedidas e 46 com falha.
- 950.254 tokens de entrada.
- 210.814 tokens de saída.
- 28.928 tokens lidos de cache.
- Custo técnico equivalente no Luna: aproximadamente US$ 2,19 para toda a janela.
- Base operacional preservada antes da limpeza: 22 simulações, 12 tentativas de relatório e 7 relatórios concluídos.
- Referência por simulação registrada: aproximadamente US$ 0,10 técnico e US$ 0,50 operacional.
- Referência por relatório concluído, incluindo o peso das falhas: aproximadamente US$ 0,31 técnico e US$ 1,56 operacional.

A interface pública usa a faixa arredondada de US$ 0,10–0,35 de custo técnico e US$ 0,50–1,75 de valor operacional por execução observada. Essa faixa deve ser revista quando houver uma nova amostra representativa com o Luna já ativo em todas as funções.

## Bloqueios encontrados no ensaio de produção

O primeiro ensaio real encontrou dois problemas operacionais que não apareciam no healthcheck:

1. O volume persistente estava sob o UID legado `197608`, enquanto o container roda como `10001:10001`. A criação de projeto falhava com `Permission denied`. A propriedade do volume foi alinhada após backup integral e inventário de permissões.
2. `LLM_BASE_URL` apontava para `172.17.0.1`, ponte anterior do Docker. O MiroFish atual usa outra rede e não alcançava o roteador. A correção permanente usa a rede Docker privada externa `inteia-ai` e o endereço `http://omniroute-inteia:20128/v1`.
3. O Luna rejeitou `temperature=0.3` com HTTP 400 porque aceita somente a temperatura padrão. O cliente passou a omitir `temperature` apenas para a família `gpt-5.6-luna`.

O healthcheck de infraestrutura deve ser complementado por uma chamada LLM mínima, pois frontend, Flask, Graphiti e Neo4j podem estar saudáveis mesmo quando o roteador de IA está inalcançável.
