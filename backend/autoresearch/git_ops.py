"""Operacoes git para versionamento de experimentos AutoResearch."""

import subprocess
from pathlib import Path
from typing import Optional


class GitOps:
    """Gerencia snapshots, commits e reverts de assets experimentais."""

    def __init__(self, repo_path: Path):
        self.repo_path = repo_path
        self._ensure_repo()

    def _run(self, *args: str, check: bool = True) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["git"] + list(args),
            cwd=str(self.repo_path),
            capture_output=True,
            text=True,
            check=check,
        )

    def _ensure_repo(self) -> None:
        """Inicializa repo git se nao existir."""
        git_dir = self.repo_path / ".git"
        if not git_dir.exists():
            self._run("init")
            self._run("add", ".")
            self._run("commit", "-m", "autoresearch: baseline")

    def snapshot(self, asset_path: Path) -> str:
        """Salva estado atual do asset. Retorna hash do commit."""
        rel = asset_path.relative_to(self.repo_path)
        self._run("add", str(rel))
        result = self._run("rev-parse", "HEAD")
        return result.stdout.strip()

    def commit_improvement(self, message: str, asset_path: Path) -> str:
        """Commita melhoria. Retorna hash do novo commit."""
        rel = asset_path.relative_to(self.repo_path)
        self._run("add", str(rel))
        self._run("commit", "-m", message)
        result = self._run("rev-parse", "HEAD")
        return result.stdout.strip()

    def revert_asset(self, asset_path: Path) -> None:
        """Reverte asset para ultimo commit."""
        rel = asset_path.relative_to(self.repo_path)
        self._run("checkout", "HEAD", "--", str(rel))

    def get_history(self, limit: int = 20) -> list:
        """Retorna historico de commits recentes."""
        result = self._run(
            "log", f"--max-count={limit}",
            "--format=%H|%s|%ai",
        )
        entries = []
        for line in result.stdout.strip().split("\n"):
            if "|" in line:
                parts = line.split("|", 2)
                entries.append({
                    "hash": parts[0],
                    "message": parts[1],
                    "date": parts[2] if len(parts) > 2 else "",
                })
        return entries

    def current_hash(self) -> str:
        result = self._run("rev-parse", "HEAD")
        return result.stdout.strip()

    def has_changes(self, asset_path: Optional[Path] = None) -> bool:
        """Verifica se ha mudancas nao commitadas."""
        if asset_path:
            rel = asset_path.relative_to(self.repo_path)
            result = self._run("diff", "--name-only", str(rel), check=False)
        else:
            result = self._run("diff", "--name-only", check=False)
        return bool(result.stdout.strip())
