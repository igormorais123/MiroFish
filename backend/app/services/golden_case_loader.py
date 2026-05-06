"""Carregador defensivo para pacote de caso de ouro."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


class GoldenCaseLoader:
    """Le um pacote de caso de ouro a partir de um caminho injetado."""

    MANIFEST_NAME_RE = re.compile(r"manifesto", re.IGNORECASE)
    PROMPT_NAME_RE = re.compile(r"(prompt|simulacao|simula[cç][aã]o)", re.IGNORECASE)
    ANALYSIS_NAME_RE = re.compile(
        r"(analise|an[aá]lise|analysis|estrategic|estrat[eé]gica)",
        re.IGNORECASE,
    )
    DECLARED_COUNT_RE = re.compile(
        r"(?:total|quantidade|qtd|contagem)\D{0,40}documentos?\D{0,20}(\d{1,4})"
        r"|(?:total|quantidade|qtd|contagem)\D{0,20}(\d{1,4})\D{0,20}documentos?"
        r"|^\s*(\d{1,4})\s+documentos?\b",
        re.IGNORECASE,
    )

    def __init__(self, base_path: str | Path):
        self.base_path = Path(base_path)

    def load_summary(self) -> dict[str, Any]:
        """Retorna resumo do pacote em campos estaveis para auditoria local."""
        manifesto_path = self._find_manifesto()
        json_path = self.base_path / "documentos_principais.json"
        markdown_paths = self._list_files("*.md")
        pdf_paths = self._list_files("*.pdf")

        manifesto_text = self._read_text(manifesto_path)
        declared_documents = self._extract_declared_documents(manifesto_text)
        indexed_documents = self._count_indexed_documents(json_path)
        mismatch = (
            declared_documents is not None
            and indexed_documents is not None
            and declared_documents != indexed_documents
        )

        return {
            "case_id": self.base_path.name,
            "manifesto_path": str(manifesto_path) if manifesto_path else None,
            "declared_documents": declared_documents,
            "indexed_documents": indexed_documents,
            "mismatch": mismatch,
            "pdf_count": len(pdf_paths),
            "markdown_count": len(markdown_paths),
            "key_files": self._key_files(manifesto_path, json_path),
        }

    def build_quality_fixture(self) -> dict[str, Any]:
        """Monta fixture curta para testes de qualidade e regressao."""
        summary = self.load_summary()
        manifesto_path = Path(summary["manifesto_path"]) if summary["manifesto_path"] else None
        markdown_paths = self._list_files("*.md")
        prompt_path = self._find_named_markdown(self.PROMPT_NAME_RE, exclude=manifesto_path)
        analysis_path = self._find_named_markdown(self.ANALYSIS_NAME_RE, exclude=manifesto_path)

        evidence_texts: list[str] = []
        for path in [manifesto_path, *markdown_paths]:
            if path and path.exists() and path not in [prompt_path, analysis_path]:
                snippet = self._snippet(self._read_text(path))
                if snippet and snippet not in evidence_texts:
                    evidence_texts.append(snippet)
            if len(evidence_texts) >= 5:
                break

        return {
            "summary": summary,
            "evidence_texts": evidence_texts,
            "simulation_prompt": self._optional_full_text(prompt_path),
            "strategic_analysis": self._optional_full_text(analysis_path),
        }

    def load_inventory(self) -> dict[str, list[str] | str | None | list[dict[str, Any]]]:
        """Carrega manifesto, JSON e listas de arquivos existentes."""
        manifesto_path = self._find_manifesto()
        json_path = self.base_path / "documentos_principais.json"
        return {
            "manifesto_path": str(manifesto_path) if manifesto_path else None,
            "manifesto_text": self._read_text(manifesto_path),
            "indexed_documents": self._load_indexed_documents(json_path),
            "pdf_files": [self._relative(path) for path in self._list_files("*.pdf")],
            "markdown_files": [self._relative(path) for path in self._list_files("*.md")],
        }

    def _list_files(self, pattern: str) -> list[Path]:
        if not self.base_path.exists() or not self.base_path.is_dir():
            return []
        return sorted(path for path in self.base_path.rglob(pattern) if path.is_file())

    def _find_manifesto(self) -> Path | None:
        markdown_paths = self._list_files("*.md")
        for path in markdown_paths:
            if self.MANIFEST_NAME_RE.search(path.name):
                return path
        return markdown_paths[0] if markdown_paths else None

    def _find_named_markdown(self, pattern: re.Pattern[str], exclude: Path | None = None) -> Path | None:
        for path in self._list_files("*.md"):
            if exclude and path == exclude:
                continue
            if pattern.search(path.name):
                return path
        return None

    def _count_indexed_documents(self, json_path: Path) -> int | None:
        documents = self._load_indexed_documents(json_path)
        return len(documents) if documents is not None else None

    def _load_indexed_documents(self, json_path: Path) -> list[dict[str, Any]] | None:
        if not json_path.exists() or not json_path.is_file():
            return None
        try:
            data = json.loads(json_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, UnicodeDecodeError):
            return None

        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
        if isinstance(data, dict):
            for key in ("documentos", "documents", "items", "entries"):
                value = data.get(key)
                if isinstance(value, list):
                    return [item for item in value if isinstance(item, dict)]
        return None

    def _extract_declared_documents(self, manifesto_text: str) -> int | None:
        if not manifesto_text:
            return None

        for line in manifesto_text.splitlines():
            explicit = self.DECLARED_COUNT_RE.search(line)
            if explicit:
                number = next(group for group in explicit.groups() if group)
                return int(number)

        table_rows = [
            line
            for line in manifesto_text.splitlines()
            if re.match(r"^\|\s*\d+\s*\|", line)
        ]
        return len(table_rows) if table_rows else None

    def _key_files(self, manifesto_path: Path | None, json_path: Path) -> list[str]:
        paths: list[Path] = []
        if manifesto_path:
            paths.append(manifesto_path)
        if json_path.exists() and json_path.is_file():
            paths.append(json_path)

        for pattern in (self.PROMPT_NAME_RE, self.ANALYSIS_NAME_RE):
            path = self._find_named_markdown(pattern, exclude=manifesto_path)
            if path:
                paths.append(path)

        key_files: list[str] = []
        for path in paths:
            rel = self._relative(path)
            if rel not in key_files:
                key_files.append(rel)
        return key_files

    def _relative(self, path: Path) -> str:
        try:
            return path.relative_to(self.base_path).as_posix()
        except ValueError:
            return path.name

    def _read_text(self, path: Path | None) -> str:
        if not path or not path.exists() or not path.is_file():
            return ""
        try:
            return path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return ""

    def _optional_full_text(self, path: Path | None) -> str | None:
        text = self._read_text(path)
        return text.strip() if text.strip() else None

    def _snippet(self, text: str, limit: int = 600) -> str:
        normalized = re.sub(r"\s+", " ", text).strip()
        if not normalized:
            return ""
        return normalized[:limit]
