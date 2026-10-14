# As Prescribed

The home program, exactly as your therapist prescribed it. Verified line by line, in the patient's own language.

> Status: under construction for the AMD Developer Hackathon ACT III (Health and Wellbeing track), 14–18 October 2026. All data in this repository is synthetic.

## What it does

During a physiotherapy visit, As Prescribed reads the session transcript as it arrives, extracts what the therapist prescribed, and drafts the patient's home program in the patient's own language (Arabic and Ukrainian in the demo). The program is ready when the visit ends, and nothing reaches the patient until the therapist approves it.

**It verifies the therapist's prescription, not the patient.** It checks three things:

1. **Fidelity:** every patient line is what the therapist prescribed (exercise, side, dose, frequency, cautions) and is linked to the transcript span where it was said.
2. **Constraints:** no line violates a documented restriction in the patient's profile. A deterministic rule engine checks this; no model decides a conflict.
3. **Translation:** each patient-language line is back-translated and compared with the prescribed item.

It does **not** assess whether an exercise suits the injury, does not diagnose and does not propose treatment. Suitability is the therapist's clinical judgement; the product makes that judgement visible instead of replacing it.

Every line has exactly one state:

| State | Meaning | What happens |
|---|---|---|
| supported | a transcript span says it, and no documented restriction blocks it | shown with a "prescribed by therapist" marker linked to the span |
| conflict | a documented restriction blocks it | the program halts; the therapist decides |
| proposal | nothing in the transcript says it | shown to the therapist only; never released without explicit approval |
| uncertain translation | the back-translation diverges from the prescribed item | flagged for the therapist |

## How it works

A generator model drafts; a model of a different family falsifies each line in rounds (entailment against the cited spans, back-translation), and the generator corrects until no blocking objection remains or the time budget is spent. Remaining objections are shown to the therapist.

Both modes run on AMD:

- **Public mode:** AMD tokenfactory (the public demo).
- **Local mode:** two llama.cpp servers on AMD Radeon GPUs with ROCm (Radeon AI PRO R9700 and RX 7900 XT): patient data never leaves the clinic.

## Run it

```bash
cp .env.example .env    # fill in the two endpoints
uv sync
uv run uvicorn asprescribed.main:app --port 8300
```

or with Docker: `docker compose up --build`. List the models your endpoints serve with `uv run python scripts/models.py`.

## Safety

The boundary above is the first safety measure: the system verifies a prescription a clinician made and never produces clinical advice of its own. The track's five questions:

- **Incorrect or unsupported responses:** a line no transcript span supports is a *proposal*, visible only to the therapist; the falsifier checks every line against its cited spans.
- **Sensitive information:** the demo uses synthetic data only. Local mode keeps everything on hardware inside the clinic. Public mode has no free-text input, so no real patient data can be entered, and transcripts are not logged.
- **Uncertain results:** *uncertain translation* and the falsifier's remaining objections are shown, never hidden.
- **High-risk decisions:** a documented restriction halts the program; the therapist decides.
- **Human review:** nothing reaches the patient without the therapist's approval.

## License

MIT
