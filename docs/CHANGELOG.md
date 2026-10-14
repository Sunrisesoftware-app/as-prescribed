# As Prescribed CHANGELOG

Newest first. One entry per session; a session that ships several distinct things gets
sub-entries. What changed and *why*, with what was measured, so a later reader can tell a
decision from a habit. The canonical state is [`BUILD_INFO.json`](BUILD_INFO.json): refer to it,
do not copy it here.

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
