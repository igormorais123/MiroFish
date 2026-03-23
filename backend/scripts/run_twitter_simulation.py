"""
Script de simulacao OASIS Twitter com configuracoes predefinidas
Este script le os parametros do arquivo de configuracao para executar a simulacao de forma totalmente automatizada

Funcionalidades:
- Apos concluir a simulacao, nao encerra o ambiente imediatamente, entra em modo de espera por comandos
- Suporta recebimento de comandos de Interview via IPC
- Suporta entrevista individual e em lote de Agentes
- Suporta comando remoto de encerramento do ambiente

Modo de uso:
    python run_twitter_simulation.py --config /path/to/simulation_config.json
    python run_twitter_simulation.py --config /path/to/simulation_config.json --no-wait  # Encerra imediatamente apos conclusao
"""

import argparse
import asyncio
import json
import logging
import os
import random
import signal
import sys
import sqlite3
from datetime import datetime
from typing import Dict, Any, List, Optional

# Variaveis globais: usadas para tratamento de sinais
_shutdown_event = None
_cleanup_done = False

# Adicionar caminho do projeto
_scripts_dir = os.path.dirname(os.path.abspath(__file__))
_backend_dir = os.path.abspath(os.path.join(_scripts_dir, '..'))
_project_root = os.path.abspath(os.path.join(_backend_dir, '..'))
sys.path.insert(0, _scripts_dir)
sys.path.insert(0, _backend_dir)

# Carregar arquivo .env do diretorio raiz do projeto (contem configuracoes como LLM_API_KEY)
from dotenv import load_dotenv
_env_file = os.path.join(_project_root, '.env')
if os.path.exists(_env_file):
    load_dotenv(_env_file)
else:
    _backend_env = os.path.join(_backend_dir, '.env')
    if os.path.exists(_backend_env):
        load_dotenv(_backend_env)


import re


class UnicodeFormatter(logging.Formatter):
    """Formatador customizado que converte sequencias de escape Unicode em caracteres legiveis"""
    
    UNICODE_ESCAPE_PATTERN = re.compile(r'\\u([0-9a-fA-F]{4})')
    
    def format(self, record):
        result = super().format(record)
        
        def replace_unicode(match):
            try:
                return chr(int(match.group(1), 16))
            except (ValueError, OverflowError):
                return match.group(0)
        
        return self.UNICODE_ESCAPE_PATTERN.sub(replace_unicode, result)


class MaxTokensWarningFilter(logging.Filter):
    """Filtra avisos do camel-ai sobre max_tokens (nao definimos max_tokens intencionalmente, deixando o modelo decidir)"""

    def filter(self, record):
        # Filtrar logs contendo aviso de max_tokens
        if "max_tokens" in record.getMessage() and "Invalid or missing" in record.getMessage():
            return False
        return True


# Adicionar filtro imediatamente ao carregar o modulo, garantindo que esteja ativo antes da execucao do codigo camel
logging.getLogger().addFilter(MaxTokensWarningFilter())


def setup_oasis_logging(log_dir: str):
    """Configura os logs do OASIS usando arquivos de log com nomes fixos"""
    os.makedirs(log_dir, exist_ok=True)
    
    # Limpar arquivos de log antigos
    for f in os.listdir(log_dir):
        old_log = os.path.join(log_dir, f)
        if os.path.isfile(old_log) and f.endswith('.log'):
            try:
                os.remove(old_log)
            except OSError:
                pass
    
    formatter = UnicodeFormatter("%(levelname)s - %(asctime)s - %(name)s - %(message)s")
    
    loggers_config = {
        "social.agent": os.path.join(log_dir, "social.agent.log"),
        "social.twitter": os.path.join(log_dir, "social.twitter.log"),
        "social.rec": os.path.join(log_dir, "social.rec.log"),
        "oasis.env": os.path.join(log_dir, "oasis.env.log"),
        "table": os.path.join(log_dir, "table.log"),
    }
    
    for logger_name, log_file in loggers_config.items():
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.DEBUG)
        logger.handlers.clear()
        file_handler = logging.FileHandler(log_file, encoding='utf-8', mode='w')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        logger.propagate = False


try:
    from camel.models import ModelFactory
    from camel.types import ModelPlatformType
    import oasis
    from oasis import (
        ActionType,
        LLMAction,
        ManualAction,
        generate_twitter_agent_graph
    )
except ImportError as e:
    print(f"Erro: dependencia ausente {e}")
    print("Instale primeiro: pip install oasis-ai camel-ai")
    sys.exit(1)


# Constantes relacionadas ao IPC
IPC_COMMANDS_DIR = "ipc_commands"
IPC_RESPONSES_DIR = "ipc_responses"
ENV_STATUS_FILE = "env_status.json"

class CommandType:
    """Constantes de tipos de comando"""
    INTERVIEW = "interview"
    BATCH_INTERVIEW = "batch_interview"
    CLOSE_ENV = "close_env"


class IPCHandler:
    """Processador de comandos IPC"""
    
    def __init__(self, simulation_dir: str, env, agent_graph):
        self.simulation_dir = simulation_dir
        self.env = env
        self.agent_graph = agent_graph
        self.commands_dir = os.path.join(simulation_dir, IPC_COMMANDS_DIR)
        self.responses_dir = os.path.join(simulation_dir, IPC_RESPONSES_DIR)
        self.status_file = os.path.join(simulation_dir, ENV_STATUS_FILE)
        self._running = True
        
        # Garantir que os diretorios existam
        os.makedirs(self.commands_dir, exist_ok=True)
        os.makedirs(self.responses_dir, exist_ok=True)
    
    def update_status(self, status: str):
        """Atualizar status do ambiente"""
        with open(self.status_file, 'w', encoding='utf-8') as f:
            json.dump({
                "status": status,
                "timestamp": datetime.now().isoformat()
            }, f, ensure_ascii=False, indent=2)
    
    def poll_command(self) -> Optional[Dict[str, Any]]:
        """Buscar comandos pendentes por polling"""
        if not os.path.exists(self.commands_dir):
            return None
        
        # Obter arquivos de comando (ordenados por tempo)
        command_files = []
        for filename in os.listdir(self.commands_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(self.commands_dir, filename)
                command_files.append((filepath, os.path.getmtime(filepath)))
        
        command_files.sort(key=lambda x: x[1])
        
        for filepath, _ in command_files:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                continue
        
        return None
    
    def send_response(self, command_id: str, status: str, result: Dict = None, error: str = None):
        """Enviar resposta"""
        response = {
            "command_id": command_id,
            "status": status,
            "result": result,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }
        
        response_file = os.path.join(self.responses_dir, f"{command_id}.json")
        with open(response_file, 'w', encoding='utf-8') as f:
            json.dump(response, f, ensure_ascii=False, indent=2)
        
        # Excluir arquivo de comando
        command_file = os.path.join(self.commands_dir, f"{command_id}.json")
        try:
            os.remove(command_file)
        except OSError:
            pass
    
    async def handle_interview(self, command_id: str, agent_id: int, prompt: str) -> bool:
        """
        Processar comando de entrevista de um unico Agente

        Returns:
            True indica sucesso, False indica falha
        """
        try:
            # Obter Agente
            agent = self.agent_graph.get_agent(agent_id)
            
            # Criar acao de Interview
            interview_action = ManualAction(
                action_type=ActionType.INTERVIEW,
                action_args={"prompt": prompt}
            )
            
            # Executar Interview
            actions = {agent: interview_action}
            await self.env.step(actions)
            
            # Obter resultado do banco de dados
            result = self._get_interview_result(agent_id)
            
            self.send_response(command_id, "completed", result=result)
            print(f"  Interview concluido: agent_id={agent_id}")
            return True
            
        except Exception as e:
            error_msg = str(e)
            print(f"  Interview falhou: agent_id={agent_id}, error={error_msg}")
            self.send_response(command_id, "failed", error=error_msg)
            return False
    
    async def handle_batch_interview(self, command_id: str, interviews: List[Dict]) -> bool:
        """
        Processar comando de entrevista em lote

        Args:
            interviews: [{"agent_id": int, "prompt": str}, ...]
        """
        try:
            # Construir dicionario de acoes
            actions = {}
            agent_prompts = {}  # Registrar o prompt de cada agente
            
            for interview in interviews:
                agent_id = interview.get("agent_id")
                prompt = interview.get("prompt", "")
                
                try:
                    agent = self.agent_graph.get_agent(agent_id)
                    actions[agent] = ManualAction(
                        action_type=ActionType.INTERVIEW,
                        action_args={"prompt": prompt}
                    )
                    agent_prompts[agent_id] = prompt
                except Exception as e:
                    print(f"  Aviso: nao foi possivel obter Agente {agent_id}: {e}")

            if not actions:
                self.send_response(command_id, "failed", error="Nenhum Agente valido")
                return False
            
            # Executar Interview em lote
            await self.env.step(actions)
            
            # Obter todos os resultados
            results = {}
            for agent_id in agent_prompts.keys():
                result = self._get_interview_result(agent_id)
                results[agent_id] = result
            
            self.send_response(command_id, "completed", result={
                "interviews_count": len(results),
                "results": results
            })
            print(f"  Interview em lote concluido: {len(results)} Agentes")
            return True
            
        except Exception as e:
            error_msg = str(e)
            print(f"  Interview em lote falhou: {error_msg}")
            self.send_response(command_id, "failed", error=error_msg)
            return False
    
    def _get_interview_result(self, agent_id: int) -> Dict[str, Any]:
        """Obter o resultado mais recente do Interview do banco de dados"""
        db_path = os.path.join(self.simulation_dir, "twitter_simulation.db")
        
        result = {
            "agent_id": agent_id,
            "response": None,
            "timestamp": None
        }
        
        if not os.path.exists(db_path):
            return result
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Consultar o registro de Interview mais recente
            cursor.execute("""
                SELECT user_id, info, created_at
                FROM trace
                WHERE action = ? AND user_id = ?
                ORDER BY created_at DESC
                LIMIT 1
            """, (ActionType.INTERVIEW.value, agent_id))
            
            row = cursor.fetchone()
            if row:
                user_id, info_json, created_at = row
                try:
                    info = json.loads(info_json) if info_json else {}
                    result["response"] = info.get("response", info)
                    result["timestamp"] = created_at
                except json.JSONDecodeError:
                    result["response"] = info_json
            
            conn.close()
            
        except Exception as e:
            print(f"  Falha ao ler resultado do Interview: {e}")
        
        return result
    
    async def process_commands(self) -> bool:
        """
        Processar todos os comandos pendentes

        Returns:
            True indica continuar executando, False indica que deve encerrar
        """
        command = self.poll_command()
        if not command:
            return True
        
        command_id = command.get("command_id")
        command_type = command.get("command_type")
        args = command.get("args", {})
        
        print(f"\nComando IPC recebido: {command_type}, id={command_id}")
        
        if command_type == CommandType.INTERVIEW:
            await self.handle_interview(
                command_id,
                args.get("agent_id", 0),
                args.get("prompt", "")
            )
            return True
            
        elif command_type == CommandType.BATCH_INTERVIEW:
            await self.handle_batch_interview(
                command_id,
                args.get("interviews", [])
            )
            return True
            
        elif command_type == CommandType.CLOSE_ENV:
            print("Comando de encerrar ambiente recebido")
            self.send_response(command_id, "completed", result={"message": "Ambiente sera encerrado"})
            return False
        
        else:
            self.send_response(command_id, "failed", error=f"Tipo de comando desconhecido: {command_type}")
            return True


class TwitterSimulationRunner:
    """Executor de simulacao Twitter"""

    # Acoes disponiveis no Twitter (nao inclui INTERVIEW, que so pode ser acionado manualmente via ManualAction)
    AVAILABLE_ACTIONS = [
        ActionType.CREATE_POST,
        ActionType.LIKE_POST,
        ActionType.REPOST,
        ActionType.FOLLOW,
        ActionType.DO_NOTHING,
        ActionType.QUOTE_POST,
    ]
    
    def __init__(self, config_path: str, wait_for_commands: bool = True):
        """
        Inicializar executor de simulacao

        Args:
            config_path: Caminho do arquivo de configuracao (simulation_config.json)
            wait_for_commands: Se deve aguardar comandos apos conclusao da simulacao (padrao True)
        """
        self.config_path = config_path
        self.config = self._load_config()
        self.simulation_dir = os.path.dirname(config_path)
        self.wait_for_commands = wait_for_commands
        self.env = None
        self.agent_graph = None
        self.ipc_handler = None
        
    def _load_config(self) -> Dict[str, Any]:
        """Carregar arquivo de configuracao"""
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _get_profile_path(self) -> str:
        """Obter caminho do arquivo de Profile (OASIS Twitter usa formato CSV)"""
        return os.path.join(self.simulation_dir, "twitter_profiles.csv")
    
    def _get_db_path(self) -> str:
        """Obter caminho do banco de dados"""
        return os.path.join(self.simulation_dir, "twitter_simulation.db")
    
    def _create_model(self):
        """
        Criar modelo LLM

        Usa configuracoes do arquivo .env do diretorio raiz do projeto (prioridade maxima):
        - LLM_API_KEY: Chave da API
        - LLM_BASE_URL: URL base da API
        - LLM_MODEL_NAME: Nome do modelo
        """
        # Prioridade: ler configuracao do .env
        llm_api_key = os.environ.get("LLM_API_KEY", "")
        llm_base_url = os.environ.get("LLM_BASE_URL", "")
        llm_model = os.environ.get("LLM_MODEL_NAME", "")
        
        # Se nao houver no .env, usar config como fallback
        if not llm_model:
            llm_model = self.config.get("llm_model", "gpt-4o-mini")
        
        # Configurar variaveis de ambiente necessarias para o camel-ai
        if llm_api_key:
            os.environ["OPENAI_API_KEY"] = llm_api_key
        
        if not os.environ.get("OPENAI_API_KEY"):
            raise ValueError("Configuracao de API Key ausente. Defina LLM_API_KEY no arquivo .env do diretorio raiz do projeto")
        
        if llm_base_url:
            os.environ["OPENAI_API_BASE_URL"] = llm_base_url
        
        print(f"Configuracao LLM: model={llm_model}, base_url={llm_base_url[:40] if llm_base_url else 'padrao'}...")
        
        return ModelFactory.create(
            model_platform=ModelPlatformType.OPENAI,
            model_type=llm_model,
        )
    
    def _get_active_agents_for_round(
        self, 
        env, 
        current_hour: int,
        round_num: int
    ) -> List:
        """
        Decidir quais Agentes ativar nesta rodada com base no horario e configuracao

        Args:
            env: Ambiente OASIS
            current_hour: Hora simulada atual (0-23)
            round_num: Rodada atual

        Returns:
            Lista de Agentes ativados
        """
        time_config = self.config.get("time_config", {})
        agent_configs = self.config.get("agent_configs", [])
        
        # Quantidade base de ativacao
        base_min = time_config.get("agents_per_hour_min", 5)
        base_max = time_config.get("agents_per_hour_max", 20)
        
        # Ajustar conforme periodo do dia
        peak_hours = time_config.get("peak_hours", [9, 10, 11, 14, 15, 20, 21, 22])
        off_peak_hours = time_config.get("off_peak_hours", [0, 1, 2, 3, 4, 5])
        
        if current_hour in peak_hours:
            multiplier = time_config.get("peak_activity_multiplier", 1.5)
        elif current_hour in off_peak_hours:
            multiplier = time_config.get("off_peak_activity_multiplier", 0.3)
        else:
            multiplier = 1.0
        
        target_count = int(random.uniform(base_min, base_max) * multiplier)
        
        # Calcular probabilidade de ativacao com base na configuracao de cada Agente
        candidates = []
        for cfg in agent_configs:
            agent_id = cfg.get("agent_id", 0)
            active_hours = cfg.get("active_hours", list(range(8, 23)))
            activity_level = cfg.get("activity_level", 0.5)
            
            # Verificar se esta no horario ativo
            if current_hour not in active_hours:
                continue
            
            # Calcular probabilidade com base no nivel de atividade
            if random.random() < activity_level:
                candidates.append(agent_id)
        
        # Selecao aleatoria
        selected_ids = random.sample(
            candidates, 
            min(target_count, len(candidates))
        ) if candidates else []
        
        # Converter para objetos Agent
        active_agents = []
        for agent_id in selected_ids:
            try:
                agent = env.agent_graph.get_agent(agent_id)
                active_agents.append((agent_id, agent))
            except Exception:
                pass
        
        return active_agents
    
    async def run(self, max_rounds: int = None):
        """Executar simulacao Twitter

        Args:
            max_rounds: Numero maximo de rodadas de simulacao (opcional, para truncar simulacoes muito longas)
        """
        print("=" * 60)
        print("Simulacao OASIS Twitter")
        print(f"Arquivo de configuracao: {self.config_path}")
        print(f"ID da simulacao: {self.config.get('simulation_id', 'unknown')}")
        print(f"Modo espera por comandos: {'ativado' if self.wait_for_commands else 'desativado'}")
        print("=" * 60)
        
        # Carregar configuracao de tempo
        time_config = self.config.get("time_config", {})
        total_hours = time_config.get("total_simulation_hours", 72)
        minutes_per_round = time_config.get("minutes_per_round", 30)
        
        # Calcular total de rodadas
        total_rounds = (total_hours * 60) // minutes_per_round
        
        # Se especificado numero maximo de rodadas, truncar
        if max_rounds is not None and max_rounds > 0:
            original_rounds = total_rounds
            total_rounds = min(total_rounds, max_rounds)
            if total_rounds < original_rounds:
                print(f"\nRodadas truncadas: {original_rounds} -> {total_rounds} (max_rounds={max_rounds})")

        print(f"\nParametros da simulacao:")
        print(f"  - Duracao total da simulacao: {total_hours} horas")
        print(f"  - Tempo por rodada: {minutes_per_round} minutos")
        print(f"  - Total de rodadas: {total_rounds}")
        if max_rounds:
            print(f"  - Limite maximo de rodadas: {max_rounds}")
        print(f"  - Quantidade de Agentes: {len(self.config.get('agent_configs', []))}")
        
        # Criar modelo
        print("\nInicializando modelo LLM...")
        model = self._create_model()
        
        # Carregar grafo de Agentes
        print("Carregando Profile dos Agentes...")
        profile_path = self._get_profile_path()
        if not os.path.exists(profile_path):
            print(f"Erro: arquivo de Profile nao existe: {profile_path}")
            return
        
        self.agent_graph = await generate_twitter_agent_graph(
            profile_path=profile_path,
            model=model,
            available_actions=self.AVAILABLE_ACTIONS,
        )
        
        # Caminho do banco de dados
        db_path = self._get_db_path()
        if os.path.exists(db_path):
            os.remove(db_path)
            print(f"Banco de dados antigo excluido: {db_path}")

        # Criar ambiente
        print("Criando ambiente OASIS...")
        self.env = oasis.make(
            agent_graph=self.agent_graph,
            platform=oasis.DefaultPlatformType.TWITTER,
            database_path=db_path,
            semaphore=80,  # Limite maximo de requisicoes LLM concorrentes para evitar sobrecarga da API
        )
        
        await self.env.reset()
        print("Inicializacao do ambiente concluida\n")
        
        # Inicializar processador IPC
        self.ipc_handler = IPCHandler(self.simulation_dir, self.env, self.agent_graph)
        self.ipc_handler.update_status("running")
        
        # Executar eventos iniciais
        event_config = self.config.get("event_config", {})
        initial_posts = event_config.get("initial_posts", [])
        
        if initial_posts:
            print(f"Executando eventos iniciais ({len(initial_posts)} postagens iniciais)...")
            initial_actions = {}
            for post in initial_posts:
                agent_id = post.get("poster_agent_id", 0)
                content = post.get("content", "")
                try:
                    agent = self.env.agent_graph.get_agent(agent_id)
                    initial_actions[agent] = ManualAction(
                        action_type=ActionType.CREATE_POST,
                        action_args={"content": content}
                    )
                except Exception as e:
                    print(f"  Aviso: nao foi possivel criar postagem inicial para Agente {agent_id}: {e}")
            
            if initial_actions:
                await self.env.step(initial_actions)
                print(f"  {len(initial_actions)} postagens iniciais publicadas")
        
        # Loop principal da simulacao
        print("\nIniciando ciclo de simulacao...")
        start_time = datetime.now()
        
        for round_num in range(total_rounds):
            # Calcular tempo simulado atual
            simulated_minutes = round_num * minutes_per_round
            simulated_hour = (simulated_minutes // 60) % 24
            simulated_day = simulated_minutes // (60 * 24) + 1
            
            # Obter Agentes ativados nesta rodada
            active_agents = self._get_active_agents_for_round(
                self.env, simulated_hour, round_num
            )
            
            if not active_agents:
                continue
            
            # Construir acoes
            actions = {
                agent: LLMAction()
                for _, agent in active_agents
            }
            
            # Executar acoes
            await self.env.step(actions)
            
            # Imprimir progresso
            if (round_num + 1) % 10 == 0 or round_num == 0:
                elapsed = (datetime.now() - start_time).total_seconds()
                progress = (round_num + 1) / total_rounds * 100
                print(f"  [Day {simulated_day}, {simulated_hour:02d}:00] "
                      f"Round {round_num + 1}/{total_rounds} ({progress:.1f}%) "
                      f"- {len(active_agents)} agents active "
                      f"- elapsed: {elapsed:.1f}s")
        
        total_elapsed = (datetime.now() - start_time).total_seconds()
        print(f"\nCiclo de simulacao concluido!")
        print(f"  - Tempo total: {total_elapsed:.1f} segundos")
        print(f"  - Banco de dados: {db_path}")
        
        # Verificar se deve entrar em modo de espera por comandos
        if self.wait_for_commands:
            print("\n" + "=" * 60)
            print("Entrando em modo de espera por comandos - ambiente permanece ativo")
            print("Comandos suportados: interview, batch_interview, close_env")
            print("=" * 60)
            
            self.ipc_handler.update_status("alive")
            
            # Loop de espera por comandos (usando _shutdown_event global)
            try:
                while not _shutdown_event.is_set():
                    should_continue = await self.ipc_handler.process_commands()
                    if not should_continue:
                        break
                    try:
                        await asyncio.wait_for(_shutdown_event.wait(), timeout=0.5)
                        break  # Sinal de saida recebido
                    except asyncio.TimeoutError:
                        pass
            except KeyboardInterrupt:
                print("\nSinal de interrupcao recebido")
            except asyncio.CancelledError:
                print("\nTarefa cancelada")
            except Exception as e:
                print(f"\nErro no processamento de comandos: {e}")
            
            print("\nEncerrando ambiente...")
        
        # Encerrar ambiente
        self.ipc_handler.update_status("stopped")
        await self.env.close()
        
        print("Ambiente encerrado")
        print("=" * 60)


async def main():
    parser = argparse.ArgumentParser(description='Simulacao OASIS Twitter')
    parser.add_argument(
        '--config',
        type=str,
        required=True,
        help='Caminho do arquivo de configuracao (simulation_config.json)'
    )
    parser.add_argument(
        '--max-rounds',
        type=int,
        default=None,
        help='Numero maximo de rodadas de simulacao (opcional, para truncar simulacoes muito longas)'
    )
    parser.add_argument(
        '--no-wait',
        action='store_true',
        default=False,
        help='Encerrar ambiente imediatamente apos simulacao, sem entrar em modo de espera por comandos'
    )
    
    args = parser.parse_args()
    
    # Criar evento de shutdown no inicio da funcao main
    global _shutdown_event
    _shutdown_event = asyncio.Event()
    
    if not os.path.exists(args.config):
        print(f"Erro: arquivo de configuracao nao existe: {args.config}")
        sys.exit(1)
    
    # Inicializar configuracao de logs (nomes fixos, limpar logs antigos)
    simulation_dir = os.path.dirname(args.config) or "."
    setup_oasis_logging(os.path.join(simulation_dir, "log"))
    
    runner = TwitterSimulationRunner(
        config_path=args.config,
        wait_for_commands=not args.no_wait
    )
    await runner.run(max_rounds=args.max_rounds)


def setup_signal_handlers():
    """
    Configurar tratadores de sinais para garantir encerramento correto ao receber SIGTERM/SIGINT
    Dar ao programa oportunidade de limpar recursos normalmente (fechar banco de dados, ambiente, etc.)
    """
    def signal_handler(signum, frame):
        global _cleanup_done
        sig_name = "SIGTERM" if signum == signal.SIGTERM else "SIGINT"
        print(f"\nSinal {sig_name} recebido, encerrando...")
        if not _cleanup_done:
            _cleanup_done = True
            if _shutdown_event:
                _shutdown_event.set()
        else:
            # Forca saida somente ao receber sinal repetidamente
            print("Saida forcada...")
            sys.exit(1)
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)


if __name__ == "__main__":
    setup_signal_handlers()
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nPrograma interrompido")
    except SystemExit:
        pass
    finally:
        print("Processo de simulacao encerrado")
