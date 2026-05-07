"""Auditable executive package generation for publishable reports."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .report_agent import ReportManager
from .safe_markdown_renderer import render_safe_markdown


EXECUTIVE_PACKAGE_FILENAMES = {
    "executive_summary.html",
    "evidence_annex.html",
    "executive_package_manifest.json",
}

ARTIFACT_INPUTS = [
    "system_gate.json",
    "evidence_manifest.json",
    "evidence_audit.json",
    "mission_bundle.json",
    "forecast_ledger.json",
    "cost_meter.json",
]


class ExecutivePackageError(Exception):
    """Base executive package error."""


class ExecutivePackageNotFound(ExecutivePackageError):
    """Report does not exist."""


class ExecutivePackageConflict(ExecutivePackageError):
    """Report is not eligible for an executive package."""


class ExecutivePackageInvalidPath(ExecutivePackageError):
    """Requested package path is unsafe or not allowlisted."""


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _package_dir(report_id: str, output_dir: Path | None = None) -> Path:
    if output_dir is not None:
        return Path(output_dir).resolve()
    return (Path(ReportManager._get_report_folder(report_id)).resolve() / "executive_package").resolve()


def _html_document(title: str, body: str) -> str:
    return "\n".join([
        "<!doctype html>",
        '<html lang="pt-BR">',
        "<head>",
        '  <meta charset="utf-8">',
        f"  <title>{title}</title>",
        "</head>",
        "<body>",
        body,
        "</body>",
        "</html>",
        "",
    ])


def _read_report_markdown(report_id: str, fallback: str) -> str:
    path = Path(ReportManager._get_report_markdown_path(report_id))
    if path.is_file():
        return path.read_text(encoding="utf-8")
    return fallback or ""


def _evidence_annex_markdown(report_id: str, artifacts: dict[str, Any]) -> str:
    sections = ["# Anexo de Evidencias", ""]
    for filename in ARTIFACT_INPUTS:
        payload = artifacts.get(filename)
        if not payload:
            continue
        sections.extend([
            f"## {filename}",
            "",
            "```json",
            json.dumps(payload, ensure_ascii=False, indent=2),
            "```",
            "",
        ])
    if len(sections) == 2:
        sections.append("Nenhum artefato opcional disponivel para anexar.")
    return "\n".join(sections)


def _write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    return data if isinstance(data, dict) else {"items": data}


def load_executive_package_manifest(report_id: str) -> dict[str, Any]:
    """Load the package manifest from disk without creating a package."""

    if not ReportManager.get_report(report_id):
        raise ExecutivePackageNotFound(f"Relatorio nao encontrado: {report_id}")
    manifest_path = _package_dir(report_id) / "executive_package_manifest.json"
    if not manifest_path.is_file():
        raise ExecutivePackageNotFound("Pacote executivo ainda nao foi criado")
    return _read_json(manifest_path)


def allowed_executive_package_file_path(report_id: str, filename: str) -> Path:
    """Resolve a package file only when it is present in the manifest allowlist."""

    if filename not in EXECUTIVE_PACKAGE_FILENAMES:
        raise ExecutivePackageInvalidPath(f"Arquivo nao permitido: {filename}")
    manifest = load_executive_package_manifest(report_id)
    allowed = {item.get("filename") for item in manifest.get("files", []) if isinstance(item, dict)}
    if filename not in allowed:
        raise ExecutivePackageInvalidPath(f"Arquivo nao listado no manifesto: {filename}")

    package_dir = _package_dir(report_id)
    path = (package_dir / filename).resolve()
    if path.parent != package_dir.resolve():
        raise ExecutivePackageInvalidPath(f"Arquivo nao permitido: {filename}")
    if not path.is_file():
        raise ExecutivePackageNotFound(f"Arquivo nao encontrado: {filename}")
    return path


def build_executive_package(report_id: str, *, output_dir: Path | None = None) -> dict[str, Any]:
    """Create executive summary, evidence annex, and manifest for a publishable report."""

    report = ReportManager.get_report(report_id)
    if not report:
        raise ExecutivePackageNotFound(f"Relatorio nao encontrado: {report_id}")

    delivery_status = report.delivery_status()
    if delivery_status != "publishable":
        raise ExecutivePackageConflict("Pacote executivo exige relatorio publicavel")

    package_dir = _package_dir(report_id, output_dir)
    package_dir.mkdir(parents=True, exist_ok=True)

    artifacts = {
        filename: ReportManager.load_json_artifact(report_id, filename)
        for filename in ARTIFACT_INPUTS
    }

    summary_result = render_safe_markdown(_read_report_markdown(report_id, report.markdown_content))
    annex_result = render_safe_markdown(_evidence_annex_markdown(report_id, artifacts))

    summary_path = package_dir / "executive_summary.html"
    annex_path = package_dir / "evidence_annex.html"
    _write_text(summary_path, _html_document("MiroFish Executive Summary", summary_result.html))
    _write_text(annex_path, _html_document("MiroFish Evidence Annex", annex_result.html))

    files = []
    for filename in ["executive_summary.html", "evidence_annex.html"]:
        path = package_dir / filename
        files.append({
            "filename": filename,
            "sha256": _sha256_file(path),
            "size": path.stat().st_size,
        })

    manifest = {
        "schema": "mirofish.executive_package_manifest.v1",
        "report_id": report_id,
        "simulation_id": report.simulation_id,
        "status": "created",
        "created_at": _now_iso(),
        "source_delivery_status": delivery_status,
        "files": files,
        "artifact_inputs": [name for name, payload in artifacts.items() if payload],
        "renderer_metadata": {
            "executive_summary.html": summary_result.metadata,
            "evidence_annex.html": annex_result.metadata,
        },
    }

    manifest_path = package_dir / "executive_package_manifest.json"
    _write_json(manifest_path, manifest)
    manifest["files"].append({
        "filename": "executive_package_manifest.json",
        "sha256": _sha256_file(manifest_path),
        "size": manifest_path.stat().st_size,
    })
    _write_json(manifest_path, manifest)

    ReportManager.save_json_artifact(report_id, "executive_package_manifest.json", manifest)
    return manifest
