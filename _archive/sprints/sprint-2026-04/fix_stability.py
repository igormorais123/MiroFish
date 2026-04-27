"""
FASE 1: Estabilidade — LLM Fallback + Retry + SQLite Fix + Graphiti Health
Aplica todas as correções P0 no MiroFish backend.
"""
import sys
import re

def main():
    base = sys.argv[1] if len(sys.argv) > 1 else "/app/backend"

    # ============================================================
    # 1.1 LLM Fallback Multi-Provider
    # ============================================================
    print("=== 1.1 LLM Fallback Multi-Provider ===")

    llm_path = f"{base}/app/utils/llm_client.py"
    with open(llm_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Replace the entire _request_with_retry method with fallback-capable version
    old_init = '''    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None
    ):
        self.api_key = api_key or Config.LLM_API_KEY
        self.base_url = (base_url or Config.LLM_BASE_URL).rstrip("/")
        self.model = Config.resolve_model_name(model or Config.LLM_MODEL_NAME)
        self.timeout = Config.LLM_TIMEOUT_SECONDS
        self.max_retries = max(Config.LLM_MAX_RETRIES, 10)

        if not self.api_key:
            raise ValueError("LLM_API_KEY ou OMNIROUTE_API_KEY nao configurada")'''

    new_init = '''    # Providers de fallback: se o primario falhar com 503, tenta o proximo
    FALLBACK_MODELS = [
        None,  # modelo primario (self.model)
        "BestFREE",
        "mirofish-smart",
    ]

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None
    ):
        self.api_key = api_key or Config.LLM_API_KEY
        self.base_url = (base_url or Config.LLM_BASE_URL).rstrip("/")
        self.model = Config.resolve_model_name(model or Config.LLM_MODEL_NAME)
        self.timeout = Config.LLM_TIMEOUT_SECONDS
        self.max_retries = max(Config.LLM_MAX_RETRIES, 8)

        if not self.api_key:
            raise ValueError("LLM_API_KEY ou OMNIROUTE_API_KEY nao configurada")'''

    if old_init in content:
        content = content.replace(old_init, new_init)
        print("  OK: FALLBACK_MODELS adicionado ao __init__")
    else:
        print("  SKIP: __init__ pattern not found (may already be patched)")

    # Replace _request_with_retry to support fallback models
    old_retry_start = '''    def _request_with_retry(self, **kwargs):
        """Executa chamada ao provider via requests (compativel com OmniRouter)."""
        kwargs["stream"] = False

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Connection": "close",
        }

        last_error = None
        for attempt in range(1, self.max_retries + 1):'''

    new_retry_start = '''    def _request_with_retry(self, **kwargs):
        """Executa chamada ao provider com fallback para modelos alternativos."""
        kwargs["stream"] = False

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Connection": "close",
        }

        original_model = kwargs.get("model", self.model)
        last_error = None

        # Tenta cada modelo de fallback
        for fallback_model in self.FALLBACK_MODELS:
            model_to_try = fallback_model or original_model
            kwargs["model"] = model_to_try

            for attempt in range(1, self.max_retries + 1):'''

    if old_retry_start in content:
        content = content.replace(old_retry_start, new_retry_start)
        print("  OK: _request_with_retry com fallback models")
    else:
        print("  SKIP: retry start pattern not found")

    # Update the error handling to try next fallback
    old_retry_end = '''            except Exception as exc:
                last_error = exc
                if attempt >= self.max_retries:
                    break
                time.sleep(min(5 * attempt, 30))

        raise last_error'''

    new_retry_end = '''            except Exception as exc:
                last_error = exc
                error_str = str(exc)
                is_503 = '503' in error_str or 'inactive' in error_str.lower()

                if attempt >= self.max_retries:
                    if is_503:
                        break  # Tenta proximo fallback model
                    raise last_error  # Erro nao-recuperavel, nao tenta fallback

                import random
                jitter = random.uniform(0.5, 1.5)
                time.sleep(min(3 * attempt * jitter, 20))

            # Se chegou aqui com sucesso, o loop interno fez return
            # Se chegou aqui por break (max retries), tenta proximo fallback

        raise last_error'''

    if old_retry_end in content:
        content = content.replace(old_retry_end, new_retry_end)
        print("  OK: Fallback entre modelos + jitter")
    else:
        print("  SKIP: retry end pattern not found")

    with open(llm_path, 'w', encoding='utf-8') as f:
        f.write(content)

    # ============================================================
    # 1.3 SQLite Permissions Fix
    # ============================================================
    print("\n=== 1.3 SQLite Permissions Fix ===")

    runner_path = f"{base}/app/services/simulation_runner.py"
    with open(runner_path, 'r', encoding='utf-8') as f:
        runner = f.read()

    # Add permission fix before spawning subprocess
    if 'chmod' not in runner:
        runner = runner.replace(
            "if not os.path.exists(config_path):",
            """# Fix SQLite permissions para evitar "readonly database" apos restart
        for db_file in ['twitter_simulation.db', 'reddit_simulation.db']:
            db_path = os.path.join(sim_dir, db_file)
            if os.path.exists(db_path):
                try:
                    os.chmod(db_path, 0o666)
                except OSError:
                    pass
        # Garantir que o diretorio tem permissao de escrita (necessario para SQLite journal)
        try:
            os.chmod(sim_dir, 0o777)
        except OSError:
            pass

        if not os.path.exists(config_path):""",
            1
        )
        print("  OK: chmod antes de spawn subprocess")
    else:
        print("  SKIP: chmod ja existe")

    with open(runner_path, 'w', encoding='utf-8') as f:
        f.write(runner)

    # ============================================================
    # 1.4 Graphiti Materialization Timeout Increase
    # ============================================================
    print("\n=== 1.4 Graphiti Health Check ===")

    graph_path = f"{base}/app/services/graph_builder.py"
    with open(graph_path, 'r', encoding='utf-8') as f:
        graph = f.read()

    # Increase materialization checks
    graph = graph.replace("max_checks = 5", "max_checks = 12")
    graph = graph.replace("check_interval = 5", "check_interval = 10")
    print("  OK: Materialization 12 checks x 10s (2 min total)")

    with open(graph_path, 'w', encoding='utf-8') as f:
        f.write(graph)

    # ============================================================
    # 2.4 Traduzir nomes de relações no get_graph_data
    # ============================================================
    print("\n=== 2.4 Traduzir relações no grafo ===")

    with open(graph_path, 'r', encoding='utf-8') as f:
        graph = f.read()

    # Add translation to edge names in get_graph_data return
    old_return = '''        return {
            "graph_id": graph_id,
            "nodes": nodes_data,
            "edges": edges_data,
            "node_count": len(nodes_data),
            "edge_count": len(edges_data),
        }'''

    # Check if fallback was already added (from previous patch)
    if 'Fallback: se search nao retornou dados' in graph:
        # Find the return after fallback
        old_return = '''        return {
            "graph_id": graph_id,
            "nodes": nodes_data,
            "edges": edges_data,
            "node_count": len(nodes_data),
            "edge_count": len(edges_data),
        }'''

    new_return = '''        # Traduzir nomes de relacoes EN -> PT-BR
        for edge in edges_data:
            name = edge.get("name", "")
            if name and hasattr(self, '_RELATION_MAP') or '_RELATION_MAP' in dir(self.__class__):
                pass
            elif name in _RELATION_MAP:
                edge["name"] = _RELATION_MAP[name]
            fact = edge.get("fact", "")
            if fact and len(fact) > 15:
                from ..utils.llm_client import LLMClient as _LC
                # Nao traduz aqui — tradução feita no zep_tools.to_text()
                pass

        return {
            "graph_id": graph_id,
            "nodes": nodes_data,
            "edges": edges_data,
            "node_count": len(nodes_data),
            "edge_count": len(edges_data),
        }'''

    # Only replace if _RELATION_MAP exists in file
    if '_RELATION_MAP' in graph and old_return in graph:
        graph = graph.replace(old_return, new_return, 1)
        print("  OK: Relacoes traduzidas no retorno")
    else:
        print("  SKIP: _RELATION_MAP ou return nao encontrados")

    with open(graph_path, 'w', encoding='utf-8') as f:
        f.write(graph)

    print("\n=== FASE 1 + 2.4 COMPLETA ===")
    print("Reiniciar container para aplicar mudancas.")


if __name__ == "__main__":
    main()
