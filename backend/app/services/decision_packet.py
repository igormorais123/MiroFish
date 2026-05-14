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
    convergence = _build_convergence_assessment(
        components=components,
        conviction=conviction,
        total_actions=total_actions,
        min_actions=min_actions,
        current_round=current_round,
        total_rounds=total_rounds,
    )
    red_team = _build_red_team_assessment(
        components=components,
        social_scale=social_scale,
        source_scale=source_scale,
        contrary_probability_percent=contrary_probability_percent,
        reversal_risk_percent=reversal_risk_percent,
        evidence_risk_percent=evidence_risk_percent,
    )

    structured_metrics = {
        "conviction_operational": conviction,
        "conviction_operational_percent": int(round(conviction * 100)),
        "scenario_base_probability_percent": base_probability_percent,
        "scenario_optimistic_probability_percent": optimistic_probability_percent,
        "scenario_contrary_probability_percent": contrary_probability_percent,
        "reversal_risk_probability_percent": reversal_risk_percent,
        "execution_risk_probability_percent": execution_risk_percent,
        "evidence_risk_probability_percent": evidence_risk_percent,
        "convergence_score_percent": convergence["score_percent"],
        "red_team_pressure_percent": red_team["pressure_percent"],
        "emergent_interactive_actions_estimate": emergent_interactions,
        "dynamic_create_posts_estimate": dynamic_posts,
        "total_actions_count": total_actions,
        "generated_texts_count": generated_texts,
    }

    thesis = (outline_summary or simulation_requirement or "tese vencedora da simulacao").strip()
    return {
        "schema": "mirofish.decision_packet.v2",
        "simulation_id": simulation_id,
        "thesis": thesis[:360],
        "conviction_operational": conviction,
        "conviction_operational_percent": structured_metrics["conviction_operational_percent"],
        "reference_class": "simulacao social INTEIA com eleitores sinteticos calibrados e auditoria de evidencias",
        "method_lock": {
            "status": "locked",
            "rules": [
                "usar somente percentuais oficiais do decision_packet",
                "apresentar tese adversaria mais forte",
                "declarar gatilhos de reversao",
                "diferenciar sinal emergente de bootstrap",
                "registrar previsao monitoravel no forecast ledger",
            ],
        },
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
        "convergence": convergence,
        "red_team": red_team,
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
    convergence = packet.get("convergence") if isinstance(packet.get("convergence"), Mapping) else {}
    red_team = packet.get("red_team") if isinstance(packet.get("red_team"), Mapping) else {}

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
        "Convergencia metodologica:",
        (
            f"- Score: {convergence.get('score_percent', 0)}%; "
            f"estado: {convergence.get('status', 'indefinido')}; "
            f"rodadas de reforco recomendadas: {convergence.get('recommended_next_runs', 0)}"
        ),
        "Red team obrigatorio:",
        f"- Tese adversaria: {red_team.get('opposing_thesis', '')}",
        f"- Vetor de ataque: {red_team.get('attack_vector', '')}",
        f"- Gatilhos de reversao: {'; '.join(red_team.get('reversal_triggers', []) or [])}",
    ]
    return "\n".join(lines)


def _build_convergence_assessment(
    *,
    components: Mapping[str, float],
    conviction: float,
    total_actions: int,
    min_actions: int,
    current_round: int,
    total_rounds: int,
) -> dict[str, Any]:
    component_values = [float(value) for value in components.values()]
    weakest = min(component_values) if component_values else 0.0
    spread = max(component_values) - weakest if component_values else 1.0
    balance = 1 - _cap(spread)
    volume = _cap(total_actions / max(min_actions * 4, 1))
    completion = _cap(current_round / total_rounds) if total_rounds else 0.55
    score = _clamp(conviction * 0.45 + weakest * 0.25 + balance * 0.15 + volume * 0.10 + completion * 0.05, 0.0, 1.0)
    if score >= 0.78:
        status = "forte"
        recommended_next_runs = 0
    elif score >= 0.62:
        status = "operacional"
        recommended_next_runs = 1
    else:
        status = "pressionada"
        recommended_next_runs = 2

    return {
        "score": round(score, 4),
        "score_percent": int(round(score * 100)),
        "status": status,
        "recommended_next_runs": recommended_next_runs,
        "weakest_component": _weakest_component(components),
        "component_spread": round(spread, 4),
    }


def _build_red_team_assessment(
    *,
    components: Mapping[str, float],
    social_scale: float,
    source_scale: float,
    contrary_probability_percent: int,
    reversal_risk_percent: int,
    evidence_risk_percent: int,
) -> dict[str, Any]:
    weakest = _weakest_component(components)
    pressure = int(round(_clamp((contrary_probability_percent + reversal_risk_percent + evidence_risk_percent) / 300, 0.0, 1.0) * 100))
    thesis_by_component = {
        "execution": "A tese adversaria dira que a execucao ainda nao acumulou rodadas e acoes suficientes para sustentar a linha dominante.",
        "semantic_density": "A tese adversaria dira que o discurso dos agentes ainda nao diferenciou mensagens o bastante para cravar a narrativa vencedora.",
        "agent_diversity": "A tese adversaria dira que a coalizao simulada ainda esta concentrada demais para representar conflito real.",
        "behavioral_signal": "A tese adversaria dira que a tracao social emergente ainda nao venceu o pulso induzido da simulacao.",
        "knowledge_backing": "A tese adversaria dira que o grafo e o material-base ainda nao bastam para blindar a recomendacao contra contestacao externa.",
    }
    attack_by_component = {
        "execution": "pressionar volume, rodadas e persistencia temporal",
        "semantic_density": "atacar repeticao semantica e baixa diferenca entre grupos",
        "agent_diversity": "atacar representatividade e heterogeneidade dos perfis",
        "behavioral_signal": "atacar ausencia de reacao social espontanea",
        "knowledge_backing": "atacar lastro documental e conexoes do grafo",
    }
    triggers = [
        "queda do score de convergencia abaixo de 62%",
        "cenario Contrario superar o Otimista na proxima rodada",
        "interacoes emergentes ficarem abaixo do pulso bootstrap",
    ]
    if social_scale < 0.5:
        triggers.append("baixo volume de comentario, repostagem ou nova publicacao emergente")
    if source_scale < 0.8:
        triggers.append("entrada de documento externo que contradiga a tese vencedora")

    return {
        "pressure_percent": pressure,
        "weakest_component": weakest,
        "opposing_thesis": thesis_by_component.get(weakest, thesis_by_component["behavioral_signal"]),
        "attack_vector": attack_by_component.get(weakest, attack_by_component["behavioral_signal"]),
        "reversal_triggers": triggers,
        "falsification_tests": [
            "rodar nova simulacao mantendo a tese vencedora e elevando opositores",
            "rodar nova simulacao invertendo o enquadramento inicial",
            "comparar se a tese base permanece dominante nos indicadores emergentes",
        ],
    }


def _weakest_component(components: Mapping[str, float]) -> str:
    if not components:
        return "behavioral_signal"
    return min(components.items(), key=lambda item: float(item[1]))[0]


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
