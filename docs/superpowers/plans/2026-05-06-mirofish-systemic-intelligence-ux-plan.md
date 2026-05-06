# Mirofish Systemic Intelligence UX Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Improve Mirofish intelligence and user experience by turning existing gates, report evidence, Ralph Loop discipline, OpenSwarm handoff patterns, and AutoResearch learning into a product-first workflow.

**Architecture:** Keep Mirofish as the product brain and do not import OpenSwarm as a runtime. Add a central readiness layer that interprets simulation/report state into concrete next actions for the user, then add audited executive packaging only after a report is publishable. Ralph Loop remains the internal execution cadence, OpenSwarm contributes only controlled specialist handoffs for composite packages, and AutoResearch learns from completed Ralph runs before proposing method changes.

**Tech Stack:** Flask API, existing Python services under `backend/app/services`, Vue 3 components under `frontend/src/components`, existing report artifacts, JSON manifests, pytest, Vite build, Markdown method files under `.ralph/`.

---

## Source Context

- Current project: `C:\Users\IgorPC\.claude\projects\Mirofish INTEIA`.
- Ralph source studied: `C:\Users\IgorPC\.claude\projects\ralphloop-autoresearch`.
- OpenSwarm source studied: [VRSEN/OpenSwarm](https://github.com/VRSEN/OpenSwarm) plus the supplied video transcript.
- Prior Mirofish OpenSwarm study: `docs/openswarm_mirofish_opportunities_2026-05-06.md`.
- Formal PRD: `docs/prd/2026-05-06-mirofish-systemic-intelligence-ux-prd.md`.
- Formal DDD: `docs/ddd/2026-05-06-mirofish-systemic-intelligence-ux-ddd.md`.
- Prior plans superseded by this one:
  - `docs/superpowers/plans/2026-05-06-mirofish-ralph-openswarm-autoresearch-trio.md`
  - `docs/superpowers/plans/2026-05-06-mirofish-auditable-executive-export.md` should now be treated as Phase 2 detail, not the first implementation slice.

## Systemic Review

### What Mirofish Already Has

Mirofish already contains useful intelligence:

- A structural report gate in `backend/app/services/report_system_gate.py`.
- Delivery governance in `backend/app/services/delivery_governance.py`.
- Report delivery status and artifacts in `backend/app/services/report_agent.py`.
- A simulation quality endpoint at `GET /api/simulation/<simulation_id>/quality`.
- Step 3 quality blocking in `frontend/src/components/Step3Simulation.vue`.
- Step 4 custody/audit panels in `frontend/src/components/Step4Report.vue`.
- Existing artifacts such as `system_gate.json`, `evidence_manifest.json`, `evidence_audit.json`, `mission_bundle.json`, `forecast_ledger.json`, and `cost_meter.json`.

The current system is not missing intelligence at the base layer. The bigger gap is that the user still has to interpret too much: what is blocked, what is safe to do next, when a report is publishable, and when it can become an executive package.

### What Ralph Adds

Ralph should not become a visible product feature and should not become another runtime agent. It adds internal execution discipline:

- One small unit per run.
- Real verification before claiming completion.
- Durable handoff in `runs/LOOP-*`.
- Method learning in `METRICS.json.autoresearch`.
- Stop conditions when an action depends on secrets, paid APIs, production, client publication, or long LLM spend.

Best Mirofish fit: implementation, validation, and delivery hygiene.

### What OpenSwarm Adds

OpenSwarm's useful idea is not the codebase itself. The useful pattern is:

- Orchestrator decides what specialist is needed.
- Specialists produce narrow artifacts.
- Handoffs compress context.
- Final integration checks contradictions and evidence.

Best Mirofish fit: composite deliverables such as "approved report -> executive summary + evidence annex + charts + deck", not normal code changes.

### What AutoResearch Adds

AutoResearch should learn from completed Ralph runs, not replace delivery:

- Read `runs/LOOP-*`.
- Detect repeated weak signals.
- Compare small method variants.
- Produce ranking, scores, proposed diff, and decision record.
- Never apply production-affecting patches automatically.

Best Mirofish fit: after 3 to 5 comparable runs, improve `.ralph/TASK_TEMPLATE.md`, `.ralph/VERIFY.md`, `.ralph/PM.md`, `.ralph/AUTORESEARCH.md`, or a narrow evaluation rubric.

### What Not To Build Now

- Do not import OpenSwarm runtime.
- Do not add an autonomous multi-agent daemon.
- Do not expose Ralph/Swarm jargon in the user interface.
- Do not generate polished decks from unapproved reports.
- Do not let AutoResearch mutate production code automatically.
- Do not run paid LLM, Apify, deploy, email, CRM, or client publication actions without explicit approval.

---

## Product Strategy

The highest value implementation sequence is:

1. **Decision readiness layer:** translate current gates and artifacts into a user-facing "state + next action".
2. **UX guidance:** show the next safe step in Step 3 and Step 4, using product language.
3. **Executive package:** only when the report is publishable, generate a clean package from existing verified artifacts.
4. **Ralph + Swarm method:** use internal handoff templates only for composite package work.
5. **AutoResearch:** after enough real runs, improve the method with evidence.

This keeps the product simple while making it feel more intelligent.

---

## File Structure

### Create

- `backend/app/services/decision_readiness.py`  
  Central product-state interpreter for simulation/report readiness and next action.

- `backend/tests/test_decision_readiness.py`  
  Unit tests for blocked, ready-for-report, report-in-progress, publishable, and diagnostic-only states.

- `backend/app/services/executive_package.py`  
  Creates an audited executive package from an already publishable report.

- `backend/tests/test_executive_package.py`  
  Unit tests for export blocking and manifest generation.

- `.ralph/SWARM.md`  
  Minimal internal composite-package contract inspired by OpenSwarm.

- `.ralph/tickets/004-product-readiness-layer.md`  
  Ralph ticket for the first implementation slice.

- `.ralph/tickets/005-executive-package.md`  
  Ralph ticket for the second implementation slice.

### Modify

- `backend/app/api/simulation.py`  
  Add `GET /api/simulation/<simulation_id>/readiness`.

- `backend/app/api/report.py`  
  Add executive package build/download endpoints.

- `frontend/src/api/simulation.js`  
  Add `getDecisionReadiness()`.

- `frontend/src/api/report.js`  
  Add executive package API helpers if this file exists; otherwise add helpers to the existing report API module.

- `frontend/src/components/Step3Simulation.vue`  
  Show decision readiness and next action near the existing quality gate.

- `frontend/src/components/Step4Report.vue`  
  Show report readiness, package eligibility, and export controls without exposing internal method jargon.

- `.ralph/RALPH.md`  
  Add one rule pointing composite work to `.ralph/SWARM.md`.

- `.ralph/TASK_TEMPLATE.md`  
  Add optional package fields for composite work.

- `.ralph/METRICS.schema.json`  
  Add optional `swarm` metrics without making all tasks composite.

- `.ralph/AUTORESEARCH.md`  
  Clarify when AutoResearch may propose method experiments.

---

## Phase 1: Decision Readiness Layer

### Task 1: Backend Readiness Service

**Files:**
- Create: `backend/app/services/decision_readiness.py`
- Test: `backend/tests/test_decision_readiness.py`

- [ ] **Step 1: Write failing tests for core readiness states**

Create `backend/tests/test_decision_readiness.py`:

```python
from types import SimpleNamespace

import pytest

from app.services.decision_readiness import evaluate_decision_readiness


class FakeStatus:
    def __init__(self, value):
        self.value = value


def fake_state(status="completed"):
    return SimpleNamespace(
        simulation_id="sim_1",
        project_id="proj_1",
        graph_id="graph_1",
        status=FakeStatus(status),
    )


def fake_gate(passes=True, issues=None, metrics=None):
    return SimpleNamespace(
        passes_gate=passes,
        issues=issues or [],
        metrics=metrics or {},
        to_dict=lambda: {
            "passes_gate": passes,
            "issues": issues or [],
            "metrics": metrics or {},
        },
    )


def patch_common(monkeypatch, *, state=None, gate=None, report=None, source_text="source"):
    import app.services.decision_readiness as module

    class FakeSimulationManager:
        def get_simulation(self, simulation_id):
            return state

    class FakeProjectManager:
        @staticmethod
        def get_extracted_text(project_id):
            return source_text

    class FakeReportManager:
        @staticmethod
        def get_report_by_simulation(simulation_id):
            return report

    monkeypatch.setattr(module, "SimulationManager", FakeSimulationManager)
    monkeypatch.setattr(module, "ProjectManager", FakeProjectManager)
    monkeypatch.setattr(module, "ReportManager", FakeReportManager)
    monkeypatch.setattr(module, "evaluate_report_system_gate", lambda **kwargs: gate)


def test_readiness_blocks_report_when_system_gate_fails(monkeypatch):
    patch_common(
        monkeypatch,
        state=fake_state("completed"),
        gate=fake_gate(False, ["Simulação sem ações interativas suficientes"]),
        report=None,
    )

    result = evaluate_decision_readiness("sim_1")

    assert result["status"] == "blocked"
    assert result["ready_for_report"] is False
    assert result["ready_for_export"] is False
    assert result["next_action"]["kind"] == "fix_simulation_quality"
    assert "ações interativas" in result["next_action"]["label"].lower()


def test_readiness_allows_report_when_gate_passes_and_no_report(monkeypatch):
    patch_common(
        monkeypatch,
        state=fake_state("completed"),
        gate=fake_gate(True, metrics={"delivery_publishable_mode": True}),
        report=None,
    )

    result = evaluate_decision_readiness("sim_1")

    assert result["status"] == "ready_for_report"
    assert result["ready_for_report"] is True
    assert result["ready_for_export"] is False
    assert result["next_action"]["kind"] == "generate_report"


def test_readiness_allows_export_only_for_publishable_report(monkeypatch):
    report = SimpleNamespace(
        report_id="report_1",
        status="completed",
        delivery_status=lambda: "publishable",
        error=None,
    )
    patch_common(
        monkeypatch,
        state=fake_state("completed"),
        gate=fake_gate(True, metrics={"delivery_publishable_mode": True}),
        report=report,
    )

    result = evaluate_decision_readiness("sim_1")

    assert result["status"] == "ready_for_export"
    assert result["ready_for_report"] is False
    assert result["ready_for_export"] is True
    assert result["report_id"] == "report_1"
    assert result["next_action"]["kind"] == "build_executive_package"


def test_readiness_blocks_export_for_diagnostic_report(monkeypatch):
    report = SimpleNamespace(
        report_id="report_1",
        status="completed",
        delivery_status=lambda: "diagnostic_only",
        error=None,
    )
    patch_common(
        monkeypatch,
        state=fake_state("completed"),
        gate=fake_gate(True, metrics={"diagnostic_only": True}),
        report=report,
    )

    result = evaluate_decision_readiness("sim_1")

    assert result["status"] == "diagnostic_only"
    assert result["ready_for_export"] is False
    assert result["next_action"]["kind"] == "rerun_complete_simulation"
```

- [ ] **Step 2: Run the failing tests**

Run:

```powershell
.\backend\.venv\Scripts\python.exe -m pytest backend\tests\test_decision_readiness.py -q
```

Expected: failure because `app.services.decision_readiness` does not exist.

- [ ] **Step 3: Create the readiness service**

Create `backend/app/services/decision_readiness.py`:

```python
"""Decision readiness layer for Mirofish.

This service turns existing simulation/report gates into product-level next actions.
It does not weaken the underlying gates and does not call external services.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..models.project import ProjectManager
from .report_agent import ReportManager
from .report_system_gate import evaluate_report_system_gate
from .simulation_manager import SimulationManager


def _safe_status_value(value: Any) -> str:
    return getattr(value, "value", value) or "unknown"


def _safe_delivery_status(report: Any) -> Optional[str]:
    if not report:
        return None
    status_fn = getattr(report, "delivery_status", None)
    if callable(status_fn):
        return status_fn()
    return getattr(report, "delivery_status", None)


def _first_issue(issues: List[Any]) -> str:
    for issue in issues:
        if isinstance(issue, str) and issue.strip():
            return issue.strip()
        if issue:
            return str(issue)
    return ""


def _action(kind: str, label: str, enabled: bool = True, reason: str = "") -> Dict[str, Any]:
    return {
        "kind": kind,
        "label": label,
        "enabled": enabled,
        "reason": reason,
    }


def _blocked_action(primary_issue: str) -> Dict[str, Any]:
    text = primary_issue.lower()
    if "interativ" in text or "ações" in text or "acoes" in text:
        return _action(
            "fix_simulation_quality",
            "Reexecutar uma simulação com mais interações antes do relatório",
            False,
            primary_issue,
        )
    if "fonte" in text or "texto" in text or "material" in text:
        return _action(
            "review_source_material",
            "Revisar o material-base antes de gerar o relatório",
            False,
            primary_issue,
        )
    if "conclu" in text:
        return _action(
            "finish_simulation",
            "Aguardar ou concluir a simulação antes do relatório",
            False,
            primary_issue,
        )
    return _action(
        "review_blockers",
        "Resolver o bloqueio principal antes de avançar",
        False,
        primary_issue,
    )


def evaluate_decision_readiness(
    simulation_id: str,
    *,
    graph_id: Optional[str] = None,
    delivery_mode: Optional[str] = None,
) -> Dict[str, Any]:
    """Return product-level readiness and the safest next action for a simulation."""

    manager = SimulationManager()
    state = manager.get_simulation(simulation_id)
    if not state:
        return {
            "simulation_id": simulation_id,
            "status": "missing",
            "ready_for_report": False,
            "ready_for_export": False,
            "blocking_issues": [f"Simulação não encontrada: {simulation_id}"],
            "next_action": _action("select_simulation", "Selecionar uma simulação válida", False),
        }

    source_text = None
    try:
        source_text = ProjectManager.get_extracted_text(state.project_id)
    except Exception:
        source_text = None

    gate_result = evaluate_report_system_gate(
        simulation_id=simulation_id,
        graph_id=graph_id or state.graph_id,
        source_text=source_text,
        require_completed_simulation=True,
        delivery_mode=delivery_mode,
    )

    report = ReportManager.get_report_by_simulation(simulation_id)
    delivery_status = _safe_delivery_status(report)
    report_id = getattr(report, "report_id", None) if report else None
    issues = list(getattr(gate_result, "issues", []) or [])
    primary_issue = _first_issue(issues)
    metrics = dict(getattr(gate_result, "metrics", {}) or {})
    gate_dict = gate_result.to_dict()

    base = {
        "simulation_id": simulation_id,
        "project_id": state.project_id,
        "graph_id": state.graph_id,
        "simulation_status": _safe_status_value(state.status),
        "report_id": report_id,
        "report_delivery_status": delivery_status,
        "gate": gate_dict,
        "metrics": metrics,
        "blocking_issues": issues,
    }

    if not gate_result.passes_gate:
        return {
            **base,
            "status": "blocked",
            "ready_for_report": False,
            "ready_for_export": False,
            "next_action": _blocked_action(primary_issue),
        }

    if delivery_status in {"publishable"}:
        return {
            **base,
            "status": "ready_for_export",
            "ready_for_report": False,
            "ready_for_export": True,
            "next_action": _action("build_executive_package", "Gerar pacote executivo auditável"),
        }

    if delivery_status in {"diagnostic_only"} or metrics.get("diagnostic_only") is True:
        return {
            **base,
            "status": "diagnostic_only",
            "ready_for_report": False,
            "ready_for_export": False,
            "next_action": _action(
                "rerun_complete_simulation",
                "Gerar uma execução completa antes de preparar entrega",
                False,
                "Relatório atual está em modo diagnóstico",
            ),
        }

    if delivery_status in {"failed", "blocked_by_system_gate", "blocked_by_evidence_audit"}:
        return {
            **base,
            "status": "report_blocked",
            "ready_for_report": True,
            "ready_for_export": False,
            "next_action": _action("regenerate_report", "Regenerar relatório após corrigir os bloqueios"),
        }

    if delivery_status in {"in_progress"}:
        return {
            **base,
            "status": "report_in_progress",
            "ready_for_report": False,
            "ready_for_export": False,
            "next_action": _action("wait_report", "Aguardar a conclusão do relatório", False),
        }

    return {
        **base,
        "status": "ready_for_report",
        "ready_for_report": True,
        "ready_for_export": False,
        "next_action": _action("generate_report", "Gerar relatório auditável"),
    }
```

- [ ] **Step 4: Run service tests**

Run:

```powershell
.\backend\.venv\Scripts\python.exe -m pytest backend\tests\test_decision_readiness.py -q
```

Expected: all tests pass.

### Task 2: Readiness API Endpoint

**Files:**
- Modify: `backend/app/api/simulation.py`
- Test: `backend/tests/test_decision_readiness.py`

- [ ] **Step 1: Add API test**

Append to `backend/tests/test_decision_readiness.py`:

```python
def test_readiness_api_returns_service_payload(monkeypatch):
    from app import create_app
    import app.api.simulation as simulation_api

    monkeypatch.setattr(
        simulation_api,
        "evaluate_decision_readiness",
        lambda simulation_id, graph_id=None, delivery_mode=None: {
            "simulation_id": simulation_id,
            "status": "ready_for_report",
            "ready_for_report": True,
            "ready_for_export": False,
            "next_action": {"kind": "generate_report", "label": "Gerar relatório auditável"},
        },
    )

    app = create_app()
    client = app.test_client()

    response = client.get("/api/simulation/sim_1/readiness")

    assert response.status_code == 200
    body = response.get_json()
    assert body["success"] is True
    assert body["data"]["status"] == "ready_for_report"
    assert body["data"]["next_action"]["kind"] == "generate_report"
```

- [ ] **Step 2: Run test and confirm failure**

Run:

```powershell
.\backend\.venv\Scripts\python.exe -m pytest backend\tests\test_decision_readiness.py::test_readiness_api_returns_service_payload -q
```

Expected: failure because the endpoint or import is missing.

- [ ] **Step 3: Add module import**

In `backend/app/api/simulation.py`, add with the other service imports:

```python
from ..services.decision_readiness import evaluate_decision_readiness
```

- [ ] **Step 4: Add endpoint after `get_simulation_quality`**

Insert after the existing `get_simulation_quality()` route:

```python
@simulation_bp.route('/<simulation_id>/readiness', methods=['GET'])
def get_simulation_readiness(simulation_id: str):
    """Obter próximo passo seguro da simulação para relatório ou pacote executivo."""
    try:
        result = evaluate_decision_readiness(
            simulation_id=simulation_id,
            graph_id=request.args.get('graph_id'),
            delivery_mode=request.args.get('delivery_mode'),
        )

        status_code = 404 if result.get("status") == "missing" else 200
        return jsonify({
            "success": status_code == 200,
            "data": result,
            "error": result["blocking_issues"][0] if status_code == 404 else None,
        }), status_code

    except Exception as e:
        logger.error(f"Falha ao obter prontidão de decisão: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
```

- [ ] **Step 5: Run readiness tests**

Run:

```powershell
.\backend\.venv\Scripts\python.exe -m pytest backend\tests\test_decision_readiness.py -q
```

Expected: all tests pass.

---

## Phase 2: User Experience Guidance

### Task 3: Frontend API Helper

**Files:**
- Modify: `frontend/src/api/simulation.js`

- [ ] **Step 1: Add API helper**

Add below `getSimulationQuality()`:

```javascript
/**
 * Obter próximo passo seguro da simulação.
 * @param {string} simulationId
 * @param {Object} params - { delivery_mode? }
 */
export const getDecisionReadiness = (simulationId, params = {}) => {
  return service.get(`/api/simulation/${simulationId}/readiness`, { params })
}
```

- [ ] **Step 2: Run frontend build**

Run:

```powershell
npm run build
```

Expected: build passes or fails only for pre-existing unrelated frontend issues. If it fails, capture the exact failure before changing more files.

### Task 4: Step 3 Next Action Panel

**Files:**
- Modify: `frontend/src/components/Step3Simulation.vue`

- [ ] **Step 1: Import helper**

Update the simulation API import list to include:

```javascript
getDecisionReadiness
```

- [ ] **Step 2: Add state**

Near existing quality-gate refs, add:

```javascript
const decisionReadiness = ref(null)
const isLoadingReadiness = ref(false)
const readinessError = ref('')
```

- [ ] **Step 3: Add computed fields**

Add near quality gate computed values:

```javascript
const readinessStatus = computed(() => decisionReadiness.value?.status || '')

const readinessAction = computed(() => {
  return decisionReadiness.value?.next_action || null
})

const readinessTitle = computed(() => {
  if (isLoadingReadiness.value) return 'Verificando próximo passo'
  if (readinessStatus.value === 'ready_for_export') return 'Pronto para pacote executivo'
  if (readinessStatus.value === 'ready_for_report') return 'Pronto para relatório'
  if (readinessStatus.value === 'blocked') return 'Ajuste necessário'
  if (readinessStatus.value === 'diagnostic_only') return 'Execução diagnóstica'
  if (readinessStatus.value === 'report_in_progress') return 'Relatório em andamento'
  return 'Prontidão pendente'
})

const readinessClass = computed(() => ({
  'readiness--ready': ['ready_for_report', 'ready_for_export'].includes(readinessStatus.value),
  'readiness--blocked': ['blocked', 'diagnostic_only', 'report_blocked'].includes(readinessStatus.value),
  'readiness--pending': !readinessStatus.value || readinessStatus.value === 'report_in_progress'
}))
```

- [ ] **Step 4: Add loader function**

Add near `loadQualityGate()`:

```javascript
const loadDecisionReadiness = async () => {
  if (!props.simulationId) return
  isLoadingReadiness.value = true
  readinessError.value = ''

  try {
    const res = await getDecisionReadiness(props.simulationId)
    if (res.success && res.data) {
      decisionReadiness.value = res.data
    } else {
      readinessError.value = res.error || 'Não foi possível avaliar o próximo passo'
    }
  } catch (err) {
    readinessError.value = err.message || 'Não foi possível avaliar o próximo passo'
  } finally {
    isLoadingReadiness.value = false
  }
}
```

- [ ] **Step 5: Call readiness after quality refresh**

Where Step 3 already calls:

```javascript
await loadQualityGate({ force: true })
```

add directly after it:

```javascript
await loadDecisionReadiness()
```

Do this in the completion paths for normal completion and manual stop.

- [ ] **Step 6: Add the panel markup**

Inside `<div class="action-controls">`, after the existing `quality-gate` block and before `mission-selector`, add:

```vue
<div v-if="phase === 2" class="readiness-panel" :class="readinessClass">
  <div class="readiness-main">
    <span class="readiness-dot"></span>
    <span class="readiness-title">{{ readinessTitle }}</span>
  </div>
  <div v-if="readinessAction" class="readiness-action">
    {{ readinessAction.label }}
  </div>
  <div v-else-if="readinessError" class="readiness-action warning">
    {{ readinessError }}
  </div>
</div>
```

- [ ] **Step 7: Add compact styles**

Add near existing quality gate styles:

```css
.readiness-panel {
  border: 1px solid rgba(15, 39, 71, 0.12);
  border-radius: 8px;
  padding: 10px 12px;
  background: rgba(255, 255, 255, 0.84);
  display: grid;
  gap: 6px;
  max-width: 360px;
}

.readiness-main {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 700;
  color: #0f2747;
}

.readiness-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #64748b;
}

.readiness-action {
  font-size: 12px;
  line-height: 1.35;
  color: #475569;
}

.readiness-action.warning {
  color: #92400e;
}

.readiness--ready .readiness-dot {
  background: #0f9f6e;
}

.readiness--blocked .readiness-dot {
  background: #d97706;
}

.readiness--pending .readiness-dot {
  background: #64748b;
}
```

- [ ] **Step 8: Run frontend build**

Run:

```powershell
npm run build
```

Expected: build passes. If it fails due to pre-existing changes in the dirty tree, record the exact error and run the narrowest available syntax check.

---

## Phase 3: Executive Package From Verified Report

### Task 5: Backend Executive Package Service

**Files:**
- Create: `backend/app/services/executive_package.py`
- Test: `backend/tests/test_executive_package.py`

- [ ] **Step 1: Write blocking and success tests**

Create `backend/tests/test_executive_package.py`:

```python
from types import SimpleNamespace

import pytest

from app.services.executive_package import ExecutivePackageError, build_executive_package


def test_package_blocks_non_publishable_report(monkeypatch, tmp_path):
    import app.services.executive_package as module

    report = SimpleNamespace(
        report_id="report_1",
        simulation_id="sim_1",
        status="completed",
        title="Relatório",
        content="Conteúdo",
        delivery_status=lambda: "diagnostic_only",
    )

    monkeypatch.setattr(module.ReportManager, "get_report", staticmethod(lambda report_id: report))

    with pytest.raises(ExecutivePackageError) as exc:
        build_executive_package("report_1", output_dir=tmp_path)

    assert "publicável" in str(exc.value).lower()


def test_package_creates_manifest_for_publishable_report(monkeypatch, tmp_path):
    import app.services.executive_package as module

    report = SimpleNamespace(
        report_id="report_1",
        simulation_id="sim_1",
        status="completed",
        title="Relatório Estratégico",
        content="# Sumário\n\nTexto final.",
        delivery_status=lambda: "publishable",
    )

    monkeypatch.setattr(module.ReportManager, "get_report", staticmethod(lambda report_id: report))
    monkeypatch.setattr(module.ReportManager, "load_json_artifact", staticmethod(lambda report_id, name: {"name": name}))
    monkeypatch.setattr(module.ReportManager, "save_json_artifact", staticmethod(lambda report_id, name, data: None))

    result = build_executive_package("report_1", output_dir=tmp_path)

    assert result["report_id"] == "report_1"
    assert result["status"] == "created"
    assert any(file["name"] == "executive_summary.html" for file in result["files"])
    assert any(file["name"] == "evidence_annex.html" for file in result["files"])
    assert (tmp_path / "report_1" / "executive_summary.html").exists()
    assert (tmp_path / "report_1" / "evidence_annex.html").exists()
```

- [ ] **Step 2: Run failing tests**

Run:

```powershell
.\backend\.venv\Scripts\python.exe -m pytest backend\tests\test_executive_package.py -q
```

Expected: failure because the service does not exist.

- [ ] **Step 3: Create the service**

Create `backend/app/services/executive_package.py`:

```python
"""Audited executive package generation for publishable reports."""

from __future__ import annotations

import html
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .report_agent import ReportManager


class ExecutivePackageError(RuntimeError):
    """Raised when an executive package cannot be created safely."""


def _delivery_status(report: Any) -> str:
    status_fn = getattr(report, "delivery_status", None)
    if callable(status_fn):
        return status_fn()
    return getattr(report, "delivery_status", "unknown")


def _read_artifact(report_id: str, name: str) -> Optional[Dict[str, Any]]:
    try:
        return ReportManager.load_json_artifact(report_id, name)
    except Exception:
        return None


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _report_html(title: str, content: str) -> str:
    escaped = html.escape(content or "")
    body = escaped.replace("\n", "<br>\n")
    return (
        "<!doctype html>\n"
        "<html lang=\"pt-BR\">\n"
        "<head><meta charset=\"utf-8\"><title>"
        + html.escape(title)
        + "</title>"
        "<style>body{font-family:Arial,sans-serif;max-width:920px;margin:40px auto;"
        "line-height:1.55;color:#172033}h1{font-size:28px}.meta{color:#64748b}</style>"
        "</head><body><h1>"
        + html.escape(title)
        + "</h1><div class=\"meta\">Pacote executivo auditável</div><main>"
        + body
        + "</main></body></html>\n"
    )


def _annex_html(report_id: str, artifacts: Dict[str, Optional[Dict[str, Any]]]) -> str:
    sections: List[str] = []
    for name, payload in artifacts.items():
        if not payload:
            continue
        sections.append(
            "<section><h2>"
            + html.escape(name)
            + "</h2><pre>"
            + html.escape(json.dumps(payload, ensure_ascii=False, indent=2))
            + "</pre></section>"
        )
    return (
        "<!doctype html>\n<html lang=\"pt-BR\"><head><meta charset=\"utf-8\">"
        "<title>Anexo de Evidências</title>"
        "<style>body{font-family:Arial,sans-serif;max-width:980px;margin:40px auto;"
        "color:#172033}pre{white-space:pre-wrap;background:#f8fafc;padding:16px;"
        "border:1px solid #e2e8f0;border-radius:8px}</style></head><body>"
        f"<h1>Anexo de Evidências</h1><p>Relatório: {html.escape(report_id)}</p>"
        + "".join(sections)
        + "</body></html>\n"
    )


def build_executive_package(report_id: str, *, output_dir: Optional[Path] = None) -> Dict[str, Any]:
    """Create executive package files from a publishable report and verified artifacts."""

    report = ReportManager.get_report(report_id)
    if not report:
        raise ExecutivePackageError(f"Relatório não encontrado: {report_id}")

    status = _delivery_status(report)
    if status != "publishable":
        raise ExecutivePackageError("Pacote executivo exige relatório publicável")

    base_dir = output_dir or Path("backend") / "data" / "reports" / "executive_packages"
    package_dir = base_dir / report_id
    package_dir.mkdir(parents=True, exist_ok=True)

    artifacts = {
        "system_gate.json": _read_artifact(report_id, "system_gate.json"),
        "evidence_manifest.json": _read_artifact(report_id, "evidence_manifest.json"),
        "evidence_audit.json": _read_artifact(report_id, "evidence_audit.json"),
        "mission_bundle.json": _read_artifact(report_id, "mission_bundle.json"),
        "forecast_ledger.json": _read_artifact(report_id, "forecast_ledger.json"),
        "cost_meter.json": _read_artifact(report_id, "cost_meter.json"),
    }

    summary_path = package_dir / "executive_summary.html"
    annex_path = package_dir / "evidence_annex.html"

    _write_text(summary_path, _report_html(getattr(report, "title", "Relatório"), getattr(report, "content", "")))
    _write_text(annex_path, _annex_html(report_id, artifacts))

    manifest = {
        "report_id": report_id,
        "simulation_id": getattr(report, "simulation_id", None),
        "status": "created",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_delivery_status": status,
        "files": [
            {"name": "executive_summary.html", "path": str(summary_path)},
            {"name": "evidence_annex.html", "path": str(annex_path)},
        ],
        "artifact_inputs": [name for name, payload in artifacts.items() if payload],
    }

    ReportManager.save_json_artifact(report_id, "executive_package_manifest.json", manifest)
    return manifest
```

- [ ] **Step 4: Run package tests**

Run:

```powershell
.\backend\.venv\Scripts\python.exe -m pytest backend\tests\test_executive_package.py -q
```

Expected: all tests pass.

### Task 6: Executive Package API and Step 4 Controls

**Files:**
- Modify: `backend/app/api/report.py`
- Modify: `frontend/src/components/Step4Report.vue`
- Modify: report API helper module used by Step 4

- [ ] **Step 1: Add backend endpoint**

In `backend/app/api/report.py`, import:

```python
from ..services.executive_package import ExecutivePackageError, build_executive_package
```

Add route:

```python
@report_bp.route('/<report_id>/executive-package', methods=['POST'])
def create_executive_package(report_id: str):
    """Gerar pacote executivo apenas para relatório publicável."""
    try:
        manifest = build_executive_package(report_id)
        return jsonify({
            "success": True,
            "data": manifest,
        })
    except ExecutivePackageError as e:
        return jsonify({
            "success": False,
            "error": str(e),
        }), 400
    except Exception as e:
        logger.error(f"Falha ao gerar pacote executivo: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e),
        }), 500
```

- [ ] **Step 2: Add frontend API helper**

In the report API helper file, add:

```javascript
export const createExecutivePackage = (reportId) => {
  return service.post(`/api/report/${reportId}/executive-package`)
}
```

- [ ] **Step 3: Add Step 4 state and action**

In `frontend/src/components/Step4Report.vue`, add:

```javascript
const isCreatingExecutivePackage = ref(false)
const executivePackageError = ref('')
const executivePackageManifest = ref(null)

const canCreateExecutivePackage = computed(() => {
  return reportRecord.value?.delivery_status === 'publishable' && !isCreatingExecutivePackage.value
})

const handleCreateExecutivePackage = async () => {
  if (!reportRecord.value?.report_id || !canCreateExecutivePackage.value) return
  isCreatingExecutivePackage.value = true
  executivePackageError.value = ''

  try {
    const res = await createExecutivePackage(reportRecord.value.report_id)
    if (res.success && res.data) {
      executivePackageManifest.value = res.data
      await loadReportArtifacts(reportRecord.value.report_id)
    } else {
      executivePackageError.value = res.error || 'Não foi possível gerar o pacote executivo'
    }
  } catch (err) {
    executivePackageError.value = err.message || 'Não foi possível gerar o pacote executivo'
  } finally {
    isCreatingExecutivePackage.value = false
  }
}
```

- [ ] **Step 4: Add Step 4 markup**

Add the control inside the existing report action area:

```vue
<button
  class="action-btn"
  :disabled="!canCreateExecutivePackage"
  @click="handleCreateExecutivePackage"
>
  <span v-if="isCreatingExecutivePackage" class="loading-spinner-small"></span>
  Pacote executivo
</button>
<div v-if="executivePackageError" class="export-error">
  {{ executivePackageError }}
</div>
```

- [ ] **Step 5: Run tests and build**

Run:

```powershell
.\backend\.venv\Scripts\python.exe -m pytest backend\tests\test_executive_package.py backend\tests\test_decision_readiness.py -q
npm run build
```

Expected: backend tests pass and frontend build passes. If build fails because of unrelated dirty-tree changes, capture that explicitly.

---

## Phase 4: Ralph + Swarm Method, Minimal and Internal

### Task 7: Composite Package Contract

**Files:**
- Create: `.ralph/SWARM.md`
- Modify: `.ralph/RALPH.md`
- Modify: `.ralph/TASK_TEMPLATE.md`
- Modify: `.ralph/METRICS.schema.json`
- Modify: `.ralph/AUTORESEARCH.md`

- [ ] **Step 1: Create `.ralph/SWARM.md`**

```markdown
# Ralph Composite Package Contract

Mirofish does not import OpenSwarm runtime. This file only adapts the useful handoff pattern for internal composite deliverables.

## Rule

Ralph remains the outer loop. Use a composite package only when one task needs two or more independently verifiable artifact types.

## Use Ralph Simple When

- The task changes one code path, prompt, test, gate, document, or UI state.
- The acceptance criteria are still unclear.
- The task touches secrets, deploy, client publication, legal claims, paid APIs, or long LLM spend.

## Use Composite Package When

- The task needs multiple artifact types such as research, data, docs, charts, deck, visual QA, or adversarial review.
- Each artifact has a path, evidence, and acceptance criterion.
- Integration can be checked before closing the run.

## Allowed Lanes

- `research_intake`
- `data`
- `docs`
- `slides`
- `visual`
- `review`
- `executor`

## Handoff

Every handoff in `runs/LOOP-*/HANDOFFS/` must include:

```text
objective:
lane:
inputs:
constraints:
expected_artifact:
output_path:
acceptance:
block_when:
```

## Integration

Every composite run must include `INTEGRATION.md` with artifacts combined, evidence used, contradictions found, remaining limits, and final status.
```

- [ ] **Step 2: Update `.ralph/RALPH.md`**

Add under `## Context`:

```markdown
- Read `.ralph/SWARM.md` only when the selected task has `composite_package: true`.
```

Add under `## Constraints`:

```markdown
- Keep normal Ralph cycles simple; use specialist handoffs only for explicit composite packages.
```

- [ ] **Step 3: Update `.ralph/TASK_TEMPLATE.md`**

Add after the frontmatter:

```markdown
composite_package: false
specialist_lanes: []
```

Add this section before `## Handoff`:

```markdown
## Composite Package

Use only when `composite_package: true`.

- Required lanes:
- Package artifacts:
- Integration proof:
- Stop condition:
```

- [ ] **Step 4: Extend `.ralph/METRICS.schema.json`**

Add optional property under `properties`:

```json
"swarm": {
  "type": "object",
  "properties": {
    "composite_package": { "type": "boolean" },
    "lanes_used": {
      "type": "array",
      "items": { "type": "string" }
    },
    "handoff_quality": { "type": "number" },
    "artifact_verification": { "type": "number" },
    "integration_debt": {
      "enum": ["none", "low", "medium", "high"]
    }
  }
}
```

Do not add `swarm` to the schema `required` list.

- [ ] **Step 5: Update `.ralph/AUTORESEARCH.md`**

Add under `## Always-On Contract`:

```markdown
For composite packages, record whether handoffs reduced confusion or created integration debt. Do not launch a method experiment until at least 3 comparable runs or one severe repeated blocker exists.
```

- [ ] **Step 6: Validate JSON schema**

Run:

```powershell
python -m json.tool .ralph\METRICS.schema.json > $null
```

Expected: no output and exit code 0.

---

## Phase 5: AutoResearch After Evidence

### Task 8: Run-Quality AutoResearch Target

**Entry condition:** Execute only after at least 3 Ralph runs exist with usable `METRICS.json`, `VERIFY.md`, and `LEARNING.md`.

**Files:**
- Create: `backend/autoresearch/targets/ralph_method.py`
- Modify: `backend/autoresearch/cli.py`
- Test: `backend/tests/test_autoresearch_ralph_method.py`

- [ ] **Step 1: Write tests**

Create `backend/tests/test_autoresearch_ralph_method.py`:

```python
import json
from pathlib import Path

from backend.autoresearch.targets.ralph_method import RalphMethodAsset, RalphMethodEvaluator


def write_run(root: Path, loop_id: str, metrics: dict, verify: str = "passed", learning: str = "no method patch"):
    run_dir = root / "runs" / loop_id
    run_dir.mkdir(parents=True)
    (run_dir / "METRICS.json").write_text(json.dumps(metrics), encoding="utf-8")
    (run_dir / "VERIFY.md").write_text(verify, encoding="utf-8")
    (run_dir / "LEARNING.md").write_text(learning, encoding="utf-8")


def test_ralph_method_evaluator_rewards_verified_runs(tmp_path):
    write_run(
        tmp_path,
        "LOOP-1",
        {
            "status": "done",
            "verification": {"type": "test", "passed": True, "evidence": "pytest passed"},
            "scores": {"acionabilidade": 0.9, "verificabilidade_factual": 0.9},
            "autoresearch": {"method_signal": "none", "experiment_recommended": False},
            "next_action": "Implement next small task",
        },
    )

    asset = RalphMethodAsset(tmp_path)
    evaluator = RalphMethodEvaluator(tmp_path)

    assert evaluator.measure(asset) >= 0.8


def test_ralph_method_evaluator_penalizes_missing_autoresearch(tmp_path):
    write_run(
        tmp_path,
        "LOOP-1",
        {
            "status": "done",
            "verification": {"type": "none", "passed": False},
            "scores": {},
            "next_action": "",
        },
    )

    asset = RalphMethodAsset(tmp_path)
    evaluator = RalphMethodEvaluator(tmp_path)

    assert evaluator.measure(asset) < 0.5
```

- [ ] **Step 2: Implement target**

Create `backend/autoresearch/targets/ralph_method.py`:

```python
"""Zero-LLM AutoResearch target for Ralph run quality."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

from .base import Asset, Constraints, Evaluator


class RalphMethodAsset(Asset):
    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)

    def path(self) -> Path:
        return self.project_root / ".ralph" / "TASK_TEMPLATE.md"

    def read(self) -> str:
        return self.path().read_text(encoding="utf-8") if self.path().exists() else ""

    def write(self, content: str) -> None:
        self.path().write_text(content, encoding="utf-8")

    def editable_sections(self) -> Dict[str, str]:
        return {"task_template": self.read()}


class RalphMethodConstraints(Constraints):
    def to_prompt(self) -> str:
        return (
            "Improve only Ralph method files. Do not modify product code, secrets, "
            "deployment, client publication, or production data."
        )

    def validate(self, asset_path: Path) -> bool:
        return asset_path.name in {"TASK_TEMPLATE.md", "VERIFY.md", "PM.md", "AUTORESEARCH.md", "RALPH.md"}


class RalphMethodEvaluator(Evaluator):
    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)

    @property
    def requires_llm(self) -> bool:
        return False

    def metric_name(self) -> str:
        return "ralph run quality score"

    def measure(self, asset: Asset) -> float:
        runs = self._load_runs()
        if not runs:
            return 0.0
        scores = [self._score_run(run) for run in runs]
        return round(sum(scores) / len(scores), 4)

    def _load_runs(self) -> List[Dict]:
        run_root = self.project_root / "runs"
        if not run_root.exists():
            return []
        loaded = []
        for metrics_path in sorted(run_root.glob("LOOP-*/METRICS.json")):
            try:
                loaded.append(json.loads(metrics_path.read_text(encoding="utf-8")))
            except Exception:
                loaded.append({})
        return loaded

    def _score_run(self, metrics: Dict) -> float:
        score = 0.0
        if metrics.get("status") == "done":
            score += 0.2
        verification = metrics.get("verification") or {}
        if verification.get("passed") is True and verification.get("type") != "none":
            score += 0.25
        if verification.get("evidence"):
            score += 0.1
        if metrics.get("next_action"):
            score += 0.15
        if metrics.get("autoresearch", {}).get("method_signal") is not None:
            score += 0.15
        scores = metrics.get("scores") or {}
        if scores.get("acionabilidade", 0) >= 0.7:
            score += 0.075
        if scores.get("verificabilidade_factual", 0) >= 0.7:
            score += 0.075
        return min(score, 1.0)
```

- [ ] **Step 3: Register CLI baseline target**

In `backend/autoresearch/cli.py`, add:

```python
def setup_ralph_target(args):
    """Configura alvo Ralph Method Quality."""
    from .targets.ralph_method import (
        RalphMethodAsset, RalphMethodConstraints, RalphMethodEvaluator,
    )
    from .targets.base import TargetConfig

    asset = RalphMethodAsset(PROJECT_ROOT)
    constraints = RalphMethodConstraints()
    evaluator = RalphMethodEvaluator(PROJECT_ROOT)

    return TargetConfig(
        name="ralph_method",
        description="Avaliacao zero-LLM da qualidade de runs Ralph",
        constraints=constraints,
        asset=asset,
        evaluator=evaluator,
        hypothesis_model=args.model or "haiku-tasks",
        max_hours=args.hours,
        budget_usd=args.budget,
    )
```

Add to `TARGET_BUILDERS`:

```python
"ralph": setup_ralph_target,
```

- [ ] **Step 4: Run tests and baseline**

Run:

```powershell
.\backend\.venv\Scripts\python.exe -m pytest backend\tests\test_autoresearch_ralph_method.py -q
.\backend\.venv\Scripts\python.exe -m backend.autoresearch.cli baseline ralph
```

Expected: tests pass and baseline prints a score. If fewer than 3 runs exist, the score may be low; that is acceptable and should be recorded, not patched around.

---

## Phase 6: Verification and Rollout

### Task 9: End-to-End Verification

**Files:**
- No new files required.

- [ ] **Step 1: Run backend targeted tests**

```powershell
.\backend\.venv\Scripts\python.exe -m pytest backend\tests\test_decision_readiness.py backend\tests\test_executive_package.py backend\tests\test_autoresearch_ralph_method.py -q
```

Expected: all targeted tests pass.

- [ ] **Step 2: Run broader backend tests if practical**

```powershell
.\backend\.venv\Scripts\python.exe -m pytest backend\tests -q
```

Expected: pass, or document unrelated pre-existing failures with exact test names.

- [ ] **Step 3: Run frontend build**

```powershell
npm run build
```

Expected: pass, or document unrelated pre-existing failures.

- [ ] **Step 4: Manual UX check**

Open the app locally and verify:

- Step 3 shows the existing quality gate plus one concrete next action.
- The report button remains blocked when the structural gate fails.
- Step 4 does not offer executive package creation for diagnostic or blocked reports.
- Step 4 offers package creation only for `delivery_status === "publishable"`.
- The UI does not expose "Ralph", "OpenSwarm", "AutoResearch", "handoff", or "specialist lane" to normal users.

- [ ] **Step 5: Ralph run record**

For the implementation run, create:

```text
runs/LOOP-YYYYMMDD-HHMMSS/
  TASK.md
  OUTPUT.md
  VERIFY.md
  AUDIT.md
  LEARNING.md
  METRICS.json
  NEXT.md
```

`METRICS.json.autoresearch.method_signal` must be filled even if no AutoResearch experiment is launched.

---

## Risk Review and Improvements

### Risk: Over-Orchestration

If Swarm is implemented as a runtime or default workflow, it will slow down Mirofish and add fragility. The plan restricts Swarm to `.ralph/SWARM.md` and composite package handoffs only.

### Risk: Fake Intelligence in the UI

A vague "AI recommendation" panel would not help users. The readiness service must return concrete actions tied to existing gates: generate report, wait, rerun simulation, review source, or build executive package.

### Risk: Weakening Delivery Gates

The readiness layer must never bypass `evaluate_report_system_gate()` or `Report.delivery_status()`. It only explains them and selects the next action.

### Risk: Exporting Unpublishable Material

The executive package service blocks unless `delivery_status() == "publishable"`.

### Risk: AutoResearch Optimizes Proxies

AutoResearch starts only after 3 to 5 real runs or one severe repeated blocker. Its first target is method quality, not production code.

### Risk: Confusing Non-Technical Users

Ralph, Swarm, and AutoResearch stay internal. Step 3 and Step 4 use product language: "Pronto para relatório", "Ajuste necessário", "Pacote executivo".

### Risk: Dirty Worktree

The repository currently has unrelated modified files. Each implementation task must inspect diffs before editing and avoid reverting unrelated changes.

---

## Self-Review

- **Spec coverage:** The plan covers Ralph, OpenSwarm, AutoResearch, current Mirofish architecture, UX improvement, intelligence improvement, and low-breakage implementation.
- **Maximum useful integration:** Ralph is execution discipline, Swarm is composite handoff only, AutoResearch is delayed until evidence exists, and Mirofish product intelligence stays central.
- **Main improvement over prior plan:** The first slice is now user-facing decision readiness, not internal method infrastructure.
- **No blind import:** No OpenSwarm runtime or dependency is introduced.
- **Gate preservation:** Report/export readiness depends on existing structural and delivery gates.
- **UX preservation:** Internal agent-method vocabulary is kept out of normal product UI.
- **Testability:** Each production feature has targeted backend tests and a frontend build check.
