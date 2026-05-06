"""Testes de unidade para app.utils.report_quality (Phase 3)."""
from __future__ import annotations

import pytest

from app.utils.report_quality import (
    audit_report_evidence,
    evaluate_section_grounding,
    extract_numeric_claims,
    extract_direct_quotes,
    jaccard_similarity,
    measure_overlap,
    quote_supported_by_evidence,
    render_evidence_audit_block,
    render_qc_block,
)
from app.services.report_attribution import normalize_report_attribution
from app.services import report_agent as report_agent_module
from app.services.report_agent import (
    Report,
    ReportAgent,
    ReportManager,
    ReportOutline,
    ReportSection,
    ReportStatus,
)
from app.utils.token_tracker import TokenTracker


def test_jaccard_disjoint_returns_zero():
    a = "Igor advogado Brasilia trabalha SEEDF"
    b = "Sergipe mar dunas Aracaju capital Nordeste"
    assert jaccard_similarity(a, b, ngram=5) == 0.0


def test_jaccard_identical_returns_one():
    text = "Igor advogado Brasilia trabalha SEEDF doutorando IDP fundador INTEIA Colmeia"
    assert jaccard_similarity(text, text, ngram=5) == pytest.approx(1.0)


def test_jaccard_normaliza_acentos():
    """NFKD garante que palavras com/sem acento batem."""
    a = "Brasilia capital federal politica nacional saude educacao"
    b = "Brasília capital federal política nacional saúde educação"
    score = jaccard_similarity(a, b, ngram=3)
    assert score > 0.5, f"esperado > 0.5, obtido {score}"


def test_jaccard_short_text_returns_zero():
    """Texto curto demais para n-grama pedido retorna 0."""
    assert jaccard_similarity("oi tudo bem", "oi tudo bem", ngram=10) == 0.0


def test_measure_overlap_alert_dispara_acima_threshold():
    text = "Igor advogado Brasilia trabalha SEEDF doutorando IDP fundador INTEIA Colmeia"
    o = measure_overlap(text, text, threshold=0.30)
    assert o["alert"] is True
    assert o["jaccard_5gram"] > 0.30


def test_measure_overlap_alert_nao_dispara_em_textos_diferentes():
    o = measure_overlap("Igor advogado Brasilia trabalha SEEDF", "Sergipe mar dunas", threshold=0.30)
    assert o["alert"] is False
    assert o["jaccard_5gram"] == 0.0


def test_grounding_aprova_secao_com_numero_quote_entidade():
    content = 'Em 2024, 35% dos eleitores apoiaram Ibaneis. "Vai ganhar de novo" disse o analista.'
    result = evaluate_section_grounding(content, known_entities=["Ibaneis", "Leandro Grass"])
    assert result["passes_gate"] is True
    assert result["has_number"] is True
    assert result["has_quote"] is True
    assert result["entity_hits"] == 1


def test_grounding_rejeita_secao_narrativa_generica():
    content = "Os agentes podem reagir de varias formas no cenario simulado, dependendo do contexto."
    result = evaluate_section_grounding(content, [])
    assert result["passes_gate"] is False
    assert result["score"] == 0.0


def test_grounding_aprova_so_com_numero_e_entidade():
    """Secao sem aspas mas com numero (0.4) + 2 entidades (0.2) = 0.6 -> passa."""
    content = "Em 2024, Ibaneis perdeu apoio para Leandro Grass na pesquisa."
    result = evaluate_section_grounding(content, ["Ibaneis", "Leandro Grass"])
    assert result["score"] >= 0.5
    assert result["passes_gate"] is True


def test_grounding_ignora_entidades_curtas():
    """Entidades com <3 chars sao ignoradas para evitar falsos positivos."""
    content = "Algo sobre PT e SP em 2024."
    result = evaluate_section_grounding(content, ["PT", "SP"])
    assert result["entity_hits"] == 0


def test_render_qc_block_inclui_alerta_quando_overlap_alto():
    overlap = {"jaccard_5gram": 0.45, "jaccard_3gram": 0.55, "alert": True, "threshold": 0.30, "tokens_report": 1000, "tokens_upload": 800}
    md = render_qc_block(overlap)
    assert "ALTO" in md
    assert "QC" in md
    assert "45.0%" in md


def test_render_qc_block_sem_alerta_quando_overlap_baixo():
    overlap = {"jaccard_5gram": 0.05, "jaccard_3gram": 0.15, "alert": False, "threshold": 0.30, "tokens_report": 1000, "tokens_upload": 800}
    md = render_qc_block(overlap)
    assert "OK" in md
    assert "ALTO" not in md


def test_render_qc_block_lista_secoes_quando_fornecidas():
    overlap = {"jaccard_5gram": 0.10, "jaccard_3gram": 0.20, "alert": False, "threshold": 0.30, "tokens_report": 500, "tokens_upload": 500}
    sections = [
        {"score": 0.8, "passes_gate": True, "has_number": True, "has_quote": True, "entity_hits": 2},
        {"score": 0.0, "passes_gate": False, "has_number": False, "has_quote": False, "entity_hits": 0},
    ]
    md = render_qc_block(overlap, sections)
    assert "1/2" in md
    assert "Gate editorial" in md


def test_extract_direct_quotes_ignora_blocos_de_codigo():
    text = 'Relatorio cita "fala real do agente".\n\n```md\n"exemplo falso no prompt"\n```'
    assert extract_direct_quotes(text) == ["fala real do agente"]


def test_quote_supported_by_evidence_exige_corpus():
    evidence = ['Agent A escreveu: "precisamos testar antes de decidir" no round 2.']
    assert quote_supported_by_evidence("precisamos testar antes de decidir", evidence) is True
    assert quote_supported_by_evidence("frase inventada sem lastro", evidence) is False


def test_audit_report_evidence_bloqueia_citacao_inventada():
    report = 'A simulacao mostrou: "frase inventada sem lastro".'
    audit = audit_report_evidence(report, ["conteudo real da simulacao"])
    assert audit["passes_gate"] is False
    assert audit["quotes_unsupported"] == 1


def test_audit_report_evidence_aprova_citacoes_presentes():
    evidence = ["Maria (twitter, round 1): precisamos testar antes de decidir"]
    report = 'A reacao central foi: "precisamos testar antes de decidir".'
    audit = audit_report_evidence(report, evidence)
    assert audit["passes_gate"] is True
    assert audit["quotes_supported"] == 1


def test_extract_numeric_claims_ignora_blocos_de_qc_gerados():
    claims = extract_numeric_claims(
        "Resultado principal: 40%.\n\n---\n\n## QC — Cobertura e Grounding\n- limite 30%"
    )

    assert [claim["number"] for claim in claims] == ["40%"]


def test_extract_numeric_claims_ignora_titulos_markdown():
    claims = extract_numeric_claims(
        "## Provas, Perguntas do Decisor e Janela de 15/30/60 Dias\n\n"
        "Resultado principal: 40%."
    )

    assert [claim["number"] for claim in claims] == ["40%"]


def test_audit_report_evidence_bloqueia_numero_sem_suporte():
    audit = audit_report_evidence(
        "Cenario Base tem 68% de probabilidade.",
        ["A simulacao registrou 10 acoes."],
        fail_on_unsupported_quotes=True,
        fail_on_unsupported_numbers=True,
    )

    assert audit["passes_gate"] is False
    assert audit["numbers_unsupported"] == 1
    assert audit["unsupported_numbers"][0]["number"] == "68%"


def test_audit_report_evidence_aceita_numero_rotulado_como_inferencia():
    audit = audit_report_evidence(
        "[Inferencia calibrada] Cenario Base tem 68% de probabilidade.",
        ["A simulacao registrou 10 acoes."],
        fail_on_unsupported_numbers=True,
    )

    assert audit["passes_gate"] is True
    assert audit["numbers_labeled_inference"] == 1


def test_audit_report_evidence_aceita_prazo_rotulado_como_sugestao_operacional():
    audit = audit_report_evidence(
        "[Sugestao operacional] Em 48 horas, anexar a decisao e as pecas essenciais.",
        ["A simulacao registrou 10 acoes."],
        fail_on_unsupported_numbers=True,
    )

    assert audit["passes_gate"] is True
    assert audit["numbers_labeled_inference"] == 1


def test_render_evidence_audit_block_mostra_bloqueio():
    audit = {
        "passes_gate": False,
        "quotes_total": 1,
        "quotes_supported": 0,
        "evidence_documents": 2,
        "unsupported_quotes": ["frase inventada sem lastro"],
    }
    md = render_evidence_audit_block(audit)
    assert "BLOQUEADO" in md
    assert "frase inventada" in md


def test_normalize_report_attribution_converte_citacao_sem_suporte_em_secao():
    content = 'A secao inventou a fala "vamos vencer sem nenhum ajuste".'
    evidence = ["Registro real: precisamos testar antes de decidir."]

    result = normalize_report_attribution(content, evidence)

    assert '"vamos vencer sem nenhum ajuste"' not in result["content"]
    assert "[Inferencia da simulacao] vamos vencer sem nenhum ajuste" in result["content"]
    assert result["converted_quotes_count"] == 1
    assert result["quotes"] == []


def test_report_agent_normalize_section_attribution_retorna_conteudo_e_metadados():
    content = 'A secao preserva "precisamos testar antes de decidir" e converte "vamos vencer".'
    evidence = ["Maria (round 1): precisamos testar antes de decidir"]

    normalized, attribution = ReportAgent._normalize_section_attribution(
        content,
        evidence,
        section_index=2,
        section_title="Sinais da simulacao",
    )

    assert '"precisamos testar antes de decidir"' in normalized
    assert '"vamos vencer"' not in normalized
    assert "[Inferencia da simulacao] vamos vencer" in normalized
    assert attribution == {
        "section_index": 2,
        "section_title": "Sinais da simulacao",
        "converted_quotes_count": 1,
        "quotes": [
            {
                "quote": "precisamos testar antes de decidir",
                "supported": True,
                "origin_index": 0,
                "origin_text": "Maria (round 1): precisamos testar antes de decidir",
            }
        ],
    }


def test_report_agent_build_failed_section_content_e_claro_para_cliente():
    content = ReportAgent._build_failed_section_content("timeout interno")

    assert content == "Falha ao gerar esta seção. A missão deve ser reexecutada para completar esta parte."
    assert "timeout interno" not in content


def test_report_agent_sanitize_llm_response_for_log_remove_final_answer_bruto():
    response = (
        "Thought: dados coletados.\n"
        'Final Answer: A secao inventou a fala "vamos vencer sem nenhum ajuste".'
    )

    sanitized = ReportAgent._sanitize_llm_response_for_log(response)

    assert "Thought: dados coletados." in sanitized
    assert 'A secao inventou a fala "vamos vencer sem nenhum ajuste".' not in sanitized
    assert sanitized.endswith(
        "Final Answer: [conteudo final normalizado registrado em section_content]"
    )


def test_report_agent_strategic_density_gate_blocks_generic_report(monkeypatch):
    saved_artifacts = {}
    saved_reports = []

    def fake_save_json_artifact(report_id, filename, payload):
        saved_artifacts[(report_id, filename)] = payload

    def fake_save_report(report):
        saved_reports.append(report)

    monkeypatch.setattr(ReportManager, "save_json_artifact", fake_save_json_artifact)
    monkeypatch.setattr(ReportManager, "save_report", fake_save_report)
    report = Report(
        report_id="report_density_blocked",
        simulation_id="sim_test",
        graph_id="graph_test",
        simulation_requirement="teste",
        status=ReportStatus.COMPLETED,
        quality_gate={"passes_gate": True, "issues": []},
    )

    with pytest.raises(ValueError, match="baixa densidade estrategica"):
        ReportAgent._apply_strategic_density_gate(
            report,
            "report_density_blocked",
            "O melhor caminho e agir com prudencia, organizar documentos e manter comunicacao clara.",
        )

    assert report.quality_gate["passes_gate"] is False
    assert report.status == ReportStatus.FAILED
    assert report.error == "Relatorio bloqueado por baixa densidade estrategica"
    assert "Relatorio bloqueado por baixa densidade estrategica" in report.quality_gate["issues"]
    assert report.quality_gate["strategic_density"]["passes_gate"] is False
    assert saved_artifacts[("report_density_blocked", "strategic_density.json")]["passes_gate"] is False
    assert saved_reports == [report]


def test_report_agent_section_error_does_not_complete_report(monkeypatch):
    saved_reports = []
    saved_artifacts = {}
    progress_updates = []
    TokenTracker().reset_all()

    class DummyGateResult:
        def to_dict(self):
            return {"passes_gate": True, "issues": []}

    class DummyReportLogger:
        def __init__(self, report_id):
            self.report_id = report_id

        def log_start(self, **kwargs):
            pass

        def log_planning_start(self):
            pass

        def log_planning_complete(self, outline_dict):
            pass

        def log_section_content(self, **kwargs):
            pass

        def log_section_full_complete(self, **kwargs):
            pass

        def log_report_complete(self, **kwargs):
            raise AssertionError("report should not be completed")

        def log_error(self, *args, **kwargs):
            pass

    class DummyConsoleLogger:
        def __init__(self, report_id):
            self.report_id = report_id

        def close(self):
            pass

    def fake_save_report(report):
        saved_reports.append(report)

    def fake_save_json_artifact(report_id, filename, payload):
        saved_artifacts[(report_id, filename)] = payload

    def fake_update_progress(report_id, status, progress, message, **kwargs):
        progress_updates.append((status, progress, message))

    def fake_assemble_full_report(report_id, outline):
        return outline.to_markdown()

    monkeypatch.setattr(report_agent_module, "ReportLogger", DummyReportLogger)
    monkeypatch.setattr(report_agent_module, "ReportConsoleLogger", DummyConsoleLogger)
    monkeypatch.setattr(ReportManager, "_ensure_report_folder", lambda report_id: None)
    monkeypatch.setattr(ReportManager, "save_report", fake_save_report)
    monkeypatch.setattr(ReportManager, "save_outline", lambda report_id, outline: None)
    monkeypatch.setattr(ReportManager, "save_section", lambda report_id, section_index, section: "")
    monkeypatch.setattr(ReportManager, "save_json_artifact", fake_save_json_artifact)
    monkeypatch.setattr(ReportManager, "update_progress", fake_update_progress)
    monkeypatch.setattr(ReportManager, "assemble_full_report", fake_assemble_full_report)

    import app.services.report_system_gate as report_system_gate

    monkeypatch.setattr(
        report_system_gate,
        "assert_report_system_ready",
        lambda **kwargs: DummyGateResult(),
    )
    monkeypatch.setattr(
        report_system_gate,
        "collect_report_evidence",
        lambda **kwargs: {
            "evidence_texts": [],
            "evidence_index": [],
            "total_evidence_documents": 0,
        },
    )
    monkeypatch.setattr(
        report_system_gate,
        "compact_evidence_for_manifest",
        lambda evidence_index: evidence_index,
    )

    outline = ReportOutline(
        title="Relatorio",
        summary="Resumo",
        sections=[
            ReportSection(title="Secao boa"),
            ReportSection(title="Secao com erro"),
        ],
    )
    agent = ReportAgent(
        simulation_id="sim_test",
        graph_id="graph_test",
        simulation_requirement="teste",
    )
    monkeypatch.setattr(agent, "plan_outline", lambda progress_callback=None: outline)

    def fake_generate_section(section, **kwargs):
        if section.title == "Secao com erro":
            raise RuntimeError("timeout interno")
        return "Conteudo substantivo da secao boa com evidencia e decisao.", 0

    monkeypatch.setattr(agent, "_generate_section_react", fake_generate_section)
    monkeypatch.setattr(
        agent,
        "_normalize_section_attribution",
        lambda content, evidence_texts, section_index, section_title: (
            content,
            {
                "section_index": section_index,
                "section_title": section_title,
                "converted_quotes_count": 0,
                "quotes": [],
            },
        ),
    )

    report = agent.generate_report(report_id="report_section_failure", source_text="texto-base")

    assert report.status == ReportStatus.FAILED
    assert report.error == "Relatorio interrompido: uma ou mais secoes falharam na geracao"
    assert report.completed_at == ""
    assert "Falha ao gerar esta seção" in report.markdown_content
    assert not any(status == "completed" for status, _progress, _message in progress_updates)
    assert saved_artifacts[("report_section_failure", "section_errors.json")]["sections"][0][
        "section_title"
    ] == "Secao com erro"
    assert saved_artifacts[("report_section_failure", "cost_meter.json")] == report.quality_gate[
        "cost_meter"
    ]
    assert saved_reports[-1].status == ReportStatus.FAILED
    assert agent._cost_session_kwargs() == {}


def test_report_agent_generate_report_success_salva_cost_meter(monkeypatch):
    saved_reports = []
    saved_artifacts = {}
    progress_updates = []
    TokenTracker().reset_all()

    class DummyGateResult:
        def to_dict(self):
            return {"passes_gate": True, "issues": []}

    class DummyReportLogger:
        def __init__(self, report_id):
            self.report_id = report_id

        def log_start(self, **kwargs):
            pass

        def log_planning_start(self):
            pass

        def log_planning_complete(self, outline_dict):
            pass

        def log_section_content(self, **kwargs):
            pass

        def log_section_full_complete(self, **kwargs):
            pass

        def log_report_complete(self, **kwargs):
            pass

        def log_error(self, *args, **kwargs):
            pass

    class DummyConsoleLogger:
        def __init__(self, report_id):
            self.report_id = report_id

        def close(self):
            pass

    monkeypatch.setattr(report_agent_module, "ReportLogger", DummyReportLogger)
    monkeypatch.setattr(report_agent_module, "ReportConsoleLogger", DummyConsoleLogger)
    monkeypatch.setattr(ReportManager, "_ensure_report_folder", lambda report_id: None)
    monkeypatch.setattr(ReportManager, "save_report", lambda report: saved_reports.append(report))
    monkeypatch.setattr(ReportManager, "save_outline", lambda report_id, outline: None)
    monkeypatch.setattr(ReportManager, "save_section", lambda report_id, section_index, section: "")
    monkeypatch.setattr(
        ReportManager,
        "save_json_artifact",
        lambda report_id, filename, payload: saved_artifacts.__setitem__(
            (report_id, filename), payload
        ),
    )
    monkeypatch.setattr(
        ReportManager,
        "update_progress",
        lambda report_id, status, progress, message, **kwargs: progress_updates.append(
            (status, progress, message)
        ),
    )
    monkeypatch.setattr(ReportManager, "assemble_full_report", lambda report_id, outline: outline.to_markdown())

    import app.services.report_system_gate as report_system_gate

    monkeypatch.setattr(
        report_system_gate,
        "assert_report_system_ready",
        lambda **kwargs: DummyGateResult(),
    )
    monkeypatch.setattr(
        report_system_gate,
        "collect_report_evidence",
        lambda **kwargs: {
            "evidence_texts": [],
            "evidence_index": [],
            "total_evidence_documents": 0,
        },
    )
    monkeypatch.setattr(
        report_system_gate,
        "compact_evidence_for_manifest",
        lambda evidence_index: evidence_index,
    )

    outline = ReportOutline(
        title="Relatorio",
        summary="Resumo",
        sections=[ReportSection(title="Secao unica")],
    )
    agent = ReportAgent(
        simulation_id="sim_test",
        graph_id="graph_test",
        simulation_requirement="teste",
    )
    monkeypatch.setattr(agent, "plan_outline", lambda progress_callback=None: outline)
    monkeypatch.setattr(
        agent,
        "_generate_section_react",
        lambda **kwargs: ("Conteudo substantivo com evidencia qualitativa e decisao.", 0),
    )
    monkeypatch.setattr(
        agent,
        "_normalize_section_attribution",
        lambda content, evidence_texts, section_index, section_title: (
            content,
            {
                "section_index": section_index,
                "section_title": section_title,
                "converted_quotes_count": 0,
                "quotes": [],
            },
        ),
    )
    monkeypatch.setattr(agent, "_generate_helena_analysis", lambda assembled_content, outline: None)
    monkeypatch.setattr(agent, "_apply_strategic_density_gate", lambda report, report_id, content: None)

    report = agent.generate_report(report_id="report_success", source_text="texto-base")

    assert report.status == ReportStatus.COMPLETED
    assert saved_artifacts[("report_success", "cost_meter.json")] == report.quality_gate[
        "cost_meter"
    ]
    assert saved_reports[-1].status == ReportStatus.COMPLETED
    assert any(status == "completed" for status, _progress, _message in progress_updates)
    assert agent._cost_session_kwargs() == {}


def test_interview_agents_result_with_success_and_items_is_usable():
    agent = ReportAgent(simulation_id="sim_test", graph_id="graph_test", simulation_requirement="teste")
    payload = {"success": True, "results": [{"agent_name": "A", "answer": "resposta util"} for _ in range(8)]}
    assert agent._is_usable_interview_result(payload) is True


def test_interview_agents_empty_success_is_not_usable():
    agent = ReportAgent(simulation_id="sim_test", graph_id="graph_test", simulation_requirement="teste")
    assert agent._is_usable_interview_result({"success": True, "results": []}) is False


def test_interview_agents_json_string_with_results_is_usable():
    agent = ReportAgent(simulation_id="sim_test", graph_id="graph_test", simulation_requirement="teste")
    payload = '{"success": true, "results": [{"agent_name": "A", "answer": "ok"}]}'
    assert agent._is_usable_interview_result(payload) is True


def test_interview_agents_success_false_is_not_usable():
    agent = ReportAgent(simulation_id="sim_test", graph_id="graph_test", simulation_requirement="teste")
    payload = {"success": False, "results": [{"agent_name": "A", "answer": "resposta"}]}
    assert agent._is_usable_interview_result(payload) is False


def test_interview_agents_data_list_is_usable():
    agent = ReportAgent(simulation_id="sim_test", graph_id="graph_test", simulation_requirement="teste")
    payload = {"success": True, "data": [{"agent_name": "A", "answer": "resposta"}]}
    assert agent._is_usable_interview_result(payload) is True


def test_interview_agents_interviews_list_is_usable():
    agent = ReportAgent(simulation_id="sim_test", graph_id="graph_test", simulation_requirement="teste")
    payload = {"success": True, "interviews": [{"agent_name": "A", "answer": "resposta"}]}
    assert agent._is_usable_interview_result(payload) is True


def test_interview_agents_empty_text_is_not_usable():
    agent = ReportAgent(simulation_id="sim_test", graph_id="graph_test", simulation_requirement="teste")
    assert agent._is_usable_interview_result("   ") is False


def test_interview_agents_non_json_text_is_not_usable():
    agent = ReportAgent(simulation_id="sim_test", graph_id="graph_test", simulation_requirement="teste")
    assert agent._is_usable_interview_result("sem entrevistas disponiveis") is False


def test_format_interview_result_text_includes_names_and_answers_from_payload_shapes():
    payload = {
        "success": True,
        "data": [
            {
                "agent_name": "Maria",
                "question": "Qual foi sua reacao?",
                "answer": "Achei a medida insuficiente.",
            }
        ],
    }

    text_from_dict = ReportAgent._format_interview_result_text(payload)
    text_from_list = ReportAgent._format_interview_result_text(payload["data"])
    text_from_json = ReportAgent._format_interview_result_text(
        '{"success": true, "interviews": [{"name": "Joao", "response": "Apoio com ressalvas."}]}'
    )

    assert "Entrevistas com agentes simulados" in text_from_dict
    assert "Maria" in text_from_dict
    assert "Pergunta: Qual foi sua reacao?" in text_from_dict
    assert "Resposta: Achei a medida insuficiente." in text_from_dict
    assert "Maria" in text_from_list
    assert "Joao" in text_from_json
    assert "Resposta: Apoio com ressalvas." in text_from_json


class _FakeTextResult:
    def __init__(self, text):
        self.text = text

    def to_text(self):
        return self.text


class _FakeZepTools:
    def __init__(self, interview_result):
        self.interview_result = interview_result
        self.quick_search_calls = 0

    def interview_agents(self, **kwargs):
        return self.interview_result

    def quick_search(self, **kwargs):
        self.quick_search_calls += 1
        return _FakeTextResult("resultado via busca rapida")


def test_execute_tool_interview_agents_does_not_call_quick_search_when_interview_is_usable():
    agent = ReportAgent(simulation_id="sim_test", graph_id="graph_test", simulation_requirement="teste")
    fake_zep = _FakeZepTools({"success": True, "results": [{"agent_name": "Ana", "answer": "resposta util"}]})
    agent.zep_tools = fake_zep

    result = agent._execute_tool("interview_agents", {"interview_topic": "tema"})

    assert fake_zep.quick_search_calls == 0
    assert "Ana" in result
    assert "Resposta: resposta util" in result


def test_execute_tool_interview_agents_calls_quick_search_when_interview_is_not_usable():
    agent = ReportAgent(simulation_id="sim_test", graph_id="graph_test", simulation_requirement="teste")
    fake_zep = _FakeZepTools("sem entrevistas disponiveis")
    agent.zep_tools = fake_zep

    result = agent._execute_tool("interview_agents", {"interview_topic": "tema"})

    assert fake_zep.quick_search_calls == 1
    assert "Entrevista nao disponivel" in result
    assert "resultado via busca rapida" in result


def test_report_agent_cost_meter_helpers_salvam_snapshot_com_fases(monkeypatch):
    saved_artifacts = {}
    tracker = TokenTracker()
    tracker.reset_all()

    def fake_save_json_artifact(report_id, filename, payload):
        saved_artifacts[(report_id, filename)] = payload

    monkeypatch.setattr(ReportManager, "save_json_artifact", fake_save_json_artifact)

    agent = ReportAgent(simulation_id="sim_test", graph_id="graph_test", simulation_requirement="teste")
    report = Report(
        report_id="report_cost_success",
        simulation_id="sim_test",
        graph_id="graph_test",
        simulation_requirement="teste",
        status=ReportStatus.COMPLETED,
        quality_gate={"passes_gate": True, "issues": []},
    )

    agent._start_cost_session(report.report_id)
    agent._switch_cost_phase("preparacao")
    tracker.track(100, 20, session_id=report.report_id, phase_id="preparacao")
    agent._switch_cost_phase("planejamento")
    tracker.track(200, 30, session_id=report.report_id, phase_id="planejamento")

    snapshot = agent._save_cost_meter_snapshot(report, report.report_id)

    assert saved_artifacts[(report.report_id, "cost_meter.json")] == snapshot
    assert report.quality_gate["cost_meter"] == snapshot
    assert snapshot["prompt_tokens"] == 300
    assert snapshot["phases"]["preparacao"]["rotulo"] == "Preparação da missão"
    assert snapshot["phases"]["planejamento"]["rotulo"] == "Planejamento do relatório"
    assert snapshot["phases"]["preparacao"]["estado"] == "concluida"
    assert snapshot["phases"]["planejamento"]["estado"] == "concluida"


def test_report_agent_cost_meter_aplica_poderes_comerciais(monkeypatch):
    saved_artifacts = {}
    tracker = TokenTracker()
    tracker.reset_all()

    monkeypatch.setattr(
        ReportManager,
        "save_json_artifact",
        lambda report_id, filename, payload: saved_artifacts.__setitem__(
            (report_id, filename), payload
        ),
    )

    agent = ReportAgent(
        simulation_id="sim_cost_power",
        graph_id="graph_cost_power",
        simulation_requirement="teste",
        power_selection={
            "selected_ids": ["modo_rapido", "bundle_supremo"],
            "multiplicador_total": 2,
            "custo_fixo_brl": 1200,
            "poderes_selecionados": [
                {
                    "id": "modo_rapido",
                    "nome": "Modo Rápido",
                    "custo_tipo": "multiplicador_tokens",
                    "multiplicador_tokens": 2.5,
                },
                {
                    "id": "bundle_supremo",
                    "nome": "Pacote Supremo",
                    "custo_tipo": "custo_fixo_brl",
                    "custo_fixo_brl": 1200,
                },
            ],
        },
    )
    report = Report(
        report_id="report_cost_power",
        simulation_id="sim_cost_power",
        graph_id="graph_cost_power",
        simulation_requirement="teste",
        status=ReportStatus.GENERATING,
    )
    tracker.track(1_000_000, 0, session_id=report.report_id)

    snapshot = agent._save_cost_meter_snapshot(report, report.report_id)

    assert snapshot["inteia_value_brl_base"] > 0
    assert snapshot["inteia_value_brl"] == round(snapshot["inteia_value_brl_base"] * 2 + 1200, 2)
    assert snapshot["power_multiplier"] == 2
    assert snapshot["power_fixed_cost_brl"] == 1200
    assert len(snapshot["poderes_comerciais"]) == 2
    assert snapshot["power_value_delta_brl"] == round(snapshot["inteia_value_brl"] - snapshot["inteia_value_brl_base"], 2)
    assert snapshot["power_cost_formula"] == "valor_base * multiplicador_total + custo_fixo"
    assert [item["nome"] for item in snapshot["power_cost_components"]] == ["Modo Rápido", "Pacote Supremo"]
    assert saved_artifacts[(report.report_id, "cost_meter.json")] == snapshot


def test_report_agent_cost_meter_snapshot_e_salvo_em_falha(monkeypatch):
    saved_artifacts = {}
    tracker = TokenTracker()
    tracker.reset_all()

    monkeypatch.setattr(
        ReportManager,
        "save_json_artifact",
        lambda report_id, filename, payload: saved_artifacts.__setitem__(
            (report_id, filename), payload
        ),
    )

    agent = ReportAgent(simulation_id="sim_test", graph_id="graph_test", simulation_requirement="teste")
    report = Report(
        report_id="report_cost_failure",
        simulation_id="sim_test",
        graph_id="graph_test",
        simulation_requirement="teste",
        status=ReportStatus.FAILED,
        error="falha simulada",
    )

    agent._start_cost_session(report.report_id)
    agent._switch_cost_phase("secoes")
    tracker.track(50, 10, session_id=report.report_id, phase_id="secoes")

    snapshot = agent._save_cost_meter_snapshot(report, report.report_id)

    assert saved_artifacts[(report.report_id, "cost_meter.json")] == snapshot
    assert report.quality_gate["cost_meter"]["phases"]["secoes"]["rotulo"] == "Escrita das seções"
    assert report.quality_gate["cost_meter"]["phases"]["secoes"]["estado"] == "concluida"


def test_report_agent_power_persona_context_vazio_nao_altera_prompt():
    agent = ReportAgent(simulation_id="sim_test", graph_id="graph_test", simulation_requirement="teste")

    assert agent._power_persona_prompt_block() == ""
    assert report_agent_module.PLAN_SYSTEM_PROMPT + agent._power_persona_prompt_block() == report_agent_module.PLAN_SYSTEM_PROMPT


def test_report_agent_power_persona_context_entra_no_bloco_de_prompt():
    agent = ReportAgent(
        simulation_id="sim_test",
        graph_id="graph_test",
        simulation_requirement="teste",
        power_persona_context="- Helena [consultor_lendario]: leitura estrategica.",
    )

    block = agent._power_persona_prompt_block()

    assert "[Contexto selecionado de poderes e personas]" in block
    assert "Helena" in block
    assert block in (report_agent_module.PLAN_SYSTEM_PROMPT + block)


def test_report_agent_power_selection_context_entra_no_bloco_de_prompt():
    agent = ReportAgent(
        simulation_id="sim_test",
        graph_id="graph_test",
        simulation_requirement="teste",
        power_selection={
            "selected_ids": ["contrarians"],
            "poderes_selecionados": [
                {
                    "id": "contrarians",
                    "nome": "Contrarians",
                    "impacto": "Eleva robustez critica.",
                }
            ],
        },
    )

    block = agent._power_selection_prompt_block()

    assert "[Poderes ativos da missao]" in block
    assert "Contrarians" in block
    assert "Eleva robustez critica" in block


def test_report_agent_prediction_contract_block_contem_eixos_obrigatorios():
    agent = ReportAgent(simulation_id="sim_test", graph_id="graph_test", simulation_requirement="teste")

    block = agent._prediction_contract_block().lower()

    for expected in [
        "linha recomendada / tese vencedora",
        "tese adversária mais forte",
        "distorcer cada movimento",
        "cortar, evitar ou não pedir agora",
        "ação/pedido seguro agora",
        "ação/pedido perigoso agora",
        "documentos/comprovantes necessários",
        "15, 30 e 60 dias",
        "perguntas prováveis do decisor",
        "gatilhos que mudariam a recomendação",
        "ganho real sobre o óbvio",
    ]:
        assert expected in block


def test_report_agent_prompts_nao_forcam_aviso_de_enfraquecimento():
    combined_prompt = (
        report_agent_module.PLAN_SYSTEM_PROMPT
        + report_agent_module.PLAN_USER_PROMPT_TEMPLATE
        + report_agent_module.SECTION_SYSTEM_PROMPT_TEMPLATE
    ).lower()

    forbidden_fragments = [
        "aviso: amostra pequena",
        "baixa confianca",
        "[base curta]",
        "disclaimer",
        "lgpd",
    ]

    for fragment in forbidden_fragments:
        assert fragment not in combined_prompt


class _CapturePlanningLLM:
    def __init__(self):
        self.messages = None

    def chat_json(self, messages, **kwargs):
        self.messages = messages
        return {
            "title": "Relatorio de teste",
            "summary": "Resumo de teste",
            "sections": [
                {"title": "Tese vencedora", "description": "desc"},
                {"title": "Tese adversaria", "description": "desc"},
            ],
        }


class _FakePlanningZepTools:
    def get_simulation_context(self, **kwargs):
        return {
            "graph_statistics": {
                "total_nodes": 2,
                "total_edges": 1,
                "entity_types": {"Agent": 2},
            },
            "total_entities": 2,
            "related_facts": [{"fact": "fato simulado"}],
        }


def test_report_agent_plan_prompt_final_inclui_contrato():
    llm = _CapturePlanningLLM()
    agent = ReportAgent(
        simulation_id="sim_test",
        graph_id="graph_test",
        simulation_requirement="teste",
        llm_client=llm,
        zep_tools=_FakePlanningZepTools(),
    )

    outline = agent.plan_outline()

    assert outline.title == "Relatorio de teste"
    assert llm.messages is not None
    assert agent._prediction_contract_block() in llm.messages[1]["content"]


class _CaptureSectionLLM:
    def __init__(self):
        self.first_messages = None

    def chat(self, messages, **kwargs):
        if self.first_messages is None:
            self.first_messages = [dict(message) for message in messages]
        return "Final Answer: Conteudo final com tese, limite e risco residual."


class _SectionLLMWithRawDraftThenFinal:
    def __init__(self):
        self.calls = 0

    def chat(self, messages, **kwargs):
        self.calls += 1
        if self.calls <= 3:
            return '<tool_call>{"name":"quick_search","parameters":{"query":"ponto"}}</tool_call>'
        if self.calls == 4:
            return "Thought: ja tenho dados. Observation: texto interno."
        return "Final Answer: Conteudo final limpo com linha recomendada."


class _SectionLLMWithInvalidForcedClose:
    def __init__(self):
        self.calls = 0

    def chat(self, messages, **kwargs):
        self.calls += 1
        if self.calls <= 3:
            return '<tool_call>{"name":"quick_search","parameters":{"query":"ponto"}}</tool_call>'
        return "Thought: rascunho interno sem fechamento correto."


def test_report_agent_section_prompt_final_inclui_contrato():
    llm = _CaptureSectionLLM()
    agent = ReportAgent(
        simulation_id="sim_test",
        graph_id="graph_test",
        simulation_requirement="teste",
        llm_client=llm,
        zep_tools=_FakePlanningZepTools(),
    )
    outline = ReportOutline(
        title="Relatorio",
        summary="Resumo",
        sections=[ReportSection(title="Secao")],
    )

    agent._generate_section_react(
        section=outline.sections[0],
        outline=outline,
        previous_sections=[],
    )

    assert llm.first_messages is not None
    assert agent._prediction_contract_block() in llm.first_messages[0]["content"]


def test_report_agent_power_persona_context_permanece_com_contrato_no_prompt_de_secao():
    llm = _CaptureSectionLLM()
    agent = ReportAgent(
        simulation_id="sim_test",
        graph_id="graph_test",
        simulation_requirement="teste",
        llm_client=llm,
        zep_tools=_FakePlanningZepTools(),
        power_persona_context="- Helena [consultor_lendario]: leitura estrategica.",
    )
    outline = ReportOutline(
        title="Relatorio",
        summary="Resumo",
        sections=[ReportSection(title="Secao")],
    )

    agent._generate_section_react(
        section=outline.sections[0],
        outline=outline,
        previous_sections=[],
    )

    system_prompt = llm.first_messages[0]["content"]
    assert agent._prediction_contract_block() in system_prompt
    assert "[Contexto selecionado de poderes e personas]" in system_prompt
    assert "Helena" in system_prompt
    assert system_prompt.count("[Contexto selecionado de poderes e personas]") == 1


def test_report_agent_section_nao_publica_rascunho_sem_final_answer(monkeypatch):
    llm = _SectionLLMWithRawDraftThenFinal()
    agent = ReportAgent(
        simulation_id="sim_test",
        graph_id="graph_test",
        simulation_requirement="teste",
        llm_client=llm,
        zep_tools=_FakePlanningZepTools(),
    )
    monkeypatch.setattr(agent, "_execute_tool", lambda *args, **kwargs: "resultado observado")
    outline = ReportOutline(
        title="Relatorio",
        summary="Resumo",
        sections=[ReportSection(title="Secao")],
    )

    content, tool_calls = agent._generate_section_react(
        section=outline.sections[0],
        outline=outline,
        previous_sections=[],
    )

    assert tool_calls == 3
    assert content == "Conteudo final limpo com linha recomendada."
    assert "Thought:" not in content
    assert "Observation:" not in content


def test_report_agent_section_falha_quando_fechamento_final_invalido(monkeypatch):
    llm = _SectionLLMWithInvalidForcedClose()
    agent = ReportAgent(
        simulation_id="sim_test",
        graph_id="graph_test",
        simulation_requirement="teste",
        llm_client=llm,
        zep_tools=_FakePlanningZepTools(),
    )
    monkeypatch.setattr(agent, "_execute_tool", lambda *args, **kwargs: "resultado observado")
    outline = ReportOutline(
        title="Relatorio",
        summary="Resumo",
        sections=[ReportSection(title="Secao")],
    )

    with pytest.raises(RuntimeError, match="Falha ao fechar a secao"):
        agent._generate_section_react(
            section=outline.sections[0],
            outline=outline,
            previous_sections=[],
        )
