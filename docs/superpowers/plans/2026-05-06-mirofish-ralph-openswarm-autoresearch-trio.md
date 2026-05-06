# Mirofish Ralph OpenSwarm AutoResearch Trio Implementation Plan

> **Superseded:** use `docs/superpowers/plans/2026-05-06-mirofish-systemic-intelligence-ux-plan.md` as the current plan. This earlier version is kept for context, but it starts too much from internal method infrastructure. The revised plan moves product decision readiness and user experience to the first implementation slice.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Ralph Loop as Mirofish's execution cadence, AutoResearch as the learning layer, and OpenSwarm-inspired specialist escalation as a controlled package pattern before building larger deliverables.

**Architecture:** Ralph owns the outer loop: one small task, real verification, durable run record, learning, next action. AutoResearch reads Ralph run artifacts and proposes method improvements without applying production changes automatically. OpenSwarm contributes only the useful pattern: specialist lanes, context packets, handoffs, and package integration when a task truly needs multiple artifact types.

**Tech Stack:** Markdown method files under `.ralph/`, local run artifacts under `runs/`, Python 3.11/3.12, pytest, existing `backend/autoresearch` target plugin pattern, JSON metrics, no OpenSwarm runtime dependency.

---

## Source Context

- RalphLoop source studied: `C:\Users\IgorPC\.claude\projects\ralphloop-autoresearch`.
- Ralph method files studied:
  - `ralphloop/references/method-ralph-autoresearch.md`
  - `ralphloop/references/local-architecture.md`
  - `ralphloop/references/efesto-autoresearch.md`
  - `ralphloop/references/openswarm-autoresearch.md`
  - `ralphloop/references/task-format.md`
  - `sources/ralph/RALPH.md`
  - `sources/ralph/README.md`
- Current Mirofish Ralph files:
  - `.ralph/RALPH.md`
  - `.ralph/LOOP.md`
  - `.ralph/PM.md`
  - `.ralph/AUTORESEARCH.md`
  - `.ralph/VERIFY.md`
  - `.ralph/SECURITY.md`
  - `.ralph/TASK_TEMPLATE.md`
  - `.ralph/METRICS.schema.json`
- Existing Mirofish AutoResearch package:
  - `backend/autoresearch/engine.py`
  - `backend/autoresearch/cli.py`
  - `backend/autoresearch/targets/base.py`
  - `backend/autoresearch/targets/frontend_perf.py`
  - `backend/autoresearch/targets/skill_prompt.py`
- Existing OpenSwarm-routing experiment:
  - `.autoresearch/experiments/openswarm-specialist-routing-v1/RANKING.md`
  - `.autoresearch/experiments/openswarm-specialist-routing-v1/PATCH_PROPOSTO.diff`
  - `.autoresearch/experiments/openswarm-specialist-routing-v1/DECISAO.md`

## Design Decision

Do not make Ralph another specialist inside a swarm. Do not make OpenSwarm the outer runtime. The stable triangle is:

```text
Ralph Loop      -> chooses one unit, executes, verifies, records
AutoResearch    -> scores run/method quality and proposes method patches
OpenSwarm idea  -> specialist handoffs only when a Ralph task is composite
Mirofish        -> product intelligence, report governance, evidence artifacts
```

Practical rule:

```text
single code/doc/test task -> Ralph simple
research + data + docs + deck package -> Ralph composite package with handoffs
method weakness across runs -> AutoResearch experiment
```

## Scope

### In First PR

- Apply the existing OpenSwarm-routing method patch to `.ralph`.
- Add `.ralph/SWARM.md` as the explicit composite-package contract.
- Extend `.ralph/METRICS.schema.json` with `swarm` and new AutoResearch method signals.
- Add a local, zero-LLM AutoResearch target that scores Ralph method/run quality.
- Expose the new target through `backend.autoresearch.cli baseline ralph`.
- Add tests for the Ralph method evaluator.
- Create a Ralph ticket that turns the auditable executive export plan into small executable Ralph units.

### Not In First PR

- No OpenSwarm runtime import.
- No Agency Swarm dependency.
- No autonomous external LLM, Apify, deploy, publish, git push, CRM, Slack, email, or calendar actions.
- No automated long-running Ralph daemon.
- No automatic application of AutoResearch production patches.

## File Structure

### Create

- `.ralph/SWARM.md`  
  Contract for when and how Ralph can escalate to specialist-style handoffs.

- `backend/autoresearch/targets/ralph_method.py`  
  Zero-LLM target that scores `.ralph` method files and completed `runs/LOOP-*` artifacts.

- `backend/tests/test_autoresearch_ralph_method.py`  
  Unit tests for method scoring, run scoring, and constraints.

- `.ralph/tickets/004-execute-auditable-export-plan.md`  
  Ralph ticket that starts implementation of the auditable executive export plan as small verified units.

### Modify

- `.ralph/RALPH.md`  
  Tell agents to read `.ralph/SWARM.md` only for composite packages.

- `.ralph/LOOP.md`  
  Add composite-package start/work rules.

- `.ralph/PM.md`  
  Add specialist routing without turning PM into executor.

- `.ralph/AUTORESEARCH.md`  
  Add lanes, context packet, and swarm-specific weak signals.

- `.ralph/TASK_TEMPLATE.md`  
  Add `specialist_lane`, `composite_package`, `specialists_needed`, and `Context Packet`.

- `.ralph/METRICS.schema.json`  
  Add `swarm` object and AutoResearch signals for weak handoff/integration.

- `.ralph/VERIFY.md`  
  Add package-level integration verification.

- `backend/autoresearch/cli.py`  
  Add `ralph` baseline target.

- `docs/superpowers/plans/2026-05-06-mirofish-auditable-executive-export.md`  
  Mark this trio plan as prerequisite before export implementation.

---

## Task 1: Apply Ralph Specialist Method Layer

**Files:**
- Create: `.ralph/SWARM.md`
- Modify: `.ralph/RALPH.md`
- Modify: `.ralph/LOOP.md`
- Modify: `.ralph/PM.md`
- Modify: `.ralph/AUTORESEARCH.md`
- Modify: `.ralph/TASK_TEMPLATE.md`
- Modify: `.ralph/VERIFY.md`

- [ ] **Step 1: Create `.ralph/SWARM.md`**

Create `.ralph/SWARM.md`:

```markdown
# Ralph Composite Package Contract

OpenSwarm inspires this file, but Mirofish does not import OpenSwarm runtime here.

## Rule

Ralph remains the outer loop. A composite package is allowed only when one Ralph task requires two or more independently verifiable artifact types.

## Use Ralph Simple When

- The task changes one code path, test, doc, prompt, gate, or UI state.
- Acceptance criteria are still vague.
- The task touches secrets, production, deploy, publication, paid APIs, legal/reputational claims, or client-delivery status.
- The bottleneck is unclear specification, weak verification, or security.

## Use Composite Package When

- The task needs multiple artifact types such as research, data, docs, slides, preview, or adversarial review.
- Inputs are stable enough to hand off.
- Each artifact has a path, evidence, and acceptance criterion.
- Integration can be verified before closing.

## Allowed Specialist Lanes

- `executor`: code or doc change with direct verification.
- `research_intake`: read-only source study and factual context packet.
- `method_mapper`: map source/run learning into Ralph method changes.
- `evaluator_designer`: define rubric, corpus, score, or check.
- `patch_writer`: produce ranking, scores, proposed diff, and decision record.
- `red_team`: adversarial review of evidence, scope, safety, and integration.
- `docs`: write structured report, summary, plan, or one-pager from verified inputs.
- `data`: compute tables, metrics, or charts from local data only.
- `slides`: prepare deck artifacts from approved narrative only.
- `visual`: prepare visual assets only when explicitly required.

## Handoff Template

Every handoff file in `runs/LOOP-*/HANDOFFS/` must contain:

```text
objective:
specialist_lane:
inputs:
constraints:
required_evidence:
expected_artifact:
output_path:
acceptance:
block_when:
```

## Specialist Return Template

Every specialist output must include:

```text
summary:
files_created:
evidence:
limits:
next_dependency:
```

## Package Folder

When `composite_package: true`, the run must include:

```text
runs/LOOP-YYYYMMDD-HHMMSS/
  PACKAGE_PLAN.md
  HANDOFFS/
  ARTIFACTS/
  INTEGRATION.md
```

## Integration Check

`INTEGRATION.md` must explain:

- artifacts combined;
- evidence used;
- contradictions found and resolved;
- remaining limits;
- whether the package is ready, blocked, partial, or failed.
```

- [ ] **Step 2: Update `.ralph/RALPH.md`**

Add this bullet under the `## Context` list:

```markdown
- Read `.ralph/SWARM.md` only when the selected task has `composite_package: true` or asks for multiple specialist artifact types.
```

Add this bullet under `## Constraints`:

```markdown
- Use specialist escalation only for explicit composite packages; otherwise keep the Ralph cycle simple.
```

- [ ] **Step 3: Update `.ralph/LOOP.md`**

Add this item to the `## Start` numbered list:

```markdown
7. If the task has `composite_package: true`, read `.ralph/SWARM.md` before planning handoffs.
```

Replace the first item under `## Work` with:

```markdown
1. Copy the task into a new `runs/LOOP-YYYYMMDD-HHMMSS/TASK.md`. If `composite_package: true`, first create `PACKAGE_PLAN.md` and explicit specialist handoffs.
```

- [ ] **Step 4: Update `.ralph/PM.md`**

Add this section after `## Blocked First`:

```markdown
## Specialist Routing

Before marking a task ready, choose exactly one owner lane:

- `executor`: code/docs change with direct verification.
- `research_intake`: read-only source study.
- `method_mapper`: translate source/run learning into Ralph method changes.
- `evaluator_designer`: define scoring, corpus, rubric, or check.
- `patch_writer`: create proposed diff and decision record.
- `red_team`: adversarial review of risk, evidence, or complexity.
- `docs`: structured report, summary, plan, or one-pager from verified inputs.
- `data`: local metrics, tables, or charts.
- `slides`: deck work from approved narrative.
- `visual`: explicit visual asset work.

If a task needs multiple lanes, set `composite_package: true` and list `specialists_needed`. The PM routes and clarifies; it does not execute the work.
```

- [ ] **Step 5: Update `.ralph/AUTORESEARCH.md`**

Add this section after `## Initial Learning Agenda`:

```markdown
## Specialist Lanes

When AutoResearch studies an external method, repo, transcript, paper, or run history, classify the work into one lane before execution:

- `research_intake`: collect source facts, commit/date, transcript claims, and limits.
- `method_mapper`: map source facts to Ralph components such as `PM.md`, `VERIFY.md`, `TASK_TEMPLATE.md`, `SWARM.md`, or `SECURITY.md`.
- `evaluator_designer`: define rubric, score, cases, and evidence expected.
- `patch_writer`: produce `RANKING.md`, `scores.json`, `PATCH_PROPOSTO.diff`, and `DECISAO.md`.
- `red_team`: challenge over-complexity, unsafe permissions, weak evidence, and source contamination.

A lane is a responsibility label, not permission to spawn a large autonomous swarm. Keep one small unit per Ralph cycle unless `composite_package: true`.

## Context Packet

For external-source AutoResearch, prefer a small context packet over raw source dumps:

- source URL, commit, local path, or date;
- verified facts;
- claims that remain unverified;
- method component affected;
- proposed evidence;
- safety limits.

The next cycle should be able to continue from files without reading the original chat.
```

- [ ] **Step 6: Update `.ralph/TASK_TEMPLATE.md` frontmatter**

Replace the frontmatter block with:

```markdown
---
id: MF-RL-001
status: ready
mode: code
owner: ralphloop
specialist_lane: executor
expected_minutes: 30
risk: low
labels: []
composite_package: false
specialists_needed: []
---
```

- [ ] **Step 7: Add Context Packet to `.ralph/TASK_TEMPLATE.md`**

Add after the `## Context` section:

```markdown
## Context Packet

For research or AutoResearch tasks, include source URL/local path, commit/date, verified facts, unverified claims, affected method component, expected evidence, and safety limits.

For composite packages, list the stable inputs that each specialist may use and the files they must write.
```

- [ ] **Step 8: Update `.ralph/VERIFY.md`**

Add before `## Human Required`:

```markdown
## Composite Package Verification

When `composite_package: true`, prove both artifact quality and integration:

- every handoff has a corresponding output or blocker;
- every final artifact has a path and evidence;
- `INTEGRATION.md` explains contradictions, limits, and final package readiness;
- `METRICS.json.swarm.integration_verified` is true only after package-level verification.
```

- [ ] **Step 9: Run method-doc checks**

Run:

```powershell
Select-String -Path .ralph\*.md -Pattern "composite_package|specialist_lane|Context Packet|SWARM.md"
git diff --check -- .ralph
```

Expected:

```text
Select-String shows matches in RALPH.md, LOOP.md, PM.md, AUTORESEARCH.md, TASK_TEMPLATE.md, VERIFY.md
git diff --check emits no output
```

- [ ] **Step 10: Commit**

```powershell
git add .ralph/RALPH.md .ralph/LOOP.md .ralph/PM.md .ralph/AUTORESEARCH.md .ralph/TASK_TEMPLATE.md .ralph/VERIFY.md .ralph/SWARM.md
git commit -m "docs: add ralph specialist package method"
```

---

## Task 2: Extend Ralph Metrics Schema

**Files:**
- Modify: `.ralph/METRICS.schema.json`

- [ ] **Step 1: Update allowed AutoResearch method signals**

In `.ralph/METRICS.schema.json`, extend `properties.autoresearch.properties.method_signal.enum` so it contains:

```json
[
  "none",
  "weak_task",
  "weak_verification",
  "weak_pm",
  "weak_security",
  "weak_next_action",
  "repeat_blocker",
  "review_bottleneck",
  "weak_swarm_handoff",
  "weak_artifact_integration"
]
```

- [ ] **Step 2: Add `swarm` property**

Add this sibling property next to `autoresearch`, `review`, and `verification`:

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

- [ ] **Step 3: Validate JSON**

Run:

```powershell
Get-Content .ralph\METRICS.schema.json -Raw | ConvertFrom-Json | Out-Null
git diff --check -- .ralph\METRICS.schema.json
```

Expected:

```text
no output
```

- [ ] **Step 4: Commit**

```powershell
git add .ralph/METRICS.schema.json
git commit -m "docs: extend ralph metrics for specialist packages"
```

---

## Task 3: Ralph Method AutoResearch Target

**Files:**
- Create: `backend/autoresearch/targets/ralph_method.py`
- Create: `backend/tests/test_autoresearch_ralph_method.py`

- [ ] **Step 1: Write failing tests**

Create `backend/tests/test_autoresearch_ralph_method.py`:

```python
from pathlib import Path

from backend.autoresearch.targets.ralph_method import (
    RalphMethodAsset,
    RalphMethodConstraints,
    RalphMethodEvaluator,
)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_ralph_method_asset_collects_editable_sections(tmp_path):
    root = tmp_path
    _write(root / ".ralph" / "PM.md", "# PM\n\n## Specialist Routing\nok")
    _write(root / ".ralph" / "VERIFY.md", "# Verify\n\n## Composite Package Verification\nok")

    asset = RalphMethodAsset(root)
    sections = asset.editable_sections()

    assert ".ralph/PM.md" in sections
    assert ".ralph/VERIFY.md" in sections
    assert "Specialist Routing" in sections[".ralph/PM.md"]


def test_ralph_method_constraints_require_core_files(tmp_path):
    root = tmp_path
    _write(root / ".ralph" / "PM.md", "# PM")

    constraints = RalphMethodConstraints(root)

    assert constraints.validate(root / ".ralph" / "PM.md") is False

    for name in ["RALPH.md", "LOOP.md", "PM.md", "VERIFY.md", "AUTORESEARCH.md", "TASK_TEMPLATE.md"]:
        _write(root / ".ralph" / name, f"# {name}\n")

    assert constraints.validate(root / ".ralph" / "PM.md") is True


def test_ralph_method_evaluator_scores_complete_method_and_runs(tmp_path):
    root = tmp_path
    for name in ["RALPH.md", "LOOP.md", "PM.md", "VERIFY.md", "AUTORESEARCH.md", "TASK_TEMPLATE.md", "SWARM.md"]:
        _write(root / ".ralph" / name, "Context Packet\nspecialist_lane\ncomposite_package\nverification\n")
    _write(root / ".ralph" / "METRICS.schema.json", '{"properties": {"swarm": {}, "autoresearch": {}}}')
    run = root / "runs" / "LOOP-20260506-120000"
    for name in ["TASK.md", "OUTPUT.md", "VERIFY.md", "AUDIT.md", "LEARNING.md", "NEXT.md"]:
        _write(run / name, f"# {name}")
    _write(
        run / "METRICS.json",
        '{"verification": {"passed": true}, "autoresearch": {"method_signal": "none"}, "swarm": {"used": false}}',
    )

    score = RalphMethodEvaluator(root).measure(RalphMethodAsset(root))

    assert score >= 80
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
.\backend\.venv\Scripts\python.exe -m pytest backend\tests\test_autoresearch_ralph_method.py -q
```

Expected:

```text
ModuleNotFoundError: No module named 'backend.autoresearch.targets.ralph_method'
```

- [ ] **Step 3: Implement target**

Create `backend/autoresearch/targets/ralph_method.py`:

```python
"""AutoResearch target for RalphLoop method and run quality.

This evaluator is intentionally zero-LLM. It scores whether the local Ralph
method creates actionable, verifiable, safe, specialist-aware runs.
"""

from __future__ import annotations

import json
from pathlib import Path

from .base import Asset, Constraints, Evaluator


CORE_METHOD_FILES = [
    ".ralph/RALPH.md",
    ".ralph/LOOP.md",
    ".ralph/PM.md",
    ".ralph/VERIFY.md",
    ".ralph/AUTORESEARCH.md",
    ".ralph/TASK_TEMPLATE.md",
]

RUN_FILES = [
    "TASK.md",
    "OUTPUT.md",
    "VERIFY.md",
    "AUDIT.md",
    "LEARNING.md",
    "METRICS.json",
    "NEXT.md",
]


class RalphMethodAsset(Asset):
    """Asset wrapper for Ralph method files in a project root."""

    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)

    def path(self) -> Path:
        return self.project_root / ".ralph" / "TASK_TEMPLATE.md"

    def read(self) -> str:
        parts = []
        for rel in CORE_METHOD_FILES:
            path = self.project_root / rel
            if path.exists():
                parts.append(f"===== {rel} =====\n{path.read_text(encoding='utf-8')}")
        swarm = self.project_root / ".ralph" / "SWARM.md"
        if swarm.exists():
            parts.append(f"===== .ralph/SWARM.md =====\n{swarm.read_text(encoding='utf-8')}")
        return "\n\n".join(parts)

    def write(self, content: str) -> None:
        raise NotImplementedError("RalphMethodAsset is read-only in the first implementation.")

    def editable_sections(self) -> dict[str, str]:
        sections = {}
        for rel in CORE_METHOD_FILES + [".ralph/SWARM.md"]:
            path = self.project_root / rel
            if path.exists():
                sections[rel] = path.read_text(encoding="utf-8")
        return sections


class RalphMethodConstraints(Constraints):
    """Safety constraints for Ralph method AutoResearch."""

    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)

    def to_prompt(self) -> str:
        return (
            "Improve RalphLoop method files only. Preserve one small unit per cycle, "
            "real verification, durable handoff, no production/deploy/external actions, "
            "and AutoResearch as proposed patches rather than automatic production edits."
        )

    def validate(self, asset_path: Path) -> bool:
        return all((self.project_root / rel).exists() for rel in CORE_METHOD_FILES)


class RalphMethodEvaluator(Evaluator):
    """Scores Ralph method quality from files and completed runs."""

    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)

    @property
    def requires_llm(self) -> bool:
        return False

    def metric_name(self) -> str:
        return "Ralph method readiness score"

    def measure(self, asset: Asset) -> float:
        method_score = self._score_method_files()
        run_score = self._score_recent_runs()
        return round(method_score * 0.65 + run_score * 0.35, 2)

    def _score_method_files(self) -> float:
        score = 0.0
        existing = [rel for rel in CORE_METHOD_FILES if (self.project_root / rel).exists()]
        score += len(existing) / len(CORE_METHOD_FILES) * 30

        corpus = RalphMethodAsset(self.project_root).read().lower()
        checks = [
            "one small unit",
            "verific",
            "autoresearch",
            "method_signal",
            "context packet",
            "specialist_lane",
            "composite_package",
            "human required",
            "security",
            "handoff",
        ]
        score += sum(1 for check in checks if check in corpus) / len(checks) * 50

        schema = self.project_root / ".ralph" / "METRICS.schema.json"
        if schema.exists():
            try:
                parsed = json.loads(schema.read_text(encoding="utf-8"))
                props = parsed.get("properties", {})
                if "autoresearch" in props:
                    score += 10
                if "swarm" in props:
                    score += 10
            except json.JSONDecodeError:
                score -= 10
        return max(0.0, min(score, 100.0))

    def _score_recent_runs(self) -> float:
        runs_root = self.project_root / "runs"
        if not runs_root.exists():
            return 50.0

        runs = sorted([path for path in runs_root.glob("LOOP-*") if path.is_dir()], reverse=True)[:5]
        if not runs:
            return 50.0

        scores = [self._score_run(run) for run in runs]
        return sum(scores) / len(scores)

    def _score_run(self, run: Path) -> float:
        score = 0.0
        score += sum(1 for name in RUN_FILES if (run / name).exists()) / len(RUN_FILES) * 45

        metrics_path = run / "METRICS.json"
        if metrics_path.exists():
            try:
                metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
                if metrics.get("verification", {}).get("passed") is True:
                    score += 20
                if "autoresearch" in metrics:
                    score += 15
                if "swarm" in metrics:
                    score += 10
                if metrics.get("next_action"):
                    score += 10
            except json.JSONDecodeError:
                score -= 20
        return max(0.0, min(score, 100.0))
```

- [ ] **Step 4: Run tests**

Run:

```powershell
.\backend\.venv\Scripts\python.exe -m pytest backend\tests\test_autoresearch_ralph_method.py -q
```

Expected:

```text
3 passed
```

- [ ] **Step 5: Commit**

```powershell
git add backend/autoresearch/targets/ralph_method.py backend/tests/test_autoresearch_ralph_method.py
git commit -m "feat: score ralph method readiness"
```

---

## Task 4: Expose Ralph AutoResearch Baseline CLI

**Files:**
- Modify: `backend/autoresearch/cli.py`

- [ ] **Step 1: Add builder function**

Add this near the other `setup_*_target` functions:

```python
def setup_ralph_target(args):
    """Configura alvo RalphLoop Method Readiness."""
    from .targets.ralph_method import (
        RalphMethodAsset,
        RalphMethodConstraints,
        RalphMethodEvaluator,
    )
    from .targets.base import TargetConfig

    asset = RalphMethodAsset(PROJECT_ROOT)
    constraints = RalphMethodConstraints(PROJECT_ROOT)
    evaluator = RalphMethodEvaluator(PROJECT_ROOT)

    return TargetConfig(
        name="ralph_method",
        description="Pontuacao local da qualidade do metodo RalphLoop e runs",
        constraints=constraints,
        asset=asset,
        evaluator=evaluator,
        hypothesis_model=args.model or "haiku-tasks",
        max_hours=args.hours,
        budget_usd=args.budget,
    )
```

- [ ] **Step 2: Register target**

Update `TARGET_BUILDERS`:

```python
TARGET_BUILDERS = {
    "hookify": setup_hookify_target,
    "skill": setup_skill_target,
    "genetic": setup_genetic_target,
    "frontend": setup_frontend_target,
    "ralph": setup_ralph_target,
}
```

- [ ] **Step 3: Run baseline**

Run:

```powershell
.\backend\.venv\Scripts\python.exe -m backend.autoresearch.cli baseline ralph
```

Expected:

```text
Medindo baseline para: ralph_method
Metrica: Ralph method readiness score
Score baseline: <numeric score>
```

- [ ] **Step 4: Commit**

```powershell
git add backend/autoresearch/cli.py
git commit -m "feat: expose ralph autoresearch baseline"
```

---

## Task 5: Create Ralph Ticket For Auditable Executive Export

**Files:**
- Create: `.ralph/tickets/004-execute-auditable-export-plan.md`
- Modify: `docs/superpowers/plans/2026-05-06-mirofish-auditable-executive-export.md`

- [ ] **Step 1: Create export execution ticket**

Create `.ralph/tickets/004-execute-auditable-export-plan.md`:

```markdown
---
id: MF-RL-004
status: ready
mode: code
owner: ralphloop
specialist_lane: executor
expected_minutes: 45
risk: medium
labels: [report, export, governance]
composite_package: false
specialists_needed: []
---

# Executar plano de export executivo auditavel

## Intent

Implementar o primeiro incremento do plano `docs/superpowers/plans/2026-05-06-mirofish-auditable-executive-export.md` como ciclos pequenos Ralph, preservando gates de relatorio, auditoria de evidencias e separacao cliente/demo.

## Acceptance

- [ ] Comecar pela Task 1 do plano de export: contrato e testes de politica.
- [ ] Criar `runs/LOOP-*/TASK.md`, `OUTPUT.md`, `VERIFY.md`, `AUDIT.md`, `LEARNING.md`, `METRICS.json` e `NEXT.md`.
- [ ] Rodar verificacao objetiva da unidade escolhida.
- [ ] Preencher `METRICS.json.autoresearch`.
- [ ] Nao executar LLM externo, Apify, deploy, publish, push, simulacao longa ou acao com segredo.

## Required Evidence

- Teste backend alvo passando ou falhando de forma esperada no ciclo TDD.
- `git diff --check`.
- Run Ralph preenchido com aprendizado e proxima acao.

## Scope

Do:

- Uma unidade pequena do plano de export por ciclo.
- Preferir teste de politica/servico antes de API/UI.

Do not:

- Implementar todo o export em uma unica sessao Ralph.
- Copiar runtime OpenSwarm.
- Enfraquecer `delivery_status`, evidence audit, numeric audit ou client/demo governance.

## Context

- Plano: `docs/superpowers/plans/2026-05-06-mirofish-auditable-executive-export.md`
- Metodo: `.ralph/RALPH.md`
- Verificacao: `.ralph/VERIFY.md`
- AutoResearch: `.ralph/AUTORESEARCH.md`
- Produto: `backend/app/services/report_agent.py`, `backend/app/api/report.py`, `frontend/src/components/Step4Report.vue`

## Context Packet

source: OpenSwarm repo/transcript already summarized in `docs/openswarm_mirofish_opportunities_2026-05-06.md`
verified_facts: specialist handoff helps composite deliverables; Ralph remains one-unit loop
unverified_claims: none required for Task 1
affected_method_component: RALPH.md, VERIFY.md, AUTORESEARCH.md
expected_evidence: pytest + diff check + run files
safety_limits: no external calls, no production, no client-publication claim

## Blockers

If tests require missing local dependencies, mark blocked with command output and propose the smallest environment fix.

## Handoff

Next cycle should read this ticket, then execute only the next unchecked task from the export plan.

## AutoResearch Signal

method_signal: weak_next_action if the next step is not small enough; otherwise none.
candidate_targets: `.ralph/TASK_TEMPLATE.md`, `.ralph/VERIFY.md`
```

- [ ] **Step 2: Add prerequisite note to export plan**

At the top of `docs/superpowers/plans/2026-05-06-mirofish-auditable-executive-export.md`, after the header block, add:

```markdown
> **Prerequisite:** Execute `docs/superpowers/plans/2026-05-06-mirofish-ralph-openswarm-autoresearch-trio.md` first. The export implementation should then run as small Ralph units, not as one large uncontrolled implementation session.
```

- [ ] **Step 3: Run doc checks**

Run:

```powershell
Select-String -Path .ralph\tickets\004-execute-auditable-export-plan.md -Pattern "specialist_lane|Context Packet|METRICS.json.autoresearch"
Select-String -Path docs\superpowers\plans\2026-05-06-mirofish-auditable-executive-export.md -Pattern "Prerequisite"
git diff --check -- .ralph\tickets\004-execute-auditable-export-plan.md docs\superpowers\plans\2026-05-06-mirofish-auditable-executive-export.md
```

Expected:

```text
Select-String shows all requested matches
git diff --check emits no output
```

- [ ] **Step 4: Commit**

```powershell
git add .ralph/tickets/004-execute-auditable-export-plan.md docs/superpowers/plans/2026-05-06-mirofish-auditable-executive-export.md
git commit -m "docs: route export plan through ralph loop"
```

---

## Task 6: Final Verification

**Files:**
- No source changes unless verification reveals a real issue.

- [ ] **Step 1: Run method checks**

Run:

```powershell
Get-Content .ralph\METRICS.schema.json -Raw | ConvertFrom-Json | Out-Null
.\backend\.venv\Scripts\python.exe -m pytest backend\tests\test_autoresearch_ralph_method.py -q
.\backend\.venv\Scripts\python.exe -m backend.autoresearch.cli baseline ralph
git diff --check
```

Expected:

```text
schema parses
3 passed
baseline prints numeric score
git diff --check emits no output
```

- [ ] **Step 2: Run broader safe checks**

Run:

```powershell
.\backend\.venv\Scripts\python.exe -m pytest backend\tests -q
npm run build
```

Expected:

```text
backend tests pass
vite build succeeds
```

- [ ] **Step 3: Commit only if a verification note changed docs**

If verification reveals a note worth preserving, add it to `.ralph/PROJECT.md` under a new `## Trio Baseline Observed On 2026-05-06` section and commit:

```powershell
git add .ralph/PROJECT.md
git commit -m "docs: record ralph trio baseline"
```

If no note is needed, do not commit in this task.

---

## Self-Review

### Spec Coverage

- Ralph Loop studied and placed as execution cadence: Tasks 1, 5.
- AutoResearch studied and placed as learning layer: Tasks 2, 3, 4.
- OpenSwarm studied and limited to specialist handoff/package pattern: Tasks 1, 2.
- Mirofish current AutoResearch package reused instead of importing OpenSwarm: Tasks 3, 4.
- Existing executive export plan connected to Ralph execution: Task 5.
- Safety and no blind import: Scope and every task excludes runtime import, external calls, production actions, and weakened governance.

### Placeholder Scan

A dedicated placeholder scan found no banned placeholder markers or unspecified test instructions. Follow-up export implementation remains in its own existing plan.

### Type Consistency

- `specialist_lane`, `composite_package`, and `specialists_needed` are introduced in Task 1 and used in Task 5.
- `swarm` metrics are introduced in Task 2 and scored in Task 3.
- `RalphMethodAsset`, `RalphMethodConstraints`, and `RalphMethodEvaluator` are introduced in Task 3 and wired into CLI in Task 4.
- The export plan is not executed here; it is explicitly routed through Ralph by Task 5.

---

## Execution Order

1. Execute this trio plan first.
2. Then execute `docs/superpowers/plans/2026-05-06-mirofish-auditable-executive-export.md` one Ralph-sized unit at a time.
3. After 3 to 5 real runs, use `backend.autoresearch.cli baseline ralph` and the run metrics to decide whether to open a new `.autoresearch/experiments/<id>/PATCH_PROPOSTO.diff`.
