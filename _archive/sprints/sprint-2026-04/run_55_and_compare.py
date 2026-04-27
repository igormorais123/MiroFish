"""Roda somente o GPT-5.5 (5.4-mini ja esta feito), depois gera COMPARATIVO.md."""
from __future__ import annotations
import re
import time
from pathlib import Path
import requests

BASE = "http://localhost:5001"
TOKEN = "mirofish-inteia-local-2026"
HEADERS = {"X-Internal-Token": TOKEN, "Content-Type": "application/json"}
ROOT = Path(r"C:\Users\IgorPC\.claude\projects\Mirofish INTEIA")
TASK_5MINI = "0f152eed-ff55-47ba-b8aa-b410de428df0"


def now() -> str:
    return time.strftime("%H:%M:%S")


def log(msg: str):
    print(f"[{now()}] {msg}", flush=True)
    with open(ROOT / "compare.log", "a", encoding="utf-8") as f:
        f.write(f"[{now()}] {msg}\n")


def wait_task(task_id: str, label: str, timeout: int = 5400) -> dict:
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
        time.sleep(10)
    raise TimeoutError(f"{label} timeout")


def load_payload() -> dict:
    d1 = Path(r"C:\Users\IgorPC\.hermes\memories\DOSSIE_IGOR_COMPLETO.md").read_text(encoding="utf-8")
    d2 = Path(r"C:\Users\IgorPC\.hermes\memories\DOSSIE_IGOR_VOZ_PROPRIA.md").read_text(encoding="utf-8")
    return {
        "name": "Igor Morais - comparativo GPT-5.5",
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


def fetch_result(task_id: str) -> dict:
    r_result = requests.get(f"{BASE}/api/internal/v1/tasks/{task_id}", headers=HEADERS, timeout=15).json()["data"]
    out = {"task_id": task_id, "result": r_result}
    try:
        t_elapsed = (time.mktime(time.strptime(r_result.get("updated_at", "").split(".")[0], "%Y-%m-%dT%H:%M:%S"))
                     - time.mktime(time.strptime(r_result.get("created_at", "").split(".")[0], "%Y-%m-%dT%H:%M:%S")))
        out["elapsed_s"] = round(t_elapsed, 1)
    except Exception:
        out["elapsed_s"] = None
    if r_result.get("status") == "completed":
        rid = (r_result.get("result") or {}).get("report_id")
        if rid:
            rep = requests.get(f"{BASE}/api/report/{rid}", timeout=30).json()["data"]
            out["report_id"] = rid
            out["markdown"] = rep.get("markdown_content", "")
            out["report_chars"] = len(out["markdown"])
    return out


def analyze(md: str, dossie: str) -> dict:
    if not md:
        return {"sections": 0, "quotes": 0, "quotes_grounded": 0, "chars": 0, "percent_refs": 0}
    sections = len(re.findall(r"^## ", md, flags=re.MULTILINE))
    quotes = re.findall(r'"([^"]{15,})"', md)
    grounded = 0
    for q in quotes:
        for start in range(0, max(1, len(q) - 20), 10):
            snippet = q[start:start + 20].strip()
            if len(snippet) >= 15 and snippet in dossie:
                grounded += 1
                break
    return {
        "sections": sections,
        "quotes": len(quotes),
        "quotes_grounded": grounded,
        "chars": len(md),
        "percent_refs": len(re.findall(r"\d+\s*%", md)),
    }


def main():
    payload = load_payload()
    log("Disparando run GPT-5.5...")
    t0 = time.time()
    r = requests.post(f"{BASE}/api/internal/v1/run-preset", json=payload, headers=HEADERS, timeout=30)
    r.raise_for_status()
    tid = r.json()["data"]["task_id"]
    log(f"[5.5] task={tid}")
    wait_task(tid, "5.5", timeout=5400)

    r1 = fetch_result(TASK_5MINI)
    r2 = fetch_result(tid)
    r1["alias"] = "gpt-5.4-mini"
    r2["alias"] = "gpt-5.5"

    dossie = (Path(r"C:\Users\IgorPC\.hermes\memories\DOSSIE_IGOR_COMPLETO.md").read_text(encoding="utf-8")
              + Path(r"C:\Users\IgorPC\.hermes\memories\DOSSIE_IGOR_VOZ_PROPRIA.md").read_text(encoding="utf-8"))
    a1 = analyze(r1.get("markdown", ""), dossie)
    a2 = analyze(r2.get("markdown", ""), dossie)

    out = ROOT / "COMPARATIVO_GPT54mini_vs_GPT55.md"
    lines = [
        "# Comparativo GPT-5.4-mini vs GPT-5.5 - Mirofish\n",
        f"Gerado: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n",
        "Payload identico (dossies Igor + preset smoke). Backend Mirofish apontando pro Codex proxy OAuth.\n\n",
        "## Resumo\n\n",
        "| Modelo | Tempo (s) | Relatorio (chars) | Secoes | Citacoes | Grounded | Percentuais |\n",
        "|---|---|---|---|---|---|---|\n",
        f"| gpt-5.4-mini | {r1.get('elapsed_s','?')} | {a1['chars']} | {a1['sections']} | {a1['quotes']} | {a1['quotes_grounded']}/{a1['quotes']} | {a1['percent_refs']} |\n",
        f"| gpt-5.5 | {r2.get('elapsed_s','?')} | {a2['chars']} | {a2['sections']} | {a2['quotes']} | {a2['quotes_grounded']}/{a2['quotes']} | {a2['percent_refs']} |\n\n",
        "## Interpretacao\n\n",
        "- Tempo: relacao 5.5/mini revela overhead do modelo premium.\n",
        "- Grounded: citacoes verificaveis no dossie (sinal anti-fabricacao).\n",
        "- Percentuais: numeros soltos sem base no dossie = potencial fabricacao.\n\n",
        "## Relatorio gpt-5.4-mini (primeiros 6000 chars)\n\n```markdown\n",
        (r1.get("markdown", "")[:6000] or "(vazio)"),
        "\n```\n\n",
        "## Relatorio gpt-5.5 (primeiros 6000 chars)\n\n```markdown\n",
        (r2.get("markdown", "")[:6000] or "(vazio)"),
        "\n```\n",
    ]
    out.write_text("".join(lines), encoding="utf-8")
    (ROOT / f"REL_5.4mini_{r1.get('task_id','')[:8]}.md").write_text(r1.get("markdown", ""), encoding="utf-8")
    (ROOT / f"REL_5.5_{r2.get('task_id','')[:8]}.md").write_text(r2.get("markdown", ""), encoding="utf-8")
    log(f"Comparativo salvo: {out}")
    print("\n=== RESUMO ===")
    print(f"5.4-mini: {r1.get('elapsed_s','?')}s | {a1['chars']} chars | {a1['quotes_grounded']}/{a1['quotes']} grounded")
    print(f"5.5     : {r2.get('elapsed_s','?')}s | {a2['chars']} chars | {a2['quotes_grounded']}/{a2['quotes']} grounded")


if __name__ == "__main__":
    main()
