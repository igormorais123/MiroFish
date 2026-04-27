"""Pipeline completo: cria projeto, grafo, simulacao e relatorio sobre os dossies de Igor."""
import json
import os
import sys
import time
from pathlib import Path

import requests

BASE = "http://localhost:5001"
TOKEN = "mirofish-inteia-local-2026"
HEADERS = {"X-Internal-Token": TOKEN, "Content-Type": "application/json"}

DOSSIES = [
    Path(r"C:\Users\IgorPC\.hermes\memories\DOSSIE_IGOR_COMPLETO.md"),
    Path(r"C:\Users\IgorPC\.hermes\memories\DOSSIE_IGOR_VOZ_PROPRIA.md"),
]

SIM_REQUIREMENT = (
    "Simular a vida cotidiana, trabalho e interacoes sociais de Igor Morais Vasconcelos "
    "(advogado, 41 anos, Assessor Especial SEEDF, doutorando IDP em IA, fundador da INTEIA, "
    "TDAH + TEA Grau 1 + Altas Habilidades) em um ciclo de 7 dias. Os perfis simulados devem "
    "reagir conforme as vozes registradas nos dossies: discurso direto, sem bajulacao, foco "
    "em sistemas e externalizacao cognitiva. Mapear pontos de tensao (saude, paixao cortes, "
    "doutorado, INTEIA como negocio) e como ele provavelmente se comportaria nas redes."
)


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def post(path, payload=None, timeout=600):
    r = requests.post(f"{BASE}{path}", headers=HEADERS, json=payload or {}, timeout=timeout)
    if r.status_code >= 400:
        log(f"ERRO {r.status_code} em {path}: {r.text[:500]}")
        r.raise_for_status()
    return r.json()


def get(path, timeout=60):
    r = requests.get(f"{BASE}{path}", headers=HEADERS, timeout=timeout)
    r.raise_for_status()
    return r.json()


def poll_task(task_id, label, max_wait=1800, interval=5):
    start = time.time()
    last_msg = ""
    while time.time() - start < max_wait:
        d = get(f"/api/internal/v1/tasks/{task_id}")["data"]
        status = d.get("status")
        msg = f"{d.get('progress', 0)}% {d.get('message', '')}"
        if msg != last_msg:
            log(f"[{label}] {msg}")
            last_msg = msg
        if status in ("completed", "failed"):
            if status == "failed":
                raise RuntimeError(f"{label} falhou: {d.get('message')}")
            return d
        time.sleep(interval)
    raise TimeoutError(f"{label} nao completou em {max_wait}s")


def main():
    # 1. Health
    h = requests.get(f"{BASE}/health", timeout=5).json()
    log(f"Backend OK - LLM model: {h['llm_model']}")

    # 2. Criar projeto a partir dos dossies (modo sync para bloquear ate ontologia)
    materials = []
    for p in DOSSIES:
        text = p.read_text(encoding="utf-8")
        materials.append({"filename": p.name, "text": text})
        log(f"Dossie {p.name}: {len(text)} chars")

    log("Criando projeto from-briefing (gera ontologia, pode levar 1-3min)...")
    payload = {
        "name": "Simulacao vida de Igor",
        "simulation_requirement": SIM_REQUIREMENT,
        "materials": materials,
        "structured_context": {
            "cenario": "Semana tipica de Igor em Brasilia-DF, balanceando SEEDF, doutorado, INTEIA e saude.",
            "territorio": "Distrito Federal",
            "atores": ["Igor Morais", "Familia", "Paixao Cortes Adv", "equipe INTEIA", "colegas SEEDF", "orientador IDP"],
            "canais": ["WhatsApp", "Gmail", "LinkedIn", "Instagram", "terapia"],
            "hipoteses": [
                "TDAH sem Venvanse amplifica dispersao em tarefas longas",
                "Foco excessivo em sistemas externos (Colmeia) como compensacao cognitiva",
                "Risco de burn-out se INTEIA nao gerar receita em 60 dias",
            ],
            "objetivos_analiticos": [
                "Mapear padroes de energia/atencao ao longo da semana",
                "Identificar pontos de ruptura e rotas de mitigacao",
                "Prever reacoes em canais sociais dadas as vozes dos dossies",
            ],
        },
    }
    r = post("/api/internal/v1/projects/from-briefing", payload, timeout=600)
    project = r["data"]
    project_id = project["project_id"]
    log(f"Projeto criado: {project_id} (status={project.get('status')})")

    # 3. Construir grafo
    log("Disparando construcao do grafo...")
    r = post(f"/api/internal/v1/projects/{project_id}/graph/build", {})
    graph_task = r["data"]["task_id"]
    poll_task(graph_task, "graph-build", max_wait=1800)
    proj = get(f"/api/internal/v1/projects/{project_id}")["data"]
    graph_id = proj["graph_id"]
    log(f"Grafo concluido: {graph_id}")

    # 4. Criar simulacao
    log("Criando simulacao...")
    r = post(f"/api/internal/v1/projects/{project_id}/simulation", {"enable_twitter": True, "enable_reddit": True})
    sim = r["data"]
    sim_id = sim["simulation_id"]
    log(f"Simulacao criada: {sim_id}")

    # 5. Preparar
    log("Preparando simulacao (gera perfis)...")
    r = post(f"/api/internal/v1/simulations/{sim_id}/prepare", {"use_llm_for_profiles": True, "parallel_profile_count": 5})
    poll_task(r["data"]["task_id"], "prepare", max_wait=1800)

    # 6. Start
    log("Iniciando simulacao...")
    r = post(f"/api/internal/v1/simulations/{sim_id}/start", {"platform": "parallel", "max_rounds": 10})
    log(f"Runner start: {json.dumps(r['data'], ensure_ascii=False)[:300]}")

    # 7. Poll run-status
    log("Aguardando simulacao rodar...")
    start = time.time()
    while time.time() - start < 3600:
        rs = get(f"/api/internal/v1/simulations/{sim_id}/run-status")["data"]
        # OASIS retorna `runner_status`, nao `status`. Aceita ambos pra compatibilidade.
        status = rs.get("runner_status") or rs.get("status")
        log(f"run-status: {status} round={rs.get('current_round')}")
        if status in ("completed", "failed", "stopped"):
            break
        time.sleep(15)

    # 8. Gerar relatorio
    log("Disparando geracao de relatorio...")
    r = requests.post(f"{BASE}/api/report/generate", json={"simulation_id": sim_id}, timeout=30).json()
    report_id = r["data"]["report_id"]
    task_id = r["data"]["task_id"]
    log(f"Report {report_id} / task {task_id}")

    # Poll report
    start = time.time()
    while time.time() - start < 1800:
        st = requests.post(f"{BASE}/api/report/generate/status", json={"task_id": task_id}, timeout=30).json()["data"]
        log(f"report: {st.get('progress')}% {st.get('message', '')}")
        if st.get("status") in ("completed", "failed"):
            break
        time.sleep(10)

    # Salvar
    full = requests.get(f"{BASE}/api/report/{report_id}", timeout=30).json()
    out = Path(f"REL_Igor_simulacao_{sim_id[:12]}.json")
    out.write_text(json.dumps(full, ensure_ascii=False, indent=2), encoding="utf-8")
    log(f"Relatorio salvo em {out}")

    # Markdown bonito se possivel
    data = full.get("data", {})
    md_parts = [f"# Simulacao Igor - {sim_id}\n"]
    md_parts.append(f"**Projeto:** {project_id}\n\n**Requirement:** {SIM_REQUIREMENT}\n\n")
    for section in data.get("sections", []) or []:
        md_parts.append(f"## {section.get('title', 'Secao')}\n\n{section.get('content', '')}\n\n")
    if data.get("content"):
        md_parts.append(f"\n---\n\n{data['content']}\n")
    Path(f"REL_Igor_simulacao_{sim_id[:12]}.md").write_text("".join(md_parts), encoding="utf-8")
    log(f"Relatorio markdown: REL_Igor_simulacao_{sim_id[:12]}.md")


if __name__ == "__main__":
    main()
