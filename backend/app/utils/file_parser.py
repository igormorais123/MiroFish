"""
Ferramenta de analise de arquivos
Suporta extracao de texto de arquivos PDF, Markdown e TXT
"""

import bisect
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# O eproc carimba a origem em toda folha que gera:
#   "Processo 5020376-80.2018.4.04.7100/RS, Evento 3, INIC2, Página 3"
# Medido no acervo da Vale Trading: 4.246 de 4.604 folhas (92%) tem o carimbo.
CARIMBO_EPROC = re.compile(
    r"Processo\s+([\d\.\-]+/\w+)\s*,\s*Evento\s+(\d+)\s*,\s*([A-Z0-9_]+)\s*,\s*"
    r"P[aáà]gina\s+(\d+)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class PageSpan:
    """Onde uma pagina de um documento comeca e termina no corpus concatenado."""
    doc_id: str
    doc_index: int
    page: int
    start: int
    end: int
    # Extraidos do carimbo do eproc, quando a folha o traz. E esta a referencia
    # que se usa numa peca: ninguem cita "PARTE_1.PDF, p. 10", cita o evento.
    evento: Optional[str] = None
    tipo_documento: Optional[str] = None
    pagina_do_evento: Optional[str] = None

    def as_citation(self) -> str:
        """Citacao processual quando o carimbo existe; caminho do PDF quando nao."""
        if self.evento:
            tipo = f", {self.tipo_documento}" if self.tipo_documento else ""
            folha = f", p. {self.pagina_do_evento}" if self.pagina_do_evento else ""
            return f"Evento {self.evento}{tipo}{folha}"
        return f"{self.doc_id}, p. {self.page}"

    def as_source_ref(self) -> str:
        """Referencia completa: citacao processual mais onde conferir no arquivo."""
        base = f"{self.doc_id}, p. {self.page}"
        return f"{self.as_citation()} ({base})" if self.evento else base


def _extrai_carimbo(texto: str) -> Dict[str, Optional[str]]:
    m = CARIMBO_EPROC.search(texto or "")
    if not m:
        return {"evento": None, "tipo_documento": None, "pagina_do_evento": None}
    return {"evento": m.group(2), "tipo_documento": m.group(3), "pagina_do_evento": m.group(4)}


def locate_page(offset: int, spans: List[PageSpan]) -> Optional[PageSpan]:
    """
    Documento e pagina de um offset do corpus, ou None fora de qualquer pagina.

    Busca binaria porque um acervo processual tem milhares de paginas e esta
    consulta roda uma vez por entidade extraida.
    """
    if not spans or offset < 0:
        return None
    inicios = [s.start for s in spans]
    indice = bisect.bisect_right(inicios, offset) - 1
    if indice < 0:
        return None
    candidato = spans[indice]
    # Offsets entre paginas (cabecalho de documento, separador) nao pertencem a
    # nenhuma folha: melhor devolver None do que atribuir a folha anterior.
    return candidato if offset < candidato.end else None


def _read_text_with_fallback(file_path: str) -> str:
    """
    Ler arquivo de texto, com deteccao automatica de codificacao em caso de falha UTF-8.

    Estrategia de fallback em multiplos niveis:
    1. Primeiro tenta decodificacao UTF-8
    2. Usa charset_normalizer para detectar codificacao
    3. Fallback para chardet para detectar codificacao
    4. Ultimo recurso: UTF-8 + errors='replace'

    Args:
        file_path: Caminho do arquivo

    Returns:
        Conteudo do texto decodificado
    """
    data = Path(file_path).read_bytes()

    # Primeiro tentar UTF-8
    try:
        return data.decode('utf-8')
    except UnicodeDecodeError:
        pass

    # Tentar usar charset_normalizer para detectar codificacao
    encoding = None
    try:
        from charset_normalizer import from_bytes
        best = from_bytes(data).best()
        if best and best.encoding:
            encoding = best.encoding
    except Exception:
        pass

    # Fallback para chardet
    if not encoding:
        try:
            import chardet
            result = chardet.detect(data)
            encoding = result.get('encoding') if result else None
        except Exception:
            pass

    # Ultimo recurso: UTF-8 + replace
    if not encoding:
        encoding = 'utf-8'

    return data.decode(encoding, errors='replace')


class FileParser:
    """Analisador de arquivos"""

    SUPPORTED_EXTENSIONS = {'.pdf', '.md', '.markdown', '.txt'}

    @classmethod
    def extract_text(cls, file_path: str) -> str:
        """
        Extrair texto de um arquivo

        Args:
            file_path: Caminho do arquivo

        Returns:
            Conteudo do texto extraido
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"Arquivo nao encontrado: {file_path}")

        suffix = path.suffix.lower()

        if suffix not in cls.SUPPORTED_EXTENSIONS:
            raise ValueError(f"Formato de arquivo nao suportado: {suffix}")

        if suffix == '.pdf':
            return cls._extract_from_pdf(file_path)
        elif suffix in {'.md', '.markdown'}:
            return cls._extract_from_md(file_path)
        elif suffix == '.txt':
            return cls._extract_from_txt(file_path)

        raise ValueError(f"Formato de arquivo nao processavel: {suffix}")

    @staticmethod
    def _extract_from_pdf(file_path: str) -> str:
        """Extrair texto de PDF"""
        try:
            import fitz  # PyMuPDF
        except ImportError:
            raise ImportError("Necessario instalar PyMuPDF: pip install PyMuPDF")

        text_parts = []
        with fitz.open(file_path) as doc:
            for page in doc:
                text = page.get_text()
                if text.strip():
                    text_parts.append(text)

        return "\n\n".join(text_parts)

    @staticmethod
    def _extract_from_md(file_path: str) -> str:
        """Extrair texto de Markdown, com deteccao automatica de codificacao"""
        return _read_text_with_fallback(file_path)

    @staticmethod
    def _extract_from_txt(file_path: str) -> str:
        """Extrair texto de TXT, com deteccao automatica de codificacao"""
        return _read_text_with_fallback(file_path)

    @staticmethod
    def _pages_from_pdf(file_path: str) -> List[str]:
        """Texto de cada pagina, preservando a posicao mesmo quando vazia."""
        try:
            import fitz  # PyMuPDF
        except ImportError:
            raise ImportError("Necessario instalar PyMuPDF: pip install PyMuPDF")

        with fitz.open(file_path) as doc:
            return [page.get_text() for page in doc]

    @classmethod
    def extract_pages(cls, file_path: str) -> List[str]:
        """
        Texto por pagina. Formatos sem paginacao devolvem uma pagina so.

        Pagina vazia continua na lista: descartar embaralharia a numeracao, e o
        numero e justamente o que da o pincite.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Arquivo nao encontrado: {file_path}")
        if path.suffix.lower() == '.pdf':
            return cls._pages_from_pdf(file_path)
        return [cls.extract_text(file_path)]

    @classmethod
    def extract_with_page_index(
        cls, file_paths: List[str]
    ) -> Tuple[str, List["PageSpan"]]:
        """
        Concatena o corpus e devolve o indice de onde cada pagina comeca.

        O texto sai igual ao de `extract_from_multiple`, para nao quebrar quem ja
        consome; o que se ganha e poder responder "de que documento e de que
        folha veio este trecho" a partir de um offset — que e o que separa
        "a IA disse" de "esta na fl. X".
        """
        # O texto e os offsets crescem juntos: montar um e depois medir o outro
        # e como os dois divergem sem ninguem perceber.
        corpus: List[str] = []
        spans: List[PageSpan] = []
        cursor = 0

        def escreve(fragmento: str) -> int:
            nonlocal cursor
            inicio = cursor
            corpus.append(fragmento)
            cursor += len(fragmento)
            return inicio

        for indice, file_path in enumerate(file_paths, 1):
            filename = Path(file_path).name
            if indice > 1:
                escreve("\n\n")

            try:
                paginas = cls.extract_pages(file_path)
            except Exception as e:
                escreve(f"=== Documento {indice}: {file_path} (falha na extracao: {str(e)}) ===")
                continue

            escreve(f"=== Documento {indice}: {filename} ===\n")
            for numero, texto in enumerate(paginas, 1):
                if not texto.strip():
                    continue
                inicio = escreve(texto)
                spans.append(PageSpan(
                    doc_id=filename,
                    doc_index=indice,
                    page=numero,
                    start=inicio,
                    end=inicio + len(texto),
                    **_extrai_carimbo(texto),
                ))
                if not texto.endswith("\n"):
                    escreve("\n")

        return "".join(corpus), spans

    @classmethod
    def extract_from_multiple(cls, file_paths: List[str]) -> str:
        """
        Extrair texto de multiplos arquivos e combinar

        Args:
            file_paths: Lista de caminhos de arquivos

        Returns:
            Texto combinado
        """
        all_texts = []

        for i, file_path in enumerate(file_paths, 1):
            try:
                text = cls.extract_text(file_path)
                filename = Path(file_path).name
                all_texts.append(f"=== Documento {i}: {filename} ===\n{text}")
            except Exception as e:
                all_texts.append(f"=== Documento {i}: {file_path} (falha na extracao: {str(e)}) ===")

        return "\n\n".join(all_texts)


def split_text_into_chunks(
    text: str,
    chunk_size: int = 500,
    overlap: int = 50
) -> List[str]:
    """
    Dividir texto em blocos menores

    Args:
        text: Texto original
        chunk_size: Numero de caracteres por bloco
        overlap: Numero de caracteres de sobreposicao

    Returns:
        Lista de blocos de texto
    """
    if len(text) <= chunk_size:
        return [text] if text.strip() else []

    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size

        # Tentar dividir na fronteira de sentenca
        if end < len(text):
            # Procurar o separador de fim de sentenca mais proximo
            for sep in ['。', '！', '？', '.\n', '!\n', '?\n', '\n\n', '. ', '! ', '? ']:
                last_sep = text[start:end].rfind(sep)
                if last_sep != -1 and last_sep > chunk_size * 0.3:
                    end = start + last_sep + len(sep)
                    break

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        # Proximo bloco comeca na posicao de sobreposicao
        start = end - overlap if end < len(text) else len(text)

    return chunks
