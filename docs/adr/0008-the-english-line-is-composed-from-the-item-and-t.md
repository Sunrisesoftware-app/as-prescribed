# ADR-0008: The English line is composed from the item and the approved catalogue sentence; the generator only translates

**Status:** Accepted
**Atlas id:** `adr.ap.008`
**Links:** `ap.program` (Tags, rule check, completeness and the composed English line), `ap.translate` (Translation into the patient's language and the number check)

> Rendered from the Atlas model (system `as-prescribed`). The model is the source of
> truth; edit it there and run `node scripts/adr-from-model.mjs`.

---

## Context

A model asked to write patient instructions adds advice; every added word is content no transcript span supports.

## Decision

The English source of every patient line is composed deterministically from the item's fields (canonical dose 'N × M', frequency, side) and the catalogue's approved how-to sentence, plus the therapist's cautions and the records' caution rules. The generator translates that line and nothing else. A field the transcript does not state is written as not stated and makes the line a proposal.

## Consequences

The back-translation check compares like with like. The patient line is as plain as the catalogue sentence; a richer wording would need its own approval.
