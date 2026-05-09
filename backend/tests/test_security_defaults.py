"""Regressoes de hardening para defaults publicos do Flask."""

import subprocess
import sys
import re
from pathlib import Path

import pytest

import app as app_module
from app.models.project import ProjectManager
from app.services.report_agent import ReportManager
from app.services.simulation_manager import SimulationManager
from app.services.simulation_runner import SimulationRunner


def test_config_debug_defaults_to_false_without_env(monkeypatch):
    monkeypatch.delenv("FLASK_DEBUG", raising=False)

    script = (
        "import os, dotenv;"
        "os.environ.pop('FLASK_DEBUG', None);"
        "dotenv.load_dotenv=lambda *_args, **_kwargs: None;"
        "from app.config import Config;"
        "raise SystemExit(0 if Config.DEBUG is False else 1)"
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr


def test_root_health_does_not_expose_backend_infra_config():
    client = app_module.create_app().test_client()

    response = client.get("/health")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["status"] == "ok"
    assert "llm_base_url" not in payload
    assert "llm_model" not in payload


def test_cors_default_rejects_untrusted_origin():
    client = app_module.create_app().test_client()

    response = client.get(
        "/api/internal/v1/health/public",
        headers={"Origin": "https://evil.example"},
    )

    assert response.status_code == 200
    assert "Access-Control-Allow-Origin" not in response.headers


def test_request_logging_does_not_record_json_body(monkeypatch):
    debug_messages = []

    class StubLogger:
        def debug(self, message):
            debug_messages.append(str(message))

        def info(self, *_args, **_kwargs):
            pass

        def warning(self, *_args, **_kwargs):
            pass

        def error(self, *_args, **_kwargs):
            pass

    monkeypatch.setattr(app_module, "get_logger", lambda _name: StubLogger())

    client = app_module.create_app().test_client()
    response = client.post(
        "/api/internal/v1/health/public",
        json={"api_key": "secret-token-value"},
    )

    assert response.status_code == 405
    assert not any("secret-token-value" in message for message in debug_messages)


@pytest.mark.parametrize(
    ("label", "resolver"),
    [
        ("project", ProjectManager._get_project_dir),
        ("simulation", lambda value: SimulationManager()._get_simulation_dir(value)),
        ("runner", SimulationRunner._load_run_state),
        ("report", ReportManager._get_report_folder),
    ],
)
def test_storage_ids_reject_path_traversal_segments(label, resolver):
    with pytest.raises(ValueError, match=label):
        resolver(r"..\outside")


def test_root_llm_proxy_does_not_commit_provider_tokens():
    source = Path(__file__).resolve().parents[2].joinpath("llm_proxy_v2.py").read_text(encoding="utf-8")

    assert not re.search(r'=\s*["\'](?:sk|csk)-[A-Za-z0-9_-]{16,}', source)


def test_maintenance_scripts_do_not_commit_neo4j_passwords():
    source = (
        Path(__file__).resolve().parents[1]
        .joinpath("scripts", "fix_neo4j_graph_ids.py")
        .read_text(encoding="utf-8")
    )

    assert 'NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")' in source
    assert not re.search(r'NEO4J_PASSWORD\s*=\s*["\'][^"\']{8,}["\']', source)


def test_flask_run_defaults_to_localhost():
    source = Path(__file__).resolve().parents[1].joinpath("run.py").read_text(encoding="utf-8")

    assert "os.environ.get('FLASK_HOST', '127.0.0.1')" in source
    assert "os.environ.get('FLASK_HOST', '0.0.0.0')" not in source
