"""
Gerador inteligente de configuracao de simulacao.
Usa LLM para produzir parametros detalhados a partir do objetivo, do texto-base
e das informacoes extraidas do grafo.

Fluxo em etapas:
1. Gerar configuracao temporal
2. Gerar eventos e topicos
3. Gerar perfis de atividade dos agentes em lotes
4. Gerar configuracoes das plataformas
"""

import json
import math
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field, asdict
from datetime import datetime

from openai import OpenAI

from ..config import Config
from ..utils.logger import get_logger
from .zep_entity_reader import EntityNode, ZepEntityReader

logger = get_logger('mirofish.simulation_config')

# Configuração-base de rotina social em horário de Brasília
BRAZIL_TIMEZONE_CONFIG = {
    # Madrugada: atividade muito baixa
    "dead_hours": [0, 1, 2, 3, 4, 5],
    # Manhã: retomada gradual
    "morning_hours": [6, 7, 8],
    # Faixa de expediente
    "work_hours": [9, 10, 11, 12, 13, 14, 15, 16, 17, 18],
    # Noite: pico de uso
    "peak_hours": [19, 20, 21, 22],
    # Fim da noite: desaceleração
    "night_hours": [23],
    # Multiplicadores de atividade
    "activity_multipliers": {
        "dead": 0.05,
        "morning": 0.4,
        "work": 0.7,
        "peak": 1.5,
        "night": 0.5
    }
}


@dataclass
class AgentActivityConfig:
    """Configuracao de atividade de um agente."""
    agent_id: int
    entity_uuid: str
    entity_name: str
    entity_type: str
    
    # Nivel geral de atividade (0.0-1.0)
    activity_level: float = 0.5
    
    # Frequencia esperada de publicacoes por hora
    posts_per_hour: float = 1.0
    comments_per_hour: float = 2.0
    
    # Horas ativas (0-23)
    active_hours: List[int] = field(default_factory=lambda: list(range(8, 23)))
    
    # Faixa de atraso de resposta em minutos simulados
    response_delay_min: int = 5
    response_delay_max: int = 60
    
    # Vies afetivo (-1.0 a 1.0)
    sentiment_bias: float = 0.0
    
    # Posicionamento frente ao tema
    stance: str = "neutral"
    
    # Peso de influencia
    influence_weight: float = 1.0


@dataclass  
class TimeSimulationConfig:
    """Configuração temporal da simulação com base em rotina social brasileira."""
    # Duracao total da simulacao em horas
    total_simulation_hours: int = 72
    
    # Minutos simulados por rodada
    minutes_per_round: int = 60
    
    # Faixa de agentes ativados por hora
    agents_per_hour_min: int = 5
    agents_per_hour_max: int = 20
    
    # Pico típico de atividade no início da noite
    peak_hours: List[int] = field(default_factory=lambda: [19, 20, 21, 22])
    peak_activity_multiplier: float = 1.5
    
    # Faixa de baixa atividade na madrugada
    off_peak_hours: List[int] = field(default_factory=lambda: [0, 1, 2, 3, 4, 5])
    off_peak_activity_multiplier: float = 0.05
    
    # Faixa da manha
    morning_hours: List[int] = field(default_factory=lambda: [6, 7, 8])
    morning_activity_multiplier: float = 0.4
    
    # Faixa de expediente
    work_hours: List[int] = field(default_factory=lambda: [9, 10, 11, 12, 13, 14, 15, 16, 17, 18])
    work_activity_multiplier: float = 0.7


@dataclass
class EventConfig:
    """Configuracao de eventos da simulacao."""
    # Gatilhos iniciais
    initial_posts: List[Dict[str, Any]] = field(default_factory=list)
    
    # Eventos agendados
    scheduled_events: List[Dict[str, Any]] = field(default_factory=list)
    
    # Topicos quentes
    hot_topics: List[str] = field(default_factory=list)
    
    # Direção narrativa predominante
    narrative_direction: str = ""


@dataclass
class PlatformConfig:
    """Configuracao especifica de plataforma."""
    platform: str  # twitter or reddit
    
    # Pesos do algoritmo de recomendacao
    recency_weight: float = 0.4
    popularity_weight: float = 0.3
    relevance_weight: float = 0.3
    
    # Limiar de viralizacao
    viral_threshold: int = 10
    
    # Intensidade do efeito de bolha
    echo_chamber_strength: float = 0.5


@dataclass
class SimulationParameters:
    """Conjunto completo de parametros da simulacao."""
    # Metadados basicos
    simulation_id: str
    project_id: str
    graph_id: str
    simulation_requirement: str
    
    # Configuracao temporal
    time_config: TimeSimulationConfig = field(default_factory=TimeSimulationConfig)
    
    # Configuracoes dos agentes
    agent_configs: List[AgentActivityConfig] = field(default_factory=list)
    
    # Configuracao de eventos
    event_config: EventConfig = field(default_factory=EventConfig)
    
    # Configuracao das plataformas
    twitter_config: Optional[PlatformConfig] = None
    reddit_config: Optional[PlatformConfig] = None
    
    # Configuracao de LLM
    llm_model: str = ""
    llm_base_url: str = ""
    
    # Metadados de geracao
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    generation_reasoning: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionario."""
        time_dict = asdict(self.time_config)
        return {
            "simulation_id": self.simulation_id,
            "project_id": self.project_id,
            "graph_id": self.graph_id,
            "simulation_requirement": self.simulation_requirement,
            "time_config": time_dict,
            "agent_configs": [asdict(a) for a in self.agent_configs],
            "event_config": asdict(self.event_config),
            "twitter_config": asdict(self.twitter_config) if self.twitter_config else None,
            "reddit_config": asdict(self.reddit_config) if self.reddit_config else None,
            "llm_model": self.llm_model,
            "llm_base_url": self.llm_base_url,
            "generated_at": self.generated_at,
            "generation_reasoning": self.generation_reasoning,
        }
    
    def to_json(self, indent: int = 2) -> str:
        """Converte para string JSON."""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)


class SimulationConfigGenerator:
    """
    Gerador inteligente de configuracao de simulacao.

    Analisa objetivo, documentos e entidades do grafo para produzir
    uma configuracao automatica e consistente.
    """
    
    # Limite maximo de contexto
    MAX_CONTEXT_LENGTH = 50000
    # Quantidade de agentes por lote
    AGENTS_PER_BATCH = 15
    
    # Limites de contexto por etapa
    TIME_CONFIG_CONTEXT_LENGTH = 10000
    EVENT_CONFIG_CONTEXT_LENGTH = 8000
    ENTITY_SUMMARY_LENGTH = 300
    AGENT_SUMMARY_LENGTH = 300
    ENTITIES_PER_TYPE_DISPLAY = 20
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model_name: Optional[str] = None
    ):
        self.api_key = api_key or Config.LLM_API_KEY
        self.base_url = base_url or Config.LLM_BASE_URL
        self.model_name = model_name or Config.LLM_MODEL_NAME
        
        if not self.api_key:
            raise ValueError("LLM_API_KEY nao configurada")
        
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
    
    def generate_config(
        self,
        simulation_id: str,
        project_id: str,
        graph_id: str,
        simulation_requirement: str,
        document_text: str,
        entities: List[EntityNode],
        enable_twitter: bool = True,
        enable_reddit: bool = True,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
    ) -> SimulationParameters:
        """Gera a configuracao completa da simulacao em varias etapas."""
        logger.info(f"Iniciando geracao inteligente da simulacao: simulation_id={simulation_id}, entidades={len(entities)}")
        
        # Calcula o total de etapas.
        num_batches = math.ceil(len(entities) / self.AGENTS_PER_BATCH)
        total_steps = 3 + num_batches
        current_step = 0
        
        def report_progress(step: int, message: str):
            nonlocal current_step
            current_step = step
            if progress_callback:
                progress_callback(step, total_steps, message)
            logger.info(f"[{step}/{total_steps}] {message}")
        
        # 1. Monta o contexto-base.
        context = self._build_context(
            simulation_requirement=simulation_requirement,
            document_text=document_text,
            entities=entities
        )
        
        reasoning_parts = []
        
        # Etapa 1: configuracao temporal.
        report_progress(1, "Gerando configuracao temporal...")
        num_entities = len(entities)
        time_config_result = self._generate_time_config(context, num_entities)
        time_config = self._parse_time_config(time_config_result, num_entities)
        reasoning_parts.append(f"Configuracao temporal: {time_config_result.get('reasoning', 'ok')}")
        
        # Etapa 2: eventos e topicos.
        report_progress(2, "Gerando eventos e topicos...")
        event_config_result = self._generate_event_config(context, simulation_requirement, entities)
        event_config = self._parse_event_config(event_config_result)
        reasoning_parts.append(f"Configuracao de eventos: {event_config_result.get('reasoning', 'ok')}")
        
        # Etapas 3..N: configuracoes de agentes em lotes.
        all_agent_configs = []
        for batch_idx in range(num_batches):
            start_idx = batch_idx * self.AGENTS_PER_BATCH
            end_idx = min(start_idx + self.AGENTS_PER_BATCH, len(entities))
            batch_entities = entities[start_idx:end_idx]
            
            report_progress(
                3 + batch_idx,
                f"Gerando configuracoes de agentes ({start_idx + 1}-{end_idx}/{len(entities)})..."
            )
            
            batch_configs = self._generate_agent_configs_batch(
                context=context,
                entities=batch_entities,
                start_idx=start_idx,
                simulation_requirement=simulation_requirement
            )
            all_agent_configs.extend(batch_configs)
        
        reasoning_parts.append(f"Configuracao de agentes: {len(all_agent_configs)} gerados")
        
        # Atribui autores para as postagens iniciais.
        logger.info("Atribuindo autores adequados para as postagens iniciais...")
        event_config = self._assign_initial_post_agents(event_config, all_agent_configs)
        assigned_count = len([p for p in event_config.initial_posts if p.get("poster_agent_id") is not None])
        reasoning_parts.append(f"Postagens iniciais atribuidas: {assigned_count}")
        
        # Ultima etapa: configuracao das plataformas.
        report_progress(total_steps, "Gerando configuracao das plataformas...")
        twitter_config = None
        reddit_config = None
        
        if enable_twitter:
            twitter_config = PlatformConfig(
                platform="twitter",
                recency_weight=0.4,
                popularity_weight=0.3,
                relevance_weight=0.3,
                viral_threshold=10,
                echo_chamber_strength=0.5
            )
        
        if enable_reddit:
            reddit_config = PlatformConfig(
                platform="reddit",
                recency_weight=0.3,
                popularity_weight=0.4,
                relevance_weight=0.3,
                viral_threshold=15,
                echo_chamber_strength=0.6
            )
        
        # Monta o objeto final de parametros.
        params = SimulationParameters(
            simulation_id=simulation_id,
            project_id=project_id,
            graph_id=graph_id,
            simulation_requirement=simulation_requirement,
            time_config=time_config,
            agent_configs=all_agent_configs,
            event_config=event_config,
            twitter_config=twitter_config,
            reddit_config=reddit_config,
            llm_model=self.model_name,
            llm_base_url=self.base_url,
            generation_reasoning=" | ".join(reasoning_parts)
        )
        
        logger.info(f"Geracao da simulacao concluida: {len(params.agent_configs)} configuracoes de agente")
        
        return params
    
    def _build_context(
        self,
        simulation_requirement: str,
        document_text: str,
        entities: List[EntityNode]
    ) -> str:
        """Monta o contexto para o LLM e o limita ao tamanho maximo."""
        
        # Resume as entidades.
        entity_summary = self._summarize_entities(entities)
        
        # Monta o contexto-base.
        context_parts = [
            f"## Objetivo da simulacao\n{simulation_requirement}",
            f"\n## Entidades ({len(entities)})\n{entity_summary}",
        ]
        
        current_length = sum(len(p) for p in context_parts)
        remaining_length = self.MAX_CONTEXT_LENGTH - current_length - 500  # Reserva uma margem de seguranca.
        
        if remaining_length > 0 and document_text:
            doc_text = document_text[:remaining_length]
            if len(document_text) > remaining_length:
                doc_text += "\n...(documento truncado)"
            context_parts.append(f"\n## Documento-base\n{doc_text}")
        
        return "\n".join(context_parts)
    
    def _summarize_entities(self, entities: List[EntityNode]) -> str:
        """Gera um resumo das entidades agrupadas por tipo."""
        lines = []
        
        # Agrupa por tipo.
        by_type: Dict[str, List[EntityNode]] = {}
        for e in entities:
            t = e.get_entity_type() or "Unknown"
            if t not in by_type:
                by_type[t] = []
            by_type[t].append(e)
        
        for entity_type, type_entities in by_type.items():
            lines.append(f"\n### {entity_type} ({len(type_entities)})")
            # Usa os limites configurados para exibicao e resumo.
            display_count = self.ENTITIES_PER_TYPE_DISPLAY
            summary_len = self.ENTITY_SUMMARY_LENGTH
            for e in type_entities[:display_count]:
                summary_preview = (e.summary[:summary_len] + "...") if len(e.summary) > summary_len else e.summary
                lines.append(f"- {e.name}: {summary_preview}")
            if len(type_entities) > display_count:
                lines.append(f"  ... e mais {len(type_entities) - display_count}")
        
        return "\n".join(lines)
    
    def _call_llm_with_retry(self, prompt: str, system_prompt: str) -> Dict[str, Any]:
        """Executa chamada ao LLM com retry e tentativa de reparo do JSON."""
        import re
        
        max_attempts = 3
        last_error = None
        
        for attempt in range(max_attempts):
            try:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.7 - (attempt * 0.1)  # Reduz a temperatura a cada tentativa.
                    # Nao fixa max_tokens para evitar truncamento desnecessario.
                )
                
                content = response.choices[0].message.content
                finish_reason = response.choices[0].finish_reason
                
                # Verifica truncamento.
                if finish_reason == 'length':
                    logger.warning(f"Saida do LLM truncada (tentativa {attempt+1})")
                    content = self._fix_truncated_json(content)
                
                # Tenta interpretar o JSON retornado.
                try:
                    return json.loads(content)
                except json.JSONDecodeError as e:
                    logger.warning(f"Falha ao interpretar JSON (tentativa {attempt+1}): {str(e)[:80]}")
                    
                    # Tenta reparar o JSON.
                    fixed = self._try_fix_config_json(content)
                    if fixed:
                        return fixed
                    
                    last_error = e
                    
            except Exception as e:
                logger.warning(f"Falha na chamada ao LLM (tentativa {attempt+1}): {str(e)[:80]}")
                last_error = e
                import time
                time.sleep(2 * (attempt + 1))
        
        raise last_error or Exception("Falha na chamada ao LLM")
    
    def _fix_truncated_json(self, content: str) -> str:
        """Fecha estruturas simples em um JSON truncado."""
        content = content.strip()
        
        # Conta estruturas ainda abertas.
        open_braces = content.count('{') - content.count('}')
        open_brackets = content.count('[') - content.count(']')
        
        # Fecha string se necessario.
        if content and content[-1] not in '",}]':
            content += '"'
        
        # Fecha colchetes e chaves.
        content += ']' * open_brackets
        content += '}' * open_braces
        
        return content
    
    def _try_fix_config_json(self, content: str) -> Optional[Dict[str, Any]]:
        """Tenta recuperar um JSON de configuracao invalido."""
        import re
        
        # Primeiro trata truncamento.
        content = self._fix_truncated_json(content)
        
        # Extrai apenas o trecho JSON.
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            json_str = json_match.group()
            
            # Remove quebras de linha no interior das strings.
            def fix_string(match):
                s = match.group(0)
                s = s.replace('\n', ' ').replace('\r', ' ')
                s = re.sub(r'\s+', ' ', s)
                return s
            
            json_str = re.sub(r'"[^"\\]*(?:\\.[^"\\]*)*"', fix_string, json_str)
            
            try:
                return json.loads(json_str)
            except:
                # Como fallback, remove caracteres de controle.
                json_str = re.sub(r'[\x00-\x1f\x7f-\x9f]', ' ', json_str)
                json_str = re.sub(r'\s+', ' ', json_str)
                try:
                    return json.loads(json_str)
                except:
                    pass
        
        return None
    
    def _generate_time_config(self, context: str, num_entities: int) -> Dict[str, Any]:
        """Gera a configuracao temporal."""
        # Limita o contexto para essa etapa.
        context_truncated = context[:self.TIME_CONFIG_CONTEXT_LENGTH]
        
        # Define o teto de agentes ativos por hora.
        max_agents_allowed = max(1, int(num_entities * 0.9))
        
        prompt = f"""Com base no objetivo abaixo, gere a configuracao temporal da simulacao.

{context_truncated}

## Tarefa
Gere um JSON de configuracao temporal.

### Principios-base
- Use como padrão uma rotina social compatível com Brasil, preferencialmente horário de Brasília
- Madrugada 0-5h quase sem atividade (multiplicador 0.05)
- Manhã 6-8h em retomada gradual (multiplicador 0.4)
- Expediente 9-18h com atividade moderada (multiplicador 0.7)
- Noite 19-22h como pico principal (multiplicador 1.5)
- Após 23h a atividade cai (multiplicador 0.5)
- Regra geral: madrugada baixa, manhã crescente, expediente moderado e noite em pico
- Os valores abaixo sao apenas referencia; ajuste conforme a natureza do evento e os grupos envolvidos
  - Exemplo: estudantes podem ter pico entre 21h e 23h; midia pode operar quase o dia todo; orgaos publicos tendem ao horario comercial
  - Exemplo: eventos urgentes podem manter discussao de madrugada, entao `off_peak_hours` pode ser reduzido

### Formato de retorno
Retorne apenas JSON puro, sem markdown.

Exemplo:
{{
    "total_simulation_hours": 72,
    "minutes_per_round": 60,
    "agents_per_hour_min": 5,
    "agents_per_hour_max": 50,
    "peak_hours": [19, 20, 21, 22],
    "off_peak_hours": [0, 1, 2, 3, 4, 5],
    "morning_hours": [6, 7, 8],
    "work_hours": [9, 10, 11, 12, 13, 14, 15, 16, 17, 18],
    "reasoning": "Breve justificativa da configuracao temporal"
}}

Campos:
- total_simulation_hours (int): duracao total da simulacao, entre 24 e 168 horas
- minutes_per_round (int): minutos simulados por rodada, entre 30 e 120
- agents_per_hour_min (int): minimo de agentes ativos por hora, entre 1 e {max_agents_allowed}
- agents_per_hour_max (int): maximo de agentes ativos por hora, entre 1 e {max_agents_allowed}
- peak_hours (array[int]): horas de pico
- off_peak_hours (array[int]): horas de baixa atividade
- morning_hours (array[int]): horas da manha
- work_hours (array[int]): horario comercial predominante
- reasoning (string): breve explicacao do criterio adotado"""

        system_prompt = "Você é especialista em simulação social. Retorne JSON puro e use, por padrão, uma rotina compatível com Brasil e horário de Brasília."
        
        try:
            return self._call_llm_with_retry(prompt, system_prompt)
        except Exception as e:
            logger.warning(f"Falha ao gerar configuracao temporal com LLM: {e}. Usando padrao.")
            return self._get_default_time_config(num_entities)
    
    def _get_default_time_config(self, num_entities: int) -> Dict[str, Any]:
        """Retorna a configuração temporal padrão em ritmo social brasileiro."""
        return {
            "total_simulation_hours": 72,
            "minutes_per_round": 60,  # Cada rodada representa 1 hora simulada.
            "agents_per_hour_min": max(1, num_entities // 15),
            "agents_per_hour_max": max(5, num_entities // 5),
            "peak_hours": [19, 20, 21, 22],
            "off_peak_hours": [0, 1, 2, 3, 4, 5],
            "morning_hours": [6, 7, 8],
            "work_hours": [9, 10, 11, 12, 13, 14, 15, 16, 17, 18],
            "reasoning": "Uso do padrão brasileiro de atividade social, com 1 hora por rodada"
        }
    
    def _parse_time_config(self, result: Dict[str, Any], num_entities: int) -> TimeSimulationConfig:
        """Interpreta a configuracao temporal e limita os valores ao total de agentes."""
        # Le os valores brutos.
        agents_per_hour_min = result.get("agents_per_hour_min", max(1, num_entities // 15))
        agents_per_hour_max = result.get("agents_per_hour_max", max(5, num_entities // 5))
        
        # Garante que nao excedam o numero total de agentes.
        if agents_per_hour_min > num_entities:
            logger.warning(f"agents_per_hour_min ({agents_per_hour_min}) excede o total de agentes ({num_entities}); valor ajustado")
            agents_per_hour_min = max(1, num_entities // 10)
        
        if agents_per_hour_max > num_entities:
            logger.warning(f"agents_per_hour_max ({agents_per_hour_max}) excede o total de agentes ({num_entities}); valor ajustado")
            agents_per_hour_max = max(agents_per_hour_min + 1, num_entities // 2)
        
        # Garante a relacao min < max.
        if agents_per_hour_min >= agents_per_hour_max:
            agents_per_hour_min = max(1, agents_per_hour_max // 2)
            logger.warning(f"agents_per_hour_min >= agents_per_hour_max; min ajustado para {agents_per_hour_min}")
        
        return TimeSimulationConfig(
            total_simulation_hours=result.get("total_simulation_hours", 72),
            minutes_per_round=result.get("minutes_per_round", 60),  # Padrao de 1 hora por rodada.
            agents_per_hour_min=agents_per_hour_min,
            agents_per_hour_max=agents_per_hour_max,
            peak_hours=result.get("peak_hours", [19, 20, 21, 22]),
            off_peak_hours=result.get("off_peak_hours", [0, 1, 2, 3, 4, 5]),
            off_peak_activity_multiplier=0.05,
            morning_hours=result.get("morning_hours", [6, 7, 8]),
            morning_activity_multiplier=0.4,
            work_hours=result.get("work_hours", list(range(9, 19))),
            work_activity_multiplier=0.7,
            peak_activity_multiplier=1.5
        )
    
    def _generate_event_config(
        self, 
        context: str, 
        simulation_requirement: str,
        entities: List[EntityNode]
    ) -> Dict[str, Any]:
        """Gera a configuracao de eventos."""
        
        # Lista os tipos de entidade disponiveis para o LLM.
        entity_types_available = list(set(
            e.get_entity_type() or "Unknown" for e in entities
        ))
        
        # Separa exemplos representativos por tipo.
        type_examples = {}
        for e in entities:
            etype = e.get_entity_type() or "Unknown"
            if etype not in type_examples:
                type_examples[etype] = []
            if len(type_examples[etype]) < 3:
                type_examples[etype].append(e.name)
        
        type_info = "\n".join([
            f"- {t}: {', '.join(examples)}" 
            for t, examples in type_examples.items()
        ])
        
        # Limita o contexto para esta etapa.
        context_truncated = context[:self.EVENT_CONFIG_CONTEXT_LENGTH]
        
        prompt = f"""Com base no objetivo abaixo, gere a configuracao de eventos.

Objetivo da simulacao: {simulation_requirement}

{context_truncated}

## Tipos de entidade disponiveis e exemplos
{type_info}

## Tarefa
Gere um JSON de eventos que:
- extraia os topicos quentes
- descreva a direcao narrativa predominante
- crie postagens iniciais, e cada postagem deve conter `poster_type`

`poster_type` deve ser escolhido exatamente entre os tipos disponiveis acima, para que cada postagem inicial possa ser atribuida a um agente compativel.
Exemplo: declaracoes oficiais devem vir de Official/University; noticias de MediaOutlet; opinioes estudantis de Student.

Retorne apenas JSON puro, sem markdown:
{{
    "hot_topics": ["topico1", "topico2"],
    "narrative_direction": "<descrição da direção narrativa predominante>",
    "initial_posts": [
        {{"content": "conteudo da postagem", "poster_type": "tipo de entidade"}},
        ...
    ],
    "reasoning": "<breve explicacao>"
}}"""

        system_prompt = "Você é especialista em análise de debate público. Retorne JSON puro. `poster_type` deve corresponder exatamente a um tipo de entidade disponível."
        
        try:
            return self._call_llm_with_retry(prompt, system_prompt)
        except Exception as e:
            logger.warning(f"Falha ao gerar configuracao de eventos com LLM: {e}. Usando padrao.")
            return {
                "hot_topics": [],
                "narrative_direction": "",
                "initial_posts": [],
                "reasoning": "Configuracao padrao aplicada"
            }
    
    def _parse_event_config(self, result: Dict[str, Any]) -> EventConfig:
        """Interpreta o resultado de configuracao de eventos."""
        return EventConfig(
            initial_posts=result.get("initial_posts", []),
            scheduled_events=[],
            hot_topics=result.get("hot_topics", []),
            narrative_direction=result.get("narrative_direction", "")
        )
    
    def _assign_initial_post_agents(
        self,
        event_config: EventConfig,
        agent_configs: List[AgentActivityConfig]
    ) -> EventConfig:
        """Atribui a cada postagem inicial um agente compativel com `poster_type`."""
        if not event_config.initial_posts:
            return event_config
        
        # Indexa os agentes por tipo de entidade.
        agents_by_type: Dict[str, List[AgentActivityConfig]] = {}
        for agent in agent_configs:
            etype = agent.entity_type.lower()
            if etype not in agents_by_type:
                agents_by_type[etype] = []
            agents_by_type[etype].append(agent)
        
        # Mapeamento de aliases para tolerar variacoes do LLM.
        type_aliases = {
            "official": ["official", "university", "governmentagency", "government"],
            "university": ["university", "official"],
            "mediaoutlet": ["mediaoutlet", "media"],
            "student": ["student", "person"],
            "professor": ["professor", "expert", "teacher"],
            "alumni": ["alumni", "person"],
            "organization": ["organization", "ngo", "company", "group"],
            "person": ["person", "student", "alumni"],
        }
        
        # Mantem um cursor por tipo para evitar repetir sempre o mesmo agente.
        used_indices: Dict[str, int] = {}
        
        updated_posts = []
        for post in event_config.initial_posts:
            poster_type = post.get("poster_type", "").lower()
            content = post.get("content", "")
            
            # Tenta localizar um agente compativel.
            matched_agent_id = None
            
            # 1. Correspondencia direta.
            if poster_type in agents_by_type:
                agents = agents_by_type[poster_type]
                idx = used_indices.get(poster_type, 0) % len(agents)
                matched_agent_id = agents[idx].agent_id
                used_indices[poster_type] = idx + 1
            else:
                # 2. Correspondencia por alias.
                for alias_key, aliases in type_aliases.items():
                    if poster_type in aliases or alias_key == poster_type:
                        for alias in aliases:
                            if alias in agents_by_type:
                                agents = agents_by_type[alias]
                                idx = used_indices.get(alias, 0) % len(agents)
                                matched_agent_id = agents[idx].agent_id
                                used_indices[alias] = idx + 1
                                break
                    if matched_agent_id is not None:
                        break
            
            # 3. Fallback: agente de maior influencia.
            if matched_agent_id is None:
                logger.warning(f"Nenhum agente compativel com '{poster_type}' foi encontrado; usando o de maior influencia")
                if agent_configs:
                    # Seleciona o agente de maior influencia.
                    sorted_agents = sorted(agent_configs, key=lambda a: a.influence_weight, reverse=True)
                    matched_agent_id = sorted_agents[0].agent_id
                else:
                    matched_agent_id = 0
            
            updated_posts.append({
                "content": content,
                "poster_type": post.get("poster_type", "Unknown"),
                "poster_agent_id": matched_agent_id
            })
            
            logger.info(f"Postagem inicial atribuida: poster_type='{poster_type}' -> agent_id={matched_agent_id}")
        
        event_config.initial_posts = updated_posts
        return event_config
    
    def _generate_agent_configs_batch(
        self,
        context: str,
        entities: List[EntityNode],
        start_idx: int,
        simulation_requirement: str
    ) -> List[AgentActivityConfig]:
        """Gera configuracoes de agentes em lote."""
        
        # Monta a lista resumida de entidades do lote.
        entity_list = []
        summary_len = self.AGENT_SUMMARY_LENGTH
        for i, e in enumerate(entities):
            entity_list.append({
                "agent_id": start_idx + i,
                "entity_name": e.name,
                "entity_type": e.get_entity_type() or "Unknown",
                "summary": e.summary[:summary_len] if e.summary else ""
            })
        
        prompt = f"""Com base nos dados abaixo, gere a configuracao de atividade social para cada entidade.

Objetivo da simulacao: {simulation_requirement}

## Lista de entidades
```json
{json.dumps(entity_list, ensure_ascii=False, indent=2)}
```

## Tarefa
Gere a configuracao de atividade para cada entidade. Considere:
- **Use rotina compatível com Brasil/DF**: madrugada 0-5h quase sem atividade e noite 19-22h como pico principal
- **Instituições oficiais** (University/GovernmentAgency): baixa atividade (0.1-0.3), atuação em horário comercial (9-17), resposta lenta (60-240 min), alta influência (2.5-3.0)
- **Mídia** (MediaOutlet): atividade média (0.4-0.6), cobertura ampla (8-23), resposta rápida (5-30 min), alta influência (2.0-2.5)
- **Perfis pessoais** (Student/Person/Alumni): atividade alta (0.6-0.9), maior presença à noite (18-23), resposta rápida (1-15 min), influência menor (0.8-1.2)
- **Especialistas e figuras públicas**: atividade média (0.4-0.6), influência média-alta (1.5-2.0)

Retorne apenas JSON puro, sem markdown:
{{
    "agent_configs": [
        {{
            "agent_id": <deve corresponder ao valor de entrada>,
            "activity_level": <0.0-1.0>,
            "posts_per_hour": <frequencia de postagens>,
            "comments_per_hour": <frequencia de comentarios>,
            "active_hours": [<lista de horas ativas, considerando rotina social brasileira>],
            "response_delay_min": <atraso minimo em minutos>,
            "response_delay_max": <atraso maximo em minutos>,
            "sentiment_bias": <-1.0 a 1.0>,
            "stance": "<supportive/opposing/neutral/observer>",
            "influence_weight": <peso de influencia>
        }},
        ...
    ]
}}"""

        system_prompt = "Você é especialista em comportamento em redes sociais. Retorne JSON puro com perfis compatíveis com rotina social brasileira."
        
        try:
            result = self._call_llm_with_retry(prompt, system_prompt)
            llm_configs = {cfg["agent_id"]: cfg for cfg in result.get("agent_configs", [])}
        except Exception as e:
            logger.warning(f"Falha ao gerar lote de configuracoes de agentes com LLM: {e}. Usando regras.")
            llm_configs = {}
        
        # Converte o resultado em objetos internos.
        configs = []
        for i, entity in enumerate(entities):
            agent_id = start_idx + i
            cfg = llm_configs.get(agent_id, {})
            
            # Se o LLM nao retornou o agente, aplica regras locais.
            if not cfg:
                cfg = self._generate_agent_config_by_rule(entity)
            
            config = AgentActivityConfig(
                agent_id=agent_id,
                entity_uuid=entity.uuid,
                entity_name=entity.name,
                entity_type=entity.get_entity_type() or "Unknown",
                activity_level=cfg.get("activity_level", 0.5),
                posts_per_hour=cfg.get("posts_per_hour", 0.5),
                comments_per_hour=cfg.get("comments_per_hour", 1.0),
                active_hours=cfg.get("active_hours", list(range(9, 23))),
                response_delay_min=cfg.get("response_delay_min", 5),
                response_delay_max=cfg.get("response_delay_max", 60),
                sentiment_bias=cfg.get("sentiment_bias", 0.0),
                stance=cfg.get("stance", "neutral"),
                influence_weight=cfg.get("influence_weight", 1.0)
            )
            configs.append(config)
        
        return configs
    
    def _generate_agent_config_by_rule(self, entity: EntityNode) -> Dict[str, Any]:
        """Gera a configuração de um agente com regras baseadas em rotina social brasileira."""
        entity_type = (entity.get_entity_type() or "Unknown").lower()
        
        if entity_type in ["university", "governmentagency", "ngo"]:
            # Instituicoes oficiais: horario comercial, baixa frequencia, alta influencia.
            return {
                "activity_level": 0.2,
                "posts_per_hour": 0.1,
                "comments_per_hour": 0.05,
                "active_hours": list(range(9, 18)),  # 9:00-17:59
                "response_delay_min": 60,
                "response_delay_max": 240,
                "sentiment_bias": 0.0,
                "stance": "neutral",
                "influence_weight": 3.0
            }
        elif entity_type in ["mediaoutlet"]:
            # Midia: cobertura ampla, frequencia media, alta influencia.
            return {
                "activity_level": 0.5,
                "posts_per_hour": 0.8,
                "comments_per_hour": 0.3,
                "active_hours": list(range(7, 24)),  # 7:00-23:59
                "response_delay_min": 5,
                "response_delay_max": 30,
                "sentiment_bias": 0.0,
                "stance": "observer",
                "influence_weight": 2.5
            }
        elif entity_type in ["professor", "expert", "official"]:
            # Especialistas e professores: expediente mais noite, frequencia media.
            return {
                "activity_level": 0.4,
                "posts_per_hour": 0.3,
                "comments_per_hour": 0.5,
                "active_hours": list(range(8, 22)),  # 8:00-21:59
                "response_delay_min": 15,
                "response_delay_max": 90,
                "sentiment_bias": 0.0,
                "stance": "neutral",
                "influence_weight": 2.0
            }
        elif entity_type in ["student"]:
            # Estudantes: concentracao maior no periodo noturno.
            return {
                "activity_level": 0.8,
                "posts_per_hour": 0.6,
                "comments_per_hour": 1.5,
                "active_hours": [8, 9, 10, 11, 12, 13, 18, 19, 20, 21, 22, 23],  # Manha + noite.
                "response_delay_min": 1,
                "response_delay_max": 15,
                "sentiment_bias": 0.0,
                "stance": "neutral",
                "influence_weight": 0.8
            }
        elif entity_type in ["alumni"]:
            # Ex-alunos: maior presenca na noite.
            return {
                "activity_level": 0.6,
                "posts_per_hour": 0.4,
                "comments_per_hour": 0.8,
                "active_hours": [12, 13, 19, 20, 21, 22, 23],  # Almoco + noite.
                "response_delay_min": 5,
                "response_delay_max": 30,
                "sentiment_bias": 0.0,
                "stance": "neutral",
                "influence_weight": 1.0
            }
        else:
            # Perfis gerais: pico principal no periodo noturno.
            return {
                "activity_level": 0.7,
                "posts_per_hour": 0.5,
                "comments_per_hour": 1.2,
                "active_hours": [9, 10, 11, 12, 13, 18, 19, 20, 21, 22, 23],  # Dia + noite.
                "response_delay_min": 2,
                "response_delay_max": 20,
                "sentiment_bias": 0.0,
                "stance": "neutral",
                "influence_weight": 1.0
            }
    

