# Mirofish Auditable Executive Export Implementation Plan

> **Superseded execution order:** Start with `docs/superpowers/plans/2026-05-06-mirofish-systemic-intelligence-trio.md`. This export plan remains useful as source material for the HTML/export phase, but it should no longer be the first implementation entrypoint.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

> **Prerequisite:** Execute `docs/superpowers/plans/2026-05-06-mirofish-ralph-openswarm-autoresearch-trio.md` first. The export implementation should then run as small Ralph units, not as one large uncontrolled implementation session.

**Goal:** Build the first OpenSwarm-inspired Mirofish improvement: turn an approved audited report into a versioned executive export package with HTML source, optional PDF output, and manifest hashes.

**Architecture:** Keep Mirofish's current intelligence as the source of truth: `ReportManager`, delivery gate, evidence audit, mission bundle, forecast ledger, and cost artifacts. Add a focused `report_exporter.py` service that reads an existing report folder, renders deterministic HTML, exports files under `reports/<report_id>/exports/<export_id>/`, writes a per-export `manifest.json`, and saves `export_manifest.json` as the latest-export pointer. Add thin API routes and UI buttons only after the service is tested.

**Tech Stack:** Python 3.11/3.12, Flask, pytest, current Mirofish services, `uv`/`pyproject.toml` dependency management, Mistune for safe Markdown-to-HTML rendering, optional WeasyPrint for PDF, Vue 3/Vite for the report UI.

---

## Source Context

- OpenSwarm commit studied: `92c8062bfeb58a9e96db8b7ac72da5f95c33479e`.
- Local opportunity memo: `docs/openswarm_mirofish_opportunities_2026-05-06.md`.
- Existing Mirofish report artifacts:
  - `backend/app/services/report_agent.py`
  - `backend/app/services/mission_bundle.py`
  - `backend/app/services/forecast_ledger.py`
  - `backend/app/utils/report_quality.py`
  - `backend/app/api/report.py`
  - `frontend/src/components/Step4Report.vue`

## Scope

### In First PR

- Add deterministic HTML executive export.
- Add PDF export path and dependency handling, with HTML remaining the stable fallback if PDF dependencies are unavailable.
- Save `export_manifest.json` with hashes and file metadata.
- Block client/public exports unless `report.delivery_status() == "publishable"`.
- Allow diagnostic export only when explicitly requested with `allow_diagnostic=true`, and stamp the export visibly as diagnostic.
- Add API endpoints to create/list/download exports.
- Add minimal UI actions in Step 4.

### Not In First PR

- PPTX deck generation.
- OpenSwarm runtime or Agency Swarm dependency.
- LLM-based rewriting of the report.
- Browser screenshot QA.
- New simulation run.
- Apify/Graphiti/OASIS changes.

## File Structure

### Create

- `backend/app/services/report_exporter.py`  
  Owns export contracts, HTML rendering, PDF writing, manifest hashing, and export listing.

- `backend/tests/test_report_exporter.py`  
  Unit tests for publishability policy, HTML contents, manifest hashes, file layout, and dependency failure.

- `backend/tests/test_report_export_api.py`  
  API-level tests for export creation, listing, download, not-found, and blocked report responses.

### Modify

- `backend/app/api/report.py`  
  Add `POST /api/report/<report_id>/export`, `GET /api/report/<report_id>/exports`, and `GET /api/report/<report_id>/exports/<export_id>/<filename>`.

- `backend/pyproject.toml`  
  Add `mistune>=3.0.2` for safe Markdown rendering. Add `weasyprint>=62.3` only if PDF export is implemented server-side in this PR.

- `backend/uv.lock`  
  Refresh with `uv lock` after dependency changes.

- `backend/requirements.txt`  
  Update only if the legacy pip install path is still intentionally maintained. Docker and `npm run setup:backend` use `backend/pyproject.toml`.

- `frontend/src/api/report.js`  
  Add API helpers for export create/list/download.

- `frontend/src/components/Step4Report.vue`  
  Add export controls and status display in the existing report/custody panel.

## Implementation Guardrails From Plan Review

- Generate `export_id` with UTC timestamp plus random suffix, for example `export_20260506T150102Z_ab12cd34`. Seconds-only timestamps can collide in fast tests and repeated clicks.
- Store files under `reports/<report_id>/exports/<export_id>/`.
- Write a `manifest.json` inside each export folder. `export_manifest.json` in the report root is only the latest-export pointer for the existing artifacts API.
- Do not expose absolute server paths in API responses or persisted manifests. Service internals may keep `internal_path` for tests, but public payloads must use `relative_path`, `name`, `kind`, `size`, and `sha256`.
- Use a real Markdown renderer with escaping enabled. Do not hand-roll Markdown parsing beyond tiny formatting helpers; report tables, lists, links, and escaped raw HTML need consistent behavior.
- Download route must include `export_id`: `GET /api/report/<report_id>/exports/<export_id>/<filename>`. Searching by filename across all export folders is ambiguous and can return the wrong version.
- Path traversal must be blocked by checking both `export_id` and `filename` with `os.path.basename(...)` and by resolving the final path under the selected export directory.
- Dependency changes must update `backend/pyproject.toml` and `backend/uv.lock`. Updating only `backend/requirements.txt` is insufficient for this repo.
- If WeasyPrint installation fails on Windows/native libraries, do not weaken the export. Keep HTML export and API dependency failure behavior, then split PDF rendering into a follow-up plan.

---

## Task 1: Service Contract And Policy Tests

**Files:**
- Create: `backend/app/services/report_exporter.py`
- Create: `backend/tests/test_report_exporter.py`

- [ ] **Step 1: Write failing tests for export policy**

Add this to `backend/tests/test_report_exporter.py`:

```python
"""Tests for audited report export package generation."""
from __future__ import annotations

from pathlib import Path

import pytest

from app.services.report_agent import Report, ReportManager, ReportStatus
from app.services.report_exporter import (
    ExportBlockedError,
    ReportExporter,
)


def _completed_report(**overrides):
    data = {
        "report_id": "report_1",
        "simulation_id": "sim_1",
        "graph_id": "graph_1",
        "simulation_requirement": "Avaliar cenario institucional",
        "status": ReportStatus.COMPLETED,
        "markdown_content": "# Relatorio\n\n## Resumo\n\nConteudo auditavel.",
        "quality_gate": {"passes_gate": True, "metrics": {"delivery_mode": "client"}},
        "evidence_audit": {"passes_gate": True, "quotes_total": 0, "numbers_total": 0},
    }
    data.update(overrides)
    return Report(**data)


def test_exporter_blocks_legacy_unverified_report(tmp_path, monkeypatch):
    monkeypatch.setattr(ReportManager, "REPORTS_DIR", str(tmp_path / "reports"))
    report = _completed_report(quality_gate=None, evidence_audit=None)
    ReportManager.save_report(report)

    with pytest.raises(ExportBlockedError) as exc:
        ReportExporter().export_report("report_1", output_format="html")

    assert "legacy_unverified" in str(exc.value)


def test_exporter_blocks_diagnostic_report_without_explicit_allow(tmp_path, monkeypatch):
    monkeypatch.setattr(ReportManager, "REPORTS_DIR", str(tmp_path / "reports"))
    report = _completed_report(
        quality_gate={
            "passes_gate": True,
            "metrics": {
                "delivery_mode": "demo",
                "delivery_publishable_mode": False,
                "diagnostic_only": True,
            },
        }
    )
    ReportManager.save_report(report)

    with pytest.raises(ExportBlockedError) as exc:
        ReportExporter().export_report("report_1", output_format="html")

    assert "diagnostic_only" in str(exc.value)
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
.\backend\.venv\Scripts\python.exe -m pytest backend\tests\test_report_exporter.py -q
```

Expected:

```text
ModuleNotFoundError: No module named 'app.services.report_exporter'
```

- [ ] **Step 3: Add minimal service contract**

Create `backend/app/services/report_exporter.py`:

```python
"""Audited export package builder for completed Mirofish reports."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from .report_agent import Report, ReportManager


ExportFormat = Literal["html", "pdf"]


class ExportError(RuntimeError):
    """Base error for report export failures."""


class ExportNotFoundError(ExportError):
    """Raised when the report does not exist."""


class ExportBlockedError(ExportError):
    """Raised when governance does not allow an export."""


class ExportDependencyError(ExportError):
    """Raised when an optional export dependency is missing."""


@dataclass(frozen=True)
class ExportResult:
    report_id: str
    export_id: str
    output_format: str
    files: list[dict]
    manifest: dict


class ReportExporter:
    """Creates deterministic client-facing exports from audited report artifacts."""

    def export_report(
        self,
        report_id: str,
        *,
        output_format: ExportFormat = "pdf",
        allow_diagnostic: bool = False,
    ) -> ExportResult:
        report = ReportManager.get_report(report_id)
        if not report:
            raise ExportNotFoundError(f"Relatorio nao encontrado: {report_id}")
        self._assert_export_allowed(report, allow_diagnostic=allow_diagnostic)
        raise NotImplementedError("Export rendering is implemented in Task 2")

    def _assert_export_allowed(self, report: Report, *, allow_diagnostic: bool) -> None:
        status = report.delivery_status()
        if status == "publishable":
            return
        if allow_diagnostic and status == "diagnostic_only":
            return
        raise ExportBlockedError(
            f"Export bloqueado: delivery_status={status}. "
            "Use allow_diagnostic=true somente para export interno diagnostico."
        )

    def _report_folder(self, report_id: str) -> Path:
        return Path(ReportManager._get_report_folder(report_id))
```

- [ ] **Step 4: Run tests to verify policy passes**

Run:

```powershell
.\backend\.venv\Scripts\python.exe -m pytest backend\tests\test_report_exporter.py -q
```

Expected:

```text
2 passed
```

- [ ] **Step 5: Commit**

```powershell
git add backend/app/services/report_exporter.py backend/tests/test_report_exporter.py
git commit -m "feat: add report export governance contract"
```

---

## Task 2: HTML Source Export

**Files:**
- Modify: `backend/app/services/report_exporter.py`
- Modify: `backend/tests/test_report_exporter.py`
- Modify: `backend/pyproject.toml`
- Modify: `backend/uv.lock`

- [ ] **Step 1: Write failing HTML export test**

Append to `backend/tests/test_report_exporter.py`:

```python
def test_exporter_creates_html_source_with_required_blocks(tmp_path, monkeypatch):
    monkeypatch.setattr(ReportManager, "REPORTS_DIR", str(tmp_path / "reports"))
    report = _completed_report(
        markdown_content=(
            "# Relatorio Helena\n\n"
            "> Sintese executiva.\n\n"
            "## Cenarios\n\n"
            "| Cenario | Probabilidade |\n"
            "| --- | --- |\n"
            "| Base | 60% [inferencia calibrada] |\n"
        )
    )
    ReportManager.save_report(report)
    ReportManager.save_json_artifact("report_1", "evidence_audit.json", {
        "passes_gate": True,
        "quotes_total": 0,
        "numbers_total": 1,
        "numbers_labeled_inference": 1,
    })
    ReportManager.save_json_artifact("report_1", "mission_bundle.json", {
        "hashes": {"manifesto": "abc123"},
        "previsoes_congeladas": [],
    })

    result = ReportExporter().export_report("report_1", output_format="html")

    html_file = Path(result.files[0]["internal_path"])
    assert html_file.name == "report_1.source.html"
    html = html_file.read_text(encoding="utf-8")
    assert "Relatorio Helena" in html
    assert "Cadeia de custodia" in html
    assert "Auditoria de evidencias" in html
    assert "abc123" in html
    assert "diagnostic_only" not in html
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
.\backend\.venv\Scripts\python.exe -m pytest backend\tests\test_report_exporter.py::test_exporter_creates_html_source_with_required_blocks -q
```

Expected:

```text
NotImplementedError: Export rendering is implemented in Task 2
```

- [ ] **Step 3: Add Markdown dependency**

Add this to the dependency list in `backend/pyproject.toml`:

```toml
"mistune>=3.0.2",
```

Refresh the lockfile and local environment before running the next test:

```powershell
Set-Location backend
uv lock
uv sync --dev
Set-Location ..
```

- [ ] **Step 4: Implement HTML rendering and file layout**

Replace `export_report()` in `backend/app/services/report_exporter.py` and add helpers:

```python
import hashlib
import html
import json
import uuid
from datetime import datetime, timezone

import mistune


def _new_export_id() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"export_{stamp}_{uuid.uuid4().hex[:8]}"


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _safe_text(value) -> str:
    return html.escape("" if value is None else str(value))


class ReportExporter:
    """Creates deterministic client-facing exports from audited report artifacts."""

    def export_report(
        self,
        report_id: str,
        *,
        output_format: ExportFormat = "pdf",
        allow_diagnostic: bool = False,
    ) -> ExportResult:
        report = ReportManager.get_report(report_id)
        if not report:
            raise ExportNotFoundError(f"Relatorio nao encontrado: {report_id}")
        self._assert_export_allowed(report, allow_diagnostic=allow_diagnostic)

        export_id = _new_export_id()
        export_dir = self._report_folder(report_id) / "exports" / export_id
        export_dir.mkdir(parents=True, exist_ok=True)

        html_path = export_dir / f"{report_id}.source.html"
        html_path.write_text(
            self.build_html(report, allow_diagnostic=allow_diagnostic),
            encoding="utf-8",
        )

        files = [self._file_entry(html_path, kind="html_source", report_id=report_id)]
        manifest = self._build_manifest(
            report=report,
            export_id=export_id,
            output_format=output_format,
            files=files,
            allow_diagnostic=allow_diagnostic,
        )
        (export_dir / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        ReportManager.save_json_artifact(report_id, "export_manifest.json", manifest)

        return ExportResult(
            report_id=report_id,
            export_id=export_id,
            output_format=output_format,
            files=files,
            manifest=manifest,
        )

    def build_html(self, report: Report, *, allow_diagnostic: bool) -> str:
        gate = report.quality_gate or {}
        audit = report.evidence_audit or {}
        mission_bundle = ReportManager.load_json_artifact(report.report_id, "mission_bundle.json") or {}
        forecast_ledger = ReportManager.load_json_artifact(report.report_id, "forecast_ledger.json") or {}
        cost_meter = ReportManager.load_json_artifact(report.report_id, "cost_meter.json") or {}

        diagnostic_banner = ""
        if report.delivery_status() == "diagnostic_only":
            diagnostic_banner = (
                '<div class="banner diagnostic">'
                'Export diagnostico interno: diagnostic_only. Nao publicavel para cliente.'
                '</div>'
            )

        report_body = self._markdown_to_html(report.markdown_content or "")
        return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <title>{_safe_text(report.report_id)} - Export Mirofish</title>
  <style>
    @page {{ size: A4; margin: 18mm 16mm 20mm 16mm; }}
    body {{ font-family: Arial, sans-serif; color: #18202a; line-height: 1.45; }}
    .header {{ border-bottom: 3px solid #0f766e; padding-bottom: 12px; margin-bottom: 18px; }}
    .kicker {{ color: #0f766e; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0; }}
    h1 {{ font-size: 26px; margin: 8px 0; }}
    h2 {{ color: #0f766e; border-bottom: 1px solid #d8e3e0; padding-bottom: 4px; margin-top: 22px; }}
    table {{ border-collapse: collapse; width: 100%; margin: 12px 0; font-size: 12px; }}
    th, td {{ border: 1px solid #cbd5d1; padding: 7px; text-align: left; vertical-align: top; }}
    th {{ background: #eef7f5; }}
    .banner {{ padding: 10px 12px; margin: 12px 0; border: 1px solid #d97706; background: #fff7ed; }}
    .meta-grid {{ width: 100%; border-collapse: collapse; }}
    .meta-grid td {{ width: 50%; }}
    .mono {{ font-family: Consolas, monospace; font-size: 11px; }}
  </style>
</head>
<body>
  <div class="header">
    <div class="kicker">Mirofish INTEIA - Pacote executivo auditavel</div>
    <h1>{_safe_text(report.report_id)}</h1>
    <p>Simulacao: <span class="mono">{_safe_text(report.simulation_id)}</span></p>
    <p>Status de entrega: <strong>{_safe_text(report.delivery_status())}</strong></p>
  </div>
  {diagnostic_banner}
  <main>{report_body}</main>
  <h2>Cadeia de custodia</h2>
  <table class="meta-grid">
    <tr><td>Graph ID</td><td class="mono">{_safe_text(report.graph_id)}</td></tr>
    <tr><td>Mission bundle hash</td><td class="mono">{_safe_text((mission_bundle.get("hashes") or {}).get("manifesto", ""))}</td></tr>
    <tr><td>Gate estrutural</td><td>{_safe_text(gate.get("passes_gate"))}</td></tr>
    <tr><td>Custo tecnico</td><td>{_safe_text(cost_meter.get("cost_brl", cost_meter.get("api_reference_brl", "")))}</td></tr>
  </table>
  <h2>Auditoria de evidencias</h2>
  <table>
    <tr><th>Metrica</th><th>Valor</th></tr>
    <tr><td>Gate</td><td>{_safe_text(audit.get("passes_gate"))}</td></tr>
    <tr><td>Citacoes sustentadas</td><td>{_safe_text(audit.get("quotes_supported", 0))}/{_safe_text(audit.get("quotes_total", 0))}</td></tr>
    <tr><td>Numeros sem suporte</td><td>{_safe_text(audit.get("numbers_unsupported", 0))}</td></tr>
    <tr><td>Previsoes congeladas</td><td>{_safe_text(len(forecast_ledger.get("previsoes", [])))}</td></tr>
  </table>
</body>
</html>
"""

    def _markdown_to_html(self, markdown_text: str) -> str:
        renderer = mistune.create_markdown(escape=True, plugins=["table", "strikethrough"])
        return renderer(markdown_text or "")

    def _file_entry(self, path: Path, *, kind: str, report_id: str) -> dict:
        report_folder = self._report_folder(report_id).resolve()
        resolved_path = path.resolve()
        relative_path = resolved_path.relative_to(report_folder).as_posix()
        return {
            "kind": kind,
            "name": path.name,
            "relative_path": relative_path,
            "internal_path": str(path),
            "size": path.stat().st_size,
            "sha256": _sha256_file(path),
        }

    def _public_file_entry(self, entry: dict) -> dict:
        return {
            key: entry[key]
            for key in ("kind", "name", "relative_path", "size", "sha256")
            if key in entry
        }

    def _build_manifest(
        self,
        *,
        report: Report,
        export_id: str,
        output_format: str,
        files: list[dict],
        allow_diagnostic: bool,
    ) -> dict:
        return {
            "report_id": report.report_id,
            "simulation_id": report.simulation_id,
            "export_id": export_id,
            "output_format": output_format,
            "delivery_status": report.delivery_status(),
            "allow_diagnostic": allow_diagnostic,
            "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            "files": [self._public_file_entry(file) for file in files],
        }
```

- [ ] **Step 5: Run targeted tests**

Run:

```powershell
.\backend\.venv\Scripts\python.exe -m pytest backend\tests\test_report_exporter.py -q
```

Expected:

```text
3 passed
```

- [ ] **Step 6: Commit**

```powershell
git add backend/app/services/report_exporter.py backend/tests/test_report_exporter.py backend/pyproject.toml backend/uv.lock
git commit -m "feat: render audited report html export"
```

---

## Task 3: Manifest And Export Listing

**Files:**
- Modify: `backend/app/services/report_exporter.py`
- Modify: `backend/tests/test_report_exporter.py`

- [ ] **Step 1: Write failing tests for manifest and listing**

Append:

```python
def test_exporter_saves_manifest_and_lists_exports(tmp_path, monkeypatch):
    monkeypatch.setattr(ReportManager, "REPORTS_DIR", str(tmp_path / "reports"))
    report = _completed_report()
    ReportManager.save_report(report)

    result = ReportExporter().export_report("report_1", output_format="html")
    manifest = ReportManager.load_json_artifact("report_1", "export_manifest.json")
    exports = ReportExporter().list_exports("report_1")

    assert manifest["report_id"] == "report_1"
    assert manifest["delivery_status"] == "publishable"
    assert manifest["files"][0]["sha256"]
    assert result.manifest["files"][0]["sha256"] == manifest["files"][0]["sha256"]
    assert len(exports) == 1
    assert exports[0]["export_id"] == result.export_id
    assert exports[0]["files"][0]["name"] == "report_1.source.html"
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
.\backend\.venv\Scripts\python.exe -m pytest backend\tests\test_report_exporter.py::test_exporter_saves_manifest_and_lists_exports -q
```

Expected:

```text
AttributeError: 'ReportExporter' object has no attribute 'list_exports'
```

- [ ] **Step 3: Implement `list_exports()`**

Add to `ReportExporter`:

```python
    def list_exports(self, report_id: str) -> list[dict]:
        report = ReportManager.get_report(report_id)
        if not report:
            raise ExportNotFoundError(f"Relatorio nao encontrado: {report_id}")

        exports_dir = self._report_folder(report_id) / "exports"
        if not exports_dir.exists():
            return []

        items: list[dict] = []
        for export_dir in sorted(exports_dir.iterdir(), reverse=True):
            if not export_dir.is_dir():
                continue
            raw_files = [
                self._file_entry(path, kind=self._infer_kind(path), report_id=report_id)
                for path in sorted(export_dir.iterdir())
                if path.is_file() and path.name != "manifest.json"
            ]
            files = [self._public_file_entry(file) for file in raw_files]
            items.append({
                "report_id": report_id,
                "export_id": export_dir.name,
                "files": files,
            })
        return items

    def _infer_kind(self, path: Path) -> str:
        if path.name.endswith(".source.html"):
            return "html_source"
        if path.suffix.lower() == ".pdf":
            return "pdf"
        if path.suffix.lower() == ".jpg":
            return "preview"
        return "file"
```

- [ ] **Step 4: Run tests**

Run:

```powershell
.\backend\.venv\Scripts\python.exe -m pytest backend\tests\test_report_exporter.py -q
```

Expected:

```text
4 passed
```

- [ ] **Step 5: Commit**

```powershell
git add backend/app/services/report_exporter.py backend/tests/test_report_exporter.py
git commit -m "feat: list report export packages"
```

---

## Task 4: PDF Writer With Graceful Dependency Handling

**Files:**
- Modify: `backend/app/services/report_exporter.py`
- Modify: `backend/tests/test_report_exporter.py`
- Modify: `backend/pyproject.toml`
- Modify: `backend/uv.lock`
- Optional legacy modify: `backend/requirements.txt`

- [ ] **Step 1: Write failing tests for PDF output and missing dependency**

Append:

```python
def test_exporter_creates_pdf_with_injected_writer(tmp_path, monkeypatch):
    monkeypatch.setattr(ReportManager, "REPORTS_DIR", str(tmp_path / "reports"))
    report = _completed_report()
    ReportManager.save_report(report)

    def fake_pdf_writer(html_path, pdf_path):
        assert html_path.read_text(encoding="utf-8").startswith("<!DOCTYPE html>")
        pdf_path.write_bytes(b"%PDF-1.4 fake pdf")

    result = ReportExporter(pdf_writer=fake_pdf_writer).export_report("report_1", output_format="pdf")

    names = [item["name"] for item in result.files]
    assert "report_1.source.html" in names
    assert "report_1.pdf" in names


def test_exporter_reports_missing_pdf_dependency(tmp_path, monkeypatch):
    monkeypatch.setattr(ReportManager, "REPORTS_DIR", str(tmp_path / "reports"))
    report = _completed_report()
    ReportManager.save_report(report)

    def missing_writer(html_path, pdf_path):
        raise ExportDependencyError("weasyprint unavailable")

    with pytest.raises(ExportDependencyError):
        ReportExporter(pdf_writer=missing_writer).export_report("report_1", output_format="pdf")
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
.\backend\.venv\Scripts\python.exe -m pytest backend\tests\test_report_exporter.py::test_exporter_creates_pdf_with_injected_writer backend\tests\test_report_exporter.py::test_exporter_reports_missing_pdf_dependency -q
```

Expected:

```text
TypeError: ReportExporter() takes no arguments
```

- [ ] **Step 3: Implement PDF writer injection**

Modify `ReportExporter`:

```python
from collections.abc import Callable


PdfWriter = Callable[[Path, Path], None]


class ReportExporter:
    """Creates deterministic client-facing exports from audited report artifacts."""

    def __init__(self, pdf_writer: PdfWriter | None = None) -> None:
        self._pdf_writer = pdf_writer or self._write_pdf_with_weasyprint
```

Inside `export_report()`, after HTML file creation and before manifest:

```python
        if output_format == "pdf":
            pdf_path = export_dir / f"{report_id}.pdf"
            self._pdf_writer(html_path, pdf_path)
            files.append(self._file_entry(pdf_path, kind="pdf", report_id=report_id))
```

Add method:

```python
    def _write_pdf_with_weasyprint(self, html_path: Path, pdf_path: Path) -> None:
        try:
            from weasyprint import HTML
        except Exception as exc:
            raise ExportDependencyError(
                "PDF export requires WeasyPrint. Install backend dependency `weasyprint>=62.3`."
            ) from exc
        HTML(filename=str(html_path)).write_pdf(str(pdf_path))
```

- [ ] **Step 4: Add dependency**

Add this to the dependency list in `backend/pyproject.toml`:

```toml
"weasyprint>=62.3",
```

Then refresh the lockfile:

```powershell
Set-Location backend
uv lock
uv sync --dev
Set-Location ..
```

Only also update `backend/requirements.txt` if the legacy pip install path is still intentionally supported in the repo at implementation time.

- [ ] **Step 5: Run tests**

Run:

```powershell
.\backend\.venv\Scripts\python.exe -m pytest backend\tests\test_report_exporter.py -q
```

Expected:

```text
6 passed
```

- [ ] **Step 6: Commit**

```powershell
git add backend/app/services/report_exporter.py backend/tests/test_report_exporter.py backend/pyproject.toml backend/uv.lock
git commit -m "feat: add pdf report export writer"
```

---

## Task 5: Export API Endpoints

**Files:**
- Create: `backend/tests/test_report_export_api.py`
- Modify: `backend/app/api/report.py`

- [ ] **Step 1: Write failing API tests**

Create `backend/tests/test_report_export_api.py`:

```python
"""API tests for report exports."""
from __future__ import annotations

from app import create_app
from app.services.report_agent import Report, ReportManager, ReportStatus


def _save_publishable_report():
    report = Report(
        report_id="report_api_1",
        simulation_id="sim_api_1",
        graph_id="graph_api_1",
        simulation_requirement="Testar export API",
        status=ReportStatus.COMPLETED,
        markdown_content="# Relatorio API\n\nConteudo.",
        quality_gate={"passes_gate": True, "metrics": {"delivery_mode": "client"}},
        evidence_audit={"passes_gate": True},
    )
    ReportManager.save_report(report)
    return report


def test_create_html_export_api(tmp_path, monkeypatch):
    monkeypatch.setattr(ReportManager, "REPORTS_DIR", str(tmp_path / "reports"))
    _save_publishable_report()
    app = create_app()
    client = app.test_client()

    response = client.post("/api/report/report_api_1/export", json={"format": "html"})

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["success"] is True
    assert payload["data"]["report_id"] == "report_api_1"
    assert payload["data"]["files"][0]["name"] == "report_api_1.source.html"
    assert "internal_path" not in payload["data"]["files"][0]
    assert "internal_path" not in payload["data"]["manifest"]["files"][0]


def test_list_exports_api(tmp_path, monkeypatch):
    monkeypatch.setattr(ReportManager, "REPORTS_DIR", str(tmp_path / "reports"))
    _save_publishable_report()
    app = create_app()
    client = app.test_client()
    client.post("/api/report/report_api_1/export", json={"format": "html"})

    response = client.get("/api/report/report_api_1/exports")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["success"] is True
    assert len(payload["data"]["exports"]) == 1
    assert "internal_path" not in payload["data"]["exports"][0]["files"][0]


def test_download_export_api_returns_selected_export_file(tmp_path, monkeypatch):
    monkeypatch.setattr(ReportManager, "REPORTS_DIR", str(tmp_path / "reports"))
    _save_publishable_report()
    app = create_app()
    client = app.test_client()

    create_response = client.post("/api/report/report_api_1/export", json={"format": "html"})
    export_data = create_response.get_json()["data"]
    export_id = export_data["export_id"]
    filename = export_data["files"][0]["name"]

    response = client.get(f"/api/report/report_api_1/exports/{export_id}/{filename}")

    assert response.status_code == 200
    assert response.data.startswith(b"<!DOCTYPE html>")


def test_download_export_api_blocks_path_traversal(tmp_path, monkeypatch):
    monkeypatch.setattr(ReportManager, "REPORTS_DIR", str(tmp_path / "reports"))
    _save_publishable_report()
    app = create_app()
    client = app.test_client()

    create_response = client.post("/api/report/report_api_1/export", json={"format": "html"})
    export_id = create_response.get_json()["data"]["export_id"]

    response = client.get(f"/api/report/report_api_1/exports/{export_id}/..%2Fmeta.json")

    assert response.status_code in (400, 404)
```

- [ ] **Step 2: Run API tests to verify they fail**

Run:

```powershell
.\backend\.venv\Scripts\python.exe -m pytest backend\tests\test_report_export_api.py -q
```

Expected:

```text
404 NOT FOUND
```

- [ ] **Step 3: Add API imports**

Modify imports in `backend/app/api/report.py`:

```python
from pathlib import Path
from flask import request, jsonify, send_file
from ..services.report_exporter import (
    ExportBlockedError,
    ExportDependencyError,
    ExportNotFoundError,
    ReportExporter,
)
```

- [ ] **Step 4: Add create/list/download routes before the Markdown download route**

Add to `backend/app/api/report.py` before `@report_bp.route('/<report_id>/download', methods=['GET'])`:

```python
PUBLIC_EXPORT_FILE_KEYS = ("kind", "name", "relative_path", "size", "sha256")


def _public_export_file(file_entry: dict) -> dict:
    return {key: file_entry[key] for key in PUBLIC_EXPORT_FILE_KEYS if key in file_entry}


def _public_export_manifest(manifest: dict) -> dict:
    public_manifest = dict(manifest)
    public_manifest["files"] = [
        _public_export_file(file_entry)
        for file_entry in manifest.get("files", [])
    ]
    return public_manifest


def _public_export_result(result) -> dict:
    return {
        "report_id": result.report_id,
        "export_id": result.export_id,
        "output_format": result.output_format,
        "files": [_public_export_file(file_entry) for file_entry in result.files],
        "manifest": _public_export_manifest(result.manifest),
    }


def _public_export_package(export_item: dict) -> dict:
    return {
        **export_item,
        "files": [
            _public_export_file(file_entry)
            for file_entry in export_item.get("files", [])
        ],
    }


@report_bp.route('/<report_id>/export', methods=['POST'])
def create_report_export(report_id: str):
    """Criar pacote executivo exportavel para relatorio auditado."""
    try:
        data = request.get_json() or {}
        output_format = data.get("format", "pdf")
        allow_diagnostic = bool(data.get("allow_diagnostic", False))
        if output_format not in {"html", "pdf"}:
            return jsonify({
                "success": False,
                "error": "Formato de export invalido. Use html ou pdf.",
            }), 400

        result = ReportExporter().export_report(
            report_id,
            output_format=output_format,
            allow_diagnostic=allow_diagnostic,
        )
        return jsonify({
            "success": True,
            "data": _public_export_result(result),
        })
    except ExportNotFoundError as exc:
        return jsonify({"success": False, "error": str(exc)}), 404
    except ExportBlockedError as exc:
        return jsonify({"success": False, "error": str(exc)}), 409
    except ExportDependencyError as exc:
        return jsonify({"success": False, "error": str(exc)}), 503
    except Exception as e:
        logger.error(f"Falha ao exportar relatorio: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"success": False, "error": str(e)}), 500


@report_bp.route('/<report_id>/exports', methods=['GET'])
def list_report_exports(report_id: str):
    """Listar pacotes exportados do relatorio."""
    try:
        exports = [
            _public_export_package(export_item)
            for export_item in ReportExporter().list_exports(report_id)
        ]
        return jsonify({
            "success": True,
            "data": {
                "report_id": report_id,
                "exports": exports,
            },
        })
    except ExportNotFoundError as exc:
        return jsonify({"success": False, "error": str(exc)}), 404
    except Exception as e:
        logger.error(f"Falha ao listar exports do relatorio: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"success": False, "error": str(e)}), 500


@report_bp.route('/<report_id>/exports/<export_id>/<path:filename>', methods=['GET'])
def download_report_export(report_id: str, export_id: str, filename: str):
    """Baixar arquivo de export sem permitir path traversal."""
    try:
        safe_export_id = os.path.basename(export_id)
        safe_name = os.path.basename(filename)
        if safe_export_id != export_id or safe_name != filename:
            return jsonify({"success": False, "error": "Identificador de export invalido"}), 400

        report_folder = Path(ReportManager._get_report_folder(report_id)).resolve()
        exports_root = (report_folder / "exports").resolve()
        export_dir = (exports_root / safe_export_id).resolve()
        try:
            export_dir.relative_to(exports_root)
        except ValueError:
            return jsonify({"success": False, "error": "Identificador de export invalido"}), 400

        if not export_dir.is_dir():
            return jsonify({"success": False, "error": "Export nao encontrado"}), 404

        target = (export_dir / safe_name).resolve()
        try:
            target.relative_to(export_dir)
        except ValueError:
            return jsonify({"success": False, "error": "Nome de arquivo invalido"}), 400

        if not target.is_file():
            return jsonify({"success": False, "error": "Arquivo de export nao encontrado"}), 404
        return send_file(target, as_attachment=True, download_name=safe_name)
    except Exception as e:
        logger.error(f"Falha ao baixar export do relatorio: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"success": False, "error": str(e)}), 500
```

- [ ] **Step 5: Run API tests**

Run:

```powershell
.\backend\.venv\Scripts\python.exe -m pytest backend\tests\test_report_export_api.py -q
```

Expected:

```text
4 passed
```

- [ ] **Step 6: Commit**

```powershell
git add backend/app/api/report.py backend/tests/test_report_export_api.py
git commit -m "feat: expose audited report export api"
```

---

## Task 6: Frontend API Helpers

**Files:**
- Modify: `frontend/src/api/report.js`

- [ ] **Step 1: Add API helper functions**

Append to `frontend/src/api/report.js`:

```javascript
/**
 * Criar export executivo do relatorio
 * @param {string} reportId
 * @param {Object} payload - { format: 'html'|'pdf', allow_diagnostic?: boolean }
 */
export const createReportExport = (reportId, payload = {}) => {
  return service.post(`/api/report/${reportId}/export`, payload)
}

/**
 * Listar exports executivos do relatorio
 * @param {string} reportId
 */
export const listReportExports = (reportId) => {
  return service.get(`/api/report/${reportId}/exports`)
}

/**
 * Montar URL relativa de download de export
 * @param {string} reportId
 * @param {string} exportId
 * @param {string} filename
 */
export const reportExportDownloadUrl = (reportId, exportId, filename) => {
  const baseUrl = service.defaults.baseURL || ''
  return `${baseUrl}/api/report/${reportId}/exports/${encodeURIComponent(exportId)}/${encodeURIComponent(filename)}`
}
```

- [ ] **Step 2: Run frontend build**

Run:

```powershell
npm run build
```

Expected:

```text
vite build
✓ built
```

- [ ] **Step 3: Commit**

```powershell
git add frontend/src/api/report.js
git commit -m "feat: add report export api helpers"
```

---

## Task 7: Step 4 Export Controls

**Files:**
- Modify: `frontend/src/components/Step4Report.vue`

- [ ] **Step 1: Update import**

Change the existing import in `frontend/src/components/Step4Report.vue` from:

```javascript
import { getAgentLog, getConsoleLog, getReport, getReportArtifacts, getMissionBundle } from '../api/report'
```

to:

```javascript
import {
  getAgentLog,
  getConsoleLog,
  getReport,
  getReportArtifacts,
  getMissionBundle,
  createReportExport,
  listReportExports,
  reportExportDownloadUrl
} from '../api/report'
```

- [ ] **Step 2: Add state**

Near existing report/audit refs, add:

```javascript
const reportExports = ref([])
const exportBusy = ref(false)
const exportError = ref('')
```

- [ ] **Step 3: Add computed gate for export**

Near existing audit computed values, add:

```javascript
const canCreateClientExport = computed(() => {
  return reportRecord.value?.delivery_status === 'publishable'
})

const canCreateDiagnosticExport = computed(() => {
  return reportRecord.value?.delivery_status === 'diagnostic_only'
})
```

- [ ] **Step 4: Add export actions**

Add near `fetchReportAudit` helpers:

```javascript
const refreshReportExports = async () => {
  if (!props.reportId) return
  try {
    const res = await listReportExports(props.reportId)
    if (res.success && res.data) {
      reportExports.value = res.data.exports || []
    }
  } catch (err) {
    console.warn('Nao foi possivel listar exports', err)
  }
}

const createExecutiveExport = async (format = 'pdf') => {
  if (!props.reportId || exportBusy.value) return
  exportBusy.value = true
  exportError.value = ''
  try {
    const payload = {
      format,
      allow_diagnostic: canCreateDiagnosticExport.value
    }
    const res = await createReportExport(props.reportId, payload)
    if (res.success) {
      await refreshReportExports()
    }
  } catch (err) {
    exportError.value = err.message || 'Falha ao criar export'
  } finally {
    exportBusy.value = false
  }
}
```

- [ ] **Step 5: Call export refresh after audit fetch**

Inside `fetchReportAudit`, after artifacts/mission bundle logic, add:

```javascript
    await refreshReportExports()
```

- [ ] **Step 6: Reset export state when report changes**

In the watcher that resets `reportRecord`, add:

```javascript
    reportExports.value = []
    exportError.value = ''
    exportBusy.value = false
```

- [ ] **Step 7: Add template block**

Place this near the mission bundle / audit custody area:

```vue
<div v-if="reportRecord" class="export-panel">
  <div class="export-panel-header">
    <div>
      <div class="audit-kicker">Entrega executiva</div>
      <h3>Export auditavel</h3>
    </div>
    <div class="export-actions">
      <button
        class="export-button"
        :disabled="exportBusy || (!canCreateClientExport && !canCreateDiagnosticExport)"
        @click="createExecutiveExport('pdf')"
      >
        {{ exportBusy ? 'Gerando...' : 'Gerar PDF' }}
      </button>
      <button
        class="export-button secondary"
        :disabled="exportBusy || (!canCreateClientExport && !canCreateDiagnosticExport)"
        @click="createExecutiveExport('html')"
      >
        HTML
      </button>
    </div>
  </div>
  <p v-if="!canCreateClientExport && !canCreateDiagnosticExport" class="export-note">
    Export bloqueado ate o relatorio ficar publicavel ou diagnostico.
  </p>
  <p v-if="canCreateDiagnosticExport" class="export-note diagnostic">
    Export diagnostico interno. Nao publicavel para cliente.
  </p>
  <p v-if="exportError" class="export-error">{{ exportError }}</p>
  <div v-if="reportExports.length" class="export-list">
    <a
      v-for="file in reportExports[0].files"
      :key="`${reportExports[0].export_id}-${file.name}`"
      class="export-link"
      :href="reportExportDownloadUrl(props.reportId, reportExports[0].export_id, file.name)"
      target="_blank"
      rel="noopener"
    >
      {{ file.name }}
    </a>
  </div>
</div>
```

- [ ] **Step 8: Add compact styles**

Add to the style section:

```css
.export-panel {
  border: 1px solid rgba(15, 118, 110, 0.18);
  background: rgba(240, 253, 250, 0.72);
  padding: 16px;
  margin-top: 16px;
}

.export-panel-header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
}

.export-actions {
  display: flex;
  gap: 8px;
}

.export-button {
  border: 1px solid #0f766e;
  background: #0f766e;
  color: #fff;
  padding: 8px 12px;
  font-weight: 700;
  cursor: pointer;
}

.export-button.secondary {
  background: #fff;
  color: #0f766e;
}

.export-button:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.export-note,
.export-error {
  margin: 10px 0 0;
  font-size: 13px;
}

.export-note.diagnostic,
.export-error {
  color: #92400e;
}

.export-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}

.export-link {
  border: 1px solid rgba(15, 118, 110, 0.24);
  color: #0f766e;
  padding: 6px 9px;
  text-decoration: none;
  font-size: 13px;
  background: #fff;
}
```

- [ ] **Step 9: Run frontend build**

Run:

```powershell
npm run build
```

Expected:

```text
vite build
✓ built
```

- [ ] **Step 10: Commit**

```powershell
git add frontend/src/components/Step4Report.vue
git commit -m "feat: add audited export controls"
```

---

## Task 8: Full Backend Regression

**Files:**
- No source changes unless tests reveal a real bug.

- [ ] **Step 1: Run targeted backend tests**

Run:

```powershell
.\backend\.venv\Scripts\python.exe -m pytest backend\tests\test_report_exporter.py backend\tests\test_report_export_api.py backend\tests\test_report_manager_artifacts.py backend\tests\test_delivery_governance.py -q
```

Expected:

```text
all selected tests passed
```

- [ ] **Step 2: Run full backend suite**

Run:

```powershell
.\backend\.venv\Scripts\python.exe -m pytest backend\tests -q
```

Expected:

```text
all tests passed
```

- [ ] **Step 3: Run frontend build**

Run:

```powershell
npm run build
```

Expected:

```text
vite build
✓ built
```

- [ ] **Step 4: Run whitespace check**

Run:

```powershell
git diff --check
```

Expected:

```text
no output
```

- [ ] **Step 5: Commit verification notes if a doc update is needed**

Only if verification revealed an operational note, update `docs/openswarm_mirofish_opportunities_2026-05-06.md` with a short implementation note, then:

```powershell
git add docs/openswarm_mirofish_opportunities_2026-05-06.md
git commit -m "docs: record report export verification notes"
```

If no doc update is needed, do not commit anything in this task.

---

## Task 9: Follow-Up Plan For Visual QA

**Files:**
- Create: `docs/superpowers/plans/2026-05-06-mirofish-report-visual-quality.md`

- [ ] **Step 1: Create the next plan only after Task 8 passes**

Create a separate Superpowers plan for:

- `backend/app/services/report_visual_quality.py`
- Playwright or browser-based preview generation.
- `report_preview.jpg`.
- Checks for blank render, missing custody blocks, missing diagnostic warning, and wide tables.
- UI display of preview thumbnail.

- [ ] **Step 2: Keep visual QA out of the first PR**

Do not implement visual QA in the export PR. The first PR must stay focused on deterministic export and governance.

---

## Task 10: Follow-Up Plan For Deterministic Charts

**Files:**
- Create: `docs/superpowers/plans/2026-05-06-mirofish-deterministic-report-charts.md`

- [ ] **Step 1: Create chart plan after visual QA is scoped**

Create a separate plan for:

- `backend/app/services/report_chart_builder.py`
- action count by round;
- action type entropy;
- agent activity entropy;
- cost by phase;
- forecast ledger summary.

- [ ] **Step 2: Require local-data-only charts**

The chart builder must use only local artifacts and simulation metrics. No LLM-generated chart values.

---

## Self-Review

### Spec Coverage

- Export executive package: Tasks 1-5.
- HTML canonical source: Task 2.
- PDF output: Task 4.
- Manifest/hash: Task 3.
- Client/demo governance: Tasks 1 and 5.
- UI access: Tasks 6-7.
- Tests and verification: Task 8.
- Future visual QA/charts/deck separation: Tasks 9-10.

### Placeholder Scan

The first-PR tasks do not contain banned placeholder tokens or unspecified tests. Follow-up work is intentionally split into separate plans and is not a gap inside the export implementation.

### Type Consistency

- `ExportResult.report_id`, `export_id`, `output_format`, `files`, `manifest` are introduced in Task 1 and used consistently.
- `ReportExporter.export_report(report_id, output_format, allow_diagnostic)` is introduced in Task 1 and extended in Tasks 2-4.
- `ReportExporter.list_exports(report_id)` is introduced in Task 3 and used in Task 5.
- Frontend helpers use the same endpoint names as Task 5, including `export_id` in download URLs.

---

## Execution Options

Plan complete. Two execution options:

1. **Subagent-Driven (recommended)** - dispatch a fresh subagent per task, review between tasks, fast iteration.
2. **Inline Execution** - execute tasks in this session using `superpowers:executing-plans`, with checkpoints.
