"""Catalogo formal de poderes comerciais do Mirofish INTEIA."""
from __future__ import annotations

from copy import deepcopy
from typing import Any


PowerItem = dict[str, Any]


class PowerCatalog:
    """Expoe poderes estaveis e estimativa comercial de selecao."""

    _POWERS: tuple[PowerItem, ...] = (
        {
            "id": "oraculo_premium",
            "nome": "Oráculo Superior",
            "descricao": "Camada analitica ampliada para perguntas estrategicas de alta complexidade.",
            "categoria": "relatorio",
            "custo_tipo": "multiplicador_tokens",
            "multiplicador_tokens": 1.5,
            "custo_fixo_brl": 0,
            "impacto": "Aumenta profundidade, cruzamento de hipoteses e custo variavel.",
            "recomendado_para": ["decisao executiva", "campanhas criticas", "diagnostico sensivel"],
            "ativo_por_padrao": False,
        },
        {
            "id": "modo_rapido",
            "nome": "Modo Rápido",
            "descricao": "Prioridade comercial de velocidade para missoes que precisam de resposta acelerada.",
            "categoria": "operacao",
            "custo_tipo": "multiplicador_tokens",
            "multiplicador_tokens": 2.5,
            "custo_fixo_brl": 0,
            "impacto": "Aplica prioridade 1.5x ao valor de referencia da missao.",
            "recomendado_para": ["missao urgente", "janela critica", "entrega superior acelerada"],
            "ativo_por_padrao": False,
        },
        {
            "id": "corte_helena",
            "nome": "Corte Helena",
            "descricao": "Revisao editorial e estrategica com padrao Helena de sintese decisoria.",
            "categoria": "relatorio",
            "custo_tipo": "custo_fixo_brl",
            "multiplicador_tokens": 1.0,
            "custo_fixo_brl": 350,
            "impacto": "Adiciona acabamento executivo e consistencia narrativa.",
            "recomendado_para": ["relatorio final", "cliente superior", "apresentacao institucional"],
            "ativo_por_padrao": False,
        },
        {
            "id": "consultores_lendarios",
            "nome": "Consultores Lendários",
            "descricao": "Ativa conselheiros sinteticos especializados para leitura multidisciplinar.",
            "categoria": "personas",
            "custo_tipo": "multiplicador_tokens",
            "multiplicador_tokens": 1.3,
            "custo_fixo_brl": 0,
            "impacto": "Amplia diversidade de enquadramentos e debate entre perspectivas.",
            "recomendado_para": ["estrategia politica", "crise reputacional", "decisao complexa"],
            "ativo_por_padrao": False,
        },
        {
            "id": "vox_personas",
            "nome": "Vox Personas",
            "descricao": "Usa personas sinteticas para testar linguagem, argumentos e reacoes.",
            "categoria": "personas",
            "custo_tipo": "multiplicador_tokens",
            "multiplicador_tokens": 1.2,
            "custo_fixo_brl": 0,
            "impacto": "Melhora leitura de aderencia discursiva por perfis sociais.",
            "recomendado_para": ["mensagens publicas", "pesquisa qualitativa", "testes de narrativa"],
            "ativo_por_padrao": False,
        },
        {
            "id": "eleitores_sinteticos",
            "nome": "Eleitores Sintéticos",
            "descricao": "Simula blocos de eleitores para avaliar recepcao de propostas e ataques.",
            "categoria": "simulacao",
            "custo_tipo": "multiplicador_tokens",
            "multiplicador_tokens": 1.35,
            "custo_fixo_brl": 0,
            "impacto": "Aumenta granularidade eleitoral e custo proporcional da simulacao.",
            "recomendado_para": ["campanha eleitoral", "segmentacao territorial", "teste de pauta"],
            "ativo_por_padrao": False,
        },
        {
            "id": "painel_judicial",
            "nome": "Painel Judicial",
            "descricao": "Organiza leitura de riscos, atores e argumentos em ambiente judicial.",
            "categoria": "setorial",
            "custo_tipo": "multiplicador_tokens",
            "multiplicador_tokens": 1.25,
            "custo_fixo_brl": 0,
            "impacto": "Traz estrutura de analise para disputas juridicas e institucionais.",
            "recomendado_para": ["contencioso estrategico", "monitoramento judicial", "analise de risco"],
            "ativo_por_padrao": False,
        },
        {
            "id": "painel_parlamentar",
            "nome": "Painel Parlamentar",
            "descricao": "Mapeia incentivos, coalizoes e narrativas em ambiente legislativo.",
            "categoria": "setorial",
            "custo_tipo": "multiplicador_tokens",
            "multiplicador_tokens": 1.25,
            "custo_fixo_brl": 0,
            "impacto": "Aprofunda leitura de governabilidade, votacao e articulacao politica.",
            "recomendado_para": ["relacoes governamentais", "agenda legislativa", "coalizoes"],
            "ativo_por_padrao": False,
        },
        {
            "id": "contrarians",
            "nome": "Contrarians",
            "descricao": "Inclui leitura adversarial para encontrar fragilidades, pontos cegos e objeccoes.",
            "categoria": "qualidade",
            "custo_tipo": "multiplicador_tokens",
            "multiplicador_tokens": 1.15,
            "custo_fixo_brl": 0,
            "impacto": "Eleva robustez critica e pode ampliar tempo de consolidacao.",
            "recomendado_para": ["validacao de tese", "pre-mortem", "gestao de risco"],
            "ativo_por_padrao": False,
        },
        {
            "id": "leitura_profunda",
            "nome": "Leitura Profunda",
            "descricao": "Expande contexto, evidencias e encadeamento causal do diagnostico.",
            "categoria": "relatorio",
            "custo_tipo": "multiplicador_tokens",
            "multiplicador_tokens": 2.4,
            "custo_fixo_brl": 0,
            "impacto": "Aumenta substancialmente tokens, profundidade e tempo de processamento.",
            "recomendado_para": ["dossie completo", "diagnostico estrategico", "caso de alta incerteza"],
            "ativo_por_padrao": False,
        },
        {
            "id": "forecast_ledger",
            "nome": "Livro de Previsões",
            "descricao": "Registra previsoes, premissas e revisoes para acompanhamento posterior.",
            "categoria": "previsao",
            "custo_tipo": "multiplicador_tokens",
            "multiplicador_tokens": 1.1,
            "custo_fixo_brl": 0,
            "impacto": "Adiciona rastreabilidade operacional a hipoteses e cenarios.",
            "recomendado_para": ["monitoramento continuo", "previsao eleitoral", "controle de hipoteses"],
            "ativo_por_padrao": False,
        },
        {
            "id": "bundle_supremo",
            "nome": "Pacote Supremo",
            "descricao": "Pacote comercial fechado para habilitar composicao maxima de poderes superiores.",
            "categoria": "bundle",
            "custo_tipo": "custo_fixo_brl",
            "multiplicador_tokens": 1.0,
            "custo_fixo_brl": 1200,
            "impacto": "Inclui curadoria superior e deve ser reservado para entregas de maior valor.",
            "recomendado_para": ["proposta corporativa", "sala estrategica", "entrega superior completa"],
            "ativo_por_padrao": False,
        },
    )

    def list_powers(self, tipo: str | None = None, categoria: str | None = None) -> list[PowerItem]:
        powers = self._POWERS
        if tipo is not None:
            powers = tuple(power for power in powers if power["custo_tipo"] == tipo)
        if categoria is not None:
            powers = tuple(power for power in powers if power["categoria"] == categoria)
        return deepcopy(list(powers))

    def get_power(self, power_id: str) -> PowerItem | None:
        for power in self._POWERS:
            if power["id"] == power_id:
                return deepcopy(power)
        return None

    def estimate_selection(
        self,
        selected_ids: list[str] | tuple[str, ...],
        base_tokens: int | float = 0,
        base_value_brl: int | float = 0,
    ) -> dict[str, Any]:
        selected_set = {str(power_id) for power_id in selected_ids}
        selected = [power for power in self._POWERS if power["id"] in selected_set]
        known_ids = {power["id"] for power in selected}
        unknown_ids = [str(power_id) for power_id in selected_ids if str(power_id) not in known_ids]

        multiplier = 1.0
        fixed_cost = 0.0
        notes: list[str] = []

        for power in selected:
            if power["custo_tipo"] == "custo_fixo_brl":
                fixed_cost += float(power["custo_fixo_brl"])
            else:
                multiplier *= float(power["multiplicador_tokens"])
            notes.append(f"{power['nome']}: {power['impacto']}")

        for unknown_id in unknown_ids:
            notes.append(f"Poder desconhecido ignorado: {unknown_id}.")

        multiplier = round(multiplier, 4)
        estimated_tokens = int(round(max(0.0, float(base_tokens)) * multiplier))
        variable_value = max(0.0, float(base_value_brl)) * multiplier
        estimated_value = round(variable_value + fixed_cost, 2)

        return {
            "poderes_selecionados": deepcopy(selected),
            "multiplicador_total": self._clean_number(multiplier),
            "tokens_estimados": estimated_tokens,
            "custo_fixo_brl": self._clean_number(round(fixed_cost, 2)),
            "valor_estimado_brl": self._clean_number(estimated_value),
            "notas_operacionais": notes,
        }

    def _clean_number(self, value: float | int) -> int | float:
        if isinstance(value, float) and value.is_integer():
            return int(value)
        return value
