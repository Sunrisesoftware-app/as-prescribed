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
sys.stdout.reconfigure(encoding="utf-8")  # Arabic and Ukrainian on a Windows console

from asprescribed.config import ROOT, settings
from asprescribed.evaluation import (
    extraction_report,
    gates,
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


async def e2e(rounds: int, reps: int) -> None:
    """S1-S3 end to end with extraction: the latency gate, and extraction against the answer key."""
    _, s = load_sealed()
    cfg = settings()
    out_dir = ROOT / "runs" / "eval" / s[:12]
    out_dir.mkdir(parents=True, exist_ok=True)
    for rep in range(1, reps + 1):
        for sid in ("S1", "S2", "S3"):
            path = out_dir / f"e2e-{sid}-{rep}.json"
            if path.exists():
                continue
            result = await run_session(sid, cfg.generator, cfg.falsifier, max_rounds=rounds)
            report = extraction_report(sid, result.items)
            path.write_text(json.dumps({
                "session": sid, "rep": rep, "seconds": round(result.seconds, 1), "summary": result.summary(),
                "extraction": report, "calls": result.calls, "notes": result.notes,
                "lines": [x.model_dump(mode="json") for x in result.lines],
                "models": {"generator": cfg.generator.model, "falsifier": cfg.falsifier.model}},
                ensure_ascii=False, indent=1), encoding="utf-8")
            print(f"e2e {sid} #{rep}: {result.seconds:.0f} s, slots {report['slot_recall']:.2f}, "
                  f"fields {report['field_accuracy']:.2f}, traps {report['traps']}, invented {report['invented']}")


def do_score() -> None:
    _, s = load_sealed()
    folder = ROOT / "runs" / "eval" / s[:12]
    files = sorted(f for f in folder.glob("*.json") if not f.name.startswith("e2e-"))
    e2e_runs = [json.loads(f.read_text(encoding="utf-8")) for f in sorted(folder.glob("e2e-*.json"))]
    data = [json.loads(f.read_text(encoding="utf-8")) for f in files]
    obs = [d["observation"] for d in data if d["observation"]]
    clean = [c for d in data for c in d["clean"]]
    runs = [{"objections_per_round": d["summary"]["objections_per_round"], "seconds": d["summary"]["seconds"],
             "calls": d["calls"]} for d in data]
    sc = score(obs, clean, runs)
    res = {"seal": s, "runs_scored": len(data), "models": data[0]["models"] if data else None, **sc,
           "e2e": [{"session": r["session"], "rep": r["rep"], "seconds": r["seconds"],
                    "slot_recall": r["extraction"]["slot_recall"], "field_accuracy": r["extraction"]["field_accuracy"],
                    "traps": r["extraction"]["traps"], "invented": r["extraction"]["invented"]} for r in e2e_runs],
           "gates": gates(sc, e2e_runs)}
    out = ROOT / "eval" / f"results-{s[:12]}.json"
    out.write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(res, ensure_ascii=False, indent=1))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["plan", "run", "e2e", "score"])
    ap.add_argument("--only", default="")
    ap.add_argument("--rounds", type=int, default=3)
    ap.add_argument("--reps", type=int, default=1)
    a = ap.parse_args()
    if a.cmd == "plan":
        s = write_plan(PLAN)
        print(f"wrote {PLAN.relative_to(ROOT)}\nsha256 {s}\nRecord it in eval/SEAL and the ENNAKKO before any run.")
    elif a.cmd == "run":
        asyncio.run(run({x for x in a.only.split(",") if x} or None, a.rounds))
    elif a.cmd == "e2e":
        asyncio.run(e2e(a.rounds, a.reps))
    else:
        do_score()


if __name__ == "__main__":
    main()
