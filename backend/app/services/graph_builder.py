"""
Servico de construcao de grafo
Usa a API REST do Graphiti Server para construir grafos de conhecimento.
"""

import json
import os
import uuid
import time
import threading
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass

from ..config import Config
from ..models.task import TaskManager, TaskStatus
from ..utils.graphiti_client import GraphitiClient
from ..utils.logger import get_logger
from .text_processor import TextProcessor

logger = get_logger('mirofish.graph_builder')

LOCAL_GRAPH_DIR = os.path.join(Config.UPLOAD_FOLDER, 'graphs')


# 2026-04-18, Phase 6: mapa de traducao para nomes de relacao em SCREAMING_SNAKE_CASE
# Graphiti extrai relacoes em ingles; o fork INTEIA exibe em pt-BR no grafo visual.
_RELATION_TRANSLATION = {
    "FEARS": "TEME",
    "ADVOCATES": "DEFENDE",
    "OPPOSES": "OPOE_A",
    "SUPPORTS": "APOIA",
    "IMPLEMENTS": "IMPLEMENTA",
    "CRITICIZES": "CRITICA",
    "PROPOSES": "PROPOE",
    "BELIEVES": "ACREDITA",
    "REPRESENTS": "REPRESENTA",
    "COMPETES": "COMPETE_COM",
    "COMPETES_WITH": "COMPETE_COM",
    "COLLABORATES": "COLABORA",
    "COLLABORATES_WITH": "COLABORA_COM",
    "DEPENDS": "DEPENDE",
    "DEPENDS_ON": "DEPENDE_DE",
    "PART_OF": "PARTE_DE",
    "LEADS": "LIDERA",
    "LEADS_TO": "LEVA_A",
    "CAUSES": "CAUSA",
    "AFFECTS": "AFETA",
    "INFLUENCES": "INFLUENCIA",
    "CONTROLS": "CONTROLA",
    "OWNS": "POSSUI",
    "CREATES": "CRIA",
    "DESTROYS": "DESTROI",
    "PROMOTES": "PROMOVE",
    "DEFENDS": "DEFENDE",
    "ATTACKS": "ATACA",
    "THREATENS": "AMEACA",
    "PROTECTS": "PROTEGE",
    "ACCUSES": "ACUSA",
    "NEGOTIATES": "NEGOCIA",
    "ALLIES_WITH": "ALIADO_DE",
    "LOCATED_IN": "LOCALIZADO_EM",
    "WORKS_FOR": "TRABALHA_PARA",
    "MEMBER_OF": "MEMBRO_DE",
}


def _translate_relation_name(name: str) -> str:
    """Traduz nomes SCREAMING_SNAKE_CASE de ingles para pt-BR."""
    if not name:
        return name
    upper = name.upper()
    if upper in _RELATION_TRANSLATION:
        return _RELATION_TRANSLATION[upper]
    return name


@dataclass
class GraphInfo:
    """Informacoes do grafo"""
    graph_id: str
    node_count: int
    edge_count: int
    entity_types: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "graph_id": self.graph_id,
            "node_count": self.node_count,
            "edge_count": self.edge_count,
            "entity_types": self.entity_types,
        }


class GraphBuilderService:
    """
    Servico de construcao de grafo.
    Responsavel por chamar a API REST do Graphiti Server para construir
    o grafo de conhecimento a partir de texto.
    """

    def __init__(self, api_key: Optional[str] = None):
        """Inicializa o servico.

        Args:
            api_key: Mantido na assinatura para compatibilidade. Nao e
                     necessario para o Graphiti Server (sem autenticacao).
        """
        self.client = GraphitiClient()
        self.task_manager = TaskManager()

    def build_graph_async(
        self,
        text: str,
        ontology: Dict[str, Any],
        graph_name: str = "MiroFish Graph",
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        batch_size: int = 3
    ) -> str:
        """
        Construir grafo de forma assincrona.

        Args:
            text: Texto de entrada
            ontology: Definicao de ontologia (saida da Interface 1)
            graph_name: Nome do grafo
            chunk_size: Tamanho do bloco de texto
            chunk_overlap: Tamanho da sobreposicao entre blocos
            batch_size: Quantidade de blocos por lote enviado

        Returns:
            ID da tarefa
        """
        task_id = self.task_manager.create_task(
            task_type="graph_build",
            metadata={
                "graph_name": graph_name,
                "chunk_size": chunk_size,
                "text_length": len(text),
            }
        )

        thread = threading.Thread(
            target=self._build_graph_worker,
            args=(task_id, text, ontology, graph_name, chunk_size, chunk_overlap, batch_size)
        )
        thread.daemon = True
        thread.start()

        return task_id

    def _build_graph_worker(
        self,
        task_id: str,
        text: str,
        ontology: Dict[str, Any],
        graph_name: str,
        chunk_size: int,
        chunk_overlap: int,
        batch_size: int
    ):
        """Thread de trabalho para construcao do grafo."""
        try:
            if not self.client.healthcheck():
                message = "Graphiti indisponivel ou endpoint de health incompatível."
                if Config.GRAPHITI_REQUIRED:
                    raise RuntimeError(message)
                graph_data = self.build_schema_fallback_graph(
                    text=text,
                    ontology=ontology,
                    graph_name=graph_name,
                    unavailable_reason=message,
                )
                self.task_manager.complete_task(task_id, {
                    "graph_id": graph_data["graph_id"],
                    "graph_info": {
                        "graph_id": graph_data["graph_id"],
                        "node_count": graph_data["node_count"],
                        "edge_count": graph_data["edge_count"],
                        "entity_types": [node["name"] for node in graph_data["nodes"]],
                    },
                    "graph_data": graph_data,
                    "chunks_processed": 0,
                    "graph_backend": "local_fallback",
                    "warning": graph_data["warning"],
                })
                return

            self.task_manager.update_task(
                task_id,
                status=TaskStatus.PROCESSING,
                progress=5,
                message="Iniciando construcao do grafo..."
            )

            # 1. Gerar group_id (no Graphiti, grupos sao criados implicitamente)
            graph_id = self.create_graph(graph_name)
            self.task_manager.update_task(
                task_id,
                progress=10,
                message=f"Grupo criado: {graph_id}"
            )

            # 2. Enviar contexto da ontologia como mensagem inicial
            self.set_ontology(graph_id, ontology)
            self.task_manager.update_task(
                task_id,
                progress=15,
                message="Contexto de ontologia enviado"
            )

            # 3. Dividir texto em blocos
            chunks = TextProcessor.split_text(text, chunk_size, chunk_overlap)
            total_chunks = len(chunks)
            self.task_manager.update_task(
                task_id,
                progress=20,
                message=f"Texto dividido em {total_chunks} blocos"
            )

            # 4. Enviar dados em lotes
            self.add_text_batches(
                graph_id, chunks, batch_size,
                lambda msg, prog: self.task_manager.update_task(
                    task_id,
                    progress=20 + int(prog * 0.4),  # 20-60%
                    message=msg
                )
            )

            # 5. Aguardar processamento do Graphiti
            self.task_manager.update_task(
                task_id,
                progress=60,
                message="Aguardando Graphiti processar dados..."
            )

            graph_data = self.wait_for_graph_materialization(
                graph_id,
                expected_count=total_chunks,
                progress_callback=lambda msg, prog: self.task_manager.update_task(
                    task_id,
                    progress=60 + int(prog * 35),  # 60-95%
                    message=msg
                ),
                timeout=120,
                stall_timeout=30,
            )

            # 6. Obter informacoes do grafo
            self.task_manager.update_task(
                task_id,
                progress=95,
                message="Obtendo informacoes do grafo..."
            )

            graph_info = self._get_graph_info(graph_id)

            # Concluir
            self.task_manager.complete_task(task_id, {
                "graph_id": graph_id,
                "graph_info": graph_info.to_dict(),
                "graph_data": graph_data,
                "chunks_processed": total_chunks,
            })

        except Exception as e:
            import traceback
            error_msg = f"{str(e)}\n{traceback.format_exc()}"
            self.task_manager.fail_task(task_id, error_msg)

    def create_graph(self, name: str) -> str:
        """Criar grupo no Graphiti (grupos sao criados implicitamente na primeira mensagem).

        Retorna o group_id gerado.
        """
        graph_id = f"mirofish_{uuid.uuid4().hex[:16]}"
        # No Graphiti, o grupo e criado automaticamente ao enviar a primeira
        # mensagem. Nao ha endpoint explicito de criacao.
        logger.info(f"Group ID gerado: {graph_id} (nome: {name})")
        return graph_id

    def create_local_graph(self, name: str) -> str:
        """Cria um ID local para fallback sem Graphiti."""
        graph_id = f"local_mirofish_{uuid.uuid4().hex[:16]}"
        logger.warning(f"Graphiti indisponivel; usando grafo local de esquema {graph_id} (nome: {name})")
        return graph_id

    def _local_graph_path(self, graph_id: str) -> str:
        return os.path.join(LOCAL_GRAPH_DIR, f"{graph_id}.json")

    def _save_local_graph_data(self, graph_data: Dict[str, Any]) -> None:
        os.makedirs(LOCAL_GRAPH_DIR, exist_ok=True)
        with open(self._local_graph_path(graph_data["graph_id"]), "w", encoding="utf-8") as f:
            json.dump(graph_data, f, ensure_ascii=False, indent=2)

    def _load_local_graph_data(self, graph_id: str) -> Optional[Dict[str, Any]]:
        path = self._local_graph_path(graph_id)
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def build_schema_fallback_graph(
        self,
        text: str,
        ontology: Dict[str, Any],
        graph_name: str,
        unavailable_reason: str,
    ) -> Dict[str, Any]:
        """Cria um grafo local de esquema quando Graphiti nao esta acessivel.

        O fallback nao finge que houve extração semântica: ele salva os tipos da
        ontologia como nós de esquema e marca o backend como local_fallback.
        """
        graph_id = self.create_local_graph(graph_name)
        entity_types = ontology.get("entity_types", []) or []
        edge_types = ontology.get("edge_types", []) or []

        nodes = []
        for index, entity in enumerate(entity_types, start=1):
            name = entity.get("name") or f"TipoEntidade{index}"
            nodes.append({
                "uuid": f"{graph_id}_entity_type_{index}",
                "name": name,
                "labels": ["TipoDeEntidade", "FallbackLocal"],
                "summary": entity.get("description", ""),
                "attributes": {
                    "kind": "ontology_entity_type",
                    "examples": entity.get("examples", []),
                    "source": "ontology",
                },
                "created_at": None,
            })

        edges = []
        edge_index = 1
        for edge in edge_types:
            relation_name = edge.get("name") or f"RELACAO_{edge_index}"
            targets = edge.get("source_targets") or [{}]
            for target in targets:
                edges.append({
                    "uuid": f"{graph_id}_edge_type_{edge_index}",
                    "name": relation_name,
                    "fact": edge.get("description", ""),
                    "fact_type": relation_name,
                    "source_node_uuid": "",
                    "target_node_uuid": "",
                    "source_node_name": target.get("source", ""),
                    "target_node_name": target.get("target", ""),
                    "attributes": {
                        "kind": "ontology_edge_type",
                        "source": "ontology",
                    },
                    "created_at": None,
                    "valid_at": None,
                    "invalid_at": None,
                    "expired_at": None,
                    "episodes": [],
                })
                edge_index += 1

        graph_data = {
            "graph_id": graph_id,
            "graph_backend": "local_fallback",
            "unavailable": True,
            "warning": (
                "Graphiti indisponível. O MiroFish criou um grafo local de esquema "
                "para continuar a preparação; a extração de entidades reais será feita "
                "por fallback LLM na etapa de simulação."
            ),
            "error": unavailable_reason,
            "source_text_length": len(text or ""),
            "nodes": nodes,
            "edges": edges,
            "node_count": len(nodes),
            "edge_count": len(edges),
        }
        self._save_local_graph_data(graph_data)
        return graph_data

    def set_ontology(self, graph_id: str, ontology: Dict[str, Any]):
        """Envia o contexto da ontologia como mensagem de sistema.

        O Graphiti nao possui configuracao explicita de ontologia como o Zep.
        Enviamos a descricao da ontologia como mensagem para que o LLM interno
        do Graphiti considere esses tipos ao extrair entidades.

        IMPORTANTE: Inclui group_id na mensagem para garantir propagacao em Neo4j.
        """
        # Constroi descricao textual da ontologia
        parts = [
            "INSTRUÇÃO DE IDIOMA: Todo o conteúdo extraído (nomes de entidades, relações, resumos, fatos) DEVE ser em português brasileiro. NÃO extraia nomes ou resumos em inglês.",
            "",
            "Ontologia do grafo de conhecimento:"
        ]

        for entity_def in ontology.get("entity_types", []):
            name = entity_def.get("name", "")
            desc = entity_def.get("description", "")
            attrs = [a.get("name", "") for a in entity_def.get("attributes", [])]
            parts.append(f"- Entidade '{name}': {desc}")
            if attrs:
                parts.append(f"  Atributos: {', '.join(attrs)}")

        for edge_def in ontology.get("edge_types", []):
            name = edge_def.get("name", "")
            desc = edge_def.get("description", "")
            sources_targets = edge_def.get("source_targets", [])
            parts.append(f"- Relacao '{name}': {desc}")
            for st in sources_targets:
                parts.append(f"  {st.get('source', '?')} -> {st.get('target', '?')}")

        ontology_text = "\n".join(parts)

        # [FIX] Incluir group_id na mensagem para garantir propagacao em Neo4j
        self.client.add_messages(
            group_id=graph_id,
            messages=[{
                "content": ontology_text,
                "role_type": "system",
                "role": "system",
                "source_description": "Definicao de ontologia MiroFish",
                "group_id": graph_id,  # Propagacao explicita do group_id
            }],
        )
        logger.info(f"Contexto de ontologia enviado para o grupo {graph_id} com {len(ontology.get('entity_types', []))} tipos de entidade")

    def add_text_batches(
        self,
        graph_id: str,
        chunks: List[str],
        batch_size: int = 3,
        progress_callback: Optional[Callable] = None
    ) -> None:
        """Adicionar texto ao grafo em lotes via POST /messages.

        IMPORTANTE: Todos os chunks DEVEM incluir o graph_id/group_id no metadata
        para garantir propagacao correta para Neo4j.
        """
        total_chunks = len(chunks)
        logger.info(f"Iniciando envio de {total_chunks} blocos para o grupo {graph_id}")

        for i in range(0, total_chunks, batch_size):
            batch_chunks = chunks[i:i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (total_chunks + batch_size - 1) // batch_size

            if progress_callback:
                progress = (i + len(batch_chunks)) / total_chunks
                progress_callback(
                    f"Enviando lote {batch_num}/{total_batches} ({len(batch_chunks)} blocos)...",
                    progress
                )

            # Constroi mensagens para o lote
            # CRITICO: Incluir group_id em cada mensagem para garantir sincronizacao em Neo4j
            messages = []
            for chunk in batch_chunks:
                messages.append({
                    "content": chunk,
                    "role_type": "user",
                    "role": "document",
                    "source_description": f"Bloco de texto do documento (lote {batch_num})",
                    # [FIX] Incluir group_id no metadata da mensagem para propagacao em Neo4j
                    "group_id": graph_id,
                })

            # Enviar para o Graphiti com retry
            max_retries = 5
            for attempt in range(max_retries):
                try:
                    self.client.add_messages(
                        group_id=graph_id,
                        messages=messages,
                    )
                    logger.debug(f"Lote {batch_num} enviado com sucesso para o grupo {graph_id}")
                    # Pausa entre lotes para nao sobrecarregar o servidor
                    time.sleep(2)
                    break

                except Exception as e:
                    error_str = str(e)
                    if '429' in error_str or 'rate limit' in error_str.lower():
                        wait_time = 30
                        logger.warning(f"Rate limit no lote {batch_num}, aguardando {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                    if progress_callback:
                        progress_callback(f"Falha no envio do lote {batch_num}: {error_str}", 0)
                    logger.error(f"Falha ao enviar lote {batch_num}: {error_str}")
                    raise

    def _wait_for_episodes(
        self,
        graph_id: str,
        expected_count: int = 0,
        progress_callback: Optional[Callable] = None,
        timeout: int = 120,
        stall_timeout: int = 30,
    ):
        """Aguardar o processamento assincrono do Graphiti.

        Faz polling em GET /episodes/{group_id}. O Graphiti pode consolidar
        mensagens em menos episodios do que blocos enviados, entao a espera
        termina por estabilidade/timeout e nao apenas por contagem exata.

        Nao trava: respeita timeout absoluto e retorna o que conseguiu.
        """
        if expected_count == 0:
            if progress_callback:
                progress_callback("Nada a aguardar (sem blocos enviados)", 1.0)
            return 0

        start_time = time.time()
        last_count = 0
        last_change = start_time
        poll_interval = 3  # segundos entre cada poll

        if progress_callback:
            progress_callback(f"Aguardando processamento de {expected_count} blocos...", 0)

        while True:
            elapsed = time.time() - start_time
            if elapsed > timeout:
                if progress_callback:
                    progress_callback(
                        f"Tempo limite ({timeout}s); {last_count} episodios detectados",
                        last_count / max(expected_count, 1)
                    )
                break

            try:
                episodes = self.client.get_episodes(graph_id, last_n=200)
                current_count = len(episodes)

                if current_count > last_count:
                    last_count = current_count
                    last_change = time.time()
                    progress_ratio = min(current_count / max(expected_count, 1), 1.0)
                    if progress_callback:
                        progress_callback(
                            f"Graphiti processando... {current_count} episodios ({int(elapsed)}s)",
                            progress_ratio
                        )

                if expected_count > 0 and current_count >= expected_count:
                    break

                # Estabilizou com dados — seguir para materializacao
                if current_count > 0 and (time.time() - last_change) >= stall_timeout:
                    if progress_callback:
                        progress_callback(
                            f"Estabilizado com {current_count} episodios",
                            min(current_count / max(expected_count, 1), 1.0)
                        )
                    break

                # Sem episodios apos stall_timeout — tenta search como fallback
                if current_count == 0 and elapsed >= stall_timeout:
                    try:
                        search_result = self.client.search(
                            group_ids=[graph_id], query="*", max_facts=5
                        )
                        facts = search_result.get("facts", [])
                        if len(facts) > 0:
                            if progress_callback:
                                progress_callback(
                                    f"Grafo com {len(facts)} fatos (via search)",
                                    1.0
                                )
                            return len(facts)
                    except Exception:
                        pass
                    # Sem fatos e sem episodios — sair sem esperar mais
                    if progress_callback:
                        progress_callback(
                            "Nenhum episodio detectado, seguindo para validacao",
                            0.0
                        )
                    break

            except Exception as e:
                logger.debug(f"Erro no polling de episodios: {e}")

            time.sleep(poll_interval)

        if progress_callback:
            progress_callback(f"Polling concluido: {last_count} episodios", 1.0)
        return last_count

    def wait_for_graph_materialization(
        self,
        graph_id: str,
        expected_count: int = 0,
        progress_callback: Optional[Callable] = None,
        timeout: int = 120,
        stall_timeout: int = 30,
    ) -> Dict[str, Any]:
        """Espera o Graphiti processar o input e valida se o grafo ganhou conteudo.

        Fluxo rapido: polling de episodios + ate 5 checks de materializacao (5s cada).
        Nunca trava mais que ~timeout + 25s.
        """
        self._wait_for_episodes(
            graph_id,
            expected_count=expected_count,
            progress_callback=progress_callback,
            timeout=timeout,
            stall_timeout=stall_timeout,
        )

        # Verificar materializacao. Com Codex + Graphiti, os episodios podem
        # aparecer antes das entidades/fatos; encerrar cedo demais gera grafo
        # "concluido" com zero nos.
        max_checks = 12
        check_interval = 10
        last_graph_data: Dict[str, Any] | None = None

        for attempt in range(max_checks):
            graph_data = self.get_graph_data(graph_id)
            last_graph_data = graph_data
            node_count = graph_data.get("node_count", 0) or 0
            edge_count = graph_data.get("edge_count", 0) or 0

            if node_count > 0 or edge_count > 0:
                if progress_callback:
                    progress_callback(
                        f"Grafo materializado: {node_count} nos, {edge_count} arestas (check {attempt+1}/{max_checks})",
                        1.0
                    )
                return graph_data

            if attempt < max_checks - 1:
                if progress_callback:
                    progress_callback(
                        f"Verificando materializacao... ({attempt+1}/{max_checks}, 0 nos ate agora)",
                        0.5 + (attempt * 0.05)
                    )
                time.sleep(check_interval)

        # Zero nos apos espera estendida — sinal forte de falha silenciosa
        # Log estruturado para diagnostico e nao silencia o problema
        import logging
        _glog = logging.getLogger('mirofish.graphiti')
        _glog.error(
            f"Graphiti zero nos apos {max_checks}x{check_interval}s para graph_id={graph_id}. "
            f"last_graph_data={last_graph_data}"
        )

        if last_graph_data is not None:
            if progress_callback:
                progress_callback(
                    "ATENCAO: grafo com zero nos apos timeout — relatorio pode ficar superficial",
                    1.0
                )
            return last_graph_data

        raise RuntimeError(f"Graphiti nao respondeu para {graph_id} apos {max_checks*check_interval}s")

    def _get_graph_info(self, graph_id: str) -> GraphInfo:
        """Obter informacoes do grafo via busca ampla."""
        # Busca ampla para obter fatos
        search_result = self.client.search(
            group_ids=[graph_id],
            query="*",
            max_facts=200,
        )

        facts = search_result.get("facts", [])

        # Extrair entidades unicas a partir dos fatos
        entity_names = set()
        for fact in facts:
            name = fact.get("name", "") if isinstance(fact, dict) else ""
            if name:
                entity_names.add(name)

        # Contar episodios como proxy para nos
        episodes = self.client.get_episodes(graph_id, last_n=200)

        return GraphInfo(
            graph_id=graph_id,
            node_count=len(entity_names) if entity_names else len(episodes),
            edge_count=len(facts),
            entity_types=list(entity_names)[:20],
        )

    def get_graph_data(self, graph_id: str) -> Dict[str, Any]:
        """
        Obter dados completos do grafo.

        No Graphiti, isso e feito via POST /search com query ampla
        e GET /episodes para listar episodios.
        """
        local_graph = self._load_local_graph_data(graph_id)
        if local_graph:
            return local_graph

        # Busca todos os fatos
        try:
            search_result = self.client.search(
                group_ids=[graph_id],
                query="*",
                max_facts=500,
            )
        except Exception as exc:
            if Config.GRAPHITI_REQUIRED:
                raise
            logger.warning(f"Graphiti indisponivel ao obter grafo {graph_id}: {exc}")
            return {
                "graph_id": graph_id,
                "graph_backend": "graphiti_unavailable",
                "unavailable": True,
                "warning": "Graphiti indisponível; dados do grafo não puderam ser carregados.",
                "error": str(exc),
                "nodes": [],
                "edges": [],
                "node_count": 0,
                "edge_count": 0,
            }

        raw_facts = search_result.get("facts", [])

        # Normalizar fatos para formato padrao
        nodes_data = []
        edges_data = []
        seen_entities = set()

        for fact in raw_facts:
            if isinstance(fact, dict):
                # Fato estruturado do Graphiti
                fact_uuid = fact.get("uuid", "")
                fact_name = fact.get("name", "")
                fact_text = fact.get("fact", "")
                valid_at = fact.get("valid_at")
                invalid_at = fact.get("invalid_at")
                created_at = fact.get("created_at")
                expired_at = fact.get("expired_at")

                edges_data.append({
                    "uuid": fact_uuid,
                    "name": fact_name,
                    "fact": fact_text,
                    "fact_type": fact_name,
                    "source_node_uuid": "",
                    "target_node_uuid": "",
                    "source_node_name": "",
                    "target_node_name": "",
                    "attributes": {},
                    "created_at": str(created_at) if created_at else None,
                    "valid_at": str(valid_at) if valid_at else None,
                    "invalid_at": str(invalid_at) if invalid_at else None,
                    "expired_at": str(expired_at) if expired_at else None,
                    "episodes": [],
                })

                # Extrair entidades mencionadas no fato
                if fact_name and fact_name not in seen_entities:
                    seen_entities.add(fact_name)
                    nodes_data.append({
                        "uuid": fact_uuid,
                        "name": fact_name,
                        "labels": ["Entidade"],
                        "summary": fact_text,
                        "attributes": {},
                        "created_at": str(created_at) if created_at else None,
                    })
            elif isinstance(fact, str):
                # Fato como string simples
                edges_data.append({
                    "uuid": "",
                    "name": "",
                    "fact": fact,
                    "fact_type": "",
                    "source_node_uuid": "",
                    "target_node_uuid": "",
                    "source_node_name": "",
                    "target_node_name": "",
                    "attributes": {},
                    "created_at": None,
                    "valid_at": None,
                    "invalid_at": None,
                    "expired_at": None,
                    "episodes": [],
                })

        # Pos-processamento: traduzir resumos em ingles para portugues
        for node in nodes_data:
            if node.get("summary"):
                node["summary"] = self._translate_if_english(node["summary"])

        for edge in edges_data:
            if edge.get("fact"):
                edge["fact"] = self._translate_if_english(edge["fact"])
            # 2026-04-18, Phase 6: traduzir nome de relacao (SCREAMING_SNAKE)
            for key in ("name", "fact_type"):
                if edge.get(key):
                    edge[key] = _translate_relation_name(edge[key])

        return {
            "graph_id": graph_id,
            "nodes": nodes_data,
            "edges": edges_data,
            "node_count": len(nodes_data),
            "edge_count": len(edges_data),
        }

    def _translate_if_english(self, text: str) -> str:
        """Detecta se o texto esta em ingles e traduz para pt-BR usando LLM barato.

        2026-04-18, Phase 6: fix da assinatura do LLMClient.chat() (usa messages=[])
        — bug silencioso antigo que fazia toda traducao falhar e voltar o texto original.
        """
        if not text or len(text) < 10:
            return text
        # Heuristica simples: se tem palavras comuns em ingles, traduz
        english_markers = [
            'the ', 'is ', 'are ', 'was ', 'has ', 'with ', 'for ', 'and ',
            'that ', 'this ', 'supports', 'opposes', 'competes', 'represents',
            'as part of', 'in order to',
        ]
        text_lower = text.lower()
        english_count = sum(1 for m in english_markers if m in text_lower)
        if english_count < 2:
            return text  # Provavelmente ja esta em portugues
        try:
            from ..utils.llm_client import LLMClient
            client = LLMClient()
            result = client.chat(
                messages=[
                    {"role": "system", "content": "Traduza o texto abaixo para português brasileiro. Retorne APENAS a tradução, sem explicações."},
                    {"role": "user", "content": text},
                ],
                temperature=0.2,
                max_tokens=1024,
            )
            return result.strip() if result else text
        except Exception:
            return text

    def delete_graph(self, graph_id: str):
        """Excluir grupo (equivale a excluir grafo)."""
        self.client.delete_group(graph_id)
        logger.info(f"Grupo excluido: {graph_id}")
