"""The chat client against a mock transport: a short 429 is retried, a long one is not."""
import httpx
import pytest

from asprescribed import llm
from asprescribed.config import Endpoint

EP = Endpoint("generator", "https://tf.example/v1", "m", "k", False, 10.0)
OK = {"choices": [{"message": {"content": "{}"}}], "usage": {"completion_tokens": 1}, "model": "m"}


def _client(monkeypatch, answers: list[httpx.Response]) -> list[int]:
    seen = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(len(seen))
        return answers.pop(0)

    real = httpx.AsyncClient
    monkeypatch.setattr(llm.httpx, "AsyncClient", lambda **kw: real(transport=httpx.MockTransport(handler), **kw))
    return seen


async def test_a_short_429_is_retried(monkeypatch):
    seen = _client(monkeypatch, [httpx.Response(429, headers={"retry-after": "0"}), httpx.Response(200, json=OK)])
    c = await llm.chat(EP, [{"role": "user", "content": "x"}])
    assert c.content == "{}" and len(seen) == 2


async def test_a_long_429_is_not_retried_so_the_run_can_fall_back(monkeypatch):
    seen = _client(monkeypatch, [httpx.Response(429, headers={"retry-after": "60"}, text="slow down")])
    with pytest.raises(llm.LLMError, match="HTTP 429"):
        await llm.chat(EP, [{"role": "user", "content": "x"}])
    assert len(seen) == 1


async def test_retries_stop_after_the_last_attempt(monkeypatch):
    seen = _client(monkeypatch, [httpx.Response(503, headers={"retry-after": "0"})] * llm.MAX_ATTEMPTS)
    with pytest.raises(llm.LLMError, match="HTTP 503"):
        await llm.chat(EP, [{"role": "user", "content": "x"}])
    assert len(seen) == llm.MAX_ATTEMPTS


def test_a_client_error_is_final():
    assert llm.retry_wait(httpx.Response(400), 1) is None
