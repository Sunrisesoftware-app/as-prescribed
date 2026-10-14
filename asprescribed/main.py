"""FastAPI app. In public mode it serves only the synthetic sessions S1-S3 (handoff D16): there is
no free-text input, so no real patient data can be pasted, and nothing is logged."""
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from . import __version__
from .config import settings
from .web import router

STATIC = Path(__file__).resolve().parent / "static"

app = FastAPI(title="As Prescribed", version=__version__, docs_url=None, redoc_url=None)
app.include_router(router)
app.mount("/static", StaticFiles(directory=STATIC), name="static")


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


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC / "index.html")


@app.get("/patient")
def patient() -> FileResponse:
    return FileResponse(STATIC / "patient.html")
