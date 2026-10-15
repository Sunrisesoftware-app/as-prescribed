"""Cut the recorded takes and the slide stills into the demo video's scene clips and a silent rough cut.

    uv run python scripts/video/assemble.py [--takes video/live] [--slides video/slides] [--out video/cut]

Follows docs/submission/video.md: every scene becomes video/cut/NN-name.mp4 (1920x1080, 30 fps), and
roughcut.mp4 joins them. The waits for the models (start -> result, visit end -> result) are sped up and say
so in the cut list (cut.json), which also gives each scene's length, for timing the narration. Used only to
make the demo video.
"""
import argparse
import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FFMPEG = shutil.which("ffmpeg") or "C:/ffmpeg/bin/ffmpeg.exe"
ENC = ["-r", "30", "-pix_fmt", "yuv420p", "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-an"]
SPEED = 3.0  # how much faster a model wait plays


def events(takes: Path, name: str) -> tuple[float, list[tuple[float, str]]]:
    d = json.loads((takes / f"{name}.events.json").read_text(encoding="utf-8"))
    return d["duration_s"], [(e["at_s"], e["label"]) for e in d["events"]]


def piece(takes: Path, name: str, start: float, end: float, speed: float = 1.0) -> dict:
    return {"src": str(takes / f"{name}.mp4"), "start": round(start, 2), "end": round(end, 2), "speed": speed}


def take(takes: Path, name: str) -> list[dict]:
    """A take in pieces: normal speed, except from each start to its result (sped up)."""
    total, ev = events(takes, name)
    out, t = [], 0.0
    for i, (at, label) in enumerate(ev):
        if label == "start":
            result = next((a for a, lab in ev[i:] if lab in ("visit_ended", "result")), None)
            # A live visit plays in real time up to its end; the verification after it is the wait.
            if any(lab == "visit_ended" for _, lab in ev[i:]):
                visit_end = next(a for a, lab in ev[i:] if lab == "visit_ended")
                res = next(a for a, lab in ev[i:] if lab == "result")
                out.append(piece(takes, name, t, visit_end))
                out.append(piece(takes, name, visit_end, res, SPEED))
                t = res
            elif result is not None:
                out.append(piece(takes, name, t, at + 1.0))
                out.append(piece(takes, name, at + 1.0, result, SPEED))
                t = result
    out.append(piece(takes, name, t, total))
    return [p for p in out if p["end"] - p["start"] > 0.05]


def still(slides: Path, n: int, seconds: float) -> dict:
    return {"png": str(slides / f"slide{n:02d}.png"), "seconds": seconds}


def scenes(takes: Path, slides: Path) -> list[tuple[str, list[dict]]]:
    cloud = [piece(takes, "cloud", 0, events(takes, "cloud")[0])] if (takes / "cloud.mp4").is_file() else []
    return [
        ("01-cover", [still(slides, 1, 20)]),
        ("02-problem-boundary", [still(slides, 2, 12), still(slides, 3, 13)]),
        ("03-clinic-hardware", take(takes, "intro")),
        ("04-s2-live-conflict", take(takes, "s2_live")),
        ("05-s2-release-sheet", take(takes, "s2_release")),
        ("06-s3-proposal", take(takes, "s3_proposal")),
        ("07-injections", take(takes, "s2_injections")),
        ("08-arabic-sheet", take(takes, "s1_arabic_sheet")),
        ("09-clinic-evaluation", [still(slides, 6, 15), still(slides, 8, 15)]),
        ("10-cloud", cloud or [still(slides, 7, 20)]),
        ("11-close", [still(slides, 11, 10)]),
    ]


def render(parts: list[dict], out: Path, work: Path) -> float:
    files, total = [], 0.0
    for i, p in enumerate(parts):
        f = work / f"{out.stem}-{i:02d}.mp4"
        if "png" in p:
            cmd = [FFMPEG, "-y", "-loglevel", "error", "-loop", "1", "-t", str(p["seconds"]), "-i", p["png"],
                   "-vf", "scale=1920:1080,format=yuv420p", *ENC, str(f)]
            total += p["seconds"]
        else:
            cmd = [FFMPEG, "-y", "-loglevel", "error", "-ss", str(p["start"]), "-to", str(p["end"]), "-i", p["src"],
                   "-vf", f"setpts=PTS/{p['speed']},fps=30,format=yuv420p", *ENC, str(f)]
            total += (p["end"] - p["start"]) / p["speed"]
        subprocess.run(cmd, check=True)
        files.append(f)
    concat(files, out, work)
    return total


def concat(files: list[Path], out: Path, work: Path) -> None:
    lst = work / f"{out.stem}.txt"
    lst.write_text("".join(f"file '{f.resolve().as_posix()}'\n" for f in files), encoding="utf-8")
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy",
                    str(out)], check=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--takes", default=str(ROOT / "video" / "live"))
    ap.add_argument("--slides", default=str(ROOT / "video" / "slides"))
    ap.add_argument("--out", default=str(ROOT / "video" / "cut"))
    a = ap.parse_args()
    takes, slides, out = Path(a.takes), Path(a.slides), Path(a.out)
    work = out / "work"
    work.mkdir(parents=True, exist_ok=True)
    cut, clips, t = [], [], 0.0
    for name, parts in scenes(takes, slides):
        clip = out / f"{name}.mp4"
        length = render(parts, clip, work)
        cut.append({"scene": name, "starts_at_s": round(t, 1), "length_s": round(length, 1),
                    "parts": [{k: v for k, v in p.items() if k != "src"} | {"from": Path(p.get("src", p.get("png", ""))).name}
                              for p in parts]})
        clips.append(clip)
        t += length
        print(f"{name}: {length:.1f} s", flush=True)
    concat(clips, out / "roughcut.mp4", work)
    (out / "cut.json").write_text(json.dumps({"total_s": round(t, 1), "speed_of_waits": SPEED, "scenes": cut},
                                             indent=1), encoding="utf-8")
    print(f"roughcut.mp4: {t:.1f} s ({t / 60:.1f} min)")


if __name__ == "__main__":
    main()
