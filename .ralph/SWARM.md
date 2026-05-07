# Ralph Swarm Contract

Mode: code

This file defines lightweight specialist lanes for RalphLoop work in Mirofish. It imports lessons from OpenSwarm, Helena/Efesto, Vox and AutoResearch without adding those systems as runtime dependencies.

## Operating Rule

- GitHub is the source of truth.
- Codex works only in `codex/*` branches and opens PRs.
- One Ralph run handles one bounded unit.
- AutoResearch scores method quality and recommends changes; it does not apply production patches automatically.
- External projects may provide patterns, prompts, rubrics and test ideas, but secrets, sessions, keys and private interactions stay out.

## Lanes

### research_intake

Collects the smallest useful context packet:

- current task;
- relevant repo files;
- current PR chain;
- recent blockers;
- evidence required for done.

Output: short context packet with assumptions and missing facts.

### method_mapper

Maps context to the right operating method:

- direct Codex implementation;
- Superpowers plan execution;
- Ralph run;
- AutoResearch baseline;
- security review;
- UX verification.

Output: one selected method plus reason.

### evaluator_designer

Defines verification before implementation expands:

- backend tests;
- frontend build;
- browser checks when UI changes;
- path safety checks;
- no `internal_path` in public responses;
- no runtime dependency on local sibling projects.

Output: acceptance checklist.

### patch_writer

Implements only the bounded unit:

- no main branch work;
- no unrelated refactor;
- no generated artifacts committed;
- no automatic patch from AutoResearch into production.

Output: commit-ready diff.

### red_team

Challenges the result before PR:

- path traversal;
- stale branch/PR base;
- hidden dependency on Helena/Vox/OpenSwarm;
- weak verification;
- user-facing confusion;
- leaked internal paths or secrets.

Output: findings or explicit no-findings statement.

## AutoResearch Targets

- `report_delivery`: scores readiness, delivery packet, method checklist, export bundle and path safety.
- `ralph`: scores Ralph method discipline, metrics schema and specialist lane coverage.

Default use is baseline measurement:

```powershell
python -m backend.autoresearch.cli baseline report_delivery
python -m backend.autoresearch.cli baseline ralph
```

Experiments may propose patches under `.autoresearch/experiments/`, but a human or PR workflow decides whether to apply them.
