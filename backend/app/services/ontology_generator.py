"""
Servico de geracao de ontologia
Interface 1: Analisa conteudo textual e gera definicoes de tipos de entidades e relacoes adequadas para simulacao social
"""

import json
from typing import Dict, Any, List, Optional
from ..config import Config
from ..utils.llm_client import LLMClient


# Prompt de sistema para geracao de ontologia
ONTOLOGY_SYSTEM_PROMPT = """Voce e um especialista profissional em design de ontologias para grafos de conhecimento. Sua tarefa e analisar o conteudo textual fornecido e as necessidades de simulacao, projetando tipos de entidades e tipos de relacoes adequados para **simulacao de opiniao publica, stakeholders institucionais, narrativas, midia e ecossistemas de decisao**.

IMPORTANTE: Todos os nomes de entidades, relações, descrições e atributos devem ser em português brasileiro. NÃO use nomes em inglês.

**Importante: Voce deve gerar dados em formato JSON valido, sem nenhum outro conteudo.**

## Contexto da Tarefa Principal

Estamos construindo um **sistema de simulacao de opiniao publica e inteligencia de stakeholders**. Neste sistema:
- Cada entidade e um ator, instituicao, publico, canal ou fonte com capacidade de influenciar, decidir, reagir, legitimar, fiscalizar ou disseminar informacoes
- As entidades influenciam umas as outras por redes sociais, imprensa, canais institucionais, relacoes economicas, regulacao, mobilizacao territorial e autoridade tecnica
- Precisamos simular reacoes, coalizoes, resistencias, riscos, canais de mobilizacao e caminhos de disseminacao de informacao

Portanto, **as entidades devem representar stakeholders reais ou classes operacionais de stakeholders**, nao apenas perfis sociais:

**Podem ser**:
- Individuos especificos (figuras publicas, partes envolvidas, formadores de opiniao, especialistas, cidadaos comuns)
- Empresas e companhias (incluindo suas contas oficiais)
- Organizacoes e instituicoes (universidades, associacoes, ONGs, sindicatos etc.)
- Orgaos governamentais, agencias reguladoras
- Veiculos de midia (jornais, emissoras de TV, midia independente, portais)
- As proprias plataformas de midias sociais
- Representantes de grupos especificos (como associacoes de ex-alunos, fas, grupos de defesa de direitos etc.)
- Stakeholders institucionais, reguladores, financiadores, opositores, aliados taticos, especialistas tecnicos, grupos economicos, operadores politicos, associacoes de classe, orgaos fiscalizadores, comunidades afetadas, imprensa local/tradicional e publicos mobilizaveis/adversariais/indecisos

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
            "name": "Nome do tipo em PORTUGUES BRASILEIRO (PascalCase, ex: CandidatoPolitico, OrgaoGovernamental, VeiculoDeMidia, InstituicaoJudiciaria, GrupoSociedadeCivil, AgenciaReguladora, PlataformaMidiaSocial, Pessoa, Organizacao). PROIBIDO usar ingles como PoliticalCandidate ou GovernmentOfficial.",
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
            "name": "NOME_RELACAO em PORTUGUES (UPPER_SNAKE_CASE, ex: APOIA, SE_OPOE_A, COMPETE_COM, COLABORA_COM, TRABALHA_PARA, AFILIADO_A, REPRESENTA, REGULAMENTA, REPORTA_SOBRE, COMENTA_SOBRE, RESPONDE_A). PROIBIDO ingles como SUPPORTS ou OPPOSES.",
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

**Requisito de quantidade: gere entre 12 e 24 tipos de entidade**

**Requisito de estrutura em camadas (deve incluir tipos especificos, institucionais e genericos)**:

Seus tipos de entidade devem conter as seguintes camadas:

A. **Tipos genericos (obrigatorios, devem ser os 2 ultimos da lista)**:
   - `Pessoa`: Tipo generico para qualquer pessoa fisica. Quando uma pessoa nao se encaixa em nenhum tipo mais especifico, deve ser classificada aqui.
   - `Organizacao`: Tipo generico para qualquer organizacao. Quando uma organizacao nao se encaixa em nenhum tipo mais especifico, deve ser classificada aqui.

B. **Tipos especificos e institucionais (10 a 22, projetados com base no conteudo textual)**:
   - Projete tipos mais especificos para os principais papeis presentes no texto
   - Exemplo: se o texto envolve eventos academicos, pode ter `Estudante`, `Professor`, `Universidade`
   - Exemplo: se o texto envolve eventos empresariais, pode ter `Empresa`, `Executivo`, `Funcionario`
   - Para politica, empresas, crise publica, regulacao, midia ou ecossistema institucional, considere camadas como `StakeholderInstitucional`, `OrgaoRegulador`, `Financiador`, `Opositor`, `AliadoTatico`, `InfluenciadorDeNicho`, `ImprensaTradicional`, `ImprensaLocal`, `ComunidadeAfetada`, `EspecialistaTecnico`, `GrupoEconomico`, `OperadorPolitico`, `AssociacaoDeClasse`, `OrgaoFiscalizador`, `PlataformaMidiaSocial`, `FontePrimaria`, `PublicoIndeciso`, `PublicoAdversarial` e `PublicoMobilizavel`

**Por que tipos genericos sao necessarios**:
- No texto aparecem diversas pessoas, como "professor do ensino medio", "transeunte", "um internauta"
- Se nao houver um tipo especifico correspondente, devem ser classificadas em `Pessoa`
- Da mesma forma, pequenas organizacoes, grupos temporarios etc. devem ser classificados em `Organizacao`

**Principios de design dos tipos especificos**:
- Identifique os tipos de papeis que aparecem com frequencia ou sao fundamentais no texto
- Cada tipo especifico deve ter limites claros, evitando sobreposicao
- A description deve explicar claramente a diferenca entre este tipo e o tipo generico

### 2. Design de Tipos de Relacoes

- Quantidade: 8 a 16
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
        self.llm_client = llm_client or LLMClient(model=Config.LLM_PREMIUM_MODEL)

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
1. Devem ser entre 12 e 24 tipos de entidade
2. Os 2 ultimos devem ser tipos genericos: Pessoa (generico para individuos) e Organizacao (generico para organizacoes)
3. Os primeiros tipos devem cobrir atores especificos, stakeholders institucionais, publicos, canais e fontes primarias relevantes ao caso
4. Todos os tipos de entidade devem representar stakeholders reais ou classes operacionais de stakeholders, nao conceitos abstratos
5. Nomes de atributos nao podem usar palavras reservadas como name, uuid, group_id; use nome_completo, nome_organizacao, papel etc.
6. Inclua relacoes suficientes para representar apoio, oposicao, regulacao, financiamento, representacao, influencia, cobertura de midia e mobilizacao
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

        MIN_ENTITY_TYPES = 12
        MAX_ENTITY_TYPES = 24
        MIN_EDGE_TYPES = 8
        MAX_EDGE_TYPES = 16
        RESERVED_ATTRIBUTES = {"name", "uuid", "group_id", "created_at", "summary"}

        def entity_type(name: str, description: str, examples: List[str]) -> Dict[str, Any]:
            return {
                "name": name,
                "description": description[:100],
                "attributes": [
                    {"name": "nome_exibicao", "type": "text", "description": "Nome exibido do stakeholder"},
                    {"name": "papel", "type": "text", "description": "Papel no ecossistema analisado"},
                    {"name": "posicao_publica", "type": "text", "description": "Posicao publica provavel"},
                ],
                "examples": examples,
            }

        person_fallback = entity_type(
            "Pessoa",
            "Pessoa fisica sem tipo mais especifico.",
            ["cidadao comum", "internauta anonimo"],
        )
        organization_fallback = entity_type(
            "Organizacao",
            "Organizacao sem tipo mais especifico.",
            ["pequena empresa", "grupo comunitario"],
        )

        priority_fallbacks = [
            entity_type("StakeholderInstitucional", "Instituicao com poder formal ou reputacional.", ["ministerio", "universidade"]),
            entity_type("OrgaoRegulador", "Agencia ou autoridade que regula o tema.", ["agencia reguladora", "conselho profissional"]),
            entity_type("OrgaoFiscalizador", "Instituicao que fiscaliza ou apura condutas.", ["tribunal de contas", "ministerio publico"]),
            entity_type("Financiador", "Ator que fornece recursos ou condiciona investimento.", ["banco publico", "fundo privado"]),
            entity_type("Opositor", "Ator organizado contra a agenda analisada.", ["grupo oposicionista", "lider adversarial"]),
            entity_type("AliadoTatico", "Ator que apoia por convergencia temporaria.", ["parceiro setorial", "coalizao local"]),
            entity_type("InfluenciadorDeNicho", "Pessoa ou perfil que influencia comunidades especificas.", ["criador regional", "lider de comunidade"]),
            entity_type("ImprensaTradicional", "Veiculo de midia com alcance editorial amplo.", ["jornal", "emissora de TV"]),
            entity_type("ImprensaLocal", "Veiculo regional ou hiperlocal relevante.", ["portal local", "radio comunitaria"]),
            entity_type("ComunidadeAfetada", "Grupo diretamente afetado pelo evento ou decisao.", ["moradores", "usuarios do servico"]),
            entity_type("EspecialistaTecnico", "Autoridade tecnica que interpreta riscos e evidencias.", ["pesquisador", "consultor tecnico"]),
            entity_type("GrupoEconomico", "Empresa, conglomerado ou setor com interesse economico.", ["associacao empresarial", "holding"]),
            entity_type("OperadorPolitico", "Articulador com capacidade de coordenar apoio ou resistencia.", ["assessor", "coordenador politico"]),
            entity_type("AssociacaoDeClasse", "Entidade representativa de categoria profissional ou setor.", ["sindicato", "conselho de classe"]),
            entity_type("PlataformaMidiaSocial", "Plataforma onde a disputa narrativa circula.", ["Instagram", "X/Twitter"]),
            entity_type("FontePrimaria", "Fonte documental ou testemunhal usada como evidencia.", ["documento oficial", "testemunha direta"]),
            entity_type("PublicoIndeciso", "Publico sem posicao consolidada.", ["eleitor indeciso", "consumidor neutro"]),
            entity_type("PublicoAdversarial", "Publico inclinado a rejeitar a narrativa.", ["base critica", "grupo hostil"]),
            entity_type("PublicoMobilizavel", "Publico propenso a engajar se acionado corretamente.", ["apoiadores potenciais", "voluntarios"]),
        ]

        normalized_entities = []
        seen_entities = set()
        for entity in result["entity_types"]:
            name = (entity.get("name") or "").strip()
            if not name or name in seen_entities:
                continue
            attributes = []
            for attr in entity.get("attributes", []):
                attr_name = (attr.get("name") or "").strip()
                if not attr_name or attr_name in RESERVED_ATTRIBUTES:
                    continue
                attributes.append({
                    "name": attr_name,
                    "type": attr.get("type") or "text",
                    "description": attr.get("description") or attr_name,
                })
            entity["attributes"] = attributes or entity_type(name, entity.get("description", ""), []).get("attributes", [])
            entity["examples"] = entity.get("examples") or []
            entity["description"] = (entity.get("description") or "")[:100]
            normalized_entities.append(entity)
            seen_entities.add(name)

        specifics = [
            entity for entity in normalized_entities
            if entity.get("name") not in {"Pessoa", "Organizacao"}
        ]
        seen_specifics = {entity.get("name") for entity in specifics}

        for fallback in priority_fallbacks:
            if len(specifics) >= MAX_ENTITY_TYPES - 2:
                break
            if len(specifics) >= MIN_ENTITY_TYPES - 2:
                break
            if fallback["name"] not in seen_specifics:
                specifics.append(fallback)
                seen_specifics.add(fallback["name"])

        specifics = specifics[:MAX_ENTITY_TYPES - 2]
        result["entity_types"] = specifics + [person_fallback, organization_fallback]

        available_names = [entity["name"] for entity in result["entity_types"]]
        default_source = available_names[0] if available_names else "Pessoa"
        default_target = available_names[1] if len(available_names) > 1 else "Organizacao"

        fallback_edges = [
            ("INFLUENCIA", "Influencia comportamento, decisao ou percepcao."),
            ("APOIA", "Apoia publicamente ou operacionalmente."),
            ("SE_OPOE_A", "Opoe-se a uma agenda, ator ou narrativa."),
            ("REGULA", "Regula ou condiciona a atuacao de outro ator."),
            ("FISCALIZA", "Fiscaliza, apura ou audita condutas."),
            ("FINANCIA", "Financia ou viabiliza recursos."),
            ("REPRESENTA", "Representa interesses de um grupo."),
            ("COBRE_NA_MIDIA", "Cobre, pauta ou amplifica em midia."),
            ("MOBILIZA", "Mobiliza publicos ou comunidades."),
            ("RESPONDE_A", "Responde a critica, crise ou solicitacao."),
        ]

        normalized_edges = []
        seen_edges = set()
        for edge in result["edge_types"]:
            name = (edge.get("name") or "").strip()
            if not name or name in seen_edges:
                continue
            source_targets = edge.get("source_targets") or [
                {"source": default_source, "target": default_target}
            ]
            edge["source_targets"] = source_targets
            edge["attributes"] = edge.get("attributes") or []
            edge["description"] = (edge.get("description") or "")[:100]
            normalized_edges.append(edge)
            seen_edges.add(name)

        for name, description in fallback_edges:
            if len(normalized_edges) >= MIN_EDGE_TYPES:
                break
            if name in seen_edges:
                continue
            normalized_edges.append({
                "name": name,
                "description": description,
                "source_targets": [{"source": default_source, "target": default_target}],
                "attributes": [],
            })
            seen_edges.add(name)

        result["edge_types"] = normalized_edges[:MAX_EDGE_TYPES]

        return result

