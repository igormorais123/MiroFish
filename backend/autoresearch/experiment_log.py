"""Log JSONL append-only para experimentos AutoResearch."""

import json
import time
from pathlib import Path
from typing import Any, Dict, Optional


class ExperimentLog:
    """Log crash-resilient de experimentos. Cada linha e um JSON independente."""

    def __init__(self, log_path: Path):
        self.log_path = log_path
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def append(
        self,
        experiment_id: int,
        hypothesis: str,
        score: float,
        best_score: float,
        kept: bool,
        delta: float = 0.0,
        details: Optional[Dict[str, Any]] = None,
        cost_usd: float = 0.0,
    ) -> None:
        """Appenda um resultado de experimento ao log."""
        entry = {
            "id": experiment_id,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "epoch": time.time(),
            "hypothesis": hypothesis[:500],
            "score": round(score, 6),
            "best_score": round(best_score, 6),
            "delta": round(delta, 6),
            "kept": kept,
            "cost_usd": round(cost_usd, 6),
        }
        if details:
            entry["details"] = details

        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def read_all(self) -> list:
        """Le todos os experimentos do log."""
        if not self.log_path.exists():
            return []
        entries = []
        with open(self.log_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    entries.append(json.loads(line))
        return entries

    def last_n(self, n: int = 5) -> list:
        """Retorna os N ultimos experimentos."""
        all_entries = self.read_all()
        return all_entries[-n:]

    def improvements_only(self) -> list:
        """Retorna apenas experimentos que foram mantidos."""
        return [e for e in self.read_all() if e.get("kept")]

    def summary(self) -> dict:
        """Resumo estatistico do log."""
        entries = self.read_all()
        if not entries:
            return {"total": 0, "kept": 0, "best_score": 0}
        kept = [e for e in entries if e.get("kept")]
        scores = [e["score"] for e in entries]
        return {
            "total": len(entries),
            "kept": len(kept),
            "hit_rate": round(len(kept) / len(entries), 3) if entries else 0,
            "best_score": max(scores),
            "worst_score": min(scores),
            "avg_score": round(sum(scores) / len(scores), 4),
            "first_score": entries[0]["score"],
            "last_score": entries[-1]["score"],
        }
