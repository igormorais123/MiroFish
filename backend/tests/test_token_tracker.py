"""Testes do TokenTracker e TokenUsage (Phase 10)."""
from __future__ import annotations

import time
import pytest

from app.utils.token_tracker import (
    DEFAULT_USD_BRL_EXCHANGE_RATE,
    INTEIA_MARKUP_MULTIPLIER,
    PRICE_INPUT_USD_PER_1M_TOKENS,
    PRICE_INPUT_PER_TOKEN,
    PRICE_OUTPUT_USD_PER_1M_TOKENS,
    PRICE_OUTPUT_PER_TOKEN,
    PRICEBOOK_NAME,
    TokenTracker,
    TokenUsage,
)


@pytest.fixture(autouse=True)
def reset_singleton():
    """Reset singleton state entre testes — TokenTracker e singleton global."""
    t = TokenTracker()
    t.reset_global()
    t._sessions.clear()
    t._phases.clear()
    yield


def test_token_usage_calcula_total_corretamente():
    u = TokenUsage(prompt_tokens=1000, completion_tokens=500)
    assert u.total_tokens == 1500


def test_token_usage_contrato_pricebook_literal():
    assert PRICEBOOK_NAME == "gpt-5.5-pro-rapido-referencia"
    assert DEFAULT_USD_BRL_EXCHANGE_RATE == pytest.approx(5.80)
    assert INTEIA_MARKUP_MULTIPLIER == pytest.approx(5.0)
    assert PRICE_INPUT_USD_PER_1M_TOKENS == pytest.approx(5.0)
    assert PRICE_OUTPUT_USD_PER_1M_TOKENS == pytest.approx(20.0)


def test_token_usage_custo_usd_calculado():
    u = TokenUsage(prompt_tokens=1_000_000, completion_tokens=500_000)
    expected = 1_000_000 * PRICE_INPUT_PER_TOKEN + 500_000 * PRICE_OUTPUT_PER_TOKEN
    assert u.cost_usd == pytest.approx(expected)
    assert expected == pytest.approx(15.0)


def test_token_usage_custo_brl_aplica_cambio():
    u = TokenUsage(prompt_tokens=1_000_000, completion_tokens=0)
    assert u.cost_brl == pytest.approx(u.cost_usd * DEFAULT_USD_BRL_EXCHANGE_RATE)


def test_token_usage_to_dict_estrutura():
    u = TokenUsage(prompt_tokens=100, completion_tokens=50, total_requests=3)
    d = u.to_dict()
    assert d["prompt_tokens"] == 100
    assert d["completion_tokens"] == 50
    assert d["total_tokens"] == 150
    assert d["total_requests"] == 3
    assert "cost_usd" in d
    assert "cost_brl" in d
    assert d["api_reference_usd"] == d["cost_usd"]
    assert d["api_reference_brl"] == d["cost_brl"]
    assert d["inteia_value_usd"] == pytest.approx(d["api_reference_usd"] * INTEIA_MARKUP_MULTIPLIER)
    assert d["inteia_value_brl"] == pytest.approx(d["api_reference_brl"] * INTEIA_MARKUP_MULTIPLIER)
    assert d["markup_multiplier"] == INTEIA_MARKUP_MULTIPLIER
    assert d["pricebook"] == PRICEBOOK_NAME
    assert d["rotulo_valor"] == "Valor operacional INTEIA"
    assert d["rotulo_custo"] == "Custo tecnico de referencia da API"
    assert "elapsed_seconds" in d
    assert "cost_per_minute_usd" in d


def test_token_usage_valor_inteia_aplica_multiplicador_5x():
    u = TokenUsage(prompt_tokens=1_000_000, completion_tokens=1_000_000)
    assert u.api_reference_usd == pytest.approx(25.0)
    assert u.inteia_value_usd == pytest.approx(125.0)
    assert u.inteia_value_brl == pytest.approx(125.0 * DEFAULT_USD_BRL_EXCHANGE_RATE)


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
    assert "phases" in a


def test_tracker_get_session_inexistente_retorna_zerado():
    t = TokenTracker()
    s = t.get_session("nao_existe")
    assert s["prompt_tokens"] == 0
    assert s["completion_tokens"] == 0
    assert s["total_requests"] == 0
    assert s["phases"] == {}


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


def test_tracker_reset_all_zera_global_sessions_e_fases():
    t = TokenTracker()
    t.start_phase("sx", "preparo", "Preparacao da missao")
    t.track(100, 50, session_id="sx", phase_id="preparo")
    t.reset_all()
    assert t.get_global()["prompt_tokens"] == 0
    assert t.get_all_sessions() == {}
    assert t.get_session("sx")["phases"] == {}


def test_tracker_get_all_sessions():
    t = TokenTracker()
    t.track(100, 50, session_id="a")
    t.track(200, 100, session_id="b")
    all_s = t.get_all_sessions()
    assert set(all_s.keys()) == {"a", "b"}
    assert all_s["a"]["prompt_tokens"] == 100
    assert all_s["b"]["prompt_tokens"] == 200


def test_tracker_fases_da_missao_acumulam_e_finalizam():
    t = TokenTracker()
    t.start_phase("missao_1", "preparo", "Preparacao da missao")
    t.track(1_000_000, 0, session_id="missao_1", phase_id="preparo")
    time.sleep(0.01)
    t.finish_phase("missao_1", "preparo")

    session = t.get_session("missao_1")
    phase = session["phases"]["preparo"]

    assert session["prompt_tokens"] == 1_000_000
    assert phase["phase_id"] == "preparo"
    assert phase["label"] == "Preparacao da missao"
    assert phase["rotulo"] == "Preparacao da missao"
    assert phase["prompt_tokens"] == 1_000_000
    assert phase["api_reference_usd"] == pytest.approx(5.0)
    assert phase["inteia_value_usd"] == pytest.approx(25.0)
    assert phase["markup_multiplier"] == 5.0
    assert phase["pricebook"] == PRICEBOOK_NAME
    assert phase["estado"] == "concluida"


def test_tracker_start_phase_idempotente_preserva_consumo():
    t = TokenTracker()
    t.start_phase("missao_1", "preparo", "Preparacao da missao")
    t.track(100, 50, session_id="missao_1", phase_id="preparo")

    phase_before = t.get_session("missao_1")["phases"]["preparo"]
    t.start_phase("missao_1", "preparo", "Preparacao revisada")
    phase_after = t.get_session("missao_1")["phases"]["preparo"]

    assert phase_after["label"] == "Preparacao revisada"
    assert phase_after["prompt_tokens"] == phase_before["prompt_tokens"] == 100
    assert phase_after["completion_tokens"] == phase_before["completion_tokens"] == 50
    assert phase_after["total_requests"] == phase_before["total_requests"] == 1


def test_tracker_track_com_phase_id_sem_start_cria_rotulo_padrao():
    t = TokenTracker()
    t.track(10, 20, session_id="missao_2", phase_id="analise")
    phase = t.get_session("missao_2")["phases"]["analise"]
    assert phase["label"] == "Fase analise"
    assert phase["completion_tokens"] == 20
