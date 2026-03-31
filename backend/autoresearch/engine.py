"""
AutoResearch Engine — Loop autonomo de experimentacao.

Ciclo: hipotese (LLM) → modificacao (asset) → avaliacao (evaluator) → decisao (git)

Baseado na arquitetura de Andrej Karpathy (github.com/karpathy/autoresearch)
adaptada para o ecossistema INTEIA.
"""

import json
import sys
import time
import traceback
from pathlib import Path
from typing import Optional

from .cost_guard import CostGuard
from .experiment_log import ExperimentLog
from .git_ops import GitOps
from .targets.base import Asset, Constraints, Evaluator, TargetConfig


class AutoResearchEngine:
    """Loop principal de AutoResearch."""

    def __init__(
        self,
        target: TargetConfig,
        llm_client_hypothesis,
        llm_client_eval=None,
        results_dir: Optional[Path] = None,
    ):
        self.target = target
        self.llm_hyp = llm_client_hypothesis
        self.llm_eval = llm_client_eval or llm_client_hypothesis
        self.cost = CostGuard(
            budget_usd=target.budget_usd,
            max_hours=target.max_hours,
        )

        results_dir = results_dir or Path(__file__).parent / "results"
        run_id = time.strftime("%Y%m%d_%H%M%S")
        self.log = ExperimentLog(results_dir / f"{target.name}_{run_id}.jsonl")

        asset_dir = target.asset.path().parent
        self.git = GitOps(asset_dir)

    def _format_history(self, last_n: int = 5) -> str:
        """Formata historico recente para o LLM usar como contexto."""
        recent = self.log.last_n(last_n)
        if not recent:
            return "Nenhum experimento anterior."
        lines = []
        for e in recent:
            status = "KEPT" if e["kept"] else "REVERTED"
            lines.append(
                f"  #{e['id']}: score={e['score']:.4f} delta={e['delta']:+.4f} [{status}] "
                f"— {e['hypothesis'][:120]}"
            )
        return "\n".join(lines)

    def _generate_hypothesis(self, best_score: float, asset_content: str) -> str:
        """Gera uma hipotese de melhoria via LLM."""
        history = self._format_history()
        editable = self.target.asset.editable_sections()
        sections_desc = "\n".join(
            f"  [{k}]: {v[:200]}..." for k, v in editable.items()
        )

        prompt = (
            f"Voce e um otimizador autonomo. Seu trabalho: melhorar o score de "
            f"'{self.target.evaluator.metric_name()}'.\n\n"
            f"Score atual (melhor): {best_score:.4f}\n\n"
            f"Historico recente:\n{history}\n\n"
            f"Secoes editaveis do asset:\n{sections_desc}\n\n"
            f"Proponha UMA modificacao especifica. Responda em JSON:\n"
            f'{{"section": "nome_da_secao", "action": "descricao curta", '
            f'"old": "trecho exato a substituir", "new": "novo trecho"}}\n\n'
            f"Regras:\n"
            f"- UMA mudanca por vez\n"
            f"- Mudancas pequenas e testáveis\n"
            f"- Nao repita hipoteses que foram REVERTED\n"
            f"- Baseie-se nos padroes que foram KEPT"
        )

        response = self.llm_hyp.chat(
            messages=[
                {"role": "system", "content": self.target.constraints.to_prompt()},
                {"role": "user", "content": prompt},
            ],
            temperature=0.8,
            max_tokens=1024,
        )
        return response

    def _apply_hypothesis(self, hypothesis_json: str, asset: Asset) -> bool:
        """Aplica hipotese ao asset. Retorna True se aplicou."""
        try:
            # Limpa markdown fences se houver
            cleaned = hypothesis_json.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned.rsplit("```", 1)[0]
            cleaned = cleaned.strip()

            hyp = json.loads(cleaned)
            content = asset.read()

            old = hyp.get("old", "")
            new = hyp.get("new", "")

            if not old or not new or old == new:
                return False

            if old not in content:
                return False

            modified = content.replace(old, new, 1)
            asset.write(modified)
            return True

        except (json.JSONDecodeError, KeyError):
            return False

    def run(self, verbose: bool = True) -> dict:
        """Executa o loop de AutoResearch ate esgotar budget ou tempo."""
        if verbose:
            print(f"\n{'='*60}")
            print(f"AutoResearch INTEIA — {self.target.name}")
            print(f"Metrica: {self.target.evaluator.metric_name()}")
            print(f"Budget: ${self.target.budget_usd} | Max: {self.target.max_hours}h")
            print(f"{'='*60}\n")

        # Baseline
        baseline_score = self.target.evaluator.measure(self.target.asset)
        best_score = baseline_score
        experiment_id = 0

        self.log.append(
            experiment_id=0,
            hypothesis="BASELINE",
            score=baseline_score,
            best_score=baseline_score,
            kept=True,
            delta=0.0,
        )

        if verbose:
            print(f"Baseline: {baseline_score:.4f}\n")

        while self.cost.can_continue():
            experiment_id += 1

            try:
                # 1. Snapshot
                self.git.snapshot(self.target.asset.path())
                asset_content = self.target.asset.read()

                # 2. Hipotese
                hypothesis_raw = self._generate_hypothesis(best_score, asset_content)

                # 3. Aplicar
                applied = self._apply_hypothesis(hypothesis_raw, self.target.asset)
                if not applied:
                    if verbose:
                        print(f"  #{experiment_id}: hipotese invalida, pulando")
                    self.log.append(
                        experiment_id=experiment_id,
                        hypothesis=hypothesis_raw[:200],
                        score=best_score,
                        best_score=best_score,
                        kept=False,
                        delta=0.0,
                        details={"error": "hypothesis_not_applicable"},
                    )
                    continue

                # 4. Validar constraints
                if not self.target.constraints.validate(self.target.asset.path()):
                    self.git.revert_asset(self.target.asset.path())
                    if verbose:
                        print(f"  #{experiment_id}: violou constraints, revertendo")
                    self.log.append(
                        experiment_id=experiment_id,
                        hypothesis=hypothesis_raw[:200],
                        score=best_score,
                        best_score=best_score,
                        kept=False,
                        delta=0.0,
                        details={"error": "constraint_violation"},
                    )
                    continue

                # 5. Avaliar
                score = self.target.evaluator.measure(self.target.asset)
                delta = score - best_score

                # 6. Decisao
                if delta >= self.target.min_improvement:
                    self.git.commit_improvement(
                        f"autoresearch: {score:.4f} (+{delta:.4f})",
                        self.target.asset.path(),
                    )
                    best_score = score
                    kept = True
                    marker = "IMPROVED"
                else:
                    self.git.revert_asset(self.target.asset.path())
                    kept = False
                    marker = "reverted"

                self.log.append(
                    experiment_id=experiment_id,
                    hypothesis=hypothesis_raw[:200],
                    score=score,
                    best_score=best_score,
                    kept=kept,
                    delta=delta,
                )

                if verbose:
                    print(
                        f"  #{experiment_id}: {score:.4f} ({delta:+.4f}) [{marker}] "
                        f"| budget: ${self.cost.budget_remaining:.3f} "
                        f"| time: {self.cost.hours_elapsed:.1f}h"
                    )

            except KeyboardInterrupt:
                if verbose:
                    print("\nInterrompido pelo usuario.")
                break

            except Exception as exc:
                self.git.revert_asset(self.target.asset.path())
                self.log.append(
                    experiment_id=experiment_id,
                    hypothesis="ERROR",
                    score=best_score,
                    best_score=best_score,
                    kept=False,
                    details={"error": str(exc), "traceback": traceback.format_exc()},
                )
                if verbose:
                    print(f"  #{experiment_id}: ERRO — {exc}")

        # Resumo final
        summary = {
            "target": self.target.name,
            "baseline": baseline_score,
            "final_best": best_score,
            "total_improvement": round(best_score - baseline_score, 6),
            "improvement_pct": round(
                (best_score - baseline_score) / max(baseline_score, 0.001) * 100, 2
            ),
            "log": self.log.summary(),
            "cost": self.cost.summary(),
        }

        if verbose:
            print(f"\n{'='*60}")
            print(f"RESULTADO FINAL")
            print(f"  Baseline:  {baseline_score:.4f}")
            print(f"  Melhor:    {best_score:.4f}")
            print(f"  Melhoria:  {summary['total_improvement']:+.4f} ({summary['improvement_pct']:+.1f}%)")
            print(f"  Experimentos: {summary['log']['total']}")
            print(f"  Mantidos: {summary['log']['kept']} ({summary['log']['hit_rate']*100:.0f}%)")
            print(f"  Custo: ${summary['cost']['total_cost_usd']:.4f}")
            print(f"{'='*60}\n")

        return summary
