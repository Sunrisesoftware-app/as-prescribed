# ADR-0005: A documented restriction that fires once stays a conflict, and an item in conflict is never corrected by a model

**Status:** Accepted
**Atlas id:** `adr.ap.005`
**Links:** `ap.pipeline` (One session end to end, in falsification rounds), `ap.rules` (Deterministic rule engine (documented restrictions))

> Rendered from the Atlas model (system `as-prescribed`). The model is the source of
> truth; edit it there and run `node scripts/adr-from-model.mjs`.

---

## Context

In evaluation run 1 (14.10.2026) the rule engine caught all five injected contraindicated items in round 0, but the generator's correction rounds then rewrote three of them (E1-E3) so that the rule no longer fired: one ended as a proposal and two as supported. A halt that a correction can undo is not a halt.

## Decision

A rule_conflict raised in any round is kept to the end and decides the line's state; an item in conflict is excluded from the generator's corrections; an item a correction withdrew after its restriction fired is shown to the therapist again. The therapist decides every conflict.

## Consequences

Run 2 (03df5e9): all five contraindicated items ended as conflicts. A false conflict cannot be corrected away either; it costs the therapist one decision.
