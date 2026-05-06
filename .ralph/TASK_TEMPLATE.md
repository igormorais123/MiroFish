---
id: MF-RL-001
status: ready
mode: code
owner: ralphloop
expected_minutes: 30
risk: low
labels: []
---

# Mirofish Task Title

## Intent

What should improve in Mirofish: backend gate, report quality, frontend state, AutoResearch harness, documentation, or P0.1 readiness.

## Acceptance

- [ ] Backend tests, frontend build, or a named targeted check proves the change.
- [ ] No hidden external API, paid data, deploy, or client-publication action occurred.
- [ ] Report/evidence/client governance remains stricter, not weaker.

## Required Evidence

Command output, test result, build result, local artifact, diff, or explicit safety stop.

## Scope

Do:

- Small useful change.

Do not:

- Unrelated refactor.
- Long simulation with LLM active unless explicitly approved.
- Edit `.env` or use secrets.

## Context

Relevant files, roadmap item, affected gate/report/frontend/API path, and whether the task touches external services or client deliverability.

## Blockers

Need for API key, paid service, long simulation, deploy, client claim, or unclear acceptance criteria.

## Handoff

Notes for the next loop if this becomes in_progress.

## AutoResearch Signal

Which method component might need improvement if this task is hard to execute: TASK_TEMPLATE, VERIFY, PM, SECURITY, AUTORESEARCH, none.
