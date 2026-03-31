"""
Alvo AutoResearch: Otimizacao de Hookify Rules.

Avaliacao: regex puro contra corpus labelado — zero custo LLM.
Metrica: F1 macro (media ponderada por categoria).

As hookify rules detectam temas em prompts do usuario e sugerem skills.
Este evaluator mede precisao e recall de cada regra contra prompts reais.
"""

import re
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .base import Asset, Constraints, Evaluator


# Categorias de regras suggest-skill-*
SKILL_CATEGORIES = [
    "juridico", "estrategia", "comunicacao", "receita",
    "pesquisa", "infra", "relatorio", "google",
]

# Categorias auxiliares (nao sao suggest-skill, mas tem pattern)
AUX_CATEGORIES = ["depth", "energy"]

ALL_CATEGORIES = SKILL_CATEGORIES + AUX_CATEGORIES + ["none"]


def parse_hookify_rule(filepath: Path) -> Optional[dict]:
    """Extrai nome e pattern de um arquivo hookify."""
    content = filepath.read_text(encoding="utf-8")

    # Extrai YAML frontmatter
    if not content.startswith("---"):
        return None
    parts = content.split("---", 2)
    if len(parts) < 3:
        return None

    try:
        meta = yaml.safe_load(parts[1])
    except yaml.YAMLError:
        return None

    if not meta or not meta.get("enabled"):
        return None

    pattern = None
    for cond in meta.get("conditions", []):
        if cond.get("operator") == "regex_match":
            pattern = cond.get("pattern", "")
            break

    if not pattern:
        return None

    return {
        "name": meta.get("name", filepath.stem),
        "pattern": pattern,
        "filepath": filepath,
    }


def match_rules(hookify_dir: Path, prompt: str) -> List[str]:
    """Avalia todas as regras contra um prompt. Retorna categorias ativadas."""
    matched = []
    for filepath in sorted(hookify_dir.glob("hookify.*.local.md")):
        rule = parse_hookify_rule(filepath)
        if not rule:
            continue

        try:
            if re.search(rule["pattern"], prompt, re.IGNORECASE):
                # Extrai categoria do nome da regra
                name = rule["name"]
                if "juridico" in name:
                    matched.append("juridico")
                elif "estrategia" in name:
                    matched.append("estrategia")
                elif "comunicacao" in name:
                    matched.append("comunicacao")
                elif "receita" in name:
                    matched.append("receita")
                elif "pesquisa" in name:
                    matched.append("pesquisa")
                elif "infra" in name:
                    matched.append("infra")
                elif "relatorio" in name:
                    matched.append("relatorio")
                elif "google" in name:
                    matched.append("google")
                elif "depth" in name:
                    matched.append("depth")
                elif "energy" in name:
                    matched.append("energy")
        except re.error:
            continue

    return matched


class HookifyConstraints(Constraints):
    """Invariantes para otimizacao de hookify rules."""

    def to_prompt(self) -> str:
        return (
            "Voce otimiza regras de deteccao de temas (hookify rules) para o Claude Code.\n\n"
            "INVARIANTES — nao violar:\n"
            "1. Manter YAML frontmatter valido (--- delimitadores)\n"
            "2. Manter enabled: true em todas as regras\n"
            "3. Manter event: prompt e action: warn\n"
            "4. Manter operator: regex_match\n"
            "5. Modificar APENAS o campo 'pattern' (regex)\n"
            "6. Regex deve ser valida em Python (re.search com IGNORECASE)\n"
            "7. Nao remover categorias de palavras existentes, apenas adicionar ou refinar\n"
            "8. Regex nao pode ser vazia\n"
            "9. Acentos devem usar character class: [aá], [eé], [cç], [aã], [oõ]\n\n"
            "OBJETIVO: Maximizar F1 macro (precisao + recall balanceados) na deteccao correta "
            "de cada categoria de skill contra prompts reais do usuario."
        )

    def validate(self, asset_path: Path) -> bool:
        """Verifica se o asset modificado ainda e valido."""
        hookify_dir = asset_path.parent
        for filepath in hookify_dir.glob("hookify.suggest-skill-*.local.md"):
            rule = parse_hookify_rule(filepath)
            if rule is None:
                return False
            # Testa compilacao do regex
            try:
                re.compile(rule["pattern"])
            except re.error:
                return False
        return True


class HookifyAsset(Asset):
    """Asset: conjunto de arquivos hookify.*.local.md."""

    def __init__(self, hookify_dir: Path):
        self.hookify_dir = hookify_dir

    def path(self) -> Path:
        return self.hookify_dir

    def read(self) -> str:
        """Le todos os arquivos hookify concatenados."""
        parts = []
        for f in sorted(self.hookify_dir.glob("hookify.suggest-skill-*.local.md")):
            parts.append(f"=== {f.name} ===\n{f.read_text(encoding='utf-8')}")
        return "\n\n".join(parts)

    def write(self, content: str) -> None:
        """Escreve de volta nos arquivos individuais (split por delimitador)."""
        blocks = content.split("=== hookify.")
        for block in blocks:
            if not block.strip():
                continue
            # Reconstroi nome do arquivo
            first_line = block.split("\n", 1)[0]
            filename = "hookify." + first_line.split(" ===")[0]
            if not filename.endswith(".local.md"):
                continue
            filepath = self.hookify_dir / filename
            file_content = block.split(" ===\n", 1)[1] if " ===\n" in block else block
            filepath.write_text(file_content, encoding="utf-8")

    def editable_sections(self) -> Dict[str, str]:
        """Retorna um dict {nome_regra: pattern_regex} para cada regra."""
        sections = {}
        for f in sorted(self.hookify_dir.glob("hookify.suggest-skill-*.local.md")):
            rule = parse_hookify_rule(f)
            if rule:
                sections[rule["name"]] = f"pattern: {rule['pattern']}"
        return sections


class HookifyEvaluator(Evaluator):
    """Avaliador F1 macro para hookify rules contra corpus labelado."""

    def __init__(self, corpus_path: Path, hookify_dir: Path):
        self.corpus_path = corpus_path
        self.hookify_dir = hookify_dir

    def metric_name(self) -> str:
        return "F1 macro (precisao x recall por categoria)"

    @property
    def requires_llm(self) -> bool:
        return False

    def _load_corpus(self) -> List[dict]:
        """Carrega corpus JSONL de prompts labelados."""
        import json
        entries = []
        with open(self.corpus_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    entries.append(json.loads(line))
        return entries

    def measure(self, asset: Asset) -> float:
        """Calcula F1 macro sobre todas as categorias."""
        corpus = self._load_corpus()

        # Contadores por categoria
        tp = {cat: 0 for cat in ALL_CATEGORIES}
        fp = {cat: 0 for cat in ALL_CATEGORIES}
        fn = {cat: 0 for cat in ALL_CATEGORIES}

        for entry in corpus:
            prompt = entry["prompt"]
            expected = set(entry.get("labels", []))
            predicted = set(match_rules(self.hookify_dir, prompt))

            # Se esperado "none" e nada foi predito, acerto
            if "none" in expected and not predicted:
                tp["none"] += 1
                continue

            # Se esperado "none" mas algo foi predito, falso positivo
            if "none" in expected and predicted:
                fp_cats = predicted
                for cat in fp_cats:
                    fp[cat] += 1
                fn["none"] += 1
                continue

            # Categorias reais
            for cat in expected:
                if cat in predicted:
                    tp[cat] += 1
                else:
                    fn[cat] += 1
            for cat in predicted:
                if cat not in expected:
                    fp[cat] += 1

        # F1 por categoria (so categorias que aparecem no corpus)
        active_cats = set()
        for entry in corpus:
            for label in entry.get("labels", []):
                active_cats.add(label)

        f1_scores = []
        for cat in active_cats:
            precision = tp[cat] / (tp[cat] + fp[cat]) if (tp[cat] + fp[cat]) > 0 else 0
            recall = tp[cat] / (tp[cat] + fn[cat]) if (tp[cat] + fn[cat]) > 0 else 0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
            f1_scores.append(f1)

        # F1 macro = media simples das F1 por categoria
        return sum(f1_scores) / len(f1_scores) if f1_scores else 0.0

    def detailed_report(self, asset: Asset) -> dict:
        """Relatorio detalhado com metricas por categoria."""
        corpus = self._load_corpus()

        tp = {cat: 0 for cat in ALL_CATEGORIES}
        fp = {cat: 0 for cat in ALL_CATEGORIES}
        fn = {cat: 0 for cat in ALL_CATEGORIES}
        mismatches = []

        for entry in corpus:
            prompt = entry["prompt"]
            expected = set(entry.get("labels", []))
            predicted = set(match_rules(self.hookify_dir, prompt))

            if "none" in expected and not predicted:
                tp["none"] += 1
                continue
            if "none" in expected and predicted:
                for cat in predicted:
                    fp[cat] += 1
                fn["none"] += 1
                mismatches.append({"prompt": prompt[:100], "expected": list(expected), "got": list(predicted)})
                continue

            for cat in expected:
                if cat in predicted:
                    tp[cat] += 1
                else:
                    fn[cat] += 1
                    mismatches.append({"prompt": prompt[:100], "expected": cat, "got": list(predicted)})
            for cat in predicted:
                if cat not in expected:
                    fp[cat] += 1

        report = {}
        for cat in ALL_CATEGORIES:
            if tp[cat] + fp[cat] + fn[cat] == 0:
                continue
            precision = tp[cat] / (tp[cat] + fp[cat]) if (tp[cat] + fp[cat]) > 0 else 0
            recall = tp[cat] / (tp[cat] + fn[cat]) if (tp[cat] + fn[cat]) > 0 else 0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
            report[cat] = {
                "tp": tp[cat], "fp": fp[cat], "fn": fn[cat],
                "precision": round(precision, 3),
                "recall": round(recall, 3),
                "f1": round(f1, 3),
            }

        return {
            "categories": report,
            "mismatches": mismatches[:20],
            "f1_macro": self.measure(asset),
        }
