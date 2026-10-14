# As Prescribed BACKLOG

**The only list of open tasks** (the HomeTeam practice), including the owner's own actions.
[`BUILD_INFO.json`](BUILD_INFO.json) tells the **state**, [`CHANGELOG.md`](CHANGELOG.md) **what was
done**, [`roadmap.md`](roadmap.md) **the order and the gates**, [`DECISIONS.md`](DECISIONS.md)
**the decisions**.

**Rules:** a finished row is **removed** here and recorded in the CHANGELOG in the same session;
before listing a row as open, verify it is not already done (an uncertain row is marked *check*).

Codes: **P** the owner's own actions · **DEPLOY** the public demo · **SUB** the submission ·
**DEMO** the demo itself · **REP** reporting.

Updated 14.10.2026 evening (session 2 closed).

## P: the owner's own actions

- **P-2 Google prize:** ask the organisers whether a project that runs Gemma on AMD hardware
  qualifies (the page lists $5,000 from Google but no criteria). The community@lablab.ai email of
  14.10. about the key can be closed as solved.
- **P-4 Video voice-over or presence** in the demo video, if wanted (SUB-1).
- **P-5 Confirm the deadline** with the organisers if convenient: the live dashboard's countdown ends
  Sun 18.10. 13:00 EEST, the event page was read as 18:00 EEST; the docs use 13:00.

## DEPLOY

- **DEPLOY-4 The public demo live on Token Factory** (DECISIONS row 22; do first on Thu 15.10.). The
  trial of 14.10. is in the CHANGELOG. Base URL and key are in the local `.env`. The manual's limits:
  20 requests a minute per account, 8 concurrent per key, a $1 daily cap. Unknown fields are dropped,
  and thinking is controlled by `reasoning_effort`.
  1. `asprescribed/llm.py`: retry 429 and 502/503 when Retry-After is short (a few seconds, with
     jitter), otherwise raise so the run falls back to its recording. Check whether Qwen3.8-27B honours
     the dropped `chat_template_kwargs` or needs `reasoning_effort: low` (the trial ran without
     thinking at about 2 s a call, 25 tok/s). Tests with the fake client.
  2. The banner and `/api/demo` say "live on AMD Radeon Cloud (Token Factory): Qwen3.8-27B +
     Gemma-4-31B-IT" for a live run, and keep the recorded wording for a fallback. A fallback in the
     public demo must not read as a failure.
  3. The machine: `/etc/as-prescribed/env` (root, 0600) with `AP_MODE=public`, the two endpoints,
     the models, `GENERATOR_THINKING_PARAM` and the key. The unit drops `AP_REPLAY=1` and reads it
     with `EnvironmentFile=` (DynamicUser cannot read a root-only file itself). Copy the key from the
     local `.env` over ssh without printing it, or the owner pastes it with a prompt.
  4. README: public mode is live on Token Factory, with the recordings as fallback. Our server logs
     nothing, but Token Factory keeps prompts about two days (synthetic only; its terms forbid real
     health data).
  5. Check in the browser: S2 live and prescription on the public URL, an injection run, two runs at
     once (the lock queues the second).
  6. Any recall figure on Token Factory is a tagged run of plan-v1 made after reading run 1
     (adr.ap.009), or a new sealed plan.
- **DEPLOY-3** (optional) A deploy workflow (test-gated ssh deploy with a public curl check), only if
  the demo changes often; until then an update is the three commands in
  [`deploy/README.md`](../deploy/README.md).

## SUB: the submission (lablab, before Sun 18.10. 13:00 EEST; target Sat 17.10.)

The form (event page, read 14.10.2026): title, short and long description, technology and category
tags, cover image, video, slide presentation, public GitHub repository, demo application platform,
application URL. Judged on application of technology, presentation, business value, originality.
"The AMD component must be part of the working product shown to the judges" (DECISIONS row 20).

- **SUB-1** Demo video, at most 5 min and under 300 MB: a live run on the Somnus box with the GPUs'
  load on screen (rocm-smi or the Somnus telemetry), S2 (the conflict), S3 (the proposal and the
  traps), one injection caught and one missed, the patient sheet in Arabic, the evaluation table.
  Needs the box (lease and Gemma per AS-PRESCRIBED-SOMNUS-BOKSI).
- **SUB-2** Slide deck: problem, user, the boundary, how it works, the evaluation as it fell, AMD
  hardware and energy, what is next.
- **SUB-3** Cover image 16:9.
- **SUB-4** Title, short and long description, track and technology tags (AMD ROCm, AMD Radeon,
  Gemma, Qwen3, FastAPI); demo application platform: self-hosted, Cloudflare in front.
- **SUB-5** Submit from the team page "Submit Project" with the public repo and the demo URL.

## DEMO

- **DEMO-4** S2's recorded conflict line carries a caution whose Ukrainian says "the skin of the hip
  part" where the English says "the residual limb"; the back-translation shows it and the falsifier
  did not object. A real miss, reported as it fell; do not show that Ukrainian line as correct in the
  video, and name it if it is shown.

## REP: reporting

- **REP-1** `AMD-ACT3-HEALTH-RAPORTTI` in Atlas (tehty / kesken / ehdotettu / avoin).
- **REP-2** The whitepaper §5c entry: R9700 + 7900 XT against tokenfactory (tok/s, Wh), when the
  tokenfactory comparison exists, otherwise the local numbers alone.
- **REP-3** What carries over to Since AI Turku (6.-8.11.2026).
- **REP-4** The Atlas model: the public demo's edge (Cloudflare Worker and Workers VPC over the
  ultragravel machine's tunnel) is not yet a connection in the model; add it in the next Atlas PR.
