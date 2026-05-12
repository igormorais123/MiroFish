"""Validacao de conteudo de upload por assinatura (magic bytes) e heuristica de texto.

A checagem por extensao em allowed_file() pode ser burlada com arquivo binario
renomeado para .pdf/.txt. Esta validacao olha os primeiros bytes do arquivo
salvo para confirmar que o conteudo bate com o tipo declarado.

Nao usa python-magic para evitar dependencia de libmagic do SO.
"""

from __future__ import annotations

import os

# Tamanho do header a inspecionar para validacao de texto.
_TEXT_SAMPLE_BYTES = 8192
# Razao maxima de bytes nulos permitidos em arquivo declarado como texto.
_NULL_BYTE_RATIO_LIMIT = 0.01

# Magic bytes conhecidos.
_PDF_MAGIC = b'%PDF-'


class InvalidFileContent(Exception):
    """Conteudo do arquivo nao bate com a extensao declarada."""


def _read_header(path: str, size: int) -> bytes:
    with open(path, 'rb') as handle:
        return handle.read(size)


def _looks_like_text(sample: bytes) -> bool:
    """Heuristica simples: decodifica em UTF-8 ou latin-1 e tem poucos nulos."""
    if not sample:
        # Arquivo vazio nao e util mas tambem nao e perigoso; deixar passar.
        return True

    null_count = sample.count(b'\x00')
    if null_count / len(sample) > _NULL_BYTE_RATIO_LIMIT:
        return False

    try:
        sample.decode('utf-8')
        return True
    except UnicodeDecodeError:
        pass

    try:
        sample.decode('latin-1')
        # latin-1 sempre decodifica, mas se ja passou no filtro de nulos,
        # provavelmente e texto em encoding legado.
        return True
    except UnicodeDecodeError:
        return False


def validate_uploaded_file(path: str, declared_filename: str) -> None:
    """Valida o conteudo do arquivo conforme a extensao declarada.

    Args:
        path: caminho do arquivo ja salvo em disco.
        declared_filename: nome original enviado pelo cliente (usado so para extensao).

    Raises:
        InvalidFileContent: se o conteudo nao bate com a extensao.
        FileNotFoundError: se path nao existe.
    """
    if not os.path.isfile(path):
        raise FileNotFoundError(path)

    ext = os.path.splitext(declared_filename or '')[1].lower().lstrip('.')

    if ext == 'pdf':
        header = _read_header(path, len(_PDF_MAGIC))
        if not header.startswith(_PDF_MAGIC):
            raise InvalidFileContent(
                f"Arquivo '{declared_filename}' declarado como PDF nao tem assinatura %PDF-."
            )
        return

    if ext in {'txt', 'md', 'markdown'}:
        sample = _read_header(path, _TEXT_SAMPLE_BYTES)
        if not _looks_like_text(sample):
            raise InvalidFileContent(
                f"Arquivo '{declared_filename}' declarado como texto contem bytes binarios."
            )
        return

    # Extensao nao reconhecida aqui — quem validar a extensao deve barrar antes.
    raise InvalidFileContent(
        f"Extensao '.{ext}' nao validada por este modulo; rejeitar upstream."
    )
