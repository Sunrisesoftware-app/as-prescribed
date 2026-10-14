# As Prescribed CHANGELOG

Newest first. One entry per session; a session that ships several distinct things gets
sub-entries. What changed and *why*, with what was measured, so a later reader can tell a
decision from a habit. The canonical state is [`BUILD_INFO.json`](BUILD_INFO.json): refer to it,
do not copy it here.

## Session 2, 14.10.2026 evening: the public demo is up

**Decided (the owner):** the order of the remaining work (deploy first, then the lablab rules, demo
polish, texts, video, submission); the Cloudflare part handed to Code; how AMD is shown to the
judges: the recordings labelled as Radeon runs and a live run on the box in the video, with the
tokenfactory key pursued for a live public demo (DECISIONS row 20, dec_4df9557bb0ad458e).

**Done:**
- https://asprescribed.sunrisesoftware.app in replay mode ([`deploy/`](../deploy/README.md)). The
  app is a systemd unit on the ultragravel machine (uvicorn on 127.0.0.1:8300, an ephemeral user, a
  read-only system, no access log). The edge is a Cloudflare Worker on the custom domain, so
  Cloudflare made the DNS record and the certificate. It reaches the app through a Workers VPC
  service over the machine's existing tunnel, so no port is opened and no certificate lives on the
  machine. Wrangler's login cannot edit DNS records, and this route needed none. An nginx vhost made
  first was removed once the Worker answered.
- The lablab rules read: the submission form, the judging criteria, the AMD requirement, and the
  Google prize (no criteria published). The live dashboard's countdown ends Sun 18.10. 13:00 EEST,
  five hours before the deadline the docs held; the docs now use 13:00.

**Measured:**
- The gate passed in the browser: the S2 recorded run shows four supported lines and the conflict on
  the prosthesis line, and the patient sheet opens in Ukrainian with the four approved lines.
- A live replay streams spans every 2-4 s through the Worker, so it is not buffered.
- The app's resident memory on the machine: 60 MB.

**Seen in passing (BACKLOG DEMO-4):** S2's recorded conflict line has a Ukrainian caution that says
"hip part" where the English says "residual limb". The falsifier did not object.

**Demo polish: a recorded run names its hardware** (DECISIONS row 20). The replay banner blamed an
endpoint that did not answer, which is wrong when the public demo runs no model by design.
- `data/recorded/recording.json` says when and on what the runs were made: 14.10.2026,
  Qwen3.5-35B-A3B on the Radeon AI PRO R9700, Gemma 3 12B on the Radeon RX 7900 XT, llama.cpp with
  ROCm.
- `GET /api/demo` serves it. In replay mode the page header says so before any run, and the banner
  and the model facts name the GPUs after a run. The fallback case (an endpoint that did not answer)
  keeps its own wording.
- Two tests: replay mode labels the run, and all 38 recordings were made on the models the label
  names (88 tests).

**Demo polish: the patient sheet and Docker.**
- The patient sheet says in English, under the exercises, that its Arabic or Ukrainian headings are
  machine-written and unchecked by a native speaker (DECISIONS row 21, the owner's choice).
- `docker compose build` and a replay run of the service (Docker 29.5.2): health, `/api/demo`, the S3
  run (three supported lines, one proposal) and the patient sheet answer, and no `.env` is in the image.

**The tokenfactory key arrived.** The owner signed in at notebooks.amd.com and opened `/tokenfactory`
after it, which showed the team's key page (team-1199): redeemed. Twelve models are listed, among them
Qwen3.8-27B, Qwen3.8-Flash-Next and Gemma-4-31B-IT. The key is the owner's, kept out of the chat.
The owner set it in `.env` with a PowerShell prompt. The base URL is
https://developer.amd.com.cn/radeon/api/v1. Token Factory is AMD Radeon Cloud's model API on AMD GPUs.
Per the owner's copy of its manual:
- 20 requests a minute per account and 8 concurrent per key, enforced by the gateway.
- The gateway drops unknown fields silently and controls thinking with `reasoning_effort`.
- Prompts are kept about two days.

**Trial on Token Factory** (BACKLOG DEPLOY-4.1; Qwen3.8-27B generating, Gemma-4-31B-IT falsifying, the
six clean demo cases through the app, sequential):
- Every case ended in the same line states as its Radeon recording.
- No call failed or fell back to a recording.
- Ready after the visit: S1 85 s, S2 53 s, S3 66 s (local Radeon: 34-44 s).
- Prescription runs: 30-86 s.
- Rounds: S1 3 rounds (round-0 objections 3 → 2 → 0); S2 and S3 1 round each.
- Speed, tokens over wall time including the network: generator 24-29 tok/s, falsifier 33-40 tok/s.
- About 11 calls per run. The day's spend was $0.0018 of the key's $1 daily cap.
- S2's caution reads "residual limb" in Ukrainian here (cf. DEMO-4).
- Raw results in `runs/tokenfactory-20261014T183321Z/` (not in git).

## Session 1, 14.10.2026 (continued): Atlas PR #477 merged and deployed

**Decided (the owner):** PR #477 merged; the name asprescribed.sunrisesoftware.app confirmed (Atlas
decision log). **Done:** both Atlas workers deployed from main b632460 (atlas-mcp d9780c2e, viewer
43c40811); `atlas_get_system` shows 13 modules; `docs/adr` re-rendered from main with no diff. The
owner emailed community@lablab.ai about the tokenfactory key; the Discord shows him no #ineedhelp
channel.

## Session 1, 14.10.2026: from the handoff to a measured, recorded demo (chain 1)

**Decided (the owner, in decision boxes; DECISIONS.md rows 9-16, 17-19):** the name As Prescribed;
English transcripts; gemma-3-12b-it on the 7900 XT as the falsifier; Laya-FI paused 15.-17.10.;
S2 a lower-limb amputation; clinical content checked on one review page; the demo at
asprescribed.sunrisesoftware.app on the ultragravel machine, systemd, no free text, with error
injection; an Atlas system of its own; the evaluation's thresholds (recall >= 0.80 and >= 0.60 on
the falsifier-only subset, false alarms <= 15 %, latency <= 90 s); S2.2 changed to a single-leg
bridge on the intact leg, and a reason added to the S2 dialogue.

**Done:**
- The repository, public under MIT, with a secret scan in CI.
- The pipeline (`asprescribed/`), the therapist's desk and the patient sheet.
- The approved synthetic content and three dialogues with answer keys.
- The sealed evaluation, run twice on the Somnus box.
- All 38 demo cases recorded for replay.
- The Atlas system (PR #475, and #477 for the modules and ADRs 005-010).
- The lablab team.

**Measured:**
- Run 1 (pre-registered, 34530da): recall 0.594 (falsifier-only 0.278, deterministic 14/14), false
  alarms 16.2 %, objections 1.93 -> 1.08, latency 40 s.
- Run 2 (after fixes, 03df5e9): recall 0.719 (0.50, 14/14), false alarms 6.9 %, 0.95 -> 0.20, 44 s.
- Contraindicated items: 5/5 caught in both runs; 5/5 kept as conflicts only in run 2.
- Extraction end to end: every slot found in S1-S3, both traps kept out.
- Speed: generator about 66 tok/s (R9700), falsifier about 55 tok/s (7900 XT).
- Energy: 304 Wh over 74.5 min.

**Why run 2 exists:** run 1 showed a correction undoing three safety halts and three invented items
becoming copies of real ones (LESSONS.md); the fixes are ADRs 005-007, and run 2 is labelled as made
after reading run 1.
