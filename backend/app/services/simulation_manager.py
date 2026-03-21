"""
Gerenciador de simulacao OASIS
Gerencia simulacao paralela em duas plataformas: Twitter e Reddit
Usa scripts predefinidos + LLM para gerar parametros de configuracao
"""

import os
import json
import shutil
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from ..config import Config
from ..utils.logger import get_logger
from .zep_entity_reader import ZepEntityReader, FilteredEntities
from .oasis_profile_generator import OasisProfileGenerator, OasisAgentProfile
from .simulation_config_generator import SimulationConfigGenerator, SimulationParameters

logger = get_logger('mirofish.simulation')


class SimulationStatus(str, Enum):
    """Estado da simulacao"""
    CREATED = "created"
    PREPARING = "preparing"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"      # simulacao parada manualmente
    COMPLETED = "completed"  # simulacao concluida naturalmente
    FAILED = "failed"


class PlatformType(str, Enum):
    """Tipo de plataforma"""
    TWITTER = "twitter"
    REDDIT = "reddit"


@dataclass
class SimulationState:
    """Estado da simulacao"""
    simulation_id: str
    project_id: str
    graph_id: str
    
    # Estado de habilitacao da plataforma
    enable_twitter: bool = True
    enable_reddit: bool = True
    
    # Estado
    status: SimulationStatus = SimulationStatus.CREATED
    
    # Dados da fase de preparacao
    entities_count: int = 0
    profiles_count: int = 0
    entity_types: List[str] = field(default_factory=list)
    
    # Informacoes de geracao de configuracao
    config_generated: bool = False
    config_reasoning: str = ""
    
    # Dados de execucao
    current_round: int = 0
    twitter_status: str = "not_started"
    reddit_status: str = "not_started"
    
    # Timestamp
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    # Informacoes de erro
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Dicionario de estado completo (uso interno)"""
        return {
            "simulation_id": self.simulation_id,
            "project_id": self.project_id,
            "graph_id": self.graph_id,
            "enable_twitter": self.enable_twitter,
            "enable_reddit": self.enable_reddit,
            "status": self.status.value,
            "entities_count": self.entities_count,
            "profiles_count": self.profiles_count,
            "entity_types": self.entity_types,
            "config_generated": self.config_generated,
            "config_reasoning": self.config_reasoning,
            "current_round": self.current_round,
            "twitter_status": self.twitter_status,
            "reddit_status": self.reddit_status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "error": self.error,
        }
    
    def to_simple_dict(self) -> Dict[str, Any]:
        """Dicionario de estado simplificado (retorno da API)"""
        return {
            "simulation_id": self.simulation_id,
            "project_id": self.project_id,
            "graph_id": self.graph_id,
            "status": self.status.value,
            "entities_count": self.entities_count,
            "profiles_count": self.profiles_count,
            "entity_types": self.entity_types,
            "config_generated": self.config_generated,
            "error": self.error,
        }


class SimulationManager:
    """
    Gerenciador de simulacao
    
    Funcionalidades principais:
    1. Ler entidades do grafo Zep e filtrar
    2. Gerar OASIS Agent Profile
    3. Usar LLM para gerar parametros de configuracao da simulacao
    4. Preparar todos os arquivos necessarios para os scripts
    """
    
    # Diretorio de armazenamento de dados de simulacao
    SIMULATION_DATA_DIR = os.path.join(
        os.path.dirname(__file__), 
        '../../uploads/simulations'
    )
    
    def __init__(self):
        # Garante que o diretorio existe
        os.makedirs(self.SIMULATION_DATA_DIR, exist_ok=True)
        
        # Cache de estado de simulacao em memoria
        self._simulations: Dict[str, SimulationState] = {}
    
    def _get_simulation_dir(self, simulation_id: str) -> str:
        """Obtem diretorio de dados da simulacao"""
        sim_dir = os.path.join(self.SIMULATION_DATA_DIR, simulation_id)
        os.makedirs(sim_dir, exist_ok=True)
        return sim_dir
    
    def _save_simulation_state(self, state: SimulationState):
        """Salva estado da simulacao em arquivo"""
        sim_dir = self._get_simulation_dir(state.simulation_id)
        state_file = os.path.join(sim_dir, "state.json")
        
        state.updated_at = datetime.now().isoformat()
        
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(state.to_dict(), f, ensure_ascii=False, indent=2)
        
        self._simulations[state.simulation_id] = state
    
    def _load_simulation_state(self, simulation_id: str) -> Optional[SimulationState]:
        """Carrega estado da simulacao do arquivo"""
        if simulation_id in self._simulations:
            return self._simulations[simulation_id]
        
        sim_dir = self._get_simulation_dir(simulation_id)
        state_file = os.path.join(sim_dir, "state.json")
        
        if not os.path.exists(state_file):
            return None
        
        with open(state_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        state = SimulationState(
            simulation_id=simulation_id,
            project_id=data.get("project_id", ""),
            graph_id=data.get("graph_id", ""),
            enable_twitter=data.get("enable_twitter", True),
            enable_reddit=data.get("enable_reddit", True),
            status=SimulationStatus(data.get("status", "created")),
            entities_count=data.get("entities_count", 0),
            profiles_count=data.get("profiles_count", 0),
            entity_types=data.get("entity_types", []),
            config_generated=data.get("config_generated", False),
            config_reasoning=data.get("config_reasoning", ""),
            current_round=data.get("current_round", 0),
            twitter_status=data.get("twitter_status", "not_started"),
            reddit_status=data.get("reddit_status", "not_started"),
            created_at=data.get("created_at", datetime.now().isoformat()),
            updated_at=data.get("updated_at", datetime.now().isoformat()),
            error=data.get("error"),
        )
        
        self._simulations[simulation_id] = state
        return state
    
    def create_simulation(
        self,
        project_id: str,
        graph_id: str,
        enable_twitter: bool = True,
        enable_reddit: bool = True,
    ) -> SimulationState:
        """
        Criar nova simulacao
        
        Args:
            project_id: ID do projeto
            graph_id: ID do grafo Zep
            enable_twitter: Se habilita simulacao Twitter
            enable_reddit: Se habilita simulacao Reddit
            
        Returns:
            SimulationState
        """
        import uuid
        simulation_id = f"sim_{uuid.uuid4().hex[:12]}"
        
        state = SimulationState(
            simulation_id=simulation_id,
            project_id=project_id,
            graph_id=graph_id,
            enable_twitter=enable_twitter,
            enable_reddit=enable_reddit,
            status=SimulationStatus.CREATED,
        )
        
        self._save_simulation_state(state)
        logger.info(f"Criando simulacao: {simulation_id}, project={project_id}, graph={graph_id}")
        
        return state
    
    def prepare_simulation(
        self,
        simulation_id: str,
        simulation_requirement: str,
        document_text: str,
        defined_entity_types: Optional[List[str]] = None,
        use_llm_for_profiles: bool = True,
        progress_callback: Optional[callable] = None,
        parallel_profile_count: int = 3
    ) -> SimulationState:
        """
        Preparar ambiente de simulacao (totalmente automatizado)
        
        Etapas:
        1. Ler e filtrar entidades do grafo Zep
        2. Gerar OASIS Agent Profile para cada entidade (LLM opcional, com paralelismo)
        3. Usar LLM para gerar parametros de configuracao da simulacao (tempo, atividade, frequencia, etc.)
        4. Salvar arquivos de configuracao e Profile
        5. Copiar scripts predefinidos para o diretorio de simulacao
        
        Args:
            simulation_id: ID da simulacao
            simulation_requirement: Descricao dos requisitos da simulacao (para LLM gerar configuracao)
            document_text: Conteudo do documento original (para o LLM entender o contexto)
            defined_entity_types: Tipos de entidade predefinidos (opcional)
            use_llm_for_profiles: Se usa LLM para gerar perfis detalhados
            progress_callback: Funcao de callback de progresso (stage, progress, message)
            parallel_profile_count: Quantidade de perfis gerados em paralelo, padrao 3
            
        Returns:
            SimulationState
        """
        state = self._load_simulation_state(simulation_id)
        if not state:
            raise ValueError(f"Simulacao nao existe: {simulation_id}")
        
        try:
            state.status = SimulationStatus.PREPARING
            self._save_simulation_state(state)
            
            sim_dir = self._get_simulation_dir(simulation_id)
            
            # ========== Etapa 1: Ler e filtrar entidades ==========
            if progress_callback:
                progress_callback("reading", 0, "Conectando ao grafo Zep...")
            
            reader = ZepEntityReader()
            
            if progress_callback:
                progress_callback("reading", 30, "Lendo dados dos nos...")
            
            filtered = reader.filter_defined_entities(
                graph_id=state.graph_id,
                defined_entity_types=defined_entity_types,
                enrich_with_edges=True
            )
            
            state.entities_count = filtered.filtered_count
            state.entity_types = list(filtered.entity_types)
            
            if progress_callback:
                progress_callback(
                    "reading", 100, 
                    f"Concluido, total de {filtered.filtered_count}  entidades",
                    current=filtered.filtered_count,
                    total=filtered.filtered_count
                )
            
            if filtered.filtered_count == 0:
                state.status = SimulationStatus.FAILED
                state.error = "Nenhuma entidade encontrada, verifique se o grafo foi construido corretamente"
                self._save_simulation_state(state)
                return state
            
            # ========== Etapa 2: Gerar Agent Profile ==========
            total_entities = len(filtered.entities)
            
            if progress_callback:
                progress_callback(
                    "generating_profiles", 0, 
                    "Iniciando geracao...",
                    current=0,
                    total=total_entities
                )
            
            # Passa graph_id para habilitar busca Zep, obtendo contexto mais rico
            generator = OasisProfileGenerator(graph_id=state.graph_id)
            
            def profile_progress(current, total, msg):
                if progress_callback:
                    progress_callback(
                        "generating_profiles", 
                        int(current / total * 100), 
                        msg,
                        current=current,
                        total=total,
                        item_name=msg
                    )
            
            # Define caminho de salvamento em tempo real (prioriza formato Reddit JSON)
            realtime_output_path = None
            realtime_platform = "reddit"
            if state.enable_reddit:
                realtime_output_path = os.path.join(sim_dir, "reddit_profiles.json")
                realtime_platform = "reddit"
            elif state.enable_twitter:
                realtime_output_path = os.path.join(sim_dir, "twitter_profiles.csv")
                realtime_platform = "twitter"
            
            profiles = generator.generate_profiles_from_entities(
                entities=filtered.entities,
                use_llm=use_llm_for_profiles,
                progress_callback=profile_progress,
                graph_id=state.graph_id,  # Passa graph_id para busca Zep
                parallel_count=parallel_profile_count,  # Quantidade de geracao em paralelo
                realtime_output_path=realtime_output_path,  # Caminho de salvamento em tempo real
                output_platform=realtime_platform  # Formato de saida
            )
            
            state.profiles_count = len(profiles)
            
            # Salvar arquivos de Profile (Twitter usa CSV, Reddit usa JSON)
            # Reddit ja foi salvo em tempo real durante geracao, salvando novamente para garantir integridade
            if progress_callback:
                progress_callback(
                    "generating_profiles", 95, 
                    "Salvando arquivos de Profile...",
                    current=total_entities,
                    total=total_entities
                )
            
            if state.enable_reddit:
                generator.save_profiles(
                    profiles=profiles,
                    file_path=os.path.join(sim_dir, "reddit_profiles.json"),
                    platform="reddit"
                )
            
            if state.enable_twitter:
                # Twitter usa formato CSV! Requisito do OASIS
                generator.save_profiles(
                    profiles=profiles,
                    file_path=os.path.join(sim_dir, "twitter_profiles.csv"),
                    platform="twitter"
                )
            
            if progress_callback:
                progress_callback(
                    "generating_profiles", 100, 
                    f"Concluido, total de {len(profiles)} Profiles",
                    current=len(profiles),
                    total=len(profiles)
                )
            
            # ========== Etapa 3: LLM gera configuracao de simulacao ==========
            if progress_callback:
                progress_callback(
                    "generating_config", 0, 
                    "Analisando requisitos da simulacao...",
                    current=0,
                    total=3
                )
            
            config_generator = SimulationConfigGenerator()
            
            if progress_callback:
                progress_callback(
                    "generating_config", 30, 
                    "Chamando LLM para gerar configuracao...",
                    current=1,
                    total=3
                )
            
            sim_params = config_generator.generate_config(
                simulation_id=simulation_id,
                project_id=state.project_id,
                graph_id=state.graph_id,
                simulation_requirement=simulation_requirement,
                document_text=document_text,
                entities=filtered.entities,
                enable_twitter=state.enable_twitter,
                enable_reddit=state.enable_reddit
            )
            
            if progress_callback:
                progress_callback(
                    "generating_config", 70, 
                    "Salvando arquivo de configuracao...",
                    current=2,
                    total=3
                )
            
            # Salva arquivo de configuracao
            config_path = os.path.join(sim_dir, "simulation_config.json")
            with open(config_path, 'w', encoding='utf-8') as f:
                f.write(sim_params.to_json())
            
            state.config_generated = True
            state.config_reasoning = sim_params.generation_reasoning
            
            if progress_callback:
                progress_callback(
                    "generating_config", 100, 
                    "Geracao de configuracao concluida",
                    current=3,
                    total=3
                )
            
            # Nota: Scripts de execucao permanecem em backend/scripts/, nao sao copiados
            # Ao iniciar, simulation_runner executa scripts do diretorio scripts/
            
            # Atualiza estado
            state.status = SimulationStatus.READY
            self._save_simulation_state(state)
            
            logger.info(f"Preparacao da simulacao concluida: {simulation_id}, "
                       f"entities={state.entities_count}, profiles={state.profiles_count}")
            
            return state
            
        except Exception as e:
            logger.error(f"Falha na preparacao da simulacao: {simulation_id}, error={str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            state.status = SimulationStatus.FAILED
            state.error = str(e)
            self._save_simulation_state(state)
            raise
    
    def get_simulation(self, simulation_id: str) -> Optional[SimulationState]:
        """Obtem estado da simulacao"""
        return self._load_simulation_state(simulation_id)
    
    def list_simulations(self, project_id: Optional[str] = None) -> List[SimulationState]:
        """Listar todas as simulacoes"""
        simulations = []
        
        if os.path.exists(self.SIMULATION_DATA_DIR):
            for sim_id in os.listdir(self.SIMULATION_DATA_DIR):
                # Pula arquivos ocultos (.DS_Store) e nao-diretorios
                sim_path = os.path.join(self.SIMULATION_DATA_DIR, sim_id)
                if sim_id.startswith('.') or not os.path.isdir(sim_path):
                    continue
                
                state = self._load_simulation_state(sim_id)
                if state:
                    if project_id is None or state.project_id == project_id:
                        simulations.append(state)
        
        return simulations
    
    def get_profiles(self, simulation_id: str, platform: str = "reddit") -> List[Dict[str, Any]]:
        """Obter Agent Profile da simulacao"""
        state = self._load_simulation_state(simulation_id)
        if not state:
            raise ValueError(f"Simulacao nao existe: {simulation_id}")
        
        sim_dir = self._get_simulation_dir(simulation_id)
        profile_path = os.path.join(sim_dir, f"{platform}_profiles.json")
        
        if not os.path.exists(profile_path):
            return []
        
        with open(profile_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get_simulation_config(self, simulation_id: str) -> Optional[Dict[str, Any]]:
        """Obter configuracao da simulacao"""
        sim_dir = self._get_simulation_dir(simulation_id)
        config_path = os.path.join(sim_dir, "simulation_config.json")
        
        if not os.path.exists(config_path):
            return None
        
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get_run_instructions(self, simulation_id: str) -> Dict[str, str]:
        """Obter instrucoes de execucao"""
        sim_dir = self._get_simulation_dir(simulation_id)
        config_path = os.path.join(sim_dir, "simulation_config.json")
        scripts_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../scripts'))
        
        return {
            "simulation_dir": sim_dir,
            "scripts_dir": scripts_dir,
            "config_file": config_path,
            "commands": {
                "twitter": f"python {scripts_dir}/run_twitter_simulation.py --config {config_path}",
                "reddit": f"python {scripts_dir}/run_reddit_simulation.py --config {config_path}",
                "parallel": f"python {scripts_dir}/run_parallel_simulation.py --config {config_path}",
            },
            "instructions": (
                f"1. Ativar ambiente conda: conda activate MiroFish\n"
                f"2. Executar simulacao (scripts em {scripts_dir}):\n"
                f"   - Executar apenas Twitter: python {scripts_dir}/run_twitter_simulation.py --config {config_path}\n"
                f"   - Executar apenas Reddit: python {scripts_dir}/run_reddit_simulation.py --config {config_path}\n"
                f"   - Executar ambas plataformas em paralelo: python {scripts_dir}/run_parallel_simulation.py --config {config_path}"
            )
        }
