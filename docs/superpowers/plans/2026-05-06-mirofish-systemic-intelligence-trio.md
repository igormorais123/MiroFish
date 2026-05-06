# Mirofish Systemic Intelligence Trio Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Improve Mirofish intelligence and user experience by turning its existing audited simulation/report artifacts into a clear, trustworthy delivery package, while using Ralph Loop as execution discipline, AutoResearch as method learning, and OpenSwarm only as a specialist-package pattern.

**Architecture:** Mirofish remains the product intelligence core: simulation, report gate, evidence audit, mission bundle, forecast ledger, cost meter, and UI custody trail. Ralph Loop stays outside the product as the small-unit execution cadence. AutoResearch reads runs and product artifacts to improve method and rubrics; OpenSwarm contributes controlled specialist handoff ideas only for composite deliverables such as research + data + report + deck.

**Tech Stack:** Python 3.11/3.12, Flask, pytest, Vue 3/Vite, existing `backend/autoresearch`, existing `.ralph` files, local JSON artifacts, deterministic HTML export, optional browser/Playwright verification for visual quality.

**GitHub/Branch Rule:** GitHub `origin/main` is the current source of truth for implementation. Codex must continue only on a named branch and must not work directly on `main`. Every implementation pass starts by syncing from GitHub, creating a `codex/<slug>` branch, and ending in a PR-ready diff.

---

## GitHub Operating Constraint

Before executing any implementation task from this plan, Codex must run the work from a branch based on GitHub `origin/main`.

Required start sequence:

```powershell
git fetch origin
git checkout main
git pull --ff-only origin main
git checkout -b codex/systemic-intelligence-trio
```

If the current worktree has unrelated local changes, use a separate worktree or a clean branch rather than mixing implementation with those changes. Do not push, commit, or merge directly to `main`; publish the branch and open a PR for review.

## Systemic Review

### Current Mirofish Strengths

- Report generation already has governance through `Report.delivery_status()`.
- The backend already writes strong audit artifacts: `system_gate.json`, `evidence_manifest.json`, `evidence_audit.json`, `cost_meter.json`, `forecast_ledger.json`, and `mission_bundle.json`.
- Step 4 already exposes custody, evidence, cost, and mission bundle state.
- The roadmap already points to "Exportacao executiva com anexo tecnico de evidencias" as P1.

### Current Mirofish Bottleneck

The user still has to infer the meaning of the intelligence from scattered status panels and Markdown. The system can already decide whether a report is `publishable`, `diagnostic_only`, blocked, or legacy, but it does not yet package that decision as a reusable executive deliverable with a clear "what can I do now?" answer.

### Useful OpenSwarm Lessons

Source studied: `https://github.com/VRSEN/OpenSwarm`, remote HEAD confirmed as `92c8062bfeb58a9e96db8b7ac72da5f95c33479e` on 2026-05-06.

Import the pattern, not the runtime:

- Orchestrator routes; specialists produce artifacts.
- Handoffs carry compressed usable context, not raw conversation dumps.
- HTML is the canonical layout source for docs/slides.
- Deliverables are versioned and file paths are first-class outputs.
- Visual/render checks catch broken exports before the user sees them.

### Useful Ralph Loop Lessons

Ralph must remain boring and reliable:

- one small unit;
- real verification;
- durable run files;
- learning;
- next action;
- stop.

Do not make Ralph a hidden autonomous product daemon. It is an engineering operating method.

### Useful AutoResearch Lessons

AutoResearch should not execute customer work. It should improve how work is done:

- score run quality;
- detect weak verification;
- detect vague next actions;
- detect weak handoffs;
- propose method patches;
- wait for human/executor application.

### Maximum Useful Integration

The maximum valuable integration without breaking Mirofish is:

```text
Mirofish product core
  -> delivery intelligence packet
  -> executive export package
  -> deterministic charts and visual QA

Ralph Loop
  -> small verified implementation units
  -> run evidence and handoff

AutoResearch
  -> scores Ralph/product method quality
  -> proposes patches after real runs

OpenSwarm pattern
  -> specialist lanes only for composite deliverables
  -> no runtime import
```

## Revised Decision

The previous direct export plan is useful but starts one step too far downstream. The first implementation should create a `delivery package` service that turns existing report intelligence into one product-facing object:

```text
Can this be delivered?
Why or why not?
Which artifacts support it?
What is the next best action?
Which exports are available?
```

Then HTML/PDF export builds on that package. This improves user experience immediately and lowers the risk of building a pretty export around a confusing report state.

## Scope

### First PR

- Add Ralph/OpenSwarm/AutoResearch guardrails only as lightweight method files.
- Add backend `report_delivery_packet.py`.
- Add API endpoint `GET /api/report/<report_id>/delivery-package`.
- Add Step 4 "Entrega inteligente" panel using the new packet.
- Add tests for publishable, diagnostic, blocked, and legacy states.

### Second PR

- Add canonical HTML export and per-export manifest using the delivery packet.
- Add download/list endpoints and UI buttons.
- Keep PDF optional until dependency validation is done locally.

### Third PR

- Add deterministic local charts from simulation/report artifacts.
- Add visual QA snapshot for generated HTML/export.
- Add AutoResearch baseline targets for Ralph method readiness and report delivery quality.

### Not In These PRs

- No OpenSwarm runtime import.
- No Agency Swarm dependency.
- No Composio integration.
- No autonomous long-running Ralph daemon.
- No automatic production patching by AutoResearch.
- No video/image agents.
- No deck generation before report/export quality is stable.

## File Structure

### Create

- `.ralph/SWARM.md`  
  Specialist-package policy for composite work.

- `backend/app/services/report_delivery_packet.py`  
  Consolidates report delivery status, blockers, warnings, artifact summary, mission bundle summary, export eligibility, and next action.

- `backend/tests/test_report_delivery_packet.py`  
  Unit tests for delivery packet policy.

- `backend/tests/test_report_delivery_packet_api.py`  
  API tests for the new endpoint.

- `backend/app/services/report_exporter.py`  
  Second PR service for HTML/export manifest.

- `backend/tests/test_report_exporter.py`  
  Second PR tests for export policy, HTML source, hashes, and path safety.

- `backend/app/services/report_chart_builder.py`  
  Third PR service for deterministic local charts.

- `backend/autoresearch/targets/report_delivery.py`  
  Zero-LLM AutoResearch target for delivery-package quality.

- `backend/autoresearch/targets/ralph_method.py`  
  Zero-LLM AutoResearch target for Ralph method readiness.

### Modify

- `.ralph/RALPH.md`
- `.ralph/LOOP.md`
- `.ralph/PM.md`
- `.ralph/AUTORESEARCH.md`
- `.ralph/TASK_TEMPLATE.md`
- `.ralph/VERIFY.md`
- `.ralph/METRICS.schema.json`
- `backend/app/api/report.py`
- `backend/autoresearch/cli.py`
- `frontend/src/api/report.js`
- `frontend/src/components/Step4Report.vue`

---

## Task 1: Ralph/Swarm Guardrails

**Files:**
- Create: `.ralph/SWARM.md`
- Modify: `.ralph/RALPH.md`
- Modify: `.ralph/PM.md`
- Modify: `.ralph/AUTORESEARCH.md`
- Modify: `.ralph/TASK_TEMPLATE.md`
- Modify: `.ralph/METRICS.schema.json`
- Modify: `.ralph/VERIFY.md`

- [ ] **Step 1: Create `.ralph/SWARM.md`**

Create the file with this content:

```markdown
# Ralph Composite Package Policy

Mirofish does not import OpenSwarm runtime. This file only defines when a Ralph task may use specialist-style handoffs.

## Rule

Use Ralph simple by default. Use a composite package only when one task requires two or more independently verifiable artifact types.

## Simple Ralph Fits

- One code change, test, prompt, document, gate, route, or UI state.
- Acceptance criteria fit in one verification command or one screenshot.
- Product decision is already clear.

## Composite Package Fits

- The task needs separate research, data, docs, slides, visual, or red-team outputs.
- Each output has a path and an acceptance criterion.
- `INTEGRATION.md` can prove the artifacts agree with each other.

## Specialist Lanes

- `executor`: code/docs change with direct verification.
- `research_intake`: read-only source study and context packet.
- `method_mapper`: map source learning into Ralph or product method.
- `evaluator_designer`: define score, rubric, corpus, or check.
- `patch_writer`: produce ranking, scores, proposed diff, and decision record.
- `red_team`: adversarial review of evidence, scope, safety, and integration.
- `data`: deterministic tables or charts from local artifacts.
- `docs`: structured report, summary, plan, or one-pager from verified inputs.
- `slides`: deck only from approved narrative and export artifacts.

## Required Package Files

```text
runs/LOOP-YYYYMMDD-HHMMSS/
  PACKAGE_PLAN.md
  HANDOFFS/
  ARTIFACTS/
  INTEGRATION.md
```
```

- [ ] **Step 2: Update `.ralph/METRICS.schema.json`**

Add this sibling property under `properties`:

```json
"swarm": {
  "type": "object",
  "properties": {
    "used": { "type": "boolean" },
    "pattern": { "enum": ["none", "handoff", "parallel", "package"] },
    "specialists": { "type": "array", "items": { "type": "string" } },
    "handoff_quality": { "enum": ["not_applicable", "weak", "adequate", "strong"] },
    "context_compression": { "enum": ["not_applicable", "weak", "adequate", "strong"] },
    "artifacts": { "type": "array", "items": { "type": "string" } },
    "integration_verified": { "type": "boolean" },
    "integration_debt": { "enum": ["none", "low", "medium", "high"] }
  }
}
```

Extend `autoresearch.method_signal.enum` with:

```json
"weak_swarm_handoff",
"weak_artifact_integration",
"weak_delivery_packet"
```

- [ ] **Step 3: Update task template metadata**

Add these keys to `.ralph/TASK_TEMPLATE.md` frontmatter:

```yaml
specialist_lane: executor
composite_package: false
specialists_needed: []
```

Add a `## Context Packet` section:

```markdown
## Context Packet

For research or AutoResearch tasks, include source URL/local path, commit/date, verified facts, unverified claims, affected method component, expected evidence, and safety limits.
```

- [ ] **Step 4: Update Ralph docs**

Add one sentence to each file:

```markdown
Read `.ralph/SWARM.md` only when `composite_package: true` or when a task has multiple independently verifiable artifact types.
```

Apply this to `.ralph/RALPH.md`, `.ralph/PM.md`, `.ralph/AUTORESEARCH.md`, and `.ralph/VERIFY.md`.

- [ ] **Step 5: Verify method files**

Run:

```powershell
Get-Content .ralph\METRICS.schema.json -Raw | ConvertFrom-Json | Out-Null
Select-String -Path .ralph\*.md -Pattern "SWARM.md|specialist_lane|Context Packet|composite_package"
git diff --check -- .ralph
```

Expected:

```text
JSON parses; Select-String shows matches; git diff --check emits no output.
```

---

## Task 2: Backend Delivery Packet

**Files:**
- Create: `backend/app/services/report_delivery_packet.py`
- Create: `backend/tests/test_report_delivery_packet.py`

- [ ] **Step 1: Write failing tests**

Create `backend/tests/test_report_delivery_packet.py`:

```python
from app.services.report_agent import Report, ReportManager, ReportStatus
from app.services.report_delivery_packet import ReportDeliveryPacketBuilder


def _report(**overrides):
    data = {
        "report_id": "report_packet_1",
        "simulation_id": "sim_packet_1",
        "graph_id": "graph_packet_1",
        "simulation_requirement": "Avaliar cenario institucional",
        "status": ReportStatus.COMPLETED,
        "markdown_content": "# Relatorio\n\nConteudo.",
        "quality_gate": {"passes_gate": True, "metrics": {"delivery_mode": "client"}},
        "evidence_audit": {"passes_gate": True, "quotes_total": 0, "numbers_total": 0},
    }
    data.update(overrides)
    return Report(**data)


def test_packet_marks_publishable_report_as_client_ready(tmp_path, monkeypatch):
    monkeypatch.setattr(ReportManager, "REPORTS_DIR", str(tmp_path / "reports"))
    ReportManager.save_report(_report())
    ReportManager.save_json_artifact("report_packet_1", "mission_bundle.json", {
        "hashes": {"manifesto": "abc123"},
        "previsoes_congeladas": [{"id": "prev_1"}],
        "arquivos": ["system_gate.json", "evidence_audit.json"],
    })

    packet = ReportDeliveryPacketBuilder().build("report_packet_1")

    assert packet["delivery_status"] == "publishable"
    assert packet["client_ready"] is True
    assert packet["next_action"]["kind"] == "export"
    assert packet["mission"]["hash_short"] == "abc123"


def test_packet_explains_diagnostic_report(tmp_path, monkeypatch):
    monkeypatch.setattr(ReportManager, "REPORTS_DIR", str(tmp_path / "reports"))
    ReportManager.save_report(_report(quality_gate={
        "passes_gate": True,
        "metrics": {"delivery_mode": "demo", "diagnostic_only": True, "delivery_publishable_mode": False},
    }))

    packet = ReportDeliveryPacketBuilder().build("report_packet_1")

    assert packet["delivery_status"] == "diagnostic_only"
    assert packet["client_ready"] is False
    assert packet["next_action"]["kind"] == "diagnostic_export"
    assert any("diagnostico" in item.lower() for item in packet["warnings"])


def test_packet_explains_blocked_report(tmp_path, monkeypatch):
    monkeypatch.setattr(ReportManager, "REPORTS_DIR", str(tmp_path / "reports"))
    ReportManager.save_report(_report(quality_gate={
        "passes_gate": False,
        "issues": ["Evidencia insuficiente"],
        "metrics": {"delivery_mode": "client"},
    }))

    packet = ReportDeliveryPacketBuilder().build("report_packet_1")

    assert packet["client_ready"] is False
    assert packet["next_action"]["kind"] == "fix_gate"
    assert "Evidencia insuficiente" in packet["blockers"]
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```powershell
.\backend\.venv\Scripts\python.exe -m pytest backend\tests\test_report_delivery_packet.py -q
```

Expected:

```text
ModuleNotFoundError: No module named 'app.services.report_delivery_packet'
```

- [ ] **Step 3: Implement service**

Create `backend/app/services/report_delivery_packet.py`:

```python
from __future__ import annotations

from typing import Any

from .report_agent import ReportManager


class ReportDeliveryPacketError(RuntimeError):
    pass


class ReportDeliveryPacketBuilder:
    def build(self, report_id: str) -> dict[str, Any]:
        report = ReportManager.get_report(report_id)
        if not report:
            raise ReportDeliveryPacketError(f"Relatorio nao encontrado: {report_id}")

        artifacts = ReportManager.list_json_artifacts(report_id)
        artifact_names = [item["name"] for item in artifacts]
        mission_bundle = ReportManager.load_json_artifact(report_id, "mission_bundle.json") or {}
        quality_gate = report.quality_gate or {}
        evidence_audit = report.evidence_audit or {}
        delivery_status = report.delivery_status()

        blockers = self._blockers(delivery_status, quality_gate, evidence_audit)
        warnings = self._warnings(delivery_status, quality_gate)

        return {
            "report_id": report.report_id,
            "simulation_id": report.simulation_id,
            "status": report.status.value if hasattr(report.status, "value") else str(report.status),
            "delivery_status": delivery_status,
            "client_ready": delivery_status == "publishable",
            "blockers": blockers,
            "warnings": warnings,
            "artifact_summary": {
                "count": len(artifact_names),
                "names": artifact_names,
                "has_system_gate": "system_gate.json" in artifact_names,
                "has_evidence_audit": "evidence_audit.json" in artifact_names,
                "has_mission_bundle": "mission_bundle.json" in artifact_names,
            },
            "mission": self._mission_summary(mission_bundle),
            "quality": {
                "system_gate_passed": quality_gate.get("passes_gate"),
                "evidence_audit_passed": evidence_audit.get("passes_gate"),
                "quotes_total": evidence_audit.get("quotes_total", 0),
                "numbers_total": evidence_audit.get("numbers_total", 0),
            },
            "next_action": self._next_action(delivery_status, blockers),
        }

    def _blockers(self, delivery_status: str, quality_gate: dict[str, Any], evidence_audit: dict[str, Any]) -> list[str]:
        if delivery_status == "publishable":
            return []
        if delivery_status == "diagnostic_only":
            return []
        issues = []
        issues.extend(quality_gate.get("issues") or [])
        issues.extend(evidence_audit.get("issues") or [])
        if not issues:
            issues.append(f"Relatorio nao publicavel: {delivery_status}")
        return [str(item) for item in issues]

    def _warnings(self, delivery_status: str, quality_gate: dict[str, Any]) -> list[str]:
        warnings = [str(item) for item in (quality_gate.get("warnings") or [])]
        if delivery_status == "diagnostic_only":
            warnings.append("Export diagnostico interno; nao publicavel para cliente.")
        if delivery_status == "legacy_unverified":
            warnings.append("Relatorio legado sem gate e auditoria completos.")
        return warnings

    def _mission_summary(self, mission_bundle: dict[str, Any]) -> dict[str, Any]:
        manifest_hash = (mission_bundle.get("hashes") or {}).get("manifesto", "")
        return {
            "title": mission_bundle.get("titulo", "Manifesto final da missao"),
            "hash_short": manifest_hash,
            "powers_count": len(mission_bundle.get("poderes_mobilizados") or []),
            "participants_count": len(mission_bundle.get("participantes") or []),
            "forecast_count": len(mission_bundle.get("previsoes_congeladas") or []),
            "files_count": len(mission_bundle.get("arquivos") or []),
        }

    def _next_action(self, delivery_status: str, blockers: list[str]) -> dict[str, str]:
        if delivery_status == "publishable":
            return {"kind": "export", "label": "Gerar pacote executivo auditavel"}
        if delivery_status == "diagnostic_only":
            return {"kind": "diagnostic_export", "label": "Gerar export diagnostico interno"}
        if delivery_status == "legacy_unverified":
            return {"kind": "regenerate", "label": "Regenerar relatorio com gate e auditoria"}
        if blockers:
            return {"kind": "fix_gate", "label": "Corrigir bloqueios antes de entregar"}
        return {"kind": "inspect", "label": "Inspecionar estado do relatorio"}
```

- [ ] **Step 4: Run tests**

Run:

```powershell
.\backend\.venv\Scripts\python.exe -m pytest backend\tests\test_report_delivery_packet.py -q
```

Expected:

```text
3 passed
```

---

## Task 3: Delivery Packet API

**Files:**
- Create: `backend/tests/test_report_delivery_packet_api.py`
- Modify: `backend/app/api/report.py`

- [ ] **Step 1: Write API tests**

Create `backend/tests/test_report_delivery_packet_api.py`:

```python
from app import create_app
from app.services.report_agent import Report, ReportManager, ReportStatus


def test_delivery_package_api_returns_packet(tmp_path, monkeypatch):
    monkeypatch.setattr(ReportManager, "REPORTS_DIR", str(tmp_path / "reports"))
    ReportManager.save_report(Report(
        report_id="report_api_packet",
        simulation_id="sim_api_packet",
        graph_id="graph_api_packet",
        simulation_requirement="Teste",
        status=ReportStatus.COMPLETED,
        markdown_content="# Relatorio",
        quality_gate={"passes_gate": True, "metrics": {"delivery_mode": "client"}},
        evidence_audit={"passes_gate": True},
    ))

    client = create_app().test_client()
    response = client.get("/api/report/report_api_packet/delivery-package")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["success"] is True
    assert payload["data"]["client_ready"] is True
    assert payload["data"]["next_action"]["kind"] == "export"
```

- [ ] **Step 2: Run API test to verify failure**

Run:

```powershell
.\backend\.venv\Scripts\python.exe -m pytest backend\tests\test_report_delivery_packet_api.py -q
```

Expected:

```text
404 NOT FOUND
```

- [ ] **Step 3: Add route**

In `backend/app/api/report.py`, import:

```python
from ..services.report_delivery_packet import (
    ReportDeliveryPacketBuilder,
    ReportDeliveryPacketError,
)
```

Add before the Markdown download route:

```python
@report_bp.route('/<report_id>/delivery-package', methods=['GET'])
def get_report_delivery_package(report_id: str):
    """Obter pacote de decisao de entrega do relatorio."""
    try:
        packet = ReportDeliveryPacketBuilder().build(report_id)
        return jsonify({"success": True, "data": packet})
    except ReportDeliveryPacketError as exc:
        return jsonify({"success": False, "error": str(exc)}), 404
    except Exception as e:
        logger.error(f"Falha ao montar pacote de entrega: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"success": False, "error": str(e)}), 500
```

- [ ] **Step 4: Run API test**

Run:

```powershell
.\backend\.venv\Scripts\python.exe -m pytest backend\tests\test_report_delivery_packet_api.py -q
```

Expected:

```text
1 passed
```

---

## Task 4: Step 4 User Experience

**Files:**
- Modify: `frontend/src/api/report.js`
- Modify: `frontend/src/components/Step4Report.vue`

- [ ] **Step 1: Add API helper**

Append to `frontend/src/api/report.js`:

```javascript
/**
 * Obter pacote inteligente de entrega do relatorio
 * @param {string} reportId
 */
export const getReportDeliveryPackage = (reportId) => {
  return service.get(`/api/report/${reportId}/delivery-package`)
}
```

- [ ] **Step 2: Add Step 4 state and fetch**

In `frontend/src/components/Step4Report.vue`, import `getReportDeliveryPackage`, add:

```javascript
const deliveryPackage = ref(null)
const deliveryPackageError = ref('')

const refreshDeliveryPackage = async () => {
  if (!props.reportId) return
  try {
    const res = await getReportDeliveryPackage(props.reportId)
    if (res.success && res.data) {
      deliveryPackage.value = res.data
      deliveryPackageError.value = ''
    }
  } catch (err) {
    deliveryPackageError.value = err.message || 'Pacote de entrega indisponivel'
  }
}
```

Call it inside `fetchReportAudit()` after report/artifacts are loaded:

```javascript
await refreshDeliveryPackage()
```

- [ ] **Step 3: Add computed display fields**

Add:

```javascript
const deliveryReadyLabel = computed(() => {
  if (!deliveryPackage.value) return 'Aguardando'
  if (deliveryPackage.value.client_ready) return 'Publicavel'
  if (deliveryPackage.value.delivery_status === 'diagnostic_only') return 'Diagnostico'
  return 'Bloqueado'
})

const deliveryNextActionLabel = computed(() => {
  return deliveryPackage.value?.next_action?.label || 'Inspecionar relatorio'
})
```

- [ ] **Step 4: Add panel near custody/mission panels**

Add the template block:

```vue
<div v-if="deliveryPackage" class="delivery-package-panel">
  <div class="delivery-package-header">
    <div>
      <div class="delivery-package-kicker">Entrega inteligente</div>
      <div class="delivery-package-title">{{ deliveryReadyLabel }}</div>
    </div>
    <span class="delivery-package-status">{{ deliveryPackage.delivery_status }}</span>
  </div>

  <div class="delivery-package-grid">
    <div class="delivery-package-stat">
      <span class="delivery-package-label">Artefatos</span>
      <span class="delivery-package-value mono">{{ deliveryPackage.artifact_summary.count }}</span>
    </div>
    <div class="delivery-package-stat">
      <span class="delivery-package-label">Previsoes</span>
      <span class="delivery-package-value mono">{{ deliveryPackage.mission.forecast_count }}</span>
    </div>
    <div class="delivery-package-stat">
      <span class="delivery-package-label">Hash</span>
      <span class="delivery-package-value mono">{{ deliveryPackage.mission.hash_short || '-' }}</span>
    </div>
  </div>

  <div v-if="deliveryPackage.blockers.length" class="delivery-package-blockers">
    <div v-for="blocker in deliveryPackage.blockers.slice(0, 2)" :key="blocker" class="delivery-package-blocker">
      {{ blocker }}
    </div>
  </div>

  <div class="delivery-package-next">{{ deliveryNextActionLabel }}</div>
</div>
```

- [ ] **Step 5: Add compact styles**

Add styles that match the existing Step 4 panels:

```css
.delivery-package-panel {
  border: 1px solid rgba(17, 24, 39, 0.12);
  background: #ffffff;
  padding: 14px;
  margin-top: 14px;
}

.delivery-package-header,
.delivery-package-grid {
  display: flex;
  justify-content: space-between;
  gap: 10px;
}

.delivery-package-kicker,
.delivery-package-label {
  font-size: 11px;
  color: #6b7280;
  text-transform: uppercase;
}

.delivery-package-title {
  font-size: 15px;
  font-weight: 700;
  color: #111827;
}

.delivery-package-status {
  font-size: 11px;
  color: #0f766e;
}

.delivery-package-stat {
  min-width: 0;
}

.delivery-package-value {
  display: block;
  margin-top: 3px;
  font-size: 13px;
}

.delivery-package-blockers {
  margin-top: 10px;
}

.delivery-package-blocker {
  font-size: 12px;
  color: #92400e;
  margin-top: 4px;
}

.delivery-package-next {
  margin-top: 10px;
  font-size: 13px;
  font-weight: 600;
  color: #0f766e;
}
```

- [ ] **Step 6: Run frontend build**

Run:

```powershell
npm run build
```

Expected:

```text
vite build succeeds.
```

---

## Task 5: Canonical HTML Export

**Files:**
- Create: `backend/app/services/report_exporter.py`
- Create: `backend/tests/test_report_exporter.py`
- Modify: `backend/app/api/report.py`
- Modify: `frontend/src/api/report.js`
- Modify: `frontend/src/components/Step4Report.vue`

- [ ] **Step 1: Implement only HTML in this task**

The export service must:

- require `ReportDeliveryPacketBuilder().build(report_id)`;
- allow client export only when `client_ready is True`;
- allow diagnostic export only with `allow_diagnostic=True`;
- write `reports/<report_id>/exports/<export_id>/<report_id>.source.html`;
- write `manifest.json` inside the export folder;
- write latest pointer `export_manifest.json` in report root;
- never expose absolute server paths in API payloads.

- [ ] **Step 2: Required test cases**

`backend/tests/test_report_exporter.py` must cover:

```text
publishable report creates source HTML
diagnostic report is blocked without allow_diagnostic
diagnostic report includes diagnostic warning when allowed
legacy report is blocked
manifest files include sha256 and relative_path
download route rejects path traversal
```

- [ ] **Step 3: Required HTML blocks**

The generated HTML must include:

```text
Mirofish INTEIA
report_id
delivery_status
Cadeia de custodia
Auditoria de evidencias
Mission bundle hash when present
Diagnostic warning when delivery_status is diagnostic_only
```

- [ ] **Step 4: Verification**

Run:

```powershell
.\backend\.venv\Scripts\python.exe -m pytest backend\tests\test_report_exporter.py backend\tests\test_report_delivery_packet.py backend\tests\test_report_delivery_packet_api.py -q
npm run build
git diff --check
```

Expected:

```text
all tests pass; frontend build succeeds; git diff --check emits no output.
```

---

## Task 6: Deterministic Charts From Local Artifacts

**Files:**
- Create: `backend/app/services/report_chart_builder.py`
- Create: `backend/tests/test_report_chart_builder.py`
- Modify: `backend/app/services/report_exporter.py`

- [ ] **Step 1: Build charts from local data only**

`report_chart_builder.py` may read only:

```text
SimulationDataReader.get_agent_actions()
quality_gate.metrics
evidence_audit
forecast_ledger.json
cost_meter.json
```

It must not call an LLM, Apify, external web, or a simulation runner.

- [ ] **Step 2: Initial charts**

Create deterministic SVG files:

```text
actions_by_round.svg
action_type_distribution.svg
forecast_status_summary.svg
cost_by_phase.svg
```

- [ ] **Step 3: Include in export manifest**

The export manifest must list every chart with:

```json
{
  "kind": "chart",
  "name": "actions_by_round.svg",
  "relative_path": "exports/<export_id>/assets/actions_by_round.svg",
  "size": 1234,
  "sha256": "..."
}
```

- [ ] **Step 4: Verification**

Run:

```powershell
.\backend\.venv\Scripts\python.exe -m pytest backend\tests\test_report_chart_builder.py backend\tests\test_report_exporter.py -q
git diff --check
```

Expected:

```text
all selected tests pass; git diff --check emits no output.
```

---

## Task 7: AutoResearch Baselines

**Files:**
- Create: `backend/autoresearch/targets/report_delivery.py`
- Create: `backend/autoresearch/targets/ralph_method.py`
- Create: `backend/tests/test_autoresearch_report_delivery.py`
- Create: `backend/tests/test_autoresearch_ralph_method.py`
- Modify: `backend/autoresearch/cli.py`

- [ ] **Step 1: Add report delivery target**

`ReportDeliveryEvaluator` must score:

```text
delivery packet exists
client_ready matches delivery_status
blockers are explicit when not publishable
next_action is present
artifact summary includes system gate and evidence audit
export manifest exists when exports exist
```

- [ ] **Step 2: Add Ralph method target**

`RalphMethodEvaluator` must score:

```text
core .ralph files exist
TASK_TEMPLATE has specialist_lane and Context Packet
METRICS schema has autoresearch and swarm
recent runs include METRICS.json, VERIFY.md, LEARNING.md, NEXT.md
recent runs include autoresearch.method_signal
```

- [ ] **Step 3: Expose CLI baselines**

Add builders:

```python
TARGET_BUILDERS = {
    "hookify": setup_hookify_target,
    "skill": setup_skill_target,
    "genetic": setup_genetic_target,
    "frontend": setup_frontend_target,
    "ralph": setup_ralph_target,
    "report-delivery": setup_report_delivery_target,
}
```

- [ ] **Step 4: Verification**

Run:

```powershell
.\backend\.venv\Scripts\python.exe -m pytest backend\tests\test_autoresearch_report_delivery.py backend\tests\test_autoresearch_ralph_method.py -q
.\backend\.venv\Scripts\python.exe -m backend.autoresearch.cli baseline ralph
.\backend\.venv\Scripts\python.exe -m backend.autoresearch.cli baseline report-delivery
```

Expected:

```text
tests pass; both baseline commands print numeric scores.
```

---

## Task 8: Visual QA And Browser Verification

**Files:**
- Create: `backend/app/services/report_visual_quality.py`
- Create: `backend/tests/test_report_visual_quality.py`
- Modify: `backend/app/services/report_exporter.py`

- [ ] **Step 1: Add visual quality result**

Write `report_visual_quality.json` with:

```json
{
  "passed": true,
  "checks": {
    "html_exists": true,
    "contains_custody": true,
    "contains_evidence_audit": true,
    "contains_delivery_status": true,
    "contains_diagnostic_warning_when_needed": true
  },
  "preview": {
    "available": false,
    "path": ""
  }
}
```

- [ ] **Step 2: Add browser screenshot only when local tooling is available**

If browser tooling is available, render the HTML export and save:

```text
report_preview.png
```

If it is not available, keep the structural checks and mark `preview.available=false`.

- [ ] **Step 3: Verification**

Run:

```powershell
.\backend\.venv\Scripts\python.exe -m pytest backend\tests\test_report_visual_quality.py backend\tests\test_report_exporter.py -q
git diff --check
```

Expected:

```text
tests pass; git diff --check emits no output.
```

---

## Execution Order

1. Sync from GitHub `origin/main` and create the implementation branch `codex/systemic-intelligence-trio`.
2. Execute Task 1 to keep method guardrails aligned.
3. Execute Tasks 2-4 as the first product-visible increment.
4. Execute Task 5 after the delivery packet is visible and tested.
5. Execute Tasks 6-8 only after export behavior is stable.
6. After 3 to 5 Ralph runs, run AutoResearch baselines and decide whether to open a new `.autoresearch/experiments/<id>/PATCH_PROPOSTO.diff`.
7. Push the Codex branch to GitHub and open a PR; do not merge directly to `main`.

## Self-Review

### Spec Coverage

- Mirofish current system: reviewed through report gate, report artifacts, mission bundle, forecast ledger, Step 4, roadmap, and AutoResearch package.
- OpenSwarm: integrated as deliverable/package/handoff discipline only.
- Ralph Loop: preserved as execution cadence with a minimal composite-package policy.
- AutoResearch: positioned as learning/scoring layer with zero-LLM baseline targets first.
- User experience: first product PR creates a single delivery packet and visible Step 4 panel.
- Intelligence: delivery state, evidence, mission hash, blockers, next action, deterministic charts, and export manifest become explicit product objects.

### Risk Review

- The plan avoids new runtime orchestration before the product surface improves.
- The first PR adds no new external service, paid API, PDF native dependency, or simulation requirement.
- Existing report governance is reused rather than weakened.
- The export path depends on the delivery packet, so blocked/diagnostic states remain visible.
- GitHub remains the coordination source; Codex work is isolated in a `codex/*` branch and reviewed through PR before `main`.

### Placeholder Scan

The executable tasks use concrete file paths, test names, commands, expected outcomes, and code snippets.

### Superseded Direction

This plan supersedes the implementation order in:

- `docs/superpowers/plans/2026-05-06-mirofish-auditable-executive-export.md`
- `docs/superpowers/plans/2026-05-06-mirofish-ralph-openswarm-autoresearch-trio.md`

Those files remain useful as source material, but execution should start here.
