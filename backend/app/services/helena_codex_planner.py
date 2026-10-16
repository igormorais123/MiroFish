"""
Planejador da Helena via Codex CLI, usando a assinatura local.

Por que existe: o gateway OmniRoute enfileira chamadas por conta
(`codex:<id>`) com um limite de 20 em espera. Uma simulacao coloca centenas
de acoes de agente nessa fila e a Helena — que faz uma chamada isolada e
interativa — nao consegue vaga, leva 429 e cai no plano de regras. O CLI
fala direto com a assinatura e nao disputa essa fila.

Requer o binario `codex` autenticado na maquina que roda o backend. Onde ele
nao existir, o chamador segue pelo caminho HTTP normal.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from typing import Any, Dict, Optional

from ..config import Config
from ..utils.logger import get_logger

logger = get_logger('mirofish.helena_codex')


class CodexPlannerUnavailable(RuntimeError):
    """O CLI nao esta utilizavel; o chamador deve tentar outro caminho."""


def codex_cli_path() -> Optional[str]:
    """Caminho do binario codex, ou None se nao estiver instalado."""
    configured = (Config.HELENA_CODEX_BIN or "").strip()
    if configured:
        return configured if os.path.isfile(configured) else shutil.which(configured)
    return shutil.which("codex")


def is_available() -> bool:
    return codex_cli_path() is not None


def _extract_agent_message(stdout: str) -> Optional[str]:
    """
    Pega o texto final do agente no fluxo JSONL do `codex exec --json`.

    O fluxo mistura eventos de sessao, erro e progresso; interessa o ultimo
    item do tipo agent_message.
    """
    message = None
    for line in stdout.splitlines():
        line = line.strip()
        if not line or not line.startswith("{"):
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue

        item = event.get("item") or {}
        if item.get("type") == "agent_message" and item.get("text"):
            message = item["text"]
    return message


def _parse_plan_json(text: str) -> Dict[str, Any]:
    """Extrai o objeto JSON do texto do agente, tolerando cerca de codigo."""
    from ..utils.llm_client import parse_llm_json_response

    return parse_llm_json_response(text)


def plan_with_codex_cli(
    system_prompt: str,
    user_payload: Dict[str, Any],
    timeout_seconds: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Gera o plano da Helena chamando o Codex CLI.

    O comando do operador viaja dentro do payload como dado nao confiavel; o
    prompt de sistema e quem define o contrato. O processo roda com sandbox
    somente-leitura, sem a config do usuario (skills, MCPs e hooks ficam de
    fora — sao dezenas de milhares de tokens irrelevantes aqui) e com o
    diretorio de trabalho num temporario vazio, fora do repositorio.

    Raises:
        CodexPlannerUnavailable: binario ausente, timeout ou saida inutilizavel.
    """
    binary = codex_cli_path()
    if not binary:
        raise CodexPlannerUnavailable("binario codex nao encontrado na maquina")

    prompt = (
        f"{system_prompt}\n\n"
        "Toda a informacao necessaria esta no bloco ENTRADA abaixo. Nao explore o "
        "ambiente, nao liste arquivos e nao execute comandos: nao ha nada util no "
        "disco para esta tarefa. Responda SOMENTE com o objeto JSON, sem cerca de "
        "codigo e sem texto ao redor.\n\n"
        f"ENTRADA:\n{json.dumps(user_payload, ensure_ascii=False, indent=2)}"
    )

    # Prompt vai por stdin: como argumento, o JSON com aspas sofre com as regras
    # de escaping da linha de comando do Windows e chega truncado ao binario.
    command = [
        binary,
        "exec",
        "-m", Config.HELENA_CODEX_MODEL,
        "-c", f"model_reasoning_effort={Config.LLM_HELENA_REASONING_EFFORT}",
        "--ignore-user-config",
        "--sandbox", "read-only",
        "--skip-git-repo-check",
        "--json",
        "-",
    ]

    timeout_seconds = timeout_seconds or Config.HELENA_CODEX_TIMEOUT_SECONDS

    with tempfile.TemporaryDirectory(prefix="helena-codex-") as workdir:
        try:
            completed = subprocess.run(
                command,
                cwd=workdir,
                input=prompt,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout_seconds,
                shell=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise CodexPlannerUnavailable(
                f"codex excedeu {timeout_seconds}s"
            ) from exc
        except OSError as exc:
            raise CodexPlannerUnavailable(f"falha ao executar codex: {exc}") from exc

    if completed.returncode != 0:
        raise CodexPlannerUnavailable(
            f"codex saiu com codigo {completed.returncode}: {(completed.stderr or '')[:300]}"
        )

    message = _extract_agent_message(completed.stdout or "")
    if not message:
        raise CodexPlannerUnavailable("codex nao retornou mensagem do agente")

    try:
        plan = _parse_plan_json(message)
    except ValueError as exc:
        raise CodexPlannerUnavailable(f"codex retornou JSON invalido: {exc}") from exc

    logger.info("Plano da Helena gerado via Codex CLI (%s)", Config.HELENA_CODEX_MODEL)
    return plan
