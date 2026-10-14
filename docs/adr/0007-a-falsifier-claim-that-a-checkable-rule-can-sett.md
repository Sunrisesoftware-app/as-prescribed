# ADR-0007: A falsifier claim that a checkable rule can settle is settled by code

**Status:** Accepted
**Atlas id:** `adr.ap.007`
**Links:** `ap.pipeline` (One session end to end, in falsification rounds), `ap.falsify` (The falsifier: fidelity against the transcript and back-translation)

> Rendered from the Atlas model (system `as-prescribed`). The model is the source of
> truth; edit it there and run `node scripts/adr-from-model.mjs`.

---

## Context

In evaluation run 1 the false-alarm rate was 16.2 %: gemma-3-12b-it read '3 x 12' and 'three sets of twelve' as different doses, called a side wrong that the cited spans name alone, and called cautions dropped that the item carried. It also found 0/5 dropped cautions when asked to compare.

## Decision

A falsifier objection is overruled, and the overrule noted, when the cited spans contradict it by a rule a reader can check: the item's side is the only side the spans name; every number of the item's dose is in the spans; every word of its frequency is. For cautions the falsifier only quotes the therapist's warnings per item, and code compares the quotes with the item; a quote the therapist never said is ignored.

## Consequences

Run 2: false alarms 6.9 %, dropped cautions 3/5. The overrules cannot hide an error the spans themselves contradict (a side the spans do not name, a number they lack), because those are deterministic objections anyway. A dose with the right numbers in the wrong arrangement (ten sets of three for three sets of ten) would be overruled; the plan has no such case.
