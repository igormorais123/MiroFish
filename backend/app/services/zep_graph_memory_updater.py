"""
Servico de atualizacao da memoria em grafo do Zep.
Atualiza dinamicamente no grafo as atividades dos agentes durante a simulacao.
"""

import os
import time
import threading
import json
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
from queue import Queue, Empty

from zep_cloud.client import Zep

from ..config import Config
from ..utils.logger import get_logger

logger = get_logger('mirofish.zep_graph_memory_updater')


@dataclass
class AgentActivity:
    """Registro de atividade de um agente."""
    platform: str           # twitter / reddit
    agent_id: int
    agent_name: str
    action_type: str        # CREATE_POST, LIKE_POST, etc.
    action_args: Dict[str, Any]
    round_num: int
    timestamp: str
    
    def to_episode_text(self) -> str:
        """
        Converte a atividade em uma descricao textual adequada para o Zep.
        """
        # Escolhe a descricao conforme o tipo de acao.
        action_descriptions = {
            "CREATE_POST": self._describe_create_post,
            "LIKE_POST": self._describe_like_post,
            "DISLIKE_POST": self._describe_dislike_post,
            "REPOST": self._describe_repost,
            "QUOTE_POST": self._describe_quote_post,
            "FOLLOW": self._describe_follow,
            "CREATE_COMMENT": self._describe_create_comment,
            "LIKE_COMMENT": self._describe_like_comment,
            "DISLIKE_COMMENT": self._describe_dislike_comment,
            "SEARCH_POSTS": self._describe_search,
            "SEARCH_USER": self._describe_search_user,
            "MUTE": self._describe_mute,
        }
        
        describe_func = action_descriptions.get(self.action_type, self._describe_generic)
        description = describe_func()
        
        # Retorna "nome do agente: descricao da atividade".
        return f"{self.agent_name}: {description}"
    
    def _describe_create_post(self) -> str:
        content = self.action_args.get("content", "")
        if content:
            return f"publicou uma postagem: \"{content}\""
        return "publicou uma postagem"
    
    def _describe_like_post(self) -> str:
        """Curtida em postagem, com contexto quando disponivel."""
        post_content = self.action_args.get("post_content", "")
        post_author = self.action_args.get("post_author_name", "")
        
        if post_content and post_author:
            return f"curtiu uma postagem de {post_author}: \"{post_content}\""
        elif post_content:
            return f"curtiu uma postagem: \"{post_content}\""
        elif post_author:
            return f"curtiu uma postagem de {post_author}"
        return "curtiu uma postagem"
    
    def _describe_dislike_post(self) -> str:
        """Reacao negativa a postagem, com contexto quando disponivel."""
        post_content = self.action_args.get("post_content", "")
        post_author = self.action_args.get("post_author_name", "")
        
        if post_content and post_author:
            return f"reagiu negativamente a uma postagem de {post_author}: \"{post_content}\""
        elif post_content:
            return f"reagiu negativamente a uma postagem: \"{post_content}\""
        elif post_author:
            return f"reagiu negativamente a uma postagem de {post_author}"
        return "reagiu negativamente a uma postagem"
    
    def _describe_repost(self) -> str:
        """Compartilhamento de postagem com conteudo e autoria quando possivel."""
        original_content = self.action_args.get("original_content", "")
        original_author = self.action_args.get("original_author_name", "")
        
        if original_content and original_author:
            return f"compartilhou uma postagem de {original_author}: \"{original_content}\""
        elif original_content:
            return f"compartilhou uma postagem: \"{original_content}\""
        elif original_author:
            return f"compartilhou uma postagem de {original_author}"
        return "compartilhou uma postagem"
    
    def _describe_quote_post(self) -> str:
        """Citacao de postagem com comentario adicional."""
        original_content = self.action_args.get("original_content", "")
        original_author = self.action_args.get("original_author_name", "")
        quote_content = self.action_args.get("quote_content", "") or self.action_args.get("content", "")
        
        base = ""
        if original_content and original_author:
            base = f"citou uma postagem de {original_author}: \"{original_content}\""
        elif original_content:
            base = f"citou uma postagem: \"{original_content}\""
        elif original_author:
            base = f"citou uma postagem de {original_author}"
        else:
            base = "citou uma postagem"
        
        if quote_content:
            base += f", comentando: \"{quote_content}\""
        return base
    
    def _describe_follow(self) -> str:
        """Acao de seguir outro usuario."""
        target_user_name = self.action_args.get("target_user_name", "")
        
        if target_user_name:
            return f"passou a seguir o usuario \"{target_user_name}\""
        return "passou a seguir um usuario"
    
    def _describe_create_comment(self) -> str:
        """Comentario publicado, com contexto da postagem quando houver."""
        content = self.action_args.get("content", "")
        post_content = self.action_args.get("post_content", "")
        post_author = self.action_args.get("post_author_name", "")
        
        if content:
            if post_content and post_author:
                return f"comentou na postagem de {post_author} \"{post_content}\": \"{content}\""
            elif post_content:
                return f"comentou na postagem \"{post_content}\": \"{content}\""
            elif post_author:
                return f"comentou em uma postagem de {post_author}: \"{content}\""
            return f"comentou: \"{content}\""
        return "publicou um comentario"
    
    def _describe_like_comment(self) -> str:
        """Curtida em comentario com contexto quando disponivel."""
        comment_content = self.action_args.get("comment_content", "")
        comment_author = self.action_args.get("comment_author_name", "")
        
        if comment_content and comment_author:
            return f"curtiu um comentario de {comment_author}: \"{comment_content}\""
        elif comment_content:
            return f"curtiu um comentario: \"{comment_content}\""
        elif comment_author:
            return f"curtiu um comentario de {comment_author}"
        return "curtiu um comentario"
    
    def _describe_dislike_comment(self) -> str:
        """Reacao negativa a comentario com contexto quando disponivel."""
        comment_content = self.action_args.get("comment_content", "")
        comment_author = self.action_args.get("comment_author_name", "")
        
        if comment_content and comment_author:
            return f"reagiu negativamente a um comentario de {comment_author}: \"{comment_content}\""
        elif comment_content:
            return f"reagiu negativamente a um comentario: \"{comment_content}\""
        elif comment_author:
            return f"reagiu negativamente a um comentario de {comment_author}"
        return "reagiu negativamente a um comentario"
    
    def _describe_search(self) -> str:
        """Busca de postagens."""
        query = self.action_args.get("query", "") or self.action_args.get("keyword", "")
        return f"buscou por \"{query}\"" if query else "realizou uma busca"
    
    def _describe_search_user(self) -> str:
        """Busca de usuarios."""
        query = self.action_args.get("query", "") or self.action_args.get("username", "")
        return f"buscou o usuario \"{query}\"" if query else "buscou um usuario"
    
    def _describe_mute(self) -> str:
        """Silenciamento ou bloqueio de usuario."""
        target_user_name = self.action_args.get("target_user_name", "")
        
        if target_user_name:
            return f"silenciou o usuario \"{target_user_name}\""
        return "silenciou um usuario"
    
    def _describe_generic(self) -> str:
        return f"executou a acao {self.action_type}"


class ZepGraphMemoryUpdater:
    """
    Atualizador de memoria em grafo do Zep.

    Monitora os logs de acoes da simulacao e envia atividades relevantes em
    lote, agrupadas por plataforma.
    """
    
    # Tamanho do lote por plataforma.
    BATCH_SIZE = 5
    
    # Nomes amigaveis para exibicao em log.
    PLATFORM_DISPLAY_NAMES = {
        'twitter': 'Feed aberto',
        'reddit': 'Comunidade',
    }
    
    # Intervalo entre envios.
    SEND_INTERVAL = 0.5
    
    # Politica de retry.
    MAX_RETRIES = 3
    RETRY_DELAY = 2  # segundos
    
    def __init__(self, graph_id: str, api_key: Optional[str] = None):
        """Inicializa o atualizador."""
        self.graph_id = graph_id
        self.api_key = api_key or Config.ZEP_API_KEY
        
        if not self.api_key:
            raise ValueError("ZEP_API_KEY nao configurada")
        
        self.client = Zep(api_key=self.api_key)
        
        # Fila de atividades.
        self._activity_queue: Queue = Queue()
        
        # Buffers por plataforma.
        self._platform_buffers: Dict[str, List[AgentActivity]] = {
            'twitter': [],
            'reddit': [],
        }
        self._buffer_lock = threading.Lock()
        
        # Flags de controle.
        self._running = False
        self._worker_thread: Optional[threading.Thread] = None
        
        # Estatisticas.
        self._total_activities = 0
        self._total_sent = 0
        self._total_items_sent = 0
        self._failed_count = 0
        self._skipped_count = 0
        
        logger.info(f"ZepGraphMemoryUpdater inicializado: graph_id={graph_id}, batch_size={self.BATCH_SIZE}")
    
    def _get_platform_display_name(self, platform: str) -> str:
        """Retorna o nome amigavel da plataforma."""
        return self.PLATFORM_DISPLAY_NAMES.get(platform.lower(), platform)
    
    def start(self):
        """Inicia a thread de processamento em segundo plano."""
        if self._running:
            return
        
        self._running = True
        self._worker_thread = threading.Thread(
            target=self._worker_loop,
            daemon=True,
            name=f"ZepMemoryUpdater-{self.graph_id[:8]}"
        )
        self._worker_thread.start()
        logger.info(f"ZepGraphMemoryUpdater iniciado: graph_id={self.graph_id}")
    
    def stop(self):
        """Interrompe a thread de processamento."""
        self._running = False
        
        # Envia o que restou pendente.
        self._flush_remaining()
        
        if self._worker_thread and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=10)
        
        logger.info(f"ZepGraphMemoryUpdater finalizado: graph_id={self.graph_id}, "
                   f"total_activities={self._total_activities}, "
                   f"batches_sent={self._total_sent}, "
                   f"items_sent={self._total_items_sent}, "
                   f"failed={self._failed_count}, "
                   f"skipped={self._skipped_count}")
    
    def add_activity(self, activity: AgentActivity):
        """Adiciona uma atividade relevante do agente a fila."""
        # Ignora acoes nulas.
        if activity.action_type == "DO_NOTHING":
            self._skipped_count += 1
            return
        
        self._activity_queue.put(activity)
        self._total_activities += 1
        logger.debug(f"Atividade adicionada a fila do Zep: {activity.agent_name} - {activity.action_type}")
    
    def add_activity_from_dict(self, data: Dict[str, Any], platform: str):
        """Adiciona uma atividade a partir de um dicionario vindo do log."""
        # Ignora entradas de evento que nao representam acoes de agente.
        if "event_type" in data:
            return
        
        activity = AgentActivity(
            platform=platform,
            agent_id=data.get("agent_id", 0),
            agent_name=data.get("agent_name", ""),
            action_type=data.get("action_type", ""),
            action_args=data.get("action_args", {}),
            round_num=data.get("round", 0),
            timestamp=data.get("timestamp", datetime.now().isoformat()),
        )
        
        self.add_activity(activity)
    
    def _worker_loop(self):
        """Loop de trabalho que envia atividades em lote por plataforma."""
        while self._running or not self._activity_queue.empty():
            try:
                # Tenta obter uma atividade da fila.
                try:
                    activity = self._activity_queue.get(timeout=1)
                    
                    # Coloca a atividade no buffer correspondente.
                    platform = activity.platform.lower()
                    with self._buffer_lock:
                        if platform not in self._platform_buffers:
                            self._platform_buffers[platform] = []
                        self._platform_buffers[platform].append(activity)
                        
                        # Quando atingir o tamanho do lote, envia.
                        if len(self._platform_buffers[platform]) >= self.BATCH_SIZE:
                            batch = self._platform_buffers[platform][:self.BATCH_SIZE]
                            self._platform_buffers[platform] = self._platform_buffers[platform][self.BATCH_SIZE:]
                            self._send_batch_activities(batch, platform)
                            time.sleep(self.SEND_INTERVAL)
                    
                except Empty:
                    pass
                    
            except Exception as e:
                logger.error(f"Erro no loop do worker: {e}")
                time.sleep(1)
    
    def _send_batch_activities(self, activities: List[AgentActivity], platform: str):
        """Envia um lote de atividades ao grafo do Zep como um unico texto."""
        if not activities:
            return
        
        # Junta varias atividades em um texto separado por linhas.
        episode_texts = [activity.to_episode_text() for activity in activities]
        combined_text = "\n".join(episode_texts)
        
        # Envio com retry.
        for attempt in range(self.MAX_RETRIES):
            try:
                self.client.graph.add(
                    graph_id=self.graph_id,
                    type="text",
                    data=combined_text
                )
                
                self._total_sent += 1
                self._total_items_sent += len(activities)
                display_name = self._get_platform_display_name(platform)
                logger.info(f"Lote enviado com sucesso: {len(activities)} atividades de {display_name} para o grafo {self.graph_id}")
                logger.debug(f"Previa do lote: {combined_text[:200]}...")
                return
                
            except Exception as e:
                if attempt < self.MAX_RETRIES - 1:
                    logger.warning(f"Falha ao enviar lote ao Zep (tentativa {attempt + 1}/{self.MAX_RETRIES}): {e}")
                    time.sleep(self.RETRY_DELAY * (attempt + 1))
                else:
                    logger.error(f"Falha ao enviar lote ao Zep apos {self.MAX_RETRIES} tentativas: {e}")
                    self._failed_count += 1
    
    def _flush_remaining(self):
        """Envia as atividades restantes na fila e nos buffers."""
        # Primeiro move o que restou na fila para os buffers.
        while not self._activity_queue.empty():
            try:
                activity = self._activity_queue.get_nowait()
                platform = activity.platform.lower()
                with self._buffer_lock:
                    if platform not in self._platform_buffers:
                        self._platform_buffers[platform] = []
                    self._platform_buffers[platform].append(activity)
            except Empty:
                break
        
        # Depois envia os itens restantes de cada plataforma.
        with self._buffer_lock:
            for platform, buffer in self._platform_buffers.items():
                if buffer:
                    display_name = self._get_platform_display_name(platform)
                    logger.info(f"Enviando {len(buffer)} atividades restantes da plataforma {display_name}")
                    self._send_batch_activities(buffer, platform)
            # Limpa todos os buffers.
            for platform in self._platform_buffers:
                self._platform_buffers[platform] = []
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatisticas do atualizador."""
        with self._buffer_lock:
            buffer_sizes = {p: len(b) for p, b in self._platform_buffers.items()}
        
        return {
            "graph_id": self.graph_id,
            "batch_size": self.BATCH_SIZE,
            "total_activities": self._total_activities,
            "batches_sent": self._total_sent,
            "items_sent": self._total_items_sent,
            "failed_count": self._failed_count,
            "skipped_count": self._skipped_count,
            "queue_size": self._activity_queue.qsize(),
            "buffer_sizes": buffer_sizes,
            "running": self._running,
        }


class ZepGraphMemoryManager:
    """Gerencia atualizadores de memoria para multiplas simulacoes."""
    
    _updaters: Dict[str, ZepGraphMemoryUpdater] = {}
    _lock = threading.Lock()
    
    @classmethod
    def create_updater(cls, simulation_id: str, graph_id: str) -> ZepGraphMemoryUpdater:
        """Cria um atualizador para a simulacao informada."""
        with cls._lock:
            # Se ja existir, encerra o anterior.
            if simulation_id in cls._updaters:
                cls._updaters[simulation_id].stop()
            
            updater = ZepGraphMemoryUpdater(graph_id)
            updater.start()
            cls._updaters[simulation_id] = updater
            
            logger.info(f"Atualizador de memoria criado: simulation_id={simulation_id}, graph_id={graph_id}")
            return updater
    
    @classmethod
    def get_updater(cls, simulation_id: str) -> Optional[ZepGraphMemoryUpdater]:
        """Obtem o atualizador de uma simulacao."""
        return cls._updaters.get(simulation_id)
    
    @classmethod
    def stop_updater(cls, simulation_id: str):
        """Interrompe e remove o atualizador da simulacao."""
        with cls._lock:
            if simulation_id in cls._updaters:
                cls._updaters[simulation_id].stop()
                del cls._updaters[simulation_id]
                logger.info(f"Atualizador de memoria interrompido: simulation_id={simulation_id}")
    
    # Evita execucao duplicada de stop_all.
    _stop_all_done = False
    
    @classmethod
    def stop_all(cls):
        """Interrompe todos os atualizadores."""
        # Evita chamadas repetidas.
        if cls._stop_all_done:
            return
        cls._stop_all_done = True
        
        with cls._lock:
            if cls._updaters:
                for simulation_id, updater in list(cls._updaters.items()):
                    try:
                        updater.stop()
                    except Exception as e:
                        logger.error(f"Falha ao interromper atualizador: simulation_id={simulation_id}, error={e}")
                cls._updaters.clear()
            logger.info("Todos os atualizadores de memoria em grafo foram interrompidos")
    
    @classmethod
    def get_all_stats(cls) -> Dict[str, Dict[str, Any]]:
        """Retorna as estatisticas de todos os atualizadores."""
        return {
            sim_id: updater.get_stats() 
            for sim_id, updater in cls._updaters.items()
        }
