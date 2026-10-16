# As Prescribed: submission texts (submitted on lablab 16.10.2026)

The texts exactly as submitted. The form limits them (title 50, short 255, long 2000 characters), so they
are shorter than the first draft, which is in git history before this file's submission commit.

Project page: https://lablab.ai/ai-hackathons/amd-developer-hackathon-act-iii/as-prescribed/as-prescribed-home-programs-verified-line-by-line

## Title (50 / 50)

As Prescribed: home programs verified line by line

## Short description (233 / 255)

As Prescribed turns a physiotherapy visit into the patient's home program in their own language and
verifies every line against the transcript, documented restrictions and a back-translation. Runs on the
clinic's own AMD Radeon GPUs.

## Long description (1930 / 2000)

The form keeps the paragraph breaks below; the public project page shows them as one paragraph.

The problem: a patient who does not speak the clinic's language leaves a physiotherapy visit with a home
program they cannot read, or with a translation nobody in the room can check. A wrong side, a wrong dose
or a dropped caution can hurt them, and a free-writing AI adds exercises nobody prescribed.

What it does: As Prescribed reads the visit transcript as it arrives, extracts what the therapist
prescribed and drafts the program in the patient's language (Arabic and Ukrainian in the demo). Every
line is supported (linked to where it was said), a conflict (a documented restriction blocks it and the
program halts), a proposal (only the therapist can complete it) or an uncertain translation. Nothing
reaches the patient until the therapist approves it. It verifies the prescription; it never diagnoses or
advises.

How: safety does not rest on a model. Documented restrictions are deterministic rules, a fired
restriction stays a conflict, and a line the rules cannot check is never supported. A generator drafts
and translates; a falsifier from another model family checks every line against the transcript and
back-translates it.

On AMD: real patient data cannot leave the clinic, so the product runs on the clinic's own AMD Radeon
GPUs: Qwen3.5-35B-A3B on a Radeon AI PRO R9700 drafts, Gemma 3 12B on a Radeon RX 7900 XT checks, on
llama.cpp with ROCm. A program is ready about 40 s after the visit, and our whole evaluation used
304 Wh. Judges can try the same pipeline live on AMD Radeon Cloud (Token Factory); each cloud run is
compared with the same case on the clinic hardware.

Measured, and reported as it fell: a sealed evaluation of 32 injected errors and 9 clean runs. The
rules caught every documented restriction; the falsifier caught 28% of the model-only errors in the
pre-registered run and 50% after fixes; false alarms fell from 16% to 7%. The recall gate failed, and
we say so. All data is synthetic.

## Participation, categories, track, technologies

- Participation mode: Online.
- Categories: Healthcare, Language and Translation.
- Event track: Health and Wellbeing.
- Technologies: AMD Developer Cloud, AMD ROCm, Gemma, Qwen3. The form's list has no llama.cpp, FastAPI
  or Cloudflare (only Cloudflare Workers AI, which we do not use); the additional information names
  them.

## Media

- Cover image: [`cover.png`](cover.png), cropped in the form to the whole image.
- Video: the captioned final cut (4:23, 15.9 MB), uploaded by the owner.
- Slides: [`deck.pdf`](deck.pdf).

## Application

- GitHub repository: https://github.com/Sunrisesoftware-app/as-prescribed
- Demo application platform: Other (the form's choices are Streamlit, Replit, Vercel, native.builder,
  Other, with no field to name it).
- Demo application URL: https://asprescribed.sunrisesoftware.app

## Additional information (804 / 2000)

Platform: self-hosted. A FastAPI service on our own server behind a Cloudflare Worker (Workers VPC over
a tunnel). Built with llama.cpp, FastAPI and Cloudflare, which the technology list did not offer.

The live demo runs each synthetic case on AMD Radeon Cloud (Token Factory: Qwen3.8-27B drafts,
Gemma-4-31B-IT checks) and shows the same case recorded on the clinic hardware (Radeon AI PRO R9700 and
Radeon RX 7900 XT, llama.cpp with ROCm) beside it. If the cloud run passes 90 s or a model is
unavailable, the page serves that clinic recording and labels it as such. The demo takes no free-text
input and logs nothing about a session; all data is synthetic.

The code is MIT. The sealed evaluation plan, its seal, the results and the raw runs are in eval/; the
architecture decisions are in docs/adr/.
