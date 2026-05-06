---
agent: claude -p
commands:
  - name: verify
    run: powershell -NoProfile -ExecutionPolicy Bypass -File .ralph/scripts/verify.ps1
args:
  - focus
---

# RalphLoop Package

Mode: code

## Goal

Run a simple autonomous loop: choose one ready unit, complete it, verify it, write handoff, and stop.

## Context

- Read `.ralph/PROJECT.md`.
- Read `.ralph/LOOP.md`.
- Read `.ralph/STATUS_VALUES.md`.
- Read `.ralph/SECURITY.md`.
- Read `.ralph/AUTORESEARCH.md` as the embedded learning contract.
- If `{{ args.focus }}` is present, treat it as the current focus.

## Feedback

Default verification output:

`{{ commands.verify }}`

## Constraints

- Exactly one unit per session.
- Retake `in_progress` work before new work.
- Do not guess unclear product decisions.
- Tests passing are not enough; verify behavior.
- Mark manual-only work as `manual-testing`.
- Record durable state in files, not in chat memory.
- Fill the `autoresearch` section of `METRICS.json` even when no experiment is launched.

## Exit Conditions

Exit after creating a run folder with `OUTPUT.md`, `VERIFY.md`, `AUDIT.md`, `LEARNING.md`, `METRICS.json`, and `NEXT.md`.

If running under an outer loop that watches for a signal, the final message must include `RALPH_DONE`.
