"""Smoke check operacional do MiroFish.

Executa validacoes locais e, se MIROFISH_LIVE_URL estiver definido, checa o
health publico e o historico contra um backend vivo.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parents[1]


def backend_python() -> str:
    windows_python = ROOT / "backend" / ".venv" / "Scripts" / "python.exe"
    posix_python = ROOT / "backend" / ".venv" / "bin" / "python"
    if windows_python.exists():
        return str(windows_python)
    if posix_python.exists():
        return str(posix_python)
    return sys.executable


def run_step(name: str, command: list[str], cwd: Path) -> bool:
    print(f"\n== {name} ==")
    started = time.perf_counter()
    command = list(command)
    if os.name == "nt" and command and command[0] == "npm":
        command[0] = "npm.cmd"
    completed = subprocess.run(command, cwd=str(cwd), text=True)
    elapsed = time.perf_counter() - started
    if completed.returncode != 0:
        print(f"FAIL {name} ({elapsed:.1f}s)")
        return False
    print(f"OK {name} ({elapsed:.1f}s)")
    return True


def fetch_json(name: str, url: str, timeout: int = 15) -> bool:
    print(f"\n== {name} ==")
    try:
        with urlopen(url, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
        print(json.dumps(payload, ensure_ascii=False, indent=2)[:1200])
        return True
    except (URLError, TimeoutError, json.JSONDecodeError) as exc:
        print(f"FAIL {name}: {exc}")
        return False


def main() -> int:
    checks = [
        run_step("frontend build", ["npm", "run", "build"], ROOT),
        run_step(
            "backend focused tests",
            [
                backend_python(),
                "-m",
                "pytest",
                "tests/test_llm_client_json.py",
                "tests/test_ontology_generator_v2.py",
                "tests/test_graph_builder.py",
                "tests/test_simulation_manager.py",
                "-q",
            ],
            ROOT / "backend",
        ),
    ]

    live_url = os.environ.get("MIROFISH_LIVE_URL", "").rstrip("/")
    if live_url:
        checks.extend([
            fetch_json("live public health", f"{live_url}/health/public", timeout=5),
            fetch_json("live history", f"{live_url}/api/simulation/history?limit=1", timeout=15),
        ])

    return 0 if all(checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
