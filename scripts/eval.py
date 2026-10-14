"""The pre-registered evaluation.

    uv run python scripts/eval.py plan            # write eval/plan-v1.json and print its sha256 (the seal)
    uv run python scripts/eval.py run [--only A1,B3] [--rounds 3]
    uv run python scripts/eval.py score           # eval/results-<seal>.json

run refuses to start when eval/plan-v1.json no longer matches the seal recorded in eval/SEAL, and it
resumes: a run whose result file exists is skipped. Results live in runs/eval/<seal>/<run>.json.
"""
import argparse
import asyncio
import json
import sys
from dataclasses import asdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from asprescribed.config import ROOT, settings
from asprescribed.evaluation import (
    injected_items,
    mutate_translation,
    observe,
    score,
    seal,
    write_plan,
)
from asprescribed.pipeline import run_session

PLAN = ROOT / "eval" / "plan-v1.json"
SEAL = ROOT / "eval" / "SEAL"


def load_sealed() -> tuple[dict, str]:
    p = json.loads(PLAN.read_text(encoding="utf-8"))
    s = seal(p)
    recorded = SEAL.read_text(encoding="utf-8").split()[0] if SEAL.exists() else None
    if recorded != s:
        sys.exit(f"plan does not match the seal (plan {s[:12]}, SEAL {recorded and recorded[:12]}): refusing")
    return p, s


async def run(only: set[str] | None, rounds: int) -> None:
    p, s = load_sealed()
    cfg = settings()
    out_dir = ROOT / "runs" / "eval" / s[:12]
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"plan {s[:12]}: generator {cfg.generator.model}, falsifier {cfg.falsifier.model}")
    for r in p["runs"]:
        if only and r["run"] not in only:
            continue
        path = out_dir / f"{r['run']}.json"
        if path.exists():
            continue
        inj = r["injection"]
        applied = {"value": True}
        hook = None
        if inj and inj["op"] == "translation":
            def hook(iid, text, inj=inj, applied=applied):
                if iid != inj["item_id"]:
                    return text
                new = mutate_translation(inj["how"], text)
                applied["value"] = new is not None
                return new if new is not None else text
        result = await run_session(r["session"], cfg.generator, cfg.falsifier, max_rounds=rounds,
                                   items=injected_items(r), translation_hook=hook)
        obs, clean = observe(r, result, injected=applied["value"])
        path.write_text(json.dumps({
            "run": r["run"], "summary": result.summary(), "observation": asdict(obs) if obs else None,
            "clean": clean, "lines": [x.model_dump(mode="json") for x in result.lines],
            "rounds": [asdict(x) for x in result.rounds], "calls": result.calls, "notes": result.notes,
            "models": {"generator": cfg.generator.model, "falsifier": cfg.falsifier.model}},
            ensure_ascii=False, indent=1), encoding="utf-8")
        o = f"detected={obs.detected} final={obs.final_state}" if obs else "clean"
        print(f"{r['run']} {r['session']} {r['type']}: {o} ({result.seconds:.0f} s)")


def do_score() -> None:
    _, s = load_sealed()
    files = sorted((ROOT / "runs" / "eval" / s[:12]).glob("*.json"))
    data = [json.loads(f.read_text(encoding="utf-8")) for f in files]
    obs = [d["observation"] for d in data if d["observation"]]
    clean = [c for d in data for c in d["clean"]]
    runs = [{"objections_per_round": d["summary"]["objections_per_round"], "seconds": d["summary"]["seconds"],
             "calls": d["calls"]} for d in data]
    res = {"seal": s, "runs_scored": len(data), "models": data[0]["models"] if data else None,
           **score(obs, clean, runs)}
    out = ROOT / "eval" / f"results-{s[:12]}.json"
    out.write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(res, ensure_ascii=False, indent=1))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["plan", "run", "score"])
    ap.add_argument("--only", default="")
    ap.add_argument("--rounds", type=int, default=3)
    a = ap.parse_args()
    if a.cmd == "plan":
        s = write_plan(PLAN)
        print(f"wrote {PLAN.relative_to(ROOT)}\nsha256 {s}\nRecord it in eval/SEAL and the ENNAKKO before any run.")
    elif a.cmd == "run":
        asyncio.run(run({x for x in a.only.split(",") if x} or None, a.rounds))
    else:
        do_score()


if __name__ == "__main__":
    main()
