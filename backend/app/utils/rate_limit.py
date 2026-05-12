"""Rate limit caseiro por IP, em memoria, sem dependencias externas.

Pensado para proteger rotas LLM caras quando expostas publicamente.
Suficiente para 1 worker; para multi-worker gunicorn o limite efetivo
e por worker (cada um tem seu dict). Em produc,ao com 2 workers o
limite real e ~2x o configurado. Aceitavel ate justificar Redis.
"""

from __future__ import annotations

import threading
import time
from collections import deque
from functools import wraps

from flask import jsonify, request

from .logger import get_logger

logger = get_logger('mirofish.rate_limit')

_lock = threading.Lock()
_buckets: dict[str, deque[float]] = {}


def _client_id() -> str:
    """Identifica o cliente. Honra X-Forwarded-For quando atras de proxy."""
    forwarded = request.headers.get('X-Forwarded-For', '').split(',')[0].strip()
    return forwarded or (request.remote_addr or 'unknown')


def _check(key: str, limit: int, window_seconds: float) -> tuple[bool, float]:
    """Retorna (permitido, segundos_para_proxima_tentativa)."""
    now = time.monotonic()
    cutoff = now - window_seconds
    with _lock:
        bucket = _buckets.setdefault(key, deque())
        while bucket and bucket[0] < cutoff:
            bucket.popleft()
        if len(bucket) >= limit:
            retry_after = max(0.0, window_seconds - (now - bucket[0]))
            return False, retry_after
        bucket.append(now)
        return True, 0.0


def rate_limit(limit: int, window_seconds: float = 60.0, scope: str | None = None):
    """Decorator que limita chamadas por IP numa janela deslizante.

    Args:
        limit: numero maximo de chamadas permitidas na janela.
        window_seconds: tamanho da janela em segundos.
        scope: rotulo para agrupar rotas no mesmo bucket. Default = nome da view.
    """

    def decorator(view_func):
        bucket_scope = scope or view_func.__name__

        @wraps(view_func)
        def wrapper(*args, **kwargs):
            client = _client_id()
            key = f"{bucket_scope}:{client}"
            allowed, retry_after = _check(key, limit, window_seconds)
            if not allowed:
                logger.warning(
                    "Rate limit excedido scope=%s client=%s retry_after=%.1fs",
                    bucket_scope, client, retry_after,
                )
                response = jsonify({
                    'success': False,
                    'error': 'rate_limit_exceeded',
                    'message': (
                        f'Muitas requisic,oes para esta rota. Tente novamente em '
                        f'{int(retry_after) + 1} segundos.'
                    ),
                    'retry_after_seconds': int(retry_after) + 1,
                })
                response.status_code = 429
                response.headers['Retry-After'] = str(int(retry_after) + 1)
                return response
            return view_func(*args, **kwargs)

        return wrapper

    return decorator
