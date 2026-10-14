"""List the models each configured endpoint serves, and the tokenfactory catalogue.

    uv run python scripts/models.py

Prints model ids only; keys are read from the environment / .env and never printed.
"""
import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from asprescribed.config import Endpoint, settings
from asprescribed.llm import LLMError, list_models


async def show(ep: Endpoint) -> None:
    if not ep.base_url:
        print(f"{ep.role}: not configured")
        return
    try:
        ids = await list_models(ep)
    except LLMError as e:
        print(f"{ep.role} ({ep.base_url}): {e}")
        return
    except Exception as e:  # noqa: BLE001 - a listing tool reports, it does not crash
        print(f"{ep.role} ({ep.base_url}): {type(e).__name__}")
        return
    print(f"{ep.role} ({ep.base_url}, key {'set' if ep.api_key else 'none'}): {len(ids)} models")
    for i in sorted(ids):
        print(f"  {i}{'   <- configured' if i == ep.model else ''}")


async def main() -> None:
    s = settings()
    tf = os.getenv("TOKENFACTORY_BASE_URL", "").rstrip("/")
    if tf:
        await show(Endpoint("tokenfactory", tf, "", os.getenv("TOKENFACTORY_API_KEY") or None, False, 15.0))
    await show(s.generator)
    await show(s.falsifier)


if __name__ == "__main__":
    asyncio.run(main())
