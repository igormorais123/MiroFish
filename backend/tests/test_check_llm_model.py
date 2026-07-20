import importlib.util
import io
import json
import sys
from pathlib import Path

import pytest


SCRIPT_PATH = Path(__file__).parents[1] / "scripts" / "check_llm_model.py"
SPEC = importlib.util.spec_from_file_location("check_llm_model", SCRIPT_PATH)
assert SPEC and SPEC.loader
check_llm_model = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = check_llm_model
SPEC.loader.exec_module(check_llm_model)


class FakeResponse:
    def __init__(self, body, content_type="application/json", status=200):
        self._body = body.encode("utf-8")
        self.headers = {"Content-Type": content_type}
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return self._body


def test_check_model_confirma_luna_sem_expor_chave():
    body = json.dumps(
        {
            "model": "gpt-5.6-luna",
            "choices": [{"message": {"content": check_llm_model.CHECK_MARKER}}],
        }
    )
    captured = {}

    def fake_open(req, timeout):
        captured["authorization"] = req.headers["Authorization"]
        captured["payload"] = json.loads(req.data)
        captured["timeout"] = timeout
        return FakeResponse(body)

    result = check_llm_model.check_model(
        base_url="http://omniroute-inteia:20128/v1",
        api_key="segredo-de-teste",
        requested_model="codex/gpt-5.6-luna",
        expected_model="gpt-5.6-luna",
        opener=fake_open,
    )

    assert result.ok is True
    assert result.effective_model == "gpt-5.6-luna"
    assert captured["authorization"] == "Bearer segredo-de-teste"
    assert captured["payload"]["reasoning_effort"] == "low"
    assert "temperature" not in captured["payload"]


def test_check_model_decodifica_sse_do_codex():
    body = "\n\n".join(
        [
            'data: {"model":"gpt-5.6-luna","choices":[{"delta":{"content":"MIROFISH_"}}]}',
            'data: {"model":"gpt-5.6-luna","choices":[{"delta":{"content":"MODEL_CHECK_OK"}}]}',
            "data: [DONE]",
        ]
    )

    result = check_llm_model.check_model(
        base_url="http://example.test/v1",
        api_key="test",
        requested_model="codex/gpt-5.6-luna",
        expected_model="gpt-5.6-luna",
        opener=lambda *_args, **_kwargs: FakeResponse(body, "text/event-stream"),
    )

    assert result.ok is True
    assert result.content_matches is True


def test_check_model_rejeita_fallback_silencioso():
    body = json.dumps(
        {
            "model": "gpt-5.5",
            "choices": [{"message": {"content": check_llm_model.CHECK_MARKER}}],
        }
    )

    with pytest.raises(check_llm_model.ModelMismatch, match="gpt-5.5"):
        check_llm_model.check_model(
            base_url="http://example.test/v1",
            api_key="test",
            requested_model="codex/gpt-5.6-luna",
            expected_model="gpt-5.6-luna",
            opener=lambda *_args, **_kwargs: FakeResponse(body),
        )


def test_check_model_remove_chave_de_erro_http():
    api_key = "segredo-que-nao-pode-aparecer"

    def fake_open(*_args, **_kwargs):
        raise check_llm_model.error.HTTPError(
            url="http://example.test/v1/chat/completions",
            code=401,
            msg="Unauthorized",
            hdrs={},
            fp=io.BytesIO(f"invalid key: {api_key}".encode()),
        )

    with pytest.raises(check_llm_model.ModelCheckError) as caught:
        check_llm_model.check_model(
            base_url="http://example.test/v1",
            api_key=api_key,
            requested_model="codex/gpt-5.6-luna",
            expected_model="gpt-5.6-luna",
            opener=fake_open,
        )

    assert api_key not in str(caught.value)
    assert "[REDACTED]" in str(caught.value)
