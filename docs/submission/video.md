# As Prescribed: the demo video (Fri 16.10.2026)

At most 5 min and under 300 MB (lablab). Target 4:40. Clinic first: the live run is on the clinic's
own Radeon cards (the Somnus box), with the GPUs' load on screen. Narration in English, by the owner
or as captions (BACKLOG P-4). The slides are the deck "As Prescribed: pitch deck"; its speaker notes
are the long form of the narration below.

## How it was made (15.10.2026)

The app scenes were recorded live on the box by a scripted browser, not by hand:
- `scripts/video/stage.py`: the stage, with the desk beside the GPUs' rocm-smi readings.
- `record.py`: the scenes, one clip each.
- `slides.ps1`: the deck's slides as stills.
- `assemble.py`: the scene clips and a silent rough cut in `video/cut/`, not in git. `cut.json` gives each
  scene's start and length; the model waits are sped up 3×.

The owner records the narration per scene to those lengths, and Code fits the cut to the voice.

| Scene | Starts | Length |
|---|---|---|
| 01 cover | 0:00 | 20 s |
| 02 problem, boundary | 0:20 | 25 s |
| 03 clinic hardware | 0:45 | 11 s |
| 04 S2 live, conflict | 0:56 | 65 s |
| 05 release, Ukrainian sheet | 2:01 | 19 s |
| 06 S3 proposal | 2:20 | 23 s |
| 07 injections F4, B3 | 2:43 | 44 s |
| 08 Arabic sheet | 3:27 | 21 s |
| 09 clinic, evaluation | 3:48 | 30 s |
| 10 cloud (slide 7) | 4:18 | 20 s |
| 11 close | 4:38 | 10 s |

The recording setup below was the manual plan; it is kept for a retake by hand.

## Recording setup

- Screen 1920×1080, the browser at 100 % zoom, the desk at `http://localhost:8300/?speed=15` (local
  mode from `.env`, no `AP_LIVE_BUDGET_S`).
- A terminal beside the browser shows the GPUs (the box run, step 7). The browser takes about 70 % of
  the width.
- Record with the Windows Snipping Tool (Win+Shift+R, video, with the microphone if the owner narrates)
  or OBS, one clip per scene. Join the clips and add captions in Clipchamp, then export 1080p (5 min ≈
  100-200 MB).
- Before recording: one rehearsal run of S2 live, so the models are warm.

## Scenes

| # | Time | On screen | Narration (proposal) |
|---|---|---|---|
| 1 | 0:00-0:20 | Slide 1 (cover) | “As Prescribed turns a physiotherapy visit into the patient’s home program, in the patient’s own language, and verifies every line against what the therapist actually said.” |
| 2 | 0:20-0:45 | Slides 2-3 (problem, boundary) | “A patient who doesn’t speak the clinic’s language goes home with instructions they can’t read. A wrong side or a dropped caution is a safety problem, and a free-writing AI adds exercises nobody prescribed. As Prescribed verifies the prescription. It never prescribes.” |
| 3 | 0:45-1:00 | The desk and the GPU terminal side by side; the header says “Runs live on the clinic’s own AMD Radeon GPUs” | “This runs on the clinic’s own hardware: a Radeon AI PRO R9700 drafts with Qwen, a Radeon RX 7900 XT checks with Gemma. Patient data never leaves it.” |
| 4 | 1:00-2:05 | S2 Ukrainian, Live visit, Start. The transcript streams (real time at 15×, 37 s), the draft grows, the visit ends. Verification rounds with the GPUs busy (43 s, cut to about 15 s with a caption “43 s on the Radeon cards, shown 3× faster”). The result: four supported lines, the conflict on single-leg standing with the rule engine’s reason. | “The program is drafted while the therapist talks. When the visit ends, every line is checked: fidelity, the documented restrictions, the translation. The therapist prescribed standing on the prosthesis at home, but the prosthetist restricted that to supervised sessions. A rule catches it, not a model, and the program halts for the therapist.” |
| 5 | 2:05-2:25 | The therapist removes the conflict line, approves the rest, releases: the patient sheet in Ukrainian with the machine-written note | “Nothing reaches the patient until the therapist approves every line. The patient gets the program in Ukrainian, with the English under each exercise.” |
| 6 | 2:25-2:50 | S3 Arabic, From the approved prescription, Verify: the proposal (an exercise without side or dose) and the list of things heard but not prescribed | “Here the therapist named an exercise without a side or a dose. It becomes a proposal the therapist must decide on, never a guess. Things the patient mentioned are kept out of the program.” |
| 7 | 2:50-3:30 | S2, inject F4 (left and right swapped in the Ukrainian): caught by the falsifier, uncertain translation. Then B3 (the bridge on the wrong side): missed, “A miss is shown as it is.” | “We can inject errors. Swap left and right in the Ukrainian translation: the falsifier back-translates it and catches it. Put the bridge on the wrong leg: this one it misses. We show misses too: when the transcript names both sides, the model is weakest.” |
| 8 | 3:30-3:45 | S1 Arabic patient sheet, right to left | “Arabic, right to left, with every dose as digits.” |
| 9 | 3:45-4:15 | Slides 6 and 8 (the clinic, the evaluation) | “We sealed the evaluation before the first run. The rules caught every documented restriction; the model found half of the errors only a model can find, and the recall gate failed. We report it as it fell. The whole evaluation used 304 watt-hours on these two cards.” |
| 10 | 4:15-4:35 | The public demo https://asprescribed.sunrisesoftware.app with a cloud run’s banner: “On the clinic hardware … the same line states” (or slide 7) | “Judges can try the same pipeline live on AMD Radeon Cloud. Every cloud run is compared with the same case on the clinic hardware.” |
| 11 | 4:35-4:45 | Slide 11 (close) | “As Prescribed. The prescription, verified line by line, on the clinic’s own AMD Radeon cards.” |

If a live run on the box differs from the recording (the injections in scene 7 are the likeliest), we
show what happened and say it; the recordings (`data/recorded/`) are the fallback for any scene.

## The box run (Code runs it; the rules: Atlas `AS-PRESCRIBED-SOMNUS-BOKSI`, CLAUDE.md)

The 7900 XT is ours on 15.-17.10. from 08 to 21 (Laya-FI paused). The R9700's Qwen is production,
shared with the Somnus worker: one request at a time.

1. Read `atlas_get_konetila`, the card queue and the `hw:somnus/` leases; take the lease
   `hw:somnus/7900xt` for 120 min (renew if needed).
2. `sudo -n systemctl start llama-theta` (Gemma on :8080; this stops Laya).
3. Lower the agent cache: `echo LLAMA_ARG_CACHE_RAM=2048 > /home/sf3d/somnus-diag/llama-agent.env`, then
   `sudo -n systemctl stop llama-agent && sudo -n systemctl start llama-agent` (Qwen is down 1-2 min).
4. Check: `curl -sf localhost:8080/health`, `curl -sf localhost:8091/health` on the box, and
   `uv run python scripts/models.py` here (both endpoints list their model).
5. Mark the energy: `cd /home/sf3d/somnus || exit 1; python3 telemetry/mark.py start "as-prescribed-video-20261016" --note "demo video"`.
6. Here: `uv run uvicorn asprescribed.main:app --port 8300`; open `http://localhost:8300/?speed=15`.
7. The GPU terminal (the owner, PowerShell): `ssh -t sf3d@100.120.156.99 "watch -n 1 rocm-smi --showuse --showmemuse --showpower"`.
8. Rehearse S2 live once, then record the scenes.
9. Restore, always: `mark.py end`; `sudo -n systemctl stop llama-theta`; remove the env file and stop and
   start llama-agent; `curl -sf localhost:8110/health || sudo -n systemctl start laya`;
   `rocm-smi --showmemuse`; release the lease; a line in the somnus thread with the Wh.
