"""Autenticacao compartilhada das superficies internas do MiroFish."""

from __future__ import annotations

import hmac
from functools import wraps

from flask import jsonify, request

from ..config import Config
from .logger import get_logger

logger = get_logger("mirofish.internal_auth")


def unauthorized_response():
    return jsonify({
        "success": False,
        "error": "Nao autorizado para a API interna",
    }), 401


def require_internal_token(view_func):
    """Exige o token interno sem expor diferencas de tempo na comparacao."""

    @wraps(view_func)
    def wrapper(*args, **kwargs):
        expected_token = (Config.INTERNAL_API_TOKEN or "").strip()
        provided_token = request.headers.get("X-Internal-Token", "").strip()

        if not expected_token:
            logger.warning("INTERNAL_API_TOKEN nao configurado; acesso interno bloqueado")
            return unauthorized_response()

        if not provided_token or not hmac.compare_digest(provided_token, expected_token):
            logger.warning("Tentativa de acesso interno com token invalido")
            return unauthorized_response()

        return view_func(*args, **kwargs)

    return wrapper
