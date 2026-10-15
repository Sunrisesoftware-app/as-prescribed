# As Prescribed BACKLOG

**The only list of open tasks** (the HomeTeam practice), including the owner's own actions.
[`BUILD_INFO.json`](BUILD_INFO.json) tells the **state**, [`CHANGELOG.md`](CHANGELOG.md) **what was
done**, [`roadmap.md`](roadmap.md) **the order and the gates**, [`DECISIONS.md`](DECISIONS.md)
**the decisions**.

**Rules:** a finished row is **removed** here and recorded in the CHANGELOG in the same session;
before listing a row as open, verify it is not already done (an uncertain row is marked *check*).

Codes: **P** the owner's own actions · **DEPLOY** the public demo · **SUB** the submission ·
**DEMO** the demo itself · **REP** reporting.

Updated 15.10.2026 evening (session 3 closed).

## P: the owner's own actions

- **P-5 Confirm the deadline** with the organisers if convenient: the live dashboard's countdown ends
  Sun 18.10. 13:00 EEST, the event page was read as 18:00 EEST; the docs use 13:00.

## DEPLOY

- **DEPLOY-5** (optional) Warm the cache with live cloud runs at a quiet hour (Token Factory was fast at
  21:30 EEST and slow at 10:00 EEST): raise `AP_CACHE_S` and have the machine run the six clean cases
  through its own API. A judge then sees a labelled cloud result at once, not the 90 s fallback.
- **DEPLOY-6** A tagged run of plan-v1 on Token Factory (adr.ap.009: reported as made after reading
  run 1) if a cloud recall figure is wanted for the pitch or the whitepaper.
- **DEPLOY-3** (optional) A deploy workflow (test-gated ssh deploy with a public curl check), only if
  the demo changes often; until then an update is the three commands in
  [`deploy/README.md`](../deploy/README.md).

## SUB: the submission (lablab, before Sun 18.10. 13:00 EEST; target Sat 17.10.)

The form (event page, read 14.10.2026): title, short and long description, technology and category
tags, cover image, video, slide presentation, public GitHub repository, demo application platform,
application URL. Judged on application of technology, presentation, business value, originality.
"The AMD component must be part of the working product shown to the judges" (DECISIONS row 20).

- **SUB-5 Submit on Sat 17.10.** from the team page "Submit Project". Every item is ready; the field map:

  | Field | What |
  |---|---|
  | Title, short and long description, tags | [`submission/texts.md`](submission/texts.md) (the owner's last read) |
  | Cover image | [`submission/cover.png`](submission/cover.png) |
  | Video presentation | `video/final/as-prescribed-demo-captioned.mp4` (4:23, 15.9 MB, captions burned in; a backup in the owner's Videos folder, As Prescribed) |
  | Slide presentation | [`submission/deck.pdf`](submission/deck.pdf) |
  | Public GitHub repository | https://github.com/Sunrisesoftware-app/as-prescribed |
  | Demo application platform | self-hosted: a systemd service behind a Cloudflare Worker; models on AMD Radeon Cloud (Token Factory), and on the clinic's AMD Radeon GPUs in local mode |
  | Application URL | https://asprescribed.sunrisesoftware.app |

  Before submitting, check that the public URL answers and an S2 run finishes or falls back with its
  label.

## DEMO

- **DEMO-4** S2's conflict line carries a caution whose Ukrainian says "the skin of the hip part" where
  the English says "the residual limb". The back-translation shows it, and Gemma 3 did not object, in
  the recording of 14.10. and the live take of 15.10. alike; Token Factory translated it right. A real
  miss, reported as it fell; the video does not call that line correct. For Since AI Turku.
- **DEMO-5** Constrain the extraction to catalogue ids (DECISIONS row 24, option b). It complements the
  fail-safe that makes an item outside the catalogue a proposal. For Since AI Turku.

## REP: reporting

- **REP-1** `AMD-ACT3-HEALTH-RAPORTTI` in Atlas (tehty / kesken / ehdotettu / avoin).
- **REP-2** The whitepaper §5c entry: R9700 + 7900 XT against tokenfactory (tok/s, Wh), when the
  tokenfactory comparison exists, otherwise the local numbers alone.
- **REP-3** What carries over to Since AI Turku (6.-8.11.2026).
- **REP-5** The Atlas model's system description of `as-prescribed` still says the public demo is
  planned behind nginx and not deployed (14.10.2026); rewrite it in the next Atlas PR (live on
  Token Factory, clinic recordings as fallback, the edge in `ap.edge`).
