"""Classes base abstratas para alvos de AutoResearch."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class ExperimentResult:
    """Resultado de um unico experimento."""
    hypothesis: str
    score: float
    improved: bool
    delta: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


class Constraints(ABC):
    """Define invariantes que o agente NAO pode violar (equivale a program.md)."""

    @abstractmethod
    def to_prompt(self) -> str:
        """Gera o prompt de restricoes para o LLM gerar hipoteses."""
        ...

    @abstractmethod
    def validate(self, asset_path: Path) -> bool:
        """Verifica se o asset modificado ainda respeita as restricoes."""
        ...


class Asset(ABC):
    """Gerencia o arquivo editavel (equivale a train.py)."""

    @abstractmethod
    def path(self) -> Path:
        """Caminho do asset principal."""
        ...

    @abstractmethod
    def read(self) -> str:
        """Le o conteudo atual do asset."""
        ...

    @abstractmethod
    def write(self, content: str) -> None:
        """Escreve conteudo modificado no asset."""
        ...

    @abstractmethod
    def editable_sections(self) -> Dict[str, str]:
        """Retorna secoes editaveis do asset (para hipoteses focadas)."""
        ...


class Evaluator(ABC):
    """Mede a qualidade do asset modificado (equivale a prepare.py)."""

    @abstractmethod
    def measure(self, asset: Asset) -> float:
        """Retorna score numerico. Maior = melhor."""
        ...

    @abstractmethod
    def metric_name(self) -> str:
        """Nome legivel da metrica (ex: 'F1 macro', 'composite score')."""
        ...

    @property
    def requires_llm(self) -> bool:
        """Se True, avaliacao consome tokens LLM. Se False, avaliacao e gratuita."""
        return True


@dataclass
class TargetConfig:
    """Configuracao de um alvo de AutoResearch."""
    name: str
    description: str
    constraints: Constraints
    asset: Asset
    evaluator: Evaluator
    hypothesis_model: str = "haiku-tasks"
    eval_model: str = "sonnet-tasks"
    max_hours: float = 8.0
    budget_usd: float = 5.0
    min_improvement: float = 0.001
