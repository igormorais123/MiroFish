"""Verified report export bundle creation and lookup."""

from __future__ import annotations

import hashlib
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .report_agent import ReportManager
from .inteia_report_html import inteia_renderer_metadata, render_inteia_report_html
from .report_method_checklist import evaluate_report_method_checklist
from .safe_markdown_renderer import render_safe_markdown


EXPORT_FILENAMES = {
    "full_report.html",
    "evidence_annex.html",
    "export_manifest.json",
    "report_bundle_manifest.json",
}


class ReportExportError(Exception):
    """Base export error."""


class ReportExportNotFound(ReportExportError):
    """Report or export does not exist."""


class ReportExportConflict(ReportExportError):
    """Report is not ready for export."""


class ReportExportInvalidPath(ReportExportError):
    """Requested export path is unsafe."""


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_report_markdown(report_id: str, fallback: str) -> str:
    path = Path(ReportManager._get_report_markdown_path(report_id))
    if path.is_file():
        return path.read_text(encoding="utf-8")
    return fallback or ""


def _safe_child(base: Path, name: str) -> Path:
    if not name or os.path.isabs(name) or Path(name).name != name or ".." in Path(name).parts:
        raise ReportExportInvalidPath(f"Unsafe export path: {name}")
    target = (base / name).resolve()
    if target.parent != base.resolve():
        raise ReportExportInvalidPath(f"Unsafe export path: {name}")
    return target


def _exports_root(report_id: str) -> Path:
    report_folder = Path(ReportManager._get_report_folder(report_id)).resolve()
    root = (report_folder / "exports").resolve()
    if report_folder not in root.parents:
        raise ReportExportInvalidPath("Unsafe exports root")
    return root


def resolve_export_dir(report_id: str, export_id: str) -> Path:
    root = _exports_root(report_id)
    if not export_id or os.path.isabs(export_id) or Path(export_id).name != export_id or ".." in Path(export_id).parts:
        raise ReportExportInvalidPath(f"Unsafe export id: {export_id}")
    export_dir = (root / export_id).resolve()
    if export_dir.parent != root.resolve():
        raise ReportExportInvalidPath(f"Unsafe export id: {export_id}")
    return export_dir


def resolve_export_file(report_id: str, export_id: str, filename: str) -> Path:
    export_dir = resolve_export_dir(report_id, export_id)
    return _safe_child(export_dir, filename)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    return data if isinstance(data, dict) else {"items": data}


def _public_export_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in manifest.items() if key != "internal_path"}


def _evidence_annex_markdown(report_id: str) -> str:
    evidence_audit = ReportManager.load_json_artifact(report_id, "evidence_audit.json")
    if not evidence_audit:
        report = ReportManager.get_report(report_id)
        evidence_audit = report.evidence_audit if report else None
    payload = json.dumps(evidence_audit or {}, ensure_ascii=False, indent=2)
    return f"# Evidence Annex\n\n```json\n{payload}\n```"


def create_report_export(report_id: str) -> dict[str, Any]:
    """Create a deterministic HTML export draft with hash manifests."""
    report = ReportManager.get_report(report_id)
    if not report:
        raise ReportExportNotFound(f"Relatorio nao encontrado: {report_id}")
    if not report.is_publishable():
        raise ReportExportConflict("Relatorio ainda nao e publicavel para exportacao.")

    checklist = evaluate_report_method_checklist(report_id)
    if checklist.get("hard_checks_pass") is not True:
        raise ReportExportConflict("Checklist metodologico bloqueou a exportacao.")

    export_id = f"export_{uuid.uuid4().hex[:12]}"
    export_dir = resolve_export_dir(report_id, export_id)
    export_dir.mkdir(parents=True, exist_ok=False)

    full_result = render_safe_markdown(_read_report_markdown(report_id, report.markdown_content))
    evidence_result = render_safe_markdown(_evidence_annex_markdown(report_id))

    _safe_child(export_dir, "full_report.html").write_text(
        render_inteia_report_html(
            title="Relatorio MiroFish",
            subtitle=report.simulation_requirement,
            body_html=full_result.html,
            metadata={
                "Report ID": report_id,
                "Simulation ID": report.simulation_id,
                "Export ID": export_id,
            },
        ),
        encoding="utf-8",
    )
    _safe_child(export_dir, "evidence_annex.html").write_text(
        render_inteia_report_html(
            title="Anexo de Evidencias MiroFish",
            subtitle="Artefatos auditaveis associados ao relatorio.",
            body_html=evidence_result.html,
            metadata={
                "Report ID": report_id,
                "Simulation ID": report.simulation_id,
                "Export ID": export_id,
            },
        ),
        encoding="utf-8",
    )

    files = []
    for filename in sorted(["full_report.html", "evidence_annex.html"]):
        path = _safe_child(export_dir, filename)
        files.append({
            "filename": filename,
            "sha256": _sha256_file(path),
            "size": path.stat().st_size,
        })

    bundle_manifest = {
        "schema": "mirofish.report_bundle_manifest.v1",
        "report_id": report_id,
        "export_id": export_id,
        "generated_at": _now_iso(),
        "expected_files": sorted(EXPORT_FILENAMES),
        "files": files,
        "renderer_metadata": {
            "full_report.html": inteia_renderer_metadata(full_result.metadata),
            "evidence_annex.html": inteia_renderer_metadata(evidence_result.metadata),
        },
    }
    _write_json(_safe_child(export_dir, "report_bundle_manifest.json"), bundle_manifest)

    for filename in ["report_bundle_manifest.json"]:
        path = _safe_child(export_dir, filename)
        files.append({
            "filename": filename,
            "sha256": _sha256_file(path),
            "size": path.stat().st_size,
        })

    export_manifest = {
        "schema": "mirofish.report_export_manifest.v1",
        "report_id": report_id,
        "simulation_id": report.simulation_id,
        "export_id": export_id,
        "status": "draft",
        "created_at": _now_iso(),
        "files": files,
        "download_filenames": sorted(EXPORT_FILENAMES),
        "internal_path": str(export_dir),
    }
    _write_json(_safe_child(export_dir, "export_manifest.json"), export_manifest)

    return _public_export_manifest(export_manifest)


def list_report_exports(report_id: str) -> list[dict[str, Any]]:
    if not ReportManager.get_report(report_id):
        raise ReportExportNotFound(f"Relatorio nao encontrado: {report_id}")

    root = _exports_root(report_id)
    if not root.is_dir():
        return []

    exports = []
    for child in sorted(root.iterdir(), key=lambda item: item.name):
        if not child.is_dir():
            continue
        manifest_path = child / "export_manifest.json"
        if not manifest_path.is_file():
            continue
        exports.append(_public_export_manifest(_read_json(manifest_path)))
    exports.sort(key=lambda item: item.get("created_at", ""), reverse=True)
    return exports


def load_export_manifest(report_id: str, export_id: str) -> dict[str, Any]:
    if not ReportManager.get_report(report_id):
        raise ReportExportNotFound(f"Relatorio nao encontrado: {report_id}")
    manifest_path = resolve_export_file(report_id, export_id, "export_manifest.json")
    if not manifest_path.is_file():
        raise ReportExportNotFound(f"Exportacao nao encontrada: {export_id}")
    return _read_json(manifest_path)


def allowed_export_file_path(report_id: str, export_id: str, filename: str) -> Path:
    manifest = load_export_manifest(report_id, export_id)
    if filename not in set(manifest.get("download_filenames") or []):
        raise ReportExportInvalidPath(f"Arquivo nao permitido: {filename}")
    path = resolve_export_file(report_id, export_id, filename)
    if not path.is_file():
        raise ReportExportNotFound(f"Arquivo nao encontrado: {filename}")
    return path
