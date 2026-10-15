"""Fit the narration to the scene clips and join the final demo video, with captions.

    uv run python scripts/video/final.py [--narration E:/sound_file.mp4]

Inputs: the scene clips of assemble.py (video/cut/NN-*.mp4, cut.json), the slide stills (video/slides), and one
narration track (here a HeyGen render whose picture is not used). video/audio/scenes.json holds each sentence's
start and end in the narration, found by aligning docs/submission/narration.md's sentences to the track's pauses
(word counts against speech time, dynamic programming). Each scene places its sentences at the moments they talk
about (a sentence block per anchor below); a slide lasts as long as its sentences; a clip shorter than its speech is
held on its last frame. Output: video/final/as-prescribed-demo.mp4 and .srt. Used only to make the demo video.
"""
import argparse
import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
V = ROOT / "video"
FFMPEG = shutil.which("ffmpeg") or "C:/ffmpeg/bin/ffmpeg.exe"
FFPROBE = str(Path(FFMPEG).with_name("ffprobe" + Path(FFMPEG).suffix))
LEAD, TAIL = 0.5, 1.5  # seconds of picture before the first and after the last word of a slide scene

# Per scene: ("clip", clip name, [(first sentence, last sentence, at seconds in the clip), ...])
#         or ("slides", [(slide number, first sentence, last sentence), ...]); sentence indices within the scene.
# The clip times come from the takes' events through cut.json (waits sped up 3x): S2 live: visit 2.4-39.1,
# s023 at 25.1, result 52.8; injections: result F4 18.9, second start 28.9, result B3 36.1; S3 result 8.8,
# proposal 16.7; S1 sheet 11.6; S2 release: sheet 9.5.
PLAN = {
    "01": ("slides", [(1, 0, 2)]),
    "02": ("slides", [(2, 0, 2), (3, 3, 5)]),
    "03": ("clip", "03-clinic-hardware", [(0, 2, 0.5)]),
    "04": ("clip", "04-s2-live-conflict", [(0, 1, 2.4), (2, 3, 12.5), (4, 4, 24.8), (5, 5, 39.2), (6, 8, 52.9)]),
    "05": ("clip", "05-s2-release-sheet", [(0, 1, 0.8), (2, 2, 9.6)]),
    "06": ("clip", "06-s3-proposal", [(0, 0, 0.5), (1, 2, 9.4), (3, 3, 18.0)]),
    "07": ("clip", "07-injections", [(0, 1, 0.3), (2, 2, 20.6), (3, 3, 28.6), (4, 6, 36.2)]),
    "08": ("clip", "08-arabic-sheet", [(0, 2, 11.4)]),
    "09": ("slides", [(6, 0, 1), (8, 2, 5)]),
    "10": ("slides", [(7, 0, 2)]),
    "11": ("slides", [(11, 0, 1)]),
}
PRE, POST = 0.12, 0.2  # keep a breath before a sentence and its tail after it
FORCE = False  # --force re-encodes the scenes already in video/final/work


def run(cmd: list[str]) -> None:
    # -nostdin and a timeout: a hung encoder fails the run instead of waiting for hours (15.10.2026).
    subprocess.run([FFMPEG, "-nostdin", "-y", "-loglevel", "error", *cmd], check=True, timeout=900)


def duration(path: Path) -> float:
    out = subprocess.run([FFPROBE, "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", str(path)], capture_output=True, text=True, check=True).stdout
    return float(out.strip())


def chunks_for(scene: str, sents: list[dict], blocks: list[tuple[int, int, float]]) -> list[tuple[float, float, float]]:
    """(narration start, narration end, at) per sentence block."""
    mine = [s for s in sents if s["scene"] == scene]
    return [(max(mine[a]["start"] - PRE, 0), mine[b]["end"] + POST, at) for a, b, at in blocks]


def build(scene: str, plan: tuple, sents: list[dict], narr: Path, work: Path, cues: list, t0: float) -> Path:
    out = work / f"{scene}.mp4"
    mine = [s for s in sents if s["scene"] == scene]
    if plan[0] == "slides":
        first = mine[0]["start"]
        parts, blocks, t = [], [], 0.0
        for i, (slide, a, b) in enumerate(plan[1]):
            end_speech = LEAD + mine[b]["end"] - first
            nxt = LEAD + mine[plan[1][i + 1][1]]["start"] - first - 0.2 if i + 1 < len(plan[1]) else end_speech + TAIL
            parts.append((slide, nxt - t))
            blocks.append((a, b, LEAD + mine[a]["start"] - first))
            t = nxt
        total = t
        inputs, filt = [], []
        for k, (slide, dur) in enumerate(parts):
            inputs += ["-loop", "1", "-t", f"{dur:.3f}", "-i", str(V / "slides" / f"slide{slide:02d}.png")]
            filt.append(f"[{k}:v]scale=1920:1080,fps=30,format=yuv420p[v{k}]")
        filt.append("".join(f"[v{k}]" for k in range(len(parts))) + f"concat=n={len(parts)}:v=1:a=0[v]")
        video_in, vmap = inputs, ";".join(filt)
        nvid = len(parts)
    else:
        clip = V / "cut" / f"{plan[1]}.mp4"
        blocks = plan[2]
        speech_end = max(at + (mine[b]["end"] - mine[a]["start"]) for a, b, at in blocks) + 0.8
        total = max(duration(clip), speech_end)
        hold = total - duration(clip)
        video_in = ["-i", str(clip)]
        # tpad with a zero hold hung ffmpeg on 15.10.2026: pad only when the speech outlasts the clip.
        pad = f"tpad=stop_mode=clone:stop_duration={hold:.3f}," if hold > 0.02 else ""
        vmap = f"[0:v]{pad}fps=30,format=yuv420p[v]"
        nvid = 1
    chunks = chunks_for(scene, sents, blocks)
    # The scene's voice is rendered on its own first, every sentence block from its own input: two atrim branches
    # on one shared input stream deadlocked ffmpeg once the first branch ended (scene 05 hung, 15.10.2026).
    afilt, ain = [], []
    for k, (a, b, at) in enumerate(chunks):
        lead = mine[blocks[k][0]]["start"] - a  # the breath kept before the first word
        delay = max(int((at - lead) * 1000), 0)
        ain += ["-ss", f"{a:.3f}", "-t", f"{b - a:.3f}", "-i", str(narr)]
        afilt.append(f"[{k}:a]asetpts=PTS-STARTPTS,adelay={delay}|{delay}[a{k}]")
    afilt.append("".join(f"[a{k}]" for k in range(len(chunks))) +
                 f"amix=inputs={len(chunks)}:normalize=0,apad,atrim=0:{total:.3f}[a]")
    voice = work / f"{scene}.wav"
    if not (out.is_file() and out.stat().st_size > 0 and not FORCE):
        run([*ain, "-filter_complex", ";".join(afilt), "-map", "[a]", "-t", f"{total:.3f}",
             "-c:a", "pcm_s16le", "-ar", "48000", "-ac", "2", str(voice)])
        run([*video_in, "-i", str(voice), "-filter_complex", vmap, "-map", "[v]", "-map", f"{nvid}:a",
             "-t", f"{total:.3f}", "-r", "30", "-c:v", "libx264", "-crf", "20", "-preset", "veryfast", "-tune",
             "stillimage", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2", str(out)])
    for (a, b, at), (i0, i1, _) in zip(chunks, blocks):
        for s in mine[i0:i1 + 1]:
            start = t0 + at + (s["start"] - mine[i0]["start"])
            cues.append((start, start + (s["end"] - s["start"]), s["text"]))
    return out


def srt_time(t: float) -> str:
    ms = round(t * 1000)
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--narration", default="E:/sound_file.mp4")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    global FORCE
    FORCE = a.force
    work, final = V / "final" / "work", V / "final"
    work.mkdir(parents=True, exist_ok=True)
    narr = V / "audio" / "narration-norm.wav"
    if FORCE or not narr.is_file():
        run(["-i", a.narration, "-vn", "-ac", "2", "-ar", "48000", "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
             str(narr)])
    data = json.loads((V / "audio" / "scenes.json").read_text(encoding="utf-8"))
    sents = data["sentences"]
    cues, files, t = [], [], 0.0
    for scene, plan in PLAN.items():
        f = build(scene, plan, sents, narr, work, cues, t)
        d = duration(f)
        print(f"{scene}: {d:.1f} s", flush=True)
        files.append(f)
        t += d
    lst = work / "list.txt"
    lst.write_text("".join(f"file '{f.resolve().as_posix()}'\n" for f in files), encoding="utf-8")
    mp4 = final / "as-prescribed-demo.mp4"
    run(["-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", "-movflags", "+faststart", str(mp4)])
    (final / "as-prescribed-demo.srt").write_text("".join(
        f"{i}\n{srt_time(s)} --> {srt_time(e)}\n{text}\n\n" for i, (s, e, text) in enumerate(cues, 1)), encoding="utf-8")
    print(f"{mp4.name}: {duration(mp4):.1f} s, {mp4.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
