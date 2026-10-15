# ADR-0011: An exercise outside the approved catalogue is always a proposal, never a supported line

**Status:** Accepted
**Atlas id:** `adr.ap.011`
**Links:** `ap.program` (Tags, rule check, completeness and the composed English line), `ap.rules` (Deterministic rule engine (documented restrictions)), `ap.extract` (Extract: the running list of what the therapist prescribed)

> Rendered from the Atlas model (system `as-prescribed`). The model is the source of
> truth; edit it there and run `node scripts/adr-from-model.mjs`.

---

## Context

The rule engine checks documented restrictions against an item's tags, and the tags come from its catalogue entry. Recording the demo video on 15.10.2026, a live S2 run on the Somnus box extracted the prosthesis stance as standing on the prosthesis. No catalogue entry matched, so the item had no tags, the restriction R04 (no unsupervised single-leg weight-bearing on the prosthesis) never ran, and the line came out supported with only a non-blocking note. The sealed evaluation (adr.ap.009) started from the approved, catalogued slots, so it never exercised this path.

## Decision

A check that cannot run never reads as a pass: an item with no catalogue match carries a blocking no_catalogue_match objection, and its line is a proposal the therapist decides. It is not correctable by a model (adr.ap.006). Decided by Petri 15.10.2026 (dec_244efd80ece4488b, DECISIONS row 24).

## Consequences

A live extraction that names an exercise in its own words halts for the therapist instead of passing the restrictions unchecked. The recordings and the evaluation's scoring are unchanged (the kind was already excluded from false alarms). Constraining the extraction to catalogue ids stays a later complement, not a replacement.
