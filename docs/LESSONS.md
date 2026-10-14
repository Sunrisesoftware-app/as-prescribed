# As Prescribed LESSONS

Newest first. The **root cause** is the heading, not the symptom, because the root cause repeats
elsewhere. Only lessons whose price was actually paid. A lesson that becomes a permanent rule moves
into `CLAUDE.md`; a lesson that becomes a decision becomes an ADR.

## 14.10.2026: a gated page's refusal can mean "no session yet", not "no access"

### "Your email is not registered for API key distribution" for most of a day

notebooks.amd.com/tokenfactory refused the owner's email, so we planned around a missing key. We
emailed the organisers, decided how to show AMD without one (DECISIONS row 20) and deployed
replay-only. In the evening the owner signed in at notebooks.amd.com itself and then opened
`/tokenfactory`, and the team's key page appeared: the key had been provisioned all along.

**The rule:** when a page behind single sign-on refuses, sign in at the service's root first and
then open the page, before treating the refusal as a fact; the provider's own manual (here the
Token Factory documentation on the key page) beats third-party descriptions.

## 14.10.2026: a correction loop can undo a safety halt

### The generator rewrote contraindicated items until the rule stopped firing

In evaluation run 1 the rule engine caught all five injected contraindicated items in round 0. The
falsifier also objected that they were not prescribed, so the items went to the generator for
correction, and the generator changed the side or the exercise until the restriction no longer
matched: one item ended as a proposal, two as supported. The same loop turned three invented items
into copies of exercises the therapist did prescribe.

**The rule:** a fired restriction is sticky and the item is never corrected by a model
(adr.ap.005); a correction may not change the exercise (adr.ap.006).

## 14.10.2026: a same-family falsifier passes its own family's errors

### Qwen checking Qwen's Arabic missed "running pain" for "knee pain"

In the first smoke run Qwen3.5 was both generator and falsifier. Its Arabic for "some knee pain"
said "running pain" (الركض for الركبة), and its own back-translation read it back as knee pain, so
the line passed. Gemma, from another family, later caught a similar error in Ukrainian ("residual
limb" translated as "hip part").

**The rule:** the falsifier stays in another family (adr.ap.002); a smoke run with one model is
plumbing, never evidence.

## 14.10.2026: right-to-left text and number words break number checks

### Three false alarms from one dose

"Two sets of ten" became "مجموعتان من 10": the two is an Arabic dual, not a digit. "3 x 10" in a
right-to-left line rendered as "x 10 3" because the Latin x splits the number run. "1 minute" became
"دقيقة", a singular noun with no digit.

**The rule:** the English line writes doses as "N × M" with digits; the number check counts the dual
and "двічі" as two and does not require one.

## 14.10.2026: a falsifier reads notation as meaning

### Gemma called "3 x 12" a different dose from "three sets of twelve"

Run 1's 16.2 % false alarms were mostly gemma-3-12b-it objecting to format (digits against words),
to a side the cited spans name alone, and to cautions the item carried.

**The rule:** a falsifier claim a checkable rule can settle is settled by code, and the overrule is
logged (adr.ap.007); the falsifier quotes cautions, code compares them.

## 14.10.2026: approving a proposal in the viewer does not put it in the model

### The system was approved but did not exist

Viewer approval is the first gate; apply-approved and a commit are the second. The proposal also
lacked `rationale` inside its payload, so it could not have passed validation, and the queue held
two stale rows that would have regressed the model.

**The rule:** a new system is written as a model file in an Atlas worktree and merged by PR (as
here, #475); a proposal carries its rationale in the payload.

## 14.10.2026: starting the Gemma unit on the Somnus box stops Laya

### Laya was down for 78 minutes

`sudo systemctl start llama-theta` stopped `laya` (journal 17.29), although the box guide said
Laya could stay alongside. It was noticed only when restoring.

**The rule:** the restore step always checks and starts Laya (`curl -sf localhost:8110/health ||
sudo -n systemctl start laya`); the observation went to the somnus thread.

## 14.10.2026: a click that arrives before the data it acts on

### "Start" ran S1 while the screen showed S2

The session buttons fetched the session asynchronously; a click on Start during the fetch ran the
previous session's stream. Fixed with a load sequence number and Start disabled until the session
has loaded.

**The rule:** an action button is disabled until the data it acts on has loaded, and a late
response is ignored.
