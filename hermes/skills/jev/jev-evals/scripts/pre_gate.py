#!/usr/bin/env python3
"""Deterministic pre-gate for the JEV eval skill.

Reads an evidence JSON and returns PASS, RETRY, HUMAN or EVALUATE (meaning the
hard rules could not decide and the model must evaluate the criteria).

Evidence format:
{
  "attempt": 1,
  "max_attempts": 3,
  "tests_exit_code": 0,
  "build_exit_code": 0,
  "changed_files": ["backend/app/x.py"]
}
"""
from __future__ import annotations

import json
import sys
from fnmatch import fnmatch

HUMAN_PATTERNS = (
    "Dockerfile",
    ".github/workflows/*",
    "deploy/*",
    "vercel.json",
    "docker-compose*.yml",
    "docker-compose*.yaml",
)
# Mirrors the "never commit" list in AGENTS.md (item 6) and CLAUDE.md (section 8);
# .env variants are handled by _is_secret_env. Keep both lists in sync.
FORBIDDEN_PATTERNS = (
    "node_modules/*",
    "*/node_modules/*",
    "dist/*",
    "frontend/dist/*",
    "backend/uploads/*",
    ".vercel/*",
    "*/.vercel/*",
    "*.log",
)


ENV_TEMPLATE_SUFFIXES = (".example", ".sample", ".template", ".dist")


def _matches(path: str, patterns: tuple[str, ...]) -> bool:
    return any(fnmatch(path, pattern) for pattern in patterns)


def _is_secret_env(path: str) -> bool:
    """True for .env, .env.local, foo/.env.production; False for .env.example*."""
    name = path.rsplit("/", 1)[-1]
    if name != ".env" and not name.startswith(".env."):
        return False
    variant = name[len(".env"):]
    return not any(variant.startswith(suffix) for suffix in ENV_TEMPLATE_SUFFIXES)


def _is_forbidden(path: str) -> bool:
    return _is_secret_env(path) or _matches(path, FORBIDDEN_PATTERNS)


def _is_int(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _evidence_errors(evidence) -> list[str]:
    """Malformed evidence must never slip past the path rules."""
    if not isinstance(evidence, dict):
        return ["evidence must be a JSON object"]
    errors = []
    files = evidence.get("changed_files")
    if files is not None and not (
        isinstance(files, list) and all(isinstance(f, str) and f for f in files)
    ):
        errors.append("changed_files must be a list of non-empty strings")
    for key in ("tests_exit_code", "build_exit_code"):
        if evidence.get(key) is not None and not _is_int(evidence[key]):
            errors.append(f"{key} must be an integer or null")
    for key in ("attempt", "max_attempts"):
        if key in evidence and not (_is_int(evidence[key]) and evidence[key] >= 1):
            errors.append(f"{key} must be a positive integer")
    return errors


def decide(evidence: dict) -> dict:
    errors = _evidence_errors(evidence)
    if errors:
        return {"decision": "HUMAN", "reason": "invalid evidence: " + "; ".join(errors)}
    attempt = evidence.get("attempt", 1)
    max_attempts = evidence.get("max_attempts", 3)
    files = evidence.get("changed_files") or []
    tests_exit = evidence.get("tests_exit_code")
    build_exit = evidence.get("build_exit_code")

    if tests_exit is None and build_exit is None:
        return {"decision": "HUMAN", "reason": "no test or build evidence"}
    if not files:
        return {"decision": "HUMAN", "reason": "empty diff"}

    # Deploy and CI changes escalate first, even when the diff also has forbidden files.
    sensitive = [f for f in files if _matches(f, HUMAN_PATTERNS)]
    if sensitive:
        return {"decision": "HUMAN", "reason": "deploy or CI files changed", "files": sensitive}

    forbidden = [f for f in files if _is_forbidden(f)]
    if forbidden:
        return {
            "decision": "RETRY" if attempt < max_attempts else "HUMAN",
            "reason": "forbidden files in diff",
            "retry_instructions": [f"Remove {f} from the diff" for f in forbidden],
        }

    failing = [
        name
        for name, code in (("tests", tests_exit), ("build", build_exit))
        if code not in (None, 0)
    ]
    if failing:
        if attempt >= max_attempts:
            return {"decision": "HUMAN", "reason": f"{', '.join(failing)} failing after {attempt} attempts"}
        return {
            "decision": "RETRY",
            "reason": f"{', '.join(failing)} failing",
            "retry_instructions": [f"Fix the failing {name} step and rerun it" for name in failing],
        }

    return {"decision": "EVALUATE", "reason": "hard rules passed; evaluate criteria"}


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: pre_gate.py evidence.json", file=sys.stderr)
        return 2
    with open(sys.argv[1], encoding="utf-8") as handle:
        evidence = json.load(handle)
    print(json.dumps(decide(evidence), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
