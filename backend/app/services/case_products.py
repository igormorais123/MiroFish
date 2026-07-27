"""
Produtos do escritorio a partir do grafo do caso.

Por que existe: a saida do sistema era um relatorio sobre o proprio sistema —
convicao operacional, convergencia, densidade estrategica. Nada disso e o que a
consulta pediu. O que o escritorio usa e outra coisa, e o protocolo da fabrica
de peticoes ja descreve: cronologia auditada dos atos, o que ficou sem resposta,
o que cada tese tem de prova e onde as proprias pecas se contradizem.

Tudo aqui e derivado do grafo, nao gerado por modelo. Sao consultas sobre o que
foi lido dos autos: se o grafo nao tem, o produto sai vazio em vez de inventado.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Sequence

# Arestas da ontologia processual que estes produtos consultam.
SUSTENTA = "SUSTENTA"
CONTRADIZ = "CONTRADIZ"
DEPENDE_DE = "DEPENDE_DE"
FOI_OMITIDO_EM = "FOI_OMITIDO_EM"


def _tipo(entidade: Any) -> str:
    """Tipo da entidade: o primeiro rotulo que nao seja o generico."""
    rotulos = getattr(entidade, "labels", None) or []
    return next((r for r in rotulos if r not in ("Entity", "Node")), "Entity")


def _attr(entidade: Any, chave: str, padrao: Any = None) -> Any:
    return (getattr(entidade, "attributes", None) or {}).get(chave, padrao)


def _citacao(entidade: Any) -> Optional[str]:
    """Ponte para os autos, quando a entidade foi ancorada na ingestao."""
    return _attr(entidade, "citation")


def _arestas(entidade: Any, nome: str) -> List[Dict[str, Any]]:
    saida = []
    for aresta in getattr(entidade, "related_edges", None) or []:
        if (aresta.get("edge_name") or "").upper() == nome:
            saida.append(aresta)
    return saida


def _por_tipo(entidades: Sequence[Any], tipo: str) -> List[Any]:
    return [e for e in entidades if _tipo(e) == tipo]


# --- 1. cronologia auditada ---

# Peca judicial escreve data por extenso com a mesma naturalidade com que
# escreve em numeros, e as vezes so o ano. No acervo da Vale, das 752 datas
# extraidas apenas 83 vinham em dd/mm/aaaa: ler so esse formato jogava fora
# 93 atos que tinham data perfeitamente legivel.
_MESES = {
    "janeiro": "01", "fevereiro": "02", "marco": "03", "março": "03",
    "abril": "04", "maio": "05", "junho": "06", "julho": "07",
    "agosto": "08", "setembro": "09", "outubro": "10",
    "novembro": "11", "dezembro": "12",
}

# Ano de dois digitos: 544 das 551 datas que sobravam no acervo da Vale vinham
# assim ("28/3/05", "25.03.92"). O corte separa os autos antigos dos recentes —
# este processo corre desde 1986, entao 92 e 1992 e 05 e 2005.
CORTE_DO_SECULO = 30


def _quatro_digitos(ano: str) -> str:
    if len(ano) == 4:
        return ano
    return f"20{ano}" if int(ano) <= CORTE_DO_SECULO else f"19{ano}"


_PADROES_DE_DATA = (
    (re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b"), lambda m: (m[1], m[2], m[3])),
    (re.compile(r"\b(\d{1,2})[/.-](\d{1,2})[/.-](\d{4}|\d{2})\b"),
     lambda m: (_quatro_digitos(m[3]), m[2].zfill(2), m[1].zfill(2))),
    # "29 (vinte e nove) de abril de 1994" — o parentetico aparece em peca.
    (re.compile(r"\b(\d{1,2})\s*(?:\([^)]*\))?\s*de\s+([a-zç]+)\s+de\s+(\d{4})\b", re.I),
     lambda m: (m[3], _MESES.get(m[2].lower(), ""), m[1].zfill(2))),
)

# Ano isolado: precisao menor, mas situa o ato na cronologia.
_SO_ANO = re.compile(r"\b(19|20)\d{2}\b")


def _data_ordenavel(bruta: Any) -> Optional[str]:
    """
    Normaliza para AAAA-MM-DD, unica forma que ordena como texto.

    Data so com ano volta como AAAA: ordena junto e deixa visivel que a
    precisao e menor, o que e melhor do que descartar o ato ou inventar
    um dia que a peca nao traz.
    """
    if not bruta:
        return None
    texto = str(bruta)
    for padrao, extrai in _PADROES_DE_DATA:
        m = padrao.search(texto)
        if m:
            ano, mes, dia = extrai(m)
            if mes:
                return f"{ano}-{mes}-{dia}"
    m = _SO_ANO.search(texto)
    return m.group(0) if m else None


# Descricao que so repete o numero e a data do proprio ato. Sai as centenas
# quando o acervo traz um indice de andamentos: no caso Vale, uma tabela do
# Evento 96 virou 456 pseudo-atos, todos com a chave repetida como descricao.
_ESQUELETO = {
    "ato", "atos", "registro", "registros", "processual", "processuais",
    "identificado", "identificada", "numerado", "numerada", "associado",
    "associada", "datado", "datada", "correspondente", "referente",
    "numero", "número", "data", "datas", "ano", "valores", "dados", "texto",
    "documento", "processo", "pelo", "pela", "de", "do", "da", "dos", "das",
    "e", "a", "o", "no", "na", "com", "em", "ao", "aos", "as", "à", "um", "uma",
}


def _e_tautologica(descricao: str) -> bool:
    """
    True quando a descricao nao diz nada alem do que a chave ja dizia.

    Retirar o esqueleto e ver o que sobra e mais robusto do que casar a frase
    inteira: o modelo escreve a mesma vacuidade de dez maneiras diferentes
    ("identificado pelo numero 25", "numerado 34", "associado aos valores de
    1987"), e o que todas tem em comum e nao sobrar substantivo nenhum.
    """
    palavras = re.findall(r"[^\W\d_]+", (descricao or "").lower(), re.UNICODE)
    if not palavras:
        return False
    return not [p for p in palavras if p not in _ESQUELETO]


@dataclass
class AtoProcessual:
    evento: Optional[str]
    data: Optional[str]
    sujeito: Optional[str]
    natureza: Optional[str]
    descricao: str
    citacao: Optional[str]

    @property
    def substantivo(self) -> bool:
        """
        O ato diz o que aconteceu, e nao apenas que aconteceu.

        Nao serve para descartar — o ato existe e a data e boa. Serve para quem
        monta a peca separar a cronologia do indice de andamentos.
        """
        return not _e_tautologica(self.descricao)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "evento": self.evento,
            "data": self.data,
            "sujeito": self.sujeito,
            "natureza": self.natureza,
            "descricao": self.descricao,
            "citacao": self.citacao,
            "substantivo": self.substantivo,
        }


def build_timeline(entidades: Sequence[Any]) -> List[AtoProcessual]:
    """
    Cronologia dos atos, ordenada por data.

    Ato sem data reconhecivel vai para o fim em vez de ser descartado: a
    ausencia da data e informacao — quem for conferir precisa saber que aquele
    ato existe e nao foi possivel situa-lo.
    """
    atos = [
        AtoProcessual(
            evento=_attr(e, "numero_evento"),
            data=_data_ordenavel(_attr(e, "data")),
            sujeito=_attr(e, "sujeito"),
            natureza=_attr(e, "natureza"),
            descricao=(getattr(e, "summary", "") or getattr(e, "name", "")),
            citacao=_citacao(e),
        )
        for e in _por_tipo(entidades, "Evento")
    ]
    return sorted(atos, key=lambda a: (a.data is None, a.data or "", a.evento or ""))


# --- 2. matriz de omissoes ---

@dataclass
class Omissao:
    ponto: str
    tipo_do_ponto: str
    nao_enfrentado_em: List[str]
    citacao: Optional[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ponto": self.ponto,
            "tipo_do_ponto": self.tipo_do_ponto,
            "nao_enfrentado_em": self.nao_enfrentado_em,
            "citacao": self.citacao,
        }


def build_omissions(entidades: Sequence[Any]) -> List[Omissao]:
    """
    O que foi suscitado e nao enfrentado — eixo dos embargos de declaracao.

    Cada item precisa da ponte para os autos: embargo por omissao sem indicar
    onde o ponto foi suscitado nao se sustenta.
    """
    omissoes = []
    for entidade in entidades:
        onde = [
            (a.get("fact") or a.get("target") or "").strip()
            for a in _arestas(entidade, FOI_OMITIDO_EM)
        ]
        onde = [o for o in onde if o]
        if onde:
            omissoes.append(Omissao(
                ponto=getattr(entidade, "name", ""),
                tipo_do_ponto=_tipo(entidade),
                nao_enfrentado_em=onde,
                citacao=_citacao(entidade),
            ))
    return omissoes


# --- 3. matriz de cobertura por tese ---

@dataclass
class CoberturaDaTese:
    tese: str
    sustentada_por: List[str] = field(default_factory=list)
    depende_de: List[str] = field(default_factory=list)
    contradita_por: List[str] = field(default_factory=list)
    citacao: Optional[str] = None

    @property
    def orfa(self) -> bool:
        """Sem nada que a sustente, a tese nao tem como ser afirmada."""
        return not self.sustentada_por

    @property
    def exposta(self) -> bool:
        """Contraditada e sem lastro suficiente para responder."""
        return bool(self.contradita_por) and len(self.sustentada_por) <= len(self.contradita_por)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tese": self.tese,
            "sustentada_por": self.sustentada_por,
            "depende_de": self.depende_de,
            "contradita_por": self.contradita_por,
            "citacao": self.citacao,
            "orfa": self.orfa,
            "exposta": self.exposta,
        }


def _alvos(entidade: Any, nome_da_aresta: str) -> List[str]:
    saida = []
    for aresta in _arestas(entidade, nome_da_aresta):
        alvo = (aresta.get("target") or aresta.get("fact") or "").strip()
        if alvo:
            saida.append(alvo)
    return saida


def build_coverage_matrix(entidades: Sequence[Any]) -> List[CoberturaDaTese]:
    """
    Para cada tese: o que a sustenta, do que ela depende, o que a ataca.

    Substitui a probabilidade fabricada. "Esta tese esta orfa de documento" e
    verificavel e acionavel; "72% de conviccao" nao e nenhum dos dois.
    """
    por_nome: Dict[str, CoberturaDaTese] = {
        getattr(t, "name", ""): CoberturaDaTese(
            tese=getattr(t, "name", ""),
            depende_de=_alvos(t, DEPENDE_DE),
            citacao=_citacao(t),
        )
        for t in _por_tipo(entidades, "Tese")
    }

    # As arestas SUSTENTA e CONTRADIZ partem do documento para a tese, entao a
    # varredura e do outro lado.
    for entidade in entidades:
        origem = getattr(entidade, "name", "")
        for alvo in _alvos(entidade, SUSTENTA):
            if alvo in por_nome:
                por_nome[alvo].sustentada_por.append(origem)
        for alvo in _alvos(entidade, CONTRADIZ):
            if alvo in por_nome:
                por_nome[alvo].contradita_por.append(origem)

    return list(por_nome.values())


# --- 4. mapa de contradicoes ---

@dataclass
class Contradicao:
    de: str
    para: str
    natureza: str
    citacao: Optional[str]

    def to_dict(self) -> Dict[str, Any]:
        return {"de": self.de, "para": self.para, "natureza": self.natureza, "citacao": self.citacao}


def build_contradiction_map(entidades: Sequence[Any]) -> List[Contradicao]:
    """
    Onde as pecas se chocam — inclusive entre si, do mesmo lado.

    Contradicao interna e o que a parte contraria explora primeiro; e melhor
    encontra-la antes de protocolar.
    """
    mapa = []
    for entidade in entidades:
        origem = getattr(entidade, "name", "")
        for aresta in _arestas(entidade, CONTRADIZ):
            alvo = (aresta.get("target") or aresta.get("fact") or "").strip()
            if alvo:
                mapa.append(Contradicao(
                    de=origem,
                    para=alvo,
                    natureza=f"{_tipo(entidade)} contradiz",
                    citacao=_citacao(entidade),
                ))
    return mapa


# --- pacote completo ---

def build_case_products(entidades: Sequence[Any]) -> Dict[str, Any]:
    """
    Os quatro produtos, mais a contagem do que esta ancorado nos autos.

    `anchored_entities` importa: um pacote bonito construido sobre entidades sem
    ponte para os autos nao e utilizavel numa peca.
    """
    entidades = list(entidades or [])
    cobertura = build_coverage_matrix(entidades)
    ancoradas = sum(1 for e in entidades if _citacao(e))
    linha = build_timeline(entidades)

    return {
        "timeline": [a.to_dict() for a in linha],
        "omissions": [o.to_dict() for o in build_omissions(entidades)],
        "coverage": [c.to_dict() for c in cobertura],
        "contradictions": [c.to_dict() for c in build_contradiction_map(entidades)],
        "information_value": [v.to_dict() for v in build_information_value(entidades)],
        "summary": {
            "total_entities": len(entidades),
            "anchored_entities": ancoradas,
            "dated_acts": sum(1 for a in linha if a.data),
            # Separa a cronologia do indice de andamentos: no caso Vale uma
            # tabela do Evento 96 respondeu por 63% dos atos datados.
            "substantive_acts": sum(1 for a in linha if a.data and a.substantivo),
            "orphan_theses": sum(1 for c in cobertura if c.orfa),
            "exposed_theses": sum(1 for c in cobertura if c.exposta),
        },
    }


# --- 5. valor da informacao ---

@dataclass
class ValorDaInformacao:
    tese: str
    falta: str
    prazo: Optional[str]
    custo_estimado: Optional[str]
    impacto_decisorio: Optional[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tese": self.tese,
            "falta": self.falta,
            "prazo": self.prazo,
            "custo_estimado": self.custo_estimado,
            "impacto_decisorio": self.impacto_decisorio,
        }


def build_information_value(entidades: Sequence[Any]) -> List[ValorDaInformacao]:
    """
    Para cada tese: o que falta, quanto custa obter e o que muda se vier.

    E o que substitui a probabilidade fabricada. "Sem a guia de 1996 a tese do
    CIEX fica orfa; obte-la custa X e leva Y" e decidivel e auditavel;
    "72% de conviccao" nao e nem uma coisa nem outra.
    """
    diligencias = {getattr(d, "name", ""): d for d in _por_tipo(entidades, "Diligencia")}
    documentos = {getattr(d, "name", "") for d in _por_tipo(entidades, "Documento")}

    itens: List[ValorDaInformacao] = []
    for tese in _por_tipo(entidades, "Tese"):
        sustentacao = {
            getattr(e, "name", "")
            for e in entidades
            if getattr(tese, "name", "") in _alvos(e, SUSTENTA)
        }
        for dependencia in _alvos(tese, DEPENDE_DE):
            # Ja sustentado: a dependencia esta satisfeita e nao ha lacuna.
            if dependencia in sustentacao:
                continue
            fonte = diligencias.get(dependencia)
            itens.append(ValorDaInformacao(
                tese=getattr(tese, "name", ""),
                falta=dependencia,
                prazo=_attr(fonte, "prazo") if fonte else None,
                custo_estimado=_attr(fonte, "custo_estimado") if fonte else None,
                impacto_decisorio=(
                    _attr(fonte, "impacto_decisorio") if fonte
                    else ("sustenta a tese" if dependencia in documentos else None)
                ),
            ))
    return itens
