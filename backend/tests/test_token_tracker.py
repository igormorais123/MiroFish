"""Testes do TokenTracker e TokenUsage (Phase 10)."""
from __future__ import annotations

import time
import pytest

from app.utils.token_tracker import (
    PRICE_INPUT_PER_TOKEN,
    PRICE_OUTPUT_PER_TOKEN,
    TokenTracker,
    TokenUsage,
)


@pytest.fixture(autouse=True)
def reset_singleton():
    """Reset singleton state entre testes — TokenTracker e singleton global."""
    t = TokenTracker()
    t.reset_global()
    t._sessions.clear()
    yield


def test_token_usage_calcula_total_corretamente():
    u = TokenUsage(prompt_tokens=1000, completion_tokens=500)
    assert u.total_tokens == 1500


def test_token_usage_custo_usd_calculado():
    u = TokenUsage(prompt_tokens=1_000_000, completion_tokens=500_000)
    expected = 1_000_000 * PRICE_INPUT_PER_TOKEN + 500_000 * PRICE_OUTPUT_PER_TOKEN
    assert u.cost_usd == pytest.approx(expected)


def test_token_usage_custo_brl_aplica_cambio():
    u = TokenUsage(prompt_tokens=1_000_000, completion_tokens=0)
    assert u.cost_brl == pytest.approx(u.cost_usd * 5.80)


def test_token_usage_to_dict_estrutura():
    u = TokenUsage(prompt_tokens=100, completion_tokens=50, total_requests=3)
    d = u.to_dict()
    assert d["prompt_tokens"] == 100
    assert d["completion_tokens"] == 50
    assert d["total_tokens"] == 150
    assert d["total_requests"] == 3
    assert "cost_usd" in d
    assert "cost_brl" in d
    assert "elapsed_seconds" in d
    assert "cost_per_minute_usd" in d


def test_tracker_e_singleton():
    a = TokenTracker()
    b = TokenTracker()
    assert a is b


def test_tracker_track_acumula_global():
    t = TokenTracker()
    t.track(prompt_tokens=100, completion_tokens=50)
    t.track(prompt_tokens=200, completion_tokens=100)
    g = t.get_global()
    assert g["prompt_tokens"] == 300
    assert g["completion_tokens"] == 150
    assert g["total_requests"] == 2


def test_tracker_track_isola_sessions():
    t = TokenTracker()
    t.track(100, 50, session_id="sess_a")
    t.track(200, 100, session_id="sess_b")
    a = t.get_session("sess_a")
    b = t.get_session("sess_b")
    assert a["prompt_tokens"] == 100 and a["total_requests"] == 1
    assert b["prompt_tokens"] == 200 and b["total_requests"] == 1


def test_tracker_get_session_inexistente_retorna_zerado():
    t = TokenTracker()
    s = t.get_session("nao_existe")
    assert s["prompt_tokens"] == 0
    assert s["completion_tokens"] == 0
    assert s["total_requests"] == 0


def test_tracker_track_error_incrementa_global_e_session():
    t = TokenTracker()
    t.track(100, 50, session_id="sx")
    t.track_error(session_id="sx")
    t.track_error()
    assert t.get_global()["total_errors"] == 2
    assert t.get_session("sx")["total_errors"] == 1


def test_tracker_reset_zera_apenas_global():
    t = TokenTracker()
    t.track(100, 50, session_id="sx")
    t.reset_global()
    assert t.get_global()["prompt_tokens"] == 0
    # Sessao preservada
    assert t.get_session("sx")["prompt_tokens"] == 100


def test_tracker_get_all_sessions():
    t = TokenTracker()
    t.track(100, 50, session_id="a")
    t.track(200, 100, session_id="b")
    all_s = t.get_all_sessions()
    assert set(all_s.keys()) == {"a", "b"}
    assert all_s["a"]["prompt_tokens"] == 100
    assert all_s["b"]["prompt_tokens"] == 200
