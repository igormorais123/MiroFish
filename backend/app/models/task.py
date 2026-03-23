"""
Gerenciamento de estado de tarefas
Usado para rastrear tarefas de longa duracao (como construcao de grafos)
Persistencia em disco via JSON para sobreviver a reinícios do servidor.
"""

import json
import os
import uuid
import threading
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional
from dataclasses import dataclass, field

from ..config import Config


class TaskStatus(str, Enum):
    """Enumeracao de estados de tarefa"""
    PENDING = "pending"          # Aguardando
    PROCESSING = "processing"    # Em processamento
    COMPLETED = "completed"      # Concluida
    FAILED = "failed"            # Falha


@dataclass
class Task:
    """Classe de dados de tarefa"""
    task_id: str
    task_type: str
    status: TaskStatus
    created_at: datetime
    updated_at: datetime
    progress: int = 0              # Progresso total em percentual 0-100
    message: str = ""              # Mensagem de estado
    result: Optional[Dict] = None  # Resultado da tarefa
    error: Optional[str] = None    # Informacao de erro
    metadata: Dict = field(default_factory=dict)  # Metadados adicionais
    progress_detail: Dict = field(default_factory=dict)  # Informacoes detalhadas de progresso

    def to_dict(self) -> Dict[str, Any]:
        """Converter para dicionario"""
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "progress": self.progress,
            "message": self.message,
            "progress_detail": self.progress_detail,
            "result": self.result,
            "error": self.error,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """Reconstruir Task a partir de dicionario"""
        return cls(
            task_id=data["task_id"],
            task_type=data["task_type"],
            status=TaskStatus(data["status"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            progress=data.get("progress", 0),
            message=data.get("message", ""),
            result=data.get("result"),
            error=data.get("error"),
            metadata=data.get("metadata", {}),
            progress_detail=data.get("progress_detail", {}),
        )


# Caminho do arquivo de persistencia
_TASKS_FILE = os.path.join(Config.UPLOAD_FOLDER, 'tasks_state.json')


class TaskManager:
    """
    Gerenciador de tarefas
    Gerenciamento de estado de tarefas com seguranca de thread e persistencia em disco.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """Padrao Singleton"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._tasks: Dict[str, Task] = {}
                    cls._instance._task_lock = threading.Lock()
                    cls._instance._load_from_disk()
        return cls._instance

    def _load_from_disk(self):
        """Carrega tarefas salvas do disco ao inicializar"""
        if not os.path.exists(_TASKS_FILE):
            return
        try:
            with open(_TASKS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            for task_data in data:
                task = Task.from_dict(task_data)
                # Tarefas que estavam em processamento quando o servidor caiu sao marcadas como falhas
                if task.status == TaskStatus.PROCESSING:
                    task.status = TaskStatus.FAILED
                    task.error = "Tarefa interrompida por reinicio do servidor"
                    task.updated_at = datetime.now()
                self._tasks[task.task_id] = task
        except Exception:
            pass  # Arquivo corrompido — começa limpo

    def _save_to_disk(self):
        """Salva estado das tarefas em disco (chamado dentro do _task_lock)"""
        try:
            os.makedirs(os.path.dirname(_TASKS_FILE), exist_ok=True)
            tasks_data = [t.to_dict() for t in self._tasks.values()]
            with open(_TASKS_FILE, 'w', encoding='utf-8') as f:
                json.dump(tasks_data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass  # Falha silenciosa — nao bloqueia operacao principal

    def create_task(self, task_type: str, metadata: Optional[Dict] = None) -> str:
        """
        Criar nova tarefa

        Args:
            task_type: Tipo da tarefa
            metadata: Metadados adicionais

        Returns:
            ID da tarefa
        """
        task_id = str(uuid.uuid4())
        now = datetime.now()

        task = Task(
            task_id=task_id,
            task_type=task_type,
            status=TaskStatus.PENDING,
            created_at=now,
            updated_at=now,
            metadata=metadata or {}
        )

        with self._task_lock:
            self._tasks[task_id] = task
            self._save_to_disk()

        return task_id

    def get_task(self, task_id: str) -> Optional[Task]:
        """Obter tarefa"""
        with self._task_lock:
            return self._tasks.get(task_id)

    def update_task(
        self,
        task_id: str,
        status: Optional[TaskStatus] = None,
        progress: Optional[int] = None,
        message: Optional[str] = None,
        result: Optional[Dict] = None,
        error: Optional[str] = None,
        progress_detail: Optional[Dict] = None
    ):
        """
        Atualizar estado da tarefa

        Args:
            task_id: ID da tarefa
            status: Novo estado
            progress: Progresso
            message: Mensagem
            result: Resultado
            error: Informacao de erro
            progress_detail: Informacoes detalhadas de progresso
        """
        with self._task_lock:
            task = self._tasks.get(task_id)
            if task:
                task.updated_at = datetime.now()
                if status is not None:
                    task.status = status
                if progress is not None:
                    task.progress = progress
                if message is not None:
                    task.message = message
                if result is not None:
                    task.result = result
                if error is not None:
                    task.error = error
                if progress_detail is not None:
                    task.progress_detail = progress_detail
                # Persiste em transicoes de estado importantes
                if status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.PROCESSING):
                    self._save_to_disk()

    def complete_task(self, task_id: str, result: Dict):
        """Marcar tarefa como concluida"""
        self.update_task(
            task_id,
            status=TaskStatus.COMPLETED,
            progress=100,
            message="Tarefa concluida",
            result=result
        )

    def fail_task(self, task_id: str, error: str):
        """Marcar tarefa como falha"""
        self.update_task(
            task_id,
            status=TaskStatus.FAILED,
            message="Tarefa falhou",
            error=error
        )

    def list_tasks(self, task_type: Optional[str] = None) -> list:
        """Listar tarefas"""
        with self._task_lock:
            tasks = list(self._tasks.values())
            if task_type:
                tasks = [t for t in tasks if t.task_type == task_type]
            return [t.to_dict() for t in sorted(tasks, key=lambda x: x.created_at, reverse=True)]

    def cleanup_old_tasks(self, max_age_hours: int = 24):
        """Limpar tarefas antigas"""
        from datetime import timedelta
        cutoff = datetime.now() - timedelta(hours=max_age_hours)

        with self._task_lock:
            old_ids = [
                tid for tid, task in self._tasks.items()
                if task.created_at < cutoff and task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]
            ]
            for tid in old_ids:
                del self._tasks[tid]
            if old_ids:
                self._save_to_disk()
