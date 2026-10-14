# ADR-0003: Rule conflicts are decided by a deterministic engine over condition x tag x side

**Status:** Accepted
**Atlas id:** `adr.ap.003`
**Links:** `ap.rules` (Deterministic rule engine (documented restrictions)), `ap.clinical-data` (Synthetic clinical content (vocabulary, catalogue, rules, profiles, sessions, dialogues, answer keys))

> Rendered from the Atlas model (system `as-prescribed`). The model is the source of
> truth; edit it there and run `node scripts/adr-from-model.mjs`.

---

## Context

Diagnoses must act only as constraints (handoff D2), and a halt that a model decides cannot be explained or reproduced.

## Decision

Exercises carry tags from a fixed movement and load vocabulary; documented restrictions are rules of the form profile condition x tag (x side) -> block | caution in data/rules.json. A block halts the program and hands the case to the therapist; a caution must appear in the patient line, so a dropped caution is an objection. An item whose side is unknown meets every side-specific rule.

## Consequences

The rules and tags are clinical content that Petri approves row by row on the review page; tests assert that every session slot gets exactly its expected state. Measured 14.10.2026: the engine caught 5/5 injected contraindicated items in both evaluation runs.
