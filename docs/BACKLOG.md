# As Prescribed BACKLOG

**The only list of open tasks** (the HomeTeam practice), including the owner's own actions.
[`BUILD_INFO.json`](BUILD_INFO.json) tells the **state**, [`CHANGELOG.md`](CHANGELOG.md) **what was
done**, [`roadmap.md`](roadmap.md) **the order and the gates**, [`DECISIONS.md`](DECISIONS.md)
**the decisions**.

**Rules:** a finished row is **removed** here and recorded in the CHANGELOG in the same session;
before listing a row as open, verify it is not already done (an uncertain row is marked *check*).

Codes: **P** the owner's own actions · **DEPLOY** the public demo · **SUB** the submission ·
**DEMO** the demo itself · **REP** reporting.

Updated 14.10.2026 (session 2).

## P: the owner's own actions

- **P-1 Tokenfactory key: waiting for the organisers** (DECISIONS row 20: pursued so the public demo
  can run live on AMD's cloud). notebooks.amd.com/tokenfactory says "Your email is not registered
  for API key distribution" for pete@sunrisesoftware.app. The owner emailed community@lablab.ai on
  14.10.2026. Next steps for the owner, in order:
  1. On the ACT III event page, while signed in to lablab, use **Sign up with AMD** (the event's own
     enrolment, which links the AMD AI Developer Program account) and check the page shows the
     enrolment; the team "As Prescribed" exists since 14.10.
  2. Link Discord in the lablab profile, so the event channels (help) appear on the lablab Discord.
  3. Retry tokenfactory on Thu 15.10. morning: the distribution list may be filled in batches.
  4. Ask in the same message whether a project that runs Gemma on AMD hardware qualifies for the
     Google prize (the page lists $5,000 from Google but no criteria).
- **P-4 Video voice-over or presence** in the demo video, if wanted (SUB-1).
- **P-5 Confirm the deadline** with the organisers if convenient: the live dashboard's countdown ends
  Sun 18.10. 13:00 EEST, the event page was read as 18:00 EEST; the docs use 13:00.

## DEPLOY

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
