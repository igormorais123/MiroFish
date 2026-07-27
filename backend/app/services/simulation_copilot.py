"""
Copiloto operacional da simulacao.

Duas camadas com custos muito diferentes:

- pulso (build_pulse): leitura deterministica do que esta acontecendo agora —
  ritmo, distribuicao de acoes, anomalias. Sem LLM, barato o bastante para o
  operador manter aberto durante a run inteira.
- resposta (answer_operator_question): usa o LLM, e so quando o operador
  pergunta. O pulso entra como contexto para a resposta ficar ancorada no
  estado real em vez de generalidades.

A deteccao de anomalia e deterministica de proposito: um alerta de simulacao
travada nao pode depender de o modelo estar disponivel, nem custar token a
cada 5 segundos.
"""

from collections import Counter
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..utils.logger import get_logger
from .simulation_runner import AgentAction, SimulationRunner

logger = get_logger('mirofish.simulation_copilot')

# Janela de acoes considerada "agora" para ritmo e distribuicao.
RECENT_WINDOW = 120

# Sem nenhuma acao nova por mais que isso, com o runner marcado como rodando,
# o processo travou.
#
# As acoes nao chegam espacadas: a rodada inteira e gravada de uma vez (mediana
# de intervalo 0s) e entre rodadas ha uma pausa longa enquanto o modelo processa
# a rodada seguinte. O limiar precisa ficar acima dessa pausa, nao acima do
# intervalo medio. Medido em execucao real de 96 rodadas (sim_8bd24ddb56d1,
# 2026-07-26): maior intervalo entre acoes 284s, p99 186s. 600s deixa margem de
# ~2x sobre o pior caso observado sem perder um travamento de verdade.
STALL_SECONDS = 600

# Acima disso, a populacao convergiu para um comportamento so e a simulacao
# deixou de produzir variacao util.
DOMINANT_ACTION_RATIO = 0.80

# Acima disso, o volume de falhas deixa de ser ruido normal de execucao.
FAILURE_RATIO = 0.20

SEVERITY_ORDER = {"critical": 0, "warning": 1, "info": 2}


def _parse_timestamp(value: str) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def _seconds_between(older: Optional[datetime], newer: Optional[datetime]) -> Optional[float]:
    """Delta em segundos, podendo ser negativo. Quem chama decide o que fazer."""
    if older is None or newer is None:
        return None
    return (newer - older).total_seconds()


def _seconds_since(moment: Optional[datetime]) -> Optional[float]:
    """
    Ha quanto tempo isso aconteceu, do ponto de vista do relogio local.

    Um delta negativo significa que o timestamp gravado esta a frente do
    relogio de quem le (fuso divergente entre quem escreve o log e quem o le,
    ou desvio de relogio). Nesse caso o evento acabou de acontecer: devolver
    None faria o detector de simulacao travada parar de funcionar em silencio.
    """
    delta = _seconds_between(moment, datetime.now())
    if delta is None:
        return None
    return max(0.0, delta)


def _actions_per_minute(actions: List[AgentAction]) -> Optional[float]:
    """Ritmo medido na propria janela, nao no relogio da parede."""
    if len(actions) < 2:
        return None

    first = _parse_timestamp(actions[0].timestamp)
    last = _parse_timestamp(actions[-1].timestamp)
    elapsed = _seconds_between(first, last)

    if not elapsed or elapsed <= 0:
        return None

    return round(len(actions) / (elapsed / 60), 2)


def _detect_alerts(
    run_state: Any,
    recent: List[AgentAction],
    seconds_since_last_action: Optional[float],
) -> List[Dict[str, Any]]:
    """Anomalias que o operador precisa ver sem precisar perguntar."""
    alerts: List[Dict[str, Any]] = []
    is_running = getattr(run_state, "runner_status", None) == "running"

    if (
        is_running
        and seconds_since_last_action is not None
        and seconds_since_last_action > STALL_SECONDS
    ):
        alerts.append({
            "code": "stalled",
            "severity": "critical",
            "message": (
                f"Nenhuma ação nova há {int(seconds_since_last_action)}s com a simulação "
                "marcada como em execução. O processo provavelmente travou."
            ),
        })

    if recent:
        failures = sum(1 for action in recent if not action.success)
        failure_ratio = failures / len(recent)
        if failure_ratio > FAILURE_RATIO:
            alerts.append({
                "code": "high_failure_rate",
                "severity": "critical" if failure_ratio > 0.5 else "warning",
                "message": (
                    f"{failure_ratio:.0%} das últimas {len(recent)} ações falharam. "
                    "O resultado da simulação fica comprometido."
                ),
            })

        type_counts = Counter(action.action_type for action in recent)
        dominant_type, dominant_count = type_counts.most_common(1)[0]
        dominant_ratio = dominant_count / len(recent)
        if len(recent) >= 20 and dominant_ratio > DOMINANT_ACTION_RATIO:
            alerts.append({
                "code": "behavior_collapse",
                "severity": "warning",
                "message": (
                    f"{dominant_ratio:.0%} das ações recentes são {dominant_type}. "
                    "A população convergiu para um comportamento único."
                ),
            })

    # Uma plataforma parada enquanto a outra avanca costuma ser processo morto,
    # nao comportamento emergente.
    if is_running:
        twitter_alive = getattr(run_state, "twitter_running", False)
        reddit_alive = getattr(run_state, "reddit_running", False)
        twitter_done = getattr(run_state, "twitter_completed", False)
        reddit_done = getattr(run_state, "reddit_completed", False)

        if twitter_alive and not reddit_alive and not reddit_done:
            alerts.append({
                "code": "platform_silent",
                "severity": "warning",
                "message": "Reddit parou enquanto o Twitter continua rodando.",
            })
        elif reddit_alive and not twitter_alive and not twitter_done:
            alerts.append({
                "code": "platform_silent",
                "severity": "warning",
                "message": "Twitter parou enquanto o Reddit continua rodando.",
            })

    alerts.sort(key=lambda alert: SEVERITY_ORDER.get(alert["severity"], 9))
    return alerts


def build_pulse(simulation_id: str, window: int = RECENT_WINDOW) -> Dict[str, Any]:
    """
    Leitura deterministica do estado corrente da simulacao.

    Returns:
        {
            "simulation_id", "runner_status", "progress": {...},
            "activity": {...}, "alerts": [...], "headline": "..."
        }
    """
    run_state = SimulationRunner.get_run_state(simulation_id)

    if not run_state:
        return {
            "simulation_id": simulation_id,
            "runner_status": "idle",
            "progress": {},
            "activity": {},
            "alerts": [],
            "headline": "Nenhuma simulação em execução para este identificador.",
        }

    delta = SimulationRunner.get_actions_delta(simulation_id, initial_limit=window)
    recent = delta["actions"]
    total_actions = delta["total"]

    last_action_at = _parse_timestamp(recent[-1].timestamp) if recent else None
    seconds_since_last_action = _seconds_since(last_action_at)

    current_round = int(getattr(run_state, "current_round", 0) or 0)
    total_rounds = int(getattr(run_state, "total_rounds", 0) or 0)
    progress_percent = round(current_round / total_rounds * 100, 1) if total_rounds else 0.0

    rate = _actions_per_minute(recent)

    activity = {
        "actions_total": total_actions,
        "actions_in_window": len(recent),
        "actions_per_minute": rate,
        "seconds_since_last_action": (
            round(seconds_since_last_action) if seconds_since_last_action is not None else None
        ),
        "by_platform": dict(Counter(action.platform for action in recent)),
        "by_action_type": dict(Counter(action.action_type for action in recent).most_common(8)),
        "failures_in_window": sum(1 for action in recent if not action.success),
        "distinct_agents_in_window": len({action.agent_id for action in recent}),
    }

    alerts = _detect_alerts(run_state, recent, seconds_since_last_action)

    return {
        "simulation_id": simulation_id,
        "runner_status": getattr(run_state, "runner_status", "idle"),
        "progress": {
            "current_round": current_round,
            "total_rounds": total_rounds,
            "progress_percent": progress_percent,
            "simulated_hours": int(getattr(run_state, "simulated_hours", 0) or 0),
            "total_simulation_hours": int(getattr(run_state, "total_simulation_hours", 0) or 0),
            "twitter_running": bool(getattr(run_state, "twitter_running", False)),
            "reddit_running": bool(getattr(run_state, "reddit_running", False)),
        },
        "activity": activity,
        "alerts": alerts,
        "headline": _build_headline(run_state, activity, alerts, progress_percent),
    }


def _build_headline(
    run_state: Any,
    activity: Dict[str, Any],
    alerts: List[Dict[str, Any]],
    progress_percent: float,
) -> str:
    """Uma frase sobre o estado atual, sem chamar o modelo."""
    if alerts:
        return alerts[0]["message"]

    status = getattr(run_state, "runner_status", "idle")

    if status != "running":
        return (
            f"Simulação {status} com {activity['actions_total']} ações registradas."
        )

    rate = activity.get("actions_per_minute")
    rate_text = f", {rate} ações/min" if rate else ""
    dominant = activity.get("by_action_type") or {}
    dominant_text = ""
    if dominant:
        top_type = next(iter(dominant))
        dominant_text = f". Predomina {top_type}"

    current_round = getattr(run_state, "current_round", 0)

    return (
        f"Rodada {current_round} ({progress_percent}%){rate_text}, "
        f"{activity['distinct_agents_in_window']} agentes ativos na janela"
        f"{dominant_text}."
    )


def _format_pulse_for_prompt(pulse: Dict[str, Any]) -> str:
    """Compacta o pulso em texto para caber no prompt sem despejar JSON cru."""
    progress = pulse.get("progress", {})
    activity = pulse.get("activity", {})

    lines = [
        f"Status do executor: {pulse.get('runner_status')}",
        f"Rodada: {progress.get('current_round')} de {progress.get('total_rounds')} "
        f"({progress.get('progress_percent')}%)",
        f"Horas simuladas: {progress.get('simulated_hours')} de {progress.get('total_simulation_hours')}",
        f"Acoes totais: {activity.get('actions_total')}",
        f"Ritmo: {activity.get('actions_per_minute')} acoes por minuto",
        f"Ultima acao ha: {activity.get('seconds_since_last_action')} segundos",
        f"Agentes distintos na janela: {activity.get('distinct_agents_in_window')}",
        f"Falhas na janela: {activity.get('failures_in_window')}",
        f"Distribuicao por plataforma: {activity.get('by_platform')}",
        f"Distribuicao por tipo de acao: {activity.get('by_action_type')}",
    ]

    alerts = pulse.get("alerts") or []
    if alerts:
        lines.append("Alertas ativos:")
        lines.extend(f"  - [{alert['severity']}] {alert['message']}" for alert in alerts)
    else:
        lines.append("Alertas ativos: nenhum")

    return "\n".join(lines)


def _format_sample_actions(actions: List[AgentAction], limit: int = 15) -> str:
    """Amostra do conteudo real, para a resposta falar do que os agentes fizeram."""
    if not actions:
        return "(nenhuma acao registrada ainda)"

    lines = []
    for action in actions[-limit:]:
        content = ""
        if isinstance(action.action_args, dict):
            content = str(
                action.action_args.get("content")
                or action.action_args.get("text")
                or ""
            )[:180]
        status = "" if action.success else " [FALHOU]"
        lines.append(
            f"- r{action.round_num} {action.platform} {action.agent_name} "
            f"{action.action_type}{status}: {content}"
        )
    return "\n".join(lines)


COPILOT_SYSTEM_PROMPT = """Voce e o copiloto operacional de uma simulacao social multiagente da INTEIA.

O operador acompanha a execucao em tempo real e precisa de leitura direta do que
esta acontecendo agora. Responda com base exclusivamente no estado fornecido.

Regras:
- Comece pela resposta a pergunta. Sem preambulo.
- Use os numeros do estado. Nao invente metrica que nao foi fornecida.
- Se o estado nao contem o que foi perguntado, diga o que falta observar.
- Quando houver alerta ativo, diga o que ele significa para o resultado da
  simulacao e qual acao operacional cabe (seguir, parar, reiniciar, ajustar).
- Portugues do Brasil, tom tecnico e direto. Nada de ressalva generica.

Demanda que originou a simulacao:
{simulation_requirement}

Estado atual:
{pulse_text}

Amostra das acoes mais recentes:
{sample_actions}
"""


def answer_operator_question(
    simulation_id: str,
    question: str,
    simulation_requirement: str = "",
    chat_history: Optional[List[Dict[str, str]]] = None,
    llm_client: Any = None,
) -> Dict[str, Any]:
    """
    Responde uma pergunta do operador ancorada no estado vivo da simulacao.

    Args:
        simulation_id: ID da simulacao
        question: pergunta do operador
        simulation_requirement: demanda que originou a simulacao
        chat_history: turnos anteriores ({"role", "content"})
        llm_client: cliente injetavel (testes)

    Returns:
        {"response": str, "pulse": {...}}
    """
    pulse = build_pulse(simulation_id)
    delta = SimulationRunner.get_actions_delta(simulation_id, initial_limit=RECENT_WINDOW)

    system_prompt = COPILOT_SYSTEM_PROMPT.format(
        simulation_requirement=simulation_requirement or "(nao informada)",
        pulse_text=_format_pulse_for_prompt(pulse),
        sample_actions=_format_sample_actions(delta["actions"]),
    )

    messages = [{"role": "system", "content": system_prompt}]
    for turn in (chat_history or [])[-6:]:
        if turn.get("role") in ("user", "assistant") and turn.get("content"):
            messages.append({"role": turn["role"], "content": turn["content"]})
    messages.append({"role": "user", "content": question})

    if llm_client is None:
        from ..utils.llm_client import LLMClient
        llm_client = LLMClient()

    response = llm_client.chat(messages=messages, temperature=0.3, max_tokens=1200)

    return {
        "response": (response or "").strip(),
        "pulse": pulse,
    }
