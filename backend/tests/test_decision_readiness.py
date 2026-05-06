from app.services.decision_readiness import evaluate_decision_readiness
from app.services.report_agent import Report, ReportStatus
from app.services.report_system_gate import ReportGateResult
from app.services.simulation_manager import SimulationState, SimulationStatus


class FakeSimulationManager:
    state = None

    def get_simulation(self, simulation_id):
        return self.state


def _state(status=SimulationStatus.COMPLETED):
    return SimulationState(
        simulation_id="sim_1",
        project_id="proj_1",
        graph_id="graph_1",
        status=status,
        profiles_count=10,
    )


def test_decision_readiness_missing_simulation(monkeypatch):
    FakeSimulationManager.state = None
    monkeypatch.setattr("app.services.decision_readiness.SimulationManager", FakeSimulationManager)

    result = evaluate_decision_readiness("sim_missing")

    assert result["status"] == "missing"
    assert result["next_action"] == "select_simulation"
    assert result["flags"]["simulation_exists"] is False


def test_decision_readiness_ready_for_report(monkeypatch):
    FakeSimulationManager.state = _state()
    monkeypatch.setattr("app.services.decision_readiness.SimulationManager", FakeSimulationManager)
    monkeypatch.setattr("app.services.decision_readiness.ProjectManager.get_project", lambda project_id: object())
    monkeypatch.setattr("app.services.decision_readiness.ProjectManager.get_extracted_text", lambda project_id: "fonte")
    monkeypatch.setattr(
        "app.services.decision_readiness.evaluate_report_system_gate",
        lambda *args, **kwargs: ReportGateResult(True, metrics={"total_actions_count": 10}),
    )
    monkeypatch.setattr("app.services.decision_readiness.ReportManager.get_report_by_simulation", lambda simulation_id: None)

    result = evaluate_decision_readiness("sim_1")

    assert result["status"] == "ready_for_report"
    assert result["next_action"] == "generate_report"
    assert result["flags"]["gate_passes"] is True


def test_decision_readiness_reports_publishable_state(monkeypatch):
    FakeSimulationManager.state = _state()
    report = Report(
        report_id="report_1",
        simulation_id="sim_1",
        graph_id="graph_1",
        simulation_requirement="teste",
        status=ReportStatus.COMPLETED,
        quality_gate={"passes_gate": True, "metrics": {}},
        evidence_audit={"passes_gate": True},
    )
    monkeypatch.setattr("app.services.decision_readiness.SimulationManager", FakeSimulationManager)
    monkeypatch.setattr("app.services.decision_readiness.ProjectManager.get_project", lambda project_id: object())
    monkeypatch.setattr("app.services.decision_readiness.ProjectManager.get_extracted_text", lambda project_id: "fonte")
    monkeypatch.setattr(
        "app.services.decision_readiness.evaluate_report_system_gate",
        lambda *args, **kwargs: ReportGateResult(True, metrics={"total_actions_count": 10}),
    )
    monkeypatch.setattr(
        "app.services.decision_readiness.ReportManager.get_report_by_simulation",
        lambda simulation_id: report,
    )

    result = evaluate_decision_readiness("sim_1")

    assert result["status"] == "ready_for_verified_delivery"
    assert result["next_action"] == "open_delivery_package"
    assert result["report"]["report_publishable"] is True


def test_decision_readiness_blocked_by_gate(monkeypatch):
    FakeSimulationManager.state = _state(SimulationStatus.READY)
    monkeypatch.setattr("app.services.decision_readiness.SimulationManager", FakeSimulationManager)
    monkeypatch.setattr("app.services.decision_readiness.ProjectManager.get_project", lambda project_id: object())
    monkeypatch.setattr("app.services.decision_readiness.ProjectManager.get_extracted_text", lambda project_id: "")
    monkeypatch.setattr(
        "app.services.decision_readiness.evaluate_report_system_gate",
        lambda *args, **kwargs: ReportGateResult(False, issues=["simulacao incompleta"]),
    )
    monkeypatch.setattr("app.services.decision_readiness.ReportManager.get_report_by_simulation", lambda simulation_id: None)

    result = evaluate_decision_readiness("sim_1")

    assert result["status"] == "blocked"
    assert result["next_action"] == "fix_simulation_or_source_material"
    assert result["blockers"] == ["simulacao incompleta"]
