# As Prescribed: the video's narration

One block per scene of the rough cut (`video/cut/`, timings in `video.md`). Each block fits its scene at
about 2.5 words a second with room for pauses. Paste each block into ElevenLabs as its own clip and
save it as `NN.mp3` (01-11). Code then fits the cut to the voice. The text is written for speech:
numbers and model names are spelled the way they should sound. The written forms are in brackets in
the notes, not in the blocks.

Pronunciation: Qwen = "chwen"; Radeon = "RAY-dee-on"; ROCm = "rock-em".

---

## 01 · Cover · 20 s · 39 words

This is As Prescribed. During a physiotherapy visit, it turns what the therapist says into the patient's home program, in the patient's own language. And it checks every line against what was actually prescribed, before anything reaches the patient.

## 02 · Problem and boundary · 25 s · 49 words

A patient who doesn't speak the clinic's language goes home with instructions they can't read. A wrong side, a wrong dose or a missing caution can hurt them. And a free-writing AI adds exercises nobody prescribed. So our boundary is strict. As Prescribed verifies the prescription. It never prescribes.

## 03 · The clinic's hardware · 11 s · 26 words

It runs on the clinic's own hardware. Qwen, on a Radeon AI Pro R ninety-seven hundred, drafts. Gemma, on a Radeon RX seventy-nine hundred XT, checks.

## 04 · Live visit and the conflict · 65 s · 115 words

Here is a live visit. The patient is recovering from a below-knee amputation, and the records say: no unsupervised standing on the prosthesis while the socket is being fitted.

As the therapist talks, the program is drafted. Watch the R ninety-seven hundred at work.

Last, the therapist adds one more exercise: stand on the left leg, at home, by the kitchen counter.

The visit ends, and every line is checked: against the transcript, against the documented restrictions, and back-translated from Ukrainian.

Four lines are supported, each linked to the moment it was said. The standing exercise collides with the prosthetist's restriction. A rule catches it, not a model, and the program halts for the therapist.

## 05 · Release to the patient · 19 s · 34 words

The therapist decides. The line is removed, the rest approved. Only then does the program reach the patient: in Ukrainian, with the English under each exercise, and a note that its headings are machine-written.

## 06 · The proposal · 23 s · 41 words

In this Arabic session, the therapist named a stretch without a side or a dose. The system does not guess. The line becomes a proposal that only the therapist can complete. Things the patient merely mentioned stay out of the program.

## 07 · Injected errors · 44 s · 68 words

We can also inject errors, to see what gets caught.

First, swap left and right inside the Ukrainian translation. The checking model back-translates the line, sees the swap, and catches it before anything is corrected.

Second, move the bridge exercise to the wrong leg. This one gets through. When the transcript mentions both sides, our checking model is at its weakest. We show the misses as they are.

## 08 · The Arabic sheet · 21 s · 33 words

For Arabic, the patient's sheet reads right to left. Every dose is written in digits, so a number can't drift in translation. The patient can print it, or keep it on the phone.

## 09 · The clinic and the evaluation · 30 s · 61 words

On these two cards, a program is ready about forty seconds after the visit. Our whole evaluation used three hundred and four watt-hours.

We sealed that evaluation before the first run. The rules caught every contraindicated exercise. The checking model caught about half of the errors only a model can see. That is below our own bar, and we say so.

## 10 · Try it in the cloud · 20 s · 31 words

Judges can try the same pipeline live, on AMD Radeon Cloud. Every cloud run is compared with the same case on the clinic hardware. In our trial, all six cases matched.

## 11 · Close · 10 s · 15 words

As Prescribed. The prescription, verified line by line, on the clinic's own AMD Radeon cards.

---

## Optional line (if scene 09 is lengthened by about 10 s)

While recording this video, we found one more gap: an exercise named outside our catalogue slipped past the rules. Now such a line always halts for the therapist.
