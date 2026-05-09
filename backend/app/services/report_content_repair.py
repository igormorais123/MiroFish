"""Reparo deterministico de conteudo de relatorios bloqueados."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..utils.report_quality import audit_report_content_consistency
from .report_agent import ReportManager, ReportStatus


class ReportContentRepairError(Exception):
    """Erro base de reparo de conteudo."""


class ReportContentRepairNotFound(ReportContentRepairError):
    """Relatorio nao encontrado."""


class ReportContentRepairConflict(ReportContentRepairError):
    """Relatorio ainda nao pode ser reparado automaticamente."""


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _artifact(report_id: str, name: str) -> dict[str, Any]:
    payload = ReportManager.load_json_artifact(report_id, name)
    return payload if isinstance(payload, dict) else {}


def _metrics_for_report(report) -> dict[str, Any]:
    system_gate = _artifact(report.report_id, "system_gate.json")
    metrics = system_gate.get("metrics") if isinstance(system_gate, dict) else None
    if isinstance(metrics, dict):
        return metrics

    quality_gate = report.quality_gate or {}
    embedded = quality_gate.get("metrics") if isinstance(quality_gate, dict) else None
    return embedded if isinstance(embedded, dict) else {}


def _positive_int(value: Any) -> int:
    if isinstance(value, bool) or value is None:
        return 0
    if isinstance(value, (int, float)):
        return int(value) if value > 0 else 0
    if isinstance(value, str):
        match = re.search(r"\d+", value)
        if match:
            parsed = int(match.group(0))
            return parsed if parsed > 0 else 0
    return 0


def _known_agents(metrics: dict[str, Any]) -> int:
    for key in ("profiles_count", "state_profiles_count", "total_agents", "agent_count"):
        parsed = _positive_int(metrics.get(key))
        if parsed:
            return parsed
    return 0


def _known_rounds(metrics: dict[str, Any]) -> int:
    for key in ("current_round", "rounds_count", "total_rounds", "max_rounds"):
        parsed = _positive_int(metrics.get(key))
        if parsed:
            return parsed
    return 0


def _known_platforms(metrics: dict[str, Any]) -> list[str]:
    platforms: list[str] = []
    diversity = metrics.get("diversity") if isinstance(metrics.get("diversity"), dict) else {}
    for platform_counts in (metrics.get("platform_counts"), diversity.get("platform_counts")):
        if isinstance(platform_counts, dict):
            for name, count in platform_counts.items():
                if _positive_int(count):
                    platforms.append(str(name))
    if _positive_int(metrics.get("twitter_actions_count")):
        platforms.append("twitter")
    if _positive_int(metrics.get("reddit_actions_count")):
        platforms.append("reddit")

    seen: set[str] = set()
    output: list[str] = []
    for name in platforms:
        normalized = name.strip().lower()
        if normalized and normalized not in seen:
            seen.add(normalized)
            output.append({"twitter": "Twitter", "reddit": "Reddit"}.get(normalized, name.title()))
    return output


def _metrics_sentence(metrics: dict[str, Any]) -> str:
    agents = _known_agents(metrics)
    rounds = _known_rounds(metrics)
    platforms = _known_platforms(metrics)
    parts = []
    if agents:
        parts.append(f"{agents} perfis")
    if rounds:
        parts.append(f"{rounds} rodadas")
    if platforms:
        parts.append("atividade em " + "/".join(platforms))
    if not parts:
        return "metadados estruturados disponíveis"
    return ", ".join(parts)


def _strip_internal_audit_blocks(content: str) -> str:
    return re.sub(
        r"\n---\n\n## QC[\s\S]*$|\n## QC[\s\S]*$",
        "",
        content or "",
        flags=re.IGNORECASE,
    )


def _repair_malformed_table_line(line: str) -> str:
    match = re.match(r"^\[([^\]]+)\]\s*\|\s*(.+)$", line.strip())
    if not match:
        return line

    label = match.group(1).strip()
    parts = [part.strip() for part in match.group(2).strip().strip("|").split("|")]
    if len(parts) >= 4:
        parts[2] = f"[{label}] {parts[2]}".strip()
        return "| " + " | ".join(parts) + " |"
    return "| [" + label + "] " + " | ".join(parts) + " |"


def _normalize_quote(line: str) -> str:
    text = line.strip().lstrip(">").strip().strip("\"'“”")
    return " ".join(re.findall(r"[A-Za-zÀ-ÿ0-9]+", text.lower()))


def repair_report_markdown_content(content: str, metrics: dict[str, Any]) -> str:
    """Limpa apenas problemas determinísticos sem inventar nova analise."""
    metrics_text = _metrics_sentence(metrics)
    repaired = _strip_internal_audit_blocks(content or "")

    repaired = re.sub(
        r"\bpor\s+n[aã]o\s+haver\s+agentes\s+ativos\s+e\s+",
        "",
        repaired,
        flags=re.IGNORECASE,
    )
    repaired = re.sub(
        r"\bn[aã]o\s+h[aá]\s+agentes\s+ativos\s+na\s+base\.?",
        f"há {metrics_text} registrados na base.",
        repaired,
        flags=re.IGNORECASE,
    )
    repaired = re.sub(
        r"A base informada n[aã]o tem agentes, rodadas e plataformas conhecidos\.",
        f"A base informada registra {metrics_text}; o limite relevante e validacao externa antes de uso decisorio amplo.",
        repaired,
        flags=re.IGNORECASE,
    )
    repaired = re.sub(
        r"agentes desconhecidos,\s*rodadas desconhecidas,\s*plataformas desconhecidas",
        metrics_text,
        repaired,
        flags=re.IGNORECASE,
    )
    repaired = re.sub(
        r"quantidade de agentes,\s*",
        "",
        repaired,
        flags=re.IGNORECASE,
    )
    repaired = re.sub(
        r"numero de rodadas,\s*plataformas,\s*",
        "",
        repaired,
        flags=re.IGNORECASE,
    )

    output_lines: list[str] = []
    previous_heading = ""
    seen_blockquotes: set[str] = set()
    for raw_line in repaired.splitlines():
        line = _repair_malformed_table_line(raw_line)
        stripped = line.strip()
        heading_match = re.match(r"^##\s+(.+?)\s*$", stripped)
        if heading_match:
            previous_heading = heading_match.group(1).strip()
            output_lines.append(line)
            continue

        bold_match = re.match(r"^\*\*(.+?)\*\*:?\s*$", stripped)
        if bold_match and previous_heading:
            if bold_match.group(1).strip().lower() == previous_heading.lower():
                previous_heading = ""
                continue

        if stripped.startswith(">"):
            normalized_quote = _normalize_quote(stripped)
            if normalized_quote and normalized_quote in seen_blockquotes:
                continue
            if normalized_quote:
                seen_blockquotes.add(normalized_quote)

        if stripped:
            previous_heading = "" if not heading_match else previous_heading
        output_lines.append(line)

    normalized = "\n".join(output_lines)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized).strip() + "\n"
    return normalized


def _write_sections(report_id: str, metrics: dict[str, Any]) -> int:
    changed = 0
    folder = Path(ReportManager._get_report_folder(report_id))
    for path in sorted(folder.glob("section_*.md")):
        original = path.read_text(encoding="utf-8")
        repaired = repair_report_markdown_content(original, metrics)
        if repaired != original:
            path.write_text(repaired, encoding="utf-8")
            changed += 1
    return changed


def repair_report_content(report_id: str) -> dict[str, Any]:
    """Repara conteudo bloqueado por auditoria editorial sem chamar LLM."""
    report = ReportManager.get_report(report_id)
    if not report:
        raise ReportContentRepairNotFound(f"Relatorio nao encontrado: {report_id}")
    if report.status in {ReportStatus.PENDING, ReportStatus.PLANNING, ReportStatus.GENERATING}:
        raise ReportContentRepairConflict("Relatorio ainda em geracao.")
    if report.status == ReportStatus.FAILED:
        raise ReportContentRepairConflict("Relatorio falhou; gere novamente antes de reparar conteudo.")

    metrics = _metrics_for_report(report)
    before = audit_report_content_consistency(report.markdown_content or "", metrics)
    report_folder = Path(ReportManager._get_report_folder(report_id))
    backup_path = report_folder / "content_repair_backup.md"
    if report.markdown_content and not backup_path.exists():
        backup_path.write_text(report.markdown_content, encoding="utf-8")

    sections_changed = _write_sections(report_id, metrics)

    if report.outline:
        report.outline.summary = repair_report_markdown_content(report.outline.summary or "", metrics).strip()
        report.markdown_content = ReportManager.assemble_full_report(report_id, report.outline)
    else:
        report.markdown_content = repair_report_markdown_content(report.markdown_content or "", metrics)

    report.markdown_content = repair_report_markdown_content(report.markdown_content or "", metrics)
    after = audit_report_content_consistency(report.markdown_content or "", metrics)
    if report.quality_gate is None:
        report.quality_gate = {}
    report.quality_gate["content_consistency"] = after
    if after.get("passes_gate"):
        report.quality_gate["passes_gate"] = True

    ReportManager.save_json_artifact(report_id, "content_consistency.json", after)
    ReportManager.save_report(report)

    result = {
        "schema": "mirofish.report_content_repair.v1",
        "report_id": report_id,
        "status": "repaired" if after.get("passes_gate") else "needs_manual_review",
        "changed": sections_changed > 0 or before != after,
        "repaired_at": _now_iso(),
        "sections_changed": sections_changed,
        "backup_file": "content_repair_backup.md" if backup_path.exists() else None,
        "before": before,
        "after": after,
    }
    ReportManager.save_json_artifact(report_id, "content_repair.json", result)
    return result
