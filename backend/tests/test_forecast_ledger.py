from __future__ import annotations

import pytest

from app.services.forecast_ledger import ForecastLedger, stable_forecast_id


def test_forecast_id_is_stable_for_essential_content():
    first = stable_forecast_id(
        enunciado="A cooperacao aumenta quando a cadencia semanal fica visivel.",
        janela="30 dias",
        base={"simulacao": "sim-1"},
        sinais=["respostas no prazo", "menos retrabalho"],
        grau_confianca_operacional="medio",
    )
    second = stable_forecast_id(
        enunciado="A cooperacao aumenta quando a cadencia semanal fica visivel.",
        janela="30 dias",
        base={"simulacao": "sim-1"},
        sinais=["respostas no prazo", "menos retrabalho"],
        grau_confianca_operacional="medio",
    )

    assert first == second
    assert first.startswith("prev_")


def test_forecast_ledger_deduplicates_equal_forecasts():
    ledger = ForecastLedger()
    original = ledger.registrar_previsao(
        enunciado="O gargalo migra para validacao se nao houver dono claro.",
        janela="15 dias",
        base={"report_id": "rep-1"},
        sinais=["fila de aprovacao"],
        grau_confianca_operacional=0.72,
        criado_em="2026-05-05T10:00:00+00:00",
    )
    duplicate = ledger.registrar_previsao(
        enunciado="O gargalo migra para validacao se nao houver dono claro.",
        janela="15 dias",
        base={"report_id": "rep-1"},
        sinais=["fila de aprovacao"],
        grau_confianca_operacional=0.72,
        status="confirmada",
        criado_em="2026-05-05T11:00:00+00:00",
    )

    assert duplicate == original
    assert len(ledger.listar_previsoes()) == 1


def test_forecast_ledger_exports_portuguese_summary_by_status():
    ledger = ForecastLedger()
    for status in ["congelada", "em_observacao", "confirmada", "revertida"]:
        ledger.registrar_previsao(
            enunciado=f"Previsao {status}",
            janela="7 dias",
            base={"fonte": status},
            sinais=[status],
            grau_confianca_operacional="baixo",
            status=status,
            criado_em="2026-05-05T10:00:00+00:00",
        )

    resumo = ledger.exportar_resumo()

    assert "Livro de previsoes: 4 previsoes registradas." in resumo
    assert "Congeladas: 1." in resumo
    assert "Em observacao: 1." in resumo
    assert "Confirmadas: 1." in resumo
    assert "Revertidas: 1." in resumo


def test_forecast_ledger_rejects_invalid_status():
    ledger = ForecastLedger()

    with pytest.raises(ValueError):
        ledger.registrar_previsao(
            enunciado="Previsao invalida",
            janela="7 dias",
            base={},
            sinais=[],
            grau_confianca_operacional="baixo",
            status="rascunho",
        )

