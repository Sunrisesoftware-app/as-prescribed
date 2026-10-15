"""Record the demo video's scenes with a scripted browser (Edge), frame by frame.

    uv run python scripts/video/stage.py &                      # the stage: desk + the box's GPUs
    uv run --with playwright python scripts/video/record.py [--out video] [scene ...]

Each scene drives the desk inside the stage (docs/submission/video.md has the script). Frames come from the
DevTools screencast (JPEG, 1920x1080) with their timestamps, and ffmpeg turns them into an MP4 at 30 fps with
the timing kept. The moments that matter (visit ended, result shown) go to <scene>.events.json, so the
assembly can speed up the waits. Used only to make the demo video; not part of the app.
"""
import argparse
import asyncio
import base64
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

from playwright.async_api import Frame, Page, async_playwright

ROOT = Path(__file__).resolve().parents[2]
FFMPEG = shutil.which("ffmpeg") or "C:/ffmpeg/bin/ffmpeg.exe"
PUBLIC = "https://asprescribed.sunrisesoftware.app/"


class Capture:
    """The DevTools screencast of one page, kept as timestamped JPEG frames for one scene."""

    def __init__(self, page: Page, out: Path, name: str):
        self.page, self.dir, self.name = page, out / f"{name}.frames", name
        self.frames: list[tuple[float, str]] = []
        self.events: list[tuple[float, str]] = []

    async def __aenter__(self):
        shutil.rmtree(self.dir, ignore_errors=True)
        self.dir.mkdir(parents=True)
        self.cdp = await self.page.context.new_cdp_session(self.page)
        self.cdp.on("Page.screencastFrame", self._frame)
        await self.cdp.send("Page.startScreencast", {"format": "jpeg", "quality": 92, "maxWidth": 1920,
                                                     "maxHeight": 1080, "everyNthFrame": 1})
        self.t0 = time.time()
        return self

    def _frame(self, p: dict) -> None:
        path = self.dir / f"f{len(self.frames):06d}.jpg"
        path.write_bytes(base64.b64decode(p["data"]))
        self.frames.append((p["metadata"].get("timestamp") or time.time(), path.name))
        asyncio.ensure_future(self.cdp.send("Page.screencastFrameAck", {"sessionId": p["sessionId"]}))

    def mark(self, label: str) -> None:
        self.events.append((time.time(), label))
        print(f"  {self.name}: {label} at {time.time() - self.t0:.1f} s", flush=True)

    async def __aexit__(self, *exc):
        await self.cdp.send("Page.stopScreencast")
        await asyncio.sleep(0.3)
        end = time.time()
        if not self.frames:
            print(f"  {self.name}: no frames", flush=True)
            return False
        start = self.frames[0][0]
        lines = []
        for i, (t, name) in enumerate(self.frames):
            nxt = self.frames[i + 1][0] if i + 1 < len(self.frames) else end
            lines += [f"file '{name}'", f"duration {max(nxt - t, 0.001):.4f}"]
        lines.append(f"file '{self.frames[-1][1]}'")
        (self.dir / "list.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
        mp4 = self.dir.parent / f"{self.name}.mp4"
        await asyncio.to_thread(subprocess.run, [
            FFMPEG, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", "list.txt", "-vf",
            "fps=30,format=yuv420p", "-c:v", "libx264", "-crf", "18", "-preset", "medium", str(mp4.resolve())],
            cwd=self.dir, check=True)
        (self.dir.parent / f"{self.name}.events.json").write_text(json.dumps(
            {"duration_s": round(end - start, 2), "frames": len(self.frames),
             "events": [{"at_s": round(t - start, 2), "label": label} for t, label in self.events]}, indent=1),
            encoding="utf-8")
        print(f"  {self.name}: {len(self.frames)} frames, {end - start:.1f} s -> {mp4.name}", flush=True)
        return False


# ---------- driving the desk ----------

async def desk(page: Page) -> Frame:
    for _ in range(100):
        f = next((f for f in page.frames if f.url.startswith(("http://localhost:8300", "http://127.0.0.1:8300"))
                  or f.url.startswith(PUBLIC)), None)
        if f and await f.evaluate("() => typeof state === 'object' && state.sessions.length > 0"):
            # Larger type for a 1080p video: the desk lays out at 1400/1.2 px in the stage, 1920/1.35 alone.
            await f.evaluate("(z) => { document.documentElement.style.zoom = z; }",
                             "1.2" if f != page.main_frame else "1.35")
            return f
        await asyncio.sleep(0.2)
    raise RuntimeError("the desk did not load")


async def until(f: Frame, js: str, timeout: float = 240) -> None:
    t = time.time()
    while not await f.evaluate(js):
        if time.time() - t > timeout:
            raise TimeoutError(js)
        await asyncio.sleep(0.25)


async def choose(f: Frame, sid: str, mode: str, injection: str = "") -> None:
    await f.locator("#sessions button", has_text=f"{sid} ·").click()
    await until(f, "() => !document.querySelector('#run').disabled")
    await f.locator("#mode-live" if mode == "live" else "#mode-rx").click()
    if injection:
        await f.select_option("#injection", injection)
    await asyncio.sleep(0.6)


async def run_and_wait(f: Frame, cap: Capture) -> None:
    await f.locator("#run").click()
    cap.mark("start")
    if await f.evaluate("() => state.mode === 'live'"):
        # A replayed recording sends no visit_ended stage: the result arrives right after the last span.
        await until(f, "() => document.querySelector('#progress').innerText.includes('Visit ended') || !!state.result")
        cap.mark("visit_ended")
    await until(f, "() => !!state.result", timeout=300)
    cap.mark("result")


async def show(f: Frame, selector: str, hold: float = 0.0) -> None:
    await f.evaluate("(s) => document.querySelector(s)?.scrollIntoView({behavior: 'smooth', block: 'center'})", selector)
    await asyncio.sleep(1.2 + hold)


async def release(f: Frame) -> None:
    await f.evaluate("() => { window.open = (u) => { location.href = u; return null; }; }")
    await f.locator("#release").click()


# ---------- the scenes (docs/submission/video.md) ----------

# S2's prosthesis stance halts as a conflict when the extraction names a catalogued exercise, or as a proposal
# when it does not (the restriction check could not run: DECISIONS row 24).
HALTED = ".line.s-conflict, .line.s-proposal"

async def intro(page: Page, cap: Capture) -> None:
    f = await desk(page)
    await choose(f, "S2", "live")
    cap.mark("idle")
    await asyncio.sleep(10)


async def s2_live(page: Page, cap: Capture) -> None:
    f = await desk(page)
    await choose(f, "S2", "live")
    await asyncio.sleep(1.5)
    await run_and_wait(f, cap)
    await show(f, "#banner", 2)
    await show(f, HALTED, 6)
    cap.mark("halt_shown")


async def s2_release(page: Page, cap: Capture) -> None:
    f = await desk(page)
    await show(f, HALTED, 2)
    await f.locator(HALTED).first.locator("button.remove").click()
    cap.mark("halted_line_removed")
    await asyncio.sleep(1.5)
    await f.locator("#approve-supported").click()
    await show(f, "#release", 1.5)
    await release(f)
    await asyncio.sleep(2)
    cap.mark("patient_sheet")
    page_f = page.frames[1] if len(page.frames) > 1 else page.main_frame
    await asyncio.sleep(5)
    await page_f.evaluate("() => document.querySelector('#note')?.scrollIntoView({behavior: 'smooth', block: 'center'})")
    await asyncio.sleep(4)


async def s3_proposal(page: Page, cap: Capture) -> None:
    await page.reload()
    f = await desk(page)
    await choose(f, "S3", "prescription")
    await asyncio.sleep(1)
    await run_and_wait(f, cap)
    await show(f, ".line.s-proposal", 6)
    cap.mark("proposal_shown")
    await show(f, "#heard-panel", 5)


async def s2_injections(page: Page, cap: Capture) -> None:
    await page.reload()
    f = await desk(page)
    for inj in ("F4", "B3"):
        await choose(f, "S2", "prescription", inj)
        await asyncio.sleep(1.5)
        await run_and_wait(f, cap)
        await show(f, "#banner", 6)
        cap.mark(f"{inj}_banner")


async def s1_arabic_sheet(page: Page, cap: Capture) -> None:
    await page.reload()
    f = await desk(page)
    await choose(f, "S1", "prescription")
    await run_and_wait(f, cap)
    await f.locator("#approve-supported").click()
    await show(f, "#release", 1)
    await release(f)
    cap.mark("patient_sheet")
    await asyncio.sleep(9)


async def cloud(page: Page, cap: Capture) -> None:
    f = await desk(page)
    await choose(f, "S2", "prescription")
    await asyncio.sleep(1)
    await run_and_wait(f, cap)
    await show(f, "#banner", 8)


SCENES = {"intro": intro, "s2_live": s2_live, "s2_release": s2_release, "s3_proposal": s3_proposal,
          "s2_injections": s2_injections, "s1_arabic_sheet": s1_arabic_sheet, "cloud": cloud}


async def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("scenes", nargs="*", default=[s for s in SCENES if s != "cloud"])
    ap.add_argument("--stage", default="http://127.0.0.1:8400/")
    ap.add_argument("--out", default=str(ROOT / "video"))
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(exist_ok=True)
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(channel="msedge", headless=True)
        ctx = await browser.new_context(viewport={"width": 1920, "height": 1080}, device_scale_factor=1)
        page = await ctx.new_page()
        await page.goto(PUBLIC if a.scenes == ["cloud"] else a.stage)
        await asyncio.sleep(3)
        for name in a.scenes:
            print(f"scene {name}", flush=True)
            async with Capture(page, out, name) as cap:
                await SCENES[name](page, cap)
        await browser.close()


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    asyncio.run(main())
