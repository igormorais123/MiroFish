"""
Executor de simulacao OASIS
Executa simulacao em segundo plano e registra acoes de cada Agent, com monitoramento em tempo real
"""

import os
import sys
import json
import time
import asyncio
import threading
import subprocess
import signal
import atexit
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from queue import Queue

from ..config import Config
from ..utils.logger import get_logger
from .zep_graph_memory_updater import ZepGraphMemoryManager
from .simulation_ipc import SimulationIPCClient, CommandType, IPCResponse

logger = get_logger('mirofish.simulation_runner')

# Flag indicando se a funcao de limpeza ja foi registrada
_cleanup_registered = False

# Deteccao de plataforma
IS_WINDOWS = sys.platform == 'win32'


class RunnerStatus(str, Enum):
    """Estado do executor"""
    IDLE = "idle"
    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class AgentAction:
    """Registro de acao do Agent"""
    round_num: int
    timestamp: str
    platform: str  # twitter / reddit
    agent_id: int
    agent_name: str
    action_type: str  # CREATE_POST, LIKE_POST, etc.
    action_args: Dict[str, Any] = field(default_factory=dict)
    result: Optional[str] = None
    success: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "round_num": self.round_num,
            "timestamp": self.timestamp,
            "platform": self.platform,
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "action_type": self.action_type,
            "action_args": self.action_args,
            "result": self.result,
            "success": self.success,
        }


@dataclass
class RoundSummary:
    """Resumo por rodada"""
    round_num: int
    start_time: str
    end_time: Optional[str] = None
    simulated_hour: int = 0
    twitter_actions: int = 0
    reddit_actions: int = 0
    active_agents: List[int] = field(default_factory=list)
    actions: List[AgentAction] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "round_num": self.round_num,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "simulated_hour": self.simulated_hour,
            "twitter_actions": self.twitter_actions,
            "reddit_actions": self.reddit_actions,
            "active_agents": self.active_agents,
            "actions_count": len(self.actions),
            "actions": [a.to_dict() for a in self.actions],
        }


@dataclass
class SimulationRunState:
    """Estado de execucao da simulacao (tempo real)"""
    simulation_id: str
    runner_status: RunnerStatus = RunnerStatus.IDLE
    
    # Informacoes de progresso
    current_round: int = 0
    total_rounds: int = 0
    simulated_hours: int = 0
    total_simulation_hours: int = 0
    
    # Rodadas e tempo independentes por plataforma (para exibicao paralela)
    twitter_current_round: int = 0
    reddit_current_round: int = 0
    twitter_simulated_hours: int = 0
    reddit_simulated_hours: int = 0
    
    # Estado da plataforma
    twitter_running: bool = False
    reddit_running: bool = False
    twitter_actions_count: int = 0
    reddit_actions_count: int = 0
    
    # Estado de conclusao por plataforma (detectado via evento simulation_end no actions.jsonl)
    twitter_completed: bool = False
    reddit_completed: bool = False
    
    # Resumo por rodada
    rounds: List[RoundSummary] = field(default_factory=list)
    
    # Acoes recentes (para exibicao em tempo real no frontend)
    recent_actions: List[AgentAction] = field(default_factory=list)
    max_recent_actions: int = 50
    
    # Timestamp
    started_at: Optional[str] = None
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None
    
    # Informacoes de erro
    error: Optional[str] = None
    
    # PID do processo (para parar)
    process_pid: Optional[int] = None
    
    def add_action(self, action: AgentAction):
        """Adiciona acao a lista de acoes recentes"""
        self.recent_actions.insert(0, action)
        if len(self.recent_actions) > self.max_recent_actions:
            self.recent_actions = self.recent_actions[:self.max_recent_actions]
        
        if action.platform == "twitter":
            self.twitter_actions_count += 1
        else:
            self.reddit_actions_count += 1
        
        self.updated_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "simulation_id": self.simulation_id,
            "runner_status": self.runner_status.value,
            "current_round": self.current_round,
            "total_rounds": self.total_rounds,
            "simulated_hours": self.simulated_hours,
            "total_simulation_hours": self.total_simulation_hours,
            "progress_percent": round(self.current_round / max(self.total_rounds, 1) * 100, 1),
            # Rodadas e tempo independentes por plataforma
            "twitter_current_round": self.twitter_current_round,
            "reddit_current_round": self.reddit_current_round,
            "twitter_simulated_hours": self.twitter_simulated_hours,
            "reddit_simulated_hours": self.reddit_simulated_hours,
            "twitter_running": self.twitter_running,
            "reddit_running": self.reddit_running,
            "twitter_completed": self.twitter_completed,
            "reddit_completed": self.reddit_completed,
            "twitter_actions_count": self.twitter_actions_count,
            "reddit_actions_count": self.reddit_actions_count,
            "total_actions_count": self.twitter_actions_count + self.reddit_actions_count,
            "started_at": self.started_at,
            "updated_at": self.updated_at,
            "completed_at": self.completed_at,
            "error": self.error,
            "process_pid": self.process_pid,
        }
    
    def to_detail_dict(self) -> Dict[str, Any]:
        """Informacoes detalhadas incluindo acoes recentes"""
        result = self.to_dict()
        result["recent_actions"] = [a.to_dict() for a in self.recent_actions]
        result["rounds_count"] = len(self.rounds)
        return result


class SimulationRunner:
    """
    Executor de simulacao
    
    Responsabilidades:
    1. Executar simulacao OASIS em processo em segundo plano
    2. Analisar logs, registrar acoes de cada Agent
    3. Fornecer interface de consulta de estado em tempo real
    4. Suportar operacoes de pausar/parar/retomar
    """
    
    # Diretorio de armazenamento de estado
    RUN_STATE_DIR = os.path.join(
        os.path.dirname(__file__),
        '../../uploads/simulations'
    )
    
    # Diretorio de scripts
    SCRIPTS_DIR = os.path.join(
        os.path.dirname(__file__),
        '../../scripts'
    )
    
    # Estado de execucao em memoria
    _run_states: Dict[str, SimulationRunState] = {}
    _processes: Dict[str, subprocess.Popen] = {}
    _action_queues: Dict[str, Queue] = {}
    _monitor_threads: Dict[str, threading.Thread] = {}
    _stdout_files: Dict[str, Any] = {}  # Armazena handles de arquivo stdout
    _stderr_files: Dict[str, Any] = {}  # Armazena handles de arquivo stderr
    
    # Configuracao de atualizacao de memoria do grafo
    _graph_memory_enabled: Dict[str, bool] = {}  # simulation_id -> enabled
    
    @classmethod
    def get_run_state(cls, simulation_id: str) -> Optional[SimulationRunState]:
        """Obter estado de execucao"""
        if simulation_id in cls._run_states:
            return cls._reconcile_run_state_from_artifacts(cls._run_states[simulation_id])
        
        # Tenta carregar do arquivo
        state = cls._load_run_state(simulation_id)
        if not state:
            state = cls._build_run_state_from_artifacts(simulation_id)
        if state:
            state = cls._reconcile_run_state_from_artifacts(state)
            cls._run_states[simulation_id] = state
        return state

    @classmethod
    def _infer_timing_from_config(cls, simulation_id: str) -> dict[str, int]:
        sim_dir = os.path.join(cls.RUN_STATE_DIR, simulation_id)
        config_path = os.path.join(sim_dir, "simulation_config.json")
        total_hours = 0
        total_rounds = 0
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            time_config = config.get("time_config", {}) if isinstance(config, dict) else {}
            total_hours = int(time_config.get("total_simulation_hours") or 0)
            minutes_per_round = int(time_config.get("minutes_per_round") or 0)
            if total_hours > 0 and minutes_per_round > 0:
                total_rounds = int(total_hours * 60 / minutes_per_round)
        except Exception:
            pass
        return {"total_hours": total_hours, "total_rounds": total_rounds}

    @classmethod
    def _build_run_state_from_artifacts(cls, simulation_id: str) -> Optional[SimulationRunState]:
        """Reconstroi um estado minimo quando run_state.json foi perdido."""
        sim_dir = os.path.join(cls.RUN_STATE_DIR, simulation_id)
        if not os.path.isdir(sim_dir):
            return None

        has_actions = any(
            os.path.exists(os.path.join(sim_dir, platform, "actions.jsonl"))
            for platform in ("twitter", "reddit")
        )
        if not has_actions:
            return None

        timing = cls._infer_timing_from_config(simulation_id)
        return SimulationRunState(
            simulation_id=simulation_id,
            runner_status=RunnerStatus.STOPPED,
            total_rounds=timing["total_rounds"],
            total_simulation_hours=timing["total_hours"],
            updated_at=datetime.now().isoformat(),
        )

    @staticmethod
    def _safe_int(value: Any, default: int = 0) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    @classmethod
    def _scan_action_log_summary(cls, log_path: str) -> dict[str, Any]:
        """Extrai resumo auditavel de um actions.jsonl sem materializar todas as acoes."""
        summary = {
            "exists": os.path.exists(log_path),
            "completed": False,
            "max_round": 0,
            "simulated_hours": 0,
            "actions_count": 0,
            "event_total_actions": 0,
            "event_total_rounds": 0,
        }
        if not summary["exists"]:
            return summary

        try:
            with open(log_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        row = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    if "event_type" in row:
                        event_type = row.get("event_type")
                        if event_type == "simulation_end":
                            summary["completed"] = True
                            summary["event_total_actions"] = max(
                                summary["event_total_actions"],
                                cls._safe_int(row.get("total_actions")),
                            )
                            summary["event_total_rounds"] = max(
                                summary["event_total_rounds"],
                                cls._safe_int(row.get("total_rounds")),
                            )
                        elif event_type == "round_end":
                            round_num = cls._safe_int(row.get("round"))
                            summary["max_round"] = max(summary["max_round"], round_num)
                            summary["simulated_hours"] = max(
                                summary["simulated_hours"],
                                cls._safe_int(row.get("simulated_hours")),
                            )
                        continue

                    if "agent_id" not in row:
                        continue

                    summary["actions_count"] += 1
                    summary["max_round"] = max(summary["max_round"], cls._safe_int(row.get("round")))
        except OSError as exc:
            logger.warning(f"Falha ao resumir log de acoes: {log_path}, error={exc}")

        if summary["event_total_rounds"]:
            summary["max_round"] = max(summary["max_round"], summary["event_total_rounds"])
        if summary["event_total_actions"] and summary["actions_count"] == 0:
            summary["actions_count"] = summary["event_total_actions"]
        return summary

    @classmethod
    def _reconcile_run_state_from_artifacts(
        cls,
        state: SimulationRunState,
        *,
        include_active: bool = False,
    ) -> SimulationRunState:
        """
        Reconcilia run_state.json com os logs auditaveis.

        Isso torna a leitura idempotente: se o processo morreu, o backend reiniciou
        ou uma rota antiga gravou "stopped", os eventos simulation_end continuam
        sendo a fonte de verdade para liberar relatorio.
        """
        if (
            not include_active
            and state.runner_status
            in {RunnerStatus.STARTING, RunnerStatus.RUNNING, RunnerStatus.PAUSED, RunnerStatus.STOPPING}
        ):
            return state

        sim_dir = os.path.join(cls.RUN_STATE_DIR, state.simulation_id)
        twitter = cls._scan_action_log_summary(os.path.join(sim_dir, "twitter", "actions.jsonl"))
        reddit = cls._scan_action_log_summary(os.path.join(sim_dir, "reddit", "actions.jsonl"))

        changed = False

        if twitter["exists"]:
            if state.twitter_current_round != max(state.twitter_current_round, twitter["max_round"]):
                state.twitter_current_round = max(state.twitter_current_round, twitter["max_round"])
                changed = True
            if state.twitter_simulated_hours != max(state.twitter_simulated_hours, twitter["simulated_hours"]):
                state.twitter_simulated_hours = max(state.twitter_simulated_hours, twitter["simulated_hours"])
                changed = True
            if state.twitter_actions_count != max(state.twitter_actions_count, twitter["actions_count"]):
                state.twitter_actions_count = max(state.twitter_actions_count, twitter["actions_count"])
                changed = True
            if twitter["completed"] and not state.twitter_completed:
                state.twitter_completed = True
                changed = True

        if reddit["exists"]:
            if state.reddit_current_round != max(state.reddit_current_round, reddit["max_round"]):
                state.reddit_current_round = max(state.reddit_current_round, reddit["max_round"])
                changed = True
            if state.reddit_simulated_hours != max(state.reddit_simulated_hours, reddit["simulated_hours"]):
                state.reddit_simulated_hours = max(state.reddit_simulated_hours, reddit["simulated_hours"])
                changed = True
            if state.reddit_actions_count != max(state.reddit_actions_count, reddit["actions_count"]):
                state.reddit_actions_count = max(state.reddit_actions_count, reddit["actions_count"])
                changed = True
            if reddit["completed"] and not state.reddit_completed:
                state.reddit_completed = True
                changed = True

        reconciled_round = max(state.current_round, state.twitter_current_round, state.reddit_current_round)
        if state.current_round != reconciled_round:
            state.current_round = reconciled_round
            changed = True

        reconciled_hours = max(state.simulated_hours, state.twitter_simulated_hours, state.reddit_simulated_hours)
        if state.simulated_hours != reconciled_hours:
            state.simulated_hours = reconciled_hours
            changed = True

        all_completed = cls._check_all_platforms_completed(state)
        if all_completed and state.runner_status != RunnerStatus.COMPLETED:
            state.runner_status = RunnerStatus.COMPLETED
            state.twitter_running = False
            state.reddit_running = False
            state.error = None
            if not state.completed_at:
                state.completed_at = datetime.now().isoformat()
            if state.total_rounds:
                state.current_round = max(state.current_round, state.total_rounds)
                if twitter["exists"]:
                    state.twitter_current_round = max(state.twitter_current_round, state.total_rounds)
                if reddit["exists"]:
                    state.reddit_current_round = max(state.reddit_current_round, state.total_rounds)
            changed = True

        if changed:
            state.updated_at = datetime.now().isoformat()
            try:
                cls._save_run_state(state)
            except Exception as exc:
                logger.warning(
                    f"Falha ao persistir reconciliacao da simulacao {state.simulation_id}: {exc}"
                )

        return state
    
    @classmethod
    def _load_run_state(cls, simulation_id: str) -> Optional[SimulationRunState]:
        """Carrega estado de execucao do arquivo"""
        state_file = os.path.join(cls.RUN_STATE_DIR, simulation_id, "run_state.json")
        if not os.path.exists(state_file):
            return None
        
        try:
            with open(state_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            state = SimulationRunState(
                simulation_id=simulation_id,
                runner_status=RunnerStatus(data.get("runner_status", "idle")),
                current_round=data.get("current_round", 0),
                total_rounds=data.get("total_rounds", 0),
                simulated_hours=data.get("simulated_hours", 0),
                total_simulation_hours=data.get("total_simulation_hours", 0),
                # Rodadas e tempo independentes por plataforma
                twitter_current_round=data.get("twitter_current_round", 0),
                reddit_current_round=data.get("reddit_current_round", 0),
                twitter_simulated_hours=data.get("twitter_simulated_hours", 0),
                reddit_simulated_hours=data.get("reddit_simulated_hours", 0),
                twitter_running=data.get("twitter_running", False),
                reddit_running=data.get("reddit_running", False),
                twitter_completed=data.get("twitter_completed", False),
                reddit_completed=data.get("reddit_completed", False),
                twitter_actions_count=data.get("twitter_actions_count", 0),
                reddit_actions_count=data.get("reddit_actions_count", 0),
                started_at=data.get("started_at"),
                updated_at=data.get("updated_at", datetime.now().isoformat()),
                completed_at=data.get("completed_at"),
                error=data.get("error"),
                process_pid=data.get("process_pid"),
            )
            
            # Carrega acoes recentes
            actions_data = data.get("recent_actions", [])
            for a in actions_data:
                state.recent_actions.append(AgentAction(
                    round_num=a.get("round_num", 0),
                    timestamp=a.get("timestamp", ""),
                    platform=a.get("platform", ""),
                    agent_id=a.get("agent_id", 0),
                    agent_name=a.get("agent_name", ""),
                    action_type=a.get("action_type", ""),
                    action_args=a.get("action_args", {}),
                    result=a.get("result"),
                    success=a.get("success", True),
                ))
            
            return state
        except Exception as e:
            logger.error(f"Falha ao carregar estado de execucao: {str(e)}")
            return None
    
    @classmethod
    def _save_run_state(cls, state: SimulationRunState):
        """Salva estado de execucao em arquivo"""
        sim_dir = os.path.join(cls.RUN_STATE_DIR, state.simulation_id)
        os.makedirs(sim_dir, exist_ok=True)
        state_file = os.path.join(sim_dir, "run_state.json")
        
        data = state.to_detail_dict()
        
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        cls._run_states[state.simulation_id] = state
        cls._sync_simulation_manager_state(state)

    @classmethod
    def _sync_simulation_manager_state(cls, state: SimulationRunState):
        """Mantem state.json coerente com run_state.json para APIs e relatorios."""
        if state.runner_status == RunnerStatus.IDLE:
            return
        try:
            from .simulation_manager import SimulationManager

            SimulationManager().apply_runner_status(state.simulation_id, state)
        except Exception as exc:
            logger.warning(
                f"Falha ao sincronizar estado mestre da simulacao {state.simulation_id}: {exc}"
            )
    
    @classmethod
    def start_simulation(
        cls,
        simulation_id: str,
        platform: str = "parallel",  # twitter / reddit / parallel
        max_rounds: int = None,  # Maximo de rodadas (opcional, para truncar simulacoes longas)
        enable_graph_memory_update: bool = False,  # se deve atualizar atividades no grafo Zep
        graph_id: str = None  # ID do grafo Zep (obrigatorio quando habilitado)
    ) -> SimulationRunState:
        """
        Iniciar simulacao
        
        Args:
            simulation_id: ID da simulacao
            platform: plataforma de execucao (twitter/reddit/parallel)
            max_rounds: Maximo de rodadas (opcional, para truncar simulacoes longas)
            enable_graph_memory_update: Se deve atualizar atividades no grafo Zep
            graph_id: ID do grafo Zep (obrigatorio quando habilitado)
            
        Returns:
            SimulationRunState
        """
        # Verifica se ja esta em execucao
        existing = cls.get_run_state(simulation_id)
        if existing and existing.runner_status in [RunnerStatus.RUNNING, RunnerStatus.STARTING]:
            raise ValueError(f"Simulacao ja em execucao: {simulation_id}")
        
        # Carrega configuracao da simulacao
        sim_dir = os.path.join(cls.RUN_STATE_DIR, simulation_id)
        config_path = os.path.join(sim_dir, "simulation_config.json")
        
        if not os.path.exists(config_path):
            raise ValueError(f"Configuracao nao existe, execute /prepare primeiro")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Inicializa estado de execucao
        time_config = config.get("time_config", {})
        total_hours = time_config.get("total_simulation_hours", 72)
        minutes_per_round = time_config.get("minutes_per_round", 30)
        total_rounds = int(total_hours * 60 / minutes_per_round)
        
        # Se maximo de rodadas especificado, trunca
        if max_rounds is not None and max_rounds > 0:
            original_rounds = total_rounds
            total_rounds = min(total_rounds, max_rounds)
            if total_rounds < original_rounds:
                logger.info(f"Rodadas truncadas: {original_rounds} -> {total_rounds} (max_rounds={max_rounds})")
        
        state = SimulationRunState(
            simulation_id=simulation_id,
            runner_status=RunnerStatus.STARTING,
            total_rounds=total_rounds,
            total_simulation_hours=total_hours,
            started_at=datetime.now().isoformat(),
        )
        
        cls._save_run_state(state)
        
        # Se atualizacao de memoria habilitada, cria atualizador
        if enable_graph_memory_update:
            if not graph_id:
                raise ValueError("graph_id e obrigatorio quando atualizacao de memoria esta habilitada")
            
            try:
                ZepGraphMemoryManager.create_updater(simulation_id, graph_id)
                cls._graph_memory_enabled[simulation_id] = True
                logger.info(f"Atualizacao de memoria do grafo habilitada: simulation_id={simulation_id}, graph_id={graph_id}")
            except Exception as e:
                logger.error(f"Falha ao criar atualizador de memoria: {e}")
                cls._graph_memory_enabled[simulation_id] = False
        else:
            cls._graph_memory_enabled[simulation_id] = False
        
        # Determina qual script executar (scripts em backend/scripts/)
        if platform == "twitter":
            script_name = "run_twitter_simulation.py"
            state.twitter_running = True
        elif platform == "reddit":
            script_name = "run_reddit_simulation.py"
            state.reddit_running = True
        else:
            script_name = "run_parallel_simulation.py"
            state.twitter_running = True
            state.reddit_running = True
        
        script_path = os.path.join(cls.SCRIPTS_DIR, script_name)
        
        if not os.path.exists(script_path):
            raise ValueError(f"Script nao existe: {script_path}")
        
        # Cria fila de acoes
        action_queue = Queue()
        cls._action_queues[simulation_id] = action_queue
        
        # Inicia processo de simulacao
        try:
            # Constroi comando de execucao com caminhos completos
            # Nova estrutura de logs:
            #   twitter/actions.jsonl - Log de acoes do Twitter
            #   reddit/actions.jsonl  - Log de acoes do Reddit
            #   simulation.log        - Log do processo principal
            
            cmd = [
                sys.executable,  # Interpretador Python
                script_path,
                "--config", config_path,  # Usa caminho completo do arquivo de configuracao
            ]
            
            # Se maximo de rodadas especificado, adiciona ao parametro da linha de comando
            if max_rounds is not None and max_rounds > 0:
                cmd.extend(["--max-rounds", str(max_rounds)])
            
            # Garante permissao de escrita em .db existentes (fix "readonly database" em restart)
            # 2026-04-18, Phase 2 Task 6 (ver DIAGNOSTICO_TRAVAMENTO.md #6)
            try:
                for _db_name in os.listdir(sim_dir):
                    if _db_name.endswith('.db') or _db_name.endswith('.sqlite'):
                        _db_path = os.path.join(sim_dir, _db_name)
                        try:
                            os.chmod(_db_path, 0o666)
                        except OSError:
                            pass
            except OSError:
                pass

            # Cria arquivo de log principal, evitando bloqueio por buffer cheio de stdout/stderr
            main_log_path = os.path.join(sim_dir, "simulation.log")
            main_log_file = open(main_log_path, 'w', encoding='utf-8')
            
            # Define variaveis de ambiente do subprocesso para usar UTF-8 no Windows
            # Corrige problema de bibliotecas (como OASIS) que nao especificam encoding ao ler arquivos
            env = os.environ.copy()
            env['PYTHONUTF8'] = '1'  # Python 3.7+ suporte, todos os open() usam UTF-8 por padrao
            env['PYTHONIOENCODING'] = 'utf-8'  # Garante que stdout/stderr use UTF-8
            
            # Define diretorio de trabalho como diretorio da simulacao (banco de dados sera gerado aqui)
            # Usa start_new_session=True para criar novo grupo de processos, garantindo terminacao via os.killpg
            process = subprocess.Popen(
                cmd,
                cwd=sim_dir,
                stdout=main_log_file,
                stderr=subprocess.STDOUT,  # stderr tambem escreve no mesmo arquivo
                text=True,
                encoding='utf-8',  # Especifica encoding explicitamente
                bufsize=1,
                env=env,  # Passa variaveis de ambiente com configuracao UTF-8
                start_new_session=True,  # Cria novo grupo de processos para terminacao ao fechar servidor
            )
            
            # Salva handles de arquivo para fechar posteriormente
            cls._stdout_files[simulation_id] = main_log_file
            cls._stderr_files[simulation_id] = None  # Nao precisa mais de stderr separado
            
            state.process_pid = process.pid
            state.runner_status = RunnerStatus.RUNNING
            cls._processes[simulation_id] = process
            cls._save_run_state(state)
            
            # Inicia thread de monitoramento
            monitor_thread = threading.Thread(
                target=cls._monitor_simulation,
                args=(simulation_id,),
                daemon=True
            )
            monitor_thread.start()
            cls._monitor_threads[simulation_id] = monitor_thread
            
            logger.info(f"Simulacao iniciada com sucesso: {simulation_id}, pid={process.pid}, platform={platform}")
            
        except Exception as e:
            state.runner_status = RunnerStatus.FAILED
            state.error = str(e)
            cls._save_run_state(state)
            raise
        
        return state
    
    @classmethod
    def _monitor_simulation(cls, simulation_id: str):
        """Monitora processo de simulacao, analisa log de acoes"""
        sim_dir = os.path.join(cls.RUN_STATE_DIR, simulation_id)
        
        # Nova estrutura de logs: log de acoes por plataforma
        twitter_actions_log = os.path.join(sim_dir, "twitter", "actions.jsonl")
        reddit_actions_log = os.path.join(sim_dir, "reddit", "actions.jsonl")
        
        process = cls._processes.get(simulation_id)
        state = cls.get_run_state(simulation_id)
        
        if not process or not state:
            return
        
        twitter_position = 0
        reddit_position = 0
        
        try:
            while process.poll() is None:  # Processo ainda em execucao
                # Le log de acoes do Twitter
                if os.path.exists(twitter_actions_log):
                    twitter_position = cls._read_action_log(
                        twitter_actions_log, twitter_position, state, "twitter"
                    )
                
                # Le log de acoes do Reddit
                if os.path.exists(reddit_actions_log):
                    reddit_position = cls._read_action_log(
                        reddit_actions_log, reddit_position, state, "reddit"
                    )
                
                # Atualiza estado
                cls._save_run_state(state)
                time.sleep(2)
            
            # Apos encerramento do processo, le logs uma ultima vez
            if os.path.exists(twitter_actions_log):
                cls._read_action_log(twitter_actions_log, twitter_position, state, "twitter")
            if os.path.exists(reddit_actions_log):
                cls._read_action_log(reddit_actions_log, reddit_position, state, "reddit")
            
            # Processo encerrado
            exit_code = process.returncode
            
            if exit_code == 0:
                state.runner_status = RunnerStatus.COMPLETED
                state.completed_at = datetime.now().isoformat()
                logger.info(f"Simulacao concluida: {simulation_id}")
                # Dispara geracao automatica de relatorio em background
                cls._auto_generate_report(simulation_id)
            else:
                state.runner_status = RunnerStatus.FAILED
                # Le informacoes de erro do arquivo de log principal
                main_log_path = os.path.join(sim_dir, "simulation.log")
                error_info = ""
                try:
                    if os.path.exists(main_log_path):
                        with open(main_log_path, 'r', encoding='utf-8') as f:
                            error_info = f.read()[-2000:]  # pega ultimos 2000 caracteres
                except Exception:
                    pass
                state.error = f"Codigo de saida do processo: {exit_code}, erro: {error_info}"
                logger.error(f"Simulacao falhou: {simulation_id}, error={state.error}")
            
            state.twitter_running = False
            state.reddit_running = False
            cls._save_run_state(state)
            
        except Exception as e:
            logger.error(f"Excecao na thread de monitoramento: {simulation_id}, error={str(e)}")
            state.runner_status = RunnerStatus.FAILED
            state.error = str(e)
            cls._save_run_state(state)
        
        finally:
            # Para atualizador de memoria do grafo
            if cls._graph_memory_enabled.get(simulation_id, False):
                try:
                    ZepGraphMemoryManager.stop_updater(simulation_id)
                    logger.info(f"Atualizacao de memoria do grafo parada: simulation_id={simulation_id}")
                except Exception as e:
                    logger.error(f"Para atualizador de memoria do grafofalhou: {e}")
                cls._graph_memory_enabled.pop(simulation_id, None)
            
            # Limpa recursos do processo
            cls._processes.pop(simulation_id, None)
            cls._action_queues.pop(simulation_id, None)
            
            # Fecha handles de arquivo de log
            if simulation_id in cls._stdout_files:
                try:
                    cls._stdout_files[simulation_id].close()
                except Exception:
                    pass
                cls._stdout_files.pop(simulation_id, None)
            if simulation_id in cls._stderr_files and cls._stderr_files[simulation_id]:
                try:
                    cls._stderr_files[simulation_id].close()
                except Exception:
                    pass
                cls._stderr_files.pop(simulation_id, None)
    
    @classmethod
    def _read_action_log(
        cls, 
        log_path: str, 
        position: int, 
        state: SimulationRunState,
        platform: str
    ) -> int:
        """
        Le arquivo de log de acoes
        
        Args:
            log_path: Caminho do arquivo de log
            position: Posicao da ultima leitura
            state: Objeto de estado de execucao
            platform: nome da plataforma (twitter/reddit)
            
        Returns:
            Nova posicao de leitura
        """
        # Verifica se atualizacao de memoria esta habilitada
        graph_memory_enabled = cls._graph_memory_enabled.get(state.simulation_id, False)
        graph_updater = None
        if graph_memory_enabled:
            graph_updater = ZepGraphMemoryManager.get_updater(state.simulation_id)
        
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                f.seek(position)
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            action_data = json.loads(line)
                            
                            # Processa entradas de tipo evento
                            if "event_type" in action_data:
                                event_type = action_data.get("event_type")
                                
                                # Detecta evento simulation_end, marca plataforma como concluida
                                if event_type == "simulation_end":
                                    if platform == "twitter":
                                        state.twitter_completed = True
                                        state.twitter_running = False
                                        logger.info(f"Simulacao Twitter concluida: {state.simulation_id}, total_rounds={action_data.get('total_rounds')}, total_actions={action_data.get('total_actions')}")
                                    elif platform == "reddit":
                                        state.reddit_completed = True
                                        state.reddit_running = False
                                        logger.info(f"Simulacao Reddit concluida: {state.simulation_id}, total_rounds={action_data.get('total_rounds')}, total_actions={action_data.get('total_actions')}")
                                    
                                    # Verifica se todas as plataformas habilitadas ja concluiram
                                    # Se apenas uma plataforma executada, verifica apenas ela
                                    # Se duas plataformas executadas, ambas precisam concluir
                                    all_completed = cls._check_all_platforms_completed(state)
                                    if all_completed:
                                        state.runner_status = RunnerStatus.COMPLETED
                                        state.completed_at = datetime.now().isoformat()
                                        logger.info(f"Simulacao de todas as plataformas concluida: {state.simulation_id}")
                                        # Dispara geracao automatica de relatorio em background
                                        cls._auto_generate_report(state.simulation_id)
                                
                                # Atualiza informacoes de rodada (do evento round_end)
                                elif event_type == "round_end":
                                    round_num = action_data.get("round", 0)
                                    simulated_hours = action_data.get("simulated_hours", 0)
                                    
                                    # Atualiza rodadas e tempo independentes por plataforma
                                    if platform == "twitter":
                                        if round_num > state.twitter_current_round:
                                            state.twitter_current_round = round_num
                                        state.twitter_simulated_hours = simulated_hours
                                    elif platform == "reddit":
                                        if round_num > state.reddit_current_round:
                                            state.reddit_current_round = round_num
                                        state.reddit_simulated_hours = simulated_hours
                                    
                                    # Rodada total e o maximo das duas plataformas
                                    if round_num > state.current_round:
                                        state.current_round = round_num
                                    # Tempo total e o maximo das duas plataformas
                                    state.simulated_hours = max(state.twitter_simulated_hours, state.reddit_simulated_hours)
                                
                                continue
                            
                            action = AgentAction(
                                round_num=action_data.get("round", 0),
                                timestamp=action_data.get("timestamp", datetime.now().isoformat()),
                                platform=platform,
                                agent_id=action_data.get("agent_id", 0),
                                agent_name=action_data.get("agent_name", ""),
                                action_type=action_data.get("action_type", ""),
                                action_args=action_data.get("action_args", {}),
                                result=action_data.get("result"),
                                success=action_data.get("success", True),
                            )
                            state.add_action(action)
                            
                            # Atualiza rodada
                            if action.round_num and action.round_num > state.current_round:
                                state.current_round = action.round_num
                            
                            # Se memoria habilitada, envia atividade para Zep
                            if graph_updater:
                                graph_updater.add_activity_from_dict(action_data, platform)
                            
                        except json.JSONDecodeError:
                            pass
                return f.tell()
        except Exception as e:
            logger.warning(f"Falha ao ler log de acoes: {log_path}, error={e}")
            return position
    
    @classmethod
    def _check_all_platforms_completed(cls, state: SimulationRunState) -> bool:
        """
        Verifica se todas as plataformas habilitadas concluiram
        
        Determina habilitacao da plataforma pela existencia do actions.jsonl
        
        Returns:
            True se todas as plataformas habilitadas concluiram
        """
        sim_dir = os.path.join(cls.RUN_STATE_DIR, state.simulation_id)
        twitter_log = os.path.join(sim_dir, "twitter", "actions.jsonl")
        reddit_log = os.path.join(sim_dir, "reddit", "actions.jsonl")
        
        # Verifica plataformas habilitadas (pela existencia dos arquivos)
        twitter_enabled = os.path.exists(twitter_log)
        reddit_enabled = os.path.exists(reddit_log)
        
        # Se plataforma habilitada mas nao concluida, retorna False
        if twitter_enabled and not state.twitter_completed:
            return False
        if reddit_enabled and not state.reddit_completed:
            return False
        
        # Pelo menos uma plataforma habilitada e concluida
        return twitter_enabled or reddit_enabled

    @classmethod
    def _auto_generate_report(cls, simulation_id: str):
        """
        Gera relatorio automaticamente ao fim da simulacao em background thread.
        Nao bloqueia o fluxo principal. Erros sao registrados no log.
        """
        def _run():
            try:
                from .report_agent import ReportAgent, ReportManager, ReportStatus
                from ..services.simulation_manager import SimulationManager
                from ..models.project import ProjectManager
                from ..models.task import TaskManager, TaskStatus
                import uuid

                logger.info(f"Geracao automatica de relatorio iniciada: {simulation_id}")

                # Verificar se ja existe relatorio concluido
                existing = ReportManager.get_report_by_simulation(simulation_id)
                if existing and existing.status == ReportStatus.COMPLETED:
                    logger.info(f"Relatorio ja existe para {simulation_id}, pulando geracao automatica")
                    return

                # Obter dados da simulacao e do projeto
                manager = SimulationManager()
                state = manager.get_simulation(simulation_id)
                if not state:
                    logger.warning(f"Simulacao nao encontrada para geracao automatica de relatorio: {simulation_id}")
                    return

                project = ProjectManager.get_project(state.project_id)
                if not project:
                    logger.warning(f"Projeto nao encontrado: {state.project_id}")
                    return

                graph_id = state.graph_id or project.graph_id
                if not graph_id:
                    logger.warning(f"graph_id ausente para geracao automatica de relatorio: {simulation_id}")
                    return

                simulation_requirement = project.simulation_requirement
                if not simulation_requirement:
                    logger.warning(f"simulation_requirement ausente para geracao automatica: {simulation_id}")
                    return

                report_id = f"report_{uuid.uuid4().hex[:12]}"

                # Criar tarefa assincrona
                task_manager = TaskManager()
                task_id = task_manager.create_task(
                    task_type="report_generate",
                    metadata={
                        "simulation_id": simulation_id,
                        "graph_id": graph_id,
                        "report_id": report_id,
                        "auto_generated": True
                    }
                )

                task_manager.update_task(
                    task_id,
                    status=TaskStatus.PROCESSING,
                    progress=0,
                    message="Geracao automatica: inicializando agente de relatorio..."
                )

                agent = ReportAgent(
                    graph_id=graph_id,
                    simulation_id=simulation_id,
                    simulation_requirement=simulation_requirement
                )

                def progress_callback(stage, progress, message):
                    task_manager.update_task(
                        task_id,
                        progress=progress,
                        message=f"[{stage}] {message}"
                    )

                # Texto-base para QC overlap (Phase 3) — best-effort
                source_text = None
                try:
                    source_text = ProjectManager.get_extracted_text(state.project_id)
                except Exception:
                    pass

                report = agent.generate_report(
                    progress_callback=progress_callback,
                    report_id=report_id,
                    source_text=source_text,
                )

                ReportManager.save_report(report)

                if report.status == ReportStatus.COMPLETED:
                    task_manager.complete_task(
                        task_id,
                        result={
                            "report_id": report.report_id,
                            "simulation_id": simulation_id,
                            "status": "completed",
                            "auto_generated": True
                        }
                    )
                    logger.info(f"Relatorio gerado automaticamente com sucesso: {report_id} para simulacao {simulation_id}")
                else:
                    task_manager.fail_task(task_id, report.error or "Falha na geracao automatica do relatorio")
                    logger.warning(f"Falha na geracao automatica do relatorio: {simulation_id}")

            except Exception as e:
                logger.error(f"Falha na geracao automatica do relatorio para {simulation_id}: {e}")

        thread = threading.Thread(target=_run, daemon=True, name=f"auto-report-{simulation_id}")
        thread.start()
        logger.info(f"Thread de geracao automatica de relatorio iniciada para: {simulation_id}")

    @classmethod
    def _terminate_process(cls, process: subprocess.Popen, simulation_id: str, timeout: int = 10):
        """
        Termina processo e subprocessos (cross-platform)
        
        Args:
            process: Processo a terminar
            simulation_id: ID da simulacao (para log)
            timeout: Tempo limite para encerramento do processo (segundos)
        """
        if IS_WINDOWS:
            # Windows: usa comando taskkill para terminar arvore de processos
            # /F = forca terminacao, /T = termina arvore de processos (incluindo subprocessos)
            logger.info(f"Terminando arvore de processos (Windows): simulation={simulation_id}, pid={process.pid}")
            try:
                # Tenta encerramento elegante primeiro
                subprocess.run(
                    ['taskkill', '/PID', str(process.pid), '/T'],
                    capture_output=True,
                    timeout=5
                )
                try:
                    process.wait(timeout=timeout)
                except subprocess.TimeoutExpired:
                    # Forcando terminacao
                    logger.warning(f"Processo nao respondeu, forcando terminacao: {simulation_id}")
                    subprocess.run(
                        ['taskkill', '/F', '/PID', str(process.pid), '/T'],
                        capture_output=True,
                        timeout=5
                    )
                    process.wait(timeout=5)
            except Exception as e:
                logger.warning(f"taskkill falhou, tentando terminate: {e}")
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
        else:
            # Unix: usa grupo de processos para terminar
            # Como start_new_session=True, PGID e igual ao PID do processo principal
            pgid = os.getpgid(process.pid)
            logger.info(f"Terminando grupo de processos (Unix): simulation={simulation_id}, pgid={pgid}")
            
            # Envia SIGTERM para todo o grupo de processos primeiro
            os.killpg(pgid, signal.SIGTERM)
            
            try:
                process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                # Se nao encerrou apos timeout, forca SIGKILL
                logger.warning(f"Grupo de processos nao respondeu ao SIGTERM, forcando: {simulation_id}")
                os.killpg(pgid, signal.SIGKILL)
                process.wait(timeout=5)
    
    @classmethod
    def stop_simulation(cls, simulation_id: str) -> SimulationRunState:
        """Parar simulacao"""
        state = cls.get_run_state(simulation_id)
        if not state:
            raise ValueError(f"Simulacao nao existe: {simulation_id}")
        
        if state.runner_status not in [RunnerStatus.RUNNING, RunnerStatus.PAUSED]:
            raise ValueError(f"Simulacao nao esta em execucao: {simulation_id}, status={state.runner_status}")
        
        state.runner_status = RunnerStatus.STOPPING
        cls._save_run_state(state)
        
        # Terminar processo
        process = cls._processes.get(simulation_id)
        if process and process.poll() is None:
            try:
                cls._terminate_process(process, simulation_id)
            except ProcessLookupError:
                # Processo ja nao existe
                pass
            except Exception as e:
                logger.error(f"Falha ao terminar grupo de processos: {simulation_id}, error={e}")
                # Fallback para terminacao direta
                try:
                    process.terminate()
                    process.wait(timeout=5)
                except Exception:
                    process.kill()
        
        state.runner_status = RunnerStatus.STOPPED
        state.twitter_running = False
        state.reddit_running = False
        state.completed_at = datetime.now().isoformat()
        cls._save_run_state(state)
        
        # Para atualizador de memoria do grafo
        if cls._graph_memory_enabled.get(simulation_id, False):
            try:
                ZepGraphMemoryManager.stop_updater(simulation_id)
                logger.info(f"Atualizacao de memoria do grafo parada: simulation_id={simulation_id}")
            except Exception as e:
                logger.error(f"Para atualizador de memoria do grafofalhou: {e}")
            cls._graph_memory_enabled.pop(simulation_id, None)
        
        logger.info(f"Simulacao parada: {simulation_id}")
        return state
    
    @classmethod
    def _read_actions_from_file(
        cls,
        file_path: str,
        default_platform: Optional[str] = None,
        platform_filter: Optional[str] = None,
        agent_id: Optional[int] = None,
        round_num: Optional[int] = None
    ) -> List[AgentAction]:
        """
        Le acoes de um unico arquivo de acoes
        
        Args:
            file_path: Caminho do arquivo de log de acoes
            default_platform: Plataforma padrao (quando o registro nao tem campo platform)
            platform_filter: Filtrar plataforma
            agent_id: Filtrar Agent ID
            round_num: Filtrar rodada
        """
        if not os.path.exists(file_path):
            return []
        
        actions = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                try:
                    data = json.loads(line)
                    
                    # Pula registros que nao sao acoes（como simulation_start, round_start, round_end, etc.）
                    if "event_type" in data:
                        continue
                    
                    # Pula registros sem agent_id (nao sao acoes de Agent)
                    if "agent_id" not in data:
                        continue
                    
                    # Obtem plataforma: prioriza platform do registro, senao usa padrao
                    record_platform = data.get("platform") or default_platform or ""
                    
                    # Filtro
                    if platform_filter and record_platform != platform_filter:
                        continue
                    if agent_id is not None and data.get("agent_id") != agent_id:
                        continue
                    if round_num is not None and data.get("round") != round_num:
                        continue
                    
                    actions.append(AgentAction(
                        round_num=data.get("round", 0),
                        timestamp=data.get("timestamp", ""),
                        platform=record_platform,
                        agent_id=data.get("agent_id", 0),
                        agent_name=data.get("agent_name", ""),
                        action_type=data.get("action_type", ""),
                        action_args=data.get("action_args", {}),
                        result=data.get("result"),
                        success=data.get("success", True),
                    ))
                    
                except json.JSONDecodeError:
                    continue
        
        return actions
    
    @classmethod
    def get_all_actions(
        cls,
        simulation_id: str,
        platform: Optional[str] = None,
        agent_id: Optional[int] = None,
        round_num: Optional[int] = None
    ) -> List[AgentAction]:
        """
        Obtem historico completo de acoes de todas as plataformas (sem paginacao)
        
        Args:
            simulation_id: ID da simulacao
            platform: Filtrar plataforma（twitter/reddit）
            agent_id: FiltroAgent
            round_num: Filtrar rodada
            
        Returns:
            Lista completa de acoes (ordenada por timestamp, recentes primeiro)
        """
        sim_dir = os.path.join(cls.RUN_STATE_DIR, simulation_id)
        actions = []
        
        # Le arquivo de acoes do Twitter (define platform automaticamente)
        twitter_actions_log = os.path.join(sim_dir, "twitter", "actions.jsonl")
        if not platform or platform == "twitter":
            actions.extend(cls._read_actions_from_file(
                twitter_actions_log,
                default_platform="twitter",  # Preenche campo platform automaticamente
                platform_filter=platform,
                agent_id=agent_id, 
                round_num=round_num
            ))
        
        # Le arquivo de acoes do Reddit (define platform automaticamente)
        reddit_actions_log = os.path.join(sim_dir, "reddit", "actions.jsonl")
        if not platform or platform == "reddit":
            actions.extend(cls._read_actions_from_file(
                reddit_actions_log,
                default_platform="reddit",  # Preenche campo platform automaticamente
                platform_filter=platform,
                agent_id=agent_id,
                round_num=round_num
            ))
        
        # Se arquivos por plataforma nao existem, tenta formato antigo de arquivo unico
        if not actions:
            actions_log = os.path.join(sim_dir, "actions.jsonl")
            actions = cls._read_actions_from_file(
                actions_log,
                default_platform=None,  # Formato antigo deve ter campo platform
                platform_filter=platform,
                agent_id=agent_id,
                round_num=round_num
            )
        
        # Ordena por timestamp (recentes primeiro)
        actions.sort(key=lambda x: x.timestamp, reverse=True)
        
        return actions
    
    @classmethod
    def get_actions(
        cls,
        simulation_id: str,
        limit: int = 100,
        offset: int = 0,
        platform: Optional[str] = None,
        agent_id: Optional[int] = None,
        round_num: Optional[int] = None
    ) -> List[AgentAction]:
        """
        Obtem historico de acoes (com paginacao)
        
        Args:
            simulation_id: ID da simulacao
            limit: Limite de quantidade
            offset: deslocamento
            platform: Filtrar plataforma
            agent_id: FiltroAgent
            round_num: Filtrar rodada
            
        Returns:
            Lista de acoes
        """
        actions = cls.get_all_actions(
            simulation_id=simulation_id,
            platform=platform,
            agent_id=agent_id,
            round_num=round_num
        )
        
        # Paginacao
        return actions[offset:offset + limit]
    
    @classmethod
    def get_timeline(
        cls,
        simulation_id: str,
        start_round: int = 0,
        end_round: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Obtem linha do tempo da simulacao (resumo por rodada)
        
        Args:
            simulation_id: ID da simulacao
            start_round: Rodada inicial
            end_round: Rodada final
            
        Returns:
            Informacoes resumidas por rodada
        """
        actions = cls.get_actions(simulation_id, limit=10000)
        
        # Agrupa por rodada
        rounds: Dict[int, Dict[str, Any]] = {}
        
        for action in actions:
            round_num = action.round_num
            
            if round_num < start_round:
                continue
            if end_round is not None and round_num > end_round:
                continue
            
            if round_num not in rounds:
                rounds[round_num] = {
                    "round_num": round_num,
                    "twitter_actions": 0,
                    "reddit_actions": 0,
                    "active_agents": set(),
                    "action_types": {},
                    "first_action_time": action.timestamp,
                    "last_action_time": action.timestamp,
                }
            
            r = rounds[round_num]
            
            if action.platform == "twitter":
                r["twitter_actions"] += 1
            else:
                r["reddit_actions"] += 1
            
            r["active_agents"].add(action.agent_id)
            r["action_types"][action.action_type] = r["action_types"].get(action.action_type, 0) + 1
            r["last_action_time"] = action.timestamp
        
        # Converte para lista
        result = []
        for round_num in sorted(rounds.keys()):
            r = rounds[round_num]
            result.append({
                "round_num": round_num,
                "twitter_actions": r["twitter_actions"],
                "reddit_actions": r["reddit_actions"],
                "total_actions": r["twitter_actions"] + r["reddit_actions"],
                "active_agents_count": len(r["active_agents"]),
                "active_agents": list(r["active_agents"]),
                "action_types": r["action_types"],
                "first_action_time": r["first_action_time"],
                "last_action_time": r["last_action_time"],
            })
        
        return result
    
    @classmethod
    def get_agent_stats(cls, simulation_id: str) -> List[Dict[str, Any]]:
        """
        Obtem estatisticas de cada Agent
        
        Returns:
            Lista de estatisticas dos Agents
        """
        actions = cls.get_actions(simulation_id, limit=10000)
        
        agent_stats: Dict[int, Dict[str, Any]] = {}
        
        for action in actions:
            agent_id = action.agent_id
            
            if agent_id not in agent_stats:
                agent_stats[agent_id] = {
                    "agent_id": agent_id,
                    "agent_name": action.agent_name,
                    "total_actions": 0,
                    "twitter_actions": 0,
                    "reddit_actions": 0,
                    "action_types": {},
                    "first_action_time": action.timestamp,
                    "last_action_time": action.timestamp,
                }
            
            stats = agent_stats[agent_id]
            stats["total_actions"] += 1
            
            if action.platform == "twitter":
                stats["twitter_actions"] += 1
            else:
                stats["reddit_actions"] += 1
            
            stats["action_types"][action.action_type] = stats["action_types"].get(action.action_type, 0) + 1
            stats["last_action_time"] = action.timestamp
        
        # Ordena por total de acoes
        result = sorted(agent_stats.values(), key=lambda x: x["total_actions"], reverse=True)
        
        return result
    
    @classmethod
    def cleanup_simulation_logs(cls, simulation_id: str) -> Dict[str, Any]:
        """
        Limpa logs de execucao da simulacao (para forcar reinicio)
        
        Remove os seguintes arquivos:
        - run_state.json
        - twitter/actions.jsonl
        - reddit/actions.jsonl
        - simulation.log
        - stdout.log / stderr.log
        - twitter_simulation.db (banco de dados da simulacao)
        - reddit_simulation.db (banco de dados da simulacao)
        - env_status.json (estado do ambiente)
        
        Nota: nao remove arquivos de configuracao (simulation_config.json) e profile
        
        Args:
            simulation_id: ID da simulacao
            
        Returns:
            Informacoes do resultado da limpeza
        """
        import shutil
        
        sim_dir = os.path.join(cls.RUN_STATE_DIR, simulation_id)
        
        if not os.path.exists(sim_dir):
            return {"success": True, "message": "Diretorio da simulacao nao existe, nao precisa limpar"}
        
        cleaned_files = []
        errors = []

        def remove_with_retry(path: str, label: str) -> bool:
            for attempt in range(1, 6):
                try:
                    os.remove(path)
                    return True
                except PermissionError as e:
                    if attempt < 5:
                        time.sleep(0.4 * attempt)
                        continue
                    errors.append(f"Remover {label} falhou: {str(e)}")
                    return False
                except Exception as e:
                    errors.append(f"Remover {label} falhou: {str(e)}")
                    return False
        
        # Lista de arquivos a remover (incluindo banco de dados)
        files_to_delete = [
            "run_state.json",
            "simulation.log",
            "stdout.log",
            "stderr.log",
            "twitter_simulation.db",  # Banco de dados da plataforma Twitter
            "reddit_simulation.db",   # Banco de dados da plataforma Reddit
            "env_status.json",        # Arquivo de estado do ambiente
        ]
        
        # Lista de diretorios a limpar (contendo logs de acoes)
        dirs_to_clean = ["twitter", "reddit"]
        
        # arquivos removidos
        for filename in files_to_delete:
            file_path = os.path.join(sim_dir, filename)
            if os.path.exists(file_path):
                if remove_with_retry(file_path, filename):
                    cleaned_files.append(filename)
        
        # Limpa logs de acoes nos diretorios de plataforma
        for dir_name in dirs_to_clean:
            dir_path = os.path.join(sim_dir, dir_name)
            if os.path.exists(dir_path):
                actions_file = os.path.join(dir_path, "actions.jsonl")
                if os.path.exists(actions_file):
                    if remove_with_retry(actions_file, f"{dir_name}/actions.jsonl"):
                        cleaned_files.append(f"{dir_name}/actions.jsonl")
        
        # Limpa estado de execucao em memoria
        if simulation_id in cls._run_states:
            del cls._run_states[simulation_id]
        
        logger.info(f"Limpeza de logs da simulacao concluida: {simulation_id}, arquivos removidos: {cleaned_files}")
        
        return {
            "success": len(errors) == 0,
            "cleaned_files": cleaned_files,
            "errors": errors if errors else None
        }
    
    # Flag para prevenir limpeza duplicada
    _cleanup_done = False
    
    @classmethod
    def cleanup_all_simulations(cls):
        """
        Limpa todos os processos de simulacao em execucao
        
        Chamado ao fechar servidor, garante terminacao de todos os subprocessos
        """
        # Previne limpeza duplicada
        if cls._cleanup_done:
            return
        cls._cleanup_done = True
        
        # Verifica se ha conteudo para limpar (evita logs desnecessarios)
        has_processes = bool(cls._processes)
        has_updaters = bool(cls._graph_memory_enabled)
        
        if not has_processes and not has_updaters:
            return  # Nada para limpar, retorna silenciosamente
        
        logger.info("Limpando todos os processos de simulacao...")
        
        # Para todos os atualizadores de memoria (stop_all imprime logs internamente)
        try:
            ZepGraphMemoryManager.stop_all()
        except Exception as e:
            logger.error(f"Para atualizador de memoria do grafofalhou: {e}")
        cls._graph_memory_enabled.clear()
        
        # Copia dicionario para evitar modificacao durante iteracao
        processes = list(cls._processes.items())
        
        for simulation_id, process in processes:
            try:
                if process.poll() is None:  # Processo ainda em execucao
                    logger.info(f"Terminando processo de simulacao: {simulation_id}, pid={process.pid}")
                    
                    try:
                        # Usa metodo de terminacao cross-platform
                        cls._terminate_process(process, simulation_id, timeout=5)
                    except (ProcessLookupError, OSError):
                        # Processo pode nao existir, tenta terminacao direta
                        try:
                            process.terminate()
                            process.wait(timeout=3)
                        except Exception:
                            process.kill()
                    
                    # Atualiza run_state.json sem sobrescrever uma conclusao ja auditada nos logs.
                    state = cls.get_run_state(simulation_id)
                    state_json_status = "stopped"
                    if state:
                        state = cls._reconcile_run_state_from_artifacts(state, include_active=True)
                        if state.runner_status == RunnerStatus.COMPLETED:
                            state_json_status = "completed"
                        else:
                            state.runner_status = RunnerStatus.STOPPED
                            state.twitter_running = False
                            state.reddit_running = False
                            state.completed_at = datetime.now().isoformat()
                            state.error = "Servidor encerrado, simulacao terminada"
                            cls._save_run_state(state)
                    
                    # Tambem atualiza state.json de forma coerente com o estado reconciliado.
                    try:
                        sim_dir = os.path.join(cls.RUN_STATE_DIR, simulation_id)
                        state_file = os.path.join(sim_dir, "state.json")
                        logger.info(f"Tentando atualizar state.json: {state_file}")
                        if os.path.exists(state_file):
                            with open(state_file, 'r', encoding='utf-8') as f:
                                state_data = json.load(f)
                            state_data['status'] = state_json_status
                            if state_json_status == "completed":
                                state_data["twitter_status"] = "completed"
                                state_data["reddit_status"] = "completed"
                                state_data["error"] = None
                            else:
                                state_data["error"] = "Servidor encerrado, simulacao terminada"
                            state_data['updated_at'] = datetime.now().isoformat()
                            with open(state_file, 'w', encoding='utf-8') as f:
                                json.dump(state_data, f, indent=2, ensure_ascii=False)
                            logger.info(f"state.json atualizado para {state_json_status}: {simulation_id}")
                        else:
                            logger.warning(f"state.json nao existe: {state_file}")
                    except Exception as state_err:
                        logger.warning(f"Falha ao atualizar state.json: {simulation_id}, error={state_err}")
                        
            except Exception as e:
                logger.error(f"Falha ao limpar processo: {simulation_id}, error={e}")
        
        # Limpa handles de arquivo
        for simulation_id, file_handle in list(cls._stdout_files.items()):
            try:
                if file_handle:
                    file_handle.close()
            except Exception:
                pass
        cls._stdout_files.clear()
        
        for simulation_id, file_handle in list(cls._stderr_files.items()):
            try:
                if file_handle:
                    file_handle.close()
            except Exception:
                pass
        cls._stderr_files.clear()
        
        # Limpa estado em memoria
        cls._processes.clear()
        cls._action_queues.clear()
        
        logger.info("Limpeza de processos de simulacao concluida")
    
    @classmethod
    def register_cleanup(cls):
        """
        Registrar funcao de limpeza
        
        Chamado ao iniciar Flask, garante limpeza ao fechar servidor
        """
        global _cleanup_registered
        
        if _cleanup_registered:
            return
        
        # No modo debug do Flask, registra limpeza apenas no subprocesso reloader (processo que executa a aplicacao)
        # WERKZEUG_RUN_MAIN=true indica subprocesso reloader
        # Se nao for modo debug, nao tem esta variavel, tambem precisa registrar
        is_reloader_process = os.environ.get('WERKZEUG_RUN_MAIN') == 'true'
        is_debug_mode = os.environ.get('FLASK_DEBUG') == '1' or os.environ.get('WERKZEUG_RUN_MAIN') is not None
        
        # No modo debug, registra apenas no subprocesso reloader; fora do debug, sempre registra
        if is_debug_mode and not is_reloader_process:
            _cleanup_registered = True  # Marca como registrado, previne nova tentativa do subprocesso
            return
        
        # Salva handlers de sinal originais
        original_sigint = signal.getsignal(signal.SIGINT)
        original_sigterm = signal.getsignal(signal.SIGTERM)
        # SIGHUP so existe em Unix (macOS/Linux), Windows nao tem
        original_sighup = None
        has_sighup = hasattr(signal, 'SIGHUP')
        if has_sighup:
            original_sighup = signal.getsignal(signal.SIGHUP)
        
        def cleanup_handler(signum=None, frame=None):
            """Handler de sinal: limpa processos primeiro, depois chama handler original"""
            # So imprime log quando ha processos para limpar
            if cls._processes or cls._graph_memory_enabled:
                logger.info(f"Sinal recebido {signum}，iniciando limpeza...")
            cls.cleanup_all_simulations()
            
            # Chama handler original, permite Flask sair normalmente
            if signum == signal.SIGINT and callable(original_sigint):
                original_sigint(signum, frame)
            elif signum == signal.SIGTERM and callable(original_sigterm):
                original_sigterm(signum, frame)
            elif has_sighup and signum == signal.SIGHUP:
                # SIGHUP: enviado ao fechar terminal
                if callable(original_sighup):
                    original_sighup(signum, frame)
                else:
                    # Comportamento padrao: saida normal
                    sys.exit(0)
            else:
                # Se handler original nao e chamavel (ex: SIG_DFL), usa comportamento padrao
                raise KeyboardInterrupt
        
        # Registra handler atexit (como backup)
        atexit.register(cls.cleanup_all_simulations)
        
        # Registra handlers de sinal (apenas na thread principal)
        try:
            # SIGTERM: sinal padrao do comando kill
            signal.signal(signal.SIGTERM, cleanup_handler)
            # SIGINT: Ctrl+C
            signal.signal(signal.SIGINT, cleanup_handler)
            # SIGHUP: fechamento de terminal (apenas Unix)
            if has_sighup:
                signal.signal(signal.SIGHUP, cleanup_handler)
        except ValueError:
            # Nao esta na thread principal, usando apenas atexit
            logger.warning("Nao foi possivel registrar handlers de sinal (nao na thread principal), usando apenas atexit")
        
        _cleanup_registered = True
    
    @classmethod
    def get_running_simulations(cls) -> List[str]:
        """
        Obtem lista de IDs de simulacoes em execucao
        """
        running = []
        for sim_id, process in cls._processes.items():
            if process.poll() is None:
                running.append(sim_id)
        return running
    
    # ============== Funcionalidade de Interview ==============
    
    @classmethod
    def check_env_alive(cls, simulation_id: str) -> bool:
        """
        Verifica se o ambiente de simulacao esta ativo (pode receber comandos)

        Args:
            simulation_id: ID da simulacao

        Returns:
            True indica ambiente ativo, False indica ambiente encerrado
        """
        sim_dir = os.path.join(cls.RUN_STATE_DIR, simulation_id)
        if not os.path.exists(sim_dir):
            return False

        ipc_client = SimulationIPCClient(sim_dir)
        return ipc_client.check_env_alive()

    @classmethod
    def get_env_status_detail(cls, simulation_id: str) -> Dict[str, Any]:
        """
        Obtem informacoes detalhadas do estado do ambiente

        Args:
            simulation_id: ID da simulacao

        Returns:
            Dicionario de detalhes do estado，, contendo status, twitter_available, reddit_available, timestamp
        """
        sim_dir = os.path.join(cls.RUN_STATE_DIR, simulation_id)
        status_file = os.path.join(sim_dir, "env_status.json")
        
        default_status = {
            "status": "stopped",
            "twitter_available": False,
            "reddit_available": False,
            "timestamp": None
        }
        
        if not os.path.exists(status_file):
            return default_status
        
        try:
            with open(status_file, 'r', encoding='utf-8') as f:
                status = json.load(f)
            return {
                "status": status.get("status", "stopped"),
                "twitter_available": status.get("twitter_available", False),
                "reddit_available": status.get("reddit_available", False),
                "timestamp": status.get("timestamp")
            }
        except (json.JSONDecodeError, OSError):
            return default_status

    @classmethod
    def interview_agent(
        cls,
        simulation_id: str,
        agent_id: int,
        prompt: str,
        platform: str = None,
        timeout: float = 60.0
    ) -> Dict[str, Any]:
        """
        Entrevistar um Agent

        Args:
            simulation_id: ID da simulacao
            agent_id: Agent ID
            prompt: pergunta da entrevista
            platform: especificar plataforma (opcional)
                - "twitter": entrevista apenas Twitter
                - "reddit": entrevista apenas Reddit
                - None: em simulacao dual, entrevista ambas plataformas, retorna resultado integrado
            timeout: tempo limite (segundos)

        Returns:
            Dicionario de resultado da entrevista

        Raises:
            ValueError: Simulacao nao existe ou ambiente nao esta em execucao
            TimeoutError: timeout ao aguardar resposta
        """
        sim_dir = os.path.join(cls.RUN_STATE_DIR, simulation_id)
        if not os.path.exists(sim_dir):
            raise ValueError(f"Simulacao nao existe: {simulation_id}")

        ipc_client = SimulationIPCClient(sim_dir)

        if not ipc_client.check_env_alive():
            raise ValueError(f"Ambiente nao esta em execucao ou foi encerrado, impossivel executar Interview: {simulation_id}")

        logger.info(f"Enviando comando de Interview: simulation_id={simulation_id}, agent_id={agent_id}, platform={platform}")

        response = ipc_client.send_interview(
            agent_id=agent_id,
            prompt=prompt,
            platform=platform,
            timeout=timeout
        )

        if response.status.value == "completed":
            return {
                "success": True,
                "agent_id": agent_id,
                "prompt": prompt,
                "result": response.result,
                "timestamp": response.timestamp
            }
        else:
            return {
                "success": False,
                "agent_id": agent_id,
                "prompt": prompt,
                "error": response.error,
                "timestamp": response.timestamp
            }
    
    @classmethod
    def interview_agents_batch(
        cls,
        simulation_id: str,
        interviews: List[Dict[str, Any]],
        platform: str = None,
        timeout: float = 120.0
    ) -> Dict[str, Any]:
        """
        Entrevistando multiplos Agents em lote

        Args:
            simulation_id: ID da simulacao
            interviews: lista de entrevistas, cada elemento contem {"agent_id": int, "prompt": str, "platform": str(opcional)}
            platform: plataforma padrao (opcional, sobrescrita pelo platform de cada item)
                - "twitter": padrao apenas Twitter
                - "reddit": padrao apenas Reddit
                - None: em simulacao dual, cada Agent entrevistado em ambas
            timeout: tempo limite (segundos)

        Returns:
            Dicionario de resultado da entrevista em lote

        Raises:
            ValueError: Simulacao nao existe ou ambiente nao esta em execucao
            TimeoutError: timeout ao aguardar resposta
        """
        sim_dir = os.path.join(cls.RUN_STATE_DIR, simulation_id)
        if not os.path.exists(sim_dir):
            raise ValueError(f"Simulacao nao existe: {simulation_id}")

        ipc_client = SimulationIPCClient(sim_dir)

        if not ipc_client.check_env_alive():
            raise ValueError(f"Ambiente nao esta em execucao ou foi encerrado, impossivel executar Interview: {simulation_id}")

        logger.info(f"Enviando comando de Interview em lote: simulation_id={simulation_id}, count={len(interviews)}, platform={platform}")

        response = ipc_client.send_batch_interview(
            interviews=interviews,
            platform=platform,
            timeout=timeout
        )

        if response.status.value == "completed":
            return {
                "success": True,
                "interviews_count": len(interviews),
                "result": response.result,
                "timestamp": response.timestamp
            }
        else:
            return {
                "success": False,
                "interviews_count": len(interviews),
                "error": response.error,
                "timestamp": response.timestamp
            }
    
    @classmethod
    def interview_all_agents(
        cls,
        simulation_id: str,
        prompt: str,
        platform: str = None,
        timeout: float = 180.0
    ) -> Dict[str, Any]:
        """
        Entrevistar todos os Agents (entrevista global)

        Entrevista todos os Agents com a mesma pergunta

        Args:
            simulation_id: ID da simulacao
            prompt: pergunta da entrevista (mesma para todos os Agents)
            platform: especificar plataforma (opcional)
                - "twitter": entrevista apenas Twitter
                - "reddit": entrevista apenas Reddit
                - None: em simulacao dual, cada Agent entrevistado em ambas
            timeout: tempo limite (segundos)

        Returns:
            Dicionario de resultado da entrevista global
        """
        sim_dir = os.path.join(cls.RUN_STATE_DIR, simulation_id)
        if not os.path.exists(sim_dir):
            raise ValueError(f"Simulacao nao existe: {simulation_id}")

        # Obtem informacoes de todos os Agents do arquivo de configuracao
        config_path = os.path.join(sim_dir, "simulation_config.json")
        if not os.path.exists(config_path):
            raise ValueError(f"Configuracao da simulacao nao existe: {simulation_id}")

        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        agent_configs = config.get("agent_configs", [])
        if not agent_configs:
            raise ValueError(f"Nenhum Agent na configuracao: {simulation_id}")

        # Constroi lista de entrevistas em lote
        interviews = []
        for agent_config in agent_configs:
            agent_id = agent_config.get("agent_id")
            if agent_id is not None:
                interviews.append({
                    "agent_id": agent_id,
                    "prompt": prompt
                })

        logger.info(f"Enviando comando de Interview global: simulation_id={simulation_id}, agent_count={len(interviews)}, platform={platform}")

        return cls.interview_agents_batch(
            simulation_id=simulation_id,
            interviews=interviews,
            platform=platform,
            timeout=timeout
        )
    
    @classmethod
    def close_simulation_env(
        cls,
        simulation_id: str,
        timeout: float = 30.0
    ) -> Dict[str, Any]:
        """
        Fechar ambiente de simulacao (sem parar o processo)
        
        Envia comando de fechamento, saindo elegantemente do modo de espera
        
        Args:
            simulation_id: ID da simulacao
            timeout: tempo limite (segundos)
            
        Returns:
            Dicionario de resultado da operacao
        """
        sim_dir = os.path.join(cls.RUN_STATE_DIR, simulation_id)
        if not os.path.exists(sim_dir):
            raise ValueError(f"Simulacao nao existe: {simulation_id}")
        
        ipc_client = SimulationIPCClient(sim_dir)
        
        if not ipc_client.check_env_alive():
            return {
                "success": True,
                "message": "Ambiente ja encerrado"
            }
        
        logger.info(f"Enviando comando de fechamento do ambiente: simulation_id={simulation_id}")
        
        try:
            response = ipc_client.send_close_env(timeout=timeout)
            
            return {
                "success": response.status.value == "completed",
                "message": "Comando de fechamento enviado",
                "result": response.result,
                "timestamp": response.timestamp
            }
        except TimeoutError:
            # Timeout pode ser porque o ambiente esta encerrando
            return {
                "success": True,
                "message": "Comando de fechamento enviado (timeout aguardando resposta, ambiente pode estar encerrando)"
            }
    
    @classmethod
    def _get_interview_history_from_db(
        cls,
        db_path: str,
        platform_name: str,
        agent_id: Optional[int] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Obtem historico de Interview de um banco de dados"""
        import sqlite3
        
        if not os.path.exists(db_path):
            return []
        
        results = []
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            if agent_id is not None:
                cursor.execute("""
                    SELECT user_id, info, created_at
                    FROM trace
                    WHERE action = 'interview' AND user_id = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                """, (agent_id, limit))
            else:
                cursor.execute("""
                    SELECT user_id, info, created_at
                    FROM trace
                    WHERE action = 'interview'
                    ORDER BY created_at DESC
                    LIMIT ?
                """, (limit,))
            
            for user_id, info_json, created_at in cursor.fetchall():
                try:
                    info = json.loads(info_json) if info_json else {}
                except json.JSONDecodeError:
                    info = {"raw": info_json}
                
                results.append({
                    "agent_id": user_id,
                    "response": info.get("response", info),
                    "prompt": info.get("prompt", ""),
                    "timestamp": created_at,
                    "platform": platform_name
                })
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Falha ao ler historico de Interview ({platform_name}): {e}")
        
        return results

    @classmethod
    def get_interview_history(
        cls,
        simulation_id: str,
        platform: str = None,
        agent_id: Optional[int] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Obtem historico de Interview (do banco de dados)
        
        Args:
            simulation_id: ID da simulacao
            platform: Tipo de plataforma (reddit/twitter/None)
                - "reddit": obtem apenas historico do Reddit
                - "twitter": obtem apenas historico do Twitter
                - None: obtem historico de ambas plataformas
            agent_id: Agent ID especifico (opcional, obtem apenas historico deste Agent)
            limit: limite de quantidade por plataforma
            
        Returns:
            Lista de registros de historico de Interview
        """
        sim_dir = os.path.join(cls.RUN_STATE_DIR, simulation_id)
        
        results = []
        
        # Determina plataformas a consultar
        if platform in ("reddit", "twitter"):
            platforms = [platform]
        else:
            # Sem platform especificado, consulta ambas plataformas
            platforms = ["twitter", "reddit"]
        
        for p in platforms:
            db_path = os.path.join(sim_dir, f"{p}_simulation.db")
            platform_results = cls._get_interview_history_from_db(
                db_path=db_path,
                platform_name=p,
                agent_id=agent_id,
                limit=limit
            )
            results.extend(platform_results)
        
        # Ordena por tempo decrescente
        results.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        # Se consultou multiplas plataformas, limita total
        if len(platforms) > 1 and len(results) > limit:
            results = results[:limit]
        
        return results

