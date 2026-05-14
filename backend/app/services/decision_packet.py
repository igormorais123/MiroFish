"""Deterministic predictive decision packet for report generation."""

from __future__ import annotations

from typing import Any, Mapping


def build_decision_packet(
    *,
    simulation_id: str,
    simulation_requirement: str,
    quality_gate: Mapping[str, Any] | None,
    outline_summary: str | None = None,
) -> dict[str, Any]:
    """Builds the structured basis used for assertive predictive claims.

    The packet keeps the report authoritative without letting the LLM invent
    probabilities. Percentages are deterministic functions of audited system
    metrics and are also exposed as numeric metrics for the evidence audit.
    """
    gate = quality_gate if isinstance(quality_gate, Mapping) else {}
    metrics = gate.get("metrics") if isinstance(gate.get("metrics"), Mapping) else {}
    diversity = metrics.get("diversity") if isinstance(metrics.get("diversity"), Mapping) else {}
    oasis_trace = diversity.get("oasis_trace") if isinstance(diversity.get("oasis_trace"), Mapping) else {}

    min_actions = _positive_int(metrics.get("min_actions"), default=10)
    total_actions = _positive_int(
        metrics.get("total_actions_count") or diversity.get("total_actions"),
        default=0,
    )
    generated_texts = _positive_int(diversity.get("generated_texts_count"), default=0)
    profiles_count = _positive_int(metrics.get("profiles_count"), default=0)
    entity_type_coverage = _positive_int(diversity.get("entity_type_coverage"), default=0)
    total_rounds = _positive_int(metrics.get("total_rounds"), default=0)
    current_round = _positive_int(metrics.get("current_round"), default=0)
    graph_nodes = _positive_int(metrics.get("graph_nodes_count"), default=0)
    graph_edges = _positive_int(metrics.get("graph_edges_count"), default=0)
    source_chars = _positive_int(metrics.get("source_text_characters"), default=0)

    action_scale = _cap(total_actions / max(min_actions * 3, 1))
    text_scale = _cap(generated_texts / max(min_actions * 2, 1))
    profile_scale = _cap(profiles_count / 12)
    role_scale = _cap(entity_type_coverage / 3)
    round_scale = _cap(current_round / total_rounds) if total_rounds else 0.55
    graph_scale = _cap((graph_nodes + graph_edges) / 20)
    source_scale = 1.0 if source_chars >= 500 else _cap(source_chars / 500)
    distinct_scale = _float_metric(diversity.get("distinct_2"), 0.0)
    agent_entropy = _float_metric(diversity.get("agent_activity_entropy_norm"), 0.0)
    behavior_entropy = _float_metric(diversity.get("action_type_entropy_norm"), 0.0)
    behavioral_entropy = _float_metric(oasis_trace.get("behavioral_entropy_norm"), behavior_entropy)

    emergent_interactions = _positive_int(
        oasis_trace.get("emergent_interactive_actions_estimate")
        if "emergent_interactive_actions_estimate" in oasis_trace
        else oasis_trace.get("interactive_actions_total"),
        default=0,
    )
    dynamic_posts = _positive_int(oasis_trace.get("dynamic_create_posts_estimate"), default=0)
    social_scale = _cap((emergent_interactions + dynamic_posts) / max(min_actions, 1))

    components = {
        "execution": round((round_scale + action_scale) / 2, 4),
        "semantic_density": round((distinct_scale + text_scale) / 2, 4),
        "agent_diversity": round((agent_entropy + profile_scale + role_scale) / 3, 4),
        "behavioral_signal": round((behavior_entropy + behavioral_entropy + social_scale) / 3, 4),
        "knowledge_backing": round((graph_scale + source_scale) / 2, 4),
    }
    weights = {
        "execution": 0.22,
        "semantic_density": 0.20,
        "agent_diversity": 0.20,
        "behavioral_signal": 0.23,
        "knowledge_backing": 0.15,
    }
    raw_conviction = sum(components[key] * weights[key] for key in weights)
    if gate.get("passes_gate") is not True:
        raw_conviction = min(raw_conviction, 0.55)
    conviction = round(_clamp(raw_conviction, 0.35, 0.92), 4)

    base_probability_percent = int(round(46 + 24 * conviction))
    contrary_probability_percent = int(round(16 + 18 * (1 - conviction)))
    optimistic_probability_percent = 100 - base_probability_percent - contrary_probability_percent
    if optimistic_probability_percent < 12:
        delta = 12 - optimistic_probability_percent
        optimistic_probability_percent = 12
        base_probability_percent = max(45, base_probability_percent - delta)

    reversal_risk_percent = int(round(_clamp(contrary_probability_percent + (1 - social_scale) * 8, 12, 44)))
    execution_risk_percent = int(round(_clamp((1 - components["execution"]) * 38 + 8, 8, 42)))
    evidence_risk_percent = int(round(_clamp((1 - components["knowledge_backing"]) * 34 + 6, 6, 38)))

    structured_metrics = {
        "conviction_operational": conviction,
        "conviction_operational_percent": int(round(conviction * 100)),
        "scenario_base_probability_percent": base_probability_percent,
        "scenario_optimistic_probability_percent": optimistic_probability_percent,
        "scenario_contrary_probability_percent": contrary_probability_percent,
        "reversal_risk_probability_percent": reversal_risk_percent,
        "execution_risk_probability_percent": execution_risk_percent,
        "evidence_risk_probability_percent": evidence_risk_percent,
        "emergent_interactive_actions_estimate": emergent_interactions,
        "dynamic_create_posts_estimate": dynamic_posts,
        "total_actions_count": total_actions,
        "generated_texts_count": generated_texts,
    }

    thesis = (outline_summary or simulation_requirement or "tese vencedora da simulacao").strip()
    return {
        "schema": "mirofish.decision_packet.v1",
        "simulation_id": simulation_id,
        "thesis": thesis[:360],
        "conviction_operational": conviction,
        "conviction_operational_percent": structured_metrics["conviction_operational_percent"],
        "reference_class": "simulacao social INTEIA com eleitores sinteticos calibrados e auditoria de evidencias",
        "probability_basis": {
            "method": "weighted_operational_conviction_v1",
            "components": components,
            "weights": weights,
            "structured_metrics": structured_metrics,
        },
        "scenarios": {
            "base": {
                "label": "Base",
                "probability": round(base_probability_percent / 100, 4),
                "probability_percent": base_probability_percent,
                "role": "tese vencedora",
            },
            "optimistic": {
                "label": "Otimista",
                "probability": round(optimistic_probability_percent / 100, 4),
                "probability_percent": optimistic_probability_percent,
                "role": "melhor janela de acao",
            },
            "contrary": {
                "label": "Contrario",
                "probability": round(contrary_probability_percent / 100, 4),
                "probability_percent": contrary_probability_percent,
                "role": "tese adversaria mais forte",
            },
        },
        "risks": {
            "reversal": {
                "label": "Reversao da tese vencedora",
                "probability": round(reversal_risk_percent / 100, 4),
                "probability_percent": reversal_risk_percent,
            },
            "execution": {
                "label": "Falha de execucao operacional",
                "probability": round(execution_risk_percent / 100, 4),
                "probability_percent": execution_risk_percent,
            },
            "evidence": {
                "label": "Lacuna de evidencia decisiva",
                "probability": round(evidence_risk_percent / 100, 4),
                "probability_percent": evidence_risk_percent,
            },
        },
        "indicators": {
            "total_actions": total_actions,
            "generated_texts": generated_texts,
            "profiles": profiles_count,
            "entity_type_coverage": entity_type_coverage,
            "current_round": current_round,
            "total_rounds": total_rounds,
            "emergent_interactive_actions": emergent_interactions,
            "dynamic_create_posts": dynamic_posts,
            "distinct_2": round(distinct_scale, 4),
            "agent_activity_entropy_norm": round(agent_entropy, 4),
            "action_type_entropy_norm": round(behavior_entropy, 4),
            "graph_nodes": graph_nodes,
            "graph_edges": graph_edges,
            "source_text_characters": source_chars,
        },
        "structured_metrics": structured_metrics,
    }


def decision_packet_prompt_block(packet: Mapping[str, Any] | None) -> str:
    """Formats the packet for Helena without exposing internal noise."""
    if not isinstance(packet, Mapping):
        return "Pacote de decisao preditiva indisponivel."
    scenarios = packet.get("scenarios") if isinstance(packet.get("scenarios"), Mapping) else {}
    risks = packet.get("risks") if isinstance(packet.get("risks"), Mapping) else {}
    indicators = packet.get("indicators") if isinstance(packet.get("indicators"), Mapping) else {}

    def pct(path: tuple[str, str], default: int = 0) -> int:
        group = scenarios.get(path[0]) if path[0] in scenarios else risks.get(path[0])
        if not isinstance(group, Mapping):
            return default
        return _positive_int(group.get(path[1]), default=default)

    lines = [
        f"Tese operacional: {packet.get('thesis', '')}",
        f"Conviccao operacional INTEIA: {packet.get('conviction_operational_percent', 0)}%",
        "Cenarios oficiais para usar no relatorio:",
        f"- Base: {pct(('base', 'probability_percent'))}%",
        f"- Otimista: {pct(('optimistic', 'probability_percent'))}%",
        f"- Contrario: {pct(('contrary', 'probability_percent'))}%",
        "Riscos oficiais para quantificar:",
        f"- Reversao da tese vencedora: {pct(('reversal', 'probability_percent'))}%",
        f"- Falha de execucao operacional: {pct(('execution', 'probability_percent'))}%",
        f"- Lacuna de evidencia decisiva: {pct(('evidence', 'probability_percent'))}%",
        "Indicadores de lastro:",
        (
            f"- Acoes: {indicators.get('total_actions', 0)}; textos: {indicators.get('generated_texts', 0)}; "
            f"perfis: {indicators.get('profiles', 0)}; papeis: {indicators.get('entity_type_coverage', 0)}"
        ),
        (
            f"- Acoes sociais emergentes: {indicators.get('emergent_interactive_actions', 0)}; "
            f"novas postagens emergentes: {indicators.get('dynamic_create_posts', 0)}"
        ),
    ]
    return "\n".join(lines)


def _positive_int(value: Any, *, default: int) -> int:
    try:
        return max(0, int(float(value)))
    except (TypeError, ValueError):
        return default


def _float_metric(value: Any, default: float) -> float:
    try:
        return _cap(float(value))
    except (TypeError, ValueError):
        return default


def _cap(value: float) -> float:
    return _clamp(value, 0.0, 1.0)


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))
