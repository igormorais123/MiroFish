# PRD: Mirofish Systemic Intelligence UX

**Status:** Ready for implementation planning  
**Date:** 2026-05-06  
**Owner:** Mirofish INTEIA  
**Related plan:** `docs/superpowers/plans/2026-05-06-mirofish-systemic-intelligence-ux-plan.md`  
**Related DDD:** `docs/ddd/2026-05-06-mirofish-systemic-intelligence-ux-ddd.md`

---

## 1. Summary

Mirofish already has strong internal intelligence: simulation quality gates, report evidence audits, delivery governance, mission bundles, and report artifacts. The current product gap is interpretability. Users can see blocked states and audit panels, but still need to infer what to do next and when a report is safe to package for executive delivery.

This PRD defines a product-first readiness and delivery workflow:

1. Convert existing technical gates into a clear user-facing next action.
2. Keep report generation blocked when the simulation is not structurally ready.
3. Allow executive packaging only after a report is publishable.
4. Keep Ralph Loop, OpenSwarm-inspired handoffs, and AutoResearch internal to execution quality, not exposed as user-facing concepts.

## 2. Problem

The current Step 3 and Step 4 experience exposes valuable audit information, but it does not consistently answer:

- Is this simulation ready for a report?
- If not, what is the next safe action?
- Is the report diagnostic, blocked, in progress, or publishable?
- Can the user create an executive package now?
- What evidence justifies the product state?

Without this layer, users may treat diagnostic or incomplete material as deliverable, or may get blocked without knowing which action improves the state.

## 3. Goals

- Make Mirofish feel more intelligent by converting technical evidence into explicit product guidance.
- Reduce user uncertainty at the report boundary.
- Preserve all existing structural gates and evidence audits.
- Add executive packaging only for reports that are already publishable.
- Keep internal agent-method complexity out of the user interface.
- Provide a clean implementation path for Ralph-driven execution.

## 4. Non-Goals

- No OpenSwarm runtime import.
- No autonomous multi-agent production daemon.
- No automatic client publication.
- No automatic paid LLM, Apify, deploy, email, CRM, or calendar action.
- No bypass of `evaluate_report_system_gate()`.
- No package generation for diagnostic or blocked reports.
- No visible product labels such as "Ralph", "Swarm", "AutoResearch", "handoff", or "specialist lane".

## 5. Users

### Primary User: Strategic Operator

Needs to run simulations, understand when outputs are reliable, and produce client-ready strategic material.

Pain points:

- Does not want to inspect raw audit JSON.
- Needs confidence that a report is publishable.
- Needs one concrete next action when blocked.

### Secondary User: Technical Maintainer

Needs deterministic states, tests, clear service boundaries, and no weakening of governance.

Pain points:

- UI states can drift from backend truth.
- Export logic can become unsafe if separated from report status.
- Internal agent-method files can create unnecessary complexity if treated as runtime product code.

## 6. Product Principles

- **Evidence first:** all readiness states come from existing simulation/report evidence.
- **One next action:** users should see a single safest next action, not a generic explanation.
- **No fake intelligence:** the product should not invent advice that is not tied to gates or artifacts.
- **No hidden bypass:** readiness explains gates; it does not override them.
- **Internal complexity stays internal:** Ralph, Swarm, and AutoResearch improve engineering flow, not normal UI language.
- **Package after approval:** executive packaging is downstream of publishable report status.

## 7. User Journey

### Step 3: After Simulation

Current:

- User sees platform progress and quality gate.
- Report button may be blocked.
- Blocking issue may be visible.

Target:

- User sees quality gate plus a readiness panel.
- The panel says one of:
  - `Pronto para relatorio`
  - `Ajuste necessario`
  - `Execucao diagnostica`
  - `Relatorio em andamento`
  - `Pronto para pacote executivo`
- The panel shows one concrete next action.
- The report button remains governed by existing gate logic.

### Step 4: Report and Delivery

Current:

- User sees report progress, custody/audit panels, mission bundle, artifacts, and blocked states.

Target:

- User sees whether the report is publishable or only diagnostic.
- Executive package controls appear only when `delivery_status === "publishable"`.
- Diagnostic/blocked reports never get a package action.
- Package generation creates an auditable manifest and evidence annex.

## 8. Functional Requirements

### FR1: Decision Readiness Service

The backend must expose a product-level readiness object for a simulation.

Endpoint:

```text
GET /api/simulation/<simulation_id>/readiness
```

Response shape:

```json
{
  "success": true,
  "data": {
    "simulation_id": "sim_1",
    "project_id": "proj_1",
    "graph_id": "graph_1",
    "simulation_status": "completed",
    "report_id": "report_1",
    "report_delivery_status": "publishable",
    "status": "ready_for_export",
    "ready_for_report": false,
    "ready_for_export": true,
    "blocking_issues": [],
    "next_action": {
      "kind": "build_executive_package",
      "label": "Gerar pacote executivo auditavel",
      "enabled": true,
      "reason": ""
    },
    "gate": {},
    "metrics": {}
  }
}
```

Accepted `status` values:

- `missing`
- `blocked`
- `ready_for_report`
- `report_in_progress`
- `report_blocked`
- `diagnostic_only`
- `ready_for_export`

Accepted `next_action.kind` values:

- `select_simulation`
- `finish_simulation`
- `fix_simulation_quality`
- `review_source_material`
- `review_blockers`
- `generate_report`
- `wait_report`
- `regenerate_report`
- `rerun_complete_simulation`
- `build_executive_package`

### FR2: Readiness Must Use Existing Gates

The readiness service must call:

- `SimulationManager.get_simulation()`
- `ProjectManager.get_extracted_text()`
- `evaluate_report_system_gate(require_completed_simulation=True)`
- `ReportManager.get_report_by_simulation()`
- `Report.delivery_status()` when a report exists

It must not reimplement or relax gate logic.

### FR3: Step 3 Readiness Panel

Step 3 must show a compact readiness panel near the existing quality gate.

The panel must show:

- readiness title;
- one next-action label;
- blocked, ready, or pending visual state.

The panel must not:

- expose internal Ralph/Swarm/AutoResearch vocabulary;
- enable report generation when the existing gate blocks it;
- add long instructional copy.

### FR4: Executive Package Service

The backend must generate an executive package only when:

```text
Report.delivery_status() == "publishable"
```

The package must include:

- `executive_summary.html`
- `evidence_annex.html`
- `executive_package_manifest.json`

The manifest must include:

- `report_id`
- `simulation_id`
- creation timestamp
- source delivery status
- generated file list
- artifact inputs used

### FR5: Step 4 Executive Package Control

Step 4 must offer package creation only when the report is publishable.

The control must be disabled or absent when:

- report is missing;
- report is in progress;
- report is blocked;
- report is diagnostic-only;
- evidence audit fails;
- structural gate fails.

### FR6: Internal Ralph/Swarm/AutoResearch Documentation

Internal method files may be updated, but only to support implementation discipline:

- `.ralph/SWARM.md`
- `.ralph/RALPH.md`
- `.ralph/TASK_TEMPLATE.md`
- `.ralph/METRICS.schema.json`
- `.ralph/AUTORESEARCH.md`

These concepts must not appear in normal product UI.

## 9. Non-Functional Requirements

### Reliability

- Readiness output must be deterministic for the same simulation/report artifacts.
- Package generation must fail closed for non-publishable reports.
- Missing optional artifacts must not crash package generation; they should be absent from the manifest inputs.

### Security and Governance

- No external services are called by readiness or package generation.
- No production/deploy/publication action occurs.
- No secrets are read or modified.
- Report delivery gates remain stricter, not weaker.

### Performance

- Readiness endpoint should run quickly enough for UI polling or refresh.
- It must not trigger long simulation, LLM generation, report generation, or package generation.
- Executive package generation should use local artifacts only.

### Maintainability

- Readiness logic must live in a focused service, not be scattered across Vue components.
- UI must consume a clear backend state instead of duplicating business rules.
- Tests must cover each readiness state that controls user action.

## 10. UX Requirements

### Tone

Use direct product language:

- `Pronto para relatorio`
- `Ajuste necessario`
- `Relatorio em andamento`
- `Execucao diagnostica`
- `Pronto para pacote executivo`

Avoid:

- internal method terms;
- long explanations;
- optimistic claims not backed by gate state.

### Visual Behavior

- Ready state: positive but restrained.
- Blocked/diagnostic state: warning, not failure panic.
- Pending state: neutral.
- Controls must not shift layout when the label changes.

## 11. Analytics and Success Metrics

Implementation success:

- Backend readiness tests pass.
- Frontend build passes.
- Existing report gate behavior remains intact.
- Executive package blocks non-publishable reports.
- Step 3 and Step 4 no longer require users to infer the next action from raw audit details.

Product success:

- Fewer blocked-report retries without clear reason.
- Faster operator decision after simulation completion.
- Fewer diagnostic reports treated as deliverables.
- Executive packages consistently include evidence annex and manifest.

## 12. Rollout

### Phase 1

Build `decision_readiness.py`, endpoint, and tests.

### Phase 2

Add Step 3 readiness panel and Step 4 readiness awareness.

### Phase 3

Add executive package service and Step 4 package control.

### Phase 4

Add minimal Ralph/Swarm internal documentation for composite packages.

### Phase 5

After 3 to 5 Ralph runs, use AutoResearch to improve method files only.

## 13. Acceptance Criteria

- `GET /api/simulation/<simulation_id>/readiness` returns one canonical readiness state.
- A blocked structural gate produces `ready_for_report: false`.
- A passed gate with no report produces `ready_for_report: true`.
- A publishable report produces `ready_for_export: true`.
- A diagnostic report produces `ready_for_export: false`.
- Step 3 shows one concrete next action after simulation completion.
- Step 4 only enables package generation for publishable reports.
- Executive package generation creates manifest and evidence annex.
- No product UI exposes Ralph, OpenSwarm, Swarm, specialist lane, handoff, or AutoResearch.

## 14. Open Decisions

- Whether package download should be a zip in the first implementation or left as manifest plus artifact links.
- Whether Step 4 should show package history when a package already exists.
- Whether readiness should be refreshed automatically while report generation is in progress or only after major state transitions.

## 15. Execution Notes

Use the implementation plan for exact code steps:

```text
docs/superpowers/plans/2026-05-06-mirofish-systemic-intelligence-ux-plan.md
```

Use the DDD document for domain terms, state transitions, invariants, and service boundaries:

```text
docs/ddd/2026-05-06-mirofish-systemic-intelligence-ux-ddd.md
```
