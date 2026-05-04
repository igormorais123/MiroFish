"""Plano deterministico para o pulso social inicial da simulacao OASIS."""
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional, Sequence


DEFAULT_BOOTSTRAP_MAX_ACTIONS = 12

DEFAULT_ACTION_MIX = {
    "twitter": ["LIKE_POST", "QUOTE_POST", "REPOST"],
    "reddit": ["CREATE_COMMENT", "LIKE_POST", "DISLIKE_POST", "CREATE_COMMENT"],
}

ALLOWED_ACTIONS = {
    "twitter": {"LIKE_POST", "QUOTE_POST", "REPOST"},
    "reddit": {"CREATE_COMMENT", "LIKE_POST", "DISLIKE_POST"},
}

BOOTSTRAP_COMMENTS = [
    "Antes de concluir, vale separar o fato observado da inferencia da simulacao.",
    "O impacto depende de quem amplifica, rejeita ou desloca o tema nas proximas rodadas.",
    "Sem dados adicionais, isso deve ser tratado como sinal de risco, nao como conclusao fechada.",
    "A leitura precisa comparar esse sinal com alternativas e evidencias externas.",
]


def is_social_bootstrap_enabled(config: Dict[str, Any]) -> bool:
    """Retorna se o pulso social inicial esta habilitado."""
    dynamics = _social_dynamics(config)
    return dynamics.get("bootstrap_enabled", True) is not False


def build_social_bootstrap_plan(
    config: Dict[str, Any],
    platform: str,
    seed_posts: Sequence[Dict[str, Any]],
    *,
    agent_ids: Optional[Iterable[int]] = None,
) -> List[Dict[str, Any]]:
    """
    Planeja acoes sociais iniciais contra posts ja publicados.

    O plano e deterministico para ser auditavel: um agente executa no maximo
    uma acao no pulso, sempre contra post de outro agente quando houver.
    """
    platform = (platform or "").lower()
    posts = _normalise_seed_posts(seed_posts)
    candidates = list(agent_ids) if agent_ids is not None else _agent_ids_from_config(config)
    candidates = [agent_id for agent_id in candidates if isinstance(agent_id, int)]

    target_count = get_social_bootstrap_target(
        config,
        platform,
        seed_post_count=len(posts),
        candidate_count=len(candidates),
    )
    if not posts or not candidates or target_count <= 0:
        return []

    action_mix = _action_mix(config, platform)
    if not action_mix:
        return []

    plan: List[Dict[str, Any]] = []
    for idx, agent_id in enumerate(candidates):
        if len(plan) >= target_count:
            break

        target_post = _pick_target_post(posts, agent_id, idx)
        if not target_post:
            continue

        action_type = action_mix[idx % len(action_mix)]
        action_args = _action_args_for(action_type, target_post["post_id"], idx)
        if not action_args:
            continue

        plan.append({
            "agent_id": agent_id,
            "action_type": action_type,
            "action_args": action_args,
            "target_post_id": target_post["post_id"],
            "target_agent_id": target_post.get("agent_id"),
        })

    return plan


def get_social_bootstrap_target(
    config: Dict[str, Any],
    platform: str,
    *,
    seed_post_count: int,
    candidate_count: int,
) -> int:
    """Calcula quantas acoes de pulso social devem ser planejadas."""
    if not is_social_bootstrap_enabled(config):
        return 0
    if seed_post_count <= 0 or candidate_count <= 0:
        return 0

    dynamics = _social_dynamics(config)
    platform = (platform or "").lower()
    configured = _coerce_non_negative_int(
        dynamics.get(f"{platform}_bootstrap_actions", dynamics.get("bootstrap_actions"))
    )
    max_actions = _coerce_non_negative_int(
        dynamics.get(f"{platform}_bootstrap_max_actions", dynamics.get("bootstrap_max_actions"))
    )
    if max_actions is None:
        max_actions = DEFAULT_BOOTSTRAP_MAX_ACTIONS

    if configured is not None:
        return min(configured, max_actions, candidate_count)

    default_target = max(3, seed_post_count * 2)
    return min(default_target, max_actions, candidate_count)


def _social_dynamics(config: Dict[str, Any]) -> Dict[str, Any]:
    dynamics = config.get("social_dynamics") if isinstance(config, dict) else {}
    return dynamics if isinstance(dynamics, dict) else {}


def _agent_ids_from_config(config: Dict[str, Any]) -> List[int]:
    candidates = []
    for item in config.get("agent_configs", []) or []:
        agent_id = _coerce_int(item.get("agent_id"))
        if agent_id is None:
            continue
        influence = _coerce_float(item.get("influence_weight"), 1.0)
        activity = _coerce_float(item.get("activity_level"), 0.5)
        candidates.append((-influence, -activity, agent_id))

    candidates.sort()
    return [agent_id for _, _, agent_id in candidates]


def _normalise_seed_posts(seed_posts: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    posts: List[Dict[str, Any]] = []
    for item in seed_posts or []:
        post_id = _coerce_int(item.get("post_id") or item.get("new_post_id"))
        if post_id is None:
            continue
        posts.append({
            "post_id": post_id,
            "agent_id": _coerce_int(item.get("agent_id")),
            "content": item.get("content") or "",
        })
    return posts


def _action_mix(config: Dict[str, Any], platform: str) -> List[str]:
    default_mix = DEFAULT_ACTION_MIX.get(platform, [])
    allowed = ALLOWED_ACTIONS.get(platform, set())
    dynamics = _social_dynamics(config)
    raw_mix = dynamics.get(f"{platform}_bootstrap_action_mix", dynamics.get("bootstrap_action_mix"))

    if isinstance(raw_mix, str):
        raw_values = [part.strip() for part in raw_mix.split(",")]
    elif isinstance(raw_mix, list):
        raw_values = raw_mix
    else:
        raw_values = default_mix

    mix = []
    for value in raw_values:
        action = str(value or "").strip().upper()
        if action in allowed:
            mix.append(action)
    return mix or list(default_mix)


def _pick_target_post(
    posts: Sequence[Dict[str, Any]],
    agent_id: int,
    offset: int,
) -> Optional[Dict[str, Any]]:
    if not posts:
        return None

    rotated = list(posts[offset % len(posts):]) + list(posts[:offset % len(posts)])
    for post in rotated:
        if post.get("agent_id") != agent_id:
            return post
    return None


def _action_args_for(action_type: str, post_id: int, idx: int) -> Dict[str, Any]:
    if action_type in {"LIKE_POST", "DISLIKE_POST", "REPOST"}:
        return {"post_id": post_id}
    if action_type == "QUOTE_POST":
        return {"post_id": post_id, "quote_content": BOOTSTRAP_COMMENTS[idx % len(BOOTSTRAP_COMMENTS)]}
    if action_type == "CREATE_COMMENT":
        return {"post_id": post_id, "content": BOOTSTRAP_COMMENTS[idx % len(BOOTSTRAP_COMMENTS)]}
    return {}


def _coerce_int(value: Any) -> Optional[int]:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _coerce_non_negative_int(value: Any) -> Optional[int]:
    parsed = _coerce_int(value)
    if parsed is None:
        return None
    return max(0, parsed)


def _coerce_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default
