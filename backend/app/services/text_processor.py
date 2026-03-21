"""
Servico de processamento de texto
"""

from typing import List, Optional
from ..utils.file_parser import FileParser, split_text_into_chunks


class TextProcessor:
    """Processador de texto"""

    @staticmethod
    def extract_from_files(file_paths: List[str]) -> str:
        """Extrair texto de multiplos arquivos"""
        return FileParser.extract_from_multiple(file_paths)

    @staticmethod
    def split_text(
        text: str,
        chunk_size: int = 500,
        overlap: int = 50
    ) -> List[str]:
        """
        Dividir texto em blocos

        Args:
            text: Texto original
            chunk_size: Tamanho do bloco
            overlap: Tamanho da sobreposicao

        Returns:
            Lista de blocos de texto
        """
        return split_text_into_chunks(text, chunk_size, overlap)

    @staticmethod
    def preprocess_text(text: str) -> str:
        """
        Pre-processar texto
        - Remover espacos em branco excessivos
        - Padronizar quebras de linha

        Args:
            text: Texto original

        Returns:
            Texto processado
        """
        import re

        # Padronizar quebras de linha
        text = text.replace('\r\n', '\n').replace('\r', '\n')

        # Remover linhas em branco consecutivas (manter no maximo duas quebras de linha)
        text = re.sub(r'\n{3,}', '\n\n', text)

        # Remover espacos no inicio e fim das linhas
        lines = [line.strip() for line in text.split('\n')]
        text = '\n'.join(lines)

        return text.strip()

    @staticmethod
    def get_text_stats(text: str) -> dict:
        """Obter estatisticas do texto"""
        return {
            "total_chars": len(text),
            "total_lines": text.count('\n') + 1,
            "total_words": len(text.split()),
        }
