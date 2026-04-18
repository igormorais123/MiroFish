"""
Rotas de API relacionadas ao grafo de conhecimento
Utiliza mecanismo de contexto por projeto, com estado persistido no servidor
"""

import os
import traceback
import threading
from flask import request, jsonify

from . import graph_bp
from ..config import Config
from ..services.ontology_generator import OntologyGenerator
from ..services.graph_builder import GraphBuilderService
from ..services.text_processor import TextProcessor
from ..utils.file_parser import FileParser
from ..utils.logger import get_logger
from ..models.task import TaskManager, TaskStatus
from ..models.project import ProjectManager, ProjectStatus

# Obtendo o logger
logger = get_logger('mirofish.api')


def allowed_file(filename: str) -> bool:
    """Verifica se a extensao do arquivo e permitida"""
    if not filename or '.' not in filename:
        return False
    ext = os.path.splitext(filename)[1].lower().lstrip('.')
    return ext in Config.ALLOWED_EXTENSIONS


# ============== Interfaces de gerenciamento de projeto ==============

@graph_bp.route('/project/<project_id>', methods=['GET'])
def get_project(project_id: str):
    """
    Obter detalhes do projeto
    """
    project = ProjectManager.get_project(project_id)

    if not project:
        return jsonify({
            "success": False,
            "error": f"Projeto não encontrado: {project_id}"
        }), 404

    return jsonify({
        "success": True,
        "data": project.to_dict()
    })


@graph_bp.route('/project/list', methods=['GET'])
def list_projects():
    """
    Listar todos os projetos
    """
    # 2026-04-18, Phase 7: validacao de limits
    from ..utils.pagination import get_limit
    limit = get_limit(default=50, max_limit=1000)
    projects = ProjectManager.list_projects(limit=limit)

    return jsonify({
        "success": True,
        "data": [p.to_dict() for p in projects],
        "count": len(projects)
    })


@graph_bp.route('/project/<project_id>', methods=['DELETE'])
def delete_project(project_id: str):
    """
    Excluir projeto
    """
    success = ProjectManager.delete_project(project_id)

    if not success:
        return jsonify({
            "success": False,
            "error": f"Projeto não encontrado ou falha ao excluir: {project_id}"
        }), 404

    return jsonify({
        "success": True,
        "message": f"Projeto removido: {project_id}"
    })


@graph_bp.route('/project/<project_id>/reset', methods=['POST'])
def reset_project(project_id: str):
    """
    Redefinir estado do projeto (para reconstruir o grafo)
    """
    project = ProjectManager.get_project(project_id)

    if not project:
        return jsonify({
            "success": False,
            "error": f"Projeto não encontrado: {project_id}"
        }), 404

    # Redefinir para o estado de ontologia gerada
    if project.ontology:
        project.status = ProjectStatus.ONTOLOGY_GENERATED
    else:
        project.status = ProjectStatus.CREATED

    project.graph_id = None
    project.graph_build_task_id = None
    project.error = None
    ProjectManager.save_project(project)

    return jsonify({
        "success": True,
        "message": f"Projeto redefinido: {project_id}",
        "data": project.to_dict()
    })


# ============== Interface 1: Upload de arquivos e geracao de ontologia ==============

@graph_bp.route('/ontology/generate', methods=['POST'])
def generate_ontology():
    """
    Interface 1: Upload de arquivos, analise e geracao da definicao de ontologia

    Metodo de requisicao: multipart/form-data

    Parametros:
        files: Arquivos enviados (PDF/MD/TXT), podendo ser multiplos
        simulation_requirement: Descricao do objetivo da simulacao (obrigatorio)
        project_name: Nome do projeto (opcional)
        additional_context: Contexto adicional (opcional)

    Retorno:
        {
            "success": true,
            "data": {
                "project_id": "proj_xxxx",
                "ontology": {
                    "entity_types": [...],
                    "edge_types": [...],
                    "analysis_summary": "..."
                },
                "files": [...],
                "total_text_length": 12345
            }
        }
    """
    try:
        logger.info("=== Iniciando geracao da definicao de ontologia ===")

        # Obter parametros
        simulation_requirement = request.form.get('simulation_requirement', '')
        project_name = request.form.get('project_name', 'Unnamed Project')
        additional_context = request.form.get('additional_context', '')

        logger.debug(f"Nome do projeto: {project_name}")
        logger.debug(f"Objetivo da simulacao: {simulation_requirement[:100]}...")

        if not simulation_requirement:
            return jsonify({
                "success": False,
                "error": "Informe a descrição do objetivo da simulação (simulation_requirement)"
            }), 400

        # Obter arquivos enviados
        uploaded_files = request.files.getlist('files')
        if not uploaded_files or all(not f.filename for f in uploaded_files):
            return jsonify({
                "success": False,
                "error": "Envie pelo menos um arquivo de documento"
            }), 400

        # Criar projeto
        project = ProjectManager.create_project(name=project_name)
        project.simulation_requirement = simulation_requirement
        logger.info(f"Projeto criado: {project.project_id}")

        # Salvar arquivos e extrair texto
        document_texts = []
        all_text = ""

        for file in uploaded_files:
            if file and file.filename and allowed_file(file.filename):
                # Salvar arquivo no diretorio do projeto
                file_info = ProjectManager.save_file_to_project(
                    project.project_id,
                    file,
                    file.filename
                )
                project.files.append({
                    "filename": file_info["original_filename"],
                    "size": file_info["size"]
                })

                # Extrair texto
                text = FileParser.extract_text(file_info["path"])
                text = TextProcessor.preprocess_text(text)
                document_texts.append(text)
                all_text += f"\n\n=== {file_info['original_filename']} ===\n{text}"

        if not document_texts:
            ProjectManager.delete_project(project.project_id)
            return jsonify({
                "success": False,
                "error": "Nenhum documento pôde ser processado com sucesso. Verifique o formato dos arquivos."
            }), 400

        # Salvar texto extraido
        project.total_text_length = len(all_text)
        ProjectManager.save_extracted_text(project.project_id, all_text)
        logger.info(f"Extracao de texto concluida, total de {len(all_text)} caracteres")

        # Gerar ontologia
        logger.info("Chamando LLM para gerar definicao de ontologia...")
        generator = OntologyGenerator()
        ontology = generator.generate(
            document_texts=document_texts,
            simulation_requirement=simulation_requirement,
            additional_context=additional_context if additional_context else None
        )

        # Salvar ontologia no projeto
        entity_count = len(ontology.get("entity_types", []))
        edge_count = len(ontology.get("edge_types", []))
        logger.info(f"Ontologia gerada: {entity_count} tipos de entidade, {edge_count} tipos de relacao")

        project.ontology = {
            "entity_types": ontology.get("entity_types", []),
            "edge_types": ontology.get("edge_types", [])
        }
        project.analysis_summary = ontology.get("analysis_summary", "")
        project.status = ProjectStatus.ONTOLOGY_GENERATED
        ProjectManager.save_project(project)
        logger.info(f"=== Geracao de ontologia concluida === ID do projeto: {project.project_id}")

        return jsonify({
            "success": True,
            "data": {
                "project_id": project.project_id,
                "project_name": project.name,
                "ontology": project.ontology,
                "analysis_summary": project.analysis_summary,
                "files": project.files,
                "total_text_length": project.total_text_length
            }
        })

    except Exception as e:
        logger.error(f"Falha na geracao de ontologia: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============== Interface 2: Construcao do grafo ==============

@graph_bp.route('/build', methods=['POST'])
def build_graph():
    """
    Interface 2: Construir grafo a partir do project_id

    Requisicao (JSON):
        {
            "project_id": "proj_xxxx",  // Obrigatorio, vindo da Interface 1
            "graph_name": "Nome do grafo",    // Opcional
            "chunk_size": 500,          // Opcional, padrao 500
            "chunk_overlap": 50         // Opcional, padrao 50
        }

    Retorno:
        {
            "success": true,
            "data": {
                "project_id": "proj_xxxx",
                "task_id": "task_xxxx",
                "message": "A tarefa de construção do grafo foi iniciada"
            }
        }
    """
    try:
        logger.info("=== Iniciando construcao do grafo ===")

        # Verificar configuracao
        errors = Config.validate()
        if errors:
            logger.error(f"Erro de configuracao: {errors}")
            return jsonify({
                "success": False,
                "error": "Erro de configuração: " + "; ".join(errors)
            }), 500

        # Processar requisicao
        data = request.get_json() or {}
        project_id = data.get('project_id')
        logger.debug(f"Parametros da requisicao: project_id={project_id}")

        if not project_id:
            return jsonify({
                "success": False,
                "error": "Informe o project_id"
            }), 400

        # Obter projeto
        project = ProjectManager.get_project(project_id)
        if not project:
            return jsonify({
                "success": False,
                "error": f"Projeto não encontrado: {project_id}"
            }), 404

        # Verificar estado do projeto
        force = data.get('force', False)  # Forcar reconstrucao

        if project.status == ProjectStatus.CREATED:
            return jsonify({
                "success": False,
                "error": "O projeto ainda não gerou a ontologia. Execute primeiro /ontology/generate"
            }), 400

        if project.status == ProjectStatus.GRAPH_BUILDING and not force:
            return jsonify({
                "success": False,
                "error": "O grafo já está em construção. Não envie novamente. Para forçar a reconstrução, use force: true.",
                "task_id": project.graph_build_task_id
            }), 400

        # Se forcando reconstrucao, redefinir estado
        if force and project.status in [ProjectStatus.GRAPH_BUILDING, ProjectStatus.FAILED, ProjectStatus.GRAPH_COMPLETED]:
            project.status = ProjectStatus.ONTOLOGY_GENERATED
            project.graph_id = None
            project.graph_build_task_id = None
            project.error = None

        # Obter configuracao
        graph_name = data.get('graph_name', project.name or 'MiroFish Graph')
        chunk_size = data.get('chunk_size', project.chunk_size or Config.DEFAULT_CHUNK_SIZE)
        chunk_overlap = data.get('chunk_overlap', project.chunk_overlap or Config.DEFAULT_CHUNK_OVERLAP)

        # Atualizar configuracao do projeto
        project.chunk_size = chunk_size
        project.chunk_overlap = chunk_overlap

        # Obter texto extraido
        text = ProjectManager.get_extracted_text(project_id)
        if not text:
            return jsonify({
                "success": False,
                "error": "Conteúdo de texto extraído não encontrado"
            }), 400

        # Obter ontologia
        ontology = project.ontology
        if not ontology:
            return jsonify({
                "success": False,
                "error": "Definição de ontologia não encontrada"
            }), 400

        # Validar ontologia
        entity_types = ontology.get("entity_types", [])
        edge_types = ontology.get("edge_types", [])

        if not entity_types:
            return jsonify({
                "success": False,
                "error": "Ontologia inválida: nenhum tipo de entidade definido"
            }), 400

        if not edge_types:
            return jsonify({
                "success": False,
                "error": "Ontologia inválida: nenhum tipo de relação definido"
            }), 400

        for et in entity_types:
            if not et.get("name"):
                return jsonify({
                    "success": False,
                    "error": "Tipo de entidade sem nome na ontologia"
                }), 400

        # Criar tarefa assincrona
        task_manager = TaskManager()
        task_id = task_manager.create_task(f"Construção do grafo: {graph_name}")
        logger.info(f"Tarefa de construcao do grafo criada: task_id={task_id}, project_id={project_id}")

        # Atualizar estado do projeto
        project.status = ProjectStatus.GRAPH_BUILDING
        project.graph_build_task_id = task_id
        ProjectManager.save_project(project)

        # Iniciar tarefa em segundo plano
        def build_task():
            build_logger = get_logger('mirofish.build')
            try:
                builder = GraphBuilderService()
                if not builder.client.healthcheck():
                    raise RuntimeError(
                        "Graphiti indisponivel ou endpoint de health incompatível."
                    )

                build_logger.info(f"[{task_id}] Iniciando construcao do grafo...")
                task_manager.update_task(
                    task_id,
                    status=TaskStatus.PROCESSING,
                    message="Inicializando o serviço de construção do grafo..."
                )

                # Dividir em blocos
                task_manager.update_task(
                    task_id,
                    message="Dividindo o texto em blocos...",
                    progress=5
                )
                chunks = TextProcessor.split_text(
                    text,
                    chunk_size=chunk_size,
                    overlap=chunk_overlap
                )
                total_chunks = len(chunks)

                # Criar grafo
                task_manager.update_task(
                    task_id,
                    message="Criando o grupo no Graphiti...",
                    progress=10
                )
                graph_id = builder.create_graph(name=graph_name)

                # Atualizar graph_id do projeto
                project.graph_id = graph_id
                ProjectManager.save_project(project)

                # Definir ontologia
                task_manager.update_task(
                    task_id,
                    message="Definindo a ontologia...",
                    progress=15
                )
                builder.set_ontology(graph_id, ontology)

                # Adicionar texto (assinatura do progress_callback: (msg, progress_ratio))
                def add_progress_callback(msg, progress_ratio):
                    progress = 15 + int(progress_ratio * 40)  # 15% - 55%
                    task_manager.update_task(
                        task_id,
                        message=msg,
                        progress=progress
                    )

                task_manager.update_task(
                    task_id,
                    message=f"Iniciando a adição de {total_chunks} blocos de texto...",
                    progress=15
                )

                builder.add_text_batches(
                    graph_id,
                    chunks,
                    batch_size=3,
                    progress_callback=add_progress_callback
                )

                # Aguardar processamento do Graphiti
                task_manager.update_task(
                    task_id,
                    message="Aguardando o Graphiti processar os dados...",
                    progress=55
                )

                def wait_progress_callback(msg, progress_ratio):
                    progress = 55 + int(progress_ratio * 35)  # 55% - 90%
                    task_manager.update_task(
                        task_id,
                        message=msg,
                        progress=progress
                    )

                graph_data = builder.wait_for_graph_materialization(
                    graph_id,
                    expected_count=total_chunks,
                    progress_callback=wait_progress_callback,
                    timeout=120,
                    stall_timeout=30,
                )

                # Obter dados do grafo
                task_manager.update_task(
                    task_id,
                    message="Obtendo dados do grafo...",
                    progress=95
                )

                # Atualizar estado do projeto
                project.status = ProjectStatus.GRAPH_COMPLETED
                ProjectManager.save_project(project)

                node_count = graph_data.get("node_count", 0)
                edge_count = graph_data.get("edge_count", 0)
                build_logger.info(f"[{task_id}] Construcao do grafo concluida: graph_id={graph_id}, nos={node_count}, arestas={edge_count}")

                # Concluir
                task_manager.update_task(
                    task_id,
                    status=TaskStatus.COMPLETED,
                    message="Construção do grafo concluída",
                    progress=100,
                    result={
                        "project_id": project_id,
                        "graph_id": graph_id,
                        "node_count": node_count,
                        "edge_count": edge_count,
                        "chunk_count": total_chunks
                    }
                )

            except Exception as e:
                # Atualizar estado do projeto para falha
                build_logger.error(f"[{task_id}] Falha na construcao do grafo: {str(e)}")
                build_logger.debug(traceback.format_exc())

                project.status = ProjectStatus.FAILED
                project.error = str(e)
                ProjectManager.save_project(project)

                task_manager.update_task(
                    task_id,
                    status=TaskStatus.FAILED,
                    message=f"Falha na construção: {str(e)}"
                )

        # Iniciar thread em segundo plano
        thread = threading.Thread(target=build_task, daemon=True)
        thread.start()

        return jsonify({
            "success": True,
            "data": {
                "project_id": project_id,
                "task_id": task_id,
                "message": "A tarefa de construção do grafo foi iniciada. Consulte o progresso em /task/{task_id}"
            }
        })

    except Exception as e:
        logger.error(f"Falha na construcao do grafo: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============== Interface de consulta de tarefas ==============

@graph_bp.route('/task/<task_id>', methods=['GET'])
def get_task(task_id: str):
    """
    Consultar estado da tarefa
    """
    task = TaskManager().get_task(task_id)

    if not task:
        return jsonify({
            "success": False,
            "error": f"Tarefa não encontrada: {task_id}"
        }), 404

    return jsonify({
        "success": True,
        "data": task.to_dict()
    })


@graph_bp.route('/tasks', methods=['GET'])
def list_tasks():
    """
    Listar todas as tarefas
    """
    tasks = TaskManager().list_tasks()

    return jsonify({
        "success": True,
        "data": [t.to_dict() for t in tasks],
        "count": len(tasks)
    })


# ============== Interface de dados do grafo ==============

@graph_bp.route('/data/<graph_id>', methods=['GET'])
def get_graph_data(graph_id: str):
    """
    Obter dados do grafo (nos e arestas)
    """
    try:
        builder = GraphBuilderService()
        graph_data = builder.get_graph_data(graph_id)

        return jsonify({
            "success": True,
            "data": graph_data
        })

    except Exception as e:
        logger.error(f"Falha ao obter dados do grafo: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@graph_bp.route('/delete/<graph_id>', methods=['DELETE'])
def delete_graph(graph_id: str):
    """
    Excluir grafo do Graphiti
    """
    try:
        builder = GraphBuilderService()
        builder.delete_graph(graph_id)

        return jsonify({
            "success": True,
            "message": f"Grafo removido: {graph_id}"
        })

    except Exception as e:
        logger.error(f"Falha ao excluir grafo: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
