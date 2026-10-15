# As Prescribed

The home program, exactly as your therapist prescribed it. Verified line by line, in the patient's own language.

> Status: under construction for the AMD Developer Hackathon ACT III (Health and Wellbeing track), 14–18 October 2026. All data in this repository is synthetic.

**Demo:** https://asprescribed.sunrisesoftware.app runs each case live on AMD Radeon Cloud (Token Factory) and compares it with the same case run on the clinic's AMD Radeon cards. When the shared cloud is too busy to finish within 90 s, it shows the clinic run instead and says so. Every person and session in it is synthetic.

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

- **In the clinic (local mode), the product:** two llama.cpp servers on the clinic's own AMD Radeon GPUs with ROCm. Qwen3.5-35B-A3B on a Radeon AI PRO R9700 drafts, and Gemma 3 12B on a Radeon RX 7900 XT checks. Patient data never leaves the clinic.
- **To try it (public mode):** AMD Radeon Cloud's Token Factory, with Qwen3.8-27B drafting and Gemma-4-31B-IT checking.
  - Each run is compared on the page with the same case recorded on the clinic hardware: the line states, and for an injected error whether both caught it.
  - A run that misses `AP_LIVE_BUDGET_S` (90 s on the demo) shows that recording instead.
  - In a trial on 14.10.2026 all six clean cases gave the same line states in both places.

## Evaluation (pre-registered)

We injected 32 errors of six types into the approved prescriptions of the three synthetic sessions (wrong dose or frequency, wrong side, invented exercise, dropped caution, contraindicated exercise, mistranslation into Arabic or Ukrainian) and ran 9 clean runs for false alarms. The plan was sealed by its sha256 (`eval/SEAL`) and the thresholds were fixed before the first run. Detection is read before any correction. Local mode: Qwen3.5-35B-A3B on a Radeon AI PRO R9700 generates, gemma-3-12b-it on a Radeon RX 7900 XT falsifies.

| | Run 1 (pre-registered) | Run 2 (after fixes made on run 1's results) | Threshold |
|---|---|---|---|
| Recall, all 32 | 0.59 | 0.72 | ≥ 0.80 |
| Recall, the 18 only a model can catch | 0.28 | 0.50 | ≥ 0.60 |
| Recall, the 14 the deterministic checks and rules catch | 1.00 | 1.00 | |
| False alarms on clean lines | 16.2 % | 6.9 % | ≤ 15 % |
| Objections, round 0 → round 1 | 1.93 → 1.08 | 0.95 → 0.20 | falls |
| Program ready after the visit (slowest session) | 40 s | 44 s | ≤ 90 s |

The recall gate failed in both runs. What carries the safety is the deterministic layer: every documented restriction was caught, and since run 2 it stays a conflict for the therapist to decide whatever a model does afterwards. The falsifier model finds about half of the errors only a model can find; it is weakest when the transcript names both sides and on Arabic mistranslations. Run 2 is not an independent test, because its fixes were made after reading run 1. Raw runs: `eval/raw/`, results: `eval/results-*.json`.

## Run it

```bash
cp .env.example .env    # fill in the two endpoints
uv sync
uv run uvicorn asprescribed.main:app --port 8300
```

or with Docker: `docker compose up --build`. List the models your endpoints serve with `uv run python scripts/models.py`.

Without any model endpoint, `AP_REPLAY=1` serves the runs recorded on the clinic hardware (`data/recorded/`, every demo case), and the page says it is a recorded run. With `AP_LIVE_BUDGET_S=90` a live run that takes longer serves its recording instead. The public demo's setup is in [`deploy/`](deploy/README.md). Run one session end to end from the command line with `uv run python scripts/run_session.py S2`, and the evaluation with `uv run python scripts/eval.py run`.

## Documentation

The product ([`docs/product.md`](docs/product.md)), the architecture ([`docs/architecture.md`](docs/architecture.md)), the decisions ([`docs/adr/`](docs/adr/README.md), rendered from the Atlas model), and the working practice ([`CLAUDE.md`](CLAUDE.md)).

## Safety

The boundary above is the first safety measure: the system verifies a prescription a clinician made and never produces clinical advice of its own. The track's five questions:

- **Incorrect or unsupported responses:** a line no transcript span supports is a *proposal*, visible only to the therapist; the falsifier checks every line against its cited spans.
- **Sensitive information:** the demo uses synthetic data only. Local mode keeps everything on hardware inside the clinic. Public mode has no free-text input, so no real patient data can be entered, and our server logs nothing about a session. Token Factory keeps prompts for about two days and its terms forbid real health data, which is why a clinic runs local mode.
- **Uncertain results:** *uncertain translation* and the falsifier's remaining objections are shown, never hidden.
- **High-risk decisions:** a documented restriction halts the program; the therapist decides.
- **Human review:** nothing reaches the patient without the therapist's approval.

## License

MIT
