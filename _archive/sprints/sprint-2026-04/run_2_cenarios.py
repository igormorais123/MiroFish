"""Roda 2 simulacoes Mirofish com cenarios COMPLETAMENTE DIFERENTES (testa hipotese cache).

1. Julgamento processo Igor vs Melissa (PDF 0812709-43.2025)
2. Eleicao Sergipe 2026 (todos cargos, 5 documentos)

Aguarda task atual terminar antes de iniciar.
"""
from __future__ import annotations
import re, time
from pathlib import Path
import requests

BASE = "http://localhost:5001"
TOKEN = "mirofish-inteia-local-2026"
HEADERS = {"X-Internal-Token": TOKEN, "Content-Type": "application/json"}
ROOT = Path(r"C:\Users\IgorPC\.claude\projects\Mirofish INTEIA")
TASK_ATUAL = "afe4b6f9-a9b0-47a5-9d7d-3e1a0e5cfb01"
LOG = ROOT / "cenarios.log"


def now(): return time.strftime("%H:%M:%S")
def log(m):
    print(f"[{now()}] {m}", flush=True)
    with open(LOG, "a", encoding="utf-8") as f: f.write(f"[{now()}] {m}\n")


def wait_task(tid, label, timeout=5400):
    start = time.time(); last = ""
    while time.time() - start < timeout:
        try:
            r = requests.get(f"{BASE}/api/internal/v1/tasks/{tid}", headers=HEADERS, timeout=15).json()["data"]
        except Exception as e:
            log(f"[{label}] WARN polling error: {e}"); time.sleep(15); continue
        cur = f"{r.get('status')} {r.get('progress',0)}% {r.get('message','')}"
        if cur != last: log(f"[{label}] {cur}"); last = cur
        if r.get("status") in ("completed", "failed"): return r
        time.sleep(12)
    raise TimeoutError(f"{label} timeout")


def fetch(tid):
    r = requests.get(f"{BASE}/api/internal/v1/tasks/{tid}", headers=HEADERS, timeout=15).json()["data"]
    out = {"task_id": tid, "result": r}
    try:
        out["elapsed_s"] = round(
            time.mktime(time.strptime(r.get("updated_at","").split(".")[0], "%Y-%m-%dT%H:%M:%S"))
            - time.mktime(time.strptime(r.get("created_at","").split(".")[0], "%Y-%m-%dT%H:%M:%S")), 1)
    except Exception: out["elapsed_s"] = None
    if r.get("status") == "completed":
        rid = (r.get("result") or {}).get("report_id")
        if rid:
            rep = requests.get(f"{BASE}/api/report/{rid}", timeout=30).json()["data"]
            out["report_id"] = rid
            out["markdown"] = rep.get("markdown_content","")
    return out


def dispatch(payload, label):
    log(f"Disparando {label}...")
    r = requests.post(f"{BASE}/api/internal/v1/run-preset", json=payload, headers=HEADERS, timeout=30)
    r.raise_for_status()
    tid = r.json()["data"]["task_id"]
    log(f"[{label}] task={tid}")
    wait_task(tid, label, timeout=5400)
    return fetch(tid)


def truncate(text, max_chars):
    if len(text) <= max_chars: return text
    half = max_chars // 2
    return text[:half] + f"\n\n[...TRUNCADO {len(text)-max_chars} chars no meio...]\n\n" + text[-half:]


def cenario_julgamento():
    pdf_text = (ROOT / "_processo_0416.txt").read_text(encoding="utf-8", errors="replace")
    log(f"PDF processo: {len(pdf_text)} chars (truncando para 180k)")
    pdf_text = truncate(pdf_text, 180000)
    return {
        "name": "Julgamento Igor vs Melissa - 0812709-43.2025.8.07.0016",
        "simulation_requirement": (
            "Simular o desenrolar do julgamento deste processo de divorcio/reconvencao Igor x Melissa. "
            "Mapear: provaveis decisoes do juiz, posturas das partes, recursos esperados, repercussao "
            "familiar e profissional para Igor (advogado, doutorando, pai), riscos reputacionais. "
            "Considerar que Igor e advogado e que o processo envolve guarda de filho e disputa patrimonial."
        ),
        "preset": "smoke",
        "materials": [{"filename": "ProcessoInteiroTeor_0416.txt", "text": pdf_text}],
        "structured_context": {
            "cenario": "Processo TJDFT 0812709-43.2025.8.07.0016 - audiencia/julgamento iminente",
            "territorio": "Distrito Federal",
            "atores": ["Igor Morais (autor/reconvinte)", "Melissa (re/reconvinda)", "Juiz da 16a Vara",
                       "Promotor", "Advogados das partes", "Familia Igor", "Familia Melissa", "Filho menor"],
        },
        "enable_twitter": False, "enable_reddit": False,
    }


def cenario_sergipe():
    base = Path(r"C:\Users\IgorPC\.claude\projects\Eleitores sintéticos Sergipe\Estudos eleitorado sergipe e dados estatisticos")
    files = [
        "SERGIPE_DADOS_DEMOGRAFICOS_2026.md",
        "deep-research-report.md",
        "Criação de Eleitores Sintéticos Sergipe.md",
        "compass_artifact_wf-07b66204-6925-467b-990d-d1816de73238_text_markdown.md",
        "dados achados notbook lm.txt",
    ]
    materials = []
    total = 0
    for f in files:
        text = (base / f).read_text(encoding="utf-8", errors="replace")
        materials.append({"filename": f, "text": text})
        total += len(text)
    log(f"Sergipe: {len(materials)} arquivos, {total} chars total")
    return {
        "name": "Eleicao Sergipe 2026 - todos os cargos",
        "simulation_requirement": (
            "Simular a eleicao 2026 em Sergipe para TODOS os cargos: Governador, Senador, "
            "Deputados Federais, Deputados Estaduais. Mapear: principais coligacoes, candidatos "
            "competitivos, regioes-chave (Aracaju, sertao, agreste, litoral sul), dinamicas "
            "demograficas (idade, renda, escolaridade), tensoes ideologicas, padroes de transferencia "
            "de votos. Identificar cenarios prováveis e zonas de incerteza."
        ),
        "preset": "smoke",
        "materials": materials,
        "structured_context": {
            "cenario": "Eleicoes gerais 2026 em Sergipe",
            "territorio": "Sergipe (todos os 75 municipios)",
            "atores": ["Eleitor sergipano", "Governador atual", "Lideres partidarios PSD/MDB/PT/PL/PP/UB",
                       "Prefeitos das regioes-chave", "Influenciadores locais", "Jornal Cinform/F5News",
                       "Empresariado", "Servidores publicos", "Movimentos sociais"],
        },
        "enable_twitter": True, "enable_reddit": True,
    }


def main():
    log("=== Aguardando task atual terminar antes de iniciar cenarios novos ===")
    wait_task(TASK_ATUAL, "5.5-v2-current", timeout=5400)
    log("Task atual finalizada. Iniciando cenarios novos.")

    log("\n========== CENARIO 1: JULGAMENTO ==========")
    r1 = dispatch(cenario_julgamento(), "julgamento")
    (ROOT / f"REL_julgamento_{r1['task_id'][:8]}.md").write_text(r1.get("markdown","") or "(vazio)", encoding="utf-8")
    log(f"Julgamento: {r1.get('elapsed_s','?')}s, {len(r1.get('markdown',''))} chars, report_id={r1.get('report_id','?')}")

    log("\n========== CENARIO 2: SERGIPE ==========")
    r2 = dispatch(cenario_sergipe(), "sergipe")
    (ROOT / f"REL_sergipe_{r2['task_id'][:8]}.md").write_text(r2.get("markdown","") or "(vazio)", encoding="utf-8")
    log(f"Sergipe: {r2.get('elapsed_s','?')}s, {len(r2.get('markdown',''))} chars, report_id={r2.get('report_id','?')}")

    log("\n=== TODOS OS CENARIOS COMPLETOS ===")


if __name__ == "__main__":
    main()
