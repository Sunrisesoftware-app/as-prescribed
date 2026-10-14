"""FastAPI app. In public mode it serves only the synthetic sessions S1-S3 (handoff D16): there is
no free-text input, so no real patient data can be pasted, and nothing is logged."""
from fastapi import FastAPI, HTTPException

from . import __version__
from .config import settings
from .ingest import SESSIONS_DIR, load_spans, session_path

app = FastAPI(title="As Prescribed", version=__version__)


@app.get("/health")
def health() -> dict:
    s = settings()
    return {
        "status": "ok",
        "version": __version__,
        "mode": s.mode,
        "generator": {"configured": s.generator.configured, "model": s.generator.model},
        "falsifier": {"configured": s.falsifier.configured, "model": s.falsifier.model},
    }


@app.get("/api/sessions")
def sessions() -> list[str]:
    return sorted(p.name.split(".")[0] for p in SESSIONS_DIR.glob("*.transcript.jsonl"))


@app.get("/api/sessions/{session_id}/transcript")
def transcript(session_id: str) -> list[dict]:
    try:
        path = session_path(session_id)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    if not path.is_file():
        raise HTTPException(404, "no such session")
    return [s.model_dump() for s in load_spans(path)]
