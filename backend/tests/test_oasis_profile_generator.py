"""Testes de contrato comportamental nos perfis OASIS."""
from __future__ import annotations

from app.services.oasis_profile_generator import OasisAgentProfile, OasisProfileGenerator


def test_social_behavior_contract_orienta_interacao_sem_duplicar():
    profile = OasisAgentProfile(
        user_id=1,
        user_name="ana",
        name="Ana",
        bio="Perfil publico.",
        persona="Pessoa critica e participativa.",
    )
    generator = object.__new__(OasisProfileGenerator)

    text = generator._append_social_behavior_contract(profile.persona, profile)
    text_again = generator._append_social_behavior_contract(text, profile)

    assert "CREATE_COMMENT" in text
    assert "LIKE_POST" in text
    assert "REPOST" in text
    assert text_again.count("Contrato de simulacao social:") == 1
