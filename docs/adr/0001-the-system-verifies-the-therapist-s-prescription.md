# ADR-0001: The system verifies the therapist's prescription, never the patient

**Status:** Accepted
**Atlas id:** `adr.ap.001`
**Links:** `ap.ui` (Therapist's review desk and the patient's sheet), `ap.rules` (Deterministic rule engine (documented restrictions))

> Rendered from the Atlas model (system `as-prescribed`). The model is the source of
> truth; edit it there and run `node scripts/adr-from-model.mjs`.

---

## Context

A health product that drafts patient instructions with a language model invites the reading that it recommends or adapts treatment. The track's safety rules forbid presenting autonomous diagnosis or treatment as medical advice, and suitability of an exercise is the therapist's clinical judgement.

## Decision

The system verifies exactly three things: fidelity (the patient gets what the therapist prescribed, each line traced to a transcript span), constraints (no line violates a documented restriction) and translation (the patient-language line means the prescribed item). It never assesses suitability, diagnoses or proposes treatment. Copy says 'verifies the therapist's prescription', never 'personalised', 'recommends' or 'adapted to your injury'. Decided in chat 13.10.2026 (handoff D8).

## Consequences

Every patient line carries a visible 'prescribed by therapist' marker linked to its span; lines without one are proposals, shown to the therapist only and never released without explicit approval. A rule conflict is framed as 'documented restriction found, therapist decides'.
