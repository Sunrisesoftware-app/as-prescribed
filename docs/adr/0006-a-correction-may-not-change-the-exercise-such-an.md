# ADR-0006: A correction may not change the exercise; such an item is withdrawn

**Status:** Accepted
**Atlas id:** `adr.ap.006`
**Links:** `ap.pipeline` (One session end to end, in falsification rounds)

> Rendered from the Atlas model (system `as-prescribed`). The model is the source of
> truth; edit it there and run `node scripts/adr-from-model.mjs`.

---

## Context

In evaluation run 1 three invented items (C1-C3) were 'corrected' into copies of exercises the therapist did prescribe, so the program carried a duplicate line and the invented item looked repaired.

## Decision

The correction prompt forbids turning an item into a different exercise, and the merge enforces it: when a corrected item's exercise differs from the original's, the original is withdrawn instead (it was not prescribed).

## Consequences

Run 2: invented items left the program (four removed, one still supported) instead of becoming copies. A real extraction error that named the wrong exercise is also withdrawn rather than repaired; the therapist sees it under 'heard, but not prescribed'.
