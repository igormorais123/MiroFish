"""
Alvo AutoResearch: Otimizacao de System Prompts de Skills.

Avaliacao: Envia casos de teste ao LLM com a skill como system prompt.
Avalia respostas em 4 dimensoes com modelo avaliador (juiz LLM).
Metrica: Score composto ponderado (0-10).

Custo: ~$0.02/experimento (N casos x 2 chamadas sonnet por caso).
"""

import json
import statistics
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base import Asset, Constraints, Evaluator


class SkillPromptConstraints(Constraints):
    """Invariantes para otimizacao de system prompts de skills INTEIA."""

    def __init__(self, skill_name: str, protected_sections: List[str] = None):
        self.skill_name = skill_name
        self.protected_sections = protected_sections or []

    def to_prompt(self) -> str:
        protected = "\n".join(f"  - {s}" for s in self.protected_sections)
        return (
            f"Voce otimiza o system prompt da skill '{self.skill_name}' do ecossistema INTEIA.\n\n"
            f"INVARIANTES — nao violar:\n"
            f"1. Manter YAML frontmatter valido (name, description, allowed-tools)\n"
            f"2. Manter TODAS as secoes existentes (nao remover, apenas reescrever)\n"
            f"3. Manter todos os nomes de tecnicas, referencias e fluxos citados\n"
            f"4. Secoes protegidas (nao alterar conteudo, so reformatar):\n"
            f"{protected}\n"
            f"5. Nao ultrapassar 150% do tamanho original (eficiencia de tokens)\n"
            f"6. Manter idioma portugues brasileiro\n"
            f"7. Nao adicionar informacoes factuais nao presentes no original\n\n"
            f"OBJETIVO: Maximizar score composto (precisao * 0.4 + formato * 0.3 + "
            f"completude * 0.2 + eficiencia * 0.1) nas respostas geradas pela skill.\n\n"
            f"ESTRATEGIAS VALIDAS:\n"
            f"- Reordenar instrucoes para priorizar as mais importantes\n"
            f"- Tornar instrucoes mais claras e diretas\n"
            f"- Adicionar exemplos concretos inline\n"
            f"- Remover redundancias\n"
            f"- Usar formatting (negrito, listas) para hierarquia visual\n"
            f"- Ajustar temperature hints e guardrails"
        )

    def validate(self, asset_path: Path) -> bool:
        content = asset_path.read_text(encoding="utf-8")
        # YAML frontmatter presente
        if not content.startswith("---"):
            return False
        parts = content.split("---", 2)
        if len(parts) < 3:
            return False
        # Nao vazio
        if len(content.strip()) < 100:
            return False
        return True


class SkillPromptAsset(Asset):
    """Asset: arquivo SKILL.md de uma skill."""

    def __init__(self, skill_path: Path):
        self._path = skill_path

    def path(self) -> Path:
        return self._path

    def read(self) -> str:
        return self._path.read_text(encoding="utf-8")

    def write(self, content: str) -> None:
        self._path.write_text(content, encoding="utf-8")

    def editable_sections(self) -> Dict[str, str]:
        """Extrai secoes editaveis por headings markdown."""
        content = self.read()
        sections = {}
        current_heading = "preamble"
        current_content = []

        for line in content.split("\n"):
            if line.startswith("## ") or line.startswith("### "):
                if current_content:
                    sections[current_heading] = "\n".join(current_content)
                current_heading = line.strip("# ").strip()
                current_content = [line]
            else:
                current_content.append(line)

        if current_content:
            sections[current_heading] = "\n".join(current_content)

        return sections


class SkillPromptEvaluator(Evaluator):
    """Avaliador LLM-as-judge para qualidade de respostas de skills."""

    def __init__(
        self,
        corpus_path: Path,
        llm_client_generate,
        llm_client_judge,
        dimensions: Optional[Dict[str, float]] = None,
    ):
        self.corpus_path = corpus_path
        self.llm_gen = llm_client_generate
        self.llm_judge = llm_client_judge
        self.dimensions = dimensions or {
            "precisao": 0.40,
            "formato": 0.30,
            "completude": 0.20,
            "eficiencia": 0.10,
        }

    def metric_name(self) -> str:
        dims = " + ".join(f"{k}*{v}" for k, v in self.dimensions.items())
        return f"Score composto ({dims})"

    @property
    def requires_llm(self) -> bool:
        return True

    def _load_corpus(self) -> List[dict]:
        entries = []
        with open(self.corpus_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    entries.append(json.loads(line))
        return entries

    def _judge_response(self, case: dict, response: str) -> Dict[str, float]:
        """Usa LLM avaliador para pontuar resposta em cada dimensao."""
        judge_prompt = (
            "Voce e um avaliador rigoroso de respostas juridicas/profissionais.\n"
            "Avalie a resposta abaixo em 4 dimensoes (0-10 cada):\n\n"
            f"CASO DE TESTE:\n{case['prompt']}\n\n"
            f"RESPOSTA GERADA:\n{response[:3000]}\n\n"
        )
        if case.get("criteria"):
            judge_prompt += f"CRITERIOS ESPECIFICOS:\n{case['criteria']}\n\n"

        judge_prompt += (
            "Retorne JSON com scores de 0-10 E justificativa curta:\n"
            "{\n"
            '  "precisao": <0-10, corretude tecnica/juridica do conteudo>,\n'
            '  "formato": <0-10, aderencia ao formato esperado (peticao, parecer, etc)>,\n'
            '  "completude": <0-10, todos os pontos do caso foram abordados>,\n'
            '  "eficiencia": <0-10, concisao sem perder qualidade (10=perfeito, 0=verborreia)>,\n'
            '  "justificativa": "razao curta"\n'
            "}\n\n"
            "Seja rigoroso. 7 = aceitavel. 8 = bom. 9 = excelente. 10 = impossivel melhorar."
        )

        try:
            result = self.llm_judge.chat_json(
                messages=[{"role": "user", "content": judge_prompt}],
                temperature=0.1,
                max_tokens=512,
            )
            return {
                dim: float(result.get(dim, 5))
                for dim in self.dimensions
            }
        except (ValueError, KeyError):
            return {dim: 5.0 for dim in self.dimensions}

    def measure(self, asset: Asset) -> float:
        """Calcula score composto medio sobre todos os casos de teste."""
        corpus = self._load_corpus()
        skill_content = asset.read()
        scores = []

        for case in corpus:
            # Gera resposta usando a skill como system prompt
            try:
                response = self.llm_gen.chat(
                    messages=[
                        {"role": "system", "content": skill_content},
                        {"role": "user", "content": case["prompt"]},
                    ],
                    temperature=0.3,
                    max_tokens=2048,
                )
            except Exception:
                scores.append(0.0)
                continue

            # Avalia resposta
            dim_scores = self._judge_response(case, response)

            # Score composto ponderado
            composite = sum(
                dim_scores.get(dim, 0) * weight
                for dim, weight in self.dimensions.items()
            )
            scores.append(composite)

        return statistics.mean(scores) if scores else 0.0
