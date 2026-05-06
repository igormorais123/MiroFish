"""Catalogo seguro de poderes e personas externas para INTEIA."""
from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import unicodedata
from pathlib import Path
from typing import Any, Iterable

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover - ambiente sem PyYAML
    yaml = None


CatalogItem = dict[str, Any]


class PowerPersonaCatalog:
    """Indexa arquivos pequenos de fontes externas sem acoplar seus sistemas."""

    ENV_ROOTS_KEY = "MIROFISH_PERSONA_ROOTS"
    DEFAULT_ROOTS = (
        Path(r"C:\Users\IgorPC\voxsintetica-platform"),
        Path(r"C:\Users\IgorPC\.hermes"),
        Path(r"C:\Users\IgorPC\.claude\projects\C--Agentes-vila-inteia"),
        Path(r"C:\Users\IgorPC\.claude\projects\Proposta reestruturação INTEIA\v2_HELENA_MEGAPOWER"),
    )
    SUPPORTED_EXTENSIONS = {".json", ".jsonl", ".csv", ".md", ".markdown", ".yaml", ".yml"}
    IGNORED_DIRS = {
        ".git",
        ".venv",
        "__pycache__",
        "backups",
        "backup",
        "dist",
        "node_modules",
        "venv",
    }
    DEFAULT_MAX_FILES = 250
    DEFAULT_MAX_FILE_SIZE = 128 * 1024
    DEFAULT_CONTEXT_LIMIT = 4000
    TYPE_ORDER = {
        "persona_sintetica": 0,
        "consultor_lendario": 1,
        "populacao": 2,
        "poder_previsao": 3,
    }

    TYPE_KEYWORDS = (
        (
            "persona_sintetica",
            ("vox", "persona sintetica", "personas sinteticas", "synthetic persona"),
        ),
        (
            "populacao",
            ("eleitor", "eleitores", "populacao", "populacao", "population"),
        ),
        (
            "consultor_lendario",
            ("cicero", "helena", "oracle", "midas", "iris", "conselho", "consultor", "lendario"),
        ),
        (
            "poder_previsao",
            (
                "poder",
                "preditivo",
                "previsao",
                "previsao",
                "harness",
                "teoria jogos",
                "teoria dos jogos",
                "persuasao",
            ),
        ),
    )

    NAME_KEYS = ("nome", "name", "title", "titulo", "role", "papel", "id")
    SUMMARY_KEYS = (
        "resumo",
        "bio",
        "description",
        "descricao",
        "descrição",
        "summary",
        "prompt",
        "system",
        "papel",
        "role",
        "content",
        "text",
    )
    INFERENCE_KEYS = (
        "description",
        "resumo",
        "bio",
        "summary",
        "prompt",
        "system",
        "descricao",
        "descrição",
        "papel",
        "role",
        "content",
        "text",
    )

    def __init__(
        self,
        roots: Iterable[str | Path] | None = None,
        max_files: int = DEFAULT_MAX_FILES,
        max_file_size: int = DEFAULT_MAX_FILE_SIZE,
    ) -> None:
        source_roots = roots if roots is not None else self.default_roots()
        self.roots = tuple(Path(root) for root in source_roots)
        self.max_files = max(0, int(max_files))
        self.max_file_size = max(1, int(max_file_size))

    @classmethod
    def default_roots(cls) -> tuple[Path, ...]:
        configured = os.environ.get(cls.ENV_ROOTS_KEY, "").strip()
        if not configured:
            return cls.DEFAULT_ROOTS

        roots = tuple(
            Path(part.strip())
            for part in configured.split(os.pathsep)
            if part.strip()
        )
        return roots or cls.DEFAULT_ROOTS

    def build_catalog(self) -> list[CatalogItem]:
        items: list[CatalogItem] = []
        seen_paths: set[str] = set()
        scanned = 0

        for root in self.roots:
            if scanned >= self.max_files:
                break
            if not root.exists():
                continue
            for path in self._iter_candidate_files(root):
                if scanned >= self.max_files:
                    break
                resolved = str(path.resolve())
                if resolved in seen_paths:
                    continue
                seen_paths.add(resolved)
                if not self._is_small_supported_file(path):
                    continue
                scanned += 1
                items.extend(self._items_from_file(path, root))

        return self._dedupe_and_sort(items)

    def select_items(
        self,
        catalog: Iterable[CatalogItem],
        selected_ids: Iterable[str],
        tipo: str | None = None,
    ) -> list[CatalogItem]:
        selected = {str(item_id) for item_id in selected_ids}
        if not selected:
            return []
        result = [
            item
            for item in catalog
            if str(item.get("id")) in selected and (tipo is None or item.get("tipo") == tipo)
        ]
        return sorted(result, key=self._sort_key)

    def build_context_pack(
        self,
        selected_items: Iterable[CatalogItem],
        max_chars: int = DEFAULT_CONTEXT_LIMIT,
    ) -> str:
        max_chars = max(0, int(max_chars))
        if max_chars == 0:
            return ""

        header = "Contexto selecionado de poderes e personas:"
        if len(header) >= max_chars:
            return header[:max_chars]

        parts = [header]
        current_len = len(header)
        for item in selected_items:
            markers = ", ".join(str(marker) for marker in item.get("marcadores", [])[:5])
            line = (
                f"- {item.get('nome', 'Sem nome')} [{item.get('tipo', 'sem_tipo')}]: "
                f"{item.get('resumo', '')}"
            ).strip()
            if markers:
                line += f" Marcadores: {markers}."
            addition = "\n" + line
            if current_len + len(addition) > max_chars:
                remaining = max_chars - current_len
                if remaining >= 3:
                    parts.append(addition[: max(0, remaining - 3)].rstrip() + "...")
                elif remaining > 0:
                    parts.append(addition[:remaining])
                break
            parts.append(addition)
            current_len += len(addition)

        return "".join(parts)[:max_chars]

    def _iter_candidate_files(self, root: Path) -> Iterable[Path]:
        stack = [root]
        yielded = 0
        while stack:
            if yielded >= self.max_files:
                return
            current = stack.pop()
            try:
                children = current.iterdir()
            except OSError:
                continue
            for child in children:
                if child.is_dir():
                    if child.name.lower() not in self.IGNORED_DIRS:
                        stack.append(child)
                    continue
                if not self._is_small_supported_file(child):
                    continue
                if yielded >= self.max_files:
                    return
                yielded += 1
                yield child

    def _is_small_supported_file(self, path: Path) -> bool:
        if path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            return False
        try:
            return path.stat().st_size <= self.max_file_size
        except OSError:
            return False

    def _items_from_file(self, path: Path, root: Path) -> list[CatalogItem]:
        text = self._read_text(path)
        if not text:
            return []

        records = self._parse_records(path, text)
        items = []
        for index, record in enumerate(records):
            item = self._normalize_record(record, path, root, index, text)
            if item:
                items.append(item)
        return items

    def _read_text(self, path: Path) -> str:
        try:
            return path.read_text(encoding="utf-8", errors="replace")[: self.max_file_size]
        except OSError:
            return ""

    def _parse_records(self, path: Path, text: str) -> list[Any]:
        suffix = path.suffix.lower()
        if suffix == ".json":
            return self._parse_json(text)
        if suffix == ".jsonl":
            return self._parse_jsonl(text)
        if suffix == ".csv":
            return self._parse_csv(text)
        if suffix in {".yaml", ".yml"} and yaml is not None:
            parsed = self._safe_yaml(text)
            return self._records_from_parsed(parsed) or [text]
        return [self._parse_markdown(text) if suffix in {".md", ".markdown"} else text]

    def _parse_json(self, text: str) -> list[Any]:
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            return [text]
        return self._records_from_parsed(parsed) or [parsed]

    def _parse_jsonl(self, text: str) -> list[Any]:
        records = []
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                records.append(line)
        return records or [text]

    def _parse_csv(self, text: str) -> list[Any]:
        try:
            return list(csv.DictReader(text.splitlines())) or [text]
        except csv.Error:
            return [text]

    def _safe_yaml(self, text: str) -> Any:
        try:
            return yaml.safe_load(text)  # type: ignore[union-attr]
        except Exception:
            return text

    def _records_from_parsed(self, parsed: Any) -> list[Any]:
        if isinstance(parsed, list):
            return parsed
        if isinstance(parsed, dict):
            for key in ("items", "personas", "poderes", "consultores", "populacoes", "agents"):
                value = parsed.get(key)
                if isinstance(value, list):
                    return value
            return [parsed]
        return []

    def _parse_markdown(self, text: str) -> dict[str, str]:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        title = ""
        for line in lines:
            if line.startswith("#"):
                title = line.lstrip("#").strip()
                break
        if not title and lines:
            title = lines[0][:120]
        body_lines = [line.lstrip("#").strip() for line in lines if not line.startswith("---")]
        return {"nome": title, "resumo": " ".join(body_lines[:5])}

    def _normalize_record(
        self,
        record: Any,
        path: Path,
        root: Path,
        index: int,
        file_text: str,
    ) -> CatalogItem | None:
        data = record if isinstance(record, dict) else {"resumo": str(record)}
        haystack = " ".join(
            [
                str(path),
                path.stem,
                str(data.get("tipo", "")),
                str(data.get("nome", "")),
                str(data.get("name", "")),
                str(data.get("title", "")),
                self._all_values(data, self.INFERENCE_KEYS),
            ]
        )
        tipo = self._infer_type(haystack)
        if tipo is None:
            return None

        nome = self._first_value(data, self.NAME_KEYS) or path.stem.replace("_", " ").replace("-", " ")
        resumo = self._first_value(data, self.SUMMARY_KEYS) or self._text_excerpt(file_text)
        marcador_source = f"{path.name} {nome} {resumo}"
        markers = self._extract_markers(marcador_source)
        origem = self._relative_or_name(path, root)
        item_id = self._make_id(tipo, nome, path, index)

        return {
            "id": item_id,
            "nome": self._clean_text(nome, 120),
            "tipo": tipo,
            "fonte": root.name or str(root),
            "origem": origem,
            "resumo": self._clean_text(resumo, 500),
            "marcadores": markers,
            "caminho": str(path.resolve()),
        }

    def _infer_type(self, value: str) -> str | None:
        normalized = self._normalize_for_match(value)
        for tipo, keywords in self.TYPE_KEYWORDS:
            if any(keyword in normalized for keyword in keywords):
                return tipo
        return None

    def _first_value(self, data: dict[str, Any], keys: Iterable[str]) -> str:
        for key in keys:
            value = data.get(key)
            if value is None:
                continue
            if isinstance(value, (list, tuple)):
                value = ", ".join(str(item) for item in value[:5])
            elif isinstance(value, dict):
                value = json.dumps(value, ensure_ascii=False)
            value = str(value).strip()
            if value:
                return value
        return ""

    def _all_values(self, data: dict[str, Any], keys: Iterable[str]) -> str:
        values = []
        for key in keys:
            value = data.get(key)
            if value is None:
                continue
            if isinstance(value, (list, tuple)):
                value = ", ".join(str(item) for item in value[:5])
            elif isinstance(value, dict):
                value = json.dumps(value, ensure_ascii=False)
            value = str(value).strip()
            if value:
                values.append(value)
        return " ".join(values)

    def _text_excerpt(self, text: str) -> str:
        lines = [line.strip(" #-") for line in text.splitlines() if line.strip()]
        return " ".join(lines[:5])

    def _extract_markers(self, value: str) -> list[str]:
        normalized = self._normalize_for_match(value)
        markers: list[str] = []
        for _, keywords in self.TYPE_KEYWORDS:
            for keyword in keywords:
                if keyword in normalized and keyword not in markers:
                    markers.append(keyword)
        return markers[:8]

    def _dedupe_and_sort(self, items: Iterable[CatalogItem]) -> list[CatalogItem]:
        seen: set[tuple[str, str]] = set()
        deduped: list[CatalogItem] = []
        for item in items:
            key = (str(item.get("caminho")), self._normalize_for_match(str(item.get("nome", ""))))
            if key in seen:
                continue
            seen.add(key)
            deduped.append(item)
        return sorted(deduped, key=self._sort_key)

    def _sort_key(self, item: CatalogItem) -> tuple[int, str]:
        tipo = str(item.get("tipo", ""))
        return (self.TYPE_ORDER.get(tipo, 99), str(item.get("nome", "")).lower())

    def _make_id(self, tipo: str, nome: str, path: Path, index: int) -> str:
        digest = hashlib.sha1(f"{path.resolve()}:{index}:{nome}".encode("utf-8")).hexdigest()[:10]
        slug = re.sub(r"[^a-z0-9]+", "-", self._normalize_for_match(nome)).strip("-")[:40]
        return f"{tipo}:{slug or 'item'}:{digest}"

    def _relative_or_name(self, path: Path, root: Path) -> str:
        try:
            return str(path.relative_to(root))
        except ValueError:
            return path.name

    def _clean_text(self, value: Any, limit: int) -> str:
        text = re.sub(r"\s+", " ", str(value)).strip()
        if len(text) <= limit:
            return text
        return text[: max(0, limit - 3)].rstrip() + "..."

    def _normalize_for_match(self, value: str) -> str:
        normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
        normalized = normalized.lower().replace("_", " ").replace("-", " ")
        return re.sub(r"\s+", " ", normalized)
