"""Testes do decorador retry_with_backoff e RetryableAPIClient (Phase 10)."""
from __future__ import annotations

import pytest

from app.utils.retry import RetryableAPIClient, retry_with_backoff


class FakyError(Exception):
    pass


def test_retry_succeeds_on_first_call():
    calls = {"n": 0}

    @retry_with_backoff(max_retries=3, initial_delay=0.0, jitter=False)
    def f():
        calls["n"] += 1
        return "ok"

    assert f() == "ok"
    assert calls["n"] == 1


def test_retry_recovers_after_transient_failures():
    calls = {"n": 0}

    @retry_with_backoff(max_retries=3, initial_delay=0.0, jitter=False, exceptions=(FakyError,))
    def f():
        calls["n"] += 1
        if calls["n"] < 3:
            raise FakyError("transient")
        return "recovered"

    assert f() == "recovered"
    assert calls["n"] == 3


def test_retry_raises_after_max_retries_exceeded():
    @retry_with_backoff(max_retries=2, initial_delay=0.0, jitter=False, exceptions=(FakyError,))
    def f():
        raise FakyError("permanent")

    with pytest.raises(FakyError, match="permanent"):
        f()


def test_retry_does_not_retry_other_exceptions():
    """Excecoes fora de `exceptions` devem subir imediatamente."""
    calls = {"n": 0}

    @retry_with_backoff(max_retries=5, initial_delay=0.0, jitter=False, exceptions=(FakyError,))
    def f():
        calls["n"] += 1
        raise ValueError("nao deve retry")

    with pytest.raises(ValueError):
        f()
    assert calls["n"] == 1


def test_retry_callback_invoked_on_each_retry():
    calls = []

    def cb(e, attempt):
        calls.append((str(e), attempt))

    @retry_with_backoff(max_retries=2, initial_delay=0.0, jitter=False, exceptions=(FakyError,), on_retry=cb)
    def f():
        raise FakyError("boom")

    with pytest.raises(FakyError):
        f()
    assert len(calls) == 2  # 2 retries -> 2 callback invocations


def test_retryable_api_client_call_with_retry_recovers():
    client = RetryableAPIClient(max_retries=3, initial_delay=0.0)
    calls = {"n": 0}

    def f():
        calls["n"] += 1
        if calls["n"] < 2:
            raise FakyError("once")
        return "ok"

    assert client.call_with_retry(f, exceptions=(FakyError,)) == "ok"
    assert calls["n"] == 2


def test_retryable_api_client_batch_continues_on_failure():
    client = RetryableAPIClient(max_retries=1, initial_delay=0.0)

    def process(item):
        if item == "bad":
            raise FakyError("bad item")
        return item.upper()

    items = ["alpha", "bad", "gamma"]
    results, failures = client.call_batch_with_retry(items, process, exceptions=(FakyError,), continue_on_failure=True)

    assert results == ["ALPHA", "GAMMA"]
    assert len(failures) == 1
    assert failures[0]["item"] == "bad"
    assert failures[0]["index"] == 1


def test_retryable_api_client_batch_stops_when_continue_false():
    client = RetryableAPIClient(max_retries=0, initial_delay=0.0)

    def process(item):
        if item == "bad":
            raise FakyError("bad item")
        return item

    with pytest.raises(FakyError):
        client.call_batch_with_retry(["a", "bad", "c"], process, exceptions=(FakyError,), continue_on_failure=False)
