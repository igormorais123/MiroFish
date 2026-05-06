"""Gate deterministico de densidade estrategica para relatorios caros."""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Any, Dict, Iterable


ISSUE_LABELS = {
    "tese_vencedora_ausente": "Falta a tese vencedora proposta para orientar a decisao.",
    "tese_adversaria_ausente": "Falta a tese adversaria mais forte.",
    "cortes_ausentes": "Falta dizer o que deve ser cortado ou evitado.",
    "acao_segura_ausente": "Falta uma acao ou pedido seguro para executar agora.",
    "risco_operacional_ausente": "Falta apontar o pedido ou acao perigosa.",
    "matriz_temporal_ausente": "Falta uma matriz temporal 15/30/60 ou equivalente.",
    "evidencia_ausente": "Falta amarrar a recomendacao a documentos ou evidencias.",
    "perguntas_decisor_ausentes": "Falta antecipar perguntas provaveis do decisor.",
    "gatilhos_reversao_ausentes": "Falta indicar sinais ou gatilhos de reversao.",
    "decisao_sem_delta": "Nao explica qual decisao muda em relacao ao obvio.",
    "excesso_generico": "Ha linguagem generica sem estrutura acionavel suficiente.",
    "conteudo_substantivo_insuficiente": "Ha sinais estrategicos sem explicacao substantiva suficiente.",
    "densidade_caso_familiar_insuficiente": (
        "Falta densidade do caso familiar: linha segura, simulacao adversarial, "
        "pedidos seguros/perigosos, documentos 15/30/60 e tratamento tecnico de escola/saude."
    ),
}


@dataclass(frozen=True)
class Signal:
    key: str
    label: str
    patterns: tuple[str, ...]


class StrategicDensityGate:
    """Avalia se um relatorio entrega decisao superior ao obvio."""

    _signals = (
        Signal(
            "tese_vencedora",
            "Tese vencedora identificada",
            (
                r"\btese vencedora\b",
                r"\btese principal\b",
                r"\bestrategia vencedora\b",
                r"\blinha recomendada\b",
                r"\bestrategia recomendada\b",
                r"\bcaminho recomendado\b",
                r"\bposicao principal\b",
                r"\bproposta principal\b",
                r"\bencaminhamento recomendado\b",
                r"\bestrategia principal\b",
                r"\brecomendacao central\b",
            ),
        ),
        Signal(
            "tese_adversaria",
            "Tese adversaria mais forte identificada",
            (
                r"\btese adversaria\b",
                r"\bargumento adversario\b",
                r"\bcontra[- ]?argumento\b",
                r"\bargumento contrario\b",
                r"\bobjecao\b",
                r"\bcomo o outro lado\b",
                r"\ba parte contraria dira\b",
                r"\ba outra parte dira\b",
                r"\bo decisor pode entender\b",
                r"\brisco de leitura do juiz\b",
                r"\brisco de leitura\b",
                r"\bataque provavel\b",
            ),
        ),
        Signal(
            "cortes",
            "Cortes ou condutas a evitar identificados",
            (
                r"\bcortar da peca\b",
                r"\bcortar\b",
                r"\bretirar\b",
                r"\bexcluir\b",
                r"\bexclua\b",
                r"\bremover\b",
                r"\bnao usar\b",
                r"\bevitar\b",
                r"\bsuprimir\b",
                r"\bnao incluir\b",
                r"\bretire\b",
                r"\bremover da peca\b",
                r"\bdeixar fora\b",
            ),
        ),
        Signal(
            "acao_segura",
            "Pedido ou acao segura identificado",
            (
                r"\bpedido seguro\b",
                r"\bacao segura\b",
                r"\bproximo passo\b",
                r"\bfazer agora\b",
                r"\bprovidencia imediata\b",
                r"\bmedida segura\b",
                r"\bmedida prudente\b",
            ),
        ),
        Signal(
            "risco_operacional",
            "Pedido ou acao perigosa identificado",
            (
                r"\bpedido perigoso\b",
                r"\bacao perigosa\b",
                r"\brisco\b",
                r"\bnao pedir\b",
                r"\brisco de parecer precipitado\b",
                r"\bnao pedir agora\b",
            ),
        ),
        Signal(
            "matriz_temporal",
            "Matriz temporal identificada",
            (
                r"\bmatriz 15/30/60\b",
                r"\b15/30/60\b",
                r"\b15\s*dias\b.*\b30\s*dias\b.*\b60\s*dias\b",
                r"\bem\s+15\s+dias\b",
                r"\bem\s+30\s+dias\b",
                r"\bem\s+60\s+dias\b",
                r"\bquinzena\b",
                r"\bproximos trinta dias\b",
                r"\bcurto prazo\b.*\bmedio prazo\b",
                r"\bproximos dias\b",
            ),
        ),
        Signal(
            "evidencia",
            "Documentos ou evidencias vinculados",
            (
                r"\bdocumentos?\b",
                r"\bevidencias?\b",
                r"\bids?\s*\d",
                r"\b\d{6,}\b",
                r"\bcomprovantes?\b",
                r"\banexos?\b",
                r"\bprovas?\b",
                r"\bids?\b",
                r"\bdocumentos prioritarios\b",
            ),
        ),
        Signal(
            "perguntas_decisor",
            "Perguntas provaveis do decisor antecipadas",
            (
                r"\bperguntas? provaveis\b",
                r"\bdecisor\b",
                r"\bo juiz perguntara\b",
                r"\bpergunta[- ]chave\b",
                r"\bo relator perguntara\b",
                r"\bo juiz pode perguntar\b",
                r"\bo decisor perguntaria\b",
                r"\bjuiz pode perguntar\b",
                r"\bponto que sera cobrado\b",
                r"\bduvida do decisor\b",
            ),
        ),
        Signal(
            "gatilhos_reversao",
            "Gatilhos de reversao identificados",
            (
                r"\bgatilhos? de reversao\b",
                r"\bsinais? de reversao\b",
                r"\bse ocorrer\b",
                r"\bse surgir\b",
                r"\breavaliar\b",
                r"\bsinal que muda\b",
                r"\bgatilho de mudanca\b",
                r"\bmudaria a conclusao\b",
            ),
        ),
        Signal(
            "ganho_obvio",
            "Ganho sobre o obvio explicitado",
            (
                r"\bganho sobre o obvio\b",
                r"\balem do obvio\b",
                r"\bmuda a decisao\b",
                r"\bdelta\b",
                r"\bdiferencial\b",
                r"\bponto decisivo\b",
                r"\bdecisao superior\b",
                r"\bo diferencial\b",
                r"\bnao e apenas\b",
                r"\bnao bastava\b",
                r"\bganho estrategico\b",
            ),
        ),
    )

    _generic_patterns = (
        r"\bagir com prudencia\b",
        r"\bmanter comunicacao clara\b",
        r"\bcomunicacao clara\b",
        r"\borganizar documentos\b",
        r"\bevitar conflitos\b",
        r"\bbuscar estabilidade\b",
        r"\bmelhor caminho\b",
        r"\be importante\b",
    )

    def evaluate(self, report: str) -> Dict[str, Any]:
        normalized = self._normalize(report)
        signal_hits = self._collect_signal_hits(normalized)
        generic_hits = self._collect_generic_hits(normalized)
        substance = self._measure_substance(normalized)
        case_specificity = self._measure_family_case_specificity(normalized)

        structure_score = len(signal_hits) / len(self._signals)
        generic_penalty = min(0.35, len(generic_hits) * 0.08)
        non_generic_score = self._clamp(structure_score - generic_penalty)

        actionability_score = self._score_presence(
            signal_hits,
            ("cortes", "acao_segura", "risco_operacional", "matriz_temporal", "gatilhos_reversao"),
        )
        adversarial_score = self._score_presence(
            signal_hits,
            ("tese_adversaria", "perguntas_decisor", "risco_operacional"),
        )
        evidence_binding_score = self._score_presence(
            signal_hits,
            ("evidencia", "matriz_temporal", "acao_segura"),
        )
        decision_delta_score = self._score_presence(
            signal_hits,
            ("tese_vencedora", "ganho_obvio", "acao_segura", "risco_operacional", "gatilhos_reversao"),
        )

        final_score = self._clamp(
            non_generic_score * 0.20
            + actionability_score * 0.25
            + adversarial_score * 0.20
            + evidence_binding_score * 0.15
            + decision_delta_score * 0.20
        )
        if case_specificity["applies"]:
            final_score = self._clamp(final_score * 0.80 + case_specificity["score"] * 0.20)
        substantive_score = substance["score"]
        issues = self._issues(
            signal_hits,
            generic_hits,
            non_generic_score,
            decision_delta_score,
            substantive_score,
            case_specificity,
        )
        passes_gate = (
            final_score >= 0.70
            and decision_delta_score >= 0.70
            and substantive_score >= 0.65
            and (not case_specificity["applies"] or case_specificity["score"] >= 0.70)
        )

        return {
            "non_generic_score": round(non_generic_score, 2),
            "actionability_score": round(actionability_score, 2),
            "adversarial_score": round(adversarial_score, 2),
            "evidence_binding_score": round(evidence_binding_score, 2),
            "decision_delta_score": round(decision_delta_score, 2),
            "substantive_score": round(substantive_score, 2),
            "case_specific_score": round(case_specificity["score"], 2),
            "final_score": round(final_score, 2),
            "passes_gate": passes_gate,
            "issues": issues,
            "hits": {
                "signals": {key: self._label_for(key) for key in signal_hits},
                "generic_terms": generic_hits,
                "substance": substance,
                "case_specificity": case_specificity,
                "issues": {issue: ISSUE_LABELS[issue] for issue in issues},
            },
        }

    def _collect_signal_hits(self, text: str) -> set[str]:
        hits = set()
        for signal in self._signals:
            if any(re.search(pattern, text, flags=re.DOTALL) for pattern in signal.patterns):
                hits.add(signal.key)
        return hits

    def _collect_generic_hits(self, text: str) -> list[str]:
        return [pattern.strip(r"\b").replace("\\b", "") for pattern in self._generic_patterns if re.search(pattern, text)]

    def _issues(
        self,
        signal_hits: set[str],
        generic_hits: list[str],
        non_generic_score: float,
        decision_delta_score: float,
        substantive_score: float,
        case_specificity: Dict[str, Any],
    ) -> list[str]:
        required = {
            "tese_vencedora": "tese_vencedora_ausente",
            "tese_adversaria": "tese_adversaria_ausente",
            "cortes": "cortes_ausentes",
            "acao_segura": "acao_segura_ausente",
            "risco_operacional": "risco_operacional_ausente",
            "matriz_temporal": "matriz_temporal_ausente",
            "evidencia": "evidencia_ausente",
            "perguntas_decisor": "perguntas_decisor_ausentes",
            "gatilhos_reversao": "gatilhos_reversao_ausentes",
        }
        issues = [issue for signal, issue in required.items() if signal not in signal_hits]
        if "ganho_obvio" not in signal_hits or decision_delta_score < 0.70:
            issues.append("decisao_sem_delta")
        if generic_hits and non_generic_score < 0.70:
            issues.append("excesso_generico")
        if substantive_score < 0.65:
            issues.append("conteudo_substantivo_insuficiente")
        if case_specificity["applies"] and case_specificity["score"] < 0.70:
            issues.append("densidade_caso_familiar_insuficiente")
        return issues

    def _label_for(self, key: str) -> str:
        for signal in self._signals:
            if signal.key == key:
                return signal.label
        return key

    @staticmethod
    def _score_presence(signal_hits: set[str], expected: Iterable[str]) -> float:
        expected_list = list(expected)
        return len([key for key in expected_list if key in signal_hits]) / len(expected_list)

    @staticmethod
    def _normalize(text: str) -> str:
        folded = unicodedata.normalize("NFKD", text or "")
        ascii_text = "".join(ch for ch in folded if not unicodedata.combining(ch))
        return ascii_text.casefold()

    @staticmethod
    def _measure_substance(text: str) -> Dict[str, Any]:
        words = re.findall(r"\b[\w-]+\b", text)
        segments = [
            segment.strip()
            for segment in re.split(r"(?:\n+|[.!?]+)", text)
            if segment.strip()
        ]
        segment_word_counts = [
            len(re.findall(r"\b[\w-]+\b", segment))
            for segment in segments
        ]
        explanatory_segments = [count for count in segment_word_counts if count >= 8]
        very_short_segments = [count for count in segment_word_counts if count <= 4]

        word_score = StrategicDensityGate._clamp(len(words) / 90)
        explanatory_ratio = (
            len(explanatory_segments) / len(segment_word_counts)
            if segment_word_counts
            else 0.0
        )
        explanatory_count_score = StrategicDensityGate._clamp(len(explanatory_segments) / 6)
        short_penalty = (
            min(0.45, len(very_short_segments) / len(segment_word_counts))
            if segment_word_counts
            else 0.45
        )
        score = StrategicDensityGate._clamp(
            word_score * 0.40
            + explanatory_ratio * 0.35
            + explanatory_count_score * 0.25
            - short_penalty
        )

        return {
            "word_count": len(words),
            "segment_count": len(segment_word_counts),
            "explanatory_segment_count": len(explanatory_segments),
            "very_short_segment_count": len(very_short_segments),
            "score": round(score, 4),
        }

    @staticmethod
    def _measure_family_case_specificity(text: str) -> Dict[str, Any]:
        context_patterns = (
            r"\bigor\b",
            r"\bcrianca\b",
            r"\bfilh[ao]\b",
            r"\bconviv",
            r"\bguarda\b",
            r"\bescola\b",
            r"\bsaude\b",
            r"\bmedicacao\b",
            r"\bmae\b",
            r"\bparental\b",
            r"\bpsicossocial\b",
        )
        context_hits = [
            pattern for pattern in context_patterns if re.search(pattern, text)
        ]
        applies = len(context_hits) >= 2
        if not applies:
            return {
                "applies": False,
                "score": 1.0,
                "context_hits": context_hits,
                "criteria": {},
            }

        criteria = {
            "linha_segura": StrategicDensityGate._score_pattern_groups(
                text,
                (
                    (r"\bcumprir impecavelmente\b", r"\bcumprimento\b", r"\bcumprir\b"),
                    (r"\bcalendario operacional\b", r"\bcalendario claro\b", r"\bagenda\b"),
                    (r"\bdossie de estabilidade\b", r"\bestabilidade comprovada\b", r"\bprevisibilidade\b"),
                    (r"\bpericia\b.*\bbilateral\b", r"\bestudo psicossocial\b.*\bbilateral\b", r"\blaudo\b"),
                    (
                        r"\bampliacao\b.*\bconsequencia\b",
                        r"\bnao\b.*\bpedido maximalista\b",
                        r"\bnao pedir agora\b.*\bampliacao\b",
                    ),
                ),
            ),
            "simulacao_adversarial_dura": StrategicDensityGate._score_pattern_groups(
                text,
                (
                    (r"\bparte contraria\b", r"\bmae\b", r"\boutro lado\b"),
                    (r"\bmp\b", r"\bministerio publico\b", r"\bjuiz\b", r"\bdecisor\b"),
                    (r"\bfalas?\b", r"\bmensagens?\b", r"\bexcesso de mensagens?\b"),
                    (r"\batraso\b", r"\bambiguidade de calendario\b", r"\bfalta de cooperacao\b"),
                    (r"\bdiscussao medica\b", r"\bmedicacao\b", r"\bsaude\b"),
                    (r"\bconflito\b.*\bescola\b", r"\bescola\b.*\bconflito\b", r"\bocorrencias escolares\b"),
                ),
            ),
            "pedidos_seguros_e_perigosos": StrategicDensityGate._score_pattern_groups(
                text,
                (
                    (r"\bpedidos? seguros?\b", r"\bmedida segura\b", r"\bpedido seguro\b"),
                    (r"\bpedidos? precipitados\b", r"\bpedido perigoso\b", r"\bperigosos? agora\b"),
                    (r"\bnao pedir agora\b", r"\bparece precipitado\b", r"\bmaximalista\b"),
                ),
            ),
            "documentos_15_30_60": StrategicDensityGate._score_pattern_groups(
                text,
                (
                    (r"\bdocumentos?\b", r"\bcomprovantes?\b", r"\bregistros?\b"),
                    (r"\b15\s*dias\b", r"\bem\s+15\s+dias\b"),
                    (r"\b30\s*dias\b", r"\bem\s+30\s+dias\b"),
                    (r"\b60\s*dias\b", r"\bem\s+60\s+dias\b"),
                    (r"\bescola\b", r"\bsaude\b", r"\bmensagens?\b", r"\blaudo\b"),
                ),
            ),
            "escola_saude_via_tecnica": StrategicDensityGate._score_pattern_groups(
                text,
                (
                    (r"\bescola\b", r"\bescolares\b"),
                    (r"\bsaude\b", r"\bmedicacao\b", r"\bmedica\b"),
                    (r"\btecnic[ao]\b", r"\bprofissional\b", r"\bpericia\b", r"\blaudo\b", r"\bpsicossocial\b"),
                    (r"\bnao\b.*\bdisputa pessoal\b", r"\bretirar\b.*\bdisputa pessoal\b"),
                ),
            ),
        }
        score = sum(criteria.values()) / len(criteria)

        return {
            "applies": True,
            "score": round(score, 4),
            "context_hits": context_hits,
            "criteria": criteria,
        }

    @staticmethod
    def _score_pattern_groups(text: str, pattern_groups: tuple[tuple[str, ...], ...]) -> float:
        hits = 0
        for patterns in pattern_groups:
            if any(re.search(pattern, text, flags=re.DOTALL) for pattern in patterns):
                hits += 1
        return hits / len(pattern_groups)

    @staticmethod
    def _clamp(value: float) -> float:
        return max(0.0, min(1.0, value))
