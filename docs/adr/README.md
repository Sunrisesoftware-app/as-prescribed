# Architecture decision records

One file per decision, rendered from the Atlas model's `decisions[]` for system
`as-prescribed`. The model is the source of truth; these files exist so the decisions are
readable in the repository without Atlas. Regenerate with:

```bash
node scripts/adr-from-model.mjs
```

A new decision is added to the model (a PR against the Atlas repository, see CLAUDE.md
"Session end"), not here. A hand edit here is lost on the next run.

- [ADR-0001](0001-the-system-verifies-the-therapist-s-prescription.md): The system verifies the therapist's prescription, never the patient *(accepted)*
- [ADR-0002](0002-generator-and-falsifier-are-different-model-fami.md): Generator and falsifier are different model families *(accepted)*
- [ADR-0003](0003-rule-conflicts-are-decided-by-a-deterministic-en.md): Rule conflicts are decided by a deterministic engine over condition x tag x side *(accepted)*
- [ADR-0004](0004-the-public-demo-replays-only-the-synthetic-sessi.md): The public demo replays only the synthetic sessions, with error-injection buttons and no free text *(accepted)*
- [ADR-0005](0005-a-documented-restriction-that-fires-once-stays-a.md): A documented restriction that fires once stays a conflict, and an item in conflict is never corrected by a model *(accepted)*
- [ADR-0006](0006-a-correction-may-not-change-the-exercise-such-an.md): A correction may not change the exercise; such an item is withdrawn *(accepted)*
- [ADR-0007](0007-a-falsifier-claim-that-a-checkable-rule-can-sett.md): A falsifier claim that a checkable rule can settle is settled by code *(accepted)*
- [ADR-0008](0008-the-english-line-is-composed-from-the-item-and-t.md): The English line is composed from the item and the approved catalogue sentence; the generator only translates *(accepted)*
- [ADR-0009](0009-the-evaluation-is-pre-registered-and-sealed-run-.md): The evaluation is pre-registered and sealed; run 1 is the reported result and every later run is labelled *(accepted)*
- [ADR-0010](0010-the-public-demo-replays-recorded-runs-while-no-h.md): The public demo replays recorded runs while no hosted AMD endpoint is available, labelled as recorded *(accepted)*
