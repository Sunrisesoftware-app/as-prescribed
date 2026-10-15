"""The video's recording stage: a 1920x1080 page with the desk on the left and the box's GPUs on the right.

    uv run python scripts/video/stage.py [--port 8400] [--app http://localhost:8300] [--fake-gpu]

Serves stage.html and /gpu, the latest rocm-smi reading of the Somnus box's two Radeon cards plus a minute of
history, streamed over ssh once a second (read only). --fake-gpu makes idle-looking numbers up, for trying the
stage without the box. Used only to record the demo video; not part of the app.
"""
import argparse
import json
import random
import subprocess
import sys
import threading
import time
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
BOX = "sf3d@100.120.156.99"
# rocm-smi's card ids on the box (checked 15.10.2026) and what runs on each in local mode.
CARDS = {
    "card1": {"name": "AMD Radeon AI PRO R9700", "role": "Generator", "model": "Qwen3.5-35B-A3B"},
    "card0": {"name": "AMD Radeon RX 7900 XT", "role": "Falsifier", "model": "Gemma 3 12B"},
}
HISTORY_S = 60

state = {"at": 0.0, "source": "none", "cards": {k: deque(maxlen=HISTORY_S) for k in CARDS}}
lock = threading.Lock()


def _num(v) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def record(reading: dict, source: str) -> None:
    with lock:
        state["at"], state["source"] = time.time(), source
        for card in CARDS:
            r = reading.get(card, {})
            state["cards"][card].append({
                "use": _num(r.get("GPU use (%)")),
                "vram": _num(r.get("GPU Memory Allocated (VRAM%)")),
                "power": _num(r.get("Average Graphics Package Power (W)")),
            })


def stream_box() -> None:
    """One ssh session that prints a rocm-smi reading a second; reconnects if it drops."""
    loop = "while true; do rocm-smi --showuse --showmemuse --showpower --json 2>/dev/null; sleep 1; done"
    while True:
        p = subprocess.Popen(["ssh", "-o", "BatchMode=yes", "-o", "ServerAliveInterval=10", BOX, loop],
                             stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
        for line in p.stdout:
            line = line.strip()
            if line.startswith("{"):
                try:
                    record(json.loads(line), "box")
                except json.JSONDecodeError:
                    pass
        p.wait()
        time.sleep(2)


def fake_gpu() -> None:
    while True:
        record({c: {"GPU use (%)": random.choice([0, 0, 1, 3]), "GPU Memory Allocated (VRAM%)": v,
                    "Average Graphics Package Power (W)": 12 + random.random() * 3}
                for c, v in (("card1", 73), ("card0", 45))}, "fake")
        time.sleep(1)


class Handler(BaseHTTPRequestHandler):
    def _send(self, body: bytes, kind: str) -> None:
        self.send_response(200)
        self.send_header("Content-Type", kind)
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.startswith("/gpu"):
            with lock:
                body = {"at": state["at"], "source": state["source"],
                        "cards": [{"id": c, **CARDS[c], "history": list(state["cards"][c])} for c in CARDS]}
            self._send(json.dumps(body).encode(), "application/json")
        elif self.path == "/" or self.path.startswith("/?"):
            html = (HERE / "stage.html").read_text(encoding="utf-8").replace("{{APP}}", self.server.app)
            self._send(html.encode("utf-8"), "text/html; charset=utf-8")
        else:
            self.send_error(404)

    def log_message(self, *args):
        pass


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8400)
    ap.add_argument("--app", default="http://localhost:8300/?speed=15")
    ap.add_argument("--fake-gpu", action="store_true")
    a = ap.parse_args()
    threading.Thread(target=fake_gpu if a.fake_gpu else stream_box, daemon=True).start()
    srv = ThreadingHTTPServer(("127.0.0.1", a.port), Handler)
    srv.app = a.app
    print(f"stage on http://127.0.0.1:{a.port}/ ({'fake' if a.fake_gpu else 'box'} GPUs, app {a.app})", flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()
