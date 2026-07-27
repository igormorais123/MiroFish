"""
Execução truncada chega ao relatório como limitação, não como duração nominal.

No caso Vale Trading rodaram 12 de 240 rodadas e o relatório apresentou
"Rodadas 12 | 12 — mesma duração nominal". O total configurado nunca chegava ao
prompt, então não havia como o modelo saber que a execução cobriu 5% do desenho.
"""

from unittest.mock import patch

from app.services.report_agent import ReportAgent


def _contexto(run_state, sim):
    """Monta o contexto de escala com os dois estados injetados."""
    with patch.object(ReportAgent, "_dict_from_runtime_state", side_effect=lambda d: d or {}), \
         patch("app.services.simulation_manager.SimulationManager") as manager, \
         patch("app.services.simulation_runner.SimulationRunner") as runner, \
         patch("app.services.simulation_data_reader.SimulationDataReader") as reader:
        manager.return_value.get_simulation.return_value = sim
        runner.get_run_state.return_value = run_state
        reader.return_value.get_diversity_metrics.return_value = {}
        return ReportAgent._build_helena_scale_context("sim_x")


def test_execucao_truncada_e_declarada_com_cobertura():
    ctx = _contexto({"current_round": 12}, {"total_rounds": 240, "profiles_count": 96})

    escopo = ctx["rounds_scope"]
    assert "12 de 240" in escopo
    assert "5%" in escopo
    assert "truncada" in escopo
    assert "limitacao" in escopo


def test_execucao_completa_nao_vira_alerta():
    ctx = _contexto({"current_round": 240}, {"total_rounds": 240, "profiles_count": 96})

    assert "completa" in ctx["rounds_scope"]
    assert "truncada" not in ctx["rounds_scope"]


def test_sem_dado_de_rodada_nao_inventa_numero():
    ctx = _contexto({}, {})

    assert ctx["rounds_scope"] == "desconhecido"


def test_configurado_ausente_nao_acusa_truncamento():
    """Sem o total previsto não dá para afirmar que faltou rodada."""
    ctx = _contexto({"current_round": 30}, {"profiles_count": 10})

    assert "truncada" not in ctx["rounds_scope"]
    assert "30" in ctx["rounds_scope"]
