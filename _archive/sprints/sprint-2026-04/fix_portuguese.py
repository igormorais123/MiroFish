"""Fix MiroFish para forçar português brasileiro em todo o sistema."""
import sys
import re

def patch_file(filepath, patches):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    for old, new, desc in patches:
        if old in content:
            content = content.replace(old, new, 1)
            print(f"  OK: {desc}")
        else:
            print(f"  SKIP: {desc} (not found)")
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)


def main():
    base = sys.argv[1] if len(sys.argv) > 1 else "/app/backend"

    # ============================================================
    # 1. PATCH zep_tools.py — traduzir facts para PT-BR
    # ============================================================
    print("PATCH 1: zep_tools.py — traduzir facts para PT-BR")

    zep_path = f"{base}/app/services/zep_tools.py"
    with open(zep_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Adicionar função de tradução simples no início do arquivo
    translate_func = '''
# === Tradução de facts para PT-BR ===
_ENGLISH_MARKERS = [
    'the ', 'is ', 'are ', 'was ', 'has ', 'with ', 'for ', 'and ',
    'that ', 'this ', 'supports', 'opposes', 'competes', 'represents',
    'advocates', 'projects', 'fears', 'implements', 'presides',
    'plans ', 'generates', 'provides', 'discusses',
]

def _is_english(text: str) -> bool:
    """Detecta se texto está em inglês."""
    if not text or len(text) < 15:
        return False
    lower = text.lower()
    return sum(1 for m in _ENGLISH_MARKERS if m in lower) >= 2

def _translate_fact_to_ptbr(fact: str) -> str:
    """Traduz fact do Graphiti para PT-BR usando LLM barato."""
    if not _is_english(fact):
        return fact
    try:
        from ..utils.llm_client import LLMClient
        client = LLMClient()
        result = client.chat(
            messages=[
                {"role": "system", "content": "Traduza o texto abaixo para português brasileiro. Retorne APENAS a tradução, sem explicações."},
                {"role": "user", "content": fact},
            ],
            temperature=0.1,
            max_tokens=500,
        )
        return result.strip() if result else fact
    except Exception:
        return fact

def _translate_facts_batch(facts: list) -> list:
    """Traduz lista de facts para PT-BR."""
    return [_translate_fact_to_ptbr(f) if isinstance(f, str) else f for f in facts]

'''

    # Inserir após os imports
    if '_translate_fact_to_ptbr' not in content:
        # Encontrar onde inserir (após os dataclass imports)
        insert_point = content.find('\n@dataclass')
        if insert_point > 0:
            content = content[:insert_point] + translate_func + content[insert_point:]
            print("  OK: Adicionada função de tradução")
        else:
            print("  WARN: Ponto de inserção não encontrado")
    else:
        print("  SKIP: Tradução já existe")

    # Patch SearchResult.to_text para traduzir facts
    content = content.replace(
        '''    def to_text(self) -> str:
        """Formata resultado de busca como texto legivel."""
        text_parts = []
        if self.facts:
            text_parts.append("Fatos encontrados:")
            for i, fact in enumerate(self.facts, 1):
                text_parts.append(f"{i}. {fact}")''',
        '''    def to_text(self) -> str:
        """Formata resultado de busca como texto legivel."""
        text_parts = []
        if self.facts:
            text_parts.append("Fatos encontrados:")
            translated = _translate_facts_batch(self.facts)
            for i, fact in enumerate(translated, 1):
                text_parts.append(f"{i}. {fact}")''',
    )
    print("  OK: SearchResult.to_text traduz facts")

    with open(zep_path, 'w', encoding='utf-8') as f:
        f.write(content)

    # ============================================================
    # 2. PATCH report_agent.py — reforçar PT-BR nas citações
    # ============================================================
    print("\nPATCH 2: report_agent.py — reforçar PT-BR nas citações")

    report_path = f"{base}/app/services/report_agent.py"
    patches = [
        # Reforçar no prompt da seção
        (
            '3. [Consistencia linguistica - Citacoes devem ser traduzidas para o idioma do relatorio]',
            '3. [REGRA ABSOLUTA - TUDO EM PORTUGUES BRASILEIRO - SEM EXCECAO]',
            "Reforçar título regra 3"
        ),
        (
            '   - Ao citar conteudo em outros idiomas, traduza primeiro para o idioma do relatorio mantendo o sentido original',
            '   - NUNCA inclua citacoes em ingles no relatorio. SEMPRE traduza para portugues antes de citar\n   - Se a ferramenta retornar "Governor advocates for..." voce DEVE traduzir para "O governador defende..."',
            "Reforçar tradução obrigatória"
        ),
        (
            '   - Esta regra se aplica tanto ao texto principal quanto ao conteudo nos blocos de citacao (formato >)',
            '   - TODAS as citacoes no formato > DEVEM estar em portugues do Brasil. Ingles = erro grave\n   - Traduza nomes de relacoes: FEARS→TEME, PROJECTS→PROJETA, ADVOCATES→DEFENDE, IMPLEMENTS→IMPLEMENTA, PRESIDES→PRESIDE',
            "Exemplos de tradução"
        ),
    ]
    patch_file(report_path, patches)

    # ============================================================
    # 3. PATCH simulation_config_generator.py — PT-BR nos prompts
    # ============================================================
    print("\nPATCH 3: simulation_config_generator.py — PT-BR reforçado")

    sim_config_path = f"{base}/app/services/simulation_config_generator.py"
    with open(sim_config_path, 'r', encoding='utf-8') as f:
        sim_content = f.read()

    # Verificar se já tem instrução de PT-BR
    if 'IMPORTANTE: Todas as respostas' in sim_content:
        print("  SKIP: Já tem instrução PT-BR")
    else:
        sim_content = sim_content.replace(
            'IMPORTANTE: Todas as respostas, análises e conteúdos gerados devem ser em português brasileiro.',
            'IMPORTANTE E INVIOLAVEL: Todas as respostas, analises, perfis, descricoes, postagens e conteudos gerados devem ser EXCLUSIVAMENTE em portugues brasileiro. NUNCA gere texto em ingles.',
        )
        with open(sim_config_path, 'w', encoding='utf-8') as f:
            f.write(sim_content)
        print("  OK: Reforçado PT-BR")

    # ============================================================
    # 4. PATCH oasis_profile_generator.py — perfis em PT-BR
    # ============================================================
    print("\nPATCH 4: oasis_profile_generator.py — perfis em PT-BR")

    profile_path = f"{base}/app/services/oasis_profile_generator.py"
    with open(profile_path, 'r', encoding='utf-8') as f:
        profile_content = f.read()

    if 'EXCLUSIVAMENTE em portugues' not in profile_content:
        profile_content = profile_content.replace(
            'Retorne JSON puro',
            'REGRA ABSOLUTA: Todo conteudo deve ser em portugues brasileiro. Retorne JSON puro',
        )
        # Also look for English instruction patterns
        profile_content = profile_content.replace(
            'You are a social media profile',
            'Voce e um gerador de perfis de redes sociais em portugues brasileiro. NUNCA escreva em ingles.',
        )
        profile_content = profile_content.replace(
            'Generate a realistic',
            'Gere um perfil realista e detalhado EM PORTUGUES BRASILEIRO para',
        )
        with open(profile_path, 'w', encoding='utf-8') as f:
            f.write(profile_content)
        print("  OK: Perfis forçados em PT-BR")
    else:
        print("  SKIP: Já tem PT-BR")

    # ============================================================
    # 5. PATCH graph_builder.py — tradução de nós do Graphiti
    # ============================================================
    print("\nPATCH 5: graph_builder.py — nomes de relações em PT-BR")

    graph_path = f"{base}/app/services/graph_builder.py"
    with open(graph_path, 'r', encoding='utf-8') as f:
        graph_content = f.read()

    # Adicionar mapa de tradução de relações
    rel_map = '''
    # Tradução de nomes de relações Graphiti (EN → PT-BR)
    _RELATION_MAP = {
        "FEARS": "TEME", "PROJECTS": "PROJETA", "ADVOCATES": "DEFENDE",
        "IMPLEMENTS": "IMPLEMENTA", "PRESIDES": "PRESIDE", "PLANS": "PLANEJA",
        "GENERATES": "GERA", "PROVIDES": "FORNECE", "DISCUSSES": "DISCUTE",
        "SUPPORTS": "APOIA", "OPPOSES": "SE_OPOE", "COMPETES": "COMPETE",
        "REPRESENTS": "REPRESENTA", "HAS_VALUE": "TEM_VALOR",
        "HAS_COMBINED": "TEM_COMBINADO", "RELATES_TO": "RELACIONA_COM",
        "AFFECTED": "AFETADO", "LEADS": "LIDERA",
    }
'''

    if '_RELATION_MAP' not in graph_content:
        # Inserir antes da classe
        insert_point = graph_content.find('class GraphBuilderService')
        if insert_point > 0:
            graph_content = graph_content[:insert_point] + rel_map + '\n' + graph_content[insert_point:]
            print("  OK: Mapa de tradução de relações adicionado")
    else:
        print("  SKIP: Mapa já existe")

    with open(graph_path, 'w', encoding='utf-8') as f:
        f.write(graph_content)

    print("\nTodas as correções de português aplicadas!")


if __name__ == "__main__":
    main()
