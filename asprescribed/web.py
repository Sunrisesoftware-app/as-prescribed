"""The views' API: the sessions, and one streamed run per click (server-sent events).

Two ways to run a session:
- live: the transcript is replayed in visit time (divided by speed) while the generator extracts the
  program during the visit; the falsification rounds start when the last chunk arrives, and the
  latency from that moment is reported.
- prescription: start from the approved slots, optionally with one of the evaluation's injected errors,
  so a judge can see whether the falsifier catches it (handoff D16).

One model run at a time (the Somnus box has 16 GB of host RAM and the endpoints are shared); identical
runs are served from a short cache, and a recorded run (data/recorded) is served when no model answers,
always labelled as such. Nothing about the session is logged.
"""
import asyncio
import json
import os
import time
from collections import Counter
from dataclasses import asdict
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from .config import DATA_DIR, Settings, settings
from .evaluation import INJECTIONS, injected_items, mutate_translation, observe
from .extract import extract
from .ingest import chunks, load_spans, session_path
from .llm import LLMError, chat
from .pipeline import SessionResult, gold_items, run_session
from .program import profile_for
from .rules import load_catalog

router = APIRouter(prefix="/api")
RECORDED = DATA_DIR / "recorded"
_lock = asyncio.Lock()
_cache: dict[str, tuple[float, dict]] = {}

INJECTION_LABELS = {
    "wrong_dose_or_frequency": "Change a dose or how often",
    "wrong_side": "Swap the side",
    "invented_item": "Add an exercise nobody prescribed",
    "dropped_caution": "Drop the therapist's caution",
    "contraindicated": "Add an exercise a documented restriction blocks",
    "mistranslation": "Corrupt the translation",
}


def _slots(sid: str) -> dict:
    return json.loads((DATA_DIR / "sessions" / f"{sid}.slots.json").read_text(encoding="utf-8"))


def _conditions() -> dict[str, dict]:
    return {c["id"]: c for c in json.loads((DATA_DIR / "rules.json").read_text(encoding="utf-8"))["conditions"]}


def recording() -> dict | None:
    """When, with which models and on which GPUs the recorded runs were made (data/recorded/recording.json),
    so a replayed run names the hardware it came from."""
    path = RECORDED / "recording.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else None


def _describe(inj: dict) -> str:
    if inj["op"] == "translation":
        return {"change_number": "a number", "swap_side": "left and right swapped",
                "drop_last_sentence": "the last sentence dropped"}[inj["how"]] + f" in {inj['item_id']}"
    if inj["op"] == "add":
        f = inj["fields"]
        return f"adds {load_catalog()[f['exercise_id']]['en']}" + (f" ({f['side']})" if f.get("side") else "")
    return f"{inj['item_id']}: " + ", ".join(f"{k} {v if v else 'removed'}" for k, v in inj["fields"].items())


def budget() -> float | None:
    """Seconds a live run may take after the visit before the recording is served instead (AP_LIVE_BUDGET_S;
    unset or 0: no limit). A shared cloud endpoint under load took 36 s one evening and 176 s the next morning."""
    v = float(os.getenv("AP_LIVE_BUDGET_S", "0") or 0)
    return v if v > 0 else None


def where(cfg: Settings) -> str:
    """Where a live run's models run, for the page."""
    if cfg.mode == "local":
        return "the clinic’s own AMD Radeon GPUs (local mode)"
    tf = os.getenv("TOKENFACTORY_BASE_URL", "").rstrip("/")
    return "AMD Radeon Cloud (Token Factory)" if tf and cfg.generator.base_url.startswith(tf) else "a hosted endpoint"


def clinic(key: str, payload: dict) -> dict | None:
    """The same case as recorded on the clinic hardware, against this cloud run: the line states, and for an
    injected error whether each caught it. Only for a run that did not itself run on the clinic's cards."""
    path = RECORDED / f"{key}.json"
    if payload.get("models", {}).get("mode") != "public" or not path.is_file():
        return None
    rec = json.loads(path.read_text(encoding="utf-8"))
    here, there = Counter(x["state"] for x in payload["lines"]), Counter(x["state"] for x in rec["lines"])
    out = {"recording": recording(), "states": dict(here), "recorded_states": dict(there), "same_states": here == there}
    if payload.get("injection") and rec.get("injection"):
        out["caught"] = payload["injection"]["observation"]["detected"]
        out["recorded_caught"] = rec["injection"]["observation"]["detected"]
    return out


@router.get("/demo")
def demo() -> dict:
    """What the page says before any run: whether this server replays recorded runs or runs live (and where),
    and where the recordings were made."""
    replay, cfg = os.getenv("AP_REPLAY") == "1", settings()
    live = None if replay or not cfg.generator.configured else {
        "mode": cfg.mode, "where": where(cfg), "generator": cfg.generator.model, "falsifier": cfg.falsifier.model}
    return {"replay": replay, "live": live, "recording": recording()}


@router.get("/sessions")
def sessions() -> list[dict]:
    out = []
    for sid in sorted(p.name.split(".")[0] for p in (DATA_DIR / "sessions").glob("*.transcript.jsonl")):
        slots, profile = _slots(sid), profile_for(sid)
        out.append({"id": sid, "language": profile.language, "demonstrates": slots["demonstrates"]})
    return out


@router.get("/sessions/{sid}")
def session(sid: str) -> dict:
    try:
        path = session_path(sid)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    if not path.is_file():
        raise HTTPException(404, "no such session")
    profile, cond = profile_for(sid), _conditions()
    return {
        "id": sid, "language": profile.language, "demonstrates": _slots(sid)["demonstrates"],
        "profile": {"id": profile.profile_id, "summary": profile.summary,
                    "conditions": [{"id": c, "en": cond[c]["en"]} for c in profile.conditions]},
        "transcript": [s.model_dump() for s in load_spans(path)],
        "injections": [{"id": rid, "type": t, "label": INJECTION_LABELS[t], "detail": _describe(inj)}
                       for rid, s, t, inj in INJECTIONS if s == sid],
    }


def _payload(result: SessionResult, *, extra: dict) -> dict:
    cfg = settings()
    tps = {role: [c["tokens_per_s"] for c in calls if c.get("tokens_per_s")] for role, calls in result.calls.items()}
    return {
        "summary": result.summary(), "lines": [x.model_dump(mode="json") for x in result.lines],
        "heard_not_prescribed": [x.model_dump() for x in result.heard_not_prescribed],
        "rounds": [asdict(r) for r in result.rounds], "notes": result.notes,
        "models": {"mode": cfg.mode, "generator": cfg.generator.model, "falsifier": cfg.falsifier.model,
                   "where": where(cfg)},
        "tokens_per_s": {role: round(sorted(v)[len(v) // 2], 1) for role, v in tps.items() if v},
        "calls": {role: len(v) for role, v in result.calls.items()},
        **extra,
    }


def _sse(kind: str, data: dict) -> str:
    return f"event: {kind}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


async def _drive(q: asyncio.Queue, request: Request, sid: str, mode: str, injection: str | None,
                 speed: float) -> None:
    chat_fn = getattr(request.app.state, "chat_fn", chat)
    cfg = settings()
    key = f"{sid}-{mode}-{injection or 'clean'}"
    spans = load_spans(session_path(sid))
    run = None
    if injection:
        run = next(({"run": rid, "session": s, "type": t, "injection": inj} for rid, s, t, inj in INJECTIONS
                    if rid == injection and s == sid), None)
        if run is None:
            await q.put(("failure", {"message": f"unknown injection {injection} for {sid}"}))
            return

    async def emit(kind: str, data: dict) -> None:
        await q.put(("stage", {"stage": kind, **data}))

    recorded = RECORDED / f"{key}.json"
    if os.getenv("AP_REPLAY") == "1":
        # Replay only: serve the recorded run without calling a model (the public demo while no hosted
        # endpoint is available). The view labels it as recorded.
        if not recorded.is_file():
            await q.put(("failure", {"message": "No recorded run exists for this case, and live models are off."}))
            return
        if mode == "live":
            for chunk in chunks(spans, 3):
                await asyncio.sleep(max(0.0, (chunk[-1].ts - chunk[0].ts + 4) / speed))
                for s in chunk:
                    await q.put(("span", s.model_dump()))
        await q.put(("result", {**json.loads(recorded.read_text(encoding="utf-8")), "recorded": True,
                                "replay": True, "recording": recording()}))
        return

    ttl = float(os.getenv("AP_CACHE_S", "1800"))
    hit = _cache.get(key)
    if hit and time.time() - hit[0] < ttl:
        if mode == "live":
            for chunk in chunks(spans, 3):
                await asyncio.sleep(min(2.0, (chunk[-1].ts - chunk[0].ts + 4) / speed))
                for s in chunk:
                    await q.put(("span", s.model_dump()))
        await q.put(("result", {**hit[1], "cached_at": hit[0], "clinic": clinic(key, hit[1])}))
        return

    if _lock.locked():
        await q.put(("queued", {"message": "another run is using the models; this one starts when it ends"}))
    async with _lock:
        try:
            if mode == "live":
                items, done = [], 0
                task: asyncio.Task | None = None
                seen = []

                async def run_extract(prefix):
                    nonlocal items, done
                    ex = await extract(prefix, items, cfg.generator, chat_fn=chat_fn)
                    items, done = ex.items, len(prefix)
                    await q.put(("items", {"upto": prefix[-1].span_id,
                                           "items": [i.model_dump() for i in items]}))

                prev = 0.0
                for chunk in chunks(spans, 3):
                    await asyncio.sleep(max(0.0, (chunk[-1].ts - prev) / speed))
                    prev = chunk[-1].ts
                    seen += chunk
                    for s in chunk:
                        await q.put(("span", s.model_dump()))
                    if any(s.speaker == "therapist" for s in chunk) and (task is None or task.done()):
                        task = asyncio.create_task(run_extract(list(seen)))
                t_last = time.perf_counter()
                await q.put(("stage", {"stage": "visit_ended"}))

                async def after_visit():
                    if task:
                        await task
                    if done < len(seen):
                        await run_extract(list(seen))
                    return await run_session(sid, cfg.generator, cfg.falsifier, chat_fn=chat_fn, items=items,
                                             on_event=emit)

                result = await asyncio.wait_for(after_visit(), budget())
                payload = _payload(result, extra={"mode": mode,
                                                  "latency_after_last_chunk_s": round(time.perf_counter() - t_last, 1)})
            else:
                hook, applied = None, {"value": True}
                if run and run["injection"]["op"] == "translation":
                    inj = run["injection"]

                    def hook(iid, text):
                        if iid != inj["item_id"]:
                            return text
                        new = mutate_translation(inj["how"], text)
                        applied["value"] = new is not None
                        return new if new is not None else text
                items = injected_items(run) if run else gold_items(sid)
                result = await asyncio.wait_for(run_session(sid, cfg.generator, cfg.falsifier, chat_fn=chat_fn,
                                                            items=items, translation_hook=hook, on_event=emit),
                                                budget())
                extra = {"mode": mode, "seconds": round(result.seconds, 1)}
                if run:
                    obs, _ = observe(run, result, injected=applied["value"])
                    extra["injection"] = {"id": run["run"], "type": run["type"], "label": INJECTION_LABELS[run["type"]],
                                          "detail": _describe(run["injection"]), "observation": asdict(obs)}
                payload = _payload(result, extra=extra)
        except (LLMError, TimeoutError) as e:
            slow = isinstance(e, TimeoutError)
            recorded = RECORDED / f"{key}.json"
            if recorded.is_file():
                await q.put(("result", {**json.loads(recorded.read_text(encoding="utf-8")), "recorded": True,
                                        "recording": recording(), "fallback": "slow" if slow else "error",
                                        "budget_s": budget()}))
            else:
                why = f"did not finish within {budget():.0f} s" if slow else f"did not answer ({e})"
                await q.put(("failure", {"message": f"The model endpoint {why}. No recorded run exists for this case."}))
            return
    _cache[key] = (time.time(), payload)
    if os.getenv("AP_RECORD") == "1":
        RECORDED.mkdir(exist_ok=True)
        Path(RECORDED / f"{key}.json").write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    await q.put(("result", {**payload, "clinic": clinic(key, payload)}))


@router.get("/sessions/{sid}/run")
async def run(sid: str, request: Request, mode: str = "prescription", injection: str = "",
              speed: float = 12.0) -> StreamingResponse:
    try:
        path = session_path(sid)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    if not path.is_file():
        raise HTTPException(404, "no such session")
    if mode not in ("live", "prescription"):
        raise HTTPException(400, "mode is live or prescription")
    if injection and mode != "prescription":
        raise HTTPException(400, "errors are injected into the approved prescription, not the live replay")
    speed = min(max(speed, 1.0), 1000.0)
    q: asyncio.Queue = asyncio.Queue()

    async def body():
        task = asyncio.create_task(_drive(q, request, sid, mode, injection or None, speed))
        try:
            while True:
                if task.done() and q.empty():
                    if task.exception():
                        yield _sse("failure", {"message": "the run failed: " + type(task.exception()).__name__})
                    yield _sse("end", {})
                    return
                try:
                    kind, data = await asyncio.wait_for(q.get(), timeout=15)
                except TimeoutError:
                    yield ": keep-alive\n\n"
                    continue
                yield _sse(kind, data)
        finally:
            if not task.done():
                task.cancel()

    return StreamingResponse(body(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
