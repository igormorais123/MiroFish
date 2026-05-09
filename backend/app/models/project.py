"""
Gerenciamento de contexto de projeto
Usado para persistir o estado do projeto no servidor, evitando a transferencia de grandes volumes de dados entre interfaces no frontend
"""

import os
import json
import uuid
import shutil
from datetime import datetime
from typing import Dict, Any, List, Optional
from enum import Enum
from dataclasses import dataclass, field, asdict
from ..config import Config


class ProjectStatus(str, Enum):
    """Estado do projeto"""
    CREATED = "created"              # Recem-criado, arquivos ja enviados
    ONTOLOGY_GENERATED = "ontology_generated"  # Ontologia gerada
    GRAPH_BUILDING = "graph_building"    # Grafo em construcao
    GRAPH_COMPLETED = "graph_completed"  # Construcao do grafo concluida
    FAILED = "failed"                # Falha


@dataclass
class Project:
    """Modelo de dados do projeto"""
    project_id: str
    name: str
    status: ProjectStatus
    created_at: str
    updated_at: str

    # Informacoes de arquivos
    files: List[Dict[str, str]] = field(default_factory=list)  # [{filename, path, size}]
    total_text_length: int = 0

    # Informacoes de ontologia (preenchido apos geracao na Interface 1)
    ontology: Optional[Dict[str, Any]] = None
    analysis_summary: Optional[str] = None

    # Informacoes do grafo (preenchido apos conclusao da Interface 2)
    graph_id: Optional[str] = None
    graph_build_task_id: Optional[str] = None
    graph_backend: Optional[str] = None
    graph_warning: Optional[str] = None

    # Configuracao
    simulation_requirement: Optional[str] = None
    structured_context: Optional[Dict[str, Any]] = None
    chunk_size: int = 500
    chunk_overlap: int = 50

    # Informacoes de erro
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Converter para dicionario"""
        return {
            "project_id": self.project_id,
            "name": self.name,
            "status": self.status.value if isinstance(self.status, ProjectStatus) else self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "files": self.files,
            "total_text_length": self.total_text_length,
            "ontology": self.ontology,
            "analysis_summary": self.analysis_summary,
            "graph_id": self.graph_id,
            "graph_build_task_id": self.graph_build_task_id,
            "graph_backend": self.graph_backend,
            "graph_warning": self.graph_warning,
            "simulation_requirement": self.simulation_requirement,
            "structured_context": self.structured_context,
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
            "error": self.error
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Project':
        """Criar a partir de dicionario"""
        status = data.get('status', 'created')
        if isinstance(status, str):
            status = ProjectStatus(status)

        return cls(
            project_id=data['project_id'],
            name=data.get('name', 'Projeto sem nome'),
            status=status,
            created_at=data.get('created_at', ''),
            updated_at=data.get('updated_at', ''),
            files=data.get('files', []),
            total_text_length=data.get('total_text_length', 0),
            ontology=data.get('ontology'),
            analysis_summary=data.get('analysis_summary'),
            graph_id=data.get('graph_id'),
            graph_build_task_id=data.get('graph_build_task_id'),
            graph_backend=data.get('graph_backend'),
            graph_warning=data.get('graph_warning'),
            simulation_requirement=data.get('simulation_requirement'),
            structured_context=data.get('structured_context'),
            chunk_size=data.get('chunk_size', 500),
            chunk_overlap=data.get('chunk_overlap', 50),
            error=data.get('error')
        )


class ProjectManager:
    """Gerenciador de projetos - responsavel pelo armazenamento persistente e recuperacao de projetos"""

    # Diretorio raiz de armazenamento de projetos
    PROJECTS_DIR = os.path.join(Config.UPLOAD_FOLDER, 'projects')

    @classmethod
    def _ensure_projects_dir(cls):
        """Garantir que o diretorio de projetos exista"""
        os.makedirs(cls.PROJECTS_DIR, exist_ok=True)

    @classmethod
    def _get_project_dir(cls, project_id: str) -> str:
        """Obter caminho do diretorio do projeto"""
        return os.path.join(cls.PROJECTS_DIR, project_id)

    @classmethod
    def _get_project_meta_path(cls, project_id: str) -> str:
        """Obter caminho do arquivo de metadados do projeto"""
        return os.path.join(cls._get_project_dir(project_id), 'project.json')

    @classmethod
    def _get_project_files_dir(cls, project_id: str) -> str:
        """Obter diretorio de armazenamento de arquivos do projeto"""
        return os.path.join(cls._get_project_dir(project_id), 'files')

    @classmethod
    def _get_project_text_path(cls, project_id: str) -> str:
        """Obter caminho de armazenamento do texto extraido do projeto"""
        return os.path.join(cls._get_project_dir(project_id), 'extracted_text.txt')

    @classmethod
    def create_project(cls, name: str = "Projeto sem nome") -> Project:
        """
        Criar novo projeto

        Args:
            name: Nome do projeto

        Returns:
            Objeto Project recem-criado
        """
        cls._ensure_projects_dir()

        project_id = f"proj_{uuid.uuid4().hex[:12]}"
        now = datetime.now().isoformat()

        project = Project(
            project_id=project_id,
            name=name,
            status=ProjectStatus.CREATED,
            created_at=now,
            updated_at=now
        )

        # Criar estrutura de diretorios do projeto
        project_dir = cls._get_project_dir(project_id)
        files_dir = cls._get_project_files_dir(project_id)
        os.makedirs(project_dir, exist_ok=True)
        os.makedirs(files_dir, exist_ok=True)

        # Salvar metadados do projeto
        cls.save_project(project)

        return project

    @classmethod
    def save_project(cls, project: Project) -> None:
        """Salvar metadados do projeto"""
        project.updated_at = datetime.now().isoformat()
        meta_path = cls._get_project_meta_path(project.project_id)

        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(project.to_dict(), f, ensure_ascii=False, indent=2)

    @classmethod
    def get_project(cls, project_id: str) -> Optional[Project]:
        """
        Obter projeto

        Args:
            project_id: ID do projeto

        Returns:
            Objeto Project, ou None se nao existir
        """
        meta_path = cls._get_project_meta_path(project_id)

        if not os.path.exists(meta_path):
            return None

        with open(meta_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return Project.from_dict(data)

    @classmethod
    def list_projects(cls, limit: int = 50) -> List[Project]:
        """
        Listar todos os projetos

        Args:
            limit: Limite de quantidade retornada

        Returns:
            Lista de projetos, ordenada por data de criacao decrescente
        """
        cls._ensure_projects_dir()

        projects = []
        for project_id in os.listdir(cls.PROJECTS_DIR):
            project = cls.get_project(project_id)
            if project:
                projects.append(project)

        # Ordenar por data de criacao decrescente
        projects.sort(key=lambda p: p.created_at, reverse=True)

        return projects[:limit]

    @classmethod
    def delete_project(cls, project_id: str) -> bool:
        """
        Excluir projeto e todos os seus arquivos

        Args:
            project_id: ID do projeto

        Returns:
            Se a exclusao foi bem-sucedida
        """
        project_dir = cls._get_project_dir(project_id)

        if not os.path.exists(project_dir):
            return False

        shutil.rmtree(project_dir)
        return True

    @classmethod
    def save_file_to_project(cls, project_id: str, file_storage, original_filename: str) -> Dict[str, str]:
        """
        Salvar arquivo enviado no diretorio do projeto

        Args:
            project_id: ID do projeto
            file_storage: Objeto FileStorage do Flask
            original_filename: Nome original do arquivo

        Returns:
            Dicionario com informacoes do arquivo {filename, path, size}
        """
        files_dir = cls._get_project_files_dir(project_id)
        os.makedirs(files_dir, exist_ok=True)

        # Gerar nome de arquivo seguro
        ext = os.path.splitext(original_filename)[1].lower()
        safe_filename = f"{uuid.uuid4().hex[:8]}{ext}"
        file_path = os.path.join(files_dir, safe_filename)

        # Salvar arquivo
        file_storage.save(file_path)

        # Obter tamanho do arquivo
        file_size = os.path.getsize(file_path)

        return {
            "original_filename": original_filename,
            "saved_filename": safe_filename,
            "path": file_path,
            "size": file_size
        }

    @classmethod
    def save_extracted_text(cls, project_id: str, text: str) -> None:
        """Salvar texto extraido"""
        text_path = cls._get_project_text_path(project_id)
        with open(text_path, 'w', encoding='utf-8') as f:
            f.write(text)

    @classmethod
    def get_extracted_text(cls, project_id: str) -> Optional[str]:
        """Obter texto extraido"""
        text_path = cls._get_project_text_path(project_id)

        if not os.path.exists(text_path):
            return None

        with open(text_path, 'r', encoding='utf-8') as f:
            return f.read()

    @classmethod
    def get_project_files(cls, project_id: str) -> List[str]:
        """Obter todos os caminhos de arquivos do projeto"""
        files_dir = cls._get_project_files_dir(project_id)

        if not os.path.exists(files_dir):
            return []

        return [
            os.path.join(files_dir, f)
            for f in os.listdir(files_dir)
            if os.path.isfile(os.path.join(files_dir, f))
        ]
