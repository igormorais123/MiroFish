"""
CLI para AutoResearch INTEIA.

Uso:
    python -m backend.autoresearch.cli --target hookify --budget 5 --hours 8
    python -m backend.autoresearch.cli --target skill --skill-name advogado-sobre-humano --budget 3
    python -m backend.autoresearch.cli --target genetic --personas /path/to/banco.json
    python -m backend.autoresearch.cli --target frontend --budget 2 --hours 4
    python -m backend.autoresearch.cli baseline report_delivery
    python -m backend.autoresearch.cli baseline ralph
    python -m backend.autoresearch.cli --baseline hookify  (mede score atual sem otimizar)
"""

import argparse
import json
import sys
from pathlib import Path

# Resolve paths relativos ao projeto
PROJECT_ROOT = Path(__file__).parent.parent.parent
BACKEND_ROOT = PROJECT_ROOT / "backend"
SKILLS_DIR = Path.home() / ".claude" / "skills"
HOOKIFY_DIR = Path.home() / ".claude"
CORPORA_DIR = Path(__file__).parent / "corpora"


def setup_hookify_target(args):
    """Configura alvo Hookify Rules."""
    from .targets.hookify_rules import (
        HookifyAsset, HookifyConstraints, HookifyEvaluator,
    )
    from .targets.base import TargetConfig

    corpus_path = CORPORA_DIR / "hookify_test_prompts.jsonl"
    asset = HookifyAsset(HOOKIFY_DIR)
    constraints = HookifyConstraints()
    evaluator = HookifyEvaluator(corpus_path, HOOKIFY_DIR)

    return TargetConfig(
        name="hookify_rules",
        description="Otimizacao de regras de deteccao hookify (F1 macro)",
        constraints=constraints,
        asset=asset,
        evaluator=evaluator,
        hypothesis_model=args.model or "haiku-tasks",
        max_hours=args.hours,
        budget_usd=args.budget,
    )


def setup_skill_target(args):
    """Configura alvo Skill Prompt."""
    from .targets.skill_prompt import (
        SkillPromptAsset, SkillPromptConstraints, SkillPromptEvaluator,
    )
    from .targets.base import TargetConfig

    skill_name = args.skill_name or "advogado-sobre-humano"
    skill_path = SKILLS_DIR / skill_name / "SKILL.md"

    if not skill_path.exists():
        print(f"Skill nao encontrada: {skill_path}")
        sys.exit(1)

    corpus_path = CORPORA_DIR / "ash_test_cases.jsonl"

    # LLM clients para gerar e avaliar respostas
    sys.path.insert(0, str(BACKEND_ROOT))
    from app.utils.llm_client import LLMClient
    from app.config import Config

    llm_gen = LLMClient(model=Config.LLM_PREMIUM_MODEL)
    llm_judge = LLMClient(model=Config.LLM_PREMIUM_MODEL)

    asset = SkillPromptAsset(skill_path)
    constraints = SkillPromptConstraints(
        skill_name=skill_name,
        protected_sections=["Tecnicas", "Fluxos", "Referencias"],
    )
    evaluator = SkillPromptEvaluator(corpus_path, llm_gen, llm_judge)

    return TargetConfig(
        name=f"skill_{skill_name}",
        description=f"Otimizacao do system prompt da skill {skill_name}",
        constraints=constraints,
        asset=asset,
        evaluator=evaluator,
        hypothesis_model=args.model or "haiku-tasks",
        eval_model=Config.LLM_PREMIUM_MODEL,
        max_hours=args.hours,
        budget_usd=args.budget,
    )


def setup_genetic_target(args):
    """Configura alvo Genetic Copy."""
    from .targets.genetic_copy import (
        GeneticCopyAsset, GeneticCopyConstraints, GeneticCopyEvaluator,
    )
    from .targets.base import TargetConfig

    template_path = SKILLS_DIR / "evolucao-genetica-copy" / "references" / "template_ag.py"
    personas_path = Path(args.personas) if args.personas else None

    if not template_path.exists():
        print(f"Template GA nao encontrado: {template_path}")
        sys.exit(1)

    if not personas_path or not personas_path.exists():
        print(f"Banco de personas nao encontrado: {personas_path}")
        sys.exit(1)

    asset = GeneticCopyAsset(template_path)
    constraints = GeneticCopyConstraints()
    evaluator = GeneticCopyEvaluator(personas_path)

    return TargetConfig(
        name="genetic_copy",
        description="Meta-otimizacao de hiperparametros do GA de copy",
        constraints=constraints,
        asset=asset,
        evaluator=evaluator,
        hypothesis_model=args.model or "haiku-tasks",
        max_hours=args.hours,
        budget_usd=args.budget,
    )


def setup_frontend_target(args):
    """Configura alvo Frontend Performance."""
    from .targets.frontend_perf import (
        FrontendPerfAsset, FrontendPerfConstraints, FrontendPerfEvaluator,
    )
    from .targets.base import TargetConfig

    frontend_dir = PROJECT_ROOT / "frontend"
    config_path = frontend_dir / "vite.config.js"

    if not config_path.exists():
        print(f"vite.config.js nao encontrado: {config_path}")
        sys.exit(1)

    asset = FrontendPerfAsset(config_path)
    constraints = FrontendPerfConstraints(frontend_dir)
    evaluator = FrontendPerfEvaluator(frontend_dir)

    return TargetConfig(
        name="frontend_perf",
        description="Otimizacao de performance do frontend Mirofish",
        constraints=constraints,
        asset=asset,
        evaluator=evaluator,
        hypothesis_model=args.model or "haiku-tasks",
        max_hours=args.hours,
        budget_usd=args.budget,
    )


def setup_report_delivery_target(args):
    """Configura alvo de score da fronteira de entrega de relatorios."""
    from .targets.report_delivery import (
        ReportDeliveryAsset, ReportDeliveryConstraints, ReportDeliveryEvaluator,
    )
    from .targets.base import TargetConfig

    asset = ReportDeliveryAsset(PROJECT_ROOT)
    constraints = ReportDeliveryConstraints(PROJECT_ROOT)
    evaluator = ReportDeliveryEvaluator(PROJECT_ROOT)

    return TargetConfig(
        name="report_delivery",
        description="Score deterministico da entrega verificavel de relatorios",
        constraints=constraints,
        asset=asset,
        evaluator=evaluator,
        hypothesis_model=args.model or "haiku-tasks",
        max_hours=args.hours,
        budget_usd=args.budget,
    )


def setup_ralph_target(args):
    """Configura alvo de score do metodo RalphLoop + AutoResearch."""
    from .targets.ralph_method import (
        RalphMethodAsset, RalphMethodConstraints, RalphMethodEvaluator,
    )
    from .targets.base import TargetConfig

    asset = RalphMethodAsset(PROJECT_ROOT)
    constraints = RalphMethodConstraints(PROJECT_ROOT)
    evaluator = RalphMethodEvaluator(PROJECT_ROOT)

    return TargetConfig(
        name="ralph_method",
        description="Score deterministico do metodo RalphLoop no Mirofish",
        constraints=constraints,
        asset=asset,
        evaluator=evaluator,
        hypothesis_model=args.model or "haiku-tasks",
        max_hours=args.hours,
        budget_usd=args.budget,
    )


TARGET_BUILDERS = {
    "hookify": setup_hookify_target,
    "skill": setup_skill_target,
    "genetic": setup_genetic_target,
    "frontend": setup_frontend_target,
    "report_delivery": setup_report_delivery_target,
    "ralph": setup_ralph_target,
}

READ_ONLY_TARGETS = {"report_delivery", "ralph"}


def run_baseline(args):
    """Mede score baseline sem modificar nada."""
    builder = TARGET_BUILDERS.get(args.baseline_target)
    if not builder:
        print(f"Alvo desconhecido: {args.baseline_target}")
        print(f"Alvos disponiveis: {', '.join(TARGET_BUILDERS.keys())}")
        sys.exit(1)

    target = builder(args)
    print(f"\nMedindo baseline para: {target.name}")
    print(f"Metrica: {target.evaluator.metric_name()}\n")

    score = target.evaluator.measure(target.asset)
    print(f"Score baseline: {score:.4f}")

    if args.baseline_target in {"report_delivery", "ralph"} and hasattr(target.evaluator, "detailed_report"):
        report = target.evaluator.detailed_report(target.asset)
        print("\nChecks:")
        for item in report.get("checks", []):
            marker = "PASS" if item.get("passes") else "FAIL"
            print(f"  {marker}: {item.get('id')}")
        if report.get("recommendations"):
            print("\nRecomendacoes:")
            for recommendation in report["recommendations"]:
                print(f"  - {recommendation}")

    # Relatorio detalhado se hookify
    if args.baseline_target == "hookify":
        from .targets.hookify_rules import HookifyEvaluator
        if isinstance(target.evaluator, HookifyEvaluator):
            report = target.evaluator.detailed_report(target.asset)
            print(f"\nDetalhes por categoria:")
            for cat, metrics in report.get("categories", {}).items():
                print(
                    f"  {cat:15s}: P={metrics['precision']:.3f} "
                    f"R={metrics['recall']:.3f} F1={metrics['f1']:.3f} "
                    f"(TP={metrics['tp']} FP={metrics['fp']} FN={metrics['fn']})"
                )
            if report.get("mismatches"):
                print(f"\nErros de classificacao ({len(report['mismatches'])} primeiros):")
                for mm in report["mismatches"][:10]:
                    print(f"  '{mm['prompt'][:60]}...' → esperado={mm['expected']}, obteve={mm.get('got', '?')}")

    return score


def main():
    parser = argparse.ArgumentParser(
        description="AutoResearch INTEIA — Loop autonomo de otimizacao",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command")

    # Comando: run
    run_parser = subparsers.add_parser("run", help="Executa loop de otimizacao")
    run_parser.add_argument("--target", required=True, choices=[name for name in TARGET_BUILDERS if name not in READ_ONLY_TARGETS])
    run_parser.add_argument("--budget", type=float, default=5.0, help="Budget em USD")
    run_parser.add_argument("--hours", type=float, default=8.0, help="Horas maximas")
    run_parser.add_argument("--model", default=None, help="Modelo para hipoteses")
    run_parser.add_argument("--skill-name", default=None, help="Nome da skill (alvo skill)")
    run_parser.add_argument("--personas", default=None, help="Caminho do banco de personas (alvo genetic)")
    run_parser.add_argument("--verbose", action="store_true", default=True)

    # Comando: baseline
    base_parser = subparsers.add_parser("baseline", help="Mede score baseline")
    base_parser.add_argument("baseline_target", choices=TARGET_BUILDERS.keys())
    base_parser.add_argument("--skill-name", default=None)
    base_parser.add_argument("--personas", default=None)
    base_parser.add_argument("--model", default=None)
    base_parser.add_argument("--budget", type=float, default=5.0)
    base_parser.add_argument("--hours", type=float, default=8.0)

    args = parser.parse_args()

    if args.command == "baseline":
        run_baseline(args)
    elif args.command == "run":
        target_config = TARGET_BUILDERS[args.target](args)

        # Setup LLM client para hipoteses
        sys.path.insert(0, str(BACKEND_ROOT))
        from app.utils.llm_client import LLMClient
        llm_hyp = LLMClient(model=target_config.hypothesis_model)

        from .engine import AutoResearchEngine
        engine = AutoResearchEngine(
            target=target_config,
            llm_client_hypothesis=llm_hyp,
        )
        result = engine.run(verbose=args.verbose)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
