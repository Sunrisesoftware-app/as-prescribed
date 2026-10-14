"""Record real runs of every demo case through the running app (AP_RECORD=1 on the server), so the public
demo can replay them when no model endpoint is available (AP_REPLAY=1). One case at a time. After a new
recording, update data/recorded/recording.json (date, models, GPUs): the page names the hardware from it.

    uv run python scripts/record.py http://127.0.0.1:8301 [--only S1-live,S2-prescription-E1]
"""
import json
import sys
import time
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout.reconfigure(encoding="utf-8")

from asprescribed.config import DATA_DIR
from asprescribed.evaluation import INJECTIONS


def cases() -> list[tuple[str, dict]]:
    out = []
    for sid in ("S1", "S2", "S3"):
        out.append((f"{sid}-live-clean", {"session": sid, "mode": "live", "speed": "1000"}))
        out.append((f"{sid}-prescription-clean", {"session": sid, "mode": "prescription"}))
    for rid, sid, _, _ in INJECTIONS:
        out.append((f"{sid}-prescription-{rid}", {"session": sid, "mode": "prescription", "injection": rid}))
    return out


def main() -> None:
    base = sys.argv[1].rstrip("/")
    only = set(sys.argv[3].split(",")) if len(sys.argv) > 3 and sys.argv[2] == "--only" else None
    for key, c in cases():
        if only and key not in only:
            continue
        if (DATA_DIR / "recorded" / f"{key}.json").is_file():
            continue
        params = {k: v for k, v in c.items() if k != "session"}
        t0, result, failure = time.time(), None, None
        with httpx.stream("GET", f"{base}/api/sessions/{c['session']}/run", params=params, timeout=600) as r:
            event = None
            for line in r.iter_lines():
                if line.startswith("event: "):
                    event = line[7:]
                elif line.startswith("data: ") and event in ("result", "failure"):
                    data = json.loads(line[6:])
                    result, failure = (data, None) if event == "result" else (None, data["message"])
        states = json.dumps(result["summary"]["states"]) if result else failure
        print(f"{key}: {time.time() - t0:.0f} s, {states}", flush=True)


if __name__ == "__main__":
    main()
