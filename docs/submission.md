# As Prescribed: submission texts (draft for the owner, not yet submitted)

## Title

As Prescribed: the home program, verified line by line

## Short description

During a physiotherapy visit, As Prescribed turns the session into the patient's home program in their
own language (Arabic, Ukrainian) and verifies every line against what the therapist said, the patient's
documented restrictions and a back-translation. In the clinic on AMD Radeon; to try, on AMD Radeon Cloud.

## Long description

**The problem.** A patient who does not speak the clinic's language leaves a physiotherapy visit with a
home program they cannot read, or with a translation nobody in the room can check. A wrong side, a
wrong dose or a dropped caution is a safety problem, and a free-writing AI makes it worse: it adds
plausible exercises nobody prescribed.

**The user.** The physiotherapist, who prescribes, and the patient, who goes home with the program.
Nothing reaches the patient until the therapist approves it.

**What it does.** As Prescribed reads the session transcript as it arrives and extracts what the
therapist prescribed. When the visit ends it has drafted the program in the patient's language, and
every line is in one of four states:
- *supported*: linked to the transcript span where it was said;
- *conflict*: a documented restriction blocks it, and the program halts for the therapist;
- *proposal*: nothing in the session says it, so only the therapist sees it;
- *uncertain translation*: the back-translation disagrees.

It verifies the therapist's prescription; it never diagnoses, never judges suitability and never adds
advice of its own.

**How.** Safety does not rest on a model. Documented restrictions are rules that a deterministic engine
checks, and a fired restriction stays a conflict whatever a model does afterwards. A generator drafts
and translates. A falsifier from a different model family checks every line against the transcript and
back-translates it, in rounds, and a correction may never change the exercise.

**On AMD.** Real patient data does not leave the clinic. The product runs on the clinic's own AMD Radeon
cards: Qwen3.5-35B-A3B on a Radeon AI PRO R9700 drafts, and Gemma 3 12B on a Radeon RX 7900 XT checks,
both on llama.cpp with ROCm. The program is ready about 40 s after the visit, and the whole evaluation
used 304 Wh. Judges can try the same pipeline live on AMD Radeon Cloud (Token Factory), and each cloud
run is compared on the page with the same case run on the clinic hardware. In our trial all six clean
cases gave the same line states in both places.

**Measured, and reported as it fell.** We sealed an evaluation plan before the first run: 32 injected
errors of six types (wrong dose, wrong side, invented exercise, dropped caution, contraindicated
exercise, mistranslation into Arabic or Ukrainian) and 9 clean runs.
- The deterministic layer caught all 14 errors it is meant to catch, and every contraindicated item.
- The model falsifier caught 28 % of the errors only a model can find in the pre-registered run, and
  50 % after fixes (that run was made after reading the first, and is labelled so).
- False alarms fell from 16 % to 7 %.

The recall gate failed in both runs, and we say so.

**What is next.** Real speech input, more languages, a native-speaker review of every fixed text, a
stronger falsifier, and a new sealed evaluation on new sessions. All data in the demo is synthetic.

## Track and tags

Track: Health and Wellbeing. Technologies: AMD ROCm, AMD Radeon, AMD Developer Cloud (Token Factory),
Gemma, Qwen3, llama.cpp, FastAPI, Cloudflare.

## Links

- Demo: https://asprescribed.sunrisesoftware.app
- Repository: https://github.com/Sunrisesoftware-app/as-prescribed
- Demo application platform: self-hosted (a systemd service behind Cloudflare); models on AMD Radeon
  Cloud and on on-prem AMD Radeon GPUs
