"""Cliente HTTP para o Graphiti Server.

Encapsula chamadas REST ao Graphiti Server, com retentativa e timeout
configuraveis. Substitui o SDK zep-cloud e o modulo zep_paging.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

import requests

from ..config import Config
from .logger import get_logger

logger = get_logger('mirofish.graphiti_client')

_DEFAULT_MAX_RETRIES = 1
_DEFAULT_RETRY_DELAY = 0.5  # segundos — fail fast quando Graphiti indisponivel


class GraphitiClient:
    """Cliente HTTP para o Graphiti Server REST API."""

    def __init__(self, base_url: Optional[str] = None, timeout: Optional[int] = None):
        self.base_url = (base_url or Config.GRAPHITI_BASE_URL).rstrip('/')
        self.timeout = timeout or Config.GRAPHITI_TIMEOUT

    # ------------------------------------------------------------------
    # Utilitarios internos
    # ------------------------------------------------------------------

    def _request(
        self,
        method: str,
        path: str,
        json_body: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        max_retries: int = _DEFAULT_MAX_RETRIES,
        retry_delay: float = _DEFAULT_RETRY_DELAY,
        operation_name: str = "request",
    ) -> Any:
        """Executa uma requisicao HTTP com retentativa e backoff exponencial."""
        url = f"{self.base_url}{path}"
        last_exception: Exception | None = None
        delay = retry_delay

        for attempt in range(max_retries):
            try:
                resp = requests.request(
                    method=method,
                    url=url,
                    json=json_body,
                    params=params,
                    timeout=self.timeout,
                )
                resp.raise_for_status()

                # Respostas 204 / corpo vazio
                if resp.status_code == 204 or not resp.content:
                    return None

                return resp.json()

            except requests.exceptions.HTTPError as e:
                status = e.response.status_code if e.response is not None else 0
                if status == 429:
                    retry_after = float(
                        e.response.headers.get('retry-after', 10)
                    )
                    logger.warning(
                        f"Graphiti rate limit (429) em {operation_name}, "
                        f"aguardando {retry_after:.0f}s (tentativa {attempt + 1}/{max_retries})"
                    )
                    time.sleep(retry_after)
                    last_exception = e
                    continue
                elif status >= 500:
                    last_exception = e
                    if attempt < max_retries - 1:
                        logger.warning(
                            f"Graphiti {operation_name} erro {status} "
                            f"(tentativa {attempt + 1}), retentando em {delay:.1f}s..."
                        )
                        time.sleep(delay)
                        delay *= 2
                        continue
                    raise
                else:
                    raise

            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout, OSError) as e:
                last_exception = e
                if attempt < max_retries - 1:
                    logger.warning(
                        f"Graphiti {operation_name} falhou (tentativa {attempt + 1}): "
                        f"{str(e)[:100]}, retentando em {delay:.1f}s..."
                    )
                    time.sleep(delay)
                    delay *= 2
                else:
                    logger.error(
                        f"Graphiti {operation_name} falhou apos {max_retries} tentativas: {str(e)}"
                    )

        if last_exception is not None:
            raise last_exception
        raise RuntimeError(f"Graphiti {operation_name}: falha inesperada sem excecao capturada")

    # ------------------------------------------------------------------
    # Healthcheck
    # ------------------------------------------------------------------

    def healthcheck(self) -> bool:
        """Verifica se o Graphiti Server esta acessivel."""
        endpoints = ("/healthcheck", "/health", "/healthz")
        last_error: Exception | None = None

        for endpoint in endpoints:
            try:
                self._request("GET", endpoint, operation_name=f"healthcheck({endpoint})")
                return True
            except Exception as e:
                last_error = e

        if last_error is not None:
            logger.warning(f"Graphiti healthcheck falhou: {last_error}")
        return False

    # ------------------------------------------------------------------
    # Mensagens (POST /messages)
    # ------------------------------------------------------------------

    def add_messages(
        self,
        group_id: str,
        messages: List[Dict[str, Any]],
    ) -> Any:
        """Envia mensagens ao Graphiti para extracao de entidades.

        Args:
            group_id: Identificador do grupo (equivale ao graph_id do Zep).
            messages: Lista de dicts com campos content, role_type, role, etc.
        """
        body = {
            "group_id": group_id,
            "messages": messages,
        }
        return self._request(
            "POST", "/messages",
            json_body=body,
            operation_name=f"add_messages(group={group_id})",
        )

    def add_text(self, group_id: str, text: str, role: str = "system") -> Any:
        """Atalho para enviar um unico bloco de texto como mensagem."""
        return self.add_messages(
            group_id=group_id,
            messages=[{
                "content": text,
                "role_type": "user",
                "role": role,
            }],
        )

    # ------------------------------------------------------------------
    # Busca (POST /search)
    # ------------------------------------------------------------------

    def search(
        self,
        group_ids: List[str],
        query: str,
        max_facts: int = 10,
    ) -> Dict[str, Any]:
        """Busca semantica de fatos no grafo.

        Retorna dict com chave 'facts' contendo lista de fatos.
        """
        body = {
            "group_ids": group_ids,
            "query": query,
            "max_facts": max_facts,
        }
        result = self._request(
            "POST", "/search",
            json_body=body,
            operation_name=f"search(groups={group_ids}, query={query[:40]})",
        )
        return result if result else {"facts": []}

    # ------------------------------------------------------------------
    # Memoria (POST /get-memory)
    # ------------------------------------------------------------------

    def get_memory(self, group_id: str, messages: List[Dict[str, Any]]) -> Any:
        """Obtem memoria a partir do historico de mensagens."""
        body = {
            "group_id": group_id,
            "messages": messages,
        }
        return self._request(
            "POST", "/get-memory",
            json_body=body,
            operation_name=f"get_memory(group={group_id})",
        )

    # ------------------------------------------------------------------
    # Episodios (GET /episodes/{group_id})
    # ------------------------------------------------------------------

    def get_episodes(self, group_id: str, last_n: int = 100) -> List[Dict[str, Any]]:
        """Lista episodios de um grupo."""
        result = self._request(
            "GET", f"/episodes/{group_id}",
            params={"last_n": last_n},
            operation_name=f"get_episodes(group={group_id})",
        )
        if isinstance(result, list):
            return result
        if isinstance(result, dict):
            return result.get("episodes", [])
        return []

    # ------------------------------------------------------------------
    # Entidade (POST /entity-node)
    # ------------------------------------------------------------------

    def create_entity_node(self, entity_data: Dict[str, Any]) -> Any:
        """Cria um no de entidade manualmente."""
        return self._request(
            "POST", "/entity-node",
            json_body=entity_data,
            operation_name="create_entity_node",
        )

    # ------------------------------------------------------------------
    # Arestas (GET/DELETE /entity-edge/{uuid})
    # ------------------------------------------------------------------

    def get_edge(self, uuid: str) -> Optional[Dict[str, Any]]:
        """Obtem uma aresta pelo UUID."""
        return self._request(
            "GET", f"/entity-edge/{uuid}",
            operation_name=f"get_edge({uuid[:8]})",
        )

    def delete_edge(self, uuid: str) -> None:
        """Remove uma aresta pelo UUID."""
        self._request(
            "DELETE", f"/entity-edge/{uuid}",
            operation_name=f"delete_edge({uuid[:8]})",
        )

    # ------------------------------------------------------------------
    # Episodios individuais (DELETE /episode/{uuid})
    # ------------------------------------------------------------------

    def delete_episode(self, uuid: str) -> None:
        """Remove um episodio pelo UUID."""
        self._request(
            "DELETE", f"/episode/{uuid}",
            operation_name=f"delete_episode({uuid[:8]})",
        )

    # ------------------------------------------------------------------
    # Grupo (DELETE /group/{group_id})
    # ------------------------------------------------------------------

    def delete_group(self, group_id: str) -> None:
        """Remove um grupo inteiro (equivale a excluir um grafo)."""
        self._request(
            "DELETE", f"/group/{group_id}",
            operation_name=f"delete_group({group_id})",
        )

    # ------------------------------------------------------------------
    # Limpeza geral (POST /clear)
    # ------------------------------------------------------------------

    def clear(self) -> None:
        """Limpa todo o grafo do Graphiti Server."""
        self._request("POST", "/clear", operation_name="clear")

    # ------------------------------------------------------------------
    # Sincronizacao de group_id em Neo4j (maintenance)
    # ------------------------------------------------------------------

    def sync_graph_id_to_neo4j(self, group_id: str, neo4j_uri: str, neo4j_user: str, neo4j_password: str) -> dict:
        """Sincroniza o group_id para todos os nós de um grupo no Neo4j.

        Esta funcao e necessaria para corrigir nós que possam ter sido criados
        sem o group_id correto durante problemas de sincronizacao.

        Args:
            group_id: Identificador do grupo (graph_id).
            neo4j_uri: URI de conexao ao Neo4j (e.g., "bolt://neo4j:7687").
            neo4j_user: Usuario do Neo4j.
            neo4j_password: Senha do Neo4j.

        Returns:
            Dict com resultado da sincronizacao.
        """
        try:
            from neo4j import GraphDatabase

            driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))

            with driver.session() as session:
                # Contar nós com este group_id
                result = session.run(
                    "MATCH (n {group_id: $group_id}) RETURN count(n) as count",
                    group_id=group_id
                )
                count_with_id = result.single()["count"] if result.single() else 0

                # Buscar nós que estao "órfaos" (sem group_id correto)
                # Isso pode acontecer se houver sincronizacao incompleta
                result = session.run(
                    "MATCH (n) WHERE n.group_id IS NULL OR n.group_id = '' RETURN count(n) as count"
                )
                count_orphaned = result.single()["count"] if result.single() else 0

                driver.close()

            return {
                "group_id": group_id,
                "nodes_with_group_id": count_with_id,
                "orphaned_nodes": count_orphaned,
                "status": "checked"
            }

        except Exception as e:
            logger.error(f"Erro ao sincronizar group_id em Neo4j: {e}")
            return {
                "group_id": group_id,
                "error": str(e),
                "status": "failed"
            }
