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


def test_forecast_ledger_calculates_brier_and_log_loss_for_resolved_forecast():
    ledger = ForecastLedger()

    entry = ledger.registrar_previsao(
        enunciado="A entrega sera aceita sem retrabalho critico.",
        janela="14 dias",
        base={"report_id": "rep-1"},
        sinais=["bundle verificado"],
        grau_confianca_operacional="alto",
        probability=0.8,
        prior=0.6,
        base_rate=0.55,
        reference_class="relatorios verificaveis",
        indicators=["sem blocker", "hash ok"],
        outcome=True,
        status="confirmada",
        resolved_at="2026-05-20T10:00:00+00:00",
        resolution_source="aceite do cliente",
        criado_em="2026-05-05T10:00:00+00:00",
    )

    assert entry["probability"] == 0.8
    assert entry["prior"] == 0.6
    assert entry["base_rate"] == 0.55
    assert entry["reference_class"] == "relatorios verificaveis"
    assert entry["brier_score"] == 0.04
    assert entry["log_loss"] == pytest.approx(0.223144)


def test_forecast_ledger_round_trips_exported_entries_with_scores():
    ledger = ForecastLedger()
    ledger.registrar_previsao(
        enunciado="A entrega sera aceita sem retrabalho critico.",
        janela="14 dias",
        base={"report_id": "rep-1"},
        sinais=["bundle verificado"],
        grau_confianca_operacional="alto",
        probability=0.8,
        outcome=True,
        status="confirmada",
        criado_em="2026-05-05T10:00:00+00:00",
    )
    exported = ledger.listar_previsoes()

    restored = ForecastLedger(exported).listar_previsoes()

    assert restored == exported


def test_forecast_ledger_rejects_probability_outside_unit_interval():
    ledger = ForecastLedger()

    with pytest.raises(ValueError):
        ledger.registrar_previsao(
            enunciado="Previsao impossivel",
            janela="7 dias",
            base={},
            sinais=[],
            grau_confianca_operacional="baixo",
            probability=1.2,
        )


def test_forecast_ledger_exports_calibration_summary_and_chart_data():
    ledger = ForecastLedger()
    ledger.registrar_previsao(
        enunciado="Previsao confirmada",
        janela="7 dias",
        base={"fonte": "a"},
        sinais=["a"],
        grau_confianca_operacional="medio",
        status="confirmada",
        probability=0.75,
        outcome=True,
        criado_em="2026-05-05T10:00:00+00:00",
    )
    ledger.registrar_previsao(
        enunciado="Previsao revertida",
        janela="7 dias",
        base={"fonte": "b"},
        sinais=["b"],
        grau_confianca_operacional="medio",
        status="revertida",
        probability=0.8,
        outcome=False,
        criado_em="2026-05-05T10:00:00+00:00",
    )
    ledger.registrar_previsao(
        enunciado="Previsao aberta",
        janela="7 dias",
        base={"fonte": "c"},
        sinais=["c"],
        grau_confianca_operacional="baixo",
        status="em_observacao",
        criado_em="2026-05-05T10:00:00+00:00",
    )

    summary = ledger.exportar_calibracao()
    chart = ledger.exportar_grafico_deterministico()

    assert summary["schema"] == "mirofish.forecast_calibration.v1"
    assert summary["total"] == 3
    assert summary["resolved"] == 2
    assert summary["probabilistic"] == 2
    assert summary["mean_brier_score"] == pytest.approx((0.0625 + 0.64) / 2)
    assert chart["schema"] == "mirofish.forecast_chart_data.v1"
    assert chart["series"][0]["id"] == "status_counts"
    assert chart["series"][0]["points"] == sorted(chart["series"][0]["points"], key=lambda item: item["label"])

