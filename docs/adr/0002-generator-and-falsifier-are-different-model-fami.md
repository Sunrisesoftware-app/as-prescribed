# ADR-0002: Generator and falsifier are different model families

**Status:** Accepted
**Atlas id:** `adr.ap.002`
**Links:** `ap.llm` (OpenAI-compatible model client and endpoint configuration), `ap.falsify` (The falsifier: fidelity against the transcript and back-translation)

> Rendered from the Atlas model (system `as-prescribed`). The model is the source of
> truth; edit it there and run `node scripts/adr-from-model.mjs`.

---

## Context

A falsifier from the generator's own family grades output it would tend to produce itself (the Somnus generate-falsify pattern, somnus ADR-0004). Somnus ADR-0005 also measured Mistral producing false contradictions (0/3), which rules it out as a falsifier.

## Decision

Local mode: generator Qwen3.5-35B-A3B on the R9700 (llama-agent :8091), falsifier gemma-3-12b-it Q4_K_M on the 7900 XT, with --no-mmap and a lowered agent prompt cache because the box has 16 GB host RAM. Public mode: two models of different families from the tokenfactory list. Decided by Petri 14.10.2026 (dec_9a6d6140ba3346b0).

## Consequences

Gemma rejects chat_template_kwargs, so the thinking switch is per endpoint. Measured 14.10.2026: with Qwen in both roles a mistranslation (running pain for knee pain) passed the back-check, the failure this decision exists for. Whether Gemma qualifies the entry for Google's partner prize is unverified.
