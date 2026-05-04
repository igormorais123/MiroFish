"""Testes da politica de entrega cliente vs diagnostico."""
from __future__ import annotations

from app.services.delivery_governance import normalize_delivery_mode, resolve_delivery_governance


def test_delivery_governance_cliente_e_estrita_por_padrao():
    policy = resolve_delivery_governance()

    assert policy.mode == "client"
    assert policy.publishable is True
    assert policy.min_actions >= 10
    assert policy.require_completed_simulation is True
    assert policy.require_source_text is True


def test_delivery_governance_demo_nunca_e_publicavel():
    policy = resolve_delivery_governance({
        "delivery_governance": {
            "mode": "smoke",
            "report_min_actions": 1,
            "require_completed_simulation": False,
            "require_source_text": False,
        }
    })

    assert policy.mode == "demo"
    assert policy.publishable is False
    assert policy.min_actions == 1
    assert policy.require_completed_simulation is False
    assert policy.require_source_text is False


def test_delivery_mode_desconhecido_volta_para_cliente():
    assert normalize_delivery_mode("modo-fraco-inventado") == "client"
