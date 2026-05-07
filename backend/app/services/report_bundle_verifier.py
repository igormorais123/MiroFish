"""Verification for generated report export bundles."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .report_agent import ReportManager
from .report_exporter import (
    EXPORT_FILENAMES,
    ReportExportInvalidPath,
    ReportExportNotFound,
    resolve_export_dir,
    resolve_export_file,
)
from .safe_markdown_renderer import RENDERER_NAME, RENDERER_VERSION

VERIFICATION_FILENAME = "report_bundle_verification.json"
ALLOWED_BUNDLE_FILENAMES = EXPORT_FILENAMES | {VERIFICATION_FILENAME}


class ReportBundleVerificationError(Exception):
    """Base verification error."""


class ReportBundleVerificationNotFound(ReportBundleVerificationError):
    """Report or export bundle is missing."""


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    return data if isinstance(data, dict) else {"items": data}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _check(check_id: str, passes: bool, message: str) -> dict[str, Any]:
    return {"id": check_id, "passes": passes, "message": message}


def _safe_manifest_filename(filename: Any) -> bool:
    if not isinstance(filename, str) or not filename:
        return False
    try:
        resolve_export_file("placeholder", "placeholder", filename)
    except ReportExportInvalidPath:
        return False
    return True


def _renderer_metadata_passes(metadata: Any) -> bool:
    if not isinstance(metadata, dict):
        return False
    return (
        metadata.get("renderer") == RENDERER_NAME
        and metadata.get("version") == RENDERER_VERSION
        and metadata.get("raw_html_escaped") is True
    )


def verify_report_export_bundle(report_id: str, export_id: str) -> dict[str, Any]:
    """Verify path safety, expected files, hashes, and renderer metadata."""
    if not ReportManager.get_report(report_id):
        raise ReportBundleVerificationNotFound(f"Relatorio nao encontrado: {report_id}")

    try:
        export_dir = resolve_export_dir(report_id, export_id)
    except ReportExportInvalidPath as exc:
        result = _result(report_id, export_id, [_check("export_path_safe", False, str(exc))])
        ReportManager.save_json_artifact(report_id, "report_bundle_verification.json", result)
        return result

    if not export_dir.is_dir():
        raise ReportBundleVerificationNotFound(f"Exportacao nao encontrada: {export_id}")

    checks: list[dict[str, Any]] = [_check("export_path_safe", True, "Export path is inside report exports root.")]

    bundle_manifest_path = export_dir / "report_bundle_manifest.json"
    export_manifest_path = export_dir / "export_manifest.json"
    if not bundle_manifest_path.is_file() or not export_manifest_path.is_file():
        missing = [
            name for name, path in {
                "report_bundle_manifest.json": bundle_manifest_path,
                "export_manifest.json": export_manifest_path,
            }.items()
            if not path.is_file()
        ]
        checks.append(_check("manifest_files_present", False, f"Missing manifest files: {', '.join(missing)}"))
        result = _result(report_id, export_id, checks)
        return _persist_result(report_id, export_dir, result)

    bundle_manifest = _read_json(bundle_manifest_path)
    export_manifest = _read_json(export_manifest_path)

    expected_files = list(bundle_manifest.get("expected_files") or [])
    manifest_files = [item.get("filename") for item in bundle_manifest.get("files") or []]
    export_files = [item.get("filename") for item in export_manifest.get("files") or []]
    all_manifest_files = set(expected_files + manifest_files + export_files + [
        "report_bundle_manifest.json",
        "export_manifest.json",
    ])

    unsafe_names = [name for name in all_manifest_files if not _safe_manifest_filename(name)]
    checks.append(_check(
        "manifest_paths_safe",
        not unsafe_names,
        "All manifest file paths are safe." if not unsafe_names else f"Unsafe manifest file paths: {unsafe_names}",
    ))

    actual_files = sorted(path.name for path in export_dir.iterdir() if path.is_file())
    unexpected = sorted(set(actual_files) - ALLOWED_BUNDLE_FILENAMES)
    checks.append(_check(
        "no_unexpected_files",
        not unexpected,
        "No unexpected files found." if not unexpected else f"Unexpected files found: {unexpected}",
    ))

    required = set(expected_files) | {"report_bundle_manifest.json", "export_manifest.json"}
    missing = sorted(name for name in required if _safe_manifest_filename(name) and not (export_dir / name).is_file())
    checks.append(_check(
        "expected_files_present",
        not missing,
        "All expected files are present." if not missing else f"Missing expected files: {missing}",
    ))

    hash_failures = []
    for item in bundle_manifest.get("files") or []:
        filename = item.get("filename")
        expected_hash = item.get("sha256")
        if not _safe_manifest_filename(filename):
            continue
        path = export_dir / filename
        if not path.is_file():
            continue
        if expected_hash != _sha256_file(path):
            hash_failures.append(filename)
    checks.append(_check(
        "hashes_match",
        not hash_failures,
        "All file hashes match." if not hash_failures else f"Hash mismatch: {hash_failures}",
    ))

    renderer_metadata = bundle_manifest.get("renderer_metadata") or {}
    renderer_failures = [
        filename for filename in expected_files
        if filename.endswith(".html") and not _renderer_metadata_passes(renderer_metadata.get(filename))
    ]
    checks.append(_check(
        "renderer_metadata_present",
        not renderer_failures,
        "Safe renderer metadata present for HTML files."
        if not renderer_failures
        else f"Missing or invalid renderer metadata: {renderer_failures}",
    ))

    result = _result(report_id, export_id, checks)
    return _persist_result(report_id, export_dir, result)


def _persist_result(report_id: str, export_dir: Path, result: dict[str, Any]) -> dict[str, Any]:
    _write_json(export_dir / VERIFICATION_FILENAME, result)
    ReportManager.save_json_artifact(report_id, "report_bundle_verification.json", result)
    return result


def _result(report_id: str, export_id: str, checks: list[dict[str, Any]]) -> dict[str, Any]:
    passes = all(item["passes"] is True for item in checks)
    return {
        "report_id": report_id,
        "export_id": export_id,
        "verified_at": _now_iso(),
        "passes": passes,
        "bundle_verified": passes,
        "checks": checks,
        "errors": [item["message"] for item in checks if item["passes"] is not True],
    }
