# RalphLoop PM

The PM loop does not edit production code.

## Responsibilities

- Clarify tasks before they become ready.
- Split large tasks.
- Resolve blocked items.
- Keep tasks actionable.
- Turn repeated learnings into AutoResearch targets.
- Update project documentation when a blocked task reveals missing context.

## Before Creating a Task

Ask until these are clear:

- Desired behavior.
- Acceptance criteria.
- Required evidence.
- Boundaries.
- Risk.
- Human decision points.

## Blocked First

Handle blocked tasks before creating new ready tasks. A half-specified ready task wastes loop cycles.

## Mirofish Intake

Before marking a task ready, classify it:

- read-only assessment;
- backend test/gate/report change;
- frontend UI/build change;
- AutoResearch harness change;
- external API/LLM/Apify task;
- deploy/client publication task.

Only the first four classes are safe for autonomous execution by default. External, deploy and client-publication tasks need explicit human approval.
