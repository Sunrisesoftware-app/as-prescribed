# As Prescribed DECISIONS

Every decision asked as a box, with its answer. **This file is the truth, the conversation is
not.** A decided row that changes the architecture enters the Atlas model as an ADR. Rows 1-8 were
decided in the owner's chat before the build (AMD-ACT3-HEALTH-HANDOFF v2, D1-D8); rows 9 onwards in
decision boxes in Code, each with a typed row in the Atlas decision log.

States: **draft** (not asked) · **OK** (decided) · **edit** · **drop** · **later**.

| # | Where | What now | Options (recommended first) | State |
|---|---|---|---|---|
| 1 | Input | A text transcript of the session, streamed in chunks; speech recognition out of scope | — | OK (D1) |
| 2 | Diagnoses | Constraints only, never generators of content | — | OK (D2) |
| 3 | Data | Synthetic only; no Premius material, no real patient | — | OK (D3) |
| 4 | Output | Patient program in the patient's language, after therapist approval | — | OK (D4) |
| 5 | Scope | CASSINI hackathon parked | — | OK (D5) |
| 6 | Languages | Arabic and Ukrainian | — | OK (D6) |
| 7 | S2 | A war-injured Ukrainian patient, described matter-of-factly | — | OK (D7) |
| 8 | Positioning | The system verifies the prescription, never the patient (adr.ap.001) | — | OK (D8) |
| 9 | Name | As Prescribed, repo as-prescribed | **As Prescribed** / Carryover / SamePage | OK (dec_e6d732c5cdd744e1) |
| 10 | Transcripts | English | **English** / Finnish / Finnish + English captions | OK (dec_b9d9b79759d34ef4) |
| 11 | Falsifier | gemma-3-12b-it on the 7900 XT (adr.ap.002) | **Gemma 3 12B** / smaller Qwen / tokenfactory both | OK (dec_9a6d6140ba3346b0) |
| 12 | 7900 XT | Laya-FI paused 15.-17.10. | booked windows (recommended) / **pause** / one window | OK, the owner chose against the recommendation (dec_975184ba2b9543e1) |
| 13 | S2 injury | Lower-limb amputation | **amputation** / nerve injury / fixator | OK (dec_7b568a36fe204ca0) |
| 14 | Clinical review | One review page, rows approved, no prose written | **review page** / Atlas doc / boxes | OK (dec_9038a0f31fcf4350) |
| 15 | Deploy | asprescribed.sunrisesoftware.app, ultragravel machine, systemd | **subdomain + systemd** / docker / own domain | OK (dec_5b3d764b787b41f1); the name confirmed by the owner 14.10.2026 (dec_591baa2b30f743b2); edit 14.10.2026: the owner handed the Cloudflare part to Code, which fronted the app with a Worker on the custom domain and Workers VPC over the machine's tunnel instead of nginx and certbot ([`deploy/README.md`](../deploy/README.md)) |
| 16 | Public input | Synthetic sessions and error injection, no free text (adr.ap.004) | **sessions + injection** / sessions only / free text | OK (dec_bc0df4d7c1d64869) |
| 17 | Atlas | A system of its own | — (the owner, in chat) | OK (14.10.2026) |
| 18 | S2.2 | Single-leg bridge on the intact (right) leg | **single-leg, right** / remove | OK (dec_053ef87aba2e4ce3) |
| 19 | Evaluation gates | Detection in round 0; recall >= 0.80 and >= 0.60 falsifier-only; false alarms <= 15 %; latency <= 90 s (adr.ap.009) | **the four recommendations** | OK (dec_19703418a6214843) |
| 20 | AMD for the judges | The lablab page: "The AMD component must be part of the working product shown to the judges." The public demo replays the Radeon runs, labelled as such; the video shows a live run on the box with the GPUs' load; the tokenfactory key is pursued so the public demo can run live on AMD's cloud | **recordings + live run in the video** / and tokenfactory live / AMD Developer Cloud credit | OK (dec_4df9557bb0ad458e) |
