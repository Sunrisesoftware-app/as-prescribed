# As Prescribed: product

What it is, for whom, and what it never does. Where this document and an ADR differ, the ADR wins
and this is corrected.

## 1. Core sentence

The home program, exactly as your therapist prescribed it. Verified line by line, in the patient's
own language. (The tagline is the owner's choice of a proposed wording, dec_e6d732c5cdd744e1.)

## 2. For whom

- **The physiotherapist** at a clinic with patients who do not share the clinic's language: the
  program is ready when the visit ends, every line linked to where it was said, and nothing reaches
  the patient without the therapist's decision.
- **The patient** who gets the program in Arabic or Ukrainian, printable, right to left for Arabic.
- **The judges** of the Health track, who read the demo, the README and the evaluation.

The demo's patients are synthetic: P1 (knee osteoarthritis, Arabic), P2 (a Ukrainian patient after
a war injury, left below-knee amputation, early prosthetic phase), P3 (shoulder pain and
osteoporosis, Arabic). The owner, a physiotherapist, approved every clinical row.

## 3. What it verifies (adr.ap.001)

1. **Fidelity:** each line is what the therapist prescribed (exercise, side, dose, frequency,
   cautions), traced to a transcript span.
2. **Constraints:** no line violates a documented restriction in the profile; a violation halts the
   program and the therapist decides (adr.ap.003, adr.ap.005).
3. **Translation:** the patient-language line means the prescribed item (back-translation by a model
   of another family, numbers checked by code).

Every line has one state: **supported**, **conflict** (therapist decides), **proposal** (not
prescribed as stated; therapist only), **uncertain translation**. Precedence: conflict > proposal >
uncertain translation > supported.

## 4. What it does in the demo

- **Live visit:** the transcript is replayed in visit time; the program is drafted during the visit;
  the falsification rounds start at the last chunk; the program is ready about 30-45 s later on the
  Somnus box (measured 14.10.2026).
- **From the approved prescription:** a judge injects one of 32 errors (wrong dose, wrong side,
  invented exercise, dropped caution, contraindicated exercise, mistranslation) and sees whether it
  is caught; a miss is shown as it is (adr.ap.004).
- **The desk:** approve or remove each line; a conflict needs an explicit acknowledgement; release
  only when every line is decided; the patient sheet opens with the approved lines.

## 5. What it never does

- Diagnose, recommend, judge suitability or propose treatment.
- Accept free text or real patient data in the public demo, or log a session.
- Let a model decide a conflict, write the English source of a patient line, or correct a halt away.
- Claim more than the evaluation measured: the falsifier finds about half of the errors only a
  model can find (run 2), and the README says so.

## 6. The three sessions

| Session | Language | Demonstrates |
|---|---|---|
| S1 | Arabic | The happy path: every line supported; right-to-left patient sheet |
| S2 | Ukrainian | A conflict: single-leg stance on the prosthesis at home collides with the prosthetist's restriction |
| S3 | Arabic | Ambiguity: a stretch without side or dose becomes a proposal; two traps (sit-ups left out, wall slides postponed); an idiom for the translation |

## 7. Later (not for the hackathon)

Real speech-to-text input, more languages, a native-speaker check of the translations, a fresh
sealed evaluation on new sessions, a larger falsifier model or several judges by majority.
