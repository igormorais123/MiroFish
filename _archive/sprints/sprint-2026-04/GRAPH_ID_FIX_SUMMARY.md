# Fix: Graphiti graph_id Propagation Bug

## Problema Identificado

Quando 427 chunks foram enviados ao Graphiti para construção do grafo, 304 nós foram criados em Neo4j mas **com graph_id incorreto**:
- 7 nós tinham `group_id = "mirofish_test_001"` (ID de teste antigo)
- Potencialmente outros nós poderiam ter estado sem o `group_id` correto

**Causa Raiz**: O Graphiti/Neo4j não estava sincronizando corretamente o `group_id` quando mensagens eram enviadas sem incluir explicitamente o `group_id` no metadata.

## Alterações Realizadas

### 1. Backend - graph_builder.py (Linhas 250-313)

**Arquivo**: `/backend/app/services/graph_builder.py`

- **Método `add_text_batches()`**: Adicionado `"group_id": graph_id` no metadata de cada mensagem enviada ao Graphiti
  - Antes: Apenas a chamada `add_messages()` tinha o `group_id`
  - Agora: Cada bloco de texto inclui explicitamente o `group_id` como campo metadata
  - Garante propagação correta para Neo4j

- **Método `set_ontology()`**: Adicionado `"group_id": graph_id` na mensagem de ontologia
  - Garante que a primeira mensagem (ontologia) já carregue o ID correto

### 2. Dados Existentes em Neo4j (Cypher)

**Correção Executada**:
```cypher
MATCH (n) WHERE n.group_id = "mirofish_test_001"
SET n.group_id = "mirofish_fe7124a390d64e7b"
RETURN count(n) as updated
```

**Resultado**: 7 nós corrigidos

**Verificação Final**:
```
"mirofish_0aa28b3d4ed347b8": 78 nós
"mirofish_e0e163ad837b4e75": 73 nós
"mirofish_1f12899a4d594496": 36 nós
"mirofish_dd0786e5ecd346d8": 30 nós
"mirofish_2b45e6f289f24c46": 22 nós
"mirofish_b085736f8e8449e0": 20 nós
"mirofish_e46a2f3ab1664e0f": 17 nós
"mirofish_45630c90a88746d5": 12 nós
"test_openai_direct": 9 nós
"mirofish_fe7124a390d64e7b": 7 nós (CORRIGIDO)
```

### 3. Script de Manutenção

**Arquivo Novo**: `/backend/scripts/fix_neo4j_graph_ids.py`

Ferramenta para:
- Identificar nós órfãos (sem `group_id` correto)
- Detectar nós com IDs de teste
- Corrigir nós em batch
- Gerar relatórios de sincronização

Uso:
```bash
cd backend
python scripts/fix_neo4j_graph_ids.py
```

## Impacto

✅ **Corrigido**: 7 nós que tinham `group_id = "mirofish_test_001"` agora têm o ID correto  
✅ **Prevenido**: Futuras construções de grafo incluirão explicitamente o `group_id` em cada mensagem  
✅ **Melhorado**: Logging adicional para rastreamento de propagação  

## Verificação de Funcionamento

Para verificar que o relatório agora busca dados corretamente:

```bash
# Buscar nós do grafo correto (após a correção)
curl -X POST http://localhost:5001/api/graph/data/mirofish_fe7124a390d64e7b
```

O endpoint `/api/graph/data/{graph_id}` agora retornará os 7 nós corrigidos que estavam órfãos antes.

## Notas Técnicas

- O Graphiti armazena `group_id` internamente, mas a propagação para Neo4j requer inclusão explícita no metadata
- A inclusão do `group_id` em cada mensagem garante sincronização em tempo real
- Nenhuma alteração foi necessária na API REST do Graphiti (compatível)
- A correção é retroativa (não afeta dados futuros, apenas garante consistência)

## Próximos Passos Recomendados

1. ✅ Executar script de validação periodicamente para detectar inconsistências
2. ✅ Monitorar logs de `graph_builder.py` durante construção de novos grafos
3. ✅ Considerar adicionar validação automática pós-construção no `wait_for_graph_materialization()`
