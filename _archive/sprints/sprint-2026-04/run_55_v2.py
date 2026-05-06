"""Roda 2a vez o GPT-5.5 (mesmo payload) para medir variabilidade intra-modelo."""
from __future__ import annotations
import re, time, json
from pathlib import Path
import requests

BASE = "http://localhost:5001"
TOKEN = "mirofish-inteia-local-2026"
HEADERS = {"X-Internal-Token": TOKEN, "Content-Type": "application/json"}
ROOT = Path(r"C:\Users\IgorPC\.claude\projects\Mirofish INTEIA")
TASK_55_V1 = "fde26412-c521-46cc-898e-48db094eabab"


def now(): return time.strftime("%H:%M:%S")
def log(m):
    print(f"[{now()}] {m}", flush=True)
    with open(ROOT / "compare_v2.log", "a", encoding="utf-8") as f:
        f.write(f"[{now()}] {m}\n")


def wait_task(tid, label, timeout=5400):
    start = time.time(); last = ""
    while time.time() - start < timeout:
        r = requests.get(f"{BASE}/api/internal/v1/tasks/{tid}", headers=HEADERS, timeout=15).json()["data"]
        cur = f"{r.get('status')} {r.get('progress',0)}% {r.get('message','')}"
        if cur != last: log(f"[{label}] {cur}"); last = cur
        if r.get("status") in ("completed", "failed"): return r
        time.sleep(10)
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
            out["markdown"] = rep.get("markdown_content", "")
            out["report_chars"] = len(out["markdown"])
    return out


def analyze(md, dossie):
    if not md: return {"sections":0,"quotes":0,"quotes_grounded":0,"chars":0,"percent_refs":0}
    sections = len(re.findall(r"^## ", md, flags=re.MULTILINE))
    quotes = re.findall(r'"([^"]{15,})"', md)
    grounded = 0
    for q in quotes:
        for s in range(0, max(1, len(q)-20), 10):
            sn = q[s:s+20].strip()
            if len(sn) >= 15 and sn in dossie: grounded += 1; break
    return {"sections":sections,"quotes":len(quotes),"quotes_grounded":grounded,
            "chars":len(md),"percent_refs":len(re.findall(r"\d+\s*%", md))}


def main():
    d1 = Path(r"C:\Users\IgorPC\.hermes\memories\DOSSIE_IGOR_COMPLETO.md").read_text(encoding="utf-8")
    d2 = Path(r"C:\Users\IgorPC\.hermes\memories\DOSSIE_IGOR_VOZ_PROPRIA.md").read_text(encoding="utf-8")
    payload = {
        "name": "Igor Morais - 5.5 run #2 (variabilidade)",
        "simulation_requirement": ("Simular vida de Igor em 7 dias conforme vozes dos dossies. "
                                   "Mapear tensoes (saude, INTEIA, doutorado, Paixao Cortes) e reacoes em redes."),
        "preset": "smoke",
        "materials": [
            {"filename": "DOSSIE_IGOR_COMPLETO.md", "text": d1},
            {"filename": "DOSSIE_IGOR_VOZ_PROPRIA.md", "text": d2},
        ],
        "structured_context": {
            "cenario": "Semana tipica de Igor em Brasilia-DF",
            "territorio": "Distrito Federal",
            "atores": ["Igor Morais","Familia","Paixao Cortes Adv","equipe INTEIA","colegas SEEDF","orientador IDP"],
        },
        "enable_twitter": True, "enable_reddit": True,
    }

    log("Disparando run #2 GPT-5.5...")
    r = requests.post(f"{BASE}/api/internal/v1/run-preset", json=payload, headers=HEADERS, timeout=30)
    r.raise_for_status()
    tid = r.json()["data"]["task_id"]
    log(f"[5.5-v2] task={tid}")
    wait_task(tid, "5.5-v2", timeout=5400)

    v1 = fetch(TASK_55_V1); v1["alias"] = "gpt-5.5 #1"
    v2 = fetch(tid); v2["alias"] = "gpt-5.5 #2"
    dossie = d1 + d2
    a1 = analyze(v1.get("markdown",""), dossie)
    a2 = analyze(v2.get("markdown",""), dossie)

    out = ROOT / "COMPARATIVO_GPT55_v1_vs_v2.md"
    lines = [
        "# Variabilidade GPT-5.5: Run #1 vs Run #2 (mesmo payload, mesmo modelo)\n",
        f"Gerado: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n",
        "Mesmo payload (dossies Igor + preset smoke), mesmo modelo (gpt-5.5 via Codex Pro OAuth).\n",
        "Objetivo: medir variabilidade intra-modelo.\n\n",
        "## Resumo\n\n",
        "| Run | Tempo (s) | Chars | Secoes | Citacoes | Grounded | % refs |\n",
        "|---|---|---|---|---|---|---|\n",
        f"| 5.5 #1 | {v1.get('elapsed_s','?')} | {a1['chars']} | {a1['sections']} | {a1['quotes']} | {a1['quotes_grounded']}/{a1['quotes']} | {a1['percent_refs']} |\n",
        f"| 5.5 #2 | {v2.get('elapsed_s','?')} | {a2['chars']} | {a2['sections']} | {a2['quotes']} | {a2['quotes_grounded']}/{a2['quotes']} | {a2['percent_refs']} |\n\n",
        "## Run #1 (referencia anterior, primeiros 4000 chars)\n\n```markdown\n",
        (v1.get("markdown","")[:4000] or "(vazio)"), "\n```\n\n",
        "## Run #2 (atual via mesmo endpoint UI usa, primeiros 4000 chars)\n\n```markdown\n",
        (v2.get("markdown","")[:4000] or "(vazio)"), "\n```\n",
    ]
    out.write_text("".join(lines), encoding="utf-8")
    (ROOT / f"REL_5.5v2_{tid[:8]}.md").write_text(v2.get("markdown",""), encoding="utf-8")
    log(f"Comparativo v1vs v2 salvo: {out}")


if __name__ == "__main__":
    main()
