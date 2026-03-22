"""
Servico de geracao de ontologia
Interface 1: Analisa conteudo textual e gera definicoes de tipos de entidades e relacoes adequadas para simulacao social
"""

import json
from typing import Dict, Any, List, Optional
from ..utils.llm_client import LLMClient


# Prompt de sistema para geracao de ontologia
ONTOLOGY_SYSTEM_PROMPT = """Voce e um especialista profissional em design de ontologias para grafos de conhecimento. Sua tarefa e analisar o conteudo textual fornecido e as necessidades de simulacao, projetando tipos de entidades e tipos de relacoes adequados para **simulacao de opiniao publica em midias sociais**.

IMPORTANTE: Todos os nomes de entidades, relações, descrições e atributos devem ser em português brasileiro. NÃO use nomes em inglês.

**Importante: Voce deve gerar dados em formato JSON valido, sem nenhum outro conteudo.**

## Contexto da Tarefa Principal

Estamos construindo um **sistema de simulacao de opiniao publica em midias sociais**. Neste sistema:
- Cada entidade e uma "conta" ou "sujeito" que pode se manifestar, interagir e disseminar informacoes em midias sociais
- As entidades influenciam umas as outras, compartilham, comentam e respondem entre si
- Precisamos simular as reacoes de cada parte envolvida em eventos de opiniao publica e os caminhos de disseminacao de informacao

Portanto, **as entidades devem ser sujeitos reais que podem se manifestar e interagir em midias sociais**:

**Podem ser**:
- Individuos especificos (figuras publicas, partes envolvidas, formadores de opiniao, especialistas, cidadaos comuns)
- Empresas e companhias (incluindo suas contas oficiais)
- Organizacoes e instituicoes (universidades, associacoes, ONGs, sindicatos etc.)
- Orgaos governamentais, agencias reguladoras
- Veiculos de midia (jornais, emissoras de TV, midia independente, portais)
- As proprias plataformas de midias sociais
- Representantes de grupos especificos (como associacoes de ex-alunos, fas, grupos de defesa de direitos etc.)

**Nao podem ser**:
- Conceitos abstratos (como "opiniao publica", "emocao", "tendencia")
- Temas/topicos (como "integridade academica", "reforma educacional")
- Pontos de vista/posicionamentos (como "apoiadores", "opositores")

## Formato de Saida

Gere o resultado em formato JSON com a seguinte estrutura:

```json
{
    "entity_types": [
        {
            "name": "Nome do tipo de entidade (portugues, PascalCase, ex: Estudante, Professor, OrgaoGovernamental)",
            "description": "Descricao breve (portugues, no maximo 100 caracteres)",
            "attributes": [
                {
                    "name": "nome_atributo (portugues, snake_case)",
                    "type": "text",
                    "description": "Descricao do atributo"
                }
            ],
            "examples": ["Exemplo de entidade 1", "Exemplo de entidade 2"]
        }
    ],
    "edge_types": [
        {
            "name": "NOME_TIPO_RELACAO (portugues, UPPER_SNAKE_CASE, ex: APOIA, TRABALHA_EM, COMPETE_COM)",
            "description": "Descricao breve (portugues, no maximo 100 caracteres)",
            "source_targets": [
                {"source": "TipoEntidadeOrigem", "target": "TipoEntidadeDestino"}
            ],
            "attributes": []
        }
    ],
    "analysis_summary": "Breve analise do conteudo textual (em portugues)"
}
```

## Diretrizes de Design (Extremamente Importante!)

### 1. Design de Tipos de Entidades - Obrigatorio seguir rigorosamente

**Requisito de quantidade: exatamente 10 tipos de entidade**

**Requisito de estrutura hierarquica (deve incluir tanto tipos especificos quanto tipos genericos)**:

Seus 10 tipos de entidade devem conter as seguintes camadas:

A. **Tipos genericos (obrigatorios, devem ser os 2 ultimos da lista)**:
   - `Pessoa`: Tipo generico para qualquer pessoa fisica. Quando uma pessoa nao se encaixa em nenhum tipo mais especifico, deve ser classificada aqui.
   - `Organizacao`: Tipo generico para qualquer organizacao. Quando uma organizacao nao se encaixa em nenhum tipo mais especifico, deve ser classificada aqui.

B. **Tipos especificos (8, projetados com base no conteudo textual)**:
   - Projete tipos mais especificos para os principais papeis presentes no texto
   - Exemplo: se o texto envolve eventos academicos, pode ter `Estudante`, `Professor`, `Universidade`
   - Exemplo: se o texto envolve eventos empresariais, pode ter `Empresa`, `Executivo`, `Funcionario`

**Por que tipos genericos sao necessarios**:
- No texto aparecem diversas pessoas, como "professor do ensino medio", "transeunte", "um internauta"
- Se nao houver um tipo especifico correspondente, devem ser classificadas em `Pessoa`
- Da mesma forma, pequenas organizacoes, grupos temporarios etc. devem ser classificados em `Organizacao`

**Principios de design dos tipos especificos**:
- Identifique os tipos de papeis que aparecem com frequencia ou sao fundamentais no texto
- Cada tipo especifico deve ter limites claros, evitando sobreposicao
- A description deve explicar claramente a diferenca entre este tipo e o tipo generico

### 2. Design de Tipos de Relacoes

- Quantidade: 6 a 10
- As relacoes devem refletir conexoes reais nas interacoes em midias sociais
- Garanta que os source_targets das relacoes abranjam os tipos de entidade definidos

### 3. Design de Atributos

- 1 a 3 atributos-chave por tipo de entidade
- **Atencao**: nomes de atributos nao podem usar `name`, `uuid`, `group_id`, `created_at`, `summary` (estes sao palavras reservadas do sistema)
- Recomendados: `full_name`, `title`, `role`, `position`, `location`, `description` etc.

## Referencia de Tipos de Entidade

**Categoria Individual (especificos)**:
- Estudante: Estudante
- Professor: Professor/Academico
- Jornalista: Jornalista
- Celebridade: Celebridade/Influenciador
- Executivo: Executivo/Alta gestao
- Funcionario: Funcionario publico/Politico
- Advogado: Advogado
- Medico: Medico

**Categoria Individual (generico)**:
- Pessoa: Qualquer pessoa fisica (usar quando nao se encaixa nos tipos especificos acima)

**Categoria Organizacional (especificos)**:
- Universidade: Universidade/Instituicao de ensino superior
- Empresa: Empresa
- OrgaoGovernamental: Orgao governamental
- VeiculoDeMidia: Veiculo de midia
- Hospital: Hospital
- Escola: Escola de ensino basico/medio
- ONG: Organizacao nao governamental

**Categoria Organizacional (generico)**:
- Organizacao: Qualquer organizacao (usar quando nao se encaixa nos tipos especificos acima)

## Referencia de Tipos de Relacoes

- TRABALHA_PARA: Trabalha em
- ESTUDA_EM: Estuda em
- AFILIADO_A: Vinculado a
- REPRESENTA: Representa
- REGULAMENTA: Regula/Fiscaliza
- REPORTA_SOBRE: Reporta/Cobre
- COMENTA_SOBRE: Comenta sobre
- RESPONDE_A: Responde a
- APOIA: Apoia
- SE_OPOE_A: Se opoe a
- COLABORA_COM: Colabora com
- COMPETE_COM: Compete com
"""


class OntologyGenerator:
    """
    Gerador de ontologia
    Analisa conteudo textual e gera definicoes de tipos de entidades e relacoes
    """

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm_client = llm_client or LLMClient()

    def generate(
        self,
        document_texts: List[str],
        simulation_requirement: str,
        additional_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Gera a definicao de ontologia

        Args:
            document_texts: Lista de textos dos documentos
            simulation_requirement: Descricao dos requisitos de simulacao
            additional_context: Contexto adicional

        Returns:
            Definicao de ontologia (entity_types, edge_types etc.)
        """
        # Construir mensagem do usuario
        user_message = self._build_user_message(
            document_texts,
            simulation_requirement,
            additional_context
        )

        messages = [
            {"role": "system", "content": ONTOLOGY_SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ]

        # Chamar o LLM
        result = self.llm_client.chat_json(
            messages=messages,
            temperature=0.3,
            max_tokens=4096
        )

        # Validar e pos-processar
        result = self._validate_and_process(result)

        return result

    # Tamanho maximo do texto enviado ao LLM (50 mil caracteres)
    MAX_TEXT_LENGTH_FOR_LLM = 50000

    def _build_user_message(
        self,
        document_texts: List[str],
        simulation_requirement: str,
        additional_context: Optional[str]
    ) -> str:
        """Constroi a mensagem do usuario"""

        # Combinar textos
        combined_text = "\n\n---\n\n".join(document_texts)
        original_length = len(combined_text)

        # Se o texto ultrapassar 50 mil caracteres, truncar (afeta apenas o conteudo enviado ao LLM, nao a construcao do grafo)
        if len(combined_text) > self.MAX_TEXT_LENGTH_FOR_LLM:
            combined_text = combined_text[:self.MAX_TEXT_LENGTH_FOR_LLM]
            combined_text += f"\n\n...(texto original com {original_length} caracteres, foram extraidos os primeiros {self.MAX_TEXT_LENGTH_FOR_LLM} caracteres para analise de ontologia)..."

        message = f"""## Requisitos de Simulacao

{simulation_requirement}

## Conteudo do Documento

{combined_text}
"""

        if additional_context:
            message += f"""
## Observacoes Adicionais

{additional_context}
"""

        message += """
Com base no conteudo acima, projete tipos de entidades e tipos de relacoes adequados para simulacao de opiniao publica em midias sociais.

**Regras obrigatorias**:
1. Devem ser exatamente 10 tipos de entidade
2. Os 2 ultimos devem ser tipos genericos: Pessoa (generico para individuos) e Organizacao (generico para organizacoes)
3. Os 8 primeiros sao tipos especificos projetados com base no conteudo textual
4. Todos os tipos de entidade devem ser sujeitos reais capazes de se manifestar, nao conceitos abstratos
5. Nomes de atributos nao podem usar palavras reservadas como name, uuid, group_id; use full_name, org_name etc.
"""

        return message

    def _validate_and_process(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Valida e pos-processa o resultado"""

        # Garantir que os campos obrigatorios existam
        if "entity_types" not in result:
            result["entity_types"] = []
        if "edge_types" not in result:
            result["edge_types"] = []
        if "analysis_summary" not in result:
            result["analysis_summary"] = ""

        # Validar tipos de entidade
        for entity in result["entity_types"]:
            if "attributes" not in entity:
                entity["attributes"] = []
            if "examples" not in entity:
                entity["examples"] = []
            # Garantir que description nao ultrapasse 100 caracteres
            if len(entity.get("description", "")) > 100:
                entity["description"] = entity["description"][:97] + "..."

        # Validar tipos de relacao
        for edge in result["edge_types"]:
            if "source_targets" not in edge:
                edge["source_targets"] = []
            if "attributes" not in edge:
                edge["attributes"] = []
            if len(edge.get("description", "")) > 100:
                edge["description"] = edge["description"][:97] + "..."

        # Limite da API Zep: maximo 10 tipos de entidade customizados, maximo 10 tipos de aresta customizados
        MAX_ENTITY_TYPES = 10
        MAX_EDGE_TYPES = 10

        # Definicao dos tipos genericos
        person_fallback = {
            "name": "Pessoa",
            "description": "Qualquer pessoa fisica que nao se encaixa nos tipos especificos.",
            "attributes": [
                {"name": "nome_completo", "type": "text", "description": "Nome completo da pessoa"},
                {"name": "papel", "type": "text", "description": "Papel ou ocupacao"}
            ],
            "examples": ["cidadao comum", "internauta anonimo"]
        }

        organization_fallback = {
            "name": "Organizacao",
            "description": "Qualquer organizacao que nao se encaixa nos tipos especificos.",
            "attributes": [
                {"name": "nome_organizacao", "type": "text", "description": "Nome da organizacao"},
                {"name": "tipo_organizacao", "type": "text", "description": "Tipo de organizacao"}
            ],
            "examples": ["pequena empresa", "grupo comunitario"]
        }

        # Verificar se os tipos genericos ja existem
        entity_names = {e["name"] for e in result["entity_types"]}
        has_person = "Pessoa" in entity_names
        has_organization = "Organizacao" in entity_names

        # Tipos genericos que precisam ser adicionados
        fallbacks_to_add = []
        if not has_person:
            fallbacks_to_add.append(person_fallback)
        if not has_organization:
            fallbacks_to_add.append(organization_fallback)

        if fallbacks_to_add:
            current_count = len(result["entity_types"])
            needed_slots = len(fallbacks_to_add)

            # Se adicionar ultrapassar 10, remover alguns tipos existentes
            if current_count + needed_slots > MAX_ENTITY_TYPES:
                # Calcular quantos precisam ser removidos
                to_remove = current_count + needed_slots - MAX_ENTITY_TYPES
                # Remover do final (preservar os tipos especificos mais importantes no inicio)
                result["entity_types"] = result["entity_types"][:-to_remove]

            # Adicionar tipos genericos
            result["entity_types"].extend(fallbacks_to_add)

        # Garantia final de que nao ultrapassa o limite (programacao defensiva)
        if len(result["entity_types"]) > MAX_ENTITY_TYPES:
            result["entity_types"] = result["entity_types"][:MAX_ENTITY_TYPES]

        if len(result["edge_types"]) > MAX_EDGE_TYPES:
            result["edge_types"] = result["edge_types"][:MAX_EDGE_TYPES]

        return result

    def generate_python_code(self, ontology: Dict[str, Any]) -> str:
        """
        Converte a definicao de ontologia em codigo Python (similar a ontology.py)

        Args:
            ontology: Definicao de ontologia

        Returns:
            String com codigo Python
        """
        code_lines = [
            '"""',
            'Definicao de tipos de entidade customizados',
            'Gerado automaticamente pelo MiroFish para simulacao de opiniao publica em midias sociais',
            '"""',
            '',
            'from pydantic import Field',
            'from zep_cloud.external_clients.ontology import EntityModel, EntityText, EdgeModel',
            '',
            '',
            '# ============== Definicao de Tipos de Entidade ==============',
            '',
        ]

        # Gerar tipos de entidade
        for entity in ontology.get("entity_types", []):
            name = entity["name"]
            desc = entity.get("description", f"A {name} entity.")

            code_lines.append(f'class {name}(EntityModel):')
            code_lines.append(f'    """{desc}"""')

            attrs = entity.get("attributes", [])
            if attrs:
                for attr in attrs:
                    attr_name = attr["name"]
                    attr_desc = attr.get("description", attr_name)
                    code_lines.append(f'    {attr_name}: EntityText = Field(')
                    code_lines.append(f'        description="{attr_desc}",')
                    code_lines.append(f'        default=None')
                    code_lines.append(f'    )')
            else:
                code_lines.append('    pass')

            code_lines.append('')
            code_lines.append('')

        code_lines.append('# ============== Definicao de Tipos de Relacao ==============')
        code_lines.append('')

        # Gerar tipos de relacao
        for edge in ontology.get("edge_types", []):
            name = edge["name"]
            # Converter para nome de classe PascalCase
            class_name = ''.join(word.capitalize() for word in name.split('_'))
            desc = edge.get("description", f"A {name} relationship.")

            code_lines.append(f'class {class_name}(EdgeModel):')
            code_lines.append(f'    """{desc}"""')

            attrs = edge.get("attributes", [])
            if attrs:
                for attr in attrs:
                    attr_name = attr["name"]
                    attr_desc = attr.get("description", attr_name)
                    code_lines.append(f'    {attr_name}: EntityText = Field(')
                    code_lines.append(f'        description="{attr_desc}",')
                    code_lines.append(f'        default=None')
                    code_lines.append(f'    )')
            else:
                code_lines.append('    pass')

            code_lines.append('')
            code_lines.append('')

        # Gerar dicionario de tipos
        code_lines.append('# ============== Configuracao de Tipos ==============')
        code_lines.append('')
        code_lines.append('ENTITY_TYPES = {')
        for entity in ontology.get("entity_types", []):
            name = entity["name"]
            code_lines.append(f'    "{name}": {name},')
        code_lines.append('}')
        code_lines.append('')
        code_lines.append('EDGE_TYPES = {')
        for edge in ontology.get("edge_types", []):
            name = edge["name"]
            class_name = ''.join(word.capitalize() for word in name.split('_'))
            code_lines.append(f'    "{name}": {class_name},')
        code_lines.append('}')
        code_lines.append('')

        # Gerar mapeamento de source_targets das arestas
        code_lines.append('EDGE_SOURCE_TARGETS = {')
        for edge in ontology.get("edge_types", []):
            name = edge["name"]
            source_targets = edge.get("source_targets", [])
            if source_targets:
                st_list = ', '.join([
                    f'{{"source": "{st.get("source", "Entity")}", "target": "{st.get("target", "Entity")}"}}'
                    for st in source_targets
                ])
                code_lines.append(f'    "{name}": [{st_list}],')
        code_lines.append('}')

        return '\n'.join(code_lines)
