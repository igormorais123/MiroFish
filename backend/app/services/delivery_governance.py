"""Politica de entrega para separar relatorio cliente de diagnostico tecnico."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Optional

from ..config import Config

CLIENT_MODES = {"client", "cliente", "production", "prod", "publicavel", "final"}
DEMO_MODES = {"demo", "smoke", "diagnostic", "diagnostico", "technical", "tecnico", "sandbox"}


@dataclass(frozen=True)
class DeliveryGovernancePolicy:
    """Contrato aplicado ao gate antes de qualquer relatorio sair do sistema."""

    mode: str
    label: str
    publishable: bool
    min_actions: int
    require_completed_simulation: bool
    require_source_text: bool
    fail_on_unsupported_quotes: bool
    enforce_diversity: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def normalize_delivery_mode(value: Optional[str]) -> str:
    """Normaliza nomes de modo sem permitir enfraquecimento acidental."""
    raw = (value or Config.REPORT_DELIVERY_MODE or "client").strip().lower()
    if raw in DEMO_MODES:
        return "demo"
    return "client"


def resolve_delivery_governance(
    simulation_config: Optional[dict[str, Any]] = None,
    *,
    requested_mode: Optional[str] = None,
    min_actions: Optional[int] = None,
    require_completed_simulation: Optional[bool] = None,
    require_source_text: Optional[bool] = None,
) -> DeliveryGovernancePolicy:
    """Resolve a politica efetiva combinando config da simulacao, API e ambiente."""
    config = simulation_config or {}
    governance = config.get("delivery_governance") if isinstance(config, dict) else {}
    governance = governance if isinstance(governance, dict) else {}

    mode = normalize_delivery_mode(requested_mode or governance.get("mode"))
    if mode == "demo":
        resolved_min_actions = Config.REPORT_DEMO_MIN_ACTIONS
        resolved_require_completed = Config.REPORT_DEMO_REQUIRE_COMPLETED_SIMULATION
        resolved_require_source = Config.REPORT_DEMO_REQUIRE_SOURCE_TEXT
        label = "Diagnostico tecnico"
        publishable = False
    else:
        resolved_min_actions = Config.REPORT_MIN_ACTIONS
        resolved_require_completed = Config.REPORT_REQUIRE_COMPLETED_SIMULATION
        resolved_require_source = Config.REPORT_REQUIRE_SOURCE_TEXT
        label = "Entrega cliente"
        publishable = True

    if mode == "demo":
        resolved_min_actions = int(governance.get("report_min_actions", resolved_min_actions) or 0)
        resolved_require_completed = bool(
            governance.get("require_completed_simulation", resolved_require_completed)
        )
        resolved_require_source = bool(governance.get("require_source_text", resolved_require_source))

    if min_actions is not None:
        resolved_min_actions = int(min_actions)
    if require_completed_simulation is not None:
        resolved_require_completed = bool(require_completed_simulation)
    if require_source_text is not None:
        resolved_require_source = bool(require_source_text)

    return DeliveryGovernancePolicy(
        mode=mode,
        label=str(governance.get("label") or label),
        publishable=publishable,
        min_actions=max(0, resolved_min_actions),
        require_completed_simulation=resolved_require_completed,
        require_source_text=resolved_require_source,
        fail_on_unsupported_quotes=Config.REPORT_FAIL_ON_UNSUPPORTED_QUOTES,
        enforce_diversity=Config.REPORT_REQUIRE_ACTION_TYPE_DIVERSITY,
    )
