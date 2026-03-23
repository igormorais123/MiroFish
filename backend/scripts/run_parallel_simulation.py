"""
Script de simulacao OASIS em paralelo para duas plataformas
Executa simultaneamente simulacoes Twitter e Reddit, lendo o mesmo arquivo de configuracao

Funcionalidades:
- Simulacao paralela em duas plataformas (Twitter + Reddit)
- Apos concluir a simulacao, nao encerra o ambiente imediatamente, entra em modo de espera por comandos
- Suporta recebimento de comandos de Interview via IPC
- Suporta entrevista individual e em lote de Agentes
- Suporta comando remoto de encerramento do ambiente

Modo de uso:
    python run_parallel_simulation.py --config simulation_config.json
    python run_parallel_simulation.py --config simulation_config.json --no-wait  # Encerra imediatamente apos conclusao
    python run_parallel_simulation.py --config simulation_config.json --twitter-only
    python run_parallel_simulation.py --config simulation_config.json --reddit-only

Estrutura de logs:
    sim_xxx/
    ├── twitter/
    │   └── actions.jsonl    # Log de acoes da plataforma Twitter
    ├── reddit/
    │   └── actions.jsonl    # Log de acoes da plataforma Reddit
    ├── simulation.log       # Log do processo principal de simulacao
    └── run_state.json       # Estado de execucao (para consulta via API)
"""

# ============================================================
# Resolver problema de codificacao no Windows: definir UTF-8 antes de todos os imports
# Isso corrige o problema de bibliotecas terceiras do OASIS que nao especificam codificacao ao ler arquivos
# ============================================================
import sys
import os

if sys.platform == 'win32':
    # Definir codificacao I/O padrao do Python como UTF-8
    # Isso afeta todas as chamadas open() que nao especificam codificacao
    os.environ.setdefault('PYTHONUTF8', '1')
    os.environ.setdefault('PYTHONIOENCODING', 'utf-8')
    
    # Reconfigurar fluxos de saida padrao para UTF-8 (resolver caracteres ilegíveis no console)
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    
    # Forcar codificacao padrao (afeta a codificacao padrao da funcao open())
    # Nota: isso precisa ser definido na inicializacao do Python; definir em tempo de execucao pode nao funcionar
    # Por isso tambem fazemos monkey-patch da funcao open embutida
    import builtins
    _original_open = builtins.open
    
    def _utf8_open(file, mode='r', buffering=-1, encoding=None, errors=None, 
                   newline=None, closefd=True, opener=None):
        """
        Wrapper da funcao open() que usa UTF-8 como codificacao padrao para modo texto
        Corrige o problema de bibliotecas terceiras (como OASIS) que nao especificam codificacao ao ler arquivos
        """
        # Definir codificacao padrao apenas para modo texto (nao binario) quando nao especificada
        if encoding is None and 'b' not in mode:
            encoding = 'utf-8'
        return _original_open(file, mode, buffering, encoding, errors, 
                              newline, closefd, opener)
    
    builtins.open = _utf8_open

import argparse
import asyncio
import json
import logging
import multiprocessing
import random
import signal
import sqlite3
import warnings
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple


# Variaveis globais: usadas para tratamento de sinais
_shutdown_event = None
_cleanup_done = False

# Adicionar diretorio backend ao path
# O script esta fixo no diretorio backend/scripts/
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
    print(f"Configuracao de ambiente carregada: {_env_file}")
else:
    # Tentar carregar backend/.env
    _backend_env = os.path.join(_backend_dir, '.env')
    if os.path.exists(_backend_env):
        load_dotenv(_backend_env)
        print(f"Configuracao de ambiente carregada: {_backend_env}")


class MaxTokensWarningFilter(logging.Filter):
    """Filtra avisos do camel-ai sobre max_tokens (nao definimos max_tokens intencionalmente, deixando o modelo decidir)"""

    def filter(self, record):
        # Filtrar logs contendo aviso de max_tokens
        if "max_tokens" in record.getMessage() and "Invalid or missing" in record.getMessage():
            return False
        return True


# Adicionar filtro imediatamente ao carregar o modulo, garantindo que esteja ativo antes da execucao do codigo camel
logging.getLogger().addFilter(MaxTokensWarningFilter())


def disable_oasis_logging():
    """
    Desabilitar saida detalhada de logs da biblioteca OASIS
    Os logs do OASIS sao muito verbosos (registram observacao e acao de cada agente), usamos nosso proprio action_logger
    """
    # Desabilitar todos os loggers do OASIS
    oasis_loggers = [
        "social.agent",
        "social.twitter", 
        "social.rec",
        "oasis.env",
        "table",
    ]
    
    for logger_name in oasis_loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.CRITICAL)  # Registrar apenas erros criticos
        logger.handlers.clear()
        logger.propagate = False


def init_logging_for_simulation(simulation_dir: str):
    """
    Inicializar configuracao de logs da simulacao

    Args:
        simulation_dir: Caminho do diretorio da simulacao
    """
    # Desabilitar logs detalhados do OASIS
    disable_oasis_logging()
    
    # Limpar diretorio de log antigo (se existir)
    old_log_dir = os.path.join(simulation_dir, "log")
    if os.path.exists(old_log_dir):
        import shutil
        shutil.rmtree(old_log_dir, ignore_errors=True)


from action_logger import SimulationLogManager, PlatformActionLogger

try:
    from camel.models import ModelFactory
    from camel.types import ModelPlatformType
    import oasis
    from oasis import (
        ActionType,
        LLMAction,
        ManualAction,
        generate_twitter_agent_graph,
        generate_reddit_agent_graph
    )
except ImportError as e:
    print(f"Erro: dependencia ausente {e}")
    print("Instale primeiro: pip install oasis-ai camel-ai")
    sys.exit(1)


# Acoes disponiveis no Twitter (nao inclui INTERVIEW, que so pode ser acionado manualmente via ManualAction)
TWITTER_ACTIONS = [
    ActionType.CREATE_POST,
    ActionType.LIKE_POST,
    ActionType.REPOST,
    ActionType.FOLLOW,
    ActionType.DO_NOTHING,
    ActionType.QUOTE_POST,
]

# Acoes disponiveis no Reddit (nao inclui INTERVIEW, que so pode ser acionado manualmente via ManualAction)
REDDIT_ACTIONS = [
    ActionType.LIKE_POST,
    ActionType.DISLIKE_POST,
    ActionType.CREATE_POST,
    ActionType.CREATE_COMMENT,
    ActionType.LIKE_COMMENT,
    ActionType.DISLIKE_COMMENT,
    ActionType.SEARCH_POSTS,
    ActionType.SEARCH_USER,
    ActionType.TREND,
    ActionType.REFRESH,
    ActionType.DO_NOTHING,
    ActionType.FOLLOW,
    ActionType.MUTE,
]


# Constantes relacionadas ao IPC
IPC_COMMANDS_DIR = "ipc_commands"
IPC_RESPONSES_DIR = "ipc_responses"
ENV_STATUS_FILE = "env_status.json"

class CommandType:
    """Constantes de tipos de comando"""
    INTERVIEW = "interview"
    BATCH_INTERVIEW = "batch_interview"
    CLOSE_ENV = "close_env"


class ParallelIPCHandler:
    """
    Processador de comandos IPC para duas plataformas

    Gerencia os ambientes de duas plataformas, processa comandos de Interview
    """
    
    def __init__(
        self,
        simulation_dir: str,
        twitter_env=None,
        twitter_agent_graph=None,
        reddit_env=None,
        reddit_agent_graph=None
    ):
        self.simulation_dir = simulation_dir
        self.twitter_env = twitter_env
        self.twitter_agent_graph = twitter_agent_graph
        self.reddit_env = reddit_env
        self.reddit_agent_graph = reddit_agent_graph
        
        self.commands_dir = os.path.join(simulation_dir, IPC_COMMANDS_DIR)
        self.responses_dir = os.path.join(simulation_dir, IPC_RESPONSES_DIR)
        self.status_file = os.path.join(simulation_dir, ENV_STATUS_FILE)
        
        # Garantir que os diretorios existam
        os.makedirs(self.commands_dir, exist_ok=True)
        os.makedirs(self.responses_dir, exist_ok=True)
    
    def update_status(self, status: str):
        """Atualizar status do ambiente"""
        with open(self.status_file, 'w', encoding='utf-8') as f:
            json.dump({
                "status": status,
                "twitter_available": self.twitter_env is not None,
                "reddit_available": self.reddit_env is not None,
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
    
    def _get_env_and_graph(self, platform: str):
        """
        Obter o ambiente e agent_graph da plataforma especificada

        Args:
            platform: Nome da plataforma ("twitter" ou "reddit")

        Returns:
            (env, agent_graph, platform_name) ou (None, None, None)
        """
        if platform == "twitter" and self.twitter_env:
            return self.twitter_env, self.twitter_agent_graph, "twitter"
        elif platform == "reddit" and self.reddit_env:
            return self.reddit_env, self.reddit_agent_graph, "reddit"
        else:
            return None, None, None
    
    async def _interview_single_platform(self, agent_id: int, prompt: str, platform: str) -> Dict[str, Any]:
        """
        Executar Interview em uma unica plataforma

        Returns:
            Dicionario com resultado, ou dicionario com erro
        """
        env, agent_graph, actual_platform = self._get_env_and_graph(platform)
        
        if not env or not agent_graph:
            return {"platform": platform, "error": f"Plataforma {platform} indisponivel"}
        
        try:
            agent = agent_graph.get_agent(agent_id)
            interview_action = ManualAction(
                action_type=ActionType.INTERVIEW,
                action_args={"prompt": prompt}
            )
            actions = {agent: interview_action}
            await env.step(actions)
            
            result = self._get_interview_result(agent_id, actual_platform)
            result["platform"] = actual_platform
            return result
            
        except Exception as e:
            return {"platform": platform, "error": str(e)}
    
    async def handle_interview(self, command_id: str, agent_id: int, prompt: str, platform: str = None) -> bool:
        """
        Processar comando de entrevista de um unico Agente

        Args:
            command_id: ID do comando
            agent_id: ID do Agente
            prompt: Pergunta da entrevista
            platform: Plataforma especificada (opcional)
                - "twitter": Entrevistar apenas na plataforma Twitter
                - "reddit": Entrevistar apenas na plataforma Reddit
                - None/nao especificado: Entrevistar em ambas as plataformas, retornar resultado integrado

        Returns:
            True indica sucesso, False indica falha
        """
        # Se uma plataforma foi especificada, entrevistar apenas nela
        if platform in ("twitter", "reddit"):
            result = await self._interview_single_platform(agent_id, prompt, platform)
            
            if "error" in result:
                self.send_response(command_id, "failed", error=result["error"])
                print(f"  Interview falhou: agent_id={agent_id}, platform={platform}, error={result['error']}")
                return False
            else:
                self.send_response(command_id, "completed", result=result)
                print(f"  Interview concluido: agent_id={agent_id}, platform={platform}")
                return True
        
        # Plataforma nao especificada: entrevistar em ambas as plataformas
        if not self.twitter_env and not self.reddit_env:
            self.send_response(command_id, "failed", error="Nenhum ambiente de simulacao disponivel")
            return False
        
        results = {
            "agent_id": agent_id,
            "prompt": prompt,
            "platforms": {}
        }
        success_count = 0
        
        # Entrevistar em ambas as plataformas em paralelo
        tasks = []
        platforms_to_interview = []
        
        if self.twitter_env:
            tasks.append(self._interview_single_platform(agent_id, prompt, "twitter"))
            platforms_to_interview.append("twitter")
        
        if self.reddit_env:
            tasks.append(self._interview_single_platform(agent_id, prompt, "reddit"))
            platforms_to_interview.append("reddit")
        
        # Executar em paralelo
        platform_results = await asyncio.gather(*tasks)
        
        for platform_name, platform_result in zip(platforms_to_interview, platform_results):
            results["platforms"][platform_name] = platform_result
            if "error" not in platform_result:
                success_count += 1
        
        if success_count > 0:
            self.send_response(command_id, "completed", result=results)
            print(f"  Interview concluido: agent_id={agent_id}, plataformas bem-sucedidas={success_count}/{len(platforms_to_interview)}")
            return True
        else:
            errors = [f"{p}: {r.get('error', 'erro desconhecido')}" for p, r in results["platforms"].items()]
            self.send_response(command_id, "failed", error="; ".join(errors))
            print(f"  Interview falhou: agent_id={agent_id}, todas as plataformas falharam")
            return False
    
    async def handle_batch_interview(self, command_id: str, interviews: List[Dict], platform: str = None) -> bool:
        """
        Processar comando de entrevista em lote

        Args:
            command_id: ID do comando
            interviews: [{"agent_id": int, "prompt": str, "platform": str(optional)}, ...]
            platform: Plataforma padrao (pode ser sobrescrita por cada item de entrevista)
                - "twitter": Entrevistar apenas na plataforma Twitter
                - "reddit": Entrevistar apenas na plataforma Reddit
                - None/nao especificado: Entrevistar cada Agente em ambas as plataformas
        """
        # Agrupar por plataforma
        twitter_interviews = []
        reddit_interviews = []
        both_platforms_interviews = []  # Entrevistas que precisam ser feitas em ambas as plataformas
        
        for interview in interviews:
            item_platform = interview.get("platform", platform)
            if item_platform == "twitter":
                twitter_interviews.append(interview)
            elif item_platform == "reddit":
                reddit_interviews.append(interview)
            else:
                # Plataforma nao especificada: entrevistar em ambas
                both_platforms_interviews.append(interview)
        
        # Dividir both_platforms_interviews entre as duas plataformas
        if both_platforms_interviews:
            if self.twitter_env:
                twitter_interviews.extend(both_platforms_interviews)
            if self.reddit_env:
                reddit_interviews.extend(both_platforms_interviews)
        
        results = {}
        
        # Processar entrevistas da plataforma Twitter
        if twitter_interviews and self.twitter_env:
            try:
                twitter_actions = {}
                for interview in twitter_interviews:
                    agent_id = interview.get("agent_id")
                    prompt = interview.get("prompt", "")
                    try:
                        agent = self.twitter_agent_graph.get_agent(agent_id)
                        twitter_actions[agent] = ManualAction(
                            action_type=ActionType.INTERVIEW,
                            action_args={"prompt": prompt}
                        )
                    except Exception as e:
                        print(f"  Aviso: nao foi possivel obter Agente Twitter {agent_id}: {e}")
                
                if twitter_actions:
                    await self.twitter_env.step(twitter_actions)
                    
                    for interview in twitter_interviews:
                        agent_id = interview.get("agent_id")
                        result = self._get_interview_result(agent_id, "twitter")
                        result["platform"] = "twitter"
                        results[f"twitter_{agent_id}"] = result
            except Exception as e:
                print(f"  Interview em lote Twitter falhou: {e}")
        
        # Processar entrevistas da plataforma Reddit
        if reddit_interviews and self.reddit_env:
            try:
                reddit_actions = {}
                for interview in reddit_interviews:
                    agent_id = interview.get("agent_id")
                    prompt = interview.get("prompt", "")
                    try:
                        agent = self.reddit_agent_graph.get_agent(agent_id)
                        reddit_actions[agent] = ManualAction(
                            action_type=ActionType.INTERVIEW,
                            action_args={"prompt": prompt}
                        )
                    except Exception as e:
                        print(f"  Aviso: nao foi possivel obter Agente Reddit {agent_id}: {e}")
                
                if reddit_actions:
                    await self.reddit_env.step(reddit_actions)
                    
                    for interview in reddit_interviews:
                        agent_id = interview.get("agent_id")
                        result = self._get_interview_result(agent_id, "reddit")
                        result["platform"] = "reddit"
                        results[f"reddit_{agent_id}"] = result
            except Exception as e:
                print(f"  Interview em lote Reddit falhou: {e}")
        
        if results:
            self.send_response(command_id, "completed", result={
                "interviews_count": len(results),
                "results": results
            })
            print(f"  Interview em lote concluido: {len(results)} Agentes")
            return True
        else:
            self.send_response(command_id, "failed", error="Nenhuma entrevista bem-sucedida")
            return False
    
    def _get_interview_result(self, agent_id: int, platform: str) -> Dict[str, Any]:
        """Obter o resultado mais recente do Interview do banco de dados"""
        db_path = os.path.join(self.simulation_dir, f"{platform}_simulation.db")
        
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
                args.get("prompt", ""),
                args.get("platform")
            )
            return True
            
        elif command_type == CommandType.BATCH_INTERVIEW:
            await self.handle_batch_interview(
                command_id,
                args.get("interviews", []),
                args.get("platform")
            )
            return True
            
        elif command_type == CommandType.CLOSE_ENV:
            print("Comando de encerrar ambiente recebido")
            self.send_response(command_id, "completed", result={"message": "Ambiente sera encerrado"})
            return False
        
        else:
            self.send_response(command_id, "failed", error=f"Tipo de comando desconhecido: {command_type}")
            return True


def load_config(config_path: str) -> Dict[str, Any]:
    """Carregar arquivo de configuracao"""
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


# Tipos de acao nao essenciais a serem filtrados (essas acoes tem baixo valor analitico)
FILTERED_ACTIONS = {'refresh', 'sign_up'}

# Tabela de mapeamento de tipos de acao (nome no banco de dados -> nome padrao)
ACTION_TYPE_MAP = {
    'create_post': 'CREATE_POST',
    'like_post': 'LIKE_POST',
    'dislike_post': 'DISLIKE_POST',
    'repost': 'REPOST',
    'quote_post': 'QUOTE_POST',
    'follow': 'FOLLOW',
    'mute': 'MUTE',
    'create_comment': 'CREATE_COMMENT',
    'like_comment': 'LIKE_COMMENT',
    'dislike_comment': 'DISLIKE_COMMENT',
    'search_posts': 'SEARCH_POSTS',
    'search_user': 'SEARCH_USER',
    'trend': 'TREND',
    'do_nothing': 'DO_NOTHING',
    'interview': 'INTERVIEW',
}


def get_agent_names_from_config(config: Dict[str, Any]) -> Dict[int, str]:
    """
    Obter mapeamento agent_id -> entity_name do simulation_config

    Assim e possivel exibir o nome real da entidade no actions.jsonl, em vez de codinomes como "Agent_0"

    Args:
        config: Conteudo do simulation_config.json

    Returns:
        Dicionario de mapeamento agent_id -> entity_name
    """
    agent_names = {}
    agent_configs = config.get("agent_configs", [])
    
    for agent_config in agent_configs:
        agent_id = agent_config.get("agent_id")
        entity_name = agent_config.get("entity_name", f"Agent_{agent_id}")
        if agent_id is not None:
            agent_names[agent_id] = entity_name
    
    return agent_names


def fetch_new_actions_from_db(
    db_path: str,
    last_rowid: int,
    agent_names: Dict[int, str]
) -> Tuple[List[Dict[str, Any]], int]:
    """
    Obter novos registros de acoes do banco de dados e complementar com informacoes de contexto completas

    Args:
        db_path: Caminho do arquivo de banco de dados
        last_rowid: Maior valor de rowid da ultima leitura (usa rowid em vez de created_at porque plataformas diferentes tem formatos de created_at diferentes)
        agent_names: Mapeamento agent_id -> agent_name

    Returns:
        (actions_list, new_last_rowid)
        - actions_list: Lista de acoes, cada elemento contem agent_id, agent_name, action_type, action_args (com informacoes de contexto)
        - new_last_rowid: Novo maior valor de rowid
    """
    actions = []
    new_last_rowid = last_rowid
    
    if not os.path.exists(db_path):
        return actions, new_last_rowid
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Usar rowid para rastrear registros ja processados (rowid e campo auto-incremento nativo do SQLite)
        # Isso evita problemas de formato diferente de created_at (Twitter usa inteiros, Reddit usa strings de data/hora)
        cursor.execute("""
            SELECT rowid, user_id, action, info
            FROM trace
            WHERE rowid > ?
            ORDER BY rowid ASC
        """, (last_rowid,))
        
        for rowid, user_id, action, info_json in cursor.fetchall():
            # Atualizar maior rowid
            new_last_rowid = rowid
            
            # Filtrar acoes nao essenciais
            if action in FILTERED_ACTIONS:
                continue
            
            # Analisar parametros da acao
            try:
                action_args = json.loads(info_json) if info_json else {}
            except json.JSONDecodeError:
                action_args = {}
            
            # Simplificar action_args, mantendo apenas campos-chave (conteudo completo, sem truncar)
            simplified_args = {}
            if 'content' in action_args:
                simplified_args['content'] = action_args['content']
            if 'post_id' in action_args:
                simplified_args['post_id'] = action_args['post_id']
            if 'comment_id' in action_args:
                simplified_args['comment_id'] = action_args['comment_id']
            if 'quoted_id' in action_args:
                simplified_args['quoted_id'] = action_args['quoted_id']
            if 'new_post_id' in action_args:
                simplified_args['new_post_id'] = action_args['new_post_id']
            if 'follow_id' in action_args:
                simplified_args['follow_id'] = action_args['follow_id']
            if 'query' in action_args:
                simplified_args['query'] = action_args['query']
            if 'like_id' in action_args:
                simplified_args['like_id'] = action_args['like_id']
            if 'dislike_id' in action_args:
                simplified_args['dislike_id'] = action_args['dislike_id']
            
            # Converter nome do tipo de acao
            action_type = ACTION_TYPE_MAP.get(action, action.upper())
            
            # Complementar informacoes de contexto (conteudo de postagem, nome de usuario, etc.)
            _enrich_action_context(cursor, action_type, simplified_args, agent_names)
            
            actions.append({
                'agent_id': user_id,
                'agent_name': agent_names.get(user_id, f'Agent_{user_id}'),
                'action_type': action_type,
                'action_args': simplified_args,
            })
        
        conn.close()
    except Exception as e:
        print(f"Falha ao ler acoes do banco de dados: {e}")
    
    return actions, new_last_rowid


def _enrich_action_context(
    cursor,
    action_type: str,
    action_args: Dict[str, Any],
    agent_names: Dict[int, str]
) -> None:
    """
    Complementar informacoes de contexto para a acao (conteudo de postagem, nome de usuario, etc.)

    Args:
        cursor: Cursor do banco de dados
        action_type: Tipo de acao
        action_args: Parametros da acao (sera modificado)
        agent_names: Mapeamento agent_id -> agent_name
    """
    try:
        # Curtir/descurtir postagem: complementar conteudo e autor da postagem
        if action_type in ('LIKE_POST', 'DISLIKE_POST'):
            post_id = action_args.get('post_id')
            if post_id:
                post_info = _get_post_info(cursor, post_id, agent_names)
                if post_info:
                    action_args['post_content'] = post_info.get('content', '')
                    action_args['post_author_name'] = post_info.get('author_name', '')
        
        # Repostagem: complementar conteudo e autor do post original
        elif action_type == 'REPOST':
            new_post_id = action_args.get('new_post_id')
            if new_post_id:
                # O original_post_id da repostagem aponta para o post original
                cursor.execute("""
                    SELECT original_post_id FROM post WHERE post_id = ?
                """, (new_post_id,))
                row = cursor.fetchone()
                if row and row[0]:
                    original_post_id = row[0]
                    original_info = _get_post_info(cursor, original_post_id, agent_names)
                    if original_info:
                        action_args['original_content'] = original_info.get('content', '')
                        action_args['original_author_name'] = original_info.get('author_name', '')
        
        # Citacao de postagem: complementar conteudo do post original, autor e comentario de citacao
        elif action_type == 'QUOTE_POST':
            quoted_id = action_args.get('quoted_id')
            new_post_id = action_args.get('new_post_id')
            
            if quoted_id:
                original_info = _get_post_info(cursor, quoted_id, agent_names)
                if original_info:
                    action_args['original_content'] = original_info.get('content', '')
                    action_args['original_author_name'] = original_info.get('author_name', '')
            
            # Obter o conteudo do comentario de citacao (quote_content)
            if new_post_id:
                cursor.execute("""
                    SELECT quote_content FROM post WHERE post_id = ?
                """, (new_post_id,))
                row = cursor.fetchone()
                if row and row[0]:
                    action_args['quote_content'] = row[0]
        
        # Seguir usuario: complementar nome do usuario seguido
        elif action_type == 'FOLLOW':
            follow_id = action_args.get('follow_id')
            if follow_id:
                # Obter followee_id da tabela follow
                cursor.execute("""
                    SELECT followee_id FROM follow WHERE follow_id = ?
                """, (follow_id,))
                row = cursor.fetchone()
                if row:
                    followee_id = row[0]
                    target_name = _get_user_name(cursor, followee_id, agent_names)
                    if target_name:
                        action_args['target_user_name'] = target_name
        
        # Silenciar usuario: complementar nome do usuario silenciado
        elif action_type == 'MUTE':
            # Obter user_id ou target_id do action_args
            target_id = action_args.get('user_id') or action_args.get('target_id')
            if target_id:
                target_name = _get_user_name(cursor, target_id, agent_names)
                if target_name:
                    action_args['target_user_name'] = target_name
        
        # Curtir/descurtir comentario: complementar conteudo e autor do comentario
        elif action_type in ('LIKE_COMMENT', 'DISLIKE_COMMENT'):
            comment_id = action_args.get('comment_id')
            if comment_id:
                comment_info = _get_comment_info(cursor, comment_id, agent_names)
                if comment_info:
                    action_args['comment_content'] = comment_info.get('content', '')
                    action_args['comment_author_name'] = comment_info.get('author_name', '')
        
        # Criar comentario: complementar informacoes da postagem comentada
        elif action_type == 'CREATE_COMMENT':
            post_id = action_args.get('post_id')
            if post_id:
                post_info = _get_post_info(cursor, post_id, agent_names)
                if post_info:
                    action_args['post_content'] = post_info.get('content', '')
                    action_args['post_author_name'] = post_info.get('author_name', '')
    
    except Exception as e:
        # Falha ao complementar contexto nao afeta o fluxo principal
        print(f"Falha ao complementar contexto da acao: {e}")


def _get_post_info(
    cursor,
    post_id: int,
    agent_names: Dict[int, str]
) -> Optional[Dict[str, str]]:
    """
    Obter informacoes da postagem

    Args:
        cursor: Cursor do banco de dados
        post_id: ID da postagem
        agent_names: Mapeamento agent_id -> agent_name

    Returns:
        Dicionario com content e author_name, ou None
    """
    try:
        cursor.execute("""
            SELECT p.content, p.user_id, u.agent_id
            FROM post p
            LEFT JOIN user u ON p.user_id = u.user_id
            WHERE p.post_id = ?
        """, (post_id,))
        row = cursor.fetchone()
        if row:
            content = row[0] or ''
            user_id = row[1]
            agent_id = row[2]
            
            # Priorizar nome de agent_names
            author_name = ''
            if agent_id is not None and agent_id in agent_names:
                author_name = agent_names[agent_id]
            elif user_id:
                # Obter nome da tabela user
                cursor.execute("SELECT name, user_name FROM user WHERE user_id = ?", (user_id,))
                user_row = cursor.fetchone()
                if user_row:
                    author_name = user_row[0] or user_row[1] or ''

            return {'content': content, 'author_name': author_name}
    except Exception:
        pass
    return None


def _get_user_name(
    cursor,
    user_id: int,
    agent_names: Dict[int, str]
) -> Optional[str]:
    """
    Obter nome do usuario

    Args:
        cursor: Cursor do banco de dados
        user_id: ID do usuario
        agent_names: Mapeamento agent_id -> agent_name

    Returns:
        Nome do usuario, ou None
    """
    try:
        cursor.execute("""
            SELECT agent_id, name, user_name FROM user WHERE user_id = ?
        """, (user_id,))
        row = cursor.fetchone()
        if row:
            agent_id = row[0]
            name = row[1]
            user_name = row[2]
            
            # Priorizar nome de agent_names
            if agent_id is not None and agent_id in agent_names:
                return agent_names[agent_id]
            return name or user_name or ''
    except Exception:
        pass
    return None


def _get_comment_info(
    cursor,
    comment_id: int,
    agent_names: Dict[int, str]
) -> Optional[Dict[str, str]]:
    """
    Obter informacoes do comentario

    Args:
        cursor: Cursor do banco de dados
        comment_id: ID do comentario
        agent_names: Mapeamento agent_id -> agent_name

    Returns:
        Dicionario com content e author_name, ou None
    """
    try:
        cursor.execute("""
            SELECT c.content, c.user_id, u.agent_id
            FROM comment c
            LEFT JOIN user u ON c.user_id = u.user_id
            WHERE c.comment_id = ?
        """, (comment_id,))
        row = cursor.fetchone()
        if row:
            content = row[0] or ''
            user_id = row[1]
            agent_id = row[2]
            
            # Priorizar nome de agent_names
            author_name = ''
            if agent_id is not None and agent_id in agent_names:
                author_name = agent_names[agent_id]
            elif user_id:
                # Obter nome da tabela user
                cursor.execute("SELECT name, user_name FROM user WHERE user_id = ?", (user_id,))
                user_row = cursor.fetchone()
                if user_row:
                    author_name = user_row[0] or user_row[1] or ''

            return {'content': content, 'author_name': author_name}
    except Exception:
        pass
    return None


def create_model(config: Dict[str, Any], use_boost: bool = False):
    """
    Criar modelo LLM

    Suporta configuracao dupla de LLM para acelerar simulacoes paralelas:
    - Configuracao geral: LLM_API_KEY, LLM_BASE_URL, LLM_MODEL_NAME
    - Configuracao de aceleracao (opcional): LLM_BOOST_API_KEY, LLM_BOOST_BASE_URL, LLM_BOOST_MODEL_NAME

    Se o LLM de aceleracao estiver configurado, plataformas diferentes podem usar provedores de API diferentes na simulacao paralela, aumentando a capacidade de concorrencia.

    Args:
        config: Dicionario de configuracao da simulacao
        use_boost: Se deve usar a configuracao de LLM acelerado (se disponivel)
    """
    # Verificar se ha configuracao de aceleracao
    boost_api_key = os.environ.get("LLM_BOOST_API_KEY", "")
    boost_base_url = os.environ.get("LLM_BOOST_BASE_URL", "")
    boost_model = os.environ.get("LLM_BOOST_MODEL_NAME", "")
    has_boost_config = bool(boost_api_key)
    
    # Selecionar qual LLM usar com base nos parametros e configuracao
    if use_boost and has_boost_config:
        # Usar configuracao de aceleracao
        llm_api_key = boost_api_key
        llm_base_url = boost_base_url
        llm_model = boost_model or os.environ.get("LLM_MODEL_NAME", "")
        config_label = "[LLM Acelerado]"
    else:
        # Usar configuracao geral
        llm_api_key = os.environ.get("LLM_API_KEY", "")
        llm_base_url = os.environ.get("LLM_BASE_URL", "")
        llm_model = os.environ.get("LLM_MODEL_NAME", "")
        config_label = "[LLM Geral]"
    
    # Se nao houver nome de modelo no .env, usar config como fallback
    if not llm_model:
        llm_model = config.get("llm_model", "gpt-4o-mini")
    
    # Configurar variaveis de ambiente necessarias para o camel-ai
    if llm_api_key:
        os.environ["OPENAI_API_KEY"] = llm_api_key
    
    if not os.environ.get("OPENAI_API_KEY"):
        raise ValueError("Configuracao de API Key ausente. Defina LLM_API_KEY no arquivo .env do diretorio raiz do projeto")
    
    if llm_base_url:
        os.environ["OPENAI_API_BASE_URL"] = llm_base_url
    
    print(f"{config_label} model={llm_model}, base_url={llm_base_url[:40] if llm_base_url else 'padrao'}...")
    
    return ModelFactory.create(
        model_platform=ModelPlatformType.OPENAI,
        model_type=llm_model,
    )


def get_active_agents_for_round(
    env,
    config: Dict[str, Any],
    current_hour: int,
    round_num: int
) -> List:
    """Decidir quais Agentes ativar nesta rodada com base no horario e configuracao"""
    time_config = config.get("time_config", {})
    agent_configs = config.get("agent_configs", [])
    
    base_min = time_config.get("agents_per_hour_min", 5)
    base_max = time_config.get("agents_per_hour_max", 20)
    
    peak_hours = time_config.get("peak_hours", [9, 10, 11, 14, 15, 20, 21, 22])
    off_peak_hours = time_config.get("off_peak_hours", [0, 1, 2, 3, 4, 5])
    
    if current_hour in peak_hours:
        multiplier = time_config.get("peak_activity_multiplier", 1.5)
    elif current_hour in off_peak_hours:
        multiplier = time_config.get("off_peak_activity_multiplier", 0.3)
    else:
        multiplier = 1.0
    
    target_count = int(random.uniform(base_min, base_max) * multiplier)
    
    candidates = []
    for cfg in agent_configs:
        agent_id = cfg.get("agent_id", 0)
        active_hours = cfg.get("active_hours", list(range(8, 23)))
        activity_level = cfg.get("activity_level", 0.5)
        
        if current_hour not in active_hours:
            continue
        
        if random.random() < activity_level:
            candidates.append(agent_id)
    
    selected_ids = random.sample(
        candidates, 
        min(target_count, len(candidates))
    ) if candidates else []
    
    active_agents = []
    for agent_id in selected_ids:
        try:
            agent = env.agent_graph.get_agent(agent_id)
            active_agents.append((agent_id, agent))
        except Exception:
            pass
    
    return active_agents


class PlatformSimulation:
    """Container de resultado da simulacao de plataforma"""
    def __init__(self):
        self.env = None
        self.agent_graph = None
        self.total_actions = 0


async def run_twitter_simulation(
    config: Dict[str, Any], 
    simulation_dir: str,
    action_logger: Optional[PlatformActionLogger] = None,
    main_logger: Optional[SimulationLogManager] = None,
    max_rounds: Optional[int] = None
) -> PlatformSimulation:
    """Executar simulacao Twitter

    Args:
        config: Configuracao da simulacao
        simulation_dir: Diretorio da simulacao
        action_logger: Registrador de log de acoes
        main_logger: Gerenciador de log principal
        max_rounds: Numero maximo de rodadas (opcional, para truncar simulacoes muito longas)

    Returns:
        PlatformSimulation: Objeto de resultado contendo env e agent_graph
    """
    result = PlatformSimulation()
    
    def log_info(msg):
        if main_logger:
            main_logger.info(f"[Twitter] {msg}")
        print(f"[Twitter] {msg}")
    
    log_info("Inicializando...")

    # Twitter usa configuracao LLM geral
    model = create_model(config, use_boost=False)
    
    # OASIS Twitter usa formato CSV
    profile_path = os.path.join(simulation_dir, "twitter_profiles.csv")
    if not os.path.exists(profile_path):
        log_info(f"Erro: arquivo de Profile nao existe: {profile_path}")
        return result
    
    result.agent_graph = await generate_twitter_agent_graph(
        profile_path=profile_path,
        model=model,
        available_actions=TWITTER_ACTIONS,
    )
    
    # Obter mapeamento de nomes reais dos Agentes do arquivo de configuracao (usando entity_name em vez do padrao Agent_X)
    agent_names = get_agent_names_from_config(config)
    # Se algum agente nao estiver na configuracao, usar o nome padrao do OASIS
    for agent_id, agent in result.agent_graph.get_agents():
        if agent_id not in agent_names:
            agent_names[agent_id] = getattr(agent, 'name', f'Agent_{agent_id}')

    db_path = os.path.join(simulation_dir, "twitter_simulation.db")
    if os.path.exists(db_path):
        os.remove(db_path)

    result.env = oasis.make(
        agent_graph=result.agent_graph,
        platform=oasis.DefaultPlatformType.TWITTER,
        database_path=db_path,
        semaphore=30,  # Limite maximo de requisicoes LLM concorrentes para evitar sobrecarga da API
    )
    
    await result.env.reset()
    log_info("Ambiente iniciado")
    
    if action_logger:
        action_logger.log_simulation_start(config)
    
    total_actions = 0
    last_rowid = 0  # Rastrear ultima linha processada no banco de dados (usar rowid para evitar diferenca de formato de created_at)
    
    # Executar eventos iniciais
    event_config = config.get("event_config", {})
    initial_posts = event_config.get("initial_posts", [])
    
    # Registrar inicio da rodada 0 (fase de eventos iniciais)
    if action_logger:
        action_logger.log_round_start(0, 0)  # round 0, simulated_hour 0
    
    initial_action_count = 0
    if initial_posts:
        initial_actions = {}
        for post in initial_posts:
            agent_id = post.get("poster_agent_id", 0)
            content = post.get("content", "")
            try:
                agent = result.env.agent_graph.get_agent(agent_id)
                initial_actions[agent] = ManualAction(
                    action_type=ActionType.CREATE_POST,
                    action_args={"content": content}
                )
                
                if action_logger:
                    action_logger.log_action(
                        round_num=0,
                        agent_id=agent_id,
                        agent_name=agent_names.get(agent_id, f"Agent_{agent_id}"),
                        action_type="CREATE_POST",
                        action_args={"content": content}
                    )
                    total_actions += 1
                    initial_action_count += 1
            except Exception:
                pass
        
        if initial_actions:
            await result.env.step(initial_actions)
            log_info(f"{len(initial_actions)} postagens iniciais publicadas")
    
    # Registrar fim da rodada 0
    if action_logger:
        action_logger.log_round_end(0, initial_action_count)
    
    # Loop principal da simulacao
    time_config = config.get("time_config", {})
    total_hours = time_config.get("total_simulation_hours", 72)
    minutes_per_round = time_config.get("minutes_per_round", 30)
    total_rounds = (total_hours * 60) // minutes_per_round
    
    # Se especificado numero maximo de rodadas, truncar
    if max_rounds is not None and max_rounds > 0:
        original_rounds = total_rounds
        total_rounds = min(total_rounds, max_rounds)
        if total_rounds < original_rounds:
            log_info(f"Rodadas truncadas: {original_rounds} -> {total_rounds} (max_rounds={max_rounds})")
    
    start_time = datetime.now()
    
    for round_num in range(total_rounds):
        # Verificar se recebeu sinal de saida
        if _shutdown_event and _shutdown_event.is_set():
            if main_logger:
                main_logger.info(f"Sinal de saida recebido, parando simulacao na rodada {round_num + 1}")
            break
        
        simulated_minutes = round_num * minutes_per_round
        simulated_hour = (simulated_minutes // 60) % 24
        simulated_day = simulated_minutes // (60 * 24) + 1
        
        active_agents = get_active_agents_for_round(
            result.env, config, simulated_hour, round_num
        )
        
        # Registrar inicio da rodada independente de haver agentes ativos
        if action_logger:
            action_logger.log_round_start(round_num + 1, simulated_hour)
        
        if not active_agents:
            # Registrar fim da rodada mesmo sem agentes ativos (actions_count=0)
            if action_logger:
                action_logger.log_round_end(round_num + 1, 0)
            continue
        
        actions = {agent: LLMAction() for _, agent in active_agents}
        await result.env.step(actions)
        
        # Obter acoes efetivamente executadas do banco de dados e registrar
        actual_actions, last_rowid = fetch_new_actions_from_db(
            db_path, last_rowid, agent_names
        )
        
        round_action_count = 0
        for action_data in actual_actions:
            if action_logger:
                action_logger.log_action(
                    round_num=round_num + 1,
                    agent_id=action_data['agent_id'],
                    agent_name=action_data['agent_name'],
                    action_type=action_data['action_type'],
                    action_args=action_data['action_args']
                )
                total_actions += 1
                round_action_count += 1
        
        if action_logger:
            action_logger.log_round_end(round_num + 1, round_action_count)
        
        if (round_num + 1) % 20 == 0:
            progress = (round_num + 1) / total_rounds * 100
            log_info(f"Day {simulated_day}, {simulated_hour:02d}:00 - Round {round_num + 1}/{total_rounds} ({progress:.1f}%)")
    
    # Nota: nao encerrar o ambiente, manter disponivel para Interview
    
    if action_logger:
        action_logger.log_simulation_end(total_rounds, total_actions)
    
    result.total_actions = total_actions
    elapsed = (datetime.now() - start_time).total_seconds()
    log_info(f"Ciclo de simulacao concluido! Tempo: {elapsed:.1f}s, total de acoes: {total_actions}")
    
    return result


async def run_reddit_simulation(
    config: Dict[str, Any], 
    simulation_dir: str,
    action_logger: Optional[PlatformActionLogger] = None,
    main_logger: Optional[SimulationLogManager] = None,
    max_rounds: Optional[int] = None
) -> PlatformSimulation:
    """Executar simulacao Reddit

    Args:
        config: Configuracao da simulacao
        simulation_dir: Diretorio da simulacao
        action_logger: Registrador de log de acoes
        main_logger: Gerenciador de log principal
        max_rounds: Numero maximo de rodadas (opcional, para truncar simulacoes muito longas)

    Returns:
        PlatformSimulation: Objeto de resultado contendo env e agent_graph
    """
    result = PlatformSimulation()
    
    def log_info(msg):
        if main_logger:
            main_logger.info(f"[Reddit] {msg}")
        print(f"[Reddit] {msg}")
    
    log_info("Inicializando...")
    
    # Reddit usa configuracao LLM acelerada (se disponivel, senao usa configuracao geral)
    model = create_model(config, use_boost=True)
    
    profile_path = os.path.join(simulation_dir, "reddit_profiles.json")
    if not os.path.exists(profile_path):
        log_info(f"Erro: arquivo de Profile nao existe: {profile_path}")
        return result

    result.agent_graph = await generate_reddit_agent_graph(
        profile_path=profile_path,
        model=model,
        available_actions=REDDIT_ACTIONS,
    )
    
    # Obter mapeamento de nomes reais dos Agentes do arquivo de configuracao (usando entity_name em vez do padrao Agent_X)
    agent_names = get_agent_names_from_config(config)
    # Se algum agente nao estiver na configuracao, usar o nome padrao do OASIS
    for agent_id, agent in result.agent_graph.get_agents():
        if agent_id not in agent_names:
            agent_names[agent_id] = getattr(agent, 'name', f'Agent_{agent_id}')

    db_path = os.path.join(simulation_dir, "reddit_simulation.db")
    if os.path.exists(db_path):
        os.remove(db_path)
    
    result.env = oasis.make(
        agent_graph=result.agent_graph,
        platform=oasis.DefaultPlatformType.REDDIT,
        database_path=db_path,
        semaphore=30,  # Limite maximo de requisicoes LLM concorrentes para evitar sobrecarga da API
    )
    
    await result.env.reset()
    log_info("Ambiente iniciado")
    
    if action_logger:
        action_logger.log_simulation_start(config)
    
    total_actions = 0
    last_rowid = 0  # Rastrear ultima linha processada no banco de dados (usar rowid para evitar diferenca de formato de created_at)
    
    # Executar eventos iniciais
    event_config = config.get("event_config", {})
    initial_posts = event_config.get("initial_posts", [])
    
    # Registrar inicio da rodada 0 (fase de eventos iniciais)
    if action_logger:
        action_logger.log_round_start(0, 0)  # round 0, simulated_hour 0
    
    initial_action_count = 0
    if initial_posts:
        initial_actions = {}
        for post in initial_posts:
            agent_id = post.get("poster_agent_id", 0)
            content = post.get("content", "")
            try:
                agent = result.env.agent_graph.get_agent(agent_id)
                if agent in initial_actions:
                    if not isinstance(initial_actions[agent], list):
                        initial_actions[agent] = [initial_actions[agent]]
                    initial_actions[agent].append(ManualAction(
                        action_type=ActionType.CREATE_POST,
                        action_args={"content": content}
                    ))
                else:
                    initial_actions[agent] = ManualAction(
                        action_type=ActionType.CREATE_POST,
                        action_args={"content": content}
                    )
                
                if action_logger:
                    action_logger.log_action(
                        round_num=0,
                        agent_id=agent_id,
                        agent_name=agent_names.get(agent_id, f"Agent_{agent_id}"),
                        action_type="CREATE_POST",
                        action_args={"content": content}
                    )
                    total_actions += 1
                    initial_action_count += 1
            except Exception:
                pass
        
        if initial_actions:
            await result.env.step(initial_actions)
            log_info(f"{len(initial_actions)} postagens iniciais publicadas")
    
    # Registrar fim da rodada 0
    if action_logger:
        action_logger.log_round_end(0, initial_action_count)
    
    # Loop principal da simulacao
    time_config = config.get("time_config", {})
    total_hours = time_config.get("total_simulation_hours", 72)
    minutes_per_round = time_config.get("minutes_per_round", 30)
    total_rounds = (total_hours * 60) // minutes_per_round
    
    # Se especificado numero maximo de rodadas, truncar
    if max_rounds is not None and max_rounds > 0:
        original_rounds = total_rounds
        total_rounds = min(total_rounds, max_rounds)
        if total_rounds < original_rounds:
            log_info(f"Rodadas truncadas: {original_rounds} -> {total_rounds} (max_rounds={max_rounds})")
    
    start_time = datetime.now()
    
    for round_num in range(total_rounds):
        # Verificar se recebeu sinal de saida
        if _shutdown_event and _shutdown_event.is_set():
            if main_logger:
                main_logger.info(f"Sinal de saida recebido, parando simulacao na rodada {round_num + 1}")
            break
        
        simulated_minutes = round_num * minutes_per_round
        simulated_hour = (simulated_minutes // 60) % 24
        simulated_day = simulated_minutes // (60 * 24) + 1
        
        active_agents = get_active_agents_for_round(
            result.env, config, simulated_hour, round_num
        )
        
        # Registrar inicio da rodada independente de haver agentes ativos
        if action_logger:
            action_logger.log_round_start(round_num + 1, simulated_hour)
        
        if not active_agents:
            # Registrar fim da rodada mesmo sem agentes ativos (actions_count=0)
            if action_logger:
                action_logger.log_round_end(round_num + 1, 0)
            continue
        
        actions = {agent: LLMAction() for _, agent in active_agents}
        await result.env.step(actions)
        
        # Obter acoes efetivamente executadas do banco de dados e registrar
        actual_actions, last_rowid = fetch_new_actions_from_db(
            db_path, last_rowid, agent_names
        )
        
        round_action_count = 0
        for action_data in actual_actions:
            if action_logger:
                action_logger.log_action(
                    round_num=round_num + 1,
                    agent_id=action_data['agent_id'],
                    agent_name=action_data['agent_name'],
                    action_type=action_data['action_type'],
                    action_args=action_data['action_args']
                )
                total_actions += 1
                round_action_count += 1
        
        if action_logger:
            action_logger.log_round_end(round_num + 1, round_action_count)
        
        if (round_num + 1) % 20 == 0:
            progress = (round_num + 1) / total_rounds * 100
            log_info(f"Day {simulated_day}, {simulated_hour:02d}:00 - Round {round_num + 1}/{total_rounds} ({progress:.1f}%)")
    
    # Nota: nao encerrar o ambiente, manter disponivel para Interview
    
    if action_logger:
        action_logger.log_simulation_end(total_rounds, total_actions)
    
    result.total_actions = total_actions
    elapsed = (datetime.now() - start_time).total_seconds()
    log_info(f"Ciclo de simulacao concluido! Tempo: {elapsed:.1f}s, total de acoes: {total_actions}")
    
    return result


async def main():
    parser = argparse.ArgumentParser(description='Simulacao OASIS paralela em duas plataformas')
    parser.add_argument(
        '--config',
        type=str,
        required=True,
        help='Caminho do arquivo de configuracao (simulation_config.json)'
    )
    parser.add_argument(
        '--twitter-only',
        action='store_true',
        help='Executar apenas simulacao Twitter'
    )
    parser.add_argument(
        '--reddit-only',
        action='store_true',
        help='Executar apenas simulacao Reddit'
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
    
    # Criar evento de shutdown no inicio da funcao main para garantir que todo o programa possa responder a sinais de saida
    global _shutdown_event
    _shutdown_event = asyncio.Event()
    
    if not os.path.exists(args.config):
        print(f"Erro: arquivo de configuracao nao existe: {args.config}")
        sys.exit(1)
    
    config = load_config(args.config)
    simulation_dir = os.path.dirname(args.config) or "."
    wait_for_commands = not args.no_wait
    
    # Inicializar configuracao de logs (desabilitar logs OASIS, limpar arquivos antigos)
    init_logging_for_simulation(simulation_dir)
    
    # Criar gerenciador de logs
    log_manager = SimulationLogManager(simulation_dir)
    twitter_logger = log_manager.get_twitter_logger()
    reddit_logger = log_manager.get_reddit_logger()
    
    log_manager.info("=" * 60)
    log_manager.info("Simulacao OASIS paralela em duas plataformas")
    log_manager.info(f"Arquivo de configuracao: {args.config}")
    log_manager.info(f"ID da simulacao: {config.get('simulation_id', 'unknown')}")
    log_manager.info(f"Modo espera por comandos: {'ativado' if wait_for_commands else 'desativado'}")
    log_manager.info("=" * 60)
    
    time_config = config.get("time_config", {})
    total_hours = time_config.get('total_simulation_hours', 72)
    minutes_per_round = time_config.get('minutes_per_round', 30)
    config_total_rounds = (total_hours * 60) // minutes_per_round
    
    log_manager.info(f"Parametros da simulacao:")
    log_manager.info(f"  - Duracao total da simulacao: {total_hours} horas")
    log_manager.info(f"  - Tempo por rodada: {minutes_per_round} minutos")
    log_manager.info(f"  - Total de rodadas configurado: {config_total_rounds}")
    if args.max_rounds:
        log_manager.info(f"  - Limite maximo de rodadas: {args.max_rounds}")
        if args.max_rounds < config_total_rounds:
            log_manager.info(f"  - Rodadas efetivas: {args.max_rounds} (truncado)")
    log_manager.info(f"  - Quantidade de Agentes: {len(config.get('agent_configs', []))}")
    
    log_manager.info("Estrutura de logs:")
    log_manager.info(f"  - Log principal: simulation.log")
    log_manager.info(f"  - Acoes Twitter: twitter/actions.jsonl")
    log_manager.info(f"  - Acoes Reddit: reddit/actions.jsonl")
    log_manager.info("=" * 60)
    
    start_time = datetime.now()
    
    # Armazenar resultados de simulacao das duas plataformas
    twitter_result: Optional[PlatformSimulation] = None
    reddit_result: Optional[PlatformSimulation] = None
    
    if args.twitter_only:
        twitter_result = await run_twitter_simulation(config, simulation_dir, twitter_logger, log_manager, args.max_rounds)
    elif args.reddit_only:
        reddit_result = await run_reddit_simulation(config, simulation_dir, reddit_logger, log_manager, args.max_rounds)
    else:
        # Executar em paralelo (cada plataforma usa registrador de log independente)
        results = await asyncio.gather(
            run_twitter_simulation(config, simulation_dir, twitter_logger, log_manager, args.max_rounds),
            run_reddit_simulation(config, simulation_dir, reddit_logger, log_manager, args.max_rounds),
        )
        twitter_result, reddit_result = results
    
    total_elapsed = (datetime.now() - start_time).total_seconds()
    log_manager.info("=" * 60)
    log_manager.info(f"Ciclo de simulacao concluido! Tempo total: {total_elapsed:.1f}s")
    
    # Verificar se deve entrar em modo de espera por comandos
    if wait_for_commands:
        log_manager.info("")
        log_manager.info("=" * 60)
        log_manager.info("Entrando em modo de espera por comandos - ambiente permanece ativo")
        log_manager.info("Comandos suportados: interview, batch_interview, close_env")
        log_manager.info("=" * 60)
        
        # Criar processador IPC
        ipc_handler = ParallelIPCHandler(
            simulation_dir=simulation_dir,
            twitter_env=twitter_result.env if twitter_result else None,
            twitter_agent_graph=twitter_result.agent_graph if twitter_result else None,
            reddit_env=reddit_result.env if reddit_result else None,
            reddit_agent_graph=reddit_result.agent_graph if reddit_result else None
        )
        ipc_handler.update_status("alive")
        
        # Loop de espera por comandos (usando _shutdown_event global)
        try:
            while not _shutdown_event.is_set():
                should_continue = await ipc_handler.process_commands()
                if not should_continue:
                    break
                # Usar wait_for em vez de sleep para poder responder ao shutdown_event
                try:
                    await asyncio.wait_for(_shutdown_event.wait(), timeout=0.5)
                    break  # Sinal de saida recebido
                except asyncio.TimeoutError:
                    pass  # Timeout, continuar loop
        except KeyboardInterrupt:
            print("\nSinal de interrupcao recebido")
        except asyncio.CancelledError:
            print("\nTarefa cancelada")
        except Exception as e:
            print(f"\nErro no processamento de comandos: {e}")
        
        log_manager.info("\nEncerrando ambiente...")
        ipc_handler.update_status("stopped")
    
    # Encerrar ambientes
    if twitter_result and twitter_result.env:
        await twitter_result.env.close()
        log_manager.info("[Twitter] Ambiente encerrado")
    
    if reddit_result and reddit_result.env:
        await reddit_result.env.close()
        log_manager.info("[Reddit] Ambiente encerrado")
    
    log_manager.info("=" * 60)
    log_manager.info(f"Tudo concluido!")
    log_manager.info(f"Arquivos de log:")
    log_manager.info(f"  - {os.path.join(simulation_dir, 'simulation.log')}")
    log_manager.info(f"  - {os.path.join(simulation_dir, 'twitter', 'actions.jsonl')}")
    log_manager.info(f"  - {os.path.join(simulation_dir, 'reddit', 'actions.jsonl')}")
    log_manager.info("=" * 60)


def setup_signal_handlers(loop=None):
    """
    Configurar tratadores de sinais para garantir encerramento correto ao receber SIGTERM/SIGINT

    Cenario de simulacao persistente: apos conclusao da simulacao, nao encerra, aguarda comandos de interview
    Ao receber sinal de terminacao:
    1. Notificar o loop asyncio para sair da espera
    2. Dar ao programa oportunidade de limpar recursos normalmente (fechar banco de dados, ambiente, etc.)
    3. Entao encerrar
    """
    def signal_handler(signum, frame):
        global _cleanup_done
        sig_name = "SIGTERM" if signum == signal.SIGTERM else "SIGINT"
        print(f"\nSinal {sig_name} recebido, encerrando...")
        
        if not _cleanup_done:
            _cleanup_done = True
            # Definir evento para notificar o loop asyncio a encerrar (dar oportunidade de limpar recursos)
            if _shutdown_event:
                _shutdown_event.set()
        
        # Nao chamar sys.exit() diretamente, deixar o loop asyncio encerrar normalmente e limpar recursos
        # Forcar saida somente ao receber sinal repetidamente
        else:
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
        # Limpar rastreador de recursos do multiprocessing (evitar avisos ao encerrar)
        try:
            from multiprocessing import resource_tracker
            resource_tracker._resource_tracker._stop()
        except Exception:
            pass
        print("Processo de simulacao encerrado")
