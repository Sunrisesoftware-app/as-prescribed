# As Prescribed BACKLOG

**The only list of open tasks** (the HomeTeam practice), including the owner's own actions.
[`BUILD_INFO.json`](BUILD_INFO.json) tells the **state**, [`CHANGELOG.md`](CHANGELOG.md) **what was
done**, [`roadmap.md`](roadmap.md) **the order and the gates**, [`DECISIONS.md`](DECISIONS.md)
**the decisions**.

**Rules:** a finished row is **removed** here and recorded in the CHANGELOG in the same session;
before listing a row as open, verify it is not already done (an uncertain row is marked *check*).

Codes: **P** the owner's own actions · **DEPLOY** the public demo · **SUB** the submission ·
**DEMO** the demo itself · **REP** reporting.

Updated 16.10.2026 (session 4: submitted on lablab).

## P: the owner's own actions

- **P-6** Permission to remove the merged somnus branch `claude/whitepaper-as-prescribed` (local and
  on GitHub) and its worktree `somnus/.claude/worktrees/wp-as-prescribed` (the somnus rule: merged
  branches go with the owner's permission).

## DEPLOY

- **DEPLOY-5** (optional) Warm the cache with live cloud runs at a quiet hour (Token Factory was fast at
  21:30 EEST and slow at 10:00 EEST; a public S2 run at 16.20 EEST on 16.10. also fell back): raise
  `AP_CACHE_S` and have the machine run the six clean cases through its own API. A judge then sees a
  labelled cloud result at once, not the 90 s fallback.
- **DEPLOY-6** A tagged run of plan-v1 on Token Factory (adr.ap.009: reported as made after reading
  run 1) if a cloud recall figure is wanted for the pitch or the whitepaper.
- **DEPLOY-3** (optional) A deploy workflow (test-gated ssh deploy with a public curl check), only if
  the demo changes often; until then an update is the three commands in
  [`deploy/README.md`](../deploy/README.md).

## SUB: the submission

Submitted on lablab on Fri 16.10.2026 (CHANGELOG session 4; the texts as submitted are in
[`submission/texts.md`](submission/texts.md)). Nothing open. Judging is in progress; the public demo
must keep answering until the results.

## DEMO

- **DEMO-4** S2's conflict line carries a caution whose Ukrainian says "the skin of the hip part" where
  the English says "the residual limb". The back-translation shows it, and Gemma 3 did not object, in
  the recording of 14.10. and the live take of 15.10. alike; Token Factory translated it right. A real
  miss, reported as it fell; the video does not call that line correct. For Since AI Turku.
- **DEMO-5** Constrain the extraction to catalogue ids (DECISIONS row 24, option b). It complements the
  fail-safe that makes an item outside the catalogue a proposal. For Since AI Turku.

## REP: reporting

- **REP-5** The Atlas model's system description of `as-prescribed` still says the public demo is
  planned behind nginx and not deployed (14.10.2026); rewrite it in the next Atlas PR (live on
  Token Factory, clinic recordings as fallback, the edge in `ap.edge`).
