"""OpenAI-compatible chat client for llama.cpp servers and AMD tokenfactory.

Adapted from somnus shared/llama.py: thinking is switched per endpoint (Qwen takes
chat_template_kwargs, Gemma rejects it), and JSON is recovered defensively because reasoning
models wrap their answer in <think>, cut it short, or repeat it.
"""
import json
import re
import time
from dataclasses import dataclass

import httpx

from .config import Endpoint


class LLMError(RuntimeError):
    pass


@dataclass(frozen=True)
class Completion:
    content: str
    model: str
    completion_tokens: int | None
    seconds: float
    # llama-server reports timings.predicted_per_second; elsewhere tokens / wall time (includes latency).
    tokens_per_s: float | None


async def chat(
    ep: Endpoint,
    messages: list[dict],
    *,
    max_tokens: int = 1024,
    temperature: float = 0.2,
    think: bool = False,
) -> Completion:
    if not ep.configured:
        raise LLMError(f"{ep.role}: endpoint not configured (set {ep.role.upper()}_BASE_URL and _MODEL)")
    payload: dict = {
        "model": ep.model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if ep.thinking_param:
        payload["chat_template_kwargs"] = {"enable_thinking": think}
    headers = {"Authorization": f"Bearer {ep.api_key}"} if ep.api_key else {}
    t0 = time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=ep.timeout_s) as client:
            r = await client.post(f"{ep.base_url}/chat/completions", json=payload, headers=headers)
    except httpx.HTTPError as e:
        raise LLMError(f"{ep.role}: {type(e).__name__}") from e
    seconds = time.perf_counter() - t0
    if r.status_code != 200:
        raise LLMError(f"{ep.role}: HTTP {r.status_code}: {r.text[:200]}")
    data = r.json()
    content = (data["choices"][0]["message"].get("content") or "").strip()
    tokens = (data.get("usage") or {}).get("completion_tokens")
    tps = (data.get("timings") or {}).get("predicted_per_second")
    if tps is None and tokens and seconds > 0:
        tps = tokens / seconds
    return Completion(content=content, model=data.get("model", ep.model), completion_tokens=tokens,
                      seconds=seconds, tokens_per_s=tps)


async def list_models(ep: Endpoint) -> list[str]:
    headers = {"Authorization": f"Bearer {ep.api_key}"} if ep.api_key else {}
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.get(f"{ep.base_url}/models", headers=headers)
    if r.status_code != 200:
        raise LLMError(f"{ep.role}: HTTP {r.status_code} listing models")
    return [m.get("id", "") for m in r.json().get("data", [])]


def extract_json(text: str) -> dict | None:
    """The answer's JSON object, or None. Strips <think> blocks and a cut-short reasoning prefix
    (a closing </think> with no opener), strips code fences, then tries brace spans widest first
    so a nested object wins over its inner objects and a repeated answer falls back to the first."""
    text = re.sub(r"<think>.*?</think>", "", text or "", flags=re.DOTALL)
    if "</think>" in text:
        text = text.rsplit("</think>", 1)[1]
    text = re.sub(r"```(?:json)?", "", text)
    start = text.find("{")
    while start >= 0:
        end = text.rfind("}")
        while end > start:
            try:
                value = json.loads(text[start:end + 1])
                if isinstance(value, dict):
                    return value
            except json.JSONDecodeError:
                pass
            end = text.rfind("}", start, end)
        start = text.find("{", start + 1)
    return None
