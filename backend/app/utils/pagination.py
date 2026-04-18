"""Validação de parâmetros de paginação.

2026-04-18, Phase 7: evita OOM e DoS por limits absurdos
(ver CONCERNS.md "Request Data Not Validated").
"""
from flask import request

MAX_LIMIT = 10000
MAX_OFFSET = 1000000


def get_limit(default: int = 50, max_limit: int = MAX_LIMIT) -> int:
    """Retorna ?limit= validado no range [1, max_limit]."""
    raw = request.args.get('limit', default, type=int)
    if raw is None or raw < 1:
        return default
    return min(raw, max_limit)


def get_offset(default: int = 0, max_offset: int = MAX_OFFSET) -> int:
    """Retorna ?offset= validado no range [0, max_offset]."""
    raw = request.args.get('offset', default, type=int)
    if raw is None or raw < 0:
        return default
    return min(raw, max_offset)


def get_from_line(default: int = 0, max_line: int = MAX_OFFSET) -> int:
    """Retorna ?from_line= validado no range [0, max_line]."""
    raw = request.args.get('from_line', default, type=int)
    if raw is None or raw < 0:
        return default
    return min(raw, max_line)
