"""
Órgão real não vira perfil que emite falas sintéticas.

No caso Vale Trading os agentes se chamavam "União", "Contadoria Judicial" e
"13ª Vara Federal de Porto Alegre/RS". Fala gerada por modelo, atribuída a
juízo federal e persistida em banco, é passivo assim que qualquer artefato sai
da máquina.
"""

import pytest

from app.services import entity_naming as en


# --- os nomes exatos do caso que originou a regra ---

@pytest.mark.parametrize("nome,papel", [
    ("13ª Vara Federal de Porto Alegre/RS", "Juízo de primeiro grau"),
    ("União", "Parte pública"),
    ("Contadoria Judicial", "Auxiliar técnico do juízo"),
    ("TRF4", "Tribunal de segundo grau"),
])
def test_orgaos_do_caso_viram_papel_funcional(nome, papel):
    assert en.nome_publico(nome) == papel


def test_papel_processual_e_preservado():
    """A deliberação precisa do papel; é a identificação nominal que sai."""
    assert en.papel_institucional("2ª Vara Cível de Santos") == "Juízo de primeiro grau"
    assert en.papel_institucional("Procuradoria-Geral da Fazenda Nacional") == (
        "Representação judicial da parte pública"
    )
    assert en.papel_institucional("Ministério Público Federal") == "Ministério Público"


@pytest.mark.parametrize("nome", [
    "Vale Trading S.A.",
    "Pedro Leite",
    "Crédito-Prêmio de IPI",
    "Lei 14.791",
])
def test_pessoa_e_empresa_privada_mantem_o_nome(nome):
    """O problema é atribuir fala a órgão público, não a qualquer entidade."""
    assert en.nome_publico(nome) == nome
    assert en.is_institucional(nome) is False


def test_agentes_no_mesmo_papel_sao_distinguidos_por_ordinal():
    assert en.nome_publico("1ª Vara Federal", ordinal=1) == "Juízo de primeiro grau"
    assert en.nome_publico("2ª Vara Federal", ordinal=2) == "Juízo de primeiro grau 2"


def test_ordinal_nao_afeta_entidade_privada():
    assert en.nome_publico("Vale Trading S.A.", ordinal=3) == "Vale Trading S.A."


def test_handle_deriva_do_nome_neutralizado():
    """Um handle como @13a_vara_federal_412 reintroduziria a identificação."""
    exibido = en.nome_publico("13ª Vara Federal de Porto Alegre/RS")
    handle = en.username_publico(exibido, 412)

    assert handle == "ju_zo_de_primeiro_grau_412"
    assert "vara" not in handle
    assert "porto" not in handle


def test_nome_vazio_nao_quebra():
    assert en.papel_institucional("") is None
    assert en.papel_institucional("   ") is None
    assert en.nome_publico("") == ""


def test_corte_superior_antes_de_orgao_colegiado():
    """A ordem dos padrões importa: o mais específico precisa vencer."""
    assert en.papel_institucional("Superior Tribunal de Justiça") == "Corte superior"
    assert en.papel_institucional("Supremo Tribunal Federal") == "Corte constitucional"
