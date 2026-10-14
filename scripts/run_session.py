"""Run one session end to end against the configured endpoints and save the result.

    uv run python scripts/run_session.py S1 [--gold] [--rounds 3] [--budget 300]

--gold starts from the approved slots instead of extracting (the clean baseline the evaluation injects
errors into). The result is written to runs/<session>-<utc time>.json; keys are never printed.
"""
import argparse
import asyncio
import json
import sys
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout.reconfigure(encoding="utf-8")  # Arabic and Ukrainian on a Windows console

from asprescribed.config import ROOT, settings
from asprescribed.pipeline import gold_items, run_session


async def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("session")
    ap.add_argument("--gold", action="store_true")
    ap.add_argument("--rounds", type=int, default=3)
    ap.add_argument("--budget", type=float, default=None)
    a = ap.parse_args()
    s = settings()
    print(f"mode {s.mode}: generator {s.generator.model or '-'}, falsifier {s.falsifier.model or '-'}")
    r = await run_session(a.session, s.generator, s.falsifier, max_rounds=a.rounds, budget_s=a.budget,
                          items=gold_items(a.session) if a.gold else None)
    print(json.dumps(r.summary(), ensure_ascii=False))
    for line in r.lines:
        print(f"\n[{line.state.value}] {line.item_id}  spans {','.join(line.span_ids)}  rules {line.rule_ids}")
        print(f"  EN   {line.source_en}")
        print(f"  {line.language.upper()}   {line.text}")
        print(f"  BACK {line.back_translation}")
        for o in line.objections:
            print(f"  - {o.kind} ({o.source}): {o.detail}")
    for i in r.heard_not_prescribed:
        print(f"\n[{i.status}] {i.item_id} {i.exercise}")
    out = ROOT / "runs" / f"{a.session}-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps({"summary": r.summary(), "lines": [x.model_dump(mode="json") for x in r.lines],
                               "heard_not_prescribed": [x.model_dump() for x in r.heard_not_prescribed],
                               "rounds": [asdict(x) for x in r.rounds], "notes": r.notes, "calls": r.calls,
                               "models": {"generator": s.generator.model, "falsifier": s.falsifier.model}},
                              ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nsaved {out}")


if __name__ == "__main__":
    asyncio.run(main())
