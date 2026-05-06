# RalphLoop Project

Target: C:\Users\IgorPC\.claude\projects\Mirofish INTEIA
Mode: code
Created: 2026-05-06T01:26:04

## Decision

Mirofish INTEIA is approved as the next RalphLoop + AutoResearch pilot after `sistema-sonhos-integrado`.

## Why This Project

- Real Git repository.
- Current branch: `codex/mirofish-upgrade-harness`.
- Baseline clean before implantation.
- Backend has 171 tests passing.
- Frontend build passes.
- Project already has `backend/autoresearch`, so the AutoResearch layer is native to the local architecture.
- Current roadmap has a concrete next step: P0.1 empirical validation with a new simulation.

## Why Not Paperclip First

The visible Paperclip folders under `C:\Users\IgorPC\.claude\projects` are mostly session/artifact folders without `.git`, `package.json`, `pyproject.toml`, or a clear verification harness. They are useful context, but not a good first target for approving an autonomous RalphLoop.

## Operating Principle

One small Mirofish task, one verification, one learning, one next action. Ralph executes; AutoResearch observes runs and improves the method.

## Local Commands

Backend tests:

```powershell
.\backend\.venv\Scripts\python.exe -m pytest backend\tests -q
```

Frontend build:

```powershell
npm run build
```

Useful read-only checks:

```powershell
git status --short
Get-Content .planning\STATE.md
Get-Content .planning\ROADMAP.md
```

## Baseline Observed On 2026-05-06

- Backend: `171 passed in 4.87s`
- Frontend: `npm run build` passed
- Git status: clean before RalphLoop files were added

## Safety Boundaries

- Do not edit `.env` or reveal secrets.
- Do not run paid/external Apify, LLM, deploy, Docker publish, VPS, or sync actions without explicit human instruction.
- Do not run a long real simulation automatically; prepare a bounded plan and dry/smoke evidence first.
- Client/publishable claims must preserve the system gate and evidence audit.
- Do not weaken report gates, citation audit, numeric audit, delivery governance, or client vs demo separation.

## AutoResearch Embedding

- Every run must fill `METRICS.json.autoresearch`.
- Good method targets here: `.ralph/VERIFY.md`, `.ralph/TASK_TEMPLATE.md`, `.ralph/SECURITY.md`, `.ralph/PM.md`.
- Also use the local `backend/autoresearch` package as domain context when optimizing prompts, gates, or evaluation harnesses.
