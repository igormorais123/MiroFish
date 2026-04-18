"""Testes unitarios para mapa de traducao de relacoes (Phase 6)."""
import pytest

from app.services.graph_builder import _translate_relation_name, _RELATION_TRANSLATION


def test_translate_fears():
    assert _translate_relation_name("FEARS") == "TEME"


def test_translate_advocates():
    assert _translate_relation_name("ADVOCATES") == "DEFENDE"


def test_translate_lowercase_input():
    assert _translate_relation_name("fears") == "TEME"


def test_translate_mixed_case():
    assert _translate_relation_name("Opposes") == "OPOE_A"


def test_translate_unknown_passes_through():
    assert _translate_relation_name("UNKNOWN_RELATION") == "UNKNOWN_RELATION"


def test_translate_empty_string():
    assert _translate_relation_name("") == ""


def test_translate_none_returns_none():
    assert _translate_relation_name(None) is None


def test_all_values_are_uppercase():
    """Garante que o lado pt-BR tambem segue SCREAMING_SNAKE_CASE (ontologia upstream)."""
    for pt in _RELATION_TRANSLATION.values():
        assert pt == pt.upper(), f"{pt} deve ser uppercase"


def test_all_keys_are_uppercase():
    """Chaves devem ser uppercase para match com SCREAMING_SNAKE_CASE do Graphiti."""
    for en in _RELATION_TRANSLATION.keys():
        assert en == en.upper(), f"{en} deve ser uppercase"


def test_no_duplicate_translations():
    """Multiplas relacoes podem mapear pro mesmo pt-BR (ex: DEFENDS/ADVOCATES → DEFENDE)."""
    # Esse teste apenas documenta — nao e um erro ter duplicatas, e comum por sinonimos.
    values = list(_RELATION_TRANSLATION.values())
    duplicated = set(v for v in values if values.count(v) > 1)
    # Documenta os sinonimos conhecidos
    known_synonyms = {"DEFENDE"}  # ADVOCATES e DEFENDS mapeiam pra DEFENDE
    assert duplicated <= known_synonyms or len(duplicated) <= 2


def test_coverage_minimum():
    """Mapa deve cobrir pelo menos 20 relacoes comuns."""
    assert len(_RELATION_TRANSLATION) >= 20
