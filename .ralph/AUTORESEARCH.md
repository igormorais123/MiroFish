# AutoResearch for RalphLoop

Mode: code

AutoResearch is embedded in the Ralph loop. Ralph executes work; AutoResearch reads the traces, finds weak parts of the method, and proposes improvements.

## Local Architecture

Mirofish already contains a domain AutoResearch package at `backend/autoresearch`.

Use it as context when improving:

- prompt/evaluation targets;
- gate and report quality rubrics;
- frontend performance targets;
- task templates for P0.1 empirical validation.

## Always-On Contract

Every run must fill the `autoresearch` section of `METRICS.json`.

Every `LEARNING.md` must say whether the learning should become a method improvement.

Do not launch an experiment for every run. Accumulate evidence, then optimize the bottleneck.

## Initial Learning Agenda

1. Baseline implantation run.
2. Read-only P0.1 readiness assessment.
3. One bounded implementation or harness-improvement task.

After 3 runs, decide whether to propose a patch to `.ralph/VERIFY.md`, `.ralph/TASK_TEMPLATE.md`, or `.ralph/SECURITY.md`.

## Good Targets

- `.ralph/VERIFY.md`
- `.ralph/TASK_TEMPLATE.md`
- `.ralph/SECURITY.md`
- `.ralph/PM.md`
- `backend/autoresearch/targets/*` only after explicit task selection

## Outputs

- `.autoresearch/experiments/<id>/RANKING.md`
- `.autoresearch/experiments/<id>/scores.json`
- `.autoresearch/experiments/<id>/PATCH_PROPOSTO.diff`
- `.autoresearch/experiments/<id>/DECISAO.md`

## Rule

Recommend a patch. Do not apply production-affecting patches automatically.
