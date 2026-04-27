"""
Gerador de Agent Profile OASIS
Converte entidades do grafo Zep para o formato Agent Profile da plataforma OASIS

Melhorias:
1. Usa busca Zep para enriquecer informacoes dos nos
2. Otimiza prompts para gerar perfis muito detalhados
3. Distingue entidades individuais e de grupo/abstrato
"""

import json
import random
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

from openai import OpenAI
from ..config import Config
from ..utils.logger import get_logger
from .zep_entity_reader import EntityNode, ZepEntityReader

logger = get_logger('mirofish.oasis_profile')


@dataclass
class OasisAgentProfile:
    """Estrutura de dados do OASIS Agent Profile"""
    # Campos gerais
    user_id: int
    user_name: str
    name: str
    bio: str
    persona: str

    # Campos opcionais - estilo Reddit
    karma: int = 1000

    # Campos opcionais - estilo Twitter
    friend_count: int = 100
    follower_count: int = 150
    statuses_count: int = 500

    # Informacoes adicionais de perfil
    age: Optional[int] = None
    gender: Optional[str] = None
    mbti: Optional[str] = None
    country: Optional[str] = None
    profession: Optional[str] = None
    interested_topics: List[str] = field(default_factory=list)

    # Informacoes da entidade de origem
    source_entity_uuid: Optional[str] = None
    source_entity_type: Optional[str] = None

    created_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))

    def to_reddit_format(self) -> Dict[str, Any]:
        """Converte para formato Reddit"""
        profile = {
            "user_id": self.user_id,
            "username": self.user_name,  # Biblioteca OASIS exige campo username (sem underscore)
            "name": self.name,
            "bio": self.bio,
            "persona": self.persona,
            "karma": self.karma,
            "created_at": self.created_at,
        }

        # Adiciona informacoes adicionais de perfil (se houver)
        if self.age:
            profile["age"] = self.age
        if self.gender:
            profile["gender"] = self.gender
        if self.mbti:
            profile["mbti"] = self.mbti
        if self.country:
            profile["country"] = self.country
        if self.profession:
            profile["profession"] = self.profession
        if self.interested_topics:
            profile["interested_topics"] = self.interested_topics

        return profile

    def to_twitter_format(self) -> Dict[str, Any]:
        """Converte para formato Twitter"""
        profile = {
            "user_id": self.user_id,
            "username": self.user_name,  # Biblioteca OASIS exige campo username (sem underscore)
            "name": self.name,
            "bio": self.bio,
            "persona": self.persona,
            "friend_count": self.friend_count,
            "follower_count": self.follower_count,
            "statuses_count": self.statuses_count,
            "created_at": self.created_at,
        }

        # Adiciona informacoes adicionais de perfil
        if self.age:
            profile["age"] = self.age
        if self.gender:
            profile["gender"] = self.gender
        if self.mbti:
            profile["mbti"] = self.mbti
        if self.country:
            profile["country"] = self.country
        if self.profession:
            profile["profession"] = self.profession
        if self.interested_topics:
            profile["interested_topics"] = self.interested_topics

        return profile

    def to_dict(self) -> Dict[str, Any]:
        """Converte para formato de dicionario completo"""
        return {
            "user_id": self.user_id,
            "user_name": self.user_name,
            "name": self.name,
            "bio": self.bio,
            "persona": self.persona,
            "karma": self.karma,
            "friend_count": self.friend_count,
            "follower_count": self.follower_count,
            "statuses_count": self.statuses_count,
            "age": self.age,
            "gender": self.gender,
            "mbti": self.mbti,
            "country": self.country,
            "profession": self.profession,
            "interested_topics": self.interested_topics,
            "source_entity_uuid": self.source_entity_uuid,
            "source_entity_type": self.source_entity_type,
            "created_at": self.created_at,
        }


class OasisProfileGenerator:
    """
    Gerador de Profile OASIS

    Converte entidades do grafo Zep para Agent Profile do OASIS

    Caracteristicas otimizadas:
    1. Usa busca no grafo Zep para contexto mais rico
    2. Gera perfis muito detalhados (info basica, experiencia, personalidade, comportamento em redes sociais)
    3. Distingue entidades individuais e de grupo/abstrato
    """

    # Lista de tipos MBTI
    MBTI_TYPES = [
        "INTJ", "INTP", "ENTJ", "ENTP",
        "INFJ", "INFP", "ENFJ", "ENFP",
        "ISTJ", "ISFJ", "ESTJ", "ESFJ",
        "ISTP", "ISFP", "ESTP", "ESFP"
    ]

    # Lista de paises comuns
    COUNTRIES = [
        "Brazil", "US", "UK", "Canada", "Australia", "Germany",
        "França", "Espanha", "Portugal", "Argentina", "Chile", "México"
    ]

    # Entidades de tipo individual (requerem perfil concreto)
    INDIVIDUAL_ENTITY_TYPES = [
        "student", "alumni", "professor", "person", "publicfigure",
        "expert", "faculty", "official", "journalist", "activist"
    ]

    # Entidades de tipo grupo/instituicao (requerem perfil representativo)
    GROUP_ENTITY_TYPES = [
        "university", "governmentagency", "organization", "ngo",
        "mediaoutlet", "company", "institution", "group", "community"
    ]

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model_name: Optional[str] = None,
        zep_api_key: Optional[str] = None,
        graph_id: Optional[str] = None
    ):
        self.api_key = api_key or Config.LLM_API_KEY
        self.base_url = base_url or Config.LLM_BASE_URL
        self.model_name = model_name or Config.LLM_AGENT_MODEL

        if not self.api_key:
            raise ValueError("LLM_API_KEY nao configurada")

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )

        # Cliente Graphiti para busca de contexto rico
        self.graph_id = graph_id
        self.graphiti_client = None
        try:
            from ..utils.graphiti_client import GraphitiClient
            self.graphiti_client = GraphitiClient()
        except Exception as e:
            logger.warning(f"Falha ao inicializar cliente Graphiti: {e}")

    def generate_profile_from_entity(
        self,
        entity: EntityNode,
        user_id: int,
        use_llm: bool = True,
        stance: str = "default",
    ) -> OasisAgentProfile:
        """
        Gera OASIS Agent Profile a partir de entidade Zep

        Args:
            entity: No de entidade Zep
            user_id: ID do usuario (para OASIS)
            use_llm: Se usa LLM para perfis detalhados

        Returns:
            OasisAgentProfile
        """
        entity_type = entity.get_entity_type() or "Entity"

        # Informacoes basicas
        name = entity.name
        user_name = self._generate_username(name)

        # Constroi informacoes de contexto
        context = self._build_entity_context(entity)

        if use_llm:
            # Usa LLM para gerar perfil detalhado
            profile_data = self._generate_profile_with_llm(
                entity_name=name,
                entity_type=entity_type,
                entity_summary=entity.summary,
                entity_attributes=entity.attributes,
                context=context,
                stance=stance,
            )
        else:
            # Gera perfil basico por regras
            profile_data = self._generate_profile_rule_based(
                entity_name=name,
                entity_type=entity_type,
                entity_summary=entity.summary,
                entity_attributes=entity.attributes
            )

        return OasisAgentProfile(
            user_id=user_id,
            user_name=user_name,
            name=name,
            bio=profile_data.get("bio", f"{entity_type}: {name}"),
            persona=profile_data.get("persona", entity.summary or f"A {entity_type} named {name}."),
            karma=profile_data.get("karma", random.randint(500, 5000)),
            friend_count=profile_data.get("friend_count", random.randint(50, 500)),
            follower_count=profile_data.get("follower_count", random.randint(100, 1000)),
            statuses_count=profile_data.get("statuses_count", random.randint(100, 2000)),
            age=profile_data.get("age"),
            gender=profile_data.get("gender"),
            mbti=profile_data.get("mbti"),
            country=profile_data.get("country"),
            profession=profile_data.get("profession"),
            interested_topics=profile_data.get("interested_topics", []),
            source_entity_uuid=entity.uuid,
            source_entity_type=entity_type,
        )

    def _generate_username(self, name: str) -> str:
        """Gera nome de usuario"""
        # Remove caracteres especiais, converte para minusculo
        username = name.lower().replace(" ", "_")
        username = ''.join(c for c in username if c.isalnum() or c == '_')

        # Adiciona sufixo aleatorio para evitar duplicatas
        suffix = random.randint(100, 999)
        return f"{username}_{suffix}"

    def _search_zep_for_entity(self, entity: EntityNode) -> Dict[str, Any]:
        """
        Usa busca hibrida no grafo Zep para obter informacoes ricas da entidade

        Zep nao tem interface de busca hibrida, precisa buscar edges e nodes separadamente e combinar.
        Usa requisicoes paralelas para busca simultanea, melhorando eficiencia.

        Args:
            entity: Objeto do no de entidade

        Returns:
            Dicionario contendo facts, node_summaries, context
        """
        import concurrent.futures

        if not self.graphiti_client:
            return {"facts": [], "node_summaries": [], "context": ""}

        entity_name = entity.name

        results = {
            "facts": [],
            "node_summaries": [],
            "context": ""
        }

        if not self.graph_id:
            logger.debug(f"Pulando busca Graphiti: graph_id nao definido")
            return results

        comprehensive_query = f"Sobre {entity_name} - todas as informacoes, atividades, eventos, relacoes e contexto"

        try:
            search_result = self.graphiti_client.search(
                group_ids=[self.graph_id],
                query=comprehensive_query,
                max_facts=30,
            )

            raw_facts = search_result.get("facts", [])
            all_facts = set()
            all_summaries = set()

            for fact in raw_facts:
                if isinstance(fact, dict):
                    fact_text = fact.get("fact", "")
                    fact_name = fact.get("name", "")
                    if fact_text:
                        all_facts.add(fact_text)
                    if fact_name and fact_name != entity_name:
                        all_summaries.add(f"entidade relacionada: {fact_name}")
                elif isinstance(fact, str):
                    all_facts.add(fact)

            results["facts"] = list(all_facts)
            results["node_summaries"] = list(all_summaries)

            context_parts = []
            if results["facts"]:
                context_parts.append("Informacoes factuais:\n" + "\n".join(f"- {f}" for f in results["facts"][:20]))
            if results["node_summaries"]:
                context_parts.append("entidade relacionada:\n" + "\n".join(f"- {s}" for s in results["node_summaries"][:10]))
            results["context"] = "\n\n".join(context_parts)

            logger.info(f"Busca Graphiti concluida: {entity_name}, obteve {len(results['facts'])} fatos, {len(results['node_summaries'])} nos relacionados")

        except Exception as e:
            logger.warning(f"Falha na busca Graphiti ({entity_name}): {e}")

        return results

    def _build_entity_context(self, entity: EntityNode) -> str:
        """
        Constroi informacoes de contexto completo da entidade

        Inclui:
        1. Informacoes de arestas da entidade (fatos)
        2. Informacoes detalhadas de nos associados
        3. Informacoes ricas obtidas por busca hibrida Zep
        """
        context_parts = []

        # 1. Adiciona informacoes de atributos da entidade
        if entity.attributes:
            attrs = []
            for key, value in entity.attributes.items():
                if value and str(value).strip():
                    attrs.append(f"- {key}: {value}")
            if attrs:
                context_parts.append("### Atributos da entidade\n" + "\n".join(attrs))

        # 2. Adiciona informacoes de arestas (fatos/relacoes)
        existing_facts = set()
        if entity.related_edges:
            relationships = []
            for edge in entity.related_edges:  # sem limite de quantidade
                fact = edge.get("fact", "")
                edge_name = edge.get("edge_name", "")
                direction = edge.get("direction", "")

                if fact:
                    relationships.append(f"- {fact}")
                    existing_facts.add(fact)
                elif edge_name:
                    if direction == "outgoing":
                        relationships.append(f"- {entity.name} --[{edge_name}]--> (entidade relacionada)")
                    else:
                        relationships.append(f"- (entidade relacionada) --[{edge_name}]--> {entity.name}")

            if relationships:
                context_parts.append("### Fatos e relacoes\n" + "\n".join(relationships))

        # 3. Adiciona informacoes detalhadas de nos associados
        if entity.related_nodes:
            related_info = []
            for node in entity.related_nodes:  # sem limite de quantidade
                node_name = node.get("name", "")
                node_labels = node.get("labels", [])
                node_summary = node.get("summary", "")

                # Filtra labels padrao
                custom_labels = [l for l in node_labels if l not in ["Entity", "Node"]]
                label_str = f" ({', '.join(custom_labels)})" if custom_labels else ""

                if node_summary:
                    related_info.append(f"- **{node_name}**{label_str}: {node_summary}")
                else:
                    related_info.append(f"- **{node_name}**{label_str}")

            if related_info:
                context_parts.append("### Informacoes de entidades associadas\n" + "\n".join(related_info))

        # 4. Usa busca hibrida Zep para informacoes mais ricas
        zep_results = self._search_zep_for_entity(entity)

        if zep_results.get("facts"):
            # Deduplicacao: exclui fatos ja existentes
            new_facts = [f for f in zep_results["facts"] if f not in existing_facts]
            if new_facts:
                context_parts.append("### Informacoes factuais obtidas pelo Zep\n" + "\n".join(f"- {f}" for f in new_facts[:15]))

        if zep_results.get("node_summaries"):
            context_parts.append("### Nos relacionados obtidos pelo Zep\n" + "\n".join(f"- {s}" for s in zep_results["node_summaries"][:10]))

        return "\n\n".join(context_parts)

    def _is_individual_entity(self, entity_type: str) -> bool:
        """Verifica se e entidade de tipo individual"""
        return entity_type.lower() in self.INDIVIDUAL_ENTITY_TYPES

    def _is_group_entity(self, entity_type: str) -> bool:
        """Verifica se e entidade de tipo grupo/instituicao"""
        return entity_type.lower() in self.GROUP_ENTITY_TYPES

    # Instrucao adversarial — Phase 3 do roadmap v1.2 ("contra-agentes/devil's advocate")
    _CONTRARIAN_INSTRUCTION = (
        "\n\n[INSTRUCAO ADICIONAL — STANCE CONTRARIA]\n"
        "Este perfil DEVE ler o cenario de forma estruturalmente OPOSTA ao consenso aparente "
        "no contexto fornecido. Pratique ceticismo metodico: questione premissas, exponha riscos "
        "que a narrativa hegemonica esconde, traga vieses ignorados, ofereca leitura adversarial. "
        "Nao seja troll nem caricato — seja um critico fundamentado, com argumentos consistentes. "
        "A persona deve refletir essa postura cetica/adversarial sem perder coerencia com o tipo "
        "de entidade representado."
    )

    def _generate_profile_with_llm(
        self,
        entity_name: str,
        entity_type: str,
        entity_summary: str,
        entity_attributes: Dict[str, Any],
        context: str,
        stance: str = "default",
    ) -> Dict[str, Any]:
        """
        Usa LLM para gerar perfil muito detalhado

        Distingue por tipo de entidade:
        - - Individual: gera configuracao de personagem concreto
        - - Grupo/instituicao: gera configuracao de conta representativa
        """

        is_individual = self._is_individual_entity(entity_type)

        if is_individual:
            prompt = self._build_individual_persona_prompt(
                entity_name, entity_type, entity_summary, entity_attributes, context
            )
        else:
            prompt = self._build_group_persona_prompt(
                entity_name, entity_type, entity_summary, entity_attributes, context
            )

        # Phase 3: stance adversarial em ~20% dos perfis para evitar viés de consenso
        if stance == "contrarian":
            prompt = prompt + self._CONTRARIAN_INSTRUCTION

        # Tenta multiplas geracoes ate sucesso ou limite de retentativas
        max_attempts = 3
        last_error = None

        for attempt in range(max_attempts):
            try:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": self._get_system_prompt(is_individual)},
                        {"role": "user", "content": prompt}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.7 - (attempt * 0.1)  # Reduz temperatura a cada retentativa
                    # Nao define max_tokens, deixa o LLM gerar livremente
                )

                content = response.choices[0].message.content

                # Verifica se foi truncado (finish_reason nao e 'stop')
                finish_reason = response.choices[0].finish_reason
                if finish_reason == 'length':
                    logger.warning(f"Saida do LLM truncada (attempt {attempt+1}), tentando corrigir...")
                    content = self._fix_truncated_json(content)

                # Tenta analisar JSON
                try:
                    result = json.loads(content)

                    # Valida campos obrigatorios
                    if "bio" not in result or not result["bio"]:
                        result["bio"] = entity_summary[:200] if entity_summary else f"{entity_type}: {entity_name}"
                    if "persona" not in result or not result["persona"]:
                        result["persona"] = entity_summary or f"{entity_name} e um(a) {entity_type}。"

                    return result

                except json.JSONDecodeError as je:
                    logger.warning(f"Falha na analise JSON (attempt {attempt+1}): {str(je)[:80]}")

                    # Tenta corrigir JSON
                    result = self._try_fix_json(content, entity_name, entity_type, entity_summary)
                    if result.get("_fixed"):
                        del result["_fixed"]
                        return result

                    last_error = je

            except Exception as e:
                logger.warning(f"Falha na chamada LLM (attempt {attempt+1}): {str(e)[:80]}")
                last_error = e
                import time
                time.sleep(1 * (attempt + 1))  # Backoff exponencial

        logger.warning(f"Falha ao gerar perfil via LLM ({max_attempts} tentativas): {last_error}, usando geracao por regras")
        return self._generate_profile_rule_based(
            entity_name, entity_type, entity_summary, entity_attributes
        )

    def _fix_truncated_json(self, content: str) -> str:
        """Corrige JSON truncado (saida truncada por limite de max_tokens)"""
        import re

        # Se JSON truncado, tenta fecha-lo
        content = content.strip()

        # Calcula chaves/colchetes nao fechados
        open_braces = content.count('{') - content.count('}')
        open_brackets = content.count('[') - content.count(']')

        # Verifica se ha strings nao fechadas
        # Verificacao simples: se apos ultima aspas nao ha virgula ou chave, string pode estar truncada
        if content and content[-1] not in '",}]':
            # Tenta fechar string
            content += '"'

        # Fecha chaves/colchetes
        content += ']' * open_brackets
        content += '}' * open_braces

        return content

    def _try_fix_json(self, content: str, entity_name: str, entity_type: str, entity_summary: str = "") -> Dict[str, Any]:
        """Tenta corrigir JSON corrompido"""
        import re

        # 1. Tenta corrigir truncamento primeiro
        content = self._fix_truncated_json(content)

        # 2. Tenta extrair parte JSON
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            json_str = json_match.group()

            # 3. Corrige problema de quebras de linha em strings
            # Encontra todos os valores string e substitui quebras de linha
            def fix_string_newlines(match):
                s = match.group(0)
                # Substitui quebras de linha reais em strings por espacos
                s = s.replace('\n', ' ').replace('\r', ' ')
                # Substitui espacos extras
                s = re.sub(r'\s+', ' ', s)
                return s

            # Corresponde valores de string JSON
            json_str = re.sub(r'"[^"\\]*(?:\\.[^"\\]*)*"', fix_string_newlines, json_str)

            # 4. Tenta analisar
            try:
                result = json.loads(json_str)
                result["_fixed"] = True
                return result
            except json.JSONDecodeError as e:
                # 5. Se ainda falhar, tenta correcao mais agressiva
                try:
                    # Remove todos os caracteres de controle
                    json_str = re.sub(r'[\x00-\x1f\x7f-\x9f]', ' ', json_str)
                    # Substitui todos os espacos em branco consecutivos
                    json_str = re.sub(r'\s+', ' ', json_str)
                    result = json.loads(json_str)
                    result["_fixed"] = True
                    return result
                except:
                    pass

        # 6. Tenta extrair informacoes parciais do conteudo
        bio_match = re.search(r'"bio"\s*:\s*"([^"]*)"', content)
        persona_match = re.search(r'"persona"\s*:\s*"([^"]*)', content)  # pode estar truncado

        bio = bio_match.group(1) if bio_match else (entity_summary[:200] if entity_summary else f"{entity_type}: {entity_name}")
        persona = persona_match.group(1) if persona_match else (entity_summary or f"{entity_name} e um(a) {entity_type}。")

        # Se extraiu conteudo significativo, marca como corrigido
        if bio_match or persona_match:
            logger.info(f"Extraiu informacoes parciais do JSON corrompido")
            return {
                "bio": bio,
                "persona": persona,
                "_fixed": True
            }

        # 7. Falha total, retorna estrutura basica
        logger.warning(f"Correcao de JSON falhou, retorna estrutura basica")
        return {
            "bio": entity_summary[:200] if entity_summary else f"{entity_type}: {entity_name}",
            "persona": entity_summary or f"{entity_name} e um(a) {entity_type}。"
        }

    def _get_system_prompt(self, is_individual: bool) -> str:
        """Obtem prompt do sistema"""
        base_prompt = (
            "Voce e especialista em geracao de perfis para redes sociais. "
            "Crie perfis detalhados e realistas para simulacao social, preservando ao maximo o contexto fornecido. "
            "Retorne JSON valido. Todos os campos de texto devem ser de linha unica, sem quebras nao escapadas. "
            "IMPORTANTE: Todas as respostas, análises e conteúdos gerados devem ser em português brasileiro. "
            "Use referencias culturais ocidentais e brasileiras quando o contexto nao indicar outra localidade."
        )
        return base_prompt

    def _build_individual_persona_prompt(
        self,
        entity_name: str,
        entity_type: str,
        entity_summary: str,
        entity_attributes: Dict[str, Any],
        context: str
    ) -> str:
        """Constroi prompt detalhado para entidade individual"""

        attrs_str = json.dumps(entity_attributes, ensure_ascii=False) if entity_attributes else "nenhum"
        context_str = context[:3000] if context else "sem contexto adicional"

        return f"""Crie um perfil detalhado de usuario para redes sociais, preservando ao maximo o contexto do mundo real.

Nome da entidade: {entity_name}
Tipo de entidade: {entity_type}
Resumo da entidade: {entity_summary}
Atributos da entidade: {attrs_str}

Informacoes de contexto:
{context_str}

Gere um JSON com os seguintes campos:

1. bio: biografia curta de rede social, em torno de 200 caracteres
2. persona: descricao detalhada do perfil, em texto corrido, contendo:
   - informacoes basicas (idade, profissao, formacao, localidade)
   - contexto pessoal (trajetoria, relacao com o evento, rede social)
   - tracos de personalidade (MBTI, temperamento, expressao emocional)
   - comportamento em redes (frequencia, preferencias, estilo de interacao, linguagem)
   - posicionamento (visao sobre o tema, gatilhos de apoio ou irritacao)
   - tracos distintivos (expressoes recorrentes, hobbies, experiencias)
   - memoria pessoal ligada ao evento
3. age: idade numerica inteira
4. gender: "male" ou "female"
5. mbti: tipo MBTI
6. country: pais em ingles padrao, por exemplo "Brazil"
7. profession: profissao
8. interested_topics: lista de temas de interesse

Importante:
- Todos os valores devem ser string, numero ou lista simples, sem quebras de linha nao escapadas
- persona deve ser um texto corrido coerente
- Use portugues do Brasil por padrao
- Se o contexto nao indicar outra localidade, assuma ambiente ocidental e brasileiro
- Quando fizer sentido geografico, prefira referencias compativeis com Brasil e Distrito Federal
- age deve ser inteiro valido e gender deve ser "male" ou "female"
"""

    def _build_group_persona_prompt(
        self,
        entity_name: str,
        entity_type: str,
        entity_summary: str,
        entity_attributes: Dict[str, Any],
        context: str
    ) -> str:
        """Constroi prompt detalhado para entidade de grupo/instituicao"""

        attrs_str = json.dumps(entity_attributes, ensure_ascii=False) if entity_attributes else "nenhum"
        context_str = context[:3000] if context else "sem contexto adicional"

        return f"""Crie uma configuracao detalhada de conta institucional ou de grupo para redes sociais, preservando ao maximo o contexto do mundo real.

Nome da entidade: {entity_name}
Tipo de entidade: {entity_type}
Resumo da entidade: {entity_summary}
Atributos da entidade: {attrs_str}

Informacoes de contexto:
{context_str}

Gere um JSON com os seguintes campos:

1. bio: descricao curta da conta oficial, profissional e clara
2. persona: descricao detalhada da conta, em texto corrido, incluindo:
   - informacoes institucionais
   - posicionamento da conta
   - estilo de publicacao e comunicacao
   - tipo de audiencia
   - postura diante de controversias
   - memoria institucional ligada ao evento
3. age: fixo em 30
4. gender: fixo em "other"
5. mbti: tipo MBTI para representar o estilo da conta
6. country: pais em ingles padrao, por exemplo "Brazil"
7. profession: funcao institucional
8. interested_topics: lista de areas de interesse

Importante:
- Nao use null
- persona deve ser um texto corrido sem quebras de linha
- Use portugues do Brasil por padrao
- Se o contexto nao indicar outra localidade, assuma ambiente ocidental e brasileiro
- age deve ser 30 e gender deve ser "other"
- A fala institucional deve ser coerente com o papel da organizacao"""

    def _generate_profile_rule_based(
        self,
        entity_name: str,
        entity_type: str,
        entity_summary: str,
        entity_attributes: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Gera perfil basico por regras"""

        # Gera perfis diferentes por tipo de entidade
        entity_type_lower = entity_type.lower()

        if entity_type_lower in ["student", "alumni"]:
            return {
                "bio": f"{entity_type} with interests in academics and social issues.",
                "persona": f"{entity_name} is a {entity_type.lower()} who is actively engaged in academic and social discussions. They enjoy sharing perspectives and connecting with peers.",
                "age": random.randint(18, 30),
                "gender": random.choice(["male", "female"]),
                "mbti": random.choice(self.MBTI_TYPES),
                "country": random.choice(self.COUNTRIES),
                "profession": "Student",
                "interested_topics": ["Educação", "Questões Sociais", "Tecnologia"],
            }

        elif entity_type_lower in ["publicfigure", "expert", "faculty"]:
            return {
                "bio": f"Expert and thought leader in their field.",
                "persona": f"{entity_name} is a recognized {entity_type.lower()} who shares insights and opinions on important matters. They are known for their expertise and influence in public discourse.",
                "age": random.randint(35, 60),
                "gender": random.choice(["male", "female"]),
                "mbti": random.choice(["ENTJ", "INTJ", "ENTP", "INTP"]),
                "country": random.choice(self.COUNTRIES),
                "profession": entity_attributes.get("occupation", "Especialista"),
                "interested_topics": ["Política", "Economia", "Cultura e Sociedade"],
            }

        elif entity_type_lower in ["mediaoutlet", "socialmediaplatform"]:
            return {
                "bio": f"Official account for {entity_name}. News and updates.",
                "persona": f"{entity_name} is a media entity that reports news and facilitates public discourse. The account shares timely updates and engages with the audience on current events.",
                "age": 30,  # Idade virtual institucional
                "gender": "other",  # Instituicao usa other
                "mbti": "ISTJ",  # Estilo institucional: rigoroso e conservador
                "country": "Brazil",
                "profession": "Media",
                "interested_topics": ["Notícias Gerais", "Atualidades", "Assuntos Públicos"],
            }

        elif entity_type_lower in ["university", "governmentagency", "ngo", "organization"]:
            return {
                "bio": f"Official account of {entity_name}.",
                "persona": f"{entity_name} is an institutional entity that communicates official positions, announcements, and engages with stakeholders on relevant matters.",
                "age": 30,  # Idade virtual institucional
                "gender": "other",  # Instituicao usa other
                "mbti": "ISTJ",  # Estilo institucional: rigoroso e conservador
                "country": "Brazil",
                "profession": entity_type,
                "interested_topics": ["Políticas Públicas", "Comunidade", "Comunicados Oficiais"],
            }

        else:
            # Perfil padrao
            return {
                "bio": entity_summary[:150] if entity_summary else f"{entity_type}: {entity_name}",
                "persona": entity_summary or f"{entity_name} is a {entity_type.lower()} participating in social discussions.",
                "age": random.randint(25, 50),
                "gender": random.choice(["male", "female"]),
                "mbti": random.choice(self.MBTI_TYPES),
                "country": random.choice(self.COUNTRIES),
                "profession": entity_type,
                "interested_topics": ["Geral", "Questões Sociais"],
            }

    def set_graph_id(self, graph_id: str):
        """Define graph_id para busca Zep"""
        self.graph_id = graph_id

    def generate_profiles_from_entities(
        self,
        entities: List[EntityNode],
        use_llm: bool = True,
        progress_callback: Optional[callable] = None,
        graph_id: Optional[str] = None,
        parallel_count: int = 15,
        realtime_output_path: Optional[str] = None,
        output_platform: str = "reddit"
    ) -> List[OasisAgentProfile]:
        """
        Gera Agent Profiles em lote a partir de entidades (com paralelismo)

        Args:
            entities: Lista de entidades
            use_llm: Se usa LLM para perfis detalhados
            progress_callback: Funcao de callback de progresso (current, total, message)
            graph_id: ID do grafo, para busca Zep com contexto mais rico
            parallel_count: Quantidade paralela, padrao 5
            realtime_output_path: Caminho de arquivo para escrita em tempo real (se fornecido, escreve a cada geracao)
            output_platform: Formato da plataforma de saida ("reddit" ou "twitter")

        Returns:
            Lista de Agent Profile
        """
        import concurrent.futures
        from threading import Lock

        # Define graph_id para busca Zep
        if graph_id:
            self.graph_id = graph_id

        total = len(entities)
        profiles = [None] * total  # Pre-aloca lista para manter ordem
        completed_count = [0]  # Usa lista para poder modificar em closure
        lock = Lock()

        # Funcao auxiliar de escrita em tempo real
        def save_profiles_realtime():
            """Salva profiles gerados em tempo real no arquivo"""
            if not realtime_output_path:
                return

            with lock:
                # Filtra profiles ja gerados
                existing_profiles = [p for p in profiles if p is not None]
                if not existing_profiles:
                    return

                try:
                    if output_platform == "reddit":
                        # Formato Reddit JSON
                        profiles_data = [p.to_reddit_format() for p in existing_profiles]
                        with open(realtime_output_path, 'w', encoding='utf-8') as f:
                            json.dump(profiles_data, f, ensure_ascii=False, indent=2)
                    else:
                        # Formato Twitter CSV
                        import csv
                        profiles_data = [p.to_twitter_format() for p in existing_profiles]
                        if profiles_data:
                            fieldnames = list(profiles_data[0].keys())
                            with open(realtime_output_path, 'w', encoding='utf-8', newline='') as f:
                                writer = csv.DictWriter(f, fieldnames=fieldnames)
                                writer.writeheader()
                                writer.writerows(profiles_data)
                except Exception as e:
                    logger.warning(f"Falha ao salvar profiles em tempo real: {e}")

        # Phase 3: define quais idx serao contrarians (~20% — 1 a cada 5).
        # Determinismo via idx evita variacao entre runs do mesmo grafo.
        # Skip se total < 5 (amostra pequena) ou se desativado por env.
        import os as _os
        contrarian_disabled = _os.environ.get("MIROFISH_DISABLE_CONTRARIANS", "0") == "1"
        contrarian_ratio = 5  # 1 a cada N
        contrarians_planned = 0 if (total < 5 or contrarian_disabled) else max(1, total // contrarian_ratio)
        if contrarians_planned > 0:
            logger.info(f"Devil's advocate: {contrarians_planned}/{total} perfis como contrarians (1/{contrarian_ratio})")

        def _stance_for(idx: int) -> str:
            if contrarians_planned <= 0:
                return "default"
            # Distribui contrarians uniformemente: idx 2, 7, 12, ...
            return "contrarian" if (idx % contrarian_ratio == 2) else "default"

        def generate_single_profile(idx: int, entity: EntityNode) -> tuple:
            """Funcao de trabalho para gerar um unico profile"""
            entity_type = entity.get_entity_type() or "Entity"

            try:
                profile = self.generate_profile_from_entity(
                    entity=entity,
                    user_id=idx,
                    use_llm=use_llm,
                    stance=_stance_for(idx),
                )

                # Imprime perfil gerado no console e log em tempo real
                self._print_generated_profile(entity.name, entity_type, profile)

                return idx, profile, None

            except Exception as e:
                logger.error(f"Geracao da entidade {entity.name}  - falha ao gerar perfil: {str(e)}")
                # Cria um profile basico
                fallback_profile = OasisAgentProfile(
                    user_id=idx,
                    user_name=self._generate_username(entity.name),
                    name=entity.name,
                    bio=f"{entity_type}: {entity.name}",
                    persona=entity.summary or f"A participant in social discussions.",
                    source_entity_uuid=entity.uuid,
                    source_entity_type=entity_type,
                )
                return idx, fallback_profile, str(e)

        logger.info(f"Iniciando geracao paralela de {total}  perfis de Agent (paralelismo: {parallel_count}）...")
        print(f"\n{'='*60}")
        print(f"Iniciando geracao de perfis de Agent - total de {total}  entidades, paralelismo: {parallel_count}")
        print(f"{'='*60}\n")

        # Executa em paralelo com pool de threads
        with concurrent.futures.ThreadPoolExecutor(max_workers=parallel_count) as executor:
            # Submete todas as tarefas
            future_to_entity = {
                executor.submit(generate_single_profile, idx, entity): (idx, entity)
                for idx, entity in enumerate(entities)
            }

            # Coleta resultados
            for future in concurrent.futures.as_completed(future_to_entity):
                idx, entity = future_to_entity[future]
                entity_type = entity.get_entity_type() or "Entity"

                try:
                    result_idx, profile, error = future.result()
                    profiles[result_idx] = profile

                    with lock:
                        completed_count[0] += 1
                        current = completed_count[0]

                    # Escreve no arquivo em tempo real
                    save_profiles_realtime()

                    if progress_callback:
                        progress_callback(
                            current,
                            total,
                            f"Concluido {current}/{total}: {entity.name}（{entity_type}）"
                        )

                    if error:
                        logger.warning(f"[{current}/{total}] {entity.name} usando perfil de fallback: {error}")
                    else:
                        logger.info(f"[{current}/{total}] Perfil gerado com sucesso: {entity.name} ({entity_type})")

                except Exception as e:
                    logger.error(f"Processando entidade {entity.name}  - excecao ocorrida: {str(e)}")
                    with lock:
                        completed_count[0] += 1
                    profiles[idx] = OasisAgentProfile(
                        user_id=idx,
                        user_name=self._generate_username(entity.name),
                        name=entity.name,
                        bio=f"{entity_type}: {entity.name}",
                        persona=entity.summary or "A participant in social discussions.",
                        source_entity_uuid=entity.uuid,
                        source_entity_type=entity_type,
                    )
                    # Escreve no arquivo em tempo real (mesmo se perfil de fallback)
                    save_profiles_realtime()

        print(f"\n{'='*60}")
        print(f"Geracao de perfis concluida! Total gerado: {len([p for p in profiles if p])}  Agents")
        print(f"{'='*60}\n")

        return profiles

    def _print_generated_profile(self, entity_name: str, entity_type: str, profile: OasisAgentProfile):
        """Imprime perfil gerado no console (conteudo completo, sem truncar)"""
        separator = "-" * 70

        # Constroi conteudo de saida completo (sem truncar)
        topics_str = ', '.join(profile.interested_topics) if profile.interested_topics else 'nenhum'

        output_lines = [
            f"\n{separator}",
            f"[Gerado] {entity_name} ({entity_type})",
            f"{separator}",
            f"Nome de usuario: {profile.user_name}",
            f"",
            f"[Bio]",
            f"{profile.bio}",
            f"",
            f"[Perfil detalhado]",
            f"{profile.persona}",
            f"",
            f"[Atributos basicos]",
            f"Idade: {profile.age} | Genero: {profile.gender} | MBTI: {profile.mbti}",
            f"Profissao: {profile.profession} | Pais: {profile.country}",
            f"Topicos de interesse: {topics_str}",
            separator
        ]

        output = "\n".join(output_lines)

        # Imprime apenas no console (evita duplicacao, logger nao imprime conteudo completo)
        print(output)

    def save_profiles(
        self,
        profiles: List[OasisAgentProfile],
        file_path: str,
        platform: str = "reddit"
    ):
        """
        Salva Profile em arquivo (escolhe formato correto por plataforma)

        Requisitos de formato da plataforma OASIS:
        - Twitter: formato CSV
        - Reddit: formato JSON

        Args:
            profiles: Lista de Profiles
            file_path: Caminho do arquivo
            platform: Tipo de plataforma ("reddit" ou "twitter")
        """
        if platform == "twitter":
            self._save_twitter_csv(profiles, file_path)
        else:
            self._save_reddit_json(profiles, file_path)

    def _save_twitter_csv(self, profiles: List[OasisAgentProfile], file_path: str):
        """
        Salva Twitter Profile em formato CSV (conforme OASIS oficial)

        Campos CSV exigidos pelo OASIS Twitter:
        - user_id: ID do usuario (comeca em 0 pela ordem do CSV)
        - name: Nome real do usuario
        - username: Nome de usuario no sistema
        - user_char: Descricao detalhada do perfil (injetada no prompt do sistema LLM, guiando comportamento do Agent)
        - description: Bio publica curta (exibida na pagina de perfil)

        Diferenca entre user_char e description:
        - - user_char: uso interno, prompt do sistema LLM, determina como o Agent pensa e age
        - - description: exibicao externa, bio visivel para outros usuarios
        """
        import csv

        # Garante extensao .csv
        if not file_path.endswith('.csv'):
            file_path = file_path.replace('.json', '.csv')

        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)

            # Escreve cabecalho exigido pelo OASIS
            headers = ['user_id', 'name', 'username', 'user_char', 'description']
            writer.writerow(headers)

            # Escreve linhas de dados
            for idx, profile in enumerate(profiles):
                # user_char: perfil completo (bio + persona), para prompt do sistema LLM
                user_char = profile.bio
                if profile.persona and profile.persona != profile.bio:
                    user_char = f"{profile.bio} {profile.persona}"
                # Processa quebras de linha (substituidas por espacos no CSV)
                user_char = user_char.replace('\n', ' ').replace('\r', ' ')

                # description: bio curta, para exibicao externa
                description = profile.bio.replace('\n', ' ').replace('\r', ' ')

                row = [
                    idx,                    # user_id: ID sequencial comecando em 0
                    profile.name,           # name: nome real
                    profile.user_name,      # username: Nome de usuario
                    user_char,              # user_char: perfil completo (uso interno LLM)
                    description             # description: bio curta (exibicao externa)
                ]
                writer.writerow(row)

        logger.info(f"Salvos {len(profiles)}  Twitter Profiles em {file_path} (formato CSV OASIS)")

    def _normalize_gender(self, gender: Optional[str]) -> str:
        """
        Padroniza campo gender para formato ingles exigido pelo OASIS

        OASIS exige: male, female, other
        """
        if not gender:
            return "other"

        gender_lower = gender.lower().strip()

        # Mapeamento do chines
        gender_map = {
            "male": "male",
            "female": "female",
            "other": "other",
            "other": "other",
            # Ingles ja existente
            "male": "male",
            "female": "female",
            "other": "other",
        }

        return gender_map.get(gender_lower, "other")

    def _save_reddit_json(self, profiles: List[OasisAgentProfile], file_path: str):
        """
        Salva Reddit Profile em formato JSON

        Usa formato consistente com to_reddit_format(), garantindo leitura correta pelo OASIS.
        Deve conter campo user_id, chave para matching do agent_graph.get_agent() do OASIS!

        Campos obrigatorios:
        - user_id: ID do usuario (inteiro, para matching com poster_agent_id em initial_posts)
        - username: Nome de usuario
        - name: Nome de exibicao
        - bio: Bio
        - persona: Perfil detalhado
        - age: Idade (inteiro)
        - gender: "male", "female", ou "other"
        - mbti: Tipo MBTI
        - country: Pais
        """
        data = []
        for idx, profile in enumerate(profiles):
            # Usa formato consistente com to_reddit_format()
            item = {
                "user_id": profile.user_id if profile.user_id is not None else idx,  # Chave: deve conter user_id
                "username": profile.user_name,
                "name": profile.name,
                "bio": profile.bio[:150] if profile.bio else f"{profile.name}",
                "persona": profile.persona or f"{profile.name} is a participant in social discussions.",
                "karma": profile.karma if profile.karma else 1000,
                "created_at": profile.created_at,
                # Campos obrigatorios do OASIS - garante valores padrao
                "age": profile.age if profile.age else 30,
                "gender": self._normalize_gender(profile.gender),
                "mbti": profile.mbti if profile.mbti else "ISTJ",
                "country": profile.country if profile.country else "Brazil",
            }

            # Campos opcionais
            if profile.profession:
                item["profession"] = profile.profession
            if profile.interested_topics:
                item["interested_topics"] = profile.interested_topics

            data.append(item)

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"Salvos {len(profiles)}  Reddit Profiles em {file_path} (formato JSON, com campo user_id)")

    # Mantem nome antigo como alias para compatibilidade
    def save_profiles_to_json(
        self,
        profiles: List[OasisAgentProfile],
        file_path: str,
        platform: str = "reddit"
    ):
        """[Obsoleto] Use o metodo save_profiles()"""
        logger.warning("save_profiles_to_json obsoleto, use o metodo save_profiles")
        self.save_profiles(profiles, file_path, platform)

