"""Transcript ingest: a session is JSON lines of spans, streamed in chunks as if the visit were
happening now (handoff D1). Any speech-to-text can feed the same shape; speech recognition is
out of scope."""
import asyncio
import json
from collections.abc import AsyncIterator, Iterable
from pathlib import Path

from .config import DATA_DIR
from .schemas import Span

SESSIONS_DIR = DATA_DIR / "sessions"


def load_spans(path: Path) -> list[Span]:
    spans = []
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            spans.append(Span.model_validate(json.loads(line)))
        except Exception as e:
            raise ValueError(f"{path.name}:{n}: {e}") from e
    ids = [s.span_id for s in spans]
    if len(ids) != len(set(ids)):
        raise ValueError(f"{path.name}: duplicate span_id")
    return spans


def session_path(session_id: str) -> Path:
    if not session_id.isalnum():
        raise ValueError("session id must be alphanumeric")
    return SESSIONS_DIR / f"{session_id}.transcript.jsonl"


def chunks(spans: Iterable[Span], size: int) -> list[list[Span]]:
    spans = list(spans)
    return [spans[i:i + size] for i in range(0, len(spans), size)]


async def stream(spans: list[Span], *, size: int = 4, speed: float = 0.0) -> AsyncIterator[list[Span]]:
    """Yield chunks of spans. speed > 0 replays in real time divided by speed (speed 10 = ten times
    faster than the visit); 0 yields as fast as the consumer reads."""
    prev_ts = 0.0
    for chunk in chunks(spans, size):
        if speed > 0:
            await asyncio.sleep(max(0.0, (chunk[-1].ts - prev_ts) / speed))
            prev_ts = chunk[-1].ts
        yield chunk
