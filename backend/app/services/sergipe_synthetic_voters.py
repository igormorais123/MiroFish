"""Carregamento e injecao de eleitores sinteticos de Sergipe."""
from __future__ import annotations

import json
import re
import hashlib
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from ..utils.logger import get_logger
from .zep_entity_reader import EntityNode, FilteredEntities

logger = get_logger("mirofish.sergipe_synthetic_voters")

SERGIPE_SYNTHETIC_VOTER_TYPE = "SyntheticVoterSE"
SERGIPE_SYNTHETIC_VOTER_SOURCE = "sergipe_eleitores_1000_v9"
DEFAULT_SERGIPE_VOTERS_PATH = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "synthetic_voters"
    / "sergipe_eleitores_1000_v9.json"
)

SERGIPE_CONTEXT_MARKERS = (
    "sergipe",
    "sergipano",
    "sergipana",
    "aracaju",
    "itabaiana",
    "lagarto",
    "nossa senhora do socorro",
    "sao cristovao",
    "estancia",
    "tobias barreto",
    "simao dias",
)


@dataclass(frozen=True)
class SergipeAugmentationResult:
    """Resultado auditavel da injecao de eleitores sinteticos."""

    filtered: FilteredEntities
    applied: bool
    added_count: int
    source_path: str


def _normalize_for_match(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value or "")
    normalized = normalized.encode("ascii", "ignore").decode("ascii")
    normalized = normalized.lower()
    return re.sub(r"\s+", " ", normalized)


def is_sergipe_research_context(*texts: str) -> bool:
    """Detecta se o objetivo/documento pede pesquisa com recorte em Sergipe."""

    raw_text = " ".join(text for text in texts if text)
    normalized = _normalize_for_match(raw_text)
    if not normalized:
        return False

    if any(marker in normalized for marker in SERGIPE_CONTEXT_MARKERS):
        return True

    if re.search(r"\bUF\s*[:=\-]?\s*SE\b", raw_text):
        return True
    if re.search(r"\bestado\s+(?:de\s+)?SE\b", raw_text):
        return True
    if re.search(r"\bSE\b", raw_text):
        return bool(
            re.search(
                r"\b(pesquisa|eleitor|eleitoral|voto|governo|prefeitura|senado|deputado)\w*",
                normalized,
            )
        )

    return False


class SergipeSyntheticVoterRepository:
    """Repositorio da populacao sintetica de Sergipe embutida no MiroFish."""

    def __init__(
        self,
        data_path: str | Path | None = None,
        voters: Iterable[dict[str, Any]] | None = None,
    ) -> None:
        self.data_path = Path(data_path) if data_path is not None else DEFAULT_SERGIPE_VOTERS_PATH
        self._voters = list(voters) if voters is not None else None

    def load_raw_voters(self) -> list[dict[str, Any]]:
        if self._voters is not None:
            return [dict(voter) for voter in self._voters]

        if not self.data_path.exists():
            logger.warning("Base de eleitores sinteticos de Sergipe nao encontrada: %s", self.data_path)
            return []

        try:
            with self.data_path.open("r", encoding="utf-8") as f:
                parsed = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("Falha ao carregar eleitores sinteticos de Sergipe: %s", exc)
            return []

        if isinstance(parsed, dict):
            for key in ("eleitores", "voters", "population", "items"):
                value = parsed.get(key)
                if isinstance(value, list):
                    return [v for v in value if isinstance(v, dict)]
            return [parsed]
        if isinstance(parsed, list):
            return [v for v in parsed if isinstance(v, dict)]
        return []

    def load_entities(self, limit: int | None = None) -> list[EntityNode]:
        voters = self.load_raw_voters()
        if limit is not None:
            voters = voters[: max(0, int(limit))]
        return [self._to_entity(voter) for voter in voters]

    def _to_entity(self, voter: dict[str, Any]) -> EntityNode:
        voter_id = str(voter.get("id") or "").strip()
        if voter_id:
            uuid = f"sergipe-voter-{voter_id}"
        else:
            digest = hashlib.sha1(
                json.dumps(voter, sort_keys=True, ensure_ascii=False).encode("utf-8")
            ).hexdigest()[:12]
            uuid = f"sergipe-voter-{digest}"
        attributes = dict(voter)
        attributes["synthetic_voter_source"] = SERGIPE_SYNTHETIC_VOTER_SOURCE
        attributes["synthetic_voter_state"] = "SE"
        attributes["synthetic_voter_kind"] = "state_electorate_persona"

        return EntityNode(
            uuid=uuid,
            name=str(voter.get("nome") or voter_id or uuid),
            labels=["Entity", SERGIPE_SYNTHETIC_VOTER_TYPE],
            summary=self._build_summary(voter),
            attributes=attributes,
            related_edges=[],
            related_nodes=[],
        )

    @staticmethod
    def _as_text_list(value: Any) -> str:
        if isinstance(value, list):
            return ", ".join(str(item) for item in value if item is not None)
        if isinstance(value, dict):
            return ", ".join(f"{key}: {item}" for key, item in value.items())
        return str(value or "")

    def _build_summary(self, voter: dict[str, Any]) -> str:
        name = voter.get("nome") or voter.get("id") or "Eleitor sintetico"
        municipality = voter.get("municipio") or "municipio nao informado"
        mesoregion = voter.get("mesorregiao") or "regiao nao informada"
        age = voter.get("idade")
        gender = voter.get("genero")
        zone = voter.get("zona_residencia")
        class_name = voter.get("classe_social") or voter.get("cluster_socioeconomico")
        profession = voter.get("profissao")
        religion = voter.get("religiao")
        concerns = self._as_text_list(voter.get("preocupacoes"))
        media = self._as_text_list(voter.get("fontes_informacao"))
        vote_2022 = voter.get("voto_2t_2022")
        vote_gov = voter.get("intencao_voto_2026_gov")
        vote_pres = voter.get("intencao_voto_2026_pres")
        story = voter.get("historia_resumida")

        parts = [
            f"{name}, eleitor(a) sintetico(a) de {municipality}, {mesoregion}, Sergipe.",
        ]
        if age or gender:
            parts.append(f"Demografia: {age or 'idade nao informada'} anos, genero {gender or 'nao informado'}.")
        if zone or class_name or profession or religion:
            parts.append(
                "Perfil social: "
                f"zona {zone or 'nao informada'}, classe {class_name or 'nao informada'}, "
                f"profissao {profession or 'nao informada'}, religiao {religion or 'nao informada'}."
            )
        if concerns:
            parts.append(f"Preocupacoes: {concerns}.")
        if media:
            parts.append(f"Fontes de informacao: {media}.")
        if vote_2022 or vote_gov or vote_pres:
            parts.append(
                "Ancoras eleitorais: "
                f"2T 2022={vote_2022 or 'nao informado'}, "
                f"governo 2026={vote_gov or 'nao informado'}, "
                f"presidencia 2026={vote_pres or 'nao informado'}."
            )
        if story:
            parts.append(str(story))

        return " ".join(parts)


def augment_entities_for_sergipe_context(
    filtered: FilteredEntities,
    *,
    simulation_requirement: str,
    document_text: str,
    repository: SergipeSyntheticVoterRepository | None = None,
    limit: int | None = None,
) -> SergipeAugmentationResult:
    """Inclui eleitores sinteticos quando a pesquisa tiver recorte sergipano."""

    repository = repository or SergipeSyntheticVoterRepository()
    if not is_sergipe_research_context(simulation_requirement, document_text):
        return SergipeAugmentationResult(
            filtered=filtered,
            applied=False,
            added_count=0,
            source_path=str(repository.data_path),
        )

    existing_uuids = {entity.uuid for entity in filtered.entities}
    existing_names = {_normalize_for_match(entity.name) for entity in filtered.entities}
    synthetic_entities = []
    for entity in repository.load_entities(limit=limit):
        normalized_name = _normalize_for_match(entity.name)
        if entity.uuid in existing_uuids or normalized_name in existing_names:
            continue
        synthetic_entities.append(entity)
        existing_uuids.add(entity.uuid)
        existing_names.add(normalized_name)

    entity_types = set(filtered.entity_types)
    if synthetic_entities or any(
        entity.get_entity_type() == SERGIPE_SYNTHETIC_VOTER_TYPE for entity in filtered.entities
    ):
        entity_types.add(SERGIPE_SYNTHETIC_VOTER_TYPE)

    augmented = FilteredEntities(
        entities=[*filtered.entities, *synthetic_entities],
        entity_types=entity_types,
        total_count=filtered.total_count + len(synthetic_entities),
        filtered_count=len(filtered.entities) + len(synthetic_entities),
    )

    logger.info(
        "Contexto de Sergipe detectado; eleitores sinteticos adicionados: %s",
        len(synthetic_entities),
    )
    return SergipeAugmentationResult(
        filtered=augmented,
        applied=True,
        added_count=len(synthetic_entities),
        source_path=str(repository.data_path),
    )
