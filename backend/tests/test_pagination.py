"""Testes de utilitarios de paginacao (Phase 10)."""
from __future__ import annotations

import pytest
from flask import Flask

from app.utils.pagination import (
    MAX_LIMIT,
    MAX_OFFSET,
    get_from_line,
    get_limit,
    get_offset,
)


@pytest.fixture
def app_ctx():
    return Flask(__name__)


def _with_args(app, **args):
    qs = "&".join(f"{k}={v}" for k, v in args.items())
    return app.test_request_context(f"/?{qs}")


def test_get_limit_default_quando_ausente(app_ctx):
    with app_ctx.test_request_context("/"):
        assert get_limit() == 50
        assert get_limit(default=10) == 10


def test_get_limit_aceita_valor_valido(app_ctx):
    with _with_args(app_ctx, limit=100):
        assert get_limit() == 100


def test_get_limit_clamps_acima_do_max(app_ctx):
    with _with_args(app_ctx, limit=999999):
        assert get_limit() == MAX_LIMIT
    with _with_args(app_ctx, limit=20000):
        assert get_limit(max_limit=15000) == 15000


def test_get_limit_rejeita_negativo_e_zero(app_ctx):
    with _with_args(app_ctx, limit=-5):
        assert get_limit(default=42) == 42
    with _with_args(app_ctx, limit=0):
        assert get_limit(default=42) == 42


def test_get_offset_default_e_clamp(app_ctx):
    with app_ctx.test_request_context("/"):
        assert get_offset() == 0
    with _with_args(app_ctx, offset=200):
        assert get_offset() == 200
    with _with_args(app_ctx, offset=99999999):
        assert get_offset() == MAX_OFFSET


def test_get_offset_negativo_volta_pro_default(app_ctx):
    with _with_args(app_ctx, offset=-3):
        assert get_offset(default=7) == 7


def test_get_from_line_se_comporta_como_offset(app_ctx):
    with _with_args(app_ctx, from_line=42):
        assert get_from_line() == 42
    with _with_args(app_ctx, from_line=99999999):
        assert get_from_line() == MAX_OFFSET
    with _with_args(app_ctx, from_line=-1):
        assert get_from_line(default=5) == 5


def test_constantes_publicas_nao_diminuiram():
    assert MAX_LIMIT >= 10000
    assert MAX_OFFSET >= 1_000_000
