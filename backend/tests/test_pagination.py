"""Testes unitarios para utils/pagination.py (Phase 7)."""
import pytest
from flask import Flask

from app.utils.pagination import get_limit, get_offset, get_from_line, MAX_LIMIT, MAX_OFFSET


@pytest.fixture
def app():
    app = Flask(__name__)
    return app


def test_get_limit_default(app):
    with app.test_request_context("/?"):
        assert get_limit(default=50) == 50


def test_get_limit_passthrough(app):
    with app.test_request_context("/?limit=123"):
        assert get_limit() == 123


def test_get_limit_clamps_max(app):
    with app.test_request_context(f"/?limit={MAX_LIMIT * 10}"):
        assert get_limit() == MAX_LIMIT


def test_get_limit_rejects_negative(app):
    with app.test_request_context("/?limit=-5"):
        assert get_limit(default=50) == 50


def test_get_limit_rejects_zero(app):
    with app.test_request_context("/?limit=0"):
        assert get_limit(default=50) == 50


def test_get_limit_custom_max(app):
    with app.test_request_context("/?limit=9999"):
        assert get_limit(max_limit=500) == 500


def test_get_offset_default(app):
    with app.test_request_context("/?"):
        assert get_offset() == 0


def test_get_offset_clamps_max(app):
    with app.test_request_context(f"/?offset={MAX_OFFSET * 10}"):
        assert get_offset() == MAX_OFFSET


def test_get_offset_rejects_negative(app):
    with app.test_request_context("/?offset=-100"):
        assert get_offset(default=0) == 0


def test_get_from_line_default(app):
    with app.test_request_context("/?"):
        assert get_from_line() == 0


def test_get_from_line_clamps_max(app):
    with app.test_request_context(f"/?from_line={MAX_OFFSET * 5}"):
        assert get_from_line() == MAX_OFFSET


def test_ddos_protection_huge_limit(app):
    """Garante que limit absurdo nao causa OOM."""
    with app.test_request_context("/?limit=999999999"):
        assert get_limit() == MAX_LIMIT
        assert get_limit() <= 10000
