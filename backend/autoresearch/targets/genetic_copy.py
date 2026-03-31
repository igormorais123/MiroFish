"""
Alvo AutoResearch: Meta-otimizacao do Algoritmo Genetico de Copy.

Avaliacao: Roda o GA localmente contra banco de personas.
O AutoResearch otimiza os HIPERPARAMETROS do GA (populacao, taxas, pesos).
Metrica: Fitness do campeao + cobertura de segmentos.

Custo: Zero LLM na eval (GA roda local). So haiku pra gerar hipotese.
"""

import json
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Optional

from .base import Asset, Constraints, Evaluator


class GeneticCopyConstraints(Constraints):
    """Invariantes para otimizacao de hiperparametros do GA."""

    def to_prompt(self) -> str:
        return (
            "Voce otimiza hiperparametros de um algoritmo genetico de copy.\n\n"
            "INVARIANTES — nao violar:\n"
            "1. Manter a estrutura Python valida (sintaxe correta)\n"
            "2. Manter interfaces: CONFIG dict, PESOS dict, fitness_persona()\n"
            "3. Manter interface CLI (--banco, --tipo, --canal, --output)\n"
            "4. Limites de CONFIG:\n"
            "   - populacao: [20, 200]\n"
            "   - geracoes: [10, 100]\n"
            "   - taxa_crossover: [0.3, 0.95]\n"
            "   - taxa_mutacao: [0.05, 0.50]\n"
            "   - elitismo: [1, 10]\n"
            "   - torneio_k: [2, 7]\n"
            "   - convergencia_parada: [3, 15]\n"
            "5. PESOS devem somar 1.0 (tolerancia ±0.01)\n"
            "6. Nenhum peso individual < 0.05 ou > 0.50\n"
            "7. Nao alterar GENE_POOLS (conteudo dos genes)\n"
            "8. Nao alterar classe Cromossomo\n\n"
            "OBJETIVO: Maximizar fitness do campeao + penalizar baixa cobertura de segmentos.\n\n"
            "ESTRATEGIAS VALIDAS:\n"
            "- Ajustar balanco crossover/mutacao\n"
            "- Redistribuir pesos de fitness para melhorar cobertura\n"
            "- Ajustar tamanho de populacao vs geracoes (trade-off)\n"
            "- Modificar penalidades na fitness_persona()\n"
            "- Ajustar criterio de convergencia"
        )

    def validate(self, asset_path: Path) -> bool:
        """Verifica se o template_ag.py e valido."""
        content = asset_path.read_text(encoding="utf-8")

        # Verifica sintaxe Python
        try:
            compile(content, str(asset_path), "exec")
        except SyntaxError:
            return False

        # Verifica CONFIG presente
        if "CONFIG" not in content or "PESOS" not in content:
            return False

        # Verifica que PESOS soma ~1.0
        pesos_match = re.search(r'PESOS\s*=\s*\{([^}]+)\}', content)
        if pesos_match:
            values = re.findall(r':\s*([\d.]+)', pesos_match.group(1))
            total = sum(float(v) for v in values)
            if abs(total - 1.0) > 0.02:
                return False

        return True


class GeneticCopyAsset(Asset):
    """Asset: template_ag.py do algoritmo genetico."""

    def __init__(self, template_path: Path):
        self._path = template_path

    def path(self) -> Path:
        return self._path

    def read(self) -> str:
        return self._path.read_text(encoding="utf-8")

    def write(self, content: str) -> None:
        self._path.write_text(content, encoding="utf-8")

    def editable_sections(self) -> Dict[str, str]:
        """Extrai CONFIG, PESOS e trechos de fitness_persona."""
        content = self.read()
        sections = {}

        # CONFIG
        config_match = re.search(r'(CONFIG\s*=\s*\{[^}]+\})', content, re.DOTALL)
        if config_match:
            sections["CONFIG"] = config_match.group(1)

        # PESOS
        pesos_match = re.search(r'(PESOS\s*=\s*\{[^}]+\})', content, re.DOTALL)
        if pesos_match:
            sections["PESOS"] = pesos_match.group(1)

        # Penalty values in fitness
        penalty_lines = [
            line for line in content.split("\n")
            if "penalty" in line.lower() or "penalidade" in line.lower()
        ]
        if penalty_lines:
            sections["penalties"] = "\n".join(penalty_lines)

        return sections


class GeneticCopyEvaluator(Evaluator):
    """Avaliador que roda o GA e mede fitness do campeao."""

    def __init__(self, personas_path: Path, python_cmd: str = "python"):
        self.personas_path = personas_path
        self.python_cmd = python_cmd

    def metric_name(self) -> str:
        return "GA champion fitness (+ cobertura de segmentos)"

    @property
    def requires_llm(self) -> bool:
        return False

    def measure(self, asset: Asset) -> float:
        """Roda o GA e retorna score composto: fitness + cobertura."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            output_path = f.name

        try:
            result = subprocess.run(
                [
                    self.python_cmd, str(asset.path()),
                    "--banco", str(self.personas_path),
                    "--tipo", "pf",
                    "--canal", "email",
                    "--output", output_path,
                ],
                capture_output=True,
                text=True,
                timeout=180,
            )

            if result.returncode != 0:
                return 0.0

            with open(output_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            fitness = data.get("fitness", 0)

            # Bonus por cobertura de segmentos (se disponivel)
            segments = data.get("segment_analysis", {})
            if segments:
                coverage_scores = []
                for seg_name, seg_data in segments.items():
                    if isinstance(seg_data, dict) and "mean" in seg_data:
                        coverage_scores.append(seg_data["mean"])
                if coverage_scores:
                    min_coverage = min(coverage_scores)
                    # Penaliza se pior segmento esta muito abaixo da media
                    avg_coverage = sum(coverage_scores) / len(coverage_scores)
                    coverage_penalty = max(0, (avg_coverage - min_coverage) / avg_coverage)
                    fitness *= (1 - coverage_penalty * 0.2)

            return fitness

        except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
            return 0.0

        finally:
            Path(output_path).unlink(missing_ok=True)
