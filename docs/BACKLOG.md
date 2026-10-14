# As Prescribed BACKLOG

**The only list of open tasks** (the HomeTeam practice), including the owner's own actions.
[`BUILD_INFO.json`](BUILD_INFO.json) tells the **state**, [`CHANGELOG.md`](CHANGELOG.md) **what was
done**, [`roadmap.md`](roadmap.md) **the order and the gates**, [`DECISIONS.md`](DECISIONS.md)
**the decisions**.

**Rules:** a finished row is **removed** here and recorded in the CHANGELOG in the same session;
before listing a row as open, verify it is not already done (an uncertain row is marked *check*).

Codes: **P** the owner's own actions · **DEPLOY** the public demo · **SUB** the submission ·
**DEMO** the demo itself · **REP** reporting.

Updated 14.10.2026.

## P: the owner's own actions

- **P-1 Tokenfactory key.** notebooks.amd.com/tokenfactory says "Your email is not registered for API
  key distribution" for pete@sunrisesoftware.app (AMD AI Developer Program and lablab use the same
  address; the lablab team exists since 14.10.). Ask the organisers: lablab Discord #ineedhelp, or
  the address community@lablab.ai shown on the lablab site. Without the key the public demo replays
  recorded runs (adr.ap.010); the AMD requirement is met by the Radeon cards in local mode.
- **P-2 Merge Atlas PR #477** (the model's modules and ADRs 005-010) if the agent's permission check
  refuses the merge; the agent then deploys and re-renders `docs/adr/`.
- **P-3 DNS for asprescribed.sunrisesoftware.app** (Cloudflare), or permission for the agent to add
  it; *check* whether the name is the one wanted (it was marked a proposal).
- **P-4 Video voice-over or presence** in the demo video, if wanted (SUB-1).

## DEPLOY

- **DEPLOY-1** On the ultragravel machine (135.181.157.185): checkout under `/opt/as-prescribed`,
  `uv sync --frozen --no-dev`, a systemd unit running uvicorn on 127.0.0.1:<free port> with
  `AP_REPLAY=1`. Check the free port and that Python 3.12 or uv is available there first.
- **DEPLOY-2** nginx vhost + certbot for the name (as for api.ultragravel.app), Cloudflare proxied.
- **DEPLOY-3** A deploy workflow (spectralforge-api's test-gated ssh deploy with a public curl check).

## SUB: the submission (lablab, before Sun 18.10. 18:00 EEST)

- **SUB-1** Demo video, at most 5 min and under 300 MB: S2 live (the conflict), S3 (the proposal and
  the traps), one injection caught and one missed, the patient sheet in Arabic, the evaluation table.
- **SUB-2** Slide deck: problem, user, the boundary, how it works, the evaluation as it fell, AMD
  hardware and energy, what is next.
- **SUB-3** Cover image 16:9.
- **SUB-4** Title, short and long description, track and technology tags.
- **SUB-5** Submit from the team page "Submit Project" with the public repo and the demo URL.

## DEMO

- **DEMO-1** Show "recorded run" and the recording date prominently when replaying (the banner
  exists; *check* it reads well on the public page).
- **DEMO-2** *check* the patient sheet's three fixed headings in Arabic and Ukrainian (written by Code;
  nobody on the team reads them): a native speaker, or mark them in the sheet as machine-written.
- **DEMO-3** Docker compose run once end to end (the README promises it).

## REP: reporting

- **REP-1** `AMD-ACT3-HEALTH-RAPORTTI` in Atlas (tehty / kesken / ehdotettu / avoin).
- **REP-2** The whitepaper §5c entry: R9700 + 7900 XT against tokenfactory (tok/s, Wh), when the
  tokenfactory comparison exists, otherwise the local numbers alone.
- **REP-3** What carries over to Since AI Turku (6.-8.11.2026).
