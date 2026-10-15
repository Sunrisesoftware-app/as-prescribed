"""Find each narration sentence's start and end in a narration track, for fitting the video to the voice.

    uv run python scripts/video/align.py [--audio video/audio/narration.wav]

The sentences come from docs/submission/narration.md, the track's pauses from ffmpeg's silencedetect. A dynamic
programme picks, for every sentence end, the pause that keeps every sentence's speech time closest to its word
count at one speaking rate, so scene boundaries fall in real pauses. Writes video/audio/scenes.json (per scene and
per sentence, with the text). Used only to make the demo video.
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FFMPEG = shutil.which("ffmpeg") or "C:/ffmpeg/bin/ffmpeg.exe"
BLOCK = re.compile(r"^## (\d\d) · (.+?) · \d+ s · \d+ words\n\n(.*?)(?=\n## |\n---)", re.DOTALL | re.MULTILINE)


def sentences() -> list[tuple[str, str, str, int]]:
    """(scene, scene name, sentence, words) in narration order."""
    out = []
    for scene, name, body in BLOCK.findall((ROOT / "docs/submission/narration.md").read_text(encoding="utf-8")):
        for s in (s for s in re.split(r"(?<=[.!?])\s+", body.strip()) if s):
            out.append((scene, name, s, len(re.sub(r"[^\w\s'-]", "", s).split())))
    return out


def pauses(audio: str) -> tuple[list[tuple[float, float]], float]:
    err = subprocess.run([FFMPEG, "-i", audio, "-af", "silencedetect=noise=-40dB:d=0.18", "-f", "null", "-"],
                         capture_output=True, text=True, check=True).stderr
    found = list(zip(map(float, re.findall(r"silence_start: ([0-9.]+)", err)),
                     map(float, re.findall(r"silence_end: ([0-9.]+)", err))))
    h, mi, s = re.search(r"Duration: (\d+):(\d+):([0-9.]+)", err).groups()
    return found, int(h) * 3600 + int(mi) * 60 + float(s)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--audio", default=str(ROOT / "video/audio/narration.wav"))
    a = ap.parse_args()
    sents = sentences()
    found, total = pauses(a.audio)
    onset = found[0][1] if found and found[0][0] < 0.05 else 0.0
    pz = [p for p in found if p[0] > 0.05 and p[1] < total - 0.05]

    def speech(x: float, y: float) -> float:
        return (y - x) - sum(min(e, y) - max(s, x) for s, e in pz if s < y and e > x)

    words = [w for *_, w in sents]
    rate = sum(words) / speech(onset, total)
    n, m, inf = len(sents), len(pz), float("inf")
    cost = [[inf] * m for _ in range(n)]
    back = [[-1] * m for _ in range(n)]
    for j in range(m):
        cost[0][j] = (speech(onset, pz[j][0]) - words[0] / rate) ** 2 / words[0]
    for i in range(1, n - 1):
        for j in range(m):
            for k in range(j):
                if cost[i - 1][k] < inf:
                    c = cost[i - 1][k] + (speech(pz[k][1], pz[j][0]) - words[i] / rate) ** 2 / words[i]
                    if c < cost[i][j]:
                        cost[i][j], back[i][j] = c, k
    last = min((cost[n - 2][k] + (speech(pz[k][1], total) - words[-1] / rate) ** 2 / words[-1], k)
               for k in range(m) if cost[n - 2][k] < inf)
    path = [last[1]]
    for i in range(n - 2, 0, -1):
        path.append(back[i][path[-1]])
    path.reverse()

    out, start = [], onset
    for i, (scene, _, text, w) in enumerate(sents):
        end = pz[path[i]][0] if i < len(path) else total
        out.append({"scene": scene, "start": round(start, 2), "end": round(end, 2), "words": w, "text": text})
        start = pz[path[i]][1] if i < len(path) else total
    scenes = []
    for scene in dict.fromkeys(s for s, *_ in sents):
        mine = [s for s in out if s["scene"] == scene]
        scenes.append({"scene": scene, "start": mine[0]["start"], "end": mine[-1]["end"],
                       "words": sum(s["words"] for s in mine)})
        print(f"{scene}: {mine[0]['start']:6.2f}-{mine[-1]['end']:6.2f} s, {scenes[-1]['words']} words")
    print(f"rate {rate:.2f} words per speech second; fit cost {last[0]:.2f}")
    (ROOT / "video/audio/scenes.json").write_text(json.dumps({"scenes": scenes, "sentences": out}, indent=1,
                                                             ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
