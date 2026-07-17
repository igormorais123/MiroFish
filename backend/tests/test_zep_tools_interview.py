from app.services.simulation_runner import SimulationRunner
from app.services.zep_tools import ZepToolsService


def test_interview_agents_retorna_sem_espera_quando_ambiente_inativo(monkeypatch):
    monkeypatch.setattr(
        SimulationRunner,
        "check_env_alive",
        classmethod(lambda cls, simulation_id: False),
    )
    service = object.__new__(ZepToolsService)

    result = service.interview_agents(
        simulation_id="sim_inativa",
        interview_requirement="avaliar coalizoes",
    )

    assert result.interviewed_count == 0
    assert "indisponivel" in result.summary.lower()


def test_check_env_alive_rejeita_status_orfao_sem_processo(monkeypatch):
    monkeypatch.setattr(SimulationRunner, "_processes", {})

    assert SimulationRunner.check_env_alive("sim_status_orfao") is False
