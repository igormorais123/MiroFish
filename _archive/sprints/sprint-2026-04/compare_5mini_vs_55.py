"""Comparativo GPT-5.4-mini vs GPT-5.5 no Mirofish.

Aguarda task atual (5.4-mini) terminar, troca .env para 5.5 em tudo, dispara
preset idêntico, coleta métricas e gera COMPARATIVO.md.
"""
from __future__ import annotations
import json
import os
import re
import time
from pathlib import Path

import requests

BASE = "http://localhost:5001"
PROXY = "http://localhost:8004"
TOKEN = "mirofish-inteia-local-2026"
HEADERS = {"X-Internal-Token": TOKEN, "Content-Type": "application/json"}
ROOT = Path(r"C:\Users\IgorPC\.claude\projects\Mirofish INTEIA")


def now() -> str:
    return time.strftime("%H:%M:%S")


def log(msg: str):
    print(f"[{now()}] {msg}", flush=True)


def wait_task(task_id: str, label: str, timeout: int = 3600) -> dict:
    start = time.time()
    last = ""
    while time.time() - start < timeout:
        r = requests.get(f"{BASE}/api/internal/v1/tasks/{task_id}", headers=HEADERS, timeout=15).json()["data"]
        cur = f"{r.get('status')} {r.get('progress', 0)}% {r.get('message', '')}"
        if cur != last:
            log(f"[{label}] {cur}")
            last = cur
        if r.get("status") in ("completed", "failed"):
            return r
        time.sleep(8)
    raise TimeoutError(f"{label} timeout")


def load_payload() -> dict:
    d1 = Path(r"C:\Users\IgorPC\.hermes\memories\DOSSIE_IGOR_COMPLETO.md").read_text(encoding="utf-8")
    d2 = Path(r"C:\Users\IgorPC\.hermes\memories\DOSSIE_IGOR_VOZ_PROPRIA.md").read_text(encoding="utf-8")
    return {
        "name": "Igor Morais — comparativo",
        "simulation_requirement": (
            "Simular vida de Igor em 7 dias conforme vozes dos dossies. "
            "Mapear tensoes (saude, INTEIA, doutorado, Paixao Cortes) e reacoes em redes."
        ),
        "preset": "smoke",
        "materials": [
            {"filename": "DOSSIE_IGOR_COMPLETO.md", "text": d1},
            {"filename": "DOSSIE_IGOR_VOZ_PROPRIA.md", "text": d2},
        ],
        "structured_context": {
            "cenario": "Semana tipica de Igor em Brasilia-DF",
            "territorio": "Distrito Federal",
            "atores": ["Igor Morais", "Familia", "Paixao Cortes Adv", "equipe INTEIA", "colegas SEEDF", "orientador IDP"],
        },
        "enable_twitter": True,
        "enable_reddit": True,
    }


def switch_env(alias_model: str):
    """Troca .env apontando todos os aliases para alias_model."""
    env_path = ROOT / ".env"
    text = env_path.read_text(encoding="utf-8")
    # Substitui todos os aliases
    text = re.sub(
        r'^LLM_MODEL_ALIASES=.*$',
        f'LLM_MODEL_ALIASES={{"helena-premium":"{alias_model}","sonnet-tasks":"{alias_model}","opus-tasks":"{alias_model}","haiku-tasks":"{alias_model}"}}',
        text, flags=re.MULTILINE,
    )
    text = re.sub(r'^LLM_MODEL_NAME=.*$', f'LLM_MODEL_NAME={alias_model}', text, flags=re.MULTILINE)
    text = re.sub(r'^GRAPHITI_MODEL=.*$', f'GRAPHITI_MODEL={alias_model}', text, flags=re.MULTILINE)
    env_path.write_text(text, encoding="utf-8")
    log(f"ENV atualizado -> modelo={alias_model}")


def restart_backend():
    import subprocess
    # Mata processo na 5001
    subprocess.run(
        ["powershell.exe", "-NoProfile", "-Command",
         "Get-NetTCPConnection -LocalPort 5001 -State Listen -ErrorAction SilentlyContinue | "
         "Select-Object -ExpandProperty OwningProcess | Sort-Object -Unique | "
         "ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }"],
        shell=False, capture_output=True,
    )
    time.sleep(3)
    # Restart backend detached
    subprocess.Popen(
        [str(ROOT / "backend" / ".venv" / "Scripts" / "python.exe"), str(ROOT / "backend" / "run.py")],
        cwd=str(ROOT),
        stdout=open(ROOT / "logs_backend.log", "ab"),
        stderr=open(ROOT / "logs_backend.log", "ab"),
        creationflags=0x00000008,  # DETACHED_PROCESS
    )
    # Aguarda health
    for _ in range(15):
        try:
            h = requests.get(f"{BASE}/health", timeout=3).json()
            if h.get("status") == "ok":
                log(f"Backend OK model={h.get('llm_model')}")
                return
        except Exception:
            pass
        time.sleep(2)
    raise RuntimeError("Backend nao subiu")


def run(alias: str, payload: dict) -> dict:
    t0 = time.time()
    r = requests.post(f"{BASE}/api/internal/v1/run-preset", json=payload, headers=HEADERS, timeout=30)
    r.raise_for_status()
    tid = r.json()["data"]["task_id"]
    log(f"[{alias}] task={tid}")
    result = wait_task(tid, alias, timeout=3600)
    elapsed = time.time() - t0
    out = {"alias": alias, "task_id": tid, "elapsed_s": round(elapsed, 1), "result": result}

    if result.get("status") == "completed" and result.get("result", {}).get("report_id"):
        rid = result["result"]["report_id"]
        rep = requests.get(f"{BASE}/api/report/{rid}", timeout=30).json()["data"]
        out["report_id"] = rid
        out["markdown"] = rep.get("markdown_content", "")
        out["report_chars"] = len(out["markdown"])
    return out


def analyze_report(md: str, dossie_text: str) -> dict:
    """Mede indicadores de qualidade / fabricacao."""
    if not md:
        return {"sections": 0, "quotes": 0, "quotes_grounded": 0, "chars": 0, "has_percent": False}
    sections = len(re.findall(r"^## ", md, flags=re.MULTILINE))
    quotes = re.findall(r'"([^"]{15,})"', md)
    quote_count = len(quotes)
    grounded = 0
    for q in quotes:
        # heuristica: se uma sub-frase de 20+ chars aparece no dossie -> grounded
        for start in range(0, max(1, len(q) - 20), 10):
            snippet = q[start:start + 20].strip()
            if len(snippet) >= 15 and snippet in dossie_text:
                grounded += 1
                break
    percent_refs = len(re.findall(r"\d+\s*%", md))
    return {
        "sections": sections,
        "quotes": quote_count,
        "quotes_grounded": grounded,
        "chars": len(md),
        "percent_refs": percent_refs,
    }


def main():
    # 1. Aguarda task atual (5.4-mini) terminar
    current_task = "0f152eed-ff55-47ba-b8aa-b410de428df0"
    log(f"Aguardando task atual {current_task} (5.4-mini)...")
    r1_result = wait_task(current_task, "5.4-mini", timeout=3600)
    t1_elapsed = None
    try:
        t1_elapsed = (time.mktime(time.strptime(r1_result.get("updated_at", "").split(".")[0], "%Y-%m-%dT%H:%M:%S"))
                      - time.mktime(time.strptime(r1_result.get("created_at", "").split(".")[0], "%Y-%m-%dT%H:%M:%S")))
    except Exception:
        t1_elapsed = None

    r1 = {"alias": "gpt-5.4-mini", "task_id": current_task, "elapsed_s": t1_elapsed, "result": r1_result}
    if r1_result.get("status") == "completed":
        rid = r1_result.get("result", {}).get("report_id")
        if rid:
            rep = requests.get(f"{BASE}/api/report/{rid}", timeout=30).json()["data"]
            r1["report_id"] = rid
            r1["markdown"] = rep.get("markdown_content", "")
            r1["report_chars"] = len(r1["markdown"])

    # 2. Troca modelo para 5.5 e roda
    switch_env("gpt-5.5")
    restart_backend()
    payload = load_payload()
    payload["name"] = "Igor Morais — comparativo GPT-5.5"
    r2 = run("gpt-5.5", payload)

    # 3. Analisa
    dossie_all = (
        Path(r"C:\Users\IgorPC\.hermes\memories\DOSSIE_IGOR_COMPLETO.md").read_text(encoding="utf-8")
        + Path(r"C:\Users\IgorPC\.hermes\memories\DOSSIE_IGOR_VOZ_PROPRIA.md").read_text(encoding="utf-8")
    )
    a1 = analyze_report(r1.get("markdown", ""), dossie_all)
    a2 = analyze_report(r2.get("markdown", ""), dossie_all)

    # 4. Relatorio comparativo
    out = ROOT / "COMPARATIVO_GPT54mini_vs_GPT55.md"
    lines = [
        "# Comparativo GPT-5.4-mini vs GPT-5.5 — Mirofish\n",
        f"Gerado: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n",
        "Payload idêntico (dossiês Igor + preset smoke). Backend Mirofish apontando pro Codex proxy.\n\n",
        "## Tempo total pipeline\n\n",
        "| Modelo | Tempo (s) | Relatório (chars) | Seções | Citações | Grounded | Nº percentuais |\n",
        "|---|---|---|---|---|---|---|\n",
        f"| gpt-5.4-mini | {r1.get('elapsed_s','?')} | {a1['chars']} | {a1['sections']} | {a1['quotes']} | {a1['quotes_grounded']}/{a1['quotes']} | {a1['percent_refs']} |\n",
        f"| gpt-5.5 | {r2.get('elapsed_s','?')} | {a2['chars']} | {a2['sections']} | {a2['quotes']} | {a2['quotes_grounded']}/{a2['quotes']} | {a2['percent_refs']} |\n\n",
        "## Interpretação Helena\n\n",
        "- **Tempo**: proporção 5.5/mini indica overhead do modelo premium.\n",
        "- **Grounded**: citações que aparecem nos dossiês (fato) vs fabricadas.\n",
        "- **Percentuais**: menos é melhor quando simulação teve poucos dados (menor fabricação).\n\n",
        "## Relatório gpt-5.4-mini\n\n",
        "```markdown\n",
        (r1.get("markdown", "")[:6000] or "(vazio)"),
        "\n```\n\n",
        "## Relatório gpt-5.5\n\n",
        "```markdown\n",
        (r2.get("markdown", "")[:6000] or "(vazio)"),
        "\n```\n",
    ]
    out.write_text("".join(lines), encoding="utf-8")
    # Salva relatórios completos também
    (ROOT / f"REL_5.4mini_{r1.get('task_id', '')[:8]}.md").write_text(r1.get("markdown", ""), encoding="utf-8")
    (ROOT / f"REL_5.5_{r2.get('task_id', '')[:8]}.md").write_text(r2.get("markdown", ""), encoding="utf-8")
    log(f"Comparativo salvo: {out}")
    print("\n=== RESUMO ===")
    print(f"5.4-mini: {r1.get('elapsed_s','?')}s | {a1['chars']} chars | {a1['quotes_grounded']}/{a1['quotes']} citações grounded")
    print(f"5.5     : {r2.get('elapsed_s','?')}s | {a2['chars']} chars | {a2['quotes_grounded']}/{a2['quotes']} citações grounded")


if __name__ == "__main__":
    main()
