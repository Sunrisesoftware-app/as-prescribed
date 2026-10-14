# ADR-0009: The evaluation is pre-registered and sealed; run 1 is the reported result and every later run is labelled

**Status:** Accepted
**Atlas id:** `adr.ap.009`
**Links:** `ap.evaluation` (The pre-registered error-injection evaluation)

> Rendered from the Atlas model (system `as-prescribed`). The model is the source of
> truth; edit it there and run `node scripts/adr-from-model.mjs`.

---

## Context

A falsification measurement is only worth its pre-registration: thresholds chosen after the results would make any outcome a pass. Petri locked the thresholds on 14.10.2026 (dec_19703418a6214843, AS-PRESCRIBED-EVAL-ENNAKKO v2).

## Decision

The plan (32 injections, 9 clean runs) is sealed by its sha256 before any run, and the run refuses a changed plan. Gates: recall >= 0.80 overall and >= 0.60 on the 18 falsifier-only injections, false alarms <= 15 %, objections falling from round 0 to 1, latency <= 90 s. Run 1 is reported as it fell; a later run of the same plan after fixes carries a tag and is always reported as made after reading run 1.

## Consequences

Run 1 (34530da) failed recall and false alarms; run 2 (03df5e9) passed false alarms, rounds and latency and failed recall. The test set is now seen: a further claim needs new sessions and a new sealed plan.
