# ADR-0004: The public demo replays only the synthetic sessions, with error-injection buttons and no free text

**Status:** Accepted
**Atlas id:** `adr.ap.004`
**Links:** `ap.api` (HTTP API and the streamed run (FastAPI, server-sent events)), `ap.ui` (Therapist's review desk and the patient's sheet)

> Rendered from the Atlas model (system `as-prescribed`). The model is the source of
> truth; edit it there and run `node scripts/adr-from-model.mjs`.

---

## Context

Judging happens after the deadline on a public URL. A free-text field invites real patient data and spends the tokenfactory quota.

## Decision

The public demo serves only S1-S3. A judge can inject an error (for example swap side or drop a caution) and see whether the falsifier catches it, using the same injection code as the evaluation; a miss is shown honestly. Nothing is logged. Decided by Petri 14.10.2026 (dec_bc0df4d7c1d64869).

## Consequences

No input path for real data exists in public mode. The recorded-run replay (adr.ap.010) keeps the demo answering when no model is reachable.
