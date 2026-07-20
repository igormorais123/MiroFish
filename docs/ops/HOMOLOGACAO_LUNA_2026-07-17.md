# Homologação GPT-5.6 Luna — 2026-07-17 a 2026-07-20

## Estado operacional atual — 2026-07-20

- Modelo ativo em backend, agentes, Helena e Graphiti: `codex/gpt-5.6-luna`.
- Autenticação upstream: OAuth da assinatura ChatGPT/Codex armazenado no cofre privado do OmniRoute. A chave que o MiroFish usa serve apenas para autorizar o gateway interno e não é uma chave paga da API OpenAI.
- Roteador homologado: OmniRoute `3.8.48`, com cliente Codex `0.144.6`.
- Esforço homologado: `LUNA_REASONING_EFFORT=low`; relatórios permanecem em `REPORT_SECTION_WORKERS=1`.
- Prova real em produção: HTTP 200, modelo solicitado `codex/gpt-5.6-luna`, modelo efetivo `gpt-5.6-luna`, sem combo ou fallback intermediário.
- Prova pelo cliente interno do MiroFish: resposta `MIROFISH_LUNA_OK` e telemetria efetiva `gpt-5.6-luna`.
- Serviços validados após recriação: `omniroute-inteia`, `mirofish-inteia` e `mirofish-graphiti` saudáveis.
- Backup verificável e material de restauração: `/root/backups/mirofish-codex-luna-20260720T030700Z`; o container anterior do roteador foi preservado parado como `omniroute-inteia-rollback-20260720T030700Z`.

O bloqueio de 17 de julho tinha duas causas. A versão antiga do OmniRoute ainda não catalogava Luna e dois padrões persistentes (`*code*` e `*codex*`) capturavam rotas explícitas `codex/...`, enviando-as ao combo `coding-power` baseado em GPT-5.5. A atualização adicionou o catálogo Luna; os padrões foram estreitados para os aliases exatos `code` e `codex`, preservando os atalhos sem reescrever nomes de provedor.

Toda alteração futura de modelo deve executar `backend/scripts/check_llm_model.py`. A checagem compara o campo `model` da resposta com o valor esperado e falha se um alias voltar a esconder fallback.

## Decisão histórica — 2026-07-17

- O caminho Luna continua preparado no código, mas a credencial OpenAI disponível no OmniRoute expirou durante o ensaio completo e o catálogo da assinatura Codex não expõe a Luna.
- Modelo operacional estável da assinatura em 2026-07-17: `codex/gpt-5.5`, sem cobrança marginal de API além da assinatura existente.
- Não usar o alias `codex/gpt-5.6-luna` como prova de Luna: o roteador o resolve para GPT-5.5 e a resposta identifica corretamente o modelo real.
- `openai/gpt-5.6-luna-pro` respondeu HTTP 404 e não deve ser configurado enquanto o roteador não o disponibilizar.
- Perfil recomendado naquele momento: `codex/gpt-5.5` em `LLM_MODEL_NAME`, `LLM_AGENT_MODEL`, `LLM_PREMIUM_MODEL`, `LLM_HELENA_MODEL` e `GRAPHITI_MODEL`. Essa orientação foi superada pela homologação real de 20 de julho.

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
4. Em uma ontologia real, o esforço de raciocínio padrão consumiu todos os 4.096 tokens de saída sem produzir conteúdo. A chamada controlada confirmou que `reasoning_effort=low` é aceito; `minimal` não é. MiroFish e Graphiti agora usam `low` por padrão, configurável por `LUNA_REASONING_EFFORT`, reservando saída para JSON sem trocar de modelo.
5. O cliente OpenAI interno da imagem Graphiti enviava `temperature=0` e `max_tokens`, ambos incompatíveis com a família Luna. O adaptador montado pelo deploy passa a omitir temperatura, usar `max_completion_tokens` e aplicar o esforço de raciocínio homologado.
6. O provedor Codex pode devolver SSE mesmo com `stream=false`; o cliente unificado agora agrega os deltas, uso de tokens e término antes de entregar a resposta ao restante do sistema.
7. Dois workers Gunicorn mantinham gerenciadores de tarefa independentes: um worker podia marcar como interrompida uma tarefa criada pelo outro. Produção usa um worker com quatro threads.
8. O Graphiti tentava gerar embeddings no OmniRoute sem credencial OpenAI válida. LLM e embeddings foram separados; o Graphiti usa `nomic-embed-text` no Ollama local, sem custo de API.

O healthcheck de infraestrutura deve ser complementado por uma chamada LLM mínima, pois frontend, Flask, Graphiti e Neo4j podem estar saudáveis mesmo quando o roteador de IA está inalcançável.
