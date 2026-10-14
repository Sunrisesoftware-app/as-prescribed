# ADR-0010: The public demo replays recorded runs while no hosted AMD endpoint is available, labelled as recorded

**Status:** Accepted
**Atlas id:** `adr.ap.010`
**Links:** `ap.api` (HTTP API and the streamed run (FastAPI, server-sent events)), `ap.ui` (Therapist's review desk and the patient's sheet)

> Rendered from the Atlas model (system `as-prescribed`). The model is the source of
> truth; edit it there and run `node scripts/adr-from-model.mjs`.

---

## Context

The tokenfactory key distribution refused the owner's email on 14.10.2026 even after the lablab team existed, and judging happens after the deadline, when the Somnus box cannot be the public endpoint (it is a home machine with a 08-21 window).

## Decision

Every demo case (three live sessions, three approved prescriptions, all 32 injections) was run once on the Somnus box and recorded in data/recorded. With AP_REPLAY=1 the server serves the recording without any model call, and the view says it is a recorded run. With live endpoints configured the recordings are only the fallback when a model does not answer.

## Consequences

The public demo answers at any hour and costs nothing per click; it shows real model output from AMD hardware, but not a fresh run. The README and the pitch say so.
